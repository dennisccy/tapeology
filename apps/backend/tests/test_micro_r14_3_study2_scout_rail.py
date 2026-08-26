"""r14.3 -- Study 2's DECISION belongs to the frozen Scout screen, not to this module.

r14.2 built Study 2's continuous representation correctly and then bolted a home-made decision rail
onto it. That rail was wrong twice over, and each way could promote a candidate that the project's
own frozen discovery screen would have killed:

* **A borrowed sample floor.** ``MIN_ANCHORS_FOR_AN_ESTIMATE = 30`` came from
  ``walkforward.WF_FOLD_MIN_OBSERVATIONS`` -- a walk-forward FOLD floor -- and was applied to ALL
  usable anchors, while the decision itself passed on ``fired.n_sessions > 0``. Thirty usable
  anchors of which exactly one fired, in one session, could reach
  ``PROMISING_FOR_MODE_B_FREEZE``.
* **The wrong statistic.** The verdict read the mechanism-fired cell's OWN raw mean. The frozen
  discovery statistic is candidate-versus-comparator. A fired cell at -2 bps against a comparator
  at -8 bps looks bearish and is +6 bps WORSE than the alternative.

This file is the executable contract for the fix: the continuous report decides nothing, and the
outcome is read off ``scout.screen_candidate``'s decision over the SAME anchors.

Every fixture here is hermetic -- hand-built anchor lists, no store, no real corpus.
"""

from __future__ import annotations

import pytest

from app.research import micro_features as mf
from app.research import micro_study2_diagnostic as s2
from app.research import scout
from app.research import walkforward as wf

_HORIZON = "trades_20"
_FAMILY = "r143-fixture-family"
# The frozen Study 2 pilot transform, exactly as `pilot_study_candidate_grid` registers it.
_TRANSFORM = "threshold"
_PARAMS = {"op": "ge", "value": 1.0}


def _anchor(session_date, symbol, *, fired, outcome_bps, ext=None, mult=None, trade_index=0):
    """One paired-touch anchor. ``fired`` sets BOTH the Card 9.1 boolean feature value the Scout
    threshold reads AND coordinates consistent with it, so the continuous plane and the screened
    variant always describe the same anchor -- which is the invariant this file exists to protect."""
    if ext is None:
        ext = 10.0 if fired else -3.0
    if mult is None:
        mult = 2.0 if fired else 0.5
    return {
        "dataset_id": f"ds-{symbol}-{session_date}",
        "symbol": symbol,
        "session_date": session_date,
        "anchor_at": float(trade_index),
        "trade_index": trade_index,
        "feature_value": 1.0 if fired else 0.0,
        "outcome_bps": outcome_bps,
        "outcome_unit": mf.OUTCOME_UNIT,
        "tod_bucket": "midday",
        "fallback_frac": 0.0,
        "price_extension_bps": ext,
        "delta_weakening_multiple": mult,
    }


def _econ_floor(floor_bps: float) -> dict:
    """The SAME econ-floor object shape ``build_candidate_spec_fields`` freezes -- never a
    free-floating number this module invents for a parallel economic check."""
    return {
        "multiple": scout.ECON_FLOOR_SPREAD_MULTIPLE,
        "family_median_spread_bps": floor_bps / scout.ECON_FLOOR_SPREAD_MULTIPLE,
        "floor_bps": floor_bps,
        "unit": mf.BPS_UNIT,
        "proxy_sentence": scout.ECON_PROXY_SENTENCE,
    }


def _screen(anchors, *, floor_bps=0.01, n_variants_tried=1):
    return scout.screen_candidate(
        feature_name="divergence_at_level_bearish", transform=_TRANSFORM, params=_PARAMS,
        sidedness=None, horizon_key=_HORIZON, econ_floor=_econ_floor(floor_bps),
        anchors=anchors, family_id=_FAMILY, n_variants_tried=n_variants_tried,
    )


def _diagnose(anchors, **kw):
    return s2.study2_diagnostic(anchors, screen=_screen(anchors, **kw))


# =====================================================================================================
# The two structural facts the fix rests on
# =====================================================================================================


def test_the_borrowed_thirty_anchor_decision_floor_is_gone():
    """The second sample rail is removed outright, not merely bypassed. Scout owns sufficiency."""
    assert not hasattr(s2, "MIN_ANCHORS_FOR_AN_ESTIMATE")
    assert "MIN_ANCHORS_FOR_AN_ESTIMATE" not in s2.__all__


