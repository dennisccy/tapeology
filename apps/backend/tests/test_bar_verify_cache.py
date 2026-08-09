"""The durable stat-keyed verified-metadata cache (``bar_verify_cache.py``) and ``BarStore``'s use
of it.

``_VERIFIED_CACHE`` is a module global, so every fresh process re-verified the whole store on its
first read — ~15s on the live desk store, paid by the first member of every screen after a restart
and again by every worker process of a parallel walk. This cache remembers what a PRIOR process
already proved, keyed on the identical ``(path, size, mtime_ns)`` triple the in-process tier uses.

What must stay true, and is pinned here: a hit is byte-identical to a from-scratch verify; ANY stat
change misses and re-verifies in full (so ordinary corruption is still caught and still raises);
losing the DB loses nothing; a store built WITHOUT a cache path behaves exactly as it did before
this module existed; and the cache never becomes load-bearing — it stores metadata only, and never
candles."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

from app.providers.adapters.base import RawBar
from app.research.bar_verify_cache import BarVerifyCache
from app.research.bars import BarSeriesIntegrityError, BarStore, _reset_verified_cache_for_tests

_BASE_EPOCH = 1_750_000_000.0
_DAY = 86_400.0


def _bars(symbol: str, timeframe: str, count: int, first: int = 0) -> list[RawBar]:
    return [
        RawBar(symbol, timeframe, _BASE_EPOCH + (first + i) * _DAY, 10.0 + i, 11.0 + i, 9.0 + i, 10.5 + i, 1_000 + i)
        for i in range(count)
    ]


def _age(root: Path) -> None:
    """Backdate every series file past ``_RACY_WRITE_GUARD_SECONDS``.

    Both cache tiers refuse to publish a file whose mtime is within a couple of seconds of "now" —
    the guard against a same-granularity rewrite being served stale. A test that records and reads
    within the same instant would therefore exercise only the full-verify path and prove nothing
    about the durable tier, so these tests age the store first, exactly as any real store is aged by
    the time between one operator run and the next."""
    old = 1_600_000_000
    for path in root.glob("*.json"):
        os.utime(path, (old, old))


@pytest.fixture
def store_with_cache(tmp_path: Path) -> tuple[BarStore, str]:
    db = str(tmp_path / "verify.db")
    store = BarStore(tmp_path / "bars", verify_cache_db_path=db)
    for symbol in ("AAPL", "MSFT"):
        for timeframe in ("1d", "1h"):
            store.record(
                symbol=symbol,
                timeframe=timeframe,
                window_start_utc="2025-06-01T00:00:00Z",
                window_end_utc="2025-06-10T00:00:00Z",
                feed="test",
                bars=_bars(symbol, timeframe, 5),
            )
    _age(store.root)
    _reset_verified_cache_for_tests()
    return store, db


def test_a_second_process_reads_the_same_bytes_without_re_verifying(store_with_cache) -> None:
    """The whole point: a cold process (empty in-process caches, warm DB) must serve exactly what a
    from-scratch verify serves."""
    store, db = store_with_cache
    warm_records, warm_errors = store.list(include_bars=False)

    _reset_verified_cache_for_tests()  # stands in for "a brand new process"
    cold = BarStore(store.root, verify_cache_db_path=db)
    cold_records, cold_errors = cold.list(include_bars=False)

    assert cold_records == warm_records
    assert cold_errors == warm_errors == []
    assert json.dumps(cold_records) == json.dumps(warm_records)  # key order too, not just equality


def test_the_merged_fold_is_identical_whether_or_not_the_cache_is_used(tmp_path: Path) -> None:
    uncached = BarStore(tmp_path / "bars")
    for count, first in ((5, 0), (5, 5)):
        uncached.record(
            symbol="AAPL", timeframe="1d",
            window_start_utc="2025-06-01T00:00:00Z", window_end_utc="2025-06-20T00:00:00Z",
            feed="test", bars=_bars("AAPL", "1d", count, first),
        )
    plain = uncached.merged_bars("AAPL", "1d")

    _age(uncached.root)
    _reset_verified_cache_for_tests()
    cached = BarStore(tmp_path / "bars", verify_cache_db_path=str(tmp_path / "verify.db"))
    assert cached.merged_bars("AAPL", "1d") == plain
    _reset_verified_cache_for_tests()
    assert cached.merged_bars("AAPL", "1d") == plain  # now served through the durable tier


def test_a_tampered_file_still_fails_loudly_across_a_restart(store_with_cache) -> None:
    """A remembered row is keyed on ``(size, mtime_ns)``; ordinary tampering changes at least one,
    so the file misses, re-verifies in full, and raises — never served from memory as healthy."""
    store, db = store_with_cache
    store.list(include_bars=False)  # populate the durable cache

    victim = sorted(store.root.glob("*.json"))[0]
    payload = json.loads(victim.read_text())
    payload["record"]["bars"][0]["close"] = 4242.0
    victim.write_text(json.dumps(payload))

    _reset_verified_cache_for_tests()
    cold = BarStore(store.root, verify_cache_db_path=db)
    records, errors = cold.list(include_bars=False)
    assert [e["file"] for e in errors] == [victim.name]
    assert len(records) == 3
    with pytest.raises(BarSeriesIntegrityError):
        cold.get(victim.stem)


def test_deleting_the_cache_loses_nothing(store_with_cache) -> None:
    store, db = store_with_cache
    expected, _ = store.list(include_bars=False)

    Path(db).unlink()
    for suffix in ("-wal", "-shm"):
        Path(db + suffix).unlink(missing_ok=True)
    _reset_verified_cache_for_tests()

    rebuilt = BarStore(store.root, verify_cache_db_path=db)
    assert rebuilt.list(include_bars=False)[0] == expected
    assert Path(db).exists()  # and it repopulated itself on the way past


def test_the_cache_holds_metadata_only_never_candles(store_with_cache) -> None:
    """The 439MB-of-rows-never-cached discipline ``dataset_index.py`` documents: this DB must stay
    small and rebuildable, so a series' candles must never reach it."""
    store, db = store_with_cache
    store.list(include_bars=False)

    conn = sqlite3.connect(db)
    stored = [json.loads(row[0]) for row in conn.execute("SELECT meta_json FROM bar_verify_cache")]
    conn.close()
    assert stored, "the cache never populated"
    for meta in stored:
        assert "bars" not in meta
        assert {"id", "symbol", "timeframe", "checksum", "bar_count"} <= set(meta)


