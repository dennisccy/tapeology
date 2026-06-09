"""J-33 — relative spread / price-impact gates (price-impact-relative-to-price calibration).

The deterministic regression fixture reproduces the iter-12 failing case: a real ~$30–50 name
(the GME reference, 14-05-2024 ~14:30 London, a >10% drop in minutes) whose spread is WIDE in
absolute dollars (above the sim-tuned $0.06 cutoff) but NORMAL relative to its price, with a
strong NEGATIVE impact. Under the old absolute gates it was stuck on `unclear`; under the relative
gates it MUST resolve to `seller_control` (and the mirror rally to `buyer_control`).

The negative guards prove the anti-goals still hold in the relative domain:
  * a genuinely WIDE RELATIVE spread (many bps) ⇒ `unclear` (honest uncertainty);
  * high one-sided aggression with NO proportionate price progress + a refreshing quote ⇒
    absorption, never control (price impact over raw aggression);
  * the absorption gates remain the EXACT complement of the control impact-return condition.

Re-derived from code (the iter-5 keystone lesson): every fixture asserts the classifier's own
output, not a screenshot.
"""

import pytest

from app.config import CONFIG
from app.engine.classifier import (
    STATE_ASK_ABSORPTION,
    STATE_BID_ABSORPTION,
    STATE_BUYER_CONTROL,
    STATE_SELLER_CONTROL,
    STATE_UNCLEAR,
    TapeStateClassifier,
)

clf = TapeStateClassifier(CONFIG)

# The ~$30–50 reference price level (GME on the reference day). A $0.10 spread here is WIDE in
# absolute dollars (> the sim-tuned $0.06 max_stable_spread) but NORMAL relative to ~$40
# (0.10/40*1e4 = 25 bps, under max_stable_spread_bps=30). This is exactly the shape the old
# absolute gate forced to `unclear`.
REF_PRICE = 40.0
WIDE_ABS_NORMAL_REL_SPREAD = 0.10  # > absolute $0.06 cutoff, but only ~25 bps of $40


def _real_features(**overrides) -> dict[str, float]:
    """A warmed real-name feature shape carrying the canonical ``reference_price`` basis (J-33)."""
    base = {
        "trade_speed": 2.0,
        "volume_speed": 400.0,
        "aggressive_buy_ratio": 0.10,
        "aggressive_sell_ratio": 0.90,
        "net_aggressive_volume": -800.0,
        # Strong NEGATIVE impact: a >10% move over the window is dollars-large at $40, and a clear
        # negative RETURN (well past max_sell_price_impact_return). buy_impact is ~flat.
        "buy_price_impact": 0.01,
        "sell_price_impact": -2.0,
        "average_spread": WIDE_ABS_NORMAL_REL_SPREAD,
        "large_print_count": 2.0,
        "absorption_score": 0.0,
        "bid_refresh_score": 0.0,
        "ask_refresh_score": 0.0,
        "reference_price": REF_PRICE,
    }
    base.update(overrides)
    return base


def test_old_absolute_gate_would_have_blocked_this_spread():
    # Documents WHY this case needed J-33: the wide-absolute spread fails the OLD absolute gate
    # ($0.10 > $0.06) — the deterministic cause of the perpetual `unclear` the relative gate fixes.
    assert WIDE_ABS_NORMAL_REL_SPREAD > CONFIG.max_stable_spread
    # ...yet it is NORMAL relative to the price (under the bps cutoff), so the relative gate admits it.
    rel_bps = WIDE_ABS_NORMAL_REL_SPREAD / REF_PRICE * 10000.0
    assert rel_bps <= CONFIG.max_stable_spread_bps


def test_real_directional_drop_resolves_to_seller_control_not_unclear():
    # THE J-33 REGRESSION FIXTURE: warmed, high sell ratio, strong negative RELATIVE impact, spread
    # wide in absolute $ but normal relative to price ⇒ seller_control (NOT a perpetual unclear).
    result = clf.classify(_real_features(), trade_count=60)
    assert result.state == STATE_SELLER_CONTROL
    assert result.state != STATE_UNCLEAR
    assert result.confidence >= CONFIG.reasonable_confidence


