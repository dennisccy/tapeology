# goal-fast_wall-iter-5 Dev Handoff

**Phase:** goal-fast_wall-iter-5
**Date:** 2026-07-17
**Agent:** developer
**Status:** complete

## What Was Built

Two deliverables, exactly per the plan.

**1. Verification only (zero product code change) — closes J-04's browser gap.** Chrome MCP
worked cleanly this session (unlike the last two iterations' documented 8+-attempt environmental
failure) — a genuine browser pass was captured against a FRESH scoped backend/frontend pair
(ports 8391/3391, fresh temp journal/dataset/bar dirs, `TAPEOLOGY_DATASET_DIR` at the committed
`apps/backend/tests/fixtures/datasets_j03` fixture, cold `TAPEOLOGY_EDGE_REPORT_CACHE_DB` AND the
new `TAPEOLOGY_EDGE_SWEEP_CACHE_DB` — never `.data/datasets`):
- TC-1: clicked "Compute edge report" on a cold cache — captured the mid-run "Computing…" state
  with the live "0 / 0 backtests" progress line, then the terminal render (the frozen warm-cache
  "No edge-report cells yet." empty state, since the PG fixture is not a config-owned panel
  symbol) — all within the same page load, zero full-page reload.
- TC-2: captured the not-computed panel's exact pre-click render (headline + detail, byte-
  identical to J-01), then reloaded post-compute to confirm the warm report serves directly (no
  button, no not-computed panel) and every other `/structure` section (Tradable Map, Case
  Studies, Fetch from Yahoo Finance, Registry, Comparison) renders exactly as shipped — captured
  via both a full-page screenshot (a tall 1280×2400 viewport avoided the scroll-then-screenshot
  blank-capture quirk noted in project memory) and a DOM-text extraction as a second, independent
  confirmation.
- TC-3: arranged a `state: "failed"` snapshot via a direct backend call (corrupt the scoped
  dataset copy → trigger a compute, which fails on integrity → then RESTORE the dataset content
  in place, without restarting the backend, so the store's stat-keyed cache re-verifies it healthy
  on the very next read while the compute manager's own in-memory snapshot still shows the
  historical failure) — confirmed `/structure` renders the not-computed panel with the exact
  backend `EdgeReportError` message verbatim in the red error line, and the button relabels to
  "Retry compute", enabled. Screenshots for all three are saved under this session's scratchpad
  (paths in Known Issues); the exact recipe and evidence are described there for the QA/audit
  lanes.
- Also ran a curl-based full compute lifecycle (POST trigger → poll → warm GET) against the same
  scoped backend as an independent, non-browser confirmation that the new `sub_cache` wiring
  (below) doesn't break the button-triggered path end to end.

**2. Backend — J-05 "the sweep becomes resumable and parallel".**
- **New `apps/backend/app/research/edge_report_backtest_cache.py`**: `EdgeReportBacktestCache` —
  a durable SQLite cache of one row per (dataset × strategy) backtest pair, beside (never
  replacing) `EdgeReportCache`. `pair_cache_key(...)` is a pure function of the eight named
  components (`dataset_id`, `dataset_checksum`, `strategy_id`, `profile`, `config_fingerprint`,
  `config_content_hash`, `strategy_registry`, `bar_store_signature`) — sha256 of their canonical
  JSON, reusing `edge_report_cache.py`'s `_canonical`/`_config_content_hash` verbatim. `lookup`/
  `publish` open fresh short-lived connections (WAL + busy_timeout, the `JournalStore._read_conn`
  precedent — safe across many worker PROCESSES, not just threads). No in-process hot slot (a
  sweep touches many distinct keys, never the same key twice in one run, so a single-slot fast
  path would never earn its keep). Both `lookup` and `publish` independently swallow
  `sqlite3.Error` (a corrupted/unreadable DB is a full miss, never a crash; a publish failure
  never blocks the sweep — the "accelerator never blocks serving" discipline applied uniformly).
  `resolve_backtest_cache_db_path` mirrors `resolve_cache_db_path` (env `TAPEOLOGY_EDGE_SWEEP_CACHE_DB`
  else `edge_report_backtests.db` sibling of the dataset dir) — a DIFFERENT env var/filename from
  the whole-report cache, so the two never collide.
