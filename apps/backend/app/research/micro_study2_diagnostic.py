"""``micro_study2_diagnostic.py`` -- Study 2's CONTINUOUS exposed-corpus diagnostic (r14.2, §8),
with its DECISION delegated to the frozen Scout screen (r14.3).

**What this is for.** Before anyone spends storage, retention risk and months of recording on an
out-of-sample campaign for divergence-at-level, one cheap question has to be answered on evidence
that is already spent: *does the exposed legacy tick corpus even produce enough paired-touch
anchors to estimate anything?* This module builds the report that answers it.

**What it may read, and what it may never read.** Study 2 discovery runs on
``historical_exposed_diagnostic`` evidence only -- the legacy tick symbol-days that ``r2``
initialization already marks exposed for their entire span. Nothing here releases a withheld
starter member, touches a sealed shard, reads ``historical_oos`` data, consults a Vault outcome, or
registers a direction.

**Why the result can never graduate.** Every anchor summarized here comes from a window that was
exposed long before any rule could have been frozen against it, so by the mechanical rule in
``walkforward.classify_evidence_class`` it is diagnostic evidence, permanently. That is a fact about
the DATA, not a policy this module applies -- which is exactly why it is safe to look. A promising
number justifies freezing a Mode B hypothesis and *then* recording; it is never itself a survivor, a
graduation, or a claim about live edge.

**r14.3 -- THE DECISION IS SCOUT'S, NOT THIS MODULE'S.** The first version of this module carried
its own decision rail, and it was a bad one in two independent ways:

1. *A borrowed sample floor.* ``MIN_ANCHORS_FOR_AN_ESTIMATE = 30`` was lifted from
   ``walkforward.WF_FOLD_MIN_OBSERVATIONS`` -- a WALK-FORWARD fold floor -- and applied to ALL
   usable anchors, while the decision itself was allowed through on ``fired.n_sessions > 0``. A
   corpus with 30 usable anchors of which exactly ONE fired, in ONE session, could reach
   ``PROMISING_FOR_MODE_B_FREEZE`` on that single observation. Scout already owns a sufficiency
   rule for exactly this question (``SCOUT_MIN_OBSERVATIONS_PER_CELL`` per cell,
   ``SCOUT_MIN_SESSION_CLUSTERS`` usable clusters); a second, weaker one is worse than none.
2. *The wrong statistic.* The verdict read the mechanism-fired cell's OWN raw forward mean. The
   project's frozen discovery statistic is candidate-versus-comparator: the mean of per-session
   (candidate mean − comparator mean) deltas, against a block-permutation null. Judging the fired
   cell alone cannot tell a mechanism-specific effect from market-wide drift. Concretely: a fired
   cell returning −2 bps while the comparator returns −8 bps looks bearish and is in fact **+6 bps
   worse** than doing nothing in particular. The old rail promoted that.

So this module no longer decides anything. It computes the CONTINUOUS representation -- which is
descriptive by construction -- and then reads its outcome off a ``scout.screen_candidate`` result
computed over the SAME anchor list. There is no second sample floor, no second p-value, no second
null, no second concentration rule, no second fragility rule and no second economic gate here.

**The one thing this module still decides, and why it is not a second gate.** Card 9.1 is an
explicitly BEARISH mechanism, and the Study 2 pilot candidate is registered ``sidedness=None`` (an
exploratory question, not a claim), so Scout's own ``killed_direction`` gate -- which only fires for
a SIDED candidate -- never runs. Its ``effect_bps`` is therefore in raw market-return space. Reading
a surviving positive effect as "the bearish mechanism is contradicted" is not an extra statistical
hurdle; it is the mechanism's own pre-stated semantics applied to a result Scout already accepted.
Turning that positive effect into a LONG hypothesis instead would be reversing the stated mechanism
after seeing discovery data, and is refused by construction: this module can only ever propose
``short``.
"""

from __future__ import annotations

import statistics

from . import micro_features as mf

__all__ = [
    "EVIDENCE_CLASS",
    "GRADUATION_CREDIT",
    "OUTCOME_INSUFFICIENT",
    "OUTCOME_KILLED",
    "OUTCOME_PROMISING",
    "PROPOSED_DIRECTION",
    "SCOUT_DECISION_INSUFFICIENT",
    "continuous_distribution",
    "quadrant_counts",
    "conditional_raw_return",
    "continuous_report",
    "study2_outcome_from_scout",
    "study2_diagnostic",
]

#: Every row this module produces is diagnostic, by construction -- see the module docstring.
EVIDENCE_CLASS = "historical_exposed_diagnostic"
GRADUATION_CREDIT = "none -- exposed-corpus discovery can never graduate a candidate"

