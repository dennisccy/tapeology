"""``desk_playbook_features.py`` -- the Playbook's eight shared primitives (Era B2, J-01).

Coverage: RTH session slicing excludes pre/post-market bars on the same UTC date; opening_range's
1m basis, its 1m->5m honest degrade, and its null (neither basis) case; baselines' MBR/sessions/
slot-volume-median math, its thin-baseline case, and its zero-bars case; swing_pivots' parity with
``levels._swing_pivots``' strict-extreme rule (including the tie-is-not-a-pivot case); the maximal
qualifying consolidation_range window and its "nothing qualifies" case; vertical_move's move/close
gates and its require_volume clause; zone_touches' full-exit re-arm rule; market_context's
no-SPY-bars null case, its insufficient-lookback null case, and its computed-move case."""

from __future__ import annotations

import pytest

from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.desk_playbook_features import (
    baselines,
    consolidation_range,
    market_context,
    opening_range,
    rth_session_slice,
    side_sign,
    swing_pivots,
    vertical_move,
    zone_touches,
)
from app.research.levels import _swing_pivots as _levels_swing_pivots

# 2026-06-22T13:30:00Z == 09:30 ET that day (EDT, UTC-4) -- verified against
# test_desk_forward.py's own E_OPEN constant.
SESSION_DATE = "2026-06-22"
E_OPEN = 1782135000.0
_RTH_SECONDS = 6.5 * 3600.0  # 09:30 -> 16:00 ET


def _bar(symbol: str, timeframe: str, epoch: float, o: float, h: float, low: float, c: float, v: int = 1000) -> RawBar:
    return RawBar(symbol, timeframe, epoch, o, h, low, c, v)


def _plant(bar_store: BarStore, symbol: str, timeframe: str, bars: list[RawBar]) -> None:
    bar_store.record(
        symbol=symbol, timeframe=timeframe,
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-12-31T00:00:00Z",
        feed="test", bars=bars,
    )


@pytest.fixture
def bar_store(tmp_path):
    return BarStore(tmp_path / "bars")


# --- rth_session_slice ---------------------------------------------------------------------------


def test_rth_session_slice_excludes_pre_and_post_market_bars(bar_store):
    bars = [
        _bar("RTHX", "5m", E_OPEN - 1800.0, 99.0, 99.2, 98.8, 99.0),  # 09:00 ET -- pre-market
        _bar("RTHX", "5m", E_OPEN, 100.0, 101.0, 99.0, 100.5),  # 09:30 ET -- slot 0
        _bar("RTHX", "5m", E_OPEN + 300.0, 100.5, 101.5, 100.0, 101.0),  # 09:35 ET -- slot 1
        _bar("RTHX", "5m", E_OPEN + _RTH_SECONDS + 300.0, 101.0, 101.5, 100.5, 101.2),  # 16:05 ET
    ]
    _plant(bar_store, "RTHX", "5m", bars)
    result = rth_session_slice(bar_store.merged_bars("RTHX", "5m"), SESSION_DATE)
    assert [b.epoch for b in result] == [E_OPEN, E_OPEN + 300.0]


def test_rth_session_slice_on_a_winter_est_date_still_resolves_0930_correctly(bar_store):
    """DST correctness: January is EST (UTC-5), not the June fixtures' EDT (UTC-4) -- 09:30 ET on
    2026-01-15 is 14:30Z, not 13:30Z. A fixed-offset bug would silently include/exclude an hour."""
    winter_open = 1768487400.0  # 2026-01-15T14:30:00Z == 09:30 ET (EST)
    bars = [
        _bar("WNTR", "5m", winter_open - 300.0, 50.0, 50.2, 49.8, 50.0),  # 09:25 ET -- pre-market
        _bar("WNTR", "5m", winter_open, 50.0, 50.5, 49.5, 50.2),  # 09:30 ET -- slot 0
    ]
    _plant(bar_store, "WNTR", "5m", bars)
    result = rth_session_slice(bar_store.merged_bars("WNTR", "5m"), "2026-01-15")
    assert [b.epoch for b in result] == [winter_open]


def test_rth_session_slice_empty_series_is_empty(bar_store):
    assert rth_session_slice([], SESSION_DATE) == []


