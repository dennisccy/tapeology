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
  9. Era iteration 11 (spec section 7.1, r5): the LIVE recorder-progress path is aggregate-only
     at every point during a run -- TC-6/TC-7, section 12 at the bottom of this file.
"""

from __future__ import annotations

import hashlib
import json
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
    # Fewer chunks done than planned -- the walk stopped before every chunk was visited. Era
    # iteration 11: `manager.snapshot()`'s own `progress` is now aggregate-only (spec section 7.1,
    # r5) and no longer carries a raw `outcomes` list at all -- `chunks_done` is the SAME count
    # `len(outcomes)` always equalled in the pre-iteration-11 shape (both incremented together by
    # `_publish`), so this assertion's meaning is unchanged.
    assert 0 < snapshot["progress"]["chunks_done"] < snapshot["progress"]["chunks_total"]

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


# ==================================================================================================
# 12. Era iteration 11 (spec section 7.1, r5): the LIVE recorder-progress path is aggregate-only
#     at every point during a run -- TC-6/TC-7. The run-log route (GET .../recorder/runs, section
#     11's `test_a_trigger_runs_to_done_records_a_dataset_and_the_runs_route_reports_it`) was
#     already aggregate-only and is untouched; this section covers ONLY the live GET/POST compute
#     paths, which used to carry a raw `progress.outcomes` list with each planned chunk's own
#     symbol/date (`tick_recorder.py`'s pre-iteration-11 `_publish`/`_copy_recorder_snapshot`).
# ==================================================================================================


_PROGRESS_AGGREGATE_KEYS = {
    "chunks_total", "chunks_done", "percent_complete", "elapsed_seconds",
    "chunks_per_minute",
}


def _assert_progress_is_aggregate_only(progress: dict) -> None:
    """TC-6's own field-shape assertion: EXACTLY the ten aggregate fields spec section 7.1 (r5)
    names -- no ``outcomes``, no ``symbol``, no ``date``, no ``dataset_id``, nothing else.

    Iteration 12 (TR-28/r7): ``trades_total``/``quotes_total`` (exact) are GONE, replaced by
    ``trades_total_bucket``/``quotes_total_bucket`` (coarse labels) -- the iteration-11 audit
    proved a one-symbol-day run's "aggregate" exact total WAS that withheld shard's exact count."""
    assert set(progress.keys()) == _PROGRESS_AGGREGATE_KEYS, sorted(progress.keys())


def test_tc8_the_recorder_progress_route_docstring_names_the_bucketed_fields_it_actually_serves():
    """TC-8 (iteration 13, docstring-only fix -- goal-rapid-microscope-iter-13): the route
    function's own docstring must name the fields ``_progress_view`` actually serves today
    (``trades_total_bucket``/``quotes_total_bucket``, TR-28/r7 -- pinned above by
    ``_assert_progress_is_aggregate_only``) -- never the stale, pre-iteration-12 unconditional
    ``trades_total``/``quotes_total`` pair as though it were still served plain."""
    from app.research.micro_routes import get_tick_recorder_compute

    doc = get_tick_recorder_compute.__doc__ or ""
    assert "trades_total_bucket" in doc
    assert "quotes_total_bucket" in doc
    # the OLD, stale field-LIST form -- `chunks_failed` through `percent_complete` listed
    # back-to-back with the bare (un-bucketed) names in the middle, as though served plain -- must
    # not appear anywhere in the corrected docstring. (The corrected prose still legitimately
    # names the bare pair once, elsewhere, to explain that they are NEVER served -- this checks
    # the specific stale listing shape, not bare mentions of the field names.)
    assert "``chunks_failed``/``trades_total``/``quotes_total``/``percent_complete``" not in doc


def test_tc6_recorder_progress_never_leaks_a_planned_chunks_symbol_date_or_dataset_id(
    route_ctx, monkeypatch
):
    """TC-6 (phase spec, literal scenario): "a tick-recorder compute job planned over 3 chunks
    spanning 2 symbol-days ... polled mid-run and again after it reaches a terminal state ...
    neither response body contains any planned chunk's symbol or date string value, nor any
    dataset_id, anywhere in the JSON -- only chunks_total, chunks_done, the four per-outcome-type
    counts, trades_total, quotes_total, percent_complete, and elapsed_seconds."

    ``plan_recorder_chunks`` is monkeypatched to this EXACT 3-chunk/2-symbol-day plan: its own
    real ``chunk_seconds`` default is bound at ITS OWN definition time (a plain Python default-
    argument gotcha), so it cannot be narrowed through the public ``trigger()``/route surface
    (which always calls it with none) without this -- the alternative, a real 26-chunks-per-
    symbol-day walk under the recorder's own throttle, works too (proven by the route tests in
    section 11 above) but is needlessly slow for what this test needs to prove. Everything AFTER
    planning -- the walk, the checkpoints, the finalize, the manager's publish loop -- is
    completely real, against the fake adapter."""
    client, mgr, _adapter, tmp_path = route_ctx
    from app.main import app, get_market_adapter

    fake_plan = [
        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z", "end": "2026-06-01T15:00:00Z"},
        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T15:00:00Z", "end": "2026-06-01T20:00:00Z"},
        {"symbol": "MSFT", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z", "end": "2026-06-01T20:00:00Z"},
    ]
    monkeypatch.setattr(tr, "plan_recorder_chunks", lambda symbols, dates: list(fake_plan))

    blocking_adapter = _BlockingTickAdapter()
    app.dependency_overrides[get_market_adapter] = lambda: blocking_adapter
    try:
        r = client.post(
            "/research/desk/micro/recorder/compute",
            json={"symbols": ["AAPL", "MSFT"], "dates": ["2026-06-01"]},
        )
        assert r.status_code == 200
        assert blocking_adapter.started.wait(timeout=5.0)

        # --- mid-run: the first chunk is being fetched, none have resolved yet ----------------
        mid_run = client.get("/research/desk/micro/recorder/compute").json()
        assert mid_run["state"] == "running"
        assert mid_run["progress"]["chunks_total"] == 3
        _assert_progress_is_aggregate_only(mid_run["progress"])
        forbidden = {"AAPL", "MSFT", "2026-06-01"}
        mid_run_text = json.dumps(mid_run)
        for token in forbidden:
            assert token not in mid_run_text, f"{token!r} leaked mid-run"
        # the POST's own immediate return goes through the SAME projection (`trigger()`'s
        # `published`, built by the SAME `_copy_recorder_snapshot`).
        assert "AAPL" not in json.dumps(r.json()) and "MSFT" not in json.dumps(r.json())

        blocking_adapter.proceed.set()  # let every remaining chunk (2, 3) proceed unblocked

        deadline = time.time() + 15
        terminal = None
        while time.time() < deadline:
            terminal = client.get("/research/desk/micro/recorder/compute").json()
            if terminal["state"] != "running":
                break
            time.sleep(0.02)
        assert terminal is not None and terminal["state"] == "done"

        # --- terminal: still aggregate-only, and the aggregates are the RIGHT numbers ---------
        _assert_progress_is_aggregate_only(terminal["progress"])
        assert terminal["progress"]["chunks_done"] == terminal["progress"]["chunks_total"] == 3
        # TR-32: no outcome-typed counter is served live any more -- the terminal run-log row
        # carries the exact counts, where TR-4 requires the disclosed failure list.
        for banned in ("chunks_fetched", "chunks_reused", "chunks_unchanged", "chunks_failed"):
            assert banned not in terminal["progress"]
        # TR-32 (amendment 1): the volume signal is gone from live progress entirely -- it
        # leaked by EXISTENCE, since totals advance only on a fetched chunk.
        for banned in ("trades_total", "quotes_total", "trades_total_bucket", "quotes_total_bucket"):
            assert banned not in terminal["progress"]
        assert terminal["progress"]["percent_complete"] == 100.0
        assert terminal["progress"]["elapsed_seconds"] >= 0.0

        terminal_text = json.dumps(terminal)
        for token in forbidden:
            assert token not in terminal_text, f"{token!r} leaked at the terminal state"

        # a leak-free trap that computed nothing proves nothing (the era's own "cannot pass merely
        # because the rig computed nothing" discipline) -- the datasets were genuinely recorded.
        dataset_store = DatasetStore(str(tmp_path / "datasets"))
        records, _errors = dataset_store.list()
        assert sorted(m["symbol"] for m in records) == ["AAPL", "MSFT"]

        # the run-log route (already aggregate-only, untouched this iteration) still names them --
        # proving the withholding above is TARGETED at the live path, never a blanket break.
        runs = client.get("/research/desk/micro/recorder/runs").json()["runs"]
        assert runs[0]["datasets_recorded"] == 2
    finally:
        blocking_adapter.proceed.set()
        mgr.join_all(timeout=10.0)


def test_tc7_the_recorder_progress_route_accepts_no_bypass_parameter_header_or_role(route_ctx):
    """TC-7 (phase spec): "given the recorder-progress route's request handling, when it is
    inspected for any query parameter, header, or role claim that would return per-chunk identity,
    then none exists." Proven two ways: (1) the route's OWN OpenAPI schema declares zero
    parameters of any kind (no query, no header, no path beyond the fixed URL); (2) a LIVE
    behavioural check -- an arbitrary probe of query params and headers that might plausibly spell
    "reveal it anyway" has literally no effect on the served body, because FastAPI ignores any
    input a route does not declare. r5's own words: "There is no operator-only bypass -- using one
    would itself be a human exposure event that destroys the tranche's blindness, and it is
    unnecessary for ordinary monitoring." """
    client, _mgr, _adapter, _tmp_path = route_ctx
    from app.main import app

    schema = app.openapi()["paths"]["/research/desk/micro/recorder/compute"]["get"]
    assert schema.get("parameters", []) == []

    plain = client.get("/research/desk/micro/recorder/compute").json()
    probed = client.get(
        "/research/desk/micro/recorder/compute",
        params={"reveal": "true", "operator": "true", "role": "admin", "symbol": "AAPL", "bypass": "1"},
        headers={"X-Operator-Override": "true", "X-Admin-Role": "operator", "Authorization": "Bearer x"},
    ).json()
    assert probed == plain  # every extra input is silently ignored -- no bypass exists anywhere


