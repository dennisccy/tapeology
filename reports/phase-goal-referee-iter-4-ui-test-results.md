# UI Test Results (merged)

**Date:** 2026-08-14
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 1/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-4-evidence/J-10-verify.png |
| UT-07 | Remaining Desk reference sections still expand | regression (supplementary) | P2 | All 5 buttons (`topupRuns`, `indexReconciliation`, `screenRuns`, `screenComparison`, `provenance`) reach `aria-expanded="true"`, marker ▸→▾, body renders content/empty-state, no error toast, no permanently-blank panel | 3 of 5 sections (`topupRuns`, `indexReconciliation`, `screenRuns`) expanded correctly with explicit empty-state text and no errors; 2 of 5 (`screenComparison`, `provenance`) do not exist in the current DOM — confirmed pre-existing, data-state-gated (`latest !== null`), unrelated to this iteration's diff | FAIL | `reports/qa/goal-referee-iter-4-evidence/UT-07-fail.png` |

## Failed Tests

### UT-07 — Remaining Desk reference sections still expand

**Verdict:** FAIL
**Failure:** 3 of 5 sections (`topupRuns`, `indexReconciliation`, `screenRuns`) expanded correctly with explicit empty-state text and no errors; 2 of 5 (`screenComparison`, `provenance`) do not exist in the current DOM — confirmed pre-existing, data-state-gated (`latest !== null`), unrelated to this iteration's diff
**Evidence:** ``reports/qa/goal-referee-iter-4-evidence/UT-07-fail.png``

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
