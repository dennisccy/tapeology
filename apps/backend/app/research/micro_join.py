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

**``band_touch_count`` is honestly zero this iteration.** No module anywhere in the shipped
product yet enumerates discrete band-map wall-touch INSTANTS as a stored, countable list --
identifying what counts as a "touch" is explicitly J-09's own predeclared-mechanism work (goal.md
OUT OF SCOPE: "Any pilot-study-specific mechanism ... is J-09; J-03 only builds the generic join
primitive and its honest corpus count"). ``join_band_touch`` below proves the JOIN PRIMITIVE
itself works against an explicit, caller-supplied ``(symbol, as_of_epoch)`` pair (TC-2); there is
simply no existing corpus of such pairs to count over yet, so ``joinable_corpus_counts`` reports
the honest, non-fabricated zero rather than inventing a detector.

**Outcome-start basis (assumption-ledger entry, this iteration).** Outcome start = the trigger's
own ``anchor_at`` (never a later, conditioned instant) -- no per-candidate conditioning feature
set exists before J-04's Scout, so ``resolve_outcome_start``'s general "max of the conditioning
set's ``available_at``" collapses to the trivial single-element case here. A future J-04/J-05
caller conditioning on a DEFERRED feature (whose ``available_at`` is later than its own
``anchor_at``) will call ``micro_features.require_outcome_start_not_before_conditioning`` itself,
not this module -- this join's own outcome rows are unconditioned.

**Never a second replay, never a second parse.** Feature rows are read through
``micro_snapshots.read_snapshot_rows`` (this module's ONLY door onto a snapshot's persisted rows,
never a raw ``open()``) after ``load_snapshot_meta`` confirms the snapshot is CURRENT (TR-7); a
dataset with no covering window, or a covering dataset with no currently-valid snapshot, is an
honest ``no_covering_snapshot`` -- never a fabricated join."""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from . import micro_features as mf
from .datasets import DatasetStore, parse_utc_epoch
from .micro_snapshots import load_snapshot_meta, read_snapshot_rows

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
    "find_covering_dataset",
    "find_covering_snapshot",
    "feature_row_at_trigger",
    "outcome_rows_after_trigger",
    "join_playbook_signal",
    "join_band_touch",
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
    counts`` below) lists once and calls ``_covering_dataset`` directly instead."""
    records, _errors = dataset_store.list()
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
    cumulative = 0.0
    for row in trade_rows[anchor_pos + 1 :]:
        cumulative += row["size"]
        if cumulative >= shares_threshold:
            return row
    return None


def _clock_horizon_row(trade_rows: list[dict], anchor_pos: int, horizon_ts: float) -> dict | None:
    """The nearest at-or-before row for a CLOCK horizon, sampled from the trade-anchored
    representation (the ONLY representation the section 2.4 benchmark chose -- there is no
    standalone quote row to sample instead; an interpretation call, logged in the dev handoff)."""
    candidate = None
    for row in trade_rows[anchor_pos:]:
        if row["anchor_at"] <= horizon_ts:
            candidate = row
        else:
            break
    return candidate


def _build_outcome(
    *, kind: str, value: int, anchor_row: dict, horizon_row: dict | None, horizon_ts: float,
    session_end_ts: float, side: str | None,
) -> dict:
    mid_at_horizon = horizon_row.get("mid") if horizon_row is not None else None
    price_at_horizon = horizon_row.get("price") if horizon_row is not None else None
    return {
        "horizon_kind": kind,
        "horizon_value": value,
        "mid": mf.mid_outcome(
            mid_at_start=anchor_row.get("mid"), mid_at_horizon=mid_at_horizon,
            outcome_start=anchor_row["anchor_at"], horizon_ts=horizon_ts,
            session_end_ts=session_end_ts, side=side,
        ),
        "last_trade": mf.last_trade_outcome(
            price_at_start=anchor_row.get("price"), price_at_horizon=price_at_horizon,
            outcome_start=anchor_row["anchor_at"], horizon_ts=horizon_ts,
            session_end_ts=session_end_ts, side=side,
        ),
        "spread_at_outcome_start_bps": mf.spread_bps(anchor_row.get("spread"), anchor_row.get("mid")),
    }


