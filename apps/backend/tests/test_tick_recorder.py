"""``tick_recorder.py`` -- Card 5.2, brought forward: the chunked, throttled, resumable tick
recorder (era "The Rapid Microscope" J-06 step 2, ``docs/rapid-validation-spec.md`` section 7.1).

Everything here runs against planted, scoped stores under ``tmp_path`` with a FAKE adapter --
never ``apps/backend/.data``, never a real vendor call, never a real credential (100% hermetic
per this iteration's own scope note). Covers, in order:

  1. Chunk planning purity (TC-1).
  2. The walk: four-outcome classification, resumability, no-partial-dataset-on-failure
     (TC-2/TC-3/TC-4/TC-5).
  3. TR-19 -- the Card-5.1 preservation-field structural gate (TC-8).
  4. Preservation-field round-trip + content-checksum independence (TC-9).
  5. The dated ``quote_size_unit`` vendor-rule stamping (TC-10/TC-11).
  6. The recorder's own throttle (spec section 1: ``RECORDER_PAGE_BUDGET_PER_MINUTE``).
  7. The published sha256 split rule (spec section 7.3, unchanged -- NOT vault.py's new seal
     axis, which stays out of scope this iteration).
  8. Bar pairing through the EXISTING, UNCHANGED ``desk_deep_backfill`` machinery.
"""

from __future__ import annotations

import hashlib
import threading
import time
from datetime import date, timezone
from pathlib import Path

import pytest

from app.config import CONFIG
from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
from app.providers.base import QuoteEvent, TradeEvent
from app.research import tick_recorder as tr
from app.research.datasets import DatasetStore, SPLIT_HOLDOUT, SPLIT_TRAIN
from app.research.micro_snapshots import read_run_log


# --- a hermetic fake adapter -- never the real SDK, never a real vendor call ----------------------


class _FakeTickAdapter:
    """Serves one trade + one quote per requested chunk window, content DERIVED from the chunk's
    own start epoch so distinct chunks never collide (each recorded dataset gets genuinely
    distinct content, never an accidental duplicate-content 409). Counts every call -- the seam
    that proves a reused/checkpointed chunk costs ZERO vendor calls. ``raise_for`` makes
    ``iter_historical_chunks`` raise for exactly the named ``(symbol, start_iso)`` chunks (TC-4's
    targeted single-chunk failure)."""

    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.raise_for: set[tuple[str, str]] = set()

    def is_available(self) -> bool:
        return True

    def warm_symbol_universe(self) -> None:
        pass

    def iter_historical_chunks(self, symbol, start, end):
        # Normalized to the SAME "...Z" shape `tick_recorder._iso_utc` emits (a bare tz-aware
        # `.isoformat()` would print "+00:00" instead, silently missing every `raise_for` lookup).
        start_iso = start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = end.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.calls.append((symbol, start_iso, end_iso))
        if (symbol, start_iso) in self.raise_for:
            raise RuntimeError(f"the vendor said no for {symbol} at {start_iso}")
        epoch = start.timestamp() + 1.0
        trade = RawTrade(
            epoch, 100.0 + (epoch % 50), 10,
            conditions=["@"], exchange="Q", tape="C", trade_id=int(epoch),
        )
        quote = RawQuote(
            epoch, 99.9, 100.1, 200, 300,
            conditions=["R"], tape="C", bid_exchange="Q", ask_exchange="K",
        )
        yield HistoricalWindow(symbol, (trade,), (quote,))


@pytest.fixture
def rec_ctx(tmp_path):
    tr._reset_recorder_throttle_for_tests()
    adapter = _FakeTickAdapter()
    dataset_store = DatasetStore(str(tmp_path / "datasets"))
    checkpoint_store = tr.RecorderCheckpointStore(str(tmp_path / "checkpoints"))
    yield adapter, dataset_store, checkpoint_store
    tr._reset_recorder_throttle_for_tests()


# ==================================================================================================
# 1. Chunk planning: pure, zero I/O (TC-1).
# ==================================================================================================


def test_tc1_the_planner_returns_the_right_count_in_symbol_date_start_order_with_zero_io(tmp_path):
    # 09:30-16:00 ET = 23400s; chunk_seconds=7800 -> exactly 3 chunks/session -> "3 per symbol-day".
    plan = tr.plan_recorder_chunks(
        ["AAPL", "MSFT"], ["2026-06-01", "2026-06-02"], chunk_seconds=7800.0
    )
    assert len(plan) == 12  # 2 symbols x 2 dates x 3 chunks/day
    # Precise (symbol, date, start) ordering: symbol outer, date inner, start ascending within a
    # day -- exactly the order TC-1 requires, and the same order the walker groups on.
    seen = [(c["symbol"], c["date"], c["start"]) for c in plan]
    assert seen == sorted(seen)
    assert {c["symbol"] for c in plan} == {"AAPL", "MSFT"}
    assert {c["date"] for c in plan} == {"2026-06-01", "2026-06-02"}
    from collections import Counter

    counts = Counter((c["symbol"], c["date"]) for c in plan)
    assert set(counts.values()) == {3}  # each symbol-day contributes exactly 3 chunks
    assert len(counts) == 4  # 2 symbols x 2 dates


