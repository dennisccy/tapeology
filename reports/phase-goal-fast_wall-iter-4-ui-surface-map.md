# Phase goal-fast_wall-iter-4 — UI Surface Map

**Phase:** goal-fast_wall-iter-4
**Date:** 2026-07-17
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/structure` | `NotComputedPanel` — "Compute edge report" button (`data-testid="edge-report-compute-button"`) | Changed behavior | The previously dead-end "not computed" panel gains an in-page action to trigger the first-ever real edge-report compute (no more out-of-band script needed) | With a cold edge-report cache (no compute ever run) navigate to `/structure`, confirm the button renders with text exactly "Compute edge report" and is enabled, click it, and confirm the label immediately changes to "Computing…" and the button becomes disabled (`disabled` attribute present) |
| `/structure` | `NotComputedPanel` — progress line (`data-testid="edge-report-compute-progress"`) | New component | Surfaces the compute job's live progress while it runs, so the operator isn't staring at a frozen page | While a triggered compute job has `state === "running"`, confirm the progress line renders text matching the pattern `{number} / {number} backtests`, and confirm the displayed numbers change (or the line disappears because the job reached a terminal state) on at least one subsequent poll tick (~700ms) without any page reload |
| `/structure` | `NotComputedPanel` — failed-state error line (`data-testid="edge-report-compute-error"`) | New component | Surfaces the backend's verbatim failure message when a triggered compute job ends in `state: "failed"`, instead of a generic error | Arrange a compute job that resolves `state: "failed"` (e.g., trigger a compute over a dataset with a corrupted/tampered file so the store's integrity check fails), reload `/structure`, and confirm the red error line shows the exact backend `error` string verbatim (not a paraphrase), and that the button simultaneously relabels to "Retry compute" and is re-enabled |
| `/structure` | `NotComputedPanel` — trigger-error line (`data-testid="edge-report-compute-trigger-error"`) | New component | Surfaces a client-side failure of the POST itself (e.g., backend unreachable at click time), kept visually distinct from a server-side `failed` job | With the backend stopped/unreachable, click "Compute edge report" on `/structure` and confirm a red line renders reading "Backend unreachable — is the API running?" (or the backend's own `detail` string if reachable but erroring), while the main button returns to its enabled idle state rather than staying stuck on "Computing…" |
| `/structure` | Edge Report section — `NotComputedPanel` → `EdgeReportBody` transition | Changed behavior | On job completion the dead-end panel is replaced in place by the pre-existing finished-report render — closing the loop from "not computed" to "computed" without leaving the page | Trigger a compute against a scoped fixture backend, wait for `state` to reach `"done"` via polling, and confirm the `edge-report-not-computed` panel disappears and is replaced by the existing report render (`edge-report-register`, `edge-report-cell-row` rows, and `edge-report-surviving-table`) with zero full-page reload (URL and scroll position unchanged) |
| `/structure` | `NotComputedPanel` — mount-time state resume | Changed behavior | A page load that lands mid-job or after a job already finished/failed shows the correct state immediately, instead of always resetting to the idle "Compute edge report" button | Trigger a compute, then (while it is still `state === "running"`) reload `/structure` in a fresh page load and confirm the panel shows the "Computing…" disabled button and an active progress line immediately on load — not the idle "Compute edge report" button — with no extra click required |

<!-- Change Type options used: Changed behavior | New component -->

---

## Backend-Only Changes (No UI Impact)

- `POST /research/edge-report/compute/cancel` — cooperative cancel of an in-flight compute job.
  Implemented, tested, and exported from `apps/frontend/lib/api.ts` as `cancelEdgeReportCompute()`,
  but no button or other UI element calls it anywhere in `apps/frontend/app/structure/page.tsx` —
  no UI surface is affected this iteration. An operator can still hit the route directly (e.g. via
  `curl`), but there is nothing to click.
- `python -m app.research.edge_report_compute` CLI warmer (`apps/backend/app/research/edge_report_compute.py`'s
  `main()`, flags `--workers`, `--force`, `--out`) — an operator-facing terminal tool, not a browser
  UI surface; it shares the same cache/storage path as the button (a warm CLI run means the
  button's next click serves the cached result instantly) but has no in-page representation.
- Five new keyword-only parameters on `run_strategy_comparison_report` (`force`, `progress`,
  `should_abort`, `sub_cache`, `workers`) in `apps/backend/app/research/edge_report.py` — internal
  function-signature additions. `force` and `progress`/`should_abort` are exercised indirectly
  through the new routes above (no direct UI element of their own); `sub_cache`/`workers` are
  accepted but currently inert — no UI or CLI behavior differs based on their value this iteration.
- `EdgeReportComputeCancelled` exception, `_count_eligible_pairs`, and `_ProgressReporter` helper
  (all in `edge_report.py`) — internal implementation details of the compute/cancel/progress
  plumbing with no direct UI coupling of their own.
- `ResearchRegistry.edge_report_compute` property and `EdgeReportComputeRequest` request model in
  `apps/backend/app/research/routes.py` — internal wiring that exposes the manager to the three
  routes above; no UI surface of its own.

---

## Summary

- **Frontend surfaces changed:** 1 (`/structure`'s Edge Report `NotComputedPanel`)
- **New pages/routes:** 0 (no new browser page; 2 new REST routes — `POST`/`GET`
  `/research/edge-report/compute` — plus `POST /research/edge-report/compute/cancel`, all consumed
  by the existing page, none is a new UI route)
- **Modified components:** 2 (`NotComputedPanel` gains the button/progress/error sub-elements;
  `StructurePage` gains the state, mount-time seed, and poll `useEffect` that drive it)
- **Navigation changes:** no
- **Backend-only changes:** 5 (cancel route with no UI caller, CLI warmer, 5 inert/indirect hook
  parameters, 3 internal helper/exception additions, registry wiring)