# ==================================================================================================
# 13. Era iteration 12 (spec section 7.1, r7): TR-28 -- event/byte VOLUMES are coarse BUCKETS
#     pre-release, never exact totals. TC-9/TC-10/TC-11 (phase spec's own test-first contract).
# ==================================================================================================


def _run_a_one_symbol_day_recording_to_done(client) -> dict:
    r = client.post(
        "/research/desk/micro/recorder/compute", json={"symbols": ["AAPL"], "dates": ["2026-06-01"]},
    )
    assert r.status_code == 200
    deadline = time.time() + 15
    terminal = None
    while time.time() < deadline:
        terminal = client.get("/research/desk/micro/recorder/compute").json()
        if terminal["state"] != "running":
            break
        time.sleep(0.02)
    assert terminal is not None and terminal["state"] == "done"
    return terminal


def test_tc9_a_one_symbol_day_run_never_serves_an_exact_trade_or_quote_count(route_ctx):
    """TC-9, carried forward under TR-32 (owner ruling 2026-08-21, amendment 1).

    The original iteration-12 form asserted the served value was a coarse BUCKET label rather than
    an exact count. TR-32 went further and removed the volume fields from live progress entirely,
    because the buckets leaked by EXISTENCE rather than magnitude: running totals advance only on a
    ``fetched`` chunk, so a bucket transition across a single-chunk advance proved that chunk's
    outcome. Absence strictly subsumes the original guarantee -- a field that is not served can
    never be an exact count."""
    client, _mgr, _adapter, _tmp = route_ctx
    r = client.post(
        "/research/desk/micro/recorder/compute",
        json={"symbols": ["AAPL"], "dates": ["2026-06-01"]},
    )
    assert r.status_code == 200
    deadline = time.time() + 20
    terminal = None
    while time.time() < deadline:
        terminal = client.get("/research/desk/micro/recorder/compute").json()
        if terminal["state"] != "running":
            break
        time.sleep(0.02)
    assert terminal is not None and terminal["state"] == "done"
    progress = terminal["progress"]
    for key in ("trades_total", "quotes_total", "trades_total_bucket", "quotes_total_bucket"):
        assert key not in progress, f"{key!r} is served on live progress again"
    _assert_progress_is_aggregate_only(progress)


