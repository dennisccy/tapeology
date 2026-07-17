"""``EdgeReportBacktestCache`` (era-fast_wall J-05) — a durable, rebuildable SQLite cache of ONE
row per (dataset x strategy) backtest PAIR: the per-pair ``result`` block ``edge_report.py``'s
``_split_cells`` loop pools into cells, cached BESIDE the whole-REPORT ``EdgeReportCache``
(``edge_report_cache.py``, untouched) rather than instead of it. Makes the 3-way sweep genuinely
RESUMABLE (a killed-and-retriggered run skips every already-published pair) and safely
PARALLELIZABLE (many worker PROCESSES publish concurrently; each publish is one atomic SQLite
transaction, safe under WAL + busy_timeout).

THIS MODULE stores a REBUILDABLE RESULT ONLY and OWNS NOTHING — the identical ``EdgeReportCache``/
``bar_index.py`` discipline (see ``edge_report_cache.py``'s own module docstring), applied to a
per-PAIR row instead of a whole-report row: ``edge_report.py`` stays the SOLE computer of a pair's
``result`` (via ``_run_backtest``, unchanged); a cache miss always recomputes byte-identically
through that ONE function. Deleting the persisted DB file loses nothing and fabricates nothing —
the very next sweep simply re-runs every pair's backtest and republishes it.

**Durable-only — no in-process hot slot.** Unlike ``EdgeReportCache`` (one key per WHOLE report,
so a hot in-process slot serves REPEATED reads of the SAME report cheaply), a single sweep touches
MANY DISTINCT pair keys in sequence and never the SAME key twice within one run — an instance-
scoped single-slot fast path would never actually serve a hit inside one sweep, so this class stays
exactly as large as its job needs to be (the developer-agent "no abstraction until it earns its
keep" discipline). Every read/write opens its OWN short-lived connection (the
``JournalStore._read_conn`` precedent, mirrored by ``EdgeReportCache`` too) — safe across MANY
worker PROCESSES (not merely threads) publishing concurrently, since each process holds no
long-lived shared connection object to begin with.

**Key — eight parts, sha256 of canonical JSON (goal.md's own named shape).** ``dataset_id``,
``dataset_checksum``, ``strategy_id``, ``profile``, ``config_fingerprint``, ``config_content_hash``,
``strategy_registry``, ``bar_store_signature``. The bar-store term is REQUIRED (not merely one more
component among equals): the structure strategies (``structure_tape``/``structure_tape_map``) read
bar content per event, so a bar-series change must bust every pair that reads bars, and the
EXISTING persisted backtest journal rows are NOT a safe resume source precisely because their own
``config_fingerprint`` excludes the ``sr_*``/``tradability_*``/``setups_*`` families and records no
bar content at all (goal.md's own words) — never consulted here. ``pair_cache_key`` accepts every
component as an explicit literal (never derived internally from an opaque ``Config``/``BarStore``
object) so each of the eight can be independently varied and tested — the REAL caller
(``edge_report._build_caching_run_pair``) derives ``config_fingerprint``/``config_content_hash``/
``strategy_registry``/``bar_store_signature`` from the SAME ``Config``/``BarStore`` ONCE per sweep
(never once per pair) and closes over them; this function itself stays a pure function of its eight
named inputs alone. Reuses ``edge_report_cache.py``'s ``_canonical``/``_config_content_hash``
VERBATIM (never re-derived a second time) — the identical byte-stable canonical-JSON hashing idiom.

**Values stored WITHOUT ``sort_keys``** — the ``EdgeReportCache._insert`` byte-identity discipline
(see that method's own docstring for the full "why"), applied to a per-pair row: a pair's cached
``result`` block, once round-tripped through this cache, must be usable identically to a freshly
computed one wherever a caller inspects its fields.

**Error handling — never a crash, an accelerator's own failure never blocks the sweep.** Every
method independently guards against ``sqlite3.Error`` (covering both connection/pragma failures
and query failures against a corrupted/unreadable DB file): ``lookup`` treats any such failure as a
full miss (``None``, forcing a fresh compute through the caller's own canonical path); ``publish``
SWALLOWS any such failure entirely (never raises) — the ``setups_scan_cache.py`` "publish failures
swallowed, an accelerator never blocks serving" discipline (goal.md's own wording for a sibling
cache), applied uniformly here regardless of caller (both the sequential ``run_pair`` closure and
every parallel worker process call this SAME method): the sweep's own correctness never depends on
every pair's cache write succeeding — a lost row merely costs one recompute on the next sweep.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .edge_report_cache import _canonical, _config_content_hash

__all__ = ["EdgeReportBacktestCache", "pair_cache_key", "resolve_backtest_cache_db_path"]

# A DIFFERENT env var from EdgeReportCache's own TAPEOLOGY_EDGE_REPORT_CACHE_DB — the two durable
# caches never collide, never share a path, never share a table.
_CACHE_DB_ENV = "TAPEOLOGY_EDGE_SWEEP_CACHE_DB"

# Mirrors edge_report_cache.py's identical brief writer-contention tolerance.
_BUSY_TIMEOUT_MS = 5000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS edge_report_backtest_cache (
    cache_key    TEXT PRIMARY KEY,
    result_json  TEXT NOT NULL,
    created_utc  TEXT NOT NULL
)
"""


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def pair_cache_key(
    *,
    dataset_id: str,
    dataset_checksum: str,
    strategy_id: str,
    profile: str,
    config_fingerprint: str,
    config_content_hash: str,
    strategy_registry: list[dict],
    bar_store_signature: tuple,
) -> str:
    """The full eight-part key material for ONE (dataset x strategy) backtest pair — sha256 of the
    canonical JSON of every component (see module docstring). A pure function of its eight named
    inputs alone: every component is independently controllable, so mutating exactly one (holding
    the other seven fixed) always yields a different key — see
    ``tests/test_edge_report_backtest_cache.py``'s key-busting matrix for the non-vacuous proof."""
    payload = {
        "dataset_id": dataset_id,
        "dataset_checksum": dataset_checksum,
        "strategy_id": strategy_id,
        "profile": profile,
        "config_fingerprint": config_fingerprint,
        "config_content_hash": config_content_hash,
        "strategy_registry": strategy_registry,
        "bar_store_signature": list(bar_store_signature),
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def resolve_backtest_cache_db_path(dataset_dir_resolved: str) -> str:
    """The sub-cache DB path resolution policy — mirrors ``edge_report_cache.resolve_cache_db_path``
    exactly (env-else-sibling-of-the-dataset-dir), for a DIFFERENT env var and a DIFFERENT sibling
    filename, so the two durable caches never collide: the ``TAPEOLOGY_EDGE_SWEEP_CACHE_DB`` env
    var if set, else ``edge_report_backtests.db`` co-located beside the caller's own resolved
    dataset directory (the SAME ``.data/`` directory ``edge_report_cache.db`` already lives in)."""
    override = os.environ.get(_CACHE_DB_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(dataset_dir_resolved), "edge_report_backtests.db")


class EdgeReportBacktestCache:
    """One durable SQLite row per (dataset x strategy) pair's backtest ``result`` block — beside
    ``EdgeReportCache``, the SAME durable discipline (WAL + busy_timeout, a hermetic dependency-
    injected DB path), never a modification of that existing whole-report cache. See the module
    docstring for the full "rebuildable, never a source of truth" contract and the error-handling
    discipline."""

    def __init__(self, db_path: str) -> None:
        self._db_path = str(db_path)
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        try:
            conn = self._connect()
            try:
                with conn:
                    conn.execute(_SCHEMA)
            finally:
                conn.close()
        except sqlite3.Error:
            # A corrupted/unreadable file at this path -- never a crash (module docstring). Every
            # subsequent lookup()/publish() independently re-attempts _connect()+query and hits the
            # SAME failure mode, so this self-heals with no separate "usable" flag to maintain.
            pass

    @property
    def db_path(self) -> str:
        """The resolved DB file path this cache was constructed with (introspection/tests only)."""
        return self._db_path

    def _connect(self) -> sqlite3.Connection:
        """A FRESH, short-lived connection (the ``JournalStore._read_conn`` precedent — never one
        long-lived connection shared across threads OR processes)."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=_BUSY_TIMEOUT_MS / 1000.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
        return conn

    def lookup(self, key: str) -> dict | None:
        """The durable row for ``key``, or ``None`` on a genuine miss — NEVER computes (there is no
        ``compute_fn`` parameter; a miss is mechanically incapable of running a backtest). A
        corrupted/unreadable DB is treated as a full miss, never a crash (module docstring)."""
        try:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT result_json FROM edge_report_backtest_cache WHERE cache_key=?", (key,)
                ).fetchone()
            finally:
                conn.close()
        except sqlite3.Error:
            return None
        return None if row is None else json.loads(row["result_json"])

    def publish(self, key: str, result: dict) -> None:
        """Durably persist ONE pair's ``result`` block — one atomic ``INSERT OR REPLACE``
        transaction (safe across many worker PROCESSES publishing concurrently; WAL + busy_timeout
        tolerate brief writer contention). Stored WITHOUT ``sort_keys`` (see module docstring). A
        publish failure of ANY kind is SWALLOWED here, never propagated (module docstring) — never
        blocks the sweep that is still holding this pair's own already-computed ``result``."""
        try:
            conn = self._connect()
            try:
                with conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO edge_report_backtest_cache "
                        "(cache_key, result_json, created_utc) VALUES (?,?,?)",
                        (key, json.dumps(result), _iso_utc_now()),
                    )
            finally:
                conn.close()
        except sqlite3.Error:
            pass
