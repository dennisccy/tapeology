"""Guards for ``desk_playbook_cohort`` — the record's own recorded pooled summary, narrowed to a
declared cohort of the locations its signals fired at.

The load-bearing property, pinned first and hardest: **the unfiltered cohort IS the record's own
summary**. The desk's per-setup table renders these numbers, so an operator flipping a filter back
to "all" must land on exactly what the record recorded — not on something re-derived that happens
to look similar. Everything else here defends the honesty of the narrowed cohorts: that narrowing
can only remove signals, that a signal with no known location is never claimed to be outside a
band, and that what was excluded is counted rather than dropped.

Every structural guard carries a seeded counter-case (a lint that cannot fail proves nothing).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.research.desk_playbook import PlaybookStore
from app.research.desk_playbook_cohort import (
    BACKING_AT_WALL,
    BACKING_AT_WALL_ROOM_GE_1R,
    COHORT_REGISTER,
    INSIDE_IN_BAND,
    INSIDE_OUT_OF_BAND,
    PLAYBOOK_COHORT_BACKING_VALUES,
    PLAYBOOK_COHORT_INSIDE_VALUES,
    PLAYBOOK_COHORT_KEYS,
    UNFILTERED_COHORT,
    cohort_key,
    cohort_parameters,
    fold_cohorts,
    signal_cohorts,
)
from app.research.desk_playbook_context import (
    AT_WALL,
    LOCATED,
    NOT_COMPUTED,
    NO_BAND_CONTEXT,
    OFF_WALL,
    ROOM_GE_2R,
    ROOM_LT_1R,
    ROOM_UNMEASURED,
    context_parameters,
)
from app.research.desk_routes import get_playbook_context_cache, get_playbook_store
from test_copy_discipline import find_violations

RESEARCH_DIR = Path(__file__).resolve().parents[1] / "app" / "research"
E_OPEN = 1782135000.0


# --- fixtures -------------------------------------------------------------------------------------


def _forward(entry: float, at_1h: float, *, side: str = "long", n_bars: int = 15) -> dict:
    """A REAL ``_measure_from`` leaf, the shape every pooled value comes from."""
    from app.providers.adapters.base import RawBar
    from app.research.desk_forward import _measure_from

    sign = 1.0 if side == "long" else -1.0
    closes = [entry] * n_bars
    if n_bars > 12:
        closes[12] = at_1h
    bars = [
        RawBar("SYN", "5m", E_OPEN + i * 300.0, c, c, c, c, 1000) for i, c in enumerate(closes)
    ]
    return _measure_from(bars, 0, entry, "level", 5, sign)


def _signal(setup_id: str, side: str, forward: dict, *, symbol: str = "SYN", ts: str | None = None):
    return {
        "symbol": symbol,
        "setup_id": setup_id,
        "side": side,
        "trigger_ts": ts or f"2026-08-07T16:{abs(hash(forward['entry_price'])) % 60:02d}:00.000000Z",
        "entry": forward["entry_price"],
        "entry_kind": "level",
        "invalidation_price": forward["entry_price"] - 1.0,
        "forward": forward,
    }


def _band_context(status=LOCATED, *, backing=AT_WALL, room=ROOM_GE_2R, containing=True):
    return {
        "status": status,
        "containing_band": {"side": "support", "class": "A"} if containing else None,
        "backing_bucket": backing if status == LOCATED else None,
        "room_bucket": room if status == LOCATED else None,
    }


def _record(signals, anchors=None, summary=None, *, cap=8, beyond=None):
    return {
        "id": "playbook-2026-08-07-fixture",
        "session_date": "2026-08-07",
        "parameters": {"rail_max_touches_per_row": cap, "signal_measures": ["1h", "to_close"]},
        "signals": signals,
        "baseline_anchors": anchors or {},
        "summary": summary if summary is not None else {"jbe:long": {}},
        "signals_beyond_cap": beyond or {},
    }


def _context(rows, anchors=None):
    """A served context stub: `rows` is [(signal, band_context)] in record order."""
    return {
        "playbook_id": "playbook-2026-08-07-fixture",
        "signals": [
            {
                "symbol": s["symbol"],
                "setup_id": s["setup_id"],
                "side": s["side"],
                "pool_key": f"{s['setup_id']}:{s['side']}",
                "trigger_ts": s["trigger_ts"],
                "measured": s.get("forward") is not None,
                "band_context": bc,
            }
            for s, bc in rows
        ],
        "baseline_anchors": anchors or {},
    }


# --- THE property: the unfiltered cohort is the record's own summary --------------------------------


def test_the_unfiltered_cohort_is_the_records_own_summary_on_the_whole_corpus():
    """The guarantee the desk's summary table rests on, checked against every recorded record on
    disk rather than a fixture — including key order, which a reader's eye would never catch."""
    playbook_dir = RESEARCH_DIR.parents[1] / ".data" / "playbook"
    if not playbook_dir.exists():
        pytest.skip("no recorded corpus on this machine")
    checked = 0
    for path in sorted(playbook_dir.glob("*.json")):
        meta = json.loads(path.read_text())["record"]["meta"]
        if not (meta.get("summary") or {}):
            continue
        # Deliberately folded with NO context: the unfiltered cohort must not depend on one.
        fold = fold_cohorts(meta, None)
        assert json.dumps(fold["cohorts"][UNFILTERED_COHORT]["summary"]) == json.dumps(
            meta["summary"]
        ), f"{path.name}: the unfiltered cohort diverged from the record's own summary"
        checked += 1
    assert checked > 0, "expected at least one recorded record with a summary"


