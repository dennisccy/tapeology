# Demo Script — goal-observation-contract-iter-7

**Mode:** record
**Date:** 2026-09-05
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Cockpit

- **Narration:** We start at the Cockpit, where traders watch live market activity. Let's open the dashboard.
- **Action:** Navigate to /
- **Point out:** The Cockpit page shows the watch controls and live chart.
- **Screenshot:** reports/demo/goal-observation-contract-iter-7/step-01.png

### Step 02 — Select Simulated data

- **Narration:** We start with simulated data, which lets us test the system without a live broker connection.
- **Action:** Click the "Simulated" button
- **Point out:** The data source selector now shows 'Simulated' selected.
- **Screenshot:** reports/demo/goal-observation-contract-iter-7/step-02.png

### Step 03 — Enter ticker and watch

- **Narration:** We'll watch SIM-BIDABS, a simulated ticker. Enter it and click Watch to start receiving observations.
- **Action:** Click "Ticker"
- **Point out:** A ticker input field appears where you can type the symbol.
- **Screenshot:** reports/demo/goal-observation-contract-iter-7/step-03.png

### Step 04 — Type the ticker symbol

- **Narration:** Let's type SIM-BIDABS, the symbol we want to observe.
- **Action:** Type "SIM-BIDABS" into "Ticker"
- **Point out:** The ticker input now contains 'SIM-BIDABS'.
- **Screenshot:** reports/demo/goal-observation-contract-iter-7/step-04.png

### Step 05 — Click Watch to start observing

- **Narration:** Now we click Watch to start receiving live observations about this ticker's market activity.
- **Action:** Click the "Watch" button
- **Point out:** The watch control starts loading, and the status changes to 'live' when ready.
- **Screenshot:** reports/demo/goal-observation-contract-iter-7/step-05.png

### Step 06 — Pause the observation

- **Narration:** Once watching is active, you can pause to freeze the observation snapshot at this exact moment—a useful way to inspect a market moment without new events changing the state.
- **Action:** Click the "Pause" button
- **Point out:** The Pause button is now visible, and clicking it freezes the observation.
- **Screenshot:** reports/demo/goal-observation-contract-iter-7/step-06.png

### Step 07 — Resume observing

- **Narration:** Resume resumes watching—the observation stays consistent, but live events flow through again.
- **Action:** Click the "Resume" button
- **Point out:** The Resume button was clicked and the live status resumes.
- **Screenshot:** reports/demo/goal-observation-contract-iter-7/step-07.png

### Step 08 — Visit Structure to see market levels

- **Narration:** The observation contract powers the entire system. Let's verify that the Structure page still works correctly, showing market levels and trade setups.
- **Action:** Navigate to /structure
- **Point out:** The Structure page loads with market level analysis.
- **Screenshot:** reports/demo/goal-observation-contract-iter-7/step-08.png