def test_tc10_live_progress_carries_no_volume_signal_that_could_be_differenced(route_ctx):
    """TC-10, carried forward under TR-32. The original asserted the bucket never NARROWED between
    two observations (differencing-resistance of the magnitude). TR-32 removes the signal outright,
    so there is no volume series to difference at all -- across any pair of observations, at any
    polling cadence."""
    client, _mgr, _adapter, _tmp = route_ctx
    before = client.get("/research/desk/micro/recorder/compute").json()["progress"]
    r = client.post(
        "/research/desk/micro/recorder/compute",
        json={"symbols": ["AAPL"], "dates": ["2026-06-01"]},
    )
    assert r.status_code == 200
    deadline = time.time() + 20
    after = None
    while time.time() < deadline:
        snap = client.get("/research/desk/micro/recorder/compute").json()
        if snap["state"] != "running":
            after = snap["progress"]
            break
        time.sleep(0.02)
    assert after is not None
    for progress in (before, after):
        assert not [k for k in progress if "trades" in k or "quotes" in k], progress
    # position and timing still advance, so the surface is not merely empty.
    assert after["chunks_done"] >= before["chunks_done"]


def test_tc11_this_surface_deliberately_never_re_enables_exact_totals(route_ctx):
    """TC-11, carried forward under TR-32: the projection is an explicit whitelist, so neither the
    exact totals (removed in iteration 12) nor the bucket labels that replaced them (removed by
    TR-32) can reappear, and neither can the outcome-typed counters. A regression here would mean
    someone widened the whitelist."""
    client, _mgr, _adapter, _tmp = route_ctx
    r = client.post(
        "/research/desk/micro/recorder/compute",
        json={"symbols": ["AAPL"], "dates": ["2026-06-01"]},
    )
    assert r.status_code == 200
    deadline = time.time() + 20
    terminal = None
    while time.time() < deadline:
        terminal = client.get("/research/desk/micro/recorder/compute").json()
        if terminal["state"] != "running":
            break
        time.sleep(0.02)
    assert terminal is not None and terminal["state"] == "done"
    again = client.get("/research/desk/micro/recorder/compute").json()["progress"]
    assert set(again) == _PROGRESS_AGGREGATE_KEYS
    for banned in ("trades_total", "quotes_total", "trades_total_bucket", "quotes_total_bucket",
                   "chunks_fetched", "chunks_reused", "chunks_unchanged", "chunks_failed"):
        assert banned not in again, f"{banned!r} reappeared on the live projection"


