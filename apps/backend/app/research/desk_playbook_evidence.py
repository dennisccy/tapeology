"""The Playbook Evidence view (Era B2, J-08) -- a READ-ONLY fold of every already-recorded
``PlaybookStore`` record at ONE signature into per-``(setup_id, side, measure)`` distribution
cells beside the pooled seeded baseline, honestly tagging low-``n`` cells. Nothing here detects,
measures, or records anything new -- it reads what ``desk_playbook.py``'s own compute already
wrote (``PlaybookStore.get``, ``compute_playbook_input_signature``, ``playbook_parameters``, all
imported verbatim) and folds it.

**Zero re-implementation of the measurement rail.** Every signal's ``forward`` block and every
baseline anchor's own forward-shaped measurement were ALREADY produced by
``desk_forward._measure_from`` at compute time (see ``desk_playbook.py``'s own docstring); this
module never touches a bar, never calls ``_measure_from``, and reuses
``desk_forward._collect_measures`` (imported verbatim, zero diff) to pool the ALREADY-MEASURED
per-signal/per-anchor leaves into per-measure value lists with their truncation-exclusion already
applied. The genuinely new math here is EVIDENCE-only, never a second implementation of anything
the rail already had: the quartile fold (``_quartile_stats``) -- ``_collect_measures``/
``_avg_cell`` (the rail's own pooling helpers) produce ``n``/``mean_pct``/``median_pct``/
``n_truncated`` but carry no p25/p75 at all, so J-08 folds those two itself -- and (J-11) the
exclusion-count fold (``_n_unmeasured_by_label``), which COUNTS, never re-derives, how many pooled
events carry a null ``return_pct`` at each horizon label: the exact fact
``_collect_measures``'s own ``if measure["return_pct"] is None: continue`` already reads per event
and then lets evaporate uncounted. This module also folds ``n_sessions`` -- the number of distinct
recorded ``session_date``s behind a pool -- straight off the per-file projection's own
``session_date``, again zero re-derivation of anything the rail or the store computes.

**The evidence pools exactly ONE signature (a hard anti-goal).** ``fold_evidence`` resolves the
CURRENT default signature via ``compute_playbook_input_signature`` (the exact function
``compute_playbook`` itself calls) and only ever folds a file whose own recorded
``playbook_input_signature`` matches it into ``cells``/``invalidation_breached``; every other
signature is listed under ``other_signatures`` (its own ``dates``/``created_span``), NEVER pooled.
``inspect_signature`` (``?signature=``) answers the SAME dates/created-span question for one named
signature, default or not, without ever touching ``cells`` -- "inspect", never "pool".

**Cells are the FULL declared cross product, never sparse.** Every ``(setup_id, side, measure)``
combination in ``PLAYBOOK_SETUPS`` x ``("long", "short")`` x ``PLAYBOOK_SIGNAL_MEASURES`` is always
served, so a combination with zero recorded signals reads ``n: 0`` (an honest absence, never a
fabricated 0.0 in the mean/median/p25/p75 slots -- ``_quartile_stats`` returns ``None`` across the
board at ``n == 0``, the ``_avg_cell`` null convention) rather than being silently omitted. This
also makes the served body deterministic and independent of file-processing order -- byte-identity
between a cold and a warm cache read (TC-2) does not depend on dict insertion order surviving a
JSON cache round trip, because ``cells``/``invalidation_breached`` are always built by iterating
the SAME fixed, declared sequences.

**The projection cache mirrors ``desk_meta_cache.py``'s contract -- a copy-paste precedent, not an
import.** ``desk_meta_cache.DeskMetaCache`` caches a lightweight META-ONLY projection keyed off
ONE store's own files; this module's own fold needs a DIFFERENT per-file projection shape (every
recorded signal's ``forward``/``invalidation_breached`` leaves, grouped by pool key, plus the
record's own ``baseline_anchors``) that store was never built to hold, and reusing its class across
an unrelated schema would either widen a foundation file for one caller or force this module to
smuggle its own shape through a generic blob -- `PlaybookEvidenceCache` below is therefore a fresh,
small class following the EXACT same rules (stat-keyed by ``(path, size, mtime_ns)``, ``json.dumps``
WITHOUT ``sort_keys`` so a cache hit reproduces the identical key order a fresh parse would, no
``update``/``delete`` method anywhere on the class -- a stale row is simply replaced by
``INSERT OR REPLACE`` under its own path, never edited or removed). Deleting the DB file changes
nothing about ``fold_evidence``'s OUTPUT -- only how many files must be re-verified through
``PlaybookStore.get`` to reproduce it (TC-6): an unopenable/deleted cache is a missing
optimisation, never a failed read (the ``ForwardStore._durable_meta_cache`` rule, applied at the
FastAPI dependency layer in ``desk_routes.py`` since this module's own functions take the cache as
a plain optional argument rather than owning a store instance)."""

from __future__ import annotations

import json
import sqlite3
import statistics
import threading
from pathlib import Path

