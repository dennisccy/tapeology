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

import dataclasses
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.config import CONFIG, Config
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.datasets import DatasetStore
from app.research.setups import BROKE, CHOPPED, REJECTED, compute_setups, enrich_with_tape_timeline

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
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
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

    config = Config(setups_panel_symbols=("AAPL",))
    result = compute_setups(store, config)
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
    # B1 (era-5B iter-5): the pinned event is nowhere near the store's recency boundary -- byte-
    # identical to before, plus the two new additive fields at their honest "untruncated" values.
    assert pinned["reaction_boundary_truncated"] is False
    assert pinned["effective_reaction_horizon_bars"] == config.setups_forward_return_horizons_bars[0] == 78


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


# --- Tape-at-the-wall join (era-5B capability 4, J-03): a committed real-tick dataset joined
# onto a synthetic PG touch event -----------------------------------------------------------------
#
# ONE synthetic PG event whose touch lands inside the REAL committed PG SIP reference window
# (tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json, 2026-06-09T17:00-17:10). Bars are
# ENGINEERED (the test_tradability.py/test_setups.py synthetic-fixture precedent: full control
# over exact expected numbers), but the recorded TICK data the join replays is REAL, never
# fabricated: tests/fixtures/datasets_j03/ was generated ONCE, through the real record path, by
# scripts/generate_setups_join_fixture.py (see that script's own docstring for provenance) --
# never hand-crafted JSON.

FIXTURE_DATASETS_J03_DIR = Path(__file__).parent / "fixtures" / "datasets_j03"

_PG_SESSION_BASE = datetime(2026, 6, 9, 17, 0, 0, tzinfo=timezone.utc).timestamp()


def _pg_5m(offset_seconds: float, o: float, h: float, l: float, c: float, v: int) -> RawBar:
    return RawBar("PG", "5m", _PG_SESSION_BASE + offset_seconds, o, h, l, c, v)


_PG_DAILY_BASIS = RawBar(
    "PG", "1d", datetime(2026, 6, 8, tzinfo=timezone.utc).timestamp(),
    100.0, 110.00, 90.00, 100.00, 1_000,
)
# Touch bar at 17:02:30Z -- 30s inside the committed fixture's own recorded [17:02:00, 17:03:00)
# window -- touching the lone resistance level (2026-06-08's daily high, 110.00).
_PG_TOUCH_BAR = _pg_5m(150.0, 109.80, 110.05, 109.70, 110.02, 5_000)
_PG_REACTION_BAR_1 = _pg_5m(450.0, 110.02, 110.10, 109.00, 109.20, 4_000)  # +1 horizon
_PG_REACTION_BAR_2 = _pg_5m(750.0, 109.20, 109.30, 108.50, 108.80, 3_000)  # +2 horizon -- REJECTED


def _pg_join_config() -> Config:
    return Config(setups_panel_symbols=("PG",), setups_forward_return_horizons_bars=(1, 2))


def _seed_pg_join_bars(store: BarStore) -> None:
    store.record(
        symbol="PG", timeframe="1d", window_start_utc="2026-06-08T00:00:00Z",
        window_end_utc="2026-06-09T00:00:00Z", feed="sip", bars=[_PG_DAILY_BASIS],
    )
    store.record(
        symbol="PG", timeframe="5m", window_start_utc="2026-06-09T17:00:00Z",
        window_end_utc="2026-06-09T17:15:00Z", feed="sip",
        bars=[_PG_TOUCH_BAR, _PG_REACTION_BAR_1, _PG_REACTION_BAR_2],
    )


def _pg_join_event(bar_store: BarStore) -> dict:
    result = compute_setups(bar_store, _pg_join_config())
    assert len(result["events"]) == 1, "the engineered PG fixture must emit exactly one event"
    return result["events"][0]


def test_pg_join_event_has_the_expected_shape_before_any_join(tmp_path):
    """Verified by direct computation against the engineered fixture (never hand-derived) -- the
    UN-enriched event compute_setups emits, before the join runs at all."""
    bar_store = BarStore(tmp_path / "bars")
    _seed_pg_join_bars(bar_store)
    event = _pg_join_event(bar_store)

    assert event["id"] == "77e4900ec3089ded"
    assert event["symbol"] == "PG"
    assert event["session_date"] == "2026-06-09"
    assert event["touch_ts"] == "2026-06-09T17:02:30.000000Z"
    assert event["reaction"] == REJECTED
    assert event["band"] == {
        "side": "resistance",
        "price_low": 110.0,
        "price_high": 110.0,
        "class": None,
        "quality_score": 27.0,
        "round_number": False,
        "member_count": 1,
        "members": [
            {
                "price": 110.0, "strength": 4.0, "timeframe": "1d",
                "touch_count": 1, "type": "prior-period-extreme",
            },
        ],
    }
    assert event["forward_returns"] == [
        {"horizon_bars": 1, "return_fraction": pytest.approx(-0.007453190329031024)},
        {"horizon_bars": 2, "return_fraction": pytest.approx(-0.011088892928558435)},
    ]
    assert event["tape_timeline"] == [], "un-joined -- honestly empty, exactly like every other event"


