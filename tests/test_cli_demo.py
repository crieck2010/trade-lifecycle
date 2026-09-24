"""Tests for the demo theater and the CLI."""

import json
import subprocess
import sys

import pytest

from trade_lifecycle.demo import run_demo
from trade_lifecycle.cli import build_parser, main


def test_demo_is_deterministic():
    a = run_demo(seed=7)
    b = run_demo(seed=7)
    assert a["theater"] == b["theater"]
    assert a["final_states"] == b["final_states"]
    assert a["n_refusals"] == b["n_refusals"]


def test_demo_outcomes():
    s = run_demo(seed=7)
    states = s["final_states"]
    assert states["trend-7"]["state"] == "LIVE"
    assert states["trend-7"]["paused"] is False
    assert states["chop-9"]["state"] == "RESEARCH"   # refused at validation
    assert states["fade-3"]["state"] == "PAPER"       # paused in paper
    assert states["fade-3"]["paused"] is True
    assert states["old-1"]["state"] == "RETIRED"
    assert s["n_refusals"] >= 4  # B validation, B skip attempt, C live-while-paused, D terminal


def test_demo_refusal_log_mentions_reasons():
    s = run_demo(seed=7)
    text = "\n".join(s["theater"])
    assert "REFUSE" in text
    assert "ALLOW" in text


def test_cli_demo_runs(capsys):
    rc = main(["--registry", "/tmp/trade_lifecycle_test_cli.jsonl", "demo", "--seed", "7"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "trend-7" in out and "Refusals logged" in out


def test_cli_promote_refusal_exits_nonzero(tmp_path):
    reg = str(tmp_path / "r.jsonl")
    cfg = str(tmp_path / "cfg.json")
    with open(cfg, "w") as fh:
        json.dump({"fast": 20}, fh)
    assert main(["--registry", reg, "register", "--id", "s1", "--config", cfg]) == 0
    # promote without a report -> refused, exit code 2
    rc = main(["--registry", reg, "promote", "s1", "--to", "VALIDATED"])
    assert rc == 2


def test_cli_status_history(tmp_path, capsys):
    reg = str(tmp_path / "r.jsonl")
    cfg = str(tmp_path / "cfg.json")
    with open(cfg, "w") as fh:
        json.dump({"fast": 20}, fh)
    main(["--registry", reg, "register", "--id", "s1", "--name", "S1"])
    capsys.readouterr()  # drain the register output
    assert main(["--registry", reg, "status", "s1", "--json"]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)["state"] == "RESEARCH"
    assert main(["--registry", reg, "history", "s1"]) == 0


def test_cli_retire_requires_reason(tmp_path):
    reg = str(tmp_path / "r.jsonl")
    main(["--registry", reg, "register", "--id", "s1"])
    assert main(["--registry", reg, "retire", "s1"]) == 2          # no reason
    assert main(["--registry", reg, "retire", "s1", "--reason", "done"]) == 0


def test_cli_presets_and_license(tmp_path, capsys):
    reg = str(tmp_path / "r.jsonl")
    assert main(["--registry", reg, "presets"]) == 0
    out = capsys.readouterr().out
    assert "strict" in out and "lenient" in out
    assert main(["--registry", reg, "license"]) == 0


def test_cli_as_subprocess():
    # the console entry point path, via python -m (absolute PYTHONPATH:
    # the child runs with cwd=/tmp, so a relative path would misresolve)
    import os
    src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    env = dict(os.environ, PYTHONPATH=src)
    proc = subprocess.run(
        [sys.executable, "-m", "trade_lifecycle", "--registry",
         "/tmp/trade_lifecycle_test_sub.jsonl", "presets"],
        capture_output=True, text=True, cwd="/tmp", env=env)
    assert proc.returncode == 0, proc.stderr
    assert "strict" in proc.stdout


def test_unknown_preset_rejected():
    with pytest.raises(ValueError):
        from trade_lifecycle.presets import get_preset
        get_preset("reckless")
