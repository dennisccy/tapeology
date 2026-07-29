# goal-desk-iter-14 — Implementation Summary

**Phase:** goal-desk-iter-14
**Date:** 2026-07-28
**Written by:** developer

---

## Features Implemented

- **Index Reconciliation**: on the `/desk` page, a new "Reconcile Index" button lets the operator
  fix a specific kind of bookkeeping drift: the app keeps a fast lookup table (an "index") that
  tracks which price history it has stored for each stock and timeframe. Occasionally that lookup
  table can fall out of sync with the actual stored files — for example a price series was
  recorded but never got listed in the lookup table, so the app "forgets" it has that data even
  though the file is sitting right there. Clicking "Reconcile Index" rebuilds the lookup table from
  the real files on disk, with live progress and a cancel option, and shows exactly what was wrong
  before and what got fixed.
- **Index Reconciliation history**: a new read-only "Index Reconciliation" panel on `/desk` (beside
  the existing "Top-up Runs" panel) keeps a permanent record of every reconciliation that was ever
  run: when it ran, how many price files exist on disk, how many were in the lookup table before
  and after, exactly which stock/timeframe pairs were affected, and any files that turned out to
  be damaged. Nothing is ever overwritten — every run adds a new, permanent entry.

## Changed Behavior

- **The "coverage" badges on the Desk briefing table** (the small colored tags next to each ranked
  stock showing which timeframes have price data) previously had no way to be corrected if they
  were wrong. They still work exactly the same way — read the same lookup table as before — but
  now that lookup table can be repaired with one click when it drifts out of sync, instead of
  silently staying wrong forever.

## Backend-Only Items

None — every new capability has a corresponding button/panel on `/desk`.

## Incomplete Items

- **The official "before" and "after" screenshots proving this works in a real browser have not
  been captured yet.** This is intentional, not a gap: once a real reconciliation run happens on
  the test environment, the "before" (nothing has ever been reconciled) state can never be shown
  again on that same environment — it's a one-time-only view, like a photo that can only be taken
  once. This developer prepared everything needed (planted a realistic example of the drift, set
  up a test environment, confirmed via direct inspection that the button, the dark badge, and the
  "nothing recorded yet" message all render correctly) and then deliberately stopped, so the next
  QA step can take that one-time "before" photo first, then run a real reconciliation and take the
  "after" photo. Both photos are the very next step, not weeks away.
- No command-line tool was built for triggering a reconciliation from a script (unlike the earlier
  "top up bars" feature, which has both a button and a command-line option). The button on `/desk`
  is the only way to trigger it. This was a deliberate scope decision, not an oversight — the
  planning document for this feature never asked for a command-line version, since a reconciliation
  is fast and local (it doesn't fetch anything from the internet), so the button already serves the
  role a command-line tool would.

## Config and Environment Changes

- No new configuration setting was added, and no existing one changed. (There is one optional,
  purely operational environment variable — `TAPEOLOGY_DESK_INDEX_RECONCILE_DIR` — that lets
  someone choose where the reconciliation history is stored on disk; it has a sensible default and
  nobody needs to set it for normal use.)
- No database migration — this feature stores its history as plain files on disk, the same way
  several other recent features already do.

## Known Limitations

- On the prepared test environment, only one deliberately-planted example of the "drift" problem
  exists (one stock's daily price data). The reconciliation logic itself is tested far more
  thoroughly than that — including a case where a stored file is actually damaged/corrupted — but
  those broader cases are proven with fast, automated checks rather than with a live screenshot,
  to avoid any chance of accidentally breaking the one clean example prepared for the screenshot
  step.
- Fixing a damaged/corrupted price file itself is out of scope for this feature — reconciliation
  only fixes the lookup table. A genuinely damaged file stays on disk untouched and is reported as
  a problem, the same honest way the app already reports other kinds of damaged files.
