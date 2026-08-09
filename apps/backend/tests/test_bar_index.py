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
    hit = index.lookup("PG", "1d", WINDOW_START, WINDOW_END, "yahoo")

    assert hit == BarIndexHit(series_id=meta["id"], checksum=meta["checksum"], bar_count=3)


def test_lookup_before_any_insert_is_a_miss(tmp_path):
    index = BarIndex(str(tmp_path / "index.db"))
    assert index.lookup("PG", "1d", WINDOW_START, WINDOW_END, "yahoo") is None


def test_lookup_on_a_different_symbol_timeframe_or_window_is_a_miss(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    meta = _record(store)
    index.insert(meta)

    assert index.lookup("F", "1d", WINDOW_START, WINDOW_END, "yahoo") is None
    assert index.lookup("PG", "1h", WINDOW_START, WINDOW_END, "yahoo") is None
    assert index.lookup("PG", "1d", "2026-06-02T00:00:00Z", WINDOW_END, "yahoo") is None
    assert index.lookup("PG", "1d", WINDOW_START, "2026-06-05T00:00:00Z", "yahoo") is None


def test_lookup_matches_the_raw_iso_string_not_the_parsed_epoch(tmp_path):
    """Two window strings that denote the identical UTC instant but are textually different (a
    trailing ``.000000`` here, ``+00:00`` instead of ``Z`` there) must NOT collide — the key is the
    exact stored string, never a parsed/normalized epoch (the plan's explicit requirement)."""
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    meta = _record(store, start="2026-06-01T00:00:00Z", end="2026-06-04T00:00:00Z")
    index.insert(meta)

    assert index.lookup("PG", "1d", "2026-06-01T00:00:00Z", "2026-06-04T00:00:00Z", "yahoo") is not None
    assert index.lookup("PG", "1d", "2026-06-01T00:00:00.000000Z", "2026-06-04T00:00:00Z", "yahoo") is None
    assert index.lookup("PG", "1d", "2026-06-01T00:00:00+00:00", "2026-06-04T00:00:00Z", "yahoo") is None


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

    hit = index.lookup("PG", "1d", WINDOW_START, WINDOW_END, "yahoo")
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

    assert index.lookup("PG", "1d", WINDOW_START, WINDOW_END, "yahoo") == BarIndexHit(pg["id"], pg["checksum"], 3)
    assert index.lookup("F", "1h", "2026-06-05T00:00:00Z", "2026-06-06T00:00:00Z", "yahoo") == BarIndexHit(
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

    assert index.lookup("PG", "1d", WINDOW_START, WINDOW_END, "yahoo") is not None
    assert index.lookup("F", "1h", "2026-06-05T00:00:00Z", "2026-06-06T00:00:00Z", "yahoo") is None
    assert len(index.list()) == 1


def test_reindex_drops_stale_entries_not_reproduced_by_the_current_store(tmp_path):
    """``reindex()`` is DROP + repopulate, not an additive merge — a stale index row for a series
    the store no longer reports (e.g. hand-deleted) must not survive a reindex."""
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    index.insert(
        {
            "symbol": "GHOST", "timeframe": "1d", "window_start_utc": WINDOW_START,
            "window_end_utc": WINDOW_END, "feed": "yahoo", "id": "ghost-id",
            "checksum": "deadbeef", "bar_count": 1,
        }
    )
    assert index.lookup("GHOST", "1d", WINDOW_START, WINDOW_END, "yahoo") is not None

    index.reindex(store)  # the store is empty -- reindex must drop the ghost entry too

    assert index.lookup("GHOST", "1d", WINDOW_START, WINDOW_END, "yahoo") is None
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
        ("PG", "1d", WINDOW_START, WINDOW_END, "yahoo"),
        ("F", "1h", "2026-06-05T00:00:00Z", "2026-06-06T00:00:00Z", "yahoo"),
    ]
    before = {key: index.lookup(*key) for key in keys}
    assert all(v is not None for v in before.values())

    db_path.unlink()  # simulate a missing/corrupted DB file

    rebuilt = BarIndex(str(db_path))
    assert rebuilt.list() == []  # a fresh DB starts empty -- nothing survives the loss
    rebuilt.reindex(store)

    after = {key: rebuilt.lookup(*key) for key in keys}
    assert after == before


# --- coverage(): Era B "The Desk" J-02, additive ------------------------------------------------
# Appended this iteration. Every assertion ABOVE this line is byte-unmodified from era-5 J-03 --
# proving the extension took the "new accessor" path (goal-desk-iter-2 spec / plan), never a new
# BarIndexHit field (which would have broken the positional/keyword BarIndexHit(...) construction
# calls used throughout this file, e.g. line 62/153-156 above).


def test_bar_index_hit_still_has_exactly_its_original_three_fields():
    """A regression that added a field to ``BarIndexHit`` would break the equality assertions
    above (``hit == BarIndexHit(series_id=..., checksum=..., bar_count=3)``,
    ``BarIndexHit(pg["id"], pg["checksum"], 3)``) -- this pins the dataclass shape directly so
    such a regression fails HERE, with a clear message, rather than as a confusing equality
    mismatch elsewhere."""
    import dataclasses

    assert [f.name for f in dataclasses.fields(BarIndexHit)] == ["series_id", "checksum", "bar_count"]


def test_coverage_on_an_empty_index_is_false_and_none(tmp_path):
    index = BarIndex(str(tmp_path / "index.db"))
    assert index.coverage("PG", "1d") == (False, None)


def test_coverage_after_insert_is_true_and_the_recorded_window_end(tmp_path):
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    meta = _record(store)
    index.insert(meta)

    assert index.coverage("PG", "1d") == (True, WINDOW_END)
    assert index.coverage("PG", "1h") == (False, None)  # a different timeframe is unaffected
    assert index.coverage("F", "1d") == (False, None)  # a different symbol is unaffected


def test_coverage_reports_the_max_window_end_across_multiple_recordings(tmp_path):
    """A symbol/timeframe recorded twice (e.g. an earlier top-up, then a later one) reports the
    MOST RECENT ``window_end_utc`` -- never the first, never an arbitrary row."""
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    first = _record(store, start=WINDOW_START, end=WINDOW_END)
    index.insert(first)

    later_start, later_end = "2026-06-05T00:00:00Z", "2026-06-08T00:00:00Z"
    extra = _bar(
        "PG", "1d", datetime(2026, 6, 5, tzinfo=timezone.utc).timestamp(), 151.0, 152.0, 150.5, 151.5, 800_000
    )
    second = store.record(
        symbol="PG", timeframe="1d", window_start_utc=later_start, window_end_utc=later_end,
        feed="yahoo", bars=_small_series("PG") + [extra],
    )
    index.insert(second)

    assert index.coverage("PG", "1d") == (True, later_end)


def test_coverage_reads_the_raw_iso_string_not_a_parsed_epoch(tmp_path):
    """Mirrors ``test_lookup_matches_the_raw_iso_string_not_the_parsed_epoch`` above: ``coverage``
    reports whatever ``window_end_utc`` string was actually stored, verbatim -- never reformatted
    or re-derived from an epoch."""
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    meta = _record(store, start="2026-06-01T00:00:00Z", end="2026-06-04T00:00:00.000000Z")
    index.insert(meta)

    assert index.coverage("PG", "1d") == (True, "2026-06-04T00:00:00.000000Z")


# --- covers_date: the date-scoped coverage question ---------------------------------------------


def test_covers_date_on_an_empty_index_is_false(tmp_path):
    index = BarIndex(str(tmp_path / "index.db"))
    assert index.covers_date("PG", "1d", "2026-06-02") is False


def test_covers_date_is_inclusive_of_both_window_bounds(tmp_path):
    """A window is recorded as the days it was ASKED for, so its own first and last day are both
    covered -- and a day outside it is not."""
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    index.insert(_record(store))  # 2026-06-01T00:00:00Z .. 2026-06-04T00:00:00Z

    assert index.covers_date("PG", "1d", "2026-06-01") is True  # the start day
    assert index.covers_date("PG", "1d", "2026-06-02") is True  # inside
    assert index.covers_date("PG", "1d", "2026-06-04") is True  # the end day
    assert index.covers_date("PG", "1d", "2026-05-31") is False  # the day before
    assert index.covers_date("PG", "1d", "2026-06-05") is False  # the day after
    assert index.covers_date("PG", "1h", "2026-06-02") is False  # another timeframe
    assert index.covers_date("F", "1d", "2026-06-02") is False  # another symbol


def test_covers_date_compares_calendar_days_across_both_stored_window_shapes(tmp_path):
    """The live index holds BOTH window-string shapes the recording path has ever written: a bare
    ``2025-01-01`` (the Alpaca-recorded fine series) and a full ``2026-08-05T00:00:00Z``. A raw
    string comparison ranks ``'2026-06-04' > '2026-06-04T00:00:00Z'``, so the end day of a
    timestamped window would read as UNCOVERED. Truncating both sides to the calendar day is what
    makes the two shapes answer the same question."""
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    index.insert(_record(store, symbol="PG", start="2026-06-01", end="2026-06-04"))
    index.insert(_record(store, symbol="F", start="2026-06-01T00:00:00Z", end="2026-06-04T00:00:00Z"))

    for symbol in ("PG", "F"):
        assert index.covers_date(symbol, "1d", "2026-06-01") is True
        assert index.covers_date(symbol, "1d", "2026-06-04") is True
        assert index.covers_date(symbol, "1d", "2026-06-05") is False


def test_covers_date_is_true_when_any_one_recording_covers_the_day(tmp_path):
    """Two recordings for one pair (an earlier top-up, then a later one) leave two rows; the day
    is covered when ANY of them contains it -- the count-based query, never the max window only."""
    store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    index.insert(_record(store, start="2026-06-01T00:00:00Z", end="2026-06-04T00:00:00Z"))
    # A genuinely different series -- `BarStore.record` refuses identical CONTENT outright, so a
    # second recording of one pair must carry its own bars (the max-window-end test's precedent).
    july = _bar(
        "PG", "1d", datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp(), 151.0, 152.0, 150.5, 151.5, 800_000
    )
    index.insert(
        store.record(
            symbol="PG", timeframe="1d", window_start_utc="2026-07-01T00:00:00Z",
            window_end_utc="2026-07-04T00:00:00Z", feed="yahoo", bars=[july],
        )
    )

    assert index.covers_date("PG", "1d", "2026-06-02") is True  # only the FIRST window holds it
    assert index.covers_date("PG", "1d", "2026-07-02") is True  # only the SECOND does
    assert index.covers_date("PG", "1d", "2026-06-20") is False  # the gap between them
