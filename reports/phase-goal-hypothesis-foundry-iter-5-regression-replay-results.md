# Regression Replay — goal-hypothesis-foundry-iter-5

**Phase:** goal-hypothesis-foundry-iter-5
**Date:** 2026-08-27
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 3/3 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The Foundry opens as a new finite era and the old self-extension loop is inactive | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-5-evidence/J-01-verify.png |
| UT-J-03 | Generic interpretation preserves timing, population symmetry, direction, and exact Scout decisions | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-5-evidence/J-03-verify.png |
| UT-J-04 | Foundry owns the denominator, append-only state, freeze barrier, and integrity lock | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-hypothesis-foundry-iter-5-evidence/J-04-verify.png |

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-08-27
