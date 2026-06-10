# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-2 — UI Test Plan

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-2
**Date:** 2026-06-10
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Cockpit page loads with ThesisStrip idle bar visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- No prior thesis has been declared on SIM-BIDABS

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the ticker input field, type `SIM-BIDABS` and start the watch (click the watch/start button)
3. Wait until the cockpit panel grid becomes visible (price chart and feature panels are populated — this may take 5–15 seconds for the SIM stream to settle)
4. Observe the area between the price chart and the cockpit panel grid
5. Confirm the text "Declare a thesis on this ticker to watch the tape judged against it." is visible in a single horizontal bar
6. Confirm a button labelled "Declare thesis" is visible within that bar
7. Confirm no form fields (Setup, Direction, Invalidation) are visible yet

**Expected Result:**
- The cockpit page renders without a blank screen or error overlay
- A single horizontal thesis strip bar appears between the price chart and the panel grid
- The bar contains the text "Declare a thesis on this ticker to watch the tape judged against it." and a "Declare thesis" button
- No form fields, dropdowns, or price inputs are visible inside the strip while it is in idle state
- The cockpit panel grid below the strip (tape state, features, event log panels) is fully visible and not shifted or hidden

---

### UT-02 — ThesisStrip does not appear during stream connecting / waiting states (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3650`
2. Immediately after typing `SIM-BIDABS` into the ticker field and clicking the watch/start button, watch the screen
3. While the page shows "Connecting…" or "Waiting for first event" (before the cockpit panel grid appears), look specifically at the area where the thesis strip will eventually appear

**Expected Result:**
- During the "Connecting…" phase, no thesis strip bar is visible
- During the "Waiting for first event" phase, no thesis strip bar is visible
- The strip only becomes visible after the cockpit panel grid is fully populated with live state and feature data
- There is no flash of the strip during the connecting/waiting period

---

### UT-03 — Declare thesis form opens with taxonomy-driven fields (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- SIM-BIDABS is being watched and the cockpit is settled (panel grid is visible)
- The thesis strip idle bar is visible with the "Declare thesis" button
- No active thesis exists on SIM-BIDABS

**Steps:**
1. Navigate to `http://localhost:3650` with SIM-BIDABS watched and cockpit settled
2. Click the "Declare thesis" button in the thesis strip
3. Wait for the form to fully load (the "Loading the setup catalog…" message may briefly appear, then disappear)
4. Confirm a "Setup" dropdown (or select element) is visible and populated with options
5. Confirm a "Direction" dropdown (or select element) is visible and populated with options
6. Confirm an "Invalidation" price input field is visible
7. Confirm a "Declare" submit button is visible
8. Confirm a "Cancel" button is visible
9. Click on the "Setup" dropdown and confirm the options include at least: "Absorption Reversal", "Trend Continuation", "Level Break" (or "Level Break-and-Go"), "Failed Move Fade"
10. Select "Absorption Reversal" from the Setup dropdown and confirm no "Level" price input field appears

**Expected Result:**
- The declare form opens inline within the thesis strip (no new page, no separate modal outside the strip)
- A "Setup" dropdown is populated with at least 4 setup options sourced from the backend taxonomy
- A "Direction" dropdown is visible (with at least "Long" and "Short" options)
- An "Invalidation" price input field is visible
- "Declare" and "Cancel" buttons are visible
- When "Absorption Reversal" is selected, NO "Level" price input field is shown
- The "Loading the setup catalog…" message does NOT persist — it resolves to the form

---

### UT-04 — Level field appears conditionally for level-requiring setups (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- SIM-BIDABS is being watched and cockpit is settled
- The thesis declare form is open (click "Declare thesis" to open it)

**Steps:**
1. With the declare form open, confirm the currently selected Setup is "Absorption Reversal" (or select it if not already selected)
2. Confirm there is NO "Level" price input field visible
3. Open the "Setup" dropdown and select "Level Break" (or "Level Break-and-Go" — whichever label the form shows)
4. Confirm a "Level" price input field NOW appears in the form
5. Open the "Setup" dropdown again and select "Failed Move Fade"
6. Confirm the "Level" price input field is still visible
7. Open the "Setup" dropdown again and select "Absorption Reversal"
8. Confirm the "Level" price input field DISAPPEARS immediately
9. Open the "Setup" dropdown again and select "Trend Continuation"
10. Confirm the "Level" price input field is NOT visible

**Expected Result:**
- No "Level" field is visible when Setup is "Absorption Reversal" or "Trend Continuation"
- A "Level" price input field appears immediately when Setup is "Level Break" or "Failed Move Fade"
- Changing the Setup back to a non-level setup causes the Level field to disappear immediately (no page reload)
- The toggle between presence and absence of the Level field is instant

