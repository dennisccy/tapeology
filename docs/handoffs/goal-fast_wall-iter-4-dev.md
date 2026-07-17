# goal-fast_wall-iter-4 Dev Handoff

**Phase:** goal-fast_wall-iter-4
**Date:** 2026-07-17
**Agent:** developer
**Status:** complete

## What Was Built

Target journey **J-04** ("The operator-run compute — button, background job, CLI warmer"). The
operator can now trigger the first-ever completed edge-report compute directly from `/structure` —
a single-flight, cancellable, progress-reporting background job — instead of the cold cache's
static "not computed" message with no path forward. `Frontend Present: yes`.

- **New `apps/backend/app/research/edge_report_compute.py`**: `EdgeReportComputeManager` —
  single-flight (exactly ONE job slot, simpler than `StudyJobManager`/`BacktestJobManager`'s
  per-id dict since there is only ever one "the edge report compute"), cooperative cancel via a
  per-job `threading.Event`, and an atomically-published progress snapshot
  (`{id, state, force, started_utc, finished_utc, error, progress: {phase, backtests_total,
  backtests_done, backtests_from_cache, current}}`). `trigger(...)` starts a background worker
  thread and returns immediately; a trigger while `state == "running"` returns the SAME job
  unchanged (`started: false`). `snapshot()` returns a caller-safe copy (two levels deep) so a
  reader can never poison the manager's internal state. A cancelled run resolves `state:
  "cancelled"`; any other exception resolves `state: "failed"` with the message surfaced verbatim.
  Also holds the CLI warmer's `main()` — `python -m app.research.edge_report_compute
  --workers N [--force] [--out report.json]` — which drives the SAME hooks synchronously,
  in-process (no manager, no thread; mirrors `edge_report.py`'s own `main()` CLI precedent, never
  going through the manager since a one-shot CLI process has no concurrent caller to serialize
  against).
- **`edge_report.py`**: five additive keyword-only params on `run_strategy_comparison_report`
  (`force=False, progress=None, should_abort=None, sub_cache=None, workers=None`) — every default
  reproduces the pre-J-04 exact behavior. `force=True` dispatches through the already-shipped
  `cache.compute_and_publish` (J-01) instead of `cache.get_or_compute`. `progress=`/`should_abort=`
  thread into `_split_cells`'s existing per-dataset×strategy loop via a new small
  `_ProgressReporter` helper (shared across both the train and hold-out `_split_cells` calls, so
  `backtests_done` counts monotonically across splits) and a `_count_eligible_pairs` helper (sizes
  `backtests_total` once, right after `events` resolves). `should_abort` is checked once per pair,
  strictly BEFORE that pair's backtest starts, and raises the new `EdgeReportComputeCancelled`
  exception — which propagates UNCHANGED through `EdgeReportCache.get_or_compute`/
  `compute_and_publish` (both publish ONLY after `compute_fn` returns normally, so "a cancelled run
  publishes nothing" holds by construction, with zero change to either cache method's body).
  `sub_cache=`/`workers=` are accepted this iteration but currently INERT (a logged assumption —
  every compute this iteration runs strictly sequentially; J-05 gives them real effect).
  `peek_strategy_comparison_report` gained a `compute=None` keyword param, embedded verbatim as the
  not-computed payload's `compute` field (replacing J-01's hardcoded `None` — same key, same shape,
  no change for a caller that never passes it).
- **`routes.py`**: `ResearchRegistry` gained an `edge_report_compute` property (the
  `study_jobs`/`backtest_jobs` precedent — `EdgeReportComputeManager()` needs no constructor args,
  unlike those two, since every `trigger()` call takes its store/dataset_store/bar_store/config/
  cache explicitly). Three new routes as subpaths of `/research/edge-report`: `POST
  /research/edge-report/compute` (body `{force: bool=false}`, returns `{started, compute}`), `GET
  /research/edge-report/compute` (the snapshot or `null`), `POST
  /research/edge-report/compute/cancel` (409 when idle, mirrors `cancel_backtest`'s check-then-call
  split). `get_edge_report`'s existing body gained ONE additional kwarg
  (`compute=registry.edge_report_compute.snapshot()`) on its existing `peek_strategy_comparison_report`
  call — the pinned `Depends(get_bar_store)`/`Depends(get_dataset_store)`/
  `Depends(get_edge_report_cache)`/`cache=cache` substrings the two existing guard tests check for
  are all still textually present (verified — see Known Issues for this judgment call). No change
  anywhere to `app/mcp/__init__.py` — the compute surface is REST-only, per the critical "No MCP
  write surface" anti-goal.
- **Frontend** (`structure/page.tsx`): `NotComputedPanel` gained a "Compute edge report" button, a
  progress line (`backtests_done / backtests_total` + a from-cache annotation), and a failed-state
  error render — all reusing the existing amber degraded-state container and the
  `structure-load-button`'s exact enabled/disabled Tailwind classes (no new visual language). A new
  poll `useEffect` mirrors the existing `needsPolling`/`setInterval(..., 700)` backtest-poll
  pattern: while `computeSnapshot.state === "running"`, it polls `GET
  /research/edge-report/compute` every 700ms; the instant a tick observes `state === "done"`, it
  re-fetches `GET /research/edge-report` exactly once so the panel falls through to the
  PRE-EXISTING `EdgeReportBody` render (zero new report-rendering code). The not-computed payload's
  own `compute` field seeds `computeSnapshot` on mount, so a page load mid-job or post-terminal
  resumes the correct view without a spurious extra click.
- **`lib/api.ts`**: `triggerEdgeReportCompute(force?)`, `fetchEdgeReportCompute()`,
  `cancelEdgeReportCompute()` — mirror `createBacktest`/`fetchBacktest`/`cancelStudy`'s exact
  `{ok, data/…, error}` shape and 422/unreachable folding byte-for-byte. `cancelEdgeReportCompute`
  is implemented and tested but NOT wired to any UI control this iteration — the plan's UI Evolution
  section names only the "Compute edge report" button, no cancel affordance.
- **`lib/types.ts`**: `EdgeReportComputeProgress`, `EdgeReportComputeSnapshot`; widened
  `EdgeReportNotComputed.compute` from its former `null`-only literal type to
  `EdgeReportComputeSnapshot | null`.

## Files Changed

- `apps/backend/app/research/edge_report_compute.py` (NEW) — `EdgeReportComputeManager` + CLI
  `main()` + `_cli_progress_printer()`.
- `apps/backend/app/research/edge_report.py` — `EdgeReportComputeCancelled`; `_count_eligible_pairs`
  + `_ProgressReporter`; `_split_cells` gained `reporter=None, should_abort=None` (pooling/
  aggregation code untouched); `_compute_strategy_comparison_report` gained `progress=None,
  should_abort=None`; `run_strategy_comparison_report` gained the 5 new hooks; `peek_strategy_
  comparison_report` gained `compute=None`.
- `apps/backend/app/research/routes.py` — `EdgeReportComputeRequest` model; `ResearchRegistry.
  edge_report_compute` property; `get_edge_report` passes `compute=registry.edge_report_compute.
  snapshot()`; three new routes (`trigger_edge_report_compute`, `get_edge_report_compute`,
  `cancel_edge_report_compute`).
- `apps/backend/tests/test_edge_report_compute.py` (NEW) — 20 tests: manager single-flight/cancel/
  force/progress/failed-state/snapshot-copy-safety (fake-compute, threading-event-driven,
  deterministic), CLI fixture-run/repeat-invocation/force/out-flag/workers-flag tests, and the CLI
  progress-printer's own formatting unit tests.
- `apps/backend/tests/test_edge_report.py` — +10 tests: TC-14a (hooked-but-unused path byte-
  identical to default), TC-14b (a `should_abort` that DOES fire is observably different — raises,
  publishes nothing, and exactly the first pair's backtest persisted before the second pair was
  ever started), force→`compute_and_publish`/`get_or_compute` dispatch spies, TC-5/TC-6 at the
  module level, an integrity-error-with-hooks-supplied regression test, and the `peek_*` `compute=`
  passthrough tests.
- `apps/backend/tests/test_edge_report_api.py` — `ctx` fixture gained `registry.edge_report_compute.
  join_all(timeout=10.0)` in teardown (test hygiene, the `backtest_jobs.join_all` precedent — no
  thread leaks across tests); +12 tests: TC-1/2/3/4/5/6/8 at the route level, a failed-compute
  route test, and two coherence guards (routes wired through `registry.edge_report_compute`; the
  two pre-existing pinned `Depends`/`cache=cache` guard-test assertions re-verified inline).
- `apps/frontend/app/structure/page.tsx` — `NotComputedPanel` gained the button/progress/failed-
  error render; `computeSnapshot`/`computeTriggering`/`computeTriggerError` state; the mount effect
  seeds `computeSnapshot`; a new poll `useEffect`; `handleTriggerEdgeReportCompute`.
- `apps/frontend/lib/api.ts` — `triggerEdgeReportCompute`, `fetchEdgeReportCompute`,
  `cancelEdgeReportCompute`.
- `apps/frontend/lib/types.ts` — `EdgeReportComputeProgress`, `EdgeReportComputeSnapshot`; widened
  `EdgeReportNotComputed.compute`.
- `docs/handoffs/goal-fast_wall-iter-4-dev.md` — this handoff.
- `docs/handoffs/goal-fast_wall-iter-4-frontend.md` — frontend-focused handoff.

**Zero diff** (verified via `git status`/`git diff --stat`): `levels.py`, `tradability.py`,
`backtests.py`, `bars.py`, `datasets.py`, `dataset_index.py`, `edge_report_cache.py` (method
bodies untouched — only new callers wire through the already-shipped `lookup`/`compute_and_publish`),
`app/mcp/__init__.py`, `config.py` — exactly the plan's expected scope, nothing wider.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (inferred from
`pyproject.toml`'s `[tool.pytest.ini_options]` and every prior iteration's own handoff —
`.claude/project-template.md` is still the framework's generic, unfilled template; see Known
Issues, carried forward, not new).

Targeted runs (all green before the full run):
- `pytest tests/test_edge_report.py -q` → 50 passed.
- `pytest tests/test_edge_report_api.py -q` → 23 passed.
- `pytest tests/test_edge_report_compute.py -q` → 20 passed.

Full suite (background run, exit code 0, confirmed via the raw dot/`s` output — zero `F` anywhere):
**1482 passed, 7 skipped, 0 failed** (1489 collected) — up from the iter-3 baseline of 1440
passed/7 skipped/1447 collected by exactly the **42 net-new tests** this iteration adds (10 in
`test_edge_report.py`, 12 in `test_edge_report_api.py`, 20 in the new `test_edge_report_compute.py`
— confirmed via `git diff | grep -c '^+def test_'` per file, summing to 42, matching the collected-
count delta exactly). Skip count is byte-identical to the baseline (0 newly skipped or deleted).

`config.config_fingerprint()` confirmed still `4d665603569b9dbf` by direct computation (no `Config`
field added — every new module uses only stdlib `threading`/`argparse`/`uuid`/`datetime`).

`app.mcp.TOOL_NAMES` confirmed still exactly 18 tools (unchanged set); a live `openapi.json` check
against a real running backend confirmed the exact registered path set: `/research/edge-report`
(GET only), `/research/edge-report/compute` (GET + POST), `/research/edge-report/compute/cancel`
(POST only) — non-GET verbs on `/research/edge-report` itself remain unaffected (405 stands, no
handler exists for them).

Frontend: `cd apps/frontend && NEXT_DIST_DIR=<isolated dir> npm run build` — compiled successfully,
zero TypeScript errors (strict mode), all 7 routes built including `/structure`. The isolated-build
tsconfig.json/next-env.d.ts side effects were reverted via `git checkout` afterward (the iter-1
precedent — confirmed clean via `git status`).

## Live verification (beyond the automated suite)

Ran a SCOPED backend (fresh temp journal/bar dirs + a private COPY of the committed
`tests/fixtures/datasets_j03` fixture — never the default `.data/datasets` 882MB/18-dataset real
corpus, per iter-0's CPU-pin hazard) on port 8391, and a scoped frontend on port 3391 pointed at it
(`NEXT_PUBLIC_API_URL=http://localhost:8391`), both started via the real `uvicorn`/`next dev`
commands (not `TestClient`):

