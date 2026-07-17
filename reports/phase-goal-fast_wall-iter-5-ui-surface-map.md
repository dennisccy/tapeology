# Phase goal-fast_wall-iter-5 — UI Surface Map

**Phase:** goal-fast_wall-iter-5
**Date:** 2026-07-17
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

`apps/frontend/app/structure/page.tsx` has zero code diff this iteration (git-confirmed
byte-identical to iter-4). Every row below reflects either (a) a narrow runtime-behavior change to
an already-shipped element, driven by this iteration's backend diff, or (b) a surface this
iteration's own required browser-QA pass re-verified — see "Why Changed" per row for which.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/structure` | Edge Report panel — progress line, "(N from cache)" clause (`data-testid="edge-report-compute-progress"`) | Changed behavior | J-05 makes the already-rendered `progress.backtests_from_cache` value genuinely non-zero on a resumed compute; previously the field existed in the code since iter-4 but was permanently `0`, so this clause never rendered | Trigger a compute against a scoped fixture backend, abort it after some (dataset, strategy) pairs have durably published to the sub-cache, then re-trigger via "Retry compute" / "Compute edge report"; while `state === "running"`, confirm the progress line shows text matching `{done} / {total} backtests (N from cache)` with N > 0. Separately, on a dataset with a cold sub-cache (never computed before), confirm the annotation is absent — text reads only `{done} / {total} backtests` with no "(N from cache)" clause — exactly as in iter-4 |
| `/structure` | Edge Report panel — full not-computed → running → terminal cycle (`edge-report-not-computed`, `edge-report-compute-button`, `edge-report-compute-progress`) | Verified only (no code change) | This iteration's browser-QA pass finally drove the complete click-through in a live Chrome session (Chrome MCP had failed to start in each of the prior two iterations); closes J-04's last open gap with zero product diff (TC-1) | Load `/structure` against the scoped fixture backend (ports 8391/3391, `TAPEOLOGY_DATASET_DIR` at `apps/backend/tests/fixtures/datasets_j03`) with a cold `TAPEOLOGY_EDGE_REPORT_CACHE_DB` and cold `TAPEOLOGY_EDGE_SWEEP_CACHE_DB`; confirm the not-computed panel renders headline "Edge report not computed yet." with an enabled button reading "Compute edge report"; click it; confirm the button immediately relabels to "Computing…" and becomes disabled; confirm the progress line appears and its counts update at least once before 90 seconds elapse; confirm the panel is then replaced by the finished report render (or the honest all-empty-cells state) with zero full-page reload (URL and scroll position unchanged) |
| `/structure` | Edge Report panel — failed-state error line + button relabel (`data-testid="edge-report-compute-error"`) | Verified only (no code change) | Re-verifies iter-4's failed-state render against a genuinely arranged `state: "failed"` snapshot, using a corrected arrangement recipe this iteration discovered (corrupt the dataset file → trigger a compute so it fails on integrity → restore the file's original bytes in place without restarting the backend) (TC-3) | Arrange a compute snapshot at `state: "failed"` per the recipe above, then load or reload `/structure`; confirm the not-computed panel's red error line (`edge-report-compute-error`) reads the exact backend `error` string verbatim (not a paraphrase — e.g. "1 dataset file(s) failed integrity verification (['...json']) — the report stops with nothing written"), and confirm the button simultaneously reads "Retry compute" and is enabled |
| `/structure` | Not-computed panel's pre-click render (headline + detail text, before any compute has ever run) | Regression check (zero code diff) | Re-verified in the SAME scoped session as TC-1, alongside J-01's original honest-not-computed-state claim, to confirm nothing about the idle render shifted while backend sweep plumbing changed underneath it (TC-2) | On a page load with a cold edge-report cache and no compute ever triggered, confirm the panel shows headline "Edge report not computed yet." plus the backend's own `detail` string rendered verbatim beneath it, with no progress line, no error line, and the button reading exactly "Compute edge report" (not "Computing…" or "Retry compute") |
| `/structure` | Tradable Map, Case Studies, Fetch from Yahoo Finance, Registry, Comparison sections (`tradable-map-table`, `case-studies-table`, `fetch-yahoo-button`, `champion-summary`, `comparison-champion`) | Regression check (zero code diff) | Re-verified as regression sentinels in the SAME scoped browser session used for TC-1/TC-2/TC-3, since this iteration's backend diff touches shared sweep/backtest plumbing (`edge_report.py`, `edge_report_compute.py`) these sections sit beside on the same page — required-still-passing J-01/J-07 (TC-2) | In the same scoped session, confirm the Tradable Map table (`data-testid="tradable-map-table"`) renders its band rows exactly as before, the Case Studies table (`data-testid="case-studies-table"`) still lists its touch-event rows with the symbol/reaction filter controls present, the "Fetch from Yahoo Finance" button (`data-testid="fetch-yahoo-button"`) is still present and clickable, the Registry's champion summary block (`data-testid="champion-summary"`) still shows the current champion strategy/profile, and the Comparison section's champion block (`data-testid="comparison-champion"`) still renders — zero structural or textual difference from iter-4's own screenshots |

