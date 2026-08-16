# Regression Replay — goal-referee-iter-14

**Phase:** goal-referee-iter-14
**Date:** 2026-08-16
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 4/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | The registry — pre-registration with an immutable boundary | regression | P1 | journey replays end-to-end; all expects hold | step 02 expected "historical-exploration" did not appear | FAIL | reports/qa/goal-referee-iter-14-evidence/J-05-verify.png |
| UT-J-07 | The starter family — historical exploration becomes registered questions | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-14-evidence/J-07-verify.png |
| UT-J-09 | The Referee on /desk + MCP contract v5 — 22 read-only tools | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-14-evidence/J-09-verify.png |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-14-evidence/J-10-verify.png |
| UT-J-11 | The accrual projection states its own basis — the wait, measured in recorded sessions | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-14-evidence/J-11-verify.png |

## Failed Tests

### UT-J-05 — The registry — pre-registration with an immutable boundary

**Verdict:** FAIL
**Failure:** step 02 expected "historical-exploration" did not appear
**Evidence:** `reports/qa/goal-referee-iter-14-evidence/J-05-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-16

---

_Reconciliation (2026-08-16): the replay FAIL row(s) for J-05 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-referee-iter-14-ui-test-results.md; the FAIL row(s) above are superseded._
