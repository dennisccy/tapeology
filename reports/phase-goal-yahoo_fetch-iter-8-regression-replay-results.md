# Regression Replay — goal-yahoo_fetch-iter-8

**Phase:** goal-yahoo_fetch-iter-8
**Date:** 2026-07-12
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | Real S/R levels and confluence zones on real Yahoo bars | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-yahoo_fetch-iter-8-evidence/J-04-verify.png |
| UT-J-05 | Fetch from the app — the Structure page fetch control with "Yahoo Finance" provenance | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-yahoo_fetch-iter-8-evidence/J-05-verify.png |

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-12
