"""``micro_observer.py`` (Era "The Rapid Microscope" J-02) -- the streaming state-machine's

integration behavior over hand-crafted event sequences run through a REAL ``TapeEngine`` (the
``test_observer_equivalence.py`` pattern: construct an engine, ``add_observer``, feed events one
at a time via ``process_event``) plus the additive ``DatasetStore.replay(observer=...)`` wiring
and the TR-1/TR-17a/TR-17b traps against a small REAL committed tick fixture. Test-first contract:
TC-1, TC-2, TC-4, TC-5, TC-8, TC-9, TC-10 in ``docs/phases/goal-rapid-microscope-iter-2.md``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.research import micro_features as mf
from app.research.datasets import DatasetStore
from app.research.micro_observer import MicroObserver

TICKER = "TEST"
SCENARIO = "test scenario"

_SMALL_FIXTURE = Path(__file__).parent / "fixtures" / "datasets" / "6c9bf2c700d749e0993efd92c5807de3.json"


def _run(events: list, quote_size_unit: str = "unverified") -> list[dict]:
    """Feed ``events`` through a fresh engine + a fresh, attached ``MicroObserver``; return the
    observer's rows after ``finalize()``."""
    engine = TapeEngine(TICKER, SCENARIO, CONFIG)
    observer = MicroObserver(quote_size_unit=quote_size_unit)
    engine.add_observer(observer)
    for event in events:
        engine.process_event(event)
    observer.finalize()
    return observer.rows


def _non_close_out(rows: list[dict]) -> list[dict]:
    return [r for r in rows if not r.get("close_out")]


# --- TC-1: the additive observer= kwarg on DatasetStore.replay --------------------------------------


def _events_for_store() -> list:
    return [
        QuoteEvent(TICKER, 0.0, 99.99, 100.02, 100, 100),
        TradeEvent(TICKER, 0.1, 100.03, 10, Side.UNKNOWN),  # engine classifies: >= ask -> BUY
        TradeEvent(TICKER, 0.2, 99.99, 10, Side.UNKNOWN),  # <= bid -> SELL
    ]


def _plant(store: DatasetStore) -> dict:
    return store.record(
        symbol=TICKER, source="fixture", source_kind="fixture", source_id="fixture",
        split="train", window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
        data_feed="sip", epoch_anchor=0.0, events=_events_for_store(),
    )


class _ProbeObserver:
    def __init__(self) -> None:
        self.events: list = []

    def on_event(self, event, snapshot) -> None:
        self.events.append(event)