def test_join_path_matches_the_committed_fixture_and_returns_the_exact_five_state_timeline(tmp_path):
    """J-03's headline join-path proof: the committed real-tick fixture
    (tests/fixtures/datasets_j03/) covers the engineered touch's own [17:02:00, 17:03:00) window,
    so ``enrich_with_tape_timeline`` matches it by symbol + window containment, replays it through
    the FROZEN ``TapeEngine``, and returns the EXACT state/confidence/order sequence -- verified by
    direct computation against the real committed fixture (never hand-derived), collapsed from
    1,963 raw trade+quote events down to 4 meaningful state-transition entries (the
    ``HistoryBuffer.note_state`` idiom this module's join mirrors)."""
    bar_store = BarStore(tmp_path / "bars")
    _seed_pg_join_bars(bar_store)
    event = _pg_join_event(bar_store)

    dataset_store = DatasetStore(FIXTURE_DATASETS_J03_DIR)
    enriched = enrich_with_tape_timeline(event, dataset_store, _pg_join_config())

    # Every OTHER field is served verbatim -- the join touches tape_timeline alone.
    unchanged = {k: v for k, v in enriched.items() if k != "tape_timeline"}
    assert unchanged == {k: v for k, v in event.items() if k != "tape_timeline"}

    assert enriched["tape_timeline"] == [
        {
            "timestamp": "2026-06-09T17:02:08.926045Z", "state": "seller_control",
            "confidence": pytest.approx(0.600948859073259),
        },
        {
            "timestamp": "2026-06-09T17:02:10.313400Z", "state": "seller_control",
            "confidence": pytest.approx(0.6186718843924585),
        },
        {
            "timestamp": "2026-06-09T17:02:13.893943Z", "state": "seller_control",
            "confidence": pytest.approx(0.6827213366979764),
        },
        {
            "timestamp": "2026-06-09T17:02:55.616940Z", "state": "seller_control",
            "confidence": pytest.approx(0.7506461682283672),
        },
    ]
    # Chronological order (never insertion-order happenstance).
    timestamps = [entry["timestamp"] for entry in enriched["tape_timeline"]]
    assert timestamps == sorted(timestamps)


