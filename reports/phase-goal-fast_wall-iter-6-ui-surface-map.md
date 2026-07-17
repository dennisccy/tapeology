# Phase goal-fast_wall-iter-6 — UI Surface Map

**Phase:** goal-fast_wall-iter-6
**Date:** 2026-07-17
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

<!-- Zero frontend files changed this iteration (git-confirmed). Every row below is an EXISTING
     component whose backing data source changed internal caching behavior only — the served data
     shape is byte-unchanged. "What to Test" reflects that: it verifies no regression, not a new
     capability. -->

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/structure` | Case Studies panel — list (testids `case-studies-loading` / `case-studies-empty` / `case-studies-no-match` / `case-studies-table`; filters `case-studies-filter-symbol` / `case-studies-filter-reaction`) | Changed behavior (backend caching only; zero frontend code diff) | Backed by `GET /research/setups` → `compute_setups`, which now checks a durable on-disk cache (keyed by config content + bar-store signature, not `id(config)`) before re-scanning, and survives a backend restart. The served `{"events": [...]}` shape is unchanged. | Navigate to `/structure` with a fresh hard reload (not client-side nav) and confirm the Case Studies panel leaves `case-studies-loading` within 10 seconds. On the scoped/keyless fixture pair (empty bar dir) it must land on `case-studies-empty` showing "No band-touch events scanned yet." On a populated dataset it must instead land on `case-studies-table` with the same row count and field values it had before this iteration. |
| `/structure` | Case Studies drill-in panel (testids `case-drillin-loading` / `case-drillin-unavailable` / `case-drillin`; Panel title "Case Studies — drill-in") | Changed behavior (same backend function; zero frontend code diff) | Backed by `GET /research/setups/{id}` → the same `compute_setups`, sharing the identical restart-surviving caching change. | Not reachable on the scoped/empty fixture used this iteration — the Case Studies table has zero rows, so there is nothing to click. On a populated dataset: click any row in the Case Studies table, confirm the drill-in panel mounts below it and shows that event's `symbol / session`, `band`, and `reaction` fields matching the clicked row, with `case-drillin` rendered (not `case-drillin-unavailable`). |
| `/structure` | Edge Report panel — "Compute edge report" button (testid `edge-report-compute-button`), which triggers `POST /research/edge-report/compute` | Changed behavior (indirect; backend caching only, zero frontend code diff) | `run_strategy_comparison_report` — invoked ONLY by this explicit operator action, never on page load (per the interlude's "no compute on page load" rule) — calls `compute_setups` internally, twice, to resolve each dataset's touch events. It now shares the same content-keyed, restart-surviving cache. This action was NOT exercised in this iteration's own verification (running the real sweep to completion is out of scope this iteration). | Click "Compute edge report" (`edge-report-compute-button`), confirm the panel transitions through `edge-report-compute-progress` with no new `edge-report-compute-trigger-error` appearing, and that the resulting train/holdout tables (`edge-report-train-table` / `edge-report-holdout-table`, or the honest `edge-report-empty`) contain the same class register and figures this action produced before this iteration — a byte-identity check, not merely "a result appears." |

**Unaffected sections re-verified this iteration for regression only (no code or behavior change):** `/structure`'s Tradable Map (`tradable-map-idle` and populated states), Registry (champion + `v1`/`structure_tape`/`structure_tape_map` strategy cards), and the Comparison section's champion/founding-baseline/dataset-picker states are fed by `levels.py` / `tradability.py` / `backtests.py`, none of which this iteration touches (zero diff, git-confirmed). They were reloaded as part of this iteration's full-page browser check (TC-9) purely to prove nothing broke elsewhere on the page — not because anything about them changed. The separate `/studies` route is unrelated to this iteration entirely (see the user-visible-changes report's scope note) and was not part of this iteration's verification.

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/setups_scan_cache.py` (NEW) — `SetupsScanCache` (durable SQLite `lookup`/`publish`), `scan_cache_key`, `resolve_scan_cache_db_path` — a new accelerator module with no REST route of its own; only `setups.py`'s internals call it. No UI surface reads it directly.
- `apps/backend/tests/conftest.py` — the existing autouse test fixture now also resets `setups.py`'s in-process hot slot between tests — test isolation infrastructure only.
- `apps/backend/tests/test_setups.py` — 7 new test cases (restart simulation, content-hash equality, `setups_*`-family cache-busting, store-signature busting, cache-loss recompute, the non-vacuous mutation probe, publish-failure swallowing) — test-only.
- `apps/backend/tests/test_setups_scan_cache.py` (NEW) — 19 tests covering the new cache module's durability, concurrency, corrupted-DB tolerance, and path resolution — test-only.
- `apps/backend/tests/test_setups_api.py` — 1 new HTTP-level test (a corrupted durable cache never blocks `GET /research/setups` from returning HTTP 200) — test-only.

---

## Summary

- **Frontend surfaces changed (code):** 0
- **New pages/routes:** 0
- **Modified components (code):** 0 — 2 existing components (Case Studies list, Case Studies drill-in) and 1 existing action (Edge Report's "Compute edge report" button) have changed *backing* behavior only, with an unchanged served data shape
- **Navigation changes:** no
- **Backend-only changes:** 5 files with zero UI tie (`setups_scan_cache.py` + 4 test files). A 6th changed file, `setups.py`, is backend-api-tied — it backs the three existing UI surfaces listed in the table above (indirect impact: latency/reliability only, no shape change) — so it is not counted as purely backend-only.
