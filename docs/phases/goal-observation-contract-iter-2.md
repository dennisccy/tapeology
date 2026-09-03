# Goal Iteration 2 — The manager-held atomic settled pair and the time law (J-02, block 2 of the Binding Execution Order)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** observation-contract
- **Iteration:** 2
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-02
- **Required-still-passing journeys:** none (0 journeys are recorded passing this session as of
  iter-1: 4 failing, 2 partial — J-01, J-06. This iteration is backend-only and touches zero
  served/UI surface, so there is nothing `passing` to regress. Because it edits `watch_manager.py`'s
  feeder and pause/resume paths, the foundation invariants that matter here are re-verified as TC
  scenarios below instead: the full backend suite including `test_stream_lifecycle.py` and
  `test_watch_manager.py` (both on the guard no-weaken list), `config_fingerprint =
  08e471b10130e1e2`, `tsc --noEmit` 0 errors, and a Cockpit Watch/Pause/Resume/Stop smoke check.)
- **Anti-goal reminders:**
  - **Rail 3 (frozen foundations):** "the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside them, never a mutation of them."
  - **Rail 6 (single source of truth):** "each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations."
  - **Rail 7 (deterministic and seeded):** "every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact."
  - **Era-specific:** "No `available_at_utc` that is not a manager-measured settled instant; no `observed_at + delivery_lag` reconstruction; no availability before the underlying event or state existed."
  - **Era-specific:** "No route that snapshots an engine for the observation; the atomic manager read is the only source."
  - **Era-specific:** "No mandatory journey or test that requires Alpaca, the network, credentials or market hours."
  - **Era-specific:** "No weakening of any existing guard: `test_no_execution_path.py`, `test_feed_basis.py`, `test_copy_discipline.py`, `test_profile_equivalence.py`, `test_fingerprint_epoch_retirement.py`, `test_mcp_server.py`, `test_stream_lifecycle.py`, `test_observer_equivalence.py` and `test_epoch_anchor.py` stay green and unedited except for additive registrations."

## GOAL

Give `WatchManager` a genuinely atomic, per-ticker settled read — the manager-held `(EngineSnapshot,
settled_at)` pair plus `get_observation_source(ticker)` — and prove the three time concepts of
Constitution §2 (`observed_at_utc`, `available_at_utc`, `availability_basis`) are honest and atomic
against real sim, historical-fixture, dataset-replay and live-fixture data — step 2 of the Binding
Execution Order — with zero visible product change.

## BACKGROUND

The evaluator's iter-1 next-step recommendation is explicit and binding: "Build the time block next —
J-02 ... the watch manager's single atomic read of the settled pair, the three time fields,
`availability_basis`, and the new test file `tests/test_tape_observation_time.py`. Do not move the web
address earlier ...; it is step 5." This spec is exactly that block.

Direct repo inspection shows the time-LAW arithmetic itself is already correct and complete inside
`apps/backend/app/observation_contract.py` from iteration 1: `_observed_at_utc` (pure
`epoch_anchor + timestamp` projection, both null clauses) and `_availability` (the §2 table keyed off
`source_mode`, live basis = the caller's `settled_at_utc` verbatim, historical/dataset_replay = null +
`historical_arrival_unknown`) are both already implemented and need no change. What is genuinely
missing, confirmed absent by `grep`, is the manager-side machinery that makes `settled_at_utc` real: no
per-ticker settled pair exists in `apps/backend/app/watch_manager.py`, `get_observation_source` is not
defined, and `tests/test_tape_observation_time.py` does not exist. This narrows the iteration to
`watch_manager.py` plus one new test module — no change to `observation_contract.py` is in scope.

