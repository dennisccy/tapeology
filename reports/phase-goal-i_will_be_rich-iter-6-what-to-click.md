# Phase N — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_rich-iter-6
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running and reachable (cockpit needs the live stream)
- No login required
- For step 7 (live transition check): a freshly restarted backend with no prior watch

---

## Verification Steps

<!-- The headline new capability: watching SIM-CHOP produces a warmed, honest "Unclear" read. -->

1. Open `http://localhost:3650/` in your browser
   - **Expect:** The "Tapeology" header loads with a ticker input (placeholder "Ticker e.g. SIM-BUYER") and a green "Watch" button. No error page.

2. Type `SIM-CHOP` into the ticker input and click the green "Watch" button
   - **Expect:** The header shows "Watching SIM-CHOP". Within ~10 seconds the "Tape State" panel headline reads **"Unclear"** in amber and Confidence reads **0.200** (not 0.100).

3. Look at the "Tape State" headline and the "Observations" panel for SIM-CHOP
   - **Expect:** The headline says **"Unclear"** — NOT "Buyer Control", "Seller Control", "Bid Absorption", or "Ask Absorption". Observations show an honest non-call like "Mixed or weak evidence — no clear side in control".

4. Look at the "Features" panel for SIM-CHOP
   - **Expect:** `aggressive_buy_ratio` and `aggressive_sell_ratio` both show < 0.60 (≈ 0.50), `average_spread` shows > 0.06, and `buy_price_impact` / `sell_price_impact` both show **0.0**.

5. Look at the "Recent Trades" panel and the scenario badge in the header
   - **Expect:** Every trade price reads exactly **100.00** with mixed buy/sell/unknown sides; the header badge reads `scenario: unclear_chop`.

6. Look at the "Event Log" panel for SIM-CHOP (do not reload)
   - **Expect:** **No** "Tape state changed to …" line appears — the honest absence of a fabricated transition (cold-start unclear → warmed unclear is not a state change).

7. Restart the backend, reload `http://localhost:3650/`, type `SIM-BUYER`, click "Watch" (first watch), and watch the Event Log without reloading
   - **Expect:** A line **"Tape state changed to buyer_control"** appears **live**; the Tape State headline reads "Buyer Control" in emerald. (Confirms the live cold-start transition, J-07.)

8. Type `SIM-SELLER` into the input and click "Watch"
   - **Expect:** The Tape State headline reads **"Seller Control"** in rose — the four resolved states are unregressed.

9. Type `NOPE-XYZ` into the input and click "Watch"
   - **Expect:** A rose error line appears under the header (`'NOPE-XYZ' could not be watched`). No panels fabricate a tape state.

---

## What "Working Correctly" Looks Like

- Watching `SIM-CHOP` produces a warmed amber **"Unclear"** at confidence **0.200** — a genuine honest non-call, not a silent cold start and not a manufactured directional read.
- The four decisive/absorption states (`SIM-BUYER`, `SIM-SELLER`, `SIM-BIDABS`, `SIM-ASKABS`) still resolve correctly with their original colors.
- The complete five-state taxonomy is reachable from the single ticker input.

## Common Issues

- **Tape State stays at confidence 0.100 / "Warming up…" never clears for SIM-CHOP**: The driven chop stream is not flowing — confirm the backend was restarted with this iteration's `simulated.py` and that the connection dot reads "live".
- **Blank page / no panels populate**: Check the backend is running and reachable (the cockpit needs the WebSocket stream).
- **SIM-CHOP shows a decisive headline (Buyer/Seller/Absorption)**: This is a failure — the chop tape must read "Unclear". Re-check the classifier/config were not altered.
- **No "Tape state changed to …" line on SIM-BUYER cold start**: Make sure the backend was freshly restarted and `SIM-BUYER` was the FIRST watch — the transition only fires on a genuine cold→resolved change.
