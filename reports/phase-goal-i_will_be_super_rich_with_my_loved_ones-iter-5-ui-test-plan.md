# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-5 — UI Test Plan

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-5
**Date:** 2026-06-10
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Cockpit loads and thesis strip element is present in DOM (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000 (verify with `curl http://localhost:8000/health`)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load (chart and panels visible)
3. Open browser DevTools (F12), switch to the Elements tab
4. Use Ctrl+F (Find) and search for `data-testid="thesis-strip"`

**Expected Result:**
- The Cockpit page renders without a blank screen or error overlay
- The chart area is visible in the upper section of the page
- Exactly one element with `data-testid="thesis-strip"` is found in the DOM
- No "Application error" or "500" message is visible on the page

---

### UT-02 — Idle thesis strip shows declare affordance with no verdict chip (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- No active thesis exists for the currently watched ticker (fresh backend start, or orphan sweep has run)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load
3. Locate the thesis strip section between the chart and the panel grid
4. Inspect the thesis strip visually

**Expected Result:**
- The thesis strip displays a single declare affordance (a button or form entry point labeled something like "Declare" or showing a declare form)
- No verdict chip (emerald/amber/rose/slate coloured pill) is visible inside the strip
- No evidence line or statement list is visible inside the strip
- The strip does NOT show the text "server error" or a 5xx error message

---

### UT-03 — Declare a thesis on SIM-BIDABS and strip transitions to active thesis view (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000 against the persistent `tapeology_journal.db` (schema v2)
- The ticker SIM-BIDABS is being watched (tape is running in bid_absorption state)
- No active thesis exists for SIM-BIDABS

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the chart and thesis strip to load
3. In the thesis strip declare form, locate the "Setup type" or equivalent field and select "absorption_reversal"
4. Locate the "Direction" field and select "long"
5. Locate the "Invalidation price" field and type `99.0`
6. Click the "Declare" button (or equivalent submit action inside the thesis strip)
7. Wait up to 5 seconds for the strip to update

**Expected Result:**
- The thesis strip transitions from the idle declare affordance view to the active thesis view
- A verdict chip appears — it is slate-coloured and shows the label "pending"
- The setup type "absorption_reversal" and direction "long" are visible inside the active thesis view
- The invalidation price 99.0 is visible in the active thesis view
- An evidence line or statement list is visible below the verdict chip
- No "server error", "503", or "500" message appears anywhere in the strip
- The URL remains `http://localhost:3650` (no page redirect)

---

### UT-04 — Verdict chip updates from pending to confirming after engine judges the tape (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- A thesis has been successfully declared (UT-03 passed or equivalent state)
- The tape scenario is producing buyer control signals (SIM-BIDABS flipping to buyer_control)
- Frontend is running at http://localhost:3650

**Steps:**
1. After a successful declaration (UT-03), remain on `http://localhost:3650`
2. Observe the verdict chip inside the thesis strip
3. Wait up to 10 seconds for the tape to produce a confirming signal
4. Watch the verdict chip label and colour

**Expected Result:**
- The verdict chip label changes from "pending" (slate) to "confirming" (emerald green)
- The chip colour updates from slate/grey to emerald/green
- The transition happens without a page reload
- An evidence line below the chip shows plain-language text explaining the confirming state (e.g. "tape moving in favour of the thesis")
- The active thesis setup, direction, and invalidation fields remain visible and unchanged

---

### UT-05 — Wrong-side invalidation price shows inline 422 error visible in pixels (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- A ticker (e.g. SIM-BUYER) is being watched
- No active thesis exists for that ticker

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the thesis strip declare form, select setup type "trend_continuation"
3. Select direction "long"
4. In the "Invalidation price" field, type a price that is ABOVE the current last traded price (an invalid placement for a long thesis — the invalidation should be below, not above)
5. Click the "Declare" button

**Expected Result:**
- The declaration does NOT succeed (no active thesis view appears in the strip)
- An error message is displayed as visible text INSIDE the thesis strip — not in a browser alert, not hidden in the browser console, not as a toast that auto-dismisses
- The error message references the wrong-side invalidation issue (e.g. "invalidation price must be below current price for a long thesis" or similar 422 error text)
- The declare form remains accessible so the operator can correct the value
- No partial thesis is saved — the strip remains in the idle declare state

---

### UT-06 — Missing level price for level_break setup shows 422 error inline (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- A ticker is being watched
- No active thesis exists for that ticker

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the thesis strip declare form, select setup type "level_break"
3. Select direction "long"
4. In the "Invalidation price" field, type a value below the current last traded price (e.g. `90.0`)
5. Leave the "Level price" field empty
6. Click the "Declare" button

**Expected Result:**
- The declaration does NOT succeed
- An error message is displayed as inline text inside the thesis strip (not a browser alert, not auto-dismissing toast)
- The error message indicates that a level price is required for the level_break setup type
- The declare form remains visible and accessible
- The URL remains `http://localhost:3650`

---

### UT-07 — Forbidden level price for absorption_reversal setup shows 422 error inline (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- A ticker is being watched
- No active thesis exists for that ticker

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the thesis strip declare form, select setup type "absorption_reversal"
3. Select direction "long"
4. In the "Invalidation price" field, type a value below the current last traded price (e.g. `90.0`)
5. In the "Level price" field, type any value (e.g. `105.0`) — this field is not permitted for absorption_reversal
6. Click the "Declare" button

**Expected Result:**
- The declaration does NOT succeed
- An error message appears as inline text inside the thesis strip
- The error message indicates that a level price is not allowed for the absorption_reversal setup type
- The declare form remains visible
- No partial thesis is saved

---

### UT-08 — Second active thesis declaration shows 409 error with explicit message (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- One thesis has already been successfully declared and is currently active for the watched ticker (UT-03 has been completed)

**Steps:**
1. Navigate to `http://localhost:3650` (or remain on the page with the active thesis)
2. Observe that the thesis strip currently shows an active thesis view (verdict chip visible)
3. Attempt to declare a second thesis: if a declare form is accessible, select any valid setup type and direction, enter a valid invalidation price, and click "Declare"
4. Wait for the response

**Expected Result:**
- The second declaration does NOT succeed
- An error message appears inside the strip with explicit text indicating only one active thesis is allowed per ticker (e.g. "a thesis is already active" or text referencing a 409 conflict)
- The original active thesis view remains unchanged in the strip
- No new thesis is created — the original thesis is still the one displayed

---

### UT-09 — Declaration against unknown / unwatched ticker shows 404 error (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- The frontend exposes a way to input a ticker symbol in the declare form (or the ticker field is editable)

**Steps:**
1. Navigate to `http://localhost:3650`
2. In the thesis strip declare form, if there is a ticker input field, type `UNKNOWN-TICKER-XYZ`
3. Select any setup type (e.g. "absorption_reversal"), direction "long", and type `90.0` in the "Invalidation price" field
4. Click the "Declare" button

**Expected Result:**
- The declaration does NOT succeed
- An error message appears in the thesis strip area indicating the ticker is not watched / not found (referencing a 404 or "not found" condition)
- The strip does not show an active thesis view
- No partial thesis is saved

---

### UT-10 — Terminal invalidated state shows rose-bordered chip and offending print as evidence (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- SIM-SELLER is being watched
- A thesis has been declared with setup type "trend_continuation", direction "long", and an invalidation price set just above the current last (so that a downward print will cross it)
- The thesis is currently in the active state

**Steps:**
1. Navigate to `http://localhost:3650` with the active thesis visible in the strip
2. Observe the verdict chip inside the thesis strip
3. Wait for the SIM-SELLER scenario to produce a trade print below the declared invalidation level
4. Observe the verdict chip and strip appearance

**Expected Result:**
- The verdict chip transitions to a rose-coloured chip with the label "invalidated"
- The chip has a visible ring border treatment (rose ring around the chip — the "terminal treatment")
- An evidence line below the chip shows the offending print price as text (e.g. "invalidated at 94.50" or "print below invalidation level: 94.50")
- The thesis auto-resolves — no further verdict changes occur after invalidation
- The active thesis view remains visible in the strip (the strip does not revert to the idle declare affordance — the invalidated thesis is still shown until explicitly dismissed or on next load)

---

### UT-11 — data-testid="thesis-strip" attribute is present in both idle and active states (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3650` with no active thesis (idle state)
2. Open browser DevTools (F12) → Elements tab
3. Use Ctrl+F to search for the text `thesis-strip`
4. Record whether the element is found and note its tag name
5. Now declare a thesis successfully (follow UT-03 steps)
6. After the strip transitions to active thesis view, repeat the DevTools search for `thesis-strip`

**Expected Result:**
- In idle state: exactly one element with `data-testid="thesis-strip"` is found; it is the root `<section>` element of the thesis strip; it is visible on screen
- In active thesis state: the same element with `data-testid="thesis-strip"` is still found in the same location; it has not been replaced with a different element lacking the attribute
- The attribute is present in BOTH states — the regression check ensures the attribute is not accidentally stripped during the idle→active transition

---

### UT-12 — Cockpit chart and panel grid still render correctly after declaration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000
- A thesis has been declared and the strip shows the active thesis view

**Steps:**
1. Navigate to `http://localhost:3650`
2. Declare a thesis following UT-03 steps
3. After the strip transitions to the active thesis view, scroll up to verify the chart area
4. Scroll down to verify the panel grid below the thesis strip

**Expected Result:**
- The price chart above the thesis strip continues to render and update with live tape data — it is not blank or frozen
- The panel grid below the thesis strip (if present) renders its panels without layout breakage
- The thesis strip is positioned between the chart and the panel grid — the layout has not shifted or collapsed
- No overlapping UI elements or visual clipping of the thesis strip content is visible

---

### UT-13 — Idle thesis strip shows only the declare affordance with no stale verdict state (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend has performed its startup orphan sweep (any previously orphaned active theses have been resolved to expired)
- No currently active thesis exists for the watched ticker

**Steps:**
1. Restart the backend (or confirm it has freshly started with the orphan sweep completed)
2. Navigate to `http://localhost:3650`
3. Wait for the page to fully load
4. Inspect the thesis strip area

**Expected Result:**
- The thesis strip shows the declare affordance — a button or form entry point to declare a new thesis
- No verdict chip (slate, emerald, amber, or rose) is visible inside the strip
- No statement list or evidence line is visible
- The strip does NOT show any error message referencing a previously orphaned thesis
- The element `[data-testid="thesis-strip"]` resolves to this single-line idle affordance — it is the only strip element visible

---

### UT-14 — Verdict chip colour semantics are visually correct for each verdict state (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Operator has access to multiple sim tickers (SIM-BIDABS, SIM-BUYER, SIM-SELLER, SIM-REVERSAL) to trigger different verdict states
- At least one thesis can be declared and observed cycling through states

**Steps:**
1. Navigate to `http://localhost:3650`
2. Declare a thesis on SIM-BIDABS (absorption_reversal / long) and observe the initial verdict chip immediately after declaration
3. Note the chip colour — it should be slate/grey for the "pending" state
4. Watch SIM-BUYER with a trend_continuation/long thesis after the dwell period elapses and observe the confirming chip colour
5. Watch SIM-SELLER with a trend_continuation/long thesis and observe the rejecting chip colour
6. Declare a thesis with an invalidation level that will be crossed and observe the invalidated chip colour and ring treatment

**Expected Result:**
- "pending" verdict: chip is slate/grey coloured with the text "pending"
- "confirming" verdict: chip is emerald/green coloured with the text "confirming"
- "weakening" verdict: chip is amber/yellow coloured with the text "weakening"
- "rejecting" verdict: chip is rose/red coloured with the text "rejecting"
- "invalidated" verdict: chip is rose/red coloured with the text "invalidated" AND has a visible rose ring border (terminal treatment distinct from "rejecting")
- Each state is clearly distinguishable from the others by colour alone (operator does not need to read the text to distinguish confirming from invalidated)

---

### UT-15 — Evidence text is always visible below the verdict chip (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- A thesis has been declared and has moved past the "pending" initial state

**Steps:**
1. Navigate to `http://localhost:3650`
2. Declare a thesis on any available sim ticker and wait for the verdict to move beyond "pending" (to confirming, weakening, rejecting, or invalidated)
3. Look below the verdict chip inside the thesis strip

**Expected Result:**
- Below the verdict chip, at least one line of plain-language evidence text is visible (e.g. "tape absorbing aggressive selling", "buyer control confirmed after dwell", "opposing control on the tape")
- The evidence text is NOT hidden below a fold, requiring a scroll to see it within the strip
- The evidence text does NOT contain technical field names or raw JSON — it is human-readable
- The evidence text accurately describes the current tape condition relative to the thesis (not a generic placeholder like "evidence")

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit loads and thesis strip element present in DOM | smoke | P1 | `/` |
| UT-02 | Idle strip shows declare affordance with no verdict chip | smoke | P1 | `/` |
| UT-03 | Declare thesis on SIM-BIDABS — strip transitions to active view | happy-path | P1 | `/` |
| UT-04 | Verdict chip updates from pending to confirming live | happy-path | P1 | `/` |
| UT-05 | Wrong-side invalidation shows inline 422 error in pixels | validation | P1 | `/` |
| UT-06 | Missing level price for level_break shows 422 inline | validation | P2 | `/` |
| UT-07 | Forbidden level price for absorption_reversal shows 422 inline | validation | P2 | `/` |
| UT-08 | Second active thesis shows 409 error with explicit message | error | P2 | `/` |
| UT-09 | Unknown ticker declaration shows 404 error | error | P2 | `/` |
| UT-10 | Terminal invalidated state shows rose-bordered chip and offending print | happy-path | P1 | `/` |
| UT-11 | data-testid="thesis-strip" present in both idle and active states | regression | P1 | `/` |
| UT-12 | Chart and panel grid still render correctly after declaration | regression | P1 | `/` |
| UT-13 | Idle strip shows only declare affordance after orphan sweep | regression | P1 | `/` |
| UT-14 | Verdict chip colour semantics are visually correct | ux | P2 | `/` |
| UT-15 | Evidence text is always visible below the verdict chip | ux | P2 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.**
