# Phase goal-desk-iter-15 — UI Test Plan

**Phase:** goal-desk-iter-15 (Era B, Journey J-11 — history-depth disclosure on `/desk`)
**Date:** 2026-07-29
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301

---

## Context for the tester

This iteration adds exactly ONE new thing to the UI: a **`history`** column on the `/desk`
ranked briefing table (immediately right of the existing `basis` column), plus one more line
in the row's existing hover tooltip. There is no new page, no new button, no new form, and no
navigation change. Every test below exercises that one column/tooltip, plus regression checks
that nothing else on `/desk` moved or broke.

Cell text format: `history <N> sessions · from <YYYY-MM-DD>` (e.g. `history 500 sessions · from
2024-07-25`). Legacy rows (screens recorded before this iteration) show the literal text
`history not recorded in this snapshot` instead of a value — never blank, never the word
`null`. The row's hover tooltip carries the full-precision, untruncated version: `history <N>
sessions from <full ISO timestamp>` (no middle dot, no date truncation).

At the time this plan was written, the rig at `http://localhost:3301` had at least two recorded
screens: an older one (screen date `2026-07-29`) recorded before this iteration's code shipped
— its rows omit the history fields — and a newer one (screen date `2026-07-28`, snapshot id
`screen-2026-07-28-ac07c9581a4f`, 63 ranked rows) recorded during this iteration's own
verification, whose rows carry `history_sessions` ranging from 27 (symbol `HONA`) to 501, with
57 rows at 400+ (e.g. `BRK-B` at exactly 500, `history_start` `2024-07-25T04:00:00.000000Z`).
These are cited as concrete, currently-true examples, not literal values the tester must
reproduce — if the store has moved on (e.g. a fresh `Run Screen` recorded another day), use
whatever short-history (≤60) and long-history (≥400) rows are present instead.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads with the new `history` column present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301 with a reachable backend.
- No login required.
- At least one screen has ever been computed (the "Desk screen not computed yet." empty state
  is NOT showing).

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the ranked table (inside the "Briefing" panel) to finish loading
3. Look at the ranked table's header row (`<thead>`)

**Expected Result:**
- The page heading "Desk" is visible at the top of the page
- The top nav bar shows three links: "Cockpit", "Structure", "Desk"
- The ranked table's header row shows column labels in this order (rightmost two):
  `... coverage | tick evidence | basis | history`
