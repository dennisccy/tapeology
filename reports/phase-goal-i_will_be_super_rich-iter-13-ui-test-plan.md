# Phase goal-i_will_be_super_rich-iter-13 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-13
**Date:** 2026-06-09
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Home page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running (no prerequisite login required)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load (up to 5 seconds)
3. Observe the page layout — TopBar, cockpit panels, chart area

**Expected Result:**
- Page renders without a blank screen, uncaught error overlay, or "Application error" banner
- The TopBar is visible at the top of the page
- The Historical mode controls (including the replay-speed dropdown showing "1x", "2x", "5x", or "10x") are visible
- The tape-state panel (row 1 of the cockpit) is visible
- No red error banner appears at the top of the page on initial load

---

### UT-02 — Historical replay-speed dropdown is visible and shows correct options (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` — TopBar replay-speed select

**Preconditions:**
- Frontend is running at http://localhost:3650
- No watch is currently running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Locate the Historical mode controls in the TopBar
3. Find the replay-speed dropdown/select control
4. Click or open the dropdown to view all available speed options

**Expected Result:**
- The dropdown is visible in the TopBar within the Historical mode controls section
- The dropdown contains exactly four options: "1x", "2x", "5x", "10x" (or equivalent labels)
- The default selected value is "1x"
- The control is enabled (not greyed out) and clickable

---

### UT-03 — Mid-replay speed change from 1x to 10x accelerates cadence without restarting watch (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — TopBar replay-speed select during active historical replay

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A historical replay watch is active and streaming events (chart is updating, trades are scrolling)

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the Historical mode section of the TopBar, ensure the symbol is set to `SIM-BUYER` (or select it)
3. Select a historical time window using a quick-pick (e.g., click the "1H" quick-pick button)
4. Click the "Watch" button to start the historical replay
5. Wait until the chart begins rendering candles and the tape panel shows activity (approximately 2–3 seconds)
6. While the replay is actively running, locate the replay-speed dropdown in the TopBar and select "10x" from it
7. Observe the chart and cockpit for the next 2–3 seconds

**Expected Result:**
- The speed dropdown updates to show "10x" as the selected value
- The cadence of incoming candles and trade prints visibly accelerates — events arrive noticeably faster than before
- The chart does NOT blank out, reload, or show a loading spinner
- The cockpit panels (tape-state row 1, chart) retain their current state and position — no position reset
- No error banner appears at the top of the page
- The watch continues running; the symbol and window are unchanged

---

### UT-04 — Replay-speed dropdown when no watch is running stages speed for next Watch (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — TopBar replay-speed select with no active watch

**Preconditions:**
- Frontend is running at http://localhost:3650
- No historical replay is currently running (either no watch was started, or a previous watch was stopped)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Ensure no watch is active (the chart area should be empty or show the idle state)
3. Locate the replay-speed dropdown in the TopBar
4. Select "5x" from the dropdown
5. In the symbol input field, type `SIM-BUYER`
6. Select a historical time window quick-pick (e.g., "1H")
7. Click the "Watch" button to start a new Historical replay
8. Observe the cadence of events from the very first second of the replay

**Expected Result:**
- The dropdown shows "5x" as selected before the Watch starts
- The replay starts and events arrive at approximately 5x speed from the outset — noticeably faster than 1x but slower than 10x
- No error banner appears
- The watch is not torn down or restarted after starting — it continues to run

---

### UT-05 — Full RTH 9:30–16:00 quick-pick loads tape data instead of showing "very high-volume" error (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — Historical quick-pick row "Full RTH 9:30–16:00" button

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running with Alpaca credentials configured (APCA_API_KEY_ID and APCA_API_SECRET_KEY present in environment)
- A liquid symbol is available (use `SPY`)

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the symbol input field in the TopBar, type `SPY`
3. In the Historical mode controls, locate the quick-pick row and click the "Full RTH 9:30–16:00" button (or equivalent label for the full-session quick-pick)
4. Click the "Watch" button to start the historical replay
5. Wait up to 30 seconds for the data to load (chunked fetch of the full session)
6. Observe the chart area and any error banners at the top of the page

**Expected Result:**
- The chart area begins populating with candle data and tape prints from the SPY session
- The tape-state panel (row 1) shows a state label (e.g., `buyer_control`, `seller_control`, `unclear`, or `absorption`) — any valid state is acceptable; the panel is not blank
- No red error banner reading "very high-volume" or "try a shorter range" appears
- The watch appears to be running normally (events are streaming)

**Note:** If Alpaca credentials are not configured, this test is marked "credential-gated" and should be skipped. Use the error-banner test (UT-09) instead.

---

### UT-06 — A clear directional move on a real sub-$100 stock resolves to buyer_control or seller_control (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — Tape-state panel (row 1) — state label + confidence bar

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running with Alpaca credentials configured
- A historical session with a clear directional move is available for a real sub-$100 stock (e.g., `GME` on a session with strong one-sided price progress)

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the symbol input field, type `GME`
3. Select a historical date and time window that covers a session with a strong directional move (e.g., use a 1-hour quick-pick on a date with notable price movement)
4. Click the "Watch" button
5. Wait up to 20 seconds for the tape to warm and the directional move to be processed
6. Observe the tape-state panel in row 1 of the cockpit — look at the state label and the confidence bar

