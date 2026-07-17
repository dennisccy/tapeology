"""``EdgeReportBacktestCache`` (era-fast_wall J-05) — store-level discipline, tested standalone (no
FastAPI, no real backtests). Mirrors ``tests/test_edge_report_cache.py``'s own directness: every
test here feeds the cache a CHEAP counting stub instead of a real ``_run_backtest`` call — the
cache mechanics (keying, durability, concurrency, corrupted-DB tolerance) are independent of what a
real backtest actually computes, so proving them against a fast stub is both faster and a purer
isolation than routing every case through a real multi-strategy sweep. The WIRING into
``edge_report.py`` (byte-identity, kill-and-resume, new-dataset-costs-three, parallel equivalence)
is covered separately in ``tests/test_edge_report.py``; the CLI/manager wiring is covered in
``tests/test_edge_report_compute.py``.
"""

from __future__ import annotations

import json
import sqlite3
import threading

from app.research.edge_report_backtest_cache import (
    EdgeReportBacktestCache,
    pair_cache_key,
    resolve_backtest_cache_db_path,
)


def _base_kwargs() -> dict:
    return dict(
        dataset_id="ds-1",
        dataset_checksum="checksum-1",
        strategy_id="v1",
        profile="default",
        config_fingerprint="fp-1",
        config_content_hash="hash-1",
        strategy_registry=[{"id": "v1"}],
        bar_store_signature=(("AAPL", "5m", "series-1", "chk-1"),),
    )


# One replacement value per key component — used both to prove the key CHANGES (pure function)
# and to prove a call-counting spy sees a fresh call for EVERY one of the eight (TC-5).
_MUTATIONS: dict[str, object] = {
    "dataset_id": "ds-2",
    "dataset_checksum": "checksum-2",
    "strategy_id": "structure_tape",
    "profile": "candidate",
    "config_fingerprint": "fp-2",
    "config_content_hash": "hash-2",
    "strategy_registry": [{"id": "v1"}, {"id": "structure_tape"}],
    "bar_store_signature": (("AAPL", "5m", "series-2", "chk-2"),),
}


# --- pair_cache_key: a pure function, non-vacuous key-busting matrix (TC-5) -----------------------


def test_pair_cache_key_is_stable_for_identical_inputs():
    assert pair_cache_key(**_base_kwargs()) == pair_cache_key(**_base_kwargs())


def test_pair_cache_key_changes_when_any_one_of_the_eight_components_changes():
    base_key = pair_cache_key(**_base_kwargs())
    for component, new_value in _MUTATIONS.items():
        mutated = _base_kwargs()
        mutated[component] = new_value
        mutated_key = pair_cache_key(**mutated)
        assert mutated_key != base_key, f"mutating {component!r} alone must change the key"


def test_pair_cache_key_mutations_are_all_pairwise_distinct():
    """A stronger non-vacuous guard than base-vs-mutated alone: no two DIFFERENT single-component
    mutations may collide with each other either (would silently mean two distinct pairs share one
    cached row)."""
    keys = [pair_cache_key(**_base_kwargs())]
    for component, new_value in _MUTATIONS.items():
        mutated = _base_kwargs()
        mutated[component] = new_value
        keys.append(pair_cache_key(**mutated))
    assert len(keys) == len(set(keys)), "every one of the 9 scenarios must produce a distinct key"