from .desk_forward import DESK_FORWARD_HORIZONS_MINUTES, _collect_measures
from .desk_playbook import (
    PLAYBOOK_MIN_N_DISCLOSURE,
    PLAYBOOK_SETUPS,
    PLAYBOOK_SIGNAL_MEASURES,
    PlaybookStore,
    compute_playbook_input_signature,
    playbook_parameters,
)
# Read-side -> read-side only. This module reads the band-context LENS; the lens never reads this
# module (no cycle), and neither is reachable from `compute_playbook`'s own walk.
from .desk_playbook_context import (
    CONTEXT_REGISTER,
    LOCATED,
    NO_BAND_CONTEXT,
    NOT_COMPUTED,
    PLAYBOOK_CONTEXT_BACKING_BUCKETS,
    PLAYBOOK_CONTEXT_ROOM_BUCKETS,
    ROOM_UNMEASURED,
    BandMapResolver,
    PlaybookContextCache,
    cached_context,
    context_parameters,
    record_map_requests,
)

__all__ = [
    "EVIDENCE_REGISTER",
    "EVIDENCE_TABLE",
    "PlaybookEvidenceCache",
    "fold_band_context",
    "fold_evidence",
    "inspect_signature",
]

# The projection shape version -- bumped when a projection gains FIELDS a fold needs. A cached row
# at an older version is a miss (see `_projections_by_signature`), never a partial hit. The v2
# band-context frame did NOT bump it: buckets live on the context, not the projection, so the
# projection cache stays warm across a lens revision.
_PROJECTION_VERSION = 2

# The five DIRECTIONAL measures -- the four rail horizons plus `to_close`. Only these are split by
# location: a drawdown is clamped <= 0 by construction, so splitting it by where the trade sat would
# multiply rows without adding a reading. The UNSPLIT table still serves all 15 measures.
# Derived from the rail's own horizon declaration rather than spelled out; deliberately a SECOND
# name from `_BREACH_HORIZONS` (same values today, different meaning -- one is "which windows can be
# measured", the other is "which windows carry a breach flag").
_DIRECTIONAL_MEASURES: tuple[str, ...] = tuple(
    label for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES
) + ("to_close",)

# Every side a signal can carry (``desk_playbook_detect.py``'s own complete vocabulary) -- a fixed,
# declared pair, never discovered from data (see the module docstring: cells are the full cross
# product, not a sparse "whatever appeared" set).
_SIDES: tuple[str, ...] = ("long", "short")

# The invalidation-breach horizon vocabulary -- the rail's own four labels plus ``to_close``,
# mirroring ``desk_playbook._invalidation_breached``'s own served keys exactly (that function is
# the ONLY writer of this shape; this module only reads and pools it).
_BREACH_HORIZONS: tuple[str, ...] = tuple(
    label for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES
) + ("to_close",)

# The visible honesty register carried by every evidence payload -- the ``PLAYBOOK_REGISTER``/
# ``FORWARD_REGISTER`` pattern verbatim (a single descriptive string, lint-checked via
# ``test_copy_discipline.find_violations`` in ``tests/test_desk_playbook_evidence.py``, the SAME
# per-module precedent those two constants use rather than a change to ``test_copy_discipline.py``
# itself, which carries no per-register assertion for any existing REGISTER constant either).
EVIDENCE_REGISTER = (
    "every recorded playbook signal at ONE input signature, pooled per setup/side/measure into "
    "forward-return and max-drawdown distributions beside the pooled baseline — the seeded random "
    "anchors already drawn beside those signals at compute time, one anchor per signal up to each "
    "session's own per-setup-and-side pooling cap, so a cell whose n_baseline is smaller than its "
    "n is one where that cap was reached and the two columns do not cover the same set of signals. "
    "Median, p25, p75, and mean of the "
    "already-recorded, already-measured values, nothing recomputed and nothing fit to an outcome. "
    "A cell tagged below_min_n has fewer than the disclosure floor's worth of recorded signals — "
    "a disclosure, never a filter: its numbers are still served, never hidden, never nulled out "
    "for being thin. Truncated values are excluded from every median/mean pool with the exclusion "
    "counted, never silently dropped — and a signal whose own horizon leaf was recorded "
    "unmeasurable at that window (finer than the session's own recorded touch series) is excluded "
    "the same way, counted as n_unmeasured instead of n_truncated, on the signal side and, "
    "identically, on the baseline side (n_truncated, n_unmeasured), beside n_sessions, the number "
    "of distinct recorded dates each pool draws from. A signature other than the current one is "
    "listed by its own dates, record count, and created span, never folded into these cells, and "
    "the pooled signature's own record count, dates, and created span are named the same way, up "
    "front, in this payload's own basis block. No fills and no costs are modeled "
    "anywhere on this payload, which describes measurements of what already happened and nothing "
    "about what happens next"
)

_BUSY_TIMEOUT_MS = 5000
EVIDENCE_TABLE = "playbook_evidence_meta_cache"


