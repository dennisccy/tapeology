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
    CLASS_A,
    CLASS_B,
    CLASS_C,
    PRIOR_PERIOD_EXTREME,
    PRIOR_PERIOD_TIMEFRAMES,
    SWING_PIVOT,
    compute_confluence_zones,
    compute_levels,
    level_change_points,
)

FIXTURE_BAR_DIR = Path(__file__).parent / "fixtures" / "bars"

_DAY = 86400.0
_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _bar(symbol: str, timeframe: str, day_index: int, high: float, low: float, close: float) -> RawBar:
    return RawBar(symbol, timeframe, _BASE + day_index * _DAY, close, high, low, close, 1_000)


def _lvl(price: float, timeframe: str, strength: float, level_type: str = SWING_PIVOT, touch_count: int = 1) -> dict:
    """A hand-built level dict -- the exact shape ``research/levels.py``'s own ``_level()``
    produces -- for testing ``compute_confluence_zones`` DIRECTLY as a pure function, independent
    of any bar/store machinery (clustering/scoring/grading depend only on ``price``, ``timeframe``,
    and ``strength``; ``type``/``touch_count`` are carried through unchanged and rarely matter
    here)."""
    return {"price": price, "timeframe": timeframe, "type": level_type, "touch_count": touch_count, "strength": strength}


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


# --- Confluence zones + A/B/C classes: the pure `compute_confluence_zones` function ----------------
# Direct unit tests -- hand-built level dicts, no bar/store machinery -- isolate the
# clustering/scoring/grading algorithm itself from the bar-derived integration proofs further below.


def test_confluence_clustering_joins_within_band_across_timeframes_and_grades_class_a():
    levels = [
        _lvl(100.00, "1h", strength=2.0),
        _lvl(100.05, "1d", strength=4.0),
        _lvl(100.10, "1w", strength=5.0),
        _lvl(500.00, "1h", strength=2.0),  # isolated -- no partner within band, joins no zone
    ]
    zones = compute_confluence_zones(levels, CONFIG)
    assert len(zones) == 1
    zone = zones[0]
    assert [m["price"] for m in zone["levels"]] == [100.00, 100.05, 100.10]
    assert {m["timeframe"] for m in zone["levels"]} == {"1h", "1d", "1w"}
    assert zone["score"] == 11.0  # 2.0 + 4.0 + 5.0, timeframe-weighted sum of member strengths
    assert zone["class"] == CLASS_A


def test_confluence_class_a_requires_a_long_term_member_not_just_timeframe_count():
    """Three DISTINCT timeframes clustering -- but NONE in the long-term bucket -- must grade B,
    not A: the long-term-member condition is enforced INDEPENDENTLY of the distinct-timeframe
    count (goal.md's "a required long-term member", not merely "several timeframes")."""
    assert not (set(("1h", "4h", "8h")) & set(PRIOR_PERIOD_TIMEFRAMES)), "the setup's own premise"
    levels = [
        _lvl(50.00, "1h", strength=2.0),
        _lvl(50.02, "4h", strength=3.0),
        _lvl(50.04, "8h", strength=3.0),
    ]
    zones = compute_confluence_zones(levels, CONFIG)
    assert len(zones) == 1
    assert len({m["timeframe"] for m in zones[0]["levels"]}) == 3  # meets the COUNT floor...
    assert zones[0]["class"] == CLASS_B  # ...but never A without a long-term member


def test_confluence_class_b_two_distinct_timeframes_below_the_class_a_floor():
    levels = [_lvl(75.00, "1h", strength=2.0), _lvl(75.03, "1d", strength=4.0)]
    zones = compute_confluence_zones(levels, CONFIG)
    assert len(zones) == 1
    assert zones[0]["score"] == 6.0
    assert zones[0]["class"] == CLASS_B


