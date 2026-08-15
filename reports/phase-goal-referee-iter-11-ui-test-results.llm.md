# Phase N — UI Test Results

**Phase:** goal-referee-iter-11
**Date:** 2026-08-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — reconciliation made testable | regression | P1 | `test_referee_guards.py` (spec-drift + zero-lens-diff + catalog-pin guards) + the 3 J-01 readiness-fold tests in `test_referee_evidence.py` all pass | Ran to completion: `22 passed, 2 warnings in 1.64s`, exit code 0 | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-02 | The evidence contract — two families, one observation shape | regression | P1 | Full `test_referee_evidence.py` (26 tests) passes | Ran to completion: `26 passed, 2 warnings in 2.33s`, exit code 0 | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-03 | The statistics core — calibrated, seeded, oracle-proven, fail-closed | regression | P1 | `test_referee_stats.py` (48) + `test_referee_oracles.py` (11) pass within `REFEREE_ORACLE_BUDGET_SECONDS` (120s) | Ran to completion: `59 passed in 87.57s (0:01:27)`, exit code 0 — within the 120s oracle budget | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-04 | Matched nulls — comparable times, identical measurement | regression | P1 | `test_referee_null.py` (36 tests) passes | Ran to completion: `36 passed, 2 warnings in 1.73s`, exit code 0 | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-05 | The registry — pre-registration with an immutable boundary | regression | P1 | `test_referee_registry.py` (47 tests) passes | Ran to completion: `47 passed, 2 warnings in 1.69s`, exit code 0 | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-06 | Estimand engines + adjudication — one checkpoint, recorded forever | regression | P1 | `test_referee_adjudicate.py` (57 tests) passes | Ran to completion: `57 passed, 2 warnings in 6.43s`, exit code 0 | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-08 | The strategy family + the promotion interlock — fail closed, no bypass | regression | P1 | `test_pnl_scan.py` (30 tests, incl. `test_no_bypass_path_exists_for_authorize_promotion` + `test_tc3`..`test_tc7` refusal classes) passes | Ran to completion: `30 passed in 7.99s`, exit code 0; all named tests confirmed present and passing | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-09 | The Referee on `/desk` + MCP contract v5 — single-flight refusal screenshot (owed evidence) | error | P1 | On the scoped fixture rig, a null build for `referee-null-tod-v1` started from a second channel while still running, then a fresh `/desk` load + Referee Runs expand + "Build Null" click for the same spec renders the exact line "Refused — a null build is already running for this spec." — with a screenshot checksum DISTINCT from the shared `d3065788c71ecfcc5623b7704ad6de73` | Confirmed via `assert_scoped_qa_backend.py` (scoped, exit 0) immediately before the write; a second-channel loop of direct `POST /research/desk/referee/nulls/compute` calls kept a build running; a fresh `/desk` load → expanded "Referee Runs" → clicked "Build Null" for `referee-null-tod-v1` rendered `data-testid="referee-null-build-trigger-error-referee-null-tod-v1"` = "Refused — a null build is already running for this spec. Wait for it to finish, then try again." — visible in the screenshot; md5 of new screenshot = `5baf7d31fdc1b73101ed7ec264d97a94`, confirmed DIFFERENT from `d3065788c71ecfcc5623b7704ad6de73` | PASS | `reports/qa/goal-referee-iter-11-evidence/UT-J-09-result.png` |

---

## Passed Tests

