# Phase goal-desk-iter-9 — UI Test Plan

**Phase:** goal-desk-iter-9 (Era B, Journey J-08 — basis disclosure)
**Date:** 2026-07-27
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301

---

## Scope

One surface changed: `/desk`. All 10 test cases below target that page's ranked-rows table, its
row hover tooltip, and its Screen History drill-through — the only three places J-08 touches. No
new page, no new form, no new button. Verified against the live instance before writing this plan:
frontend responds `200` at `http://localhost:3301/desk`; backend responds `200` at
`http://localhost:8301/research/desk/screen`; the two screens currently on record
(`2026-06-22`, `2026-07-25`) both genuinely lack `basis_as_of`/`basis_age_days` on every row (confirmed
by direct query), so UT-05/UT-06 below are exercisable right now without any setup.

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads with the new 8-column basis header (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend reachable at `http://localhost:3301`; backend reachable (page must not show the amber
  "The desk screen could not be loaded." panel).
- At least one screen has already been computed (true today — the Screen History panel lists
  entries for `2026-06-22` and `2026-07-25`).

**Steps:**
1. Navigate to `http://localhost:3301/desk`.
2. Wait for the gray pulsing loading skeleton to disappear.
3. Locate the "Briefing" panel's ranked-rows table.
4. Read the table's header row left to right.

**Expected Result:**
- The page heading reads "Desk".
- No amber "Desk screen not computed yet." or "The desk screen could not be loaded." panel appears.
- The Briefing table's header row contains exactly 8 columns, in this exact order: `symbol`,
  `side`, `class`, `distance`, `score`, `coverage`, `tick evidence`, `basis`.
- Below the Briefing table, the "Skipped Members", "Screen History", and "Run Screen / Top-up"
  panels are all visible with no visual overlap or broken layout.
- No browser console errors.

---

### UT-02 — Operator runs a new screen and the basis column populates with real data (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded per UT-01.
- A universe snapshot is already registered (true today — the "Provenance" panel shows a
  non-"—" "Universe snapshot" value).

**Steps:**
1. Navigate to `http://localhost:3301/desk`.
2. Scroll to the "Run Screen / Top-up" panel at the bottom of the page.
3. Click the "Run Screen" button.
4. Wait while the button reads "Computing…" and a line below it counts up "`<done>` / `<total>`
   members" (this reads only already-stored bars — no network fetch — so it typically finishes in
   well under a minute).
5. Once the button returns to reading "Run Screen" (no longer disabled), read the outcome line
   just above it and the "basis" column of the ranked table.

**Expected Result:**
- The outcome line reads either "Recorded a new snapshot — screen-2026-07-27-…" or "Reused the
  snapshot already recorded for this key — screen-2026-07-27-…" (either wording is a PASS — both
  confirm the compute finished; only a FAIL if a red error line appears instead, e.g. under the
  "The screen compute could not be started." or a similar compute-error message).
- Every ranked row's "basis" cell now shows text matching the pattern
  `basis YYYY-MM-DD · N d before as-of` (e.g. "basis 2026-07-23 · 4 d before as-of") — a real date
  and a real non-negative integer, never blank, never a dash, never the word "null" or "undefined".
- A new row dated "2026-07-27" appears at the top of the "Screen History" table.

---

### UT-03 — Fresh and stale basis ages are distinguishable at a glance (happy-path — the iteration's core goal)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- UT-02 completed — a freshly computed screen (with real basis data) is being displayed.

**Steps:**
1. On the ranked table from UT-02, read every row's "basis" cell top to bottom.
2. Note the smallest "N d before as-of" value shown and the largest.
3. Compare the two.
4. Capture a full-page or table-region screenshot showing both the freshest and stalest row
   together, legibly.

**Expected Result:**
- The smallest and largest day-counts shown are visibly different numbers — not every row shows
  the same age.
- At least one row shows a noticeably small count (the freshest reading available that day) and at
  least one shows a noticeably larger count, typically ≥10 d. (On this codebase's own most recent
  live measurement: AAPL/large-cap rows read ~3–4 d while META/NFLX/NVDA read ~12–14 d — exact
  numbers drift daily since these are real calendar-date measurements against live data, so read
  the actual values on screen rather than expecting these specific ones.)
- If, at test time, no row's count is ≤ 2 d, use judgment: a spread of 7+ days between the
  smallest and largest visible values still satisfies "fresh vs. stale" legibility even if the
  literal "≤2 d" example isn't hit that day — this is an explicit, documented allowance for this
  iteration, not a shortcut around the requirement.
- The screenshot is legible — text is not clipped, overlapping, or cut off by the viewport.

---

### UT-04 — Row hover tooltip discloses full-precision basis detail (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- A ranked row with real basis data is on screen (from UT-02/UT-03).

