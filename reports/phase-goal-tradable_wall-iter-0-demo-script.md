# Demo Script — goal-tradable_wall-iter-0

**Mode:** record
**Date:** 2026-07-14
**Frontend URL:** http://localhost:3301
**Iteration:** 0

## Highlights

### Step 01 — Open the cockpit

- **Narration:** Start on the home page, where you can watch any ticker's live tape.
- **Action:** Navigate to /
- **Point out:** The page opens with no ticker watched yet — the natural starting point before choosing one.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-0/step-01.png

### Step 03 — Watch the simulated buyer tape

- **Narration:** Click Watch, and the cockpit reads the live tape and settles on a state once there's enough evidence.
- **Action:** Click the "Watch" button
- **Point out:** The tape settles to "buyer_control," with an event log explaining why — rising prints and a tightening spread.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-0/step-03.png

### Step 06 — Watch the simulated seller tape

- **Narration:** Click Watch again, and this time the tape reads the other way.
- **Action:** Click the "Watch" button
- **Point out:** The state settles to "seller_control," driven by falling prints and rising seller aggression.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-0/step-06.png

### Step 07 — Check the trade journal

- **Narration:** The Journal page keeps a running record of what the cockpit has observed.
- **Action:** Navigate to /journal
- **Point out:** The Journal page loads and is ready to hold entries.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-0/step-07.png

### Step 08 — Replay past studies

- **Narration:** The Studies page lets you replay historical tape sessions to study how they played out.
- **Action:** Navigate to /studies
- **Point out:** "Replay studies" confirms the replay tools are ready to use.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-0/step-08.png

### Step 09 — Review strategy performance

- **Narration:** The Performance page tracks how each strategy has done, anchored to a fixed research configuration so results stay comparable over time.
- **Action:** Navigate to /performance
- **Point out:** The configuration fingerprint shown on screen confirms the underlying research setup hasn't drifted.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-0/step-09.png

### Step 10 — Explore price structure

- **Narration:** The Structure page shows the price-structure research tools, including the strategies registered so far for backtesting on real market bars.
- **Action:** Navigate to /structure
- **Point out:** The strategy registry confirms the research tools are present and loaded.
- **Screenshot:** reports/demo/goal-tradable_wall-iter-0/step-10.png

## Full tour (text only)

### Step 02 — Type a ticker to watch

- **Narration:** Enter SIM-BUYER, one of the app's built-in simulated tickers used to demonstrate how the tape reading works.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** The Ticker field is ready to accept a symbol.

### Step 04 — Return to the cockpit

- **Narration:** Head back to the home page to pick a different ticker.
- **Action:** Navigate to /
- **Point out:** The cockpit resets cleanly, ready for the next symbol.

### Step 05 — Type a second ticker to watch

- **Narration:** This time enter SIM-SELLER — the matching simulated ticker for seller-driven tape.
- **Action:** Type "SIM-SELLER" into the "Ticker" field
- **Point out:** The Ticker field accepts a new symbol before clicking Watch again.
