"""FastAPI app: watch a ticker, read the engine snapshot over REST, stream it over WS.

Every read endpoint serves a pure projection of the engine's single snapshot via
``app.serializers`` — none recompute a value. ``/state`` and ``/features`` are the canonical
reads; ``/summary`` and ``WS /stream`` re-expose the same snapshot read-only. Unknown tickers
and not-watched reads return explicit errors — no fabricated data.

Real-data modes (``live`` / ``historical``) route only through the vendor-neutral adapter seam
(never the sim registry). ``historical`` fetches a real past window from the adapter and replays
it through the SAME engine (J-11); ``GET /symbols/search`` offers real tradable suggestions
(J-13). Every real-data failure is an explicit, distinct error with NO engine created — missing
creds, an untradable symbol, or an empty window each surface their own ``reason`` and never a
fabricated cockpit.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import CONFIG
from .env import load_env
from .providers.adapters import MarketDataAdapter, get_adapter
from .providers.adapters.base import NoDataForWindow, SymbolNotTradable, VendorTimeout
from .providers.historical import HistoricalProvider
from .providers.live import LiveProvider
from .serializers import (
    serialize_events,
    serialize_features,
    serialize_history,
    serialize_state,
    serialize_stream,
    serialize_summary,
)
from .watch_manager import UnknownTickerError, WatchManager

# Make uvicorn (and any importer) see the operator's apps/backend/.env without sourcing it by
# hand. Load-if-missing: never overrides an already-set var, so the test suite stays hermetic.
load_env()

logger = logging.getLogger(__name__)


class WatchRequest(BaseModel):
    """Optional ``POST /watch`` body selecting the data-source mode.

    Backward compatible: no body / ``{}`` / ``mode == "sim"`` is the existing simulated watch.
    ``mode == "historical"`` replays a real past window: ``start`` / ``end`` (ISO date-times)
    and ``speed`` (one of the config-allowed replay speeds) are required/validated. An
    unrecognized ``mode`` is rejected by the ``Literal`` as a 422 — never a silent default into
    a real feed.
    """

    mode: Literal["sim", "live", "historical"] = "sim"
    start: str | None = None
    end: str | None = None
    speed: float | None = None


class SpeedRequest(BaseModel):
    """Body for ``POST /watch/{ticker}/speed`` (J-32): the new replay speed for a RUNNING watch.

    ``speed`` is validated against ``CONFIG.allowed_replay_speeds`` in the route (out-of-set ⇒ 422),
    so the allowed set stays backend-authoritative (the frontend control disable is only a
    courtesy). It is a delivery-pacing change only — never a displayed engine value."""

    speed: float


class RealDataError(Exception):
    """Refuse a real-mode watch with an explicit, distinct non-cockpit response instead of
    fabricating a snapshot (no-fabricated-data anti-goal). Carries a machine-readable ``reason``
    and a human ``detail`` at an explicit ``status_code``; raising it creates no engine. A
    ``market_closed`` refusal additionally carries ``next_open`` (ISO-8601 UTC) so the honest
    closed-market panel can show when the market reopens; it is ``None`` for the other reasons."""

    def __init__(
        self,
        reason: str,
        detail: str,
        status_code: int = 503,
        next_open: str | None = None,
    ) -> None:
        self.reason = reason
        self.detail = detail
        self.status_code = status_code
        self.next_open = next_open


# Wall-clock seconds between WS pushes (re-exposes the latest snapshot; no recompute).
WS_PUSH_INTERVAL = 0.2

# The ACTIONABLE message for a Historical watch that exceeds the vendor budget (J-28). A
# historical-fetch timeout deterministically means the window pulled too much data, so the message
# names the real cause and the fix — NOT a misleading generic "please try again" that would
# deterministically fail again on the same window. It is still surfaced via the existing row-9
# `provider_timeout` reason on the same `POST /watch/{ticker}` failure path (no new endpoint).
HISTORICAL_OVERSIZE_DETAIL = (
    "that window is very high-volume — try a shorter range"
)

manager = WatchManager(CONFIG)


def get_market_adapter() -> MarketDataAdapter:
    """The vendor-neutral market-data adapter (overridable in tests via dependency_overrides)."""
    return get_adapter()


async def _warm_symbol_universe_bg(adapter: MarketDataAdapter) -> None:
    """Background task: warm the tradable-symbol universe so the first search is not a cold stall
    (J-30). Runs the (blocking) neutral warm off the event loop; NO-OP without credentials, and a
    warm failure is logged (never crashes startup — search falls back to its lazy fetch)."""
    try:
        await asyncio.to_thread(adapter.warm_symbol_universe)
    except Exception:
        logger.exception("symbol-universe warm failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fire-and-forget the symbol-universe warm at startup through the NEUTRAL adapter seam (J-30)
    # — main.py never names the SDK or the universe cache. Non-blocking: startup does not wait on
    # it (no-creds makes it a no-op; the search endpoint stays correct either way). The adapter is
    # resolved honoring any test ``dependency_overrides`` so a hermetic test warms its FakeAdapter,
    # never the real vendor. Kept referenced so it is not GC'd mid-flight, and cancelled on shutdown.
    warm_adapter = app.dependency_overrides.get(get_market_adapter, get_market_adapter)()
    warm_task = asyncio.create_task(_warm_symbol_universe_bg(warm_adapter))
    try:
        yield
    finally:
        warm_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await warm_task
        await manager.shutdown()


app = FastAPI(title="Tapeology", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Phase-1 dev: open to the local Next.js origin.
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RealDataError)
async def _real_data_error_handler(_, exc: RealDataError) -> JSONResponse:
    # An explicit real-data refusal: the body carries both the human detail and the machine
    # reason at the error's own status; NO engine/snapshot is produced. ``next_open`` is added
    # only when present (a market_closed refusal), so the other reasons' bodies stay unchanged.
    content = {"detail": exc.detail, "reason": exc.reason}
    if exc.next_open is not None:
        content["next_open"] = exc.next_open
    return JSONResponse(status_code=exc.status_code, content=content)


def _engine_or_404(ticker: str):
    engine = manager.get(ticker)
    if engine is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' is not being watched")
    return engine


def _parse_window_dt(value: str) -> datetime:
    """Parse an ISO date-time (UI sends ``YYYY-MM-DDTHH:MM``); a naive value is treated as UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/watch/{ticker}")
