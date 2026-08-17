# Demo Script — goal-rapid-microscope-iter-6

**Mode:** record
**Date:** 2026-08-17
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Playbook Signals page

- **Narration:** Let's start by confirming the main Playbook Signals page loads without errors. This is our baseline check.
- **Action:** Navigate to /desk
- **Point out:** The Playbook Signals heading is visible at the top, and the page has fully loaded.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-6/step-01.png

### Step 02 — Check the Microscope Readiness section

- **Narration:** Next, we'll scroll down and open the Microscope Readiness section at the bottom of the page to see the corpus summary tables.
- **Action:** Click the "Microscope Readiness" button
- **Point out:** After expanding, you should see the Corpus Totals table and the Legacy Tick Shards data, confirming the product still has access to its diagnostic datasets.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-6/step-02.png

### Step 03 — Visit the Cockpit page

- **Narration:** Now let's check the Cockpit dashboard. We'll verify it loads and shows the empty state before a ticker is watched.
- **Action:** Navigate to /
- **Point out:** The Cockpit page is ready, and you should see the text 'No ticker watched' showing the empty state.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-6/step-03.png

### Step 04 — Watch a test ticker in the Cockpit

- **Narration:** Let's watch a ticker to confirm the real-time quote and tape features still work. We'll use the SIM-BUYER symbol.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** After watching, the page should show 'Buyer Control' confirming the simulation data is flowing and the watch flow is operational.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-6/step-04.png

### Step 06 — Open the Structure page

- **Narration:** Let's check the Structure page to see the Tradable Map feature. This shows the support and resistance bands.
- **Action:** Navigate to /structure
- **Point out:** The Tradable Map heading should appear, showing the page is ready to load structure data.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-6/step-06.png

### Step 07 — Load a specific Tradable Map

- **Narration:** We'll load the S/R bands for AAPL as of June 22, 2026, which is a key data point for our testing.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** The band range '300.11–302.2' should appear after loading, confirming the structure engine is computing correctly.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-6/step-07.png

## Full tour (text only)

### Step 05 — Confirm the watch is active

- **Narration:** Click the Watch button to activate the ticker watch.
- **Action:** Click the "Watch" button
- **Point out:** You should see 'Buyer Control' appear, confirming the watch is working and live data is streaming.

### Step 08 — Set the date for the structure lookup

- **Narration:** Now we'll set the date to June 22, 2026, 5 PM ET, to match our reference data.
- **Action:** Type "2026-06-22 17:00:00" into "[data-testid="structure-as-of-input"]"
- **Point out:** The as-of date field should accept this timestamp.

### Step 09 — Load the structure data

- **Narration:** Click the Load button to retrieve the Tradable Map for these parameters.
- **Action:** Click "[data-testid="structure-load-button"]"
- **Point out:** The support-resistance band should appear, showing the product is correctly computing structure levels.

### Step 10 — Return to Playbook Signals

- **Narration:** Let's go back to the Desk page to verify the Playbook Evidence section and other core surfaces.
- **Action:** Navigate to /desk
- **Point out:** We're back on the Desk page with the Playbook Signals heading visible.

### Step 11 — Open the Playbook Evidence section

- **Narration:** We'll open the Playbook Evidence section to confirm it's rendering real signals from our recorded playbook.
- **Action:** Click "[data-testid="desk-section-expand-playbookEvidence"]"
- **Point out:** The section should expand and show 'Built from signature:' text, indicating real playbook data is being served.

### Step 12 — Filter Playbook Evidence by date

- **Narration:** Let's filter the playbook signals to June 22, 2026, to see the real signals for that date.
- **Action:** Type "2026-06-22" into "[data-testid="desk-playbook-date-input"]"
- **Point out:** After entering the date, the text 'recorded signals, none hidden' should appear, confirming the filter is working.

### Step 13 — Check the Referee Registry

- **Narration:** Now let's open the Referee Registry section to confirm the configuration fingerprint is frozen.
- **Action:** Click "[data-testid="desk-section-expand-refereeRegistry"]"
- **Point out:** The section should show 'config fingerprint 08e471b10130e1e2', confirming that the frozen configuration foundation is in place.

### Step 14 — Verify Referee Adjudications is empty

- **Narration:** Let's check the Referee Adjudications section to confirm there are no hypotheses registered yet.
- **Action:** Click "[data-testid="desk-section-expand-refereeAdjudications"]"
- **Point out:** This section should show 'No hypotheses registered', which is the correct honest-empty state.

### Step 15 — Verify Referee Runs is empty

- **Narration:** Finally, let's check the Referee Runs section to confirm there are no evaluation runs yet.
- **Action:** Click "[data-testid="desk-section-expand-refereeRuns"]"
- **Point out:** This section should show 'No evaluation runs recorded yet.', which is the correct honest-empty state for a fresh configuration.
