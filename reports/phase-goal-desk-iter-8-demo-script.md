# Demo Script — goal-desk-iter-8

**Mode:** record
**Date:** 2026-07-27
**Frontend URL:** http://localhost:3301
**Iteration:** 8

## Highlights

### Step 01 — Open the Desk page

- **Narration:** This page scans about a hundred well-known stocks and shows which ones sit closest to one of their own key price levels today. It also keeps a record of every past scan.
- **Action:** Navigate to /desk
- **Point out:** Today's ranked list, the stocks it had to skip, and the full history of past scans.
- **Screenshot:** reports/demo/goal-desk-iter-8/step-01.png

### Step 02 — Look at a past scan

- **Narration:** You can open any earlier scan and see it exactly as it was recorded that day.
- **Action:** Click "[data-testid="desk-history-row"][data-screen-date="2026-06-22"]"
- **Point out:** A banner makes clear you're looking at an older scan, not today's, plus an honest note on the stocks that had no price history to rank that day.
- **Screenshot:** reports/demo/goal-desk-iter-8/step-02.png

### Step 03 — Jump from a ranked stock straight into its chart

- **Narration:** Clicking anywhere on a ranked stock's row takes you straight to its price chart, already loaded for that exact day.
- **Action:** Click "[data-testid="desk-screen-row"][data-symbol="AAPL"] [data-testid="desk-row-drill-in"]"
- **Point out:** The chart opens pre-filled with the stock and date, showing its key price level.
- **Screenshot:** reports/demo/goal-desk-iter-8/step-03.png

### Step 06 — Watch the tape settle

- **Narration:** After watching for a moment, the reading settles into a clear call.
- **Action:** Click the "Watch" button
- **Point out:** The Tape State panel shows the bold read-out "Buyer Control", with live price bars, trades, and an event log all filled in.
- **Screenshot:** reports/demo/goal-desk-iter-8/step-06.png

### Step 12 — See the real chart with its key levels drawn on

- **Narration:** Switching the chart to hourly bars shows the stock's real recorded price history, with its key support and resistance levels drawn right on top.
- **Action:** Click the "1h" button
- **Point out:** Real candles, the timeframe switch, and the price-level lines are all drawn on the same chart.
- **Screenshot:** reports/demo/goal-desk-iter-8/step-12.png

### Step 13 — Open the price-level map fresh

- **Narration:** The Structure page maps a chosen stock's key support and resistance levels over its real price history.
- **Action:** Navigate to /structure
- **Point out:** A report panel plainly says whether it has been worked out yet for this page — never a blank or made-up result.
- **Screenshot:** reports/demo/goal-desk-iter-8/step-13.png

### Step 16 — Load its key price levels

- **Narration:** Loading draws the stock's real price history with its key support and resistance levels marked on top.
- **Action:** Click "[data-testid="structure-load-button"]"
- **Point out:** The level table and the chart both show a level around 300.11, a well-known price wall for this stock.
- **Screenshot:** reports/demo/goal-desk-iter-8/step-16.png

### Step 17 — Study one past price touch

- **Narration:** Clicking a past case opens a closer look at how the price behaved when it touched that level.
- **Action:** Click "[data-testid="case-studies-row"]"
- **Point out:** A drill-in panel opens showing how the price reacted, its returns afterward, and the recorded trades around it, or an honest note if none were recorded.
- **Screenshot:** reports/demo/goal-desk-iter-8/step-17.png

## Full tour (text only)

### Step 04 — Move to the live tape reader

- **Narration:** The Desk sits alongside two earlier pages, both reachable from the same menu at the top.
- **Action:** Click the "Cockpit" link
- **Point out:** The Cockpit page opens, ready to watch a stock's price action.

### Step 05 — Name a practice stock

- **Narration:** Typing in a practice ticker that always settles into a predictable pattern, so you can try the reader without needing a real market feed.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field now reads SIM-BUYER.

### Step 07 — Switch to a real recorded stock

- **Narration:** Switching to Historical mode replays a real stock's own recorded price action instead of a live practice feed.
- **Action:** Click the "Historical" button
- **Point out:** The Historical option is now selected.

### Step 08 — Name the real stock

- **Narration:** Typing in a real stock symbol to replay its recorded price history.
- **Action:** Type "AAPL" into the "Symbol search" field
- **Point out:** The symbol field now reads AAPL.

### Step 09 — Choose the day to replay

- **Narration:** Typing in the day to replay.
- **Action:** Type "22-06-2026" into the "Date" field
- **Point out:** The date field now reads 22-06-2026.

### Step 10 — Fill the trading day in one click

- **Narration:** One click fills in the whole trading day, instead of typing exact times by hand.
- **Action:** Click the "Full RTH 9:30–16:00 ET" button
- **Point out:** The start and end time fields fill in automatically.

### Step 11 — Start the replay

- **Narration:** Watching starts the replay of that real stock's real trading day.
- **Action:** Click the "Watch" button
- **Point out:** The page now shows it is watching AAPL.

### Step 14 — Choose a stock to map

- **Narration:** Typing in a stock to load its price levels.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** The Symbol field now reads AAPL.

### Step 15 — Choose the date to look at

- **Narration:** Typing in the exact date and time to look at.
- **Action:** Type "2026-06-22T21:00:00Z" into "[data-testid="structure-as-of-input"]"
- **Point out:** The As-of field now reads the chosen date and time.
