"""``micro_features.py`` -- Era "The Rapid Microscope" J-02: the Wave-1 feature FAMILIES

(``docs/rapid-validation-spec.md`` section 3) plus the closed outcome set (section 4) and the
section 2.6 cross-basis unit gate. Every value here is a PURE function of its explicit inputs --
no state, no I/O, no wall-clock, no randomness -- so the same inputs reproduce byte-identical
outputs (the determinism anti-goal) and every family has a hand-derived oracle fixture
(``tests/test_micro_features.py``, TR-16 feature-level vectors).

**This module owns the constants table (spec section 1), narrowed to exactly what J-02 consumes.**
The remaining rows of that table (``SCOUT_*``, ``WF_*`` beyond what ``micro_readiness.py`` already
transcribed, ``VAULT_*``, ``TRANCHE_MINIMUMS``, ``KILL_REASONS``, ``ALPACA_QUOTE_SIZE_UNIT_
EFFECTIVE``, ``MICRO_HORIZON_*``) belong to the modules that actually read them (``scout.py``,
``walkforward.py``, ``vault.py``, ``tick_recorder.py`` -- J-04 through J-06) and are deliberately
NOT pre-declared here: minting an unused constant now would risk a second, independently-valued
copy the day those modules land (the exact anti-pattern ``micro_readiness.py``'s own docstring
warns against for ``WF_TRAIN_MIN_SESSIONS``/``WF_TEST_MIN_SESSIONS``). Every constant below is
frozen verbatim from the spec table -- arbitrary-but-fixed, chosen before any outcome was read; a
change to any of them is a NAMED REVISION, never a tuning act.

**Statelessness is the point.** The STREAMING state machine that turns one ordered event stream
into rows (rolling buffers, deferred-construct pending queues, the prefix law itself) lives in
``micro_observer.py`` -- this module supplies the pure arithmetic that state machine calls into,
so every formula is independently testable against a hand-computed fixture without replaying a
single event.

**Reuse, never recompute (spec section 2.5).** Nothing here re-derives the aggressor side, the
five engine window features, tape state, or bid/ask/spread/last -- those are read verbatim off the
``EngineSnapshot`` by the observer and threaded through untouched. This module computes ONLY the
additive research quantities the engine does not already produce.
"""

from __future__ import annotations

import hashlib
import json
import statistics
from typing import Sequence

__all__ = [
    "MICRO_SEED",
    "MICRO_ALGO_VERSION",
    "MICRO_FEATURE_WINDOW_TRADES",
    "MICRO_FEATURE_WINDOW_SHARES",
    "REFILL_M_QUOTES",
    "RESPONSE_K_TRADES",
    "BURST_BASELINE_TRAILING_WINDOWS",
    "DEPLETION_WINDOW_QUOTES",
    "IMPACT_FLATNESS_SCALE_BPS",
    "DIVERGENCE_TRAILING_SECONDS",
    "DIVERGENCE_DELTA_VOLUME_FRACTION",
    "QUOTE_SIZE_UNITS",
    "CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT",
    "CROSS_BASIS_SHARE_DENOMINATED_KINDS",
    "SIDE_SOURCE_QUOTE_RULE",
    "SIDE_SOURCE_TICK_TEST",
    "SIDE_SOURCE_CARRIED",
    "SIDE_SOURCE_UNKNOWN",
    "micro_parameters",
    "micro_parameters_hash",
    "dominant_side_volume_share",
    "failed_aggression_score",
    "rolling_imbalance",
    "quote_imbalance",
    "microprice",
    "mid_price",
    "bps_move",
    "price_extreme_trailing",
    "divergence_delta_threshold",
    "divergence_at_level",
    "DIVERGENCE_CONTINUOUS_EQUIVALENCE",
    "OutcomeRefused",
    "resolve_outcome_start",
    "require_outcome_start_not_before_conditioning",
    "BPS_UNIT",
    "OUTCOME_UNIT",
    "AGGRESSOR_SIDES",
    "CANDIDATE_DIRECTIONS",
    "UnknownSideVocabularyError",
    "UnitMismatchError",
    "aggressor_sign",
    "direction_sign",
    "direction_for_aggressor",
    "require_bps_floor",
    "require_return_bps_effect",
    "validate_candidate_direction",
    "clears_economic_floor",
    "mid_outcome",
    "last_trade_outcome",
    "spread_bps",
    "CrossBasisUnverifiedUnitError",
    "is_verified_unit",
    "require_verified_unit",
    "require_uniform_unit_for_pool",
    "require_share_denominated_magnitude_allowed",
    "execution_vs_replenishment_ratio",
]