def test_tc1_replay_with_no_observer_arg_is_unaffected(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    no_observer_snapshots = list(store.replay(meta["id"], CONFIG))
    assert len(no_observer_snapshots) == 3
    # A second no-observer replay reproduces byte-identical snapshots (determinism preserved).
    again = list(store.replay(meta["id"], CONFIG))
    assert [s.tape_state for s in no_observer_snapshots] == [s.tape_state for s in again]
    assert [s.event_count for s in no_observer_snapshots] == [s.event_count for s in again]


def test_tc1_probe_observer_fires_once_per_event_in_stored_order(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    probe = _ProbeObserver()
    snapshots = list(store.replay(meta["id"], CONFIG, observer=probe))
    assert len(probe.events) == 3 == len(snapshots)
    assert [type(e).__name__ for e in probe.events] == ["QuoteEvent", "TradeEvent", "TradeEvent"]
    assert [e.timestamp for e in probe.events] == [0.0, 0.1, 0.2]


def test_tc1_attaching_a_micro_observer_does_not_change_the_replayed_snapshots(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    plain = list(store.replay(meta["id"], CONFIG))
    observed = list(store.replay(meta["id"], CONFIG, observer=MicroObserver(quote_size_unit="unverified")))
    assert [s.tape_state for s in plain] == [s.tape_state for s in observed]
    assert [s.bid for s in plain] == [s.bid for s in observed]
    assert [s.recent_trades for s in plain] == [s.recent_trades for s in observed]


def test_micro_observer_produces_one_row_per_trade_never_per_quote(tmp_path):
    store = DatasetStore(tmp_path / "datasets")
    meta = _plant(store)
    observer = MicroObserver(quote_size_unit="unverified")
    for _snap in store.replay(meta["id"], CONFIG, observer=observer):
        pass
    observer.finalize()
    assert len(_non_close_out(observer.rows)) == 2  # 2 TradeEvents, 1 QuoteEvent -- no quote row


# --- F-FLOW: cumulative delta, same-side run length, rolling imbalance (TC-8) -----------------------


def _flow_fixture_events() -> list:
    return [
        QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500),
        TradeEvent(TICKER, 1.0, 100.10, 10, Side.UNKNOWN),  # >= ask -> BUY
        TradeEvent(TICKER, 2.0, 100.10, 20, Side.UNKNOWN),  # >= ask -> BUY
        TradeEvent(TICKER, 3.0, 100.00, 5, Side.UNKNOWN),  # <= bid -> SELL
        TradeEvent(TICKER, 4.0, 100.10, 15, Side.UNKNOWN),  # >= ask -> BUY
        TradeEvent(TICKER, 5.0, 100.00, 8, Side.UNKNOWN),  # <= bid -> SELL
        TradeEvent(TICKER, 6.0, 100.00, 2, Side.UNKNOWN),  # <= bid -> SELL
    ]


def test_tc8_cumulative_delta_and_run_length_hand_computed():
    rows = _non_close_out(_run(_flow_fixture_events()))
    assert [r["side"] for r in rows] == ["buy", "buy", "sell", "buy", "sell", "sell"]
    assert [r["cumulative_delta"] for r in rows] == [10.0, 30.0, 25.0, 40.0, 32.0, 30.0]
    assert [r["same_side_run_length"] for r in rows] == [1, 2, 1, 1, 1, 2]
    assert all(r["cumulative_delta_unknown_excluded_count"] == 0 for r in rows)


def test_tc8_cumulative_delta_excludes_and_counts_unknown_sided_prints():
    # The FIRST print has no quote in effect and no prior trade -- the one honest UNKNOWN case.
    events = [
        TradeEvent(TICKER, 0.0, 100.0, 10, Side.UNKNOWN),  # no quote, no prior -> UNKNOWN
        QuoteEvent(TICKER, 0.5, 99.99, 100.02, 100, 100),
        TradeEvent(TICKER, 1.0, 100.03, 5, Side.UNKNOWN),  # >= ask -> BUY
    ]
    rows = _non_close_out(_run(events))
    assert rows[0]["side"] == "unknown"
    assert rows[0]["cumulative_delta"] == 0.0
    assert rows[0]["cumulative_delta_unknown_excluded_count"] == 1
    assert rows[0]["same_side_run_length"] == 0
    assert rows[1]["side"] == "buy"
    assert rows[1]["cumulative_delta"] == 5.0
    assert rows[1]["cumulative_delta_unknown_excluded_count"] == 1  # carried forward, not reset


def test_tc8_rolling_imbalance_20t_matches_the_pure_formula_within_the_window():
    rows = _non_close_out(_run(_flow_fixture_events()))
    # Fewer than 20 trades total -> the whole session is "the window" so far; hand-computed
    # cumulative buy/sell after each row: (10,0) (30,0) (30,5) (45,5) (45,13) (45,15).
    expected = [
        mf.rolling_imbalance(10, 0), mf.rolling_imbalance(30, 0), mf.rolling_imbalance(30, 5),
        mf.rolling_imbalance(45, 5), mf.rolling_imbalance(45, 13), mf.rolling_imbalance(45, 15),
    ]
    assert [r["rolling_imbalance_20t"] == pytest.approx(e) for r, e in zip(rows, expected)]
    for r, e in zip(rows, expected):
        assert r["rolling_imbalance_20t"] == pytest.approx(e)
        assert r["rolling_imbalance_5000sh"] == pytest.approx(e)  # also within the 5,000-share window


def test_tc8_side_source_distinguishes_quote_rule_tick_test_and_carried():
    events = [
        QuoteEvent(TICKER, 0.0, 99.99, 100.02, 100, 100),
        TradeEvent(TICKER, 1.0, 100.03, 5, Side.UNKNOWN),  # >= ask -> quote_rule
        TradeEvent(TICKER, 2.0, 100.01, 5, Side.UNKNOWN),  # strictly between, prior 100.03 -> tick_test (down)
        TradeEvent(TICKER, 3.0, 100.01, 5, Side.UNKNOWN),  # strictly between, price==prior -> carried
    ]
    rows = _non_close_out(_run(events))
    assert [r["side_source"] for r in rows] == ["quote_rule", "tick_test", "carried"]


def test_tc8_volume_burst_undefined_below_five_baseline_windows():
    # Only 6 trades total -- zero completed 20-trade tiles -> undefined (counted), never guessed.
    rows = _non_close_out(_run(_flow_fixture_events()))
    assert all(r["volume_burst_20t"] is None for r in rows)
    assert all(r["volume_burst_100t"] is None for r in rows)


def test_volume_burst_defined_once_five_baseline_tiles_complete():
    # 5 completed 20-trade tiles (100 trades) of volume 10 each, then a 6th (current, in-progress)
    # tile whose running volume so far is checked against the median baseline of 10.
    events: list = [QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500)]
    ts = 1.0
    for _tile in range(5):
        for _i in range(20):
            events.append(TradeEvent(TICKER, ts, 100.10, 1, Side.UNKNOWN))  # size 1 x 20 = tile volume 20
            ts += 1.0
    events.append(TradeEvent(TICKER, ts, 100.10, 40, Side.UNKNOWN))  # one more trade, size 40
    rows = _non_close_out(_run(events))
    last = rows[-1]
    # window_volume (total, trailing 20t) = 19 * 1 + 40 = 59 (the last 20 trades: 19 of size-1 + this one)
    assert last["volume_burst_20t"] == pytest.approx(59 / 20.0)  # median baseline of five 20-volume tiles = 20


# --- F-RESPONSE: absorption_score reuse, failed_aggression_score, response_asymmetry (TC-9) --------


def test_tc9_absorption_score_is_reused_verbatim_from_the_engine():
    engine = TapeEngine(TICKER, SCENARIO, CONFIG)
    observer = MicroObserver(quote_size_unit="unverified")
    engine.add_observer(observer)
    snap = None
    for event in _flow_fixture_events():
        snap = engine.process_event(event)
    assert observer.rows[-1]["absorption_score"] == snap.primary_features["absorption_score"]


def test_tc9_response_asymmetry_resolves_at_the_kth_subsequent_trade():
    events: list = [QuoteEvent(TICKER, 0.0, 100.00, 100.02, 500, 500)]
    ts = 1.0
    for _i in range(10):  # trades 1..10 at the initial quote
        events.append(TradeEvent(TICKER, ts, 100.02, 10, Side.UNKNOWN))  # >= ask -> BUY
        ts += 1.0
    events.append(QuoteEvent(TICKER, ts, 100.10, 100.12, 500, 500))  # the quote shifts
    ts += 1.0
    for _i in range(11):  # trades 11..21 at the shifted quote -- 21 trades total
        events.append(TradeEvent(TICKER, ts, 100.12, 10, Side.UNKNOWN))  # >= ask -> BUY
        ts += 1.0
    rows = _non_close_out(_run(events))
    assert len(rows) == 21
    # trade #1's mid was (100.00+100.02)/2=100.01; by trade #21 (K=20 subsequent trades later) the
    # mid is (100.10+100.12)/2=100.11 -- resolved on row 21 (index 20), attached to THAT row.
    row21_deferred = rows[20]["deferred"]
    resolved = [d for d in row21_deferred if d["kind"] == "response_asymmetry" and d["anchor_at"] == 1.0]
    assert len(resolved) == 1
    expected = mf.bps_move(100.01, 100.11)
    assert resolved[0]["value"] == pytest.approx(expected)
    assert resolved[0]["side"] == "buy"
    assert resolved[0]["available_at"] == resolved[0]["observed_through"]
    assert resolved[0]["unavailable"] is False
    # No PRIOR row (1..20) carries this anchor's completion -- it is attached exactly once.
    for row in rows[:20]:
        assert all(d["anchor_at"] != 1.0 for d in row["deferred"] if d["kind"] == "response_asymmetry")


def test_tc9_response_asymmetry_is_unavailable_when_the_session_ends_first():
    events: list = [QuoteEvent(TICKER, 0.0, 100.00, 100.02, 500, 500)]
    ts = 1.0
    for _i in range(5):  # only 5 trades -- far short of RESPONSE_K_TRADES (20)
        events.append(TradeEvent(TICKER, ts, 100.02, 10, Side.UNKNOWN))
        ts += 1.0
    rows = _run(events)  # includes the close-out row this time -- finalize() must sweep the pending anchors
    all_deferred = [d for row in rows for d in row["deferred"]]
    response_completions = [d for d in all_deferred if d["kind"] == "response_asymmetry"]
    assert len(response_completions) == 5  # every one of the 5 buy anchors swept at finalize
    assert all(d["unavailable"] is True and d["value"] is None for d in response_completions)


# === GAP B4 (goal-rapid-microscope-iter-17, TC-17): a session whose LAST event is a TRADE, not a
# quote -- finalize()'s session-end stamp equals the TRADE's own timestamp, numerically DIFFERENT
# from what it would be had the session ended on a quote instead (`self._last_event_ts` is set
# unconditionally in `_consume` for EVERY event type, before the trade/quote branch -- this test
# proves that behavior directly, on the close-out row itself, with a discriminating twin). ==========


def _events_ending_on_a_trade() -> list:
    """5 buy-aggressive trades (far short of RESPONSE_K_TRADES=20, so response_asymmetry stays
    pending into finalize()) -- the stream's OWN LAST event is the 5th TRADE, at ts=5.0."""
    events: list = [QuoteEvent(TICKER, 0.0, 100.00, 100.02, 500, 500)]
    ts = 1.0
    for _i in range(5):
        events.append(TradeEvent(TICKER, ts, 100.02, 10, Side.UNKNOWN))
        ts += 1.0
    return events  # last event: TradeEvent at ts=5.0


def test_gap_b4_a_trade_terminated_session_stamps_finalize_at_the_trades_own_timestamp():
    rows = _run(_events_ending_on_a_trade())
    close_out_rows = [r for r in rows if r.get("close_out")]
    assert len(close_out_rows) == 1
    close_out = close_out_rows[0]
    # the session's LAST event was the 5th trade, at ts=5.0 -- finalize()'s own stamp equals it.
    assert close_out["anchor_at"] == close_out["observed_through"] == close_out["available_at"] == 5.0
    pending = [d for d in close_out["deferred"] if d["kind"] == "response_asymmetry"]
    assert len(pending) == 5
    assert all(d["observed_through"] == d["available_at"] == 5.0 for d in pending)


def test_gap_b4_discriminating_twin_a_trailing_quote_moves_the_same_stamp_to_a_different_instant():
    """The discriminating twin (TC-17's own requirement: correct and corrupted-basis values must
    be numerically DIFFERENT, never coincidentally equal): the IDENTICAL 5-trade stream, PLUS one
    trailing QuoteEvent at ts=9.0 -- now the session ends on a QUOTE instead. finalize()'s own
    stamp moves to 9.0 -- proving the trade-terminated case's 5.0 is genuinely the trade's OWN
    timestamp, not some incidental default that would show up regardless of what the last event
    was."""
    events = _events_ending_on_a_trade() + [QuoteEvent(TICKER, 9.0, 100.00, 100.02, 500, 500)]
    rows = _run(events)
    close_out_rows = [r for r in rows if r.get("close_out")]
    assert len(close_out_rows) == 1
    close_out = close_out_rows[0]
    assert close_out["anchor_at"] == close_out["observed_through"] == close_out["available_at"] == 9.0
    # numerically DIFFERENT from the trade-terminated case's own 5.0 -- never coincidentally equal.
    assert close_out["observed_through"] != 5.0
    pending = [d for d in close_out["deferred"] if d["kind"] == "response_asymmetry"]
    assert len(pending) == 5
    assert all(d["observed_through"] == d["available_at"] == 9.0 for d in pending)
    assert all(d["observed_through"] != 5.0 for d in pending)


# --- F-LIQUIDITY: quote_imbalance, microprice, quote_depletion, refill_consistent (TC-10) ----------


def test_tc10_quote_imbalance_and_microprice_hand_computed():
    events = [
        QuoteEvent(TICKER, 0.0, 99.90, 100.10, 300, 100),
        TradeEvent(TICKER, 1.0, 100.10, 5, Side.UNKNOWN),
    ]
    rows = _non_close_out(_run(events))
    assert rows[0]["quote_imbalance"] == pytest.approx(mf.quote_imbalance(300, 100))
    assert rows[0]["microprice"] == pytest.approx(mf.microprice(99.90, 100.10, 300, 100))


def _depletion_events() -> list:
    return [
        QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500),  # ask run starts: price 100.10, size 500
        QuoteEvent(TICKER, 1.0, 100.00, 100.10, 500, 400),  # same price, size drops to 400
        QuoteEvent(TICKER, 2.0, 100.00, 100.10, 500, 300),  # same price, size drops to 300
        QuoteEvent(TICKER, 3.0, 100.00, 100.20, 500, 300),  # PRICE CHANGE -- resolves the old run
        TradeEvent(TICKER, 4.0, 100.20, 10, Side.UNKNOWN),  # first trade at/after resolution
    ]


