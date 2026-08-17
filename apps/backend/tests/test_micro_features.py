"""``micro_features.py`` (Era "The Rapid Microscope" J-02) -- hand-derived oracle fixtures for the
pure per-value arithmetic (TR-16 feature-level vectors), the closed outcome set (spec section 4,
TC-6/TR-17c), and the cross-basis unit gate (spec section 2.6, TC-7/TR-18).

Test-first contract: TC-6 through TC-10 in ``docs/phases/goal-rapid-microscope-iter-2.md``. The
STATEFUL streaming integration (cumulative delta, rolling windows, run length, the deferred
constructs) is exercised through a real ``TapeEngine`` + ``MicroObserver`` in
``test_micro_observer.py`` instead -- this file covers ONLY the stateless arithmetic each row's
computation ultimately calls into."""

from __future__ import annotations

import pytest

from app.research import micro_features as mf


# --- F-FLOW: rolling_imbalance / dominant_side_volume_share / volume_burst -----------------------


def test_rolling_imbalance_all_buy_is_one():
    assert mf.rolling_imbalance(10, 0) == 1.0


def test_rolling_imbalance_all_sell_is_minus_one():
    assert mf.rolling_imbalance(0, 10) == -1.0


def test_rolling_imbalance_balanced_is_zero():
    assert mf.rolling_imbalance(5, 5) == 0.0


def test_rolling_imbalance_no_directional_volume_is_none():
    assert mf.rolling_imbalance(0, 0) is None


def test_dominant_side_volume_share_hand_computed():
    assert mf.dominant_side_volume_share(30, 10) == pytest.approx(0.75)
    assert mf.dominant_side_volume_share(10, 30) == pytest.approx(0.75)


def test_dominant_side_volume_share_no_volume_is_zero_not_none():
    assert mf.dominant_side_volume_share(0, 0) == 0.0


def test_volume_burst_hand_computed():
    # baseline windows [100, 120, 90, 110, 105] -> median 105; window volume 210 -> 210/105 = 2.0
    assert mf.volume_burst(210, [100, 120, 90, 110, 105]) == pytest.approx(2.0)


def test_volume_burst_undefined_with_fewer_than_five_baseline_windows():
    assert mf.volume_burst(100, [100, 100, 100, 100]) is None  # 4 windows -- undefined, counted
    assert mf.volume_burst(100, []) is None


def test_volume_burst_undefined_with_zero_median_baseline():
    assert mf.volume_burst(100, [0, 0, 0, 0, 0]) is None


# --- F-FLOW: price_extreme_trailing / divergence_at_level (Card 9.1, amended r2) ------------------


def test_price_extreme_trailing_hand_computed():
    history = [(0.0, 100.0), (30.0, 100.5), (60.0, 101.0), (90.0, 100.8)]
    # tau=60, window [-60, 60] -> every point in range -> max = 101.0
    assert mf.price_extreme_trailing(history, tau=60.0) == pytest.approx(101.0)
    # tau=90, window [-30, 90] -> points at 30/60/90 in range (0.0 excluded) -> max = 101.0
    assert mf.price_extreme_trailing(history, tau=90.0) == pytest.approx(101.0)


def test_price_extreme_trailing_none_with_no_point_in_range():
    history = [(0.0, 100.0)]
    assert mf.price_extreme_trailing(history, tau=1000.0) is None


def test_divergence_delta_threshold_hand_computed():
    # median([1000, 1200, 900, 1100, 1000]) = 1000 -> 0.25 * 1000 = 250
    assert mf.divergence_delta_threshold([1000, 1200, 900, 1100, 1000]) == pytest.approx(250.0)