def test_tc1_two_symbol_days_yield_exactly_six_chunks_the_literal_tc1_fixture_shape():
    plan = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01", "2026-06-02"], chunk_seconds=7800.0)
    assert len(plan) == 6  # 1 symbol x 2 dates x 3 chunks/day = TC-1's own "2 symbol-days ... 6 total"


def test_tc1_planning_touches_no_store_and_no_adapter(tmp_path, rec_ctx):
    adapter, dataset_store, _checkpoint_store = rec_ctx
    tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)
    assert adapter.calls == []
    records, _errors = dataset_store.list()
    assert records == []


def test_the_plan_is_clock_free_and_reproducible():
    first = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)
    second = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)
    assert first == second


def test_a_short_window_yields_exactly_one_chunk_the_default_recorder_chunk_seconds():
    # Default RECORDER_CHUNK_SECONDS (900s) against a full 23400s RTH session -> 26 chunks, never 1
    # -- but a single-day, coarse chunk_seconds proves the "one chunk for a window at/under the
    # chunk size" boundary the same way `split_window`'s own docstring states.
    plan = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=100_000.0)
    assert len(plan) == 1


# ==================================================================================================
# 2. The walk: outcome classification, resumability, no-partial-dataset-on-failure.
# ==================================================================================================


def test_tc2_a_first_walk_fetches_every_chunk_and_records_one_dataset_per_symbol_day(rec_ctx):
    adapter, dataset_store, checkpoint_store = rec_ctx
    chunks = tr.plan_recorder_chunks(
        ["AAPL", "MSFT"], ["2026-06-01"], chunk_seconds=7800.0
    )
    assert len(chunks) == 6

    outcomes = tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)

    assert len(outcomes) == 6
    assert {o["outcome"] for o in outcomes} == {"fetched"}
    records, errors = dataset_store.list()
    assert errors == []
    assert len(records) == 2  # one per symbol-day
    assert {r["symbol"] for r in records} == {"AAPL", "MSFT"}
    for record in records:
        assert record["checksum"]  # verifying, non-empty
    # Exactly one outcome row per symbol-day carries the finalizing dataset_id.
    finalized = [o for o in outcomes if o["dataset_id"]]
    assert len(finalized) == 2
    assert {o["dataset_outcome"] for o in finalized} == {"recorded"}


def test_tc3_a_second_walk_over_the_same_plan_costs_zero_vendor_calls_and_zero_new_records(rec_ctx):
    adapter, dataset_store, checkpoint_store = rec_ctx
    chunks = tr.plan_recorder_chunks(["AAPL", "MSFT"], ["2026-06-01"], chunk_seconds=7800.0)
    tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
    calls_after_first = len(adapter.calls)
    records_after_first, _ = dataset_store.list()

    outcomes = tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)

    assert {o["outcome"] for o in outcomes} == {"reused"}
    assert len(adapter.calls) == calls_after_first  # zero new vendor calls
    records_after_second, _ = dataset_store.list()
    assert len(records_after_second) == len(records_after_first)  # zero new DatasetStore.record calls
    assert all(o["dataset_id"] is None for o in outcomes)  # the day short-circuit never finalizes


def test_tc4_one_failing_chunk_never_aborts_the_walk_and_leaves_no_partial_dataset(rec_ctx):
    adapter, dataset_store, checkpoint_store = rec_ctx
    chunks = tr.plan_recorder_chunks(["AAPL", "MSFT"], ["2026-06-01"], chunk_seconds=7800.0)
    assert len(chunks) == 6
    failing_chunk = chunks[3]  # MSFT's first chunk -- "chunk 4 of 6"
    assert failing_chunk["symbol"] == "MSFT"
    adapter.raise_for.add((failing_chunk["symbol"], failing_chunk["start"]))

    outcomes = tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)

    assert len(outcomes) == 6  # the walk never aborts -- every planned chunk gets an outcome
    failed = [o for o in outcomes if o["outcome"] == "failed"]
    assert len(failed) == 1
    assert failed[0]["symbol"] == "MSFT" and failed[0]["start"] == failing_chunk["start"]
    assert "the vendor said no" in failed[0]["detail"]
    # Chunks 1-3 (AAPL) and 5-6 (MSFT, after the failed one) still complete.
    msft_outcomes = [o for o in outcomes if o["symbol"] == "MSFT"]
    assert {o["outcome"] for o in msft_outcomes} == {"failed", "fetched"}
    assert sum(1 for o in msft_outcomes if o["outcome"] == "fetched") == 2

    records, _errors = dataset_store.list()
    assert len(records) == 1  # ONLY AAPL's day finalized -- MSFT's has no partial record
    assert records[0]["symbol"] == "AAPL"


