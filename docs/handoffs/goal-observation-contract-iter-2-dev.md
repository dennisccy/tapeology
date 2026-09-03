# goal-observation-contract-iter-2 Dev Handoff

**Phase:** goal-observation-contract-iter-2
**Date:** 2026-09-03
**Agent:** developer
**Status:** complete

## What Was Built

Binding Execution Order step 2 only (the manager-held atomic settled pair and the time law,
J-02 block 2) -- lean, backend-only, zero served/UI surface, exactly per the iter spec's IN
SCOPE list. `apps/backend/app/observation_contract.py` is untouched (out of scope this
iteration; its time-law arithmetic from iter-1 was already correct).

- **`WatchManager`'s per-ticker atomic settled pair** (`apps/backend/app/watch_manager.py`):
  `self._settled: dict[ticker -> (EngineSnapshot, settled_at_epoch | None)]`, written by
  exactly ONE helper, `_settle(engine, *, new_event)`:
  - `new_event=True` -- called immediately after `process_event` (and any same-tick
    `set_delivery_lag`) in every feeder path (`_feed`, `_feed_paced` via `_replay_events`,
    `_feed_progressive` via `_replay_events`, `_feed_live`). Stamps `time.time()` NOW as the
    newly-settled instant, in the SAME dict-item write that stores the snapshot from that tick
    -- the atomic-read invariant.
  - `new_event=False` -- called after every lifecycle-only status mutation that carries no new
    event: `pause()`, `resume()`, the `waiting` flip at the start of each feeder, the live
    stale-gap flip, and the `closed`/`failed` flips (natural exhaustion, `CancelledError`, and
    the `except Exception` branch) in every feeder. Carries the PREVIOUS `settled_at_epoch`
    forward unchanged (Constitution §2: "no new event, same availability") -- never re-stamps
    to "now".
  - `_settle` derives the ticker from `engine.snapshot().ticker`, so no feeder needed a new
    `ticker` parameter threaded through its call chain.
- **`WatchManager.get_observation_source(ticker)`** -- the one atomic managed-observation read.
  Returns `(settled EngineSnapshot, pinned-ISO settled_at_utc | None, end_reason)` from the ONE
  settled pair; it never calls `engine.snapshot()` at read time. Returns `None` for a ticker not
  currently watched (mirrors `get()`/`pause()`/`resume()`'s "no fabricated engine" idiom).
  `end_reason` is read from the live `TapeEngine.end_reason` property, which changes only on a
  terminal flip that itself always calls `_settle` in the same statement sequence, so it stays
  in lockstep with the returned snapshot.
- **Cold-reset at every fresh-engine construction** (`watch`, `watch_with_provider`,
  `watch_with_progressive_historical`, `watch_with_async_provider`): each sets
  `self._settled[ticker] = (engine.snapshot(), None)` immediately after registering the new
  engine. This is a design decision beyond the iter spec's literal call-site list (see below).
- **`watch_manager._iso_utc(epoch)`** -- a private per-module ISO formatter matching
  `observation_contract._iso_utc`/`research/bars.py`'s `_iso_utc` byte-for-byte, following this
  repo's established convention of each module owning its own small ISO formatter (~30
  `_iso_utc_now` precedents already exist) rather than importing a private cross-module name.
  Cross-checked against `observation_contract._iso_utc` by a dedicated test so it can never
  silently drift.