def test_the_continuous_report_decides_nothing_on_its_own():
    """Continuous FIRST, threshold second -- and the continuous half carries no verdict at all."""
    anchors = [_anchor("2026-04-01", "AAPL", fired=True, outcome_bps=-50.0)]
    report = s2.continuous_report(anchors)
    for verdict_key in ("outcome", "proposed_direction", "scout_decision"):
        assert verdict_key not in report, f"{verdict_key} must not be reachable from descriptives"
    assert report["evidence_class"] == "historical_exposed_diagnostic"


def test_the_raw_cell_mean_is_not_named_effect_bps():
    """``effect_bps`` is Scout's DECISION statistic. A one-cell raw mean under the same field name
    is exactly how market drift gets mistaken for a mechanism."""
    anchors = [_anchor("2026-04-01", "AAPL", fired=True, outcome_bps=-50.0)]
    report = s2.continuous_report(anchors)
    assert "effect_bps" not in report
    assert report["mechanism_raw_return_bps"] == pytest.approx(-50.0)
    assert report["mechanism_cell"]["label"].startswith("descriptive only")
    assert "DESCRIPTIVE ONLY" in report["descriptive_separation_label"]


def test_the_insufficient_sentinel_matches_scouts_own_vocabulary():
    assert s2.SCOUT_DECISION_INSUFFICIENT == "killed_insufficient_n"
    assert s2.SCOUT_DECISION_INSUFFICIENT in scout.CLOSED_DECISIONS
    assert s2._SCOUT_DECISION_SURVIVE == scout.SCOUT_DECISION_SURVIVE


# =====================================================================================================
# A. THIN FIRED CELL -- the exact false promotion the old rail permitted
# =====================================================================================================


def test_a_thirty_anchor_corpus_with_one_fired_anchor_is_insufficient_never_promising():
    """**The r14.2 regression, pinned.** 30+ usable anchors, but the candidate cell holds ONE
    anchor from ONE session. The old rail cleared its 30-anchor floor, saw ``n_sessions == 1 > 0``,
    read the single -50 bps observation and returned PROMISING. Scout's own cell floor refuses."""
    anchors = [_anchor("2026-04-01", "AAPL", fired=True, outcome_bps=-50.0)]
    anchors += [
        _anchor(f"2026-04-{(i % 10) + 1:02d}", "AAPL", fired=False, outcome_bps=1.0, trade_index=i)
        for i in range(35)
    ]
    assert len([a for a in anchors if a["feature_value"] >= 1.0]) == 1
    assert len(anchors) > 30, "the OLD 30-anchor floor is cleared -- that was never the safeguard"

    result = _diagnose(anchors)
    assert result["scout_decision"] == "killed_insufficient_n"
    assert result["outcome"] == s2.OUTCOME_INSUFFICIENT
    assert result["proposed_direction"] is None
    assert result["scout"]["screen_result"]["n_candidate"] == 1
    assert result["scout"]["screen_result"]["n_candidate"] < scout.SCOUT_MIN_OBSERVATIONS_PER_CELL
    # The single fired observation is still REPORTED, descriptively -- suppressed nowhere.
    assert result["mechanism_raw_return_bps"] == pytest.approx(-50.0)


def test_a_single_usable_session_is_insufficient_even_with_full_cells():
    """The other half of Scout's sufficiency rule: you cannot permute across one cluster."""
    anchors = [
        _anchor("2026-04-01", "AAPL", fired=True, outcome_bps=-9.0, trade_index=i) for i in range(8)
    ] + [
        _anchor("2026-04-01", "AAPL", fired=False, outcome_bps=1.0, trade_index=50 + i)
        for i in range(8)
    ]
    result = _diagnose(anchors)
    assert result["scout"]["screen_result"]["n_usable_sessions"] < scout.SCOUT_MIN_SESSION_CLUSTERS
    assert result["outcome"] == s2.OUTCOME_INSUFFICIENT


# =====================================================================================================
# B. MARKET DRIFT COUNTEREXAMPLE -- a bearish-looking cell that is worse than its comparator
# =====================================================================================================


