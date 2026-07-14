"""The touch-event scanner + case-study registry (era-5B capability 2, J-02) --
``research/setups.py`` unit + fixture coverage. Mirrors ``test_tradability.py``'s structure: a
small synthetic multi-session, multi-symbol ``"5m"`` fixture gives full control over exact
expected numbers (touch detection, reaction classification, forward returns, the re-arm rule, and
-- critically -- per-session map scoping), then the real committed AAPL fixture proves the SAME
mechanism holds end to end on real data and satisfies J-02's pinned acceptance (the 2026-06-22
``rejected`` event with negative forward returns).

The synthetic fixture (symbol ``SYN-SETUPS-A``, six daily bars + four ``"5m"`` sessions;
``SYN-SETUPS-B``, two daily bars + one ``"5m"`` session) is engineered so ONE resistance level
(anchored near 250) grows a new daily member each session (2026-01-04 through 2026-01-06) while its
INTRADAY price action differs session to session -- a clean ``rejected`` example (2026-01-04, a
1-member band), a clean ``broke`` example (2026-01-05, a 2-member band), and a ``chopped`` example
(2026-01-06, a 4-member band) that doubles as the intraday-density regression guard (a huge-volume,
big-wick touch bar that fully settles back near the band by the reaction horizon). All values below
are VERIFIED BY DIRECT COMPUTATION (printed from a real ``compute_setups`` run against this exact
fixture), never hand-derived -- the ``test_tradability.py`` precedent, because ``compute_tradability``
also folds in ``"5m"``-timeframe swing pivots from EARLIER sessions' own bars once enough later bars
confirm them (see ``test_2026_01_06_session_gains_a_swing_pivot_band_2026_01_05_did_not_have`` for
exactly this -- itself a direct, positive proof of correct per-session ``as_of`` threading, the
module's central risk)."""

from __future__ import annotations

import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.config import CONFIG, Config
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.setups import BROKE, CHOPPED, REJECTED, compute_setups

FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"

_DAY = 86400.0
_FIVE_MIN = 300.0
_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()

SYM_A = "SYN-SETUPS-A"
SYM_B = "SYN-SETUPS-B"

_SMALL_HORIZONS = (2, 5)  # bars -- small so a handful of engineered 5m bars per session suffice


def _syn_config(**overrides) -> Config:
    fields = {"setups_panel_symbols": (SYM_A, SYM_B), "setups_forward_return_horizons_bars": _SMALL_HORIZONS}
    fields.update(overrides)
    return Config(**fields)


def _daily(symbol: str, day_index: int, high: float, low: float, close: float) -> RawBar:
    return RawBar(symbol, "1d", _BASE + day_index * _DAY, close, high, low, close, 1_000)


def _bar5m(symbol: str, day_index: int, bar_offset: int, o: float, h: float, l: float, c: float, v: int) -> RawBar:
    epoch = _BASE + day_index * _DAY + bar_offset * _FIVE_MIN
    return RawBar(symbol, "5m", epoch, o, h, l, c, v)


# --- SYN-SETUPS-A: six daily bars (days 0..5). Days 0/1 are far-apart filler (no accidental
# clustering with the 250-ish target). Days 2/3/4/5 each add ONE new high near 250 (within the
# default 70 bps tradability_band_width_bps of each other, so they progressively join the SAME
# band) and a mirrored low near 150 (unused by the resistance-side tests below). -----------------
_DAILY_A: tuple[RawBar, ...] = (
    _daily(SYM_A, 0, 210.00, 190.00, 200.00),
    _daily(SYM_A, 1, 215.00, 185.00, 200.00),
    _daily(SYM_A, 2, 250.10, 150.10, 200.00),
    _daily(SYM_A, 3, 250.20, 150.20, 200.00),
    _daily(SYM_A, 4, 250.30, 150.30, 200.00),
    _daily(SYM_A, 5, 250.40, 150.40, 200.00),
)

# Session 2026-01-01 (day 0): NO prior daily bar precedes it in the store -> compute_tradability's
# basis never resolves -> an honest empty map -> zero events, regardless of this bar's own price.
_SESSION_DAY0: tuple[RawBar, ...] = (_bar5m(SYM_A, 0, 0, 200, 205, 195, 200, 1_000),)

