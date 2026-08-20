# goal-rapid-microscope-iter-19 — Implementation Summary

**Phase:** goal-rapid-microscope-iter-19
**Date:** 2026-08-20
**Written by:** developer

---

## Features Implemented

- **Deterministic-rerun proof for the three era computations**: a new backend test module proves
  that running the snapshot builder, the Scout screener, and the walk-forward fold evaluator a
  second time — over the exact same recorded data — produces the exact same numbers every time
  (same effect sizes, same p-values, same disclosures). This closes the last open item on J-10
  ("The kept product stands"), one of this era's ten Must-have journeys.
- **Four regression-check scripts made discriminating**: four of this era's automated
  browser-replay scripts (J-02 through J-05) previously only checked that the Desk page loaded at
  all — they would have "passed" even if the Rapid-Microscope sections they are supposed to be
  guarding were completely broken. Each now opens its own section and checks a real, specific
  piece of text that only appears when that section's data actually loaded correctly.
- **A durable record of which test database a QA pass used**: the script that stands up a
  scoped, disposable backend for browser testing now writes a small report file recording exactly
  which folders/databases that test run was pointed at. This lets anyone reading a later QA report
  verify the claim "this was tested against a safe, isolated store" instead of having to take it
  on faith.

## Changed Behavior

None. This iteration is test-and-harness-only — no page, button, endpoint, or served number
changed. The Desk page renders identically to before this iteration.

## Backend-Only Items

None — nothing new is served to the UI or MCP this iteration.

## Incomplete Items

None from this iteration's own scope. Carried forward from the era, unchanged and explicitly out
of scope this round (per the phase spec):

- **J-09 "The pilot studies"** — still blocked on an owner ruling about the sealed judge's
  economic-floor/evidence-label sourcing (no revision landed in the spec as of this iteration).
- **J-06 step 4 (real Alpaca tranche recording)** — still an operator-owned act, not run this
  iteration.

## Config and Environment Changes

None. No new environment variable, config field, or migration. The QA launcher script's existing
`TAPEOLOGY_*` environment variables are unchanged; the script now additionally WRITES a report
file (`reports/qa-scoped-backend-store-manifest.md`) recording their resolved values at launch —
that file is generated output, not a new input.

## Verification

Full backend test suite: **3279 passed, 8 skipped, 0 failed, 0 errors** (3287 total collected),
run to completion after this iteration's changes — at or above the count recorded at the start of
this iteration, with zero regressions.

## Known Limitations

- The four deepened replay scripts assert text that the developer confirmed (by reading the
  frontend source and by querying the scoped-backend API directly) renders unconditionally once
  each section's data loads — but a live browser pass (the browser-qa-agent's job for this
  iteration) is what actually proves it on screen with a screenshot. No screenshot means "unknown,"
  never "passing," per this project's own standing evidence rule.
- The new manifest file always reflects the MOST RECENT time the QA launcher script was run.
  Anyone citing it must confirm it corresponds to the actual test pass being described, not a
  stale run from earlier testing.