def test_divergence_at_level_bearish_when_price_higher_and_delta_collapses():
    history = [
        (0.0, 100.0), (30.0, 100.5), (60.0, 101.0),
        (90.0, 100.8), (150.0, 101.5), (200.0, 102.0),
    ]
    result = mf.divergence_at_level(
        price_history=history, tau1=60.0, tau2=200.0,
        cum_delta_at_tau1=500.0, cum_delta_at_tau2=100.0,
        baseline_volumes=[1000, 1200, 900, 1100, 1000],
    )
    assert result["price_extreme_tau1"] == pytest.approx(101.0)
    assert result["price_extreme_tau2"] == pytest.approx(102.0)
    assert result["delta_volume_fraction_threshold"] == pytest.approx(250.0)
    # price made a higher high (102.0 > 101.0) AND CD(200)=100 <= CD(60)-delta=500-250=250 -> True
    assert result["bearish_divergence"] is True
    assert result["available_at"] == 200.0


def test_divergence_at_level_false_when_delta_does_not_collapse_enough():
    history = [(0.0, 100.0), (60.0, 101.0), (200.0, 102.0)]
    result = mf.divergence_at_level(
        price_history=history, tau1=60.0, tau2=200.0,
        cum_delta_at_tau1=500.0, cum_delta_at_tau2=400.0,  # 400 > 250 -> condition fails
        baseline_volumes=[1000, 1200, 900, 1100, 1000],
    )
    assert result["bearish_divergence"] is False


def test_divergence_at_level_none_with_insufficient_baseline():
    history = [(0.0, 100.0), (60.0, 101.0), (200.0, 102.0)]
    result = mf.divergence_at_level(
        price_history=history, tau1=60.0, tau2=200.0,
        cum_delta_at_tau1=500.0, cum_delta_at_tau2=100.0,
        baseline_volumes=[1000, 1200],  # only 2 windows -- undefined
    )
    assert result["delta_volume_fraction_threshold"] is None
    assert result["bearish_divergence"] is None


# --- F-RESPONSE: failed_aggression_score / impact_efficiency ---------------------------------------


def test_failed_aggression_score_hand_computed():
    # dominant_share=0.8, |delta|=2.5bps of a 5.0bps scale -> flatness=1-2.5/5.0=0.5 -> 0.8*0.5=0.4
    assert mf.failed_aggression_score(0.8, 2.5) == pytest.approx(0.4)


def test_failed_aggression_score_clamps_flatness_at_zero_for_a_large_move():
    # |delta| = 10 bps > the 5.0 scale -> flatness clamps to 0.0 -> score 0.0 regardless of share
    assert mf.failed_aggression_score(0.9, 10.0) == 0.0


def test_failed_aggression_score_treats_no_measured_move_as_maximally_flat():
    assert mf.failed_aggression_score(0.6, None) == pytest.approx(0.6)


def test_impact_efficiency_hand_computed():
    # 4.0 bps over 2,000 aggressive shares -> 4.0 / (2000/1000) = 2.0 bps per 1,000 shares
    assert mf.impact_efficiency(4.0, 2000) == pytest.approx(2.0)


def test_impact_efficiency_none_with_zero_aggressive_volume():
    assert mf.impact_efficiency(4.0, 0) is None


def test_impact_efficiency_none_with_no_measured_move():
    assert mf.impact_efficiency(None, 2000) is None


# --- F-LIQUIDITY: quote_imbalance / microprice / mid_price / bps_move ------------------------------


def test_quote_imbalance_hand_computed():
    assert mf.quote_imbalance(bid_size=300, ask_size=100) == pytest.approx(0.5)
    assert mf.quote_imbalance(bid_size=100, ask_size=300) == pytest.approx(-0.5)


def test_quote_imbalance_none_with_zero_total_size():
    assert mf.quote_imbalance(0, 0) is None


def test_microprice_hand_computed():
    # bid=99.90 (size 300), ask=100.10 (size 100) -> (100.10*300 + 99.90*100) / 400
    expected = (100.10 * 300 + 99.90 * 100) / 400
    assert mf.microprice(bid=99.90, ask=100.10, bid_size=300, ask_size=100) == pytest.approx(expected)


