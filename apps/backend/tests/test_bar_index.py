"""``BarIndex`` (era-5 capability 3, J-03) — store-level discipline.

Mirrors ``tests/test_bars.py``'s directness: this module tests ``BarIndex`` on its own (no
FastAPI/TestClient), proving the exact-key lookup, additive insert-on-record, the symbol/timeframe
filter, and the ``reindex()`` rebuild-from-``BarStore.list()`` contract (including its "healthy
records only" and "self-heals after the DB file is lost" guarantees). The route-level store-first
coordinator + the ``?symbol=&timeframe=`` filter's wiring through the API are covered separately in
``tests/test_bars_api.py``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from app.providers.adapters.base import RawBar
from app.research.bar_index import BarIndex, BarIndexHit
from app.research.bars import BarStore

WINDOW_START, WINDOW_END = "2026-06-01T00:00:00Z", "2026-06-04T00:00:00Z"


def _bar(symbol: str, timeframe: str, epoch: float, o: float, h: float, l: float, c: float, v: int) -> RawBar:
    return RawBar(symbol, timeframe, epoch, o, h, l, c, v)


def _small_series(symbol: str = "PG") -> list[RawBar]:
    base = datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp()
    day = 86400.0
    return [
        _bar(symbol, "1d", base + 0 * day, 148.0, 149.5, 147.5, 149.0, 1_000_000),
        _bar(symbol, "1d", base + 1 * day, 149.0, 150.0, 148.5, 149.8, 1_100_000),
        _bar(symbol, "1d", base + 2 * day, 149.8, 151.0, 149.2, 150.5, 1_050_000),
    ]


def _record(
    store: BarStore,
    symbol: str = "PG",
    timeframe: str = "1d",
    start: str = WINDOW_START,
    end: str = WINDOW_END,
    feed: str = "yahoo",
) -> dict:
    return store.record(
        symbol=symbol, timeframe=timeframe, window_start_utc=start, window_end_utc=end,
        feed=feed, bars=_small_series(symbol),
    )


# --- lookup / insert: the exact-key contract -------------------------------------------------


def test_insert_then_lookup_is_a_hit(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    meta = _record(store)

    index.insert(meta)
    hit = index.lookup("PG", "1d", WINDOW_START, WINDOW_END)

    assert hit == BarIndexHit(series_id=meta["id"], checksum=meta["checksum"], bar_count=3)


def test_lookup_before_any_insert_is_a_miss(tmp_path):
    index = BarIndex(str(tmp_path / "index.db"))
    assert index.lookup("PG", "1d", WINDOW_START, WINDOW_END) is None


def test_lookup_on_a_different_symbol_timeframe_or_window_is_a_miss(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    meta = _record(store)
    index.insert(meta)

    assert index.lookup("F", "1d", WINDOW_START, WINDOW_END) is None
    assert index.lookup("PG", "1h", WINDOW_START, WINDOW_END) is None
    assert index.lookup("PG", "1d", "2026-06-02T00:00:00Z", WINDOW_END) is None
    assert index.lookup("PG", "1d", WINDOW_START, "2026-06-05T00:00:00Z") is None


def test_lookup_matches_the_raw_iso_string_not_the_parsed_epoch(tmp_path):
    """Two window strings that denote the identical UTC instant but are textually different (a
    trailing ``.000000`` here, ``+00:00`` instead of ``Z`` there) must NOT collide — the key is the
    exact stored string, never a parsed/normalized epoch (the plan's explicit requirement)."""
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    meta = _record(store, start="2026-06-01T00:00:00Z", end="2026-06-04T00:00:00Z")
    index.insert(meta)

    assert index.lookup("PG", "1d", "2026-06-01T00:00:00Z", "2026-06-04T00:00:00Z") is not None
    assert index.lookup("PG", "1d", "2026-06-01T00:00:00.000000Z", "2026-06-04T00:00:00Z") is None
    assert index.lookup("PG", "1d", "2026-06-01T00:00:00+00:00", "2026-06-04T00:00:00Z") is None


def test_insert_is_idempotent_and_overwrites_the_same_key(tmp_path):
    """The self-heal shape: re-inserting under the IDENTICAL key (e.g. after a stale hit fell
    through to a real re-fetch) overwrites rather than duplicates."""
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    first = _record(store)
    index.insert(first)

    extra = _bar("PG", "1d", datetime(2026, 6, 4, tzinfo=timezone.utc).timestamp(), 150.5, 151.0, 150.0, 150.8, 900_000)
    second = store.record(
        symbol="PG", timeframe="1d", window_start_utc=WINDOW_START, window_end_utc=WINDOW_END,
        feed="yahoo", bars=_small_series("PG") + [extra],
    )
    index.insert(second)

    hit = index.lookup("PG", "1d", WINDOW_START, WINDOW_END)
    assert hit.series_id == second["id"] != first["id"]
    assert hit.bar_count == 4
    assert len(index.list()) == 1  # overwritten, not duplicated


# --- list: the symbol/timeframe filter --------------------------------------------------------


def test_list_filters_independently_by_symbol_and_timeframe(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    pg_daily = _record(store, symbol="PG", timeframe="1d")
    pg_hourly = _record(
        store, symbol="PG", timeframe="1h", start="2026-06-05T00:00:00Z", end="2026-06-06T00:00:00Z"
    )
    f_daily = _record(
        store, symbol="F", timeframe="1d", start="2026-06-07T00:00:00Z", end="2026-06-08T00:00:00Z"
    )
    for meta in (pg_daily, pg_hourly, f_daily):
        index.insert(meta)

    assert {h.series_id for h in index.list()} == {pg_daily["id"], pg_hourly["id"], f_daily["id"]}
    assert {h.series_id for h in index.list(symbol="PG")} == {pg_daily["id"], pg_hourly["id"]}
    assert {h.series_id for h in index.list(timeframe="1d")} == {pg_daily["id"], f_daily["id"]}
    assert [h.series_id for h in index.list(symbol="PG", timeframe="1d")] == [pg_daily["id"]]
    assert index.list(symbol="ZZZZ") == []


# --- reindex: rebuild from BarStore.list(), healthy records only ------------------------------


def test_reindex_populates_from_bar_store_list(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    pg = _record(store, symbol="PG", timeframe="1d")
    f = _record(
        store, symbol="F", timeframe="1h", start="2026-06-05T00:00:00Z", end="2026-06-06T00:00:00Z"
    )

    index.reindex(store)

    assert index.lookup("PG", "1d", WINDOW_START, WINDOW_END) == BarIndexHit(pg["id"], pg["checksum"], 3)
    assert index.lookup("F", "1h", "2026-06-05T00:00:00Z", "2026-06-06T00:00:00Z") == BarIndexHit(
        f["id"], f["checksum"], 3
    )


def test_reindex_skips_corrupt_files_reported_in_bar_store_errors(tmp_path):
    """``reindex()`` rebuilds ONLY from ``BarStore.list()``'s healthy ``records`` — anything in
    that call's ``errors`` (a corrupt file) is not legitimately indexable data and must never be
    fabricated into a lookup."""
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    _record(store, symbol="PG", timeframe="1d")
    corrupt = _record(
        store, symbol="F", timeframe="1h", start="2026-06-05T00:00:00Z", end="2026-06-06T00:00:00Z"
    )
    corrupt_path = tmp_path / "bars" / f"{corrupt['id']}.json"
    data = json.loads(corrupt_path.read_text())
    data["record"]["bars"][0]["close"] += 1.0
    corrupt_path.write_text(json.dumps(data))

    _records, errors = store.list()
    assert len(errors) == 1  # sanity: the corrupt file is genuinely reported as an error

    index.reindex(store)

    assert index.lookup("PG", "1d", WINDOW_START, WINDOW_END) is not None
    assert index.lookup("F", "1h", "2026-06-05T00:00:00Z", "2026-06-06T00:00:00Z") is None
    assert len(index.list()) == 1


def test_reindex_drops_stale_entries_not_reproduced_by_the_current_store(tmp_path):
    """``reindex()`` is DROP + repopulate, not an additive merge — a stale index row for a series
    the store no longer reports (e.g. hand-deleted) must not survive a reindex."""
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    index.insert(
        {
            "symbol": "GHOST", "timeframe": "1d", "window_start_utc": WINDOW_START,
            "window_end_utc": WINDOW_END, "id": "ghost-id", "checksum": "deadbeef", "bar_count": 1,
        }
    )
    assert index.lookup("GHOST", "1d", WINDOW_START, WINDOW_END) is not None

    index.reindex(store)  # the store is empty -- reindex must drop the ghost entry too

    assert index.lookup("GHOST", "1d", WINDOW_START, WINDOW_END) is None
    assert index.list() == []


def test_reindex_after_deleting_the_db_file_reproduces_identical_lookups(tmp_path):
    """The DoD's literal scenario: delete the index DB file entirely (models both a MISSING and,
    since a truly corrupt SQLite file must be removed before a fresh connection can reuse that
    path, a CORRUPT DB -- the same recovery mechanism), construct a brand-new ``BarIndex`` at the
    identical path, and confirm ``reindex()`` reproduces identical lookups -- nothing lost,
    nothing fabricated."""
    store = BarStore(tmp_path / "bars")
    db_path = tmp_path / "index.db"
    index = BarIndex(str(db_path))
    _record(store, symbol="PG", timeframe="1d")
    _record(store, symbol="F", timeframe="1h", start="2026-06-05T00:00:00Z", end="2026-06-06T00:00:00Z")
    index.reindex(store)

    keys = [
        ("PG", "1d", WINDOW_START, WINDOW_END),
        ("F", "1h", "2026-06-05T00:00:00Z", "2026-06-06T00:00:00Z"),
    ]
    before = {key: index.lookup(*key) for key in keys}
    assert all(v is not None for v in before.values())

    db_path.unlink()  # simulate a missing/corrupted DB file

    rebuilt = BarIndex(str(db_path))
    assert rebuilt.list() == []  # a fresh DB starts empty -- nothing survives the loss
    rebuilt.reindex(store)

    after = {key: rebuilt.lookup(*key) for key in keys}
    assert after == before
