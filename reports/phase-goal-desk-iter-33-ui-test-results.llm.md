# Phase goal-desk-iter-33 — UI Test Results

**Phase:** goal-desk-iter-33
**Date:** 2026-07-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

**Overall:** 1/2 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-17 | A top-up asks the vendor only for the bars the frozen store cannot already prove | regression | P1 | `/desk`'s Top-up Runs section renders the four-outcome counts line and the tail/full-lookback window-basis line with real recorded values (not the not-recorded fallback), and the ranked briefing table still renders with no horizontal scroll at 1440×900 | Latest run `topup-2026-07-31-8fb5c9a1f737` (404/404 pairs attempted) renders `0 reused · 404 fetched · 0 unchanged · 0 failed` and `390 pairs asked for a tail window · 14 pairs asked for the full lookback window` — both lines render live recorded values, not fallback text; ranked table renders 100 rows + 1 skipped, `scrollWidth === clientWidth` (no horizontal scroll) confirmed via `getBoundingClientRect`/DOM measurement | PASS | `reports/qa/goal-desk-iter-33-evidence/UT-J-17-result.png` |
| UT-J-19 | Every top-up run records the date each pair's frozen history actually reaches | target | P1 | The "newest recorded reach" line and the "Pairs recorded earlier" list agree with each other at calendar-day granularity (no pair printed under "earlier" shares the calendar day named as "newest"), and the earlier list is capped to at most 20 rows with a "showing N of M" disclosure when the true total exceeds 20 | Self-contradiction still present, unchanged from the exact defect iter-32's confirm rejected: the page reads `newest recorded reach 2026-07-30 · 101 pairs reach it` and then lists `Pairs recorded earlier (303)` with the FIRST rows in that list dated `2026-07-30` — the SAME calendar day just named "newest" (e.g. `AAPL 4h — 2026-07-30`, `AAPL 1d — 2026-07-30`, `ABBV 4h — 2026-07-30`, ...). The earlier list is NOT capped: DOM query confirms 303 `data-testid="desk-topup-run-latest-reach-earlier-row"` elements render (not ≤20), and no "showing N of M" sentence appears anywhere on the page. `apps/frontend/app/desk/page.tsx`'s `topupLibraryReach` function (lines 878-904) still compares `store_frozen_through_after` by raw full-timestamp equality, not calendar-day truncation — no code change landed this iteration (dev handoff: "Evidence-only iteration: no code changes were planned or made") | FAIL | `reports/qa/goal-desk-iter-33-evidence/UT-J-19-fail.png` |

---

## Passed Tests

### UT-J-17 — A top-up asks the vendor only for the bars the frozen store cannot already prove
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-33-evidence/UT-J-17-result.png`
- Navigated to `http://localhost:3301/desk`, scrolled to the Top-up Runs section.
- `desk-topup-runs-table` lists 2 runs (`topup-2026-07-29-5de907c83fc4`, `topup-2026-07-31-8fb5c9a1f737`), both `done`, `404 / 404`.
- `desk-topup-run-latest-detail` for the latest run (`topup-2026-07-31-8fb5c9a1f737`) renders `state: done`, `404 of 404 pairs attempted`, `desk-topup-run-latest-counts` = `0 reused · 404 fetched · 0 unchanged · 0 failed`, and `desk-topup-run-latest-window-basis` = `390 pairs asked for a tail window · 14 pairs asked for the full lookback window` — i.e. the real recorded window-basis line renders (not the `WINDOW_BASIS_NOT_RECORDED` fallback), proving `window_basis` is present and read verbatim on this run.
- No `desk-topup-run-latest-failed` block mounts (the run has 0 failed pairs, so `failedOutcomes.length > 0` correctly gates the block off — not a defect, an honest absence).
- Ranked briefing table (`BRIEFING`) renders all 100 ranked rows + 1 skipped-member row (`NOW — no basis`), matching J-16's shipped column set (rank/symbol/side/class/distance/score/coverage/tick evidence/basis/history/band/opposite/levels); `document.documentElement.scrollWidth === clientWidth` (1425 === 1425) confirms no horizontal scroll at the 1440×900 viewport.
- Note on acceptance nuance: J-17's original literal acceptance text (written at build time) describes a run with "at least one `unchanged`" outcome and "one failed pair" visible in the screenshot. The CURRENT ambient latest run genuinely has 0 `unchanged` and 0 `failed` outcomes (full coverage, no failures) — this is the exact class of environmental drift the iteration spec's own golden-script-refresh instructions for `J-17.json` explicitly anticipate and route around (replacing the exact-count assertions with a structural liveness check). The MECHANISM (four-outcome tally + window-basis disclosure, correctly omitting empty sections) is verified intact; the specific historical example values are not reproducible on today's ambient store, which is a fact about the data, not a code regression.

---

## Failed Tests

### UT-J-19 — Every top-up run records the date each pair's frozen history actually reaches
**Verdict:** FAIL
**Failure:** The reach-line/earlier-list self-contradiction that iter-32's second-key confirm explicitly rejected is still present unchanged, and the earlier-pairs list is still uncapped (303 rows rendered, not ≤20). No frontend code change landed this iteration to fix `topupLibraryReach`.
**Evidence:** `reports/qa/goal-desk-iter-33-evidence/UT-J-19-fail.png` (full-page capture cropped to the Top-up Runs → Latest Run detail section, 1440×900 viewport, showing the exact contradiction: "newest recorded reach 2026-07-30 · 101 pairs reach it" immediately followed by "Pairs recorded earlier (303)" whose first several rows — AAPL 4h, AAPL 1d, ABBV 4h, ABBV 1d, ABT 4h, ABT 1d, ... — are all also dated 2026-07-30)