def test_mid_price_and_bps_move_hand_computed():
    mid_start = mf.mid_price(99.98, 100.02)
    mid_end = mf.mid_price(100.08, 100.12)
    assert mid_start == pytest.approx(100.0)
    assert mid_end == pytest.approx(100.10)
    assert mf.bps_move(mid_start, mid_end) == pytest.approx(10.0)  # +0.10 on 100.0 = 10 bps


def test_bps_move_none_with_missing_side():
    assert mf.bps_move(None, 100.0) is None
    assert mf.bps_move(100.0, None) is None


# --- micro_parameters(): every constant embedded verbatim, moves when monkeypatched ----------------


def test_micro_parameters_embeds_every_constant_it_uses():
    params = mf.micro_parameters()
    assert params["refill_m_quotes"] == mf.REFILL_M_QUOTES
    assert params["response_k_trades"] == mf.RESPONSE_K_TRADES
    assert params["burst_baseline_trailing_windows"] == mf.BURST_BASELINE_TRAILING_WINDOWS
    assert params["depletion_window_quotes"] == mf.DEPLETION_WINDOW_QUOTES
    assert params["impact_flatness_scale_bps"] == mf.IMPACT_FLATNESS_SCALE_BPS
    assert params["divergence_trailing_seconds"] == mf.DIVERGENCE_TRAILING_SECONDS
    assert params["divergence_delta_volume_fraction"] == mf.DIVERGENCE_DELTA_VOLUME_FRACTION


def test_a_monkeypatched_constant_moves_the_parameters_hash(monkeypatch):
    """The counter-test the goal.md Constraints section demands: a changed constant must move
    BOTH the parameters dict AND its hash (never a stale hash over a changed formula)."""
    before_params = mf.micro_parameters()
    before_hash = mf.micro_parameters_hash()
    monkeypatch.setattr(mf, "REFILL_M_QUOTES", mf.REFILL_M_QUOTES + 1)
    after_params = mf.micro_parameters()
    after_hash = mf.micro_parameters_hash()
    assert after_params != before_params
    assert after_hash != before_hash


# --- the closed outcome set (spec section 4) --------------------------------------------------------


def test_resolve_outcome_start_is_the_max_of_conditioning_available_at():
    assert mf.resolve_outcome_start([10.0, 25.0, 5.0]) == 25.0


def test_resolve_outcome_start_requires_at_least_one_instant():
    with pytest.raises(ValueError):
        mf.resolve_outcome_start([])


def test_require_outcome_start_not_before_conditioning_passes_a_legal_start():
    assert mf.require_outcome_start_not_before_conditioning(30.0, [10.0, 25.0]) == 30.0
    assert mf.require_outcome_start_not_before_conditioning(25.0, [10.0, 25.0]) == 25.0  # equal is legal


def test_tc6_planted_outcome_before_conditioning_max_is_refused():
    """TC-6 / TR-17c: a planted outcome start earlier than the conditioning set's maximum
    available_at is refused with a typed error, never silently measured early."""
    with pytest.raises(mf.OutcomeRefused):
        mf.require_outcome_start_not_before_conditioning(20.0, [10.0, 25.0])  # 20 < 25 -- illegal


def test_mid_outcome_hand_computed_side_signed():
    buy = mf.mid_outcome(
        mid_at_start=100.0, mid_at_horizon=100.5, outcome_start=0.0, horizon_ts=30.0,
        session_end_ts=100.0, side="buy",
    )
    assert buy == {
        "basis": "mid", "outcome_start": 0.0, "horizon_ts": 30.0,
        "value": pytest.approx(0.5), "unmeasured": False, "truncated": False,
    }
    sell = mf.mid_outcome(
        mid_at_start=100.0, mid_at_horizon=100.5, outcome_start=0.0, horizon_ts=30.0,
        session_end_ts=100.0, side="sell",
    )
    assert sell["value"] == pytest.approx(-0.5)  # sell-signed: the same raw move flips sign


