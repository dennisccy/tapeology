# Demo Script — goal-i_will_be_rich-iter-5

**Mode:** record
**Date:** 2026-06-03
**Frontend URL:** http://localhost:3650
**Iteration:** 5

## Highlights

### Step 01 — Open the tape cockpit

- **Narration:** This is Tapeology's single-screen cockpit for reading one stock's live order flow. Top-left is the wordmark, the center is where you type a ticker and press Watch, and a status dot top-right honestly tracks whether the stream is live or closed.
- **Action:** Navigate to /
- **Point out:** The 'idle' status and the 'No ticker watched' empty state — nothing is being watched yet.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-5/step-01.png

### Step 03 — Buyers are in control

- **Narration:** Press Watch and the cockpit fills with a live read — quote, recent trades, named measurements, observations and an event log — and calls 'Buyer Control' in green with a confidence score, because the aggressive buying is actually moving the price up.
- **Action:** Click the "Watch" button
- **Point out:** The green 'Buyer Control' headline with its confidence bar, and all six panels populated live without any page reload.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-5/step-03.png

### Step 05 — Sellers are in control

- **Narration:** The cockpit recognises sellers are in control and shows 'Seller Control' in red — but only because the selling is genuinely driving the price lower.
- **Action:** Click the "Watch" button
- **Point out:** The red 'Seller Control' headline; the price is actually falling on the sell prints, which is what earns the directional call.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-5/step-05.png

### Step 07 — Bid Absorption, not Seller Control  [NEW]

- **Narration:** Because the price holds despite the selling, Tapeology calls 'Bid Absorption' in amber — heavy selling is being quietly absorbed, not winning. Reading price impact over raw aggression is the whole reason this product exists.
- **Action:** Click the "Watch" button
- **Point out:** The amber 'Bid Absorption' headline; the new Absorption score / Bid refresh score / Ask refresh score rows in Features; and the event-log lines 'Large sell print absorbed' and 'Bid refreshing at 100.00'.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-5/step-07.png

### Step 09 — Ask Absorption, not Buyer Control  [NEW]

- **Narration:** The ask holds and the price stalls instead of rising, so the call is 'Ask Absorption' in amber — heavy buying being absorbed rather than lifting the tape.
- **Action:** Click the "Watch" button
- **Point out:** The amber 'Ask Absorption' headline and the elevated Ask refresh score that justifies the call.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-5/step-09.png

### Step 11 — It refuses to fabricate data

- **Narration:** Instead of inventing a reading, Tapeology shows a clear error and stays idle — it never fabricates a tape state for a stock it doesn't know.
- **Action:** Click the "Watch" button
- **Point out:** The red 'is not a known simulated ticker' message, with the status still 'idle' and no fake panels populated.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-5/step-11.png

## Full tour (text only)

### Step 02 — Type the buyer-driven sample

- **Narration:** We start with the built-in sample stock SIM-BUYER, where aggressive buying is genuinely lifting the price.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field now reads SIM-BUYER, ready to watch.

### Step 04 — Now the seller-driven sample

- **Narration:** Next we watch SIM-SELLER, the mirror case where heavy selling is pushing the price down.
- **Action:** Type "SIM-SELLER" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field now reads SIM-SELLER.

### Step 06 — The same heavy selling — absorbed  [NEW]

- **Narration:** Now the headline new read. SIM-BIDABS has the very same heavy selling as SIM-SELLER, but here the bid keeps refreshing and the price refuses to fall.
- **Action:** Type "SIM-BIDABS" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field now reads SIM-BIDABS.

### Step 08 — The buy-side mirror  [NEW]

- **Narration:** SIM-ASKABS is the mirror case: heavy aggressive buying into an offer that holds firm.
- **Action:** Type "SIM-ASKABS" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field now reads SIM-ASKABS.

### Step 10 — Try an unknown ticker

- **Narration:** Finally, a trust check: we type a ticker the system doesn't recognise.
- **Action:** Type "NOPE" into "Ticker e.g. SIM-BUYER"
- **Point out:** The ticker field reads NOPE.
