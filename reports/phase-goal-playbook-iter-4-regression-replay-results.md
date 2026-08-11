# Regression Replay — goal-playbook-iter-4

**Phase:** goal-playbook-iter-4
**Date:** 2026-08-11
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 1/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-03 | The Playbook lands on /desk | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-4-evidence/J-03-verify.png |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | step 05 expected "300.11" did not appear | FAIL | reports/qa/goal-playbook-iter-4-evidence/J-10-verify.png |

## Failed Tests

### UT-J-10 — The kept product stands — regression sentinel

**Verdict:** FAIL
**Failure:** step 05 expected "300.11" did not appear
**Evidence:** `reports/qa/goal-playbook-iter-4-evidence/J-10-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-11

---

_Reconciliation (2026-08-11): the replay FAIL row(s) for J-10 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-playbook-iter-4-ui-test-results.md; the FAIL row(s) above are superseded._
