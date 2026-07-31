# Phase goal-desk-iter-29 — UI Test Plan

**Phase:** goal-desk-iter-29
**Date:** 2026-07-31
**Written by:** ui-impact-analyst (combined mode)
**Frontend URL:** http://localhost:3301

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads and the Screen Runs panel is present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301, backend at http://localhost:8301
- No login required

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load (the `desk-title` heading "Desk" is visible)
3. Scroll to the bottom of the page, past the "Top-up Runs" and "Index Reconciliation" panels

**Expected Result:**
- A fourth panel titled "Screen Runs" (rendered in uppercase per this page's house style) is
  visible immediately after "Index Reconciliation", with no blank screen or error message
- The panel shows either the empty-state text "No screen runs recorded yet." (element with
  `data-testid="desk-screen-runs-empty"`) or a table with `data-testid="desk-screen-runs-table"`
- No horizontal scrollbar appears at a 1440x900 viewport
- No console errors related to `desk-screen-runs` or `fetchDeskScreenRuns`

---

### UT-02 — A freshly-completed screen run appears in Screen Runs (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- A universe snapshot is already registered (the standing session-desk fixture/ambient state
  already has one — the "Run Screen" button is enabled, not the "not computed" empty panel)
- No screen run has yet been recorded for today's UTC date in the store being tested, OR it is
  acceptable that this run reuses an existing one (see UT-03 for the reuse-specific case)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the "Run Screen" button (`data-testid="desk-run-screen-button"`)
3. Wait for the button to change from "Computing…" back to "Run Screen" and the members progress
   counter (`data-testid="desk-screen-compute-progress"`) to stop advancing
4. Scroll down to the "Screen Runs" panel

**Expected Result:**
- The "Screen Runs" table (`data-testid="desk-screen-runs-table"`) shows a new row
  (`data-testid="desk-screen-run-row"`) whose date column matches today's UTC date
- That row's "state" column reads "done"
- That row's "attempted / total" column shows two equal numbers if this was a fresh (non-reused)
  walk, e.g. "101 / 101"
- That row's "produced" column shows a screen id string (not "nothing recorded")
- Below the table, the "Latest run" detail block (`data-testid="desk-screen-run-latest-detail"`)
  shows a heading "Latest run — `<today's date>` · `<the same run id>`", the state "state: done",
  an elapsed-time string, and a ranked/skipped-counts line
  (`data-testid="desk-screen-run-latest-counts"`) reading "`<N>` ranked · `<N>` skipped (no bars) ·
  `<N>` skipped (no basis)"

---

### UT-03 — A duplicate Run Screen click short-circuits and is recorded as reused (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- UT-02 has just completed on this same session (a screen run for today's UTC date already exists)

**Steps:**
1. On `/desk`, immediately click the "Run Screen" button (`data-testid="desk-run-screen-button"`)
   a second time
2. Observe how quickly the button returns from "Computing…" to "Run Screen" compared to the first
   click in UT-02
3. Scroll down to the "Screen Runs" panel

**Expected Result:**
- The button resolves noticeably faster than the first (UT-02) click, and the members progress
  counter does NOT climb through its full range (`0 / 101` -> `101 / 101`) the way it did in UT-02
- A new row appears in the "Screen Runs" table for this second run, with "attempted / total"
  reading "0 / `<total>`" (e.g. "0 / 101")
- That row's "produced" column reads "reused `<id>` — no walk was performed", and `<id>` is
  IDENTICAL to the screen id produced in UT-02
- The "Latest run" detail block's outcome line (`data-testid="desk-screen-run-latest-outcome"`)
  reads the same "reused `<id>` — no walk was performed" text
- The ranked/skipped-counts line (`data-testid="desk-screen-run-latest-counts"`) does NOT appear
  for this reused run (it only renders when `state === "done"` per the component, and a reused run
  IS `state === "done"` — verify instead that the counts shown, if any, describe the ORIGINAL walk,
  not a fabricated re-count)

---

### UT-04 — The empty state never fabricates a produced outcome (validation / data-honesty)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` (Screen Runs panel)

**Preconditions:**
- A fixture-scoped or fresh backend store with zero recorded screen runs (set
  `TAPEOLOGY_DESK_SCREEN_LOG_DIR` to an empty temp directory and restart the backend, or use a
  scoped rig per the phase's own fixture-scoping convention — never the operator's real ambient
  `.data/` store)

**Steps:**
1. With the backend pointed at the empty screen-run store, navigate to
   `http://localhost:3301/desk`
2. Scroll to the "Screen Runs" panel

**Expected Result:**
- The panel shows the exact text "No screen runs recorded yet." inside an element with
  `data-testid="desk-screen-runs-empty"`
- No table (`data-testid="desk-screen-runs-table"`) is rendered
- No "Latest run" detail block is rendered
- No screen id, date, or state text of any kind appears — the page shows nothing invented in place
  of real data

