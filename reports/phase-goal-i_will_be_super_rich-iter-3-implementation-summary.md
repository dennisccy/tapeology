# Goal Iteration 3 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-3
**Date:** 2026-06-04
**Written by:** developer

---

## Features Implemented

- **Live market-status indicator**: When you choose the **Live** data source, the top bar now shows the *real* US market session — **open** (green), **closed** with the **next open time** (amber), or **unavailable** (amber, when no data credentials are configured). It refreshes itself about once a minute while you stay on Live. Previously this was a fixed "market unavailable" label that never told the truth.
- **Honest "market is closed" screen**: If you try to **Watch** a real symbol in **Live** mode while the US market is closed, you now get a clear amber **"Market is closed"** message that also tells you when the market next opens — instead of a fake or empty trading cockpit. No prices, trades, or tape readings are ever invented to fill the gap.
- **Market clock service** (`GET /market/clock`): a new backend endpoint that reports whether the market is open or closed plus the next open/close times, pulled live from the data vendor (Alpaca). It's read-only — it only checks the clock and never places or simulates any order.

This completes the "real-data honesty" set: every real-data failure mode — no credentials, an unknown symbol, an empty historical window, and now a **closed market** — shows its own distinct, honest message rather than a fabricated screen.

---

## Changed Behavior

- **Live mode top-bar badge**: Previously always showed a static "market unavailable" pill regardless of the real session. Now shows the real open/closed/unavailable status with the next-open time when closed.
- **Live "Watch" while the market is closed**: Previously a Live watch (with credentials) returned a generic "not yet available" message in all cases. Now, when the market is specifically **closed**, it returns the distinct "market is closed (next open …)" state. With the market **open**, it still honestly reports that live streaming isn't built yet (that arrives in the next iteration).
- All other behavior — Simulated watching, Historical replay, symbol search, Stop — is unchanged.

---

## Backend-Only Items

- None. Every backend capability added this iteration (the market clock and the closed-market refusal) is surfaced in the UI (the Live indicator and the "Market is closed" panel).

---

## Incomplete Items

- **Real live streaming (J-12)** is intentionally **not** built this iteration. With credentials and an open market, a Live watch still reports "not yet available." This is deliberate and honest — the real-time streaming feed is scheduled for the next iteration (iter-4). The market clock built here is the prerequisite "is the market open?" check for that work.
- **Live-feed gap → `stale` → recover (J-15)** is also deferred to iter-4 (it needs the streaming feed to exist first).

---

## Config and Environment Changes

- **No new environment variables.** The market clock reuses the existing Alpaca credentials (`ALPACA_API_KEY` / `ALPACA_API_SECRET`) already documented in `apps/backend/.env.example`. With no credentials, the indicator simply shows "unavailable" and the clock endpoint reports `available:false` — it never guesses.
- New internal setting `market_closed_status_code` (default **409**) in `app/config.py` — the HTTP status used when a Live watch is refused because the market is closed. Operators don't need to change this; the UI keys off the message, not the number.
- Frontend poll cadence for the indicator is a named constant (60 seconds) in `MarketStatusIndicator.tsx`.

---

## Known Limitations

- **The closed-market screen and the "open/closed" indicator depend on the actual time of day.** At the time of this build the US market was closed, so the closed state is directly visible. If you test during regular market hours, you'll see "market open" instead, and a Live watch will report "not yet available" (since live streaming is iter-4). The closed-market path is also fully covered by an automated backend test that does not depend on the wall clock.
- **No credentials → "unavailable", not a guess.** If Alpaca credentials are missing or the vendor can't be reached, the indicator and endpoint both report "unavailable" rather than assuming open or closed. This is intentional (the no-fabricated-data rule).
- The next-open time is shown in your browser's local timezone with the zone labelled (e.g. "Jun 4, 09:30 EDT"), converted from the backend's authoritative UTC value.