# --- opening_range ---------------------------------------------------------------------------------


def test_opening_range_1m_basis_uses_all_available_1m_bars_in_the_window(bar_store):
    bars_1m = [
        _bar("OR1M", "1m", E_OPEN + i * 60.0, 100.5, 101.0, 100.0, 100.5) for i in range(12)
    ]
    _plant(bar_store, "OR1M", "1m", bars_1m)
    result = opening_range(bar_store.merged_bars("OR1M", "1m"), [], SESSION_DATE, 15, 10)
    assert result == {"high": 101.0, "low": 100.0, "width": 1.0, "basis": "1m", "bars_used": 12}


def test_opening_range_degrades_to_5m_basis_below_the_1m_floor(bar_store):
    bars_1m = [_bar("OR5M", "1m", E_OPEN + i * 60.0, 100.5, 100.6, 100.4, 100.5) for i in range(4)]
    bars_5m = [
        _bar("OR5M", "5m", E_OPEN, 100.0, 100.8, 99.8, 100.2),
        _bar("OR5M", "5m", E_OPEN + 300.0, 100.2, 101.0, 100.0, 100.9),
        _bar("OR5M", "5m", E_OPEN + 600.0, 100.9, 100.9, 99.9, 100.4),
    ]
    _plant(bar_store, "OR5M", "1m", bars_1m)
    _plant(bar_store, "OR5M", "5m", bars_5m)
    result = opening_range(
        bar_store.merged_bars("OR5M", "1m"), bar_store.merged_bars("OR5M", "5m"),
        SESSION_DATE, 15, 10,
    )
    assert result["high"] == pytest.approx(101.0)
    assert result["low"] == pytest.approx(99.8)
    assert result["width"] == pytest.approx(1.2)
    assert result["basis"] == "5m"
    assert result["bars_used"] == 3


def test_opening_range_5m_fallback_never_builds_from_bars_outside_the_opening_window(bar_store):
    """A session whose 5m series is MISSING its 09:30 and 09:35 bars has no opening range -- the
    honest answer is the null (the caller's disclosed absence), never an "opening range" quietly
    built from the 09:40/09:45/09:50 bars and served as ``basis: "5m"`` like a genuine one.
    Positional ``session_5m[:3]`` slicing did exactly that; both bases read the same
    ``09:30 .. 09:45`` epoch window."""
    bars_5m = [
        _bar("ORGAP", "5m", E_OPEN + 600.0, 100.0, 100.4, 99.8, 100.2),  # 09:40 -- inside window
        _bar("ORGAP", "5m", E_OPEN + 900.0, 100.2, 100.6, 100.0, 100.5),  # 09:45 -- OUTSIDE
        _bar("ORGAP", "5m", E_OPEN + 1200.0, 100.5, 100.9, 100.3, 100.8),  # 09:50 -- OUTSIDE
        _bar("ORGAP", "5m", E_OPEN + 1500.0, 100.8, 101.2, 100.6, 101.0),
    ]
    _plant(bar_store, "ORGAP", "5m", bars_5m)
    assert opening_range([], bar_store.merged_bars("ORGAP", "5m"), SESSION_DATE, 15, 10) is None


def test_opening_range_null_when_neither_basis_is_available(bar_store):
    bars_1m = [_bar("ORNULL", "1m", E_OPEN + i * 60.0, 100.5, 100.6, 100.4, 100.5) for i in range(4)]
    bars_5m = [_bar("ORNULL", "5m", E_OPEN, 100.0, 100.8, 99.8, 100.2)]  # only 1 -- need >= 3
    _plant(bar_store, "ORNULL", "1m", bars_1m)
    _plant(bar_store, "ORNULL", "5m", bars_5m)
    result = opening_range(
        bar_store.merged_bars("ORNULL", "1m"), bar_store.merged_bars("ORNULL", "5m"),
        SESSION_DATE, 15, 10,
    )
    assert result is None


# --- baselines -------------------------------------------------------------------------------------

_PRIOR_DATES_12 = [f"2026-06-{d:02d}" for d in range(1, 13)]  # 12 dates, all < 2026-06-22