# --- Pre-registered constants (docs/rapid-validation-spec.md section 1 -- transcribed verbatim,
# narrowed to J-02's own consumption; see module docstring). --------------------------------------

MICRO_SEED = 314159
MICRO_ALGO_VERSION = 1

MICRO_FEATURE_WINDOW_TRADES: tuple[int, ...] = (20, 100)
MICRO_FEATURE_WINDOW_SHARES: tuple[int, ...] = (5_000, 50_000)
REFILL_M_QUOTES = 20
RESPONSE_K_TRADES = 20
BURST_BASELINE_TRAILING_WINDOWS = 20
DEPLETION_WINDOW_QUOTES = 20
IMPACT_FLATNESS_SCALE_BPS = 5.0
DIVERGENCE_TRAILING_SECONDS = 120.0
DIVERGENCE_DELTA_VOLUME_FRACTION = 0.25

QUOTE_SIZE_UNITS: tuple[str, ...] = ("shares", "round_lots", "unverified")

# The closed refusal vocabulary of the section 2.6 gate. A STREAMING caller (``micro_observer.py``)
# cannot let ``CrossBasisUnverifiedUnitError`` escape -- aborting a whole replay because one
# dataset's unit basis is unverified would refuse the unit-INVARIANT features too -- so it records
# this token on the affected value instead: same refusal, same fail-closed meaning, expressed as
# persisted data rather than as an exception. Kept short deliberately: it lands on every refused
# row of a multi-GB snapshot corpus.
CROSS_BASIS_REFUSAL_UNVERIFIED_UNIT = "cross_basis_unverified_quote_size_unit"

# The deferred-construct kinds whose VALUE is a raw share-denominated cross-basis magnitude (spec
# section 3: "as is any share-denominated depletion/replenishment magnitude") -- each one refused
# unless its dataset's ``quote_size_unit`` is verified. The closed list the TR-18 guards sweep.
CROSS_BASIS_SHARE_DENOMINATED_KINDS: tuple[str, ...] = ("quote_depletion",)

# The side_source vocabulary (spec section 2.5) -- the ONLY four values that may ever appear.
SIDE_SOURCE_QUOTE_RULE = "quote_rule"
SIDE_SOURCE_TICK_TEST = "tick_test"
SIDE_SOURCE_CARRIED = "carried"
SIDE_SOURCE_UNKNOWN = "unknown"


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding this module hashes -- the identical ``datasets.py``
    ``_canonical`` shape (sorted keys, no whitespace), duplicated here (not imported) because it
    is a generic 1-line utility, not a second implementation of any measurement rail."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def micro_parameters() -> dict:
    """Every module constant a persisted feature value actually depends on, embedded VERBATIM
    (the desk ``playbook_parameters()`` pattern) -- keyed on its hash by every persisted snapshot
    record. A monkeypatched constant must move BOTH this dict's hash AND the depending result's
    own identity (counter-tested in ``tests/test_micro_features.py``)."""
    return {
        "micro_seed": MICRO_SEED,
        "micro_feature_window_trades": list(MICRO_FEATURE_WINDOW_TRADES),
        "micro_feature_window_shares": list(MICRO_FEATURE_WINDOW_SHARES),
        "refill_m_quotes": REFILL_M_QUOTES,
        "response_k_trades": RESPONSE_K_TRADES,
        "burst_baseline_trailing_windows": BURST_BASELINE_TRAILING_WINDOWS,
        "depletion_window_quotes": DEPLETION_WINDOW_QUOTES,
        "impact_flatness_scale_bps": IMPACT_FLATNESS_SCALE_BPS,
        "divergence_trailing_seconds": DIVERGENCE_TRAILING_SECONDS,
        "divergence_delta_volume_fraction": DIVERGENCE_DELTA_VOLUME_FRACTION,
    }


def micro_parameters_hash() -> str:
    """sha256 of ``micro_parameters()``'s canonical encoding -- one component of the snapshot
    identity tuple (``micro_snapshots.py``, spec section 2.3)."""
    return _sha256(_canonical(micro_parameters()))


# --- F-FLOW ------------------------------------------------------------------------------------


