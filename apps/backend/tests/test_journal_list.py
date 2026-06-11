"""Journal LIST endpoint (J-51): ``GET /research/journal`` — the ONLY serving path for journal rows.

ONE row-projection function over the persisted theses rows (id, ticker, bound source, data_feed,
config_fingerprint, setup, direction, declared logical+wall timestamps, status, resolution incl. the
VERBATIM persisted expired/interruption reason, entry/exit-mark presence) — nothing recomputed at
read. Filters (ticker / setup_type / direction / resolution / status) + limit/offset; unknown enum
filter values are 422 (never silent coercion); the page size is config-owned and CLAMPED to the max.

These tests inject a temp-path store + registry directly (the existing dependency-override pattern)
and seed rows straight into the store, so the suite is hermetic and does NOT need a live sim watch to
exercise the read path. (The declare→resolve→restart end-to-end is covered browser-side by J-51.)
"""

import dataclasses

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, manager
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import ActionRecord, JournalStore, ThesisRecord, VerdictEventRecord


def _thesis(
    tid: str,
    *,
    ticker: str = "SIM-BUYER",
    setup_type: str = "trend_continuation",
    direction: str = "long",
    status: str = "active",
    created_wall_ts: float,
    bound_source: str = "buyer_control",
    data_feed: str = "sim",
) -> ThesisRecord:
    return ThesisRecord(
        id=tid,
        ticker=ticker,
        setup_type=setup_type,
        direction=direction,
        invalidation_price=99.0,
        level_price=None,
        status=status,
        bound_source=bound_source,
        data_feed=data_feed,
        config_fingerprint="abc123",
        entry_context={"last": 100.0, "tape_state": "buyer_control"},
        statements=[{"text": "x", "kind": "tape_state_is", "params": {"states": ["buyer_control"]}}],
        created_logical_ts=12.5,
        created_wall_ts=created_wall_ts,
    )


@pytest.fixture
def ctx(tmp_path):
    """A temp-path store + registry wired into the app for the duration of the test."""
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


# --- taxonomy owns status / resolution labels (J-51) ---------------------------------------------

def test_taxonomy_owns_status_and_resolution_labels(ctx):
    client, _ = ctx
    payload = client.get("/research/taxonomy").json()
    statuses = {s["id"]: s["name"] for s in payload["statuses"]}
    assert statuses["active"] == "Active"
    assert statuses["played_out"] == "Played out"
    assert statuses["expired"] == "Expired"
    # The resolution subset is the four terminal statuses (a resolution IS a terminal status).
    assert {r["id"] for r in payload["resolutions"]} == {
        "played_out", "abandoned", "invalidated", "expired"
    }


# --- empty store ---------------------------------------------------------------------------------

def test_empty_store_returns_empty_rows(ctx):
    client, _ = ctx
    payload = client.get("/research/journal").json()
    assert payload["rows"] == []


# --- ordering + verbatim row shape ---------------------------------------------------------------

def test_rows_newest_declared_first_and_verbatim(ctx):
    client, store = ctx
    store.insert_thesis(_thesis("old", created_wall_ts=1700000000.0))
    store.insert_thesis(
        _thesis("new", created_wall_ts=1700000200.0, bound_source="historical AAPL 2024-01-02",
                data_feed="sip")
    )
    rows = client.get("/research/journal").json()["rows"]
    assert [r["id"] for r in rows] == ["new", "old"]
    new_row = rows[0]
    # Every field is a VERBATIM read of the persisted record (nothing recomputed at read).
    assert new_row["ticker"] == "SIM-BUYER"
    assert new_row["bound_source"] == "historical AAPL 2024-01-02"
    assert new_row["data_feed"] == "sip"
    assert new_row["config_fingerprint"] == "abc123"
    assert new_row["setup_type"] == "trend_continuation"
    assert new_row["direction"] == "long"
    assert new_row["status"] == "active"
    assert new_row["created_logical_ts"] == 12.5
    assert new_row["created_wall_ts"] == 1700000200.0
    # An active thesis has no resolution (honest absence — never a fabricated terminal state).
    assert new_row["resolution"] is None
    assert new_row["resolution_reason"] is None
    # Entry/exit-mark presence is an explicit boolean (never inferred from a price).
    assert new_row["has_entry"] is False
    assert new_row["has_exit"] is False
    # Grade / reviewed fields are NOT fabricated this iteration (honest omission — they land with
    # J-56/J-57). The key is absent, not an empty/dishonest value.
    assert "outcome_grade" not in new_row
    assert "process_grade" not in new_row
    assert "reviewed" not in new_row


# --- resolution + verbatim expired/interruption reason -------------------------------------------

def test_played_out_row_carries_resolution_and_reason(ctx):
    client, store = ctx
    store.insert_thesis(_thesis("p", status="active", created_wall_ts=1.0))
    store.resolve_thesis_with_event(
        "p",
        "played_out",
        VerdictEventRecord("p", 5.0, 1700000005.0, "played_out",
                           "You resolved this thesis as played out — the idea has run its course.",
                           "buyer_control", 0.7, 100.4),
    )
    [row] = client.get("/research/journal").json()["rows"]
    assert row["status"] == "played_out"
    assert row["resolution"] == "played_out"
    # The resolution reason is the VERBATIM persisted terminal-event evidence (never recomputed).
    assert row["resolution_reason"] == (
        "You resolved this thesis as played out — the idea has run its course."
    )