Per the iter-0 lessons entry (applies to iterations 1-4): a flat journey table is the expected, correct
signal here — J-02's Acceptance is a conjunction that includes the served JSON at
`/tape/{ticker}/observation`, which does not exist until iteration 5. Do not move the route earlier.
The iter-1 lessons entry flagged `availability_basis` as a value that "most likely" would hit the same
import-guard tension iter-1 resolved for `TAPE_STATE_VOCABULARY` (duplicate + test-side cross-check
instead of importing a forbidden module). Checked directly: it does not recur here —
`_AVAILABILITY_BASIS_BY_SOURCE_MODE` is already singly owned inside `observation_contract.py` itself and
`WatchManager` is not subject to the classifier/feature recompute guard (that guard applies only to
`observation_contract.py`), so no cross-module duplication is needed this iteration.

## IN SCOPE

### Backend
- [ ] `WatchManager`: add a manager-held, per-ticker atomic settled pair — `(EngineSnapshot,
      settled_at_epoch)` — written by exactly ONE helper, called after every `process_event` in every
      feeder path (`_feed`, `_feed_paced`, `_replay_events`, `_feed_progressive`, `_feed_live`) and after
      every lifecycle-only status mutation that carries no new event (`pause()`, `resume()`, the stale
      flip in `_feed_live`, and the `failed`/`closed` flips in each feeder's except/finally blocks). A
      lifecycle-only mutation carries the PREVIOUS settled time forward unchanged (Constitution §2: "no
      new event, same availability") — it never re-stamps `settled_at_epoch` to "now". `stop()` removes
      the engine as today (no settled-pair bookkeeping needed for a ticker that will 404).
- [ ] `WatchManager.get_observation_source(ticker)` — returns, from the ONE atomic settled pair, the
      settled `EngineSnapshot`, the pinned-ISO `settled_at_utc` (or `None` before any event has settled),
      and `end_reason`; returns `None` for a ticker not currently watched (mirrors the existing
      `get()`/`pause()`/`resume()` "no fabricated engine" idiom — never synthesizes a pair). The exact
      return shape (tuple/dataclass) is an implementation choice; iteration 3 adds the source/session
      descriptor fields onto this same read without re-fetching the pair.
- [ ] A source scan/AST test proving `app/engine/*.py` contains no `time.time`, `datetime.now`,
      `datetime.utcnow`, `random.*` call or git subprocess reference (Constitution §2/Constraints:
      "`app/engine/` stays free of wall-clock reads, randomness, git access and session identity").
- [ ] Create `apps/backend/tests/test_tape_observation_time.py` covering, each as a named test (Required
      Trap Coverage items 15-24): `observed_at_utc` equals the latest processed event for the sim
      provider, `HistoricalProvider` over the committed PG SIP fixture
      (`tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json`), `DatasetStore.replay` over a
      committed `datasets_j03` fixture, and `LiveProvider` over merged fixture records; both
      `observed_at_utc` null clauses; historical/dataset_replay `available_at_utc = null` +
      `historical_arrival_unknown` with a `test_counterexample_*` that fails when event time is copied
      into `available_at_utc`; live `available_at_utc == settled_at_utc` from a monkeypatched clock in
      `watch_manager`, with a `test_counterexample_*` that fails when the builder derives
      `observed + delivery_lag`; `settled − observed` cross-checked against `delivery_lag_seconds` on a
      controlled clock (telemetry only, never a source of truth); the atomic-read interleaving test
      (event N settled, event N+1 processed but not yet settled: the read still pairs snapshot N with
      settled N; after settling N+1 it pairs N+1 with settled N+1; a naive
      `(engine.snapshot(), last_settled_at)` read is shown to mis-pair); the `app/engine/` clock/git scan
      above; `availability_basis` exhaustive per `source_mode` (all four values distinct, an unrecognized
      mode raises); the pinned ISO function round-trips to the microsecond; two independent
      `DatasetStore.replay` reruns over the same fixture yield identical `observation_hash` at every
      captured tick.

### Frontend (if applicable)
None — zero frontend files touched this iteration (goal Product Shape: "No page, panel, link or
component is added or modified").

### New user-facing capability
None. `get_observation_source` is an in-process manager method with no served, watched or visible
surface.

### New information displayed
None — nothing is served by any endpoint, page or MCP tool yet (route is iteration 5).

### New user actions
None. The existing Watch / Pause / Resume / Stop controls on `/` are exercised only as regression
coverage for the touched `pause()`/`resume()` code paths — no new control, no behavior change visible
to a user.

### UI surface changes
None — Cockpit `/`, `/structure`, `/desk` are untouched.

### Product surface delta
None visible. The only artifacts of this iteration are changes inside `apps/backend/app/watch_manager.py`
plus one new test module; a user (or browser-qa) sees the exact same product as after iter-1.

### Blueprint conformance
No new surfaces. `runs/goal-session-observation-contract/state/blueprint.md`'s Information Architecture
is unchanged (no page, no nav entry). This iteration builds the manager-side half of the
"Provenance / source / lifecycle metadata" Data Contract row's computing module
(`WatchManager.get_observation_source`); the row's registered future computing-module/serving-endpoint
pairing does not change, and the blueprint's status note is updated (not a new registration).

### Data-contract additions
None. `get_observation_source` exists as an in-process manager method only this iteration — it is not
served by any endpoint, so no NEW DISPLAYED value exists to register. `blueprint.md`'s existing
Provenance/source/lifecycle-metadata row already names `WatchManager.get_observation_source` as the
eventual (partial) computing module; this iteration builds the atomic-settled-pair half of it (settled
snapshot, `settled_at_utc`, `end_reason`) without changing the registered future serving endpoint
(`GET /tape/{ticker}/observation`, still not live until iteration 5). Source/session descriptor fields
on the same row remain iteration 3's work.

## OUT OF SCOPE

- Any change to `apps/backend/app/observation_contract.py` or `build_tape_observation` — the time-law
  arithmetic they already contain (from iteration 1) is correct and needs no edit this iteration.
- The source/session descriptor's real population (mode/scenario/window/session id/session start/
  profile id) and feed-owner agreement across fixture datasets — Binding Execution Order step 3
  (iteration 3, J-03).
- `tests/test_tape_observation_lifecycle_feed.py`, `_path_equivalence.py`, `_route.py`, `_guards.py` —
  later iterations' own modules; this iteration ships only `test_tape_observation_time.py`.
- The `GET /tape/{ticker}/observation` route and any wiring into `apps/backend/app/main.py` — step 5
  (iteration 5, J-05). No route exists after this iteration; `/tape/SIM-BIDABS/observation` still 404s.
- Any MCP change.
- Any `Config` field addition (the era adds zero; module-level constants/helpers only).
- Any frontend file, page, panel or nav change.
- Real-provider (Alpaca) code paths — all fixtures and harnesses are local and deterministic
  (`HistoricalProvider`/`LiveProvider`/`DatasetStore.replay` over committed fixtures, sim provider, a
  monkeypatched clock).

## DEFINITION OF DONE

- [ ] `WatchManager` holds a per-ticker atomic settled pair, written by one helper reachable from every
      feeder path and from `pause()`/`resume()`; a lifecycle-only mutation carries the previous settled
      time forward unchanged.
- [ ] `WatchManager.get_observation_source(ticker)` returns the settled snapshot, `settled_at_utc` and
      `end_reason` from that one atomic read, and `None` for an unwatched ticker.
- [ ] `apps/backend/tests/test_tape_observation_time.py` passes with 0 failures, and every
      `test_counterexample_*` test it ships is present and passes.
- [ ] Full backend suite still green — no fewer than iter-1's baseline of 3968 passed / 8 skipped / 0
      failed, plus this iteration's new tests, 0 failed. `test_stream_lifecycle.py` and
      `test_watch_manager.py` (guard-list / directly-touched-surface files) pass unedited except for any
      additive registration.
- [ ] `Config.config_fingerprint()` unchanged (`08e471b10130e1e2`); `cd apps/frontend && npx tsc
      --noEmit` reports 0 errors (unaffected — no frontend file touched).
- [ ] Browser-qa confirms zero visible product change: `/`, `/structure`, `/desk` render exactly as at
      iter-1; `/tape/SIM-BIDABS/observation` still 404s (route not yet built — expected, correct, not a
      defect); Watch / Pause / Resume / Stop on `/` behave exactly as before (status dot transitions
      `live` → `paused` → `live`, then stops).
- [ ] No anti-goal violation introduced (scan-report CLEAN).
- [ ] Dev handoff written at `docs/handoffs/goal-observation-contract-iter-2-dev.md`.

Note on J-02's overall journey status: this iteration cannot make J-02 fully pass — its Acceptance
requires the served JSON at `/tape/SIM-BIDABS/observation`, which needs the route (iteration 5). Expect
the evaluator to record J-02 as still `failing` or move it to `partial` on the strength of the passing
`test_tape_observation_time.py` module, per the same convention applied to J-01 at iter-1; this is
correct, not a regression.

## TESTING REQUIREMENTS

- Browser: no journey's Acceptance can be newly satisfied this iteration (route absent). Confirm
  `/tape/SIM-BIDABS/observation` still answers "Not Found" after a live Sim watch; confirm `/structure`
  and `/desk` render unchanged; confirm Watch → Pause → Resume → Stop on `/` still transition the status
  dot correctly (regression smoke on the touched `watch_manager.py` code paths).
- Unit/integration: `apps/backend/tests/test_tape_observation_time.py` (new) — see TC-1..TC-17 below. No
  integration test needs a running uvicorn server or network access.
- Error cases: an unrecognized `source_mode` passed to the availability law raises; `get_observation_source`
  on an unwatched ticker returns `None` (never a fabricated pair); a naive non-atomic read is shown to
  mis-pair under interleaving (the counter-example that proves the atomic helper is necessary, not
  decorative).

Test-first contract:

- TC-1: given `SIM-BIDABS` watched live with at least one event processed, when
  `WatchManager.get_observation_source("SIM-BIDABS")` is called, then it returns the settled
  `EngineSnapshot` paired with the `settled_at_utc` stamped by that SAME `process_event` call, under a
  deterministic interleaving harness with a monkeypatched clock in `watch_manager`.
- TC-2: given event N has settled and event N+1 has been `process_event`-applied but the settle helper
  has not yet run for it, when `get_observation_source(ticker)` is called, then the returned pair shows
  snapshot N paired with settled-time N (never N+1 with settled-time N, nor the reverse); after the
  settle helper runs for N+1, the pair shows snapshot N+1 with settled-time N+1.
- TC-3: given the same interleaving fixture, when a NAIVE read
  `(engine.snapshot(), <last recorded settled_at>)` is constructed instead of the atomic helper, then
  the test demonstrates it mis-pairs snapshot N+1 with settled-time N — the counter-example proving the
  atomic read is required, not decorative.
- TC-4: given a watch with one settled event, when `pause()` then `get_observation_source(ticker)` is
  called, then `settled_at_utc` is identical to its pre-pause value (carried forward, never re-stamped
  to "now").
- TC-5: given a sim-provider snapshot, a `HistoricalProvider` snapshot over the committed PG SIP fixture,
  a `DatasetStore.replay` tick over the committed `datasets_j03` fixture, and a `LiveProvider` snapshot
  over merged fixture records, when `build_tape_observation(...)` is called for each, then
  `observed_at_utc` equals `iso(epoch_anchor + timestamp)` of that snapshot's latest processed event in
  all four cases.
- TC-6: given a snapshot with `epoch_anchor=None`, and separately a snapshot with `epoch_anchor` set but
  zero events processed (`bid`/`ask`/`last` all null), when `build_tape_observation(...)` is called, then
  `observed_at_utc` is `null` in both cases.
- TC-7: given `source_mode="historical"` and separately `source_mode="dataset_replay"`, when
  `build_tape_observation(...)` is called with any non-null `settled_at_utc`, then `available_at_utc` is
  `null` and `availability_basis` is `"historical_arrival_unknown"` in both cases; `test_counterexample_*`
  shows that copying `observed_at_utc` into `available_at_utc` is caught as a failing assertion.
- TC-8: given `source_mode="live"` and a `settled_at_utc` produced by the monkeypatched `watch_manager`
  clock, when `build_tape_observation(...)` is called, then `available_at_utc` equals `settled_at_utc`
  exactly; `test_counterexample_*` shows that deriving it as `observed_at_utc + delivery_lag_seconds` is
  caught as a failing assertion.
- TC-9: given a controlled clock in `watch_manager` and a live-mode snapshot with a known
  `delivery_lag_seconds`, when `settled_at_utc − observed_at_utc` is computed, then it agrees with
  `delivery_lag_seconds` within the clock's resolution (telemetry cross-check only).
- TC-10: given each of the four `source_mode` values (`live`, `historical`, `dataset_replay`, `sim`),
  when `build_tape_observation(...)` is called, then `availability_basis` is defined and distinct for
  each; an unrecognized `source_mode` raises.
- TC-11: given a UTC instant with non-zero microseconds, when it is formatted by the pinned ISO function
  and re-parsed, then the round-tripped value equals the original to the microsecond.
- TC-12: given `DatasetStore.replay` over the committed `datasets_j03` fixture run twice independently,
  when `build_tape_observation(...)` is called at every captured tick in both runs, then
  `observation_hash` is identical tick-for-tick across the two runs.
- TC-13: given `apps/backend/app/engine/*.py`'s source, when the clock/randomness/git source scan runs,
  then it asserts zero occurrences of `time.time`, `datetime.now`, `datetime.utcnow` or `random.` across
  every module and zero git subprocess references; `test_counterexample_*` inserts a `time.time()` call
  into a throwaway fixture module and asserts the scan fails on it.
- TC-14: given `SIM-BIDABS` watched live via the Cockpit, when `/tape/SIM-BIDABS/observation` is
  requested over HTTP (browser-qa), then the response is still a 404 "Not Found" body (route lands
  iteration 5 — expected), and Pause / Resume / Stop on `/` behave exactly as before.
- TC-15: given the full backend suite, when `cd apps/backend && .venv/bin/python -m pytest tests/ -q` is
  run, then the pass count is >= 3968 (iter-1 baseline) plus the count of tests newly added in
  `test_tape_observation_time.py`, with 0 failed, and `Config.config_fingerprint()` still returns
  `08e471b10130e1e2`.
- TC-16: given `cd apps/frontend && npx tsc --noEmit` is run after this iteration's changes, then it
  reports 0 errors (no frontend file was touched).
- TC-17: given the goal-mode scan step over the diff restricted to `apps/`, `docs/`, `scripts/`, when it
  runs, then the report is CLEAN with zero secret/dependency/license findings.

## NOTES

- Applying the iter-0 lessons entry (applies to iterations 1-4): a flat journey table this iteration
  (J-02 not fully unlocked) is the expected, correct signal — do not read it as a stall and do not move
  the route earlier. Score this iteration on `test_tape_observation_time.py`'s pass/fail and the honest
  absence of the route, not on J-02's merged verdict alone.
- Applying the iter-1 lessons entry: it flagged `availability_basis` as a candidate for the same
  guard-forbidden-import tension iter-1 hit with `TAPE_STATE_VOCABULARY`. Checked directly this
  iteration: it does not recur — `_AVAILABILITY_BASIS_BY_SOURCE_MODE` is already singly owned inside
  `observation_contract.py`, and `WatchManager` (unlike `observation_contract.py`) carries no
  classifier/feature import guard, so nothing needs duplicating or cross-checking here.
- The pytest venv (9.1.1) prints no final "N passed" summary line; tally via `-q` progress characters or
  `--collect-only -q` per-file counts, per the iter-0 lessons entry — do not grep for a summary line that
  never appears.
- Assumption logged to `runs/goal-session-observation-contract/state/assumptions.md` (iter-2): this spec
  reads `get_observation_source`'s scope as the atomic settled pair + `settled_at_utc` + `end_reason`
  only, deferring the source/session descriptor fields Key Capability 3 also names to iteration 3 (the
  Binding Execution Order's own step split) — the alternative reading (build the full descriptor now) is
  explicitly out of scope this iteration to keep the change set to one module plus one test file.