def rolling_imbalance(buy_volume: float, sell_volume: float) -> float | None:
    """``(buy - sell) / (buy + sell)`` over whatever window the caller already accumulated;
    ``None`` (undefined, never a fabricated 0.0) when the window carries no directional volume."""
    directional = buy_volume + sell_volume
    if directional <= 0:
        return None
    return (buy_volume - sell_volume) / directional


def dominant_side_volume_share(buy_volume: float, sell_volume: float) -> float:
    """``max(buy, sell) / directional`` -- ``0.0`` when neither side has traded (spec section 3's
    own stated default), never ``None`` (this one feeds a continuous score, not a ratio display)."""
    directional = buy_volume + sell_volume
    if directional <= 0:
        return 0.0
    return max(buy_volume, sell_volume) / directional


def volume_burst(window_volume: float, baseline_window_volumes: Sequence[float]) -> float | None:
    """``window_volume`` (the trailing feature-window's own volume) divided by the median of the
    prior ``BURST_BASELINE_TRAILING_WINDOWS`` non-overlapping same-length baseline windows.
    ``None`` (undefined, COUNTED never guessed) with fewer than 5 baseline windows (spec section
    3) or a zero median (a burst ratio against zero volume is not a meaningful multiple)."""
    if len(baseline_window_volumes) < 5:
        return None
    baseline = statistics.median(baseline_window_volumes)
    if baseline <= 0:
        return None
    return window_volume / baseline


def mid_price(bid: float | None, ask: float | None) -> float | None:
    if bid is None or ask is None:
        return None
    return (bid + ask) / 2.0


def bps_move(mid_start: float | None, mid_end: float | None) -> float | None:
    """Signed move from ``mid_start`` to ``mid_end`` in basis points of ``mid_start``. ``None``
    when either side is unmeasured or the starting mid is non-positive (no basis to express a
    bps move against)."""
    if mid_start is None or mid_end is None or mid_start <= 0:
        return None
    return (mid_end - mid_start) / mid_start * 10_000.0


def price_extreme_trailing(
    price_history: Sequence[tuple[float, float]], tau: float, window_seconds: float = DIVERGENCE_TRAILING_SECONDS
) -> float | None:
    """The max mid over the TRAILING ``[tau - window_seconds, tau]`` window, AS-OF ``tau`` (never
    a later value) -- spec section 3's ``price_extreme(tau)`` for the divergence-at-level formula.
    Max (never min): "bearish divergence" pairs a HIGHER price high against a weaker cumulative
    delta -- a named interpretation call (a higher price extreme is the one meaningful basis for a
    *bearish* reading; the spec's "max/min" phrasing does not otherwise disambiguate), logged in
    the dev handoff. ``price_history`` is an ascending ``(ts, mid)`` sequence; ``None`` with no
    point in range (undefined, never fabricated)."""
    lo = tau - window_seconds
    values = [mid for ts, mid in price_history if lo <= ts <= tau]
    if not values:
        return None
    return max(values)


def divergence_delta_threshold(baseline_volumes: Sequence[float]) -> float | None:
    """``delta = DIVERGENCE_DELTA_VOLUME_FRACTION x median(trailing-120s session-prefix baseline
    volumes)`` (spec section 3, Card 9.1's fraction) -- "the SAME session-prefix baseline windows"
    ``volume_burst`` draws from, so the identical ``BURST_BASELINE_TRAILING_WINDOWS``-derived floor
    applies: fewer than 5 windows is undefined (counted), never a thin-sample guess."""
    if len(baseline_volumes) < 5:
        return None
    return DIVERGENCE_DELTA_VOLUME_FRACTION * statistics.median(baseline_volumes)