def test_confluence_class_c_same_timeframe_cluster_below_the_class_b_floor():
    levels = [_lvl(60.00, "1h", strength=2.0), _lvl(60.02, "1h", strength=2.0)]
    zones = compute_confluence_zones(levels, CONFIG)
    assert len(zones) == 1
    assert zones[0]["score"] == 4.0
    assert zones[0]["class"] == CLASS_C


def test_confluence_clustering_is_anchor_fixed_not_chained_to_the_previous_member():
    """A -> B is within band of the cluster's ANCHOR (A, the first/lowest member); B -> C is
    within band of B but C is NOT within band of the anchor -- proves the scan re-checks every
    candidate against the cluster's FIXED anchor, never against the most-recently-added member (a
    naive chained scan would incorrectly admit C too, letting the cluster's price span drift
    unbounded)."""
    band_bps = CONFIG.sr_confluence_band_bps
    a, b, c = 100.00, 100.15, 100.30
    tol = a * band_bps / 10_000.0
    assert abs(b - a) <= tol and abs(c - b) <= tol and abs(c - a) > tol, "the setup's own premise"
    levels = [_lvl(a, "1h", strength=2.0), _lvl(b, "1d", strength=4.0), _lvl(c, "1w", strength=5.0)]
    zones = compute_confluence_zones(levels, CONFIG)
    assert len(zones) == 1  # {a, b} cluster; c is dropped as an isolated singleton
    assert [m["price"] for m in zones[0]["levels"]] == [a, b]


def test_confluence_singleton_level_produces_no_zone():
    levels = [_lvl(10.0, "1h", strength=2.0), _lvl(900.0, "1d", strength=4.0)]
    assert compute_confluence_zones(levels, CONFIG) == []


def test_confluence_zones_sorted_by_explicit_total_order_ascending_by_lowest_member_price():
    levels = [
        _lvl(500.00, "1h", strength=2.0), _lvl(500.02, "1d", strength=4.0),
        _lvl(100.00, "1h", strength=2.0), _lvl(100.01, "1d", strength=4.0),
    ]
    zones = compute_confluence_zones(levels, CONFIG)
    assert [z["levels"][0]["price"] for z in zones] == [100.00, 500.00]


def test_confluence_zones_empty_for_empty_levels():
    assert compute_confluence_zones([], CONFIG) == []


# --- Lookahead-free: the headline correctness property ---------------------------------------------


def test_lookahead_free_a_level_at_t_is_unchanged_by_any_bar_after_t():
    """The definitive proof: a store holding ONLY bars timestamped <= T produces the IDENTICAL
    result to a store holding the FULL committed fixture (including bars after T), both queried at
    the SAME as-of T. Uses the real committed PG 1h fixture, truncated at bar index 6 (2026-06-09
    19:00Z) -- squarely inside the window, well before the last bar. The full-dict
    ``json.dumps(...) == json.dumps(...)`` comparison below covers ``confluence_zones``/``class``
    too (J-03) -- extended below with an EXPLICIT non-vacuous zone assertion, since
    ``compute_confluence_zones`` is a pure function of this SAME (already lookahead-free) `levels`
    list and introduces no second truncation surface of its own."""
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

    # J-03 extension: at this EARLIER as_of the cross-timeframe zone has only TWO members --
    # 148.095 (the 1h swing confirmed only once bar index 7 becomes visible) is NOT yet part of it
    # -- proving idx6's not-yet-visible neighbour never leaked into the zone or its class either.
    zones = full_result["confluence_zones"]
    assert len(zones) == 6, "the proof must exercise a real, non-trivial set of zones"
    cross_tf_zone = zones[-1]
    assert [m["price"] for m in cross_tf_zone["levels"]] == [148.06, 148.23]
    assert cross_tf_zone["score"] == 8.0
    assert cross_tf_zone["class"] == CLASS_B


# --- Byte-identical determinism ---------------------------------------------------------------------