**Expected Result:**
- The tape-state panel shows either `buyer control` (green label) or `seller control` (red label) — NOT `unclear` (amber) and NOT `absorption`
- The confidence bar is filled to a visible level (above the minimum threshold)
- The state label color matches the state: green for buyer control, red for seller control

**Note:** This test is credential-gated. If Alpaca credentials are not configured, skip this test. The deterministic proof lives in the backend classifier fixture tests (TC-05 in the functional test plan).

---

### UT-07 — A tape with high aggression but no proportionate price progress stays on unclear or absorption (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` — Tape-state panel (row 1) — state label

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A simulator symbol with balanced aggression and no strong price move is available (use `SIM-SELLER` during a period where the spread is wide relative to price but price progress is minimal, or use a balanced scenario)

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the symbol input field, type `SIM-SELLER`
3. Click the "Watch" button to start a live simulator watch
4. Wait approximately 5–10 seconds for the tape to warm up and the classifier to produce a reading
5. Observe the tape-state panel in row 1 of the cockpit

**Expected Result:**
- If the SIM-SELLER scenario has strong one-sided aggression with clear price progress: the panel shows `seller control` (red) — this is correct classifier behavior
- If using a scenario with high aggression but negligible price change: the panel shows `unclear` (amber) or `absorption` (amber)
- In neither case should the classifier oscillate rapidly or show an error

**Note:** This test verifies the negative guard: the classifier must not over-classify weak signals as control. The exact result depends on the simulator scenario. The key assertion is: no `seller_control` label should appear when price progress is negligible relative to aggression level.

---

### UT-08 — SIM-BUYER resolves to buyer_control and SIM-SELLER resolves to seller_control after J-33 re-tuning (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — Tape-state panel (row 1)

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- No watch is currently active

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the symbol input field, type `SIM-BUYER`
3. Click the "Watch" button (Live / Simulator mode)
4. Wait approximately 4–6 seconds for the tape to warm and resolve
5. Observe the tape-state panel in row 1 — note the state label and confidence bar level
6. Stop or reset the current watch (click the "Stop" button if available, or navigate away and back)
7. In the symbol input field, type `SIM-SELLER`
8. Click the "Watch" button
9. Wait approximately 4–6 seconds for the tape to warm and resolve
10. Observe the tape-state panel in row 1

**Expected Result:**
- SIM-BUYER: the tape-state panel shows `buyer control` with a green label; confidence bar is at or above 80% filled
- SIM-SELLER: the tape-state panel shows `seller control` with a red label; confidence bar is at or above 80% filled
- Neither symbol shows `unclear` or `absorption` as its resolved state after the warm-up period
- The J-33 classifier re-tuning has not regressed the simulator baselines

---

### UT-09 — Multi-hour historical window no longer triggers "shorter range" error for normal sessions (error)

**Type:** error
**Priority:** P1
**Surface:** `/` — Historical window loading — error banner

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running with Alpaca credentials configured
- A liquid symbol is available (use `SPY`)

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the symbol input field, type `SPY`
3. In the Historical mode controls, select a 2-hour window (use a quick-pick labeled "2H" if available, or manually enter a start time and end time 2 hours apart on a recent trading day)
4. Click the "Watch" button
5. Wait up to 30 seconds for the data to load
6. Observe the top of the page for any error banners

**Expected Result:**
- No red error banner reading "very high-volume — try a shorter range" or similar appears
- The chart begins populating with tape data within 30 seconds
- The tape-state panel (row 1) shows a valid state after the data loads

**Note:** This test is credential-gated. If Alpaca credentials are not available, skip.

---

### UT-10 — Error banner appears when a genuinely oversized window is requested (error)

**Type:** error
**Priority:** P2
**Surface:** `/` — Error banner (top of page)

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running with Alpaca credentials configured
- A liquid symbol is available (use `SPY`)

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the symbol input field, type `SPY`
3. In the Historical mode date/time range inputs, manually enter a start date that is 10 full trading days before today, and an end date of today (a window spanning approximately 65 trading hours)
4. Click the "Watch" button
5. Wait up to 60 seconds for the backend to process the request

**Expected Result:**
- A red or amber error banner appears at the top of the page
- The error banner text includes a message such as "shorter range", "too large", or "window exceeds budget" — an actionable message indicating the user should reduce their window
- The message does NOT say "very high-volume" as the sole text (the new error is more specific and actionable)
- The chart area remains empty or shows the previous state — no fabricated data is displayed

**Note:** This test is credential-gated and may take up to 60 seconds for the timeout to fire.

---

### UT-11 — Historical window picker quick-picks still work as before J-34 changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — Historical quick-pick row

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- No watch is currently active