---

### UT-05 — Declare a valid absorption_reversal long thesis and see active display (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- SIM-BIDABS is being watched and the cockpit is settled
- The thesis strip idle bar is visible
- No active thesis exists on SIM-BIDABS
- The current last price for SIM-BIDABS is visible in the price chart (note this value before declaring)

**Steps:**
1. Navigate to `http://localhost:3650` with SIM-BIDABS watched and cockpit settled
2. Click the "Declare thesis" button in the thesis strip
3. Wait for the form to load fully
4. In the "Setup" dropdown, select "Absorption Reversal"
5. In the "Direction" dropdown, select "Long"
6. In the "Invalidation" price field, type a price that is below the current last price visible on the chart (for example, if last price is 100.00, type `98.50`)
7. Confirm no "Level" price field is visible (correct for Absorption Reversal)
8. Click the "Declare" button
9. Wait for the submission to complete (the button may show "Declaring…" briefly while in flight)
10. Observe the thesis strip after the form closes

**Expected Result:**
- The "Declare" button shows "Declaring…" and is disabled while the POST is in flight
- After submission, the form closes and the strip transitions to the active thesis display without a page reload
- The active strip shows the setup name (e.g., "Absorption Reversal") in normal or sentence-case text
- The direction "Long" is shown in emerald (green) color
- The invalidation price entered is shown in a monospace font
- A bulleted list of expected-behaviour statements is visible, each with a colored status dot and a label ("met", "not yet", or "violated")
- A slate-colored "Pending" badge is visible
- A footer line shows the bound source (e.g., "SIM-BIDABS") and feed (e.g., "sim") stamp
- The text "Descriptive only — not trading advice." appears somewhere in the active strip
- No error message appears in the strip

---

### UT-06 — Cancel button dismisses the form without creating a thesis (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- SIM-BIDABS is being watched and the cockpit is settled
- The thesis strip idle bar is visible with the "Declare thesis" button

**Steps:**
1. Click the "Declare thesis" button in the thesis strip
2. Wait for the form to load
3. In the "Setup" dropdown, select "Trend Continuation"
4. In the "Direction" dropdown, select "Short"
5. In the "Invalidation" field, type `105.00`
6. Click the "Cancel" button
7. Observe the thesis strip after clicking Cancel

**Expected Result:**
- The form closes immediately when "Cancel" is clicked
- The thesis strip returns to its idle single-line state with the text "Declare a thesis on this ticker to watch the tape judged against it." and the "Declare thesis" button
- No active thesis is shown — the strip does NOT transition to the active thesis display
- The cockpit panel grid below is unchanged and undisturbed

---

### UT-07 — Wrong-side invalidation shows inline rose error and preserves form values (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- SIM-BIDABS is being watched and the cockpit is settled
- The thesis declare form is open
- The current last price for SIM-BIDABS is visible (note the value)

**Steps:**
1. With the declare form open, select "Absorption Reversal" from the Setup dropdown
2. Select "Long" from the Direction dropdown
3. In the "Invalidation" price field, type a price that is ABOVE the current last price (for example, if last price is 100.00, type `102.00` — this is the wrong side for a long thesis)
4. Click the "Declare" button
5. Wait for the response

**Expected Result:**
- The form does NOT close
- An error message in rose (red) text appears below the form — the message should reference the wrong-side invalidation (e.g., "invalidation price must be below current last for long" or similar wording from the backend)
- The form values are preserved: Setup still shows "Absorption Reversal", Direction still shows "Long", Invalidation field still shows the entered price
- No thesis is created — the strip does NOT transition to the active thesis display
- The "Declare" button is re-enabled after the error appears

---

### UT-08 — Level Break setup without level price shows inline error (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- SIM-BIDABS is being watched and the cockpit is settled
- The thesis declare form is open

**Steps:**
1. With the declare form open, select "Level Break" (or "Level Break-and-Go") from the Setup dropdown
2. Confirm a "Level" price input field appears
3. Select "Long" from the Direction dropdown
4. In the "Invalidation" price field, type `98.00` (a price below current last, valid for long)
5. Leave the "Level" price field empty
6. Click the "Declare" button
7. Wait for the response

**Expected Result:**
- The form does NOT close
- A rose (red) error message appears indicating the level price is required for this setup type (e.g., "level_price is required for level_break" or equivalent)
- The form values are preserved: Setup still shows "Level Break", Direction still shows "Long", Invalidation still shows `98.00`, Level field is still empty
- No thesis is created

---

### UT-09 — Taxonomy loading state is shown explicitly while catalog is fetching (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- SIM-BIDABS is being watched and the cockpit is settled
- Browser DevTools is open; Network tab is accessible

