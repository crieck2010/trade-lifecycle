# Changelog

All notable changes to this project will be documented in this file.

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
