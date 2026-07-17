# Demo Script — goal-fast_wall-iter-0

**Mode:** record
**Date:** 2026-07-17
**Frontend URL:** http://localhost:3301
**Iteration:** 0

## Highlights

### Step 01 — Open the home page

- **Narration:** This is the home page, where a simulated market tape plays out live so you can see the underlying engine at work.
- **Action:** Navigate to /
- **Point out:** A ticker box invites you to try SIM-BUYER, one of the built-in demo scenarios.
- **Screenshot:** reports/demo/goal-fast_wall-iter-0/step-01.png

### Step 03 — Watch the tape settle into Buyer Control

- **Narration:** Click Watch and the simulator replays the scripted tape. Within a few seconds it settles into Buyer Control, complete with a confidence score.
- **Action:** Click the "Watch" button
- **Point out:** The Tape State panel reads Buyer Control, and the event log confirms the tape state changed to buyer_control.
- **Screenshot:** reports/demo/goal-fast_wall-iter-0/step-03.png

### Step 06 — Watch the tape settle into Seller Control

- **Narration:** Click Watch again, and this scenario settles into Seller Control instead — proof the simulator can reproduce both sides of the tape.
- **Action:** Click the "Watch" button
- **Point out:** The Tape State panel now reads Seller Control, with its own confidence score and a matching log entry.
- **Screenshot:** reports/demo/goal-fast_wall-iter-0/step-06.png

### Step 07 — Review the trading journal

- **Narration:** Every simulated session is logged as a thesis in the journal, so you can look back later at what was watched and why.
- **Action:** Navigate to /journal
- **Point out:** The journal list shows the SIM-BUYER and SIM-SELLER entries that were just recorded.
- **Screenshot:** reports/demo/goal-fast_wall-iter-0/step-07.png

### Step 08 — Browse replay studies

- **Narration:** The Studies page holds journaled measurements from tape replays — always labeled as measurements, never as a trading signal.
- **Action:** Navigate to /studies
- **Point out:** The "Replay studies" heading and the reference-window and seeded-sim source options are visible.
- **Screenshot:** reports/demo/goal-fast_wall-iter-0/step-08.png

### Step 09 — Check the performance ledger

- **Narration:** Finally, the Performance page shows the simulated profit ledger for the founding baseline strategy.
- **Action:** Navigate to /performance
- **Point out:** A banner makes clear every figure is simulated — assumed fees and slippage — not indicative of live results.
- **Screenshot:** reports/demo/goal-fast_wall-iter-0/step-09.png

## Full tour (text only)

### Step 02 — Type in a simulated ticker

- **Narration:** Enter SIM-BUYER — a scripted scenario built to show what buyer-controlled tape looks like.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field now shows SIM-BUYER.

### Step 04 — Stop the run

- **Narration:** Stop the simulation so we can try a second scenario.
- **Action:** Click the "Stop" button
- **Point out:** The controls reset, ready for a new ticker.

### Step 05 — Try a second scenario

- **Narration:** This time, enter SIM-SELLER to see the opposite side of the tape.
- **Action:** Type "SIM-SELLER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field now shows SIM-SELLER.
