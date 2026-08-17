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
    "OutcomeRefused",
    "resolve_outcome_start",
    "require_outcome_start_not_before_conditioning",
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
    touch fixes when the comparison could first be made)."""
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
    return {
        "tau1": tau1,
        "tau2": tau2,
        "price_extreme_tau1": price_extreme_tau1,
        "price_extreme_tau2": price_extreme_tau2,
        "cum_delta_tau1": cum_delta_at_tau1,
        "cum_delta_tau2": cum_delta_at_tau2,
        "delta_volume_fraction_threshold": delta,
        "bearish_divergence": bearish,
        "available_at": tau2,
    }


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


def _signed(value: float | None, side: str | None) -> float | None:
    if value is None:
        return None
    return -value if side == "sell" else value


def mid_outcome(
    *,
    mid_at_start: float | None,
    mid_at_horizon: float | None,
    outcome_start: float,
    horizon_ts: float,
    session_end_ts: float,
    side: str | None,
) -> dict:
    """The mid-basis PRIMARY outcome (spec section 4): forward mid-price move from ``outcome_
    start`` to ``horizon_ts``, side-signed when ``side`` names a hypothesis direction ("buy"/
    "sell"), session-truncated with the truncation flagged (and the row excluded from any later
    average, never silently measured past the session). A row lacking a quote mid at either end is
    ``unmeasured`` -- excluded and counted, never silently measured off the last trade."""
    truncated = horizon_ts > session_end_ts
    unmeasured = mid_at_start is None or mid_at_horizon is None
    value = None
    if not unmeasured and not truncated:
        value = _signed(mid_at_horizon - mid_at_start, side)
    return {
        "basis": "mid",
        "outcome_start": outcome_start,
        "horizon_ts": horizon_ts,
        "value": value,
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
    side: str | None,
) -> dict:
    """The SEPARATELY NAMED last-trade-basis sensitivity column (spec section 4) -- identical
    shape to ``mid_outcome``, never pooled with, substituted for, or averaged into the mid-basis
    primary. Callers must keep the two bases apart at every serving surface."""
    truncated = horizon_ts > session_end_ts
    unmeasured = price_at_start is None or price_at_horizon is None
    value = None
    if not unmeasured and not truncated:
        value = _signed(price_at_horizon - price_at_start, side)
    return {
        "basis": "last_trade",
        "outcome_start": outcome_start,
        "horizon_ts": horizon_ts,
        "value": value,
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