- **`apps/backend/tests/test_tape_observation_time.py`** (new, 33 tests) -- covers TC-1..TC-13
  from the iter spec, each a named test with `test_counterexample_*` pairs where the spec
  requires one:
  - TC-1..TC-4: the atomic-read interleaving proof + pause-carries-forward, via a deterministic
    SYNC harness (`manager.watch(...)` called from a plain, non-`async def` test function finds
    no running event loop and leaves the engine cold with no feeder -- its own documented "the
    caller feeds the engine itself" contract, precedented in `test_watch_manager.py`). This gives
    race-free control over exactly when each event settles, which a real running feeder cannot
    offer (it settles both N and N+1 back-to-back with no `await` point between them).
  - TC-5/TC-6: `observed_at_utc` across sim / `HistoricalProvider` (committed PG SIP fixture) /
    `DatasetStore.replay` (committed `datasets_j03` fixture) / `LiveProvider` (merged fixture
    records), plus both null clauses.
  - TC-7/TC-8/TC-9: historical/dataset_replay honest-null availability; live
    `available_at_utc == settled_at_utc` from a monkeypatched `watch_manager` clock via the REAL
    `_feed_live` path (`LiveProvider` over hand-built `RawQuote`/`RawTrade` records, not a bare
    event double, so the epoch anchor and delivery lag are genuinely computed); a clock-skew
    counterexample showing the delivery-lag-derivation shortcut is wrong, not merely unused (a
    clamped lag makes `observed + lag != available_at_utc` when settlement genuinely precedes the
    record's own event time); the delivery-lag telemetry cross-check.
  - TC-10: `availability_basis` per `source_mode`, and an unrecognized-mode raise. Written to
    match Constitution §2's table exactly -- `historical` and `dataset_replay` legitimately
    SHARE `historical_arrival_unknown` by design, so the test asserts "defined for every mode"
    and the correct 3-distinct-values shape, not a false "all four pairwise distinct" claim.
  - TC-11: the pinned ISO function round-trips to the microsecond, plus the
    `watch_manager._iso_utc` vs `observation_contract._iso_utc` drift cross-check.
  - TC-12: two independent `DatasetStore.replay` reruns yield identical `observation_hash` at
    every tick (1963 events, both runs).
  - TC-13: an AST scan of `app/engine/*.py` (via `observation_contract.ENGINE_SOURCE_MODULES` /
    `_ENGINE_DIR`, unchanged from iter-1) proving zero `time.time`/`datetime.now`/
    `datetime.utcnow`/`random.*`/`subprocess` references, with three counterexample fixtures.
  - Plus two extra error-case tests from TESTING REQUIREMENTS ("get_observation_source on an
    unwatched ticker returns None") and one extra regression test proving the cold-reset fix
    (below) actually prevents a re-watched ticker from reading a prior watch's stale pair.

### Design decision made without a stop-and-ask (documented for the reviewer)

**The four `watch*` constructors now cold-reset `self._settled[ticker]` to
`(engine.snapshot(), None)` immediately after registering the fresh engine -- a write site NOT
in the iter spec's literal enumeration** ("written by exactly ONE helper, called after every
process_event ... and after every lifecycle-only status mutation ... pause(), resume(), the
stale flip in `_feed_live`, and the failed/closed flips"). Reasoning: without this reset, a
stopped-then-re-watched ticker would have a stale `self._settled[ticker]` entry left over from
its PRIOR (now-discarded) engine instance. Since a fresh engine's feeder does not call `_settle`
until its first status/event write, `get_observation_source` called in that narrow window would
return the WRONG engine's snapshot/settled_at_utc paired under the CURRENT (different) watch --
a genuine violation of the atomic-read invariant this iteration exists to build, not merely a
cosmetic gap. The reset is a direct dict-item assignment (matching the existing
`self._speeds[ticker] = speed_cell` precedent at the same call sites), not routed through
`_settle` (which is reserved for the enumerated event/lifecycle write sites), so "written by
exactly ONE helper" still holds for every one of THOSE sites.
`test_rewatch_before_first_settle_never_returns_a_prior_watchs_stale_pair` in the new test file
proves the fix; I verified by temporarily reverting it that `get_observation_source` would
otherwise return the stale engine object in that scenario.

## Files Changed

- `apps/backend/app/watch_manager.py` -- the settled-pair dict, `_settle`,
  `get_observation_source`, the `_iso_utc` helper, and settle calls threaded through
  `pause()`/`resume()`/all five feeder paths/the four `watch*` constructors.
- `apps/backend/tests/test_tape_observation_time.py` -- new file (33 tests).

No other file touched. `apps/backend/app/observation_contract.py`, `app/main.py`, and every
frontend file are unchanged (verified via `git status`/`git diff --stat`).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_time.py -v`
Result: 33 passed, 0 failed.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_watch_manager.py tests/test_stream_lifecycle.py tests/test_pause.py tests/test_epoch_anchor.py -q`
Result: all pass (0 failed) -- the guard-list files (`test_stream_lifecycle.py`,
`test_watch_manager.py`) pass unedited.

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (run TWICE)
Result, run 1: one failure, `tests/test_tick_recorder.py::test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates`
-- a pre-existing, unrelated flake (see Known Issues). Result, run 2 (immediately after,
no code change): **4001 passed / 8 skipped / 0 failed** (4009 collected via
`--collect-only -q` per-file counts, tallied per the iter-0 lessons-ledger note since this
venv's pytest 9.1.1 prints no final "N passed" summary line). 4009 = iter-1's baseline 3976
collected (3968 passed + 8 skipped) + 33 new tests in `test_tape_observation_time.py`. No fewer
than iter-1's baseline, plus this iteration's new tests, 0 failed -- DoD met.

Command: `python3 -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"`
Result: `08e471b10130e1e2` -- unchanged.

Command: `cd apps/frontend && npx tsc --noEmit`
Result: 0 errors (unaffected -- no frontend file touched).

### Live backend smoke check (Pre-handoff verification / DoD's browser-equivalent regression)

Started `apps/backend` via `scripts/start-backend.sh` on the project's pinned offset port
(8301), then via curl: `POST /watch/SIM-BIDABS` -> `stream_status: live`; `GET
/tape/SIM-BIDABS/observation` -> **404** (route not yet built -- expected, correct, matches DoD);
`POST /watch/SIM-BIDABS/pause` -> `stream_status: paused, paused: true`; `POST
/watch/SIM-BIDABS/resume` -> `stream_status: live`; `DELETE /watch/SIM-BIDABS` -> 200, then both
`GET /tape/SIM-BIDABS/state` and `GET /tape/SIM-BIDABS/observation` -> 404. Exactly the DoD's
"status dot transitions live -> paused -> live, then stops" and "`/tape/SIM-BIDABS/observation`
still 404s" -- confirmed live, not just via unit test. Backend process was killed
(`pkill -f "uvicorn main:app"`) after the check; no server left running.

## Known Issues

- **Pre-existing, unrelated flake confirmed, not caused by this iteration's changes**:
  `tests/test_tick_recorder.py::test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates`
  failed exactly once, in the FIRST full-suite run today, on a coincidental digit-substring
  collision: that test's `format_cli_progress_line` embeds a real wall-clock-derived
  `elapsed_seconds` (computed from a hardcoded past `started_utc="2026-06-01T13:00:00Z"` to
  `datetime.now()` via `_iso_utc_now()`), and on that run the resulting elapsed-seconds digit
  string happened to contain `"4253"` as a substring, colliding with the test's own
  `trades_total: 4253` fixture value on its forbidden-substring blacklist. This file is untouched
  by this iteration (I only touched `watch_manager.py` and added a new test file with no
  `tick_recorder` dependency). Verified NOT a regression: (1) the single test passed 3/3 times
  when re-run in isolation immediately after; (2) a full second `pytest tests/ -q` run
  immediately afterward (no code change in between) passed with 0 failures. This is a real,
  pre-existing test-design fragility (a CLI-progress-line test depending on genuine wall-clock
  elapsed time against a fixed past date, which will periodically produce a digit collision with
  its own fixture's constants) -- out of scope to fix this iteration (untouched file, not listed
  in the iter spec's IN SCOPE), but worth flagging for a future cleanup.
- J-02 cannot fully pass this iteration by design: its Acceptance requires the served JSON at
  `/tape/SIM-BIDABS/observation`, which needs the route (iteration 5, per the Binding Execution
  Order). This is the expected, correct signal per the iter-0 lessons entry, not a gap in this
  iteration's own scope.
- No `Config` field was added (module-level constants/helpers only, per Constraints).
