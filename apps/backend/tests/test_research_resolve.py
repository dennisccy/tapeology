"""User-facing thesis resolution (J-50): POST /research/thesis/{id}/resolve.

A user may close their own declared thesis as ``played_out`` or ``abandoned`` ONLY; ``invalidated``
/ ``expired`` are system-owned (422). Resolution flips the terminal status AND appends ONE final
timeline event atomically (append-only — prior verdict events stay byte-identical), detaches verdict
evaluation (no verdict event appended after resolution), and frees the active-thesis slot so a
redeclare on the same ticker succeeds (no 409). An entry-marked thesis refuses ``abandoned``
(anti-survivorship), proven with a directly-inserted action row.

Each test injects a TEMP-PATH journal store + registry via the existing dependency-override pattern
(hermetic — no real journal file). The app's module-level WatchManager is wired to the registry's
engine-created hook for the duration of the test."""

import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, manager
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import ActionRecord, JournalStore


@pytest.fixture
def client(tmp_path):
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as c:
        yield c, store
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    store.close()


def _watch_until_state(client: TestClient, ticker: str, state: str, timeout: float = 12.0) -> float:
    r = client.post(f"/watch/{ticker}")
    assert r.status_code == 200
    deadline = time.time() + timeout
    while time.time() < deadline:
        summary = client.get(f"/tape/{ticker}/summary").json()
        last = summary.get("market", {}).get("last")
        if last is not None and summary.get("tape_state") == state:
            return last
        time.sleep(0.1)
    raise AssertionError(f"{ticker} did not warm to {state} in time")


def _declare(client: TestClient, ticker: str, last: float) -> str:
    r = client.post(
        "/research/thesis",
        json={
            "ticker": ticker,
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": round(last - 0.5, 2),
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["thesis"]["id"]


# --- happy paths ---------------------------------------------------------------------------------

def test_resolve_played_out_flips_status_and_appends_event(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)

    timeline_before = store.verdict_events(tid)
    n_before = len(timeline_before)

    r = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "played_out"})
    assert r.status_code == 200, r.text
    body = r.json()["thesis"]
    assert body["status"] == "played_out"
    assert isinstance(body["resolved_logical_ts"], (int, float))
    assert isinstance(body["resolved_wall_ts"], (int, float))

    # GET /research/journal/{id} serves the resolved record + appended final event.
    entry = c.get(f"/research/journal/{tid}").json()
    assert entry["thesis"]["status"] == "played_out"
    timeline = entry["timeline"]
    assert len(timeline) == n_before + 1  # exactly ONE appended row
    final = timeline[-1]
    assert final["verdict"] == "played_out"
    assert final["evidence"]  # plain-language evidence (no naked outputs)
    assert final["logical_ts"] is not None
    assert final["wall_ts"] is not None
    # Prior rows are byte-identical (append-only — never edited/backfilled).
    for before, after in zip(timeline_before, timeline[:n_before]):
        assert after["verdict"] == before.verdict
        assert after["evidence"] == before.evidence
        assert after["logical_ts"] == before.logical_ts
        assert after["wall_ts"] == before.wall_ts


def test_resolve_abandoned_flips_status(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    r = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "abandoned"})
    assert r.status_code == 200
    assert r.json()["thesis"]["status"] == "abandoned"
    assert c.get(f"/research/journal/{tid}").json()["thesis"]["status"] == "abandoned"


# --- active slot frees up + monitor detach -------------------------------------------------------

def test_active_returns_null_after_resolution_and_redeclare_succeeds(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    # Before resolution the active read returns the thesis.
    assert c.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"] is not None

    c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "played_out"})

    # After resolution the projection clears (a user resolution returns the strip to idle).
    assert c.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"] is None
    # The WS thesis key matches verbatim (row-15 parity — null).
    with c.websocket_connect("/tape/SIM-BUYER/stream") as ws:
        frame = ws.receive_json()
    assert frame["thesis"] is None

    # A redeclare on the same ticker now succeeds (the active-thesis uniqueness freed up — no 409).
    r = c.post(
        "/research/thesis",
        json={
            "ticker": "SIM-BUYER",
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": round(last - 0.5, 2),
        },
    )
    assert r.status_code == 200
    assert r.json()["thesis"]["id"] != tid


def test_no_verdict_events_appended_after_resolution(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "played_out"})

    # The final row is the resolution; let the engine keep streaming and confirm NOTHING is appended
    # after it (the monitor detached — the verdict stream stopped for this thesis).
    timeline_after_resolve = c.get(f"/research/journal/{tid}").json()["timeline"]
    last_verdict = timeline_after_resolve[-1]["verdict"]
    assert last_verdict == "played_out"
    n = len(timeline_after_resolve)
    time.sleep(2.0)  # SIM-BUYER keeps emitting events through the (now detached) monitor
    timeline_later = c.get(f"/research/journal/{tid}").json()["timeline"]
    assert len(timeline_later) == n, "a verdict event was appended AFTER resolution"
    assert timeline_later[-1]["verdict"] == "played_out"


# --- validation matrix ---------------------------------------------------------------------------

def test_resolve_unknown_id_is_404(client):
    c, _ = client
    r = c.post("/research/thesis/does-not-exist/resolve", json={"resolution": "played_out"})
    assert r.status_code == 404


def test_resolve_system_owned_invalidated_is_422(client):
    c, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    r = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "invalidated"})
    assert r.status_code == 422
    assert "system-owned" in r.json()["detail"].lower()
    # Nothing changed — still active.
    assert c.get(f"/research/journal/{tid}").json()["thesis"]["status"] == "active"


def test_resolve_system_owned_expired_is_422(client):
    c, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    r = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "expired"})
    assert r.status_code == 422
    assert "system-owned" in r.json()["detail"].lower()


def test_resolve_unknown_enum_is_422(client):
    c, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    r = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "moon"})
    assert r.status_code == 422
    assert "unknown resolution" in r.json()["detail"].lower()


def test_resolve_already_resolved_is_409_no_duplicate_event(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    r1 = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "played_out"})
    assert r1.status_code == 200
    timeline_after_first = c.get(f"/research/journal/{tid}").json()["timeline"]

    # A second resolve (e.g. a double-click) yields a 409 and appends NO duplicate event.
    r2 = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "abandoned"})
    assert r2.status_code == 409
    assert "already resolved" in r2.json()["detail"].lower()
    timeline_after_second = c.get(f"/research/journal/{tid}").json()["timeline"]
    assert len(timeline_after_second) == len(timeline_after_first)


def test_entry_marked_thesis_refuses_abandon(client):
    # The anti-survivorship rule: an entry-marked thesis can never be abandoned. No entry-mark UI
    # exists yet, so inject the action row directly via the store (spec-mandated proof).
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    store.insert_action(ActionRecord("act-1", tid, "entry", last, 0.0, time.time()))

    r = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "abandoned"})
    assert r.status_code == 409
    assert "abandon" in r.json()["detail"].lower()
    # Still active — the abandon was refused, nothing appended.
    assert c.get(f"/research/journal/{tid}").json()["thesis"]["status"] == "active"

    # The SAME entry-marked thesis CAN still be resolved played_out (a real position runs its course).
    ok = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "played_out"})
    assert ok.status_code == 200
    assert ok.json()["thesis"]["status"] == "played_out"