async def watch(
    ticker: str,
    body: WatchRequest | None = None,
    adapter: MarketDataAdapter = Depends(get_market_adapter),
) -> dict:
    # Async so it runs on the event loop: the feeders start via asyncio.create_task, which
    # needs a running loop (a sync route runs in a threadpool).
    mode = body.mode if body is not None else "sim"

    if mode == "live":
        return await _watch_live(ticker, adapter)

    if mode == "historical":
        return await _watch_historical(ticker, body, adapter)

    # Simulated path — unchanged.
    try:
        engine = manager.watch(ticker)
    except UnknownTickerError:
        raise HTTPException(
            status_code=400,
            detail=f"'{ticker}' is not a known simulated ticker",
        )
    snap = engine.snapshot()
    return {"ticker": ticker, "scenario": snap.scenario, "status": "watching"}


async def _watch_live(ticker: str, adapter: MarketDataAdapter) -> dict:
    """Stream a real symbol's live trades + quotes through the SAME engine (J-12 / J-15).

    Gate, then stream — never fabricate, never fall back to sim:
      1. No credentials → explicit ``provider_unavailable`` (503), NO engine.
      2. Market-closed pre-flight (J-14): read the clock from the SAME computing owner the
         indicator endpoint uses (``adapter.get_market_clock``, off the event loop). Only an
         AUTHORITATIVE closed clock (``is_open is False``) refuses with ``market_closed`` (409 +
         next open), NO engine. A degraded/unreachable clock is INDETERMINATE — it is NOT reported
         as closed (that would fabricate a session); the watch proceeds and the live feed itself
         honestly shows ``stale``/no events if the market is in fact closed.
      3. Otherwise open the vendor live socket behind the neutral adapter and stream it through the
         engine via the async feeder; a feed gap flips the row-6 status to ``stale`` (no invented
         trades) and recovers to ``live`` on resume.
    """
    if not adapter.is_available():
        raise RealDataError("provider_unavailable", "real-data provider unavailable", 503)
    # Read the clock under an explicit per-call timeout (no-unbounded-waits anti-goal): a hung
    # market-clock call can NOT block the Watch request indefinitely. A TIMEOUT is an explicit
    # `provider_timeout` refusal (distinct, NO engine) — not the degraded-but-reachable path. A
    # degraded/unreachable (non-timeout) clock stays INDETERMINATE (`clock = None`) and the watch
    # proceeds, since reporting "closed" off an unknown clock would fabricate a session.
    try:
        clock = await asyncio.wait_for(
            asyncio.to_thread(adapter.get_market_clock),
            timeout=CONFIG.vendor_call_timeout_seconds,
        )
    except asyncio.TimeoutError:
        raise RealDataError("provider_timeout", "market data provider timed out", 504)
    except Exception:
        clock = None
    if clock is not None and clock.is_open is False:
        raise RealDataError(
            "market_closed",
            "market is closed",
            CONFIG.market_closed_status_code,
            next_open=clock.next_open,
        )
    # Stream the real live feed through the SAME engine. The scenario label is the row-6 source
    # descriptor, rendered verbatim from the canonical snapshot.
    scenario = f"live {ticker}"
    provider = LiveProvider(ticker, adapter.stream_live(ticker), scenario)
    engine = manager.watch_with_async_provider(ticker, provider)
    snap = engine.snapshot()
    return {"ticker": ticker, "scenario": snap.scenario, "status": "watching"}


