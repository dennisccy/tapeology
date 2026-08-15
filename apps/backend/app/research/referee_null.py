"""Era 6 "The Referee" (J-04) -- matched nulls: for every eligible Playbook occurrence, seeded
comparison anchors measured through the identical rail, so a future "beats chance" verdict can mean
"beats chance at a comparable time under identical measurement" (spec Sec4), never a strawman.

**What this module builds, spec-verbatim (docs/referee-statistical-spec.md Sec4).**
``referee-null-tod-v1`` draws ``K = REFEREE_NULL_ANCHORS_PER_OCCURRENCE`` seeded anchor bars per
eligible J-02 observation -- same symbol, same measurement series, same ToD bucket,
remaining-time-matched for fixed horizons (ToD-bucket-only for ``to_close``-family measures),
excluding the occurrence's own trigger/anchor bar, without replacement -- and measures each through
the imported ``desk_forward._measure_from`` at ``entry_kind="close"`` with the occurrence's own
side sign. ``referee-null-context-v1`` adds one more filter: the anchor's own close must also
satisfy a named backing-bucket predicate (e.g. ``at_wall``), evaluated through the imported
``desk_playbook_context.BandMapResolver``/``band_context_block`` over the RECORDED band map --
never re-derived locally (anti-goal 6, single source of truth).

**Why this module, and only this one, imports the context resolver.** ``docs/goal.md``'s Read-side
law names ``BandMapResolver`` as a sanctioned import for the Referee generally, but the
import-topology guard (``tests/test_referee_guards.py``) narrows the EXCEPTION to this module by
name -- every other ``referee_*.py`` module stays banned from ``desk_playbook_context`` (see that
test file's own comment for the exact cited sentence). Nothing here mutates, re-tunes, or feeds
back into ``desk_playbook_context.py``/``desk_playbook.py``/``desk_forward.py`` -- every import is
read-only, zero diff to any of them.

**"Eligible occurrence" is exactly one J-02 observation.** ``referee_evidence.playbook_observations``
already excludes every truncated/unmeasurable leaf (never emits an observation for one) and already
pools at the current ``(detector_basis, config_fingerprint)``, newest-per-date (T-6) -- so every
observation this module walks is, by construction, "primary-horizon-complete" for its OWN
``measure_key``. A null record is keyed ``(observation_id, null_spec_signature)`` -- ONE record per
(signal, measure_key, null-spec) triple, matching the Data Contract's own ``observation_id: str``
(singular) field, plus the per-anchor ``measure_key`` the served ``anchors[]`` schema carries
(redundant across a record's own anchors by construction, since every anchor is measured for that
SAME record's own ``measure_key`` -- self-describing rather than requiring a reader to look at the
top level).

**Reconstructing the occurrence's own measurement series, without re-deriving detection.** The J-02
observation contract deliberately does not expose the raw ``forward`` block (only
``anchor_ts = signal["trigger_ts"]``, the DETECTION-time epoch). To find the occurrence's own
measurement anchor bar (which may be a finer 1m bar mapped from the 5m trigger window -- see
``desk_playbook._measurement_anchor``, a detector-adjacent private helper this module deliberately
does NOT import), this module reads the underlying ``PlaybookStore`` RECORD directly (via the
``record_id``/signal-index encoded in ``observation_id``) for its own already-recorded
``forward["at_utc"]``, then locates the RTH session bar carrying that EXACT epoch -- finest series
(1m) first, then 5m, the same preference order the detector itself used. This is bar-epoch lookup
against already-recorded data, not a second implementation of any measurement or detection logic.

**Two draw-without-replacement helpers exist project-wide, on purpose (see NOTES in
``docs/phases/goal-referee-iter-5.md``).** This module imports ``desk_forward._draw_anchor_indices``
directly (it needs ``desk_forward._measure_from`` regardless, per the Read-side law) -- it does NOT
call ``referee_stats._draw_indices_without_replacement`` (that copy exists only because
``referee_stats.py`` carries its OWN stricter, estimand-agnostic import ban).

**Stream discipline.** No hypothesis exists yet at J-04 (registration is J-05) -- the seeded stream
recipe's ``hypothesis_id`` slot is filled with the null-spec id itself (``purpose="null-draw"``,
``session_date=<the occurrence's own session_date>``, ``i=<the observation_id>``), giving every
occurrence its own deterministic, reproducible sub-stream scoped under "this null variant, this
occurrence" -- the natural pre-registration analogue until J-05 mints real hypothesis ids (which
will scope their OWN null builds the same way, once they exist).

**Adapter-layer exclusion vs. stats-core fail-loud are deliberately different (see this module's
own inline comment on ``_measure_one_anchor``).** A non-finite ``_measure_from`` result here
EXCLUDES-and-COUNTS that one anchor (T-5's normal, disclosed "unmeasurable" pattern) -- it never
excludes the whole occurrence and never raises, unlike ``referee_stats.py``'s new door guard, which
RAISES because at that layer a non-finite value can only mean an upstream bug."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import threading
import uuid
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from ..config import CONFIG, Config
from .bars import BarStore
from .desk_forward import DESK_FORWARD_HORIZONS_MINUTES, _draw_anchor_indices, _measure_from
from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
from .desk_playbook_context import (
    AT_WALL,
    PLAYBOOK_CONTEXT_ALGORITHM_VERSION,
    PLAYBOOK_CONTEXT_BACKING_BUCKETS,
    BandMapResolver,
    band_context_block,
)
from .desk_playbook_features import rth_session_slice, side_sign
from .referee_evidence import (
    _HORIZON_LABELS,
    _epoch_from_iso,
    _iso,
    _resolve_leaf,
    playbook_observations,
)
from .referee_stats import referee_stream
from .routes import get_bar_store

__all__ = [
    "REFEREE_NULL_ANCHORS_PER_OCCURRENCE",
    "REFEREE_TOD_BUCKETS",
    "REFEREE_NULL_TOD_SPEC_ID",
    "REFEREE_NULL_CONTEXT_SPEC_ID",
    "REFEREE_TEST_PERM_SPEC_ID",
    "resolve_referee_null_dir",
    "resolve_referee_null_log_dir",
    "tod_bucket_for_epoch",
    "null_tod_spec_parameters",
    "null_tod_spec_signature",
    "null_context_spec_parameters",
    "null_context_spec_signature",
    "test_perm_spec_parameters",
    "test_perm_spec_signature",
    "NullIntegrityError",
    "NullAlreadyRecorded",
    "resolve_occurrence_backing_bucket",
    "RefereeNullStore",
    "RefereeNullRunStore",
    "record_null_run",
    "build_null_record",
    "RefereeNullComputeManager",
    "run_null_build_and_record",
]

# === spec Sec1: pre-registered constants (module constants, never Config fields) ====================

REFEREE_NULL_ANCHORS_PER_OCCURRENCE: int = 4

# Card 6.5's ToD buckets, verbatim (spec Sec0/Sec1), ET wall-clock, half-open [start, end).
REFEREE_TOD_BUCKETS: tuple[tuple[str, str, str], ...] = (
    ("open", "09:30", "10:30"),
    ("mid", "10:30", "15:00"),
    ("close", "15:00", "16:00"),
)

REFEREE_NULL_TOD_SPEC_ID: str = "referee-null-tod-v1"
REFEREE_NULL_CONTEXT_SPEC_ID: str = "referee-null-context-v1"
REFEREE_TEST_PERM_SPEC_ID: str = "referee-test-perm-v1"

_NULL_SPEC_IDS = frozenset({REFEREE_NULL_TOD_SPEC_ID, REFEREE_NULL_CONTEXT_SPEC_ID})

_NULL_DIR_ENV = "TAPEOLOGY_DESK_REFEREE_NULL_DIR"
_NULL_LOG_DIR_ENV = "TAPEOLOGY_DESK_REFEREE_NULL_LOG_DIR"

# The Referee's own ET zone constant -- the `desk_playbook_features.py`/`referee_evidence.py`
# per-module idiom: each module that needs ET wall-clock resolution owns a private ZoneInfo
# constant rather than reaching into another module's private one.
_ET_ZONE = ZoneInfo("America/New_York")
_RTH_CLOSE = time(16, 0)


def resolve_referee_null_dir(desk_universe_dir_resolved: str) -> str:
    """The null store's directory: ``TAPEOLOGY_DESK_REFEREE_NULL_DIR`` if set, else a
    ``referee_null`` SIBLING of the caller's own already-resolved universe directory (the
    ``resolve_desk_forward_dir`` pattern verbatim). Deliberately NOT a ``Config`` field."""
    override = os.environ.get(_NULL_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "referee_null")


def resolve_referee_null_log_dir(desk_universe_dir_resolved: str) -> str:
    """The null run-ledger's directory -- its own ``_LOG_DIR``-family sibling default, the
    ``resolve_desk_playbook_log_dir`` pattern verbatim. Deliberately NOT a ``Config`` field."""
    override = os.environ.get(_NULL_LOG_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "referee_null_runs")


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum/signature in this module hashes -- the SAME
    encoding every other desk/referee store hashes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


# === ToD bucket resolution (spec Sec0) ===============================================================


def tod_bucket_for_epoch(epoch: float) -> str | None:
    """The ``REFEREE_TOD_BUCKETS`` bucket ``epoch`` (converted ET, DST-correct via ``zoneinfo``)
    falls in, half-open ``[start, end)`` -- ``None`` outside RTH (09:30-16:00 ET), an honest
    non-membership rather than a fabricated bucket."""
    wall = datetime.fromtimestamp(epoch, tz=_ET_ZONE).time()
    for name, start, end in REFEREE_TOD_BUCKETS:
        start_h, start_m = (int(p) for p in start.split(":"))
        end_h, end_m = (int(p) for p in end.split(":"))
        if time(start_h, start_m) <= wall < time(end_h, end_m):
            return name
    return None


def _session_close_epoch(session_date: str) -> float:
    """The UTC epoch RTH close (16:00 ET) resolves to on ``session_date`` -- DST-correct by
    construction. The literal wall-clock basis TC-4 hand-verifies remaining-time eligibility
    against (e.g. "60 min remaining" at 15:00 ET before a 16:00 close)."""
    day = date.fromisoformat(session_date)
    return datetime.combine(day, _RTH_CLOSE, tzinfo=_ET_ZONE).timestamp()


# === spec ids: three named, signature-bearing parameter-blob hashes ==================================
#
# Each hashes its OWN full parameter blob, read at call time (a monkeypatched constant genuinely
# moves both the blob and the signature -- counter-tested). File placement here (rather than a
# separate shared helper) is an implementation choice named as such in the iter-5 spec; the
# behavior contract (own blob, own hash, stable/reproducible, changes on any parameter change) is
# fixed, not this placement.


def null_tod_spec_parameters() -> dict:
    """``referee-null-tod-v1``'s own full parameter blob (spec Sec4.1)."""
    return {
        "id": REFEREE_NULL_TOD_SPEC_ID,
        "k": REFEREE_NULL_ANCHORS_PER_OCCURRENCE,
        "tod_buckets": [list(bucket) for bucket in REFEREE_TOD_BUCKETS],
        "horizons_minutes": [list(pair) for pair in DESK_FORWARD_HORIZONS_MINUTES],
        "entry_kind": "close",
        "exclude_own_trigger_bar": True,
        "remaining_time_matched_for_fixed_horizons": True,
        "tod_bucket_only_for_to_close_family": True,
        "without_replacement": True,
    }


