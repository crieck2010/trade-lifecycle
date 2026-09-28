# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-09-28

### Added
- `evidence_translate.py`: Tier-1 evidence -> trade-swing
  ValidationReport (schema v1) translator. Rule: translation, not
  re-validation — same numbers, same verdicts, zero new claims; every
  mapped field traces to a source field; unavailable fields are `null`
  with explicit notes, never invented. Unknown gates, missing fields, or
  wrong evidence schema raise `EvidenceTranslationError` (fail closed).
  Config binding reuses the lifecycle's own `config_hash` (no new
  hashing convention). Emitted reports carry a `translation` provenance
  section (source file, source evaluation date, `numbers_recomputed:
  False`).
- `frozen_config_regcond1()` + `build_regcond1_report()`: the canonical
  machine config transcribed from the frozen pre-registration, and the
  artifact builder for REGCOND-1.
- `docs/validation/regcond-1/`: `config.json` (pass to `trade-lifecycle
  register --config`) and `validation-report-v1.json` (pass to
  `trade-lifecycle promote --to VALIDATED --report`). Verified:
  `gate_research_to_validated` accepts the translated report
  structurally (`passed: True`, no reasons).
- `docs/EVIDENCE_TRANSLATION.md`: the two evidence formats, the
  field-mapping table, the provenance model, and the config-binding
  maths. README section added.
- `tests/test_evidence_translate.py` (15 tests): field-by-field
  round-trip fidelity against the real `tier1_evidence.json` (verbatim
  fixture), provenance audit, config-hash binding (report == on-disk
  config == frozen config), lifecycle gate acceptance, tamper refusal,
  and fail-closed translation errors.

## [0.1.0] - 2026-09-24

### Added
- Initial release: the investment committee in code.
- `lifecycle.py`: strict state machine RESEARCH → VALIDATED → PAPER →
  LIVE → RETIRED, no skipping; PAUSED as an overlay; RETIRED terminal.
- `gates.py`: fail-closed guards — validation report (all gates PASS,
  fresh, config-hash bound), human approvals with rationale, incubation
  enrollment, graduation, two-person rule for LIVE, mode authorization,
  policy-file checksum.
- `registry.py`: append-only JSONL event log; state derived by replay;
  every refused attempt logged with actor, timestamp, and reasons.
- `policy.py`: minimal investment-policy hooks (`<policy_id>.md`,
  SHA-256 checksums).
- `adapters.py`: lazy, fail-closed sibling bridges (trade-swing,
  trade-incubate) with test/demo injection.
- `presets.py`: strict / balanced / lenient gate profiles.
- `demo.py`: seeded four-strategy theater (A→LIVE, B refused, C paused,
  D retired).
- Full CLI: register, promote, status, history, pause, resume, retire,
  demo, presets, license, update-check. Refusals exit non-zero.
- Docs: README (with "The maths"), ARCHITECTURE, METHODOLOGY,
  LIFECYCLE.md (the fund's constitution), example.