async def _watch_historical(
    ticker: str, body: WatchRequest, adapter: MarketDataAdapter
) -> dict:
    """Validate -> fetch the real window -> replay it through the engine. Each failure mode is
    an explicit, distinct error with NO engine created (no fabricated tape)."""
    if not adapter.is_available():
        raise RealDataError("provider_unavailable", "real-data provider unavailable", 503)

    # 1. Validate params -> 422, no engine, no fetch.
    if not body.start or not body.end:
        raise HTTPException(status_code=422, detail="historical mode requires start and end")
    try:
        start = _parse_window_dt(body.start)
        end = _parse_window_dt(body.end)
    except ValueError:
        raise HTTPException(status_code=422, detail="start and end must be ISO date-times")
    if end <= start:
        raise HTTPException(status_code=422, detail="end must be after start")
    speed = body.speed if body.speed is not None else CONFIG.default_replay_speed
    if speed not in CONFIG.allowed_replay_speeds:
        allowed = ", ".join(str(s) for s in CONFIG.allowed_replay_speeds)
        raise HTTPException(status_code=422, detail=f"speed must be one of: {allowed}")

    # 2. Fetch the real window OFF the event loop, bounded TWO ways (no-unbounded-waits +
    #    bounded-honest-vendor-calls anti-goals): the adapter applies a REAL call-level HTTP
    #    deadline (cutting the vendor request off itself -> a neutral `VendorTimeout`), and this
    #    `asyncio.wait_for` is the OUTER backstop. Either way a hung/slow/oversized vendor can NOT
    #    block the Watch indefinitely: it is refused with an explicit `provider_timeout` and NO
    #    engine (no fabricated tape). On the historical path a timeout deterministically means the
    #    window pulled too much data, so the message is ACTIONABLE ("try a shorter range"), not a
    #    misleading generic retry. Map the other neutral failures -> distinct 4xx, no engine.
    try:
        window = await asyncio.wait_for(
            asyncio.to_thread(adapter.fetch_historical, ticker, start, end),
            timeout=CONFIG.vendor_call_timeout_seconds,
        )
    except (asyncio.TimeoutError, VendorTimeout):
        raise RealDataError("provider_timeout", HISTORICAL_OVERSIZE_DETAIL, 504)
    except SymbolNotTradable:
        raise RealDataError("symbol_not_tradable", "not a tradable symbol", 404)
    except NoDataForWindow:
        raise RealDataError("no_data_for_window", "no data for that window", 404)

    # 3. Success -> replay through the SAME engine. The scenario label is the row-6 source
    #    descriptor, rendered verbatim from the canonical snapshot.
    scenario = f"historical {ticker} {body.start}–{body.end}"
    provider = HistoricalProvider(ticker, window, scenario)
    engine = manager.watch_with_provider(ticker, provider, speed)
    snap = engine.snapshot()
    return {"ticker": ticker, "scenario": snap.scenario, "status": "watching"}