- **`edge_report.py`**: `_split_cells` gains a `run_pair=None` provider seam — `None` (the
  default) is byte-identical to the pre-J-05 inline `_run_backtest` call; the pooling/ordering/
  aggregation code is untouched. `_ProgressReporter` gains `note_cache_hit()` (bumps the running
  `backtests_from_cache` counter without emitting its own patch — the caller's unchanged
  `pair_done()` picks it up). New `_build_caching_run_pair(...)` builds the caching `run_pair`
  closure: `bar_store_signature`/`config_fingerprint`/`config_content_hash`/`strategy_registry`
  are computed ONCE (outside the closure, proven by a dedicated coherence-guard test), never once
  per pair. `_compute_strategy_comparison_report` gains `sub_cache=None`; when supplied, it builds
  ONE caching provider (after `reporter` resolves) and threads it into BOTH the train and hold-out
  `_split_cells` calls — the same provider/cache instance serves both splits. New
  `_parallel_prewarm_sub_cache(...)` (CLI-only — see below) + module-level
  `_run_dataset_pairs_in_worker(...)` (the picklable `ProcessPoolExecutor` task target — this
  codebase's first use of `multiprocessing` anywhere): determines the eligible (dataset, all 3
  strategies) task set via the same eligibility test `_split_cells` itself uses, schedules
  largest-first (LPT) by each dataset's own recorded `event_counts.total`, and runs one task per
  dataset across `workers` worker processes (`spawn` context), each building its own stores from
  explicit paths and a throwaway temp journal DB, publishing to the shared durable sub-cache the
  instant each pair finishes. A registry with zero eligible pairs never constructs a process pool
  at all (proven by a test that makes `ProcessPoolExecutor` itself raise if touched).
  `run_strategy_comparison_report`'s `compute()` dispatch: when `sub_cache` is supplied AND
  `workers > 1`, it FIRST pre-warms the sub-cache via the parallel provider, THEN calls
  `_compute_strategy_comparison_report` sequentially (now 100% cache hits — reassembly is
  byte-identical to a sequential run by construction, since the aggregation code never changed).
  `workers in (None, 0, 1)` skips the pre-warm entirely — byte-identical to before J-05.
- **`edge_report_compute.py`**: CLI `main()` now also constructs a real `EdgeReportBacktestCache`
  (via `resolve_backtest_cache_db_path`) and passes `sub_cache=<cache>` alongside the
  already-passed `workers=args.workers`; `--workers`'s default now reads
  `TAPEOLOGY_EDGE_SWEEP_WORKERS` if set, else the existing `_DEFAULT_WORKERS = 4` constant.
  `EdgeReportComputeManager.trigger()` gains `sub_cache: EdgeReportBacktestCache | None = None`
  (default preserves every existing caller byte-for-byte), threaded into its own
  `run_strategy_comparison_report` call — a browser-triggered compute is resumable too. `trigger()`
  NEVER passes `workers` at all (not even `None` explicitly — simply omitted), so the parallel
  branch can never fire from the manager, structurally, not just by convention.
- **`routes.py`**: new `get_edge_report_backtest_cache()` dependency (the `get_edge_report_cache`
  precedent), threaded into `trigger_edge_report_compute` as a new `sub_cache` param — no second
  store/cache construction path. `get_edge_report`'s own body is untouched.

## Files Changed

- `apps/backend/app/research/edge_report_backtest_cache.py` (NEW) — `EdgeReportBacktestCache`,
  `pair_cache_key`, `resolve_backtest_cache_db_path`.
- `apps/backend/app/research/edge_report.py` — `_ProgressReporter.note_cache_hit`; `_split_cells`
  gained `run_pair=None`; new `_build_caching_run_pair`, `_eligible_datasets`,
  `_run_dataset_pairs_in_worker`, `_parallel_prewarm_sub_cache`; `_compute_strategy_comparison_report`
  gained `sub_cache=None`; `run_strategy_comparison_report`'s `compute()` dispatch gained the
  parallel pre-warm branch + docstring updates.