class PlaybookEvidenceCache:
    """The durable, stat-keyed per-file evidence-projection cache for ONE playbook store --
    ``desk_meta_cache.DeskMetaCache``'s contract, copied fresh (see the module docstring for why a
    new class rather than an import). Owns nothing: every row only ever remembers one
    already-verified file's own already-extracted projection, keyed by that file's exact
    ``(path, size, mtime_ns)``. Deliberately carries no ``update``/``delete`` method anywhere on
    this class (structural, guard-tested) -- ``insert``/``insert_many`` are ``INSERT OR REPLACE``,
    idempotent under the identical key a legitimately re-verified file would produce."""

    def __init__(self, db_path: str) -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # One connection, several threads (FastAPI's sync-route threadpool) -- the
        # ``bar_index.py``/``desk_meta_cache.py`` serialization, for the identical reason.
        self._lock = threading.Lock()
        if self._db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
        with self._lock, self._conn:
            self._conn.execute(
                f"CREATE TABLE IF NOT EXISTS {EVIDENCE_TABLE} ("
                "    path         TEXT PRIMARY KEY,"
                "    size         INTEGER NOT NULL,"
                "    mtime_ns     INTEGER NOT NULL,"
                "    meta_json    TEXT NOT NULL)"
            )

    @property
    def db_path(self) -> str:
        return self._db_path

    def lookup(self, path: str, size: int, mtime_ns: int) -> dict | None:
        """An exact ``(path, size, mtime_ns)`` match -- ANY stat difference (a genuine content
        change, a moved file, or simply no row yet) is an honest miss, never a stale hit."""
        with self._lock:
            row = self._conn.execute(
                f"SELECT size, mtime_ns, meta_json FROM {EVIDENCE_TABLE} WHERE path=?", (path,)
            ).fetchone()
        if row is None or row["size"] != size or row["mtime_ns"] != mtime_ns:
            return None
        return json.loads(row["meta_json"])

    def insert(self, path: str, size: int, mtime_ns: int, projection: dict) -> None:
        """Additively remember ONE already-extracted file projection. ``json.dumps`` WITHOUT
        ``sort_keys`` -- a cache hit must reproduce the EXACT key order a fresh extraction would
        (the ``desk_meta_cache.py`` byte-identity precedent), so a served response never differs
        between a cold and a warm read (TC-2)."""
        with self._lock, self._conn:
            self._conn.execute(
                f"INSERT OR REPLACE INTO {EVIDENCE_TABLE} (path, size, mtime_ns, meta_json) "
                "VALUES (?,?,?,?)",
                (path, size, mtime_ns, json.dumps(projection)),
            )


# --- per-file projection extraction (pure data extraction -- zero measurement) ----------------------


def _file_projection(record: dict) -> dict:
    """Extract ONE already-verified playbook record's own per-``(setup_id, side)`` signal/baseline
    forward-shaped events plus per-``(setup_id, side, horizon)`` invalidation-breach counts -- pure
    grouping of data ``compute_playbook`` already wrote; nothing here calls ``_measure_from`` or
    any other rail function. A signal recorded before J-02's measurement pass existed (an honest,
    older-format record) carries no ``forward`` block -- it is excluded from this record's own
    projection (the same "predates measurement" absence ``PlaybookStore._registered`` already reads
    back verbatim for the record-level fields), never fabricated, never a crash."""
    signal_events: dict[str, list[dict]] = {}
    breach_counts: dict[str, dict[str, dict[str, int]]] = {}
    for signal in record["signals"]:
        forward = signal.get("forward")
        if forward is None:
            continue
        pool_key = f"{signal['setup_id']}:{signal['side']}"
        signal_events.setdefault(pool_key, []).append(forward)
        breached = signal.get("invalidation_breached") or {}
        counts = breach_counts.setdefault(pool_key, {})
        for horizon in _BREACH_HORIZONS:
            if horizon not in breached:
                continue
            cell = counts.setdefault(horizon, {"breached": 0, "total": 0})
            cell["total"] += 1
            if breached[horizon]:
                cell["breached"] += 1
    return {
        # v2 (band context): adds `playbook_id` + `map_requests` — the key material the band-context
        # cache needs to answer WITHOUT re-reading this file. A row cached at v1 lacks both and is
        # treated as a miss by `_projections_by_signature`, then re-extracted and replaced under the
        # same stat key; nothing is served from a v1 row and nothing about the v1 numbers changes.
        "projection_version": 2,
        "playbook_id": record["id"],
        "playbook_input_signature": record["playbook_input_signature"],
        "session_date": record["session_date"],
        "recorded_at": record["recorded_at"],
        "map_requests": record_map_requests(record),
        "signal_events": signal_events,
        "baseline_events": {
            key: list(events) for key, events in record.get("baseline_anchors", {}).items()
        },
        "breach_counts": breach_counts,
    }


def _projections_by_signature(
    store: PlaybookStore, cache: PlaybookEvidenceCache | None
) -> list[dict]:
    """Every recorded playbook file's own projection, oldest-path-first -- a cache hit skips the
    file's own parse+checksum verification entirely; a cache miss reads it through
    ``PlaybookStore.get`` (the store's own public, verified reader -- zero re-implementation of its
    checksum/corruption handling) and remembers the freshly extracted projection for next time. A
    file that fails verification (``PlaybookStore.get`` returns ``None``) is silently excluded from
    the fold -- ``GET /research/desk/playbook``'s own ``integrity_errors`` already surfaces a
    corrupted file explicitly; this evidence fold does not duplicate that disclosure, it simply
    never crashes and never fabricates a projection for a file it could not verify."""
    if not store.root.exists():
        return []
    projections: list[dict] = []
    for path in sorted(store.root.glob("*.json")):
        try:
            stat = path.stat()
        except OSError:
            continue
        key = str(path)
        cached = cache.lookup(key, stat.st_size, stat.st_mtime_ns) if cache is not None else None
        # A row written before the projection grew its band-context key material is an honest MISS,
        # never a partial hit: re-extraction is cheap, and serving a v1 row would leave the split
        # unable to name the maps it was built from.
        if cached is not None and cached.get("projection_version") == _PROJECTION_VERSION:
            projections.append(cached)
            continue
        record = store.get(path.stem)
        if record is None:
            continue
        projection = _file_projection(record)
        if cache is not None:
            cache.insert(key, stat.st_size, stat.st_mtime_ns, projection)
        projections.append(projection)
    return projections


