# Phase goal-i_will_be_super_rich-iter-8 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-8
**Date:** 2026-06-05
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Home page loads in Historical mode without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- No login required

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load (the top bar and chart area are visible)
3. Locate the mode selector in the top bar
4. Click the "Historical" option in the mode selector

**Expected Result:**
- The page renders without a blank screen, error overlay, or crash message
- The Historical mode controls are revealed: a date input, start time input, end time input, and speed input are all visible
- No "Something went wrong" or 500 error text is shown anywhere on the page
- The chart area displays its idle/placeholder state (e.g., "No ticker watched" or similar message), not a blank area or JavaScript error

---

### UT-02 — Timezone label appears immediately on entering Historical mode (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- No date has been entered in the Historical picker

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Historical" option in the mode selector to switch to Historical mode
3. Look at the area adjacent to (directly beside or directly below) the start and end time inputs — do not enter any date or time values

**Expected Result:**
- A small muted monospaced timezone label is visible without entering any date. The label shows the browser's local IANA timezone name (e.g., `Asia/Hong_Kong`, `America/New_York`, `Europe/London`)
- The label text is not empty, not "undefined", and not "null"
- A tooltip "Your date and time entry is interpreted in this timezone" appears when hovering over the label

---

### UT-03 — Quick-pick buttons are visible in Historical mode without a date (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Historical mode is selected
- The date input is empty (no date entered)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Historical" option in the mode selector
3. Leave the date field empty — do not type anything
4. Look at the row of controls in the Historical section for any quick-pick buttons

**Expected Result:**
- Three quick-pick buttons are visible: "Open 9:30 ET", "Close 16:00 ET", and "Full RTH 9:30–16:00 ET"
- All three buttons appear visually disabled: they render at approximately 40% opacity (noticeably faded compared to the active controls)
- Hovering the mouse over any of the three buttons shows a `not-allowed` cursor (the prohibited/circle-slash cursor), not the normal pointer or hand cursor

---

### UT-04 — Quick-pick buttons activate and show local annotations when a date is entered (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Historical mode is selected
- Date field is empty

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Historical" option in the mode selector
3. Click into the date input field and type `2026-06-02`
4. Click or tab away from the date field so it is committed
5. Observe all three quick-pick buttons

**Expected Result:**
- All three quick-pick buttons transition from disabled/faded to visually active (full opacity, standard interactive cursor on hover)
- Each button now shows a local-time annotation alongside the ET time, for example:
  - "Open 9:30 ET (09:30 PM local)" if in Hong Kong (Asia/Hong_Kong)
  - "Open 9:30 ET (09:30 AM local)" if in New York (America/New_York)
- The annotation reflects the actual local-time equivalent of 9:30 ET on 2026-06-02 (a weekday in EDT / UTC-04:00), which is 13:30 UTC
- The "Close 16:00 ET" button shows the local equivalent of 16:00 ET on that date
- The "Full RTH 9:30–16:00 ET" button shows both the 9:30 ET and 16:00 ET local equivalents

---

### UT-05 — "Open 9:30 ET" quick-pick fills start and end time inputs (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Historical mode is selected
- Date `2026-06-02` is entered in the date field
- Quick-pick buttons are visible and active (not faded)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Historical" option in the mode selector
3. Type `2026-06-02` in the date input field and commit it
4. Click the "Open 9:30 ET" button
5. Observe the start time and end time input fields

**Expected Result:**
- The start time input is populated with a time value. This value is the local-timezone equivalent of 9:30 ET (EDT, UTC-04:00) on 2026-06-02. For example, in Asia/Hong_Kong (UTC+8) the start time shows `21:30`; in America/New_York it shows `09:30`
- The end time input is also populated with a value that is greater than the start time (start < end is satisfied — the "Open" preset covers a small window around the open, not just a single instant)
- Neither input shows an empty value or a placeholder like "hh:mm"
- The start time field value is less than the end time field value (no inverted window)

---

### UT-06 — "Close 16:00 ET" quick-pick fills start and end time inputs (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Historical mode is selected
- Date `2026-06-02` is entered in the date field
- Quick-pick buttons are active (not faded)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Historical" option in the mode selector
3. Type `2026-06-02` in the date input field and commit it
4. Click the "Close 16:00 ET" button
5. Observe the start time and end time input fields

**Expected Result:**
- The end time input is populated with the local-timezone equivalent of 16:00 ET (EDT) on 2026-06-02. For example, in Asia/Hong_Kong (UTC+8): `00:00` (next day) or displayed as midnight; in America/New_York: `16:00`
- The start time input is populated with a value that is less than the end time value
- No input shows an empty value or the placeholder "hh:mm"
- The start time field value is less than the end time field value

---

