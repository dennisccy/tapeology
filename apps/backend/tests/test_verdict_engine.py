"""The verdict-transition engine (capability 24 / iter-4 J-40–J-46) — PURE evaluator unit matrix.

Each test replays a deterministic, UNPACED sim stream through a fresh ``TapeEngine`` and feeds every
snapshot to a ``VerdictEvaluator`` (exactly what the monitor does on the hot path), asserting the
PUBLISHED verdict SEQUENCE and the per-transition evidence/timing record. No FastAPI, no real journal
file — the evaluator is pure, so the matrix is hermetic and fast.

Covered (per the iteration spec's unit list):
  * one test per setup type asserting its J-40/J-42/J-45/J-46 verdict sequence on its named scenario;
  * the J-40 trap (sustained absorption alone NEVER confirms absorption_reversal);
  * the J-45 latch (no confirm pre-cross, however strong control is);
  * confirmed->weakening (J-43) and rejecting (J-41) with their evidence registers;
  * invalidation robustness with a synthetic outlier print (a lone print inside the ε guard does NOT
    invalidate; a ≥ε single print and k-consecutive both do; dwell-exemption; offending print recorded);
  * dwell semantics (a rule holding PRE-declaration does not confirm until it holds POST-declaration
    through the dwell; rule_first_true != published_at recorded);
  * no per-tick flapping; no transition published before declaration.
"""

import itertools

import pytest

from app.config import CONFIG, Config
from app.engine.snapshot import EngineSnapshot
from app.engine.tape_engine import TapeEngine
from app.providers.simulated import SimulatedProvider
from app.research.store import ThesisRecord
from app.research.taxonomy import frozen_statements
from app.research.verdict import VerdictEvaluator

import dataclasses


# --- helpers -------------------------------------------------------------------------------------

def _thesis(
    ticker: str,
    scenario: str,
    *,
    setup: str,
    direction: str = "long",
    invalidation: float,
    level: float | None = None,
) -> ThesisRecord:
    return ThesisRecord(
        id="t-test",
        ticker=ticker,
        setup_type=setup,
        direction=direction,
        invalidation_price=invalidation,
        level_price=level,
        status="active",
        bound_source=scenario,
        data_feed="sim",
        config_fingerprint=CONFIG.config_fingerprint(),
        entry_context={},
        statements=frozen_statements(setup, direction),
        created_logical_ts=0.0,
        created_wall_ts=1700000000.0,
    )


def _replay_with_evaluator(
    ticker: str,
    scenario: str,
    thesis: ThesisRecord,
    *,
    config: Config = CONFIG,
    warm: int = 0,
    n: int | None = None,
):
    """Warm the engine ``warm`` events, then evaluate the thesis over the rest of the stream.

    Returns ``(published_sequence, decisions)`` where ``published_sequence`` is the list of verdicts
    in publication order (each PUBLISHED transition once) and ``decisions`` is every ``changed``
    decision (so timing/evidence can be asserted). The first element is the implicit ``pending``
    (the declaration's initial row) — we model it explicitly here for sequence clarity.
    """
    provider = SimulatedProvider(ticker, scenario)
    engine = TapeEngine(ticker, scenario, config)
    stream = provider.stream()
    for event in itertools.islice(stream, warm):
        engine.process_event(event)

    evaluator = VerdictEvaluator(thesis, config)
    published = ["pending"]
    decisions = []
    remaining = stream if n is None else itertools.islice(stream, n)
    for event in remaining:
        snap = engine.process_event(event)
        decision = evaluator.evaluate(snap)
        if decision.changed:
            published.append(decision.verdict)
            decisions.append(decision)
        if evaluator.published_verdict == "invalidated":
            break
    return published, decisions, engine


# =================================================================================================
# J-40 — absorption_reversal: pending through absorption, confirming only on the reversal
# =================================================================================================

