"""Entry risk flags (capability 26, J-49) — the frozen, advisory, computed-once flag set.

These tests pin the SINGLE ``compute_risk_flags`` function against deterministic sim snapshots,
asserting EXACT measured-evidence values (never just "a flag fired"). Each of the six flags has a
positive case (with its exact measured payload) AND a negative case (just inside the gate => no
flag). The setup-aware ``against_expected_tape`` matrix is unit-pinned (no browser leg). Frozen-ness,
advisory-never-blocking, and the honest ABSENT-vs-EMPTY omission are pinned here too.

Discipline mirrored from the engine: the research layer is read-only — these snapshots come straight
from the engine; ``compute_risk_flags`` only READS them. No new indicator is introduced; every flag
reuses canonical engine values + the classifier's own gates (only the two new research thresholds —
chase return / invalidation-too-tight spread multiple — are new, and they are config-owned).
"""

import itertools

import pytest

from app.config import CONFIG
from app.engine.snapshot import EngineSnapshot
from app.engine.tape_engine import TapeEngine
from app.providers.simulated import SimulatedProvider
from app.research.monitor import compute_risk_flags
from app.research.taxonomy import RISK_FLAGS, frozen_statements


def _warm_snapshot(ticker: str, scenario: str, n: int) -> EngineSnapshot:
    provider = SimulatedProvider(ticker, scenario)
    engine = TapeEngine(ticker, scenario, CONFIG)
    for event in itertools.islice(provider.stream(), n):
        engine.process_event(event)
    return engine.snapshot()


def _snapshot_at_count(ticker: str, scenario: str, count: int) -> EngineSnapshot:
    """Advance the engine until exactly ``event_count >= count`` and return that snapshot."""
    provider = SimulatedProvider(ticker, scenario)
    engine = TapeEngine(ticker, scenario, CONFIG)
    stream = provider.stream()
    while True:
        engine.process_event(next(stream))
        snap = engine.snapshot()
        if snap.event_count >= count:
            return snap


def _flags(snap, *, setup_type, direction, invalidation_price):
    return compute_risk_flags(
        snap,
        setup_type=setup_type,
        direction=direction,
        invalidation_price=invalidation_price,
        statements=frozen_statements(setup_type, direction),
        config=CONFIG,
    )


def _by_name(flags, name):
    matches = [f for f in flags if f["flag"] == name]
    return matches[0] if matches else None


# --- the taxonomy owns every flag label (no hardcoded copy anywhere else) -------------------------

def test_every_emitted_flag_carries_taxonomy_label_and_evidence():
    snap = _warm_snapshot("SIM-BUYER", "buyer_control", 240)
    flags = _flags(snap, setup_type="trend_continuation", direction="long", invalidation_price=99.0)
    assert flags, "SIM-BUYER warm long should fire at least chasing_entry"
    for f in flags:
        assert f["flag"] in RISK_FLAGS
        assert f["label"] == RISK_FLAGS[f["flag"]]  # taxonomy-owned, verbatim
        assert isinstance(f["evidence"], str) and f["evidence"]  # no naked flag — always evidence
        assert isinstance(f["measured"], dict) and f["measured"]  # measured values frozen for review


# --- before_warmup --------------------------------------------------------------------------------

def test_before_warmup_fires_with_exact_trade_count_evidence():
    snap = _snapshot_at_count("SIM-BUYER", "buyer_control", 4)  # well under the 40-event floor
    assert snap.event_count < CONFIG.warmup_min_events
    flags = _flags(snap, setup_type="trend_continuation", direction="long", invalidation_price=99.0)
    f = _by_name(flags, "before_warmup")
    assert f is not None
    assert f["measured"] == {
        "trade_count": snap.event_count,
        "warmup_min_events": CONFIG.warmup_min_events,
    }
    assert str(snap.event_count) in f["evidence"]
    assert str(CONFIG.warmup_min_events) in f["evidence"]


