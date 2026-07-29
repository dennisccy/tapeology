# Phase goal-desk-iter-16 — UI Test Plan

**Phase:** goal-desk-iter-16
**Date:** 2026-07-29
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301

---

## Data used by this plan

This plan is grounded in the REAL `apps/backend/.data/screen` store as inspected on 2026-07-29
(the same store the running app serves — nothing here was fabricated). Sorted oldest-recorded to
newest-recorded (the exact order `GET /research/desk/screen`'s `screens` list — and therefore the
Screen History table — renders them in):

| # (top→bottom in table) | id | screen_date | created_utc |
|---|---|---|---|
| 1 | `screen-2026-06-22-3ecd45c062c7` | 2026-06-22 | 2026-07-25T09:14:02.041409Z |
| 2 | `screen-2026-07-25-e184a7dc2f86` | 2026-07-25 | 2026-07-25T11:45:58.551296Z |
| 3 | `screen-2026-07-27-936543601e75` | 2026-07-27 | 2026-07-27T21:42:14.636275Z |
| 4 | `screen-2026-07-27-3ad3c57aa6ba` | 2026-07-27 | 2026-07-28T21:30:16.111871Z |
| 5 | `screen-2026-07-29-ce0d82b8e9bf` | 2026-07-29 | 2026-07-29T01:11:42.662560Z |
| 6 | `screen-2026-07-28-ac07c9581a4f` | 2026-07-28 | 2026-07-29T02:07:39.867805Z |

Rows 3 and 4 are the same-`screen_date` pair (`2026-07-27`) this journey exists to make both
individually reachable. Row 6 has the newest `created_utc` of all six — it is `latest`, the
default-view snapshot — even though its `screen_date` (2026-07-28) is chronologically EARLIER than
row 5's `screen_date` (2026-07-29). This is the real, on-disk, live demonstration of "most recently
recorded ≠ latest screen date" that the reworded Provenance copy (UT-07) describes. In row 3's
snapshot, symbol `NFLX`'s `1d` coverage badge has `has_bars: false` (dark); in row 4's snapshot the
same badge has `has_bars: true` (lit) — this is the exact worked example goal.md names.

**If the store has changed by the time these tests run** (new screens recorded since 2026-07-29):
locate the CURRENT two rows sharing an identical "date" column value for TC UT-02/UT-03, and the
CURRENT row with the largest "recorded" value (bottom of the table, since the table is
recorded-ascending) for UT-05/UT-06/UT-07 — the same relative logic these steps use, just with
different literal values.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301
- Backend is reachable and serving the real ambient desk store
- No login required

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Desk" (`data-testid="desk-title"`) is visible
- No blank screen, no "The desk screen could not be loaded." unavailable panel
- The following panel headings are all visible somewhere on the page: "Provenance", "Briefing",
  "Skipped Members", "Screen History", "Run Screen / Top-up / Reconcile Index", "Top-up Runs",
  "Index Reconciliation"
- No console errors

---

### UT-02 — Selecting the earlier of two same-date Screen History entries opens that exact recording (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Screen History table

**Preconditions:**
- The real ambient store contains the `2026-07-27` same-date pair (rows 3 and 4 in the Data table
  above)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Screen History" panel, locate the two adjacent rows whose "date" column both read
   `2026-07-27` (they are rows 3 and 4 from the top, immediately below the `2026-07-25` row)
3. Confirm their "recorded" column values differ (`2026-07-27T21:42:14.636275Z` vs.
   `2026-07-28T21:30:16.111871Z`)
4. Click the `2026-07-27` row whose "recorded" value is `2026-07-27T21:42:14.636275Z` (the
   EARLIER one)
5. Wait for the page to re-render

**Expected Result:**
- Only the clicked row shows a darker/highlighted background; the other `2026-07-27` row is NOT
  highlighted
- A banner reading "Viewing the recorded screen for 2026-07-27 — not the latest." appears above the
  Provenance panel, with a "Latest" button
- In the "Provenance" panel, "Snapshot id" reads `screen-2026-07-27-936543601e75` and "Recorded at"
  reads `2026-07-27T21:42:14.636275Z`
- In the "Briefing" table, the row where the leftmost cell reads "NFLX" shows its `1d` coverage
  badge in the dim/gray style (border-slate, not green) — hovering it shows a tooltip starting
  "window last requested: never" or an old date, reflecting `has_bars: false`

---

### UT-03 — Selecting the later of two same-date Screen History entries opens a distinct recording (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Screen History table

