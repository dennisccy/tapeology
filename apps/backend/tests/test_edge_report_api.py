"""``GET /research/edge-report`` (era-5B capability 6, J-04) -- route-level integration. Mirrors
``test_strategies_api.py``'s ``ctx`` fixture (TestClient + temp journal/dataset/bar dirs): the
route wiring, non-GET 405, byte-identity to the module's own ``run_strategy_comparison_report``,
and one real recorded-dataset smoke test through the ACTUAL ``POST /research/datasets`` route --
the full request path, never a direct module call (``test_edge_report.py`` covers the pure
computation's exact cell values and gate logic in isolation).
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, manager
from app.research.bars import BarStore
from app.research.datasets import DatasetStore
from app.research.edge_report import REGISTER, run_strategy_comparison_report
from app.research.routes import ResearchRegistry, get_bar_store, set_registry
from app.research.store import JournalStore


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    with TestClient(app) as c:
        yield c, store, tmp_path
    registry.backtest_jobs.join_all(timeout=10.0)
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    set_registry(None)
    store.close()


def test_edge_report_empty_registry_is_an_honest_200(ctx):
    client, _store, _tmp_path = ctx
    response = client.get("/research/edge-report")
    assert response.status_code == 200
    payload = response.json()
    assert payload["register"] == REGISTER
    assert payload["pnl_min_sample_size"] == CONFIG.pnl_min_sample_size
    assert payload["train"]["cells"] == []
    assert payload["holdout"]["cells"] == []
    assert payload["surviving_train_cells"] == []
    assert "champion" not in payload  # this report is never about a single champion pointer


def test_edge_report_matches_the_module_function_byte_for_byte(ctx):
    """Single source of truth: the route's JSON is a VERBATIM serving of
    ``run_strategy_comparison_report`` — never a second computation. Recording one dataset
    through the real API first proves this on a genuinely non-trivial (if still
    ``insufficient_sample``-shaped) payload, not merely the vacuous empty case."""
    client, store, tmp_path = ctx
    recorded = client.post(
        "/research/datasets",
        json={
            "source_kind": "reference",
            "split": "train",
            "start": "2026-06-09T17:00:00Z",
            "end": "2026-06-09T17:00:30Z",
        },
    )
    assert recorded.status_code == 200, recorded.text

    route_payload = client.get("/research/edge-report").json()
    dataset_store = DatasetStore(tmp_path / "datasets")
    bar_store = BarStore(tmp_path / "bars")
    direct = run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG)
    assert json.dumps(route_payload, sort_keys=True) == json.dumps(direct, sort_keys=True)
    # PG (the reference fixture's own symbol) is not a config-owned panel symbol, so this
    # recording honestly resolves no owning scan event -- still an empty, valid cell list.
    assert route_payload["train"]["cells"] == []


def test_edge_report_integrity_failure_is_an_explicit_500_never_a_partial_report(ctx, monkeypatch):
    """A dataset failing checksum verification aborts the WHOLE report — the
    ``create_backtest``/``DatasetIntegrityError`` precedent, mapped explicitly rather than
    surfacing a raw 500 traceback or a silently-partial 200."""
    client, _store, tmp_path = ctx
    recorded = client.post(
        "/research/datasets",
        json={
            "source_kind": "reference",
            "split": "train",
            "start": "2026-06-09T17:00:00Z",
            "end": "2026-06-09T17:00:30Z",
        },
    )
    assert recorded.status_code == 200, recorded.text
    dataset_id = recorded.json()["dataset"]["id"]
    path = tmp_path / "datasets" / f"{dataset_id}.json"
    data = json.loads(path.read_text())
    data["record"]["meta"]["checksum"] = "0" * 64  # tamper
    path.write_text(json.dumps(data))

    response = client.get("/research/edge-report")
    assert response.status_code == 500
    assert "integrity" in response.json()["detail"].lower()


def test_non_get_verbs_are_405_no_write_surface_exists(ctx):
    client, _store, _tmp_path = ctx
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)("/research/edge-report")
        assert response.status_code == 405, f"{method.upper()} must be Method Not Allowed"


def test_edge_report_route_wired_through_the_existing_get_bar_store_seam():
    """A coherence guard (never a second bar-store construction): the route depends on the SAME
    ``get_bar_store`` seam every other bar-reading route already uses."""
    import inspect

    from app.research import routes

    src = inspect.getsource(routes.get_edge_report)
    assert "Depends(get_bar_store)" in src
    assert "Depends(get_dataset_store)" in src
    assert get_bar_store is routes.get_bar_store


# --- The rebuildable result cache (era-5B J-08) — route-level wiring -----------------------------


def test_edge_report_route_wired_through_the_new_cache_dependency():
    """The route depends on the NEW ``get_edge_report_cache`` seam — the identical
    ``Depends(get_bar_index)`` pattern ``record_bar_series``/``list_bar_series`` already use for
    their own derived, DI-overridable cache."""
    import inspect

    from app.research import routes

    src = inspect.getsource(routes.get_edge_report)
    assert "Depends(get_edge_report_cache)" in src
    assert "cache=cache" in src


def test_edge_report_route_serves_a_warm_result_on_the_second_call_without_recomputing(ctx, monkeypatch):
    """The end-to-end proof J-08 exists for: TWO real HTTP requests against the SAME running
    backend, the second of which must never re-enter the expensive computation — proven by
    counting calls to ``_compute_strategy_comparison_report`` (the ONE real computer), not merely
    inferring it from response shape."""
    client, _store, _tmp_path = ctx
    recorded = client.post(
        "/research/datasets",
        json={
            "source_kind": "reference",
            "split": "train",
            "start": "2026-06-09T17:00:00Z",
            "end": "2026-06-09T17:00:30Z",
        },
    )
    assert recorded.status_code == 200, recorded.text

    from app.research import edge_report as edge_report_module

    calls = []
    real_compute = edge_report_module._compute_strategy_comparison_report

    def _counting_compute(*args, **kwargs):
        calls.append(1)
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(edge_report_module, "_compute_strategy_comparison_report", _counting_compute)

    first = client.get("/research/edge-report")
    second = client.get("/research/edge-report")

    assert first.status_code == 200 and second.status_code == 200
    assert len(calls) == 1  # the SECOND request served entirely from the warm cache
    assert first.json() == second.json()


def test_edge_report_route_response_is_byte_identical_whether_cache_is_cold_or_warm(ctx):
    client, _store, _tmp_path = ctx
    recorded = client.post(
        "/research/datasets",
        json={
            "source_kind": "reference",
            "split": "train",
            "start": "2026-06-09T17:00:00Z",
            "end": "2026-06-09T17:00:30Z",
        },
    )
    assert recorded.status_code == 200, recorded.text

    cold = client.get("/research/edge-report")
    warm = client.get("/research/edge-report")

    assert cold.status_code == 200 and warm.status_code == 200
    assert json.dumps(cold.json(), sort_keys=True) == json.dumps(warm.json(), sort_keys=True)


def test_edge_report_route_cache_db_lives_hermetically_beside_the_test_dataset_dir(ctx):
    """The ``get_bar_index`` "every existing test gets this hermetically for free" property,
    proven for the NEW cache seam too: the ``ctx`` fixture only points ``TAPEOLOGY_DATASET_DIR`` at
    a temp dir (never a dedicated cache env var), yet the cache DB must land inside that SAME temp
    tree — never the real package-anchored default (which would leak state across test runs)."""
    client, _store, tmp_path = ctx
    recorded = client.post(
        "/research/datasets",
        json={
            "source_kind": "reference",
            "split": "train",
            "start": "2026-06-09T17:00:00Z",
            "end": "2026-06-09T17:00:30Z",
        },
    )
    assert recorded.status_code == 200, recorded.text

    response = client.get("/research/edge-report")
    assert response.status_code == 200
    assert (tmp_path / "edge_report_cache.db").exists()
