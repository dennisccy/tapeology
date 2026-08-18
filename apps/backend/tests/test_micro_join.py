"""``micro_join.py`` (Era "The Rapid Microscope" J-03) -- the structure x flow join.

Test-first contract: TC-1 through TC-9 in
``docs/phases/goal-rapid-microscope-iter-3.md``. TC-1/TC-2/TC-3/TC-6 run against the
already-committed ``tests/fixtures/datasets_j03/`` PG SIP dataset, built into a real snapshot via
the existing (already-tested) J-02 pipeline -- this file never re-verifies J-02's own arithmetic,
only that ``micro_join.py`` LOCATES and serves the right rows. TC-4 is a pinned whole-module
byte-freeze (the ``test_referee_guards.py`` precedent). TC-5's ``joinable_corpus`` readiness field
is exercised end to end in ``test_micro_readiness.py`` instead -- this file covers the counting
function it calls into (``joinable_corpus_counts``) directly, over small hermetic fixtures.

**iter-4 passenger-fix additions (TC-14, TC-15, TC-16 -- ``docs/phases/goal-rapid-microscope-
iter-4.md``, a DISTINCT numbering scope from this file's own iter-3 TC-1..9 above):** a corrupt
playbook record now surfaces in ``playbook_integrity_errors`` rather than silently vanishing from
the count (TC-14); ``band_touch_count`` is now a typed ``{"status": "not_enumerated", "count":
None}`` rather than a bare ``0`` a reader could mistake for a real zero (TC-15); the REAL-corpus
enumerated arithmetic (``playbook_signal_count``/``by_setup_id``) is unchanged by either fix
(TC-16)."""

from __future__ import annotations

import hashlib
import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.config import CONFIG
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import desk_playbook as desk_playbook_module
from app.research import desk_playbook_context as desk_playbook_context_module
from app.research import micro_join
from app.research import vault
from app.research.datasets import DatasetStore
from app.research.desk_playbook import PlaybookStore, playbook_parameters
from app.research.desk_playbook_context import BandMapResolver
from app.research.micro_snapshots import read_snapshot_rows, resolve_micro_snapshots_dir, run_snapshot_build_and_record
from app.research.tradability_cache import TradabilityCache

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "datasets_j03"
PG_DATASET_ID = "5232fa672b7b4077a5117d34b14c807d"


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


# --- shared fixture: the real PG snapshot, built once per module (577 trades -- cheap) -------------


@pytest.fixture(scope="module")
def pg_snapshot(tmp_path_factory):
    dataset_store = DatasetStore(FIXTURES_DIR)
    snapshots_dir = str(tmp_path_factory.mktemp("micro_join_snapshots"))
    run_snapshot_build_and_record(dataset_store, CONFIG, snapshots_dir, [PG_DATASET_ID])
    rows = read_snapshot_rows(snapshots_dir, PG_DATASET_ID)
    dataset_meta = dataset_store.get(PG_DATASET_ID)
    return {
        "dataset_store": dataset_store,
        "snapshots_dir": snapshots_dir,
        "rows": rows,
        "trade_rows": [r for r in rows if not r.get("close_out")],
        "dataset_meta": dataset_meta,
    }


def _trigger_epoch(dataset_meta: dict, logical_ts: float) -> float:
    return dataset_meta["epoch_anchor"] + logical_ts


# --- TC-1: the feature-at-trigger row matches the nearest at-or-before row -------------------------


def test_tc1_feature_at_trigger_matches_the_row_pinned_exactly_at_the_trigger(pg_snapshot):
    trade_rows = pg_snapshot["trade_rows"]
    dataset_meta = pg_snapshot["dataset_meta"]
    trigger_row = trade_rows[49]  # an arbitrary, comfortably-interior trade
    trigger_epoch = _trigger_epoch(dataset_meta, trigger_row["anchor_at"])
    signal = {"symbol": "PG", "trigger_ts": _iso(trigger_epoch), "setup_id": "fixture_probe"}

    result = micro_join.join_playbook_signal(
        signal, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
    )

    assert result["status"] == micro_join.JOIN_STATUS_JOINED
    assert result["dataset_id"] == PG_DATASET_ID
    feature = result["feature_at_trigger"]
    assert feature["cumulative_delta"] == pytest.approx(trigger_row["cumulative_delta"])
    assert feature["spread"] == pytest.approx(trigger_row["spread"])
    assert feature["tape_state"] == trigger_row["tape_state"]
    assert feature["trade_index"] == trigger_row["trade_index"]