**Preconditions:**
- UT-02 has just been completed (currently viewing the earlier `2026-07-27` recording), OR start
  fresh from `http://localhost:3301/desk`

**Steps:**
1. In the "Screen History" panel, click the OTHER `2026-07-27` row — the one whose "recorded"
   column reads `2026-07-28T21:30:16.111871Z` (the LATER one)
2. Wait for the page to re-render

**Expected Result:**
- The highlight moves to this row only; the row clicked in UT-02 is no longer highlighted
- The "Provenance" panel's "Snapshot id" updates to `screen-2026-07-27-3ad3c57aa6ba` and "Recorded
  at" updates to `2026-07-28T21:30:16.111871Z`
- In the "Briefing" table, the "NFLX" row's `1d` coverage badge is now the LIT emerald/green style
  (`has_bars: true`) — visibly different from UT-02's dark badge, proving the two same-date
  recordings serve genuinely different data
- The "Screen date" row in Provenance still reads `2026-07-27` for both UT-02 and UT-03 (only the
  id/recorded-at/data differ, confirming this is the SAME date, DIFFERENT recording)

---

### UT-04 — Screen History "recorded" column shows distinct timestamps for same-date rows (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk` — Screen History table

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Screen History" table header row, confirm a column labeled "recorded" appears between
   "date" and "rows"
3. Read the "recorded" column value for each of the two rows dated `2026-07-27`

**Expected Result:**
- The "recorded" column header is present
- Every row in the table has a non-empty "recorded" value
- The two `2026-07-27` rows show two DIFFERENT "recorded" values (`2026-07-27T21:42:14.636275Z` and
  `2026-07-28T21:30:16.111871Z`) even though their "date" column is identical

---

### UT-05 — Default (no selection) view highlights the most-recently-RECORDED row, not the chronologically-latest date (ux)

**Type:** ux
**Priority:** P1
**Surface:** `/desk` — Screen History table

**Steps:**
1. Navigate to `http://localhost:3301/desk` (fresh load — do not click any Screen History row)
2. In the "Screen History" table, find the LAST row (bottom of the table) — dated `2026-07-28`,
   recorded `2026-07-29T02:07:39.867805Z`
3. Confirm that row alone shows the highlighted/darker background
4. Look for the row dated `2026-07-29` (the second-to-last row) and confirm it is NOT highlighted

**Expected Result:**
- Exactly one row is highlighted by default: the one with the newest "recorded" value
  (`2026-07-29T02:07:39.867805Z`, dated `2026-07-28`)
- The `2026-07-29`-dated row (recorded earlier, at `2026-07-29T01:11:42.662560Z`) is visibly NOT
  highlighted, even though its date is chronologically later — this demonstrates that highlighting
  now tracks `id`/recorded-at, not calendar date

---

### UT-06 — Provenance panel shows the exact displayed snapshot's identity, including a recorded-at/screen-date divergence (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` — Provenance panel

**Steps:**
1. Navigate to `http://localhost:3301/desk` (fresh load, no history row clicked)
2. In the "Provenance" panel, read every row top to bottom

**Expected Result:**
- Rows appear in this exact order: "Snapshot id", "Recorded at", "Universe snapshot", "Screen
  date", "As of", "Config fingerprint", "Bar-store signature"
- "Snapshot id" reads `screen-2026-07-28-ac07c9581a4f`
- "Recorded at" reads `2026-07-29T02:07:39.867805Z`
- "Screen date" reads `2026-07-28` — an EARLIER calendar date than "Recorded at"'s own day
  (2026-07-29), directly illustrating why "most recently recorded" and "latest screen date" are
  different claims

---

### UT-07 — Default-view Provenance note reads "most recently recorded," never "latest screen date" (ux)

**Type:** ux
**Priority:** P1
**Surface:** `/desk` — Provenance panel

**Steps:**
1. Navigate to `http://localhost:3301/desk` (do not click any Screen History row)
2. Locate the small note text below the Provenance panel's metric rows (below "Bar-store
   signature")
3. Read the note text in full
4. Separately, scan the Screen History table for the `2026-07-29`-dated row noted in UT-05/UT-06

**Expected Result:**
- The note reads exactly: "This is the most recently recorded screen (by recorded-at time), not
  necessarily the latest screen date — an earlier same-date recording can still exist and be opened
  from Screen History below."
- The note does NOT read anything implying the displayed snapshot is simply "the latest date"
- No advice, imperative, or urgency language appears anywhere in the note (no "should", "buy",
  "watch", "opportunity")