def test_the_equality_is_a_real_constraint_not_a_tautology():
    """The counter-case: pooling BEYOND the cap — the other defensible rule — must NOT reproduce
    the record's summary, so the equality above is load-bearing rather than accidental."""
    from app.research.desk_forward import _avg_cell, _collect_measures

    over_cap = [_signal("jbe", "long", _forward(100.0, 100.0 + i)) for i in range(1, 5)]
    anchors = {"jbe:long": [_forward(100.0, 100.5)] * 2}
    record = _record(over_cap, anchors, summary={"jbe:long": {}}, cap=2, beyond={"jbe:long": 2})
    capped = fold_cohorts(record, None)["cohorts"][UNFILTERED_COHORT]["summary"]["jbe:long"]
    uncapped_pool = _collect_measures([s["forward"] for s in over_cap])
    assert capped["1h"]["signals"]["n"] == 2
    assert _avg_cell(*uncapped_pool["1h"])["n"] == 4
    assert capped["1h"]["signals"] != _avg_cell(*uncapped_pool["1h"])


# --- membership: the predicate this module owns ------------------------------------------------------


def test_not_inside_is_never_claimed_for_a_signal_with_no_known_location():
    """The trap this module exists to close. The lens serves ``containing_band: null`` for every
    absence too, so a bare "containing_band is null" test would file every un-warmed signal under
    "not inside a band" — claiming a location for an event that has none."""
    for status in (NOT_COMPUTED, NO_BAND_CONTEXT):
        cohorts = signal_cohorts(_band_context(status, containing=False))
        assert cohorts == (UNFILTERED_COHORT,), status
        assert cohort_key("all", INSIDE_OUT_OF_BAND) not in cohorts
        assert cohort_key("all", INSIDE_IN_BAND) not in cohorts
    # ...while a LOCATED signal with no containing band genuinely is "not inside".
    located = signal_cohorts(_band_context(LOCATED, backing=OFF_WALL, containing=False))
    assert cohort_key("all", INSIDE_OUT_OF_BAND) in located


def test_inside_and_not_inside_partition_the_located_signals():
    inside = signal_cohorts(_band_context(containing=True))
    outside = signal_cohorts(_band_context(backing=OFF_WALL, containing=False))
    assert cohort_key("all", INSIDE_IN_BAND) in inside
    assert cohort_key("all", INSIDE_OUT_OF_BAND) not in inside
    assert cohort_key("all", INSIDE_OUT_OF_BAND) in outside
    assert cohort_key("all", INSIDE_IN_BAND) not in outside


