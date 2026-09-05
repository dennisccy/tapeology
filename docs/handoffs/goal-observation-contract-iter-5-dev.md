# goal-observation-contract-iter-5 Dev Handoff

**Phase:** goal-observation-contract-iter-5
**Date:** 2026-09-04
**Agent:** developer
**Status:** complete

## What Was Built

- New route `GET /tape/{ticker}/observation` in `apps/backend/app/main.py` (Binding Execution Order
  step 5, J-05) -- the one read-only machine path for the `TapeObservation` v1 artifact, completing
  the served-JSON half of J-01 through J-05 in one small, transport-only addition:
  - Looks up `manager.get_observation_source(ticker)` (the ONE atomic managed-observation read,
    already built in iterations 2-3).
  - When it returns `None`, raises `HTTPException(404, "Ticker '{ticker}' is not being watched")`
    -- byte-for-byte the same detail string `_engine_or_404` raises for every sibling `/tape/*`
    route, since `get_observation_source` checks the identical `self._engines.get(ticker) is None`
    condition `_engine_or_404` itself checks.
  - Otherwise unpacks the atomic `(snapshot, settled_at_utc, end_reason, SourceDescriptor)` 4-tuple
    and calls `build_tape_observation(...)` (already built in iteration 1) with the descriptor's
    fields verbatim, `generated_at_utc` from a new tiny `_now_utc()` seam (mirrors `_iso_utc`'s own
    per-module-helper convention; a test can freeze it via `monkeypatch.setattr(main, "_now_utc",
    ...)` instead of patching the stdlib `datetime` class), and
    `resolve_implementation_provenance()`'s already-cached triple.
  - Calls no `TapeEngine` method and performs no computation of its own -- proven by an AST/source
    guard in the new test module (see below), never `manager.get(ticker)` or `.snapshot()`.
- New test module `apps/backend/tests/test_tape_observation_route.py` (8 tests, 0 failed) covering
  the backend-pytest slice of the Definition of Done (TC-8 through TC-15):
  - `test_route_consumes_the_atomic_read_and_calls_no_tape_engine_method` (TC-8) + its
    `test_counterexample_engine_method_scan_detects_an_injected_snapshot_call` (TC-10): the scan
    introspects `TapeEngine`'s own real public method names dynamically (never a hand-guessed list)
    and proves the route's own source calls none of them, with a counter-example (a copy of the
    route source with an injected `manager.get(ticker).snapshot()` call) proving the same scan can
    fail.
  - `test_404_parity_with_tape_state_for_an_unwatched_ticker` (TC-9): `/tape/ZZZZ/observation` and
    `/tape/ZZZZ/state` return the identical 404 status and body.
  - `test_route_output_equals_builder_output_field_for_field_with_frozen_now` (TC-11) +
    `test_counterexample_route_builder_equality_comparator_detects_a_mutated_field` (TC-15): with
    `_now_utc` frozen and the watch paused (so the route's own read and the test's own follow-up
    `get_observation_source` call observe the identical atomic pair), the route's parsed JSON is
    asserted `==` to `build_tape_observation`'s direct output for the same read; the counter-example
    mutates a real built observation's `tape_state` in a deep copy and proves the same `==` check
    fails.
  - `test_hashes_recomputable_from_served_json` (TC-12): `observation_hash`/`artifact_hash`
    recompute from the served JSON via the existing §6 canonical-encoding functions.
  - `test_get_starts_no_watch_computation_or_git_call_across_100_requests` (TC-14): monkeypatches
    `manager.get_observation_source` and `observation_contract._run_git` to count calls; 100
    consecutive GETs against an already-watched, paused ticker show exactly 100 manager reads and 0
    git calls (the provenance memo is warmed before counting, mirroring real process lifetime).
  - `test_mcp_get_endpoint_bytes_equal_rest_bytes_against_real_uvicorn` (TC-13): a self-contained
    real-uvicorn-subprocess fixture (the same pattern `test_mcp_server.py` establishes, not imported
    -- this module owns its own tiny fixture per the repo's per-module convention) proves the MCP
    `get_endpoint` proxy and a direct REST GET agree field-for-field and share the same
    `observation_hash`, with the MCP-served document's own hashes independently recomputable (proof
    the proxy performs zero transformation). **One necessary, explicitly-documented adjustment from
    a literal full-body byte comparison — see Known Issues.** The 28-tool pin is reconfirmed inline.
