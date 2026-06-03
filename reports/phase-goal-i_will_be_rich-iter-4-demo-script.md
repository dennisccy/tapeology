# Demo Script — goal-i_will_be_rich-iter-4

**Mode:** record
**Date:** 2026-06-03
**Frontend URL:** http://localhost:3650
**Iteration:** 4

## Highlights

### Step 01 — Open the live tape cockpit

- **Narration:** Tapeology opens to a single live cockpit that watches one stock at a time. Before you pick a stock it sits quietly at idle, with no invented numbers, just a prompt to start watching.
- **Action:** Navigate to /
- **Point out:** The ticker box and green Watch button in the header, the 'idle' status in the top-right, and the empty 'No ticker watched' state.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-4/step-01.png

### Step 03 — Sellers in control, shown in rose  [NEW]

- **Narration:** Click Watch and the cockpit fills itself live and settles on 'Seller Control' — the first time the product reads a down-tape. It only makes this call because aggressive selling is genuinely pushing the price down, not merely because sell volume is high.
- **Action:** Click the "Watch" button
- **Point out:** The rose 'Seller Control' headline with high confidence, a high Aggressive sell ratio, a negative Sell price impact, the three seller observations, and 'Tape state changed to seller_control' in the Event Log.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-4/step-03.png

### Step 06 — Buyers in control, still shown in green

- **Narration:** Click Watch and the cockpit settles on 'Buyer Control' in green — the up-tape reading is untouched by the new seller logic. The same screen now speaks both directions in its own color: rose for sellers, green for buyers.
- **Action:** Click the "Watch" button
- **Point out:** The green 'Buyer Control' headline, a positive Buy price impact, and 'Tape state changed to buyer_control' in the Event Log — the buyer read is intact.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-4/step-06.png

### Step 09 — Unknown stocks are refused, never faked

- **Narration:** Click Watch and the cockpit refuses politely: it shows a clear error and reads nothing at all, rather than inventing a fake tape state to look busy. No data is ever fabricated.
- **Action:** Click the "Watch" button
- **Point out:** The rose error line under the header and the cockpit staying empty — no made-up 'control' reading for a stock it doesn't know.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-4/step-09.png

## Full tour (text only)

### Step 02 — Enter the down-tape sample stock  [NEW]

- **Narration:** Let's start with the brand-new ability this round adds: reading a market where sellers are in charge. Type the built-in down-tape sample, SIM-SELLER, into the ticker box.
- **Action:** Type "SIM-SELLER" into the "Ticker" field
- **Point out:** SIM-SELLER typed into the ticker box, ready to watch.

### Step 04 — Back to a fresh cockpit

- **Narration:** Now let's confirm the older up-tape reading still works exactly as before. We reload to a clean cockpit first.
- **Action:** Navigate to /
- **Point out:** The cockpit returns to its empty 'No ticker watched' state, ready for the next stock.

### Step 05 — Enter the up-tape sample stock

- **Narration:** This time we'll watch the up-tape sample, SIM-BUYER, where aggressive buyers are lifting the price.
- **Action:** Type "SIM-BUYER" into the "Ticker" field
- **Point out:** SIM-BUYER typed into the ticker box.

### Step 07 — Back to a fresh cockpit

- **Narration:** One last check — the product's honesty promise. Let's reset and try a stock the system doesn't recognise.
- **Action:** Navigate to /
- **Point out:** A clean, empty cockpit again.

### Step 08 — Enter an unknown ticker

- **Narration:** Type a made-up ticker, NOPE123, that isn't one of the built-in sample stocks.
- **Action:** Type "NOPE123" into the "Ticker" field
- **Point out:** NOPE123 entered in the ticker box.
