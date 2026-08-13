"""Guards for ``desk_playbook_context`` — the read-side band-context lens joining every recorded
playbook signal to the desk's own tradable band map.

Every guard here carries a seeded counter-test where the guard is structural (a lint that cannot
fail proves nothing), and every honesty property the module claims in prose is pinned by a test
that would fail if the prose became untrue:

  * the geometry is deterministic and its threshold boundary is INCLUSIVE at exactly 70.0 bps;
  * ``not_computed`` (no map cached yet) and ``no_band_context`` (a map that puts no band near the
    price) are DISTINCT states, never conflated;
  * a serving path NEVER computes a map, and NEVER writes to the playbook store;
  * baseline-anchor attribution is positional AND verified, and refuses wholesale on any
    disagreement rather than pairing an anchor with the wrong symbol's wall;
  * the recorded corpus is never modified by reading it;
  * ``compute_playbook``'s own walk still makes zero structural calls (TC-7 lives in
    ``test_desk_playbook_guards.py`` and must stay green; the import-direction guard below is its
    structural companion).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.research.desk_playbook import PlaybookStore
from app.research.desk_playbook_context import (
    AT_WALL,
    CONTEXT_REGISTER,
    LOCATED,
    NO_BAND_CONTEXT,
    NOT_COMPUTED,
    NO_WALL_AHEAD,
    NO_WALL_BEHIND,
    OFF_WALL,
    PLAYBOOK_CONTEXT_BACKING_BUCKETS,
    PLAYBOOK_CONTEXT_NEAR_BAND_BPS,
    PLAYBOOK_CONTEXT_ROOM_BUCKETS,
    PLAYBOOK_CONTEXT_ROOM_R_EDGES,
    ROOM_1R_2R,
    ROOM_GE_2R,
    ROOM_LT_1R,
    ROOM_UNMEASURED,
    PlaybookContextCache,
    _attribute_anchors,
    _backing_bucket,
    _band_distance_bps,
    _bracket,
    _risk_bps,
    _room_bucket,
    band_context_block,
    context_for_record,
    playbook_context_cache_key,
    record_band_context,
    record_map_requests,
    resolve_playbook_context_cache_db_path,
)
from app.research.desk_routes import get_playbook_context_cache, get_playbook_store
from test_copy_discipline import find_violations

RESEARCH_DIR = Path(__file__).resolve().parents[1] / "app" / "research"


# --- fixtures -------------------------------------------------------------------------------------


def _band(side, low, high, *, klass="B", quality=1.0, round_number=False, members=2):
    return {
        "side": side,
        "price_low": low,
        "price_high": high,
        "class": klass,
        "quality_score": quality,
        "round_number": round_number,
        "member_count": members,
        "members": [{"price": low, "timeframe": "1d", "type": "swing-pivot"}],
    }


def _map(bands, basis="2026-08-06T04:00:00.000000Z"):
    return {"bands": bands, "no_bar_series_for_symbol": False, "basis_as_of": basis}


class _StubResolver:
    """A resolver with a fixed answer per symbol — the geometry tests need no store at all.
    ``None`` models the lookup-only miss (the ``not_computed`` state)."""

    def __init__(self, maps: dict):
        self.maps = maps
        self.calls: list[tuple] = []

    def resolve(self, symbol, epoch):
        self.calls.append((symbol, epoch))
        return self.maps.get(symbol)

    def map_key_for_basis_day(self, symbol, basis_day):
        return f"stub:{symbol}:{basis_day}"

    def map_key(self, symbol, epoch):
        return f"stub:{symbol}"


def _forward_leaf(close_price: float) -> dict:
    """The subset of a ``_measure_from`` leaf this module actually reads."""
    return {
        "at_utc": "2026-08-07T16:07:00.000000Z",
        "entry_price": 100.0,
        "entry_kind": "level",
        "horizons": {},
        "close_price": close_price,
        "to_close_pct": 0.0,
        "minutes_to_close": 100,
    }


def _signal(symbol, setup_id, side, entry, close_price, *, ts="2026-08-07T16:05:00.000000Z"):
    return {
        "symbol": symbol,
        "setup_id": setup_id,
        "side": side,
        "trigger_ts": ts,
        "trigger_price": entry,
        "entry": entry,
        "entry_kind": "level",
        "invalidation_price": entry - 1.0,
        "forward": _forward_leaf(close_price),
    }


def _anchor(entry_price, close_price, *, at="2026-08-07T15:17:00.000000Z"):
    return {
        "at_utc": at,
        "entry_price": entry_price,
        "entry_kind": "close",
        "horizons": {},
        "close_price": close_price,
        "to_close_pct": 0.0,
        "minutes_to_close": 150,
    }


def _record(signals, anchors=None, *, record_id="playbook-2026-08-07-testrecord"):
    return {
        "id": record_id,
        "session_date": "2026-08-07",
        "playbook_input_signature": "sig-abc",
        "payload_version": 3,
        "recorded_at": "2026-08-07T22:00:00.000000Z",
        "signals": signals,
        "absences": [],
        "diagnostics": [],
        "baseline_anchors": anchors or {},
        "summary": {},
        "signals_beyond_cap": {},
    }


# --- the geometry ---------------------------------------------------------------------------------


def test_a_price_inside_a_band_is_zero_bps_at_both_edges_inclusive():
    """Inside is a REAL measured zero, not an absence — and an entry sitting exactly ON an edge is
    inside, never a wall a hair's breadth away."""
    band = _band("support", 100.0, 102.0)
    for price in (100.0, 101.0, 102.0):  # both edges inclusive
        assert _band_distance_bps(band, price) == 0.0


def test_distance_is_measured_to_the_nearest_edge_in_bps_of_the_price():
    band = _band("resistance", 110.0, 112.0)
    # 100 -> nearest edge 110: (110-100)/100 * 10_000 = 1000 bps.
    assert _band_distance_bps(band, 100.0) == pytest.approx(1000.0)
    # 112.56 -> nearest edge 112: (0.56/112.56)*10_000 ~= 49.75 bps.
    assert _band_distance_bps(band, 112.56) == pytest.approx(0.56 / 112.56 * 10_000)


def test_the_backing_threshold_is_inclusive_at_exactly_the_registered_value():
    """The boundary is pinned so it can never drift silently: EXACTLY 70.0 bps is ``at_wall``."""
    assert PLAYBOOK_CONTEXT_NEAR_BAND_BPS == 70.0
    assert _backing_bucket(0.0) == AT_WALL
    assert _backing_bucket(69.999) == AT_WALL
    assert _backing_bucket(70.0) == AT_WALL
    assert _backing_bucket(70.001) == OFF_WALL
    assert _backing_bucket(10_000.0) == OFF_WALL
    assert _backing_bucket(None) == NO_WALL_BEHIND