def test_tc5_a_resumed_run_only_refetches_the_previously_failed_chunk_and_registers_once(rec_ctx):
    adapter, dataset_store, checkpoint_store = rec_ctx
    chunks = tr.plan_recorder_chunks(["AAPL", "MSFT"], ["2026-06-01"], chunk_seconds=7800.0)
    failing_chunk = chunks[3]
    adapter.raise_for.add((failing_chunk["symbol"], failing_chunk["start"]))
    tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
    calls_after_first = len(adapter.calls)
    assert calls_after_first == 6

    adapter.raise_for.clear()  # the transient vendor condition is gone by the time of the retry
    outcomes = tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)

    # AAPL's day short-circuits entirely (already fully recorded); MSFT's previously-completed
    # chunks (5, 6) report reused from the checkpoint; only chunk 4 is genuinely re-fetched.
    aapl_outcomes = [o for o in outcomes if o["symbol"] == "AAPL"]
    msft_outcomes = [o for o in outcomes if o["symbol"] == "MSFT"]
    assert {o["outcome"] for o in aapl_outcomes} == {"reused"}
    assert [o["outcome"] for o in msft_outcomes] == ["fetched", "reused", "reused"]
    assert len(adapter.calls) == calls_after_first + 1  # exactly one new vendor call

    records, _errors = dataset_store.list()
    assert len(records) == 2  # MSFT's day is now registered exactly once, alongside AAPL's
    assert sorted(r["symbol"] for r in records) == ["AAPL", "MSFT"]
    # A second resume attempt over the now-fully-recorded plan costs zero further vendor calls.
    tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
    assert len(adapter.calls) == calls_after_first + 1


def test_an_abort_stops_the_walk_and_keeps_what_it_finished(rec_ctx):
    adapter, dataset_store, checkpoint_store = rec_ctx
    chunks = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01", "2026-06-02"], chunk_seconds=7800.0)
    assert len(chunks) == 6
    seen = 0

    def _abort() -> bool:
        return seen >= 2

    def _count(_entry) -> None:
        nonlocal seen
        seen += 1

    outcomes = tr.run_tick_recording(
        chunks, dataset_store, checkpoint_store, adapter, CONFIG,
        progress=_count, should_abort=_abort,
    )

    assert len(outcomes) == 2
    records, _errors = dataset_store.list()
    assert records == []  # day 1 (2026-06-01) never reached its 3rd chunk -- never finalized


def test_events_recorded_carry_the_card_5_1_preservation_fields_verbatim(rec_ctx):
    adapter, dataset_store, checkpoint_store = rec_ctx
    chunks = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)
    tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
    records, _errors = dataset_store.list()
    events = dataset_store.load_events(records[0]["id"])
    trades = [e for e in events if isinstance(e, TradeEvent)]
    quotes = [e for e in events if isinstance(e, QuoteEvent)]
    assert trades and all(t.conditions == ["@"] and t.exchange == "Q" and t.tape == "C" and t.trade_id for t in trades)
    assert quotes and all(
        q.conditions == ["R"] and q.tape == "C" and q.bid_exchange == "Q" and q.ask_exchange == "K"
        for q in quotes
    )


# ==================================================================================================
# 3. TR-19 -- the Card-5.1 preservation-field structural gate (TC-8).
# ==================================================================================================


def test_tc8_the_recorder_refuses_to_record_anything_when_the_preservation_capability_is_absent(rec_ctx):
    import dataclasses as _dc

    adapter, dataset_store, checkpoint_store = rec_ctx
    chunks = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)

    # Build a genuinely field-incomplete dataclass (rather than hand-rolling __dataclass_fields__)
    # so `dataclasses.fields()` -- the real introspection the production check calls -- works.
    IncompleteTrade = _dc.make_dataclass(
        "IncompleteTrade",
        [("ticker", str), ("timestamp", float), ("price", float), ("size", int)],
    )
    with pytest.raises(tr.RecorderPreservationCapabilityMissing, match="conditions"):
        tr.verify_preservation_capability(trade_cls=IncompleteTrade)

    with pytest.raises(tr.RecorderPreservationCapabilityMissing):
        tr.run_tick_recording(
            chunks, dataset_store, checkpoint_store, adapter, CONFIG,
            _trade_cls=IncompleteTrade,
        )
    assert adapter.calls == []
    records, _errors = dataset_store.list()
    assert records == []


def test_tc8_the_real_trade_and_quote_event_classes_satisfy_the_capability_check():
    tr.verify_preservation_capability()  # must not raise -- the real classes ship the fields


# ==================================================================================================
# 4. Preservation-field round-trip + content-checksum independence (TC-9).
# ==================================================================================================


