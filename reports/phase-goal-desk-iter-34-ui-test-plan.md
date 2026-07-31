# Phase goal-desk-iter-34 — UI Test Plan

**Phase:** goal-desk-iter-34
**Date:** 2026-07-31
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` Top-up Runs panel loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301, backend at http://localhost:8301
- The ambient store holds at least one recorded top-up run (currently
  `topup-2026-07-31-8fb5c9a1f737`, 404/404 pairs, state "done")
- No login required

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load
3. Scroll down to the section titled "Top-up Runs"

**Expected Result:**
- Page renders without a blank screen or error message
- A table with columns "date", "run", "state", "attempted / total", "universe snapshot" is visible
  under "Top-up Runs" (`data-testid="desk-topup-runs-table"`)
- Below that table, a "Latest run — `<date>` · `<run-id>`" heading is visible
  (`data-testid="desk-topup-run-latest-detail"`)
- No console errors

---

### UT-02 — Newest-reach line and "Pairs recorded earlier" list never name the same day (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Top-up Runs → Latest run detail

**Preconditions:**
- Same as UT-01
- The latest run has both a "newest recorded reach" value and a non-empty "Pairs recorded earlier"
  list (true on the ambient run: "newest recorded reach 2026-07-30", "Pairs recorded earlier (101)")

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Latest run" detail block, locate the line reading
   "newest recorded reach `<date>` · `<N>` pairs reach it" (`data-testid="desk-topup-run-latest-reach"`)
3. Note the calendar day printed (format `YYYY-MM-DD`), e.g. `2026-07-30`
4. Locate the "Pairs recorded earlier (`<M>`)" heading directly below it
   (`data-testid="desk-topup-run-latest-reach-earlier"`)
5. Read every row rendered under that heading (`data-testid="desk-topup-run-latest-reach-earlier-row"`)
   — each row prints `SYMBOL TIMEFRAME — YYYY-MM-DD`

**Expected Result:**
- None of the rows' printed dates equal the day noted in step 3 (e.g. no row shows `2026-07-30` if
  that is the newest-reach day)
- On the ambient run, every visible row instead prints `2026-07-27`

---

### UT-03 — Honest cap disclosure appears when more than 20 pairs are earlier (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Top-up Runs → Latest run detail

**Preconditions:**
- Same as UT-01
- The latest run's true "Pairs recorded earlier" total exceeds 20 (true on the ambient run: 101)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Locate the "Pairs recorded earlier (`<M>`)" heading (`data-testid="desk-topup-run-latest-reach-earlier"`);
   confirm `<M>` is greater than 20 (ambient: `101`)
3. Look directly below the heading, before the first row, for a line matching
   "showing `<shown>` of `<M>`" (`data-testid="desk-topup-run-latest-reach-earlier-cap"`)
4. Count the rendered `desk-topup-run-latest-reach-earlier-row` elements

**Expected Result:**
- The sentence "showing 20 of `<M>`" is visible (ambient: "showing 20 of 101"), styled as small
  muted text matching the existing fallback lines (no color/badge/urgency)
- Exactly 20 rows are rendered, even though the heading's count `<M>` is larger (101)

---

### UT-04 — No cap-disclosure sentence when the true earlier-pairs total is 20 or fewer (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` — Top-up Runs → Latest run detail (`topupLibraryReach` function)

