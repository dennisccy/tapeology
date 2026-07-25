# goal-desk-iter-2 Dev Handoff

**Phase:** goal-desk-iter-2
**Date:** 2026-07-25
**Agent:** developer
**Status:** complete

## What Was Built

- **Desk coverage read** (`app/research/desk_coverage.py`, new) — the pinned desk top-up timeframe
  set `DESK_TOPUP_TIMEFRAMES = ("1h", "4h", "1d", "1w")` (a plain structural constant, re-verified
  live against `config.py:770` `bar_timeframes`, `config.py:821` `sr_timeframe_weights`,
  `levels.py:106` `PRIOR_PERIOD_TIMEFRAMES`, and `yahoo.py`'s `_INTERVAL_MAP`/`4h` resample — NOT a
  `Config` field, mirroring the `PRIOR_PERIOD_TIMEFRAMES` precedent) and `get_desk_coverage()`, a
  pure read over the latest universe snapshot's members x that timeframe set, reporting `has_bars`
  + `latest_window_end_utc` per pair. Reads `bar_index` ONLY (T-4) via a new additive
  `BarIndex.coverage()` accessor — never touches `BarStore`.
- **Additive `BarIndex` extension** (`app/research/bar_index.py`) — one new method,
  `coverage(symbol, timeframe) -> (has_bars: bool, latest_window_end_utc: str | None)`, a single
  `COUNT`+`MAX` SQL query over the already-existing `window_end_utc` column. Deliberately did NOT
  add a field to `BarIndexHit` (the plan's other named option) — `tests/test_bar_index.py`'s
  existing tests construct `BarIndexHit` with exactly its original 3 fields via `==` equality
  against real `.lookup()`/`.reindex()` results, so a new field with a default would have silently
  broken those equality checks the first time a real `window_end_utc` value diverged from the
  default. `.lookup()`/`.insert()`/`.list()`/`.reindex()` and the `BarIndexHit` dataclass are
  byte-unchanged.
- **`GET /research/desk/coverage`** (new route in `desk_routes.py`) — honest empty payload
  (`universe_snapshot_id: null`, `members: []`, HTTP 200, never 404) before any universe snapshot
  exists; a single synchronous read (no compute-manager needed, mirroring
  `GET /research/desk/universe`'s own shape).
- **Desk bar top-up compute manager** (`app/research/desk_topup_compute.py`, new) —
  `DeskTopupComputeManager` mirrors `EdgeReportComputeManager` verbatim in shape (single-flight,
  cooperative cancel, atomic progress snapshot, in-memory/process-scoped, honestly lost on
  restart). The shared walker `run_topup()` calls `routes.record_bar_series` **in-process, per
  (symbol, timeframe) pair** — the SAME store-first fetch-and-record logic
  `POST /research/bars` already uses, never a second implementation. Per-pair outcome
  (`"reused"`/`"fetched"`/`"failed"`) is classified by comparing the returned series'
  `created_utc` against a timestamp captured immediately before the call (a store-first hit's
  `created_utc` necessarily predates it; a freshly-written series' does not) — this reads only the
  already-returned field, so it never duplicates `record_bar_series`'s own adapter/feed-resolution
  decisions. A failing pair (`HTTPException` or any other exception) is caught, recorded as
  `"failed"` with the detail preserved verbatim, and the walk continues — never aborts the job.
  Resumability is a property of `record_bar_series`'s own store-first coordinator, not job-level
  checkpoint bookkeeping: a cancelled run's `outcomes` list is simply shorter than `pairs_total`,
  and a fresh `trigger()` naturally re-reports already-covered pairs as `"reused"` with zero new
  vendor calls.
- **Three routes** (`POST /research/desk/topup/compute`, `GET /research/desk/topup/compute`,
  `POST /research/desk/topup/compute/cancel`) mirroring `routes.py`'s `/edge-report/compute` trio
  exactly (single-flight `{"started": bool, "compute": <snapshot>}`, verbatim-snapshot poll,
  409-when-idle cancel).
- **CLI warmer** (`python -m app.research.desk_topup_compute`) — runs `run_topup()` to completion
  synchronously against the operator's real universe/bar dirs, one progress line per pair, exit 1
  if any pair failed.
- **No new `Config` field.** The top-up's fetch window (`_fetch_window_now()`) uses a single
  hardcoded 730-day lookback (matching Yahoo's own `1h`/`4h` retention ceiling,
  `yahoo.py:95` `_INTERVAL_LIMITS["1h"]`) ending "today" (UTC), for ALL four pinned timeframes —
  the vendor adapter's own `_clamp_to_retention` already trims/notes anything a timeframe can't
  serve, exactly as it does for a manual `POST /research/bars` call, so the desk module needs no
  per-timeframe retention table of its own. This is a plain module constant
  (`_TOPUP_LOOKBACK_DAYS`), not a `Config` field — it shapes no persisted research value, only
  which bars a top-up call happens to ask the vendor for (the same rationale `yahoo.py`'s own
  `_INTERVAL_LIMITS` and `bar_recency_delay_seconds` carry). Zero Path-A work was needed this
  iteration; `Config().config_fingerprint()` is unchanged by construction (no field was added).
- **Widened kept-route capture (TC-13)** — `runs/goal-desk-iter-2/kept-route-baseline-24.txt` /
  `kept-route-after-24.txt`: all 24 kept GET route templates (OpenAPI-enumerated `/research`,
  `/tape`, `/meta` routes, excluding the desk-era's own `/research/desk/*`), captured before/after
  this iteration's diff via a `git worktree add <tmp> HEAD` (a clean pre-diff checkout, no stash
  needed since nothing was committed this session) against a SHARED data dir populated by this
  iteration's own fixture top-up run (a real `run_topup()` call with `FakeAdapter`, 3 of 8 members
  covered across all 4 timeframes — not near-empty). Diff: **zero deltas**, including on
  `/research/levels`/`/research/tradability` (30KB/3.5KB real computed bodies, not empty
  placeholders) — the exact class of route an empty-dir capture (iter-1's audit finding T2) cannot
  exercise.
- **41 new tests** across three files (see Files Changed) plus 5 additive tests appended to the
  existing `test_bar_index.py`.

## Files Changed

- `apps/backend/app/research/desk_coverage.py` (new) — `DESK_TOPUP_TIMEFRAMES` constant,
  `get_desk_coverage()`.
- `apps/backend/app/research/desk_topup_compute.py` (new) — `DeskTopupComputeManager`,
  `run_topup()`, `_run_one_pair()`, the CLI `main()`.
- `apps/backend/app/research/bar_index.py` — additive: `BarIndex.coverage()`. No other line
  changed.
- `apps/backend/app/research/desk_routes.py` — added `GET /research/desk/coverage` and the three
  `/research/desk/topup/compute*` routes + their FastAPI dependencies
  (`get_desk_topup_manager`); the module docstring was rewritten to describe the expanded scope
  (the `fetch_universe`/`get_universe` J-01 handler bodies are byte-unchanged — verified via
  `git diff`, no `-`/`+` lines inside either function).
- `apps/backend/tests/test_desk_coverage.py` (new, 8 tests) — pinned-timeframe-set assertion,
  honest-empty, truth-table (2-of-5 covered), freshness exactness (incl. max-across-multiple-
  recordings and raw-string-not-epoch), index-only call-counting guard (T-4).
- `apps/backend/tests/test_desk_topup_compute.py` (new, 17 tests) — manager mechanics (mocked
  `_run_one_pair`, deterministic `threading.Event`-gated: shape/pairs_total, single-flight,
  fresh-job-after-terminal, cancel-mid-flight, unexpected-crash-resolves-failed, snapshot-copy-
  independence) + store-first/resumability against the REAL `record_bar_series` path with
  `FakeAdapter` (first-run-all-fetched, second-run-all-reused-zero-vendor-calls, pre-populated-
  pairs-report-reused-the-rest-fetched, honest-per-pair-failure-with-a-custom-`_NthCallFailsAdapter`
  proving the run continues) + routes (GET-never-computes on both new GET routes, trigger/poll
  round-trip, idle-cancel-409, cancel-while-running-then-idle-409).
- `apps/backend/tests/test_bar_index.py` — 5 tests appended (dataclass-shape pin, empty/populated/
  multi-recording/raw-string `coverage()` behavior). Every pre-existing line is byte-unmodified
  (`git diff --stat`: 67 insertions, 0 deletions).
- `runs/goal-desk-iter-2/kept-route-baseline-24.txt`, `kept-route-after-24.txt` (new) — the
  widened TC-13 capture.

**Not touched, deliberately:** `apps/backend/app/config.py` (no new Config field needed — see
above), `apps/backend/app/main.py` (the desk router was already mounted in iter-1; no lifespan
change needed since the top-up manager is a plain FastAPI-dependency singleton, not a
`ResearchRegistry` property — see Known Issues), `apps/backend/app/research/routes.py`
(`record_bar_series`/`ResearchRegistry`/`get_bar_index`/`get_bar_store` are imported and reused
verbatim, never modified — `routes.py` itself has zero diff).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`

Result: **1240 passed, 8 skipped, 0 failed** (iter-1's floor was 1210 passed / 8 skipped — this
diff adds exactly 30 new passing tests, zero new skips, zero regressions).

- `Config().config_fingerprint()` == `08e471b10130e1e2` — unchanged (confirmed live via
  `python -c`; no new Config field was added this iteration, so no Path-A work was required).
- **TC-12 (J-01 stays passing):** `test_desk_universe.py` + `test_desk_universe_api.py` re-run in
  isolation — 41/41 passing, unchanged from iter-1. `git diff` on `desk_routes.py` shows the
  `fetch_universe`/`get_universe` function bodies carry zero added or removed lines (only the
  module docstring and the import block changed) — the J-01 route handlers are byte-identical to
  what iter-1 shipped.
- **TC-13 (widened kept-route capture):** see "What Was Built" above — 24/24 templates
  byte-identical (status + sha256 + body_len) before/after this diff, against a populated data
  dir. Zero deltas.
- **TC-5/T-4 (index-only coverage):** `test_coverage_issues_zero_bar_store_calls` monkeypatches
  `BarStore.list`/`.get` at the class level and asserts zero calls during `get_desk_coverage()` —
  passes; `get_desk_coverage` also structurally cannot reach a `BarStore` (it is never passed one).
- **TC-7/TC-8 (store-first / resumability):** proven against the REAL `record_bar_series` path
  (not mocked) — a second `trigger()` over the same universe reports all-`"reused"` with the
  vendor's `fetch_bars_calls` count unchanged; pairs recorded ahead of time (standing in for an
  earlier interrupted run) report `"reused"` while the rest report `"fetched"`, with vendor calls
  growing by exactly the remaining-pairs count.
- Threading-based tests (`test_desk_topup_compute.py`'s single-flight/cancel tests, which use
  `threading.Event` gating rather than wall-clock sleeps) re-run 5x consecutively with zero
  flakiness.

### Live external verification (Yahoo, real vendor, zero mocks)

Per the pre-handoff checklist, ran the NEW `run_topup()` orchestration for real, against a
temp-scoped data dir (never `.data/`), for AAPL x all 4 pinned timeframes, with no `FakeAdapter`
override — the real `YahooAdapter`:

```
AAPL 1h: fetched
AAPL 4h: fetched
AAPL 1d: fetched
AAPL 1w: fetched
coverage read-back: AAPL has_bars=True on all 4 timeframes, latest_window_end_utc=2026-07-25
summary: 4 fetched, 0 failed
```

All four pairs succeeded on the first real attempt. (yfinance printed two informational
"possibly delisted; no price data found" lines for the still-forming final `1h` chunk near the
UTC-day boundary — pre-existing, harmless `_chunks()`/vendor library chatter documented in
`yahoo.py`'s own module docstring, "one empty chunk is NOT fatal"; not a new finding, not a bug
in this iteration's code, and every pair still reported `"fetched"` with real bars recorded.)

This is NOT the real ~100-symbol operator top-up (explicitly out of scope for dev work — see the
phase spec's OUT OF SCOPE section); it is a single-symbol proof that the new orchestration code
genuinely drives the real vendor correctly, not just `FakeAdapter`. The temp dir was deleted after
the check; nothing was written to the real `apps/backend/.data/`.

### Service startup (dev.sh)

Ran `scripts/dev.sh` twice (backend `:8301`, frontend `:3301`). Both runs: backend health check
200, frontend root 200, no errors in either log. **Found and worked around a pre-existing gap in
`scripts/dev.sh` (not touched this iteration — out of scope, logged here per the pre-handoff
checklist's explicit instruction to verify this):** `dev.sh`'s cleanup only kills its own two
direct child PIDs (`$BACKEND_PID`/`$FRONTEND_PID` — the uvicorn *reloader* and the `npm exec`
wrapper). Uvicorn's `--reload` mode correctly cascades a signal to its own worker subprocess, so
the backend's full tree dies cleanly. The frontend's tree does not: `npm exec` → `sh -c` → `node
next dev` → `next-server` are grandchildren that survive a `kill` of the `npm exec` PID alone,
leaving `next-server` still bound to port 3301. Verified directly (killed `bash scripts/dev.sh`,
observed `next-server` and its `node` parent still running and the port still held), then manually
killed the survivors before starting the second run, which then came up cleanly with no port
conflict. Also found on my OWN cleanup: sending `kill -9` directly to the uvicorn *reloader* PID
(bypassing `dev.sh`'s trap) similarly orphans the reloader's *worker* subprocess — `SIGKILL`
doesn't allow the reloader to forward the signal, so I had to find and kill the worker PID
separately via `lsof -i :8301`. All server processes (both runs, plus my own manual test/verify
sessions) were confirmed fully stopped (`lsof`/`ss` show both ports free) before finishing this
task.

## Known Issues

- **`scripts/dev.sh` does not clean up the frontend's full process tree on stop** (see above) —
  a pre-existing gap, not introduced or fixed this iteration (out of scope: this is an unrelated
  shell script, not part of J-02's backend work). Documented so the next iteration that touches
  service startup/QA tooling doesn't have to rediscover it.
- **The desk top-up compute manager is a `desk_routes.py` module-level singleton, not a
  `ResearchRegistry` property** (unlike `EdgeReportComputeManager`). This is a deliberate,
  necessary deviation from the "mirrors `EdgeReportComputeManager` verbatim" plan language:
  `DeskTopupComputeManager` reuses `routes.record_bar_series` in-process, so `desk_topup_compute.py`
  imports FROM `routes.py`. If `ResearchRegistry` (in `routes.py`) held the manager instance,
  `routes.py` would need to import `desk_topup_compute.py` back — a circular import. Instead,
  `get_desk_topup_manager()` is a plain FastAPI dependency (the `get_universe_fetcher` pattern
  already established in `desk_routes.py`), fully test-overridable via
  `app.dependency_overrides`. Functionally equivalent for every acceptance clause (single-flight,
  progress poll, cancel, GET-never-computes) — verified by the route-level tests — but it means
  `apps/backend/app/main.py`'s shutdown drain (which joins `registry.edge_report_compute`/
  `registry.backtest_jobs`) does NOT also join the desk top-up thread. Since the worker thread is
  `daemon=True` (the same "in-flight jobs honestly lost on restart" contract every compute
  manager in this app already carries), this is a documented, accepted parity gap, not a
  correctness bug — flagging it explicitly per honesty policy rather than silently deviating from
  the plan's stated shape without comment.
- **"Reused" vs "fetched" classification uses a `created_utc`-timestamp heuristic**, not a direct
  signal from `record_bar_series` (which returns the same shape either way). Documented in
  `desk_topup_compute.py`'s module docstring: reliable for every path this iteration's tests and
  the live check exercise, but the one theoretical edge case is the existing route's own
  `stale_clamped` 409-recovery branch (a vendor call that runs but returns content already on
  file for a previously vendor-capped window) — that case would be labeled `"reused"` even though
  a real vendor call happened. This branch is not reachable by any of this iteration's fixtures
  (it requires a previously `vendor_limit`-capped recording made on an earlier UTC day) and is not
  named by any DEFINITION OF DONE/TC line; noted here for completeness, not because it blocks
  anything this iteration claims.
- **The top-up's fetch window is a single 730-day lookback for all four timeframes**, not a
  per-timeframe-tuned window — see "What Was Built" for the rationale (matches Yahoo's own `1h`/
  `4h` ceiling; the adapter's existing retention clamp handles the rest). If a future iteration
  needs a different window (e.g., to reduce real-run latency further), that is a one-constant
  change in `desk_topup_compute.py`, not a new architecture.
- **No CLI `--symbol` filter** — the CLI warmer always tops up every member of the latest
  registered universe snapshot; not named as a requirement by J-02's steps, and easy to add later
  if needed.
- Everything else — coverage/top-up remain entirely backend/REST/CLI surfaces this iteration
  (`Frontend Present: no`, per the plan); zero frontend files touched; `UI_ROUTES`/nav unchanged
  (verified live: `GET /meta/ui-routes` still returns exactly the 2 existing rows). This is
  explicitly correct scope, not an oversight — `/desk` ships in J-04.
