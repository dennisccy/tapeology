# Goal Iteration 3 — Source/session descriptor and lifecycle honesty (J-03, block 3 of the Binding Execution Order)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** observation-contract
- **Iteration:** 3
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-03
- **Required-still-passing journeys:** none (0 journeys are recorded passing this session as of
  iter-2: 3 failing — J-03, J-04, J-05 — and 3 partial — J-01, J-02, J-06. This iteration is
  backend-only and touches zero served/UI surface, so there is nothing `passing` to regress. Because
  it edits `watch_manager.py`'s watch-creation and cancellation paths and `main.py`'s historical-watch
  call sites, the foundation invariants that matter here are re-verified as TC scenarios below instead:
  the full backend suite including `test_stream_lifecycle.py`, `test_feed_basis.py` and
  `test_watch_manager.py` (all on the guard no-weaken / directly-touched-surface list),
  `config_fingerprint = 08e471b10130e1e2`, `tsc --noEmit` 0 errors, and a Cockpit
  Watch/Pause/Resume/Stop smoke check).
- **Anti-goal reminders:**
  - **Rail 3 (frozen foundations):** "the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside them, never a mutation of them."
  - **Rail 6 (single source of truth):** "each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations."
  - **Rail 7 (deterministic and seeded):** "every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact."
  - **Era-specific:** "No pooling, equating or silent conversion between `sim`, `iex` and `sip`."
  - **Era-specific:** "No field, token or copy that reads as a trading action, readiness or verdict (READY, NO_TRADE, NO_VERDICT, `trade_allowed`, PENDING_CONDITION or any equivalent) anywhere in the artifact, the module, its tests or the spec's served surface."
  - **Era-specific:** "No recomputation of any tape feature, state, confidence, freshness or feed basis outside the engine and the one existing `data_feed_for_scenario`; no second scenario-prefix parser."
  - **Era-specific:** "No mandatory journey or test that requires Alpaca, the network, credentials or market hours."
  - **Era-specific:** "No weakening of any existing guard: `test_no_execution_path.py`, `test_feed_basis.py`, `test_copy_discipline.py`, `test_profile_equivalence.py`, `test_fingerprint_epoch_retirement.py`, `test_mcp_server.py`, `test_stream_lifecycle.py`, `test_observer_equivalence.py` and `test_epoch_anchor.py` stay green and unedited except for additive registrations."

## GOAL

Give every managed watch (sim, live, historical) a real, manager-recorded source/session descriptor
(mode, feed, window, session identity, profile) and prove the seven lifecycle statuses stay honest and
the three feed bases stay distinct — step 3 of the Binding Execution Order — with zero visible product
change.

## BACKGROUND

