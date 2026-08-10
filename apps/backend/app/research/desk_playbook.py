"""The Playbook (Era B2 "The Playbook", J-01/J-02) -- the book's intraday setups
(Graifer & Schumacher, *Techniques of Tape Reading*, 2004), detected on the desk's own recorded
5m/1m bars and measured with the desk forward rail's own conventions. This module owns the
pre-registered constant table, the parameters/signature recipe, the append-only store, and the
per-session compute walker; ``app/research/desk_playbook_features.py`` owns the shared primitives
and ``app/research/desk_playbook_detect.py`` owns the detectors themselves -- see
``docs/playbook-detector-spec.md`` for the canonical rule set every constant/detector here
implements verbatim.

**A THIRD "setup" vocabulary -- never conflate.** ``setups.py`` (the tick-touch-of-a-structural-
level scanner) and ``backtests.py`` (tape-arming occurrences under a strategy profile) ALREADY use
"setup" for two OTHER things. A playbook signal is the book's intraday PATTERN (an opening-range
break, a jump-base-explosion, ...) -- a third, unrelated sense of the word. This module never
imports from ``setups.py`` or ``backtests.py``, and no field here is ever named ``stop_loss``
(the field is ``invalidation_price`` -- a disclosed structural level, never an order concept).

**Detection only, this iteration.** ``compute_playbook`` walks the desk universe's members and
detects the opening-range-break family (spec §3.1-3.2); trigger-anchored measurement (forward
returns, ``invalidation_breached``, the seeded baseline) is J-02 -- ``entry``/``entry_kind`` are
computed now (spec §0's stop-through fill convention is part of a signal's own GEOMETRY, decided
at the trigger bar, not part of measuring what happened afterward).

**Parameters discipline (the ``desk_forward.forward_parameters`` pattern, applied at birth).**
``playbook_parameters()`` reads every constant below at CALL TIME (so a test monkeypatching one
genuinely moves both the served blob and the signature) and embeds the measurement rail's own
horizon/seed/measure-shape constants verbatim -- a FUTURE change to ``desk_forward.py`` would
re-key every playbook record instead of silently reinterpreting it, even though this iteration
does no measurement at all. ``compute_playbook_input_signature`` mirrors
``desk_forward.compute_forward_input_signature`` exactly: sha256[:16] over the sorted
``(symbol, timeframe, series_id, checksum)`` tuples of every series the compute could read
(members union {SPY}, the two fine timeframes only) plus the config fingerprint plus the
parameters blob.

**Store discipline (the ``desk_forward.ForwardStore`` pattern).** ``PlaybookStore`` is a 2-pin
(``session_date``, ``playbook_input_signature``) append-only file store: every load verifies a
whole-record checksum, an identical key is refused (never silently reused as a second file), a
corrupt file is surfaced loudly and never overwritten, and -- structurally, by never being written
-- there is no update or delete method anywhere on this class. A changed constant re-keys and
mints a NEW version; every older recorded file stays byte-identical forever.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .desk_forward import (
    DESK_FORWARD_BASELINE_SEED,
    DESK_FORWARD_HORIZONS_MINUTES,
    DESK_FORWARD_HORIZON_MEASURES,
    DESK_FORWARD_MAX_TOUCHES_PER_ROW,
    DESK_FORWARD_MEASURE_KEYS,
    _avg_cell,
    _collect_measures,
    _draw_anchor_indices,
    _measure_from,
)
from .desk_playbook_detect import detect_opening_range_breaks
from .desk_playbook_features import baselines, opening_range, rth_session_slice, side_sign
from .desk_sessions import refuse_if_not_a_session

__all__ = [
    "PLAYBOOK_SETUPS",
    "PLAYBOOK_MARKET_SYMBOL",
    "PLAYBOOK_REGISTER",
    "PlaybookIntegrityError",
    "PlaybookAlreadyRecorded",
    "PlaybookSessionRefused",
    "PlaybookStore",
    "resolve_desk_playbook_dir",
    "playbook_parameters",
    "compute_playbook_input_signature",
    "compute_playbook",
]

# --- Pre-registered constants (docs/playbook-detector-spec.md §1 -- the COMPLETE tunable surface,
# transcribed verbatim; nothing else exists). Every one is embedded in `playbook_parameters()` and
# hashed into the input signature, whether or not a detector built so far actually reads it -- the
# table is declared whole (T-1: "no threshold exists outside the spec"), detectors are built
# incrementally. BOOK = the book's own stated number; ADAPTATION = a single named choice where the
# book is vague (rationale in the spec doc; not re-derived here). ------------------------------------

PLAYBOOK_BASELINE_SESSIONS: int = 20  # ADAPTATION -- Card 5.5's RVOL convention
PLAYBOOK_MIN_BASELINE_SESSIONS: int = 10  # ADAPTATION -- minimum honest median
PLAYBOOK_RVOL_SURGE: float = 2.0  # ADAPTATION -- book's "volume surge" unquantified
PLAYBOOK_RVOL_ELEVATED: float = 1.5  # ADAPTATION -- Card 5.5 high-RVOL bucket boundary
PLAYBOOK_RVOL_DRYUP: float = 0.7  # ADAPTATION -- Card 5.5 low-RVOL bucket boundary
PLAYBOOK_VOL_CONTRAST_RATIO: float = 0.6  # ADAPTATION -- mechanical "dries on pullback" ratio
PLAYBOOK_MAX_CHASE_FRAC: float = 0.002  # BOOK -- 3-5c chase on ~$20 approx 0.2%
PLAYBOOK_STOP_PAD_FRAC: float = 0.30  # BOOK -- 20-40% stop padding; midpoint
PLAYBOOK_OR_MINUTES: int = 15  # BOOK -- opening range = first 15-20 min; lower endpoint
# ADAPTATION, not tabulated in the spec's own §1 table -- stated in §2 primitive 2's prose ONLY
# ("fewer than 10 of the 15 one-minute bars on file -> fall back"). Named here rather than left an
# inline literal so it still passes through `playbook_parameters()`/the signature like every other
# threshold; flagged in the dev handoff for an owner ruling on whether §1 should gain this row.
PLAYBOOK_OR_MIN_1M_BARS: int = 10
PLAYBOOK_NARROW_OR_MAX_MBR: float = 3.0  # ADAPTATION -- relative form of the <=25c narrow range
PLAYBOOK_JUMP_MIN_MULT: float = 1.5  # BOOK -- jump >= 1.5-2x base; stated minimum
PLAYBOOK_JUMP_MIN_MOVE_MBR: float = 3.0  # ADAPTATION -- floor so tiny/tiny can't satisfy the ratio
PLAYBOOK_JUMP_LOOKBACK_BARS: int = 6  # ADAPTATION -- jump low read from the 30 min before the base
PLAYBOOK_BASE_MIN_BARS: int = 3  # ADAPTATION -- book gives no consolidation duration
PLAYBOOK_BASE_MAX_BARS: int = 12  # ADAPTATION -- 60-min cap
PLAYBOOK_BASE_MAX_RANGE_MBR: float = 2.0  # ADAPTATION -- relative form of the <=25c narrow base
PLAYBOOK_NEAR_EXTREME_MBR: float = 1.0  # ADAPTATION -- mechanical "near the high/low"
PLAYBOOK_PIVOT_LOOKBACK_BARS: int = 3  # ADAPTATION -- 5m intraday N for the strict-pivot rule
PLAYBOOK_CUP_MIN_BARS: int = 6  # BOOK -- cup >= 30 min
PLAYBOOK_CUP_OPTIMAL_BARS: int = 12  # BOOK -- >= 1h optimal (disclosure only)
PLAYBOOK_HANDLE_MAX_RETRACE_FRAC: float = 0.5  # BOOK -- handle <= 50% of cup depth
PLAYBOOK_HANDLE_MAX_DURATION_FRAC: float = 0.30  # BOOK -- handle <= 30% of cup duration
PLAYBOOK_RIM_MATCH_MBR: float = 1.0  # ADAPTATION -- "cup edges at the day's high" tolerance
PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR: float = 2.0  # ADAPTATION -- min cup depth AND min valley depth
PLAYBOOK_VERTICAL_WINDOW_BARS: int = 3  # ADAPTATION -- "near-vertical" window (15 min)
PLAYBOOK_VERTICAL_MOVE_MBR: float = 4.0  # ADAPTATION -- net move for capitulation/euphoria
PLAYBOOK_VERTICAL_BAR_MBR: float = 2.5  # ADAPTATION -- single-bar spike (spiky-approach flag)
PLAYBOOK_BOUNCE_MAX_BARS: int = 3  # ADAPTATION -- reversal confirmation must come fast
PLAYBOOK_RANGE_MIN_WIDTH_MBR: float = 4.0  # ADAPTATION -- narrower = breakout-only per Ch 13
PLAYBOOK_RANGE_HOLD_TOL_MBR: float = 0.5  # ADAPTATION -- "held" tolerance; absorption-bar max range
PLAYBOOK_TOPS_MATCH_MBR: float = 1.0  # ADAPTATION -- two tops "at the same level"
PLAYBOOK_TOPS_MIN_SEPARATION_BARS: int = 4  # ADAPTATION -- tops >= 20 min apart
PLAYBOOK_LADDER_HEALTHY_LOW: float = 0.50  # BOOK -- ladder step 50-75% of prior step (disclosure)
PLAYBOOK_LADDER_HEALTHY_HIGH: float = 0.75  # BOOK -- ladder step 50-75% of prior step (disclosure)
PLAYBOOK_MKT_LOOKBACK_BARS: int = 6  # ADAPTATION -- 30-min index-direction window
PLAYBOOK_MKT_NEUTRAL_BAND_MBR: float = 1.0  # ADAPTATION -- neutral band, index-MBR units
PLAYBOOK_MARKER_DECAY_BARS: int = 6  # ADAPTATION -- euphoria/capitulation marker decorates 30 min
PLAYBOOK_APPROACH_BARS: int = 3  # ADAPTATION -- volume-into-trigger window
PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION: int = 2  # ADAPTATION -- ladder steps

# Companion structural constants (shape, not thresholds).
# This iteration implements ONLY the opening-range-break family; J-04/J-05/J-06 EXTEND this tuple
# as they land their own detectors (a signature-moving, expected, visible change) -- declaring a
# setup id here before its detector exists would claim a compute that does not happen.
PLAYBOOK_SETUPS: tuple[str, ...] = ("open_high_break", "open_low_break")
PLAYBOOK_MARKET_SYMBOL: str = "SPY"
# The rail's own baseline seed, echoed (not re-derived) -- the seed discipline itself is J-02's;
# embedding the CONSTANT now is what makes a future rail-seed change re-key playbook records too.
PLAYBOOK_BASELINE_SEED: int = DESK_FORWARD_BASELINE_SEED
PLAYBOOK_RETURN_SIGN_CONVENTION: str = "side_relative"
# The rail's own measure-key shape, echoed verbatim (J-02 measures playbook signals through it).
PLAYBOOK_SIGNAL_MEASURES: tuple[str, ...] = DESK_FORWARD_MEASURE_KEYS
PLAYBOOK_MIN_N_DISCLOSURE: int = 12  # evidence low-n tag (J-08) -- a disclosure floor, never a gate

# The visible honesty register carried by every playbook payload. Lint-checked via
# test_copy_discipline.find_violations (the desk_forward.FORWARD_REGISTER precedent).
PLAYBOOK_REGISTER = (
    "pre-registered opening-range-break signals detected on the desk's own recorded 5m/1m bars — "
    "every threshold is fixed in advance in docs/playbook-detector-spec.md, never fit to outcomes. "
    "A signal is a recorded observation, not advice: invalidation_price is the book's own "
    "structural level, disclosed as geometry, never a stop order, a size, or an account concept. "
    "Each signal's forward block is measured with the desk forward rail's own conventions — "
    "trading-bar horizons, dual max drawdown, truncation honesty — anchored at the entry already "
    "decided at detection time, never recomputed a second way; invalidation_breached discloses "
    "whether price ever traded through that structural level, never an exit model; baseline_anchors "
    "and summary compare every signal against the SAME math anchored at seeded random minutes of "
    "the same session. A record computed before this measurement pass existed carries an honest "
    "absence instead — no fills, no costs, and no probability, expectancy, edge, or significance "
    "claim are made anywhere on this payload"
)

_PLAYBOOK_DIR_ENV = "TAPEOLOGY_DESK_PLAYBOOK_DIR"
_PLAYBOOK_SIGNATURE_TIMEFRAMES: tuple[str, ...] = ("1m", "5m")


class PlaybookIntegrityError(Exception):
    """An on-disk playbook record file failed its checksum verification on load -- corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated record)."""


class PlaybookAlreadyRecorded(Exception):
    """A playbook record with this EXACT 2-pin key (``session_date``, ``playbook_input_signature``)
    is already registered. Playbook records are immutable and append-only -- a re-run over
    identical inputs reuses the existing record, never a second file."""

    def __init__(self, existing_id: str) -> None:
        self.existing_id = existing_id
        super().__init__(
            f"a playbook record with this exact key is already recorded as '{existing_id}' -- "
            f"playbook records are immutable and are never re-recorded"
        )


class PlaybookSessionRefused(Exception):
    """``session_date`` is provably not a recorded trading session
    (``desk_sessions.refuse_if_not_a_session``'s sentence) -- nothing to detect, and
    ``compute_playbook`` writes nothing (mirrors ``ForwardScreenNotFound``: a whole-computation
    refusal, raised before any walk starts)."""


def resolve_desk_playbook_dir(desk_universe_dir_resolved: str) -> str:
    """The playbook store's directory: ``TAPEOLOGY_DESK_PLAYBOOK_DIR`` if set, else a ``playbook``
    SIBLING of the caller's own already-resolved universe directory -- the
    ``resolve_desk_forward_dir`` pattern verbatim. Deliberately NOT a ``Config`` field."""
    override = os.environ.get(_PLAYBOOK_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "playbook")


def playbook_parameters() -> dict:
    """The parameters block embedded verbatim in every recorded payload AND hashed into the input
    signature -- ONE builder so the two can never drift (the ``desk_forward.forward_parameters``
    pattern). Reads every module constant at CALL TIME, so a test monkeypatching one genuinely
    moves both the payload and the key. This is also the ONLY dict a detector ever reads playbook
    thresholds from (``desk_playbook_detect.py`` takes no constant import of its own) -- so "the
    parameters blob matches what the detector actually used" holds by construction, not by
    coincidence."""
    return {
        "setups": list(PLAYBOOK_SETUPS),
        "market_symbol": PLAYBOOK_MARKET_SYMBOL,
        "baseline_seed": PLAYBOOK_BASELINE_SEED,
        "return_sign_convention": PLAYBOOK_RETURN_SIGN_CONVENTION,
        "signal_measures": list(PLAYBOOK_SIGNAL_MEASURES),
        "min_n_disclosure": PLAYBOOK_MIN_N_DISCLOSURE,
        "baseline_sessions": PLAYBOOK_BASELINE_SESSIONS,
        "min_baseline_sessions": PLAYBOOK_MIN_BASELINE_SESSIONS,
        "rvol_surge": PLAYBOOK_RVOL_SURGE,
        "rvol_elevated": PLAYBOOK_RVOL_ELEVATED,
        "rvol_dryup": PLAYBOOK_RVOL_DRYUP,
        "vol_contrast_ratio": PLAYBOOK_VOL_CONTRAST_RATIO,
        "max_chase_frac": PLAYBOOK_MAX_CHASE_FRAC,
        "stop_pad_frac": PLAYBOOK_STOP_PAD_FRAC,
        "or_minutes": PLAYBOOK_OR_MINUTES,
        "or_min_1m_bars": PLAYBOOK_OR_MIN_1M_BARS,
        "narrow_or_max_mbr": PLAYBOOK_NARROW_OR_MAX_MBR,
        "jump_min_mult": PLAYBOOK_JUMP_MIN_MULT,
        "jump_min_move_mbr": PLAYBOOK_JUMP_MIN_MOVE_MBR,
        "jump_lookback_bars": PLAYBOOK_JUMP_LOOKBACK_BARS,
        "base_min_bars": PLAYBOOK_BASE_MIN_BARS,
        "base_max_bars": PLAYBOOK_BASE_MAX_BARS,
        "base_max_range_mbr": PLAYBOOK_BASE_MAX_RANGE_MBR,
        "near_extreme_mbr": PLAYBOOK_NEAR_EXTREME_MBR,
        "pivot_lookback_bars": PLAYBOOK_PIVOT_LOOKBACK_BARS,
        "cup_min_bars": PLAYBOOK_CUP_MIN_BARS,
        "cup_optimal_bars": PLAYBOOK_CUP_OPTIMAL_BARS,
        "handle_max_retrace_frac": PLAYBOOK_HANDLE_MAX_RETRACE_FRAC,
        "handle_max_duration_frac": PLAYBOOK_HANDLE_MAX_DURATION_FRAC,
        "rim_match_mbr": PLAYBOOK_RIM_MATCH_MBR,
        "min_structure_depth_mbr": PLAYBOOK_MIN_STRUCTURE_DEPTH_MBR,
        "vertical_window_bars": PLAYBOOK_VERTICAL_WINDOW_BARS,
        "vertical_move_mbr": PLAYBOOK_VERTICAL_MOVE_MBR,
        "vertical_bar_mbr": PLAYBOOK_VERTICAL_BAR_MBR,
        "bounce_max_bars": PLAYBOOK_BOUNCE_MAX_BARS,
        "range_min_width_mbr": PLAYBOOK_RANGE_MIN_WIDTH_MBR,
        "range_hold_tol_mbr": PLAYBOOK_RANGE_HOLD_TOL_MBR,
        "tops_match_mbr": PLAYBOOK_TOPS_MATCH_MBR,
        "tops_min_separation_bars": PLAYBOOK_TOPS_MIN_SEPARATION_BARS,
        "ladder_healthy_low": PLAYBOOK_LADDER_HEALTHY_LOW,
        "ladder_healthy_high": PLAYBOOK_LADDER_HEALTHY_HIGH,
        "mkt_lookback_bars": PLAYBOOK_MKT_LOOKBACK_BARS,
        "mkt_neutral_band_mbr": PLAYBOOK_MKT_NEUTRAL_BAND_MBR,
        "marker_decay_bars": PLAYBOOK_MARKER_DECAY_BARS,
        "approach_bars": PLAYBOOK_APPROACH_BARS,
        "max_jbe_signals_per_session": PLAYBOOK_MAX_JBE_SIGNALS_PER_SESSION,
        # The measurement rail's own shape constants, echoed verbatim (embedded at birth, per the
        # module docstring) -- a FUTURE desk_forward.py change re-keys playbook records instead of
        # silently reinterpreting them, even though J-01 measures nothing itself.
        "rail_horizons_minutes": [list(pair) for pair in DESK_FORWARD_HORIZONS_MINUTES],
        "rail_baseline_seed": DESK_FORWARD_BASELINE_SEED,
        "rail_horizon_measures": list(DESK_FORWARD_HORIZON_MEASURES),
        # J-02: the rail's own per-row touch cap, reused verbatim (never re-derived) as the
        # per-(setup_id, side) pooling cap on baseline_anchors/summary -- bounds a pathological
        # many-symbols-firing-the-same-setup session exactly the way it already bounds a
        # band-hugging one, without hiding that it was one (signals_beyond_cap discloses the rest).
        # Embedding it here is also what re-keys every J-01-era (unmeasured) record: the SAME
        # session_date and bar content under J-02's code now hashes a DIFFERENT parameters blob, so
        # a fresh compute mints a genuinely NEW version instead of matching the old, unmeasured one.
        "rail_max_touches_per_row": DESK_FORWARD_MAX_TOUCHES_PER_ROW,
    }


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum in this module hashes -- the SAME encoding
    every other desk store hashes (``desk_forward.py._canonical`` et al)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def compute_playbook_input_signature(bar_store, members: list[str], config_fingerprint: str) -> str:
    """The playbook record's own input pin: sha256[:16] over the sorted ``(symbol, timeframe,
    series_id, checksum)`` tuples of every recorded series the compute could possibly read
    (``members`` union ``{SPY}``, the two fine timeframes ONLY), plus the config fingerprint and
    the canonical parameters blob -- ``desk_forward.compute_forward_input_signature``'s recipe
    verbatim. Metadata-only (``list(include_bars=False)``): resolving the pin costs no bar reads."""
    records, _errors = bar_store.list(include_bars=False)
    wanted = set(members) | {PLAYBOOK_MARKET_SYMBOL}
    tuples = sorted(
        (record["symbol"], record["timeframe"], record["id"], record["checksum"])
        for record in records
        if record["symbol"] in wanted and record["timeframe"] in _PLAYBOOK_SIGNATURE_TIMEFRAMES
    )
    return _sha256(_canonical([tuples, config_fingerprint, playbook_parameters()]))[:16]


def _prior_session_close(bars_5m: list, session_date: str) -> float | None:
    """The most recent PRIOR RTH session's own last 5m close, for ``geometry.
    open_vs_prior_close_pct``'s gap-context disclosure -- ``None`` (never a guess) when no earlier
    session is on file. A small, self-contained scan (distinct from ``baselines()``'s own prior-
    dates walk -- that one pools MANY sessions for a median; this one only ever needs the single
    most recent one)."""
    all_dates = sorted(
        {datetime.fromtimestamp(bar.epoch, tz=timezone.utc).date().isoformat() for bar in bars_5m}
    )
    priors = [d for d in all_dates if d < session_date]
    if not priors:
        return None
    prior_bars = rth_session_slice(bars_5m, priors[-1])
    return prior_bars[-1].close if prior_bars else None


def _measurement_anchor(
    session_5m: list, session_1m: list, trigger_idx_5m: int, trigger_price: float
) -> tuple[list, int, int]:
    """Map ONE signal's already-detected 5m trigger bar to its OWN measurement anchor on the
    finest series ITS OWN trigger window can actually supply -- spec Sec0's 5m->1m mapping: the
    first 1m bar of the trigger bar's own ``[epoch, epoch+300)`` window whose ``[low, high]``
    contains the trigger price ``T``, falling back to that window's first 1m bar. A gap spanning
    the WHOLE window (no 1m bar inside it at all) degrades THIS signal to the 5m basis rather than
    silently borrowing a bar from a neighboring 5m window -- ``_measure_from``'s own per-horizon
    ``reason`` field (the ``minutes % tf_minutes`` mismatch) already discloses the coarser basis
    honestly, so no new served field is needed for the degrade itself. A session carrying no 1m
    bars at all degrades every one of its signals the same way, for free -- "session-level, not
    per-signal" falls out of this rule rather than needing a separate pre-check.

    Returns ``(measure_bars, anchor_index, tf_minutes)`` -- the SAME series/tf a baseline anchor
    for this signal's own (symbol, setup_id) must also use, so the null lives in the same basis as
    what it is the null for."""
    trigger_bar_5m = session_5m[trigger_idx_5m]
    if not session_1m:
        return session_5m, trigger_idx_5m, 5
    window_start = trigger_bar_5m.epoch
    window_end = window_start + 300.0
    window_1m = [
        (idx, bar) for idx, bar in enumerate(session_1m) if window_start <= bar.epoch < window_end
    ]
    if not window_1m:
        return session_5m, trigger_idx_5m, 5
    for idx, bar in window_1m:
        if bar.low <= trigger_price <= bar.high:
            return session_1m, idx, 1
    first_idx, _first_bar = window_1m[0]
    return session_1m, first_idx, 1


def _invalidation_breached(
    measure_bars: list,
    anchor_index: int,
    invalidation_price: float,
    side: str,
    tf_minutes: int,
    forward: dict,
) -> dict:
    """The same-pass, OUTSIDE-``_measure_from`` disclosure spec Sec0 requires (so the rail's own
    served horizon shape never changes): did price ever trade through ``invalidation_price`` from
    the anchor bar through the session close, and -- if so -- at what bar-equivalent minute offset
    (``first_breach_minutes``: ONE session-wide fact, the same value on every horizon leaf that
    reaches it -- never re-derived per horizon, never a guess). A horizon key is ``True`` when the
    first breach falls AT OR BEFORE that horizon's own already-measured ``effective_minutes``
    (reusing ``forward``'s own truncation-honest window -- never a second, independent walk); a
    horizon this signal could not even measure at this tf (``reason`` set, ``effective_minutes``
    null) is vacuously ``False`` -- it never observed anything. ``to_close`` spans the whole
    remaining session by definition, so it is ``True`` exactly when any breach was ever observed at
    all. Long: breached when a bar's low reaches the level (below entry); short: mirrored (high)."""
    tail = measure_bars[anchor_index:]
    first_breach_offset: int | None = None
    for offset, bar in enumerate(tail):
        breached = (
            bar.low <= invalidation_price if side == "long" else bar.high >= invalidation_price
        )
        if breached:
            first_breach_offset = offset
            break
    first_breach_minutes = (
        first_breach_offset * tf_minutes if first_breach_offset is not None else None
    )

    result: dict = {}
    for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES:
        effective = forward["horizons"][label]["effective_minutes"]
        result[label] = (
            first_breach_minutes is not None
            and effective is not None
            and first_breach_minutes <= effective
        )
    result["to_close"] = first_breach_minutes is not None
    result["first_breach_minutes"] = first_breach_minutes
    return result


def _measure_signal(signal: dict, session_5m: list, session_1m: list) -> tuple[dict, dict, list, int]:
    """Measure ONE already-detected signal through the rail's own ``_measure_from`` -- THE call
    site the convention-identity test compares against a direct ``desk_forward._measure_from`` call
    with the identical arguments. Reuses the signal's own already-detected ``entry``/``entry_kind``
    (spec Sec0's stop-through convention, decided at J-01 detection time) and ``trigger_price``
    verbatim -- nothing here re-derives them a second way. Returns
    ``(forward, invalidation_breached, measure_bars, tf_minutes)`` -- the last two so the caller's
    baseline-anchor draw for this signal's (symbol, setup_id) measures on the SAME basis."""
    trigger_idx_5m = signal["geometry"]["slots_to_break"]
    measure_bars, anchor_index, tf_minutes = _measurement_anchor(
        session_5m, session_1m, trigger_idx_5m, signal["trigger_price"]
    )
    sign = side_sign(signal["side"])
    forward = _measure_from(
        measure_bars, anchor_index, signal["entry"], signal["entry_kind"], tf_minutes, sign
    )
    breached = _invalidation_breached(
        measure_bars, anchor_index, signal["invalidation_price"], signal["side"], tf_minutes, forward
    )
    return forward, breached, measure_bars, tf_minutes


def _baseline_seed(session_date: str, symbol: str, setup_id: str, firing_index: int) -> str:
    """The baseline-anchor draw's own seed for ONE signal firing of ``(symbol, setup_id)`` within
    ``session_date`` -- ``firing_index`` is the running WITHIN-SESSION count of prior firings of
    this EXACT ``(symbol, setup_id)`` pair (``0`` for the first).

    **The recipe is UNCHANGED -- no discriminator suffix at all -- for ``firing_index == 0``.**
    Every currently-recordable signal (opening-range-break fires at MOST once per symbol-session,
    the detector's own mutual-exclusion rule) draws the byte-identical seed it always has, so a
    fresh compute over already-recorded fixture inputs reproduces byte-identical output before vs.
    after this change. A detector that CAN fire more than once for the same ``(symbol, setup_id)``
    in one session (J-04's JBE ladder steps) gets a distinguishing ``:<firing_index>`` suffix from
    its SECOND firing on, so each firing draws an INDEPENDENT anchor index instead of colliding on
    the identical one the un-discriminated seed would draw twice -- today this is a genuine no-op
    (the collision it guards against cannot occur yet), but it must land before J-04 lands a
    detector that can trigger it."""
    discriminator = "" if firing_index == 0 else f":{firing_index}"
    return f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{setup_id}{discriminator}"


def compute_playbook(
    universe_store,
    bar_store,
    config_fingerprint: str,
    session_date: str,
    *,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> dict:
    """Detect AND measure the opening-range-break family for EVERY member of the latest registered
    universe snapshot, on ``session_date``'s own recorded bars, in the SAME walk -- returns
    everything ``PlaybookStore.record`` needs minus the store-assigned ``id``/``recorded_at`` (the
    ``compute_forward``/``compute_screen`` contract shape: a PURE compute, never itself a store
    write).

    Session-honesty first: ``desk_sessions.refuse_if_not_a_session`` is checked before any bar is
    read for detection (no separate compute-manager/route layer exists yet this iteration, so this
    function plays that role) -- a non-session date raises ``PlaybookSessionRefused`` and NOTHING
    is walked. Per member: no 5m bars for the session, a thin/zero baseline, or no buildable opening
    range are each a disclosed ``absences`` row (never a crash, never a guess); everything else
    reaches the detector, which may add a signal, an ``ambiguous_outside_bar`` diagnostic, or
    neither (a legitimate "the setup did not form" outcome -- not an absence).

    J-02: every detected signal is measured in the SAME pass -- ``_measure_signal`` attaches
    ``forward`` (the rail's own ``_measure_from`` shape, anchored on the finest series THIS
    signal's own trigger window can supply) and ``invalidation_breached`` (computed OUTSIDE
    ``_measure_from``, never touching its served shape). In-cap signals (per ``(setup_id, side)``,
    capped at the rail's own ``DESK_FORWARD_MAX_TOUCHES_PER_ROW`` -- see ``playbook_parameters``)
    also draw ONE seeded random-anchor baseline measurement each
    (``f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{setup_id}"``, a fresh per-
    symbol-and-setup stream so pooling is walk-order-independent), pooled across every symbol
    sharing that ``(setup_id, side)`` into the record's ``baseline_anchors``/``summary``; a pool
    that exceeds the cap discloses the excess via ``signals_beyond_cap`` rather than silently
    dropping it. ``progress``, if given, is called after EACH member with ``{"symbol": symbol}``
    (whether it fired, was absent, or neither); a ``should_abort`` returning True stops the walk
    early -- the CALLER must then discard the partial result (a cancelled walk is never recorded)."""
    universe_records, _universe_errors = universe_store.list()
    members = list(universe_records[-1]["members"]) if universe_records else []

    refusal = refuse_if_not_a_session(session_date, bar_store, members)
    if refusal is not None:
        raise PlaybookSessionRefused(refusal)

    params = playbook_parameters()
    signature = compute_playbook_input_signature(bar_store, members, config_fingerprint)
    index_bars = bar_store.merged_bars(PLAYBOOK_MARKET_SYMBOL, "5m")
    # SPY's own baseline MBR normalizes `market_move` into MBR units (spec §0) -- resolved ONCE
    # (it does not vary per member), not re-baselined inside every member's detector call.
    index_baseline = baselines(
        bar_store, PLAYBOOK_MARKET_SYMBOL, session_date,
        PLAYBOOK_BASELINE_SESSIONS, PLAYBOOK_MIN_BASELINE_SESSIONS,
    )

    signals: list[dict] = []
    absences: list[dict] = []
    diagnostics: list[dict] = []
    # Cross-symbol pools keyed "<setup_id>:<side>" -- the ONLY pooling boundary that makes sense
    # this iteration, since a single symbol-session can carry at most ONE opening-range-break
    # signal (the detector's own mutual-exclusion rule); a future multi-signal-per-session detector
    # (J-04's JBE) pools into the SAME dict by construction, no rewrite needed.
    signal_pool: dict[str, list[dict]] = {}
    baseline_pool: dict[str, list[dict]] = {}
    pool_counts: dict[str, int] = {}
    pool_beyond_cap: dict[str, int] = {}
    # The baseline-draw seed's own per-firing discriminator (see `_baseline_seed`) -- keyed
    # "<symbol>:<setup_id>", DISTINCT from `pool_counts` above (that one bounds the CROSS-SYMBOL
    # pooling cap; this one counts how many times THIS symbol's own (symbol, setup_id) pair has
    # already fired THIS session, currently always 0 since a symbol is walked once and the
    # opening-range-break detector fires at most one signal per call).
    firing_counts: dict[str, int] = {}

    for symbol in members:
        if should_abort is not None and should_abort():
            break

        bars_5m = bar_store.merged_bars(symbol, "5m")
        session_5m = rth_session_slice(bars_5m, session_date)
        if not session_5m:
            absences.append(
                {"symbol": symbol, "reason": f"no 5m bars recorded for the {session_date} session"}
            )
            if progress is not None:
                progress({"symbol": symbol})
            continue

        baseline = baselines(
            bar_store, symbol, session_date,
            PLAYBOOK_BASELINE_SESSIONS, PLAYBOOK_MIN_BASELINE_SESSIONS,
        )
        if baseline["sessions"] < PLAYBOOK_MIN_BASELINE_SESSIONS or baseline["mbr"] == 0.0:
            absences.append(
                {
                    "symbol": symbol,
                    "reason": (
                        f"fewer than {PLAYBOOK_MIN_BASELINE_SESSIONS} prior sessions on file or "
                        f"MBR == 0 for {symbol} -- baseline too thin to detect against"
                    ),
                }
            )
            if progress is not None:
                progress({"symbol": symbol})
            continue

        bars_1m = bar_store.merged_bars(symbol, "1m")
        or_result = opening_range(
            bars_1m, bars_5m, session_date, PLAYBOOK_OR_MINUTES, PLAYBOOK_OR_MIN_1M_BARS
        )
        if or_result is None:
            absences.append(
                {
                    "symbol": symbol,
                    "reason": (
                        "no opening range could be built -- neither 1m nor 5m bars cover the "
                        "first 15 minutes of the session"
                    ),
                }
            )
            if progress is not None:
                progress({"symbol": symbol})
            continue

        signal, diagnostic = detect_opening_range_breaks(
            session_5m, or_result, baseline, symbol, session_date, index_bars, index_baseline,
            params, _prior_session_close(bars_5m, session_date),
        )
        if signal is not None:
            session_1m = rth_session_slice(bars_1m, session_date)
            forward, breached, measure_bars, tf_minutes = _measure_signal(signal, session_5m, session_1m)
            signal["forward"] = forward
            signal["invalidation_breached"] = breached
            signals.append(signal)

            pool_key = f"{signal['setup_id']}:{signal['side']}"
            count_so_far = pool_counts.get(pool_key, 0)
            pool_counts[pool_key] = count_so_far + 1
            if count_so_far < DESK_FORWARD_MAX_TOUCHES_PER_ROW:
                signal_pool.setdefault(pool_key, []).append(forward)
                sign = side_sign(signal["side"])
                firing_key = f"{symbol}:{signal['setup_id']}"
                firing_index = firing_counts.get(firing_key, 0)
                firing_counts[firing_key] = firing_index + 1
                rng = random.Random(
                    _baseline_seed(session_date, symbol, signal["setup_id"], firing_index)
                )
                k = min(1, len(measure_bars))  # this symbol's own capped signal count is <= 1
                for anchor_idx in _draw_anchor_indices(rng, len(measure_bars), k):
                    anchor_bar = measure_bars[anchor_idx]
                    baseline_pool.setdefault(pool_key, []).append(
                        _measure_from(
                            measure_bars, anchor_idx, anchor_bar.close, "close", tf_minutes, sign
                        )
                    )
            else:
                pool_beyond_cap[pool_key] = pool_beyond_cap.get(pool_key, 0) + 1
        if diagnostic is not None:
            diagnostics.append(diagnostic)
        if progress is not None:
            progress({"symbol": symbol})

    summary: dict[str, dict] = {}
    for pool_key, pooled_signals in signal_pool.items():
        signal_measures = _collect_measures(pooled_signals)
        pooled_baseline = baseline_pool.get(pool_key, [])
        baseline_measures = _collect_measures(pooled_baseline)
        summary[pool_key] = {
            key: {
                "signals": _avg_cell(*signal_measures[key]),
                "baseline": _avg_cell(*baseline_measures[key]),
            }
            for key in PLAYBOOK_SIGNAL_MEASURES
        }

    return {
        "session_date": session_date,
        "config_fingerprint": config_fingerprint,
        "playbook_input_signature": signature,
        # 2: every signal now carries `forward` + `invalidation_breached`, and the record gains
        # `baseline_anchors`/`summary`/`signals_beyond_cap` (see the module + this function's own
        # docstrings). The version DESCRIBES the shape; it is the new `rail_max_touches_per_row` key
        # inside `parameters` (see `playbook_parameters`) that makes the change actually RE-KEY: a
        # J-01-era record's own signature is untouched (its file is never rewritten), but a fresh
        # compute over the SAME session_date/bar content now hashes a DIFFERENT parameters blob and
        # so mints a genuinely new version rather than matching the old, unmeasured one.
        "payload_version": 2,
        "parameters": params,
        "register": PLAYBOOK_REGISTER,
        "signals": signals,
        "absences": absences,
        "diagnostics": diagnostics,
        "baseline_anchors": dict(baseline_pool),
        "summary": summary,
        "signals_beyond_cap": pool_beyond_cap,
    }


class PlaybookStore:
    """File-based store rooted at the playbook directory -- the ONE reader/writer. Mirrors
    ``desk_forward.ForwardStore``'s discipline: every load verifies a whole-record checksum
    (``PlaybookIntegrityError`` on any mismatch); the only mutation, ``record``, refuses an
    identical 2-pin key (``PlaybookAlreadyRecorded``, never a second file for the same key); no
    update/delete method exists anywhere on this class (structural -- it is simply never written).
    A changed parameter re-keys, so a re-compute records a NEW version and every older one is kept
    forever."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, playbook_id: str) -> Path:
        return self._root / f"{playbook_id}.json"

    def _load(self, path: Path) -> dict:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise PlaybookIntegrityError(
                f"playbook record file '{path.name}' is not parseable ({exc}) -- corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise PlaybookIntegrityError(
                f"playbook record file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise PlaybookIntegrityError(
                f"playbook record file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise PlaybookIntegrityError(
                f"playbook record file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        return meta

    @staticmethod
    def _id_for_key(session_date: str, playbook_input_signature: str) -> str:
        """The id a record with this 2-pin key is stored under -- a pure function of the key, so
        the key IS an address (the ``ForwardStore._id_for_key`` pattern, simplified: a playbook
        key's ``session_date`` is already the record's own field, with no external-id parsing step
        ``ForwardStore`` needs for its ``screen_id``-derived dates)."""
        checksum = _sha256(_canonical([session_date, playbook_input_signature]))[:12]
        return f"playbook-{session_date}-{checksum}"

    @staticmethod
    def _registered(meta: dict) -> dict:
        """One verified ``meta`` in the shape every read of this store hands back: fresh copies of
        the nested ``signals``/``absences``/``diagnostics``/``baseline_anchors``/``summary`` (the
        ``ForwardStore`` per-list-copy discipline, so a caller mutating what it received can never
        poison a later read). ``.get(..., default)`` on every J-02 field: a J-01-era record on disk
        carries none of them -- TC-11's honest-absence contract -- and must keep reading back
        verbatim rather than raising on a missing key."""
        return {
            **meta,
            "signals": [dict(s) for s in meta["signals"]],
            "absences": [dict(a) for a in meta["absences"]],
            "diagnostics": [dict(d) for d in meta.get("diagnostics", [])],
            "baseline_anchors": {
                key: [dict(m) for m in measures]
                for key, measures in meta.get("baseline_anchors", {}).items()
            },
            "summary": {key: dict(value) for key, value in meta.get("summary", {}).items()},
            "signals_beyond_cap": dict(meta.get("signals_beyond_cap", {})),
        }

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every recorded playbook record (each file verified), oldest first by
        ``(recorded_at, id)``, plus an EXPLICIT error row per file that failed verification."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                records.append(self._registered(self._load(path)))
            except PlaybookIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("recorded_at", ""), meta.get("id", "")))
        return records, errors

    def get(self, playbook_id: str) -> dict | None:
        """The record registered under ``playbook_id``, or ``None`` -- a direct read of that id's
        own deterministic path, never a walk (``ForwardStore.get``'s contract verbatim, including
        its refusal of an id that does not name a file directly inside this store)."""
        path = self._path(playbook_id)
        if path.parent != self._root:
            return None
        try:
            meta = self._load(path)
        except PlaybookIntegrityError:
            return None
        if meta.get("id") != playbook_id:
            return None
        return self._registered(meta)

    def _records_for_date(self, session_date: str) -> list[dict]:
        """Every recorded version for ``session_date``, ``(recorded_at, id)`` ascending -- narrowed
        by the filename's own date prefix (every version of a date shares it), membership decided
        by the verified ``session_date`` FIELD."""
        if not self._root.exists():
            return []
        records: list[dict] = []
        for path in sorted(self._root.glob(f"playbook-{session_date}-*.json")):
            try:
                meta = self._load(path)
            except PlaybookIntegrityError:
                continue
            if meta.get("session_date") != session_date:
                continue
            records.append(self._registered(meta))
        records.sort(key=lambda meta: (meta.get("recorded_at", ""), meta.get("id", "")))
        return records

    def find_by_key(self, session_date: str, playbook_input_signature: str) -> dict | None:
        """The already-recorded playbook record matching this EXACT 2-pin key, or ``None`` -- reads
        ONE file (the key determines the id, which determines the path); both fields are compared
        anyway rather than trusted to a 12-hex-digit address."""
        playbook_id = self._id_for_key(session_date, playbook_input_signature)
        record = self.get(playbook_id)
        if record is None:
            return None
        key = (session_date, playbook_input_signature)
        return record if (record["session_date"], record["playbook_input_signature"]) == key else None

    def newest_for_date(self, session_date: str) -> tuple[dict | None, int]:
        """The NEWEST recorded playbook record for ``session_date``, plus an honest count of every
        version ever recorded for it."""
        matching = self._records_for_date(session_date)
        if not matching:
            return None, 0
        return matching[-1], len(matching)

    def record(
        self,
        *,
        session_date: str,
        config_fingerprint: str,
        playbook_input_signature: str,
        payload_version: int,
        parameters: dict,
        register: str,
        signals: list[dict],
        absences: list[dict],
        diagnostics: list[dict],
        baseline_anchors: dict[str, list[dict]] | None = None,
        summary: dict[str, dict] | None = None,
        signals_beyond_cap: dict[str, int] | None = None,
    ) -> dict:
        """Persist ONE new playbook record (append-only). An identical 2-pin key raises
        ``PlaybookAlreadyRecorded``; a file already at this key's own deterministic path but
        failing its integrity check raises ``PlaybookIntegrityError`` -- never a silent overwrite
        (the ``ForwardStore.record`` refuse-loudly branch verbatim). ``baseline_anchors``/
        ``summary``/``signals_beyond_cap`` default to empty (J-02's measurement fields; a caller
        planting a J-01-shaped, pre-measurement record -- e.g. a fixture for the "measurement not
        recorded in this record" absence contract -- simply omits them)."""
        existing = self.find_by_key(session_date, playbook_input_signature)
        if existing is not None:
            raise PlaybookAlreadyRecorded(existing["id"])

        playbook_id = self._id_for_key(session_date, playbook_input_signature)
        if self._path(playbook_id).exists():
            raise PlaybookIntegrityError(
                f"playbook record file '{self._path(playbook_id).name}' already exists on disk "
                f"but failed its integrity check -- refusing to overwrite it (playbook records are "
                f"append-only and are never rewritten). Move or remove the damaged file explicitly "
                f"before re-recording this key."
            )
        meta = {
            "id": playbook_id,
            "session_date": session_date,
            "config_fingerprint": config_fingerprint,
            "playbook_input_signature": playbook_input_signature,
            "payload_version": payload_version,
            "parameters": dict(parameters),
            "register": register,
            "recorded_at": _iso_utc_now(),
            "signals": list(signals),
            "absences": list(absences),
            "diagnostics": list(diagnostics),
            "baseline_anchors": {
                key: list(measures) for key, measures in (baseline_anchors or {}).items()
            },
            "summary": {key: dict(value) for key, value in (summary or {}).items()},
            "signals_beyond_cap": dict(signals_beyond_cap or {}),
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(playbook_id).write_text(json.dumps(payload))
        return dict(meta)