def _path_stats(store: PlaybookStore) -> dict[str, tuple[int, int]]:
    """``{playbook_id: (size, mtime_ns)}`` for every recorded file — a ``glob`` plus one ``stat``
    each, zero file CONTENT read. The band-context cache keys each record's context on its file
    identity, and this is how a fold names that identity without undoing the projection cache's own
    reason for existing."""
    if not store.root.exists():
        return {}
    stats: dict[str, tuple[int, int]] = {}
    for path in sorted(store.root.glob("*.json")):
        try:
            stat = path.stat()
        except OSError:
            continue
        stats[path.stem] = (stat.st_size, stat.st_mtime_ns)
    return stats


# --- the quartile fold (new evidence-only math -- see the module docstring) -------------------------


def _quartile_stats(values: list[float]) -> tuple[float | None, float | None, float | None, float | None]:
    """``(median, p25, p75, mean)`` over one pooled value list -- ``None`` across the board at
    ``n == 0`` (``_avg_cell``'s own honest-absence convention, never a fabricated 0.0). At
    ``n == 1`` every one of the four readings IS that single value (``statistics.quantiles``
    refuses fewer than two points, and repeating the lone value is the only non-fabricating
    reading of "this cell's own p25/p75/median/mean"). ``method="inclusive"`` (linear
    interpolation between order statistics, the common convention) is the ONE deterministic
    quantile method this module ever uses -- proven against TC-1's hand-computed fixture."""
    if not values:
        return None, None, None, None
    if len(values) == 1:
        v = values[0]
        return v, v, v, v
    p25, _p50, p75 = statistics.quantiles(values, n=4, method="inclusive")
    return statistics.median(values), p25, p75, statistics.mean(values)


def _n_positive_for(measure: str, values: list[float]) -> int | None:
    """How many of this cell's OWN pooled values are strictly greater than zero — counted over the
    exact same untruncated list ``_quartile_stats`` medians and means, so "positive: 14 of 20" and
    "median of 20" always describe one pool, never two.

    Only the five DIRECTIONAL measures carry it (the four horizon returns and ``to_close``). A
    return is side-relative — ``desk_forward``'s own sign convention makes a positive number mean
    price moved the way the setup's own side implied — so this is a plain count of recorded moves
    in that direction, arithmetic over values already on disk.

    ``None`` for the ten ``mdd_*`` measures: a drawdown is clamped ``<= 0`` by construction, so
    "greater than zero" is not a fact those measures can carry, and serving ``0`` there would read
    as a measured absence of something rather than the category error it is. Strictly ``> 0``: a
    recorded ``0.0`` (a real measured "went nowhere") is not counted as a move in either direction."""
    if measure.startswith("mdd_"):
        return None
    return sum(1 for value in values if value > 0.0)


def _positive_share(n_positive: int | None, n: int) -> float | None:
    """``n_positive / n`` -- a share of the SAME pooled values, computed once server-side so no
    surface divides served numbers of its own. ``None`` wherever the count itself is meaningless
    (every ``mdd_*`` measure) or the pool is empty (a share of nothing is not 0.0)."""
    if n_positive is None or n == 0:
        return None
    return n_positive / n


def _signal_cell(
    measure: str, values: list[float], n_truncated: int, n_unmeasured: int, n_sessions: int
) -> dict:
    median, p25, p75, mean = _quartile_stats(values)
    return {
        "n": len(values),
        "n_positive": _n_positive_for(measure, values),
        # The same count restated against the same pool -- served so a reader (and a sorted column)
        # never has to divide two served numbers to compare cohorts of different sizes. `None`
        # exactly where `n_positive` is: at n == 0, and on every drawdown measure.
        "positive_share": _positive_share(_n_positive_for(measure, values), len(values)),
        "n_truncated": n_truncated,
        "n_unmeasured": n_unmeasured,
        "n_sessions": n_sessions,
        "median_pct": median,
        "p25_pct": p25,
        "p75_pct": p75,
        "mean_pct": mean,
    }


def _baseline_cell(
    measure: str, values: list[float], n_truncated: int, n_unmeasured: int, n_sessions: int
) -> dict:
    median, p25, p75, mean = _quartile_stats(values)
    return {
        "n_baseline": len(values),
        "n_positive": _n_positive_for(measure, values),
        # The same count restated against the same pool -- served so a reader (and a sorted column)
        # never has to divide two served numbers to compare cohorts of different sizes. `None`
        # exactly where `n_positive` is: at n == 0, and on every drawdown measure.
        "positive_share": _positive_share(_n_positive_for(measure, values), len(values)),
        "n_truncated": n_truncated,
        "n_unmeasured": n_unmeasured,
        "n_sessions": n_sessions,
        "median_pct": median,
        "p25_pct": p25,
        "p75_pct": p75,
        "mean_pct": mean,
    }


# --- exclusion counting (J-11, new evidence-only math -- pure counts, never a re-measurement) -------

# The four rail horizon LABELS, in the rail's own declared order -- NOT re-derived from
# PLAYBOOK_SIGNAL_MEASURES/DESK_FORWARD_MEASURE_KEYS, whose own order interleaves them with the
# session-level trio and the mdd siblings.
_HORIZON_LABELS: tuple[str, ...] = tuple(label for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES)