def test_tc9_preservation_values_round_trip_and_never_perturb_content_identity(rec_ctx):
    adapter, dataset_store, checkpoint_store = rec_ctx
    chunks = tr.plan_recorder_chunks(["AAPL"], ["2026-06-01"], chunk_seconds=7800.0)
    tr.run_tick_recording(chunks, dataset_store, checkpoint_store, adapter, CONFIG)
    records, _errors = dataset_store.list()
    meta = records[0]

    # A second, INDEPENDENT store instance re-verifies the SAME checksum on load (the checksum is
    # unaffected by which preservation values are present -- iter-7 audit finding B1's own proof,
    # re-exercised here against genuinely recorder-produced content).
    reloaded = DatasetStore(str(Path(checkpoint_store._root).parent / "datasets")).get(meta["id"])
    assert reloaded["checksum"] == meta["checksum"]


# ==================================================================================================
# 5. The dated quote_size_unit vendor-rule stamping (TC-10/TC-11).
# ==================================================================================================


def test_tc10_the_dated_rule_stamps_round_lots_before_and_shares_on_or_after_the_cutover():
    assert tr.quote_size_unit_for_session_date("2025-10-15") == "round_lots"
    assert tr.quote_size_unit_for_session_date("2025-11-03") == "shares"  # the cutover date itself
    assert tr.quote_size_unit_for_session_date("2025-11-10") == "shares"
    assert tr.ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE == "2025-11-03"


def test_tc10_recorded_datasets_carry_the_stamped_quote_size_unit_from_the_single_existing_tuple(rec_ctx):
    from app.research.micro_features import QUOTE_SIZE_UNITS

    adapter, dataset_store, checkpoint_store = rec_ctx
    pre_chunks = tr.plan_recorder_chunks(["AAPL"], ["2025-10-15"], chunk_seconds=7800.0)
    post_chunks = tr.plan_recorder_chunks(["MSFT"], ["2025-11-10"], chunk_seconds=7800.0)
    tr.run_tick_recording(pre_chunks, dataset_store, checkpoint_store, adapter, CONFIG)
    tr.run_tick_recording(post_chunks, dataset_store, checkpoint_store, adapter, CONFIG)

    records, _errors = dataset_store.list()
    by_symbol = {r["symbol"]: r for r in records}
    assert by_symbol["AAPL"]["quote_size_unit"] == "round_lots"
    assert by_symbol["MSFT"]["quote_size_unit"] == "shares"
    assert by_symbol["AAPL"]["quote_size_unit"] in QUOTE_SIZE_UNITS
    assert by_symbol["AAPL"]["schema_basis"] == tr.RECORDER_SCHEMA_BASIS


def test_tc12_finalize_day_stamps_the_rule_text_and_a_per_dataset_verification_note(rec_ctx):
    """iter-9 TC-12 (spec section 2.6's own closing clause): ``_finalize_day``'s
    ``record_from_source`` call gains the two new sibling fields alongside the existing
    ``schema_basis``/``quote_size_unit`` stamps -- the rule text is the ONE frozen sentence
    (``QUOTE_SIZE_UNIT_RULE_TEXT``) verbatim on every dataset regardless of which side of the
    cutover it falls on; the verification note is genuinely PER-DATASET (names each dataset's own
    ``session_date`` and the actual comparison direction against ``ALPACA_QUOTE_SIZE_UNIT_
    EFFECTIVE``, TC-13's own "not one frozen sentence repeated regardless" contract)."""
    adapter, dataset_store, checkpoint_store = rec_ctx
    pre_chunks = tr.plan_recorder_chunks(["AAPL"], ["2025-10-15"], chunk_seconds=7800.0)
    post_chunks = tr.plan_recorder_chunks(["MSFT"], ["2025-11-10"], chunk_seconds=7800.0)
    tr.run_tick_recording(pre_chunks, dataset_store, checkpoint_store, adapter, CONFIG)
    tr.run_tick_recording(post_chunks, dataset_store, checkpoint_store, adapter, CONFIG)

    records, _errors = dataset_store.list()
    by_symbol = {r["symbol"]: r for r in records}

    for symbol in ("AAPL", "MSFT"):
        assert by_symbol[symbol]["quote_size_unit_rule_text"] == tr.QUOTE_SIZE_UNIT_RULE_TEXT
        assert "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE" in by_symbol[symbol]["quote_size_unit_verification_note"]

    # the pre-cutover (round_lots) dataset's note names a "<" comparison; the post-cutover
    # (shares) dataset's note names a ">=" comparison -- genuinely per-dataset, not one constant
    # string copy-pasted onto every row regardless of its own date.
    assert "('2025-10-15') < " in by_symbol["AAPL"]["quote_size_unit_verification_note"]
    assert "('2025-11-10') >= " in by_symbol["MSFT"]["quote_size_unit_verification_note"]
    assert by_symbol["AAPL"]["quote_size_unit_verification_note"] != by_symbol["MSFT"]["quote_size_unit_verification_note"]

    # both survive a reload verbatim (the schema_basis/quote_size_unit reload precedent, extended).
    reloaded = DatasetStore(str(Path(checkpoint_store._root).parent / "datasets")).get(by_symbol["AAPL"]["id"])
    assert reloaded["quote_size_unit_rule_text"] == tr.QUOTE_SIZE_UNIT_RULE_TEXT
    assert reloaded["quote_size_unit_verification_note"] == by_symbol["AAPL"]["quote_size_unit_verification_note"]


