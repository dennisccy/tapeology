# Phase goal-i_will_be_super_rich-iter-2 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-2
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

All surfaces are on the single route `/` (Watch — HOME). No new page or route was added.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `SymbolSearch` (symbol input in Live/Historical) | New component | J-13: live tradable-symbol suggestions | Switch to Historical, type `AAP` in the symbol box, wait ¼ sec; verify a dropdown of `SYMBOL` + company-name rows appears (e.g. `AAPL Apple Inc`) |
| `/` | `SymbolSearch` dropdown row | New component | J-13: selecting a suggestion fills the box | Click a suggestion row; verify the symbol box is filled with that ticker and the dropdown closes |
| `/` | `SymbolSearch` (free-text fallback) | Changed behavior | J-13 must degrade to free-text | Type `F` and press Watch without clicking any dropdown row; verify the watch starts for `F` |
| `/` | `SymbolSearch` (empty/short query) | New component | Debounce + no-result handling | Clear the symbol box; verify no dropdown is shown. Type a query that returns nothing; verify the dropdown shows no stale rows |
| `/` | `TopBar` symbol input (Simulated mode) | Changed behavior | Sim keeps the plain input (no search) | Switch to Simulated; verify the symbol box is a plain field with placeholder `Ticker e.g. SIM-BUYER` and shows **no** suggestions dropdown |
| `/` | `Cockpit` (Historical watch) | Changed behavior | J-11: cockpit now fed by real data | In Historical mode watch `F` for a known-good past UTC window at speed 10×; verify bid/ask/spread/last, recent trades (price/size/side), feature readouts, tape state + confidence, observations, and event log all populate with real values |
| `/` | `TopBar` scenario chip | Changed behavior | Row-6 source label for historical | After a successful Historical watch, verify the `scenario:` chip reads `historical <SYM> <window>` (e.g. `historical F …`) |
| `/` | `ProviderUnavailable` — `symbol_not_tradable` panel | New component | J-14: untradable-symbol honest state | In Historical mode watch a bogus symbol (e.g. `ZZZZNOPE`); verify an amber panel titled "Symbol not tradable" with phrase **"not a tradable symbol"** shows in place of the cockpit (no cockpit panels visible) |
| `/` | `ProviderUnavailable` — `no_data_for_window` panel | New component | J-14: empty-window honest state | In Historical mode watch a valid symbol over a window with no trades; verify an amber panel titled "No data for that window" with phrase **"no data for that window"** shows, and no cockpit appears |
| `/` | `ProviderUnavailable` — `provider_unavailable` panel | Changed behavior | J-14 regression: no-creds state generalized | With no credentials configured, attempt a Historical/Live watch; verify the amber "Real-data provider unavailable" panel still appears (no cockpit, no fall-back to Simulated) |
| `/` | `page.tsx` failure routing | Changed behavior | Routes each `reason` to the matching panel | Trigger each of the three failures in turn; verify the displayed panel matches the reason and the cockpit is never shown alongside a honest panel |
| `/` | `lib/api.ts` `searchSymbols` / `watchTicker` | Changed behavior (frontend support) | Carries `reason`; calls `GET /symbols/search` | Verify the search dropdown is populated only from the API (with no creds the dropdown stays empty and free-text Watch still works) |

---

## Backend-Only Changes (No UI Impact)

These changes enable the surfaces above but have no directly-visible UI element of their own:

- `apps/backend/app/env.py` — stdlib `.env` loader — enables real-data features when creds present; no UI surface.
- `apps/backend/app/providers/historical.py` — `HistoricalProvider` (epoch→logical mapping) — feeds the existing cockpit; no new UI element.
- `apps/backend/app/providers/adapters/alpaca.py`, `adapters/base.py`, `adapters/__init__.py` — vendor adapter `fetch_historical` / `search_symbols` + neutral seam types — power the cockpit/search but are not user-visible.
- `apps/backend/app/watch_manager.py` — `watch_with_provider` + cancellable paced feeder — drives replay; no UI element (effect is the cockpit populating over time).
- `apps/backend/app/main.py` — `POST /watch` historical branch, `GET /symbols/search`, `RealDataError` reasons, adapter DI — the APIs the frontend consumes (covered by surface rows above).
- `apps/backend/app/config.py` — replay speeds/default, pacing cap, search limit/min-query — tunables, no UI element.
- `apps/backend/scripts/capture_alpaca_fixture.py`, `tests/fixtures/alpaca/*.json`, `tests/fakes.py`, and all `tests/*` — operator/test artifacts, no UI surface.
- `apps/backend/requirements.txt`, `config/install-security-policy.json` — dependency/supply-chain, no UI surface.
- `apps/frontend/lib/types.ts` — `SymbolMatch`, `FailureReason` type definitions — no rendered element.

---

## Summary

- **Frontend surfaces changed:** 12 (all on `/`)
- **New pages/routes:** 0
- **Modified components:** `SymbolSearch` (new), `TopBar`, `ProviderUnavailable`, `page.tsx`, `lib/api.ts`, `lib/types.ts`; `Cockpit` reused (now real-fed)
- **Navigation changes:** no (still exactly one screen, `/`)
- **Backend-only changes:** 9 areas (env loader, historical provider, adapter, watch manager, main.py APIs, config, capture/fixtures/tests, dependency/policy, frontend types)