@app.get("/symbols/search")
async def symbols_search(
    q: str = "", adapter: MarketDataAdapter = Depends(get_market_adapter)
) -> list[dict]:
    """Real tradable-symbol suggestions (symbol + name) for the search box (J-13).

    A short/empty query, no credentials, or any adapter error -> an empty list (never an error,
    never a fabricated suggestion): free-text watch entry always remains possible.
    """
    query = q.strip()
    if len(query) < CONFIG.symbol_search_min_query or not adapter.is_available():
        return []
    try:
        matches = await asyncio.to_thread(adapter.search_symbols, query)
    except Exception:
        return []
    return [
        {"symbol": m.symbol, "name": m.name}
        for m in matches[: CONFIG.symbol_search_limit]
    ]


def _clock_unavailable() -> dict:
    """The explicit row-8 unavailable: null fields, never a guessed open/closed."""
    return {"available": False, "is_open": None, "next_open": None, "next_close": None}


@app.get("/market/clock")
async def market_clock(
    adapter: MarketDataAdapter = Depends(get_market_adapter),
) -> dict:
    """Market session status (Data Contract row 8): open/closed + next open/close, read by the
    Live market-status indicator. With no credentials -> explicit ``available:false`` (null
    fields); a vendor/network error degrades to the same unavailable (benign, like
    ``/symbols/search``). It NEVER fabricates an open/closed. Single source of truth: this is the
    one serving endpoint, and ``adapter.get_market_clock`` is the one computing owner the live
    pre-flight gate also reads — no recomputation, no second lookup.
    """
    if not adapter.is_available():
        return _clock_unavailable()
    try:
        clock = await asyncio.to_thread(adapter.get_market_clock)
    except Exception:
        return _clock_unavailable()
    return {
        "available": True,
        "is_open": clock.is_open,
        "next_open": clock.next_open,
        "next_close": clock.next_close,
    }


@app.post("/watch/{ticker}/pause")
async def pause_watch(ticker: str) -> dict:
    """Freeze a watched ticker WITHOUT tearing it down (J-19) — the opposite of DELETE/stop.

    The feeder is left alive (its task is NOT cancelled, a live socket stays open) and the engine,
    its latest snapshot, and the history buffer survive; only the canonical paused flag is set and
    the row-6 status flips to "paused" (owned once by the engine — no second writer here). Returns
    the updated canonical snapshot projection (carrying ``paused`` + ``stream_status``). A
    not-watched ticker is an honest 404 — no engine is fabricated. Idempotent: pausing an
    already-paused watch is a no-op 200.
    """
    if not manager.pause(ticker):
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' is not being watched")
    return serialize_summary(_engine_or_404(ticker).snapshot())


@app.post("/watch/{ticker}/resume")
async def resume_watch(ticker: str) -> dict:
    """Continue a paused watch (J-19): clear ``paused`` and restore the prior pre-pause status.

    Feeding resumes from where it left off (paced replay) or rejoins current real data (live) —
    NO catch-up is synthesized (honest pause). Returns the updated canonical snapshot projection.
    A not-watched ticker is an honest 404. Idempotent: resuming a not-paused watch is a no-op 200.
    """
    if not manager.resume(ticker):
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' is not being watched")
    return serialize_summary(_engine_or_404(ticker).snapshot())


