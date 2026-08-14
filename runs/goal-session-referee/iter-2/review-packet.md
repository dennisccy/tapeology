# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 1.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/referee_evidence.py` (210 lines not shown)
- `apps/backend/tests/test_referee_evidence.py` (124 lines not shown)

```diff
diff --git a/apps/backend/app/research/referee_evidence.py b/apps/backend/app/research/referee_evidence.py
index c952ec7..a6d267d 100644
--- a/apps/backend/app/research/referee_evidence.py
+++ b/apps/backend/app/research/referee_evidence.py
@@ -51,24 +51,85 @@ store). ``REFEREE_FORMING_BAR_BASIS_CAVEAT`` is this iteration's FIRST authoring
 forming-bar disclosure sentence (``docs/goal.md``'s NOTES: no verbatim text exists anywhere yet) —
 the single source of truth later journeys (J-06, J-08) must read back verbatim rather than minting
 a second version.
+
+**The pinned J-01 response shape, restated (iteration-1 documentation rider).** ``GET
+/research/desk/referee/evidence``'s body is ``{"playbook_occurrence": {...}, "strategy_trade":
+{...}}``. Each block additionally carries an ``integrity_errors`` key (each store's own
+``.list()``-surfaced ``errors`` return, verbatim) — part of the pinned response shape from J-01
+onward: ``playbook_occurrence.integrity_errors`` and ``strategy_trade.integrity_errors`` are both
+served on every response, empty lists on a healthy corpus, and a corrupted/unparseable store file
+is surfaced there rather than crashing the endpoint or being silently dropped.
+
+**J-02 — the typed observation contract, two families, one shape.** ``docs/referee-statistical-
+spec.md`` §2 pins ONE observation record implemented ONCE, below, via the shared ``_observation``
+builder: ``{evidence_family, observation_id, symbol, session_date, anchor_ts, side, measure_key,
+value, cluster_key, provenance{detector_basis, config_fingerprint, context_algorithm_version,
+source_record_id, basis_caveats}}``. Units: directional ``value``s are the rail's own side-signed
+percent returns (``desk_forward._measure_from``'s ``sign`` already applied inside every recorded
+``forward`` block); MDD ``value``s are unsigned, direction-named, ``<= 0``-clamped, with the
+side→MDD binding ``long -> mdd_long_*``, ``short -> mdd_short_*``. Stated once, here; no adapter
+below restates or varies it.
+
+- **Playbook adapter** (``playbook_observations``): reuses ``current_playbook_detector_basis()``
+  and ``_newest_per_session_date()`` verbatim (J-01) for the ``(detector_basis,
+  config_fingerprint)`` pooling/dedup identity, then walks each newest-per-date record's own
+  already-measured signals through ``_resolve_leaf`` into one observation per applicable
+  ``DESK_FORWARD_MEASURE_KEYS`` entry — a truncated or structurally-unmeasurable
+  (``reason``-non-null) leaf is counted as an exclusion, never a fabricated or fallback value
+  (``desk_forward._collect_measures``'s own established exclusion rule, applied per-leaf here
+  instead of pooled). ``context_algorithm_version`` is always ``None`` this iteration (zero
+  dependency on ``desk_playbook_context`` — the import-ban guard proves it structurally) and
+  ``basis_caveats`` is always ``[]`` (the Card-6.4 caveat names strategy-family evidence only).
+  A per-file, stat-keyed ``RefereeObservationCache`` (see its own docstring) makes a warm read
+  skip every file's own parse+checksum verification; deleting it changes latency only.
+- **Strategy adapter** (``strategy_observations``): reads each recorded backtest report's own
+  ``result`` block, which ALREADY carries its trades joined to dataset/strategy identity verbatim
+  (``backtests.py``'s own ``"dataset": dataset_meta`` at record time) — no second ``DatasetStore``
+  lookup, no re-join. One ``measure_key == "net_r"`` observation per trade; ``cluster_key`` = the
+  dataset id; ``anchor_ts`` = ISO-8601 UTC of ``dataset.epoch_anchor + trade.entry.logical_ts``;
+  ``session_date`` = the ET calendar date of that same instant (spec §2 — distinct from
+  ``desk_sessions._session_date``, which is UTC-calendar and serves a different purpose); the
+  recorded ``random_null`` trades (``backtests.py::_null_trades``) are adapted as a SEPARATE,
+  labeled ``null_observations`` list, never merged into the primary trades; ``basis_caveats``
+  always carries ``REFEREE_FORMING_BAR_BASIS_CAVEAT`` verbatim (the iter-1 rider). ``detector_basis``
+  is always ``None`` for this family — a strategy trade has no detector, so the field the playbook
+  family uses for its own pooling identity is an honest absence here, the identical pattern
+  ``context_algorithm_version`` already uses when no context predicate is involved. Not cached —
+  see ``RefereeObservationCache``'s own docstring for why.
+
+Neither adapter writes to any pre-existing store (playbook/dataset/journal); both are pure reads
+through each store's own public API, exactly as J-01's readiness fold already established.
 """
 
 from __future__ import annotations
 
 import hashlib
 import json
+import os
+import sqlite3
+import threading
+from datetime import date, datetime, time, timezone
+from pathlib import Path
+from zoneinfo import ZoneInfo
 
 from .datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore
-from .desk_playbook import PlaybookStore, playbook_parameters
+from .desk_forward import DESK_FORWARD_HORIZONS_MINUTES, DESK_FORWARD_MEASURE_KEYS
+from .desk_playbook import PlaybookStore, playbook_parameters, resolve_desk_playbook_dir
 from .store import JournalStore
 
 __all__ = [
     "REFEREE_FORMING_BAR_BASIS_CAVEAT",
     "REFEREE_TICK_GATE_SYMBOL_DAYS",
+    "REFEREE_SESSION_COMPLETE_ET",
     "current_playbook_detector_basis",
     "playbook_occurrence_readiness",
     "strategy_trade_readiness",
     "referee_evidence",
+    # J-02: the typed evidence contract
+    "RefereeObservationCache",
+    "resolve_referee_obs_cache_db_path",
+    "playbook_observations",
+    "strategy_observations",
 ]
 
 # The Era-6 tick-corpus readiness gate (docs/research-directions.md's Part-1 prerequisite table:
@@ -97,6 +158,33 @@ REFEREE_FORMING_BAR_BASIS_CAVEAT: str = (
 # A readiness count must read every recorded report on file, never a display-sized sample.
 _ALL_BACKTESTS_SCAN_LIMIT = 1_000_000
 
+# spec Sec1's pre-registered completed-session constant: a record is confirmatory-eligible for a
+# symbol only if that symbol's finest measurement series reaches this ET wall-clock time on the
+# session date (partial mid-day records are exploratory-only). Era-wide, minted here since J-02 is
+# the first consumer; a plain module constant, never a Config field.
+REFEREE_SESSION_COMPLETE_ET: str = "15:55"
+
+# The Referee's own ET zone constant -- the `desk_playbook_features.py` per-module idiom (each
+# module that needs ET wall-clock resolution owns a private ZoneInfo constant rather than reaching
+# into another module's private one; RTH/ET conversion is a one-line stdlib call, not logic worth
+# a cross-module import for).
+_ET_ZONE = ZoneInfo("America/New_York")
+
+# The four rail horizon labels, in DESK_FORWARD_HORIZONS_MINUTES' own declared order -- derived,
+# never spelled out a second time, so a rail horizon addition can never silently desync here.
+_HORIZON_LABELS: tuple[str, ...] = tuple(label for label, _minutes in DESK_FORWARD_HORIZONS_MINUTES)
+
+# The observation cache's env override name and busy-timeout -- the `TAPEOLOGY_..._CACHE_DB`
+# family (`bar_verify_cache`/`playbook_evidence_cache_db_path`) precedent verbatim.
+_REFEREE_OBS_CACHE_DB_ENV = "TAPEOLOGY_REFEREE_OBS_CACHE_DB"
+_REFEREE_OBS_CACHE_BUSY_TIMEOUT_MS = 5000
+_REFEREE_PLAYBOOK_OBS_TABLE = "referee_playbook_observation_cache"
+
+# The playbook per-file observation-projection cache schema version -- bumped whenever a cached
+# projection's own shape gains fields a fold needs (the `desk_playbook_evidence._PROJECTION_
+# VERSION` precedent). A row cached at an older version is an honest miss, never a partial hit.
+_PLAYBOOK_OBS_PROJECTION_VERSION = 1
+
 
 def _canonical(obj: object) -> bytes:
     """The one canonical JSON encoding this module hashes -- the SAME encoding every other desk
@@ -243,3 +331,484 @@ def referee_evidence(
         "playbook_occurrence": playbook_occurrence_readiness(playbook_store, config_fingerprint),
         "strategy_trade": strategy_trade_readiness(dataset_store, journal_store),
     }
+
+
+# === J-02: the typed evidence contract — two families, one observation shape ========================
+#
+# Nothing below this line is wired into `referee_evidence()`/`GET /research/desk/referee/evidence`
+# — J-01's already-served response shape stays byte-identical (OUT OF SCOPE). This section adds a
+# standalone contract later journeys (J-04/J-05/J-06) import directly; J-02 itself serves no route
+# (goal.md's own `(Keyless; automated.)` tag — its acceptance is the hermetic fixture suite).
+
+
+def _iso(epoch: float) -> str:
+    """The per-module tiny-helper convention (``desk_forward.py._iso`` / ``desk_screen.py._iso``):
+    epoch -> ISO, so every served timestamp is formatted identically wherever it is read."""
+    return (
+        datetime.fromtimestamp(epoch, tz=timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _epoch_from_iso(iso: str) -> float:
+    """The inverse of ``_iso`` -- ``desk_forward._epoch``'s own idiom, copied fresh."""
+    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
+
+
+def _et_session_date(epoch: float) -> str:
+    """The ET calendar date ``epoch`` falls on, ``yyyy-MM-dd`` -- DST-correct by construction
+    (``zoneinfo`` resolves the UTC offset from the instant given, never a fixed offset). Spec
+    §2: a strategy observation's ``session_date`` is the ET date of its own entry instant --
+    distinct from ``desk_sessions._session_date``, which is UTC-calendar-date and serves session
+    detection, a different concept for a different purpose."""
+    return datetime.fromtimestamp(epoch, tz=_ET_ZONE).date().isoformat()
+
+
+def _session_complete_epoch(session_date: str) -> float:
+    """The UTC epoch ``REFEREE_SESSION_COMPLETE_ET`` (ET wall-clock) resolves to on
+    ``session_date`` -- ``desk_playbook_features._et_epoch``'s own idiom, copied fresh (a
+    one-line zoneinfo combine is not worth a cross-module import for)."""
+    hour, minute = (int(part) for part in REFEREE_SESSION_COMPLETE_ET.split(":"))
+    day = date.fromisoformat(session_date)
+    return datetime.combine(day, time(hour, minute), tzinfo=_ET_ZONE).timestamp()
+
+
+def _observation(
+    *,
+    evidence_family: str,
+    observation_id: str,
+    symbol: str | None,
+    session_date: str,
+    anchor_ts: str,
+    side: str,
+    measure_key: str,
+    value: float,
+    cluster_key: str | None,
+    detector_basis: str | None,
+    config_fingerprint: str | None,
+    context_algorithm_version: str | None,
+    source_record_id: str,
+    basis_caveats: list[str],
+) -> dict:
+    """ONE typed observation record -- ``docs/referee-statistical-spec.md`` §2's shape,
+    implemented ONCE, here, for both families (``docs/goal.md`` Key Capability 1). See the module
+    docstring's own J-02 section for the units/side->MDD binding stated once."""
+    return {
+        "evidence_family": evidence_family,
+        "observation_id": observation_id,
+        "symbol": symbol,
+        "session_date": session_date,
+        "anchor_ts": anchor_ts,
+        "side": side,
+        "measure_key": measure_key,
+        "value": value,
+        "cluster_key": cluster_key,
+        "provenance": {
+            "detector_basis": detector_basis,
+            "config_fingerprint": config_fingerprint,
+            "context_algorithm_version": context_algorithm_version,
+            "source_record_id": source_record_id,
+            "basis_caveats": list(basis_caveats),
+        },
+    }
+
+
+# --- the playbook adapter ----------------------------------------------------------------------------
+
+
+def _resolve_leaf(measure_key: str, forward: dict) -> tuple[float | None, bool]:
+    """``(value, excluded)`` for ONE of ``DESK_FORWARD_MEASURE_KEYS``' 15 keys, read off one
+    already-measured signal's own ``forward`` block (never re-measured). The four horizon labels
+    and their own ``mdd_long_*``/``mdd_short_*`` siblings share that horizon's own
+    ``reason``/``truncated`` flags -- ``desk_forward._measure_from`` measures a horizon's return
+    AND both its drawdowns over the IDENTICAL window, so all three are excluded together. The
+    session-end trio (``to_close``, ``mdd_long``, ``mdd_short``) is measured through session close
+    and is never excluded -- ``desk_forward._collect_measures``'s own "the session-end trio pools
+    every event" rule, applied per-leaf here instead of pooled. ``excluded`` means "no fallback
+    value, ever" (spec §2) -- the caller counts the exclusion and emits no observation for it."""
+    if measure_key == "to_close":
+        return forward["to_close_pct"], False
+    if measure_key == "mdd_long":
+        return forward["mdd_long_pct"], False
+    if measure_key == "mdd_short":
+        return forward["mdd_short_pct"], False
+    if measure_key in _HORIZON_LABELS:
+        horizon = forward["horizons"][measure_key]
+        excluded = horizon["reason"] is not None or horizon["truncated"]
+        return (None if excluded else horizon["return_pct"]), excluded
+    for prefix, field in (("mdd_long_", "mdd_long_pct"), ("mdd_short_", "mdd_short_pct")):
+        if measure_key.startswith(prefix) and measure_key[len(prefix) :] in _HORIZON_LABELS:
+            horizon = forward["horizons"][measure_key[len(prefix) :]]
+            excluded = horizon["reason"] is not None or horizon["truncated"]
+            return (None if excluded else horizon[field]), excluded
+    raise ValueError(f"unknown DESK_FORWARD_MEASURE_KEYS entry {measure_key!r}")
+
+
+def _signal_reaches_session_complete(signal: dict, session_date: str) -> bool:
+    """Best-effort per-signal completeness check (spec §2's completed-session rule): whether this
+    signal's own finest measurement series reaches ``REFEREE_SESSION_COMPLETE_ET`` on
+    ``session_date``, estimated from the signal's own already-recorded ``forward`` block
+    (``at_utc`` + ``minutes_to_close``, in bar-count-equivalent minutes -- ``_measure_from``'s own
+    documented unit for that field). **Known limitation, disclosed rather than hidden:** this
+    reading is blind to any intra-session bar gap between the signal's own anchor and the
+    session's actual last recorded bar (bar-count-equivalent minutes under-count true elapsed
+    wall-clock time whenever the finest series has a gap), so it is carried as a DISCLOSURE this
+    iteration, never a gate -- J-02 emits every applicable observation regardless of this flag;
+    only a later journey's confirmatory-eligibility fold (J-06) may ever filter on it."""
+    forward = signal.get("forward")
+    if forward is None:
+        return False
+    anchor_epoch = _epoch_from_iso(forward["at_utc"])
+    last_bar_epoch = anchor_epoch + forward["minutes_to_close"] * 60.0
+    return last_bar_epoch >= _session_complete_epoch(session_date)
+
+
+def _playbook_file_projection(record: dict) -> dict:
+    """Extract ONE already-verified playbook record's own candidate observations -- independent
+    of pooling (newest-per-date / current-basis selection happens in the caller, across every
+    file's own projection -- the ``desk_playbook_evidence._file_projection`` split). Nothing here
+    re-measures anything: every ``value`` is read off the record's own already-recorded
+    ``signal["forward"]`` block via ``_resolve_leaf``. A signal recorded before the (era-B2)
+    forward-measurement pass existed carries no ``forward`` block at all -- excluded from this
+    projection entirely (the same "predates measurement" absence ``PlaybookStore._registered``
+    itself reads back verbatim), never fabricated, never a crash."""
+    basis = _record_detector_basis(record)
+    observations: list[dict] = []
+    excluded_leaves = 0
+    symbols_with_signals: set[str] = set()
+    complete_by_symbol: dict[str, bool] = {}
+    for index, signal in enumerate(record["signals"]):
+        forward = signal.get("forward")
+        if forward is None:
+            continue
+        symbol = signal["symbol"]
+        symbols_with_signals.add(symbol)
+        if _signal_reaches_session_complete(signal, record["session_date"]):
+            complete_by_symbol[symbol] = True
+        else:
+            complete_by_symbol.setdefault(symbol, False)
+        for measure_key in DESK_FORWARD_MEASURE_KEYS:
+            value, excluded = _resolve_leaf(measure_key, forward)
+            if excluded:
+                excluded_leaves += 1
+                continue
+            observations.append(
+                _observation(
+                    evidence_family="playbook_occurrence",
+                    observation_id=f"playbook:{record['id']}:{index}:{measure_key}",
+                    symbol=symbol,
+                    session_date=record["session_date"],
+                    anchor_ts=signal["trigger_ts"],
+                    side=signal["side"],
+                    measure_key=measure_key,
+                    value=value,
+                    cluster_key=record["session_date"],
+                    detector_basis=basis,
+                    config_fingerprint=record["config_fingerprint"],
+                    context_algorithm_version=None,
+                    source_record_id=record["id"],
+                    basis_caveats=[],
+                )
+            )
+    return {
+        "projection_version": _PLAYBOOK_OBS_PROJECTION_VERSION,
+        "id": record["id"],
+        "session_date": record["session_date"],
+        "recorded_at": record["recorded_at"],
+        "record_detector_basis": basis,
+        "config_fingerprint": record["config_fingerprint"],
+        "symbol_coverage": len(symbols_with_signals),
+        "symbol_completeness": complete_by_symbol,
+        "excluded_leaves": excluded_leaves,
+        "observations": observations,
+    }
+
+
+class RefereeObservationCache:
+    """The durable, stat-keyed per-file cache behind the playbook adapter's observation
+    projections -- ``desk_playbook_evidence.PlaybookEvidenceCache``'s contract, copied fresh (the
+    identical "a fresh small class, not a shared import, because the cached SHAPE differs"
+    reasoning that module gives for not reusing ``desk_meta_cache.DeskMetaCache`` either). Owns
+    nothing: a row only ever remembers one already-verified playbook file's own already-built
+    candidate observations, keyed by that file's exact ``(path, size, mtime_ns)``. No
+    update/delete method exists anywhere on this class (structural): ``insert`` is
+    ``INSERT OR REPLACE``, idempotent under the identical key a legitimately re-verified file
+    would produce. Deleting the DB file changes only how many files must be re-read through
+    ``PlaybookStore.get`` to reproduce the IDENTICAL result -- never the served content (TC-2).
+
+    **The strategy family is deliberately NOT cached through this class, or any other.** Unlike
+    ``PlaybookStore``'s per-file JSON store (no metadata-only listing exists, so every
+    ``store.list()`` call re-parses and re-verifies every file on disk -- the exact cost
+    ``desk_meta_cache.py``'s own docstring motivates this whole class family against),
+    ``JournalStore`` is a single indexed SQLite table and ``DatasetStore`` already carries its own
+    optional index accelerator (``index_db_path``) -- neither exposes a metadata-only projection
+    cheaper than the read itself, so a cache here could only ever cost as much as what it claims
+    to save. ``strategy_observations`` reads fresh every call, exactly as J-01's own
+    ``strategy_trade_readiness`` already does, uncached, today."""
+
+    def __init__(self, db_path: str) -> None:
+        self._db_path = str(db_path)
+        if self._db_path != ":memory:":
+            Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
+        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
+        self._conn.row_factory = sqlite3.Row
+        # One connection, several threads (FastAPI's sync-route threadpool) -- the
+        # `desk_meta_cache.py`/`desk_playbook_evidence.py` serialization, for the identical reason.
+        self._lock = threading.Lock()
+        if self._db_path != ":memory:":
+            self._conn.execute("PRAGMA journal_mode=WAL")
+        self._conn.execute(f"PRAGMA busy_timeout={_REFEREE_OBS_CACHE_BUSY_TIMEOUT_MS}")
+        with self._lock, self._conn:
+            self._conn.execute(
+                f"CREATE TABLE IF NOT EXISTS {_REFEREE_PLAYBOOK_OBS_TABLE} ("
+                "    path            TEXT PRIMARY KEY,"
+                "    size            INTEGER NOT NULL,"
+                "    mtime_ns        INTEGER NOT NULL,"
+                "    projection_json TEXT NOT NULL)"
+            )
+
+    @property
+    def db_path(self) -> str:
+        return self._db_path
+
+    def lookup(self, path: str, size: int, mtime_ns: int) -> dict | None:
+        """An exact ``(path, size, mtime_ns)`` match -- ANY stat difference (a genuine content
+        change, a moved file, or simply no row yet) is an honest miss, never a stale hit."""
+        with self._lock:
+            row = self._conn.execute(
+                f"SELECT size, mtime_ns, projection_json FROM {_REFEREE_PLAYBOOK_OBS_TABLE} "
+                "WHERE path=?",
+                (path,),
+            ).fetchone()
+        if row is None or row["size"] != size or row["mtime_ns"] != mtime_ns:
+            return None
+        return json.loads(row["projection_json"])
+
+    def insert(self, path: str, size: int, mtime_ns: int, projection: dict) -> None:
+        """Additively remember ONE already-extracted file projection. ``json.dumps`` WITHOUT
+        ``sort_keys`` -- a cache hit must reproduce the EXACT key order a fresh extraction would
+        (the ``desk_meta_cache.py`` byte-identity precedent), so a served result never differs
+        between a cold and a warm read (TC-2)."""
+        with self._lock, self._conn:
+            self._conn.execute(
+                f"INSERT OR REPLACE INTO {_REFEREE_PLAYBOOK_OBS_TABLE} "
+                "(path, size, mtime_ns, projection_json) VALUES (?,?,?,?)",
+                (path, size, mtime_ns, json.dumps(projection)),
+            )
+
+
+def resolve_referee_obs_cache_db_path(desk_universe_dir_resolved: str) -> str:
+    """The resolved durable observation-cache path: the ``TAPEOLOGY_REFEREE_OBS_CACHE_DB`` env
+    var if set, else a file co-located as a SIBLING of the playbook directory
+    (``playbook_evidence_cache_db_path``'s resolver verbatim, one level up since this module has
... [diff_bound] apps/backend/app/research/referee_evidence.py: 210 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_referee_evidence.py b/apps/backend/tests/test_referee_evidence.py
index aaff88d..8d5f20e 100644
--- a/apps/backend/tests/test_referee_evidence.py
+++ b/apps/backend/tests/test_referee_evidence.py
@@ -10,7 +10,10 @@ hand computation can reproduce, not one a compute happened to produce."""
 
 from __future__ import annotations
 
