# Iteration diff (bounded)

Files changed: 8. Shown in full: 3.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/desk_screen.py` (95 lines not shown)
- `apps/backend/tests/fixtures/yahoo/MSFT_1d_20260101_20260626.json` (575 lines not shown)
- `apps/backend/tests/fixtures/yahoo/MSFT_1h_20260601_20260618.json` (391 lines not shown)
- `apps/backend/tests/test_desk_screen.py` (256 lines not shown)
- `apps/backend/tests/test_desk_screen_compute.py` (199 lines not shown)

```diff
diff --git a/README.md b/README.md
index 21c7d5e..880fac2 100644
--- a/README.md
+++ b/README.md
@@ -61,7 +61,8 @@ Current capabilities:
 - **Operator-run edge report compute** — beneath the "Edge report not computed yet." message, a "Compute edge report" button starts the full three-strategy comparison as a background job without leaving the page. While it runs, a live counter shows how many of the comparison's individual backtests have finished so far — including how many were reused from already-completed work rather than recomputed — updating automatically with no manual refresh needed. When the computation completes, the finished report renders in place automatically, using the same table already shown for a previously-computed report. If the computation fails partway through, the panel shows the specific error message instead of a generic failure, and the button relabels itself so a fresh attempt is one more click away. Reloading the page, or landing on it, while a compute is running, or after one has already finished or failed, immediately shows the matching state rather than resetting to idle. A compute that is interrupted — by a server restart, a crash, or a cancellation — resumes cleanly when re-triggered: it skips every result already durably saved and computes only what's left, finishing far faster than starting over. The same computation can also be started, unattended, from the command line for long background runs, where it can be spread across several worker processes at once for a further speedup; the on-page button always runs single-process by design.
 - **Cockpit price-chart tradable bands and a descriptive confluence chip** — the tradable support/resistance bands from the Structure page's map now also draw directly on the live cockpit price chart while watching a symbol in Simulated or Historical mode: one or two solid price lines per band (rose for resistance, emerald for support), each labeled with side, class, quality score, and whether it sits on a round number — alongside the existing tape-state markers, without changing how those render. A small descriptive banner appears beneath the chart only when the last traded price sits inside one of those bands AND the live tape reading matches that band's configured rejection-or-breakthrough state — for example "Inside R-band 300.05–300.17 (class A) · tape: Ask Absorption (rejection) · measured history: edge report." The banner states the current condition and points to the edge report as measured history; it never tells you to buy or sell and never predicts an outcome. A simulated ticker with no real recorded price history shows an honest "No tradable map for TICKER" note instead of a fabricated band. Live mode is unchanged — the price chart, and therefore the bands and banner, stay hidden there exactly as before.
 - **S&P 100 universe snapshot fetch and registry (research API)** — on explicit request, fetch the current S&P 100 constituent list from a public source (Wikipedia) and validate it (a real company-symbol table, roughly 90–110 names, no garbled entries), refusing with a specific explanation on any anomaly rather than guessing or saving a partial list. A valid fetch is saved as a permanent, checksummed, dated snapshot; fetching identical membership again is recognized and refused rather than silently duplicated or overwritten. Dual-class tickers are normalized for use elsewhere in the app (for example `BRK.B` → `BRK-B`) while the original source form is kept in the snapshot's own record. A second call lists every saved snapshot and returns the most recent membership, honestly reporting that nothing has been fetched yet before the first run. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
-- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `GET /research/taxonomy`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/bars/{id}/candles`, `GET /research/candles`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `POST /research/desk/universe/fetch`, `GET /research/desk/universe`, `GET /meta/ui-routes`.
+- **Bar coverage check and resumable top-up over the universe (research API + command-line tool)** — for every member of the most recently registered S&P 100 universe snapshot, see instantly — read from a lookup index, never by re-scanning the underlying bar files — whether hourly, 4-hour, daily, and weekly price bars are already on file and how fresh each one is. A single operator-triggered job then walks every member of that universe and fills in whichever of those four windows are missing, reusing the exact same fetch-and-record path a single manual bar request already uses, so behavior is identical; it reports live progress per symbol/timeframe (newly fetched, already on file, or failed), can be cancelled mid-run, and safely resumes without re-downloading anything already recorded. A command-line version runs the same job unattended for a real, full pass over the whole universe. There is no browser page for this yet; the coverage check and the top-up job are both reachable through the research API, and the top-up job also from the command line.
+- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `GET /research/taxonomy`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/bars/{id}/candles`, `GET /research/candles`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `POST /research/desk/universe/fetch`, `GET /research/desk/universe`, `GET /research/desk/coverage`, `POST /research/desk/topup/compute`, `GET /research/desk/topup/compute`, `POST /research/desk/topup/compute/cancel`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, and navigation data the REST API serves. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
 
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
diff --git a/apps/backend/app/research/desk_screen.py b/apps/backend/app/research/desk_screen.py
new file mode 100644
index 0000000..55ac2e1
--- /dev/null
+++ b/apps/backend/app/research/desk_screen.py
@@ -0,0 +1,489 @@
+"""The screen: pinned inputs, append-only snapshot, deterministic rank (Era B "The Desk", Key
+Capability 3, J-03) -- the Data Contract's "Screen snapshots, rank rows, skip rows" row's ONE
+owner, served by ``GET /research/desk/screen``.
+
+THIS MODULE computes NOTHING about tradable structure itself -- it is a pure ORCHESTRATION lens
+over three already-canonical owners: ``compute_tradability`` (``tradability.py:381`` -- bands,
+class, quality score, verbatim), ``desk_coverage.get_desk_coverage`` (per-member coverage badge,
+verbatim reuse -- also the source of ``bar_store_signature``, see below), and ``DatasetStore.list``
+(tick-evidence presence, verbatim). Two new desk-owned values are computed HERE and only here:
+``distance_bps`` (a plain arithmetic derivation from a band's own edge price and a reference close
+this module resolves) and the cross-symbol rank order.
+
+**The append-only store** (``ScreenStore``) mirrors ``desk_universe.UniverseStore``'s discipline
+exactly: a checksum-verified load on every read, ``record`` as the only mutation, no update/delete
+function anywhere (immutability is structural, not policed). UNLIKE the universe store (which dedups
+on parsed CONTENT), a screen dedups on its own 5-pin KEY -- ``(screen_date, as_of,
+universe_snapshot_id, config_fingerprint, bar_store_signature)`` -- because the key alone
+deterministically determines the content (the row computation is a pure function of those five
+pins), so keying on the pins is equivalent to keying on content while being resolvable BEFORE the
+(potentially ~100-member) walk ever runs.
+
+**``as_of`` translation (T-6, goal-desk-iter-3 NOTES).** ``as_of`` is a deterministic function of
+the operator-given ``screen_date`` alone -- ``f"{screen_date}T23:59:59Z"`` -- reusing ``/structure``'s
+own plain-date convention rather than inventing a new one. ``compute_tradability``'s basis
+resolution is a CALENDAR-DATE comparison, so any ``as_of`` inside ``screen_date``'s own UTC day
+resolves the identical prior-session basis -- never ``datetime.now()``.
+
+**``bar_store_signature`` (T-4, TC-15).** A checksum over the sorted ``(symbol, timeframe,
+latest_window_end_utc)`` tuples read ENTIRELY from ``desk_coverage.get_desk_coverage``'s own
+per-member x per-timeframe output (already ``bar_index``-backed, already proven index-fast in J-02)
+-- never a ``BarStore``/JSON-file re-hash (the era-5C 31.4s mistake T-4 exists to prevent).
+``_bar_store_signature`` below takes the ALREADY-fetched coverage payload and touches no store at
+all, so it is structurally incapable of issuing a ``BarStore`` call.
+
+**Reference close price (TC-19).** ``compute_tradability``/``compute_levels`` serve no
+``current_price``/close field (adding one would break their existing exact-dict-equality tests --
+a "Frozen foundations" violation), so this module resolves it itself: the ONE daily bar in
+``BarStore.merged_bars(symbol, "1d")`` whose OWN timestamp matches ``basis_as_of`` verbatim (a
+value ``compute_tradability`` already returns) -- comparing via the SAME ISO-formatting function on
+both sides (never parsing ``basis_as_of`` back to a float, which would risk a microsecond
+round-trip mismatch). Never re-deriving WHICH bar is the basis; never touching ``tradability.py``'s
+or ``levels.py``'s return shape.
+
+**Best-band selection + cross-symbol rank (assumptions.md iter-3, entry 1).** Per symbol, the
+"best" band minimizes ``(class rank A=3/B=2/C=1/null=0 -- DESCENDING preference, distance_bps
+ascending, quality_score descending)``, iterating ``compute_tradability``'s own already-deterministic
+served band order so an exact tie resolves identically every run (Python's ``min`` keeps the FIRST
+of equal-key items). The SAME tuple, plus ``symbol`` ascending as the final tie-break, orders the
+screen's final ``rows`` list (TC-14) -- one rule serves both jobs.
+
+**Skip reasons -- exactly two, never conflated.** ``"no_bars"`` = ``compute_tradability``'s own
+``no_bar_series_for_symbol: true``; ``"no_basis"`` = a daily series exists but no session resolves
+(``basis_as_of: null``, ``bands: []``). Both honest, distinct absences -- a skip row's ``coverage``
+still reflects whichever pinned timeframes genuinely have bars (never a fabricated all-false).
+
+**No new ``Config`` field.** The screen store's directory resolves via ``resolve_desk_screen_dir``
+below -- a bare ``TAPEOLOGY_DESK_SCREEN_DIR``-env-var-or-sibling-of-``desk_universe_dir_resolved()``
+default (the ``edge_report_cache.resolve_cache_db_path`` pattern) -- never a ``desk_screen_dir``
+``Config`` field. This keeps ``config_fingerprint()`` untouched this iteration.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Callable
+
+from ..config import Config
+from .bar_index import BarIndex
+from .bars import BarStore
+from .datasets import DatasetStore
+from .desk_coverage import DESK_TOPUP_TIMEFRAMES, get_desk_coverage
+from .desk_universe import UniverseStore
+from .tradability import compute_tradability
+
+# The two band sides `compute_tradability` serves. Only `RESISTANCE` is referenced by name below
+# (`_distance_bps` treats anything else as the support case) -- no `SUPPORT` constant is defined
+# since nothing in this module ever compares against it.
+RESISTANCE = "resistance"
+
+# Class rank for both the within-symbol "best band" selection and the cross-symbol final rank
+# (assumptions.md iter-3 entry 1) -- a band with no inherited class ranks lowest, never highest
+# (an honest absence is never preferred over a graded band).
+_CLASS_RANK: dict[str | None, int] = {"A": 3, "B": 2, "C": 1, None: 0}
+
+# The screen store's own env-var override (the ``TAPEOLOGY_DESK_UNIVERSE_DIR``/
+# ``TAPEOLOGY_EDGE_REPORT_CACHE_DB`` pattern) -- see ``resolve_desk_screen_dir``.
+_SCREEN_DIR_ENV = "TAPEOLOGY_DESK_SCREEN_DIR"
+
+
+class ScreenIntegrityError(Exception):
+    """An on-disk screen snapshot file failed its checksum verification on load -- corrupted or
+    tampered, surfaced explicitly (never silence, never a fabricated snapshot)."""
+
+
+class ScreenAlreadyRecorded(Exception):
+    """A screen with this EXACT 5-pin key (``screen_date``, ``as_of``, ``universe_snapshot_id``,
+    ``config_fingerprint``, ``bar_store_signature``) is already registered. Screen snapshots are
+    immutable and append-only -- there is no update/re-record path anywhere in this module; a new
+    run under the identical pins reuses the existing snapshot, never a second file."""
+
+    def __init__(self, existing_id: str) -> None:
+        self.existing_id = existing_id
+        super().__init__(
+            f"a screen with this exact key is already recorded as snapshot '{existing_id}' "
+            f"-- screen snapshots are immutable and are never re-recorded"
+        )
+
+
+def resolve_desk_screen_dir(desk_universe_dir_resolved: str) -> str:
+    """The screen store's directory: the ``TAPEOLOGY_DESK_SCREEN_DIR`` env var if set, else a file
+    co-located as a SIBLING of the CALLER's own already-resolved universe directory (the
+    ``edge_report_cache.resolve_cache_db_path`` pattern -- takes a plain string, never imports
+    ``config.py``'s singleton, so the caller resolves its own universe directory first exactly as
+    ``desk_routes.py`` already does). Deliberately NOT a ``desk_screen_dir`` Config field (see the
+    module docstring) -- this is an operational storage-location knob, the Constraints' own
+    explicit sanction for "worker counts, timeouts, store dirs"."""
+    override = os.environ.get(_SCREEN_DIR_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "screen")
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding every checksum in this module hashes (stable across
+    processes: sorted keys, no whitespace) -- the SAME encoding ``research/desk_universe.py`` /
+    ``research/bars.py`` hash."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _iso_utc_now() -> str:
+    return (
+        datetime.now(timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _iso(epoch: float) -> str:
+    """The SAME epoch -> ISO formatting ``tradability.py``'s own ``_iso`` uses -- kept as a local
+    copy (this project's own convention: each module owns its tiny formatting helper rather than
+    sharing one -- see ``bars.py._iso_utc``, ``desk_universe.py._iso_utc_now``) so a reference
+    close is matched by comparing ISO strings on BOTH sides, never by parsing ``basis_as_of`` back
+    to a float (which would risk a microsecond round-trip mismatch)."""
+    return (
+        datetime.fromtimestamp(epoch, tz=timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _epoch(iso: str) -> float:
+    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
+
+
+def screen_as_of(screen_date: str) -> str:
+    """T-6: ``as_of`` is a deterministic function of ``screen_date`` ALONE, never
+    ``datetime.now()`` -- see the module docstring's "as_of translation" section."""
+    return f"{screen_date}T23:59:59Z"
+
+
+# --- bar_store_signature (T-4, TC-15) ------------------------------------------------------------
+
+
+def _bar_store_signature(coverage: dict) -> str:
+    """T-4: a checksum over the sorted ``(symbol, timeframe, latest_window_end_utc)`` tuples,
+    derived ENTIRELY from an ALREADY-FETCHED ``desk_coverage.get_desk_coverage`` payload -- this
+    function receives no store reference of any kind, so it is structurally incapable of issuing a
+    ``BarStore`` call (TC-15)."""
+    tuples = sorted(
+        (member["symbol"], timeframe, member["per_timeframe"][timeframe]["latest_window_end_utc"])
+        for member in coverage["members"]
+        for timeframe in DESK_TOPUP_TIMEFRAMES
+    )
+    return _sha256(_canonical(tuples))[:16]
+
+
+def compute_bar_store_signature(universe_store: UniverseStore, bar_index: BarIndex) -> str:
+    """The standalone accessor: fetches coverage (index-only, T-4) and derives the signature from
+    it. Exposed separately from ``compute_screen`` so a caller (or a test) can resolve the 5-pin
+    key's ``bar_store_signature`` component WITHOUT running the full per-member walk -- the SAME
+    cheap-resolution property ``DeskTopupComputeManager.trigger`` already relies on for
+    ``pairs_total`` (known synchronously, before any background work starts)."""
+    return _bar_store_signature(get_desk_coverage(universe_store, bar_index))
+
+
+# --- best-band selection + distance_bps (assumptions.md iter-3, entry 1) -------------------------
+
+
+def _distance_bps(band: dict, close: float) -> float:
+    """``abs(edge_price - close) / close * 10000``, where ``edge_price`` is the near edge to price
+    -- ``price_low`` for a resistance band (support from below), ``price_high`` for a support band
+    (resistance from above). Correct by construction: ``compute_tradability``'s own side split
+    already guarantees ``price_low``/``price_high`` are the closest member on the relevant side."""
+    edge_price = band["price_low"] if band["side"] == RESISTANCE else band["price_high"]
+    return abs(edge_price - close) / close * 10_000.0
+
+
+def _select_best_band(bands: list[dict], close: float) -> dict:
+    """The symbol's single "best" band: minimizes ``(class rank DESCENDING preference, distance_bps
+    ascending, quality_score descending)`` over ``bands`` in ``compute_tradability``'s own served
+    order -- ``min`` returns the FIRST of any exactly-tied items, so a tie resolves identically
+    every run without a second, invented tie-break."""
+
+    def key(band: dict) -> tuple[int, float, float]:
+        return (-_CLASS_RANK[band["class"]], _distance_bps(band, close), -band["quality_score"])
+
+    return min(bands, key=key)
+
+
+def _row_rank_key(row: dict) -> tuple[int, float, float, str]:
+    """The FINAL cross-symbol ``rows`` order (TC-14): the identical selection tuple above, plus
+    ``symbol`` ascending as the final tie-break."""
+    return (-_CLASS_RANK[row["band_class"]], row["distance_bps"], -row["band_score"], row["symbol"])
+
+
+# --- reference close price (TC-19) ----------------------------------------------------------------
+
+
+def _resolve_reference_close(store: BarStore, symbol: str, basis_as_of: str) -> float:
+    """The ONE daily bar in ``store.merged_bars(symbol, "1d")`` whose own timestamp -- formatted
+    through the SAME ``_iso`` function ``tradability.py`` uses -- matches ``basis_as_of`` verbatim.
+    Never re-derives WHICH bar is the basis (that stays ``compute_tradability``'s exclusive
+    decision); never touches ``tradability.py``'s or ``levels.py``'s return shape.
+
+    Structurally this bar always exists: ``basis_as_of`` is itself derived from a bar
+    ``compute_tradability`` read via this EXACT accessor (``tradability.py``'s own
+    ``_select_daily_series`` calls ``BarStore.merged_bars(symbol, "1d")``), and the store is
+    immutable between the two reads within one screen computation -- a missing match is an
+    unreachable internal-invariant failure, surfaced loudly (never a fabricated close)."""
+    for bar in store.merged_bars(symbol, "1d"):
+        if _iso(bar.epoch) == basis_as_of:
+            return bar.close
+    raise RuntimeError(
+        f"internal invariant violated: no daily bar for {symbol!r} matches basis_as_of "
+        f"{basis_as_of!r} -- compute_tradability's own basis bar must always be present in "
+        f"merged_bars(symbol, '1d')"
+    )
+
+
+# --- the row computation (the SOLE walker; the manager and the CLI both call this) ----------------
+
+
+def compute_screen(
+    universe_store: UniverseStore,
+    bar_store: BarStore,
+    bar_index: BarIndex,
+    dataset_store: DatasetStore,
+    config: Config,
+    screen_date: str,
+    *,
+    progress: Callable[[dict], None] | None = None,
+    should_abort: Callable[[], bool] | None = None,
+) -> dict:
+    """Walk the LATEST universe snapshot's members, as of ``screen_date``'s session close,
+    computing one ranked row (or an honest skip) per member via the canonical owners
+    (``compute_tradability``, ``desk_coverage.get_desk_coverage``, ``DatasetStore.list``). Returns
+    the full snapshot content MINUS the store-assigned ``id``/``created_utc`` (``ScreenStore.record``
+    assigns those): ``{screen_date, as_of, universe_snapshot_id, config_fingerprint,
+    bar_store_signature, rows, skipped}``.
+
+    ``progress``, if given, is called after EACH member with ``{"symbol": symbol}`` (the caller
+    tracks its own done/total counters -- the ``desk_topup_compute.run_topup`` precedent).
+    ``should_abort``, if given and it returns ``True`` before a member starts, stops the walk early
+    -- ``rows``/``skipped`` are simply shorter than the full member list; a cooperative stop, never
+    a raise. No universe snapshot registered yet -> an honest empty walk (``universe_snapshot_id``
+    is ``None``, both lists empty) -- never an error."""
+    as_of = screen_as_of(screen_date)
+    as_of_epoch = _epoch(as_of)
+
+    universe_records, _universe_errors = universe_store.list()
+    universe_snapshot_id = universe_records[-1]["id"] if universe_records else None
+    members = list(universe_records[-1]["members"]) if universe_records else []
+
+    coverage_payload = get_desk_coverage(universe_store, bar_index)
+    coverage_by_symbol = {m["symbol"]: m["per_timeframe"] for m in coverage_payload["members"]}
+    bar_store_signature = _bar_store_signature(coverage_payload)
+
+    dataset_records, _dataset_errors = dataset_store.list()
+    tick_symbols = {meta["symbol"] for meta in dataset_records}
+
+    config_fingerprint = config.config_fingerprint()
+
+    rows: list[dict] = []
+    skipped: list[dict] = []
+    for symbol in members:
+        if should_abort is not None and should_abort():
+            break
+        coverage = coverage_by_symbol[symbol]
+        tick_evidence = symbol in tick_symbols
+        result = compute_tradability(bar_store, symbol, as_of_epoch, config)
+
+        if result["no_bar_series_for_symbol"]:
+            skipped.append(
+                {"symbol": symbol, "skipped": True, "reason": "no_bars",
+                 "coverage": coverage, "tick_evidence": tick_evidence}
+            )
+        elif result["basis_as_of"] is None:
+            skipped.append(
+                {"symbol": symbol, "skipped": True, "reason": "no_basis",
+                 "coverage": coverage, "tick_evidence": tick_evidence}
+            )
+        else:
+            close = _resolve_reference_close(bar_store, symbol, result["basis_as_of"])
+            best = _select_best_band(result["bands"], close)
+            rows.append(
+                {
+                    "symbol": symbol,
+                    "side": best["side"],
+                    "band_class": best["class"],
+                    "distance_bps": _distance_bps(best, close),
+                    "band_score": best["quality_score"],
+                    "price_low": best["price_low"],
+                    "price_high": best["price_high"],
+                    "coverage": coverage,
+                    "tick_evidence": tick_evidence,
+                }
+            )
+
+        if progress is not None:
+            progress({"symbol": symbol})
+
+    rows.sort(key=_row_rank_key)
+    # `skipped` is already symbol-ascending by construction (walked in `members`' own sorted
+    # order, per `desk_universe.UniverseStore.record`'s `sorted(normalized_to_raw)` -- never
+    # reordered here, so no redundant second sort is needed.
+
+    return {
+        "screen_date": screen_date,
+        "as_of": as_of,
+        "universe_snapshot_id": universe_snapshot_id,
+        "config_fingerprint": config_fingerprint,
+        "bar_store_signature": bar_store_signature,
+        "rows": rows,
+        "skipped": skipped,
+    }
+
+
+# --- the store (frozen JSON, one file per snapshot, structurally immutable) ----------------------
+
+
+class ScreenStore:
+    """File-based store rooted at the config-owned screen directory -- the ONE reader/writer.
+    Mirrors ``desk_universe.UniverseStore``'s discipline exactly: every load verifies a
+    whole-record checksum (``ScreenIntegrityError`` on any mismatch); the only mutation,
+    ``record``, refuses an identical 5-pin key (``ScreenAlreadyRecorded``, never a second file for
+    the same key); no update/delete function exists anywhere."""
+
+    def __init__(self, root: str | Path) -> None:
+        self._root = Path(root)
+
+    @property
+    def root(self) -> Path:
+        return self._root
+
+    def _path(self, screen_id: str) -> Path:
+        return self._root / f"{screen_id}.json"
+
+    def _load(self, path: Path) -> dict:
+        """Load ONE snapshot file, verifying its whole-record checksum. Raises
+        ``ScreenIntegrityError`` for any parse/shape/checksum failure -- explicit, never silent."""
+        try:
+            data = json.loads(path.read_text())
+        except (OSError, ValueError) as exc:
+            raise ScreenIntegrityError(
+                f"screen snapshot file '{path.name}' is not parseable ({exc}) -- corrupted or "
+                f"tampered"
+            ) from exc
+        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
+            raise ScreenIntegrityError(
+                f"screen snapshot file '{path.name}' does not carry the expected record shape -- "
+                f"corrupted or tampered"
+            )
+        record = data["record"]
+        if _sha256(_canonical(record)) != data["file_checksum"]:
+            raise ScreenIntegrityError(
+                f"screen snapshot file '{path.name}' failed its integrity check (checksum "
+                f"mismatch) -- the file was corrupted or tampered with"
+            )
+        meta = record.get("meta")
+        if not isinstance(meta, dict):
+            raise ScreenIntegrityError(
+                f"screen snapshot file '{path.name}' does not carry the expected record shape -- "
+                f"corrupted or tampered"
+            )
+        return meta
+
... [diff_bound] apps/backend/app/research/desk_screen.py: 95 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/app/research/desk_screen_compute.py b/apps/backend/app/research/desk_screen_compute.py
new file mode 100644
index 0000000..87bfa1e
--- /dev/null
+++ b/apps/backend/app/research/desk_screen_compute.py
@@ -0,0 +1,278 @@
+"""Era B "The Desk" (J-03) -- the desk screen compute manager: a single-flight, cancellable,
+progress-reporting background job around ``desk_screen.compute_screen`` (the SOLE row-computation
+walker; this module computes nothing about tradable structure itself), plus a CLI warmer that
+drives the SAME function synchronously, in-process, for a REQUIRED ``--date``.
+
+Mirrors ``desk_topup_compute.DeskTopupComputeManager``/``edge_report_compute.EdgeReportComputeManager``
+verbatim in shape: one in-flight job slot (``self._snapshot``), an in-memory, process-scoped
+progress snapshot (``id``/``state``/``screen_date``/``started_utc``/``finished_utc``/``error``/
+``progress``), cooperative cancel, an atomic snapshot publish under a lock (a fresh dict rebound in
+ONE assignment, never mutated in place). Job state is process-scoped bookkeeping -- honestly lost
+on restart, never a research value.
+
+**Unlike ``DeskTopupComputeManager``, this manager needs nothing from ``routes.py``** --
+``desk_screen.compute_screen`` reuses only ``tradability.py``/``desk_coverage.py``/``datasets.py``,
+none of which live in ``routes.py``. So there is no circular-import constraint forcing this off
+``ResearchRegistry`` -- it is STILL a module-level singleton behind a FastAPI dependency in
+``desk_routes.py`` (the ``get_desk_topup_manager`` pattern, for placement consistency with its
+sibling and full test-to-test isolation via ``app.dependency_overrides``), simply because there is
+no functional reason to prefer the registry either.
+
+**Append-only reuse, not a pre-compute skip.** ``trigger`` ALWAYS runs the full member walk (via
+``compute_screen``) rather than pre-checking the store before paying for it. ``compute_screen``
+calls ``compute_tradability`` DIRECTLY (never through the durable ``TradabilityCache``
+``GET /research/tradability`` uses -- this module has no reason to import from ``routes.py``, the
+module that owns that cache), so an identical-pin retrigger genuinely repeats the CPU work, not a
+cheap cache hit -- live-verified (see the dev handoff's "Known Issues"): a real ~100-member walk's
+first symbol can take several seconds, cold. This is a DELIBERATE, logged trade-off (not an
+oversight): the row content is a pure, deterministic function of the five pins (TC-10), so
+repeating the computation changes nothing observable, and the APPEND-ONLY guarantee (never a
+second file, never a rewrite) is enforced STRUCTURALLY by ``ScreenStore.record`` itself
+(``ScreenAlreadyRecorded``) regardless of whether the walk was "worth" repeating. No TC requires a
+hard "zero recompute calls on retrigger" proof (unlike TC-15's explicit ``BarStore``-call-counting
+for ``bar_store_signature``); a future iteration can add a cheap pre-check (the five pins resolve
+synchronously before the walk, the SAME way ``members_total`` already does) if a real retrigger's
+latency is ever measured to matter -- the same "measure first, optimize later" discipline
+``bars.py``/``datasets.py``'s own stat-keyed caches followed."""
+
+from __future__ import annotations
+
+import argparse
+import threading
+import uuid
+from datetime import datetime, timezone
+from typing import Callable
+
+from ..config import CONFIG, Config
+from .bar_index import BarIndex
+from .bars import BarStore
+from .datasets import DatasetStore
+from .desk_screen import ScreenAlreadyRecorded, ScreenStore, compute_screen, resolve_desk_screen_dir
+from .desk_universe import UniverseStore
+from .routes import get_bar_index, get_bar_store, get_dataset_store
+
+__all__ = ["DeskScreenComputeManager", "run_screen_and_record"]
+
+
+def _iso_utc_now() -> str:
+    return (
+        datetime.now(timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _copy_snapshot(snapshot: dict) -> dict:
+    """A caller-safe copy so a reader mutating what ``snapshot()`` returns can never poison
+    ``DeskScreenComputeManager``'s own internal state (the ``EdgeReportComputeManager._copy_snapshot``
+    precedent)."""
+    progress = snapshot["progress"]
+    return {**snapshot, "progress": dict(progress)}
+
+
+def run_screen_and_record(
+    universe_store: UniverseStore,
+    bar_store: BarStore,
+    bar_index: BarIndex,
+    dataset_store: DatasetStore,
+    config: Config,
+    screen_store: ScreenStore,
+    screen_date: str,
+    *,
+    progress: Callable[[dict], None] | None = None,
+    should_abort: Callable[[], bool] | None = None,
+) -> dict:
+    """Compute ONE screen (``compute_screen`` -- the sole walker) and persist it, append-only. If
+    an identical-pin screen is already recorded, the EXISTING snapshot's meta is returned (never a
+    second file, never a rewrite) rather than raising -- ``ScreenAlreadyRecorded`` is caught here,
+    not propagated, since reusing an already-recorded snapshot is a normal, expected outcome, not a
+    failure. A cancelled (partial) walk is NEVER recorded -- returns ``None`` instead (the caller
+    distinguishes "cancelled, nothing recorded" from "recorded/reused" by this ``None`` check)."""
+    result = compute_screen(
+        universe_store, bar_store, bar_index, dataset_store, config, screen_date,
+        progress=progress, should_abort=should_abort,
+    )
+    if should_abort is not None and should_abort():
+        return None
+    try:
+        return screen_store.record(
+            screen_date=result["screen_date"],
+            as_of=result["as_of"],
+            universe_snapshot_id=result["universe_snapshot_id"],
+            config_fingerprint=result["config_fingerprint"],
+            bar_store_signature=result["bar_store_signature"],
+            rows=result["rows"],
+            skipped=result["skipped"],
+        )
+    except ScreenAlreadyRecorded as exc:
+        existing = screen_store.find_by_key(
+            result["screen_date"], result["as_of"], result["universe_snapshot_id"],
+            result["config_fingerprint"], result["bar_store_signature"],
+        )
+        assert existing is not None and existing["id"] == exc.existing_id
+        return existing
+
+
+class DeskScreenComputeManager:
+    """Owns the SINGLE in-flight (or last-terminal) desk screen compute job. Construct with no
+    arguments -- every ``trigger()`` call takes its stores/config explicitly (the
+    ``EdgeReportComputeManager``/``DeskTopupComputeManager`` per-call-injection precedent)."""
+
+    def __init__(self) -> None:
+        self._lock = threading.Lock()
+        self._snapshot: dict | None = None
+        self._cancel_event: threading.Event | None = None
+        self._thread: threading.Thread | None = None
+
+    def snapshot(self) -> dict | None:
+        """The current/last job's snapshot, or ``None`` if none has ever run -- a caller-safe
+        copy, never a shared mutable reference."""
+        current = self._snapshot  # read-local-reference-before-inspect
+        if current is None:
+            return None
+        return _copy_snapshot(current)
+
+    def trigger(
+        self,
+        screen_date: str,
+        universe_store: UniverseStore,
+        bar_store: BarStore,
+        bar_index: BarIndex,
+        dataset_store: DatasetStore,
+        config: Config,
+        screen_store: ScreenStore,
+    ) -> dict:
+        """Start a NEW screen compute job for ``screen_date``, or -- if one is already
+        ``state == "running"`` -- return it UNCHANGED (``started: False``, single-flight, TC-7).
+        Once the current job is terminal (done/cancelled/failed, or none has ever run), the NEXT
+        call always starts a genuinely new job (a fresh id), discarding the prior snapshot. Never
+        blocks -- the walk runs on a dedicated worker thread, off the caller's thread, so an HTTP
+        route calling this returns immediately."""
+        with self._lock:
+            current = self._snapshot
+            if current is not None and current["state"] == "running":
+                return {"started": False, "compute": _copy_snapshot(current)}
+
+            records, _errors = universe_store.list()
+            members_total = len(records[-1]["members"]) if records else 0
+
+            job_id = uuid.uuid4().hex
+            cancel_event = threading.Event()
+            self._cancel_event = cancel_event
+            snapshot = {
+                "id": job_id,
+                "state": "running",
+                "screen_date": screen_date,
+                "started_utc": _iso_utc_now(),
+                "finished_utc": None,
+                "error": None,
+                "progress": {"members_total": members_total, "members_done": 0, "current": None},
+            }
+            self._snapshot = snapshot
+
+        def _publish(entry: dict) -> None:
+            with self._lock:
+                current = self._snapshot
+                if current is None or current["id"] != job_id:
+                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
+                progress = current["progress"]
+                self._snapshot = {
+                    **current,
+                    "progress": {
+                        **progress, "members_done": progress["members_done"] + 1,
+                        "current": entry["symbol"],
+                    },
+                }
+
+        def _work() -> None:
+            try:
+                run_screen_and_record(
+                    universe_store, bar_store, bar_index, dataset_store, config, screen_store,
+                    screen_date, progress=_publish, should_abort=cancel_event.is_set,
+                )
+            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
+                self._resolve(job_id, "failed", error=str(exc))
+                return
+            self._resolve(job_id, "cancelled" if cancel_event.is_set() else "done", error=None)
+
+        thread = threading.Thread(target=_work, name=f"desk-screen-compute:{job_id}", daemon=True)
+        with self._lock:
+            self._thread = thread
+        thread.start()
+        return {"started": True, "compute": _copy_snapshot(snapshot)}
+
+    def _resolve(self, job_id: str, state: str, *, error: str | None) -> None:
+        with self._lock:
+            current = self._snapshot
+            if current is None or current["id"] != job_id:
+                return  # superseded -- never resolve a job that is no longer the current one
+            self._snapshot = {**current, "state": state, "finished_utc": _iso_utc_now(), "error": error}
+
+    def cancel(self) -> None:
+        """Signal cooperative cancellation for the in-flight job -- a harmless no-op if idle (the
+        ROUTE is the one that rejects an idle cancel with a 409 -- see ``desk_routes.py``)."""
+        with self._lock:
+            cancel_event = self._cancel_event
+        if cancel_event is not None:
+            cancel_event.set()
+
+    def join_all(self, timeout: float = 30.0) -> None:
+        """Wait for the in-flight job thread, if any (test/shutdown hygiene -- the
+        ``EdgeReportComputeManager.join_all`` precedent)."""
+        with self._lock:
+            thread = self._thread
+        if thread is not None:
+            thread.join(timeout=timeout)
+
+
+# --- The CLI warmer --------------------------------------------------------------------------------
+# Mirrors ``desk_topup_compute.py``'s own CLI precedent: resolves the SAME env/config seams the
+# backend reads, runs ``run_screen_and_record`` to completion SYNCHRONOUSLY in-process (no manager,
+# no background thread -- a CLI invocation IS the one caller), and exits 0 with a summary.
+# ``--date`` is REQUIRED (``argparse``'s own ``required=True`` exits non-zero with a usage error on
+# a missing value) -- this CLI never defaults to today's wall-clock date (T-6).
+
+
+def _cli_progress_printer() -> Callable[[dict], None]:
+    def _printer(entry: dict) -> None:
+        print(f"[{entry['symbol']}] done", flush=True)
+
+    return _printer
+
+
+def main() -> int:
+    """The CLI entry: ``python -m app.research.desk_screen_compute --date YYYY-MM-DD``. Runs the
+    screen to completion against the operator's real universe/bar/dataset dirs, publishing to the
+    SAME durable screen store ``GET /research/desk/screen`` serves."""
+    parser = argparse.ArgumentParser(
+        description="Era B \"The Desk\" J-03 CLI warmer -- compute the desk screen for a REQUIRED "
+        "--date (never defaults to today), over the latest registered universe snapshot, and "
+        "persist it append-only to the SAME durable screen store GET /research/desk/screen serves."
+    )
+    parser.add_argument(
+        "--date", required=True,
+        help="the screen date (YYYY-MM-DD) to compute the screen for -- REQUIRED; never defaults "
+        "to today's wall-clock date (T-6).",
+    )
+    args = parser.parse_args()
+
+    config = CONFIG
+    universe_store = UniverseStore(config.desk_universe_dir_resolved())
+    bar_store = get_bar_store()
+    bar_index = get_bar_index()
+    dataset_store = get_dataset_store()
+    screen_store = ScreenStore(resolve_desk_screen_dir(config.desk_universe_dir_resolved()))
+
+    recorded = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, config, screen_store,
+        args.date, progress=_cli_progress_printer(),
+    )
+    print(
+        f"desk screen complete for {args.date}: {len(recorded['rows'])} ranked, "
+        f"{len(recorded['skipped'])} skipped -- snapshot {recorded['id']}."
+    )
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/fixtures/yahoo/MSFT_1d_20260101_20260626.json b/apps/backend/tests/fixtures/yahoo/MSFT_1d_20260101_20260626.json
new file mode 100644
index 0000000..fb78b2f
--- /dev/null
+++ b/apps/backend/tests/fixtures/yahoo/MSFT_1d_20260101_20260626.json
@@ -0,0 +1,968 @@
+{
+  "symbol": "MSFT",
+  "timeframe": "1d",
+  "start": "2026-01-01T00:00:00Z",
+  "end": "2026-06-26T04:00:00Z",
+  "bars": [
+    {
+      "epoch": 1767330000.0,
+      "open": 482.24244872265706,
+      "high": 482.5112407273309,
+      "low": 468.07552715971417,
+      "close": 470.84320068359375,
+      "volume": 25571600
+    },
+    {
+      "epoch": 1767589200.0,
+      "open": 471.95822796941724,
+      "high": 473.95932625248497,
+      "low": 467.41844739653146,
+      "close": 470.75360107421875,
+      "volume": 25250300
+    },
+    {
+      "epoch": 1767675600.0,
+      "open": 471.69937935780575,
+      "high": 476.617480129593,
+      "low": 467.6673473241013,
+      "close": 476.3885192871094,
+      "volume": 23037700
+    },
+    {
+      "epoch": 1767762000.0,
+      "open": 477.63296458601815,
+      "high": 487.5288974221053,
+      "low": 475.83099176167434,
+      "close": 481.3265075683594,
+      "volume": 25564200
+    },
+    {
+      "epoch": 1767848400.0,
+      "open": 479.10639276886474,
+      "high": 480.5201105081445,
+      "low": 473.7502403609407,
+      "close": 475.9902648925781,
+      "volume": 18162600
+    },
+    {
+      "epoch": 1767934800.0,
+      "open": 471.9582322108041,
+      "high": 477.6927047258898,
+      "low": 470.106493184136,
+      "close": 477.15509033203125,
+      "volume": 18491000
+    },
+    {
+      "epoch": 1768194000.0,
+      "open": 474.5566738594685,
+      "high": 478.85749783991434,
+      "low": 473.57104241242143,
+      "close": 475.06439208984375,
+      "volume": 23519900
+    },
+    {
+      "epoch": 1768280400.0,
+      "open": 472.57548334410274,
+      "high": 473.6706125344443,
+      "low": 463.88420753037366,
+      "close": 468.5832824707031,
+      "volume": 28545800
+    },
+    {
+      "epoch": 1768366800.0,
+      "open": 464.3919508718589,
+      "high": 466.12425727832346,
+      "low": 455.14315976714454,
+      "close": 457.3433532714844,
+      "volume": 28184300
+    },
+    {
+      "epoch": 1768453200.0,
+      "open": 462.06232415810086,
+      "high": 462.191752665677,
+      "low": 453.8787662235596,
+      "close": 454.6354064941406,
+      "volume": 23225800
+    },
+    {
+      "epoch": 1768539600.0,
+      "open": 455.8001987238622,
+      "high": 461.13645097900303,
+      "low": 454.4562082505655,
+      "close": 457.8211975097656,
+      "volume": 34246700
+    },
+    {
+      "epoch": 1768885200.0,
+      "open": 449.2194951600843,
+      "high": 454.77474258752966,
+      "low": 447.28809381488645,
+      "close": 452.5048522949219,
+      "volume": 26130000
+    },
+    {
+      "epoch": 1768971600.0,
+      "open": 450.5933708341933,
+      "high": 450.6829681667298,
+      "low": 436.73507280530305,
+      "close": 442.1409912109375,
+      "volume": 37980500
+    },
+    {
+      "epoch": 1769058000.0,
+      "open": 445.6354487179439,
+      "high": 450.8323067932568,
+      "low": 442.7284117030413,
+      "close": 449.1398620605469,
+      "volume": 25349400
+    },
+    {
+      "epoch": 1769144400.0,
+      "open": 449.8665935761158,
+      "high": 469.01134678020316,
+      "low": 448.5325382185013,
+      "close": 463.8841857910156,
+      "volume": 38000200
+    },
+    {
+      "epoch": 1769403600.0,
+      "open": 463.2470104625561,
+      "high": 472.14737672642065,
+      "low": 459.9516880286902,
+      "close": 468.1949768066406,
+      "volume": 29291200
+    },
+    {
+      "epoch": 1769490000.0,
+      "open": 471.59986874099184,
+      "high": 480.72919663912324,
+      "low": 471.06225431764057,
+      "close": 478.4493408203125,
+      "volume": 29213900
+    },
+    {
+      "epoch": 1769576400.0,
+      "open": 481.0676409982362,
+      "high": 481.59528998521284,
+      "low": 475.8807484603396,
+      "close": 479.4946594238281,
+      "volume": 36875400
+    },
+    {
+      "epoch": 1769662800.0,
+      "open": 438.0392806211351,
+      "high": 440.5381621786467,
+      "low": 419.1533835040837,
+      "close": 431.57806396484375,
+      "volume": 128855300
+    },
+    {
+      "epoch": 1769749200.0,
+      "open": 437.2229285851671,
+      "high": 437.65101486434605,
+      "low": 424.55932220203715,
+      "close": 428.3822937011719,
+      "volume": 58566800
+    },
+    {
+      "epoch": 1770008400.0,
+      "open": 428.33251789753194,
+      "high": 428.8303011436502,
+      "low": 420.37795134689077,
+      "close": 421.49298095703125,
+      "volume": 42219900
+    },
+    {
+      "epoch": 1770094800.0,
+      "open": 420.1390072256922,
+      "high": 420.178808008447,
+      "low": 406.7486263222299,
+      "close": 409.3868713378906,
+      "volume": 61424100
+    },
+    {
+      "epoch": 1770181200.0,
+      "open": 409.17783910585314,
+      "high": 417.93881231579195,
+      "low": 407.4256323109538,
+      "close": 412.35369873046875,
+      "volume": 45012400
+    },
+    {
+      "epoch": 1770267600.0,
+      "open": 405.6335909812077,
+      "high": 406.4897635323938,
+      "low": 390.5806313349955,
+      "close": 391.9246520996094,
+      "volume": 66289200
+    },
+    {
+      "epoch": 1770354000.0,
+      "open": 397.4002746193236,
+      "high": 400.0086538663787,
+      "low": 391.17798428483076,
+      "close": 399.3615417480469,
+      "volume": 53515300
+    },
+    {
+      "epoch": 1770613200.0,
+      "open": 403.0550898097971,
+      "high": 413.05058563481117,
+      "low": 399.0927243377603,
+      "close": 411.76629638671875,
+      "volume": 45480500
+    },
+    {
+      "epoch": 1770699600.0,
+      "open": 417.75959730190846,
+      "high": 421.80159473973595,
+      "low": 410.8702943432265,
+      "close": 411.437744140625,
+      "volume": 44857900
+    },
+    {
+      "epoch": 1770786000.0,
+      "open": 414.33481566901673,
+      "high": 414.61357304478975,
+      "low": 399.2320904458023,
+      "close": 402.5771789550781,
+      "volume": 42491000
+    },
+    {
+      "epoch": 1770872400.0,
+      "open": 403.20440420967,
+      "high": 404.3990960787573,
+      "low": 396.24540458526855,
+      "close": 400.05841064453125,
+      "volume": 40802400
+    },
+    {
+      "epoch": 1770958800.0,
+      "open": 402.65686886295305,
+      "high": 403.7420326637702,
+      "low": 396.2852191820681,
+      "close": 399.5407409667969,
+      "volume": 34091600
+    },
+    {
+      "epoch": 1771304400.0,
+      "open": 397.45004705087115,
+      "high": 398.7442713079252,
+      "low": 392.78083787972264,
+      "close": 395.1004943847656,
+      "volume": 32078800
+    },
+    {
+      "epoch": 1771390800.0,
+      "open": 396.3648548030424,
+      "high": 400.77520665339193,
+      "low": 394.56288205367116,
+      "close": 397.8283386230469,
+      "volume": 23223400
+    },
+    {
+      "epoch": 1771477200.0,
+      "open": 399.82403795970674,
+      "high": 403.55594539020564,
+      "low": 395.8127368785549,
+      "close": 397.5988464355469,
+      "volume": 28234000
+    },
+    {
+      "epoch": 1771563600.0,
+      "open": 395.2539159508346,
+      "high": 399.2552593187824,
+      "low": 394.3059873534157,
+      "close": 396.37152099609375,
+      "volume": 34015200
+    },
+    {
+      "epoch": 1771822800.0,
+      "open": 394.14630950985264,
+      "high": 394.50551684604494,
+      "low": 382.27203437696886,
+      "close": 383.6390686035156,
+      "volume": 43238300
+    },
+    {
+      "epoch": 1771909200.0,
+      "open": 383.30981969967445,
+      "high": 388.5185091169527,
+      "low": 380.88504821898124,
+      "close": 388.1593017578125,
+      "volume": 33884700
+    },
+    {
+      "epoch": 1771995600.0,
+      "open": 389.68597856263057,
+      "high": 400.60233728073825,
+      "low": 389.31678308531696,
+      "close": 399.7342224121094,
+      "volume": 43625500
+    },
+    {
+      "epoch": 1772082000.0,
+      "open": 403.8353349281015,
+      "high": 406.6093255926281,
+      "low": 397.8782360341113,
+      "close": 400.851806640625,
+      "volume": 34405900
+    },
+    {
+      "epoch": 1772168400.0,
+      "open": 390.03523926255787,
+      "high": 395.9624042352165,
+      "low": 389.0374004516944,
+      "close": 391.8912048339844,
+      "volume": 51367200
+    },
+    {
+      "epoch": 1772427600.0,
+      "open": 392.01092411942045,
+      "high": 400.32293811697235,
+      "low": 389.78576315389057,
+      "close": 397.6886291503906,
+      "volume": 35474900
+    },
+    {
+      "epoch": 1772514000.0,
+      "open": 392.2903484387299,
+      "high": 405.82103971635513,
+      "low": 391.82136299902305,
+      "close": 403.0570068359375,
+      "volume": 38199200
+    },
+    {
+      "epoch": 1772600400.0,
+      "open": 400.4027502952161,
+      "high": 410.14166638677375,
+      "low": 399.44483360720756,
+      "close": 404.32427978515625,
+      "volume": 35808000
+    },
+    {
+      "epoch": 1772686800.0,
+      "open": 403.54596943015656,
+      "high": 410.72040218284053,
+      "low": 403.525993165685,
+      "close": 409.79241943359375,
+      "volume": 39001300
+    },
+    {
+      "epoch": 1772773200.0,
+      "open": 408.31564337314285,
+      "high": 412.1572983375802,
+      "low": 407.6271321747383,
+      "close": 408.0761413574219,
+      "volume": 31123900
+    },
+    {
+      "epoch": 1773028800.0,
+      "open": 404.044890641513,
+      "high": 409.3234358422322,
+      "low": 402.62794618065146,
+      "close": 408.5251770019531,
+      "volume": 30131900
+    },
+    {
+      "epoch": 1773115200.0,
+      "open": 409.1438479339772,
+      "high": 409.31349393117443,
+      "low": 402.05918625996463,
+      "close": 404.8830871582031,
+      "volume": 31706400
+    },
+    {
+      "epoch": 1773201600.0,
+      "open": 404.6934855668013,
+      "high": 408.1260534422115,
+      "low": 400.7220762180728,
+      "close": 404.0049743652344,
+      "volume": 25512100
+    },
+    {
+      "epoch": 1773288000.0,
+      "open": 403.7555185610488,
+      "high": 405.2422886286942,
+      "low": 400.84181586601125,
+      "close": 400.9914855957031,
+      "volume": 27263900
+    },
+    {
+      "epoch": 1773374400.0,
+      "open": 400.13336309353434,
+      "high": 403.9251383935716,
... [diff_bound] apps/backend/tests/fixtures/yahoo/MSFT_1d_20260101_20260626.json: 575 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/fixtures/yahoo/MSFT_1h_20260601_20260618.json b/apps/backend/tests/fixtures/yahoo/MSFT_1h_20260601_20260618.json
new file mode 100644
index 0000000..57d4b25
--- /dev/null
+++ b/apps/backend/tests/fixtures/yahoo/MSFT_1h_20260601_20260618.json
@@ -0,0 +1,784 @@
+{
+  "symbol": "MSFT",
+  "timeframe": "1h",
+  "start": "2026-06-01T13:30:00Z",
+  "end": "2026-06-18T19:30:00Z",
+  "bars": [
+    {
+      "epoch": 1780320600.0,
+      "open": 465.05999755859375,
+      "high": 466.32000732421875,
+      "low": 458.9200134277344,
+      "close": 461.7950134277344,
+      "volume": 0
+    },
+    {
+      "epoch": 1780324200.0,
+      "open": 461.8299865722656,
+      "high": 463.45001220703125,
+      "low": 459.1708068847656,
+      "close": 460.5799865722656,
+      "volume": 6423476
+    },
+    {
+      "epoch": 1780327800.0,
+      "open": 460.6199951171875,
+      "high": 463.9100036621094,
+      "low": 459.20001220703125,
+      "close": 461.760009765625,
+      "volume": 4871854
+    },
+    {
+      "epoch": 1780331400.0,
+      "open": 461.760009765625,
+      "high": 462.45001220703125,
+      "low": 459.5899963378906,
+      "close": 460.2799987792969,
+      "volume": 3061170
+    },
+    {
+      "epoch": 1780335000.0,
+      "open": 460.3500061035156,
+      "high": 461.70001220703125,
+      "low": 458.2699890136719,
+      "close": 460.8699951171875,
+      "volume": 4257015
+    },
+    {
+      "epoch": 1780338600.0,
+      "open": 460.8599853515625,
+      "high": 464.1199951171875,
+      "low": 460.05999755859375,
+      "close": 463.7699890136719,
+      "volume": 3592662
+    },
+    {
+      "epoch": 1780342200.0,
+      "open": 463.7585144042969,
+      "high": 464.1499938964844,
+      "low": 460.0203857421875,
+      "close": 460.57000732421875,
+      "volume": 3640495
+    },
+    {
+      "epoch": 1780407000.0,
+      "open": 447.16900634765625,
+      "high": 453.5,
+      "low": 443.5,
+      "close": 444.2300109863281,
+      "volume": 10605001
+    },
+    {
+      "epoch": 1780410600.0,
+      "open": 444.2300109863281,
+      "high": 445.2597961425781,
+      "low": 442.3399963378906,
+      "close": 443.57000732421875,
+      "volume": 4862335
+    },
+    {
+      "epoch": 1780414200.0,
+      "open": 443.54998779296875,
+      "high": 446.20001220703125,
+      "low": 443.17999267578125,
+      "close": 445.7799987792969,
+      "volume": 2903136
+    },
+    {
+      "epoch": 1780417800.0,
+      "open": 445.79998779296875,
+      "high": 445.8999938964844,
+      "low": 442.3999938964844,
+      "close": 444.4700012207031,
+      "volume": 3251530
+    },
+    {
+      "epoch": 1780421400.0,
+      "open": 444.4700012207031,
+      "high": 444.5899963378906,
+      "low": 441.4397888183594,
+      "close": 442.09478759765625,
+      "volume": 2783822
+    },
+    {
+      "epoch": 1780425000.0,
+      "open": 442.0899963378906,
+      "high": 442.8299865722656,
+      "low": 440.42999267578125,
+      "close": 441.69000244140625,
+      "volume": 3010126
+    },
+    {
+      "epoch": 1780428600.0,
+      "open": 441.7099914550781,
+      "high": 442.1000061035156,
+      "low": 440.7200012207031,
+      "close": 441.2900085449219,
+      "volume": 3152055
+    },
+    {
+      "epoch": 1780493400.0,
+      "open": 438.45001220703125,
+      "high": 440.3900146484375,
+      "low": 430.54998779296875,
+      "close": 430.81500244140625,
+      "volume": 9367976
+    },
+    {
+      "epoch": 1780497000.0,
+      "open": 430.81500244140625,
+      "high": 431.5199890136719,
+      "low": 425.8500061035156,
+      "close": 427.739990234375,
+      "volume": 5871937
+    },
+    {
+      "epoch": 1780500600.0,
+      "open": 427.7900085449219,
+      "high": 427.7900085449219,
+      "low": 425.1199951171875,
+      "close": 425.4750061035156,
+      "volume": 3020826
+    },
+    {
+      "epoch": 1780504200.0,
+      "open": 425.4599914550781,
+      "high": 425.8299865722656,
+      "low": 424.25,
+      "close": 425.45989990234375,
+      "volume": 3512091
+    },
+    {
+      "epoch": 1780507800.0,
+      "open": 425.4800109863281,
+      "high": 428.29998779296875,
+      "low": 425.0899963378906,
+      "close": 428.1499938964844,
+      "volume": 2538548
+    },
+    {
+      "epoch": 1780511400.0,
+      "open": 428.19000244140625,
+      "high": 428.9599914550781,
+      "low": 427.3699951171875,
+      "close": 427.8299865722656,
+      "volume": 2641197
+    },
+    {
+      "epoch": 1780515000.0,
+      "open": 427.8349914550781,
+      "high": 428.739990234375,
+      "low": 426.7900085449219,
+      "close": 427.5799865722656,
+      "volume": 4334327
+    },
+    {
+      "epoch": 1780579800.0,
+      "open": 435.9949951171875,
+      "high": 436.1499938964844,
+      "low": 428.75,
+      "close": 430.1351013183594,
+      "volume": 7191457
+    },
+    {
+      "epoch": 1780583400.0,
+      "open": 430.2200012207031,
+      "high": 431.55999755859375,
+      "low": 429.0,
+      "close": 430.2900085449219,
+      "volume": 2447017
+    },
+    {
+      "epoch": 1780587000.0,
+      "open": 430.3900146484375,
+      "high": 430.7900085449219,
+      "low": 427.7445068359375,
+      "close": 427.7699890136719,
+      "volume": 2732327
+    },
+    {
+      "epoch": 1780590600.0,
+      "open": 427.82000732421875,
+      "high": 428.95001220703125,
+      "low": 426.4100036621094,
+      "close": 426.92999267578125,
+      "volume": 2056733
+    },
+    {
+      "epoch": 1780594200.0,
+      "open": 426.9750061035156,
+      "high": 428.4700012207031,
+      "low": 426.70001220703125,
+      "close": 427.7146911621094,
+      "volume": 1831947
+    },
+    {
+      "epoch": 1780597800.0,
+      "open": 427.69000244140625,
+      "high": 429.0,
+      "low": 426.9800109863281,
+      "close": 427.68499755859375,
+      "volume": 2281672
+    },
+    {
+      "epoch": 1780601400.0,
+      "open": 427.6650085449219,
+      "high": 428.44000244140625,
+      "low": 427.0,
+      "close": 428.0799865722656,
+      "volume": 2383020
+    },
+    {
+      "epoch": 1780666200.0,
+      "open": 428.3399963378906,
+      "high": 429.4700012207031,
+      "low": 421.7099914550781,
+      "close": 423.0559997558594,
+      "volume": 5532712
+    },
+    {
+      "epoch": 1780669800.0,
+      "open": 422.9989013671875,
+      "high": 423.135009765625,
+      "low": 420.70001220703125,
+      "close": 422.2500915527344,
+      "volume": 3905078
+    },
+    {
+      "epoch": 1780673400.0,
+      "open": 422.25,
+      "high": 422.3800048828125,
+      "low": 418.9100036621094,
+      "close": 419.79998779296875,
+      "volume": 3441361
+    },
+    {
+      "epoch": 1780677000.0,
+      "open": 419.82000732421875,
+      "high": 420.75,
+      "low": 418.5801086425781,
+      "close": 419.69000244140625,
+      "volume": 2331915
+    },
+    {
+      "epoch": 1780680600.0,
+      "open": 419.6499938964844,
+      "high": 421.5199890136719,
+      "low": 417.79998779296875,
+      "close": 418.2900085449219,
+      "volume": 3203638
+    },
+    {
+      "epoch": 1780684200.0,
+      "open": 418.2799987792969,
+      "high": 418.3500061035156,
+      "low": 414.3999938964844,
+      "close": 416.3900146484375,
+      "volume": 4033474
+    },
+    {
+      "epoch": 1780687800.0,
+      "open": 416.375,
+      "high": 417.4800109863281,
+      "low": 416.0299987792969,
+      "close": 416.67999267578125,
+      "volume": 3674739
+    },
+    {
+      "epoch": 1780925400.0,
+      "open": 414.1600036621094,
+      "high": 417.159912109375,
+      "low": 411.29010009765625,
+      "close": 412.7349853515625,
+      "volume": 6939242
+    },
+    {
+      "epoch": 1780929000.0,
+      "open": 412.7349853515625,
+      "high": 413.6000061035156,
+      "low": 411.3500061035156,
+      "close": 411.4200134277344,
+      "volume": 3206417
+    },
+    {
+      "epoch": 1780932600.0,
+      "open": 411.3999938964844,
+      "high": 411.5899963378906,
+      "low": 409.82000732421875,
+      "close": 410.489990234375,
+      "volume": 2801780
+    },
+    {
+      "epoch": 1780936200.0,
+      "open": 410.4800109863281,
+      "high": 410.7799987792969,
+      "low": 408.55999755859375,
+      "close": 410.01031494140625,
+      "volume": 2519234
+    },
+    {
+      "epoch": 1780939800.0,
+      "open": 409.989990234375,
+      "high": 412.75,
+      "low": 409.6300048828125,
+      "close": 412.2699890136719,
+      "volume": 2523666
+    },
+    {
+      "epoch": 1780943400.0,
+      "open": 412.2200012207031,
+      "high": 413.0,
+      "low": 411.6004943847656,
+      "close": 412.2900085449219,
+      "volume": 1973534
+    },
+    {
+      "epoch": 1780947000.0,
+      "open": 412.2900085449219,
+      "high": 413.25,
+      "low": 411.17999267578125,
+      "close": 411.739990234375,
+      "volume": 2978824
+    },
+    {
+      "epoch": 1781011800.0,
+      "open": 409.0299987792969,
+      "high": 411.9800109863281,
+      "low": 407.2099914550781,
+      "close": 409.4849853515625,
+      "volume": 6855395
+    },
+    {
+      "epoch": 1781015400.0,
+      "open": 409.4599914550781,
+      "high": 410.0299987792969,
+      "low": 403.5199890136719,
+      "close": 403.7149963378906,
+      "volume": 3823575
+    },
+    {
+      "epoch": 1781019000.0,
+      "open": 403.67999267578125,
+      "high": 403.9100036621094,
+      "low": 400.4700927734375,
+      "close": 401.1300048828125,
+      "volume": 4154859
+    },
+    {
+      "epoch": 1781022600.0,
+      "open": 401.04998779296875,
+      "high": 402.1000061035156,
+      "low": 398.4814147949219,
+      "close": 401.69000244140625,
+      "volume": 4051363
+    },
+    {
+      "epoch": 1781026200.0,
+      "open": 401.7049865722656,
+      "high": 403.9612121582031,
+      "low": 401.5899963378906,
+      "close": 403.6400146484375,
+      "volume": 2371470
+    },
+    {
+      "epoch": 1781029800.0,
+      "open": 403.6449890136719,
+      "high": 404.4599914550781,
+      "low": 402.4288024902344,
+      "close": 402.75,
+      "volume": 2923013
+    },
+    {
+      "epoch": 1781033400.0,
+      "open": 402.75,
+      "high": 404.25,
... [diff_bound] apps/backend/tests/fixtures/yahoo/MSFT_1h_20260601_20260618.json: 391 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_desk_screen.py b/apps/backend/tests/test_desk_screen.py
new file mode 100644
index 0000000..718a97d
--- /dev/null
+++ b/apps/backend/tests/test_desk_screen.py
@@ -0,0 +1,650 @@
+"""``desk_screen.py`` (Era B "The Desk", J-03) — the screen-snapshot store discipline, the
+``bar_store_signature`` index-only derivation (T-4/TC-15), best-band selection + ``distance_bps``,
+and the row-computation function (``compute_screen``) against the REAL committed fixture universe
+(103 members) and the real AAPL/MSFT bar fixtures — never a synthetic ``AAA...EEE`` stand-in for
+any clause naming real symbols (lessons.md iter-2). Compute-manager/route/CLI coverage lives in
+``test_desk_screen_compute.py``.
+"""
+
+from __future__ import annotations
+
+import json
+import shutil
+from pathlib import Path
+
+import pytest
+
+from app.config import CONFIG
+from app.providers.adapters.base import RawBar
+from app.providers.base import Side, TradeEvent
+from app.research.bar_index import BarIndex
+from app.research.bars import BarStore
+from app.research.datasets import SPLIT_TRAIN, DatasetStore
+from app.research.desk_coverage import get_desk_coverage
+from app.research.desk_screen import (
+    ScreenAlreadyRecorded,
+    ScreenIntegrityError,
+    ScreenStore,
+    compute_bar_store_signature,
+    compute_screen,
+    resolve_desk_screen_dir,
+    screen_as_of,
+)
+from app.research.desk_screen import _distance_bps, _row_rank_key, _select_best_band
+from app.research.desk_universe import UniverseStore
+
+FIXTURE_UNIVERSE_DIR = Path(__file__).parent / "fixtures" / "universe"
+REGISTERED_SNAPSHOT_PATH = FIXTURE_UNIVERSE_DIR / "universe-2026-07-25-817cc184bbb3.json"
+FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"
+
+AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"
+MSFT_DAILY_FIXTURE = "MSFT_1d_20260101_20260626.json"
+MSFT_HOURLY_FIXTURE = "MSFT_1h_20260601_20260618.json"
+
+# The pinned session goal.md's J-01/J-05/J-07 acceptance text already names (test_tradability.py's
+# own golden: as_of="2026-06-22T15:00:00Z" resolves basis_as_of="2026-06-18T04:00:00.000000Z") --
+# any as_of inside this same UTC calendar day resolves the identical basis (T-6), so this is a
+# zero-new-fixture-risk screen_date.
+SCREEN_DATE = "2026-06-22"
+
+# The goal.md build-anchors' own 11 recorded dataset symbols. SPY is in this list but is NOT an
+# S&P 100 constituent (it is the index-tracking ETF, never a member of the index itself) -- so it
+# never appears in the fixture universe's `rows`/`skipped` and its tick_evidence is never asserted.
+DATASET_SYMBOLS = (
+    "AAPL", "AMD", "AMZN", "GOOGL", "META", "MSFT", "NFLX", "NVDA", "PG", "SPY", "TSLA",
+)
+
+
+def _load_yahoo_fixture(name: str) -> dict:
+    return json.loads((FIXTURE_YAHOO_DIR / name).read_text())
+
+
+def _seed_yahoo_fixture(bar_store: BarStore, bar_index: BarIndex, fixture: dict) -> None:
+    bars = [
+        RawBar(
+            fixture["symbol"], fixture["timeframe"], b["epoch"],
+            b["open"], b["high"], b["low"], b["close"], b["volume"],
+        )
+        for b in fixture["bars"]
+    ]
+    meta = bar_store.record(
+        symbol=fixture["symbol"], timeframe=fixture["timeframe"],
+        window_start_utc=fixture["start"], window_end_utc=fixture["end"],
+        feed="yahoo", bars=bars,
+    )
+    bar_index.insert(meta)
+
+
+def _register_fixture_universe(universe_dir: Path) -> UniverseStore:
+    """"The fixture universe" (J-01's own naming): the REAL committed 103-member snapshot, copied
+    into a temp universe dir exactly as ``test_desk_universe.py``'s
+    ``test_the_committed_fixture_snapshot_loads_cleanly_through_the_store`` does."""
+    universe_dir.mkdir(parents=True, exist_ok=True)
+    shutil.copy(REGISTERED_SNAPSHOT_PATH, universe_dir / REGISTERED_SNAPSHOT_PATH.name)
+    return UniverseStore(universe_dir)
+
+
+def _register_dataset(dataset_store: DatasetStore, symbol: str) -> None:
+    """A minimal, single-trade synthetic dataset registration -- proves ONLY that ``symbol`` is a
+    presence in the dataset store (the tick-evidence badge's own honest contract), never a claim
+    about real tick content."""
+    dataset_store.record(
+        symbol=symbol, source=f"synthetic {symbol}", source_kind="reference", source_id=symbol,
+        split=SPLIT_TRAIN, window_start_utc="2026-01-02T14:30:00Z", window_end_utc="2026-01-02T14:30:01Z",
+        data_feed="sim", epoch_anchor=None,
+        events=[TradeEvent(symbol, 0.0, 100.0, 100, Side.UNKNOWN)],
+    )
+
+
+@pytest.fixture
+def ctx(tmp_path):
+    """A fully-scoped desk context: the real fixture universe + empty bar/dataset stores, all
+    rooted under ``tmp_path`` -- never the ambient real ``.data/`` tree."""
+    universe_store = _register_fixture_universe(tmp_path / "universe")
+    bar_store = BarStore(tmp_path / "bars")
+    bar_index = BarIndex(str(tmp_path / "index.db"))
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    return universe_store, bar_store, bar_index, dataset_store
+
+
+# ==================================================================================================
+# as_of translation (T-6)
+# ==================================================================================================
+
+
+def test_screen_as_of_is_a_pure_function_of_screen_date():
+    assert screen_as_of("2026-06-22") == "2026-06-22T23:59:59Z"
+    assert screen_as_of("2026-01-01") == "2026-01-01T23:59:59Z"
+
+
+# ==================================================================================================
+# bar_store_signature (T-4, TC-15)
+# ==================================================================================================
+
+
+def test_bar_store_signature_issues_zero_bar_store_calls(ctx, monkeypatch):
+    """T-4/TC-15: instrumented exactly like ``test_desk_coverage.py``'s
+    ``test_coverage_issues_zero_bar_store_calls`` -- derivation goes entirely through
+    ``desk_coverage.get_desk_coverage`` (index-only), never a ``BarStore`` read."""
+    universe_store, bar_store, bar_index, _dataset_store = ctx
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+
+    calls: list[str] = []
+    original_list = BarStore.list
+    original_get = BarStore.get
+
+    def _tracked_list(self, *args, **kwargs):
+        calls.append("list")
+        return original_list(self, *args, **kwargs)
+
+    def _tracked_get(self, *args, **kwargs):
+        calls.append("get")
+        return original_get(self, *args, **kwargs)
+
+    monkeypatch.setattr(BarStore, "list", _tracked_list)
+    monkeypatch.setattr(BarStore, "get", _tracked_get)
+
+    signature = compute_bar_store_signature(universe_store, bar_index)
+
+    assert calls == []
+    assert isinstance(signature, str) and len(signature) == 16
+
+
+def test_bar_store_signature_changes_when_coverage_changes(ctx):
+    universe_store, bar_store, bar_index, _dataset_store = ctx
+    before = compute_bar_store_signature(universe_store, bar_index)
+
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+    after = compute_bar_store_signature(universe_store, bar_index)
+
+    assert before != after
+
+
+def test_bar_store_signature_is_deterministic_across_fresh_instances(ctx):
+    universe_store, bar_store, bar_index, _dataset_store = ctx
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+
+    first = compute_bar_store_signature(universe_store, bar_index)
+    second = compute_bar_store_signature(UniverseStore(universe_store.root), BarIndex(bar_index.db_path))
+    assert first == second
+
+
+# ==================================================================================================
+# best-band selection + distance_bps (assumptions.md iter-3 entry 1) -- pure-function unit tests
+# ==================================================================================================
+
+
+def _band(side: str, price_low: float, price_high: float, band_class: str | None, quality: float) -> dict:
+    return {"side": side, "price_low": price_low, "price_high": price_high, "class": band_class, "quality_score": quality}
+
+
+def test_distance_bps_resistance_uses_the_low_edge():
+    band = _band("resistance", 101.0, 102.0, "A", 10.0)
+    assert _distance_bps(band, 100.0) == pytest.approx((101.0 - 100.0) / 100.0 * 10_000.0)
+
+
+def test_distance_bps_support_uses_the_high_edge():
+    band = _band("support", 98.0, 99.0, "A", 10.0)
+    assert _distance_bps(band, 100.0) == pytest.approx((100.0 - 99.0) / 100.0 * 10_000.0)
+
+
+def test_select_best_band_prefers_higher_class_over_closer_distance():
+    close_but_low_class = _band("resistance", 100.1, 100.2, "C", 500.0)
+    far_but_high_class = _band("resistance", 110.0, 111.0, "A", 1.0)
+    best = _select_best_band([close_but_low_class, far_but_high_class], 100.0)
+    assert best is far_but_high_class
+
+
+def test_select_best_band_ties_on_class_prefer_closer_distance():
+    near = _band("resistance", 100.5, 100.6, "B", 1.0)
+    far = _band("resistance", 120.0, 121.0, "B", 999.0)
+    best = _select_best_band([far, near], 100.0)
+    assert best is near
+
+
+def test_select_best_band_ties_on_class_and_distance_prefer_higher_quality():
+    a = _band("resistance", 105.0, 105.0, "B", 5.0)
+    b = _band("resistance", 105.0, 105.0, "B", 50.0)
+    best = _select_best_band([a, b], 100.0)
+    assert best is b
+
+
+def test_select_best_band_exact_tie_keeps_the_served_order_first_item():
+    a = _band("resistance", 105.0, 105.0, "B", 5.0)
+    b = _band("resistance", 105.0, 105.0, "B", 5.0)
+    assert _select_best_band([a, b], 100.0) is a
+    assert _select_best_band([b, a], 100.0) is b
+
+
+def test_select_best_band_null_class_ranks_below_every_graded_class():
+    graded = _band("resistance", 200.0, 201.0, "C", 1.0)
+    ungraded_and_closer = _band("resistance", 100.1, 100.2, None, 999.0)
+    best = _select_best_band([graded, ungraded_and_closer], 100.0)
+    assert best is graded
+
+
+# ==================================================================================================
+# ScreenStore discipline -- mirrors test_desk_universe.py's store-level suite exactly
+# ==================================================================================================
+
+
+def _record(store: ScreenStore, **overrides) -> dict:
+    defaults = dict(
+        screen_date="2026-06-22", as_of="2026-06-22T23:59:59Z",
+        universe_snapshot_id="universe-2026-07-25-817cc184bbb3",
+        config_fingerprint=CONFIG.config_fingerprint(), bar_store_signature="deadbeef00000000",
+        rows=[{"symbol": "AAPL", "side": "resistance", "band_class": "C", "distance_bps": 1.0,
+               "band_score": 2.0, "price_low": 100.0, "price_high": 101.0,
+               "coverage": {}, "tick_evidence": True}],
+        skipped=[{"symbol": "ABBV", "skipped": True, "reason": "no_bars", "coverage": {}, "tick_evidence": False}],
+    )
+    defaults.update(overrides)
+    return store.record(**defaults)
+
+
+def test_record_stores_the_exact_5pin_key_and_content(tmp_path):
+    store = ScreenStore(tmp_path / "screen")
+    meta = _record(store)
+
+    assert meta["id"].startswith("screen-2026-06-22-")
+    checksum_suffix = meta["id"].removeprefix("screen-2026-06-22-")
+    assert len(checksum_suffix) == 12
+    int(checksum_suffix, 16)  # hex, or this raises
+    assert meta["screen_date"] == "2026-06-22"
+    assert meta["as_of"] == "2026-06-22T23:59:59Z"
+    assert meta["universe_snapshot_id"] == "universe-2026-07-25-817cc184bbb3"
+    assert meta["config_fingerprint"] == CONFIG.config_fingerprint()
+    assert meta["bar_store_signature"] == "deadbeef00000000"
+    assert meta["created_utc"].endswith("Z")
+    assert len(meta["rows"]) == 1 and len(meta["skipped"]) == 1
+    assert len(list((tmp_path / "screen").glob("*.json"))) == 1
+
+
+def test_list_serves_the_stored_record_verbatim_oldest_first(tmp_path):
+    store = ScreenStore(tmp_path / "screen")
+    recorded = _record(store)
+
+    records, errors = store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0] == recorded
+
+
+def test_store_survives_a_reload_from_disk(tmp_path):
+    root = tmp_path / "screen"
+    recorded = _record(ScreenStore(root))
+
+    reloaded = ScreenStore(root)
+    records, errors = reloaded.list()
+    assert errors == [] and records == [recorded]
+
+
+def test_empty_store_lists_nothing(tmp_path):
+    store = ScreenStore(tmp_path / "screen")
+    records, errors = store.list()
+    assert records == [] and errors == []
+
+
+# --- append-only refusal on an identical 5-pin key (TC-4, store level) --------------------------
+
+
+def test_rerecording_an_identical_key_is_refused(tmp_path):
+    store = ScreenStore(tmp_path / "screen")
+    first = _record(store)
+
+    with pytest.raises(ScreenAlreadyRecorded) as excinfo:
+        _record(store)
+    assert excinfo.value.existing_id == first["id"]
+    assert len(list((tmp_path / "screen").glob("*.json"))) == 1  # no second file
+
+
+def test_rerecording_an_identical_key_leaves_the_file_byte_unchanged(tmp_path):
+    screen_dir = tmp_path / "screen"
+    store = ScreenStore(screen_dir)
+    _record(store)
+    path = next(screen_dir.glob("*.json"))
+    before = path.read_bytes()
+
+    with pytest.raises(ScreenAlreadyRecorded):
+        _record(store)
+    assert path.read_bytes() == before
+
+
+def test_rerecording_the_same_key_with_different_row_content_is_still_refused(tmp_path):
+    """The dedup key is the 5 PINS, never the row content -- two calls sharing the same key but
+    carrying different (e.g. accidentally miscomputed) row content still collide, exactly as
+    intended (the row content is a deterministic function of the pins, so this can only diverge
+    on a genuine bug, and the store must refuse regardless)."""
+    store = ScreenStore(tmp_path / "screen")
+    first = _record(store)
+
+    with pytest.raises(ScreenAlreadyRecorded) as excinfo:
+        _record(store, rows=[], skipped=[])
+    assert excinfo.value.existing_id == first["id"]
+
+
+def test_a_different_key_registers_a_second_distinct_snapshot(tmp_path):
+    store = ScreenStore(tmp_path / "screen")
+    first = _record(store, screen_date="2026-06-22")
+    second = _record(store, screen_date="2026-06-23", as_of="2026-06-23T23:59:59Z")
+
+    assert first["id"] != second["id"]
+    records, errors = store.list()
+    assert errors == []
+    assert {r["id"] for r in records} == {first["id"], second["id"]}
+
+
+def test_find_by_key_returns_none_when_nothing_matches(tmp_path):
+    store = ScreenStore(tmp_path / "screen")
+    _record(store)
+    assert store.find_by_key("2099-01-01", "2099-01-01T23:59:59Z", "x", "y", "z") is None
+
+
+def test_find_by_key_returns_the_exact_match(tmp_path):
+    store = ScreenStore(tmp_path / "screen")
+    recorded = _record(store)
+    found = store.find_by_key(
+        "2026-06-22", "2026-06-22T23:59:59Z", "universe-2026-07-25-817cc184bbb3",
+        CONFIG.config_fingerprint(), "deadbeef00000000",
+    )
+    assert found == recorded
+
+
+# --- integrity: a corrupted file is explicit, never silent --------------------------------------
+
+
+def test_corrupted_snapshot_file_surfaces_explicitly_in_list_errors(tmp_path):
+    screen_dir = tmp_path / "screen"
+    store = ScreenStore(screen_dir)
+    _record(store)
+    path = next(screen_dir.glob("*.json"))
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["screen_date"] = "2099-12-31"  # tamper -- file_checksum now disagrees
+    path.write_text(json.dumps(data))
+
+    records, errors = store.list()
+    assert records == []
+    assert len(errors) == 1
+    assert errors[0]["file"] == path.name
+    assert "integrity" in errors[0]["error"]
+
+
+def test_recording_over_a_corrupted_file_at_the_same_key_is_refused_never_a_silent_overwrite(tmp_path):
+    """A tampered snapshot is withheld from ``records`` (and reported in ``integrity_errors``), so
+    ``find_by_key`` cannot see it -- but the snapshot's PATH is a pure function of the 5-pin key, so
+    a re-record for that same key lands on the SAME file. ``record`` must refuse explicitly: never
+    overwrite a damaged snapshot (that is a rewrite -- "snapshots are append-only ... never
+    rewritten"), and never erase the integrity error the store was honestly surfacing."""
+    screen_dir = tmp_path / "screen"
+    store = ScreenStore(screen_dir)
+    _record(store)
+    path = next(screen_dir.glob("*.json"))
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["rows"] = [{"symbol": "AAPL", "band_class": "TAMPERED"}]
+    path.write_text(json.dumps(data))
+    tampered_bytes = path.read_bytes()
+
+    with pytest.raises(ScreenIntegrityError) as excinfo:
+        _record(store)
+    assert path.name in str(excinfo.value)
+
+    assert path.read_bytes() == tampered_bytes, "the damaged file must be left exactly as found"
+    records, errors = store.list()
+    assert records == []
+    assert [e["file"] for e in errors] == [path.name], "the integrity error must still be surfaced"
... [diff_bound] apps/backend/tests/test_desk_screen.py: 256 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_desk_screen_compute.py b/apps/backend/tests/test_desk_screen_compute.py
new file mode 100644
index 0000000..5dbaa4c
--- /dev/null
+++ b/apps/backend/tests/test_desk_screen_compute.py
@@ -0,0 +1,593 @@
+"""``desk_screen_compute.py`` (Era B "The Desk", J-03) — manager mechanics (single-flight, cancel,
+atomic progress), the append-only reuse guarantee (TC-4), the four HTTP routes, and the CLI
+warmer's ``main()`` (TC-18).
+
+Manager-mechanics tests substitute a FAKE ``compute_screen`` (monkeypatched onto THIS module's own
+imported name — the ``test_desk_topup_compute.py``/``test_edge_report_compute.py`` fake-swap
+precedent) for deterministic, threading-free control over timing. The append-only reuse guarantee
+and the routes are proven end to end against the REAL ``compute_screen`` (real fixture universe,
+real AAPL bars). CLI tests mirror ``test_edge_report_compute.py``'s own CLI pattern (``sys.argv``
++ scoped env vars, never the ambient real ``.data/`` tree).
+"""
+
+from __future__ import annotations
+
+import json
+import shutil
+import sys
+import threading
+import time
+from pathlib import Path
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app, get_market_adapter, manager as ws_manager
+from app.providers.adapters.base import RawBar
+from app.research import desk_screen_compute
+from app.research.bar_index import BarIndex
+from app.research.bars import BarStore
+from app.research.datasets import DatasetStore
+from app.research.desk_routes import get_desk_screen_compute_manager
+from app.research.desk_screen import ScreenStore
+from app.research.desk_screen_compute import DeskScreenComputeManager, run_screen_and_record
+from app.research.desk_universe import UniverseStore
+from app.research.routes import ResearchRegistry, set_registry
+from app.research.store import JournalStore
+
+FIXTURE_UNIVERSE_DIR = Path(__file__).parent / "fixtures" / "universe"
+REGISTERED_SNAPSHOT_PATH = FIXTURE_UNIVERSE_DIR / "universe-2026-07-25-817cc184bbb3.json"
+FIXTURE_YAHOO_DIR = Path(__file__).parent / "fixtures" / "yahoo"
+AAPL_DAILY_FIXTURE = "AAPL_1d_20260101_20260626.json"
+
+SCREEN_DATE = "2026-06-22"
+SMALL_MEMBERS = ["AAA", "BBB"]
+
+
+def _load_yahoo_fixture(name: str) -> dict:
+    return json.loads((FIXTURE_YAHOO_DIR / name).read_text())
+
+
+def _seed_yahoo_fixture(bar_store: BarStore, bar_index: BarIndex, fixture: dict) -> None:
+    bars = [
+        RawBar(
+            fixture["symbol"], fixture["timeframe"], b["epoch"],
+            b["open"], b["high"], b["low"], b["close"], b["volume"],
+        )
+        for b in fixture["bars"]
+    ]
+    meta = bar_store.record(
+        symbol=fixture["symbol"], timeframe=fixture["timeframe"],
+        window_start_utc=fixture["start"], window_end_utc=fixture["end"],
+        feed="yahoo", bars=bars,
+    )
+    bar_index.insert(meta)
+
+
+def _register_fixture_universe(universe_dir: Path) -> UniverseStore:
+    universe_dir.mkdir(parents=True, exist_ok=True)
+    shutil.copy(REGISTERED_SNAPSHOT_PATH, universe_dir / REGISTERED_SNAPSHOT_PATH.name)
+    return UniverseStore(universe_dir)
+
+
+def _register_small_universe(universe_dir: Path, members: list[str]) -> UniverseStore:
+    store = UniverseStore(universe_dir)
+    store.record(
+        members=sorted(members), raw_members={m: m for m in members},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    return store
+
+
+def _wait_for_terminal(mgr: DeskScreenComputeManager, timeout: float = 5.0) -> dict:
+    deadline = time.time() + timeout
+    while time.time() < deadline:
+        snap = mgr.snapshot()
+        if snap is not None and snap["state"] != "running":
+            return snap
+        time.sleep(0.01)
+    raise AssertionError("desk screen compute job never reached a terminal state")
+
+
+@pytest.fixture
+def manager_env(tmp_path):
+    """Manager-level tests: no ``TestClient``/registry needed -- every dependency is passed
+    explicitly to ``manager.trigger(...)`` (the ``EdgeReportComputeManager``/
+    ``DeskTopupComputeManager`` per-call-injection precedent)."""
+    universe_store = _register_small_universe(tmp_path / "universe", SMALL_MEMBERS)
+    bar_store = BarStore(tmp_path / "bars")
+    bar_index = BarIndex(str(tmp_path / "index.db"))
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    screen_store = ScreenStore(tmp_path / "screen")
+    return universe_store, bar_store, bar_index, dataset_store, screen_store
+
+
+# ==================================================================================================
+# Manager mechanics -- a FAKE `compute_screen` gives deterministic, threading-free control.
+# ==================================================================================================
+
+
+def test_no_job_has_ever_run_snapshot_is_none():
+    assert DeskScreenComputeManager().snapshot() is None
+
+
+def test_trigger_members_total_is_known_synchronously_before_any_background_work(manager_env, monkeypatch):
+    """``members_total`` (the fixture universe's 2 members) is correct in the response returned
+    from ``trigger()`` itself -- known BEFORE the background thread even starts (the
+    ``DeskTopupComputeManager`` ``pairs_total`` precedent)."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+
+    started = threading.Event()
+    release = threading.Event()
+
+    def fake_compute_screen(*_args, **_kwargs):
+        started.set()
+        release.wait(timeout=5)
+        return {
+            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z",
+            "universe_snapshot_id": "x", "config_fingerprint": "y", "bar_store_signature": "z",
+            "rows": [], "skipped": [],
+        }
+
+    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
+
+    mgr = DeskScreenComputeManager()
+    result = mgr.trigger(
+        SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store,
+    )
+    assert result["started"] is True
+    assert result["compute"]["progress"]["members_total"] == len(SMALL_MEMBERS)
+    assert result["compute"]["screen_date"] == SCREEN_DATE
+    assert started.wait(timeout=5)
+    release.set()
+    _wait_for_terminal(mgr)
+    mgr.join_all(timeout=5)
+
+
+def test_trigger_with_no_universe_snapshot_is_an_honest_empty_job_that_completes(tmp_path):
+    universe_store = UniverseStore(tmp_path / "universe")
+    bar_store = BarStore(tmp_path / "bars")
+    bar_index = BarIndex(str(tmp_path / "index.db"))
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    screen_store = ScreenStore(tmp_path / "screen")
+
+    mgr = DeskScreenComputeManager()
+    result = mgr.trigger(
+        SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store,
+    )
+    assert result["started"] is True
+    assert result["compute"]["progress"]["members_total"] == 0
+
+    snap = _wait_for_terminal(mgr)
+    assert snap["state"] == "done"
+    assert snap["progress"]["members_done"] == 0
+    mgr.join_all(timeout=5)
+
+    records, errors = screen_store.list()
+    assert errors == [] and len(records) == 1
+    assert records[0]["universe_snapshot_id"] is None
+    assert records[0]["rows"] == [] and records[0]["skipped"] == []
+
+
+def test_second_trigger_while_running_returns_the_same_job_started_false(manager_env, monkeypatch):
+    """TC-7: single-flight."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+    started = threading.Event()
+    release = threading.Event()
+
+    def fake_compute_screen(*_args, **_kwargs):
+        started.set()
+        release.wait(timeout=5)
+        return {
+            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z",
+            "universe_snapshot_id": "x", "config_fingerprint": "y", "bar_store_signature": "z",
+            "rows": [], "skipped": [],
+        }
+
+    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
+
+    mgr = DeskScreenComputeManager()
+    first = mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    assert started.wait(timeout=5)
+
+    second = mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    assert second["started"] is False
+    assert second["compute"]["id"] == first["compute"]["id"]
+
+    release.set()
+    _wait_for_terminal(mgr)
+    mgr.join_all(timeout=5)
+
+
+def test_trigger_after_a_terminal_job_starts_a_genuinely_new_job(manager_env, monkeypatch):
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+    monkeypatch.setattr(
+        desk_screen_compute, "compute_screen",
+        lambda *a, **k: {
+            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
+            "config_fingerprint": "y", "bar_store_signature": "z", "rows": [], "skipped": [],
+        },
+    )
+
+    mgr = DeskScreenComputeManager()
+    first = mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    _wait_for_terminal(mgr)
+    mgr.join_all(timeout=5)
+
+    second = mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    assert second["started"] is True
+    assert second["compute"]["id"] != first["compute"]["id"]
+    _wait_for_terminal(mgr)
+    mgr.join_all(timeout=5)
+
+
+def test_a_cancellation_signal_resolves_state_cancelled_with_partial_progress_and_nothing_recorded(
+    manager_env, monkeypatch,
+):
+    """TC-8: cancel mid-flight -- state transitions to "cancelled" with fewer than members_total
+    processed, and (append-only) the partial walk is NEVER persisted as a screen snapshot."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+    started = threading.Event()
+    release = threading.Event()
+    calls: list[str] = []
+
+    def fake_compute_screen(_us, _bs, _bi, _ds, _cfg, _sd, *, progress=None, should_abort=None):
+        for symbol in SMALL_MEMBERS:
+            calls.append(symbol)
+            if len(calls) == 1:
+                started.set()
+                release.wait(timeout=5)
+            if should_abort is not None and should_abort():
+                break
+            if progress is not None:
+                progress({"symbol": symbol})
+        return {
+            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
+            "config_fingerprint": "y", "bar_store_signature": "z", "rows": [], "skipped": [],
+        }
+
+    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
+
+    mgr = DeskScreenComputeManager()
+    mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    assert started.wait(timeout=5)
+    mgr.cancel()
+    release.set()
+
+    snap = _wait_for_terminal(mgr)
+    assert snap["state"] == "cancelled"
+    assert snap["error"] is None
+    assert snap["progress"]["members_done"] < snap["progress"]["members_total"]
+    mgr.join_all(timeout=5)
+
+    records, _errors = screen_store.list()
+    assert records == [], "a cancelled (partial) walk must never be persisted"
+
+
+def test_an_unexpected_crash_resolves_state_failed(manager_env, monkeypatch):
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+
+    def fake_compute_screen(*_args, **_kwargs):
+        raise RuntimeError("synthetic catastrophic failure")
+
+    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
+
+    mgr = DeskScreenComputeManager()
+    mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    snap = _wait_for_terminal(mgr)
+
+    assert snap["state"] == "failed"
+    assert snap["error"] == "synthetic catastrophic failure"
+    mgr.join_all(timeout=5)
+    records, _errors = screen_store.list()
+    assert records == []
+
+
+def test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite(
+    manager_env, monkeypatch,
+):
+    """The job-level view of ``ScreenStore.record``'s integrity refusal: a re-trigger whose 5-pin
+    key lands on an already-corrupted file resolves ``"failed"`` with the explicit integrity error
+    -- never a silent overwrite, and never a fabricated ``"done"``."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+    monkeypatch.setattr(
+        desk_screen_compute, "compute_screen",
+        lambda *a, **k: {
+            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
+            "config_fingerprint": "y", "bar_store_signature": "z", "rows": [], "skipped": [],
+        },
+    )
+
+    mgr = DeskScreenComputeManager()
+    mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    assert _wait_for_terminal(mgr)["state"] == "done"
+    mgr.join_all(timeout=5)
+
+    path = next(Path(screen_store.root).glob("*.json"))
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["rows"] = [{"symbol": "AAPL", "band_class": "TAMPERED"}]
+    path.write_text(json.dumps(data))
+    tampered_bytes = path.read_bytes()
+
+    mgr2 = DeskScreenComputeManager()
+    mgr2.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    snap = _wait_for_terminal(mgr2)
+    mgr2.join_all(timeout=5)
+
+    assert snap["state"] == "failed"
+    assert "integrity" in snap["error"]
+    assert path.read_bytes() == tampered_bytes
+    records, errors = screen_store.list()
+    assert records == [] and len(errors) == 1
+
+
+def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_reference(manager_env, monkeypatch):
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+    monkeypatch.setattr(
+        desk_screen_compute, "compute_screen",
+        lambda *a, **k: {
+            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
+            "config_fingerprint": "y", "bar_store_signature": "z", "rows": [], "skipped": [],
+        },
+    )
+
+    mgr = DeskScreenComputeManager()
+    mgr.trigger(SCREEN_DATE, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store)
+    snap = _wait_for_terminal(mgr)
+    snap["progress"]["current"] = "POISONED"
+
+    fresh = mgr.snapshot()
+    assert fresh["progress"]["current"] != "POISONED"
+    mgr.join_all(timeout=5)
+
+
+# ==================================================================================================
+# Append-only reuse (TC-4) + cancel-returns-None -- against the REAL compute_screen.
+# ==================================================================================================
+
+
+@pytest.fixture
+def real_ctx(tmp_path):
+    universe_store = _register_fixture_universe(tmp_path / "universe")
+    bar_store = BarStore(tmp_path / "bars")
+    bar_index = BarIndex(str(tmp_path / "index.db"))
+    _seed_yahoo_fixture(bar_store, bar_index, _load_yahoo_fixture(AAPL_DAILY_FIXTURE))
+    dataset_store = DatasetStore(tmp_path / "datasets")
+    screen_store = ScreenStore(tmp_path / "screen")
+    return universe_store, bar_store, bar_index, dataset_store, screen_store
+
+
+def test_first_run_screen_and_record_persists_a_new_snapshot(real_ctx):
+    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
+    recorded = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+    )
+    assert recorded is not None
+    assert any(r["symbol"] == "AAPL" for r in recorded["rows"])
+    records, errors = screen_store.list()
+    assert errors == [] and len(records) == 1 and records[0]["id"] == recorded["id"]
+
+
+def test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file(real_ctx, tmp_path):
+    """TC-4: the manager/store returns the EXISTING snapshot (same id) rather than writing a
+    second file."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
+    first = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+    )
+    second = run_screen_and_record(
+        UniverseStore(universe_store.root), BarStore(bar_store.root), BarIndex(bar_index.db_path),
+        DatasetStore(tmp_path / "datasets"), CONFIG, screen_store, SCREEN_DATE,
+    )
+    assert second["id"] == first["id"]
+    records, errors = screen_store.list()
+    assert errors == [] and len(records) == 1  # no second file
+
+
+def test_cancel_before_the_walk_starts_returns_none_and_records_nothing(real_ctx):
+    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
+    result = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+        should_abort=lambda: True,
+    )
+    assert result is None
... [diff_bound] apps/backend/tests/test_desk_screen_compute.py: 199 more diff lines omitted — Read the file for full detail
```