def test_tc1_a_trigger_strictly_between_two_rows_never_picks_the_later_one(pg_snapshot):
    """Proves "nearest AT-OR-BEFORE, never after" precisely: a trigger sitting strictly between
    two consecutive trade rows must resolve to the EARLIER one."""
    trade_rows = pg_snapshot["trade_rows"]
    dataset_meta = pg_snapshot["dataset_meta"]
    earlier, later = trade_rows[49], trade_rows[50]
    assert later["anchor_at"] > earlier["anchor_at"]
    midpoint_logical = (earlier["anchor_at"] + later["anchor_at"]) / 2.0
    trigger_epoch = _trigger_epoch(dataset_meta, midpoint_logical)
    signal = {"symbol": "PG", "trigger_ts": _iso(trigger_epoch), "setup_id": "fixture_probe"}

    result = micro_join.join_playbook_signal(
        signal, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
    )

    assert result["feature_at_trigger"]["trade_index"] == earlier["trade_index"]


def test_a_trigger_before_the_first_trade_is_an_honest_absence_not_a_fabricated_row(pg_snapshot):
    trade_rows = pg_snapshot["trade_rows"]
    dataset_meta = pg_snapshot["dataset_meta"]
    before_first = trade_rows[0]["anchor_at"] - 0.5
    trigger_epoch = _trigger_epoch(dataset_meta, before_first)
    signal = {"symbol": "PG", "trigger_ts": _iso(trigger_epoch), "setup_id": "fixture_probe"}

    result = micro_join.join_playbook_signal(
        signal, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
    )

    assert result["status"] == micro_join.JOIN_STATUS_NO_ROW_BEFORE_TRIGGER
    assert result["feature_at_trigger"] is None
    assert result["outcomes"] == []


def test_a_trigger_outside_every_recorded_window_is_no_covering_snapshot(pg_snapshot):
    signal = {"symbol": "PG", "trigger_ts": "2099-01-01T00:00:00Z", "setup_id": "fixture_probe"}

    result = micro_join.join_playbook_signal(
        signal, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
    )

    assert result["status"] == micro_join.JOIN_STATUS_NO_COVERING_SNAPSHOT
    assert result["feature_at_trigger"] is None


def test_an_unknown_symbol_is_no_covering_snapshot(pg_snapshot):
    dataset_meta = pg_snapshot["dataset_meta"]
    trigger_epoch = _trigger_epoch(dataset_meta, 5.0)
    signal = {"symbol": "NOPE", "trigger_ts": _iso(trigger_epoch)}

    result = micro_join.join_playbook_signal(
        signal, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
    )

    assert result["status"] == micro_join.JOIN_STATUS_NO_COVERING_SNAPSHOT


def test_a_signal_missing_symbol_or_trigger_ts_is_an_honest_absence_never_a_crash(pg_snapshot):
    for broken in [{"trigger_ts": "2026-06-09T17:02:05Z"}, {"symbol": "PG"}]:
        result = micro_join.join_playbook_signal(
            broken, pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG
        )
        assert result["status"] == micro_join.JOIN_STATUS_NO_COVERING_SNAPSHOT
        assert result["feature_at_trigger"] is None


# --- TC-3: the lookahead assertion -------------------------------------------------------------------


def test_tc3_lookahead_no_returned_feature_row_ever_exceeds_its_own_trigger(pg_snapshot):
    trade_rows = pg_snapshot["trade_rows"]
    rows = pg_snapshot["rows"]
    # A grid sampled across the whole stream (every 23rd trade -- coprime-ish stride, not just the
    # first few rows) plus the exact-boundary case for each sampled row.
    for row in trade_rows[::23]:
        t = row["anchor_at"]
        matched = micro_join.feature_row_at_trigger(rows, t)
        assert matched is not None
        assert matched["anchor_at"] <= t, "a matched row's own anchor must never exceed the trigger"
        assert matched["anchor_at"] == t  # the exact row itself, since t IS one of its own anchors


def test_tc3_lookahead_holds_at_every_consecutive_pair_gap(pg_snapshot):
    trade_rows = pg_snapshot["trade_rows"]
    rows = pg_snapshot["rows"]
    for earlier, later in zip(trade_rows[::31], trade_rows[1::31]):
        if later["anchor_at"] <= earlier["anchor_at"]:
            continue
        probe_t = later["anchor_at"] - 1e-6
        matched = micro_join.feature_row_at_trigger(rows, probe_t)
        assert matched["anchor_at"] <= probe_t
        assert matched["anchor_at"] != later["anchor_at"], "must never jump ahead to the later row"


# --- TC-6: the unavailable flag on a deferred construct survives the join verbatim ------------------


def test_tc6_unavailable_deferred_completion_survives_the_join_verbatim():
    rows = [
        {
            "anchor_at": 1.0, "observed_through": 1.0, "available_at": 1.0, "trade_index": 1,
            "side": "buy", "price": 100.0, "mid": 100.0, "spread": 0.02, "tape_state": "trending_up",
            "cumulative_delta": 5.0,
            "deferred": [
                {
                    "kind": "response_asymmetry", "side": "buy", "anchor_at": 0.5,
                    "observed_through": 1.0, "available_at": 1.0, "value": None, "unavailable": True,
                }
            ],
        }
    ]
    matched = micro_join.feature_row_at_trigger(rows, 1.0)
    assert matched["deferred"][0]["unavailable"] is True
    assert matched["deferred"][0]["value"] is None  # never coerced to a number


