# Demo Script — goal-i_will_be_rich-iter-2

**Mode:** record
**Date:** 2026-06-02
**Frontend URL:** http://localhost:3650
**Iteration:** 2

## Highlights

### Step 01 — Open Tapeology

- **Narration:** Open Tapeology and you land on a clean cockpit that is waiting for a ticker. Nothing is invented yet — until you choose something to watch, it honestly says there is no ticker.
- **Action:** Navigate to /
- **Point out:** The centered "No ticker watched" prompt with the "Try: SIM-BUYER" hint, and the footer line reminding you this is descriptive only — not trading advice.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-2/step-01.png

### Step 03 — Watch the live tape

- **Narration:** Click Watch and the whole cockpit comes alive — six panels fill at once with real, live numbers streaming straight from the engine.
- **Action:** Click the "Watch" button
- **Point out:** Quote (bid, ask, spread, last), Recent Trades, Features, Tape State, Observations, and the Event Log all populate together — no spinner, no placeholder dashes.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-2/step-03.png

### Step 04 — The tape reads Buyer Control

- **Narration:** Give it a moment and the tape resolves to Buyer Control at high confidence. Notice the numbers climbed on their own — no page reload — arriving continuously over the live stream.
- **Action:** Wait for the page to settle
- **Point out:** Tape State reads "Buyer Control" with the confidence bar nearly full; the Features panel shows a high aggressive-buy ratio and a positive buy price impact (genuine control, not just noise); the Event Log records "Tape state changed to buyer_control".
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-2/step-04.png

### Step 07 — Honest about bad input

- **Narration:** Tapeology refuses to fake it. An unknown ticker gets a clear message and the cockpit stays calm — no crash, no blank screen, and crucially no made-up tape.
- **Action:** Click the "Watch" button
- **Point out:** A red message under the top bar explains the ticker is not known; the idle prompt returns and you can immediately try a valid ticker again.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-2/step-07.png

## Full tour (text only)

### Step 02 — Enter a ticker

- **Narration:** Type SIM-BUYER into the ticker box — the built-in scenario we will read live off the tape.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker box now reads SIM-BUYER, ready to watch.

### Step 05 — One source of truth

- **Narration:** Every number on screen is read straight from the engine — open the same ticker's data endpoint and the state, confidence, and features match exactly. There is never a second, disagreeing copy.
- **Action:** Wait for the page to settle
- **Point out:** The on-screen tape state, confidence, and feature values mirror the API readings for SIM-BUYER one for one.

### Step 06 — Try an unknown ticker

- **Narration:** Now the honesty test: type NOPE_UNKNOWN, a ticker that does not exist, and try to watch it.
- **Action:** Type "NOPE_UNKNOWN" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker box now reads NOPE_UNKNOWN.
