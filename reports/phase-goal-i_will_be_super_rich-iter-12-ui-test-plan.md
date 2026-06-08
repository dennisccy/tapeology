# Phase goal-i_will_be_super_rich-iter-12 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-12
**Date:** 2026-06-09
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Home cockpit loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- Backend is running at `http://localhost:8000`

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Wait for the page to fully load (allow up to 5 seconds)
3. Observe the main cockpit layout

**Expected Result:**
- Page renders without a blank screen or error message
- A price chart pane is visible on the page
- A control row containing a ticker field and a "Watch" button is visible
- The Historical mode controls include a text input field (not a native date picker calendar widget) with the placeholder text `dd-MM-yyyy`
- No red error banners or unhandled exception messages are shown

---

### UT-02 — Simulated chart axis shows synthetic session-clock times (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- Backend is running at `http://localhost:8000`
- The simulated ticker `SIM-BUYER` is available (no external market data required)

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Locate the ticker input field at the top of the cockpit
3. Clear any existing value and type `SIM-BUYER` into the ticker field
4. Click the "Watch" button
5. Wait up to 30 seconds for bars to appear in the price chart pane
6. Observe the labels on the horizontal (time) axis of the price chart

**Expected Result:**
- The price chart renders with at least 1 candle bar visible
- The horizontal axis tick labels show dates and times in the format `dd-MM-yyyy HH:mm:ss` (e.g., `02-01-2024 09:30:00`) — not bare elapsed-second numbers like `0`, `60`, or `120`
- The format `YYYY-MM-DD` (ISO) and locale formats like `Jan 2` must NOT appear on the axis

---

### UT-03 — Historical chart axis shows real market clock times (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- Backend is running at `http://localhost:8000`
- Historical bar data for ticker `AAPL` is available for the date `08-01-2024` (08 January 2024)

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Locate the mode selector and ensure "Historical" mode is selected
3. Locate the ticker input field and type `AAPL`
4. Locate the date input field (a text box showing the placeholder `dd-MM-yyyy`)
5. Click the date input field and type `08-01-2024`
6. Set the start time to `09:30` and end time to `11:00` in the time fields (if visible)
7. Click the "Watch" button
8. Wait up to 30 seconds for at least 5 bars to appear in the price chart

**Expected Result:**
- The price chart renders with at least 5 candle bars visible
- The horizontal axis tick labels show dates and times in the format `dd-MM-yyyy HH:mm:ss` (e.g., `08-01-2024 09:30:00`)
- No elapsed-second counter (`0`, `60`, `120`, `600`) appears on the horizontal axis
- The watched-source descriptor at the top of the cockpit panel reads something like `historical AAPL 08-01-2024 09:30` — using `dd-MM-yyyy` notation, NOT raw ISO strings like `2024-01-08T13:30:00.000Z`

---

### UT-04 — Crosshair tooltip shows true clock time on hover (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- A `SIM-BUYER` or historical chart with at least 5 visible bars is displayed (complete UT-02 or UT-03 first)

**Steps:**
1. With the populated price chart visible at `http://localhost:3650/`
2. Move the mouse cursor slowly over the middle of the candlestick area until a crosshair appears
3. Observe the crosshair tooltip / legend label showing the time of the hovered candle

**Expected Result:**
- The crosshair or chart legend displays a timestamp in the format `dd-MM-yyyy HH:mm:ss` (e.g., `02-01-2024 09:30:30`)
- The displayed timestamp is NOT an elapsed-second value (e.g., `30` or `30.5`)
- The displayed timestamp is NOT an ISO format string (e.g., `2024-01-02T09:30:30Z`)

---

### UT-05 — Tape-state marker labels show true clock time (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- A `SIM-BUYER` watch has been started and bars are visible in the chart (complete UT-02 first)
- At least one tape-state marker (e.g., labeled `buyer_control`) has appeared on the chart

**Steps:**
1. With the `SIM-BUYER` chart loaded at `http://localhost:3650/`
2. Wait until a tape-state classification marker (a colored vertical line or label on the chart) becomes visible
3. Observe the timestamp label attached to the marker

**Expected Result:**
- The tape-state marker label shows a timestamp in the format `dd-MM-yyyy HH:mm:ss` (e.g., `02-01-2024 09:30:19`)
- The marker timestamp is NOT a bare elapsed-second value like `19` or `19.5`
- The classification label (e.g., `buyer_control`) is still visible alongside the time

---

### UT-06 — Bar-size switcher preserves real-clock time axis (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- A `SIM-BUYER` chart with bars visible is displayed at `http://localhost:3650/` (complete UT-02 first)

**Steps:**
1. With the populated chart visible, locate the bar-size control (buttons labeled `10`, `30`, `60` for seconds, or similar)
2. Note the current axis time label format (confirm it shows `dd-MM-yyyy HH:mm:ss`)
3. Click the `30` (30-second) bar-size button
4. Wait for the chart to re-render
5. Observe the horizontal axis tick labels
6. Click the `60` (60-second) bar-size button
7. Wait for the chart to re-render
8. Observe the horizontal axis tick labels

