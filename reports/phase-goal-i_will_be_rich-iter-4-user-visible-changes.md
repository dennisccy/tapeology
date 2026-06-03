# Phase goal-i_will_be_rich-iter-4 — User-Visible Changes

**Phase:** goal-i_will_be_rich-iter-4
**Date:** 2026-06-03
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now watch the **down-tape** scenario: type `SIM-SELLER` into the ticker input on `/`, click **Watch**, and the cockpit resolves to a real **"Seller Control"** read within a few seconds. Before this iteration the same ticker sat at "unclear / warming up" forever (it emitted no events), so this is a brand-new working outcome even though no screen or control was added.
- Users can now see the cockpit identify the down-tape with the same fidelity it already had for the up-tape, rendered in the **rose/red** color language (sell-side / price falling) instead of the buyer's green.
- Users can now read seller-specific evidence: the observations list shows "Seller aggression increasing", "Price falling on sell prints", and "Spread stable and narrow", and the event log records "Tape state changed to seller_control" at the moment the read flips.
- Users can confirm the product's core honesty promise on the sell side: "Seller Control" appears only when aggressive selling is **actually pushing the price down** (negative `sell_price_impact`), not merely when sell volume is high. Heavy selling with no price drop stays "unclear".

---

## What Changed in the Visible UI

No structural UI change — the single `/` cockpit, its panels, layout, and controls are all unchanged. The change is in the **content** the existing components now render when `SIM-SELLER` is watched:

- The **Tape State panel** (`TapeStatePanel`) headline now reads **"Seller Control"** in rose (`text-rose-400`), and its confidence-bar fill renders rose (`bg-rose-500`) — the first on-screen render of the dynamic `stateColor("seller_control")` path. Previously, for this ticker, the panel showed only "Unclear" in slate.
- The **Features panel** (`FeaturesPanel`) now shows a high `aggressive_sell_ratio` and a **negative** `sell_price_impact`, with the negative impact cell colored rose via `impactColor`.
- The **Observations panel** (`ObservationsPanel`) now lists the three seller messages instead of being empty/cold-start.
- The **Event Log panel** (`EventLogPanel`) now contains the line "Tape state changed to seller_control".
- All of the above update live over the WebSocket with no page reload as the rolling window fills.

---

## What Old Behavior Changed

- **Watching `SIM-SELLER`**: previously resolved nothing — it stayed at the cold-start "unclear" read indefinitely. Now it deterministically settles on "Seller Control" with confidence above the reasonable threshold within ~4–5 seconds.
- **Watching `SIM-BUYER` (regression-sensitive, must be re-verified, NOT changed by design)**: still settles on "Buyer Control" with the same confidence and the same green color. The new seller logic runs alongside the buyer logic and does not alter the buyer or unclear reads (developer-verified; the buyer tests are the regression guard). Testers must re-confirm this on the live UI.

---

## Not Visible Yet

- The other three reserved simulated tickers — `SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP` — are known tickers (Watch returns 200) but still emit no events and remain "unclear". Their tape states (bid/ask absorption, choppy) are deferred to later journeys (J-04/J-05).
- There is still no "stop watching" / `DELETE /watch` control in the UI (deferred to J-09).
- The top-bar stream-status dot is still driven by the client connection status, not the engine's canonical `snapshot.stream_status` — this consolidation remains deferred (belongs to the no-data / teardown journeys).
