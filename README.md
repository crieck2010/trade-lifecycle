# trade-lifecycle

The investment committee in code. Strategies move
**RESEARCH → VALIDATED → PAPER → LIVE → RETIRED** strictly in order —
every transition carries machine-enforced guards, and a `promote`
command that **refuses** with stated reasons when the guards aren't met.
Refused attempts are logged as first-class audit events: a strategy that
was never refused was never really gated.

Part of the [trade-suite](https://github.com/crieck2010/trade-suite)
algorithmic trading system. It governs *permission*: nothing here
executes trades, sizes positions, or touches a broker.

## Install

```bash
pip install trade-lifecycle
# or from source
git clone https://github.com/crieck2010/trade-lifecycle
cd trade-lifecycle
pip install -e .
```

Requires Python 3.10+. No third-party dependencies — not even NumPy.

## Quick start

```python
from trade_lifecycle.registry import StrategyRegistry

reg = StrategyRegistry("lifecycle.jsonl")
reg.register("trend-7", "Trend Seven", "ma-cross",
             config={"fast": 20, "slow": 50, "atr_period": 14},
             policy_id="fund-ips-v1")

# RESEARCH -> VALIDATED: needs a trade-swing ValidationReport (schema v1)
# with every gate PASS, fresh, and bound to the registered config.
result = reg.promote("trend-7", "VALIDATED", actor="you", report=report)
print(result["allowed"], result["reasons"])   # False + reasons, unless the gates pass
```

The full walkthrough — including the seeded four-strategy theater — is
in `examples/lifecycle_example.py`, or run it directly:

```bash
trade-lifecycle demo
```

CLI:

```bash
trade-lifecycle register --id trend-7 --name "Trend Seven" --family ma-cross \
    --config config.json --policy-id fund-ips-v1
trade-lifecycle promote trend-7 --to VALIDATED --report validation_report.json
trade-lifecycle promote trend-7 --to PAPER --approver alice \
    --rationale "Validation clean; enroll in Q4 incubation." --enrolled
trade-lifecycle promote trend-7 --to LIVE --approver bob \
    --rationale "Graduated; authorizing autonomous mode." \
    --graduated --mode autonomous --policy-dir ./policies
trade-lifecycle status trend-7
trade-lifecycle history trend-7 --refusals-only
trade-lifecycle pause trend-7 --reason "drift VIOLATION in week 7"
trade-lifecycle resume trend-7 --approver alice --rationale "Drift resolved."
trade-lifecycle retire trend-7 --reason "Superseded; edge decayed."
trade-lifecycle presets
```

Refusals exit non-zero with the reasons printed. `promote --to` also
accepts `PAUSED`, `RESUME`, and `RETIRED` (with `--reason`), but the
dedicated commands read better.

## The maths

**What you learn.** Whether a strategy has *earned* its next stage —
not whether it looks promising, but whether the paperwork exists: a
fresh, passing validation bound to the exact config; a named human who
signed off with a written rationale; a completed incubation; a recorded
mandate. The committee checks evidence, not enthusiasm.

**Why it matters.** Every live-trading disaster story has the same
shape: a strategy skipped a step. It went live on a backtest nobody
reproduced, on parameters nobody recorded, approved by nobody in
particular. Gates that can be skipped are suggestions. This module makes
skipping *structurally impossible* — the transition table has no path
from RESEARCH to LIVE, and the registry is the only way forward.

**The maths.**

- *Config-hash binding.* The registered config is canonicalized (sorted
  keys, compact JSON) and hashed with SHA-256. Any parameter change —
  even a float rounding — yields a different hash, so a validation
  report earned by one parameter set cannot promote another. This is
  tamper-evidence, not cryptography worship: it closes the
  bait-and-switch where the tested config and the traded config drift
  apart.
- *Freshness as decay.* Reports older than 90 days (strict) are refused.
  Strategies decay — markets change, edges erode — so evidence has a
  half-life. The threshold is a convention, documented as one.
- *The two-person rule.* LIVE authorization must come from a different
  human than PAPER authorization. Separation of duties is the oldest
  internal control in finance; here it is three lines of code.
- *Refusal logging as deterrence.* Every refused attempt is appended to
  the same immutable log as every allowed transition, with actor,
  timestamp, and reasons. Audit trails change behavior: people who know
  their override attempts are permanently recorded attempt fewer of
  them.
- *Fail-closed guards.* Each guard returns `{passed, reasons[]}`, and
  every unknown — missing report, missing sibling, unparseable
  timestamp — maps to refusal. Absence of evidence is never evidence
  of validity.

**Honest limitations.** The gates check *paperwork*, not truth. A
fabricated validation report with all gates PASS will promote — this
module prevents skipping steps, not fraud or bad judgment. Human
approvals are only as good as the human; the two-person rule raises the
bar but doesn't guarantee wisdom. A strategy can pass every gate and
still lose money: graduation means "earned consideration for capital,"
not "proven." Thresholds (90 days, 20 trades, distinct approvers) are
conventions, not derived constants.

## Interop

| Sibling | Direction | Contract |
|---|---|---|
| `trade-swing` | in (lazy) | ValidationReport `schema_version: 1` — every gate PASS, fresh, config-hash bound |
| `trade-incubate` | in (lazy) | Enrollment + GRADUATED verdict; kill conditions drive `pause` |
| `trade-regime` | in (docs) | `DECISION_LOOP.md` mode switch — `supervised` / `autonomous` recorded at PAPER→LIVE |
| `trade-agents` | out (docs) | PM agent reads lifecycle state before allocating; no mandate, no capital |
| `trade-paper` | out (docs) | Execution layer; never consults this module (permission ≠ execution, by design) |
| `trade-suite` | in (future) | `promote` is the enforcement point for the suite's strategy pipeline |

All sibling reads are lazy and fail-closed: with siblings uninstalled,
gates refuse with clear reasons instead of erroring. `schema_version: 1`
on every `TransitionResult` (see `docs/ARCHITECTURE.md`).

## License

MIT. `trade-lifecycle license` shows the license-key hook (community
tier accepts any key in v0.1.x); `trade-lifecycle update-check` queries
the GitHub releases API and never raises.
