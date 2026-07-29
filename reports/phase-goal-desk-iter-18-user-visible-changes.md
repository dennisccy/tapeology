# Phase goal-desk-iter-18 — User-Visible Changes

**Phase:** goal-desk-iter-18
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On the `/desk` page's ranked screen table, users can now see — for every row computed by a screen
  run from this iteration forward — the nearest wall on the OTHER side of price from the one the row
  was ranked on (e.g. `opposite resistance A 490.88–494.22 · 0.6 bps`), in a new "opposite" column
  placed immediately after the existing "band" column.
- Users can now distinguish, at a glance, rows with a very close opposite-side wall (as little as a
  fraction of a percent away) from rows where the opposite wall is far away (potentially thousands of
  basis points), a spread that was previously invisible because every row only ever showed the one
  band it was ranked on.
- By hovering over any ranked row (the existing drill-in tooltip), users can now also see a full
  per-class breakdown of every wall the instrument found for that symbol — e.g.
  `bands by class A 10 · B 0 · C 0 · unclassified 0` — giving context for how many candidate walls
  (of each class) the row's own displayed wall was chosen out of.
- No new button, control, page, or navigation entry was added — both pieces of information are
  read-only additions to the table row and its existing tooltip.

---

## What Changed in the Visible UI

- The `/desk` ranked-rows table grows from ten columns to eleven: a new "opposite" `<th>`/`<td>`
  column appears after the existing "band" column, on every row.
- The new "opposite" cell shows one of three distinguishable states:
  - A populated opposite wall: `opposite <side> <class> <price low>–<price high> · <distance> bps`.
  - An honest `"no band on the other side"` when the instrument found no wall at all on that side of
    price (a genuinely recorded `null`, not a missing value).
  - An honest `"opposite wall not recorded in this snapshot"` for any row from a screen snapshot
    recorded before this iteration shipped (the field is absent, not blank or zero).
- The row's existing composite hover tooltip (already shown on drill-in) gains one additional line
  carrying the full-precision `bands_by_class` breakdown (or `"bands by class not recorded in this
  snapshot"` for a legacy row) — no new per-cell tooltip was added; this line was folded into the
  same tooltip the row already exposes.
- No layout change beyond the one new column and one new tooltip line — same dense terminal-style
  table styling, same rounded-number display convention as the neighboring `distance`/`score`/`band`
  cells.

---

## What Old Behavior Changed

- None. Every existing column, its rounding, its data, and the rest of the composite tooltip's
  existing lines (distance, score, basis, history, band, coverage) are unchanged. This phase is
  purely additive to the row's display.

---

## Not Visible Yet

- The new "opposite" column and `bands_by_class` tooltip line will show real, populated data ONLY
  on screen snapshots computed from this iteration forward. Every screen snapshot recorded before
  this iteration (which, as of this handoff, is every snapshot currently sitting in the live/ambient
  data store) will continue to show the honest "not recorded in this snapshot" fallback text on
  every row, forever — those older records are never rewritten or backfilled.
- The opposite wall's own quality score (`band_score`) is available in the underlying data
  (`row.opposite_band.band_score`) but is intentionally not rendered anywhere in the UI this
  iteration — only side, class, price range, and distance are shown in the "opposite" cell. A future
  iteration could choose to surface it, but nothing today does.
- Live-browser evidence (an actual screenshot of the new column and tooltip populated with real
  near/far/null examples, plus a recorded walkthrough) was not part of this developer dispatch; per
  the dev handoff, that capture is downstream work for the browser-QA and demo-narrator lanes, since
  producing it requires computing a brand-new screen snapshot (out of scope for the developer's own
  dispatch, which is restricted from writing new snapshots to the live data store).