def _one_ask_depletion(rows: list[dict]) -> dict:
    assert len(rows) == 1
    depletions = [d for d in rows[0]["deferred"] if d["kind"] == "quote_depletion" and d["side"] == "ask"]
    assert len(depletions) == 1
    return depletions[0]


def test_tc10_quote_depletion_resolves_at_a_price_change_attached_to_the_next_trade_row():
    """The VERIFIED-unit half of the contract: the run's own timing facts, and -- because
    ``quote_size_unit`` is verified -- the share-denominated magnitude itself, served.

    goal-rapid-microscope-iter-16 (TR-26, r6 owner ruling 2026-08-18): ``observed_through``/
    ``available_at`` corrected from the pre-fix ``2.0`` (the LAST same-price quote -- measurement
    end) to ``3.0`` (the price-CHANGING/REVEALING quote's own instant -- knowledge time). This is
    the specified behaviour fix itself, not a regression: the spec's own words are "measurement end
    != knowledge time" (section 3) -- the observer does not actually LEARN the run has ended until
    it sees the price-changing quote, so THAT instant is when the completion becomes available, even
    though the run's magnitude (500 - 300 = 200, unaffected) is still measured only over the
    same-price quotes that preceded it."""
    rows = _non_close_out(_run(_depletion_events(), quote_size_unit="shares"))
    d = _one_ask_depletion(rows)
    assert d["anchor_at"] == 0.0  # the run's own start
    assert d["observed_through"] == 3.0  # the REVEALING price-changing quote (r6) -- was 2.0 pre-fix
    assert d["available_at"] == 3.0
    assert d["value"] == pytest.approx(200.0)  # 500 - 300, unaffected by the timestamp fix
    assert d["unavailable"] is False
    assert d["refused"] is False
    assert d["refusal_reason"] is None


