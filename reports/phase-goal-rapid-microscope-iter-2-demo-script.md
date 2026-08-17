# Demo Script — goal-rapid-microscope-iter-2

**Mode:** record
**Date:** 2026-08-17
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** We start by opening the Desk page, which is the main hub for analyzing trading data and position quality.
- **Action:** Navigate to /desk
- **Point out:** The page loads with no errors. You can see the Desk heading and various analysis sections below.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-2/step-01.png

### Step 02 — View the Microscope Readiness panel

- **Narration:** Scroll to the bottom and expand the Microscope Readiness section. This shows a summary of the tick data that the analysis engine has processed.
- **Action:** Click the element
- **Point out:** The panel displays a Corpus Totals table showing 1 distinct symbol-day and 2 datasets, plus a Legacy Tick Shards table with two rows of real PG data from the sip feed — proof that tick data is being recorded and tracked.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-2/step-02.png

### Step 03 — Verify the Referee Registry section

- **Narration:** Scroll and expand the Referee Registry section to confirm all the regression analysis sections are still working.
- **Action:** Click the element
- **Point out:** The Referee Registry expands to show a table of candidates and their configuration. This confirms the existing analysis infrastructure is intact and responsive.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-2/step-03.png

### Step 04 — Open the Cockpit for live market data

- **Narration:** Now let's open the Cockpit, which displays live market prices and trading tape. This verifies the market data pipeline is still working.
- **Action:** Navigate to /
- **Point out:** The page loads with the Tapeology header and a Ticker input field, ready for you to enter a symbol.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-2/step-04.png

### Step 05 — Enter a ticker symbol to watch

- **Narration:** Type SIM-BUYER into the Ticker field to select a symbol for analysis.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** The field accepts the ticker symbol and displays it, ready for the next action.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-2/step-05.png

### Step 06 — Start watching the live price chart

- **Narration:** Click the Watch button to begin viewing the live price chart and trading tape for the selected symbol.
- **Action:** Click the "Watch" button
- **Point out:** The page displays a live price chart with candles, volume, and tape data streaming in real-time. This confirms the cockpit's price feed and tape engine are both functioning correctly.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-2/step-06.png
