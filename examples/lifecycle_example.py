"""trade-lifecycle example: the committee from Python.

Runs the seeded four-strategy theater and prints the audit-relevant
outcomes.  No siblings required; no network; nothing trades.
"""

import json
import tempfile
import os

from trade_lifecycle.demo import run_demo
from trade_lifecycle.presets import list_presets
from trade_lifecycle.registry import StrategyRegistry


def main() -> None:
    summary = run_demo(seed=7)
    print("=== The theater ===")
    for line in summary["theater"]:
        print(line)

    print("\n=== Final states ===")
    for sid, st in summary["final_states"].items():
        paused = " (PAUSED)" if st["paused"] else ""
        print(f"  {sid}: {st['state']}{paused}")
    print(f"\nRefusals logged: {summary['n_refusals']}")

    print("\n=== A refusal, up close ===")
    tmp = tempfile.mkdtemp(prefix="lifecycle_example_")
    reg = StrategyRegistry(os.path.join(tmp, "r.jsonl"))
    reg.register("bad-idea", "Bad Idea", "gut-feel", {"vibes": 11})
    result = reg.promote("bad-idea", "VALIDATED", actor="mallory")
    print(json.dumps(result, indent=2))
    print(f"\nRefusals for bad-idea: {len(reg.refusals('bad-idea'))}")

    print("\n=== Gate presets ===")
    for name, preset in list_presets().items():
        print(f"  {name}: {preset['description']}")


if __name__ == "__main__":
    main()