def test_byte_identical_determinism_across_independent_runs():
    store = BarStore(FIXTURE_BAR_DIR)
    as_of = _epoch("2026-06-09T21:00:00Z")
    first = compute_levels(store, "PG", as_of, CONFIG)
    second = compute_levels(BarStore(FIXTURE_BAR_DIR), "PG", as_of, CONFIG)  # a FRESH store object
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert len(first["confluence_zones"]) >= 1, "the proof must exercise at least one real zone"


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


def test_committed_fixture_confluence_zones_exact_values_keyless():
    """The real PG fixture (era-4 J-01) stores only TWO timeframes (1h, 1d) -- confirmed by direct
    computation, not hand-derived: it produces SIX confluence zones, FIVE same-timeframe (1d-only)
    C-grade zones and exactly ONE genuine cross-timeframe (1h+1d) B-grade zone -- and, honestly,
    NEVER a class A zone (which needs a THIRD distinct timeframe the committed fixture does not
    have; class A is instead proven reachable on the synthetic 3-timeframe fixture below)."""
    store = BarStore(FIXTURE_BAR_DIR)
    as_of = _epoch("2026-06-09T21:00:00Z")
    result = compute_levels(store, "PG", as_of, CONFIG)
    zones = result["confluence_zones"]

    assert [z["class"] for z in zones] == [CLASS_C, CLASS_C, CLASS_C, CLASS_C, CLASS_C, CLASS_B]
    assert CLASS_A not in {z["class"] for z in zones}, "unreachable on this 2-timeframe fixture"

    def _prices(zone: dict) -> list[float]:
        return [m["price"] for m in zone["levels"]]

    assert _prices(zones[0]) == [138.86, 139.03] and zones[0]["score"] == 8.0
    assert _prices(zones[1]) == [139.89, 139.89, 140.0] and zones[1]["score"] == 12.0
    assert _prices(zones[2]) == [140.19, 140.28] and zones[2]["score"] == 8.0
    assert _prices(zones[3]) == [140.78, 140.82] and zones[3]["score"] == 8.0
    assert _prices(zones[4]) == [141.8, 141.82] and zones[4]["score"] == 16.0

    cross_tf_zone = zones[5]
    assert _prices(cross_tf_zone) == [148.06, 148.095, 148.23]
    assert {m["timeframe"] for m in cross_tf_zone["levels"]} == {"1h", "1d"}
    assert cross_tf_zone["score"] == 12.0


# --- Confluence zones through `compute_levels`: a real bar-derived class A (the plan's own "Known
# Consideration" -- the committed PG fixture stores only TWO timeframes and can never itself
# produce a class A zone, so a synthetic THREE-timeframe fixture proves class A IS reachable
# through the real, bar-driven `compute_levels` path, not merely the pure-function unit tests above)
# ------------------------------------------------------------------------------------------------

_CONFLUENCE_SYMBOL = "SYN-CONFLUENCE"