**Steps:**
1. Navigate to `http://localhost:3650`
2. Locate the Historical mode controls section in the TopBar
3. Observe the quick-pick buttons row (e.g., "5M", "15M", "1H", "2H", and "Full RTH 9:30–16:00")
4. In the symbol input field, type `SIM-BUYER`
5. Click the "1H" quick-pick button
6. Observe that the time range fields update to reflect a 1-hour window
7. Click the "Watch" button
8. Wait approximately 3–5 seconds
9. Verify the chart and cockpit are populated

**Expected Result:**
- Clicking the "1H" quick-pick button updates the time range inputs to show a 1-hour window (start and end times visible in the input fields)
- Clicking "Watch" starts a historical replay and the chart begins rendering candle data
- No error banner appears
- The quick-pick row layout is unchanged — all buttons are visible and labeled as before

---

### UT-12 — Home page chart area renders for SIM-BUYER simulator watch (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — Chart area (simulator watch)

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- No active watch is currently running

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the symbol input field in the TopBar, type `SIM-BUYER`
3. Click the "Watch" button (ensure Simulator / Live mode is selected, not Historical)
4. Wait approximately 5 seconds for events to stream

**Expected Result:**
- The chart area (upper portion of the cockpit) begins rendering candle data
- Buy-side markers are visible — at minimum one green marker or green-colored data point appears in the chart
- The chart does NOT show a blank canvas or "no data" message after 5 seconds
- The cockpit panels (rows 1–10) show live updating values (tape state, confidence bar, etc.)

---

### UT-13 — Replay-speed control shows correct selected value while replay is running (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — TopBar replay-speed select

**Preconditions:**
- Frontend is running at http://localhost:3650
- A historical replay is active

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the symbol input field, type `SIM-BUYER`
3. In Historical mode, select the "1H" quick-pick
4. Click the "Watch" button to start the replay
5. Wait until the replay is actively running (chart is updating)
6. Observe the replay-speed dropdown — note the currently selected value (should be "1x")
7. Select "2x" from the dropdown
8. Immediately observe the dropdown's selected value

**Expected Result:**
- Before the speed change: the dropdown shows "1x" as the selected value
- After selecting "2x": the dropdown immediately updates to show "2x" as the selected value — there is no delay or revert to "1x"
- The speed label in the dropdown remains "2x" while the replay continues running at the new speed
- No loading spinner or page reload occurs

---

### UT-14 — Speed dropdown is present and labeled correctly in Historical mode (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — TopBar Historical mode controls

**Preconditions:**
- Frontend is running at http://localhost:3650
- No watch is currently running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Look at the TopBar and locate the Historical mode section
3. Observe the replay-speed control — note its label, position, and available options
4. Without starting a watch, open the dropdown and read the option labels

**Expected Result:**
- The replay-speed control is clearly visible within the Historical mode controls (not hidden, not collapsed)
- The control is labeled with a word or icon that communicates "speed" or "replay speed" (e.g., a speed label, an "x" multiplier notation, or a speedometer icon)
- The options are labeled "1x", "2x", "5x", "10x" (or equivalent — the key is that they are numeric multipliers, not abstract labels)
- The control position is consistent with the existing TopBar layout — it has not moved from the Historical mode section

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home page loads without errors | smoke | P1 | `/` |
| UT-02 | Replay-speed dropdown visible and shows correct options | smoke | P1 | `/` TopBar |
| UT-03 | Mid-replay speed change accelerates cadence without restarting watch | happy-path | P1 | `/` TopBar |
| UT-04 | Pre-watch speed selection stages speed for next Watch | regression | P1 | `/` TopBar |
| UT-05 | Full RTH quick-pick loads tape data (no "very high-volume" error) | happy-path | P1 | `/` quick-pick row |
| UT-06 | Clear directional move on real sub-$100 stock resolves to control | happy-path | P1 | `/` tape-state panel |
| UT-07 | High aggression with no price progress stays unclear/absorption | validation | P2 | `/` tape-state panel |
| UT-08 | SIM-BUYER/SIM-SELLER simulator baselines unchanged after J-33 re-tuning | regression | P1 | `/` tape-state panel |
| UT-09 | Multi-hour window no longer triggers "shorter range" error | error | P1 | `/` error banner |
| UT-10 | Genuinely oversized window still shows actionable error banner | error | P2 | `/` error banner |
| UT-11 | Historical window picker quick-picks unchanged after J-34 | regression | P1 | `/` quick-pick row |
| UT-12 | SIM-BUYER simulator chart renders correctly | regression | P1 | `/` chart area |
| UT-13 | Speed dropdown reflects correct selected value while replay runs | ux | P2 | `/` TopBar |
| UT-14 | Speed dropdown present, labeled correctly, discoverable in Historical mode | ux | P2 | `/` TopBar |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Credential-gated tests:** UT-05, UT-06, UT-09, UT-10 require Alpaca API credentials (APCA_API_KEY_ID, APCA_API_SECRET_KEY). If credentials are not available, mark these tests as SKIP — they are covered by backend unit/API tests TC-09, TC-16 in the functional test plan.
