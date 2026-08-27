# Phase goal-hypothesis-foundry-iter-5 — Implementation Summary

**Phase:** goal-hypothesis-foundry-iter-5
**Date:** 2026-08-27
**Written by:** developer

---

## Features Implemented

- **The real, frozen research epoch**: this iteration generated and permanently recorded (in Git)
  the one and only "real" pass of the Hypothesis Foundry's candidate registry for this research
  era. It looked at 11 specific research ideas from the project's own idea catalog (two previously
  parked studies, five microstructure "cards," and four already-excluded ideas), and for each one
  it recorded — mechanically, from the written rules, with no guessing — whether that idea could
  become a real testable trading hypothesis today, or whether it has to stay blocked because a
  scientific decision (a threshold, a direction, a missing rule) was never actually pinned down.
  The honest answer this round: **none of the 11 could become a real testable hypothesis yet** —
  every one is blocked, excluded, or marked as "this is just a stand-in, not the real idea" for a
  documented, specific reason. This is not a bug or a shortfall; it is the expected, allowed
  outcome when a research idea genuinely isn't finished being specified.
- **An independent second opinion before anything was locked in**: before committing this result
  to the permanent record, a separate, fresh reviewer (with no memory of how the first pass was
  built) checked every one of the 11 decisions against the original source documents. It found two
  small mistakes — a report field that was silently missing, and one decision's supporting note
  using an unsupported word — both of which were fixed before anything was committed.
  Its full review was also permanently recorded, side by side with the decisions it reviewed.
- **A new "Epoch / Manifest" screen on the Desk page**: operators can now open `/desk` →
  Hypothesis Foundry → Epoch / Manifest and see this real result directly — every one of the 11
  research ideas and its outcome, the permanent record's unique fingerprint, and a link to the
  independent review. It is visually marked in a different color from the four "practice"/test
  screens next to it, so nobody can mistake a real result for a rehearsal.
- **Two small display fixes on existing screens**: the "Sources / Compiler" screen now shows three
  extra pieces of context per research idea that were already being calculated but never actually
  shown; and it now shows both halves of a two-variant example instead of just one. The "Hermetic
  Oracles" (practice/test) screen now shows, side by side, which internal state each of its seven
  test scenarios reached, plus one extra statistical disclosure line.
- **One integrity cleanup**: a small piece of test-only code that was temporarily borrowing a
  scientific setting while the system was running for real users has been replaced with a cleaner
  approach that reaches the same test result without ever touching that setting live.

---

## Changed Behavior

- **The "Sources/Compiler" and "Epoch/Manifest" screens' underlying data now include your actual
  committed research decisions**, not just practice examples. Previously the summary line at the
  top of the Foundry panel always said "not yet generated" — it now reflects the real, permanent
  result once generated.

---

## Backend-Only Items

- None. Everything built this round has a corresponding screen on `/desk`.

---

## Incomplete Items

- **Running the actual research tests against real market data (the next step in this project's
  plan) was intentionally NOT done this round.** This round only decided which of the 11 ideas
  are even eligible to be tested — it did not run any test. That is deliberately saved for a
  later, separate step, so that the "which ideas are eligible" decision can never be influenced,
  even accidentally, by seeing how a test turns out first.
- The optional "read-only API tool" version of this new screen was not built — the project's own
  plan marks this as nice-to-have, not required.

---

## Config and Environment Changes

- None. No new settings, no new environment variables, no database changes.

---

## Known Limitations

- Because none of the 11 research ideas were ready to become a real testable hypothesis this
  round, the new Epoch/Manifest screen's "compiled results" list is currently empty — this is
  expected and correctly shown as an honest "nothing here yet" message, not an error.
- One statistical disclosure number shown on the practice/test screen (a "how surprising would
  this be by chance" line) turns out to vary slightly between the seven practice test scenarios,
  rather than being exactly the same for all seven as originally expected. The screen shows one
  real, non-invented example of that number rather than pretending all seven are identical.
