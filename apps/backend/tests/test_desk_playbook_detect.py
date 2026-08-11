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
from app.research.desk_playbook_detect import (
    detect_capitulation,
    detect_cup_handle,
    detect_dbi,
    detect_euphoria,
    detect_jbe,
    detect_opening_range_breaks,
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
