"""The ``/research/studies/*`` endpoints (capability 32, J-60/J-61) — create / list / get / cancel.

Serves the runner's persisted payload VERBATIM (the UI computes nothing). Covers the create + start
happy path (background job → done), the full 422/404/409 error matrix, the taxonomy studies copy,
and the arbitrary-window-without-credentials explicit refusal (never fixture-substituted).

Injects a temp-path store + registry via the existing dependency-override pattern (hermetic). A
created study runs as a real background job; the test polls until terminal (bounded).
"""

import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, get_market_adapter, manager
from app.research.feed_basis import data_feed_for_scenario
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore
from fakes import FakeAdapter


@pytest.fixture
def ctx(tmp_path):
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as c:
        yield c, store, registry
    registry.study_jobs.join_all(timeout=10.0)
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    store.close()


def _poll_until_terminal(client, study_id, attempts=200):
    for _ in range(attempts):
        pl = client.get(f"/research/studies/{study_id}").json()["study"]
        if pl["status"] in ("done", "failed", "cancelled"):
            return pl
        time.sleep(0.05)
    raise AssertionError(f"study {study_id} did not reach a terminal status")


# --- create + start (background job → done) ------------------------------------------------------

def test_create_sim_study_runs_to_done_with_baseline(ctx):
    client, _store, _reg = ctx
    r = client.post(
        "/research/studies",
        json={"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"},
    )
    assert r.status_code == 200
    created = r.json()["study"]
    assert created["status"] == "queued"
    pl = _poll_until_terminal(client, created["id"])
    assert pl["status"] == "done"
    # Results carry the setup distribution side-by-side with the seeded null baseline.
    assert pl["aggregates"]["setup"]["n"] == 1
    assert pl["aggregates"]["null_baseline"]["n"] == 100
    assert pl["data_feed"] == "sim"
    assert pl["config_fingerprint"] == CONFIG.config_fingerprint()


def test_get_serves_persisted_payload_verbatim(ctx):
    client, store, _reg = ctx
    r = client.post(
        "/research/studies",
        json={"source_kind": "sim", "source_id": "SIM-BUYER", "setup_type": "trend_continuation", "direction": "long"},
    )
    sid = r.json()["study"]["id"]
    pl = _poll_until_terminal(client, sid)
    # The served payload equals the store's persisted record (no recompute at read).
    assert pl == store.get_study(sid).payload


def test_list_returns_created_studies(ctx):
    client, _store, _reg = ctx
    r = client.post(
        "/research/studies",
        json={"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"},
    )
    _poll_until_terminal(client, r.json()["study"]["id"])
    listed = client.get("/research/studies").json()["studies"]
    assert len(listed) == 1
    assert listed[0]["id"] == r.json()["study"]["id"]


# --- error matrix --------------------------------------------------------------------------------

