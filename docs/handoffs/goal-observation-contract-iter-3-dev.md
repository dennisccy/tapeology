# goal-observation-contract-iter-3 Dev Handoff

**Phase:** goal-observation-contract-iter-3
**Date:** 2026-09-04
**Agent:** developer
**Status:** complete

## Note on this handoff

At dispatch, `runs/goal-observation-contract-iter-3/status.json` already showed
`current_step: "dev_complete"` (timestamped the previous day) and the implementation, migrations-free
schema, and the new test module were already present and complete in the working tree — but no dev
handoff file existed yet at the path `status.json` already listed. This indicates a prior developer
session finished the implementation and test run but was interrupted before writing the handoff. This
session independently re-verified every IN SCOPE item and the full Definition of Done against the spec
and the actual code (not just trusting the prior `status.json` claim), re-ran every test, and now writes
this handoff. No implementation changes were needed beyond what was already in the working tree.

## What Was Built

- `WatchManager.SourceDescriptor` (`apps/backend/app/watch_manager.py`) — a frozen dataclass carrying
  the per-watch source/session descriptor: `source_mode`, `data_feed`, `window_start_utc` /
  `window_end_utc`, `dataset_id` / `dataset_checksum` (always `None` for a WatchManager-managed watch),
  `session_id` (uuid4 hex minted at watch creation), `session_started_at_utc` (pinned-ISO wall clock at
  creation), `profile_id` (`PROFILE_DEFAULT`).
- `WatchManager._record_source(...)` — records the descriptor exactly once per fresh engine, called from
  all four `watch*` constructors (`watch`, `watch_with_provider`, `watch_with_progressive_historical`,
  `watch_with_async_provider`), using the same cold-reset-per-fresh-engine pattern already used for
  `_settled`. `data_feed` is resolved via the single existing `data_feed_for_scenario` — no second
  scenario-prefix parser.
- `watch_with_provider(...)` / `watch_with_progressive_historical(...)` — new optional
  `window_start_utc: str | None = None, window_end_utc: str | None = None` keyword parameters
  (backward-compatible defaults; every existing caller that omits them is unaffected).
- `WatchManager.get_observation_source(ticker)` — return shape widened from a 3-tuple to
  `(EngineSnapshot, settled_at_utc, end_reason, SourceDescriptor)`, read from the SAME per-ticker state
  as before (no re-fetch, no second read of the settled pair).
- `WatchManager._settle(...)` — added the identity check the iter-2 reviewer flagged as a carried-forward
  MINOR: `if self._engines.get(ticker) is not engine: return` before any write. A stale/superseded
  engine's late write (e.g. a cancelled feeder's `except asyncio.CancelledError` branch settling AFTER a
  switch/re-watch has already cold-reset the ticker for a fresh engine) is now a silent no-op instead of
  clobbering the fresh watch's settled pair.
- `apps/backend/app/main.py` — a new small `_iso_utc(dt)` helper (matches
  `watch_manager._iso_utc` / `observation_contract._iso_utc` byte-for-byte, per the repo's per-module
  ISO-formatter convention) and `_watch_historical` now threads the already-parsed `start` / `end`
  datetimes into BOTH `manager.watch_with_provider(...)` (short window) and
  `manager.watch_with_progressive_historical(...)` (long/progressive window) as
  `window_start_utc` / `window_end_utc`. No other route behavior changed (verified by direct diff read).