def test_room_of_at_least_one_multiple_reads_the_served_room_bucket():
    """`no_wall_ahead` and `room_unmeasured` are not "room of at least 1x" — room is a statement
    about a wall ahead, and neither state has one. Counted, never folded in."""
    assert BACKING_AT_WALL_ROOM_GE_1R in [
        k.split(":", 1)[0] for k in signal_cohorts(_band_context(room=ROOM_GE_2R))
    ]
    for room in (ROOM_LT_1R, ROOM_UNMEASURED, "no_wall_ahead"):
        backings = {k.split(":", 1)[0] for k in signal_cohorts(_band_context(room=room))}
        assert BACKING_AT_WALL_ROOM_GE_1R not in backings, room
        assert BACKING_AT_WALL in backings, room  # still at a wall, just no room measurement


def test_an_off_wall_signal_joins_no_wall_cohort():
    backings = {k.split(":", 1)[0] for k in signal_cohorts(_band_context(backing=OFF_WALL))}
    assert backings == {"all"}


# --- the fold ---------------------------------------------------------------------------------------


def _two_signal_record():
    """One at-wall-inside signal and one off-wall signal, with distinguishable anchors."""
    first = _signal("jbe", "long", _forward(100.0, 110.0), ts="2026-08-07T16:00:00.000000Z")
    second = _signal("jbe", "long", _forward(100.0, 90.0), ts="2026-08-07T16:05:00.000000Z")
    anchors = {"jbe:long": [_forward(100.0, 101.0), _forward(100.0, 99.0)]}
    record = _record([first, second], anchors, summary={"jbe:long": {}})
    context = _context(
        [(first, _band_context(containing=True)), (second, _band_context(backing=OFF_WALL, containing=False))],
        anchors={
            "jbe:long": [
                {"attribution": "positional_verified"},
                {"attribution": "positional_verified"},
            ]
        },
    )
    return record, context


def test_narrowing_can_only_reduce_how_many_signals_a_cell_covers():
    record, context = _two_signal_record()
    fold = fold_cohorts(record, context)
    unfiltered = fold["cohorts"][UNFILTERED_COHORT]["summary"]["jbe:long"]["1h"]["signals"]["n"]
    for key, cohort in fold["cohorts"].items():
        cell = cohort["summary"]["jbe:long"]["1h"]
        assert cell["signals"]["n"] <= unfiltered, key
        # Both lines describe the same signals here (unlike the cross-session evidence table).
        assert cell["baseline"]["n"] <= cell["signals"]["n"], key


def test_each_pooled_signal_brings_its_own_paired_anchor():
    """The at-wall cohort pools signal 0 only, so it must pool anchor 0 only — the baseline line is
    a per-signal paired null, not a location-matched one."""
    record, context = _two_signal_record()
    fold = fold_cohorts(record, context)
    at_wall = fold["cohorts"][cohort_key(BACKING_AT_WALL, "all")]["summary"]["jbe:long"]["1h"]
    assert at_wall["signals"]["n"] == 1
    assert at_wall["baseline"]["n"] == 1
    # anchor 0 rose (+1%), anchor 1 fell (-1%) -- the pooled baseline proves WHICH one was taken.
    assert at_wall["baseline"]["mean_pct"] > 0


def test_an_unlocated_signal_is_pooled_unfiltered_and_counted_out_of_every_narrowed_cohort():
    signal = _signal("jbe", "long", _forward(100.0, 110.0))
    record = _record([signal], summary={"jbe:long": {}})
    context = _context([(signal, _band_context(NOT_COMPUTED, containing=False))])
    fold = fold_cohorts(record, context)
    assert fold["cohorts"][UNFILTERED_COHORT]["pools"]["jbe:long"]["n_signals"] == 1
    narrowed = fold["cohorts"][cohort_key(BACKING_AT_WALL, "all")]["pools"]["jbe:long"]
    assert narrowed["n_signals"] == 0
    assert narrowed["n_excluded_not_computed"] == 1
    # ...and an un-warmed map reads differently from a computed one with no band nearby.
    assert narrowed["n_excluded_no_band_context"] == 0


