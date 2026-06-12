# Iteration 17 — Implementation Summary

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-17
**Date:** 2026-06-12
**Written by:** developer

---

## Features Implemented

- **Engine keeps up with dense, real market tape (performance gate)**: The tape-reading engine now
  processes a long, busy stream of real trades and quotes without slowing down as the stream grows.
  Previously, after the first time old data aged out of a rolling window, the engine quietly fell
  back to re-scanning the entire window on every single new event — which got dramatically slower
  the longer you watched. That slowdown is removed: the engine maintains its "did the quote hold?"
  refresh measurements incrementally, so a ten-minute real window that used to take about three
  minutes to replay now replays in about ten seconds. Crucially, the numbers it produces are exactly
  the same as before — this is a speed fix, not a behaviour change.

- **A committed real-market test recording**: A real ten-minute slice of Procter & Gamble (PG)
  trading from 2026-06-09 (captured from the consolidated SIP feed) is now saved in the project so
  the engine's speed and correctness can be re-checked automatically, with no market-data account
  required. This same recording will be reused next iteration as the reference for the "replay
  studies" feature.

- **An automatic speed check (CI gate)**: A test replays that real recording through the engine and
  fails if it takes longer than a configured time budget — so if the old slowdown ever sneaks back,
  the test suite catches it immediately.

---

## Changed Behavior

- **None visible to a user.** Watching a ticker, the tape state, confidence, features, chart,
  observations, and event log all behave exactly as before. The only difference is internal: the
  engine computes the same results faster on long/dense streams. This was verified by re-running the
  full existing test suite and by a live check that watching `SIM-BUYER` still resolves to
  "buyer_control" at the same confidence as before.

---

## Backend-Only Items

- The performance improvement is entirely inside the engine's feature computation. There is no UI to
  wire — a speed gate is not something the interface exposes. (This is by design for this iteration.)

---

## Incomplete Items

- **None for this iteration's scope.** This iteration is deliberately a prerequisite step: it makes
  the engine fast enough for the upcoming "replay studies" feature (journeys J-60–J-62), which is
  built next iteration on top of this gate. The studies page, the studies API, and the pinned
  reference study itself are intentionally out of scope here.

---

## Config and Environment Changes

- `dense_replay_time_budget_seconds` — the time budget (in seconds) the automatic speed check allows
  for replaying the committed real recording through the engine — default: `60.0`. It is a
  CI/testing value only; it deliberately does not affect any saved research record or analytics
  grouping.
- No database/schema change (the research store stays at version 7). No new environment variables.

---

## Known Limitations

- The committed test recording is a single calm mid-session window of one liquid stock, chosen so
  the file stays small (~1.2 MB) while still being long enough that every rolling window ages out
  old data (the condition the performance fix needed to be proven against). It is real, captured
  data — not synthesized.
- One internal path (re-mapping when a quote ages out from under an old trade) still does a single
  bounded recompute of the current window when it occurs; on the real recording this happens a few
  hundred times and is the main reason the replay takes ~10 seconds rather than near-instant. It is
  bounded (never a per-event full re-scan) and produces identical numbers, so it does not bring back
  the old slowdown — but it is the honest residual cost worth noting.