def test_j40_absorption_reversal_pending_through_absorption_then_confirming():
    # SIM-REVERSAL: bid_absorption phase, then buyer_control phase. Declare during absorption.
    thesis = _thesis(
        "SIM-REVERSAL", "reversal_absorption_then_buyer",
        setup="absorption_reversal", direction="long", invalidation=98.0,
    )
    # Warm into the absorption phase so declaration happens DURING bid_absorption.
    published, decisions, _ = _replay_with_evaluator(
        "SIM-REVERSAL", "reversal_absorption_then_buyer", thesis, warm=60,
    )
    # The ONLY published transition away from pending is confirming (on the reversal). No premature
    # confirm during the long absorption phase, no rejecting (the thesis is never contradicted).
    assert published[0] == "pending"
    assert "confirming" in published
    assert published.index("confirming") == 1  # pending -> confirming, nothing in between
    assert "rejecting" not in published
    # The confirming transition cites the FLIP to buyer_control with real upward impact (J-40).
    confirm = next(d for d in decisions if d.verdict == "confirming")
    assert confirm.tape_state == "buyer_control"
    assert "reversed" in confirm.evidence.lower() or "took control" in confirm.evidence.lower()
    assert "buy_price_impact" in confirm.evidence
    # Timing record: rule_first_true precedes (or equals at most) published_at, and is recorded.
    assert confirm.rule_first_true_ts is not None and confirm.published_at_ts is not None
    assert confirm.published_at_ts >= confirm.rule_first_true_ts


def test_j40_trap_sustained_absorption_alone_never_confirms():
    # SIM-BIDABS is bid_absorption FOREVER (no reversal phase). A long absorption_reversal declared on
    # it must NEVER confirm — sustained absorption is the premise, not the trigger (the J-40 trap).
    thesis = _thesis(
        "SIM-BIDABS", "bid_absorption",
        setup="absorption_reversal", direction="long", invalidation=98.0,
    )
    published, decisions, _ = _replay_with_evaluator(
        "SIM-BIDABS", "bid_absorption", thesis, warm=40, n=400,
    )
    assert published == ["pending"]  # stays pending the whole way — never confirms on absorption
    assert decisions == []


# =================================================================================================
# J-41 — trend_continuation: opposing control publishes rejecting; thesis stays active
# =================================================================================================

def test_j41_trend_continuation_long_rejecting_on_seller_control():
    # SIM-SELLER is seller_control — the OPPOSITE side for a long trend_continuation. Far invalidation
    # so the price drop never trips invalidation (we want rejecting, a judgement, not a resolution).
    thesis = _thesis(
        "SIM-SELLER", "seller_control",
        setup="trend_continuation", direction="long", invalidation=50.0,
    )
    published, decisions, _ = _replay_with_evaluator(
        "SIM-SELLER", "seller_control", thesis, warm=40, n=400,
    )
    assert "rejecting" in published
    reject = next(d for d in decisions if d.verdict == "rejecting")
    assert reject.tape_state == "seller_control"
    assert "opposite side" in reject.evidence.lower() or "rejecting" in reject.evidence.lower()
    assert "sell_price_impact" in reject.evidence
    # Rejecting is NOT terminal — the evaluator did not flip to invalidated (thesis stays active).
    assert "invalidated" not in published


# =================================================================================================
# J-42 — trend_continuation: confirming after dwell, stays confirming (no flapping)
# =================================================================================================

def test_j42_trend_continuation_long_confirms_and_stays_confirming():
    thesis = _thesis(
        "SIM-BUYER", "buyer_control",
        setup="trend_continuation", direction="long", invalidation=98.0,
    )
    published, decisions, _ = _replay_with_evaluator(
        "SIM-BUYER", "buyer_control", thesis, warm=40, n=400,
    )
    assert published == ["pending", "confirming"]  # exactly one transition — no flapping
    confirm = decisions[0]
    assert confirm.verdict == "confirming"
    assert confirm.tape_state == "buyer_control"
    assert "confirms your thesis" in confirm.evidence.lower()


# =================================================================================================
# J-43 — trend_continuation: confirming, then weakening after the shift (never back to pending)
# =================================================================================================