- Fixed the carried-forward vacuous counter-example (TC-16):
  `test_tape_observation_path_equivalence.py::test_counterexample_field_partition_drift_is_detected`
  previously built a `widened` tuple and compared it only to a second hand-written literal, never
  touching the real subject. Rewrote it to `monkeypatch.setattr` the REAL
  `observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS` attribute with the widened tuple and
  show the module's own real partition-equality check (the same assertion
  `test_field_partition_groups_are_unchanged_from_iteration_1` makes) fails against it.
- Rewrote the three stale golden replay scripts so none still asserts the route is absent (TC-17):
  - `journey-scripts/J-01.json` step 5: `"Not Found"` -> `"\"schema_version\": \"tape-observation-v1\""`.
  - `journey-scripts/J-03.json` step 11 (after the Stop + re-Watch sequence): `"Not Found"` ->
    `"\"source_mode\": \"sim\""` (matching that step's own J-03 acceptance clause).
  - `journey-scripts/J-04.json` steps 6-7 (was steps 6-9: Resume/Stop/404/404): rewritten to follow
    the CURRENT `docs/goal.md` J-04 Step 1 text exactly -- Watch -> Pause -> two reloads of
    `/tape/SIM-BIDABS/observation`, each now expecting `"\"observation_hash\""` (real, honestly
    served content) instead of a post-Stop `"404"`. The old Resume/Stop steps were removed since
    they are no longer part of the current J-04 Step 1 sequence.
- `apps/backend/app/observation_contract.py`, `apps/backend/app/watch_manager.py`, and
  `apps/backend/app/mcp/__init__.py` are all **unmodified** -- confirmed by direct inspection and
  `git status`, exactly per OUT OF SCOPE.

## Files Changed

- `apps/backend/app/main.py` -- one new import line, the `_now_utc()` helper, and the
  `GET /tape/{ticker}/observation` route (+48/-0 lines; nothing else touched).
- `apps/backend/tests/test_tape_observation_route.py` (new, 399 lines, 8 tests) -- the route-level
  proof described above.
- `apps/backend/tests/test_tape_observation_path_equivalence.py` (+13/-6 lines) -- TC-16 fix only;
  no test added or removed, same test name.
- `runs/goal-session-observation-contract/journey-scripts/J-01.json` (1 line changed).
- `runs/goal-session-observation-contract/journey-scripts/J-03.json` (1 line changed).
- `runs/goal-session-observation-contract/journey-scripts/J-04.json` (4 lines removed, 2 changed --
  net 7 lines shorter).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **4044 passed, 8 skipped, 0 failed** (4052 collected; exit code 0) -- exactly iter-4's 4036
baseline plus this iteration's 8 net-new tests (`test_tape_observation_route.py`), 8 skipped
unchanged, 0 regressions. The venv's pytest prints no final "N passed" summary line, so this was
tallied by counting `-q` progress characters directly from the captured output (`.`=4044, `s`=8,
`F`=0, `E`=0), per the iter-0 lessons entry, and cross-checked against an independent
`--collect-only -q` per-file-count sum (4052 collected) -- the two tallies agree exactly.

Also run individually before/alongside the full-suite pass:
- `tests/test_tape_observation_route.py` -- 8 passed, 0 failed.
- `tests/test_tape_observation_path_equivalence.py` -- 6 passed, 0 failed (unchanged count; one
  test body rewritten, none added/removed).
- The full observation-contract + MCP + API regression set together
  (`test_tape_observation_route.py test_tape_observation_path_equivalence.py
  test_tape_observation_projection.py test_tape_observation_time.py
  test_tape_observation_lifecycle_feed.py test_mcp_server.py test_api.py`) -- 194 passed, 0 failed.
- `Config.config_fingerprint()` -- confirmed `08e471b10130e1e2` (unchanged from the pinned value).
- `cd apps/frontend && npx tsc --noEmit` -- 0 errors (exit code 0; no frontend file touched, as
  expected).

## Manual verification (live backend, real HTTP, not mocked)

Started both services via `scripts/dev.sh` (backend :8301, frontend :3301 -- this repo's
deterministic per-path port offset). Confirmed `GET /health` -> `{"status":"ok"}` and `GET /` ->
200. Stopped both (`kill -9` on the bound ports), confirmed the ports were clear, started `dev.sh`
again to verify a clean restart with no port conflicts -- both came back up cleanly.

With the backend live, exercised the ENTIRE J-01 through J-09 acceptance surface with real curl
calls against the real running app (not TestClient, not mocked):
- Watched `SIM-BIDABS`; polled `/tape/SIM-BIDABS/observation` before and after settling -- confirmed
  `schema_version: tape-observation-v1`, `provider: tapeology`, every named top-level key present,
  `engine_identity.engine_semantics_version = tape-engine-v1`,
  `engine_identity.config_fingerprint = 08e471b10130e1e2`, `engine_identity.profile_id = default`,
  a non-empty `source.session_id`, a `Z`-suffixed `source.session_started_at_utc`, a real 64-hex
  `implementation_provenance.engine_source_hash`, a `source_revision` that matched
  `git rev-parse HEAD` exactly, `worktree_dirty: true` (honest -- the worktree genuinely has
  uncommitted changes right now), a 64-hex `observation_hash`, and a 64-hex `artifact_hash`.
- Confirmed `observed_at_utc` starts `2024-01-02T14:3...` (the synthetic sim anchor),
  `available_at_utc: null`, `availability_basis: simulated_not_applicable`, and
  `timing.settled_at_utc` / `generated_at_utc` both carried today's real date (TC-3).
- Pressed Pause via `POST /watch/SIM-BIDABS/pause`; two live reloads of the observation JSON while
  paused showed `lifecycle.stream_status: paused`, `lifecycle.paused: true`, an unchanged
  `tape_state`, an unchanged `timing.settled_at_utc`, an **identical** `observation_hash` across the
  two reloads, and **different** `generated_at_utc` / `artifact_hash` between them -- TC-4 and TC-7
  both verified live.
- Pressed Resume (`stream_status` -> `live`), then Stop (`DELETE /watch/SIM-BIDABS`) -- the
  observation route then returned a real live 404 (TC-5).
- Re-watched `SIM-BIDABS` -- the observation JSON showed a **new** `source.session_id` (different
  from the pre-Stop value), with `source.source_mode: sim` and `source.data_feed: sim` unchanged
  (TC-6).
- `GET /tape/ZZZZ/observation` and `GET /tape/ZZZZ/state` returned byte-identical bodies
  (`{"detail":"Ticker 'ZZZZ' is not being watched"}`) at 404 (TC-9).
- Spot-checked `/`, `/structure`, `/desk` on the live frontend -- all three returned 200 with no
  code changes underneath them (zero frontend files touched this iteration).

Both services were stopped again (ports confirmed clear) before finishing, per the server-cleanup
rule.

## Self-check (anti-goal spot scan)

Grepped every file touched this iteration for the era's actionability/external-system tokens
(`READY`, `NO_TRADE`, `NO_VERDICT`, `trade_allowed`, `PENDING_CONDITION`, `Workstation`, `Trendora`,
`TenSteps`, `composite_policy`, `should_trade`, `entry_price`, `stop_loss`, `position_size`) -- zero
matches. Confirmed no `Config` field was added (`git diff apps/backend/app/config.py` is empty), no
frontend file changed, no new named MCP tool or edit to `apps/backend/app/mcp/__init__.py`, no CLI or
WebSocket addition, and no widening of the field-partition constants (only the counter-example test
body changed; the constants themselves are read, never edited). `Config.config_fingerprint()`
confirmed unchanged (`08e471b10130e1e2`). The formal goal-mode diff-scan step (TC-20) is a downstream
pipeline stage, not run by this developer pass.

## Definition of Done -- verification against the spec

- [x] `GET /tape/SIM-BIDABS/observation` (watched live) returns HTTP 200 with the complete v1 field
  set and the identity/provenance values J-01 names -- verified both by
  `test_tape_observation_route.py` and live curl (TC-1, TC-2).
- [x] `GET /tape/ZZZZ/observation` (never watched) returns a 404 body in the same shape as
  `/tape/ZZZZ/state` -- verified both ways (TC-9).
- [x] The three honest time fields and `availability_basis` are correct for the Sim basis -- live
  curl confirmed (TC-3).
- [x] A full Watch -> Pause -> Resume -> Stop -> re-Watch cycle is visible end-to-end on the served
  JSON -- live curl confirmed every clause (TC-4, TC-5, TC-6).
- [x] Two reloads of a paused watch's observation show identical `observation_hash` and different
  `generated_at_utc` / `artifact_hash` -- live curl confirmed (TC-7).
- [x] `test_tape_observation_route.py` passes with 0 failures, `test_counterexample_*` included,
  proving TC-10 through TC-15.
- [x] `test_tape_observation_path_equivalence.py`'s `test_counterexample_field_partition_drift_is_detected`
  now perturbs the real `observation_contract` constant (TC-16).
- [x] None of the three golden replay scripts still assert the route is absent (TC-17).
- [x] Full backend suite green, pass count no lower than iter-4's 4036-passed baseline plus this
  iteration's net new tests -- **4044 passed / 8 skipped / 0 failed** (4036 + 8 net-new, exact
  match, 0 regressions).
