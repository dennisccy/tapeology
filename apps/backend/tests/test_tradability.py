"""The tradable level map (era-5B capability 1, J-01) -- ``research/tradability.py`` unit +
fixture coverage. Mirrors ``test_levels.py``'s structure: a small synthetic fixture gives full
control over exact expected numbers (band clustering, quality-score arithmetic, round-number
flagging, class inheritance, and top-K capping all verified by direct computation, not
hand-derived), then the real committed AAPL fixture proves the SAME mechanisms hold end to end on
real data and satisfy J-01's pinned acceptance (the 2026-06-22 map's 300.48-302.07 resistance
band).

The synthetic ``SYN-TRADABILITY`` fixture (7 daily bars, symbol isolated from every other test)
deliberately spaces every day's OHLC values far apart (>>20 bps, the raw confluence tolerance) so
``compute_confluence_zones`` returns [] for every price EXCEPT four deliberately engineered
same-day swing-pivot/prior-period-extreme coincidences (170, 190, 220, 250 -- each day's own
extreme is ALSO a swing pivot), which each form a genuine 2-member, class-C zone. This gives one
fixture that exercises BOTH ``class`` outcomes (a real inherited grade, and the honest ``None``
absence) without needing a second, multi-timeframe fixture.
"""

from __future__ import annotations

import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.config import CONFIG, Config
from app.providers.adapters.base import RawBar
from app.research.bars import BarStore
from app.research.tradability import RESISTANCE, SUPPORT, basis_day_key, compute_tradability

FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"

_DAY = 86400.0
_BASE = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()
_SYN_SYMBOL = "SYN-TRADABILITY"