def test_tc6_a_refused_cross_basis_completion_also_survives_verbatim():
    """The section 2.6 refusal shape (``refused``/``refusal_reason``) is a DIFFERENT closed-
    vocabulary state from ``unavailable`` -- both must ride through the join untouched."""
    rows = [
        {
            "anchor_at": 2.0, "observed_through": 2.0, "available_at": 2.0, "trade_index": 2,
            "side": "sell", "price": 99.0, "mid": 99.0, "spread": 0.02, "tape_state": "trending_down",
            "cumulative_delta": -3.0,
            "deferred": [
                {
                    "kind": "quote_depletion", "side": "bid", "anchor_at": 1.0,
                    "observed_through": 2.0, "available_at": 2.0, "value": None, "unavailable": False,
                    "refused": True, "refusal_reason": "cross_basis_unverified_quote_size_unit",
                }
            ],
        }
    ]
    matched = micro_join.feature_row_at_trigger(rows, 2.0)
    assert matched["deferred"][0]["refused"] is True
    assert matched["deferred"][0]["refusal_reason"] == "cross_basis_unverified_quote_size_unit"


# --- TC-4: the detector/context byte-freeze guard (the test_referee_guards.py precedent) ------------

# Recorded BEFORE this iteration touches anything -- goal.md's own Non-Goal: "No detector,
# threshold, or context change of any kind" / "no change to desk_playbook.py, desk_playbook_
# context.py". These two files carry ZERO diff this iteration; both hashes must still match at the
# end of it too.
_DESK_PLAYBOOK_MODULE_SHA256 = "f059dcba80a7f09db8bcf74c4d2234c28aee5df2fb6bca32685cb30f8ba55bea"
_DESK_PLAYBOOK_CONTEXT_MODULE_SHA256 = "75537d161661b9660cf82896c56b60d92acdf3179fd77bd041c38ae45530fc23"


def test_tc4_desk_playbook_module_is_byte_unchanged_this_iteration():
    source = inspect.getsource(desk_playbook_module)
    assert hashlib.sha256(source.encode()).hexdigest() == _DESK_PLAYBOOK_MODULE_SHA256


def test_tc4_desk_playbook_context_module_is_byte_unchanged_this_iteration():
    source = inspect.getsource(desk_playbook_context_module)
    assert hashlib.sha256(source.encode()).hexdigest() == _DESK_PLAYBOOK_CONTEXT_MODULE_SHA256


def test_tc4_byte_freeze_guard_can_fail_on_a_seeded_violation():
    """A lint that cannot fail proves nothing."""
    source = inspect.getsource(desk_playbook_module)
    real_hash = hashlib.sha256(source.encode()).hexdigest()
    assert real_hash != "0" * 64


# --- the outcome set: horizons, truncation, the spread cost-proxy column ---------------------------


def test_outcome_rows_cover_every_spec_section_1_horizon_family(pg_snapshot):
    trade_rows = pg_snapshot["trade_rows"]
    rows = pg_snapshot["rows"]
    dataset_meta = pg_snapshot["dataset_meta"]
    anchor_row = trade_rows[9]  # early in the window -- plenty of trailing trades/shares/seconds
    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)

    outcomes = micro_join.outcome_rows_after_trigger(rows, anchor_row, session_end_ts)

    kinds_values = [(o["horizon_kind"], o["horizon_value"]) for o in outcomes]
    assert kinds_values == [
        ("trades", 20), ("trades", 100),
        ("shares", 5_000), ("shares", 50_000),
        ("clock_seconds", 30), ("clock_seconds", 60), ("clock_seconds", 300),
    ]
    for outcome in outcomes:
        assert outcome["mid"]["basis"] == "mid"
        assert outcome["last_trade"]["basis"] == "last_trade"
        assert "spread_at_outcome_start_bps" in outcome
        # the cost-proxy column is never netted into either outcome's own value (spec section 4):
        # it is a THIRD, independent key, not part of either outcome dict.
        assert "spread_at_outcome_start_bps" not in outcome["mid"]
        assert "spread_at_outcome_start_bps" not in outcome["last_trade"]


