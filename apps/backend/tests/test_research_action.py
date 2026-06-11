"""Action marks (J-52): POST /research/thesis/{id}/action — verbatim entry/exit recording, the
guard matrix, spread-at-mark persistence, and the single-path realized-R projection.

A user journals their OWN already-taken entry/exit on the active thesis. The mark is recorded
VERBATIM (price exactly as submitted — never an inferred/simulated fill, never an order), stamped at
the current logical + wall time with the snapshot's spread-at-mark taken once at recording. The
realized move in R is computed by ONE shared projection function, so the row-15 thesis projection
and GET /research/journal/{id} return identical values (no second path, no client math).

Each test injects a TEMP-PATH journal store + registry via the existing dependency-override pattern
(hermetic — no real journal file)."""

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


def _declare(client: TestClient, ticker: str, last: float, *, invalidation: float | None = None) -> str:
    r = client.post(
        "/research/thesis",
        json={
            "ticker": ticker,
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": invalidation if invalidation is not None else round(last - 1.0, 2),
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["thesis"]["id"]


# --- happy path: entry then exit, verbatim, with spread-at-mark + realized R ---------------------

def test_mark_entry_then_exit_records_verbatim_with_spread_and_realized_r(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    # Invalidation 2.00 below entry so R is a clean known basis regardless of the exact last.
    tid = _declare(c, "SIM-BUYER", last, invalidation=round(last - 2.0, 2))

    entry_price = round(last, 2)
    r1 = c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": entry_price})
    assert r1.status_code == 200, r1.text
    proj = r1.json()["thesis"]
    marks = proj["marks"]
    # Entry recorded verbatim with logical/wall stamps + a moment spread (SIM has a live quote).
    assert marks["entry"]["price"] == entry_price
    assert marks["entry"]["kind"] == "entry"
    assert isinstance(marks["entry"]["logical_ts"], (int, float))
    assert isinstance(marks["entry"]["wall_ts"], (int, float))
    assert marks["entry"]["spread_at_mark"] is not None  # SIM quote present
    assert marks["has_entry"] is True
    assert marks["exit"] is None
    # R basis is present once entry exists; no realized move yet (no exit).
    assert marks["r_basis"] == pytest.approx(abs(entry_price - round(last - 2.0, 2)))
    assert marks["realized_r"] is None

    # Exit 1.00 above entry => a long realized move of +0.5R given the 2.00 R basis.
    exit_price = round(entry_price + 1.0, 2)
    r2 = c.post(f"/research/thesis/{tid}/action", json={"kind": "exit", "price": exit_price})
    assert r2.status_code == 200, r2.text
    marks2 = r2.json()["thesis"]["marks"]
    assert marks2["exit"]["price"] == exit_price
    assert marks2["exit"]["spread_at_mark"] is not None
    assert marks2["realized_r"] == pytest.approx(1.0 / marks2["r_basis"])
    assert marks2["realized_r"] > 0  # exited in the thesis's favor (long, higher)


def test_realized_r_single_path_projection_equals_journal_detail(client):
    # The realized-R single-path guarantee: the row-15 thesis projection and GET /journal/{id} return
    # IDENTICAL marks (no second computation path, no client math).
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last, invalidation=round(last - 2.0, 2))
    entry_price = round(last, 2)
    c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": entry_price})
    c.post(f"/research/thesis/{tid}/action", json={"kind": "exit", "price": round(entry_price + 1.0, 2)})

    active_marks = c.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]["marks"]
    journal_marks = c.get(f"/research/journal/{tid}").json()["marks"]
    assert active_marks == journal_marks
    # Both carry the same realized R + spread-at-mark on both marks (verbatim readback).
    assert active_marks["realized_r"] == journal_marks["realized_r"]
    assert active_marks["entry"]["spread_at_mark"] == journal_marks["entry"]["spread_at_mark"]
    assert active_marks["exit"]["spread_at_mark"] == journal_marks["exit"]["spread_at_mark"]


def test_no_marks_means_no_realized_metric_no_dishonest_zero(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    marks = c.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]["marks"]
    # No marks => entry/exit None, NO realized metric (no fabricated 0).
    assert marks["entry"] is None
    assert marks["exit"] is None
    assert marks["has_entry"] is False
    assert marks["r_basis"] is None
    assert marks["realized_r"] is None


# --- WS thesis key carries the marks verbatim (row-15 parity) -------------------------------------

def test_ws_thesis_key_carries_marks_after_entry(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last, invalidation=round(last - 2.0, 2))
    entry_price = round(last, 2)
    c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": entry_price})
    with c.websocket_connect("/tape/SIM-BUYER/stream") as ws:
        frame = ws.receive_json()
    assert frame["thesis"]["marks"]["entry"]["price"] == entry_price
    assert frame["thesis"]["marks"]["has_entry"] is True


# --- guard matrix --------------------------------------------------------------------------------

def test_action_unknown_thesis_is_404(client):
    c, _ = client
    r = c.post("/research/thesis/does-not-exist/action", json={"kind": "entry", "price": 100.0})
    assert r.status_code == 404


def test_action_unknown_kind_is_422(client):
    c, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    r = c.post(f"/research/thesis/{tid}/action", json={"kind": "scale_in", "price": last})
    assert r.status_code == 422
    assert "unknown action kind" in r.json()["detail"].lower()


def test_action_non_positive_price_is_422(client):
    c, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    for bad in (0.0, -5.0):
        r = c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": bad})
        assert r.status_code == 422, (bad, r.text)
        assert "positive" in r.json()["detail"].lower()
    # Nothing recorded — no entry mark on the thesis.
    assert c.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]["marks"]["entry"] is None


