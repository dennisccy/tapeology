# Regression Replay — goal-fast_wall-iter-5

**Phase:** goal-fast_wall-iter-5
**Date:** 2026-07-17
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 0/1 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | The foundation is unchanged (regression sentinel) | regression | P1 | journey replays end-to-end; all expects hold | step 03 expected "buyer_control" did not appear | FAIL | reports/qa/goal-fast_wall-iter-5-evidence/J-07-verify.png |

## Failed Tests

### UT-J-07 — The foundation is unchanged (regression sentinel)

**Verdict:** FAIL
**Failure:** step 03 expected "buyer_control" did not appear
**Evidence:** `reports/qa/goal-fast_wall-iter-5-evidence/J-07-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-17

---

_Reconciliation (2026-07-17): the replay FAIL row(s) for J-07 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-fast_wall-iter-5-ui-test-results.md; the FAIL row(s) above are superseded._