def test_the_trades_20_horizon_matches_an_independently_computed_reference(pg_snapshot):
    """A reference computed a SECOND, obviously-correct way (plain list indexing in the test
    itself, not through any of micro_join.py's own helpers) -- the "hand-computed" oracle TC-1's
    acceptance describes, applied to an outcome instead of the feature-at-trigger row."""
    trade_rows = pg_snapshot["trade_rows"]
    rows = pg_snapshot["rows"]
    dataset_meta = pg_snapshot["dataset_meta"]
    anchor_pos = 9
    anchor_row = trade_rows[anchor_pos]
    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)
    expected_horizon_row = trade_rows[anchor_pos + 20]
    assert expected_horizon_row["anchor_at"] <= session_end_ts  # sanity: not truncated

    outcomes = micro_join.outcome_rows_after_trigger(rows, anchor_row, session_end_ts)
    trades_20 = next(o for o in outcomes if o["horizon_kind"] == "trades" and o["horizon_value"] == 20)

    expected_mid_move = expected_horizon_row["mid"] - anchor_row["mid"]
    assert trades_20["mid"]["value"] == pytest.approx(expected_mid_move)
    assert trades_20["mid"]["truncated"] is False
    assert trades_20["mid"]["unmeasured"] is False
    expected_spread_bps = anchor_row["spread"] / anchor_row["mid"] * 10_000.0
    assert trades_20["spread_at_outcome_start_bps"] == pytest.approx(expected_spread_bps)


def test_a_horizon_beyond_the_recorded_stream_is_truncated_never_measured_off_the_last_trade(pg_snapshot):
    trade_rows = pg_snapshot["trade_rows"]
    rows = pg_snapshot["rows"]
    dataset_meta = pg_snapshot["dataset_meta"]
    anchor_row = trade_rows[-3]  # near the very end of the 577-trade window
    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)

    outcomes = micro_join.outcome_rows_after_trigger(rows, anchor_row, session_end_ts)

    trades_100 = next(o for o in outcomes if o["horizon_kind"] == "trades" and o["horizon_value"] == 100)
    assert trades_100["mid"]["truncated"] is True
    assert trades_100["mid"]["value"] is None
    assert trades_100["last_trade"]["truncated"] is True
    clock_300 = next(o for o in outcomes if o["horizon_kind"] == "clock_seconds" and o["horizon_value"] == 300)
    assert clock_300["mid"]["truncated"] is True
    assert clock_300["mid"]["value"] is None


# --- TC-2: the band-map wall touch join -------------------------------------------------------------


class _EmptyBarStore:
    def __init__(self, root="/tmp/does-not-exist-micro-join-test"):
        self.root = root

    def list(self):
        return [], []


def _resolver(tmp_path) -> BandMapResolver:
    return BandMapResolver(
        _EmptyBarStore(), CONFIG, cache=TradabilityCache(str(tmp_path / "trad.db"))
    )


def test_tc2_a_cached_band_map_joins_the_matching_feature_and_outcome_rows(pg_snapshot, tmp_path):
    trade_rows = pg_snapshot["trade_rows"]
    dataset_meta = pg_snapshot["dataset_meta"]
    resolver = _resolver(tmp_path)
    touch_row = trade_rows[19]
    as_of_epoch = _trigger_epoch(dataset_meta, touch_row["anchor_at"])
    fixture_map = {"basis_day": "2026-06-09", "bands": [{"kind": "support", "low": 148.0, "high": 149.0}]}
    resolver._cache.publish(resolver.map_key("PG", as_of_epoch), fixture_map)

    result = micro_join.join_band_touch(
        {"symbol": "PG", "as_of_epoch": as_of_epoch}, resolver,
        pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG,
    )

    assert result["status"] == micro_join.JOIN_STATUS_JOINED
    assert result["band_map"] == fixture_map
    assert result["feature_at_trigger"]["trade_index"] == touch_row["trade_index"]
    assert len(result["outcomes"]) == 7


def test_tc2_an_uncached_band_map_is_an_honest_absence_never_a_fabricated_wall(pg_snapshot, tmp_path):
    dataset_meta = pg_snapshot["dataset_meta"]
    resolver = _resolver(tmp_path)  # nothing published -- a genuine miss
    as_of_epoch = _trigger_epoch(dataset_meta, 5.0)

    result = micro_join.join_band_touch(
        {"symbol": "PG", "as_of_epoch": as_of_epoch}, resolver,
        pg_snapshot["dataset_store"], pg_snapshot["snapshots_dir"], CONFIG,
    )

    assert result["status"] == micro_join.JOIN_STATUS_NO_BAND_CONTEXT
    assert result["band_map"] is None
    assert result["feature_at_trigger"] is None
    assert result["outcomes"] == []


# --- joinable_corpus_counts (micro_readiness.py's new field; TC-5's own computation) -----------------


def _plant_events(symbol: str) -> list:
    return [
        QuoteEvent(symbol, 0.0, 99.99, 100.02, 100, 100),
        TradeEvent(symbol, 0.1, 100.0, 10, Side.BUY),
        TradeEvent(symbol, 0.2, 100.0, 10, Side.SELL),
    ]


def _plant_dataset(store: DatasetStore, *, symbol: str, window_start_utc: str, window_end_utc: str) -> dict:
    return store.record(
        symbol=symbol, source="fixture", source_kind="fixture", source_id=f"{symbol}-fixture",
        split="train", window_start_utc=window_start_utc, window_end_utc=window_end_utc,
        data_feed="sip", epoch_anchor=0.0, events=_plant_events(symbol),
    )


