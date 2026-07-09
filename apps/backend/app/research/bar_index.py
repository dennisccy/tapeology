"""A derived, rebuildable SQLite index over the canonical JSON ``BarStore`` (era-5 capability 3,
J-03) — the Data Contract's "Store-first lookup" row's owner.

THIS MODULE stores METADATA ONLY and OWNS NOTHING. The checksummed, append-only JSON ``BarStore``
(``research/bars.py``) stays the ONE source of truth for bar data; every store-first hit this
index reports is resolved back through ``BarStore.get`` (which recomputes both checksums on every
load) before it is ever served — the index itself never serves a candle. Losing or deleting this
DB file loses nothing and fabricates nothing: ``reindex()`` rebuilds it, from scratch, entirely
from ``BarStore.list()``'s HEALTHY records (a corrupt file reported in that call's ``errors`` is
not legitimately indexable data and is silently excluded — never fabricated as a lookup).

Mirrors the stdlib-``sqlite3`` discipline of ``research/store.py`` (WAL journal mode +
``busy_timeout``, a hermetic dependency-injected DB path) WITHOUT that module's
writer-thread-queue machinery: that queue exists there to keep disk writes off a live
event-processing/WS hot path for high-frequency verdict writes. This index is a low-frequency
metadata cache (one write per explicit bar-series record), so a direct synchronous connection is
the right-sized implementation.

The lookup key is the exact tuple ``(symbol, timeframe, window_start_utc, window_end_utc)`` —
matched on the RAW ISO window strings exactly as ``BarStore.record`` stores them (verbatim
``body.start`` / ``body.end``, never parsed epochs), so two epoch-equal-but-textually-different
window strings never collide.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .bars import BarStore

# Mirrors ``Config.journal_busy_timeout_ms``'s default (config.py:402) — the identical brief
# writer-contention tolerance a low-frequency cache needs — without requiring a ``Config``
# dependency here (this module is intentionally hermetic/DI'd on a bare path only, the
# ``BarStore`` precedent, so ``config.py`` stays untouched by this iteration).
_BUSY_TIMEOUT_MS = 5000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS bar_index (
    symbol              TEXT NOT NULL,
    timeframe           TEXT NOT NULL,
    window_start_utc    TEXT NOT NULL,
    window_end_utc      TEXT NOT NULL,
    series_id           TEXT NOT NULL,
    checksum            TEXT NOT NULL,
    bar_count           INTEGER NOT NULL,
    PRIMARY KEY (symbol, timeframe, window_start_utc, window_end_utc)
)
"""


@dataclass(frozen=True)
class BarIndexHit:
    """One indexed lookup result — metadata ONLY, never the candles themselves. A hit is always
    resolved back through ``BarStore.get`` for the checksum-verified series before being served;
    this dataclass exists so a caller never mistakes the index's own row for served data."""

    series_id: str
    checksum: str
    bar_count: int


class BarIndex:
    """The derived SQLite index — constructed with an explicit, hermetic DB path (the
    ``BarStore``/``JournalStore`` dependency-injection precedent)."""

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
        never used to bypass the lookup/insert/list/reindex API)."""
        return self._db_path

    def _apply_pragmas(self) -> None:
        # ``:memory:`` does not support WAL (mirrors ``JournalStore``'s identical guard).
        if self._db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")

    # --- lookup / insert (the store-first coordinator's two calls) ------------------------------

    def lookup(
        self, symbol: str, timeframe: str, window_start_utc: str, window_end_utc: str
    ) -> BarIndexHit | None:
        """The exact-key lookup the store-first coordinator consults BEFORE touching the adapter.
        Matches the RAW ISO window strings verbatim — no epoch parsing here, so the caller must
        normalize ``symbol`` the SAME way it will be stored (the route does this)."""
        row = self._conn.execute(
            "SELECT series_id, checksum, bar_count FROM bar_index "
            "WHERE symbol=? AND timeframe=? AND window_start_utc=? AND window_end_utc=?",
            (symbol, timeframe, window_start_utc, window_end_utc),
        ).fetchone()
        if row is None:
            return None
        return BarIndexHit(row["series_id"], row["checksum"], row["bar_count"])

    def insert(self, meta: dict) -> None:
        """Additively index ONE bar series, using the fields of the ``meta`` dict
        ``BarStore.record`` returns — never re-derived from the request body (the values that
        actually got written are the only honest key). Idempotent (``INSERT OR REPLACE``): a
        second insert under the identical key overwrites with fresh values — the self-heal path
        when a stale entry pointed at a since-deleted/corrupted series and a real re-fetch ran."""
        with self._conn:
            self._conn.execute(
                "INSERT OR REPLACE INTO bar_index "
                "(symbol, timeframe, window_start_utc, window_end_utc, series_id, checksum, bar_count) "
                "VALUES (?,?,?,?,?,?,?)",
                self._params_from_meta(meta),
            )

    # --- list (the GET filter) -------------------------------------------------------------------

    def list(self, symbol: str | None = None, timeframe: str | None = None) -> list[BarIndexHit]:
        """Every indexed entry matching the given (optional, independently combinable) filters.
        Row order is NOT meaningful here — the route re-sorts after resolving each hit through
        ``BarStore.get`` (``BarStore.list()``'s own ``created_utc`` ordering)."""
        query = "SELECT series_id, checksum, bar_count FROM bar_index"
        clauses: list[str] = []
        params: list[str] = []
        if symbol is not None:
            clauses.append("symbol=?")
            params.append(symbol)
        if timeframe is not None:
            clauses.append("timeframe=?")
            params.append(timeframe)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        rows = self._conn.execute(query, params).fetchall()
        return [BarIndexHit(row["series_id"], row["checksum"], row["bar_count"]) for row in rows]

    # --- reindex (rebuild from the canonical store) -----------------------------------------------

    def reindex(self, store: BarStore) -> None:
        """Drop + repopulate the ENTIRE index from ``store.list()``'s HEALTHY records only —
        anything reported in that call's ``errors`` (a corrupt file) is not legitimately indexable
        data and is silently excluded (never fabricated as a lookup). Deleting this DB file and
        constructing a fresh ``BarIndex`` at the same path, then calling ``reindex()``, reproduces
        identical lookups — this index holds metadata only and owns nothing; its loss loses and
        fabricates nothing."""
        records, _errors = store.list()
        with self._conn:
            self._conn.execute("DELETE FROM bar_index")
            for meta in records:
                self._conn.execute(
                    "INSERT INTO bar_index "
                    "(symbol, timeframe, window_start_utc, window_end_utc, series_id, checksum, bar_count) "
                    "VALUES (?,?,?,?,?,?,?)",
                    self._params_from_meta(meta),
                )

    @staticmethod
    def _params_from_meta(meta: dict) -> tuple:
        return (
            meta["symbol"],
            meta["timeframe"],
            meta["window_start_utc"],
            meta["window_end_utc"],
            meta["id"],
            meta["checksum"],
            meta["bar_count"],
        )
