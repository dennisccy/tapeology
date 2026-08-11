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
applied. The ONLY genuinely new math here is the quartile fold (``_quartile_stats``) --
``_collect_measures``/``_avg_cell`` (the rail's own pooling helpers) produce ``n``/``mean_pct``/
``median_pct``/``n_truncated`` but carry no p25/p75 at all; J-08 needs its own evidence-only fold
for those two, which is new EVIDENCE math, not a second implementation of anything the rail
already had.

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

__all__ = [
    "EVIDENCE_REGISTER",
    "EVIDENCE_TABLE",
    "PlaybookEvidenceCache",
    "fold_evidence",
    "inspect_signature",
]

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
    "counted, never silently dropped. A signature other than the current one is listed by its own "
    "dates and created span, never folded into these cells. No fills and no costs are modeled "
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
        "playbook_input_signature": record["playbook_input_signature"],
        "session_date": record["session_date"],
        "recorded_at": record["recorded_at"],
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
        if cached is not None:
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


def _signal_cell(values: list[float], n_truncated: int) -> dict:
    median, p25, p75, mean = _quartile_stats(values)
    return {
        "n": len(values),
        "n_truncated": n_truncated,
        "median_pct": median,
        "p25_pct": p25,
        "p75_pct": p75,
        "mean_pct": mean,
    }


def _baseline_cell(values: list[float]) -> dict:
    median, p25, p75, mean = _quartile_stats(values)
    return {
        "n_baseline": len(values),
        "median_pct": median,
        "p25_pct": p25,
        "p75_pct": p75,
        "mean_pct": mean,
    }


def _fold_cells(default_projections: list[dict]) -> list[dict]:
    """The FULL declared cross product of ``PLAYBOOK_SETUPS`` x sides x
    ``PLAYBOOK_SIGNAL_MEASURES`` -- every cell served, never a sparse "whatever fired" set (see the
    module docstring). ``_collect_measures`` (the rail's own pooling helper, imported verbatim) does
    the ENTIRE truncation-exclusion/grouping-by-measure-key job; this function only pools the raw
    per-file event lists across every default-signature file first, so a signal recorded in one
    session-date's file and a signal recorded in another's pool into the SAME cell exactly as if
    they had been measured in one walk."""
    cells: list[dict] = []
    for setup_id in PLAYBOOK_SETUPS:
        for side in _SIDES:
            pool_key = f"{setup_id}:{side}"
            signal_events: list[dict] = []
            baseline_events: list[dict] = []
            for projection in default_projections:
                signal_events.extend(projection["signal_events"].get(pool_key, []))
                baseline_events.extend(projection["baseline_events"].get(pool_key, []))
            signal_pools = _collect_measures(signal_events)
            baseline_pools = _collect_measures(baseline_events)
            for measure in PLAYBOOK_SIGNAL_MEASURES:
                signal_values, n_truncated = signal_pools[measure]
                baseline_values, _baseline_truncated = baseline_pools[measure]
                signal_block = _signal_cell(signal_values, n_truncated)
                cells.append(
                    {
                        "setup_id": setup_id,
                        "side": side,
                        "measure": measure,
                        "signal": signal_block,
                        "baseline": _baseline_cell(baseline_values),
                        "below_min_n": signal_block["n"] < PLAYBOOK_MIN_N_DISCLOSURE,
                    }
                )
    return cells


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


def _fold_other_signatures(other_projections: list[dict]) -> list[dict]:
    """Every NON-default signature present, its own ``dates``/``created_span`` only -- listed,
    never pooled (the hard anti-goal: "the evidence pools one signature"). Signatures sorted for a
    deterministic served order; ``dates`` deduplicated and sorted (a signature can record at most
    ONE file per date -- ``PlaybookStore``'s own 2-pin key refuses a duplicate -- so dedup here is
    defensive, not load-bearing)."""
    by_signature: dict[str, list[dict]] = {}
    for projection in other_projections:
        by_signature.setdefault(projection["playbook_input_signature"], []).append(projection)
    result: list[dict] = []
    for signature in sorted(by_signature):
        entries = by_signature[signature]
        dates = sorted({entry["session_date"] for entry in entries})
        recorded_ats = sorted(entry["recorded_at"] for entry in entries)
        result.append(
            {
                "signature": signature,
                "dates": dates,
                "created_span": {"from": recorded_ats[0], "to": recorded_ats[-1]},
            }
        )
    return result


def fold_evidence(
    store: PlaybookStore,
    bar_store,
    members: list[str],
    config_fingerprint: str,
    *,
    cache: PlaybookEvidenceCache | None = None,
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
    return {
        "signature": default_signature,
        "cells": _fold_cells(default_projections),
        "invalidation_breached": _fold_invalidation_breached(default_projections),
        "other_signatures": _fold_other_signatures(other_projections),
        "parameters": playbook_parameters(),
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