def null_tod_spec_signature() -> str:
    return _sha256(_canonical(null_tod_spec_parameters()))[:16]


def null_context_spec_parameters() -> dict:
    """``referee-null-context-v1``'s own full parameter blob (spec Sec4.2): everything
    ``referee-null-tod-v1`` requires, PLUS the backing-bucket predicate machinery."""
    blob = null_tod_spec_parameters()
    blob["id"] = REFEREE_NULL_CONTEXT_SPEC_ID
    blob["context_algorithm_version"] = PLAYBOOK_CONTEXT_ALGORITHM_VERSION
    blob["backing_buckets"] = list(PLAYBOOK_CONTEXT_BACKING_BUCKETS)
    blob["risk_source"] = "paired_signal"
    return blob


def null_context_spec_signature() -> str:
    return _sha256(_canonical(null_context_spec_parameters()))[:16]


def test_perm_spec_parameters() -> dict:
    """``referee-test-perm-v1``'s own full parameter blob (spec Sec1/Sec3.4) -- describes
    ``referee_stats.permutation_test``'s own procedure (weights formula identity, sidedness
    handling, enumeration rule, p convention); minted HERE so J-05 hypothesis records can reference
    it immutably before any hypothesis exists. Exactly spec Sec1's stated contents -- no additional
    input invented."""
    from .referee_stats import REFEREE_B, REFEREE_ENUMERATION_THRESHOLD

    return {
        "id": REFEREE_TEST_PERM_SPEC_ID,
        "weights_formula": (
            "A/C: w_s = n_s*K_s/(n_s+K_s) (harmonic); B: w_s = n1_s*n2_s/(n1_s+n2_s) -- the SAME "
            "formula, group-size-1 times group-size-2 over their sum"
        ),
        "sidedness_handling": ["greater", "less", "two-sided"],
        "enumeration_rule": (
            f"full enumeration when the total per-session-combination product <= "
            f"{REFEREE_ENUMERATION_THRESHOLD}, else {REFEREE_B} seeded draws"
        ),
        "p_convention": "p = (1 + #{T* extreme}) / (draws + 1) -- the Phipson-Smyth +1 convention",
    }