def test_tc7_tr18_quote_depletion_magnitude_is_refused_under_an_unverified_unit():
    """TR-18 at the STREAMING call site: the depletion magnitude is share-denominated CROSS-BASIS
    (spec section 3), so under an unverified ``quote_size_unit`` -- the state of all 18 legacy
    datasets -- it is refused with the closed-vocabulary reason, never served as a raw number. The
    run's unit-INVARIANT facts (availability triple, price, updates observed) are served either
    way, and ``unavailable`` stays False: the window closed, only its magnitude is not reportable."""
    rows = _non_close_out(_run(_depletion_events(), quote_size_unit="unverified"))
    d = _one_ask_depletion(rows)
    assert d["value"] is None
    assert d["refused"] is True
    assert d["refusal_reason"] == mf.CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT
    assert d["unavailable"] is False  # observed to completion -- refused, not missing
    # the unit-invariant facts are unaffected by the refusal
    assert d["anchor_at"] == 0.0
    # goal-rapid-microscope-iter-16 (TR-26): the same timing fix as TC-10 above -- the revealing
    # quote's own instant (3.0), not the last same-price quote (was 2.0 pre-fix). The unit gate
    # only ever governs `value`/`refused`/`refusal_reason`; it does not touch this timestamp.
    assert d["observed_through"] == 3.0
    assert d["available_at"] == 3.0
    assert d["price"] == pytest.approx(100.10)
    assert d["updates_observed"] == 2


def test_tc7_tr18_round_lots_is_a_verified_unit_for_the_depletion_magnitude_too():
    """The gate asks "verified?", never "shares?" -- ``round_lots`` is a RECORDED unit basis, so it
    serves the magnitude (in round lots) exactly as ``shares`` does."""
    rows = _non_close_out(_run(_depletion_events(), quote_size_unit="round_lots"))
    d = _one_ask_depletion(rows)
    assert d["value"] == pytest.approx(200.0)
    assert d["refused"] is False