def _plant_playbook_signal(
    store: PlaybookStore, *, session_date: str, playbook_input_signature: str, signals: list[dict]
) -> dict:
    return store.record(
        session_date=session_date,
        config_fingerprint=CONFIG.config_fingerprint(),
        playbook_input_signature=playbook_input_signature,
        payload_version=1,
        parameters=playbook_parameters(),
        register="",
        signals=signals,
        absences=[],
        diagnostics=[],
    )


def test_joinable_corpus_counts_only_counts_signals_inside_a_recorded_tick_window(tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _plant_dataset(
        dataset_store, symbol="ZJN",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
    )
    playbook_store = PlaybookStore(tmp_path / "playbook")
    inside = {"symbol": "ZJN", "setup_id": "opening_range_break", "trigger_ts": "2026-06-09T13:00:30Z"}
    outside = {"symbol": "ZJN", "setup_id": "opening_range_break", "trigger_ts": "2026-06-09T14:00:00Z"}
    no_ticks_for_symbol = {"symbol": "OTHER", "setup_id": "jbe", "trigger_ts": "2026-06-09T13:00:30Z"}
    missing_trigger = {"symbol": "ZJN", "setup_id": "jbe"}
    _plant_playbook_signal(
        playbook_store, session_date="2026-06-09", playbook_input_signature="sig-1",
        signals=[inside, outside, no_ticks_for_symbol, missing_trigger],
    )

    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)

    assert counts["playbook_signal_count"] == 1
    assert counts["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None}
    assert counts["total"] == 1
    assert counts["by_setup_id"] == {"opening_range_break": 1}
    assert counts["playbook_integrity_errors"] == []


def test_joinable_corpus_counts_breaks_down_by_setup_id(tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _plant_dataset(
        dataset_store, symbol="ZJN",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
    )
    playbook_store = PlaybookStore(tmp_path / "playbook")
    signals = [
        {"symbol": "ZJN", "setup_id": "opening_range_break", "trigger_ts": "2026-06-09T13:00:10Z"},
        {"symbol": "ZJN", "setup_id": "jbe", "trigger_ts": "2026-06-09T13:00:20Z"},
        {"symbol": "ZJN", "setup_id": "jbe", "trigger_ts": "2026-06-09T13:00:30Z"},
    ]
    _plant_playbook_signal(
        playbook_store, session_date="2026-06-09", playbook_input_signature="sig-2", signals=signals
    )

    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)

    assert counts["total"] == 3
    assert counts["by_setup_id"] == {"opening_range_break": 1, "jbe": 2}


def test_joinable_corpus_counts_is_an_honest_zero_with_no_playbook_records(tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    playbook_store = PlaybookStore(tmp_path / "playbook")

    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)

    assert counts == {
        "total": 0,
        "playbook_signal_count": 0,
        "band_touch_count": {"status": micro_join.BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None},
        "by_setup_id": {},
        "playbook_integrity_errors": [],
        # spec section 7.5 point 6 (r4): the enumerator's own disclosure of what it left out.
        "withheld_excluded": 0,
    }


def test_joinable_corpus_counts_fails_closed_on_a_malformed_trigger_ts_never_silently_undercounts(tmp_path):
    """A trigger_ts that IS present but unparseable is a corrupted record, not a structural
    absence -- it must raise, never be silently skipped (the iter-2 completeness lesson)."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _plant_dataset(
        dataset_store, symbol="ZJN",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
    )
    playbook_store = PlaybookStore(tmp_path / "playbook")
    _plant_playbook_signal(
        playbook_store, session_date="2026-06-09", playbook_input_signature="sig-3",
        signals=[{"symbol": "ZJN", "setup_id": "jbe", "trigger_ts": "not-a-timestamp"}],
    )

    with pytest.raises(ValueError):
        micro_join.joinable_corpus_counts(dataset_store, playbook_store)


# --- find_covering_dataset / find_covering_snapshot ---------------------------------------------------


def test_find_covering_dataset_ties_break_on_created_utc_then_id(tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    older = _plant_dataset(
        dataset_store, symbol="ZJN",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T14:00:00Z",
    )
    result = micro_join.find_covering_dataset(
        "ZJN", micro_join.parse_utc_epoch("2026-06-09T13:30:00Z"), dataset_store
    )
    assert result["id"] == older["id"]


def test_find_covering_snapshot_is_none_without_a_built_snapshot(tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    _plant_dataset(
        dataset_store, symbol="ZJN",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
    )
    snapshots_dir = str(tmp_path / "micro_snapshots_never_built")
    result = micro_join.find_covering_snapshot(
        "ZJN", micro_join.parse_utc_epoch("2026-06-09T13:00:10Z"), dataset_store, snapshots_dir, CONFIG
    )
    assert result is None


# --- TC-14 (iter-4 passenger fix): a corrupt playbook record surfaces honestly, never a silent
# undercount --------------------------------------------------------------------------------------


def test_tc14_a_corrupted_playbook_record_surfaces_in_playbook_integrity_errors(tmp_path):
    """Mirrors ``test_micro_readiness.py``'s own ``test_corrupted_dataset_is_surfaced_never_
    dropped_never_a_crash`` precedent, applied to the PLAYBOOK store's own on-disk shape (the same
    ``{"file_checksum": ..., "record": {...}}`` envelope every store in this codebase hashes)."""
    import json

    dataset_store = DatasetStore(tmp_path / "datasets")
    _plant_dataset(
        dataset_store, symbol="ZJN",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
    )
    playbook_store = PlaybookStore(tmp_path / "playbook")
    healthy = _plant_playbook_signal(
        playbook_store, session_date="2026-06-09", playbook_input_signature="sig-healthy",
        signals=[{"symbol": "ZJN", "setup_id": "opening_range_break", "trigger_ts": "2026-06-09T13:00:10Z"}],
    )
    corrupted = _plant_playbook_signal(
        playbook_store, session_date="2026-06-10", playbook_input_signature="sig-corrupt",
        signals=[{"symbol": "ZJN", "setup_id": "jbe", "trigger_ts": "2026-06-10T13:00:10Z"}],
    )
    corrupted_path = playbook_store._path(corrupted["id"])
    payload = json.loads(corrupted_path.read_text())
    payload["record"]["meta"]["session_date"] = "tampered"
    corrupted_path.write_text(json.dumps(payload))

    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)

    assert len(counts["playbook_integrity_errors"]) == 1
    assert counts["playbook_integrity_errors"][0]["file"] == corrupted_path.name
    # the healthy record is NEVER dropped alongside the corrupted one -- never a silent full
    # undercount just because ONE other file failed verification.
    assert counts["playbook_signal_count"] == 1
    assert counts["by_setup_id"] == {"opening_range_break": 1}
    assert counts["total"] == 1


def test_tc14_healthy_playbook_records_still_count_when_none_are_corrupted(tmp_path):
    """A lint that can fail proves something: the healthy path still serves an EMPTY error list,
    never a fabricated one."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    _plant_dataset(
        dataset_store, symbol="ZJN",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
    )
    playbook_store = PlaybookStore(tmp_path / "playbook")
    _plant_playbook_signal(
        playbook_store, session_date="2026-06-09", playbook_input_signature="sig-clean",
        signals=[{"symbol": "ZJN", "setup_id": "opening_range_break", "trigger_ts": "2026-06-09T13:00:10Z"}],
    )
    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
    assert counts["playbook_integrity_errors"] == []
    assert counts["playbook_signal_count"] == 1