def test_tc11_an_out_of_vocabulary_quote_size_unit_is_still_rejected_by_the_existing_guard(rec_ctx):
    _adapter, dataset_store, _checkpoint_store = rec_ctx
    with pytest.raises(ValueError, match="unknown quote_size_unit"):
        dataset_store.record(
            symbol="AAPL", source="fixture", source_kind="fixture", source_id="x", split=SPLIT_TRAIN,
            window_start_utc="2026-06-01T13:30:00Z", window_end_utc="2026-06-01T20:00:00Z",
            data_feed="sip", epoch_anchor=0.0,
            events=[TradeEvent("AAPL", 0.0, 100.0, 10)],
            quote_size_unit="not-a-real-unit",
        )


# ==================================================================================================
# 6. The recorder's own throttle (spec section 1: RECORDER_PAGE_BUDGET_PER_MINUTE).
# ==================================================================================================


def test_throttle_recorder_fetch_spaces_consecutive_calls(monkeypatch):
    monkeypatch.setattr(tr, "RECORDER_PAGE_BUDGET_PER_MINUTE", 600)  # 0.1s interval
    tr._reset_recorder_throttle_for_tests()
    try:
        t0 = time.monotonic()
        tr._throttle_recorder_fetch()
        t1 = time.monotonic()
        tr._throttle_recorder_fetch()
        t2 = time.monotonic()
    finally:
        tr._reset_recorder_throttle_for_tests()
    assert (t1 - t0) < 0.05, "the first call has nothing prior to wait behind"
    assert (t2 - t1) >= 0.09, "the second call must wait ~the configured min interval"


def test_recorder_page_budget_is_the_frozen_spec_value():
    assert tr.RECORDER_PAGE_BUDGET_PER_MINUTE == 200


# ==================================================================================================
# 7. The published sha256 split rule (spec section 7.3, Card 5.2 -- unchanged, frozen).
# ==================================================================================================


def test_recorder_split_matches_the_published_sha256_rule_directly_recomputed():
    for symbol, session_date in [("AAPL", "2026-06-22"), ("PG", "2026-01-05"), ("NVDA", "2026-03-14")]:
        digest = hashlib.sha256(f"{symbol}:{session_date}".encode("utf-8")).hexdigest()
        expected = SPLIT_HOLDOUT if int(digest[-1], 16) in (0, 1, 2) else SPLIT_TRAIN
        assert tr.recorder_split_for(symbol, session_date) == expected


def test_recorder_split_is_deterministic_and_only_train_or_holdout():
    a = tr.recorder_split_for("AAPL", "2026-06-22")
    b = tr.recorder_split_for("AAPL", "2026-06-22")
    assert a == b
    assert a in (SPLIT_TRAIN, SPLIT_HOLDOUT)


# ==================================================================================================
# 8. Bar pairing through the EXISTING, UNCHANGED desk_deep_backfill machinery.
# ==================================================================================================


class _FakeBarVendorAdapter:
    name = "fake"

    def __init__(self) -> None:
        self.fetch_bars_calls: list[tuple] = []

    def is_available(self) -> bool:
        return True

    def warm_symbol_universe(self) -> None:
        pass

    def fetch_bars(self, symbol, start, end, timeframe):
        from app.providers.adapters.base import RawBar

        self.fetch_bars_calls.append((symbol, timeframe, start, end))
        return (RawBar(symbol, timeframe, start.timestamp(), 10.0, 11.0, 9.0, 10.5, 1000),)


def test_bar_pairing_backfills_only_symbols_that_got_a_dataset_this_run(tmp_path, monkeypatch):
    from app.main import app, get_market_adapter
    from app.research.bar_index import BarIndex
    from app.research.bars import BarStore
    from app.research.routes import ResearchRegistry, set_registry
    from app.research.store import JournalStore

    monkeypatch.setenv("TAPEOLOGY_DESK_DEEP_BACKFILL_WORKERS", "1")
    bar_adapter = _FakeBarVendorAdapter()
    app.dependency_overrides[get_market_adapter] = lambda: bar_adapter
    journal = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(journal, CONFIG)
    set_registry(registry)
    bar_store = BarStore(tmp_path / "bars")
    bar_index = BarIndex(str(tmp_path / "index.db"))
    try:
        tick_outcomes = [
            {"symbol": "AAPL", "date": "2026-06-01", "dataset_id": "d1", "dataset_outcome": "recorded"},
            {"symbol": "AAPL", "date": "2026-06-02", "dataset_id": None, "dataset_outcome": None},
            {"symbol": "MSFT", "date": "2026-06-01", "dataset_id": None, "dataset_outcome": None},
        ]
        outcomes = tr.pair_bar_backfill_for_recorded_days(
            tick_outcomes, bar_store, bar_index, registry, today=date(2026, 8, 18),
        )
        assert outcomes  # AAPL's one recorded day was backfilled
        assert {c[0] for c in bar_adapter.fetch_bars_calls} == {"AAPL"}
    finally:
        set_registry(None)
        app.dependency_overrides.pop(get_market_adapter, None)
        journal.close()


