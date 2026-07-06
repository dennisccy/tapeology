# goal-tape_to_profit_support_resistence-iter-2 — Implementation Summary

**Phase:** goal-tape_to_profit_support_resistence-iter-2
**Date:** 2026-07-06
**Written by:** developer

---

## Features Implemented

- **Finding support/resistance price levels from saved bar data**: Given a stock symbol and a
  point in time, the system can now look at the price-bar history saved for that symbol (from the
  previous iteration) and work out where the meaningful "support" and "resistance" price levels
  are — the price points where the market has previously turned, or where a prior day/week/month's
  high, low, or closing price sits. This is the first time the product has ever produced this kind
  of structural price-level information; until now it only stored raw bars.
- **Each level comes with a strength score**: Every level the system finds is labelled with which
  calendar timeframe it came from (e.g. hourly vs daily), how it was derived (a market-turning
  point vs a prior period's high/low/close), how many times price has come close to that exact
  level, and an overall "strength" number — longer timeframes and more touches both make a level
  stronger. All of these numbers come from one central, documented settings file — nothing is
  hard-coded or invented on the fly.
- **No hindsight allowed**: If you ask "what were the levels at 2pm yesterday," the answer only
  ever uses price bars up through 2pm yesterday — bars recorded afterward (even if they already
  exist in storage) can never sneak into that answer. This was proven directly: the same question
  asked against a data store that has the "future" bars in it, and against one that has had those
  future bars physically removed, gives byte-for-byte the identical answer.
- **Always the same answer for the same question**: Asking the same "levels as of this time"
  question twice in a row — or from two completely separate copies of the tool — always returns
  the identical result, down to the byte.
- **Honest "nothing to show" messages**: If you ask about a symbol that has never had any price
  history recorded at all, you get a clearly different answer than if you ask about a symbol that
  DOES have history but simply has no notable price levels yet — the system never quietly returns
  the same blank-looking answer for two different reasons.
- **A machine-readable version of all of the above**: The same levels information is also
  available through the project's MCP (AI-assistant) tool interface, word-for-word identical to
  what a human would see through the web API.

## Changed Behavior

- None. This is a purely additive capability — nothing that existed before this iteration behaves
  differently. The live cockpit, the journal, the studies, and the performance page are all
  unchanged (confirmed: zero files under the website's frontend code were touched), and the
  existing bar-recording feature from the previous iteration works exactly as before.

## Backend-Only Items

- `GET /research/levels` — computing and reading support/resistance levels — exists only as a
  machine endpoint (web API + the MCP tool) this iteration. There is no new page or panel in the
  website yet; that is intentionally out of scope for this step (a future "levels" screen is
  possible later, but this iteration is purely the underlying data-foundation calculation).

## Incomplete Items

- **Grouping levels together and grading their conviction, and everything after that**: this
  iteration only finds individual price levels. The next planned steps — clustering levels that
  line up across several timeframes into "confluence zones" and grading each zone's conviction
  (A/B/C), building a trading strategy that reacts when price reaches a graded zone, and honestly
  measuring whether that strategy would have made money — are **not** part of this iteration and
  remain to be built.
- **No screen to view levels yet**: an operator can fetch levels only through the API/MCP tools
  right now, not through a page in the website.

## Config and Environment Changes

- No new environment variables were added. Three new *internal* settings now exist in the
  system's one central settings file (all with sensible starting defaults, and all clearly
  labelled as starting points rather than proven-optimal values): how many neighbouring price bars
  must confirm a turning point, how close a price must come to a level to count as "touching" it,
  and how much extra weight each calendar timeframe (hourly, daily, weekly, etc.) gets when scoring
  a level's strength.
- No database migration was needed and no new external account/service is introduced — this
  feature only reads price-bar data the system already has saved from the previous iteration.

## Known Limitations

- **The "how close counts as a touch" and "how much extra weight per timeframe" numbers are
  reasonable starting points, not scientifically validated values.** They were chosen to be
  sensible and are documented as such (the same honesty standard already applied elsewhere in the
  project to similar starting-point settings) — they have not been tested against real trading
  outcomes yet. That honest measurement is a later step in this project, not this iteration.
- **If a saved price-bar file for a symbol ever becomes corrupted, the system currently reports "no
  price history for this symbol" rather than a more specific "this symbol's data is damaged"
  message.** The existing corruption-detection safeguard from the previous iteration still catches
  and reports the damage separately elsewhere; it just isn't distinguished within this particular
  levels answer yet. This wasn't required for this iteration and can be revisited later if needed.
- **Confluence zones, conviction grades (A/B/C), the future trading strategy, and honest profit
  measurement remain unbuilt, as planned** — this iteration is purely the "find individual price
  levels" building block those later steps will consume.
- **No screen in the website to look at levels directly** — machine-only (web API + MCP tool), as
  planned for this step.