- New test module `apps/backend/tests/test_tape_observation_lifecycle_feed.py` (30 tests, 0 failed) —
  covers TC-1 through TC-12 from the iteration spec:
  - TC-1..TC-5: fresh/historical/progressive/live descriptor shapes, main.py's `_watch_historical` route
    wiring end-to-end (a real `TestClient` POST, not just a manager-level call), re-watch mints a new
    `session_id` while recomputing `source_mode`/`data_feed` fresh (never carried over), session identity
    stable across repeated reads.
  - TC-6: a REAL async running-task-switch test — `FakeLiveProvider`'s `stream()` is a genuine async
    generator blocked on its own internal `asyncio.Queue.get()` (a real pending awaitable, not a timer);
    the test seeds one event, lets the feeder settle, then switches to a second provider for the same
    ticker and advances the loop until the old task's `CancelledError` handler actually runs, asserting
    `get_observation_source` still returns the NEW engine's pair. Its `test_counterexample_*` monkeypatches
    `_settle` back to the naive pre-fix version and proves the exact clobber reproduces.
  - TC-7/TC-8: every one of the seven `lifecycle.stream_status` values plus `watch_stopped` is exercised
    as a distinguishable, named test (`connecting`, `waiting`, `live`, `stale` with zero events, `stale`
    after events retaining `tape_state`/`confidence` exactly, `paused` retaining settled time, `closed`
    with `end_reason="stream_closed"`, `watch_stopped` returning `None`, `failed` with `end_reason=None`
    and zero fabricated events), plus a counter-example proving a nulled `tape_state`/`confidence` fails.
  - TC-9/TC-10: `(data_feed, availability_basis)` pairs pairwise distinct across sim/historical/live, plus
    dataset-manifest feed-owner agreement over every fixture under `tests/fixtures/datasets_j03/`, each
    with a counter-example.
  - TC-11: two AST guards — no second scenario-prefix parser in `watch_manager.py`/`main.py` outside
    `data_feed_for_scenario`, and no `session_id`/`session_started_at_utc` reference anywhere under
    `app/engine/*.py` — each with a counter-example fixture proving the scan is non-vacuous.
  - TC-12: a fully-built live `TapeObservation` dict scanned case-insensitively for the five
    actionability tokens (`READY`, `NO_TRADE`, `NO_VERDICT`, `trade_allowed`, `PENDING_CONDITION`) finds
    zero matches, with a counter-example proving the scan catches an injected token.
- `apps/backend/tests/test_tape_observation_time.py` — updated 8 tuple-unpacking call sites for the
  widened `get_observation_source` return (3-tuple → 4-tuple: `snapshot, settled_at_utc, end_reason` →
  `snapshot, settled_at_utc, end_reason, _descriptor`). No test added, removed, or logically changed
  (still exactly 33 tests, all passing) — a mechanical consequence of iter-3's signature change, not new
  behavior.

## Files Changed

- `apps/backend/app/watch_manager.py` (+128/-6) — `SourceDescriptor` dataclass, `_record_source`, all
  four `watch*` constructors record the descriptor, `get_observation_source` returns it, `_settle`
  identity check.
- `apps/backend/app/main.py` (+23/-2) — new `_iso_utc` helper; `_watch_historical` threads
  `window_start_utc`/`window_end_utc` into both historical watch call sites (its only two callers in the
  codebase, confirmed by grep).
- `apps/backend/tests/test_tape_observation_lifecycle_feed.py` (new, 675 lines, 30 tests) — TC-1..TC-12
  plus their named `test_counterexample_*` tests.
- `apps/backend/tests/test_tape_observation_time.py` (+13/-13) — tuple-unpacking updated for the widened
  `get_observation_source` return shape only.

No change to `apps/backend/app/observation_contract.py`, `apps/backend/app/config.py`, or any frontend
file — all out of scope per the iteration spec and confirmed untouched by `git status`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **4031 passed, 8 skipped, 0 failed** (4039 collected; exit code 0) — exactly iter-2's baseline
(4001 passed / 8 skipped / 0 failed) plus this iteration's 30 new tests, all passing, 0 regressions. The
venv's pytest (9.1.1) prints no final "N passed" summary line, so this was tallied by counting `-q`
progress characters (`.`=4031, `s`=8, `F`=0, `E`=0) directly from the captured output, per the iter-0
lessons entry.

Also run individually before the full-suite pass:
- `tests/test_tape_observation_lifecycle_feed.py` — 30 passed, 0 failed (all tests, including every
  `test_counterexample_*`).
- `tests/test_tape_observation_time.py`, `tests/test_stream_lifecycle.py`, `tests/test_feed_basis.py`,
  `tests/test_watch_manager.py`, `tests/test_tape_observation_projection.py` (combined; the guard-listed
  modules plus the directly-touched-by-signature-change module) — 108 passed, 0 failed. Confirms
  `test_stream_lifecycle.py`, `test_feed_basis.py`, and `test_watch_manager.py` pass unedited (git status
  shows no changes to these three files) and green.
