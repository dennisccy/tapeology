# Phase goal-i_will_be_super_rich-iter-9 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-9
**Date:** 2026-06-06
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Main cockpit page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- No prior session state in the browser

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load (allow up to 5 seconds)

**Expected Result:**
- Page renders without a blank screen or error page
- The Tapeology header/TopBar is visible at the top of the page
- A mode selector with "SIM", "LIVE", and "HIST" tabs is visible
- A symbol input field is visible in the TopBar
- A "Watch" button is visible
- The cockpit area shows the idle state (e.g., "No ticker watched" or equivalent idle placeholder)
- No red error banners appear on initial load

---

### UT-02 — ConnectingState appears immediately on Watch click in Simulated mode (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- App is displaying in Simulated ("SIM") mode — the SIM tab must be active
- The cockpit area is in the idle state (no ticker currently watched)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the "SIM" tab is active in the mode selector; if not, click the "SIM" tab
3. Click the symbol input field in the TopBar and type `SIM-BUYER`
4. Click the "Watch" button
5. Observe the cockpit area within approximately 1 second of clicking Watch

**Expected Result:**
- Within approximately 1 second of clicking Watch (before any tape data arrives from the backend), the cockpit area changes away from the idle "No ticker watched" state
- The cockpit area shows an amber pulsing dot and the text "Connecting to SIM-BUYER…" (exact symbol name called out)
- The idle placeholder ("No ticker watched" or equivalent) is no longer visible
- The TopBar status dot shows the "connecting" state (not "idle")

---

### UT-03 — ConnectingState appears immediately on Watch click in Live mode (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- The cockpit area is in the idle state

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "LIVE" tab in the mode selector
3. Click the symbol input field and type `AAPL`
4. Click the "Watch" button
5. Observe the cockpit area within approximately 1 second of clicking Watch

**Expected Result:**
- Within approximately 1 second, the cockpit area shows an amber pulsing dot and the text "Connecting to AAPL…"
- The idle placeholder is no longer visible
- The TopBar status dot shows the "connecting" state (not "idle")

---

### UT-04 — ConnectingState appears immediately on Watch click in Historical mode (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- The cockpit area is in the idle state

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "HIST" tab in the mode selector
3. Click the symbol input field and type `AAPL`
4. Fill in a valid start date/time (e.g., 2024-01-01) in the historical start date field
5. Fill in a valid end date/time (e.g., 2024-01-02) in the historical end date field
6. Click the "Watch" button
7. Observe the cockpit area within approximately 1 second of clicking Watch

**Expected Result:**
- Within approximately 1 second, the cockpit area shows an amber pulsing dot and the text "Connecting to AAPL…"
- The idle placeholder is no longer visible

---

### UT-05 — StreamFailedState panel appears when tape connection fails (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- App is in Simulated ("SIM") mode with the idle cockpit displayed

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the "SIM" tab is active
3. Click the symbol input field and type `SIM-BUYER`
4. Click the "Watch" button
5. After the "Connecting to SIM-BUYER…" state appears, stop the backend server immediately
6. Wait up to 15 seconds for the error to surface

**Expected Result:**
- The "Connecting to SIM-BUYER…" state is replaced by an error panel in the cockpit area
- The error panel displays a rose (red/pink) warning icon (⚠) and the heading "Couldn't connect to the tape stream"
- The panel also displays the instruction text "Try Watch again"
- The cockpit does NOT remain indefinitely in the "Connecting to SIM-BUYER…" state
- The TopBar error banner below the header shows a rose-colored error message referencing connection failure

---

### UT-06 — TopBar status dot shows "failed" state after stream connection failure (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Operator has just completed the steps in UT-05 (backend stopped after Watch) and the StreamFailedState panel is visible

**Steps:**
1. With the StreamFailedState panel visible (after completing UT-05), look at the status dot in the TopBar (upper-right area)

**Expected Result:**
- The status dot in the TopBar shows a rose (red/pink) color
- The status dot label reads "failed" (not "connecting", not "closed", not "idle")

---

### UT-07 — TopBar error banner shows timeout message when backend is unreachable (error)

**Type:** error
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- The backend is NOT running (or has been stopped before clicking Watch)
- App is in Simulated ("SIM") mode with the idle cockpit displayed

**Steps:**
1. Navigate to `http://localhost:3650` with the backend stopped
2. Confirm the "SIM" tab is active
3. Click the symbol input field and type `SIM-BUYER`
4. Click the "Watch" button
5. Wait up to 15 seconds for the frontend client-side timeout to fire

