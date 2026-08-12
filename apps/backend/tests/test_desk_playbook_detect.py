"""``desk_playbook_detect.py`` -- the opening-range-break detector pair (Era B2, J-01,
``docs/playbook-detector-spec.md`` §3.1-3.2): fixture goldens for the canonical firing case (TC-2),
the wide-OR near-miss (TC-3), the 1m->5m opening-range degrade on a firing signal (TC-4), the
both-sides ambiguous outside bar (TC-5), and the generic lookahead property test (TC-6) -- built
so J-04/J-05/J-06 extend ``_LOOKAHEAD_FIXTURES`` with their own detectors' fixtures without
touching the property test's own body.

**J-04 addendum.** ``detect_jbe``/``detect_dbi`` (spec §3.3-3.4) and ``detect_cup_handle`` (spec
§3.6) take a DIFFERENT call signature than ``detect_opening_range_breaks`` (no ``or_result``, no
``prior_close`` -- neither setup reads the opening range) -- extending the literal
``_LOOKAHEAD_FIXTURES`` list/test body below (which is hard-wired to
``detect_opening_range_breaks``'s own signature) would mean either a lossy tuple shape or touching
that test's own body, and TC-11/T-11 require the OR-break family's own tests to stay
byte-unmodified. This file instead adds a SECOND, otherwise-identical two-assertion harness
(``_CONTINUATION_LOOKAHEAD_FIXTURES`` for jbe/dbi, plus one direct pair of truncate/mutate tests
for ``cup_handle``) proving the SAME truncation-invariance + mutation-invariance property TC-6/TC-7
require, for every new detector's own canonical fixture -- the OR-break harness above is not
touched.

``detect_opening_range_breaks``/``detect_jbe``/``detect_dbi``/``detect_cup_handle`` are all tested
directly as pure functions of bars + hand-built ``baseline``/``index_baseline`` dicts --
``desk_playbook_features.py``'s primitives that would normally produce those dicts are already
covered by ``test_desk_playbook_features.py``; this file is detector logic only.
``test_desk_playbook.py`` separately proves the full bar-store-backed walk (``compute_playbook``)
wires the primitives into every detector correctly."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.providers.adapters.base import RawBar
from app.research.desk_playbook import playbook_parameters
from app.research.desk_playbook_features import zone_touches
from app.research.desk_playbook_detect import (
    detect_capitulation,
    detect_cup_handle,
    detect_dbi,
    detect_double_bottom,
    detect_double_top,
    detect_euphoria,
    detect_jbe,
    detect_opening_range_breaks,
    detect_range_trade,
)

SESSION_DATE = "2026-06-22"
E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _bar(symbol: str, epoch: float, o: float, h: float, low: float, c: float, v: int = 1000) -> RawBar:
    return RawBar(symbol, "5m", epoch, o, h, low, c, v)


_EMPTY_INDEX_BASELINE = {"mbr": 0.0, "sessions": 0, "slot_volume_medians": {}}
_NO_SPY_MARKET = {
    "direction": None, "market_move_mbr": None, "book_would_skip_market": False,
    "relative_strength_strong": False, "source": "SPY", "reason": "no SPY bars recorded for the session",
}


def _canonical_session_bars(symbol: str) -> list[RawBar]:
    """Slots 0-2: unremarkable pre-trigger bars (flat close, RVOL 0.5 vs the 1000-median baseline
    below -- deliberately non-decreasing and never surging, so the volume-into-trigger verdict is
    "constructive"). Slot 3: the trigger -- opens on the near side of or_high=101.0 ("level" entry,
    no chase gap), breaks only the high side. Slots 4-5: session tail (bars_to_close)."""
    return [
        _bar(symbol, E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
        _bar(symbol, E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar(symbol, E_OPEN + 900.0, 100.8, 101.5, 100.7, 101.2, 1000),  # trigger: breaks 101.0 high
        _bar(symbol, E_OPEN + 1200.0, 101.2, 101.4, 101.0, 101.1, 800),
        _bar(symbol, E_OPEN + 1500.0, 101.1, 101.3, 100.9, 101.0, 800),
    ]


_CANONICAL_OR = {"high": 101.0, "low": 100.0, "width": 1.0, "basis": "1m", "bars_used": 15}
_CANONICAL_BASELINE = {
    "mbr": 1.0, "sessions": 10,
    "slot_volume_medians": {0: 1000, 1: 1000, 2: 1000, 3: 1000, 4: 1000, 5: 1000},
}
_PARAMS = playbook_parameters()


def _detect_canonical(symbol: str = "OHB1", *, session_bars=None):
    bars = session_bars if session_bars is not None else _canonical_session_bars(symbol)
    return detect_opening_range_breaks(
        bars, _CANONICAL_OR, _CANONICAL_BASELINE, symbol, SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS, 100.0,
    )


# --- TC-2: the canonical firing fixture, every field hand-computed -------------------------------


def test_canonical_open_high_break_matches_the_hand_computed_signal():
    signal, diagnostic = _detect_canonical()
    assert diagnostic is None
    assert signal == {
        "symbol": "OHB1",
        "setup_id": "open_high_break",
        "side": "long",
        "trigger_ts": _iso(E_OPEN + 900.0),
        "trigger_price": 101.0,
        "entry": 101.0,
        "entry_kind": "level",
        "price_low": 100.0,
        "price_high": 101.0,
        "invalidation_price": pytest.approx(99.7),
        "geometry": {
            "or_high": 101.0,
            "or_low": 100.0,
            "or_width_mbr": pytest.approx(1.0),
            "or_bars_used": 15,
            "opening_range_basis": "1m",
            "slots_to_break": 3,
            "open_vs_prior_close_pct": pytest.approx(0.5),
        },
        "volume": {
            "rvol_trigger_bar": pytest.approx(1.0),
            "approach_rvol_max": pytest.approx(0.5),
            "spike_into_trigger_verdict": "constructive",
            "spiky_approach": False,
        },
        "market": _NO_SPY_MARKET,
        "principles": ["P4"],
        "disclosures": {
            "gapped_beyond_chase": False,
            "session_bar_count": 6,
            "attempt_count": 0,
            "bars_to_close": 2,
            "concurrent_signals": [],
            "euphoria_recent": False,
            "capitulation_recent": False,
        },
    }


def test_open_low_break_mirrors_the_high_side():
    """The mirror side: a session whose 5m bars only ever break DOWN through or_low, entry/
    invalidation/side all mirrored per spec §0."""
    bars = [
        _bar("OLB1", E_OPEN, 100.5, 100.9, 100.1, 100.4, 500),
        _bar("OLB1", E_OPEN + 300.0, 100.4, 100.9, 100.1, 100.4, 500),
        _bar("OLB1", E_OPEN + 600.0, 100.4, 100.9, 100.1, 100.4, 500),
        _bar("OLB1", E_OPEN + 900.0, 100.2, 100.3, 99.5, 99.8, 1000),  # trigger: breaks 100.0 low
        _bar("OLB1", E_OPEN + 1200.0, 99.8, 99.9, 99.6, 99.7, 800),
    ]
    signal, diagnostic = detect_opening_range_breaks(
        bars, _CANONICAL_OR, _CANONICAL_BASELINE, "OLB1", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS, None,
    )
    assert diagnostic is None
    assert signal["setup_id"] == "open_low_break"
    assert signal["side"] == "short"
    assert signal["trigger_price"] == 100.0
    # open=100.2 is still ABOVE T=100.0 -- the near (not-yet-crossed) side for a short breaking
    # DOWN through the level -- so the modeled fill is at the level itself, not the open.
    assert signal["entry"] == 100.0
    assert signal["entry_kind"] == "level"
    assert signal["invalidation_price"] == pytest.approx(101.3)  # or_high + 0.30*(or_high-or_low)
    assert signal["geometry"]["open_vs_prior_close_pct"] is None  # prior_close=None -> honest null


# --- TC-3: the wide-OR near-miss -- zero signals regardless of what the bars do afterward --------


def test_wide_opening_range_fires_no_signal():
    wide_or = {"high": 105.0, "low": 100.0, "width": 5.0, "basis": "1m", "bars_used": 15}
    bars = [
        _bar("WIDE", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
        _bar("WIDE", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar("WIDE", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar("WIDE", E_OPEN + 900.0, 100.8, 106.0, 100.7, 105.5, 1000),  # would break 105 if checked
    ]
    signal, diagnostic = detect_opening_range_breaks(
        bars, wide_or, _CANONICAL_BASELINE, "WIDE", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS, None,
    )
    assert signal is None
    assert diagnostic is None


# --- TC-4: the 5m-basis opening range on an otherwise-firing signal --------------------------------


def test_5m_basis_opening_range_still_fires_with_the_basis_disclosed():
    five_min_or = {"high": 101.0, "low": 100.0, "width": 1.0, "basis": "5m", "bars_used": 3}
    signal, diagnostic = detect_opening_range_breaks(
        _canonical_session_bars("OR5M"), five_min_or, _CANONICAL_BASELINE, "OR5M", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS, None,
    )
    assert diagnostic is None
    assert signal["geometry"]["opening_range_basis"] == "5m"
    assert signal["geometry"]["or_bars_used"] == 3
    assert signal["trigger_price"] == 101.0  # geometry unaffected by the basis itself


# --- TC-5: a bar strictly breaking both OR sides, neither previously broken -----------------------


def test_ambiguous_outside_bar_fires_no_signal_and_records_a_diagnostic():
    bars = [
        _bar("AMBIG", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
        _bar("AMBIG", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar("AMBIG", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar("AMBIG", E_OPEN + 900.0, 100.5, 102.0, 99.0, 100.5, 1000),  # breaks BOTH 101 and 100
    ]
    signal, diagnostic = detect_opening_range_breaks(
        bars, _CANONICAL_OR, _CANONICAL_BASELINE, "AMBIG", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS, None,
    )
    assert signal is None
    assert diagnostic == {
        "symbol": "AMBIG", "diagnostic": "ambiguous_outside_bar", "at_utc": _iso(E_OPEN + 900.0),
    }


def test_a_session_that_never_breaks_either_side_fires_nothing():
    bars = [
        _bar("QUIET", E_OPEN, 100.5, 100.9, 100.1, 100.6, 500),
        _bar("QUIET", E_OPEN + 300.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar("QUIET", E_OPEN + 600.0, 100.6, 100.9, 100.1, 100.6, 500),
        _bar("QUIET", E_OPEN + 900.0, 100.6, 100.9, 100.2, 100.5, 500),  # stays inside [100, 101]
    ]
    signal, diagnostic = detect_opening_range_breaks(
        bars, _CANONICAL_OR, _CANONICAL_BASELINE, "QUIET", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS, None,
    )
    assert signal is None
    assert diagnostic is None


# --- audit T3: the detector's populated-SPY branches -------------------------------------------------
# Every fixture above passes `index_bars=[]` -- only the no-SPY-bars null branch ever ran. These two
# exercise a REAL, non-empty SPY 5m series: a trigger late enough in the session (slot 10) for
# `market_context`'s lookback window (needs >= PLAYBOOK_MKT_LOOKBACK_BARS+1 == 7 prior SPY bars) to
# resolve at all.


def test_market_context_populated_spy_reports_a_supportive_direction():
    """A clearly rising SPY beside a long trigger -- `direction` resolves non-null, and specifically
    "supportive" (SPY moved > the neutral band, signed with the signal's own long side)."""
    bars = [_bar("RS2", E_OPEN + i * 300.0, 100.1, 100.3, 100.0, 100.2, 500) for i in range(10)]
    bars.append(_bar("RS2", E_OPEN + 10 * 300.0, 100.6, 101.2, 100.5, 101.0, 1000))  # slot 10: trigger

    spy_bars = [
        _bar(
            "SPY", E_OPEN + i * 300.0,
            400.0 + i * 0.3, 400.2 + i * 0.3, 399.9 + i * 0.3, 400.1 + i * 0.3, 500,
        )
        for i in range(10)
    ]
    or_result = {"high": 100.3, "low": 100.0, "width": 0.3, "basis": "1m", "bars_used": 15}
    baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 500 for i in range(11)}}
    index_baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {}}

    signal, diagnostic = detect_opening_range_breaks(
        bars, or_result, baseline, "RS2", SESSION_DATE, spy_bars, index_baseline, _PARAMS, None,
    )
    assert diagnostic is None and signal is not None
    assert signal["market"]["direction"] == "supportive"
    assert signal["market"]["market_move_mbr"] == pytest.approx(1.8)
    assert signal["market"]["reason"] is None


