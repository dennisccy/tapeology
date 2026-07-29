# Regression Replay — goal-desk-iter-17

**Phase:** goal-desk-iter-17
**Date:** 2026-07-29
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-11 | Every ranked briefing row states how much completed history its wall was measured over | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-11-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-17-evidence/J-12-verify.png |

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-29
