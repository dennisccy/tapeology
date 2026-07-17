# goal-fast_wall-iter-1 Dev Handoff

**Phase:** goal-fast_wall-iter-1
**Date:** 2026-07-17
**Agent:** developer
**Status:** complete

## What Was Built

J-01 ("Stop the bleeding — `GET /research/edge-report` never computes"), the opening journey of
the "Fast Wall" performance interlude. `GET /research/edge-report` no longer runs the multi-hour
backtest sweep synchronously inside a GET request; a cold cache now answers instantly with an
honest "not computed" payload, and `/structure` renders that as a distinct panel.

- `EdgeReportCache.lookup(records, config) -> dict | None` — checks the hot slot then the durable
  row for the current key; **never** calls a compute function; `None` on a genuine miss. This is
  now the GET path's exclusive read method.
- `EdgeReportCache.compute_and_publish(dataset_store, config, compute_fn) -> dict` — always calls
  `compute_fn` exactly once and republishes to both layers (the future operator/CLI "force" path,
  J-04). Both new methods live beside the untouched `get_or_compute` (its own 16 existing tests
  are unmodified).
- `resolve_cache_db_path(dataset_dir_resolved)` — the cache DB path policy (env
  `TAPEOLOGY_EDGE_REPORT_CACHE_DB` else `.data/edge_report_cache.db` sibling of the dataset dir),
  extracted from `routes.py`'s inline dependency body into one shared function in
  `edge_report_cache.py`, so a future CLI caller resolves the identical path.
- `edge_report.peek_strategy_comparison_report(store, dataset_store, bar_store, config, *, cache)`
  — the GET path's new exclusive entry point, three branches: a store-integrity error raises
  `EdgeReportError` exactly as today; an empty dataset registry still computes inline (today's
  O(1), zero-backtest shape, no `status` key); a non-empty registry consults `cache.lookup(...)`
  only — a warm key returns the report verbatim, a cold key returns
  `{status: "not_computed", detail: EDGE_REPORT_NOT_COMPUTED_DETAIL, dataset_count, register:
  backtests.REGISTER, compute: null}`.
- `edge_report._verified_records(dataset_store)` — a small shared helper extracted from
  `_split_datasets` (list + integrity-check + raise), reused by both `_split_datasets` and
  `peek_strategy_comparison_report` so the integrity-error message is defined in exactly one
  place.
- `routes.py`: `get_edge_report` rewired to call `peek_strategy_comparison_report` instead of
  `run_strategy_comparison_report`, preserving the exact `Depends(get_bar_store)` /
  `Depends(get_dataset_store)` / `Depends(get_edge_report_cache)` signature and the literal
  `cache=cache` kwarg (pinned verbatim by `test_edge_report_api.py`'s two guard tests — left
  byte-unchanged). `get_edge_report_cache()` now delegates its path resolution to
  `resolve_cache_db_path`.