def test_the_room_axis_boundaries_are_lower_inclusive_at_exactly_1r_and_2r():
    """Exactly 1.0 reads ``room_1r_2r`` and exactly 2.0 reads ``room_ge_2r`` — the two edges a
    guard pins so the book's own reward-to-risk vocabulary cannot drift."""
    assert PLAYBOOK_CONTEXT_ROOM_R_EDGES == (1.0, 2.0)
    assert _room_bucket(100.0, 0.999) == ROOM_LT_1R
    assert _room_bucket(100.0, 1.0) == ROOM_1R_2R
    assert _room_bucket(100.0, 1.999) == ROOM_1R_2R
    assert _room_bucket(100.0, 2.0) == ROOM_GE_2R
    assert _room_bucket(100.0, 30.0) == ROOM_GE_2R
    # A measured fact about the map, versus "headroom known, no risk to divide by".
    assert _room_bucket(None, None) == NO_WALL_AHEAD
    assert _room_bucket(100.0, None) == ROOM_UNMEASURED


def test_the_bracket_partitions_a_map_into_containing_below_and_above():
    """The three slots are a TOTAL, exclusive partition of the map around the entry — and the
    nearest wall on each side wins its slot regardless of arrival order."""
    inside = _band("support", 99.5, 100.5)
    near_below = _band("support", 98.0, 99.0)
    far_below = _band("support", 90.0, 91.0)
    near_above = _band("resistance", 101.0, 102.0)
    far_above = _band("resistance", 130.0, 131.0)
    bands = [far_above, near_below, inside, far_below, near_above]

    containing, below, above = _bracket(bands, 100.0)
    assert containing is inside
    assert below[0] is near_below
    assert above[0] is near_above
    # Distances are to the facing EDGE: 99.0 -> 100.0 is 100 bps; 100.0 -> 101.0 is 100 bps.
    assert below[1] == pytest.approx(100.0)
    assert above[1] == pytest.approx(100.0)
    # Arrival order cannot change any slot.
    assert _bracket(list(reversed(bands)), 100.0)[0] is inside


def test_a_wall_tie_breaks_on_class_then_quality_then_price():
    """Two walls at the SAME distance on the same side: class first, then quality, then the lower
    price — never dict order."""
    tie_b = _band("support", 98.0, 99.0, klass="B", quality=50.0)
    tie_a = _band("support", 98.0, 99.0, klass="A", quality=1.0)
    assert _bracket([tie_b, tie_a], 100.0)[1][0] is tie_a
    assert _bracket([tie_a, tie_b], 100.0)[1][0] is tie_a


def test_an_edge_touching_entry_is_containing_never_a_wall():
    """The edge is a real level: an entry exactly on it is INSIDE, and calling it a wall a hair
    away would invent a gap the map does not have."""
    band = _band("support", 99.0, 100.0)
    for price in (99.0, 100.0):
        containing, below, above = _bracket([band], price)
        assert containing is band
        assert below is None and above is None
    # A hair beyond the edge IS a wall.
    containing, below, above = _bracket([band], 100.01)
    assert containing is None and below[0] is band and above is None


def test_multi_containing_is_deterministic_even_though_a_real_map_cannot_produce_one():
    """Unreachable on a real map (same-side bands are disjoint; the two sides split around prior
    close) — pinned anyway so a hand-built map or a future band engine cannot make this depend on
    dict order."""
    weak = _band("support", 99.0, 101.0, klass="C", quality=99.0)
    strong = _band("support", 99.5, 100.5, klass="A", quality=1.0)
    assert _bracket([weak, strong], 100.0)[0] is strong
    assert _bracket([strong, weak], 100.0)[0] is strong


def test_a_class_null_band_is_still_a_band():
    """Class is a quality projection inherited from the zone engine, never a test of whether a band
    exists — an unclassified band still locates a signal."""
    unclassified = _band("support", 99.9, 100.0, klass=None)
    assert _bracket([unclassified], 100.0)[0] is unclassified
    block = band_context_block(_map([unclassified]), 100.0, "long")
    assert block["backing_bucket"] == AT_WALL
    assert block["containing_band"]["class"] is None


def test_an_event_with_no_side_is_an_honest_absence_not_a_half_frame():
    """The frame is trade-relative — which wall is behind and which is ahead is decided by the
    side. Without one there is no honest frame, only a pair of raw directions."""
    block = band_context_block(_map([_band("support", 99.0, 100.0)]), 100.0, None)
    assert block["status"] == NO_BAND_CONTEXT
    assert block["backing_bucket"] is None and block["room_bucket"] is None
    assert "no side" in block["caption"]


# --- the three states, kept distinct ---------------------------------------------------------------


def test_not_computed_and_no_band_context_are_distinct_states():
    """The single most important honesty property of this lens: "we have not computed the map yet"
    and "we computed the map and no band is near this price" are DIFFERENT facts, and conflating
    them would let an un-warmed cache masquerade as a measured absence of structure."""
    not_computed = band_context_block(None, 100.0, "long")
    assert not_computed["status"] == NOT_COMPUTED
    assert not_computed["backing_bps"] is None and not_computed["room_bucket"] is None
    assert "has not been computed" in not_computed["caption"]

    empty_map = band_context_block(_map([]), 100.0, "long")
    assert empty_map["status"] == NO_BAND_CONTEXT
    assert empty_map["backing_bps"] is None
    assert "honest absence" in empty_map["caption"]

    assert not_computed["caption"] != empty_map["caption"]


def test_a_located_signal_serves_every_disclosure_field():
    """The whole frame, verbatim: three slots, four readings, two buckets — every value a copy of
    something served, nothing derived twice."""
    containing = _band("support", 99.5, 100.2, klass="A", quality=4.25)
    floor = _band("support", 97.0, 98.0, klass="B")
    ceiling = _band("resistance", 102.0, 103.0, klass="A")
    block = band_context_block(
        _map([containing, floor, ceiling]), 100.0, "long", risk_bps=100.0, risk_source="own"
    )
    assert block["status"] == LOCATED
    assert block["containing_band"] == {
        "side": "support", "class": "A", "price_low": 99.5, "price_high": 100.2,
        "quality_score": 4.25, "round_number": False, "member_count": 2,
    }
    assert block["wall_below"]["price_high"] == 98.0
    assert block["wall_below"]["distance_bps"] == pytest.approx(200.0)
    assert block["wall_above"]["price_low"] == 102.0
    assert block["wall_above"]["distance_bps"] == pytest.approx(200.0)
    # Inside a band => backed at zero; ahead is ABOVE for a long; room is headroom over risk.
    assert block["backing_bps"] == 0.0
    assert block["headroom_bps"] == pytest.approx(200.0)
    assert block["risk_bps"] == 100.0
    assert block["risk_source"] == "own"
    assert block["room_r"] == pytest.approx(2.0)
    assert block["backing_bucket"] == AT_WALL
    assert block["room_bucket"] == ROOM_GE_2R
    assert block["basis_as_of"] == "2026-08-06T04:00:00.000000Z"
    # Each band's full member list stays with the tradable-map endpoint that owns it.
    assert "members" not in block["containing_band"]
    assert "members" not in block["wall_below"]


