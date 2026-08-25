"""``micro_join.py`` -- Era "The Rapid Microscope" J-03: the structure x flow join.

Joins a PLAYBOOK SIGNAL ``(symbol, trigger_ts)`` (read verbatim from ``desk_playbook.py``'s
recorded records) or a BAND-MAP WALL TOUCH ``(symbol, as_of_epoch)`` (resolved read-only through
``desk_playbook_context.BandMapResolver.resolve``, ``compute=False`` -- never a second band-map
computation) to the covering micro snapshot's own feature row AT-OR-BEFORE the trigger, plus the
closed set of outcome rows AFTER it (``docs/rapid-validation-spec.md`` section 4). This module
computes NOTHING the engine/observer/detector/context modules already own -- it locates and reads
their already-persisted output (spec's own "read-side law").

**The lookahead rail, mechanically.** A feature-at-trigger row is chosen by scanning the
snapshot's own append-order rows (ascending ``anchor_at`` -- ``micro_observer.py``'s prefix-law
invariant) and keeping the LAST one whose ``anchor_at`` is at-or-before the trigger instant; a row
strictly after the trigger can never be selected (``_locate_at_or_before``, TR-1 in spirit, TC-3's
own dedicated test).

**The absolute-vs-logical clock translation.** A playbook signal's ``trigger_ts`` (an ISO string,
``desk_playbook_detect.py``'s ``_iso(trigger_bar.epoch)``) and a band touch's ``as_of_epoch`` are
both ABSOLUTE UTC epochs; a snapshot row's own ``anchor_at`` is the dataset's LOGICAL replay clock
(``HistoricalProvider``'s "logical, not wall-clock" scheme -- the dataset events' raw ``ts``
values, small offsets from zero, never absolute epochs -- see ``datasets.py``'s
``_event_to_row``/``_row_to_event`` round trip). The translation is the IDENTICAL
``epoch_anchor + logical_ts`` reconstruction ``setups.py``'s own tape-at-the-wall join
(``_tape_timeline``) and ``serializers.serialize_history``'s chart projection already use,
inverted here (absolute -> logical instead of logical -> absolute) -- never a second scheme.

**The dataset-window match.** ``_covering_dataset`` mirrors ``setups.py``'s own
``_matching_dataset`` technique verbatim (symbol equality + ``[window_start_utc, window_end_utc]``
numeric-epoch containment, ties on ``(created_utc, id)``) -- re-implemented locally rather than
imported because it is a small, generic technical match over dataset METADATA, not a second
implementation of any measurement rail (the same class of judgment call
``micro_readiness.py``'s own ``_quote_rule_decides`` docstring makes for mirroring, rather than
importing, a sibling module's technique). Logged as an interpretation call in the iteration's dev
handoff.

**``band_touch_count`` is a typed "not enumerated" state, never a bare zero (iter-4 passenger
fix).** No module anywhere in the shipped product yet enumerates discrete band-map wall-touch
INSTANTS as a stored, countable list -- identifying what counts as a "touch" is explicitly J-09's
own predeclared-mechanism work (goal.md OUT OF SCOPE: "Any pilot-study-specific mechanism ... is
J-09; J-03 only builds the generic join primitive and its honest corpus count"). ``join_band_touch``
below proves the JOIN PRIMITIVE itself works against an explicit, caller-supplied ``(symbol,
as_of_epoch)`` pair (TC-2); there is simply no existing corpus of such pairs to count over yet. The
J-03 iteration originally served a bare ``0`` here -- indistinguishable, at the response's own
surface, from "we counted and found zero touches". The iter-4 fix (goal.md J-04 passenger item)
replaces it with ``{"status": "not_enumerated", "count": None}`` (``_band_touch_not_enumerated``,
``BAND_TOUCH_STATUS_NOT_ENUMERATED``) -- a reader can no longer mistake absence-of-a-detector for a
real, counted zero. ``total`` is defined as ``playbook_signal_count`` alone (never summing a
not-yet-a-number band-touch state): numerically identical to before this fix, since the prior bare
``0`` always contributed nothing to the sum either (TC-16). Defining an actual touch enumeration
stays J-09's job; when it lands, this becomes ``{"status": "enumerated", "count": <int>}``.

**J-09 materializes it (this iteration).** ``joinable_corpus_counts`` gains an OPTIONAL, keyword-
only ``resolver`` (default ``None``, byte-identical to before for every existing caller that omits
it -- the ``playbook_store`` optionality precedent): when given, ``band_touch_count`` becomes the
REAL ``{"status": "enumerated", "count": <int>}`` -- the sum of ``enumerate_band_touches`` across
every withheld-excluded dataset already in ``records`` (the SAME denominator ``playbook_signal_
count`` already reads, never a second corpus enumeration); when omitted, the honest ``not_
enumerated`` sentinel is unchanged. ``total`` stays ``playbook_signal_count`` alone either way
(this field has never summed the band-touch state, materialized or not -- TC-16 unaffected).

**A corrupt playbook record surfaces honestly, never a silent undercount (iter-4 passenger fix).**
``playbook_store.list()`` returns ``(records, errors)`` (the SAME shape ``DatasetStore.list()``
serves, and the shape every reader of it already surfaces at ITS own call site --
``desk_playbook.PlaybookStore.list()``'s own docstring: "an EXPLICIT error row per file that failed
verification"). The J-03 iteration's own ``joinable_corpus_counts`` discarded the error half
outright (``playbook_store.list()[0]``) -- a corrupted playbook file would silently vanish from
``total``/``playbook_signal_count``/``by_setup_id`` with no trace anywhere in the response. Fixed
by capturing both halves and serving the error half verbatim as ``playbook_integrity_errors`` --
the corruption is now visible beside the (necessarily undercounted, but no longer SILENTLY
undercounted) count, the same discipline dataset errors already get via ``micro_readiness.py``'s
own ``integrity_errors`` field.

**Outcome-start basis (assumption-ledger entry, this iteration).** Outcome start = the trigger's
own ``anchor_at`` (never a later, conditioned instant) -- no per-candidate conditioning feature
set exists before J-04's Scout, so ``resolve_outcome_start``'s general "max of the conditioning
set's ``available_at``" collapses to the trivial single-element case here. A future J-04/J-05
caller conditioning on a DEFERRED feature (whose ``available_at`` is later than its own
``anchor_at``) will call ``micro_features.require_outcome_start_not_before_conditioning`` itself,
not this module -- this join's own outcome rows are unconditioned.

**Never a second replay, never a second parse.** Feature rows are read through
``micro_accessor.MicroAccessor`` (J-05 re-point -- the sole legal door onto a snapshot's persisted
rows, TR-3's import-ban; this module constructs it unfenced, ``origin=None``, since this call site
has never been chronologically fenced and the legacy corpus it reads is r2-pre-marked exposed for
its entire span regardless -- see ``micro_accessor.py``'s own module docstring, "Two callers, two
disciplines") after ``load_snapshot_meta`` confirms the snapshot is CURRENT (TR-7); a dataset with
no covering window, or a covering dataset with no currently-valid snapshot, is an honest
``no_covering_snapshot`` -- never a fabricated join."""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from . import micro_features as mf
from ..providers.base import TradeEvent
from .datasets import DatasetStore, parse_utc_epoch
from .micro_accessor import MicroAccessor
# ``exclude_withheld``: spec section 7.5 point 6 (r4) -- the ONE withholding predicate every
# corpus-wide enumerator shares, imported rather than re-implemented here.
from .micro_snapshots import exclude_withheld, load_snapshot_meta

