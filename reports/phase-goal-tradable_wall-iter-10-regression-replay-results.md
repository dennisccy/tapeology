# Regression Replay — goal-tradable_wall-iter-10

**Phase:** goal-tradable_wall-iter-10
**Date:** 2026-07-16
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 1/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | /structure decluttered — the map is the default, the noise is a toggle | regression | P1 | journey replays end-to-end; all expects hold | step 04 expected "300.1700134277344" did not appear | FAIL | reports/qa/goal-tradable_wall-iter-10-evidence/J-05-verify.png |
| UT-J-07 | The foundation is unchanged (regression sentinel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tradable_wall-iter-10-evidence/J-07-verify.png |

## Failed Tests

### UT-J-05 — /structure decluttered — the map is the default, the noise is a toggle

**Verdict:** FAIL
**Failure:** step 04 expected "300.1700134277344" did not appear
**Evidence:** `reports/qa/goal-tradable_wall-iter-10-evidence/J-05-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-16
