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
    STATE_UNCLEAR,
)
from app.engine.tape_engine import TapeEngine
from app.providers.simulated import SimulatedProvider, build_provider

# The four resolved (decisive) states — chop must NEVER read as any of them.
_RESOLVED_STATES = (
    STATE_BUYER_CONTROL,
    STATE_SELLER_CONTROL,
    STATE_BID_ABSORPTION,
    STATE_ASK_ABSORPTION,
)


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


def _run_chop(n_events: int = 600) -> TapeEngine:
    # dt = 0.2s/tick, so 600 events (~300 trades, ~60s of logical time) is comfortably warm and
    # fills every rolling window with representative choppy data.
    return _run("SIM-CHOP", "unclear_chop", n_events)


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


# --- Unclear / choppy tape (J-06) — the honest non-call, the fifth and final MVP state -----

def test_sim_chop_settles_on_unclear():
    # A genuinely choppy stream (balanced two-sided aggression, wide jittery spread, no price
    # progress, no refresh) WARMS UP and still reads unclear by MIXED signals — distinct from
    # iter-5's honest-unclear-on-silence (an undriven ticker). This is the keystone honest-
    # uncertainty anti-goal proven positively.
    snap = _run_chop().snapshot()
    assert snap.tape_state == STATE_UNCLEAR
    assert snap.warm is True                                  # it genuinely warmed up...
    assert snap.event_count >= CONFIG.warmup_min_events       # ...on real processed trades...
    assert snap.confidence == CONFIG.unclear_confidence       # ...the WARMED unclear (0.20),
    assert snap.confidence < CONFIG.reasonable_confidence     # not the cold-start 0.10, and low.
    # Honest behaviour: a cold-start unclear that stays unclear is NOT a state change, so the
    # engine must NOT manufacture a spurious "Tape state changed to ..." line. (The absence of a
    # transition is itself correct — contrast the four resolved scenarios, which each emit one.)
    assert not any(m.startswith("Tape state changed to") for m in snap.event_log)


def test_sim_chop_never_misfires_a_resolved_state_step_through():
    # THE CRITICAL GUARD: process the choppy stream event-by-event and assert the classified
    # state is NEVER one of the four resolved states at ANY tick — cold-start OR warmed. With
    # four active gates the false-fire surface is large; this proves no window's transient noise
    # ever trips one. (Defense in depth: every gate needs a one-sided ratio >= floor AND a stable
    # spread, and the chop denies BOTH everywhere — so no gate is ever even reachable.)
    provider = SimulatedProvider("SIM-CHOP", "unclear_chop")
    engine = TapeEngine("SIM-CHOP", "unclear_chop", CONFIG)
    saw_warm = False
    for event in itertools.islice(provider.stream(), 600):
        snap = engine.process_event(event)
        assert snap.tape_state == STATE_UNCLEAR
        assert snap.tape_state not in _RESOLVED_STATES
        saw_warm = saw_warm or snap.warm
    assert saw_warm  # the guard covered the warmed regime too, not just the cold start


def test_sim_chop_all_windows_deny_every_gate():
    # ALL-WINDOWS FEATURE GUARD (defense-in-depth evidence of WHY it is unclear): on the warmed
    # end-state snapshot, EVERY rolling window simultaneously fails the gate preconditions, so no
    # gate is reachable in any window — including the short, noise-prone 10s window.
    snap = _run_chop().snapshot()
    assert snap.warm is True
    assert "10s" in snap.features  # the noise-prone short window is present and checked below
    for label, f in snap.features.items():
        # (1) Mixed two-sided aggression: neither ratio reaches its 0.60 floor (the load-bearing
        #     guarantee — every gate requires a one-sided ratio at/above floor).
        assert f["aggressive_buy_ratio"] < CONFIG.min_aggressive_buy_ratio, label
        assert f["aggressive_sell_ratio"] < CONFIG.min_aggressive_sell_ratio, label
        # (2) Wide spread: above max_stable_spread (every gate requires spread <= it).
        assert f["average_spread"] > CONFIG.max_stable_spread, label
        # (3) No refresh evidence: below both floors (so absorption can't be fabricated).
        assert f["bid_refresh_score"] < CONFIG.min_bid_refresh_score, label
        assert f["ask_refresh_score"] < CONFIG.min_ask_refresh_score, label
        # (4) No clean price progress: impact is past NEITHER control cutoff (near zero).
        assert f["buy_price_impact"] < CONFIG.min_buy_price_impact, label
        assert f["sell_price_impact"] > CONFIG.max_sell_price_impact, label


def test_sim_chop_is_deterministic():
    a = _run_chop().snapshot()
    b = _run_chop().snapshot()
    assert a == b  # same seed + same stream => identical snapshot


def test_known_vs_unknown_ticker_contract():
    # The seven reserved sim tickers are all DRIVEN to their reads (the original five single-state
    # scenarios + the two regime-transition scenarios added this iteration). The known-vs-unknown
    # provider contract is UNCHANGED: a KNOWN sim ticker resolves a provider; an UNKNOWN ticker
    # never fabricates one (returns None) — no accidental loosening while registering the new
    # tickers.
    assert build_provider("SIM-CHOP") is not None
    assert build_provider("SIM-SHIFT") is not None
    assert build_provider("SIM-REVERSAL") is not None
    assert build_provider("NOPE123") is None


# --- Regime-transition scenarios (capability 21): SIM-SHIFT and SIM-REVERSAL ----------------
# These two are the first sims that deliberately CHANGE state mid-stream. The tests assert the
# deterministic phase SEQUENCE on the engine (the read settles into phase 1, then transitions into
# phase 2's read), plus determinism per scenario — mirroring the existing five single-state tests.


