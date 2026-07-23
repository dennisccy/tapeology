"""A rebuildable, checksum-keyed result cache around ``run_strategy_comparison_report`` (era-5B
J-08) — makes the era's central "what actually profits" deliverable observable within an
interactive time budget on a warm cache, instead of the documented ~10+h / ~9.1M-tick sweep the
``BacktestJobManager`` runs inside ``edge_report.py``'s ``_compute_strategy_comparison_report``
(the sweep this module accelerates; NOT ``compute_setups``, which already owns its own
process-local ``_SCAN_CACHE`` in ``setups.py`` — untouched, unrelated, a different cost center).

THIS MODULE stores a REBUILDABLE RESULT ONLY and OWNS NOTHING — mirrors ``bar_index.py``'s
"metadata/derived-cache only, the canonical computation stays elsewhere" discipline, adapted from
an indexed lookup to a computed report: ``edge_report.py`` stays the SOLE computer; a cache miss
(first-ever call, or any input change) always recomputes byte-identically through the caller's
OWN ``compute_fn`` — this module never re-derives a cell, a measurement, a null baseline, or any
other research value itself. Deleting the persisted DB file loses nothing and fabricates nothing:
the very next call simply recomputes and republishes (the ``bar_index.py`` "loss loses and
fabricates nothing" guarantee, applied to a report instead of an index row).

Two layers, mirroring the plan's two named precedents:

  * **Durable (SQLite, mirrors ``bar_index.py``).** One row per cache key, WAL journal mode +
    ``busy_timeout``, a hermetic dependency-injected path — survives a backend restart. Every
    read and write opens its OWN short-lived connection (the ``JournalStore._read_conn()``
    precedent — see ``store.py`` — NOT ``bar_index.py``'s one-long-lived-connection-with-
    ``check_same_thread=False`` shape): this module's own concurrency test fires many THREADS at
    one shared ``EdgeReportCache`` instance, and sharing a single ``sqlite3.Connection`` object
    across genuinely concurrent callers is unproven and unnecessary here, so it is sidestepped
    entirely rather than relied upon. A write is one atomic transaction (``INSERT OR REPLACE``
    inside ``with conn:``) — a reader can only ever observe the fully-committed prior row or the
    fully-committed new one, never a partial write.
  * **In-process fast path (mirrors ``setups.py``'s ``_SCAN_CACHE``, lines 357-408).** An
    INSTANCE-scoped (never module-level) atomic ``(key, result)`` tuple: a single rebind publishes
    a complete pair in one step, and every reader takes ONE local reference before inspecting it
    (read-local-reference-before-inspect) — the identical iter-6-hardened pattern, so a concurrent
    cold-cache reader either observes a complete prior publish or safely (redundantly, harmlessly)
    recomputes, never a torn key/result pairing. INSTANCE-scoped (not a module global) is
    deliberate: a freshly constructed ``EdgeReportCache`` always starts at ``_hot = None``, so
    "no in-process state carried over" (the durability test's simulated-restart premise) is a
    structural fact of construction, never a promise this class could accidentally break.

**Cache key — why it is FOUR parts, not the three the plan names.** The plan's key description is
"dataset checksums + strategy registry + ``config_fingerprint``". Three of those are exactly what
is implemented below — but ``config_fingerprint()`` is *deliberately* scoped to the tape/backtest/
PnL pipeline (see its own docstring's exclusion rationale in ``config.py``) and excludes several
field families this report's OWN call graph reads directly:

  * ``pnl_min_sample_size`` — the ``insufficient_sample`` gate ``edge_report.py``'s
    ``_split_cells`` bakes into every cell. It is fingerprint-excluded because everywhere ELSE
    that gate is a fresh PRESENTATION overlay recomputed on every read (``pnl_ledger.
    ledger_projection``), never persisted or cached — this report is the FIRST place its result
    gets baked into a value that might now be cached, so the "safe to exclude because never
    cached" premise no longer holds for this caller.
  * The ``sr_*`` / ``tradability_*`` / ``setups_*`` families (pivot/touch/cluster/band/quality/
    panel/horizon/threshold parameters) — excluded because levels/tradability/setups are
    documented as "a SEPARATE research computation... never stamped with, or compared across, a
    ``config_fingerprint`` anywhere" (``config.py``'s own words), true for every OTHER caller. But
    ``run_strategy_comparison_report`` calls ``compute_setups`` (which calls ``compute_tradability``,
    which consumes ``compute_levels``) to resolve each dataset's owning event, so a change to ANY
    of these parameters genuinely changes this report's cells (band class/side, reaction, or
    whether an event exists at all).

Rather than hand-enumerate and maintain that exact field list a second time here — the identical
"second copy of a policy" risk ``config_fingerprint``'s own docstring warns against ("not a
hand-picked subset") — the key ADDITIONALLY hashes the config's ENTIRE field content (the same
``dataclasses.asdict`` + canonical-JSON + sha256 mechanism ``config_fingerprint()`` itself uses,
with NO exclusion set) as a conservative catch-all: any config field change, fingerprinted or not,
busts this cache. The harmless cost: a purely-operational path field (e.g. a test's own temp
``journal_db_path``) also busts it on a genuine value change — an extra, harmless recompute,
accepted in exchange for NEVER silently serving a report computed under different levels/
tradability/setups/label parameters. ``config_fingerprint()`` and ``strategy_registry()`` stay in
the key too (not merely subsumed): ``strategy_registry()`` additionally catches a registered
STRATEGY SET/SHAPE change that no single field's value encodes (e.g. a new strategy id
registered in code), and ``config_fingerprint()`` is kept as an explicit, literally-named
component for auditability against the plan's own wording. This is a flagged judgment call — see
the dev handoff for the full reasoning.

**Store-integrity failures bypass the cache entirely — never risk masking one.** If
``dataset_store.list()`` reports ANY integrity error, ``get_or_compute`` does not attempt to key
or consult the cache at all; it calls ``compute_fn`` directly, which raises the SAME explicit
``EdgeReportError`` the uncached path always has (mirroring ``edge_report.py``'s own "a dataset
failing integrity verification aborts the whole report" discipline). Excluding corrupt files from
the signature (the ``setups.py`` ``_store_signature`` precedent) would otherwise risk a corrupt
file that is NOT part of any previously-cached healthy subset coincidentally matching a stale
cached key and silently serving a result that never saw the corruption — never worth the risk for
what is already the rare, explicit-failure path.

**era-fast_wall J-01 additions — ``lookup``/``compute_and_publish`` beside ``get_or_compute``.**
``get_or_compute`` stays UNTOUCHED (byte-identical, every one of its own tests unmodified). Two
new methods split its "check cache, else compute" behaviour into its two named halves, for the
interlude's headline "no compute on a GET, ever" anti-goal: ``lookup(records, config)`` is the
READ-ONLY half (hot slot then durable row, returns ``None`` on a miss, NEVER calls a compute
function) — the sole method the route now calls; ``compute_and_publish(dataset_store, config,
compute_fn)`` is the WRITE half (always recomputes unconditionally, republishes to both layers) —
the future operator/CLI "force" path (J-04). Both share the identical key derivation
(``_cache_key``) and store-integrity-bypass discipline ``get_or_compute`` already established
above. ``resolve_cache_db_path`` (module-level, not a method) is the DB-path resolution policy
itself, extracted from ``routes.py``'s inline dependency body so a future CLI caller resolves the
IDENTICAL path with zero duplicated logic.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..config import Config
from .algorithm_version import LEVELS_ALGORITHM_VERSION
from .datasets import DatasetStore

__all__ = ["EdgeReportCache", "resolve_cache_db_path"]

# The env var this cache's DB path resolution checks first (era-5B J-08, extracted to a shared
# resolver at era-fast_wall J-01 — see ``resolve_cache_db_path`` below).
_CACHE_DB_ENV = "TAPEOLOGY_EDGE_REPORT_CACHE_DB"

# Mirrors ``bar_index.py``'s ``_BUSY_TIMEOUT_MS`` (5000ms) — the identical brief writer-contention
# tolerance a low-frequency, small-payload cache needs.
_BUSY_TIMEOUT_MS = 5000

_SCHEMA = """
CREATE TABLE IF NOT EXISTS edge_report_cache (
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


def _canonical(obj: object) -> str:
    """The one canonical JSON encoding this module HASHES/KEYS with (stable across processes:
    sorted keys, no whitespace) — the ``datasets.py`` ``_canonical`` idiom, reused by name rather
    than re-derived a second time. HASHING/KEYING use ONLY: never used to serialize a RESULT for
    storage (see ``EdgeReportCache._insert``'s own docstring for why sorting there would break
    response byte-identity) — key order is irrelevant to a hash, but load-bearing for a stored
    report."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _config_content_hash(config: Config) -> str:
    """A conservative hash over EVERY ``Config`` field value (no exclusion set) — see the module
    docstring's "why four parts" section for exactly why ``config_fingerprint()`` alone is not
    enough for this specific cache. Reuses ``config_fingerprint()``'s own
    ``asdict`` + canonical-JSON + sha256 mechanism (never re-derived differently), just without
    its hand-picked exclusion set.

    ``LEVELS_ALGORITHM_VERSION`` (``algorithm_version.py`` — a dependency-free constants module,
    so this module still imports no computation path) is hashed in ALONGSIDE the config values: a
    change to the level/tradability computation moves every derived value here while leaving both
    the config and the store's own checksums byte-identical, so without it a cache written before
    such a change would keep serving results the current code can no longer produce. Every cache
    in this package keys through this ONE function, so the version lands in all of them at once
    (see that constant's own comment)."""
    payload = {
        "config": dataclasses.asdict(config),
        "levels_algorithm_version": LEVELS_ALGORITHM_VERSION,
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _cache_key(records: list[dict], config: Config) -> str:
    """The full key material: every registered dataset's (id, checksum) — train and hold-out
    together, sorted for order-independence (the ``setups.py`` ``_store_signature`` precedent) —
    plus the strategy registry, ``config_fingerprint()``, and the conservative whole-config
    content hash (see module docstring). Callers MUST have already confirmed ``records`` came from
    an error-free ``dataset_store.list()`` call (``get_or_compute`` enforces this — a store with
    integrity errors never reaches this function)."""
    payload = {
        "dataset_checksums": sorted((r["id"], r["checksum"]) for r in records),
        "strategy_registry": config.strategy_registry(),
        "config_fingerprint": config.config_fingerprint(),
        "config_content_hash": _config_content_hash(config),
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def resolve_cache_db_path(dataset_dir_resolved: str) -> str:
    """The cache DB path resolution policy (era-fast_wall J-01) — extracted from ``routes.py``'s
    inline ``get_edge_report_cache()`` body into ONE shared function (the ``get_bar_index``
    env-else-sibling shape) so a future CLI caller (J-04's warmer) resolves the IDENTICAL path with
    zero duplicated logic: the ``TAPEOLOGY_EDGE_REPORT_CACHE_DB`` env var if set, else a file
    co-located as a SIBLING of the caller's OWN already-resolved dataset directory. Takes the
    resolved dataset directory as a plain string rather than a ``Config`` — this module never
    imports ``config.py``'s singleton or its resolution helpers, only the ``Config`` dataclass type
    (unchanged import list) — so the caller (``routes.py``, and later the CLI) resolves its own
    dataset directory first, exactly as it already does today."""
    override = os.environ.get(_CACHE_DB_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(dataset_dir_resolved), "edge_report_cache.db")


class EdgeReportCache:
    """The persisted, rebuildable edge-report result cache — construct with an explicit, hermetic
    DB path (the ``BarIndex``/``DatasetStore``/``BarStore`` dependency-injection precedent)."""

    def __init__(self, db_path: str) -> None:
        self._db_path = str(db_path)
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = self._connect()
        try:
            with conn:
                conn.execute(_SCHEMA)
        finally:
            conn.close()
        # In-process atomic fast-path slot (mirrors setups.py's `_SCAN_CACHE`) — INSTANCE-scoped,
        # never a module-level global: see the module docstring for why this is load-bearing for
        # the durability test's "no in-process state carried over" simulated-restart guarantee.
        self._hot: tuple[str, dict] | None = None

    @property
    def db_path(self) -> str:
        """The resolved DB file path this cache was constructed with (introspection/tests only —
        never used to bypass ``get_or_compute``)."""
        return self._db_path

    def _connect(self) -> sqlite3.Connection:
        """A FRESH, short-lived connection (the ``JournalStore._read_conn()`` precedent — never
        one long-lived connection shared across threads; see the module docstring). Callers close
        it explicitly when done."""
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
        return conn

    def _select(self, key: str) -> dict | None:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT result_json FROM edge_report_cache WHERE cache_key=?", (key,)
            ).fetchone()
        finally:
            conn.close()
        return None if row is None else json.loads(row["result_json"])

    def _insert(self, key: str, result: dict) -> None:
        """One atomic transaction (``INSERT OR REPLACE`` inside ``with conn:``) — a concurrent
        reader can only ever observe the fully-committed prior row or the fully-committed new one,
        never a partial write (the torn-read guard's durable-layer half; the in-process tuple is
        the other half — see the module docstring).

        Deliberately serialized WITHOUT ``sort_keys`` (never ``_canonical`` — that helper is for
        HASHING/KEYING only, see its own docstring): FastAPI/Starlette's ``JSONResponse`` serializes
        a route's returned dict in its NATURAL insertion order, never alphabetically — so a
        cold-miss response (the caller's freshly computed dict, declaration order) and a
        durable-cache-hit response (this row, ``json.loads`` back into a fresh dict) are
        byte-identical ONLY if storage preserves that SAME order verbatim. Sorting here would
        silently make a warm SQLite-served response byte-DIFFER from an uncached one despite
        carrying identical content — the exact regression this discipline avoids (caught by
        ``tests/test_mcp_server.py``'s REST/MCP-proxy byte-identity tests, which compare raw wire
        bytes, not merely parsed-JSON equality)."""
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO edge_report_cache "
                    "(cache_key, result_json, created_utc) VALUES (?,?,?)",
                    (key, json.dumps(result), _iso_utc_now()),
                )
        finally:
            conn.close()

    def get_or_compute(
        self,
        dataset_store: DatasetStore,
        config: Config,
        compute_fn: Callable[[], dict],
    ) -> dict:
        """Serve a cached result for the CURRENT ``(dataset_store, config)`` signature, or call
        ``compute_fn`` (the caller's ONE computation path — this method never computes a report
        itself) and publish its result to both layers.

        A store-integrity failure bypasses the cache entirely (see module docstring): ``compute_fn``
        is called directly and its exception (if any) propagates unchanged — no key is ever
        computed or consulted in that case.

        Atomic against concurrent callers (mirrors ``setups.py``'s iter-6 ``_SCAN_CACHE``
        hardening): ``self._hot`` is read ONCE into a local (``hot``) before any inspection, so a
        concurrent rebind by another thread can never be observed as two different values within
        one call here. A cache miss on multiple concurrent threads only ever costs redundant,
        harmless recompute (``compute_fn`` is a pure function of its inputs) — it can never produce
        a torn key/result pairing, on either the in-process tuple or the durable SQLite row (whose
        own write is one atomic transaction)."""
        records, errors = dataset_store.list()
        if errors:
            return compute_fn()
        key = _cache_key(records, config)

        hot = self._hot  # read-local-reference-before-inspect
        if hot is not None and hot[0] == key:
            return hot[1]

        persisted = self._select(key)
        if persisted is not None:
            self._hot = (key, persisted)  # single atomic rebind
            return persisted

        result = compute_fn()
        self._insert(key, result)
        self._hot = (key, result)  # single atomic rebind, published AFTER the durable write
        return result

    def lookup(self, records: list[dict], config: Config) -> dict | None:
        """era-fast_wall J-01 — the GET-path's EXCLUSIVE read method: serve the CURRENT
        ``(records, config)`` key's cached result (hot slot then durable row), or ``None`` on a
        genuine miss. NEVER calls a compute function (unlike ``get_or_compute``) — there is no
        ``compute_fn`` parameter to call, so a miss is mechanically incapable of starting the
        sweep. Callers MUST have already confirmed ``records`` came from an error-free
        ``dataset_store.list()`` call — the identical ``get_or_compute``/``_cache_key`` contract
        (see that method's own docstring and the module docstring's key-derivation section).

        Atomic against concurrent callers, the identical ``get_or_compute`` discipline: ``self.
        _hot`` is read ONCE into a local before any inspection, and a durable hit republishes it to
        the hot slot in one atomic rebind (harmless if raced — the republished value is always the
        SAME already-persisted row)."""
        key = _cache_key(records, config)

        hot = self._hot  # read-local-reference-before-inspect
        if hot is not None and hot[0] == key:
            return hot[1]

        persisted = self._select(key)
        if persisted is not None:
            self._hot = (key, persisted)  # single atomic rebind
        return persisted

    def compute_and_publish(
        self,
        dataset_store: DatasetStore,
        config: Config,
        compute_fn: Callable[[], dict],
    ) -> dict:
        """era-fast_wall J-01 — the operator/CLI "force" half (J-04's future compute manager and
        CLI warmer both republish through this exact method; this iteration exercises it directly
        since no route calls it yet — see the module docstring). Always calls ``compute_fn``
        exactly once — UNCONDITIONALLY, never checking the cache first, unlike ``get_or_compute``
        — and republishes its result to both layers under the CURRENT ``(dataset_store, config)``
        key, so a subsequent ``lookup`` for the same key returns it verbatim.

        A store-integrity failure still bypasses the cache and calls ``compute_fn`` directly,
        propagating its exception unchanged — the identical ``get_or_compute`` discipline (see the
        module docstring's own "store-integrity failures bypass the cache entirely" section)."""
        records, errors = dataset_store.list()
        if errors:
            return compute_fn()
        key = _cache_key(records, config)

        result = compute_fn()
        self._insert(key, result)
        self._hot = (key, result)  # single atomic rebind, published AFTER the durable write
        return result
