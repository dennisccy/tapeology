# Regression Replay — counter-check

**Phase:** counter-check
**Date:** 2026-07-30
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 0/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-13 | Every ranked briefing row states the price its wall sits at and the close it was measured from | regression | P1 | journey replays end-to-end; all expects hold | step 03 could not perform expect: expect not satisfied | FAIL | none |
| UT-J-14 | Every ranked briefing row states where the nearest wall on the OTHER side of price sits | regression | P1 | journey replays end-to-end; all expects hold | step 03 could not perform expect: expect not satisfied | FAIL | none |

## Failed Tests

### UT-J-13 — Every ranked briefing row states the price its wall sits at and the close it was measured from

**Verdict:** FAIL
**Failure:** step 03 could not perform expect: expect not satisfied
**Evidence:** `none`

### UT-J-14 — Every ranked briefing row states where the nearest wall on the OTHER side of price sits

**Verdict:** FAIL
**Failure:** step 03 could not perform expect: expect not satisfied
**Evidence:** `none`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-30