def divergence_at_level(
    *,
    price_history: Sequence[tuple[float, float]],
    tau1: float,
    tau2: float,
    cum_delta_at_tau1: float,
    cum_delta_at_tau2: float,
    baseline_volumes: Sequence[float],
) -> dict:
    """Divergence-at-level (Card 9.1, amended r2): bearish divergence iff
    ``price_extreme(tau2) > price_extreme(tau1)`` AND ``CD(tau2) <= CD(tau1) - delta``, at
    consecutive touches ``tau1 < tau2`` of the same recorded band. Pure and oracle-testable: the
    caller (a future ``micro_join.py``, J-03 -- out of scope this iteration, since no band-touch
    join exists yet) supplies the two cumulative-delta readings and the trailing price history
    directly; this function performs no lookup of its own. ``available_at = tau2`` (the later
    touch fixes when the comparison could first be made).

    **r14.2 -- the continuous representation, added alongside (never in place of) the boolean.**
    goal.md requires continuous mechanism-defined representations first and threshold variants
    second. This returns Card 9.1's own two conjuncts as two independent, mechanism-preserving
    coordinates -- ``price_extension_bps`` (how much further price extended, in bps of the earlier
    extreme) and ``delta_weakening_multiple`` (how many threshold-widths of cumulative delta were
    given up) -- and ``bearish_divergence`` is then exactly the predeclared corner
    ``price_extension_bps > 0 and delta_weakening_multiple >= 1``. No weighted composite, no
    z-score, no fitted weights, no new threshold: the axes are the mechanism, and the boolean is
    one transform of them. Card 9.1's semantics are unchanged -- every input that produced ``True``
    before produces ``True`` now. See ``DIVERGENCE_CONTINUOUS_EQUIVALENCE`` for the algebra and for
    the single disclosed domain asymmetry (``delta == 0``)."""
    price_extreme_tau1 = price_extreme_trailing(price_history, tau1)
    price_extreme_tau2 = price_extreme_trailing(price_history, tau2)
    delta = divergence_delta_threshold(baseline_volumes)
    bearish: bool | None
    if price_extreme_tau1 is None or price_extreme_tau2 is None or delta is None:
        bearish = None
    else:
        bearish = (price_extreme_tau2 > price_extreme_tau1) and (
            cum_delta_at_tau2 <= cum_delta_at_tau1 - delta
        )

    # --- r14.2: the CONTINUOUS mechanism-defined coordinates (goal.md's "continuous
    # mechanism-defined representations first; threshold variants second"). Two axes, each one of
    # Card 9.1's own two conjuncts measured on its own scale -- never a weighted composite, a
    # z-score, or a fitted blend, all of which would introduce a free parameter this era has not
    # predeclared and could not falsify.
    #
    # Axis 1: how much FURTHER price extended at the later touch, in basis points of the earlier
    # extreme. Undefined without a positive basis to divide by.
    if (
        price_extreme_tau1 is None
        or price_extreme_tau2 is None
        or price_extreme_tau1 <= 0
    ):
        price_extension_bps = None
    else:
        price_extension_bps = (
            (price_extreme_tau2 - price_extreme_tau1) / price_extreme_tau1 * 10_000.0
        )

    # Axis 2: how many THRESHOLD-WIDTHS of cumulative delta were given up between the touches. The
    # threshold is the unit, so 1.0 is exactly Card 9.1's own bar and the axis is dimensionless.
    # `delta` is None on a thin baseline (<5 windows) and can legitimately be 0.0 when the median
    # baseline volume is zero -- neither is a positive measured denominator, so both read None
    # rather than infinity or a divide-by-zero.
    if delta is None or delta <= 0:
        delta_weakening_multiple = None
    else:
        delta_weakening_multiple = (cum_delta_at_tau1 - cum_delta_at_tau2) / delta

    return {
        "tau1": tau1,
        "tau2": tau2,
        "price_extreme_tau1": price_extreme_tau1,
        "price_extreme_tau2": price_extreme_tau2,
        "cum_delta_tau1": cum_delta_at_tau1,
        "cum_delta_tau2": cum_delta_at_tau2,
        "delta_volume_fraction_threshold": delta,
        # The continuous representation (r14.2). The boolean below is one predeclared threshold
        # transform OF these two coordinates, not an independent measurement:
        #   bearish_divergence  <=>  price_extension_bps > 0 AND delta_weakening_multiple >= 1
        # exactly, whenever both coordinates are defined (see `DIVERGENCE_CONTINUOUS_EQUIVALENCE`).
        "price_extension_bps": price_extension_bps,
        "delta_weakening_multiple": delta_weakening_multiple,
        "bearish_divergence": bearish,
        "available_at": tau2,
    }