def test_expired_row_carries_verbatim_interruption_reason(ctx):
    client, store = ctx
    # An UNMARKED active thesis expired by the startup sweep carries its explicit interruption reason.
    store.insert_thesis(_thesis("e", status="active", created_wall_ts=1.0))
    store.expire_stale_actives(1700000123.0)
    [row] = client.get("/research/journal").json()["rows"]
    assert row["status"] == "expired"
    assert row["resolution"] == "expired"
    # The verbatim persisted reason — the sweep's explicit "expired on restart" evidence.
    assert "restart" in row["resolution_reason"]
    assert row["has_entry"] is False


def test_entry_marked_row_reports_marks_present(ctx):
    client, store = ctx
    store.insert_thesis(_thesis("m", status="active", created_wall_ts=1.0))
    store.insert_action(ActionRecord("a1", "m", "entry", 100.0, 1.0, 1700000001.0, 0.02))
    [row] = client.get("/research/journal").json()["rows"]
    # An entry-marked active thesis reads active/not-evaluated honestly with its mark presence shown.
    assert row["status"] == "active"
    assert row["has_entry"] is True
    assert row["has_exit"] is False


# --- filters (server-side, AND-combined) ---------------------------------------------------------

def test_filter_by_ticker_setup_direction_status(ctx):
    client, store = ctx
    store.insert_thesis(_thesis("a", ticker="SIM-BUYER", setup_type="trend_continuation",
                                direction="long", status="active", created_wall_ts=1.0))
    store.insert_thesis(_thesis("b", ticker="SIM-SELLER", setup_type="absorption_reversal",
                                direction="short", status="active", created_wall_ts=2.0))
    assert [r["id"] for r in client.get("/research/journal?ticker=SIM-SELLER").json()["rows"]] == ["b"]
    assert [r["id"] for r in client.get(
        "/research/journal?setup_type=trend_continuation").json()["rows"]] == ["a"]
    assert [r["id"] for r in client.get("/research/journal?direction=short").json()["rows"]] == ["b"]
    assert {r["id"] for r in client.get("/research/journal?status=active").json()["rows"]} == {"a", "b"}


def test_filter_by_resolution(ctx):
    client, store = ctx
    store.insert_thesis(_thesis("active1", status="active", created_wall_ts=1.0))
    store.insert_thesis(_thesis("done", status="active", created_wall_ts=2.0))
    store.resolve_thesis_with_event(
        "done", "played_out",
        VerdictEventRecord("done", 5.0, 1700000005.0, "played_out", "resolved", None, None, None),
    )
    rows = client.get("/research/journal?resolution=played_out").json()["rows"]
    assert [r["id"] for r in rows] == ["done"]


# --- 422 on unknown enum filter (never silent coercion) ------------------------------------------

@pytest.mark.parametrize(
    "param,value",
    [
        ("setup_type", "moon_shot"),
        ("direction", "sideways"),
        ("resolution", "vaporized"),
        ("status", "zombie"),
    ],
)
def test_unknown_enum_filter_is_422(ctx, param, value):
    client, _ = ctx
    r = client.get(f"/research/journal?{param}={value}")
    assert r.status_code == 422
    assert param in r.json()["detail"].lower() or value in r.json()["detail"].lower()


def test_unknown_ticker_filter_is_not_an_error(ctx):
    # A ticker is a free-form symbol, NOT an enum — an unknown ticker is a valid filter that simply
    # matches nothing (never a 422, never coercion).
    client, _ = ctx
    r = client.get("/research/journal?ticker=NOPE")
    assert r.status_code == 200
    assert r.json()["rows"] == []


# --- pagination + config-owned page-size clamping ------------------------------------------------

def test_limit_and_offset_paginate(ctx):
    client, store = ctx
    for i in range(5):
        store.insert_thesis(_thesis(f"t{i}", created_wall_ts=float(i)))
    page1 = client.get("/research/journal?limit=2&offset=0").json()["rows"]
    page2 = client.get("/research/journal?limit=2&offset=2").json()["rows"]
    assert [r["id"] for r in page1] == ["t4", "t3"]
    assert [r["id"] for r in page2] == ["t2", "t1"]


def test_default_page_size_applies_when_limit_omitted(tmp_path):
    # Inject more rows than the (test-shrunk) default page size to prove a default is applied. Uses a
    # file-path store (a ``:memory:`` store is not shared across the store's read/write connections).
    small = dataclasses.replace(CONFIG, journal_list_default_limit=3, journal_list_max_limit=10)
    store2 = JournalStore(str(tmp_path / "default.db"), small)
    set_registry(ResearchRegistry(store2, small))
    manager.set_on_engine_created(None)
    try:
        with TestClient(app) as client:
            for i in range(7):
                store2.insert_thesis(_thesis(f"d{i}", created_wall_ts=float(i)))
            rows = client.get("/research/journal").json()["rows"]
            assert len(rows) == 3  # the config-owned default, applied when limit is omitted
            # Newest-first => d6, d5, d4.
            assert [r["id"] for r in rows] == ["d6", "d5", "d4"]
    finally:
        set_registry(None)
        store2.close()


def test_limit_above_max_is_clamped(tmp_path):
    small = dataclasses.replace(CONFIG, journal_list_default_limit=3, journal_list_max_limit=4)
    store2 = JournalStore(str(tmp_path / "clamp.db"), small)
    set_registry(ResearchRegistry(store2, small))
    manager.set_on_engine_created(None)
    try:
        with TestClient(app) as client:
            for i in range(10):
                store2.insert_thesis(_thesis(f"c{i}", created_wall_ts=float(i)))
            # Request well above the max — the route CLAMPS to journal_list_max_limit (a serving safety
            # bound, never a 422; an over-large page is honestly satisfied with the most rows served).
            rows = client.get("/research/journal?limit=9999").json()["rows"]
            assert len(rows) == 4
    finally:
        set_registry(None)
        store2.close()