- Frontend: `/structure`'s Edge Report section renders a new `NotComputedPanel` (headline "Edge
  report not computed yet.", the server `detail` verbatim) when the fetched payload's
  `status === "not_computed"`, checked before the existing `EdgeReportBody` branch. No button, no
  POST, no polling (deliberately out of scope — J-04). The frozen warm-empty-cache text ("No
  edge-report cells yet.") and the register banner are untouched and reachable.

## Files Changed

- `apps/backend/app/research/edge_report_cache.py` — added `resolve_cache_db_path()`, `lookup()`,
  `compute_and_publish()`, and the `_CACHE_DB_ENV` constant, beside the untouched `get_or_compute`.
- `apps/backend/app/research/edge_report.py` — added `_verified_records()` (refactored
  `_split_datasets` to use it), `EDGE_REPORT_NOT_COMPUTED_DETAIL`, and
  `peek_strategy_comparison_report()`; updated `run_strategy_comparison_report`'s docstring to
  reflect that the route no longer calls it directly; updated `__all__`.
- `apps/backend/app/research/routes.py` — rewired `get_edge_report` to call
  `peek_strategy_comparison_report`; routed `get_edge_report_cache()`'s path logic through
  `resolve_cache_db_path`; updated both functions' docstrings and the section comment block.
- `apps/backend/tests/test_edge_report_cache.py` — added 9 tests for `lookup`, `compute_and_publish`,
  and `resolve_cache_db_path`, beside the untouched 16 existing tests.
- `apps/backend/tests/test_edge_report.py` — added 5 tests for `peek_strategy_comparison_report`'s
  three branches, the integrity-bypass discipline, and a source-coherence guard.
- `apps/backend/tests/test_edge_report_api.py` — added `EdgeReportCache` import; added 1 new test
  (cold-cache not-computed shape + compute-spy); adapted 3 existing tests to the new contract (a
  cold GET no longer computes) — `test_edge_report_matches_the_module_function_byte_for_byte` now
  pre-warms via `compute_and_publish` before comparing; the former
  `..._serves_a_warm_result_on_the_second_call...` and `..._byte_identical_whether_cache_is_cold_
  or_warm` tests were renamed and rewritten to match the new contract (repeated warm calls never
  recompute; repeated cold calls are byte-identical to each other). The two pinned `Depends`/
  `cache=cache` guard tests and the empty-registry/integrity/405/hermetic-path tests are
  byte-unchanged.
- `apps/backend/tests/test_mcp_server.py` — adapted `test_edge_report_tool_byte_identical_to_rest`
  (by that point in the module an earlier test has already registered a dataset, so this GET
  naturally returns the not-computed shape; updated the assertion and docstring accordingly) and
  fixed a stale docstring claim in `test_edge_report_tool_byte_identical_after_recording_a_real_
  dataset` (its assertions needed no change — it never hardcoded a shape). No MCP server code
  changed.
- `apps/frontend/lib/types.ts` — added `status?: undefined` to `EdgeReportResponse`, added
  `EdgeReportNotComputed`, added the `EdgeReportPayload` discriminated union.
- `apps/frontend/lib/api.ts` — `fetchEdgeReport()`'s return type updated to `EdgeReportPayload`;
  no change to the fetch call itself.
- `apps/frontend/app/structure/page.tsx` — added `NotComputedPanel` component; updated
  `edgeReportResult` state type; added the `status === "not_computed"` render branch before
  `EdgeReportBody`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1407 passed, 7 skipped** (1414 collected), 0 failed, 0 errors, exit 0. The 7 skips are
the same three credential/opt-in-gated files as the iter-0 baseline, unaffected by this change.
The 15 net-new tests exactly account for 1414 − 1399 (iter-0's baseline collected count).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_observer_equivalence.py tests/test_profile_equivalence.py -q`
Result: **22 passed**, 0 skipped — engine/profile equivalence guards green (J-07).

Command: `cd apps/backend && .venv/bin/python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"`
Result: `4d665603569b9dbf` — matches the pinned fingerprint exactly (zero `Config` fields added, as
required).

Command: `cd apps/frontend && NEXT_DIST_DIR=<isolated dir> npm run build`
Result: compiled successfully, zero TypeScript errors (strict mode), all 7 routes built including
`/structure`. (The isolated `NEXT_DIST_DIR` build auto-mutated `tsconfig.json`/`next-env.d.ts` as
a side effect of Next.js's config-sync step; both were reverted via `git checkout` after the build
so no unrelated diff remains.)

## Live verification (beyond the automated suite)

Ran a scoped backend (fresh temp journal/dataset/bar dirs, port 8391) + frontend (port 3391)
pointed at it, both started via the real `uvicorn`/`next dev` commands (not TestClient):

- Empty registry → `GET /research/edge-report` returns the full pre-J-01 report shape, no
  `status` key.
- Recorded one dataset (the committed reference fixture) → `GET /research/edge-report` returns the
  not-computed payload in **28ms** with `dataset_count: 1`.
- Browser (Chrome MCP) navigation to `/structure` on this scoped backend: confirmed via
  `await_text` + full-page text extraction that the "Edge report not computed yet." headline and
  its exact `detail` string render, and "No edge-report cells yet." is absent (TC-11).
- Pre-warmed the SAME cache DB the running backend resolves to via `EdgeReportCache.compute_and_
  publish` (an all-empty report), reloaded `/structure`: confirmed "No edge-report cells yet."
  renders byte-identical to the frozen text (TC-12).
- Torn down cleanly (port-based kill, both ports confirmed free before proceeding).

Then ran the project's real `scripts/dev.sh` stack against the **default real corpus**
(`.data/datasets`, 882MB, 18 registered datasets — the exact hazard iter-0's SAFETY NOTE
documented):

- `GET /research/edge-report` against the real corpus: **28.9 seconds**, `status: "not_computed"`,
  `dataset_count: 18` — bounded by the still-unaccelerated `dataset_store.list()` cost (J-02's
  future scope), never by the sweep. This is the literal fix for the Vision section's documented
  hazard ("the backend worker pinned at 98% CPU for hours after a single page visit").
  `.data/edge_report_cache.db` did not exist before OR after this call (confirmed by `ls`),
  mechanically proving nothing was computed or published.
  - **Backend CPU immediately after: 0.5%** (idle) — no lingering sweep. A second immediate GET
    also answered in ~28.7s (same bounded, un-accelerated `list()` cost every time — expected,
    not a regression).
- Stopped (port-based kill, both ports confirmed free), restarted `scripts/dev.sh` on the SAME
  ports: both services healthy within 2 seconds, no `error`/`EADDRINUSE` in either log.
- Stopped again; final check confirms no `uvicorn`/`next dev` process remains for this project and
  both ports are free.

## Known Issues

- **`.claude/project-template.md` is still the generic unfilled vendored template** (same
  pre-existing finding every prior iteration's dev handoff has recorded). Test/build commands used
  above came from `README.md`, `pyproject.toml`, and direct repo inspection, consistent with prior
  iterations' practice.
- **J-02 (store acceleration) is explicitly out of scope this iteration.** A cold GET against the
  real 882MB corpus still costs ~29s (the unaccelerated `dataset_store.list()` price) — this is
  the documented, expected interim state per the phase spec's NOTES, not a defect. `/structure`'s
  Case Studies section can still take minutes to load on the real corpus because of the separate,
  unrelated `GET /research/setups` cold-scan cost (J-06's future scope) — not a regression
  introduced or expected to be fixed here.
- **No "Compute edge report" button, POST trigger, or CLI warmer exist yet** — `EdgeReportCache.
  compute_and_publish` and `run_strategy_comparison_report` are fully implemented and tested but
  have no caller in the running application this iteration (J-04's scope). The only way to warm
  the cache today is a direct Python call (as this handoff's live verification and several tests
  do) — this is intentional, not a gap.
- The `EdgeReportNotComputed.compute` field is typed `null` and always emitted as `null` this
  iteration (no compute-job manager exists until J-04) — matches the phase spec's explicit
  assumption ledger entry.
- Two ternary-based frontend design decisions worth flagging for review: `EdgeReportResponse`
  gained a `status?: undefined` field purely for TypeScript discriminated-union narrowing (never
  sent or read at runtime — the backend's real report JSON has no `status` key at all, matching
  today's exact wire shape); `NotComputedPanel` reuses `UnavailablePanel`'s exact amber
  degraded-state Tailwind classes (a deliberate "no new visual language" choice per the phase
  spec's Visual Requirements) rather than `EmptyState`'s slate treatment, since a not-computed
  report is closer in spirit to "needs an operator's attention" than "a genuinely empty result."