@app.post("/watch/{ticker}/speed")
async def set_watch_speed(ticker: str, body: SpeedRequest) -> dict:
    """Change the historical replay speed of a RUNNING watch (J-32) — applies immediately.

    The body ``speed`` is validated against ``CONFIG.allowed_replay_speeds`` (backend-authoritative):
    an out-of-set value is a 422 BEFORE any feeder mutation (never silently coerced); a not-watched
    ticker is an honest 404 (no engine fabricated). On success the per-ticker mutable speed cell is
    updated, so ``_feed_paced`` re-paces the in-progress replay within ~1s with NO re-fetch, engine
    restart, or teardown — and because speed scales delivery pacing only (never the events, their
    order, or their logical timestamps), the resulting features/state/confidence are unchanged
    (determinism preserved). Returns the canonical snapshot projection (carrying the unchanged
    state/confidence); the new speed itself is delivery-pacing metadata, never a displayed value.
    """
    if body.speed not in CONFIG.allowed_replay_speeds:
        allowed = ", ".join(str(s) for s in CONFIG.allowed_replay_speeds)
        raise HTTPException(status_code=422, detail=f"speed must be one of: {allowed}")
    if not manager.set_speed(ticker, body.speed):
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' is not being watched")
    return serialize_summary(_engine_or_404(ticker).snapshot())


@app.delete("/watch/{ticker}")
async def stop_watch(ticker: str) -> dict:
    # Async so task cancellation runs on the event loop (the feeder lives there). Tearing the
    # engine down removes it from the registry, so subsequent reads honestly 404 and a fresh
    # WS connect is rejected 4404 — no fabricated success, no synthesized post-stop snapshot.
    if not manager.stop(ticker):
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' is not being watched")
    return {"ticker": ticker, "status": "stopped"}


@app.get("/tape/{ticker}/state")
def get_state(ticker: str) -> dict:
    return serialize_state(_engine_or_404(ticker).snapshot())


@app.get("/tape/{ticker}/features")
def get_features(ticker: str) -> dict:
    return serialize_features(_engine_or_404(ticker).snapshot())


@app.get("/tape/{ticker}/events")
def get_events(ticker: str) -> dict:
    return serialize_events(_engine_or_404(ticker).snapshot())


@app.get("/tape/{ticker}/summary")
def get_summary(ticker: str) -> dict:
    return serialize_summary(_engine_or_404(ticker).snapshot())


@app.get("/tape/{ticker}/history")
def get_history(ticker: str, bar: int = CONFIG.history_bar_sizes[0]) -> dict:
    """Engine-computed OHLC candles + tape-state markers for the prediction chart (J-17 / J-18).

    A pure projection of the engine history buffer (single source of truth — the chart recomputes
    no price/side/state). Honest contract:
      * Not-watched ticker -> 404 (reuse ``_engine_or_404``; never a fabricated empty 200).
      * ``bar`` not in the configured set -> 422 (rejected, not silently coerced).
      * Watched but no trades yet / an empty historical window -> empty bars + empty markers (200);
        no invented candles.
    Works for simulated + historical alike — the backend does not special-case the mode; it serves
    whatever the engine accumulated (Live is hidden in the UI, not here).
    """
    if bar not in CONFIG.history_bar_sizes:
        allowed = ", ".join(str(b) for b in CONFIG.history_bar_sizes)
        raise HTTPException(status_code=422, detail=f"bar must be one of: {allowed}")
    engine = _engine_or_404(ticker)
    # Pass the engine's canonical display/epoch anchor (row 13, J-31) through to the projection so
    # the chart renders TRUE clock time (`epoch_anchor + bar.time`). Read verbatim — no recompute.
    return serialize_history(engine.history, bar, epoch_anchor=engine.epoch_anchor)


@app.websocket("/tape/{ticker}/stream")
async def stream(websocket: WebSocket, ticker: str) -> None:
    engine = manager.get(ticker)
    if engine is None:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(serialize_stream(engine.snapshot()))
            await asyncio.sleep(WS_PUSH_INTERVAL)
    except WebSocketDisconnect:
        return