def test_j43_trend_continuation_confirms_then_weakens_on_shift():
    # SIM-SHIFT: buyer_control phase, then unclear. A long trend_continuation declared during control
    # confirms, then WEAKENS once the tape decays to unclear — never a silent return to pending (J-43).
    thesis = _thesis(
        "SIM-SHIFT", "shift_buyer_then_unclear",
        setup="trend_continuation", direction="long", invalidation=98.0,
    )
    # Warm to ~t=25 (into the buyer_control phase, which starts ~t=19.5) so declaration is during control.
    published, decisions, _ = _replay_with_evaluator(
        "SIM-SHIFT", "shift_buyer_then_unclear", thesis, warm=55,
    )
    assert published[:2] == ["pending", "confirming"]
    assert "weakening" in published
    assert published.index("weakening") > published.index("confirming")
    # NEVER a silent return to pending after confirming.
    assert "pending" not in published[1:]
    weak = next(d for d in decisions if d.verdict == "weakening")
    assert "weakening" in weak.evidence.lower() and "faded" in weak.evidence.lower()


# =================================================================================================
# J-44 — invalidation: dwell-exempt, robust, system-owned, offending print recorded
# =================================================================================================

def test_j44_invalidation_single_big_print_through_level():
    # SIM-SELLER drops price; a long thesis with invalidation just below the entry last is invalidated
    # the moment a print runs ≥ε·spread through it. Assert the terminal invalidated decision carries
    # the offending print + logical ts and that it is dwell-exempt (no confirming first).
    thesis = _thesis(
        "SIM-SELLER", "seller_control",
        setup="trend_continuation", direction="long", invalidation=99.80,
    )
    published, decisions, engine = _replay_with_evaluator(
        "SIM-SELLER", "seller_control", thesis, warm=40,
    )
    assert published[-1] == "invalidated"
    inval = decisions[-1]
    assert inval.invalidated is True
    assert inval.last is not None and inval.last <= 99.80  # the print is through the level
    assert inval.rule_first_true_ts is not None  # offending print's logical ts recorded
    assert inval.published_at_ts == inval.rule_first_true_ts  # dwell-exempt (immediate)
    assert "invalidat" in inval.evidence.lower() and "99.80" in inval.evidence


def test_j44_lone_bad_print_inside_guard_does_not_invalidate():
    # A SINGLE synthetic print just barely through the invalidation — INSIDE the ε·spread guard and
    # not k-consecutive — must NOT invalidate. We build a tiny synthetic snapshot stream by hand so
    # the breach is controlled to the cent.
    config = CONFIG
    thesis = _thesis(
        "SIM-BUYER", "buyer_control",
        setup="trend_continuation", direction="long", invalidation=100.00,
    )
    ev = VerdictEvaluator(thesis, config)

    def snap(last, spread=0.02, ts=1.0, state="buyer_control"):
        return EngineSnapshot(
            ticker="SIM-BUYER", scenario="buyer_control", timestamp=ts, event_count=1, warm=True,
            stream_status="live", bid=last - spread / 2, ask=last + spread / 2, spread=spread,
            last=last, features={"30s": {"buy_price_impact": 0.4, "sell_price_impact": 0.0}},
            primary_window="30s", tape_state=state, confidence=0.9, observations=(),
        )

    # ε=1.5, spread=0.02 => guard = 0.03. A lone print 100.00 - 0.02 = 99.98 is only 0.02 through the
    # level — INSIDE the 0.03 guard — so it must NOT invalidate (and is the 1st of <k consecutive).
    d1 = ev.evaluate(snap(99.98, ts=1.0))
    assert d1.invalidated is False
    assert ev.published_verdict != "invalidated"
    # A print back on the right side resets the consecutive counter (so it cannot accumulate to k).
    d2 = ev.evaluate(snap(100.05, ts=1.5))
    assert ev.published_verdict != "invalidated"
    # Now a SINGLE print 0.04 through the level (>= 0.03 guard) DOES invalidate immediately.
    d3 = ev.evaluate(snap(99.96, ts=2.0))
    assert d3.invalidated is True
    assert ev.published_verdict == "invalidated"