def _plant_prior_sessions(bar_store, symbol, dates, *, flat=False, volume=1000):
    bars = []
    for day_offset, day in enumerate(dates):
        day_open = E_OPEN - (22 - int(day[-2:])) * 86_400.0
        for slot in range(4):
            if flat:
                o = h = low = c = 100.0
            else:
                o, h, low, c = 100.0, 100.5, 99.5, 100.0
            bars.append(_bar(symbol, "5m", day_open + slot * 300.0, o, h, low, c, volume))
    _plant(bar_store, symbol, "5m", bars)


def test_baselines_computes_mbr_and_slot_volume_medians_over_prior_sessions(bar_store):
    _plant_prior_sessions(bar_store, "BASE", _PRIOR_DATES_12)
    result = baselines(bar_store, "BASE", SESSION_DATE, 20, 10)
    assert result["sessions"] == 12
    assert result["mbr"] == pytest.approx(1.0)
    assert result["slot_volume_medians"] == {0: 1000, 1: 1000, 2: 1000, 3: 1000}


def test_baselines_reports_a_thin_session_count_below_the_minimum(bar_store):
    _plant_prior_sessions(bar_store, "THIN", _PRIOR_DATES_12[:3])  # only 3 prior sessions
    result = baselines(bar_store, "THIN", SESSION_DATE, 20, 10)
    assert result["sessions"] == 3
    assert result["mbr"] == pytest.approx(1.0)  # still computable -- the CALLER applies the floor


def test_baselines_reports_mbr_zero_for_flat_bars(bar_store):
    _plant_prior_sessions(bar_store, "FLAT", _PRIOR_DATES_12, flat=True)
    result = baselines(bar_store, "FLAT", SESSION_DATE, 20, 10)
    assert result["sessions"] == 12
    assert result["mbr"] == 0.0


def test_baselines_with_no_bars_at_all_is_an_honest_zero(bar_store):
    result = baselines(bar_store, "NOBARS", SESSION_DATE, 20, 10)
    assert result == {"mbr": 0.0, "sessions": 0, "slot_volume_medians": {}}


# --- swing_pivots ------------------------------------------------------------------------------------


def test_swing_pivots_matches_levels_swing_pivots_strict_extreme_rule():
    # highs: pivots at index 2 (105) and index 8 (106); lows: one pivot at index 5 (80); every
    # near-miss (a tie, or falling short on one side) is deliberately included to prove both
    # modules agree on the STRICT rule, not just the easy cases.
    highs = [100, 101, 105, 101, 100, 99, 100, 101, 106, 101, 100]
    lows = [90, 89, 88, 87, 86, 80, 86, 87, 88, 89, 90]
    bars = [
        _bar("PIVOT", "5m", E_OPEN + i * 300.0, (highs[i] + lows[i]) / 2, highs[i], lows[i], (highs[i] + lows[i]) / 2)
        for i in range(len(highs))
    ]
    mine = swing_pivots(bars, lookback=2)
    reference = _levels_swing_pivots(bars, "5m", 2, 0.0, 1.0)

    mine_prices = sorted(p["price"] for p in mine)
    reference_prices = sorted(level["price"] for level in reference)
    assert mine_prices == reference_prices == [80.0, 105.0, 106.0]

    by_price = {p["price"]: p for p in mine}
    assert by_price[105.0]["kind"] == "high"
    assert by_price[105.0]["index"] == 2
    assert by_price[105.0]["confirmed_at"] == 4  # index + lookback
    assert by_price[106.0]["kind"] == "high"
    assert by_price[80.0]["kind"] == "low"
    assert by_price[80.0]["index"] == 5


def test_swing_pivots_too_short_a_series_yields_nothing():
    bars = [_bar("SHORT", "5m", E_OPEN + i * 300.0, 100, 101, 99, 100) for i in range(3)]
    assert swing_pivots(bars, lookback=2) == []  # needs 2*lookback+1 == 5 bars minimum


# --- consolidation_range ------------------------------------------------------------------------------


_CONSOL_BARS = [
    _bar("CONS", "5m", E_OPEN + i * 300.0, o, h, low, c)
    for i, (o, h, low, c) in enumerate(
        [(100.0, 100.5, 99.5, 100.2), (100.2, 100.6, 99.6, 100.3), (100.3, 100.4, 99.7, 100.1), (100.1, 100.7, 99.5, 100.4)]
    )
]


