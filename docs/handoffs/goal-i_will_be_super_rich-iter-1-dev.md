# goal-i_will_be_super_rich-iter-1 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-1
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built

First real-data slice — the seam, the credentials/availability contract, the honest
no-credentials failure state, and the data-source selector UI. **The engine and every
canonical read (`/state`, `/features`, `/summary`, `/events`, `WS /stream`) are untouched.**

**Backend**
- **Vendor-neutral adapter seam** — `app/providers/adapters/base.py` defines a
  `MarketDataAdapter` Protocol (`name` + `is_available()`). The engine/API depend only on this
  interface; no vendor SDK leaks outward.
- **Single concrete adapter** — `app/providers/adapters/alpaca.py` (`AlpacaAdapter`): env-only
  credential detection. `is_available()` is `True` only when **both** `ALPACA_API_KEY` and
  `ALPACA_API_SECRET` are present and non-blank. **No Alpaca SDK is imported or installed**
  (no new dependency, no supply-chain gate). This is the **only** module where the `ALPACA_*`
  names appear (enforced by a test).
- **Canonical `real_data_available()`** — derived from `AlpacaAdapter().is_available()`,
  evaluated fresh on each call. The one source for the row-9 availability state.
- **Optional `{mode, start, end, speed}` watch body** on `POST /watch/{ticker}` (`WatchRequest`
  Pydantic model, all fields optional, `mode` defaults to `"sim"`).
- **No-credentials gate** — a `live`/`historical` watch with `real_data_available()` False
  raises **before any engine is created** → **HTTP 503** `{"detail": "real-data provider
  unavailable", "reason": "provider_unavailable"}`. No snapshot/trade/quote synthesized, no sim
  fall-back. A `live`/`historical` watch **with** creds present returns a distinct 503
  `provider_not_implemented` (real serving is J-11/J-12) — still never a fabricated cockpit.
- **`apps/backend/.env.example`** — documents `ALPACA_API_KEY=`, `ALPACA_API_SECRET=` (empty)
  and `ALPACA_FEED=iex`. The only committable env file; no key value is committed.

**Frontend**
- **Data-source selector** in the TopBar — exactly three modes **Live / Historical /
  Simulated**, default **Simulated**.
- **Mode-specific control reveal** — Simulated: ticker input; Live: symbol search +
  market-status indicator; Historical: symbol search + date + start/end time + replay-speed.
  The cockpit body is identical across modes.
- **Honest non-cockpit state** — a Live/Historical Watch that returns 503 renders the
  `ProviderUnavailable` panel **in place of** the cockpit (never a fabricated cockpit, never a
  silent fall-back to Simulated).
- **Market-status indicator (Live)** — static honest **"unavailable"** (no clock call, no
  fabricated open/closed; the real `GET /market/clock` is deferred to J-12).
- **Watch-lifecycle hardening (iter-0 lesson)** — a new Watch, or switching the data source /
  symbol, FIRST tears down the prior watch (`DELETE /watch/{prev}`) and closes its WS before
  starting the new one.

## Files Changed

**Created**
- `apps/backend/app/providers/adapters/__init__.py` — adapter-seam package marker.
- `apps/backend/app/providers/adapters/base.py` — vendor-neutral `MarketDataAdapter` interface.
- `apps/backend/app/providers/adapters/alpaca.py` — `AlpacaAdapter` + canonical `real_data_available()`; the sole home of the `ALPACA_*` names.
- `apps/backend/.env.example` — credential variable names with empty values; `ALPACA_FEED=iex`.
- `apps/backend/tests/test_real_data_gate.py` — 15 tests (gate, no-engine, env presence/absence, single-module confinement).
- `apps/frontend/components/DataSourceSelector.tsx` — the 3-way segmented control.
- `apps/frontend/components/ProviderUnavailable.tsx` — the "real-data provider unavailable" non-cockpit panel.

**Modified**
- `apps/backend/app/main.py` — `WatchRequest` body + `RealDataUnavailableError` (+ handler); `watch()` routes sim vs. real and raises the 503 gate before creating an engine. Read/stream endpoints untouched.
- `apps/frontend/app/page.tsx` — holds `mode`; tears down the prior watch on Watch/switch; renders `ProviderUnavailable` on a 503.
- `apps/frontend/components/TopBar.tsx` — hosts the selector + per-mode controls + Live market-status indicator.
- `apps/frontend/lib/api.ts` — `watchTicker(ticker, params?)` sends a body for real modes (none for sim) and distinguishes the 503 `provider_unavailable` result.
- `apps/frontend/lib/types.ts` — `DataSourceMode` + `WatchParams`.

## Tests Run

**Backend** — Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **83 passed, 0 failed** (68 prior + 15 new; no regressions).

**Frontend** — Command: `cd apps/frontend && npm run build`
Result: **Compiled successfully**, types valid, 4/4 static pages generated.

**Live HTTP smoke (real uvicorn, no creds, port 8765)** — all exact:
- `POST /watch/SIM-BUYER` (no body) → `200 {"scenario":"buyer_control","status":"watching"}`
- `POST /watch/AAPL {"mode":"live"}` → `503 {"detail":"real-data provider unavailable","reason":"provider_unavailable"}`
- `GET /tape/AAPL/state` (after refusal) → `404` (proves **no engine created**)
- `POST /watch/AAPL {"mode":"historical",…}` → `503 provider_unavailable`
- `POST /watch/AAPL {"mode":"bogus"}` → `422` literal_error
- Frontend dev server booted (`next dev`, wired to the backend) and served `GET / 200`.
All smoke servers were killed; ports 8765/3765 confirmed free.

## Known Issues

- **No live/historical *serving* this iteration** (by design). With creds present, the
  real-mode watch returns 503 `provider_not_implemented` rather than a cockpit — the real
  providers land with J-11/J-12. Verification is intentionally **credentials-absent**.
- **Market-status indicator is static "unavailable"** (Assumption #2). It does not call a clock
  endpoint; the real open/closed status arrives with J-12 (`GET /market/clock`).
- **Historical date/time/speed controls render and feed the (rejected) watch body but drive no
  real fetch** (Assumption #5) — symbol entry is free-text only (vendor search is J-13).
- **Existing `apps/backend/.env` uses `ALPACA_SECRET_KEY`**, not the adapter's
  `ALPACA_API_SECRET`. It is **not loaded** by the app (no dotenv loader; `start-backend.sh`
  does not source it), so it does not affect the no-creds verification. When real creds are
  configured later, they must use the `.env.example` names (`ALPACA_API_KEY` /
  `ALPACA_API_SECRET`).
- **J-14 is intentionally partial** — only the no-credentials path is implemented/verified this
  iteration; unknown-symbol / empty-window / market-closed land with J-13/J-11/J-12.

## Suggested Next Phase

Wire the first **real provider behind the seam** — the historical-replay provider (J-11) is the
safest next slice because it is reproducible for a fixed symbol + past window and needs no live
market hours: install `alpaca-py` (through the supply-chain gate) inside the single
`adapters/alpaca.py` module, fetch a window's real trades/quotes, map their real timestamps onto
the engine's logical timeline, and feed the **same** `TapeEngine` through a new
`HistoricalProvider` — turning the credentials-present branch from `provider_not_implemented`
into a populated cockpit, with `GET /symbols/search` (J-13) added for the symbol box.
