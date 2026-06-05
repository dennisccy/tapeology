# Goal iter-6 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-6
**Date:** 2026-06-05
**Written by:** developer

---

## Features Implemented

- **Price chart with tape-state markers**: When you watch a ticker in **Simulated** or
  **Historical** mode, a candlestick price chart now appears **above** the existing cockpit. It
  draws the watched price as candles and places a colored marker on the chart at each moment the
  tape state changed to a meaningful one — **green** for buyer control, **red** for seller control,
  **amber** for absorption. (An "unclear" state is deliberately not marked.) This lets you see, at
  a glance, whether a marked state actually preceded the next price move.
- **Bar-size selector (10s / 30s / 60s)**: A small set of buttons on the chart lets you switch how
  much time each candle covers. The chart redraws at the chosen size. You can also drag to pan and
  scroll to zoom.
- **Chart shown only where it makes sense**: The chart appears for **Simulated** and **Historical**
  watches and is **hidden in Live** mode (by design for this step). It stays on the same single
  screen — no new page or menu.
- **"No data" is shown honestly**: Before any price data arrives, or for a historical window that
  has no data, the chart shows a plain "no price history yet" message instead of fake candles.

---

## Changed Behavior

- **The Watch screen now has a chart area at the top** for Simulated/Historical. Everything that
  was already on the cockpit (quote, recent trades, features, tape state, observations, event log)
  is unchanged and sits below the chart. Switching the data source still tears down the prior watch
  and returns to idle; the chart simply appears/disappears with the mode.

---

## Backend-Only Items

- `GET /tape/{ticker}/history?bar=<10|30|60>` — returns the price candles + tape-state markers the
  chart draws. The chart is the UI consumer, so this is wired end-to-end; the endpoint is also
  directly readable for verification. (It returns the same numbers the engine computed once — it
  never recomputes anything.)

---

## Incomplete Items

- **J-19 (pause/resume)** and **J-20 (local-time window picker + US-session quick-picks)** — these
  were explicitly **out of scope** for this step and were not started. They are planned as their
  own later slices.
- **Live real-feed verification of the chart** is not part of this step (the chart is hidden in
  Live mode here). The real-data side of the chart is the **Historical** path, whose correctness is
  guaranteed by automated backend tests and is fully exercised the moment vendor credentials are
  present.

---

## Config and Environment Changes

- New engine config values (no behavior to set by an operator — they are the single source for the
  chart's numbers): the allowed candle sizes `(10, 30, 60)` seconds, the set of tape states that
  earn a marker, and in-memory caps on how many candles/markers are retained.
- `NEXT_DIST_DIR` (frontend, optional) — lets a one-off production build write to a separate output
  folder so it can't disturb a running dev server. **Unset by default**; normal start/build is
  unchanged. Operators do not need to set this.
- No database, no migrations, no secrets, no new backend dependency. One new **frontend** library
  was added for the chart (`lightweight-charts`), installed via the normal `npm install`.

---

## Known Limitations

- The price history is kept **in memory only** (consistent with Phase 1) and is **capped**, so a
  very long historical replay keeps only the most recent candles/markers on the chart.
- When you switch the candle size, there is a sub-second moment before the chart re-fetches and
  redraws at the new size. This is cosmetic and clears within about one second.
- At the coarser candle sizes, two markers that are close in time can visually overlap on the chart
  — the underlying marker data (count, state, color) is still correct.
- The chart refreshes by re-reading the history about once per second (matching the rest of the
  cockpit's update rate) rather than instantly on every single trade.