def test_join_path_is_deterministic_across_repeat_calls(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    _seed_pg_join_bars(bar_store)
    event = _pg_join_event(bar_store)
    dataset_store = DatasetStore(FIXTURE_DATASETS_J03_DIR)

    first = enrich_with_tape_timeline(event, dataset_store, _pg_join_config())
    second = enrich_with_tape_timeline(event, dataset_store, _pg_join_config())
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_unmatched_event_keeps_an_honestly_empty_tape_timeline(tmp_path):
    """An event with NO recorded dataset covering its touch -- here, a differently-timed touch (3h
    later) the committed fixture's [17:02, 17:03) window does not cover -- stays honestly empty,
    never fabricated. Verified by direct computation: an otherwise-identical fixture, time-shifted,
    still emits exactly one REJECTED event -- only ``touch_ts``/``id`` differ."""
    bar_store = BarStore(tmp_path / "bars")
    bar_store.record(
        symbol="PG", timeframe="1d", window_start_utc="2026-06-08T00:00:00Z",
        window_end_utc="2026-06-09T00:00:00Z", feed="sip", bars=[_PG_DAILY_BASIS],
    )
    late_offset = 3 * 3600  # three hours later than the committed fixture's own window
    bar_store.record(
        symbol="PG", timeframe="5m", window_start_utc="2026-06-09T17:00:00Z",
        window_end_utc="2026-06-09T21:00:00Z", feed="sip",
        bars=[
            _pg_5m(late_offset + 150.0, 109.80, 110.05, 109.70, 110.02, 5_000),
            _pg_5m(late_offset + 450.0, 110.02, 110.10, 109.00, 109.20, 4_000),
            _pg_5m(late_offset + 750.0, 109.20, 109.30, 108.50, 108.80, 3_000),
        ],
    )
    event = _pg_join_event(bar_store)
    assert event["touch_ts"] == "2026-06-09T20:02:30.000000Z"
    assert event["reaction"] == REJECTED

    dataset_store = DatasetStore(FIXTURE_DATASETS_J03_DIR)  # the SAME real committed fixture
    enriched = enrich_with_tape_timeline(event, dataset_store, _pg_join_config())
    assert enriched == event, "no matching dataset -> the event is returned completely unchanged"
    assert enriched["tape_timeline"] == []


def test_empty_dataset_store_leaves_every_event_honestly_empty(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    _seed_pg_join_bars(bar_store)
    event = _pg_join_event(bar_store)

    empty_dataset_store = DatasetStore(tmp_path / "no-datasets-here")
    enriched = enrich_with_tape_timeline(event, empty_dataset_store, _pg_join_config())
    assert enriched == event
    assert enriched["tape_timeline"] == []


# --- Single source of truth: the join reuses the frozen TapeEngine/DatasetStore.replay, and stays
# confined to the detail route's own wiring -- never inside compute_setups' shared scan loop ------


def test_setups_join_reuses_dataset_store_replay_never_a_second_tape_engine():
    """era-5B J-03 critical anti-goal (mirrors
    ``test_setups_module_reuses_compute_tradability_verbatim_never_a_second_map_engine``): the tape
    join must replay through the FROZEN ``TapeEngine`` via ``DatasetStore.replay`` -- never
    construct a second engine, never reimplement classification."""
    from app.research import setups as setups_module

    src = inspect.getsource(setups_module)
    assert "dataset_store.replay(" in src
    assert "TapeEngine(" not in src, "setups.py must never construct a second TapeEngine"
    assert "TapeStateClassifier" not in src, "setups.py must never reimplement classification"

    import_lines = [
        line.strip() for line in src.splitlines() if line.strip().startswith(("import ", "from "))
    ]
    dataset_imports = [
        line for line in import_lines
        if line.endswith(".datasets import DatasetStore, parse_utc_epoch")
    ]
    assert dataset_imports, "setups.py must import DatasetStore (+ parse_utc_epoch) from .datasets"


def test_compute_setups_itself_never_touches_the_dataset_store():
    """Architecture guard: the join lives ONLY in ``enrich_with_tape_timeline``, called ONLY from
    the ``GET /research/setups/{id}`` route -- neither the public ``compute_setups`` (the B3 cache
    wrapper, era-5B iter-5) nor its internal ``_run_full_panel_scan`` (the actual shared scan loop
    used by BOTH the list and detail routes) may ever reference the ``DatasetStore``, so the join
    never adds an O(events) dataset-store scan to the already-slow full-panel list route."""
    from app.research.setups import _run_full_panel_scan

    assert "dataset" not in inspect.getsource(compute_setups).lower(), (
        "compute_setups must never reference the dataset store"
    )
    assert "dataset" not in inspect.getsource(_run_full_panel_scan).lower(), (
        "_run_full_panel_scan must never reference the dataset store"
    )


# --- Config: the recording constants are excluded from config_fingerprint -----------------------


def test_recording_config_fields_are_excluded_from_config_fingerprint():
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
    assert Config(recording_pre_touch_minutes=1.0).config_fingerprint() == CONFIG.config_fingerprint()
    assert Config(recording_post_touch_minutes=1.0).config_fingerprint() == CONFIG.config_fingerprint()
    assert Config(recording_event_selection_cap=1).config_fingerprint() == CONFIG.config_fingerprint()
    assert Config(recording_holdout_fraction=0.99).config_fingerprint() == CONFIG.config_fingerprint()
    # ...while a real classifier threshold still moves it (the counter-test).
    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()


# --- B1 (era-5B iter-5): the recency-boundary regression -- a purpose-built fixture whose final
# touch has FEWER than the shipped ``setups_forward_return_horizons_bars[0]`` (78) bars remaining
# anywhere in the store, mirroring SYN-SETUPS-A's proven ``_DAILY_A``/``_SESSION_DAY3`` shape (a
# singleton 250.10 resistance level, a touch that decisively fails back off it) but with only 5
# total "5m" bars in the WHOLE store -- so the store runs out of bars LONG before the real 78-bar
# horizon elapses, the exact shape a freshly-fetched panel symbol's latest session is in every day
# until enough later bars accumulate. The committed AAPL fixtures (`AAPL_5m_20260615_20260630.json`)
# stop 2026-06-30 -- comfortably far from any recency boundary -- so they cannot exercise this path
# (iter-2 + iter-4 lesson): this dedicated symbol/fixture is required. -------------------------------

SYM_BOUNDARY = "SYN-SETUPS-BOUNDARY"

_DAILY_BOUNDARY: tuple[RawBar, ...] = (
    _daily(SYM_BOUNDARY, 0, 210.00, 190.00, 200.00),  # filler -- far from the target level
    _daily(SYM_BOUNDARY, 1, 215.00, 185.00, 200.00),  # filler -- far from the target level
    _daily(SYM_BOUNDARY, 2, 250.10, 150.10, 200.00),  # the ONE level-forming daily bar
)

# Day 3's own (and ONLY) "5m" session: deliberately just 5 bars -- the exact SYN-SETUPS-A
# ``_SESSION_DAY3`` touch/price shape (a clean REJECTED example), truncated after its former +2
# reaction-close bar so the WHOLE store ends there. With the real horizons[0]=78, the reaction
# close for the touch at index 0 is capped at index 4 (the last bar in the store) -- an
# effective horizon of 4 bars, not 78.
_SESSION_BOUNDARY: tuple[RawBar, ...] = (
    _bar5m(SYM_BOUNDARY, 3, 0, 249.80, 250.15, 249.70, 250.05, 5_000),  # touch (index 0)
    _bar5m(SYM_BOUNDARY, 3, 1, 250.05, 250.10, 249.00, 249.20, 4_000),
    _bar5m(SYM_BOUNDARY, 3, 2, 249.20, 249.30, 248.50, 248.80, 3_000),
    _bar5m(SYM_BOUNDARY, 3, 3, 248.80, 249.00, 248.00, 248.30, 3_000),
    _bar5m(SYM_BOUNDARY, 3, 4, 248.30, 248.50, 247.80, 248.00, 3_000),  # last bar in the store
)


def _seed_boundary(store: BarStore) -> None:
    store.record(
        symbol=SYM_BOUNDARY, timeframe="1d", window_start_utc="2026-01-01T00:00:00Z",
        window_end_utc="2026-01-04T00:00:00Z", feed="sip", bars=list(_DAILY_BOUNDARY),
    )
    store.record(
        symbol=SYM_BOUNDARY, timeframe="5m", window_start_utc="2026-01-04T00:00:00Z",
        window_end_utc="2026-01-04T00:25:00Z", feed="sip", bars=list(_SESSION_BOUNDARY),
    )


def test_boundary_touch_discloses_truncated_horizon_with_a_definitive_reaction(tmp_path):
    """B1 (era-5B iter-5) headline regression: a touch inside the store's MOST RECENT (and only)
    session, with fewer than the shipped ``setups_forward_return_horizons_bars[0]`` (78) bars
    remaining anywhere in the store, still gets a DEFINITIVE reaction label -- but the event now
    additively discloses that the horizon was truncated, rather than silently pairing a definitive
    label with a bare ``None`` horizon-0 return. All values verified by direct computation against
    this exact fixture (never hand-derived): touch at index 0 of a 5-bar store, reaction read at
    the last available bar (index 4, close 248.00) -- decisively below the 30bps-widened reject
    level of a singleton 250.10 resistance band -> REJECTED, effective horizon 4 (not 78)."""
    store = BarStore(tmp_path / "bars")
    _seed_boundary(store)
    config = Config(setups_panel_symbols=(SYM_BOUNDARY,))
    assert config.setups_forward_return_horizons_bars[0] == 78, (
        "this regression must exercise the REAL shipped horizon, never a small test-only override"
    )

    result = compute_setups(store, config)
    events = result["events"]
    assert len(events) == 1, "the engineered fixture emits exactly one boundary touch event"
    event = events[0]

    assert event["band"]["side"] == "resistance"
    assert event["band"]["price_low"] == event["band"]["price_high"] == 250.10
    assert event["touch_ts"] == "2026-01-04T00:00:00.000000Z"
    assert event["reaction"] in (REJECTED, BROKE, CHOPPED), "a definitive label, never suppressed"
    assert event["reaction"] == REJECTED
    assert event["forward_returns"][0] == {"horizon_bars": 78, "return_fraction": None}
    assert event["reaction_boundary_truncated"] is True
    assert event["effective_reaction_horizon_bars"] == 4
    assert event["effective_reaction_horizon_bars"] < config.setups_forward_return_horizons_bars[0]


def test_boundary_regression_is_deterministic_across_repeat_scans(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_boundary(store)
    config = Config(setups_panel_symbols=(SYM_BOUNDARY,))
    first = compute_setups(store, config)
    second = compute_setups(BarStore(tmp_path / "bars"), config)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


# --- B3 (era-5B iter-5): the process-local memoized scan cache ----------------------------------
# `compute_setups` is now a thin cache wrapper around the real scan (`_run_full_panel_scan`,
# exercised directly here to prove cache vs. fresh byte-identity). All four tests below use the
# SYN-SETUPS-A/B fixtures (`_seed_full`) except the immutable-safety test, which reuses the PG
# tape-join fixtures below (a real, non-empty ``tape_timeline`` is the only genuine proof that an
# enriched read could corrupt the shared cache if it were not copy-on-write).


def test_cache_hit_is_byte_identical_to_a_fresh_uncached_scan(tmp_path):
    """A cache HIT (the second ``compute_setups`` call) must be byte-identical to a genuinely
    fresh, uncached scan (``_run_full_panel_scan``, called directly, bypassing the cache entirely)
    -- the cache changes only WHETHER the scan runs, never WHAT it returns."""
    from app.research.setups import _run_full_panel_scan

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()

    first = compute_setups(store, config)  # populates the cache
    cached = compute_setups(store, config)  # a cache HIT
    fresh = _run_full_panel_scan(store, config)  # bypasses the cache entirely

    first_json = json.dumps(first, sort_keys=True)
    assert first_json == json.dumps(cached, sort_keys=True) == json.dumps(fresh, sort_keys=True)
    assert len(fresh["events"]) >= 1, "the proof must exercise at least one real event"


def test_scan_runs_at_most_once_across_repeated_reads_of_an_unchanged_store(tmp_path, monkeypatch):
    """The underlying scan body runs exactly ONCE across repeated ``compute_setups`` calls against
    an unchanged store/config (a call-count spy, never wall-clock) -- the
    ``test_compute_setups_runs_at_most_once_per_report_call`` precedent in
    ``test_edge_report.py``, applied one layer down to the scan itself."""
    import app.research.setups as setups_module

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()

    calls: list[int] = []
    real_scan = setups_module._run_full_panel_scan

    def _counting_scan(*args, **kwargs):
        calls.append(1)
        return real_scan(*args, **kwargs)

    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)

    for _ in range(4):
        compute_setups(store, config)
    assert len(calls) == 1, "an unchanged store/config must only ever trigger ONE real scan"


def test_cache_busts_and_rescans_when_the_store_gains_a_new_series(tmp_path, monkeypatch):
    """Mutating the store (registering a brand-new series) must bust the cache and re-run the
    scan on the VERY NEXT read -- never serve a stale result computed before the mutation."""
    import app.research.setups as setups_module

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()

    calls: list[int] = []
    real_scan = setups_module._run_full_panel_scan

    def _counting_scan(*args, **kwargs):
        calls.append(1)
        return real_scan(*args, **kwargs)

    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)

    compute_setups(store, config)
    compute_setups(store, config)
    assert len(calls) == 1, "unchanged store so far -- still just the one real scan"

    # A brand-new registered series -- any content -- changes the store's own content signature.
    store.record(
        symbol=SYM_B, timeframe="1d", window_start_utc="2026-03-01T00:00:00Z",
        window_end_utc="2026-03-02T00:00:00Z", feed="sip",
        bars=[_daily(SYM_B, 60, 999.0, 998.0, 998.5)],
    )
    compute_setups(store, config)
    assert len(calls) == 2, "a newly registered series must bust the cache and re-run the scan"


def test_enriched_detail_read_never_leaks_into_the_shared_cached_list(tmp_path):
    """The B3 immutable-safety guard: a ``/setups/{id}``-style enriched read
    (``enrich_with_tape_timeline``, already copy-on-write per its own docstring) must never
    corrupt the SHARED cached list a subsequent ``/setups``-style list read serves. Uses the real
    committed J-03 tape-join fixture so the enrichment is genuinely non-empty -- an empty-to-empty
    enrichment would prove nothing."""
    store = BarStore(tmp_path / "bars")
    _seed_pg_join_bars(store)
    config = _pg_join_config()

    listed_before = compute_setups(store, config)
    event = listed_before["events"][0]
    assert event["tape_timeline"] == [], "unenriched, exactly like every fresh scan result"

    dataset_store = DatasetStore(FIXTURE_DATASETS_J03_DIR)
    enriched = enrich_with_tape_timeline(event, dataset_store, config)
    assert enriched["tape_timeline"], "the join must have actually attached a real, non-empty timeline"

    listed_after = compute_setups(store, config)  # a cache HIT -- the SAME shared object
    assert listed_after["events"][0]["tape_timeline"] == [], (
        "the enriched read must never leak into the shared cached list"
    )
    assert json.dumps(listed_before, sort_keys=True) == json.dumps(listed_after, sort_keys=True)


# --- B3 atomicity hardening (era-5B iter-6) ------------------------------------------------------
# iter-6 is the first caller to fire `/setups` + `/setups/{id}` + `/edge-report` concurrently from
# one browser page load against a possibly-cold scan cache -- see the `_SCAN_CACHE` block comment
# in setups.py for the exact torn-read hazard the prior two-key dict form had. TWO tests, each
# covering a different failure mode:
#   * the STRUCTURAL guard below proves the fix DETERMINISTICALLY (never relies on winning a GIL
#     timing race): the historical bug was two SEPARATE writes to two dict keys, and the narrow
#     window between them is far too small for any wall-clock trick in a test to land on reliably
#     (confirmed empirically while developing this test: the behavioral test below passed 5/5 runs
#     against the deliberately-reverted OLD two-key-dict implementation -- a real proof that a
#     purely behavioral/timing-based test alone would give false confidence here);
#   * the BEHAVIORAL test after it proves the CURRENT implementation genuinely tolerates concurrent
#     callers under real thread contention -- no crash, no None, byte-identical results everywhere.


def test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes():
    """The DETERMINISTIC half of the B3 atomicity proof (see the section comment above for why a
    timing-based test alone cannot be trusted here): ``compute_setups`` must publish the cache via
    EXACTLY ONE assignment to the shared module-level slot -- never the old two-key-dict shape
    (``_SCAN_CACHE["key"] = ...`` THEN ``_SCAN_CACHE["result"] = ...``), which is the literal
    torn-read hazard this iteration closes. Mirrors this file's own established
    ``inspect.getsource``-based architecture guards (e.g.
    ``test_setups_module_reuses_compute_tradability_verbatim_never_a_second_map_engine``,
    ``test_compute_setups_itself_never_touches_the_dataset_store``)."""
    src = inspect.getsource(compute_setups)

    # The exact historical bug shape must never reappear.
    assert '_SCAN_CACHE["key"]' not in src, "the old two-key dict publish must not return"
    assert '_SCAN_CACHE["result"]' not in src, "the old two-key dict publish must not return"
    assert "_SCAN_CACHE.update(" not in src, "an in-place dict update is the identical hazard"

    # Exactly one publish, and it is a single rebind of the whole slot (`global` + one `= (` on the
    # module-level name) -- never two statements that could be observed half-done.
    rebinds = [line for line in src.splitlines() if line.strip().startswith("_SCAN_CACHE = ")]
    assert len(rebinds) == 1, (
        f"expected exactly ONE atomic rebind of _SCAN_CACHE, found {len(rebinds)}: {rebinds}"
    )
    assert "global _SCAN_CACHE" in src, "a module-level rebind from inside the function needs `global`"


def test_concurrent_cold_cache_reads_never_observe_a_torn_key_result_pair(tmp_path, monkeypatch):
    """Many threads racing a COLD cache (nothing published yet) with a deliberately widened publish
    window (a small sleep injected into the scan, forcing genuine overlap around the moment the
    winning thread's result would be published) must ALL return a real, non-`None`,
    byte-identical result -- never a crash and never a torn key/result pairing (a result that is
    `None`, or one that fails to match every other thread's own result). Uses a fresh `Config(...)`
    (never previously cached, per the module's own `id(config)` keying) so this test can never
    accidentally observe a DIFFERENT test's leftover cache entry."""
    import threading
    import time

    import app.research.setups as setups_module

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()

    real_scan = setups_module._run_full_panel_scan

    def _slow_scan(*args, **kwargs):
        result = real_scan(*args, **kwargs)
        time.sleep(0.05)  # widen the window so concurrent callers genuinely overlap the publish
        return result

    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _slow_scan)

    thread_count = 16
    results: list[dict | None] = [None] * thread_count
    errors: list[BaseException] = []
    start_barrier = threading.Barrier(thread_count)

    def _call(index: int) -> None:
        start_barrier.wait()  # every thread reaches compute_setups at roughly the same instant
        try:
            results[index] = compute_setups(store, config)
        except BaseException as exc:  # pragma: no cover -- failure path only
            errors.append(exc)

    threads = [threading.Thread(target=_call, args=(i,)) for i in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    assert errors == [], f"a concurrent cold-cache read raised (never a torn read, never a crash): {errors}"
    assert all(r is not None for r in results), (
        "every concurrent caller must return a real result -- a None here IS the torn-read bug "
        "(a published key paired with the slot's still-stale/None result)"
    )
    expected = json.dumps(results[0], sort_keys=True)
    assert all(json.dumps(r, sort_keys=True) == expected for r in results), (
        "every concurrent caller must observe the SAME byte-identical result -- a mismatch would "
        "mean some reader saw a torn/partial key-result pairing"
    )
    assert len(results[0]["events"]) >= 1, "the proof must exercise at least one real event"


# --- era-fast_wall J-06: the durable setups scan cache (three-tier lookup: hot slot -> durable ->
# real scan). ``setups_scan_cache.py``'s own module docstring/test file
# (``test_setups_scan_cache.py``) cover the cache's own mechanics (key composition, byte-identity,
# corrupted-DB tolerance) in isolation; this section proves ``compute_setups``'s OWN wiring of that
# cache into its three-tier lookup -- restart simulation, content-hash equality, cache-busting, and
# the non-vacuous mutation probe (iter-3's lesson, named for exactly this journey in
# `docs/goal.md`'s BACKGROUND section). --------------------------------------------------------------


def test_tc1_hot_slot_cleared_simulating_a_restart_serves_the_durable_cache_with_zero_rescans(
    tmp_path, monkeypatch,
):
    """TC-1: a call-counting spy proves the durable cache -- not a fresh rescan -- answers once the
    in-process hot slot is cleared (simulating a process restart), and the served result is
    byte-identical to the original scan."""
    import app.research.setups as setups_module

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()
    original = compute_setups(store, config)  # populates BOTH the hot slot and the durable cache

    setups_module._reset_scan_cache_for_tests()  # simulate a process restart -- hot slot cleared

    calls: list[int] = []
    real_scan = setups_module._run_full_panel_scan

    def _counting_scan(*args, **kwargs):
        calls.append(1)
        return real_scan(*args, **kwargs)

    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)

    restarted = compute_setups(store, config)

    assert calls == [], "a durable-cache hit must cost ZERO calls to the real scan"
    assert json.dumps(restarted, sort_keys=True) == json.dumps(original, sort_keys=True)


