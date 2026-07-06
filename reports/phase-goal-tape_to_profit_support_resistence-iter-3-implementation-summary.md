# goal-tape_to_profit_support_resistence-iter-3 — Implementation Summary

**Phase:** goal-tape_to_profit_support_resistence-iter-3
**Date:** 2026-07-06
**Written by:** developer

---

## Features Implemented

- **Grouping price levels that line up across timeframes into "confluence zones"**: Building on the
  previous iteration's individual support/resistance price levels, the system now looks at all of a
  symbol's levels together — across every timeframe (hourly, daily, weekly, and so on) — and groups
  together any that sit close to the same price into a single "zone." A zone that only ever shows up
  on one timeframe stays its own separate thing; a zone where several different timeframes agree on
  roughly the same price is grouped as one.
- **Each zone gets a conviction grade (A / B / C)**: Every zone is graded honestly based on how many
  *different* timeframes agree on it, and whether at least one of those timeframes is a longer-term
  one (daily, weekly, or monthly). A zone confirmed by several timeframes including a longer-term
  one earns the top grade, "A." A zone confirmed by two different timeframes earns "B." A zone that
  only shows up within a single timeframe (for example, two nearby turning points both found on the
  hourly chart) still gets reported — honestly, as the lowest grade, "C" — rather than being hidden.
  Nothing is ever upgraded or invented to make a zone look stronger than it is.
- **Each zone also carries a combined strength score**: The individual strength numbers of every
  level inside a zone are added together into one combined score for the zone, so a zone's overall
  weight-of-evidence is visible alongside its letter grade.
- **No hindsight allowed, extended to zones and grades**: The same "no looking into the future"
  guarantee proven for individual levels last iteration now also covers zones and their grades — a
  price bar recorded after the moment you're asking about can never change a zone or its grade,
  proven directly by comparing the answer with and without that later bar physically present in
  storage.
- **Always the same answer for the same question**: Asking the same "zones as of this time"
  question twice in a row, or from two separate copies of the tool, always returns the identical
  result, down to the byte — the same guarantee individual levels already had.
- **Honest "nothing to show" messages, extended**: A symbol with levels but none of them close
  enough together to form a zone now honestly reports an empty zone list — never a fabricated zone,
  and never confused with "this symbol has no price history at all" (which remains its own,
  separate honest answer from last iteration).
- **Available everywhere levels already were**: The zone and grade information rides on the exact
  same web address and the exact same AI-assistant (MCP) tool that already served individual levels
  — there is no new web address or new tool to learn, and the machine-tool answer stays
  word-for-word identical to the website's own answer, as with every other feature in this project.

## Changed Behavior

- None beyond the addition itself. Every existing feature — the live trading-tape cockpit, the
  research journal, the studies page, the performance page, and last iteration's individual
  support/resistance levels — behaves exactly as before (confirmed: zero files under the website's
  frontend code were touched, and the full backend test suite, including the dedicated
  "nothing changed" checks, stayed green).

## Backend-Only Items

- The new zone/grade information rides on `GET /research/levels` (the same machine endpoint from
  last iteration) plus the matching MCP tool — there is still no page or panel in the website that
  displays it. That remains intentionally out of scope for this step; a future "levels" screen
  showing zones and grades visually is possible later, but this iteration is purely the underlying
  calculation.

## Incomplete Items

- **A real trading strategy that reacts to graded zones, and honestly measuring whether it would
  have made money**: This iteration only produces the zones and their letter grades. The next
  planned steps — building a strategy that enters a trade when price reaches a graded zone and the
  live tape confirms a direction, sizing that trade and its risk based on the zone's grade, and then
  honestly measuring (on saved historical data, never live money) whether that strategy would have
  beaten doing nothing — are **not** part of this iteration and remain to be built.
- **No screen to view zones/grades yet**: an operator can see zone and grade information only
  through the API/MCP tools right now, not through a page in the website.

## Config and Environment Changes

- No new environment variables were added. Three new *internal* settings now exist in the system's
  one central settings file (all with sensible starting defaults, clearly labelled as starting
  points rather than proven-optimal values): how close in price two levels from different
  timeframes must be to count as the "same" zone, how many different timeframes a zone needs to earn
  the top "A" grade, and the (lower) bar for the middle "B" grade.
- No database migration was needed and no new external account/service is introduced — this feature
  only re-groups price levels the system already computes from bar data it already has saved.

## Known Limitations

- **The "how close counts as the same zone" and "how many timeframes for each grade" numbers are
  reasonable starting points, not scientifically validated values.** They were chosen to be sensible
  and are documented as such (the same honesty standard already applied to similar starting-point
  settings elsewhere in the project) — they have not been tested against real trading outcomes yet.
- **The one real, committed sample of saved price history only covers two timeframes (hourly and
  daily), so it can never by itself produce a top-grade "A" zone** (an A-grade zone needs a third
  timeframe to agree). This is an honest, expected consequence of how much sample data exists today,
  not a bug — a top-grade zone IS proven to work correctly using a purpose-built practice example
  with three timeframes, and separately, the real two-timeframe sample data honestly produces
  several middle- and lowest-grade zones exactly as it should.
- **Zones don't yet say whether a price level is acting as "support" or "resistance"** — that
  depends on which direction price is approaching from and what the live tape says at the moment,
  which is explicitly the NEXT planned step, not this one.
- **If a saved price-bar file for a symbol's only timeframe ever becomes corrupted, the system still
  reports "no price history for this symbol" rather than a more specific "this symbol's data is
  damaged" message** — unchanged from last iteration; this was a conscious decision to leave alone
  for now (not something newly discovered), and the existing corruption-detection safeguard still
  catches and reports the damage separately elsewhere.
- **The trading strategy, its risk sizing, and honest profit measurement against graded zones remain
  unbuilt, as planned** — this iteration is purely the "group levels into graded zones" building
  block those later steps will consume.
- **No screen in the website to look at zones/grades directly** — machine-only (web API + MCP
  tool), as planned for this step.
