"""``SetupsScanCache`` (era-fast_wall J-06) — a durable, rebuildable SQLite cache of ONE row per
(config content x bar-store content) full-panel touch-event scan ``setups.compute_setups`` performs,
kept BESIDE (never instead of) that module's own in-process hot slot (``_SCAN_CACHE``). Makes the
multi-minute scan survive a backend restart -- or simply a freshly-constructed but content-equal
``Config`` object -- instead of re-paying the full scan every time the hot slot happens to be cold.

THIS MODULE stores a REBUILDABLE RESULT ONLY and OWNS NOTHING — the identical ``EdgeReportCache``/
``EdgeReportBacktestCache``/``bar_index.py`` discipline (see those modules' own docstrings), applied
to a full-panel scan result instead of a report or a backtest pair: ``setups._run_full_panel_scan``
stays the SOLE computer of a scan's result; a cache miss always recomputes byte-identically through
that ONE function. Deleting the persisted DB file loses nothing and fabricates nothing — the very
next call simply re-runs the scan and republishes it.

**Durable-only — no in-process hot slot of its own.** ``setups.py`` already owns its own in-process
hot slot (``_SCAN_CACHE``) for repeated reads of the SAME key within one process's lifetime, so this
class stays exactly as large as its job needs to be (the ``EdgeReportBacktestCache`` "no abstraction
until it earns its keep" precedent, applied here since it is ``setups.py``'s hot slot -- not this
module -- that already covers the repeated-read-within-one-process case). Every read/write opens its
OWN short-lived connection (the ``JournalStore._read_conn`` precedent, mirrored by every sibling
durable cache in this codebase) — safe across a future multi-process caller too, since no long-lived
shared connection object is ever held.

**Key — two parts, sha256 of canonical JSON.** ``config_content_hash`` (the config's ENTIRE field
content, reused verbatim from ``edge_report_cache._config_content_hash`` by the caller -- never
re-derived a second time -- rather than ``config.config_fingerprint()`` alone, whose own documented
exclusion set drops exactly the ``setups_*``/``tradability_*``/``sr_*`` field families the scan
reads) and ``store_signature`` (the sorted per-series ``(symbol, timeframe, id, checksum)`` tuples
``setups._store_signature`` already computes). ``scan_cache_key`` accepts both as explicit literals
(never derived internally from an opaque ``Config``/``BarStore`` object) — the
``edge_report_backtest_cache.pair_cache_key`` precedent — so each component is independently
controllable and testable.

**Values stored WITHOUT ``sort_keys``** — the ``EdgeReportCache._insert`` byte-identity discipline: a
cached scan result, once round-tripped through this cache, must be usable identically to a freshly
computed one wherever a caller inspects its fields.

**Error handling — never a crash, an accelerator's own failure never blocks serving.** Every method
independently guards against ``sqlite3.Error`` (covering both connection/pragma failures and query
failures against a corrupted/unreadable DB file): ``lookup`` treats any such failure as a full miss
(``None``, forcing a fresh scan through the caller's own canonical path); ``publish`` SWALLOWS any
such failure entirely (never raises) — the sweep/scan's own correctness never depends on the durable
write succeeding; a lost row merely costs one recompute on the next call.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .edge_report_cache import _canonical

__all__ = ["SetupsScanCache", "resolve_scan_cache_db_path", "scan_cache_key"]

# A DIFFERENT env var from EdgeReportCache's/EdgeReportBacktestCache's own -- the three durable
# caches never collide, never share a path, never share a table.
_CACHE_DB_ENV = "TAPEOLOGY_SETUPS_CACHE_DB"

# Mirrors every sibling durable cache's identical brief writer-contention tolerance.
_BUSY_TIMEOUT_MS = 5000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS setups_scan_cache (
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


def scan_cache_key(*, config_content_hash: str, store_signature: tuple) -> str:
    """The full key material for ONE full-panel scan (see module docstring) — sha256 of the
    canonical JSON of both components. A pure function of its two named inputs alone: each is
    independently controllable, so mutating either (holding the other fixed) always yields a
    different key — see ``tests/test_setups_scan_cache.py``'s key-busting matrix for the
    non-vacuous proof."""
    payload = {
        "config_content_hash": config_content_hash,
        "store_signature": [list(item) for item in store_signature],
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def resolve_scan_cache_db_path(bar_dir_resolved: str) -> str:
    """The cache DB path resolution policy — mirrors ``edge_report_cache.resolve_cache_db_path`` /
    ``edge_report_backtest_cache.resolve_backtest_cache_db_path`` exactly (env-else-sibling), for a
    DIFFERENT env var and a DIFFERENT sibling filename: the ``TAPEOLOGY_SETUPS_CACHE_DB`` env var if
    set, else ``setups_scan_cache.db`` co-located as a SIBLING of the caller's own already-resolved
    bar directory (e.g. ``.data/bars`` -> ``.data/setups_scan_cache.db`` — the ``get_bar_index``
    env-else-sibling-of-``bar_dir_resolved()`` shape)."""
    override = os.environ.get(_CACHE_DB_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(bar_dir_resolved), "setups_scan_cache.db")


class SetupsScanCache:
    """One durable SQLite row per full-panel scan key — beside ``setups.py``'s own in-process hot
    slot, never a modification of it. See the module docstring for the full "rebuildable, never a
    source of truth" contract and the error-handling discipline."""

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
        long-lived connection shared across callers)."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False, timeout=_BUSY_TIMEOUT_MS / 1000.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
        return conn

    def lookup(self, key: str) -> dict | None:
        """The durable row for ``key``, or ``None`` on a genuine miss — NEVER computes (there is no
        ``compute_fn`` parameter; a miss is mechanically incapable of running a scan). A
        corrupted/unreadable DB is treated as a full miss, never a crash (module docstring)."""
        try:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT result_json FROM setups_scan_cache WHERE cache_key=?", (key,)
                ).fetchone()
            finally:
                conn.close()
        except sqlite3.Error:
            return None
        return None if row is None else json.loads(row["result_json"])

    def publish(self, key: str, result: dict) -> None:
        """Durably persist ONE scan's result — one atomic ``INSERT OR REPLACE`` transaction. Stored
        WITHOUT ``sort_keys`` (see module docstring). A publish failure of ANY kind is SWALLOWED
        here, never propagated (module docstring) — never blocks the caller that is still holding
        its own freshly-scanned result."""
        try:
            conn = self._connect()
            try:
                with conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO setups_scan_cache "
                        "(cache_key, result_json, created_utc) VALUES (?,?,?)",
                        (key, json.dumps(result), _iso_utc_now()),
                    )
            finally:
                conn.close()
        except sqlite3.Error:
            pass
