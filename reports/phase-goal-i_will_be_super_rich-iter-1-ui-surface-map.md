# Phase goal-i_will_be_super_rich-iter-1 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-1
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

All changes stay under the single existing screen `/` — no new routes. The surfaces below are the components/elements within `/` that changed.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `DataSourceSelector` (TopBar) | New component | J-10 data-source selection | Confirm the selector shows exactly three buttons — `Live`, `Historical`, `Simulated` — with `Simulated` highlighted (aria-pressed) on first load; click each and confirm only the clicked one becomes active |
| `/` | `TopBar` symbol/ticker input | Changed behavior | Input is now mode-aware | In Simulated, confirm the box placeholder reads `Ticker e.g. SIM-BUYER` (aria-label "Ticker"); switch to Live and confirm it changes to `Symbol e.g. AAPL` (aria-label "Symbol search") |
| `/` | `TopBar` Historical controls (date / start time / end time / replay-speed) | New form controls | Historical needs a replay window (J-10) | Click `Historical`; confirm a date input, a start-time input, an end-time input, and a speed `select` (options 1× / 2× / 5× / 10×) all appear inline; switch to Live or Simulated and confirm they disappear |
| `/` | `TopBar` market-status indicator | New component | Live honest market status (J-10) | Click `Live`; confirm an amber pill reading `market unavailable` (with an amber dot) appears; switch away from Live and confirm it disappears; confirm it never shows "open" or "closed" |
| `/` (main area) | `ProviderUnavailable` panel | New component | Honest no-credentials state (J-14 no-creds path) | Select `Live`, type `AAPL`, click `Watch`; confirm the main area shows the amber "Real-data provider unavailable" panel with the text "real-data provider unavailable" and NO cockpit grid; repeat in `Historical` and confirm the same panel appears |
| `/` (main area) | `Cockpit` (Simulated regression) | Changed behavior (no-regression check) | Selector now precedes the ticker box | Select `Simulated`, type `SIM-BUYER`, click `Watch`; confirm the cockpit populates and tape state resolves to `buyer_control` (unchanged from J-01/J-02) |
| `/` | `page.tsx` watch lifecycle / status dot | Changed behavior | iter-0 orphaned-watch fix | While watching SIM-BUYER, switch the data source (or Watch a different symbol); confirm the prior "Watching <ticker>" indicator clears and the status dot returns to idle/connecting before the new watch starts (no leftover watch) |

---

## Backend-Only Changes (No UI Impact)

- `app/providers/adapters/base.py` — vendor-neutral `MarketDataAdapter` interface (`name`, `is_available()`) — no UI surface; foundation for later real providers.
- `app/providers/adapters/alpaca.py` — `AlpacaAdapter` env-only credential detection + canonical `real_data_available()` — drives the 503 gate but is never displayed directly; the UI only observes its effect via the provider-unavailable panel.
- `app/main.py` `WatchRequest` body + `RealDataUnavailableError` / 503 gate — the routing logic is exercised through the Live/Historical Watch buttons (surfaced as the provider-unavailable panel), so it is not hidden; the `provider_not_implemented` (creds-present) branch has no UI this iteration by design.
- `apps/backend/.env.example` — documents `ALPACA_API_KEY` / `ALPACA_API_SECRET` / `ALPACA_FEED` names with empty values — config file, no UI.
- `apps/backend/tests/test_real_data_gate.py` — backend tests — no UI.

---

## Summary

- **Frontend surfaces changed:** 7 (all within the single `/` screen)
- **New pages/routes:** 0
- **Modified components:** `TopBar`, `page.tsx` (+ new `DataSourceSelector`, `ProviderUnavailable` components)
- **Navigation changes:** no (still exactly one screen `/`)
- **Backend-only changes:** 5