def test_perm_spec_signature() -> str:
    return _sha256(_canonical(test_perm_spec_parameters()))[:16]


# === eligibility: which anchor bars a given occurrence's null may draw from ==========================


def _required_horizon_minutes(measure_key: str) -> float | None:
    """The remaining-time requirement for ``measure_key`` (spec Sec4.1) -- ``None`` means
    ToD-bucket-only eligibility (the ``to_close``-family session-end trio: ``to_close``,
    ``mdd_long``, ``mdd_short``, unsuffixed). Derived from ``DESK_FORWARD_HORIZONS_MINUTES`` /
    ``_HORIZON_LABELS`` (imported from ``referee_evidence.py``) rather than spelled out a second
    time, so a rail horizon addition can never silently desync here."""
    horizon_minutes = dict(DESK_FORWARD_HORIZONS_MINUTES)
    if measure_key in _HORIZON_LABELS:
        return float(horizon_minutes[measure_key])
    if measure_key in ("to_close", "mdd_long", "mdd_short"):
        return None
    for prefix in ("mdd_long_", "mdd_short_"):
        if measure_key.startswith(prefix):
            suffix = measure_key[len(prefix) :]
            if suffix in _HORIZON_LABELS:
                return float(horizon_minutes[suffix])
    raise ValueError(f"unknown DESK_FORWARD_MEASURE_KEYS entry {measure_key!r}")


def _parse_observation_id(observation_id: str) -> tuple[str, int, str]:
    """``(record_id, signal_index, measure_key)`` -- the inverse of
    ``referee_evidence._playbook_file_projection``'s own
    ``f"playbook:{record['id']}:{index}:{measure_key}"`` construction."""
    prefix, record_id, index_str, measure_key = observation_id.split(":", 3)
    if prefix != "playbook":
        raise ValueError(f"not a playbook observation id: {observation_id!r}")
    return record_id, int(index_str), measure_key


def _locate_measurement_series(
    bar_store: BarStore, symbol: str, session_date: str, at_epoch: float
) -> tuple[list, int, int] | None:
    """Reconstructs ``(measure_bars, anchor_index, tf_minutes)`` for an already-recorded signal's
    own forward measurement, by locating the RTH session bar whose epoch matches the signal's own
    recorded ``forward["at_utc"]`` EXACTLY -- finest series (1m) first, then 5m, the SAME
    preference order ``desk_playbook._measurement_anchor`` used to build that measurement in the
    first place. Returns ``None`` when neither series carries a bar at that exact epoch (an honest
    "cannot be located" case -- see ``build_null_record``'s own handling)."""
    for tf, tf_minutes in (("1m", 1), ("5m", 5)):
        bars = rth_session_slice(bar_store.merged_bars(symbol, tf), session_date)
        for idx, bar in enumerate(bars):
            if bar.epoch == at_epoch:
                return bars, idx, tf_minutes
    return None


def _eligible_anchor_positions(
    measure_bars: list,
    trigger_index: int,
    bucket: str,
    required_minutes: float | None,
    session_close_epoch: float,
) -> list[int]:
    """Every index in ``measure_bars`` (excluding ``trigger_index`` itself) whose OWN epoch falls
    in the occurrence's ToD ``bucket`` and (for fixed-horizon primaries) leaves ``>= required_
    minutes`` of session remaining, measured as literal wall-clock distance to the session's own
    16:00 ET close (spec Sec4.1's remaining-time rule; TC-4's own hand-verified boundary: 60 min
    remain at 15:00 ET before a 16:00 close, 55 min at 15:05 ET). Reads only each candidate bar's
    OWN already-recorded epoch -- lookahead-clean by construction (TC-7)."""
    positions: list[int] = []
    for idx, bar in enumerate(measure_bars):
        if idx == trigger_index:
            continue
        if tod_bucket_for_epoch(bar.epoch) != bucket:
            continue
        if required_minutes is not None:
            remaining_minutes = (session_close_epoch - bar.epoch) / 60.0
            if remaining_minutes < required_minutes:
                continue
        positions.append(idx)
    return positions


