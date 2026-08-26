"""``micro_study2_diagnostic.py`` -- Study 2's CONTINUOUS exposed-corpus diagnostic (r14.2, §8).

**What this is for.** Before anyone spends storage, retention risk and months of recording on an
out-of-sample campaign for divergence-at-level, one cheap question has to be answered on evidence
that is already spent: *does the exposed legacy tick corpus even produce enough paired-touch
anchors to estimate anything?* This module builds the report that answers it. It does not run it.

**What it may read, and what it may never read.** Study 2 discovery runs on
``historical_exposed_diagnostic`` evidence only -- the legacy tick symbol-days that ``r2``
initialization already marks exposed for their entire span. Nothing here releases a withheld
starter member, touches a sealed shard, reads ``historical_oos`` data, consults a Vault outcome, or
registers a direction. Those are the acts that would spend real evidence, and the whole point of an
exposed-corpus diagnostic is that it spends none.

**Why the result can never graduate.** Every anchor this report summarizes comes from a window that
was exposed long before any rule could have been frozen against it, so by the mechanical rule in
``walkforward.classify_evidence_class`` it is diagnostic evidence, permanently. That is a fact
about the DATA, not a policy this module applies -- which is exactly why it is safe to look. A
promising number here justifies freezing a Mode B hypothesis and *then* recording; it is never
itself a survivor, a graduation, or a claim about live edge. ``EVIDENCE_CLASS`` and
``GRADUATION_CREDIT`` below state that in-band on every report this module emits.

**The representation is continuous, and that is the point (goal.md).** goal.md requires continuous
mechanism-defined representations first and threshold variants second. Card 9.1's boolean answers
"did this pair sit in the bearish corner?", which throws away how far into the corner it sat and
cannot distinguish a hair-crossing from an extreme one. This module summarizes the two coordinates
``micro_features.divergence_at_level`` now returns -- ``price_extension_bps`` and
``delta_weakening_multiple`` -- and reports the boolean as one predeclared corner of that plane
(``extension > 0 and weakening >= 1``), never as a separate measurement.

**No sweep, no search, no manufactured survivor.** The quadrant counts below are the FOUR corners of
the two predeclared axis origins (0 and 1), which is the mechanism's own structure, not a grid. This
module offers no threshold sweep, no candidate ranking and no selection rule. If the honest answer
is "too few anchors", that is the answer.
"""

from __future__ import annotations

import statistics

from . import micro_features as mf

__all__ = [
    "EVIDENCE_CLASS",
    "GRADUATION_CREDIT",
    "MIN_ANCHORS_FOR_AN_ESTIMATE",
    "OUTCOME_INSUFFICIENT",
    "OUTCOME_KILLED",
    "OUTCOME_PROMISING",
    "continuous_distribution",
    "quadrant_counts",
    "conditional_outcome",
    "study2_continuous_diagnostic",
]

#: Every row this module produces is diagnostic, by construction -- see the module docstring.
EVIDENCE_CLASS = "historical_exposed_diagnostic"
GRADUATION_CREDIT = "none -- exposed-corpus discovery can never graduate a candidate"

#: The floor below which no distribution summary is meaningful. Deliberately the SAME number as
#: ``walkforward.WF_FOLD_MIN_OBSERVATIONS`` (30), reused rather than re-chosen: a discovery sample
#: too thin to satisfy one walk-forward fold is too thin to justify recording a campaign for.
MIN_ANCHORS_FOR_AN_ESTIMATE = 30

#: The three honest answers this diagnostic can return. Named constants because the operator brief
#: asks for exactly one of them, and a free-text verdict is how a "maybe" survives review.
OUTCOME_INSUFFICIENT = "INSUFFICIENT"
OUTCOME_KILLED = "KILLED"
OUTCOME_PROMISING = "PROMISING_FOR_MODE_B_FREEZE"


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


def conditional_outcome(anchors: list[dict], predicate) -> dict:
    """Canonical forward ``return_bps`` for the anchors satisfying ``predicate``, aggregated the way
    the rest of this era aggregates: MEAN OF SESSION-CLUSTER MEANS, never a flat pooled mean.

    A flat mean lets one busy session dominate; the session-cluster mean is the aggregation spec
    §5.3 and ``walkforward.summarize_fold_observations`` already use, mirrored here so a discovery
    number and a fold number are the same KIND of number.

    Every outcome's unit is PROVEN, not assumed -- a non-``return_bps`` anchor raises rather than
    being averaged into a bps figure (the r13 unit-provenance discipline)."""
    selected = [a for a in anchors if predicate(a)]
    if not selected:
        return {"n": 0, "n_sessions": 0, "n_symbols": 0, "effect_bps": None, "sign": None,
                "unit": mf.OUTCOME_UNIT}
    by_session: dict[str, list[float]] = {}
    symbols: set[str] = set()
    for a in selected:
        mf.require_return_bps_effect(a["outcome_bps"], a.get("outcome_unit"))
        by_session.setdefault(a["session_date"], []).append(a["outcome_bps"])
        symbols.add(a["symbol"])
    effect = statistics.mean([statistics.mean(v) for v in by_session.values()])
    return {
        "n": len(selected),
        "n_sessions": len(by_session),
        "n_symbols": len(symbols),
        "effect_bps": effect,
        "sign": "positive" if effect > 0 else ("negative" if effect < 0 else "zero"),
        "unit": mf.OUTCOME_UNIT,
    }


