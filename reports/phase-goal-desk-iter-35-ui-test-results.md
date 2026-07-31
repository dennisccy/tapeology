# UI Test Results (merged)

**Date:** 2026-07-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 11/11 journeys passed (0 skipped)

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
| UT-J-20 | Every recorded screen states how it differs from the screen recorded before it | smoke | P1 | `/desk` renders a new read-only "Screen Comparison" section for the currently-displayed screen, showing (a) the identical state for the latest-vs-prior pair, (b) a churned state (≥1 row rank-moved ≥20 places, ≥1 side change) when an older churned pair is selected, and (c) an honest "no earlier recorded screen" state on the ledger's oldest snapshot — all legible at 1440×900 with no horizontal scroll and the ranked briefing table unchanged from J-16 | All three states rendered exactly as specified, confirmed via both DOM extraction and full-page screenshots (see Passed Tests below for exact text/values) | PASS | see per-state screenshots below |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-31

