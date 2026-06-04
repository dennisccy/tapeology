# goal-i_will_be_super_rich-iter-1 — Implementation Summary

**Phase:** goal-i_will_be_super_rich-iter-1
**Date:** 2026-06-04
**Written by:** developer

---

## Features Implemented

- **Data-source selector**: A control at the top of the page lets the user choose between three
  data sources — **Live**, **Historical**, and **Simulated**. Simulated is selected by default.
- **Mode-specific controls**: Each source reveals only the controls it needs — Simulated shows
  the ticker box; Live adds a symbol box and a market-status indicator; Historical adds a symbol
  box, a date and start/end time picker, and a replay-speed chooser.
- **Honest "real-data provider unavailable" state**: Choosing **Live** or **Historical** and
  clicking **Watch** while no vendor credentials are configured shows a clear "real-data provider
  unavailable" message in place of the tape cockpit — the system never invents or shows fake tape
  data, and never quietly drops back to the simulator.
- **Live market-status indicator**: In Live mode a small indicator honestly reads "unavailable"
  (because no credentials are configured and the real market clock is not wired yet) instead of
  guessing whether the market is open.
- **Vendor-agnostic data seam (under the hood)**: A single, isolated place in the backend now
  owns all knowledge of the data vendor (Alpaca). This is the foundation that later lets real
  live and historical data flow through the exact same engine without changing it.
- **Cleaner watch handover**: Starting a new watch, or switching the source or symbol, now
  properly stops the previous watch first — so no stale or orphaned watches are left running in
  the background.

---

## Changed Behavior

- **Watching a ticker**: Previously the page had a single ticker box. Now it has the data-source
  selector first, and the ticker box is the Simulated mode's control. **Simulated mode behaves
  exactly as before** — watching `SIM-BUYER` still resolves to buyer_control with the same live
  cockpit.
- **Starting a watch / switching**: Previously, switching tickers did not stop the previous
  backend watch. Now any new watch or source/symbol switch stops the prior watch first.

---

## Backend-Only Items

- None that are hidden — every backend change this iteration is reachable from the UI:
  the watch-body routing and the no-credentials 503 are exercised by the Live/Historical Watch
  buttons, which surface the "provider unavailable" panel.
- The credential-availability check (`real_data_available`) is internal and is **intentionally
  not** exposed as its own screen value — the UI learns availability only when a real-mode Watch
  is refused.

---

## Incomplete Items

- **Real Live / Historical data (serving)**: Out of scope this iteration by design. With
  credentials present, a real-mode watch still returns an explicit "not yet available" error
  rather than a cockpit. Real data lands in later iterations (J-11 historical, J-12 live).
- **J-14 edge cases other than no-credentials**: Unknown symbol, empty historical window, and
  market-closed are deferred (they need live vendor calls — J-11/J-12/J-13).
- **Symbol search suggestions and the real market clock**: The symbol box is free-text only and
  the market indicator is a static "unavailable"; vendor-backed search (J-13) and the live clock
  (J-12) are later.

---

## Config and Environment Changes

- `ALPACA_API_KEY` — Alpaca API key for real data — default: **empty** (real modes report
  "unavailable" until set).
- `ALPACA_API_SECRET` — Alpaca API secret for real data — default: **empty**.
- `ALPACA_FEED` — which market-data feed to use — default: `iex` (Alpaca's free feed).
- New file `apps/backend/.env.example` documents these names with empty values. **No secret is
  committed.** Credentials are read from the environment only; an operator copies `.env.example`
  to `.env` and fills it in to enable real modes later.
- Note: an existing local `apps/backend/.env` uses the name `ALPACA_SECRET_KEY`; the app reads
  `ALPACA_API_SECRET` (per `.env.example`). The local file is not loaded by the app and does not
  affect behavior — use the `.env.example` names when configuring real credentials.

---

## Known Limitations

- The Live and Historical modes can currently only demonstrate the **honest unavailable** state —
  they do not yet show real market data. This is intentional for this iteration.
- The market-status indicator is a fixed "unavailable" and does not reflect real market hours yet.
- The Historical date/time/speed inputs are accepted but not yet used to fetch anything (the
  watch is refused before they take effect).
- Verification was performed with **no credentials configured**, which is the supported and
  intended path for this iteration.