class _CountingBacktest:
    """A stub standing in for ``edge_report._run_backtest`` (mirrors ``test_edge_report_cache.py``'s
    own ``_CountingCompute`` precedent) — proving the CACHE's mechanics against a cheap stub,
    independent of what a real backtest actually computes."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> dict:
        self.calls += 1
        return {"call_number": self.calls}


def test_key_busting_matrix_a_call_counting_spy_records_a_new_call_for_every_mutation(tmp_path):
    """TC-5, non-vacuous: a warm row for the base pair, then EACH of the eight components mutated
    in turn (holding the other seven fixed) forces a fresh 'backtest' call — proving each component
    independently busts the key (a cache silently ignoring one component would fail exactly that
    row)."""
    cache = EdgeReportBacktestCache(str(tmp_path / "sub_cache.db"))
    compute = _CountingBacktest()

    def _lookup_or_compute(kwargs: dict) -> dict:
        key = pair_cache_key(**kwargs)
        cached = cache.lookup(key)
        if cached is not None:
            return cached
        result = compute()
        cache.publish(key, result)
        return result

    _lookup_or_compute(_base_kwargs())
    assert compute.calls == 1
    _lookup_or_compute(_base_kwargs())  # a genuine warm hit -- no new call
    assert compute.calls == 1

    expected_calls = 1
    for component, new_value in _MUTATIONS.items():
        mutated = _base_kwargs()
        mutated[component] = new_value
        _lookup_or_compute(mutated)
        expected_calls += 1
        assert compute.calls == expected_calls, f"mutating {component!r} must trigger a fresh compute"
        _lookup_or_compute(mutated)  # a second request for the SAME mutated pair -- must NOT recompute
        assert compute.calls == expected_calls


# --- lookup / publish mechanics -------------------------------------------------------------------


def test_cold_lookup_is_none(tmp_path):
    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
    assert cache.lookup(pair_cache_key(**_base_kwargs())) is None


def test_publish_then_lookup_returns_the_result_verbatim(tmp_path):
    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
    key = pair_cache_key(**_base_kwargs())
    result = {"trades": [{"a": 1}], "aggregates": {"net_r": 1.5}}

    cache.publish(key, result)

    assert cache.lookup(key) == result


def test_result_round_trips_byte_identically_through_json_persistence(tmp_path):
    """Floats, nested lists/dicts, and ``None`` all survive a JSON round-trip through the durable
    layer byte-identically (structural equality on the round-tripped dict)."""
    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
    key = pair_cache_key(**_base_kwargs())
    result = {
        "trades": [{"entry": {"price": 100.245, "logical_ts": 19.5}, "exit": None}],
        "aggregates": {"net_r": -0.16000000000001136, "n": 1, "win_rate": None},
    }

    cache.publish(key, result)

    assert cache.lookup(key) == result


def test_second_publish_under_the_same_key_replaces_the_row(tmp_path):
    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
    key = pair_cache_key(**_base_kwargs())

    cache.publish(key, {"version": 1})
    cache.publish(key, {"version": 2})

    assert cache.lookup(key) == {"version": 2}

    conn = sqlite3.connect(str(tmp_path / "cache.db"))
    try:
        (count,) = conn.execute(
            "SELECT COUNT(*) FROM edge_report_backtest_cache WHERE cache_key=?", (key,)
        ).fetchone()
    finally:
        conn.close()
    assert count == 1  # INSERT OR REPLACE -- never a duplicate row under one key


def test_stored_value_is_not_sort_keys_serialized(tmp_path):
    """The ``EdgeReportCache._insert`` byte-identity discipline, applied here: storage preserves
    the dict's OWN insertion order rather than alphabetizing it (``json.dumps`` default, never
    ``sort_keys=True``) — a stored row's raw bytes reflect the caller's own field order."""
    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
    key = pair_cache_key(**_base_kwargs())
    # A dict whose insertion order is deliberately NOT alphabetical.
    result = {"zeta": 1, "alpha": 2, "middle": 3}

    cache.publish(key, result)

    conn = sqlite3.connect(str(tmp_path / "cache.db"))
    try:
        (raw,) = conn.execute(
            "SELECT result_json FROM edge_report_backtest_cache WHERE cache_key=?", (key,)
        ).fetchone()
    finally:
        conn.close()
    assert raw == json.dumps(result)  # NOT json.dumps(result, sort_keys=True)


# --- durability across a simulated backend/worker restart -----------------------------------------


def test_durability_across_a_simulated_restart_serves_the_prior_row(tmp_path):
    db_path = str(tmp_path / "cache.db")
    key = pair_cache_key(**_base_kwargs())
    original = EdgeReportBacktestCache(db_path)
    original.publish(key, {"shape": "real"})

    restarted = EdgeReportBacktestCache(db_path)  # a brand-new instance, no in-process state at all

    assert restarted.lookup(key) == {"shape": "real"}


def test_deleting_the_db_file_is_harmless_a_fresh_instance_starts_cold(tmp_path):
    db_path = tmp_path / "cache.db"
    key = pair_cache_key(**_base_kwargs())
    cache = EdgeReportBacktestCache(str(db_path))
    cache.publish(key, {"shape": "real"})
    assert cache.lookup(key) == {"shape": "real"}

    for suffix in ("", "-wal", "-shm"):
        sidecar = db_path.parent / (db_path.name + suffix)
        if sidecar.exists():
            sidecar.unlink()

    fresh = EdgeReportBacktestCache(str(db_path))
    assert fresh.lookup(key) is None  # loses nothing it shouldn't -- an honest cold miss


# --- error handling: never a crash, never blocks the sweep (goal.md's own error-cases clause) -----


def test_construction_against_a_corrupted_file_never_raises(tmp_path):
    db_path = tmp_path / "garbage.db"
    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)

    EdgeReportBacktestCache(str(db_path))  # must not raise


def test_lookup_on_a_corrupted_db_file_returns_none_never_crashes(tmp_path):
    db_path = tmp_path / "garbage.db"
    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
    cache = EdgeReportBacktestCache(str(db_path))

    assert cache.lookup("any-key") is None


def test_publish_on_a_corrupted_db_file_is_swallowed_never_crashes(tmp_path):
    db_path = tmp_path / "garbage.db"
    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
    cache = EdgeReportBacktestCache(str(db_path))

    cache.publish("some-key", {"n": 1})  # must not raise, whether or not it actually persisted


# --- concurrency: many THREADS publishing distinct keys never crash or corrupt each other ---------
# (Mirrors test_edge_report_cache.py's own concurrency test shape — the genuine multi-PROCESS
# proof, via a real ProcessPoolExecutor, lives in test_edge_report.py's parallel-sweep test, since
# it needs the real _run_backtest/dataset/bar-store machinery this module intentionally stays
# ignorant of.)


def test_many_threads_publishing_distinct_keys_concurrently_never_lose_or_corrupt_a_row(tmp_path):
    cache = EdgeReportBacktestCache(str(tmp_path / "cache.db"))
    n_threads = 16

    def _publish_one(i: int) -> None:
        kwargs = _base_kwargs()
        kwargs["dataset_id"] = f"ds-{i}"
        key = pair_cache_key(**kwargs)
        cache.publish(key, {"i": i})

    threads = [threading.Thread(target=_publish_one, args=(i,)) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    for i in range(n_threads):
        kwargs = _base_kwargs()
        kwargs["dataset_id"] = f"ds-{i}"
        key = pair_cache_key(**kwargs)
        assert cache.lookup(key) == {"i": i}


# --- resolve_backtest_cache_db_path: env-else-sibling-of-dataset-dir (mirrors resolve_cache_db_path)


def test_resolve_backtest_cache_db_path_defaults_to_a_sibling_of_the_dataset_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", raising=False)
    dataset_dir = str(tmp_path / "datasets")

    resolved = resolve_backtest_cache_db_path(dataset_dir)

    assert resolved == str(tmp_path / "edge_report_backtests.db")


def test_resolve_backtest_cache_db_path_honors_the_env_override(tmp_path, monkeypatch):
    override = str(tmp_path / "custom" / "sub_cache.db")
    monkeypatch.setenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", override)

    resolved = resolve_backtest_cache_db_path(str(tmp_path / "datasets"))

    assert resolved == override


def test_resolve_backtest_cache_db_path_never_collides_with_the_whole_report_cache_path(tmp_path, monkeypatch):
    """The two durable caches must resolve to DIFFERENT default sibling filenames — a real
    regression this test would catch (accidentally reusing edge_report_cache.py's own filename)."""
    monkeypatch.delenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", raising=False)
    monkeypatch.delenv("TAPEOLOGY_EDGE_REPORT_CACHE_DB", raising=False)
    from app.research.edge_report_cache import resolve_cache_db_path

    dataset_dir = str(tmp_path / "datasets")
    assert resolve_backtest_cache_db_path(dataset_dir) != resolve_cache_db_path(dataset_dir)
