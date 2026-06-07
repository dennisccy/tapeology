# goal-i_will_be_super_rich-iter-11 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-11
**Date:** 2026-06-07
**Agent:** developer
**Status:** complete

## What Was Built

Vendor responsiveness — the last three unbuilt Must-haves (J-28, J-29, J-30). All additive
hardening of existing seams; no new endpoint, route, page, nav element, or displayed engine value.

- **J-28 — a true call-level vendor deadline + actionable oversize message.** A real HTTP timeout
  is now applied at the vendor-call boundary inside the one adapter (`alpaca.py`), set on the SDK
  client's underlying `requests.Session` (the pinned `alpaca-py==0.43.4` exposes no per-request
  `timeout` kwarg — confirmed). A slow/large/CPU-bound response is cut off by the client itself
  (raising `requests.exceptions.Timeout`), mapped to a new neutral `VendorTimeout` the API turns
  into the existing row-9 `provider_timeout`. The outer `asyncio.wait_for` wrapper in `main.py`
  stays as the backstop. The HTTP deadline (`vendor_http_timeout_seconds=6.0`) is ≤ the wrapper
  bound (`vendor_call_timeout_seconds=8.0`), which is strictly < the frontend client timeout
  (12000ms) — a unit test asserts this ordering **from config**, never hardcoded. A Historical
  window that times out now returns the **actionable** message "that window is very high-volume —
  try a shorter range" (not a misleading generic retry), via the same failure path, with **no**
  engine created.

- **J-29 — fast historical load by design.** In `alpaca.py`: trades and quotes are now fetched
  **concurrently** (a 2-worker `ThreadPoolExecutor` inside the already-off-loop `fetch_historical`),
  so a fetch costs ≈ max(t_trades, t_quotes), not their sum. The **needless pre-flight** round-trip
  is folded out — `get_asset` is consulted **only** when the data fetch comes back empty (to
  decide unknown-symbol vs. empty-window), so a successful fetch is one round-trip. A bounded
  in-process **window cache** (LRU + TTL, keyed by symbol/start/end/feed) makes a re-watch of the
  same window near-instant and replays the **same real** `HistoricalWindow` (never fabricated). The
  historical-replay feeder (`_feed_paced`) now **fast-forwards** delivery of the first
  `warmup_min_events` events so the cockpit warms promptly — delivery pacing only; the engine sees
  the same events in the same order with the same logical timestamps, so features/state/confidence
  are byte-identical (a unit test proves it against a synchronous reference).

- **J-30 — warmed/cancellable symbol search.** Backend: the tradable-symbol universe is **warmed
  once at FastAPI startup** in the background (via a new neutral `warm_symbol_universe()` on the
  adapter seam — `main.py` never names the SDK or the universe cache), so the first search after a
  (re)start is not a cold stall. No-creds ⇒ a no-op (search stays `[]`); a warm failure is logged
  and swallowed (never crashes startup). The module-level `_ASSET_UNIVERSE` remains the **single**
  owner. Frontend: `searchSymbols` now takes an `AbortSignal`; `SymbolSearch.tsx` aborts the prior
  in-flight request on each new debounced lookup (real cancellation, no pile-up / out-of-order
  overwrite), reads its debounce-ms + min-query from `config.ts`, and an aborted request resolves
  to no result (never an error / stuck spinner).

## Files Changed

- `apps/backend/app/config.py` — new config constants (no magic numbers): `vendor_http_timeout_seconds`
  (real HTTP deadline), `frontend_watch_request_timeout_ms` (mirrored to make the ordering invariant
  testable), `historical_cache_max_entries` / `historical_cache_ttl_seconds` (window cache),
  `warmup_fast_forward_pace_seconds`, `symbol_universe_refresh_seconds`. Documents the backend<frontend
  ordering invariant.
- `apps/backend/app/providers/adapters/base.py` — new neutral `VendorTimeout` exception; added
  `warm_symbol_universe()` to the `MarketDataAdapter` Protocol (doc-only, vendor-free).
