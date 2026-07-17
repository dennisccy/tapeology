"""``GET /research/edge-report`` (era-5B capability 6, J-04) -- route-level integration. Mirrors
``test_strategies_api.py``'s ``ctx`` fixture (TestClient + temp journal/dataset/bar dirs): the
route wiring, non-GET 405, byte-identity to the module's own ``run_strategy_comparison_report``,
and one real recorded-dataset smoke test through the ACTUAL ``POST /research/datasets`` route --
the full request path, never a direct module call (``test_edge_report.py`` covers the pure
computation's exact cell values and gate logic in isolation).
"""

from __future__ import annotations

import json
import os
import threading
import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, manager
from app.research.bars import BarStore
from app.research.datasets import DatasetStore
from app.research.edge_report import EdgeReportComputeCancelled, REGISTER, run_strategy_comparison_report
from app.research.edge_report_cache import EdgeReportCache
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
    registry.edge_report_compute.join_all(timeout=10.0)
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
    """Single source of truth (TC-4): a WARM route response is a VERBATIM serving of
    ``run_strategy_comparison_report``'s own output — never a second computation. era-fast_wall
    J-01: a cold GET no longer computes at all (see the not-computed tests below), so this test
    now pre-warms the cache directly via ``EdgeReportCache.compute_and_publish`` — standing in for
    the future operator/CLI trigger (J-04) — at the SAME hermetic path the route's own dependency
    resolves to (see ``test_edge_report_route_cache_db_lives_hermetically_beside_the_test_dataset_
    dir`` below), before asserting byte-identity on a genuinely non-trivial (if still
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

    dataset_store = DatasetStore(tmp_path / "datasets")
    bar_store = BarStore(tmp_path / "bars")
    direct = run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG)
    EdgeReportCache(str(tmp_path / "edge_report_cache.db")).compute_and_publish(
        dataset_store, CONFIG, lambda: direct
    )

    route_payload = client.get("/research/edge-report").json()
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


def test_integrity_failure_after_a_warm_datasets_list_read_is_still_a_500(ctx):
    """TC-14 — era-fast_wall J-02: proves the new ``datasets.py`` metadata cache never masks an
    integrity error inside ``peek_strategy_comparison_report``'s ``_verified_records`` call, even
    when ``GET /research/datasets`` ALREADY warm-cached this exact dataset's metadata before it
    was tampered. The tamper changes the file's stat, so the cache's next lookup is an honest
    miss that forces a full re-verify — never a stale-good served value."""
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
    past = time.time() - 5.0
    os.utime(path, (past, past))  # past the ~2s racy-write guard, so the warm read below actually caches

    warm = client.get("/research/datasets")
    assert warm.status_code == 200
    assert warm.json()["integrity_errors"] == [], "sanity: genuinely warm-cached as healthy"

    data = json.loads(path.read_text())
    data["record"]["meta"]["checksum"] = "0" * 64  # tamper AFTER the warm read
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


def test_edge_report_route_serves_a_warm_result_on_repeated_calls_without_recomputing(ctx, monkeypatch):
    """The end-to-end proof J-08 exists for, updated for era-fast_wall J-01's new contract: a GET
    itself no longer WARMS the cache (see the not-computed tests below), so this pre-warms directly
    via ``EdgeReportCache.compute_and_publish`` — standing in for the future operator/CLI trigger
    (J-04) — at the SAME hermetic path the route's own dependency resolves to, then proves TWO real
    HTTP requests against the SAME running backend never re-enter the expensive computation —
    proven by counting calls to ``_compute_strategy_comparison_report`` (the ONE real computer),
    not merely inferring it from response shape."""
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

    dataset_store = DatasetStore(tmp_path / "datasets")
    bar_store = BarStore(tmp_path / "bars")
    EdgeReportCache(str(tmp_path / "edge_report_cache.db")).compute_and_publish(
        dataset_store, CONFIG,
        lambda: run_strategy_comparison_report(store, dataset_store, bar_store, CONFIG),
    )

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
    assert len(calls) == 0  # already warm BEFORE either request -- neither recomputes
    assert first.json() == second.json()
    assert "status" not in first.json()  # the genuine warm report shape, never not-computed


def test_edge_report_route_cold_response_is_byte_identical_across_repeated_calls(ctx):
    """era-fast_wall J-01 retires this test's ORIGINAL claim (a cold GET used to compute-and-cache,
    so cold and warm bytes matched by construction) — a cold GET now returns the intentionally
    DIFFERENT not-computed shape (TC-1/TC-4 above), so cold-vs-warm byte-identity is no longer the
    right property. What's still genuinely true and worth proving: the not-computed payload itself
    is STABLE — repeated cold GETs (nothing here ever warms the cache) return byte-identical
    responses, never a flapping ``dataset_count``/``detail``."""
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

    first = client.get("/research/edge-report")
    second = client.get("/research/edge-report")

    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["status"] == "not_computed"
    assert json.dumps(first.json(), sort_keys=True) == json.dumps(second.json(), sort_keys=True)


def test_edge_report_cold_cache_returns_the_not_computed_payload_and_never_computes(ctx, monkeypatch):
    """TC-1 + TC-2: a cold cache with a non-empty registry answers instantly with the honest
    not-computed shape, and a counting spy proves the expensive sweep is NEVER entered — the
    mechanical proof era-fast_wall J-01 exists to deliver."""
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
    dataset_count = client.get("/research/datasets").json()
    assert len(dataset_count["datasets"]) == 1

    from app.research import edge_report as edge_report_module

    calls = []
    real_compute = edge_report_module._compute_strategy_comparison_report

    def _counting_compute(*args, **kwargs):
        calls.append(1)
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(edge_report_module, "_compute_strategy_comparison_report", _counting_compute)

    response = client.get("/research/edge-report")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "not_computed"
    assert isinstance(payload["detail"], str) and payload["detail"] != ""
    assert payload["dataset_count"] == 1
    assert payload["register"] == REGISTER
    assert payload["compute"] is None
    assert calls == []  # the GET path never enters the sweep


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


# ==================================================================================================
# era-fast_wall J-04 — the operator-run compute: POST /research/edge-report/compute,
# GET /research/edge-report/compute, POST /research/edge-report/compute/cancel. The manager's OWN
# single-flight/cancel/progress/failed-state mechanics are unit-tested in isolation (a FAKE compute
# function, threading-free determinism) in test_edge_report_compute.py; this section proves the
# HTTP wiring — dependency injection, status codes, and the not-computed payload's ``compute``
# field mirroring GET .../compute byte-for-byte (TC-8).
# ==================================================================================================


def _record_reference_dataset(client):
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
    return recorded.json()["dataset"]


def _poll_compute_until_terminal(client, attempts=400):
    for _ in range(attempts):
        payload = client.get("/research/edge-report/compute").json()
        if payload is not None and payload["state"] != "running":
            return payload
        time.sleep(0.05)
    raise AssertionError("edge-report compute never reached a terminal state")


def test_get_compute_is_null_before_anything_has_ever_triggered(ctx):
    client, _store, _tmp_path = ctx
    assert client.get("/research/edge-report/compute").json() is None


def test_cancel_while_idle_is_409(ctx):
    """TC-4."""
    client, _store, _tmp_path = ctx
    response = client.post("/research/edge-report/compute/cancel")
    assert response.status_code == 409


def test_trigger_on_an_empty_registry_reaches_done_fast_and_get_compute_agrees(ctx):
    """TC-1 — the O(1) empty-registry leg (zero backtests, deterministic and fast)."""
    client, _store, _tmp_path = ctx
    response = client.post("/research/edge-report/compute", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["started"] is True
    assert body["compute"]["state"] == "running"
    assert body["compute"]["force"] is False

    terminal = _poll_compute_until_terminal(client)
    assert terminal["state"] == "done"
    assert terminal["error"] is None
    assert terminal["finished_utc"] is not None

    report = client.get("/research/edge-report").json()
    assert "status" not in report  # now a genuine warm report, never the not-computed shape
    assert report["train"]["cells"] == []


def test_trigger_missing_body_field_defaults_force_to_false(ctx):
    client, _store, _tmp_path = ctx
    response = client.post("/research/edge-report/compute", json={})
    assert response.status_code == 200
    assert response.json()["compute"]["force"] is False
    _poll_compute_until_terminal(client)


def test_second_trigger_while_running_returns_the_same_job(ctx, monkeypatch):
    """TC-2, at the route level."""
    client, _store, _tmp_path = ctx
    started = threading.Event()
    release = threading.Event()

    def fake_run(*args, **kwargs):
        started.set()
        release.wait(timeout=5)
        return {"train": {"cells": []}, "holdout": {"cells": []}, "surviving_train_cells": []}

    from app.research import edge_report_compute as edge_report_compute_module

    monkeypatch.setattr(edge_report_compute_module, "run_strategy_comparison_report", fake_run)

    first = client.post("/research/edge-report/compute", json={}).json()
    assert started.wait(timeout=5)

    second = client.post("/research/edge-report/compute", json={}).json()
    assert second["started"] is False
    assert second["compute"]["id"] == first["compute"]["id"]

    release.set()
    _poll_compute_until_terminal(client)


def test_cancel_mid_run_resolves_cancelled_and_the_cache_holds_no_partial_report(ctx, monkeypatch):
    """TC-3."""
    client, _store, tmp_path = ctx
    _record_reference_dataset(client)

    before = client.get("/research/edge-report").json()
    assert before["status"] == "not_computed"

    started = threading.Event()

    def fake_run(*args, **kwargs):
        should_abort = kwargs["should_abort"]
        started.set()
        deadline = time.time() + 5
        while time.time() < deadline:
            if should_abort():
                raise EdgeReportComputeCancelled()
            time.sleep(0.005)
        raise AssertionError("should_abort never fired")

    from app.research import edge_report_compute as edge_report_compute_module

    monkeypatch.setattr(edge_report_compute_module, "run_strategy_comparison_report", fake_run)

    client.post("/research/edge-report/compute", json={})
    assert started.wait(timeout=5)

    cancel_response = client.post("/research/edge-report/compute/cancel")
    assert cancel_response.status_code == 200

    terminal = _poll_compute_until_terminal(client)
    assert terminal["state"] == "cancelled"
    assert terminal["error"] is None

    after = client.get("/research/edge-report").json()
    assert after["status"] == "not_computed"
    assert after["dataset_count"] == before["dataset_count"]

    dataset_store = DatasetStore(tmp_path / "datasets")
    records, errors = dataset_store.list()
    assert errors == []
    cache = EdgeReportCache(str(tmp_path / "edge_report_cache.db"))
    assert cache.lookup(records, CONFIG) is None  # mechanical proof: no row was ever published


def test_a_failed_compute_surfaces_error_verbatim_and_publishes_no_partial_report(ctx, monkeypatch):
    """TC-13, at the route level."""
    client, _store, tmp_path = ctx
    _record_reference_dataset(client)

    def fake_run(*args, **kwargs):
        raise RuntimeError("synthetic mid-sweep failure")

    from app.research import edge_report_compute as edge_report_compute_module

    monkeypatch.setattr(edge_report_compute_module, "run_strategy_comparison_report", fake_run)

    client.post("/research/edge-report/compute", json={})
    terminal = _poll_compute_until_terminal(client)

    assert terminal["state"] == "failed"
    assert terminal["error"] == "synthetic mid-sweep failure"

    after = client.get("/research/edge-report").json()
    assert after["status"] == "not_computed"

    dataset_store = DatasetStore(tmp_path / "datasets")
    records, errors = dataset_store.list()
    assert errors == []
    cache = EdgeReportCache(str(tmp_path / "edge_report_cache.db"))
    assert cache.lookup(records, CONFIG) is None


def test_force_true_recomputes_over_a_warm_key(ctx, monkeypatch):
    """TC-5."""
    client, _store, _tmp_path = ctx
    _record_reference_dataset(client)

    client.post("/research/edge-report/compute", json={})
    _poll_compute_until_terminal(client)

    from app.research import edge_report as edge_report_module

    calls = []
    real_compute = edge_report_module._compute_strategy_comparison_report

    def _counting_compute(*args, **kwargs):
        calls.append(1)
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(edge_report_module, "_compute_strategy_comparison_report", _counting_compute)

    response = client.post("/research/edge-report/compute", json={"force": True})
    assert response.json()["compute"]["force"] is True
    terminal = _poll_compute_until_terminal(client)

    assert terminal["state"] == "done"
    assert len(calls) == 1  # a fresh call, even though the key was already warm


def test_non_force_trigger_over_the_same_warm_key_does_not_recompute(ctx, monkeypatch):
    """TC-6."""
    client, _store, _tmp_path = ctx
    _record_reference_dataset(client)

    client.post("/research/edge-report/compute", json={})
    _poll_compute_until_terminal(client)

    from app.research import edge_report as edge_report_module

    calls = []
    real_compute = edge_report_module._compute_strategy_comparison_report

    def _counting_compute(*args, **kwargs):
        calls.append(1)
        return real_compute(*args, **kwargs)

    monkeypatch.setattr(edge_report_module, "_compute_strategy_comparison_report", _counting_compute)

    response = client.post("/research/edge-report/compute", json={})
    assert response.json()["compute"]["force"] is False
    terminal = _poll_compute_until_terminal(client)

    assert terminal["state"] == "done"
    assert calls == []  # zero recompute — served entirely from the warm cache


def test_compute_field_on_the_edge_report_payload_mirrors_get_compute_byte_for_byte(ctx, monkeypatch):
    """TC-8."""
    client, _store, _tmp_path = ctx
    _record_reference_dataset(client)

    cold = client.get("/research/edge-report").json()
    assert cold["status"] == "not_computed"
    assert cold["compute"] is None  # unchanged J-01 behavior — nothing has ever triggered

    started = threading.Event()
    release = threading.Event()

    def fake_run(*args, **kwargs):
        started.set()
        release.wait(timeout=5)
        return {"train": {"cells": []}, "holdout": {"cells": []}, "surviving_train_cells": []}

    from app.research import edge_report_compute as edge_report_compute_module

    monkeypatch.setattr(edge_report_compute_module, "run_strategy_comparison_report", fake_run)

    client.post("/research/edge-report/compute", json={})
    assert started.wait(timeout=5)

    while_running = client.get("/research/edge-report").json()
    compute_endpoint_while_running = client.get("/research/edge-report/compute").json()
    assert while_running["status"] == "not_computed"  # the fake never touches the real cache
    assert while_running["compute"] == compute_endpoint_while_running
    assert while_running["compute"]["state"] == "running"

    release.set()
    _poll_compute_until_terminal(client)


def test_trigger_route_wired_through_the_registry_edge_report_compute_property():
    """A coherence guard (never a second manager construction): the trigger route reads the SAME
    ``registry.edge_report_compute`` property ``GET``/``cancel`` read."""
    import inspect

    from app.research import routes

    for fn in (routes.trigger_edge_report_compute, routes.get_edge_report_compute, routes.cancel_edge_report_compute):
        src = inspect.getsource(fn)
        assert "registry.edge_report_compute" in src


def test_edge_report_route_still_passes_the_pinned_depends_and_cache_kwarg_after_this_iteration():
    """Re-runs the TWO pre-existing pinned guard tests' own assertions inline (never edited) to
    confirm this iteration's ADDITIVE ``compute=`` kwarg on the SAME call did not disturb them."""
    import inspect

    from app.research import routes

    src = inspect.getsource(routes.get_edge_report)
    assert "Depends(get_bar_store)" in src
    assert "Depends(get_dataset_store)" in src
    assert "Depends(get_edge_report_cache)" in src
    assert "cache=cache" in src