# --- TC-15 (iter-4 passenger fix): band_touch_count is a typed "not enumerated" state --------------


def test_tc15_band_touch_count_is_a_typed_not_enumerated_state_never_a_bare_zero(tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    playbook_store = PlaybookStore(tmp_path / "playbook")
    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
    band_touch = counts["band_touch_count"]
    assert not isinstance(band_touch, int)  # never a bare int a reader could read as "counted zero"
    assert band_touch == {"status": micro_join.BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None}
    assert band_touch["status"] == "not_enumerated"
    assert band_touch["count"] is None


def test_tc15_band_touch_count_shape_is_a_fresh_dict_every_call_never_shared_mutable_state(tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    playbook_store = PlaybookStore(tmp_path / "playbook")
    first = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
    first["band_touch_count"]["count"] = 999  # mutate the caller's own copy
    second = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
    assert second["band_touch_count"]["count"] is None  # unaffected by the earlier mutation


# --- TC-16: the real-corpus enumerated arithmetic is unchanged by either passenger fix --------------


def test_tc16_real_corpus_joinable_corpus_arithmetic_is_unchanged_by_the_passenger_fixes():
    """Against the REAL ``.data/datasets`` + playbook stores (a direct call against the real
    stores, per the phase spec's own TC-16 wording -- not the browser rig): ``playbook_signal_
    count`` stays ``2`` and ``by_setup_id`` stays ``{"range_trade": 2}`` -- the fixes changed only
    corruption-surfacing and the ``band_touch_count``/``total`` representation, never the
    enumerated arithmetic itself."""
    from app.research.desk_playbook import resolve_desk_playbook_dir

    dataset_store = DatasetStore(CONFIG.dataset_dir_resolved())
    playbook_store = PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))

    counts = micro_join.joinable_corpus_counts(dataset_store, playbook_store)

    assert counts["playbook_signal_count"] == 2
    assert counts["by_setup_id"] == {"range_trade": 2}
    assert counts["total"] == 2  # total == playbook_signal_count alone now (module docstring)
    assert counts["playbook_integrity_errors"] == []  # the real corpus is healthy
    assert counts["band_touch_count"] == {"status": micro_join.BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None}


# --- J-05 TC-4: the accessor re-point (micro_accessor.MicroAccessor, unfenced) serves the SAME ------
# --- real-corpus join result as the pre-re-point direct micro_snapshots.read_snapshot_rows call. ----