def test_tc2_equal_content_but_distinct_config_object_is_a_cache_hit_identity_fragility_gone(
    tmp_path, monkeypatch,
):
    """TC-2: the ``id(config)`` fragility is gone -- a SECOND, freshly-constructed ``Config`` with
    IDENTICAL field values (a different ``id()``) is a genuine cache hit, served WITHOUT even
    needing to clear the (still-warm) hot slot -- proving the key itself is content-derived."""
    import app.research.setups as setups_module

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()
    original = compute_setups(store, config)

    second_config = dataclasses.replace(config)
    assert second_config is not config, "the proof requires a genuinely distinct object"

    calls: list[int] = []
    real_scan = setups_module._run_full_panel_scan

    def _counting_scan(*args, **kwargs):
        calls.append(1)
        return real_scan(*args, **kwargs)

    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)

    second = compute_setups(store, second_config)

    assert calls == [], "a content-equal Config object must be a genuine cache HIT, never id()-keyed"
    assert json.dumps(second, sort_keys=True) == json.dumps(original, sort_keys=True)


def test_tc3_a_setups_family_field_change_busts_the_cache_content_hash_not_fingerprint_alone(
    tmp_path, monkeypatch,
):
    """TC-3: ``config_fingerprint()`` EXCLUDES the ``setups_*``/``tradability_*``/``sr_*`` families
    (see ``test_setups_config_fields_are_excluded_from_config_fingerprint`` above), so a cache keyed
    on the fingerprint alone would silently under-invalidate here. The full CONTENT hash must not."""
    import app.research.setups as setups_module

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()
    compute_setups(store, config)

    changed = _syn_config(setups_reaction_threshold_bps=config.setups_reaction_threshold_bps + 5.0)
    assert changed.config_fingerprint() == config.config_fingerprint(), (
        "sanity: setups_reaction_threshold_bps is excluded from config_fingerprint"
    )

    calls: list[int] = []
    real_scan = setups_module._run_full_panel_scan

    def _counting_scan(*args, **kwargs):
        calls.append(1)
        return real_scan(*args, **kwargs)

    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)

    compute_setups(store, changed)

    assert len(calls) == 1, "the CONTENT hash (not config_fingerprint alone) must drive the key"


