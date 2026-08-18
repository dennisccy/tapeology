# Demo Script — goal-rapid-microscope-iter-7

**Mode:** record
**Date:** 2026-08-18
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page loads with all sections in place. This regression pass verifies that backend changes to the data pipeline don't break the UI.
- **Action:** Navigate to /desk
- **Point out:** The Playbook Signals heading is visible; scroll down to see all 10 collapsible sections.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-7/step-01.png

### Step 02 — Expand Microscope Readiness to verify corpus data

- **Narration:** The Microscope Readiness section shows the fixture rig's real data: exactly 1 symbol-day and 2 datasets, both PG symbols from June 9, 2026.
- **Action:** Click "[data-testid='desk-section-expand-microReadiness']"
- **Point out:** The Corpus Totals table shows 'Distinct symbol-days: 1' and 'Distinct datasets: 2'; the Legacy Tick Shards table lists 2 PG rows, both with 'hand_assigned' provenance and 'exploratory' exposure state.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-7/step-02.png

### Step 03 — Open the Cockpit page

- **Narration:** The Cockpit is the live trading watchlist and chart. It shows no ticker by default.
- **Action:** Navigate to /
- **Point out:** The text 'No ticker watched' appears, confirming the empty state.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-7/step-03.png

### Step 04 — Watch a ticker to verify live tape still works

- **Narration:** Type SIM-BUYER into the Ticker field and click Watch. The live tape rendering pipeline is unaffected by this iteration's backend changes.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** After clicking Watch, 'Buyer Control' appears, confirming the watch flow completes without error.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-7/step-04.png

### Step 05 — Click Watch to activate the ticker

- **Narration:** Clicking Watch confirms the cockpit's tape engine responds correctly.
- **Action:** Click the "Watch" button
- **Point out:** The text 'Buyer Control' appears, indicating the ticker watch completed successfully.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-7/step-05.png

### Step 06 — Open the Structure page to check the Tradable Map

- **Narration:** The Structure page computes support/resistance bands from historical bar data. This page's data pipeline is independent of this iteration's trade/quote storage changes.
- **Action:** Navigate to /structure
- **Point out:** The 'Tradable Map' heading is visible on page load.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-7/step-06.png

### Step 07 — Load AAPL's Tradable Map as of June 22, 2026

- **Narration:** Fill in AAPL and the as-of date (2026-06-22 17:00:00 ET), then click Load. The band computation is byte-identical — this verifies the bar-store and structure engine remain unaffected.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** The text '300.11–302.2' appears, the pinned real support/resistance band for AAPL on that date. This exact band has been verified across iterations.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-7/step-07.png

### Step 08 — Fill the as-of date and load the structure

- **Narration:** Enter the target date in the as-of field, then click Load to compute the Tradable Map.
- **Action:** Type "2026-06-22 17:00:00" into "[data-testid='structure-as-of-input']"
- **Point out:** The band '300.11–302.2' confirms the structure engine byte-compatibility.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-7/step-08.png

### Step 09 — Click Load to compute the structure

- **Narration:** Trigger the structure computation.
- **Action:** Click "[data-testid='structure-load-button']"
- **Point out:** The expected band '300.11–302.2' appears.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-7/step-09.png

## Full tour (text only)

### Step 10 — Return to Desk and expand Playbook Evidence

- **Narration:** Back on the Desk page, the Playbook Evidence section reads real, pre-computed playbook signals from the fixture dataset.
- **Action:** Navigate to /desk
- **Point out:** When the section expands, 'Built from signature:' is visible, confirming a real playbook is loaded.

### Step 11 — Expand Playbook Evidence section

- **Narration:** Open the Playbook Evidence section to verify it renders real signal data.
- **Action:** Click "[data-testid='desk-section-expand-playbookEvidence']"
- **Point out:** 'Built from signature:' appears.

### Step 12 — Enter a date in the Playbook Evidence filter

- **Narration:** Type 2026-06-22 into the date field to filter the signals for that day.
- **Action:** Type "2026-06-22" into "[data-testid='desk-playbook-date-input']"
- **Point out:** The text 'recorded signals, none hidden' appears, confirming the full, unfiltered signal set is served for the selected date.

### Step 13 — Expand Referee Registry to verify the frozen fingerprint

- **Narration:** The Referee Registry section displays the configuration fingerprint. This frozen value proves the computation engine's byte-identity.
- **Action:** Click "[data-testid='desk-section-expand-refereeRegistry']"
- **Point out:** The text 'config fingerprint 08e471b10130e1e2' appears, exactly as expected.

### Step 14 — Verify Referee Adjudications honest-empty state

- **Narration:** The Referee Adjudications section is intentionally empty — no hypotheses are registered yet. This is the correct state, not an error.
- **Action:** Click "[data-testid='desk-section-expand-refereeAdjudications']"
- **Point out:** The text 'No hypotheses registered' appears.

### Step 15 — Verify Referee Runs honest-empty state

- **Narration:** The Referee Runs section also shows an honest empty state — no evaluation runs have been recorded yet.
- **Action:** Click "[data-testid='desk-section-expand-refereeRuns']"
- **Point out:** The text 'No evaluation runs recorded yet.' appears.
