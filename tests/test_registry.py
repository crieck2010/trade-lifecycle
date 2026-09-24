"""Tests for the append-only registry: replay, refusals, audit."""

from datetime import datetime, timedelta, timezone

import pytest

from trade_lifecycle import adapters, policy as _policy
from trade_lifecycle.demo import make_report
from trade_lifecycle.registry import StrategyRegistry

NOW = datetime(2026, 9, 24, 12, 0, 0, tzinfo=timezone.utc)
CFG = {"fast": 20, "slow": 50}


def _reg(tmp_path, clock=None):
    return StrategyRegistry(str(tmp_path / "reg.jsonl"),
                            clock=clock or (lambda: NOW.isoformat()))


def _fresh_report(config=CFG, verdicts=("PASS", "PASS")):
    return make_report(config,
                       [(f"g{i}", v) for i, v in enumerate(verdicts)],
                       (NOW - timedelta(days=20)).isoformat())


def _approval(who="alice"):
    return {"approver": who, "at": NOW.isoformat(), "rationale": "ok"}


@pytest.fixture(autouse=True)
def _clean_backends():
    adapters.clear_backends()
    yield
    adapters.clear_backends()


def test_register_and_status(tmp_path):
    reg = _reg(tmp_path)
    out = reg.register("s1", "S One", "ma-cross", CFG, actor="t")
    assert out["registered"] is True and out["state"] == "RESEARCH"
    st = reg.status("s1")
    assert st["state"] == "RESEARCH" and st["paused"] is False
    assert st["config_hash"] == out["config_hash"]


def test_duplicate_register_rejected(tmp_path):
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG)
    with pytest.raises(ValueError):
        reg.register("s1", "S", "f", CFG)


def test_unknown_strategy_attempt_refused_and_logged(tmp_path):
    reg = _reg(tmp_path)
    r = reg.promote("ghost", "VALIDATED", report=_fresh_report())
    assert r["allowed"] is False
    assert len(reg.refusals("ghost")) == 1


def test_full_path_to_validated(tmp_path):
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG)
    r = reg.promote("s1", "VALIDATED", actor="t", report=_fresh_report())
    assert r["allowed"] is True, r["reasons"]
    assert reg.status("s1")["state"] == "VALIDATED"


def test_no_skipping(tmp_path):
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG)
    r = reg.promote("s1", "LIVE", actor="t", report=_fresh_report(),
                    approval=_approval(), graduated=True, mode="supervised",
                    policy_dirs=[])
    assert r["allowed"] is False
    assert reg.status("s1")["state"] == "RESEARCH"


def test_refusal_is_logged_with_reasons(tmp_path):
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG)
    bad = _fresh_report(verdicts=("FAIL", "PASS"))
    r = reg.promote("s1", "VALIDATED", actor="mallory", report=bad)
    assert r["allowed"] is False
    refusals = reg.refusals("s1")
    assert len(refusals) == 1
    assert refusals[0]["actor"] == "mallory"
    assert "g0" in json_reasons(refusals[0])


def json_reasons(refusal_event):
    return " ".join(refusal_event["result"]["reasons"])


def test_validated_to_paper_needs_approval_and_enrollment(tmp_path):
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG)
    reg.promote("s1", "VALIDATED", report=_fresh_report())
    r = reg.promote("s1", "PAPER", actor="t")  # no approval, no enrollment
    assert r["allowed"] is False
    assert len(r["reasons"]) >= 2  # approval reasons + enrollment
    r2 = reg.promote("s1", "PAPER", actor="t", approval=_approval("alice"),
                     incubation_enrolled=True)
    assert r2["allowed"] is True
    assert reg.status("s1")["state"] == "PAPER"


