# goal-i_will_be_super_rich-iter-2 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-2
**Date:** 2026-06-04
**Written by:** developer

---

## Features Implemented

- **Replay a real historical session (J-11)**: In **Historical** mode you can now enter a real US
  symbol, pick a past date + time window and a replay speed, and press Watch — Tapeology fetches
  that window's **real** trades and quotes from the market-data vendor (Alpaca) and replays them
  through the exact same engine the simulator uses. Every cockpit panel fills with real values
  (bid/ask/spread/last, recent trades, the feature readouts, the tape state + confidence,
  observations, and the event log), and the read is reproducible for a fixed symbol + window.
- **Find a symbol by search (J-13)**: In Live or Historical mode the symbol box suggests real
  matching tradable symbols (ticker + company name) as you type. Pick one to fill the box — or just
  type the symbol yourself and press Watch.
- **Honest messages when real data isn't there (J-14, two new cases)**: Instead of a cockpit, you
  now see a distinct, plain message when a real symbol **isn't tradable** ("not a tradable symbol")
  or when a chosen window **has no data** ("no data for that window"). The existing "real-data
  provider unavailable" message (no credentials) still appears too. Tapeology never invents a tape
  to cover a gap.

---

## Changed Behavior

- **Historical mode** previously refused every watch with a generic "not yet available" message.
  Now it actually fetches and replays real data (or shows one of the distinct honest messages
  above).
- **The symbol box in Live/Historical mode** previously was a plain text field. Now it offers a
  live suggestions dropdown — typing free text and pressing Watch still works exactly as before.
- **Simulated mode is unchanged** — the built-in scenarios (SIM-BUYER, etc.) behave exactly as
  before.
- **Live mode is unchanged** this iteration — it still reports that real-time streaming is not yet
  wired (that is the next phase, J-12).

---

## Backend-Only Items

- None. Every new capability is reachable from the one screen at `/` (the symbol search dropdown,
  the historical cockpit, and the three distinct honest messages).

---

## Incomplete Items

- **Live streaming (J-12)** is intentionally out of scope — Live mode still shows "not yet
  available". Market-status, the live socket, and `GET /market/clock` are deferred.
- **The "market is closed" honest case (the 4th J-14 case)** depends on Live mode, so it is
  deferred with J-12.
- **Stale-feed recovery (J-15)** is deferred with live streaming.

---

## Config and Environment Changes

- **`apps/backend/.env`** (operator-only, never committed): the secret variable was renamed to the
  name the app expects — `ALPACA_API_SECRET` (it was previously `ALPACA_SECRET_KEY`, which the app
  could not read). With both `ALPACA_API_KEY` and `ALPACA_API_SECRET` set, real Live/Historical data
  is enabled; with them blank/absent, the app runs simulator-only and the real modes show the honest
  "unavailable" message. A new tiny loader makes both the server and the test suite read this file
  automatically — no manual sourcing needed.
- **`ALPACA_FEED`** (optional, non-secret): the market-data feed, default `iex` (Alpaca's free feed).
- **New dependency:** `alpaca-py==0.43.4` (the official Alpaca SDK), pinned and cleared through the
  install security gate. Installed in the backend virtualenv; listed in `requirements.txt`.
- **Engine tunables added** (in `app/config.py`, not hard-coded anywhere): the allowed replay speeds
  (1×/2×/5×/10×) and default, a pacing cap so a quiet stretch never stalls the cockpit, and the
  symbol-search result limit and minimum query length.

---

## Known Limitations

- **Real data needs credentials + network.** With operator credentials present (as in this build),
  Historical replay and symbol search work against the live vendor. Without them, those real
  features honestly report unavailable; the simulator keeps working offline. A committed **real**
  captured sample (Ford, a fixed 2-minute window) lets the historical-replay test re-verify itself
  offline and deterministically.
- **Times are entered in UTC.** The date/time window you pick is read as UTC. To replay a US-market
  session, enter the UTC time (e.g. 15:00 UTC = 11:00 US Eastern in summer). A local-time picker is
  a future refinement.
- **Some real symbols read "unclear".** On the free IEX feed, very high-priced, widely-quoted names
  (e.g. AAPL) often have a noisy/wide quote, so the engine honestly reports "unclear" rather than
  forcing a directional call — this is the system being honest, not an error. Lower-priced liquid
  names (e.g. Ford) show clean reads.
- **Replay speed.** At 1× a window replays in roughly its real duration; choose 2×/5×/10× for a
  quicker walkthrough. The classification result is identical regardless of speed.
- **Nothing about orders or brokerage.** Symbol search uses only the vendor's read-only list of
  tradable symbols; Tapeology places no orders and integrates no trading/execution capability.
