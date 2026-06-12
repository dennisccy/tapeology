"""Feeder-level freshness integration (J-64) — the iter-21 lesson made binding.

These tests drive the REAL app / WatchManager / engine-observer seam (NOT the pure evaluator in
isolation) across an ACTUAL status flip, reproducing the iter-21 evaluator's confirmed live defect:
after a ``POST /watch/{ticker}/pause`` the served ``/research/thesis/active`` projection used to keep
reading a frozen-green ``conditions_met`` over a paused tape because the monitor advanced its checklist
only in ``on_event`` and served the checklist from the snapshot captured at the LAST event — status
flips travel via ``on_status``, which never refreshed the served checklist.

The fix (iter-22): on every non-terminal ``on_status`` flip (``paused`` / ``stale`` / the restore on
resume) the monitor re-reads the engine's CURRENT canonical snapshot (row-6 ``stream_status`` +
row-14 ``delivery_lag_seconds`` — a READ, the iter-9 precedent) and re-advances the checklist /
management-stance evaluators, so the dwell-exempt ``no_fresh_tape`` publishes IMMEDIATELY — no second
computation of any contract value, no new serving path.

Each test injects a TEMP-PATH journal store + registry (the existing dependency-override pattern), so
the suite stays hermetic. The verdict-confirming substrate is SIM-BUYER trend_continuation/long (the
proven ``conditions_met`` substrate — its checklist goes all-green once the verdict publishes
``confirming``; we POLL the served projection to TIME the pause click while the green is actually
showing, per the iter-11 lesson).
"""

import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, manager
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore


@pytest.fixture
def client(tmp_path):
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as c:
        yield c
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    store.close()


def _watch_until_state(client: TestClient, ticker: str, state: str, timeout: float = 12.0) -> None:
    r = client.post(f"/watch/{ticker}")
    assert r.status_code == 200
    deadline = time.time() + timeout
    while time.time() < deadline:
        summary = client.get(f"/tape/{ticker}/summary").json()
        if summary.get("market", {}).get("last") is not None and summary.get("tape_state") == state:
            return
        time.sleep(0.05)
    raise AssertionError(f"{ticker} did not warm to {state} in time")


def _declare_trend_long(client: TestClient, ticker: str, invalidation: float = 98.0) -> str:
    declared = client.post(
        "/research/thesis",
        json={
            "ticker": ticker,
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": invalidation,
        },
    ).json()["thesis"]
    assert declared["verdict"] == "pending"
    return declared["id"]