def _epoch(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _syn_bar(day_index: int, high: float, low: float, close: float) -> RawBar:
    return RawBar(_SYN_SYMBOL, "1d", _BASE + day_index * _DAY, close, high, low, close, 1_000)


# Eight days total (index 0..7): the CORE seven days every test in this file relies on, plus an
# EIGHTH ("day 7", 2026-01-08) used only by the no-lookahead / basis-shift tests below -- kept as
# ONE canonical sequence (never two independently-typed literals) so "truncated to N days" always
# means an exact PREFIX of the same real values.
#
# Day 6 (2026-01-07) is the most recent CORE bar; every core test uses
# ``as_of = _SYN_AS_OF`` (2026-01-08), so day 6 is the prior completed session and
# ``current_price`` (day 6's own close) is exactly 100 -- everything above it is a resistance
# candidate, everything at-or-below is a support candidate.
#
# Engineered swing pivots among days 0-6 (lookback=1, verified by direct computation): LOW @190
# (day 2), HIGH @250 (day 3), LOW @170 (day 4), HIGH @220 (day 5) -- each price EXACTLY coincides
# with that same day's own prior-period-extreme high/low, so ``compute_confluence_zones`` forms a
# genuine (same-timeframe, class-C) 2-member zone at each of those four prices. Every other day's
# OHLC values are pairwise >> 20 bps apart (no accidental confluence) and >> 70 bps apart across
# days (no accidental tradability-band merging) -- so every OTHER resistance/support price ends up
# its own singleton band with an honest ``class: None`` (no overlapping zone). Day 7's values
# (999/998/998.5) are deliberately far outside every other day's range -- an unmissable canary for
# "did a bar dated on/after the requested session leak into the result".
_SYN_BAR_SEQUENCE: tuple[RawBar, ...] = (
    _syn_bar(0, 500, 490, 495),
    _syn_bar(1, 400, 390, 395),
    _syn_bar(2, 200, 190, 195),
    _syn_bar(3, 250, 240, 245),
    _syn_bar(4, 180, 170, 175),
    _syn_bar(5, 220, 210, 215),
    _syn_bar(6, 105, 95, 100),
    _syn_bar(7, 999, 998, 998.5),
)


def _seed_synthetic(store: BarStore, num_days: int = 7) -> None:
    """Records the first ``num_days`` bars of ``_SYN_BAR_SEQUENCE`` as ONE ``"1d"`` series (a
    single ``record()`` call, the ``test_levels.py`` lookahead-proof precedent -- never several
    calls, so "truncated to N days" stays an exact PREFIX rather than a merge of several
    independently-registered windows)."""
    bars = list(_SYN_BAR_SEQUENCE[:num_days])
    window_end = datetime.fromtimestamp(_BASE + num_days * _DAY, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    store.record(
        symbol=_SYN_SYMBOL, timeframe="1d",
        window_start_utc="2026-01-01T00:00:00Z", window_end_utc=window_end,
        feed="sip", bars=bars,
    )


_SYN_AS_OF = _BASE + 7 * _DAY  # 2026-01-08 -- one session after the last CORE (2026-01-07) bar


def _by_price(bands: list[dict]) -> dict[float, dict]:
    return {b["price_low"]: b for b in bands}


# --- Band clustering + quality scoring: exact values on the synthetic fixture -----------------


def test_synthetic_fixture_resistance_bands_exact_values(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_synthetic(store)
    result = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)

    assert result["no_bar_series_for_symbol"] is False
    assert result["basis_as_of"] == "2026-01-07T00:00:00.000000Z"

    resistance = [b for b in result["bands"] if b["side"] == RESISTANCE]
    assert len(resistance) == CONFIG.tradability_band_cap_per_side == 5
    by_price = _by_price(resistance)
    assert set(by_price) == {250.0, 200.0, 400.0, 500.0, 105.0}

    # Served order is already descending by quality score (side, then -score, then price).
    assert [b["price_low"] for b in resistance] == [250.0, 200.0, 400.0, 500.0, 105.0]

    # Band @250: the ENGINEERED 2-member band (a real swing-pivot + prior-period-extreme
    # coincidence) -- breadth=1 (both members are "1d"), touch_total=2 (touch_count 1 each),
    # round_number=True (250 is an exact multiple of the 50-point increment), and an INHERITED
    # class (a genuine class-C zone exists at this exact price -- never re-graded here).
    band_250 = by_price[250.0]
    assert band_250["price_high"] == 250.0
    assert band_250["member_count"] == 2
    assert {m["type"] for m in band_250["members"]} == {"prior-period-extreme", "swing-pivot"}
    assert band_250["round_number"] is True
    assert band_250["class"] == "C"
    assert band_250["quality_score"] == pytest.approx(10 * 1 + 2 * 2 + 20 * 1 + 15 * (4 / 7))

    # Bands @200/@400/@500: true singletons (no swing-pivot coincidence at these prices) --
    # round_number=True (each an exact multiple of 50) but class=None: NO confluence zone
    # overlaps a lone level with no confluence partner (levels.py's own honest absence,
    # never re-graded/defaulted here).
    for price, day_index in ((200.0, 2), (400.0, 1), (500.0, 0)):
        band = by_price[price]
        assert band["price_high"] == price
        assert band["member_count"] == 1
        assert band["round_number"] is True
        assert band["class"] is None
        expected = 10 * 1 + 2 * 1 + 20 * 1 + 15 * ((day_index + 1) / 7)
        assert band["quality_score"] == pytest.approx(expected)

    # Band @105 (day 6's own high): singleton, NOT a round number (105 is 5 away from the
    # nearest 50-multiple, outside the default tolerance), most recent bar (recency == 1.0).
    band_105 = by_price[105.0]
    assert band_105["member_count"] == 1
    assert band_105["round_number"] is False
    assert band_105["class"] is None
    assert band_105["quality_score"] == pytest.approx(10 * 1 + 2 * 1 + 0 + 15 * 1.0)


def test_synthetic_fixture_support_bands_exact_values(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_synthetic(store)
    result = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)

    support = [b for b in result["bands"] if b["side"] == SUPPORT]
    assert len(support) == 2  # day 6's own low (95) and close (100) -- the only two candidates
    by_price = _by_price(support)
    assert set(by_price) == {100.0, 95.0}
    assert [b["price_low"] for b in support] == [100.0, 95.0]  # already served by descending score

    # 100 == current_price itself (side classification is price <= current_price -> support) AND
    # an exact multiple of 50 -- the highest-scoring band in the whole fixture.
    band_100 = by_price[100.0]
    assert band_100["round_number"] is True
    assert band_100["class"] is None
    assert band_100["quality_score"] == pytest.approx(10 * 1 + 2 * 1 + 20 * 1 + 15 * 1.0)
    assert band_100["quality_score"] == 47.0

    band_95 = by_price[95.0]
    assert band_95["round_number"] is False
    assert band_95["quality_score"] == pytest.approx(10 * 1 + 2 * 1 + 0 + 15 * 1.0)
    assert band_95["quality_score"] == 27.0

    # current_price == 100.0 is itself in the SUPPORT bucket (side is `price <= current_price`,
    # never a fabricated third "at the price" side) -- the class-A/B/C "side" concept stays binary.
    assert band_100["price_high"] == 100.0


# --- Top-K-per-side capping -----------------------------------------------------------------


def test_band_cap_per_side_drops_lower_scoring_bands(tmp_path):
    """The SAME synthetic fixture with ``tradability_band_cap_per_side=3`` keeps only the THREE
    highest-scoring resistance bands (250, 200, 400) and drops the two lowest (500, 105) -- a
    direct proof the cap is enforced by SCORE rank, not by insertion/price order (500 > 105 in
    price, yet 500 survives and 105 does not; both are dropped to make room for 400, whose SCORE
    beats both)."""
    store = BarStore(tmp_path / "bars")
    _seed_synthetic(store)
    capped_config = Config(tradability_band_cap_per_side=3)
    result = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, capped_config)

    resistance = [b for b in result["bands"] if b["side"] == RESISTANCE]
    assert len(resistance) == 3
    assert [b["price_low"] for b in resistance] == [250.0, 200.0, 400.0]

    # The support side (only 2 real candidates) is unaffected by a cap of 3 -- never padded.
    support = [b for b in result["bands"] if b["side"] == SUPPORT]
    assert len(support) == 2


# --- Determinism + no-lookahead ---------------------------------------------------------------


def test_repeat_call_determinism(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_synthetic(store)
    first = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
    second = compute_tradability(BarStore(tmp_path / "bars"), _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert len(first["bands"]) >= 1, "the proof must exercise at least one real band"


def test_no_lookahead_shifting_as_of_within_the_same_session_is_unchanged(tmp_path):
    """Every instant inside the SAME calendar session (2026-01-08) must resolve to the identical
    basis and produce byte-identical output -- the morning-markup as-of resolution keys off the
    calendar DATE, never the clock time within it."""
    store = BarStore(tmp_path / "bars")
    _seed_synthetic(store)
    early = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)  # 2026-01-08T00:00:00Z
    late = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF + 23 * 3600, CONFIG)  # same day, 23:00
    assert json.dumps(early, sort_keys=True) == json.dumps(late, sort_keys=True)


def test_no_lookahead_a_later_session_shifts_the_basis_forward(tmp_path):
    """A request one session later (2026-01-09), against a store that ALSO has the eighth
    (2026-01-08) bar recorded, resolves its basis to 2026-01-08 (the NEW prior session), never
    staying pinned to 2026-01-07 -- proves the resolver tracks the requested session, not a
    stale/cached prior answer."""
    store = BarStore(tmp_path / "bars")
    _seed_synthetic(store, num_days=8)
    next_session = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF + _DAY, CONFIG)
    assert next_session["basis_as_of"] == "2026-01-08T00:00:00.000000Z"


