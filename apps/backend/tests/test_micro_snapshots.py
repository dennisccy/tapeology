"""``micro_snapshots.py`` + the three ``GET``/``POST`` snapshot routes (Era "The Rapid Microscope"
J-02) -- identity/persistence/load-time re-verification (TC-3/TR-7), the single-flight compute
manager (TC-13), and the real 18-dataset legacy-corpus build (TC-12). Test-first contract: TC-3,
TC-12, TC-13 in ``docs/phases/goal-rapid-microscope-iter-2.md``.

The real-corpus tests (TC-12) run against the ACTUAL committed 18-dataset legacy tick corpus at
``apps/backend/.data/datasets`` -- the ``test_micro_readiness.py`` precedent: a fixture cannot
substitute for the real-corpus build acceptance. A snapshot is DERIVED and REUSABLE (module
docstring), so this module-scoped fixture pays the real build cost only the FIRST time it ever
runs against a given machine's ``.data`` tree; every subsequent run (including a re-run of just
this file) reuses the already-valid snapshots near-instantly (``load_snapshot_meta``'s own
identity re-verification)."""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.research import micro_snapshots as ms
from app.research.datasets import DatasetStore
from app.research.micro_routes import (
    get_micro_snapshot_compute_manager,
    get_micro_snapshots_dir,
)
from app.research.routes import get_dataset_store
from tests.test_micro_observer import _events_for_store

TICKER = "TEST"


def _plant(store: DatasetStore, symbol: str = TICKER) -> dict:
    return store.record(
        symbol=symbol, source="fixture", source_kind="fixture", source_id="fixture",
        split="train", window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
        data_feed="sip", epoch_anchor=0.0, events=_events_for_store(),
    )


# --- identity + quote_size_unit ---------------------------------------------------------------------


def test_feature_source_hash_is_stable_across_calls():
    assert ms.feature_source_hash() == ms.feature_source_hash()


def test_feature_source_hash_covers_the_observer_module_not_only_the_feature_module(monkeypatch):
    """Audit regression (spec section 2.3, fail-closed direction): the values that land in a
    persisted row are produced by ``micro_observer.py``'s streaming state machine, so an
    observer-only edit MUST re-key the snapshot identity. Hashing ``micro_features.py`` alone left
    every stored identity verifying against code that no longer produces those rows."""
    import hashlib
    from pathlib import Path

    from app.research import micro_features as mf_mod
    from app.research import micro_observer as mo_mod

    assert ms._IDENTITY_SOURCE_MODULES == (mf_mod, mo_mod)
    both = ms.feature_source_hash()
    monkeypatch.setattr(ms, "_IDENTITY_SOURCE_MODULES", (mf_mod,))
    features_only = ms.feature_source_hash()
    assert features_only == hashlib.sha256(Path(mf_mod.__file__).read_bytes()).hexdigest()
    assert both != features_only  # the observer's own bytes genuinely participate


def test_quote_size_unit_for_dataset_defaults_to_unverified():
    assert ms.quote_size_unit_for_dataset({"id": "x"}) == "unverified"


def test_quote_size_unit_for_dataset_reads_a_future_stamped_value_verbatim():
    assert ms.quote_size_unit_for_dataset({"id": "x", "quote_size_unit": "shares"}) == "shares"


def test_snapshot_identity_carries_every_component(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    identity = ms.snapshot_identity(meta, CONFIG)
    assert identity["dataset_id"] == meta["id"]
    assert identity["dataset_checksum"] == meta["checksum"]
    assert identity["micro_algo_version"] == 1
    assert identity["snapshot_format_version"] == ms.SNAPSHOT_FORMAT_VERSION
    assert identity["config_fingerprint"] == CONFIG.config_fingerprint()


# --- write_snapshot / load_snapshot_meta round trip --------------------------------------------------


def test_write_then_load_round_trips(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    rows = ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
    identity = ms.snapshot_identity(meta, CONFIG)
    written = ms.write_snapshot(str(tmp_path / "snapshots"), meta["id"], rows, {**identity, "quote_size_unit": "unverified"})
    assert written["row_count"] == len(rows)
    assert written["bytes_on_disk"] > 0

    loaded = ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], CONFIG)
    assert loaded == written


