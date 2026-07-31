# UI Test Results (merged)

**Date:** 2026-07-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-32-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-32-evidence/J-02-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-32-evidence/J-04-verify.png |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-32-evidence/J-06-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-32-evidence/J-07-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-32-evidence/J-09-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-32-evidence/J-16-verify.png |
| UT-J-17 | A top-up asks the vendor only for the bars the frozen store cannot already prove | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-32-evidence/J-17-verify.png |
| UT-J-18 | Every screen run leaves an append-only record of what it attempted — and a re-run under identical pins says so before it walks | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-32-evidence/J-18-verify.png |
| UT-J-19 | Every top-up run records the date each pair's frozen history actually reaches | happy-path | P1 | After a real top-up run, `/desk`'s Top-up Runs latest-run detail shows one descriptive line naming the newest `store_frozen_through_after` date across the run's pairs plus the count reaching it, AND a list of pairs whose own recorded reach date is earlier (or null), each with symbol/timeframe/date, both legible in one 1440×900 frame with no horizontal scroll, and the ranked briefing table unchanged from J-16 | Triggered a real top-up run via the shipped "Top-up" button against the ambient `:3301`/`:8301` store (404/404 pairs, `topup-2026-07-31-8fb5c9a1f737`). `/desk`'s latest-run detail now renders `desk-topup-run-latest-reach` = "newest recorded reach 2026-07-30 · 101 pairs reach it" and `desk-topup-run-latest-reach-earlier` = "Pairs recorded earlier (303)" with per-pair rows (e.g. "AAPL 4h — 2026-07-30", "AAPL 1w — 2026-07-27") each showing symbol/timeframe/date verbatim. `document.documentElement.scrollWidth` (1440) equals `window.innerWidth` (1440) confirming zero horizontal scroll. The ranked briefing table at the top of `/desk` renders with its unchanged rank/symbol/side/class/distance/score/coverage/tick-evidence/basis/history/band/opposite/levels columns. | PASS | `reports/qa/goal-desk-iter-32-evidence/UT-J-19-result.png`, `reports/qa/goal-desk-iter-32-evidence/UT-J-19-ranked-table-unchanged.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-31

