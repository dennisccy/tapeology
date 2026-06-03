# Demo Script — goal-i_will_be_rich-iter-6

**Mode:** record
**Date:** 2026-06-03
**Frontend URL:** http://localhost:3650
**Iteration:** 6

## Highlights

### Step 01 — Open the tape cockpit

- **Narration:** This is Tapeology — a live read of one stock's order flow that tells you who is in control of the tape. It opens clean, with nothing watched yet, so you just type a ticker to begin.
- **Action:** Navigate to /
- **Point out:** The Tapeology header with the ticker box and the green Watch button, and the calm 'No ticker watched' idle screen — no panels populated yet.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-6/step-01.png

### Step 03 — Watch SIM-CHOP settle on "Unclear"  [NEW]

- **Narration:** We hit Watch and the cockpit fills with live data — but instead of forcing a call, it honestly reads 'Unclear' at low confidence. When the tape is genuinely choppy, the product says so rather than faking a direction. This is the honesty the whole tool is built around.
- **Action:** Click the "Watch" button
- **Point out:** The amber 'Unclear' headline, the low confidence reading (0.200), balanced buy/sell pressure near 0.50 with 0.0 price impact, and the 'Mixed or weak evidence — no clear side in control' note. No buyer, seller, or absorption call is made.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-6/step-03.png

### Step 05 — Watch SIM-BUYER announce "Buyer Control"

- **Narration:** The cockpit reads 'Buyer Control' in green and announces the change live in the event log the moment it resolves — aggressive buying is genuinely lifting the price.
- **Action:** Click the "Watch" button
- **Point out:** The green 'Buyer Control' headline with a high confidence bar, and the 'Tape state changed to buyer_control' line appearing in the Event Log — the live transition.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-6/step-05.png

### Step 07 — Watch SIM-SELLER flip to "Seller Control"

- **Narration:** The read flips to 'Seller Control' in red — sellers are pressing and the price is dropping — with its own live transition note in the log.
- **Action:** Click the "Watch" button
- **Point out:** The red 'Seller Control' headline and the 'Tape state changed to seller_control' line in the Event Log.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-6/step-07.png

### Step 09 — Watch SIM-BIDABS read "Bid Absorption"

- **Narration:** Despite a flood of selling, the price holds — so the cockpit reads 'Bid Absorption' in amber. The call rests on whether the price actually moved, not on how much aggression there was: pressure being soaked up, not control.
- **Action:** Click the "Watch" button
- **Point out:** The amber 'Bid Absorption' headline; the price holding at 100.00 while heavy sells print, and notes like 'Heavy sell volume being absorbed' / 'Bid refreshing at 100.00'.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-6/step-09.png

### Step 11 — Watch SIM-ASKABS read "Ask Absorption"

- **Narration:** Heavy buying that stalls at the ask reads as 'Ask Absorption' in amber — buyers being absorbed rather than taking control. That completes the full set of five tape situations the cockpit can recognise.
- **Action:** Click the "Watch" button
- **Point out:** The amber 'Ask Absorption' headline; the price stalling at 100.02 despite buy prints, and notes like 'Heavy buy volume being absorbed'.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-6/step-11.png

### Step 13 — Unknown ticker is refused, not faked

- **Narration:** Instead of inventing a tape, the cockpit refuses cleanly with a plain error and stays idle. It never fabricates a reading for a stock it doesn't know.
- **Action:** Click the "Watch" button
- **Point out:** The rose error line "'NOPE-XYZ' is not a known simulated ticker" under the header, and the empty cockpit — no panels and no fabricated tape state.
- **Screenshot:** reports/demo/goal-i_will_be_rich-iter-6/step-13.png

## Full tour (text only)

### Step 02 — Type the choppy sample ticker  [NEW]

- **Narration:** Let's start with the honest case. We enter SIM-CHOP — a deliberately messy, two-sided tape with no clear winner.
- **Action:** Type "SIM-CHOP" into "Ticker e.g. SIM-BUYER"
- **Point out:** SIM-CHOP typed into the ticker box, ready to watch.

### Step 04 — Switch to the buyer sample

- **Narration:** Now the opposite — a clean, decisive tape. We type SIM-BUYER into the same box.
- **Action:** Type "SIM-BUYER" into "Ticker e.g. SIM-BUYER"
- **Point out:** SIM-BUYER entered in the ticker box, replacing the previous ticker.

### Step 06 — Switch to the seller sample

- **Narration:** Next we flip to the mirror case and type SIM-SELLER.
- **Action:** Type "SIM-SELLER" into "Ticker e.g. SIM-BUYER"
- **Point out:** SIM-SELLER entered in the ticker box.

### Step 08 — Switch to the bid-absorption sample

- **Narration:** Now the product's signature call. We type SIM-BIDABS — heavy selling that meets a price which simply refuses to fall.
- **Action:** Type "SIM-BIDABS" into "Ticker e.g. SIM-BUYER"
- **Point out:** SIM-BIDABS entered in the ticker box.

### Step 10 — Switch to the ask-absorption sample

- **Narration:** The mirror of absorption. We type SIM-ASKABS — heavy buying that fails to lift the price.
- **Action:** Type "SIM-ASKABS" into "Ticker e.g. SIM-BUYER"
- **Point out:** SIM-ASKABS entered in the ticker box.

### Step 12 — Try an unknown ticker

- **Narration:** Finally, the honesty guardrail. We type a ticker the system doesn't recognise — NOPE-XYZ.
- **Action:** Type "NOPE-XYZ" into "Ticker e.g. SIM-BUYER"
- **Point out:** NOPE-XYZ entered in the ticker box.
