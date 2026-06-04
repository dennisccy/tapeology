"""FastAPI app: watch a ticker, read the engine snapshot over REST, stream it over WS.

Every read endpoint serves a pure projection of the engine's single snapshot via
``app.serializers`` — none recompute a value. ``/state`` and ``/features`` are the canonical
reads; ``/summary`` and ``WS /stream`` re-expose the same snapshot read-only. Unknown tickers
and not-watched reads return explicit errors — no fabricated data.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import CONFIG
from .providers.adapters.alpaca import real_data_available
from .serializers import (
    serialize_events,
    serialize_features,
    serialize_state,
    serialize_stream,
    serialize_summary,
)
from .watch_manager import UnknownTickerError, WatchManager


class WatchRequest(BaseModel):
    """Optional ``POST /watch`` body selecting the data-source mode.

    Backward compatible: no body / ``{}`` / ``mode == "sim"`` is the existing simulated watch.
    ``start`` / ``end`` / ``speed`` are accepted for a historical request but are not replayed
    this iteration (the real historical provider lands with J-11); an unrecognized ``mode`` is
    rejected by the ``Literal`` as a 422 — never a silent default into a real feed.
    """

    mode: Literal["sim", "live", "historical"] = "sim"
    start: str | None = None
    end: str | None = None
    speed: float | None = None


class RealDataUnavailableError(Exception):
    """Refuse a real-mode watch with an explicit, distinct non-cockpit response instead of
    fabricating a snapshot (no-fabricated-data anti-goal). Carries a machine-readable ``reason``
    alongside a human ``detail``; raising it creates no engine."""

    def __init__(self, reason: str, detail: str) -> None:
        self.reason = reason
        self.detail = detail

# Wall-clock seconds between WS pushes (re-exposes the latest snapshot; no recompute).
WS_PUSH_INTERVAL = 0.2

manager = WatchManager(CONFIG)


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


@app.exception_handler(RealDataUnavailableError)
async def _real_data_unavailable_handler(_, exc: RealDataUnavailableError) -> JSONResponse:
    # 503: the real-data provider exists in the contract but cannot serve right now. The body
    # carries both the human detail and the machine reason; NO engine/snapshot is produced.
    return JSONResponse(status_code=503, content={"detail": exc.detail, "reason": exc.reason})


def _engine_or_404(ticker: str):
    engine = manager.get(ticker)
    if engine is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' is not being watched")
    return engine


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/watch/{ticker}")
async def watch(ticker: str, body: WatchRequest | None = None) -> dict:
    # Async so it runs on the event loop: WatchManager.watch starts the background feeder
    # via asyncio.create_task, which needs a running loop (a sync route runs in a threadpool).
    mode = body.mode if body is not None else "sim"

    if mode in ("live", "historical"):
        # Real-data modes never touch the sim registry. Gate on the single canonical
        # availability source FIRST and create NO engine on refusal — no fabricated snapshot,
        # no fall-back to the simulator.
        if not real_data_available():
            raise RealDataUnavailableError("provider_unavailable", "real-data provider unavailable")
        # Credentials present, but the live/historical provider is not wired yet (J-11/J-12).
        # Still refuse with an explicit non-cockpit error rather than synthesizing a cockpit.
        raise RealDataUnavailableError(
            "provider_not_implemented", "real-data provider not yet available"
        )

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