# Session 2026-01-04 (day 3, basis = day 2's close): the resistance band is a lone 250.10 level (a
# singleton band -- day 2 is the ONLY prior daily bar visible). The touch bar's high (250.15)
# reaches the band; by +2 bars the close has fallen decisively below price_low*(1-30bps) -> REJECTED.
_SESSION_DAY3: tuple[RawBar, ...] = (
    _bar5m(SYM_A, 3, 0, 249.80, 250.15, 249.70, 250.05, 5_000),  # touch
    _bar5m(SYM_A, 3, 1, 250.05, 250.10, 249.00, 249.20, 4_000),
    _bar5m(SYM_A, 3, 2, 249.20, 249.30, 248.50, 248.80, 3_000),  # +2 reaction close
    _bar5m(SYM_A, 3, 3, 248.80, 249.00, 248.00, 248.30, 3_000),
    _bar5m(SYM_A, 3, 4, 248.30, 248.50, 247.80, 248.00, 3_000),
    _bar5m(SYM_A, 3, 5, 248.00, 248.20, 247.50, 247.70, 3_000),  # +5 forward-return bar
)

# Session 2026-01-05 (day 4, basis = day 3's close): the band has grown to [250.10, 250.20] (2
# members). The touch bar's range reaches into the band; by +2 bars the close has pushed decisively
# above price_high*(1+30bps) -> BROKE.
_SESSION_DAY4: tuple[RawBar, ...] = (
    _bar5m(SYM_A, 4, 0, 250.00, 250.15, 249.90, 250.10, 5_000),  # touch
    _bar5m(SYM_A, 4, 1, 250.10, 250.80, 250.05, 250.70, 4_000),
    _bar5m(SYM_A, 4, 2, 250.70, 251.20, 250.60, 251.10, 4_000),  # +2 reaction close
    _bar5m(SYM_A, 4, 3, 251.10, 251.50, 251.00, 251.40, 3_000),
    _bar5m(SYM_A, 4, 4, 251.40, 251.80, 251.30, 251.70, 3_000),
    _bar5m(SYM_A, 4, 5, 251.70, 252.00, 251.60, 251.90, 3_000),  # +5 forward-return bar
)

# Session 2026-01-06 (day 5, basis = day 4's close): the band has grown to [250.10, 250.30] (now
# ALSO picking up a genuine "5m"-timeframe swing-pivot member at 250.15 -- see the dedicated test
# below). The touch bar is a huge-volume (50,000), big-wick (low 245.00, far below the band) bar
# that nonetheless settles back near the band by the reaction horizon -- CHOPPED, proving neither
# the wick nor the volume drove the classification (only the reaction-horizon CLOSE does).
_SESSION_DAY5: tuple[RawBar, ...] = (
    _bar5m(SYM_A, 5, 0, 250.20, 250.25, 245.00, 250.15, 50_000),  # touch: big wick + huge volume
    _bar5m(SYM_A, 5, 1, 250.15, 250.40, 250.00, 250.20, 2_000),
    _bar5m(SYM_A, 5, 2, 250.20, 250.35, 250.05, 250.25, 2_000),  # +2 reaction close
    _bar5m(SYM_A, 5, 3, 250.25, 250.40, 250.10, 250.30, 2_000),
    _bar5m(SYM_A, 5, 4, 250.30, 250.45, 250.15, 250.35, 2_000),
    _bar5m(SYM_A, 5, 5, 250.35, 250.50, 250.20, 250.40, 2_000),  # +5 forward-return bar
)

_FIVE_MIN_A: tuple[RawBar, ...] = _SESSION_DAY0 + _SESSION_DAY3 + _SESSION_DAY4 + _SESSION_DAY5

# --- SYN-SETUPS-B: an isolated second symbol proving (a) events never cross symbols and (b) the
# SUPPORT-side reaction branch (mirrored from the resistance-side logic above). ------------------
_DAILY_B: tuple[RawBar, ...] = (
    _daily(SYM_B, 0, 110.00, 90.00, 100.00),
    _daily(SYM_B, 1, 112.00, 88.10, 100.00),
)
_SESSION_B_DAY2: tuple[RawBar, ...] = (
    _bar5m(SYM_B, 2, 0, 88.50, 88.60, 88.05, 88.20, 1_000),  # touch
    _bar5m(SYM_B, 2, 1, 88.20, 88.90, 88.15, 88.70, 800),
    _bar5m(SYM_B, 2, 2, 88.70, 89.50, 88.60, 89.30, 800),  # +2 reaction close
    _bar5m(SYM_B, 2, 3, 89.30, 89.60, 89.20, 89.50, 800),
    _bar5m(SYM_B, 2, 4, 89.50, 89.80, 89.40, 89.70, 800),
    _bar5m(SYM_B, 2, 5, 89.70, 90.00, 89.60, 89.90, 800),  # +5 forward-return bar
)


