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
from .providers.adapters.base import NoDataForWindow, SymbolNotTradable
from .providers.historical import HistoricalProvider
from .serializers import (
    serialize_events,
    serialize_features,
    serialize_state,
    serialize_stream,
    serialize_summary,
)
from .watch_manager import UnknownTickerError, WatchManager

# Make uvicorn (and any importer) see the operator's apps/backend/.env without sourcing it by
# hand. Load-if-missing: never overrides an already-set var, so the test suite stays hermetic.
load_env()


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


class RealDataError(Exception):
    """Refuse a real-mode watch with an explicit, distinct non-cockpit response instead of
    fabricating a snapshot (no-fabricated-data anti-goal). Carries a machine-readable ``reason``
    and a human ``detail`` at an explicit ``status_code``; raising it creates no engine."""

    def __init__(self, reason: str, detail: str, status_code: int = 503) -> None:
        self.reason = reason
        self.detail = detail
        self.status_code = status_code


# Wall-clock seconds between WS pushes (re-exposes the latest snapshot; no recompute).
WS_PUSH_INTERVAL = 0.2

manager = WatchManager(CONFIG)


def get_market_adapter() -> MarketDataAdapter:
    """The vendor-neutral market-data adapter (overridable in tests via dependency_overrides)."""
    return get_adapter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
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
    # reason at the error's own status; NO engine/snapshot is produced.
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail, "reason": exc.reason}
    )


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
        # Live streaming is out of scope this iteration: gate on availability, then refuse
        # explicitly (no fabricated cockpit, no sim fall-back). Behavior unchanged from iter-1.
        if not adapter.is_available():
            raise RealDataError("provider_unavailable", "real-data provider unavailable", 503)
        raise RealDataError(
            "provider_not_implemented", "real-data provider not yet available", 503
        )

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

    # 2. Fetch the real window OFF the event loop. Map neutral failures -> distinct 4xx, no engine.
    try:
        window = await asyncio.to_thread(adapter.fetch_historical, ticker, start, end)
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
