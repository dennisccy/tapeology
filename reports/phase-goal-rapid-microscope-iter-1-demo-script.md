# Demo Script — goal-rapid-microscope-iter-1

**Mode:** record
**Date:** 2026-08-17
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Cockpit homepage

- **Narration:** Let's start with the live cockpit. This is where you watch real market tape and live charts.
- **Action:** Navigate to /
- **Point out:** The cockpit page with the Ticker field, Tape State, Quote, and live candle chart.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-1/step-01.png

### Step 02 — Watch a symbol and connect live tape

- **Narration:** Type a ticker symbol into the Ticker field and click Watch to connect live market data.
- **Action:** Type "SIM-BUYER" into "Symbol"
- **Point out:** The Tape State showing 'Buyer Control', the Quote panel with real prices, and the live 10-second candle chart.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-1/step-02.png

### Step 03 — Connect to the tape

- **Narration:** Click the Watch button to connect live tape.
- **Action:** Click the "Watch" button
- **Point out:** The Tape State should change to 'Buyer Control' and the Quote panel should populate with Bid/Ask prices.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-1/step-03.png

### Step 04 — Navigate to Structure

- **Narration:** Now let's look at the Structure page to examine support and resistance bands.
- **Action:** Navigate to /structure
- **Point out:** The Structure page with the Symbol field, as-of date picker, and the Tradable Map.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-1/step-04.png

### Step 05 — Load structure for a symbol

- **Narration:** Enter a symbol and select an as-of date to analyze its support and resistance levels.
- **Action:** Type "AAPL" into "Symbol"
- **Point out:** The Tradable Map table showing quality-scored bands with Class ratings and member counts.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-1/step-05.png

### Step 07 — Load the structure

- **Narration:** Click Load to compute the Tradable Map for this symbol and date.
- **Action:** Click the "Load" button
- **Point out:** The Tradable Map table populated with real quality-scored bands.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-1/step-07.png

### Step 08 — Navigate to the Desk

- **Narration:** Open the Desk page to see the Microscope Readiness panel, the era's first honest inventory of what research data exists.
- **Action:** Navigate to /desk
- **Point out:** The Desk page with all sections including the new Microscope Readiness panel at the bottom.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-1/step-08.png

### Step 09 — Expand the Microscope Readiness section  [NEW]

- **Narration:** Click to expand the Microscope Readiness section and see the corpus inventory — how many symbol-days of tick data exist and whether they meet the research floor.
- **Action:** Click "[data-testid='desk-section-expand-microReadiness']"
- **Point out:** The Corpus Totals showing the distinct symbol-days, distinct datasets, and session-equivalents; the Legacy Tick Shards table; the Pilot-Study Floors table showing which floors are met.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-1/step-09.png

## Full tour (text only)

### Step 06 — Set the analysis date

- **Narration:** Pick the date for the historical analysis.
- **Action:** Type "2026-06-22 17:00:00" into the "as-of" field
- **Point out:** The as-of date field populated.
