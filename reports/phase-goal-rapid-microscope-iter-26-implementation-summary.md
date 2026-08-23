# goal-rapid-microscope-iter-26 — Implementation Summary

**Phase:** goal-rapid-microscope-iter-26
**Date:** 2026-08-23
**Written by:** developer

---

## Features Implemented

- **Faster "desk readiness" loading, second time onward**: the "Microscope Readiness" panel's
  band-touch figure (part of the joinable-corpus count shown under Readiness) is now backed by a
  small on-disk cache. The first time this figure is computed for a given dataset and band map, it
  is stored; every later request for that same combination is served instantly instead of
  re-scanning the raw tick data. Nothing the operator sees on the page changes — the numbers stay
  exactly the same — only how quickly the page gets there after the first load.

---

## Changed Behavior

- **Desk readiness — Scout pilot-study wiring**: Previously, the code deciding which of the three
  pilot studies needs which supporting data (a band map vs. a playbook lookup) kept a second,
  hand-typed copy of that list next to the one real list. Now there is exactly one list, and the
  decision logic reads it directly every time. Nothing visible changes — this is an internal
  cleanup that removes a place a future edit could have silently gone out of sync.
- **Desk readiness — response speed**: Previously, every load of the readiness figure that needed
  the band-touch count re-scanned the raw recorded tick data for every relevant dataset, which
  keeps getting slower as more tick data is recorded (already tens of minutes on the full real
  archive). Now, after the first scan, later loads for the same data are near-instant. The numbers
  shown are unchanged either way.

---

## Backend-Only Items

None — this iteration touches only an existing endpoint's internal speed and an internal code
cleanup; there is no new endpoint or capability without UI wiring.

---

## Incomplete Items

- **Referee disclosure item (deferred by design)**: the prior iteration's evaluator flagged a
  fourth item — disclosing that one Referee-owned readiness figure can go stale — as safe to fix
  but explicitly said it may be dropped under time pressure ("drop 4 and 5, never 1"). This
  iteration deliberately does not build it, per the phase spec's own scope boundary, to avoid
  bundling two independently risky backend changes in one pass. It remains open for a future
  iteration.
- Two owner-owned items noted in prior iterations (a data-lineage gap in one internal ledger, and
  a money-floor configuration question) remain open — they require an operator decision, not
  developer judgment, and were not touched this iteration.

---

## Config and Environment Changes

- `TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB` — optional environment variable pointing the new cache's
  storage file to a custom location. Default (when unset): a file named
  `micro_band_touch_cache.db` stored next to the existing dataset folder — no operator action is
  required for normal use.
- No changes to the application's `Config` class, no schema migration, and no change to the
  product's version fingerprint (`08e471b10130e1e2`, unchanged).

---

## Known Limitations

- The new cache only speeds up REPEAT loads of the same dataset-and-band-map combination. The
  very first load for a given combination still pays the full scan cost — this iteration reduces
  ongoing cost, not the one-time warm-up cost.
- This iteration's speed improvement was verified against the automated test suite (using small,
  synthetic test data) and via direct code review, not by manually timing a live request against
  the full real tick archive (which currently holds far more data than originally recorded at the
  start of this project chapter, making a full "before/after" timing run itself a multi-minute
  operation). The QA pass that follows this handoff is expected to verify the on-screen numbers
  are unchanged using the standard browser-testing rig.
- No screen, page, or navigation changed. If you load `/desk` before and after this change, it
  should look and read identically — the only difference is how quickly the readiness numbers
  populate on a repeat visit.
