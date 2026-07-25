"""``desk_coverage.py`` (Era B "The Desk", J-02) — the coverage-read module's own contract: the
pinned timeframe set, honest-empty pre-universe, the per-member truth-table, freshness exactness,
and the index-only latency guard (T-4). Direct construction (no FastAPI/TestClient — the
``tests/test_bar_index.py``/``tests/test_desk_universe.py`` precedent); the route wiring is
covered in ``tests/test_desk_topup_compute.py`` alongside the top-up routes.
"""

from __future__ import annotations

from app.config import CONFIG
from app.providers.adapters.base import RawBar
from app.research.bar_index import BarIndex
from app.research.bars import BarStore
from app.research.desk_coverage import DESK_TOPUP_TIMEFRAMES, get_desk_coverage
from app.research.desk_universe import UniverseStore
from app.research.levels import PRIOR_PERIOD_TIMEFRAMES

FIVE_MEMBERS = ["AAA", "BBB", "CCC", "DDD", "EEE"]
COVERED = ["AAA", "BBB"]
START, END = "2026-06-01T00:00:00Z", "2026-06-04T00:00:00Z"
_BASE_EPOCH = 1780358400.0  # 2026-06-01T00:00:00Z


def _register_universe(tmp_path, members: list[str]) -> UniverseStore:
    store = UniverseStore(tmp_path / "universe")
    store.record(
        members=sorted(members),
        raw_members={m: m for m in members},
        source_url="https://example.invalid/constituents",
        min_members=1,
        max_members=999,
    )
    return store


def _bar(symbol: str, timeframe: str, epoch: float) -> RawBar:
    return RawBar(symbol, timeframe, epoch, 1.0, 1.5, 0.5, 1.2, 100)


def _record_series(
    bar_store: BarStore,
    index: BarIndex,
    symbol: str,
    timeframe: str,
    start: str,
    end: str,
    epoch_base: float,
) -> dict:
    bars = [_bar(symbol, timeframe, epoch_base), _bar(symbol, timeframe, epoch_base + 86400.0)]
    meta = bar_store.record(
        symbol=symbol, timeframe=timeframe, window_start_utc=start, window_end_utc=end,
        feed="yahoo", bars=bars,
    )
    index.insert(meta)
    return meta


# --- the pinned timeframe set (re-verified, not re-derived) ------------------------------------


def test_pinned_timeframe_set_matches_the_verified_live_derivation():
    """The desk top-up's pinned set is a plain structural constant, re-verified against the live
    tree (goal-desk-iter-2 NOTES) — never re-derived per iteration. Excludes 5m/1m (the desk-era's
    own explicit acceptance text); 1d/1w are inside the PRIOR_PERIOD_TIMEFRAMES long-term bucket
    (minus 1mo, which the Yahoo adapter does not serve at all)."""
    assert DESK_TOPUP_TIMEFRAMES == ("1h", "4h", "1d", "1w")
    assert set(DESK_TOPUP_TIMEFRAMES) <= set(CONFIG.bar_timeframes)
    assert set(DESK_TOPUP_TIMEFRAMES) & {"5m", "1m"} == set()
    assert {"1d", "1w"} <= set(PRIOR_PERIOD_TIMEFRAMES)


# --- honest empty (TC-1) ------------------------------------------------------------------------


def test_no_universe_snapshot_is_an_honest_empty_payload(tmp_path):
    universe_store = UniverseStore(tmp_path / "universe")
    index = BarIndex(str(tmp_path / "index.db"))

    coverage = get_desk_coverage(universe_store, index)

    assert coverage == {
        "universe_snapshot_id": None,
        "timeframes": list(DESK_TOPUP_TIMEFRAMES),
        "members": [],
    }


def test_universe_with_no_bars_at_all_reports_has_bars_false_for_every_member_and_timeframe(tmp_path):
    """TC-2: an empty bar store — every member reports ``has_bars == False`` on all four pinned
    timeframes, asserted per-member (never a bulk/aggregate assertion)."""
    universe_store = _register_universe(tmp_path, FIVE_MEMBERS)
    index = BarIndex(str(tmp_path / "index.db"))

    coverage = get_desk_coverage(universe_store, index)

    assert coverage["universe_snapshot_id"] is not None
    by_symbol = {m["symbol"]: m for m in coverage["members"]}
    assert set(by_symbol) == set(FIVE_MEMBERS)
    for symbol in FIVE_MEMBERS:
        for timeframe in DESK_TOPUP_TIMEFRAMES:
            entry = by_symbol[symbol]["per_timeframe"][timeframe]
            assert entry == {"has_bars": False, "latest_window_end_utc": None}, (symbol, timeframe)


