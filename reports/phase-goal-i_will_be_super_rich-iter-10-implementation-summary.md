# Iteration 10 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-10
**Date:** 2026-06-07
**Written by:** developer

---

## Features Implemented

- **"Waiting for the first trade" screen**: When you click Watch and the connection succeeds but no
  trade has come through yet (a quiet or off-hours symbol, or just the moment right after connect),
  the screen now clearly says "Connected to `<SYMBOL>` (`<mode>`) — waiting for the first trade…"
  instead of showing a wall of empty panels. You always know the watch is alive and what it is
  waiting for.
- **Honest "waiting" status light**: A new amber, gently pulsing status dot reads "waiting" while
  the tape is connected but empty — it never shows a confident green "live" over a blank tape.
- **Background failure is now shown, not hidden**: If the data feed breaks in the background after a
  successful Watch (for example the connection drops), the screen now shows an explicit error
  ("The tape feed failed after connecting. No tape is shown.") with a red "failed" status light,
  instead of silently freezing. The failure is also recorded in the server log.
- **A quiet feed eventually says "stale"**: A live watch that connects but never receives a trade
  (e.g. a thinly traded symbol or after market hours) automatically moves from "waiting" to "stale"
  after the configured quiet-period, rather than sitting on "waiting" forever — and no fake trades
  are invented during the wait.

---

## Changed Behavior

- **The cockpit after a successful Watch**: Previously, once any snapshot existed the app would draw
  the full grid of (often blank) panels, which could look like a connected-but-empty "live" cockpit.
  Now an empty, just-connected tape shows the explicit "waiting" screen, and only fills in the full
  panel grid once real trade/quote data arrives. No more mute/blank cockpit.
- **Status light meaning**: The status light now has two additional honest states — "waiting"
  (connected, no data yet) and "failed" (the feed broke after connecting) — in addition to the
  existing connecting / live / stale / paused / closed.

These changes are purely about how the connection state is reported. The tape reading itself — the
five tape states, confidence, features, prices, and the chart — is unchanged and produces identical
results for the same data.

---

## Backend-Only Items

- None. Every backend change (the two new connection states, `waiting` and `failed`) is surfaced in
  the UI. They travel on the existing `stream_status` value that the summary endpoint and the live
  stream already send — no new endpoint was added.

---

## Incomplete Items

- **J-28 / J-29 / J-30 (data-vendor speed and timeouts)** were intentionally left for a later
  iteration and are not part of this work: making vendor calls time out at the network level,
  loading busy historical windows faster, and a faster symbol search. They were explicitly out of
  scope here to keep this iteration focused on the connection-lifecycle fix.

---

## Config and Environment Changes

- None. No new settings, environment variables, or magic numbers were added. The "quiet feed →
  stale" timing reuses the existing `stale_gap_seconds` setting.

---

## Known Limitations

- The new "waiting" / "stale" / "failed" behavior on a **real live market socket** is proven by
  automated tests using stand-in feeds; confirming it against the real data vendor during/after
  market hours is still an operator check (the same as for the existing live-streaming feature).
- For the built-in simulated tickers (e.g. SIM-BUYER), the "waiting" screen is only shown very
  briefly because simulated data arrives almost instantly — it flips to a live read within a second
  or two. The "waiting" screen is most visible on real, quiet, or off-hours symbols.
- Pausing a watch was not changed in this iteration; the Pause button stays hidden during the brief
  "waiting" phase (Stop is always available).
