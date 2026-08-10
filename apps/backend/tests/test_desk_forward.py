"""Forward-test era v2: ``desk_forward.py`` / ``desk_forward_compute.py`` — touch-anchored
forward returns in PERCENT over a recorded desk screen snapshot, with the exit-re-arm touch rule,
the modeled limit-fill entry, trading-bar horizons truncated-with-disclosure, per-touch long/short
max drawdown, per-row untruncated-only averages, and the seeded random-minute baseline.

The coverage map follows the design-review test matrix: touch predicate/re-arm/cap/beyond-cap;
whole-day-inside-band; gap-beyond-band exclusion + disclosures; limit-fill both sides; the
screen-date-session window boundary (out-of-sample by ``tradability._resolve_basis``'s own
strictly-before filter); the 1m-else-5m ladder ON the date; offsets 1/5/60/240 vs 1/12/48;
truncation flags + the exact-last-bar non-truncation; degenerate last-bar/single-bar sessions;
``to_close``; MDD hand-checks + the zero clamp + the touch-bar smear; baseline determinism
(pinned anchor indices as the stdlib-drift tripwire, row-order independence, cancel-rerun
byte-identity, global-RNG immunity, the k=min rule, close-anchored entries); pools/percent/
averages; signature narrowing (coarse series can never re-key); parameters liveness; store
discipline; manager single-flight/cancel; routes incl. the populated bulk-list projection; CLI;
register lexicon; fingerprint stability (zero new Config fields by construction)."""

from __future__ import annotations

import json
import random
import sys
import threading
import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG, Config
from app.main import app
from app.providers.adapters.base import RawBar
from app.research import desk_forward as desk_forward_module
from app.research import desk_forward_compute
from app.research.bars import BarStore
from app.research.desk_forward import (
    DESK_FORWARD_HORIZONS_MINUTES,
    DESK_FORWARD_MAX_TOUCHES_PER_ROW,
    DESK_FORWARD_MEASURE_KEYS,
    FORWARD_REGISTER,
    ForwardAlreadyRecorded,
    ForwardIntegrityError,
    ForwardScreenNotFound,
    ForwardStore,
    _touch_scan,
    compute_forward,
    compute_forward_input_signature,
    forward_row_counts,
    no_fine_bars_reason,
    resolve_desk_forward_dir,
)
from app.research.desk_forward_compute import DeskForwardComputeManager, run_forward_and_record
from app.research.desk_forward_log import ForwardRunStore
from app.research.desk_forward_pins import resolve_desk_forward_pins
from app.research.bar_index import BarIndex
from app.research.desk_routes import get_desk_forward_compute_manager
from app.research.desk_screen import ScreenStore
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore
from test_copy_discipline import find_violations

# One synthetic screen: as_of = the screen date's own last second; the touch window is the screen
# date's OWN session (out-of-sample: the wall map's basis resolution reads sessions strictly
# before the screen date). 1m bars start at the NYSE open, 13:30Z.
SCREEN_DATE = "2026-06-22"
AS_OF = "2026-06-22T23:59:59Z"
E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z

# ScreenStore ids are pure functions of the 5-pin key; the fixture pins below make screen_id
# deterministic, which the pinned-anchor-indices tripwire relies on.
FIXTURE_SCREEN_ID = "screen-2026-06-22-f011abb58d07"


def _minute(i: int) -> float:
    return E_OPEN + i * 60.0


def _bar(symbol: str, timeframe: str, epoch: float, o: float, h: float, low: float, c: float) -> RawBar:
    return RawBar(symbol, timeframe, epoch, o, h, low, c, 1000)


def _plant(bar_store: BarStore, symbol: str, timeframe: str, bars: list[RawBar]) -> dict:
    return bar_store.record(
        symbol=symbol, timeframe=timeframe,
        window_start_utc="2026-06-01T00:00:00Z", window_end_utc="2026-06-30T00:00:00Z",
        feed="test", bars=bars,
    )


def _screen_row(
    symbol: str, side: str, price_low: float | None = 99.0, price_high: float | None = 100.0
) -> dict:
    row = {
        "symbol": symbol, "side": side, "band_class": "A", "distance_bps": 0.0,
        "band_score": 1.0, "coverage": {}, "tick_evidence": False,
    }
    if price_low is not None:
        row["price_low"] = price_low
    if price_high is not None:
        row["price_high"] = price_high
    return row


def _record_screen(screen_store: ScreenStore, rows: list[dict]) -> dict:
    return screen_store.record(
        screen_date=SCREEN_DATE, as_of=AS_OF,
        universe_snapshot_id="universe-test", config_fingerprint=CONFIG.config_fingerprint(),
        bar_store_signature="sig-a", rows=rows, skipped=[],
    )


def _above_band_bar(symbol: str, i: int, tf: str = "1m") -> RawBar:
    """A bar safely ABOVE the default support band [99, 100] (no overlap)."""
    return _bar(symbol, tf, _minute(i), 101.0, 101.5, 100.5, 101.0)


def _in_band_bar(symbol: str, i: int, tf: str = "1m", low: float = 99.5, close: float = 100.2) -> RawBar:
    """A bar dipping into the default support band from above."""
    return _bar(symbol, tf, _minute(i), 100.6, 100.8, low, close)


FIXTURE_SYMBOL = "SESS"


def _plant_fixture_session(bar_store: BarStore, symbol: str = FIXTURE_SYMBOL) -> None:
    """A 90-bar 1m session that re-touches the default band [99, 100] several times and then
    drifts away with a widening range. Deliberately NOT flat: the per-horizon assertions it
    supports would pass vacuously on a session where every window saw the same extremes. Fully
    deterministic -- a fixed arithmetic shape, never an RNG."""
    bars = []
    for i in range(90):
        swing = (i % 7) - 3  # -3..3, so price re-enters the band every seventh minute
        close = 100.0 + swing * 0.25 + i * 0.02
        bars.append(
            _bar(
                symbol, "1m", _minute(i),
                close - swing * 0.05,          # open
                close + 0.20 + i * 0.01,       # high, widening
                close - 0.30 - i * 0.01,       # low, widening
                close,
            )
        )
    _plant(bar_store, symbol, "1m", bars)


@pytest.fixture
def env(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    screen_store = ScreenStore(tmp_path / "screen")
    forward_store = ForwardStore(tmp_path / "forward")
    return bar_store, screen_store, forward_store


def _canonical(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, default=str)


# --- touch detection -------------------------------------------------------------------------------


def test_touch_overlap_and_exit_rearm_hand_checked(env):
    """Overlap counts while armed; a still-overlapping bar never re-counts; re-arm requires a bar
    FULLY exiting the band (the setups.py semantics, copied with attribution)."""
    bar_store, screen_store, _ = env
    bars = [
        _in_band_bar("AAA", 0),          # touch 1
        _in_band_bar("AAA", 1),          # still overlapping -- not a new touch
        _above_band_bar("AAA", 2),       # full exit -- re-arms
        _in_band_bar("AAA", 3),          # touch 2
    ]
    _plant(bar_store, "AAA", "1m", bars)
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    row = result["rows"][0]
    assert row["touch_count"] == 2
    assert [t["at_utc"][:19] for t in row["touches"]] == [
        "2026-06-22T13:30:00", "2026-06-22T13:33:00",
    ]
    # A partial move that never fully exits does not re-arm: verified at the scanner level.
    partial = [
        _in_band_bar("X", 0),
        _bar("X", "1m", _minute(1), 100.2, 100.4, 99.9, 100.1),   # still overlaps (low <= 100)
        _in_band_bar("X", 2),
    ]
    indices, total, _beyond, _gap = _touch_scan(partial, 99.0, 100.0, "support", 8)
    assert indices == [0] and total == 1


def test_band_wider_than_session_range_is_exactly_one_touch(env):
    """Price inside the band all day: armed never resets -- exactly one touch, at bar 0, entered
    at that bar's open (an in-band open is an 'open'-kind fill)."""
    bar_store, screen_store, _ = env
    bars = [_bar("WIDE", "1m", _minute(i), 99.5, 99.8, 99.2, 99.6) for i in range(5)]
    _plant(bar_store, "WIDE", "1m", bars)
    screen = _record_screen(screen_store, [_screen_row("WIDE", "support", 98.0, 101.0)])
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]
    assert row["touch_count"] == 1
    assert row["touches"][0]["entry_price"] == 99.5
    assert row["touches"][0]["entry_kind"] == "open"


def test_cap_and_beyond_cap_disclosed_and_baseline_k_matches_the_cap(env):
    """More re-armed touches than the cap: the cap holds, the excess is disclosed, and the
    baseline draws k = min(CAPPED count, bars in session) anchors."""
    bar_store, screen_store, _ = env
    bars: list[RawBar] = []
    for pair in range(10):  # alternate in/out -> 10 genuine re-armed touches over 20 bars
        bars.append(_in_band_bar("CAP", pair * 2))
        bars.append(_above_band_bar("CAP", pair * 2 + 1))
    _plant(bar_store, "CAP", "1m", bars)
    screen = _record_screen(screen_store, [_screen_row("CAP", "support")])
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]
    assert row["touch_count"] == DESK_FORWARD_MAX_TOUCHES_PER_ROW == 8
    assert row["touches_beyond_cap"] == 2
    assert len(row["baseline_anchors"]) == 8  # k = min(8, 20)


def test_gap_fully_beyond_band_is_not_a_touch_but_disclosed(env):
    """A bar entirely on the wall's far side is NOT a touch under the overlap predicate -- even
    though a resting limit at the edge would have filled -- and the exclusion is disclosed."""
    bar_store, screen_store, _ = env
    bars = [
        _above_band_bar("GAP", 0),
        _bar("GAP", "1m", _minute(1), 98.5, 98.8, 98.0, 98.4),   # entirely BELOW [99,100]
        _bar("GAP", "1m", _minute(2), 99.2, 99.6, 99.0, 99.5),   # re-entry -> the FIRST touch
    ]
    _plant(bar_store, "GAP", "1m", bars)
    screen = _record_screen(screen_store, [_screen_row("GAP", "support")])
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]
    assert row["touch_count"] == 1
    assert row["touches"][0]["at_utc"].startswith("2026-06-22T13:32:00")
    assert row["bars_fully_beyond_band"] == 1
    assert row["gap_through_before_first_touch"] is True


