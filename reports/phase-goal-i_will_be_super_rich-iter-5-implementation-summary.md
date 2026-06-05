# goal-i_will_be_super_rich-iter-5 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-5
**Date:** 2026-06-05
**Written by:** developer

---

## Features Implemented

- **Resolved buy/sell side for real-data trades (J-16)**: When watching real market data (a
  historical replay, and live too), the recent-trades list now shows whether each trade was a
  **buy** or a **sell** for the large majority of prints, instead of a wall of "unknown". It does
  this by first using the published bid/ask (a trade at/above the ask is a buy, at/below the bid is
  a sell) and, when that can't decide (no quote yet, or the trade printed between the bid and ask),
  falling back to the classic **tick test**: compare the trade's price to the previous trade — a
  higher price counts as a buy, a lower price as a sell, an equal price keeps the last clear
  direction. A trade with no quote and no earlier trade to compare against still honestly reads
  "unknown" — nothing is guessed or invented.

---

## Changed Behavior

- **Recent-trades side on real historical replay**: Previously most real trades that didn't land
  exactly on the bid or ask were labeled "unknown" (on the bundled real Ford test window, 20% of
  trades — 13 of 65 — were unknown). Now those same trades are resolved to buy/sell (0 of 65
  unknown on that window). The directional features that depend on side — the buy/sell aggression
  ratios and the net aggressive volume — are correspondingly more accurate on real data.
- **Simulated scenarios are unchanged**: SIM-BUYER, SIM-SELLER, SIM-BIDABS, SIM-ASKABS, and
  SIM-CHOP still resolve to the same tape states at the same confidence as before. This was
  re-verified by the full test suite because the shared classification code was touched.

---

## Backend-Only Items

- None. This is an engine-internal accuracy improvement surfaced through the **existing**
  recent-trades panel and the existing `GET /tape/{ticker}/events` endpoint. There is no new
  endpoint and no new screen — the same "side" field is simply correct more often.

---

## Incomplete Items

- None for this slice. iter-5 was scoped to J-16 only. The remaining new journeys are explicitly
  out of scope and handled in later slices: the price/candlestick chart with tape-state markers
  (J-17/J-18), pause/resume (J-19), and the local-time historical-window picker (J-20).

---

## Config and Environment Changes

- None. No new environment variables, no config-file changes, and no new tunable numbers were
  introduced (the tick test is an exact rule with no threshold to configure).

---

## Known Limitations

- **No visible UI change**: The improvement appears automatically inside the existing recent-trades
  panel; there is no new control or layout to look at. The visible effect is simply far fewer
  "unknown" rows when replaying real historical data.
- **Authoritative proof is offline**: The accuracy gain is proven against a committed snapshot of
  **real** captured market data replayed through the engine (so it reproduces with no API keys and
  no live market). Confirming it through the live UI requires vendor credentials configured during
  QA; that run is confirmatory, not required.
- **First-trade edge case**: At the very start of a brand-new watch, if the first trade has no
  quote and no earlier trade to compare against, it correctly remains "unknown" until there is
  something to compare to. This is intended honest behavior, not a gap.
