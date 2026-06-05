# Phase goal-i_will_be_super_rich-iter-6 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-6
**Date:** 2026-06-05
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Home page loads with chart panel when SIM-BUYER is watched (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running (verify with `curl http://localhost:8000/health` returning 200)
- No ticker is currently being watched (fresh page load)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load (title bar visible, no spinner)
3. Confirm the mode selector in the TopBar shows "Simulated" or equivalent Sim option
4. Type `SIM-BUYER` into the ticker input field and click the "Watch" button (or press Enter)
5. Wait 5 seconds for the initial poll to complete

**Expected Result:**
- Page renders without a blank screen, white page, or error overlay
- A panel titled "Price Chart — Tape-State Markers" is visible above the cockpit grid
- The panel contains a dark-background candlestick canvas (slate-950 background, not white or bright)
- A bar-size selector row labeled "Bar size" with three buttons ("10s", "30s", "60s") is visible inside or above the chart canvas
- The cockpit panels (quote, recent trades, tape-state, observations, event log) remain visible below the chart
- No JavaScript error banners or "Something went wrong" messages are displayed

---

### UT-02 — SIM-BUYER watch shows loading overlay then populates candlesticks (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated" (default)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the mode selector shows "Simulated"
3. Type `SIM-BUYER` into the ticker input field
4. Click the "Watch" button
5. Immediately observe the chart panel area — within the first 1–2 seconds, look for a "Loading price history…" text overlay
6. Wait 10–15 seconds for candles to accrue
7. Observe the chart canvas

**Expected Result:**
- Immediately after clicking "Watch", the chart panel shows the text "Loading price history…" (not candles)
- After 10–15 seconds, at least 3 candlestick bars are visible on the chart canvas
- Candles are rendered in white/green/red colors on the dark slate-950 background
- The chart updates incrementally: new bars appear on the right edge as time progresses
- No error message is displayed in place of the chart

---

### UT-03 — Emerald (green) buyer_control marker appears on chart for SIM-BUYER (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated"

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait 15–20 seconds for the replay to run and for the cockpit tape-state panel to show `buyer_control`
4. Observe the chart canvas

**Expected Result:**
- At least one emerald (bright green) arrow marker appears on the chart canvas at the point corresponding to the `buyer_control` transition
- The marker is visible as a colored arrow or symbol, not an invisible dot
- The cockpit tape-state panel simultaneously shows `buyer_control` (the chart and cockpit agree)
- No marker appears while the tape state shows `unclear`

---

### UT-04 — Rose (red) seller_control marker appears on chart for SIM-SELLER (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated"

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-SELLER` into the ticker input and click "Watch"
3. Wait 15–20 seconds for the replay to run and for the cockpit tape-state panel to show `seller_control`
4. Observe the chart canvas

**Expected Result:**
- At least one rose (red/pink, approximately #fb7185) arrow marker appears on the chart canvas at the point corresponding to the `seller_control` transition
- The marker color is clearly red or rose-pink, not green or amber
- The cockpit tape-state panel simultaneously shows `seller_control`
- Candlestick bodies trend downward consistent with a seller simulation

---

### UT-05 — Amber markers appear on chart for SIM-BIDABS and SIM-ASKABS (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated"

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BIDABS` into the ticker input and click "Watch"
3. Wait 15–20 seconds for the cockpit tape-state panel to show `bid_absorption`
4. Observe the chart canvas for an amber marker
5. Click "Stop" (or equivalent) to stop the current watch
6. Type `SIM-ASKABS` into the ticker input and click "Watch"
7. Wait 15–20 seconds for the cockpit tape-state panel to show `ask_absorption`
8. Observe the chart canvas for an amber marker

**Expected Result:**
- For SIM-BIDABS: an amber (orange-yellow, approximately #fbbf24) arrow marker appears on the chart at the `bid_absorption` transition point
- For SIM-ASKABS: an amber arrow marker appears on the chart at the `ask_absorption` transition point
- Both markers are the same amber color (not rose, not emerald)
- No marker appears for `unclear` state in either watch

---

### UT-06 — Bar-size selector switches granularity from 10s to 30s to 60s (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated"
- `SIM-BUYER` is being watched and at least 5 candles are visible on the chart

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait 20 seconds for multiple candles to accumulate
4. Note the approximate number of candles visible with "10s" selected (the default)
5. Click the "30s" button in the bar-size selector
6. Wait 1 second and observe the chart
7. Click the "60s" button in the bar-size selector
8. Wait 1 second and observe the chart
9. Click the "10s" button to return to the original view

**Expected Result:**
- After clicking "30s": the chart redraws and the number of visible candle bars is fewer than with "10s" (candles are coarser, each bar spans 30 seconds of data)
- After clicking "60s": the chart redraws and the number of visible candle bars is fewer than with "30s"
- After clicking "10s": the chart redraws and shows the original fine-grained candles
- Each time a new bar-size button is clicked, that button becomes visually distinct — it gains a filled/dark appearance (bg-slate-700 or similar) and the previously selected button loses that styling
- The chart does not display an error or blank out when switching bar sizes

---

### UT-07 — Chart is hidden when mode switches to Live (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated"
- `SIM-BUYER` is being watched and the chart panel is visible

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait 10 seconds and confirm the "Price Chart — Tape-State Markers" panel is visible
4. Click the "Live" button or data-source selector in the TopBar to switch to Live mode
5. Observe the page layout

**Expected Result:**
- Immediately after switching to Live mode, the "Price Chart — Tape-State Markers" panel disappears completely from the page
- Only the TopBar and the cockpit area remain visible (no empty space or ghost panel where the chart was)
- The cockpit panels (quote, tape-state, etc.) remain visible and functioning
- No JavaScript error appears

---

### UT-08 — Chart reappears when switching back from Live to Simulated (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- The chart was previously hidden by switching to Live mode (continuation from UT-07, or independent setup)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait 5 seconds for the chart to appear
4. Click the "Live" button in the TopBar to switch to Live mode
5. Confirm the chart panel has disappeared
6. Click the "Simulated" button (or "Sim") in the TopBar to switch back to Simulated mode
7. Wait 5 seconds

**Expected Result:**
- After switching back to Simulated mode, the "Price Chart — Tape-State Markers" panel reappears above the cockpit
- The chart begins loading data (shows "Loading price history…" or begins displaying candles)
- The bar-size selector ("10s", "30s", "60s") is again visible
- The cockpit panels remain in their original position below the chart

---

### UT-09 — Chart shows "Loading price history…" immediately after watch starts (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated"
- No ticker currently being watched

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input
3. Click the "Watch" button
4. Immediately look at the chart panel area (within the first 2 seconds)

**Expected Result:**
- The chart panel is immediately visible above the cockpit
- Inside the chart area, the text "Loading price history…" is displayed as an overlay or placeholder
- No candlestick bars are drawn yet (the loading state is shown, not an empty canvas with no message)
- After approximately 2–5 seconds, the loading overlay disappears and candles begin appearing

---

### UT-10 — Chart shows "No price history for this window yet" when no data exists (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- A ticker is being watched but the backend has no trade data (e.g., immediately after a backend restart before any trades arrive, or a Historical window with no trades)

**Steps:**
1. Navigate to `http://localhost:3650`
2. If using Historical mode: click the "Historical" button in the TopBar; enter a ticker symbol and a date/time range that falls on a weekend or outside regular trading hours (e.g., a Saturday date)
3. Click "Watch"
4. Wait 5 seconds for the chart to finish loading

**Expected Result:**
- The chart panel is visible above the cockpit
- The chart displays the text "No price history for this window yet" (or similar empty-state message)
- No candlestick bars are drawn — the canvas is empty except for the message
- No placeholder or fabricated candles appear
- The chart does NOT show an error, crash, or blank white box

---

### UT-11 — Chart panel is positioned above cockpit, not displacing any cockpit panel (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated"

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait 5 seconds for the chart to appear
4. Visually inspect the page layout from top to bottom

**Expected Result:**
- The layout order from top to bottom is: TopBar → "Price Chart — Tape-State Markers" panel → cockpit grid panels
- The cockpit panels (quote, recent trades, tape-state, observations, event log) are all present and none are hidden behind the chart
- No cockpit panel is pushed off-screen or partially obscured by the chart
- The chart and cockpit together fit within the viewport without requiring vertical scrolling (on a standard 1920×1080 or 1440×900 desktop viewport)

---

### UT-12 — Pan and zoom interaction works on the chart canvas (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated"
- `SIM-BUYER` is being watched and multiple candles are visible (wait at least 15 seconds)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait 20 seconds for multiple candles to appear
4. Click and drag the chart canvas to the left (pan right on the time axis)
5. Observe the time axis
6. Scroll the mouse wheel upward while hovering over the chart canvas (zoom in)
7. Observe the time axis again

**Expected Result:**
- After dragging left: the time axis shifts — earlier candles scroll into view on the left
- After scrolling the mouse wheel: the visible time window narrows or widens (zoom changes)
- The chart remains functional after interaction (no freezing or error)
- The candles remain correctly proportioned after pan/zoom

---

### UT-13 — Existing cockpit panels still receive live updates during Sim watch (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated"

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait 10 seconds
4. Observe the "Quote" panel in the cockpit grid — check the bid price, ask price, or last trade price
5. Wait another 5 seconds
6. Observe the same "Quote" panel again
7. Observe the "Recent Trades" panel — check whether new trade rows appear over time
8. Observe the "Tape State" panel — check whether the state label updates

**Expected Result:**
- The "Quote" panel bid/ask/last values change over time (they are not frozen at their initial value)
- The "Recent Trades" panel adds new rows as trades occur
- The "Tape State" panel displays a state value (e.g., `buyer_control`, `unclear`) that updates during the watch
- None of these panels are blank, frozen, or showing stale data from before iter-6

---

### UT-14 — Chart styling matches the cockpit dark instrument-panel theme (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated"
- `SIM-BUYER` is being watched and candles are visible

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait 10 seconds for candles to appear
4. Visually compare the chart panel to the cockpit panels below it

**Expected Result:**
- The chart canvas background is dark (slate-950 or very dark navy/charcoal — not white or light gray)
- The grid lines on the chart are subtle and dark (slate-800 or similar muted lines)
- Price axis labels on the chart use monospaced numerics (digits are all same width, consistent with a terminal/instrument look)
- The chart panel frame matches the cockpit panels in border color and padding (slate-800 border, consistent with the existing Panel.tsx wrapper)
- The chart does NOT appear as a bright, colorful third-party widget that stands out from the cockpit

---

### UT-15 — Bar-size selector selected state is visually distinct (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running
- Mode is "Simulated"
- `SIM-BUYER` is being watched and candles are visible

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait 5 seconds
4. Observe the bar-size selector — the default selected button should be visually distinct
5. Click "30s"
6. Observe which button is now visually distinct
7. Click "60s"
8. Observe which button is now visually distinct

**Expected Result:**
- At all times, exactly one bar-size button has a visually distinct "active" style (darker fill, lighter text — e.g., bg-slate-700 with white/light text)
- The other two buttons appear as unselected (no fill or lighter styling)
- After clicking "30s", that button becomes the active/filled one and "10s" loses its active style
- After clicking "60s", that button becomes active and "30s" loses its active style
- The transition between states is immediate with no delay or flicker

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home page loads with chart panel when SIM-BUYER is watched | smoke | P1 | `/` |
| UT-02 | SIM-BUYER watch shows loading overlay then populates candlesticks | happy-path | P1 | `/` |
| UT-03 | Emerald marker appears for buyer_control on SIM-BUYER chart | happy-path | P1 | `/` |
| UT-04 | Rose marker appears for seller_control on SIM-SELLER chart | happy-path | P1 | `/` |
| UT-05 | Amber markers appear for SIM-BIDABS and SIM-ASKABS | happy-path | P1 | `/` |
| UT-06 | Bar-size selector switches granularity 10s / 30s / 60s | happy-path | P1 | `/` |
| UT-07 | Chart is hidden when mode switches to Live | validation | P1 | `/` |
| UT-08 | Chart reappears when switching back from Live to Simulated | regression | P1 | `/` |
| UT-09 | Chart shows loading overlay immediately after watch starts | validation | P2 | `/` |
| UT-10 | Chart shows empty-state message when no price data exists | validation | P2 | `/` |
| UT-11 | Chart is above cockpit, no cockpit panel displaced or obscured | regression | P1 | `/` |
| UT-12 | Pan and zoom interaction works on the chart canvas | happy-path | P2 | `/` |
| UT-13 | Cockpit panels still receive live updates during Sim watch | regression | P1 | `/` |
| UT-14 | Chart styling matches the cockpit dark instrument-panel theme | ux | P2 | `/` |
| UT-15 | Bar-size selector selected state is visually distinct | ux | P2 | `/` |

**P1 tests must all pass for the browser QA verdict to be PASS.**
**P2 tests are important but non-blocking for the pass verdict.**
