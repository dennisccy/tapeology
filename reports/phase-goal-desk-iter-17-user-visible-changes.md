# Phase goal-desk-iter-17 — User-Visible Changes

**Phase:** goal-desk-iter-17
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see, for every ranked row on the `/desk` page, the exact daily closing price the
  row's tradable "wall" was measured against — directly in a new **band** column on the ranked
  table, without having to invert `distance_bps` arithmetic in their head to figure out whether the
  price sits inside the band.
- Users can now see the band's own price range (`price_low`–`price_high`) shown right next to that
  close price, in the same cell (e.g. `band 488.50–490.85 · close 490.85`).
- Users can now hover over (or inspect) a ranked row and see the same close/band detail rendered at
  full, untruncated precision inside the row's existing composite tooltip, alongside the
  distance/score/basis/history detail that tooltip already showed.

No new button, filter, control, or page was added — this is a read-only disclosure of a value the
backend was already computing internally but had never returned.

---

## What Changed in the Visible UI

- The `/desk` ranked-rows table grew from nine columns to ten: a new **band** header cell (labelled
  `band`) was appended after the existing `history` column.
- Every ranked row's new rightmost cell renders either:
  - `band <price_low>–<price_high> · close <reference_close>` (for a row belonging to a screen
    snapshot computed by the new code), or
  - the honest fallback text **"close not recorded in this snapshot"** (for a row belonging to any
    screen snapshot recorded before this iteration).
- The row's existing hover/drill-in tooltip text gained one more segment (full precision, not
  rounded) carrying the same close/band detail, appended after the existing basis/history segments.
- **Caveat for testers:** as of this iteration, every screen snapshot currently on record in the
  live/ambient data store predates this change. That means every row currently visible on the
  running `/desk` page shows the `"close not recorded in this snapshot"` fallback — not a populated
  example — until a brand-new screen is computed. The populated (`band <low>–<high> · close <val>`)
  state is verified by the backend's automated tests and was not yet captured live in a screenshot
  by the developer; see the Known Issues note in the dev handoff.

---

## What Old Behavior Changed

- None. This is a purely additive column and tooltip line — every other column, its data, and its
  ordering is unchanged. The existing `basis` and `history` disclosure columns (added in earlier
  iterations) behave identically to before.

---

## Not Visible Yet

- Nothing is backend-only in this iteration — the new `reference_close` field is fully wired into
  both the ranked table's `band` column and the row's hover tooltip in this same iteration.
- The one open item is evidentiary, not a missing UI wire-up: a live screenshot of a row whose close
  sits inside its band next to a row whose close sits outside it has not yet been captured, because
  no new screen snapshot has been computed since this code landed (see caveat above). The rendering
  logic for both cases is covered by backend tests, but an operator opening `/desk` today will only
  see the legacy fallback text until a new screen is run.
