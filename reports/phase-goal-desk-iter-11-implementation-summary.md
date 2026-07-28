# goal-desk-iter-11 — Implementation Summary

**Phase:** goal-desk-iter-11
**Date:** 2026-07-28
**Written by:** developer

---

## Features Implemented

- **Top-up run history on the Desk page**: every time you click "Top-up" on `/desk` to fetch fresh
  bars for the tracked symbols, the outcome of that run is now saved permanently. Before this
  change, that information disappeared the moment you started a new top-up run — there was no way
  to look back and see what an earlier run actually did. Now `/desk` shows a new "Top-up Runs"
  panel listing every run that has ever completed: its date, an id, whether it finished normally,
  was cancelled, or failed, and how many symbol/timeframe pairs it attempted out of the total.
- **Failure detail on the most recent run**: for the latest top-up run, the panel also shows a
  breakdown of how many pairs were reused (already had data), freshly fetched, or failed — and for
  any pair that failed, the exact error message is shown in full, plus an honest count of any pairs
  the run never got to (e.g. because it was cancelled partway through).
- **Nothing is invented or guessed**: if no top-up run has ever been completed, the panel says so
  plainly ("No top-up runs recorded yet.") instead of showing a blank or misleading screen.

---

## Changed Behavior

- None. Every existing button, page, and API response continues to behave exactly as before. This
  is a pure addition — a new panel that shows information that already existed in memory during a
  run, now saved so it survives past that run.

---

## Backend-Only Items

- None. The new backend endpoint (`GET /research/desk/topup/runs`) is fully wired to the new panel
  on `/desk` described above.

---

## Incomplete Items

- **Live vendor verification**: the mechanism was proven using simulated (fixture) data only, per
  this iteration's own plan — a real ~100-symbol top-up run against the live data vendor is a
  separate, explicit action for you (the operator) to run whenever you choose; it is not something
  this pipeline runs automatically.
- **Browser screenshots**: the visual verification of this new panel in an actual browser (both the
  "no runs yet" state and a populated state with a failure shown) happens in the next pipeline step
  (browser testing), not in this implementation step.

---

## Config and Environment Changes

- One new optional environment variable: `TAPEOLOGY_DESK_TOPUP_LOG_DIR` — lets you point the new
  run-history storage at a custom folder. If not set, it defaults automatically to a folder next to
  where the existing universe/screen data already lives, so no action is needed for normal use.
- No changes to any existing settings, and no change to the app's internal "fingerprint" (the
  built-in check that proves nothing about how results are calculated has silently changed).

---

## Known Limitations

- The history list only shows summary information (date, id, status, how many pairs were
  attempted) for older runs — the full pair-by-pair breakdown (which symbols succeeded/failed) is
  only shown for the most recent run. This matches how the same page already shows detailed screen
  results only for the currently selected screen, not every screen ever run.
- This panel is read-only — there is no button to retry a failed pair or re-run a past top-up from
  this panel. You still use the existing Top-up button to start a new run.
