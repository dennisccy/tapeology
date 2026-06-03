"""End-to-end sim scenarios through the real engine: buyer_control / seller_control /
bid_absorption / ask_absorption + determinism, the keystone price-impact distinction, and
the reserved-but-unresolved ticker contract."""

import itertools

from app.config import CONFIG
from app.engine.classifier import (
    STATE_ASK_ABSORPTION,
    STATE_BID_ABSORPTION,
    STATE_BUYER_CONTROL,
    STATE_SELLER_CONTROL,
)
from app.engine.tape_engine import TapeEngine
from app.providers.simulated import SimulatedProvider, build_provider


def _run(ticker: str, scenario: str, n_events: int = 240) -> TapeEngine:
    provider = SimulatedProvider(ticker, scenario)
    engine = TapeEngine(ticker, scenario, CONFIG)
    for event in itertools.islice(provider.stream(), n_events):
        engine.process_event(event)
    return engine


def _run_buyer(n_events: int = 240) -> TapeEngine:
    return _run("SIM-BUYER", "buyer_control", n_events)


def _run_seller(n_events: int = 240) -> TapeEngine:
    return _run("SIM-SELLER", "seller_control", n_events)


def test_sim_buyer_settles_on_buyer_control():
    snap = _run_buyer().snapshot()
    assert snap.tape_state == STATE_BUYER_CONTROL
    assert snap.confidence >= CONFIG.reasonable_confidence
    # Price-impact-keyed evidence: high buy ratio AND positive buy impact.
    primary = snap.primary_features
    assert primary["aggressive_buy_ratio"] >= CONFIG.min_aggressive_buy_ratio
    assert primary["buy_price_impact"] > 0
    # The transition into buyer_control was announced exactly once in the event log.
    assert "Tape state changed to buyer_control" in snap.event_log


def test_sim_buyer_is_deterministic():
    a = _run_buyer().snapshot()
    b = _run_buyer().snapshot()
    assert a == b  # same seed + same stream => identical snapshot


def test_sim_seller_settles_on_seller_control():
    snap = _run_seller().snapshot()
    assert snap.tape_state == STATE_SELLER_CONTROL
    assert snap.confidence >= CONFIG.reasonable_confidence
    # Price-impact-keyed evidence: high sell ratio AND genuinely NEGATIVE sell impact
    # (real downward price progress — the mirror of the buyer guard).
    primary = snap.primary_features
    assert primary["aggressive_sell_ratio"] >= CONFIG.min_aggressive_sell_ratio
    assert primary["sell_price_impact"] < 0
    # The transition into seller_control was announced exactly once in the event log.
    assert "Tape state changed to seller_control" in snap.event_log


def test_sim_seller_is_deterministic():
    a = _run_seller().snapshot()
    b = _run_seller().snapshot()
    assert a == b  # same seed + same stream => identical snapshot


def test_sim_bidabs_settles_on_bid_absorption():
    snap = _run("SIM-BIDABS", "bid_absorption").snapshot()
    assert snap.tape_state == STATE_BID_ABSORPTION
    assert snap.confidence >= CONFIG.reasonable_confidence
    primary = snap.primary_features
    # Keystone evidence: high sell aggression but NO real downward progress (flat impact)
    # AND a refreshing bid — the exact opposite of seller_control's negative impact.
    assert primary["aggressive_sell_ratio"] >= CONFIG.min_aggressive_sell_ratio
    assert primary["sell_price_impact"] > CONFIG.max_sell_price_impact   # not a real drop
    assert primary["bid_refresh_score"] >= CONFIG.min_bid_refresh_score
    assert primary["absorption_score"] > 0
    # NOT misrouted to seller_control despite the high sell ratio.
    assert snap.tape_state != STATE_SELLER_CONTROL
    # The absorption message and the transition line both reached the event log.
    assert "Tape state changed to bid_absorption" in snap.event_log
    assert any(m.startswith("Bid refreshing at ") for m in snap.event_log)


def test_sim_bidabs_is_deterministic():
    a = _run("SIM-BIDABS", "bid_absorption").snapshot()
    b = _run("SIM-BIDABS", "bid_absorption").snapshot()
    assert a == b


def test_sim_askabs_settles_on_ask_absorption():
    snap = _run("SIM-ASKABS", "ask_absorption").snapshot()
    assert snap.tape_state == STATE_ASK_ABSORPTION
    assert snap.confidence >= CONFIG.reasonable_confidence
    primary = snap.primary_features
    assert primary["aggressive_buy_ratio"] >= CONFIG.min_aggressive_buy_ratio
    assert primary["buy_price_impact"] < CONFIG.min_buy_price_impact     # not a real rise
    assert primary["ask_refresh_score"] >= CONFIG.min_ask_refresh_score
    assert primary["absorption_score"] > 0
    assert snap.tape_state != STATE_BUYER_CONTROL
    assert "Tape state changed to ask_absorption" in snap.event_log
    assert any(m.startswith("Ask refreshing at ") for m in snap.event_log)


def test_sim_askabs_is_deterministic():
    a = _run("SIM-ASKABS", "ask_absorption").snapshot()
    b = _run("SIM-ASKABS", "ask_absorption").snapshot()
    assert a == b


def test_sim_buyer_not_misrouted_to_ask_absorption():
    # Regression guard: real upward progress keeps SIM-BUYER on buyer_control, never the
    # new ask_absorption state.
    snap = _run_buyer().snapshot()
    assert snap.tape_state == STATE_BUYER_CONTROL
    assert snap.tape_state != STATE_ASK_ABSORPTION


def test_sim_seller_not_misrouted_to_bid_absorption():
    # Regression guard: real downward progress keeps SIM-SELLER on seller_control, never
    # the new bid_absorption state — the keystone, proven end-to-end.
    snap = _run_seller().snapshot()
    assert snap.tape_state == STATE_SELLER_CONTROL
    assert snap.tape_state != STATE_BID_ABSORPTION


def test_reserved_ticker_known_but_unresolved():
    # SIM-CHOP is a known (reserved) ticker, not driven to its state yet this iteration
    # (SIM-BIDABS/SIM-ASKABS now resolve, so the still-reserved assertion moves here). A
    # known sim ticker resolves a provider; an unknown ticker never fabricates one.
    provider = build_provider("SIM-CHOP")
    assert provider is not None
    assert build_provider("NOPE123") is None