def test_b_a_bearish_looking_cell_that_underperforms_its_comparator_is_never_promising():
    """The mechanism cell returns about -2 bps and LOOKS bearish. The comparator returns about
    -8 bps. Candidate-minus-comparator is therefore POSITIVE: the mechanism is +6 bps worse than
    the alternative, and what the old rail read as a bearish edge is market-wide drift."""
    anchors = []
    for d in range(1, 7):
        date = f"2026-04-{d:02d}"
        for i in range(6):
            anchors.append(_anchor(date, "AAPL", fired=True, outcome_bps=-2.0, trade_index=i))
            anchors.append(_anchor(date, "MSFT", fired=False, outcome_bps=-8.0, trade_index=50 + i))

    report = s2.continuous_report(anchors)
    assert report["mechanism_raw_return_bps"] == pytest.approx(-2.0)
    assert report["comparator_raw_return_bps"] == pytest.approx(-8.0)
    assert report["mechanism_raw_return_bps"] < 0, "the fired cell really does look bearish"

    result = _diagnose(anchors)
    effect = result["scout"]["screen_result"]["effect_bps"]
    assert effect == pytest.approx(6.0), "candidate MINUS comparator is positive"
    assert result["outcome"] != s2.OUTCOME_PROMISING
    assert result["outcome"] == s2.OUTCOME_KILLED
    assert result["proposed_direction"] is None


# =====================================================================================================
# C-F. EVERY OTHER SCOUT KILL MAPS TO KILLED
# =====================================================================================================


def test_c_a_null_effect_is_killed():
    """Adequate cells and sessions, but the effect does not clear the block-permutation null."""
    anchors = []
    for d in range(1, 9):
        date = f"2026-04-{d:02d}"
        for i in range(6):
            anchors.append(_anchor(date, "AAPL", fired=True, outcome_bps=-1.0, trade_index=i))
            anchors.append(_anchor(date, "MSFT", fired=False, outcome_bps=-1.0, trade_index=50 + i))
    result = _diagnose(anchors)
    assert result["scout_decision"] == "killed_null"
    assert result["outcome"] == s2.OUTCOME_KILLED


def test_d_a_concentrated_effect_is_killed():
    """A large, correctly-signed, statistically significant effect drawn almost entirely from ONE
    session is an idiosyncrasy risk, and Scout's frozen ceiling -- not a rule this module invents --
    is what kills it. The fixture must clear the null gate first, or it would die at
    ``killed_null`` and prove nothing about concentration."""
    anchors = []
    # 8 usable sessions, every one carrying the same strongly negative delta (so the permutation
    # null is beaten), but session 1 holds 60 of the 74 candidate anchors -> top1 share ~0.81.
    for i in range(60):
        anchors.append(_anchor("2026-04-01", "AAPL", fired=True, outcome_bps=-40.0, trade_index=i))
    for i in range(6):
        anchors.append(_anchor("2026-04-01", "AAPL", fired=False, outcome_bps=2.0, trade_index=90 + i))
    for d in range(2, 9):
        date = f"2026-04-{d:02d}"
        for i in range(2):
            anchors.append(_anchor(date, "AAPL", fired=True, outcome_bps=-40.0, trade_index=i))
        for i in range(6):
            anchors.append(_anchor(date, "AAPL", fired=False, outcome_bps=2.0, trade_index=90 + i))

    result = _diagnose(anchors)
    conc = result["scout"]["screen_result"]["concentration"]
    assert conc["top1_session_share"] > scout.SCOUT_MAX_TOP1_CONCENTRATION
    assert result["scout"]["screen_result"]["p_screen"] < scout.SCOUT_SCREEN_ALPHA, (
        "the fixture must clear the null gate, or this proves nothing about concentration"
    )
    assert result["scout"]["screen_result"]["effect_bps"] < 0, "and be correctly signed"
    assert result["scout_decision"] == "killed_concentration"
    assert result["outcome"] == s2.OUTCOME_KILLED


def test_e_an_economically_negligible_effect_is_killed():
    """Statistically interesting, correctly signed, and too small to trade -- judged against the
    SPEC's econ_floor object, never a free-floating econ_floor_bps this module passes in."""
    anchors = []
    for d in range(1, 13):
        date = f"2026-04-{d:02d}"
        for i in range(6):
            anchors.append(_anchor(date, "AAPL", fired=True, outcome_bps=-1.0 - 0.01 * d,
                                   trade_index=i))
            anchors.append(_anchor(date, "MSFT", fired=False, outcome_bps=0.0, trade_index=50 + i))
    result = _diagnose(anchors, floor_bps=25.0)
    assert result["scout_decision"] == "killed_economic"
    assert result["outcome"] == s2.OUTCOME_KILLED
    assert result["scout"]["screen_result"]["econ_interesting"] is False