def test_before_warmup_does_not_fire_once_warm():
    snap = _snapshot_at_count("SIM-BUYER", "buyer_control", CONFIG.warmup_min_events)
    assert snap.event_count >= CONFIG.warmup_min_events
    flags = _flags(snap, setup_type="trend_continuation", direction="long", invalidation_price=99.0)
    assert _by_name(flags, "before_warmup") is None


# --- invalidation_too_tight -----------------------------------------------------------------------

def test_invalidation_too_tight_fires_inside_the_spread_multiple_band():
    snap = _warm_snapshot("SIM-BUYER", "buyer_control", 240)
    last = snap.last
    spread = snap.spread
    band = spread * CONFIG.invalidation_too_tight_spread_multiple
    # An invalidation HALF a spread below the last is comfortably inside the band (distance < band).
    invalidation = round(last - spread * 0.5, 4)
    flags = _flags(snap, setup_type="trend_continuation", direction="long",
                   invalidation_price=invalidation)
    f = _by_name(flags, "invalidation_too_tight")
    assert f is not None
    assert f["measured"]["distance"] == pytest.approx(abs(last - invalidation))
    assert f["measured"]["spread"] == pytest.approx(spread)
    assert f["measured"]["spread_multiple"] == CONFIG.invalidation_too_tight_spread_multiple
    assert f["measured"]["band"] == pytest.approx(band)
    assert f["measured"]["distance"] < f["measured"]["band"]


def test_invalidation_too_tight_does_not_fire_for_a_normal_distance():
    snap = _warm_snapshot("SIM-BUYER", "buyer_control", 240)
    last = snap.last
    # A normal invalidation ~$1 below the last is ~50x the spread away — comfortably outside the band.
    flags = _flags(snap, setup_type="trend_continuation", direction="long",
                   invalidation_price=round(last - 1.0, 2))
    assert _by_name(flags, "invalidation_too_tight") is None


# --- chasing_entry --------------------------------------------------------------------------------

def test_chasing_entry_fires_on_an_extended_long_move_with_exact_return_evidence():
    snap = _warm_snapshot("SIM-BUYER", "buyer_control", 240)
    ref = snap.primary_features["reference_price"]
    buy_return = snap.primary_features["buy_price_impact"] / ref
    assert buy_return > CONFIG.chase_return_threshold  # an extended move (precondition)
    flags = _flags(snap, setup_type="trend_continuation", direction="long",
                   invalidation_price=round(snap.last - 1.0, 2))
    f = _by_name(flags, "chasing_entry")
    assert f is not None
    assert f["measured"]["impact_return"] == pytest.approx(buy_return)
    assert f["measured"]["threshold"] == CONFIG.chase_return_threshold
    assert f["measured"]["side"] == "buy"
    # The plain-language margin cites the measured return vs the threshold (descriptive, present-tense).
    assert "chase threshold" in f["evidence"]


def test_chasing_entry_does_not_fire_at_warmup_when_the_move_has_not_extended():
    # Right at the warm-up boundary SIM-BUYER's favorable return is ~0.0033, BELOW the 0.0040 chase
    # threshold — a clean (no-chase) declare. This is the spec's no-flags frame boundary.
    snap = _snapshot_at_count("SIM-BUYER", "buyer_control", CONFIG.warmup_min_events)
    ref = snap.primary_features["reference_price"]
    buy_return = snap.primary_features["buy_price_impact"] / ref
    assert buy_return <= CONFIG.chase_return_threshold
    flags = _flags(snap, setup_type="trend_continuation", direction="long",
                   invalidation_price=round(snap.last - 1.0, 2))
    assert _by_name(flags, "chasing_entry") is None


def test_chasing_entry_is_direction_aware_short_reads_sell_impact():
    # A SHORT declared on a BUYER-control tape is NOT chasing (price moved AGAINST a short — the
    # favorable downside has not run). The favorable side for a short is selling; SIM-BUYER's sell
    # impact return is small, so no chase fires.
    snap = _warm_snapshot("SIM-BUYER", "buyer_control", 240)
    flags = _flags(snap, setup_type="trend_continuation", direction="short",
                   invalidation_price=round(snap.last + 1.0, 2))
    assert _by_name(flags, "chasing_entry") is None