- `apps/backend/app/providers/adapters/alpaca.py` — HTTP timeout on the SDK session
  (`_with_http_timeout`); requests-timeout → `VendorTimeout` mapping (`_mapped_vendor_timeout`);
  concurrent trades+quotes fetch; folded pre-flight (lazy `get_asset` only on empty result); bounded
  LRU+TTL window cache (`_cache_get`/`_cache_put`/`_clear_caches`); `warm_symbol_universe()` +
  `_fetch_asset_universe()` (single-owner universe). SDK still confined to this one module.
- `apps/backend/app/main.py` — actionable historical oversize/timeout message (`HISTORICAL_OVERSIZE_DETAIL`),
  catching both the wrapper `TimeoutError` and the new `VendorTimeout`; background symbol-universe
  warm fired from the `lifespan` startup through the neutral seam (no SDK name in `main.py`).
- `apps/backend/app/watch_manager.py` — `_feed_paced` only: warm-up fast-forward of the first
  `warmup_min_events` deliveries, then normal pacing (delivery-only; determinism preserved). `_feed`,
  `_feed_live`, pause, and the stale watchdog are untouched.
- `apps/backend/tests/fakes.py` — `FakeAdapter` gains `warm_symbol_universe()` (+`warm_calls` counter),
  a `fetch_timeout` lever (raises `VendorTimeout`), and a `warm_raises` lever.
- `apps/backend/tests/test_vendor_responsiveness.py` — NEW: 32 tests covering J-28/J-29/J-30 (see below).
- `apps/backend/tests/test_vendor_timeout.py` — updated one assertion: the historical-fetch timeout
  message is now the actionable oversize variant (reason stays `provider_timeout`).
- `apps/frontend/lib/config.ts` — `SYMBOL_SEARCH_DEBOUNCE_MS` + `SYMBOL_SEARCH_MIN_QUERY` constants;
  documented the backend<frontend ordering invariant.
- `apps/frontend/lib/api.ts` — `searchSymbols(q, signal?)` with `AbortController` support; aborted ⇒ `[]`.
- `apps/frontend/components/SymbolSearch.tsx` — real per-lookup cancellation; reads debounce/min-query
  from config; enforces the client min-query.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **230 passed, 1 skipped** (iter-10 floor was 198 passed / 1 skipped; +32 new tests, 0 regressions).

Frontend: `cd apps/frontend && npx tsc --noEmit` → clean (0 errors). NOTE: `npm run build` was
deliberately NOT run — a harness `next dev` server is live on :3650 sharing `.next`; building would
corrupt its chunks (the iter-3/6/8/10 lesson). Type-check writes no `.next`.

New backend tests (`test_vendor_responsiveness.py`):
- J-28: HTTP-deadline constant is config-sourced; backend-effective bound < frontend bound (from
  config); the adapter injects the HTTP timeout on the SDK session; idempotent/defensive wrapper;
  requests.Timeout → neutral VendorTimeout; a historical VendorTimeout → actionable provider_timeout
  with NO engine; the actionable message is distinct from provider_unavailable.
- J-29: trades+quotes fetched concurrently (total ≈ max not sum, via a timed fake SDK); a successful
  fetch makes one round-trip (no get_asset on the hot path); the empty-result path consults get_asset
  once (tradable→no_data, 404→symbol_not_tradable); unknown/empty still map correctly via the route;
  cache hit skips the vendor and returns the SAME real window; cache keyed by window (miss on a
  different range); TTL expiry → miss; bounded LRU eviction; warm-up fast-forward yields identical
  engine features/state/confidence as a synchronous reference; warm-up does not wait out logical
  gaps; the fast-forward bound is config-sourced.
- J-30: warm-then-search does not re-fetch; warm is a no-op without creds; warm is idempotent; warm
  swallows a vendor error (never raises); the lazy universe is single-owner / fetched once; backend
  min-query drops a too-short query (no vendor call); a search vendor error degrades to `[]`; the
  lifespan startup warms via the neutral seam; a warm failure does not crash startup; `main.py` does
  not name the SDK for the warm.
