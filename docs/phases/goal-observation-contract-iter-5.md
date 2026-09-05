# Goal Iteration 5 — The observation route: `GET /tape/{ticker}/observation` (Binding Execution Order block 5; unlocks J-01–J-05's served-JSON half)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** observation-contract
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — the route wires `main.py` + `watch_manager.py` + `observation_contract.py` (three previously separately-tested modules) into the era's first live, externally-reachable surface, whose correctness simultaneously gates J-01 through J-05; a defect here (e.g. the critical Binding-Order violation of an engine-snapshotting route) would break all five at once, a cross-journey failure mode no single already-shipped module's own test can catch, and this is the first iteration this era that edits any file under `apps/backend/app/`.
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02, J-03, J-04, J-05
- **Required-still-passing journeys:** none (0 journeys are recorded passing prior to this iteration — iteration-state after iter-4: 1 failing (J-05), 5 partial (J-01, J-02, J-03, J-04, J-06). This iteration's own DEFINITION OF DONE re-verifies the full backend suite, `tsc --noEmit`, the fingerprint, and the Cockpit Watch/Pause/Resume/Stop + `/structure`/`/desk` unchanged-render checks as the regression floor instead, matching the iter-1 through iter-4 precedent. No golden replay runs for lack of any `passing` journey to protect — expected, not a gap.)
- **Anti-goal reminders:**
  - **Rail 3 (frozen foundations):** "the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside them, never a mutation of them."
  - **Rail 6 (single source of truth):** "each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations."
  - **Rail 8 (read-only MCP):** "MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state."
  - **Era-specific:** "No recomputation of any tape feature, state, confidence, freshness or feed basis outside the engine and the one existing `data_feed_for_scenario`; no second scenario-prefix parser."
  - **Era-specific:** "No `available_at_utc` that is not a manager-measured settled instant; no `observed_at + delivery_lag` reconstruction; no availability before the underlying event or state existed."
  - **Era-specific:** "No pooling, equating or silent conversion between `sim`, `iex` and `sip`."
  - **Era-specific:** "No route that snapshots an engine for the observation; the atomic manager read is the only source."
  - **Era-specific:** "No invented git provenance: `source_revision` and `worktree_dirty` are null when unavailable, never guessed; no git call per request."
  - **Era-specific:** "No new UI page, panel, link, component or frontend file change; no new `Config` field; no named MCP tool; no CLI; no WebSocket embedding; no listing endpoint."
  - **Era-specific:** "No weakening of any existing guard: `test_no_execution_path.py`, `test_feed_basis.py`, `test_copy_discipline.py`, `test_profile_equivalence.py`, `test_fingerprint_epoch_retirement.py`, `test_mcp_server.py`, `test_stream_lifecycle.py`, `test_observer_equivalence.py` and `test_epoch_anchor.py` stay green and unedited except for additive registrations."
  - **Era-specific:** "No mandatory journey or test that requires Alpaca, the network, credentials or market hours."
  - **Goal-Mode:** "No Goal Mode workaround that edits, deletes, skips or xfails a guard merely to pass a journey."
  - **Goal-Mode:** "No browser proof based on a fabricated state presented as real; fixture and real views must be visibly distinguished."
  - **Binding Execution Order (verbatim, governs this exact step):** "A route that reads an engine directly, an `available_at_utc` derived from event time, or a semantic divergence hidden by widening the metadata partition is a critical anti-goal violation, not an iteration opportunity."

## GOAL

Land the one read-only machine path `GET /tape/{ticker}/observation` in `apps/backend/app/main.py` — a
transport-only route over the already-built atomic manager read and pure builder — so that watching a
Sim ticker on the Cockpit and then opening that URL returns the complete `TapeObservation` v1 artifact
instead of 404, completing the served-JSON half of J-01 through J-05 in one change.

## BACKGROUND

Four iterations of groundwork are done and, per the iteration-state "Do not redo" list, byte-identical
since: the schema constants, `build_tape_observation` and both hash laws (iter-1); the atomic settled
pair and `get_observation_source` (iter-2); the `SourceDescriptor`/session/feed-basis provenance
(iter-3); and the replay-vs-live ingestion-path equivalence proof (iter-4). The evaluator's iter-4
next-step recommendation is explicit and threefold: build the route plus
`tests/test_tape_observation_route.py` (J-05, Binding Execution Order step 5); in the same round rewrite
the three saved replay scripts that still assert the route is absent
(`journey-scripts/J-01.json` step 5, `J-03.json` step 11, `J-04.json` steps 8-9) or later automatic
replays will report false failures; and repair the one vacuous counter-example the evaluator found in
`test_tape_observation_path_equivalence.py` (`test_counterexample_field_partition_drift_is_detected`
compares two hand-written lists to each other and never reads the real `observation_contract` constant).

Direct repo inspection confirms the route is a small, well-contained addition: `main.py` does not yet
import `observation_contract` at all (only a comment references it); `WatchManager.get_observation_source`
already returns exactly the 4-tuple the builder needs
(`snapshot, settled_at_utc, end_reason, SourceDescriptor`) and already returns `None` for an unwatched
ticker, mirroring the existing `_engine_or_404` idiom the other five `/tape/*` siblings use; and the
MCP `get_endpoint` proxy's allowlist (`apps/backend/app/mcp/__init__.py`,
`ALLOWED_GET_PREFIXES = ("/tape/", "/research/", "/meta/")`) already covers the new path with zero
registry change — no new named tool, no change to the pinned v8/28-tool contract. The one genuinely new
production code is a single transport-only route function plus one new import line.

