# Iteration 4 — Coherence Audit

**Iteration:** goal-tradable_wall-iter-4
**Date:** 2026-07-14
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Summary

Backend-only iteration (`Frontend Present: no`, confirmed empty by `git diff --stat -- 'apps/frontend/*' 'apps/web/*' 'frontend/*' 'src/*'` and by `reports/phase-goal-tradable_wall-iter-4-ui-surface-map.md` = "N/A — Backend-only phase"). It registers a new strategy (`structure_tape_map`) and extends the existing era-3 `edge_report.py` additively to serve the 3-way edge report. Both values were already rows in `blueprint.md` at baseline (confirmed: `blueprint.md` does not appear in the diff stat), so no blueprint edit was required or made.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Edge-report cells (strategy × class × side × reaction × feed; n, R stats, $ full register, null baseline) | OK | Computed by `apps/backend/app/research/edge_report.py:426` (`run_strategy_comparison_report`, the sole new computer — verified only one function of that name in the repo); served by `apps/backend/app/research/routes.py:2076-2077` (`@router.get("/edge-report")` under `router = APIRouter(prefix="/research", ...)` at `routes.py:103` → resolves to exactly `GET /research/edge-report`, matching the registered endpoint verbatim). |
| Backtest trade-population aggregation (n / gross / net R / $ / win_rate / max_drawdown) feeding a cell | OK — reused, not re-derived | `edge_report.py:73` imports `_aggregate` from `.backtests` (the existing canonical aggregator) and calls it at `edge_report.py:360,369` — no second R/$ formula. |
| Touch events + reaction labels (`rejected`/`broke`/`chopped`) joined to a cell | OK — read verbatim | `edge_report.py:447` calls `compute_setups(bar_store, config)` once for the whole report (not per-dataset/per-split) — the canonical `setups.py` function, not a re-implementation. |
| Tradable level map bands (arming source for `structure_tape_map`) | OK — read verbatim | `apps/backend/app/research/backtests.py:103` imports `compute_tradability` from `.tradability`; `backtests.py:807` calls it directly — the same canonical function `GET /research/tradability` serves, never a re-detection of levels/bands in the runner (matches iter spec's explicit instruction). |
| `structure_tape_map` strategy definition + registry membership | OK | `apps/backend/app/config.py:41` (`STRATEGY_TAPE_MAP_ID`), `config.py:69` (added to the single `_STRATEGY_IDS_IN_ORDER` tuple), `config.py:1513` (`strategy_definition` returns the identical `structure_tape` grammar dict keyed by either id — one branch, no second grammar). `strategies.py` (unchanged, absent from the diff) continues to project `Config.strategy_registry()` verbatim to `GET /research/strategies`, so the new id surfaces there automatically with no second registration path. |
| MCP `edge_report` proxy | OK — byte-identical mirror | `apps/backend/app/mcp/__init__.py:106` (`_STATIC_PATHS["edge_report"] = "/research/edge-report"`) + `mcp/__init__.py:280` (`types.Tool(name="edge_report", ...)`) — same dict/pattern as the existing `tradability`/`setups` proxies, no computation added. Grep confirms no second `/research/edge-report` route or second `run_strategy_comparison_report` definition anywhere in `apps/backend/app`. |
| Champion pointer | OK — untouched | `run_strategy_comparison_report` never calls `store.get_champion_pointer()` or any promotion/ledger-append path; the module docstring and `_cell_clears_gate`'s own docstring (`edge_report.py`) both state the informational gate is "used ONLY to rank/annotate... this module promotes nothing." |

The developer's own test suite independently backs the single-source claim: `apps/backend/tests/test_edge_report_api.py::test_edge_report_matches_the_module_function_byte_for_byte` asserts the route's JSON is byte-identical to a direct call of `run_strategy_comparison_report`, and `test_edge_report_route_wired_through_the_existing_get_bar_store_seam` asserts the route uses the same `Depends(get_bar_store)` / `Depends(get_dataset_store)` seams as every other route (no second store construction).

No new displayed value appears in this iteration that is absent from the Data Contract (backend-only; nothing is displayed yet — J-05 renders it next).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /research/edge-report` (new REST endpoint + MCP proxy) | OK / N/A — no UI surface this iteration | API-only addition; no nav check applies. The iteration spec's "Blueprint conformance" section and "OUT OF SCOPE" both confirm the `/structure` → **Edge Report** section render is deferred to J-05, and the blueprint (`runs/goal-session-tradable_wall/state/blueprint.md`, Feature/journey homes table) already reserves that canonical home. No nav/sidebar/router file was touched (frontend diff is empty), so no parallel shell or hidden-feature risk was introduced. |

No new page/route/feature landed in the UI this iteration, so Part B (navigation reachability, duplicate home, parallel shell) has nothing to check.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `edge_report.py`'s new `_cell_clears_gate` (positivity gate: net R > 0 AND net $ > 0 AND n ≥ `pnl_min_sample_size` AND beats null) mirrors the logic of the module's existing `_is_positive_edge` gate (used by the champion-only report above it in the same file) rather than calling it directly. Both live inside the single owning module (`edge_report.py`), so this is not a Data-Contract violation (no second module/endpoint), and the new gate is explicitly documented as informational-only (never a promotion path) — but a future cleanup could factor the shared predicate into one helper both call, for code-level DRY rather than coherence.
