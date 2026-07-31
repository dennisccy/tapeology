# Phase goal-desk-iter-29 — UI Surface Map

**Phase:** goal-desk-iter-29
**Date:** 2026-07-31
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `ScreenRunsSection` / new `<section aria-label="Screen Runs">` (page.tsx ~2257) | New component | J-18: new fourth ledger section surfacing `GET /research/desk/screen/runs` | Navigate to `http://localhost:3301/desk`, scroll to the bottom, verify a `Panel` titled "Screen Runs" is present immediately after the "Index Reconciliation" panel |
| `/desk` | `ScreenRunsTable` / `ScreenRunRow` (`data-testid="desk-screen-runs-table"` / `"desk-screen-run-row"`) | New table | Lists every recorded screen run's meta (date, id, state, attempted/total, produced) | With at least one run recorded, verify the table shows column headers "date", "run", "state", "attempted / total", "produced" and one row per recorded run with those five values populated |
| `/desk` | `ScreenRunsTable` empty state (`data-testid="desk-screen-runs-empty"`) | New empty state | Honest "nothing recorded" state when the ledger is empty | With zero screen runs recorded (fresh fixture-scoped store), verify the text "No screen runs recorded yet." renders in place of the table |
| `/desk` | `LatestScreenRunDetail` (`data-testid="desk-screen-run-latest-detail"`) | New detail block | Shows full detail (elapsed, ranked/skipped counts, failure detail) for the most recent run only | With one completed run recorded, verify the detail block under the table shows "Latest run — `<date>` · `<run-id>`", "state: done", "`<N>` of `<M>` members attempted", and an elapsed-time string ending in "s" or "m `<ss>`s" |
| `/desk` | `LatestScreenRunDetail` reused-outcome text (`data-testid="desk-screen-run-latest-outcome"`) | New text state | A duplicate-pin retrigger shows the honest "no walk performed" note instead of a fabricated recompute | Trigger "Run Screen" twice in a row for the same day against a scoped fixture rig; verify the second run's row and latest-detail both read "reused `<screen_id>` — no walk was performed" and "attempted" shows "0 of `<total>`" |
| `/desk` | `LatestScreenRunDetail` failed state (`data-testid="desk-screen-run-latest-failed"` / `"desk-screen-run-latest-failed-detail"`) | New conditional block | Verbatim exception + raising member name shown only when `state === "failed"` | With a `failed` run recorded (fixture-scoped), verify the block shows the raising member's name in monospace text followed by " — " and the verbatim error string; verify this block does NOT render for a `done` or `cancelled` run |
| `/desk` | `LatestScreenRunDetail` ranked/skipped counts (`data-testid="desk-screen-run-latest-counts"`) | New conditional block | Ranked/skipped-by-reason counts shown only on a completed (`done`) walk | With a `done` non-reused run recorded, verify the text reads "`<N>` ranked · `<N>` skipped (no bars) · `<N>` skipped (no basis)"; verify this line is absent for a `cancelled` or `failed` run |
| `/desk` | `IntegrityErrorsNote` inside `ScreenRunsSection` (`data-testid="desk-screen-runs-integrity-errors"`) | New (reused component) | Surfaces any corrupted run-record file via `store.list()`'s `errors` return | With no corrupted files, verify no integrity-errors note renders; this is a regression-only check unless a corrupted fixture file is deliberately planted |
| `/desk` | `desk-run-screen-button` ("Run Screen" button, page.tsx ~1493) | Changed behavior (no visible/label change) | Backend now pre-checks the five pins before walking; a duplicate-pin click short-circuits instead of re-walking ~101 members | Click "Run Screen" once (fresh day), let it finish, then click "Run Screen" again immediately; verify the second click resolves without the members-progress counter climbing from 0, and the outcome text reads "Reused the snapshot already recorded for this key — `<id>`" |
| `/desk` | Ranked table / `DeskRowsTable` (unchanged) | Regression — no change | J-16's measured width contract and stored golden replay scripts must remain untouched | Load `/desk` with a populated screen, verify the ranked table's columns and row content are identical to before this iteration (no new column, no layout shift, no horizontal scroll at 1440x900) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/desk_screen_log.py` — new module (`ScreenRunStore`, `record_screen_run`,
  `resolve_desk_screen_log_dir`, `ScreenRunIntegrityError`) — no direct UI surface; consumed
  entirely through the new `/desk` "Screen Runs" section above (not backend-only in effect, but the
  file itself has no template/markup).
- `apps/backend/app/research/desk_screen_compute.py` — five-pin pre-check + reuse short-circuit +
  terminal-state `record_screen_run` wiring inside `run_screen_and_record`; the CLI's `main()` now
  also threads a `ScreenRunStore` — the CLI path has no UI surface (operator-run command line only).
- `apps/backend/app/research/desk_routes.py` — new `get_screen_run_store` dependency; UI-consumed
  via the new route below.
- `apps/backend/tests/test_desk_screen_log.py`, `test_desk_screen_compute.py` (new cases),
  `test_mcp_server.py` (new reachability test) — test-only, no UI surface.

---

## Backend-API Change Consumed By The Frontend

- `GET /research/desk/screen/runs` (new route, `desk_routes.py`) — confirmed consumed by
  `apps/frontend/lib/api.ts`'s new `fetchDeskScreenRuns()`, called from `page.tsx`'s mount-time
  effect and the screen-compute poll's terminal tick. Surface: the "Screen Runs" section rows above.

---

## Summary

- **Frontend surfaces changed:** 1 (the `/desk` page — one new section, no new route/page)
- **New pages/routes:** 0 new pages; 1 new backend route (`GET /research/desk/screen/runs`), fully
  consumed by the existing `/desk` page
- **Modified components:** 1 new section (`ScreenRunsSection` + `ScreenRunsTable` + `ScreenRunRow` +
  `LatestScreenRunDetail`, all new); 0 existing components edited beyond the page's own mount effect
  and poll-tick extension
- **Navigation changes:** no (no nav-skeleton change; the new section is reached by scrolling the
  existing `/desk` page, not via a new link)
- **Backend-only changes:** 3 files with no direct markup (log module, compute wiring, route
  dependency) — all fully surfaced through the one new frontend section above