def _measure_horizon_label(measure: str) -> str | None:
    """Which of the four horizon LABELS governs ``measure``'s own unmeasurability -- a horizon's
    own return key (e.g. ``"1h"``) and its two ``mdd_long_1h``/``mdd_short_1h`` siblings all read
    the EXACT SAME ``event["horizons"]["1h"]["return_pct"]`` fact (``_measure_from`` writes a
    horizon leaf as one all-null shape or one all-populated shape, never a mix), so all three
    measure keys share one label and therefore one shared count (TC-2). ``None`` for the
    session-level trio (``to_close``/``mdd_long``/``mdd_short``), which reads the session-end
    fields ``_measure_from`` always populates -- never unmeasurable."""
    if measure in _HORIZON_LABELS:
        return measure
    for prefix in ("mdd_long_", "mdd_short_"):
        if measure.startswith(prefix) and measure[len(prefix) :] in _HORIZON_LABELS:
            return measure[len(prefix) :]
    return None


def _n_unmeasured_by_label(events: list[dict]) -> dict[str, int]:
    """Per horizon LABEL, how many of ``events`` carry ``return_pct: None`` there -- the exact fact
    ``desk_forward._collect_measures`` silently ``continue``s past with no counter. Read directly
    off each event's own leaf, never derived by subtracting pool lengths (the module NOTES this
    iteration carries: an MDD sibling's own value list can in principle be shorter than its return
    sibling's for a reason UNRELATED to unmeasurability -- a pre-per-horizon-MDD legacy leaf missing
    ``mdd_long_pct``/``mdd_short_pct`` while ``return_pct`` is populated; never observed in playbook
    data today, not provably impossible, and a subtraction-only reading would silently get it wrong
    the day it is). Every label is always a key, even at ``0`` -- an empty ``events`` list (an empty
    pool) reads every label ``0``, never an omitted key, mirroring the existing zero-signals
    precedent the rest of this module already follows."""
    counts = {label: 0 for label in _HORIZON_LABELS}
    for event in events:
        horizons = event.get("horizons") or {}
        for label in _HORIZON_LABELS:
            leaf = horizons.get(label)
            if leaf is not None and leaf.get("return_pct") is None:
                counts[label] += 1
    return counts


def _n_unmeasured_for(measure: str, unmeasured_by_label: dict[str, int]) -> int:
    """``0`` for the session-level trio (never unmeasurable); otherwise the SAME count its own
    horizon label's return key and its two mdd siblings all share -- never independently
    recomputed per measure key (TC-2)."""
    label = _measure_horizon_label(measure)
    return unmeasured_by_label[label] if label is not None else 0


def _fold_cells(default_projections: list[dict]) -> list[dict]:
    """The FULL declared cross product of ``PLAYBOOK_SETUPS`` x sides x
    ``PLAYBOOK_SIGNAL_MEASURES`` -- every cell served, never a sparse "whatever fired" set (see the
    module docstring). ``_collect_measures`` (the rail's own pooling helper, imported verbatim) does
    the ENTIRE truncation-exclusion/grouping-by-measure-key job; this function only pools the raw
    per-file event lists across every default-signature file first, so a signal recorded in one
    session-date's file and a signal recorded in another's pool into the SAME cell exactly as if
    they had been measured in one walk.

    ``n_unmeasured`` and ``n_sessions`` (J-11) are each computed ONCE per ``(setup_id, side)`` pool
    -- not independently per measure -- then applied identically to every one of that pool's
    ``PLAYBOOK_SIGNAL_MEASURES`` cells: ``n_unmeasured`` shares one count per horizon LABEL across a
    return key and its two mdd siblings (``_n_unmeasured_for``), and ``n_sessions`` counts distinct
    recorded dates behind the WHOLE pool of raw signal events, not behind any one measure's own
    filtered sub-pool (a session contributed ``>= 1`` signal, full stop -- which horizons that
    signal happened to measure at is a separate, per-measure fact already carried by ``n``/
    ``n_truncated``/``n_unmeasured``)."""
    cells: list[dict] = []
    for setup_id in PLAYBOOK_SETUPS:
        for side in _SIDES:
            pool_key = f"{setup_id}:{side}"
            signal_events: list[dict] = []
            baseline_events: list[dict] = []
            signal_dates: set[str] = set()
            baseline_dates: set[str] = set()
            for projection in default_projections:
                pool_signals = projection["signal_events"].get(pool_key, [])
                pool_baseline = projection["baseline_events"].get(pool_key, [])
                signal_events.extend(pool_signals)
                baseline_events.extend(pool_baseline)
                if pool_signals:
                    signal_dates.add(projection["session_date"])
                if pool_baseline:
                    baseline_dates.add(projection["session_date"])
            signal_pools = _collect_measures(signal_events)
            baseline_pools = _collect_measures(baseline_events)
            signal_unmeasured = _n_unmeasured_by_label(signal_events)
            baseline_unmeasured = _n_unmeasured_by_label(baseline_events)
            n_sessions_signal = len(signal_dates)
            n_sessions_baseline = len(baseline_dates)
            for measure in PLAYBOOK_SIGNAL_MEASURES:
                signal_values, n_truncated = signal_pools[measure]
                baseline_values, baseline_truncated = baseline_pools[measure]
                signal_block = _signal_cell(
                    measure,
                    signal_values,
                    n_truncated,
                    _n_unmeasured_for(measure, signal_unmeasured),
                    n_sessions_signal,
                )
                cells.append(
                    {
                        "setup_id": setup_id,
                        "side": side,
                        "measure": measure,
                        "signal": signal_block,
                        "baseline": _baseline_cell(
                            measure,
                            baseline_values,
                            baseline_truncated,
                            _n_unmeasured_for(measure, baseline_unmeasured),
                            n_sessions_baseline,
                        ),
                        "below_min_n": signal_block["n"] < PLAYBOOK_MIN_N_DISCLOSURE,
                    }
                )
    return cells


