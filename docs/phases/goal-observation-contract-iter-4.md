# Goal Iteration 4 — Ingestion-path equivalence proof (J-04, block 4 of the Binding Execution Order)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** observation-contract
- **Iteration:** 4
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-04
- **Required-still-passing journeys:** none (0 journeys are recorded passing this session as of
  iter-3: 2 failing — J-04, J-05 — and 4 partial — J-01, J-02, J-03, J-06. This iteration adds ONE
  new test module plus two test-only fixups to already-shipped test files — zero files under
  `apps/backend/app/` are touched, so there is no production surface to regress and nothing
  `passing` to protect. The foundation invariants that matter here are re-verified as TC scenarios
  instead: the full backend suite (which already includes every prior iteration's test module),
  `config_fingerprint = 08e471b10130e1e2`, `tsc --noEmit` 0 errors, and a Cockpit
  Watch/Pause/Resume/Stop smoke check.)
- **Anti-goal reminders:**
  - **Rail 3 (frozen foundations):** "the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside them, never a mutation of them."
  - **Rail 6 (single source of truth):** "each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations."
  - **Rail 7 (deterministic and seeded):** "every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact."
  - **Era-specific:** "No pooling, equating or silent conversion between `sim`, `iex` and `sip`."
  - **Era-specific:** "No recomputation of any tape feature, state, confidence, freshness or feed basis outside the engine and the one existing `data_feed_for_scenario`; no second scenario-prefix parser."
  - **Era-specific:** "No mandatory journey or test that requires Alpaca, the network, credentials or market hours."
  - **Era-specific:** "No weakening of any existing guard: `test_no_execution_path.py`, `test_feed_basis.py`, `test_copy_discipline.py`, `test_profile_equivalence.py`, `test_fingerprint_epoch_retirement.py`, `test_mcp_server.py`, `test_stream_lifecycle.py`, `test_observer_equivalence.py` and `test_epoch_anchor.py` stay green and unedited except for additive registrations."
  - **Binding Execution Order (verbatim, governs this exact step):** "A route that reads an engine directly, an `available_at_utc` derived from event time, or a semantic divergence hidden by widening the metadata partition is a critical anti-goal violation, not an iteration opportunity."
  - **Constitution §5 explicit non-claim (verbatim):** "This invariant does not assert semantic equality between independently sourced IEX and SIP market data, which may contain different events. Feed bases are never pooled. If any ingestion path produces semantic divergence on identical ordered input, that is a blocking finding to report — never excluded by widening the metadata partition."

## GOAL

Prove, with deterministic tests only, that the frozen tape engine yields an identical
machine-observation semantic set and `observation_hash` whether an identical valid event stream
reaches it through the replay feeder or the live feeder — Binding Execution Order step 4 — with zero
visible product change and zero edits to any file under `apps/backend/app/`.

## BACKGROUND

The evaluator's iter-3 next-step recommendation is explicit and binding: build J-04 — feed one
identical recorded event stream through the replay path and through the live path, capture every
tick on both, and prove the content identity matches on both while source/session details honestly
differ — by adding `apps/backend/tests/test_tape_observation_path_equivalence.py` with its mutation
counter-test.

Direct repo inspection confirms this entire proof is buildable from surfaces that already exist,
with no change to any production module:
`WatchManager.watch_with_provider(ticker, provider, speed=...)` and
`WatchManager.watch_with_async_provider(ticker, provider)` are already the manager's public replay
and live entry points; `WatchManager(CONFIG, pace=...)` already accepts the pacing knob named in the
goal's own Constraints; `TapeEngine.add_observer` is the same seam
`apps/backend/tests/test_observer_equivalence.py` already exercises for per-tick capture;
`build_tape_observation`, `field_partition_map()`, `compute_observation_hash` and
`compute_artifact_hash` (all iteration-1 work, `apps/backend/app/observation_contract.py`) already
compute exactly the comparison this journey needs; and
`apps/backend/tests/test_tape_observation_time.py` already establishes the exact fixture-loading and
live-leg idiom this module reuses — `load_fixture_window(PG_FIXTURE)` for the committed
`tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json` fixture's `HistoricalProvider` leg, and
the local `_aiter(records)` async generator feeding `LiveProvider(ticker, _aiter(records), "live
TICKER")` for the live leg (its own
`test_observed_at_utc_equals_latest_event_for_live_provider` is the closest existing precedent). This
iteration is therefore the leanest of the session so far: one new test file plus two small,
test-only fixups the reviewer, evaluator and coherence-auditor flagged across iteration 3 — no
change to `watch_manager.py`, `observation_contract.py`, or `main.py`.

The two fixups: (1) the reviewer's carried-forward MINOR —
`test_seven_lifecycle_statuses_plus_watch_stopped_are_pairwise_distinguishable`
(`apps/backend/tests/test_tape_observation_lifecycle_feed.py:513`) asserts only
`len({seven hand-written literals}) == 7` and never calls `WatchManager`; the lessons-learned entry
for iteration 3 names exactly this failure mode ("a spec item phrased 'all N values are pairwise
distinguishable' invites a tautological summary test") and warns it applies to future
"every one of N states/values is distinct" coverage — this iteration's own new equivalence tests
must not repeat it (any "the two legs differ" assertion must read real built artifacts, never a
hand-written literal pair); (2) the coherence-auditor's non-blocking advisory — `main.py`'s new
`_iso_utc(dt: datetime)` claims in its own docstring to match `watch_manager._iso_utc` and
`observation_contract._iso_utc` (both `_iso_utc(epoch: float)`) byte-for-byte, but nothing tests that
third leg; `test_tape_observation_time.py` already has the pairwise version of this exact check
(`test_watch_manager_iso_helper_matches_observation_contract_byte_for_byte`) to extend.

Applying the iter-0 lessons entry (applies through iteration 4, the last build iteration before the
route lands): a flat journey table remains the expected, correct signal. J-04's Acceptance is a
conjunction whose first half is a browser check on `/tape/SIM-BIDABS/observation` — a route that does
not exist until iteration 5 — so this iteration cannot move J-04 to `passing`; the honest signal is
the new pytest module's pass/fail, matching the same convention already applied to J-01/J-02/J-03.
Do not move the route earlier. The iter-2 lessons entry about
`test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates` being a genuine
time-dependent flake still applies to any full-suite re-run this iteration.

Target selection follows the priority rubric with no deviation: no journey is regressed, the last
coherence verdict was `COHERENCE-PASS` (no consolidation forced), and J-04 is the next step the
goal's own mandatory Binding Execution Order permits — the sequencing itself is an external
constraint from `docs/goal.md`, not a free choice among independent journeys. It is also, by
construction, the smallest available increment this session has shipped: a single new test file
plus two test-only fixups, no production diff at all.

## IN SCOPE

### Backend
- [ ] New test module `apps/backend/tests/test_tape_observation_path_equivalence.py` (J-04, Binding
      Execution Order step 4; Required Trap Coverage items 32-34). It feeds the committed PG SIP
      fixture (`tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json`, via the existing
      `fakes.load_fixture_window`) and one fixed seeded sim scenario, each as a valid ordered event
      stream, into two freshly constructed, identically configured engines per fixture: one leg
      delivered through the manager's paced-replay entry point (`speed=float("inf")` per the goal's
      "`speed_cell=[inf]`" knob, manager constructed with `WatchManager(CONFIG, pace=0.0)`), one leg
      delivered through the manager's live entry point (`LiveProvider(ticker, _aiter(records), "live
      TICKER")`, the same `_aiter` idiom `test_tape_observation_time.py` already uses). Per-tick
      capture on each leg via `TapeEngine.add_observer` (the seam `test_observer_equivalence.py`
      already exercises), with waits of at least 30 s where the harness polls for the live leg's
      completion (per the goal's Constraints — the default 3 s timeout used elsewhere in this
      session's harnesses is not assumed to be enough here). At every captured tick and at the end of
      each fixture's run: assert the two legs' `observation_hash` (and the full semantic field set
      per `field_partition_map()`'s `"semantic"` group) are equal, while `source.source_mode`,
      `source.data_feed` (on the PG-fixture pair: `historical`/`sip` vs `live`/`iex`) and session
      metadata (`session_id`, `session_started_at_utc`) differ between the legs. Ships a named
      `test_counterexample_*` that mutates one leg's captured tick before the comparison and shows
      the comparator raises. Module docstring states the Constitution §5 IEX-vs-SIP non-claim
      verbatim. Asserts `field_partition_map()`'s four groups are byte-identical to the already-
      committed iteration-1 constants (no widened partition).
- [ ] Fix the reviewer's carried-forward MINOR (iter-3):
      `test_seven_lifecycle_statuses_plus_watch_stopped_are_pairwise_distinguishable`
      (`apps/backend/tests/test_tape_observation_lifecycle_feed.py:513`) asserts only over a
      hand-written set literal and never calls `WatchManager`. Either remove it (the nine sibling
      tests directly above it, lines 370-510, already exercise every status from real
      manager/engine sequences) or rewrite it to assert over statuses actually collected from those
      real calls — either resolution is acceptable, but no test in the module may keep asserting
      "all N values are distinguishable" solely over a literal disconnected from `WatchManager`.
- [ ] Close the coherence-auditor's non-blocking advisory (iter-3): extend
      `test_tape_observation_time.py`'s `test_watch_manager_iso_helper_matches_observation_contract_byte_for_byte`
      into a three-way check that also calls `apps.main._iso_utc` (its signature takes a `datetime`,
      unlike the other two's `epoch: float` signature — convert the same representative epochs with
      `datetime.fromtimestamp(epoch, timezone.utc)` before calling it) and asserts byte-identical
      output against `observation_contract._iso_utc` for the same instants. Extend the sibling
      `test_counterexample_iso_round_trip_detects_a_hand_formatted_string` (or add one) so a
      hand-formatted string still fails the now-three-way comparison.

### Frontend
None — zero frontend files touched this iteration (goal Product Shape: "No page, panel, link or
component is added or modified").

### New user-facing capability
None. The equivalence proof and the two fixups are backend test files only, with no served,
watched or visible surface.

### New information displayed
None — nothing is served by any endpoint, page or MCP tool yet (route is iteration 5).

### New user actions
None. The existing Watch / Pause / Resume / Stop controls on `/` are exercised only as the
regression smoke check for this iteration's (zero) production changes — no new control, no visible
behavior change.

### UI surface changes
None — Cockpit `/`, `/structure`, `/desk` are untouched.

### Product surface delta
None visible. This iteration's only artifacts are one new test module plus edits confined to two
existing test files; a user (or browser-qa) sees the exact same product as after iter-3.

### Blueprint conformance
No new surfaces. `runs/goal-session-observation-contract/state/blueprint.md`'s Information
Architecture is unchanged (no page, no nav entry). This iteration adds a deterministic proof over
already-registered Data Contract computing modules — it introduces no new row, no new computing
module and no new serving endpoint. `blueprint.md`'s Data Contract closing paragraph has been
updated in place with an iter-4 progress note; no nav-skeleton change, so no re-approval request was
filed.

### Data-contract additions
None. The equivalence proof runs entirely in-process against already-existing, already-registered
computing modules (`build_tape_observation`, `WatchManager.get_observation_source`) — nothing new is
served, so no NEW displayed value exists to register.

## OUT OF SCOPE

- The route `/tape/{ticker}/observation` and any change to `apps/backend/app/main.py` — Binding
  Execution Order step 5 (iteration 5, J-05); it still 404s for every ticker after this iteration, so
  J-01 through J-04's browser steps that read the served JSON remain unmet.
- Any change to `apps/backend/app/observation_contract.py` or `apps/backend/app/watch_manager.py` —
  the proof consumes their already-existing public functions/methods unmodified. If the developer
  finds a genuine gap forcing a production change, record it in the dev handoff rather than silently
  expanding scope.
- `tests/test_tape_observation_route.py`, `tests/test_tape_observation_guards.py` — later iterations'
  own modules (5, 6).
- Any claim of semantic equality between independently sourced IEX and SIP market data (Constitution
  §5's explicit non-claim); any widening of the metadata partition to manufacture equivalence.
- Any `Config` field addition (the era adds zero); any frontend file, page, panel or nav change.
- Real-provider (Alpaca) network calls — `LiveProvider` is exercised only over the committed fixture
  and the seeded sim scenario, never a live vendor connection.

## DEFINITION OF DONE

- [ ] `apps/backend/tests/test_tape_observation_path_equivalence.py` passes with 0 failures on both
      the PG-fixture leg-pair and the seeded-sim-scenario leg-pair, with its `test_counterexample_*`
      present and passing.
- [ ] At every captured tick and at the end of each leg-pair, `observation_hash` and the full
      semantic field set are identical between the replay leg and the live leg, while
      `source.source_mode`, `source.data_feed` (PG pair) and session metadata differ between the
      legs.
- [ ] No semantic divergence is hidden by a widened metadata partition — `field_partition_map()`'s
      four groups are unchanged from iteration 1.
- [ ] The new module's docstring states the Constitution §5 IEX-vs-SIP non-claim verbatim.
- [ ] `test_tape_observation_lifecycle_feed.py`'s vacuous summary test no longer asserts solely over
      a hand-written literal disconnected from `WatchManager`.
- [ ] `test_tape_observation_time.py`'s ISO cross-check is a three-way comparison including
      `main._iso_utc`, with its counter-example still failing a hand-formatted string.
- [ ] Full backend suite still green — no fewer than iter-3's baseline of 4039 passed / 8 skipped / 0
      failed, net of this iteration's additions and (only if the vacuous test is removed rather than
      rewritten) that one subtraction. `Config.config_fingerprint()` unchanged (`08e471b10130e1e2`).
- [ ] `cd apps/frontend && npx tsc --noEmit` reports 0 errors (unaffected — no frontend file
      touched).
- [ ] Browser-qa confirms zero visible product change: `/`, `/structure`, `/desk` render exactly as
      at iter-3; `/tape/SIM-BIDABS/observation` still 404s (route not yet built — expected, correct,
      not a defect); Watch / Pause / Resume / Stop on `/` behave exactly as before.
- [ ] No anti-goal violation introduced (scan-report CLEAN); coherence verdict stays
      `COHERENCE-PASS`.
- [ ] Dev handoff written at `docs/handoffs/goal-observation-contract-iter-4-dev.md`.

Note on J-04's overall journey status: this iteration cannot make J-04 fully pass — its Acceptance
requires two reloads of the served JSON at `/tape/SIM-BIDABS/observation`, which needs the route
(iteration 5). Expect the evaluator to record J-04 as still `failing` or move it to `partial` on the
strength of the passing `test_tape_observation_path_equivalence.py` module, per the same convention
already applied to J-01/J-02/J-03; this is correct, not a regression.

## TESTING REQUIREMENTS

- Browser: no journey's Acceptance can be newly satisfied this iteration (route absent). Confirm
  `/tape/SIM-BIDABS/observation` still answers "Not Found" after a live Sim watch, across two
  reloads; confirm `/structure` and `/desk` render unchanged; confirm Watch → Pause → Resume → Stop
  on `/` still transition the status dot through `live` → `paused` → `live` → `closed` in that order
  (regression smoke — no production code was touched this iteration, so this is a pure sanity check).
- Unit/integration: `apps/backend/tests/test_tape_observation_path_equivalence.py` (new) — see
  TC-1..TC-6 below. `apps/backend/tests/test_tape_observation_lifecycle_feed.py` (fixup) — TC-8.
  `apps/backend/tests/test_tape_observation_time.py` (fixup) — TC-9. No integration test needs a
  running uvicorn server or network access.
- Error cases: an ingestion-path pair that genuinely diverges in machine-observation semantics is a
  reported blocking finding, never silently accommodated by widening the metadata partition (TC-6);
  a stale/hand-formatted ISO string is never accepted as matching the pinned format by any of the
  three `_iso_utc` copies (TC-9).

Test-first contract:

- TC-1: given the committed PG SIP fixture loaded and fed as an identical valid ordered event stream
  into two freshly constructed engines — one leg via the manager's paced-replay entry point
  (`speed=float("inf")`, manager constructed with `pace=0.0`) and one leg via
  `LiveProvider(ticker, _aiter(records), "live TICKER")` on the manager's live entry point — when
  each engine's per-tick capture (`TapeEngine.add_observer`) is compared at every captured tick and
  at the end, then `observation_hash` is equal between the two legs at every compared point.
- TC-2: given the same two PG-fixture legs' final built `TapeObservation` dicts, when every field
  named in `field_partition_map()`'s `"semantic"` group is compared between them, then all of those
  fields are equal, while `source.source_mode` (`historical` vs `live`), `source.data_feed` (`sip`
  vs `iex`) and session metadata (`session_id`, `session_started_at_utc`) differ.
- TC-3: given one fixed seeded sim scenario fed the same way — through the manager's paced-replay
  entry point and through its live entry point — when the two legs' captured ticks are compared,
  then `observation_hash` is equal between the two legs at every compared point while
  `source.source_mode` and session metadata differ.
- TC-4: given the comparator used in TC-1/TC-3, when a `test_counterexample_*` mutates one leg's
  captured `tape_state` (or another semantic field) before the comparison runs, then the comparison
  raises `AssertionError`, proving the comparator is not vacuously true.
- TC-5: given `test_tape_observation_path_equivalence.py`'s module docstring, when read, then it
  states the Constitution §5 non-claim verbatim — that the invariant does not assert semantic
  equality between independently sourced IEX and SIP market data.
- TC-6: given `app.observation_contract.field_partition_map()`'s four groups, when diffed against
  the already-committed `MACHINE_OBSERVATION_SEMANTIC_FIELDS` / `PROVENANCE_SOURCE_LIFECYCLE_METADATA_FIELDS`
  / `EXPLANATORY_METADATA_FIELDS` / `INTEGRITY_FIELDS` tuples from iteration 1, then the diff is
  empty — no field was moved into a wider partition to manufacture the TC-1/TC-3 equivalence.
- TC-7: given `SIM-BIDABS` watched live via the Cockpit and then paused, when
  `/tape/SIM-BIDABS/observation` is requested twice over HTTP (two reloads), then both responses are
  still a 404 body.
- TC-8: given `apps/backend/tests/test_tape_observation_lifecycle_feed.py` after this iteration's
  fix, when the module is inspected, then no test asserts its "all statuses distinct" claim solely
  over a hand-written set literal disconnected from a `WatchManager`/`get_observation_source` call.
- TC-9: given `main._iso_utc`, `watch_manager._iso_utc` and `observation_contract._iso_utc`, when
  each is called for the same set of representative instants, then all three produce byte-identical
  ISO-8601 output; the sibling `test_counterexample_*` shows a hand-formatted string (no
  microseconds, no trailing `Z`) fails that three-way comparison.
- TC-10: given the full backend suite, when `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
  is run, then it reports 0 failed, its pass count equals iter-3's 4039 baseline plus this
  iteration's net new tests minus one only if the vacuous lifecycle-feed test was removed rather than
  rewritten, and `Config.config_fingerprint()` still returns `08e471b10130e1e2`.
- TC-11: given `cd apps/frontend && npx tsc --noEmit` is run after this iteration's changes, then it
  reports 0 errors (no frontend file was touched).
- TC-12: given the goal-mode scan step over the diff restricted to `apps/`, `docs/`, `scripts/`, when
  it runs, then the report is CLEAN with zero secret/dependency/license findings.

## NOTES

- Applying the iter-0 lessons entry (applies through iteration 4): a flat journey table this
  iteration (J-04 cannot fully unlock — route absent) is the expected, correct signal — do not read
  it as a stall and do not move the route earlier. Score this iteration on
  `test_tape_observation_path_equivalence.py`'s pass/fail and the honest, unchanged absence of the
  route, not on J-04's merged verdict alone.
- Applying the iter-3 lessons entry on tautological "all N values are distinguishable" summary
  tests: this iteration both fixes the one that entry names AND must not introduce a new one of its
  own — every "the two legs differ" or "the two legs match" assertion in the new equivalence module
  must read real built `TapeObservation` dicts or real captured engine state, never a hand-written
  literal pair standing in for them.
- The iter-2 lessons entry about `tests/test_tick_recorder.py::test_tr31_...` being a genuine
  time-dependent flake still applies: a single failure in that one unrelated test during the
  full-suite re-run is not a regression signal — re-run before treating it as one.
- The pytest venv (9.1.1) prints no final "N passed" summary line; tally via `-q` progress
  characters or `--collect-only -q` per-file counts, per the iter-0 lessons entry — do not grep for
  a summary line that never appears.
- No new interpretation call was logged to `runs/goal-session-observation-contract/state/assumptions.md`
  this iteration: Constitution §5 and the J-04 Steps text already make explicit (via "the two legs",
  "capturing every tick" plural, and Required Trap Coverage item 32's "identical semantic set...
  while... metadata legs differ") that the comparison is between two independently constructed
  engines/legs, not a claim about reusing one mutable engine object across two feeders — this reading
  needed no ambiguity resolution.
- No full-depth trigger holds: this iteration touches zero files under `apps/backend/app/` (the
  smallest possible change set this session has shipped — one new test file plus edits confined to
  two existing test files), is purely additive to already-registered blueprint computing modules (no
  computing-module or serving-endpoint change to any value, and no new row), carries no frontend
  work, and follows a `CONTINUE` verdict (not `ESCALATE`). The hardening cadence (6) is not yet due
  (this is the 4th consecutive lean iteration). Lean matches the evaluator's binding recommendation.