#: r14.2 -- the exact, hand-checkable algebra tying Card 9.1's boolean to the continuous axes above,
#: recorded next to the code that must keep satisfying it.
#:
#:   price_extension_bps > 0
#:     <=> (p2 - p1)/p1 * 10000 > 0        [p1 > 0, so the divisor is sign-preserving]
#:     <=> p2 > p1                          [Card 9.1's price conjunct, exactly]
#:
#:   delta_weakening_multiple >= 1
#:     <=> (cd1 - cd2)/delta >= 1           [delta > 0, so the inequality direction is preserved]
#:     <=> cd1 - cd2 >= delta
#:     <=> cd2 <= cd1 - delta               [Card 9.1's delta conjunct, exactly]
#:
#: **The one disclosed asymmetry.** When `delta == 0.0` (>=5 baseline windows whose median volume is
#: zero -- thin tape, not a bug) the BOOLEAN is still defined and reduces to `cd2 <= cd1`, while the
#: continuous multiple is undefined (no positive unit to express weakening in). Card 9.1's semantics
#: are frozen and are NOT changed here; the equivalence is therefore stated over the domain where
#: both coordinates are defined, and a consumer of the continuous representation drops those anchors
#: honestly rather than imputing a value for them.
DIVERGENCE_CONTINUOUS_EQUIVALENCE = (
    "bearish_divergence <=> price_extension_bps > 0 and delta_weakening_multiple >= 1 "
    "(over anchors where both coordinates are defined)"
)


# --- F-RESPONSE ----------------------------------------------------------------------------------


def failed_aggression_score(dominant_share: float, delta_mid_bps: float | None) -> float:
    """``dominant_side_volume_share x clamp(1 - |delta_mid_bps| / IMPACT_FLATNESS_SCALE_BPS, 0, 1)``
    (spec section 3, the continuous complement to the engine's own gated ``absorption_score``).
    A ``None`` price move (no quote basis) reads as maximal flatness (1.0) -- consistent with the
    engine's own ``absorption_score``, which also treats "no measured impact" as flat, never as
    undefined."""
    if delta_mid_bps is None:
        flatness = 1.0
    else:
        flatness = max(0.0, min(1.0, 1.0 - abs(delta_mid_bps) / IMPACT_FLATNESS_SCALE_BPS))
    return dominant_share * flatness


def impact_efficiency(delta_mid_bps: float | None, aggressive_shares: float) -> float | None:
    """Signed mid move (bps, aggressor-signed -- ``delta_mid_bps`` is expected pre-signed by the
    caller) per 1,000 aggressive shares over a feature window. ``None`` with no measured move or
    zero aggressive volume (no basis for a per-1000-share rate)."""
    if delta_mid_bps is None or aggressive_shares <= 0:
        return None
    return delta_mid_bps / (aggressive_shares / 1_000.0)


# --- F-LIQUIDITY ---------------------------------------------------------------------------------


def quote_imbalance(bid_size: float, ask_size: float) -> float | None:
    total = bid_size + ask_size
    if total <= 0:
        return None
    return (bid_size - ask_size) / total


def microprice(bid: float, ask: float, bid_size: float, ask_size: float) -> float | None:
    total = bid_size + ask_size
    if total <= 0:
        return None
    return (ask * bid_size + bid * ask_size) / total


# --- The closed outcome set (spec section 4) ------------------------------------------------------


class OutcomeRefused(Exception):
    """A requested outcome start precedes its conditioning feature set's maximum ``available_at``
    (TR-17c) -- refused, never silently measured early."""


def resolve_outcome_start(conditioning_available_at: Sequence[float]) -> float:
    """Outcome start = the conditioning feature set's maximum ``available_at`` (spec section 4;
    equals ``anchor_at`` when every conditioning feature is prefix, strictly later for a deferred
    construct). The canonical, always-legal resolution -- callers that want the guarded, possibly-
    illegal path use ``require_outcome_start_not_before_conditioning`` instead (TC-6/TR-17c)."""
    if not conditioning_available_at:
        raise ValueError("at least one conditioning available_at instant is required")
    return max(conditioning_available_at)


def require_outcome_start_not_before_conditioning(
    requested_start: float, conditioning_available_at: Sequence[float]
) -> float:
    """TR-17c's refusal: a ``requested_start`` earlier than the conditioning set's maximum
    ``available_at`` is refused with a typed error, never silently measured early. Returns
    ``requested_start`` unchanged when it is legal (>= the conditioning floor)."""
    floor = resolve_outcome_start(conditioning_available_at)
    if requested_start < floor:
        raise OutcomeRefused(
            f"requested outcome start {requested_start!r} precedes the conditioning feature "
            f"set's maximum available_at {floor!r} -- refused (TR-17c), never measured early"
        )
    return requested_start