if TYPE_CHECKING:  # pragma: no cover -- type-checking only, never a runtime import (no cycle risk)
    from ..config import Config
    from .desk_playbook_context import BandMapResolver

__all__ = [
    "MICRO_HORIZON_TRADES",
    "MICRO_HORIZON_SHARES",
    "MICRO_HORIZON_CLOCK_SECONDS",
    "JOIN_STATUS_JOINED",
    "JOIN_STATUS_NO_COVERING_SNAPSHOT",
    "JOIN_STATUS_NO_ROW_BEFORE_TRIGGER",
    "JOIN_STATUS_NO_BAND_CONTEXT",
    "BAND_TOUCH_STATUS_NOT_ENUMERATED",
    "BAND_TOUCH_STATUS_ENUMERATED",
    "find_covering_dataset",
    "find_covering_snapshot",
    "feature_row_at_trigger",
    "outcome_rows_after_trigger",
    "outcome_rows_at_position",
    "outcome_row_at_single_horizon",
    "join_playbook_signal",
    "join_band_touch",
    "enumerate_band_touches",
    "joinable_corpus_counts",
]

# docs/rapid-validation-spec.md section 1 -- transcribed verbatim (module docstring: this module is
# the FIRST caller of an outcome horizon, so it is this module's constants to own; deliberately
# NOT the same Python objects as micro_features.py's MICRO_FEATURE_WINDOW_* -- that module's own
# docstring calls the windows and the horizons "deliberately separate constants" despite sharing
# today's numeric values).
MICRO_HORIZON_TRADES: tuple[int, ...] = (20, 100)
MICRO_HORIZON_SHARES: tuple[int, ...] = (5_000, 50_000)
MICRO_HORIZON_CLOCK_SECONDS: tuple[int, ...] = (30, 60, 300)

# A horizon whose target row does not exist in the recorded stream is, by construction, beyond the
# session -- this sentinel need only satisfy `horizon_ts > session_end_ts` (mid_outcome's own
# truncation test); its exact magnitude carries no meaning beyond "later than the window".
_BEYOND_SESSION_EPS = 1.0

JOIN_STATUS_JOINED = "joined"
JOIN_STATUS_NO_COVERING_SNAPSHOT = "no_covering_snapshot"
JOIN_STATUS_NO_ROW_BEFORE_TRIGGER = "no_row_before_trigger"
JOIN_STATUS_NO_BAND_CONTEXT = "no_band_context"

_ABSENT_JOIN = {"dataset_id": None, "feature_at_trigger": None, "outcomes": []}


# --- absolute epoch <-> a dataset's own logical replay clock (module docstring) --------------------