def _seed_full(store: BarStore) -> None:
    store.record(
        symbol=SYM_A, timeframe="1d", window_start_utc="2026-01-01T00:00:00Z",
        window_end_utc="2026-01-07T00:00:00Z", feed="sip", bars=list(_DAILY_A),
    )
    store.record(
        symbol=SYM_A, timeframe="5m", window_start_utc="2026-01-01T00:00:00Z",
        window_end_utc="2026-01-07T00:00:00Z", feed="sip", bars=list(_FIVE_MIN_A),
    )
    store.record(
        symbol=SYM_B, timeframe="1d", window_start_utc="2026-01-01T00:00:00Z",
        window_end_utc="2026-01-04T00:00:00Z", feed="sip", bars=list(_DAILY_B),
    )
    store.record(
        symbol=SYM_B, timeframe="5m", window_start_utc="2026-01-01T00:00:00Z",
        window_end_utc="2026-01-04T00:00:00Z", feed="sip", bars=list(_SESSION_B_DAY2),
    )


def _events_for(result: dict, symbol: str, session_date: str) -> list[dict]:
    return [e for e in result["events"] if e["symbol"] == symbol and e["session_date"] == session_date]


def _one_event(result: dict, symbol: str, session_date: str, price_low: float) -> dict:
    matches = [e for e in _events_for(result, symbol, session_date) if e["band"]["price_low"] == price_low]
    assert len(matches) == 1, f"expected exactly one {symbol}/{session_date}/{price_low} event"
    return matches[0]


# --- Exact-value reaction coverage: rejected / broke / chopped ---------------------------------