def test_the_cof_case_the_v1_lens_could_not_express():
    """The real 2026-08-07 COF long that motivated this frame. v1 said "support A · 0.00 · aligned"
    — true, but it never named the band and said nothing about what was overhead. The frame a
    trader actually needs: inside a class-A support, the next floor ~93 bps under it, the first
    ceiling ~110 bps over it, which is ~1.6x the trade's own 67.8 bps invalidation distance."""
    entry, invalidation = 217.635, 216.16
    bands = [
        _band("support", 217.13, 218.635, klass="A", quality=513.0),
        _band("support", 214.11, 215.60, klass="A", quality=458.9),
        _band("resistance", 220.02, 221.56, klass="A", quality=359.0),
        _band("resistance", 221.57, 223.11, klass="A", quality=273.0),
    ]
    risk = _risk_bps(entry, invalidation)
    block = band_context_block(_map(bands), entry, "long", risk_bps=risk, risk_source="own")

    assert block["containing_band"]["price_low"] == 217.13
    assert block["wall_below"]["price_high"] == 215.60
    # ~93.5 here vs ~93.4 on the live map: the fixture rounds the band edges to two decimals.
    assert block["wall_below"]["distance_bps"] == pytest.approx(93.5, abs=0.1)
    assert block["wall_above"]["price_low"] == 220.02
    assert block["wall_above"]["distance_bps"] == pytest.approx(109.6, abs=0.1)
    assert block["backing_bps"] == 0.0
    assert block["backing_bucket"] == AT_WALL
    assert risk == pytest.approx(67.8, abs=0.1)
    assert block["room_r"] == pytest.approx(1.62, abs=0.01)
    assert block["room_bucket"] == ROOM_1R_2R
    # The caption names the band, both walls, and the room -- everything v1 left unsaid.
    assert "from inside the support band 217.13–218.63" in block["caption"]
    assert "next floor 214.11–215.60" in block["caption"]
    assert "first ceiling 220.02–221.56" in block["caption"]
    assert "1.6× the 67.8 bps invalidation distance" in block["caption"]


def test_the_crm_case_where_v1_claimed_a_relationship_that_did_not_exist():
    """The real 2026-08-07 CRM long. v1 reported "support A · 288.19 · aligned" — but the nearest
    band in ANY direction was 288 bps away and the nearest resistance thousands of bps away. v2
    says plainly that the entry is inside no band, and puts the trade off_wall."""
    entry, invalidation = 192.23, 190.25
    bands = [
        _band("support", 185.40, 186.69, klass="A", quality=189.0),
        _band("support", 180.27, 181.53, klass="A", quality=216.9),
        _band("resistance", 251.70, 253.46, klass="A", quality=665.8),
    ]
    risk = _risk_bps(entry, invalidation)
    block = band_context_block(_map(bands), entry, "long", risk_bps=risk, risk_source="own")

    assert block["containing_band"] is None
    assert block["wall_below"]["price_high"] == 186.69
    assert block["backing_bps"] == pytest.approx(288.2, abs=0.1)
    assert block["backing_bucket"] == OFF_WALL          # not "aligned" with anything
    assert block["room_bucket"] == ROOM_GE_2R
    assert "inside no band on this map" in block["caption"]


def test_the_frame_mirrors_for_a_short():
    """A short leans on what is ABOVE and runs into what is BELOW — the same map read the other
    way round, with no client-side inversion anywhere."""
    containing = _band("resistance", 99.8, 100.2, klass="A")
    below = _band("support", 97.0, 98.0, klass="A")
    block = band_context_block(
        _map([containing, below]), 100.0, "short", risk_bps=100.0, risk_source="own"
    )
    assert block["backing_bps"] == 0.0
    assert block["headroom_bps"] == pytest.approx(200.0)
    assert block["room_bucket"] == ROOM_GE_2R
    above = _band("resistance", 100.5, 101.0, klass="A")
    plain = band_context_block(
        _map([above, below]), 100.0, "short", risk_bps=100.0, risk_source="own"
    )
    assert plain["backing_bps"] == pytest.approx(50.0)
    assert plain["backing_bucket"] == AT_WALL
    assert plain["headroom_bps"] == pytest.approx(200.0)


def test_risk_is_read_off_the_trades_own_recorded_invalidation():
    assert _risk_bps(100.0, 99.0) == pytest.approx(100.0)
    assert _risk_bps(100.0, 101.0) == pytest.approx(100.0)  # unsigned
    assert _risk_bps(100.0, None) is None
    assert _risk_bps(None, 99.0) is None


def test_headroom_without_a_derivable_risk_is_room_unmeasured_never_a_guess():
    block = band_context_block(
        _map([_band("resistance", 102.0, 103.0)]), 100.0, "long", risk_bps=None
    )
    assert block["status"] == LOCATED
    assert block["headroom_bps"] == pytest.approx(200.0)
    assert block["room_r"] is None
    assert block["risk_source"] is None
    assert block["room_bucket"] == ROOM_UNMEASURED
    assert "no invalidation distance is derivable" in block["caption"]


def test_a_map_with_nothing_on_one_side_reads_the_axis_absence():
    only_below = band_context_block(
        _map([_band("support", 90.0, 91.0)]), 100.0, "long", risk_bps=100.0, risk_source="own"
    )
    assert only_below["room_bucket"] == NO_WALL_AHEAD
    assert only_below["headroom_bps"] is None
    only_above = band_context_block(
        _map([_band("resistance", 110.0, 111.0)]), 100.0, "long", risk_bps=100.0, risk_source="own"
    )
    assert only_above["backing_bucket"] == NO_WALL_BEHIND
    assert only_above["backing_bps"] is None


