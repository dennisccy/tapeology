# Phase goal-desk-iter-15 — UI Surface Map

**Phase:** goal-desk-iter-15
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `DeskRowsTable` header row (`<th>` "history") | Added navigation-adjacent table column | J-11 adds a per-row history-depth disclosure to the ranked briefing | Load `/desk` with a computed screen present; verify a `history` column header renders in the ranked table's `<thead>`, positioned immediately after the `basis` header |
| `/desk` | `DeskRow` cell, `data-testid="desk-row-history"` | New table column | Every ranked row now discloses session count + start date, derived from `desk_screen.py`'s existing basis-resolution walk | For a row from a freshly computed screen (e.g. via `POST /research/desk/screen/compute`), verify the cell text matches the pattern `history <N> sessions · from <YYYY-MM-DD>`, where `<N>` and the date equal that symbol's own `merged_bars(symbol, "1d")` count/earliest timestamp at or before its `basis_as_of` |
| `/desk` | `DeskRow` cell, `data-testid="desk-row-history"` (legacy row) | Changed behavior (honest fallback) | Screen snapshots recorded before this iteration never carry the new fields (append-only rail — no backfill) | Load a screen snapshot recorded before iter-15 (e.g. `GET /research/desk/screen?date=<pre-iteration date>` such as the cited `screen-2026-07-29-ce0d82b8e9bf`); verify every ranked row's history cell reads exactly `history not recorded in this snapshot` — not blank, not the text `null` |
| `/desk` | Row drill-in anchor composite tooltip (`deskRowDrillInTitle`, `data-testid="desk-row-drill-in"` `title` attribute) | Changed behavior (tooltip content) | Tooltip gains full-precision history detail alongside existing distance/score/basis/coverage lines | Hover a ranked row's symbol/drill-in link on a freshly computed screen; verify the native browser tooltip text includes `history <N> sessions from <full ISO timestamp>` appended after the `basis` line, and confirm the anchor's `href` (`/structure?symbol=...&asof=...`) and clickable area are unchanged from before this iteration |
| `/desk` | Ranked table, multiple rows (short vs. long history) | New capability (data range legible together) | Operator needs to tell a thin listing from a deep one at a glance, per the DoD's `<=60` / `>=400` split | With a screen whose ranked rows include at least one member with `history_sessions <= 60` and one with `history_sessions >= 400` (e.g. a scoped rig or the real store's `screen-2026-07-28-ac07c9581a4f`), verify both rows' history cells are simultaneously readable in one screenshot without needing to scroll to reveal the second value |
| `/desk` | `DeskSkipTable` (skipped-members sections, `data-testid="desk-skip-row"`) | No change (confirm absence, structurally separate table) | Skip rows (`no_bars`/`no_basis`) never carry `history_sessions`/`history_start` and were never ranked | Load a screen with skipped members; verify the `"Skipped — no bars"` and `"Skipped — no basis session"` tables render with their existing columns (symbol, reason, coverage, tick evidence) only — no `history` header or cell appears anywhere in either skip table |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_desk_screen.py` — new pytest block (`history disclosure` test group:
  golden per-row values, off-by-one edge case, byte-identical recompute, legacy-row absence,
  zero-extra-`merged_bars`-call guard, single-source-of-truth cross-check against
  `GET /research/candles`) — test-suite file, no UI surface affected.
- `apps/backend/tests/test_desk_hover_tooltip_guard.py` — added `row.history_start` as a required
  source-code needle in the tooltip-builder guard test — test-suite file, no UI surface affected
  (it verifies the frontend behavior above rather than being one).
- `runs/goal-session-desk/journey-scripts/J-11.json` — new deterministic golden replay script for
  the downstream browser-QA/demo-narrator lanes — QA/test infrastructure artifact, not a UI
  surface itself.

Note: `apps/backend/app/research/desk_screen.py` is classified **backend-api → full-stack**, not
backend-only — it adds `history_sessions`/`history_start` to the response of the existing
`GET /research/desk/screen` endpoint, and the frontend (`page.tsx`/`types.ts`, rows above) already
consumes those fields directly, so its change is fully reflected in the UI surfaces listed above.

---

## Summary

- **Frontend surfaces changed:** 1 (`/desk` — ranked table + row drill-in tooltip)
- **New pages/routes:** 0
- **Modified components:** 2 (`DeskRowsTable`/`DeskRow` ranked table; `deskRowDrillInTitle`
  composite tooltip builder)
- **Navigation changes:** no
- **Backend-only changes:** 3 (2 backend test files + 1 golden replay script)