def test_paper_to_live_full_guard(tmp_path):
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG, policy_id="fund-ips-v1")
    reg.promote("s1", "VALIDATED", report=_fresh_report())
    reg.promote("s1", "PAPER", approval=_approval("alice"), incubation_enrolled=True)
    # no graduation, no policy file -> refuse
    r = reg.promote("s1", "LIVE", approval=_approval("bob"),
                    graduated=False, mode="autonomous", policy_dirs=[])
    assert r["allowed"] is False
    _policy.write_policy(str(tmp_path), "fund-ips-v1", "mandate")
    r2 = reg.promote("s1", "LIVE", approval=_approval("bob"),
                     graduated=True, mode="autonomous", policy_dirs=[str(tmp_path)])
    assert r2["allowed"] is True, r2["reasons"]
    st = reg.status("s1")
    assert st["state"] == "LIVE"
    # policy checksum recorded in the transition event
    evs = [e for e in reg.history("s1") if e["event"] == "transition"]
    assert evs[-1]["policy_checksum"] == _policy.policy_checksum(b"mandate")
    assert evs[-1]["mode"] == "autonomous"


def test_pause_resume_cycle(tmp_path):
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG)
    reg.promote("s1", "VALIDATED", report=_fresh_report())
    r = reg.pause("s1", reason="drift violation", actor="risk")
    assert r["allowed"] is True
    st = reg.status("s1")
    assert st["paused"] is True and st["state"] == "VALIDATED"
    # forward motion blocked while paused
    r2 = reg.promote("s1", "PAPER", approval=_approval(), incubation_enrolled=True)
    assert r2["allowed"] is False
    # resume needs approval
    r3 = reg.resume("s1", approval=None)
    assert r3["allowed"] is False
    r4 = reg.resume("s1", approval=_approval("alice"))
    assert r4["allowed"] is True
    assert reg.status("s1")["paused"] is False


def test_retire_is_terminal(tmp_path):
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG)
    r = reg.retire("s1", reason="superseded", actor="t")
    assert r["allowed"] is True
    assert reg.status("s1")["state"] == "RETIRED"
    for to in ("VALIDATED", "PAPER", "LIVE", "RESUME"):
        assert reg.promote("s1", to, report=_fresh_report())["allowed"] is False
    assert reg.pause("s1", reason="x")["allowed"] is False


def test_replay_reconstructs_state(tmp_path):
    path = str(tmp_path / "reg.jsonl")
    reg = StrategyRegistry(path, clock=lambda: NOW.isoformat())
    reg.register("s1", "S", "f", CFG)
    reg.promote("s1", "VALIDATED", report=_fresh_report())
    reg2 = StrategyRegistry(path, clock=lambda: NOW.isoformat())
    assert reg2.status("s1")["state"] == "VALIDATED"
    assert len(reg2.history("s1")) == len(reg.history("s1"))


def test_stale_report_refused_via_registry(tmp_path):
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG)
    stale = make_report(CFG, [("g0", "PASS")],
                        (NOW - timedelta(days=200)).isoformat())
    r = reg.promote("s1", "VALIDATED", report=stale)
    assert r["allowed"] is False
    assert any("200" in reason for reason in r["reasons"])


def test_config_hash_mismatch_refused(tmp_path):
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG)
    other = _fresh_report(config={"fast": 99})
    r = reg.promote("s1", "VALIDATED", report=other)
    assert r["allowed"] is False


def test_lenient_preset_allows_warns(tmp_path):
    from trade_lifecycle.presets import get_preset
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG)
    rep = _fresh_report(verdicts=("PASS", "WARN"))
    r = reg.promote("s1", "VALIDATED", report=rep,
                    preset=get_preset("lenient"))
    assert r["allowed"] is True
    reg2_path = str(tmp_path / "r2.jsonl")
    reg2 = StrategyRegistry(reg2_path, clock=lambda: NOW.isoformat())
    reg2.register("s2", "S", "f", CFG)
    r2 = reg2.promote("s2", "VALIDATED", report=rep)  # strict default
    assert r2["allowed"] is False


def test_history_refusals_only(tmp_path):
    reg = _reg(tmp_path)
    reg.register("s1", "S", "f", CFG)
    reg.promote("s1", "VALIDATED", report=_fresh_report(verdicts=("FAIL",)))
    evs = reg.history("s1", refusals_only=True)
    assert len(evs) == 1 and evs[0]["event"] == "refusal"
    assert len(reg.history("s1")) == 2  # registered + refusal
