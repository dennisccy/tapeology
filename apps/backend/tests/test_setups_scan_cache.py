"""``SetupsScanCache`` (era-fast_wall J-06) -- store-level discipline, tested standalone (no
``compute_setups``, no real bar store/scan). Mirrors ``tests/test_edge_report_backtest_cache.py``'s
own directness: every test here feeds the cache a CHEAP dict instead of a real scan result -- the
cache mechanics (keying, durability, concurrency, corrupted-DB tolerance) are independent of what a
real scan actually computes. The WIRING into ``setups.compute_setups`` (the three-tier lookup,
byte-identity, restart simulation, the non-vacuous mutation probe) is covered separately in
``tests/test_setups.py``.
"""

from __future__ import annotations

import json
import sqlite3
import threading

from app.research.setups_scan_cache import (
    SetupsScanCache,
    resolve_scan_cache_db_path,
    scan_cache_key,
)


def _base_kwargs() -> dict:
    return dict(
        config_content_hash="hash-1",
        store_signature=(("AAPL", "5m", "series-1", "chk-1"), ("AAPL", "1d", "series-2", "chk-2")),
    )


# One replacement value per key component -- used both to prove the key CHANGES (pure function) and
# to prove a call-counting spy sees a fresh call for EVERY one of the two (the key-busting matrix).
_MUTATIONS: dict[str, object] = {
    "config_content_hash": "hash-2",
    "store_signature": (("AAPL", "5m", "series-3", "chk-3"),),
}


# --- scan_cache_key: a pure function, non-vacuous key-busting matrix -----------------------------


def test_scan_cache_key_is_stable_for_identical_inputs():
    assert scan_cache_key(**_base_kwargs()) == scan_cache_key(**_base_kwargs())


def test_scan_cache_key_changes_when_either_component_changes():
    base_key = scan_cache_key(**_base_kwargs())
    for component, new_value in _MUTATIONS.items():
        mutated = _base_kwargs()
        mutated[component] = new_value
        mutated_key = scan_cache_key(**mutated)
        assert mutated_key != base_key, f"mutating {component!r} alone must change the key"


def test_scan_cache_key_mutations_are_pairwise_distinct():
    """A stronger non-vacuous guard than base-vs-mutated alone: no two DIFFERENT single-component
    mutations may collide with each other either (would silently mean two distinct scans share one
    cached row)."""
    keys = [scan_cache_key(**_base_kwargs())]
    for component, new_value in _MUTATIONS.items():
        mutated = _base_kwargs()
        mutated[component] = new_value
        keys.append(scan_cache_key(**mutated))
    assert len(keys) == len(set(keys)), "every one of the 3 scenarios must produce a distinct key"


def test_scan_cache_key_store_signature_order_independence_is_the_callers_job_not_this_functions():
    """``scan_cache_key`` itself is a PURE, literal function of whatever tuple it is handed --
    ordering stability is ``setups._store_signature``'s own contract (it already sorts), not
    something this function re-derives. A differently-ORDERED tuple is a genuinely different literal
    input and therefore correctly produces a different key here."""
    ordered = (("AAPL", "5m", "a", "1"), ("AAPL", "1d", "b", "2"))
    reordered = (("AAPL", "1d", "b", "2"), ("AAPL", "5m", "a", "1"))
    key_a = scan_cache_key(config_content_hash="h", store_signature=ordered)
    key_b = scan_cache_key(config_content_hash="h", store_signature=reordered)
    assert key_a != key_b