def test_market_context_relative_strength_strong_when_stock_high_and_spy_low():
    """The stock closing near its own session-high-so-far while SPY closes near ITS OWN
    session-low-so-far -- `relative_strength_strong: True` for a long (spec Sec0)."""
    bars = [_bar("RS1", E_OPEN + i * 300.0, 100.1, 100.3, 100.0, 100.2, 500) for i in range(9)]
    bars.append(_bar("RS1", E_OPEN + 9 * 300.0, 100.3, 100.5, 100.1, 100.45, 500))  # near its own high
    bars.append(_bar("RS1", E_OPEN + 10 * 300.0, 100.6, 101.2, 100.5, 101.0, 1000))  # slot 10: trigger

    spy_bars = [
        _bar(
            "SPY", E_OPEN + i * 300.0,
            400.3 - i * 0.1, 400.5 - i * 0.1, 400.1 - i * 0.1, 400.2 - i * 0.1, 500,
        )
        for i in range(9)
    ]
    spy_bars.append(_bar("SPY", E_OPEN + 9 * 300.0, 399.4, 399.6, 399.0, 399.05, 500))  # near its own low

    or_result = {"high": 100.3, "low": 100.0, "width": 0.3, "basis": "1m", "bars_used": 15}
    baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 500 for i in range(11)}}
    index_baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {}}

    signal, diagnostic = detect_opening_range_breaks(
        bars, or_result, baseline, "RS1", SESSION_DATE, spy_bars, index_baseline, _PARAMS, None,
    )
    assert diagnostic is None and signal is not None
    assert signal["market"]["direction"] is not None  # a real, populated-SPY market block
    assert signal["market"]["relative_strength_strong"] is True


# --- TC-6: the generic lookahead property test -----------------------------------------------------
#
# Registered fixtures, each ``(session_bars, or_result, baseline, symbol, index_bars,
# index_baseline, prior_close, trigger_idx)`` -- J-04/J-05/J-06 extend this list with their OWN
# detector's canonical-firing fixtures (and their own detect_* call, parametrized alongside) WITHOUT
# touching the two assertion bodies below.

_LOOKAHEAD_FIXTURES = [
    (
        _canonical_session_bars("LOOK1"), _CANONICAL_OR, _CANONICAL_BASELINE, "LOOK1",
        [], _EMPTY_INDEX_BASELINE, 100.0, 3,
    ),
]


@pytest.mark.parametrize("bars, or_result, baseline, symbol, index_bars, index_baseline, prior_close, trigger_idx", _LOOKAHEAD_FIXTURES)
def test_truncating_to_the_trigger_bar_reproduces_the_core_detection_fields(
    bars, or_result, baseline, symbol, index_bars, index_baseline, prior_close, trigger_idx
):
    """``detect(bars[:trigger_index+1])`` must reproduce the SAME trigger_price, invalidation_price
    and geometry as the full-session call -- these are the fields a genuinely lookahead-clean
    detection can never depend on bars after the trigger for. (``bars_to_close`` legitimately
    differs under truncation -- it describes how much of the session remains, not a detection
    decision -- so it is deliberately excluded from this comparison; the MUTATION variant below
    proves the whole signal, including disclosures, is unaffected when nothing about the session's
    LENGTH changes.)"""
    full_signal, _ = detect_opening_range_breaks(
        bars, or_result, baseline, symbol, SESSION_DATE, index_bars, index_baseline,
        _PARAMS, prior_close,
    )
    assert full_signal is not None

    truncated_signal, _ = detect_opening_range_breaks(
        bars[: trigger_idx + 1], or_result, baseline, symbol, SESSION_DATE, index_bars,
        index_baseline, _PARAMS, prior_close,
    )
    assert truncated_signal is not None
    assert truncated_signal["trigger_price"] == full_signal["trigger_price"]
    assert truncated_signal["invalidation_price"] == full_signal["invalidation_price"]
    assert truncated_signal["geometry"] == full_signal["geometry"]


@pytest.mark.parametrize("bars, or_result, baseline, symbol, index_bars, index_baseline, prior_close, trigger_idx", _LOOKAHEAD_FIXTURES)
def test_mutating_a_bar_after_the_trigger_changes_nothing(
    bars, or_result, baseline, symbol, index_bars, index_baseline, prior_close, trigger_idx
):
    """Mutating any bar strictly AFTER the trigger index (same session length, different values)
    must leave the detected signal byte-identical -- proving no disclosure secretly reads ahead."""
    original_signal, _ = detect_opening_range_breaks(
        bars, or_result, baseline, symbol, SESSION_DATE, index_bars, index_baseline,
        _PARAMS, prior_close,
    )
    assert original_signal is not None
    assert trigger_idx + 1 < len(bars), "fixture must carry at least one bar after the trigger"

    mutated = list(bars)
    victim = mutated[trigger_idx + 1]
    mutated[trigger_idx + 1] = RawBar(
        victim.symbol, victim.timeframe, victim.epoch,
        victim.open * 3.0, victim.high * 5.0, victim.low * 0.2, victim.close * 4.0, victim.volume * 50,
    )
    mutated_signal, mutated_diagnostic = detect_opening_range_breaks(
        mutated, or_result, baseline, symbol, SESSION_DATE, index_bars, index_baseline,
        _PARAMS, prior_close,
    )
    assert mutated_diagnostic is None
    assert mutated_signal == original_signal


# === J-04: the continuation family -- jbe (TC-1, TC-4) / dbi (TC-2, TC-5) =========================
#
# A tight, hand-computed base+jump: 6 flat lookback bars (slots 0-5, deliberate volume surge on the
# LAST one) then a 3-bar base (slots 6-8, tight range, dry volume) then a trigger at slot 9. Every
# earlier candidate trigger bar the detector's own rolling search visits is deliberately unable to
# find a qualifying (base, jump) pair -- either the base window it finds swallows part of the
# lookback leg (range too wide) or there aren't yet enough bars before the candidate base start for
# a full jump-lookback window -- so slot 9 is the unique, deterministic firing point (verified by
# direct execution, not just by inspection).

_CONTINUATION_BASELINE = {
    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(12)},
}


def _canonical_jbe_bars(symbol: str = "JBE1") -> list[RawBar]:
    return [
        _bar(symbol, E_OPEN, 98.4, 98.5, 98.0, 98.3, 1200),
        _bar(symbol, E_OPEN + 300.0, 98.3, 98.4, 98.1, 98.3, 1200),
        _bar(symbol, E_OPEN + 600.0, 98.3, 98.4, 98.05, 98.3, 1200),
        _bar(symbol, E_OPEN + 900.0, 98.3, 98.45, 98.2, 98.3, 1200),
        _bar(symbol, E_OPEN + 1200.0, 98.3, 98.4, 98.15, 98.3, 1200),
        _bar(symbol, E_OPEN + 1500.0, 98.3, 98.5, 98.3, 98.4, 3000),  # lookback volume surge
        _bar(symbol, E_OPEN + 1800.0, 103.5, 103.8, 103.2, 103.6, 400),  # base bar 1
        _bar(symbol, E_OPEN + 2100.0, 103.6, 104.0, 103.3, 103.7, 500),  # base bar 2
        _bar(symbol, E_OPEN + 2400.0, 103.7, 103.9, 103.4, 103.8, 450),  # base bar 3
        _bar(symbol, E_OPEN + 2700.0, 103.9, 104.8, 103.8, 104.5, 1500),  # trigger: breaks U=104.0
        _bar(symbol, E_OPEN + 3000.0, 104.5, 104.7, 104.3, 104.6, 900),
        _bar(symbol, E_OPEN + 3300.0, 104.6, 104.8, 104.4, 104.7, 900),
    ]


def _canonical_dbi_bars(symbol: str = "DBI1") -> list[RawBar]:
    """The exact mirror of ``_canonical_jbe_bars``: a high lookback, a tight base near a LOWER
    level, and a trigger breaking DOWN through the base's own low."""
    return [
        _bar(symbol, E_OPEN, 109.6, 110.0, 109.5, 109.7, 1200),
        _bar(symbol, E_OPEN + 300.0, 109.7, 109.9, 109.6, 109.7, 1200),
        _bar(symbol, E_OPEN + 600.0, 109.7, 109.95, 109.6, 109.7, 1200),
        _bar(symbol, E_OPEN + 900.0, 109.7, 109.8, 109.55, 109.7, 1200),
        _bar(symbol, E_OPEN + 1200.0, 109.7, 109.85, 109.6, 109.7, 1200),
        _bar(symbol, E_OPEN + 1500.0, 109.6, 109.7, 109.5, 109.6, 3000),  # lookback volume surge
        _bar(symbol, E_OPEN + 1800.0, 104.5, 104.8, 104.2, 104.4, 400),  # base bar 1
        _bar(symbol, E_OPEN + 2100.0, 104.4, 104.7, 104.0, 104.3, 500),  # base bar 2
        _bar(symbol, E_OPEN + 2400.0, 104.3, 104.6, 104.1, 104.2, 450),  # base bar 3
        _bar(symbol, E_OPEN + 2700.0, 104.1, 104.2, 103.2, 103.5, 1500),  # trigger: breaks L=104.0
        _bar(symbol, E_OPEN + 3000.0, 103.5, 103.7, 103.3, 103.4, 900),
        _bar(symbol, E_OPEN + 3300.0, 103.4, 103.6, 103.2, 103.3, 900),
    ]


