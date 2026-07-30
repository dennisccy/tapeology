# Phase goal-desk-iter-23 — User-Visible Changes

**Phase:** goal-desk-iter-23
**Date:** 2026-07-30
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see, for every ranked row on the `/desk` briefing table, exactly how many price
  levels the row's selected wall (its "band") is actually built from — e.g. "155 levels" — instead
  of only the wall's price range, class, distance, and score.
- Users can now see the per-timeframe breakdown of those levels on the same row — e.g. "1d 68 · 1h
  57 · 4h 19 · 1w 11" — showing whether a wall is confirmed mostly by daily touches, mostly by
  intraday (1m/5m) touches, or a mix, without leaving `/desk` and cross-referencing `/structure`.
- Users can now see a "round number" badge on any `/desk` row whose selected wall sits at a
  round-number price — the exact same badge `/structure`'s own band table already shows for the
  identical band — directly in the ranked list instead of only on the drill-in page.
- Users can distinguish two rows that read identically on every other column (e.g. both "support ·
  Class A · 0.00 bps") by how thick their evidence actually is — one row's wall might be a single
  touch, another's might be 600+.

---

## What Changed in the Visible UI

- The `/desk` ranked-rows table now has one new column, `levels`, positioned after the existing
  `opposite` column (rightmost column in the table).
- Each populated row's `levels` cell shows a tally string in the format `${count} levels ·
  ${timeframe} ${count} · ${timeframe} ${count} ...` (e.g. `155 levels · 1d 68 · 1h 57 · 4h 19 · 1w
  11`), followed by a small bordered "round number" badge when that row's wall sits at a round
  number.
- The table header row gains a new `levels` header cell alongside `symbol`, `side`, `band class`,
  `distance`, `score`, `coverage`, `tick evidence`, `basis`, `history`, `band`, and `opposite`.
- No new page, no new section, and no navigation change — the change is confined to one additional
  column on the existing ranked table.

---

## What Old Behavior Changed

None. This is a pure addition. Every existing `/desk` column (symbol, side, band class, distance,
score, coverage, tick evidence, basis, history, band, opposite), the row ranking order, the
screen-history list, the skipped-members section, the provenance line, and the Run Screen / Top-up
/ Reconcile Index controls behave exactly as before. No existing field's value, label, or position
changed.

---

## Not Visible Yet

- Screens computed BEFORE this update (every screen currently recorded in the ambient environment —
  confirmed live: the current `/desk` "latest" screen, `screen-2026-07-20-ca185294a384`, was
  recorded before this change and its rows do not carry the three new fields) will continue to show
  the honest fallback text "composition not recorded in this snapshot" in the `levels` column
  forever — these snapshots are append-only and are never rewritten or backfilled. Only a screen
  computed AFTER this change (via the "Run Screen" button, for a `screen_date` not already
  recorded) will show the populated tally and badge.
- Nothing else is backend-only: the three new fields (`band_member_count`, `band_round_number`,
  `band_member_timeframes`) are computed on the existing `GET /research/desk/screen` endpoint and
  are fully wired into the `/desk` page in this same iteration.