- Cold `GET /research/edge-report`: `status: "not_computed"`, `dataset_count: 1`, `compute: null`.
- `POST /research/edge-report/compute` (empty body): `started: true`, a fresh running snapshot.
- Polled `GET /research/edge-report/compute`: resolved to `state: "done"` in ~15ms (the committed
  fixture's symbol, PG, is not a config-owned panel symbol under the real 12-symbol panel, so this
  is the honest zero-eligible-pairs empty compute — the SAME finding `test_keyless_committed_j03_
  fixture_with_the_real_panel_is_an_honest_empty_report` already proves for the direct-call path),
  `error: null`, `finished_utc` populated.
- `GET /research/edge-report` afterward: the real report shape, no `status` key, `train.cells: []`
  — the cache is now genuinely warm.
- A second `POST /research/edge-report/compute`: started a genuinely NEW job (a fresh `id`,
  distinct from the first) — confirmed the "terminal job → next trigger starts fresh" semantics.
- `POST /research/edge-report/compute/cancel` while idle: `409`.
- Tampered the SCOPED temp copy's dataset checksum (never the committed fixture) and re-triggered:
  the job resolved `state: "failed"` with `error` carrying the EXACT `EdgeReportError` message
  verbatim ("1 dataset file(s) failed integrity verification (['...']) — the report stops with
  nothing written") — no swallowing, no generic message. `GET /research/edge-report` afterward
  still explicitly failed on the same corrupt file (the pre-existing, unmodified integrity
  discipline — no new bypass path).
- Server-rendered HTML (`curl http://localhost:3391/structure`, pre-hydration) confirmed the page's
  structure renders without error, including the `edge-report-loading` testid in its initial state.
- Torn down cleanly: both ports confirmed free, no stray `uvicorn`/`next dev` process for this
  project remains (a `pgrep -af uvicorn`/`next dev` check found only an unrelated process from a
  different, unrelated repository on the same machine).

**Chrome-MCP browser click-through could not be completed** — see Known Issues below for the full
diagnostic trail. This is a session/environment limitation, not a defect surfaced by testing; the
curl-based live verification above exercises the identical HTTP surface a browser click would.

## Known Issues

- **Chrome MCP failed to start in this session despite extensive diagnosis** (8+ attempts: default
  profile, `hide_browser`, `kill_chrome`, `restart_chrome`, clearing stale `SingletonLock`/
  `SingletonSocket`/`SingletonCookie` files, two never-before-used fresh profile names) — every
  attempt failed identically with "Chrome did not become ready on port 9222 within 15000ms". A
  MANUALLY-launched Chrome (both a fresh-profile headless instance on a different port, and the
  MCP's own exact command line copied verbatim) confirmed Chrome itself works fine on this machine
  (a fresh profile's DevTools port answered within ~4s); the failure is specific to how the MCP
  bridge launches/detects readiness in this session. I could not get a real visual click-through of
  the "Compute edge report" button, so TC-15 (progress updates while running, panel replaced within
  90s) and TC-16 (a pre-arranged failed snapshot renders its exact error on page load) are
  **unverified by browser** this iteration — they ARE verified by the curl-based live check above
  (which exercises the identical backend responses the button/poll code consumes) plus the
  SSR-HTML structural check, but no screenshot exists. Per this project's own "no screenshot ⇒
  unknown, never passing" discipline, this should be flagged explicitly for the browser-qa-agent
  stage, which may need a different browser session or an explicit Chrome restart to recover.
- **Judgment call**: `get_edge_report`'s route body gained one additional kwarg
  (`compute=registry.edge_report_compute.snapshot()`) on its existing `peek_strategy_comparison_
  report(...)` call. The phase spec's own wording says the route body "stays byte-unmodified", but
  also separately requires "Rewire `peek_strategy_comparison_report`'s `compute` field to read the
  registry's compute-manager snapshot" (TC-8) — these two statements are only jointly satisfiable if
  "byte-unmodified" means the PINNED substrings (`Depends(get_bar_store)`, `Depends(get_dataset_
  store)`, `Depends(get_edge_report_cache)`, `cache=cache`) stay textually present, not that literally
  zero characters change. I read it that way; both pre-existing guard tests (which check for those
  exact substrings, not byte-for-byte function-body equality) pass unmodified, and TC-8's own
  requirement is otherwise unsatisfiable by any caller. Flagging for reviewer/auditor confirmation.
- **`sub_cache=`/`workers=` are accepted but INERT this iteration** (a logged assumption, matching
  goal.md's own iteration split) — every compute this iteration triggers, whether via the button or
  the CLI's `--workers` flag, runs strictly sequentially. J-05 gives them real effect
  (`EdgeReportBacktestCache`, the `run_pair` provider seam, `ProcessPoolExecutor`).
- **The CLI warmer's `--out` flag was not in the phase spec's Test-first TC list but IS in goal.md's
  own step 3 usage string** (`[--out report.json]`) — implemented as optional (unlike the existing
  era-3 `edge_report.py` CLI, which requires `--out`), since this warmer's primary job is publishing
  to the durable cache, not producing a file.
- **`.claude/project-template.md` is still the generic, unfilled vendored template** (the same
  finding every prior iteration's dev handoff has recorded) — test/build commands used above came
  from `pyproject.toml`, `package.json`, and prior iterations' own handoffs.
- This iteration's live corpus is entirely the committed `datasets_j03` fixture (PG, not a
  config-owned panel symbol) — so the button's progress line was observed going straight from
  `backtests_total: 0` to `done` (an honest zero-backtest run) rather than incrementing through a
  multi-pair sweep. The multi-pair progress-increment behavior (TC-14b's exact mechanism) IS proven
  at the unit level with the `scan_config`/`scan_bar_store` synthetic fixtures (a real classified
  event, 3 real backtests), just not observed live through the button this iteration.

## Suggested Next Phase

J-05 ("The sweep becomes resumable and parallel — durable pair results + process pool") per
goal.md's own dependency order (J-01 → J-02 → J-03 → J-04 → J-05). It gives `sub_cache=`/`workers=`
real effect (`EdgeReportBacktestCache`, the `_split_cells` `run_pair(dataset_meta, strategy_id)`
provider seam, `ProcessPoolExecutor`) — deliberately NOT bundled with this iteration (goal.md's own
rule 5, never bundle two risky journeys touching the SAME function). Before that: the operator
should confirm the Chrome-MCP environment issue documented above is resolved (or find a workaround)
so TC-15/TC-16's actual browser click-through can be captured with a screenshot.