def test_entry_limit_fill_both_sides(env):
    """Support: a bar opening above the edge fills AT the edge; a bar opening inside fills at its
    open. Resistance mirrors via max(open, price_low)."""
    bar_store, screen_store, _ = env
    _plant(bar_store, "SUP", "1m", [
        _bar("SUP", "1m", _minute(0), 100.6, 100.8, 99.5, 100.2),  # opens above 100 -> edge
        _above_band_bar("SUP", 1),
        _bar("SUP", "1m", _minute(2), 99.7, 100.1, 99.4, 99.9),    # opens inside -> open
    ])
    _plant(bar_store, "RES", "1m", [
        _bar("RES", "1m", _minute(0), 98.4, 99.3, 98.2, 98.9),     # opens below 99 -> edge
        _bar("RES", "1m", _minute(1), 98.0, 98.5, 97.8, 98.2),     # full exit below -> re-arm
        _bar("RES", "1m", _minute(2), 99.4, 99.8, 99.1, 99.5),     # opens inside -> open
    ])
    screen = _record_screen(screen_store, [
        _screen_row("SUP", "support"),                 # band [99, 100]
        _screen_row("RES", "resistance", 99.0, 100.0),  # band [99, 100], approached from below
    ])
    rows = {r["symbol"]: r for r in compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"]}
    sup = rows["SUP"]["touches"]
    assert (sup[0]["entry_price"], sup[0]["entry_kind"]) == (100.0, "edge")
    assert (sup[1]["entry_price"], sup[1]["entry_kind"]) == (99.7, "open")
    res = rows["RES"]["touches"]
    assert (res[0]["entry_price"], res[0]["entry_kind"]) == (99.0, "edge")
    assert (res[1]["entry_price"], res[1]["entry_kind"]) == (99.4, "open")


# --- the window ------------------------------------------------------------------------------------


def test_window_is_the_screen_dates_own_session_only(env):
    """Bars from the prior session, the next session, and a pathological sub-second bar past
    as_of never enter the scan -- only the screen date's own session bars do."""
    bar_store, screen_store, _ = env
    day = 86400.0
    _plant(bar_store, "WIN", "1m", [
        _bar("WIN", "1m", _minute(0) - day, 100.6, 100.8, 99.5, 100.2),  # prior session, in band
        _above_band_bar("WIN", 0),                                        # the date's session
        _bar("WIN", "1m", 1782172799.5, 99.5, 99.9, 99.2, 99.6),          # 23:59:59.5Z -- past as_of
        _bar("WIN", "1m", _minute(0) + day, 100.6, 100.8, 99.4, 100.2),   # next session, in band
    ])
    screen = _record_screen(screen_store, [_screen_row("WIN", "support")])
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]
    assert row["touch_basis"]["bars_in_session"] == 1  # only the date's real session bar
    assert row["touch_count"] == 0  # that bar never touches; the poisoned/in-band others excluded


def test_no_fine_bars_on_the_date_is_an_honest_row_absence(env):
    bar_store, screen_store, _ = env
    _plant(bar_store, "COARSE", "1h", [_bar("COARSE", "1h", _minute(0), 99.5, 100.5, 99.0, 100.0)])
    screen = _record_screen(screen_store, [_screen_row("COARSE", "support")])
    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    row = result["rows"][0]
    assert row["touch_basis"] is None
    assert "no 1m or 5m bars recorded" in row["reason"]
    assert result["rows_with_touches"] == 0


def test_ladder_prefers_1m_else_5m_on_the_date_and_5m_offsets_hold(env):
    """A symbol with only 5m bars on the date uses the 5m series: the '1m' label is an honest
    absence, and the 5m/1h/4h offsets are 1/12/48 bars."""
    bar_store, screen_store, _ = env
    five = [_bar("FIVE", "5m", E_OPEN + i * 300.0, 100.6, 100.8, 99.5, 100.0 + i * 0.1) for i in range(14)]
    _plant(bar_store, "FIVE", "5m", five)
    screen = _record_screen(screen_store, [_screen_row("FIVE", "support")])
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]
    assert row["touch_basis"]["timeframe"] == "5m"
    touch = row["touches"][0]  # bar 0 touches (low 99.5); entry = edge 100.0
    assert touch["horizons"]["1m"]["return_pct"] is None
    assert "finer than the 5m touch series" in touch["horizons"]["1m"]["reason"]
    # 5m -> 1 bar: close 100.1 vs entry 100.0 = +0.1%; 1h -> 12 bars: close 101.2 -> +1.2%
    assert touch["horizons"]["5m"]["return_pct"] == pytest.approx(0.1)
    assert touch["horizons"]["1h"]["return_pct"] == pytest.approx(1.2)
    # 4h -> 48 bars: past the 14-bar session -> truncated at the last bar (13 bars later = 65 min)
    assert touch["horizons"]["4h"]["truncated"] is True
    assert touch["horizons"]["4h"]["effective_minutes"] == 65


# --- horizons, truncation, to_close ---------------------------------------------------------------


def test_horizon_offsets_truncation_and_exact_last_bar(env):
    bar_store, screen_store, _ = env
    # 6 bars: touch at index 0; 5m target = index 5 == last -> NOT truncated; 1h truncated.
    bars = [_in_band_bar("HZ", 0)] + [
        _bar("HZ", "1m", _minute(i), 100.0, 100.4, 99.8, 100.0 + i * 0.01) for i in range(1, 6)
    ]
    _plant(bar_store, "HZ", "1m", bars)
    screen = _record_screen(screen_store, [_screen_row("HZ", "support")])
    touch = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]["touches"][0]
    assert touch["horizons"]["1m"]["truncated"] is False
    assert touch["horizons"]["1m"]["effective_minutes"] == 1
    assert touch["horizons"]["5m"]["truncated"] is False          # target exactly the last bar
    assert touch["horizons"]["5m"]["effective_minutes"] == 5
    assert touch["horizons"]["1h"]["truncated"] is True
    assert touch["horizons"]["1h"]["effective_minutes"] == 5
    assert touch["minutes_to_close"] == 5
    # entry = edge 100.0; last close 100.05 -> +0.05%
    assert touch["to_close_pct"] == pytest.approx(0.05)
    assert touch["horizons"]["1h"]["return_pct"] == pytest.approx(0.05)  # measured AT the last bar


def test_touch_on_the_last_bar_is_degenerate_but_honest(env):
    bar_store, screen_store, _ = env
    bars = [_above_band_bar("LAST", 0), _in_band_bar("LAST", 1, close=100.3)]
    _plant(bar_store, "LAST", "1m", bars)
    screen = _record_screen(screen_store, [_screen_row("LAST", "support")])
    touch = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]["touches"][0]
    for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES:
        assert touch["horizons"][label]["truncated"] is True
        assert touch["horizons"][label]["effective_minutes"] == 0
        assert touch["horizons"][label]["return_pct"] == pytest.approx(touch["to_close_pct"])
    assert touch["minutes_to_close"] == 0


def test_single_bar_session_end_to_end(env):
    bar_store, screen_store, _ = env
    _plant(bar_store, "ONE", "1m", [_in_band_bar("ONE", 0, low=99.0, close=100.0)])
    screen = _record_screen(screen_store, [_screen_row("ONE", "support")])
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]
    assert row["touch_count"] == 1
    assert len(row["baseline_anchors"]) == 1  # the only bar
    assert row["baseline_anchors"][0]["entry_kind"] == "close"


# --- MDD -------------------------------------------------------------------------------------------


def test_mdd_hand_checked_zero_clamp_and_touch_bar_smear(env):
    bar_store, screen_store, _ = env
    # Touch bar's own low 99.0 (the pre-touch smear counts); later high 102.0.
    bars = [
        _bar("MDD", "1m", _minute(0), 100.6, 100.8, 99.0, 100.2),   # touch, entry = edge 100.0
        _bar("MDD", "1m", _minute(1), 100.2, 102.0, 100.0, 101.5),
    ]
    _plant(bar_store, "MDD", "1m", bars)
    # A second symbol whose session never trades below its entry: the long side is a REAL zero.
    _plant(bar_store, "UP", "1m", [
        _bar("UP", "1m", _minute(0), 99.5, 100.4, 99.5, 100.2),     # opens inside -> entry 99.5
        _bar("UP", "1m", _minute(1), 100.2, 101.0, 99.8, 100.9),
    ])
    screen = _record_screen(
        screen_store, [_screen_row("MDD", "support"), _screen_row("UP", "support")]
    )
    rows = {r["symbol"]: r for r in compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"]}
    mdd = rows["MDD"]["touches"][0]
    assert mdd["mdd_long_pct"] == pytest.approx(-1.0)    # (99-100)/100
    assert mdd["mdd_short_pct"] == pytest.approx(-2.0)   # (100-102)/100
    up = rows["UP"]["touches"][0]
    assert up["mdd_long_pct"] == 0.0                      # clamped: a real measured zero


def test_the_session_mdds_are_unchanged_by_the_running_prefix_rewrite(env):
    """The per-horizon drawdowns are read off a running-extreme pass over the SAME tail the
    session MDD always used, so the session values must still equal the original one-shot formula
    -- `min(low over the tail)` / `max(high over the tail)` against the entry, clamped. This is the
    one place that refactor could have silently moved a recorded number."""
    bar_store, screen_store, _ = env
    bars = [_in_band_bar("SAME", 0, low=99.4, close=100.2)] + [
        _bar("SAME", "1m", _minute(i), 100.2, 100.0 + i * 0.30, 100.0 - i * 0.20, 100.1)
        for i in range(1, 9)
    ]
    _plant(bar_store, "SAME", "1m", bars)
    screen = _record_screen(screen_store, [_screen_row("SAME", "support")])
    touch = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]["touches"][0]

    entry = touch["entry_price"]
    expected_long = min(0.0, (min(bar.low for bar in bars) - entry) / entry * 100.0)
    expected_short = min(0.0, (entry - max(bar.high for bar in bars)) / entry * 100.0)
    assert touch["mdd_long_pct"] == pytest.approx(expected_long)
    assert touch["mdd_short_pct"] == pytest.approx(expected_short)
    # 4h truncates to the last bar on a 9-bar session, so its window IS the session -- the two
    # must therefore agree EXACTLY rather than merely approximately.
    assert touch["horizons"]["4h"]["mdd_long_pct"] == touch["mdd_long_pct"]
    assert touch["horizons"]["4h"]["mdd_short_pct"] == touch["mdd_short_pct"]