- No red or amber error banner is visible ("The desk screen could not be loaded." / "Desk
  screen not computed yet." do NOT appear)
- No browser console errors

---

### UT-02 — Short-history and long-history rows both legible in the `history` column (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Same as UT-01
- The currently-displayed screen includes at least one ranked row with `history_sessions <= 60`
  and at least one with `history_sessions >= 400` (per the "Context for the tester" section
  above — if not currently true, use the "Run Screen" button per UT-07 to record a fresh screen,
  or click an older row in "Screen History" that has a wide split)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll the ranked table (inside "Briefing") down its rows, scrolling the table horizontally
   right if needed to bring the `history` column into view
3. Locate one row whose `history` cell shows a small session count (e.g. `history 27 sessions ·
   from <date>`)
4. Locate a different row whose `history` cell shows a large session count (e.g. `history 500
   sessions · from 2024-07-25`)
5. Take a screenshot (or resize the browser) so both rows are visible together

**Expected Result:**
- Both rows' `history` cells render the exact pattern `history <N> sessions · from
  <YYYY-MM-DD>` — a number, the literal words "sessions" and "from", and a date
- The two `<N>` values are visibly different by at least 10× (e.g. 27 vs. 500)
- No cell in the `history` column shows the literal text `null`, `undefined`, `NaN`, or is blank
- The rest of each row (symbol, side, class, distance, score, coverage badges, tick evidence,
  basis) still renders exactly as it did before — unaffected by the new column

---

### UT-03 — Hovering a row's drill-in link discloses full-precision history in the tooltip (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Same as UT-01, viewing a screen with at least one ranked row carrying `history_sessions`/
  `history_start`

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the ranked table, hover the mouse pointer over any ranked row (anywhere in the row —
   the whole row is one clickable link to `/structure`), and hold still for ~1 second
3. Read the native browser tooltip that appears

**Expected Result:**
- A tooltip appears containing, in order: a `distance ... bps` segment, a `score ...` segment, a
  `basis ...` segment, then a `history <N> sessions from <full timestamp>` segment (full
  precision — e.g. `history 500 sessions from 2024-07-25T04:00:00.000000Z`, NOT the rounded
  `2024-07-25` shown in the visible cell)
- The tooltip's `history` segment uses the word "from" with no middle dot before it (unlike the
  visible cell, which uses "· from")
- Clicking the row (anywhere in it) still navigates to a `/structure?symbol=...&asof=...` URL —
  the same click target as before this iteration, confirmed by checking the browser's address
  bar after the click

---

### UT-04 — Legacy screen row shows the honest fallback, never blank or `null` (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` — Screen History panel

**Preconditions:**
- The "Screen History" table (near the bottom of `/desk`) has more than one row, including at
  least one screen recorded before this iteration shipped (per "Context for the tester", the
  screen dated `2026-07-29` is the known pre-iteration example at the time this plan was
  written)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll down to the "Screen History" panel
3. Click a row in the history table whose "date" column reads `2026-07-29` (or, if that row is
   no longer present, the row with the OLDEST date shown)
4. Scroll back up to the "Briefing" panel's ranked table

**Expected Result:**
- After clicking, a banner appears reading "Viewing the recorded screen for 2026-07-29 — not
  the latest." with a "Latest" button beside it
- Every ranked row's `history` column cell reads exactly `history not recorded in this
  snapshot` — no session count, no date, and NOT the word `null`
- The `basis` column on those same rows still shows its own (unrelated) values normally —
  confirming only the new `history` field is affected, not the whole row
- Clicking the "Latest" button returns the page to the current/latest screen, and the `history`
  column on that screen goes back to showing real values (not the fallback text)

---

### UT-05 — Skipped-members tables never grow a `history` column (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/desk` — Skipped Members panel

**Preconditions:**
- The currently-displayed screen has at least one skipped member (check the "Skipped Members"
  panel is not showing "No members were skipped in this screen.")

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the "Skipped Members" panel
3. Inspect the header row of the "Skipped — no bars" table (if present) and the "Skipped — no
   basis session" table (if present)

**Expected Result:**
- Neither skipped-members table has a `history` column header
- Each skipped row shows only its existing columns: symbol, reason ("no bars" / "no basis"),
  coverage, tick evidence — structurally identical to before this iteration
- No skipped row shows the text "history not recorded in this snapshot" or any history-related
  text anywhere (skip rows were never ranked, so there is nothing to disclose)

---

### UT-06 — Existing row data (basis, distance, score, coverage) unchanged by the new column (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Same rig as UT-01, viewing a screen with at least 3 ranked rows

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. For any 3 ranked rows, read the `distance`, `score`, `coverage`, `tick evidence`, and `basis`
   cell values
3. Reload the page (F5)
4. Re-read the same 5 cell values for the same 3 rows

**Expected Result:**
- All 5 values for all 3 rows are identical before and after reload (the screen snapshot is a
  static, already-recorded record — nothing recomputes on page load)
- The `basis` column still shows its pre-existing format `basis <YYYY-MM-DD> · <N> d before
  as-of` (or "basis not recorded in this snapshot" for legacy rows) — unchanged by this
  iteration
- The table has exactly one new column (`history`) compared to what J-08/J-10's own test plans
  described for this table — no other column was added, removed, or reordered

---

### UT-07 — "Run Screen" and Screen History click-through still work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Run Screen / Top-up / Reconcile Index panel

**Preconditions:**
- Frontend and backend both reachable at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the "Run Screen / Top-up / Reconcile Index" panel and click the "Run Screen" button
3. Wait for the button to stop reading "Computing…" and return to "Run Screen" (or "Retry Run
   Screen" on failure)
4. Scroll to "Screen History" and confirm a row now exists (or already existed) for today's date

**Expected Result:**
- Immediately after clicking, the button becomes disabled and reads "Computing…" with a
  progress line ("`<n>` / `<total>` members")
- On completion, a line appears reading either "Recorded a new snapshot — screen-…" or "Reused
  the snapshot already recorded for this key — screen-…" (both are valid outcomes — this is the
  same idempotent-compute behavior as every prior iteration; the point is it does NOT error)
- Clicking the button did not remove or alter the `history` column — it is still present in the
  ranked table header afterward
- Clicking a row in "Screen History" still swaps the displayed snapshot and shows the "Viewing
  the recorded screen for `<date>` — not the latest." banner, exactly as before this iteration

---

### UT-08 — Top-up Runs and Index Reconciliation sections unaffected (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` — Top-up Runs / Index Reconciliation panels

**Preconditions:**
- Same rig as UT-01

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the bottom of the page, past "Screen History"
3. Read the "Top-up Runs" section and, below it, the "Index Reconciliation" section

**Expected Result:**
- Both sections render with their pre-existing content unchanged: no `history` column or any
  history-related text appears in either section's tables
- The only permissible difference from a pre-iteration screenshot is vertical position (both
  sections may sit slightly lower on the page because the wider ranked table above them takes
  more horizontal — not vertical — space; if either section appears CUT OFF, missing rows, or
  showing broken content, that is a regression, not an acceptable layout shift)

---

### UT-09 — `history` column is discoverable and uses plain, non-advisory language (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- Same rig as UT-01

**Steps:**
1. Navigate to `http://localhost:3301/desk` as a first-time viewer (no prior knowledge of this
   iteration)
2. Without consulting any documentation, look at the ranked table and try to determine what the
   `history` column means from its header label and cell content alone

**Expected Result:**
- The column header reads simply "history" (lowercase, matching the style of neighboring headers
  "coverage", "tick evidence", "basis")
- The cell content ("history 500 sessions · from 2024-07-25") is self-explanatory without needing
  to hover or click anything — a count and a date, with no jargon
- No cell or tooltip anywhere in the `history` column/detail uses advisory or judgement language
  such as "enough history", "reliable", "confidence", "buy", "watch this", or "opportunity" — the
  copy is purely descriptive (a count and a date), matching the rest of the `/desk` page's
  house style
- The column sits immediately next to "basis" (not scattered elsewhere in the row or in a
  separate panel), so a reader familiar with the existing "basis" column can infer "history" is a
  related disclosure at a glance

---

### UT-10 — Backend-unavailable state shows an honest message, not a crash (error)

**Type:** error
**Priority:** P3 (optional — requires temporarily stopping the backend; skip if that is not safe
to do on this rig, and rely on TC-10's automated coverage instead)

**Surface:** `/desk`

**Preconditions:**
- Ability to briefly stop and restart the backend process serving this rig without disrupting
  other in-progress work

**Steps:**
1. Stop the backend process
2. Navigate to (or reload) `http://localhost:3301/desk`
3. Restart the backend process afterward

**Expected Result:**
- The page does NOT crash, show a blank white screen, or show raw JSON/stack trace
- An amber panel appears with the message "The desk screen could not be loaded." and the
  sub-text "Nothing cached and nothing fabricated is shown in its place." — no fabricated
  `history` values are shown in place of real data
- After restarting the backend and reloading, the page returns to normal, and the `history`
  column shows real values again

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads with `history` column present | smoke | P1 | `/desk` |
| UT-02 | Short- and long-history rows legible together | happy-path | P1 | `/desk` |
| UT-03 | Hover tooltip discloses full-precision history | happy-path | P1 | `/desk` |
| UT-04 | Legacy row shows honest fallback, never null | validation | P2 | `/desk` (Screen History) |
| UT-05 | Skip tables never grow a `history` column | validation | P2 | `/desk` (Skipped Members) |
| UT-06 | Existing row data unchanged by new column | regression | P1 | `/desk` |
| UT-07 | Run Screen / Screen History click-through still work | regression | P1 | `/desk` |
| UT-08 | Top-up Runs / Index Reconciliation unaffected | regression | P2 | `/desk` |
| UT-09 | `history` column discoverable, plain language | ux | P2 | `/desk` |
| UT-10 | Backend-unavailable shows honest message | error | P3 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS:** UT-01, UT-02, UT-03, UT-06, UT-07.