def study2_continuous_diagnostic(anchors: list[dict], *, econ_floor_bps: float | None = None) -> dict:
    """The whole exposed-corpus report for Study 2, over ALREADY-EXTRACTED paired-touch anchors.

    Takes anchors rather than a corpus so this module reads no store, opens no dataset and cannot
    reach a sealed shard even by accident -- the caller does the reading, through the ordinary
    exposed-corpus path, and hands the result here.

    ``econ_floor_bps`` is optional and purely descriptive: when supplied, the report says whether
    the mechanism's conditional effect clears it. Supplying it does NOT make this a screen, a
    survivor test or a graduation -- see ``GRADUATION_CREDIT``.

    **The verdict.** Card 9.1 is a BEARISH mechanism, so its evidence is a claim about SHORT edge:
    a negative conditional forward return is the mechanism working, a positive one is it working
    backwards. The report therefore reads:

      * ``INSUFFICIENT``  -- fewer than ``MIN_ANCHORS_FOR_AN_ESTIMATE`` usable anchors, or no
        session/symbol breadth. Nothing is claimed in either direction.
      * ``KILLED`` -- enough anchors, but the mechanism's own cell is null, points the WRONG way
        (positive forward return for a bearish setup), or is economically negligible against
        ``econ_floor_bps``. Study 2 dies here, cheaply, having spent no fresh evidence.
      * ``PROMISING_FOR_MODE_B_FREEZE`` -- enough anchors, right sign, and (if a floor was given)
        past it. This is the ONLY outcome that justifies freezing a long|short Mode B rule and then
        paying for an OOS campaign. It is not evidence of edge; it is permission to go looking for
        some under falsifiable conditions."""
    ext_values = [a.get("price_extension_bps") for a in anchors]
    mult_values = [a.get("delta_weakening_multiple") for a in anchors]
    quadrants = quadrant_counts(anchors)

    def _defined(a: dict) -> bool:
        return a.get("price_extension_bps") is not None and a.get("delta_weakening_multiple") is not None

    def _mechanism(a: dict) -> bool:
        return (
            _defined(a)
            and a["price_extension_bps"] > 0
            and a["delta_weakening_multiple"] >= 1
        )

    fired = conditional_outcome(anchors, _mechanism)
    did_not_fire = conditional_outcome(anchors, lambda a: _defined(a) and not _mechanism(a))

    usable = [a for a in anchors if _defined(a)]
    report = {
        "evidence_class": EVIDENCE_CLASS,
        "graduation_credit": GRADUATION_CREDIT,
        "n_paired_touch_anchors": len(anchors),
        "n_usable_anchors": len(usable),
        "n_session_dates": len({a["session_date"] for a in anchors}),
        "n_symbols": len({a["symbol"] for a in anchors}),
        "price_extension_bps": continuous_distribution(ext_values),
        "delta_weakening_multiple": continuous_distribution(mult_values),
        "quadrants": quadrants,
        "mechanism_fired": fired,
        "mechanism_did_not_fire": did_not_fire,
        "econ_floor_bps": econ_floor_bps,
        # The boolean stays visible as ONE predeclared transform of the plane above, never as an
        # independent result: `both` IS `bearish_divergence` over the defined domain.
        "boolean_variant": {
            "definition": mf.DIVERGENCE_CONTINUOUS_EQUIVALENCE,
            "n_fired": quadrants["both"],
        },
    }

    if len(usable) < MIN_ANCHORS_FOR_AN_ESTIMATE or fired["n_sessions"] == 0:
        report["outcome"] = OUTCOME_INSUFFICIENT
        report["reason"] = (
            f"{len(usable)} usable anchors across {report['n_session_dates']} session dates -- "
            f"below the {MIN_ANCHORS_FOR_AN_ESTIMATE}-anchor floor for any estimate. The exposed "
            "legacy corpus cannot answer this question; nothing is claimed in either direction."
        )
        return report

    effect = fired["effect_bps"]
    separation = None if did_not_fire["effect_bps"] is None else effect - did_not_fire["effect_bps"]
    report["separation_bps"] = separation
    if effect is None or effect >= 0:
        report["outcome"] = OUTCOME_KILLED
        report["reason"] = (
            f"the mechanism's own cell returns {effect} bps forward -- a BEARISH setup with a "
            "non-negative forward return is the mechanism working backwards or not at all. Study 2 "
            "dies here, having spent no fresh evidence."
        )
    elif econ_floor_bps is not None and abs(effect) < econ_floor_bps:
        report["outcome"] = OUTCOME_KILLED
        report["reason"] = (
            f"the mechanism's cell returns {effect} bps, whose magnitude is below the "
            f"{econ_floor_bps} bps economic floor -- correctly signed but too small to be worth an "
            "OOS campaign."
        )
    else:
        report["outcome"] = OUTCOME_PROMISING
        report["reason"] = (
            f"{fired['n']} anchors across {fired['n_sessions']} sessions and "
            f"{fired['n_symbols']} symbols return {effect} bps forward -- correctly signed for a "
            "bearish mechanism. This is permission to FREEZE a Mode B short rule and then record; "
            "it is not evidence of edge, and it can never graduate."
        )
    return report
