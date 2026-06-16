# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-29 — UI Test Plan

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-29
**Date:** 2026-06-16
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Context

No UI source files changed in this iteration. All three surfaces below existed before this
iteration; the iteration's goal was to verify them on a real live IEX feed. Test cases here
therefore have more regression and verification character than new-feature character. The API
test cases (TC-01, TC-15 through TC-18 in the functional plan) are not duplicated here — only
user-visible browser interactions appear in this plan.

---

## Test Cases

---

### UT-01 — Cockpit home page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend is running (probe: `curl http://localhost:8000/health` returns HTTP 200)
- Frontend is running at http://localhost:3650
- No watch has been started yet

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load (no loading spinner visible)
3. Observe the cockpit layout

**Expected Result:**
- Page renders without a blank screen or JavaScript error overlay
- The cockpit panel grid is visible (status area, bid/ask panel, recent-trades panel, confidence panel, thesis strip are all present)
- The sound toggle control is visible somewhere in the cockpit header or status area
- No red error banner or "Something went wrong" text is visible

---

### UT-02 — Journal page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/journal`

**Preconditions:**
- Backend is running
- Frontend is running at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650/journal`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or JavaScript error overlay
- A table or list area is visible (even if empty)
- No red error banner or "Something went wrong" text is visible

---

### UT-03 — Live watch shows "live" status indicator (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- US regular market session is OPEN (Mon-Fri, 9:30 AM–4:00 PM US Eastern)
- Backend is running with `ALPACA_API_KEY` and `ALPACA_API_SECRET` loaded from `apps/backend/.env`
- Frontend is running at http://localhost:3650
- No active watch is running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Locate the symbol input field in the cockpit (labelled "Symbol" or similar — the text entry near the Watch button)
3. Type `F` into the symbol input field
4. Click the "Watch" button (or press Enter if the field submits on Enter)
5. Wait up to 15 seconds for the cockpit to transition from "connecting" to a live state
6. Observe the status dot and label in the cockpit status area

**Expected Result:**
- The status dot is green (emerald color, visually distinct from amber/grey)
- The label next to the dot reads exactly `live`
- The recent-trades count begins advancing (new rows appear as market prints arrive)

---

### UT-04 — FeedBasisBadge renders "IEX (live)" with disclosure text (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- A live IEX watch is active on symbol `F` (status indicator reads `live` — complete UT-03 first)
- Frontend is running at http://localhost:3650

**Steps:**
1. Remain on `http://localhost:3650` with an active live watch on `F`
2. Locate the `FeedBasisBadge` in the cockpit status area (adjacent to or below the status dot and label)
3. Read the text displayed in the badge

**Expected Result:**
- The badge displays text containing `IEX (live)` or `iex`
- A disclosure line is visible in the cockpit viewport reading: "live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ"
- The disclosure line is legible (not truncated, not hidden behind a tooltip requiring hover)

---

### UT-05 — Status indicator flips to "stale" during feed lull (happy path / verification)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- A live IEX watch is active on symbol `F` and status reads `live` (complete UT-03 first)
- Operator is prepared to observe the cockpit continuously for up to 60 seconds
- A natural IEX feed lull (no new prints for more than 10 seconds) is expected during a moderately-quiet moment

**Steps:**
1. Remain on `http://localhost:3650` with the live watch on `F` showing status `live`
2. Note the current recent-trades count displayed in the cockpit (e.g., "47 trades")
3. Wait and watch the status indicator — do not interact with the page
4. When the status dot and label visibly change from green `live` to amber `stale` (this happens after 10 seconds of no feed activity), observe the cockpit immediately
5. Note that the recent-trades count has NOT changed since step 2 (it remains frozen at the same number)
6. Continue watching — when the next real market print arrives, observe the status dot and label

**Expected Result:**
- The status dot turns amber (or neutral/grey — visually distinct from the green used for `live`) and the label reads exactly `stale`
- The recent-trades count is frozen at the same number it held when `stale` appeared — no new rows were added during the gap
- After the next real market print arrives, the status dot returns to green and the label returns to `live`
- The count begins advancing again after recovery

---

### UT-06 — Live thesis declaration produces an IEX-stamped journal row (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` and `/journal`

**Preconditions:**
- A live IEX watch is active on symbol `F` and status reads `live`
- Frontend is running at http://localhost:3650
- The thesis strip in the cockpit is visible (idle state — no active thesis)

**Steps:**
1. Remain on `http://localhost:3650` with the active live watch on `F`
2. Locate the thesis strip at the bottom of the cockpit panel
3. Click the thesis entry field or the "Declare thesis" button in the thesis strip
4. Type a thesis text such as `absorption_reversal long` into the thesis input
5. Submit the thesis (click "Submit" or "Declare" button, or press Enter)
6. Confirm the UI acknowledges the thesis (the thesis strip updates to show an active/pending thesis — no error message appears)
7. Navigate to `http://localhost:3650/journal`
8. Locate the most recently created row in the journal table (it should correspond to the thesis just declared)
9. Find the `data_feed` column in that row

**Expected Result:**
- The thesis is accepted without an error message in the cockpit
- In the `/journal` table, a row exists for the declared thesis
- The `data_feed` column for that row reads `iex` (not `sim`, not `sip`, not blank)
- No other rows in the same session show `sip` mixed with `iex` (no feed pooling)