# --- wide_spread_illiquid / low_trade_speed (classifier gates VERBATIM) ---------------------------

def test_low_trade_speed_fires_early_with_exact_speed_evidence():
    snap = _snapshot_at_count("SIM-CHOP", "unclear_chop", 4)  # very early — tape still slow
    speed = snap.primary_features["trade_speed"]
    assert speed < CONFIG.min_trade_speed
    flags = _flags(snap, setup_type="trend_continuation", direction="long", invalidation_price=99.0)
    f = _by_name(flags, "low_trade_speed")
    assert f is not None
    assert f["measured"]["trade_speed"] == pytest.approx(speed)
    assert f["measured"]["min_trade_speed"] == CONFIG.min_trade_speed


def test_low_trade_speed_does_not_fire_once_the_tape_is_fast():
    snap = _warm_snapshot("SIM-CHOP", "unclear_chop", 240)  # warm chop runs fast (speed >> floor)
    assert snap.primary_features["trade_speed"] >= CONFIG.min_trade_speed
    flags = _flags(snap, setup_type="trend_continuation", direction="long", invalidation_price=99.0)
    assert _by_name(flags, "low_trade_speed") is None


def test_wide_spread_illiquid_uses_the_classifier_relative_gate_verbatim():
    # SIM-CHOP's warm spread (~14 bps) is UNDER the classifier's 30-bps stable cap — so the gate read
    # VERBATIM does NOT fire (the spread is genuinely not wide relative to a ~$100 instrument). This
    # pins the no-new-threshold contract: the flag uses max_stable_spread_bps as-is.
    snap = _warm_snapshot("SIM-CHOP", "unclear_chop", 240)
    ref = snap.primary_features["reference_price"]
    spread_bps = snap.spread / ref * 10000.0
    assert spread_bps <= CONFIG.max_stable_spread_bps
    flags = _flags(snap, setup_type="trend_continuation", direction="long", invalidation_price=99.0)
    assert _by_name(flags, "wide_spread_illiquid") is None


def test_wide_spread_illiquid_fires_when_the_relative_spread_exceeds_the_cap():
    # A synthetic snapshot whose relative spread clears the classifier cap (a genuinely wide spread)
    # fires the flag with the exact bps margin — proving the gate, not just the SIM-CHOP non-firing.
    snap = _warm_snapshot("SIM-BUYER", "buyer_control", 240)
    ref = snap.primary_features["reference_price"]
    wide_spread = ref * (CONFIG.max_stable_spread_bps + 20.0) / 10000.0  # 20 bps over the cap
    wide = snap.__class__(
        **{**{f.name: getattr(snap, f.name) for f in snap.__dataclass_fields__.values()},
           "spread": wide_spread}
    )
    flags = _flags(wide, setup_type="trend_continuation", direction="long",
                   invalidation_price=round(snap.last - 1.0, 2))
    f = _by_name(flags, "wide_spread_illiquid")
    assert f is not None
    assert f["measured"]["unit"] == "bps"
    assert f["measured"]["max_spread"] == CONFIG.max_stable_spread_bps
    assert f["measured"]["spread_metric"] == pytest.approx(wide_spread / ref * 10000.0)
    assert f["measured"]["spread_metric"] > CONFIG.max_stable_spread_bps


# --- against_expected_tape (setup-aware matrix; unit-pinned, no browser leg) -----------------------

def test_against_expected_tape_fires_for_long_absorption_reversal_during_seller_control():
    snap = _warm_snapshot("SIM-SELLER", "seller_control", 240)
    assert snap.tape_state == "seller_control"
    flags = _flags(snap, setup_type="absorption_reversal", direction="long",
                   invalidation_price=round(snap.last - 1.0, 2))
    f = _by_name(flags, "against_expected_tape")
    assert f is not None
    assert f["measured"]["tape_state"] == "seller_control"
    # The expected premise states for a long absorption_reversal are bid_absorption (then buyer_control).
    assert "bid_absorption" in f["measured"]["expected_states"]