def test_an_event_without_a_price_or_instant_is_an_honest_absence_never_a_crash():
    """The tolerance ``_file_projection`` already applies to older/partial records: excluded from
    what it cannot support, never fabricated, never an exception."""
    assert band_context_block(_map([_band("support", 99.0, 100.0)]), None, "long")["status"] == (
        NO_BAND_CONTEXT
    )
    record = _record([{"symbol": "SYN", "setup_id": "jbe", "side": "long", "forward": _forward_leaf(1.0)}])
    context = record_band_context(record, _StubResolver({}))
    assert context["signals"][0]["band_context"]["status"] == NO_BAND_CONTEXT
    assert record_map_requests(record) == []


# --- baseline-anchor attribution -------------------------------------------------------------------


def test_anchors_are_attributed_positionally_and_verified_against_their_close_price():
    signals = [
        _signal("AAA", "jbe", "long", 100.0, close_price=111.0),
        _signal("BBB", "jbe", "long", 200.0, close_price=222.0),
    ]
    anchors = {"jbe:long": [_anchor(101.0, 111.0), _anchor(201.0, 222.0)]}
    attributed = _attribute_anchors(_record(signals, anchors))
    assert [s["symbol"] for s in attributed["jbe:long"]] == ["AAA", "BBB"]

    context = record_band_context(
        _record(signals, anchors), _StubResolver({"AAA": _map([]), "BBB": _map([])})
    )
    rows = context["baseline_anchors"]["jbe:long"]
    assert [r["symbol"] for r in rows] == ["AAA", "BBB"]
    assert {r["attribution"] for r in rows} == {"positional_verified"}
    assert context["basis"]["n_anchors_unattributable"] == 0


def test_a_close_price_disagreement_refuses_the_whole_pool_rather_than_guessing():
    """A partial attribution inside one pool is the ONE shape that could pair an anchor with the
    wrong symbol's wall, so a disagreement refuses the pool wholesale."""
    signals = [
        _signal("AAA", "jbe", "long", 100.0, close_price=111.0),
        _signal("BBB", "jbe", "long", 200.0, close_price=222.0),
    ]
    # Second anchor's close price belongs to no signal in this pool.
    anchors = {"jbe:long": [_anchor(101.0, 111.0), _anchor(201.0, 999.0)]}
    attributed = _attribute_anchors(_record(signals, anchors))
    assert attributed["jbe:long"] == [None, None]

    context = record_band_context(_record(signals, anchors), _StubResolver({"AAA": _map([])}))
    rows = context["baseline_anchors"]["jbe:long"]
    assert [r["symbol"] for r in rows] == [None, None]
    assert {r["attribution"] for r in rows} == {"unattributable"}
    assert {r["band_context"]["status"] for r in rows} == {NO_BAND_CONTEXT}
    assert context["basis"]["n_anchors_unattributable"] == 2


def test_more_anchors_than_signals_is_refused_not_truncated():
    signals = [_signal("AAA", "jbe", "long", 100.0, close_price=111.0)]
    anchors = {"jbe:long": [_anchor(101.0, 111.0), _anchor(102.0, 111.0)]}
    assert _attribute_anchors(_record(signals, anchors))["jbe:long"] == [None, None]


def test_an_anchor_carries_its_pools_own_side_so_both_columns_read_the_same_way():
    """``compute_playbook`` signs an anchor's measurement with its signal's side; the lens uses the
    same side, so ``side_relation`` is populated on both halves of the comparison."""
    signals = [_signal("AAA", "double_top", "short", 100.0, close_price=111.0)]
    anchors = {"double_top:short": [_anchor(100.0, 111.0)]}
    resolver = _StubResolver(
        {"AAA": _map([_band("resistance", 99.9, 100.1), _band("support", 97.0, 98.0)])}
    )
    context = record_band_context(_record(signals, anchors), resolver)
    anchor = context["baseline_anchors"]["double_top:short"][0]["band_context"]
    # Read as a SHORT (the pool's own side): backed by the resistance band it sits in, with room
    # down to the support band -- and the risk borrowed from its paired signal, disclosed.
    assert anchor["backing_bps"] == 0.0
    assert anchor["backing_bucket"] == AT_WALL
    assert anchor["headroom_bps"] is not None
    assert anchor["risk_source"] == "paired_signal"


# --- serving paths never compute, never write ------------------------------------------------------


def test_the_serving_resolver_never_computes_a_map(tmp_path, monkeypatch):
    """GET-never-computes, enforced by a counting stub: constructing a default ``BandMapResolver``
    and resolving an uncached pair must make ZERO ``compute_tradability`` calls."""
    from app.research import desk_playbook_context as context_module

    calls = {"n": 0}

    def _counting(*_a, **_k):
        calls["n"] += 1
        raise AssertionError("a serving path must never compute a tradable map")

    monkeypatch.setattr(context_module, "compute_tradability", _counting)

    class _EmptyStore:
        root = tmp_path / "bars"

        def list(self):
            return [], []

    resolver = context_module.BandMapResolver(_EmptyStore(), CONFIG)
    assert resolver.resolve("AAA", 1_800_000_000.0) is None
    assert calls["n"] == 0


def test_the_compute_flag_can_fail_the_never_computes_guard(tmp_path, monkeypatch):
    """The seeded counter-test: the SAME guard, with the warmer's own ``compute=True``, does reach
    the computer — so the assertion above is non-vacuous."""
    from app.research import desk_playbook_context as context_module

    calls = {"n": 0}

    def _counting(*_a, **_k):
        calls["n"] += 1
        return {"bands": [], "no_bar_series_for_symbol": True, "basis_as_of": None}

    monkeypatch.setattr(context_module, "compute_tradability", _counting)

    class _EmptyStore:
        root = tmp_path / "bars"

        def list(self):
            return [], []

    resolver = context_module.BandMapResolver(_EmptyStore(), CONFIG, compute=True)
    resolver.resolve("AAA", 1_800_000_000.0)
    assert calls["n"] == 1


def test_reading_context_never_modifies_one_recorded_byte(tmp_path):
    """The append-only corpus is not touched by reading it — every file's bytes AND stat are
    identical before and after a context is built and cached."""
    playbook_dir = tmp_path / "playbook"
    store = PlaybookStore(playbook_dir)
    playbook_dir.mkdir(parents=True)
    record = _record([_signal("AAA", "jbe", "long", 100.0, close_price=111.0)])
    path = playbook_dir / f"{record['id']}.json"
    path.write_text(json.dumps({"file_checksum": "x", "record": {"meta": record}}))

    before = (path.read_bytes(), path.stat().st_size, path.stat().st_mtime_ns)
    cache = PlaybookContextCache(str(tmp_path / "ctx.db"))
    stat = path.stat()
    context_for_record(record, stat.st_size, stat.st_mtime_ns, _StubResolver({"AAA": _map([])}), cache)
    after = (path.read_bytes(), path.stat().st_size, path.stat().st_mtime_ns)
    assert before == after
    assert sorted(p.name for p in playbook_dir.iterdir()) == [f"{record['id']}.json"]


