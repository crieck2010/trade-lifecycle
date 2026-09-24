"""Tests for policy files and the fail-closed adapters."""

from trade_lifecycle import adapters
from trade_lifecycle import policy as _policy


def test_checksum_deterministic(tmp_path):
    a = _policy.policy_checksum(b"mandate text")
    b = _policy.policy_checksum(b"mandate text")
    assert a == b and len(a) == 64
    assert _policy.policy_checksum(b"other") != a


def test_write_and_resolve(tmp_path):
    written = _policy.write_policy(str(tmp_path), "fund-ips-v1", "mandate text")
    assert written["policy_id"] == "fund-ips-v1"
    resolved = _policy.resolve_policy("fund-ips-v1", [str(tmp_path), "/nonexistent"])
    assert resolved is not None
    assert resolved["checksum"] == written["checksum"]
    assert resolved["path"] == written["path"]


def test_resolve_missing_returns_none(tmp_path):
    assert _policy.resolve_policy("nope", [str(tmp_path)]) is None
    assert _policy.resolve_policy("nope", []) is None


def test_adapters_fail_closed_without_backends():
    adapters.clear_backends()
    assert adapters.get_validation_report("s1") is None
    assert adapters.get_incubation_status("s1") is None


def test_adapters_use_injected_backends():
    adapters.clear_backends()
    adapters.use_backends(
        validation_report_fn=lambda sid: {"schema_version": 1, "sid": sid},
        incubation_status_fn=lambda sid: {"enrolled": True, "graduated": False},
    )
    assert adapters.get_validation_report("s1")["sid"] == "s1"
    st = adapters.get_incubation_status("s1")
    assert st["enrolled"] is True and st["graduated"] is False
    adapters.clear_backends()
    assert adapters.get_incubation_status("s1") is None


def test_sibling_available_probe():
    assert adapters.sibling_available("json") is True
    assert adapters.sibling_available("trade_nonexistent_xyz") is False