def test_real_directional_rally_resolves_to_buyer_control():
    # The mirror: a comparable RALLY on a real ~$40 name ⇒ buyer_control.
    rally = _real_features(
        aggressive_buy_ratio=0.90,
        aggressive_sell_ratio=0.10,
        buy_price_impact=2.0,     # strong positive return at $40
        sell_price_impact=-0.01,  # ~flat
        net_aggressive_volume=800.0,
    )
    result = clf.classify(rally, trade_count=60)
    assert result.state == STATE_BUYER_CONTROL
    assert result.confidence >= CONFIG.reasonable_confidence


# --- Negative guards: the anti-goals still hold in the relative domain -----------------------


def test_wide_relative_spread_still_reads_unclear():
    # A genuinely WIDE RELATIVE spread (here $1.00 on $40 = 250 bps, far over the 30-bps cutoff)
    # blocks control even with strong negative impact ⇒ honest unclear (honest-uncertainty holds).
    wide_rel = _real_features(average_spread=1.0)  # 250 bps of $40
    assert wide_rel["average_spread"] / REF_PRICE * 10000.0 > CONFIG.max_stable_spread_bps
    result = clf.classify(wide_rel, trade_count=60)
    assert result.state == STATE_UNCLEAR
    assert result.state != STATE_SELLER_CONTROL


def test_high_sell_aggression_no_proportionate_progress_is_absorption_not_control():
    # High sell aggression but NO proportionate price progress (flat RELATIVE impact) + a refreshing
    # bid ⇒ bid_absorption, never seller_control (price-impact-over-aggression holds in the relative
    # domain). The impact is flat as a RETURN even at the real price level.
    absorbed = _real_features(
        sell_price_impact=0.0,    # flat — no real drop as a return
        bid_refresh_score=1.0,    # the bid held / refreshed under selling
        absorption_score=0.90,
    )
    result = clf.classify(absorbed, trade_count=60)
    assert result.state == STATE_BID_ABSORPTION
    assert result.state != STATE_SELLER_CONTROL
    assert result.confidence >= CONFIG.reasonable_confidence


def test_absorption_gate_is_exact_complement_of_control_impact_in_relative_domain():
    # KEYSTONE: identical high sell aggression on a real name resolves to seller_control when the
    # RELATIVE impact is past the cutoff, and to bid_absorption (with refresh) when it is flat —
    # never both, never a silent unclear. Proven on the SAME reference shape at the boundary.
    refreshing = _real_features(bid_refresh_score=1.0, absorption_score=0.90)

    real_drop = clf.classify({**refreshing, "sell_price_impact": -2.0}, trade_count=60)
    flat = clf.classify({**refreshing, "sell_price_impact": 0.0}, trade_count=60)
    assert real_drop.state == STATE_SELLER_CONTROL
    assert flat.state == STATE_BID_ABSORPTION


def test_ask_absorption_mirror_on_real_name():
    # The buy/ask mirror at the real price level: high buy aggression, flat relative impact, a
    # refreshing ask ⇒ ask_absorption, not buyer_control.
    absorbed = _real_features(
        aggressive_buy_ratio=0.90,
        aggressive_sell_ratio=0.10,
        buy_price_impact=0.0,     # flat as a return
        sell_price_impact=-0.01,
        ask_refresh_score=1.0,
        absorption_score=0.90,
        net_aggressive_volume=800.0,
    )
    result = clf.classify(absorbed, trade_count=60)
    assert result.state == STATE_ASK_ABSORPTION
    assert result.state != STATE_BUYER_CONTROL


