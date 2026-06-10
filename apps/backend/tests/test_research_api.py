"""Research API (capability 23/24): POST /research/thesis validation matrix (404/409/422 both
directions), nothing persisted on rejection, taxonomy endpoint, REST==WS thesis projection verbatim.

Each test injects a TEMP-PATH journal store + registry (the existing dependency-override pattern)
so the suite stays hermetic — no real journal file is written. The app's module-level WatchManager
is wired to the registry's engine-created hook for the duration of the test."""

import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, manager
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore


@pytest.fixture
def client(tmp_path):
    # Inject a temp-path store + registry BEFORE the app starts, so the lifespan leaves it in place
    # (skips building the default file store). Wire the WatchManager hook to it.
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as c:
        yield c
    # Teardown: stop any leftover watches, clear the registry + hook, close the store.
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    store.close()


def _watch_bidabs(client: TestClient) -> None:
    """Watch SIM-BIDABS and wait until it warms to bid_absorption with a last price."""
    r = client.post("/watch/SIM-BIDABS")
    assert r.status_code == 200
    deadline = time.time() + 10
    while time.time() < deadline:
        summary = client.get("/tape/SIM-BIDABS/summary").json()
        if summary.get("market", {}).get("last") is not None and summary.get("tape_state") == "bid_absorption":
            return
        time.sleep(0.1)
    raise AssertionError("SIM-BIDABS did not warm to bid_absorption in time")


# --- taxonomy ------------------------------------------------------------------------------------

def test_taxonomy_endpoint_lists_setups_directions_verdicts(client):
    payload = client.get("/research/taxonomy").json()
    setup_ids = {s["id"] for s in payload["setups"]}
    assert setup_ids == {
        "absorption_reversal",
        "trend_continuation",
        "level_break",
        "failed_move_fade",
    }
    # The per-setup level requirement is taxonomy-owned (the frontend hardcodes none of it).
    by_id = {s["id"]: s for s in payload["setups"]}
    assert by_id["level_break"]["requires_level"] is True
    assert by_id["failed_move_fade"]["requires_level"] is True
    assert by_id["absorption_reversal"]["requires_level"] is False
    assert by_id["trend_continuation"]["requires_level"] is False
    assert {d["id"] for d in payload["directions"]} == {"long", "short"}
    assert "pending" in {v["id"] for v in payload["verdicts"]}
    assert payload["disclaimer"].startswith("Descriptive only")


# --- 404 / 409 -----------------------------------------------------------------------------------

def test_declare_on_unwatched_ticker_is_404_nothing_persisted(client):
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 404
    # Nothing persisted on rejection.
    assert client.get("/research/thesis/active?ticker=SIM-BIDABS").json()["thesis"] is None


def test_valid_declare_then_second_is_409(client):
    _watch_bidabs(client)
    body = {
        "ticker": "SIM-BIDABS",
        "setup_type": "absorption_reversal",
        "direction": "long",
        "invalidation_price": 99.0,
    }
    r1 = client.post("/research/thesis", json=body)
    assert r1.status_code == 200
    r2 = client.post("/research/thesis", json=body)
    assert r2.status_code == 409
    assert "active thesis" in r2.json()["detail"].lower()


# --- 422 validation matrix -----------------------------------------------------------------------

def test_wrong_side_invalidation_long_is_422_nothing_persisted(client):
    _watch_bidabs(client)
    # last == 100.0; a LONG invalidation at/above last is wrong-side.
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 101.0,
        },
    )
    assert r.status_code == 422
    assert "below" in r.json()["detail"].lower()
    assert client.get("/research/thesis/active?ticker=SIM-BIDABS").json()["thesis"] is None


def test_wrong_side_invalidation_short_is_422(client):
    _watch_bidabs(client)
    # A SHORT invalidation at/below last is wrong-side.
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "trend_continuation",
            "direction": "short",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 422
    assert "above" in r.json()["detail"].lower()


def test_level_setup_without_level_is_422(client):
    _watch_bidabs(client)
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "level_break",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 422
    assert "level" in r.json()["detail"].lower()


def test_non_level_setup_with_level_is_422(client):
    _watch_bidabs(client)
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
            "level_price": 100.5,
        },
    )
    assert r.status_code == 422
    assert "does not take a level" in r.json()["detail"].lower()


def test_unknown_setup_enum_is_422(client):
    _watch_bidabs(client)
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "moon_shot",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 422
    assert "setup_type" in r.json()["detail"].lower()


def test_unknown_direction_enum_is_422(client):
    _watch_bidabs(client)
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "sideways",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 422
    assert "direction" in r.json()["detail"].lower()


# --- success projection --------------------------------------------------------------------------

def test_valid_declare_returns_full_projection_and_pending(client):
    _watch_bidabs(client)
    r = client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    assert r.status_code == 200
    thesis = r.json()["thesis"]
    assert thesis["setup_type"] == "absorption_reversal"
    assert thesis["direction"] == "long"
    assert thesis["invalidation_price"] == 99.0
    assert thesis["verdict"] == "pending"
    assert thesis["bound_source"] == "bid_absorption"  # scenario descriptor, not the ticker
    assert thesis["data_feed"] == "sim"
    assert thesis["config_fingerprint"] == CONFIG.config_fingerprint()
    assert "risk_flags" not in thesis  # omitted entirely this iteration
    assert len(thesis["statements"]) == 2
    assert all("status" in s and "text" in s for s in thesis["statements"])
    # The initial pending verdict event is recorded (timeline starts at declaration).
    assert thesis["monitor_status"] == "ok"


def test_active_read_null_is_normal_before_any_declare(client):
    _watch_bidabs(client)
    r = client.get("/research/thesis/active?ticker=SIM-BIDABS")
    assert r.status_code == 200
    assert r.json()["thesis"] is None  # a normal state, not an error


def test_rest_active_equals_ws_thesis_key_verbatim(client):
    _watch_bidabs(client)
    client.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BIDABS",
            "setup_type": "absorption_reversal",
            "direction": "long",
            "invalidation_price": 99.0,
        },
    )
    rest = client.get("/research/thesis/active?ticker=SIM-BIDABS").json()["thesis"]
    assert rest is not None
    with client.websocket_connect("/tape/SIM-BIDABS/stream") as ws:
        frame = ws.receive_json()
    ws_thesis = frame["thesis"]
    # Data-contract row 15: the WS thesis key MUST equal the REST projection verbatim. Both come
    # from the SAME monitor.projection(); the only fields that can drift are the live statement
    # statuses (recomputed per call from the current snapshot). Assert the stable thesis fields are
    # byte-identical and statuses are from the same enum.
    for key in (
        "id",
        "setup_type",
        "direction",
        "invalidation_price",
        "level_price",
        "verdict",
        "bound_source",
        "data_feed",
        "config_fingerprint",
        "entry_context",
        "monitor_status",
    ):
        assert rest[key] == ws_thesis[key], f"REST/WS diverged on {key}"
    assert [s["text"] for s in rest["statements"]] == [s["text"] for s in ws_thesis["statements"]]


def test_ws_thesis_key_is_null_when_none(client):
    _watch_bidabs(client)
    with client.websocket_connect("/tape/SIM-BIDABS/stream") as ws:
        frame = ws.receive_json()
    assert "thesis" in frame
    assert frame["thesis"] is None
