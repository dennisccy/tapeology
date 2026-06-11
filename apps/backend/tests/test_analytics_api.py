"""Segregated journal analytics endpoint (capability 31, J-59): ``GET /research/analytics``.

The single serving path for the J-59 aggregates — it must serve the analytics MODULE's projection
VERBATIM (the frontend renders it directly). Plus:
  * the empty journal serves an honest empty payload (not an error, not fabricated groups);
  * the taxonomy carries the analytics display copy (the frontend hardcodes no label);
  * ``analytics_min_sample_size`` is a SERVING-ONLY key — changing it does NOT change
    ``config_fingerprint`` (the documented iter-12 page-size precedent).

Injects a temp-path store + registry via the existing dependency-override pattern (hermetic — no
live sim watch needed for the read path).
"""

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG, Config
from app.main import app, manager
from app.research.analytics import compute_analytics
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore, ThesisRecord


def _thesis(tid: str, *, data_feed: str = "sim", config_fingerprint: str = "abc123") -> ThesisRecord:
    return ThesisRecord(
        id=tid,
        ticker="SIM-BIDABS",
        setup_type="absorption_reversal",
        direction="long",
        invalidation_price=99.0,
        level_price=None,
        status="played_out",
        bound_source="bid_absorption",
        data_feed=data_feed,
        config_fingerprint=config_fingerprint,
        entry_context={"last": 100.0, "tape_state": "bid_absorption"},
        statements=[{"text": "x", "kind": "tape_state_is", "params": {"states": ["bid_absorption"]}}],
        created_logical_ts=0.0,
        created_wall_ts=1700000000.0,
    )


@pytest.fixture
def ctx(tmp_path):
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


def test_endpoint_serves_module_projection_verbatim(ctx):
    client, store = ctx
    store.insert_thesis(_thesis("t1", data_feed="sim", config_fingerprint="fp1"))
    store.insert_thesis(_thesis("t2", data_feed="iex", config_fingerprint="fp1"))
    served = client.get("/research/analytics").json()
    expected = compute_analytics(store, CONFIG)
    assert served == expected
    # Two distinct feeds => two partitions (never pooled).
    assert {p["data_feed"] for p in served["partitions"]} == {"sim", "iex"}


def test_empty_journal_returns_honest_empty_payload(ctx):
    client, _store = ctx
    served = client.get("/research/analytics").json()
    assert served["partitions"] == []
    assert served["min_sample_size"] == CONFIG.analytics_min_sample_size


def test_taxonomy_carries_analytics_display_copy(ctx):
    client, _store = ctx
    payload = client.get("/research/taxonomy").json()
    assert "analytics" in payload
    analytics = payload["analytics"]
    # The required taxonomy-owned labels (the frontend hardcodes none of these).
    for key in (
        "abandonment_label",
        "insufficient_sample_label",
        "truncated_label",
        "spread_per_r_caption",
        "measurement_framing",
    ):
        assert key in analytics and isinstance(analytics[key], str) and analytics[key]


# --- fingerprint stability (the deliberate serving-only exclusion) -------------------------------

def test_changing_analytics_min_sample_size_does_not_change_fingerprint():
    base = Config().config_fingerprint()
    bumped = Config(analytics_min_sample_size=99).config_fingerprint()
    assert base == bumped   # serving-only key is excluded from the fingerprint (no pool fragmentation)


def test_changing_a_real_threshold_does_change_fingerprint():
    # A sanity counter-test: a genuine classifier/research threshold DOES move the fingerprint.
    base = Config().config_fingerprint()
    changed = Config(excursion_target_r=2.0).config_fingerprint()
    assert base != changed
