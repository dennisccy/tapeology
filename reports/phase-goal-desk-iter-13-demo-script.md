# Demo Script — goal-desk-iter-13

**Mode:** record
**Date:** 2026-07-28
**Frontend URL:** http://localhost:3301
**Iteration:** 13

## Highlights

### Step 01 — Open the Desk page

- **Narration:** The Desk page scans about 100 well-known stocks. It ranks each one by how close it sits to a key price level, and names the exact price bar behind that measurement.
- **Action:** Navigate to /desk
- **Point out:** Today's ranked list. Each row names the exact price bar its distance was measured from.
- **Screenshot:** reports/demo/goal-desk-iter-13/step-01.png

### Step 02 — See the Desk before any top-up has run  [NEW]

- **Narration:** Refreshing the Desk's price data is called a "top-up." Before the first one is recorded, the Top-up Runs panel says so in plain words — "No top-up runs recorded yet." — with no rows and no stand-in numbers.
- **Action:** Navigate to /desk
- **Point out:** The Top-up Runs panel at the foot of the page: zero rows, and one sentence stating that nothing has been recorded yet.
- **Screenshot:** reports/demo/goal-desk-iter-13/step-02.png

### Step 03 — See every top-up run saved for good  [NEW]

- **Narration:** After three runs were recorded on that same Desk, the panel lists all three — one ordinary run, one cancelled part-way through, and one that hit a problem. Each result is saved for good, and a later run is added beside the earlier ones, never on top of them.
- **Action:** Click "[data-testid="desk-topup-runs-table"]"
- **Point out:** Three recorded runs: two that ran to the end and one cancelled after 3 of 404 pairs — each row showing its own real recorded state, not a placeholder.
- **Screenshot:** reports/demo/goal-desk-iter-13/step-03.png

### Step 04 — See exactly how each run went  [NEW]

- **Narration:** Every run's outcome is broken down clearly: how many pairs were checked, how many succeeded, and how many hit a problem.
- **Action:** Click "[data-testid="desk-topup-run-latest-detail"]"
- **Point out:** This run finished all 404 pairs attempted, with 403 fetched and 1 that could not be fetched.
- **Screenshot:** reports/demo/goal-desk-iter-13/step-04.png

### Step 05 — See the exact reason a pair failed  [NEW]

- **Narration:** When a top-up run hits a real problem, the Desk shows the exact reason. It never hides behind a vague error message.
- **Action:** Click "[data-testid="desk-topup-run-latest-failed"]"
- **Point out:** One pair could not be fetched. The real, specific reason is spelled out in full.
- **Screenshot:** reports/demo/goal-desk-iter-13/step-05.png

### Step 06 — Look back at a past scan

- **Narration:** Every past scan is saved. Opening one shows it exactly as it was recorded, never mixed with today's numbers.
- **Action:** Click "[data-testid="desk-history-row"][data-screen-date="2026-06-22"]"
- **Point out:** A note confirms this is an older, saved scan, not today's.
- **Screenshot:** reports/demo/goal-desk-iter-13/step-06.png

### Step 07 — Jump from a ranked stock into its chart

- **Narration:** Clicking any ranked stock opens that stock's own chart, already loaded for the same date.
- **Action:** Click "[data-testid="desk-screen-row"][data-symbol="AAPL"] [data-testid="desk-row-drill-in"]"
- **Point out:** The Structure page opens with AAPL's own chart and price-level table, both loaded for that date.
- **Screenshot:** reports/demo/goal-desk-iter-13/step-07.png

### Step 11 — Watch the tape settle into a read

- **Narration:** Price bars move in real time. The tape settles into a plain-English read, like "Buyer Control."
- **Action:** Click the "Watch" button
- **Point out:** The live read label sits just above the moving price bars.
- **Screenshot:** reports/demo/goal-desk-iter-13/step-11.png

### Step 15 — Load its key price levels

- **Narration:** Loading draws the stock's real price history, with its key support and resistance levels marked on top.
- **Action:** Click "[data-testid="structure-load-button"]"
- **Point out:** The chart and the level table both show a level near 300.11 — a well-known price wall for this stock.
- **Screenshot:** reports/demo/goal-desk-iter-13/step-15.png

## Full tour (text only)

### Step 08 — Move to the live tape reader

- **Narration:** The Desk sits alongside two other pages, all reachable from the same menu at the top.
- **Action:** Click the "Cockpit" link
- **Point out:** The Cockpit page opens, ready to watch a stock's price action.

### Step 09 — Choose the simulated tape

- **Narration:** You can try the reader on a made-up stock first. No live market feed is needed.
- **Action:** Click the "Simulated" button
- **Point out:** The Simulated option is now selected.

### Step 10 — Name the simulated ticker

- **Narration:** Typing a name sets up which made-up stock the tape will follow.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** The ticker field now holds the name just typed.

### Step 12 — Open the price-level map fresh

- **Narration:** The Structure page maps a stock's key support and resistance levels. This time, the symbol and date are typed in by hand.
- **Action:** Navigate to /structure
- **Point out:** An empty form, waiting for a stock symbol and a date.

### Step 13 — Choose a stock to map

- **Narration:** Typing in a stock loads its own price levels.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** The Symbol field now reads AAPL.

### Step 14 — Choose the date to look at

- **Narration:** Typing in the exact date and time to look at.
- **Action:** Type "2026-06-22T21:00:00Z" into "[data-testid="structure-as-of-input"]"
- **Point out:** The As-of field now reads the chosen date and time.