**Steps:**
1. Move the mouse pointer over any part of a ranked row — e.g., over the symbol text, or over the
   new basis cell's own text — and hold it still until the native browser tooltip appears (usually
   under one second).
2. Read the full tooltip text.
3. Move to a DIFFERENT ranked row and repeat.

**Expected Result:**
- One single tooltip appears for the whole row — not a separate tooltip per cell.
- Its text contains, in this order: a `distance … bps` segment, then `score …`, then a
  `basis … (N d before as-of)` segment using the FULL-precision basis timestamp (e.g.
  "basis 2026-07-23T04:00:00.000000Z (4 d before as-of)" — long, not the rounded date shown in the
  cell), then — if the row has any coverage entries — `… window last requested: …` segment(s).
- The basis segment sits between the `score` segment and the coverage segment(s) — never before
  "distance", never after coverage.
- The second row's tooltip shows that row's own values, not the first row's.

---

### UT-05 — Legacy screen rows show the honest "not recorded" fallback, never a fabricated value (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded; the "Screen History" panel lists at least one screen recorded before this
  iteration (today, both `2026-06-22` and `2026-07-25` qualify — confirmed to already lack basis
  data on the live instance).

**Steps:**
1. Navigate to `http://localhost:3301/desk`.
2. In the "Screen History" panel, click the row whose date column reads "2026-07-25".
3. Wait for the "Viewing the recorded screen for 2026-07-25 — not the latest." banner to appear at
   the top.
4. Read every ranked row's "basis" cell in the now-displayed table.
5. Hover over one of those rows and read the tooltip.

**Expected Result:**
- Every ranked row's basis cell reads exactly "basis not recorded in this snapshot" — never blank,
  never a dash "—", never "null"/"undefined", never a guessed date.
- The hover tooltip's basis segment reads that same "basis not recorded in this snapshot" text in
  place of a date/day-count.
- The page does not crash, throw a visible error, or blank out — the rest of each row (symbol,
  side, class, distance, score, coverage, tick evidence) still renders normally.

---

### UT-06 — Screen History drill-through is consistent and "Latest" reverts cleanly (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- Continuing from UT-05 — currently viewing the `2026-07-25` historical screen.

**Steps:**
1. Click the "Latest" button in the viewing-indicator banner.
2. Confirm the banner disappears and the ranked table refreshes.
3. If UT-02 already ran this session, confirm the basis column now shows real data again (not the
   fallback) for the latest screen.
4. Click the "2026-06-22" row in "Screen History" (the OTHER legacy screen).
5. Confirm its ranked rows also show the fallback text, then click "Latest" again to return.

**Expected Result:**
- After step 1, the "Viewing the recorded screen for … — not the latest." banner is gone, and the
  ranked table shows the latest screen's own data.
- Both legacy screens (`2026-06-22` and `2026-07-25`) render the fallback text identically — no
  behavioral difference between them.
- No JavaScript error, no blank page, at any point in this click sequence.
- The same table component visibly renders both the historical and latest views — identical column
  layout, "basis" column in the same (8th) position in both.

---

### UT-07 — Row click-through still works at the new basis cell's location (regression — flagged risk)

**Type:** regression
**Priority:** P1 *(elevated above this category's default P2/P3 — this is an explicit,
still-unverified item from the dev handoff: the table gained an 8th column, so every cell's screen
position shifted, including the drill-in anchor's hit area at the new cell. Not yet confirmed with
a real browser hit-test per the caveats carried into QA.)*
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded with at least one ranked row visible.

**Steps:**
1. Navigate to `http://localhost:3301/desk`.
2. In any ranked row, click directly on the visible text inside the "basis" cell (e.g., click on
   the digits of the date, not on empty padding around it).
3. Observe the browser's resulting URL and page content.
4. (Optional, more rigorous check) Right-click precisely on that same spot and choose "Inspect"
   from the browser's context menu; in the DevTools panel that opens, confirm the
   highlighted/selected element is the row's drill-in link (an `<a>` element), not the `<td>` table
   cell itself.

**Expected Result:**
- The click navigates the browser to `/structure?symbol=<that row's symbol>&asof=<the displayed
  screen's as_of>` — the same destination clicking any other cell in that row would produce.
- The page does NOT stay on `/desk` with no effect. A "dead click" on the basis cell would mean the
  new column's `<td>` is intercepting the click instead of the row's stretched link overlay — this
  is the specific defect this test is designed to catch.
- If the optional DevTools check is performed: the topmost element at that pixel is the anchor, not
  the table cell.

---

### UT-08 — Other 7 ranked columns and the skip-rows table are unchanged (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded with both ranked and skipped rows present (true today — 10 ranked / ~91 skipped).

**Steps:**
1. Navigate to `http://localhost:3301/desk`.
2. In the ranked table, compare the 7 columns before "basis" (symbol, side, class, distance,
   score, coverage, tick evidence) against their known prior behavior: distance/score show
   2-decimal numbers, coverage shows one colored badge per timeframe, tick evidence shows a badge
   only when true.
