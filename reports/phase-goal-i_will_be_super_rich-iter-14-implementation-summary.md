# Goal iter-14 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-14
**Date:** 2026-06-09
**Written by:** developer

---

## Features Implemented

- **Real sharp moves now read correctly (not "unclear").** When you replay a real symbol that made a
  genuine fast directional move — the reference case is GME's ~6% open drop on 14-05-2024 — the
  cockpit now reads **seller_control** (and a comparable rally reads buyer_control) instead of sitting
  on "unclear" through an obvious move. Two things make this work: historical replay now pulls the
  **SIP consolidated feed** (which has realistic, tight spreads) instead of the single-venue IEX feed
  that produced misleadingly wide spreads; and the engine now treats a momentarily wide spread on a
  clearly-directional move as a *confidence factor*, not a hard "can't decide" veto.

- **Long historical windows start playing quickly instead of being refused.** Picking a long window
  (e.g. Full RTH) on a liquid symbol used to fail with "that window is very high-volume — try a
  shorter range." Now the cockpit and chart begin filling from the **first piece of the window** while
  the rest streams in behind it. The "shorter range" message is now a true last resort — it only
  appears if even the first piece genuinely can't load in time.

- **The engine handles very dense real data without stalling.** A real consolidated-tape window can
  carry tens of thousands of trades in seconds. The engine's number-crunching was rewritten to update
  incrementally, so a dense window now processes in about a second instead of stalling for minutes.
  The numbers it produces are exactly the same as before — only faster.

---

## Changed Behavior

- **Historical replay data source:** Previously both live and historical used the free IEX feed. Now
  **historical replay uses the SIP consolidated feed** (realistic spreads); **live streaming still
  uses IEX** by design.

- **Tape state on a real wide-spread move:** Previously a wide quoted spread always vetoed a
  directional call (so a real fast mover got stuck on "unclear"). Now a wide-but-plausible spread on
  an otherwise-clear move no longer vetoes the call — it just lowers confidence. A *genuinely* wide
  spread on mixed/weak tape still reads "unclear" (the system stays honest about uncertainty).

- **Long historical Watch:** Previously the whole window was fetched before the Watch responded
  (so long windows timed out). Now only the first slice is fetched up front; the rest loads in the
  background as the replay advances.

---

## Backend-Only Items

- None new. Every change sits behind UI rows that already exist (the tape-state panel and its chart
  markers, and the historical fetch-wait treatment). No new endpoint, field, panel, or control.

---

## Incomplete Items

- **J-37 long/dense real fixture is a representative slice + in-test chunking, not a separate
  committed multi-hour capture.** A genuinely long real window for a liquid symbol is many megabytes
  (too large to commit and too dense to replay in the automated test budget). So the long-window
  behavior is verified over the *same real GME data* split into multiple pieces inside the test (real
  records, real stitching) plus a controlled fake for the "first piece loads before the whole window"
  timing. This is documented in the dev handoff; if a separately-committed real multi-piece capture is
  required, the test seam already supports adding one.

---

## Config and Environment Changes

- `historical_feed` — which market-data feed historical replay reads — default: `sip`
- `live_feed` — which market-data feed live streaming reads — default: `iex`
- `directional_override_enabled` — master switch for the "spread is a graded factor, not a veto" rule
  — default: `true`
- `override_max_spread_multiple` — how much wider than the normal "stable" spread a move's spread may
  be before the override stops applying (beyond this it stays "unclear") — default: `4.0`
- `override_spread_floor_score` — the lowest the spread can drag confidence to inside that band —
  default: `0.5`
- The vendor feed-override environment variable (set to `sip`/`iex`) still pins both modes for an
  operator who wants to force a feed for testing. No new secrets. No database/migrations (still
  in-memory).

---

## Known Limitations

- The committed real GME fixture is ~1.2 MB (real market data only — no credentials in it). A full
  10-minute / Full-RTH SIP capture would be ~5–6 MB and too dense to replay in the test budget, so a
  dense representative slice of the drop is committed instead.
- The engine's fast incremental path is used while a window is still filling (the dense-burst case
  this iteration targets). If a window slides continuously through a very long dense stretch, the
  engine falls back to a slower-but-exact computation for those moments — still correct, and still far
  faster than before.
- No UI changes this iteration; the improvements are visible through the existing cockpit (correct
  tape state on real moves) and the existing historical fetch-wait (long windows start quickly).
