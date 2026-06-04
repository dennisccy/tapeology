# Phase goal-i_will_be_super_rich-iter-4 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-4
**Date:** 2026-06-04
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

<!-- No frontend file changed this iteration. The surfaces below are EXISTING elements whose
     observable behavior changed because the backend Live "Watch" action now streams real data.
     Every "What to Test" is a concrete click-path with an expected result. -->

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | Live mode "Watch" button (`app/page.tsx` `handleWatch` → `watchTicker`) | Changed behavior | Backend live branch now streams instead of refusing (`provider_not_implemented` 503 removed) | Select **Live**, enter a tradable symbol, click **Watch**; confirm the `<Cockpit>` mounts (tape panels appear) instead of an error banner — `POST /watch/<SYM>` returns `{scenario:"live <SYM>", status:"watching"}` |
| `/` | `TopBar` status dot (`STREAM_DOT`, reads `snapshot.stream_status`) | Changed behavior | The `live`/`stale` values now originate from a real live feed (row-6 `stream_status`) | On a successful live watch, confirm the dot is **emerald** (`live`); during a feed lull beyond the stale gap confirm it turns **amber** (`stale`) and returns to **emerald** when events resume — verifiable on the real socket / gated run |
| `/` | `TopBar` watched-source label (renders `snapshot.scenario`) | Changed behavior | Backend now emits `live <SYM>` as the row-6 source descriptor | On a live watch of `F`, confirm the label reads exactly `scenario: live F` |
| `/` | `MarketStatusIndicator` (Live mode, `GET /market/clock`) | No change (re-verify) | Live pre-flight reuses the existing clock; indicator must still render | Switch to **Live**; confirm the market-open/closed indicator renders with a status (open or closed + next open) |
| `/` | `SymbolSearch` (Live mode) | No change (re-verify) | Live mode reveals the existing symbol search (J-13) | Switch to **Live**; type a query; confirm matching symbols appear and a selection fills the symbol box |
| `/` | Mode selector (sim / historical / live) | No change (re-verify) | J-10 must still reveal Live controls without regression | Click the data-source selector; confirm choosing **Live** reveals the symbol search + market-status indicator |
| `/` | `Cockpit` teardown on Stop / switch (`teardownActiveWatch` → `DELETE /watch/<SYM>`) | Changed behavior | Stop/switch now also closes the real vendor socket (no leak) | After a live watch, click **Stop** (or switch symbol); confirm the cockpit clears / dot goes `closed` and a subsequent `GET /watch/<SYM>/state` 404s |

---

## Backend-Only Changes (No UI Impact)

<!-- These deliver the capability but have no new UI surface of their own. -->

- `app/providers/base.py` — added the async `AsyncProvider` Protocol (sync `Provider` 0-diff) — no UI surface affected.
- `app/providers/live.py` (**NEW**) — `LiveProvider` maps the adapter's async neutral records onto the engine's logical timeline — no UI surface affected.
- `app/providers/adapters/base.py` — added `LiveRecord` type + `stream_live` on the `MarketDataAdapter` Protocol — no UI surface affected.
- `app/providers/adapters/alpaca.py` — added `stream_live()` (lazy `StockDataStream`, subscribe trades+quotes, bounded graceful socket close) — the SOLE vendor module; no UI surface affected.
- `app/watch_manager.py` — added `watch_with_async_provider` + `_feed_live` (async feeder + stale watchdog + socket-close-on-cancel) — drives row-6 `stream_status`; the value surfaces via the existing TopBar dot, no new surface.
- `app/main.py` — `POST /watch/{ticker}` live branch (`_watch_live`): replaced the 503 refusal with the real streaming path (no-creds → `provider_unavailable`; market-closed → `market_closed` + next open) — consumed by the existing `watchTicker` call; no new surface.
- `app/config.py` — added `stale_gap_seconds` (default 10.0) — internal tunable; no UI surface affected.
- `pyproject.toml` — registered the `integration` pytest marker — build config; no UI impact.
- `tests/fakes.py`, `tests/test_live_provider.py` (NEW), `tests/test_watch_manager.py`, `tests/test_real_data_gate.py`, `tests/test_live_integration.py` (NEW) — test doubles + hermetic/gated tests — no UI impact (test-only, never wired into the prod path).

---

## Summary

- **Frontend surfaces changed:** 4 existing surfaces with changed *behavior* (Live Watch button, status dot, source label, teardown); 3 re-verify-only (market indicator, symbol search, mode selector). **0 frontend files modified.**
- **New pages/routes:** 0
- **Modified components:** 0 (no frontend code change — behavior changes are driven by the backend)
- **Navigation changes:** no
- **Backend-only changes:** 9 files (1 new provider module, 1 new test module, 1 gated test module, plus seam/adapter/feeder/route/config/build edits)