def test_the_context_module_never_calls_the_stores_writer():
    """Structural companion to the behavioural test above: the module's own source contains no
    ``.record(`` call at all — it is mechanically incapable of writing a playbook file."""
    source = (RESEARCH_DIR / "desk_playbook_context.py").read_text()
    assert ".record(" not in source
    # Non-vacuous: the writer this guard bans is real and reachable from a sibling module.
    assert ".record(" in (RESEARCH_DIR / "desk_playbook_compute.py").read_text()


# --- the import direction (TC-7's structural companion) --------------------------------------------

_DETECTION_MODULES = ("desk_playbook.py", "desk_playbook_detect.py", "desk_playbook_features.py")
_CONTEXT_IMPORT = re.compile(r"^\s*(from|import)\s+.*context", re.MULTILINE)


def test_the_detection_modules_never_import_the_context_lens():
    """The lens reads the walk's output; the walk must never reach the lens. This is the structural
    half of TC-7 (``test_desk_playbook_guards.py``'s call-counting walk guard): even a future edit
    that wired band context INTO detection would be caught here, before it could re-key one
    recorded signature or make a detector depend on structure."""
    for name in _DETECTION_MODULES:
        source = (RESEARCH_DIR / name).read_text()
        assert not _CONTEXT_IMPORT.search(source), f"{name} must not import the band-context lens"


def test_the_import_direction_guard_can_fail_on_a_seeded_violation():
    seeded = "from __future__ import annotations\nfrom .desk_playbook_context import AT_WALL\n"
    assert _CONTEXT_IMPORT.search(seeded)


_EVIDENCE_IMPORT = re.compile(r"^\s*(from|import)\s+.*desk_playbook_evidence", re.MULTILINE)


def test_the_lens_never_imports_the_evidence_fold():
    """The other direction of the same rule — evidence reads the lens, so the lens importing
    evidence back would be a cycle and a second owner of the fold. Matched on IMPORT LINES only:
    the lens is free to NAME the fold in prose (it documents the alignment contract they share),
    and a guard that banned the word would punish the documentation that makes the pairing safe."""
    source = (RESEARCH_DIR / "desk_playbook_context.py").read_text()
    assert not _EVIDENCE_IMPORT.search(source)
    # Non-vacuous, and the direction that IS allowed is real.
    assert _EVIDENCE_IMPORT.search("from .desk_playbook_evidence import fold_evidence\n")
    assert re.search(
        r"^\s*from\s+\.desk_playbook_context\s+import",
        (RESEARCH_DIR / "desk_playbook_evidence.py").read_text(),
        re.MULTILINE,
    )


# --- the durable cache ------------------------------------------------------------------------------


def test_cold_and_warm_contexts_are_byte_identical(tmp_path):
    record = _record([_signal("AAA", "jbe", "long", 100.0, close_price=111.0)])
    cache = PlaybookContextCache(str(tmp_path / "ctx.db"))
    resolver = _StubResolver({"AAA": _map([_band("support", 99.9, 100.1)])})
    cold = context_for_record(record, 10, 20, resolver, cache)
    calls_after_cold = len(resolver.calls)
    warm = context_for_record(record, 10, 20, resolver, cache)
    assert json.dumps(cold) == json.dumps(warm)
    # A warm read resolves NO maps at all — the whole reason the cache exists.
    assert len(resolver.calls) == calls_after_cold


def test_the_cache_key_busts_on_every_component_that_could_change_the_answer():
    base = dict(
        playbook_id="playbook-2026-08-07-testrecord",
        file_size=10,
        file_mtime_ns=20,
        map_keys=[("AAA", "2026-08-07", "key-1")],
    )
    key = playbook_context_cache_key(**base)
    assert key == playbook_context_cache_key(**base)  # deterministic
    assert key != playbook_context_cache_key(**{**base, "playbook_id": "other"})
    assert key != playbook_context_cache_key(**{**base, "file_size": 11})
    assert key != playbook_context_cache_key(**{**base, "file_mtime_ns": 21})
    assert key != playbook_context_cache_key(
        **{**base, "map_keys": [("AAA", "2026-08-07", "key-2")]}
    )
    # Order-independent: the same set of maps in any order is the same context.
    two = [("AAA", "2026-08-07", "key-1"), ("BBB", "2026-08-07", "key-2")]
    assert playbook_context_cache_key(**{**base, "map_keys": two}) == playbook_context_cache_key(
        **{**base, "map_keys": list(reversed(two))}
    )


def test_a_changed_tradability_key_serves_a_fresh_context_not_a_stale_one(tmp_path):
    """The invalidation that actually matters: new bars for the symbol move its tradability key,
    which moves this record's context key, so a re-warm cannot serve the old location."""
    record = _record([_signal("AAA", "jbe", "long", 100.0, close_price=111.0)])
    cache = PlaybookContextCache(str(tmp_path / "ctx.db"))

    class _Shifting(_StubResolver):
        def __init__(self, maps, key_suffix):
            super().__init__(maps)
            self.key_suffix = key_suffix

        def map_key_for_basis_day(self, symbol, basis_day):
            return f"stub:{symbol}:{basis_day}:{self.key_suffix}"

    first = context_for_record(
        record, 10, 20, _Shifting({"AAA": _map([_band("support", 99.9, 100.1)])}, "v1"), cache
    )
    second = context_for_record(
        record, 10, 20, _Shifting({"AAA": _map([_band("resistance", 110.0, 111.0)])}, "v2"), cache
    )
    assert first["signals"][0]["band_context"]["backing_bucket"] == AT_WALL
    assert second["signals"][0]["band_context"]["backing_bucket"] == NO_WALL_BEHIND


def test_the_context_cache_carries_no_update_or_delete_method():
    """Structural, the ``PlaybookEvidenceCache`` discipline: a rebuildable accelerator owns nothing
    and can never be the thing that loses data."""
    for forbidden in ("update", "delete", "remove", "purge"):
        assert not hasattr(PlaybookContextCache, forbidden)


def test_a_missing_cache_file_loses_nothing_and_fabricates_nothing(tmp_path):
    record = _record([_signal("AAA", "jbe", "long", 100.0, close_price=111.0)])
    resolver = _StubResolver({"AAA": _map([_band("support", 99.9, 100.1)])})
    db = tmp_path / "ctx.db"
    cache = PlaybookContextCache(str(db))
    with_cache = context_for_record(record, 10, 20, resolver, cache)
    db.unlink()
    without_cache = context_for_record(record, 10, 20, resolver, None)
    assert json.dumps(with_cache) == json.dumps(without_cache)


