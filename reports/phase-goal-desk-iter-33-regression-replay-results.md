# Regression Replay — goal-desk-iter-33

**Phase:** goal-desk-iter-33
**Date:** 2026-07-31
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 4/5 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-33-evidence/J-04-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-33-evidence/J-07-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-33-evidence/J-09-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-33-evidence/J-16-verify.png |
| UT-J-17 | A top-up asks the vendor only for the bars the frozen store cannot already prove | regression | P1 | journey replays end-to-end; all expects hold | step 02 expected "0 reused · 390 fetched · 0 unchanged · 14 failed" did not appear | FAIL | reports/qa/goal-desk-iter-33-evidence/J-17-verify.png |

## Failed Tests

### UT-J-17 — A top-up asks the vendor only for the bars the frozen store cannot already prove

**Verdict:** FAIL
**Failure:** step 02 expected "0 reused · 390 fetched · 0 unchanged · 14 failed" did not appear
**Evidence:** `reports/qa/goal-desk-iter-33-evidence/J-17-verify.png`

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-31

---

_Reconciliation (2026-07-31): the replay FAIL row(s) for J-17 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-desk-iter-33-ui-test-results.md; the FAIL row(s) above are superseded._