def test_f_a_fragile_effect_is_killed():
    """Passes the null, concentration and economic gates, then dies on leave-one-session-out.

    **This fixture took real care to build, and the reason is worth recording.** Scout's gate ORDER
    means most "fragile-looking" shapes -- one outlier session dragging the mean -- are caught by
    the block-permutation null first, because an outlier large enough to flip the sign also widens
    that session's own rotated null. Reaching the fragility gate needs a session whose candidate
    cell is a SMALL CONTIGUOUS block inside a large session: rotating the label sequence then moves
    that block almost entirely onto the comparator outcomes, so the null is tight while the
    observed delta stays extreme. That is a genuine property of the rail, not a fixture trick."""
    anchors = []
    # The dominant session: 40 candidate anchors (the most of any session, but only 27% of all
    # candidates, so the concentration ceiling is NOT what kills this) inside 1,200 anchors.
    t = 0
    for _ in range(40):
        anchors.append(_anchor("2026-04-01", "AAPL", fired=True, outcome_bps=-600.0, trade_index=t))
        t += 1
    for _ in range(1_200 - 40):
        anchors.append(_anchor("2026-04-01", "AAPL", fired=False, outcome_bps=0.0, trade_index=t))
        t += 1
    # Eleven ordinary sessions leaning the OTHER way, so dropping the dominant one flips the sign.
    for d in range(2, 13):
        date = f"2026-04-{d:02d}"
        t = 0
        for _ in range(10):
            anchors.append(_anchor(date, "AAPL", fired=True, outcome_bps=5.0, trade_index=t))
            t += 1
        for _ in range(190):
            anchors.append(_anchor(date, "AAPL", fired=False, outcome_bps=0.0, trade_index=t))
            t += 1

    result = _diagnose(anchors, floor_bps=0.01)
    sr = result["scout"]["screen_result"]
    # Every earlier gate genuinely PASSED -- otherwise this would prove nothing about fragility.
    assert sr["p_screen"] < scout.SCOUT_SCREEN_ALPHA, "the null gate must be cleared"
    assert sr["concentration"]["top1_session_share"] <= scout.SCOUT_MAX_TOP1_CONCENTRATION
    assert sr["econ_interesting"] is True, "the economic gate must be cleared"
    assert sr["effect_bps"] < 0, "and the effect must be correctly signed for a bearish mechanism"
    # ... and it still dies, because the sign does not survive dropping one session.
    assert result["scout_decision"] == "killed_fragile"
    assert result["outcome"] == s2.OUTCOME_KILLED
    assert result["proposed_direction"] is None, (
        "a correctly-signed, significant, economically-material effect that is FRAGILE must never "
        "reach PROMISING"
    )


def test_an_unknown_future_scout_kill_still_maps_to_killed():
    """The mapping is open at the kill end deliberately: a decision this module has never heard of
    is a kill, never a promotion."""
    verdict = s2.study2_outcome_from_scout(
        {"decision": "killed_something_invented_later", "notes": "n/a",
         "screen_result": {"effect_bps": -99.0}}
    )
    assert verdict["outcome"] == s2.OUTCOME_KILLED
    assert verdict["proposed_direction"] is None


# =====================================================================================================
# G/H. THE ONLY PATH TO PROMISING, AND THE SEMANTIC DIRECTION GATE
# =====================================================================================================


def test_g_a_surviving_correctly_signed_effect_is_promising_and_proposes_short():
    anchors = []
    for d in range(1, 13):
        date = f"2026-04-{d:02d}"
        for i in range(6):
            anchors.append(_anchor(date, "AAPL", fired=True, outcome_bps=-40.0 - d, trade_index=i))
            anchors.append(_anchor(date, "MSFT", fired=False, outcome_bps=0.0, trade_index=50 + i))
    result = _diagnose(anchors, floor_bps=1.0)
    assert result["scout_decision"] == scout.SCOUT_DECISION_SURVIVE
    assert result["scout"]["screen_result"]["effect_bps"] < 0
    assert result["outcome"] == s2.OUTCOME_PROMISING
    assert result["proposed_direction"] == "short"
    assert "never" in result["reason"] and "graduate" in result["reason"]
    assert result["evidence_class"] == "historical_exposed_diagnostic", (
        "even PROMISING is permanently diagnostic"
    )


