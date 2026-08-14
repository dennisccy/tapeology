# UI Test Results (merged)

**Date:** 2026-08-14
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 1/2 journeys passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-3-evidence/J-10-verify.png |
| UT-J-03 | The statistics core — calibrated, seeded, oracle-proven, fail-closed | backend-only (no UI) | P1 | N/A — goal.md's own J-03 Acceptance line ends `(Keyless; automated.)`; its steps describe building `referee_stats.py` + `tests/test_referee_oracles.py` + `run_oracle_attestation()`, with no browser action of any kind named | No browser-testable surface exists for J-03 this iteration; confirmed by direct evidence (see Skipped Tests below) | SKIP | none (no browser-testable surface — see reason) |

## Skipped Tests

### UT-J-03 — The statistics core — calibrated, seeded, oracle-proven, fail-closed

**Verdict:** SKIPPED
**Reason:** No browser-testable surface exists for J-03 this iteration; confirmed by direct evidence (see Skipped Tests below)

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-14


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | J-01 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-02 | J-02 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