**Lessons applied.** The iter-2 lesson flagged the `_settle` helper's lack of an identity check as a
risk specifically "before the route reads it at iteration 5," naming iteration 5 as "the first
production reader of `get_observation_source`." I confirmed by direct read that this was already fully
closed in iteration 3: `watch_manager.py:454` (`if self._engines.get(ticker) is not engine: return`)
plus a real async running-task-switch test
(`test_settle_identity_check_prevents_a_stale_feeders_late_settle_from_clobbering_a_switch`) and its
counter-example (`test_counterexample_settle_without_identity_check_reproduces_the_clobber`) both exist
in `test_tape_observation_lifecycle_feed.py` — so the route can safely become that first production
reader with no further hardening needed. The iter-3/iter-4 lessons on tautological "distinct/unchanged"
counter-examples that never touch the real subject apply twice this round: fixing the one the iter-4
evaluator found, and not introducing a new one in this iteration's own `test_tape_observation_route.py`
`test_counterexample_*`. The iter-0 lesson on the pytest venv printing no final summary line (tally via
`-q` progress or `--collect-only -q` counts) and the iter-2 lesson on
`test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates` being a genuine
time-dependent flake both still apply to this iteration's full-suite re-run.

**Depth.** The evaluator's recommendation for this iteration is `full`, which is BINDING by default, and
it is independently justified under trigger 1 (structural/cross-cutting): this is the first iteration this
era that edits any file under `apps/backend/app/` — every prior iteration was test-only. The route wires
three previously-isolated, separately-tested modules (`main.py`, `watch_manager.py`,
`observation_contract.py`) into ONE first-time live HTTP surface, and a single defect in that wiring
(most obviously the named critical violation — a route that snapshots the engine directly) would
silently invalidate J-01 through J-05 all at once, a failure mode no individual module's own unit-test
module (already green) can detect. This is not a data-model migration (trigger 2 is explicitly excluded
for purely additive work, and every value served here was already registered in `blueprint.md`'s Data
Contract at iteration 1 as `(planned)`), nor is the prior verdict `ESCALATE` (trigger 3), nor is the
hardening cadence due yet (4 consecutive lean iterations against a cadence of 6, trigger 4). Trigger 1
alone carries it. Per `docs/goal.md` Constraints ("if the engine escalates an iteration to full depth,
the iteration spec sets `Frontend Present: yes` with the served JSON page as the browser surface and
answers the UI-evolution audit 'no user-facing capability introduced'"), `Frontend Present` is set to
`yes` here even though zero frontend files change — the served-JSON URL itself is the browser surface
this iteration's full-depth UI/QA lanes exercise, exactly as J-01 through J-05's own Steps already read
it in a browser tab.

**Target selection.** Five journeys are targeted at once, a deliberate exception to the usual 1-3 cap:
the iter-0 lessons entry names exactly this shape ("every one of J-01..J-05 asserts on the SAME served
surface... several correctly-executed build iterations will legitimately produce zero newly-passing
journeys, and the journey table will only unlock in a burst once the route lands... Applies to
iterations 1-4 ... the decomposer and the evaluator both"), and `blueprint.md`'s Data Contract already
registers all four value-rows under the identical single serving endpoint. This is not the "never bundle
two risky journeys" rule being broken: the actual change set is ONE small, well-scoped, already-prepared
addition (one route function, one import) touching a single file, not five independent risky changes —
the five journey IDs describe the SHAPE of what that one change unlocks, not five separate diffs. The
goal's own Binding Execution Order (step 5) also makes this the one mandatory next increment, not a free
choice among independent journeys, exactly the external-constraint carve-out iteration 4's own BACKGROUND
already used for its single-journey pick. J-06 (guards/sentinel) is deliberately excluded — it is step 6,
gated on a still-unbuilt guard test module — and is not degraded by this round's work.

## IN SCOPE

### Backend

- [ ] New route `GET /tape/{ticker}/observation` in `apps/backend/app/main.py` (Binding Execution Order
      step 5, J-05; Required Trap Coverage items 35-39). Transport only: looks up
      `manager.get_observation_source(ticker)`; when it returns `None`, raises the same 404 shape the
      five existing `/tape/*` siblings use (`_engine_or_404`'s convention); otherwise unpacks the atomic
      `(snapshot, settled_at_utc, end_reason, SourceDescriptor)` 4-tuple and calls
      `build_tape_observation(...)` with the descriptor's fields verbatim, `generated_at_utc` from the
      route's own `now` (via the existing `_iso_utc` helper — never a hand-formatted string), and
      `resolve_implementation_provenance()`'s already-cached triple; returns the resulting dict verbatim
      for FastAPI to serialize. The route calls no `TapeEngine` method and performs no computation of its
      own — the one critical Binding-Order violation this iteration must not commit.
- [ ] New test module `apps/backend/tests/test_tape_observation_route.py` (J-05, Required Trap Coverage
      items 35-39), each as a named test: an AST/source guard proving the route consumes
      `manager.get_observation_source(ticker)` and calls no `TapeEngine` method, with a
      `test_counterexample_*` proving the guard can fail; with `now` frozen, the route's parsed JSON is
      field-for-field and value-for-value equal to `build_tape_observation`'s direct output for the same
      atomic read; `observation_hash` and `artifact_hash` are recomputable from the served JSON via the
      §6 canonical encoding; the MCP `get_endpoint` response bytes equal the REST response bytes against
      a real uvicorn subprocess (the same real-uvicorn-subprocess pattern `test_mcp_server.py` already
      establishes), and the MCP no-write / no-app-import / 28-tool pins are unchanged; a GET starts no
      watch, computation, git call or recording, shown by unchanged manager and provenance-resolver call
      counts across 100 consecutive requests; 404 parity with `/tape/{ticker}/state` for an unwatched
      ticker.
- [ ] Fix the carried-forward vacuous counter-example the iter-4 evaluator found:
      `apps/backend/tests/test_tape_observation_path_equivalence.py::test_counterexample_field_partition_drift_is_detected`
      currently builds a `widened` tuple and compares it only to a second hand-written literal
      (`_FROZEN_SEMANTIC_FIELDS`), never touching the real subject. Rewrite it to perturb the REAL
      `observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS` (e.g. via `monkeypatch.setattr`) and show
      the module's own real partition check fails against the perturbed value — matching the iter-4
      lessons entry ("the counter-example must perturb ... the REAL constant, not a second copy of the
      literal").

### Frontend

None — zero frontend files touched (`docs/goal.md` Product Shape: "No page, panel, link or component is
added or modified"; Constraints: "No frontend file changes this era"). `Frontend Present: yes` is set
purely per goal.md's own full-depth rule so the browser-qa/UI-evolution lane runs against the served-JSON
URL as its browser surface — not because any UI file changes.

### QA / regression fixtures

- [ ] Rewrite the three stale golden replay scripts so none still asserts the route is absent:
      `runs/goal-session-observation-contract/journey-scripts/J-01.json` step 5 (currently expects
      `"Not Found"` at `/tape/SIM-BIDABS/observation`), `J-03.json` step 11 (same URL, same stale
      expectation), and `J-04.json` steps 8-9 (currently expect `"404"` at a point in the sequence that
      predates the CURRENT `docs/goal.md` J-04 Step 1 text — that step now asks for a live watch, a
      Pause, and two reloads confirming `observation_hash` is stable while `generated_at_utc` and
      `artifact_hash` differ, not a post-Stop 404 check; the rewrite must follow the current Step 1 text,
      not just swap the expected string). Each script's new assertions must match literal content the
      route now honestly serves for that exact browser sequence.

### New user-facing capability

A user can watch a Sim ticker on the Cockpit (`/`, unchanged) and then open
`/tape/{ticker}/observation` directly in the browser to read the complete `TapeObservation` v1 JSON
artifact for that ticker — previously a 404, now a real, complete, hashable artifact. No new page, panel
or control is added; the capability is reaching an already-documented URL that now honestly answers.

### New information displayed

Every field of `TapeObservation` v1 becomes visible for the first time at
`/tape/{ticker}/observation` for any currently-watched ticker: schema/provider/ticker identity,
`tape_state`/`confidence`/`warm`/`primary_window`/`features`/`trade_event_count`/`market.*`,
`observations[]`, `lifecycle.*`, `timing.*`, `source.*`, `engine_identity.*`,
`implementation_provenance.*`, `observation_hash`, `artifact_hash`.

### New user actions

None new. The existing Watch / Pause / Resume / Stop controls on `/` are unchanged; the only new action
available is navigating the browser to an already-documented URL.

### UI surface changes

None. `/`, `/structure`, `/desk` render exactly as before — zero component, page or nav change. The
"browser surface" the full-depth QA/UI-evolution lane exercises this iteration is the served-JSON URL
itself, per `docs/goal.md` Constraints.

### Product surface delta

The product's set of pages is unchanged; what changes is that one previously-404 machine path now serves
real content. A user navigating the product notices nothing different; a user (or browser-qa) who reads
that specific URL directly now sees the artifact instead of an error.

### Blueprint conformance

No new Information-Architecture home is needed — the route already has its entry
("Machine-only surface... `GET /tape/{ticker}/observation`") from the iter-0 baseline blueprint. This
iteration is registered in `blueprint.md`'s Data Contract: all four rows' "Served by" column moves from
`(planned — route lands iter-5)` to `(iter-5)`, and the closing paragraph gets one added sentence
attributing the route itself to this iteration. Additive edits only — no nav-skeleton change, so no
`blueprint.reapproval-requested` note was filed.

### Data-contract additions

None. All four Data Contract rows (machine observation semantics; provenance/source/lifecycle metadata;
explanatory metadata; integrity) were already fully registered at iteration 1, with their computing
modules completed across iterations 1-3. This iteration gives them their already-planned SINGLE serving
endpoint (`GET /tape/{ticker}/observation`) and introduces no new field, no new computing module and no
second endpoint for any of them.

## OUT OF SCOPE

- `apps/backend/tests/test_tape_observation_guards.py` and any of its five guards (copy-discipline /
  compound-identifier ban, external-system reference, English-only, real-provider isolation,
  mutator-call-site) — Binding Execution Order step 6, J-06, reserved for the next iteration.
- Any change to `apps/backend/app/observation_contract.py` or `apps/backend/app/watch_manager.py` — both
  are already complete (iterations 1-3, "Do not redo"); the route consumes their existing public surface
  unmodified. If the developer finds a genuine gap, record it in the dev handoff rather than silently
  expanding scope.
- Any change to `apps/backend/app/mcp/__init__.py` — the generic `/tape/` prefix in
  `ALLOWED_GET_PREFIXES` already covers the new route with zero registry change (confirmed by direct
  inspection this round); no new named MCP tool, no change to the pinned v8/28-tool contract.
- `docs/observation-contract-spec.md` — already exists and already matches the schema constants (the
  J-01 parity test, iteration 1); no edit needed to serve the route.
- Any `Config` field addition; any frontend file, page, panel or nav change; any CLI or WebSocket
  embedding; any new listing endpoint.
- Real-provider (Alpaca) network calls.
- Any widening of the metadata partition, any engine-snapshot read inside the route, any
  `available_at_utc` derivation from event time — Binding-Order critical violations, not iteration
  opportunities.

## DEFINITION OF DONE

- [ ] `GET /tape/SIM-BIDABS/observation` (ticker watched live via the Cockpit) returns HTTP 200 with the
      complete v1 field set and the identity/provenance values J-01 names (TC-1, TC-2).
- [ ] `GET /tape/ZZZZ/observation` (never watched) returns a 404 body in the same shape as
      `/tape/ZZZZ/state` (TC-9).
- [ ] The three honest time fields and `availability_basis` are correct on the served JSON for the Sim
      basis (TC-3).
- [ ] A full Watch → Pause → Resume → Stop → re-Watch cycle is visible end-to-end on the served JSON:
      `lifecycle.stream_status`/`lifecycle.paused` track each transition, `tape_state` and
      `timing.settled_at_utc` are unchanged across the pause, the route 404s after Stop, and the
      re-watch shows a new `source.session_id` (TC-4, TC-5, TC-6).
- [ ] Two reloads of a paused watch's observation show identical `observation_hash` and different
      `generated_at_utc` / `artifact_hash` (TC-7).
- [ ] `apps/backend/tests/test_tape_observation_route.py` passes with 0 failures, `test_counterexample_*`
      included, proving: the route never calls a `TapeEngine` method (TC-10); frozen-`now` route output
      equals `build_tape_observation`'s direct output field-for-field (TC-11); both hashes are
      recomputable from the served JSON (TC-12); MCP `get_endpoint` bytes equal REST bytes against a real
      uvicorn subprocess and the 28-tool / no-write / no-app-import pins are unchanged (TC-13); a GET's
      manager and provenance-resolver call counts are unchanged across 100 requests (TC-14); the module's
      own counter-example(s) prove TC-10/TC-11 are not vacuous (TC-15).
- [ ] `test_tape_observation_path_equivalence.py`'s `test_counterexample_field_partition_drift_is_detected`
      perturbs the real `observation_contract` constant rather than two hand-written literals (TC-16).
- [ ] None of the three golden replay scripts (`J-01.json`, `J-03.json`, `J-04.json`) still assert the
      route is absent (TC-17).
- [ ] Full backend suite green, pass count no lower than iter-4's 4036-passed baseline plus this
      iteration's net new tests; `Config.config_fingerprint()` unchanged at `08e471b10130e1e2` (TC-18).
- [ ] `cd apps/frontend && npx tsc --noEmit` reports 0 errors (TC-19).
- [ ] `/`, `/structure`, `/desk` render exactly as before — zero new panel, link or control (regression
      check; this also advances J-06's own eventual acceptance criterion even though J-06 itself is not
      targeted this iteration).
- [ ] No anti-goal violation introduced (scan-report CLEAN); coherence verdict stays `COHERENCE-PASS` or
      better.
- [ ] Dev handoff written at `docs/handoffs/goal-observation-contract-iter-5-dev.md`.

Note on journey status: this iteration is expected to make every clause of J-01 through J-05's Acceptance
checkable for the first time — but which of them the evaluator records as `passing` versus still
`partial` on some other narrow gap is the evaluator's call to make from the evidence, not predicted here.

## TESTING REQUIREMENTS

- Browser: J-01, J-02, J-03, J-04, J-05 — this is the first iteration where every literal Step of all
  five is actually executable (not the narrowed "regression-smoke" scope iterations 1-4 used). Browser-qa
  must run all five in full, producing a fresh capture that supersedes the three stale golden scripts
  named above, plus an unchanged-render spot check on `/structure` and `/desk`.
- Unit/integration: `apps/backend/tests/test_tape_observation_route.py` (new — TC-10..TC-15);
  `test_tape_observation_path_equivalence.py` fixup (TC-16); full backend suite (TC-18);
  `tsc --noEmit` (TC-19). No integration test needs network access or real Alpaca credentials.
- Error cases: an unwatched ticker never fabricates a 200 (TC-9); a route that reads an engine directly,
  or derives `available_at_utc` from event time, is a critical anti-goal violation to report — never an
  accepted shortcut; a GET that starts a watch, computation, git call or recording is a reported defect,
  never accepted as "mostly stateless" (TC-14).

Test-first contract:

- TC-1: given `SIM-BIDABS` watched live via the Cockpit, when `/tape/SIM-BIDABS/observation` is opened,
  then the body is HTTP 200 JSON containing `"schema_version": "tape-observation-v1"`,
  `"provider": "tapeology"`, `"ticker": "SIM-BIDABS"`, and the top-level keys `tape_state`, `confidence`,
  `warm`, `primary_window`, `features`, `trade_event_count`, `market`, `observations`, `lifecycle`,
  `timing`, `source`, `engine_identity`, `implementation_provenance`, `observation_hash`,
  `artifact_hash`.
- TC-2: given that same response, then `engine_identity.engine_semantics_version` equals
  `"tape-engine-v1"`, `engine_identity.config_fingerprint` equals `"08e471b10130e1e2"`,
  `engine_identity.profile_id` equals `"default"`, `source.session_id` is non-empty,
  `source.session_started_at_utc` is an ISO-8601 UTC instant ending in `Z`, and
  `implementation_provenance` shows a 64-hex `engine_source_hash`, a `source_revision` that is 40-hex or
  `null`, and a `worktree_dirty` that is `true`, `false` or `null`.
- TC-3: given the same watch, when `/tape/SIM-BIDABS/observation` is opened, then `observed_at_utc`
  starts with `"2024-01-02T14:3"`, `available_at_utc` is `null`, `availability_basis` equals
  `"simulated_not_applicable"`, and both `timing.settled_at_utc` and `generated_at_utc` carry today's
  date.
- TC-4: given `SIM-BIDABS` watched and live, when `/tape/SIM-BIDABS/observation` is read, then
  `lifecycle.stream_status` equals `"live"` and `lifecycle.paused` is `false`; when `Pause watching` is
  pressed and the JSON reloaded, then `lifecycle.stream_status` equals `"paused"`, `lifecycle.paused` is
  `true`, `tape_state` is unchanged from the prior read, and `timing.settled_at_utc` is unchanged from
  the prior read.
- TC-5: given the paused watch from TC-4, when `Resume watching` is pressed and the JSON reloaded, then
  `lifecycle.stream_status` reads `"live"` again; when `Stop watching` is then pressed and the JSON
  reloaded, then the response is a 404 body.
- TC-6: given `SIM-BIDABS` re-watched after the Stop in TC-5, when `/tape/SIM-BIDABS/observation` is
  reloaded, then `source.session_id` differs from the value read in TC-4 while `source.source_mode`
  equals `"sim"` and `source.data_feed` equals `"sim"`.
- TC-7: given `SIM-BIDABS` watched and then paused, when `/tape/SIM-BIDABS/observation` is opened twice
  (two reloads), then `observation_hash` is identical across the two responses while `generated_at_utc`
  and `artifact_hash` differ between them.
- TC-8: given `apps/backend/app/main.py`'s new route source, when it is inspected (AST or source scan),
  then it calls `manager.get_observation_source(ticker)` and contains no call to any `TapeEngine` method.
- TC-9: given `ZZZZ` is never watched, when `/tape/ZZZZ/observation` is opened, then the response is a
  404 body in the same shape as `/tape/ZZZZ/state`'s 404.
- TC-10: given the guard in TC-8, when a `test_counterexample_*` reintroduces a direct engine-snapshot
  call in a copy of the route, then the guard raises, proving it is not vacuous.
- TC-11: given a frozen `now`, when the route's parsed JSON response is diffed field-by-field against
  `build_tape_observation`'s direct return value for the identical atomic read and the identical `now`,
  then every field and value is equal between the two.
- TC-12: given a served observation JSON, when `observation_hash` and `artifact_hash` are recomputed
  from it via the §6 canonical encoding, then both recomputed values equal the served values.
- TC-13: given a real uvicorn subprocess serving the app, when the MCP `get_endpoint` tool reaches
  `/tape/{ticker}/observation` and the REST endpoint is requested directly for the same ticker, then the
  two response bodies are byte-identical, the advertised MCP tool count is still 28, and the no-write /
  no-app-import pins are unchanged.
- TC-14: given the watch manager's `get_observation_source` call count and the provenance resolver's
  underlying git-call count sampled before and after issuing 100 consecutive
  `GET /tape/{ticker}/observation` requests against an already-watched ticker, then both counts show
  exactly 100 additional manager reads and zero additional git calls (no watch started, no recording).
- TC-15: given `test_tape_observation_route.py`'s `test_counterexample_*` test(s), when they run, then
  they show that mutating a served field (or reintroducing a direct engine-snapshot call) makes the
  TC-10 or TC-11 comparison fail, proving neither guard is vacuous.
- TC-16: given `test_tape_observation_path_equivalence.py::test_counterexample_field_partition_drift_is_detected`
  after this iteration's fix, when it runs, then it perturbs the real
  `observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS` attribute (e.g. via `monkeypatch.setattr`)
  and shows the module's own real partition-equality check fails against that perturbed value.
- TC-17: given the three stored golden replay scripts `journey-scripts/J-01.json` (step 5),
  `journey-scripts/J-03.json` (step 11) and `journey-scripts/J-04.json` (steps 8-9), when they are
  read after this iteration, then none of them expects `"Not Found"` or `"404"` at a step where the
  route now serves real content — each asserts literal content the route now honestly returns instead.
- TC-18: given the full backend suite, when `cd apps/backend && .venv/bin/python -m pytest tests/ -q` is
  run, then it reports 0 failed with a pass count of iter-4's 4036 baseline plus this iteration's net new
  tests, and `Config.config_fingerprint()` still returns `"08e471b10130e1e2"`.
- TC-19: given `cd apps/frontend && npx tsc --noEmit` run after this iteration's changes, then it reports
  0 errors (no frontend file was touched).
- TC-20: given the goal-mode scan step over the diff restricted to `apps/`, `docs/`, `scripts/`, when it
  runs, then the report is CLEAN with zero secret/dependency/license findings.

## NOTES

- Lessons applied this round: the iter-2 settle-identity-race lesson (confirmed already closed in
  iteration 3 — see BACKGROUND); the iter-3/iter-4 tautological-counter-example lesson (fixed once,
  avoided once more in the new module); the iter-0 pytest-summary-line lesson; the iter-2
  `test_tr31_...` flaky-test lesson. All four are named in BACKGROUND rather than repeated here.
- Depth `full` is the evaluator's binding recommendation and is independently justified under trigger 1
  (structural/cross-cutting) — see BACKGROUND for the full argument. No hardening-cadence trigger is
  needed or claimed; the consecutive-lean counter (4 of 6) resets on this dispatch regardless.
- No new interpretation call was logged to `runs/goal-session-observation-contract/state/assumptions.md`
  this iteration: `docs/goal.md`'s own text answers every open question this round needed (the route's
  shape from Constitution §1/§7, the `Frontend Present: yes` full-depth rule from Constraints, and the
  MCP allowlist already covering `/tape/` from the existing, unmodified `mcp/__init__.py`) — nothing
  required a discretionary reading.
- `blueprint.md` was updated in place this iteration: the Data Contract's four "Served by" cells move
  from `(planned — route lands iter-5)` to `(iter-5)`, the Feature/journey-homes table drops
  `(planned)` for J-01 through J-05, and the closing paragraph gains one sentence attributing the route
  to this iteration. No nav-skeleton change, so no `blueprint.reapproval-requested` note was filed.