def test_a_store_without_a_cache_path_touches_no_database(tmp_path: Path) -> None:
    """Opt-in, exactly like ``DatasetStore``'s durable index — a bare ``BarStore(root)`` keeps its
    from-scratch verification and writes nothing beside the bar directory."""
    store = BarStore(tmp_path / "bars")
    store.record(
        symbol="AAPL", timeframe="1d",
        window_start_utc="2025-06-01T00:00:00Z", window_end_utc="2025-06-10T00:00:00Z",
        feed="test", bars=_bars("AAPL", "1d", 3),
    )
    store.list(include_bars=False)
    assert list(tmp_path.glob("*.db")) == []


def test_an_unopenable_cache_degrades_to_full_verification(tmp_path: Path) -> None:
    """A derived cache that cannot be opened is a missing optimisation, never a failed read."""
    store = BarStore(tmp_path / "bars", verify_cache_db_path=str(tmp_path / "bars"))  # a directory
    store.record(
        symbol="AAPL", timeframe="1d",
        window_start_utc="2025-06-01T00:00:00Z", window_end_utc="2025-06-10T00:00:00Z",
        feed="test", bars=_bars("AAPL", "1d", 3),
    )
    records, errors = store.list(include_bars=False)
    assert len(records) == 1 and errors == []


def test_lookup_is_an_exact_stat_match(tmp_path: Path) -> None:
    cache = BarVerifyCache(str(tmp_path / "verify.db"))
    cache.insert("/x/a.json", 100, 500, {"id": "a"})
    assert cache.lookup("/x/a.json", 100, 500) == {"id": "a"}
    assert cache.lookup("/x/a.json", 101, 500) is None
    assert cache.lookup("/x/a.json", 100, 501) is None
    assert cache.lookup("/x/b.json", 100, 500) is None
    assert cache.lookup_all() == {"/x/a.json": (100, 500, '{"id": "a"}')}


def test_insert_replaces_a_superseded_row(tmp_path: Path) -> None:
    cache = BarVerifyCache(str(tmp_path / "verify.db"))
    cache.insert("/x/a.json", 100, 500, {"id": "a"})
    cache.insert("/x/a.json", 120, 900, {"id": "a", "bar_count": 7})
    assert cache.lookup("/x/a.json", 100, 500) is None
    assert cache.lookup("/x/a.json", 120, 900) == {"id": "a", "bar_count": 7}
    assert len(cache.lookup_all()) == 1
