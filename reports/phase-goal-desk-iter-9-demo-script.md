# Demo Script — goal-desk-iter-9

**Mode:** record
**Date:** 2026-07-27
**Frontend URL:** http://localhost:3301
**Iteration:** 9

## Highlights

### Step 01 — Open the Desk page  [NEW]

- **Narration:** This page scans about a hundred well-known stocks. It ranks them by closeness to a key price level. Every ranked row now also says how many days old that price reading is. Hovering over any row shows the exact date and time behind it.
- **Action:** Navigate to /desk
- **Point out:** A new "basis" column sits at the end of the table, showing a real date and day-count for every row. Some rows are only a few days old; others are two weeks old or more.
- **Screenshot:** reports/demo/goal-desk-iter-9/step-01.png

### Step 02 — Look at a scan from before this update  [NEW]

- **Narration:** Opening a scan recorded before this feature existed shows an honest note instead of a guess. The page says plainly that this measurement wasn't captured back then.
- **Action:** Click "[data-testid="desk-history-row"][data-screen-date="2026-06-22"]"
- **Point out:** Every row's "basis" cell reads "basis not recorded in this snapshot." It is never a blank cell or a made-up date.
- **Screenshot:** reports/demo/goal-desk-iter-9/step-02.png

### Step 03 — Confirm a row still opens its chart  [NEW]

- **Narration:** A new column was added to this row. Clicking anywhere on it — even the new "basis" text — still opens that stock's own chart.
- **Action:** Click "[data-testid="desk-screen-row"][data-symbol="AAPL"] [data-testid="desk-row-drill-in"]"
- **Point out:** The page jumps straight to the Structure chart for AAPL. Its key price levels are already loaded.
- **Screenshot:** reports/demo/goal-desk-iter-9/step-03.png

### Step 06 — Watch the tape settle

- **Narration:** After watching for a moment, the reading settles into a clear call.
- **Action:** Click the "Watch" button
- **Point out:** The Tape State panel shows the bold read-out "Buyer Control", with live price bars, trades, and an event log all filled in.
- **Screenshot:** reports/demo/goal-desk-iter-9/step-06.png

### Step 12 — See the real chart with its key levels drawn on

- **Narration:** Switching the chart to hourly bars shows the stock's real recorded price history, with its key support and resistance levels drawn right on top.
- **Action:** Click the "1h" button
- **Point out:** Real candles, the timeframe switch, and the price-level lines are all drawn on the same chart.
- **Screenshot:** reports/demo/goal-desk-iter-9/step-12.png

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
