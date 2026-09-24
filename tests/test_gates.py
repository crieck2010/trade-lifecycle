"""Tests for the guard functions (fail-closed paperwork checks)."""

from datetime import datetime, timedelta, timezone

from trade_lifecycle import gates
from trade_lifecycle.gates import config_hash

NOW = datetime(2026, 9, 24, 12, 0, 0, tzinfo=timezone.utc)
CFG = {"fast": 20, "slow": 50}
HASH = config_hash(CFG)


def _report(verdicts=("PASS", "PASS"), age_days=20, config=CFG, status=None):
    gates_list = [{"name": f"g{i}", "verdict": v, "value": 1.0,
                   "threshold": 0.0, "margin": 1.0}
                  for i, v in enumerate(verdicts)]
    if status is None:
        status = "FAIL" if "FAIL" in verdicts else "PASS"
    return {
        "schema_version": 1,
        "generated_utc": (NOW - timedelta(days=age_days)).isoformat(),
        "strategy": {"config": config},
        "validation": {"status": status, "gates": gates_list},
    }


def _approval(who="alice"):
    return {"approver": who, "at": NOW.isoformat(), "rationale": "looks good"}


# ------------------------------------------------ RESEARCH -> VALIDATED

def test_config_hash_is_deterministic_and_sensitive():
    assert config_hash(CFG) == config_hash({"slow": 50, "fast": 20})
    assert config_hash(CFG) != config_hash({"fast": 20, "slow": 51})


def test_good_report_passes():
    g = gates.gate_research_to_validated(_report(), HASH, now=NOW)
    assert g["passed"] is True and g["reasons"] == []


def test_missing_report_fails_closed():
    g = gates.gate_research_to_validated(None, HASH, now=NOW)
    assert g["passed"] is False and g["reasons"]


def test_failing_gate_refuses_with_names():
    g = gates.gate_research_to_validated(_report(("PASS", "FAIL")), HASH, now=NOW)
    assert g["passed"] is False
    assert any("g1" in r for r in g["reasons"])


def test_warn_refused_under_strict_allowed_under_lenient():
    rep = _report(("PASS", "WARN"), status="WARN")
    strict = gates.gate_research_to_validated(rep, HASH, allow_warns=False, now=NOW)
    assert strict["passed"] is False
    lax = gates.gate_research_to_validated(rep, HASH, allow_warns=True, now=NOW)
    assert lax["passed"] is True


def test_stale_report_refuses():
    g = gates.gate_research_to_validated(_report(age_days=200), HASH, now=NOW)
    assert g["passed"] is False
    assert any("200" in r for r in g["reasons"])


def test_future_report_refuses():
    rep = _report()
    rep["generated_utc"] = (NOW + timedelta(days=1)).isoformat()
    g = gates.gate_research_to_validated(rep, HASH, now=NOW)
    assert g["passed"] is False


def test_config_hash_mismatch_refuses():
    g = gates.gate_research_to_validated(_report(config={"fast": 99}), HASH, now=NOW)
    assert g["passed"] is False
    assert any("hash" in r.lower() for r in g["reasons"])


def test_skipped_gates_refuse():
    rep = _report(("PASS", "SKIPPED"), status="WARN")
    g = gates.gate_research_to_validated(rep, HASH, allow_warns=True, now=NOW)
    assert g["passed"] is False
    assert any("SKIPPED" in r for r in g["reasons"])


def test_wrong_schema_refuses():
    rep = _report()
    rep["schema_version"] = 2
    g = gates.gate_research_to_validated(rep, HASH, now=NOW)
    assert g["passed"] is False


# ------------------------------------------------ VALIDATED -> PAPER

def test_paper_gate_happy_path():
    g = gates.gate_validated_to_paper(_approval(), True)
    assert g["passed"] is True


def test_paper_gate_no_approval_refuses():
    g = gates.gate_validated_to_paper(None, True)
    assert g["passed"] is False


def test_paper_gate_blank_rationale_refuses():
    ap = _approval()
    ap["rationale"] = "   "
    g = gates.gate_validated_to_paper(ap, True)
    assert g["passed"] is False


def test_paper_gate_not_enrolled_fails_closed():
    assert gates.gate_validated_to_paper(_approval(), False)["passed"] is False
    assert gates.gate_validated_to_paper(_approval(), None)["passed"] is False


# ------------------------------------------------ PAPER -> LIVE

def _live_gate(**kw):
    base = {"graduated": True, "approval": _approval("bob"),
            "mode": "supervised", "policy_id": "fund-ips-v1",
            "policy_dirs": kw.pop("policy_dirs", []),
            "prior_approver": "alice",
            "require_distinct_approver": True}
    base.update(kw)
    return gates.gate_paper_to_live(**base)


def test_live_gate_needs_policy_file(tmp_path):
    from trade_lifecycle import policy as _policy
    _policy.write_policy(str(tmp_path), "fund-ips-v1", "mandate text")
    g = _live_gate(policy_dirs=[str(tmp_path)])
    assert g["passed"] is True, g["reasons"]


def test_live_gate_missing_policy_refuses():
    g = _live_gate(policy_dirs=[])
    assert g["passed"] is False
    assert any("Policy file" in r for r in g["reasons"])


def test_live_gate_not_graduated_refuses(tmp_path):
    from trade_lifecycle import policy as _policy
    _policy.write_policy(str(tmp_path), "fund-ips-v1", "mandate text")
    g = _live_gate(graduated=False, policy_dirs=[str(tmp_path)])
    assert g["passed"] is False


def test_live_gate_same_approver_refuses_under_two_person_rule(tmp_path):
    from trade_lifecycle import policy as _policy
    _policy.write_policy(str(tmp_path), "fund-ips-v1", "mandate text")
    g = _live_gate(approval=_approval("alice"), policy_dirs=[str(tmp_path)])
    assert g["passed"] is False
    assert any("Two-person" in r for r in g["reasons"])


def test_live_gate_same_approver_allowed_when_rule_off(tmp_path):
    from trade_lifecycle import policy as _policy
    _policy.write_policy(str(tmp_path), "fund-ips-v1", "mandate text")
    g = _live_gate(approval=_approval("alice"), policy_dirs=[str(tmp_path)],
                   require_distinct_approver=False)
    assert g["passed"] is True


def test_live_gate_bad_mode_refuses(tmp_path):
    g = _live_gate(mode="yolo", policy_dirs=[str(tmp_path)])
    assert g["passed"] is False
    assert any("supervised" in r for r in g["reasons"])


# ------------------------------------------------ pause / resume / retire

def test_pause_needs_reason():
    assert gates.gate_pause("drift violation")["passed"] is True
    assert gates.gate_pause("")["passed"] is False
    assert gates.gate_pause(None)["passed"] is False


def test_resume_needs_approval():
    assert gates.gate_resume(_approval())["passed"] is True
    assert gates.gate_resume(None)["passed"] is False


def test_retire_needs_reason():
    assert gates.gate_retire("edge decayed")["passed"] is True
    assert gates.gate_retire("  ")["passed"] is False