def _event_coordinates(context: dict | None) -> tuple[dict, dict]:
    """Per pool, the ordered (backing, room) coordinate of each measured signal and each anchor —
    or ``None`` where the event carries no location. Reads ONLY served context fields; this module
    never re-derives a bucket."""
    signal_coords: dict[str, list] = {}
    anchor_coords: dict[str, list] = {}
    if not context:
        return signal_coords, anchor_coords
    for signal in context.get("signals", []):
        if signal.get("measured"):
            signal_coords.setdefault(signal["pool_key"], []).append(_coordinate(signal))
    for pool_key, rows in (context.get("baseline_anchors") or {}).items():
        anchor_coords[pool_key] = [_coordinate(row) for row in rows]
    return signal_coords, anchor_coords


def _coordinate(event: dict):
    """One event's split coordinate: ``(backing_bucket, room_bucket)`` when it is placeable, else
    the single state naming WHY it is not (an absence status, or a measured headroom with no
    invalidation distance to divide by)."""
    band_context = event["band_context"]
    if band_context["status"] != LOCATED:
        return band_context["status"]
    room = band_context["room_bucket"]
    if room == ROOM_UNMEASURED:
        return ROOM_UNMEASURED
    return (band_context["backing_bucket"], room)


def _tally_coordinate(counts: dict[str, int], coordinate) -> None:
    """Every event increments exactly one backing state and one room state, so each axis
    independently sums to the record's own event total."""
    if isinstance(coordinate, tuple):
        counts[coordinate[0]] += 1
        counts[coordinate[1]] += 1
    else:
        counts[coordinate] += 1


def _new_split_counts() -> dict[str, int]:
    keys = (
        (NO_BAND_CONTEXT, NOT_COMPUTED, ROOM_UNMEASURED)
        + PLAYBOOK_CONTEXT_BACKING_BUCKETS
        + PLAYBOOK_CONTEXT_ROOM_BUCKETS
    )
    return {key: 0 for key in keys}


def _bucketed_events(projection: dict, context: dict | None) -> tuple[dict, dict, dict]:
    """This record's own signal and baseline events REGROUPED by their (backing, room) coordinate,
    plus the counts behind that regrouping.

    Alignment: ``_file_projection`` appends a pool's events in record order (skipping a signal with
    no ``forward``), and ``record_band_context`` walks the same record in the same order tagging
    each signal ``measured`` — so filtering the context's signals to ``measured`` and grouping by
    ``pool_key`` reproduces exactly the projection's own per-pool ordering. That correspondence is
    checked, not trusted: any pool whose two lengths disagree contributes its events as
    ``no_band_context`` rather than risking a mispaired coordinate."""
    signal_out: dict[tuple, list[dict]] = {}
    baseline_out: dict[tuple, list[dict]] = {}
    counts = _new_split_counts()
    anchor_counts = _new_split_counts()
    signal_coords, anchor_coords = _event_coordinates(context)

    for source, coords, out, tally in (
        (projection["signal_events"], signal_coords, signal_out, counts),
        (projection["baseline_events"], anchor_coords, baseline_out, anchor_counts),
    ):
        for pool_key, events in source.items():
            pool_coords = coords.get(pool_key)
            if pool_coords is None or len(pool_coords) != len(events):
                pool_coords = [NO_BAND_CONTEXT] * len(events)
            for event, coordinate in zip(events, pool_coords):
                _tally_coordinate(tally, coordinate)
                if isinstance(coordinate, tuple):
                    out.setdefault((pool_key, *coordinate), []).append(event)
    return signal_out, baseline_out, {"signals": counts, "anchors": anchor_counts}


