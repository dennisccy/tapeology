# Regression Replay — goal-yahoo_fetch-iter-7

**Phase:** goal-yahoo_fetch-iter-7
**Date:** 2026-07-12
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 2/3 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | Real S/R levels and confluence zones on real Yahoo bars | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-yahoo_fetch-iter-7-evidence/J-04-verify.png |
| UT-J-05 | Fetch from the app — the Structure page fetch control with "Yahoo Finance" provenance | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-yahoo_fetch-iter-7-evidence/J-05-verify.png |
| UT-J-06 | The foundation is unchanged (regression sentinel) | regression | P1 | journey replays end-to-end; all expects hold | step 03 expected "Absorption reversal" did not appear | FAIL | reports/qa/goal-yahoo_fetch-iter-7-evidence/J-06-verify.png |

## Failed Tests

### UT-J-06 — The foundation is unchanged (regression sentinel)

**Verdict:** FAIL
**Failure:** step 03 expected "Absorption reversal" did not appear
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-7-evidence/J-06-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-12
