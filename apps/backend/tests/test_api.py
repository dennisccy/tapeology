"""API tests: single-source-of-truth across views, error cases, and a live SIM-BUYER watch."""

import asyncio
import itertools

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from starlette.websockets import WebSocketDisconnect

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


def _warm_chop(n: int = 480) -> TapeEngine:
    # dt = 0.2s/tick, so 480 events (~240 trades) is comfortably warmed.
    provider = SimulatedProvider("SIM-CHOP", "unclear_chop")
    engine = TapeEngine("SIM-CHOP", "unclear_chop", CONFIG)
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


def test_chop_views_agree_single_source():
    # J-08 extended to the FIFTH state: for a watched SIM-CHOP, /state, /features, /summary and
    # the WS stream serve ONE engine value per metric (no recompute), and the read is honestly
    # `unclear` at low confidence — not a fabricated decisive call. Single source of truth holds
    # on the honest non-call exactly as it does on the decisive states.
    snap = _warm_chop().snapshot()
    state = serialize_state(snap)
    features = serialize_features(snap)
    summary = serialize_summary(snap)
    stream = serialize_stream(snap)

    assert state["tape_state"] == "unclear"
    assert state["confidence"] == CONFIG.unclear_confidence
    assert state["confidence"] < CONFIG.reasonable_confidence
    assert summary["tape_state"] == state["tape_state"]
    assert summary["confidence"] == state["confidence"]
    assert stream["tape_state"] == state["tape_state"]
    assert stream["confidence"] == state["confidence"]
    # Every window's features are one identical object across /features and the WS stream.
    assert stream["features"] == features["windows"]
    primary = features["windows"][features["primary_window"]]
    for name in HEADLINE_FEATURES:
        assert summary["headline_features"][name] == primary[name]
    # The headline impact readouts are honestly past NEITHER control cutoff (no fabricated
    # decisive numbers on the choppy tape).
    assert primary["buy_price_impact"] < CONFIG.min_buy_price_impact
    assert primary["sell_price_impact"] > CONFIG.max_sell_price_impact


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


# --- Live SIM-CHOP watch over HTTP — the honest non-call through the real feeder (J-06) ----

@pytest.mark.anyio
async def test_watch_sim_chop_reads_unclear_over_feeder():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        post = await client.post("/watch/SIM-CHOP")
        assert post.status_code == 200
        assert post.json()["scenario"] == "unclear_chop"

        # Poll until the engine has WARMED on real choppy data (confidence steps from the
        # cold-start 0.10 to the warmed-up 0.20). It must read `unclear` the whole way — a
        # genuinely choppy tape never manufactures a directional/absorption call.
        state = {}
        for _ in range(120):  # up to ~12s for the feeder to push past warmup_min_events
            state = (await client.get("/tape/SIM-CHOP/state")).json()
            assert state["tape_state"] == "unclear"  # never a resolved state at any poll
            if state["warm"]:
                break
            await asyncio.sleep(0.1)

        assert state["warm"] is True
        assert state["tape_state"] == "unclear"
        assert state["confidence"] == CONFIG.unclear_confidence       # warmed unclear (0.20)...
        assert state["confidence"] < CONFIG.reasonable_confidence     # ...honestly low.

        # Freeze the feeder so every view reads ONE identical snapshot (see the buyer test).
        await manager.shutdown()
        await asyncio.sleep(0.1)

        state = (await client.get("/tape/SIM-CHOP/state")).json()
        features = (await client.get("/tape/SIM-CHOP/features")).json()
        summary = (await client.get("/tape/SIM-CHOP/summary")).json()
        events = (await client.get("/tape/SIM-CHOP/events")).json()

        # Single source of truth on the fifth state (J-08 extended to `unclear`).
        assert summary["tape_state"] == state["tape_state"] == "unclear"
        assert summary["confidence"] == state["confidence"]
        primary = features["windows"][features["primary_window"]]
        for name in HEADLINE_FEATURES:
            assert summary["headline_features"][name] == primary[name]

        # Real choppy values, no fabricated decisive numbers: impacts past neither cutoff, and
        # NO spurious transition line (cold-start unclear -> warmed unclear is not a change).
        assert primary["buy_price_impact"] < CONFIG.min_buy_price_impact
        assert primary["sell_price_impact"] > CONFIG.max_sell_price_impact
        assert events["recent_trades"] and all("side" in r for r in events["recent_trades"])
        assert not any(m.startswith("Tape state changed to") for m in events["event_log"])

    await manager.shutdown()


# --- DELETE /watch/{ticker}: deliberate teardown, then re-watch is a fresh read (J-09) -----

def test_delete_watch_stops_then_reads_404_and_rewatch_is_fresh():
    # TestClient drives a real event loop so POST starts the background feeder and DELETE
    # cancels it. SIM-ASKABS is used by no other test against the shared manager, and this
    # test removes its own engine, so it leaves no cross-test residue.
    client = TestClient(app)

    assert client.post("/watch/SIM-ASKABS").status_code == 200

    # Stop: an explicit success body, not a fabricated something.
    stopped = client.delete("/watch/SIM-ASKABS")
    assert stopped.status_code == 200
    assert stopped.json() == {"ticker": "SIM-ASKABS", "status": "stopped"}

    # Engine removed => reads are an explicit 404 (never a synthesized snapshot) and a fresh
    # WS connect is rejected with 4404 — the timing-independent teardown evidence.
    assert client.get("/tape/SIM-ASKABS/state").status_code == 404
    assert client.get("/tape/SIM-ASKABS/features").status_code == 404
    with pytest.raises(WebSocketDisconnect) as ws_exc:
        with client.websocket_connect("/tape/SIM-ASKABS/stream"):
            pass
    assert ws_exc.value.code == 4404

    # Re-watch rebuilds the engine: reads went 404 (gone) -> 200 (rebuilt) across the re-POST,
    # the timing-independent API-level proof of "stop, then a fresh re-watch". (The cold-start /
    # no-state-leakage guarantee for the fresh engine is proven directly in test_watch_manager.py.)
    rewatch = client.post("/watch/SIM-ASKABS")
    assert rewatch.status_code == 200
    assert rewatch.json() == {"ticker": "SIM-ASKABS", "scenario": "ask_absorption", "status": "watching"}
    assert client.get("/tape/SIM-ASKABS/state").status_code == 200  # engine present again

    # Clean up the re-watch feeder + engine so nothing leaks into later tests.
    assert client.delete("/watch/SIM-ASKABS").status_code == 200


def test_delete_not_watched_ticker_returns_404():
    client = TestClient(app)
    # SIM-SELLER is a known reserved ticker but is not being watched — honest 404, no fabrication.
    assert client.delete("/watch/SIM-SELLER").status_code == 404