def test_the_cache_path_resolver_is_a_sibling_of_the_playbook_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_PLAYBOOK_CONTEXT_CACHE_DB", raising=False)
    resolved = resolve_playbook_context_cache_db_path(str(tmp_path / "data" / "playbook"))
    assert resolved == str(tmp_path / "data" / "playbook_context_cache.db")
    monkeypatch.setenv("TAPEOLOGY_PLAYBOOK_CONTEXT_CACHE_DB", "/tmp/override.db")
    assert resolve_playbook_context_cache_db_path(str(tmp_path)) == "/tmp/override.db"


# --- copy discipline --------------------------------------------------------------------------------


def test_the_register_and_every_caption_template_are_clean():
    """The served prose carries no advice, forecast, or edge/probability claim — checked with the
    project's own lint rather than by eye."""
    assert find_violations(CONTEXT_REGISTER) == []
    band = _band("support", 99.5, 100.2, klass="A")
    for block in (
        band_context_block(None, 100.0, "long"),
        band_context_block(_map([]), 100.0, "long"),
        band_context_block(_map([band]), 100.0, "long"),
        band_context_block(_map([band]), 130.0, "short"),
        band_context_block(_map([band]), None, "long"),
    ):
        assert find_violations(block["caption"]) == [], block["caption"]


def test_the_copy_lint_can_fail_on_a_seeded_caption():
    assert find_violations("this setup has an edge at the band, you should buy now") != []


# --- the route ---------------------------------------------------------------------------------------


@pytest.fixture
def context_client(tmp_path, monkeypatch):
    playbook_dir = tmp_path / "playbook"
    playbook_dir.mkdir(parents=True)
    store = PlaybookStore(playbook_dir)
    app.dependency_overrides[get_playbook_store] = lambda: store
    app.dependency_overrides[get_playbook_context_cache] = lambda: PlaybookContextCache(
        str(tmp_path / "ctx.db")
    )
    with TestClient(app) as client:
        yield client, playbook_dir
    app.dependency_overrides.pop(get_playbook_store, None)
    app.dependency_overrides.pop(get_playbook_context_cache, None)


def test_route_serves_an_honest_null_for_an_id_nothing_recorded(context_client):
    client, _ = context_client
    response = client.get("/research/desk/playbook/context", params={"id": "playbook-nope"})
    assert response.status_code == 200
    assert response.json() == {"context": None}


def test_route_requires_an_id(context_client):
    client, _ = context_client
    assert client.get("/research/desk/playbook/context").status_code == 422


def test_route_serves_not_computed_rather_than_computing_a_cold_map(context_client):
    """The route's own GET-never-computes proof, end to end: a real recorded record whose maps were
    never warmed serves ``not_computed`` — an honest, distinct state — instead of paying a
    multi-second computation per symbol inside a page load."""
    client, playbook_dir = context_client
    # Written through the store's OWN writer, so this exercises a record that really verifies
    # rather than a hand-built shape the store would refuse.
    meta = PlaybookStore(playbook_dir).record(
        session_date="2026-08-07",
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature="sig-abc",
        payload_version=3,
        parameters={},
        register="",
        signals=[_signal("AAA", "jbe", "long", 100.0, close_price=111.0)],
        absences=[],
        diagnostics=[],
    )
    response = client.get("/research/desk/playbook/context", params={"id": meta["id"]})
    assert response.status_code == 200
    context = response.json()["context"]
    assert context is not None
    assert context["signals"][0]["band_context"]["status"] == NOT_COMPUTED
    assert context["basis"]["n_signals_not_computed"] == 1
    assert "has not been computed" in context["signals"][0]["band_context"]["caption"]


# --- the declared comparison axis --------------------------------------------------------------------


def test_the_two_axes_are_exactly_the_declared_buckets_and_absences_are_on_neither():
    """The split compares locations on two axes; the absence states are EXCLUSIONS counted in the
    basis, never distribution cells of their own."""
    assert PLAYBOOK_CONTEXT_BACKING_BUCKETS == (AT_WALL, OFF_WALL, NO_WALL_BEHIND)
    assert PLAYBOOK_CONTEXT_ROOM_BUCKETS == (ROOM_LT_1R, ROOM_1R_2R, ROOM_GE_2R, NO_WALL_AHEAD)
    for absence in (NOT_COMPUTED, NO_BAND_CONTEXT, ROOM_UNMEASURED):
        assert absence not in PLAYBOOK_CONTEXT_BACKING_BUCKETS
        assert absence not in PLAYBOOK_CONTEXT_ROOM_BUCKETS


# --- the evidence split (n_positive + the at-band/away comparison) -----------------------------------
# These live here, beside the lens they exercise, rather than in `test_desk_playbook_evidence.py`:
# they are assertions ABOUT the band-context axis, and the fold's own pre-existing guards stay where
# they are.

from app.providers.adapters.base import RawBar  # noqa: E402
from app.research.desk_forward import _measure_from  # noqa: E402
from app.research.desk_playbook import PLAYBOOK_SETUPS, PLAYBOOK_SIGNAL_MEASURES  # noqa: E402
from app.research.desk_playbook_evidence import (  # noqa: E402
    _baseline_cell,
    _n_positive_for,
    _signal_cell,
    fold_band_context,
)


def test_n_positive_counts_only_strictly_positive_values():
    """A recorded 0.0 is a real measured "went nowhere" and is NOT counted as a move in either
    direction — the boundary that decides what the count means."""
    assert _n_positive_for("1h", [2.0, -1.0, 0.0, 0.5]) == 2
    assert _n_positive_for("1h", []) == 0
    assert _n_positive_for("to_close", [-0.1, -0.2]) == 0


def test_n_positive_is_null_on_every_drawdown_measure():
    """A drawdown is clamped ``<= 0`` by construction, so "greater than zero" is not a fact it can
    carry; serving 0 there would read as a measured absence rather than the category error it is."""
    for measure in PLAYBOOK_SIGNAL_MEASURES:
        value = _n_positive_for(measure, [1.0, -1.0])
        if measure.startswith("mdd_"):
            assert value is None, measure
        else:
            assert value == 1, measure


def test_n_positive_shares_one_pool_with_the_median_it_sits_beside():
    """"positive: k of n" and "median of n" must describe ONE pool — the same untruncated list."""
    cell = _signal_cell("1h", [2.0, -1.0, 4.0], n_truncated=2, n_unmeasured=1, n_sessions=1)
    assert cell["n"] == 3 and cell["n_positive"] == 2
    baseline = _baseline_cell("1h", [-1.0], n_truncated=0, n_unmeasured=0, n_sessions=1)
    assert baseline["n_baseline"] == 1 and baseline["n_positive"] == 0
    assert _signal_cell("mdd_long_1h", [-1.0], 0, 0, 1)["n_positive"] is None


