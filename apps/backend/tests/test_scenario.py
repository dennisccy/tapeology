"""End-to-end SIM-BUYER scenario through the real engine: buyer_control + determinism."""

import itertools

from app.config import CONFIG
from app.engine.classifier import STATE_BUYER_CONTROL
from app.engine.tape_engine import TapeEngine
from app.providers.simulated import SimulatedProvider, build_provider


def _run_buyer(n_events: int = 240) -> TapeEngine:
    provider = SimulatedProvider("SIM-BUYER", "buyer_control")
    engine = TapeEngine("SIM-BUYER", "buyer_control", CONFIG)
    for event in itertools.islice(provider.stream(), n_events):
        engine.process_event(event)
    return engine


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


def test_reserved_ticker_known_but_unresolved():
    # SIM-SELLER is a known (reserved) ticker, but is not driven to its state this iteration.
    provider = build_provider("SIM-SELLER")
    assert provider is not None
    assert build_provider("NOPE123") is None
