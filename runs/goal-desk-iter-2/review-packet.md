# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/app/research/bar_index.py b/apps/backend/app/research/bar_index.py
index 525af40..9f60084 100644
--- a/apps/backend/app/research/bar_index.py
+++ b/apps/backend/app/research/bar_index.py
@@ -149,6 +149,32 @@ class BarIndex:
 
     # --- list (the GET filter) -------------------------------------------------------------------
 
+    # --- coverage (Era B "The Desk" J-02, additive) -----------------------------------------------
+
+    def coverage(self, symbol: str, timeframe: str) -> tuple[bool, str | None]:
+        """``(has_bars, latest_window_end_utc)`` for ONE ``(symbol, timeframe)`` pair — Era B J-02's
+        coverage-read accessor (``desk_coverage.py``). A SINGLE indexed aggregate query
+        (``COUNT``+``MAX`` over the already-existing ``window_end_utc`` column) — never resolved
+        through ``BarStore`` (T-4: coverage/freshness reads ``bar_index`` only). ``has_bars`` is
+        ``True`` iff at least one indexed row exists for this pair; ``latest_window_end_utc`` is the
+        lexicographically-greatest recorded ``window_end_utc`` among those rows (== chronologically
+        latest, since every ``window_end_utc`` this codebase writes is a zero-padded ISO-8601 UTC
+        string — the same string-sort convention ``bars.py``/``desk_universe.py`` already rely on),
+        or ``None`` when ``has_bars`` is ``False`` — never a fabricated placeholder.
+
+        Purely ADDITIVE: a brand-new method: ``BarIndexHit``'s fields and every existing
+        ``lookup``/``insert``/``list``/``reindex`` call site are byte-unchanged (a new dataclass
+        field on ``BarIndexHit`` would have broken ``tests/test_bar_index.py``'s existing
+        equality assertions, which construct ``BarIndexHit`` with exactly its original three
+        fields — this accessor exists instead of that)."""
+        row = self._conn.execute(
+            "SELECT COUNT(*) AS n, MAX(window_end_utc) AS latest FROM bar_index "
+            "WHERE symbol=? AND timeframe=?",
+            (symbol, timeframe),
+        ).fetchone()
+        has_bars = row["n"] > 0
+        return has_bars, (row["latest"] if has_bars else None)
+
     def list(self, symbol: str | None = None, timeframe: str | None = None) -> list[BarIndexHit]:
         """Every indexed entry matching the given (optional, independently combinable) filters.
         Row order is NOT meaningful here — the route re-sorts after resolving each hit through
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 9cde5d0..0878d09 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -1,14 +1,27 @@
-"""``/research/desk/*`` — Era B "The Desk" (J-01): universe ingestion.
-
-THIS is the first desk-era route module: two routes over the new universe subsystem
-(``desk_universe.py``) — ``POST /research/desk/universe/fetch`` (the explicit operator research
-action: fetch -> parse -> validate -> register) and ``GET /research/desk/universe`` (snapshot
-list + latest membership, honestly empty before any registration — never 404). Kept as its own
-module (mirroring the plan's stated preference) rather than folding into ``routes.py``, which is
-already large; mounted separately in ``app/main.py``.
-
-The fetch is a single synchronous vendor call, so — unlike the longer-running J-02/J-03 top-up and
-screen runs — it needs no compute-manager (that pattern lands with those later journeys)."""
+"""``/research/desk/*`` — Era B "The Desk" (J-01 + J-02): universe ingestion, coverage, and the
+bar top-up.
+
+J-01 (unmodified this iteration): two routes over the universe subsystem (``desk_universe.py``) —
+``POST /research/desk/universe/fetch`` (the explicit operator research action: fetch -> parse ->
+validate -> register) and ``GET /research/desk/universe`` (snapshot list + latest membership,
+honestly empty before any registration — never 404).
+
+J-02 (this iteration) adds two more concepts under the SAME router: ``GET /research/desk/coverage``
+(a pure read, ``desk_coverage.get_desk_coverage`` — no compute-manager needed, mirrors
+``GET /research/desk/universe``'s own single-synchronous-read shape) and the desk bar top-up's
+three compute-manager routes (``POST``/``GET /research/desk/topup/compute``,
+``POST /research/desk/topup/compute/cancel`` — mirrors ``routes.py``'s
+``/edge-report/compute`` trio verbatim). Kept as its own module (mirroring the plan's stated
+preference) rather than folding into ``routes.py``, which is already large; mounted separately in
+``app/main.py``.
+
+**The top-up manager is a module-level singleton here, NOT a ``ResearchRegistry`` property.**
+``DeskTopupComputeManager`` (``desk_topup_compute.py``) reuses ``routes.record_bar_series``
+in-process, so it must import FROM ``routes.py`` — if ``ResearchRegistry`` held the manager (the
+``EdgeReportComputeManager`` precedent), ``routes.py`` would need to import IT back, a circular
+import. ``get_desk_topup_manager`` is a FastAPI dependency instead (the ``get_universe_fetcher``
+seam), test-overridable via ``app.dependency_overrides`` exactly like every other store/seam in
+this module."""
 
 from __future__ import annotations
 
@@ -17,6 +30,10 @@ from typing import Callable
 from fastapi import APIRouter, Depends, HTTPException
 
 from ..config import CONFIG
+from .bar_index import BarIndex
+from .bars import BarStore
+from .desk_coverage import get_desk_coverage
+from .desk_topup_compute import DeskTopupComputeManager
 from .desk_universe import (
     UniverseAlreadyRegistered,
     UniverseFetchError,
@@ -25,9 +42,17 @@ from .desk_universe import (
     fetch_constituents_html,
     parse_constituents,
 )
+from .routes import ResearchRegistry, get_bar_index, get_bar_store, get_registry
 
 router = APIRouter(prefix="/research/desk", tags=["desk"])
 
+# The desk top-up compute manager — a process-wide singleton (constructed once at import time,
+# mirroring how ``EdgeReportComputeManager`` lives for the life of the process). Exposed only
+# through ``get_desk_topup_manager`` below so a test overrides it outright via
+# ``app.dependency_overrides`` for complete test-to-test isolation (the ``get_universe_fetcher``
+# pattern), rather than sharing in-flight job state across tests.
+_desk_topup_manager = DeskTopupComputeManager()
+
 
 def get_universe_store() -> UniverseStore:
     """The universe store rooted at the config-owned directory (``TAPEOLOGY_DESK_UNIVERSE_DIR``
@@ -101,3 +126,75 @@ def get_universe(store: UniverseStore = Depends(get_universe_store)) -> dict:
     records, errors = store.list()
     latest = records[-1] if records else None
     return {"snapshots": records, "latest": latest, "integrity_errors": errors}
+
+
+# --- Coverage (J-02) --------------------------------------------------------------------------
+# A single synchronous read — no compute-manager needed (unlike the top-up below): coverage is
+# always index-fast (T-4), never a multi-second operation.
+
+
+@router.get("/coverage")
+def get_coverage(
+    store: UniverseStore = Depends(get_universe_store),
+    index: BarIndex = Depends(get_bar_index),
+) -> dict:
+    """Per-member x per-``DESK_TOPUP_TIMEFRAMES`` bar coverage for the LATEST universe snapshot,
+    read entirely from ``bar_index`` (T-4 — never re-hashes ``BarStore``). An explicit HTTP 200
+    honest-empty payload (``universe_snapshot_id: null``, ``members: []``) before any universe
+    snapshot exists — never a 404 (the ``GET /research/desk/universe`` convention). See
+    ``desk_coverage.get_desk_coverage`` for the exact shape."""
+    return get_desk_coverage(store, index)
+
+
+# --- The operator-run bar top-up (J-02) — three subpaths, mirrors ``routes.py``'s
+# ``/edge-report/compute`` trio (``routes.py:1268/1293/1302``) exactly: ``POST
+# /research/desk/topup/compute`` (single-flight trigger), ``GET /research/desk/topup/compute``
+# (poll the snapshot), ``POST /research/desk/topup/compute/cancel`` (409 when idle). ---------------
+
+
+def get_desk_topup_manager() -> DeskTopupComputeManager:
+    """The desk top-up compute manager — a FastAPI dependency (the ``get_universe_store``/
+    ``get_universe_fetcher`` pattern) so a test overrides it outright via
+    ``app.dependency_overrides`` for complete test-to-test isolation. The default resolves the
+    process-wide singleton constructed at module import time."""
+    return _desk_topup_manager
+
+
+@router.post("/topup/compute")
+def trigger_desk_topup_compute(
+    universe_store: UniverseStore = Depends(get_universe_store),
+    bar_store: BarStore = Depends(get_bar_store),
+    bar_index: BarIndex = Depends(get_bar_index),
+    registry: ResearchRegistry = Depends(get_registry),
+    manager: DeskTopupComputeManager = Depends(get_desk_topup_manager),
+) -> dict:
+    """Start the single-flight desk top-up job over the LATEST universe snapshot's members, or —
+    if one is already running — return it UNCHANGED (``started: False``, never a second concurrent
+    job). Returns ``{"started": bool, "compute": <snapshot>}``; the actual walk runs on a
+    background worker thread, off this request, so this route returns immediately regardless of
+    how long the top-up takes."""
+    return manager.trigger(universe_store, bar_store, bar_index, registry)
+
+
+@router.get("/topup/compute")
+def get_desk_topup_compute(
+    manager: DeskTopupComputeManager = Depends(get_desk_topup_manager),
+) -> dict | None:
+    """The top-up job's current/last snapshot, served VERBATIM — or ``null`` if no top-up has ever
+    run this process. A plain read: never triggers a compute as a side effect (GET-never-computes,
+    TC-10)."""
+    return manager.snapshot()
+
+
+@router.post("/topup/compute/cancel")
+def cancel_desk_topup_compute(
+    manager: DeskTopupComputeManager = Depends(get_desk_topup_manager),
+) -> dict:
+    """Cancel the in-flight desk top-up (cooperative — observed between pairs). ``409`` when idle
+    (no job has ever run, or the last job already reached a terminal state) — mirrors
+    ``cancel_edge_report_compute``'s own 409-when-terminal shape."""
+    snapshot = manager.snapshot()
+    if snapshot is None or snapshot["state"] != "running":
+        raise HTTPException(status_code=409, detail="no desk top-up compute is currently running")
+    manager.cancel()
+    return {"cancelling": True}
diff --git a/apps/backend/tests/test_bar_index.py b/apps/backend/tests/test_bar_index.py
index 605c0ed..24944ac 100644
--- a/apps/backend/tests/test_bar_index.py
+++ b/apps/backend/tests/test_bar_index.py
@@ -229,3 +229,70 @@ def test_reindex_after_deleting_the_db_file_reproduces_identical_lookups(tmp_pat
 
     after = {key: rebuilt.lookup(*key) for key in keys}
     assert after == before
+
+
+# --- coverage(): Era B "The Desk" J-02, additive ------------------------------------------------
+# Appended this iteration. Every assertion ABOVE this line is byte-unmodified from era-5 J-03 --
+# proving the extension took the "new accessor" path (goal-desk-iter-2 spec / plan), never a new
+# BarIndexHit field (which would have broken the positional/keyword BarIndexHit(...) construction
+# calls used throughout this file, e.g. line 62/153-156 above).
+
+
+def test_bar_index_hit_still_has_exactly_its_original_three_fields():
+    """A regression that added a field to ``BarIndexHit`` would break the equality assertions
+    above (``hit == BarIndexHit(series_id=..., checksum=..., bar_count=3)``,
+    ``BarIndexHit(pg["id"], pg["checksum"], 3)``) -- this pins the dataclass shape directly so
+    such a regression fails HERE, with a clear message, rather than as a confusing equality
+    mismatch elsewhere."""
+    import dataclasses
+
+    assert [f.name for f in dataclasses.fields(BarIndexHit)] == ["series_id", "checksum", "bar_count"]
+
+
+def test_coverage_on_an_empty_index_is_false_and_none(tmp_path):
+    index = BarIndex(str(tmp_path / "index.db"))
+    assert index.coverage("PG", "1d") == (False, None)
+
+
+def test_coverage_after_insert_is_true_and_the_recorded_window_end(tmp_path):
+    store = BarStore(tmp_path / "bars")
+    index = BarIndex(str(tmp_path / "index.db"))
+    meta = _record(store)
+    index.insert(meta)
+
+    assert index.coverage("PG", "1d") == (True, WINDOW_END)
+    assert index.coverage("PG", "1h") == (False, None)  # a different timeframe is unaffected
+    assert index.coverage("F", "1d") == (False, None)  # a different symbol is unaffected
+
+
+def test_coverage_reports_the_max_window_end_across_multiple_recordings(tmp_path):
+    """A symbol/timeframe recorded twice (e.g. an earlier top-up, then a later one) reports the
+    MOST RECENT ``window_end_utc`` -- never the first, never an arbitrary row."""
+    store = BarStore(tmp_path / "bars")
+    index = BarIndex(str(tmp_path / "index.db"))
+    first = _record(store, start=WINDOW_START, end=WINDOW_END)
+    index.insert(first)
+
+    later_start, later_end = "2026-06-05T00:00:00Z", "2026-06-08T00:00:00Z"
+    extra = _bar(
+        "PG", "1d", datetime(2026, 6, 5, tzinfo=timezone.utc).timestamp(), 151.0, 152.0, 150.5, 151.5, 800_000
+    )
+    second = store.record(
+        symbol="PG", timeframe="1d", window_start_utc=later_start, window_end_utc=later_end,
+        feed="yahoo", bars=_small_series("PG") + [extra],
+    )
+    index.insert(second)
+
+    assert index.coverage("PG", "1d") == (True, later_end)
+
+
+def test_coverage_reads_the_raw_iso_string_not_a_parsed_epoch(tmp_path):
+    """Mirrors ``test_lookup_matches_the_raw_iso_string_not_the_parsed_epoch`` above: ``coverage``
+    reports whatever ``window_end_utc`` string was actually stored, verbatim -- never reformatted
+    or re-derived from an epoch."""
+    store = BarStore(tmp_path / "bars")
+    index = BarIndex(str(tmp_path / "index.db"))
+    meta = _record(store, start="2026-06-01T00:00:00Z", end="2026-06-04T00:00:00.000000Z")
+    index.insert(meta)
+
+    assert index.coverage("PG", "1d") == (True, "2026-06-04T00:00:00.000000Z")
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-desk/telemetry.jsonl   | 6 ++++++
 runs/goal-session-desk/trace/trace.jsonl | 3 +++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