def test_tc4_real_corpus_join_playbook_signal_is_unaffected_by_the_accessor_re_point():
    """The ONE real recorded playbook signal whose window falls inside a recorded tick dataset AND
    already carries a currently-valid built snapshot on disk (verified live, not assumed) --
    ``_join_core``'s re-pointed ``MicroAccessor(...).read_snapshot_rows(...)`` call (J-05) must
    still resolve this join exactly as the pre-re-point direct call did: ``status == "joined"``, a
    non-``None`` ``feature_at_trigger``, and a full closed outcome set."""
    from app.research.desk_playbook import resolve_desk_playbook_dir

    dataset_store = DatasetStore(CONFIG.dataset_dir_resolved())
    playbook_store = PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))
    snapshots_dir = resolve_micro_snapshots_dir(CONFIG.dataset_dir_resolved())

    playbook_records, _errors = playbook_store.list()
    signal = None
    for record in playbook_records:
        for candidate in record.get("signals") or []:
            if candidate.get("symbol") == "AMZN" and candidate.get("trigger_ts") == "2026-06-26T16:20:00.000000Z":
                signal = candidate
                break
        if signal is not None:
            break
    assert signal is not None, "the fixed real-corpus signal this test pins is no longer on disk"

    result = micro_join.join_playbook_signal(signal, dataset_store, snapshots_dir, CONFIG)
    assert result["status"] == micro_join.JOIN_STATUS_JOINED
    assert result["feature_at_trigger"] is not None
    assert result["dataset_id"] == "60e0cd6613804fdaa87d549dcef38d31"
    assert len(result["outcomes"]) == 7  # the closed outcome set: 2 trades + 2 shares + 3 clock


# --- iter-4 perf fix: outcome_rows_at_position / outcome_row_at_single_horizon are byte-identical
# to outcome_rows_after_trigger's own output -- added when a live Scout run against the real
# 18-dataset corpus (J-04) exposed an O(n^2) cost in the O(n) `.index()` lookup + a per-call
# O(n) slice copy inside `_shares_horizon_row`/`_clock_horizon_row`; both are rewritten here to
# avoid an O(n)-per-call cost, with zero output change -----------------------------------------


def test_outcome_rows_at_position_matches_outcome_rows_after_trigger_exactly(pg_snapshot):
    trade_rows = pg_snapshot["trade_rows"]
    rows = pg_snapshot["rows"]
    dataset_meta = pg_snapshot["dataset_meta"]
    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)

    for anchor_pos in (0, 9, 49, 50, len(trade_rows) - 3, len(trade_rows) - 1):
        anchor_row = trade_rows[anchor_pos]
        via_trigger = micro_join.outcome_rows_after_trigger(rows, anchor_row, session_end_ts, side=None)
        via_position = micro_join.outcome_rows_at_position(trade_rows, anchor_pos, session_end_ts, side=None)
        assert via_position == via_trigger


def test_outcome_rows_at_position_matches_with_a_hypothesis_side(pg_snapshot):
    trade_rows = pg_snapshot["trade_rows"]
    rows = pg_snapshot["rows"]
    dataset_meta = pg_snapshot["dataset_meta"]
    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)
    anchor_pos = 9
    anchor_row = trade_rows[anchor_pos]

    via_trigger = micro_join.outcome_rows_after_trigger(rows, anchor_row, session_end_ts, side="buy")
    via_position = micro_join.outcome_rows_at_position(trade_rows, anchor_pos, session_end_ts, side="buy")
    assert via_position == via_trigger


def test_outcome_row_at_single_horizon_matches_the_corresponding_entry_of_the_full_closed_set(pg_snapshot):
    trade_rows = pg_snapshot["trade_rows"]
    dataset_meta = pg_snapshot["dataset_meta"]
    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)

    horizon_pairs = [
        ("trades", 20), ("trades", 100),
        ("shares", 5_000), ("shares", 50_000),
        ("clock_seconds", 30), ("clock_seconds", 60), ("clock_seconds", 300),
    ]
    for anchor_pos in (9, 49, len(trade_rows) - 3):
        full_set = micro_join.outcome_rows_at_position(trade_rows, anchor_pos, session_end_ts, side=None)
        for kind, value in horizon_pairs:
            single = micro_join.outcome_row_at_single_horizon(
                trade_rows, anchor_pos, kind, value, session_end_ts, side=None
            )
            expected = next(o for o in full_set if o["horizon_kind"] == kind and o["horizon_value"] == value)
            assert single == expected


def test_outcome_row_at_single_horizon_rejects_an_unknown_horizon_kind(pg_snapshot):
    trade_rows = pg_snapshot["trade_rows"]
    dataset_meta = pg_snapshot["dataset_meta"]
    session_end_ts = micro_join._session_end_logical_ts(dataset_meta)
    with pytest.raises(ValueError):
        micro_join.outcome_row_at_single_horizon(trade_rows, 9, "not-a-real-kind", 20, session_end_ts)