def test_action_malformed_price_is_422(client):
    c, _ = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    # A non-numeric price is rejected by the pydantic schema (422) before the route runs.
    r = c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": "abc"})
    assert r.status_code == 422


def test_action_duplicate_entry_is_409_single_record(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    r1 = c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": last})
    assert r1.status_code == 200
    r2 = c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": last + 0.5})
    assert r2.status_code == 409
    assert "already has an entry" in r2.json()["detail"].lower()
    # Exactly ONE entry persisted (the duplicate recorded nothing).
    entries = [a for a in store.get_actions(tid) if a.kind == "entry"]
    assert len(entries) == 1
    assert entries[0].price == last  # the first, verbatim


def test_action_duplicate_exit_is_409(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": last})
    r1 = c.post(f"/research/thesis/{tid}/action", json={"kind": "exit", "price": last + 1.0})
    assert r1.status_code == 200
    r2 = c.post(f"/research/thesis/{tid}/action", json={"kind": "exit", "price": last + 2.0})
    assert r2.status_code == 409
    assert "already has an exit" in r2.json()["detail"].lower()
    assert len([a for a in store.get_actions(tid) if a.kind == "exit"]) == 1


def test_action_exit_before_entry_is_409(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    r = c.post(f"/research/thesis/{tid}/action", json={"kind": "exit", "price": last + 1.0})
    assert r.status_code == 409
    assert "before an entry" in r.json()["detail"].lower()
    assert store.get_actions(tid) == []  # nothing recorded


def test_action_on_resolved_thesis_is_409(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "played_out"})
    r = c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": last})
    assert r.status_code == 409
    assert "already resolved" in r.json()["detail"].lower()
    assert store.get_actions(tid) == []


# --- entry-marked refuses abandon still green (anti-survivorship, via the live endpoint) ----------

def test_entry_marked_refuses_abandon_via_endpoint(client):
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": last})
    # The projection exposes the entry-marked fact (the UI reads it to withdraw Abandon).
    assert c.get("/research/thesis/active?ticker=SIM-BUYER").json()["thesis"]["marks"]["has_entry"] is True
    # Abandon is refused (409) — anti-survivorship.
    r = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "abandoned"})
    assert r.status_code == 409
    assert "abandon" in r.json()["detail"].lower()
    # Played out still works on the entry-marked thesis (a real position runs its course).
    ok = c.post(f"/research/thesis/{tid}/resolve", json={"resolution": "played_out"})
    assert ok.status_code == 200


def test_double_click_entry_yields_one_record_and_one_409(client):
    # Error-case from the spec: a double-submit yields one mark + one 409, no duplicate record.
    c, store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    r1 = c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": last})
    r2 = c.post(f"/research/thesis/{tid}/action", json={"kind": "entry", "price": last})
    assert {r1.status_code, r2.status_code} == {200, 409}
    assert len([a for a in store.get_actions(tid) if a.kind == "entry"]) == 1
