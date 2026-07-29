# Phase goal-desk-iter-19 — UI Surface Map

**Phase:** goal-desk-iter-19
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Ranked-row "opposite" cell (`DeskRow`, `data-testid="desk-row-opposite"`, `apps/frontend/app/desk/page.tsx:418-425`) | Changed behavior (content only, no markup/format change) | `_select_opposite_band` (`apps/backend/app/research/desk_screen.py`) now picks the nearest-by-distance opposite-side wall instead of the highest-graded one; the field is already rendered, only the value it resolves to on divergent rows changes | On a freshly computed `/desk` screen (never a screen re-opened from Screen History), find or reproduce a row with two candidate opposite-side walls of different band class (e.g. a HONA-equivalent row on a fixture-scoped rig). Confirm the `desk-row-opposite` cell text names the band with the SMALLER `distance_bps` value — e.g. it should read `opposite support Class B ... · 153.67 bps`, not `opposite support Class A ... · 336.96 bps`, for a row reproducing the HONA divergence; and `opposite resistance Class C ... · 92.05 bps`, not `... Class A ... · 232.58 bps`, for a row reproducing the META divergence. Also confirm at least one row shows a within-25-bps opposite distance and one shows a beyond-1,000-bps opposite distance, both legible together in the same screenshot (TC-13). |
| `/desk` | Ranked-row hover tooltip (`deskRowDrillInTitle`, exposed via the `title` attribute on `data-testid="desk-row-drill-in"`, `apps/frontend/app/desk/page.tsx:278-305,344-346`) | Unchanged — re-verify only | Reads the same row object whose `opposite_band`/`bands_by_class` are now computed under the corrected rule; the tooltip itself renders `bands_by_class`, not `opposite_band`, so its content should NOT change, but it sits on the same data path and must be re-verified | Hover over a ranked row's symbol cell (`desk-row-drill-in`) on the same freshly computed screen used above. Capture a screenshot of the tooltip and confirm its `bands by class A n · B n · C n · unclassified n` line still shows real, non-zero-looking counts consistent with the row's `opposite` cell (e.g. if the opposite cell shows a Class B wall, the tooltip's `B` count should be ≥1). |
| `/desk` | Ranked table header row (`<th>opposite</th>`, `apps/frontend/app/desk/page.tsx:457`) | Unchanged | No column added/removed/reordered/relabeled by this fix | Confirm the ranked table's header still reads, left to right, ...`band`, `opposite`, `basis`... (or whatever the current shipped order is) with the label text exactly `opposite`, unchanged from the pre-iteration screenshot. |
| `/desk` | Screen History list (`data-testid="desk-history-table"` / `desk-history-row`, `apps/frontend/app/desk/page.tsx:586-622`) | Regression check (no code change, but this is the surface where a wrong "backfill" bug would show) | Snapshots are append-only; this fix must NOT retroactively change any already-recorded screen's stored `opposite_band` values | Open a screen recorded BEFORE this fix from the Screen History list (click an older `desk-history-row` entry) and confirm its `opposite` column values are identical to what they showed prior to this iteration (i.e., still reflect the old class-first selection where the two rules disagreed) — proving no legacy row was silently rewritten. |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/desk_screen.py` — `_select_opposite_band`'s tie-break key logic and its
  module docstring — the code change itself lives entirely in the backend, but it directly determines
  the content of the already-rendered `/desk` "opposite" cell above; it is listed here only to note
  that the FILE is backend-only, not that its effect is invisible (see the surface row above for the
  visible consequence).
- `apps/backend/tests/test_desk_screen.py` — test-only change (flipped/renamed one unit test,
  re-verified the rest) — no UI surface, exercises the corrected selector directly.
- `apps/backend/tests/test_mcp_server.py` — test-only, re-verified with no value change — no UI
  surface.

---

## Summary

- **Frontend surfaces changed:** 0 (zero `page.tsx`/component code diff — confirmed in dev handoff)
- **New pages/routes:** 0
- **Modified components:** 0 (component code unchanged; only the backend-computed data flowing into
  the existing `desk-row-opposite` cell changes on affected rows)
- **Navigation changes:** no
- **Backend-only changes:** 3 files (`desk_screen.py`, `test_desk_screen.py`, `test_mcp_server.py`),
  1 of which (`desk_screen.py`) has a direct, user-visible content effect on the existing `/desk`
  "opposite" column despite being a backend-only file change.
