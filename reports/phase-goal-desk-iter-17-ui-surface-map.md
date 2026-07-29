# Phase goal-desk-iter-17 — UI Surface Map

**Phase:** goal-desk-iter-17
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `DeskRowsTable` header row (`apps/frontend/app/desk/page.tsx`) | Updated layout (new column) | J-13 discloses `reference_close` beside the row's own `price_low`–`price_high` band, closing the gap where the price was only recoverable by inverting `distance_bps` arithmetic | Navigate to `/desk`, wait for the ranked table to render, run `document.querySelectorAll('th')` (or read the header row visually) and verify it reads exactly 10 cells in order: `symbol, side, class, distance, score, coverage, tick evidence, basis, history, band` — `band` must be the last header cell |
| `/desk` | `DeskRow` ranked-row cell, `data-testid="desk-row-band"` (`apps/frontend/app/desk/page.tsx`) | New table column | Same as above — renders the row's own `reference_close` next to `price_low`–`price_high` | For a ranked row belonging to a screen snapshot recorded before this iteration (the current ambient/live store), verify the `band` cell's text is exactly `"close not recorded in this snapshot"`. For a ranked row belonging to a NEW screen snapshot computed after this change, verify the `band` cell's text matches the pattern `band <low>–<high> · close <val>` with three legible numeric values, with at least one visible row whose close falls inside its own `price_low`–`price_high` range and one whose close falls outside it, both in the same screenshot (per TC-6) |
| `/desk` | `deskRowDrillInTitle` composite hover tooltip (`apps/frontend/app/desk/page.tsx`) | Changed behavior (new tooltip segment) | Extends the row's existing composite drill-in tooltip with a full-precision `bandLine`, following the same pattern as the earlier `basisLine`/`historyLine` additions | Hover the mouse over a ranked row's drill-in anchor (or read its `title` attribute via `document.querySelector('[data-testid="desk-row-band"]')`'s parent row anchor) and verify the tooltip text includes a close/band segment appended after the existing distance/score/basis/history segments, at full (untruncated) precision — showing the fallback text for a legacy row or the numeric close/band values for a new-snapshot row |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_desk_screen.py` — new backend test coverage (golden per-row assertion,
  in-band/out-of-band cases, candles cross-check, byte-identical re-run, legacy-row absence,
  rank-order-unchanged) — verifies correctness of the field but is not itself a UI surface.
- `apps/backend/tests/test_mcp_server.py` — new byte-identity test between the MCP `desk_screen`
  tool response and the direct `GET /research/desk/screen` response for the new field — no UI
  surface affected (this proxies API responses for MCP/agent tool callers, not a browser page).
- `apps/backend/tests/test_desk_ui_guards.py` — new static source-scan guard test asserting
  `apps/frontend/app/desk/page.tsx` never derives a price value via arithmetic on
  `distance_bps`/`price_low`/`price_high` outside the existing band-range display — a regression
  guard, not itself a rendered UI element.

**Note on the underlying backend change:** `apps/backend/app/research/desk_screen.py`'s
`compute_screen` function now includes `"reference_close": close` on every ranked row it returns
from the already-registered `GET /research/desk/screen` endpoint. This is a backend-api change, but
it is fully consumed by the frontend in this same iteration (see the three `/desk` rows above) — it
is not a "not visible yet" backend-only capability. `apps/frontend/lib/types.ts`'s
`DeskScreenRow.reference_close?: number | null` is the supporting type declaration for this data and
has no independent UI surface of its own; its effect is captured by the `/desk` rows above.

---

## Summary

- **Frontend surfaces changed:** 1 (`/desk`)
- **New pages/routes:** 0
- **Modified components:** 3 (`DeskRowsTable` header, `DeskRow` ranked-row cell, `deskRowDrillInTitle` tooltip)
- **Navigation changes:** no
- **Backend-only changes:** 3 (test files only — the production backend field change is fully surfaced in the UI)