def test_h_a_surviving_positive_effect_is_killed_and_never_proposes_long():
    """Card 9.1 is explicitly BEARISH. A statistically surviving POSITIVE effect contradicts the
    stated mechanism; re-reading it as a long hypothesis would be reversing the mechanism after
    seeing discovery data."""
    anchors = []
    for d in range(1, 13):
        date = f"2026-04-{d:02d}"
        for i in range(6):
            anchors.append(_anchor(date, "AAPL", fired=True, outcome_bps=40.0 + d, trade_index=i))
            anchors.append(_anchor(date, "MSFT", fired=False, outcome_bps=0.0, trade_index=50 + i))
    result = _diagnose(anchors, floor_bps=1.0)
    assert result["scout_decision"] == scout.SCOUT_DECISION_SURVIVE
    assert result["scout"]["screen_result"]["effect_bps"] > 0
    assert result["outcome"] == s2.OUTCOME_KILLED
    assert result["proposed_direction"] is None
    assert s2.PROPOSED_DIRECTION == "short", "this module can only ever propose short"
    # There is NO input to the mapping that can yield any direction other than short: the only
    # branch that sets one at all is the surviving-negative branch.
    for effect in (-1.0, -1e9, 1.0, 1e9, 0.0, None):
        verdict = s2.study2_outcome_from_scout(
            {"decision": "survive", "notes": "", "screen_result": {"effect_bps": effect}}
        )
        assert verdict["proposed_direction"] in (None, "short")


def test_a_surviving_exactly_zero_effect_is_killed():
    """The boundary is explicit: zero is not bearish."""
    verdict = s2.study2_outcome_from_scout(
        {"decision": "survive", "notes": "", "screen_result": {"effect_bps": 0.0}}
    )
    assert verdict["outcome"] == s2.OUTCOME_KILLED


# =====================================================================================================
# I. THE CONTINUOUS REPORT IS INVARIANT TO THE VERDICT
# =====================================================================================================


def test_i_the_continuous_coordinates_are_identical_regardless_of_the_scout_verdict():
    """Continuous-first means the representation is a property of the EVIDENCE, not of the outcome.
    The same anchors screened under two different economic floors -- one surviving, one killed --
    must yield byte-identical continuous halves."""
    anchors = []
    for d in range(1, 13):
        date = f"2026-04-{d:02d}"
        for i in range(6):
            anchors.append(_anchor(date, "AAPL", fired=True, outcome_bps=-40.0 - d, trade_index=i))
            anchors.append(_anchor(date, "MSFT", fired=False, outcome_bps=0.0, trade_index=50 + i))

    surviving = _diagnose(anchors, floor_bps=1.0)
    killed = _diagnose(anchors, floor_bps=10_000.0)
    assert surviving["outcome"] == s2.OUTCOME_PROMISING
    assert killed["outcome"] == s2.OUTCOME_KILLED

    baseline = s2.continuous_report(anchors)
    for key in (
        "n_paired_touch_anchors", "n_usable_anchors", "n_undefined_anchors", "n_session_dates",
        "n_symbols", "price_extension_bps", "delta_weakening_multiple", "quadrants",
        "mechanism_raw_return_bps", "comparator_raw_return_bps", "descriptive_separation_bps",
        "boolean_variant",
    ):
        assert surviving[key] == baseline[key], f"{key} moved with the verdict"
        assert killed[key] == baseline[key], f"{key} moved with the verdict"


def test_the_quadrant_plane_and_the_screened_threshold_agree_on_the_same_anchors():
    """The continuous corner ``both`` and Scout's candidate cell must be the SAME anchors -- that
    is what makes the boolean a transform of the plane rather than a second measurement."""
    anchors = []
    for d in range(1, 7):
        date = f"2026-04-{d:02d}"
        for i in range(5):
            anchors.append(_anchor(date, "AAPL", fired=True, outcome_bps=-9.0, trade_index=i))
            anchors.append(_anchor(date, "MSFT", fired=False, outcome_bps=1.0, trade_index=50 + i))
    result = _diagnose(anchors)
    assert result["quadrants"]["both"] == result["scout"]["screen_result"]["n_candidate"]
    assert (
        result["quadrants"]["extension_only"]
        + result["quadrants"]["weakening_only"]
        + result["quadrants"]["neither"]
    ) == result["scout"]["screen_result"]["n_comparator"]


# =====================================================================================================
# The production wiring: ONE extraction feeds both halves
# =====================================================================================================


