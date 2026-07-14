# goal-tradable_wall-iter-2 — Implementation Summary

**Phase:** goal-tradable_wall-iter-2 (Era 5B "The Tradable Wall", J-02: the wide scan — a
case-study registry across the 12-symbol panel)
**Date:** 2026-07-14
**Written by:** developer

---

## Features Implemented

- **The touch-event scanner and case-study registry**: a new backend capability that walks through
  every one of the 12 watched symbols (AAPL, MSFT, NVDA, TSLA, AMZN, GOOGL, META, AMD, NFLX, SPY,
  QQQ, JPM), looks at every trading session in the recorded 5-minute price history, and checks each
  session's price action against that morning's tradable-wall map (built by last iteration's
  capability). Whenever price actually touches one of those walls, it records what happened next:
  did price get rejected and turn away, did it break through, or did it just chop around near the
  wall without a clear outcome? Each of these recorded "touches" also carries how much price moved
  by two later checkpoints (about one trading session later, and about three sessions later).
- **A real evidence base, not a guess**: after populating the system with fresh real price data for
  all 12 symbols, the scanner found **801 real touch events across all 12 symbols** — far more than
  the minimum bar this iteration needed to clear (15 events across at least 8 symbols). The outcomes
  are a healthy mix: 309 breakouts, 306 rejections, 186 inconclusive/choppy touches.
- **The cited example, confirmed again with this new lens**: the specific AAPL wall the project's
  own research flagged (the roughly $300–$302 resistance level that rejected price six times before
  a sharp drop) shows up in the new registry exactly as expected — logged as a "rejected" touch on
  June 22, 2026, with price meaningfully lower both one session and three sessions later.
- **Two new ways to reach this data**: a new web address (`GET /research/setups`, with optional
  filters by symbol, outcome, or conviction grade) plus a matching detail address for drilling into
  one specific event, and a matching read-only AI-tool endpoint — so a future on-screen "Case
  Studies" browser and any AI assistant querying the system will see identical numbers.
- **A one-time data-gathering step**: this iteration also fetched and stored fresh real price
  history (daily, hourly, and 5-minute candles) for all 12 watched symbols from Yahoo Finance — no
  paid data subscription needed. Previously only one symbol (AAPL) had this data on hand; now all 12
  do, which is what let the scanner find real examples across the whole panel rather than just one
  stock.

## Changed Behavior

- None. This iteration is purely additive — no existing page, endpoint, computation, or displayed
  value changed behavior. The tradable-wall map from last iteration and the underlying raw levels
  computation from earlier iterations are both confirmed byte-for-byte unchanged before and after
  this work.

## Backend-Only Items

- `GET /research/setups` (and its detail/AI-tool counterparts) — fully built and tested, but **not
  yet shown anywhere on screen**. The `/structure` page will grow a "Case Studies" browser that lets
  someone click through this registry in a later iteration (already planned); until then this
  capability is reachable only via the API/AI-tool, not through the browser.

## Incomplete Items

- None from this iteration's own scope. The plan explicitly limited this iteration to the scanning
  logic, its API, its AI-tool proxy, and the one-time data-gathering step — no on-screen page, no
  real tape/trade recording, and no new trading strategy were part of this iteration's job (those
  are separate, later iterations already named in the project roadmap).

## Config and Environment Changes

- No new environment variables and no credentials were needed (the data fetch is the same keyless
  Yahoo Finance source already in use). Five new internal tuning values were added (the list of 12
  symbols to scan, how far forward to check price after a touch, how big a move counts as a real
  breakout/rejection versus noise, how many touches to log per wall per day, and how many days of
  5-minute history to request) — these are pre-set to reasonable, documented defaults; no operator
  action is required. They do not change the site's overall configuration fingerprint, so nothing
  that depends on that fingerprint is affected.

## Known Limitations

- **The full 12-symbol scan is slow — a little under 5 minutes per request** against the
  now-fully-populated real data, because it re-examines the complete price history for every symbol
  and every trading day from scratch each time it is asked, rather than remembering the answer from
  last time. This does not affect correctness (every run produces the identical, correct answer),
  and the automated test suite runs against much smaller sample data in well under a second, but
  anyone checking this live against the real data (including the next automated check in this
  project's pipeline) needs to allow several minutes rather than expecting an instant reply. Speeding
  this up is flagged as a good candidate for a future iteration rather than something rushed in here.
- **The "what counts as a rejection vs. a breakout vs. a chop" rule and the "how far forward to
  check" checkpoints are a first, reasonable design choice**, chosen for defensible reasons (roughly
  one trading session and three trading sessions ahead, wide enough to avoid being fooled by a brief
  price wiggle) and confirmed against real price data before being locked in — not tuned afterward to
  force a particular answer. They can be adjusted later without any restructuring if they classify
  things differently than a trader would expect on other symbols or examples.
- Every recorded touch event currently has an empty placeholder where the real tape (trade-by-trade)
  reading will eventually go — that is intentionally out of scope for this iteration (it needs the
  operator's brokerage credentials, coming in the next iteration) and is clearly labeled as "not yet
  recorded" rather than missing or broken.