def test_no_lookahead_bars_after_the_basis_never_affect_the_result(tmp_path):
    """The definitive proof (the ``test_levels.py`` lookahead-free precedent): a store holding
    ONLY the seven CORE bars (through the resolved basis) produces output IDENTICAL to a store
    that ALSO holds the eighth bar (2026-01-08, dated strictly on/after the requested session,
    with unmissable canary prices 999/998/998.5) -- the later bar can never leak into a request
    still resolved to the day-6 basis. Both series are recorded as a SINGLE ``record()`` call each
    (``_seed_synthetic``'s own discipline) so this is a true prefix-truncation, not two
    independently-selected series."""
    full_store = BarStore(tmp_path / "full")
    _seed_synthetic(full_store, num_days=8)
    truncated_store = BarStore(tmp_path / "truncated")
    _seed_synthetic(truncated_store, num_days=7)

    full_result = compute_tradability(full_store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
    truncated_result = compute_tradability(truncated_store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
    assert json.dumps(full_result, sort_keys=True) == json.dumps(truncated_result, sort_keys=True)
    assert not any(m["price"] == 999.0 for b in full_result["bands"] for m in b["members"])


# --- Honest, distinct failure states (never one bare ambiguous empty array) ------------------


def test_symbol_with_no_recorded_bar_series_is_a_distinct_honest_state(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_synthetic(store)  # records ONLY `_SYN_SYMBOL` -- never the queried symbol below
    result = compute_tradability(store, "NEVER-RECORDED", _SYN_AS_OF, CONFIG)
    assert result == {"bands": [], "no_bar_series_for_symbol": True, "basis_as_of": None}


def test_empty_bar_store_is_no_bar_series_for_symbol(tmp_path):
    store = BarStore(tmp_path / "bars")  # never recorded anything at all
    result = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
    assert result == {"bands": [], "no_bar_series_for_symbol": True, "basis_as_of": None}


def test_series_exist_but_none_is_daily_is_honest_empty_not_no_bar_series(tmp_path):
    """A symbol WITH a recorded (non-daily) series is a DISTINCT honest state from "no series at
    all": ``no_bar_series_for_symbol`` mirrors ``levels.py``'s exact meaning (true only when
    NOTHING is recorded for the symbol), so this case reports ``False`` with an honest empty map
    -- never a fabricated basis resolved from the wrong timeframe."""
    store = BarStore(tmp_path / "bars")
    store.record(
        symbol=_SYN_SYMBOL, timeframe="1h", window_start_utc="2026-01-01T00:00:00Z",
        window_end_utc="2026-01-02T00:00:00Z", feed="sip",
        bars=[RawBar(_SYN_SYMBOL, "1h", _BASE, 100, 101, 99, 100.5, 1_000)],
    )
    result = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
    assert result == {"bands": [], "no_bar_series_for_symbol": False, "basis_as_of": None}


def test_as_of_before_any_prior_session_is_honest_empty(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_synthetic(store)
    result = compute_tradability(store, _SYN_SYMBOL, _BASE - 1, CONFIG)  # before the series starts
    assert result == {"bands": [], "no_bar_series_for_symbol": False, "basis_as_of": None}


def test_as_of_on_the_first_recorded_session_has_no_prior_session_yet(tmp_path):
    """``as_of`` inside day 0's OWN session: no session precedes it in the store, so no basis
    resolves at all -- distinct from (but as honest as) the ``no_bar_series_for_symbol`` state."""
    store = BarStore(tmp_path / "bars")
    _seed_synthetic(store)
    result = compute_tradability(store, _SYN_SYMBOL, _BASE, CONFIG)
    assert result == {"bands": [], "no_bar_series_for_symbol": False, "basis_as_of": None}


def test_a_one_bar_recording_created_last_does_not_pin_the_basis(tmp_path):
    """The reported /structure symptom at its source: a 1-bar daily recording written AFTER a full
    history used to be the ONLY daily series read, so ``basis_as_of`` froze on that single bar's
    session and the tradable map was identical for every ``as_of`` the operator loaded. Every
    recording now contributes to one merged daily view, so the basis tracks the as-of date again."""
    store = BarStore(tmp_path / "bars")
    _seed_synthetic(store)
    # The sliver: one bar on a session BEFORE the synthetic history, recorded LAST.
    store.record(
        symbol=_SYN_SYMBOL, timeframe="1d",
        window_start_utc="2025-12-30T00:00:00Z", window_end_utc="2025-12-30T00:00:00Z",
        feed="sip",
        bars=[RawBar(_SYN_SYMBOL, "1d", _BASE - 2 * _DAY, 145.0, 150.0, 140.0, 145.0, 1_000)],
    )

    # Three as-of instants, three different prior sessions -- the property that was broken.
    bases = [
        compute_tradability(store, _SYN_SYMBOL, _BASE + n * _DAY, CONFIG)["basis_as_of"]
        for n in (4, 6, 7)
    ]
    assert bases == [
        "2026-01-04T00:00:00.000000Z",
        "2026-01-06T00:00:00.000000Z",
        "2026-01-07T00:00:00.000000Z",
    ], "the basis must advance with the requested as-of date, not pin to the newest recording"

    # And the map itself moves with it -- not just the marker.
    early = compute_tradability(store, _SYN_SYMBOL, _BASE + 4 * _DAY, CONFIG)
    late = compute_tradability(store, _SYN_SYMBOL, _SYN_AS_OF, CONFIG)
    assert early["bands"] != late["bands"]

    # The sliver's own session is still reachable as a basis -- it was merged in, not discarded.
    assert (
        compute_tradability(store, _SYN_SYMBOL, _BASE - _DAY, CONFIG)["basis_as_of"]
        == "2025-12-30T00:00:00.000000Z"
    )


# --- No magic numbers: every tradability parameter is config-sourced -------------------------


def test_tradability_parameters_are_config_sourced_no_magic_numbers():
    assert isinstance(CONFIG.tradability_band_cap_per_side, int)
    assert 1 <= CONFIG.tradability_band_cap_per_side <= 5  # goal.md: "K <= 5"
    assert isinstance(CONFIG.tradability_band_width_bps, float) and CONFIG.tradability_band_width_bps > 0
    assert isinstance(CONFIG.tradability_quality_weights, dict)
    assert set(CONFIG.tradability_quality_weights) == {
        "timeframe_breadth", "touch_count", "recency", "round_number",
    }
    assert all(isinstance(w, float) and w >= 0 for w in CONFIG.tradability_quality_weights.values())
    assert isinstance(CONFIG.tradability_round_number_increment, float)
    assert CONFIG.tradability_round_number_increment > 0
    assert isinstance(CONFIG.tradability_round_number_tolerance_bps, float)
    assert CONFIG.tradability_round_number_tolerance_bps > 0

    from app.research import tradability as tradability_module

    src = inspect.getsource(tradability_module)
    assert "config.tradability_band_cap_per_side" in src
    assert "config.tradability_band_width_bps" in src
    assert "config.tradability_quality_weights" in src
    assert "config.tradability_round_number_increment" in src
    assert "config.tradability_round_number_tolerance_bps" in src


def test_tradability_config_fields_are_excluded_from_config_fingerprint():
    assert CONFIG.config_fingerprint() == "4d665603569b9dbf"
    assert Config(tradability_band_cap_per_side=1).config_fingerprint() == CONFIG.config_fingerprint()
    assert Config(tradability_band_width_bps=999.0).config_fingerprint() == CONFIG.config_fingerprint()
    assert (
        Config(tradability_quality_weights={"timeframe_breadth": 1.0}).config_fingerprint()
        == CONFIG.config_fingerprint()
    )
    assert (
        Config(tradability_round_number_increment=1.0).config_fingerprint() == CONFIG.config_fingerprint()
    )
    assert (
        Config(tradability_round_number_tolerance_bps=1.0).config_fingerprint()
        == CONFIG.config_fingerprint()
    )
    # ...while a real classifier threshold still moves it (the counter-test).
    assert Config(min_trade_speed=0.51).config_fingerprint() != CONFIG.config_fingerprint()


# --- basis_day_key: the arm memo's day-key contract (goal-fast_wall J-03) ----------------------


def test_basis_day_key_same_utc_date_is_stable():
    """TC-3: two ``as_of_epoch`` values on the SAME UTC calendar date resolve to the identical key
    -- reusing ``_session_date`` (never a second date derivation), mirroring
    ``test_no_lookahead_shifting_as_of_within_the_same_session_is_unchanged``'s own premise."""
    early = _SYN_AS_OF  # 2026-01-08T00:00:00Z
    late = _SYN_AS_OF + 23 * 3600  # same UTC date, 23:00
    assert basis_day_key(early) == basis_day_key(late)


def test_basis_day_key_differs_across_a_utc_midnight_boundary():
    """TC-4: an ``as_of_epoch`` strictly before, and one strictly after, a UTC midnight boundary
    resolve to DIFFERENT keys -- the property ``backtests.py``'s ``_StructureArmMemo`` relies on
    to memoize ``tradability_at`` once per real UTC session date instead of per confirming tick."""
    just_before_midnight = _SYN_AS_OF - 1.0  # 2026-01-07T23:59:59Z
    just_after_midnight = _SYN_AS_OF + 1.0  # 2026-01-08T00:00:01Z
    assert basis_day_key(just_before_midnight) != basis_day_key(just_after_midnight)


def test_basis_day_key_matches_the_date_boundary_compute_tradability_itself_shifts_basis_across(tmp_path):
    """Direct-computation cross-check (never hand-waved): the SAME midnight boundary where
    ``basis_day_key`` changes is really where ``compute_tradability`` itself resolves a DIFFERENT
    ``basis_as_of`` (the existing ``test_no_lookahead_a_later_session_shifts_the_basis_forward``
    fixture, reused) -- proving the memo's cache key genuinely tracks the value it stands in for."""
    store = BarStore(tmp_path / "bars")
    _seed_synthetic(store, num_days=8)
    boundary = _SYN_AS_OF + _DAY  # 2026-01-09T00:00:00Z -- the day8/day9 boundary this fixture uses

    before_key = basis_day_key(boundary - 1.0)
    after_key = basis_day_key(boundary + 1.0)
    assert before_key != after_key

    before_map = compute_tradability(store, _SYN_SYMBOL, boundary - 1.0, CONFIG)
    after_map = compute_tradability(store, _SYN_SYMBOL, boundary + 1.0, CONFIG)
    assert before_map["basis_as_of"] != after_map["basis_as_of"]



# --- "Lens, not a second engine": tradability.py never re-detects structure ------------------


def test_tradability_module_is_a_lens_never_a_second_levels_engine():
    """Static-analysis guard for the era-5B critical anti-goal: ``tradability.py`` must consume
    ``compute_levels`` output verbatim -- it must never import or CALL a pivot/prior-period
    detection internal, and it must never read ``levels.py``'s frozen ``sr_pivot_lookback`` /
    ``sr_touch_tolerance_bps`` parameters off ``config``. Checks actual imports/calls/attribute
    reads specifically (never a bare substring match), so this survives the module's own docstring
    prose NAMING those same precedents when explaining a mirrored technique or tie-break."""
    from app.research import tradability as tradability_module

    src = inspect.getsource(tradability_module)
    assert "compute_levels(" in src

    import_lines = [
        line.strip() for line in src.splitlines() if line.strip().startswith(("import ", "from "))
    ]
    levels_imports = [line for line in import_lines if " .levels " in line or line.endswith(".levels")]
    assert levels_imports == ["from .levels import compute_levels"], (
        f"the ONLY symbol imported from levels.py must be compute_levels, got {levels_imports!r}"
    )

    # No CALL to a levels.py pivot/extreme/selection internal, and no READ of a frozen levels.py
    # config threshold, appears anywhere in the module body.
    for forbidden_call in (
        "_swing_pivots(", "_prior_period_extremes(", "_bars_as_of(",
        "_select_one_series_per_timeframe(", "_cluster_levels(", "_grade_zone(",
    ):
        assert forbidden_call not in src, f"tradability.py must not call levels.py internal {forbidden_call!r}"
    for forbidden_config_read in ("config.sr_pivot_lookback", "config.sr_touch_tolerance_bps"):
        assert forbidden_config_read not in src, (
            f"tradability.py must not read the frozen levels.py threshold {forbidden_config_read!r}"
        )


# --- The committed real AAPL fixture: J-01's pinned acceptance -------------------------------


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

# The multi-timeframe committed slices (real, frozen live-fetched Yahoo bars truncated to the
# 2026-06-18 basis) that -- ALONGSIDE the daily fixture -- reproduce the exact multi-timeframe level
# density of the live ``.data/bars`` AAPL store the phase spec's NOTES section names as the
# reference (~1,000 intraday levels dominated by the 5m series). Committed the SAME way as
# ``AAPL_DAILY_FIXTURE`` (real, frozen, per the ``test_levels_api.py`` committed-real-fixture
# precedent) -- never fabricated synthetic prices.
AAPL_MULTITIMEFRAME_FIXTURES = (
    AAPL_DAILY_FIXTURE,
    "AAPL_1h_20260601_20260618.json",
    "AAPL_4h_20260601_20260618.json",
    "AAPL_5m_20260601_20260618.json",
    "AAPL_1w_20260601_20260615.json",
)


def _seed_aapl_multitimeframe(store: BarStore) -> None:
    for name in AAPL_MULTITIMEFRAME_FIXTURES:
        _seed_yahoo_fixture(store, _load_yahoo_fixture(name))


def test_aapl_pinned_resistance_band_top2_with_round_number_and_inherited_class(tmp_path):
    """J-01's headline acceptance: AAPL as of the 2026-06-22 session, morning-markup basis = the
    2026-06-18 close. The real fixture (frozen live-fetched Yahoo daily bars, 2026-01-01 through
    2026-06-26) contains the exact pinned rejection cluster goal.md cites (300.75 on 06-09, 300.48
    on 06-16, 302.07 on 06-17, 300.57 on 06-18) -- all four real highs join ONE band."""
    store = BarStore(tmp_path / "bars")
    _seed_yahoo_fixture(store, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))

    as_of = _epoch("2026-06-22T15:00:00Z")  # inside the 2026-06-22 session
    result = compute_tradability(store, "AAPL", as_of, CONFIG)
    assert result["no_bar_series_for_symbol"] is False
    assert result["basis_as_of"] == "2026-06-18T04:00:00.000000Z"

    bands = result["bands"]
    assert len(bands) == 10, "<=10 bands total (the headline distillation)"
    resistance = [b for b in bands if b["side"] == RESISTANCE]
    support = [b for b in bands if b["side"] == SUPPORT]
    assert len(resistance) == 5 and len(resistance) <= CONFIG.tradability_band_cap_per_side
    assert len(support) == 5 and len(support) <= CONFIG.tradability_band_cap_per_side

    # Resistance bands are served in descending quality-score order (side, then -score, then
    # price) -- so the pinned band ranking IN the top 2 is simply "appears at index 0 or 1".
    pinned_index = next(
        i for i, b in enumerate(resistance)
        if b["price_low"] <= 300.48 and b["price_high"] >= 302.07
    )
    assert pinned_index in (0, 1), "the pinned resistance band must rank in the top 2 by quality score"
    assert pinned_index == 0, "verified by direct computation: it is in fact the single best band"

    pinned = resistance[pinned_index]
    assert pinned["price_low"] == 300.2300109863281
    assert pinned["price_high"] == 302.25
    assert pinned["price_low"] <= 300.48 <= pinned["price_high"]
    assert pinned["price_low"] <= 302.07 <= pinned["price_high"]
    assert pinned["round_number"] is True, "300 must be flagged as a round number"
    assert pinned["class"] == "C", "an inherited class must be present, never null, for this band"
    assert pinned["quality_score"] == pytest.approx(123.0)

    member_prices = {m["price"] for m in pinned["members"]}
    for real_rejection_high in (300.75, 300.4800109863281, 302.07000732421875, 300.57000732421875):
        assert real_rejection_high in member_prices, f"{real_rejection_high} must be a member of the pinned band"

    # No band anywhere is fabricated: every price is a REAL member level, never synthesized.
    for band in bands:
        assert band["member_count"] == len(band["members"]) >= 1


def test_aapl_map_derives_from_no_bar_newer_than_the_2026_06_18_close(tmp_path):
    """No-lookahead, proven the ``test_levels.py`` way: a store holding bars ONLY through the
    2026-06-18 close produces output IDENTICAL to the full fixture (which also holds real bars
    through 2026-06-26, well past the pinned session) at the SAME ``as_of`` inside 2026-06-22."""
    fixture = _load_yahoo_fixture(AAPL_DAILY_FIXTURE)
    as_of = _epoch("2026-06-22T15:00:00Z")

    full_store = BarStore(tmp_path / "full")
    _seed_yahoo_fixture(full_store, fixture)
    full_result = compute_tradability(full_store, "AAPL", as_of, CONFIG)

    cutoff = datetime(2026, 6, 18, tzinfo=timezone.utc).date()
    truncated_bars = [
        b for b in fixture["bars"]
        if datetime.fromtimestamp(b["epoch"], tz=timezone.utc).date() <= cutoff
    ]
    assert len(truncated_bars) < len(fixture["bars"]), "the truncation must actually drop real bars"
    truncated_fixture = {**fixture, "bars": truncated_bars, "end": "2026-06-18T23:59:59Z"}
    truncated_store = BarStore(tmp_path / "truncated")
    _seed_yahoo_fixture(truncated_store, truncated_fixture)
    truncated_result = compute_tradability(truncated_store, "AAPL", as_of, CONFIG)

    assert json.dumps(full_result, sort_keys=True) == json.dumps(truncated_result, sort_keys=True)

    # Every basis/member timestamp this run touches resolves no later than the 2026-06-18 close.
    assert full_result["basis_as_of"] == "2026-06-18T04:00:00.000000Z"
    assert _epoch(full_result["basis_as_of"]) <= _epoch("2026-06-18T23:59:59Z")


def test_aapl_repeat_call_determinism(tmp_path):
    store = BarStore(tmp_path / "bars")
    _seed_yahoo_fixture(store, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    as_of = _epoch("2026-06-22T15:00:00Z")
    first = compute_tradability(store, "AAPL", as_of, CONFIG)
    second = compute_tradability(BarStore(tmp_path / "bars"), "AAPL", as_of, CONFIG)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_aapl_frozen_levels_output_is_byte_identical_to_before(tmp_path):
    """The critical single-source-of-truth guard: computing the tradable map must not perturb
    ``compute_levels``' own output on the SAME store/as_of -- ``tradability.py`` only READS it."""
    from app.research.levels import compute_levels

    store = BarStore(tmp_path / "bars")
    _seed_yahoo_fixture(store, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
    as_of = _epoch("2026-06-18T04:00:00Z")

    before = compute_levels(store, "AAPL", as_of, CONFIG)
    compute_tradability(store, "AAPL", _epoch("2026-06-22T15:00:00Z"), CONFIG)
    after = compute_levels(store, "AAPL", as_of, CONFIG)
    assert json.dumps(before, sort_keys=True) == json.dumps(after, sort_keys=True)


# --- Multi-timeframe regression: the wall must survive realistic intraday level density ---------


def test_aapl_pinned_band_ranks_top2_under_realistic_multitimeframe_density(tmp_path):
    """The regression the daily-only fixture could NOT surface (the reviewer's CRITICAL): seeded
    with the FULL multi-timeframe density (1d + 1h + 4h + 5m + 1w -- ~1,000 intraday levels, the
    live ``.data/bars`` AAPL state), the pinned 300.48-302.07 wall must STILL rank in the top 2
    resistance bands. It does because the quality score's touch factor is the DAILY touch count, not
    a sum across every timeframe: the dozens of shallow intraday touches a band near the current
    price accumulates would otherwise let raw intraday VOLUME (a 5m/1h noise cluster) outscore a
    genuine multi-day rejection wall -- exactly what pushed this band to rank 7th-of-9 (excluded
    from the served top-5) under the original all-timeframe sum. This test fails if that factor ever
    reverts."""
    store = BarStore(tmp_path / "bars")
    _seed_aapl_multitimeframe(store)

    as_of = _epoch("2026-06-22T15:00:00Z")  # inside the 2026-06-22 session
    result = compute_tradability(store, "AAPL", as_of, CONFIG)
    assert result["no_bar_series_for_symbol"] is False
    assert result["basis_as_of"] == "2026-06-18T04:00:00.000000Z"

    bands = result["bands"]
    assert len(bands) == 10, "<=10 bands total -- the headline distillation holds under real density"
    resistance = [b for b in bands if b["side"] == RESISTANCE]
    support = [b for b in bands if b["side"] == SUPPORT]
    assert len(resistance) == 5 and len(support) == 5

    # Resistance is served descending by quality score, so "top 2" == index 0 or 1.
    pinned_index = next(
        i for i, b in enumerate(resistance)
        if b["price_low"] <= 300.48 and b["price_high"] >= 302.07
    )
    assert pinned_index in (0, 1), "the pinned wall must rank top-2 under realistic multi-timeframe density"
    assert pinned_index == 0, "verified by direct computation: it is in fact the single best band"

    pinned = resistance[pinned_index]
    assert pinned["price_low"] <= 300.48 <= pinned["price_high"]
    assert pinned["price_low"] <= 302.07 <= pinned["price_high"]
    assert pinned["round_number"] is True, "300 must be flagged as a round number"
    # The wall now overlaps a genuine CROSS-timeframe confluence zone (intraday members joined the
    # daily-only zone), so it inherits the highest grade -- projected from levels.py, never re-graded.
    assert pinned["class"] == "A"

    # It is a GENUINE multi-timeframe band (real intraday members joined it) and the DAILY series
    # rejected it dozens of times -- the exact signal the score keys off.
    pinned_timeframes = {member["timeframe"] for member in pinned["members"]}
    assert "1d" in pinned_timeframes and len(pinned_timeframes) >= 2, "the band must span multiple timeframes"
    pinned_daily_touch = sum(m["touch_count"] for m in pinned["members"] if m["timeframe"] == "1d")
    assert pinned_daily_touch == 39
    # score == breadth*10 + daily_touch*2 + recency(1.0)*15 + round(1)*20 == 40 + 78 + 15 + 20.
    assert pinned["quality_score"] == pytest.approx(153.0)

    # THE REGRESSION GUARD: at least one OTHER served resistance band carries far MORE raw
    # (all-timeframe) touch volume than the pinned wall, yet still ranks strictly BELOW it -- the
    # direct proof the score is driven by DAILY touches, not summed intraday volume. Under the old
    # all-timeframe sum such a band (e.g. the 309-311 5m/1h cluster, ~2,300 summed touches vs the
    # wall's ~95) outscored the wall and pushed it out of the top 2 entirely.
    def summed_touch(band: dict) -> int:
        return sum(member["touch_count"] for member in band["members"])

    pinned_summed_touch = summed_touch(pinned)
    louder_but_lower_ranked = [
        band for rank, band in enumerate(resistance)
        if rank > pinned_index and summed_touch(band) > 3 * pinned_summed_touch
    ]
    assert louder_but_lower_ranked, (
        "expected a higher-raw-touch intraday-heavy band ranked BELOW the pinned wall (the "
        "daily-touch-count guard); none found -- has scoring reverted to an all-timeframe sum?"
    )

    # No band is fabricated: every price is a REAL member level.
    for band in bands:
        assert band["member_count"] == len(band["members"]) >= 1


# --- _ZoneClassIndex: the binary-search class-inheritance path ≡ the reference walk ---------------


def test_zone_class_index_gap_case_a_band_between_two_members_of_an_overlapping_zone():
    """A band whose RANGE overlaps a zone's [min, max] span while containing NO member is NOT an
    overlap: class inheritance requires an actual member level inside the band (the reference's
    per-member walk), never mere interval intersection -- the exact case a min/max-only index
    would silently get wrong."""
    from app.research.tradability import _best_zone_class, _ZoneClassIndex

    zones = [{"levels": [{"price": 100.0}, {"price": 100.2}], "class": "A", "score": 10.0}]
    index = _ZoneClassIndex(zones)
    # Falls strictly in the gap between the two members: no inheritance.
    assert _best_zone_class(zones, 100.05, 100.15) is None
    assert index.best_class(100.05, 100.15) is None
    # Contains a member (edge-inclusive both ways): inherits.
    assert _best_zone_class(zones, 100.05, 100.2) == "A"
    assert index.best_class(100.05, 100.2) == "A"
    assert _best_zone_class(zones, 100.0, 100.15) == "A"
    assert index.best_class(100.0, 100.15) == "A"


def test_zone_class_index_fuzz_against_the_reference_walk():
    """Seeded fuzz: `_ZoneClassIndex.best_class` ≡ `_best_zone_class` over random zones (mixed
    classes/scores, cent-quantized member prices so band edges land EXACTLY on members) and random
    bands (including empty ranges, gap-straddling ranges, and whole-corpus-spanning ranges)."""
    import random

    from app.research.tradability import _best_zone_class, _ZoneClassIndex

    rng = random.Random(5723)
    checked_inherited = 0
    for _ in range(60):
        zones = []
        for _z in range(rng.randrange(0, 12)):
            members = [
                {"price": round(rng.uniform(90.0, 110.0), 2)}
                for _ in range(rng.randrange(2, 8))
            ]
            zones.append(
                {
                    "levels": members,
                    "class": rng.choice(["A", "B", "C"]),
                    "score": round(rng.uniform(1.0, 50.0), 4),
                }
            )
        index = _ZoneClassIndex(zones)
        for _q in range(40):
            if rng.random() < 0.4 and zones:
                # Anchor the band's edges ON real member prices (exact-boundary cases).
                zone = rng.choice(zones)
                member_price = rng.choice(zone["levels"])["price"]
                low = member_price - rng.choice([0.0, 0.01, 0.5])
                high = member_price + rng.choice([0.0, 0.01, 0.5])
            else:
                low = round(rng.uniform(88.0, 112.0), 2)
                high = round(low + rng.uniform(0.0, 4.0), 2)
            want = _best_zone_class(zones, low, high)
            assert index.best_class(low, high) == want, f"disagreement at [{low}, {high}]"
            if want is not None:
                checked_inherited += 1
    assert checked_inherited > 0, "the fuzz must exercise real inheritance, not only misses"