### UT-07 — "Full RTH 9:30–16:00 ET" quick-pick fills the complete RTH window (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Historical mode is selected
- Date `2026-06-02` is entered in the date field
- Quick-pick buttons are active

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Historical" option in the mode selector
3. Type `2026-06-02` in the date input field and commit it
4. Click the "Full RTH 9:30–16:00 ET" button
5. Observe both start time and end time input fields

**Expected Result:**
- The start time input shows the local equivalent of 9:30 ET on 2026-06-02 (the same value that "Open 9:30 ET" would set as its start time)
- The end time input shows the local equivalent of 16:00 ET on 2026-06-02 (the same value that "Close 16:00 ET" would set as its end time)
- start time < end time (a span of 6.5 hours in local time, representing the full Regular Trading Hours window)
- Neither input is empty

---

### UT-08 — Historical Watch POST body contains tz-aware UTC instants (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- Browser DevTools are open to the Network tab (press F12, click "Network")
- Historical mode is selected
- Date `2026-06-02` is entered
- A valid start and end time are entered (e.g., by clicking "Open 9:30 ET" or entering manual times)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Open browser DevTools by pressing F12; click the "Network" tab; ensure recording is active
3. Click the "Historical" option in the mode selector
4. Type `2026-06-02` in the date input field and commit it
5. Click the "Open 9:30 ET" quick-pick button
6. Type `F` (for Ford) into the ticker input field
7. Click the "Watch" button
8. In the DevTools Network tab, find the request to `POST /watch/F` (or similar path containing `/watch/`)
9. Click that request and inspect its Request Payload / Body

**Expected Result:**
- The `start` field in the POST body is a string ending with `Z` or with a timezone offset (e.g., `2026-06-02T13:30:00.000Z` or `2026-06-02T09:30:00-04:00`). It must NOT be a naive string like `2026-06-02T09:30` or `2026-06-02T21:30`
- The `end` field likewise ends with `Z` or a timezone offset — it is not a naive string
- The UTC instant represented by `start` is the correct resolution of 9:30 ET on 2026-06-02: 13:30:00 UTC (since June 2 is in EDT, UTC-04:00)
- Both `start` and `end` are valid ISO-8601 strings parseable by a standard JSON/date parser

---

### UT-09 — Manual time entry after quick-pick overrides the quick-pick in the POST body (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- Browser DevTools are open to the Network tab
- Historical mode is selected; date `2026-06-02` is entered

**Steps:**
1. Navigate to `http://localhost:3650`, open DevTools (F12 → Network tab)
2. Click the "Historical" option in the mode selector
3. Type `2026-06-02` in the date input field and commit it
4. Click the "Open 9:30 ET" quick-pick button (note the start time value it sets, e.g., `21:30` in Hong Kong)
5. Click into the start time input field and change the value to `14:00` (manually overwrite the quick-pick value)
6. Type `F` in the ticker input and click "Watch"
7. In DevTools Network, find and click the `POST /watch/F` request; inspect the Request Body

**Expected Result:**
- The `start` field in the POST body reflects the manually typed `14:00`, resolved to its UTC equivalent (e.g., `2026-06-02T06:00:00.000Z` for 14:00 in Asia/Hong_Kong UTC+8), NOT the earlier quick-pick value of `2026-06-02T13:30:00.000Z`
- The quick-pick selection is visually cleared or deselected in the UI (the previously highlighted quick-pick button is no longer highlighted/active)
- The form does not submit an empty or malformed window

---

### UT-10 — Quick-pick buttons are no-op when date field is empty (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Historical mode is selected
- Date input is empty (no date entered or date was cleared)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Historical" option in the mode selector
3. Confirm the date input is empty (clear it if needed)
4. Move the mouse over the "Open 9:30 ET" button — observe the cursor
5. Click the "Open 9:30 ET" button
6. Observe the start time and end time input fields

**Expected Result:**
- The cursor is a `not-allowed` cursor (circle-slash) when hovering over the button — NOT a hand/pointer cursor
- Clicking the button does NOT populate the start time or end time fields (both remain empty or unchanged)
- No JavaScript error or crash occurs
- No network request is sent to `/watch/` (verify in DevTools Network tab if desired — no new request appears)

---

### UT-11 — End time earlier than start time is rejected (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- Historical mode is selected

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Historical" option in the mode selector
3. Type `2026-06-02` in the date input field
4. Type `16:00` in the start time input field
5. Type `09:30` in the end time input field (end is before start)
6. Type `F` in the ticker input field
7. Click the "Watch" button

**Expected Result:**
- The application does NOT silently submit a reversed window and display fabricated data
- Either: (a) the frontend shows an inline validation error message such as "End time must be after start time" before even making a network request, OR (b) the backend returns a 422 error and the frontend displays an error message visible to the user (not just a silent failure or blank chart)
- The chart area remains in its idle/empty state — no candles appear from an invalid window