**Expected Result:**
- Within approximately 12 seconds of clicking Watch, the error banner below the TopBar header becomes visible with a rose background
- The error banner text contains either "timed out" or "Market data provider timed out" or "Couldn't connect"
- The cockpit area does NOT remain on the idle screen indefinitely — it enters the "Connecting to SIM-BUYER…" state immediately, then transitions to an error state after the timeout
- No infinite spinner is shown; the UI is fully responsive after the error appears

---

### UT-08 — Watch button is disabled and shows inline message when symbol field is empty (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- App is in Simulated ("SIM") mode
- The symbol input field is empty (cleared)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the "SIM" tab is active
3. If there is any text in the symbol input field, clear it completely (select all and delete)
4. Observe the Watch button and the area beside it without clicking anything

**Expected Result:**
- The "Watch" button appears grayed out (disabled)
- The inline validation message "Enter a ticker symbol" appears in amber text immediately beside the Watch button (without requiring any click)
- The Watch button cannot be activated in this state

---

### UT-09 — Inline validation message "Enter a ticker symbol" appears with whitespace-only input (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- App is in Simulated ("SIM") mode

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the "SIM" tab is active
3. Click the symbol input field and type three space characters (press the spacebar three times)
4. Observe the Watch button and the area beside it

**Expected Result:**
- The "Watch" button appears grayed out (disabled)
- The inline validation message "Enter a ticker symbol" appears in amber text beside the Watch button
- No Watch request is sent to the backend

---

### UT-10 — Watch button is disabled and shows inline message when Historical time window is missing (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- App is in Historical ("HIST") mode
- A valid symbol has been entered

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "HIST" tab in the mode selector
3. Click the symbol input field and type `AAPL`
4. Leave the historical start date/time fields and end date/time fields blank (do not fill them in)
5. Observe the Watch button and the area beside it without clicking anything

**Expected Result:**
- The "Watch" button appears grayed out (disabled)
- The inline validation message "Choose a valid time window" appears in amber text beside the Watch button
- The Watch button cannot be activated in this state

---

### UT-11 — Inline validation message clears immediately when user types a valid symbol (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- App is in Simulated ("SIM") mode
- The symbol input field is empty, causing the "Enter a ticker symbol" validation message to be visible

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the "SIM" tab is active
3. Ensure the symbol input field is empty and the amber "Enter a ticker symbol" message is visible beside the Watch button
4. Click the symbol input field and type the single character `A`
5. Observe the area beside the Watch button immediately

**Expected Result:**
- As soon as the character `A` is typed, the amber inline validation message "Enter a ticker symbol" disappears
- The Watch button is no longer grayed out (it becomes active/enabled)
- No page reload or form submission is needed for the message to clear

---

### UT-12 — Mode switch while connecting clears the ConnectingState (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- App is in Simulated ("SIM") mode with the idle cockpit displayed

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the "SIM" tab is active
3. Click the symbol input field and type `SIM-BUYER`
4. Click the "Watch" button
5. Immediately (within 1–2 seconds, while the "Connecting to SIM-BUYER…" state is visible) click the "LIVE" tab in the mode selector
6. Observe the cockpit area

**Expected Result:**
- After clicking the "LIVE" tab, the cockpit area returns to the idle state (e.g., "No ticker watched" or equivalent idle placeholder)
- The "Connecting to SIM-BUYER…" text and amber pulsing dot are NO LONGER visible
- No stale "Connecting to…" text remains on screen

---

### UT-13 — Simulated cockpit populates successfully end-to-end (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- App is in Simulated ("SIM") mode with the idle cockpit displayed

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the "SIM" tab is active
3. Click the symbol input field and type `SIM-BUYER`
4. Click the "Watch" button
5. Wait up to 10 seconds for the cockpit to populate with tape data

**Expected Result:**
- The cockpit area transitions from "Connecting to SIM-BUYER…" to a fully populated cockpit
- At least one tape row/event is visible in the cockpit
- A confidence score is displayed
- The text "Connecting to SIM-BUYER…" is no longer visible once data has loaded
- The TopBar status dot changes from "connecting" to "live" (or equivalent active state)

---

### UT-14 — Stop button returns cockpit to idle state (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A cockpit is currently active and displaying tape data (complete UT-13 first)

**Steps:**
1. With the active cockpit displaying tape data, locate the "Stop" button (in the TopBar)
2. Click the "Stop" button
3. Observe the cockpit area

**Expected Result:**
- The cockpit area clears and returns to the idle state
- Tape rows are no longer visible
- The idle placeholder ("No ticker watched" or equivalent) reappears
- The mode selector and symbol input fields are accessible again
- The TopBar status dot shows "idle" or equivalent inactive state