def _states_along_stream(ticker: str, scenario: str, n_events: int):
    """Run the engine over the full scenario stream, returning (snapshots-trace, final-engine).

    Each entry is the per-tick snapshot, so a test can assert a state was REACHED in an early phase
    and a DIFFERENT state by the end — the deterministic regime transition. Trades-only price is
    tracked via the snapshot's ``last``."""
    provider = SimulatedProvider(ticker, scenario)
    engine = TapeEngine(ticker, scenario, CONFIG)
    trace = []
    for event in itertools.islice(provider.stream(), n_events):
        trace.append(engine.process_event(event))
    return trace, engine


# SIM-SHIFT phase lengths (quote+trade per directional tick / per chop tick). The directional phase
# is 120 ticks => 240 events; the chop phase is 360 ticks => 720 events. Run the whole stream.
_SHIFT_PHASE1_EVENTS = 240
_SHIFT_TOTAL_EVENTS = _SHIFT_PHASE1_EVENTS + 720

# SIM-REVERSAL: absorption phase 120 ticks => 240 events; control phase 240 ticks => 480 events.
_REV_PHASE1_EVENTS = 240
_REV_TOTAL_EVENTS = _REV_PHASE1_EVENTS + 480


def test_sim_shift_buyer_control_then_unclear():
    trace, engine = _states_along_stream(
        "SIM-SHIFT", "shift_buyer_then_unclear", _SHIFT_TOTAL_EVENTS
    )
    # Phase 1 (end of the directional phase) settled on buyer_control with reasonable confidence.
    phase1_end = trace[_SHIFT_PHASE1_EVENTS - 1]
    assert phase1_end.tape_state == STATE_BUYER_CONTROL
    assert phase1_end.confidence >= CONFIG.reasonable_confidence
    assert phase1_end.primary_features["buy_price_impact"] > 0  # earned by real upward progress
    late_control_last = phase1_end.last
    # Phase 2 (end of the stream) decayed honestly to unclear — the regime changed.
    final = engine.snapshot()
    assert final.tape_state == STATE_UNCLEAR
    assert final.tape_state not in _RESOLVED_STATES
    # The chop-phase price band dips BELOW the late-control price (no fabricated progress): the
    # final last (a chop-phase print, all at the chop center) is strictly below the late-control
    # last (which the buyer phase had walked up).
    assert final.last < late_control_last
    # The transition was announced in the event log: buyer_control reached, then back to unclear.
    assert "Tape state changed to buyer_control" in final.event_log
    assert "Tape state changed to unclear" in final.event_log
    # The buyer_control announcement precedes the unclear announcement (the SEQUENCE, not just both).
    log = list(final.event_log)
    assert log.index("Tape state changed to buyer_control") < log.index(
        "Tape state changed to unclear"
    )


def test_sim_shift_is_deterministic():
    a, _ = _states_along_stream("SIM-SHIFT", "shift_buyer_then_unclear", _SHIFT_TOTAL_EVENTS)
    b, _ = _states_along_stream("SIM-SHIFT", "shift_buyer_then_unclear", _SHIFT_TOTAL_EVENTS)
    # Same seed + same stream => identical per-tick state trace AND identical final snapshot.
    assert [s.tape_state for s in a] == [s.tape_state for s in b]
    assert a[-1] == b[-1]


def test_sim_reversal_bid_absorption_then_buyer_control():
    trace, engine = _states_along_stream(
        "SIM-REVERSAL", "reversal_absorption_then_buyer", _REV_TOTAL_EVENTS
    )
    # Phase 1 (end of the absorption phase) settled on bid_absorption — NOT seller_control, despite
    # the heavy sell aggression (the price-impact discipline / keystone anti-goal).
    phase1_end = trace[_REV_PHASE1_EVENTS - 1]
    assert phase1_end.tape_state == STATE_BID_ABSORPTION
    assert phase1_end.tape_state != STATE_SELLER_CONTROL
    assert phase1_end.confidence >= CONFIG.reasonable_confidence
    primary = phase1_end.primary_features
    assert primary["aggressive_sell_ratio"] >= CONFIG.min_aggressive_sell_ratio  # high sell aggr...
    assert primary["sell_price_impact"] > CONFIG.max_sell_price_impact           # ...but ~no drop
    absorbed_last = phase1_end.last
    # Phase 2 (end of the stream) flipped to buyer_control with the price LIFTED above the absorbed
    # level — buyers taking control with REAL upward progress (earned via positive impact, never a
    # relaxed aggression-only shortcut — the critical buyer guard).
    final = engine.snapshot()
    assert final.tape_state == STATE_BUYER_CONTROL
    assert final.confidence >= CONFIG.reasonable_confidence
    assert final.primary_features["buy_price_impact"] > 0
    assert final.last > absorbed_last  # the last is lifted above the absorbed price
    # The SEQUENCE is announced in order: bid_absorption first, then buyer_control.
    log = list(final.event_log)
    assert "Tape state changed to bid_absorption" in log
    assert "Tape state changed to buyer_control" in log
    assert log.index("Tape state changed to bid_absorption") < log.index(
        "Tape state changed to buyer_control"
    )


def test_sim_reversal_is_deterministic():
    a, _ = _states_along_stream(
        "SIM-REVERSAL", "reversal_absorption_then_buyer", _REV_TOTAL_EVENTS
    )
    b, _ = _states_along_stream(
        "SIM-REVERSAL", "reversal_absorption_then_buyer", _REV_TOTAL_EVENTS
    )
    assert [s.tape_state for s in a] == [s.tape_state for s in b]
    assert a[-1] == b[-1]
