# METHODOLOGY — trade-lifecycle

## What this module is

An investment committee rendered as a state machine. Real funds separate
*idea generation* from *capital allocation* with a formal process; this
module is that process, executable. It answers one question at each
stage boundary: "has this strategy earned the next stage?"

## The stages

- **RESEARCH.** Ideas live here. Nothing is promised. A strategy enters
  the registry here with its config hash bound at birth.
- **VALIDATED.** The strategy survived the overfit gates
  (trade-overfit via trade-swing): deflated Sharpe, walk-forward,
  drawdown, worst-regime, net excess — all PASS, on a fresh report, for
  the *registered* config. Validation is evidence, not a prediction.
- **PAPER.** A named human approved paper trading with a written
  rationale, and the strategy is enrolled in the incubation harness
  (trade-incubate). Paper is where the strategy meets reality without
  risking capital.
- **LIVE.** Incubation graduated, a *second* human approved, the
  autonomy mode (`supervised` / `autonomous`) was explicitly authorized,
  and the investment-policy file's checksum was recorded. This is the
  only stage where capital is at risk, and it is the hardest to reach
  by design.
- **RETIRED.** Terminal. Strategies die with a written reason —
  superseded, decayed, never worked. The dead teach the living if their
  obituaries are honest.
- **PAUSED (overlay).** Kill conditions or humans halt a strategy
  without erasing its stage. Resume requires re-approval.

## Why the guards are shaped this way

- *Validation bound to config hash.* Prevents the most common quiet
  fraud in strategy research: validating one parameter set and trading
  another. The hash makes bait-and-switch structurally visible.
- *Freshness limits.* Evidence decays. A 2023 validation does not
  authorize 2026 capital.
- *Two humans for LIVE.* No single person should be able to take a
  strategy from paper to live money alone — including the person who
  built it.
- *Mode as part of the approval.* Authorizing "live" is ambiguous;
  authorizing "live, supervised" vs "live, autonomous" is a real
  decision. The mode switch from trade-regime's DECISION_LOOP.md is
  recorded here, not assumed later.
- *Refusals logged.* The committee's "no" is as much a decision as its
  "yes" and gets the same archival treatment.

## What this module deliberately does not do

- It does not evaluate strategy quality beyond the gates' paperwork.
- It does not execute, size, or route anything.
- It does not replace the human: every forward step past RESEARCH
  requires a named human with a written rationale. The machine enforces
  the *process*; the human supplies the *judgment*.
