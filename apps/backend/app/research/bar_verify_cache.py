"""A derived, rebuildable SQLite metadata cache over the canonical JSON ``BarStore`` — the durable
sibling of ``bars.py``'s in-process, stat-keyed ``_VERIFIED_CACHE``.

THIS MODULE stores METADATA ONLY and OWNS NOTHING. The checksummed, append-only JSON ``BarStore``
(``research/bars.py``) stays the ONE source of truth for bar content; every hit reported here is
metadata that ``BarStore`` itself already checksum-verified in full at the moment it was written.
Nothing is re-derived, approximated, or fabricated — a row only ever remembers one already-proven
answer: "for this exact file content (keyed by path + size + mtime_ns), verification already
produced this metadata." Deleting the DB loses nothing: the next read misses, re-verifies the file
in full, and repopulates. This is ``dataset_index.py``'s contract verbatim, applied to the bar
store; see that module for the shared rationale, and ``bar_index.py`` — a DIFFERENT index, keyed on
the ``(symbol, timeframe, window, feed)`` BUSINESS key, which answers "has this fetch already been
recorded" rather than "has this file already been verified".

**Why it exists.** ``_VERIFIED_CACHE`` is a module global, so every fresh process starts cold, and
a cold ``BarStore`` read pays a full verify of the entire store: on the live desk store (5,104
files / 439 MB / 3.25M rows) that is ~15s, of which ~10s is not hashing at all but the two
``json.dumps(sort_keys=True)`` canonicalizations the two checksums hash. That tax was paid by the
first member of every screen after a backend restart, and would be paid again by EVERY worker
process of a parallel screen walk — which is what made it worth making durable rather than merely
per-process.

**What the durability costs.** A stat match now means "some earlier process verified this exact
(size, mtime_ns) and got this metadata", where before it meant "this process did". A file rewritten
with byte-identical size AND a restored mtime is therefore served from the remembered metadata
instead of being re-verified — the same trade the in-process cache already makes within a process,
now surviving restarts. Any ordinary corruption, truncation, or edit changes size or mtime, misses,
and re-verifies (and then fails loudly, since an integrity error is never cached at any layer).
This is a deliberate, operator-approved trade for the restart tax, not an oversight.

**Bulk reads.** Unlike ``dataset_index`` (18 files), a bar store holds thousands, so a per-file
``lookup`` would trade 5,104 disk verifies for 5,104 SQLite round-trips. ``lookup_all`` answers the
whole directory in ONE query, and ``insert_many`` repopulates in one transaction.

``meta_json`` is stored via plain ``json.dumps`` WITHOUT ``sort_keys`` — the ``dataset_index.py`` /
``edge_report_cache.py`` byte-identity precedent: a cache-served record must reproduce the EXACT key
order a fresh disk verify would produce (``BarStore._load``'s ``json.loads`` preserves the on-disk
key order), so every REST/MCP response stays byte-identical whether it came from a hit or a verify.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

# Mirrors ``bar_index.py``/``dataset_index.py``'s ``_BUSY_TIMEOUT_MS`` — the identical brief
# writer-contention tolerance. It matters more here: a parallel screen walk has several worker
# processes repopulating this cache at once.
_BUSY_TIMEOUT_MS = 5000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS bar_verify_cache (
    path         TEXT PRIMARY KEY,
    size         INTEGER NOT NULL,
    mtime_ns     INTEGER NOT NULL,
    meta_json    TEXT NOT NULL,
    created_utc  TEXT NOT NULL
)
"""


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


class BarVerifyCache:
    """The durable stat-keyed verified-metadata cache — constructed with an explicit, hermetic DB
    path (the ``BarIndex``/``DatasetIndex`` dependency-injection precedent). ``BarStore`` is the
    ONLY caller; the lookup key is exactly ``BarStore``'s own in-process cache key (``path``,
    ``st_size``, ``st_mtime_ns``), so ANY stat difference is an honest miss."""

    def __init__(self, db_path: str) -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # One connection, one transaction state, several threads: the desk top-up walk overlaps
        # pairs, and each one may read and repopulate this cache. Two threads entering
        # ``with self._conn`` at once interleave a BEGIN with a COMMIT and SQLite answers "bad
        # parameter or other API misuse", so every statement below runs under this lock (the
        # identical ``bar_index.py`` serialization, for the identical reason).
        self._lock = threading.Lock()
        self._apply_pragmas()
        with self._lock, self._conn:
            self._conn.execute(_SCHEMA)

    @property
    def db_path(self) -> str:
        """The resolved DB file path (introspection/tests only — never used to bypass
        ``lookup``/``insert``)."""
        return self._db_path

    def _apply_pragmas(self) -> None:
        # ``:memory:`` does not support WAL (the identical ``BarIndex``/``DatasetIndex`` guard).
        if self._db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")

    def lookup(self, path: str, size: int, mtime_ns: int) -> dict | None:
        """An exact ``(path, size, mtime_ns)`` match — ANY stat difference (a genuine content
        change, or simply no row yet) is an honest miss, never a stale or approximate hit."""
        with self._lock:
            row = self._conn.execute(
                "SELECT size, mtime_ns, meta_json FROM bar_verify_cache WHERE path=?", (path,)
            ).fetchone()
        if row is None or row["size"] != size or row["mtime_ns"] != mtime_ns:
            return None
        return json.loads(row["meta_json"])

    def lookup_all(self) -> dict[str, tuple[int, int, str]]:
        """Every remembered row as ``{path: (size, mtime_ns, meta_json)}`` — ONE query for a whole
        directory scan. The caller compares each entry's stat against the file it actually found and
        parses ``meta_json`` only for the rows it keeps, so a stale or superseded row costs nothing
        and is never trusted without that same exact stat comparison ``lookup`` makes."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT path, size, mtime_ns, meta_json FROM bar_verify_cache"
            ).fetchall()
        return {row["path"]: (row["size"], row["mtime_ns"], row["meta_json"]) for row in rows}

    def insert(self, path: str, size: int, mtime_ns: int, meta: dict) -> None:
        """Additively remember ONE already-verified series' metadata. Idempotent
        (``INSERT OR REPLACE``) — re-inserting under the same path overwrites with the fresh
        ``(size, mtime_ns, meta)`` triple, the self-heal path for a legitimately changed file."""
        self.insert_many([(path, size, mtime_ns, meta)])

    def insert_many(self, rows: list[tuple[str, int, int, dict]]) -> None:
        """The bulk form of ``insert`` — one transaction for a whole cold scan's worth of freshly
        verified files, so repopulating an empty cache costs one commit rather than thousands."""
        if not rows:
            return
        stamp = _iso_utc_now()
        with self._lock, self._conn:
            self._conn.executemany(
                "INSERT OR REPLACE INTO bar_verify_cache "
                "(path, size, mtime_ns, meta_json, created_utc) VALUES (?,?,?,?,?)",
                [(path, size, mtime_ns, json.dumps(meta), stamp) for path, size, mtime_ns, meta in rows],
            )
