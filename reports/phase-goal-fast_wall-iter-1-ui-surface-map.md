# Phase goal-fast_wall-iter-1 — UI Surface Map

**Phase:** goal-fast_wall-iter-1
**Date:** 2026-07-17
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/structure` | `NotComputedPanel` — new component in the Edge Report section, `data-testid="edge-report-not-computed"` (`apps/frontend/app/structure/page.tsx:287-297`) | New component / New UI state | A cold edge-report cache with at least 1 registered dataset now renders an honest "not computed" panel instead of the page silently starting the multi-hour backtest sweep | Point the frontend at a backend whose edge-report cache is cold with at least 1 registered dataset. Navigate to `/structure` and wait for the Edge Report panel to finish loading. Confirm the element `[data-testid="edge-report-not-computed"]` is present, showing the exact headline text "Edge report not computed yet." and a non-empty detail line beneath it. Confirm `[data-testid="edge-report-empty"]` is NOT present at the same time. |
| `/structure` | Edge Report warm-empty state — `EmptyState` (`data-testid="edge-report-empty"`) + register banner (`data-testid="edge-report-register"`), rendered via `EdgeReportBody` (`apps/frontend/app/structure/page.tsx:758-773`) | Regression-guard (existing behavior, now reached through the rewired route) | The backend route was rewired to call a new `peek_strategy_comparison_report` function; this pre-existing frozen state must still render byte-identically for a warm, all-empty cache | Pre-warm the backend's edge-report cache with an all-empty report (e.g. call `EdgeReportCache.compute_and_publish` directly, or use a fixture that already has a warm empty row). Navigate to `/structure` and confirm the Edge Report panel shows `[data-testid="edge-report-empty"]` with text "No edge-report cells yet." and `[data-testid="edge-report-register"]` with non-empty register text. Confirm `[data-testid="edge-report-not-computed"]` is NOT present. |
| `/structure` | Edge Report mount-time fetch — `fetchEdgeReport()` invoked inside the page's `useEffect` (`apps/frontend/app/structure/page.tsx:1248-1274`, call at line 1269), hitting `GET /research/edge-report` | Changed behavior (backend side effect removed) | The same automatic on-load fetch that used to trigger a multi-hour backend computation on a cold cache no longer does so — it now always returns promptly regardless of cache state | With a backend whose edge-report cache is cold and has ≥1 registered dataset, start a process/CPU monitor on the backend (e.g. `top` or equivalent). Navigate to `/structure`. In the browser network tab, confirm the `GET /research/edge-report` request completes with HTTP 200 in well under a minute (not hours). On the backend monitor, confirm CPU usage does not sustain near 100% after the request completes — it should return to idle within a few seconds. |
| `/structure` | `GET /research/edge-report` response contract consumed by `fetchEdgeReport()` (`apps/frontend/lib/api.ts:1144-1165`) and typed by `EdgeReportPayload` (`apps/frontend/lib/types.ts:1354-1380`) | Changed API contract (backend-api, consumed by this one frontend surface) | The endpoint's cold-cache response shape changed from "the full computed report" to a discriminated three-way shape (`not_computed` / empty-registry-full-shape / warm-verbatim) | Call `GET /research/edge-report` directly (curl, or the `mcp__tapeology__edge_report` MCP tool) against a backend with a cold cache and ≥1 registered dataset. Confirm the JSON body contains `"status": "not_computed"`, a non-empty string `"detail"`, an integer `"dataset_count"` equal to the number of registered datasets, a non-empty string `"register"`, and `"compute": null`. |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `EdgeReportCache.lookup()` / `EdgeReportCache.compute_and_publish()` (`apps/backend/app/research/edge_report_cache.py`) — new cache read/write methods added beside the untouched `get_or_compute`. `compute_and_publish` is fully implemented and unit-tested but has no caller anywhere in the running application yet (the future "Compute edge report" trigger is a later phase, J-04) — no UI surface affected this phase.
- `resolve_cache_db_path()` (`apps/backend/app/research/edge_report_cache.py`) — extracted the cache-database file-path resolution policy into one shared function, called by `routes.py`'s `get_edge_report_cache()` dependency. Reproduces the exact same resolved path as before — a pure internal refactor with no observable effect.
- `peek_strategy_comparison_report()` and `_verified_records()` (`apps/backend/app/research/edge_report.py`) — the new backend logic that decides which of the three response shapes to serve. Its outward, user-visible effect is already captured in the `GET /research/edge-report` row above; the functions themselves are internal implementation, not directly user-facing.
- `get_edge_report_cache()` dependency wiring change in `apps/backend/app/research/routes.py` (now delegates to `resolve_cache_db_path()`) — internal-only, no observable UI difference; the pinned `Depends(...)`/`cache=cache` signature itself is unchanged.
- MCP `edge_report` tool (`apps/backend/app/mcp_server.py`, unchanged code — only its test coverage was extended) — a read-only proxy that mirrors the new contract byte-for-byte, but MCP tools are a machine/agent interface, not a human-facing UI surface — no UI surface affected.
- Backend test-only files (`apps/backend/tests/test_edge_report_cache.py`, `test_edge_report.py`, `test_edge_report_api.py`, `test_mcp_server.py`) — test coverage additions/adaptations only, no runtime behavior a user could observe beyond what the rows above already describe.

---

## Summary

- **Frontend surfaces changed:** 1 (the Edge Report section of `/structure`)
- **New pages/routes:** 0
- **Modified components:** 2 (`NotComputedPanel` added as a new component; the Edge Report section's conditional render branch plus its supporting types (`lib/types.ts`, `lib/api.ts`) updated to recognize the new state)
- **Navigation changes:** no
- **Backend-only changes:** 6
