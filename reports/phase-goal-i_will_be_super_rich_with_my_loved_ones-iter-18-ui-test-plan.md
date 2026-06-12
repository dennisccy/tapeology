# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-18 — UI Test Plan

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-18
**Date:** 2026-06-12
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->
<!-- Vague steps like "test the form" or "verify it works" are not acceptable. -->

---

### UT-01 — Studies nav entry is an active link, not a disabled label (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** Global nav (`NavBar.tsx`) — all pages

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running (canary: `curl -s http://localhost:8000/research/taxonomy` returns HTTP 200)

**Steps:**
1. Navigate to `http://localhost:3650` (the home/cockpit page)
2. Locate the "Studies" item in the top navigation bar
3. Inspect whether it has a hover cursor (pointer, not not-allowed)
4. Confirm no tooltip text "Coming with replay studies" appears on hover

**Expected Result:**
- The "Studies" label in the top navigation is rendered as a clickable link (not greyed-out text)
- Hovering over "Studies" shows a pointer cursor and no disabled tooltip
- The link does NOT have `aria-disabled="true"` or `cursor-not-allowed` styling

---

### UT-02 — Studies nav entry navigates to /studies (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** Global nav (`NavBar.tsx`) — all pages

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Studies" link in the top navigation bar
3. Wait for the page to fully load

**Expected Result:**
- Browser navigates to `http://localhost:3650/studies`
- The "Studies" nav entry gains an emerald (green) active highlight
- No blank screen, no 404 error, no JavaScript crash banner

---

### UT-03 — /studies page loads with required structure (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/studies`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Wait for the page to fully load

**Expected Result:**
- Page title or heading containing "Replay studies" (or "Studies") is visible
- A measurement-framing paragraph is visible near the top of the page (descriptive copy, not a marketing claim)
- A create-study form area is visible on the left side of the layout
- A right-column panel with "∅" and placeholder text is visible (empty selection state)
- No blank white area, no crash banner, no "undefined" text visible anywhere

---

### UT-04 — /studies empty selection state shows correct placeholder (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/studies` — `StudyResultsView` empty state

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- No study has been selected (fresh page load or no studies exist)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Do NOT click any row in the job list
3. Observe the right column

**Expected Result:**
- The right column shows a grey panel containing the "∅" symbol
- The text "Create a study, or select one from the list, to read its results." is visible in the right column
- No white blank area, no error message, no spinner stuck indefinitely

---

### UT-05 — StudyList shows "No studies yet" empty state (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/studies` — `StudyList` empty state

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- No studies have been created (use a fresh database or clear all studies)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Wait for the job list area to finish loading (loading spinner disappears)

**Expected Result:**
- The job list area shows the text "No studies yet — create one above…" (or equivalent from taxonomy)
- No blank/white area appears in the job list section
- No spinner is stuck in a permanent loading state

---

### UT-06 — StudyList shows brief loading state on hard reload (smoke)

**Type:** smoke
**Priority:** P2
**Surface:** `/studies` — `StudyList` loading state

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Immediately hard-reload the page (press Ctrl+Shift+R or Cmd+Shift+R)
3. Observe the job list area in the first ~1–2 seconds before data loads

**Expected Result:**
- A brief loading indicator is visible (pulsing dot or spinner and "Loading studies…" text)
- After loading completes, either the empty state message or the list of studies renders
- The page does NOT flash a blank white area or error without first showing a loading indicator

---

### UT-07 — Create study with Reference Window source: happy path end-to-end (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyCreateForm`, `StudyList`, `StudyResultsView`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running with the PG SIP fixture available
- No studies are in progress (clean state preferred)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. In the create form, click the radio card labeled "Reference window" (the card describing the committed PG SIP fixture — no credentials required)
3. In the "Setup" dropdown, select "absorption_reversal"
4. In the "Direction" dropdown, select "long"
5. Click the "Run study" button
6. Observe the job list: note the status badge on the newly created row
7. Wait for the status badge to change from "Queued" (slate) to "Running" (amber) — do NOT refresh; the list should poll automatically
8. Wait for the status badge to change from "Running" (amber) to "Done" (neutral slate)
9. Click the completed study row in the job list