def _logical_ts(dataset_meta: dict, absolute_epoch: float) -> float:
    anchor = dataset_meta.get("epoch_anchor")
    if anchor is None:
        return absolute_epoch
    return absolute_epoch - anchor


def _session_end_logical_ts(dataset_meta: dict) -> float:
    """The dataset's own recorded window end, in ITS logical clock -- the honest truncation
    boundary (spec section 4), independent of whether a close-out row happens to exist (module
    docstring: ``MicroObserver.finalize()`` only appends one when a deferred construct was still
    pending -- module ``micro_observer.py``)."""
    return _logical_ts(dataset_meta, parse_utc_epoch(dataset_meta["window_end_utc"]))


# --- the dataset-window match (module docstring: mirrors setups.py's _matching_dataset) ------------


def _covering_dataset(symbol: str, at_epoch: float, records: Sequence[dict]) -> dict | None:
    candidates = [
        r for r in records
        if r["symbol"] == symbol
        and parse_utc_epoch(r["window_start_utc"]) <= at_epoch <= parse_utc_epoch(r["window_end_utc"])
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda r: (r["created_utc"], r["id"]))


def find_covering_dataset(symbol: str, at_epoch: float, dataset_store: DatasetStore) -> dict | None:
    """The single-lookup convenience form of ``_covering_dataset`` -- lists the store fresh for
    THIS one call. A caller checking many instants against the SAME store (``joinable_corpus_
    counts`` below) lists once and calls ``_covering_dataset`` directly instead.

    Withheld Validation-Vault shards are excluded (spec section 7.5 point 6, r4): this lookup is
    the door onto a covering SNAPSHOT and therefore onto a shard's rows, so a sealed shard covering
    the instant is an honest ``None`` (the same answer this function already gives when no window
    covers it) rather than a read of held-out tape."""
    records, _errors = dataset_store.list()
    records, _withheld_excluded = exclude_withheld(records, dataset_store)
    return _covering_dataset(symbol, at_epoch, records)


def find_covering_snapshot(
    symbol: str, at_epoch: float, dataset_store: DatasetStore, snapshots_dir: str, config: "Config"
) -> tuple[dict, dict] | None:
    """``(dataset_meta, snapshot_meta)`` for the covering, CURRENTLY-VALID snapshot, or ``None``
    when no dataset window covers ``at_epoch`` for ``symbol``, or one does but carries no
    currently-valid snapshot (TR-7 -- a stale/never-built snapshot is an honest miss, never
    served)."""
    dataset_meta = find_covering_dataset(symbol, at_epoch, dataset_store)
    if dataset_meta is None:
        return None
    snapshot_meta = load_snapshot_meta(snapshots_dir, dataset_store, dataset_meta["id"], config)
    if snapshot_meta is None:
        return None
    return dataset_meta, snapshot_meta


# --- the feature-at-trigger lookup (the lookahead rail, mechanically -- module docstring) ----------


def _trade_rows(rows: Sequence[dict]) -> list[dict]:
    """Every TRADE-anchored row -- excludes the optional close-out row
    (``micro_observer.finalize()``'s own ``close_out: True`` marker), which carries no
    ``cumulative_delta``/``mid``/``price`` and is never itself a feature-at-trigger candidate."""
    return [r for r in rows if not r.get("close_out")]


def _locate_at_or_before(trade_rows: list[dict], trigger_logical_ts: float) -> int | None:
    """The index of the LAST row (ascending ``anchor_at`` order -- the snapshot's own append
    order) with ``anchor_at <= trigger_logical_ts``, or ``None`` when every row is strictly after
    the trigger (or the stream is empty). A row is selected ONLY because its own anchor precedes
    or equals the trigger -- never because it is merely nearby (TC-3)."""
    found = None
    for i, row in enumerate(trade_rows):
        if row["anchor_at"] <= trigger_logical_ts:
            found = i
        else:
            break
    return found


def feature_row_at_trigger(rows: Sequence[dict], trigger_logical_ts: float) -> dict | None:
    """The feature row at-or-before ``trigger_logical_ts`` (a dataset-LOGICAL instant -- callers
    holding an absolute epoch convert via ``_logical_ts`` first), or ``None`` when the trigger
    precedes every trade row. Returns the row VERBATIM (including its ``deferred`` list, with any
    ``unavailable``/``refused`` flag intact -- TC-6): this function never projects or coerces a
    row's own fields."""
    trade_rows = _trade_rows(rows)
    i = _locate_at_or_before(trade_rows, trigger_logical_ts)
    return None if i is None else trade_rows[i]


# --- the closed outcome set (spec section 4), resolved over the trade-anchored representation ------


def _trade_horizon_row(trade_rows: list[dict], anchor_pos: int, n_trades: int) -> dict | None:
    target_pos = anchor_pos + n_trades
    return trade_rows[target_pos] if target_pos < len(trade_rows) else None


