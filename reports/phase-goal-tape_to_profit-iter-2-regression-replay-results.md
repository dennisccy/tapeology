# Regression Replay — goal-tape_to_profit-iter-2

**Phase:** goal-tape_to_profit-iter-2
**Date:** 2026-07-03
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | A read-only MCP server exposes the product over the canonical API | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-2-evidence/J-01-verify.png |
| UT-J-08 | The existing product is unchanged (regression sentinel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-tape_to_profit-iter-2-evidence/J-08-verify.png |

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-03
