# Evidence translation: Tier-1 -> ValidationReport (schema v1)

## The two evidence formats

The suite speaks two evidence dialects for the same question — "has this
strategy earned promotion?"

| | Tier-1 evidence | ValidationReport (schema v1) |
|---|---|---|
| Owned by | trade-allocate (contract), trade-strategies (framework) | trade-swing (producer), trade-lifecycle (consumer) |
| File | `tier1_evidence.json` | `validation-report-v1.json` |
| Gate set | two-tier/tier-1 entry filter (5 gates) | `validation.gates[]` with per-gate `verdict` |
| Verdict field | `verdict: "PASS"` + per-gate `passed: bool` | `validation.status` + per-gate `verdict: "PASS"` |
| Config binding | none | `strategy.config` hashed, must match registration |
| Freshness | `evaluated_at` | `generated_utc` (< 90 days for the strict preset) |

The lifecycle gate (`gates.gate_research_to_validated`) only reads the
right-hand column. A strategy validated under the two-tier framework
therefore needs its evidence *re-enveloped* — never re-evaluated — into
the schema-v1 shape. That is what `trade_lifecycle.evidence_translate`
does.

## The rule: translation, not re-validation

**Same numbers, same verdicts, zero new claims.** The translator copies
values; it never recomputes them. `numbers_recomputed` is always
`False`. Every emitted field traces to a source field; fields the
schema expects but Tier-1 evidence cannot supply (engine-level backtest
detail: initial cash, per-trade records) are `null` with an explicit
note — never invented, never silently zero-filled.

The module docstring states this plainly, and the emitted report
carries a `translation` section plus a `TRANSLATION` limitation entry
so any reader — human or agent — can see the provenance without
guessing.

## Mapping table (source field -> report field)

| `tier1_evidence.json` gate | report `validation.gates[]` entry |
|---|---|
| `oos_sharpe_median` (value 1.385, threshold 0.3) | `name` kept verbatim, `metric: median_oos_sharpe`, `op: gt`, `verdict: PASS`, `margin = value - threshold` |
| `max_drawdown` (-0.23, -0.25) | `metric: max_drawdown`, `op: gt`, `verdict: PASS` |
| `deflated_sharpe` (1.0, 0.8) | `metric: dsr`, `op: gt`, `verdict: PASS` |
| `excess_return_vs_benchmark_net_per_yr` (0.0491, 0.0) | `metric: excess_return_vs_benchmark_after_costs`, `op: gt`, `verdict: PASS` |
| `sortino` (1.41, 0.75) | `metric: sortino`, `op: gt`, `verdict: PASS` |

`op` follows trade-swing's convention; every Tier-1 gate is a strict
`>` threshold per the adopted framework. `margin` is derived exactly as
trade-swing derives it (for `gt`: `value - threshold`) — arithmetic, not
a claim. `gate_preset` is set to the evidence's `framework`
(`"two-tier/tier-1"`), and `validation.status` is `"PASS"` iff every
mapped gate is PASS.

Supplementary trace: `n_windows_walkforward: 13` comes from
trade-strategies `docs/validation/regcond-1/evidence.json`
`walk_forward.n_folds` (cited in the tier-1 evidence's `evidence_ref`);
its source is recorded in `n_windows_source`.

## The maths: config-hash binding

The lifecycle's `config_hash` canonicalizes the config dict (sorted
keys, compact JSON separators, `default=str`) and hashes it with
SHA-256. The translator invents no hashing: it imports the lifecycle's
own `config_hash` and binds the report's `strategy.config` to the
frozen config.

The frozen config is transcribed once, in code
(`frozen_config_regcond1()`), from the frozen pre-registration
(`trade-strategies/docs/validation/regcond-1/PRE-REGISTRATION.md`,
frozen 2026-09-26; amended 2026-09-27 for the gate set only). The same
dict is written to `docs/validation/regcond-1/config.json` — the file
that must be passed to `trade-lifecycle register --config`. By
construction, `config_hash(report.strategy.config) ==
config_hash(config.json) ==` the registered hash, so the gate's
bait-and-switch check passes. Any parameter drift — in the registered
file or the report — changes the hash and the gate refuses.

## Provenance model

Each translated report carries three provenance layers:

1. `data_provenance` — where the *evidence* came from (source file,
   `evaluated_at` 2026-09-27, evaluator `trade-overfit`, framework,
   pre-registration reference, `n_trials`).
2. `translation` — the translation event itself (translator name and
   version, source schema version, `translated_at`,
   `numbers_recomputed: False`, `new_claims: []`).
3. `limitations` — the frozen known limitations from the
   pre-registration, plus the explicit `TRANSLATION` entry.

The *underlying evidence* keeps its 2026-09-27 evaluation date; only the
report envelope's `generated_utc` is "now", which is what the gate's
freshness check reads.

## Fail-closed behavior

The translator raises `EvidenceTranslationError` — refusing to emit a
report — when:

- the evidence `schema_version` is not 1,
- a gate entry lacks `name`, `value`, `threshold`, or a boolean
  `passed`,
- a gate name is not in the Tier-1 gate map (unknown gates are never
  guessed at),
- the gate list is empty.

A source gate with `passed: False` translates to `verdict: FAIL` and
`validation.status: FAIL`; the lifecycle gate then refuses promotion,
exactly as it would for a natively failing report.

## Regenerating the REGCOND-1 artifacts

```bash
cd trade-lifecycle
PYTHONPATH=src python3 -c "
from trade_lifecycle.evidence_translate import build_regcond1_report
out = build_regcond1_report(
    'tests/fixtures/tier1_evidence_regcond1.json',
    'docs/validation/regcond-1')
print(out['config_hash'])"
```

`tests/fixtures/tier1_evidence_regcond1.json` is a verbatim copy of the
canonical evidence (trade-strategies
`docs/validation/regcond-1/tier1_evidence.json`); the translator is
tested for field-by-field fidelity against it.

## Charlie's promotion path (unchanged, now unblocked)

```bash
trade-lifecycle register --id REGCOND-1 --name "Regime-conditional cross-asset tilt" \
  --family regime-macro \
  --config ~/workspace/trade-suite/trade-lifecycle/docs/validation/regcond-1/config.json \
  --policy-id <his-ips-id>

trade-lifecycle promote REGCOND-1 --to VALIDATED \
  --report ~/workspace/trade-suite/trade-lifecycle/docs/validation/regcond-1/validation-report-v1.json

trade-incubate start --strategy REGCOND-1 --preset balanced \
  --backtest-sharpe 1.385 --backtest-dd 0.23

trade-lifecycle promote REGCOND-1 --to PAPER --approver Charlie \
  --rationale "Paper incubation authorized 2026-09-28, see trade-lifecycle docs/approvals/REGCOND-1-paper-2026-09-28.md" \
  --enrolled

trade-lifecycle status REGCOND-1
trade-lifecycle history REGCOND-1
```

Step 2 was the blocked one; the translated report unblocks it
structurally. The transition itself remains his CLI action.