def _shares_horizon_row(trade_rows: list[dict], anchor_pos: int, shares_threshold: int) -> dict | None:
    """iter-4 perf fix (behavior-unchanged): iterates by INDEX rather than ``trade_rows[anchor_pos
    + 1:]`` -- that slice notation copies every remaining row on EVERY call regardless of how
    quickly the loop below breaks, which is O(n) per call and, summed across one caller evaluating
    every anchor of a dataset (``scout.extract_anchors``, J-04), O(n^2) overall -- measured to hang
    ``POST /research/desk/micro/scout/compute`` against the real 18-dataset corpus. Output is
    byte-identical: same iteration order, same early-return row, same ``None`` when the threshold
    is never reached."""
    cumulative = 0.0
    for i in range(anchor_pos + 1, len(trade_rows)):
        row = trade_rows[i]
        cumulative += row["size"]
        if cumulative >= shares_threshold:
            return row
    return None


def _clock_horizon_row(trade_rows: list[dict], anchor_pos: int, horizon_ts: float) -> dict | None:
    """The nearest at-or-before row for a CLOCK horizon, sampled from the trade-anchored
    representation (the ONLY representation the section 2.4 benchmark chose -- there is no
    standalone quote row to sample instead; an interpretation call, logged in the dev handoff).

    iter-4 perf fix (behavior-unchanged): the SAME index-iteration fix as ``_shares_horizon_row``
    above, for the identical reason (``trade_rows[anchor_pos:]`` was an O(n)-per-call slice
    copy)."""
    candidate = None
    for i in range(anchor_pos, len(trade_rows)):
        row = trade_rows[i]
        if row["anchor_at"] <= horizon_ts:
            candidate = row
        else:
            break
    return candidate


def _build_outcome(
    *, kind: str, value: int, anchor_row: dict, horizon_row: dict | None, horizon_ts: float,
    session_end_ts: float, direction: str | None,
) -> dict:
    mid_at_horizon = horizon_row.get("mid") if horizon_row is not None else None
    price_at_horizon = horizon_row.get("price") if horizon_row is not None else None
    return {
        "horizon_kind": kind,
        "horizon_value": value,
        "mid": mf.mid_outcome(
            mid_at_start=anchor_row.get("mid"), mid_at_horizon=mid_at_horizon,
            outcome_start=anchor_row["anchor_at"], horizon_ts=horizon_ts,
            session_end_ts=session_end_ts, direction=direction,
        ),
        "last_trade": mf.last_trade_outcome(
            price_at_start=anchor_row.get("price"), price_at_horizon=price_at_horizon,
            outcome_start=anchor_row["anchor_at"], horizon_ts=horizon_ts,
            session_end_ts=session_end_ts, direction=direction,
        ),
        "spread_at_outcome_start_bps": mf.spread_bps(anchor_row.get("spread"), anchor_row.get("mid")),
    }


def _outcome_rows_after(
    trade_rows: list[dict], anchor_pos: int, session_end_ts: float, *, direction: str | None
) -> list[dict]:
    anchor_row = trade_rows[anchor_pos]
    outcomes: list[dict] = []
    for n in MICRO_HORIZON_TRADES:
        horizon_row = _trade_horizon_row(trade_rows, anchor_pos, n)
        horizon_ts = horizon_row["anchor_at"] if horizon_row is not None else session_end_ts + _BEYOND_SESSION_EPS
        outcomes.append(_build_outcome(
            kind="trades", value=n, anchor_row=anchor_row, horizon_row=horizon_row,
            horizon_ts=horizon_ts, session_end_ts=session_end_ts, direction=direction,
        ))
    for shares in MICRO_HORIZON_SHARES:
        horizon_row = _shares_horizon_row(trade_rows, anchor_pos, shares)
        horizon_ts = horizon_row["anchor_at"] if horizon_row is not None else session_end_ts + _BEYOND_SESSION_EPS
        outcomes.append(_build_outcome(
            kind="shares", value=shares, anchor_row=anchor_row, horizon_row=horizon_row,
            horizon_ts=horizon_ts, session_end_ts=session_end_ts, direction=direction,
        ))
    for seconds in MICRO_HORIZON_CLOCK_SECONDS:
        horizon_ts = anchor_row["anchor_at"] + seconds
        horizon_row = None if horizon_ts > session_end_ts else _clock_horizon_row(trade_rows, anchor_pos, horizon_ts)
        outcomes.append(_build_outcome(
            kind="clock_seconds", value=seconds, anchor_row=anchor_row, horizon_row=horizon_row,
            horizon_ts=horizon_ts, session_end_ts=session_end_ts, direction=direction,
        ))
    return outcomes


def outcome_rows_after_trigger(
    rows: Sequence[dict], anchor_row: dict, session_end_ts: float, *, direction: str | None = None
) -> list[dict]:
    """The closed set of outcome rows (spec section 4) at every horizon of section 1, anchored at
    ``anchor_row`` (a row returned by ``feature_row_at_trigger`` over the SAME ``rows``). Outcome
    start = ``anchor_row["anchor_at"]`` (this iteration's assumption-ledger entry -- module
    docstring). Each entry carries the mid-basis primary, the last-trade sensitivity basis, and
    the spread-at-outcome-start cost-proxy column, never merged into either outcome's own value.

    ``trade_rows.index(anchor_row)`` is an O(n) scan -- fine for the single at-or-before lookup
    this function's own callers (``_join_core``) make once per join, but pathological for a
    caller iterating every anchor of a whole snapshot (O(n^2) overall). ``outcome_rows_at_position``
    below is the O(1)-position counterpart for exactly that caller shape (iter-4, J-04's own
    ``scout.extract_anchors``, added when a live run against the real 18-dataset corpus stalled on
    this scan -- see that function's own docstring)."""
    trade_rows = _trade_rows(rows)
    anchor_pos = trade_rows.index(anchor_row)
    return _outcome_rows_after(trade_rows, anchor_pos, session_end_ts, direction=direction)


