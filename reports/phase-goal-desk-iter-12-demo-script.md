# Demo Script — goal-desk-iter-12

**Mode:** record
**Date:** 2026-07-28
**Frontend URL:** http://localhost:3301
**Iteration:** 12

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page scans about 100 well-known stocks. It ranks each one by how close it sits to a key price level.
- **Action:** Navigate to /desk
- **Point out:** Today's ranked list, with a fresh price reading for every row.
- **Screenshot:** reports/demo/goal-desk-iter-12/step-01.png

### Step 02 — See every top-up run kept on record  [NEW]

- **Narration:** Refreshing a stock's price data is called a "top-up." The very first run starts this list from nothing. Every run since then is saved here for good.
- **Action:** Click "desk-topup-runs-table"
- **Point out:** A running history of top-ups. Each row shows its date, result, and how many stocks it reached.
- **Screenshot:** reports/demo/goal-desk-iter-12/step-02.png

### Step 03 — See exactly why one stock could not be updated  [NEW]

- **Narration:** The latest run's full result is kept in detail. That includes the exact reason for any stock it could not update.
- **Action:** Click "desk-topup-run-latest-detail"
- **Point out:** The plain reason recorded for the one stock that failed to update, right next to the rest of the result.
- **Screenshot:** reports/demo/goal-desk-iter-12/step-03.png

### Step 04 — Look back at a past scan

- **Narration:** Every past scan is saved. Opening one shows it exactly as it was recorded, never mixed with today's numbers.
- **Action:** Click "[data-testid="desk-history-row"][data-screen-date="2026-06-22"]"
- **Point out:** A note confirming this is an older, saved scan, not today's.
- **Screenshot:** reports/demo/goal-desk-iter-12/step-04.png

### Step 05 — Jump from a ranked stock into its chart

- **Narration:** Clicking any ranked stock opens that stock's own chart, already loaded for the same day.
- **Action:** Click "desk-screen-row"
- **Point out:** The Structure page opens with that stock's own chart and price-level table, both loaded for 2026-06-22.
- **Screenshot:** reports/demo/goal-desk-iter-12/step-05.png

### Step 09 — Watch the tape settle into a read

- **Narration:** Price bars move in real time. The tape settles into a plain-English read, like "Buyer Control."
- **Action:** Click the "Watch" button
- **Point out:** The live read label above the moving price bars.
- **Screenshot:** reports/demo/goal-desk-iter-12/step-09.png

### Step 13 — Load its key price levels

- **Narration:** Loading draws the stock's real price history with its key support and resistance levels marked on top.
- **Action:** Click "structure-load-button"
- **Point out:** The chart and the level table both show a level near 300.11 — a well-known price wall for this stock.
- **Screenshot:** reports/demo/goal-desk-iter-12/step-13.png

## Full tour (text only)

### Step 06 — Move to the live tape reader

- **Narration:** The Desk sits alongside two other pages, all reachable from the same menu at the top.
- **Action:** Click the "Cockpit" link
- **Point out:** The Cockpit page opens, ready to watch a stock's price action.

### Step 07 — Choose the simulated tape

- **Narration:** You can try the reader on a made-up stock first. No live market feed is needed.
- **Action:** Click the "Simulated" button
- **Point out:** The Simulated option is now selected.

### Step 08 — Name the simulated ticker

- **Narration:** Typing a name sets up which made-up stock the tape will follow.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** The ticker field now holds the name just typed.

### Step 10 — Open the price-level map fresh

- **Narration:** The Structure page maps a stock's key support and resistance levels. This time, the symbol and date are typed in by hand.
- **Action:** Navigate to /structure
- **Point out:** An empty form, waiting for a stock symbol and a date.

### Step 11 — Choose a stock to map

- **Narration:** Typing in a stock loads its own price levels.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** The Symbol field now reads AAPL.

### Step 12 — Choose the date to look at

- **Narration:** Typing in the exact date and time to look at.
- **Action:** Type "2026-06-22T21:00:00Z" into "structure-as-of-input"
- **Point out:** The As-of field now reads the chosen date and time.