def test_against_expected_tape_does_not_fire_during_the_expected_premise_tape():
    # The defining capability-26 distinction: a long absorption_reversal declared DURING bid_absorption
    # is NOT flagged (the tape is exactly the premise the setup expects).
    snap = _warm_snapshot("SIM-BIDABS", "bid_absorption", 240)
    assert snap.tape_state == "bid_absorption"
    flags = _flags(snap, setup_type="absorption_reversal", direction="long",
                   invalidation_price=round(snap.last - 1.0, 2))
    assert _by_name(flags, "against_expected_tape") is None


def test_against_expected_tape_never_fires_on_unclear():
    # Honest-uncertainty is NOT a contradiction: an unclear tape never fires against_expected_tape (no
    # definite read to contradict the setup).
    snap = _warm_snapshot("SIM-CHOP", "unclear_chop", 240)
    assert snap.tape_state == "unclear"
    flags = _flags(snap, setup_type="trend_continuation", direction="long", invalidation_price=99.0)
    assert _by_name(flags, "against_expected_tape") is None


# --- frozen-ness: the flag set is a record of the entry moment, never a live indicator -------------

def test_flags_are_computed_once_and_independent_of_later_tape():
    # The flags computed at an EARLY (extended) declaration do not change as the tape moves on — they
    # are frozen at the entry moment. compute_risk_flags is a pure function of the handed snapshot;
    # the persisted-then-reread frozen-ness is covered by the API/store tests. Here: two DIFFERENT
    # later snapshots do not retroactively alter the EARLIER flag set.
    early = _warm_snapshot("SIM-BUYER", "buyer_control", 240)
    later = _warm_snapshot("SIM-BUYER", "buyer_control", 360)
    early_flags = _flags(early, setup_type="trend_continuation", direction="long",
                         invalidation_price=round(early.last - 1.0, 2))
    # Recomputing against the EARLY snapshot again is byte-identical (deterministic, no state).
    again = _flags(early, setup_type="trend_continuation", direction="long",
                   invalidation_price=round(early.last - 1.0, 2))
    assert early_flags == again
    # A later snapshot is its own (possibly different) computation — it never mutates the early set.
    _ = _flags(later, setup_type="trend_continuation", direction="long",
               invalidation_price=round(later.last - 1.0, 2))
    assert _flags(early, setup_type="trend_continuation", direction="long",
                  invalidation_price=round(early.last - 1.0, 2)) == early_flags


# --- advisory, never blocking; an EMPTY list is a valid (assessed-nothing-fired) result -----------

def test_clean_declare_returns_empty_list_not_none():
    # A clean at-warm-up SIM-BUYER declare fires NO flags — the result is an EMPTY list (assessed,
    # nothing fired), NEVER None (None means "never assessed" — a pre-v4 thesis only).
    snap = _snapshot_at_count("SIM-BUYER", "buyer_control", CONFIG.warmup_min_events)
    flags = _flags(snap, setup_type="trend_continuation", direction="long",
                   invalidation_price=round(snap.last - 1.0, 2))
    assert flags == []


def test_maximally_flagged_declare_still_returns_a_list_never_raises():
    # An early SIM-CHOP declare with a too-tight, wrong-side-of-expected stack of risks computes a
    # NON-empty list and NEVER raises — advisory, never blocking (creation succeeds regardless).
    snap = _snapshot_at_count("SIM-CHOP", "unclear_chop", 4)
    flags = _flags(snap, setup_type="trend_continuation", direction="long",
                   invalidation_price=round((snap.last or 100.0) - 0.01, 2))
    names = {f["flag"] for f in flags}
    # At minimum before_warmup + low_trade_speed fire early on chop.
    assert {"before_warmup", "low_trade_speed"} <= names