def test_bar_pairing_is_honestly_empty_when_nothing_was_recorded(tmp_path):
    outcomes = tr.pair_bar_backfill_for_recorded_days([], None, None, None)
    assert outcomes == []


# ==================================================================================================
# 9. The compute manager: single-flight, cancel (TC-6/TC-7).
# ==================================================================================================


class _BlockingTickAdapter(_FakeTickAdapter):
    """Blocks INSIDE ``iter_historical_chunks`` for every chunk until the test releases it --
    deterministic control over exactly when the background worker is "still running", never a
    wall-clock race."""

    def __init__(self) -> None:
        super().__init__()
        self.started = threading.Event()
        self.proceed = threading.Event()

    def iter_historical_chunks(self, symbol, start, end):
        self.started.set()
        self.proceed.wait(timeout=10.0)
        yield from super().iter_historical_chunks(symbol, start, end)


@pytest.fixture
def manager_ctx(tmp_path):
    tr._reset_recorder_throttle_for_tests()
    manager = tr.TickRecorderComputeManager()
    dataset_store = DatasetStore(str(tmp_path / "datasets"))
    checkpoint_store = tr.RecorderCheckpointStore(str(tmp_path / "checkpoints"))
    run_log_dir = str(tmp_path / "runs")
    yield manager, dataset_store, checkpoint_store, run_log_dir
    manager.join_all(timeout=10.0)
    tr._reset_recorder_throttle_for_tests()


def test_tc6_a_concurrent_second_trigger_returns_the_in_flight_runs_snapshot_unchanged(manager_ctx):
    manager, dataset_store, checkpoint_store, run_log_dir = manager_ctx
    adapter = _BlockingTickAdapter()

    first = manager.trigger(
        dataset_store, checkpoint_store, adapter, None, None, None, CONFIG, run_log_dir,
        symbols=["AAPL"], dates=["2026-06-01"],
    )
    assert first["started"] is True
    assert adapter.started.wait(timeout=5.0), "the worker thread must have started fetching"

    second = manager.trigger(
        dataset_store, checkpoint_store, adapter, None, None, None, CONFIG, run_log_dir,
        symbols=["MSFT"], dates=["2026-06-02"],  # deliberately a DIFFERENT request
    )

    assert second["started"] is False
    assert second["compute"]["run_id"] == first["compute"]["run_id"]  # the SAME job, unchanged
    assert second["compute"]["state"] == "running"

    adapter.proceed.set()  # release the worker so the fixture's join_all doesn't hang
    manager.join_all(timeout=10.0)
    # The second (refused) request never started its own walk -- MSFT was never touched.
    assert all(call[0] != "MSFT" for call in adapter.calls)


def test_tc7_cancel_on_an_idle_manager_is_rejected_by_the_route_layers_own_409_contract(manager_ctx):
    """The manager's OWN ``.cancel()`` is a harmless no-op when idle (module docstring); the route
    is what turns "idle" into an HTTP 409 (micro_routes.py's established convention, tested at the
    route layer by ``test_cancelling_an_idle_recorder_is_a_409`` further down in THIS SAME file,
    section 11's REST-route tests). Pinned here at the manager level: cancelling an idle manager
    never raises, and its own ``accepted`` flag says nothing was running."""
    manager, _dataset_store, _checkpoint_store, _run_log_dir = manager_ctx
    result = manager.cancel()
    assert result == {"state": "cancelled", "accepted": False}
    assert manager.snapshot()["state"] == "idle"


def test_tc7_a_cancelled_run_finishes_its_in_flight_chunk_and_stops_before_the_next(manager_ctx):
    manager, dataset_store, checkpoint_store, run_log_dir = manager_ctx
    adapter = _BlockingTickAdapter()

    manager.trigger(
        dataset_store, checkpoint_store, adapter, None, None, None, CONFIG, run_log_dir,
        symbols=["AAPL"], dates=["2026-06-01", "2026-06-02"],  # 2 symbol-days -> multiple chunks
    )
    assert adapter.started.wait(timeout=5.0)

    cancel_result = manager.cancel()
    assert cancel_result == {"state": "cancelled", "accepted": True}
    adapter.proceed.set()  # let the IN-FLIGHT chunk finish -- cooperative, never mid-fetch

    deadline = time.time() + 10.0
    snapshot = manager.snapshot()
    while time.time() < deadline and snapshot["state"] == "running":
        time.sleep(0.02)
        snapshot = manager.snapshot()

    assert snapshot["state"] == "cancelled"
    # A shorter-than-planned outcome list -- the walk stopped before every chunk was visited.
    assert 0 < len(snapshot["progress"]["outcomes"]) < snapshot["progress"]["chunks_total"]

    runs = read_run_log(run_log_dir)
    assert len(runs) == 1
    assert runs[0]["state"] == "cancelled"


