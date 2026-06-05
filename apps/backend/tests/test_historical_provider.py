"""HistoricalProvider (J-11): logical timestamp mapping + deterministic REAL-fixture replay.

The committed fixture is REAL captured Alpaca data (Ford, a fixed 2-minute past window). It is
NOT synthesized — replaying it through the SAME engine the simulator uses populates every
cockpit value and is reproducible run-to-run, which is the in-loop evidence for J-11.
"""

import pytest

from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.providers.adapters.base import HistoricalWindow, RawQuote, RawTrade
from app.providers.base import QuoteEvent, Side, TradeEvent
from app.providers.historical import HistoricalProvider
from app.serializers import HEADLINE_FEATURES
from fakes import load_fixture_window

VALID_STATES = {
    "buyer_control",
    "seller_control",
    "bid_absorption",
    "ask_absorption",
    "unclear",
}


def _replay(window: HistoricalWindow, scenario: str = "historical TEST") -> TapeEngine:
    provider = HistoricalProvider(window.symbol, window, scenario)
    engine = TapeEngine(window.symbol, provider.scenario, CONFIG)
    for event in provider.stream():
        engine.process_event(event)
    return engine


# --- Timestamp mapping: logical, monotonic non-decreasing, from window start ----------------

def test_timestamps_are_logical_offsets_from_window_start():
    # Raw epochs deliberately out of order and far from zero; the provider must emit logical
    # offsets from the EARLIEST event (first event at 0.0), monotonic non-decreasing.
    quotes = (RawQuote(1000.0, 1.0, 1.02, 10, 10), RawQuote(1002.0, 1.0, 1.02, 10, 10))
    trades = (RawTrade(1001.0, 1.01, 100), RawTrade(1003.0, 1.02, 100))
    events = list(HistoricalProvider("X", HistoricalWindow("X", trades, quotes), "s").stream())

    timestamps = [e.timestamp for e in events]
    assert timestamps[0] == 0.0
    assert timestamps == sorted(timestamps)  # monotonic non-decreasing
    assert timestamps == [0.0, 1.0, 2.0, 3.0]  # epoch - 1000.0
    # No wall-clock leaked in: every timestamp is a small logical offset, not an epoch.
    assert all(0.0 <= t <= 3.0 for t in timestamps)


def test_quote_is_delivered_before_trade_at_the_same_instant():
    # A trade and a quote share the exact epoch; the quote MUST come first so the in-effect
    # quote is set before the engine classifies the trade.
    window = HistoricalWindow(
        "X", trades=(RawTrade(5.0, 1.0, 100),), quotes=(RawQuote(5.0, 0.99, 1.01, 10, 10),)
    )
    events = list(HistoricalProvider("X", window, "s").stream())
    assert isinstance(events[0], QuoteEvent)
    assert isinstance(events[1], TradeEvent)
    assert events[0].timestamp == events[1].timestamp == 0.0


def test_trades_are_yielded_as_unknown_side():
    window = HistoricalWindow(
        "X", trades=(RawTrade(0.0, 1.0, 100), RawTrade(1.0, 1.0, 100)),
        quotes=(RawQuote(0.0, 0.99, 1.01, 10, 10),),
    )
    trades = [e for e in HistoricalProvider("X", window, "s").stream() if isinstance(e, TradeEvent)]
    assert trades and all(t.side is Side.UNKNOWN for t in trades)


def test_scenario_label_is_carried_through():
    window, _ = load_fixture_window()
    provider = HistoricalProvider("F", window, "historical F 2026-06-02T15:00–15:02")
    assert provider.scenario == "historical F 2026-06-02T15:00–15:02"


def test_empty_window_streams_nothing():
    window = HistoricalWindow("X", trades=(), quotes=())
    assert list(HistoricalProvider("X", window, "s").stream()) == []


# --- Deterministic REAL-fixture replay: every cockpit value populated, reproducible ---------