#: The three honest answers this diagnostic can return. Named constants because the operator brief
#: asks for exactly one of them, and a free-text verdict is how a "maybe" survives review.
OUTCOME_INSUFFICIENT = "INSUFFICIENT"
OUTCOME_KILLED = "KILLED"
OUTCOME_PROMISING = "PROMISING_FOR_MODE_B_FREEZE"

#: The ONLY direction this module can ever propose. Card 9.1 is bearish; a surviving POSITIVE effect
#: contradicts it and is killed, never re-read as a long hypothesis (module docstring).
PROPOSED_DIRECTION = "short"

#: Scout's own vocabulary for "the sample could not support a screen at all" -- the one kill that
#: means *we could not look*, as opposed to *we looked and it failed*. Transcribed here rather than
#: imported so this module keeps its "no scout import" shape; the mapping test pins the two equal.
SCOUT_DECISION_INSUFFICIENT = "killed_insufficient_n"
_SCOUT_DECISION_SURVIVE = "survive"


def continuous_distribution(values: list[float | None]) -> dict:
    """Distribution summary of one continuous coordinate over the anchors where it is DEFINED.

    ``None`` values are counted and excluded, never imputed: an undefined coordinate means the
    mechanism could not be measured on that pair (a thin baseline, a zero-median volume), and
    substituting a zero would silently move mass onto the axis origin the boolean tests against."""
    defined = [v for v in values if v is not None]
    n_undefined = len(values) - len(defined)
    if not defined:
        return {
            "n": 0, "n_undefined": n_undefined, "min": None, "p10": None, "median": None,
            "p90": None, "max": None, "mean": None,
        }
    ordered = sorted(defined)

    def _q(q: float) -> float:
        if len(ordered) == 1:
            return ordered[0]
        pos = q * (len(ordered) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(ordered) - 1)
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)

    return {
        "n": len(defined),
        "n_undefined": n_undefined,
        "min": ordered[0],
        "p10": _q(0.10),
        "median": statistics.median(ordered),
        "p90": _q(0.90),
        "max": ordered[-1],
        "mean": statistics.mean(ordered),
    }


def quadrant_counts(anchors: list[dict]) -> dict:
    """The four corners of the mechanism plane, split at the two PREDECLARED axis origins.

    The split points are 0 for ``price_extension_bps`` and 1 for ``delta_weakening_multiple``,
    because those are precisely Card 9.1's own two conjuncts -- not tuned cut-points and not a grid.
    ``both`` is therefore identical to ``bearish_divergence`` on every anchor where both
    coordinates are defined, which is what makes the boolean a transform of this plane rather than
    a second, independent measurement.

    Anchors missing either coordinate are counted in ``undefined`` and enter no quadrant."""
    counts = {"both": 0, "extension_only": 0, "weakening_only": 0, "neither": 0, "undefined": 0}
    for a in anchors:
        ext = a.get("price_extension_bps")
        mult = a.get("delta_weakening_multiple")
        if ext is None or mult is None:
            counts["undefined"] += 1
            continue
        extended = ext > 0
        weakened = mult >= 1
        if extended and weakened:
            counts["both"] += 1
        elif extended:
            counts["extension_only"] += 1
        elif weakened:
            counts["weakening_only"] += 1
        else:
            counts["neither"] += 1
    return counts


def conditional_raw_return(anchors: list[dict], predicate) -> dict:
    """**Descriptive only.** Raw forward ``return_bps`` for the anchors satisfying ``predicate``,
    aggregated as a MEAN OF SESSION-CLUSTER MEANS rather than a flat pooled mean.

    r14.3 renamed this from ``conditional_outcome`` and its magnitude from ``effect_bps`` to
    ``raw_return_bps``, deliberately. ``effect_bps`` is Scout's name for the DECISION statistic --
    the mean of per-session candidate-minus-comparator deltas -- and a one-cell raw mean sitting in
    a field with the same name is precisely how market drift gets mistaken for a mechanism. These
    two numbers answer different questions and must never be confusable by field name.

    The session-cluster aggregation mirrors spec §5.3 and ``scout._observed_effect``, so a
    descriptive number here is at least the same KIND of number as the decision statistic.

    Every outcome's unit is PROVEN, not assumed -- a non-``return_bps`` anchor raises rather than
    being averaged into a bps figure (the r13 unit-provenance discipline)."""
    selected = [a for a in anchors if predicate(a)]
    if not selected:
        return {"n": 0, "n_sessions": 0, "n_symbols": 0, "raw_return_bps": None, "sign": None,
                "unit": mf.OUTCOME_UNIT, "label": "descriptive only -- not a decision statistic"}
    by_session: dict[str, list[float]] = {}
    symbols: set[str] = set()
    for a in selected:
        mf.require_return_bps_effect(a["outcome_bps"], a.get("outcome_unit"))
        by_session.setdefault(a["session_date"], []).append(a["outcome_bps"])
        symbols.add(a["symbol"])
    raw = statistics.mean([statistics.mean(v) for v in by_session.values()])
    return {
        "n": len(selected),
        "n_sessions": len(by_session),
        "n_symbols": len(symbols),
        "raw_return_bps": raw,
        "sign": "positive" if raw > 0 else ("negative" if raw < 0 else "zero"),
        "unit": mf.OUTCOME_UNIT,
        "label": "descriptive only -- not a decision statistic",
    }