**Expected Result:**
- After step 5: a new row appears in the job list with a "Queued" slate badge and the setup name "absorption_reversal" and direction "long"
- After step 7: the badge turns amber and shows "Running"; the row shows a monospace event counter (e.g. "3200 events processed")
- After step 8: the badge reads "Done" in neutral slate; the Cancel button is gone from the row
- After step 9: the right panel renders the results with:
  - An "Occurrences" table with columns "Arm time (logical s)", "Verdict reached", "R basis" in monospace font
  - Two side-by-side distribution blocks labeled "Your setup" and "Random-time baseline"
  - Each distribution block shows horizon rows (10s, 30s, 60s, 120s) with four chips per row: +1R (emerald), −1R (rose), neither (slate), Truncated (amber)
  - Three monospace chips in the results header: a Feed chip (e.g. "sip"), a Config fingerprint chip, and a Baseline seed chip
  - The framing text "Descriptive only — not trading advice" visible near the distribution blocks

---

### UT-08 — Create study with Seeded Sim source: SIM-REVERSAL happy path (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyCreateForm`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Click the radio card labeled "Seeded sim scenario"
3. Confirm a dropdown appears with scenario options
4. In the sim scenario dropdown, select "SIM-REVERSAL"
5. In the "Setup" dropdown, select "absorption_reversal"
6. In the "Direction" dropdown, select "long"
7. Click the "Run study" button
8. Wait for the study to reach "Done" status (status badge changes to neutral slate)
9. Click the completed study row

**Expected Result:**
- After step 2: the "Seeded sim scenario" card is selected (visually highlighted); the sim dropdown appears; the symbol/date fields do NOT appear
- After step 3: the dropdown contains at least: SIM-REVERSAL, SIM-BUYER, SIM-SHIFT, SIM-SELLER
- After step 7: a new row appears in the job list with a source/feed badge identifying it as a seeded sim
- After step 9: the right panel shows results with "Your setup" and "Random-time baseline" side by side; feed chip shows the sim identifier

---

### UT-09 — Create study with Symbol + Past Window source: form fields appear (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyCreateForm` historical source

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Click the radio card labeled "Symbol + past window"
3. Observe the form area for newly revealed fields
4. Click the "Open 9:30 ET" preset button (without entering a date first)
5. Enter a date in the date field in the format "09-06-2026" (dd-MM-yyyy)
6. Click the "Open 9:30 ET" preset button again

**Expected Result:**
- After step 2: a symbol search field, a date input labeled or formatted as dd-MM-yyyy, start time input, end time input, and three preset buttons ("Open 9:30 ET", "Close 16:00 ET", "Full RTH") are all visible
- The "Reference window" and "Seeded sim scenario" fields are hidden
- After step 4: the preset button is disabled or produces no action (no time values are filled) — presets are disabled until a valid date is entered
- After step 6: the start time field is populated with "09:30" and the end time field is populated with a corresponding value, confirming the preset became active after a date was entered

---

### UT-10 — Level setup shows level price input and hindsight warning; non-level setup hides it (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/studies` — `StudyCreateForm` conditional level input

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Click the "Reference window" radio card
3. In the "Setup" dropdown, select "absorption_reversal"
4. Observe the form — specifically look for a "Level price" input field and any amber warning box
5. In the "Setup" dropdown, change the selection to "level_break"
6. Observe the form again
7. In the "Setup" dropdown, change the selection back to "absorption_reversal"
8. Observe the form again

**Expected Result:**
- After step 4: NO "Level price" number input is visible; NO amber hindsight warning box is visible
- After step 6: a "Level price" number input appears; an amber-colored warning box appears below it (containing copy about the level being chosen with hindsight and exclusion from cross-study comparison); neither element was present before changing the setup
- After step 8: the "Level price" input disappears; the amber warning box disappears — the form returns to its prior state

---