def test_real_fixture_replay_populates_every_cockpit_value():
    window, raw = load_fixture_window()
    assert raw["source"] == "alpaca" and raw["trades"], "fixture must be real captured data"

    snap = _replay(window).snapshot()

    # Market: bid/ask/spread/last all real numbers; spread == ask - bid (single source).
    assert snap.bid is not None and snap.ask is not None and snap.last is not None
    assert snap.spread == pytest.approx(snap.ask - snap.bid)

    # Recent trades populated with price/size/side.
    assert snap.recent_trades
    row = snap.recent_trades[0]
    assert row.price > 0 and row.size > 0 and row.side in {"buy", "sell", "unknown"}

    # Every headline feature is a real number.
    primary = snap.primary_features
    for name in HEADLINE_FEATURES:
        assert isinstance(primary[name], float)

    # A real tape state + confidence. This fixed real window resolves to bid_absorption (heavy
    # selling absorbed at a holding bid) at high confidence — the keystone price-impact case.
    assert snap.warm is True
    assert snap.tape_state in VALID_STATES
    assert snap.tape_state == "bid_absorption"
    assert snap.confidence >= CONFIG.reasonable_confidence

    # Observations + an event log with at least one real state transition.
    assert snap.observations
    assert snap.event_log
    assert any(m.startswith("Tape state changed to") for m in snap.event_log)


def test_real_fixture_replay_is_reproducible():
    window, _ = load_fixture_window()
    first = _replay(window).snapshot()
    second = _replay(window).snapshot()  # independent engine, same window

    assert first.tape_state == second.tape_state
    assert first.confidence == second.confidence
    assert first.event_count == second.event_count
    assert first.bid == second.bid and first.ask == second.ask and first.last == second.last
    assert first.features == second.features  # identical per-window feature values
    assert first.event_log == second.event_log


# --- J-16: resolved aggressor side (quote rule + Lee-Ready tick-test fallback) ---------------
#
# The authoritative, offline, no-creds proof that the tick-test fallback materially reduces the
# `unknown` fraction on REAL data (the iter-2 lesson: prove it in-loop against the committed
# real-vendor fixture, never with synthesized trades). The quote-only reference below is an
# independent re-implementation of the OLD rule, so "strictly lower than quote-only" is an honest
# comparison and not a tautology against the engine's new code.


def _replay_capturing_sides(window: HistoricalWindow) -> tuple[TapeEngine, list[str]]:
    """Replay the window through the real engine, capturing each TRADE's DISPLAYED side.

    Each captured side is read from the canonical snapshot (the freshly appended
    ``recent_trades[0]`` after the trade tick) — the exact value the cockpit shows. No second
    side computation is introduced; we only observe the engine's one value per print.
    """
    provider = HistoricalProvider(window.symbol, window, "historical SIDE")
    engine = TapeEngine(window.symbol, provider.scenario, CONFIG)
    sides: list[str] = []
    for event in provider.stream():
        snap = engine.process_event(event)
        if isinstance(event, TradeEvent):
            sides.append(snap.recent_trades[0].side)  # the just-appended row's side
    return engine, sides


def _quote_only_sides(window: HistoricalWindow) -> list[str]:
    """The OLD quote-rule-only classification over the same ordered stream (reference baseline).

    Deliberately independent of ``app.engine.aggressor`` so the improvement comparison is honest:
    price >= ask => buy, price <= bid => sell, otherwise (incl. no quote yet) => unknown.
    """
    provider = HistoricalProvider(window.symbol, window, "historical QO")
    quote: QuoteEvent | None = None
    sides: list[str] = []
    for event in provider.stream():
        if isinstance(event, QuoteEvent):
            quote = event
        else:  # TradeEvent
            if quote is None:
                sides.append(Side.UNKNOWN.value)
            elif event.price >= quote.ask:
                sides.append(Side.BUY.value)
            elif event.price <= quote.bid:
                sides.append(Side.SELL.value)
            else:
                sides.append(Side.UNKNOWN.value)
    return sides


def _unknown_fraction(sides: list[str]) -> float:
    return sides.count(Side.UNKNOWN.value) / len(sides) if sides else 0.0


