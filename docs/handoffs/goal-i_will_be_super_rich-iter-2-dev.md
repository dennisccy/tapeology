# goal-i_will_be_super_rich-iter-2 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-2
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built

First **real provider behind the seam** — Historical replay (J-11) + symbol search (J-13),
plus the unknown-symbol / no-data honest states (J-14, 2 of its 4 cases). The same `TapeEngine`
now renders **real Alpaca data**; real data adds no parallel state/feature path.

**Backend**
- **`.env` credential-name fix + loader.** Renamed `ALPACA_SECRET_KEY` → `ALPACA_API_SECRET` in
  the untracked operator `apps/backend/.env` (the adapter names are the contract; the adapter was
  NOT renamed). Added `app/env.py` — a stdlib, no-dependency, **load-if-missing** `.env` loader
  (never overrides an already-set var, tolerates the file's CRLF endings). Called at `app.main`
  import (so uvicorn sees it) and in `tests/conftest.py`. `.env` stays untracked.
- **`alpaca-py==0.43.4`** added through the supply-chain gate (allowlisted in
  `config/install-security-policy.json`, pinned in `apps/backend/requirements.txt`, installed into
  the venv).
- **Alpaca adapter extended** (`app/providers/adapters/alpaca.py`, the ONE vendor module):
  `fetch_historical(symbol, start, end) -> HistoricalWindow` and
  `search_symbols(query) -> list[SymbolMatch]`, with vendor errors translated to neutral outcomes
  (`SymbolNotTradable` / `NoDataForWindow`). SDK is imported **lazily** inside the methods (the
  no-creds/sim/test paths never load pandas/numpy). The asset universe is cached per-process for
  search. `is_available()` / `real_data_available()` stay the single availability source.
- **Vendor-neutral seam types** in `app/providers/adapters/base.py`: `RawTrade`, `RawQuote`,
  `HistoricalWindow`, `SymbolMatch`, and the neutral `SymbolNotTradable` / `NoDataForWindow`
  exceptions; the `MarketDataAdapter` Protocol broadened to the three methods.
- **`HistoricalProvider`** (`app/providers/historical.py`) implementing the `Provider` Protocol:
  merges a window's trades+quotes, maps real UTC epochs → **logical** seconds (monotonic
  non-decreasing offsets from window start), preserves **quote-before-trade** at the same instant,
  yields trades as `Side.UNKNOWN` (engine re-derives the aggressor). `scenario` = the
  `historical <SYM> <window>` row-6 source label.
- **WatchManager real-provider lifecycle** (`app/watch_manager.py`): `watch_with_provider(ticker,
  provider, speed)` builds an engine fed by any provider **without touching the sim registry**,
  tears down any prior watch first (switch/re-watch = fresh), and runs a cancellable
  `_feed_paced` feeder that paces by **logical gap ÷ speed**, clamped to
  `config.replay_pacing_cap_seconds`. The feeder is registered in `self._tasks`, so `stop()` and a
  switch already cancel it (no orphaned replay task — iter-0 lesson).
- **`main.py` historical branch:** `mode=="historical"` → gate on availability (503
  `provider_unavailable`) → validate params (`start`<`end`, parseable, `speed` ∈ config set) → **422
  no engine** → fetch off the event loop (`asyncio.to_thread`) → distinct **404** for
  `symbol_not_tradable` / `no_data_for_window` (no engine) → success builds the `HistoricalProvider`
  and watches. The old `provider_not_implemented` stub is **replaced for historical**; **live mode
  is unchanged**. The honest-failure exception was generalized to `RealDataError(reason, detail,
  status_code)` so each failure carries its own reason + status. The adapter is injected via a
  FastAPI dependency (`get_market_adapter`) so tests can override it.
- **`GET /symbols/search?q=`** (row 7): real tradable matches `[{symbol, name}, …]`, capped by
  `config.symbol_search_limit`; short/empty query, no creds, or any adapter error → `[]` (graceful
  free-text degrade, never fabricated).
- **Config additions** (`app/config.py`, no magic numbers): `allowed_replay_speeds` (⊇ UI
  {1,2,5,10}), `default_replay_speed`, `replay_pacing_cap_seconds`, `symbol_search_limit`,
  `symbol_search_min_query`.
- **Capture script + REAL fixture:** `apps/backend/scripts/capture_alpaca_fixture.py` (committed
  operator script) fetched a real window through the adapter and wrote
  `apps/backend/tests/fixtures/alpaca/F_20260602_150000_20260602_150200.json` — **real captured
  Ford market data** (65 trades, 1772 quotes; NOT synthesized).

**Frontend** (cockpit body unchanged across modes)
- `lib/api.ts`: `searchSymbols(q)`; `watchTicker` now returns the distinct failure `reason`.
- `lib/types.ts`: `SymbolMatch`, `FailureReason`.
- `components/SymbolSearch.tsx`: debounced (250ms) suggestions dropdown; free-text entry preserved.
- `components/TopBar.tsx`: uses `SymbolSearch` in Live/Historical; plain input in Simulated.
- `components/ProviderUnavailable.tsx`: generalized to a distinct amber honest panel per reason
  (provider unavailable / **not a tradable symbol** / **no data for that window**).
- `app/page.tsx`: tracks the distinct `reason` and renders the matching panel in place of the
  cockpit; a successful historical watch drives the existing `Cockpit`.

## Files Changed

