# Iteration 22 — Implementation Summary

**Phase:** goal-rapid-microscope-iter-22
**Date:** 2026-08-20
**Written by:** developer

---

## Features Implemented

- **Study 1 (range-wall failed aggression) can now be run by an operator.** A new request value
  (`range_wall_failed_aggression_pilot`) on the existing "run a screening pass" action — usable
  either from the command line or from the same background-job trigger the product already uses —
  runs this predeclared research question against the recorded tape and records its answer
  (survive / kill, with a stated reason) in the same trial ledger the product already shows.
- **Study 3 (capitulation exhaustion) can now be run by an operator**, the same way, via a second
  new request value (`capitulation_exhaustion_pilot`).
- **Every study now also records its own "is there enough independently-verified evidence yet"
  check** as a second, visible entry alongside its main answer — honestly reporting "not yet" today
  (the product has zero confirmed-independent trading sessions on record so far), rather than
  silently skipping that check.

## Changed Behavior

- **None.** The existing default screening run (the wide, general-purpose scan the product already
  ran) behaves exactly as before — same number of results, same shape. The one study that was
  already wired up last round (delta-divergence) behaves exactly as before too. This round is
  purely additive: two more research questions became runnable through the same door.

## Backend-Only Items

- None this round — both new request values are reachable through the SAME already-shipped
  trigger surface (the CLI warmer and the compute-trigger action on `/desk`), and their results
  render through the SAME already-shipped Scout Ledger / Walk-Forward table on `/desk`. No new UI
  screen, button, or field was needed or added — the table already displays any study's rows
  generically.

## Incomplete Items

- **Study 1's real question is still asked in a simplified, single-signal form.** The full research
  question described in the project's goal document asks whether AGGRESSIVE buying/selling into a
  price wall, TOGETHER WITH a specific liquidity signature on the opposite side, predicts a
  rejection. Only the first half (the aggression signal alone) is actually screened this round —
  the second half (the liquidity co-occurrence) is machinery that has never been built, and this
  round does not build it. This was already disclosed as deliberately deferred in the prior round
  and remains disclosed, not silently narrowed.
- **No real run against the operator's actual recorded tape happened this round** — every proof
  that the new capability works ran against small, hand-built test data, plus a quick live check
  that the running product's new option is wired up correctly (without actually letting it churn
  through the full recorded history, which is known to be slow and was explicitly out of scope to
  fix or trigger this round).

## Config and Environment Changes

- None. No new environment variable, no new configuration field, no schema change.

## Known Limitations

- Running either new study against the FULL real recorded history (rather than test data) is known
  to be slow today (a pre-existing, previously-identified limitation, not something this round
  introduced or worsened) — fixing that speed issue was explicitly excluded from this round's work.
- An operator who types an unrecognized study name into the trigger request gets a generic server
  error rather than a friendly validation message — a pre-existing, known, and explicitly
  out-of-scope rough edge, unchanged this round.
- Every number either study produces continues to carry its "how sure can I be" label (its evidence
  class) exactly as before — nothing about this round changes how trustworthy any number is, only
  which questions can now actually be asked and answered on the record.
