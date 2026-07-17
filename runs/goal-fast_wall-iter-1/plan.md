# goal-fast_wall-iter-1 Execution Plan

Session `fast_wall`, iteration 1, single target journey **J-01** ("Stop the bleeding — `GET
/research/edge-report` never computes"). Required-still-passing: J-07 (foundation regression
sentinel). This is the opening journey of the "Fast Wall" performance interlude (`docs/goal.md`),
which layers on top of the frozen era-1–5B foundation without changing any research value — only
*when* the edge-report sweep runs.

**Alignment check:** the phase spec matches `docs/goal.md`'s stated dependency order
(J-01 → J-02 → J-03 → J-04 → J-05, J-06 riding on J-02) and Success Criterion #2 verbatim
("`/structure` never triggers compute"). No drift, no scope creep detected — the spec's OUT OF
SCOPE list is internally consistent with the goal doc's Non-Goals ("no compute on page load",
"no new nav/page/Config field/MCP tool"). Codebase probe below confirms every file/line the spec
cites still matches current `main`.

## What to Build

- `EdgeReportCache.lookup(records, config) -> dict | None` — checks the hot slot then the durable
  row for the current key; **never** calls a compute function; `None` on a genuine miss.
- `EdgeReportCache.compute_and_publish(dataset_store, config, compute_fn) -> dict` — always calls
  `compute_fn` exactly once and republishes to both the hot slot and the durable row (the future
  J-04 "force" path; exercised directly by this iteration's own tests since no route calls it yet).
- Extract the cache DB-path resolution policy (env `TAPEOLOGY_EDGE_REPORT_CACHE_DB` else
  `.data/edge_report_cache.db` sibling of the dataset dir) out of `routes.py`'s inline
  `get_edge_report_cache()` body into one shared resolver function in `edge_report_cache.py`; the
  route's dependency calls it, reproducing today's exact resolved path.
- `edge_report.peek_strategy_comparison_report(store, dataset_store, bar_store, config, *, cache)`
  — three branches: store-integrity errors raise `EdgeReportError` exactly as today; an **empty**
  dataset registry still computes inline (today's O(1), zero-backtest shape, no `status` key); a
  **non-empty + warm** key returns `cache.lookup(...)` verbatim; a **non-empty + cold** key returns
  `{status: "not_computed", detail: <non-empty str>, dataset_count: <int>, register:
  backtests.REGISTER, compute: null}`.
- `routes.py`: rewire `GET /research/edge-report` to call `peek_strategy_comparison_report`
  instead of `run_strategy_comparison_report`, preserving the exact `Depends(get_bar_store)` /
  `Depends(get_dataset_store)` / `Depends(get_edge_report_cache)` signature and the literal
  `cache=cache` kwarg — pinned verbatim by `test_edge_report_api.py:114-141`; do not edit that test.
- Frontend: extend the edge-report response type with the not-computed shape; render a distinct
  panel on `/structure` when `status === "not_computed"` — headline "**Edge report not computed
  yet.**", server `detail` verbatim — checked *before* the existing `EdgeReportBody` branch, reusing
  the page's existing `LoadingPanel`/`UnavailablePanel`/`EmptyState` visual pattern. No new button,
  no POST, no polling (J-04 scope). No change to `fetchEdgeReport()`'s call site or the frozen
  warm-empty-cache text/testids.
- Tests: a compute-spy proving zero `_compute_strategy_comparison_report` calls on a cold-cache GET;
  adapted route tests that pre-warm via `compute_and_publish` before asserting warm-serve/byte
  identity; new tests for the three `peek_strategy_comparison_report` branches, the path resolver,
  and MCP↔REST byte-identity in the new not-computed state.

## Agents Required

- developer: yes -- implements both the backend contract change and the frontend panel in one pass
  (this project's convention: a single full-stack developer dispatch per phase, not split agents).
- backend-data: yes -- `edge_report_cache.py` (2 new methods + path resolver), `edge_report.py`
  (`peek_strategy_comparison_report`), `routes.py` rewire, and all backend test additions/adaptations.
- frontend-ux: yes -- `lib/types.ts` type extension, `lib/api.ts` return-type update (no fetch logic
  change), `structure/page.tsx` new panel + render branch.

Frontend Present: yes

## Files to Create/Modify

Backend:
- `apps/backend/app/research/edge_report_cache.py` -- add `lookup()`, `compute_and_publish()`, and
  the shared cache-DB-path resolver, beside the untouched `get_or_compute` (leave its 16 existing
  tests in `test_edge_report_cache.py` untouched).
- `apps/backend/app/research/edge_report.py` -- add `peek_strategy_comparison_report(...)`; import
  `REGISTER` from `backtests` if not already in scope (it is, via `_compute_strategy_comparison_report`'s
  return dict at line ~487) — read it, never restate the literal.
- `apps/backend/app/research/routes.py` -- rewire `get_edge_report` (lines 2093-2117) to call
  `peek_strategy_comparison_report`; route `get_edge_report_cache`'s inline path logic (lines
  1564-1576) through the new shared resolver.
- `apps/backend/tests/test_edge_report_cache.py` -- add new tests for `lookup`/`compute_and_publish`/
  the resolver beside the existing 16 (`test_cold_cache_miss_calls_compute_fn_once...` through
  `test_cache_source_never_computes_a_research_value_itself`, lines 60-401) — none of those 16 change.
- `apps/backend/tests/test_edge_report_api.py` -- `test_edge_report_empty_registry_is_an_honest_200`
  (lines 41-51) and the two `Depends`/cache-wiring guard tests (lines 114-141) stay byte-unchanged.
  Adapt `test_edge_report_matches_the_module_function_byte_for_byte` (54-79),
  `test_edge_report_route_serves_a_warm_result_on_the_second_call_without_recomputing` (143-177), and
  `test_edge_report_route_response_is_byte_identical_whether_cache_is_cold_or_warm` (179-196) to the
  new contract (pre-warm via `compute_and_publish`, since a cold GET no longer computes). Add new
  tests for TC-1 (not-computed shape), TC-2 (compute-spy zero-calls), TC-3 (empty-registry unchanged,
  likely already covered by the untouched 41-51 test), TC-5 (integrity 500, likely already covered),
  TC-7 (405s, likely already covered by untouched `test_non_get_verbs_are_405...`).
- `apps/backend/tests/test_edge_report.py` -- unit-level tests for
  `peek_strategy_comparison_report`'s three branches called directly (not through the route).
- `apps/backend/tests/test_mcp_server.py` -- extend/add beside
  `test_edge_report_tool_byte_identical_to_rest` (line 540) and
  `test_edge_report_tool_byte_identical_after_recording_a_real_dataset` (line 556) to cover TC-6 (the
  new not-computed state's REST↔MCP byte-identity). No MCP server code changes — the tool is an
  existing byte-identical proxy; only new test coverage is needed.

Frontend:
- `apps/frontend/lib/types.ts` -- beside `EdgeReportResponse` (line 1354), add the not-computed
  companion shape (`status`, `detail`, `dataset_count`, `register`, `compute: null`) and a
  discriminated union type for `fetchEdgeReport`'s return.
- `apps/frontend/lib/api.ts` -- `fetchEdgeReport()` (line 1144) return type updated to the union;
  the fetch call itself (same endpoint, same shape passthrough) is unchanged.
- `apps/frontend/app/structure/page.tsx` -- add a `NotComputedPanel` (or similarly named) component
  near `LoadingPanel`/`UnavailablePanel`/`EmptyState` (lines 251-300); insert a new conditional branch
  in the Edge Report section's render (lines 1853-1862, currently `edgeReportResult === null ? ... :
  !edgeReportResult.ok || !edgeReport ? ... : <EdgeReportBody report={edgeReport} />`) that checks
  `edgeReport.status === "not_computed"` *before* falling into `EdgeReportBody`. No change to the
  `useEffect` mount fetch (line ~1228-1252) or to `EdgeReportBody`/its frozen testids (line 740,
  `edge-report-empty`/`edge-report-register` at 745-753).

Docs:
- `docs/handoffs/goal-fast_wall-iter-1-dev.md` -- required dev handoff (DoD item).

## UI Evolution

- New user-facing capability: opening `/structure` with a cold edge-report cache now shows an
  honest "Edge report not computed yet." panel instead of an indefinite spinner or a CPU-pinning
  hang — the page becomes safe to open regardless of cache state.
- New information displayed: the not-computed payload's `detail` (what triggers a compute) and
  `dataset_count` (how many datasets are registered) become visible when the cache is cold.
- New user actions: none this iteration — no button, no trigger (the "Compute edge report" control
  is J-04's scope). The only relevant action is navigating to `/structure`.
- UI surface changes: one new panel state inside the existing `/structure` → **Edge Report**
  section, added alongside its existing loading/unavailable/empty/populated states. No new page.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `LoadingPanel` / `UnavailablePanel` / `EmptyState`
  components (`app/structure/page.tsx` lines 251-300) as the template for the new not-computed
  panel — same rounded-border/centered-text/honest-state treatment, not a new visual language
  (per `docs/goal.md`'s Design Direction: "no new visual language").
- Layout: no layout change — the panel is one more conditional branch inside the existing
  `<section aria-label="Edge report">` / `<Panel title="Edge Report">` (lines 1844-1864).
- Key visual effects: none new. Dark-only, dense, terminal-grade, consistent with the amber-toned
  degraded/honest-absence styling `UnavailablePanel`/`EmptyState` already use. No glassmorphism, no
  glow — this project's structure pages do not use those effects.
- States to handle in the Edge Report section (five total after this change): loading (existing),
  fetch-unavailable (existing `UnavailablePanel`), **not-computed (new)**, warm-empty (existing
  frozen `EmptyState` "No edge-report cells yet." — byte-identical, untouched), warm-populated
  (existing `EdgeReportBody`).

## Key Test Scenarios

Full test-first contract (TC-1..TC-15) is in `docs/phases/goal-fast_wall-iter-1.md` — highlights:

- Cold cache + non-empty registry → `GET /research/edge-report` returns 200 with
  `status: "not_computed"`, non-empty `detail`, correct `dataset_count`, `register ==
  backtests.REGISTER`, `compute: null` — and a counting-spy proves **zero** calls to
  `_compute_strategy_comparison_report` (TC-1, TC-2).
- Empty registry → unchanged full-report shape, no `status` key (TC-3).
- Warm cache (published via `compute_and_publish`) → route response is byte-identical
  (`json.dumps(..., sort_keys=True)`) to a fresh, cache-cleared direct compute (TC-4).
- Dataset-store integrity error → still an explicit 500 with "integrity" in `detail`, cache bypassed
  entirely (TC-5).
- MCP `edge_report` tool and the REST route agree byte-for-byte in the new not-computed state (TC-6).
- POST/PUT/PATCH/DELETE on `/research/edge-report` still 405 (TC-7).
- `EdgeReportCache.lookup`/`compute_and_publish` behave exactly as specified in isolation (TC-8, TC-9).
- The extracted shared path resolver reproduces today's exact resolved path (TC-10).
- Browser (scoped keyless fixture, per NOTES — never the default real-corpus backend): cold cache →
  "Edge report not computed yet." panel visible, "No edge-report cells yet." absent (TC-11); warm
  all-empty cache → the frozen empty-state text and register banner render byte-identical to the
  iter-0 baseline (TC-12).
- `routes.get_edge_report`'s pinned `Depends`/`cache=cache` source wiring is unmodified (TC-13); the
  MCP tool list gains no new entry (TC-14).
- Full backend suite green; `config.config_fingerprint()` still `4d665603569b9dbf` (TC-15).
- J-07 regression sentinel: full backend suite + engine equivalence pass; the Edge-Report-section
  live-hazard leg is closed by construction (the old always-compute code path no longer exists,
  mechanically proven by the compute-spy) — the separate, unrelated `/research/setups` cold-scan
  slowness is a pre-existing, already-diagnosed gap for J-06, **not** a regression to fix here.

**Guardrails (do not touch, per phase spec OUT OF SCOPE):** `bars.py`, `datasets.py`, `levels.py`,
`tradability.py`, `backtests.py`, `setups.py`, or any of their source-introspection guard tests;
`EdgeReportCache.get_or_compute` and its 16 existing tests; any new nav entry/page, `Config` field,
or MCP tool; any "Compute edge report" button/POST/polling (J-04); any `bars.py`/`datasets.py`
acceleration (J-02) — a real-corpus cold GET still costs the existing ~31s `dataset_store.list()`
price this iteration, which is expected and not a failure.
