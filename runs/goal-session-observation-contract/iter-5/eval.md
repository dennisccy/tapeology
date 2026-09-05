# Iteration 5 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The web address `/tape/{ticker}/observation` now works. Watching the simulated ticker
SIM-BIDABS and then opening that address shows the whole observation record instead of an
error page, and I read that record myself in three screenshots taken this round. Four
journeys move to passing: J-01 "The artifact is a pure projection", J-02 "Three honest
instants", J-03 "Lifecycle, feed and session stay honest" and J-05 "One read-only machine
path". Two are not done: J-04 "Same result from both ingestion paths" was never opened in a
browser this round, and J-06 "Guards and the sentinel" was skipped because the round ran out
of time. I also found a real problem in the test tooling, not in the product: the automatic
replay tool always opens web addresses on the page server, which has no such address, so it
reported three false failures.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The artifact is a pure projection with semantic identity, provenance and integrity | partial | **passing** | `reports/qa/goal-observation-contract-iter-5-evidence/UT-J-01-result.png` (I opened it: `"schema_version":"tape-observation-v1"`, `engine_semantics_version":"tape-engine-v1"`, `config_fingerprint":"08e471b10130e1e2"`, `profile_id":"default"`, `session_id":"c51880f7bec148eeafa0b27d8248bd65"`, 64-hex `observation_hash` + `artifact_hash`, 64-hex `engine_source_hash`, 40-hex `source_revision`, `worktree_dirty":true`) + row `UT-J-01` PASS in `reports/phase-goal-observation-contract-iter-5-ui-test-results.canary.md` + my own run of `tests/test_tape_observation_projection.py` = 38 passed, 0 failed, 5 `test_counterexample_*` present |
| J-02 Market-event time, measured availability and generation time are three distinct, honest instants, read atomically | partial | **passing** | Same screenshot `UT-J-01-result.png` — it is the served JSON for the exact browser sequence J-02 Step 1 prescribes, and every Acceptance value is legible in it: `observed_at_utc":"2024-01-02T14:31:08.500000Z"` (begins `2024-01-02T14:3`), `available_at_utc":null`, `availability_basis":"simulated_not_applicable"`, `generated_at_utc":"2026-09-05T00:34:22.915539Z"` and `timing…settled_at_utc":"2026-09-05T00:34:22.887143Z"` (both today) + my own run of `tests/test_tape_observation_time.py` = 33 passed, 0 failed, interleaving test `test_atomic_read_never_mispairs_snapshot_n_plus_1_with_settled_time_n` and its counter-example present by name. Scoring note in `state/assumptions.md` (no browser row ran J-02's own numbered steps). |
| J-03 Lifecycle, feed basis and session identity stay honest | partial | **passing** | `reports/qa/goal-observation-contract-iter-5-evidence/UT-J-03-result.png` (I opened it: `stream_status":"live"`, `source_mode":"sim"`, `data_feed":"sim"`, `session_id":"6bb9aa2c7d3e482294949bdc23dda96c"` — genuinely different from J-01's pre-Stop `c51880f7bec148eeafa0b27d8248bd65`, so the re-watch really did start a new session) + row `UT-J-03` PASS in `…-ui-test-results.canary.md` (full live→paused→live→404→re-watch cycle, 404 body quoted) + my own run of `tests/test_tape_observation_lifecycle_feed.py` = 29 passed, 0 failed. Scoring note in `state/assumptions.md` (the "settled time unchanged across the pause" clause). |
| J-04 Ingestion-path equivalence under an identical valid event stream | partial | **partial** (unchanged) | Deterministic half green: my own run of `tests/test_tape_observation_path_equivalence.py` = 6 passed, 0 failed, and I read the repaired counter-example in `runs/goal-session-observation-contract/iter-5/iter-diff.md` — it now perturbs the real `observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS` via `monkeypatch`. Served-JSON half NOT verified: the only capture, `reports/qa/goal-observation-contract-iter-5-evidence/J-04-verify.png`, is the page server's own "404 — This page could not be found" screen (byte-identical, same md5 `cdcf05e2…`, to `J-01-verify.png` and `J-03-verify.png`), i.e. the wrong origin. Row `UT-J-04` in the merged results is SKIP. |
| J-05 One read-only machine path | failing | **passing** | `reports/qa/goal-observation-contract-iter-5-evidence/UT-J-05-result.png` (I opened it: the complete artifact with `"schema_version":"tape-observation-v1"`, served from the backend origin in Chrome's JSON viewer) + row `UT-J-05` PASS in `reports/phase-goal-observation-contract-iter-5-ui-test-results.md` (unwatched-ticker body `{"detail":"Ticker 'ZZZZ' is not being watched"}` confirmed byte-identical to `/tape/ZZZZ/state`) + my own run of `tests/test_tape_observation_route.py` = 8 passed, 0 failed, both `test_counterexample_*` included |
| J-06 Guards and the regression sentinel | partial | **partial** (carried over — NOT tested) | Row `UT-J-06` is `DEFERRED-BUDGET` in `reports/phase-goal-observation-contract-iter-5-ui-test-results.md`; independently, `apps/backend/tests/test_tape_observation_guards.py` still does not exist (I checked) — it is Binding Execution Order step 6, not yet built |

Deterministic replay note: `reports/phase-goal-observation-contract-iter-5-regression-replay-results.md`
reported FAIL for J-01, J-03 and J-04, then VOIDED all three under the mass-false-FAIL breaker after the
canary re-check came back green. I confirmed the void was correct: the three `*-verify.png` captures are
one and the same page-server 404 image, so the replay never reached the backend at all.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | `runs/goal-session-observation-contract/iter-5/scan-report.md` — "CLEAN — no secret, dependency, or license findings on added lines" (tracked + 1 untracked file scanned) |
| Paid / external SaaS dependency | OK | Same scan, no dependency findings; no manifest file appears in the iteration diff (3 files only: `apps/backend/app/main.py`, `apps/backend/tests/test_tape_observation_route.py`, `apps/backend/tests/test_tape_observation_path_equivalence.py` — confirmed by my own `git status --porcelain -- apps/`) |
| License change | OK | Same scan, no license findings; no LICENSE file in the diff |
| Fabricated / substituted data presented as real | OK | The three PASS screenshots are Chrome's JSON viewer over real backend responses (`Pretty-print` checkbox, real 64-hex hashes, real session ids that differ across a Stop/re-Watch). No fixture stood in for a real view |
| Rail 1 — no execution path | OK | `apps/backend/tests/test_no_execution_path.py` untouched (my own `git status` check); no order/broker code added |
| Rail 3 — frozen foundations | OK | `apps/backend/app/engine/`, `config.py`, `observation_contract.py`, `watch_manager.py`, `mcp/` all untouched (my own `git status` check); I ran `Config.config_fingerprint()` myself = `08e471b10130e1e2`, unchanged |
| Rail 6 — single source of truth | OK | `runs/goal-session-observation-contract/iter-5/coherence.md` = **COHERENCE-PASS**, no blocking violations, no advisory notes. The route re-computes nothing: it passes the atomic read straight into the one builder |
| Rail 8 — read-only MCP | OK | `apps/backend/app/mcp/` not in the diff; the existing `/tape/` prefix allowlist covers the new path; `test_mcp_get_endpoint_bytes_equal_rest_bytes_against_real_uvicorn` passed in my own run |
| Era — no route that snapshots an engine; atomic manager read only | OK | I read the route in `iter-diff.md`: its only data call is `manager.get_observation_source(ticker)`. The guard `test_route_consumes_the_atomic_read_and_calls_no_tape_engine_method` introspects `TapeEngine`'s real method surface and scans the real route source; its counter-example injects `manager.get(ticker).snapshot()` into that same real source and proves the scan catches it |
| Era — no `available_at_utc` that is not a manager-measured settled instant | OK | Served value is `null` with `availability_basis":"simulated_not_applicable"` on the sim basis (seen in all three screenshots); `test_counterexample_copying_event_time_into_available_at_utc_is_caught` present and passing |
| Era — no pooling / equating of `sim`, `iex`, `sip` | OK | Served `source_mode":"sim"` and `data_feed":"sim"` throughout; no feed-mapping code added |
| Era — no invented git provenance, no git call per request | OK | `test_get_starts_no_watch_computation_or_git_call_across_100_requests` counts real calls through `observation_contract._run_git` and asserts 0 across 100 requests — I read the body and ran it |
| Era — no new UI page/panel/link/component, no new `Config` field, no named MCP tool, no CLI, no WebSocket embedding, no listing endpoint | OK | Zero files under `apps/frontend/`; `config.py` and `mcp/__init__.py` untouched (my own `git status` check); the one added address is a single-ticker GET |
| Era — no weakening of any existing guard | OK | I checked all nine named guard files with `git status`: none modified |
| Era — no actionability field or token in the artifact | OK | I read the full served JSON in three screenshots: no `READY`, `NO_TRADE`, `trade_allowed`, `PENDING_CONDITION` or equivalent anywhere; the dev handoff's own token grep also came back empty |
| Era — no mandatory journey/test needing Alpaca, network, credentials or market hours | OK | Everything verified ran on the simulated feed and committed fixtures |
| Goal-Mode — no workaround that edits/skips/xfails a guard to pass a journey | OK | No guard edited, nothing skipped or xfailed; the three rewritten replay scripts assert the real served content the iteration spec called for |
| Goal-Mode — no browser proof from a fabricated state | OK | See "fabricated data" row |

Ledger (`anti_goal_disposition.py summary`): **total=0, resolved=0, unresolved_blocking=0,
unresolved_non_blocking=0, unresolved_critical=0.**

## Next-Step Recommendation

Build the last block, J-06 "Guards and the regression sentinel": the missing test file
`apps/backend/tests/test_tape_observation_guards.py`, then the whole-product re-check (all
backend tests, the frontend compile check, the settings fingerprint, and the three pages
Cockpit, Structure and Desk loading with nothing new on them).

In the same round, close the two verification gaps this round left, because they are what
stands between the project and a clean finish:

1. Have the browser tester open the observation address itself for **J-04 "Same result from
   both ingestion paths"**: watch SIM-BIDABS, press Pause, then reload the address twice and
   show that the content identity stays the same while the generation time and the record
   identity differ. Save a screenshot of each reload. Today the only picture we have for J-04
   is the page server's error screen.
2. Have the browser tester also run **J-02 "Three honest instants"** as its own numbered
   steps, so its record no longer rests on a picture filed under another journey's name.

Also fix, or work around in writing, the tooling problem found this round: the automatic
replay tool sends every address to the page server, which has no `/tape/...` address, so it
will keep reporting false failures for J-01, J-03 and J-04 and no saved script exists for
J-05. Until that is fixed, the browser tester must be the one that checks these journeys.

Next iteration should run at **full** depth — it is the final block, it carries the whole
product re-check, and this round showed the automatic checks cannot be trusted on their own.

## Halt Justification (if halting)

Not halting. ESCALATE only pins the next iteration to the full pipeline; the loop continues.
