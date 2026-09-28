# Paper-incubation approval — REGCOND-1

| Field | Value |
|---|---|
| `strategy_id` | REGCOND-1 |
| `approval_type` | paper incubation (lifecycle VALIDATED → PAPER, plus enrollment in the `trade-incubate` 63-trading-day program) |
| `granted_by` | Charlie |
| `granted_via` | chat (main session) |
| `date` | 2026-09-28 (America/New_York) |
| `verbatim` | "I authorize the negative-price bug fix, and give the paper approval for REGCOND-1's incubation." |

## Scope

**Authorizes:**

1. The lifecycle transition preconditions for REGCOND-1's VALIDATED → PAPER
   promotion to be satisfied via Charlie's own CLI actions
   (`trade-lifecycle promote REGCOND-1 --to PAPER --approver Charlie
   --rationale <see below> --enrolled`), with this record as the
   human-approval evidence the gate requires.
2. Enrollment of REGCOND-1 in the `trade-incubate` paper-trading incubation
   program (63 trading days, dry-run default, paper only).

**Does NOT authorize:**

- The transition itself. Lifecycle transitions remain Charlie's CLI action
  per standing rule; no agent executed or will execute `promote`.
- Live trading. PAPER is paper-only by construction; a separate approval
  with a different approver is required for any LIVE transition
  (two-person rule).
- The negative-price bug-fix half of the quoted sentence. That authorization
  is tracked as its own workstream (trade-backtest); this record covers only
  the paper-approval half. The full sentence is quoted verbatim above so
  nothing is taken out of context.

## Rationale

No separate written rationale was given beyond the approval itself. When
running the promote command, use a rationale that references this record,
e.g. `--rationale "Paper incubation authorized 2026-09-28, see trade-lifecycle docs/approvals/REGCOND-1-paper-2026-09-28.md"`.

## Evidence at time of approval

- `trade-strategies/docs/validation/regcond-1/tier1_evidence.json`:
  Tier-1 verdict PASS (5/5 gates), evaluated 2026-09-27, passes
  `trade-allocate`'s `validate_evidence()` (re-verified 2026-09-28).
- Two-tier framework adopted 2026-09-27
  (`trade-strategies/docs/validation/GATES.md`); REGCOND-1 grandfathered
  from the prospective cost-speed-limit gate.

## Known open item (not a refusal of this approval)

The `trade-lifecycle` RESEARCH → VALIDATED gate consumes a trade-swing
ValidationReport (schema v1); REGCOND-1's evidence is in the two-tier
`tier1_evidence.json` shape. The format translation (or a native re-run) is
still needed before `promote --to VALIDATED` will pass its guards. This is
a mechanical evidence-format gap, not a finding against the strategy.

```approval.json
{
  "strategy_id": "REGCOND-1",
  "approval_type": "paper incubation",
  "granted_by": "Charlie",
  "granted_via": "chat",
  "date": "2026-09-28",
  "timezone": "America/New_York",
  "verbatim": "I authorize the negative-price bug fix, and give the paper approval for REGCOND-1's incubation.",
  "authorizes": ["lifecycle VALIDATED -> PAPER preconditions via his CLI", "trade-incubate enrollment"],
  "does_not_authorize": ["executing the transition", "live trading", "the bug-fix workstream (tracked separately)"],
  "record": "trade-lifecycle/docs/approvals/REGCOND-1-paper-2026-09-28.md"
}
```
