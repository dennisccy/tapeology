# Regression Replay — goal-desk-iter-35

**Phase:** goal-desk-iter-35
**Date:** 2026-07-31
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-35-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-35-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-35-evidence/J-05-verify.png |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-35-evidence/J-06-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-35-evidence/J-07-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-35-evidence/J-12-verify.png |
| UT-J-13 | Every ranked briefing row states the price its wall sits at and the close it was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-35-evidence/J-13-verify.png |
| UT-J-14 | Every ranked briefing row states where the nearest wall on the OTHER side of price sits | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-35-evidence/J-14-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-35-evidence/J-16-verify.png |
| UT-J-18 | Every screen run leaves an append-only record of what it attempted — and a re-run under identical pins says so before it walks | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-35-evidence/J-18-verify.png |

## Environment

- **Frontend URL:** http://localhost:3301
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-31