### UT-11 — Run Study button stays disabled when required fields are missing (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/studies` — `StudyCreateForm` submit button

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Do NOT select any radio card or fill in any field
3. Observe the "Run study" button
4. Click the "Reference window" radio card
5. Leave the Setup and Direction dropdowns at their defaults (empty / placeholder)
6. Observe the "Run study" button
7. Select "level_break" in the Setup dropdown and "long" in the Direction dropdown
8. Do NOT fill in the "Level price" field
9. Observe the "Run study" button

**Expected Result:**
- After step 3: the "Run study" button is visibly disabled (greyed out or non-interactive)
- After step 6: the "Run study" button remains disabled while required dropdowns are unpopulated
- After step 9: the "Run study" button remains disabled even though source and direction are filled — it requires the level price for level setups before becoming enabled

---

### UT-12 — Run Study button transitions to "Running…" during request in flight (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/studies` — `StudyCreateForm` submit button state

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- Reference window source is selected, absorption_reversal + long are selected

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Select "Reference window" radio card
3. In the "Setup" dropdown, select "absorption_reversal"
4. In the "Direction" dropdown, select "long"
5. Click the "Run study" button and immediately watch the button text

**Expected Result:**
- At the moment of clicking, or very shortly after, the button text changes from "Run study" to "Running…" (or an equivalent in-flight indicator)
- The button becomes non-clickable while the request is in flight
- After the request completes and a row appears in the job list, the button returns to its original "Run study" state (ready for the next study)

---

### UT-13 — Run study button enabled for level_break only after level price is filled (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/studies` — `StudyCreateForm` level price validation

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Select "Reference window" radio card
3. In the "Setup" dropdown, select "level_break"
4. In the "Direction" dropdown, select "long"
5. Observe the "Run study" button (it should be disabled)
6. Click the "Level price" number input field and type "150.50"
7. Observe the "Run study" button

**Expected Result:**
- After step 5: the "Run study" button is disabled (not clickable)
- After step 7: the "Run study" button becomes enabled (clickable, normal styling) — the level price was the only remaining required field

---

### UT-14 — Study job list shows correct status badge colors (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyList` status badges

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- At least one study has been completed (Done), one has been cancelled (Cancelled), and one has failed (Failed) — or create them during this test

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Create a new reference-window + absorption_reversal + long study and let it complete (status: Done)
3. Observe the status badge color on the Done row
4. Create another reference-window study; click "Cancel" before it reaches Done
5. Observe the status badge color on the Cancelled row
6. Submit a historical study (Symbol + past window) without valid credentials; wait for it to reach terminal state
7. Observe the status badge color on the Failed row

**Expected Result:**
- Done row: the status badge shows "Done" in neutral slate color
- Running row (while in progress): the status badge shows "Running" in amber color
- Cancelled row: the status badge shows "Cancelled" in slate color
- Failed row: the status badge shows "Failed" in rose (red) color
- No status badge is shown in green (success framing is intentionally avoided)

---

### UT-15 — Cancel a running study: status changes to Cancelled, Cancel button disappears (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyList` cancel action

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A study can be created that remains in Running state long enough to cancel (use a Seeded sim scenario with SIM-REVERSAL)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Select "Seeded sim scenario" radio card, choose "SIM-REVERSAL"
3. Select "absorption_reversal" setup and "long" direction
4. Click "Run study"
5. Watch the job list row until the status badge changes from "Queued" to "Running" (amber)
6. While the status is "Running" (amber badge), click the "Cancel" button on that row
7. Observe the row

**Expected Result:**
- After step 6: the status badge changes from "Running" (amber) to "Cancelled" (slate)
- The "Cancel" button disappears from the row — it is not visible on a Cancelled row
- The list does NOT require a page refresh to show the updated status

---

### UT-16 — Cancelled study shows PARTIAL warning above partial results (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyResultsView` cancelled state

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A study has been successfully cancelled while in Running state (see UT-15)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Locate a row in the job list with a "Cancelled" status badge
3. Click that row