- `apps/backend/app/research/edge_report_compute.py` — module docstring updated; `_DEFAULT_WORKERS`/
  `_WORKERS_ENV`; `trigger()` gained `sub_cache=None` + docstring; CLI `main()` constructs
  `EdgeReportBacktestCache`, resolves `--workers`' default from env, passes `sub_cache=`.
- `apps/backend/app/research/routes.py` — new `get_edge_report_backtest_cache()`;
  `trigger_edge_report_compute` gained the `sub_cache` dependency + wiring.
- `apps/backend/tests/test_edge_report_backtest_cache.py` (NEW) — 18 tests: the key-busting
  matrix (pure function + a call-counting-stub proof, TC-5), lookup/publish mechanics, durability,
  corrupted-DB tolerance, thread concurrency, path resolution.
- `apps/backend/tests/test_edge_report.py` — +10 tests in a new J-05 section (TC-4/6/7/9/13, the
  non-vacuous multi-process TC-8 proof, a zero-eligible-pairs-never-spins-a-pool guard, two error-
  case tests, one coherence guard); 2 pre-existing J-04 tests updated (the `object()`/`workers=7`
  sentinel test now uses a real `EdgeReportBacktestCache` + `workers=1`, since `sub_cache`/
  `workers` are no longer inert; the hook-documentation coherence guard's expected literal strings
  updated for the two hooks' new type hints).
- `apps/backend/tests/test_edge_report_compute.py` — `_set_cli_env` gained
  `TAPEOLOGY_EDGE_SWEEP_CACHE_DB` (the SAME hazard `TAPEOLOGY_EDGE_REPORT_CACHE_DB` was already
  guarding against — the sub-cache's own default path would otherwise land beside the committed
  fixture dir); the old "`--workers` accepted-and-inert" test renamed/updated to reflect real
  (but degenerate-fixture-safe) behavior; +6 new tests (manager `sub_cache` default/threading/
  TC-11 resumability/TC-12 guard, CLI env-default + wiring spy, TC-10's non-vacuous published-
  rows-reused proof).
- `docs/handoffs/goal-fast_wall-iter-5-dev.md` — this handoff.

**Zero diff** (git-confirmed via `git diff --stat`): `levels.py`, `tradability.py`, `backtests.py`,
`bars.py`, `datasets.py`, `dataset_index.py`, `edge_report_cache.py` (method bodies — only
`_canonical`/`_config_content_hash` are imported elsewhere), `setups.py` (`_store_signature` is
imported directly, never re-derived or exported), `app/mcp/__init__.py`, `config.py`, and the
entire `apps/frontend/` tree — exactly the plan's expected scope, nothing wider.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (the framework's generic
`.claude/project-template.md` is still unfilled — see Known Issues, carried forward unchanged from
every prior iteration).

Targeted runs (all green before the full run):
- `pytest tests/test_edge_report_backtest_cache.py -q` → 18 passed.
- `pytest tests/test_edge_report.py -q` → 62 passed (52 pre-existing + 10 new).
- `pytest tests/test_edge_report_api.py -q` → 23 passed (unchanged).
- `pytest tests/test_edge_report_compute.py -q` → 27 passed (21 pre-existing/renamed + 6 new).

Full suite: **1517 passed, 7 skipped, 0 failed, 0 errors (1524 collected)** — up from the iter-4
baseline of 1482 passed / 7 skipped / 1489 collected by exactly **35 net-new tests** (18 + 10 + 7 =
35, confirmed by direct `def test_` diff-counting per file, matching the collected-count delta
exactly). Confirmed via raw dot-output character counting (`.`/`s`/`F`/`E`/`x`/`X` tally): 1517
dots, 7 `s`, zero `F`/`E`/`x`/`X` anywhere — this project's own test harness does not print the
usual final pytest summary line (a pre-existing environment quirk noted by iter-4's own handoff
too), so this counting method is the established verification technique.

