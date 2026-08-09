"""The two directory-generation memos in ``bars.py`` never make a bad file look good.

Reading one merged pair used to re-list and re-stat the WHOLE store — 5,104 files per read, 1.1M
syscalls across a single top-up slice. ``_DIR_LISTING_CACHE`` (which files exist) and
``_PAIR_SCAN_CACHE`` (which pair each belongs to) both answer from a memo keyed on the store
directory's own ``(mtime_ns, ctime_ns)``.

That key notices files being ADDED or REMOVED. It deliberately does NOT notice a file being edited
in place — editing a file leaves its directory's mtime untouched. So the load-bearing question is
whether integrity still holds while a memo is warm, and the answer must come from the layer below:
every file the fold actually reads goes through ``_cached_load``, which stats it and re-verifies in
full on any change. These tests pin exactly that, plus the add/remove cases the memo key does own."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.providers.adapters.base import RawBar
from app.research.bars import BarSeriesIntegrityError, BarStore

_BASE_EPOCH = 1_750_000_000.0
_DAY = 86_400.0


def _bars(symbol: str, timeframe: str, count: int, first: int = 0) -> list[RawBar]:
    return [
        RawBar(symbol, timeframe, _BASE_EPOCH + (first + i) * _DAY,
               10.0 + i, 11.0 + i, 9.0 + i, 10.5 + i, 100 + i)
        for i in range(count)
    ]


@pytest.fixture
def store(tmp_path: Path) -> BarStore:
    s = BarStore(tmp_path / "bars", verify_cache_db_path=str(tmp_path / "verify.db"))
    for symbol in ("AAPL", "MSFT"):
        s.record(symbol=symbol, timeframe="1d",
                 window_start_utc="2025-06-01T00:00:00Z", window_end_utc="2025-06-10T00:00:00Z",
                 feed="test", bars=_bars(symbol, "1d", 5))
    return s


def _edit_in_place(path: Path) -> None:
    payload = json.loads(path.read_text())
    payload["record"]["bars"][0]["close"] = 4242.0
    path.write_text(json.dumps(payload))


def test_an_in_place_edit_is_caught_even_with_both_memos_warm(store: BarStore) -> None:
    """The case the memo key cannot see, and therefore the one that matters."""
    assert len(store.merged_bars("AAPL", "1d")) == 5  # warms both memos

    victim = next(p for p in store.root.glob("*.json") if "AAPL" in p.read_text())
    directory_before = store.root.stat().st_mtime_ns
    _edit_in_place(victim)
    assert store.root.stat().st_mtime_ns == directory_before, (
        "an in-place edit must NOT move the directory mtime — otherwise this test proves nothing"
    )

    rows, _before, _after, meta = store.merged_candles("AAPL", "1d", limit=500)
    assert rows == []  # the tampered recording contributes nothing
    assert [e["file"] for e in meta["integrity_errors"]] == [victim.name]
    assert store.merged_bars("AAPL", "1d") == []
    with pytest.raises(BarSeriesIntegrityError):
        store.get(victim.stem)

    records, errors = store.list(include_bars=False)
    assert [r["symbol"] for r in records] == ["MSFT"]
    assert [e["file"] for e in errors] == [victim.name]


def test_an_unrelated_pair_is_unaffected_by_another_pairs_corruption(store: BarStore) -> None:
    store.merged_bars("AAPL", "1d")
    store.merged_bars("MSFT", "1d")
    victim = next(p for p in store.root.glob("*.json") if "AAPL" in p.read_text())
    _edit_in_place(victim)
    assert len(store.merged_bars("MSFT", "1d")) == 5  # still served, still healthy


def test_a_newly_recorded_series_is_visible_immediately(store: BarStore) -> None:
    """Adding a file moves the directory mtime, and ``record`` evicts both memos outright — a fresh
    recording must never be hidden behind a warm listing."""
    assert len(store.merged_bars("AAPL", "1d")) == 5
    store.record(symbol="AAPL", timeframe="1d",
                 window_start_utc="2025-06-10T00:00:00Z", window_end_utc="2025-06-20T00:00:00Z",
                 feed="test", bars=_bars("AAPL", "1d", 5, first=5))
    assert len(store.merged_bars("AAPL", "1d")) == 10
    assert len(store.list(include_bars=False)[0]) == 3


def test_a_series_recorded_by_another_process_is_visible(store: BarStore) -> None:
    """The memo must not require the write to have gone through THIS store instance — a screen
    worker or a second process writing into the same directory bumps its mtime, and that alone has
    to invalidate the listing."""
    assert len(store.merged_bars("AAPL", "1d")) == 5
    other = BarStore(store.root)  # a different instance, as another process would have
    other.record(symbol="AAPL", timeframe="1d",
                 window_start_utc="2025-06-10T00:00:00Z", window_end_utc="2025-06-20T00:00:00Z",
                 feed="test", bars=_bars("AAPL", "1d", 5, first=5))
    assert len(store.merged_bars("AAPL", "1d")) == 10


def test_a_removed_file_disappears_from_both_reads(store: BarStore) -> None:
    assert len(store.list(include_bars=False)[0]) == 2
    victim = next(p for p in store.root.glob("*.json") if "AAPL" in p.read_text())
    victim.unlink()
    assert store.merged_bars("AAPL", "1d") == []
    assert [r["symbol"] for r in store.list(include_bars=False)[0]] == ["MSFT"]
