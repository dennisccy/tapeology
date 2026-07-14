# goal-tradable_wall-iter-1 — Implementation Summary

**Phase:** goal-tradable_wall-iter-1 (Era 5B "The Tradable Wall", J-01: the tradable level map)
**Date:** 2026-07-14
**Written by:** developer

---

## Features Implemented

- **The tradable level map**: a new backend capability that takes a symbol's raw support/resistance
  levels (which today can number in the thousands for a heavily-traded stock like AAPL) and
  distills them down to at most 10 price "bands" total — the handful of price zones actually worth
  marking on a chart. Each band shows its price range, whether it's a support or resistance level,
  a quality score, how many underlying levels back it up, whether it sits on a psychologically
  "round" price (like $300), and an inherited conviction grade (A/B/C) where one applies.
- **Morning-markup discipline**: the map for any given day is always built using only data that was
  fully available before that trading day started — never a peek at data from later in the day or
  from later days. This mirrors how a real trader marks up their charts before the market opens.
  Weekends and market holidays are handled automatically (the map simply uses whichever trading day
  actually closed last, whatever that was).
- **Verified on the real, cited example — including the full multi-timeframe data**: using AAPL's
  actual price history, requesting the map "as of" June 22, 2026 correctly builds it from data
  through June 18 (June 19 was a market holiday) and produces a resistance band spanning roughly
  $300.23–$302.25 — which contains the real $300.48 and $302.07 rejection highs the project's own
  research documented, is flagged as sitting on the round $300 level, and ranks as the **single best
  resistance band** by quality score. This now holds against the complete real data set (daily plus
  the hourly/4-hour/5-minute series together — roughly 1,800 raw levels), not only the trimmed
  daily-only test data. A first attempt ranked this wall correctly on the daily-only test data but
  **buried it 7th** once the minute-level data was included, because the score was adding up every
  short-timeframe "touch" — so sheer intraday noise near the current price outscored the real
  multi-day wall. The fix (see Known Limitations) makes the score count only the *daily* touch
  history for this factor, which is what the project's own research brief specified; the wall's
  daily bars rejected that price 39 times — the highest of any band — so it now ranks first.
- **A new way to reach this data**: a new web address (`GET /research/tradability`) and a matching
  read-only AI-tool endpoint both serve this same map, so both the future on-screen chart and any
  AI assistant querying the system see identical numbers.

## Changed Behavior

- None. This iteration is purely additive — no existing endpoint, computation, or displayed value
  changed behavior. The existing raw levels page/endpoint (era 4/5's `/research/levels`) is
  confirmed byte-for-byte unchanged before and after this work, both in automated tests and in a
  live check against a running server.

## Backend-Only Items

- `GET /research/tradability` and its AI-tool counterpart — fully built and tested, but **not yet
  shown anywhere on screen**. The `/structure` page will grow a "Tradable Map" view that renders
  this data in a later iteration (already planned as J-05); until then this capability is reachable
  only via the API/AI-tool, not through the browser.

## Incomplete Items

- None from this iteration's own scope. The plan explicitly limited this iteration to the backend
  map computation, its API, and its AI-tool proxy — no on-screen page, no scanner, no tape
  recording, and no new trading strategy were part of this iteration's job (those are separate,
  later iterations already named in the project roadmap).

## Config and Environment Changes

- No new environment variables. Five new internal tuning values were added (how many bands to keep
  per side, how wide a price band is, how the quality score is weighted, and what counts as a
  "round" price) — these are pre-set to reasonable defaults chosen and checked against real AAPL
  data; no operator action is required. They do not change the site's overall configuration
  fingerprint, so nothing that depends on that fingerprint is affected.

## Known Limitations

- The "quality score" weighting (how much round numbers, recent touches, timeframe variety, and
  daily touch history count toward a band's ranking) is a first, reasonable design choice — now
  validated against the FULL real AAPL data (all timeframes together), not just the trimmed daily
  test data — but still not a value tuned from live trading feedback. The one factor labelled "touch
  history" deliberately counts only *daily-bar* touches (the project's research brief calls for
  "daily touch count"); this is what keeps a genuine multi-day wall ranked above the far more
  numerous but shallow minute-by-minute touches near the current price. The weights can be adjusted
  later without any code restructuring if they rank things differently than a trader would expect on
  other symbols.
- **A known, deliberately-deferred data-completeness nicety** (advisory, no effect on any result):
  when the map is built for a given day, it currently uses the prior trading day's daily bar but
  not that same prior day's own minute/hour bars (it stops at the prior day's opening timestamp).
  Strictly, "data through the prior session's close" could include those intraday bars too. This was
  measured to change **nothing** about the produced map — every band's price range, ranking, and
  score is identical with or without them, because the ranking is driven by daily touches (already
  fully included). It was left as-is this round because the code that decides "which data is visible
  for a given day" is the most safety-critical part of the no-lookahead guarantee, and the current
  behavior errs on the safe side (it can only ever *exclude* valid data, never leak future data).
  A safe way to include those bars is documented in the developer handoff for a future iteration
  that needs them.
- While building this, an early version of the "which data is visible for a given day" logic had a
  subtle flaw: on two back-to-back trading days (the normal case — most days), it could
  occasionally let a sliver of the *next* day's data quietly influence the map. This was caught by
  a dedicated stress test before shipping and fixed; the fix was independently re-verified against
  the real AAPL example, which was unaffected either way (that example has a market-holiday gap
  that happened to hide the issue). No incorrect output ever reached a test assertion or a
  live-verified example.