def test_each_horizon_carries_the_drawdown_of_its_own_window_hand_checked(env):
    """A 1m return must not be reported beside a drawdown measured over the whole session. Bars
    are built so the adverse excursion deepens strictly AFTER the 1m mark, which is exactly the
    case a single session-wide number could not tell apart."""
    bar_store, screen_store, _ = env
    bars = [
        # touch bar: opens above the band, entry = edge 100.0; its own low 99.8 is the 1m window's
        # worst (the disclosed pre-touch smear).
        _bar("MW", "1m", _minute(0), 100.6, 100.4, 99.8, 100.1),
        _bar("MW", "1m", _minute(1), 100.1, 100.5, 99.5, 100.0),   # 1m window ends here
        _bar("MW", "1m", _minute(2), 100.0, 101.0, 99.0, 100.4),
        _bar("MW", "1m", _minute(3), 100.4, 102.0, 98.0, 100.6),
        _bar("MW", "1m", _minute(4), 100.6, 103.0, 97.0, 100.8),
        _bar("MW", "1m", _minute(5), 100.8, 104.0, 96.0, 101.0),   # 5m window ends here
    ]
    _plant(bar_store, "MW", "1m", bars)
    screen = _record_screen(screen_store, [_screen_row("MW", "support")])
    touch = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]["touches"][0]

    # 1m = bars[0..1]: worst low 99.5, worst high 100.5, against entry 100.0.
    assert touch["horizons"]["1m"]["mdd_long_pct"] == pytest.approx(-0.5)
    assert touch["horizons"]["1m"]["mdd_short_pct"] == pytest.approx(-0.5)
    # 5m = bars[0..5]: worst low 96.0, worst high 104.0.
    assert touch["horizons"]["5m"]["mdd_long_pct"] == pytest.approx(-4.0)
    assert touch["horizons"]["5m"]["mdd_short_pct"] == pytest.approx(-4.0)
    # The session number is the widest of all -- the one this used to be the ONLY value for.
    assert touch["mdd_long_pct"] == pytest.approx(-4.0)


def test_a_horizons_drawdown_is_never_shallower_than_a_shorter_horizons(env):
    """Nested windows: a longer horizon can only ever see more of the excursion. Proven over the
    real fixture session rather than a hand-built one, across every touch AND every baseline
    anchor -- the property must hold for the null too, or the comparison is not like-for-like."""
    bar_store, screen_store, _ = env
    _plant_fixture_session(bar_store)
    screen = _record_screen(screen_store, [_screen_row(FIXTURE_SYMBOL, "support")])
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]

    events = row["touches"] + row["baseline_anchors"]
    assert events, "the monotonicity scan is vacuous"
    labels = [label for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES]
    for event in events:
        measured = [
            event["horizons"][label] for label in labels
            if event["horizons"][label]["return_pct"] is not None
        ]
        for shorter, longer in zip(measured, measured[1:]):
            assert longer["mdd_long_pct"] <= shorter["mdd_long_pct"]
            assert longer["mdd_short_pct"] <= shorter["mdd_short_pct"]
        for measure in measured:
            assert measure["mdd_long_pct"] <= 0.0 and measure["mdd_short_pct"] <= 0.0
        # The session pair is the widest window of all.
        for measure in measured:
            assert event["mdd_long_pct"] <= measure["mdd_long_pct"]
            assert event["mdd_short_pct"] <= measure["mdd_short_pct"]


# --- the exit price every return was measured to ---------------------------------------------------


def test_exit_price_is_the_close_at_the_horizons_own_measurement_point(env):
    bar_store, screen_store, _ = env
    bars = [_in_band_bar("EX", 0)] + [
        _bar("EX", "1m", _minute(i), 100.0, 100.4, 99.8, 100.0 + i * 0.01) for i in range(1, 6)
    ]
    _plant(bar_store, "EX", "1m", bars)
    screen = _record_screen(screen_store, [_screen_row("EX", "support")])
    touch = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]["touches"][0]

    assert touch["horizons"]["1m"]["exit_price"] == pytest.approx(bars[1].close)
    assert touch["horizons"]["5m"]["exit_price"] == pytest.approx(bars[5].close)
    # Truncated: measured AT the last bar, so the exit is the last bar's close -- the SAME point
    # `return_pct` was measured to, never the price at the horizon that never arrived.
    assert touch["horizons"]["1h"]["truncated"] is True
    assert touch["horizons"]["1h"]["exit_price"] == pytest.approx(bars[-1].close)
    assert touch["close_price"] == pytest.approx(bars[-1].close)


def test_the_exit_price_reproduces_the_served_return_on_both_sides(env):
    """The whole point of serving it: (exit - entry) / entry, signed to the row's side, must
    reproduce the served return exactly. Checked on a resistance row too, where the sign flips."""
    bar_store, screen_store, _ = env
    _plant_fixture_session(bar_store)
    screen = _record_screen(
        screen_store,
        [_screen_row(FIXTURE_SYMBOL, "support"), _screen_row(FIXTURE_SYMBOL, "resistance")],
    )
    rows = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"]
    checked = 0
    for row in rows:
        sign = -1.0 if row["side"] == "resistance" else 1.0
        for event in row["touches"] + row["baseline_anchors"]:
            entry = event["entry_price"]
            for measure in event["horizons"].values():
                if measure["return_pct"] is None:
                    continue
                recomputed = sign * (measure["exit_price"] - entry) / entry * 100.0
                assert measure["return_pct"] == pytest.approx(recomputed)
                checked += 1
            assert event["to_close_pct"] == pytest.approx(
                sign * (event["close_price"] - entry) / entry * 100.0
            )
    assert checked, "the exit-price cross-check is vacuous"


def test_a_horizon_finer_than_the_series_carries_every_key_present_and_null(env):
    """The honest-absence branch. A missing key would read as "this record predates the field";
    a null reads as "measured, no value" -- two different facts, never conflated."""
    bar_store, screen_store, _ = env
    _plant(bar_store, "FINE", "5m", [
        _bar("FINE", "5m", _minute(0), 100.6, 100.8, 99.8, 100.2),
        _bar("FINE", "5m", _minute(5), 100.2, 100.9, 100.0, 100.5),
    ])
    screen = _record_screen(screen_store, [_screen_row("FINE", "support")])
    touch = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]["touches"][0]

    absent = touch["horizons"]["1m"]
    assert absent["reason"] is not None
    for key in ("return_pct", "exit_price", "mdd_long_pct", "mdd_short_pct", "effective_minutes"):
        assert key in absent, f"{key} must be PRESENT and null, never missing"
        assert absent[key] is None


def test_baseline_anchors_carry_the_identical_new_fields(env):
    """Like-for-like: the null is measured by the same function, so it gains every field a touch
    gains -- otherwise the comparison quietly becomes apples-to-oranges."""
    bar_store, screen_store, _ = env
    _plant_fixture_session(bar_store)
    screen = _record_screen(screen_store, [_screen_row(FIXTURE_SYMBOL, "support")])
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]

    assert row["touches"] and row["baseline_anchors"]
    for anchor in row["baseline_anchors"]:
        assert "close_price" in anchor
        for measure in anchor["horizons"].values():
            assert set(measure) == set(row["touches"][0]["horizons"]["5m"])


# --- baseline --------------------------------------------------------------------------------------


def test_baseline_anchor_indices_are_pinned_for_the_fixture_seed(env):
    """The stdlib-drift tripwire: the partial Fisher-Yates over rng.randrange owns its byte
    stream, so these exact indices are the contract. If this test ever fails after an interpreter
    upgrade, the RNG contract itself drifted -- investigate before touching the pin."""
    bar_store, screen_store, _ = env
    bars = [_in_band_bar("PINNED", 0), _above_band_bar("PINNED", 1), _in_band_bar("PINNED", 2),
            _above_band_bar("PINNED", 3), _in_band_bar("PINNED", 4)] + [
        _above_band_bar("PINNED", i) for i in range(5, 10)
    ]
    _plant(bar_store, "PINNED", "1m", bars)  # 10 bars, 3 re-armed touches
    screen = _record_screen(screen_store, [_screen_row("PINNED", "support")])
    assert screen["id"] == FIXTURE_SCREEN_ID  # the pinned indices are keyed by this id
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]
    assert row["touch_count"] == 3
    anchor_minutes = [a["at_utc"][14:16] for a in row["baseline_anchors"]]
    assert anchor_minutes == ["30", "37", "39"]  # indices [0, 7, 9] of the 13:30 session


def test_baseline_is_row_order_independent_and_cancel_rerun_byte_identical(env, tmp_path):
    bar_store, _screen_store, _ = env
    for symbol in ("AAA", "BBB"):
        _plant(bar_store, symbol, "1m", [
            _in_band_bar(symbol, 0), _above_band_bar(symbol, 1), _in_band_bar(symbol, 2),
        ])
    store_ab = ScreenStore(tmp_path / "screen-ab")
    store_ba = ScreenStore(tmp_path / "screen-ba")
    screen_ab = store_ab.record(
        screen_date=SCREEN_DATE, as_of=AS_OF, universe_snapshot_id="universe-test",
        config_fingerprint=CONFIG.config_fingerprint(), bar_store_signature="sig-a",
        rows=[_screen_row("AAA", "support"), _screen_row("BBB", "support")], skipped=[],
    )
    screen_ba = store_ba.record(
        screen_date=SCREEN_DATE, as_of=AS_OF, universe_snapshot_id="universe-test",
        config_fingerprint=CONFIG.config_fingerprint(), bar_store_signature="sig-b",
        rows=[_screen_row("BBB", "support"), _screen_row("AAA", "support")], skipped=[],
    )
    fp = CONFIG.config_fingerprint()
    ab = compute_forward(screen_ab, bar_store, fp)
    ba = compute_forward(screen_ba, bar_store, fp)
    # Per-symbol anchors depend only on (seed, screen_id, symbol) -- with the SAME screen the
    # walk order cannot matter; across the two screens only screen_id differs by design.
    by_ab = {r["symbol"]: r["baseline_anchors"] for r in ab["rows"]}
    ab_again = compute_forward(screen_ab, bar_store, fp)
    assert _canonical(ab) == _canonical(ab_again)  # full byte-identity on a re-run
    assert {r["symbol"] for r in ba["rows"]} == set(by_ab)

    # Cancel-then-rerun: a walk aborted after the first row records nothing and a fresh full run
    # is byte-identical to an uninterrupted one.
    seen: list[str] = []

    def abort_after_first() -> bool:
        return len(seen) >= 1

    partial = compute_forward(
        screen_ab, bar_store, fp,
        progress=lambda entry: seen.append(entry["symbol"]), should_abort=abort_after_first,
    )
    assert len(partial["rows"]) < len(ab["rows"])
    assert _canonical(compute_forward(screen_ab, bar_store, fp)) == _canonical(ab)


def test_no_global_rng_state_is_used(env, monkeypatch):
    bar_store, screen_store, _ = env
    _plant(bar_store, "AAA", "1m", [
        _in_band_bar("AAA", 0), _above_band_bar("AAA", 1), _in_band_bar("AAA", 2),
        _above_band_bar("AAA", 3), _in_band_bar("AAA", 4), _above_band_bar("AAA", 5),
    ])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    fp = CONFIG.config_fingerprint()
    random.seed(0)
    first = compute_forward(screen, bar_store, fp)
    random.seed(12345)
    second = compute_forward(screen, bar_store, fp)
    assert _canonical(first) == _canonical(second)

    def _trap(*_args, **_kwargs):  # module-level random functions must never be touched
        raise AssertionError("module-level random.* called")

    monkeypatch.setattr(random, "random", _trap)
    monkeypatch.setattr(random, "randrange", _trap)
    monkeypatch.setattr(random, "sample", _trap)
    third = compute_forward(screen, bar_store, fp)
    assert _canonical(third) == _canonical(first)