def _defined(a: dict) -> bool:
    return (
        a.get("price_extension_bps") is not None
        and a.get("delta_weakening_multiple") is not None
    )


def _mechanism_fired(a: dict) -> bool:
    """Card 9.1's predeclared corner of the continuous plane. Identical to ``bearish_divergence``
    over the defined domain -- see ``micro_features.DIVERGENCE_CONTINUOUS_EQUIVALENCE``."""
    return _defined(a) and a["price_extension_bps"] > 0 and a["delta_weakening_multiple"] >= 1


def continuous_report(anchors: list[dict]) -> dict:
    """**The continuous representation, and NOTHING that decides anything** (r14.3).

    goal.md requires continuous mechanism-defined representations first and threshold variants
    second, so this is computed first and independently of any screen. Every field is descriptive:
    counts, distributions, quadrants, and the two cells' raw returns. None of them, alone or in
    combination, produces ``KILLED`` or ``PROMISING_FOR_MODE_B_FREEZE`` -- that mapping lives in
    ``study2_outcome_from_scout`` and reads only a Scout decision.

    ``descriptive_separation_bps`` is retained because it is genuinely informative to a reader, and
    it is explicitly NOT the decision statistic: it is a difference of two session-cluster means
    taken over DIFFERENT session sets, whereas Scout's ``effect_bps`` is the mean of per-session
    paired deltas over the sessions where BOTH cells are present. They can disagree in sign, and
    when they do, Scout is right."""
    fired = conditional_raw_return(anchors, _mechanism_fired)
    did_not_fire = conditional_raw_return(anchors, lambda a: _defined(a) and not _mechanism_fired(a))
    separation = (
        None
        if fired["raw_return_bps"] is None or did_not_fire["raw_return_bps"] is None
        else fired["raw_return_bps"] - did_not_fire["raw_return_bps"]
    )
    usable = [a for a in anchors if _defined(a)]
    quadrants = quadrant_counts(anchors)
    return {
        "evidence_class": EVIDENCE_CLASS,
        "graduation_credit": GRADUATION_CREDIT,
        "n_paired_touch_anchors": len(anchors),
        "n_usable_anchors": len(usable),
        "n_undefined_anchors": len(anchors) - len(usable),
        "n_session_dates": len({a["session_date"] for a in anchors}),
        "n_symbols": len({a["symbol"] for a in anchors}),
        "price_extension_bps": continuous_distribution(
            [a.get("price_extension_bps") for a in anchors]
        ),
        "delta_weakening_multiple": continuous_distribution(
            [a.get("delta_weakening_multiple") for a in anchors]
        ),
        "quadrants": quadrants,
        # Both cells' RAW returns, named so they can never be read as the decision statistic.
        "mechanism_raw_return_bps": fired["raw_return_bps"],
        "comparator_raw_return_bps": did_not_fire["raw_return_bps"],
        "mechanism_cell": fired,
        "comparator_cell": did_not_fire,
        "descriptive_separation_bps": separation,
        "descriptive_separation_label": (
            "DESCRIPTIVE ONLY -- a difference of two cell means over different session sets. The "
            "decision statistic is Scout's effect_bps: the mean of per-session "
            "candidate-minus-comparator deltas over sessions carrying BOTH cells."
        ),
        # The boolean stays visible as ONE predeclared transform of the plane above, never as an
        # independent result: `both` IS `bearish_divergence` over the defined domain.
        "boolean_variant": {
            "definition": mf.DIVERGENCE_CONTINUOUS_EQUIVALENCE,
            "n_fired": quadrants["both"],
        },
    }


