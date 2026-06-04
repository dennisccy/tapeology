# Goal Iteration 4 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-4
**Date:** 2026-06-04
**Written by:** developer

---

## Features Implemented

- **Live real-time tape streaming**: Selecting **Live**, entering a real US symbol, and pressing
  **Watch** now streams the vendor's real-time trades and quotes through the same engine and shows
  the single-ticker cockpit with the status reading **live** (green dot). Previously this was
  refused with a "not yet available" message.
- **Honest "stale" on a feed lull, with automatic recovery**: When no live event arrives for a
  configured window (default 10 seconds), the status honestly flips to **stale** (amber dot) and
  the system invents **no** trades during the quiet period; when real data resumes it returns to
  **live**.
- **Clean stop / switch of a live watch**: Stopping a live watch — or switching to another symbol
  or data source — closes the underlying live connection to the vendor, so no connection is left
  dangling.

---

## Changed Behavior

- **Live "Watch" button**: Previously, choosing Live and pressing Watch returned an explicit
  "real-data provider not yet available" refusal (no cockpit). Now it starts a real live stream and
  shows the live cockpit (when credentials are configured and the market is open).
- **Live watch while the market is closed**: Still refused with an explicit "market is closed"
  message that includes the next market open — unchanged from the prior iteration (reuses the same
  market clock; no second lookup).
- **Live watch with no credentials**: Still shows an explicit "real-data provider unavailable" —
  unchanged.

---

## Backend-Only Items

- None. Every new capability is reachable through the existing single screen — the Live mode's
  Watch action now streams, and the existing status dot and watched-source label display the live /
  stale status and the "live <SYM>" descriptor. No frontend code change was required (verified).

---

## Incomplete Items

- **Operator/gated live-socket check**: The spec described this as likely *not* runnable this loop
  (expecting an off-hours market). In fact the market was **open** at implementation time, so the
  check was run and **passed** against the real Alpaca live socket (Ford/F: live status with real
  trades within ~2 seconds, then a clean disconnect). Nothing about this item is incomplete.
- **Auto-reconnect of a dropped live connection**: Intentionally out of scope. A dropped
  connection honestly shows **stale** until data resumes or the watch is stopped.

---

## Config and Environment Changes

- `stale_gap_seconds` (engine config, default `10.0`) — how many seconds without a live event
  before the status flips to **stale**. Not a secret; a plain tunable.
- `ALPACA_API_KEY` / `ALPACA_API_SECRET` (environment only, already documented in `.env.example`) —
  required for any real-data mode. With them blank, the app runs simulator-only and Live reports
  "unavailable". No new credentials were added this iteration.
- A pytest marker `integration` was registered so the gated real-socket test is recognized and
  skipped by default (it only runs with `TAPEOLOGY_LIVE_INTEGRATION=1`, credentials, and market
  hours).

---

## Known Limitations

- **One live connection at a time (vendor free tier)**: Alpaca's free feed permits a single
  concurrent live WebSocket. The app watches one symbol at a time (by design), so this is not a
  limit in normal use; but two live watches at once, or a leftover connection from an abruptly
  killed process, can starve each other of data.
- **A high-priced symbol may honestly read "unclear" on the free IEX feed**: The free feed's
  top-of-book can be wide for expensive names, so the tape may legitimately read **unclear** at low
  confidence. This is correct, honest behavior — not a bug. For a clean live demo, prefer a
  tight/penny-spread liquid name (e.g. F).
- **Historical date/time picker uses UTC**: (carried over) the window picker sends naive times
  treated as UTC; an operator must enter UTC times. A market-local/timezone picker is not built.