def test_volume_bucket_scheme_is_frozen_predeclared_and_never_a_rounded_number(monkeypatch):
    """The scheme itself, pinned: a module constant (never a ``Config`` field, never tuned from an
    observed run), monotonic, and never produces a label that LOOKS like a rounded exact count."""
    assert tr._volume_bucket(0) == "0"
    assert tr._volume_bucket(1) == tr._volume_bucket(999) == "1-999"
    assert tr._volume_bucket(1000) == "1K-10K"
    assert tr._volume_bucket(3_842_117) == "1M-10M"
    labels = [label for _, _, label in tr._VOLUME_BUCKETS]
    assert len(labels) == len(set(labels))  # no duplicate label across bands
    # "0" is the one legitimate bare-digit label -- a genuinely, unambiguously empty count is not
    # an approximation of anything hidden, so it carries no rounding risk. Every OTHER band must
    # never look like a rounded exact number.
    assert labels[0] == "0"
    for label in labels[1:]:
        assert not label.isdigit()
    # monotonic across a wide, increasing sample -- never a larger count mapping to an earlier band.
    sample = [0, 1, 500, 999, 1_000, 50_000, 999_999, 1_000_000, 5_000_000_000]
    indices = [labels.index(tr._volume_bucket(n)) for n in sample]
    assert indices == sorted(indices)


from app.config import CONFIG  # noqa: E402 -- imported at bottom to keep the fixture section terse


# ==================================================================================================
# 14. TR-31 -- the CLI/operator-facing progress surface is aggregate-only too (iteration 23).
# ==================================================================================================