def test_tc7_tr18_unit_invariant_liquidity_features_are_never_refused_by_the_gate():
    """The section 2.6 carve-out, counter-tested: quote imbalance and microprice compare quote
    sizes only to quote sizes WITHIN one dataset, so an unverified unit must NOT suppress them --
    a gate that refused everything would be as dishonest as one that refused nothing."""
    events = [
        QuoteEvent(TICKER, 0.0, 99.90, 100.10, 300, 100),
        TradeEvent(TICKER, 1.0, 100.10, 5, Side.UNKNOWN),
    ]
    rows = _non_close_out(_run(events, quote_size_unit="unverified"))
    assert rows[0]["quote_size_unit"] == "unverified"
    assert rows[0]["quote_imbalance"] == pytest.approx(mf.quote_imbalance(300, 100))
    assert rows[0]["microprice"] == pytest.approx(mf.microprice(99.90, 100.10, 300, 100))


def test_tc10_refill_consistent_true_when_size_is_restored_within_the_window():
    events = [
        QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500),
        TradeEvent(TICKER, 1.0, 100.10, 200, Side.UNKNOWN),  # lifts the ask (quote_rule) -- consumes 200
        QuoteEvent(TICKER, 2.0, 100.00, 100.10, 500, 200),  # ask size still down -- not yet restored
        QuoteEvent(TICKER, 3.0, 100.00, 100.10, 500, 500),  # restored to >= the pre-trade size
        TradeEvent(TICKER, 4.0, 100.10, 5, Side.UNKNOWN),  # first trade at/after resolution
    ]
    rows = _non_close_out(_run(events))
    refills = [d for row in rows for d in row["deferred"] if d["kind"] == "refill_consistent"]
    assert len(refills) == 1
    assert refills[0]["value"] is True
    assert refills[0]["side"] == "ask"
    assert refills[0]["anchor_at"] == 1.0
    assert refills[0]["observed_through"] == 3.0


def test_tc10_refill_consistent_false_when_the_window_expires_unresolved(monkeypatch):
    monkeypatch.setattr(mf, "REFILL_M_QUOTES", 2)  # shrink the window so the test stays small
    events = [
        QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500),
        TradeEvent(TICKER, 1.0, 100.10, 200, Side.UNKNOWN),  # lifts the ask -- consumes 200
        QuoteEvent(TICKER, 2.0, 100.00, 100.10, 500, 200),  # update 1: still not restored
        QuoteEvent(TICKER, 3.0, 100.00, 100.10, 500, 250),  # update 2 (== M): still short of 500 -> expires False
        TradeEvent(TICKER, 4.0, 100.10, 5, Side.UNKNOWN),
    ]
    rows = _non_close_out(_run(events))
    refills = [d for row in rows for d in row["deferred"] if d["kind"] == "refill_consistent"]
    assert len(refills) == 1
    assert refills[0]["value"] is False
    assert refills[0]["unavailable"] is False  # observed to completion -- a negative outcome, not missing


def _unfinished_depletion_events() -> list:
    """A depletion run the session CUTS SHORT: the ask price never changes and the run never
    reaches ``DEPLETION_WINDOW_QUOTES`` updates, so its window simply never ends."""
    return [
        QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500),  # ask run starts at 500
        TradeEvent(TICKER, 0.5, 100.10, 10, Side.UNKNOWN),
        QuoteEvent(TICKER, 1.0, 100.00, 100.10, 500, 400),  # same price, size drops
        QuoteEvent(TICKER, 2.0, 100.00, 100.10, 500, 100),  # ...and the stream ends here
    ]


@pytest.mark.parametrize("unit", ["shares", "round_lots", "unverified"])
def test_quote_depletion_is_unavailable_when_the_session_ends_before_the_window_closes(unit):
    """Audit regression (spec section 0's availability law, section 3's "ends at a price change or
    the bound"): a depletion window the session cut short NEVER ended, so ``finalize()`` must sweep
    it as ``unavailable`` (counted, never guessed) exactly like ``response_asymmetry``/
    ``refill_consistent`` -- never as a completed observation carrying a magnitude. Before the fix
    it was resolved with ``unavailable: False`` and, under a VERIFIED unit, a real number (400),
    asserting a window closure that never happened."""
    rows = _run(_unfinished_depletion_events(), quote_size_unit=unit)
    depletions = [d for row in rows for d in row["deferred"] if d["kind"] == "quote_depletion"]
    assert depletions, "the fixture must leave at least one depletion run open at session end"
    for d in depletions:
        assert d["unavailable"] is True
        assert d["value"] is None  # no magnitude for a window that never ended, at ANY unit basis
        assert d["refused"] is False  # nothing to refuse: a refusal claims the window DID close
        assert d["refusal_reason"] is None
        assert d["available_at"] == d["observed_through"] == 2.0  # the session's last event


def test_quote_depletion_that_genuinely_closes_is_still_a_completed_observation():
    """The counter-test to the one above -- the fix must not turn every depletion ``unavailable``:
    a run ended by a real price change still resolves with its magnitude and ``unavailable: False``."""
    rows = _non_close_out(_run(_depletion_events(), quote_size_unit="shares"))
    d = _one_ask_depletion(rows)
    assert d["unavailable"] is False
    assert d["value"] == pytest.approx(200.0)


