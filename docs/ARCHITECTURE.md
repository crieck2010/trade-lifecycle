# ARCHITECTURE — trade-lifecycle

## Position in the system

```
trade-swing ──ValidationReport──▶            ┌─────────────────┐
trade-incubate ──enrollment/graduation──▶    │ trade-lifecycle │──permission──▶ (human / suite pipeline)
trade-regime ──mode vocabulary──▶ (docs)     │  THE COMMITTEE  │
human ──approvals, reasons──▶                └─────────────────┘
                                                      │
                                                      ▼ (docs only, never called)
                                             trade-agents (PM reads state)
                                             trade-paper  (execution; independent)
```

The committee sits *beside* the execution path, not in it. `trade-paper`
never imports or consults this module: permission and execution are
separate failure domains. A bug here can wrongly refuse a promotion; it
can never place a trade.

## Modules

| Module | Responsibility |
|---|---|
| `lifecycle.py` | The transition table. `classify()` is a pure function: (target, state, paused) → {kind, legal, note}. The single source of truth for what moves are possible. |
| `gates.py` | Pure guard functions → `{passed, reasons[]}`. Every guard fails closed. |
| `registry.py` | Append-only JSONL event log + `StrategyRegistry`. `attempt()` classifies, runs the guard, appends `transition` or `refusal`, returns a `TransitionResult`. |
| `policy.py` | Minimal mandate hooks: write/resolve `<policy_id>.md`, SHA-256 checksums. |
| `adapters.py` | Lazy sibling bridges with test/demo injection. Fail-soft, fail-closed. |
| `presets.py` | `strict` / `balanced` / `lenient` gate profiles. |
| `demo.py` | Seeded four-strategy theater (deterministic). |
| `cli.py` | `register`, `promote`, `status`, `history`, `pause`, `resume`, `retire`, `demo`, `presets`, `license`, `update-check`. |
| `licensing.py` | Suite-wide license-key / update-check hooks. |

## The event log

One JSON object per line. Event types: `registered`, `transition`,
`refusal`. Current state is derived by *folding* the log — the log is
the source of truth and history cannot be rewritten, only appended to.

A `transition` event carries the full `TransitionResult`, any approvals,
the pause/retire reason, the authorized `mode`, and the recorded policy
checksum. A `refusal` event carries the attempted transition, actor,
timestamp, and every reason. Refusals are queryable per strategy
(`history --refusals-only`).

## The PAUSED overlay

Pause is not a state — it is a boolean overlay on the record. The audit
trail always shows *where* a strategy was paused (e.g. paused in PAPER),
and resume returns to that underlying state. Forward transitions are
blocked while paused. Only a human re-approval clears the overlay; kill
conditions can set it but never clear it.

## Scaling

- `attempt()` is O(events for the strategy); the fold is per-registry but
  registries are per-strategy-file in practice. Thousands of strategies
  and millions of events are comfortable on one machine.
- The log is plain JSONL: `grep`, `jq`, and log shippers all work. For a
  multi-operator fund, point the registry path at shared storage; the
  append-only discipline survives concurrent writers (interleaved lines
  are still valid JSONL; fold order = file order).
- No threads, no network, no background processes. The committee is a
  library + CLI, embeddable in the suite pipeline or a cron job.

## Contracts

- `TransitionResult`: `{schema_version: 1, allowed, reasons[], from, to,
  paused, at, actor}` — JSON-serializable, always.
- Guard result: `{passed, reasons[]}`.
- Registry record: `{strategy_id, name, family, created_at, config,
  config_hash, policy_id, state, paused, paused_reason}`.