def _projection(pool_key, events, *, playbook_id="rec-1", session_date="2026-08-07", anchors=None):
    return {
        "projection_version": 2,
        "playbook_id": playbook_id,
        "playbook_input_signature": "sig-abc",
        "session_date": session_date,
        "recorded_at": "2026-08-07T22:00:00.000000Z",
        "map_requests": [],
        "signal_events": {pool_key: events},
        "baseline_events": {pool_key: anchors or []},
        "breach_counts": {},
    }


def _bc(coordinate):
    """A served band_context stub from a test coordinate: either a ``(backing, room)`` pair or one
    of the states that is not a cell (an absence, or room_unmeasured)."""
    if isinstance(coordinate, tuple):
        backing, room = coordinate
        return {"status": LOCATED, "backing_bucket": backing, "room_bucket": room}
    if coordinate == ROOM_UNMEASURED:
        return {"status": LOCATED, "backing_bucket": AT_WALL, "room_bucket": ROOM_UNMEASURED}
    return {"status": coordinate, "backing_bucket": None, "room_bucket": None}


def _context(pool_key, coordinates, *, playbook_id="rec-1", anchor_coordinates=None):
    return {
        "playbook_id": playbook_id,
        "signals": [
            {"pool_key": pool_key, "measured": True, "band_context": _bc(c)}
            for c in coordinates
        ],
        "baseline_anchors": {
            pool_key: [{"band_context": _bc(c)} for c in (anchor_coordinates or [])]
        },
        "basis": {"n_anchors_unattributable": 0},
    }


def _event(return_pct):
    """A REAL ``_measure_from`` leaf whose 1h return is EXACTLY ``return_pct`` — built the way
    ``test_desk_playbook_evidence`` builds its own fixtures (a flat 5m session with the 1h horizon
    at offset 12), so these split assertions run through the rail's own pooling rather than a
    hand-shaped dict the rail might read differently."""
    entry = 100.0
    closes = [entry] * 15
    closes[12] = entry * (1.0 + return_pct / 100.0)
    bars = [
        RawBar(
            symbol="SYN", timeframe="5m", epoch=1_800_000_000.0 + i * 300.0,
            open=c, high=c, low=c, close=c, volume=1000.0,
        )
        for i, c in enumerate(closes)
    ]
    return _measure_from(bars, 0, entry, "level", 5, 1.0)


def _cell(body, setup_id, side, measure, backing, room):
    return next(
        c for c in body["cells"]
        if c["setup_id"] == setup_id and c["side"] == side and c["measure"] == measure
        and c["backing_bucket"] == backing and c["room_bucket"] == room
    )


def test_the_split_serves_the_full_declared_cross_product_including_empty_cells():
    body = fold_band_context([], {})
    assert len(body["cells"]) == (
        len(PLAYBOOK_SETUPS) * 2
        * len(PLAYBOOK_CONTEXT_BACKING_BUCKETS)
        * len(PLAYBOOK_CONTEXT_ROOM_BUCKETS)
        * 5  # the five DIRECTIONAL measures only
    )
    empty = _cell(body, "jbe", "long", "1h", AT_WALL, ROOM_GE_2R)
    assert empty["signal"]["n"] == 0
    assert empty["below_min_n"] is True  # a tag, served, never a filter


def test_the_split_folds_only_the_five_directional_measures():
    """A drawdown is clamped <= 0 by construction, so splitting it by location would multiply rows
    without adding a reading — the UNSPLIT table still serves all fifteen."""
    measures = {c["measure"] for c in fold_band_context([], {})["cells"]}
    assert measures == {"1m", "5m", "1h", "4h", "to_close"}
    assert not any(m.startswith("mdd_") for m in measures)


def test_events_route_to_the_joint_cohort_their_own_context_names():
    projection = _projection("jbe:long", [_event(2.0), _event(-3.0), _event(4.0)])
    context = _context(
        "jbe:long",
        [(AT_WALL, ROOM_GE_2R), (OFF_WALL, ROOM_LT_1R), (AT_WALL, ROOM_GE_2R)],
    )
    body = fold_band_context([projection], {"rec-1": context})

    backed = _cell(body, "jbe", "long", "1h", AT_WALL, ROOM_GE_2R)["signal"]
    naked = _cell(body, "jbe", "long", "1h", OFF_WALL, ROOM_LT_1R)["signal"]
    assert backed["n"] == 2 and backed["n_positive"] == 2 and backed["median_pct"] == 3.0
    assert naked["n"] == 1 and naked["n_positive"] == 0 and naked["median_pct"] == -3.0
    # Each axis independently sums to the located total -- a reader can check the disclosure adds up.
    assert body["basis"]["n_signals_at_wall"] == 2
    assert body["basis"]["n_signals_off_wall"] == 1
    assert body["basis"]["n_signals_room_ge_2r"] == 2
    assert body["basis"]["n_signals_room_lt_1r"] == 1


def test_absent_context_is_counted_in_the_basis_and_never_enters_a_cohort():
    """The exclusion discipline: what is not known is counted, and it never silently pads any
    cohort."""
    projection = _projection("jbe:long", [_event(2.0), _event(9.0)])
    context = _context("jbe:long", [(AT_WALL, ROOM_GE_2R), NOT_COMPUTED])
    body = fold_band_context([projection], {"rec-1": context})
    assert _cell(body, "jbe", "long", "1h", AT_WALL, ROOM_GE_2R)["signal"]["n"] == 1
    assert body["basis"]["n_signals_not_computed"] == 1
    assert body["basis"]["n_signals_at_wall"] == 1
    # The excluded event is in NO backing bucket and NO room bucket.
    assert body["basis"]["n_signals_off_wall"] == 0
    assert body["basis"]["n_signals_no_wall_behind"] == 0


def test_room_unmeasured_is_counted_and_never_placed_in_a_cohort():
    """Headroom known but no invalidation distance to divide by: a real state, counted, never a
    cell keyed on a coordinate the event does not have."""
    projection = _projection("jbe:long", [_event(2.0), _event(5.0)])
    context = _context("jbe:long", [(AT_WALL, ROOM_1R_2R), ROOM_UNMEASURED])
    body = fold_band_context([projection], {"rec-1": context})
    assert _cell(body, "jbe", "long", "1h", AT_WALL, ROOM_1R_2R)["signal"]["n"] == 1
    assert body["basis"]["n_signals_room_unmeasured"] == 1
    assert sum(
        _cell(body, "jbe", "long", "1h", AT_WALL, room)["signal"]["n"]
        for room in PLAYBOOK_CONTEXT_ROOM_BUCKETS
    ) == 1