def fold_band_context(
    default_projections: list[dict],
    contexts_by_id: dict[str, dict],
) -> dict:
    """The structural split: the SAME cells, the SAME builders, the SAME pooling rules as the
    unsplit table, computed once more per declared (backing, room) cohort.

    The two DECLARED axes are ``PLAYBOOK_CONTEXT_BACKING_BUCKETS`` (is there a wall behind this
    trade, and is the trade at it?) x ``PLAYBOOK_CONTEXT_ROOM_BUCKETS`` (how far is the wall ahead,
    in multiples of this trade's own invalidation distance?), served as the full cross product
    setups x sides x backing x room x the five DIRECTIONAL measures, every cell present even at
    ``n: 0``. The joint grid is the point: "backed by structure" and "with room to travel" are two
    different questions, and a trade is taken on both at once.

    Only the five return measures are split (``_DIRECTIONAL_MEASURES``) — a drawdown is clamped
    ``<= 0`` by construction, so splitting it by location would multiply rows without adding a
    reading; the unsplit table above still serves all fifteen.

    Three states are EXCLUSIONS, counted in this block's own ``basis`` exactly the way
    ``n_truncated``/``n_unmeasured`` are counted beside every cell, never served as distribution
    cells: a map not computed yet, a computed map with no band anywhere around the price, and a
    measured headroom with no invalidation distance to divide by. A distribution over "this is not
    known" would describe nothing, but how much is not known must be visible.

    ``below_min_n`` tags a thin cell and NEVER filters it — the same floor, the same disclosure
    rule, applied to a split whose cells are thinner than the unsplit table's by construction."""
    signal_pools: dict[tuple, list[dict]] = {}
    baseline_pools: dict[tuple, list[dict]] = {}
    signal_dates: dict[tuple, set[str]] = {}
    baseline_dates: dict[tuple, set[str]] = {}
    template = _new_split_counts()
    basis_counts = {f"n_signals_{state}": 0 for state in template}
    basis_counts.update({f"n_anchors_{state}": 0 for state in template})
    n_unattributable = 0

    for projection in default_projections:
        context = contexts_by_id.get(projection.get("playbook_id"))
        signal_out, baseline_out, counts = _bucketed_events(projection, context)
        for state in template:
            basis_counts[f"n_signals_{state}"] += counts["signals"][state]
            basis_counts[f"n_anchors_{state}"] += counts["anchors"][state]
        if context:
            n_unattributable += context.get("basis", {}).get("n_anchors_unattributable", 0)
        for key, events in signal_out.items():
            signal_pools.setdefault(key, []).extend(events)
            signal_dates.setdefault(key, set()).add(projection["session_date"])
        for key, events in baseline_out.items():
            baseline_pools.setdefault(key, []).extend(events)
            baseline_dates.setdefault(key, set()).add(projection["session_date"])

    cells: list[dict] = []
    for setup_id in PLAYBOOK_SETUPS:
        for side in _SIDES:
            pool_key = f"{setup_id}:{side}"
            for backing in PLAYBOOK_CONTEXT_BACKING_BUCKETS:
                for room in PLAYBOOK_CONTEXT_ROOM_BUCKETS:
                    key = (pool_key, backing, room)
                    signal_events = signal_pools.get(key, [])
                    baseline_events = baseline_pools.get(key, [])
                    signal_measures = _collect_measures(signal_events)
                    baseline_measures = _collect_measures(baseline_events)
                    signal_unmeasured = _n_unmeasured_by_label(signal_events)
                    baseline_unmeasured = _n_unmeasured_by_label(baseline_events)
                    n_sessions_signal = len(signal_dates.get(key, set()))
                    n_sessions_baseline = len(baseline_dates.get(key, set()))
                    for measure in _DIRECTIONAL_MEASURES:
                        signal_values, signal_truncated = signal_measures[measure]
                        baseline_values, baseline_truncated = baseline_measures[measure]
                        signal_block = _signal_cell(
                            measure,
                            signal_values,
                            signal_truncated,
                            _n_unmeasured_for(measure, signal_unmeasured),
                            n_sessions_signal,
                        )
                        cells.append(
                            {
                                "setup_id": setup_id,
                                "side": side,
                                "measure": measure,
                                "backing_bucket": backing,
                                "room_bucket": room,
                                "signal": signal_block,
                                "baseline": _baseline_cell(
                                    measure,
                                    baseline_values,
                                    baseline_truncated,
                                    _n_unmeasured_for(measure, baseline_unmeasured),
                                    n_sessions_baseline,
                                ),
                                "below_min_n": signal_block["n"] < PLAYBOOK_MIN_N_DISCLOSURE,
                            }
                        )
    return {
        "parameters": context_parameters(),
        "cells": cells,
        "basis": {**basis_counts, "n_anchors_unattributable": n_unattributable},
        "register": CONTEXT_REGISTER,
    }


def _fold_invalidation_breached(default_projections: list[dict]) -> list[dict]:
    """The FULL declared cross product of setups x sides x breach horizons, each entry a plain sum
    of the per-file breach counts already extracted by ``_file_projection`` -- no re-derivation of
    "did price breach the level", that fact was already computed once, outside ``_measure_from``,
    by ``desk_playbook._invalidation_breached`` at compute time."""
    entries: list[dict] = []
    for setup_id in PLAYBOOK_SETUPS:
        for side in _SIDES:
            pool_key = f"{setup_id}:{side}"
            for horizon in _BREACH_HORIZONS:
                breached = 0
                total = 0
                for projection in default_projections:
                    counts = projection["breach_counts"].get(pool_key, {}).get(horizon)
                    if counts is not None:
                        breached += counts["breached"]
                        total += counts["total"]
                entries.append(
                    {
                        "setup_id": setup_id,
                        "side": side,
                        "horizon": horizon,
                        "breached_count": breached,
                        "total_count": total,
                    }
                )
    return entries


def _signature_basis(projections: list[dict]) -> dict:
    """The ``dates``/``n_records``/``created_span`` ONE signature's own recorded projections
    disclose -- extracted so ``_fold_other_signatures`` (below) and ``fold_evidence``'s new
    payload-level ``basis`` block (J-11) both call the SAME summarizer instead of each growing its
    own copy. ``dates`` deduplicated and sorted (a signature can record at most ONE file per date --
    ``PlaybookStore``'s own 2-pin key refuses a duplicate -- so dedup here is defensive, not
    load-bearing); ``n_records`` is the plain count of ``projections`` (by that same 2-pin-key
    invariant, always equal to ``len(dates)`` for a fixed signature -- served as its own field
    anyway so a reader is never asked to derive it). ``created_span`` is ``None`` iff ``projections``
    is empty, matching ``inspect_signature``'s own ``min``/``max`` convention byte-for-byte (both
    read the identical ``session_date``/``recorded_at`` fields off the identical records -- one via
    a projection, the other via a fresh ``store.get`` -- so the two are provably the same computation
    under two different callers, not two independent ones; TC-5)."""
    dates = sorted({p["session_date"] for p in projections})
    recorded_ats = sorted(p["recorded_at"] for p in projections)
    created_span = {"from": recorded_ats[0], "to": recorded_ats[-1]} if recorded_ats else None
    return {"dates": dates, "n_records": len(projections), "created_span": created_span}