### UT-J-01 — The era transition stands — reconciliation made testable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-11-test.log`
- Keyless/automated journey (no dedicated browser surface — its UI reveals land inside J-09's own Referee sections, per goal.md). Ran `apps/backend/tests/test_referee_guards.py` (all 19 tests: spec-drift guard for `playbook-band-context-v3` + zero-diff-to-`desk_playbook_context.py` guard + the `research-directions.md` catalog-pin guard) plus the 3 named J-01 readiness-fold tests in `test_referee_evidence.py` — `test_playbook_readiness_pools_newest_per_date_at_the_current_basis`, `test_strategy_readiness_counts_datasets_splits_and_trades`, `test_strategy_readiness_names_the_unmet_tick_gate_and_the_forming_bar_caveat`. Result: 22/22 passed, exit code 0.

### UT-J-02 — The evidence contract — two families, one observation shape
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-11-test.log`
- Keyless/automated. Ran the full `test_referee_evidence.py` (26 tests: observation contract, both adapters, the derived-observation cache cold/warm/deleted, dedup/coverage-shrink disclosure). Result: 26/26 passed, exit code 0.

### UT-J-03 — The statistics core — calibrated, seeded, oracle-proven, fail-closed
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-11-test.log`
- Keyless/automated. Ran `test_referee_stats.py` (48 tests) + `test_referee_oracles.py` (11 tests, "the oracle suite is green and IS the acceptance" per goal.md) together. Result: 59/59 passed in 87.57s wall-clock, comfortably inside the 120s `REFEREE_ORACLE_BUDGET_SECONDS` ceiling; exit code 0.

### UT-J-04 — Matched nulls — comparable times, identical measurement
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-11-test.log`
- Keyless/automated. Ran `test_referee_null.py` (36 tests). Result: 36/36 passed, exit code 0.

### UT-J-05 — The registry — pre-registration with an immutable boundary
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-11-test.log`
- Keyless/automated. Ran `test_referee_registry.py` (47 tests). Result: 47/47 passed, exit code 0.

### UT-J-06 — Estimand engines + adjudication — one checkpoint, recorded forever
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-11-test.log`
- Keyless/automated. Ran `test_referee_adjudicate.py` (57 tests). Result: 57/57 passed, exit code 0.

### UT-J-08 — The strategy family + the promotion interlock — fail closed, no bypass
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-11-test.log`
- Keyless/automated. Ran `test_pnl_scan.py` (30 tests). Result: 30/30 passed, exit code 0. Confirmed the specific named tests are present and passing among the 30: `test_no_bypass_path_exists_for_authorize_promotion`, `test_no_bypass_guard_can_fail_on_a_seeded_violation`, `test_tc3_a_stale_config_fingerprint_certificate_refuses`, `test_tc4_a_certificate_for_a_different_profile_refuses_wrong_candidate`, `test_tc5_a_mismatched_train_dataset_pin_refuses`, `test_tc6_a_certificate_with_a_failed_gate_refuses`, `test_tc7_a_malformed_certificate_store_refuses_and_never_crashes_promote`.

### UT-J-09 — The Referee on `/desk` + MCP contract v5 — 22 read-only tools (single-flight refusal capture)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-11-evidence/UT-J-09-result.png`
- This iteration's only genuine browser task: J-09's two other acceptance screenshots (empty state, populated registry with verdict chips) already carry real evidence from iteration 10 and were not re-shot (`Depth: evidence`, zero code change, `evidence_makeup` was scoped to exactly one clause). Mechanics used to capture the owed single-flight-refusal screenshot:
  1. Confirmed the backend at `http://localhost:8301` is the scoped fixture rig via `apps/backend/.venv/bin/python apps/backend/scripts/assert_scoped_qa_backend.py` — `SCOPED ... source_url='fixture-rig-iter8-replay'`, exit 0 — run immediately before the write, and again re-confirmed right before the capture sequence.
  2. Root-caused why a plain double-click cannot produce the refusal: `RefereeNullComputeManager` is single-flight PER PROCESS, in-memory, keyed by `null_spec_id` (`referee_null.py:983`) — only a second POST landing at the SAME running backend process while a job is in flight can trigger `started: false`; the standalone CLI runs in its own process and does not share this state. A timing probe (direct POST + tight-poll) measured this fixture corpus's `referee-null-tod-v1` build at ~88 ms (126/126) — far too fast for a manual navigate+expand+click sequence to land inside naturally.
  3. Started a second channel: a bounded (600s safety cap), stop-file-controlled background loop issuing back-to-back direct `POST /research/desk/referee/nulls/compute {"null_spec_id":"referee-null-tod-v1"}` calls against the SAME running backend (`http://localhost:8301`), keeping the spec's manager state "running" for a large majority of wall-clock time.
  4. In the primary tab (attached via the pinned CDP endpoint), loaded `/desk` fresh, expanded "Referee Runs" (`desk-section-expand-refereeRuns`), and clicked "Build Null" for `referee-null-tod-v1` (`referee-null-build-trigger-referee-null-tod-v1`) while the second channel's loop was active.
  5. Confirmed via `extract` and the screenshot itself that `data-testid="referee-null-build-trigger-error-referee-null-tod-v1"` reads exactly "Refused — a null build is already running for this spec. Wait for it to finish, then try again." (the required exact clause is the sentence up to "for this spec." — present verbatim), alongside the borrowed "Building… 57/126" progress and a "Cancel" button (both correctly rendered too, since the refused trigger's response snapshot is the OTHER job's live state).
  6. Stopped the second-channel loop (stop-file) once the screenshot was captured — no lingering background writers.
  7. Checksummed the new screenshot: md5 `5baf7d31fdc1b73101ed7ec264d97a94` — confirmed DIFFERENT from the shared `d3065788c71ecfcc5623b7704ad6de73` (`UT-07-result.png`/`UT-09-result.png`/`UT-10-result.png`, iteration 10's own finding), clearing `evidence_makeup` for this clause.
  - This iteration's action created real, irreversible append-only null-build run-ledger rows on the scoped fixture rig only (never the operator's real store) — an expected consequence of exercising this control for real, per the pump note's own instructions.

---

## Failed Tests

None.

---

## Skipped Tests

None. (J-07 and J-10 were explicitly excluded from this run's scope — a deterministic replay verifies them separately this iteration; their own evidence, `J-07-verify.png` and `J-10-verify.png`, already exists in the evidence directory from that separate pass.)

---

## Golden replay scripts

- `runs/goal-session-referee/journey-scripts/J-09.json` — reviewed, left unchanged. It already
  covers J-09's deterministic, replayable surface (fresh `/desk` load, expand all three Referee
  sections, confirm honest baseline copy in each) and nothing in this iteration's zero-code-diff
  work invalidates it. The single-flight-refusal race this iteration captured cannot be expressed
  in the `goto`/`click`/`fill` replay schema (it requires a genuinely concurrent second-channel
  writer racing the primary tab's click) — asserting the refusal text in a script that cannot
  reproduce the race would create a deterministic false-FAIL on replay, so per the "best-effort,
  skip if you can't produce one" rule this facet is not encoded; it falls back to an LLM
  browser-qa pass next time it needs re-verification.
- J-01–J-06 and J-08 are keyless/automated journeys with no dedicated page (`journey-scripts/J-01.json.invalid`,
  `J-02.json.invalid` mark this explicitly; J-03–J-06/J-08 never had one). No browser replay script
  applies — their re-verification path is their own named pytest module, run above.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (scoped fixture rig; confirmed via `assert_scoped_qa_backend.py`, `source_url='fixture-rig-iter8-replay'`)
- **Browser:** Chromium via Chrome MCP, attached to the pre-launched CDP endpoint on 127.0.0.1:9222 (pump-provided; not launched or killed by this agent)
- **Test Date:** 2026-08-15
- **Evidence directory:** `reports/qa/goal-referee-iter-11-evidence/`
- **Non-browser test evidence:** `reports/qa/goal-referee-iter-11-test.log`