# === TR-26: quote_depletion's revealing-quote availability (r6, spec section 3) =====================
# goal-rapid-microscope-iter-16 (J-10): a genuine production bug, fixed here. `_advance_depletion_
# run`'s price-change-termination branch used to resolve using the OLD run's own last-recorded
# `observed_through` (the last same-price quote) -- the r6 owner ruling (docs/rapid-validation-
# spec.md revision header, 2026-08-18) requires the REVEALING price-CHANGING quote's own instant
# instead ("measurement end != knowledge time"). TC-9 above is the corrected assertion (the fix
# itself); TC-10 below proves the OTHER termination path (hitting DEPLETION_WINDOW_QUOTES) was
# already correct and stays that way; TC-11 proves the fix is prefix-honest (TR-1-style) at the
# exact revealing instant; TC-12 is this trap's own non-vacuity mutation-proof.


def _bound_terminated_depletion_events() -> list:
    """A depletion run that terminates by hitting ``DEPLETION_WINDOW_QUOTES`` (20 same-side,
    same-price updates) -- NEVER a price change -- the OTHER termination path (spec section 1's own
    table), already correct before this iteration's fix (the bound-termination branch already
    stamps ``run["observed_through"] = ts`` on every same-price update, the 20th included, before
    checking the bound) and untouched by it; this fixture is this iteration's first DEDICATED test
    of that path."""
    events = [QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500)]  # run starts: price 100.10, size 500
    size = 500
    for i in range(1, mf.DEPLETION_WINDOW_QUOTES + 1):
        size -= 1  # any same-price update advances the run; the exact size path is not asserted
        events.append(QuoteEvent(TICKER, float(i), 100.00, 100.10, 500, size))
    events.append(TradeEvent(TICKER, float(mf.DEPLETION_WINDOW_QUOTES) + 1.0, 100.10, 10, Side.UNKNOWN))
    return events


def test_tc10_bound_terminated_depletion_resolves_at_the_bound_hitting_quotes_own_instant():
    events = _bound_terminated_depletion_events()
    rows = _non_close_out(_run(events, quote_size_unit="shares"))
    d = _one_ask_depletion(rows)
    assert d["unavailable"] is False
    assert d["available_at"] == d["observed_through"] == float(mf.DEPLETION_WINDOW_QUOTES)
    assert d["updates_observed"] == mf.DEPLETION_WINDOW_QUOTES


def test_tc11_truncating_strictly_before_the_revealing_quote_leaves_the_run_unresolved():
    """Truncate the stream strictly BEFORE the price-changing/revealing quote's own instant
    (``ts=3.0`` in ``_depletion_events()``) -- the run's only termination trigger never arrives, so
    it must surface as ``unavailable`` (counted, never guessed), exactly like any other deferred
    construct the session cuts short -- never a value computed as if the window had closed."""
    events = _depletion_events()
    truncated = [e for e in events if e.timestamp < 3.0]  # strictly before the revealer
    rows = _run(truncated, quote_size_unit="shares")
    depletions = [
        d for row in rows for d in row["deferred"] if d["kind"] == "quote_depletion" and d["side"] == "ask"
    ]
    assert len(depletions) == 1
    d = depletions[0]
    assert d["unavailable"] is True
    assert d["value"] is None
    assert d["available_at"] == d["observed_through"] == 2.0  # the last event genuinely seen


def test_tc11_truncating_at_the_revealing_quote_resolves_the_run_deterministically():
    """The counter-test: INCLUDING the revealing quote's own instant resolves the run immediately --
    deterministically, matching the full replay's own value -- even with no trade afterward to carry
    the completion; the close-out row (``finalize()``) attaches it, proving the resolution does not
    depend on a LATER trade ever occurring."""
    events = _depletion_events()
    truncated = [e for e in events if e.timestamp <= 3.0]  # at/after -> inclusive of the revealer
    rows = _run(truncated, quote_size_unit="shares")
    depletions = [
        d
        for row in rows
        for d in row["deferred"]
        if d["kind"] == "quote_depletion" and d["side"] == "ask" and d["anchor_at"] == 0.0
    ]
    assert len(depletions) == 1
    d = depletions[0]
    assert d["unavailable"] is False
    assert d["value"] == pytest.approx(200.0)
    assert d["available_at"] == d["observed_through"] == 3.0  # the revealing quote itself


def _depletion_events_with_a_differently_sized_revealing_quote() -> list:
    """``_depletion_events()``'s twin, except the REVEALING (price-changing) quote carries a
    deliberately DIFFERENT size (900) from the run's own last same-price size (300).

    ``_depletion_events()`` cannot tell the two magnitude rules apart: its revealing quote happens
    to carry ask size 300 -- byte-identical to the run's last same-price size -- so
    ``start_size - current_size`` computes 200 whether or not the revealing quote's size was
    (wrongly) folded into the run first."""
    return [
        QuoteEvent(TICKER, 0.0, 100.00, 100.10, 500, 500),  # ask run starts: price 100.10, size 500
        QuoteEvent(TICKER, 1.0, 100.00, 100.10, 500, 400),  # same price, size drops to 400
        QuoteEvent(TICKER, 2.0, 100.00, 100.10, 500, 300),  # same price, size drops to 300
        QuoteEvent(TICKER, 3.0, 100.00, 100.20, 500, 900),  # PRICE CHANGE -- and a DIFFERENT size
        TradeEvent(TICKER, 4.0, 100.20, 10, Side.UNKNOWN),  # first trade at/after resolution
    ]