**Expected Result:**
- The right-column results panel displays a "PARTIAL" warning label prominently above any occurrence data (the label should be amber or otherwise visually distinct)
- If any partial occurrence data exists, it is shown below the PARTIAL warning
- The panel does NOT show a generic success state or empty/blank area without explanation
- The panel does NOT show the same results display as a fully completed (Done) study without a warning

---

### UT-17 — Failed study shows rose error message in results panel (error)

**Type:** error
**Priority:** P1
**Surface:** `/studies` — `StudyResultsView` failed state

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running without valid Alpaca/market-data credentials
- A study using "Symbol + past window" source has been submitted and reached "Failed" status

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Submit a study using the "Symbol + past window" source: type "AAPL" in the symbol field, enter a valid past date (e.g. "09-06-2026"), click "Open 9:30 ET" to set times, select any setup and direction, click "Run study"
3. Wait for the row's status badge to change to "Failed" (rose)
4. Click the failed study row

**Expected Result:**
- The study row shows a "Failed" status badge in rose color
- Clicking the row opens the results panel showing a rose-colored error box containing the backend's error message (e.g., "provider unavailable" or similar)
- The results panel does NOT show an empty area, a blank panel, or a generic "no results" without explanation
- The error message is readable and describes the failure reason (not just "error")

---

### UT-18 — Backend 422 error surfaces inline below the form (error)

**Type:** error
**Priority:** P2
**Surface:** `/studies` — `StudyCreateForm` inline error

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running without valid credentials (to reliably trigger a 422 on a historical study submission)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Select "Symbol + past window" radio card
3. Type "AAPL" in the symbol search field
4. Enter the date "09-06-2026" in the date field
5. Click "Open 9:30 ET" to fill start/end times
6. Select "absorption_reversal" in the Setup dropdown
7. Select "long" in the Direction dropdown
8. Click "Run study"
9. Observe the area below the form

**Expected Result:**
- If the backend returns a 422 (validation error or provider unavailable), a rose-colored error box appears below the create form containing the backend's error message
- The page does NOT navigate away, crash, or show a full-page error
- The form fields remain intact so the operator can correct and re-submit

---

### UT-19 — Queued study row shows queued-specific absence copy in results panel (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/studies` — `StudyResultsView` queued absence sentence

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A study has just been submitted and is still in "Queued" state (act quickly after submission)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Submit a new reference-window + absorption_reversal + long study by clicking "Run study"
3. Immediately click the new row in the job list while its badge shows "Queued" (slate)
4. Observe the right-column results panel

**Expected Result:**
- The results panel shows a queued-specific absence sentence (describing that the study is queued, not yet running)
- The copy for a Queued study is DIFFERENT from the copy for a Running study — they are NOT the same sentence
- No results data, no distribution blocks, no occurrence table is shown (the study has not run yet)
- No generic "no results yet" placeholder that could apply to any status

---

### UT-20 — Running study row shows running-specific absence copy in results panel (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/studies` — `StudyResultsView` running absence sentence

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A study is actively in "Running" state

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Submit a new reference-window + absorption_reversal + long study
3. Wait until the status badge changes to "Running" (amber), then click the row
4. Observe the right-column results panel

**Expected Result:**
- The results panel shows a running-specific absence sentence (describing that the study is in progress)
- The copy for a Running study is DIFFERENT from the copy for a Queued study
- No completed results are shown yet
- The running-specific copy is distinct and informative, not a generic placeholder

---

### UT-21 — Running study row shows events-processed counter (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/studies` — `StudyList` running row

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A study is actively in "Running" state

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Submit a new reference-window + absorption_reversal + long study
3. Wait until the status badge changes to "Running" (amber)
4. Observe the running row in the job list — specifically the area after the status badge

**Expected Result:**
- The running row displays a monospace event counter showing a number and the word "events processed" (e.g. "3200 events processed")
- The counter is visible directly on the row without needing to click it
- The counter is in monospace font (consistent with the numeric display convention)

---

