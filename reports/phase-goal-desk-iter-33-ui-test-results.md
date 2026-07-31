# UI Test Results (merged)

**Date:** 2026-07-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 5/6 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-33-evidence/J-04-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-33-evidence/J-07-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-33-evidence/J-09-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-33-evidence/J-16-verify.png |
| UT-J-17 | A top-up asks the vendor only for the bars the frozen store cannot already prove | regression | P1 | `/desk`'s Top-up Runs section renders the four-outcome counts line and the tail/full-lookback window-basis line with real recorded values (not the not-recorded fallback), and the ranked briefing table still renders with no horizontal scroll at 1440×900 | Latest run `topup-2026-07-31-8fb5c9a1f737` (404/404 pairs attempted) renders `0 reused · 404 fetched · 0 unchanged · 0 failed` and `390 pairs asked for a tail window · 14 pairs asked for the full lookback window` — both lines render live recorded values, not fallback text; ranked table renders 100 rows + 1 skipped, `scrollWidth === clientWidth` (no horizontal scroll) confirmed via `getBoundingClientRect`/DOM measurement | PASS | `reports/qa/goal-desk-iter-33-evidence/UT-J-17-result.png` |
| UT-J-19 | Every top-up run records the date each pair's frozen history actually reaches | target | P1 | The "newest recorded reach" line and the "Pairs recorded earlier" list agree with each other at calendar-day granularity (no pair printed under "earlier" shares the calendar day named as "newest"), and the earlier list is capped to at most 20 rows with a "showing N of M" disclosure when the true total exceeds 20 | Self-contradiction still present, unchanged from the exact defect iter-32's confirm rejected: the page reads `newest recorded reach 2026-07-30 · 101 pairs reach it` and then lists `Pairs recorded earlier (303)` with the FIRST rows in that list dated `2026-07-30` — the SAME calendar day just named "newest" (e.g. `AAPL 4h — 2026-07-30`, `AAPL 1d — 2026-07-30`, `ABBV 4h — 2026-07-30`, ...). The earlier list is NOT capped: DOM query confirms 303 `data-testid="desk-topup-run-latest-reach-earlier-row"` elements render (not ≤20), and no "showing N of M" sentence appears anywhere on the page. `apps/frontend/app/desk/page.tsx`'s `topupLibraryReach` function (lines 878-904) still compares `store_frozen_through_after` by raw full-timestamp equality, not calendar-day truncation — no code change landed this iteration (dev handoff: "Evidence-only iteration: no code changes were planned or made") | FAIL | `reports/qa/goal-desk-iter-33-evidence/UT-J-19-fail.png` |

## Failed Tests

### UT-J-19 — Every top-up run records the date each pair's frozen history actually reaches

**Verdict:** FAIL
**Failure:** Self-contradiction still present, unchanged from the exact defect iter-32's confirm rejected: the page reads `newest recorded reach 2026-07-30 · 101 pairs reach it` and then lists `Pairs recorded earlier (303)` with the FIRST rows in that list dated `2026-07-30` — the SAME calendar day just named "newest" (e.g. `AAPL 4h — 2026-07-30`, `AAPL 1d — 2026-07-30`, `ABBV 4h — 2026-07-30`, ...). The earlier list is NOT capped: DOM query confirms 303 `data-testid="desk-topup-run-latest-reach-earlier-row"` elements render (not ≤20), and no "showing N of M" sentence appears anywhere on the page. `apps/frontend/app/desk/page.tsx`'s `topupLibraryReach` function (lines 878-904) still compares `store_frozen_through_after` by raw full-timestamp equality, not calendar-day truncation — no code change landed this iteration (dev handoff: "Evidence-only iteration: no code changes were planned or made")
**Evidence:** ``reports/qa/goal-desk-iter-33-evidence/UT-J-19-fail.png``

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-31