def test_tr26_the_magnitude_is_measured_over_the_pre_change_run_never_the_revealing_quotes_own_size():
    """iter-16 audit (TR-26 trap-coverage hole): the r6 ruling moves only the availability STAMP to
    the revealing quote -- "measurement end != knowledge time". The MAGNITUDE must still be measured
    over the pre-change run alone (spec section 3; this iteration's own DEFINITION OF DONE: "the
    depletion MAGNITUDE stays computed from the pre-change run data, unaffected").

    TC-9's ``value == 200.0`` assertion cannot prove that on ``_depletion_events()``: that fixture's
    revealing quote carries the same size (300) the run already held, so folding the revealing
    quote's size into the run before resolving leaves ``value`` at 200.0 either way -- verified by
    mutating ``_advance_depletion_run`` to do exactly that, against which the whole file stayed
    green. This fixture separates the two rules: measured over the pre-change run alone the
    magnitude is 500 - 300 = 200; folding the revealing quote's own size (900) in first would make
    it 500 - 900 = -400 (a nonsensical NEGATIVE depletion), and this test fails."""
    rows = _non_close_out(_run(_depletion_events_with_a_differently_sized_revealing_quote(), quote_size_unit="shares"))
    d = _one_ask_depletion(rows)
    assert d["value"] == pytest.approx(200.0)  # 500 - 300, the pre-change run's own two sizes
    assert d["value"] != pytest.approx(-400.0)  # 500 - 900, the revealing quote's size folded in
    # ...and the availability stamp is still the revealing quote's own instant (the r6 fix itself),
    # so this fixture proves BOTH halves of the ruling at once, on the same run.
    assert d["anchor_at"] == 0.0
    assert d["observed_through"] == d["available_at"] == 3.0
    assert d["unavailable"] is False
    assert d["updates_observed"] == 2


def test_tc12_tr26_reverting_the_fix_makes_the_corrected_assertion_fail_restoring_it_passes(monkeypatch):
    """Non-vacuity, this round's binding rule (iteration 15's own opaque-pool regression test was
    proven structurally unable to fail -- every new trap this round must prove the opposite):
    monkeypatch in the EXACT pre-fix ``_advance_depletion_run`` (stamps the OLD run's own already-
    stale ``observed_through`` instead of threading the revealing quote's own ``ts`` through) and
    show the corrected TC-9 assertion (``observed_through == 3.0``) would FAIL against it --
    reproducing the exact pre-fix wrong value, ``2.0`` -- then restore (``monkeypatch.undo()``) and
    show it passes again, byte-identically to the shipped fix."""
    import app.research.micro_observer as mo

    def _pre_fix_advance_depletion_run(self, side, price, size, ts):
        run = self._depletion_run[side]
        if run is None or run["price"] != price:
            if run is not None:
                self._resolve_depletion(side, run)  # BUG: stamps the OLD run's own stale observed_through
            self._depletion_run[side] = {
                "run_start_ts": ts, "price": price, "start_size": size, "current_size": size,
                "updates_seen": 0, "observed_through": ts,
            }
            return
        run["current_size"] = size
        run["updates_seen"] += 1
        run["observed_through"] = ts
        if run["updates_seen"] >= mf.DEPLETION_WINDOW_QUOTES:
            self._resolve_depletion(side, run)
            self._depletion_run[side] = None

    monkeypatch.setattr(mo.MicroObserver, "_advance_depletion_run", _pre_fix_advance_depletion_run)
    rows = _non_close_out(_run(_depletion_events(), quote_size_unit="shares"))
    d = _one_ask_depletion(rows)
    # The exact leaked/incorrect value the pre-fix code produces -- proving the corrected assertion
    # (observed_through == 3.0) WOULD fail against this reverted code.
    assert d["observed_through"] == 2.0
    assert d["observed_through"] != 3.0

    monkeypatch.undo()
    rows_restored = _non_close_out(_run(_depletion_events(), quote_size_unit="shares"))
    d_restored = _one_ask_depletion(rows_restored)
    assert d_restored["observed_through"] == 3.0


def test_refill_consistent_only_registers_on_a_confirmed_quote_rule_execution():
    # A tick-test-decided trade never confirms it executed AGAINST the displayed quote -- no refill
    # check should register for it (module docstring's own gating rule).
    events = [
        QuoteEvent(TICKER, 0.0, 99.00, 101.00, 500, 500),  # a wide quote -- the next print is mid-spread
        TradeEvent(TICKER, 1.0, 100.00, 50, Side.UNKNOWN),  # strictly between -> no prior trade -> unknown
        TradeEvent(TICKER, 2.0, 100.01, 50, Side.UNKNOWN),  # strictly between, tick_test (up)
        QuoteEvent(TICKER, 3.0, 99.00, 101.00, 500, 999),  # any subsequent quote update
    ]
    rows = _non_close_out(_run(events))
    for row in rows:
        assert all(d["kind"] != "refill_consistent" for d in row["deferred"])


