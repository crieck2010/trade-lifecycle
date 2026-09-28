# Approvals ledger — human authorizations

This directory holds durable, timestamped records of human approvals that the
`trade-lifecycle` state machine requires but does not itself originate:
paper-incubation authorizations, live-trading authorizations, pause/resume
rationales issued out-of-band (chat, phone, in-person).

## Why this exists

The lifecycle registry (`~/.trade-lifecycle/registry.jsonl` by default) is the
system of record for *executed* transitions — an approval is attached to the
`promote` event when it runs. But the approval itself is granted by a human,
often in a different medium (chat) and sometimes well before the CLI command
runs. This directory preserves the approval verbatim so the later
`--approver` / `--rationale` flags can be shown to trace back to the human's
actual words, not someone's paraphrase months later.

## Format

One file per approval: `<STRATEGY-ID>-<kind>-<YYYY-MM-DD>.md`, where `<kind>`
is `paper`, `live`, `pause`, `resume`, or `retire`.

Each file MUST contain, verbatim where quoted:

| Field | Meaning |
|---|---|
| `strategy_id` | Lifecycle registry id of the strategy |
| `approval_type` | What is authorized (e.g. `paper incubation` = VALIDATED → PAPER) |
| `granted_by` | Human who granted it, as they identify themselves |
| `granted_via` | Medium: `chat`, `phone`, `in-person`, `email` |
| `date` | Calendar date of grant (user's timezone, America/New_York) |
| `verbatim` | The human's exact words authorizing it — never paraphrased |
| `scope` | What the approval authorizes, and explicitly what it does NOT |

Rules:

- Never invent a rationale. If the human gave none beyond the approval
  itself, say so; the `promote` command's `--rationale` flag is the
  operator's to fill, referencing this record.
- Never forge fields. A record contains only what the human said plus
  mechanical metadata (date, medium).
- A record here does NOT execute the transition. Lifecycle transitions
  remain the human's CLI action (`trade-lifecycle promote ...`).
- Machine-readable summary: each file ends with a fenced `approval.json`
  block carrying the same fields, so tooling can parse what humans can read.