# --- Units and the two side vocabularies (spec section 0 "Units", section 4, revision r13) -------
#
# **Revision r13 (2026-08-25).** Before r13 the primary outcome was an absolute mid-price
# DIFFERENCE -- dollars -- which ``scout.py`` then renamed ``effect_bps`` without converting and
# compared against a floor genuinely expressed in basis points (spec section 5.5). The gate was
# therefore dimensionally invalid, and the pooled estimator was itself meaningless across a corpus
# spanning ~$160 (PG) to ~$600 (SPY): a dollar is not comparable between price levels. r13 makes
# the canonical primary outcome a PRICE-SCALE-INVARIANT RETURN in basis points, computed by the
# ``bps_move`` primitive this module already owned and the outcome path simply never called.
#
# The ambiguous ``value`` key is deliberately GONE rather than redefined: an unlabelled number is
# exactly what let dollars masquerade as basis points for a whole era. Callers read ``return_bps``
# (the scientific primary) or ``delta_price`` (a diagnostic only -- never gated, never pooled).

BPS_UNIT = "bps"
OUTCOME_UNIT = "return_bps"

# The two vocabularies, previously implicit and silently interchangeable. **Aggressor side** names
# who crossed the spread on a TRADE (``micro_observer.py``'s own domain). **Candidate direction**
# names the hypothesis a registered candidate takes (``walkforward.py``/``micro_sealed_evaluation.
# py``'s ``sidedness``, and the frozen ``desk_playbook_detect.py``/``backtests.py`` vocabulary).
# They are disjoint by construction so a value from one can never satisfy a test written for the
# other -- the pre-r13 defect, where ``_signed`` flipped only on ``"sell"`` and a ``"short"``
# candidate was therefore silently NOT flipped and then killed as wrong-direction.
AGGRESSOR_SIDES: tuple[str, ...] = ("buy", "sell")
CANDIDATE_DIRECTIONS: tuple[str, ...] = ("long", "short")


class UnknownSideVocabularyError(ValueError):
    """A side/direction string outside its declared closed vocabulary reached a signing helper.
    Raised, never silently treated as positive (which is what the pre-r13 ``_signed`` did to every
    value that was not exactly ``"sell"``)."""


class UnitMismatchError(ValueError):
    """A magnitude was about to be compared against a floor that does not declare basis points --
    including a pre-r13 persisted floor, which carries no ``unit`` at all. Refused, because
    silently reinterpreting old-semantics evidence under the new convention is precisely the
    laundering r13 exists to prevent."""


def aggressor_sign(side: str) -> int:
    """``+1`` for a buy-side aggressor, ``-1`` for a sell-side one. A candidate DIRECTION
    (``long``/``short``) is not an aggressor side and is refused here."""
    if side not in AGGRESSOR_SIDES:
        raise UnknownSideVocabularyError(
            f"unknown aggressor side {side!r} -- expected one of {AGGRESSOR_SIDES}"
        )
    return 1 if side == "buy" else -1


def direction_sign(direction: str) -> int:
    """``+1`` for a long candidate, ``-1`` for a short one. An aggressor SIDE (``buy``/``sell``) is
    not a candidate direction and is refused here."""
    if direction not in CANDIDATE_DIRECTIONS:
        raise UnknownSideVocabularyError(
            f"unknown candidate direction {direction!r} -- expected one of {CANDIDATE_DIRECTIONS}"
        )
    return 1 if direction == "long" else -1


def direction_for_aggressor(side: str) -> str:
    """The ONE explicit adapter between the two vocabularies, for a caller that genuinely wants to
    read a trade's aggressor side as a hypothesis direction. Never implicit."""
    return "long" if aggressor_sign(side) == 1 else "short"


def _require_direction(direction: str | None) -> int:
    """Validates a candidate direction EAGERLY -- before any ``unmeasured``/``truncated``
    short-circuit -- and returns its sign. ``direction=None`` is an UNSIDED candidate (the honest
    default; every candidate registered to date carries it) and signs ``+1``. Anything outside
    ``CANDIDATE_DIRECTIONS`` raises, so an unmeasured or truncated row can never launder a bad
    vocabulary past the gate that would have caught it."""
    return 1 if direction is None else direction_sign(direction)


def require_bps_floor(econ_floor: dict) -> float:
    """The floor's magnitude, having proved it is expressed in basis points. The ONE door every
    economic-relevance comparison goes through (``scout.py``, ``walkforward.py``,
    ``micro_sealed_evaluation.py``), so no gate can compare against an undeclared unit."""
    unit = econ_floor.get("unit")
    if unit != BPS_UNIT:
        raise UnitMismatchError(
            f"economic floor declares unit {unit!r}, not {BPS_UNIT!r} -- refused. A floor with no "
            "unit is a pre-r13 record; its magnitude was never comparable to an r13 return_bps "
            "effect and is never reinterpreted as though it were."
        )
    floor_bps = econ_floor.get("floor_bps")
    if floor_bps is None:
        raise UnitMismatchError("economic floor carries no floor_bps magnitude -- refused")
    return float(floor_bps)


