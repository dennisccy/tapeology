"""``GET /research/pnl/ledger`` (era-3 capability 5, J-04) — exactly ONE route, GET only.

The route serves the stored ledger rows VERBATIM through the ONE ``ledger_projection`` read (the
same function the markdown render consumes), carrying the visible simulated register and the
config-owned "insufficient sample" labels. There is NO REST write surface for the ledger — any
non-GET verb on the path is FastAPI's default 405 (no handler exists). An empty ledger is an
honest 200 empty list, never an error.

Everything is keyless: the founding row is seeded through the REAL ``seed_founding_row`` path
(reference-window datasets recorded into a temp dir, real backtests run synchronously), then read
back over the API and cross-checked against the persisted backtest reports it cites.
"""

from __future__ import annotations

import dataclasses

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG, STRATEGY_V1_ID
from app.main import app, manager
from app.research.backtests import PROFILE_DEFAULT, REGISTER
from app.research.datasets import DatasetStore
from app.research.pnl_baseline import seed_founding_row
from app.research.pnl_ledger import render_history_markdown
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    with TestClient(app) as c:
        yield c, store
    registry.backtest_jobs.join_all(timeout=10.0)
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    set_registry(None)
    store.close()


def test_empty_ledger_is_an_honest_200_empty_list(ctx):
    client, _store = ctx
    response = client.get("/research/pnl/ledger")
    assert response.status_code == 200
    payload = response.json()
    assert payload["rows"] == []
    assert payload["register"] == REGISTER
    assert payload["min_sample_size"] == CONFIG.pnl_min_sample_size


def test_non_get_verbs_are_405_no_write_surface_exists(ctx):
    client, _store = ctx
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)("/research/pnl/ledger")
        assert response.status_code == 405, f"{method.upper()} must be Method Not Allowed"


def test_founding_row_served_verbatim_with_register_and_provenance(ctx, tmp_path):
    client, store = ctx
    dstore = DatasetStore(tmp_path / "datasets")
    created, _ = seed_founding_row(store, dstore, CONFIG)
    assert created is True
    response = client.get("/research/pnl/ledger")
    assert response.status_code == 200
    payload = response.json()
    assert payload["register"] == REGISTER
    (row,) = payload["rows"]
    # The founding marker id/title are the config-owned constants.
    assert row["enhancement_id"] == CONFIG.pnl_founding_enhancement_id
    assert row["title"] == CONFIG.pnl_founding_enhancement_title
    assert row["founding"] is True and row["baseline"] is None
    # Cross-surface single source of truth: the row's per-split values equal the persisted
    # backtest reports (row 31) it cites, fetched over THEIR canonical endpoint.
    for split in ("train", "holdout"):
        prov = row["provenance"][split]
        report = client.get(f"/research/backtests/{prov['backtest_id']}").json()["backtest"]
        agg = report["result"]["aggregates"]
        measured = row["candidate"][split]
        assert measured["net_r"] == agg["net_r"]
        assert measured["net_usd"] == agg["net_usd"]
        assert measured["n"] == agg["n"]
        assert prov["dataset_id"] == report["result"]["dataset"]["id"]
        assert prov["dataset_checksum"] == report["result"]["dataset"]["checksum"]
        assert report["result"]["dataset"]["split"] == split
        # The label marker is present per split with n still shown.
        assert isinstance(measured["insufficient_sample"], bool)
    assert row["provenance"]["strategy_id"] == STRATEGY_V1_ID
    assert row["provenance"]["profile"] == PROFILE_DEFAULT
    assert row["provenance"]["config_fingerprint"] == CONFIG.config_fingerprint()
    assert "created_utc" in row and "created_wall_ts" in row


def test_rest_and_markdown_show_identical_numbers_and_identical_labels(ctx, tmp_path):
    client, store = ctx
    dstore = DatasetStore(tmp_path / "datasets")
    seed_founding_row(store, dstore, CONFIG)
    # A minimum above any fixture n labels EVERY split on BOTH surfaces (the same one function);
    # a minimum of 0 labels NONE. The registry serves the replaced config for the REST leg.
    for min_n, expect_labeled in ((99, True), (0, False)):
        config = dataclasses.replace(CONFIG, pnl_min_sample_size=min_n)
        set_registry(ResearchRegistry(store, config))
        row = client.get("/research/pnl/ledger").json()["rows"][0]
        md = render_history_markdown(store, config)
        for split in ("train", "holdout"):
            measured = row["candidate"][split]
            assert measured["insufficient_sample"] is expect_labeled
            # Identical numbers across surfaces: the exact JSON values appear in the markdown.
            assert str(measured["net_r"]) in md
            assert str(measured["net_usd"]) in md
        assert ("insufficient sample" in md) is expect_labeled
        assert REGISTER in md