**Created**
- `apps/backend/app/env.py` — stdlib load-if-missing `.env` loader.
- `apps/backend/app/providers/historical.py` — `HistoricalProvider` (epoch→logical mapping).
- `apps/backend/scripts/capture_alpaca_fixture.py` — committed operator capture script.
- `apps/backend/tests/fixtures/alpaca/F_20260602_150000_20260602_150200.json` — REAL fixture.
- `apps/backend/tests/test_historical_provider.py` — mapping + deterministic real-fixture replay.
- `apps/backend/tests/test_symbols_search.py` — search parsing/limit/degrade.
- `apps/backend/tests/fakes.py` — fake adapter + fixture loader (DI test seam).
- `apps/frontend/components/SymbolSearch.tsx` — debounced suggestions dropdown.

**Modified**
- `apps/backend/app/config.py` — replay-speed set/default, pacing cap, search limit/min-query.
- `apps/backend/app/providers/adapters/base.py` — neutral records + exceptions + broadened Protocol.
- `apps/backend/app/providers/adapters/alpaca.py` — `fetch_historical` + `search_symbols` (SDK lazy).
- `apps/backend/app/providers/adapters/__init__.py` — neutral `get_adapter()` accessor.
- `apps/backend/app/watch_manager.py` — `watch_with_provider` + cancellable paced feeder.
- `apps/backend/app/main.py` — historical branch, `/symbols/search`, `RealDataError`, adapter DI, `load_env`.
- `apps/backend/requirements.txt` — pinned `alpaca-py==0.43.4`.
- `apps/backend/.env` — credential-name fix *(untracked; NOT committed)*.
- `apps/backend/tests/conftest.py` — import + call the `.env` loader.
- `apps/backend/tests/test_real_data_gate.py` — historical distinct-reason + 422 + success + SDK-confinement tests.
- `apps/backend/tests/test_watch_manager.py` — historical-lifecycle tests.
- `config/install-security-policy.json` — allowlist `alpaca-py`.
- `apps/frontend/lib/api.ts`, `lib/types.ts`, `components/TopBar.tsx`, `components/ProviderUnavailable.tsx`, `app/page.tsx`.

## Tests Run

- **Backend:** `cd apps/backend && .venv/bin/python -m pytest tests/ -v` → **110 passed** (was 84;
  +26 new). Includes the deterministic real-fixture replay (Ford → `bid_absorption` @ 0.95,
  reproducible), timestamp-mapping + quote-before-trade, symbol-search parsing/limit/degrade,
  historical distinct-reason + 422 + success, WatchManager historical lifecycle (cancellable;
  stop/switch tear-down), and the alpaca-py-SDK single-module confinement guard.
- **Frontend:** `cd apps/frontend && npm run build` → compiled + type-checked clean.
- **Live external integration (operator creds present):** verified the REAL path end-to-end over
  HTTP — `POST /watch/F {historical}` fetched the real window and the feeder populated the cockpit
  (resolved to a real absorption state, REST views agree), `GET /symbols/search?q=AAP` returned
  real matches, `POST /watch/ZZZZNOPE {historical}` → 404 `symbol_not_tradable`,
  `POST /watch/AAPL {live}` → 503 `provider_not_implemented` (unchanged), sim `SIM-BUYER` → 200.
  The committed fixture is byte-for-byte the real adapter output (a live re-fetch reproduces the
  identical `bid_absorption` read).

## Known Issues / Limitations

- **Live confirmation is environment-dependent.** Real fetches require operator creds + network. In
  this dev environment both were present, so J-11 was confirmed live AND in-loop (deterministic
  fixture). A QA environment without creds/network will see real fetches fail honestly — the
  in-loop evidence then rests on the committed real-fixture replay test (offline, deterministic)
  plus the historical controls + honest states.
- **Datetime convention:** the historical window picker sends naive `YYYY-MM-DDTHH:MM`; the backend
  treats naive values as **UTC**. So an operator picking a US-market-hours window must enter the
  **UTC** time (e.g. 15:00 UTC = 11:00 ET). A market-local/tz picker is out of scope.
- **IEX spread reality:** the free IEX feed's top-of-book for high-priced names (e.g. AAPL) is
  often wide/noisy, so the engine honestly reads `unclear` there (the spread gate is calibrated for
  tight tapes and is **out of scope to change** — it would regress J-01–J-09). The committed fixture
  uses Ford (penny spread), which resolves to a clean `bid_absorption`. This is honest behavior, not
  a defect — real data + an honest read.
- **Replay pacing at speed 1** replays a window in roughly real time (a 2-min window ≈ 2 min);
  pick a higher speed (2/5/10) for a faster browser walkthrough. Engine math is unaffected (pacing
  is delivery-only).
- **Live streaming (J-12) + `GET /market/clock` + the market-closed J-14 case** remain out of scope
  (live mode still returns `provider_not_implemented`).
- **Symbol search uses Alpaca's read-only asset reference** (`get_all_assets`/`get_asset`) only — no
  order/execution/brokerage capability is touched (no-execution anti-goal holds). An unexpected
  vendor/network error during a historical fetch surfaces as a 500 (an honest error, never
  fabricated data).

## Suggested Next Phase

**J-12 live streaming** + `GET /market/clock` (data-contract row 8) and the market-closed honest
state (the 4th J-14 case): wire the Alpaca live websocket behind the same adapter seam, add the
`stale` status path (J-15), and replace the live-mode `provider_not_implemented` stub with the real
streaming provider — reusing the exact `watch_with_provider` lifecycle and the existing status
machinery. This completes the real-data journeys (J-11–J-15) on top of the seam proven here.
