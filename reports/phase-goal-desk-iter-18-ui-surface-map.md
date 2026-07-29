# Phase goal-desk-iter-18 — UI Surface Map

**Phase:** goal-desk-iter-18
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `DeskRow` — new `opposite` `<td data-testid="desk-row-opposite">` cell (after the `band` cell) | New table column (populated state) | J-14: disclose the nearest wall on the side of price the row's own displayed wall did NOT select, sourced from `opposite_band` on `GET /research/desk/screen` | Load `/desk` with a screen snapshot computed after this iteration; in the "opposite" column, find one row whose text reads a distance ≤25 bps (e.g. `... · 0.6 bps`) and confirm it is legible; find a second row whose text reads a distance >1,000 bps and confirm it is legible and distinct from the near row |
| `/desk` | `DeskRow` — `opposite` cell, recorded-`null` state | Changed behavior (new state) | `opposite_band` can be a genuine `null` when `compute_tradability` found no wall on the other side of price at all | On a screen snapshot computed after this iteration, find a row whose `opposite_band` was recorded as `null` and confirm its "opposite" cell reads exactly `"no band on the other side"` (not blank, not a dash, not an error) |
| `/desk` | `DeskRow` — `opposite` cell, legacy-absent state | Changed behavior (new fallback state) | Screen snapshots recorded before this iteration never carry the `opposite_band`/`bands_by_class` keys at all | Load `/desk` against a screen snapshot recorded before this iteration (e.g. via `?date=` for a pre-iteration date, or the current ambient `latest` snapshot); confirm every row's "opposite" cell reads exactly `"opposite wall not recorded in this snapshot"` |
| `/desk` | `DeskRowsTable` — new `<th>opposite</th>` header cell | Added navigation/column header | Header must label the new column so the table stays self-describing at eleven columns | Confirm a header cell reading "opposite" appears immediately after the "band" header, aligned above the new data column |
| `/desk` | `deskRowDrillInTitle` — composite hover tooltip, new `bandsByClassLine` | Updated tooltip content | J-14: disclose the per-class count of every wall `compute_tradability` returned for the symbol, without adding a new per-cell tooltip (iter-6/7 F2 lesson: per-cell titles are pointer-unreachable under the stretched drill-in anchor) | Hover over (or focus, to trigger the title) a ranked row computed after this iteration and confirm the tooltip's last line reads `bands by class A <n> · B <n> · C <n> · unclassified <n>` with all four counts visible and none blank |
| `/desk` | `deskRowDrillInTitle` — composite hover tooltip, legacy-absent `bands_by_class` state | Changed behavior (new fallback state) | Legacy rows never carry `bands_by_class`, so the tooltip line must say so rather than show blank or zero counts | Hover over a ranked row from a pre-iteration screen snapshot and confirm the tooltip's last line reads exactly `"bands by class not recorded in this snapshot"` |

<!-- Change Type options used above: New table column | Changed behavior (new state) | Changed behavior (new fallback state) | Added navigation/column header | Updated tooltip content -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/desk_screen.py` — new `_select_opposite_band(bands, close, best_side)`
  and `_bands_by_class(bands)` pure-function helpers, and the two new dict keys they populate in
  `compute_screen`'s ranked-row builder — this is the backend-api change the frontend surfaces above
  directly consume via the already-registered `GET /research/desk/screen` endpoint (no new route);
  the helpers themselves are backend-internal implementation detail with no separate UI surface.
- `apps/backend/tests/test_desk_screen.py`, `apps/backend/tests/test_mcp_server.py`,
  `apps/backend/tests/test_desk_ui_guards.py` — new/extended unit, golden, byte-identity, and
  arithmetic-derivation-guard tests for the two new fields — test-only, no UI surface affected.
- MCP `desk_screen` tool / `get_endpoint`'s `?date=` proxy — both fields now flow through
  byte-identically as an incidental consequence of proxying the same `GET /research/desk/screen`
  response verbatim; zero MCP code change, tool count stays at 17 — no separate UI surface (MCP
  clients are not the browser-facing `/desk` page).

---

## Summary

- **Frontend surfaces changed:** 1 (`/desk` ranked-rows table: `DeskRow`, `DeskRowsTable`,
  `deskRowDrillInTitle`)
- **New pages/routes:** 0
- **Modified components:** 2 (`DeskRow`/`DeskRowsTable` — new column; `deskRowDrillInTitle` — new
  tooltip line)
- **Navigation changes:** no
- **Backend-only changes:** 3 (row-builder helpers in `desk_screen.py`; backend test additions; MCP
  proxy pass-through)