def outcome_rows_at_position(
    trade_rows: list[dict], anchor_pos: int, session_end_ts: float, *, direction: str | None = None
) -> list[dict]:
    """The O(1)-position counterpart to ``outcome_rows_after_trigger`` (module docstring, iter-4):
    for a caller that ALREADY knows an anchor's own position in its trade-only row list (e.g. one
    iterating via ``enumerate(trade_rows)``), this skips the O(n) ``.index()`` lookup that function
    performs internally -- byte-identical output to
    ``outcome_rows_after_trigger(rows, trade_rows[anchor_pos], session_end_ts, direction=direction)`` for the
    SAME ``trade_rows``/``anchor_pos``/``session_end_ts``/``direction`` (both call the SAME
    ``_outcome_rows_after`` core -- no second outcome implementation, the read-side law honored).

    Takes ``trade_rows`` (a plain ``list``, not ``Sequence``) and passes it through UNCOPIED:
    ``_outcome_rows_after`` only ever reads it, never mutates it, so a defensive ``list(...)`` copy
    here would itself be an O(n) cost paid on EVERY call -- exactly the anti-pattern this function
    exists to eliminate, and the reason a caller iterating every anchor of a large dataset must
    pass the SAME list object through every call, never a fresh copy per anchor."""
    return _outcome_rows_after(trade_rows, anchor_pos, session_end_ts, direction=direction)


def outcome_row_at_single_horizon(
    trade_rows: list[dict],
    anchor_pos: int,
    horizon_kind: str,
    horizon_value: int,
    session_end_ts: float,
    *,
    direction: str | None = None,
) -> dict:
    """ONE entry of the closed outcome set (spec section 4) -- computes only the requested
    ``(horizon_kind, horizon_value)`` pair, byte-identical to the matching entry of
    ``outcome_rows_at_position(...)``'s own list, by calling the IDENTICAL per-horizon-kind
    row-finder (``_trade_horizon_row``/``_shares_horizon_row``/``_clock_horizon_row``) and
    ``_build_outcome`` core those functions already use (no second implementation).

    Exists because ``_outcome_rows_after`` always computes the FULL closed set (2 trade + 2 shares
    + 3 clock horizons) even when a caller wants exactly one -- fine for the join primitives' own
    call volume (once per playbook signal or band touch), but for a caller evaluating one horizon
    across EVERY anchor of a large dataset (``scout.extract_anchors``, J-04), the other 6 unused
    horizons' own forward scans (``_shares_horizon_row``/``_clock_horizon_row``, each bounded only
    by how many subsequent trades it takes to satisfy the threshold) are pure waste -- measured on
    the real NVDA dataset (~929K trades) to turn a should-be-fast trade-count-horizon extraction
    into a multi-minute stall. A trade-count horizon (``horizon_kind="trades"``) resolves in O(1)
    here (direct index arithmetic, no scan of any kind) since the unused shares/clock row-finders
    are never even called."""
    anchor_row = trade_rows[anchor_pos]
    if horizon_kind == "trades":
        horizon_row = _trade_horizon_row(trade_rows, anchor_pos, horizon_value)
        horizon_ts = (
            horizon_row["anchor_at"] if horizon_row is not None else session_end_ts + _BEYOND_SESSION_EPS
        )
    elif horizon_kind == "shares":
        horizon_row = _shares_horizon_row(trade_rows, anchor_pos, horizon_value)
        horizon_ts = (
            horizon_row["anchor_at"] if horizon_row is not None else session_end_ts + _BEYOND_SESSION_EPS
        )
    elif horizon_kind == "clock_seconds":
        horizon_ts = anchor_row["anchor_at"] + horizon_value
        horizon_row = (
            None if horizon_ts > session_end_ts else _clock_horizon_row(trade_rows, anchor_pos, horizon_ts)
        )
    else:
        raise ValueError(f"unknown horizon_kind {horizon_kind!r}")
    return _build_outcome(
        kind=horizon_kind, value=horizon_value, anchor_row=anchor_row, horizon_row=horizon_row,
        horizon_ts=horizon_ts, session_end_ts=session_end_ts, direction=direction,
    )


# --- the shared join core --------------------------------------------------------------------------


