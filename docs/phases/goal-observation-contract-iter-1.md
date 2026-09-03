# Goal Iteration 1 — Constants, the pure builder, and the two hash laws (J-01, block 1 of the Binding Execution Order)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** observation-contract
- **Iteration:** 1
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-01
- **Required-still-passing journeys:** none (0 journeys are recorded passing this session as of iter-0: 5 failing, 1 partial. This iteration is backend-only and touches zero served/UI surface, so there is nothing passing to regress. The foundation invariants — full backend suite 3930 passed / 8 skipped / 0 failed, `config_fingerprint = 08e471b10130e1e2`, `tsc --noEmit` 0 errors — are re-verified as TC scenarios below, not as journey IDs.)
- **Anti-goal reminders:**
  - **Rail 6 (single source of truth):** "each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations."
  - **Rail 7 (deterministic and seeded):** "every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact."
  - **Rail 3 (frozen foundations):** "the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, and archived-era behavior stay byte-identical. New work is additive and versioned beside them, never a mutation of them."
  - **Era-specific:** "No recomputation of any tape feature, state, confidence, freshness or feed basis outside the engine and the one existing `data_feed_for_scenario`; no second scenario-prefix parser."
  - **Era-specific:** "No invented git provenance: `source_revision` and `worktree_dirty` are null when unavailable, never guessed; no git call per request."
  - **Era-specific:** "No `content_hash` field; no `reason_codes[]`; no semantic-version inference automation."
  - **Era-specific:** "No new UI page, panel, link, component or frontend file change; no new `Config` field; no named MCP tool; no CLI; no WebSocket embedding; no listing endpoint."
  - **Era-specific:** "No mandatory journey or test that requires Alpaca, the network, credentials or market hours."

## GOAL

Build the schema constants, the pure `build_tape_observation` projection function and the two hash laws
(`observation_hash`, `artifact_hash`) as one deterministic, in-process module with its own proof suite —
step 1 of the goal's mandatory Binding Execution Order — with zero visible product change.

## BACKGROUND

Iter-0 (baseline) confirmed every observation surface unbuilt and recorded 0 passing / 5 failing / 1
partial. The evaluator's own next-step recommendation is explicit: "Build the first block of the goal's
binding order — the constants, the builder, the two hash rules and
`tests/test_tape_observation_projection.py` for J-01. Keep the web address for later, as the goal's order
requires. Next iteration should be lean, backend-only, with no visible change for users." This spec is
exactly that block, no more.

Per the lessons ledger (iter-0, applies to iterations 1-4): every one of J-01..J-05 asserts on the same
served surface `/tape/{ticker}/observation`, which is Binding Execution Order step 5 — several correctly
executed build iterations, including this one, will legitimately leave J-01 not-yet-fully-passing (the
route to actually SERVE the JSON does not exist until iteration ~5). That is expected, not a stall or a
regression; the honest per-iteration signal in the meantime is the named pytest module this iteration
builds. Do not reorder the route earlier to manufacture a passing journey.

Repo inspection confirms the prerequisites this iteration needs already exist and are untouched: the
single-producer `EngineSnapshot` dataclass (`apps/backend/app/engine/snapshot.py`), the classifier's five
frozen states (`app/engine/classifier.py`), `Config.config_fingerprint()` and `PROFILE_DEFAULT`
(`app/config.py`), the one feed-basis function `data_feed_for_scenario` (`app/research/feed_basis.py`),
`TapeEngine.end_reason` (`app/engine/tape_engine.py`), and the repository's existing canonical-encoding
idiom `json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")` (used identically by
several `app/research/*.py` hash functions already). None of `apps/backend/app/observation_contract.py`,
`WatchManager.get_observation_source`, the `/tape/{ticker}/observation` route, or any
`test_tape_observation_*.py` module exists — confirmed absent again by direct inspection, matching the
"Do not redo" list.

## IN SCOPE

