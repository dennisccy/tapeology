# UI Test Results (merged)

**Date:** 2026-08-15
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | The starter family — historical exploration becomes registered questions | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-11-evidence/J-07-verify.png |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-11-evidence/J-10-verify.png |
| UT-J-01 | The era transition stands — reconciliation made testable | regression | P1 | `test_referee_guards.py` (spec-drift + zero-lens-diff + catalog-pin guards) + the 3 J-01 readiness-fold tests in `test_referee_evidence.py` all pass | Ran to completion: `22 passed, 2 warnings in 1.64s`, exit code 0 | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-02 | The evidence contract — two families, one observation shape | regression | P1 | Full `test_referee_evidence.py` (26 tests) passes | Ran to completion: `26 passed, 2 warnings in 2.33s`, exit code 0 | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-03 | The statistics core — calibrated, seeded, oracle-proven, fail-closed | regression | P1 | `test_referee_stats.py` (48) + `test_referee_oracles.py` (11) pass within `REFEREE_ORACLE_BUDGET_SECONDS` (120s) | Ran to completion: `59 passed in 87.57s (0:01:27)`, exit code 0 — within the 120s oracle budget | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-04 | Matched nulls — comparable times, identical measurement | regression | P1 | `test_referee_null.py` (36 tests) passes | Ran to completion: `36 passed, 2 warnings in 1.73s`, exit code 0 | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-05 | The registry — pre-registration with an immutable boundary | regression | P1 | `test_referee_registry.py` (47 tests) passes | Ran to completion: `47 passed, 2 warnings in 1.69s`, exit code 0 | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-06 | Estimand engines + adjudication — one checkpoint, recorded forever | regression | P1 | `test_referee_adjudicate.py` (57 tests) passes | Ran to completion: `57 passed, 2 warnings in 6.43s`, exit code 0 | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-08 | The strategy family + the promotion interlock — fail closed, no bypass | regression | P1 | `test_pnl_scan.py` (30 tests, incl. `test_no_bypass_path_exists_for_authorize_promotion` + `test_tc3`..`test_tc7` refusal classes) passes | Ran to completion: `30 passed in 7.99s`, exit code 0; all named tests confirmed present and passing | PASS | `reports/qa/goal-referee-iter-11-test.log` |
| UT-J-09 | The Referee on `/desk` + MCP contract v5 — single-flight refusal screenshot (owed evidence) | error | P1 | On the scoped fixture rig, a null build for `referee-null-tod-v1` started from a second channel while still running, then a fresh `/desk` load + Referee Runs expand + "Build Null" click for the same spec renders the exact line "Refused — a null build is already running for this spec." — with a screenshot checksum DISTINCT from the shared `d3065788c71ecfcc5623b7704ad6de73` | Confirmed via `assert_scoped_qa_backend.py` (scoped, exit 0) immediately before the write; a second-channel loop of direct `POST /research/desk/referee/nulls/compute` calls kept a build running; a fresh `/desk` load → expanded "Referee Runs" → clicked "Build Null" for `referee-null-tod-v1` rendered `data-testid="referee-null-build-trigger-error-referee-null-tod-v1"` = "Refused — a null build is already running for this spec. Wait for it to finish, then try again." — visible in the screenshot; md5 of new screenshot = `5baf7d31fdc1b73101ed7ec264d97a94`, confirmed DIFFERENT from `d3065788c71ecfcc5623b7704ad6de73` | PASS | `reports/qa/goal-referee-iter-11-evidence/UT-J-09-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-15