def test_a_record_with_no_context_at_all_is_absent_never_a_location():
    """A fold running before any warm must not invent locations — every event is an honest
    absence, and every cohort stays empty."""
    body = fold_band_context([_projection("jbe:long", [_event(2.0)])], {})
    assert all(c["signal"]["n"] == 0 for c in body["cells"])
    assert body["basis"]["n_signals_no_band_context"] == 1


def test_a_length_disagreement_refuses_the_pool_rather_than_mispairing_cohorts():
    """The alignment between a projection's events and a context's signals is CHECKED, not
    trusted: a disagreement degrades to absent context instead of pairing an event with another
    event's location."""
    projection = _projection("jbe:long", [_event(2.0), _event(3.0), _event(4.0)])
    context = _context("jbe:long", [(AT_WALL, ROOM_GE_2R)])  # one context for three events
    body = fold_band_context([projection], {"rec-1": context})
    assert all(c["signal"]["n"] == 0 for c in body["cells"])
    assert body["basis"]["n_signals_no_band_context"] == 3


def test_baseline_anchors_split_by_the_same_lens_as_the_signals():
    """The comparison is location-matched: a backed-with-room signal is compared against anchors
    that also sat backed with room, so the null answers "did a random minute in the SAME structural
    position do this?" rather than "did any random minute anywhere do this?"."""
    projection = _projection("jbe:long", [_event(2.0)], anchors=[_event(0.5), _event(-0.5)])
    context = _context(
        "jbe:long",
        [(AT_WALL, ROOM_GE_2R)],
        anchor_coordinates=[(AT_WALL, ROOM_GE_2R), (OFF_WALL, ROOM_LT_1R)],
    )
    body = fold_band_context([projection], {"rec-1": context})
    assert _cell(body, "jbe", "long", "1h", AT_WALL, ROOM_GE_2R)["baseline"]["n_baseline"] == 1
    assert _cell(body, "jbe", "long", "1h", OFF_WALL, ROOM_LT_1R)["baseline"]["n_baseline"] == 1
    assert body["basis"]["n_anchors_at_wall"] == 1
    assert body["basis"]["n_anchors_off_wall"] == 1


def test_the_split_pools_across_records_and_counts_distinct_sessions():
    first = _projection("jbe:long", [_event(2.0)], playbook_id="rec-1", session_date="2026-08-06")
    second = _projection("jbe:long", [_event(4.0)], playbook_id="rec-2", session_date="2026-08-07")
    contexts = {
        "rec-1": _context("jbe:long", [(AT_WALL, ROOM_GE_2R)], playbook_id="rec-1"),
        "rec-2": _context("jbe:long", [(AT_WALL, ROOM_GE_2R)], playbook_id="rec-2"),
    }
    body = fold_band_context([first, second], contexts)
    cell = _cell(body, "jbe", "long", "1h", AT_WALL, ROOM_GE_2R)["signal"]
    assert cell["n"] == 2 and cell["n_sessions"] == 2 and cell["median_pct"] == 3.0


def test_the_split_carries_its_own_parameters_and_register():
    body = fold_band_context([], {})
    assert body["parameters"]["near_band_bps"] == PLAYBOOK_CONTEXT_NEAR_BAND_BPS
    assert body["parameters"]["room_r_edges"] == [1.0, 2.0]
    assert body["parameters"]["distance_from"] == "entry"
    assert body["parameters"]["backing_buckets"] == list(PLAYBOOK_CONTEXT_BACKING_BUCKETS)
    assert body["parameters"]["room_buckets"] == list(PLAYBOOK_CONTEXT_ROOM_BUCKETS)
    assert body["register"] == CONTEXT_REGISTER
    assert find_violations(body["register"]) == []


def test_an_incomplete_context_is_never_persisted_and_never_trusted(tmp_path):
    """The cache-poisoning guard. This cache keys on the maps a context was built FROM, not on
    whether those maps had been computed — so a lookup-only serving path (every event honestly
    ``not_computed``) must NOT write a row, or that row would keep serving "no location known"
    forever, long after the warmer computed the real maps, and the absence would look permanent
    and measured when it was neither.

    Both halves are guarded, which is also what makes an already-poisoned DB self-heal: an
    incomplete row that somehow exists is ignored on lookup and replaced by the first complete
    build."""
    record = _record([_signal("AAA", "jbe", "long", 100.0, close_price=111.0)])
    cache = PlaybookContextCache(str(tmp_path / "ctx.db"))

    # A serving-shaped resolver knows no maps: every event reads not_computed.
    cold_serve = context_for_record(record, 10, 20, _StubResolver({}), cache)
    assert cold_serve["signals"][0]["band_context"]["status"] == NOT_COMPUTED
    assert cold_serve["basis"]["n_signals_not_computed"] == 1

    # ...and nothing was written, so the warmer that follows is not shadowed by it.
    warmed = context_for_record(
        record, 10, 20, _StubResolver({"AAA": _map([_band("support", 99.9, 100.1)])}), cache
    )
    assert warmed["signals"][0]["band_context"]["backing_bucket"] == AT_WALL

    # The complete context IS persisted: a later serving-shaped read gets the real location.
    served = context_for_record(record, 10, 20, _StubResolver({}), cache)
    assert served["signals"][0]["band_context"]["backing_bucket"] == AT_WALL


def test_a_pre_existing_incomplete_row_is_ignored_rather_than_served(tmp_path):
    """The self-heal, proven directly: an incomplete row planted under the exact key a build would
    use is not served."""
    record = _record([_signal("AAA", "jbe", "long", 100.0, close_price=111.0)])
    cache = PlaybookContextCache(str(tmp_path / "ctx.db"))
    resolver = _StubResolver({"AAA": _map([_band("support", 99.9, 100.1)])})
    key = playbook_context_cache_key(
        playbook_id=record["id"],
        file_size=10,
        file_mtime_ns=20,
        map_keys=sorted(
            {
                (symbol, basis_day, resolver.map_key_for_basis_day(symbol, basis_day))
                for symbol, basis_day in record_map_requests(record)
            }
        ),
    )
    poisoned = record_band_context(record, _StubResolver({}))
    cache.publish(key, poisoned)
    assert cache.lookup(key) is not None  # the row really is there

    served = context_for_record(record, 10, 20, resolver, cache)
    assert served["signals"][0]["band_context"]["backing_bucket"] == AT_WALL