### UT-22 — Completed results: side-by-side distribution blocks with four chips per horizon (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyResultsView` distribution blocks

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A reference-window study with absorption_reversal + long has completed (Done)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Click the "Done" study row for a reference-window absorption_reversal study
3. Locate the two distribution blocks in the results panel
4. Within the "Your setup" block, find any horizon row (e.g. the 60s row)
5. Count and identify the chips on that horizon row

**Expected Result:**
- Two distribution blocks are visible side by side (or stacked on narrow screens): "Your setup" (with darker border) and "Random-time baseline" (with lighter border)
- Each distribution block contains rows for horizons: 10s, 30s, 60s, 120s (or whatever horizons are configured)
- Each horizon row shows exactly FOUR distinct chips: +1R (emerald/green chip), −1R (rose/red chip), neither (slate chip), and Truncated (amber chip)
- The Truncated chip is its own chip — it is NEVER merged into the other three counts
- Both distribution blocks show the same horizons, enabling direct side-by-side comparison

---

### UT-23 — Completed results: occurrences table with correct columns in monospace font (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyResultsView` occurrences table

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A reference-window study has completed (Done)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Click any completed "Done" study row
3. Locate the occurrences table in the results panel
4. Read the column headers of the table

**Expected Result:**
- An occurrences table is present with exactly these three columns: "Arm time (logical s)", "Verdict reached", and "R basis"
- All numeric values in the table are rendered in monospace font (not proportional font)
- The table contains at least one data row (for the reference-window study, at least one occurrence should exist)

---

### UT-24 — Completed results: honesty stamps visible in results header (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyResultsView` honesty stamps

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A reference-window study has completed (Done)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Click any completed "Done" study row
3. Look at the results panel header (area at the top of the results view, above the distribution blocks)
4. Identify the three monospace chips

**Expected Result:**
- Three monospace chips are visible in the results header:
  1. A "Feed" chip showing the data feed (e.g. "sip")
  2. A "Config fingerprint" chip showing a hash or short identifier; hovering over it shows a tooltip with the full hash value
  3. A "Baseline seed" chip showing a numeric seed value (e.g. "1729")
- All three chips are rendered in monospace font
- The chips are visible without scrolling (in the header area of the results panel)

---

### UT-25 — Completed results: measurement-framing line visible twice (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyResultsView` framing copy

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A reference-window study has completed (Done) and is selected in the job list

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Click any completed "Done" study row
3. Read the results panel from top to bottom
4. Look for the framing line containing "Descriptive only — not trading advice" (or equivalent from taxonomy)

**Expected Result:**
- The framing line (containing "Descriptive only — not trading advice" or a measurement-framing equivalent) appears at least once ABOVE the distribution blocks
- The same or equivalent framing line appears AGAIN at the foot of the results panel
- The phrase "Journaled measurements" or similar measurement-framing language is present
- No text on the results page uses the words "edge", "win rate", "profit", "predict", "recommend", "buy", or "sell"

---

### UT-26 — Level-break study: hindsight label and amber caption appear in results (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyResultsView` hindsight disclosure

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A level_break study with a level price has been created and completed

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. If no level_break study exists: select "Reference window" source, choose "level_break" in Setup, "long" in Direction, type "150.50" in "Level price", click "Run study", wait for Done status
3. Click the completed level_break study row in the job list
4. Read the results panel header and the area below the framing line

**Expected Result:**
- An amber-colored label reading "Level chosen with hindsight" (or equivalent from taxonomy) is visible in the results header area
- An amber caption block below the framing line explains that this study is excluded from cross-study comparison because the level was chosen with hindsight
- The hindsight label is visually distinct (amber color) and separate from the honesty stamps

---

### UT-27 — Level-break study row shows amber "Hindsight level" chip in job list (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyList` hindsight chip

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A level_break study with a level price has been created (Done or any status)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Create a level_break study with level price "150.50" if one does not already exist
3. Locate the level_break study row in the job list (regardless of its current status)
4. Observe the row for a chip or label related to "Hindsight"

**Expected Result:**
- The level_break study row displays an amber "Hindsight level" chip (or equivalent label) directly on the row in the job list
- This chip is visually distinct in amber color and is visible without clicking the row
- No non-level-setup study rows have this amber chip