**Expected Result:**
- After switching to 30-second bars: the axis tick labels still show `dd-MM-yyyy HH:mm:ss` format, NOT elapsed seconds
- After switching to 60-second bars: the axis tick labels still show `dd-MM-yyyy HH:mm:ss` format, NOT elapsed seconds
- The base clock anchor (the session start date visible in the leftmost tick) does not change between bar sizes

---

### UT-07 — Historical date input accepts valid dd-MM-yyyy entry (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- Historical mode controls are visible on the page

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Ensure Historical mode is selected in the mode selector
3. Locate the date input field — it must be a plain text input (not a browser calendar popup)
4. Click the date input field to focus it
5. Type `15-03-2024` into the field
6. Click anywhere outside the field (or press Tab) to trigger any blur validation
7. Observe whether the "Watch" button is enabled or disabled

**Expected Result:**
- The date field accepts the typed text `15-03-2024` without immediately rejecting it
- No amber/red border appears around the field
- No inline error message appears near the field
- The "Watch" button becomes enabled (not grayed out)

---

### UT-08 — Historical date input rejects impossible date with inline validation (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- Historical mode controls are visible on the page

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Ensure Historical mode is selected
3. Locate the date input field (text box with placeholder `dd-MM-yyyy`)
4. Click the date input field and type `31-02-2026` (February 31 does not exist)
5. Click anywhere outside the field (or press Tab) to trigger blur validation

**Expected Result:**
- The date input field border turns amber (or red/orange) — a visible color change indicating an error
- An inline error message appears near the field (e.g., "Invalid date", "Date does not exist", or similar wording)
- The "Watch" button remains disabled (grayed out) and cannot be clicked to submit

---

### UT-09 — Historical date input rejects malformed entry with inline validation (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- Historical mode controls are visible

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Ensure Historical mode is selected
3. Locate the date input field
4. Click the date input field and type `2024-03-15` (ISO format — wrong format for this field)
5. Click anywhere outside the field (or press Tab) to trigger blur validation
6. Observe the field state and the "Watch" button
7. Clear the field (select all, delete) and then click away with the field empty
8. Observe the field state and the "Watch" button

**Expected Result:**
- After typing `2024-03-15`: the field border turns amber and an inline error message appears; "Watch" remains disabled
- After clearing the field: the field border turns amber (or remains in error state) and an inline error message appears indicating the field is required or the format is invalid; "Watch" remains disabled
- At no point does the "Watch" button become enabled while the date field shows an error or is empty

---

### UT-10 — Market-status "next open" time shows dd-MM-yyyy HH:mm UTC format (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- The app is viewed when the market is closed (outside US Eastern trading hours: before 09:30 or after 16:00 US Eastern, or on a weekend)

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Locate the market-status indicator panel (typically in the top bar or cockpit panel)
3. Look for a "next open" or "market closed" time display
4. Observe the date and time format shown

**Expected Result:**
- The "next open" time reads in the format `dd-MM-yyyy HH:mm UTC+HH:MM` (e.g., `09-06-2026 09:30 UTC+08:00`)
- The format does NOT show locale-specific shorthand like `Jun 9` or `Mon, Jun 9`
- The format does NOT show ISO `YYYY-MM-DD` (e.g., `2026-06-09`)
- An explicit UTC offset label (e.g., `UTC+08:00`, `UTC-05:00`) is visible alongside the time

---

### UT-11 — Watched-source descriptor shows dd-MM-yyyy dates (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- A historical watch for `AAPL` with date `08-01-2024` has been started and bars are visible (complete UT-03 first)

**Steps:**
1. With the historical AAPL chart loaded at `http://localhost:3650/`
2. Locate the watched-source descriptor text at the top of the cockpit panel (the line describing the currently watched tape, e.g., "historical AAPL …")
3. Read the date portions of the descriptor text

**Expected Result:**
- The descriptor contains dates in `dd-MM-yyyy` format (e.g., `08-01-2024 09:30`)
- The descriptor does NOT contain raw ISO-8601 instants like `2024-01-08T13:30:00.000Z`
- The descriptor does NOT contain `YYYY-MM-DD` ISO date format (e.g., `2024-01-08`)

---

### UT-12 — Empty historical window shows empty chart without fabricated timestamps (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- Backend is running at `http://localhost:8000`

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Ensure Historical mode is selected
3. Click the date input field and type `06-07-2024` (a Saturday — no market data)
4. Click away to confirm no validation error (Saturday is a valid calendar date in `dd-MM-yyyy` format)
5. Set start time to `09:30` and end time to `10:00` if time fields are visible
6. Click the "Watch" button
7. Wait up to 15 seconds for the chart to finish loading
8. Observe the price chart pane