def test_no_reference_price_falls_back_to_absolute_path_unchanged():
    # When no reference_price basis is present (legacy fixtures / a cold-empty window), the gates
    # fall back to the ABSOLUTE constants — byte-identical to pre-J-33. The classic ~$100 buyer
    # shape (spread $0.02, impact $0.40) still resolves buyer_control at the pinned confidence.
    legacy = {
        "trade_speed": 2.0,
        "volume_speed": 400.0,
        "aggressive_buy_ratio": 0.90,
        "aggressive_sell_ratio": 0.10,
        "net_aggressive_volume": 800.0,
        "buy_price_impact": 0.40,
        "sell_price_impact": -0.01,
        "average_spread": 0.02,
        "large_print_count": 2.0,
        "absorption_score": 0.0,
        "bid_refresh_score": 0.0,
        "ask_refresh_score": 0.0,
        # no reference_price key at all
    }
    result = clf.classify(legacy, trade_count=60)
    assert result.state == STATE_BUYER_CONTROL
    assert result.confidence == pytest.approx(0.8542, abs=1e-3)


# --- J-36: spread is a GRADED factor (override), not an absolute veto -------------------------
#
# The directional override admits a CLEARLY-directional move with a wide-but-in-band quoted spread
# (the single-venue / SIP fast-mover / momentarily-halted case), while a spread BEYOND the band
# still vetoes control (honest uncertainty for genuinely illiquid tape). The override is config-
# gated so the pre-override fixtures stay byte-identical when disabled (the keystone switch).

import dataclasses

from app.engine.classifier import Classification  # noqa: E402

# A spread wide in absolute $ AND moderately wide relative to ~$40 (just over the 30-bps cap), but
# INSIDE the override band (≤ override_max_spread_multiple × cap = 120 bps). This is the real-SIP
# GME-drop shape: a clear >5% directional drop whose SIP quote read ~40–55 bps during the cascade.
IN_BAND_WIDE_SPREAD = 0.20  # 50 bps of $40 — over the 30-bps cap, under the 120-bps band edge


def _bps(spread: float) -> float:
    return spread / REF_PRICE * 10000.0


def test_in_band_wide_spread_directional_drop_resolves_to_seller_control():
    # A clearly-directional drop (high sell ratio + strong negative relative impact + speed) with a
    # wide-but-in-band quoted spread resolves to seller_control via the override — NOT a perpetual
    # `unclear`. This is exactly the J-36 real-GME-on-SIP case (spread over the cap, move obvious).
    assert CONFIG.max_stable_spread_bps < _bps(IN_BAND_WIDE_SPREAD)  # over the stable cap...
    assert _bps(IN_BAND_WIDE_SPREAD) <= CONFIG.max_stable_spread_bps * CONFIG.override_max_spread_multiple  # ...but in band
    result = clf.classify(_real_features(average_spread=IN_BAND_WIDE_SPREAD), trade_count=60)
    assert result.state == STATE_SELLER_CONTROL
    assert result.confidence >= CONFIG.reasonable_confidence


def test_in_band_wide_spread_directional_rally_resolves_to_buyer_control():
    # The mirror: a clearly-directional RALLY with an in-band wide spread ⇒ buyer_control.
    rally = _real_features(
        aggressive_buy_ratio=0.90,
        aggressive_sell_ratio=0.10,
        buy_price_impact=2.0,
        sell_price_impact=-0.01,
        net_aggressive_volume=800.0,
        average_spread=IN_BAND_WIDE_SPREAD,
    )
    result = clf.classify(rally, trade_count=60)
    assert result.state == STATE_BUYER_CONTROL
    assert result.confidence >= CONFIG.reasonable_confidence


def test_spread_beyond_the_band_still_vetoes_control_honest_uncertainty():
    # A spread BEYOND the override band (here $1.00 on $40 = 250 bps ≈ 8× the cap) still reads
    # `unclear` even with a strong directional impact — the artifact-vs-illiquid boundary holds, so
    # genuinely illiquid / mixed tape is never forced to a directional call (honest-uncertainty).
    beyond = _real_features(average_spread=1.0)
    assert _bps(1.0) > CONFIG.max_stable_spread_bps * CONFIG.override_max_spread_multiple
    result = clf.classify(beyond, trade_count=60)
    assert result.state == STATE_UNCLEAR
    assert result.state != STATE_SELLER_CONTROL