def test_tr31_format_cli_progress_line_serves_only_the_whitelisted_aggregates():
    """TR-31 (spec section 7.1, r5/r7 -- iteration 23 leak fix), unit level.

    ``format_cli_progress_line`` is the CLI's ONLY live-progress formatter. Given an internal
    progress dict that carries a full identity-bearing ``outcomes`` list and EXACT running event
    totals, the string it returns must carry none of that: no symbol, no date, no chunk time, no
    dataset id, no per-chunk outcome label, no exact count. The internal dict keeping them is
    correct and deliberate (checkpoint/recovery/audit) -- what section 7.1 forbids is SERVING
    them, on any transport."""
    progress = {
        "chunks_total": 4,
        "chunks_done": 3,
        "outcomes": [
            {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z",
             "outcome": "fetched", "detail": None, "dataset_id": "ds-aapl-0601",
             "trade_count": 4242, "quote_count": 91_337},
            {"symbol": "MSFT", "date": "2026-06-02", "start": "2026-06-02T13:30:00Z",
             "outcome": "failed", "detail": "vendor 500", "dataset_id": None,
             "trade_count": 0, "quote_count": 0},
            {"symbol": "RKLB", "date": "2026-06-03", "start": "2026-06-03T13:30:00Z",
             "outcome": "reused", "detail": None, "dataset_id": "ds-rklb-0603",
             "trade_count": 11, "quote_count": 22},
        ],
        "trades_total": 4253,
        "quotes_total": 91_359,
    }

    line = tr.format_cli_progress_line(progress, started_utc="2026-06-01T13:00:00Z")

    # --- nothing identity-bearing survives ------------------------------------------------------
    for forbidden in (
        "AAPL", "MSFT", "RKLB",                      # symbols
        "2026-06-01", "2026-06-02", "2026-06-03",    # dates
        "13:30", "T13:30:00Z",                       # chunk times
        "ds-aapl-0601", "ds-rklb-0603",              # dataset ids
        "vendor 500",                                # per-chunk failure detail
        "4242", "91337", "4253", "91359",            # exact event counts (per-chunk AND running)
    ):
        assert forbidden not in line, f"{forbidden!r} leaked into the CLI progress line: {line!r}"

    # No outcome-typed word survives in ANY form -- not as a realized verdict and not as a count
    # noun. TR-32 (owner ruling section F) removed the counters entirely: a coarse bucket would
    # still have an exact 0 -> 1 boundary, so a first failure would still be pinned as it crossed.
    for word in ("fetched", "reused", "unchanged", "failed"):
        assert word not in line, f"outcome-typed field {word!r} survived: {line!r}"

    # --- the safe aggregates ARE there ----------------------------------------------------------
    assert "[3/4]" in line and "75%" in line
    # TR-32 amendment 1: no volume field either -- running totals advance only on a fetched
    # chunk, so a bucket transition across a single-chunk advance would prove that outcome.
    assert "trades" not in line and "quotes" not in line
    assert "chunks/min" in line