---

### UT-12 — Real-historical Ford chart renders with populated candlesticks (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650 against a clean build (not a stale shared `.next`)
- Backend is running with the Ford fixture (`apps/backend/tests/fixtures/alpaca/F_20260602_150000_20260602_150200.json`) accessible
- No live credentials needed — the Ford fixture is offline-reproducible
- Historical mode will be used

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Historical" option in the mode selector
3. Type `F` in the ticker input field
4. Type `2026-06-02` in the date input field
5. In the start time input, type the local-timezone equivalent of 15:00 UTC (e.g., `23:00` if in Asia/Hong_Kong UTC+8, or `11:00` if in America/New_York EDT)
6. In the end time input, type the local-timezone equivalent of 15:02 UTC (e.g., `23:02` if in Asia/Hong_Kong, or `11:02` if in America/New_York)
7. Click the "Watch" button
8. Wait up to 10 seconds for the cockpit and chart to populate
9. Observe the chart area above (or beside) the cockpit

**Expected Result:**
- The chart area is NOT empty and does NOT show an idle "No ticker watched" or placeholder message
- Candlestick bars are rendered with real prices from the Ford fixture. Each bar has a visible body and wicks (open, high, low, close) — the bars are not all identical in height
- Tape-state markers (colored dots or flags) may be visible at state transition points on the chart timeline
- The cockpit panels show real data: bid/ask prices, recent trades with price/size, tape state, confidence score

---

### UT-13 — Bar-size selector re-renders the real-historical chart at 10s, 30s, 60s (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650 against a clean build
- Backend is running with the Ford fixture accessible
- The Ford historical window (2026-06-02 15:00–15:02 UTC, in local time) has been successfully watched and the candlestick chart is populated (see UT-12 above as the prerequisite state)

**Steps:**
1. With the populated Ford historical chart visible on `http://localhost:3650`, locate the bar-size selector (a row of buttons or a dropdown labeled "10s", "30s", "60s" or similar)
2. Note the current bar size — the chart starts at 10s; count approximately how many bars are visible
3. Click the "30s" bar-size option
4. Wait up to 3 seconds for the chart to re-render; observe the chart
5. Click the "60s" bar-size option
6. Wait up to 3 seconds for the chart to re-render; observe the chart again

**Expected Result:**
- At 10s: the chart shows the greatest number of bars (many narrow candlesticks)
- After clicking "30s": the chart re-renders and shows fewer, wider/taller bars (approximately one-third as many as 10s). The price range and overall price trajectory remain consistent with the 10s view
- After clicking "60s": the chart re-renders again and shows the fewest bars (approximately one candle per minute). Price range remains consistent
- No flickering, loading spinner stuck indefinitely, or crash at any bar-size switch
- The chart does NOT revert to the idle/placeholder state when switching bar sizes

---

### UT-14 — Empty historical window shows no fabricated data (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- Historical mode is selected

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Historical" option in the mode selector
3. Type `ZZZZZ` in the ticker input (a ticker with no data in any fixture or vendor)
4. Type `2026-01-01` in the date input (a holiday/non-trading day)
5. Type `10:00` in the start time input and `10:05` in the end time input
6. Click the "Watch" button
7. Observe the cockpit and chart area

**Expected Result:**
- The cockpit shows an explicit "no data for window" message, or a "no_data_for_window" status label, or similar text indicating no data was returned
- The chart area remains empty — no candlestick bars appear, no placeholder shapes or fabricated prices are rendered
- The application does NOT crash or display a JavaScript error overlay
- No error about "undefined" prices or NaN values appears in the chart area

---

### UT-15 — Simulated mode still renders chart after Historical picker changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- No credentials needed (Simulated mode)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Simulated" option in the mode selector
3. Type `SIM-BUYER` in the ticker input field
4. Click the "Watch" button
5. Wait up to 10 seconds for the cockpit to begin populating
6. Observe the chart area above the cockpit

**Expected Result:**
- A candlestick chart renders for the simulated buy-control scenario with upward-trending bars
- The chart is NOT empty and does NOT show the "No ticker watched" idle placeholder
- Tape-state markers (green dots or flags) are visible at buy-pressure transition points
- The cockpit panels populate with simulated bid/ask, trades, tape state, and confidence values
- No JavaScript error overlay appears

---

### UT-16 — Pause and resume still work after this iteration's changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Simulated mode is available (no credentials needed)
- A watch session is running (see UT-15 steps 1–5 to establish this state)

**Steps:**
1. With a `SIM-BUYER` Simulated watch session running and the cockpit populating, locate the "Pause" button in the top bar
2. Click the "Pause" button
3. Observe the cockpit values, chart, and event counters for 3 seconds
4. Look for a visual "PAUSED" indicator on the screen
5. Click the "Resume" button (the same button which may now read "Resume" or show a play icon)
6. Observe the cockpit values and chart for 3 seconds after resuming

