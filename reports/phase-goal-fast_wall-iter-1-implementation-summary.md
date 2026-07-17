# goal-fast_wall-iter-1 — Implementation Summary

**Phase:** goal-fast_wall-iter-1
**Date:** 2026-07-17
**Written by:** developer

---

## Features Implemented

- **The Structure page no longer risks hanging your machine.** Opening the Structure page's Edge
  Report section used to be dangerous the first time it hadn't been pre-computed: it would
  silently start a multi-hour number-crunching job on your machine in the background of that page
  load, pinning the backend at very high CPU for hours and slowing down every other part of the
  app while it ran. That is now fixed. Opening the page (or asking the backend for the report
  directly) always answers in well under a minute — usually instantly — no matter what state the
  report is in.
- **An honest "not computed yet" message.** When the report genuinely hasn't been calculated yet,
  the page now says so plainly: "Edge report not computed yet," with a short explanation of why.
  Previously you'd either see an endless spinner or, worse, silently trigger the hours-long job
  described above without any warning.

## Changed Behavior

- **Opening `/structure`'s Edge Report section**: Previously, if the report had never been
  computed, simply loading the page would kick off the full multi-hour research calculation in the
  background — an invisible, expensive side effect of just looking at a page. Now, loading the
  page never starts that calculation. It either shows the already-computed report (if one exists)
  or an honest "not computed yet" notice. The calculation itself is not available to trigger from
  the app yet in this update — that comes in a following update.

## Backend-Only Items

- The machinery to run the report calculation on demand and save the result for later
  (`compute_and_publish`, in developer terms) is built and tested, but there is no button or
  command yet that a user or operator can click/run to actually trigger it. It is wired up and
  ready for the next update, which will add the actual "Compute edge report" button on the page
  plus a command-line option for running it in the background. Until that next update ships, there
  is no way to make the report finish computing through the app — it will keep showing "not
  computed yet."

## Incomplete Items

- **The "Compute edge report" button** (and the equivalent command-line tool) that will let an
  operator actually run the calculation: not built yet. This was intentionally left for the next
  update in this series — this update's job was specifically to stop the risky automatic
  triggering, not yet to add the manual way to run it.
- **Making the page load faster overall**: this update only fixes the Edge Report section
  specifically. Other slow parts of the Structure page (loading the list of recorded data, and
  loading the Case Studies section) are not sped up yet — those are planned for later updates in
  this same series.

## Config and Environment Changes

- None. No new settings were added, and nothing existing was renamed or moved. The one file path
  the report's saved results live in (an internal cache file) now uses one shared, cleaner internal
  method to figure out where it lives, but the actual location on disk is unchanged from before.

## Known Limitations

- On the real, full dataset (not a test/demo dataset), asking for the report still takes about 30
  seconds to answer — because listing what data has been recorded is itself slow today (a separate,
  already-known issue planned for a future update). 30 seconds is a large improvement over "hours,"
  but it is not yet instant. It will become near-instant once that separate listing speedup ships.
- The Case Studies section of the Structure page can still take several minutes to finish loading
  on the real dataset — that is a pre-existing, already-known slowness in a different part of the
  page, unrelated to this update, and is scheduled to be fixed in a later step of this series.
- Nothing about the actual research numbers changed. Every level, band, backtest result, and dollar
  figure the app has ever shown is computed exactly the same way as before — this update only
  changes when and how often those calculations are allowed to run, never what they calculate.