def test_tr31_the_live_cli_run_never_prints_a_realized_symbol_day_outcome(tmp_path, monkeypatch, capsys):
    """TR-31 at the OPERATOR path, end to end -- the gap the pre-iteration-23 traps left open.

    ``test_tc6_...`` already sweeps the REST projection; this sweeps the CLI, which is the surface
    an operator actually watches during a real attended recording. The plan is monkeypatched to an
    explicit 3-chunk/2-symbol plan (the TC-6 precedent) so the walk stays fast and the exact
    identity tokens under test are known.

    The pre-fetch plan banner (``_print_plan``) legitimately shows the frozen universe -- an
    operator approving their own registered tranche is explicitly NOT the threat model (spec
    section 7.2's own note). So this asserts against the REALIZED PROGRESS LINES only: the
    per-member success/failure stream that would reveal the hidden partition."""
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
        sys, "argv", ["tick_recorder.py", "--symbols", "AAPL,MSFT", "--dates", "2026-06-01"],
    )
    fake_plan = [
        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z", "end": "2026-06-01T15:00:00Z"},
        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T15:00:00Z", "end": "2026-06-01T20:00:00Z"},
        {"symbol": "MSFT", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z", "end": "2026-06-01T20:00:00Z"},
    ]
    monkeypatch.setattr(tr, "plan_recorder_chunks", lambda symbols, dates: list(fake_plan))
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
    out = capsys.readouterr().out

    # The realized-progress stream is exactly the lines `_tick` emits. TR-32 put these on a coarse
    # milestone cadence, so this asserts the CONTENT contract, never a line-per-chunk count.
    progress_lines = [ln for ln in out.splitlines() if ln.startswith("  [")]
    assert progress_lines, "the operator must still get progress"

    for line in progress_lines:
        for forbidden in ("AAPL", "MSFT", "2026-06-01", "13:30", "15:00", "20:00"):
            assert forbidden not in line, f"{forbidden!r} leaked into a live progress line: {line!r}"
        assert "->" not in line, f"a per-chunk outcome arrow leaked: {line!r}"

    # ...and the operator still gets genuinely useful aggregate progress.
    assert "[3/3]" in progress_lines[-1] and "100%" in progress_lines[-1]

    # The pre-fetch plan banner is the sanctioned exception -- it may (and does) name the universe.
    assert "3 chunk(s) over 2 symbol-day(s)" in out


# ==================================================================================================
# 15. TR-32 -- the COMPOSED (differencing) leak: snapshots x the known plan (owner ruling, iter 23).
# ==================================================================================================


def _parse_outcome_counters(line: str) -> dict | None:
    """Every outcome-typed counter an operator can read off ONE progress line, or ``None`` when the
    line carries no outcome-typed information at all (the post-fix shape)."""
    import re

    found = {}
    for key in ("fetched", "reused", "unchanged", "failed"):
        m = re.search(rf"(\d+)\s+{key}\b", line)
        if m:
            found[key] = int(m.group(1))
    return found or None


def _reconstruct_outcomes_by_differencing(lines: list[str], plan: list[dict]) -> list[tuple]:
    """THE ATTACK (owner ruling section F). The operator knows the registered plan and its
    deterministic walk order, and watches every progress line. Difference each line's cumulative
    outcome counters against its predecessor: whenever exactly one counter advances by exactly one,
    that chunk's realized outcome is pinned -- and its identity is already known from the plan.

    Returns every (symbol, date, outcome) triple recovered WITH CERTAINTY."""
    recovered: list[tuple] = []
    prev = {"fetched": 0, "reused": 0, "unchanged": 0, "failed": 0}
    for idx, line in enumerate(lines):
        cur = _parse_outcome_counters(line)
        if cur is None:
            continue  # no outcome-typed information on this line -- nothing to difference
        advanced = [k for k, v in cur.items() if v - prev.get(k, 0) == 1]
        total_advance = sum(v - prev.get(k, 0) for k, v in cur.items())
        if len(advanced) == 1 and total_advance == 1 and idx < len(plan):
            recovered.append((plan[idx]["symbol"], plan[idx]["date"], advanced[0]))
        prev = {**prev, **cur}
    return recovered


def test_tr32_no_snapshot_sequence_plus_the_known_plan_pins_a_chunks_realized_outcome():
    """TR-32 (owner ruling 2026-08-21, section F) -- the COMPOSITION requirement r5/r7 actually
    imposes, which iteration 23's first fix (f54d0ee) did NOT satisfy.

    f54d0ee removed the explicit ``{symbol} {date} -> {outcome}`` string, but kept ONE line per
    completed chunk carrying EXACT cumulative ``fetched``/``reused``/``unchanged``/``failed``
    counters. Those two properties compose into a full break: the Nth line corresponds to the Nth
    chunk of a deterministic, operator-known plan, and differencing consecutive lines pins that
    chunk's realized outcome exactly. Verified before the fix -- the attack below reconstructed all
    four chunks' outcomes with an EXACT match to ground truth.

    The requirement is OUTCOME-based, not field-based: no sequence of operator-visible snapshots,
    combined with the known registered plan, may reveal a specific chunk's realized success or
    failure with certainty. Internal exact progress stays permitted (checkpoint/recovery/audit),
    and the TERMINAL batch report still discloses failures -- TR-4 REQUIRES that disclosure; what
    is forbidden is the progressive, per-member reconstruction during the run."""
    plan = [
        {"symbol": "AAPL", "date": "2026-06-01"}, {"symbol": "AAPL", "date": "2026-06-02"},
        {"symbol": "MSFT", "date": "2026-06-01"}, {"symbol": "MSFT", "date": "2026-06-02"},
        {"symbol": "PG", "date": "2026-06-01"},   {"symbol": "PG", "date": "2026-06-02"},
    ]
    realized = ["fetched", "fetched", "failed", "reused", "fetched", "unchanged"]

    progress = {
        "chunks_total": len(plan), "chunks_done": 0, "outcomes": [],
        "trades_total": 0, "quotes_total": 0,
    }
    lines: list[str] = []
    for outcome in realized:
        progress["chunks_done"] += 1
        progress["outcomes"].append({"outcome": outcome, "trade_count": 1_000, "quote_count": 5_000})
        progress["trades_total"] += 1_000
        progress["quotes_total"] += 5_000
        if tr.should_emit_cli_progress(progress["chunks_done"], progress["chunks_total"]):
            lines.append(tr.format_cli_progress_line(progress, started_utc="2026-06-01T13:00:00Z"))

    recovered = _reconstruct_outcomes_by_differencing(lines, plan)
    assert recovered == [], (
        "the differencing attack pinned a specific chunk's realized outcome from the operator-"
        f"visible progress stream: {recovered!r}\nlines were:\n" + "\n".join(lines)
    )

    # ...and, belt and braces, no line carries outcome-typed counters at all.
    for line in lines:
        assert _parse_outcome_counters(line) is None, f"outcome counters survived on: {line!r}"

    # The stream must still be genuinely useful: real completion progress and coarse volume.
    assert lines, "the operator must still get progress"
    assert "[6/6]" in lines[-1] and "100" in lines[-1]
    assert "chunks/min" in lines[-1]  # the safe throughput indicator the ruling permits


def test_tr32_the_live_cli_run_survives_the_differencing_attack_with_a_real_failed_chunk(
    tmp_path, monkeypatch, capsys
):
    """TR-32 end to end, against the REAL CLI with a REAL failing chunk -- the operator path, not a
    simulation. ``_FakeTickAdapter.raise_for`` fails exactly one known chunk; the attack then runs
    against the genuine captured stdout."""
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
        sys, "argv", ["tick_recorder.py", "--symbols", "AAPL,MSFT", "--dates", "2026-06-01"],
    )
    fake_plan = [
        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z", "end": "2026-06-01T15:00:00Z"},
        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T15:00:00Z", "end": "2026-06-01T20:00:00Z"},
        {"symbol": "MSFT", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z", "end": "2026-06-01T20:00:00Z"},
    ]
    monkeypatch.setattr(tr, "plan_recorder_chunks", lambda symbols, dates: list(fake_plan))
    tr._reset_recorder_throttle_for_tests()
    adapter = _FakeTickAdapter()
    adapter.raise_for = {("MSFT", "2026-06-01T13:30:00Z")}  # one known chunk genuinely fails
    app.dependency_overrides[get_market_adapter] = lambda: adapter
    journal = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    set_registry(ResearchRegistry(journal, CONFIG))
    try:
        tr.main()
    finally:
        set_registry(None)
        app.dependency_overrides.pop(get_market_adapter, None)
        journal.close()
        tr._reset_recorder_throttle_for_tests()

    out = capsys.readouterr().out
    progress_lines = [ln for ln in out.splitlines() if ln.startswith("  [")]
    recovered = _reconstruct_outcomes_by_differencing(progress_lines, fake_plan)
    assert recovered == [], (
        f"the live CLI stream leaked a specific chunk's realized outcome: {recovered!r}\n"
        + "\n".join(progress_lines)
    )
    for line in progress_lines:
        assert _parse_outcome_counters(line) is None, f"outcome counters survived on: {line!r}"


# ==================================================================================================
# 16. TR-32 across EVERY live transport -- the REST path (owner ruling 2026-08-21 amendment 1).
# ==================================================================================================


class _SteppingTickAdapter(_FakeTickAdapter):
    """Releases exactly ONE chunk at a time, so a test can poll the REST progress surface between
    consecutive chunk completions -- the precise cadence the differencing attack needs (an observer
    polling frequently enough that ``chunks_done`` advances by exactly one)."""

    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Semaphore(0)
        self.release = threading.Semaphore(0)

    def iter_historical_chunks(self, symbol, start, end):
        self.entered.release()
        assert self.release.acquire(timeout=15.0), "stepping adapter was never released"
        yield from super().iter_historical_chunks(symbol, start, end)


def test_tr32_rest_live_progress_carries_no_outcome_typed_counter_in_a_pollable_sequence():
    """TR-32 at the canonical SERVING OWNER (owner ruling amendment 1). ``_progress_view`` is what
    ``GET /research/desk/micro/recorder/compute`` forwards VERBATIM (via
    ``_copy_recorder_snapshot``), so its per-poll shape IS the REST contract -- fixing only the CLI
    formatter left this transport wide open.

    The attack is identical to the CLI one: poll often enough that ``chunks_done`` advances by
    exactly one, difference the cumulative outcome counters, and read the chunk's identity off the
    known deterministic plan."""
    progress = {
        "chunks_total": 5, "chunks_done": 0, "outcomes": [], "trades_total": 0, "quotes_total": 0,
    }
    views = []
    for outcome in ("fetched", "failed", "fetched", "reused", "unchanged"):
        progress["chunks_done"] += 1
        progress["outcomes"].append(
            {"outcome": outcome,
             "trade_count": 5_000 if outcome == "fetched" else 0,
             "quote_count": 20_000 if outcome == "fetched" else 0}
        )
        if outcome == "fetched":
            progress["trades_total"] += 5_000
            progress["quotes_total"] += 20_000
        views.append(tr._progress_view(progress, started_utc="2026-06-01T13:00:00Z", finished_utc=None))

    for view in views:
        for key in view:
            assert not key.startswith("chunks_fetched"), view
        leaked = [k for k in view if k in
                  ("chunks_fetched", "chunks_reused", "chunks_unchanged", "chunks_failed")]
        assert leaked == [], f"outcome-typed counters served on the REST projection: {leaked}"


def test_tr32_rest_volume_buckets_cannot_prove_a_specific_chunk_was_fetched():
    """TR-32, the SECOND attack the owner ruling names (amendment 1): the live volume buckets.

    ``trade_count``/``quote_count`` are populated at exactly ONE call site -- the ``"fetched"``
    branch (``tick_recorder.py``'s ``_chunk_entry`` call in ``run_tick_recording``). So the running
    totals advance ONLY for freshly fetched chunks. If a bucket TRANSITIONS while ``chunks_done``
    advances by exactly one, that single chunk provably contributed events, i.e. it was ``fetched``
    rather than failed/reused/unchanged -- a specific chunk's realized outcome, identified with
    certainty from the known plan. That is a genuine break, so live progress carries no volume
    field at all."""
    progress = {
        "chunks_total": 3, "chunks_done": 0, "outcomes": [], "trades_total": 0, "quotes_total": 0,
    }
    # chunk 1 reused (0 events), chunk 2 fetched enough to CROSS a bucket boundary, chunk 3 failed.
    steps = [("reused", 0), ("fetched", 1_500_000), ("failed", 0)]
    views = []
    for outcome, events in steps:
        progress["chunks_done"] += 1
        progress["outcomes"].append({"outcome": outcome, "trade_count": events, "quote_count": events})
        progress["trades_total"] += events
        progress["quotes_total"] += events
        views.append(tr._progress_view(progress, started_utc="2026-06-01T13:00:00Z", finished_utc=None))

    volume_keys = [k for k in views[0] if "trades_total" in k or "quotes_total" in k]
    assert volume_keys == [], (
        "live progress still serves a volume field; a bucket transition while chunks_done advances "
        f"by exactly one proves that chunk was fetched: {volume_keys}"
    )


def test_tr32_the_live_rest_route_survives_a_per_chunk_polling_attack(route_ctx, monkeypatch):
    """TR-32 end to end on the REAL route, polling between every chunk with a stepping adapter --
    the operator-observable transport, not a projection unit test."""
    client, _mgr, _adapter, _tmp = route_ctx
    from app.main import app, get_market_adapter

    fake_plan = [
        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z", "end": "2026-06-01T15:00:00Z"},
        {"symbol": "AAPL", "date": "2026-06-01", "start": "2026-06-01T15:00:00Z", "end": "2026-06-01T20:00:00Z"},
        {"symbol": "MSFT", "date": "2026-06-01", "start": "2026-06-01T13:30:00Z", "end": "2026-06-01T20:00:00Z"},
    ]
    monkeypatch.setattr(tr, "plan_recorder_chunks", lambda symbols, dates: list(fake_plan))
    stepper = _SteppingTickAdapter()
    stepper.raise_for = {("MSFT", "2026-06-01T13:30:00Z")}
    app.dependency_overrides[get_market_adapter] = lambda: stepper
    polls = []
    try:
        r = client.post(
            "/research/desk/micro/recorder/compute",
            json={"symbols": ["AAPL", "MSFT"], "dates": ["2026-06-01"]},
        )
        assert r.status_code == 200
        for _ in range(len(fake_plan)):
            assert stepper.entered.acquire(timeout=15.0)
            polls.append(client.get("/research/desk/micro/recorder/compute").json()["progress"])
            stepper.release.release()
        deadline = time.time() + 15
        while time.time() < deadline:
            snap = client.get("/research/desk/micro/recorder/compute").json()
            if snap["state"] != "running":
                polls.append(snap["progress"])
                break
            time.sleep(0.02)
    finally:
        app.dependency_overrides.pop(get_market_adapter, None)
        stepper.release.release()

    assert polls, "the attack needs at least one observed poll"
    forbidden = {"chunks_fetched", "chunks_reused", "chunks_unchanged", "chunks_failed"}
    for progress in polls:
        leaked = forbidden & set(progress)
        assert leaked == set(), f"REST poll leaked outcome-typed counters: {sorted(leaked)}"
        vol = [k for k in progress if "trades_total" in k or "quotes_total" in k]
        assert vol == [], f"REST poll leaked a volume field: {vol}"