# ==================================================================================================
# 10. The CLI -- the walker is the ONLY implementation (no second one).
# ==================================================================================================


def test_the_cli_dry_run_prints_the_plan_and_issues_no_vendor_call_and_writes_nothing(tmp_path, monkeypatch, capsys):
    import sys

    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    monkeypatch.setattr(
        sys, "argv",
        ["tick_recorder.py", "--symbols", "AAPL,MSFT", "--dates", "2026-06-01,2026-06-02", "--dry-run"],
    )

    exit_code = tr.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out
    assert "104 chunk(s) over 4 symbol-day(s)" in captured.out
    assert not (tmp_path / "datasets").exists()


def test_the_cli_runs_the_identical_walker_end_to_end_against_a_fake_adapter(tmp_path, monkeypatch, capsys):
    import sys

    from app.main import app, get_market_adapter
    from app.research.routes import ResearchRegistry, set_registry
    from app.research.store import JournalStore

    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_BAR_INDEX_DB", str(tmp_path / "index.db"))
    monkeypatch.setenv("TAPEOLOGY_MICRO_RECORDER_CHECKPOINT_DIR", str(tmp_path / "checkpoints"))
    monkeypatch.setenv("TAPEOLOGY_MICRO_RECORDER_LOG_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("TAPEOLOGY_DESK_DEEP_BACKFILL_WORKERS", "1")
    monkeypatch.setattr(
        sys, "argv", ["tick_recorder.py", "--symbols", "AAPL", "--dates", "2026-06-01"],
    )
    tr._reset_recorder_throttle_for_tests()
    adapter = _FakeTickAdapter()
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    journal = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    set_registry(ResearchRegistry(journal, CONFIG))
    try:
        exit_code = tr.main()
    finally:
        set_registry(None)
        app.dependency_overrides.pop(get_market_adapter, None)
        journal.close()
        tr._reset_recorder_throttle_for_tests()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "tick recording complete" in captured.out
    dataset_store = DatasetStore(str(tmp_path / "datasets"))
    records, errors = dataset_store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0]["symbol"] == "AAPL"
    runs = read_run_log(str(tmp_path / "runs"))
    assert len(runs) == 1 and runs[0]["state"] == "done" and runs[0]["datasets_recorded"] == 1


def test_the_cli_refuses_cleanly_when_the_preservation_capability_is_reported_missing(tmp_path, monkeypatch, capsys):
    import sys

    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    monkeypatch.setattr(sys, "argv", ["tick_recorder.py", "--symbols", "AAPL", "--dates", "2026-06-01"])
    monkeypatch.setattr(
        tr, "verify_preservation_capability",
        lambda: (_ for _ in ()).throw(tr.RecorderPreservationCapabilityMissing("simulated absent")),
    )

    exit_code = tr.main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "recording refused" in captured.out
    assert not (tmp_path / "datasets").exists()


# ==================================================================================================
# 11. The REST routes (micro_routes.py) -- POST/GET/POST-cancel compute + GET runs.
# ==================================================================================================


