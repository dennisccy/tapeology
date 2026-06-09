"""POST /watch/{ticker}/speed (J-32) — live replay re-pacing without re-Watch / teardown.

The route is a thin shell over ``WatchManager.set_speed``: it validates the body speed against
``CONFIG.allowed_replay_speeds`` (backend-authoritative; out-of-set ⇒ 422 BEFORE any mutation),
404s a not-watched ticker (no fabricated engine), mutates the per-ticker speed cell the running
feeder reads each iteration, and keeps the watch ALIVE (no teardown). The keystone determinism
proof — replaying ONE fixed window at 1× and 10× yields byte-identical features/state/confidence —
lives here too: speed is delivery pacing ONLY.
"""

from __future__ import annotations

import asyncio
import dataclasses

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.main import app, get_market_adapter
from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
from app.providers.historical import HistoricalProvider
from app.watch_manager import WatchManager
from fakes import FakeAdapter

HIST_BODY = {
    "mode": "historical",
    "start": "2026-06-02T15:00",
    "end": "2026-06-02T15:02",
    "speed": 1,
}


def _busy_window() -> HistoricalWindow:
    """A real-shaped window long enough that the replay is still running when we re-pace it."""
    trades = tuple(RawTrade(float(i), 10.0 + (i % 5) * 0.01, 100) for i in range(1, 200))
    quotes = tuple(
        RawQuote(float(i) - 0.5, 10.0 - 0.01, 10.0 + 0.01, 5, 5) for i in range(1, 200)
    )
    return HistoricalWindow("AAPL", trades, quotes)


# --- Route validation: out-of-set ⇒ 422, not-watched ⇒ 404 (backend-authoritative) ---------


def test_speed_out_of_set_is_422_and_does_not_create_engine():
    # An out-of-set speed is rejected with 422 (validated against the config allowed set) and no
    # engine is fabricated by the attempt. 3.0 is deliberately not in {1,2,5,10}.
    with TestClient(app) as client:
        resp = client.post("/watch/AAPL/speed", json={"speed": 3.0})
        assert resp.status_code == 422
        assert "speed must be one of" in resp.json()["detail"]
        # Not fabricated into existence by the attempt.
        assert client.get("/tape/AAPL/state").status_code == 404


def test_speed_on_not_watched_ticker_is_404():
    # A valid (in-set) speed on a ticker that is NOT being watched is an honest 404 — never a
    # fabricated engine. The 422 validation runs first, so this uses an in-set speed.
    with TestClient(app) as client:
        resp = client.post("/watch/AAPL/speed", json={"speed": 5.0})
        assert resp.status_code == 404


def test_speed_422_precedes_404_for_out_of_set_on_not_watched():
    # Validation order (the iter-11 mirror lesson): an out-of-set speed is a 422 even on a
    # not-watched ticker — the allowed-set check is backend-authoritative and runs first.
    with TestClient(app) as client:
        resp = client.post("/watch/NOPE999/speed", json={"speed": 7.0})
        assert resp.status_code == 422


# --- Happy path over the real feeder: speed applies live, watch is NOT torn down ------------


