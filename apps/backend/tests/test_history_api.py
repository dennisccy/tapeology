"""`GET /tape/{ticker}/history` projection + honest error cases (J-17 / J-18).

The endpoint serves a pure projection of the engine history buffer for the requested bar size.
These assert it agrees with the engine buffer (single source of truth — the `/history`-agrees-
with-engine analogue of the existing `/state`/`/features` single-source tests), and that every
honest contract holds: 404 not-watched, 422 invalid bar, empty-but-watched -> empty 200.
"""

from __future__ import annotations

import asyncio
import itertools

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.main import app, manager
from app.providers.simulated import SimulatedProvider
from app.serializers import serialize_history


def _warm_engine(n: int = 400) -> TapeEngine:
    provider = SimulatedProvider("SIM-BUYER", "buyer_control")
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    for event in itertools.islice(provider.stream(), n):
        engine.process_event(event)
    return engine


# --- Serializer projection equals the engine buffer (single source of truth) --------------

def test_serialize_history_matches_engine_buffer():
    engine = _warm_engine()
    for bar in CONFIG.history_bar_sizes:
        out = serialize_history(engine.history, bar)
        buf_bars = engine.history.bars(bar)
        assert out["bar"] == bar
        assert len(out["bars"]) == len(buf_bars)
        for served, b in zip(out["bars"], buf_bars):
            assert served == {
                "time": b.start,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
            }
        buf_markers = engine.history.markers()
        assert len(out["markers"]) == len(buf_markers)
        for served, m in zip(out["markers"], buf_markers):
            assert served == {
                "time": m.timestamp,
                "state": m.state,
                "confidence": m.confidence,
            }


# --- Over HTTP, against a live watched sim ticker ------------------------------------------

@pytest.mark.anyio
async def test_history_endpoint_agrees_with_engine_for_watched_ticker():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.post("/watch/SIM-BUYER")).status_code == 200
        # Let the feeder accrue some candles + the buyer_control transition marker.
        for _ in range(120):
            state = (await client.get("/tape/SIM-BUYER/state")).json()
            if state["tape_state"] == "buyer_control":
                break
            await asyncio.sleep(0.1)

        # Freeze the feeder so the HTTP read and the in-process engine read ONE identical buffer.
        await manager.shutdown()
        await asyncio.sleep(0.1)

        engine = manager.get("SIM-BUYER")
        assert engine is not None
        for bar in CONFIG.history_bar_sizes:
            resp = await client.get(f"/tape/SIM-BUYER/history?bar={bar}")
            assert resp.status_code == 200
            body = resp.json()
            # The served projection equals the engine buffer for that bar size (single source) —
            # including the canonical display/epoch anchor (row 13, J-31) the route passes through.
            assert body == serialize_history(
                engine.history, bar, epoch_anchor=engine.epoch_anchor
            )
            # The sim watch carries the config synthetic session-start anchor (true-clock axis).
            assert body["epoch_anchor"] == CONFIG.sim_session_anchor_epoch
            assert body["bars"], "a warmed buyer scenario must have accrued candles"

        # The chart's defining read: exactly one buyer_control marker, in emerald-coded state.
        markers = (await client.get("/tape/SIM-BUYER/history?bar=10")).json()["markers"]
        buyer_markers = [m for m in markers if m["state"] == "buyer_control"]
        assert len(buyer_markers) == 1
        assert buyer_markers[0]["confidence"] >= CONFIG.reasonable_confidence

    await manager.shutdown()


# --- Default bar (no query) is a valid configured size, served at 200 ----------------------

@pytest.mark.anyio
async def test_history_default_bar_is_served():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.post("/watch/SIM-BUYER")).status_code == 200
        await manager.shutdown()
        await asyncio.sleep(0.1)
        resp = await client.get("/tape/SIM-BUYER/history")  # no ?bar=
        assert resp.status_code == 200
        assert resp.json()["bar"] == CONFIG.history_bar_sizes[0]
    await manager.shutdown()


# --- Honest error / edge cases ------------------------------------------------------------

@pytest.mark.anyio
async def test_history_not_watched_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Never watched -> explicit 404 (not a fabricated empty 200 for an unknown engine).
        resp = await client.get("/tape/SIM-SELLER/history?bar=10")
        assert resp.status_code == 404


@pytest.mark.anyio
async def test_history_invalid_bar_returns_422():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.post("/watch/SIM-BUYER")).status_code == 200
        # An out-of-set bar is rejected, NOT silently coerced to a valid one.
        resp = await client.get("/tape/SIM-BUYER/history?bar=7")
        assert resp.status_code == 422
        # And a non-integer bar is a 422 from FastAPI's int coercion.
        resp2 = await client.get("/tape/SIM-BUYER/history?bar=abc")
        assert resp2.status_code == 422
    await manager.shutdown()


def test_empty_buffer_serializes_to_empty_lists():
    # A fresh engine has processed no trades -> the projection is empty bars + empty markers
    # (HTTP 200 at the route), never invented candles (no-fabricated-data / one-focused-chart).
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    for bar in CONFIG.history_bar_sizes:
        # No anchor passed -> epoch_anchor None, empty bars/markers (no fabricated candle/time).
        assert serialize_history(engine.history, bar) == {
            "bar": bar,
            "epoch_anchor": None,
            "bars": [],
            "markers": [],
        }