- [x] `cd apps/frontend && npx tsc --noEmit` reports 0 errors.
- [x] `/`, `/structure`, `/desk` render exactly as before -- live spot check, all three 200, zero
  frontend files touched.
- [x] No anti-goal violation introduced (self-check scan clean; the formal scan-report/coherence
  steps are downstream pipeline stages).
- [x] Dev handoff written at this path.

## Known Issues

**TC-13's MCP byte-identity test required one necessary, explicitly-documented adjustment from a
literal full-body byte comparison.** `TapeObservation` v1 embeds `generated_at_utc` (the route's own
wall-clock read at generation time) and `artifact_hash` (derived from it) -- both are, BY DESIGN
(Constitution §2/§6, and the very TC-7 behavior verified live above), honestly different on every
independent read of the same underlying snapshot. `test_mcp_get_endpoint_bytes_equal_rest_bytes_against_real_uvicorn`
makes two genuinely separate HTTP requests (one direct REST GET, one through the MCP tool's own
independent proxied GET), so a literal byte-for-byte comparison of the two FULL response bodies can
never pass -- not a bug in the route or the MCP proxy, a mathematical certainty of two independently
generated timestamps. I confirmed this empirically (the first version of the test failed exactly and
only on `generated_at_utc`/`artifact_hash`, every other byte identical) before adjusting the test to:
(1) assert `observation_hash` -- the stable machine-observation equivalence identity -- matches
between the two responses; (2) assert every OTHER field is byte-identical (both documents with
`generated_at_utc`/`artifact_hash` stripped compare `==`); and (3) independently recompute both
hashes from the MCP-served document to prove the proxy did not corrupt anything in transit. This is
documented in the test's own docstring/comments. No existing MCP byte-identity test in
`test_mcp_server.py` embeds a similarly time-varying field, so there was no established precedent to
follow here -- this is a genuine, first-of-its-kind case for this specific route's honest design,
not a corner cut. Flagging this explicitly per the "record a genuine gap in the handoff rather than
silently expand or narrow scope" instruction, so the reviewer/QA/auditor can independently judge
whether this interpretation of "byte-identical" (TC-13's own wording) is acceptable; I believe it is
the only interpretation that is both literally achievable and faithful to the contract's own honest
non-determinism guarantee.

No other gaps found. On direct inspection the new route, the new test module, and both fixups match
the iteration spec's IN SCOPE list, OUT OF SCOPE exclusions, and Test-first contract exactly.
`apps/backend/app/observation_contract.py`, `apps/backend/app/watch_manager.py`, and
`apps/backend/app/mcp/__init__.py` were read but not modified, confirming the BACKGROUND section's
claim that no further hardening was needed there this iteration.

One honest limitation of the three rewritten golden replay scripts (J-01/J-03/J-04): the deterministic
replay runner (`demo_runner.py`) resolves every `goto` URL against the single frontend `base_url`
(`normalize_url` rewrites even an absolute `localhost`/`127.0.0.1` URL's port to match it), and the
frontend has -- correctly, per this era's own "no frontend file changes" constraint -- no page at
`/tape/{ticker}/observation`. This means a mechanical replay of these specific `goto` steps will
render Next.js's own default not-found page, not the backend's JSON, regardless of the backend route
existing. I fixed the specific stale assertions the iteration spec named (none now expects "Not
Found" or "404" -- TC-17's literal text), matching the exact wording of each step's own current
J-0X acceptance clause; I was not able to find a way to make a demo_runner golden script literally
cross the frontend/backend origin boundary (there genuinely is no rewrite/proxy configured between
them in this project, confirmed by inspecting `next.config.mjs` and the start scripts). The real
J-01/J-03/J-05 acceptance is exercised by the browser-qa-agent driving the browser directly to the
backend's own origin (as its own agent instructions already describe for machine-JSON paths), not by
this replay mechanism -- and the pipeline's own replay-lane reconciliation logic already treats a
golden-script false FAIL as non-blocking (re-confirmed by the LLM lane, never a hard failure), so
this is a bounded, self-healing limitation rather than a pipeline risk. Recording this for the
record rather than silently declaring the fix complete.