def test_shares_and_clock_horizon_rows_are_unchanged_by_the_index_iteration_rewrite(pg_snapshot):
    """A hand-computed oracle over the SAME small fixture TC-1 already trusts: the rewritten
    ``_shares_horizon_row``/``_clock_horizon_row`` (index iteration, never a slice copy) return
    the identical row a naive, obviously-correct reference implementation finds."""
    trade_rows = pg_snapshot["trade_rows"]
    anchor_pos = 9

    def _reference_shares_horizon_row(threshold):
        cumulative = 0.0
        for row in trade_rows[anchor_pos + 1 :]:
            cumulative += row["size"]
            if cumulative >= threshold:
                return row
        return None

    def _reference_clock_horizon_row(horizon_ts):
        candidate = None
        for row in trade_rows[anchor_pos:]:
            if row["anchor_at"] <= horizon_ts:
                candidate = row
            else:
                break
        return candidate

    assert micro_join._shares_horizon_row(trade_rows, anchor_pos, 5_000) == _reference_shares_horizon_row(5_000)
    assert micro_join._shares_horizon_row(trade_rows, anchor_pos, 50_000) == _reference_shares_horizon_row(50_000)
    horizon_ts = trade_rows[anchor_pos]["anchor_at"] + 60
    assert micro_join._clock_horizon_row(trade_rows, anchor_pos, horizon_ts) == _reference_clock_horizon_row(horizon_ts)


# --- spec section 7.5 point 6 (r4): the seal-aware enumerator + its disclosure -------------------
# iter-9 audit finding B5: `micro_readiness` already excludes a withheld shard from
# `totals.distinct_datasets`, but this counter enumerated the store itself and counted the SAME
# shard's window as joinable evidence -- two numbers in one payload, one excluding sealed shards
# and one including them.


def _seal(dataset_store: DatasetStore, meta: dict, *, universe_id: str = "starter-tranche-v1") -> None:
    """Seal one already-recorded dataset through the vault's OWN public lifecycle entry point
    (never a hand-written ledger line), resolved from THIS store's own directory."""
    vault.seal_shard(
        vault.shard_ledger_for_dataset_dir(str(dataset_store.root)),
        dataset_id=meta["id"],
        universe_id=universe_id,
        content_checksum=meta["checksum"],
        event_count=meta["event_counts"]["total"],
        vault_secret=b"micro-join-fixture-secret",
    )


def test_r4_a_withheld_shards_window_never_counts_as_joinable_evidence(tmp_path):
    """A signal whose ONLY covering tick window belongs to a withheld Validation-Vault shard is
    not joinable evidence -- and the count that dropped is DISCLOSED, never silently shrunk."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    sealed_meta = _plant_dataset(
        dataset_store, symbol="ZJN",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
    )
    _plant_dataset(
        dataset_store, symbol="PBL",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
    )
    playbook_store = PlaybookStore(tmp_path / "playbook")
    _plant_playbook_signal(
        playbook_store, session_date="2026-06-09", playbook_input_signature="sig-r4",
        signals=[
            {"symbol": "ZJN", "setup_id": "opening_range_break", "trigger_ts": "2026-06-09T13:00:30Z"},
            {"symbol": "PBL", "setup_id": "jbe", "trigger_ts": "2026-06-09T13:00:30Z"},
        ],
    )

    before = micro_join.joinable_corpus_counts(dataset_store, playbook_store)
    assert before["total"] == 2
    assert before["by_setup_id"] == {"opening_range_break": 1, "jbe": 1}
    assert before["withheld_excluded"] == 0  # an empty vault withholds nothing

    _seal(dataset_store, sealed_meta)
    after = micro_join.joinable_corpus_counts(dataset_store, playbook_store)

    assert after["total"] == 1  # only the PUBLIC sibling's signal remains joinable
    assert after["by_setup_id"] == {"jbe": 1}
    assert after["withheld_excluded"] == 1  # the shrink is stated, never silent
    assert "ZJN" not in str(after) and sealed_meta["id"] not in str(after)  # a COUNT, never an id


def test_r4_find_covering_dataset_refuses_to_hand_back_a_withheld_shard(tmp_path):
    """``find_covering_dataset`` is the door onto a covering SNAPSHOT and therefore onto a shard's
    rows: a withheld shard covering the instant is an honest ``None``, exactly as if no window
    covered it -- never a read of held-out tape."""
    dataset_store = DatasetStore(tmp_path / "datasets")
    meta = _plant_dataset(
        dataset_store, symbol="ZJN",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
    )
    at_epoch = datetime(2026, 6, 9, 13, 0, 30, tzinfo=timezone.utc).timestamp()

    found = micro_join.find_covering_dataset("ZJN", at_epoch, dataset_store)
    assert found is not None and found["id"] == meta["id"]

    _seal(dataset_store, meta)
    assert micro_join.find_covering_dataset("ZJN", at_epoch, dataset_store) is None