3. Scroll to the "Skipped Members" panel and inspect its table(s) (headed "Skipped — no bars (N)"
   and/or "Skipped — no basis session (N)").

**Expected Result:**
- The 7 pre-existing ranked columns behave exactly as before — no change to their values, order,
  or styling.
- The skip table(s) show exactly 4 columns — `symbol`, `reason`, `coverage`, `tick evidence` — with
  NO "basis" column anywhere, and every reason reads "no bars" or "no basis" (never a raw
  `no_bars`/`no_basis` code, never a basis value on a skip row).
- The "Run Screen" and "Top-up" buttons are both present, enabled (when no compute is running), and
  unchanged in label/position at the bottom of the page.

---

### UT-09 — Basis copy is plain and descriptive, never advice/urgency language (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded with both a fresher and a staler row visible (per UT-03).

**Steps:**
1. Read the "basis" column header text and a few basis cell values.
2. Visually compare the styling (text color, weight, background) of a small-day-count basis cell
   versus a large-day-count basis cell.
3. Re-read the hover tooltip's basis segment from UT-04.

**Expected Result:**
- All basis text is plain descriptive measurement only (e.g., "basis 2026-07-23 · 4 d before
  as-of") — no words like "stale", "warning", "act now", "buy", "sell", "opportunity", or similar
  advice/urgency language anywhere in the column or tooltip.
- The stale (large-day-count) row's basis cell is styled identically to the fresh (small-day-count)
  row's cell — same text color, no red/amber/warning highlight, no icon — matching the explicit
  "no color-coded freshness/urgency indicator" requirement for this feature.
- The column header reads simply "basis" (lowercase, matching the other 7 headers' casing/style).

---

### UT-10 — New basis information is visible without any extra navigation (ux — discoverability)

**Type:** ux
**Priority:** P3
**Surface:** `/desk`

**Preconditions:**
- None beyond a running frontend.

**Steps:**
1. Open a fresh browser tab and navigate directly to `http://localhost:3301/desk` (as a first-time
   visitor would, with no prior clicks).
2. Look at the ranked-rows table without scrolling horizontally.

**Expected Result:**
- The "basis" column and its data are visible as part of the normal page load — no extra click,
  toggle, "show more," or settings menu is required to reveal it.
- If the table is wider than the viewport, the page scrolls horizontally within the table's own
  container rather than breaking the page layout; the "basis" column is reachable by that scroll
  alone.
- The full-precision detail (exact timestamp) is reachable in exactly one additional action —
  hovering — consistent with how distance/score's full precision is already surfaced elsewhere on
  this same row.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Page loads, 8-column header present | smoke | P1 | `/desk` |
| UT-02 | Run Screen populates real basis data | happy-path | P1 | `/desk` |
| UT-03 | Fresh vs. stale ages distinguishable | happy-path | P1 | `/desk` |
| UT-04 | Hover tooltip shows full-precision basis | happy-path | P1 | `/desk` |
| UT-05 | Legacy rows show honest fallback text | error | P2 | `/desk` |
| UT-06 | History drill-through + Latest revert | regression | P2 | `/desk` |
| UT-07 | Row click-through still hits at basis cell | regression | P1 (elevated) | `/desk` |
| UT-08 | Other columns + skip table unchanged | regression | P3 | `/desk` |
| UT-09 | Copy is descriptive, no urgency styling | ux | P3 | `/desk` |
| UT-10 | Basis column visible with zero extra clicks | ux | P3 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.**

### Coverage notes

- **No validation-type test case.** `/desk` has no form or text-input field anywhere on the page —
  J-08 adds zero new user actions ("the existing Run Screen button's output simply carries two more
  fields," per the execution plan). The "validation" category in the test-design skill applies to
  form input handling, which does not exist on this surface; manufacturing one would mean testing
  something this iteration didn't build. The nearest equivalent — how the UI handles the *absence*
  of a value — is covered as UT-05 under the "error" category instead.
- **UT-07's elevated priority** reflects that it is the one item explicitly flagged as
  browser-unverified in the user-visible-changes report's "Caveats carried into QA" section, and is
  a named Definition-of-Done line item ("a hit-test confirms the anchor stays topmost at the new
  cell's center") — not a general-purpose regression sweep.
- **Dynamic data notice:** every basis date/day-count referenced above is illustrative. Actual
  values move forward with the calendar every day the live universe's bars stay unrefreshed; testers
  should read the values actually rendered on screen rather than expecting an exact literal match to
  the examples given.
- Backend-only assertions already in `reports/qa/goal-desk-iter-9-test-plan.md` (TC-01/02/03/04/08/
  09/10/11/13/14/15/16 — byte-identity, call counting, suite/fingerprint, golden replay, frozen-file
  diffs) are intentionally not duplicated here.
