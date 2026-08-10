"""A derived, rebuildable SQLite metadata cache over the recorded screen and forward snapshot
files -- ``bar_verify_cache.py``'s contract, applied to the two desk stores.

THIS MODULE stores METADATA ONLY and OWNS NOTHING. The checksummed, append-only JSON files
(``desk_screen.py`` / ``desk_forward.py``) stay the ONE source of truth. A row only ever remembers
one already-proven answer: "for this exact file content (keyed by path + size + mtime_ns), the
store's own full verification already produced this metadata." Deleting the DB loses nothing: the
next read misses, re-verifies every file in full, and repopulates.

**Why it exists.** A snapshot store's no-params ``GET`` serves a meta-only projection of every
recorded snapshot, and building it re-read, re-parsed, re-canonicalized and re-hashed the whole
store on EVERY request -- 1.5s for 939 screens (85 MB), 2.9s for 960 forward records (165 MB), paid
again on every page load. As with the bar store, most of that is not hashing but the
``json.dumps(sort_keys=True)`` canonicalization the checksum hashes.

**Narrower than the bar cache, deliberately.** Only the meta-only PROJECTION is remembered -- never
``rows``/``skipped``/``summary``. Every response that serves a snapshot's actual content
(``?id=``, ``?date=``, ``latest``, the comparison) reads that file from disk and verifies it in
full, every time. So the trade the bar cache documents (a file rewritten with byte-identical size
AND a restored mtime is served from remembered metadata rather than re-verified) is confined here
to counts and pins in a LIST -- it can never put unverified snapshot CONTENT in front of anyone.

**An integrity error is never cached, at any layer.** A file that fails verification is not
inserted, so it is re-verified and re-surfaced in ``integrity_errors`` on every single call, with
the same text and in the same position as an uncached walk.

**Two stores, two DB files, one class.** Each store directory is independently relocatable
(``TAPEOLOGY_DESK_SCREEN_DIR`` / ``TAPEOLOGY_DESK_FORWARD_DIR``), so each gets its own sibling DB --
the ``bars`` -> ``bar_verify_cache.db`` precedent, twice. ``table`` is fixed per instance by the
store that constructs it; nothing here decides which store it is caching.

``meta_json`` is stored via plain ``json.dumps`` WITHOUT ``sort_keys`` -- the ``dataset_index.py`` /
``bar_verify_cache.py`` byte-identity precedent: a cache-served row must reproduce the EXACT key
order a fresh disk verify would produce, so every REST/MCP response stays byte-identical whether it
came from a hit or a verify.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

# Mirrors ``bar_verify_cache.py``/``bar_index.py``'s own value, for the identical reason.
_BUSY_TIMEOUT_MS = 5000

# The two tables this class can own. A fixed set rather than a free-form name: the table is part of
# the schema, not a caller-supplied string, so nothing can interpolate an arbitrary identifier here.
SCREEN_TABLE = "screen_meta_cache"
FORWARD_TABLE = "forward_meta_cache"
_TABLES = (SCREEN_TABLE, FORWARD_TABLE)


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


class DeskMetaCache:
    """The durable stat-keyed meta-projection cache for ONE desk snapshot store -- constructed with
    an explicit, hermetic DB path (the ``BarVerifyCache``/``BarIndex`` dependency-injection
    precedent). The lookup key is exactly the store's own ``(path, st_size, st_mtime_ns)``, so ANY
    stat difference is an honest miss."""

    def __init__(self, db_path: str, table: str = SCREEN_TABLE) -> None:
        if table not in _TABLES:
            raise ValueError(f"unknown desk meta cache table {table!r} -- expected one of {_TABLES}")
        self._table = table
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # One connection, one transaction state, several threads: FastAPI serves these sync routes
        # from a threadpool, so two requests can repopulate this cache at once. Two threads entering
        # ``with self._conn`` interleave a BEGIN with a COMMIT and SQLite answers "bad parameter or
        # other API misuse", so every statement below runs under this lock (the identical
        # ``bar_index.py``/``bar_verify_cache.py`` serialization, for the identical reason).
        self._lock = threading.Lock()
        self._apply_pragmas()
        with self._lock, self._conn:
            self._conn.execute(
                f"CREATE TABLE IF NOT EXISTS {self._table} ("
                "    path         TEXT PRIMARY KEY,"
                "    size         INTEGER NOT NULL,"
                "    mtime_ns     INTEGER NOT NULL,"
                "    meta_json    TEXT NOT NULL,"
                "    created_utc  TEXT NOT NULL)"
            )

    @property
    def db_path(self) -> str:
        """The resolved DB file path (introspection/tests only -- never used to bypass
        ``lookup``/``insert``)."""
        return self._db_path

    @property
    def table(self) -> str:
        return self._table

    def _apply_pragmas(self) -> None:
        # ``:memory:`` does not support WAL (the identical ``BarVerifyCache`` guard).
        if self._db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")

    def lookup(self, path: str, size: int, mtime_ns: int) -> dict | None:
        """An exact ``(path, size, mtime_ns)`` match -- ANY stat difference (a genuine content
        change, or simply no row yet) is an honest miss, never a stale or approximate hit."""
        with self._lock:
            row = self._conn.execute(
                f"SELECT size, mtime_ns, meta_json FROM {self._table} WHERE path=?", (path,)
            ).fetchone()
        if row is None or row["size"] != size or row["mtime_ns"] != mtime_ns:
            return None
        return json.loads(row["meta_json"])

    def lookup_all(self) -> dict[str, tuple[int, int, str]]:
        """Every remembered row as ``{path: (size, mtime_ns, meta_json)}`` -- ONE query for a whole
        directory scan. The caller compares each entry's stat against the file it actually found and
        parses ``meta_json`` only for the rows it keeps, so a stale or superseded row costs nothing
        and is never trusted without that same exact stat comparison ``lookup`` makes."""
        with self._lock:
            rows = self._conn.execute(
                f"SELECT path, size, mtime_ns, meta_json FROM {self._table}"
            ).fetchall()
        return {row["path"]: (row["size"], row["mtime_ns"], row["meta_json"]) for row in rows}

    def insert(self, path: str, size: int, mtime_ns: int, meta: dict) -> None:
        """Additively remember ONE already-verified snapshot's meta projection. Idempotent
        (``INSERT OR REPLACE``) -- re-inserting under the same path overwrites with the fresh
        ``(size, mtime_ns, meta)`` triple, the self-heal path for a legitimately changed file."""
        self.insert_many([(path, size, mtime_ns, meta)])

    def insert_many(self, rows: list[tuple[str, int, int, dict]]) -> None:
        """The bulk form of ``insert`` -- one transaction for a whole cold scan's worth of freshly
        verified files, so repopulating an empty cache costs one commit rather than thousands."""
        if not rows:
            return
        stamp = _iso_utc_now()
        with self._lock, self._conn:
            self._conn.executemany(
                f"INSERT OR REPLACE INTO {self._table} "
                "(path, size, mtime_ns, meta_json, created_utc) VALUES (?,?,?,?,?)",
                [
                    (path, size, mtime_ns, json.dumps(meta), stamp)
                    for path, size, mtime_ns, meta in rows
                ],
            )

    def prune_missing(self, present_paths: set[str]) -> int:
        """Forget rows for files no longer on disk, returning how many were dropped. Purely
        housekeeping -- a stale row is already unreachable (its path is never looked up again), so
        this only stops a cleanup's worth of removed snapshots from being remembered forever."""
        with self._lock:
            known = {
                row["path"] for row in self._conn.execute(f"SELECT path FROM {self._table}")
            }
        gone = known - present_paths
        if not gone:
            return 0
        with self._lock, self._conn:
            self._conn.executemany(
                f"DELETE FROM {self._table} WHERE path=?", [(path,) for path in gone]
            )
        return len(gone)
