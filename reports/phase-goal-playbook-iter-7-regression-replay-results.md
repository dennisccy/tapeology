# Regression Replay — goal-playbook-iter-7

**Phase:** goal-playbook-iter-7
**Date:** 2026-08-11
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 5/6 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-7-evidence/J-01-verify.png |
| UT-J-02 | Every signal measured — the rail's own conventions, anchored at the trigger bar | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-7-evidence/J-02-verify.png |
| UT-J-03 | The Playbook lands on /desk | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-7-evidence/J-03-verify.png |
| UT-J-04 | The continuation family — JBE, DBI, cup-and-handle | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-7-evidence/J-04-verify.png |
| UT-J-05 | The climax family — capitulation entry, euphoria marker | regression | P1 | journey replays end-to-end; all expects hold | step 03 could not perform click: Locator.wait_for: Timeout 10000ms exceeded. | FAIL | reports/qa/goal-playbook-iter-7-evidence/J-05-verify.png |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-7-evidence/J-10-verify.png |

## Failed Tests

### UT-J-05 — The climax family — capitulation entry, euphoria marker

**Verdict:** FAIL
**Failure:** step 03 could not perform click: Locator.wait_for: Timeout 10000ms exceeded.
**Evidence:** `reports/qa/goal-playbook-iter-7-evidence/J-05-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-11

---

_Reconciliation (2026-08-11): the replay FAIL row(s) for J-05 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-playbook-iter-7-ui-test-results.md; the FAIL row(s) above are superseded._
