# Phase goal-i_will_be_super_rich-iter-10 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-10
**Date:** 2026-06-07
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
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load (up to 3 seconds)

**Expected Result:**
- Page renders without a blank screen or error message
- The idle/home screen is visible with a symbol input field and a Watch button
- No full-screen error overlay is present

---

### UT-02 — WaitingState renders when stream connects but no trade has arrived (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running with the simulator (Simulated mode)
- A symbol that will trigger a `waiting` stream status is available (e.g., use the backend's no-event provider — in Simulated mode this can be triggered by entering a symbol the backend does not have a playback script for, such as `WAIT-TEST`)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the data-source selector is set to "Simulated" (if a selector is visible, click it and select "Simulated")
3. Type `WAIT-TEST` into the ticker/symbol input field
4. Click the "Watch" button
5. Wait up to 3 seconds for the connection to progress past the connecting state
6. Observe the cockpit area in the centre of the page

**Expected Result:**
- The idle screen is replaced within ~1 second of clicking Watch
- The cockpit does NOT show a blank panel grid (no empty "Quote", "Trades", "Features", "State", "Observations", "Event Log" panels)
- A waiting treatment screen appears containing both the text "waiting for the first trade" and the ticker symbol (`WAIT-TEST`)
- A mode label ("Simulated" or "sim") is visible alongside the ticker in that waiting screen
- The full cockpit panel grid (Quote, Recent Trades, Features, TapeState, Observations, EventLog) is NOT rendered

---

### UT-03 — TopBar status dot shows amber "waiting" label during the waiting phase (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — TopBar

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running; a stream is in `stream_status === "waiting"` (follow UT-02 steps 1–5 to reach this state)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `WAIT-TEST` into the ticker/symbol input field
3. Click the "Watch" button
4. Wait up to 3 seconds for the stream to reach the waiting phase
5. Look at the status indicator in the top bar area of the page

**Expected Result:**
- The status dot/badge in the TopBar reads the label "waiting" (not "live", not "connecting", not "stale")
- The dot is amber/yellow coloured (not green, not rose/red)
- The dot has a pulsing/animated appearance (consistent with the "in-progress" style used for "stale" and "paused" states)

---

### UT-04 — Snapshot-borne failed state renders StreamFailedState and error banner (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running with a provider configured to raise an exception mid-stream, or the backend is stopped after the watch connection is established (to simulate a feeder failure)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type any symbol (e.g., `FAIL-TEST`) into the ticker/symbol input field
3. Click the "Watch" button and wait for the connection to establish
4. While the stream is active, stop or kill the backend process to force a feeder failure (or use a test symbol pre-configured to raise)
5. Wait up to 5 seconds for the UI to update

**Expected Result:**
- The cockpit does NOT remain frozen on a "Connecting" or blank live grid
- The page displays the StreamFailedState component (previously introduced in iter-9), showing a rose/pink warning icon
- An error banner appears in the TopBar area displaying the text "The tape feed failed after connecting. No tape is shown."
- The full cockpit panel grid (Quote, Trades, Features, etc.) is NOT rendered

---

### UT-05 — TopBar status dot shows rose "failed" label for snapshot-borne failure (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — TopBar

**Preconditions:**
- Frontend is running at http://localhost:3650
- A watch session has reached `stream_status === "failed"` (follow UT-04 steps 1–5 to reach this state)

**Steps:**
1. Follow steps 1–5 from UT-04 to put the stream into the `failed` state
2. Look at the status indicator in the top bar area of the page

**Expected Result:**
- The status dot/badge in the TopBar reads the label "failed"
- The dot is rose/pink coloured (not green, not amber, not grey)
- The label and colour are distinct from the pre-snapshot connect failure dot (which also reads "failed" but is driven by the client connection status, not the engine snapshot)

---

### UT-06 — Price chart is hidden during the waiting state (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running; a stream can be placed into `stream_status === "waiting"` (follow UT-02 steps 1–4)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `WAIT-TEST` into the ticker/symbol input field
3. Click the "Watch" button
4. Wait up to 3 seconds for the stream to reach the waiting phase
5. Scroll through the entire page to inspect what panels/components are visible

**Expected Result:**
- No price/tape chart is visible on the page while the stream is in the waiting state
- The waiting treatment screen is visible (text "waiting for the first trade")
- After the stream later advances to `live` (if it does), the price chart reappears in the cockpit

---

### UT-07 — Price chart is hidden during the snapshot-borne failed state (error)

**Type:** error
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- A stream has reached `stream_status === "failed"` (follow UT-04 steps 1–5)

**Steps:**
1. Follow steps 1–5 from UT-04 to reach the `failed` state
2. Scroll through the entire page to inspect what panels/components are visible

**Expected Result:**
- No price/tape chart is visible on the page while the stream is in the `failed` state
- The StreamFailedState component and error banner are visible
- No blank or zeroed chart panel is rendered beneath the failure message

---

### UT-08 — Empty Watch (no ticker entered) shows inline validation, no silent no-op (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- No symbol has been entered

**Steps:**
1. Navigate to `http://localhost:3650`
2. Leave the ticker/symbol input field empty (do not type anything)
3. Click the "Watch" button

**Expected Result:**
- The page does NOT silently do nothing (no silent no-op)
- Either a validation message appears (e.g., "Enter a ticker symbol") near the input field, OR the Watch button is disabled/greyed out when the field is empty
- The idle screen remains in place; no connecting or waiting state is entered

---

### UT-09 — Whitespace-only ticker input shows validation, no silent no-op (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type two or three space characters into the ticker/symbol input field
3. Click the "Watch" button (if the button is enabled)

**Expected Result:**
- The page does NOT proceed to a connecting or waiting state
- Either a validation message appears (e.g., "Enter a ticker symbol") near the input field, OR the Watch button remained disabled for whitespace-only input
- The idle screen remains displayed

---

### UT-10 — Idle screen leaves within ~1 second of clicking Watch (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Note the current time (or observe the clock)
3. Type `AAPL` into the ticker/symbol input field
4. Click the "Watch" button
5. Watch the cockpit area — count to 1 second

**Expected Result:**
- Within approximately 1 second of clicking Watch, the idle screen (home/search state) is replaced by either a "Connecting to AAPL…" screen or the waiting treatment or a cockpit with data
- The idle screen must not remain visible for more than ~1 second after clicking Watch
- The page must not silently return to idle after a brief flicker

---

### UT-11 — SIM-BUYER still resolves to full cockpit with buyer_control (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running in Simulated mode
- Data-source selector is set to "Simulated" (or default)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Confirm the data-source selector shows "Simulated" (or select it if needed)
3. Type `SIM-BUYER` into the ticker/symbol input field
4. Click the "Watch" button
5. Wait up to 10 seconds for the cockpit to populate with data

**Expected Result:**
- The idle screen leaves within ~1 second
- The cockpit renders with real data: Quote panel (bid/ask/spread/last), Recent Trades list, Features panel, TapeState panel, Observations panel, and EventLog panel — all populated with values (not blank/zeroed)
- The TapeState panel shows "buyer_control" (or "Buyer Control")
- The TopBar status dot reads "live" (green) once data has arrived
- The waiting treatment screen (UT-02) does NOT persist after the first trade arrives

---

### UT-12 — Mode selector switches between Live, Historical, and Simulated without regression (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Locate the data-source mode selector (e.g., a dropdown or tab set near the top of the page)
3. Click "Live" mode — observe what controls appear
4. Click "Historical" mode — observe what controls appear (expect a date/time picker or window selector)
5. Click "Simulated" mode — observe what controls appear (expect a ticker/symbol input)
6. In Simulated mode, type `SIM-BUYER` and click "Watch"
7. Wait up to 10 seconds for the cockpit to populate

**Expected Result:**
- Step 3: Live mode shows a symbol search input (for real tickers); no date picker
- Step 4: Historical mode shows a symbol search input AND a date/window picker; no simulator ticker field
- Step 5: Simulated mode shows the simulator ticker input; no date picker
- Step 7: `SIM-BUYER` produces a cockpit with buyer_control state (regression: this behaviour is unchanged)

---

### UT-13 — Connecting state appears immediately after clicking Watch on a valid symbol (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker/symbol input field (Simulated mode)
3. Click the "Watch" button
4. Immediately look at the cockpit area (within the first 1 second)

**Expected Result:**
- A "Connecting to SIM-BUYER…" (or similar connecting/pending) message appears within approximately 1 second of clicking Watch
- The idle screen is no longer visible
- The status dot in the TopBar changes from its idle state to a connecting or waiting indicator

---

### UT-14 — Waiting treatment screen is discoverable and labels are clear (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- A stream is in the `waiting` state (follow UT-02 steps 1–5)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `WAIT-TEST` into the ticker/symbol input field
3. Click the "Watch" button
4. Wait for the waiting treatment screen to appear
5. Read the text on the waiting treatment screen without any developer knowledge

**Expected Result:**
- The waiting screen clearly identifies: (a) the ticker symbol being watched (e.g., "WAIT-TEST"), (b) the data-source mode (e.g., "Simulated" or "sim"), and (c) what the user is waiting for (e.g., "waiting for the first trade")
- A new user unfamiliar with the system can understand why nothing is shown yet (they are waiting for the first trade, not experiencing an error)
- The amber pulsing dot in the TopBar visually reinforces that the system is active but waiting (not broken)

---

### UT-15 — Snapshot-borne failed error banner message is readable and actionable (UX)

**Type:** ux
**Priority:** P2
**Surface:** `/` — TopBar error banner

**Preconditions:**
- Frontend is running at http://localhost:3650
- A stream has reached `stream_status === "failed"` after connecting (follow UT-04 steps 1–5)

**Steps:**
1. Follow steps 1–5 from UT-04 to reach the `failed` state
2. Read the error banner that appears in the TopBar area
3. Read the content of the StreamFailedState component in the cockpit area

**Expected Result:**
- The TopBar error banner contains the text "The tape feed failed after connecting. No tape is shown."
- The StreamFailedState component displays a rose/pink warning icon (not a blank panel)
- A new user can understand that the connection was established but subsequently failed, and that no tape data is available — they are not left wondering if the page is loading or broken

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home page loads without errors | smoke | P1 | `/` |
| UT-02 | WaitingState renders when stream connects with no trade | happy-path | P1 | `/` |
| UT-03 | TopBar status dot shows amber "waiting" label | happy-path | P1 | `/` TopBar |
| UT-04 | Snapshot-borne failed state renders StreamFailedState and error banner | happy-path | P1 | `/` |
| UT-05 | TopBar status dot shows rose "failed" label for snapshot-borne failure | happy-path | P1 | `/` TopBar |
| UT-06 | Price chart is hidden during waiting state | happy-path | P1 | `/` |
| UT-07 | Price chart is hidden during snapshot-borne failed state | error | P1 | `/` |
| UT-08 | Empty Watch shows inline validation | validation | P2 | `/` |
| UT-09 | Whitespace-only ticker shows validation | validation | P2 | `/` |
| UT-10 | Idle screen leaves within ~1 second of clicking Watch | regression | P1 | `/` |
| UT-11 | SIM-BUYER still resolves to full cockpit with buyer_control | regression | P1 | `/` |
| UT-12 | Mode selector switches between modes without regression | regression | P1 | `/` |
| UT-13 | Connecting state appears immediately after clicking Watch | regression | P1 | `/` |
| UT-14 | Waiting treatment screen is discoverable and labels are clear | ux | P2 | `/` |
| UT-15 | Snapshot-borne failed error banner is readable and actionable | ux | P2 | `/` TopBar |

**P1 tests must all pass for browser QA verdict to be PASS.**