**Steps taken:**
1. Navigated to `http://localhost:3301/desk` at a 1440×900 viewport.
2. Located the Top-up Runs section's `desk-topup-run-latest-reach` line: text = `newest recorded reach 2026-07-30 · 101 pairs reach it`.
3. Located the adjacent `desk-topup-run-latest-reach-earlier` block: heading = `Pairs recorded earlier (303)`; read its rows via DOM query (`document.querySelectorAll('[data-testid="desk-topup-run-latest-reach-earlier-row"]')` → 303 elements, confirming no cap is applied).
4. Read the first ~15 rendered rows verbatim: `AAPL 4h — 2026-07-30`, `AAPL 1d — 2026-07-30`, `AAPL 1w — 2026-07-27`, `ABBV 4h — 2026-07-30`, `ABBV 1d — 2026-07-30`, `ABBV 1w — 2026-07-27`, `ABT 4h — 2026-07-30`, `ABT 1d — 2026-07-30`, ... — the majority of "earlier" rows are dated `2026-07-30`, the SAME calendar day the reach line calls "newest."
5. Cross-checked against the raw `GET /research/desk/topup/runs` payload: computed the CORRECT calendar-day grouping (newest day `2026-07-30` with 303 pairs reaching it, `2026-07-27` with 101 pairs earlier) versus the CURRENT buggy raw-timestamp grouping the page renders (newest exact timestamp `2026-07-30T19:30:00.000000Z` with only 101 pairs matching it, 303 pairs "earlier" including 202 that are also on 2026-07-30 but at a different time-of-day). The page's rendered 101/303 split matches the BUGGY raw-timestamp computation exactly, confirming `topupLibraryReach` was not changed.
6. Read `apps/frontend/app/desk/page.tsx` lines 878-904 (`topupLibraryReach`) directly: `newestDate`/`newestCount`/`earlier` are still computed via `d === newestDate` / `o.store_frozen_through_after !== newestDate` (raw string equality on the full microsecond-precision timestamp), not a calendar-day-truncated comparison. No capping logic (`.slice(0, 20)` or similar) exists on the `earlier` array or its render.
7. Confirmed via `git diff` / `git status` that `apps/frontend/app/desk/page.tsx` has zero uncommitted diff versus HEAD, and the dev handoff (`docs/handoffs/goal-desk-iter-33-dev.md`) states "Evidence-only iteration: no code changes were planned or made" — i.e. the iteration's own IN SCOPE frontend fix (calendar-day grouping + 20-row cap) was not implemented.

**Expected:** Per the iteration spec's DEFINITION OF DONE and TC-1/TC-2/TC-3/TC-7: the reach line and the earlier list should be mutually consistent at calendar-day granularity (no earlier row shares the reach line's named day), and the earlier list should render at most 20 rows with a "showing N of M" disclosure when the true total exceeds 20.
**Actual:** The reach line and earlier list still disagree exactly as before (202 of the 303 "earlier" rows share the "newest" day), and all 303 rows render with no cap and no "showing N of M" sentence.

---

## Skipped Tests

None.

---

## Notes for the goal-evaluator

- This dispatch's target journeys were J-17 and J-19 (per the dispatch's "test EXACTLY these journeys" instruction). J-17 also appeared in the dispatch's separate "Do NOT test — deterministic replay covers it" list alongside J-04/J-07/J-09/J-16; since J-17 was explicitly named in the "test EXACTLY" list too, it was browser-verified here rather than skipped, and its golden script (`journey-scripts/J-17.json`) was refreshed per the iteration spec's explicit assignment (see below). This is flagged in case the duplicate listing was a dispatch-prompt error rather than deliberate.
- J-04, J-07, J-09, J-16 were NOT re-tested in this browser-qa pass (per the dispatch's explicit exclusion list) — see the separate deterministic-replay report (`reports/phase-goal-desk-iter-33-regression-replay-results.md`), which already reports these 4 as PASS via golden-script replay.
- **The iteration's own frontend fix did not land.** `docs/phases/goal-desk-iter-33.md`'s IN SCOPE explicitly requires fixing `topupLibraryReach` to calendar-day granularity and capping the earlier list to 20 rows, but the dev handoff states no code changes were made ("Evidence-only iteration"). This browser-qa pass confirms the bug iter-32's confirm rejected is still live and unchanged on `/desk`. J-19 cannot pass until this fix actually lands.
- Golden replay script maintenance performed this dispatch:
  - `runs/goal-session-desk/journey-scripts/J-17.json` — REFRESHED (J-17 verified PASS): now asserts stable substrings (`fetched`, `asked for a tail window`) plus a liveness re-check, instead of the stale exact counts/fallback-text/failed-block assertions that no longer match the current ambient run. Lint-checked clean (`demo_runner.py --mode lint`).
  - `runs/goal-session-desk/journey-scripts/J-19.json` — NOT refreshed. J-19 verified FAIL this iteration (the underlying self-contradiction/cap bug is still present), so per the golden-script policy ("for every journey you verify PASS, also write a replay script... skip if you cannot produce one") no new golden was written. The EXISTING `J-19.json` on disk still asserts the exact stale values from iter-32 (`newest recorded reach 2026-07-30 · 101 pairs reach it`, `Pairs recorded earlier (303)`, `AAPL 4h — 2026-07-30`) — coincidentally these still textually match the CURRENT (still-buggy) page output, so a deterministic replay of the unmodified file would report a false PASS. This is flagged explicitly: the existing `J-19.json` should not be read as confirmation the bug is fixed — it predates the fix requirement and encodes the buggy behavior's own output. It should be regenerated by browser-qa AFTER a real frontend fix lands, using stable substrings that assert the CORRECTED behavior, not reused as-is.
