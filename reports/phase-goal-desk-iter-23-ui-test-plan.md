# Phase goal-desk-iter-23 — UI Test Plan

**Phase:** goal-desk-iter-23
**Date:** 2026-07-30
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Context for the tester

The `/desk` ranked table gains one new `levels` column (rightmost, after `opposite`). It shows
each row's `band_member_count` + `band_member_timeframes` as a tally string, plus a reused "round
number" badge (`data-testid="tradable-band-round-number"`) when `band_round_number` is true. Rows
from a screen snapshot recorded BEFORE this iteration render the honest fallback text
"composition not recorded in this snapshot" instead — these fields are never backfilled.

As of this writing, the ambient `/desk` "latest" screen (`screen-2026-07-20-ca185294a384`) was
recorded before this change, so it will show the legacy-absent state on every row until a new
screen is computed (via the "Run Screen" button, `data-testid="desk-run-screen-button"`, for a
`screen_date` not already recorded) or a fixture-scoped/QA-recorded screen is used. Tests below
that require the POPULATED state should be run against such a post-iteration screen; tests that
require the LEGACY-ABSENT state can be run directly against the current ambient latest screen.

---

## Test Cases

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is running at http://localhost:8301

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load (ranked table or "Desk screen not computed yet." panel appears)

**Expected Result:**
- Page renders without a blank screen or error boundary
- The ranked table, identified by `data-testid="desk-screen-rows-table"`, is present in the DOM
  (assuming at least one screen has ever been recorded — true in the current ambient environment)
- The table header row includes cells reading, in order after `opposite`: `levels`
- No browser console errors

---

### UT-02 — `levels` column header is visible beside `band`/`opposite` (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk` → `DeskRowsTable` header row

**Preconditions:**
- `/desk` has loaded with a ranked table visible (UT-01 passed)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll the ranked table header row into view (it is the `<thead>` row inside
   `data-testid="desk-screen-rows-table"`)

**Expected Result:**
- The header row reads, from left to right (final columns): `...`, `band`, `opposite`, `levels`
- The `levels` header cell is the LAST column — no column appears to its right

---

### UT-03 — Populated row shows the wall-composition tally and (when applicable) the round-number badge (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → `DeskRow`, `levels` cell (`data-testid="desk-row-levels"`)

**Preconditions:**
- A screen snapshot computed AFTER this iteration's deploy is the one currently displayed on
  `/desk` (either the "latest" screen if one has been run today, or a screen selected from the
  Screen History list whose `created_utc` is after this change was deployed). If the current
  latest screen is legacy, click the "Run Screen" button (`data-testid="desk-run-screen-button"`,
  visible in the "Run Screen / Top-up / Reconcile Index" panel) and wait for it to finish
  (`data-testid="desk-screen-compute-running"` disappears and the ranked table refreshes).

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. If the ranked table's `levels` column shows "composition not recorded in this snapshot" on
   every row, click the "Run Screen" button and wait for the compute to finish
3. Locate any ranked row whose `data-testid="desk-row-levels"` cell is NOT the legacy-absent copy
4. Read that cell's text

**Expected Result:**
- The cell text matches the pattern `<N> levels · <tf1> <n1> · <tf2> <n2> ...` — e.g. `155 levels
  · 1d 68 · 1h 57 · 4h 19 · 1w 11`
- The sum of every `<n>` value after each timeframe abbreviation equals the leading `<N>` value
  (e.g. `68 + 57 + 19 + 11 = 155`)
- If that row's underlying data has `band_round_number: true`, a small bordered badge reading
  exactly "round number" (`data-testid="tradable-band-round-number"`) appears immediately after
  the tally text, inside the same cell
- If that row's underlying data has `band_round_number: false`, no badge of any kind appears in
  the cell — only the tally text

---

### UT-04 — Legacy screen renders the honest absence copy, never a computed fallback (regression / error-shape)

**Type:** error
**Priority:** P1
**Surface:** `/desk` → `DeskRow`, `levels` cell, legacy state