**Steps:**
1. In browser DevTools, navigate to the Network tab and enable network throttling — set to "Slow 3G" (or the slowest available preset)
2. Click the "Declare thesis" button in the thesis strip
3. Immediately observe the thesis strip area before the form fully appears

**Expected Result:**
- While the `GET /research/taxonomy` request is in flight, the strip shows the text "Loading the setup catalog…" explicitly
- The form fields (Setup dropdown, Direction dropdown, Invalidation input) do NOT appear before the catalog is loaded
- Once the catalog loads, the loading message is replaced by the form
- If the catalog request fails entirely, the strip shows a rose error line (e.g., "Could not load setup catalog") and a "Close" button — NOT a form with guessed values

---

### UT-10 — Duplicate thesis declaration shows inline 409 error (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- SIM-BIDABS is being watched and an active thesis is already declared (the active thesis display is visible in the strip)

**Steps:**
1. With an active thesis already showing in the strip, open a new browser tab or use `curl` in a terminal to send a second thesis declaration:
   - Run: `curl -X POST http://localhost:8000/research/thesis -H "Content-Type: application/json" -d '{"ticker":"SIM-BIDABS","setup_type":"trend_continuation","direction":"short","invalidation_price":105.00}'`
2. Observe the response from the curl command

**Expected Result:**
- The curl command receives HTTP 409 response
- The response body contains a message explicitly stating an active thesis already exists (e.g., "An active thesis already exists on this ticker" or equivalent)
- The frontend's active thesis strip continues to show the FIRST (original) thesis — it is not replaced or cleared
- The second thesis declaration is not persisted

---

### UT-11 — Monitor unavailable notice appears in active thesis footer on backend fault (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- SIM-BIDABS is being watched with an active thesis declared and the active thesis display is visible
- Access to backend logs or ability to simulate a monitor fault is available (advanced tester)

**Steps:**
1. With an active thesis showing in the strip, observe the footer area of the active thesis display
2. If the monitor status is functioning normally, there is NO "Monitor unavailable" notice
3. To trigger the fault state: stop the backend's database (or rename the journal DB file to simulate an I/O error) so the research monitor fails on the next event
4. Observe the footer area of the active thesis display

**Expected Result:**
- When the monitor is functioning: the footer shows the source and feed stamp, and "Descriptive only — not trading advice." — NO "Monitor unavailable" text
- When the monitor is faulted: the footer shows "Monitor unavailable — statement statuses may be stale." in amber text
- Despite the monitor fault, the live tape feed continues: the tape state, confidence score, and price chart still update
- The "Monitor unavailable" notice is shown inline in the thesis strip footer, not as a full-page error or alert

---

### UT-12 — Active thesis statement statuses update live without page reload (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- SIM-BIDABS is being watched with an active thesis declared (active thesis display is visible)
- The expected-behaviour statements with status dots are visible in the strip

**Steps:**
1. Observe the colored status dots next to each expected-behaviour statement in the active thesis strip
2. Note the current status label for at least one statement (e.g., "not yet")
3. Continue observing the strip for 30–60 seconds as the SIM tape progresses through events
4. Watch for any status dot color or label to change (e.g., from "not yet" to "met" or "violated")

**Expected Result:**
- Over time, at least one statement status dot changes color and/or label without requiring a page reload
- The status transitions use: emerald (green) for "met", slate or amber for "not yet", rose (red) for "violated"
- The status changes reflect the live tape data updating in the WebSocket stream
- The price chart, tape state panel, and feature panels continue updating normally alongside the thesis strip — no interference between the strip and existing cockpit components

---

### UT-13 — Cockpit page layout is undisturbed by the idle thesis strip (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- SIM-BIDABS is being watched and the cockpit is settled
- No active thesis exists (strip is in idle state)

**Steps:**
1. Navigate to `http://localhost:3650` with SIM-BIDABS watched and cockpit settled
2. Observe the vertical order of elements on the page: TopBar, PriceChart, ThesisStrip (idle bar), and the Cockpit panel grid
3. Confirm the PriceChart (candlestick chart) is fully visible and rendering candles with the bar-size selector
4. Confirm the pause/resume control buttons are visible in the cockpit
5. Confirm the tape state panel, feature panels, and event log are all visible in the panel grid below
6. Scroll down the page — confirm the panel grid is not displaced, hidden, or clipped by the thesis strip
7. Resize the browser window (drag it narrower or shorter) — confirm the strip remains a single horizontal bar and does not cause the panel grid to reflow vertically

**Expected Result:**
- The top-to-bottom order of elements is: TopBar → PriceChart → ThesisStrip (single idle bar) → Cockpit panel grid
- The price chart shows candlesticks and a bar-size selector — unchanged from before this phase
- Pause/resume controls are visible and functional
- The panel grid shows all feature panels and event log — unchanged from before this phase
- The idle thesis strip does NOT cause any panel below it to shift, hide, or misalign
- Resizing the viewport does not cause the strip to expand and push down the grid