def test_mid_outcome_unmeasured_when_a_mid_is_missing():
    result = mf.mid_outcome(
        mid_at_start=None, mid_at_horizon=100.5, outcome_start=0.0, horizon_ts=30.0,
        session_end_ts=100.0, side=None,
    )
    assert result["unmeasured"] is True
    assert result["value"] is None


def test_mid_outcome_truncated_when_horizon_exceeds_session_end():
    result = mf.mid_outcome(
        mid_at_start=100.0, mid_at_horizon=100.5, outcome_start=0.0, horizon_ts=150.0,
        session_end_ts=100.0, side="buy",
    )
    assert result["truncated"] is True
    assert result["value"] is None  # excluded, never measured past the session


def test_last_trade_outcome_is_a_separately_named_basis_never_the_primary():
    result = mf.last_trade_outcome(
        price_at_start=50.0, price_at_horizon=50.25, outcome_start=0.0, horizon_ts=30.0,
        session_end_ts=100.0, side="buy",
    )
    assert result["basis"] == "last_trade"
    assert result["value"] == pytest.approx(0.25)


# --- J-03: the section 4 cost-proxy column, served BESIDE every outcome, never netted in -----------


def test_spread_bps_hand_computed():
    # 0.06 wide on a 149.0 mid -> (0.06 / 149.0) * 10_000.
    assert mf.spread_bps(0.06, 149.0) == pytest.approx(0.06 / 149.0 * 10_000.0)


def test_spread_bps_none_with_no_measured_spread_or_mid():
    assert mf.spread_bps(None, 149.0) is None
    assert mf.spread_bps(0.06, None) is None


def test_spread_bps_none_with_a_non_positive_mid():
    assert mf.spread_bps(0.06, 0.0) is None
    assert mf.spread_bps(0.06, -1.0) is None


# --- the section 2.6 cross-basis unit gate (TC-7 / TR-18) -------------------------------------------


def test_is_verified_unit():
    assert mf.is_verified_unit("shares") is True
    assert mf.is_verified_unit("round_lots") is True
    assert mf.is_verified_unit("unverified") is False


def test_tc7_unverified_unit_refuses_cross_basis_feature():
    with pytest.raises(mf.CrossBasisUnverifiedUnitError):
        mf.execution_vs_replenishment_ratio(executed_volume=100, replenished_size=50, quote_size_unit="unverified")


def test_tc7_verified_unit_serves_cross_basis_feature():
    value = mf.execution_vs_replenishment_ratio(executed_volume=100, replenished_size=50, quote_size_unit="shares")
    assert value == pytest.approx(2.0)
    value2 = mf.execution_vs_replenishment_ratio(executed_volume=100, replenished_size=50, quote_size_unit="round_lots")
    assert value2 == pytest.approx(2.0)


def test_execution_vs_replenishment_ratio_none_with_zero_replenishment():
    assert mf.execution_vs_replenishment_ratio(executed_volume=100, replenished_size=0, quote_size_unit="shares") is None


def test_tc7_pooled_request_spanning_unverified_and_verified_is_refused_outright():
    with pytest.raises(mf.CrossBasisUnverifiedUnitError):
        mf.require_uniform_unit_for_pool(["shares", "unverified"])


def test_tc7_pooled_request_of_a_single_unanimous_verified_unit_is_served():
    assert mf.require_uniform_unit_for_pool(["shares", "shares"]) == "shares"


def test_tc7_pooled_request_of_a_single_unanimous_but_unverified_unit_is_still_refused():
    with pytest.raises(mf.CrossBasisUnverifiedUnitError):
        mf.require_uniform_unit_for_pool(["unverified", "unverified"])


def test_require_share_denominated_magnitude_allowed_mirrors_the_ratio_gate():
    mf.require_share_denominated_magnitude_allowed("shares")  # does not raise
    with pytest.raises(mf.CrossBasisUnverifiedUnitError):
        mf.require_share_denominated_magnitude_allowed("unverified")