The evaluator's iter-2 next-step recommendation is explicit and binding: build J-03 — "give each watch a
real source and session description (mode, scenario, window, session id, session start, data feed), keep
the lifecycle wording honest across the seven statuses, and add
`apps/backend/tests/test_tape_observation_lifecycle_feed.py`" — and fold in the reviewer's carried-forward
MINOR finding first: `_settle` (`apps/backend/app/watch_manager.py:320`) keys its write off
`engine.snapshot().ticker` alone, with no check that `engine` is still the CURRENTLY REGISTERED engine
for that ticker. Direct inspection confirms the exact race: every feeder's `except asyncio.CancelledError`
branch (for example `_feed_live`'s, `apps/backend/app/watch_manager.py:774-777`) calls
`self._settle(engine, new_event=False)` on the OLD engine object, and that branch only actually runs when
the cancelled task next reaches an `await` — which can happen AFTER a switch/re-watch has already reset
`self._settled[ticker]` for the fresh engine (every `watch*` constructor does `self.stop(ticker)` then
immediately `self._settled[ticker] = (new_engine.snapshot(), None)`). The late write silently clobbers the
new watch's pair with the old engine's stale snapshot. The all-sync no-feeder harness in
`test_stream_lifecycle.py` cannot exercise this because nothing is ever genuinely still in flight when a
switch happens; this iteration adds a real async test that keeps a feeder mid-flight across the switch.

Direct repo inspection also confirms `build_tape_observation` (iteration 1) already accepts every
descriptor field this iteration must populate as caller-resolved parameters (`source_mode`, `data_feed`,
`window_start_utc`, `window_end_utc`, `dataset_id`, `dataset_checksum`, `session_id`,
`session_started_at_utc`, `profile_id`) — no change to `observation_contract.py` is in scope. What is
genuinely missing is the manager-side machinery that resolves those values honestly: none of the four
`watch*` constructors in `watch_manager.py` record a source/session descriptor today, `main.py`'s
`_watch_historical` never threads its already-parsed `start`/`end` window into the manager, and
`data_feed_for_scenario` (the single existing feed-basis function, `apps/backend/app/research/feed_basis.py`)
is never called from the watch path. This narrows the iteration to `watch_manager.py` plus `main.py`'s two
historical call sites plus one new test module — no change to `observation_contract.py`.

Per the iter-0 lessons entry (applies through iteration 4): a flat journey table remains the expected
signal — J-03's Acceptance is a conjunction that includes the served JSON, which does not exist until
iteration 5. Do not move the route earlier. The iter-1 lessons entry flagged the import-guard tension
(a guard forbids importing what a contract needs the value of) as likely to recur for "lifecycle/feed-basis
vocabularies" at iteration 3. Checked directly: it does NOT recur here — `lifecycle.stream_status` and
`source.data_feed` are free-form pass-through strings from `EngineSnapshot`/`data_feed_for_scenario`, not
a closed vocabulary constant `observation_contract.py` itself must embed and cross-check (unlike
`TAPE_STATE_VOCABULARY` at iteration 1), so nothing needs duplicating this iteration.

## IN SCOPE

### Backend
- [ ] `WatchManager`: record a per-ticker source/session descriptor ONCE at each of the four `watch*`
      constructor call sites (the same "cold reset per fresh engine" pattern already used for
      `self._settled`) — `source_mode` (`"sim"` for `watch()`; `"historical"` for `watch_with_provider()`
      and `watch_with_progressive_historical()`; `"live"` for `watch_with_async_provider()`), `data_feed`
      (`data_feed_for_scenario(scenario, config)` — the one existing function), `window_start_utc` /
      `window_end_utc` (pinned-ISO parsed UTC window for the two historical constructors, `None`
      otherwise), `dataset_id` / `dataset_checksum` (`None` for every WatchManager-managed watch —
      `dataset_replay` is a distinct in-process path outside the manager), `session_id` (`uuid.uuid4().hex`
      minted fresh at construction — confirmed no existing per-watch identifier to reuse), and
      `session_started_at_utc` (pinned-ISO wall clock at construction). Include `profile_id =
      PROFILE_DEFAULT` as a constant field of the same descriptor (see NOTES assumption entry).
- [ ] `watch_with_provider(...)` and `watch_with_progressive_historical(...)`: add optional
      `window_start_utc: str | None = None, window_end_utc: str | None = None` parameters (backward
      compatible defaults) so the manager can record the real request window.
- [ ] `apps/backend/app/main.py`'s `_watch_historical`: thread the already-parsed `start`/`end` datetimes
      (pinned-ISO formatted) into `manager.watch_with_provider(...)` / `manager.watch_with_progressive_historical(...)`
      as the new `window_start_utc` / `window_end_utc` arguments. No other route change.
- [ ] `WatchManager.get_observation_source(ticker)`: extend its return to also carry the source/session
      descriptor recorded at watch creation, read from the SAME per-ticker state (no re-fetch, no second
      read of the settled pair). Exact return shape (tuple/dataclass) is an implementation choice, as
      iteration 2 already deferred.
- [ ] Fix the reviewer's carried-forward MINOR: `_settle` (`watch_manager.py:320`) must skip its write
      (silent no-op, no exception) whenever `self._engines.get(ticker) is not engine` — i.e. the engine
      calling `_settle` is no longer the currently-registered engine for that ticker (already stopped, or
      superseded by a switch/re-watch). This is the identity check the reviewer asked for before the
      route becomes the first production reader of `get_observation_source` at iteration 5.
- [ ] Create `apps/backend/tests/test_tape_observation_lifecycle_feed.py` covering, each as a named test
      (Required Trap Coverage items 25-31): a table-driven pass over all seven `lifecycle.stream_status`
      values using the existing `test_stream_lifecycle.py` harness (paced + live feeders), plus `paused`,
      natural `closed` (`end_reason="stream_closed"`), in-process `watch_stopped` (post-`stop()`,
      `get_observation_source` returns `None`), `failed` (`end_reason=None`), and live `waiting`/`stale`
      with zero events (both times null) — every status distinguishable from the artifact/return value
      alone; `tape_state`/`confidence` never nulled or rewritten by any lifecycle transition; feed-basis
      distinctness across `LiveProvider` (`iex` / `live_settled_wall_clock`), the committed PG SIP
      `HistoricalProvider` fixture (`sip` / `historical_arrival_unknown`) and sim (`sim` /
      `simulated_not_applicable`) — pairwise distinct, never pooled; dataset-manifest feed-owner agreement
      across every committed fixture dataset under `tests/fixtures/datasets_j03/`; an AST guard proving no
      second scenario-prefix parser exists outside `data_feed_for_scenario` and the manager descriptor;
      session identity present, stable across repeated reads of one watch, different across two successive
      watches of the same ticker, and an AST guard proving no `app/engine/*.py` module references
      `session_id` / `session_started_at_utc`; a scoped scan of one fully-built artifact dict for the fixed
      actionability-token list (`READY`, `NO_TRADE`, `NO_VERDICT`, `trade_allowed`, `PENDING_CONDITION`),
      case-insensitively, finding zero matches.
- [ ] A REAL async running-task-switch test (not the existing sync no-feeder harness): start a live/paced
      watch whose feeder is genuinely still mid-flight (an async provider blocked on an unresolved
      awaitable), trigger a switch/re-watch for the SAME ticker, advance the event loop enough to run the
      old feeder's cancellation handler, and assert `get_observation_source(ticker)` returns the NEW
      engine's settled pair and descriptor — never the old engine's stale write.
- [ ] Each item above ships a named `test_counterexample_*` proving it can fail (nulling `tape_state` on
      `stale`; equating `iex`/`sip`; reusing a `session_id` across two watches; reverting the `_settle`
      identity check to reproduce the clobber; injecting an actionability token).

### Frontend (if applicable)
None — zero frontend files touched this iteration (goal Product Shape: "No page, panel, link or
component is added or modified").

### New user-facing capability
None. The source/session descriptor and the `_settle` identity fix are in-process manager state with no
served, watched or visible surface.

### New information displayed
None — nothing is served by any endpoint, page or MCP tool yet (route is iteration 5).

### New user actions
None. The existing Watch / Pause / Resume / Stop controls on `/` are exercised only as regression
coverage for the touched watch-creation and cancellation code paths — no new control, no visible
behavior change.

### UI surface changes
None — Cockpit `/`, `/structure`, `/desk` are untouched.

### Product surface delta
None visible. The only artifacts of this iteration are changes inside `apps/backend/app/watch_manager.py`
and `apps/backend/app/main.py`'s two historical call sites, plus one new test module; a user (or
browser-qa) sees the exact same product as after iter-2.

### Blueprint conformance
No new surfaces. `runs/goal-session-observation-contract/state/blueprint.md`'s Information Architecture
is unchanged (no page, no nav entry). This iteration completes the "Provenance / source / lifecycle
metadata" Data Contract row's computing module (`WatchManager.get_observation_source`) with the
source/session descriptor half; the row's registered future computing-module/serving-endpoint pairing
does not change. `blueprint.md` has been updated in place (row + progress note) to reflect iter-3's
completion — no nav-skeleton change, so no re-approval request was filed.

### Data-contract additions
None. The source/session descriptor exists as in-process `WatchManager` state only this iteration — it
is not served by any endpoint, so no NEW displayed value exists to register. `blueprint.md`'s existing
Provenance/source/lifecycle-metadata row already named `WatchManager.get_observation_source` as the
eventual (partial) computing module; this iteration completes it (still unserved — the route lands
iteration 5) without changing the registered future serving endpoint (`GET /tape/{ticker}/observation`).

## OUT OF SCOPE

- The route `/tape/{ticker}/observation` and any wiring into `apps/backend/app/main.py` beyond threading
  `window_start_utc`/`window_end_utc` into the two historical watch call sites — the route itself is
  Binding Execution Order step 5 (iteration 5, J-05); it still 404s for every ticker after this iteration.
- Any change to `apps/backend/app/observation_contract.py` or `build_tape_observation` — the descriptor
  parameters it already accepts (from iteration 1) need no change; this iteration only makes their VALUES
  genuinely correct at the source.
- `tests/test_tape_observation_path_equivalence.py`, `_route.py`, `_guards.py` — later iterations' own
  modules (4, 5, 6); this iteration ships only `test_tape_observation_lifecycle_feed.py`.
- The full copy-discipline / external-system-reference / English-only / real-provider-isolation /
  mutator-call-site guard MODULE (`test_tape_observation_guards.py`, iteration 6, J-06). This iteration's
  actionability-token check is a scoped grep serving J-03's own acceptance only.
- `dataset_id`/`dataset_checksum` population for `dataset_replay` — out of the WatchManager's descriptor
  scope; `dataset_replay` is a distinct in-process caller identified by its own manifest, never a managed
  watch.
- Any `Config` field addition (the era adds zero; module-level constants/helpers only).
- Any frontend file, page, panel or nav change.
- Real-provider (Alpaca) network calls — `LiveProvider` is exercised only over committed fixture/merged
  records and monkeypatched/fake harnesses, never a live vendor connection.

## DEFINITION OF DONE

- [ ] Every `WatchManager` `watch*` constructor records a per-ticker source/session descriptor
      (`source_mode`, `data_feed`, window bounds, `dataset_id`/`dataset_checksum=None`, `session_id`,
      `session_started_at_utc`, `profile_id`) at creation, exposed by `get_observation_source(ticker)`
      alongside the existing atomic settled pair, with no re-fetch.
- [ ] `_settle` never overwrites a ticker's settled pair with a stale/superseded engine's write (identity
      check in place); the real running-task-switch test proves the previously-reproducible clobber no
      longer occurs, and its `test_counterexample_*` (reverting the check) shows the clobber reproduces.
- [ ] `apps/backend/tests/test_tape_observation_lifecycle_feed.py` passes with 0 failures, and every
      `test_counterexample_*` test it ships is present and passes.
- [ ] Full backend suite still green — no fewer than iter-2's baseline of 4001 passed / 8 skipped / 0
      failed, plus this iteration's new tests, 0 failed. `test_stream_lifecycle.py`, `test_feed_basis.py`
      and `test_watch_manager.py` pass unedited except for any additive registration.
- [ ] `Config.config_fingerprint()` unchanged (`08e471b10130e1e2`); `cd apps/frontend && npx tsc
      --noEmit` reports 0 errors (unaffected — no frontend file touched).
- [ ] Browser-qa confirms zero visible product change: `/`, `/structure`, `/desk` render exactly as at
      iter-2; `/tape/SIM-BIDABS/observation` still 404s (route not yet built — expected, correct, not a
      defect); Watch / Pause / Resume / Stop on `/` behave exactly as before.
- [ ] No anti-goal violation introduced (scan-report CLEAN).
- [ ] Dev handoff written at `docs/handoffs/goal-observation-contract-iter-3-dev.md`.

Note on J-03's overall journey status: this iteration cannot make J-03 fully pass — its Acceptance
requires the served JSON at `/tape/SIM-BIDABS/observation`, which needs the route (iteration 5). Expect
the evaluator to record J-03 as still `failing` or move it to `partial` on the strength of the passing
`test_tape_observation_lifecycle_feed.py` module, per the same convention applied to J-01/J-02; this is
correct, not a regression.

## TESTING REQUIREMENTS

- Browser: no journey's Acceptance can be newly satisfied this iteration (route absent). Confirm
  `/tape/SIM-BIDABS/observation` still answers "Not Found" after a live Sim watch; confirm `/structure`
  and `/desk` render unchanged; confirm Watch → Pause → Resume → Stop on `/` still transition the status
  dot through live → paused → live → closed in that order (regression smoke on the touched `watch_manager.py` code paths).
- Unit/integration: `apps/backend/tests/test_tape_observation_lifecycle_feed.py` (new) — see TC-1..TC-16
  below. No integration test needs a running uvicorn server or network access.
- Error cases: an unrecognized lifecycle status is never produced by any code path (only the seven
  defined values plus `watch_stopped` ever appear); a stale/superseded engine's `_settle` call is a silent
  no-op, never an exception, never a state mutation.

Test-first contract:

- TC-1: given a fresh sim watch for `SIM-BIDABS`, when `get_observation_source("SIM-BIDABS")` is called
  right after watch creation, then the returned descriptor shows `source_mode="sim"`, `data_feed="sim"`,
  `window_start_utc=None`, `window_end_utc=None`, `dataset_id=None`, `dataset_checksum=None`, a
  non-empty `session_id`, a pinned-ISO `session_started_at_utc`, and `profile_id="default"`.
- TC-2: given a historical watch created with a parsed UTC start/end window, when
  `get_observation_source(ticker)` is called, then `source_mode="historical"`, `data_feed` equals
  `data_feed_for_scenario` for that scenario (`"sip"` by default config), and `window_start_utc` /
  `window_end_utc` equal the pinned-ISO parsed request window exactly.
- TC-3: given a live watch fed via `LiveProvider` over fixture/merged records, when
  `get_observation_source(ticker)` is called, then `source_mode="live"` and `data_feed` equals the
  config-owned `live_feed` value (`"iex"` by default).
- TC-4: given the same ticker watched, stopped, and re-watched, when `session_id` is read at each watch,
  then the two values differ, while `source_mode`/`data_feed` are recomputed fresh for the new watch's
  mode (never carried over from the old watch's descriptor).
- TC-5: given one watch left running, when `get_observation_source(ticker)` is called twice without any
  intervening lifecycle change, then `session_id` and `session_started_at_utc` are identical across both
  reads (stable within one watch).
- TC-6: given a live/paced feeder task genuinely still executing (an async provider blocked mid-iteration
  on an unresolved awaitable), when a switch/re-watch for the SAME ticker is issued and the event loop is
  then advanced enough to run the old feeder's `CancelledError` handler, then `get_observation_source(ticker)`
  returns the NEW engine's settled pair and descriptor, never the old engine's; `test_counterexample_*`
  reverting the `_settle` identity check reproduces the old clobber (the new pair is overwritten).
- TC-7: given each of the seven `lifecycle.stream_status` values (`connecting`, `waiting`, `live`,
  `stale`, `paused`, `closed`, `failed`) plus the in-process `watch_stopped` case, when
  `build_tape_observation(...)` is called for each (or `get_observation_source` is called after `stop()`
  for `watch_stopped`), then every case is distinguishable from every other by `lifecycle.stream_status`
  (or the `None` return) alone.
- TC-8: given a `stale`, `closed` or `failed` transition after at least one processed event, when the
  artifact is built, then `tape_state` and `confidence` equal their last-processed values exactly (never
  null, never rewritten); `test_counterexample_*` shows a build that nulls them on `stale` fails the
  assertion.
- TC-9: given a sim watch, a `HistoricalProvider` watch over the committed PG SIP fixture, and a
  `LiveProvider` watch, when each one's `(data_feed, availability_basis)` pair is read, then the three
  pairs (`sim`/`simulated_not_applicable`, `sip`/`historical_arrival_unknown`, `iex`/`live_settled_wall_clock`)
  are pairwise distinct and never equal to one another.
- TC-10: given every committed fixture dataset under `tests/fixtures/datasets_j03/`, when its manifest
  `data_feed` is compared against a fresh call to `data_feed_for_scenario(meta["scenario"], config)`, then
  the two values are equal for every fixture; `test_counterexample_*` mutates one manifest's `data_feed`
  in a loaded copy and shows the comparison fails on it.
- TC-11: given `app/watch_manager.py` and `app/main.py`'s source, when an AST scan runs for a second
  scenario-prefix parser (a bare scenario-string check computing a feed or source-mode value outside
  `data_feed_for_scenario` and the manager's own descriptor recording), then zero occurrences are found;
  given `app/engine/*.py`'s source, when scanned for `session_id` / `session_started_at_utc` references,
  then zero occurrences are found.
- TC-12: given a fully-built `TapeObservation` dict for a live watch, when it is scanned case-insensitively
  for `READY`, `NO_TRADE`, `NO_VERDICT`, `trade_allowed`, `PENDING_CONDITION`, then zero matches are found;
  `test_counterexample_*` injects one of those tokens into a copy of the dict and shows the scan catches it.
- TC-13: given the full backend suite, when `cd apps/backend && .venv/bin/python -m pytest tests/ -q` is
  run, then the pass count is >= 4001 (iter-2 baseline) plus the count of tests newly added in
  `test_tape_observation_lifecycle_feed.py`, with 0 failed, and `Config.config_fingerprint()` still
  returns `08e471b10130e1e2`.
- TC-14: given `cd apps/frontend && npx tsc --noEmit` is run after this iteration's changes, then it
  reports 0 errors (no frontend file was touched).
- TC-15: given the goal-mode scan step over the diff restricted to `apps/`, `docs/`, `scripts/`, when it
  runs, then the report is CLEAN with zero secret/dependency/license findings.
- TC-16: given `SIM-BIDABS` watched live via the Cockpit, when `/tape/SIM-BIDABS/observation` is
  requested over HTTP (browser-qa), then the response is still a 404 "Not Found" body, and
  Pause / Resume / Stop on `/` behave exactly as before.

## NOTES

- Applying the iter-0 lessons entry (applies through iteration 4): a flat journey table this iteration
  (J-03 not fully unlocked) is the expected, correct signal — do not read it as a stall and do not move
  the route earlier. Score this iteration on `test_tape_observation_lifecycle_feed.py`'s pass/fail and
  the honest absence of the route, not on J-03's merged verdict alone.
- Applying the iter-1 lessons entry: it flagged `availability_basis`/lifecycle/feed-basis vocabularies as
  candidates for the same guard-forbidden-import tension iter-1 hit with `TAPE_STATE_VOCABULARY`. Checked
  directly this iteration (as iter-2 did for `availability_basis`): it does not recur — `lifecycle.stream_status`
  and `source.data_feed` are free-form pass-through strings, not a closed vocabulary constant
  `observation_contract.py` must embed and cross-check, so nothing needs duplicating here.
- Applying the iter-2 lessons entry (the `_settle` clobber risk): this iteration is the fix — the
  identity check plus the real running-task-switch test named there (TC-6 above).
- The iter-2 lessons entry about `tests/test_tick_recorder.py::test_tr31_...` being a genuine
  time-dependent flake applies here too: a single failure in that one unrelated test during the full-suite
  re-run is not a regression signal — re-run before treating it as one.
- Two interpretation calls logged to `runs/goal-session-observation-contract/state/assumptions.md`
  (iter-3): (1) `profile_id=PROFILE_DEFAULT` is stored as a constant field of the per-watch descriptor
  recorded at creation, per Key Capability 4's literal wording, rather than left for the iteration-5 route
  to supply inline; (2) J-03's own test module ships a SCOPED actionability-token scan satisfying its own
  acceptance step now, while the general-purpose, lexicon-driven guard module remains iteration 6's
  (Required Trap Coverage item 31 is listed under both journeys by design, not duplicated work).
- The pytest venv (9.1.1) prints no final "N passed" summary line; tally via `-q` progress characters or
  `--collect-only -q` per-file counts, per the iter-0 lessons entry — do not grep for a summary line that
  never appears.
- No full-depth trigger holds: this iteration touches one already-incrementally-built manager module
  (`watch_manager.py`) plus two call sites in an already-touched route module (`main.py`), is purely
  additive to the ALREADY-registered "Provenance / source / lifecycle metadata" blueprint row (no
  computing-module or serving-endpoint change to any value outside a still-unserved row), carries no
  frontend work, and follows a CONTINUE verdict (not ESCALATE). The hardening cadence (6) is not yet due
  (this is the 3rd consecutive lean iteration). Lean matches the evaluator's binding recommendation.
