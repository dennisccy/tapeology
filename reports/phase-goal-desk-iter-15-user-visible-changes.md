# Phase goal-desk-iter-15 — User-Visible Changes

**Phase:** goal-desk-iter-15
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Operators can now see, for every ranked row on the `/desk` briefing, how many completed daily
  trading sessions (and from what start date) the row's "wall" measurement is based on — e.g.
  `history 500 sessions · from 2024-07-25` — without leaving `/desk` or opening `/structure`.
- Operators can now hover a ranked row's symbol/drill-in link to see the full-precision session
  count and start date in the existing composite tooltip, alongside the distance/score/basis/
  coverage details it already showed.

---

## What Changed in the Visible UI

- The `/desk` ranked briefing table gained a new **`history`** column, positioned immediately
  after the existing `basis` column (last column in the row).
- Each ranked row's composite hover tooltip (shown when hovering the row's symbol/drill-in
  anchor) gained one more line: `history <N> sessions from <full timestamp>`.
- Screen snapshots recorded **before** this iteration display the honest fallback text
  `"history not recorded in this snapshot"` in the new column instead of a value — never blank,
  never the literal word `"null"`.
- The skipped-members tables (`"Skipped — no bars"` / `"Skipped — no basis session"`) are
  structurally unchanged — they never had a history column and still don't; skip rows have no
  basis for the disclosure (they were never ranked).

---

## What Old Behavior Changed

- None. No existing column, button, link, click target, or navigation element changed. The one
  side effect is that the ranked table is now one column wider, which may shift the vertical
  position of content below it (the Top-up Runs and Index Reconciliation sections' own content is
  untouched).

---

## Not Visible Yet

- None. This is a fully wired disclosure feature — the backend computation
  (`history_sessions`/`history_start` in `apps/backend/app/research/desk_screen.py`) and the
  on-screen `/desk` column/tooltip shipped together in the same iteration; there is no backend
  capability here without a corresponding UI surface.
