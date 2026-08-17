# Regression Replay — goal-rapid-microscope-iter-2

**Phase:** goal-rapid-microscope-iter-2
**Date:** 2026-08-17
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 0/1 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | step 09 expected "b06e0bc289c54d77" did not appear | FAIL | reports/qa/goal-rapid-microscope-iter-2-evidence/J-10-verify.png |

## Failed Tests

### UT-J-10 — The kept product stands — traps armed, sentinel green

**Verdict:** FAIL
**Failure:** step 09 expected "b06e0bc289c54d77" did not appear
**Evidence:** `reports/qa/goal-rapid-microscope-iter-2-evidence/J-10-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-17
