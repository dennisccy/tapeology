# Regression Replay — goal-playbook-iter-8

**Phase:** goal-playbook-iter-8
**Date:** 2026-08-11
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 6/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-8-evidence/J-01-verify.png |
| UT-J-02 | Every signal measured — the rail's own conventions, anchored at the trigger bar | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-8-evidence/J-02-verify.png |
| UT-J-03 | The Playbook lands on /desk | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-8-evidence/J-03-verify.png |
| UT-J-04 | The continuation family — JBE, DBI, cup-and-handle | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-8-evidence/J-04-verify.png |
| UT-J-05 | The climax family — capitulation entry, euphoria marker | regression | P1 | journey replays end-to-end; all expects hold | step 03 could not perform click: Locator.wait_for: Timeout 10000ms exceeded. | FAIL | reports/qa/goal-playbook-iter-8-evidence/J-05-verify.png |
| UT-J-06 | The range family — range trades, double top/bottom | regression | P1 | journey replays end-to-end; all expects hold | step 03 could not perform click: Locator.wait_for: Timeout 10000ms exceeded. | FAIL | reports/qa/goal-playbook-iter-8-evidence/J-06-verify.png |
| UT-J-07 | The back-scan — every recorded session, resumable and append-only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-8-evidence/J-07-verify.png |
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-8-evidence/J-10-verify.png |

## Failed Tests

### UT-J-05 — The climax family — capitulation entry, euphoria marker

**Verdict:** FAIL
**Failure:** step 03 could not perform click: Locator.wait_for: Timeout 10000ms exceeded.
**Evidence:** `reports/qa/goal-playbook-iter-8-evidence/J-05-verify.png`

### UT-J-06 — The range family — range trades, double top/bottom

**Verdict:** FAIL
**Failure:** step 03 could not perform click: Locator.wait_for: Timeout 10000ms exceeded.
**Evidence:** `reports/qa/goal-playbook-iter-8-evidence/J-06-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-11