def _window_end_index(start_index: int, required_minutes: float | None, tf_minutes: int, last: int) -> int:
    """The (possibly truncated) end index of one measurement's own window, for the overlap
    disclosure below -- mirrors ``_measure_from``'s own truncation rule (``min(target, last)``)
    without recomputing anything the rail already owns; ``to_close``-family measures (``required_
    minutes is None``) run to the session's own last bar by definition."""
    if required_minutes is None:
        return last
    offset = int(required_minutes // tf_minutes)
    return min(start_index + offset, last)


def _window_overlap_fraction(occ_start: int, occ_end: int, anchor_start: int, anchor_end: int) -> float:
    """The fraction of the OCCURRENCE's own measurement window that ``anchor``'s window overlaps
    (spec Sec4.1's same-session power-cost disclosure) -- both windows expressed as bar-index
    ranges on the SAME ``measure_bars`` array, so index arithmetic is exact."""
    occ_len = occ_end - occ_start
    if occ_len <= 0:
        return 0.0
    overlap = min(occ_end, anchor_end) - max(occ_start, anchor_start)
    return max(0.0, overlap) / occ_len


# === exceptions =======================================================================================


class NullIntegrityError(Exception):
    """An on-disk null-record file failed its checksum verification on load -- corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated record)."""


class NullAlreadyRecorded(Exception):
    """A null record with this EXACT ``(observation_id, null_spec_signature)`` key is already
    registered. Null records are immutable and append-only -- a re-run over identical inputs reuses
    the existing record, never a second file."""

    def __init__(self, existing_id: str) -> None:
        self.existing_id = existing_id
        super().__init__(
            f"a null record with this exact key is already recorded as '{existing_id}' -- null "
            f"records are immutable and are never re-recorded"
        )


# === the anchor-measurement adapter: non-finite exclusion, T-5's normal disclosed pattern ============


def _measure_one_anchor(
    measure_bars: list, anchor_index: int, tf_minutes: int, sign: float, measure_key: str
) -> tuple[float | None, dict]:
    """Measures ONE anchor bar through the imported rail (``entry = anchor bar close``,
    ``entry_kind="close"``, spec Sec4.1) and extracts ``measure_key``'s own value via the SAME
    ``_resolve_leaf`` extraction ``referee_evidence.py`` already owns (single source of truth --
    never a second horizon/MDD extraction). Returns ``(value_or_None, forward_dict)``: ``None``
    means excluded (either the leaf itself is unmeasurable/truncated, OR the extracted value is
    non-finite) -- the caller counts this, never substitutes a fallback (T-5).

    Deliberately EXCLUDES rather than raises, unlike ``referee_stats.py``'s new door guard: at this
    layer a non-finite/unmeasurable result is a normal, per-anchor outcome this adapter still knows
    which occurrence it belongs to -- the stats core has no such identity left to attach a
    disclosure to once values reach it."""
    bar = measure_bars[anchor_index]
    forward = _measure_from(measure_bars, anchor_index, bar.close, "close", tf_minutes, sign)
    value, excluded = _resolve_leaf(measure_key, forward)
    if excluded or value is None:
        return None, forward
    if not math.isfinite(value):
        return None, forward
    return value, forward


# === the core builder: shared by both null-spec variants =============================================


def build_null_record(
    observation: dict,
    *,
    null_spec_id: str,
    playbook_store: PlaybookStore,
    bar_store: BarStore,
    config_fingerprint: str,
    backing_bucket: str = AT_WALL,
    context_resolver: BandMapResolver | None = None,
    record_cache: dict[str, dict] | None = None,
) -> dict:
    """Builds ONE null record for ``observation`` (a single J-02 playbook-family observation) under
    ``null_spec_id`` -- the full field shape ``runs/goal-session-referee/state/blueprint.md``'s
    iter-5 note pins. ``context_resolver`` is REQUIRED (and ``compute=False``, lookup-only -- GETs
    never compute, T-8) for ``REFEREE_NULL_CONTEXT_SPEC_ID``; ignored for the ToD variant.
    ``record_cache`` (keyed by raw ``PlaybookStore`` record id) lets a caller walking many
    observations from the SAME record avoid re-verifying its file more than once; a fresh dict is
    used when the caller passes none."""
    if null_spec_id not in _NULL_SPEC_IDS:
        raise ValueError(f"unknown null_spec_id {null_spec_id!r} -- expected one of {sorted(_NULL_SPEC_IDS)}")
    is_context = null_spec_id == REFEREE_NULL_CONTEXT_SPEC_ID
    if is_context and context_resolver is None:
        raise ValueError("null_spec_id=referee-null-context-v1 requires a context_resolver")

    observation_id = observation["observation_id"]
    symbol = observation["symbol"]
    session_date = observation["session_date"]
    side = observation["side"]
    measure_key = observation["measure_key"]
    trigger_epoch = _epoch_from_iso(observation["anchor_ts"])
    bucket = tod_bucket_for_epoch(trigger_epoch)

    cache = {} if record_cache is None else record_cache
    record_id, signal_index, parsed_measure_key = _parse_observation_id(observation_id)
    assert parsed_measure_key == measure_key  # the id and the field must always agree (belt-and-braces)
    record = cache.get(record_id)
    if record is None:
        record = playbook_store.get(record_id)
        cache[record_id] = record
    signal = record["signals"][signal_index] if record is not None else None

    null_spec_signature = (
        null_context_spec_signature() if is_context else null_tod_spec_signature()
    )
    null_record_id = _sha256(_canonical([observation_id, null_spec_signature]))[:16]

    empty_result = {
        "null_record_id": null_record_id,
        "null_spec_id": null_spec_id,
        "null_spec_signature": null_spec_signature,
        "observation_id": observation_id,
        "symbol": symbol,
        "session_date": session_date,
        "side": side,
        "tod_bucket": bucket,
        "k_requested": REFEREE_NULL_ANCHORS_PER_OCCURRENCE,
        "k_drawn": 0,
        "eligible_count": 0,
        "excluded": True,
        "anchors": [],
        "mean_window_overlap": None,
        "non_finite_excluded_count": 0,
        "backing_bucket_eligibility_rate": None,
        "context_algorithm_version": PLAYBOOK_CONTEXT_ALGORITHM_VERSION if is_context else None,
        "provenance": {"config_fingerprint": config_fingerprint, "computed_at": _iso_utc_now()},
    }

    if signal is None or bucket is None:
        # An occurrence whose own trigger falls outside every named bucket, or whose source signal
        # cannot be re-read, can draw no matched anchors at all -- excluded and counted (T-5).
        return empty_result

    located = _locate_measurement_series(bar_store, symbol, session_date, trigger_epoch)
    if located is None:
        return empty_result
    measure_bars, trigger_index, tf_minutes = located
    required_minutes = _required_horizon_minutes(measure_key)
    session_close_epoch = _session_close_epoch(session_date)

    tod_eligible = _eligible_anchor_positions(
        measure_bars, trigger_index, bucket, required_minutes, session_close_epoch
    )

    backing_rate: float | None = None
    if not is_context:
        eligible_positions = tod_eligible
    else:
        tod_eligible_count = len(tod_eligible)
        entry = signal.get("entry")
        invalidation = signal.get("invalidation_price")
        risk_bps = (
            abs(entry - invalidation) / entry * 10_000.0
            if isinstance(entry, (int, float))
            and isinstance(invalidation, (int, float))
            and entry != 0
            else None
        )
        map_result = context_resolver.resolve(symbol, trigger_epoch)
        if map_result is None or tod_eligible_count == 0:
            # "A cell whose anchors cannot be found is an exclusion disclosure, never a
            # substitution" (spec Sec4.2) -- an unresolvable map means NO candidate can be
            # VERIFIED to satisfy the predicate, so the honest eligible population is empty, not a
            # fallback to the unfiltered ToD population.
            #
            # iter-6 rider (reviewer NOTE carried from iteration 5): when `tod_eligible_count == 0`
            # but `map_result` WAS resolved, zero candidates were even CHECKED against the
            # predicate -- `None` ("nothing measurable") is the honest reading, not `0.0` (which
            # implies a measured 0% match rate over a real, non-empty candidate population). The
            # genuine `len(matched) / tod_eligible_count == 0.0` case (real candidates checked,
            # zero matched) is unaffected -- it stays in the `else` branch below, untouched.
            eligible_positions = []
            backing_rate = None
        else:
            matched: list[int] = []
            for idx in tod_eligible:
                anchor_close = measure_bars[idx].close
                context = band_context_block(
                    map_result, anchor_close, side, risk_bps=risk_bps, risk_source="paired_signal"
                )
                if context["backing_bucket"] == backing_bucket:
                    matched.append(idx)
            eligible_positions = matched
            backing_rate = len(matched) / tod_eligible_count

    eligible_count = len(eligible_positions)
    if eligible_count == 0:
        empty_result["backing_bucket_eligibility_rate"] = backing_rate
        return empty_result

    k_drawn = min(REFEREE_NULL_ANCHORS_PER_OCCURRENCE, eligible_count)
    stream = referee_stream(null_spec_id, "null-draw", session_date=session_date, i=observation_id)
    drawn = _draw_anchor_indices(stream, eligible_count, k_drawn)
    anchor_indices = [eligible_positions[j] for j in drawn]

    sign = side_sign(side)
    occ_end = _window_end_index(trigger_index, required_minutes, tf_minutes, len(measure_bars) - 1)
    last = len(measure_bars) - 1

    anchors: list[dict] = []
    overlaps: list[float] = []
    non_finite_excluded = 0
    for anchor_index in anchor_indices:
        value, _forward = _measure_one_anchor(measure_bars, anchor_index, tf_minutes, sign, measure_key)
        if value is None:
            non_finite_excluded += 1
            continue
        anchor_end = _window_end_index(anchor_index, required_minutes, tf_minutes, last)
        overlap = _window_overlap_fraction(trigger_index, occ_end, anchor_index, anchor_end)
        overlaps.append(overlap)
        anchors.append(
            {
                "anchor_ts": _iso(measure_bars[anchor_index].epoch),
                "measure_key": measure_key,
                "value": value,
                "window_overlap_fraction": overlap,
                "backing_bucket_match": True if is_context else None,
            }
        )

    return {
        "null_record_id": null_record_id,
        "null_spec_id": null_spec_id,
        "null_spec_signature": null_spec_signature,
        "observation_id": observation_id,
        "symbol": symbol,
        "session_date": session_date,
        "side": side,
        "tod_bucket": bucket,
        "k_requested": REFEREE_NULL_ANCHORS_PER_OCCURRENCE,
        "k_drawn": k_drawn,
        "eligible_count": eligible_count,
        "excluded": False,
        "anchors": anchors,
        "mean_window_overlap": (math.fsum(overlaps) / len(overlaps)) if overlaps else None,
        "non_finite_excluded_count": non_finite_excluded,
        "backing_bucket_eligibility_rate": backing_rate,
        "context_algorithm_version": PLAYBOOK_CONTEXT_ALGORITHM_VERSION if is_context else None,
        "provenance": {"config_fingerprint": config_fingerprint, "computed_at": _iso_utc_now()},
    }


# === iter-7 (J-06): the occurrence's OWN context-cell membership, for Estimand B ======================
#
# Estimand B (spec Sec3.2, "among occurrences of setup S, do occurrences in context cell C differ
# from same-setup occurrences outside C?") needs, per OCCURRENCE, whether ITS OWN entry satisfies a
# named backing-bucket predicate -- a live band-map resolve, exactly the operation
# `build_null_record`'s context branch already performs for an ANCHOR bar above, applied here to the
# occurrence itself instead. `referee_adjudicate.py` (J-06) is banned from importing
# `desk_playbook_context` directly (the import-topology guard narrows that exception to THIS module
# alone, per this file's own module docstring) -- it reaches this through the module boundary below
# instead, mirroring how `referee_registry.py` already imports `PLAYBOOK_CONTEXT_BACKING_BUCKETS`
# transitively rather than importing `desk_playbook_context` itself. Nothing here mutates,
# re-tunes, or feeds back into `desk_playbook_context.py`/`desk_playbook.py` -- a read-only lookup,
# `compute=False` context resolvers only (GETs/evaluations never compute a NEW band map, T-8).


def resolve_occurrence_backing_bucket(
    signal: dict, symbol: str, trigger_epoch: float, price: float, side: str,
    context_resolver: BandMapResolver,
) -> str | None:
    """The occurrence's OWN ``backing_bucket`` at ``price`` (its own entry, or a close-anchored
    re-measurement price for the entry-basis sensitivity) -- the SAME ``band_context_block()`` call
    ``build_null_record``'s context branch already makes for an anchor bar's own close, applied here
    to the OCCURRENCE itself. ``None`` when the band map cannot be resolved AT ALL for this
    ``(symbol, trigger_epoch)`` (an honest "not evaluable" absence -- the caller excludes and counts
    this occurrence, never substituting a fallback bucket, T-5)."""
    entry = signal.get("entry")
    invalidation = signal.get("invalidation_price")
    risk_bps = (
        abs(entry - invalidation) / entry * 10_000.0
        if isinstance(entry, (int, float))
        and isinstance(invalidation, (int, float))
        and entry != 0
        else None
    )
    map_result = context_resolver.resolve(symbol, trigger_epoch)
    if map_result is None:
        return None
    context = band_context_block(
        map_result, price, side, risk_bps=risk_bps, risk_source="paired_signal"
    )
    return context["backing_bucket"]


# === the append-only null store =======================================================================


class RefereeNullStore:
    """File-based store rooted at the resolved null directory -- the ONE reader/writer. Mirrors
    ``desk_forward.ForwardStore``'s discipline exactly: every load verifies a whole-record checksum
    (``NullIntegrityError`` on any mismatch); the only mutation, ``record``, refuses an identical
    ``(observation_id, null_spec_signature)`` key (``NullAlreadyRecorded``, never a second file for
    the same key); no update/delete method exists anywhere on this class (structural -- source-scan
    guard-tested in ``tests/test_referee_null.py``)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, null_record_id: str) -> Path:
        return self._root / f"{null_record_id}.json"

    def _load(self, path: Path) -> dict:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise NullIntegrityError(
                f"null record file '{path.name}' is not parseable ({exc}) -- corrupted or tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise NullIntegrityError(
                f"null record file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise NullIntegrityError(
                f"null record file '{path.name}' failed its integrity check (checksum mismatch) "
                f"-- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise NullIntegrityError(
                f"null record file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every recorded null record (each file verified), oldest first, plus an EXPLICIT error
        row per file that failed verification."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                records.append(dict(self._load(path)))
            except NullIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("provenance", {}).get("computed_at", ""), meta.get("null_record_id", "")))
        return records, errors

    def get(self, null_record_id: str) -> dict | None:
        """The record registered under ``null_record_id``, or ``None`` -- a direct read of that
        id's own deterministic path, never a walk (``ForwardStore.get``'s contract verbatim,
        including its refusal of an id that does not name a file directly inside this store)."""
        path = self._path(null_record_id)
        if path.parent != self._root:
            return None
        try:
            meta = self._load(path)
        except NullIntegrityError:
            return None
        if meta.get("null_record_id") != null_record_id:
            return None
        return dict(meta)

    def find_by_key(self, observation_id: str, null_spec_signature: str) -> dict | None:
        """The already-recorded null record matching this EXACT ``(observation_id, null_spec_
        signature)`` key, or ``None`` -- the append-only dedup lookup ``record`` itself uses, also
        usable standalone by a compute walker deciding whether to skip an already-built record."""
        null_record_id = _sha256(_canonical([observation_id, null_spec_signature]))[:16]
        record = self.get(null_record_id)
        if record is None:
            return None
        key = (record.get("observation_id"), record.get("null_spec_signature"))
        return record if key == (observation_id, null_spec_signature) else None

    def record(self, fields: dict) -> dict:
        """Persist ONE new null record (append-only). ``fields`` is exactly a ``build_null_record``
        return value. An identical key raises ``NullAlreadyRecorded``; a file already at this key's
        own deterministic path but failing its integrity check raises ``NullIntegrityError`` --
        never a silent overwrite (the ``ForwardStore.record`` refuse-loudly branch verbatim)."""
        null_record_id = fields["null_record_id"]
        existing = self.find_by_key(fields["observation_id"], fields["null_spec_signature"])
        if existing is not None:
            raise NullAlreadyRecorded(existing["null_record_id"])
        path = self._path(null_record_id)
        if path.exists():
            raise NullIntegrityError(
                f"null record file '{path.name}' already exists on disk but failed its integrity "
                f"check -- refusing to overwrite it (null records are append-only and are never "
                f"rewritten). Move or remove the damaged file explicitly before re-recording this "
                f"key."
            )
        record = {"meta": dict(fields)}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))
        return dict(fields)


# === the durable run ledger (terminal-state-only writes) =============================================


class RefereeNullRunStore:
    """File-based store rooted at the resolved null-run-log directory -- the ONE reader/writer.
    Mirrors ``desk_forward_log.ForwardRunStore``'s discipline: a checksum-verified load on every
    read, ``record()`` the only mutation, no update/delete function anywhere, no content-based
    dedup (every terminal run is its own genuinely distinct event). Unlike ``desk_playbook_log.py``
    (whose ``outcome`` enum excludes cancel entirely), this ledger DOES record a ``"cancelled"``
    terminal state -- the Data Contract's own ``state`` enum requires it, and a null build's cancel
    is a real, reportable attempt outcome (some observations may already be durably recorded)."""

    _TERMINAL_STATES = ("completed", "failed", "cancelled")

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.json"

    def _load(self, path: Path) -> dict:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise NullIntegrityError(
                f"null run record file '{path.name}' is not parseable ({exc}) -- corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise NullIntegrityError(
                f"null run record file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise NullIntegrityError(
                f"null run record file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise NullIntegrityError(
                f"null run record file '{path.name}' does not carry the expected record shape -- "
                f"corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                records.append(dict(self._load(path)))
            except NullIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("started_at", ""), meta.get("run_id", "")))
        return records, errors

    def list_for_null_spec(self, null_spec_id: str) -> list[dict]:
        records, _errors = self.list()
        return [record for record in records if record.get("null_spec_id") == null_spec_id]

    def record(
        self,
        *,
        null_spec_id: str,
        state: str,
        started_at: str,
        finished_at: str,
        progress: dict,
        error: str | None,
    ) -> dict:
        if state not in self._TERMINAL_STATES:
            raise ValueError(f"invalid terminal state {state!r} -- must be one of {self._TERMINAL_STATES}")
        date_prefix = started_at[:10]
        run_id = f"refereenullrun-{date_prefix}-{uuid.uuid4().hex[:12]}"
        while self._path(run_id).exists():
            run_id = f"refereenullrun-{date_prefix}-{uuid.uuid4().hex[:12]}"
        meta = {
            "run_id": run_id,
            "null_spec_id": null_spec_id,
            "state": state,
            "started_at": started_at,
            "finished_at": finished_at,
            "progress": dict(progress),
            "error": error,
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(run_id).write_text(json.dumps(payload))
        return dict(meta)


def record_null_run(
    store: RefereeNullRunStore,
    *,
    null_spec_id: str,
    state: str,
    started_at: str,
    finished_at: str,
    progress: dict,
    error: str | None,
) -> dict:
    """THE single shared writer -- called AT MOST once per run, at its own terminal state, from
    inside ``run_null_build_and_record`` (the ``record_forward_run``/``record_playbook_run``
    precedent: one named free function per store, never a call site invoking the method directly)."""
    return store.record(
        null_spec_id=null_spec_id, state=state, started_at=started_at, finished_at=finished_at,
        progress=progress, error=error,
    )


# === the compute walker + single-flight-per-null-spec manager ========================================


def run_null_build_and_record(
    playbook_store: PlaybookStore,
    bar_store: BarStore,
    config: Config,
    null_store: RefereeNullStore,
    null_spec_id: str,
    *,
    backing_bucket: str = AT_WALL,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
    run_store: RefereeNullRunStore | None = None,
) -> dict:
    """Walks every eligible J-02 observation (``referee_evidence.playbook_observations``) and
    records (or reuses) ONE null record per observation under ``null_spec_id`` -- resumable and
    idempotent: an observation already recorded for this EXACT key is skipped with zero re-write
    (TC-8), so a re-run over an unchanged corpus writes zero new files. ``should_abort`` is checked
    BEFORE each observation's own build starts, so a cancel never leaves a half-written record for
    one (TC-20) -- everything already recorded for OTHER, already-processed observations stays on
    disk, exactly as the idempotent-reuse contract intends.

    If ``run_store`` is given, persists exactly ONE durable run-ledger row at this run's own
    terminal outcome (``"completed"``/``"failed"``/``"cancelled"``) -- terminal-state-only, never a
    ``"running"`` row (the shipped compute-manager pattern's own discipline)."""
    if null_spec_id not in _NULL_SPEC_IDS:
        raise ValueError(f"unknown null_spec_id {null_spec_id!r} -- expected one of {sorted(_NULL_SPEC_IDS)}")
    started_at = _iso_utc_now()
    config_fingerprint = config.config_fingerprint()
    is_context = null_spec_id == REFEREE_NULL_CONTEXT_SPEC_ID
    context_resolver = BandMapResolver(bar_store, config, compute=False) if is_context else None

    def _log(*, state: str, done: int, total: int, error: str | None) -> None:
        if run_store is None:
            return
        record_null_run(
            run_store, null_spec_id=null_spec_id, state=state, started_at=started_at,
            finished_at=_iso_utc_now(), progress={"done": done, "total": total}, error=error,
        )

    try:
        observations = playbook_observations(playbook_store, config_fingerprint)["observations"]
    except Exception as exc:  # noqa: BLE001 -- logged, then re-raised verbatim, never swallowed
        _log(state="failed", done=0, total=0, error=str(exc))
        raise

    total = len(observations)
    recorded = 0
    reused = 0
    excluded = 0
    record_cache: dict[str, dict] = {}
    cancelled = False

    try:
        for done, observation in enumerate(observations):
            if should_abort is not None and should_abort():
                cancelled = True
                break
            null_spec_signature = (
                null_context_spec_signature() if is_context else null_tod_spec_signature()
            )
            existing = null_store.find_by_key(observation["observation_id"], null_spec_signature)
            if existing is not None:
                reused += 1
            else:
                fields = build_null_record(
                    observation, null_spec_id=null_spec_id, playbook_store=playbook_store,
                    bar_store=bar_store, config_fingerprint=config_fingerprint,
                    backing_bucket=backing_bucket, context_resolver=context_resolver,
                    record_cache=record_cache,
                )
                try:
                    null_store.record(fields)
                    recorded += 1
                except NullAlreadyRecorded:
                    reused += 1  # a concurrent racer recorded it first -- an honest reuse, not a crash
                if fields["excluded"]:
                    excluded += 1
            if progress is not None:
                progress({"done": done + 1, "total": total})
    except Exception as exc:  # noqa: BLE001 -- logged, then re-raised verbatim, never swallowed
        _log(state="failed", done=recorded + reused, total=total, error=str(exc))
        raise

    final_done = recorded + reused
    _log(state="cancelled" if cancelled else "completed", done=final_done, total=total, error=None)
    return {
        "null_spec_id": null_spec_id, "total": total, "recorded": recorded, "reused": reused,
        "excluded": excluded, "cancelled": cancelled,
    }


_IDLE_SNAPSHOT_TEMPLATE: dict = {
    "id": None, "status": "idle", "null_spec_id": None, "done": 0, "total": 0, "error": None,
}


class RefereeNullComputeManager:
    """Owns one in-flight (or last-terminal) null-build job PER ``null_spec_id`` -- single-flight
    PER null-spec (the iter-5 IN SCOPE bullet's own wording), not process-global: a
    ``referee-null-tod-v1`` build and a ``referee-null-context-v1`` build may run concurrently, but
    two requests for the SAME null-spec never do (TC-19). Mirrors ``DeskPlaybookComputeManager``'s
    shape (one lock, an in-memory process-scoped snapshot per key, cooperative cancel, an atomic
    snapshot publish under the lock) -- job state is process-scoped bookkeeping, honestly lost on
    restart, never a research value."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshots: dict[str, dict] = {}
        self._job_ids: dict[str, str] = {}
        self._cancel_events: dict[str, threading.Event] = {}
        self._threads: dict[str, threading.Thread] = {}

    def snapshot(self, null_spec_id: str) -> dict:
        """The current/last job's snapshot for ``null_spec_id`` -- ALWAYS a real dict (never
        ``None``): before any job has ever run for this key this process, ``status == "idle"``."""
        current = self._snapshots.get(null_spec_id)
        return dict(current) if current is not None else {**_IDLE_SNAPSHOT_TEMPLATE, "null_spec_id": null_spec_id}

    def trigger(
        self,
        null_spec_id: str,
        playbook_store: PlaybookStore,
        bar_store: BarStore,
        config: Config,
        null_store: RefereeNullStore,
        *,
        backing_bucket: str = AT_WALL,
        run_store: RefereeNullRunStore | None = None,
    ) -> dict:
        """Start a NEW null-build job for ``null_spec_id``, or -- if one is already ``status`` in
        (``"running"``, ``"cancelling"``) -- return it UNCHANGED (``started: False``, single-flight
        per key). Never blocks -- the walk runs on a dedicated worker thread."""
        if null_spec_id not in _NULL_SPEC_IDS:
            raise ValueError(f"unknown null_spec_id {null_spec_id!r} -- expected one of {sorted(_NULL_SPEC_IDS)}")
        with self._lock:
            current = self._snapshots.get(null_spec_id)
            if current is not None and current["status"] in ("running", "cancelling"):
                return {"started": False, "compute": dict(current)}

            job_id = uuid.uuid4().hex
            self._job_ids[null_spec_id] = job_id
            cancel_event = threading.Event()
            self._cancel_events[null_spec_id] = cancel_event
            snapshot = {
                "id": job_id, "status": "running", "null_spec_id": null_spec_id,
                "done": 0, "total": 0, "error": None,
            }
            self._snapshots[null_spec_id] = snapshot

        def _publish(entry: dict) -> None:
            with self._lock:
                if self._job_ids.get(null_spec_id) != job_id:
                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
                current = self._snapshots.get(null_spec_id)
                if current is None:
                    return
                self._snapshots[null_spec_id] = {**current, "done": entry["done"], "total": entry["total"]}

        def _work() -> None:
            try:
                run_null_build_and_record(
                    playbook_store, bar_store, config, null_store, null_spec_id,
                    backing_bucket=backing_bucket, progress=_publish,
                    should_abort=cancel_event.is_set, run_store=run_store,
                )
            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                self._resolve_error(null_spec_id, job_id, str(exc))
                return
            if cancel_event.is_set():
                self._resolve_cancelled(null_spec_id, job_id)
            else:
                self._resolve_done(null_spec_id, job_id)

        thread = threading.Thread(target=_work, name=f"referee-null-compute:{null_spec_id}", daemon=True)
        with self._lock:
            self._threads[null_spec_id] = thread
        thread.start()
        return {"started": True, "compute": dict(snapshot)}

    def _resolve_done(self, null_spec_id: str, job_id: str) -> None:
        with self._lock:
            current = self._snapshots.get(null_spec_id)
            if current is None or self._job_ids.get(null_spec_id) != job_id:
                return
            self._snapshots[null_spec_id] = {**current, "status": "done", "error": None}

    def _resolve_error(self, null_spec_id: str, job_id: str, error: str) -> None:
        with self._lock:
            current = self._snapshots.get(null_spec_id)
            if current is None or self._job_ids.get(null_spec_id) != job_id:
                return
            self._snapshots[null_spec_id] = {**current, "status": "error", "error": error}

    def _resolve_cancelled(self, null_spec_id: str, job_id: str) -> None:
        with self._lock:
            if self._job_ids.get(null_spec_id) != job_id:
                return
            self._snapshots[null_spec_id] = {
                **_IDLE_SNAPSHOT_TEMPLATE, "null_spec_id": null_spec_id, "id": job_id,
            }

    def cancel(self, null_spec_id: str) -> None:
        """Signal cooperative cancellation for the in-flight job under ``null_spec_id`` -- flips
        the visible ``status`` to ``"cancelling"`` immediately, a harmless no-op if idle (the ROUTE
        rejects an idle cancel with a 409, the shipped desk pattern)."""
        with self._lock:
            cancel_event = self._cancel_events.get(null_spec_id)
            current = self._snapshots.get(null_spec_id)
            if current is not None and current["status"] == "running":
                self._snapshots[null_spec_id] = {**current, "status": "cancelling"}
        if cancel_event is not None:
            cancel_event.set()

    def join_all(self, timeout: float = 30.0) -> None:
        """Wait for every in-flight job thread (test/shutdown hygiene)."""
        with self._lock:
            threads = list(self._threads.values())
        for thread in threads:
            thread.join(timeout=timeout)


# --- The CLI warmer --------------------------------------------------------------------------------


def _cli_progress_printer() -> Callable[[dict], None]:
    def _print(entry: dict) -> None:
        print(f"  {entry['done']}/{entry['total']}", flush=True)

    return _print


def main() -> int:
    """CLI: ``python -m app.research.referee_null --null-spec-id referee-null-tod-v1``. Runs the
    null build to completion against the operator's real playbook/bar/null-store dirs, in-process,
    synchronously -- the CLI warmer precedent every desk compute module carries."""
    parser = argparse.ArgumentParser(
        description="Referee null-build CLI warmer -- draws seeded ToD-matched (or context-"
        "matched) comparison anchors for every eligible Playbook observation and persists the "
        "result append-only to the SAME durable store GET /research/desk/referee/nulls serves."
    )
    parser.add_argument(
        "--null-spec-id", required=True, choices=sorted(_NULL_SPEC_IDS),
        help="which matched-null variant to build -- REQUIRED, no default.",
    )
    args = parser.parse_args()

    config = CONFIG
    bar_store = get_bar_store()
    playbook_store = PlaybookStore(resolve_desk_playbook_dir(config.desk_universe_dir_resolved()))
    null_store = RefereeNullStore(resolve_referee_null_dir(config.desk_universe_dir_resolved()))
    run_store = RefereeNullRunStore(resolve_referee_null_log_dir(config.desk_universe_dir_resolved()))

    summary = run_null_build_and_record(
        playbook_store, bar_store, config, null_store, args.null_spec_id,
        progress=_cli_progress_printer(), run_store=run_store,
    )
    print(
        f"referee null build complete for {args.null_spec_id}: {summary['total']} observation(s) "
        f"walked, {summary['recorded']} newly recorded, {summary['reused']} reused, "
        f"{summary['excluded']} excluded."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