**Preconditions:**
- A screen snapshot recorded BEFORE this iteration is selected. The current ambient latest screen,
  `screen-2026-07-20-ca185294a384`, satisfies this as of this writing — if a newer screen has since
  become "latest", open the Screen History list and click any entry with a `created_utc` predating
  this deploy.

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. If the displayed screen is not a pre-iteration one, scroll to the "Screen History" section and
   click on a history row whose `created_utc` predates this deploy
3. Read the `levels` cell (`data-testid="desk-row-levels"`) of every visible ranked row

**Expected Result:**
- Every row's `levels` cell reads exactly the literal string "composition not recorded in this
  snapshot" — not blank, not "0 levels", not a dash, not any other placeholder
- No round-number badge appears in any `levels` cell for this screen

---

### UT-05 — Pre-existing `/desk` columns are unaffected (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → `DeskRow`, all pre-existing cells

**Preconditions:**
- `/desk` has loaded with a ranked table visible (UT-01 passed)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. For the first ranked row, read the values of the `symbol` (`data-testid="desk-row-symbol"`),
   `side` (`data-testid="desk-row-side"`), `band class` (`data-testid="desk-row-band-class"`),
   `distance` (`data-testid="desk-row-distance"`), `score` (`data-testid="desk-row-score"`),
   `basis` (`data-testid="desk-row-basis"`), `history` (`data-testid="desk-row-history"`), `band`
   (`data-testid="desk-row-band"`), and `opposite` (`data-testid="desk-row-opposite"`) cells

**Expected Result:**
- Every one of those nine cells renders non-empty, correctly formatted content in the same style
  and position as before this iteration (e.g. `basis` still reads `basis <date> · <n> d before
  as-of` or the honest absence copy; `opposite` still reads `opposite <side> <class> <low>–<high> ·
  <n> bps`, `no band on the other side`, or its own legacy-absence copy)
- No pre-existing cell's content, format, or position changed as a side effect of adding the
  `levels` column

---

### UT-06 — Symbol-cell drill-in tooltip is unchanged (no new tooltip line) (regression / UX)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` → `DeskRow` symbol cell composite `title` tooltip

**Preconditions:**
- `/desk` has loaded with a ranked table visible

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Hover the mouse over the `symbol` cell (`data-testid="desk-row-symbol"`) of any ranked row and
   wait for the native browser tooltip to appear

**Expected Result:**
- The tooltip text appears (native browser title tooltip) and does NOT contain the words
  "band_member_count", "band_round_number", "band_member_timeframes", "levels", or "round number"
- The tooltip's existing content (distance/score/bands_by_class precision, per prior iterations)
  is unchanged from before this iteration

---

### UT-07 — `levels` column is discoverable without scrolling past the fold on a standard viewport (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` ranked table

**Steps:**
1. Navigate to `http://localhost:3301/desk` in a browser window at least 1440px wide
2. Look at the ranked table without any horizontal scrolling

**Expected Result:**
- The `levels` header cell and at least one populated (or legacy-absent) `levels` cell are visible
  without needing to scroll the table horizontally, given the table's existing column widths use
  compact `whitespace-nowrap` cells

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads without errors | smoke | P1 | `/desk` |
| UT-02 | `levels` header visible beside `band`/`opposite` | smoke | P1 | `/desk` header row |
| UT-03 | Populated row shows tally + round-number badge | happy-path | P1 | `/desk` row `levels` cell |
| UT-04 | Legacy screen shows honest absence copy | error | P1 | `/desk` row `levels` cell (legacy) |
| UT-05 | Pre-existing columns unaffected | regression | P1 | `/desk` row (all prior cells) |
| UT-06 | Symbol tooltip unchanged (no new line) | ux | P2 | `/desk` row symbol cell |
| UT-07 | `levels` column discoverable without scroll | ux | P2 | `/desk` ranked table |

**P1 tests must all pass for browser QA verdict to be PASS.**