def _outcome_rows_after(
    trade_rows: list[dict], anchor_pos: int, session_end_ts: float, *, side: str | None
) -> list[dict]:
    anchor_row = trade_rows[anchor_pos]
    outcomes: list[dict] = []
    for n in MICRO_HORIZON_TRADES:
        horizon_row = _trade_horizon_row(trade_rows, anchor_pos, n)
        horizon_ts = horizon_row["anchor_at"] if horizon_row is not None else session_end_ts + _BEYOND_SESSION_EPS
        outcomes.append(_build_outcome(
            kind="trades", value=n, anchor_row=anchor_row, horizon_row=horizon_row,
            horizon_ts=horizon_ts, session_end_ts=session_end_ts, side=side,
        ))
    for shares in MICRO_HORIZON_SHARES:
        horizon_row = _shares_horizon_row(trade_rows, anchor_pos, shares)
        horizon_ts = horizon_row["anchor_at"] if horizon_row is not None else session_end_ts + _BEYOND_SESSION_EPS
        outcomes.append(_build_outcome(
            kind="shares", value=shares, anchor_row=anchor_row, horizon_row=horizon_row,
            horizon_ts=horizon_ts, session_end_ts=session_end_ts, side=side,
        ))
    for seconds in MICRO_HORIZON_CLOCK_SECONDS:
        horizon_ts = anchor_row["anchor_at"] + seconds
        horizon_row = None if horizon_ts > session_end_ts else _clock_horizon_row(trade_rows, anchor_pos, horizon_ts)
        outcomes.append(_build_outcome(
            kind="clock_seconds", value=seconds, anchor_row=anchor_row, horizon_row=horizon_row,
            horizon_ts=horizon_ts, session_end_ts=session_end_ts, side=side,
        ))
    return outcomes


def outcome_rows_after_trigger(
    rows: Sequence[dict], anchor_row: dict, session_end_ts: float, *, side: str | None = None
) -> list[dict]:
    """The closed set of outcome rows (spec section 4) at every horizon of section 1, anchored at
    ``anchor_row`` (a row returned by ``feature_row_at_trigger`` over the SAME ``rows``). Outcome
    start = ``anchor_row["anchor_at"]`` (this iteration's assumption-ledger entry -- module
    docstring). Each entry carries the mid-basis primary, the last-trade sensitivity basis, and
    the spread-at-outcome-start cost-proxy column, never merged into either outcome's own value."""
    trade_rows = _trade_rows(rows)
    anchor_pos = trade_rows.index(anchor_row)
    return _outcome_rows_after(trade_rows, anchor_pos, session_end_ts, side=side)


# --- the shared join core --------------------------------------------------------------------------


def _join_core(
    symbol: str, at_epoch: float, dataset_store: DatasetStore, snapshots_dir: str, config: "Config"
) -> dict:
    found = find_covering_snapshot(symbol, at_epoch, dataset_store, snapshots_dir, config)
    if found is None:
        return {"status": JOIN_STATUS_NO_COVERING_SNAPSHOT, **_ABSENT_JOIN}
    dataset_meta, _snapshot_meta = found
    rows = read_snapshot_rows(snapshots_dir, dataset_meta["id"])
    trade_rows = _trade_rows(rows)
    trigger_logical_ts = _logical_ts(dataset_meta, at_epoch)
    i = _locate_at_or_before(trade_rows, trigger_logical_ts)
    if i is None:
        return {
            "status": JOIN_STATUS_NO_ROW_BEFORE_TRIGGER,
            "dataset_id": dataset_meta["id"], "feature_at_trigger": None, "outcomes": [],
        }
    session_end_ts = _session_end_logical_ts(dataset_meta)
    outcomes = _outcome_rows_after(trade_rows, i, session_end_ts, side=None)
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


# --- the honest joinable-corpus count (micro_readiness.py's new field) -----------------------------


def joinable_corpus_counts(dataset_store: DatasetStore, playbook_store) -> dict:
    """``total``/``playbook_signal_count``/``band_touch_count``/``by_setup_id`` -- every recorded
    playbook signal whose ``(symbol, trigger_ts)`` falls inside a recorded tick dataset's own
    window (module docstring's dataset-window match), counted honestly from the real stores.
    Never requires a snapshot to already be BUILT: a snapshot is a reproducible, rebuildable cache
    of the SAME tick data (``micro_snapshots.py``'s own "derived, rebuildable" docstring) -- an
    unbuilt one says nothing about whether the underlying evidence is joinable.

    Fails CLOSED, never silently under-counts (the iter-2 "streamed-artifact completeness"
    lesson, applied to this enumeration loop): a signal recording no symbol or no ``trigger_ts``
    is a structural, honest absence and is skipped (the identical treatment
    ``desk_playbook_context.record_band_context`` already gives it); a signal whose ``trigger_ts``
    is PRESENT but unparseable is never silently skipped -- ``parse_utc_epoch`` raises and this
    function raises with it, rather than serving an undercounted total."""
    records, _errors = dataset_store.list()
    total_playbook = 0
    by_setup_id: dict[str, int] = {}
    for playbook_record in playbook_store.list()[0]:
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

    # Honestly zero this iteration -- see the module docstring's "band_touch_count is honestly
    # zero" section. Expressed as a variable (never a bare literal at the return site) so a future
    # J-09 caller wiring a real touch enumeration in changes exactly one line.
    band_touch_count = 0

    return {
        "total": total_playbook + band_touch_count,
        "playbook_signal_count": total_playbook,
        "band_touch_count": band_touch_count,
        "by_setup_id": by_setup_id,
    }