---

### UT-15 — Mode switching updates TopBar controls correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- No active watch session (cockpit is idle)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the app is in "SIM" mode (SIM tab active)
3. Click the "LIVE" tab in the mode selector
4. Observe the TopBar controls
5. Click the "HIST" tab in the mode selector
6. Observe the TopBar controls

**Expected Result:**
- After clicking "LIVE": the mode selector shows LIVE as active; the TopBar shows a symbol input field but no date/time window fields; the cockpit resets to idle
- After clicking "HIST": the mode selector shows HIST as active; the TopBar shows a symbol input field AND date/time window fields (start and end); the cockpit resets to idle
- No errors appear during mode switches; the watch button is visible after each switch

---

### UT-16 — ConnectingState is discoverable and labels are clear (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- App is in Simulated ("SIM") mode with the idle cockpit displayed

**Steps:**
1. Navigate to `http://localhost:3650`
2. As a first-time user, scan the TopBar for input affordances
3. Confirm the symbol input and Watch button are immediately visible without scrolling
4. Click the symbol input and type `SIM-BUYER`
5. Click the "Watch" button
6. Observe the cockpit area for the connecting state

**Expected Result:**
- The symbol input and Watch button are visible in the TopBar without scrolling
- The "Connecting to SIM-BUYER…" text in the cockpit clearly communicates which symbol is being connected (the name "SIM-BUYER" appears in the message)
- The amber pulsing dot is visually distinct from the idle cockpit state
- A user who has never used the app before can understand "the system is connecting to SIM-BUYER" from the cockpit display alone

---

### UT-17 — StreamFailedState panel is clear and actionable (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- The StreamFailedState panel is visible (complete UT-05 first)

**Steps:**
1. With the StreamFailedState panel visible in the cockpit area, read the text displayed in the panel
2. Identify whether the panel tells the user what went wrong and what to do next

**Expected Result:**
- The panel heading "Couldn't connect to the tape stream" clearly communicates the failure
- The panel includes the instruction "Try Watch again" (or equivalent actionable next step)
- The rose warning icon (⚠) is visually prominent and distinguishable from the amber pulsing dot used during connecting state
- A user reading the panel can understand the connection failed and knows to try clicking Watch again

---

### UT-18 — Inline validation messages are visible and positioned near the Watch button (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- App is in Simulated ("SIM") mode
- Symbol input field is empty

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the "SIM" tab is active
3. Ensure the symbol input field is empty
4. Look at the area near the Watch button for any validation messaging

**Expected Result:**
- The amber inline validation message "Enter a ticker symbol" is positioned in close proximity to the Watch button (not in a distant part of the page)
- The amber color is visually distinct from normal label text
- A user can immediately associate the message with the Watch button action

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Main cockpit page loads without errors | smoke | P1 | `/` |
| UT-02 | ConnectingState appears immediately on Watch click in Simulated mode | happy-path | P1 | `/` |
| UT-03 | ConnectingState appears immediately on Watch click in Live mode | happy-path | P1 | `/` |
| UT-04 | ConnectingState appears immediately on Watch click in Historical mode | happy-path | P1 | `/` |
| UT-05 | StreamFailedState panel appears when tape connection fails | happy-path | P1 | `/` |
| UT-06 | TopBar status dot shows "failed" state after stream connection failure | happy-path | P1 | `/` |
| UT-07 | TopBar error banner shows timeout message when backend is unreachable | error | P1 | `/` |
| UT-08 | Watch button is disabled and shows inline message when symbol field is empty | validation | P1 | `/` |
| UT-09 | Inline validation message appears with whitespace-only input | validation | P1 | `/` |
| UT-10 | Watch button is disabled when Historical time window is missing | validation | P1 | `/` |
| UT-11 | Inline validation message clears immediately when user types a valid symbol | validation | P1 | `/` |
| UT-12 | Mode switch while connecting clears the ConnectingState | regression | P1 | `/` |
| UT-13 | Simulated cockpit populates successfully end-to-end | regression | P1 | `/` |
| UT-14 | Stop button returns cockpit to idle state | regression | P1 | `/` |
| UT-15 | Mode switching updates TopBar controls correctly | regression | P1 | `/` |
| UT-16 | ConnectingState is discoverable and labels are clear | ux | P2 | `/` |
| UT-17 | StreamFailedState panel is clear and actionable | ux | P2 | `/` |
| UT-18 | Inline validation messages are visible and positioned near the Watch button | ux | P2 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.**
