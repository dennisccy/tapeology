# goal-tradable_wall-iter-4 — Implementation Summary

**Phase:** goal-tradable_wall-iter-4
**Date:** 2026-07-14
**Written by:** developer

---

## Features Implemented

- **A third trading strategy, "structure_tape_map"**: the app now has three registered ways of
  simulating trades against historical data — the original `v1`, the frozen `structure_tape`
  (which trades off the raw list of 1,800+ price levels), and this new one, which trades off the
  same handful of "tradable bands" the map view is meant to show a trader. It reuses the exact
  same stop/target/position-sizing rules as `structure_tape` — only *which levels it watches*
  differs.
- **The 3-way profit comparison ("edge report")**: a new backend read endpoint
  (`GET /research/edge-report`) that runs all three strategies over every recorded practice-tape
  window and reports, honestly, how each one did — broken down by price-level quality (A/B/C),
  which side of the market (support or resistance), how price reacted at the touch (rejected /
  broke / chopped), and which data feed the window came from. Every dollar figure carries its
  sample size, its comparison against a random-baseline strategy, and the same "simulated, not
  real trading" disclaimer every other measurement in this app carries.
- **Same information available to AI tools**: the read-only AI assistant interface (MCP) can now
  fetch this same 3-way comparison, byte-for-byte identical to what a person would see calling the
  same web address directly.

---

## Changed Behavior

- **None.** Every existing capability — the original `v1` strategy, the frozen `structure_tape`
  strategy, the raw levels list, the Yahoo bar library, the champion-strategy pointer, and every
  page that already exists — behaves exactly as before. This was verified by re-running the
  entire automated test suite (1,338 tests) with zero failures.

---

## Backend-Only Items

- **`GET /research/edge-report`** — the 3-way profit comparison described above — no UI wiring
  exists yet. The next iteration (J-05) will add a section on the `/structure` page that displays
  this data. Right now the only way to see it is through the API directly (or the AI-assistant
  read tool).
- **The `structure_tape_map` strategy itself** — runnable through the existing "run a backtest"
  API, but there's no button anywhere in the app to pick it; it only gets exercised automatically
  as part of the new comparison report above.

---

## Incomplete Items

None — every requirement for this iteration was completed. The two items that were explicitly
**out of scope** for this iteration (and are planned for later) are:

- Displaying any of this on a page — that's the next iteration (J-05).
- Recording more real historical trading data with the operator's credentials to make the
  comparison numbers more meaningful — that requires the operator to supply Alpaca API keys and
  run a separate recording step; it isn't something this iteration builds.

---

## Config and Environment Changes

None. No new environment variables, no new settings, no database migration. One internal numeric
fingerprint the app uses to guarantee "these results were computed under the same rules" was
double-checked and confirmed unchanged.

---

## Known Limitations

- **The comparison report can be slow to load if there's a lot of recorded history.** Right now,
  with only a handful of practice recordings, it answers instantly. Once the operator has recorded
  many real trading windows across many symbols, computing this report can take several minutes,
  because it has to re-scan the whole 12-symbol watchlist's price history each time it's asked.
  This is a pre-existing cost from an earlier iteration (the scanning step itself wasn't rebuilt
  or slowed down this iteration) — it's flagged here because a future iteration should consider
  caching that scan so the comparison report feels instant even with a full history. It does not
  affect correctness, only response time.
- **With only the practice fixture data available today, the comparison report is honestly
  empty** (no strategy has enough recorded real-world touches yet to report a real result). This is
  expected and by design — the report is built to say so honestly rather than making anything up.
  Once the operator records real trading windows with their own market-data credentials (a
  separate, already-existing action), the report will start showing real, if still small-sample,
  numbers.