def test_consolidation_range_returns_the_maximal_qualifying_window():
    result = consolidation_range(_CONSOL_BARS, end_idx=3, min_bars=2, max_bars=4, max_range=1.5)
    assert result == (0, 100.7, 99.5)  # the full 4-bar window already qualifies (range 1.2 <= 1.5)


def test_consolidation_range_none_when_even_the_shortest_window_fails():
    result = consolidation_range(_CONSOL_BARS, end_idx=3, min_bars=2, max_bars=4, max_range=0.5)
    assert result is None


# --- vertical_move -------------------------------------------------------------------------------------

_VERT_BARS = [
    _bar("VERT", "5m", E_OPEN + i * 300.0, c, c + 0.2, c - 0.2, c)
    for i, c in enumerate([100.0, 100.2, 100.5, 103.0])
]


def test_vertical_move_true_when_the_net_move_and_close_direction_both_qualify():
    assert vertical_move(_VERT_BARS, end_idx=3, n=3, k=2.5, direction="up") is True


def test_vertical_move_false_when_the_net_move_is_too_small():
    assert vertical_move(_VERT_BARS, end_idx=3, n=3, k=5.0, direction="up") is False


def test_vertical_move_require_volume_gate():
    rising = [1.0, 1.2, 1.5, 2.5]
    assert vertical_move(
        _VERT_BARS, 3, 3, 2.5, "up", require_volume=True, rvol_surge=2.0, rvols=rising
    ) is True
    below_surge = [1.0, 1.2, 1.5, 1.9]
    assert vertical_move(
        _VERT_BARS, 3, 3, 2.5, "up", require_volume=True, rvol_surge=2.0, rvols=below_surge
    ) is False


# --- zone_touches ------------------------------------------------------------------------------------


def test_zone_touches_re_arms_only_after_a_full_exit():
    def _in(i):
        return _bar("ZT", "5m", E_OPEN + i * 300.0, 100.6, 100.8, 99.5, 100.2)

    def _above(i):
        return _bar("ZT", "5m", E_OPEN + i * 300.0, 101.0, 101.5, 100.5, 101.0)

    bars = [_in(0), _in(1), _above(2), _in(3)]
    assert zone_touches(bars, 99.0, 100.0) == [0, 3]


# --- market_context ------------------------------------------------------------------------------------


def test_market_context_null_with_no_spy_bars_at_all():
    assert market_context([], SESSION_DATE, E_OPEN + 900.0, lookback_bars=6) is None


def test_market_context_null_when_not_enough_lookback_bars_exist_yet():
    bars = [_bar("SPY", "5m", E_OPEN + i * 300.0, 400.0, 400.5, 399.5, 400.2) for i in range(3)]
    # lookback=6 needs 7 prior bars; only 3 exist before the trigger epoch.
    assert market_context(bars, SESSION_DATE, E_OPEN + 3 * 300.0, lookback_bars=6) is None


def test_market_context_computes_the_move_once_enough_bars_exist():
    bars = [
        _bar("SPY", "5m", E_OPEN + i * 300.0, 400.0 + i * 0.1, 400.5 + i * 0.1, 399.5 + i * 0.1, 400.0 + i * 0.1)
        for i in range(10)
    ]
    result = market_context(bars, SESSION_DATE, E_OPEN + 9 * 300.0 + 1.0, lookback_bars=6)
    assert result == {
        "move": pytest.approx(0.6), "close_before": pytest.approx(400.9), "bars_available": 10,
    }


# --- side_sign (goal-playbook-iter-3, J-03: the one owner of the playbook's own long/short sign) ---


def test_side_sign_long_is_positive_and_short_is_negative():
    assert side_sign("long") == 1.0
    assert side_sign("short") == -1.0


def test_side_sign_is_never_desk_forwards_side_sign():
    """Deliberately NOT `desk_forward._side_sign` -- that helper is built for the rail's OWN
    support/resistance vocabulary and returns +1.0 for "short" (since "short" != "resistance"),
    which would silently flip every short-side playbook signal's sign positive."""
    from app.research.desk_forward import _side_sign as rail_side_sign

    assert rail_side_sign("short") == 1.0  # the rail's own answer -- proves the two must differ
    assert side_sign("short") == -1.0
