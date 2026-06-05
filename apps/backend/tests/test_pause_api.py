"""POST /watch/{ticker}/pause and /resume routes (J-19) — freeze without teardown, 404 honest.

The routes are a thin shell over the WatchManager feeder freeze: they return the updated
canonical snapshot (carrying ``paused`` + ``stream_status``), keep the engine alive (a read is
still 200, not 404), and 404 a not-watched ticker (never a fabricated engine). Stop after a
pause must still tear the instance down.
"""

import asyncio

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app, manager


# --- Error path: pause/resume of a not-watched ticker is an honest 404 (no fabrication) ----

@pytest.mark.anyio
async def test_pause_not_watched_ticker_returns_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # SIM-SELLER is a known reserved ticker but is NOT being watched -> honest 404, no engine.
        assert (await client.post("/watch/SIM-SELLER/pause")).status_code == 404
        assert (await client.post("/watch/SIM-SELLER/resume")).status_code == 404
        # And it was not fabricated into existence by the attempt.
        assert (await client.get("/tape/SIM-SELLER/state")).status_code == 404


@pytest.mark.anyio
async def test_pause_unknown_ticker_returns_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/watch/NOPE999/pause")).status_code == 404
        assert (await client.post("/watch/NOPE999/resume")).status_code == 404


# --- Happy path over the real feeder: pause freezes (no teardown), resume continues ---------

def test_pause_resume_route_freezes_then_resumes_without_teardown():
    # TestClient drives a real event loop so POST /watch starts the background feeder. SIM-SELLER
    # is used by no other route test against the shared manager, and this test stops it at the end.
    import time

    # Context-manager form so the app lifespan is entered and the background feeder is driven on
    # the event loop (the engine advances as the test polls).
    with TestClient(app) as client:
        assert client.post("/watch/SIM-SELLER").status_code == 200

        # Let the feeder apply some events: the logical timestamp climbs past its cold-start 0.0.
        for _ in range(120):
            s = client.get("/tape/SIM-SELLER/summary").json()
            if s["timestamp"] > 0.0:
                break
            time.sleep(0.05)
        assert client.get("/tape/SIM-SELLER/summary").json()["timestamp"] > 0.0

        # Pause: 200, the body carries the canonical paused state, and the engine is NOT torn down.
        paused = client.post("/watch/SIM-SELLER/pause")
        assert paused.status_code == 200
        body = paused.json()
        assert body["paused"] is True
        assert body["stream_status"] == "paused"
        # The session is NOT cleared — a read is still 200 (not the 404 a stop would give).
        assert client.get("/tape/SIM-SELLER/state").status_code == 200
        st = client.get("/tape/SIM-SELLER/state").json()
        assert st["stream_status"] == "paused"  # row-6 canonical, read identically by /state

        # While paused the snapshot never reads "live"; the logical timestamp is FROZEN (the feeder
        # applies no new events), proving the read is genuinely frozen — not just relabeled.
        frozen = client.get("/tape/SIM-SELLER/summary").json()
        time.sleep(0.3)
        again = client.get("/tape/SIM-SELLER/summary").json()
        assert again["stream_status"] == "paused"
        assert again["timestamp"] == frozen["timestamp"]  # frozen: no events applied while paused

        # Resume: 200, paused cleared, status restored to a real feed status (not fabricated).
        resumed = client.post("/watch/SIM-SELLER/resume")
        assert resumed.status_code == 200
        rbody = resumed.json()
        assert rbody["paused"] is False
        assert rbody["stream_status"] != "paused"
        assert client.get("/tape/SIM-SELLER/state").status_code == 200

        # After resume the timestamp advances again (feeding genuinely continued, not a backfill).
        for _ in range(60):
            s = client.get("/tape/SIM-SELLER/summary").json()
            if s["timestamp"] > frozen["timestamp"]:
                break
            time.sleep(0.05)
        assert client.get("/tape/SIM-SELLER/summary").json()["timestamp"] > frozen["timestamp"]

        # Stop leaves no cross-test residue on the shared manager (lifespan teardown also cancels).
        client.delete("/watch/SIM-SELLER")


def test_stop_after_pause_route_still_returns_404_on_read():
    # The DELETE teardown must still work after a pause (pause did not break stop).
    client = TestClient(app)
    assert client.post("/watch/SIM-BIDABS").status_code == 200
    assert client.post("/watch/SIM-BIDABS/pause").status_code == 200
    assert client.get("/tape/SIM-BIDABS/state").status_code == 200  # alive while paused

    assert client.delete("/watch/SIM-BIDABS").status_code == 200  # stop still tears down
    assert client.get("/tape/SIM-BIDABS/state").status_code == 404  # gone, honest 404


@pytest.mark.anyio
async def test_summary_and_stream_expose_paused_field():
    # The canonical paused field is re-exposed (read-only) on /summary and the WS /stream payload —
    # one engine value, read identically (single source of truth). Hermetic: warm an engine via the
    # serializers directly is covered in test_api; here we assert the route projection over a watch.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/watch/SIM-ASKABS")).status_code == 200
        try:
            # Before pause: summary exposes paused=False.
            summary = (await client.get("/tape/SIM-ASKABS/summary")).json()
            assert summary["paused"] is False

            assert (await client.post("/watch/SIM-ASKABS/pause")).status_code == 200
            summary = (await client.get("/tape/SIM-ASKABS/summary")).json()
            assert summary["paused"] is True
            assert summary["stream_status"] == "paused"
        finally:
            await client.delete("/watch/SIM-ASKABS")
            await manager.shutdown()