---

### UT-07 — "stale" indicator is visually distinct from "live" (UX)

**Type:** ux
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Operator has observed both `live` and `stale` states during UT-05 (or can reproduce them)

**Steps:**
1. Remain on `http://localhost:3650` during or after observing a `stale` transition
2. Compare the visual treatment of the status dot and label in the `stale` state versus the `live` state (from memory or a screenshot taken during UT-03)

**Expected Result:**
- The `stale` state uses a clearly different color from `live`: the dot is amber or neutral (not green/emerald)
- The label text changes from `live` to `stale`
- The visual change is noticeable without needing to read the label text — the color contrast alone communicates the state change
- The layout of the status area (dot position, label position) does not shift when the state changes

---

### UT-08 — Unknown symbol shows explicit failure message (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend is running
- Frontend is running at http://localhost:3650
- No active watch is running (or stop the current watch first)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `ZZZNOEXIST` into the symbol input field
3. Click the "Watch" button (or press Enter)
4. Wait up to 15 seconds for the cockpit to respond

**Expected Result:**
- The cockpit displays an explicit failure or error message — something like "not a tradable symbol" or an error panel with a clear explanation
- The cockpit does NOT show a valid tape state (no `buyer_control`, `seller_control`, `bid_absorption`, etc.)
- The cockpit does NOT show a blank screen or a stuck "connecting" spinner indefinitely
- No fabricated bid/ask prices or trade data appears

---

### UT-09 — Cockpit layout unchanged — full panel grid, idle thesis strip, sound toggle (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend is running
- Frontend is running at http://localhost:3650
- A watch is active (use symbol `F` in simulated mode or any valid symbol) with no thesis declared

**Steps:**
1. Navigate to `http://localhost:3650`
2. Start a watch on `F` (or use any symbol that produces a valid cockpit state)
3. Do NOT declare a thesis
4. Scan the full cockpit viewport carefully

**Expected Result:**
- All expected panels are visible and in their correct positions:
  - Status area (stream status dot + label + FeedBasisBadge)
  - Bid/ask panel (current bid and ask prices)
  - Recent-trades panel (list of recent prints)
  - Confidence panel (tape state + confidence score)
  - Thesis strip at the bottom (shows an idle/placeholder state, not removed)
- The sound toggle control is visible (not hidden or displaced)
- No panel is missing, collapsed, or pushed off-screen
- Layout matches the same visual structure seen in previous iterations

---

### UT-10 — Journal page shows data_feed column for existing rows (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/journal`

**Preconditions:**
- Backend is running
- Frontend is running at http://localhost:3650
- At least one journal row exists (created in a prior session or during UT-06 above)

**Steps:**
1. Navigate to `http://localhost:3650/journal`
2. Wait for the table to load
3. Locate the `data_feed` column in the table header
4. Observe the values in the `data_feed` column for each row

**Expected Result:**
- The `data_feed` column is visible in the table
- Each row in the table shows a non-blank value in the `data_feed` column (e.g., `iex`, `sip`, or `sim`)
- Rows produced during a live IEX watch show `iex`; rows produced during historical/SIP replay show `sip` or similar — the two are never mixed on the same row

---

### UT-11 — FeedBasisBadge disclosure text is legible without scrolling (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- A live IEX watch is active on `F` and the badge reads `IEX (live)` (complete UT-04 first)

**Steps:**
1. Remain on `http://localhost:3650` with the active live watch
2. Without scrolling, look at the cockpit status area
3. Locate the disclosure line: "live verdicts read the single-venue IEX feed; historical replay and studies use SIP — spreads and prints differ"

**Expected Result:**
- The full disclosure line is readable in the cockpit viewport without scrolling
- The text is not truncated with an ellipsis
- The text is not hidden behind a collapsed accordion, tooltip, or "show more" toggle — it is displayed inline

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit home loads without errors | smoke | P1 | `/` |
| UT-02 | Journal page loads without errors | smoke | P1 | `/journal` |
| UT-03 | Live watch shows "live" status indicator | happy-path | P1 | `/` |
| UT-04 | FeedBasisBadge renders "IEX (live)" + disclosure | happy-path | P1 | `/` |
| UT-05 | Status indicator flips to "stale" during feed lull | happy-path | P1 | `/` |
| UT-06 | Live thesis produces IEX-stamped journal row | happy-path | P1 | `/` and `/journal` |
| UT-07 | "stale" indicator visually distinct from "live" | ux | P1 | `/` |
| UT-08 | Unknown symbol shows explicit failure message | regression | P1 | `/` |
| UT-09 | Full panel grid, idle thesis strip, sound toggle present | regression | P1 | `/` |
| UT-10 | Journal shows data_feed column for existing rows | regression | P2 | `/journal` |
| UT-11 | FeedBasisBadge disclosure legible without scrolling | ux | P2 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Note:** UT-03, UT-04, UT-05, UT-06, and UT-07 require an OPEN US market session and valid
Alpaca IEX credentials in `apps/backend/.env`. If the market is closed, mark these tests
"DEFERRED (market closed)" — they cannot be executed against a real live IEX feed outside
market hours. UT-08, UT-09, and UT-10 can run at any time.
