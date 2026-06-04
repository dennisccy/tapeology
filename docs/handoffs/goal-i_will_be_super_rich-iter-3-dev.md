# goal-i_will_be_super_rich-iter-3 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-3
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built

**Market clock (Data Contract row 8) — built end-to-end, registered→built:**
- `MarketClock` vendor-neutral record in `providers/adapters/base.py` (`is_open: bool`, `next_open`/`next_close` as ISO-8601 UTC strings) + `get_market_clock()` added to the `MarketDataAdapter` Protocol.
- `AlpacaAdapter.get_market_clock()` via `TradingClient.get_clock()` — a **read-only** reference call (no order placed/echoed); vendor tz-aware datetimes serialized to ISO-8601 UTC (`…Z`). The `alpaca` SDK import stays **lazy and confined** to `alpaca.py`.
- `GET /market/clock` endpoint (the **one** canonical serving endpoint): creds present → `{available:true, is_open, next_open, next_close}`; no creds → `{available:false, null…}`; adapter/network error → degrades to the same `available:false` (never a fabricated open/closed). Blocking vendor call runs off the event loop via `asyncio.to_thread`.

**Market-closed pre-flight gate — completes J-14 (4/4):**
- The `live` branch of `POST /watch/{ticker}` now reads `adapter.get_market_clock()` (same computing owner, **not** a second endpoint) between the no-creds check and the existing not-implemented refusal. An **authoritative** closed clock (`is_open is False`) → `RealDataError("market_closed", "market is closed", 409, next_open=…)` with **no engine created**. A degraded/unreachable clock is treated as indeterminate and falls through to `provider_not_implemented` (it is **never** reported as closed — that would fabricate a session).
- `RealDataError` extended with an optional `next_open`; the exception handler adds `next_open` to the JSON body **only** for `market_closed`, so the other three reasons' bodies stay byte-for-byte unchanged.
- New config tunable `CONFIG.market_closed_status_code = 409` (no inline literal).