def test_every_pool_basis_adds_up_in_every_cohort():
    """What was excluded is accounted for by name — the difference between "nothing was at a wall"
    and "no map has been computed yet"."""
    record, context = _two_signal_record()
    for key, cohort in fold_cohorts(record, context)["cohorts"].items():
        for pool, basis in cohort["pools"].items():
            excluded = sum(
                basis[field] for field in basis if field.startswith("n_excluded_")
            )
            assert basis["n_eligible"] == basis["n_signals"] + excluded, (key, pool)


def test_a_missing_context_still_serves_the_records_own_summary():
    record, _ = _two_signal_record()
    fold = fold_cohorts(record, None)
    assert fold["basis"]["context_status"] == "absent"
    assert fold["cohorts"][UNFILTERED_COHORT]["summary"]["jbe:long"]["1h"]["signals"]["n"] == 2
    narrowed = fold["cohorts"][cohort_key(BACKING_AT_WALL, "all")]["pools"]["jbe:long"]
    assert narrowed["n_signals"] == 0 and narrowed["n_excluded_no_context"] == 2


def test_a_pool_whose_context_disagrees_in_length_is_refused_rather_than_mispaired():
    record, context = _two_signal_record()
    context["signals"] = context["signals"][:1]  # one context for two measured signals
    fold = fold_cohorts(record, context)
    assert fold["cohorts"][UNFILTERED_COHORT]["summary"]["jbe:long"]["1h"]["signals"]["n"] == 2
    pool = fold["cohorts"][cohort_key(BACKING_AT_WALL, "all")]["pools"]["jbe:long"]
    assert pool["context_aligned"] is False
    assert pool["n_signals"] == 0 and pool["n_excluded_no_context"] == 2


def test_the_served_cell_is_the_rails_own_avg_cell():
    record, context = _two_signal_record()
    cell = fold_cohorts(record, context)["cohorts"][UNFILTERED_COHORT]["summary"]["jbe:long"]["1h"]
    assert set(cell) == {"signals", "baseline"}
    assert set(cell["signals"]) == {"n", "mean_pct", "median_pct", "n_truncated"}


def test_beyond_cap_signals_are_served_as_display_members_but_never_pooled():
    """Two facts under two names: a beyond-cap signal at a wall still belongs in a narrowed ROW
    list, it just did not feed the pooled means."""
    signals = [_signal("jbe", "long", _forward(100.0, 100.0 + i), ts=f"2026-08-07T16:0{i}:00.000000Z") for i in range(3)]
    record = _record(signals, summary={"jbe:long": {}}, cap=1, beyond={"jbe:long": 2})
    context = _context([(s, _band_context(containing=True)) for s in signals])
    fold = fold_cohorts(record, context)
    rows = fold["signals"]
    assert [row["in_cap"] for row in rows] == [True, False, False]
    assert all(cohort_key(BACKING_AT_WALL, INSIDE_IN_BAND) in row["cohorts"] for row in rows)
    assert fold["cohorts"][cohort_key(BACKING_AT_WALL, INSIDE_IN_BAND)]["pools"]["jbe:long"][
        "n_signals"
    ] == 1


# --- vocabulary + structural guards -------------------------------------------------------------------


def test_the_declared_vocabulary_is_exactly_nine_cohorts_in_declared_order():
    assert PLAYBOOK_COHORT_BACKING_VALUES == ("all", "at_wall", "at_wall_room_ge_1r")
    assert PLAYBOOK_COHORT_INSIDE_VALUES == ("all", "inside", "not_inside")
    assert len(PLAYBOOK_COHORT_KEYS) == 9
    assert PLAYBOOK_COHORT_KEYS[0] == UNFILTERED_COHORT == "all:all"
    params = cohort_parameters()
    assert params["cohort_keys"] == list(PLAYBOOK_COHORT_KEYS)
    assert params["pooling"] == "record_in_cap_only"
    assert params["baseline_pairing"] == "paired_signal"


def test_the_lens_parameters_block_is_left_untouched():
    """The cohort vocabulary is a display composition on top of the lens, not part of it — the
    lens's own parameters ride two already-shipped payloads and must stay byte-stable."""
    assert set(context_parameters()) == {
        "algorithm",
        "near_band_bps",
        "room_r_edges",
        "distance_from",
        "statuses",
        "backing_buckets",
        "room_buckets",
    }