# --- TR-1 / TR-17a / TR-17b against a REAL small committed tick fixture -----------------------------


def _load_real_fixture_events(tmp_path) -> tuple[DatasetStore, str]:
    assert _SMALL_FIXTURE.exists(), f"missing committed fixture {_SMALL_FIXTURE}"
    root = tmp_path / "datasets"
    root.mkdir()
    (root / _SMALL_FIXTURE.name).write_bytes(_SMALL_FIXTURE.read_bytes())
    store = DatasetStore(root)
    dataset_id = _SMALL_FIXTURE.stem
    return store, dataset_id


def test_tr1_truncated_replay_reproduces_the_full_runs_prefix_byte_identically(tmp_path):
    store, dataset_id = _load_real_fixture_events(tmp_path)
    all_events = store.load_events(dataset_id)
    full_rows = _non_close_out(_run(all_events))

    for cut in (1, len(all_events) // 3, (2 * len(all_events)) // 3):
        truncated_rows = _non_close_out(_run(all_events[:cut]))
        assert truncated_rows == full_rows[: len(truncated_rows)], f"diverged at cut={cut}"


def test_tr1_one_additional_tail_event_changes_no_prior_row(tmp_path):
    store, dataset_id = _load_real_fixture_events(tmp_path)
    all_events = store.load_events(dataset_id)
    cut = len(all_events) // 2
    shorter = _non_close_out(_run(all_events[:cut]))
    longer = _non_close_out(_run(all_events[: cut + 1]))
    assert shorter == longer[: len(shorter)]


def test_tr17a_deferred_completions_available_at_equals_observed_through(tmp_path):
    store, dataset_id = _load_real_fixture_events(tmp_path)
    rows = _run(store.load_events(dataset_id))
    checked = 0
    for row in rows:
        for item in row["deferred"]:
            assert item["available_at"] == item["observed_through"]
            checked += 1
    assert checked > 0  # the fixture genuinely exercises at least one deferred completion


def test_tr18_real_fixture_serves_no_share_denominated_magnitude_under_an_unverified_unit(tmp_path):
    """TR-18's whole-stream sweep against the REAL committed tick fixture (the shape every one of
    the 18 legacy datasets has): under ``quote_size_unit: "unverified"``, NO deferred completion of
    any cross-basis share-denominated kind anywhere in the stream carries a numeric value -- the
    per-event oracle above proves the rule, this proves nothing in a real replay escapes it."""
    store, dataset_id = _load_real_fixture_events(tmp_path)
    rows = _run(store.load_events(dataset_id), quote_size_unit="unverified")
    cross_basis = [
        d
        for row in rows
        for d in row["deferred"]
        if d["kind"] in mf.CROSS_BASIS_SHARE_DENOMINATED_KINDS
    ]
    assert cross_basis, "the fixture must genuinely exercise a cross-basis deferred construct"
    assert all(d["value"] is None for d in cross_basis)
    # The two honest states are DIFFERENT and must not be conflated: a window that CLOSED is
    # refused (the unit gate withheld its magnitude); a window the session cut short is
    # ``unavailable`` (spec section 0) and has no magnitude to refuse in the first place.
    completed = [d for d in cross_basis if not d["unavailable"]]
    unfinished = [d for d in cross_basis if d["unavailable"]]
    assert completed, "the fixture must genuinely exercise a CLOSED depletion window"
    assert all(d["refused"] is True for d in completed)
    assert all(d["refusal_reason"] == mf.CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT for d in completed)
    assert all(d["refused"] is False and d["refusal_reason"] is None for d in unfinished)


def test_tr18_the_same_real_fixture_serves_those_magnitudes_once_the_unit_is_verified(tmp_path):
    """The other half: the gate refuses on the UNIT, never on the feature -- the identical replay
    under a verified unit serves genuine magnitudes, so the refusal above is a unit judgment and
    not a silently disabled feature."""
    store, dataset_id = _load_real_fixture_events(tmp_path)
    rows = _run(store.load_events(dataset_id), quote_size_unit="shares")
    cross_basis = [
        d
        for row in rows
        for d in row["deferred"]
        if d["kind"] in mf.CROSS_BASIS_SHARE_DENOMINATED_KINDS
    ]
    assert cross_basis
    assert all(d["refused"] is False and d["refusal_reason"] is None for d in cross_basis)
    assert any(d["value"] is not None and d["value"] != 0 for d in cross_basis)
    # ...and a VERIFIED unit still never invents a magnitude for a window the session cut short.
    assert all(d["value"] is None for d in cross_basis if d["unavailable"])


def test_tr17b_truncating_at_an_instant_reproduces_exactly_the_rows_with_available_at_le_t(tmp_path):
    store, dataset_id = _load_real_fixture_events(tmp_path)
    all_events = store.load_events(dataset_id)
    full_rows = _non_close_out(_run(all_events))
    t = all_events[len(all_events) // 2].timestamp
    truncated_events = [e for e in all_events if e.timestamp <= t]
    truncated_rows = _non_close_out(_run(truncated_events))
    expected = [r for r in full_rows if r["available_at"] <= t]
    assert truncated_rows == expected
    assert all(r["available_at"] <= t for r in truncated_rows)
    assert not any(r["available_at"] > t for r in truncated_rows)