def test_baseline_k_capped_by_session_size_and_anchors_use_bar_close(env):
    bar_store, screen_store, _ = env
    # 5 bars, alternating -> 3 touches; a tiny session bounds k at min(touches, bars).
    bars = [
        _in_band_bar("CAPK", 0, close=100.2), _above_band_bar("CAPK", 1),
        _in_band_bar("CAPK", 2, close=100.1), _above_band_bar("CAPK", 3),
        _in_band_bar("CAPK", 4, close=100.3),
    ]
    _plant(bar_store, "CAPK", "1m", bars)
    screen = _record_screen(screen_store, [_screen_row("CAPK", "support")])
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]
    assert row["touch_count"] == 3
    assert len(row["baseline_anchors"]) == 3
    for anchor in row["baseline_anchors"]:
        assert anchor["entry_kind"] == "close"
    # One anchor hand-check: identical math to a touch, entered at the anchor bar's close.
    first = row["baseline_anchors"][0]  # pinned index 0 for this fixture seed
    assert first["entry_price"] == 100.2
    assert first["to_close_pct"] == pytest.approx((100.3 - 100.2) / 100.2 * 100.0)
    assert row["anchors_in_band"] >= 1  # in-band anchors are kept, and reported


def test_zero_touch_row_contributes_nothing(env):
    bar_store, screen_store, _ = env
    _plant(bar_store, "FAR", "1m", [_above_band_bar("FAR", 0), _above_band_bar("FAR", 1)])
    screen = _record_screen(screen_store, [_screen_row("FAR", "support")])
    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    row = result["rows"][0]
    assert row["touch_count"] == 0
    assert row["touches"] == [] and row["baseline_anchors"] == []
    assert row["averages"]["to_close"] == {"n": 0, "mean_pct": None, "median_pct": None, "n_truncated": 0}
    assert result["rows_with_touches"] == 0 and result["total_touches"] == 0
    assert result["summary"]["support"]["to_close"]["touches"]["n"] == 0


# --- averages, summary, percent --------------------------------------------------------------------


def test_averages_pool_untruncated_only_with_truncation_counted(env):
    bar_store, screen_store, _ = env
    # Two touches: index 0 (1m horizon untruncated) and index 2 == last (1m truncated).
    bars = [
        _in_band_bar("TR", 0, close=100.2),
        _bar("TR", "1m", _minute(1), 100.5, 100.9, 100.4, 100.6),   # full exit above -> re-arm
        _in_band_bar("TR", 2, close=100.4),
    ]
    _plant(bar_store, "TR", "1m", bars)
    screen = _record_screen(screen_store, [_screen_row("TR", "support")])
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]
    assert row["touch_count"] == 2
    cell = row["averages"]["1m"]
    assert cell["n"] == 1 and cell["n_truncated"] == 1
    # The one untruncated 1m value: touch at bar 0, entry edge 100.0, bar-1 close 100.6 -> +0.6%.
    assert cell["mean_pct"] == pytest.approx(0.6)
    assert cell["median_pct"] == pytest.approx(0.6)
    assert row["averages"]["to_close"]["n"] == 2 and row["averages"]["to_close"]["n_truncated"] == 0
    # A horizon's own drawdowns share its window, so they share its truncation rule exactly -- a
    # truncated 1m measurement contributes neither its return nor its two drawdowns.
    for key in ("mdd_long_1m", "mdd_short_1m"):
        assert row["averages"][key]["n"] == 1 and row["averages"][key]["n_truncated"] == 1
    # The session-end trio is never truncated: the session end is simply where the bars stop.
    for key in ("mdd_long", "mdd_short"):
        assert row["averages"][key]["n"] == 2 and row["averages"][key]["n_truncated"] == 0


def test_the_per_horizon_averages_cover_every_declared_measure_key(env):
    """The averages block is keyed in DESK_FORWARD_MEASURE_KEYS' own declared order -- that order
    IS the column order both frontend tables render, so a drifted key set would silently drop or
    reorder a column."""
    bar_store, screen_store, _ = env
    _plant_fixture_session(bar_store)
    screen = _record_screen(screen_store, [_screen_row(FIXTURE_SYMBOL, "support")])
    row = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]

    assert list(row["averages"]) == list(DESK_FORWARD_MEASURE_KEYS)
    assert len(DESK_FORWARD_MEASURE_KEYS) == 15  # 4 horizons + to_close + 2 x (4 horizons + session)
    for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES:
        for key in (f"mdd_long_{label}", f"mdd_short_{label}"):
            assert key in row["averages"]


def test_declaring_the_horizon_shape_re_keys_the_record(env, monkeypatch):
    """The whole reason the shape rides in `parameters`: the 2-pin reuse rule compares input
    signatures, and the recorded row shape is not otherwise in one. Without this, a screen already
    measured would reuse a payload that predates a newly-added field, forever."""
    import app.research.desk_forward as forward_module

    bar_store, screen_store, _ = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    before = compute_forward(screen, bar_store, CONFIG.config_fingerprint())

    monkeypatch.setattr(
        forward_module, "DESK_FORWARD_HORIZON_MEASURES", ("return_pct", "exit_price"),
    )
    after = compute_forward(screen, bar_store, CONFIG.config_fingerprint())

    assert after["forward_input_signature"] != before["forward_input_signature"]
    assert after["parameters"]["horizon_measures"] == ["return_pct", "exit_price"]


def test_summary_pools_by_side_with_baseline_beside_and_percent_convention(env):
    bar_store, screen_store, _ = env
    _plant(bar_store, "AAA", "1m", [
        _in_band_bar("AAA", 0, close=100.2),
        _bar("AAA", "1m", _minute(1), 100.3, 100.6, 100.1, 100.5),  # +50 bps from entry -> 0.5
    ])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    cell = result["summary"]["support"]["1m"]
    assert cell["touches"]["n"] == 1
    assert cell["touches"]["mean_pct"] == pytest.approx(0.5)   # +50 bps serves 0.5, not 50
    # ONE anchor was drawn (matched count); whether its 1m horizon pooled or truncated depends on
    # which bar the seeded stream picked -- the invariant is the disclosed split, and to_close
    # (never truncated) always carries the matched n.
    assert cell["baseline"]["n"] + cell["baseline"]["n_truncated"] == 1
    assert result["summary"]["support"]["to_close"]["baseline"]["n"] == 1
    empty = result["summary"]["resistance"]["1m"]
    assert empty == {
        "touches": {"n": 0, "mean_pct": None, "median_pct": None, "n_truncated": 0},
        "baseline": {"n": 0, "mean_pct": None, "median_pct": None, "n_truncated": 0},
    }
    assert "_bps" not in _canonical(result)  # the percent convention, structurally
    assert set(result["summary"]["support"].keys()) == set(DESK_FORWARD_MEASURE_KEYS)


def test_parameters_register_and_payload_version_served(env):
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    recorded = forward_store.record(**result)
    assert recorded["payload_version"] == 4
    assert recorded["parameters"] == {
        "horizons_minutes": [["1m", 1], ["5m", 5], ["1h", 60], ["4h", 240]],
        "max_touches_per_row": 8,
        "baseline_seed": 1729,
        "touch_timeframes": ["1m", "5m"],
        "return_sign_convention": "side_relative",
        # The declared shape of every horizon leaf. It rides here, not merely in the version, so
        # that adding a measured field genuinely re-keys the record rather than leaving every
        # already-measured screen reusing a payload that predates the field.
        "horizon_measures": ["return_pct", "exit_price", "mdd_long_pct", "mdd_short_pct"],
    }
    assert recorded["register"] == FORWARD_REGISTER
    assert "horizons" not in recorded  # the v1 top-level key is gone