def _poll_until_conditions_met(client: TestClient, ticker: str, timeout: float = 14.0) -> dict:
    """Poll the SERVED projection until the entry checklist publishes ``conditions_met`` (the green
    substrate the pause click must degrade), and return that projection."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        proj = client.get(f"/research/thesis/active?ticker={ticker}").json()["thesis"]
        cl = (proj or {}).get("entry_checklist")
        if cl and cl["stance"]["value"] == "conditions_met":
            return proj
        time.sleep(0.05)
    raise AssertionError("entry checklist never published conditions_met")


def _checklist_check(checklist: dict, check_id: str) -> dict:
    return next(c for c in checklist["checks"] if c["check"] == check_id)


# --- the named reproduction probe: pause -> immediate no_fresh_tape, resume -> honest ------------

def test_pause_degrades_checklist_to_no_fresh_tape_immediately_then_resume_restores(client):
    _watch_until_state(client, "SIM-BUYER", "buyer_control")
    _declare_trend_long(client, "SIM-BUYER")

    # The green substrate: the served checklist publishes conditions_met (every check passing).
    green = _poll_until_conditions_met(client, "SIM-BUYER")
    assert _checklist_check(green["entry_checklist"], "feed_live")["passed"] is True

    # PAUSE through the real route (flips the engine status to "paused", fires on_status).
    assert client.post("/watch/SIM-BUYER/pause").status_code == 200

    # IMMEDIATELY (no dwell hold, no second poll loop) the served projection must read no_fresh_tape
    # with feed_live failing and its margin naming the paused status — the frozen green is gone.
    proj = client.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]
    cl = proj["entry_checklist"]
    assert cl["stance"]["value"] == "no_fresh_tape", cl["stance"]
    feed_live = _checklist_check(cl, "feed_live")
    assert feed_live["passed"] is False
    assert "paused" in feed_live["margin"]  # the margin names the actual (paused) status
    # tape_lag_ok / feed_live are the failing freshness checks named in the blockers.
    assert "feed_live" in cl["blockers"]
    # The summary confirms the capture was taken WHILE paused (iter-21 lesson cross-check).
    assert client.get("/tape/SIM-BUYER/summary").json()["stream_status"] == "paused"

    # RESUME restores honest live evaluation: no_fresh_tape clears. A re-green is dwell-gated, so we
    # accept conditions_met/conditions_not_met per live evidence — only assert the degradation cleared.
    assert client.post("/watch/SIM-BUYER/resume").status_code == 200
    deadline = time.time() + 12
    cleared = False
    while time.time() < deadline:
        proj = client.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]
        cl = proj["entry_checklist"]
        if cl["stance"]["value"] != "no_fresh_tape":
            cleared = True
            assert _checklist_check(cl, "feed_live")["passed"] is True
            assert "live" in _checklist_check(cl, "feed_live")["margin"]
            break
        time.sleep(0.05)
    assert cleared, "no_fresh_tape never cleared after resume"


def test_pause_no_fresh_tape_is_not_a_persisted_pre_pause_green(client):
    # A previously-green conditions_met MUST NOT persist over the paused tape — the degraded read is
    # NOT a frozen copy of the pre-pause projection; the stance flips and the failing checks are named.
    _watch_until_state(client, "SIM-BUYER", "buyer_control")
    _declare_trend_long(client, "SIM-BUYER")
    green = _poll_until_conditions_met(client, "SIM-BUYER")
    assert green["entry_checklist"]["stance"]["value"] == "conditions_met"
    assert green["entry_checklist"]["blockers"] == []  # nothing failing while green

    assert client.post("/watch/SIM-BUYER/pause").status_code == 200
    cl = client.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]["entry_checklist"]
    assert cl["stance"]["value"] == "no_fresh_tape"
    assert cl["blockers"], "a degraded checklist must name its failing freshness checks"


# --- the stale-flip variant on the SAME seam (the operator-gated live leg's monitor equivalent) ---

def test_stale_flip_degrades_checklist_to_no_fresh_tape_immediately(client):
    # J-15's real live-lull leg is operator-gated (goal.md); this exercises the IDENTICAL monitor seam
    # by flipping the running engine's canonical stream status to "stale" via its own setter, which
    # fires on_status("stale") through the real observer — the same seam pause uses.
    _watch_until_state(client, "SIM-BUYER", "buyer_control")
    _declare_trend_long(client, "SIM-BUYER")
    _poll_until_conditions_met(client, "SIM-BUYER")

    # Flip to stale through the canonical engine setter (the live feeder's watchdog path, exercised
    # here directly on the running engine — the SAME on_status seam).
    manager._engines["SIM-BUYER"].set_stream_status("stale")

    proj = client.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]
    cl = proj["entry_checklist"]
    assert cl["stance"]["value"] == "no_fresh_tape", cl["stance"]
    feed_live = _checklist_check(cl, "feed_live")
    assert feed_live["passed"] is False
    assert "stale" in feed_live["margin"]


# --- REST == WS verbatim AT/AFTER the status flip ------------------------------------------------

def test_rest_equals_ws_verbatim_at_pause_flip(client):
    # The WS frame at/after the pause flip carries the SAME degraded checklist as REST (one projection,
    # never a second path) — verbatim equality extended to a status-flip moment.
    _watch_until_state(client, "SIM-BUYER", "buyer_control")
    _declare_trend_long(client, "SIM-BUYER")
    _poll_until_conditions_met(client, "SIM-BUYER")
    assert client.post("/watch/SIM-BUYER/pause").status_code == 200

    rest = client.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]
    with client.websocket_connect("/tape/SIM-BUYER/stream") as ws:
        ws_thesis = ws.receive_json()["thesis"]

    assert rest["entry_checklist"]["stance"]["value"] == "no_fresh_tape"
    # The full checklist projection is byte-identical across REST and the WS thesis key.
    assert rest["entry_checklist"] == ws_thesis["entry_checklist"]


# --- closed-leg coverage: a stream end clears any green; nothing persists ------------------------

def test_closed_leg_unmarked_thesis_expires_no_green_persists(client):
    # An unmarked thesis carrying a (green or any) checklist: at stream end the thesis expires and the
    # projection clears — no green of any kind persists (the closed terminal path is honest-by-removal).
    _watch_until_state(client, "SIM-BUYER", "buyer_control")
    _declare_trend_long(client, "SIM-BUYER")
    # The checklist is being served live (pre-entry-mark path).
    proj = client.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]
    assert "entry_checklist" in proj

    # Stop the watch (a terminal "closed" with end_reason watch_stopped) — the unmarked thesis expires
    # and the projection clears to null. No frozen checklist survives the teardown.
    assert client.delete("/watch/SIM-BUYER").status_code == 200
    active = client.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]
    assert active is None