`config.CONFIG.config_fingerprint()` confirmed still `4d665603569b9dbf` by direct computation (no
`Config` field added; every new module uses only stdlib `sqlite3`/`hashlib`/`json`/`os`/`tempfile`/
`multiprocessing`/`concurrent.futures`).

Named guard tests re-run individually and confirmed passing, byte-unmodified source:
`test_backtests.py::test_structure_tape_map_reads_tradability_never_recomputes_levels_or_zones`,
`test_backtests.py::test_structure_tape_reads_levels_from_the_one_canonical_compute_levels_owner`,
`test_backtests.py::test_default_fingerprint_still_pinned_with_the_new_structure_tape_fields_present`,
`test_setups.py::test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes`,
`test_setups.py::test_compute_setups_itself_never_touches_the_dataset_store`,
`test_mcp_server.py::test_advertised_tool_set_is_exactly_capability_6` (still exactly 18 tools).

## Live verification (beyond the automated suite)

Ran a SCOPED backend (ports 8391/3391, fresh temp journal/dataset/bar dirs, a private COPY of the
committed `tests/fixtures/datasets_j03` fixture, cold `TAPEOLOGY_EDGE_REPORT_CACHE_DB` AND
`TAPEOLOGY_EDGE_SWEEP_CACHE_DB` — never `.data/datasets`), matching iter-0/iter-4's own established
recipe:

- curl lifecycle: cold `GET /research/edge-report` → `status: "not_computed"`, `dataset_count: 1`,
  `compute: null`. `POST /research/edge-report/compute` → `started: true`. Polled `GET
  .../compute` → resolved `state: "done"` in well under a second (the honest zero-eligible-pairs
  empty compute, PG not being a config-owned panel symbol). `GET /research/edge-report` afterward
  → the real warm report shape, `train.cells: []`, no `status` key.
- **Chrome MCP browser pass succeeded this session** (unlike the last two iterations' documented
  environmental failure): captured real screenshots for TC-1 (click → "Computing…" + "0 / 0
  backtests" progress line → terminal warm-report render, zero full-page reload), TC-2 (the
  not-computed panel's exact pre-click text; a post-compute reload serving the warm report
  directly with no button; every other `/structure` section — Tradable Map, Case Studies, Fetch
  from Yahoo Finance, Registry, Comparison — rendering exactly as shipped, confirmed both visually
  and via DOM-text extraction), and TC-3 (a `state: "failed"` compute snapshot, arranged by
  corrupting the scoped dataset copy, triggering a compute, then restoring the file content
  in-place without restarting the backend — the not-computed panel renders the exact backend
  `EdgeReportError` message verbatim: "1 dataset file(s) failed integrity verification
  (['5232fa672b7b4077a5117d34b14c807d.json']) — the report stops with nothing written", and the
  button relabels to "Retry compute", enabled).
- Torn down cleanly: both scoped ports confirmed free afterward, no stray `uvicorn`/`next dev`
  process for this project remains.

## Known Issues