def test_unknown_setup_is_422(ctx):
    client, _store, _reg = ctx
    r = client.post(
        "/research/studies",
        json={"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "nope", "direction": "long"},
    )
    assert r.status_code == 422


def test_unknown_direction_is_422(ctx):
    client, _store, _reg = ctx
    r = client.post(
        "/research/studies",
        json={"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "sideways"},
    )
    assert r.status_code == 422


def test_unknown_source_kind_is_422(ctx):
    client, _store, _reg = ctx
    r = client.post(
        "/research/studies",
        json={"source_kind": "telepathy", "source_id": "X", "setup_type": "absorption_reversal", "direction": "long"},
    )
    assert r.status_code == 422


def test_level_setup_without_level_is_422_never_guessed(ctx):
    client, _store, _reg = ctx
    r = client.post(
        "/research/studies",
        json={"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "level_break", "direction": "long"},
    )
    assert r.status_code == 422
    assert "level" in r.json()["detail"].lower()


def test_level_on_non_level_setup_is_422(ctx):
    client, _store, _reg = ctx
    r = client.post(
        "/research/studies",
        json={"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long", "level_price": 100.0},
    )
    assert r.status_code == 422


def test_unknown_sim_scenario_is_422(ctx):
    client, _store, _reg = ctx
    r = client.post(
        "/research/studies",
        json={"source_kind": "sim", "source_id": "SIM-NOPE", "setup_type": "absorption_reversal", "direction": "long"},
    )
    assert r.status_code == 422


def test_historical_missing_window_is_422(ctx):
    client, _store, _reg = ctx
    # A credentialed adapter is injected, but no start/end -> 422 (never a guessed window).
    app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(available=True)
    r = client.post(
        "/research/studies",
        json={"source_kind": "historical", "source_id": "AAPL", "setup_type": "trend_continuation", "direction": "long"},
    )
    assert r.status_code == 422


def test_historical_end_before_start_is_422(ctx):
    client, _store, _reg = ctx
    app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(available=True)
    r = client.post(
        "/research/studies",
        json={
            "source_kind": "historical",
            "source_id": "AAPL",
            "setup_type": "trend_continuation",
            "direction": "long",
            "start": "2026-06-09T17:10:00Z",
            "end": "2026-06-09T17:00:00Z",
        },
    )
    assert r.status_code == 422


def test_arbitrary_window_without_credentials_is_explicit_unavailable_never_fixture(ctx):
    client, _store, _reg = ctx
    # No credentials -> the historical study is REFUSED explicitly, never fixture-substituted.
    app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(available=False)
    r = client.post(
        "/research/studies",
        json={
            "source_kind": "historical",
            "source_id": "AAPL",
            "setup_type": "trend_continuation",
            "direction": "long",
            "start": "2026-06-09T17:00:00Z",
            "end": "2026-06-09T17:10:00Z",
        },
    )
    assert r.status_code == 422
    assert "unavailable" in r.json()["detail"].lower()


def test_cancel_unknown_id_is_404(ctx):
    client, _store, _reg = ctx
    assert client.post("/research/studies/nope/cancel").status_code == 404


def test_get_unknown_id_is_404(ctx):
    client, _store, _reg = ctx
    assert client.get("/research/studies/nope").status_code == 404


def test_cancel_terminal_study_is_409(ctx):
    client, _store, _reg = ctx
    r = client.post(
        "/research/studies",
        json={"source_kind": "sim", "source_id": "SIM-REVERSAL", "setup_type": "absorption_reversal", "direction": "long"},
    )
    sid = r.json()["study"]["id"]
    _poll_until_terminal(client, sid)
    # A done study cannot be cancelled.
    assert client.post(f"/research/studies/{sid}/cancel").status_code == 409


# --- the creation-time data_feed stamp consolidates to the ONE feed mapping (iter-25, J-66) -------
# The iter-24 reviewer NOTE: the study-create route hardcoded ``data_feed = "sip"`` for the reference
# and historical kinds (a literal feed string) instead of reading the registered row-26 canonical
# source (``feed_basis.data_feed_for_scenario`` / the config-owned ``historical_feed`` key). This is the
# exact feed-honesty drift the J-66 copy/stamp sweep exists to close. The consolidation reads
# ``registry.config.historical_feed`` — the SAME key the one mapping exposes for the historical-replay
# path — so the CREATE-time stamp equals the mapping's output (and equals the runner's later re-stamp of
# the resolved ``historical ...`` descriptor) by construction. Defaults unchanged ⇒ byte-identical "sip".

def test_reference_study_creation_stamp_equals_the_one_feed_mapping(ctx):
    client, _store, _reg = ctx
    # The reference kind loads the committed SIP fixture (no credentials); the queued payload carries
    # the create-time data_feed stamp BEFORE the background run re-stamps the resolved descriptor.
    r = client.post(
        "/research/studies",
        json={
            "source_kind": "reference",
            "source_id": "PG_SIP_REFERENCE",
            "setup_type": "trend_continuation",
            "direction": "long",
        },
    )
    assert r.status_code == 200
    created = r.json()["study"]
    # The create-time stamp equals the ONE mapping's output for the resolved reference descriptor
    # (``historical PG reference`` -> config.historical_feed) — NOT a hardcoded literal. Defaults => "sip".
    assert created["data_feed"] == data_feed_for_scenario("historical PG reference", CONFIG)
    assert created["data_feed"] == CONFIG.historical_feed
    assert created["data_feed"] == "sip"  # the default is byte-identical to the prior hardcoded literal


def test_historical_study_creation_stamp_equals_the_one_feed_mapping(ctx):
    client, _store, _reg = ctx
    # A credentialed adapter is injected so the create path accepts the historical study (the background
    # run may then fail to fetch — irrelevant here; we assert ONLY the create-time stamp on the queued
    # payload). The stamp consolidates to the one mapping's historical-feed output, not a literal.
    app.dependency_overrides[get_market_adapter] = lambda: FakeAdapter(available=True)
    r = client.post(
        "/research/studies",
        json={
            "source_kind": "historical",
            "source_id": "AAPL",
            "setup_type": "trend_continuation",
            "direction": "long",
            "start": "2026-06-09T17:00:00Z",
            "end": "2026-06-09T17:10:00Z",
        },
    )
    assert r.status_code == 200
    created = r.json()["study"]
    # The create-time stamp equals the ONE mapping's output for the resolved historical descriptor
    # (``historical AAPL`` -> config.historical_feed) — NOT a hardcoded literal. Defaults => "sip".
    assert created["data_feed"] == data_feed_for_scenario("historical AAPL", CONFIG)
    assert created["data_feed"] == CONFIG.historical_feed
    assert created["data_feed"] == "sip"


# --- taxonomy studies copy (the frontend hardcodes none) -----------------------------------------

def test_taxonomy_carries_studies_copy_with_each_status_distinct(ctx):
    client, _store, _reg = ctx
    tax = client.get("/research/taxonomy").json()
    studies = tax["studies"]
    status_ids = {s["id"] for s in studies["statuses"]}
    assert status_ids == {"queued", "running", "done", "cancelled", "failed"}
    # Each status carries its OWN explicit absence sentence (iter-15 lesson — no shared fallback).
    absence = studies["status_absence"]
    sentences = [absence["queued"], absence["running"], absence["cancelled"], absence["failed"]]
    assert len(set(sentences)) == 4  # all distinct
    # The measurement framing + null-baseline caption are present (the honesty register).
    assert "random-arm-time baseline" in studies["copy"]["measurement_framing"]
    assert studies["copy"]["null_baseline_caption"]
    assert studies["copy"]["hindsight_level_label"]
