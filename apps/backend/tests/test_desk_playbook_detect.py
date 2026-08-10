"""``desk_playbook_detect.py`` -- the opening-range-break detector pair (Era B2, J-01,
``docs/playbook-detector-spec.md`` §3.1-3.2): fixture goldens for the canonical firing case (TC-2),
the wide-OR near-miss (TC-3), the 1m->5m opening-range degrade on a firing signal (TC-4), the
both-sides ambiguous outside bar (TC-5), and the generic lookahead property test (TC-6) -- built
so J-04/J-05/J-06 extend ``_LOOKAHEAD_FIXTURES`` with their own detectors' fixtures without
touching the property test's own body.

``detect_opening_range_breaks`` is tested directly as a pure function of bars + a hand-built
``or_result``/``baseline`` dict -- ``desk_playbook_features.py``'s primitives that would normally
produce those dicts are already covered by ``test_desk_playbook_features.py``; this file is
detector logic only. ``test_desk_playbook.py`` separately proves the full bar-store-backed walk
(``compute_playbook``) wires the primitives into the detector correctly."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.providers.adapters.base import RawBar
from app.research.desk_playbook import playbook_parameters
from app.research.desk_playbook_detect import detect_opening_range_breaks

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
