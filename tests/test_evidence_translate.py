"""Tests for trade_lifecycle.evidence_translate.

The fidelity rule under test: the translator is a format change only.
Every number in the emitted report must equal the source evidence
number; every verdict must equal the source verdict; nothing may be
invented. The fixture is a verbatim copy of trade-strategies
docs/validation/regcond-1/tier1_evidence.json (canonical source of
truth lives there); the translator must be faithful to it field by
field.
"""

from __future__ import annotations

import copy
import json
import os

import pytest

from trade_lifecycle.evidence_translate import (
    EvidenceTranslationError,
    build_regcond1_report,
    frozen_config_regcond1,
    translate_tier1_to_validation_report,
)
from trade_lifecycle.gates import config_hash, gate_research_to_validated

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures",
                       "tier1_evidence_regcond1.json")


def _evidence():
    with open(FIXTURE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _report(evidence=None, **kwargs):
    return translate_tier1_to_validation_report(
        evidence if evidence is not None else _evidence(),
        frozen_config_regcond1(), **kwargs)


# ------------------------------------------------------- round-trip fidelity

def test_every_gate_value_threshold_verdict_matches_source():
    evidence = _evidence()
    report = _report(evidence)
    src = {g["name"]: g for g in evidence["gates"]}
    assert len(report["validation"]["gates"]) == len(src) == 5
    for rg in report["validation"]["gates"]:
        sg = src[rg["name"]]
        assert rg["value"] == sg["value"], rg["name"]
        assert rg["threshold"] == sg["threshold"], rg["name"]
        assert rg["verdict"] == ("PASS" if sg["passed"] else "FAIL"), rg["name"]


def test_gate_names_preserved_verbatim():
    evidence = _evidence()
    report = _report(evidence)
    assert [g["name"] for g in report["validation"]["gates"]] == [
        g["name"] for g in evidence["gates"]]


def test_evidence_metrics_equal_source_values():
    evidence = _evidence()
    report = _report(evidence)
    metrics = report["validation"]["evidence"]
    assert metrics == {
        "median_oos_sharpe": 1.385,
        "max_drawdown": -0.23,
        "dsr": 1.0,
        "excess_return_vs_benchmark_after_costs": 0.0491,
        "sortino": 1.41,
    }
    assert report["backtest"]["metrics"] == metrics


def test_margin_is_derived_not_claimed():
    report = _report()
    for g in report["validation"]["gates"]:
        assert g["margin"] == pytest.approx(g["value"] - g["threshold"])


def test_status_pass_when_all_gates_pass():
    report = _report()
    assert report["validation"]["status"] == "PASS"
    assert all(g["verdict"] == "PASS"
               for g in report["validation"]["gates"])


# ---------------------------------------------------------- provenance audit

def test_provenance_records_source_and_dates():
    report = _report()
    tr = report["translation"]
    assert tr["kind"] == "format translation -- NOT a re-validation"
    assert tr["source_evaluated_at"] == "2026-09-27T13:18:08+00:00"
    assert tr["source_evaluator"] == "trade-overfit"
    assert tr["source_framework"] == "two-tier/tier-1"
    assert tr["numbers_recomputed"] is False
    assert tr["new_claims"] == []
    assert tr["translator_version"] == "0.2.0"
    assert report["data_provenance"]["evaluated_at"] == \
        "2026-09-27T13:18:08+00:00"


def test_unavailable_fields_are_null_never_zero_filled():
    report = _report()
    bt = report["backtest"]
    assert bt["engine"] is None
    assert bt["initial_cash"] is None
    assert bt["final_equity"] is None
    assert bt["n_trades"] is None
    assert bt["n_open_positions"] is None
    assert any("unavailable" in n for n in bt["engine_notes"])
    assert "TRANSLATION" in " ".join(report["limitations"])


# -------------------------------------------------------- config-hash binding

def test_report_config_hash_matches_frozen_config():
    report = _report()
    assert (config_hash(report["strategy"]["config"])
            == config_hash(frozen_config_regcond1()))


def test_build_artifacts_config_json_hashes_identically(tmp_path):
    out = build_regcond1_report(FIXTURE, str(tmp_path))
    with open(out["config_path"], "r", encoding="utf-8") as fh:
        on_disk = json.load(fh)
    assert config_hash(on_disk) == out["config_hash"]
    assert config_hash(on_disk) == config_hash(frozen_config_regcond1())


def test_frozen_config_carries_frozen_weights():
    cfg = frozen_config_regcond1()
    assert cfg["weights"]["EXPANSION"] == {"SPY": 0.6, "CPER": 0.2,
                                          "TLT": 0.2, "GLD": 0.0}
    assert cfg["weights"]["CONTRACTION"] == {"SPY": 0.2, "CPER": 0.0,
                                            "TLT": 0.4, "GLD": 0.4}
    assert cfg["universe"] == ["SPY", "CPER", "TLT", "GLD"]
    assert cfg["signal"]["persist_days"] == 5


# ------------------------------------------------- lifecycle gate acceptance

def test_lifecycle_gate_structurally_accepts_translated_report():
    out_report = _report()
    expected = config_hash(frozen_config_regcond1())
    result = gate_research_to_validated(out_report, expected)
    assert result["passed"] is True, result["reasons"]
    assert result["reasons"] == []


def test_gate_refuses_on_config_mismatch():
    report = _report()
    tampered = copy.deepcopy(report)
    tampered["strategy"]["config"]["weights"]["EXPANSION"]["SPY"] = 0.7
    result = gate_research_to_validated(
        tampered, config_hash(frozen_config_regcond1()))
    assert result["passed"] is False
    assert any("Config-hash mismatch" in r for r in result["reasons"])


# ------------------------------------------------------------- fail-closed

def test_unknown_gate_name_refuses_translation():
    evidence = _evidence()
    evidence["gates"] = evidence["gates"] + [{
        "name": "mystery_gate", "value": 1.0, "threshold": 0.5,
        "passed": True}]
    with pytest.raises(EvidenceTranslationError):
        _report(evidence)


def test_missing_gate_value_refuses_translation():
    evidence = _evidence()
    broken = copy.deepcopy(evidence["gates"][0])
    del broken["value"]
    evidence["gates"][0] = broken
    with pytest.raises(EvidenceTranslationError):
        _report(evidence)


def test_wrong_evidence_schema_version_refuses():
    evidence = _evidence()
    evidence["schema_version"] = 2
    with pytest.raises(EvidenceTranslationError):
        _report(evidence)


def test_failing_source_gate_maps_to_fail_and_gate_refuses():
    evidence = _evidence()
    evidence["gates"][0]["passed"] = False
    report = _report(evidence)
    assert report["validation"]["gates"][0]["verdict"] == "FAIL"
    assert report["validation"]["status"] == "FAIL"
    result = gate_research_to_validated(
        report, config_hash(frozen_config_regcond1()))
    assert result["passed"] is False
