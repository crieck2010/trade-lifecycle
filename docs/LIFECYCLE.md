# LIFECYCLE.md — the fund's constitution

This document is the investment-committee charter for the trading
system, written as an executable specification. Where this document and
the code disagree, the code governs and the document must be amended.

## Article I — Stages

A strategy exists in exactly one of RESEARCH, VALIDATED, PAPER, LIVE,
RETIRED. PAUSED is an overlay, not a stage.

## Article II — Order

Stages are strictly ordered. No strategy may skip a stage, move
backward, or leave RETIRED. The transition table in `lifecycle.py` is
the complete law; there are no exceptions, waivers, or back doors.

## Article III — Evidence at each boundary

1. **RESEARCH → VALIDATED.** A `trade-swing` ValidationReport
   (schema v1): every gate PASS, generated within the freshness window,
   config hash matching the registered config.
2. **VALIDATED → PAPER.** A named human approval (approver, timestamp,
   written rationale) AND enrollment in the `trade-incubate` harness.
3. **PAPER → LIVE.** A GRADUATED incubation verdict, a second human
   approval from a *different* approver, explicit authorization of the
   autonomy mode (`supervised` or `autonomous`), and a recorded
   investment-policy checksum.
4. **→ PAUSED.** A stated reason: kill condition or human judgment.
5. **PAUSED → stage.** Human re-approval with rationale. Kill
   conditions may pause; only humans resume.
6. **→ RETIRED.** A stated reason. Terminal.

## Article IV — The refusal record

Every refused transition is permanently logged with actor, timestamp,
and reasons, in the same ledger as allowed transitions. The refusal
record is reviewed, not hidden.

## Article V — Modes

`supervised`: the human approves orders (the current standing rule).
`autonomous`: the system trades within the authorized policy, guarded
by the daily loss limit, per-position caps, regime stand-down, and the
human kill switch. The mode is authorized at PAPER → LIVE and recorded
in the transition event; changing it later requires a new approval.

## Article VI — Amendments

Gate thresholds (freshness windows, WARN tolerance, the two-person
rule) are set by the `strict` / `balanced` / `lenient` presets.
Changing the transition table itself requires a code change, a version
bump, and a changelog entry — the constitution is not edited casually.

## Article VII — Limitations of the law

This constitution governs *process*, not outcomes. It cannot detect a
fabricated report, guarantee a human's wisdom, or make a strategy
profitable. What it guarantees: no strategy reaches capital without
passing every stage in order, with the evidence on record.