**Expected Result:**
- After clicking Pause: all cockpit values (bid/ask, tape state, confidence, trade list) stop updating — they are frozen at the values they held at the moment of pause
- A visible "PAUSED" indicator, badge, or button-state change is shown on the screen
- After clicking Resume: the cockpit values begin updating again within 2–3 seconds; the chart continues rendering new bars; the event log continues appending entries
- No data is lost or reset when resuming — the counter values continue incrementing from where they paused (not reset to zero)

---

### UT-17 — Historical mode controls are discoverable within 2 clicks from home (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- User has never used the app before (fresh session / no prior state)

**Steps:**
1. Navigate to `http://localhost:3650` (home page)
2. Look at the top bar — identify a mode selector or a control labeled "Historical", "Live", "Simulated", or similar
3. Click the "Historical" option (this is the first click)
4. Observe what is revealed in the top bar without scrolling or navigating elsewhere

**Expected Result:**
- "Historical" is visible in the top bar without scrolling on a standard 1280px-wide browser window — it is not hidden in a hamburger menu or off-screen
- After clicking "Historical" (one click from the home page), all of the following are immediately visible without a second navigation action: date input, start time input, end time input, replay speed input, the timezone label, and all three quick-pick buttons
- The quick-pick buttons' labels ("Open 9:30 ET", "Close 16:00 ET", "Full RTH 9:30–16:00 ET") make their purpose self-evident to a trader — no tooltip is needed to understand what they do
- The timezone label (e.g., `Asia/Hong_Kong`) is readable and clearly associated with the time inputs — a new user would understand their entries are being interpreted in that timezone

---

### UT-18 — Timezone label is correct for the browser's local timezone (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- The tester knows the IANA timezone name of the machine running the browser (check with `Intl.DateTimeFormat().resolvedOptions().timeZone` in the browser console if needed)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Historical" option in the mode selector
3. Read the timezone label displayed adjacent to the time inputs (e.g., `Asia/Hong_Kong`, `America/New_York`, `Europe/London`)
4. Compare it to the known system timezone

**Expected Result:**
- The label text exactly matches the IANA timezone name of the machine's local timezone (e.g., `Asia/Hong_Kong` for a Hong Kong browser, `America/New_York` for a US East Coast browser)
- The label is NOT: "UTC", "undefined", "null", a raw numeric offset like "+08:00", or an abbreviated code like "HKT"
- The label does not change if the user switches between Historical and other modes and back — it is stable and reflects the system timezone, not a session variable

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home page loads in Historical mode without errors | smoke | P1 | `/` |
| UT-02 | Timezone label appears immediately on entering Historical mode | smoke | P1 | `/` |
| UT-03 | Quick-pick buttons are visible in Historical mode without a date | smoke | P1 | `/` |
| UT-04 | Quick-pick buttons activate and show local annotations when a date is entered | happy-path | P1 | `/` |
| UT-05 | "Open 9:30 ET" quick-pick fills start and end time inputs | happy-path | P1 | `/` |
| UT-06 | "Close 16:00 ET" quick-pick fills start and end time inputs | happy-path | P1 | `/` |
| UT-07 | "Full RTH 9:30–16:00 ET" quick-pick fills the complete RTH window | happy-path | P1 | `/` |
| UT-08 | Historical Watch POST body contains tz-aware UTC instants | happy-path | P1 | `/` |
| UT-09 | Manual time entry after quick-pick overrides the quick-pick in the POST body | validation | P2 | `/` |
| UT-10 | Quick-pick buttons are no-op when date field is empty | validation | P2 | `/` |
| UT-11 | End time earlier than start time is rejected | validation | P2 | `/` |
| UT-12 | Real-historical Ford chart renders with populated candlesticks | happy-path | P1 | `/` |
| UT-13 | Bar-size selector re-renders the real-historical chart at 10s, 30s, 60s | happy-path | P1 | `/` |
| UT-14 | Empty historical window shows no fabricated data | error | P2 | `/` |
| UT-15 | Simulated mode still renders chart after Historical picker changes | regression | P1 | `/` |
| UT-16 | Pause and resume still work after this iteration's changes | regression | P1 | `/` |
| UT-17 | Historical mode controls are discoverable within 2 clicks from home | ux | P2 | `/` |
| UT-18 | Timezone label is correct for the browser's local timezone | ux | P2 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.**

P1 tests: UT-01, UT-02, UT-03, UT-04, UT-05, UT-06, UT-07, UT-08, UT-12, UT-13, UT-15, UT-16
P2 tests: UT-09, UT-10, UT-11, UT-14, UT-17, UT-18
