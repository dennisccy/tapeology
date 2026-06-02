"""FastAPI app: watch a ticker, read the engine snapshot over REST, stream it over WS.

Every read endpoint serves a pure projection of the engine's single snapshot via
``app.serializers`` — none recompute a value. ``/state`` and ``/features`` are the canonical
reads; ``/summary`` and ``WS /stream`` re-expose the same snapshot read-only. Unknown tickers
and not-watched reads return explicit errors — no fabricated data.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import CONFIG
from .serializers import (
    serialize_events,
    serialize_features,
    serialize_state,
    serialize_stream,
    serialize_summary,
)
from .watch_manager import UnknownTickerError, WatchManager

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


def _engine_or_404(ticker: str):
    engine = manager.get(ticker)
    if engine is None:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' is not being watched")
    return engine


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/watch/{ticker}")
async def watch(ticker: str) -> dict:
    # Async so it runs on the event loop: WatchManager.watch starts the background feeder
    # via asyncio.create_task, which needs a running loop (a sync route runs in a threadpool).
    try:
        engine = manager.watch(ticker)
    except UnknownTickerError:
        raise HTTPException(
            status_code=400,
            detail=f"'{ticker}' is not a known simulated ticker",
        )
    snap = engine.snapshot()
    return {"ticker": ticker, "scenario": snap.scenario, "status": "watching"}


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