- No-fabrication/SSOT guards: a cache hit replays unchanged real records; the concurrent fetch
  preserves record content.

## Live credentialed verification (creds present in apps/backend/.env)

Ran a real isolated backend (port 8791, killed afterward) against the live Alpaca IEX feed:
- **J-30 universe warm + J-13 search** — `GET /symbols/search?q=AAPL` returned real Alpaca matches
  immediately after startup (the startup warm populated the universe).
- **J-29 first historical fetch** — `POST /watch/F` (2-minute window) populated the engine in ~1.0s
  (concurrent fetch + folded pre-flight).
- **J-29 cache hit** — re-watching the same window returned in **0.013s** (~75× faster), confirming
  the near-instant re-watch; the warm-up fast-forward advanced the logical clock to ~12s within 1s
  of wall-clock.
- **Market clock** — `GET /market/clock` returned a real `is_open:false` + next open (HTTP-timeout
  wrapper applied, no regression).

(J-28's oversize-against-live-vendor leg and J-29's market-open-minute busy-window leg remain
operator/browser-gated; the deterministic in-loop proofs use the slow/timeout/timed doubles.)

## Known Issues

- **Operator-env test note:** because real creds are present in `apps/backend/.env`, the two
  `with TestClient(app)` tests that do NOT override the adapter (`test_pause_api.py`) fire a real
  background `get_all_assets()` warm during the run. It is non-blocking, suppressed, HTTP-timeout
  bounded, and does not affect assertions; in a no-creds CI env it is a clean no-op. All new
  warm/lifespan tests override the adapter with a FakeAdapter and are fully hermetic. Suite is
  stable across repeated runs (verified 3×, ~19s, no flakiness in the timing-sensitive tests).
- **Live-socket teardown untouched** (iter-4 deadlock lesson): this iteration only touched the
  historical-fetch + search paths; `stream_live`'s bounded graceful close and `_feed_live` were not
  modified.
- **Concurrency lives inside `fetch_historical`** (kept sync, called via one `to_thread`) rather
  than making the adapter method async — this preserves the `fetch_historical(symbol, start, end)`
  signature the existing `fetch_calls` / window-resolution / real-data-gate tests assert against,
  while still overlapping the two vendor calls via an internal thread pool.

## Resume Re-verification (2026-06-07)

The prior dev run finished but the pump aborted on a heartbeat timeout *after* the developer
completed (not a code problem). On re-dispatch the existing implementation was re-verified against
the plan — no rebuild, no re-architecture:

- **Backend suite re-run:** `cd apps/backend && .venv/bin/python -m pytest tests/` →
  **230 passed, 1 skipped** (unchanged from the original run; iter-10 floor 198 + 32 new). The
  new `test_vendor_responsiveness.py` alone → **32 passed**.
- **Frontend type-check re-run:** `cd apps/frontend && npx tsc --noEmit` → **0 errors** (no `.next`
  written, per the shared-dev-server lesson).
- **Code re-confirmed present & matching the plan:** the J-28 real `requests.Session`-level HTTP
  deadline (`alpaca._with_http_timeout`) + neutral `VendorTimeout` + actionable
  `HISTORICAL_OVERSIZE_DETAIL`; the config-asserted backend<frontend ordering invariant; the J-29
  concurrent `ThreadPoolExecutor` fetch + folded `_require_tradable` (empty-result only) + LRU/TTL
  window cache + `_feed_paced` warm-up fast-forward (delivery-only, determinism proven); the J-30
  `lifespan` background `warm_symbol_universe()` through the neutral seam (single-owner
  `_ASSET_UNIVERSE`) + the frontend `AbortController` cancellation in `searchSymbols` / `SymbolSearch.tsx`.
- **Anti-goal spot-checks:** `grep` confirms the Alpaca SDK is imported in `alpaca.py` ONLY and that
  `main.py` names neither the SDK nor `_ASSET_UNIVERSE` (the `test_main_does_not_name_the_vendor_sdk_for_the_warm`
  guard also enforces this). No corrective changes were required.