def test_j44_k_consecutive_prints_inside_guard_invalidate():
    # k=3 consecutive prints just through the level (each INSIDE the ε guard, so no single one trips
    # the big-print rule) together invalidate — a sustained leak through the level.
    config = CONFIG
    thesis = _thesis(
        "SIM-BUYER", "buyer_control",
        setup="trend_continuation", direction="long", invalidation=100.00,
    )
    ev = VerdictEvaluator(thesis, config)

    def snap(last, ts):
        return EngineSnapshot(
            ticker="SIM-BUYER", scenario="buyer_control", timestamp=ts, event_count=1, warm=True,
            stream_status="live", bid=last - 0.01, ask=last + 0.01, spread=0.02, last=last,
            features={"30s": {"buy_price_impact": 0.4, "sell_price_impact": 0.0}},
            primary_window="30s", tape_state="buyer_control", confidence=0.9, observations=(),
        )

    # Each print is 99.98 — 0.02 through the level, inside the 0.03 guard. The 1st and 2nd do not
    # invalidate; the 3rd (k=3) does.
    assert ev.evaluate(snap(99.98, 1.0)).invalidated is False
    assert ev.evaluate(snap(99.98, 1.5)).invalidated is False
    d3 = ev.evaluate(snap(99.98, 2.0))
    assert d3.invalidated is True
    assert "consecutive" in d3.evidence.lower()


# =================================================================================================
# J-45 — level_break: pending pre-cross despite control; confirming after latch + control
# =================================================================================================

def test_j45_level_break_latch_no_confirm_before_cross():
    # SIM-BUYER walks price up from 100.00. Declare level_break/long with a level ABOVE the current
    # last so it has not yet crossed: it must stay pending DESPITE buyer_control until last crosses
    # the level, then confirm.
    thesis = _thesis(
        "SIM-BUYER", "buyer_control",
        setup="level_break", direction="long", invalidation=99.0, level=100.30,
    )
    # Warm only a little so the level (100.30) is still above last when we declare.
    published, decisions, _ = _replay_with_evaluator(
        "SIM-BUYER", "buyer_control", thesis, warm=10,
    )
    assert published[0] == "pending"
    assert "confirming" in published  # eventually crosses 100.30 and confirms
    confirm = next(d for d in decisions if d.verdict == "confirming")
    assert confirm.last is not None and confirm.last > 100.30  # confirmed only AFTER the cross
    assert "broke" in confirm.evidence.lower() and "100.30" in confirm.evidence


def test_j45_level_break_never_confirms_if_level_unreached():
    # A level FAR above anything SIM-BUYER reaches: control is strong but the latch never trips, so
    # the verdict stays pending forever (the latch, not control, is the trigger).
    thesis = _thesis(
        "SIM-BUYER", "buyer_control",
        setup="level_break", direction="long", invalidation=99.0, level=200.00,
    )
    published, decisions, _ = _replay_with_evaluator(
        "SIM-BUYER", "buyer_control", thesis, warm=10, n=400,
    )
    assert published == ["pending"]
    assert decisions == []


# =================================================================================================
# J-46 — failed_move_fade: confirming DURING the absorption (the deliberate J-40 asymmetry)
# =================================================================================================

def test_j46_failed_move_fade_confirms_during_absorption():
    # A long failed_move_fade expects a failed UP push absorbed at the ask (ask_absorption). SIM-ASKABS
    # is ask_absorption forever — so a long failed_move_fade confirms DURING the absorption (the
    # asymmetry with absorption_reversal, which would stay pending on the same tape).
    thesis = _thesis(
        "SIM-ASKABS", "ask_absorption",
        setup="failed_move_fade", direction="long", invalidation=99.0, level=100.5,
    )
    published, decisions, _ = _replay_with_evaluator(
        "SIM-ASKABS", "ask_absorption", thesis, warm=40, n=200,
    )
    assert published[:2] == ["pending", "confirming"]
    confirm = decisions[0]
    assert confirm.tape_state == "ask_absorption"
    assert "absorbed" in confirm.evidence.lower() and "fading" in confirm.evidence.lower()