def _join_core(
    symbol: str, at_epoch: float, dataset_store: DatasetStore, snapshots_dir: str, config: "Config"
) -> dict:
    found = find_covering_snapshot(symbol, at_epoch, dataset_store, snapshots_dir, config)
    if found is None:
        return {"status": JOIN_STATUS_NO_COVERING_SNAPSHOT, **_ABSENT_JOIN}
    dataset_meta, _snapshot_meta = found
    # J-05 re-point (TR-3's import-ban): the ONLY door onto a snapshot's persisted rows is now
    # micro_accessor.py. `origin=None` is the disclosed UNFENCED mode -- this call site has never
    # been chronologically fenced and the legacy corpus it reads is r2-pre-marked exposed for its
    # entire span regardless (micro_accessor.py's own module docstring, "Two callers, two
    # disciplines"); output is byte-identical to the direct `read_snapshot_rows` call it replaces
    # (TC-4).
    rows = MicroAccessor(dataset_store, snapshots_dir, config).read_snapshot_rows(dataset_meta["id"])
    trade_rows = _trade_rows(rows)
    trigger_logical_ts = _logical_ts(dataset_meta, at_epoch)
    i = _locate_at_or_before(trade_rows, trigger_logical_ts)
    if i is None:
        return {
            "status": JOIN_STATUS_NO_ROW_BEFORE_TRIGGER,
            "dataset_id": dataset_meta["id"], "feature_at_trigger": None, "outcomes": [],
        }
    session_end_ts = _session_end_logical_ts(dataset_meta)
    outcomes = _outcome_rows_after(trade_rows, i, session_end_ts, direction=None)
    return {
        "status": JOIN_STATUS_JOINED,
        "dataset_id": dataset_meta["id"],
        "feature_at_trigger": dict(trade_rows[i]),
        "outcomes": outcomes,
    }


# --- the two public entry points (goal.md Key Capability 4) ----------------------------------------


def join_playbook_signal(
    signal: dict, dataset_store: DatasetStore, snapshots_dir: str, config: "Config"
) -> dict:
    """Join ONE recorded playbook signal (``desk_playbook.py``'s own ``symbol``/``trigger_ts``/
    ``setup_id`` fields, read verbatim -- never re-detected) to its covering snapshot's
    feature-at-trigger row plus the closed outcome set after it."""
    symbol = signal.get("symbol")
    trigger_ts = signal.get("trigger_ts")
    base = {"symbol": symbol, "trigger_ts": trigger_ts, "setup_id": signal.get("setup_id")}
    if not symbol or not trigger_ts:
        return {"status": JOIN_STATUS_NO_COVERING_SNAPSHOT, **_ABSENT_JOIN, **base}
    trigger_epoch = parse_utc_epoch(trigger_ts)
    core = _join_core(symbol, trigger_epoch, dataset_store, snapshots_dir, config)
    return {**core, **base}


def join_band_touch(
    touch: dict, resolver: "BandMapResolver", dataset_store: DatasetStore, snapshots_dir: str,
    config: "Config",
) -> dict:
    """Join ONE band-map wall touch ``{"symbol": ..., "as_of_epoch": ...}`` to its covering
    snapshot's feature-at-trigger row plus the closed outcome set after it, carrying the resolved
    band map beside them. ``resolver.resolve(...)`` is READ-ONLY (``compute=False`` at
    construction, per goal.md's own framing) -- a cache miss is an honest absence, never a
    fabricated wall (TC-2)."""
    symbol = touch.get("symbol")
    as_of_epoch = touch.get("as_of_epoch")
    base = {"symbol": symbol, "as_of_epoch": as_of_epoch, "band_map": None}
    if not symbol or as_of_epoch is None:
        return {"status": JOIN_STATUS_NO_BAND_CONTEXT, **_ABSENT_JOIN, **base}
    band_map = resolver.resolve(symbol, as_of_epoch)
    if band_map is None:
        return {"status": JOIN_STATUS_NO_BAND_CONTEXT, **_ABSENT_JOIN, **base}
    core = _join_core(symbol, as_of_epoch, dataset_store, snapshots_dir, config)
    return {**core, "symbol": symbol, "as_of_epoch": as_of_epoch, "band_map": band_map}


# --- the band-touch enumerator (J-09, goal.md Key Capability 5's own primitive) --------------------


def _band_id(band: dict) -> str:
    """A stable identifier for ONE band, from its own ``(side, price_low, price_high)`` identity --
    the SAME two price bounds ``setups.py``'s own ``_event_id`` precedent hashes beside its call's
    symbol/session/touch_ts (that module's own docstring) -- never ``quality_score``/``class``/
    ``members``, which can shift between two computes of the IDENTICAL wall (a re-ranked
    ``quality_score`` after a bar backfill, say) without changing WHICH wall it is."""
    return f"{band['side']}:{band['price_low']!r}:{band['price_high']!r}"


