# Demo Script — goal-rapid-microscope-iter-19

**Mode:** record
**Date:** 2026-08-20
**Frontend URL:** http://localhost:3301

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page shows your research work: data readiness, a running ledger of ideas you have tested, how they held up over time, and whether any idea graduated. Let's see it.
- **Action:** Navigate to /desk
- **Point out:** The page heading 'Playbook Signals' appears at the top. Below are seven collapsible sections showing your research state.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-19/step-01.png

### Step 02 — Expand Microscope Readiness

- **Narration:** This section shows how much data you have on hand: the symbol-dates covered, the daily minutes, and a table of past recordings with their quality score in the 'Fallback frac' column.
- **Action:** Click "[data-testid='desk-section-expand-microReadiness']"
- **Point out:** The section opens. You see a summary table of corpus totals and below it a table with columns including 'Fallback frac', showing data quality for each recording.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-19/step-02.png

### Step 03 — Expand Scout Ledger

- **Narration:** The Scout Ledger holds every quick idea you have tested: the screening results, whether each passed or failed, and integrity proof. The ledger is chain-verified so you can trust the record is complete.
- **Action:** Click "[data-testid='desk-section-expand-scoutLedger']"
- **Point out:** The section opens. You see 'Ledger chain verification:' followed by 'ok' or an error message, confirming the record is intact and unbroken.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-19/step-03.png

### Step 04 — Expand Walk-Forward

- **Narration:** This section shows how your ideas hold up when tested forward over time, fold by fold. It also has chain verification to prove the fold records are genuine and unbroken.
- **Action:** Click "[data-testid='desk-section-expand-walkForward']"
- **Point out:** The section opens. You see 'Ledger chain verification:' confirming the walk-forward record is complete.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-19/step-04.png

### Step 05 — Navigate to the Cockpit

- **Narration:** The Cockpit is your live market workspace. It shows a real-time tape of orders and quotes, watched price charts, and a control panel showing your current read of market pressure for each tracked symbol.
- **Action:** Navigate to /
- **Point out:** The Cockpit loads. You see 'No ticker watched' because we have not asked it to track any symbol yet.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-19/step-05.png

### Step 07 — Click Watch

- **Narration:** Clicking Watch activates the live tape reader for this symbol. It begins flowing market data through your pressure algorithm in real time.
- **Action:** Click the "Watch" button
- **Point out:** A panel labeled 'Buyer Control' appears, showing that the tape reader is live and has generated its first pressure reading.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-19/step-07.png

### Step 08 — Navigate to the Structure page

- **Narration:** The Structure page is a support-resistance wall map. It shows where the real price levels are on a chart—the exact points where supply or demand is so concentrated that they stand out. Enter a symbol and a date, and it computes and displays the map for that exact moment.
- **Action:** Navigate to /structure
- **Point out:** The Structure page loads. You see the heading 'Tradable Map' and fields ready for a symbol and date.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-19/step-08.png

### Step 11 — Load the structure map

- **Narration:** Click Load to compute and display the support-resistance band for this symbol and date. This is the real AAPL wall at that exact moment—the exact levels where supply and demand meet.
- **Action:** Click "[data-testid='structure-load-button']"
- **Point out:** The map appears. You see the resistance band labeled '300.11–302.2', the real wall example that has been shipped and verified in every iteration.
- **Screenshot:** reports/demo/goal-rapid-microscope-iter-19/step-11.png

## Full tour (text only)

### Step 06 — Add a ticker to watch

- **Narration:** Type a symbol name into the Ticker field. This tells the Cockpit to stream live market data for that symbol.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** The ticker field is filled and ready for the next step.

### Step 09 — Enter symbol and date

- **Narration:** Enter AAPL as the symbol and 2026-06-22 16:00:00 (Eastern Time) as the date to load the structure map for that exact moment in time.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** Both fields are filled in.

### Step 10 — Enter the as-of date

- **Narration:** This date tells the Structure page exactly when to measure the wall.
- **Action:** Type "2026-06-22 16:00:00" into "[data-testid='structure-as-of-input']"
- **Point out:** The date field is filled.
