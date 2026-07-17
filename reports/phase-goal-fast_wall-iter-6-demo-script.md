# Demo Script — goal-fast_wall-iter-6

**Mode:** record
**Date:** 2026-07-17
**Frontend URL:** http://localhost:3301
**Iteration:** 6

## Highlights

### Step 01 — Open the Cockpit

- **Narration:** This is Tapeology's Cockpit — the home screen where a trader watches a simulated market tape play out live. There's nothing to sign into; it's ready right away.
- **Action:** Navigate to /
- **Point out:** A ticker box invites you to try SIM-BUYER, one of the built-in demo scenarios.
- **Screenshot:** reports/demo/goal-fast_wall-iter-6/step-01.png

### Step 03 — Watch the tape settle into Buyer Control

- **Narration:** Click Watch, and the simulator replays the scripted tape. Within a few seconds it settles into Buyer Control.
- **Action:** Click the "Watch" button
- **Point out:** The Tape State panel reads buyer_control, confirming the scenario played out as scripted.
- **Screenshot:** reports/demo/goal-fast_wall-iter-6/step-03.png

### Step 06 — Watch it settle the other way — Seller Control

- **Narration:** Click Watch again, and this time the tape settles into Seller Control — the simulator reliably reproduces either side on demand.
- **Action:** Click the "Watch" button
- **Point out:** The Tape State panel now reads seller_control.
- **Screenshot:** reports/demo/goal-fast_wall-iter-6/step-06.png

### Step 07 — Review the trading journal

- **Narration:** Every simulated session gets logged as a thesis in the journal, so a trader can look back later at what was watched and why.
- **Action:** Navigate to /journal
- **Point out:** The journal list shows the SIM-BUYER entry that was just recorded.
- **Screenshot:** reports/demo/goal-fast_wall-iter-6/step-07.png

### Step 08 — Browse replay studies

- **Narration:** The Studies page holds journaled measurements from tape replays — always labeled as measurements, never as a trading signal.
- **Action:** Navigate to /studies
- **Point out:** The "Replay studies" heading and its source options are visible.
- **Screenshot:** reports/demo/goal-fast_wall-iter-6/step-08.png

### Step 09 — Check the performance ledger

- **Narration:** The Performance page shows the simulated profit ledger for the founding baseline strategy.
- **Action:** Navigate to /performance
- **Point out:** A banner makes clear every figure is simulated — assumed fees and slippage — never a claim about live results.
- **Screenshot:** reports/demo/goal-fast_wall-iter-6/step-09.png

### Step 10 — Open Structure — the price-research page

- **Narration:** Now to Structure, the page with Tapeology's price-level research tools: tradable price bands, case studies of past price reactions, and a deeper price-comparison report. This page just wrapped up several rounds of work making sure it always loads quickly, even right after the server restarts.
- **Action:** Navigate to /structure
- **Point out:** The Tradable Map panel loads right away, inviting you to choose a symbol and a time to see its level map. Case Studies and the Edge Report sit further down the page, both loading in promptly too.
- **Screenshot:** reports/demo/goal-fast_wall-iter-6/step-10.png

### Step 11 — An honest answer, with a button ready when someone wants it

- **Narration:** Scroll down to the Edge Report panel — the page's deepest calculation. It never runs itself in the background; it waits for a person to ask for it.
- **Action:** Click the "Edge Report" heading
- **Point out:** A calm amber message reads "Edge report not computed yet.", with a "Compute edge report" button underneath it — a person can click it anytime to run the calculation on demand; we won't trigger it in this quick tour, since a real run can take a while over the full trading-data history.
- **Screenshot:** reports/demo/goal-fast_wall-iter-6/step-11.png

## Full tour (text only)

### Step 02 — Type in a simulated ticker

- **Narration:** Enter SIM-BUYER — a scripted scenario built to show what buyer-controlled tape looks like.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field now shows SIM-BUYER.

### Step 04 — Stop and try the opposite scenario

- **Narration:** Stop the tape, ready to try its mirror-image scenario.
- **Action:** Click the "Stop" button
- **Point out:** The Watch button becomes available again for a new ticker.

### Step 05 — Type in the seller scenario

- **Narration:** This time, enter SIM-SELLER — the scripted scenario for seller-controlled tape.
- **Action:** Type "SIM-SELLER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field now shows SIM-SELLER.