def test_the_fold_never_reads_a_bar_computes_a_map_or_writes_a_record():
    source = (RESEARCH_DIR / "desk_playbook_cohort.py").read_text()
    for banned in ("compute_tradability", "compute_levels", "merged_bars", ".record(", "_measure_from"):
        assert banned not in source, f"the cohort fold must never reach {banned}"
    # Non-vacuous: those names are real and reachable from sibling modules.
    assert "compute_tradability" in (RESEARCH_DIR / "desk_playbook_context.py").read_text()


def test_the_fold_pools_through_the_rails_own_helpers_only():
    """One pooling owner. A second implementation of the mean is exactly what the measurement rail
    exists to prevent."""
    source = (RESEARCH_DIR / "desk_playbook_cohort.py").read_text()
    assert "from .desk_forward import _avg_cell, _collect_measures" in source
    assert source.count("_avg_cell(") == 2  # the signals line and the baseline line, once each


def test_nothing_imports_the_cohort_fold_back_into_the_lens_or_the_detectors():
    """One-way imports: cohort reads the lens; neither the lens nor any detector may reach cohort."""
    pattern = re.compile(r"^\s*(from|import)\s+.*cohort", re.MULTILINE)
    for name in (
        "desk_playbook.py",
        "desk_playbook_detect.py",
        "desk_playbook_features.py",
        "desk_playbook_context.py",
        "desk_playbook_evidence.py",
    ):
        assert not pattern.search((RESEARCH_DIR / name).read_text()), name
    assert pattern.search("from .desk_playbook_cohort import fold_cohorts\n")  # seeded


def test_the_register_is_clean():
    assert find_violations(COHORT_REGISTER) == []
    assert find_violations("this cohort has an edge, you should buy now") != []


# --- the route ---------------------------------------------------------------------------------------


@pytest.fixture
def cohort_client(tmp_path):
    playbook_dir = tmp_path / "playbook"
    playbook_dir.mkdir(parents=True)
    store = PlaybookStore(playbook_dir)
    meta = store.record(
        session_date="2026-08-07",
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature="sig-abc",
        payload_version=3,
        parameters={"rail_max_touches_per_row": 8, "signal_measures": ["1h"]},
        register="",
        signals=[_signal("jbe", "long", _forward(100.0, 110.0))],
        absences=[],
        diagnostics=[],
        summary={"jbe:long": {}},
    )
    app.dependency_overrides[get_playbook_store] = lambda: store
    app.dependency_overrides[get_playbook_context_cache] = lambda: None
    with TestClient(app) as client:
        yield client, meta["id"]
    app.dependency_overrides.pop(get_playbook_store, None)
    app.dependency_overrides.pop(get_playbook_context_cache, None)


def test_the_default_body_is_unchanged_by_the_flags_existence(cohort_client):
    """Load-bearing: /structure reads this route for one caption and must not pay for a block it
    never renders — and the route's existing exact-equality test must stay true."""
    client, record_id = cohort_client
    body = client.get("/research/desk/playbook/context", params={"id": record_id}).json()
    assert set(body) == {"context"}


def test_the_flag_adds_a_sibling_block_and_leaves_the_context_identical(cohort_client):
    client, record_id = cohort_client
    plain = client.get("/research/desk/playbook/context", params={"id": record_id}).json()
    flagged = client.get(
        "/research/desk/playbook/context", params={"id": record_id, "cohorts": "true"}
    ).json()
    assert set(flagged) == {"context", "cohort_summaries"}
    assert flagged["context"] == plain["context"]
    assert set(flagged["cohort_summaries"]["cohorts"]) == set(PLAYBOOK_COHORT_KEYS)


def test_an_unknown_id_is_an_honest_null_on_both_keys(cohort_client):
    client, _ = cohort_client
    body = client.get(
        "/research/desk/playbook/context", params={"id": "playbook-nope", "cohorts": "true"}
    ).json()
    assert body == {"context": None, "cohort_summaries": None}


def test_a_malformed_flag_is_refused_rather_than_guessed(cohort_client):
    client, record_id = cohort_client
    response = client.get(
        "/research/desk/playbook/context", params={"id": record_id, "cohorts": "maybe"}
    )
    assert response.status_code == 422