def _confluence_fixture(store: BarStore) -> None:
    """A three-timeframe (1h/1d/1w) synthetic fixture engineered for an exact A/B/C case. Every
    "noise" extreme (each bar's OTHER high/low, engineered far outside any band) sits isolated --
    verified by direct computation, not hand-derived:

      * ~100.00 (1h swing-high) + ~100.05 (1d prior-period close) + ~100.10 (1w prior-period close)
        -- THREE distinct timeframes including two long-term ones -- class A.
      * ~200.00 (1h swing-high) + ~200.08 (1d prior-period close) -- TWO distinct timeframes --
        class B.
      * ~300.00 + ~300.05 (both 1h swing-highs) -- ONE distinct timeframe -- class C.
      * ~500.00 (1h swing-high), isolated -- no confluence partner -- appears in NO zone.
    """
    hourly_specs = [
        (50, 40, 45), (100.00, 41, 98), (55, 42, 50), (200.00, 43, 198), (57, 44, 52),
        (300.00, 45, 298), (58, 46, 53), (300.05, 47, 297), (59, 48, 54), (500.00, 49, 498),
        (60, 50, 55),
    ]
    hourly_bars = [
        RawBar(_CONFLUENCE_SYMBOL, "1h", _BASE + i * 3600.0, close, high, low, close, 1_000)
        for i, (high, low, close) in enumerate(hourly_specs)
    ]
    daily_bars = [
        RawBar(_CONFLUENCE_SYMBOL, "1d", _BASE + 0 * _DAY, 100.05, 900, 10, 100.05, 1_000),
        RawBar(_CONFLUENCE_SYMBOL, "1d", _BASE + 1 * _DAY, 200.08, 910, 20, 200.08, 1_000),
    ]
    weekly_bars = [
        RawBar(_CONFLUENCE_SYMBOL, "1w", _BASE + 0 * _DAY, 100.10, 920, 30, 100.10, 1_000),
    ]
    store.record(
        symbol=_CONFLUENCE_SYMBOL, timeframe="1h",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-01T11:00:00Z",
        feed="sip", bars=hourly_bars,
    )
    store.record(
        symbol=_CONFLUENCE_SYMBOL, timeframe="1d",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-03T00:00:00Z",
        feed="sip", bars=daily_bars,
    )
    store.record(
        symbol=_CONFLUENCE_SYMBOL, timeframe="1w",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc="2026-01-08T00:00:00Z",
        feed="sip", bars=weekly_bars,
    )


def test_synthetic_three_timeframe_fixture_produces_exact_a_b_c_zones_through_compute_levels(tmp_path):
    store = BarStore(tmp_path / "bars")
    _confluence_fixture(store)
    as_of = _BASE + 8 * _DAY  # comfortably past every period's closure (1w's 604800s is longest)
    result = compute_levels(store, _CONFLUENCE_SYMBOL, as_of, CONFIG)
    assert result["no_bar_series_for_symbol"] is False
    zones = result["confluence_zones"]
    assert len(zones) == 3

    zone_a, zone_b, zone_c = zones
    assert [m["price"] for m in zone_a["levels"]] == [100.00, 100.05, 100.10]
    assert {m["timeframe"] for m in zone_a["levels"]} == {"1h", "1d", "1w"}
    assert zone_a["score"] == 11.0  # 2.0 (1h) + 4.0 (1d) + 5.0 (1w)
    assert zone_a["class"] == CLASS_A

    assert [m["price"] for m in zone_b["levels"]] == [200.00, 200.08]
    assert {m["timeframe"] for m in zone_b["levels"]} == {"1h", "1d"}
    assert zone_b["score"] == 6.0  # 2.0 (1h) + 4.0 (1d)
    assert zone_b["class"] == CLASS_B

    assert [m["price"] for m in zone_c["levels"]] == [300.00, 300.05]
    assert {m["timeframe"] for m in zone_c["levels"]} == {"1h"}
    assert zone_c["score"] == 8.0  # 4.0 + 4.0 (both touch_count 2 -- see the 130.0/130.03 precedent)
    assert zone_c["class"] == CLASS_C

    # The isolated 500.00 swing-high and every engineered noise extreme appear in NO zone.
    all_zone_prices = {m["price"] for z in zones for m in z["levels"]}
    assert 500.00 not in all_zone_prices
    assert all(price not in all_zone_prices for price in (900, 10, 910, 20, 920, 30))


def test_no_qualifying_cluster_on_bar_derived_levels_is_an_honest_empty_zones_list(tmp_path):
    """The EXISTING J-02 swing fixture, unmodified: its four pivots (100.0/102.0/115.0/130.0) are
    all far apart in price (the closest gap is 200+ bps, well outside the confluence band) -- an
    honest empty ``confluence_zones`` list, never fabricated, and distinct from
    ``no_bar_series_for_symbol`` (which stays False: the symbol DOES have levels, just no
    qualifying cluster among them)."""
    store = BarStore(tmp_path / "bars")
    _swing_fixture(store)
    result = compute_levels(store, _SWING_SYMBOL, _BASE + 5 * _DAY, CONFIG)
    assert result["no_bar_series_for_symbol"] is False
    assert len(result["levels"]) == 4
    assert result["confluence_zones"] == []


