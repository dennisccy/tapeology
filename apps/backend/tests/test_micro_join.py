"""``micro_join.py`` (Era "The Rapid Microscope" J-03) -- the structure x flow join.

Test-first contract: TC-1 through TC-9 in
``docs/phases/goal-rapid-microscope-iter-3.md``. TC-1/TC-2/TC-3/TC-6 run against the
already-committed ``tests/fixtures/datasets_j03/`` PG SIP dataset, built into a real snapshot via
the existing (already-tested) J-02 pipeline -- this file never re-verifies J-02's own arithmetic,
only that ``micro_join.py`` LOCATES and serves the right rows. TC-4 is a pinned whole-module
byte-freeze (the ``test_referee_guards.py`` precedent). TC-5's ``joinable_corpus`` readiness field
is exercised end to end in ``test_micro_readiness.py`` instead -- this file covers the counting
function it calls into (``joinable_corpus_counts``) directly, over small hermetic fixtures."""

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
from app.research.datasets import DatasetStore
from app.research.desk_playbook import PlaybookStore, playbook_parameters
from app.research.desk_playbook_context import BandMapResolver
from app.research.micro_snapshots import read_snapshot_rows, run_snapshot_build_and_record
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
    assert counts["band_touch_count"] == 0
    assert counts["total"] == 1
    assert counts["by_setup_id"] == {"opening_range_break": 1}


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

    assert counts == {"total": 0, "playbook_signal_count": 0, "band_touch_count": 0, "by_setup_id": {}}


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
