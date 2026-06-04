# Demo Script — goal-i_will_be_super_rich-iter-1

**Mode:** record
**Date:** 2026-06-04
**Frontend URL:** http://localhost:3650
**Iteration:** 1

## Highlights

### Step 01 — Open Tapeology  [NEW]

- **Narration:** Tapeology opens straight to the tape cockpit. New this time: a Data source switch at the top lets you choose Live, Historical, or Simulated, and it starts on Simulated.
- **Action:** Navigate to /
- **Point out:** The three-way Live / Historical / Simulated switch in the top bar, with Simulated highlighted.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-1/step-01.png

### Step 03 — Watch the simulated tape

- **Narration:** Click Watch and the cockpit comes alive: the quote, recent trades, features, and event log all stream in, and the tape state reads Buyer Control.
- **Action:** Click the "Watch" button
- **Point out:** The full cockpit populated, the tape state resolved to Buyer Control, and the status dot turned green.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-1/step-03.png

### Step 04 — Switch to Live data  [NEW]

- **Narration:** Switch the source to Live. The simulated watch is torn down cleanly, and an honest 'market unavailable' pill appears, because Tapeology won't invent a market status it can't verify.
- **Action:** Click the "Live" button
- **Point out:** The amber 'market unavailable' pill, and the cockpit cleared back to idle as the old watch is dropped (no orphaned stream).
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-1/step-04.png

### Step 06 — An honest answer with no credentials  [NEW]

- **Narration:** Click Watch. Because no vendor credentials are configured, Tapeology shows a clear 'real-data provider unavailable' panel instead of a cockpit. There are no fabricated prices and no silent fall-back to the simulator.
- **Action:** Click the "Watch" button
- **Point out:** The amber 'Real-data provider unavailable' panel with a warning icon and guidance to add Alpaca credentials or switch to Simulated. No cockpit, no fake data.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-1/step-06.png

### Step 07 — Explore Historical mode  [NEW]

- **Narration:** Switch to Historical and the top bar reveals exactly the controls a replay needs: a date, a start and end time, and a replay-speed selector.
- **Action:** Click the "Historical" button
- **Point out:** The new date picker, the start and end time boxes separated by an en-dash, and the replay-speed dropdown defaulting to 1x.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-1/step-07.png

### Step 12 — Same honest answer for Historical  [NEW]

- **Narration:** Click Watch. With no credentials, Historical gives the same honest 'real-data provider unavailable' panel, never a fabricated replay.
- **Action:** Click the "Watch" button
- **Point out:** The same amber 'Real-data provider unavailable' panel, now for Historical data — still no cockpit and no invented tape.
- **Screenshot:** reports/demo/goal-i_will_be_super_rich-iter-1/step-12.png

## Full tour (text only)

### Step 02 — Enter the demo ticker

- **Narration:** With Simulated selected, type the built-in demo ticker SIM-BUYER into the ticker box.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** SIM-BUYER typed into the ticker box, ready to watch.

### Step 05 — Look up a real symbol  [NEW]

- **Narration:** In Live mode you get a symbol search box. Type a real ticker such as AAPL.
- **Action:** Type "AAPL" into the "Symbol search" field
- **Point out:** The input now reads 'Symbol e.g. AAPL' — it adapts to the chosen data source.

### Step 08 — Enter a historical symbol  [NEW]

- **Narration:** Type a symbol to replay — say MSFT.
- **Action:** Type "MSFT" into the "Symbol search" field
- **Point out:** MSFT entered in the symbol box for the historical replay window.

### Step 09 — Pick a replay date  [NEW]

- **Narration:** Choose the session date you want to replay.
- **Action:** Type "2026-06-03" into the "Date" field
- **Point out:** A past date selected in the date picker.

### Step 10 — Set the start time  [NEW]

- **Narration:** Set when the replay window should begin.
- **Action:** Type "09:30" into the "Start time" field
- **Point out:** The start time set to 09:30.

### Step 11 — Set the end time  [NEW]

- **Narration:** And when the replay window should end.
- **Action:** Type "10:30" into the "End time" field
- **Point out:** The end time set to 10:30, closing a one-hour replay window.
