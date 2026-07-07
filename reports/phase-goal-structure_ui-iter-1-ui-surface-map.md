# Phase goal-structure_ui-iter-1 — UI Surface Map

**Phase:** goal-structure_ui-iter-1
**Date:** 2026-07-07
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| All pages (shared layout) | `NavBar` — new "Structure" top-bar link | Added navigation | `apps/backend/app/meta.py`'s `UI_ROUTES` tuple gained one entry (`{"path": "/structure", "label": "Structure", "nav": true}`); `NavBar.tsx` fetches this list live and renders it — zero `NavBar.tsx` code changed | From `/performance` (or any existing page), confirm a "Structure" link now renders in the top bar immediately after "Performance", and clicking it navigates the browser to `/structure` |
| `/structure` | Page shell (`app/structure/page.tsx`), header `data-testid="structure-title"` | New page | New read-only S/R levels + confluence-zones surface (J-01) | Navigate directly to `http://<host>/structure`; confirm the page returns 200 (not a 404) and shows the "Structure" heading plus the read-only framing text (`data-testid="structure-framing"`) |
| `/structure` | Symbol input (`SymbolSearch`), as-of input (`data-testid="structure-as-of-input"`), Load button (`data-testid="structure-load-button"`) | New form/controls | Lets the user choose which symbol + point in time to query against `GET /research/levels` | Leave both fields empty and confirm the Load button is disabled; type `PG` in the symbol box and `2026-06-09T21:00:00Z` in the as-of box and confirm the Load button becomes enabled, then click it |
| `/structure` | Idle placeholder (`data-testid="structure-idle"`) | New state | Shown before the user has ever clicked Load | Load `/structure` fresh (no prior query this session) and confirm the message "Choose a symbol and an as-of time, then Load, to see its S/R levels and confluence zones." is visible, with no chart or table present |
| `/structure` | Loading placeholder (`data-testid="structure-loading"`) | New state | Shown while the `GET /research/levels` + `GET /research/bars` fetches are in flight | Click Load with a valid symbol/as-of and confirm a pulse-skeleton placeholder appears momentarily before the result renders |
| `/structure` | Price chart (`StructureChart`, canvas `data-testid="structure-chart-canvas"`) | New chart | Renders candles for the symbol's recorded bar series plus one dashed price line per S/R level, labelled by timeframe + type | Seed the committed PG fixture (`apps/backend/tests/fixtures/bars/*.json`) into the backend, load symbol `PG` at `as_of=2026-06-09T21:00:00Z`, and confirm the chart renders candles plus 20 dashed price lines (e.g. one labelled "1h swing-pivot 149.48") — cross-check every rendered price/timeframe/type against the live `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z` JSON |
| `/structure` | Confluence-zones table (`ZoneRow` cards, `data-testid="zone-row"`, badge `data-testid="zone-class-badge"`, score `data-testid="zone-score"`, member rows `data-testid="zone-member-level"`) | New table | One card per `confluence_zones[]` entry: A/B/C class badge, score, and member levels (price/timeframe/type), all read verbatim | With the same seeded PG fixture and as-of, confirm exactly 6 zone cards render (5 badged "Class C", 1 badged "Class B") and that one zone's member-level rows and score (e.g. 139.89/1d/prior-period-extreme, 139.89/1d/swing-pivot, 140/1d/prior-period-extreme, score 12) match the live JSON exactly |
| `/structure` | No-bar-series honest state (`data-testid="structure-no-bar-series"`) | New empty state | Distinct message when `no_bar_series_for_symbol: true` (nothing ever recorded for that symbol) | Load a symbol with nothing seeded (or query `PG` before seeding any fixture) and confirm the message "No bar series recorded for `<SYMBOL>`." plus "Recording historical bars needs provider credentials." appears — no chart, no table, no crash |
| `/structure` | No-levels honest state (`data-testid="structure-no-levels"`) | New empty state | Distinct message when a series exists but `levels: []` at the chosen as-of | With the seeded PG fixture, load `as_of=2026-05-01T00:00:00Z` (before either recorded window opens) and confirm the message "No levels found for PG as of 2026-05-01T00:00:00Z." plus "A bar series is recorded, but nothing is derivable at this as-of time." appears, with different wording than the no-bar-series state |
| `/structure` | No-qualifying-zone honest state (`data-testid="structure-no-zones"`) | New empty state | Distinct message scoped to the zones panel only, when `levels` is non-empty but `confluence_zones: []` — the chart still renders | With the seeded PG fixture, load `as_of=2026-06-02T12:00:00Z` and confirm the chart still renders its 3 level lines while the zones panel (only) shows "No qualifying confluence zone among these levels." |
| `/structure` | Degraded state (`data-testid="structure-degraded"`) | New error state | Shared state for backend-unreachable, any non-200, or a malformed `as_of` (422 folded in per the plan's documented assumption) | (a) Stop the backend process, click Load with any valid-looking input, and confirm the amber panel shows "Backend unreachable — is the API running?" with "Nothing cached and nothing fabricated is shown in its place."; (b) with the backend running, type `not-a-date` in the as-of field and click Load, and confirm the same panel shows the backend's own validation message (e.g. "as_of must be an ISO date-time") instead of a crash or blank chart |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_meta_routes.py` — updated/added test assertions (`test_ui_routes_lists_exactly_the_live_routes`, `test_ui_routes_top_bar_entries_match_the_rendered_nav_set`, new `test_ui_routes_includes_structure_now_its_page_ships`) that verify the `meta.py` route-list change. Test-only file, never served to a browser — no separate UI surface.

<!-- All other backend-adjacent work (apps/backend/app/meta.py) is NOT backend-only: it is the
     single-line addition that makes the new "Structure" nav link appear, so it is captured above
     as a UI-affecting change rather than listed here. -->

---

## Summary

- **Frontend surfaces changed:** 10 (1 shared-nav row + 9 rows scoped to the new `/structure` route)
- **New pages/routes:** 1 (`/structure`)
- **New components:** 2 (`apps/frontend/app/structure/page.tsx`, `apps/frontend/components/StructureChart.tsx`); plus supporting (non-rendering) additions to `apps/frontend/lib/api.ts` (`fetchLevels`, `fetchBarSeriesList`) and `apps/frontend/lib/types.ts` (`SrLevel`, `ConfluenceZone`, `LevelsResponse`, `BarRow`, `BarSeriesRecord`, `BarSeriesListResult`) that the new page/component depend on
- **Modified components:** 0 (`NavBar.tsx` and all four pre-existing pages are byte-unchanged; the new nav link is a pure data effect of the backend's route-list change)
- **Navigation changes:** yes — one new top-bar link ("Structure"), added without touching any frontend navigation code
- **Backend-only changes:** 1 (`test_meta_routes.py` — verification-only, no independent UI surface)