+import hashlib
+import os
 import time
+from pathlib import Path
 
 import pytest
 from fastapi.testclient import TestClient
@@ -18,14 +21,19 @@ from fastapi.testclient import TestClient
 from app.config import CONFIG
 from app.main import app
 from app.providers.base import Side, TradeEvent
+from app.research import desk_playbook as desk_playbook_module
+from app.research import referee_evidence as referee_evidence_module
 from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore
 from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
 from app.research.desk_routes import get_playbook_store
 from app.research.referee_evidence import (
     REFEREE_FORMING_BAR_BASIS_CAVEAT,
     REFEREE_TICK_GATE_SYMBOL_DAYS,
+    RefereeObservationCache,
     _tick_gate_state,
     current_playbook_detector_basis,
+    playbook_observations,
+    strategy_observations,
 )
 from app.research.routes import ResearchRegistry, get_dataset_store, set_registry
 from app.research.store import BacktestRecord, JournalStore
@@ -248,3 +256,488 @@ def test_tick_gate_state_met_branch():
     comfortably_met, statement2 = _tick_gate_state(REFEREE_TICK_GATE_SYMBOL_DAYS + 50)
     assert comfortably_met is True
     assert str(REFEREE_TICK_GATE_SYMBOL_DAYS + 50) in statement2