def test_an_algorithm_version_bump_busts_the_cache_with_config_and_store_unchanged(
    tmp_path, monkeypatch,
):
    """The third way a cached value can go stale, beside a config change (TC-3) and a store change
    (TC-4): the COMPUTATION itself changes while both key inputs stay byte-identical. Without
    ``LEVELS_ALGORITHM_VERSION`` in the key, a cache written before such a change keeps serving
    results the current code would never produce -- exactly what happened when levels moved to the
    merged per-timeframe bar view (the store's checksums and every ``Config`` field were
    untouched)."""
    import app.research.edge_report_cache as cache_module
    import app.research.setups as setups_module

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()
    compute_setups(store, config)

    calls: list[int] = []
    real_scan = setups_module._run_full_panel_scan

    def _counting_scan(*args, **kwargs):
        calls.append(1)
        return real_scan(*args, **kwargs)

    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)
    # Nothing about the inputs moves -- only the declared version of the computation.
    monkeypatch.setattr(cache_module, "LEVELS_ALGORITHM_VERSION", 999)
    setups_module._reset_scan_cache_for_tests()

    compute_setups(store, config)

    assert len(calls) == 1, "an algorithm-version bump must bust the durable cache key"


def test_tc4_recording_a_new_5m_series_into_the_store_busts_the_durable_cache_key(tmp_path, monkeypatch):
    """TC-4: a store-content change (a newly recorded '5m' series) must bust the key even though
    ``config`` itself is unchanged."""
    import app.research.setups as setups_module

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()
    compute_setups(store, config)

    calls: list[int] = []
    real_scan = setups_module._run_full_panel_scan

    def _counting_scan(*args, **kwargs):
        calls.append(1)
        return real_scan(*args, **kwargs)

    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)

    store.record(
        symbol="SYN-SETUPS-NEW", timeframe="5m", window_start_utc="2026-03-01T00:00:00Z",
        window_end_utc="2026-03-01T00:05:00Z", feed="sip",
        bars=[_bar5m("SYN-SETUPS-NEW", 60, 0, 100, 105, 95, 100, 1_000)],
    )
    compute_setups(store, config)

    assert len(calls) == 1, "a newly recorded series must bust the cache and re-run the scan"