# --- Honest, distinct failure states (never one bare ambiguous empty array) ------------------------


def test_symbol_with_no_recorded_bar_series_is_a_distinct_honest_state(tmp_path):
    store = BarStore(tmp_path / "bars")
    _swing_fixture(store)  # records ONLY `_SWING_SYMBOL` -- never the queried symbol below
    result = compute_levels(store, "NEVER-RECORDED", _BASE + 100 * _DAY, CONFIG)
    assert result == {"levels": [], "no_bar_series_for_symbol": True, "confluence_zones": []}


def test_symbol_with_bar_series_but_nothing_derivable_yet_is_a_distinct_honest_state(tmp_path):
    store = BarStore(tmp_path / "bars")
    _swing_fixture(store)
    result = compute_levels(store, _SWING_SYMBOL, _BASE - 1, CONFIG)  # before the series even starts
    assert result == {"levels": [], "no_bar_series_for_symbol": False, "confluence_zones": []}


def test_empty_bar_store_is_no_bar_series_for_symbol(tmp_path):
    store = BarStore(tmp_path / "bars")  # never recorded anything at all
    result = compute_levels(store, "PG", _BASE, CONFIG)
    assert result == {"levels": [], "no_bar_series_for_symbol": True, "confluence_zones": []}


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
    assert isinstance(CONFIG.sr_confluence_band_bps, float) and CONFIG.sr_confluence_band_bps > 0
    assert isinstance(CONFIG.sr_confluence_class_a_min_timeframes, int)
    assert isinstance(CONFIG.sr_confluence_class_b_min_timeframes, int)
    assert CONFIG.sr_confluence_class_b_min_timeframes >= 2  # "distinct timeframes" needs >= 2
    # A is the strictly higher bar -- its floor can never be laxer than B's.
    assert CONFIG.sr_confluence_class_a_min_timeframes >= CONFIG.sr_confluence_class_b_min_timeframes

    import inspect

    from app.research import levels as levels_module

    src = inspect.getsource(levels_module)
    assert "config.sr_pivot_lookback" in src
    assert "config.sr_touch_tolerance_bps" in src
    assert "config.sr_timeframe_weights" in src
    assert "config.sr_confluence_band_bps" in src
    assert "config.sr_confluence_class_a_min_timeframes" in src
    assert "config.sr_confluence_class_b_min_timeframes" in src


# --- config_fingerprint: sr_* fields excluded, default pinned unmoved -------------------------------


def test_sr_config_fields_are_excluded_from_config_fingerprint():
    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
    assert Config(sr_pivot_lookback=5).config_fingerprint() == CONFIG.config_fingerprint()
    assert Config(sr_touch_tolerance_bps=50.0).config_fingerprint() == CONFIG.config_fingerprint()
    assert (
        Config(sr_timeframe_weights={"1d": 99.0}).config_fingerprint() == CONFIG.config_fingerprint()
    )
    assert Config(sr_confluence_band_bps=999.0).config_fingerprint() == CONFIG.config_fingerprint()
    assert (
        Config(sr_confluence_class_a_min_timeframes=9).config_fingerprint()
        == CONFIG.config_fingerprint()
    )
    assert (
        Config(sr_confluence_class_b_min_timeframes=9).config_fingerprint()
        == CONFIG.config_fingerprint()
    )
    # ...while a real classifier threshold still moves it (the counter-test).
    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()


# --- level_change_points: the arm memo's change-point contract (goal-fast_wall J-03) ---------------
# Reuses the synthetic three-timeframe ``_confluence_fixture`` directly above (already has a
# non-prior-period series ("1h") AND two prior-period series ("1d", "1w") -- exactly TC-1's own
# premise) rather than a second, near-duplicate fixture.


