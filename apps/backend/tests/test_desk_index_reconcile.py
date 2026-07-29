"""``desk_index_reconcile.py`` (Era B "The Desk", J-10, goal-desk-iter-14) — the coverage-index
reconciliation: drift classification between the frozen JSON ``BarStore`` and the derived
``bar_index`` SQLite index, repair through the EXISTING ``BarIndex.reindex()`` (never a second
index-building path), the durable append-only run-record store, and the single-flight/pollable/
cancellable compute manager plus its four HTTP routes.

Sections mirror three existing precedents:
  * ``classify_drift``/``run_reconcile`` — pure composition over ``BarStore``/``BarIndex``'s own
    public reads, mirrors ``test_bar_index.py``'s directness (no FastAPI/TestClient).
  * ``ReconcileRunStore`` — the durable run-record store's checksum/append-only/corrupted-file
    discipline, mirrors ``test_desk_topup_log.py`` line for line.
  * ``DeskIndexReconcileComputeManager`` + routes — manager mechanics (single-flight, cancel,
    atomic progress) and HTTP wiring, mirrors ``test_desk_topup_compute.py``.

Zero diff to ``bar_index.py``/``bars.py``/``tradability.py``/``levels.py``/``desk_coverage.py`` —
every fixture below drives ONLY their existing public reads (``BarStore.list``/``record``,
``BarIndex.list``/``insert``/``reindex``/``coverage``, ``compute_screen``/``get_desk_coverage``).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.providers.adapters.base import RawBar
from app.research import desk_index_reconcile
from app.research.bar_index import BarIndex
from app.research.bars import BarStore
from app.research.datasets import DatasetStore
from app.research.desk_coverage import get_desk_coverage
from app.research.desk_index_reconcile import (
    DeskIndexReconcileComputeManager,
    ReconcileRunStore,
    classify_drift,
    record_reconcile_run,
    resolve_desk_index_reconcile_dir,
    run_reconcile,
)
from app.research.desk_routes import get_desk_reconcile_manager, get_reconcile_run_store
from app.research.desk_screen import ScreenStore, compute_screen
from app.research.desk_universe import UniverseStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore

FIXTURE_UNIVERSE_DIR = Path(__file__).parent / "fixtures" / "universe"
REGISTERED_SNAPSHOT_PATH = FIXTURE_UNIVERSE_DIR / "universe-2026-07-25-817cc184bbb3.json"

EMPTY_DRIFT = {"unindexed_series": [], "orphan_index_rows": [], "stale_checksum_rows": []}


def _bar(symbol, timeframe, epoch, o, h, l, c, v):
    return RawBar(symbol, timeframe, epoch, o, h, l, c, v)


def _small_series(symbol: str = "PG") -> list[RawBar]:
    base = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()
    day = 86400.0
    return [
        _bar(symbol, "1d", base + 0 * day, 148.0, 149.5, 147.5, 149.0, 1_000_000),
        _bar(symbol, "1d", base + 1 * day, 149.0, 150.0, 148.5, 149.8, 1_100_000),
    ]


def _record(
    store: BarStore,
    symbol: str = "PG",
    timeframe: str = "1d",
    start: str = "2026-06-01T00:00:00Z",
    end: str = "2026-06-04T00:00:00Z",
    feed: str = "yahoo",
) -> dict:
    return store.record(
        symbol=symbol, timeframe=timeframe, window_start_utc=start, window_end_utc=end,
        feed=feed, bars=_small_series(symbol),
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _wait_for_terminal(mgr: DeskIndexReconcileComputeManager, timeout: float = 5.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        snap = mgr.snapshot()
        if snap is not None and snap["state"] != "running":
            return snap
        time.sleep(0.01)
    raise AssertionError("desk index reconcile compute job never reached a terminal state")


# ==================================================================================================
# classify_drift -- TC-1/2/3, pure composition, no FastAPI needed.
# ==================================================================================================


def test_classify_drift_on_an_empty_store_and_index_is_all_empty(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    drift, errors = classify_drift(store, index)
    assert drift == EMPTY_DRIFT
    assert errors == []


def test_classify_drift_reports_nothing_when_store_and_index_already_agree(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    index.insert(_record(store))
    drift, errors = classify_drift(store, index)
    assert drift == EMPTY_DRIFT
    assert errors == []


def test_tc1_a_healthy_series_with_no_index_row_is_reported_as_unindexed_by_symbol_and_timeframe(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    meta = _record(store, symbol="PG", timeframe="1d")
    # deliberately never index.insert(meta) -- the TC-1 drift case

    drift, errors = classify_drift(store, index)
    assert drift["unindexed_series"] == [{"series_id": meta["id"], "symbol": "PG", "timeframe": "1d"}]
    assert drift["orphan_index_rows"] == []
    assert drift["stale_checksum_rows"] == []
    assert errors == []


def test_tc2_an_index_row_whose_series_id_matches_no_file_is_reported_as_orphan_by_series_id_alone(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    index.insert(
        {
            "symbol": "GHOST", "timeframe": "1d", "window_start_utc": "2026-06-01T00:00:00Z",
            "window_end_utc": "2026-06-04T00:00:00Z", "feed": "yahoo", "id": "ghost-series-id",
            "checksum": "deadbeef", "bar_count": 1,
        }
    )

    drift, errors = classify_drift(store, index)
    assert drift["orphan_index_rows"] == [{"series_id": "ghost-series-id"}]
    assert drift["unindexed_series"] == []
    assert drift["stale_checksum_rows"] == []
    assert errors == []


def test_tc3_an_index_row_pointing_at_a_corrupted_file_is_reported_as_stale_checksum_by_series_id_alone(
    tmp_path,
):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    meta = _record(store, symbol="F", timeframe="1h", start="2026-06-05T00:00:00Z", end="2026-06-06T00:00:00Z")
    index.insert(meta)
    corrupt_path = tmp_path / "bars" / f"{meta['id']}.json"
    data = json.loads(corrupt_path.read_text())
    data["record"]["bars"][0]["close"] += 1.0
    corrupt_path.write_text(json.dumps(data))

    drift, errors = classify_drift(store, index)
    assert len(errors) == 1 and errors[0]["file"] == f"{meta['id']}.json"
    assert drift["stale_checksum_rows"] == [{"series_id": meta["id"]}]
    assert drift["unindexed_series"] == []
    assert drift["orphan_index_rows"] == []


def test_the_three_buckets_are_mutually_exclusive_and_together_cover_every_drifted_id(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    unindexed = _record(store, symbol="PG", timeframe="1d")
    corrupt = _record(store, symbol="F", timeframe="1h", start="2026-06-05T00:00:00Z", end="2026-06-06T00:00:00Z")
    index.insert(corrupt)
    corrupt_path = tmp_path / "bars" / f"{corrupt['id']}.json"
    data = json.loads(corrupt_path.read_text())
    data["record"]["bars"][0]["close"] += 1.0
    corrupt_path.write_text(json.dumps(data))
    index.insert(
        {
            "symbol": "GHOST", "timeframe": "1d", "window_start_utc": "2026-01-01T00:00:00Z",
            "window_end_utc": "2026-01-02T00:00:00Z", "feed": "yahoo", "id": "ghost-id",
            "checksum": "deadbeef", "bar_count": 1,
        }
    )

    drift, _errors = classify_drift(store, index)
    assert [e["series_id"] for e in drift["unindexed_series"]] == [unindexed["id"]]
    assert [e["series_id"] for e in drift["orphan_index_rows"]] == ["ghost-id"]
    assert [e["series_id"] for e in drift["stale_checksum_rows"]] == [corrupt["id"]]
    all_ids = (
        [e["series_id"] for e in drift["unindexed_series"]]
        + [e["series_id"] for e in drift["orphan_index_rows"]]
        + [e["series_id"] for e in drift["stale_checksum_rows"]]
    )
    assert len(all_ids) == len(set(all_ids))  # no id appears in two buckets


# ==================================================================================================
# run_reconcile -- TC-4/5, the sole repair walker (classify -> reindex() -> classify).
# ==================================================================================================


def test_tc4_a_reconciliation_run_repairs_the_index_and_get_desk_coverage_flips_false_to_true(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    universe_store = UniverseStore(tmp_path / "universe")
    universe_store.record(
        members=["PG"], raw_members={"PG": "PG"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    meta = _record(store, symbol="PG", timeframe="1d")  # unindexed -- TC-1's drift case

    before = get_desk_coverage(universe_store, index)
    assert before["members"][0]["per_timeframe"]["1d"]["has_bars"] is False

    result = run_reconcile(store, index)

    assert result["series_on_disk"] == 1
    assert result["rows_indexed_before"] == 0
    assert result["rows_indexed_after"] == 1
    assert result["drift_before"] == {
        "unindexed_series": [{"series_id": meta["id"], "symbol": "PG", "timeframe": "1d"}],
        "orphan_index_rows": [], "stale_checksum_rows": [],
    }
    assert result["drift_after"] == EMPTY_DRIFT
    assert result["store_errors"] == []
    assert result["aborted"] is False

    after = get_desk_coverage(universe_store, index)
    assert after["members"][0]["per_timeframe"]["1d"]["has_bars"] is True


def test_tc5_a_corrupt_file_stays_unindexed_after_repair_and_store_errors_are_verbatim(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    _good = _record(store, symbol="PG", timeframe="1d")
    corrupt = _record(store, symbol="F", timeframe="1h", start="2026-06-05T00:00:00Z", end="2026-06-06T00:00:00Z")
    index.insert(corrupt)  # indexed before corruption -- a genuine stale row once the file rots
    corrupt_path = tmp_path / "bars" / f"{corrupt['id']}.json"
    data = json.loads(corrupt_path.read_text())
    data["record"]["bars"][0]["close"] += 1.0
    corrupt_path.write_text(json.dumps(data))
    _healthy, expected_errors = store.list(include_bars=False)

    result = run_reconcile(store, index)

    assert result["store_errors"] == expected_errors
    assert index.lookup("F", "1h", "2026-06-05T00:00:00Z", "2026-06-06T00:00:00Z", "yahoo") is None
    assert index.lookup("PG", "1d", "2026-06-01T00:00:00Z", "2026-06-04T00:00:00Z", "yahoo") is not None
    assert index.list(symbol="F") == []


def test_run_reconcile_on_a_clean_store_is_a_true_no_op(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    index.insert(_record(store))

    result = run_reconcile(store, index)

    assert result["drift_before"] == EMPTY_DRIFT
    assert result["drift_after"] == EMPTY_DRIFT
    assert result["rows_indexed_before"] == result["rows_indexed_after"] == 1


def test_run_reconcile_progress_callback_receives_the_three_phases_in_order(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    _record(store)
    phases: list[str] = []

    run_reconcile(store, index, progress=phases.append)

    assert phases == ["classifying", "reindexing", "verifying"]


def test_run_reconcile_should_abort_before_reindex_skips_the_repair_entirely(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    _record(store)  # a real drift case exists -- a completed repair would be observable

    result = run_reconcile(store, index, should_abort=lambda: True)

    assert result["aborted"] is True
    assert result["rows_indexed_after"] == result["rows_indexed_before"] == 0
    assert result["drift_after"] == result["drift_before"]
    assert index.list() == []  # reindex() never ran


def test_tc12_a_post_repair_screen_gets_a_new_bar_store_signature_and_the_pre_repair_snapshot_is_untouched(
    tmp_path,
):
    universe_dir = tmp_path / "universe"
    universe_dir.mkdir(parents=True)
    shutil.copy(REGISTERED_SNAPSHOT_PATH, universe_dir / REGISTERED_SNAPSHOT_PATH.name)
    universe_store = UniverseStore(universe_dir)
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    dataset_store = DatasetStore(tmp_path / "datasets")
    screen_store = ScreenStore(tmp_path / "screens")

    _record(bar_store, symbol="AAPL", timeframe="1d")  # unindexed -- AAPL is a real fixture member

    pre_repair = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, "2026-06-22")
    pre_record = screen_store.record(**pre_repair)
    pre_path = screen_store.root / f"{pre_record['id']}.json"
    pre_bytes = pre_path.read_bytes()

    run_reconcile(bar_store, bar_index)

    post_repair = compute_screen(universe_store, bar_store, bar_index, dataset_store, CONFIG, "2026-06-22")
    assert post_repair["bar_store_signature"] != pre_repair["bar_store_signature"]
    post_record = screen_store.record(**post_repair)
    assert post_record["id"] != pre_record["id"]
    assert pre_path.read_bytes() == pre_bytes  # the pre-repair snapshot file is byte-unchanged


def test_tc8_reconciliation_never_writes_to_any_bar_series_file_or_universe_snapshot_file(tmp_path):
    """Byte-identity proof at the unit level: ``run_reconcile`` touches only the derived
    ``bar_index`` DB -- it takes no ``UniverseStore``/``ScreenStore``/``TopupRunStore`` parameter at
    all, so it cannot write to those directories even in principle. This test proves the ONE store
    it CAN touch (``BarStore``'s own series files) is also left byte-identical."""
    bars_root = tmp_path / "bars"
    store = BarStore(bars_root)
    index = BarIndex(str(tmp_path / "index.db"))
    meta = _record(store, symbol="PG", timeframe="1d")

    universe_dir = tmp_path / "universe"
    universe_dir.mkdir()
    (universe_dir / "dummy.json").write_text('{"marker": true}')

    before = {p: _sha256_file(p) for p in bars_root.glob("*.json")}
    universe_before = _sha256_file(universe_dir / "dummy.json")

    run_reconcile(store, index)

    after = {p: _sha256_file(p) for p in bars_root.glob("*.json")}
    assert after == before
    assert set(before) == {bars_root / f"{meta['id']}.json"}
    assert _sha256_file(universe_dir / "dummy.json") == universe_before


# ==================================================================================================
# ReconcileRunStore -- the durable run-record store's discipline, mirrors test_desk_topup_log.py.
# ==================================================================================================

SAMPLE_DRIFT_BEFORE = {
    "unindexed_series": [{"series_id": "s1", "symbol": "PG", "timeframe": "1d"}],
    "orphan_index_rows": [], "stale_checksum_rows": [],
}


def _record_sample(
    store: ReconcileRunStore,
    *,
    state: str = "done",
    started_utc: str = "2026-07-28T09:00:00.000000Z",
    finished_utc: str = "2026-07-28T09:00:05.000000Z",
    series_on_disk: int = 1,
    rows_indexed_before: int = 0,
    rows_indexed_after: int = 1,
    drift_before: dict | None = None,
    drift_after: dict | None = None,
    store_errors: list[dict] | None = None,
) -> dict:
    return record_reconcile_run(
        store,
        config_fingerprint="08e471b10130e1e2",
        started_utc=started_utc,
        finished_utc=finished_utc,
        state=state,
        series_on_disk=series_on_disk,
        rows_indexed_before=rows_indexed_before,
        rows_indexed_after=rows_indexed_after,
        drift_before=SAMPLE_DRIFT_BEFORE if drift_before is None else drift_before,
        drift_after=EMPTY_DRIFT if drift_after is None else drift_after,
        store_errors=[] if store_errors is None else store_errors,
    )


def test_record_stores_every_field_verbatim(tmp_path):
    store = ReconcileRunStore(tmp_path / "runs")
    meta = _record_sample(store)

    assert meta["config_fingerprint"] == "08e471b10130e1e2"
    assert meta["started_utc"] == "2026-07-28T09:00:00.000000Z"
    assert meta["finished_utc"] == "2026-07-28T09:00:05.000000Z"
    assert meta["state"] == "done"
    assert meta["series_on_disk"] == 1
    assert meta["rows_indexed_before"] == 0
    assert meta["rows_indexed_after"] == 1
    assert meta["drift_before"] == SAMPLE_DRIFT_BEFORE
    assert meta["drift_after"] == EMPTY_DRIFT
    assert meta["store_errors"] == []
    assert meta["id"].startswith("reconcile-2026-07-28-")
    assert len(list((tmp_path / "runs").glob("*.json"))) == 1


def test_record_rejects_a_non_terminal_state(tmp_path):
    store = ReconcileRunStore(tmp_path / "runs")
    with pytest.raises(ValueError):
        _record_sample(store, state="running")


def test_list_on_a_directory_that_was_never_created_is_honestly_empty(tmp_path):
    store = ReconcileRunStore(tmp_path / "runs" / "never-created")
    records, errors = store.list()
    assert records == [] and errors == []
    assert not (tmp_path / "runs" / "never-created").exists()


def test_a_run_that_never_reaches_the_writer_call_leaves_the_store_untouched(tmp_path):
    store = ReconcileRunStore(tmp_path / "runs")
    # ... a real caller's walk would happen here; the writer is deliberately never invoked, standing
    # in for a process that ends before the terminal write.
    records, errors = store.list()
    assert records == [] and errors == []
    assert not (tmp_path / "runs").exists()


def test_two_calls_with_identical_field_values_still_append_two_distinct_records(tmp_path):
    store = ReconcileRunStore(tmp_path / "runs")
    first = _record_sample(store)
    second = _record_sample(store)

    assert first["id"] != second["id"]
    records, errors = store.list()
    assert errors == []
    assert {r["id"] for r in records} == {first["id"], second["id"]}


def test_a_second_run_appends_without_touching_the_first_files_bytes_on_disk(tmp_path):
    root = tmp_path / "runs"
    store = ReconcileRunStore(root)
    first = _record_sample(store, started_utc="2026-07-28T09:00:00Z", finished_utc="2026-07-28T09:00:05Z")
    first_path = root / f"{first['id']}.json"
    first_bytes_before = first_path.read_bytes()

    second = _record_sample(
        store, started_utc="2026-07-28T10:00:00Z", finished_utc="2026-07-28T10:00:05Z", series_on_disk=2,
    )

    assert first_path.read_bytes() == first_bytes_before
    records, errors = store.list()
    assert errors == []
    assert len(records) == 2
    assert records[0]["id"] == first["id"]  # oldest-started first
    assert records[1]["id"] == second["id"]


def test_reconcile_run_store_has_no_update_or_delete_method():
    public_methods = {name for name in dir(ReconcileRunStore) if not name.startswith("_")}
    assert public_methods == {"root", "list", "record"}


def test_returned_drift_lists_are_independent_copies_never_a_shared_mutable_reference(tmp_path):
    store = ReconcileRunStore(tmp_path / "runs")
    _record_sample(store)

    records, _errors = store.list()
    records[0]["drift_before"]["unindexed_series"].append({"poison": True})
    records[0]["store_errors"].append({"poison": True})

    fresh, _errors2 = store.list()
    assert len(fresh[0]["drift_before"]["unindexed_series"]) == 1  # mutation above is invisible
    assert fresh[0]["store_errors"] == []


def test_tc20_corrupted_run_record_file_surfaces_explicitly_and_never_blocks_the_genuine_record(tmp_path):
    root = tmp_path / "runs"
    store = ReconcileRunStore(root)
    good = _record_sample(store)
    bad_path = root / "reconcile-2026-01-01-deadbeef0000.json"
    bad_path.write_text("{not json")

    records, errors = store.list()
    assert len(records) == 1 and records[0]["id"] == good["id"]
    assert len(errors) == 1 and errors[0]["file"] == "reconcile-2026-01-01-deadbeef0000.json"


def test_tampered_checksum_surfaces_as_an_integrity_error(tmp_path):
    root = tmp_path / "runs"
    store = ReconcileRunStore(root)
    _record_sample(store)
    path = next(root.glob("*.json"))
    data = json.loads(path.read_text())
    data["record"]["meta"]["series_on_disk"] = 999  # tamper -- file_checksum now disagrees
    path.write_text(json.dumps(data))

    records, errors = store.list()
    assert records == []
    assert len(errors) == 1
    assert "integrity" in errors[0]["error"]


def test_resolve_desk_index_reconcile_dir_defaults_to_a_sibling_of_the_universe_dir(monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_DESK_INDEX_RECONCILE_DIR", raising=False)
    resolved = resolve_desk_index_reconcile_dir("/some/root/.data/universe")
    assert resolved == "/some/root/.data/index_reconcile_runs"


def test_resolve_desk_index_reconcile_dir_env_override(monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_INDEX_RECONCILE_DIR", "/tmp/custom-reconcile-dir")
    assert resolve_desk_index_reconcile_dir("/some/root/.data/universe") == "/tmp/custom-reconcile-dir"


# ==================================================================================================
# DeskIndexReconcileComputeManager -- mechanics. A FAKE `classify_drift` (monkeypatched onto this
# module's own imported name -- the test_desk_topup_compute.py `_run_one_pair` precedent) gives
# deterministic, threading-free control for the single-flight/cancel tests (the plan's own
# "test-seam note").
# ==================================================================================================


def test_no_job_has_ever_run_snapshot_is_none():
    assert DeskIndexReconcileComputeManager().snapshot() is None


@pytest.fixture
def manager_env(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    reconcile_run_store = ReconcileRunStore(tmp_path / "runs")
    return bar_store, bar_index, reconcile_run_store


def test_trigger_on_an_empty_store_is_an_honest_zero_drift_job_that_completes(manager_env):
    bar_store, bar_index, reconcile_run_store = manager_env
    mgr = DeskIndexReconcileComputeManager()

    result = mgr.trigger(bar_store, bar_index, reconcile_run_store)
    assert result["started"] is True

    snap = _wait_for_terminal(mgr)
    assert snap["state"] == "done"
    mgr.join_all(timeout=5)

    records, errors = reconcile_run_store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0]["state"] == "done"
    assert records[0]["series_on_disk"] == 0
    assert records[0]["drift_before"] == EMPTY_DRIFT


def test_trigger_shape_reflects_a_real_drift_case_end_to_end(manager_env):
    bar_store, bar_index, reconcile_run_store = manager_env
    meta = _record(bar_store, symbol="PG", timeframe="1d")

    mgr = DeskIndexReconcileComputeManager()
    mgr.trigger(bar_store, bar_index, reconcile_run_store)
    snap = _wait_for_terminal(mgr)
    assert snap["state"] == "done"
    mgr.join_all(timeout=5)

    records, errors = reconcile_run_store.list()
    assert errors == []
    assert records[0]["series_on_disk"] == 1
    assert records[0]["rows_indexed_before"] == 0
    assert records[0]["rows_indexed_after"] == 1
    assert records[0]["drift_before"]["unindexed_series"] == [
        {"series_id": meta["id"], "symbol": "PG", "timeframe": "1d"}
    ]
    assert records[0]["drift_after"] == EMPTY_DRIFT


def test_second_trigger_while_running_returns_the_same_job_started_false(manager_env, monkeypatch):
    bar_store, bar_index, reconcile_run_store = manager_env
    started = threading.Event()
    release = threading.Event()

    def fake_classify_drift(store, index):
        started.set()
        release.wait(timeout=5)
        return dict(EMPTY_DRIFT), []

    monkeypatch.setattr(desk_index_reconcile, "classify_drift", fake_classify_drift)

    mgr = DeskIndexReconcileComputeManager()
    first = mgr.trigger(bar_store, bar_index, reconcile_run_store)
    assert started.wait(timeout=5)

    second = mgr.trigger(bar_store, bar_index, reconcile_run_store)
    assert second["started"] is False
    assert second["compute"]["id"] == first["compute"]["id"]

    release.set()
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)


def test_trigger_after_a_terminal_job_starts_a_genuinely_new_job(manager_env):
    bar_store, bar_index, reconcile_run_store = manager_env
    mgr = DeskIndexReconcileComputeManager()
    first = mgr.trigger(bar_store, bar_index, reconcile_run_store)
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)

    second = mgr.trigger(bar_store, bar_index, reconcile_run_store)
    assert second["started"] is True
    assert second["compute"]["id"] != first["compute"]["id"]
    _wait_for_terminal(mgr)
    mgr.join_all(timeout=5)

    records, errors = reconcile_run_store.list()
    assert errors == [] and len(records) == 2


def test_a_cancel_signal_observed_before_reindex_resolves_state_cancelled_with_no_repair(
    manager_env, monkeypatch
):
    bar_store, bar_index, reconcile_run_store = manager_env
    _record(bar_store)  # a real drift case -- a completed repair would be observable if it ran
    started = threading.Event()
    release = threading.Event()
    real_classify = desk_index_reconcile.classify_drift
    calls = {"n": 0}

    def fake_classify_drift(store, index):
        calls["n"] += 1
        if calls["n"] == 1:
            started.set()
            release.wait(timeout=5)
        return real_classify(store, index)

    monkeypatch.setattr(desk_index_reconcile, "classify_drift", fake_classify_drift)

    mgr = DeskIndexReconcileComputeManager()
    mgr.trigger(bar_store, bar_index, reconcile_run_store)
    assert started.wait(timeout=5)
    mgr.cancel()
    release.set()

    snap = _wait_for_terminal(mgr)
    assert snap["state"] == "cancelled"
    assert snap["error"] is None
    mgr.join_all(timeout=5)

    assert bar_index.list() == []  # reindex() never ran -- the abort fired before it started

    records, errors = reconcile_run_store.list()
    assert errors == [] and len(records) == 1
    assert records[0]["state"] == "cancelled"
    assert records[0]["rows_indexed_after"] == records[0]["rows_indexed_before"]


def test_an_unexpected_crash_resolves_state_failed_and_records_a_zeroed_run(manager_env, monkeypatch):
    bar_store, bar_index, reconcile_run_store = manager_env

    def fake_run_reconcile(*args, **kwargs):
        raise RuntimeError("synthetic catastrophic failure")

    monkeypatch.setattr(desk_index_reconcile, "run_reconcile", fake_run_reconcile)

    mgr = DeskIndexReconcileComputeManager()
    mgr.trigger(bar_store, bar_index, reconcile_run_store)
    snap = _wait_for_terminal(mgr)

    assert snap["state"] == "failed"
    assert snap["error"] == "synthetic catastrophic failure"
    mgr.join_all(timeout=5)

    records, errors = reconcile_run_store.list()
    assert errors == [] and len(records) == 1
    assert records[0]["state"] == "failed"
    assert records[0]["series_on_disk"] == 0
    assert records[0]["drift_before"] == EMPTY_DRIFT


def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_reference(manager_env):
    bar_store, bar_index, reconcile_run_store = manager_env
    mgr = DeskIndexReconcileComputeManager()
    mgr.trigger(bar_store, bar_index, reconcile_run_store)
    snap = _wait_for_terminal(mgr)
    snap["progress"]["phase"] = "POISONED"

    fresh = mgr.snapshot()
    assert fresh["progress"]["phase"] != "POISONED"
    mgr.join_all(timeout=5)


# ==================================================================================================
# Routes -- GET-never-computes, single-flight/cancel through HTTP, idle-cancel 409, honest-empty
# runs list, meta-only list vs full latest, corrupted-file survival (TC-6, TC-9, TC-10, TC-11,
# TC-20).
# ==================================================================================================


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    fresh_manager = DeskIndexReconcileComputeManager()
    app.dependency_overrides[get_desk_reconcile_manager] = lambda: fresh_manager
    with TestClient(app) as client:
        yield client, fresh_manager, tmp_path
    fresh_manager.join_all(timeout=5.0)
    set_registry(None)
    app.dependency_overrides.pop(get_desk_reconcile_manager, None)
    store.close()


def test_get_reconcile_compute_before_any_trigger_is_an_honest_null_and_starts_nothing(route_ctx):
    """TC-9."""
    client, fresh_manager, _tmp_path = route_ctx
    r = client.get("/research/desk/coverage/reconcile/compute")
    assert r.status_code == 200
    assert r.json() is None
    assert fresh_manager.snapshot() is None


def test_get_reconcile_runs_before_any_run_is_the_honest_empty_payload_and_starts_nothing(route_ctx):
    """TC-6. ``integrity_errors`` added goal-desk-iter-16 (J-12) — see
    ``test_get_reconcile_runs_surfaces_a_corrupted_run_records_integrity_error`` below for the
    non-empty case."""
    client, fresh_manager, _tmp_path = route_ctx
    r = client.get("/research/desk/coverage/reconcile/runs")
    assert r.status_code == 200
    assert r.json() == {"runs": [], "latest": None, "integrity_errors": []}
    assert fresh_manager.snapshot() is None  # the unrelated compute snapshot stayed untouched


def test_post_trigger_runs_to_completion_and_get_polls_the_same_snapshot(route_ctx):
    client, _fresh_manager, tmp_path = route_ctx
    BarStore(tmp_path / "bars").record(
        symbol="PG", timeframe="1d", window_start_utc="2026-06-01T00:00:00Z",
        window_end_utc="2026-06-04T00:00:00Z", feed="yahoo", bars=_small_series("PG"),
    )

    r = client.post("/research/desk/coverage/reconcile/compute")
    assert r.status_code == 200
    body = r.json()
    assert body["started"] is True
    assert body["compute"]["state"] == "running"

    deadline = time.time() + 5
    snap = None
    while time.time() < deadline:
        snap = client.get("/research/desk/coverage/reconcile/compute").json()
        if snap is not None and snap["state"] != "running":
            break
        time.sleep(0.02)
    assert snap["state"] == "done"

    runs = client.get("/research/desk/coverage/reconcile/runs").json()
    assert runs["latest"] is not None
    assert runs["latest"]["state"] == "done"
    assert runs["latest"]["series_on_disk"] == 1
    assert runs["latest"]["rows_indexed_after"] == 1
    assert len(runs["runs"]) == 1
    for heavy_key in ("drift_before", "drift_after", "store_errors"):
        assert heavy_key not in runs["runs"][0]  # meta-only list omits the heavy fields
        assert heavy_key in runs["latest"]


def test_cancel_while_idle_is_409(route_ctx):
    """TC-11."""
    client, _fresh_manager, _tmp_path = route_ctx
    r = client.post("/research/desk/coverage/reconcile/compute/cancel")
    assert r.status_code == 409


def test_cancel_while_running_succeeds_and_a_subsequent_idle_cancel_is_409(route_ctx, monkeypatch):
    client, fresh_manager, _tmp_path = route_ctx
    started = threading.Event()
    release = threading.Event()

    def fake_classify_drift(store, index):
        started.set()
        release.wait(timeout=5)
        return dict(EMPTY_DRIFT), []

    monkeypatch.setattr(desk_index_reconcile, "classify_drift", fake_classify_drift)

    trigger_resp = client.post("/research/desk/coverage/reconcile/compute")
    assert trigger_resp.json()["started"] is True
    assert started.wait(timeout=5)

    cancel_resp = client.post("/research/desk/coverage/reconcile/compute/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json() == {"cancelling": True}
    release.set()

    _wait_for_terminal(fresh_manager)
    fresh_manager.join_all(timeout=5)

    idle_cancel = client.post("/research/desk/coverage/reconcile/compute/cancel")
    assert idle_cancel.status_code == 409


def test_second_post_while_running_returns_started_false_through_http(route_ctx, monkeypatch):
    """TC-10."""
    client, fresh_manager, _tmp_path = route_ctx
    started = threading.Event()
    release = threading.Event()

    def fake_classify_drift(store, index):
        started.set()
        release.wait(timeout=5)
        return dict(EMPTY_DRIFT), []

    monkeypatch.setattr(desk_index_reconcile, "classify_drift", fake_classify_drift)

    first = client.post("/research/desk/coverage/reconcile/compute")
    assert started.wait(timeout=5)
    second = client.post("/research/desk/coverage/reconcile/compute")
    assert second.json()["started"] is False
    assert second.json()["compute"]["id"] == first.json()["compute"]["id"]

    release.set()
    _wait_for_terminal(fresh_manager)
    fresh_manager.join_all(timeout=5)


def test_reconcile_run_store_directory_defaults_to_a_sibling_of_the_scoped_universe_dir(route_ctx):
    client, _fresh_manager, tmp_path = route_ctx
    BarStore(tmp_path / "bars").record(
        symbol="PG", timeframe="1d", window_start_utc="2026-06-01T00:00:00Z",
        window_end_utc="2026-06-04T00:00:00Z", feed="yahoo", bars=_small_series("PG"),
    )
    client.post("/research/desk/coverage/reconcile/compute")
    deadline = time.time() + 5
    while time.time() < deadline:
        snap = client.get("/research/desk/coverage/reconcile/compute").json()
        if snap is not None and snap["state"] != "running":
            break
        time.sleep(0.02)

    store = ReconcileRunStore(tmp_path / "index_reconcile_runs")  # the sibling-of-universe-dir default
    records, errors = store.list()
    assert errors == []
    assert len(records) == 1


def test_tc20_get_reconcile_runs_survives_a_corrupted_run_record_file_alongside_a_genuine_one(route_ctx):
    client, _fresh_manager, tmp_path = route_ctx
    BarStore(tmp_path / "bars").record(
        symbol="PG", timeframe="1d", window_start_utc="2026-06-01T00:00:00Z",
        window_end_utc="2026-06-04T00:00:00Z", feed="yahoo", bars=_small_series("PG"),
    )
    client.post("/research/desk/coverage/reconcile/compute")
    deadline = time.time() + 5
    while time.time() < deadline:
        snap = client.get("/research/desk/coverage/reconcile/compute").json()
        if snap is not None and snap["state"] != "running":
            break
        time.sleep(0.02)

    # goal-desk-iter-16 (J-12) TC-6: the corrupt file is planted in this test's OWN scoped
    # `route_ctx` dir (rooted under `tmp_path`) -- never `apps/backend/.data`.
    reconcile_dir = tmp_path / "index_reconcile_runs"
    corrupt_path = reconcile_dir / "reconcile-2026-01-01-deadbeef0000.json"
    corrupt_path.write_text("{not json")

    r = client.get("/research/desk/coverage/reconcile/runs")
    assert r.status_code == 200
    body = r.json()
    assert len(body["runs"]) == 1  # the corrupted file is excluded, never fabricated, never a crash
    assert body["latest"] is not None
    assert body["latest"]["state"] == "done"
    # TC-6: the store's own `errors` return is now surfaced, never silently discarded.
    assert len(body["integrity_errors"]) == 1
    assert body["integrity_errors"][0]["file"] == corrupt_path.name
    assert "corrupted or tampered" in body["integrity_errors"][0]["error"]


def test_tc8_route_level_a_reconcile_run_leaves_the_universe_snapshot_file_byte_identical(route_ctx):
    client, _fresh_manager, tmp_path = route_ctx
    universe_store = UniverseStore(tmp_path / "universe")
    universe_store.record(
        members=["PG"], raw_members={"PG": "PG"},
        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
    )
    universe_path = next((tmp_path / "universe").glob("*.json"))
    universe_bytes_before = universe_path.read_bytes()
    BarStore(tmp_path / "bars").record(
        symbol="PG", timeframe="1d", window_start_utc="2026-06-01T00:00:00Z",
        window_end_utc="2026-06-04T00:00:00Z", feed="yahoo", bars=_small_series("PG"),
    )

    client.post("/research/desk/coverage/reconcile/compute")
    deadline = time.time() + 5
    while time.time() < deadline:
        snap = client.get("/research/desk/coverage/reconcile/compute").json()
        if snap is not None and snap["state"] != "running":
            break
        time.sleep(0.02)

    assert universe_path.read_bytes() == universe_bytes_before