- The `2026-07-29`-dated row IS visible in Screen History, concretely confirming the note's own
  claim that a later calendar date can exist without being the recorded-latest snapshot

---

### UT-08 — Default-view note disappears/reappears correctly as the operator navigates history, and "Latest" reverts fully (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` — Provenance panel + Screen History

**Preconditions:**
- UT-07's default-view note is currently visible

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Confirm the default-view note (UT-07's text) is visible
3. Click any Screen History row OTHER than the highlighted (bottom) row — e.g. the `2026-07-25` row
4. Confirm the note is gone, and a "Viewing the recorded screen for 2026-07-25 — not the latest."
   banner with a "Latest" button appears above Provenance
5. Click the "Latest" button

**Expected Result:**
- After step 3: the default-view note (`data-testid="desk-provenance-latest-note"`) is no longer
  rendered; Provenance shows the `2026-07-25` row's own "Snapshot id"
  (`screen-2026-07-25-e184a7dc2f86`) and "Recorded at" (`2026-07-25T11:45:58.551296Z`)
- After step 5: the "Viewing the recorded screen for..." banner disappears; Provenance reverts to
  "Snapshot id" `screen-2026-07-28-ac07c9581a4f` / "Recorded at" `2026-07-29T02:07:39.867805Z`
  (UT-06's values); the default-view note reappears with its exact UT-07 text; the bottom Screen
  History row is highlighted again

---

### UT-09 — Single-recording history dates still open correctly after the id-based switch (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` — Screen History table

**Preconditions:**
- At least one `screen_date` in the store has exactly ONE recording (every date except `2026-07-27`
  in the current store — e.g. `2026-06-22`, `2026-07-25`, `2026-07-29`, `2026-07-28`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Click the row dated `2026-06-22` (`screen-2026-06-22-3ecd45c062c7`, the only recording for that
   date)
3. Wait for the page to re-render

**Expected Result:**
- Only that row is highlighted
- "Provenance" panel's "Snapshot id" reads `screen-2026-06-22-3ecd45c062c7` and "Screen date" reads
  `2026-06-22`
- The Briefing table updates to that snapshot's rows
- No error/fetch-failure note appears (`data-testid="desk-history-fetch-error"` is absent) — the
  id-based rewrite behaves identically to the old date-based click for every date that only has one
  recording (the overwhelming majority of real dates)

---

### UT-10 — No integrity-error note renders for any of the three ledgers when the store has zero corrupted files (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk` — Screen History, Top-up Runs, Index Reconciliation panels

**Preconditions:**
- Real ambient store, no corrupted files planted (the store's current honest state per the dev
  handoff)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Inspect the "Screen History" panel below its table
3. Inspect the "Top-up Runs" panel below its run table/latest-run detail
4. Inspect the "Index Reconciliation" panel below its run table/latest-run detail

**Expected Result:**
- None of the three panels shows an amber note containing the phrase "failed an integrity check"
- No empty-array placeholder text (e.g. "0 files failed...") appears either — the note is fully
  absent, not present-but-empty, whenever a ledger's `integrity_errors` array is empty

---

### UT-11 — Screen History integrity-error note names a corrupted screen-record file when present (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` — Screen History panel

**Preconditions:**
- A scoped backend instance is running with `TAPEOLOGY_DESK_SCREEN_DIR` pointed at a temporary
  directory that is a `cp -a` copy of the real `apps/backend/.data/screen` store PLUS one
  additional file (e.g. `screen-corrupt-001.json`) whose JSON either fails to parse or whose
  `file_checksum` does not match its `record` content — this file is NEVER written into
  `apps/backend/.data`
- The frontend at http://localhost:3301 is configured (via its baked `NEXT_PUBLIC_API_URL`, or a
  rebuild pointed at the scoped backend's port) to read from that scoped backend

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Locate the "Screen History" panel
3. Look below the history table for an amber note
4. Take a screenshot of the note

**Expected Result:**
- A note reading "1 file failed an integrity check and is excluded: screen-corrupt-001.json" (exact
  count and filename will match whatever was planted) is visible directly below the Screen History
  table
- The corrupt record does NOT appear as a row in the Screen History table
- The rest of the Screen History table (genuine records) renders normally

---

### UT-12 — Top-up Runs integrity-error note names a corrupted run-record file when present (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` — Top-up Runs panel

**Preconditions:**
- A scoped backend instance is running with `TAPEOLOGY_DESK_TOPUP_LOG_DIR` pointed at a temporary
  directory that is a `cp -a` copy of the real top-up run store PLUS one additional file (e.g.
  `topup-run-corrupt-001.json`) that fails to parse or fails its `file_checksum` verification —
  never written into `apps/backend/.data`
- The frontend at http://localhost:3301 is reading from that scoped backend

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Locate the "Top-up Runs" panel
3. Look below the run table / latest-run detail for an amber note
4. Take a screenshot of the note

**Expected Result:**
- A note reading "1 file failed an integrity check and is excluded: topup-run-corrupt-001.json"
  (exact count/filename per the planted file) is visible in the Top-up Runs panel
- The corrupt record is absent from both the runs table and the latest-run detail
- Genuine top-up runs still render normally in the table

---

### UT-13 — Index Reconciliation integrity-error note names a corrupted run-record file when present (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk` — Index Reconciliation panel

**Preconditions:**
- A scoped backend instance is running with `TAPEOLOGY_DESK_INDEX_RECONCILE_DIR` pointed at a
  temporary directory that is a `cp -a` copy of the real reconcile-run store PLUS one additional
  file (e.g. `reconcile-run-corrupt-001.json`) that fails to parse or fails its `file_checksum`
  verification — never written into `apps/backend/.data`
- The frontend at http://localhost:3301 is reading from that scoped backend

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Locate the "Index Reconciliation" panel
3. Look below the run table / latest-run detail for an amber note
4. Take a screenshot of the note

**Expected Result:**
- A note reading "1 file failed an integrity check and is excluded: reconcile-run-corrupt-001.json"
  (exact count/filename per the planted file) is visible in the Index Reconciliation panel
- The corrupt record is absent from both the runs table and the latest-run detail
- Genuine reconciliation runs still render normally in the table

---

### UT-14 — No "Universe" ledger list exists anywhere on `/desk` (documented gap, ux)

**Type:** ux
**Priority:** P3
**Surface:** `/desk` (whole page)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll through the ENTIRE page from top to bottom
3. Look for any table or list showing multiple registered universe snapshots (distinct from the
   single "Universe snapshot" row inside the Provenance panel)

**Expected Result:**
- No such section exists anywhere on the page
- The only place a universe-snapshot id appears is the single "Universe snapshot" `Metric` row
  inside the Provenance panel (already present before this iteration)
- This is a documented, known gap for this iteration (goal.md named a fourth "Universe" ledger
  integrity line, but no Universe list section exists in the frontend to attach it to — see the
  ui-impact-analyst's "Not Visible Yet" note) — NOT a regression to fail this test over, only a
  sanity check that nothing broke or half-rendered

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads without errors | smoke | P1 | `/desk` |
| UT-02 | Earlier same-date entry opens its own recording | happy-path | P1 | `/desk` Screen History |
| UT-03 | Later same-date entry opens a distinct recording | happy-path | P1 | `/desk` Screen History |
| UT-04 | "recorded" column shows distinct timestamps | smoke | P1 | `/desk` Screen History |
| UT-05 | Default highlight tracks recorded-at, not date | ux | P1 | `/desk` Screen History |
| UT-06 | Provenance shows exact snapshot identity | happy-path | P1 | `/desk` Provenance |
| UT-07 | Default note reads "most recently recorded" | ux | P1 | `/desk` Provenance |
| UT-08 | Note toggles correctly; "Latest" reverts fully | regression | P2 | `/desk` Provenance |
| UT-09 | Single-recording dates still open correctly | regression | P1 | `/desk` Screen History |
| UT-10 | No false-positive integrity note with clean data | regression | P2 | `/desk` (3 ledgers) |
| UT-11 | Screen History integrity-error note visible | error | P2 | `/desk` Screen History |
| UT-12 | Top-up Runs integrity-error note visible | error | P2 | `/desk` Top-up Runs |
| UT-13 | Index Reconciliation integrity-error note visible | error | P2 | `/desk` Index Reconciliation |
| UT-14 | No Universe ledger section exists (documented gap) | ux | P3 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Note on coverage:** No "validation" (form-input) test case is included — J-12 adds no new form or
input control; every surface changed this iteration is either a read-only click-through (Screen
History rows) or a passively-rendered disclosure (Provenance rows, integrity-error notes). The
functional test plan (`reports/qa/goal-desk-iter-16-test-plan.md`) already covers the one
input-shaped edge case reachable only via direct API/MCP calls, not through any `/desk` UI control
(TC-04, `?id=`+`?date=` together → 4xx refusal — the frontend never constructs such a request).