def study2_outcome_from_scout(screen: dict) -> dict:
    """Map a ``scout.screen_candidate`` result onto Study 2's three honest answers (r14.3).

    ``screen`` is the whole ``{decision, reason, notes, screen_result}`` dict, or a ledger row
    carrying the same two keys.

    The mapping, in full:

      * ``killed_insufficient_n``  -> ``INSUFFICIENT``. The one kill that means *we could not look*:
        Scout's own cell and session-cluster floors were not met, so no screen was computed.
      * any other kill (``killed_null``, ``killed_concentration``, ``killed_economic``,
        ``killed_fragile``, ``killed_direction``, ...) -> ``KILLED``. We looked, and it failed. The
        list is deliberately open: a kill this module has never heard of is still a kill, never a
        promotion.
      * ``survive`` -> Card 9.1's own semantics decide, and only then:
          - ``effect_bps < 0``  -> ``PROMISING_FOR_MODE_B_FREEZE``, proposed direction ``short``.
          - ``effect_bps >= 0`` -> ``KILLED``. A bearish mechanism that survives with a POSITIVE
            candidate-minus-comparator effect has been contradicted by its own evidence. It is
            never re-read as a long hypothesis -- that would be reversing the stated mechanism
            after seeing discovery data.

    Note the asymmetry that makes this safe: every path out of a non-``survive`` decision leads to
    ``INSUFFICIENT`` or ``KILLED``. ``PROMISING`` is reachable only through Scout's full ladder --
    sufficiency, the block-permutation null, concentration, the economic floor and
    leave-one-session-out fragility -- and then only with the correct sign."""
    decision = screen.get("decision")
    effect_bps = (screen.get("screen_result") or {}).get("effect_bps")

    if decision == SCOUT_DECISION_INSUFFICIENT:
        return {
            "outcome": OUTCOME_INSUFFICIENT,
            "scout_decision": decision,
            "decision_statistic_effect_bps": effect_bps,
            "proposed_direction": None,
            "reason": (
                "Scout refused the screen on its own sufficiency floors "
                f"({screen.get('notes')}) -- the exposed legacy corpus cannot answer Study 2. "
                "Nothing is claimed in either direction."
            ),
        }
    if decision != _SCOUT_DECISION_SURVIVE:
        return {
            "outcome": OUTCOME_KILLED,
            "scout_decision": decision,
            "decision_statistic_effect_bps": effect_bps,
            "proposed_direction": None,
            "reason": (
                f"Scout screened the candidate and killed it: {decision} ({screen.get('notes')}). "
                "Study 2 dies here, cheaply, having spent no fresh evidence."
            ),
        }
    if effect_bps is None or effect_bps >= 0:
        return {
            "outcome": OUTCOME_KILLED,
            "scout_decision": decision,
            "decision_statistic_effect_bps": effect_bps,
            "proposed_direction": None,
            "reason": (
                f"Scout survived with effect_bps={effect_bps!r} -- a NON-NEGATIVE "
                "candidate-minus-comparator effect for an explicitly BEARISH mechanism. Card 9.1 "
                "is contradicted by its own evidence. This is never re-read as a long hypothesis: "
                "reversing a stated mechanism after seeing discovery data is exactly the "
                "post-hoc freedom this funnel exists to remove."
            ),
        }
    return {
        "outcome": OUTCOME_PROMISING,
        "scout_decision": decision,
        "decision_statistic_effect_bps": effect_bps,
        "proposed_direction": PROPOSED_DIRECTION,
        "reason": (
            f"Scout survived its full ladder with effect_bps={effect_bps!r} -- correctly signed "
            "for a bearish mechanism. This is permission to FREEZE a Mode B short rule and only "
            "then record; it is not evidence of edge, and it can never graduate."
        ),
    }


def study2_diagnostic(anchors: list[dict], *, screen: dict) -> dict:
    """The whole Study 2 exposed-corpus report: the continuous representation FIRST, then the
    outcome read off ``screen`` (r14.3).

    ``anchors`` and ``screen`` MUST come from the same extraction -- the continuous report and the
    threshold screen describe one body of evidence, and computing them over two extractions would
    let them silently disagree. The caller owns that (see ``scripts/study2_diagnostic.py``), because
    this module deliberately reads no store and opens no dataset: it cannot reach a sealed shard
    even by accident."""
    report = continuous_report(anchors)
    verdict = study2_outcome_from_scout(screen)
    return {
        **report,
        **verdict,
        "scout": {
            "decision": screen.get("decision"),
            "reason": screen.get("reason"),
            "notes": screen.get("notes"),
            "screen_result": screen.get("screen_result"),
        },
    }
