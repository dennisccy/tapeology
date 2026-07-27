# Phase goal-desk-iter-7 — UI Surface Map

**Phase:** goal-desk-iter-7
**Date:** 2026-07-26
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `DeskRow`'s `desk-row-drill-in` anchor (`apps/frontend/app/desk/page.tsx`) | Changed behavior (hover-only, no layout/geometry change) | Audit finding F2: the row's `absolute inset-0` drill-in link paints above the per-cell `title`s at `desk-row-distance`/`desk-row-score` and each coverage badge, making them pointer-unreachable; the composite `title` (built by the new `deskRowDrillInTitle(row)` function) is now attached directly to the anchor so it is reachable everywhere in the row | Load `/desk` with a populated screen, hover the mouse anywhere inside a ranked row (e.g. over the symbol cell, the side cell, or empty row space away from any specific number) and confirm the browser tooltip text contains that row's full unrounded `distance_bps` value, its full `band_score` value, and a "window last requested" line for each of the row's coverage timeframes |
| `/desk` | `DeskSkipRow`'s `desk-skip-row-drill-in` anchor (`apps/frontend/app/desk/page.tsx`) | Changed behavior (hover-only, no layout/geometry change) | Same F2 regression, skip-row case: the new `deskSkipDrillInTitle(skip)` function composes only the coverage-freshness portion since a skipped member has no distance/score | Load `/desk` with a screen that has skipped members, hover anywhere inside a skipped row and confirm the tooltip shows each coverage timeframe's "window last requested" value and does NOT show any distance or score value (none exists for that row) |
| `/desk` | `DeskRow`'s `desk-row-drill-in` anchor — click behavior (unchanged, regression-checked) | No change (verify no regression) | The F2 fix was deliberately built to touch `title` only, leaving `href`, the `absolute inset-0` class, and `data-testid` byte-identical, to protect the already-shipped whole-row click | Click anywhere inside a ranked row (e.g. on the band-class cell, not just the symbol text) and confirm the browser navigates to `/structure?symbol=<that row's symbol>&asof=<the displayed snapshot's as_of>`, exactly as before this iteration |
| `/desk` | `DeskSkipRow`'s `desk-skip-row-drill-in` anchor — click behavior (unchanged, regression-checked) | No change (verify no regression) | Same protection as above, applied to skip rows | Click anywhere inside a skipped row and confirm the browser navigates to `/structure?symbol=<that row's symbol>&asof=<the displayed snapshot's as_of>`, exactly as before this iteration |
| N/A (no page — MCP surface) | `desk_universe` MCP tool (`apps/backend/app/mcp/__init__.py`) | New capability (machine-readable, not a browser UI surface) | J-06: adds a Claude-callable read-only tool proxying the already-shipped `GET /research/desk/universe` | From a Claude conversation with this project's MCP server connected, call the `desk_universe` tool and confirm the returned JSON's `snapshots`/`latest`/`integrity_errors` fields match what `curl http://localhost:8301/research/desk/universe` returns for the same backend state |
| N/A (no page — MCP surface) | `desk_screen` MCP tool (`apps/backend/app/mcp/__init__.py`) | New capability (machine-readable, not a browser UI surface) | J-06: adds a Claude-callable read-only tool proxying the already-shipped `GET /research/desk/screen` | From a Claude conversation with this project's MCP server connected, call the `desk_screen` tool and confirm the returned JSON's `screens`/`latest`/`integrity_errors` fields match what `curl http://localhost:8301/research/desk/screen` returns for the same backend state |
| N/A (regression asset, not a UI surface) | `runs/goal-session-desk/journey-scripts/J-05.json` step 2 (golden script) | Test asset fix | Step 2's click target changed from the first-DOM-match `desk-history-row` testid to a date-qualified CSS selector (`[data-testid="desk-history-row"][data-screen-date="2026-06-22"]`), so replay selects the intended history row by its recorded date instead of table position | On `/desk`'s Screen History panel, with more than one history row present, click the row whose date cell reads `2026-06-22` specifically (not just the first row in the table) and confirm the page shows "Viewing the recorded screen for 2026-06-22" and swaps in that date's own rows/skipped/provenance |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_mcp_server.py` — extends `EXPECTED_TOOLS` to 17 names and adds
  byte-identity tests (empty + populated fixture states) for `desk_universe`/`desk_screen`, plus a
  `get_endpoint` proxy test for `/research/desk/screen?date=` — test-only, no UI surface affected.
- `apps/backend/tests/test_desk_hover_tooltip_guard.py` (new file) — a source-introspection guard
  test (plus its seeded-violation counter-test) that reads `apps/frontend/app/desk/page.tsx` as text
  and asserts the two tooltip-composing functions reference the right fields — a CI safeguard, not a
  UI surface itself.
- `apps/backend/app/mcp/__init__.py`'s `_STATIC_PATHS` dict and `TOOLS` tuple registry entries for
  `desk_universe`/`desk_screen` — these register the two new MCP tools listed in the surface map
  above (they ARE the mechanism behind those rows); there is no additional backend-only change
  beyond what is already captured there.

---

## Summary

- **Frontend surfaces changed:** 1 (`apps/frontend/app/desk/page.tsx` — hover-tooltip content on
  two existing row anchors; no new page/component)
- **New pages/routes:** 0
- **Modified components:** 2 (`DeskRow`'s drill-in anchor, `DeskSkipRow`'s drill-in anchor — both
  inside the single already-shipped `/desk` page)
- **Navigation changes:** no
- **Backend-only changes:** 3 (MCP tool registry additions, `test_mcp_server.py` extension,
  new `test_desk_hover_tooltip_guard.py` guard test) — 2 of these (the MCP tools themselves) are
  captured as their own rows above because they are a new user-reachable surface, just not a browser
  one; the test files themselves have no UI impact.
