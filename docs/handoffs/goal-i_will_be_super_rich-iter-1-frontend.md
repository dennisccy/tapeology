# goal-i_will_be_super_rich-iter-1 Frontend Handoff

**Phase:** goal-i_will_be_super_rich-iter-1
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built (UI)

Still **exactly one screen** (`/`). The cockpit grid itself is **unchanged**; only the TopBar
controls and the cockpit-area empty/failure state evolved.

- **Data-source selector** (TopBar) — a hand-built 3-way segmented control with exactly **Live /
  Historical / Simulated**. Default **Simulated**. `aria-label="Data source"`, each button
  `aria-pressed`.
- **Per-mode control reveal** (TopBar):
  - **Simulated** → ticker input (`aria-label="Ticker"`, placeholder `Ticker e.g. SIM-BUYER`) + Watch.
  - **Live** → symbol search (`aria-label="Symbol search"`, placeholder `Symbol e.g. AAPL`) + a
    **market-status indicator** (amber pill reading `market unavailable`) + Watch.
  - **Historical** → symbol search + **date** picker + **start time** + **end time** + a
    **replay-speed** select (`1× / 2× / 5× / 10×`) + Watch.
- **"Real-data provider unavailable" panel** (`ProviderUnavailable.tsx`) — replaces the cockpit
  grid in `<main>` when a Live/Historical Watch returns 503. Amber-bordered `Panel` with the
  exact phrase **"real-data provider unavailable"** and operator guidance (set Alpaca creds or
  switch to Simulated). Never a fabricated cockpit, never a silent fall-back to Simulated.
- **Watch-lifecycle teardown** — a new Watch or a source/symbol switch first `DELETE`s the prior
  watch and closes its WebSocket (via `setTicker(null)` → `useTapeStream` cleanup) before the
  new watch starts. No orphaned backend watch/socket.

## Color Semantics (load-bearing, unchanged tokens)

- **Amber** = unavailable/unclear → the market-status pill and the provider-unavailable panel.
- **Emerald** = active Watch CTA (unchanged). **Rose** = Stop / closed (unchanged).
- Monospaced numerics for the symbol input and any readouts. No new palette tokens.

## Files Changed

**Created**
- `apps/frontend/components/DataSourceSelector.tsx`
- `apps/frontend/components/ProviderUnavailable.tsx`

**Modified**
- `apps/frontend/app/page.tsx` — owns `mode` + `unavailableMode`; `handleWatch` / `handleModeChange` tear down the prior watch first; renders `Cockpit` | `ProviderUnavailable` | `IdleState`.
- `apps/frontend/components/TopBar.tsx` — hosts the selector + per-mode form controls + Live market-status indicator.
- `apps/frontend/lib/api.ts` — `watchTicker(ticker, params?)`; no body for sim, JSON body for real modes; flags the 503 `provider_unavailable` result via `providerUnavailable`.
- `apps/frontend/lib/types.ts` — `DataSourceMode`, `WatchParams`.

## Single Source of Truth

- The frontend renders engine values verbatim (unchanged). `real_data_available` is **never**
  re-derived in the UI — the UI learns "provider unavailable" only from the backend's 503.
- Simulated mode sends a **bodyless** `POST /watch` (byte-for-byte the prior request), so the
  J-01/J-02/J-08 sim path is unchanged.

## How to Verify (operator, ~2 min, NO credentials)

1. `bash scripts/start-backend.sh` and `bash scripts/start-frontend.sh`; open the frontend URL.
2. The TopBar shows the **Live / Historical / Simulated** selector (Simulated active).
3. Click **Live** → a symbol box + an amber **market unavailable** pill appear. Click **Watch** →
   the main area shows the **"real-data provider unavailable"** panel (no cockpit).
4. Click **Historical** → symbol box + date + two time inputs + a speed select appear. Type
   `AAPL`, click **Watch** → the same **provider-unavailable** panel (no cockpit).
5. Click **Simulated** → ticker box appears. Type `SIM-BUYER`, click **Watch** → the cockpit
   populates and the tape state resolves to **buyer_control** (J-01/J-02, no regression).
6. While watching, switch the selector or re-Watch a different ticker → the prior watch is torn
   down (the status dot returns to idle/connecting; no leftover watch).

## Known Limitations

- Live/Historical produce **only** the honest provider-unavailable state this iteration (no real
  cockpit) — real serving is J-11/J-12.
- The market-status indicator is a **static** "unavailable" (no live clock yet — J-12).
- The Historical date/time/speed values are sent in the watch body but drive **no** real fetch
  yet (the watch is refused before use). Symbol entry is free-text (vendor search is J-13).
