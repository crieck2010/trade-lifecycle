"""Tests for the lifecycle state machine (transition table)."""

import pytest

from trade_lifecycle.lifecycle import STATES, classify


def test_states_are_ordered():
    assert STATES == ("RESEARCH", "VALIDATED", "PAPER", "LIVE", "RETIRED")


def test_forward_path_is_legal():
    assert classify("VALIDATED", "RESEARCH", False)["legal"] is True
    assert classify("PAPER", "VALIDATED", False)["legal"] is True
    assert classify("LIVE", "PAPER", False)["legal"] is True


@pytest.mark.parametrize("frm,to", [
    ("RESEARCH", "PAPER"), ("RESEARCH", "LIVE"), ("VALIDATED", "LIVE"),
    ("PAPER", "VALIDATED"), ("LIVE", "PAPER"), ("VALIDATED", "RESEARCH"),
    ("LIVE", "RESEARCH"),
])
def test_no_skipping_or_backwards(frm, to):
    assert classify(to, frm, False)["legal"] is False


def test_skip_mentions_ordering():
    note = classify("LIVE", "RESEARCH", False)["note"]
    assert "RESEARCH" in note and "skipped" in note.lower()


def test_retired_is_terminal():
    for to in list(STATES) + ["PAUSED", "RESUME"]:
        assert classify(to, "RETIRED", False)["legal"] is False
    note = classify("VALIDATED", "RETIRED", False)["note"]
    assert "terminal" in note.lower()


def test_retire_from_any_non_terminal_is_legal():
    for frm in ("RESEARCH", "VALIDATED", "PAPER", "LIVE"):
        r = classify("RETIRED", frm, False)
        assert r["legal"] is True and r["kind"] == "retire"


def test_pause_overlay_rules():
    assert classify("PAUSED", "PAPER", False)["legal"] is True
    assert classify("PAUSED", "VALIDATED", False)["legal"] is True
    assert classify("PAUSED", "LIVE", False)["legal"] is True
    assert classify("PAUSED", "RESEARCH", False)["legal"] is False
    assert classify("PAUSED", "PAPER", True)["legal"] is False  # already paused


def test_resume_rules():
    assert classify("RESUME", "PAPER", True)["legal"] is True
    assert classify("RESUME", "PAPER", False)["legal"] is False


def test_forward_blocked_while_paused():
    r = classify("LIVE", "PAPER", True)
    assert r["legal"] is False
    assert "paused" in r["note"].lower()


def test_unknown_target():
    r = classify("MOON", "PAPER", False)
    assert r["legal"] is False and r["kind"] == "unknown"


def test_guards_are_named():
    r = classify("VALIDATED", "RESEARCH", False)
    assert "validation" in r["note"].lower()