### Backend
- [ ] Add the module constant `ENGINE_SEMANTICS_VERSION = "tape-engine-v1"` to
      `apps/backend/app/engine/tape_engine.py` (Constitution §6: "a module constant in
      `app/engine/tape_engine.py`, bumped only by an owner act").
- [ ] Create `apps/backend/app/observation_contract.py` containing, and nothing else:
  - Schema constants: `OBSERVATION_SCHEMA_VERSION = "tape-observation-v1"`, `PROVIDER = "tapeology"`.
  - The four-group partition constants (machine-observation semantics / provenance-source-lifecycle
    metadata / explanatory / integrity) enumerating every leaf field path from Constitution §1 exactly
    once, in a form a test can iterate to assert full coverage.
  - `canonical_encode(obj) -> bytes` using the pinned encoding
    (`json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")`).
  - `compute_observation_hash(observation: dict) -> str` — sha256 hex of the canonical encoding of the
    machine-observation-semantic partition only.
  - `compute_artifact_hash(observation: dict) -> str` — sha256 hex of the canonical encoding of the whole
    artifact minus the `artifact_hash` key itself.
  - `resolve_implementation_provenance()` — a process-memoized (called at most once per process; a call
    counter or cache is test-observable) resolver returning `(engine_source_hash, source_revision,
    worktree_dirty)`: `engine_source_hash` = sha256 over the concatenated source bytes of a fixed,
    explicitly-ordered tuple of `app/engine/*.py` modules (a test asserts the tuple equals the sorted
    module glob); `source_revision` = `git rev-parse HEAD` output or `None`; `worktree_dirty` = the
    tri-state result of `git status --porcelain --untracked-files=no -- apps/backend/app`, or `None` when
    git is unavailable. `engine_source_hash` is computed independently of git and is identical across the
    clean/dirty/git-unavailable cases.
  - `build_tape_observation(...)` — the one pure builder: no clock read, no git call, no engine-internal
    import, no import of the classifier or any feature-computation module (AST-checkable). It accepts
    already-resolved inputs (an `EngineSnapshot`; `source_mode`, `data_feed`, `scenario`,
    `window_start_utc`/`window_end_utc`, `dataset_id`/`dataset_checksum`, `session_id`/
    `session_started_at_utc`; `settled_at_utc`; `end_reason`; `generated_at_utc`; `profile_id`; a
    `Config`; the provenance triple) and returns the full `TapeObservation` v1 dict per Constitution §1,
    including the pure-math projections that need no live wiring: `observed_at_utc` (pinned-ISO of
    `epoch_anchor + timestamp`, null per the two null clauses), `available_at_utc`/`availability_basis`
    (per the §2 table, keyed off the caller-supplied `source_mode` and `settled_at_utc` — this iteration
    computes the LAW correctly from its inputs; it does not yet build the machinery that makes those
    inputs genuinely atomic/live-correct, which is iteration 2's job), `trade_event_count` (verbatim
    `snapshot.event_count`), `market.*`, `observations[]`, `lifecycle.*` (verbatim from `snapshot` +
    `end_reason`), `source.*` (verbatim pass-through of the caller's descriptor fields), `engine_identity.*`
    (`ENGINE_SEMANTICS_VERSION`, `config.config_fingerprint()`, `profile_id`, the classifier's closed state
    list, `config.windows`, `config.warmup_min_events`), `implementation_provenance.*` (verbatim from the
    provenance triple), and the two hashes. The builder raises when `profile_id == "default"` but
    `config.config_fingerprint()` differs from the process `CONFIG` fingerprint (the profile refusal); it
    never invents a profile string.
- [ ] Create `apps/backend/tests/test_tape_observation_projection.py` covering, each as a named test
      (per the goal's J-01 Steps.4 list): sentinel-mutation projection is echoed verbatim; an AST guard
      proving the module imports no classifier/feature-computation code and references no threshold, with
      a `test_counterexample_*` proving the guard can fail; `trade_event_count == snapshot.event_count`
      with no re-count; both hashes recomputable from the documented canonical encoding, and key-order
      permutation changes neither; `observation_hash` changes when `engine_semantics_version`,
      `config_fingerprint` or `profile_id` changes, and does NOT change when `engine_source_hash`,
      `worktree_dirty`, `observations[]` wording, `generated_at_utc`, `session_id` or `settled_at_utc`
      changes; `artifact_hash` changes for every one of those metadata changes; clean/dirty/git-unavailable
      provenance triples are distinct while `engine_source_hash` is identical across them; the resolver
      runs once per process (repeated direct calls do not re-invoke git — HTTP-level "no git call per
      request" is re-verified again in iteration 5 once the route exists); the engine-source module tuple
      equals the sorted `app/engine/*.py` set; the profile refusal; the four-group partition covers every
      leaf path exactly once; the schema constants equal `docs/observation-contract-spec.md`'s field table
      (doc-lint); a doc-lint asserting the spec states that exact downstream evidence references use
      `artifact_hash`. Every guard/law test ships a named `test_counterexample_*` proving it can fail.

### Frontend (if applicable)
None — zero frontend files touched this iteration (goal Product Shape: "No page, panel, link or
component is added or modified").

### New user-facing capability
None. This iteration is a pure in-process backend module with no served, watched or visible surface.

### New information displayed
None — `build_tape_observation` is callable in-process by its own test module only; nothing is served by
any endpoint, page or MCP tool yet.

### New user actions
None.

### UI surface changes
None — Cockpit `/`, `/structure`, `/desk` are untouched.

### Product surface delta
None visible. The only artifact of this iteration is two new/changed backend source files plus one new
test module; a user (or browser-qa) sees the exact same product as after iter-0.

### Blueprint conformance
No new surfaces. `runs/goal-session-observation-contract/state/blueprint.md`'s Information Architecture
is unchanged (no page, no nav entry — matches its own "no new surfaces" note). The eventual served home
for everything this iteration builds is already registered there: `GET /tape/{ticker}/observation`
(still not live until iteration ~5).

### Data-contract additions
None. `build_tape_observation` exists as an in-process pure function only this iteration — it is not
served by any endpoint, so no NEW DISPLAYED value exists to register. `blueprint.md`'s existing Data
Contract rows already name `apps/backend/app/observation_contract.py` as the eventual sole computing
module for the machine-observation-semantics and integrity partitions; this iteration builds that module
without changing its registered future computing-module/serving-endpoint pairing. (A status-only edit —
noting the module now exists in-process but is not yet served — is made to `blueprint.md`; this is not a
new value registration.)

## OUT OF SCOPE

- `WatchManager.get_observation_source`, the manager-held atomic settled pair, and the settled-clock
  stamping machinery — Binding Execution Order step 2 (iteration 2, J-02).
- The source/session descriptor's real population at watch creation, and feed-owner agreement across
  fixture datasets — step 3 (iteration 3, J-03).
- `tests/test_tape_observation_time.py`, `_lifecycle_feed.py`, `_path_equivalence.py`, `_route.py`,
  `_guards.py` — later iterations' own modules; this iteration ships only
  `test_tape_observation_projection.py`.
- The `GET /tape/{ticker}/observation` route and any wiring into `apps/backend/app/main.py` — step 5
  (iteration 5, J-05). No route exists after this iteration; `/tape/SIM-BIDABS/observation` still 404s
  (route not found) exactly as at baseline.
- Any MCP change (`get_endpoint` proxy parity is a step-5 concern).
- Any `Config` field addition (the era adds zero; this iteration adds module constants only).
- Any frontend file, page, panel or nav change.
- Real-provider (Alpaca) code paths — the provenance resolver's git calls are local `git` subprocess
  calls only, never a market-data provider call.

## DEFINITION OF DONE

- [ ] `apps/backend/app/observation_contract.py` exists with the schema constants, the four-group
      partition constants, `canonical_encode`, `compute_observation_hash`, `compute_artifact_hash`,
      `resolve_implementation_provenance`, and `build_tape_observation`.
- [ ] `ENGINE_SEMANTICS_VERSION = "tape-engine-v1"` module constant added to `app/engine/tape_engine.py`.
- [ ] `apps/backend/tests/test_tape_observation_projection.py` passes with 0 failures, and every
      `test_counterexample_*` test it ships is present and passes.
- [ ] Full backend suite (`cd apps/backend && .venv/bin/python -m pytest tests/ -q`) still green — no
      fewer than the iter-0 baseline of 3930 passed / 8 skipped / 0 failed, plus this iteration's new
      tests, 0 failed.
- [ ] `Config.config_fingerprint()` is unchanged (`08e471b10130e1e2`); `cd apps/frontend && npx tsc
      --noEmit` reports 0 errors (unaffected — no frontend file touched).
- [ ] Browser-qa confirms zero visible product change: `/`, `/structure`, `/desk` render exactly as at
      iter-0, and `/tape/SIM-BIDABS/observation` still 404s (route not yet built — this is the EXPECTED,
      correct result this iteration, not a failure to fix).
- [ ] No anti-goal violation introduced (scan-report CLEAN).
- [ ] Dev handoff written at `docs/handoffs/goal-observation-contract-iter-1-dev.md`.

Note on J-01's overall journey status: this iteration cannot make J-01 fully pass — its Acceptance
requires the served JSON at `/tape/SIM-BIDABS/observation`, which needs the route (iteration 5). Expect
the evaluator to record J-01 as still `failing` or move it to `partial` on the strength of the passing
`test_tape_observation_projection.py` module, per the lessons-ledger guidance; this is correct, not a
regression.

## TESTING REQUIREMENTS

- Browser: J-01's Sim-mode step only, on the no-screenshot rail — visit `/`, watch `SIM-BIDABS`
  (Simulated), confirm the status dot reads `live`; then confirm `/tape/SIM-BIDABS/observation` still
  answers "Not Found" (route absent, expected); confirm `/structure` and `/desk` render unchanged.
- Unit/integration: `apps/backend/tests/test_tape_observation_projection.py` (new) — see TC-1..TC-15
  below. No integration test needs a running uvicorn server or network access.
- Error cases: profile-fingerprint mismatch raises; git-unavailable provenance yields `(None, None)` for
  `source_revision`/`worktree_dirty` (never fabricated) while `engine_source_hash` is still a valid
  64-hex string; malformed/incomplete `EngineSnapshot` inputs are rejected by the dataclass's own typing,
  not silently coerced.

Test-first contract:

- TC-1: given an `EngineSnapshot` fixture with `tape_state="bid_absorption"`, `confidence=0.83` and a
  patched `features` dict, when `build_tape_observation(...)` is called, then the returned dict's
  `tape_state`, `confidence` and `features` equal the fixture's values byte-for-byte (verbatim echo, no
  recomputation).
- TC-2: given `apps/backend/app/observation_contract.py`'s source, when the AST recompute guard test
  runs, then it asserts the module imports no name from `app.engine.classifier` or any feature-computation
  module and references no numeric threshold literal used by the classifier; `test_counterexample_*`
  inserts such an import into a throwaway fixture module and asserts the guard fails on it.
- TC-3: given a snapshot with `event_count=17`, when `build_tape_observation(...)` runs, then the returned
  `trade_event_count` equals `17` and the test asserts no loop or count call over any trade list exists in
  the builder (AST or source-scan check).
- TC-4: given a built observation dict, when `compute_observation_hash` and `compute_artifact_hash` are
  each called twice — once on the dict as returned, once on a `dict` built by inserting keys in reverse
  order — then both hash values are identical across the two orderings.
- TC-5: given a built observation, when `engine_semantics_version`, then separately `config_fingerprint`,
  then separately `profile_id` is mutated in a copy, then `compute_observation_hash` on the mutated copy
  differs from the original hash in every one of the three cases.
- TC-6: given a built observation, when `engine_source_hash`, then separately `worktree_dirty`, then
  `observations[]` wording, then `generated_at_utc`, then `session_id`, then `settled_at_utc` is mutated in
  a copy, then `compute_observation_hash` on the mutated copy equals the original hash in every one of the
  six cases (unchanged).
- TC-7: given the same six mutations as TC-6, when `compute_artifact_hash` is recomputed on each mutated
  copy, then it differs from the original `artifact_hash` in every one of the six cases.
- TC-8: given three provenance resolutions — clean worktree, dirty worktree, git binary unavailable (each
  via a monkeypatched subprocess call) — when `resolve_implementation_provenance()` runs under each, then
  `source_revision`/`worktree_dirty` differ across the three cases while `engine_source_hash` is identical
  across all three.
- TC-9: given `resolve_implementation_provenance()` is called 5 times in one process, when a monkeypatched
  git-subprocess call counter is inspected, then the underlying git subprocess was invoked at most once
  (memoized, not once per call).
- TC-10: given the sorted glob of `app/engine/*.py`, when compared to the resolver's fixed module tuple,
  then the two sets are equal (`test_counterexample_*` adds a throwaway module to the directory and
  asserts the equality test fails).
- TC-11: given `profile_id="default"` and a `Config` whose `config_fingerprint()` differs from the process
  `CONFIG.config_fingerprint()`, when `build_tape_observation(...)` is called, then it raises (no observation
  dict is returned); given matching fingerprints, then it returns normally.
- TC-12: given the four partition constants (machine-observation semantics / provenance-source-lifecycle
  metadata / explanatory / integrity) and the full Constitution §1 field-path list, when the partition
  coverage test runs, then every leaf path appears in exactly one of the four groups (`test_counterexample_*`
  removes one leaf from all groups and asserts the coverage test fails).
- TC-13: given the schema constants (`OBSERVATION_SCHEMA_VERSION`, `PROVIDER`, and the full field-owner
  table) and `docs/observation-contract-spec.md`'s field table, when the doc-lint test runs, then the two
  are identical with 0 differences, and a second assertion confirms the spec's text states that exact
  downstream evidence references use `artifact_hash`.
- TC-14: given `SIM-BIDABS` watched live via the Cockpit and `/tape/SIM-BIDABS/observation` requested over
  HTTP, when browser-qa performs the request, then the response is a 404 "Not Found" body identical in
  shape to the iter-0 baseline screenshot (expected — the route lands at iteration 5).
- TC-15: given the full backend suite, when `cd apps/backend && .venv/bin/python -m pytest tests/ -q` is
  run, then the pass count is >= 3930 (iter-0 baseline) plus the count of tests newly added in
  `test_tape_observation_projection.py`, with 0 failed, and `Config.config_fingerprint()` still returns
  `08e471b10130e1e2`.

## NOTES

- Applying the lessons-ledger entry (iter-0, applies to iterations 1-4): a flat journey table this
  iteration (J-01 not fully unlocked) is the expected, correct signal — do not read it as a stall and do
  not move the route earlier. The evaluator should score this iteration primarily on
  `test_tape_observation_projection.py`'s pass/fail and the honest absence of the route, not on J-01's
  merged verdict alone.
- Assumption logged to `runs/goal-session-observation-contract/state/assumptions.md` (iter-1): this spec
  reads the Binding Execution Order's step 1 ("the builder") as requiring `build_tape_observation` to
  produce the COMPLETE v1 schema now (including the pure-math time/lifecycle/source projections), with
  only the WIRING that makes its inputs genuinely correct deferred to steps 2/3/5 — because the four-group
  partition-coverage trap (Required Trap Coverage item 13) can only be satisfied this iteration if every
  leaf field already exists in the builder's output.
- The pytest venv (9.1.1) prints no final "N passed" summary line; tally via `-q` progress characters or
  `--collect-only -q` per-file counts, per the iter-0 lessons entry — do not grep for a summary line that
  never appears.