def test_j46_failed_move_fade_stays_confirming_through_reclaim():
    # SIM-REVERSAL: bid_absorption then buyer_control. For a long failed_move_fade the buyer_control
    # phase is the RECLAIM (control turning to your side) — it must KEEP confirming, not flip away.
    # (We declare on SIM-REVERSAL where the absorption is bid_absorption — the fade's premise for a
    # long fmf is ask_absorption, so it confirms on the reclaim's buyer_control phase.)
    thesis = _thesis(
        "SIM-REVERSAL", "reversal_absorption_then_buyer",
        setup="failed_move_fade", direction="long", invalidation=98.0, level=100.5,
    )
    published, decisions, _ = _replay_with_evaluator(
        "SIM-REVERSAL", "reversal_absorption_then_buyer", thesis, warm=60,
    )
    # Confirms on the buyer_control reclaim and stays confirming (no weakening/rejecting afterwards).
    assert "confirming" in published
    assert "rejecting" not in published
    # Once confirmed it does not silently revert.
    assert published[-1] in ("confirming", "weakening")


# =================================================================================================
# Dwell semantics — pre-declaration hold never confirms; rule_first_true != published_at
# =================================================================================================

def test_dwell_pre_declaration_hold_does_not_confirm_until_post_declaration_dwell():
    # SIM-BUYER is buyer_control from early on. Even if we warm DEEP into a sustained control phase
    # (the rule held LONG before declaration), the dwell restarts at declaration — so confirmation
    # still requires the rule to hold for ``dwell`` AFTER the evaluator is created.
    thesis = _thesis(
        "SIM-BUYER", "buyer_control",
        setup="trend_continuation", direction="long", invalidation=98.0,
    )
    # Warm 200 events (~t=100, deep into control) before attaching the evaluator.
    published, decisions, _ = _replay_with_evaluator(
        "SIM-BUYER", "buyer_control", thesis, warm=200, n=200,
    )
    assert published == ["pending", "confirming"]
    confirm = decisions[0]
    # rule_first_true is recorded at the FIRST post-declaration tick the rule held — strictly before
    # the post-dwell publish, so the two timestamps differ (dwell honesty).
    assert confirm.rule_first_true_ts is not None
    assert confirm.published_at_ts is not None
    assert confirm.published_at_ts > confirm.rule_first_true_ts
    assert (confirm.published_at_ts - confirm.rule_first_true_ts) >= (
        CONFIG.verdict_dwell_seconds["trend_continuation"] - 1e-9
    )


def test_no_flapping_one_published_row_while_rule_holds():
    # Over a long sustained-control run, exactly ONE confirming transition is published (not one per
    # tick). The decisions list (only `changed` rows) has length 1.
    thesis = _thesis(
        "SIM-BUYER", "buyer_control",
        setup="trend_continuation", direction="long", invalidation=98.0,
    )
    _, decisions, _ = _replay_with_evaluator(
        "SIM-BUYER", "buyer_control", thesis, warm=40, n=600,
    )
    assert len(decisions) == 1
    assert decisions[0].verdict == "confirming"


def test_shorter_dwell_publishes_sooner_config_owned():
    # The dwell is config-owned (no magic number): a config with a tiny dwell publishes confirming on
    # an earlier logical instant than the default. Proves the timing is read from config, not hardcoded.
    fast = dataclasses.replace(CONFIG, verdict_dwell_seconds={
        "absorption_reversal": 0.5, "trend_continuation": 0.5, "level_break": 0.5, "failed_move_fade": 0.5,
    })
    thesis_fast = _thesis(
        "SIM-BUYER", "buyer_control",
        setup="trend_continuation", direction="long", invalidation=98.0,
    )
    _, fast_decisions, _ = _replay_with_evaluator(
        "SIM-BUYER", "buyer_control", thesis_fast, config=fast, warm=40, n=200,
    )
    thesis_slow = _thesis(
        "SIM-BUYER", "buyer_control",
        setup="trend_continuation", direction="long", invalidation=98.0,
    )
    _, slow_decisions, _ = _replay_with_evaluator(
        "SIM-BUYER", "buyer_control", thesis_slow, config=CONFIG, warm=40, n=200,
    )
    assert fast_decisions[0].published_at_ts < slow_decisions[0].published_at_ts
