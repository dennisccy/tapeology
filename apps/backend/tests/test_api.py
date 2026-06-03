"""API tests: single-source-of-truth across views, error cases, and a live SIM-BUYER watch."""

import asyncio
import itertools

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.main import app, manager
from app.providers.simulated import SimulatedProvider
from app.serializers import (
    HEADLINE_FEATURES,
    serialize_features,
    serialize_state,
    serialize_stream,
    serialize_summary,
)


def _warm_engine(n: int = 240) -> TapeEngine:
    provider = SimulatedProvider("SIM-BUYER", "buyer_control")
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    for event in itertools.islice(provider.stream(), n):
        engine.process_event(event)
    return engine


def _warm_bidabs(n: int = 240) -> TapeEngine:
    provider = SimulatedProvider("SIM-BIDABS", "bid_absorption")
    engine = TapeEngine("SIM-BIDABS", "bid_absorption", CONFIG)
    for event in itertools.islice(provider.stream(), n):
        engine.process_event(event)
    return engine


# --- Single source of truth at the serializer layer (re-expose, never recompute) --------

def test_summary_reexposes_state():
    snap = _warm_engine().snapshot()
    state, summary = serialize_state(snap), serialize_summary(snap)
    assert summary["tape_state"] == state["tape_state"]
    assert summary["confidence"] == state["confidence"]


def test_summary_headline_features_match_features_endpoint():
    snap = _warm_engine().snapshot()
    features, summary = serialize_features(snap), serialize_summary(snap)
    primary = features["windows"][features["primary_window"]]
    for name in HEADLINE_FEATURES:
        assert summary["headline_features"][name] == primary[name]


def test_stream_payload_matches_canonical_reads():
    snap = _warm_engine().snapshot()
    stream, state, features = (
        serialize_stream(snap),
        serialize_state(snap),
        serialize_features(snap),
    )
    assert stream["tape_state"] == state["tape_state"]
    assert stream["confidence"] == state["confidence"]
    assert stream["features"] == features["windows"]


def test_spread_is_ask_minus_bid():
    market = serialize_summary(_warm_engine().snapshot())["market"]
    assert market["spread"] == pytest.approx(market["ask"] - market["bid"])


def test_absorption_views_agree_single_source():
    # J-08 for absorption: /state, /features, /summary and the WS stream serve ONE engine
    # value per metric, including the new absorption feature readouts (no recompute).
    snap = _warm_bidabs().snapshot()
    state = serialize_state(snap)
    features = serialize_features(snap)
    summary = serialize_summary(snap)
    stream = serialize_stream(snap)

    assert state["tape_state"] == "bid_absorption"
    assert summary["tape_state"] == state["tape_state"]
    assert stream["tape_state"] == state["tape_state"]
    assert stream["confidence"] == state["confidence"]
    # Every window's features are the same object across /features and the stream.
    assert stream["features"] == features["windows"]
    primary = features["windows"][features["primary_window"]]
    assert primary["bid_refresh_score"] >= CONFIG.min_bid_refresh_score
    assert primary["absorption_score"] > 0


# --- Error cases: explicit, no fabrication ----------------------------------------------

@pytest.mark.anyio
async def test_unknown_ticker_post_is_rejected_and_not_fabricated():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/watch/NOPE123")).status_code == 400
        # And a read for it is an explicit not-watched, never a fabricated snapshot.
        assert (await client.get("/tape/NOPE123/state")).status_code == 404


@pytest.mark.anyio
async def test_read_of_not_watched_ticker_returns_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # SIM-SELLER is a known (reserved) ticker, but it was never watched.
        assert (await client.get("/tape/SIM-SELLER/state")).status_code == 404


# --- Live SIM-BUYER watch over HTTP, with the real background feeder ---------------------

@pytest.mark.anyio
async def test_watch_sim_buyer_resolves_and_views_agree():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        post = await client.post("/watch/SIM-BUYER")
        assert post.status_code == 200
        assert post.json()["scenario"] == "buyer_control"

        state = {}
        for _ in range(120):  # poll up to ~12s for the feeder to resolve the scenario
            state = (await client.get("/tape/SIM-BUYER/state")).json()
            if state["tape_state"] == "buyer_control":
                break
            await asyncio.sleep(0.1)

        assert state["tape_state"] == "buyer_control"
        assert state["confidence"] >= CONFIG.reasonable_confidence

        # Freeze the feeder before the cross-view comparison: otherwise the background feeder
        # advances the snapshot between the separate HTTP reads, and a value that is still
        # climbing at resolution (confidence) can legitimately differ by a tick between two
        # reads. With the feeder stopped, every view reads ONE identical engine snapshot, so
        # the single-source equality below is exact and deterministic.
        await manager.shutdown()
        await asyncio.sleep(0.1)  # let the cancelled feeder settle (no further events)

        state = (await client.get("/tape/SIM-BUYER/state")).json()
        features = (await client.get("/tape/SIM-BUYER/features")).json()
        summary = (await client.get("/tape/SIM-BUYER/summary")).json()
        events = (await client.get("/tape/SIM-BUYER/events")).json()

        # Single source of truth: summary re-exposes /state and the /features headline subset.
        assert summary["tape_state"] == state["tape_state"]
        assert summary["confidence"] == state["confidence"]
        primary = features["windows"][features["primary_window"]]
        for name in HEADLINE_FEATURES:
            assert summary["headline_features"][name] == primary[name]

        # J-01 panels are populated with live values.
        assert primary["buy_price_impact"] > 0
        assert events["recent_trades"] and all("side" in r for r in events["recent_trades"])
        assert events["observations"]
        assert "Tape state changed to buyer_control" in events["event_log"]

    await manager.shutdown()
