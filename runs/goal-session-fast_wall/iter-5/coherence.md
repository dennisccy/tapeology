# Iteration 5 — Coherence Audit

**Iteration:** goal-fast_wall-iter-5
**Date:** 2026-07-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration is backend-only (zero frontend diff — `structure/page.tsx` is byte-unchanged,
confirmed by both the ui-surface-map and the diff's file list). It touches
`apps/backend/app/research/edge_report.py`, `edge_report_compute.py`, `routes.py`, and adds one new
module, `edge_report_backtest_cache.py` (`EdgeReportBacktestCache`) — the durable per-(dataset x
strategy)-pair backtest sub-cache, giving the already-forward-declared `sub_cache=`/`workers=` hooks
(accepted-but-inert since J-04) real resumable/parallel effect. No new displayed value or entity is
introduced (the spec's own "Data-contract additions: None new" claim, verified against the diff).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Compute-job snapshot `progress.backtests_from_cache` (registered since iter-4) | OK — same field, same owner, same endpoint; only its runtime value now increments | `apps/backend/app/research/edge_report.py:408-416` (`_ProgressReporter.note_cache_hit`, the ONLY new call site bumping `self._from_cache`); `:418-423` (`pair_done()`, unchanged, still the sole reader of `self._from_cache` into the emitted patch); `apps/backend/app/research/routes.py:2213-2219` (`GET /research/edge-report/compute` still reads `registry.edge_report_compute.snapshot()` verbatim, untouched this iteration) |
| Not-computed edge-report payload (registered since iter-4, `peek_strategy_comparison_report`) | OK — zero diff this iteration | grep-confirmed: no hunk in `edge_report.py`'s diff touches `peek_strategy_comparison_report`; `GET /research/edge-report` route body untouched in `routes.py`'s diff |
| `EdgeReportBacktestCache` / `edge_report_backtests.db` (new module this iteration, pre-registered as a "rebuildable accelerator — explicitly NOT canonical" at baseline) | OK — sole computer of a pair's `result` stays `_run_backtest` (unchanged); the cache only stores/retrieves, never computes | `apps/backend/app/research/edge_report_backtest_cache.py:173-207` (`lookup`/`publish` — no compute path, mechanically incapable of running a backtest); `edge_report.py:156-177` (`_build_caching_run_pair`'s `run_pair` closure calls the SAME `_run_backtest` on a miss, publishes, returns — never a second backtest implementation); key composition in `edge_report_backtest_cache.py:95-121` (`pair_cache_key`) is byte-for-byte identical to the blueprint's newly-refined bullet (8 named components, sha256 of canonical JSON, `bar_store_signature` reusing `setups._store_signature` verbatim) |
| Sub-cache read surface | OK — no non-canonical serving | `routes.py:1616-1623` (`get_edge_report_backtest_cache` dependency) is wired into exactly one place, `trigger_edge_report_compute` (`routes.py:2187-2208`, the POST route) — never into any GET route, never returned as raw pair data on the wire. Full-repo grep confirms `EdgeReportBacktestCache`/`pair_cache_key`/`TAPEOLOGY_EDGE_SWEEP_CACHE_DB` appear in exactly 7 files: the module, its test file, `edge_report.py`, `edge_report_compute.py`, `routes.py`, and their two test files — no MCP file, no frontend file |

Blueprint cross-check: `runs/goal-session-fast_wall/state/blueprint.md`'s iter-5 update (diffed
directly against the iter-5 snapshot) is exactly what its own changelog note claims — one expanded
"rebuildable accelerators" bullet (the `edge_report_backtests.db` key composition), one appended
clause to the compute-job snapshot's Notes column, and one new HTML-comment codebase probe. No row
added or removed from either the Information Architecture table or the Data Contract table; no
`blueprint.reapproval-requested` marker was written (state/ contains only the original
`blueprint.approved`), consistent with "no nav-skeleton change."

## Information Architecture check

Zero new pages/routes/features this iteration — confirmed by the ui-surface-map ("Frontend surfaces
changed: 0... Navigation changes: no") and independently by the diff's file list (no file under
`apps/frontend/` appears in `git diff <snapshot-sha>`). `/structure`'s Edge Report section is
byte-unchanged; it remains J-04's already-registered home per the blueprint's IA table. The
`GET /edge-report/compute` and `POST /edge-report/compute/cancel` routes are untouched; the only
route-level change is a new FastAPI dependency (`sub_cache`) injected into the existing
`POST /edge-report/compute` route — same path, same request/response shape.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/structure` Edge Report section (unchanged) | OK — no new surface, no nav change | `reports/phase-goal-fast_wall-iter-5-ui-surface-map.md` ("Frontend surfaces changed: 0"); `git diff` file list has zero `apps/frontend/` entries |
| CLI-only parallel provider (`python -m app.research.edge_report_compute --workers N`) | OK — no UI surface expected or claimed; terminal-only, explicitly out of scope for a button | `apps/backend/app/research/edge_report_compute.py` `main()`; iteration spec's own "Frontend (if applicable): None planned" and "OUT OF SCOPE: Wiring workers > 1 ... into the button path" |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md`'s "AUTO:capabilities" block is updated to (a) replace stale iter-4 prose ("There is no
  button or control anywhere in the app yet...") with an accurate description of the already-shipped
  "Compute edge report" button/counter, and (b) list the three `/edge-report/compute*` routes in the
  REST enumeration. This is documentation catch-up for an iter-4 capability the README apparently
  never mentioned, not a new capability introduced this iteration — flagged here only for
  transparency, not as a coherence defect.
- The manager (`EdgeReportComputeManager.trigger()`) never passes `workers` to
  `run_strategy_comparison_report`, so the browser-triggered compute path and the CLI warmer both
  funnel through the identical `_split_cells`/`_run_backtest` aggregation code — confirmed by
  `edge_report.py:355-359`'s dispatch (`if sub_cache is not None and workers is not None and
  workers > 1:`) and the CLI-only reachability of `_parallel_prewarm_sub_cache`. No divergent
  computation path exists between the two entry points; noted here as supporting evidence for the
  Data Contract PASS above, not a separate finding.