def test_tr18_source_scan_every_function_referencing_quote_size_unit_is_gated():
    """TR-18's source-scan requirement: no silent normalization path exists -- EVERY function
    body in this module that reads ``quote_size_unit`` (a parameter or local named exactly that)
    is either one of the gate functions themselves, or calls one of them before returning. An AST
    walk (not a plain substring grep) so a comment or docstring mentioning the name cannot hide a
    genuine violation, and a genuine violation cannot hide behind unusual formatting."""
    import ast
    import inspect

    gate_names = {"require_verified_unit", "require_uniform_unit_for_pool", "is_verified_unit"}
    tree = ast.parse(inspect.getsource(mf))

    def _calls_a_gate(node: ast.AST) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
                if name in gate_names:
                    return True
        return False

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name in gate_names:
            continue
        param_names = {a.arg for a in node.args.args}
        references_unit = "quote_size_unit" in param_names or any(
            isinstance(n, ast.Name) and n.id == "quote_size_unit" for n in ast.walk(node)
        )
        if references_unit and not _calls_a_gate(node):
            violations.append(node.name)
    assert violations == [], f"ungated quote_size_unit reference(s): {violations}"


def test_tr18_source_scan_every_streaming_emitter_of_a_share_denominated_magnitude_is_gated():
    """TR-18's source-scan requirement extended to the STREAMING layer -- the half the scan above
    structurally cannot see, since it walks only THIS module while the code that actually runs
    against the 18 real (all ``unverified``) datasets lives in ``micro_observer.py``. Rule: every
    function there that CONSTRUCTS a deferred completion whose ``kind`` is a cross-basis
    share-denominated one (``CROSS_BASIS_SHARE_DENOMINATED_KINDS``) must call a section 2.6 gate in
    its own body -- so a new emitter that attaches a raw magnitude ungated fails here rather than
    silently persisting a share-denominated number for an unverified dataset. Scoped to the
    EMITTERS (not to every reader of ``quote_size_unit``) deliberately: serving the unit as a row
    LABEL is not arithmetic over it, and a rule that flagged the label would have to be muzzled by
    an exemption list -- which is how a guard stops guarding."""
    import ast
    import inspect

    from app.research import micro_observer

    gate_names = {
        "require_verified_unit",
        "require_uniform_unit_for_pool",
        "require_share_denominated_magnitude_allowed",
        "is_verified_unit",
    }
    tree = ast.parse(inspect.getsource(micro_observer))

    def _emits_a_cross_basis_kind(node: ast.AST) -> bool:
        for child in ast.walk(node):
            if not isinstance(child, ast.Dict):
                continue
            for key, value in zip(child.keys, child.values):
                if (
                    isinstance(key, ast.Constant)
                    and key.value == "kind"
                    and isinstance(value, ast.Constant)
                    and value.value in mf.CROSS_BASIS_SHARE_DENOMINATED_KINDS
                ):
                    return True
        return False

    def _calls_a_gate(node: ast.AST) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
                if name in gate_names:
                    return True
        return False

    emitters: list[str] = []
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not _emits_a_cross_basis_kind(node):
            continue
        emitters.append(node.name)
        if not _calls_a_gate(node):
            violations.append(node.name)
    assert emitters, "no streaming emitter of a share-denominated magnitude found -- scan is vacuous"
    assert violations == [], f"ungated share-denominated magnitude emitter(s): {violations}"


# --- TC-10's own explicit ban: no iceberg / institutional-intent language anywhere ------------------


def test_no_banned_microstructure_claim_language_in_this_module():
    import inspect

    source = inspect.getsource(mf)
    lowered = source.lower()
    for banned in ("iceberg", "institutional", "spoof", "manipulat"):
        assert banned not in lowered, f"banned microstructure-claim language found: {banned!r}"
