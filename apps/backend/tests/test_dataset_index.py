"""``DatasetIndex`` (era-fast_wall J-02) — store-level discipline, mirroring
``tests/test_bar_index.py``'s directness: this module tests ``DatasetIndex`` on its own first
(no ``DatasetStore``), proving the exact stat-keyed lookup and the idempotent insert-overwrite
contract, then proves the TWO durable-index acceptance clauses (TC-9, TC-10) through
``DatasetStore`` itself — the restart-simulation and delete-and-repopulate guarantees that are
the whole reason this index exists.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import CONFIG
from app.research.dataset_index import DatasetIndex
from app.research.datasets import DatasetStore, SPLIT_TRAIN, record_from_source

TRAIN_START, TRAIN_END = "2026-06-09T17:00:00Z", "2026-06-09T17:01:00Z"
HOLDOUT_START, HOLDOUT_END = "2026-06-09T17:05:00Z", "2026-06-09T17:05:45Z"


def _age(path: Path, seconds: float = 5.0) -> None:
    past = time.time() - seconds
    os.utime(path, (past, past))


def _record(store: DatasetStore, start: str, end: str, split: str = SPLIT_TRAIN) -> dict:
    return record_from_source(
        store, source_kind="reference", source_id="", split=split, start=start, end=end, config=CONFIG
    )


# --- DatasetIndex on its own: the exact stat-keyed lookup contract --------------------------------


def test_insert_then_lookup_is_a_hit(tmp_path):
    index = DatasetIndex(str(tmp_path / "index.db"))
    meta = {"id": "abc123", "symbol": "PG", "split": SPLIT_TRAIN}

    index.insert("/some/path/abc123.json", 4096, 1_700_000_000_000_000_000, meta)

    hit = index.lookup("/some/path/abc123.json", 4096, 1_700_000_000_000_000_000)
    assert hit == meta


def test_lookup_before_any_insert_is_a_miss(tmp_path):
    index = DatasetIndex(str(tmp_path / "index.db"))
    assert index.lookup("/nowhere.json", 1, 1) is None


def test_lookup_with_a_different_size_or_mtime_is_a_miss(tmp_path):
    """ANY stat mismatch is an honest miss — never an approximate or stale hit."""
    index = DatasetIndex(str(tmp_path / "index.db"))
    meta = {"id": "abc123"}
    index.insert("/p.json", 4096, 1_700_000_000_000_000_000, meta)

    assert index.lookup("/p.json", 4097, 1_700_000_000_000_000_000) is None  # size differs
    assert index.lookup("/p.json", 4096, 1_700_000_000_000_000_001) is None  # mtime differs
    assert index.lookup("/different-path.json", 4096, 1_700_000_000_000_000_000) is None


def test_insert_is_idempotent_and_overwrites_the_same_path(tmp_path):
    """The self-heal shape: re-inserting under the IDENTICAL path (e.g. a legitimate content
    change, new size/mtime) overwrites rather than duplicates or errors."""
    index = DatasetIndex(str(tmp_path / "index.db"))
    index.insert("/p.json", 100, 111, {"version": 1})
    index.insert("/p.json", 200, 222, {"version": 2})

    assert index.lookup("/p.json", 100, 111) is None  # the OLD stat no longer matches
    assert index.lookup("/p.json", 200, 222) == {"version": 2}


def test_meta_json_is_stored_without_sort_keys_preserving_insertion_order(tmp_path):
    """The ``edge_report_cache.py``/goal.md byte-identity discipline: a durable-index-served
    value must reproduce the EXACT key order it was given, never alphabetized — otherwise a
    warm-index-served REST/MCP response could byte-differ from a fresh verify despite identical
    content."""
    index = DatasetIndex(str(tmp_path / "index.db"))
    ordered_meta = {"zeta": 1, "alpha": 2, "middle": 3}
    index.insert("/p.json", 1, 1, ordered_meta)

    row = index._conn.execute("SELECT meta_json FROM dataset_index WHERE path=?", ("/p.json",)).fetchone()
    assert row["meta_json"] == '{"zeta": 1, "alpha": 2, "middle": 3}'


# --- DatasetStore + DatasetIndex integration: TC-9, TC-10 ------------------------------------------


def test_fresh_datasetstore_restart_serves_list_from_the_durable_index_with_zero_reads(tmp_path, monkeypatch):
    """TC-9."""
    root = tmp_path / "datasets"
    index_db = tmp_path / "dataset_index.db"

    warm_store = DatasetStore(root, index_db_path=str(index_db))
    a = _record(warm_store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)
    b = _record(warm_store, HOLDOUT_START, HOLDOUT_END, "holdout")
    for meta in (a, b):
        _age(root / f"{meta['id']}.json")
    warm_records, warm_errors = warm_store.list()  # populates BOTH the in-process and durable index
    assert warm_errors == []
    assert len(warm_records) == 2

    # A from-scratch, INDEX-FREE store — the comparison baseline (never touches the index).
    baseline_records, baseline_errors = DatasetStore(root).list()
    assert baseline_errors == []

    # A BRAND NEW DatasetStore instance -- SAME index_db_path -- simulates a backend restart. The
    # module-level in-process cache is SHARED by path across every DatasetStore instance in this
    # process (by design -- it is not instance-scoped), so it must be explicitly reset here to
    # genuinely simulate "fresh in-process cache" -- otherwise this test would trivially pass via
    # the STILL-WARM in-process layer without ever proving the DURABLE index did the work.
    import app.research.datasets as datasets_module

    datasets_module._reset_verified_cache_for_tests()

    calls: list[int] = []
    real_load = datasets_module.DatasetStore._load

    def _counting_load(self, path):
        calls.append(1)
        return real_load(self, path)

    monkeypatch.setattr(datasets_module.DatasetStore, "_load", _counting_load)

    restarted_store = DatasetStore(root, index_db_path=str(index_db))
    restarted_records, restarted_errors = restarted_store.list()

    assert len(calls) == 0, "a durable-index hit must cost ZERO calls to the full verifier"
    assert restarted_errors == []
    import json

    assert json.dumps(restarted_records, sort_keys=True) == json.dumps(baseline_records, sort_keys=True)


def test_deleting_the_index_db_costs_one_reverify_pass_and_repopulates(tmp_path, monkeypatch):
    """TC-10."""
    root = tmp_path / "datasets"
    index_db = tmp_path / "dataset_index.db"

    seed_store = DatasetStore(root, index_db_path=str(index_db))
    a = _record(seed_store, TRAIN_START, TRAIN_END, SPLIT_TRAIN)
    b = _record(seed_store, HOLDOUT_START, HOLDOUT_END, "holdout")
    for meta in (a, b):
        _age(root / f"{meta['id']}.json")
    seed_records, seed_errors = seed_store.list()  # populates the durable index with 2 rows
    assert seed_errors == [] and len(seed_records) == 2
    assert index_db.exists()

    index_db.unlink()  # simulate a missing/corrupted durable index DB file
    assert not index_db.exists()

    import app.research.datasets as datasets_module

    # Simulate "fresh in-process cache" too (see the identical note in the TC-9 test above) --
    # otherwise the still-warm in-process layer would serve this without ever touching either
    # the (just-deleted) durable index OR the full verifier, and the call-count assertions below
    # would prove nothing.
    datasets_module._reset_verified_cache_for_tests()

    calls: list[int] = []
    real_load = datasets_module.DatasetStore._load

    def _counting_load(self, path):
        calls.append(1)
        return real_load(self, path)

    monkeypatch.setattr(datasets_module.DatasetStore, "_load", _counting_load)

    fresh_store = DatasetStore(root, index_db_path=str(index_db))
    records, errors = fresh_store.list()

    assert errors == [], "no exception, no lost dataset — a missing index DB is fully recoverable"
    assert len(records) == 2
    assert len(calls) == 2, "each of the N=2 dataset files must be fully re-verified exactly once"
    assert index_db.exists(), "the durable index DB must exist again, repopulated"

    # And the durable index really was repopulated -- a THIRD, brand-new store instance, with the
    # in-process cache explicitly cleared AGAIN (the identical "simulate a fresh process" note
    # above), now serves entirely from the durable index with zero further reads.
    calls.clear()
    datasets_module._reset_verified_cache_for_tests()
    third_store = DatasetStore(root, index_db_path=str(index_db))
    third_records, third_errors = third_store.list()
    assert third_errors == []
    assert len(calls) == 0, "the repopulated index must serve the next restart with zero reads too"
    import json

    assert json.dumps(third_records, sort_keys=True) == json.dumps(records, sort_keys=True)
