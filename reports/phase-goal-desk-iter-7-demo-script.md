# Demo Script — goal-desk-iter-7

**Mode:** record
**Date:** 2026-07-26
**Frontend URL:** http://localhost:3301
**Iteration:** 7

## Highlights

### Step 01 — Open the Desk page

- **Narration:** This page scans about a hundred well-known stocks and shows which ones sit closest to one of their own key price levels today. It also keeps a memory of past scans.
- **Action:** Navigate to /desk
- **Point out:** The Desk page loads with its provenance details, today's ranked list, the stocks it skipped, and a history of every past scan.
- **Screenshot:** reports/demo/goal-desk-iter-7/step-01.png

### Step 02 — Look at a past scan

- **Narration:** You can click any earlier scan in the history list to see it exactly as it was recorded that day.
- **Action:** Click "[data-testid="desk-history-row"][data-screen-date="2026-06-22"]"
- **Point out:** A banner explains you're viewing an older scan, not today's.
- **Screenshot:** reports/demo/goal-desk-iter-7/step-02.png

### Step 03 — Jump from a ranked stock straight into its chart

- **Narration:** Clicking anywhere on a ranked stock's row, not just its name, takes you straight to its price chart, already loaded for that exact day. Hovering over the row also now reveals the stock's precise distance and score, a small fix from this round.
- **Action:** Click "[data-testid="desk-screen-row"][data-symbol="AAPL"] [data-testid="desk-row-band-class"]"
- **Point out:** The chart page opens already filled in with the stock and date, showing its key price band.
- **Screenshot:** reports/demo/goal-desk-iter-7/step-03.png

### Step 06 — See an honest result for a skipped stock

- **Narration:** A stock the scan couldn't rank, because there was no price history for it, can still be clicked. It opens the chart page and says so plainly, instead of faking a result.
- **Action:** Click "[data-testid="desk-skip-row"][data-symbol="ABBV"] [data-testid="desk-skip-reason"]"
- **Point out:** The chart page says plainly that no price history was recorded for this stock — no invented chart.
- **Screenshot:** reports/demo/goal-desk-iter-7/step-06.png

### Step 10 — Watch the tape settle

- **Narration:** After watching for a moment, the reading settles into a clear call.
- **Action:** Click the "Watch" button
- **Point out:** The Tape State panel shows the bold read-out "Buyer Control", with live price, trades, and an event log all filled in.
- **Screenshot:** reports/demo/goal-desk-iter-7/step-10.png

### Step 11 — Open Structure fresh

- **Narration:** The Structure page maps a chosen stock's key support and resistance levels over its real price history.
- **Action:** Navigate to /structure
- **Point out:** Below, the Edge Report panel plainly says whether it has been computed yet — never a blank or made-up result.
- **Screenshot:** reports/demo/goal-desk-iter-7/step-11.png

### Step 14 — Load its key price levels

- **Narration:** Loading draws the stock's real price history with its key support and resistance levels marked on top.
- **Action:** Click "[data-testid="structure-load-button"]"
- **Point out:** The level table and the chart both show a level around 300.11, a well-known price wall for this stock.
- **Screenshot:** reports/demo/goal-desk-iter-7/step-14.png

### Step 15 — Study one past price touch

- **Narration:** Clicking a past case opens a closer look at how the price behaved when it touched that level.
- **Action:** Click "[data-testid="case-studies-row"]"
- **Point out:** A drill-in panel opens below the table showing how the price reacted, its returns afterward, and the recorded trades around it (or an honest note if none were recorded).
- **Screenshot:** reports/demo/goal-desk-iter-7/step-15.png

## Full tour (text only)

### Step 04 — Back to the Desk

- **Narration:** Heading back to the Desk page to check what happens with a stock the scan had to skip.
- **Action:** Navigate to /desk
- **Point out:** The Desk page loads again with the same panels.

### Step 05 — Re-open that same past scan

- **Narration:** Selecting the same earlier scan again to look at one of its skipped stocks.
- **Action:** Click "[data-testid="desk-history-row"][data-screen-date="2026-06-22"]"
- **Point out:** The same "viewing an older scan" banner appears.

### Step 07 — Move to the live tape reader

- **Narration:** The Desk sits alongside two older pages, Cockpit and Structure, all reachable from the same navigation bar.
- **Action:** Click the "Cockpit" link
- **Point out:** Exactly three pages are listed: Cockpit, Structure, and Desk.

### Step 08 — Choose the practice data source

- **Narration:** The Cockpit page reads a stock's live price action. For this walk-through it uses a built-in practice feed instead of a real market feed.
- **Action:** Click the "Simulated" button
- **Point out:** The Simulated option is selected.

### Step 09 — Name the practice stock

- **Narration:** Typing in a practice ticker that always settles into a predictable pattern.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field now reads SIM-BUYER.

### Step 12 — Choose a stock to map

- **Narration:** Typing in a stock to load its price levels.
- **Action:** Type "AAPL" into the "Structure symbol" field
- **Point out:** The Symbol field now reads AAPL.

### Step 13 — Choose the date to look at

- **Narration:** Typing in the exact date and time to look at.
- **Action:** Type "2026-06-22T21:00:00Z" into "[data-testid="structure-as-of-input"]"
- **Point out:** The As-of field now reads the chosen date and time.
