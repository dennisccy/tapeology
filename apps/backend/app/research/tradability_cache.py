"""``TradabilityCache`` — a durable, rebuildable SQLite cache of ONE row per
(symbol x basis session x symbol store content x config content) ``compute_tradability`` result,
read and written ONLY by the ``GET /research/tradability`` route.

Why: the tradable map is the /structure page's DEFAULT view, recomputed from scratch on every
Load click. The computation itself is now ~1-2s (the vectorized ``levels.py``/``tradability.py``
paths), but an operator flipping between a handful of as-of dates re-pays it on every repeat —
and a backend restart (routine under ``--reload``) forgets everything. One durable row per
resolved basis makes every repeat of an already-computed date a ~10ms read that survives
restarts.

THIS MODULE stores a REBUILDABLE RESULT ONLY and OWNS NOTHING — the identical
``SetupsScanCache``/``EdgeReportCache``/``EdgeReportBacktestCache``/``bar_index.py`` discipline
(see those modules' own docstrings): ``tradability.compute_tradability`` stays the SOLE computer
of a map, a cache miss always recomputes byte-identically through that ONE function, and deleting
the persisted DB file loses nothing and fabricates nothing — the very next request simply
recomputes and republishes. The ROUTE is the only caller: ``compute_tradability`` itself stays a
pure function, so the backtest/setups/arm-memo paths (which have their own memo discipline) are
structurally unaffected.

**Key — four parts, sha256 of canonical JSON** (``scan_cache_key``'s explicit-literals shape —
each component independently controllable and testable, never derived internally from an opaque
``Config``/``BarStore`` object):

  * ``symbol`` — the normalized (upper-cased) symbol the route resolved.
  * ``basis_day`` — ``tradability.basis_day_key(as_of_epoch)``: ``compute_tradability``'s output
    depends on ``as_of`` ONLY through which prior session it resolves, and that resolution is
    constant across every ``as_of`` sharing one UTC calendar date (the ``basis_day_key`` contract,
    already pinned by ``tests/test_tradability.py``'s own basis-day tests and relied on by
    ``backtests.py``'s ``_StructureArmMemo``) — so two same-day requests share one row while each
    response still echoes its own requested ``as_of`` (the route re-wraps; the ``as_of`` echo is
    never stored here). Distinct UTC dates that happen to resolve the SAME basis (a Saturday and
    the following Monday both resolve Friday) keep distinct keys — an accepted missed-sharing,
    never a wrong answer.
  * ``store_signature`` — ``symbol_store_signature(...)``: the sorted ``(timeframe, id,
    checksum)`` triples of THIS SYMBOL's healthy recorded series only. ``compute_tradability``
    reads nothing but this symbol's own series (every read is ``merged_bars(symbol, ...)`` /
    ``list()`` filtered to the symbol), so another symbol's new recording rightly does NOT bust
    this symbol's rows, while any new/changed/deleted recording of THIS symbol does.
  * ``config_content_hash`` — ``edge_report_cache._config_content_hash`` reused verbatim (never
    re-derived; the ``setups.py`` precedent), which already folds in ``LEVELS_ALGORITHM_VERSION``
    — so an algorithm bump invalidates these rows together with every sibling cache.

**Values stored WITHOUT ``sort_keys``** — the ``EdgeReportCache._insert`` byte-identity
discipline: a cached map, once round-tripped through this cache, serves byte-identically to a
freshly computed one (json round-trips floats exactly and preserves key order).

**Error handling — never a crash, an accelerator's own failure never blocks serving.** Every
method independently guards ``sqlite3.Error``: ``lookup`` treats any failure as a full miss
(forcing a fresh compute through the canonical path); ``publish`` SWALLOWS any failure entirely —
a lost row merely costs one recompute on the next request.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .edge_report_cache import _canonical

__all__ = [
    "TradabilityCache",
    "resolve_tradability_cache_db_path",
    "symbol_store_signature",
    "tradability_cache_key",
]

# A DIFFERENT env var from every sibling durable cache's own -- the caches never collide, never
# share a path, never share a table.
_CACHE_DB_ENV = "TAPEOLOGY_TRADABILITY_CACHE_DB"

# Mirrors every sibling durable cache's identical brief writer-contention tolerance.
_BUSY_TIMEOUT_MS = 5000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tradability_cache (
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


def symbol_store_signature(records: list[dict], symbol: str) -> tuple:
    """A deterministic fingerprint of everything ``compute_tradability`` can possibly read from
    the store for ``symbol``: THAT SYMBOL's healthy series' ``(timeframe, id, checksum)``, sorted
    for order-independence — ``setups._store_signature`` narrowed to one symbol (the module
    docstring's key rationale). ``records`` is ``store.list()``'s already-HEALTHY half; a corrupt
    file is excluded there exactly as every compute path excludes it, so its mere
    presence/absence can never change a served map and rightly never busts a row."""
    return tuple(
        sorted(
            (record["timeframe"], record["id"], record["checksum"])
            for record in records
            if record["symbol"] == symbol
        )
    )


def tradability_cache_key(
    *, symbol: str, basis_day: str, store_signature: tuple, config_content_hash: str
) -> str:
    """The full key material for ONE tradable map (see module docstring) — sha256 of the
    canonical JSON of all four components, each an explicit literal (the ``scan_cache_key``
    shape) so mutating any one (holding the others fixed) always yields a different key — see
    ``tests/test_tradability_cache.py``'s key-busting matrix for the non-vacuous proof."""
    payload = {
        "symbol": symbol,
        "basis_day": basis_day,
        "store_signature": [list(item) for item in store_signature],
        "config_content_hash": config_content_hash,
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def resolve_tradability_cache_db_path(bar_store_root: str) -> str:
    """The cache DB path resolution policy — the ``resolve_scan_cache_db_path`` env-else-sibling
    shape for a DIFFERENT env var and filename: ``TAPEOLOGY_TRADABILITY_CACHE_DB`` if set, else
    ``tradability_cache.db`` co-located as a SIBLING of the caller's bar-store ROOT (e.g.
    ``.data/bars`` -> ``.data/tradability_cache.db``). Resolved from the INJECTED store's own
    root (``BarStore.root``) rather than global config so a test pointing its store at a
    ``tmp_path`` gets a hermetic cache for free — the exact property ``conftest.py`` documents
    for ``SetupsScanCache``."""
    override = os.environ.get(_CACHE_DB_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(bar_store_root), "tradability_cache.db")


class TradabilityCache:
    """One durable SQLite row per (symbol, basis session, store content, config content) — see
    the module docstring for the full "rebuildable, never a source of truth" contract and the
    error-handling discipline. Structurally ``SetupsScanCache`` for a different table/key."""

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
            # subsequent lookup()/publish() independently re-attempts and hits the SAME failure
            # mode, so this self-heals with no separate "usable" flag to maintain.
            pass

    @property
    def db_path(self) -> str:
        """The resolved DB file path this cache was constructed with (introspection/tests only)."""
        return self._db_path

    def _connect(self) -> sqlite3.Connection:
        """A FRESH, short-lived connection per call (the ``JournalStore._read_conn`` precedent —
        never one long-lived connection shared across requests/threads)."""
        conn = sqlite3.connect(
            self._db_path, check_same_thread=False, timeout=_BUSY_TIMEOUT_MS / 1000.0
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
        return conn

    def lookup(self, key: str) -> dict | None:
        """The durable row for ``key``, or ``None`` on a genuine miss — NEVER computes (no
        ``compute_fn`` parameter exists; a miss is mechanically incapable of running the map). A
        corrupted/unreadable DB is a full miss, never a crash (module docstring)."""
        try:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT result_json FROM tradability_cache WHERE cache_key=?", (key,)
                ).fetchone()
            finally:
                conn.close()
        except sqlite3.Error:
            return None
        return None if row is None else json.loads(row["result_json"])

    def publish(self, key: str, result: dict) -> None:
        """Durably persist ONE map — one atomic ``INSERT OR REPLACE`` transaction, stored WITHOUT
        ``sort_keys`` (module docstring). A publish failure of ANY kind is SWALLOWED, never
        propagated — the caller is still holding its own freshly-computed result."""
        try:
            conn = self._connect()
            try:
                with conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO tradability_cache "
                        "(cache_key, result_json, created_utc) VALUES (?,?,?)",
                        (key, json.dumps(result), _iso_utc_now()),
                    )
            finally:
                conn.close()
        except sqlite3.Error:
            pass