def test_load_snapshot_meta_is_none_when_nothing_was_ever_built(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    assert ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], CONFIG) is None


def test_load_snapshot_meta_raises_on_a_corrupted_meta_file(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    snapshots_dir = tmp_path / "snapshots"
    snapshots_dir.mkdir()
    (snapshots_dir / f"{meta['id']}.meta.json").write_text("not json")
    with pytest.raises(ms.MicroSnapshotIntegrityError):
        ms.load_snapshot_meta(str(snapshots_dir), store, meta["id"], CONFIG)


# --- a mid-stream observer failure is refused, never persisted as a short snapshot -----------------


def test_a_mid_stream_observer_failure_refuses_the_build_instead_of_truncating_silently(
    tmp_path, monkeypatch
):
    """Audit regression: ``TapeEngine._notify_event`` isolates observer exceptions BY DESIGN (the
    engine must never be perturbed by a research observer), so a raising observer simply stops
    producing rows -- invisibly. This test proves both halves: the engine really does sail on
    (every event still yields its snapshot, and the observer's row set is silently short), and
    ``build_snapshot_rows`` now REFUSES rather than persisting that short row set as a complete,
    identity-verified snapshot."""
    from app.research.micro_observer import MicroObserver

    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    real_consume = MicroObserver._consume

    def _boom_on_the_last_event(self, event, snapshot):
        if event.timestamp >= 0.2:
            raise RuntimeError("simulated observer bug")
        real_consume(self, event, snapshot)

    monkeypatch.setattr(MicroObserver, "_consume", _boom_on_the_last_event)

    # (a) the engine is unaffected -- all 3 events still replay, and the observer is silently short
    observer = MicroObserver(quote_size_unit="unverified")
    snapshots = list(store.replay(meta["id"], CONFIG, observer=observer))
    assert len(snapshots) == 3
    assert observer.failure is not None
    assert len(observer.rows) == 1  # the second trade's row never happened -- silently

    # (b) the builder refuses, and nothing is written
    root = str(tmp_path / "snapshots")
    with pytest.raises(ms.MicroObserverFailure):
        ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
    with pytest.raises(ms.MicroObserverFailure):
        ms.run_snapshot_build_and_record(store, CONFIG, root, [meta["id"]])
    assert ms.load_snapshot_meta(root, store, meta["id"], CONFIG) is None


def test_a_failed_build_surfaces_as_a_failed_run_never_a_silent_success(tmp_path, monkeypatch):
    """The manager's own half of the same rail: the refusal reaches ``state: "failed"`` with the
    error verbatim, and the durable run log records it -- never a "done" over a partial corpus."""
    from app.research.micro_observer import MicroObserver

    store = DatasetStore(tmp_path / "datasets")
    _plant(store)
    monkeypatch.setattr(
        MicroObserver,
        "_consume",
        lambda self, event, snapshot: (_ for _ in ()).throw(RuntimeError("simulated observer bug")),
    )
    root = str(tmp_path / "snapshots")
    manager = ms.MicroSnapshotComputeManager()
    manager.trigger(store, CONFIG, root)
    manager.join_all(timeout=10.0)
    time.sleep(0.05)
    snap = manager.snapshot()
    assert snap["state"] == "failed"
    assert "simulated observer bug" in (snap["error"] or "")
    assert ms.read_run_log(root)[0]["state"] == "failed"


# --- TC-3 / TR-7: cache MISS on a config_fingerprint change or a mutated feature-module byte --------


def test_tc3_cache_miss_on_config_fingerprint_change(tmp_path, monkeypatch):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    rows = ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
    identity = ms.snapshot_identity(meta, CONFIG)
    ms.write_snapshot(str(tmp_path / "snapshots"), meta["id"], rows, {**identity, "quote_size_unit": "unverified"})

    assert ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], CONFIG) is not None

    class _FakeConfig:
        def config_fingerprint(self) -> str:
            return "deadbeefdeadbeef"

    assert ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], _FakeConfig()) is None


