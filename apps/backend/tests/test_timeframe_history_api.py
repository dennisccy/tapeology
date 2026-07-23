"""`GET /tape/{ticker}/history?timeframe=` — the additive wall-clock cockpit "history" mode.

These assert the new projection is served correctly AND — critically — that the pre-existing
``?bar=`` mode is byte-identical (the additive-discipline pin: new data arrives under new keys /
a new param, the legacy shape never gains a field). Plus the honest error contract (422 for both
params together, unknown timeframe, 1w/1mo) and the no-lookahead boundary.
"""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import CONFIG, Config
from app.engine.tape_engine import TapeEngine
from app.main import app, manager
from app.serializers import serialize_timeframe_history


async def _warm_watch(client: AsyncClient, n_polls: int = 150) -> TapeEngine:
    """Watch SIM-BUYER until it classifies buyer_control (guaranteeing >=1 timeframe candle AND the
    buyer_control marker), then freeze the feeder so the HTTP read and the in-process engine read
    ONE identical buffer (test_history_api.py's own pattern)."""
    assert (await client.post("/watch/SIM-BUYER")).status_code == 200
    for _ in range(n_polls):
        state = (await client.get("/tape/SIM-BUYER/state")).json()
        if state["tape_state"] == "buyer_control":
            break
        await asyncio.sleep(0.1)
    await manager.shutdown()
    await asyncio.sleep(0.1)
    engine = manager.get("SIM-BUYER")
    assert engine is not None
    return engine


# --- The ?bar= mode stays byte-identical (additive discipline) ----------------------------

@pytest.mark.anyio
async def test_bar_mode_top_level_keys_and_rows_are_byte_identical():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _warm_watch(client)
        body = (await client.get("/tape/SIM-BUYER/history?bar=10")).json()
        # EXACT top-level key set — the legacy shape must not gain a key.
        assert set(body) == {"bar", "epoch_anchor", "bars", "markers"}
        assert body["bars"], "a warmed buyer scenario must have accrued candles"
        for row in body["bars"]:
            assert set(row) == {"time", "open", "high", "low", "close"}  # no ts/volume here
        for marker in body["markers"]:
            assert set(marker) == {"time", "state", "confidence"}  # no bucket_ts here
    await manager.shutdown()


@pytest.mark.anyio
async def test_default_request_still_serves_bar_10():
    # Guards the `bar: int | None = None` refactor: no param -> the first configured size, verbatim.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.post("/watch/SIM-BUYER")).status_code == 200
        await manager.shutdown()
        await asyncio.sleep(0.1)
        body = (await client.get("/tape/SIM-BUYER/history")).json()  # no ?bar=
        assert body["bar"] == CONFIG.history_bar_sizes[0]
        assert set(body) == {"bar", "epoch_anchor", "bars", "markers"}
    await manager.shutdown()


# --- The ?timeframe= mode ------------------------------------------------------------------

@pytest.mark.anyio
async def test_timeframe_mode_serves_real_epoch_bars_with_volume_and_anchor_bucket_start():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        engine = await _warm_watch(client)
        resp = await client.get("/tape/SIM-BUYER/history?timeframe=1m")
        assert resp.status_code == 200
        body = resp.json()
        # Single source of truth: the served body equals the serializer over the same buffer.
        assert body == serialize_timeframe_history(
            engine.history, "1m", epoch_anchor=engine.epoch_anchor
        )
        assert set(body) == {
            "timeframe", "timeframe_seconds", "epoch_anchor",
            "anchor_bucket_start", "timeframe_bars", "markers",
        }
        assert body["timeframe"] == "1m"
        assert body["timeframe_seconds"] == 60
        assert body["epoch_anchor"] == CONFIG.sim_session_anchor_epoch
        assert body["anchor_bucket_start"] == (CONFIG.sim_session_anchor_epoch // 60) * 60
        assert body["timeframe_bars"], "a warmed buyer scenario must have accrued timeframe candles"
        for row in body["timeframe_bars"]:
            assert set(row) == {"ts", "open", "high", "low", "close", "volume"}
        assert sum(r["volume"] for r in body["timeframe_bars"]) > 0
    await manager.shutdown()


@pytest.mark.anyio
async def test_no_lookahead_every_served_timeframe_bar_ts_is_at_or_after_anchor_bucket_start():
    # The live tape bars begin at (never before) the anchor's bucket — the boundary the chart clamps
    # the recorded-store window against. No served live bar predates it.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _warm_watch(client)
        body = (await client.get("/tape/SIM-BUYER/history?timeframe=5m")).json()
        boundary = body["anchor_bucket_start"]
        assert boundary is not None
        assert all(row["ts"] >= boundary for row in body["timeframe_bars"])
    await manager.shutdown()


@pytest.mark.anyio
async def test_timeframe_markers_carry_bucket_ts_of_containing_bar():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _warm_watch(client)
        body = (await client.get("/tape/SIM-BUYER/history?timeframe=1m")).json()
        assert body["markers"], "a warmed buyer scenario must have a tape-state marker"
        secs = body["timeframe_seconds"]
        anchor = body["epoch_anchor"]
        for marker in body["markers"]:
            assert set(marker) == {"time", "state", "confidence", "bucket_ts"}
            # bucket_ts is the real-epoch left edge of the timeframe bucket the marker falls in.
            assert marker["bucket_ts"] == ((anchor + marker["time"]) // secs) * secs
    await manager.shutdown()


# --- Honest error contract -----------------------------------------------------------------

@pytest.mark.anyio
async def test_bar_and_timeframe_together_is_422():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.post("/watch/SIM-BUYER")).status_code == 200
        resp = await client.get("/tape/SIM-BUYER/history?bar=10&timeframe=1m")
        assert resp.status_code == 422
    await manager.shutdown()


@pytest.mark.anyio
async def test_unknown_timeframe_is_422_listing_allowed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.post("/watch/SIM-BUYER")).status_code == 200
        resp = await client.get("/tape/SIM-BUYER/history?timeframe=3m")
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "1m" in detail and "1d" in detail  # names the allowed set
    await manager.shutdown()


@pytest.mark.anyio
async def test_1w_and_1mo_are_422():
    # Valid bar_timeframes, but NOT honestly floorable live bars -> rejected, not silently served.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.post("/watch/SIM-BUYER")).status_code == 200
        for tf in ("1w", "1mo"):
            resp = await client.get(f"/tape/SIM-BUYER/history?timeframe={tf}")
            assert resp.status_code == 422, tf
    await manager.shutdown()


@pytest.mark.anyio
async def test_timeframe_not_watched_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/tape/SIM-SELLER/history?timeframe=1m")
        assert resp.status_code == 404


# --- Anchorless engine: empty 200 (serializer-level, mirrors test_history_api's empty test) ----

def test_timeframe_for_anchorless_engine_is_empty_200():
    # An anchorless engine (no first record epoch known) serves empty timeframe bars + a null
    # anchor_bucket_start — never invented candles or a fabricated boundary.
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)  # no anchor
    out = serialize_timeframe_history(engine.history, "1m", epoch_anchor=None)
    assert out == {
        "timeframe": "1m",
        "timeframe_seconds": 60,
        "epoch_anchor": None,
        "anchor_bucket_start": None,
        "timeframe_bars": [],
        "markers": [],
    }


# --- Belt-and-braces: this feature adds no Config field -------------------------------------

def test_fingerprint_unchanged_by_this_feature():
    assert Config().config_fingerprint() == "4d665603569b9dbf"
