# goal-fast_wall-iter-4 Execution Plan

Target journey: **J-04 — "The operator-run compute — button, background job, CLI warmer"**
(session `fast_wall`, the "Fast Wall" performance interlude). Required-still-passing: J-01, J-02,
J-03, J-07 (all currently `passing` per `journey-history.json`). Depth: full.

## Alignment check

Directly continues the goal.md dependency order (J-01 → J-02 → J-03 → **J-04** → J-05), matches the
phase spec's own IN SCOPE/OUT OF SCOPE line-for-line, and introduces no scope beyond it. It is
enabling work for goal.md Success Criteria #4 (the first full real edge report as one resumable
operator act) and adds **zero** research-value change, **zero** new `Config` field, and **zero** new
MCP tool — consistent with the interlude's critical anti-goals. No drift detected between the phase
spec and `docs/goal.md`/the session blueprint.

Codebase probe (verified directly, matches the phase spec's own probe exactly): `edge_report_compute.py`
does not exist yet. `EdgeReportCache.lookup`/`compute_and_publish` (J-01) already exist beside the
untouched `get_or_compute` (`edge_report_cache.py:262-350`). `run_strategy_comparison_report`
(`edge_report.py:450-484`) has only `cache=None` today. `peek_strategy_comparison_report`
(`edge_report.py:487-525`) unconditionally emits `"compute": None` at line 524. `routes.py` has no
`/research/edge-report/compute*` routes; `ResearchRegistry.__init__` (`routes.py:237-250`) wires only
`_study_jobs`/`_backtest_jobs` — the exact `BacktestJobManager` (`backtests.py:1121-1256`) precedent
this iteration's single-flight manager adapts. `structure/page.tsx`'s `NotComputedPanel` (line 287,
`{ detail }`-only today) and the `needsPolling`/`setInterval(...,700)` poll pattern (lines 195-201,
1301-1327) are the exact precedents to mirror. `app/mcp/__init__.py` has exactly 18 registered tool
names, pinned by `test_advertised_tool_set_is_exactly_capability_6` — must stay byte-unmodified.

## What to Build

- New `EdgeReportComputeManager` in a new `edge_report_compute.py` module: **single-flight** (exactly
  one job slot — simpler than `StudyJobManager`/`BacktestJobManager`'s per-id dict), cooperative
  cancel via `threading.Event` observed between dataset×strategy pairs, and an atomically-published
  progress snapshot (`{id, state, force, started_utc, finished_utc, error, progress: {phase,
  backtests_total, backtests_done, backtests_from_cache, current}}`, read-local-reference-before-inspect
  — the `EdgeReportCache._hot` precedent). A trigger while `state=="running"` returns the existing
  snapshot with `started:false`. A cancelled/failed run publishes NOTHING to the edge-report cache
  (publish only after the compute function returns normally).
- Five new additive keyword-only hooks on `run_strategy_comparison_report`: `force=False, progress=None,
  should_abort=None, sub_cache=None, workers=None` — every default reproduces today's exact behavior.
  `force=True` dispatches through the already-shipped `cache.compute_and_publish` instead of
  `get_or_compute`. `progress=`/`should_abort=` thread down into `_split_cells`'s existing per-dataset×
  strategy loop (`edge_report.py:338-397`) as an optional reporting/cooperative-cancel seam — the
  loop's own ordering/pooling/aggregation code stays untouched. `sub_cache=`/`workers=` are accepted
  but **currently INERT** this iteration (logged assumption; J-05 gives them real effect) — every
  compute this iteration triggers runs strictly sequentially regardless of `workers` value.
- Rewire `peek_strategy_comparison_report`'s hardcoded `"compute": None` (line 524) to read the
  registry's compute-manager current/last snapshot — same key, same shape, no change for a reader that
  has only ever seen `null`.
- Three new REST routes as subpaths of the existing `/research/edge-report` section: `POST
  /research/edge-report/compute` (body `{force: bool=false}`), `GET /research/edge-report/compute`
  (snapshot or `null`), `POST /research/edge-report/compute/cancel` (409 when idle — mirrors
  `cancel_backtest`/`cancel_study`'s 404/409 shape at `routes.py:2023-2051` / `1383-1399`) — resolved
  through the SAME existing `get_registry`/`get_dataset_store`/`get_bar_store`/`get_edge_report_cache`
  deps, no second store/cache construction path. The EXISTING `get_edge_report` route body
  (`routes.py:2109-2133`) and its pinned `Depends`/`cache=cache` wiring stay byte-unmodified — the new
  routes are subpaths, so non-GET verbs on `/research/edge-report` itself are structurally unaffected
  (405 stands).
- CLI warmer (`edge_report_compute.py`'s own `main()`): `python -m app.research.edge_report_compute
  --workers N [--force] [--out report.json]` (default 4, inert this iteration), resolving the same
  env/config seams the backend reads (journal, dataset dir, bar dir, both cache DBs) — mirrors
  `edge_report.py`'s own `main()` CLI precedent (`edge_report.py:573`). Prints one progress line per
  completed backtest, exits 0 with a summary, nohup-able/restart-proof. The existing era-3 J-09
  `edge_report.main()` CLI stays byte-untouched.
- **Zero** change anywhere to `app/mcp/__init__.py` (`TOOL_NAMES`/`EXPECTED_TOOLS` stay at 18) — the
  compute surface is REST-only.
- Frontend: `NotComputedPanel` gains a "Compute edge report" button; POST the trigger, then a new poll
  effect (mirrors the existing `needsPolling`/`setInterval(...,700)` pattern, reusing the PATTERN not
  the endpoint) renders `backtests_done/backtests_total` (+ `backtests_from_cache`) verbatim while
  `state==="running"`. On `state==="done"`, re-fetch `GET /research/edge-report` and fall into the
  EXISTING `EdgeReportBody` render (zero new report-rendering code). On `"failed"`, render the
  snapshot's `error` verbatim. The payload's already-typed `compute` field seeds the panel's initial
  state on mount, so a page load mid-job or post-terminal resumes the correct view.
- OPTIONAL, non-blocking bonus only (never required for Definition of Done, never simulated if
  attempted): run the CLI warmer to completion against the FULL real corpus and append the completed
  three-way comparison to `reports/pnl/pnl-history.md` — *(operator-verified on the real corpus)*.

**Explicitly out of scope this iteration** (per the phase spec, mirrored here so no agent drifts):
J-05 (`EdgeReportBacktestCache`, `_split_cells`'s `run_pair` seam, `ProcessPoolExecutor`), J-06
(`setups_scan_cache.py`), any real parallel EXECUTION behind `workers=`/`sub_cache=`/`--workers`, any
change to `EdgeReportCache`'s three existing method BODIES, any change to `levels.py`/`tradability.py`/
`backtests.py`'s `_StructureArmMemo`, any change to `bars.py`/`datasets.py`/`dataset_index.py`, any new
`Config` field or runtime dependency.

## Agents Required
- developer: yes -- implements the backend compute manager/hooks/routes/CLI and the frontend button/poll/types in one pass, TDD per the phase spec's Test-first TC-1..TC-16 contract
- backend-data: yes -- new `edge_report_compute.py` (manager + CLI), `edge_report.py` hook additions, three new `routes.py` subpaths, new/updated tests in `test_edge_report_compute.py` / `test_edge_report_api.py` / `test_edge_report.py`
- frontend-ux: yes -- `structure/page.tsx` button + poll + done/failed rendering, `lib/api.ts` three new functions, `lib/types.ts` new snapshot type

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

Backend:
- `apps/backend/app/research/edge_report_compute.py` (NEW) -- `EdgeReportComputeManager` (single-flight/cancel/progress) + CLI `main()`
- `apps/backend/app/research/edge_report.py` -- add 5 keyword-only hooks to `run_strategy_comparison_report`; thread `progress=`/`should_abort=` into `_split_cells`'s loop; rewire `peek_strategy_comparison_report`'s `compute` field to the manager snapshot
- `apps/backend/app/research/routes.py` -- add `registry.edge_report_compute` property (mirrors `_study_jobs`/`_backtest_jobs`, lines 246-250) + 3 new routes beside `get_edge_report` (line 2109); existing route body byte-unchanged
- `apps/backend/tests/test_edge_report_compute.py` (NEW) -- manager single-flight/cancel/force/progress/failed-state unit tests + CLI tests
- `apps/backend/tests/test_edge_report_api.py` -- 3 new routes' request/response/error-code tests; existing pinned guard tests (`test_non_get_verbs_are_405_no_write_surface_exists`, the two `Depends`/`cache=cache` wiring tests) re-run byte-unmodified
- `apps/backend/tests/test_edge_report.py` -- the 5 new hooks' default-path byte-identity + non-vacuous `should_abort` equivalence tests
- `apps/backend/tests/test_mcp_server.py` -- re-run unmodified (TC-10 regression check only, no edits expected)
- `docs/handoffs/goal-fast_wall-iter-4-dev.md` (NEW) -- dev handoff

Frontend:
- `apps/frontend/app/structure/page.tsx` -- `NotComputedPanel` (line 287, `{ detail }`-only today) gains the button + poll effect + done/failed branches
- `apps/frontend/lib/api.ts` -- add `triggerEdgeReportCompute(force?)`, `fetchEdgeReportCompute()`, `cancelEdgeReportCompute()`, mirroring `createBacktest`/`fetchBacktest`/`cancelStudy`'s exact `{ok, data/…, error}` shape + 422/unreachable folding (see `createBacktest` at `lib/api.ts:1006-1030`)
- `apps/frontend/lib/types.ts` -- add `EdgeReportComputeSnapshot` (id/state/force/started_utc/finished_utc/error/progress); widen `EdgeReportNotComputed.compute` from its current `null`-only literal (line 1374) to `EdgeReportComputeSnapshot | null`

**Zero diff expected** (scope discipline — any diff here signals leakage into J-05/J-06 territory):
`levels.py`, `tradability.py`, `backtests.py`, `bars.py`, `datasets.py`, `dataset_index.py`,
`edge_report_cache.py` (method bodies), `app/mcp/__init__.py`, `config.py`.

## UI Evolution
- New user-facing capability: the operator starts the first-ever completed real edge-report compute
  directly from `/structure` — no out-of-band script, no page-load side effect.
- New information displayed: live progress counts (`backtests_done`/`backtests_total`/
  `backtests_from_cache`), job `state`, and on failure the `error` string, all inside the existing
  `NotComputedPanel`. On `done`, the pre-existing `EdgeReportBody` render takes over (not new
  information — the same report shape J-01 already types, now actually reachable).
- New user actions: a "Compute edge report" button inside the not-computed panel (POST trigger);
  continuous polling while a job is in flight needs no further user action.
- UI surface changes: `/structure`'s EXISTING Edge Report section's `NotComputedPanel` only — no new
  page, no new panel, no nav entry.
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse `NotComputedPanel`'s existing amber degraded-state container
  (`border-amber-800/60 bg-amber-900/20`, `text-amber-300` headline / `text-amber-200/70` body) for
  the panel shell. The button mirrors the existing primary-action button already in this file (e.g.
  `structure-load-button`: `rounded-md border border-slate-600 bg-slate-800 px-3 py-1.5 text-sm
  font-medium text-slate-200 transition-colors hover:border-slate-500 hover:bg-slate-700
  focus:outline-none focus:ring-1 focus:ring-emerald-500 active:bg-slate-900 disabled:cursor-not-allowed
  disabled:opacity-40`) for its enabled/disabled/in-flight states — no new color or button style.
- Layout: button + progress line sit inside the existing `NotComputedPanel` div, stacked below the
  current headline/detail text — no layout restructuring, no new section.
- Key visual effects: none new — Design Direction explicitly states "no new visual language"; reuse
  the existing panel/empty-state/poll patterns verbatim.
- States to handle: idle (button visible, enabled), running (progress line updating, button
  disabled/hidden, poll active), done (panel replaced entirely by `EdgeReportBody`), failed (panel
  shows the server's `error` string verbatim, button re-enabled to retry). Seed initial state from the
  payload's `compute` field on mount so a page load mid-job or post-terminal resumes the correct view
  without a spurious extra click.

## Key Test Scenarios

Authoritative source is the phase spec's Test-first contract (TC-1 through TC-16); highlights:

- Single-flight: a second POST while running returns the SAME job (`started:false`, same `id`) — never
  a second job (TC-2).
- Cancel: resolves `cancelled`, edge-report cache holds no partial report (TC-3); cancel while idle is
  409 (TC-4).
- Force semantics: `force:true` over a warm key recomputes + republishes, moving the freshness marker
  (TC-5); a non-force trigger over the same warm key does NOT recompute (TC-6).
- After `done`, `GET /research/edge-report` serves the report byte-identical
  (`json.dumps(sort_keys=True)`) to an uncached compute of the same inputs (TC-7).
- The not-computed payload's `compute` field mirrors `GET /research/edge-report/compute`'s own
  snapshot byte-for-byte, in every state (TC-8).
- Non-GET verbs on `/research/edge-report` itself stay 405 (TC-9); MCP tool list unchanged at exactly
  18 tools, source byte-unmodified (TC-10).
- CLI warmer completes on fixtures + prints per-backtest progress (TC-11); a repeat invocation without
  `--force` exits in <5s on the warm key with zero backtests re-run (TC-12).
- A test-injected mid-sweep failure resolves `state:"failed"`, surfaces `error` verbatim, publishes no
  partial report (TC-13).
- The 5 new hooks are proven genuinely wired, not decorative: default path is byte-identical with
  unused hooks actively supplied (TC-14a); a `should_abort` that DOES fire changes the observable
  outcome — cancelled/nothing published (TC-14b) — the non-vacuous equivalence proof iter-3's lesson
  demands, not just "the test passes."
- Browser, on a SCOPED backend/frontend pair only (fresh temp journal/dataset/bar dirs, backend port
  8391 / frontend port 3391, `TAPEOLOGY_DATASET_DIR` pointed at `tests/fixtures/datasets_j03` or
  `tests/fixtures/datasets` — **never** the default `.data/datasets` 882MB/18-dataset real corpus, per
  iter-0's CPU-pin hazard and iter-1's already-established recipe in
  `docs/handoffs/goal-fast_wall-iter-1-dev.md`): click "Compute edge report" → progress updates at
  least once while running → within 90s the panel is replaced by `EdgeReportBody` or the honest
  all-empty-cells state, zero full-page reload (TC-15); a pre-arranged `failed` snapshot (backend
  primed directly before navigation) renders its exact `error` string on page load (TC-16).
- Required-still-passing regression, verified in the SAME scoped browser pass as TC-15/16: J-01 (frozen
  not-computed headline/detail/register render when no compute has run — must stay byte-unchanged),
  J-02 (verified-content caches untouched), J-03 (arm memo untouched, byte-identical backtests), J-07
  (full backend suite green, `config_fingerprint` still `4d665603569b9dbf`, all era-1–5B surfaces
  behave exactly as shipped, Tradable Map / Case Studies / Registry / Comparison sections unaffected).
- Anti-goal guards: a compute-spy on the existing `GET /research/edge-report` proves **zero** sweep
  calls from any GET, in every iteration's test suite (the interlude's headline critical anti-goal);
  no MCP write surface added; no divergent accelerator output (byte-identity proven by TC-7/TC-14, not
  merely "the equivalence test exists").