- `Config.config_fingerprint()` — confirmed `08e471b10130e1e2` (unchanged from the pinned value).
- `cd apps/frontend && npx tsc --noEmit` — 0 errors (exit code 0; no frontend file touched, as expected).

## Manual verification (live backend)

Started the backend via `scripts/start-backend.sh` (bound port 8301) and exercised the touched
watch-creation/cancellation code paths end-to-end over real HTTP (not mocked):

- `POST /watch/SIM-BIDABS` (`{"mode":"sim"}`) → `{"status":"watching"}`; `GET /tape/SIM-BIDABS/state`
  shortly after shows `stream_status: "live"`.
- `POST /watch/SIM-BIDABS/pause` → `stream_status: "paused"`, `paused: true`, `tape_state`/`confidence`
  unchanged from the live read.
- `POST /watch/SIM-BIDABS/resume` → `stream_status: "live"` again.
- `DELETE /watch/SIM-BIDABS` → `{"status":"stopped"}`; `GET /tape/SIM-BIDABS/state` then 404.
- `GET /tape/SIM-BIDABS/observation` → 404 at every point in the sequence (the route does not exist until
  iteration 5 — expected, correct, not a defect per the phase spec).

This confirms the Watch → Pause → Resume → Stop regression path (the DoD's required smoke check and
TC-16) behaves exactly as before at the HTTP layer, ahead of the downstream browser-qa pass. The backend
process was killed afterward (`pkill -f "uvicorn main:app"`); confirmed no uvicorn process remains.

## Definition of Done — verification against the spec

- [x] Every `WatchManager` `watch*` constructor records the descriptor at creation, exposed by
  `get_observation_source(ticker)` alongside the settled pair, no re-fetch — verified by direct code
  read and TC-1/TC-2/TC-3 passing.
- [x] `_settle` never overwrites a ticker's settled pair with a stale/superseded engine's write; TC-6's
  real running-task-switch test passes, and its `test_counterexample_*` (reverting the check) reproduces
  the clobber.
- [x] `test_tape_observation_lifecycle_feed.py` passes with 0 failures; every `test_counterexample_*` is
  present and passes (30/30).
- [x] Full backend suite green at 4031 passed / 8 skipped / 0 failed — iter-2's baseline (4001/8/0) plus
  this iteration's 30 new tests. `test_stream_lifecycle.py`, `test_feed_basis.py`, `test_watch_manager.py`
  pass unedited (confirmed via `git status`, no diff on those three files).
- [x] `Config.config_fingerprint()` unchanged (`08e471b10130e1e2`); `tsc --noEmit` reports 0 errors.
- [x] Zero visible product change confirmed at the HTTP/backend layer (see Manual verification above);
  full browser-qa (the actual `/`, `/structure`, `/desk` render checks) is the downstream browser-qa-agent
  step, not run by this developer pass.
- [ ] Anti-goal scan-report CLEAN — this is the downstream goal-mode diff-scan step; spot checks run here
  (actionability-token scan in TC-12, no `Workstation`/`Trendora`/`TenSteps` reference, `config.py`
  untouched, no frontend file touched) all came back clean.
- [x] Dev handoff written at this path.

## Known Issues

- None found in the implementation itself. On direct inspection the code matches the iteration spec's
  IN SCOPE list, OUT OF SCOPE exclusions, and Test-first contract (TC-1 through TC-12) exactly — no gaps,
  no workarounds.
- J-03's overall journey status is expected to remain `failing` or move to `partial` (not fully
  `passing`) this iteration, per the phase spec's own note: its Acceptance requires the served
  `/tape/{ticker}/observation` JSON, which does not exist until iteration 5 (Binding Execution Order step
  5). This is the expected, correct signal, not a regression — confirmed the route still 404s in the
  manual verification above.
- Browser QA and the goal-mode anti-goal diff scan are downstream pipeline steps and were not run in full
  by this developer pass; the manual live-backend HTTP check above exercises the same Watch → Pause →
  Resume → Stop surface the browser-qa-agent will check, and the code-level spot checks for the
  actionability-token/external-system-reference/Config-field anti-goals all came back clean.