@pytest.fixture
def route_ctx(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app, get_market_adapter
    from app.research.micro_routes import get_tick_recorder_compute_manager
    from app.research.routes import ResearchRegistry, set_registry
    from app.research.store import JournalStore

    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
    monkeypatch.setenv("TAPEOLOGY_BAR_INDEX_DB", str(tmp_path / "bar_index.db"))
    monkeypatch.setenv("TAPEOLOGY_MICRO_RECORDER_CHECKPOINT_DIR", str(tmp_path / "checkpoints"))
    monkeypatch.setenv("TAPEOLOGY_MICRO_RECORDER_LOG_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("TAPEOLOGY_DESK_DEEP_BACKFILL_WORKERS", "1")
    tr._reset_recorder_throttle_for_tests()
    adapter = _FakeTickAdapter()
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    fresh_manager = tr.TickRecorderComputeManager()
    app.dependency_overrides[get_tick_recorder_compute_manager] = lambda: fresh_manager
    journal = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    set_registry(ResearchRegistry(journal, CONFIG))
    with TestClient(app) as client:
        yield client, fresh_manager, adapter, tmp_path
    fresh_manager.join_all(timeout=10.0)
    set_registry(None)
    app.dependency_overrides.pop(get_market_adapter, None)
    app.dependency_overrides.pop(get_tick_recorder_compute_manager, None)
    journal.close()
    tr._reset_recorder_throttle_for_tests()


def test_the_runs_route_is_honestly_empty_before_any_recording(route_ctx):
    client, _mgr, _adapter, _tmp_path = route_ctx
    assert client.get("/research/desk/micro/recorder/runs").json() == {"runs": []}


def test_the_compute_get_is_idle_before_any_recording_and_never_starts_a_walk(route_ctx):
    client, mgr, adapter, _tmp_path = route_ctx
    body = client.get("/research/desk/micro/recorder/compute").json()
    assert body["state"] == "idle"
    assert mgr.snapshot()["state"] == "idle"
    assert adapter.calls == []


def test_trigger_refuses_empty_symbols_or_dates_and_starts_nothing(route_ctx):
    client, mgr, _adapter, _tmp_path = route_ctx
    r1 = client.post(
        "/research/desk/micro/recorder/compute", json={"symbols": [], "dates": ["2026-06-01"]}
    )
    assert r1.status_code == 422
    r2 = client.post(
        "/research/desk/micro/recorder/compute", json={"symbols": ["AAPL"], "dates": []}
    )
    assert r2.status_code == 422
    assert mgr.snapshot()["state"] == "idle"


def test_cancelling_an_idle_recorder_is_a_409(route_ctx):
    client, _mgr, _adapter, _tmp_path = route_ctx
    r = client.post("/research/desk/micro/recorder/compute/cancel")
    assert r.status_code == 409


def test_a_trigger_runs_to_done_records_a_dataset_and_the_runs_route_reports_it(route_ctx):
    client, _mgr, _adapter, tmp_path = route_ctx
    r = client.post(
        "/research/desk/micro/recorder/compute",
        json={"symbols": ["AAPL"], "dates": ["2026-06-01"]},
    )
    assert r.status_code == 200
    assert r.json()["started"] is True

    deadline = time.time() + 15
    snapshot = None
    while time.time() < deadline:
        snapshot = client.get("/research/desk/micro/recorder/compute").json()
        if snapshot["state"] != "running":
            break
        time.sleep(0.02)
    assert snapshot is not None and snapshot["state"] == "done"
    assert snapshot["progress"]["chunks_done"] == snapshot["progress"]["chunks_total"] > 0

    dataset_store = DatasetStore(str(tmp_path / "datasets"))
    records, _errors = dataset_store.list()
    assert len(records) == 1 and records[0]["symbol"] == "AAPL"

    runs = client.get("/research/desk/micro/recorder/runs").json()
    assert len(runs["runs"]) == 1
    assert runs["runs"][0]["state"] == "done"
    assert runs["runs"][0]["datasets_recorded"] == 1


def test_a_second_trigger_while_running_returns_the_in_flight_snapshot_unchanged(route_ctx):
    from app.main import app, get_market_adapter

    client, mgr, _adapter, _tmp_path = route_ctx
    blocking_adapter = _BlockingTickAdapter()
    app.dependency_overrides[get_market_adapter] = lambda: blocking_adapter
    try:
        first = client.post(
            "/research/desk/micro/recorder/compute",
            json={"symbols": ["AAPL"], "dates": ["2026-06-01"]},
        ).json()
        assert blocking_adapter.started.wait(timeout=5.0)

        second = client.post(
            "/research/desk/micro/recorder/compute",
            json={"symbols": ["MSFT"], "dates": ["2026-06-02"]},
        ).json()
        assert second["started"] is False
        assert second["compute"]["run_id"] == first["compute"]["run_id"]
    finally:
        blocking_adapter.proceed.set()
        mgr.join_all(timeout=10.0)


def test_cancel_while_running_stops_the_walk_cooperatively_through_the_route(route_ctx):
    from app.main import app, get_market_adapter

    client, mgr, _adapter, _tmp_path = route_ctx
    blocking_adapter = _BlockingTickAdapter()
    app.dependency_overrides[get_market_adapter] = lambda: blocking_adapter
    try:
        client.post(
            "/research/desk/micro/recorder/compute",
            json={"symbols": ["AAPL"], "dates": ["2026-06-01", "2026-06-02"]},
        )
        assert blocking_adapter.started.wait(timeout=5.0)

        r = client.post("/research/desk/micro/recorder/compute/cancel")
        assert r.status_code == 200
        assert r.json() == {"state": "cancelled"}
        blocking_adapter.proceed.set()

        deadline = time.time() + 10
        snapshot = None
        while time.time() < deadline:
            snapshot = client.get("/research/desk/micro/recorder/compute").json()
            if snapshot["state"] != "running":
                break
            time.sleep(0.02)
        assert snapshot is not None and snapshot["state"] == "cancelled"
    finally:
        mgr.join_all(timeout=10.0)


from app.config import CONFIG  # noqa: E402 -- imported at bottom to keep the fixture section terse