**Preconditions:**
- Requires a top-up run whose true earlier-pairs total is ≤ 20. The CURRENT ambient run's true
  total is 101 (> 20), so this branch cannot be exercised live against `:3301` today — this is an
  environment limitation, not a defect (see the dev handoff's TC-5 disclosure).

**Steps (live, when a qualifying run exists):**
1. Navigate to `http://localhost:3301/desk` after a top-up run with ≤ 20 true earlier pairs is the
   latest run on disk
2. Locate the "Pairs recorded earlier (`<M>`)" heading where `<M>` ≤ 20
3. Look for any text matching "showing `<N>` of `<M>`" in the block

**Steps (fallback — current ambient state, unit/structural verification):**
1. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_topup_library_reach_guard.py -k cap -v`
2. Inspect the passing test `test_topup_library_reach_caps_the_earlier_list_and_preserves_the_true_total`
   and the render-wiring test asserting the disclosure paragraph is gated on
   `earlierTotal > EARLIER_PAIRS_DISPLAY_CAP`

**Expected Result:**
- Live: no "showing N of M" text appears anywhere in the "Pairs recorded earlier" block; all ≤ 20
  rows render normally
- Fallback: the named pytest tests pass, confirming the disclosure is structurally impossible to
  render when the true total is at or below the 20-row cap

---

### UT-05 — Legacy run (no recorded reach data) still shows the honest fallback text (error / edge case)

**Type:** error
**Priority:** P2
**Surface:** `/desk` — Top-up Runs → Latest run detail

**Preconditions:**
- Requires a top-up run where every outcome lacks `store_frozen_through_after` (a pre-iter-32
  legacy run). No such run currently exists on the ambient `:3301` store — this branch is unchanged
  by this iteration's diff and was verified only at the unit level (dev handoff TC-6 disclosure).

**Steps (fallback — unit/structural verification):**
1. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_topup_library_reach_guard.py -k lacks_store_frozen_through_after -v`

**Expected Result:**
- `test_topup_library_reach_returns_null_when_any_outcome_lacks_store_frozen_through_after` passes
  unmodified, confirming that on such a run the reach line renders the literal text
  "library reach not recorded in this run" and no earlier-pairs section renders at all — untouched
  by the day-truncation/cap logic added this iteration

---

### UT-06 — Top-up Runs summary table and adjacent pages are unaffected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` (summary table), `/`, `/structure`

**Preconditions:**
- Same as UT-01

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Top-up Runs" table (`data-testid="desk-topup-runs-table"`), confirm the column headers
   read exactly: "date", "run", "state", "attempted / total", "universe snapshot" — no new column
3. Click "Cockpit" in the top navigation bar
4. Confirm the Cockpit page (`http://localhost:3301/`) loads without errors
5. Click "Structure" in the top navigation bar
6. Confirm the Structure page (`http://localhost:3301/structure`) loads without errors

**Expected Result:**
- The Top-up Runs summary table has exactly the 5 original columns (no width/column regression —
  J-16's contract)
- Both "Cockpit" and "Structure" pages load normally; nothing about this iteration's frontend-only
  change to `/desk` affects them (zero diff outside `apps/frontend/app/desk/page.tsx`)

---

### UT-07 — Cap-disclosure sentence reads as plain description, not advice (ux / copy discipline)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` — Top-up Runs → Latest run detail

**Preconditions:**
- Same as UT-03 (a run whose true earlier total exceeds 20)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Read the "showing `<shown>` of `<total>`" sentence beneath the "Pairs recorded earlier" heading
3. Compare its visual styling to the "library reach not recorded in this run" /
   "window basis not recorded" fallback lines elsewhere in the same detail block

**Expected Result:**
- The sentence contains only the word "showing" and the two numbers — no urgency, judgement, or
  advice language (e.g. no "warning", "should", "recommend")
- Font size/color match the existing muted descriptive-text style (`text-xs text-slate-400`) — no
  new color, icon, or badge

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` Top-up Runs panel loads | smoke | P1 | `/desk` |
| UT-02 | Reach line and earlier list never share a day | happy-path | P1 | `/desk` |
| UT-03 | Cap disclosure shows "showing 20 of N" | happy-path | P1 | `/desk` |
| UT-04 | No disclosure when true total ≤ 20 | validation | P2 | `/desk` (unit fallback) |
| UT-05 | Legacy run still shows honest fallback text | error | P2 | `/desk` (unit fallback) |
| UT-06 | Summary table + adjacent pages unaffected | regression | P1 | `/desk`, `/`, `/structure` |
| UT-07 | Disclosure sentence is plain description | ux | P2 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.**