def test_legacy_row_shapes_degrade_or_measure_honestly(env):
    """A row missing the band range degrades with a reason; a row lacking reference_close (the v1
    anchor) measures NORMALLY -- reference_close is no longer consumed at all."""
    bar_store, screen_store, _ = env
    _plant(bar_store, "OK", "1m", [_in_band_bar("OK", 0)])
    screen = _record_screen(
        screen_store,
        [_screen_row("OK", "support"), _screen_row("NOBAND", "support", None, None)],
    )
    rows = {r["symbol"]: r for r in compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"]}
    assert rows["OK"]["touch_count"] == 1          # no reference_close on the fixture row at all
    assert rows["NOBAND"]["touch_count"] == 0
    assert "no band price range" in rows["NOBAND"]["reason"]


# --- signature, store, versioning ------------------------------------------------------------------


def test_signature_narrows_to_the_touch_timeframes_only(env):
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    first, reused = run_forward_and_record(screen_store, bar_store, CONFIG, forward_store, screen["id"])
    assert reused is False

    # Coarse series are structurally invisible: planting 1h AND 1d for the ranked symbol reuses.
    _plant(bar_store, "AAA", "1h", [_bar("AAA", "1h", _minute(0), 100.0, 101.0, 99.0, 100.5)])
    _plant(bar_store, "AAA", "1d", [_bar("AAA", "1d", _minute(0), 100.0, 101.0, 99.0, 100.5)])
    again, reused_again = run_forward_and_record(screen_store, bar_store, CONFIG, forward_store, screen["id"])
    assert reused_again is True and again["id"] == first["id"]

    # A fine series for a NON-ranked symbol is also invisible.
    _plant(bar_store, "ZZZ", "1m", [_in_band_bar("ZZZ", 0)])
    still, reused_still = run_forward_and_record(screen_store, bar_store, CONFIG, forward_store, screen["id"])
    assert reused_still is True and still["id"] == first["id"]

    # A NEW fine series for a ranked symbol re-keys -> a new version, the old kept.
    _plant(bar_store, "AAA", "5m", [_bar("AAA", "5m", E_OPEN, 100.6, 100.8, 99.5, 100.2)])
    third, reused_third = run_forward_and_record(screen_store, bar_store, CONFIG, forward_store, screen["id"])
    assert reused_third is False and third["id"] != first["id"]
    newest, versions = forward_store.newest_for_screen(screen["id"])
    assert versions == 2 and newest["id"] == third["id"]


# --- the side-relative sign convention ------------------------------------------------------------


def _falling_session(symbol: str) -> list[RawBar]:
    """Two bars that touch the default band [99, 100] from below and then fall. Shared by the
    sign tests so support and resistance are measured over BYTE-IDENTICAL price history and the
    only difference between the two answers is the row's own side."""
    return [
        _bar(symbol, "1m", _minute(0), 98.4, 99.3, 98.2, 98.9),   # overlaps the band
        _bar(symbol, "1m", _minute(1), 98.5, 98.6, 97.5, 98.01),  # price falls away
    ]


def test_returns_are_signed_to_the_rows_own_side(env):
    """The convention: a POSITIVE forward number always means the wall worked. Support keeps the
    raw price move (its thesis is long); resistance is negated (its thesis is short), so the same
    falling session reads negative for support and positive for resistance."""
    bar_store, screen_store, _ = env
    _plant(bar_store, "SUP", "1m", _falling_session("SUP"))
    _plant(bar_store, "RES", "1m", _falling_session("RES"))
    screen = _record_screen(
        screen_store, [_screen_row("SUP", "support"), _screen_row("RES", "resistance")]
    )
    rows = {r["symbol"]: r for r in compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"]}

    sup = rows["SUP"]["touches"][0]
    assert (sup["entry_price"], sup["entry_kind"]) == (98.4, "open")  # min(open, price_high)
    # raw (98.01 - 98.4) / 98.4 -> the long thesis lost; support serves it unchanged
    assert sup["horizons"]["1m"]["return_pct"] == pytest.approx(-0.39634146341)
    assert sup["to_close_pct"] == pytest.approx(-0.39634146341)

    res = rows["RES"]["touches"][0]
    assert (res["entry_price"], res["entry_kind"]) == (99.0, "edge")  # max(open, price_low)
    # raw (98.01 - 99.0) / 99.0 = -1.0 -> the short thesis WON; resistance serves +1.0
    assert res["horizons"]["1m"]["return_pct"] == pytest.approx(1.0)
    assert res["to_close_pct"] == pytest.approx(1.0)
    # ... and the averages/summary pool the signed values, never the raw ones
    assert rows["RES"]["averages"]["1m"]["mean_pct"] == pytest.approx(1.0)
    assert rows["RES"]["averages"]["to_close"]["mean_pct"] == pytest.approx(1.0)


def test_the_mdd_pair_stays_in_absolute_price_direction_on_both_sides(env):
    """The two drawdowns name their own direction, so they are NOT re-signed: `mdd_long` is always
    the worst move BELOW entry and `mdd_short` always the worst move ABOVE it, on either side.
    Both stay clamped <= 0 — signing them would destroy which way price actually went."""
    bar_store, screen_store, _ = env
    _plant(bar_store, "RES", "1m", _falling_session("RES"))
    screen = _record_screen(screen_store, [_screen_row("RES", "resistance")])
    touch = compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"][0]["touches"][0]
    # entry 99.0; session low 97.5, session high 99.3 — both measured from the touch bar onward
    assert touch["mdd_long_pct"] == pytest.approx((97.5 - 99.0) / 99.0 * 100.0)
    assert touch["mdd_short_pct"] == pytest.approx((99.0 - 99.3) / 99.0 * 100.0)
    assert touch["mdd_long_pct"] < 0 and touch["mdd_short_pct"] < 0


def test_baseline_anchors_carry_their_rows_sign_so_the_comparison_stays_like_for_like(env):
    """The null must live in the SAME signed space as the touches it is the null for — otherwise
    'did the wall beat a random minute?' compares a signed number against a raw one."""
    bar_store, screen_store, _ = env
    _plant(bar_store, "RES", "1m", _falling_session("RES"))
    _plant(bar_store, "SUP", "1m", _falling_session("SUP"))
    screen = _record_screen(
        screen_store, [_screen_row("RES", "resistance"), _screen_row("SUP", "support")]
    )
    rows = {r["symbol"]: r for r in compute_forward(screen, bar_store, CONFIG.config_fingerprint())["rows"]}
    # A monotonically falling session: every anchor's signed to-close is >= 0 on the short side
    # and <= 0 on the long side, whichever minutes the seeded stream drew.
    res_anchors = rows["RES"]["baseline_anchors"]
    sup_anchors = rows["SUP"]["baseline_anchors"]
    assert res_anchors and sup_anchors
    assert all(anchor["to_close_pct"] >= 0 for anchor in res_anchors)
    assert all(anchor["to_close_pct"] <= 0 for anchor in sup_anchors)
    assert rows["RES"]["baseline_anchors"][0]["entry_kind"] == "close"


def test_the_sign_convention_is_declared_in_the_parameters_and_re_keys_the_record(env, monkeypatch):
    """The convention rides in `parameters` — so it is BOTH visible in the payload and hashed into
    the input signature. That is what makes a stored raw-signed record re-key rather than be
    silently reused as if it were side-signed."""
    bar_store, screen_store, _ = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    fp = CONFIG.config_fingerprint()
    base = compute_forward(screen, bar_store, fp)
    assert base["parameters"]["return_sign_convention"] == "side_relative"
    monkeypatch.setattr(desk_forward_module, "DESK_FORWARD_RETURN_SIGN_CONVENTION", "raw")
    changed = compute_forward(screen, bar_store, fp)
    assert changed["parameters"]["return_sign_convention"] == "raw"
    assert changed["forward_input_signature"] != base["forward_input_signature"]


def test_parameters_liveness_moves_payload_and_signature(env, monkeypatch):
    bar_store, screen_store, _ = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    fp = CONFIG.config_fingerprint()
    base = compute_forward(screen, bar_store, fp)
    monkeypatch.setattr(desk_forward_module, "DESK_FORWARD_MAX_TOUCHES_PER_ROW", 2)
    changed = compute_forward(screen, bar_store, fp)
    assert changed["parameters"]["max_touches_per_row"] == 2
    assert changed["forward_input_signature"] != base["forward_input_signature"]


def test_store_discipline_tamper_duplicate_and_damaged_file(env):
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    recorded = forward_store.record(**result)

    with pytest.raises(ForwardAlreadyRecorded) as excinfo:
        forward_store.record(**result)
    assert excinfo.value.existing_id == recorded["id"]

    path = forward_store.root / f"{recorded['id']}.json"
    payload = json.loads(path.read_text())
    payload["record"]["meta"]["screen_date"] = "1999-01-01"
    path.write_text(json.dumps(payload))
    records, errors = forward_store.list()
    assert records == []
    assert len(errors) == 1 and "integrity check" in errors[0]["error"]

    with pytest.raises(ForwardIntegrityError):
        forward_store.record(**result)


def test_unknown_screen_id_raises_forward_screen_not_found(env):
    bar_store, screen_store, forward_store = env
    with pytest.raises(ForwardScreenNotFound):
        run_forward_and_record(screen_store, bar_store, CONFIG, forward_store, "screen-nope")


def test_recorded_file_round_trips_byte_identical(env):
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0), _above_band_bar("AAA", 1)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    forward_store.record(**result)
    records, errors = forward_store.list()
    assert errors == []
    assert _canonical(records[0]["rows"]) == _canonical(result["rows"])
    assert _canonical(records[0]["summary"]) == _canonical(result["summary"])


# --- the targeted reads: only the files a screen's own date prefix names --------------------------
# `newest_for_screen`/`find_by_key` opened and verified EVERY recorded record to hand back one of
# them -- the read behind a `/desk` history click. They now open only the candidate files a screen's
# own date prefix names; these pin the equivalence with the full scan they replaced.


def test_newest_for_screen_and_find_by_key_match_the_full_scan_expressions(env):
    """Both answers -- including the ``versions`` count -- are computed BOTH ways here: the
    ``list()``-then-filter expression these two replaced, and the targeted read itself."""
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0), _above_band_bar("AAA", 1)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    versions = [
        forward_store.record(**{**result, "forward_input_signature": signature})
        for signature in ("sig-1", "sig-2", "sig-3")
    ]
    # A SECOND screen carrying its own record under a signature one of the above also uses: "this
    # screen's versions" must be a real narrowing, and the 2-pin key a real pair.
    other_screen = screen_store.record(
        screen_date=SCREEN_DATE, as_of=AS_OF, universe_snapshot_id="universe-test",
        config_fingerprint=CONFIG.config_fingerprint(), bar_store_signature="sig-b",
        rows=[_screen_row("AAA", "support")], skipped=[],
    )
    other = forward_store.record(
        **{**result, "screen_id": other_screen["id"], "forward_input_signature": "sig-1"}
    )

    records, errors = forward_store.list()
    assert errors == [] and len(records) == 4
    matching = [record for record in records if record["screen_id"] == screen["id"]]

    newest, count = forward_store.newest_for_screen(screen["id"])
    assert _canonical(newest) == _canonical(matching[-1])
    assert count == len(matching) == 3
    assert newest["id"] == max(versions, key=lambda r: (r["created_utc"], r["id"]))["id"]

    for record in versions + [other]:
        key = (record["screen_id"], record["forward_input_signature"])
        by_scan = next(
            (r for r in records if (r["screen_id"], r["forward_input_signature"]) == key), None
        )
        assert _canonical(forward_store.find_by_key(*key)) == _canonical(by_scan)
    assert forward_store.find_by_key(screen["id"], "sig-never-recorded") is None


def test_a_malformed_or_unknown_screen_id_is_an_honest_absence(env):
    """A screen id is an ADDRESS -- a version's filename inherits the date inside it -- so an id
    carrying no parseable date can name no recordable screen at all. Both reads say so plainly,
    ``(None, 0)`` / ``None``, rather than raising or walking the store to find out."""
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    forward_store.record(**compute_forward(screen, bar_store, CONFIG.config_fingerprint()))

    assert forward_store.newest_for_screen("screen-nope") == (None, 0)
    assert forward_store.newest_for_screen("screen-2026-13-99-000000000000") == (None, 0)
    assert forward_store.newest_for_screen("screen-2026-06-23-000000000000") == (None, 0)
    assert forward_store.find_by_key("screen-nope", "sig-a") is None
    assert forward_store.find_by_key(screen["id"], "never-recorded") is None


def test_record_refuses_a_screen_date_that_disagrees_with_its_screen_id(env):
    """A version is ADDRESSED by the date its screen id carries -- that is what lets a screen's
    versions be found without opening the whole store -- so a pair that does NOT agree would record
    a file its own dedup lookup could never find again. Refused loudly, and nothing is written."""
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())

    with pytest.raises(ValueError) as excinfo:
        forward_store.record(**{**result, "screen_date": "2026-06-23"})
    assert screen["id"] in str(excinfo.value)
    assert list(forward_store.root.glob("*.json")) == []

    with pytest.raises(ValueError):
        forward_store.record(**{**result, "screen_id": "screen-nope"})
    assert list(forward_store.root.glob("*.json")) == []

    forward_store.record(**result)  # the agreeing pair still records normally
    assert len(list(forward_store.root.glob("*.json"))) == 1


