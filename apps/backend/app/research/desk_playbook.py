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
from datetime import datetime, timezone
from pathlib import Path

from .desk_forward import (
    DESK_FORWARD_BASELINE_SEED,
    DESK_FORWARD_HORIZONS_MINUTES,
    DESK_FORWARD_HORIZON_MEASURES,
    DESK_FORWARD_MEASURE_KEYS,
)
from .desk_playbook_detect import detect_opening_range_breaks
from .desk_playbook_features import baselines, opening_range, rth_session_slice
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
    "This record does not yet carry a measurement — forward returns, invalidation-breach, and the "
    "seeded random-anchor baseline are added by a later compute pass; no fills, no costs, and no "
    "probability, expectancy, edge, or significance claim are made anywhere on this payload"
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


def compute_playbook(universe_store, bar_store, config_fingerprint: str, session_date: str) -> dict:
    """Detect the opening-range-break family for EVERY member of the latest registered universe
    snapshot, on ``session_date``'s own recorded bars -- returns everything ``PlaybookStore.record``
    needs minus the store-assigned ``id``/``recorded_at`` (the ``compute_forward``/``compute_screen``
    contract shape: a PURE compute, never itself a store write).

    Session-honesty first: ``desk_sessions.refuse_if_not_a_session`` is checked before any bar is
    read for detection (no separate compute-manager/route layer exists yet this iteration, so this
    function plays that role) -- a non-session date raises ``PlaybookSessionRefused`` and NOTHING
    is walked. Per member: no 5m bars for the session, a thin/zero baseline, or no buildable opening
    range are each a disclosed ``absences`` row (never a crash, never a guess); everything else
    reaches the detector, which may add a signal, an ``ambiguous_outside_bar`` diagnostic, or
    neither (a legitimate "the setup did not form" outcome -- not an absence)."""
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

    for symbol in members:
        bars_5m = bar_store.merged_bars(symbol, "5m")
        session_5m = rth_session_slice(bars_5m, session_date)
        if not session_5m:
            absences.append(
                {"symbol": symbol, "reason": f"no 5m bars recorded for the {session_date} session"}
            )
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
            continue

        signal, diagnostic = detect_opening_range_breaks(
            session_5m, or_result, baseline, symbol, session_date, index_bars, index_baseline,
            params, _prior_session_close(bars_5m, session_date),
        )
        if signal is not None:
            signals.append(signal)
        if diagnostic is not None:
            diagnostics.append(diagnostic)

    return {
        "session_date": session_date,
        "config_fingerprint": config_fingerprint,
        "playbook_input_signature": signature,
        "payload_version": 1,
        "parameters": params,
        "register": PLAYBOOK_REGISTER,
        "signals": signals,
        "absences": absences,
        "diagnostics": diagnostics,
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
        the nested ``signals``/``absences``/``diagnostics`` lists (the ``ForwardStore``
        per-list-copy discipline, so a caller mutating what it received can never poison a later
        read)."""
        return {
            **meta,
            "signals": [dict(s) for s in meta["signals"]],
            "absences": [dict(a) for a in meta["absences"]],
            "diagnostics": [dict(d) for d in meta.get("diagnostics", [])],
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
    ) -> dict:
        """Persist ONE new playbook record (append-only). An identical 2-pin key raises
        ``PlaybookAlreadyRecorded``; a file already at this key's own deterministic path but
        failing its integrity check raises ``PlaybookIntegrityError`` -- never a silent overwrite
        (the ``ForwardStore.record`` refuse-loudly branch verbatim)."""
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
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(playbook_id).write_text(json.dumps(payload))
        return dict(meta)
