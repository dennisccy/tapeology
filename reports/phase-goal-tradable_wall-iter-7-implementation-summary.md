# goal-tradable_wall-iter-7 — Implementation Summary

**Phase:** goal-tradable_wall-iter-7
**Date:** 2026-07-15
**Written by:** developer

---

## Features Implemented

- **Tradable bands now show up on your main trading screen, not just on the Structure page.** When
  you watch a stock in Simulated or Historical mode, the price chart now draws the same "tradable
  wall" bands (support/resistance zones) that the Structure page already showed — right on the chart
  you're actually watching, next to the buy/sell-pressure markers.
- **A small text banner appears when price is at a wall and the tape agrees.** When the last traded
  price sits inside one of those bands AND the live tape reading matches what would be expected at
  that wall (a rejection or a breakout), a small gray banner appears describing the situation in
  plain language — for example "Inside R-band 300.05–300.17 (class A) · tape: Ask Absorption
  (rejection) · measured history: edge report." It never tells you to buy or sell, and it never
  predicts what happens next — it only states what is currently true and points you to the edge
  report for the measured history.
- **Honest "no map" message for made-up test tickers.** If you watch one of the built-in simulated
  tickers (which don't correspond to a real stock), the chart still works normally, but instead of a
  fabricated band it shows a small "No tradable map for SIM-BUYER" note.

## Changed Behavior

- **The cockpit price chart** (the one on the main `/` page): previously showed only candles + tape
  markers + your own declared-thesis lines. It now ALSO shows band lines and, at the right moment, a
  descriptive banner. Nothing about the existing candles/markers/thesis lines changed.
- **Live mode** (watching a real, currently-trading stock with no time delay): unchanged. The price
  chart — and therefore the new bands/banner — still does not appear in Live mode, exactly as before.

None if no existing behavior changed. — *(N/A — see above; nothing else changed.)*

---

## Backend-Only Items

None. Every piece of data this feature uses (the bands, the strategy's rejection/breakout rules, the
tape reading) was already being served by the backend from earlier work — this iteration only wired
the existing cockpit screen up to read it.

---

## Incomplete Items

- **Seeing the banner actually pop up during a real credentialed replay was not personally witnessed
  in this build session.** I confirmed the bands draw correctly on a real historical replay of the
  exact date/stock this project has been using as its test case (AAPL, 22 June 2026), and confirmed
  the underlying "does the tape agree" logic is correct and reads only from the server (never
  invented on-screen), but the live price didn't happen to cross into a band at the exact moment the
  tape also matched during my observation window. This is expected to be confirmed by the next
  verification step (browser QA), which can watch for longer or target the exact right moment.

---

## Config and Environment Changes

None. No new environment variable, no config file change, no migration.

---

## Known Limitations

- **No automated on-screen (browser) test suite exists for this app's frontend** — this has been true
  since the project started. Frontend correctness is checked by (a) a type-checker that catches most
  coding mistakes, (b) a set of automated checks that inspect the actual page code, and (c) manually
  driving a real browser against the real running app (done extensively this iteration, including a
  real credentialed historical replay).
- **A design fix was needed and applied during this build.** The initial plan called for the band
  overlay to always use "right now" as its reference date. While testing with a real historical
  replay, this turned out to show TODAY's bands even when replaying a PAST day — which made no sense
  next to the old price action being replayed. This was corrected so the overlay instead uses the
  date of whatever session is actually being watched (already-available data, no new fetch, no
  backend change). This is called out prominently in the developer handoff for the reviewer to
  double-check.
- **The banner's wording adds a small "(rejection)" or "(breakthrough)" note** beyond the single
  example sentence quoted in the project's planning documents. This is a minor wording choice, not a
  new capability — it uses only vocabulary the server already provides.