def test_tc5_deleting_the_durable_db_file_is_harmless_recomputes_once_byte_identical(tmp_path, monkeypatch):
    """TC-5: deleting the durable cache DB (plus its WAL/SHM sidecars) and clearing the hot slot
    costs exactly one recompute, byte-identical to the pre-deletion result -- proving the durable
    layer is a rebuildable accelerator, never a source of truth."""
    import app.research.setups as setups_module
    from app.research.setups_scan_cache import resolve_scan_cache_db_path

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()
    original = compute_setups(store, config)

    db_path = Path(resolve_scan_cache_db_path(str(store.root)))
    assert db_path.exists(), "the durable cache DB must exist after a real publish"
    for suffix in ("", "-wal", "-shm"):
        sidecar = db_path.parent / (db_path.name + suffix)
        if sidecar.exists():
            sidecar.unlink()
    assert not db_path.exists()

    setups_module._reset_scan_cache_for_tests()  # simulate a restart too -- hot slot cleared

    calls: list[int] = []
    real_scan = setups_module._run_full_panel_scan

    def _counting_scan(*args, **kwargs):
        calls.append(1)
        return real_scan(*args, **kwargs)

    monkeypatch.setattr(setups_module, "_run_full_panel_scan", _counting_scan)

    recomputed = compute_setups(store, config)

    assert len(calls) == 1, "deleting the durable DB must cost exactly one recompute, never a crash"
    assert json.dumps(recomputed, sort_keys=True) == json.dumps(original, sort_keys=True)