---

### UT-28 — Insufficient sample marker appears when study has too few occurrences (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/studies` — `StudyResultsView` insufficient-sample marker

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A study exists that produced fewer occurrences than the configured minimum sample size (this may occur with short windows or rare setups — use the reference-window fixture and check if the sample is below threshold, or create a sim scenario likely to produce few occurrences)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Click a completed "Done" study row that you believe may have produced few occurrences (or where n is known to be below minimum)
3. Observe the distribution blocks in the results panel

**Expected Result:**
- If the study produced fewer occurrences than the minimum sample size, an amber chip reading "Insufficient sample (n = X < Y)" appears inside the relevant distribution block (where X is the actual count and Y is the minimum threshold)
- The chip is amber-colored and clearly distinct from the outcome chips
- The chip appears INSIDE the distribution block, not as a separate section

---

### UT-29 — Re-run identical: produces a new row with same setup and matching counts (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/studies` — `StudyResultsView` re-run button

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- A reference-window study with absorption_reversal + long has completed (Done)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Click a completed "Done" reference-window study row
3. In the results panel, locate and click the "Re-run identical" button
4. Observe the job list
5. Wait for the new study row to reach "Done" status
6. Click the new row to view its results
7. Compare the distribution block counts (e.g. "+1R at 60s") between the original and re-run studies

**Expected Result:**
- After step 3: a new row appears in the job list with the same source, setup, and direction as the original study
- After step 5: the new row reaches "Done" status
- After step 7: the occurrence counts in both distribution blocks (Your setup and Random-time baseline) match the original study's counts exactly — the numbers are identical because the baseline seed is re-used

---

### UT-30 — J-68 Regression sentinel: cockpit page is unchanged except Studies nav entry (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (cockpit) — `NavBar.tsx`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650` (cockpit/home page)
2. Examine the navigation bar: identify all nav items and their states
3. Observe the "Studies" nav item specifically — verify it is enabled (not greyed out)
4. Examine the main cockpit area: the chart, tape, state display, thesis panel, and all cockpit controls
5. Compare the cockpit controls, colors, and layout against prior-iteration expectations — look for any new buttons, panels, or color changes that were NOT present before

**Expected Result:**
- The "Studies" link in the navigation bar is enabled (clickable, pointer cursor, no disabled styling)
- The "Studies" link is the ONLY visible change in the navigation bar compared to the previous iteration
- The cockpit chart, tape, state display, thesis panel, and all other cockpit controls are visually identical to prior iterations — no new elements, no color changes, no new controls
- No new panels, badges, or UI elements appear on the cockpit page itself

---

### UT-31 — Journal and Cockpit pages still reachable after nav change (regression)

**Type:** regression
**Priority:** P1
**Surface:** Global nav — Cockpit and Journal links

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Click the "Cockpit" (or home) link in the top navigation bar
3. Verify the cockpit page loads without error
4. Click the "Journal" link in the top navigation bar
5. Verify the journal page loads without error

**Expected Result:**
- The Cockpit link navigates to the cockpit page at `http://localhost:3650` (or equivalent); the page loads with no error
- The Journal link navigates to `http://localhost:3650/journal` (or equivalent); the page loads with no error
- Neither the Cockpit nor Journal nav items have been disabled or changed in appearance as a result of the Studies entry being enabled

---

### UT-32 — Studies page is discoverable in exactly one click from home (ux)

**Type:** ux
**Priority:** P2
**Surface:** Global nav — discoverability

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running

**Steps:**
1. Navigate to `http://localhost:3650` (home/cockpit page)
2. Without using the browser address bar, navigate to the Studies page using only the top navigation bar
3. Count the number of clicks required

**Expected Result:**
- The "Studies" item is visible in the top navigation bar on the home page without any dropdown or expand action
- Clicking "Studies" once navigates to `/studies` — it requires exactly 1 click from home
- The "Studies" nav item has active (emerald) highlighting after navigating to `/studies`

---

### UT-33 — Never-pool: feed and config fingerprint stamps visible and distinct per study (ux)