def test_prune_for_screen_refuses_to_remove_a_corrupt_file_and_is_empty_for_an_unknown_screen(env):
    """``prune_for_screen`` removes only REGISTERED records, and a file that failed its integrity
    check is not one (``_records_for_screen`` withholds it exactly as ``list`` does). A damaged file
    therefore keeps being surfaced honestly instead of being quietly swept away by a supersede; an
    unknown screen id -- parseable or not -- is a plain empty list, never an error."""
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0), _above_band_bar("AAA", 1)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    healthy = forward_store.record(**{**result, "forward_input_signature": "sig-1"})
    damaged = forward_store.record(**{**result, "forward_input_signature": "sig-2"})

    path = forward_store.root / f"{damaged['id']}.json"
    payload = json.loads(path.read_text())
    payload["record"]["meta"]["screen_date"] = "1999-01-01"  # tamper -- the checksum now disagrees
    path.write_text(json.dumps(payload))
    damaged_bytes = path.read_bytes()

    assert forward_store.prune_for_screen("screen-2026-06-22-notrecorded") == []
    assert forward_store.prune_for_screen("screen-nope") == []

    assert forward_store.prune_for_screen(screen["id"]) == [healthy["id"]]
    assert not (forward_store.root / f"{healthy['id']}.json").exists()
    assert path.read_bytes() == damaged_bytes, "the damaged file must be left exactly as found"
    records, errors = forward_store.list()
    assert records == []
    assert [e["file"] for e in errors] == [path.name]


# --- the durable run ledger (forward-test era) -------------------------------------------------------
# The store's own discipline lives in test_desk_forward_log.py; these prove the SHARED WRITER
# contract -- that `record_forward_run` is reached from inside `run_forward_and_record`, the ONE
# entry point both the manager's worker and the CLI call, at every terminal outcome and only there.


def test_a_run_with_no_ledger_store_writes_no_run_record(env, tmp_path):
    """The default. Every pre-existing caller passes no store and must keep behaving identically --
    the compute path is unchanged, and nothing is written anywhere new."""
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])

    record, reused = run_forward_and_record(screen_store, bar_store, CONFIG, forward_store, screen["id"])

    assert record is not None and reused is False
    assert not (tmp_path / "forward_runs").exists()


def test_a_completed_run_records_one_ledger_row_naming_what_it_measured(env, tmp_path):
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0), _above_band_bar("AAA", 1)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    run_store = ForwardRunStore(tmp_path / "forward_runs")

    record, _reused = run_forward_and_record(
        screen_store, bar_store, CONFIG, forward_store, screen["id"], forward_run_store=run_store,
    )

    rows, errors = run_store.list()
    assert errors == []
    assert len(rows) == 1
    assert rows[0]["state"] == "done"
    assert rows[0]["reused"] is False
    assert rows[0]["screen_id"] == screen["id"]
    assert rows[0]["screen_date"] == SCREEN_DATE
    assert rows[0]["forward_id"] == record["id"]
    assert rows[0]["forward_input_signature"] == record["forward_input_signature"]
    assert rows[0]["rows_total"] == 1
    assert rows[0]["rows_measured"] == 1
    assert rows[0]["rows_absent_no_fine_bars"] == 0
    assert rows[0]["total_touches"] == record["total_touches"]
    assert rows[0]["error"] is None


def test_a_run_over_a_date_with_no_fine_bars_records_that_it_ran_and_found_nothing(env, tmp_path):
    """The whole point of this ledger. A screen whose session holds no 1m/5m bars still produces a
    real forward record -- of pure absence -- and the ledger says so, which is what distinguishes it
    from a measurement that never ran at all (that leaves no row)."""
    bar_store, screen_store, forward_store = env
    # 1d bars only: the touch ladder is 1m/5m, so every row is an honest absence.
    _plant(bar_store, "AAA", "1d", [_bar("AAA", "1d", _minute(0), 100.0, 101.0, 99.0, 100.5)])
    screen = _record_screen(
        screen_store, [_screen_row("AAA", "support"), _screen_row("BBB", "resistance")]
    )
    run_store = ForwardRunStore(tmp_path / "forward_runs")

    record, _reused = run_forward_and_record(
        screen_store, bar_store, CONFIG, forward_store, screen["id"], forward_run_store=run_store,
    )

    assert all(row["reason"] is not None for row in record["rows"])
    row = run_store.list_for_screen(screen["id"])[0]
    assert row["state"] == "done"
    assert (row["rows_total"], row["rows_measured"], row["rows_absent_no_fine_bars"]) == (2, 0, 2)
    assert row["total_touches"] == 0


def test_a_reused_run_records_a_second_row_carrying_the_existing_records_counts(env, tmp_path):
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0), _above_band_bar("AAA", 1)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    run_store = ForwardRunStore(tmp_path / "forward_runs")
    first, _ = run_forward_and_record(
        screen_store, bar_store, CONFIG, forward_store, screen["id"], forward_run_store=run_store,
    )

    second, reused = run_forward_and_record(
        screen_store, bar_store, CONFIG, forward_store, screen["id"], forward_run_store=run_store,
    )

    assert reused is True and second["id"] == first["id"]
    rows = run_store.list_for_screen(screen["id"])
    assert len(rows) == 2  # a reuse is its own real attempt, never folded into the first
    assert rows[1]["reused"] is True
    assert rows[1]["forward_id"] == first["id"]
    # ...and it reports what that record HOLDS, never a misleading row of zeroes.
    assert rows[1]["rows_measured"] == rows[0]["rows_measured"] == 1
    assert rows[1]["total_touches"] == rows[0]["total_touches"]


def test_a_cancelled_walk_records_a_cancelled_row_and_names_no_forward_record(env, tmp_path):
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    run_store = ForwardRunStore(tmp_path / "forward_runs")

    record, _reused = run_forward_and_record(
        screen_store, bar_store, CONFIG, forward_store, screen["id"],
        should_abort=lambda: True, forward_run_store=run_store,
    )

    assert record is None
    assert forward_store.list() == ([], [])  # a partial walk is never recorded
    row = run_store.list_for_screen(screen["id"])[0]
    assert row["state"] == "cancelled"
    assert row["forward_id"] is None
    assert row["rows_total"] == 1  # the run's SCOPE, not how far the partial walk got


def test_a_failing_walk_records_a_failed_row_carrying_the_error_and_re_raises(env, tmp_path, monkeypatch):
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    run_store = ForwardRunStore(tmp_path / "forward_runs")

    def _boom(*_args, **_kwargs):
        raise RuntimeError("the bar store went away mid-walk")

    monkeypatch.setattr(desk_forward_compute, "compute_forward", _boom)

    with pytest.raises(RuntimeError, match="went away mid-walk"):
        run_forward_and_record(
            screen_store, bar_store, CONFIG, forward_store, screen["id"],
            forward_run_store=run_store,
        )

    row = run_store.list_for_screen(screen["id"])[0]
    assert row["state"] == "failed"
    assert row["error"] == "the bar store went away mid-walk"
    assert row["forward_id"] is None


def test_an_unknown_screen_id_records_a_failed_row_with_an_honest_null_date(env, tmp_path):
    bar_store, screen_store, forward_store = env
    run_store = ForwardRunStore(tmp_path / "forward_runs")

    with pytest.raises(ForwardScreenNotFound):
        run_forward_and_record(
            screen_store, bar_store, CONFIG, forward_store, "screen-nope",
            forward_run_store=run_store,
        )

    rows, _errors = run_store.list()
    assert len(rows) == 1
    assert rows[0]["state"] == "failed"
    assert rows[0]["screen_date"] is None  # never fabricated from the id string
    assert "screen-nope" in rows[0]["error"]


def test_a_ledger_write_that_itself_raises_leaves_no_row_and_never_double_logs(env, tmp_path, monkeypatch):
    """The B1 latch. A terminal ledger write that fails (a full disk, a read-only log dir) must not
    be caught by the outer handler and re-entered as a SECOND "failed" row -- that would fabricate a
    measurement failure out of the LEDGER's own I/O error, for a record that really was persisted."""
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    run_store = ForwardRunStore(tmp_path / "forward_runs")
    calls = []

    def _failing_record(*_args, **kwargs):
        calls.append(kwargs["state"])
        raise OSError("no space left on device")

    monkeypatch.setattr(run_store, "record", _failing_record)

    with pytest.raises(OSError, match="no space left on device"):
        run_forward_and_record(
            screen_store, bar_store, CONFIG, forward_store, screen["id"],
            forward_run_store=run_store,
        )

    assert calls == ["done"]  # exactly one attempt -- never re-entered as a "failed" second row
    assert len(forward_store.list()[0]) == 1  # ...and the forward record itself really is on disk


def test_the_manager_threads_the_ledger_store_through_to_the_walk(env, tmp_path):
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    run_store = ForwardRunStore(tmp_path / "forward_runs")

    manager = DeskForwardComputeManager()
    manager.trigger(screen["id"], screen_store, bar_store, CONFIG, forward_store, run_store)
    snap = _wait_for_terminal(manager)

    assert snap["state"] == "done"
    row = run_store.list_for_screen(screen["id"])[0]
    assert row["forward_id"] == snap["forward_id"]
    manager.join_all(timeout=5)


def test_the_no_fine_bars_reason_is_built_and_classified_by_one_owner(env):
    """`forward_row_counts` classifies the sentence `compute_forward` writes. If the two ever drift,
    every ledger row's absent count silently becomes zero while the records still say otherwise."""
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1d", [_bar("AAA", "1d", _minute(0), 100.0, 101.0, 99.0, 100.5)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])

    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())

    assert result["rows"][0]["reason"] == no_fine_bars_reason(SCREEN_DATE)
    assert forward_row_counts(result["rows"])["rows_absent_no_fine_bars"] == 1


def test_the_other_absence_reason_is_not_counted_as_a_missing_fine_bar(env):
    """A screen row carrying no band price range is a DIFFERENT absence -- one no top-up can fix --
    so folding it into the fine-bar count would overstate what fetching bars would recover."""
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(
        screen_store, [_screen_row("AAA", "support", price_low=None, price_high=None)]
    )

    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    counts = forward_row_counts(result["rows"])

    assert result["rows"][0]["reason"] is not None
    assert counts == {"rows_total": 1, "rows_measured": 0, "rows_absent_no_fine_bars": 0}


# --- the manager -----------------------------------------------------------------------------------