def test_tc6_mutation_probe_a_durable_hit_is_returned_verbatim_never_silently_rescanned(tmp_path):
    """TC-6 (non-vacuous -- iter-3's lesson, named explicitly for J-06 in `docs/goal.md`'s
    BACKGROUND section): a durable row pre-seeded under the EXACT current key with a DELIBERATELY
    WRONG payload must be returned VERBATIM -- proving the durable-hit branch is genuinely read, not
    dead code a naive byte-identity assertion could pass vacuously (a bug that silently fell through
    to a fresh, CORRECT rescan would otherwise look identical to success)."""
    import app.research.setups as setups_module
    from app.research.edge_report_cache import _config_content_hash
    from app.research.setups import _store_signature
    from app.research.setups_scan_cache import SetupsScanCache, resolve_scan_cache_db_path, scan_cache_key

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()

    key = scan_cache_key(
        config_content_hash=_config_content_hash(config), store_signature=_store_signature(store),
    )
    wrong_payload = {"events": [{"id": "deliberately-wrong-fabricated-event", "fabricated": True}]}
    cache = SetupsScanCache(resolve_scan_cache_db_path(str(store.root)))
    cache.publish(key, wrong_payload)

    setups_module._reset_scan_cache_for_tests()  # force the durable tier to be the one that answers

    result = compute_setups(store, config)

    assert result == wrong_payload, (
        "a durable HIT must be served verbatim, never silently replaced by a fresh (correct) rescan"
    )


def test_tc8_durable_publish_failure_never_blocks_compute_setups_from_serving_the_fresh_scan(tmp_path):
    """TC-8: a corrupted/unusable durable cache DB file never raises out of ``compute_setups`` -- the
    publish failure is swallowed (``setups_scan_cache.py``'s own discipline) and the freshly-scanned
    (correct) result is still returned."""
    from app.research.setups_scan_cache import resolve_scan_cache_db_path

    store = BarStore(tmp_path / "bars")
    _seed_full(store)
    config = _syn_config()

    db_path = Path(resolve_scan_cache_db_path(str(store.root)))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_bytes(b"not a real sqlite database, just garbage bytes " * 20)

    result = compute_setups(store, config)  # must not raise

    assert len(result["events"]) >= 1, "the freshly-scanned (correct) result must still be served"