**Type:** ux
**Priority:** P1
**Surface:** `/studies` — `StudyResultsView` honesty stamps (never-pool discipline)

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- Two completed studies exist with the same setup but different sources (e.g., one reference-window, one seeded sim)

**Steps:**
1. Navigate to `http://localhost:3650/studies`
2. Click the reference-window study row and note the Feed chip value and Config fingerprint chip value in the results header
3. Click the seeded sim study row and note the Feed chip value and Config fingerprint chip value in the results header

**Expected Result:**
- Each completed study's results panel shows its own Feed chip (e.g. "sip" for reference-window, a sim identifier for sim)
- Each completed study's results panel shows a Config fingerprint chip with a hash value
- Studies with different sources show different Feed chip values
- The fingerprint chip tooltip (on hover) shows the full hash value, confirming the stamp is a real fingerprint and not a placeholder

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Studies nav entry is active link | smoke | P1 | Global nav |
| UT-02 | Studies nav entry navigates to /studies | smoke | P1 | Global nav |
| UT-03 | /studies page loads with required structure | smoke | P1 | `/studies` |
| UT-04 | /studies empty selection state shows placeholder | smoke | P1 | `/studies` |
| UT-05 | StudyList shows "No studies yet" empty state | smoke | P1 | `/studies` |
| UT-06 | StudyList shows brief loading state on reload | smoke | P2 | `/studies` |
| UT-07 | Create study with Reference Window: happy path | happy-path | P1 | `/studies` |
| UT-08 | Create study with Seeded Sim (SIM-REVERSAL) | happy-path | P1 | `/studies` |
| UT-09 | Create study with Symbol + Past Window: fields appear | happy-path | P1 | `/studies` |
| UT-10 | Level setup shows level input and hindsight warning | validation | P1 | `/studies` |
| UT-11 | Run Study disabled when required fields missing | validation | P1 | `/studies` |
| UT-12 | Run Study button transitions to "Running…" in flight | validation | P2 | `/studies` |
| UT-13 | Run Study enabled only after level price filled | validation | P1 | `/studies` |
| UT-14 | Job list shows correct status badge colors | happy-path | P1 | `/studies` |
| UT-15 | Cancel running study: badge → Cancelled, button gone | happy-path | P1 | `/studies` |
| UT-16 | Cancelled study shows PARTIAL warning above results | happy-path | P1 | `/studies` |
| UT-17 | Failed study shows rose error message in results | error | P1 | `/studies` |
| UT-18 | Backend 422 error surfaces inline below form | error | P2 | `/studies` |
| UT-19 | Queued study shows queued-specific absence copy | ux | P2 | `/studies` |
| UT-20 | Running study shows running-specific absence copy | ux | P2 | `/studies` |
| UT-21 | Running study row shows events-processed counter | ux | P2 | `/studies` |
| UT-22 | Results: side-by-side distributions with four chips | happy-path | P1 | `/studies` |
| UT-23 | Results: occurrences table with correct columns | happy-path | P1 | `/studies` |
| UT-24 | Results: honesty stamps visible in header | happy-path | P1 | `/studies` |
| UT-25 | Results: measurement-framing line visible twice | happy-path | P1 | `/studies` |
| UT-26 | Level-break results: hindsight label and amber caption | happy-path | P1 | `/studies` |
| UT-27 | Level-break row shows amber Hindsight chip in list | happy-path | P1 | `/studies` |
| UT-28 | Insufficient sample marker in distribution block | ux | P2 | `/studies` |
| UT-29 | Re-run identical: new row with matching counts | happy-path | P1 | `/studies` |
| UT-30 | J-68: cockpit unchanged except Studies nav entry | regression | P1 | `/` (cockpit) |
| UT-31 | Journal and Cockpit pages still reachable | regression | P1 | Global nav |
| UT-32 | Studies discoverable in 1 click from home | ux | P2 | Global nav |
| UT-33 | Feed and fingerprint stamps distinct per study | ux | P1 | `/studies` |

**P1 tests must all pass for browser QA verdict to be PASS.**