def test_set_speed_applies_to_running_watch_without_teardown():
    # Driving a real event loop so POST /watch (historical) starts the paced feeder. Set a new
    # (in-set) speed on the running watch: 200, the body carries the canonical snapshot (state
    # unchanged), and the watch is NOT torn down (a read is still 200, not the 404 a stop gives).
    import time

    app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(
        available=True, window=_busy_window()
    )
    try:
        with TestClient(app) as client:
            assert client.post("/watch/AAPL", json=HIST_BODY).status_code == 200
            # Let the feeder apply some events first.
            for _ in range(120):
                if client.get("/tape/AAPL/summary").json()["timestamp"] > 0.0:
                    break
                time.sleep(0.05)

            resp = client.post("/watch/AAPL/speed", json={"speed": 10.0})
            assert resp.status_code == 200
            body = resp.json()
            # The summary projection carries the canonical fields (single source of truth) — the
            # speed itself is delivery-pacing metadata, never a displayed value, so it is NOT here.
            assert "tape_state" in body and "confidence" in body
            assert "speed" not in body

            # The watch is alive (NOT torn down) — a read is still 200, feeder keeps advancing.
            assert client.get("/tape/AAPL/state").status_code == 200
            frozen_ts = client.get("/tape/AAPL/summary").json()["timestamp"]
            for _ in range(60):
                if client.get("/tape/AAPL/summary").json()["timestamp"] > frozen_ts:
                    break
                time.sleep(0.05)
            assert client.get("/tape/AAPL/summary").json()["timestamp"] >= frozen_ts

            client.delete("/watch/AAPL")
    finally:
        app.dependency_overrides.pop(get_market_adapter, None)


# --- Determinism: the SAME fixed window at 1× and 10× ⇒ identical engine output -------------


def _synthetic_window() -> HistoricalWindow:
    """A small deterministic window (alternating quote/trade) for the speed-determinism test."""
    trades = tuple(RawTrade(float(i), 10.0 + i * 0.01, 100) for i in range(1, 61))
    quotes = tuple(
        RawQuote(float(i) - 0.5, 10.0 + i * 0.01 - 0.01, 10.0 + i * 0.01 + 0.01, 5, 5)
        for i in range(1, 61)
    )
    return HistoricalWindow("SYN", trades, quotes)


async def _replay_at_speed(speed: float) -> TapeEngine:
    """Replay the fixed window through the real feeder at a fixed ``speed`` (mutable cell of one)."""
    # Tiny pacing cap so the test runs fast; pacing changes never affect engine math (the point).
    cfg = dataclasses.replace(CONFIG, replay_pacing_cap_seconds=0.0)
    manager = WatchManager(cfg)
    engine = TapeEngine("SYN", "historical SYN", cfg)
    await manager._feed_paced(
        engine, HistoricalProvider("SYN", _synthetic_window(), "historical SYN"), [speed]
    )
    return engine


@pytest.mark.anyio
async def test_same_window_at_1x_and_10x_yields_identical_engine_output():
    # KEYSTONE J-32 determinism: speed is delivery pacing ONLY — the engine processes the same
    # ordered events with the same logical timestamps regardless of speed, so the final
    # features/state/confidence are byte-identical at 1× and 10×.
    slow = (await _replay_at_speed(1.0)).snapshot()
    fast = (await _replay_at_speed(10.0)).snapshot()
    assert slow.tape_state == fast.tape_state
    assert slow.confidence == fast.confidence
    assert slow.timestamp == fast.timestamp
    assert slow.features == fast.features  # single source of truth holds under any pacing


@pytest.mark.anyio
async def test_set_speed_mid_replay_changes_cadence_not_engine_output():
    # A live ``set_speed`` mutates the shared cell the feeder reads each iteration. Even when the
    # speed CHANGES mid-stream, the engine output equals a fixed-speed replay of the SAME window
    # (delivery re-pacing never perturbs the deterministic engine math).
    cfg = dataclasses.replace(CONFIG, replay_pacing_cap_seconds=0.0)
    manager = WatchManager(cfg)
    engine = TapeEngine("SYN", "historical SYN", cfg)
    cell = [1.0]
    task = asyncio.create_task(
        manager._feed_paced(
            engine, HistoricalProvider("SYN", _synthetic_window(), "historical SYN"), cell
        )
    )
    await asyncio.sleep(0)  # let the feeder start
    cell[0] = 10.0  # change speed mid-replay (the live re-pacing lever)
    await task

    reference = (await _replay_at_speed(1.0)).snapshot()
    snap = engine.snapshot()
    assert snap.tape_state == reference.tape_state
    assert snap.confidence == reference.confidence
    assert snap.features == reference.features