---

### UT-05 — A failed run's exact error and raising member are shown verbatim (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` (Screen Runs panel)

**Preconditions:**
- This scenario cannot be triggered through normal UI operation — a real member walk failure
  requires a fixture that forces `_resolve_reference_close_and_history` to raise (the backend's own
  TC-6 coverage in `apps/backend/tests/test_desk_screen_compute.py`). To verify this UI surface
  manually, plant a `failed`-state record via the same fixture-scoped `ScreenRunStore.record()` path
  the backend test suite uses (or run the backend test itself and inspect the record it produces),
  then point a scoped frontend at that store.

**Steps:**
1. With a fixture-scoped backend serving a store whose latest record has `state: "failed"`,
   `error: "<some exact message>"`, and `failed_member: "<some symbol>"`, navigate to `/desk` on a
   frontend pointed at that backend
2. Scroll to the "Screen Runs" panel and locate the row with `state` = "failed"
   (`data-testid="desk-screen-run-state"`)
3. Confirm that row is also the "Latest run" (its date/id match the detail heading)

**Expected Result:**
- The failed row's "produced" column (`data-testid="desk-screen-run-outcome"`) reads "nothing
  recorded" (never a fabricated screen id)
- The "Latest run" detail block shows a failure block (`data-testid="desk-screen-run-latest-failed"`)
  containing the raising member's name in monospace text, followed by " — ", followed by the exact
  error string (`data-testid="desk-screen-run-latest-failed-detail"`) — byte-identical to the
  `error` field served by `GET /research/desk/screen/runs`, not truncated or reworded
- The ranked/skipped-counts line does NOT appear for this failed run

---

### UT-06 — The ranked briefing table is unchanged by this iteration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` (ranked table)

**Preconditions:**
- At least one screen has been computed (the ranked table is populated, not the "not computed"
  empty panel)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Observe the ranked members table above the "Screen Runs" panel (the main briefing table showing
   symbol/wall distance/score/class columns)
3. Click into one ranked row's drill-in anchor (per this project's own house rule, do NOT script a
   raw `click` on a table cell — click the row's own stretched link area) to confirm it still
   navigates to `/structure`

**Expected Result:**
- The ranked table's columns, row content, and layout are pixel-identical to the pre-iteration
  shipped layout (no new column, no width shift)
- Clicking a row still navigates to `/structure` as of the row's symbol/date (unchanged
  drill-through behavior)
- No horizontal scroll appears at 1440x900

---

### UT-07 — Top-up Runs and Index Reconciliation sections still render correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` (Top-up Runs, Index Reconciliation)

**Preconditions:**
- None beyond a running frontend/backend pair

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the "Top-up Runs" panel (immediately above "Index Reconciliation")
3. Scroll to the "Index Reconciliation" panel (immediately above the new "Screen Runs" panel)

**Expected Result:**
- Both panels render exactly as before this iteration — their own tables/empty-states/latest-detail
  blocks are unaffected, with no shared state leaking from the new "Screen Runs" section (e.g. no
  screen-run row text appearing inside either sibling panel)
- The visual order top-to-bottom is: ranked briefing (or not-computed panel) → Screen History (if
  applicable) → Run Screen / Top-up / Reconcile Index controls → Top-up Runs → Index Reconciliation
  → Screen Runs (new, last)

---

### UT-08 — The Screen Runs panel is discoverable without special knowledge (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk` navigation/layout

**Steps:**
1. Navigate to `http://localhost:3301/desk` as a first-time viewer
2. Scroll down the page from the top

**Expected Result:**
- The "Screen Runs" panel is reached within a single scroll gesture from the "Index Reconciliation"
  panel (same section spacing/styling as its three siblings, `className="mt-6"`)
- The panel's heading text "Screen Runs" is unambiguous and consistent in capitalization/style with
  "Top-up Runs" and "Index Reconciliation" immediately above it
- No separate navigation link, tab, or menu item is required or expected — this is a same-page
  scroll-to section, matching the plan's explicit "no nav-skeleton change"

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads, Screen Runs panel present | smoke | P1 | `/desk` |
| UT-02 | Freshly-completed run appears in ledger | happy-path | P1 | `/desk` |
| UT-03 | Duplicate click short-circuits, recorded as reused | happy-path | P1 | `/desk` |
| UT-04 | Empty state never fabricates outcome | validation | P2 | `/desk` |
| UT-05 | Failed run shows verbatim error + member | error | P2 | `/desk` |
| UT-06 | Ranked table unchanged | regression | P1 | `/desk` |
| UT-07 | Top-up Runs / Index Reconciliation unaffected | regression | P1 | `/desk` |
| UT-08 | Screen Runs panel discoverable | ux | P2 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.**