def _fold_other_signatures(other_projections: list[dict]) -> list[dict]:
    """Every NON-default signature present, its own ``dates``/``n_records``/``created_span`` only --
    listed, never pooled (the hard anti-goal: "the evidence pools one signature"). Signatures sorted
    for a deterministic served order."""
    by_signature: dict[str, list[dict]] = {}
    for projection in other_projections:
        by_signature.setdefault(projection["playbook_input_signature"], []).append(projection)
    result: list[dict] = []
    for signature in sorted(by_signature):
        result.append({"signature": signature, **_signature_basis(by_signature[signature])})
    return result


def _contexts_for(
    store: PlaybookStore,
    default_projections: list[dict],
    bar_store,
    config,
    context_cache: PlaybookContextCache | None,
) -> dict[str, dict]:
    """Every pooled record's band context, keyed by playbook id — served from the durable context
    cache, and LOOKUP-ONLY throughout (``BandMapResolver`` defaults to ``compute=False``): a fold is
    a GET path, and a GET never pays a ~1,800-map computation. A record whose context has not been
    warmed simply contributes ``not_computed`` events, counted honestly in the split's basis.

    Returns ``{}`` — an empty split rather than a broken one — if the resolver cannot even be built
    (no bar store, an unreadable store listing): band context is an ADDITIVE disclosure, and its
    absence must never take the evidence table down with it."""
    if not default_projections:
        return {}
    try:
        resolver = BandMapResolver(bar_store, config)
    except Exception:  # pragma: no cover - defensive: an accelerator never breaks the read
        return {}
    stats = _path_stats(store)
    contexts: dict[str, dict] = {}
    for projection in default_projections:
        playbook_id = projection.get("playbook_id")
        if playbook_id is None or playbook_id not in stats:
            continue
        size, mtime_ns = stats[playbook_id]
        context = cached_context(
            playbook_id=playbook_id,
            stat_size=size,
            stat_mtime_ns=mtime_ns,
            map_requests=projection.get("map_requests") or [],
            load_record=lambda pid=playbook_id: store.get(pid),
            resolver=resolver,
            cache=context_cache,
        )
        if context:
            contexts[playbook_id] = context
    return contexts


def fold_evidence(
    store: PlaybookStore,
    bar_store,
    members: list[str],
    config_fingerprint: str,
    *,
    cache: PlaybookEvidenceCache | None = None,
    context_cache: PlaybookContextCache | None = None,
    config=None,
) -> dict:
    """The whole ``GET /research/desk/playbook/evidence`` body -- a pure fold over every recorded
    playbook file (via ``PlaybookStore``'s own verified reader, zero re-implementation), split by
    whether each file's own ``playbook_input_signature`` matches the CURRENT default signature
    (``compute_playbook_input_signature``, imported verbatim -- the EXACT function
    ``compute_playbook`` itself resolves its own signature through). A pure function of the
    recorded file set: identical files in, byte-identical body out, with or without ``cache``
    (TC-2/TC-6) -- ``cache`` only changes how many files must be re-verified to produce it."""
    default_signature = compute_playbook_input_signature(bar_store, members, config_fingerprint)
    projections = _projections_by_signature(store, cache)
    default_projections = [
        p for p in projections if p["playbook_input_signature"] == default_signature
    ]
    other_projections = [
        p for p in projections if p["playbook_input_signature"] != default_signature
    ]
    contexts = (
        _contexts_for(store, default_projections, bar_store, config, context_cache)
        if config is not None
        else {}
    )
    return {
        "signature": default_signature,
        "cells": _fold_cells(default_projections),
        "invalidation_breached": _fold_invalidation_breached(default_projections),
        "other_signatures": _fold_other_signatures(other_projections),
        "basis": _signature_basis(default_projections),
        "parameters": playbook_parameters(),
        "band_context": fold_band_context(default_projections, contexts),
        "register": EVIDENCE_REGISTER,
    }


def inspect_signature(store: PlaybookStore, signature: str) -> dict:
    """``?signature=`` mode: the ``dates``/``created_span`` ONE named signature's own recorded
    files carry -- default or not -- WITHOUT pooling it into any cell (the module docstring's
    "inspect, never pool" rule). An unknown signature is an honest empty ``dates: []``,
    ``created_span: null``, never a 404. Reads every file through ``PlaybookStore.get`` directly
    (never the evidence cache -- an inspect call is a rare, non-hot path; caching it would only add
    a second cache-invalidation surface for no measured benefit)."""
    dates: set[str] = set()
    recorded_ats: list[str] = []
    if store.root.exists():
        for path in sorted(store.root.glob("*.json")):
            record = store.get(path.stem)
            if record is None or record["playbook_input_signature"] != signature:
                continue
            dates.add(record["session_date"])
            recorded_ats.append(record["recorded_at"])
    created_span = {"from": min(recorded_ats), "to": max(recorded_ats)} if recorded_ats else None
    return {"signature": signature, "dates": sorted(dates), "created_span": created_span}