def _wait_for_terminal(manager: DeskForwardComputeManager, timeout: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        snap = manager.snapshot()
        if snap is not None and snap["state"] != "running":
            return snap
        time.sleep(0.01)
    raise AssertionError("forward compute never reached a terminal state")


def test_manager_single_flight_second_trigger_returns_the_same_job(env, monkeypatch):
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])

    started = threading.Event()
    release = threading.Event()

    def _blocking_compute(screen_arg, bar_store_arg, fp, *, progress=None, should_abort=None):
        started.set()
        release.wait(timeout=5)
        return compute_forward(screen_arg, bar_store_arg, fp)

    monkeypatch.setattr(desk_forward_compute, "compute_forward", _blocking_compute)
    manager = DeskForwardComputeManager()
    first = manager.trigger(screen["id"], screen_store, bar_store, CONFIG, forward_store)
    assert first["started"] is True
    assert started.wait(timeout=5)
    second = manager.trigger(screen["id"], screen_store, bar_store, CONFIG, forward_store)
    assert second["started"] is False
    assert second["compute"]["id"] == first["compute"]["id"]
    release.set()
    snap = _wait_for_terminal(manager)
    assert snap["state"] == "done"
    assert snap["progress"]["rows_total"] == 1
    manager.join_all(timeout=5)


def test_manager_cancel_mid_walk_records_nothing(env, monkeypatch):
    bar_store, screen_store, forward_store = env
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])

    entered = threading.Event()
    release = threading.Event()
    real_compute = desk_forward_compute.compute_forward

    def _pausing_compute(screen_arg, bar_store_arg, fp, *, progress=None, should_abort=None):
        entered.set()
        release.wait(timeout=5)
        return real_compute(
            screen_arg, bar_store_arg, fp, progress=progress, should_abort=should_abort
        )

    monkeypatch.setattr(desk_forward_compute, "compute_forward", _pausing_compute)
    manager = DeskForwardComputeManager()
    manager.trigger(screen["id"], screen_store, bar_store, CONFIG, forward_store)
    assert entered.wait(timeout=5)
    manager.cancel()
    release.set()
    snap = _wait_for_terminal(manager)
    assert snap["state"] == "cancelled"
    assert snap["forward_id"] is None
    records, _errors = forward_store.list()
    assert records == []
    manager.join_all(timeout=5)


# --- the coverage preflight (forward-test era) -------------------------------------------------------
# What a measurement could POSSIBLY reach, disclosed before anything is clicked. Index-only: these
# assert against `BarIndex` rows, never `BarStore` content, which is the whole point (the exact
# answer costs the same as the walk).


def _pins_env(tmp_path):
    bar_store = BarStore(tmp_path / "bars")
    screen_store = ScreenStore(tmp_path / "screen")
    forward_store = ForwardStore(tmp_path / "forward")
    bar_index = BarIndex(str(tmp_path / "bar_index.db"))
    return bar_store, screen_store, forward_store, bar_index


def test_forward_pins_counts_the_members_whose_fine_window_covers_the_screen_date(tmp_path):
    bar_store, screen_store, forward_store, bar_index = _pins_env(tmp_path)
    # AAA's 1m window covers the screen date; BBB's 1m window stops a month before it (the 2025
    # shape: a screen whose map is real while its session's fine bars were never fetchable).
    bar_index.insert(_plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)]))
    bar_index.insert(
        bar_store.record(
            symbol="BBB", timeframe="1m", window_start_utc="2026-05-01T00:00:00Z",
            window_end_utc="2026-05-30T00:00:00Z", feed="test", bars=[_in_band_bar("BBB", 0)],
        )
    )
    screen = _record_screen(
        screen_store, [_screen_row("AAA", "support"), _screen_row("BBB", "support")]
    )

    pins = resolve_desk_forward_pins(screen["id"], screen_store, bar_index, forward_store)

    assert pins["screen_id"] == screen["id"]
    assert pins["screen_date"] == SCREEN_DATE
    assert pins["as_of"] == AS_OF
    assert pins["touch_timeframes"] == ["1m", "5m"]
    assert pins["members_total"] == 2
    assert pins["members_with_fine_series"] == 1
    assert pins["versions"] == 0
    assert pins["recorded"] is None


def test_forward_pins_counts_a_member_once_whichever_ladder_rung_covers_the_date(tmp_path):
    """The walk takes the FINEST rung holding bars, so a 5m-only member is as reachable as a 1m
    one — and a member with both must not be counted twice."""
    bar_store, screen_store, forward_store, bar_index = _pins_env(tmp_path)
    bar_index.insert(_plant(bar_store, "BOTH", "1m", [_in_band_bar("BOTH", 0)]))
    bar_index.insert(_plant(bar_store, "BOTH", "5m", [_in_band_bar("BOTH", 0, tf="5m")]))
    bar_index.insert(_plant(bar_store, "FIVEONLY", "5m", [_in_band_bar("FIVEONLY", 0, tf="5m")]))
    screen = _record_screen(
        screen_store, [_screen_row("BOTH", "support"), _screen_row("FIVEONLY", "support")]
    )

    pins = resolve_desk_forward_pins(screen["id"], screen_store, bar_index, forward_store)

    assert pins["members_total"] == 2
    assert pins["members_with_fine_series"] == 2


def test_forward_pins_ignores_the_coarse_timeframes_entirely(tmp_path):
    """A member with years of 1d/1h bars covering the date is still unreachable: the touch ladder
    is 1m/5m only, and counting coarse coverage here would promise measurements that cannot
    happen."""
    bar_store, screen_store, forward_store, bar_index = _pins_env(tmp_path)
    bar_index.insert(_plant(bar_store, "COARSE", "1d", [_in_band_bar("COARSE", 0, tf="1d")]))
    bar_index.insert(_plant(bar_store, "COARSE", "1h", [_in_band_bar("COARSE", 0, tf="1h")]))
    screen = _record_screen(screen_store, [_screen_row("COARSE", "support")])

    pins = resolve_desk_forward_pins(screen["id"], screen_store, bar_index, forward_store)

    assert pins["members_total"] == 1
    assert pins["members_with_fine_series"] == 0


def test_forward_pins_is_an_upper_bound_not_a_promise(tmp_path):
    """The honesty this whole disclosure rests on. A covering WINDOW is not bars in that SESSION: a
    series recorded over the month with nothing on the screen date itself still counts here, and
    the run then measures nothing. The count may only ever be read as "at most"."""
    bar_store, screen_store, forward_store, bar_index = _pins_env(tmp_path)
    # A window spanning June, holding a single bar from a DIFFERENT day than the screen date.
    other_day = _bar("EMPTY", "1m", E_OPEN - 5 * 86400.0, 100.0, 100.5, 99.5, 100.2)
    bar_index.insert(_plant(bar_store, "EMPTY", "1m", [other_day]))
    screen = _record_screen(screen_store, [_screen_row("EMPTY", "support")])

    pins = resolve_desk_forward_pins(screen["id"], screen_store, bar_index, forward_store)
    assert pins["members_with_fine_series"] == 1  # the window covers the date...

    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    assert result["rows"][0]["reason"] == no_fine_bars_reason(SCREEN_DATE)  # ...the session is empty


def test_forward_pins_names_the_recorded_measurement_once_one_exists(tmp_path):
    bar_store, screen_store, forward_store, bar_index = _pins_env(tmp_path)
    bar_index.insert(_plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0), _above_band_bar("AAA", 1)]))
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])
    record, _reused = run_forward_and_record(screen_store, bar_store, CONFIG, forward_store, screen["id"])

    pins = resolve_desk_forward_pins(screen["id"], screen_store, bar_index, forward_store)

    assert pins["versions"] == 1
    assert pins["recorded"] == {
        "id": record["id"],
        "created_utc": record["created_utc"],
        "rows_with_touches": record["rows_with_touches"],
        "total_touches": record["total_touches"],
    }


def test_forward_pins_on_an_unknown_screen_id_is_honestly_empty(tmp_path):
    _bar_store, screen_store, forward_store, bar_index = _pins_env(tmp_path)

    pins = resolve_desk_forward_pins("screen-nope", screen_store, bar_index, forward_store)

    assert pins == {
        "screen_id": "screen-nope",
        "screen_date": None,
        "as_of": None,
        "touch_timeframes": ["1m", "5m"],
        "members_total": 0,
        "members_with_fine_series": 0,
        "versions": 0,
        "recorded": None,
        # An id that resolves to no screen resolves to no date either, so there is nothing to
        # place against the daily bars -- unknown, whether or not a store was supplied.
        "session": {"state": "unknown", "evidence": None},
    }


def test_forward_pins_takes_a_bar_store_only_for_the_session_state(tmp_path):
    """The fine-coverage count still resolves through ``BarIndex`` alone -- the reason this guard
    existed, and the reason a page-load GET can afford it. The ``bar_store`` parameter was added
    for exactly one thing (``session.state``: whether the screen date has a recorded daily bar),
    reaches one accessor over a bounded handful of anchors, and DEFAULTS TO NONE so the honest
    non-answer survives a caller that has none. Asserted on the signature so a future parameter
    still has to come here and say why."""
    import inspect

    signature = inspect.signature(resolve_desk_forward_pins)
    assert list(signature.parameters) == [
        "screen_id", "screen_store", "bar_index", "forward_store", "bar_store",
    ]
    assert signature.parameters["bar_store"].default is None


def test_forward_pins_without_a_bar_store_says_unknown_rather_than_guessing(tmp_path):
    _bar_store, screen_store, forward_store, bar_index = _pins_env(tmp_path)
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])

    pins = resolve_desk_forward_pins(screen["id"], screen_store, bar_index, forward_store)

    assert pins["session"] == {"state": "unknown", "evidence": None}


def test_forward_pins_names_a_screen_date_with_a_recorded_daily_bar_a_session(tmp_path):
    bar_store, screen_store, forward_store, bar_index = _pins_env(tmp_path)
    _plant(bar_store, "AAA", "1d", [_bar("AAA", "1d", E_OPEN, 100.0, 101.0, 99.0, 100.5)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])

    pins = resolve_desk_forward_pins(
        screen["id"], screen_store, bar_index, forward_store, bar_store=bar_store
    )

    assert pins["session"]["state"] == "recorded_session"
    assert pins["session"]["evidence"]["anchor_symbols"] == ["AAA"]


def test_forward_pins_names_a_screen_date_the_daily_bars_bracket_but_skip(tmp_path):
    """The weekend/holiday case, and the whole reason a table of em-dashes was unreadable: daily
    bars exist on both sides of the screen date and none on it."""
    bar_store, screen_store, forward_store, bar_index = _pins_env(tmp_path)
    _plant(
        bar_store, "AAA", "1d",
        [
            _bar("AAA", "1d", E_OPEN - 86400.0, 100.0, 101.0, 99.0, 100.5),
            _bar("AAA", "1d", E_OPEN + 86400.0, 100.0, 101.0, 99.0, 100.5),
        ],
    )
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])

    pins = resolve_desk_forward_pins(
        screen["id"], screen_store, bar_index, forward_store, bar_store=bar_store
    )

    assert pins["session"]["state"] == "not_a_recorded_session"