<!-- Change Type options used: Changed behavior | Verified only (no code change) | Regression check (zero code diff) -->

---

## Backend-Only Changes (No UI Impact)

- `EdgeReportBacktestCache` (`apps/backend/app/research/edge_report_backtest_cache.py`, NEW) — a
  durable SQLite cache of one row per (dataset, strategy) backtest pair (`pair_cache_key`,
  `lookup`/`publish`, `resolve_backtest_cache_db_path`). No UI, REST, or MCP surface reads it
  directly — it is a pure internal accelerator behind the sweep; per the project's own anti-goal,
  accelerators are never a source of truth and this one is no exception.
- `_split_cells`'s new `run_pair` provider seam, plus new `_build_caching_run_pair`,
  `_eligible_datasets`, `_run_dataset_pairs_in_worker`, and `_parallel_prewarm_sub_cache` helpers
  (all in `apps/backend/app/research/edge_report.py`) — internal sweep-orchestration functions with
  no UI element calling or displaying them.
- The `ProcessPoolExecutor`/`spawn`-context parallel provider — reachable only via
  `python -m app.research.edge_report_compute --workers N`, a terminal command with no browser page
  or button equivalent. `--workers`'s default now also reads `TAPEOLOGY_EDGE_SWEEP_WORKERS` — an
  environment variable, not a UI control.
- `EdgeReportComputeManager.trigger()`'s new `sub_cache` keyword parameter
  (`apps/backend/app/research/edge_report_compute.py`) — threaded internally into the
  browser-triggered compute call; the route's own request/response JSON shape is unchanged
  (confirmed byte-identical per TC-13), so nothing observable differs on the wire.
- `routes.py`'s new `get_edge_report_backtest_cache()` FastAPI dependency resolver and its wiring
  into `trigger_edge_report_compute` — internal dependency injection; adds no new route, path, or
  response field, and changes no existing one.
- New/updated test modules — `apps/backend/tests/test_edge_report_backtest_cache.py` (NEW, 18
  tests) and additions to `test_edge_report.py` (+10) and `test_edge_report_compute.py` (+6) — test
  code, no UI coupling.

---

## Summary

- **Frontend surfaces changed:** 0 (zero frontend file diff this iteration)
- **New pages/routes:** 0 (no new browser page; no new REST route — the existing
  `POST`/`GET /research/edge-report/compute` routes gained an internal dependency only, same path,
  same request/response shape)
- **Modified components:** 0 at the code level (`structure/page.tsx` byte-unchanged); 1 existing
  element's rendered value narrowly changes under a specific runtime condition (the progress line's
  "(N from cache)" clause, on a resumed compute only)
- **Navigation changes:** no
- **Backend-only changes:** 6 (new sub-cache module, new sweep-orchestration helpers, CLI-only
  parallel provider, manager `sub_cache` wiring, routes.py dependency resolver, new/updated test
  modules)
