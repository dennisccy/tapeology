# Goal iter-5 — Implementation Summary

**Phase:** goal-i_will_be_rich-iter-5
**Date:** 2026-06-03
**Written by:** developer

---

## Features Implemented

- **Bid Absorption read (SIM-BIDABS):** Watching `SIM-BIDABS` now settles the cockpit on
  **Bid Absorption** — heavy selling is hitting the bid, but the bid keeps refreshing at the
  same price, so the price does not actually fall. The system says "absorption", not "sellers
  in control".
- **Ask Absorption read (SIM-ASKABS):** The mirror — watching `SIM-ASKABS` settles on **Ask
  Absorption**: heavy buying into an offer that holds, so the price stalls rather than rising.
- **The product's headline distinction, proven end-to-end:** identical high one-sided
  aggression now resolves differently based purely on whether price actually moved — to
  *control* when it moved, to *absorption* when it did not. A tape with high sell aggression
  and a real price drop is still Seller Control; the same aggression with a holding bid is Bid
  Absorption.
- **Three new feature readouts** in the Features panel: **Absorption score**, **Bid refresh
  score**, **Ask refresh score** — the numbers that justify an absorption call.
- **Absorption messages in the event log:** on an absorption read the log shows, e.g., "Large
  sell print absorbed" and "Bid refreshing at 100.00" (real values, not canned text), alongside
  the existing "Tape state changed to …" line.
- **Honest stream-status indicator:** the small status dot in the top bar now reflects what the
  engine's data stream is actually doing (connecting / live / stale / closed) instead of a
  separate client-side guess that could wrongly stay "live" after the stream ended.

---

## Changed Behavior

- **Top-bar status dot:** Previously it showed only the browser's view of the WebSocket
  connection, which could read "live" even after the underlying tape stream had closed. Now it
  shows the engine's authoritative stream status, so it tells the truth when a stream ends. The
  live dot on the buyer/seller scenarios is unaffected.
- **`SIM-BIDABS` / `SIM-ASKABS` tickers:** Previously these were known tickers that produced no
  data (the read stayed an honest "unclear"). Now they drive their full absorption scenarios.
- **Features panel:** Previously nine rows; now twelve (the three absorption readouts appended).

---

## Backend-Only Items

- None. Every new capability is visible in the cockpit (the three feature rows, the two amber
  absorption states with confidence, the absorption observations and event-log messages, and
  the canonical status dot).

---

## Incomplete Items

- **J-06 (choppy / unclear scenario):** Out of scope this iteration. `SIM-CHOP` remains a known
  ticker that produces no data, so it reads as honest "unclear" — but an *actively choppy*
  driven stream is a later iteration.
- **J-09 (Stop / un-watch control):** Out of scope. No "stop watching" button this iteration;
  the status-dot work done here is the groundwork it depends on.
- **Remaining features** `spread_change` and `liquidity_imbalance` are not built (not needed for
  absorption).

---

## Config and Environment Changes

- No new environment variables. Four new internal tuning numbers were added to the engine config
  file (`app/config.py`) so that no threshold is hard-coded in the logic: the bid/ask refresh
  floors, the "price is flat" band width, and a confidence scale for the refresh component.
  Operators do not need to set anything.

---

## Known Limitations

- **The absorption simulations are deliberately one-sided.** To make "price did not move" exact
  and unambiguous, every print in the absorption scenarios lands at one held price. This is a
  clean, deterministic teaching scenario, not a model of messy real flow — real-feed behavior is
  a later phase.
- **The "stale" status** is supported by the dot but is not yet produced by any data path (there
  is no provider-gap detector yet), so in practice the dot shows connecting / live / closed.
- **Final visual confirmation of the amber coloring** for a resolved absorption state is done by
  the automated browser test; at the build level the amber styles are confirmed present in the
  shipped stylesheet.