**Expected Result:**
- The chart pane is empty (no candle bars rendered)
- The chart shows the message "No price history for this window yet" or equivalent empty-state hint
- The horizontal time axis does NOT show fabricated timestamps or arbitrary placeholder times
- The page does not crash or show an unhandled error

---

### UT-13 — Simulated chart classification still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- Backend is running at `http://localhost:8000`
- `SIM-BUYER` ticker is available

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Clear the ticker field and type `SIM-BUYER`
3. Click the "Watch" button
4. Wait up to 60 seconds for bars to populate the chart and for at least one tape-state classification marker to appear
5. Observe whether a tape-state label (e.g., `buyer_control`) appears in the chart or in the classification panel below the chart

**Expected Result:**
- The price chart renders bars as before
- A tape-state classification label such as `buyer_control` appears (in the chart as a marker, or in a classification panel) — confirming the backend classification pipeline was not broken by the epoch anchor changes
- The confidence score (if shown) is a numeric percentage value, not zero or empty

---

### UT-14 — Historical watch resolves correct date window, no UTC shift (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- Backend is running at `http://localhost:8000`
- Historical data for `AAPL` on `08-01-2024` is available

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Ensure Historical mode is selected
3. Type `AAPL` in the ticker field
4. Click the date input field and type `08-01-2024`
5. Set start time to `09:30` and end time to `10:30` in the time fields
6. Click the "Watch" button
7. Wait for bars to appear in the chart
8. Observe the leftmost bar's timestamp on the horizontal axis

**Expected Result:**
- The leftmost visible bar on the chart starts at or near `08-01-2024 09:30` (local time) — confirming the `dd-MM-yyyy` custom input resolves to the same local instant as the old native date picker
- The chart does NOT start at `08-01-2024 14:30` or another UTC-offset time (which would indicate a UTC shift regression)
- The watched-source descriptor confirms the date as `08-01-2024`

---

### UT-15 — Native date picker is NOT present (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- Historical mode is selected

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Select Historical mode if not already active
3. Click the date input field
4. Observe whether a native browser calendar popup appears

**Expected Result:**
- No browser-native calendar popup or date picker widget opens when clicking the date field
- The field behaves as a plain text input: a text cursor appears inside the field
- The field shows the placeholder text `dd-MM-yyyy` when empty
- The field accepts typed characters (keyboard input)

---

### UT-16 — Simulated chart date format consistent with historical chart format (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at `http://localhost:3650`
- Both a simulated (`SIM-BUYER`) and a historical (`AAPL` on `08-01-2024`) chart can be loaded

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Load `SIM-BUYER` (click Watch) and note the format of the axis tick labels
3. Navigate back or change the ticker to `AAPL` with date `08-01-2024` and click Watch
4. Compare the axis tick label format of both charts

**Expected Result:**
- Both the simulated chart and the historical chart use the same `dd-MM-yyyy HH:mm:ss` format on the time axis
- There is no inconsistency where one chart shows clock time and the other shows elapsed seconds
- The overall chart UI layout (candle style, colors, panel positions) is unchanged — the only difference is the axis labels now show real/synthetic clock times

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home cockpit loads without errors | smoke | P1 | `/` |
| UT-02 | Simulated chart axis shows synthetic session-clock times | happy-path | P1 | `/` |
| UT-03 | Historical chart axis shows real market clock times | happy-path | P1 | `/` |
| UT-04 | Crosshair tooltip shows true clock time on hover | happy-path | P1 | `/` |
| UT-05 | Tape-state marker labels show true clock time | happy-path | P1 | `/` |
| UT-06 | Bar-size switcher preserves real-clock time axis | happy-path | P1 | `/` |
| UT-07 | Historical date input accepts valid dd-MM-yyyy entry | happy-path | P1 | `/` |
| UT-08 | Historical date input rejects impossible date | validation | P2 | `/` |
| UT-09 | Historical date input rejects malformed entry | validation | P2 | `/` |
| UT-10 | Market-status next-open time shows dd-MM-yyyy HH:mm UTC format | happy-path | P1 | `/` |
| UT-11 | Watched-source descriptor shows dd-MM-yyyy dates | happy-path | P1 | `/` |
| UT-12 | Empty historical window shows empty chart without fabricated timestamps | error | P2 | `/` |
| UT-13 | Simulated chart classification still works | regression | P1 | `/` |
| UT-14 | Historical watch resolves correct date window, no UTC shift | regression | P1 | `/` |
| UT-15 | Native date picker is NOT present | ux | P2 | `/` |
| UT-16 | Simulated and historical chart date format is consistent | ux | P2 | `/` |

**P1 tests (UT-01 through UT-07, UT-10, UT-11, UT-13, UT-14) must all pass for browser QA verdict to be PASS.**