**Frontend — real Live market-status indicator + honest closed-market panel:**
- New `MarketStatusIndicator` component: fetches `GET /market/clock` on mount + on a 60s interval **only while in Live mode**, renders **open** (emerald) / **closed + next open** (amber) / **unavailable** (amber) / in-flight placeholder. Replaces the prior hardcoded "market unavailable" stub. Poll is torn down on unmount/mode-change (the component is conditionally mounted, so the effect cleanup clears the interval — iter-0 resource-leak lesson).
- `getMarketClock()` reader in `lib/api.ts`; any failure → `available:false` (never a fabricated status).
- `"market_closed"` added to the `FailureReason` union, to `HONEST_REASONS`, and as a new `ProviderUnavailable` case rendering "market is closed" + the next-open time. `next_open` is threaded from the backend body → `WatchResult.nextOpen` → the `failure` state → the panel.
- New `lib/datetime.ts` `formatMarketTime()` helper (renders the ISO-8601 UTC instant in the operator's local zone with an explicit zone label, so "next open" is never mis-read).

## Files Changed

**Backend — modified**
- `apps/backend/app/providers/adapters/base.py` — added `MarketClock` record + `get_market_clock()` on the Protocol.
- `apps/backend/app/providers/adapters/alpaca.py` — implemented `get_market_clock()` (lazy SDK import) + `_to_iso_utc()` helper; added `from datetime import timezone`.
- `apps/backend/app/main.py` — added `GET /market/clock` (+ `_clock_unavailable` helper); inserted the live market-closed pre-flight gate; extended `RealDataError`/handler with `next_open`.
- `apps/backend/app/config.py` — added `market_closed_status_code` (409).
- `apps/backend/tests/fakes.py` — `FakeAdapter` gained a configurable clock (`clock` / `clock_raises`) + `get_market_clock()`.
- `apps/backend/tests/test_real_data_gate.py` — reconciled the live+creds test to be hermetic (FakeAdapter clock, no real network); added market-closed / degraded-clock / 4-way-distinct / non-market_closed-body-unchanged tests.

**Backend — created**
- `apps/backend/tests/test_market_clock.py` — `GET /market/clock` matrix (open / closed-with-next-open / no-creds-nulls / adapter-error-degrade).

**Frontend — modified**
- `apps/frontend/lib/types.ts` — `market_closed` in `FailureReason`; new `MarketClock` interface.
- `apps/frontend/lib/api.ts` — `getMarketClock()`; `nextOpen` on `WatchResult` (parsed from `next_open`).
- `apps/frontend/components/TopBar.tsx` — replaced the hardcoded stub pill with `<MarketStatusIndicator />`.
- `apps/frontend/components/ProviderUnavailable.tsx` — `market_closed` copy case + `nextOpen` prop.
- `apps/frontend/app/page.tsx` — `market_closed` in `HONEST_REASONS`; thread `nextOpen` into `failure` → panel.

**Frontend — created**
- `apps/frontend/components/MarketStatusIndicator.tsx` — the Live market-status indicator (poll + cleanup).
- `apps/frontend/lib/datetime.ts` — `formatMarketTime()` shared formatter.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **118 passed** (110 baseline + 8 net new), 0 failed.

Command: `cd apps/frontend && npm run build`
Result: **Compiled successfully**, types valid, 4/4 static pages generated.

**Live external-integration test (real Alpaca creds present in `apps/backend/.env`):**
- `AlpacaAdapter().get_market_clock()` → `is_open=False`, `next_open="2026-06-04T13:30:00Z"`, `next_close="2026-06-04T20:00:00Z"` (`is_open` is `bool`, `next_open` is `str`). Read-only — no order placed.
- Running server (`uvicorn`, port 8765): `GET /market/clock` → `{"available":true,"is_open":false,"next_open":"2026-06-04T13:30:00Z","next_close":"2026-06-04T20:00:00Z"}`; `POST /watch/AAPL {"mode":"live"}` → **HTTP 409** `{"detail":"market is closed","reason":"market_closed","next_open":"2026-06-04T13:30:00Z"}`; `GET /tape/AAPL/state` after → **404** (no engine). The market is closed at run time, so the J-14 closed branch is live-verifiable in browser QA.

**Anti-goal guardrails verified independently (`git diff`):**
- `import alpaca` and `ALPACA_API_*` confined to `providers/adapters/alpaca.py` only (confinement tests green, unchanged).
- `main.py` / `adapters/base.py` / `config.py` reference no vendor name.
- Engine, `serializers.py`, `providers/base.py`, `providers/simulated.py`, `providers/historical.py` show an **empty diff** (sim + historical paths behavior-identical).
- No secret committed (`.env` untracked; `.env.example` unchanged). No broker/order/execution code — the clock call is read-only.

## Known Issues

- **Live streaming (J-12) remains intentionally out of scope.** A live watch with creds + an **open** market still returns `provider_not_implemented` (503). This is the honest iter-4 boundary, not a regression — the async socket/feeder is deferred to iter-4. The market clock built here is iter-4's pre-flight "is the market open" check.
- **J-15 (stale-on-gap watchdog)** is untouched (belongs with the live feeder in iter-4). The `stale` dot mapping already exists.
- **Browser QA of the closed-market panel depends on wall-clock.** At the time of this handoff the US market is closed, so the closed branch is browser-verifiable now; if QA runs during market hours, the indicator will show "open" and the live watch will return `provider_not_implemented` — in that case the closed-refusal branch is covered authoritatively by the deterministic backend test (`FakeAdapter` clock=closed), consistent with goal.md's "closed-market path is verifiable without a live feed."

## Suggested Next Phase

**iter-4 — the live half (J-12 + J-15).** Introduce the async provider/feeder seam (today's `Provider.stream()` is synchronous; a live feed is async/unbounded), wire the real Alpaca live WebSocket behind the vendor-neutral adapter, and add the stale-on-gap → recover watchdog (fabricating no trades during a lull). Reuse this iteration's `get_market_clock()` as the live pre-flight open-check and the existing cancellable feeder teardown so a live socket is never orphaned on switch/stop. Real-socket behavior is operator/gated (market hours + creds).
