# Goal iter-13 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-13
**Date:** 2026-06-09
**Written by:** developer

---

## Features Implemented

- **Change replay speed on the fly (J-32):** While watching a historical replay, the user can pick a
  new speed (1× / 2× / 5× / 10×) and the replay immediately re-paces to it — the chart and panels
  keep going from where they are, without re-loading the window or restarting the watch.
- **Honest "control" reads on real moves (J-33):** A real stock making a clear directional move now
  reads as **buyer control** or **seller control** instead of being stuck on "unclear". The system
  now judges whether a spread is "wide" and whether price actually moved *relative to the stock's
  price level* (a $0.10 spread is normal for a $40 stock but wide for a $5 one), instead of using
  one fixed dollar cutoff that only fit the ~$100 simulator. Genuinely uncertain tapes (a spread
  that is wide *for that price*, or heavy one-sided pressure with no real price progress) still read
  "unclear" or "absorption" — the system does not manufacture a confident call.
- **Long historical windows load (J-34):** Choosing the "Full RTH 9:30–16:00" quick-pick (or any
  multi-hour window) for a busy stock now loads the real data instead of refusing it with the "very
  high-volume — try a shorter range" message. Behind the scenes the window is fetched in several
  bounded pieces at the same time and stitched back together in time order, so it loads quickly. The
  "shorter range" message now appears only for a window that is genuinely too large to load in time.

---

## Changed Behavior

- **Tape-state classification:** Previously a real stock with a proportionate-but-absolutely-wide
  spread, or with a strong move expressed in cents on a sub-$100 price, could sit on "unclear". Now
  it resolves to buyer/seller control when the move is real relative to the price. The five
  simulated scenarios and every existing classifier test still produce the same results.
- **Historical window loading:** Previously every window was fetched as a single vendor request, so
  a long window could time out and return "very high-volume". Now a long window is fetched in
  parallel pieces and stitched in order; a short window is still one request (unchanged).
- **Replay-speed control:** Previously the speed dropdown only affected the *next* Watch. Now, while
  a replay is running, changing it re-paces the *current* replay live.

---

## Backend-Only Items

- None new without UI. The one new endpoint, `POST /watch/{ticker}/speed`, is wired to the existing
  Historical replay-speed control.

---

## Incomplete Items

- **Credential-gated confirmation legs are not run here.** J-33's real-GME confirmation and J-34's
  real Full-RTH liquid-symbol load need Alpaca credentials (not configured in this environment).
  They are covered by deterministic, no-credentials gating tests (a classifier regression fixture
  for J-33; chunk-split + in-order-stitch unit tests for J-34), which pass. An operator with
  credentials should run the real-data confirmation legs.

---

## Config and Environment Changes

- No new environment variables. All new tunables are config constants (no magic numbers):
  - Relative classifier gates: `max_stable_spread_bps` (30 bps), `min_buy_price_impact_return`
    (0.0002), `max_sell_price_impact_return` (-0.0002), `absorption_flat_band_return` (0.0005),
    `impact_return_scale` (0.003).
  - Chunked fetch bounds: `historical_chunk_seconds` (900 s = 15 min sub-windows),
    `historical_chunk_max_concurrency` (4 sub-windows in flight at once).
- No database, no migrations (Phase 1 stays in-memory).

---

## Known Limitations

- The replay-speed change is silent on success (the new cadence is simply visible as new data
  arrives); only a failure shows a message.
- A new internal `reference_price` value now appears in the raw per-window feature data served by
  `/features` and the live stream. It is used by the classifier (single source of truth) and is not
  shown as a new on-screen readout.
- Changing speed only applies to historical replays (not to the simulator or a live feed, which have
  no replay pacing) — that matches where the control is shown.