def test_synthetic_2026_01_04_singleton_band_touch_is_rejected_with_negative_forward_returns(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    result = compute_setups(store, _syn_config())

    event = _one_event(result, SYM_A, "2026-01-04", 250.10)
    assert event["band"]["side"] == "resistance"
    assert event["band"]["price_high"] == 250.10
    assert event["band"]["member_count"] == 1
    assert event["touch_ts"] == "2026-01-04T00:00:00.000000Z"
    assert event["touch_open"] == 249.80
    assert event["touch_high"] == 250.15
    assert event["touch_low"] == 249.70
    assert event["touch_close"] == 250.05
    assert event["touch_volume"] == 5_000
    assert event["reaction"] == REJECTED
    assert event["forward_returns"] == [
        {"horizon_bars": 2, "return_fraction": pytest.approx(-0.004999000199960008)},
        {"horizon_bars": 5, "return_fraction": pytest.approx(-0.009398120375924905)},
    ]
    for fr in event["forward_returns"]:
        assert fr["return_fraction"] < 0, "a rejected event must carry negative forward returns"
    assert event["tape_timeline"] == [], "present-but-empty until J-03 records"


def test_synthetic_2026_01_05_two_member_band_touch_is_broke_with_positive_forward_returns(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    result = compute_setups(store, _syn_config())

    event = _one_event(result, SYM_A, "2026-01-05", 250.10)
    assert event["band"]["price_high"] == 250.20
    assert event["band"]["member_count"] == 2
    assert event["reaction"] == BROKE
    assert event["forward_returns"] == [
        {"horizon_bars": 2, "return_fraction": pytest.approx(0.003998400639744102)},
        {"horizon_bars": 5, "return_fraction": pytest.approx(0.00719712115153943)},
    ]


def test_synthetic_2026_01_06_four_member_band_touch_is_chopped_despite_a_huge_wick_and_volume(tmp_path):
    """The intraday-density regression guard: the touch bar has a 5.15-point low-side wick (245.00
    vs a 250.10-250.30 band) and 50,000 volume -- 25x every neighbouring bar's volume in this
    fixture -- yet the reaction reads ``chopped``, never ``rejected``, because classification reads
    ONLY the reaction-horizon CLOSE (250.25, which clears neither band edge by the configured
    threshold), never the touch bar's own wick extent or its volume."""
    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    result = compute_setups(store, _syn_config())

    event = _one_event(result, SYM_A, "2026-01-06", 250.10)
    assert event["band"]["price_high"] == 250.30
    assert event["band"]["member_count"] == 4
    assert event["touch_low"] == 245.00, "the touch bar's own wick reaches far below the band"
    assert event["touch_volume"] == 50_000, "and carries far more volume than any neighbouring bar"
    assert event["reaction"] == CHOPPED, "neither the wick nor the volume may drive the reaction"
    assert event["forward_returns"] == [
        {"horizon_bars": 2, "return_fraction": pytest.approx(0.0003997601439136291)},
        {"horizon_bars": 5, "return_fraction": pytest.approx(0.0009994003597841295)},
    ]


def test_synthetic_support_side_rejected_and_symbol_isolation(tmp_path):
    """SYN-SETUPS-B exercises the mirrored SUPPORT-side reaction branch (a failed breakdown that
    bounces back above the band reads ``rejected``, the identical DoD wording applied to the other
    side) AND proves symbol isolation: scanning the panel (A + B together) emits B's event with
    symbol ``SYN-SETUPS-B`` only, never conflated with any of A's resistance events above."""
    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    result = compute_setups(store, _syn_config())

    b_events = [e for e in result["events"] if e["symbol"] == SYM_B]
    assert len(b_events) == 1
    event = b_events[0]
    assert event["session_date"] == "2026-01-03"
    assert event["band"]["side"] == "support"
    assert event["band"]["price_low"] == 88.10
    assert event["band"]["price_high"] == 88.10
    assert event["reaction"] == REJECTED
    assert event["forward_returns"] == [
        {"horizon_bars": 2, "return_fraction": pytest.approx(0.01247165532879812)},
        {"horizon_bars": 5, "return_fraction": pytest.approx(0.01927437641723359)},
    ]
    for fr in event["forward_returns"]:
        assert fr["return_fraction"] > 0, "a rejected SUPPORT band bounces price back UP"

    # No A-symbol event is ever misattributed to B, and vice versa.
    assert all(e["symbol"] in (SYM_A, SYM_B) for e in result["events"])
    a_events = [e for e in result["events"] if e["symbol"] == SYM_A]
    assert len(a_events) == 4  # the three resistance events above, plus the 247.5 event below
    assert all(e["symbol"] != SYM_B for e in a_events)


# --- The central risk: per-session `as_of` threading (never a shared/fixed value) ---------------


def test_2026_01_06_session_gains_a_swing_pivot_band_2026_01_05_did_not_have(tmp_path):
    """A DIRECT, positive proof of correct per-session threading -- the exact bug class the module
    docstring's "central risk" describes. 2026-01-04's session (2026-01-04 5m bar 5, low=247.50) is
    visible to BOTH the 2026-01-05 and 2026-01-06 maps, but it only CONFIRMS as a "5m"-timeframe
    swing-pivot low once its right-hand neighbour (2026-01-05's own bar 0) is ALSO visible -- which
    happens for the 2026-01-06 map (basis = 2026-01-05's close, so ALL of 2026-01-05's bars are
    visible) but NOT for the 2026-01-05 map (basis = 2026-01-04's close, so 2026-01-05's OWN bars
    are correctly excluded). A buggy implementation sharing one fixed/latest `as_of` across the
    whole walk would show this EXTRA 247.50 band on EVERY session alike; the correct, per-session
    implementation shows it ONLY from 2026-01-06 onward."""
    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    result = compute_setups(store, _syn_config())

    day4_events = _events_for(result, SYM_A, "2026-01-05")
    assert len(day4_events) == 1, "2026-01-05's map must NOT yet see the 247.50 pivot"
    assert {e["band"]["price_low"] for e in day4_events} == {250.10}

    day5_events = _events_for(result, SYM_A, "2026-01-06")
    assert len(day5_events) == 2, "2026-01-06's map gains the newly-confirmed 247.50 pivot band"
    assert {e["band"]["price_low"] for e in day5_events} == {247.50, 250.10}
    pivot_event = _one_event(result, SYM_A, "2026-01-06", 247.50)
    assert pivot_event["band"]["price_high"] == 247.50
    assert pivot_event["band"]["member_count"] == 1
    assert pivot_event["band"]["members"][0]["timeframe"] == "5m"
    assert pivot_event["band"]["members"][0]["type"] == "swing-pivot"


def test_no_lookahead_extending_the_5m_series_forward_never_changes_an_earlier_session_event(tmp_path):
    """The ``test_tradability.py``
    ``test_no_lookahead_bars_after_the_basis_never_affect_the_result`` technique, applied one layer
    up: a store truncated to ONLY 2026-01-04's own session (plus the daily bars its OWN map needs)
    must emit a BYTE-IDENTICAL 2026-01-04 event to a store that ALSO holds the later 2026-01-05 and
    2026-01-06 sessions -- extending the scan forward never mutates an already-emitted event."""
    full_store = BarStore(tmp_path / "full")
    _seed_full(full_store)
    full_result = compute_setups(full_store, _syn_config())
    full_event = _one_event(full_result, SYM_A, "2026-01-04", 250.10)

    truncated_store = BarStore(tmp_path / "truncated")
    truncated_store.record(
        symbol=SYM_A, timeframe="1d", window_start_utc="2026-01-01T00:00:00Z",
        window_end_utc="2026-01-04T00:00:00Z", feed="sip", bars=list(_DAILY_A[:3]),
    )
    truncated_store.record(
        symbol=SYM_A, timeframe="5m", window_start_utc="2026-01-01T00:00:00Z",
        window_end_utc="2026-01-04T00:00:00Z", feed="sip", bars=list(_SESSION_DAY0 + _SESSION_DAY3),
    )
    truncated_config = Config(setups_panel_symbols=(SYM_A,), setups_forward_return_horizons_bars=_SMALL_HORIZONS)
    truncated_result = compute_setups(truncated_store, truncated_config)
    assert len(truncated_result["events"]) == 1, "the truncated store must only ever emit 2026-01-04's event"
    truncated_event = _one_event(truncated_result, SYM_A, "2026-01-04", 250.10)

    assert json.dumps(full_event, sort_keys=True) == json.dumps(truncated_event, sort_keys=True)


def test_repeat_scan_determinism(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()
    first = compute_setups(store, config)
    second = compute_setups(BarStore(tmp_path / "bars"), config)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert len(first["events"]) >= 1, "the proof must exercise at least one real event"


# --- Honest, distinct empty states (never one fabricated event) --------------------------------


def test_session_with_no_derivable_prior_basis_contributes_no_events(tmp_path):
    """2026-01-01 (day 0) has NO daily bar strictly before it in the store -- compute_tradability's
    basis never resolves, so its map is honestly empty and this session contributes ZERO events,
    regardless of its own 5m bar's price."""
    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    result = compute_setups(store, _syn_config())
    assert _events_for(result, SYM_A, "2026-01-01") == []


def test_symbol_with_no_5m_series_at_all_contributes_no_events(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_full(store)  # never records anything for "SYN-SETUPS-NEVER-RECORDED"
    result = compute_setups(store, _syn_config(setups_panel_symbols=(SYM_A, SYM_B, "SYN-SETUPS-NEVER-RECORDED")))
    assert all(e["symbol"] != "SYN-SETUPS-NEVER-RECORDED" for e in result["events"])


def test_symbol_with_5m_series_but_no_1d_series_contributes_no_events(tmp_path):
    """A "5m" series with no companion "1d" series can never resolve a morning-markup basis
    (compute_tradability's own honest-empty state) -- so it contributes no events, never a crash."""
    store = BarStore(tmp_path / "bars")
    store.record(
        symbol="SYN-SETUPS-NO-DAILY", timeframe="5m", window_start_utc="2026-01-04T00:00:00Z",
        window_end_utc="2026-01-04T01:00:00Z", feed="sip",
        bars=[_bar5m("SYN-SETUPS-NO-DAILY", 3, 0, 100, 105, 95, 100, 1_000)],
    )
    result = compute_setups(store, _syn_config(setups_panel_symbols=("SYN-SETUPS-NO-DAILY",)))
    assert result == {"events": []}


def test_symbol_with_1d_series_but_no_5m_series_contributes_no_events(tmp_path):
    store = BarStore(tmp_path / "bars")
    store.record(
        symbol="SYN-SETUPS-NO-5M", timeframe="1d", window_start_utc="2026-01-01T00:00:00Z",
        window_end_utc="2026-01-02T00:00:00Z", feed="sip",
        bars=[_daily("SYN-SETUPS-NO-5M", 0, 100, 90, 95)],
    )
    result = compute_setups(store, _syn_config(setups_panel_symbols=("SYN-SETUPS-NO-5M",)))
    assert result == {"events": []}


def test_empty_bar_store_is_an_honest_empty_registry(tmp_path):
    store = BarStore(tmp_path / "bars")  # never recorded anything at all
    result = compute_setups(store, _syn_config())
    assert result == {"events": []}


# --- No magic numbers: every setups parameter is config-sourced --------------------------------


def test_setups_parameters_are_config_sourced_no_magic_numbers():
    assert isinstance(CONFIG.setups_panel_symbols, tuple) and len(CONFIG.setups_panel_symbols) == 12
    assert CONFIG.setups_panel_symbols == (
        "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "AMD", "NFLX", "SPY", "QQQ", "JPM",
    )
    assert isinstance(CONFIG.setups_forward_return_horizons_bars, tuple)
    assert len(CONFIG.setups_forward_return_horizons_bars) >= 1
    assert all(isinstance(h, int) and h > 0 for h in CONFIG.setups_forward_return_horizons_bars)
    assert isinstance(CONFIG.setups_reaction_threshold_bps, float) and CONFIG.setups_reaction_threshold_bps > 0
    assert isinstance(CONFIG.setups_max_events_per_band_per_session, int)
    assert CONFIG.setups_max_events_per_band_per_session >= 1
    assert isinstance(CONFIG.setups_5m_fetch_retention_days, int) and CONFIG.setups_5m_fetch_retention_days > 0

    from app.research import setups as setups_module

    src = inspect.getsource(setups_module)
    assert "config.setups_panel_symbols" in src
    assert "config.setups_forward_return_horizons_bars" in src
    assert "config.setups_reaction_threshold_bps" in src
    assert "config.setups_max_events_per_band_per_session" in src


def test_setups_config_fields_are_excluded_from_config_fingerprint():
    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
    assert (
        Config(setups_panel_symbols=("AAPL",)).config_fingerprint() == CONFIG.config_fingerprint()
    )
    assert (
        Config(setups_forward_return_horizons_bars=(1,)).config_fingerprint() == CONFIG.config_fingerprint()
    )
    assert (
        Config(setups_reaction_threshold_bps=999.0).config_fingerprint() == CONFIG.config_fingerprint()
    )
    assert (
        Config(setups_max_events_per_band_per_session=99).config_fingerprint() == CONFIG.config_fingerprint()
    )
    assert (
        Config(setups_5m_fetch_retention_days=1).config_fingerprint() == CONFIG.config_fingerprint()
    )
    # ...while a real classifier threshold still moves it (the counter-test).
    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()


# --- "Scanner, never a second engine": setups.py never re-derives the map/levels ----------------


def test_setups_module_reuses_compute_tradability_verbatim_never_a_second_map_engine():
    """Static-analysis guard for the era-5B critical anti-goal (mirrors
    ``test_tradability_module_is_a_lens_never_a_second_levels_engine``): ``setups.py`` must call
    ``compute_tradability`` -- never ``compute_levels`` directly, never a pivot/extreme detection
    internal, and never a tradability internal that would amount to a second, independent band
    computation."""
    from app.research import setups as setups_module

    src = inspect.getsource(setups_module)
    assert "compute_tradability(" in src
    assert "compute_levels(" not in src, "setups.py must never call compute_levels directly"

    import_lines = [
        line.strip() for line in src.splitlines() if line.strip().startswith(("import ", "from "))
    ]
    tradability_imports = [line for line in import_lines if line.endswith(".tradability import RESISTANCE, SUPPORT, compute_tradability")]
    assert tradability_imports, "setups.py must import compute_tradability (plus the side constants) from .tradability"
    levels_imports = [line for line in import_lines if ".levels" in line]
    assert levels_imports == [], f"setups.py must not import anything from levels.py, got {levels_imports!r}"

    for forbidden_call in (
        "_swing_pivots(", "_prior_period_extremes(", "_cluster_levels(", "_grade_zone(",
        "_cluster_side(", "_band(", "_quality_score(",
    ):
        assert forbidden_call not in src, f"setups.py must not call a levels.py/tradability.py internal {forbidden_call!r}"


# --- The committed real AAPL fixture: J-02's pinned end-to-end acceptance -----------------------


def _load_yahoo_fixture(name: str) -> dict:
    return json.loads((FIXTURE_YAHOO_DIR / name).read_text())


def _seed_yahoo_fixture(store: BarStore, fixture: dict) -> None:
    bars = [
        RawBar(
            fixture["symbol"], fixture["timeframe"], b["epoch"],
            b["open"], b["high"], b["low"], b["close"], b["volume"],
        )
        for b in fixture["bars"]
    ]
    store.record(
        symbol=fixture["symbol"], timeframe=fixture["timeframe"],
        window_start_utc=fixture["start"], window_end_utc=fixture["end"],
        feed="yahoo", bars=bars,
    )


AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"
AAPL_5M_SETUPS_FIXTURE = "AAPL_5m_20260615_20260630.json"


def test_aapl_pinned_2026_06_22_event_is_rejected_with_negative_forward_returns(tmp_path):
    """J-02's headline acceptance: scanning the committed real AAPL fixtures with the SHIPPED
    default config (``setups_forward_return_horizons_bars`` = (78, 234) 5-minute bars, i.e. one and
    three regular NYSE sessions) surfaces the pinned 2026-06-22 ~300-302 resistance-band touch as
    ``rejected`` with BOTH forward-return horizons negative -- goal.md's four/six daily rejections
    then a three-day, -6% collapse. All values verified by direct computation against this
    environment's own live Yahoo-fetched bars (never hand-derived) before being committed here."""
    store = BarStore(tmp_path / "bars")
    _seed_yahoo_fixture(store, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    _seed_yahoo_fixture(store, _load_yahoo_fixture(AAPL_5M_SETUPS_FIXTURE))

    result = compute_setups(store, Config(setups_panel_symbols=("AAPL",)))
    day_events = _events_for(result, "AAPL", "2026-06-22")
    assert day_events, "the pinned 2026-06-22 session must emit at least one event"

    pinned = next(
        e for e in day_events
        if e["band"]["side"] == "resistance"
        and e["band"]["price_low"] <= 300.48 and e["band"]["price_high"] >= 302.07
    )
    assert pinned["reaction"] == REJECTED
    assert len(pinned["forward_returns"]) == 2
    for fr in pinned["forward_returns"]:
        assert fr["return_fraction"] is not None
        assert fr["return_fraction"] < 0, "the pinned event must carry negative forward returns"
    assert pinned["touch_ts"] == "2026-06-22T13:30:00.000000Z"
    assert pinned["band"]["round_number"] is True
    assert pinned["tape_timeline"] == []


def test_aapl_repeat_scan_determinism(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_yahoo_fixture(store, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    _seed_yahoo_fixture(store, _load_yahoo_fixture(AAPL_5M_SETUPS_FIXTURE))
    config = Config(setups_panel_symbols=("AAPL",))
    first = compute_setups(store, config)
    second = compute_setups(BarStore(tmp_path / "bars"), config)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_aapl_frozen_tradability_and_levels_output_is_byte_identical_to_before(tmp_path):
    """The critical single-source-of-truth guard: scanning for events must not perturb
    ``compute_tradability``'s (or, transitively, ``compute_levels``'s) own output on the SAME
    store/as_of -- ``setups.py`` only READS them, per session, and never mutates anything."""
    from app.research.levels import compute_levels
    from app.research.tradability import compute_tradability

    store = BarStore(tmp_path / "bars")
    _seed_yahoo_fixture(store, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    _seed_yahoo_fixture(store, _load_yahoo_fixture(AAPL_5M_SETUPS_FIXTURE))
    as_of = datetime(2026, 6, 22, 15, 0, tzinfo=timezone.utc).timestamp()

    levels_before = compute_levels(store, "AAPL", as_of, CONFIG)
    tradability_before = compute_tradability(store, "AAPL", as_of, CONFIG)
    compute_setups(store, Config(setups_panel_symbols=("AAPL",)))
    levels_after = compute_levels(store, "AAPL", as_of, CONFIG)
    tradability_after = compute_tradability(store, "AAPL", as_of, CONFIG)

    assert json.dumps(levels_before, sort_keys=True) == json.dumps(levels_after, sort_keys=True)
    assert json.dumps(tradability_before, sort_keys=True) == json.dumps(tradability_after, sort_keys=True)