def test_tc3_cache_miss_on_a_mutated_feature_module_byte(tmp_path, monkeypatch):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    rows = ms.build_snapshot_rows(store, meta["id"], CONFIG, quote_size_unit="unverified")
    identity = ms.snapshot_identity(meta, CONFIG)
    ms.write_snapshot(str(tmp_path / "snapshots"), meta["id"], rows, {**identity, "quote_size_unit": "unverified"})

    assert ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], CONFIG) is not None

    monkeypatch.setattr(ms, "feature_source_hash", lambda: "simulated-different-source-hash")
    assert ms.load_snapshot_meta(str(tmp_path / "snapshots"), store, meta["id"], CONFIG) is None


def test_tc3_rebuild_after_a_miss_serves_fresh_not_stale(tmp_path, monkeypatch):
    import dataclasses

    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    root = str(tmp_path / "snapshots")
    first = ms.run_snapshot_build_and_record(store, CONFIG, root, [meta["id"]])
    assert first[0]["config_fingerprint"] == CONFIG.config_fingerprint()

    changed_config = dataclasses.replace(CONFIG, large_print_size=CONFIG.large_print_size + 1)
    assert changed_config.config_fingerprint() != CONFIG.config_fingerprint()
    second = ms.run_snapshot_build_and_record(store, changed_config, root, [meta["id"]])
    assert second[0]["config_fingerprint"] == changed_config.config_fingerprint()  # rebuilt, not stale


# --- run_snapshot_build_and_record: reuse-or-build -----------------------------------------------------


