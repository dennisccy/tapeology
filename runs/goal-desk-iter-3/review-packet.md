# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 1. Shown in full: 1.

```diff
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 0878d09..411be36 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -1,38 +1,50 @@
-"""``/research/desk/*`` — Era B "The Desk" (J-01 + J-02): universe ingestion, coverage, and the
-bar top-up.
+"""``/research/desk/*`` — Era B "The Desk" (J-01 + J-02 + J-03): universe ingestion, coverage, the
+bar top-up, and the screen.
 
 J-01 (unmodified this iteration): two routes over the universe subsystem (``desk_universe.py``) —
 ``POST /research/desk/universe/fetch`` (the explicit operator research action: fetch -> parse ->
 validate -> register) and ``GET /research/desk/universe`` (snapshot list + latest membership,
 honestly empty before any registration — never 404).
 
-J-02 (this iteration) adds two more concepts under the SAME router: ``GET /research/desk/coverage``
-(a pure read, ``desk_coverage.get_desk_coverage`` — no compute-manager needed, mirrors
-``GET /research/desk/universe``'s own single-synchronous-read shape) and the desk bar top-up's
-three compute-manager routes (``POST``/``GET /research/desk/topup/compute``,
-``POST /research/desk/topup/compute/cancel`` — mirrors ``routes.py``'s
-``/edge-report/compute`` trio verbatim). Kept as its own module (mirroring the plan's stated
-preference) rather than folding into ``routes.py``, which is already large; mounted separately in
-``app/main.py``.
-
-**The top-up manager is a module-level singleton here, NOT a ``ResearchRegistry`` property.**
+J-02 (unmodified this iteration) adds two more concepts under the SAME router:
+``GET /research/desk/coverage`` (a pure read, ``desk_coverage.get_desk_coverage`` — no
+compute-manager needed, mirrors ``GET /research/desk/universe``'s own single-synchronous-read
+shape) and the desk bar top-up's three compute-manager routes (``POST``/``GET
+/research/desk/topup/compute``, ``POST /research/desk/topup/compute/cancel`` — mirrors
+``routes.py``'s ``/edge-report/compute`` trio verbatim).
+
+J-03 (this iteration) adds the screen: ``GET /research/desk/screen`` (latest + ``?date=`` + a
+lightweight meta-only snapshot list — never full ``rows``/``skipped`` for every historical
+snapshot, see ``desk_screen.py``'s module docstring) and the screen's own three compute-manager
+routes (``POST``/``GET /research/desk/screen/compute``, ``POST
+/research/desk/screen/compute/cancel`` — mirrors the top-up trio exactly). Kept as its own module
+(mirroring the plan's stated preference) rather than folding into ``routes.py``, which is already
+large; mounted separately in ``app/main.py``.
+
+**Both compute managers are module-level singletons here, NOT ``ResearchRegistry`` properties.**
 ``DeskTopupComputeManager`` (``desk_topup_compute.py``) reuses ``routes.record_bar_series``
 in-process, so it must import FROM ``routes.py`` — if ``ResearchRegistry`` held the manager (the
 ``EdgeReportComputeManager`` precedent), ``routes.py`` would need to import IT back, a circular
-import. ``get_desk_topup_manager`` is a FastAPI dependency instead (the ``get_universe_fetcher``
-seam), test-overridable via ``app.dependency_overrides`` exactly like every other store/seam in
-this module."""
+import. ``DeskScreenComputeManager`` (``desk_screen_compute.py``) has no such constraint (it needs
+nothing from ``routes.py``), but is placed here anyway for consistency with its sibling — there is
+no functional reason to prefer the registry either. Both are FastAPI dependencies instead (the
+``get_universe_fetcher`` seam), test-overridable via ``app.dependency_overrides`` exactly like
+every other store/seam in this module."""
 
 from __future__ import annotations
 
 from typing import Callable
 
 from fastapi import APIRouter, Depends, HTTPException
+from pydantic import BaseModel
 
 from ..config import CONFIG
 from .bar_index import BarIndex
 from .bars import BarStore
+from .datasets import DatasetStore
 from .desk_coverage import get_desk_coverage
+from .desk_screen import ScreenStore, resolve_desk_screen_dir
+from .desk_screen_compute import DeskScreenComputeManager
 from .desk_topup_compute import DeskTopupComputeManager
 from .desk_universe import (
     UniverseAlreadyRegistered,
@@ -42,7 +54,7 @@ from .desk_universe import (
     fetch_constituents_html,
     parse_constituents,
 )
-from .routes import ResearchRegistry, get_bar_index, get_bar_store, get_registry
+from .routes import ResearchRegistry, get_bar_index, get_bar_store, get_dataset_store, get_registry
 
 router = APIRouter(prefix="/research/desk", tags=["desk"])
 
@@ -53,6 +65,10 @@ router = APIRouter(prefix="/research/desk", tags=["desk"])
 # pattern), rather than sharing in-flight job state across tests.
 _desk_topup_manager = DeskTopupComputeManager()
 
+# The desk screen compute manager (J-03) — the SAME process-wide-singleton-behind-a-dependency
+# shape as ``_desk_topup_manager`` immediately above.
+_desk_screen_compute_manager = DeskScreenComputeManager()
+
 
 def get_universe_store() -> UniverseStore:
     """The universe store rooted at the config-owned directory (``TAPEOLOGY_DESK_UNIVERSE_DIR``
@@ -198,3 +214,112 @@ def cancel_desk_topup_compute(
         raise HTTPException(status_code=409, detail="no desk top-up compute is currently running")
     manager.cancel()
     return {"cancelling": True}
+
+
+# --- The screen (J-03) — GET (latest / ?date= / meta-only list) plus the screen compute's three
+# subpaths, mirroring the top-up trio above exactly. ------------------------------------------------
+
+
+def get_screen_store() -> ScreenStore:
+    """The screen store rooted at a bare env-var-or-sibling-of-the-universe-dir default (zero new
+    ``Config`` field — see ``desk_screen.resolve_desk_screen_dir``) — the ``get_universe_store``
+    pattern. A FastAPI dependency so tests can point it at a temp dir via the env var or override
+    it outright."""
+    return ScreenStore(resolve_desk_screen_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+def _screen_meta_only(record: dict) -> dict:
+    """The lightweight projection ``GET /research/desk/screen``'s bulk list serves — id/pins/
+    counts only, NEVER the full ``rows``/``skipped`` arrays (see ``desk_screen.py``'s module
+    docstring: a screen snapshot is materially larger than a universe snapshot, so returning full
+    content for every historical snapshot in one list call risks the era-5C latency mistake)."""
+    return {
+        "id": record["id"],
+        "screen_date": record["screen_date"],
+        "as_of": record["as_of"],
+        "universe_snapshot_id": record["universe_snapshot_id"],
+        "config_fingerprint": record["config_fingerprint"],
+        "bar_store_signature": record["bar_store_signature"],
+        "created_utc": record["created_utc"],
+        "counts": {"rows": len(record["rows"]), "skipped": len(record["skipped"])},
+    }
+
+
+@router.get("/screen")
+def get_screen(date: str | None = None, store: ScreenStore = Depends(get_screen_store)) -> dict:
+    """Two shapes, selected by whether ``?date=`` is given (Data Contract addition #1):
+
+      * no ``date``: ``{"screens": [...meta-only...], "latest": <full snapshot>|null,
+        "integrity_errors": [...]}`` — an explicit HTTP 200 honest-empty payload
+        (``{"screens": [], "latest": null, "integrity_errors": []}``) before any screen has ever
+        been computed, never a 404 (the ``GET /research/desk/universe`` convention).
+      * ``date=YYYY-MM-DD``: ``{"screen": <the exact persisted snapshot for the latest recording
+        on that date, verbatim>|null}`` — a plain read, NEVER recomputed on the GET (TC-6)."""
+    records, errors = store.list()
+    if date is not None:
+        matching = [r for r in records if r["screen_date"] == date]
+        return {"screen": matching[-1] if matching else None}
+    return {
+        "screens": [_screen_meta_only(r) for r in records],
+        "latest": records[-1] if records else None,
+        "integrity_errors": errors,
+    }
+
+
+class ScreenComputeRequest(BaseModel):
+    """Body for ``POST /research/desk/screen/compute`` — ``screen_date`` is REQUIRED (FastAPI 422s
+    a missing/absent body before the route handler runs, TC-9); this endpoint never defaults to
+    the current wall-clock date (T-6)."""
+
+    screen_date: str
+
+
+def get_desk_screen_compute_manager() -> DeskScreenComputeManager:
+    """The desk screen compute manager — a FastAPI dependency (the ``get_desk_topup_manager``
+    pattern) so a test overrides it outright via ``app.dependency_overrides`` for complete
+    test-to-test isolation. The default resolves the process-wide singleton constructed at module
+    import time."""
+    return _desk_screen_compute_manager
+
+
+@router.post("/screen/compute")
+def trigger_desk_screen_compute(
+    body: ScreenComputeRequest,
+    universe_store: UniverseStore = Depends(get_universe_store),
+    bar_store: BarStore = Depends(get_bar_store),
+    bar_index: BarIndex = Depends(get_bar_index),
+    dataset_store: DatasetStore = Depends(get_dataset_store),
+    screen_store: ScreenStore = Depends(get_screen_store),
+    manager: DeskScreenComputeManager = Depends(get_desk_screen_compute_manager),
+) -> dict:
+    """Start the single-flight desk screen compute job for ``body.screen_date``, or — if one is
+    already running — return it UNCHANGED (``started: False``, never a second concurrent job).
+    Returns ``{"started": bool, "compute": <snapshot>}``; the actual walk runs on a background
+    worker thread, off this request, so this route returns immediately."""
+    return manager.trigger(
+        body.screen_date, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store,
+    )
+
+
+@router.get("/screen/compute")
+def get_desk_screen_compute(
+    manager: DeskScreenComputeManager = Depends(get_desk_screen_compute_manager),
+) -> dict | None:
+    """The screen compute job's current/last snapshot, served VERBATIM — or ``null`` if no screen
+    compute has ever run this process. A plain read: never triggers a compute as a side effect
+    (GET-never-computes)."""
+    return manager.snapshot()
+
+
+@router.post("/screen/compute/cancel")
+def cancel_desk_screen_compute(
+    manager: DeskScreenComputeManager = Depends(get_desk_screen_compute_manager),
+) -> dict:
+    """Cancel the in-flight desk screen compute (cooperative — observed between members). ``409``
+    when idle (no job has ever run, or the last job already reached a terminal state) — mirrors
+    ``cancel_desk_topup_compute``'s own 409-when-terminal shape."""
+    snapshot = manager.snapshot()
+    if snapshot is None or snapshot["state"] != "running":
+        raise HTTPException(status_code=409, detail="no desk screen compute is currently running")
+    manager.cancel()
+    return {"cancelling": True}
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-desk/telemetry.jsonl   | 6 ++++++
 runs/goal-session-desk/trace/trace.jsonl | 3 +++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