def enumerate_band_touches(
    dataset_meta: dict, dataset_store: DatasetStore, resolver: "BandMapResolver"
) -> list[dict]:
    """Ordered per-wall touch instants -- ``{"symbol", "as_of_epoch", "band_id"}`` -- across ONE
    dataset's own recorded trade timeline (spec section 3's structural join primitive; goal.md Key
    Capability 5). The band map is resolved ONCE, at the dataset's own window start (module
    docstring: a recorded RTH window never spans an ET midnight, so one basis session covers every
    trade in it) -- ``resolver.resolve(...)`` is READ-ONLY (``compute=False`` at the caller's own
    construction, per goal.md's own framing); an unresolvable map is an honest empty list, never a
    fabricated touch (TC-3).

    Reads the dataset's OWN raw event stream (``DatasetStore.load_events`` -- an existing,
    already-sanctioned store reader, the SAME call ``micro_readiness.py``'s own ``fallback_frac``
    fold already makes; TR-3's accessor fence governs SNAPSHOT/vault reads, not this) rather than a
    built snapshot's feature rows -- deliberately, so this enumeration NEVER requires a snapshot to
    already exist (the ``joinable_corpus_counts`` docstring's own "never requires a snapshot to
    already be BUILT" law, extended here from playbook signals to band touches). The expensive
    event load only happens AFTER the band map resolves (a durable-cache hit or an honest miss) --
    the common case today (most symbol/dates have no operator-warmed tradability map) pays only the
    cheap resolver lookup, never a multi-million-row parse for nothing.

    A touch mirrors ``setups.py``'s own ``_touches`` "first touch, re-arm only once fully exited"
    rule (that function's own docstring), applied here to a TRADE PRICE against one band's
    ``[price_low, price_high]`` instead of a bar's own ``[low, high]`` range: each band arms/re-arms
    INDEPENDENTLY, so one trade can touch several bands at once, and a later trade only re-arms the
    bands it has fully exited."""
    symbol = dataset_meta.get("symbol")
    if not symbol:
        return []
    band_map = resolver.resolve(symbol, parse_utc_epoch(dataset_meta["window_start_utc"]))
    if band_map is None:
        return []
    bands = band_map.get("bands") or []
    if not bands:
        return []
    epoch_anchor = dataset_meta.get("epoch_anchor") or 0.0
    armed = [True] * len(bands)
    touches: list[dict] = []
    for event in dataset_store.load_events(dataset_meta["id"]):
        if not isinstance(event, TradeEvent):
            continue
        absolute_epoch = epoch_anchor + event.timestamp
        for i, band in enumerate(bands):
            inside = band["price_low"] <= event.price <= band["price_high"]
            if inside and armed[i]:
                touches.append(
                    {"symbol": symbol, "as_of_epoch": absolute_epoch, "band_id": _band_id(band)}
                )
                armed[i] = False
            elif not inside:
                armed[i] = True
    return touches


# --- the honest joinable-corpus count (micro_readiness.py's new field) -----------------------------

# The closed vocabulary for band_touch_count's status (iter-4 passenger fix; J-09 adds the
# "enumerated" sibling the iter-4 docstring already predicted -- see the module docstring).
BAND_TOUCH_STATUS_NOT_ENUMERATED = "not_enumerated"
BAND_TOUCH_STATUS_ENUMERATED = "enumerated"


def _band_touch_not_enumerated() -> dict:
    """A FRESH dict every call (never a shared mutable literal -- the ``desk_playbook.py``
    per-list-copy discipline, applied to a plain dict here) so no caller can ever poison a later
    read by mutating what it received."""
    return {"status": BAND_TOUCH_STATUS_NOT_ENUMERATED, "count": None}