def test_run_snapshot_build_and_record_reuses_an_already_valid_snapshot(tmp_path, monkeypatch):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    root = str(tmp_path / "snapshots")
    ms.run_snapshot_build_and_record(store, CONFIG, root, [meta["id"]])

    calls = {"n": 0}
    original = ms.build_snapshot_rows

    def _spy(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(ms, "build_snapshot_rows", _spy)
    ms.run_snapshot_build_and_record(store, CONFIG, root, [meta["id"]])
    assert calls["n"] == 0  # reused -- no second replay


def test_run_snapshot_build_and_record_defaults_to_every_dataset_in_the_store(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    a = _plant(store, symbol="AAA")
    b = _plant(store, symbol="BBB")
    results = ms.run_snapshot_build_and_record(store, CONFIG, str(tmp_path / "snapshots"))
    assert {r["dataset_id"] for r in results} == {a["id"], b["id"]}


# --- the durable run log -------------------------------------------------------------------------------


def test_run_log_append_and_read_newest_first(tmp_path):
    root = str(tmp_path / "snapshots")
    ms.append_run_log(root, {"run_id": "a", "state": "done"})
    ms.append_run_log(root, {"run_id": "b", "state": "failed"})
    runs = ms.read_run_log(root)
    assert [r["run_id"] for r in runs] == ["b", "a"]


def test_run_log_read_is_an_honest_empty_list_when_nothing_was_ever_recorded(tmp_path):
    assert ms.read_run_log(str(tmp_path / "nonexistent")) == []


# --- TC-13: the single-flight compute manager --------------------------------------------------------


def test_tc13_manager_reports_idle_before_any_job(tmp_path):
    manager = ms.MicroSnapshotComputeManager()
    snap = manager.snapshot()
    assert snap["state"] == "idle"
    assert snap["progress"]["datasets_total"] == 0


def test_tc13_manager_refuses_a_second_concurrent_trigger(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    a = _plant(store, symbol="AAA")
    manager = ms.MicroSnapshotComputeManager()
    first = manager.trigger(store, CONFIG, str(tmp_path / "snapshots"), [a["id"]])
    assert first["state"] == "running"
    second = manager.trigger(store, CONFIG, str(tmp_path / "snapshots"), [a["id"]])
    assert second == {"state": "refused", "reason": "already_running"}
    manager.join_all(timeout=5.0)


def test_tc13_progress_increases_monotonically_to_done(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    for i in range(3):
        _plant(store, symbol=f"SYM{i}")
    manager = ms.MicroSnapshotComputeManager()
    manager.trigger(store, CONFIG, str(tmp_path / "snapshots"))
    manager.join_all(timeout=10.0)
    seen_done_counts: list[int] = []
    deadline = time.time() + 5.0
    while time.time() < deadline:
        snap = manager.snapshot()
        seen_done_counts.append(snap["progress"]["datasets_done"])
        if snap["state"] == "done":
            break
        time.sleep(0.01)
    assert seen_done_counts == sorted(seen_done_counts)  # monotonically non-decreasing
    final = manager.snapshot()
    assert final["state"] == "done"
    assert final["progress"]["datasets_done"] == 3
    assert final["progress"]["datasets_total"] == 3


def test_tc13_cancel_on_an_idle_manager_is_a_harmless_no_op(tmp_path):
    manager = ms.MicroSnapshotComputeManager()
    result = manager.cancel()
    assert result["accepted"] is False


def test_tc13_run_log_gains_one_terminal_entry_per_job(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    _plant(store, symbol="AAA")
    root = str(tmp_path / "snapshots")
    manager = ms.MicroSnapshotComputeManager()
    manager.trigger(store, CONFIG, root)
    manager.join_all(timeout=10.0)
    time.sleep(0.05)
    runs = ms.read_run_log(root)
    assert len(runs) == 1
    assert runs[0]["state"] == "done"
    assert runs[0]["datasets_done"] == 1


# --- routes (TestClient) ------------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    snapshots_dir = str(tmp_path / "snapshots")
    manager = ms.MicroSnapshotComputeManager()
    app.dependency_overrides[get_dataset_store] = lambda: dataset_store
    app.dependency_overrides[get_micro_snapshots_dir] = lambda: snapshots_dir
    app.dependency_overrides[get_micro_snapshot_compute_manager] = lambda: manager
    with TestClient(app) as c:
        yield c, dataset_store, snapshots_dir, manager
    app.dependency_overrides.pop(get_dataset_store, None)
    app.dependency_overrides.pop(get_micro_snapshots_dir, None)
    app.dependency_overrides.pop(get_micro_snapshot_compute_manager, None)


def test_get_snapshots_is_an_honest_empty_list_on_a_fresh_store(client):
    c, _store, _dir, _manager = client
    resp = c.get("/research/desk/micro/snapshots")
    assert resp.status_code == 200
    assert resp.json() == {"snapshots": []}


def test_snapshots_route_lists_a_built_snapshot(client):
    c, store, snapshots_dir, _manager = client
    meta = _plant(store)
    ms.run_snapshot_build_and_record(store, CONFIG, snapshots_dir, [meta["id"]])
    resp = c.get("/research/desk/micro/snapshots")
    body = resp.json()
    assert len(body["snapshots"]) == 1
    assert body["snapshots"][0]["dataset_id"] == meta["id"]
    assert body["snapshots"][0]["quote_size_unit"] == "unverified"
    assert "row_count" in body["snapshots"][0] and "bytes_on_disk" in body["snapshots"][0]
    # never raw per-event rows (the boundary note) -- only metadata keys are served
    assert "deferred" not in body["snapshots"][0] and "cumulative_delta" not in body["snapshots"][0]


def test_compute_route_triggers_a_build_and_reports_progress_to_done(client):
    c, store, _dir, _manager = client
    _plant(store)
    post_resp = c.post("/research/desk/micro/snapshots/compute")
    assert post_resp.status_code == 200
    assert post_resp.json()["state"] == "running"
    assert "run_id" in post_resp.json()

    deadline = time.time() + 5.0
    state = None
    while time.time() < deadline:
        get_resp = c.get("/research/desk/micro/snapshots/compute")
        state = get_resp.json()["state"]
        if state == "done":
            break
        time.sleep(0.01)
    assert state == "done"


@contextmanager
def _pinned_build(monkeypatch):
    """Hold the compute manager's worker INSIDE its build until this block exits, yielding an
    ``Event`` the caller waits on to know the worker is genuinely in flight.

    Both route-level concurrency tests below assert on a job that must still be RUNNING when a
    second HTTP request lands. Left to real timing that is a coin flip: they build a 3-event
    synthetic dataset in well under a millisecond, while a ``TestClient`` round trip through the
    ASGI stack costs several -- so the job is usually already terminal by the time the request
    arrives, and the assertion fails. Measured before this barrier existed: 14/20 and 11/20
    isolated-run failures respectively (identically 15/20 against the pre-fix observer, so the
    race predates this iteration's unit-gate fix and is not caused by it). Pinning the worker
    makes the concurrency REAL rather than hoped-for -- the refusal and the cancel acknowledgement
    become genuine single-flight outcomes instead of a race the test happened to win. Nothing about
    the asserted CONTRACT is relaxed; only the timing is made deterministic."""
    entered = threading.Event()
    release = threading.Event()
    real_build = ms.run_snapshot_build_and_record

    def _blocking_build(*args, **kwargs):
        entered.set()
        release.wait(timeout=10.0)
        return real_build(*args, **kwargs)

    monkeypatch.setattr(ms, "run_snapshot_build_and_record", _blocking_build)
    try:
        yield entered
    finally:
        release.set()


def test_compute_route_refuses_a_second_concurrent_trigger(client, monkeypatch):
    c, store, snapshots_dir, manager = client
    a = _plant(store, symbol="AAA")
    with _pinned_build(monkeypatch) as entered:
        manager.trigger(store, CONFIG, snapshots_dir, [a["id"]])
        assert entered.wait(timeout=10.0), "the first job never entered its build"
        resp = c.post("/research/desk/micro/snapshots/compute")
        assert resp.json() == {"state": "refused", "reason": "already_running"}
    manager.join_all(timeout=10.0)


def test_cancel_route_409s_when_nothing_is_running(client):
    c, _store, _dir, _manager = client
    resp = c.post("/research/desk/micro/snapshots/compute/cancel")
    assert resp.status_code == 409


def test_cancel_route_acknowledges_a_running_job(client, monkeypatch):
    c, store, snapshots_dir, manager = client
    _plant(store)
    with _pinned_build(monkeypatch) as entered:
        manager.trigger(store, CONFIG, snapshots_dir)
        assert entered.wait(timeout=10.0), "the job never entered its build"
        resp = c.post("/research/desk/micro/snapshots/compute/cancel")
        assert resp.status_code == 200
        assert resp.json() == {"state": "cancelled"}
    manager.join_all(timeout=10.0)


def test_runs_route_is_an_honest_empty_list_before_any_job(client):
    c, _store, _dir, _manager = client
    resp = c.get("/research/desk/micro/snapshots/runs")
    assert resp.status_code == 200
    assert resp.json() == {"runs": []}


def test_runs_route_lists_a_completed_job(client):
    c, store, _dir, manager = client
    _plant(store)
    post_resp = c.post("/research/desk/micro/snapshots/compute")
    run_id = post_resp.json()["run_id"]
    manager.join_all(timeout=10.0)
    time.sleep(0.05)
    resp = c.get("/research/desk/micro/snapshots/runs")
    runs = resp.json()["runs"]
    assert len(runs) == 1
    assert runs[0]["run_id"] == run_id
    assert runs[0]["state"] == "done"


# --- TC-12: the REAL 18-dataset legacy corpus (module-scoped -- pays the build cost once) -----------


@pytest.fixture(scope="module")
def real_snapshots():
    dataset_dir = CONFIG.dataset_dir  # the un-overridden package default -- the committed real corpus
    store = DatasetStore(dataset_dir)
    snapshots_dir = ms.resolve_micro_snapshots_dir(dataset_dir)
    results = ms.run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)
    return store, snapshots_dir, results


def test_tc12_real_corpus_builds_all_eighteen_legacy_datasets(real_snapshots):
    _store, _dir, results = real_snapshots
    assert len(results) == 18


def test_tc12_real_corpus_every_snapshot_carries_unverified_quote_size_unit(real_snapshots):
    _store, _dir, results = real_snapshots
    assert all(r["quote_size_unit"] == "unverified" for r in results)


def test_tc12_real_corpus_identity_re_verifies_on_a_second_read(real_snapshots):
    store, snapshots_dir, results = real_snapshots
    for r in results:
        reloaded = ms.load_snapshot_meta(snapshots_dir, store, r["dataset_id"], CONFIG)
        assert reloaded == r


def test_tc12_real_corpus_listed_via_the_route(real_snapshots):
    store, snapshots_dir, _results = real_snapshots
    app.dependency_overrides[get_dataset_store] = lambda: store
    app.dependency_overrides[get_micro_snapshots_dir] = lambda: snapshots_dir
    try:
        with TestClient(app) as c:
            resp = c.get("/research/desk/micro/snapshots")
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["snapshots"]) == 18
    finally:
        app.dependency_overrides.pop(get_dataset_store, None)
        app.dependency_overrides.pop(get_micro_snapshots_dir, None)
