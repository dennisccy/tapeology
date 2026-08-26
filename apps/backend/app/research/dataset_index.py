"""A derived, rebuildable SQLite metadata index over the canonical JSON ``DatasetStore``
(era-fast_wall J-02) — the durable sibling half of the interlude's "verified-content store
caches" capability.

THIS MODULE stores METADATA ONLY and OWNS NOTHING. The checksummed, append-only JSON
``DatasetStore`` (``research/datasets.py``) stays the ONE source of truth for dataset content;
every hit this index reports is metadata that was ALREADY fully checksum-verified by
``DatasetStore`` at the moment it was written here — this index never re-derives or fabricates a
value, it only remembers one already-proven answer: "for this exact file content (keyed by path +
size + mtime_ns), verification already produced this metadata." Losing or deleting this DB file
loses nothing and fabricates nothing: the very next ``DatasetStore.get``/``list`` call simply
misses, re-verifies the file in full, and repopulates this index — the identical "derived,
rebuildable, owns nothing" guarantee ``bar_index.py`` documents, applied to a stat-keyed
verification cache instead of a store-first business-key lookup.

Mirrors ``bar_index.py``'s stdlib-``sqlite3`` discipline exactly: WAL journal mode +
``busy_timeout``, a hermetic dependency-injected DB path, ONE long-lived connection (never a
fresh-connection-per-call shape like ``edge_report_cache.py`` — that module's concurrency test
fires many threads at ONE shared cache instance, a scenario this module does not need to survive,
since ``DatasetStore`` constructs its own private ``DatasetIndex`` lazily and is itself
constructed fresh per FastAPI dependency call).

``meta_json`` is stored via plain ``json.dumps`` WITHOUT ``sort_keys`` — the
``edge_report_cache.py`` ``_insert`` byte-identity precedent: a durable-index-served response must
reproduce the EXACT key order a fresh disk verify would produce (``DatasetStore._load``'s own
``json.loads`` preserves the on-disk file's key order), so REST/MCP responses stay byte-identical
whether served from a durable-index hit or a from-scratch verify.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path



import os  # noqa: E402 -- co-located with the resolver below, the module's only os use


def resolve_dataset_index_db_path(dataset_dir_resolved: str) -> str:
    """The ONE resolution of where this index lives: the ``TAPEOLOGY_DATASET_INDEX_DB`` env var if
    set, else a ``dataset_index.db`` SIBLING of the resolved dataset directory (the
    ``get_bar_index`` env-else-sibling shape).

    r14: previously inlined in ``routes.get_dataset_store``, which meant it was the ONLY caller
    that passed ``index_db_path`` at all -- every CLI and module-level ``DatasetStore(dir)``
    silently took the full-verify path and re-hashed the whole corpus on every ``list()``. Owned
    here (the module the index belongs to) so every caller lands on the SAME file rather than a
    second index, and deliberately not a ``Config`` field (``config_fingerprint`` untouched)."""
    override = os.environ.get("TAPEOLOGY_DATASET_INDEX_DB")
    if override:
        return override
    return str(Path(dataset_dir_resolved).parent / "dataset_index.db")


def indexed_dataset_store(dataset_dir_resolved: str, store_cls):
    """``store_cls(dataset_dir, index_db_path=<resolved>)`` -- the one-liner every CLI entry point
    uses instead of a bare construction. ``store_cls`` is injected rather than imported to keep
    this module free of any dependency on ``datasets.py`` (which imports THIS module)."""
    return store_cls(dataset_dir_resolved, index_db_path=resolve_dataset_index_db_path(dataset_dir_resolved))

# Mirrors ``bar_index.py``'s ``_BUSY_TIMEOUT_MS`` (5000ms) — the identical brief writer-contention
# tolerance a low-frequency metadata cache needs.
_BUSY_TIMEOUT_MS = 5000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS dataset_index (
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


class DatasetIndex:
    """The derived SQLite metadata index — constructed with an explicit, hermetic DB path (the
    ``BarIndex``/``EdgeReportCache`` dependency-injection precedent). ``DatasetStore`` is the
    ONLY caller; the lookup key is exactly ``DatasetStore``'s own in-process stat cache key
    (``path``, ``st_size``, ``st_mtime_ns``) — ANY stat difference is treated as a miss, so a
    tampered or re-written file is never served stale metadata from here either."""

    def __init__(self, db_path: str) -> None:
        self._db_path = str(db_path)
        if self._db_path != ":memory:":
            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._apply_pragmas()
        with self._conn:
            self._conn.execute(_SCHEMA)

    @property
    def db_path(self) -> str:
        """The resolved DB file path this index was constructed with (introspection/tests only —
        never used to bypass ``lookup``/``insert``)."""
        return self._db_path

    def _apply_pragmas(self) -> None:
        # ``:memory:`` does not support WAL (mirrors ``BarIndex``'s identical guard).
        if self._db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")

    def lookup(self, path: str, size: int, mtime_ns: int) -> dict | None:
        """An exact ``(path, size, mtime_ns)`` match — ANY stat difference (a genuine content
        change, or simply no row yet) is an honest miss, never a stale or approximate hit."""
        row = self._conn.execute(
            "SELECT size, mtime_ns, meta_json FROM dataset_index WHERE path=?", (path,)
        ).fetchone()
        if row is None or row["size"] != size or row["mtime_ns"] != mtime_ns:
            return None
        return json.loads(row["meta_json"])

    def insert(self, path: str, size: int, mtime_ns: int, meta: dict) -> None:
        """Additively index ONE already-verified dataset's metadata. Idempotent
        (``INSERT OR REPLACE``): re-inserting under the identical path overwrites with the fresh
        ``(size, mtime_ns, meta)`` triple — the self-heal path when a file's content legitimately
        changed (a new stat) or a stale row needs correcting."""
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO dataset_index "
                "(path, size, mtime_ns, meta_json, created_utc) VALUES (?,?,?,?,?)",
                (path, size, mtime_ns, json.dumps(meta), _iso_utc_now()),
            )