def test_canonical_jbe_matches_the_hand_computed_signal():
    """TC-1: the canonical JBE firing -- setup chip, side, and every geometry field hand-verified
    (values confirmed by direct execution against the fixture, per the module-level note above)."""
    results = detect_jbe(
        _canonical_jbe_bars(), _CONTINUATION_BASELINE, "JBE1", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert len(results) == 1
    signal = results[0]
    assert signal["setup_id"] == "jbe"
    assert signal["side"] == "long"
    assert signal["trigger_price"] == 104.0
    assert signal["entry"] == 104.0
    assert signal["entry_kind"] == "level"
    assert signal["price_low"] == pytest.approx(103.2)
    assert signal["price_high"] == 104.0
    assert signal["invalidation_price"] == pytest.approx(102.96)
    geometry = signal["geometry"]
    assert geometry["slots_to_break"] == 9
    assert geometry["jump_mbr"] == pytest.approx(6.0)
    assert geometry["base_range_mbr"] == pytest.approx(0.8)
    assert geometry["base_bars"] == 3
    assert geometry["base_flatline"] is True
    assert geometry["base_lows_ascending"] is True
    assert geometry["ladder_step_ratio"] is None
    assert signal["volume"]["rvol_trigger_bar"] == pytest.approx(1.5)
    assert signal["principles"] == ["P3", "P4"]
    assert signal["disclosures"]["bars_to_close"] == 2
    assert signal["disclosures"]["concurrent_signals"] == []


def test_canonical_dbi_mirrors_the_jbe_fixture():
    """TC-2: the exact mirror -- short side, invalidation ABOVE the base, geometry magnitudes
    identical to the JBE canonical (same shape, direction-flipped)."""
    results = detect_dbi(
        _canonical_dbi_bars(), _CONTINUATION_BASELINE, "DBI1", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert len(results) == 1
    signal = results[0]
    assert signal["setup_id"] == "dbi"
    assert signal["side"] == "short"
    assert signal["trigger_price"] == 104.0
    assert signal["entry"] == 104.0
    assert signal["entry_kind"] == "level"
    assert signal["invalidation_price"] == pytest.approx(105.04)
    geometry = signal["geometry"]
    assert geometry["slots_to_break"] == 9
    assert geometry["jump_mbr"] == pytest.approx(6.0)
    assert geometry["base_range_mbr"] == pytest.approx(0.8)
    assert geometry["base_bars"] == 3
    assert geometry["base_flatline"] is True
    assert geometry["base_lows_ascending"] is True  # mirrored meaning: base HIGHS non-increasing
    assert geometry["ladder_step_ratio"] is None
    assert signal["principles"] == ["P3", "P4"]


# --- TC-4 / TC-5: the near-miss fixtures, rebuilt by the goal-playbook-iter-4 audit -------------
#
# The near-miss pair MUST fail on the jump gate itself and on nothing else. The original fixtures
# did not: `consolidation_range` is the MAXIMAL window ending at `t-1`, and because their lookback
# leg sat within `base_max_range_mbr` of the base, that window swallowed the whole leg back to
# bar 0, so every candidate `t` was rejected at `start_idx - jump_lookback_bars < 0` and the jump
# gate was never reached (re-running them with BOTH jump gates zeroed still produced zero signals
# -- the definition of a test that passes for the wrong reason). These fixtures keep the lookback
# leg far enough below the base (> `base_max_range_mbr` MBR) that the maximal window stops at the
# base's own first bar, so the formation reaches the jump gate with a real, hand-computed jump of
# 2.4 MBR -- under the `jump_min_move_mbr` (3.0) floor, and nothing else failing. Each test proves
# that by ALSO running the identical bars with only the two jump gates relaxed: exactly one signal
# then fires, at the same slot, so the gate is provably the decisive rejecter.
#
# Note (audit): with `base_max_range_mbr` = 2.0 and `jump_min_move_mbr` = 3.0, the BOOK ratio gate
# (`jump >= jump_min_mult * base_range`, 1.5x) can never reject ALONE -- any base range is <= 2.0
# MBR, so 1.5 x base_range <= 3.0 MBR <= any jump that clears the floor. The near-miss therefore
# fails the floor, which is the only independently reachable half of TC-4's "jump too small".

_JUMP_GATES_RELAXED = {**_PARAMS, "jump_min_mult": 0.0, "jump_min_move_mbr": 0.0}


def _jbe_near_miss_bars() -> list[RawBar]:
    """A valid, tight 3-bar base (slots 6-8, U = 100.0, range 0.5 MBR) reached by a jump of only
    2.4 MBR from the 6 lookback bars before it (slots 0-5) -- under the 3.0-MBR floor. Slot 9
    would break U; slots 10-11 never exceed the rolling base high, so no later firing exists."""
    return [
        _bar("JBENM", E_OPEN, 97.9, 98.0, 97.7, 97.9, 1200),
        _bar("JBENM", E_OPEN + 300.0, 97.9, 98.0, 97.75, 97.9, 1200),
        _bar("JBENM", E_OPEN + 600.0, 97.9, 98.0, 97.6, 97.9, 1200),  # jump low = 97.6
        _bar("JBENM", E_OPEN + 900.0, 97.9, 98.0, 97.7, 97.9, 1200),
        _bar("JBENM", E_OPEN + 1200.0, 97.9, 98.0, 97.7, 97.9, 1200),
        _bar("JBENM", E_OPEN + 1500.0, 97.9, 98.0, 97.8, 97.95, 3000),  # lookback volume surge
        _bar("JBENM", E_OPEN + 1800.0, 99.6, 99.9, 99.5, 99.7, 400),  # base bar 1
        _bar("JBENM", E_OPEN + 2100.0, 99.7, 100.0, 99.55, 99.8, 500),  # base bar 2 -- U = 100.0
        _bar("JBENM", E_OPEN + 2400.0, 99.8, 99.95, 99.6, 99.9, 450),  # base bar 3
        _bar("JBENM", E_OPEN + 2700.0, 99.9, 100.8, 99.85, 100.5, 1500),  # would break U = 100.0
        _bar("JBENM", E_OPEN + 3000.0, 100.5, 100.6, 100.3, 100.4, 900),
        _bar("JBENM", E_OPEN + 3300.0, 100.4, 100.5, 100.2, 100.3, 900),
    ]


def _dbi_near_miss_bars() -> list[RawBar]:
    """The exact mirror: a tight base (slots 6-8, L = 100.0) reached by a 2.4-MBR drop from the
    lookback leg's own high (102.4) -- under the same 3.0-MBR floor."""
    return [
        _bar("DBINM", E_OPEN, 102.1, 102.3, 102.0, 102.1, 1200),
        _bar("DBINM", E_OPEN + 300.0, 102.1, 102.3, 102.05, 102.1, 1200),
        _bar("DBINM", E_OPEN + 600.0, 102.1, 102.4, 102.0, 102.1, 1200),  # jump high = 102.4
        _bar("DBINM", E_OPEN + 900.0, 102.1, 102.3, 102.0, 102.1, 1200),
        _bar("DBINM", E_OPEN + 1200.0, 102.1, 102.3, 102.0, 102.1, 1200),
        _bar("DBINM", E_OPEN + 1500.0, 102.1, 102.2, 102.0, 102.05, 3000),  # lookback volume surge
        _bar("DBINM", E_OPEN + 1800.0, 100.4, 100.5, 100.1, 100.3, 400),  # base bar 1
        _bar("DBINM", E_OPEN + 2100.0, 100.3, 100.45, 100.0, 100.2, 500),  # base bar 2 -- L = 100.0
        _bar("DBINM", E_OPEN + 2400.0, 100.2, 100.4, 100.05, 100.1, 450),  # base bar 3
        _bar("DBINM", E_OPEN + 2700.0, 100.1, 100.15, 99.2, 99.5, 1500),  # would break L = 100.0
        _bar("DBINM", E_OPEN + 3000.0, 99.5, 99.7, 99.4, 99.6, 900),
        _bar("DBINM", E_OPEN + 3300.0, 99.6, 99.8, 99.5, 99.7, 900),
    ]


def test_jbe_near_miss_jump_too_small_fires_no_signal():
    """TC-4: a fully-formed, volume-clean base that WOULD trigger, silenced by the jump gate alone
    (jump 2.4 MBR < the 3.0-MBR ``jump_min_move_mbr`` floor)."""
    bars = _jbe_near_miss_bars()
    results = detect_jbe(
        bars, _CONTINUATION_BASELINE, "JBENM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert results == []

    # The control: with ONLY the two jump gates relaxed, the identical bars fire exactly one
    # signal -- so every OTHER gate passed and the jump gate is provably what silenced it.
    relaxed = detect_jbe(
        bars, _CONTINUATION_BASELINE, "JBENM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE,
        _JUMP_GATES_RELAXED,
    )
    assert len(relaxed) == 1
    assert relaxed[0]["geometry"]["slots_to_break"] == 9
    assert relaxed[0]["geometry"]["jump_mbr"] == pytest.approx(2.4)
    assert relaxed[0]["geometry"]["jump_mbr"] < _PARAMS["jump_min_move_mbr"]


def test_dbi_near_miss_mirrors_the_jbe_near_miss():
    """TC-5: the mirrored gate failure -- the same 2.4-MBR jump, short side, same control."""
    bars = _dbi_near_miss_bars()
    results = detect_dbi(
        bars, _CONTINUATION_BASELINE, "DBINM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert results == []

    relaxed = detect_dbi(
        bars, _CONTINUATION_BASELINE, "DBINM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE,
        _JUMP_GATES_RELAXED,
    )
    assert len(relaxed) == 1
    assert relaxed[0]["geometry"]["slots_to_break"] == 9
    assert relaxed[0]["geometry"]["jump_mbr"] == pytest.approx(2.4)
    assert relaxed[0]["geometry"]["jump_mbr"] < _PARAMS["jump_min_move_mbr"]


def test_jbe_ladder_two_firings_draw_independent_bases_and_disclose_the_step_ratio():
    """TC-8 (detector level): a second, independent base+jump+trigger AFTER the first trigger bar
    fires a second ``jbe`` signal, capped at
    ``PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION`` (2) -- ``ladder_step_ratio`` is null on the first
    firing and the (second jump / first jump) ratio on the second. ``test_desk_playbook.py`` proves
    the SAME two-firing shape draws independent, non-colliding baseline anchors through the full
    ``compute_playbook`` walk."""
    bars = _canonical_jbe_bars("LADDER")[:10]  # step 1 only, through its own trigger bar (index 9)
    bars += [
        _bar("LADDER", E_OPEN + 3000.0, 104.5, 104.6, 104.3, 104.4, 1200),
        _bar("LADDER", E_OPEN + 3300.0, 104.4, 104.5, 104.2, 104.3, 1200),
        _bar("LADDER", E_OPEN + 3600.0, 104.3, 104.4, 104.1, 104.2, 1200),
        _bar("LADDER", E_OPEN + 3900.0, 104.2, 104.3, 104.0, 104.1, 1200),
        _bar("LADDER", E_OPEN + 4200.0, 104.1, 104.2, 103.9, 104.0, 1200),
        _bar("LADDER", E_OPEN + 4500.0, 104.0, 104.3, 103.9, 104.2, 3000),  # step-2 lookback surge
        _bar("LADDER", E_OPEN + 4800.0, 107.5, 107.8, 107.2, 107.6, 400),
        _bar("LADDER", E_OPEN + 5100.0, 107.6, 108.0, 107.3, 107.7, 500),
        _bar("LADDER", E_OPEN + 5400.0, 107.7, 107.9, 107.4, 107.8, 450),
        _bar("LADDER", E_OPEN + 5700.0, 107.9, 108.8, 107.8, 108.5, 1500),  # step 2 trigger
        _bar("LADDER", E_OPEN + 6000.0, 108.5, 108.7, 108.3, 108.6, 900),
        _bar("LADDER", E_OPEN + 6300.0, 108.6, 108.8, 108.4, 108.7, 900),
    ]
    baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(22)}}
    results = detect_jbe(bars, baseline, "LADDER", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
    assert len(results) == 2
    step1, step2 = results
    assert step1["geometry"]["slots_to_break"] == 9
    assert step1["geometry"]["ladder_step_ratio"] is None
    assert step2["geometry"]["slots_to_break"] == 19
    # a genuinely SECOND base -- starts strictly after step 1's own trigger bar
    assert step2["geometry"]["slots_to_break"] > step1["geometry"]["slots_to_break"]
    assert step2["geometry"]["ladder_step_ratio"] == pytest.approx(
        step2["geometry"]["jump_mbr"] / step1["geometry"]["jump_mbr"]
    )


# --- J-04: the continuation family's own truncate/mutate lookahead property test (TC-7) ----------

_CONTINUATION_LOOKAHEAD_FIXTURES = [
    (detect_jbe, _canonical_jbe_bars(), "JBE1"),
    (detect_dbi, _canonical_dbi_bars(), "DBI1"),
]


@pytest.mark.parametrize("detect_fn, bars, symbol", _CONTINUATION_LOOKAHEAD_FIXTURES)
def test_continuation_truncating_to_the_trigger_bar_reproduces_the_core_detection_fields(
    detect_fn, bars, symbol
):
    full = detect_fn(bars, _CONTINUATION_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
    assert len(full) == 1
    trigger_idx = full[0]["geometry"]["slots_to_break"]

    truncated = detect_fn(
        bars[: trigger_idx + 1], _CONTINUATION_BASELINE, symbol, SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert len(truncated) == 1
    assert truncated[0]["trigger_price"] == full[0]["trigger_price"]
    assert truncated[0]["invalidation_price"] == full[0]["invalidation_price"]
    assert truncated[0]["geometry"] == full[0]["geometry"]


@pytest.mark.parametrize("detect_fn, bars, symbol", _CONTINUATION_LOOKAHEAD_FIXTURES)
def test_continuation_mutating_a_bar_after_the_trigger_changes_nothing(detect_fn, bars, symbol):
    full = detect_fn(bars, _CONTINUATION_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
    assert len(full) == 1
    trigger_idx = full[0]["geometry"]["slots_to_break"]
    assert trigger_idx + 1 < len(bars), "fixture must carry at least one bar after the trigger"

    mutated = list(bars)
    victim = mutated[trigger_idx + 1]
    mutated[trigger_idx + 1] = RawBar(
        victim.symbol, victim.timeframe, victim.epoch,
        victim.open * 3.0, victim.high * 5.0, victim.low * 0.2, victim.close * 4.0, victim.volume * 50,
    )
    mutated_result = detect_fn(
        mutated, _CONTINUATION_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert mutated_result == full


# === J-04: cup_handle (TC-3, TC-6) =================================================================


def _canonical_cup_handle_bars(symbol: str = "CUP1", handle_ohlcv=None) -> list[RawBar]:
    """Left rim (slot 3) -- decline to a cup bottom (slot 9, low=105.0) -- right rim (slot 15,
    matching the left rim exactly) -- a 3-bar handle (slots 16-18, the pivot's own confirmation
    window) -- trigger at slot 19 (the first bar legally allowed to use the confirmed right rim)."""
    if handle_ohlcv is None:
        handle_ohlcv = [
            (109.6, 109.3, 108.0, 108.5, 400),
            (108.5, 109.0, 107.8, 108.2, 400),
            (108.2, 109.4, 108.0, 108.9, 400),
        ]
    bars = [
        _bar(symbol, E_OPEN, 106.5, 107.0, 106.0, 106.8, 500),
        _bar(symbol, E_OPEN + 300.0, 106.8, 108.0, 106.5, 107.5, 500),
        _bar(symbol, E_OPEN + 600.0, 107.5, 109.0, 107.0, 108.5, 500),
        _bar(symbol, E_OPEN + 900.0, 108.5, 110.0, 108.0, 109.5, 1000),  # LEFT RIM
        _bar(symbol, E_OPEN + 1200.0, 109.5, 109.0, 108.0, 108.5, 1000),
        _bar(symbol, E_OPEN + 1500.0, 108.5, 108.0, 107.0, 107.5, 1000),
        _bar(symbol, E_OPEN + 1800.0, 107.5, 107.5, 106.5, 107.0, 1000),
        _bar(symbol, E_OPEN + 2100.0, 107.0, 106.5, 106.0, 106.2, 300),
        _bar(symbol, E_OPEN + 2400.0, 106.2, 106.0, 105.5, 105.8, 300),
        _bar(symbol, E_OPEN + 2700.0, 105.8, 105.5, 105.0, 105.2, 300),  # cup bottom low=105.0
        _bar(symbol, E_OPEN + 3000.0, 105.2, 106.0, 105.1, 105.8, 300),
        _bar(symbol, E_OPEN + 3300.0, 105.8, 107.0, 105.5, 106.8, 300),
        _bar(symbol, E_OPEN + 3600.0, 106.8, 108.0, 106.5, 107.8, 1000),
        _bar(symbol, E_OPEN + 3900.0, 107.8, 109.0, 107.5, 108.8, 1000),
        _bar(symbol, E_OPEN + 4200.0, 108.8, 109.5, 108.5, 109.2, 1000),
        _bar(symbol, E_OPEN + 4500.0, 109.2, 110.0, 108.8, 109.6, 1000),  # RIGHT RIM
    ]
    for i, (o, h, l, c, v) in enumerate(handle_ohlcv, start=16):
        bars.append(_bar(symbol, E_OPEN + i * 300.0, o, h, l, c, v))
    next_i = 16 + len(handle_ohlcv)
    bars.append(_bar(symbol, E_OPEN + next_i * 300.0, 108.9, 110.5, 108.7, 110.2, 1500))  # trigger
    bars.append(_bar(symbol, E_OPEN + (next_i + 1) * 300.0, 110.2, 110.4, 109.9, 110.1, 900))
    bars.append(_bar(symbol, E_OPEN + (next_i + 2) * 300.0, 110.1, 110.3, 109.8, 110.0, 900))
    return bars


_CUP_HANDLE_BASELINE = {
    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(25)},
}


def test_canonical_cup_handle_matches_the_hand_computed_signal():
    """TC-3: the canonical cup-and-handle firing -- rims, cup depth/duration, handle retrace/
    duration, and the three RVOL medians hand-verified (values confirmed by direct execution)."""
    signal = detect_cup_handle(
        _canonical_cup_handle_bars(), _CUP_HANDLE_BASELINE, "CUP1", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert signal is not None
    assert signal["setup_id"] == "cup_handle"
    assert signal["side"] == "long"
    assert signal["trigger_price"] == 110.0
    assert signal["entry"] == 110.0
    assert signal["entry_kind"] == "level"
    assert signal["price_low"] == pytest.approx(105.0)
    assert signal["invalidation_price"] == pytest.approx(107.14)
    geometry = signal["geometry"]
    assert geometry["slots_to_break"] == 19
    assert geometry["cup_bars"] == 12
    assert geometry["cup_depth_mbr"] == pytest.approx(5.0)
    assert geometry["handle_retrace_frac"] == pytest.approx(0.44)
    assert geometry["handle_duration_frac"] == pytest.approx(0.25)
    assert geometry["cup_optimal"] is True
    assert geometry["handle_duration_desirable"] is True
    assert geometry["cup_middle_third_rvol_median"] == pytest.approx(0.3)
    assert geometry["cup_outer_third_rvol_median"] == pytest.approx(1.0)
    assert geometry["handle_rvol_median"] == pytest.approx(0.4)
    assert signal["principles"] == ["P4", "P5-inverse"]


def test_cup_handle_near_miss_handle_retrace_beyond_50pct_fires_no_signal():
    """TC-6: the SAME cup, but the handle dips well past 50% of cup depth before the rim ever
    breaks -- voids silently even though a later bar still crosses the rim price."""
    near_miss_handle = [
        (109.6, 109.0, 105.5, 106.0, 400),  # retrace to 105.5 -- 90% of a 5.0 cup depth
        (106.0, 106.5, 105.6, 106.2, 400),
        (106.2, 106.8, 106.0, 106.5, 400),
    ]
    bars = _canonical_cup_handle_bars("CUPNM", handle_ohlcv=near_miss_handle)
    signal = detect_cup_handle(
        bars, _CUP_HANDLE_BASELINE, "CUPNM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert signal is None


def test_cup_handle_truncating_to_the_trigger_bar_reproduces_the_core_detection_fields():
    """TC-7: the same truncation-invariance property, for ``cup_handle``."""
    bars = _canonical_cup_handle_bars()
    full = detect_cup_handle(
        bars, _CUP_HANDLE_BASELINE, "CUP1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert full is not None
    trigger_idx = full["geometry"]["slots_to_break"]

    truncated = detect_cup_handle(
        bars[: trigger_idx + 1], _CUP_HANDLE_BASELINE, "CUP1", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert truncated is not None
    assert truncated["trigger_price"] == full["trigger_price"]
    assert truncated["invalidation_price"] == full["invalidation_price"]
    assert truncated["geometry"] == full["geometry"]


def test_cup_handle_mutating_a_bar_after_the_trigger_changes_nothing():
    """TC-7: mutation-invariance for ``cup_handle``."""
    bars = _canonical_cup_handle_bars()
    full = detect_cup_handle(
        bars, _CUP_HANDLE_BASELINE, "CUP1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert full is not None
    trigger_idx = full["geometry"]["slots_to_break"]
    assert trigger_idx + 1 < len(bars), "fixture must carry at least one bar after the trigger"

    mutated = list(bars)
    victim = mutated[trigger_idx + 1]
    mutated[trigger_idx + 1] = RawBar(
        victim.symbol, victim.timeframe, victim.epoch,
        victim.open * 3.0, victim.high * 5.0, victim.low * 0.2, victim.close * 4.0, victim.volume * 50,
    )
    mutated_result = detect_cup_handle(
        mutated, _CUP_HANDLE_BASELINE, "CUP1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert mutated_result == full


# === J-05: the climax family -- capitulation (TC-1, TC-2, TC-6, TC-7) / euphoria marker (TC-3) ====
#
# A 4-bar reference-then-decline leg (slot 0 the pre-window close reference, slots 1-3 the
# `PLAYBOOK_VERTICAL_WINDOW_BARS`-bar vertical decline itself, climax bar at slot 3 with the
# volume surge `vertical_move`'s `require_volume` clause needs) followed by a trigger bar at slot 4
# whose high exceeds slot 3's own high -- values hand-computed and cross-checked by direct
# execution (this module's own convention, per the JBE/DBI/cup_handle fixtures above).

_CAPITULATION_BASELINE = {
    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(9)},
}


def _canonical_capitulation_bars(symbol: str = "CAP1") -> list[RawBar]:
    """No re-anchoring: the climax bar (slot 3) already holds the session's lowest low, and slot
    4's low never dips below it -- the re-anchoring fixture right below this one is the ONE that
    exercises the "a new low after v re-anchors v" clause."""
    return [
        _bar(symbol, E_OPEN, 104.1, 104.3, 103.9, 104.0, 1000),
        _bar(symbol, E_OPEN + 300.0, 104.0, 104.1, 102.4, 102.5, 1000),  # window start (slot 1)
        _bar(symbol, E_OPEN + 600.0, 102.5, 102.6, 100.9, 101.0, 1200),
        _bar(symbol, E_OPEN + 900.0, 101.0, 101.1, 99.3, 99.5, 2500),  # climax (slot 3), RVOL surge
        _bar(symbol, E_OPEN + 1200.0, 99.6, 101.5, 99.4, 101.0, 1000),  # trigger: breaks high[3]=101.1
        _bar(symbol, E_OPEN + 1500.0, 101.0, 101.3, 100.8, 101.1, 900),
        _bar(symbol, E_OPEN + 1800.0, 101.1, 101.4, 100.9, 101.2, 900),
    ]


def test_canonical_capitulation_matches_the_hand_computed_signal():
    """TC-1: the canonical capitulation firing -- setup chip, side, and every geometry field
    hand-verified (values confirmed by direct execution against the fixture)."""
    signal = detect_capitulation(
        _canonical_capitulation_bars(), _CAPITULATION_BASELINE, "CAP1", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert signal is not None
    assert signal["setup_id"] == "capitulation"
    assert signal["side"] == "long"
    assert signal["trigger_price"] == pytest.approx(101.1)
    assert signal["entry"] == pytest.approx(101.1)
    assert signal["entry_kind"] == "level"
    assert signal["price_low"] == pytest.approx(99.3)
    assert signal["price_high"] == pytest.approx(101.1)
    assert signal["invalidation_price"] == pytest.approx(98.76)
    geometry = signal["geometry"]
    assert geometry["slots_to_break"] == 4
    assert geometry["decline_mbr"] == pytest.approx(4.7)
    assert geometry["decline_bars"] == 3
    assert geometry["climax_rvol"] == pytest.approx(2.5)
    assert geometry["bars_from_climax_to_trigger"] == 1
    assert signal["volume"]["rvol_trigger_bar"] == pytest.approx(1.0)
    assert signal["volume"]["approach_rvol_max"] == pytest.approx(2.5)
    assert signal["principles"] == ["P1"]
    assert signal["disclosures"]["bars_to_close"] == 2
    assert signal["disclosures"]["concurrent_signals"] == []
    assert signal["disclosures"]["euphoria_recent"] is False
    assert signal["disclosures"]["capitulation_recent"] is False


def _reanchoring_capitulation_bars(symbol: str = "REANCH") -> list[RawBar]:
    """TC-7: identical through the raw climax candidate at slot 3, but slot 4 makes a NEW, lower
    low (98.5 < the raw climax's own 99.3) WITHOUT triggering -- the panic still running -- before
    slot 5 finally triggers. `leg_low`/the disclosed `decline_*`/`climax_rvol` fields must reflect
    the RE-ANCHORED slot-4 climax, never the original slot-3 one."""
    return [
        _bar(symbol, E_OPEN, 104.1, 104.3, 103.9, 104.0, 1000),
        _bar(symbol, E_OPEN + 300.0, 104.0, 104.1, 102.4, 102.5, 1000),
        _bar(symbol, E_OPEN + 600.0, 102.5, 102.6, 100.9, 101.0, 1200),
        _bar(symbol, E_OPEN + 900.0, 101.0, 101.1, 99.3, 99.5, 2500),  # raw climax candidate
        _bar(symbol, E_OPEN + 1200.0, 99.4, 100.0, 98.5, 98.8, 1500),  # NEW low, no trigger yet
        _bar(symbol, E_OPEN + 1500.0, 98.9, 100.6, 98.6, 100.2, 1000),  # trigger: breaks high[4]=100.0
        _bar(symbol, E_OPEN + 1800.0, 100.2, 100.5, 100.0, 100.3, 900),
    ]


def test_capitulation_re_anchors_the_climax_bar_when_a_new_low_forms_before_any_trigger():
    """TC-7: the re-anchored climax (slot 4, low=98.5) drives `leg_low`/`decline_bars`/
    `decline_mbr`/`climax_rvol`/`trigger_price`/`invalidation_price` -- NOT the original slot-3
    candidate's own values (which the canonical fixture above already proves as a contrast)."""
    signal = detect_capitulation(
        _reanchoring_capitulation_bars(), _CAPITULATION_BASELINE, "REANCH", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert signal is not None
    geometry = signal["geometry"]
    assert geometry["slots_to_break"] == 5  # trigger, not the (re-anchored) climax bar itself
    assert signal["price_low"] == pytest.approx(98.5)  # re-anchored leg_low, not 99.3
    assert geometry["decline_bars"] == 4  # extended by the re-anchoring, not the raw window's 3
    assert geometry["decline_mbr"] == pytest.approx(5.5)
    assert geometry["climax_rvol"] == pytest.approx(1.5)  # RVOL of the RE-ANCHORED bar (1500/1000)
    assert geometry["bars_from_climax_to_trigger"] == 1
    assert signal["trigger_price"] == pytest.approx(100.0)  # high[4], the re-anchored climax's high
    assert signal["invalidation_price"] == pytest.approx(98.05)


# --- TC-2: the near-miss fixture (meets the vertical-move/RVOL-surge gates, never reverses in the
# window) paired with the gate-relaxed control -- proves the bounce-window gate SPECIFICALLY is
# what rejects it (the iter-4 lesson: a "must not fire" fixture can pass for the wrong reason).


def _capitulation_near_miss_bars(symbol: str = "NM1") -> list[RawBar]:
    """The SAME climax formation as the canonical fixture (slots 0-3), but every subsequent bar's
    high stays BELOW the immediately preceding bar's own high through slot 6 (`t - v > bounce_max`
    at slot 7, so the walk expires before slot 7's own high -- which WOULD exceed slot 6's -- is
    ever checked). Nothing else about the formation is disturbed."""
    return [
        _bar(symbol, E_OPEN, 104.1, 104.3, 103.9, 104.0, 1000),
        _bar(symbol, E_OPEN + 300.0, 104.0, 104.1, 102.4, 102.5, 1000),
        _bar(symbol, E_OPEN + 600.0, 102.5, 102.6, 100.9, 101.0, 1200),
        _bar(symbol, E_OPEN + 900.0, 101.0, 101.1, 99.3, 99.5, 2500),  # climax (slot 3), high=101.1
        _bar(symbol, E_OPEN + 1200.0, 99.4, 101.0, 99.35, 99.6, 1000),  # high 101.0, not > 101.1
        _bar(symbol, E_OPEN + 1500.0, 99.5, 100.9, 99.4, 99.7, 1000),  # high 100.9, not > 101.0
        _bar(symbol, E_OPEN + 1800.0, 99.6, 100.8, 99.5, 99.8, 1000),  # high 100.8, not > 100.9
        # slot 7: high 101.0 WOULD exceed slot 6's 100.8 -- but t-v=4 > bounce_max=3 by then.
        _bar(symbol, E_OPEN + 2100.0, 99.7, 101.0, 99.55, 100.8, 1000),
    ]


def test_capitulation_near_miss_no_reversal_within_the_bounce_window_fires_no_signal():
    """TC-2: the formation expires silently -- no signal, regardless of what a later bar's high
    does. The control below relaxes ONLY `bounce_max_bars` and proves that gate, specifically, is
    what rejected it (every other gate -- the vertical move, the RVOL surge -- already passed)."""
    bars = _capitulation_near_miss_bars()
    baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(8)}}
    signal = detect_capitulation(
        bars, baseline, "NM1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert signal is None

    relaxed = {**_PARAMS, "bounce_max_bars": 10}
    relaxed_signal = detect_capitulation(
        bars, baseline, "NM1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, relaxed,
    )
    assert relaxed_signal is not None
    assert relaxed_signal["geometry"]["slots_to_break"] == 7
    assert relaxed_signal["geometry"]["bars_from_climax_to_trigger"] == 4
    assert relaxed_signal["geometry"]["bars_from_climax_to_trigger"] > _PARAMS["bounce_max_bars"]


# --- TC-6 / TC-7: the truncate/mutate lookahead property test, for capitulation ------------------


def test_capitulation_truncating_to_the_trigger_bar_reproduces_the_core_detection_fields():
    """TC-6: extends the generic truncation-invariance property (own direct test, mirroring
    ``detect_cup_handle``'s own truncate/mutate pair, since ``detect_capitulation`` is a
    single-return detector like ``detect_cup_handle`` rather than a list-returning one)."""
    bars = _canonical_capitulation_bars()
    full = detect_capitulation(
        bars, _CAPITULATION_BASELINE, "CAP1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert full is not None
    trigger_idx = full["geometry"]["slots_to_break"]

    truncated = detect_capitulation(
        bars[: trigger_idx + 1], _CAPITULATION_BASELINE, "CAP1", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert truncated is not None
    assert truncated["trigger_price"] == full["trigger_price"]
    assert truncated["invalidation_price"] == full["invalidation_price"]
    assert truncated["geometry"] == full["geometry"]


def test_capitulation_mutating_a_bar_after_the_trigger_changes_nothing():
    """TC-7: mutation-invariance for capitulation."""
    bars = _canonical_capitulation_bars()
    full = detect_capitulation(
        bars, _CAPITULATION_BASELINE, "CAP1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert full is not None
    trigger_idx = full["geometry"]["slots_to_break"]
    assert trigger_idx + 1 < len(bars), "fixture must carry at least one bar after the trigger"

    mutated = list(bars)
    victim = mutated[trigger_idx + 1]
    mutated[trigger_idx + 1] = RawBar(
        victim.symbol, victim.timeframe, victim.epoch,
        victim.open * 3.0, victim.high * 5.0, victim.low * 0.2, victim.close * 4.0, victim.volume * 50,
    )
    mutated_result = detect_capitulation(
        mutated, _CAPITULATION_BASELINE, "CAP1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert mutated_result == full


# --- TC-3: detect_euphoria -- a marker event only, never a served signal shape ---------------------


def _canonical_euphoria_bars(symbol: str = "EUP1") -> list[RawBar]:
    """The exact mirror UP of ``_canonical_capitulation_bars``: a vertical RALLY into a climax bar
    (slot 3), then a first-strength reversal DOWN at slot 4 (``low < low[3]``) -- the euphoria
    marker's own trigger."""
    return [
        _bar(symbol, E_OPEN, 95.9, 96.1, 95.7, 96.0, 1000),
        _bar(symbol, E_OPEN + 300.0, 96.0, 97.6, 95.9, 97.5, 1000),
        _bar(symbol, E_OPEN + 600.0, 97.5, 99.1, 97.4, 99.0, 1200),
        _bar(symbol, E_OPEN + 900.0, 99.0, 100.7, 98.9, 100.5, 2500),  # climax (slot 3)
        _bar(symbol, E_OPEN + 1200.0, 100.4, 100.6, 98.5, 98.9, 1000),  # trigger: low < low[3]=98.9
        _bar(symbol, E_OPEN + 1500.0, 98.9, 99.1, 98.6, 99.0, 900),
    ]


_EUPHORIA_BASELINE = {
    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(6)},
}


def test_canonical_euphoria_fires_a_marker_event_only():
    """TC-3: the euphoria marker's only output is its own trigger-bar index -- no side, no entry,
    no invalidation, no geometry, no setup_id (structurally incapable of becoming a served signal
    row)."""
    marker = detect_euphoria(_canonical_euphoria_bars(), _EUPHORIA_BASELINE, _PARAMS)
    assert marker == {"trigger_idx": 4}
    assert set(marker.keys()) == {"trigger_idx"}


def test_euphoria_near_miss_no_reversal_within_the_bounce_window_fires_no_marker():
    """The mirrored error case: a euphoric rally that meets the vertical-move/RVOL-surge gates but
    never produces a downside reversal bar within ``PLAYBOOK_BOUNCE_MAX_BARS`` emits no marker."""
    bars = [
        _bar("EUPNM", E_OPEN, 95.9, 96.1, 95.7, 96.0, 1000),
        _bar("EUPNM", E_OPEN + 300.0, 96.0, 97.6, 95.9, 97.5, 1000),
        _bar("EUPNM", E_OPEN + 600.0, 97.5, 99.1, 97.4, 99.0, 1200),
        _bar("EUPNM", E_OPEN + 900.0, 99.0, 100.7, 98.9, 100.5, 2500),  # climax
        _bar("EUPNM", E_OPEN + 1200.0, 100.4, 100.6, 98.95, 100.5, 1000),  # low not < 98.9
        _bar("EUPNM", E_OPEN + 1500.0, 100.4, 100.5, 99.0, 100.3, 1000),  # low not < prior
        _bar("EUPNM", E_OPEN + 1800.0, 100.2, 100.4, 99.1, 100.2, 1000),  # low not < prior
    ]
    baseline = {"mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(7)}}
    marker = detect_euphoria(bars, baseline, _PARAMS)
    assert marker is None


# === J-06: the range family -- range_trade (TC-1, TC-2, TC-3) / double_top+double_bottom
# (TC-4, TC-5, TC-10) ===============================================================================
#
# range_trade: a session-wide high/low (`SH`/`SL`, prefix extremes) wide enough
# (>= PLAYBOOK_RANGE_MIN_WIDTH_MBR) with BOTH the low zone AND the high zone showing >= 2 touches
# each, each later touch holding its own extreme within PLAYBOOK_RANGE_HOLD_TOL_MBR (spec §3.7's
# full arming clause -- the BOOK's "test the low AND high twice and hold"), then a reversal-bar
# trigger within PLAYBOOK_BOUNCE_MAX_BARS of the arming-completing touch, gated by
# PLAYBOOK_RANGE_HOLD_TOL_MBR throughout the scan, and voided fail-closed when the trigger
# reference is degenerate (`T <= SL` long / `T >= SH` short -- spec §3.7's Edge cases). Values
# hand-computed and cross-checked by direct execution (this module's own convention); every
# fixture bar is physically valid (`low <= min(open, close)`, `high >= max(open, close)`).

_RANGE_TRADE_BASELINE = {
    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(12)},
}


def _canonical_range_trade_long_bars(symbol: str = "RT1") -> list[RawBar]:
    """A genuinely TWO-SIDED range (spec §3.7 arms on both zones, never one). MBR = 1.0, so the
    zones are 1.00 wide and the hold tolerance is 0.50.
    Slot 0: HIGH TOUCH 1 -- sets `SH` = 105.0, so the high zone is [104.0, 105.0].
    Slot 1: leaves both zones (103.9 high / 101.5 low).
    Slot 2: LOW TOUCH 1 -- sets `SL` = 100.0, so the low zone is [100.0, 101.0].
    Slot 3: leaves the low zone (low 101.5), re-arming it; its high 103.0 crosses the 102.5
      midrange, which is what makes `crossed_midrange` True here.
    Slot 4: HIGH TOUCH 2 (high 104.8, inside the high zone; extends `SH` by 0.0 -- "held").
    Slot 5: leaves the high zone (high 103.5), re-arming it.
    Slot 6: LOW TOUCH 2 (low 100.4; extends `SL` by 0.0 -- "held") -- the arming-completing
      touch `b = 6`, so the arming attempt is evaluated at `t = 7`.
    Slot 7: the reversal-bar trigger (`high 103.5 > high[6] = 102.6`), volume surge; the hold
      check passes (`min(low[6..6]) = 100.4 >= SL - 0.5 = 99.5`). `T = high[6] = 102.6`.
    Slots 8-9: session tail (also the post-trigger bars the lookahead property test mutates)."""
    return [
        _bar(symbol, E_OPEN + 0 * 300.0, 104.0, 105.0, 103.5, 104.5, 1000),
        _bar(symbol, E_OPEN + 1 * 300.0, 103.9, 103.9, 101.5, 101.8, 1000),
        _bar(symbol, E_OPEN + 2 * 300.0, 101.8, 102.0, 100.0, 100.4, 1000),
        _bar(symbol, E_OPEN + 3 * 300.0, 101.6, 103.0, 101.5, 102.8, 1000),
        _bar(symbol, E_OPEN + 4 * 300.0, 102.8, 104.8, 102.5, 104.4, 1000),
        _bar(symbol, E_OPEN + 5 * 300.0, 103.4, 103.5, 102.0, 102.4, 1000),
        _bar(symbol, E_OPEN + 6 * 300.0, 102.4, 102.6, 100.4, 100.7, 1000),
        _bar(symbol, E_OPEN + 7 * 300.0, 101.0, 103.5, 100.6, 103.2, 2000),
        _bar(symbol, E_OPEN + 8 * 300.0, 103.2, 103.4, 102.9, 103.1, 1000),
        _bar(symbol, E_OPEN + 9 * 300.0, 103.1, 103.3, 102.8, 103.0, 1000),
    ]


def _canonical_range_trade_short_bars(symbol: str = "RT2") -> list[RawBar]:
    """The resistance-fade mirror, hand-built INDEPENDENTLY (different price scale, different
    range width, and the two zones tested in the opposite ORDER -- low/low then high/high -- so it
    is a genuine second computation, not the long fixture's values negated).
    `SL` = 198.0 (slot 0), `SH` = 205.0 (slot 4) -> range 7.00 MBR; low zone [198.0, 199.0],
    high zone [204.0, 205.0]; midrange 201.5.
    Slot 0: LOW TOUCH 1. Slot 1: leaves it. Slot 2: LOW TOUCH 2 (low 198.3 -- held).
    Slot 3: leaves it. Slot 4: HIGH TOUCH 1 (sets `SH`). Slot 5: leaves the high zone, its low
      202.0 staying ABOVE the 201.5 midrange -- which is what makes `crossed_midrange` False on
      this fixture (the True/False pair that proves the field is not constant by construction).
    Slot 6: HIGH TOUCH 2 (high 204.7 -- held), the arming-completing touch `b = 6`.
    Slot 7: the reversal-bar trigger (`low 201.0 < low[6] = 202.6`); `T = low[6] = 202.6`.
    Slots 8-9: session tail."""
    return [
        _bar(symbol, E_OPEN + 0 * 300.0, 199.0, 200.4, 198.0, 198.5, 1000),
        _bar(symbol, E_OPEN + 1 * 300.0, 199.5, 201.0, 199.4, 200.8, 1000),
        _bar(symbol, E_OPEN + 2 * 300.0, 200.1, 200.2, 198.3, 198.7, 1000),
        _bar(symbol, E_OPEN + 3 * 300.0, 199.7, 202.5, 199.6, 202.3, 1000),
        _bar(symbol, E_OPEN + 4 * 300.0, 202.5, 205.0, 202.3, 204.5, 1000),
        _bar(symbol, E_OPEN + 5 * 300.0, 203.7, 203.8, 202.0, 202.4, 1000),
        _bar(symbol, E_OPEN + 6 * 300.0, 203.0, 204.7, 202.6, 204.5, 1000),
        _bar(symbol, E_OPEN + 7 * 300.0, 204.0, 204.2, 201.0, 201.3, 2000),
        _bar(symbol, E_OPEN + 8 * 300.0, 201.3, 201.8, 200.8, 201.0, 1000),
        _bar(symbol, E_OPEN + 9 * 300.0, 201.0, 201.5, 200.6, 201.2, 1000),
    ]


def _one_sided_range_trade_bars(symbol: str = "RT1S") -> list[RawBar]:
    """The both-zones near-miss: the low zone is tested TWICE (slots 1 and 3) while the high zone
    is touched ONCE (slot 0) -- a plain support test inside a one-way session, the "breakout-only"
    case spec §3.7's own Ch 13 note excludes. Every other gate this fixture meets (range 5.00 MBR
    wide, both low touches held, a reversal bar at slot 4 within the bounce window), so the
    both-zones clause specifically is what silences it; its control is the canonical two-sided
    fixture above, which differs by exactly one thing -- a genuine second high-zone test."""
    return [
        _bar(symbol, E_OPEN + 0 * 300.0, 103.0, 105.0, 103.0, 104.0, 1000),
        _bar(symbol, E_OPEN + 1 * 300.0, 104.0, 104.2, 100.0, 100.3, 1000),
        _bar(symbol, E_OPEN + 2 * 300.0, 100.3, 103.0, 102.0, 102.5, 1000),
        _bar(symbol, E_OPEN + 3 * 300.0, 102.5, 102.8, 100.4, 100.6, 1000),
        _bar(symbol, E_OPEN + 4 * 300.0, 100.6, 103.5, 100.2, 103.0, 2000),
        _bar(symbol, E_OPEN + 5 * 300.0, 103.0, 103.2, 102.8, 103.0, 1000),
        _bar(symbol, E_OPEN + 6 * 300.0, 103.0, 103.1, 102.9, 103.0, 1000),
    ]


def test_canonical_range_trade_long_matches_the_hand_computed_signal():
    """TC-1: the canonical support-bounce firing -- setup chip, side, and every geometry field
    hand-verified (values confirmed by direct execution against the fixture). The range is
    two-sided as spec §3.7 requires: BOTH zone touch counts are 2, and the invalidation
    (`SL - 0.30*(T - SL)` = 100.0 - 0.30*2.6 = 99.22) sits BELOW the long's own entry."""
    results = detect_range_trade(
        _canonical_range_trade_long_bars(), _RANGE_TRADE_BASELINE, "RT1", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert len(results) == 1
    signal = results[0]
    assert signal["setup_id"] == "range_trade"
    assert signal["side"] == "long"
    assert signal["trigger_price"] == pytest.approx(102.6)
    assert signal["entry"] == pytest.approx(102.6)
    assert signal["entry_kind"] == "level"
    assert signal["price_low"] == pytest.approx(100.0)
    assert signal["price_high"] == pytest.approx(105.0)
    assert signal["invalidation_price"] == pytest.approx(99.22)
    assert signal["invalidation_price"] < signal["entry"]
    geometry = signal["geometry"]
    assert geometry["slots_to_break"] == 7
    assert geometry["range_width_mbr"] == pytest.approx(5.0)
    assert geometry["low_zone_touches"] == 2
    assert geometry["high_zone_touches"] == 2
    assert geometry["crossed_midrange"] is True
    # goal-playbook-iter-10 (R-3.2(b)): the approach swing's own peak is bar 4's high (104.8),
    # 2.3 away from the 102.5 midpoint -- well beyond the 0.50 `PLAYBOOK_RANGE_HOLD_TOL_MBR`
    # tolerance, so the swing did NOT turn at midrange even though it crossed it.
    assert geometry["turned_at_midrange"] is False
    assert geometry["absorption_bar_present"] is False
    assert signal["volume"]["rvol_trigger_bar"] == pytest.approx(2.0)
    assert signal["principles"] == []
    assert signal["disclosures"]["attempt_count"] == 1
    assert signal["disclosures"]["bars_to_close"] == 2


def test_canonical_range_trade_short_mirrors_the_long_fixture():
    """TC-2: the exact mirror -- resistance-fade short, invalidation ABOVE the range, geometry
    magnitudes an independent (not merely negated) hand-computation of the mirrored fixture."""
    results = detect_range_trade(
        _canonical_range_trade_short_bars(), _RANGE_TRADE_BASELINE, "RT2", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert len(results) == 1
    signal = results[0]
    assert signal["setup_id"] == "range_trade"
    assert signal["side"] == "short"
    assert signal["trigger_price"] == pytest.approx(202.6)
    assert signal["entry"] == pytest.approx(202.6)
    assert signal["entry_kind"] == "level"
    assert signal["price_low"] == pytest.approx(198.0)
    assert signal["price_high"] == pytest.approx(205.0)
    # `SH + 0.30*(SH - T)` = 205.0 + 0.30*2.4 = 205.72 -- ABOVE the short's own entry.
    assert signal["invalidation_price"] == pytest.approx(205.72)
    assert signal["invalidation_price"] > signal["entry"]
    geometry = signal["geometry"]
    assert geometry["slots_to_break"] == 7
    assert geometry["range_width_mbr"] == pytest.approx(7.0)
    assert geometry["low_zone_touches"] == 2
    assert geometry["high_zone_touches"] == 2
    assert geometry["crossed_midrange"] is False
    # goal-playbook-iter-10 (R-3.2(b)): the approach swing's own trough is bar 5's low (202.0),
    # exactly 0.50 away from the 201.5 midpoint -- AT the `PLAYBOOK_RANGE_HOLD_TOL_MBR` boundary
    # (the `_zone_held`-style inclusive "<=" reading), so the swing DID turn at midrange even
    # though it never crossed it -- proof the two disclosures are genuinely independent facts.
    assert geometry["turned_at_midrange"] is True
    assert geometry["absorption_bar_present"] is False
    assert signal["volume"]["rvol_trigger_bar"] == pytest.approx(2.0)
    assert signal["principles"] == ["P5"]  # "P5 at the high side" -- the resistance-fade short
    assert signal["disclosures"]["attempt_count"] == 1


def _turned_at_midrange_bars(symbol: str, peak_high: float) -> list[RawBar]:
    """A range_trade LONG arming whose approach swing (the window between the low zone's first
    touch at slot 4 and its arming-completing touch at slot 6 -- the SAME window `crossed_midrange`
    reads) peaks at a CONTROLLED level, `peak_high`: the ONLY value that differs between the
    `turned_at_midrange` True fixture (`peak_high=105.2`, 0.20 from the 105.0 midpoint -- inside
    the 0.50 `PLAYBOOK_RANGE_HOLD_TOL_MBR` tolerance) and its near-miss control (`peak_high=106.0`,
    1.00 away -- outside it). The high zone (`SH=110.0`) is touched and held ENTIRELY before the
    window opens (slots 0 and 2), so it never contributes a bar to the window this disclosure
    reads -- the swing's own extreme genuinely comes from the approach bar (slot 5), not from a
    zone-touch bar the arming gate would have forced near an edge anyway. Values cross-checked by
    direct execution (this module's own convention): the SAME signal fires regardless of
    `peak_high` (`trigger_price=101.3`, `entry=101.3`, `entry_kind="level"`,
    `invalidation_price=99.61`), since only slot 5's high ever changes."""
    return [
        _bar(symbol, E_OPEN + 0 * 300.0, 108.5, 110.0, 108.3, 109.5, 1000),  # HIGH TOUCH 1 (SH=110.0)
        _bar(symbol, E_OPEN + 1 * 300.0, 108.8, 108.9, 106.5, 107.0, 1000),  # exits the high zone
        _bar(symbol, E_OPEN + 2 * 300.0, 107.0, 109.6, 106.8, 109.0, 1000),  # HIGH TOUCH 2 (held, ext 0)
        _bar(symbol, E_OPEN + 3 * 300.0, 108.0, 108.3, 104.0, 104.5, 1000),  # transition, exits high zone
        _bar(symbol, E_OPEN + 4 * 300.0, 104.0, 104.2, 100.0, 100.5, 1000),  # LOW TOUCH 1 (SL=100.0)
        _bar(symbol, E_OPEN + 5 * 300.0, 101.5, peak_high, 101.2, 102.0, 1000),  # the controlled swing peak
        _bar(symbol, E_OPEN + 6 * 300.0, 101.0, 101.3, 100.2, 100.5, 1000),  # LOW TOUCH 2 (held) -- b=6
        _bar(symbol, E_OPEN + 7 * 300.0, 100.8, 103.0, 100.5, 102.5, 1000),  # reversal trigger
        _bar(symbol, E_OPEN + 8 * 300.0, 102.5, 102.8, 102.3, 102.6, 1000),
        _bar(symbol, E_OPEN + 9 * 300.0, 102.6, 102.9, 102.4, 102.7, 1000),
    ]


def test_range_trade_turned_at_midrange_true_and_its_near_miss_control():
    """TC-6/TC-7: spec §3.7's R-3.2(b) disclosure. The approach swing's own extreme sits within
    `PLAYBOOK_RANGE_HOLD_TOL_MBR * MBR` (0.50) of the range midpoint (105.0: `SH=110.0`,
    `SL=100.0`) in the True fixture (peak 105.2, 0.20 away) and just beyond it in the near-miss
    control (peak 106.0, 1.00 away) -- the ONLY value that changes between the two calls (the
    file's own near-miss-pairing convention: a bare change in outcome alone proves nothing without
    isolating the one mechanism that caused it). Every pre-existing field the signal carries
    (`trigger_price`, `entry`, `entry_kind`, `invalidation_price`, `crossed_midrange`,
    `absorption_bar_present`, `range_width_mbr`, the touch counts) is asserted identical between
    the two, proving this field's own presence changes nothing else."""
    true_results = detect_range_trade(
        _turned_at_midrange_bars("RTTM", 105.2), _RANGE_TRADE_BASELINE, "RTTM", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert len(true_results) == 1
    true_signal = true_results[0]
    assert true_signal["side"] == "long"
    assert true_signal["trigger_price"] == pytest.approx(101.3)
    assert true_signal["entry"] == pytest.approx(101.3)
    assert true_signal["entry_kind"] == "level"
    assert true_signal["invalidation_price"] == pytest.approx(99.61)
    true_geometry = true_signal["geometry"]
    assert true_geometry["turned_at_midrange"] is True
    assert true_geometry["crossed_midrange"] is True
    assert true_geometry["absorption_bar_present"] is False
    assert true_geometry["range_width_mbr"] == pytest.approx(10.0)
    assert true_geometry["low_zone_touches"] == 2
    assert true_geometry["high_zone_touches"] == 2

    false_results = detect_range_trade(
        _turned_at_midrange_bars("RTTM", 106.0), _RANGE_TRADE_BASELINE, "RTTM", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert len(false_results) == 1
    false_signal = false_results[0]
    false_geometry = false_signal["geometry"]
    assert false_geometry["turned_at_midrange"] is False

    # Every OTHER field is byte-identical to the True fixture's own signal -- the near-miss control
    # changes nothing but the one mechanism this test targets.
    assert false_signal["trigger_price"] == true_signal["trigger_price"]
    assert false_signal["entry"] == true_signal["entry"]
    assert false_signal["entry_kind"] == true_signal["entry_kind"]
    assert false_signal["invalidation_price"] == true_signal["invalidation_price"]
    assert false_geometry["crossed_midrange"] == true_geometry["crossed_midrange"]
    assert false_geometry["absorption_bar_present"] == true_geometry["absorption_bar_present"]
    assert false_geometry["range_width_mbr"] == true_geometry["range_width_mbr"]
    assert false_geometry["low_zone_touches"] == true_geometry["low_zone_touches"]
    assert false_geometry["high_zone_touches"] == true_geometry["high_zone_touches"]


def test_range_trade_one_sided_range_never_arms_and_its_two_sided_control_fires_once():
    """Spec §3.7's arming clause is "test the low AND high twice and hold": a session that tests
    one extreme twice while touching the other once -- the breakout-only case Ch 13 excludes --
    arms nothing on EITHER side. Paired with its control (the iter-4 lesson: `results == []` alone
    proves nothing): the canonical fixture, which differs by exactly one added high-zone test,
    fires exactly one signal. This is the formation the pre-audit implementation fired on."""
    one_sided = _one_sided_range_trade_bars()
    assert detect_range_trade(
        one_sided, _RANGE_TRADE_BASELINE, "RT1S", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    ) == []
    # The one-sided fixture's own touch counts, read directly: the low zone IS tested twice, so
    # the rejecter is the high zone's single touch, not the low side or the range width.
    session_low = min(bar.low for bar in one_sided[:4])
    session_high = max(bar.high for bar in one_sided[:4])
    near = _PARAMS["near_extreme_mbr"] * _RANGE_TRADE_BASELINE["mbr"]
    assert (session_high - session_low) >= _PARAMS["range_min_width_mbr"]
    assert len(zone_touches(one_sided[:4], session_low, session_low + near)) == 2
    assert len(zone_touches(one_sided[:4], session_high - near, session_high)) == 1

    control = detect_range_trade(
        _canonical_range_trade_long_bars(), _RANGE_TRADE_BASELINE, "RT1", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert len(control) == 1
    assert control[0]["geometry"]["high_zone_touches"] == 2


def _range_trade_unheld_bars() -> list[RawBar]:
    """Both zones tested twice, but the SECOND low touch (slot 6, low 99.1) extends the running
    low by 0.90 MBR against the 0.50 `PLAYBOOK_RANGE_HOLD_TOL_MBR` tolerance -- the range did not
    "hold", so spec §3.7's arming clause rejects it even though every count is satisfied."""
    bars = _canonical_range_trade_long_bars("RTH")
    bars[6] = _bar("RTH", E_OPEN + 6 * 300.0, 102.4, 102.6, 99.1, 99.4, 1000)
    bars[7] = _bar("RTH", E_OPEN + 7 * 300.0, 99.6, 103.5, 99.3, 103.2, 2000)
    return bars


def test_range_trade_a_touch_that_does_not_hold_the_extreme_never_arms():
    """The "held" half of spec §3.7's arming clause, with its gate-relaxed control: the ONLY
    parameter the control changes is `range_hold_tol_mbr` (0.50 -> 2.00, which covers the 0.90
    extension), and the same bars then fire exactly one signal -- proving that named tolerance
    specifically is the rejecter."""
    bars = _range_trade_unheld_bars()
    assert detect_range_trade(
        bars, _RANGE_TRADE_BASELINE, "RTH", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    ) == []

    relaxed = {**_PARAMS, "range_hold_tol_mbr": 2.0}
    relaxed_results = detect_range_trade(
        bars, _RANGE_TRADE_BASELINE, "RTH", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, relaxed,
    )
    assert len(relaxed_results) == 1
    assert relaxed_results[0]["side"] == "long"
    assert relaxed_results[0]["trigger_price"] == pytest.approx(102.6)
    assert relaxed_results[0]["geometry"]["low_zone_touches"] == 2
    assert relaxed_results[0]["geometry"]["high_zone_touches"] == 2


def _range_trade_degenerate_reference_bars(reference_high: float) -> list[RawBar]:
    """The canonical arming (slots 0-6) followed by a bar whose whole range sits at/below the
    arming-time `SL` = 100.0 while staying inside the 0.50 hold tolerance (low 99.6 >= 99.5), then
    a higher-high reversal bar. `reference_high` is the ONLY value that differs between the
    degenerate fixture (99.9, below `SL`) and its control (100.2, above `SL`)."""
    bars = _canonical_range_trade_long_bars("RTD")[:7]
    bars.append(_bar("RTD", E_OPEN + 7 * 300.0, 99.8, reference_high, 99.6, 99.7, 1000))
    bars.append(_bar("RTD", E_OPEN + 8 * 300.0, 99.7, 100.5, 99.6, 100.4, 2000))
    bars.append(_bar("RTD", E_OPEN + 9 * 300.0, 100.4, 100.6, 100.1, 100.5, 1000))
    return bars


def test_range_trade_degenerate_trigger_reference_below_the_range_low_fails_closed():
    """Spec §3.7's Edge cases, "degenerate trigger reference": the invalidation clause is
    arithmetic on `T - SL`, so `T <= SL` inverts it -- a long whose structural invalidation lands
    ABOVE its own entry, i.e. recorded born-invalidated. Voided fail-closed. Control: the SAME
    bars with the reversal bar's reference high lifted from 99.9 to 100.2 (just above `SL`) fire
    exactly one coherent signal, so the degeneracy clause specifically is the rejecter."""
    degenerate = _range_trade_degenerate_reference_bars(99.9)
    assert detect_range_trade(
        degenerate, _RANGE_TRADE_BASELINE, "RTD", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    ) == []
    # What the spec's formula WOULD have produced there, computed here from the fixture itself:
    # T = high[7] = 99.9 < SL = 100.0 -> invalidation 100.03, i.e. above the entry.
    would_be_trigger, session_low = degenerate[7].high, min(bar.low for bar in degenerate[:7])
    assert would_be_trigger < session_low
    assert session_low - _PARAMS["stop_pad_frac"] * (would_be_trigger - session_low) > would_be_trigger

    control = detect_range_trade(
        _range_trade_degenerate_reference_bars(100.2), _RANGE_TRADE_BASELINE, "RTD", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert len(control) == 1
    assert control[0]["side"] == "long"
    assert control[0]["trigger_price"] == pytest.approx(100.2)
    assert control[0]["invalidation_price"] == pytest.approx(99.94)
    assert control[0]["invalidation_price"] < control[0]["entry"]


def _range_trade_degenerate_reference_bars_short(reference_low: float) -> list[RawBar]:
    """The SHORT-side mirror of ``_range_trade_degenerate_reference_bars`` (goal-playbook-iter-7,
    TC-12): the canonical short arming (slots 0-6, `SH` = 205.0) followed by a reference bar whose
    high (205.3) stays within the 0.50 hold tolerance of `SH` (205.3 <= 205.5) without itself
    resetting the arming, then a lower-low reversal bar. ``reference_low`` is the ONLY value that
    differs between the degenerate fixture (205.1, at/above `SH`) and its control (204.5, below
    `SH`) -- the ``reference_high``-only-varies precedent, mirrored onto the field the SHORT side's
    own trigger reference (`prev_bar.low`) actually reads."""
    bars = _canonical_range_trade_short_bars("RTDS")[:7]
    bars.append(_bar("RTDS", E_OPEN + 7 * 300.0, 205.2, 205.3, reference_low, 205.2, 1000))
    bars.append(_bar("RTDS", E_OPEN + 8 * 300.0, 205.0, 205.2, 204.0, 204.2, 2000))
    bars.append(_bar("RTDS", E_OPEN + 9 * 300.0, 204.2, 204.4, 203.9, 204.1, 1000))
    return bars


def test_range_trade_degenerate_trigger_reference_at_or_above_the_range_high_fails_closed_short():
    """TC-12 (goal-playbook-iter-7): the SHORT-side mirror of
    ``test_range_trade_degenerate_trigger_reference_below_the_range_low_fails_closed`` -- spec
    §3.7's Edge cases "degenerate trigger reference" clause is symmetric (module source: ``T <= SL``
    long / ``T >= SH`` short): a short whose structural invalidation would land AT OR BELOW its own
    entry, i.e. recorded born-invalidated, is voided fail-closed. Control: the SAME bars with the
    reference bar's low lowered from 205.1 to 204.5 (just below `SH`) fire exactly one coherent
    short signal, proving the degeneracy clause specifically -- not the arming or the reversal
    predicate -- is the rejecter (the fixture is byte-identical between the two calls except for
    that one field, the iter-6 lesson: a bare `results == []` alone proves nothing)."""
    degenerate = _range_trade_degenerate_reference_bars_short(205.1)
    assert detect_range_trade(
        degenerate, _RANGE_TRADE_BASELINE, "RTDS", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    ) == []
    # What the spec's formula WOULD have produced there, computed here from the fixture itself:
    # T = low[7] = 205.1 >= SH = 205.0 -> invalidation 204.97, i.e. at/below the entry.
    would_be_trigger, session_high = degenerate[7].low, max(bar.high for bar in degenerate[:7])
    assert would_be_trigger >= session_high
    assert session_high + _PARAMS["stop_pad_frac"] * (session_high - would_be_trigger) < would_be_trigger

    control = detect_range_trade(
        _range_trade_degenerate_reference_bars_short(204.5), _RANGE_TRADE_BASELINE, "RTDS",
        SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert len(control) == 1
    assert control[0]["side"] == "short"
    assert control[0]["trigger_price"] == pytest.approx(204.5)
    assert control[0]["invalidation_price"] == pytest.approx(205.15)
    assert control[0]["invalidation_price"] > control[0]["entry"]


# --- TC-3: a strict break beyond the low zone by more than PLAYBOOK_RANGE_HOLD_TOL_MBR dissolves
# range-mode -- no signal, PAIRED with a gate-relaxed control (range_hold_tol_mbr widened) proving
# the hold-tolerance gate specifically is the rejecter (the iter-4 lesson: `results == []` alone
# proves nothing).


def _range_trade_near_miss_bars() -> list[RawBar]:
    """The SAME two-sided arming as the canonical long fixture (slots 0-6), but slot 7 breaks well
    beyond the hold floor (`SL - RANGE_HOLD_TOL_MBR*MBR = 99.5`) without itself reversing -- the
    scan's hold check fails at slot 8 (`min(low[6..7]) == 97.0 < 99.5`), ending the scan before the
    would-be-reversal bar at slot 8 is ever reached under the default tolerance."""
    bars = _canonical_range_trade_long_bars("RTNM")[:7]
    bars.append(_bar("RTNM", E_OPEN + 7 * 300.0, 100.7, 100.8, 97.0, 97.2, 1000))  # breaks hold tol
    bars.append(_bar("RTNM", E_OPEN + 8 * 300.0, 97.2, 103.5, 97.0, 103.0, 2000))  # unreachable
    bars.append(_bar("RTNM", E_OPEN + 9 * 300.0, 103.0, 103.2, 102.8, 103.0, 1000))
    return bars


def test_range_trade_near_miss_break_beyond_hold_tolerance_fires_no_signal():
    """TC-3: the formation dissolves silently -- no signal, regardless of the later reversal bar.
    The control below relaxes ONLY `range_hold_tol_mbr` and proves that gate, specifically, is what
    rejected it (the arming itself -- range width, both zones tested twice and held -- passed)."""
    bars = _range_trade_near_miss_bars()
    results = detect_range_trade(
        bars, _RANGE_TRADE_BASELINE, "RTNM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert results == []

    relaxed = {**_PARAMS, "range_hold_tol_mbr": 10.0}
    relaxed_results = detect_range_trade(
        bars, _RANGE_TRADE_BASELINE, "RTNM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, relaxed,
    )
    assert len(relaxed_results) == 1
    assert relaxed_results[0]["side"] == "long"
    assert relaxed_results[0]["geometry"]["slots_to_break"] == 8
    assert relaxed_results[0]["trigger_price"] == pytest.approx(100.8)


# --- range_trade's own truncate/mutate lookahead property test (TC-8) -----------------------------
# BOTH sides are parametrized (the J-04 `_CONTINUATION_LOOKAHEAD_FIXTURES` precedent): the long and
# short walks share one code path, but a shared walk is exactly where a mirror-only lookahead bug
# would hide, so the mirror is truncate/mutate-tested in its own right.

_RANGE_TRADE_LOOKAHEAD_FIXTURES = [
    (detect_range_trade, _canonical_range_trade_long_bars(), "RT1"),
    (detect_range_trade, _canonical_range_trade_short_bars(), "RT2"),
]


@pytest.mark.parametrize("detect_fn, bars, symbol", _RANGE_TRADE_LOOKAHEAD_FIXTURES)
def test_range_trade_truncating_to_the_trigger_bar_reproduces_the_core_detection_fields(
    detect_fn, bars, symbol
):
    full = detect_fn(bars, _RANGE_TRADE_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
    assert len(full) == 1
    trigger_idx = full[0]["geometry"]["slots_to_break"]

    truncated = detect_fn(
        bars[: trigger_idx + 1], _RANGE_TRADE_BASELINE, symbol, SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert len(truncated) == 1
    assert truncated[0]["trigger_price"] == full[0]["trigger_price"]
    assert truncated[0]["invalidation_price"] == full[0]["invalidation_price"]
    assert truncated[0]["geometry"] == full[0]["geometry"]


@pytest.mark.parametrize("detect_fn, bars, symbol", _RANGE_TRADE_LOOKAHEAD_FIXTURES)
def test_range_trade_mutating_a_bar_after_the_trigger_changes_nothing(detect_fn, bars, symbol):
    full = detect_fn(bars, _RANGE_TRADE_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
    assert len(full) == 1
    trigger_idx = full[0]["geometry"]["slots_to_break"]
    assert trigger_idx + 1 < len(bars), "fixture must carry at least one bar after the trigger"

    mutated = list(bars)
    victim = mutated[trigger_idx + 1]
    mutated[trigger_idx + 1] = RawBar(
        victim.symbol, victim.timeframe, victim.epoch,
        victim.open * 3.0, victim.high * 5.0, victim.low * 0.2, victim.close * 4.0, victim.volume * 50,
    )
    mutated_result = detect_fn(
        mutated, _RANGE_TRADE_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert mutated_result == full


# === J-06: double_top (TC-4, TC-5, TC-10) / double_bottom (mirror) =================================

_DOUBLE_TOP_BASELINE = {
    "mbr": 1.0, "sessions": 10, "slot_volume_medians": {i: 1000 for i in range(20)},
}


def _canonical_double_top_bars(symbol: str = "DT1", p2_high: float = 110.3, idx14_low: float = 107.0) -> list[RawBar]:
    """Two confirmed swing-high pivots -- P1 at slot 3 (high=110, confirmed_at=6), P2 at slot 13
    (high=`p2_high`, confirmed_at=16), separated by 10 bars (>= `TOPS_MIN_SEPARATION_BARS`=4) and
    `TOPS_MATCH_MBR`-close (110.3-110=0.3 <= 1.0 by default). A valley (min low strictly between
    them, at slot 8, low=97.0) with depth 13.0 MBR (>= `MIN_STRUCTURE_DEPTH_MBR`=2.0). Slot 18: the
    valley-break trigger (low=96.0 < 97.0). `idx14_low` is parameterized so the fail-closed fixture
    below can reuse this exact shape with only that one bar's low changed."""
    return [
        _bar(symbol, E_OPEN + 0 * 300.0, 104, 105, 104, 104.5, 1000),
        _bar(symbol, E_OPEN + 1 * 300.0, 104.5, 106, 104, 105.5, 1000),
        _bar(symbol, E_OPEN + 2 * 300.0, 105.5, 107, 105, 106.5, 1000),
        _bar(symbol, E_OPEN + 3 * 300.0, 106.5, 110, 106, 109, 1000),  # P1
        _bar(symbol, E_OPEN + 4 * 300.0, 109, 108, 107, 107.5, 1000),
        _bar(symbol, E_OPEN + 5 * 300.0, 107.5, 105, 104, 104.5, 1000),
        _bar(symbol, E_OPEN + 6 * 300.0, 104.5, 102, 101, 101.5, 1000),
        _bar(symbol, E_OPEN + 7 * 300.0, 101.5, 100, 99, 99.5, 1000),
        _bar(symbol, E_OPEN + 8 * 300.0, 99.5, 98, 97, 97.5, 1000),  # valley low=97
        _bar(symbol, E_OPEN + 9 * 300.0, 97.5, 99, 97.2, 98.5, 1000),
        _bar(symbol, E_OPEN + 10 * 300.0, 98.5, 101, 98, 100.5, 1000),
        _bar(symbol, E_OPEN + 11 * 300.0, 100.5, 104, 100, 103.5, 1000),
        _bar(symbol, E_OPEN + 12 * 300.0, 103.5, 107, 103, 106.5, 1000),
        _bar(symbol, E_OPEN + 13 * 300.0, 106.5, p2_high, 106, p2_high - 0.8, 1000),  # P2
        _bar(symbol, E_OPEN + 14 * 300.0, p2_high - 0.8, 108, idx14_low, 107.5, 1000),
        _bar(symbol, E_OPEN + 15 * 300.0, 107.5, 106, 105, 105.5, 1000),
        _bar(symbol, E_OPEN + 16 * 300.0, 105.5, 104, 103, 103.5, 1000),  # P2 confirmed_at
        _bar(symbol, E_OPEN + 17 * 300.0, 103.5, 103.8, 102, 102.5, 1000),
        _bar(symbol, E_OPEN + 18 * 300.0, 102.5, 103, 96.0, 96.5, 2000),  # TRIGGER: breaks the valley
        _bar(symbol, E_OPEN + 19 * 300.0, 96.5, 97, 96, 96.8, 1000),
    ]


def test_canonical_double_top_matches_the_hand_computed_signal():
    """TC-4: the canonical double-top firing -- triggered at the valley break (never at the second
    top's own bar), with `nominal_risk_mbr` the FULL pattern height (never shrunk)."""
    signal = detect_double_top(
        _canonical_double_top_bars(), _DOUBLE_TOP_BASELINE, "DT1", SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert signal is not None
    assert signal["setup_id"] == "double_top"
    assert signal["side"] == "short"
    assert signal["trigger_price"] == pytest.approx(97.0)
    assert signal["entry"] == pytest.approx(97.0)
    assert signal["entry_kind"] == "level"
    assert signal["price_low"] == pytest.approx(97.0)
    assert signal["price_high"] == pytest.approx(110.3)
    assert signal["invalidation_price"] == pytest.approx(114.29)
    geometry = signal["geometry"]
    assert geometry["slots_to_break"] == 18
    assert geometry["tops_gap_mbr"] == pytest.approx(0.3)
    assert geometry["tops_separation_bars"] == 10
    assert geometry["valley_depth_mbr"] == pytest.approx(13.0)
    assert geometry["nominal_risk_mbr"] == pytest.approx(13.3)
    assert geometry["second_top_rvol_vs_first"] == pytest.approx(1.0)
    assert signal["principles"] == ["P5"]
    assert signal["disclosures"]["bars_to_close"] == 1


def _canonical_double_bottom_bars(symbol: str = "DB1") -> list[RawBar]:
    """The double_top fixture's exact mirror, hand-computed independently (P1 low 90.0 at slot 3,
    P2 low 89.7 at slot 13, peak high 103.0 at slot 8, peak-break trigger at slot 18). Extracted
    from the canonical test so the truncate/mutate lookahead property test can parametrize the
    MIRROR as well as `double_top` -- byte-identical values, no re-derivation."""
    return [
        _bar(symbol, E_OPEN + 0 * 300.0, 96, 97, 96, 96.5, 1000),
        _bar(symbol, E_OPEN + 1 * 300.0, 96.5, 97, 95, 95.5, 1000),
        _bar(symbol, E_OPEN + 2 * 300.0, 95.5, 96, 94, 94.5, 1000),
        _bar(symbol, E_OPEN + 3 * 300.0, 94.5, 95, 90, 91, 1000),  # P1, low=90
        _bar(symbol, E_OPEN + 4 * 300.0, 91, 93, 92, 92.5, 1000),
        _bar(symbol, E_OPEN + 5 * 300.0, 92.5, 96, 95, 95.5, 1000),
        _bar(symbol, E_OPEN + 6 * 300.0, 95.5, 99, 98, 98.5, 1000),
        _bar(symbol, E_OPEN + 7 * 300.0, 98.5, 101, 100, 100.5, 1000),
        _bar(symbol, E_OPEN + 8 * 300.0, 100.5, 103, 102, 102.5, 1000),  # peak high=103
        _bar(symbol, E_OPEN + 9 * 300.0, 102.5, 101, 100.8, 101, 1000),
        _bar(symbol, E_OPEN + 10 * 300.0, 101, 99, 98, 98.5, 1000),
        _bar(symbol, E_OPEN + 11 * 300.0, 98.5, 96, 95, 95.5, 1000),
        _bar(symbol, E_OPEN + 12 * 300.0, 95.5, 93, 92, 92.5, 1000),
        _bar(symbol, E_OPEN + 13 * 300.0, 92.5, 91, 89.7, 90.2, 1000),  # P2, low=89.7
        _bar(symbol, E_OPEN + 14 * 300.0, 90.2, 92, 91, 91.5, 1000),
        _bar(symbol, E_OPEN + 15 * 300.0, 91.5, 94, 93, 93.5, 1000),
        _bar(symbol, E_OPEN + 16 * 300.0, 93.5, 96, 95, 95.5, 1000),
        _bar(symbol, E_OPEN + 17 * 300.0, 95.5, 95.8, 94, 94.5, 1000),
        _bar(symbol, E_OPEN + 18 * 300.0, 94.5, 104.0, 95, 103.5, 2000),  # TRIGGER: breaks the peak
        _bar(symbol, E_OPEN + 19 * 300.0, 103.5, 104, 103, 103.8, 1000),
    ]


def test_canonical_double_bottom_mirrors_the_double_top_fixture():
    """The exact mirror: two confirmed swing-LOW pivots, a PEAK between them, the peak-break
    trigger longs."""
    bars = _canonical_double_bottom_bars()
    signal = detect_double_bottom(
        bars, _DOUBLE_TOP_BASELINE, "DB1", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert signal is not None
    assert signal["setup_id"] == "double_bottom"
    assert signal["side"] == "long"
    assert signal["trigger_price"] == pytest.approx(103.0)
    assert signal["entry"] == pytest.approx(103.0)
    assert signal["entry_kind"] == "level"
    assert signal["price_low"] == pytest.approx(89.7)
    assert signal["price_high"] == pytest.approx(103.0)
    assert signal["invalidation_price"] == pytest.approx(85.71)
    geometry = signal["geometry"]
    assert geometry["slots_to_break"] == 18
    assert geometry["tops_gap_mbr"] == pytest.approx(0.3)
    assert geometry["tops_separation_bars"] == 10
    assert geometry["valley_depth_mbr"] == pytest.approx(13.0)
    assert geometry["nominal_risk_mbr"] == pytest.approx(13.3)
    assert signal["principles"] == ["P5"]


# --- TC-5: p2 exceeding p1 by more than PLAYBOOK_TOPS_MATCH_MBR -- no double_top, PAIRED with a
# gate-relaxed control (tops_match_mbr widened) proving that gate specifically is the rejecter.


def test_double_top_near_miss_p2_exceeds_p1_beyond_tolerance_fires_no_signal():
    """TC-5: the SAME formation as the canonical fixture, but P2's own high (113.0) sits 3.0 MBR
    above P1's (110.0) -- well beyond `PLAYBOOK_TOPS_MATCH_MBR` (1.0). No signal by default; the
    control (tops_match_mbr widened to 5.0) fires exactly one, at the same gap, proving the match
    tolerance specifically is what rejected it."""
    bars = _canonical_double_top_bars("DTNM", p2_high=113.0)
    signal = detect_double_top(
        bars, _DOUBLE_TOP_BASELINE, "DTNM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert signal is None

    relaxed = {**_PARAMS, "tops_match_mbr": 5.0}
    relaxed_signal = detect_double_top(
        bars, _DOUBLE_TOP_BASELINE, "DTNM", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, relaxed,
    )
    assert relaxed_signal is not None
    assert relaxed_signal["geometry"]["tops_gap_mbr"] == pytest.approx(3.0)
    assert relaxed_signal["geometry"]["tops_gap_mbr"] > _PARAMS["tops_match_mbr"]


# --- TC-10: price collapsing through the valley INSIDE p2's own pivot-confirmation window fails
# closed -- the pivot-confirmation-delay rule, applied to double_top for the first time.


def test_double_top_fails_closed_when_price_collapses_inside_p2_confirmation_window():
    """TC-10: the SAME formation as the canonical fixture, but slot 14 (strictly inside P2's own
    confirmation window, slots 14-16) already breaks below the valley (low=96.5 < 97.0) -- this
    pair fails closed. No signal fires (there is no other candidate pivot pair in this fixture for
    the search to fall back to)."""
    bars = _canonical_double_top_bars("DTFC", idx14_low=96.5)
    signal = detect_double_top(
        bars, _DOUBLE_TOP_BASELINE, "DTFC", SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert signal is None


# --- double_top/double_bottom's own truncate/mutate lookahead property test (TC-8) -----------------

_DOUBLE_EXTREME_LOOKAHEAD_FIXTURES = [
    (detect_double_top, _canonical_double_top_bars(), "DT1"),
    (detect_double_bottom, _canonical_double_bottom_bars(), "DB1"),
]


@pytest.mark.parametrize("detect_fn, bars, symbol", _DOUBLE_EXTREME_LOOKAHEAD_FIXTURES)
def test_double_extreme_truncating_to_the_trigger_bar_reproduces_the_core_detection_fields(
    detect_fn, bars, symbol
):
    full = detect_fn(bars, _DOUBLE_TOP_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
    assert full is not None
    trigger_idx = full["geometry"]["slots_to_break"]

    truncated = detect_fn(
        bars[: trigger_idx + 1], _DOUBLE_TOP_BASELINE, symbol, SESSION_DATE,
        [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert truncated is not None
    assert truncated["trigger_price"] == full["trigger_price"]
    assert truncated["invalidation_price"] == full["invalidation_price"]
    assert truncated["geometry"] == full["geometry"]


@pytest.mark.parametrize("detect_fn, bars, symbol", _DOUBLE_EXTREME_LOOKAHEAD_FIXTURES)
def test_double_extreme_mutating_a_bar_after_the_trigger_changes_nothing(detect_fn, bars, symbol):
    full = detect_fn(bars, _DOUBLE_TOP_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS)
    assert full is not None
    trigger_idx = full["geometry"]["slots_to_break"]
    assert trigger_idx + 1 < len(bars), "fixture must carry at least one bar after the trigger"

    mutated = list(bars)
    victim = mutated[trigger_idx + 1]
    mutated[trigger_idx + 1] = RawBar(
        victim.symbol, victim.timeframe, victim.epoch,
        victim.open * 3.0, victim.high * 5.0, victim.low * 0.2, victim.close * 4.0, victim.volume * 50,
    )
    mutated_result = detect_fn(
        mutated, _DOUBLE_TOP_BASELINE, symbol, SESSION_DATE, [], _EMPTY_INDEX_BASELINE, _PARAMS,
    )
    assert mutated_result == full
