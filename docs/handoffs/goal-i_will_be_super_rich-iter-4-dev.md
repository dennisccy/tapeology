# goal-i_will_be_super_rich-iter-4 Dev Handoff

**Phase:** goal-i_will_be_super_rich-iter-4
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built

The **live real-time streaming** half of the product — closing the last two failing must-have
journeys, **J-12** (stream a real live ticker) and **J-15** (a live-feed gap shows `stale`, then
recovers) — with **zero changes** to the engine, classifier, serializers, or the synchronous
providers.

- **Async provider seam (`providers/base.py`).** Added an `AsyncProvider` Protocol
  (`stream() -> AsyncIterator[Event]`) — the async/unbounded counterpart to the existing
  synchronous `Provider`. The sync `Provider` class is untouched (0-diff). The engine still
  consumes each event through the unchanged `engine.process_event`.
- **`LiveProvider` (`providers/live.py`, NEW, vendor-neutral).** Consumes an adapter's async
  stream of neutral `RawTrade` / `RawQuote` records and yields ordered `QuoteEvent` / `TradeEvent`,
  mapping each real UTC epoch onto the engine's logical timeline (first event → 0.0, offsets
  clamped monotonic non-decreasing). Trades carry `Side.UNKNOWN` (the engine re-derives the
  aggressor). `scenario = "live <SYM>"`. Imports no vendor SDK. Cascades `aclose()` into the
  underlying adapter stream so the socket closes even on mid-iteration cancel.
- **Alpaca live method (`providers/adapters/alpaca.py` — the SOLE vendor module).** Added
  `async def stream_live(symbol)` using `alpaca.data.live.StockDataStream` (lazy import), which
  subscribes to **trades + quotes for the one symbol** (market data ONLY — no order/account/
  position call) and bridges the SDK's async callbacks into a vendor-neutral async record stream
  via a queue. On teardown it performs a **bounded graceful close** (`stop_ws()` → bounded wait
  for the run loop → cancel-if-needed → bounded `close()`) so the vendor socket is genuinely
  closed and the close can never hang. Declared `stream_live` on the `MarketDataAdapter` Protocol.
- **Async live feeder + stale watchdog (`watch_manager.py`).** Added `watch_with_async_provider`
  + `_feed_live`: tears down any prior watch first (orphan/leak prevention), processes each event
  and ensures the status reads `live`, flips to `stale` when no event arrives within
  `CONFIG.stale_gap_seconds` (fabricating **no** trades during the lull), flips back to `live` on
  resume, and on cancel sets `closed` and `aclose()`s the stream (closing the vendor socket). A
  single background "puller" task owns the generator so the stale-gap `wait_for` times out on the
  queue, never on the generator itself.
- **`POST /watch/{ticker}` live branch (`main.py`).** Replaced the iter-3
  `provider_not_implemented` (503) refusal with the real path via a new `_watch_live` helper:
  no creds → `provider_unavailable` (503); authoritative market-closed → `market_closed` (409 +
  next open, reusing the existing clock — no second clock); otherwise build the `LiveProvider`
  from `adapter.stream_live(...)` and start it. Returns `{ticker, scenario: "live <SYM>",
  status: "watching"}`. No sim fall-back on any failure.
- **Config (`config.py`).** Added `stale_gap_seconds` (default `10.0`) — the live stale-watchdog
  timeout (a named config field; no inline literal).

## Files Changed

- `apps/backend/app/providers/base.py` — added `AsyncProvider` Protocol + `AsyncIterator` import (sync `Provider` 0-diff).
- `apps/backend/app/providers/live.py` — **NEW.** `LiveProvider` async neutral→logical mapping.
- `apps/backend/app/providers/adapters/base.py` — added `LiveRecord` type + `stream_live` on the `MarketDataAdapter` Protocol.
- `apps/backend/app/providers/adapters/alpaca.py` — added `stream_live()` (lazy `StockDataStream`, subscribe trades+quotes, bounded graceful socket close) + `LIVE_TEARDOWN_GRACE_SECONDS` constant.
- `apps/backend/app/watch_manager.py` — added `watch_with_async_provider` + `_feed_live` (stale watchdog + socket-close-on-cancel).
- `apps/backend/app/main.py` — added `_watch_live`; replaced the live `provider_not_implemented` refusal with the real streaming path.
- `apps/backend/app/config.py` — added `stale_gap_seconds`.
- `apps/backend/pyproject.toml` — registered the `integration` pytest marker.
- `apps/backend/tests/fakes.py` — added `FakeLiveSocket`, `FakeLiveProvider`, and `FakeAdapter.stream_live` (test-only doubles, never wired into prod).
- `apps/backend/tests/test_live_provider.py` — **NEW.** Mapping + full hermetic live pipeline + SSOT (4 tests).
- `apps/backend/tests/test_watch_manager.py` — added 4 live-feeder tests (stale→recover, socket-close lifecycle, switch, registry isolation).
- `apps/backend/tests/test_real_data_gate.py` — updated the 3 live-branch tests (open-market & degraded-clock now start a stream; refusal-body test drops the live case) + added 2 anti-goal guards (live-SDK confinement, no-execution/account API).
- `apps/backend/tests/test_live_integration.py` — **NEW.** Operator/gated real Alpaca live-socket check (`@pytest.mark.integration`).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **128 passed, 1 skipped** (the gated integration test skips without opt-in). iter-3 baseline was 118 passed → +10 new passing tests, 0 regressions.