def test_the_anchors_sink_returns_exactly_what_the_screen_judged(tmp_path, monkeypatch):
    """``anchors_sink`` is what makes "no second extraction" true rather than merely intended."""
    from app.research.scout_ledger import ScoutLedger
    from app.research.datasets import DatasetStore

    calls = {"n": 0}
    real_extract = scout.extract_anchors

    def counting_extract(**kw):
        calls["n"] += 1
        return real_extract(**kw)

    monkeypatch.setattr(scout, "extract_anchors", counting_extract)

    fixture = [
        _anchor(f"2026-04-{d:02d}", "AAPL", fired=(i % 2 == 0), outcome_bps=-1.0, trade_index=i)
        for d in range(1, 5) for i in range(4)
    ]
    monkeypatch.setattr(scout, "extract_anchors", lambda **kw: (calls.__setitem__("n", calls["n"] + 1) or fixture))
    monkeypatch.setattr(scout, "_family_median_spread_bps", lambda *a, **k: 1.0)

    ledger = ScoutLedger(str(tmp_path / "scout"))
    store = DatasetStore(str(tmp_path / "datasets"))
    sink: list[dict] = []
    row = scout.register_and_screen_candidate(
        ledger=ledger, dataset_store=store, snapshots_dir=str(tmp_path / "snap"), config=None,
        feature_name="divergence_at_level_bearish", transform=_TRANSFORM, params=_PARAMS,
        structure_context_kind="band_touch", horizon_key=_HORIZON, corpus_manifest=[],
        sidedness=None, anchors_sink=sink,
    )
    assert calls["n"] == 1, "exactly ONE extraction"
    assert sink == fixture, "the sink carries precisely the anchors the screen judged"
    assert row["decision"] in scout.CLOSED_DECISIONS


def test_the_sink_defaults_off_and_changes_nothing(tmp_path, monkeypatch):
    """Every existing caller passes no sink and must be byte-identical."""
    from app.research.scout_ledger import ScoutLedger
    from app.research.datasets import DatasetStore

    fixture = [
        _anchor(f"2026-04-{d:02d}", "AAPL", fired=(i % 2 == 0), outcome_bps=-1.0, trade_index=i)
        for d in range(1, 5) for i in range(4)
    ]
    monkeypatch.setattr(scout, "extract_anchors", lambda **kw: fixture)
    monkeypatch.setattr(scout, "_family_median_spread_bps", lambda *a, **k: 1.0)

    def _run(sink):
        ledger = ScoutLedger(str(tmp_path / f"scout-{sink is not None}"))
        store = DatasetStore(str(tmp_path / f"datasets-{sink is not None}"))
        return scout.register_and_screen_candidate(
            ledger=ledger, dataset_store=store, snapshots_dir=str(tmp_path / "snap"), config=None,
            feature_name="divergence_at_level_bearish", transform=_TRANSFORM, params=_PARAMS,
            structure_context_kind="band_touch", horizon_key=_HORIZON, corpus_manifest=[],
            sidedness=None, registered_at="2026-05-01T00:00:00.000000Z",
            econ_floor_computed_at="2026-05-01T00:00:00.000000Z", anchors_sink=sink,
        )

    without = _run(None)
    with_sink = _run([])
    for key in ("spec_hash", "candidate_id", "family_id", "decision", "reason", "screen_result"):
        assert without[key] == with_sink[key], f"{key} moved when a sink was supplied"


def test_the_study2_pilot_spec_is_unchanged_and_is_the_one_this_run_uses():
    """No new threshold, no new variant, no grid sweep -- the already-frozen pilot request."""
    from app.research.datasets import DatasetStore
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        grid = scout.pilot_study_candidate_grid(DatasetStore(d))
    request = grid["delta_divergence_level_tests"]
    assert request["feature_name"] == "divergence_at_level_bearish"
    assert request["transform"] == "threshold"
    assert request["params"] == {"op": "ge", "value": 1.0}
    assert request["structure_context_kind"] == "band_touch"
    assert request["horizon_key"] == "trades_20"
    assert request["sidedness"] is None
    assert request["fitting_rule"] is None


def test_no_scout_frozen_constant_moved():
    """r14.3 reuses the decision rail; it must not have edged any part of it."""
    assert scout.SCOUT_MIN_SESSION_CLUSTERS == 2
    assert scout.SCOUT_MIN_OBSERVATIONS_PER_CELL == 5
    assert scout.SCOUT_BLOCK_PERMUTATIONS == 2_000
    assert scout.SCOUT_SCREEN_ALPHA == 0.05
    assert scout.SCOUT_MAX_TOP1_CONCENTRATION == 0.8
    assert scout.ECON_FLOOR_SPREAD_MULTIPLE == 1.0
    assert wf.WF_FOLD_MIN_OBSERVATIONS == 30, (
        "the walk-forward floor is untouched -- it simply no longer leaks into Scout discovery"
    )
