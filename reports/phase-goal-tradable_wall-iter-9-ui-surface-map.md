# Phase goal-tradable_wall-iter-9 — UI Surface Map

**Phase:** goal-tradable_wall-iter-9
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/structure` | Edge Report panel — warm-cache render (`section[aria-label="Edge report"]` → `EdgeReportBody`; `data-testid="edge-report-register"`, `"edge-report-train-table"`, `"edge-report-holdout-table"`, `"edge-report-surviving-table"`/`"edge-report-surviving-empty"`) | Changed behavior | `GET /research/edge-report` now serves through the new `EdgeReportCache` (`routes.py`'s `get_edge_report` gained a `cache` dependency); response shape is unchanged, only latency | Warm the cache (call `GET http://localhost:8301/research/edge-report` once against a populated dataset registry so it completes, or restart the backend after a prior warm run so the persisted cache is loaded), then load `/structure` in a browser. Confirm the panel leaves the `data-testid="edge-report-loading"` state within a few seconds (not the ~10+h original wait), then confirm the values rendered in `edge-report-train-table`/`edge-report-holdout-table` match a direct `curl :8301/research/edge-report` response for the same fields byte-for-byte. |
| `/structure` | Edge Report panel — cold-cache loading state (`data-testid="edge-report-loading"`) | Changed behavior (regression check) | A cache miss must still fall back to the original honest long-compute path — never a fabricated or partially-populated result | Point the backend at a fresh cache DB that has never been warmed (set `TAPEOLOGY_EDGE_REPORT_CACHE_DB` to a new empty temp path, or delete `.data/edge_report_cache.db`), restart the backend, then load `/structure`. Confirm the panel immediately shows `data-testid="edge-report-loading"` and does NOT show `data-testid="edge-report-unavailable"` or any populated table row while the compute is still running. |
| `/structure` | Edge Report panel — key-busting after a dataset/config change | Changed behavior | The cache key includes dataset checksums + strategy registry + `config_fingerprint` + a conservative whole-config hash; any of these changing must force a recompute rather than serve a stale cached report | With a warmed cache in place, register a new dataset (or change a cache-key-affecting config field such as `pnl_min_sample_size`), then request `GET /research/edge-report` again (or reload `/structure`). Confirm the panel goes back to the `edge-report-loading` state (a fresh recompute), not a stale, now-incorrect `edge-report-register`/table render from before the change. |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/edge_report_cache.py` (new) — `EdgeReportCache`: a persisted SQLite
  result cache (WAL + busy_timeout) plus an in-process atomic `(key, result)` fast path. Purely
  internal accelerator plumbing behind `GET /research/edge-report`; nothing in the UI reads,
  displays, or configures it directly — no UI surface affected beyond the latency change captured
  in the table above.
- `apps/backend/app/research/edge_report.py` — `run_strategy_comparison_report` was split into a
  thin cache-dispatching wrapper over a renamed `_compute_strategy_comparison_report` (the
  unchanged original computation body). Internal refactor only; the externally-visible effect is
  already captured by the route rows above — no additional UI surface.
- `apps/backend/app/research/pnl_ledger.py` — new `append_strategy_comparison_row` function
  (composes one ledger row from a completed 3-way comparison report). Not called by any API route
  — reachable only from `pnl_history.py`'s CLI. No UI surface affected.
- `apps/backend/app/research/pnl_history.py` — new `append_strategy_comparison_and_render`
  function plus CLI flags `--append-report`/`--enhancement-id`/`--title`/`--out`. This is an
  operator-run terminal command, not part of the web app (no route, no button) — no UI surface
  affected. The pre-existing no-flag `main()` behavior is unchanged.
- `apps/backend/tests/test_edge_report_cache.py` (new), plus additions to
  `test_edge_report.py`, `test_edge_report_api.py`, `test_pnl_ledger.py`, and new
  `test_pnl_history.py` — test coverage for the above; no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 1 (the existing `/structure` Edge Report panel — behavior/latency
  only; zero frontend source files modified this iteration)
- **New pages/routes:** 0
- **Modified components:** 0 (no `apps/frontend/**` file changed; `EdgeReportBody` and its
  children render the identical response shape, just arriving faster once warmed)
- **Navigation changes:** no
- **Backend-only changes:** 4 backend source files with no UI surface
  (`edge_report_cache.py` new, `edge_report.py` internal dispatcher split, `pnl_ledger.py`,
  `pnl_history.py`), plus 5 test files
