# Regression Replay — goal-desk-iter-19

**Phase:** goal-desk-iter-19
**Date:** 2026-07-29
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 7/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | step 07 could not perform expect: expect not satisfied | FAIL | reports/qa/goal-desk-iter-19-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-07-verify.png |
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-08-verify.png |
| UT-J-11 | Every ranked briefing row states how much completed history its wall was measured over | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-11-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-12-verify.png |
| UT-J-13 | Every ranked briefing row states the price its wall sits at and the close it was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-19-evidence/J-13-verify.png |

## Failed Tests

### UT-J-05 — Ledger history + drill-in to /structure

**Verdict:** FAIL
**Failure:** step 07 could not perform expect: expect not satisfied
**Evidence:** `reports/qa/goal-desk-iter-19-evidence/J-05-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-29

---

_Reconciliation (2026-07-29): the replay FAIL row(s) for J-05 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-desk-iter-19-ui-test-results.md; the FAIL row(s) above are superseded._
