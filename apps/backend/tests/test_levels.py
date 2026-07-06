"""Deterministic, lookahead-free support/resistance levels (era-4 capability 2, J-02) --
``research/levels.py`` unit + fixture coverage.

Two synthetic fixtures give full control over exact expected numbers (the ``test_bars.py``
``_small_daily_series`` precedent):
  * ``_swing_fixture`` -- a 6-bar ``4h`` series engineered to produce FOUR swing pivots, one of
    them with a DELIBERATE near-duplicate high (a clean, unambiguous ``touch_count == 2`` case)
    and three isolated ones (``touch_count == 1``).
  * ``_prior_period_fixture`` -- a 3-bar ``1d`` series isolating the period-closing gate: a day's
    high/low/close become referenceable starting exactly at the FOLLOWING day's as-of, never
    earlier, independent of the swing-pivot mechanism.

The committed keyless PG fixture (``tests/fixtures/bars``, era-4 J-01) then proves the SAME
mechanisms hold on real recorded data end to end, with exact values confirmed by direct
computation (not hand-derived): a swing-high at 149.4796 (1h, touch 1, strength 2.0), a swing-low
at 148.06 (1h, touch 2, strength 4.0 -- its neighbour pivot at 148.095 sits within the configured
touch tolerance), and the 1d series' prior-period extremes + its own swing-low pivot at 139.89.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import CONFIG, Config
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.levels import (
    PRIOR_PERIOD_EXTREME,
    PRIOR_PERIOD_TIMEFRAMES,
    SWING_PIVOT,
    compute_levels,
)

FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"

_DAY = 86400.0
_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _bar(symbol: str, timeframe: str, day_index: int, high: float, low: float, close: float) -> RawBar:
    return RawBar(symbol, timeframe, _BASE + day_index * _DAY, close, high, low, close, 1_000)


# --- Synthetic swing-pivot fixture: 6 "4h" bars (NOT a prior-period timeframe, so ONLY swing
# pivots are computed -- isolates the pivot/touch/strength mechanism from prior-period extremes).
_SWING_SYMBOL = "SYN-SWING"


def _swing_fixture(store: BarStore) -> dict:
    bars = [
        _bar(_SWING_SYMBOL, "4h", 0, 99.0, 90.0, 95.0),
        _bar(_SWING_SYMBOL, "4h", 1, 130.0, 120.0, 125.0),   # swing-high @130 (neighbours 99/110)
        _bar(_SWING_SYMBOL, "4h", 2, 110.0, 100.0, 105.0),   # swing-low @100 (neighbours 120/105)
        _bar(_SWING_SYMBOL, "4h", 3, 115.0, 105.0, 110.0),   # swing-high @115 (neighbours 110/112)
        _bar(_SWING_SYMBOL, "4h", 4, 112.0, 102.0, 108.0),   # swing-low @102 (neighbours 105/120)
        _bar(_SWING_SYMBOL, "4h", 5, 130.03, 120.0, 125.0),  # NOT a pivot itself (last bar) --
        # its high (130.03) sits within tolerance of bar 1's swing-high (130.0), giving that ONE
        # level touch_count == 2 while the other three stay touch_count == 1.
    ]
    return store.record(
        symbol=_SWING_SYMBOL, timeframe="4h",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-07T00:00:00Z",
        feed="sip", bars=bars,
    )


# --- Synthetic prior-period fixture: 3 "1d" bars, isolating the period-closing gate.
_PRIOR_SYMBOL = "SYN-PRIOR"


def _prior_period_fixture(store: BarStore) -> dict:
    bars = [
        _bar(_PRIOR_SYMBOL, "1d", 0, 50.0, 40.0, 45.0),
        _bar(_PRIOR_SYMBOL, "1d", 1, 60.0, 42.0, 55.0),  # swing-high @60 once day 2 is visible
        _bar(_PRIOR_SYMBOL, "1d", 2, 52.0, 41.0, 48.0),
    ]
    return store.record(
        symbol=_PRIOR_SYMBOL, timeframe="1d",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-04T00:00:00Z",
        feed="sip", bars=bars,
    )


def _levels_by_price(result: dict) -> dict[float, dict]:
    return {lvl["price"]: lvl for lvl in result["levels"]}


# --- Swing pivots: exact price/touch_count/strength, config-sourced N -----------------------------


def test_swing_pivot_strict_extreme_over_configured_lookback(tmp_path):
    store = BarStore(tmp_path / "bars")
    _swing_fixture(store)
    as_of = _BASE + 5 * _DAY  # the last bar's own ts -- every pivot fully confirmable
    result = compute_levels(store, _SWING_SYMBOL, as_of, CONFIG)

    assert result["no_bar_series_for_symbol"] is False
    by_price = _levels_by_price(result)
    assert set(by_price) == {100.0, 102.0, 115.0, 130.0}
    for price in (100.0, 102.0, 115.0, 130.0):
        assert by_price[price]["timeframe"] == "4h"
        assert by_price[price]["type"] == SWING_PIVOT

    # Three isolated pivots: touch_count == 1, strength == weight (the 4h weight) * 1.
    weight_4h = CONFIG.sr_timeframe_weights["4h"]
    for price in (100.0, 102.0, 115.0):
        assert by_price[price]["touch_count"] == 1
        assert by_price[price]["strength"] == weight_4h

    # The engineered near-duplicate: bar 5's high (130.03) is within the configured touch
    # tolerance of bar 1's swing-high (130.0) -- touch_count == 2, strength == weight * 2.
    assert by_price[130.0]["touch_count"] == 2
    assert by_price[130.0]["strength"] == weight_4h * 2


def test_swing_pivot_lookback_is_config_sourced_a_wider_n_suppresses_a_pivot(tmp_path):
    """The SAME fixture with a wider ``sr_pivot_lookback`` requires more confirming neighbours on
    each side -- 130.0's neighbours (99.0, 110.0 on one side; 110.0 is fine but with lookback=2 the
    130.0 bar (index 1) has no second bar to its left, so it can never be checked at all. This
    proves N is read from config, not hardcoded to 1."""
    store = BarStore(tmp_path / "bars")
    _swing_fixture(store)
    as_of = _BASE + 5 * _DAY
    wide_config = Config(sr_pivot_lookback=2)
    result = compute_levels(store, _SWING_SYMBOL, as_of, wide_config)
    # With N=2 a centre needs 2 bars on EACH side; only index 2 and 3 qualify (of 6 bars, valid
    # centres are index 2..3). Bar 1 (index 1, the 130.0 pivot under N=1) can no longer be checked
    # at all -- proving the lookback width came from config, not a hardcoded 1.
    prices = {lvl["price"] for lvl in result["levels"]}
    assert 130.0 not in prices


# --- Prior-period extremes: exact gating on the FOLLOWING period's as-of ---------------------------


def test_prior_period_extreme_referenceable_only_from_the_following_periods_as_of(tmp_path):
    store = BarStore(tmp_path / "bars")
    _prior_period_fixture(store)

    # As of day 1's own instant: only day 0 has CLOSED (period_end == this as_of); day 1 itself is
    # still the current, forming period -- not yet a prior-period level. No swing pivot yet either
    # (the day-1 candidate needs day 2, which is not even visible at this as_of).
    as_of_day1 = _BASE + 1 * _DAY
    result_day1 = compute_levels(store, _PRIOR_SYMBOL, as_of_day1, CONFIG)
    by_price_1 = _levels_by_price(result_day1)
    assert set(by_price_1) == {40.0, 45.0, 50.0}  # day 0's low / close / high
    weight_1d = CONFIG.sr_timeframe_weights["1d"]
    for price in (40.0, 45.0, 50.0):
        assert by_price_1[price]["type"] == PRIOR_PERIOD_EXTREME
        assert by_price_1[price]["timeframe"] == "1d"
        assert by_price_1[price]["touch_count"] == 1
        assert by_price_1[price]["strength"] == weight_1d

    # As of day 2's own instant: day 1 has now closed too (its low/close/high join the prior-period
    # set) AND its swing-high pivot (60.0) is now confirmable (day 2 is visible).
    as_of_day2 = _BASE + 2 * _DAY
    result_day2 = compute_levels(store, _PRIOR_SYMBOL, as_of_day2, CONFIG)
    by_price_2 = _levels_by_price(result_day2)
    prior_period_prices = {
        lvl["price"] for lvl in result_day2["levels"] if lvl["type"] == PRIOR_PERIOD_EXTREME
    }
    swing_prices = {lvl["price"] for lvl in result_day2["levels"] if lvl["type"] == SWING_PIVOT}
    assert prior_period_prices == {40.0, 45.0, 50.0, 42.0, 55.0, 60.0}
    assert swing_prices == {60.0}
    assert by_price_2[60.0]["type"] == SWING_PIVOT  # the swing-pivot entry wins the price key here
    # Both the swing-pivot AND prior-period-extreme entries at 60.0 exist (two distinct `type`
    # values, same price) -- assert via the raw list since `_levels_by_price` collapses same-price
    # entries to the last one.
    entries_at_60 = [lvl for lvl in result_day2["levels"] if lvl["price"] == 60.0]
    assert {e["type"] for e in entries_at_60} == {SWING_PIVOT, PRIOR_PERIOD_EXTREME}
    for e in entries_at_60:
        assert e["touch_count"] == 1 and e["strength"] == weight_1d


def test_prior_period_timeframes_are_exactly_the_long_term_bucket():
    assert PRIOR_PERIOD_TIMEFRAMES == ("1d", "1w", "1mo")
    # Swing pivots apply to a NON-prior-period timeframe too (proven above on "4h") -- prior-period
    # extremes must NOT leak onto it.


def test_prior_period_extreme_does_not_apply_to_a_non_prior_period_timeframe(tmp_path):
    store = BarStore(tmp_path / "bars")
    _swing_fixture(store)  # "4h" -- not in PRIOR_PERIOD_TIMEFRAMES
    as_of = _BASE + 5 * _DAY
    result = compute_levels(store, _SWING_SYMBOL, as_of, CONFIG)
    assert all(lvl["type"] == SWING_PIVOT for lvl in result["levels"])


# --- Lookahead-free: the headline correctness property ---------------------------------------------


def test_lookahead_free_a_level_at_t_is_unchanged_by_any_bar_after_t():
    """The definitive proof: a store holding ONLY bars timestamped <= T produces the IDENTICAL
    result to a store holding the FULL committed fixture (including bars after T), both queried at
    the SAME as-of T. Uses the real committed PG 1h fixture, truncated at bar index 6 (2026-06-09
    19:00Z) -- squarely inside the window, well before the last bar."""
    full_store = BarStore(FIXTURE_BAR_DIR)
    as_of = _epoch("2026-06-09T19:00:00Z")  # bar index 6's own ts
    full_result = compute_levels(full_store, "PG", as_of, CONFIG)

    full_hourly_bars = full_store.load_bars("009371c9c02f46338bafef47148f92ad")
    full_daily_bars = full_store.load_bars("b08b1a55ef4a45b2a1adad8fa82ccdf1")
    truncated_hourly = [b for b in full_hourly_bars if b.epoch <= as_of]
    assert len(truncated_hourly) < len(full_hourly_bars), "the truncation must actually drop bars"

    def _make_truncated_store(root: Path) -> BarStore:
        trunc = BarStore(root)
        trunc.record(
            symbol="PG", timeframe="1h", window_start_utc="2026-06-09T13:00:00Z",
            window_end_utc="2026-06-09T19:00:00Z", feed="sip", bars=truncated_hourly,
        )
        trunc.record(
            symbol="PG", timeframe="1d", window_start_utc="2026-06-01T00:00:00Z",
            window_end_utc="2026-06-06T00:00:00Z", feed="sip", bars=full_daily_bars,
        )
        return trunc

    import tempfile

    with tempfile.TemporaryDirectory() as td:
        truncated_store = _make_truncated_store(Path(td) / "bars")
        truncated_result = compute_levels(truncated_store, "PG", as_of, CONFIG)

    assert json.dumps(truncated_result, sort_keys=True) == json.dumps(full_result, sort_keys=True)
    assert len(full_result["levels"]) >= 1, "the proof must exercise at least one real level"


# --- Byte-identical determinism ---------------------------------------------------------------------


def test_byte_identical_determinism_across_independent_runs():
    store = BarStore(FIXTURE_BAR_DIR)
    as_of = _epoch("2026-06-09T21:00:00Z")
    first = compute_levels(store, "PG", as_of, CONFIG)
    second = compute_levels(BarStore(FIXTURE_BAR_DIR), "PG", as_of, CONFIG)  # a FRESH store object
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


# --- The committed PG fixture: exact real-data acceptance values -----------------------------------


def test_committed_fixture_swing_pivots_exact_values_keyless():
    """Manual verification target (plan's Key Test Scenario): the PG 1h fixture (9 bars,
    2026-06-09T13:00-21:00Z) yields a swing-high at bar index 3 (149.4796, both neighbours lower)
    and a swing-low at bar index 4 (148.06, both neighbours higher) with the default N=1 -- exact
    values, not just "a pivot exists". The full detector also finds bar index 6 as BOTH a
    swing-high (148.74) and a swing-low (148.095), each within touch tolerance of the OTHER's
    respective swing-low (148.06 vs 148.095, 0.035 apart) -- both of those levels carry
    touch_count 2; the isolated 149.4796 high stays touch_count 1."""
    store = BarStore(FIXTURE_BAR_DIR)
    as_of = _epoch("2026-06-09T21:00:00Z")  # the window's own end -- every 1h bar visible
    result = compute_levels(store, "PG", as_of, CONFIG)
    weight_1h = CONFIG.sr_timeframe_weights["1h"]

    hourly = [lvl for lvl in result["levels"] if lvl["timeframe"] == "1h"]
    by_price = {lvl["price"]: lvl for lvl in hourly}
    assert set(by_price) == {149.4796, 148.74, 148.06, 148.095}
    for price in by_price:
        assert by_price[price]["type"] == SWING_PIVOT

    assert by_price[149.4796]["touch_count"] == 1
    assert by_price[149.4796]["strength"] == weight_1h * 1
    for price in (148.74, 148.06, 148.095):
        assert by_price[price]["touch_count"] == 2
        assert by_price[price]["strength"] == weight_1h * 2


def test_committed_fixture_prior_period_extremes_exact_values_keyless():
    """The PG 1d fixture (5 bars, early June 2026): each day's high/low/close is referenceable as a
    prior-period level once queried at/after the FOLLOWING day (here, well after the whole window)."""
    store = BarStore(FIXTURE_BAR_DIR)
    as_of = _epoch("2026-06-09T21:00:00Z")  # well after the 1d window closes -- all 5 days prior
    result = compute_levels(store, "PG", as_of, CONFIG)
    weight_1d = CONFIG.sr_timeframe_weights["1d"]

    daily_prior = [
        lvl for lvl in result["levels"]
        if lvl["timeframe"] == "1d" and lvl["type"] == PRIOR_PERIOD_EXTREME
    ]
    assert len(daily_prior) == 15  # 5 days * (high, low, close)
    by_price = {lvl["price"]: lvl for lvl in daily_prior}
    # Day 1 (2026-06-01): high 141.82, low 138.86, close 140.28 (the committed fixture's own values).
    assert by_price[141.82]["touch_count"] == 2  # within touch tolerance of day 5's low, 141.8
    assert by_price[141.82]["strength"] == weight_1d * 2
    assert by_price[138.86]["touch_count"] == 1
    assert by_price[138.86]["strength"] == weight_1d * 1
    assert by_price[140.28]["touch_count"] == 1
    assert by_price[140.28]["strength"] == weight_1d * 1

    daily_swing = [
        lvl for lvl in result["levels"] if lvl["timeframe"] == "1d" and lvl["type"] == SWING_PIVOT
    ]
    assert len(daily_swing) == 1
    assert daily_swing[0]["price"] == 139.89
    assert daily_swing[0]["touch_count"] == 1
    assert daily_swing[0]["strength"] == weight_1d * 1

    assert len(result["levels"]) == 20  # 15 prior-period + 1 daily swing + 4 hourly swing


# --- Honest, distinct failure states (never one bare ambiguous empty array) ------------------------


def test_symbol_with_no_recorded_bar_series_is_a_distinct_honest_state(tmp_path):
    store = BarStore(tmp_path / "bars")
    _swing_fixture(store)  # records ONLY `_SWING_SYMBOL` -- never the queried symbol below
    result = compute_levels(store, "NEVER-RECORDED", _BASE + 100 * _DAY, CONFIG)
    assert result == {"levels": [], "no_bar_series_for_symbol": True}


def test_symbol_with_bar_series_but_nothing_derivable_yet_is_a_distinct_honest_state(tmp_path):
    store = BarStore(tmp_path / "bars")
    _swing_fixture(store)
    result = compute_levels(store, _SWING_SYMBOL, _BASE - 1, CONFIG)  # before the series even starts
    assert result == {"levels": [], "no_bar_series_for_symbol": False}


def test_empty_bar_store_is_no_bar_series_for_symbol(tmp_path):
    store = BarStore(tmp_path / "bars")  # never recorded anything at all
    result = compute_levels(store, "PG", _BASE, CONFIG)
    assert result == {"levels": [], "no_bar_series_for_symbol": True}


# --- Multiple series for the same (symbol, timeframe): most-recently-created wins ------------------


def test_multiple_series_for_same_symbol_and_timeframe_the_most_recently_created_wins(tmp_path):
    store = BarStore(tmp_path / "bars")
    # Two DISTINCT (different content, so both are legally recordable) 3-bar series for the SAME
    # (symbol, timeframe) -- each yields its OWN uniquely-priced swing-low pivot, so whichever
    # price appears in the result proves which series' content was selected.
    older = [
        _bar("DUP", "4h", 0, 210.0, 200.0, 205.0),
        _bar("DUP", "4h", 1, 195.0, 190.0, 192.0),  # swing-low @190 (older series' signature)
        _bar("DUP", "4h", 2, 205.0, 195.0, 198.0),
    ]
    newer = [
        _bar("DUP", "4h", 0, 310.0, 300.0, 305.0),
        _bar("DUP", "4h", 1, 295.0, 290.0, 292.0),  # swing-low @290 (newer series' signature)
        _bar("DUP", "4h", 2, 305.0, 295.0, 298.0),
    ]
    store.record(
        symbol="DUP", timeframe="4h", window_start_utc="2026-01-01T00:00:00Z",
        window_end_utc="2026-01-02T00:00:00Z", feed="sip", bars=older,
    )
    store.record(
        symbol="DUP", timeframe="4h", window_start_utc="2026-02-01T00:00:00Z",
        window_end_utc="2026-02-02T00:00:00Z", feed="sip", bars=newer,
    )
    records, _errors = store.list()
    dup_records = [r for r in records if r["symbol"] == "DUP"]
    assert len(dup_records) == 2, "both distinct series must have registered"
    # The store's own `created_utc` ordering decides which series wins -- confirm the SECOND
    # recorded row really does carry the later timestamp before trusting the selection result.
    dup_records.sort(key=lambda r: r["created_utc"])
    assert dup_records[-1]["bars"][1]["low"] == 290.0, "the later-created record must be `newer`"

    result = compute_levels(store, "DUP", _BASE + 2 * _DAY, CONFIG)
    prices = {lvl["price"] for lvl in result["levels"]}
    assert 290.0 in prices, "the most-recently-created series must be the one selected"
    assert 190.0 not in prices, "the older series' content must not also leak into the result"


# --- No magic numbers: every S/R parameter is config-sourced ----------------------------------------


def test_sr_parameters_are_config_sourced_no_magic_numbers():
    assert isinstance(CONFIG.sr_pivot_lookback, int) and CONFIG.sr_pivot_lookback >= 1
    assert isinstance(CONFIG.sr_touch_tolerance_bps, float) and CONFIG.sr_touch_tolerance_bps > 0
    assert isinstance(CONFIG.sr_timeframe_weights, dict) and CONFIG.sr_timeframe_weights
    assert set(CONFIG.sr_timeframe_weights) == set(CONFIG.bar_timeframes)

    import inspect

    from app.research import levels as levels_module

    src = inspect.getsource(levels_module)
    assert "config.sr_pivot_lookback" in src
    assert "config.sr_touch_tolerance_bps" in src
    assert "config.sr_timeframe_weights" in src


# --- config_fingerprint: sr_* fields excluded, default pinned unmoved -------------------------------


def test_sr_config_fields_are_excluded_from_config_fingerprint():
    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
    assert Config(sr_pivot_lookback=5).config_fingerprint() == CONFIG.config_fingerprint()
    assert Config(sr_touch_tolerance_bps=50.0).config_fingerprint() == CONFIG.config_fingerprint()
    assert (
        Config(sr_timeframe_weights={"1d": 99.0}).config_fingerprint() == CONFIG.config_fingerprint()
    )
    # ...while a real classifier threshold still moves it (the counter-test).
    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()
