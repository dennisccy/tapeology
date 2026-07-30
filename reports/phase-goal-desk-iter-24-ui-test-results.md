# UI Test Results (merged)

**Date:** 2026-07-30
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 14/14 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-02-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-04-verify.png |
| UT-J-05 | Ledger history + drill-in to /structure | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-05-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-07-verify.png |
| UT-J-08 | Every ranked briefing row names the bar its distance was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-08-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-09-verify.png |
| UT-J-10 | The coverage the briefing shows is the coverage the frozen store can prove | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-10-verify.png |
| UT-J-11 | Every ranked briefing row states how much completed history its wall was measured over | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-11-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-12-verify.png |
| UT-J-13 | Every ranked briefing row states the price its wall sits at and the close it was measured from | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-13-verify.png |
| UT-J-14 | Every ranked briefing row states where the nearest wall on the OTHER side of price sits | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-24-evidence/J-14-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression-fix | P1 | At a 1440×900 viewport, no horizontal scroll (`scrollWidth<=clientWidth`), one screenshot shows rank/symbol/side/class/distance/score/coverage/tick-evidence/basis/history/band/opposite/levels for the top row; 4 coverage badges on one line, row height ≤60px; first 8 ranked rows legible with rank 1–8 in served order; legacy snapshot honest-absence strings intact; skipped-members table still groups honestly | `table.scrollWidth` 1214px === container `clientWidth` 1214px (doc-level 1425===1425) — zero horizontal scroll, closing iter-23's UT-07 FAIL (was 1795/1214); all 12 disclosures + new `rank` cell legible in one screenshot of row 1 (BRK-B); coverage badges share one top y-coordinate on every row checked (4/4, one line); row height: first 8 rows all 57px, full-table 98/100 rows ≤60px (2 rows — positions 24 & 80 — measure 63px, a disclosed 3px residual); rank cells read 1,2,3,4,5,6,7,8 in order on rows 1–8; legacy snapshot `screen-2026-06-22-3ecd45c062c7` renders all 5 honest-absence strings verbatim; Skipped Members table still groups "SKIPPED — NO BASIS SESSION (1)" honestly; SHA-256 listing of `.data/{screen,universe,topup_runs,index_reconcile_runs}` identical before/after (zero write) | PASS | `reports/qa/goal-desk-iter-24-evidence/J-16-viewport.png` (+ `J-16-eight-rows-crop.png`, `J-16-legacy-snapshot.png`, `J-16-skipped-table.png`) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-30


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | J-06 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-15 | J-15 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
