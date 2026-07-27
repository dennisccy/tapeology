# Regression Replay — goal-desk-iter-8

**Phase:** goal-desk-iter-8
**Date:** 2026-07-27
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 1/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-8-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | step 06 could not perform expect: expect not satisfied | FAIL | reports/qa/goal-desk-iter-8-evidence/J-05-verify.png |

## Failed Tests

### UT-J-05 — Ledger history + drill-in to /structure

**Verdict:** FAIL
**Failure:** step 06 could not perform expect: expect not satisfied
**Evidence:** `reports/qa/goal-desk-iter-8-evidence/J-05-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-27

---

_Reconciliation (2026-07-27): the replay FAIL row(s) for J-05 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-desk-iter-8-ui-test-results.md; the FAIL row(s) above are superseded._
