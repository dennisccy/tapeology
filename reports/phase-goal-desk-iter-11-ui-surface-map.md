# Phase goal-desk-iter-11 — UI Surface Map

**Phase:** goal-desk-iter-11
**Date:** 2026-07-28
**Written by:** ui-impact-analyst

---

## Changed-File Classification

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/research/desk_topup_log.py` (new) | backend-internal | none (direct) | New `TopupRunStore` / `resolve_desk_topup_log_dir` / `record_topup_run` — a checksum-verified, append-only JSON-file store. No route decorator, not imported by the frontend; its data reaches a user only through the new route below. |
| `apps/backend/tests/test_desk_topup_log.py` (new) | backend-internal (test) | none | 15 store-discipline tests (checksum/append-only/no-dedup/no-update, interrupted-run-leaves-no-record, second-run-appends). No UI surface. |
| `apps/backend/app/research/desk_topup_compute.py` (modified) | backend-internal | none (direct) | Threads `universe_snapshot_id` / `requested_window` through `trigger()`/`main()` and calls the new writer at both `_work` terminal exits and once in the CLI's `main()`. The EXISTING `POST`/`GET /research/desk/topup/compute` response shape is confirmed unchanged (no new key added to `self._snapshot` — the plan's own trap #1). This file's own output stays invisible to the UI; its side effect (a persisted run record) surfaces only through the route below. |
| `apps/backend/app/research/desk_routes.py` (modified) | backend-api | indirect — frontend consumes this API, surface affected | New `GET /research/desk/topup/runs` route + `get_topup_run_store` dependency. `apps/frontend/lib/api.ts`'s new `fetchDeskTopupRuns()` calls this exact path — confirmed by grep and by the diff below. |
| `apps/backend/tests/test_desk_topup_compute.py` (modified) | backend-internal (test) | none | 6 new test functions (byte-identical-to-`run_topup` spy, honest-empty + populated route tests, dir-resolution test, CLI shape-parity test, CLI no-universe test) plus inline assertions added to 3 existing tests. No UI surface. |
| `apps/frontend/lib/types.ts` (modified) | frontend-direct | direct | New `DeskTopupRunMeta` / `DeskTopupRun` / `DeskTopupRunsListResult` interfaces consumed directly by the new `/desk` components. |
| `apps/frontend/lib/api.ts` (modified) | frontend-direct | direct | New `fetchDeskTopupRuns()` — the exact client call `/desk/page.tsx`'s mount effect and terminal-state poll both invoke. |
| `apps/frontend/app/desk/page.tsx` (modified) | frontend-direct | direct | New `TopupRunsTable` / `TopupRunRow` / `LatestTopupRunDetail` / `TopupRunsSection` components, a new top-level `<section aria-label="Top-up runs">`, a 4th mount-time GET, and a terminal-state poll refetch. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | New section `<section aria-label="Top-up runs">` wrapping `Panel title="Top-up Runs"` | New feature (page-level section) | J-09: gives the operator a durable view of top-up run history that previously vanished once superseded by the next run | Navigate to `/desk` while a screen is loading, unavailable, not-yet-computed, and populated (four separate loads/states); confirm the "Top-up Runs" panel renders as the LAST section on the page in all four states — its presence must not depend on whether a screen has ever been computed. |
| `/desk` | `TopupRunsSection` honest-empty state (`data-testid="desk-topup-runs-empty"`) | New empty state | Before any top-up run has ever completed, the panel must say so honestly rather than render blank | Against a store/backend with zero recorded top-up runs, load `/desk`; confirm the panel shows the exact text "No top-up runs recorded yet." and zero rows; open the browser network tab during the load and confirm no `POST /research/desk/topup/compute` fires — the GET must never trigger a compute as a side effect. |
| `/desk` | `TopupRunsTable` (`data-testid="desk-topup-runs-table"`, rows `data-testid="desk-topup-run-row"`) | New table | Lists every historical top-up run's summary — the core of the new durable-history capability | After at least 2 fixture-scoped top-up runs have completed, reload `/desk`; confirm the table shows one row per run (`desk-topup-run-row` count matches the number of completed runs) with 5 columns: date, run id (`desk-topup-run-id`), state (`desk-topup-run-state`), "attempted / total" (`desk-topup-run-attempted`), and universe snapshot id (`desk-topup-run-universe`). |
| `/desk` | `LatestTopupRunDetail` (`data-testid="desk-topup-run-latest-detail"`) | New detail panel | Only the latest run gets a full per-pair breakdown, since that is the only record the backend serves with `outcomes` | After the most recent top-up run completes, reload `/desk`; confirm a "Latest run — `<date>` · `<id>`" block appears below the table showing `state: <state>` (`desk-topup-run-latest-state`), "`N` of `M` pairs attempted" (`desk-topup-run-latest-attempted`), and a counts string "`N` reused · `N` fetched · `N` failed" (`desk-topup-run-latest-counts`) whose three numbers sum to the attempted count. |
| `/desk` | Failed-pairs disclosure (`data-testid="desk-topup-run-latest-failed"`, rows `desk-topup-run-latest-failed-row`, detail span `desk-topup-run-latest-failed-detail`) | New conditional element | Every failed pair's real error text must be shown verbatim, never summarized or truncated (TC-13's screenshot requirement) | Replay or trigger a fixture-scoped top-up run with at least one induced failure (the existing monkeypatched-adapter / `NoDataForWindow` technique `test_desk_topup_compute.py` already uses — never a live vendor call); reload `/desk`; confirm a "Failed pairs (`N`)" heading appears with one list item per failed pair reading "`<SYMBOL>` `<timeframe>` — `<verbatim error text>`", and confirm the full error string is legible and not cut off in a single screenshot. |
| `/desk` | Unreached-pairs note (`data-testid="desk-topup-run-latest-unreached"`) | New conditional element | A cancelled/interrupted run must honestly disclose pairs it never reached, without a false "0 not reached" claim | Start a top-up run and click the existing "Cancel" button mid-walk so `pairs_attempted < pairs_total`; reload `/desk`; confirm the latest-run block shows "`N` pairs not reached" in amber text where `N` equals `pairs_total − pairs_attempted`. Separately, for a run that completed every pair, confirm this element is entirely absent (never a "0 pairs not reached" line). |
| `/desk` | Auto-refresh on run completion (terminal-state branch of the existing top-up poll `useEffect` in `DeskPage`) | Changed behavior (background) | The panel must pick up a just-finished run without a manual reload | With `/desk` open and idle (no reload), click "Top-up" and let the run finish; confirm that within one poll tick (~700ms) after the run reaches a terminal state, the Top-up Runs table's row count increases by one and the Latest-run detail block updates to reference the new run's id — with no manual page refresh performed. |
| `GET /research/desk/topup/runs` (backend endpoint consumed by `/desk`) | New route in `desk_routes.py` | New backend-api endpoint | The single data source backing every row above; must be honest-empty and never a 404 | With curl or the browser network tab, call `GET /research/desk/topup/runs` against a store with zero runs; confirm HTTP 200 with body exactly `{"runs": [], "latest": null}`. After a run completes, call it again and confirm `latest.outcomes` is present and non-empty while every entry in the `runs` array has no `outcomes` key at all. |

<!-- Change Type options used above: New feature | New empty state | New table | New detail panel | New conditional element | Changed behavior | New backend-api endpoint -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/desk_topup_log.py` — the `TopupRunStore` persistence layer itself
  (checksum verification on load, append-only file writes, directory resolution via
  `TAPEOLOGY_DESK_TOPUP_LOG_DIR` or a sibling-of-universe-dir default) — no UI surface of its own;
  its data reaches a user only through the `GET /research/desk/topup/runs` route captured above.
