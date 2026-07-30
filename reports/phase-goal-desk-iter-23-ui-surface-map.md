# Phase goal-desk-iter-23 — UI Surface Map

**Phase:** goal-desk-iter-23
**Date:** 2026-07-30
**Written by:** ui-impact-analyst

---

## File Classification

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/research/desk_screen.py` | backend-api | indirect → direct (consumed same iteration) | Ranked-row builder inside `compute_screen` now copies `band_member_count`/`band_round_number` verbatim off the existing `_select_best_band` return and adds a new `_band_member_timeframes` helper for the tally. Served unchanged via the existing `GET /research/desk/screen` route — no new route. Frontend consumes it this same iteration (see `page.tsx` below), so this is UI-visible, not "not visible yet". |
| `apps/backend/tests/test_desk_screen.py` | backend-internal (test) | none | Golden/invariant/call-count/rank-order/legacy-row tests for the new fields. No UI impact — verifies the backend contract only. |
| `apps/frontend/lib/types.ts` | frontend-direct | direct | `DeskScreenRow` interface gains three new optional fields (`band_member_count?`, `band_round_number?`, `band_member_timeframes?`) consumed directly by `page.tsx`'s new cell. Type-only change with no runtime UI by itself, but it is the contract the rendered column depends on. |
| `apps/frontend/app/desk/page.tsx` | frontend-direct | direct | `DeskRow` gains a new `<td data-testid="desk-row-levels">` cell; `DeskRowsTable`'s header row gains a new `<th>levels</th>`. This is the actual rendered UI change. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `DeskRowsTable` header row (`<th>levels</th>`) | Updated layout | New column header added beside `band`/`opposite` for J-15 wall-composition disclosure | Navigate to `http://localhost:3301/desk`; in the ranked table's header row, confirm a `levels` header cell appears immediately after the `opposite` header cell, before the row body starts |
| `/desk` | `DeskRow` — new `<td data-testid="desk-row-levels">` cell, populated state | New table column | Row now discloses `band_member_count`/`band_member_timeframes` as a tally string for any row from a screen computed after this change | On a row from a NEWLY computed screen (post-iteration `screen_date`), confirm the `levels` cell text matches the pattern `<N> levels · <tf> <n> · <tf> <n> ...` (e.g. `155 levels · 1d 68 · 1h 57 · 4h 19 · 1w 11`) and that the sum of the per-timeframe counts equals the leading `<N> levels` number |
| `/desk` | `DeskRow` — round-number badge (`data-testid="tradable-band-round-number"`) inside the `levels` cell | New component (reused) | Row discloses whether its selected wall sits at a round number, reusing `/structure`'s exact badge markup | On a row whose band is a round number, confirm a small bordered badge reading exactly "round number" appears to the right of the tally text inside the same `levels` cell; on a row whose band is NOT a round number, confirm the badge is absent (no empty badge shell rendered) |
| `/desk` | `DeskRow` — `levels` cell, legacy-absent state | Changed behavior (honest-absence copy) | A screen computed before this iteration never carries the three new fields; the cell must render the established honest-absence copy instead of a blank cell or a computed fallback | Load `/desk` with a screen recorded before this change selected (the current ambient "latest" screen, `screen-2026-07-20-ca185294a384`, is one such case as of this writing), or use the screen-history list to select any pre-iteration date; confirm every row's `levels` cell reads exactly "composition not recorded in this snapshot" |
| `/desk` | `DeskRow` — anchor `title` tooltip on the row's `symbol` cell (`deskRowDrillInTitle`) | No change (verify absence of change) | Spec explicitly requires NO new tooltip line for this iteration (all three new values are exact, unrounded) | Hover over the `symbol` cell of any ranked row and confirm the composite tooltip text is unchanged from before this iteration — it does NOT mention `band_member_count`, `band_round_number`, or `band_member_timeframes` |
| `/desk` | `DeskRow` — existing columns (`band`, `opposite`, `basis`, `history`, `score`, `distance`, `coverage`, `tick evidence`, `side`, `symbol`) | Regression check (unchanged) | Pure-additive change; every prior column must render identically to before | Confirm all ten pre-existing columns render their prior values/format unchanged and the new `levels` column does not shift or truncate any of them |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_desk_screen.py` — golden/invariant/call-count/rank-order/legacy-row test
  additions verifying the new fields' correctness and the zero-extra-compute guarantee — no UI
  surface affected (test-only file).
- `desk_screen.py`'s module/`compute_screen` docstring updates (the new "Wall-composition
  disclosure" section) — developer-facing documentation only, no UI surface affected.

<!-- All production code changes in this iteration have direct UI impact; nothing shipped this
     iteration is a backend capability without a corresponding UI surface. -->

---

## Summary

- **Frontend surfaces changed:** 1 (`/desk` ranked table)
- **New pages/routes:** 0
- **Modified components:** 2 (`DeskRow`, `DeskRowsTable` — both in `apps/frontend/app/desk/page.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 0 production files (test file + docstrings only, no UI-relevant logic)