def test_forward_pins_names_a_screen_date_past_the_last_recorded_daily_bar(tmp_path):
    """The ``/desk`` default view on 2026-08-08: the newest recorded screen was the coming Monday,
    for which no daily bar exists yet. Distinct from a proven non-session -- nothing is claimed
    about whether that Monday will trade."""
    bar_store, screen_store, forward_store, bar_index = _pins_env(tmp_path)
    _plant(
        bar_store, "AAA", "1d",
        [_bar("AAA", "1d", E_OPEN - 5 * 86400.0, 100.0, 101.0, 99.0, 100.5)],
    )
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])

    pins = resolve_desk_forward_pins(
        screen["id"], screen_store, bar_index, forward_store, bar_store=bar_store
    )

    assert pins["session"]["state"] == "after_recorded_evidence"


def test_forward_pins_reads_one_snapshot_and_never_walks_the_screen_store(tmp_path, monkeypatch):
    """The preflight resolves ONE named snapshot, so it opens that snapshot's own file -- never a
    ``ScreenStore.list`` that verifies every recorded screen to hand back one of them (a read this
    route paid for on every ``/desk`` page load). ``list`` is poisoned to prove that structurally,
    and the served body is compared against the ``list()``-then-``next()`` expression it replaced."""
    bar_store, screen_store, forward_store, bar_index = _pins_env(tmp_path)
    bar_index.insert(_plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)]))
    screen = _record_screen(
        screen_store, [_screen_row("AAA", "support"), _screen_row("NOFINE", "support")]
    )

    records, _errors = screen_store.list()
    by_scan = next((record for record in records if record["id"] == screen["id"]), None)
    assert by_scan is not None

    def _boom(*_args, **_kwargs):
        raise AssertionError("resolve_desk_forward_pins must never walk the screen store")

    monkeypatch.setattr(ScreenStore, "list", _boom)

    pins = resolve_desk_forward_pins(screen["id"], screen_store, bar_index, forward_store)

    assert pins == {
        "screen_id": screen["id"],
        "screen_date": by_scan["screen_date"],
        "as_of": by_scan["as_of"],
        "touch_timeframes": ["1m", "5m"],
        "members_total": len(by_scan["rows"]),
        "members_with_fine_series": 1,
        "versions": 0,
        "recorded": None,
        "session": {"state": "unknown", "evidence": None},
    }


# --- the routes ------------------------------------------------------------------------------------


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
    monkeypatch.setenv("TAPEOLOGY_DESK_FORWARD_DIR", str(tmp_path / "forward"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    fresh_manager = DeskForwardComputeManager()
    app.dependency_overrides[get_desk_forward_compute_manager] = lambda: fresh_manager
    with TestClient(app) as client:
        yield client, fresh_manager, tmp_path
    fresh_manager.join_all(timeout=5.0)
    set_registry(None)
    app.dependency_overrides.pop(get_desk_forward_compute_manager, None)
    store.close()


def test_routes_honest_empty_and_unknown_screen_id(route_ctx):
    client, _manager, _tmp = route_ctx
    empty = client.get("/research/desk/forward")
    assert empty.status_code == 200
    assert empty.json() == {"forwards": [], "latest": None, "integrity_errors": []}

    by_screen = client.get("/research/desk/forward", params={"screen_id": "screen-nope"})
    assert by_screen.status_code == 200
    assert by_screen.json() == {"forward": None, "versions": 0}

    assert client.get("/research/desk/forward/compute").json() is None  # GET-never-computes

    refused = client.post("/research/desk/forward/compute", json={"screen_id": "screen-nope"})
    assert refused.status_code == 422
    assert "screen-nope" in refused.json()["detail"]

    idle_cancel = client.post("/research/desk/forward/compute/cancel")
    assert idle_cancel.status_code == 409


def test_route_compute_runs_to_done_and_the_bulk_list_serves_v2_meta(route_ctx):
    client, manager, tmp = route_ctx
    bar_store = BarStore(tmp / "bars")
    screen_store = ScreenStore(tmp / "screen")
    _plant(bar_store, "AAA", "1m", [
        _in_band_bar("AAA", 0, close=100.2),
        _bar("AAA", "1m", _minute(1), 100.3, 100.6, 100.1, 100.5),
    ])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])

    trigger = client.post("/research/desk/forward/compute", json={"screen_id": screen["id"]})
    assert trigger.status_code == 200
    body = trigger.json()
    assert body["started"] is True
    assert body["compute"]["progress"]["rows_total"] == 1

    snap = _wait_for_terminal(manager)
    assert snap["state"] == "done" and snap["reused"] is False

    served = client.get("/research/desk/forward", params={"screen_id": screen["id"]})
    payload = served.json()
    assert payload["versions"] == 1
    record = payload["forward"]
    assert record["payload_version"] == 4
    assert record["rows"][0]["touches"][0]["horizons"]["1m"]["return_pct"] == pytest.approx(0.5)
    baseline_cell = record["summary"]["support"]["to_close"]["baseline"]
    assert baseline_cell["n"] == 1  # the matched anchor, in the never-truncated measure

    listing = client.get("/research/desk/forward").json()  # the _forward_meta_only projection
    assert len(listing["forwards"]) == 1
    meta = listing["forwards"][0]
    assert meta["counts"] == {"rows": 1, "rows_with_touches": 1, "total_touches": 1}
    assert meta["parameters"]["max_touches_per_row"] == 8
    assert "rows" not in meta
    assert listing["latest"]["id"] == record["id"]


def test_the_runs_and_pins_routes_are_honestly_empty_before_anything_is_computed(route_ctx):
    client, _manager, _tmp = route_ctx
    runs = client.get("/research/desk/forward/runs")
    assert runs.status_code == 200
    assert runs.json() == {"runs": [], "latest": None, "integrity_errors": []}

    pins = client.get("/research/desk/forward/pins", params={"screen_id": "screen-nope"})
    assert pins.status_code == 200
    assert pins.json()["members_total"] == 0
    assert pins.json()["members_with_fine_series"] == 0
    assert pins.json()["recorded"] is None

    assert client.get("/research/desk/forward/pins").status_code == 422  # screen_id is REQUIRED


def test_the_runs_route_records_a_row_the_compute_snapshot_would_have_lost(route_ctx):
    """The whole point, end to end: the manager's own snapshot is process-scoped, so after a
    restart it says nothing about what ran. The ledger row survives it, and says both that the
    measurement happened and what it found."""
    client, manager, tmp = route_ctx
    bar_store = BarStore(tmp / "bars")
    screen_store = ScreenStore(tmp / "screen")
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0), _above_band_bar("AAA", 1)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])

    client.post("/research/desk/forward/compute", json={"screen_id": screen["id"]})
    snap = _wait_for_terminal(manager)

    runs = client.get("/research/desk/forward/runs").json()
    assert len(runs["runs"]) == 1
    row = runs["runs"][0]
    assert row["state"] == "done"
    assert row["screen_id"] == screen["id"]
    assert row["forward_id"] == snap["forward_id"]
    assert row["rows_total"] == 1
    assert row["rows_absent_no_fine_bars"] == 0
    assert runs["latest"]["id"] == row["id"]

    narrowed = client.get("/research/desk/forward/runs", params={"screen_id": screen["id"]}).json()
    assert [r["id"] for r in narrowed["runs"]] == [row["id"]]
    other = client.get("/research/desk/forward/runs", params={"screen_id": "screen-other"}).json()
    assert other == {"runs": [], "latest": None, "integrity_errors": []}


def test_the_pins_route_discloses_the_reachable_upper_bound_for_a_recorded_snapshot(route_ctx):
    client, _manager, tmp = route_ctx
    bar_store = BarStore(tmp / "bars")
    screen_store = ScreenStore(tmp / "screen")
    bar_index = BarIndex(str(tmp / "bar_index.db"))  # where get_bar_index resolves for this env
    bar_index.insert(_plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)]))
    screen = _record_screen(
        screen_store, [_screen_row("AAA", "support"), _screen_row("NOFINE", "support")]
    )

    pins = client.get("/research/desk/forward/pins", params={"screen_id": screen["id"]}).json()

    assert pins["screen_date"] == SCREEN_DATE
    assert pins["members_total"] == 2
    assert pins["members_with_fine_series"] == 1
    assert pins["touch_timeframes"] == ["1m", "5m"]
    assert pins["versions"] == 0 and pins["recorded"] is None


# --- register, fingerprint, CLI --------------------------------------------------------------------


def test_the_register_and_served_reasons_clear_the_copy_lexicon(env):
    assert find_violations(FORWARD_REGISTER) == []
    bar_store, screen_store, _ = env
    _plant(bar_store, "COARSE", "1h", [_bar("COARSE", "1h", _minute(0), 99.5, 100.5, 99.0, 100.0)])
    _plant(bar_store, "FIVE", "5m", [_bar("FIVE", "5m", E_OPEN, 100.6, 100.8, 99.5, 100.2)])
    screen = _record_screen(
        screen_store,
        [_screen_row("COARSE", "support"), _screen_row("FIVE", "support"),
         _screen_row("NOBAND", "support", None, None)],
    )
    result = compute_forward(screen, bar_store, CONFIG.config_fingerprint())
    for row in result["rows"]:
        if row["reason"] is not None:
            assert find_violations(row["reason"]) == []
        for touch in row["touches"]:
            for measure in touch["horizons"].values():
                if measure["reason"] is not None:
                    assert find_violations(measure["reason"]) == []


def test_fingerprint_stability_zero_new_config_fields():
    assert CONFIG.config_fingerprint() == "08e471b10130e1e2"
    assert Config().config_fingerprint() == "08e471b10130e1e2"


def test_cli_records_into_the_env_scoped_store_and_unknown_id_exits_1(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_UNIVERSE_DIR", str(tmp_path / "universe"))
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_DIR", str(tmp_path / "screen"))
    monkeypatch.setenv("TAPEOLOGY_DESK_FORWARD_DIR", str(tmp_path / "forward"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_JOURNAL_DB", str(tmp_path / "journal.db"))

    bar_store = BarStore(tmp_path / "bars")
    screen_store = ScreenStore(tmp_path / "screen")
    _plant(bar_store, "AAA", "1m", [_in_band_bar("AAA", 0)])
    screen = _record_screen(screen_store, [_screen_row("AAA", "support")])

    monkeypatch.setattr(sys, "argv", ["desk_forward_compute", "--screen-id", screen["id"]])
    assert desk_forward_compute.main() == 0
    forward_store = ForwardStore(resolve_desk_forward_dir(str(tmp_path / "universe")))
    records, errors = forward_store.list()
    assert errors == [] and len(records) == 1
    assert records[0]["payload_version"] == 4

    monkeypatch.setattr(sys, "argv", ["desk_forward_compute", "--screen-id", "screen-nope"])
    assert desk_forward_compute.main() == 1
    records_after, _errors = forward_store.list()
    assert len(records_after) == 1