def validate_candidate_direction(direction: str | None) -> str | None:
    """The PUBLIC-BOUNDARY validator for a registered candidate's direction. ``None`` is a genuine,
    legal unsided exploratory candidate and passes; anything else must be a member of
    ``CANDIDATE_DIRECTIONS`` or this raises.

    Helper-level validation inside the outcome signer is not enough on its own: a bad vocabulary
    must be refused BEFORE it reaches a corpus read, an outcome read, or a frozen candidate spec,
    so it can never be laundered into the permanent record by a candidate that later happens to
    die as ``killed_insufficient_n`` (which never reaches the signer at all)."""
    if direction is not None:
        direction_sign(direction)  # raises UnknownSideVocabularyError on anything else
    return direction


def require_return_bps_effect(value: float | None, unit: str | None) -> float | None:
    """Proves a scientific effect magnitude is expressed in the canonical ``return_bps`` unit
    before anything compares, pools or gates it. Returns the value unchanged.

    r13's first pass proved the FLOOR's unit but took the effect on trust because a Python
    variable happened to be named ``effect_bps``. A name is not a proof: ``0.25`` percent placed
    in a field called ``effect`` must never reach the gate and be read as ``0.25`` bps."""
    if unit != OUTCOME_UNIT:
        raise UnitMismatchError(
            f"effect magnitude declares unit {unit!r}, not the canonical {OUTCOME_UNIT!r} -- "
            "refused. A magnitude with no declared unit, or one in a legacy/percent convention, "
            "is never compared, pooled, or gated as though it were basis points."
        )
    return value


def clears_economic_floor(
    effect_value: float | None, effect_unit: str | None, econ_floor: dict | None
) -> bool | None:
    """Spec section 5.5's economic-relevance column: ``|effect| >= floor_bps`` -- with **BOTH**
    sides proved, the effect through ``require_return_bps_effect`` and the floor through
    ``require_bps_floor``. ``None`` when either magnitude is genuinely absent -- never a fabricated
    ``False``. The unit is checked FIRST and unconditionally: a wrongly-united effect is a contract
    breach whether or not there is a value to compare.

    This answers "is the measured effect larger than the quoted-spread cost proxy", i.e. whether
    the effect is **economically interesting**. It is NOT a profitability finding: profitability
    requires an execution model (entry/exit rules, fill basis, slippage, fees, latency, capacity,
    borrow) that this era does not build. The proxy sentence travels with every served floor."""
    require_return_bps_effect(effect_value, effect_unit)
    if effect_value is None or econ_floor is None:
        return None
    return abs(effect_value) >= require_bps_floor(econ_floor)


def mid_outcome(
    *,
    mid_at_start: float | None,
    mid_at_horizon: float | None,
    outcome_start: float,
    horizon_ts: float,
    session_end_ts: float,
    direction: str | None,
) -> dict:
    """The mid-basis PRIMARY outcome (spec section 4, revision r13): the forward mid **return in
    basis points** from ``outcome_start`` to ``horizon_ts``, direction-signed when ``direction``
    names a hypothesis direction (``"long"``/``"short"``), session-truncated with the truncation
    flagged (and the row excluded from any later average, never silently measured past the
    session). A row lacking a quote mid at either end -- or carrying a non-positive starting mid,
    which has no basis to express a return against -- is ``unmeasured``: excluded and counted,
    never silently measured off the last trade and never a fabricated 0.0.

    ``return_bps`` is the scientific primary. ``delta_price`` is retained beside it as a raw
    DIAGNOSTIC (the dollar move an operator can eyeball against a chart); it is never gated,
    never pooled, and never compared to a bps floor."""
    sign = _require_direction(direction)
    truncated = horizon_ts > session_end_ts
    return_bps = bps_move(mid_at_start, mid_at_horizon)
    unmeasured = return_bps is None
    measured = not (unmeasured or truncated)
    return {
        "basis": "mid",
        "unit": OUTCOME_UNIT,
        "outcome_start": outcome_start,
        "horizon_ts": horizon_ts,
        "return_bps": sign * return_bps if measured else None,
        "delta_price": sign * (mid_at_horizon - mid_at_start) if measured else None,
        "unmeasured": unmeasured,
        "truncated": truncated,
    }


