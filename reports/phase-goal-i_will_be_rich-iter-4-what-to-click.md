# Phase goal-i_will_be_rich-iter-4 — What to Click (Operator Verification Guide)

**Phase:** goal-i_will_be_rich-iter-4
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3650`
- Backend running (the cockpit streams from it over WebSocket)
- No login or seed data required — the simulated tickers (`SIM-SELLER`, `SIM-BUYER`) are built in

---

## Verification Steps

1. Open `http://localhost:3650/` in your browser.
   - **Expect:** The **Tapeology** header loads with a ticker input (placeholder **Ticker e.g. SIM-BUYER**) and a green **Watch** button. Top-right shows the word **idle**. No red error text.

2. Click the ticker input, type `SIM-SELLER`, then click the green **Watch** button.
   - **Expect:** The top-right status word changes **connecting → live** (green dot), and the header shows **Watching SIM-SELLER**.

3. Wait about 5 seconds for the warm-up to finish (the amber "Warming up…" note disappears).
   - **Expect:** The **Tape State** headline reads **Seller Control** in **rose/red** text (not green, not grey). The **Confidence** line shows a number **≥ 0.600**.

4. Look at the **Features** panel.
   - **Expect:** **Aggressive sell ratio** is high (≥ 0.600) and **Sell price impact** is a **negative** number shown in rose/red.

5. Look at the **Observations** and **Event Log** panels.
   - **Expect:** Observations lists **Seller aggression increasing**, **Price falling on sell prints**, **Spread stable and narrow**. The Event Log (newest first) contains **Tape state changed to seller_control**.

6. Watch the **Confidence** number/bar for a few more seconds — do NOT refresh.
   - **Expect:** The value updates on its own (climbs as data streams in) with no page reload — confirming the live WebSocket feed.

7. Refresh the page (F5), type `SIM-BUYER`, click **Watch**, wait ~5 seconds.
   - **Expect:** Headline reads **Buyer Control** in **green** at **Confidence ≥ 0.600**, **Buy price impact** is positive. This is the regression check — the seller change must not have broken the buyer read.

8. Refresh the page (F5), type `NOPE123`, click **Watch**.
   - **Expect:** A rose error line appears under the header and **no** tape-state read is shown — the app refuses to fabricate a snapshot for an unknown ticker.

---

## What "Working Correctly" Looks Like

- `SIM-SELLER` settles on a **rose "Seller Control"** headline with a **negative Sell price impact**, three seller observations, and a `seller_control` event-log line.
- `SIM-BUYER` still settles on a **green "Buyer Control"** headline (no regression).
- An unknown ticker shows an error and **no** invented read.

## Common Issues

- **Stays "Unclear" / "Warming up" forever for SIM-SELLER:** the backend `SIM-SELLER` provider may not be running this build — confirm the backend restarted after this iteration. (Reserved sims `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP` are *supposed* to stay Unclear — only `SIM-SELLER` and `SIM-BUYER` resolve.)
- **Headline is green or grey instead of rose for SIM-SELLER:** the state being emitted isn't `seller_control` — check the Event Log for the `seller_control` transition line and the backend `/tape/SIM-SELLER/state`.
- **Blank page / status stuck on "connecting":** backend or WebSocket is down — confirm the backend is up and `NEXT_PUBLIC_API_URL` points at it.