**0-diff guarantee verified** (`git diff --stat`): `app/engine/`, `app/serializers.py`,
`app/providers/simulated.py`, `app/providers/historical.py` show an empty diff; the sync
`Provider` class in `base.py` is unchanged.

**Vendor confinement verified** (`git grep`): `StockDataStream`, `import alpaca`, and
`ALPACA_API_KEY` / `ALPACA_API_SECRET` each appear in **only** `providers/adapters/alpaca.py`.

### External integration (operator/gated) — RUN and PASSED ✅

Contrary to the plan's Assumption #2 (which expected the market closed today), at the time of
implementation the **US market was OPEN** (`is_open: True`, next close `2026-06-04T20:00:00Z`)
and credentials were present, so the gated real-socket check was actually executed:

```
TAPEOLOGY_LIVE_INTEGRATION=1 TAPEOLOGY_LIVE_SYMBOL=F \
  .venv/bin/python -m pytest tests/test_live_integration.py -v
=> 1 passed in 3.16s
```

The real Alpaca live WebSocket (`wss://stream.data.alpaca.markets/v2/iex`) connected, subscribed
to Ford (F) trades+quotes, and within ~2s the engine read **`stream_status == "live"`** with real
trades flowing (count 1→4→6) and a real penny spread (bid 15.51 / ask 15.52), classifying a valid
tape state, then tore down cleanly (`data stream stopped`, socket closed, no leak). Also verified
end-to-end on a real uvicorn server: `POST /watch/F {"mode":"live"}` →
`{"ticker":"F","scenario":"live F","status":"watching"}`, then `DELETE` → stopped. **This is
genuine real-socket evidence for J-12, not a mock.** (A wide-spread / cold-start name honestly
reads `unclear` at low confidence — correct per the iter-2 IEX lesson, not a defect.)

J-15's stale→recover **state machine** is proven hermetically in-loop (a real natural >10s feed
gap for a liquid name does not occur during active market hours, so the deterministic fake is the
appropriate in-loop proof — exactly as the spec specifies); the live read it builds on is
confirmed by the gated run above.

## Known Issues

- **Alpaca free tier allows ONE concurrent live WebSocket.** Two simultaneous live watches (or a
  leftover zombie from an unclean kill) will starve each other of data. The bounded graceful close
  prevents zombies in normal operation; an operator running the gated test should ensure no other
  live socket is open. (Single-symbol live is the spec's scope; multi-symbol live is out of scope.)
- **`stream_live` teardown deliberately does NOT call the SDK's `unsubscribe_*()`.** Those methods
  run `asyncio.run_coroutine_threadsafe(...).result()`, which **deadlocks** the event loop when
  invoked from the loop thread (as our generator finally is). Closing the socket drops all
  subscriptions anyway; this is documented in the adapter and is load-bearing — do not re-add it.
- **Auto-reconnect of a dropped socket is not implemented** (out of scope per the spec). A dropped
  socket honestly surfaces as `stale` until events resume or the watch is stopped.
- **Frontend: no code change** (see the frontend handoff). The existing TopBar dot already renders
  `live` (emerald) / `stale` (amber) from the canonical `snapshot.stream_status`, and `watchTicker`
  already handles a successful live watch — verified, no gap found.

## Suggested Next Phase

With J-12 and J-15 closed and all 13 required-still-passing journeys intact, the full must-have
journey set (J-01–J-15) is complete — the goal-evaluator can consider **GOAL_ACHIEVED**. If
continuing, the next natural step is one of the explicitly-later `docs/goal.md` items (Level 2 /
`BookLevelEvent` + `liquidity_pull_score`, or the predictive-edge replay harness), none of which
are required for the current goal.