---

### UT-14 — Thesis strip verdict badge is always "Pending" in this iteration (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- SIM-BIDABS is being watched with an active thesis declared
- The active thesis display is visible in the thesis strip

**Steps:**
1. Observe the active thesis display in the strip
2. Locate the verdict badge — it should appear as a small colored pill/badge near the thesis information
3. Confirm the badge shows the text "Pending" in a slate (grey) color
4. Wait 60 seconds while the tape continues streaming
5. Confirm the verdict badge still shows "Pending" — it does NOT change to any other verdict

**Expected Result:**
- The verdict badge shows exactly "Pending" in slate (grey) color
- The badge does not change to "Confirming", "Weakening", "Rejecting", or "Invalidated" during this iteration
- The badge remains "Pending" for the full duration of the watched session
- This behavior is expected and correct for iteration 2 — the verdict transition engine is a future iteration

---

### UT-15 — Active thesis displays "not trading advice" disclaimer (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- SIM-BIDABS is being watched with an active thesis declared
- The active thesis display is visible

**Steps:**
1. Look at the footer of the active thesis display in the strip
2. Read all text in the footer area

**Expected Result:**
- The footer contains the text "Descriptive only — not trading advice." (exact wording may vary slightly but the substance must be present)
- No imperative trading language appears anywhere in the strip (no "Buy", "Sell", "Enter", "Exit")
- The setup name and direction labels use present-tense descriptive language, not prediction language

---

### UT-16 — Active thesis shows source and feed stamp in footer (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- SIM-BIDABS is being watched with an active thesis declared
- The active thesis display is visible

**Steps:**
1. Observe the footer of the active thesis display
2. Look for a line that identifies the data source and feed

**Expected Result:**
- The footer contains a source identifier (e.g., "SIM-BIDABS" or the scenario name) and a feed label (e.g., "sim" or "SIM")
- Both the source and feed values are visible — the operator can confirm which data source and feed the thesis was declared on
- The source and feed are not blank or "undefined"

---

### UT-17 — Short thesis direction displays in rose color (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- SIM-BIDABS is being watched with a SHORT thesis declared (e.g., Trend Continuation / Short / invalidation above current last)

**Steps:**
1. Declare a valid short thesis: click "Declare thesis", select "Trend Continuation", select "Short", type a price ABOVE the current last price in the "Invalidation" field, click "Declare"
2. Wait for the active thesis display to appear
3. Observe the direction label in the active thesis display

**Expected Result:**
- The direction "Short" is displayed in rose (red/pink) color
- Compare this with a long thesis: the direction "Long" should appear in emerald (green) color
- The color coding provides an at-a-glance directional indicator

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit page loads with ThesisStrip idle bar visible | smoke | P1 | `/` |
| UT-02 | ThesisStrip does not appear during connecting/waiting states | smoke | P1 | `/` |
| UT-03 | Declare thesis form opens with taxonomy-driven fields | happy-path | P1 | `/` |
| UT-04 | Level field appears conditionally for level-requiring setups | happy-path | P1 | `/` |
| UT-05 | Declare a valid absorption_reversal long thesis and see active display | happy-path | P1 | `/` |
| UT-06 | Cancel button dismisses the form without creating a thesis | happy-path | P1 | `/` |
| UT-07 | Wrong-side invalidation shows inline rose error and preserves form values | validation | P2 | `/` |
| UT-08 | Level Break setup without level price shows inline error | validation | P2 | `/` |
| UT-09 | Taxonomy loading state is shown explicitly while catalog is fetching | validation | P2 | `/` |
| UT-10 | Duplicate thesis declaration shows inline 409 error | error | P2 | `/` |
| UT-11 | Monitor unavailable notice appears in active thesis footer on backend fault | error | P2 | `/` |
| UT-12 | Active thesis statement statuses update live without page reload | regression | P1 | `/` |
| UT-13 | Cockpit page layout is undisturbed by the idle thesis strip | regression | P1 | `/` |
| UT-14 | Thesis strip verdict badge is always "Pending" in this iteration | ux | P3 | `/` |
| UT-15 | Active thesis displays "not trading advice" disclaimer | ux | P3 | `/` |
| UT-16 | Active thesis shows source and feed stamp in footer | ux | P2 | `/` |
| UT-17 | Short thesis direction displays in rose color | ux | P2 | `/` |

**P1 tests (UT-01, UT-02, UT-03, UT-04, UT-05, UT-06, UT-12, UT-13) must all pass for browser QA verdict to be PASS.**