# --- per-member truth-table (TC-3) ---------------------------------------------------------------


def test_truth_table_exactly_the_covered_members_report_has_bars_true_on_all_four_timeframes(tmp_path):
    universe_store = _register_universe(tmp_path, FIVE_MEMBERS)
    bar_store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    for symbol in COVERED:
        for timeframe in DESK_TOPUP_TIMEFRAMES:
            _record_series(bar_store, index, symbol, timeframe, START, END, _BASE_EPOCH)

    coverage = get_desk_coverage(universe_store, index)
    by_symbol = {m["symbol"]: m for m in coverage["members"]}

    for symbol in COVERED:
        for timeframe in DESK_TOPUP_TIMEFRAMES:
            assert by_symbol[symbol]["per_timeframe"][timeframe]["has_bars"] is True, (symbol, timeframe)
    for symbol in set(FIVE_MEMBERS) - set(COVERED):
        for timeframe in DESK_TOPUP_TIMEFRAMES:
            entry = by_symbol[symbol]["per_timeframe"][timeframe]
            assert entry == {"has_bars": False, "latest_window_end_utc": None}, (symbol, timeframe)


# --- freshness exactness (TC-4) -------------------------------------------------------------------


def test_latest_window_end_utc_matches_the_exact_recorded_bar_index_value(tmp_path):
    universe_store = _register_universe(tmp_path, FIVE_MEMBERS)
    bar_store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    _record_series(bar_store, index, "AAA", "1d", START, END, _BASE_EPOCH)

    coverage = get_desk_coverage(universe_store, index)
    by_symbol = {m["symbol"]: m for m in coverage["members"]}

    assert by_symbol["AAA"]["per_timeframe"]["1d"]["latest_window_end_utc"] == END


def test_latest_window_end_utc_is_the_max_across_multiple_recorded_windows(tmp_path):
    """A symbol recorded twice at the SAME timeframe (e.g. an earlier top-up, then a later one)
    reports the MOST RECENT window_end_utc, never the first or an arbitrary one."""
    universe_store = _register_universe(tmp_path, ["AAA"])
    bar_store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    _record_series(bar_store, index, "AAA", "1d", START, END, _BASE_EPOCH)
    later_start, later_end = "2026-06-05T00:00:00Z", "2026-06-08T00:00:00Z"
    _record_series(bar_store, index, "AAA", "1d", later_start, later_end, _BASE_EPOCH + 4 * 86400.0)

    coverage = get_desk_coverage(universe_store, index)
    by_symbol = {m["symbol"]: m for m in coverage["members"]}

    assert by_symbol["AAA"]["per_timeframe"]["1d"]["latest_window_end_utc"] == later_end


# --- index-only latency (TC-5) --------------------------------------------------------------------


def test_coverage_issues_zero_bar_store_calls(tmp_path, monkeypatch):
    """T-4: coverage is read from ``bar_index`` only — ``get_desk_coverage`` takes no ``BarStore``
    reference at all, but this proves it directly (a call-counting guard) rather than relying on
    signature inspection alone, so a future regression that reaches for ``BarStore`` as a fallback
    is caught."""
    universe_store = _register_universe(tmp_path, FIVE_MEMBERS)
    bar_store = BarStore(tmp_path / "bars")
    index = BarIndex(str(tmp_path / "index.db"))
    for symbol in COVERED:
        for timeframe in DESK_TOPUP_TIMEFRAMES:
            _record_series(bar_store, index, symbol, timeframe, START, END, _BASE_EPOCH)

    calls: list[str] = []
    original_list = BarStore.list
    original_get = BarStore.get

    def _tracked_list(self, *args, **kwargs):
        calls.append("list")
        return original_list(self, *args, **kwargs)

    def _tracked_get(self, *args, **kwargs):
        calls.append("get")
        return original_get(self, *args, **kwargs)

    monkeypatch.setattr(BarStore, "list", _tracked_list)
    monkeypatch.setattr(BarStore, "get", _tracked_get)

    get_desk_coverage(universe_store, index)

    assert calls == []


def test_bar_index_coverage_accessor_is_additive_and_index_only(tmp_path):
    """``BarIndex.coverage()`` (the new accessor this iteration adds) answers directly from SQLite
    — a fresh, empty index reports ``(False, None)`` for any pair, never an error."""
    index = BarIndex(str(tmp_path / "index.db"))
    assert index.coverage("ZZZZ", "1d") == (False, None)
