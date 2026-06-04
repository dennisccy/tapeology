# Demo Script — goal-i_will_be_super_rich-iter-2

**Mode:** record
**Date:** 2026-06-04
**Frontend URL:** http://localhost:3650
**Iteration:** 2

## Highlights

### Step 01 — Open Tapeology

- **Narration:** We start on Tapeology's home screen, which opens in Simulated mode by default. The main area sits quietly idle, waiting for you to pick a ticker to watch.
- **Action:** Navigate to /
- **Point out:** The Live / Historical / Simulated switch and the ticker box across the top, with "No ticker watched" filling the main area.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-2/step-01.png

### Step 02 — Switch to Historical data

- **Narration:** One click on "Historical" turns Tapeology into a time machine — the controls for replaying a real past trading session appear right here on the same screen, no extra page to find.
- **Action:** Click the "Historical" button
- **Point out:** A symbol search box plus Date, Start time, End time, and a replay-speed picker, all revealed in place.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-2/step-02.png

### Step 03 — Search for a real symbol  [NEW]

- **Narration:** Start typing part of a symbol and Tapeology suggests real, tradable matches — the ticker on the left, the company name on the right.
- **Action:** Type "AAP" into the "Symbol search" field
- **Point out:** The live dropdown under the box: real matches such as AAPL · Apple Inc. appear as you type "AAP".
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-2/step-03.png

### Step 10 — Replay real Ford order flow  [NEW]

- **Narration:** Press Watch and the full cockpit fills with Ford's real trades and quotes for that window — read exactly the same way Tapeology reads a simulated tape.
- **Action:** Click the "Watch" button
- **Point out:** Real bid/ask/spread/last, real recent trades, the live tape state "Bid Absorption" with its confidence, and the "historical F …" label up top — all from genuine market data.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-2/step-10.png

### Step 12 — Honest answer: not tradable  [NEW]

- **Narration:** Instead of inventing numbers, Tapeology says plainly that this isn't a tradable symbol — and shows no cockpit at all.
- **Action:** Click the "Watch" button
- **Point out:** An amber panel reading "Symbol not tradable" with the phrase "not a tradable symbol" — and no fabricated tape anywhere.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-2/step-12.png

### Step 15 — Honest answer: no data  [NEW]

- **Narration:** Again Tapeology refuses to guess: with no trades in that window it simply says so, rather than drawing a fake tape.
- **Action:** Click the "Watch" button
- **Point out:** An amber "No data for that window" panel standing in place of the cockpit.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-2/step-15.png

### Step 18 — Simulated tape still reads true

- **Narration:** The simulated tape plays through the very same cockpit and is correctly read as buyers in control — proving the new real-data work didn't change how the built-in scenarios behave.
- **Action:** Click the "Watch" button
- **Point out:** The cockpit reaching "Buyer Control" with its confidence, just as it did before this iteration.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-2/step-18.png

### Step 19 — Stop watching

- **Narration:** Press Stop and the cockpit clears cleanly back to the calm idle screen, ready for the next ticker.
- **Action:** Click the "Stop" button
- **Point out:** Back to "No ticker watched" with no leftover data lingering on screen.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-2/step-19.png

## Full tour (text only)

### Step 04 — Pick a suggestion  [NEW]

- **Narration:** Click any match and it drops straight into the symbol box — or you can ignore the list entirely and just type the symbol yourself.
- **Action:** Click the "AAPL" button
- **Point out:** The symbol box now holds the symbol you picked from the list.

### Step 05 — Type the ticker to replay  [NEW]

- **Narration:** Here we just type Ford's ticker, F, by hand — free-text entry always works, with or without the dropdown.
- **Action:** Type "F" into the "Symbol search" field
- **Point out:** F sitting in the symbol box, ready to replay.

### Step 06 — Choose the past date  [NEW]

- **Narration:** Pick the calendar date of the session you want to relive.
- **Action:** Type "2026-06-02" into the "Date" field
- **Point out:** The date set to a recent trading day.

### Step 07 — Set the start time  [NEW]

- **Narration:** Set the start of the window you want to watch.
- **Action:** Type "15:00" into the "Start time" field
- **Point out:** Start time entered for the replay window.

### Step 08 — Set the end time  [NEW]

- **Narration:** And the end of the window — here a tight two-minute slice of the tape.
- **Action:** Type "15:02" into the "End time" field
- **Point out:** End time entered, defining the full replay window.

### Step 09 — Pick a replay speed  [NEW]

- **Narration:** Choose how fast to replay — 10× compresses a couple of minutes of real tape into a few seconds.
- **Action:** Type "10×" into the "Replay speed" field
- **Point out:** Replay speed set to 10×.

### Step 11 — Try a symbol that isn't real  [NEW]

- **Narration:** Now we deliberately ask for a symbol that doesn't exist as a tradable stock.
- **Action:** Type "ZZZZNOPE" into the "Symbol search" field
- **Point out:** A made-up symbol typed into the box.

### Step 13 — Back to a real symbol  [NEW]

- **Narration:** Back to Ford — but this time we'll point it at a window when the market was closed.
- **Action:** Type "F" into the "Symbol search" field
- **Point out:** F typed into the box again.

### Step 14 — Pick a closed-market day  [NEW]

- **Narration:** We choose a weekend date, when no trading happened at all.
- **Action:** Type "2026-05-31" into the "Date" field
- **Point out:** The date set to a market-closed day.

### Step 16 — Back to Simulated mode

- **Narration:** Switching back to Simulated confirms the built-in scenarios still work exactly as they always did.
- **Action:** Click the "Simulated" button
- **Point out:** The plain ticker box returns and the historical date/time controls tuck away.

### Step 17 — Watch a built-in scenario

- **Narration:** We type one of the built-in scenarios, SIM-BUYER, and press Watch.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** SIM-BUYER entered in the plain ticker box.
