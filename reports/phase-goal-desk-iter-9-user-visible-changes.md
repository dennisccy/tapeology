# Phase goal-desk-iter-9 — User-Visible Changes

**Phase:** goal-desk-iter-9
**Date:** 2026-07-27
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- See how many calendar days old the price reading behind a ranked row's distance/class
  measurement is, via a new **"basis"** column on every row of the `/desk` ranked-rows table (e.g.
  `"basis 2026-07-13 · 12 d before as-of"`).
- See the full-precision basis date and age by hovering anywhere on a ranked row — the row's
  existing hover tooltip now includes this detail alongside the distance/score/coverage information
  that was already there.
- When reviewing a screen recorded before this update (via the "Screen History" list), see an
  honest **"basis not recorded in this snapshot"** disclosure on every ranked row instead of a blank
  cell, a dash, or a guessed value.

---

## What Changed in the Visible UI

- The `/desk` ranked-rows table now has **8 columns instead of 7** — a new "basis" column is
  appended after the existing "tick evidence" column (order: symbol, side, class, distance, score,
  coverage, tick evidence, **basis**).
- The row's hover tooltip (the same consolidated tooltip covering the whole row, not a per-cell one)
  now contains one more segment: a `basis <date> (<N> d before as-of)` clause inserted between the
  existing "score" and "coverage" clauses.
- Opening a past screen through "Screen History" renders this same new column and tooltip content —
  real dates/ages for any screen computed from this iteration onward, the honest fallback text for
  anything recorded earlier. This is the same table component used for both the latest screen and
  history drill-through, so there is no separate/inconsistent rendering path.
- The skip-rows table (symbol/reason/coverage/tick evidence, shown for members the screen could not
  rank) is unchanged — it still has 4 columns; skip rows never carry basis data because a skip
  already means no basis was resolved.

---

## What Old Behavior Changed

- **Ranked-row hover tooltip:** previously read `"distance X bps · score Y[ · coverage...]"`. It now
  always reads `"distance X bps · score Y · basis <detail or fallback>[ · coverage...]"` — the basis
  clause is new and always present, so the exact tooltip text is different even though nothing was
  removed. Anyone/anything (tests, muscle-memory) relying on the previous exact tooltip wording will
  see the added segment.
- No other existing behavior changed: the other 7 table columns, row sorting, the "Run Screen" /
  "Top-up" buttons, and the skip-rows table are byte-identical to before this iteration.

---

## Not Visible Yet

None — this is a fully wired, single-iteration feature. The two new fields (`basis_as_of`,
`basis_age_days`) are computed on the backend by `desk_screen.py` and rendered on `/desk` in the
same change set; nothing is backend-only. (As a side note, not a gap: the read-only `desk_screen`
MCP tool also now returns the two fields automatically, with zero code change, because it is a
byte-identical proxy of the same `GET /research/desk/screen` response.)

**Caveats carried into QA** (not gaps in the shipped feature, but unverified claims worth knowing
before signing off):
- The claim that the row's full-row hover anchor (not the new `<td>`) stays on top at the new basis
  cell's exact center point has not yet been confirmed with a real browser hit-test — the table
  gained a column, so cell centers moved.
- The dev pass observed a real basis-age spread of about 3–14 days on live data (not the literal
  "≤2 days and ≥10 days in one screenshot" example called for in the plan) — worth a fresh look at
  QA time in case a fresher row is available, or an explicit judgment call that the observed spread
  is legible enough as "fresh vs. stale."