def test_override_grades_spread_into_confidence_monotonically():
    # Within the band, a WIDER spread LOWERS confidence (graded, honest) — never asserting false
    # certainty — while still resolving to control. A near-cap spread is more confident than a
    # near-band-edge spread on the same otherwise-identical clearly-directional drop.
    near_cap = clf.classify(_real_features(average_spread=0.13), trade_count=60)   # ~32 bps
    near_edge = clf.classify(_real_features(average_spread=0.45), trade_count=60)  # ~112 bps
    assert near_cap.state == STATE_SELLER_CONTROL
    assert near_edge.state == STATE_SELLER_CONTROL
    assert near_cap.confidence > near_edge.confidence  # wider in-band spread => lower confidence


def test_override_does_not_force_a_call_on_weak_evidence():
    # The override is ADDITIVE: with the spread wide-but-in-band but the RATIO weak (mixed tape), the
    # directional predicate fails, so the read stays `unclear` — the override never manufactures a
    # call on weak evidence (price-impact / honest-uncertainty anti-goals hold).
    weak = _real_features(
        aggressive_sell_ratio=0.55,  # below the 0.60 floor — mixed
        aggressive_buy_ratio=0.45,
        average_spread=IN_BAND_WIDE_SPREAD,
    )
    result = clf.classify(weak, trade_count=60)
    assert result.state == STATE_UNCLEAR


def test_override_disabled_is_byte_identical_to_a_hard_spread_veto():
    # KEYSTONE SWITCH: with the override DISABLED the spread is a hard veto again, so the in-band
    # wide-spread drop that resolves to seller_control WITH the override falls back to `unclear`
    # WITHOUT it — proving the override is the ONLY thing admitting the wide-spread case and the
    # pre-override behavior is recoverable exactly (the absolute-fallback fixtures stay pinned).
    cfg_off = dataclasses.replace(CONFIG, directional_override_enabled=False)
    clf_off = TapeStateClassifier(cfg_off)
    drop = _real_features(average_spread=IN_BAND_WIDE_SPREAD)
    assert clf.classify(drop, trade_count=60).state == STATE_SELLER_CONTROL      # override ON
    assert clf_off.classify(drop, trade_count=60).state == STATE_UNCLEAR         # override OFF
    # A NARROW-spread drop is unaffected by the switch (the override only changes the wide case).
    narrow = _real_features(average_spread=0.02)  # 5 bps
    on = clf.classify(narrow, trade_count=60)
    off = clf_off.classify(narrow, trade_count=60)
    assert on.state == off.state == STATE_SELLER_CONTROL
    assert on.confidence == pytest.approx(off.confidence, abs=1e-9)  # identical narrow confidence


def test_absorption_keystone_holds_under_wide_in_band_spread():
    # KEYSTONE under the override: at an in-band wide spread, identical high sell aggression resolves
    # to seller_control when the relative impact is past the cutoff and to bid_absorption (with
    # refresh + a NARROW spread) when it is flat — the override never lets absorption masquerade as
    # control. Absorption keeps the spread term (its gate is unchanged), so a wide-spread flat-impact
    # tape stays `unclear` (no fabricated absorption), while a clean drop is control.
    real_drop = clf.classify(
        _real_features(average_spread=IN_BAND_WIDE_SPREAD, sell_price_impact=-2.0), trade_count=60
    )
    assert real_drop.state == STATE_SELLER_CONTROL
    # Flat impact + refresh at a NORMAL spread ⇒ bid_absorption (the complement), proving the two are
    # mutually exclusive on the impact condition regardless of the override.
    absorbed = clf.classify(
        _real_features(sell_price_impact=0.0, bid_refresh_score=1.0, absorption_score=0.9),
        trade_count=60,
    )
    assert absorbed.state == STATE_BID_ABSORPTION