- `apps/backend/app/research/desk_topup_compute.py` — the threading of `universe_snapshot_id` /
  `requested_window` and the two `record_topup_run` call sites (`_work`'s normal and exception exit
  paths, plus the CLI's `main()`) — this file has no route of its own; it is the plumbing that makes
  the new route non-empty, not a UI surface itself. The EXISTING `POST`/`GET
  /research/desk/topup/compute` response shapes it backs are confirmed unchanged.
- `apps/backend/tests/test_desk_topup_log.py` (15 tests) and the additions to
  `apps/backend/tests/test_desk_topup_compute.py` (6 new + 3 extended) — test coverage only, no UI
  surface.
- The CLI entry point (`python -m app.research.desk_topup_compute`) now also writes a durable run
  record on completion — an operator-run script, not a UI surface; this iteration adds no new UI
  trigger for it (it was already CLI-only before J-09, and stays that way).

**Note on unchanged files that still gain the new capability's data path:** `app/mcp/__init__.py`
shows zero diff this iteration (confirmed via the dev handoff's `_STATIC_PATHS` count staying at 11
and `test_mcp_server.py`'s unmodified 17-tool contract still passing) — the new route is already
reachable through the existing `ALLOWED_GET_PREFIXES` (`/research/`) allowlist, so the MCP
`get_endpoint` tool can proxy `/research/desk/topup/runs` with no code change, even though this is
not itself a rendered UI surface.

---

## Summary

- **Frontend surfaces changed:** 1 (route: `/desk`)
- **New pages/routes:** 0 new frontend pages/routes (one new backend GET endpoint,
  `/research/desk/topup/runs`, consumed by the existing `/desk` page)
- **Modified components:** 4 new components (`TopupRunsTable`, `TopupRunRow`,
  `LatestTopupRunDetail`, `TopupRunsSection`) plus 2 existing effect hooks extended (the mount-time
  GET batch, the top-up compute poll's terminal-state branch) — all within the existing
  `apps/frontend/app/desk/page.tsx`
- **Navigation changes:** no
- **Backend-only changes:** 4 (the new store module, the compute-manager threading/writer-call
  changes, and two test files)