def test_level_change_points_returns_sorted_deduped_superset_of_bar_epochs_and_period_closes(tmp_path):
    """TC-1: the union of every healthy series' own bar epochs, plus each PRIOR_PERIOD_TIMEFRAMES
    bar's own epoch + period_seconds close instant -- sorted, deduplicated -- verified by direct
    computation against the confluence fixture's own known epochs (never hand-waved)."""
    store = BarStore(tmp_path / "bars")
    _confluence_fixture(store)
    points = level_change_points(store, _CONFLUENCE_SYMBOL)

    assert points == tuple(sorted(points)), "must be sorted ascending"
    assert len(points) == len(set(points)), "must be deduplicated"

    # Every 1h bar's own epoch (11 hourly bars; "1h" is NOT a prior-period timeframe -- only its
    # own epochs are change points, never an epoch+period_seconds entry).
    hourly_epochs = {_BASE + i * 3600.0 for i in range(11)}
    assert hourly_epochs <= set(points)

    # The 1d series (a PRIOR_PERIOD_TIMEFRAMES member, two bars at day 0 and day 1): both bars'
    # own epochs (also shared with the 1h/1w series' own day-0 epoch) AND bar 1's own
    # epoch + period_seconds (86400s) close instant.
    assert {_BASE, _BASE + _DAY} <= set(points)
    assert _BASE + 2 * _DAY in points

    # The 1w series (also a PRIOR_PERIOD_TIMEFRAMES member, one bar at day 0): its own epoch
    # (already covered above) AND its own epoch + period_seconds (604800s) close instant.
    assert _BASE + 7 * _DAY in points

    # Exact count: 11 distinct hourly epochs (i=0..10, spanning BASE..BASE+36000) plus the 1d/1w
    # period-close instants NOT already covered by an hourly epoch (BASE+DAY=86400 and
    # BASE+2*DAY=172800 from the 1d series, BASE+7*DAY=604800 from the 1w series -- none of which
    # coincide with any hourly epoch, all <= 36000) -- verified by direct computation.
    assert len(points) == 14


def test_compute_levels_is_constant_between_two_consecutive_change_points(tmp_path):
    """TC-2: the change-point contract, mechanically proven -- two ``as_of`` instants strictly
    between the SAME two consecutive ``level_change_points`` entries produce byte-identical
    ``compute_levels`` output (the property ``backtests.py``'s ``_StructureArmMemo`` relies on to
    memoize arming checks by change-point interval instead of per confirming tick)."""
    store = BarStore(tmp_path / "bars")
    _confluence_fixture(store)
    points = level_change_points(store, _CONFLUENCE_SYMBOL)

    # BASE+2*DAY and BASE+7*DAY are two CONSECUTIVE entries -- nothing else falls between them on
    # this fixture (verified by direct computation against the fixture's own known epochs, per the
    # exact-count proof above).
    lower, upper = _BASE + 2 * _DAY, _BASE + 7 * _DAY
    idx = points.index(lower)
    assert points[idx + 1] == upper, "the fixture's own premise: these must be consecutive entries"

    as_of_1 = lower + 1.0  # strictly between
    as_of_2 = upper - 1.0  # strictly between, far from as_of_1
    assert lower < as_of_1 < as_of_2 < upper

    result_1 = compute_levels(store, _CONFLUENCE_SYMBOL, as_of_1, CONFIG)
    result_2 = compute_levels(store, _CONFLUENCE_SYMBOL, as_of_2, CONFIG)
    assert json.dumps(result_1, sort_keys=True) == json.dumps(result_2, sort_keys=True)
    assert len(result_1["levels"]) >= 1, "the proof must exercise at least one real level"