def joinable_corpus_counts(
    dataset_store: DatasetStore,
    playbook_store,
    *,
    resolver: "BandMapResolver | None" = None,
    band_touch_cache=None,
) -> dict:
    """``total``/``playbook_signal_count``/``band_touch_count``/``by_setup_id``/
    ``playbook_integrity_errors`` -- every recorded playbook signal whose ``(symbol, trigger_ts)``
    falls inside a recorded tick dataset's own window (module docstring's dataset-window match),
    counted honestly from the real stores. Never requires a snapshot to already be BUILT: a
    snapshot is a reproducible, rebuildable cache of the SAME tick data (``micro_snapshots.py``'s
    own "derived, rebuildable" docstring) -- an unbuilt one says nothing about whether the
    underlying evidence is joinable.

    Fails CLOSED, never silently under-counts (the iter-2 "streamed-artifact completeness"
    lesson, applied to this enumeration loop): a signal recording no symbol or no ``trigger_ts``
    is a structural, honest absence and is skipped (the identical treatment
    ``desk_playbook_context.record_band_context`` already gives it); a signal whose ``trigger_ts``
    is PRESENT but unparseable is never silently skipped -- ``parse_utc_epoch`` raises and this
    function raises with it, rather than serving an undercounted total. A CORRUPTED playbook
    record (``playbook_store.list()``'s own error half) is skipped from the count -- there is no
    signal content to read from a file that failed verification -- but is never silently dropped
    from the RESPONSE: it is surfaced verbatim in ``playbook_integrity_errors`` (module docstring's
    iter-4 passenger fix).

    **Withheld shards are excluded, and the exclusion is disclosed (spec section 7.5 point 6, r4;
    iter-9 audit finding B5).** A dataset whose vault shard has not reached ``exposed`` is not
    available evidence, so counting its window as joinable would make this number disagree with
    ``micro_readiness``' own ``totals.distinct_datasets`` (which already excludes it) inside one
    payload. ``withheld_excluded`` carries the COUNT -- never the ids -- so the shrink is never
    silent. Byte-identical (``0``) while nothing is sealed.

    ``band_touch_cache`` (iter-26, ``micro_readiness.MicroBandTouchCache``) is OPTIONAL and
    defaults to ``None`` -- byte-identical to today's uncached compute (every existing caller)
    when omitted. When given (and ``resolver`` is also given -- band touches are only ever
    enumerated with a resolver in hand), each record's touch count is looked up, or computed once
    and published, keyed on the COMPOSITE ``(dataset_meta["checksum"], resolver.map_key(symbol,
    window_start_epoch))`` -- never the checksum alone, so a re-warmed/changed band map (a new
    ``map_key``) is a genuine miss, never a stale hit under the old map (this module's own
    ``enumerate_band_touches`` already resolves the SAME map at the SAME instant internally, so the
    externally-computed ``map_key`` here can never disagree with what that function's own
    ``resolver.resolve`` call would key on). A cache miss still computes through
    ``enumerate_band_touches`` -- this never fabricates a placeholder count -- and the resolved
    value is published before moving to the next record. Only a record whose map ACTUALLY RESOLVES
    is cached at all (iter-26 audit B1): ``map_key`` names the map REQUEST, not its answer, so an
    unresolved map's honest ``0`` shares the very key the operator's later tradability warm
    publishes under, and caching it would serve that ``0`` forever -- the phase's own "publish ONLY
    a resolved count, never a placeholder" rail. An unresolved record therefore stays on the
    uncached path, which costs only the resolver's own memoized lookup (never the event load).
    Only warm-path LATENCY changes; the summed ``total_band_touches`` is unaffected
    (TC-2/TC-3/TC-4)."""
    records, _errors = dataset_store.list()
    records, withheld_excluded = exclude_withheld(records, dataset_store)
    total_playbook = 0
    by_setup_id: dict[str, int] = {}
    playbook_records, playbook_errors = playbook_store.list()
    for playbook_record in playbook_records:
        for signal in playbook_record.get("signals") or []:
            symbol = signal.get("symbol")
            trigger_ts = signal.get("trigger_ts")
            if not symbol or not trigger_ts:
                continue
            trigger_epoch = parse_utc_epoch(trigger_ts)
            if _covering_dataset(symbol, trigger_epoch, records) is None:
                continue
            total_playbook += 1
            setup_id = signal.get("setup_id") or "unknown"
            by_setup_id[setup_id] = by_setup_id.get(setup_id, 0) + 1

    # J-09: materialized ONLY when a resolver is supplied (module docstring) -- summed over the
    # SAME withheld-excluded `records` the playbook loop above already reads, so a sealed shard is
    # excluded from this count the identical way it is excluded from `playbook_signal_count`
    # (never a second, differently-scoped corpus).
    if resolver is None:
        band_touch_count = _band_touch_not_enumerated()
    else:
        total_band_touches = 0
        for meta in records:
            symbol = meta.get("symbol")
            cacheable = False
            if band_touch_cache is not None and symbol:
                window_start_epoch = parse_utc_epoch(meta["window_start_utc"])
                # Only a RESOLVED map's count may ever enter the cache (iter-26 audit B1).
                # `map_key` names the map REQUEST -- (symbol, basis day, store signature, config
                # hash) -- NOT its answer, so the key an UNRESOLVED map produces is byte-identical
                # to the one the operator's own later tradability warm publishes under. Caching the
                # honest `0` an unresolved map yields would therefore serve that `0` forever once
                # the map exists. `resolver.resolve` memoizes per `(symbol, basis day)`, so this is
                # the SAME lookup `enumerate_band_touches` makes below, not a second one -- and an
                # unresolved map still costs only that lookup, never the event load.
                cacheable = resolver.resolve(symbol, window_start_epoch) is not None
            if cacheable:
                checksum = meta["checksum"]
                map_key = resolver.map_key(symbol, window_start_epoch)
                touch_count = band_touch_cache.lookup(checksum, map_key)
                if touch_count is None:
                    touch_count = len(enumerate_band_touches(meta, dataset_store, resolver))
                    band_touch_cache.publish(checksum, map_key, touch_count)
            else:
                touch_count = len(enumerate_band_touches(meta, dataset_store, resolver))
            total_band_touches += touch_count
        band_touch_count = {"status": BAND_TOUCH_STATUS_ENUMERATED, "count": total_band_touches}

    return {
        # `playbook_signal_count` alone -- `band_touch_count` is no longer a plain number to sum
        # (module docstring); numerically identical to the pre-fix total, since the prior bare `0`
        # always contributed nothing to the sum either (TC-16).
        "total": total_playbook,
        "playbook_signal_count": total_playbook,
        "band_touch_count": band_touch_count,
        "by_setup_id": by_setup_id,
        "playbook_integrity_errors": playbook_errors,
        # Spec section 7.5 point 6 (r4): the count of registered datasets whose windows were NOT
        # eligible to make a signal joinable, because their vault shards are withheld.
        "withheld_excluded": withheld_excluded,
    }