class _CountingScan:
    """A stub standing in for ``setups._run_full_panel_scan`` (mirrors
    ``test_edge_report_backtest_cache.py``'s own ``_CountingBacktest`` precedent) — proving the
    CACHE's mechanics against a cheap stub, independent of what a real scan actually computes."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> dict:
        self.calls += 1
        return {"call_number": self.calls}


def test_key_busting_matrix_a_call_counting_spy_records_a_new_call_for_every_mutation(tmp_path):
    """Non-vacuous: a warm row for the base scan, then EACH of the two components mutated in turn
    (holding the other fixed) forces a fresh 'scan' call — proving each component independently
    busts the key (a cache silently ignoring one component would fail exactly that case)."""
    cache = SetupsScanCache(str(tmp_path / "scan_cache.db"))
    compute = _CountingScan()

    def _lookup_or_compute(kwargs: dict) -> dict:
        key = scan_cache_key(**kwargs)
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
        _lookup_or_compute(mutated)  # a second request for the SAME mutated scan -- must NOT recompute
        assert compute.calls == expected_calls


# --- lookup / publish mechanics -------------------------------------------------------------------


def test_cold_lookup_is_none(tmp_path):
    cache = SetupsScanCache(str(tmp_path / "cache.db"))
    assert cache.lookup(scan_cache_key(**_base_kwargs())) is None


def test_publish_then_lookup_returns_the_result_verbatim(tmp_path):
    cache = SetupsScanCache(str(tmp_path / "cache.db"))
    key = scan_cache_key(**_base_kwargs())
    result = {"events": [{"id": "abc", "reaction": "rejected"}]}

    cache.publish(key, result)

    assert cache.lookup(key) == result


def test_result_round_trips_byte_identically_through_json_persistence(tmp_path):
    """Floats, nested lists/dicts, and ``None`` all survive a JSON round-trip through the durable
    layer byte-identically (structural equality on the round-tripped dict)."""
    cache = SetupsScanCache(str(tmp_path / "cache.db"))
    key = scan_cache_key(**_base_kwargs())
    result = {
        "events": [
            {
                "id": "abc",
                "forward_returns": [{"horizon_bars": 78, "return_fraction": -0.007453190329031024}],
                "reaction_boundary_truncated": False,
                "tape_timeline": [],
            },
        ],
    }

    cache.publish(key, result)

    assert cache.lookup(key) == result


def test_second_publish_under_the_same_key_replaces_the_row(tmp_path):
    cache = SetupsScanCache(str(tmp_path / "cache.db"))
    key = scan_cache_key(**_base_kwargs())

    cache.publish(key, {"events": [], "version": 1})
    cache.publish(key, {"events": [], "version": 2})

    assert cache.lookup(key) == {"events": [], "version": 2}

    conn = sqlite3.connect(str(tmp_path / "cache.db"))
    try:
        (count,) = conn.execute(
            "SELECT COUNT(*) FROM setups_scan_cache WHERE cache_key=?", (key,)
        ).fetchone()
    finally:
        conn.close()
    assert count == 1  # INSERT OR REPLACE -- never a duplicate row under one key


def test_stored_value_is_not_sort_keys_serialized(tmp_path):
    """The ``EdgeReportCache._insert`` byte-identity discipline, applied here: storage preserves the
    dict's OWN insertion order rather than alphabetizing it (``json.dumps`` default, never
    ``sort_keys=True``) — a stored row's raw bytes reflect the caller's own field order."""
    cache = SetupsScanCache(str(tmp_path / "cache.db"))
    key = scan_cache_key(**_base_kwargs())
    result = {"zeta": 1, "alpha": 2, "middle": 3}  # deliberately not alphabetical

    cache.publish(key, result)

    conn = sqlite3.connect(str(tmp_path / "cache.db"))
    try:
        (raw,) = conn.execute(
            "SELECT result_json FROM setups_scan_cache WHERE cache_key=?", (key,)
        ).fetchone()
    finally:
        conn.close()
    assert raw == json.dumps(result)  # NOT json.dumps(result, sort_keys=True)


# --- durability across a simulated backend restart -------------------------------------------------


def test_durability_across_a_simulated_restart_serves_the_prior_row(tmp_path):
    db_path = str(tmp_path / "cache.db")
    key = scan_cache_key(**_base_kwargs())
    original = SetupsScanCache(db_path)
    original.publish(key, {"events": [{"id": "real"}]})

    restarted = SetupsScanCache(db_path)  # a brand-new instance, no in-process state at all

    assert restarted.lookup(key) == {"events": [{"id": "real"}]}


def test_deleting_the_db_file_is_harmless_a_fresh_instance_starts_cold(tmp_path):
    db_path = tmp_path / "cache.db"
    key = scan_cache_key(**_base_kwargs())
    cache = SetupsScanCache(str(db_path))
    cache.publish(key, {"events": [{"id": "real"}]})
    assert cache.lookup(key) == {"events": [{"id": "real"}]}

    for suffix in ("", "-wal", "-shm"):
        sidecar = db_path.parent / (db_path.name + suffix)
        if sidecar.exists():
            sidecar.unlink()

    fresh = SetupsScanCache(str(db_path))
    assert fresh.lookup(key) is None  # loses nothing it shouldn't -- an honest cold miss


# --- error handling: never a crash, never blocks the caller (goal.md's own error-cases clause) -----


def test_construction_against_a_corrupted_file_never_raises(tmp_path):
    db_path = tmp_path / "garbage.db"
    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)

    SetupsScanCache(str(db_path))  # must not raise


def test_lookup_on_a_corrupted_db_file_returns_none_never_crashes(tmp_path):
    db_path = tmp_path / "garbage.db"
    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
    cache = SetupsScanCache(str(db_path))

    assert cache.lookup("any-key") is None


def test_publish_on_a_corrupted_db_file_is_swallowed_never_crashes(tmp_path):
    db_path = tmp_path / "garbage.db"
    db_path.write_bytes(b"not a real sqlite file, just garbage bytes " * 20)
    cache = SetupsScanCache(str(db_path))

    cache.publish("some-key", {"events": []})  # must not raise, whether or not it actually persisted


# --- concurrency: many THREADS publishing distinct keys never crash or corrupt each other ----------


def test_many_threads_publishing_distinct_keys_concurrently_never_lose_or_corrupt_a_row(tmp_path):
    cache = SetupsScanCache(str(tmp_path / "cache.db"))
    n_threads = 16

    def _publish_one(i: int) -> None:
        kwargs = _base_kwargs()
        kwargs["config_content_hash"] = f"hash-{i}"
        key = scan_cache_key(**kwargs)
        cache.publish(key, {"events": [{"i": i}]})

    threads = [threading.Thread(target=_publish_one, args=(i,)) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    for i in range(n_threads):
        kwargs = _base_kwargs()
        kwargs["config_content_hash"] = f"hash-{i}"
        key = scan_cache_key(**kwargs)
        assert cache.lookup(key) == {"events": [{"i": i}]}


# --- resolve_scan_cache_db_path: env-else-sibling-of-bar-dir (mirrors resolve_cache_db_path /
# resolve_backtest_cache_db_path) --------------------------------------------------------------------


def test_resolve_scan_cache_db_path_defaults_to_a_sibling_of_the_bar_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_SETUPS_CACHE_DB", raising=False)
    bar_dir = str(tmp_path / "bars")

    resolved = resolve_scan_cache_db_path(bar_dir)

    assert resolved == str(tmp_path / "setups_scan_cache.db")


def test_resolve_scan_cache_db_path_honors_the_env_override(tmp_path, monkeypatch):
    override = str(tmp_path / "custom" / "scan_cache.db")
    monkeypatch.setenv("TAPEOLOGY_SETUPS_CACHE_DB", override)

    resolved = resolve_scan_cache_db_path(str(tmp_path / "bars"))

    assert resolved == override


def test_resolve_scan_cache_db_path_never_collides_with_sibling_cache_paths(tmp_path, monkeypatch):
    """The three durable caches (whole-report, per-pair sub-results, setups scan) must resolve to
    DIFFERENT default sibling filenames beside the SAME parent directory — a real regression this
    test would catch (accidentally reusing a sibling cache's own filename)."""
    monkeypatch.delenv("TAPEOLOGY_SETUPS_CACHE_DB", raising=False)
    monkeypatch.delenv("TAPEOLOGY_EDGE_REPORT_CACHE_DB", raising=False)
    monkeypatch.delenv("TAPEOLOGY_EDGE_SWEEP_CACHE_DB", raising=False)
    from app.research.edge_report_backtest_cache import resolve_backtest_cache_db_path
    from app.research.edge_report_cache import resolve_cache_db_path

    parent = str(tmp_path / "bars")
    resolved = {
        resolve_scan_cache_db_path(parent),
        resolve_cache_db_path(parent),
        resolve_backtest_cache_db_path(parent),
    }
    assert len(resolved) == 3