- **A methodological note on TC-3's arrangement**: my first attempt corrupted the dataset and left
  it corrupted while navigating — this produces a DIFFERENT (and also legitimate) render: `GET
  /research/edge-report` itself 500s on every call (since `peek_strategy_comparison_report`
  re-verifies dataset integrity on every read, independent of the compute snapshot), so the
  frontend shows a generic `UnavailablePanel`-style error ("edge report could not complete: ...
  Nothing cached and nothing fabricated is shown in its place."), never the not-computed panel's
  own embedded-failed-compute render at all. TC-3 specifically wants the LATTER (the not-computed
  panel's own `compute.error` field rendered), which requires the dataset to read HEALTHY again
  while the compute manager's in-memory snapshot still remembers its last failure — achieved by
  restoring the file content without restarting the backend (a restart would also wipe the
  in-memory snapshot). This is a genuine, useful finding for future browser-QA passes of this
  exact flow: iter-4's own `ui-test-plan.md` UT-05 predicted the not-computed-panel-with-error
  render from a *permanently* corrupted dataset, which is not what actually happens — the
  corrected recipe (corrupt → trigger → restore, all without a restart) is what produces it.
  Flagging for the reviewer/auditor/QA lanes to confirm and, if useful, fold into a corrected
  `ui-test-plan.md` for this journey.
- **TC-8's non-vacuous multi-process proof uses a purpose-built 2-dataset synthetic scan fixture
  (the SAME `scan_bar_store`/`scan_config`/`_record_v1_arming_dataset` machinery `test_edge_report.py`
  already established for J-04's own non-degenerate tests), not the phase spec's own "e.g."
  fixture (`apps/backend/tests/fixtures/datasets`).** That fixture's one symbol (PG) is not a
  config-owned panel symbol, so it always resolves ZERO eligible pairs — with nothing to
  distribute across workers, "at least two distinct worker process ids were used" would be
  impossible to prove from it. The synthetic fixture makes the proof genuinely non-vacuous: 2
  datasets, 6 real backtests, `_parallel_prewarm_sub_cache(..., workers=2)` returns 2 tasks whose
  RETURNED `os.getpid()` values (crossing the process boundary via pickling — this cannot be
  faked by a same-process shortcut) are asserted distinct, and the reassembled report is
  byte-identical to an independent sequential compute. A SEPARATE, lighter CLI-level test proves
  the CLI's `--workers`/`sub_cache` kwargs genuinely reach `run_strategy_comparison_report`
  (kwarg-capturing spy, fast, degenerate fixture) — together these two tests cover both the
  mechanism (real multiprocessing, real byte-identity) and the wiring (CLI → function), which I
  judged more rigorous than a single test straining to do both through a fixture that can't
  actually exercise parallelism.
- **Two shell commands during the browser-verification pass returned exit code 144 despite
  succeeding** (`pkill -f "uvicorn ..."` twice) — an apparent artifact of this sandboxed shell
  environment when a matched process is actually killed, not a real failure; verified in every
  case via a follow-up port/process check that the intended process was in fact stopped. No repo
  files were affected.
- **`.claude/project-template.md` is still the generic, unfilled vendored template** (the same
  finding every prior iteration's dev handoff has recorded) — test/build commands used above came
  from `pyproject.toml` and prior iterations' own handoffs.
- **Bonus real-corpus items intentionally NOT attempted this iteration** (matching the phase
  spec's own explicit framing — never required for this iteration's Definition of Done): running
  the CLI warmer to completion against the full `.data/datasets` real corpus, and the
  `reports/pnl/pnl-history.md` append this would enable. J-05 makes this leg cheaper whenever it
  does eventually run (resumable + parallel), but does not itself run it — the documented
  CPU-pin hazard from era 5B/the "Fast Wall" interlude's own founding measurement makes this an
  operator-gated act, not something to attempt speculatively inside a dev/QA pass.
- **`EdgeReportComputeManager.trigger()`'s `sub_cache` resumability test
  (`test_trigger_resumability_end_to_end_via_a_real_sub_cache`) uses `force=True` on its second
  `trigger()` call** — necessary because the FIRST trigger already warmed the WHOLE-report cache
  too (a different cache than the sub-cache under test), and `get_or_compute`'s hot/durable hit
  would otherwise skip calling `compute()` (and therefore the sub-cache machinery) entirely on the
  second call. This is a genuine, intentional test design choice, not a workaround for a product
  gap — flagging only so a reviewer doesn't mistake the `force=True` for masking something.

## Suggested Next Phase

J-06 ("Restarts stop hurting — the durable setups scan cache", `setups_scan_cache.py`) per
goal.md's own dependency order — the last of the seven journeys named in this interlude's goal.md.
Independent of J-05 (different file: `setups.py`'s `compute_setups`, not `edge_report.py`).
Before that: the operator may want to run the CLI warmer's `--workers N` against the real corpus
now that it is genuinely parallel and resumable (bonus, non-blocking, operator-gated — see Known
Issues above), and/or fold the corrected TC-3 arrangement recipe into a refreshed
`ui-test-plan.md` for a future QA pass of this journey.