+
+
+# --- TC-11: the iteration-1 documentation rider ------------------------------------------------------
+
+
+def test_module_docstring_pins_integrity_errors_as_part_of_the_response_shape():
+    """The iter-1 eval/coherence rider: the two already-served ``integrity_errors`` fields are now
+    named explicitly as part of the pinned ``GET /research/desk/referee/evidence`` response shape
+    -- documentation-only, behavior unchanged (J-01's own fixture tests above still pass
+    unmodified, proving the shape itself never moved)."""
+    doc = referee_evidence_module.__doc__ or ""
+    assert "playbook_occurrence.integrity_errors" in doc
+    assert "strategy_trade.integrity_errors" in doc
+
+
+# === J-02: the typed evidence contract -- fixture builders (goal-referee-iter-2 TC-1..TC-9) ==========
+#
+# Every fixture below plants records through each store's own public write path
+# (``PlaybookStore.record`` / ``DatasetStore.record`` / ``JournalStore.insert_backtest`` --
+# ``_plant_playbook_record``/``_plant_dataset`` reused verbatim from the J-01 section above), so
+# every pooled count and every served value below is a number this file's own hand computation can
+# reproduce, never one a real compute happened to produce.
+
+
+def _horizon(
+    *,
+    return_pct: float | None = None,
+    mdd_long_pct: float | None = None,
+    mdd_short_pct: float | None = None,
+    truncated: bool = False,
+    reason: str | None = None,
+) -> dict:
+    """One ``forward["horizons"][label]`` leaf, shaped exactly as ``desk_forward._measure_from``
+    returns it (every key present, ``exit_price``/``effective_minutes`` are irrelevant filler for
+    this fold since the adapter never reads them)."""
+    return {
+        "return_pct": return_pct,
+        "exit_price": 0.0,
+        "mdd_long_pct": mdd_long_pct,
+        "mdd_short_pct": mdd_short_pct,
+        "truncated": truncated,
+        "effective_minutes": 0,
+        "reason": reason,
+    }
+
+
+# 15 DISTINCT, hand-typed values -- one per ``DESK_FORWARD_MEASURE_KEYS`` entry -- so a test can
+# assert each key's own served value by literal comparison, never by re-deriving it through the
+# same mapping the adapter itself uses.
+_EXPECTED_FULL_FORWARD_VALUES = {
+    "1m": 10.0, "5m": 20.0, "1h": 30.0, "4h": 40.0, "to_close": 99.0,
+    "mdd_long_1m": -1.0, "mdd_long_5m": -2.0, "mdd_long_1h": -3.0, "mdd_long_4h": -4.0,
+    "mdd_long": -9.0,
+    "mdd_short_1m": -1.5, "mdd_short_5m": -2.5, "mdd_short_1h": -3.5, "mdd_short_4h": -4.5,
+    "mdd_short": -9.5,
+}
+
+
+def _full_forward(at_utc: str, *, minutes_to_close: int = 240) -> dict:
+    """A fully-measured ``forward`` block -- every one of the 15 ``DESK_FORWARD_MEASURE_KEYS``
+    leaves present and unexcluded, matching ``_EXPECTED_FULL_FORWARD_VALUES`` exactly."""
+    return {
+        "at_utc": at_utc,
+        "entry_price": 100.0,
+        "entry_kind": "level",
+        "horizons": {
+            "1m": _horizon(return_pct=10.0, mdd_long_pct=-1.0, mdd_short_pct=-1.5),
+            "5m": _horizon(return_pct=20.0, mdd_long_pct=-2.0, mdd_short_pct=-2.5),
+            "1h": _horizon(return_pct=30.0, mdd_long_pct=-3.0, mdd_short_pct=-3.5),
+            "4h": _horizon(return_pct=40.0, mdd_long_pct=-4.0, mdd_short_pct=-4.5),
+        },
+        "to_close_pct": 99.0,
+        "close_price": 101.0,
+        "minutes_to_close": minutes_to_close,
+        "mdd_long_pct": -9.0,
+        "mdd_short_pct": -9.5,
+    }
+
+
+def _measured_signal(*, symbol: str, side: str, setup_id: str, trigger_ts: str, forward: dict) -> dict:
+    """A minimal already-measured signal -- only the fields ``playbook_observations`` reads."""
+    return {"symbol": symbol, "setup_id": setup_id, "side": side, "trigger_ts": trigger_ts, "forward": forward}
+
+
+def _trade(*, direction: str = "long", logical_ts: float = 100.0, net_r: float = 1.0) -> dict:
+    """A minimal ``_close_trade``-shaped trade -- only the fields the strategy adapter reads."""
+    return {
+        "setup_type": "v1",
+        "direction": direction,
+        "entry": {"logical_ts": logical_ts, "price": 100.0, "fill_price": 100.0, "spread": 0.0},
+        "exit": {
+            "logical_ts": logical_ts + 60.0, "price": 101.0, "fill_price": 101.0, "spread": 0.0,
+            "reason": "horizon",
+        },
+        "invalidation_price": 99.0,
+        "r_basis": 1.0,
+        "shares": 1.0,
+        "gross_r": net_r,
+        "net_r": net_r,
+        "gross_usd": 0.0,
+        "net_usd": 0.0,
+        "fees_usd": 0.0,
+        "slippage_usd": 0.0,
+    }
+
+
+def _plant_backtest_result(
+    journal_store: JournalStore,
+    *,
+    backtest_id: str,
+    dataset: dict,
+    strategy_id: str = "v1",
+    profile: str = "default",
+    config_fingerprint: str | None = None,
+    trades: list[dict],
+    null_trades: list[dict],
+) -> None:
+    """Plant one ``done`` backtest report whose ``result`` block already carries the dataset
+    joined verbatim -- ``backtests.py``'s own result-block shape (§0.4's `"dataset": dataset_meta`
+    line), reproduced by hand rather than run through a real replay."""
+    payload = {
+        "id": backtest_id,
+        "status": "done",
+        "result": {
+            "dataset": dataset,
+            "strategy_id": strategy_id,
+            "profile": profile,
+            "config_fingerprint": config_fingerprint or CONFIG.config_fingerprint(),
+            "trades": trades,
+            "null_baseline": {"seed": 1729, "entry_count": len(null_trades), "trades": null_trades},
+        },
+    }
+    journal_store.insert_backtest(
+        BacktestRecord(id=backtest_id, payload=payload, created_wall_ts=time.time())
+    )
+
+
+def _hash_store_files(*roots: Path) -> dict[str, str]:
+    digest: dict[str, str] = {}
+    for root in roots:
+        if not root.exists():
+            continue
+        for path in sorted(root.rglob("*")):
+            if path.is_file():
+                digest[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
+    return digest
+
+
+# --- TC-1 / TC-6: the playbook observation contract, cold, including one excluded leaf ---------------
+
+
+def test_playbook_observations_matches_hand_computed_golden_fixture_and_excludes_unmeasurable_leaves(
+    client,
+):
+    c, store, _dataset_store, _journal_store = client
+    fingerprint = CONFIG.config_fingerprint()
+    basis = current_playbook_detector_basis()
+
+    forward_a = _full_forward("2026-06-08T13:35:00.000000Z")
+    signal_a = _measured_signal(
+        symbol="AAPL", side="long", setup_id="capitulation",
+        trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward_a,
+    )
+    # A second signal with ONE structurally-unmeasurable leaf -- the real "1m horizon finer than
+    # the 5m touch series" absence text `_measure_from` itself writes -- TC-1's own "at least one
+    # truncated/unmeasurable leaf" requirement, and TC-6's dedicated exclusion case.
+    forward_b = _full_forward("2026-06-08T14:00:00.000000Z")
+    forward_b["horizons"]["1m"] = _horizon(
+        reason="the 1m horizon is finer than the 5m touch series",
+    )
+    signal_b = _measured_signal(
+        symbol="MSFT", side="short", setup_id="jbe",
+        trigger_ts="2026-06-08T14:00:00.000000Z", forward=forward_b,
+    )
+    record = _plant_playbook_record(
+        store, session_date="2026-06-08", signature="sig-tc1", signals=[signal_a, signal_b],
+    )
+
+    result = playbook_observations(store, fingerprint)
+
+    assert result["detector_basis"] == basis
+    assert result["config_fingerprint"] == fingerprint
+    # signal_a: all 15 keys. signal_b: the "1m" horizon's own reason excludes THREE keys that
+    # share its window -- "1m", "mdd_long_1m", "mdd_short_1m" (_resolve_leaf's own rule: a
+    # horizon's return and both its drawdowns are measured over the identical window, so all
+    # three are excluded together) -- leaving 12.
+    assert len(result["observations"]) == 15 + 12
+
+    by_key = {(o["symbol"], o["measure_key"]): o for o in result["observations"]}
+    for measure_key, expected_value in _EXPECTED_FULL_FORWARD_VALUES.items():
+        assert by_key[("AAPL", measure_key)] == {
+            "evidence_family": "playbook_occurrence",
+            "observation_id": f"playbook:{record['id']}:0:{measure_key}",
+            "symbol": "AAPL",
+            "session_date": "2026-06-08",
+            "anchor_ts": "2026-06-08T13:35:00.000000Z",
+            "side": "long",
+            "measure_key": measure_key,
+            "value": expected_value,
+            "cluster_key": "2026-06-08",
+            "provenance": {
+                "detector_basis": basis,
+                "config_fingerprint": fingerprint,
+                "context_algorithm_version": None,
+                "source_record_id": record["id"],
+                "basis_caveats": [],
+            },
+        }
+
+    excluded_keys = {"1m", "mdd_long_1m", "mdd_short_1m"}
+    for key in excluded_keys:
+        assert ("MSFT", key) not in by_key  # the excluded leaves -- no fallback, no fabricated value
+    for measure_key, expected_value in _EXPECTED_FULL_FORWARD_VALUES.items():
+        if measure_key in excluded_keys:
+            continue
+        obs = by_key[("MSFT", measure_key)]
+        assert obs["value"] == expected_value
+        assert obs["side"] == "short"
+        assert obs["anchor_ts"] == "2026-06-08T14:00:00.000000Z"
+        assert obs["observation_id"] == f"playbook:{record['id']}:1:{measure_key}"
+        assert obs["cluster_key"] == "2026-06-08"
+
+    assert result["excluded_leaves"] == 3
+    assert result["coverage_by_date"] == [{"session_date": "2026-06-08", "symbol_count": 2}]
+    assert result["coverage_shrink_disclosures"] == []
+
+
+# --- TC-2: cold / warm / deleted-cache parity ---------------------------------------------------------
+
+
+def test_playbook_observations_cache_cold_warm_deleted_parity(client, tmp_path):
+    c, store, _dataset_store, _journal_store = client
+    forward = _full_forward("2026-06-08T13:35:00.000000Z")
+    signal = _measured_signal(
+        symbol="AAPL", side="long", setup_id="capitulation",
+        trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward,
+    )
+    _plant_playbook_record(store, session_date="2026-06-08", signature="sig-tc2", signals=[signal])
+    fingerprint = CONFIG.config_fingerprint()
+
+    db_path = str(tmp_path / "referee_obs_cache.db")
+    cache_cold = RefereeObservationCache(db_path)
+    result_cold = playbook_observations(store, fingerprint, cache=cache_cold)
+
+    cache_warm = RefereeObservationCache(db_path)  # a FRESH connection to the now-populated file
+    result_warm = playbook_observations(store, fingerprint, cache=cache_warm)
+
+    os.remove(db_path)
+    cache_deleted = RefereeObservationCache(db_path)  # recreates the file, empty
+    result_deleted = playbook_observations(store, fingerprint, cache=cache_deleted)
+
+    assert result_cold["observations"]  # sanity: the fixture actually produced observations
+    assert result_cold == result_warm == result_deleted
+
+
+# --- TC-3: two signatures, identical parameters -> ONE pooled detector_basis --------------------------
+
+
+def test_playbook_observations_pools_two_signatures_with_identical_parameters_into_one_basis(client):
+    c, store, _dataset_store, _journal_store = client
+    forward_1 = _full_forward("2026-06-08T13:35:00.000000Z")
+    signal_1 = _measured_signal(
+        symbol="AAPL", side="long", setup_id="capitulation",
+        trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward_1,
+    )
+    forward_2 = _full_forward("2026-06-09T13:35:00.000000Z")
+    signal_2 = _measured_signal(
+        symbol="MSFT", side="long", setup_id="capitulation",
+        trigger_ts="2026-06-09T13:35:00.000000Z", forward=forward_2,
+    )
+    _plant_playbook_record(store, session_date="2026-06-08", signature="sig-x", signals=[signal_1])
+    _plant_playbook_record(store, session_date="2026-06-09", signature="sig-y", signals=[signal_2])
+
+    result = playbook_observations(store, CONFIG.config_fingerprint())
+
+    assert {o["session_date"] for o in result["observations"]} == {"2026-06-08", "2026-06-09"}
+    assert {o["provenance"]["detector_basis"] for o in result["observations"]} == {
+        current_playbook_detector_basis()
+    }
+
+
+# --- TC-4: a monkeypatched detector constant splits the pool ------------------------------------------
+
+
+def test_playbook_detector_basis_splits_on_a_monkeypatched_constant(client, monkeypatch):
+    c, store, _dataset_store, _journal_store = client
+    fingerprint = CONFIG.config_fingerprint()
+
+    forward_1 = _full_forward("2026-06-08T13:35:00.000000Z")
+    signal_1 = _measured_signal(
+        symbol="AAPL", side="long", setup_id="capitulation",
+        trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward_1,
+    )
+    _plant_playbook_record(store, session_date="2026-06-08", signature="sig-before", signals=[signal_1])
+    basis_before = current_playbook_detector_basis()
+
+    monkeypatch.setattr(desk_playbook_module, "PLAYBOOK_MIN_N_DISCLOSURE", 999)
+    basis_after = current_playbook_detector_basis()
+    assert basis_after != basis_before  # sanity: the monkeypatch genuinely moves the LIVE basis
+
+    forward_2 = _full_forward("2026-06-09T13:35:00.000000Z")
+    signal_2 = _measured_signal(
+        symbol="MSFT", side="long", setup_id="capitulation",
+        trigger_ts="2026-06-09T13:35:00.000000Z", forward=forward_2,
+    )
+    _plant_playbook_record(store, session_date="2026-06-09", signature="sig-after", signals=[signal_2])
+
+    result_after = playbook_observations(store, fingerprint)
+    assert result_after["detector_basis"] == basis_after
+    assert {o["session_date"] for o in result_after["observations"]} == {"2026-06-09"}
+    assert all(o["provenance"]["detector_basis"] == basis_after for o in result_after["observations"])
+
+    monkeypatch.undo()
+    result_before = playbook_observations(store, fingerprint)
+    assert result_before["detector_basis"] == basis_before
+    assert {o["session_date"] for o in result_before["observations"]} == {"2026-06-08"}
+    assert all(
+        o["provenance"]["detector_basis"] == basis_before for o in result_before["observations"]
+    )
+
+
+# --- TC-5: same-date dedup, newest wins, coverage-shrink disclosure ------------------------------------
+
+
+def test_playbook_observations_dedup_selects_newest_and_discloses_coverage_shrink(client):
+    c, store, _dataset_store, _journal_store = client
+    forward = _full_forward("2026-06-08T13:35:00.000000Z")
+    older_signals = [
+        _measured_signal(
+            symbol=sym, side="long", setup_id="capitulation",
+            trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward,
+        )
+        for sym in ("AAPL", "MSFT", "GOOG")
+    ]
+    newer_signals = [
+        _measured_signal(
+            symbol=sym, side="long", setup_id="capitulation",
+            trigger_ts="2026-06-08T13:35:00.000000Z", forward=forward,
+        )
+        for sym in ("AAPL", "MSFT")
+    ]
+    older = _plant_playbook_record(
+        store, session_date="2026-06-08", signature="sig-older", signals=older_signals,
+    )
+    newer = _plant_playbook_record(
+        store, session_date="2026-06-08", signature="sig-newer", signals=newer_signals,
+    )
+
+    result = playbook_observations(store, CONFIG.config_fingerprint())
+
+    assert {o["symbol"] for o in result["observations"]} == {"AAPL", "MSFT"}  # newer record only
+    assert result["coverage_by_date"] == [{"session_date": "2026-06-08", "symbol_count": 2}]
+    assert result["coverage_shrink_disclosures"] == [
+        {
+            "session_date": "2026-06-08",
+            "newest_record_id": newer["id"],
+            "newest_symbol_count": 2,
+            "superseded_record_id": older["id"],
+            "superseded_symbol_count": 3,
+        }
+    ]
... [diff_bound] apps/backend/tests/test_referee_evidence.py: 124 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_referee_guards.py b/apps/backend/tests/test_referee_guards.py
index f86400f..b2557a6 100644
--- a/apps/backend/tests/test_referee_guards.py
+++ b/apps/backend/tests/test_referee_guards.py
@@ -26,6 +26,7 @@ playbook_guards.py`` precedent: "a lint that cannot fail proves nothing")."""
 
 from __future__ import annotations
 
+import ast
 import hashlib
 import inspect
 import pathlib
@@ -36,6 +37,7 @@ from app.research.desk_playbook_context import PLAYBOOK_CONTEXT_ALGORITHM_VERSIO
 REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
 _SPEC_PATH = REPO_ROOT / "docs" / "playbook-detector-spec.md"
 _CATALOG_PATH = REPO_ROOT / "docs" / "research-directions.md"
+_RESEARCH_DIR = pathlib.Path(__file__).resolve().parents[1] / "app" / "research"
 
 
 # --- (a) the playbook-band-context-v3 spec-drift pin (TC-6, TC-7) ----------------------------------
@@ -129,3 +131,82 @@ def test_catalog_reconciliation_guard_can_fail_on_a_seeded_removal():
     """The lint CAN fail: a string genuinely absent from the doc is rejected."""
     text = _CATALOG_PATH.read_text()
     assert "this exact sentence was never written to the catalog, ever" not in text
+
+
+# --- (c) goal-referee-iter-2 TC-10: the bidirectional import-ban -------------------------------------
+#
+# goal.md's "the Referee never feeds back" anti-goal (critical): no referee_*.py module may import
+# the live detection/context machinery (it reads already-recorded records only), and neither
+# desk_playbook_detect.py nor desk_playbook_context.py may import any referee_* module (the frozen
+# detection/context layer stays wholly unaware the Referee exists). AST-structural
+# (``test_bar_store_projection_guard.py``'s precedent), not a regex over source text, which a
+# comment or a string literal could false-positive.
+
+
+def _imported_module_names(path: pathlib.Path) -> set[str]:
+    """Every dotted name this file's ``import``/``from ... import ...`` statements mention --
+    both the bare module (``import a.b`` -> ``a.b``; ``from a.b import c`` -> ``a.b``) and each
+    imported name alone AND module-qualified (``from a.b import c`` also adds ``c`` and
+    ``a.b.c``), so ``from . import referee_evidence``, ``from .referee_evidence import X``, and
+    ``from app.research import referee_evidence`` are all caught the same way."""
+    tree = ast.parse(path.read_text())
+    names: set[str] = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Import):
+            for alias in node.names:
+                names.add(alias.name)
+        elif isinstance(node, ast.ImportFrom):
+            if node.module:
+                names.add(node.module)
+            for alias in node.names:
+                names.add(alias.name)
+                if node.module:
+                    names.add(f"{node.module}.{alias.name}")
+    return names
+
+
+def _mentioning(names: set[str], target: str) -> set[str]:
+    """Every name in ``names`` whose own LAST dotted component equals ``target`` exactly --
+    ``app.research.desk_playbook_context`` matches ``desk_playbook_context``;
+    ``desk_playbook_context_module`` (a local alias' own bound name, never an import target) does
+    not."""
+    return {name for name in names if name.split(".")[-1] == target}
+
+
+def _referee_modules() -> list[pathlib.Path]:
+    return sorted(_RESEARCH_DIR.glob("referee_*.py"))
+
+
+def test_no_referee_module_imports_the_detect_or_context_modules():
+    """TC-10 (first direction): zero imports of ``desk_playbook_detect`` or
+    ``desk_playbook_context`` inside any ``referee_*.py`` module."""
+    referee_modules = _referee_modules()
+    assert referee_modules, "no referee_*.py module found -- has the glob/location changed?"
+    for path in referee_modules:
+        imported = _imported_module_names(path)
+        hit = _mentioning(imported, "desk_playbook_detect") | _mentioning(imported, "desk_playbook_context")
+        assert not hit, f"{path.name} imports the banned module(s) {hit}"
+
+
+def test_the_detect_and_context_modules_import_no_referee_module():
+    """TC-10 (second direction): zero imports of any ``referee_*`` module inside
+    ``desk_playbook_detect.py`` or ``desk_playbook_context.py``."""
+    for filename in ("desk_playbook_detect.py", "desk_playbook_context.py"):
+        path = _RESEARCH_DIR / filename
+        assert path.exists(), f"{filename} not found at the expected location -- has it moved?"
+        imported = _imported_module_names(path)
+        hits = {name for name in imported if name.split(".")[-1].startswith("referee_")}
+        assert not hits, f"{filename} imports referee module(s) {hits}"
+
+
+def test_import_ban_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing (this file's own established
+    per-guard precedent, e.g. ``test_desk_playbook_context_zero_diff_guard_can_fail_on_a_seeded_
+    violation`` above)."""
+    seeded_imports = {"app.research.desk_playbook_detect", "app.research.other"}
+    assert _mentioning(seeded_imports, "desk_playbook_detect") == {
+        "app.research.desk_playbook_detect"
+    }
+    seeded_referee_imports = {"app.research.referee_evidence", "app.research.other"}
+    hits = {name for name in seeded_referee_imports if name.split(".")[-1].startswith("referee_")}
+    assert hits == {"app.research.referee_evidence"}
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-referee/telemetry.jsonl   | 7 +++++++
 runs/goal-session-referee/trace/trace.jsonl | 1 +
 2 files changed, 8 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