def test_tick_test_reduces_unknown_fraction_on_real_fixture():
    # J-16 keystone: the resolved `unknown` fraction is far lower than the quote-only rule AND
    # below a stated bound. On the committed Ford window the quote-only rule leaves ~20% of prints
    # `unknown` (the half-cent mid-spread prints inside a penny quote); the tick test resolves them.
    window, raw = load_fixture_window()
    assert raw["source"] == "alpaca" and raw["trades"], "fixture must be real captured data"

    _engine, two_stage_sides = _replay_capturing_sides(window)
    quote_only_sides = _quote_only_sides(window)

    assert len(two_stage_sides) == len(quote_only_sides) == len(raw["trades"])  # all 65 prints

    two_stage_unknown = _unknown_fraction(two_stage_sides)
    quote_only_unknown = _unknown_fraction(quote_only_sides)

    # The quote-only baseline really does leave a meaningful chunk unknown (else there is nothing
    # to prove); the two-stage rule is strictly lower AND under the stated bound.
    assert quote_only_unknown > 0.15
    assert two_stage_unknown < quote_only_unknown  # strictly lower (the fidelity gain)
    assert two_stage_unknown <= 0.05  # stated bound: recent-trades no longer dominated by unknown

    # The large majority of prints carry a resolved buy/sell side (J-16 acceptance).
    resolved = sum(1 for s in two_stage_sides if s in (Side.BUY.value, Side.SELL.value))
    assert resolved / len(two_stage_sides) >= 0.90


def test_tick_test_resolves_a_mid_spread_print_the_quote_rule_left_unknown():
    # A concrete, named example: at least one print is `unknown` under the quote-only rule but
    # `buy`/`sell` under the two-stage rule, at the SAME index — i.e. the tick test (not a quote
    # change) is what resolved it. Proves the fallback fires INSIDE the spread on real data.
    window, _ = load_fixture_window()
    _engine, two_stage_sides = _replay_capturing_sides(window)
    quote_only_sides = _quote_only_sides(window)

    rescued = [
        i
        for i, (qo, ts) in enumerate(zip(quote_only_sides, two_stage_sides))
        if qo == Side.UNKNOWN.value and ts in (Side.BUY.value, Side.SELL.value)
    ]
    assert rescued, "expected the tick test to resolve >=1 print the quote rule left unknown"


def test_real_fixture_sides_are_deterministic():
    # Determinism: replaying the same ordered stream twice yields identical per-print sides AND
    # identical aggressive ratios / net aggressive volume (pure function of the stream — no
    # wall-clock, no randomness).
    window, _ = load_fixture_window()
    engine_a, sides_a = _replay_capturing_sides(window)
    engine_b, sides_b = _replay_capturing_sides(window)

    assert sides_a == sides_b  # identical resolved sides, print for print
    fa = engine_a.snapshot().primary_features
    fb = engine_b.snapshot().primary_features
    for name in ("aggressive_buy_ratio", "aggressive_sell_ratio", "net_aggressive_volume"):
        assert fa[name] == fb[name]


def test_displayed_side_equals_feature_counted_side_single_source():
    # Single source of truth: the side shown in `recent_trades` is the SAME value the
    # FeatureEngine counted. The whole 2-minute window fits inside the 300s feature window (no
    # eviction), so net_aggressive_volume there counts every print exactly once; reconstructing
    # net volume from the DISPLAYED sides must reproduce the engine's reported number.
    window, raw = load_fixture_window()
    engine, displayed_sides = _replay_capturing_sides(window)

    sizes = [t["size"] for t in raw["trades"]]
    assert len(sizes) == len(displayed_sides)
    reconstructed_net = sum(
        size if side == Side.BUY.value else -size if side == Side.SELL.value else 0
        for side, size in zip(displayed_sides, sizes)
    )

    full_window = engine.snapshot().features[CONFIG.window_label(300)]
    assert full_window["net_aggressive_volume"] == float(reconstructed_net)


def test_empty_window_produces_no_fabricated_side():
    # Honesty: an empty/silent stream yields no trades, hence no sides — nothing is fabricated.
    empty = HistoricalWindow("X", trades=(), quotes=())
    _engine, sides = _replay_capturing_sides(empty)
    assert sides == []