def last_trade_outcome(
    *,
    price_at_start: float | None,
    price_at_horizon: float | None,
    outcome_start: float,
    horizon_ts: float,
    session_end_ts: float,
    direction: str | None,
) -> dict:
    """The SEPARATELY NAMED last-trade-basis sensitivity column (spec section 4) -- identical
    shape and identical r13 unit to ``mid_outcome``, never pooled with, substituted for, or
    averaged into the mid-basis primary. Callers must keep the two bases apart at every serving
    surface."""
    sign = _require_direction(direction)
    truncated = horizon_ts > session_end_ts
    return_bps = bps_move(price_at_start, price_at_horizon)
    unmeasured = return_bps is None
    measured = not (unmeasured or truncated)
    return {
        "basis": "last_trade",
        "unit": OUTCOME_UNIT,
        "outcome_start": outcome_start,
        "horizon_ts": horizon_ts,
        "return_bps": sign * return_bps if measured else None,
        "delta_price": sign * (price_at_horizon - price_at_start) if measured else None,
        "unmeasured": unmeasured,
        "truncated": truncated,
    }


def spread_bps(spread: float | None, mid: float | None) -> float | None:
    """The quoted spread (dollar terms, exactly as the engine/observer already compute it)
    expressed in basis points of the mid -- spec section 4's cost-proxy column: "Quoted spread at
    the outcome start (bps) is served beside every outcome ... never netted into the outcome
    silently." A caller (``micro_join.py``, the FIRST caller of this closed outcome set) reads
    this beside ``mid_outcome``/``last_trade_outcome`` as an independent field -- it is never
    added to or subtracted from either outcome's own ``value``. ``None`` with no measured spread
    or mid, or a non-positive mid (no basis for a bps expression), never a fabricated 0.0."""
    if spread is None or mid is None or mid <= 0:
        return None
    return spread / mid * 10_000.0


# --- The section 2.6 cross-basis unit gate (TR-18) ------------------------------------------------


class CrossBasisUnverifiedUnitError(Exception):
    """A cross-basis liquidity computation (trade shares vs. displayed quote sizes) was requested
    against an unverified -- or, for a pooled request, a mixed -- ``quote_size_unit``. Refused,
    never silently normalized (spec section 2.6)."""


def is_verified_unit(quote_size_unit: str) -> bool:
    return quote_size_unit in ("shares", "round_lots")


def require_verified_unit(quote_size_unit: str) -> None:
    if not is_verified_unit(quote_size_unit):
        raise CrossBasisUnverifiedUnitError(
            f"cross-basis liquidity arithmetic refused: quote_size_unit={quote_size_unit!r} is "
            "not verified (spec section 2.6) -- unit normalization exists only as a recorded "
            "verification act, never silent arithmetic"
        )


def require_uniform_unit_for_pool(units: Sequence[str]) -> str:
    """TR-18's pooled-request refusal: a request spanning more than one distinct
    ``quote_size_unit`` (verified or not) is refused outright, and a single unanimous-but-
    unverified unit is refused too (``require_verified_unit``)."""
    distinct = sorted(set(units))
    if len(distinct) != 1:
        raise CrossBasisUnverifiedUnitError(
            f"pooled cross-basis request spans mixed quote_size_unit values {distinct} -- "
            "refused (TR-18)"
        )
    require_verified_unit(distinct[0])
    return distinct[0]


def execution_vs_replenishment_ratio(
    *, executed_volume: float, replenished_size: float, quote_size_unit: str
) -> float | None:
    """Executed trade volume at a price divided by displayed-size restoration there (spec section
    3) -- CROSS-BASIS, so it is refused unless ``quote_size_unit`` is verified. ``None`` with zero
    replenishment observed (no basis for a ratio), never a division by zero."""
    require_verified_unit(quote_size_unit)
    if replenished_size <= 0:
        return None
    return executed_volume / replenished_size


def require_share_denominated_magnitude_allowed(quote_size_unit: str) -> None:
    """The section 2.6 gate applied to any OTHER share-denominated depletion/replenishment
    MAGNITUDE (as opposed to a ratio) -- the identical refusal, a separate named entry point so a
    caller expressing "I am about to report a raw share-denominated cross-basis magnitude" reads
    as exactly that at the call site."""
    require_verified_unit(quote_size_unit)
