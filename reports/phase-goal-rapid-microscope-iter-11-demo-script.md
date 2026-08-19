# Demo Script — goal-rapid-microscope-iter-11

**Mode:** record
**Date:** 2026-08-19
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Visit the Cockpit homepage

- **Narration:** The Cockpit page shows the live price chart with candlestick data and a market tape panel that updates in real time.
- **Action:** Navigate to /
- **Point out:** The chart renders candlesticks and the tape panel displays live bid, ask, and volume information from the simulated market feed.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-11/step-01.png

### Step 02 — Navigate to the Structure page

- **Narration:** The Structure page displays the Tradable Map chart and tools for comparing different datasets and strategy results.
- **Action:** Navigate to /structure
- **Point out:** The Tradable Map shows support and resistance levels, and the Comparison panel below provides dataset selection and analysis tools.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-11/step-02.png

### Step 03 — Open the Dataset dropdown in the Comparison panel

- **Narration:** The dataset selector allows you to choose which recorded data to compare and analyze.
- **Action:** Click "[data-testid="comparison-dataset-select"]"
- **Point out:** The dropdown opens to reveal available datasets, each showing the symbol, data split type, and a unique identifier.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-11/step-03.png

### Step 04 — View the Edge Report comparison results

- **Narration:** The Edge Report displays a comparison of strategy results, or indicates if the analysis has not yet been computed.
- **Action:** Navigate to /structure
- **Point out:** The panel shows either a table of comparison metrics or an honest 'Edge report not computed yet' message with a Compute button.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-11/step-04.png

### Step 05 — Open the Desk page

- **Narration:** The Desk page brings together multiple research sections, with Microscope Readiness showing your recorded tape datasets.
- **Action:** Navigate to /desk
- **Point out:** The page contains various analysis panels; the Microscope Readiness section near the bottom displays recorded datasets with their metadata.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-11/step-05.png

### Step 06 — Examine the Legacy Tick Shards table in Microscope Readiness

- **Narration:** The shard table lists each recorded tape dataset with its symbol, date, checksum, and current status.
- **Action:** Click "[data-testid="micro-readiness-shards-table"]"
- **Point out:** Each row displays the Symbol, Session Date, Checksum, and exposure state (exploratory or sealed) for a recorded tape shard.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-11/step-06.png

### Step 07 — Return to Cockpit and confirm navigation

- **Narration:** The navigation bar connects all three main pages and properly highlights the active section.
- **Action:** Navigate to /
- **Point out:** All navigation links (Cockpit, Structure, Desk) are responsive, and the active link highlights to show which page you are viewing.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-11/step-07.png