def test_level_change_points_empty_for_symbol_with_no_healthy_bar_series(tmp_path):
    """The honest empty-tuple absence -- mirrors ``no_bar_series_for_symbol``'s own precedent
    (never a fabricated instant for a symbol with nothing recorded)."""
    store = BarStore(tmp_path / "bars")
    _swing_fixture(store)  # records ONLY `_SWING_SYMBOL` -- never the queried symbol below
    assert level_change_points(store, "NEVER-RECORDED") == ()


# --- The touch-count index: the same answer, in log time -----------------------------------------
# `_touch_count` walked every bar per detected level -- O(levels x bars), invisible at ~2,000 bars
# per series and a 3.5-minute page load once deeper history arrived (AMD 1m: 34k bars, 16.6k levels,
# ~560M comparisons measured). `_TouchIndex` narrows the candidates with a binary search and then
# applies the ORIGINAL predicate to each, so the answers must agree exactly -- not "closely".


def _touch_probe_bars() -> list[RawBar]:
    """Bars whose highs/lows land ON, just inside, and just outside the tolerance boundary of the
    probe prices below — the only region where a windowed pre-filter could disagree with the
    original scan."""
    prices = [
        100.0, 100.0, 100.05, 99.95, 100.0500001, 99.9499999, 100.1, 99.9,
        250.0, 250.125, 249.875, 250.1250001, 0.5, 0.500025, 0.4999,
    ]
    return [
        RawBar("PROBE", "1m", 1_780_000_000.0 + i * 60, p, p + 0.01, p - 0.01, p, 1_000)
        for i, p in enumerate(prices)
    ]


def test_touch_index_agrees_with_the_reference_scan_bar_for_bar():
    from app.research.levels import _touch_count, _TouchIndex

    bars = _touch_probe_bars()
    index = _TouchIndex(bars)
    probes = [b.high for b in bars] + [b.low for b in bars] + [100.0, 250.0, 0.5, 1e-9]
    for tol_bps in (0.0, 1.0, 5.0, CONFIG.sr_touch_tolerance_bps, 100.0):
        for price in probes:
            for defining_index in (0, len(bars) - 1):
                assert index.count(price, tol_bps, defining_index) == _touch_count(
                    bars, price, tol_bps, defining_index
                ), f"disagreement at price={price!r} tol_bps={tol_bps} idx={defining_index}"


def test_touch_index_counts_a_bar_once_even_when_both_its_high_and_low_qualify():
    """A wide tolerance puts BOTH a bar's high and its low inside the window; the bar is still one
    touch. (A naive "count the high matches plus the low matches" index would double it.)"""
    from app.research.levels import _touch_count, _TouchIndex

    bars = _touch_probe_bars()
    wide = 500.0  # basis points — far wider than any bar's own high-to-low span
    for price in (100.0, 250.0):
        assert _TouchIndex(bars).count(price, wide, 0) == _touch_count(bars, price, wide, 0)
        assert _TouchIndex(bars).count(price, wide, 0) <= len(bars)


def test_levels_are_unchanged_by_the_index_on_the_committed_fixture():
    """End to end over the committed real-data fixture: every served level (price, touch_count,
    strength, zones) is byte-identical to computing each touch with the reference scan."""
    from app.research import levels as levels_module

    class _ReferenceIndex:
        def __init__(self, bars: list[RawBar]) -> None:
            self._bars = bars

        def count(self, price: float, tol_bps: float, defining_index: int) -> int:
            return levels_module._touch_count(self._bars, price, tol_bps, defining_index)

    store = BarStore(FIXTURE_BAR_DIR)
    as_of = _epoch("2026-06-09T21:00:00Z")
    indexed = compute_levels(store, "PG", as_of, CONFIG)

    original_index = levels_module._TouchIndex
    levels_module._TouchIndex = _ReferenceIndex  # every detector now uses the full scan
    try:
        reference = compute_levels(store, "PG", as_of, CONFIG)
    finally:
        levels_module._TouchIndex = original_index

    assert json.dumps(indexed, sort_keys=True) == json.dumps(reference, sort_keys=True)
    assert indexed["levels"], "the proof must exercise real levels"
