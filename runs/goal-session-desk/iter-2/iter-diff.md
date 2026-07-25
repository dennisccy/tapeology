# Iteration diff (bounded)

Files changed: 8. Shown in full: 7.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_desk_topup_compute.py` (141 lines not shown)

```diff
diff --git a/README.md b/README.md
index 72c499d..21c7d5e 100644
--- a/README.md
+++ b/README.md
@@ -60,7 +60,8 @@ Current capabilities:
 - **Safe-by-default Edge Report** — opening the Structure page's Edge Report section, or asking the underlying research endpoint for the report directly, never risks silently starting that full computation as a side effect of simply loading a page — before this update, doing so could pin the backend near 100% CPU for hours with no warning shown anywhere. If a report has already been computed, it — or the honest "No edge-report cells yet." empty state — is shown exactly as before. If nothing has been computed yet, the panel instead shows a plain, prompt "Edge report not computed yet." message with a short explanation of why, answering promptly rather than spinning indefinitely or silently starting work in the background. Starting that computation is now a separate, explicit action — see the next capability.
 - **Operator-run edge report compute** — beneath the "Edge report not computed yet." message, a "Compute edge report" button starts the full three-strategy comparison as a background job without leaving the page. While it runs, a live counter shows how many of the comparison's individual backtests have finished so far — including how many were reused from already-completed work rather than recomputed — updating automatically with no manual refresh needed. When the computation completes, the finished report renders in place automatically, using the same table already shown for a previously-computed report. If the computation fails partway through, the panel shows the specific error message instead of a generic failure, and the button relabels itself so a fresh attempt is one more click away. Reloading the page, or landing on it, while a compute is running, or after one has already finished or failed, immediately shows the matching state rather than resetting to idle. A compute that is interrupted — by a server restart, a crash, or a cancellation — resumes cleanly when re-triggered: it skips every result already durably saved and computes only what's left, finishing far faster than starting over. The same computation can also be started, unattended, from the command line for long background runs, where it can be spread across several worker processes at once for a further speedup; the on-page button always runs single-process by design.
 - **Cockpit price-chart tradable bands and a descriptive confluence chip** — the tradable support/resistance bands from the Structure page's map now also draw directly on the live cockpit price chart while watching a symbol in Simulated or Historical mode: one or two solid price lines per band (rose for resistance, emerald for support), each labeled with side, class, quality score, and whether it sits on a round number — alongside the existing tape-state markers, without changing how those render. A small descriptive banner appears beneath the chart only when the last traded price sits inside one of those bands AND the live tape reading matches that band's configured rejection-or-breakthrough state — for example "Inside R-band 300.05–300.17 (class A) · tape: Ask Absorption (rejection) · measured history: edge report." The banner states the current condition and points to the edge report as measured history; it never tells you to buy or sell and never predicts an outcome. A simulated ticker with no real recorded price history shows an honest "No tradable map for TICKER" note instead of a fabricated band. Live mode is unchanged — the price chart, and therefore the bands and banner, stay hidden there exactly as before.
-- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `GET /research/taxonomy`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/bars/{id}/candles`, `GET /research/candles`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `GET /meta/ui-routes`.
+- **S&P 100 universe snapshot fetch and registry (research API)** — on explicit request, fetch the current S&P 100 constituent list from a public source (Wikipedia) and validate it (a real company-symbol table, roughly 90–110 names, no garbled entries), refusing with a specific explanation on any anomaly rather than guessing or saving a partial list. A valid fetch is saved as a permanent, checksummed, dated snapshot; fetching identical membership again is recognized and refused rather than silently duplicated or overwritten. Dual-class tickers are normalized for use elsewhere in the app (for example `BRK.B` → `BRK-B`) while the original source form is kept in the snapshot's own record. A second call lists every saved snapshot and returns the most recent membership, honestly reporting that nothing has been fetched yet before the first run. There is no browser page for this yet; it is reachable through the research API and the matching machine-readable tool.
+- **REST and WebSocket API** — `POST /watch/{ticker}`, `DELETE /watch/{ticker}`, `POST /watch/{ticker}/pause`, `POST /watch/{ticker}/resume`, `POST /watch/{ticker}/speed`, `GET /tape/{ticker}/state`, `GET /tape/{ticker}/features`, `GET /tape/{ticker}/events`, `GET /tape/{ticker}/summary`, `GET /tape/{ticker}/history?bar=<10|30|60>`, `WS /tape/{ticker}/stream`, `GET /symbols/search`, `GET /market/clock`, `GET /research/taxonomy`, `POST /research/datasets`, `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`, `GET /research/backtests`, `GET /research/backtests/{id}`, `POST /research/backtests/{id}/cancel`, `GET /research/pnl/ledger`, `GET /research/profiles`, `GET /research/strategies`, `POST /research/bars`, `GET /research/bars`, `GET /research/bars/{id}`, `GET /research/bars/{id}/candles`, `GET /research/candles`, `GET /research/levels`, `GET /research/tradability`, `GET /research/setups`, `GET /research/setups/{id}`, `GET /research/edge-report`, `POST /research/edge-report/compute`, `GET /research/edge-report/compute`, `POST /research/edge-report/compute/cancel`, `POST /research/desk/universe/fetch`, `GET /research/desk/universe`, `GET /meta/ui-routes`.
 - **Machine-readable access for AI tools** — alongside the browser UI and REST API, a read-only connection (Model Context Protocol) lets AI assistants and other external tools query the exact same tape state, datasets, backtests, strategy registry, PnL ledger, bar series, support/resistance levels, tradable level maps, touch-event case studies, profit edge reports, and navigation data the REST API serves. Every value it returns matches the REST API exactly, nothing can ever be written or changed through it, and it surfaces an explicit error — never fabricated data — when the backend isn't reachable. The site's own top navigation bar is generated from that same canonical list of live pages rather than a hand-maintained one, and shows an honest notice instead of guessing if that list can't be reached.
 <!-- /AUTO:capabilities -->
 
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
diff --git a/apps/backend/app/research/desk_coverage.py b/apps/backend/app/research/desk_coverage.py
new file mode 100644
index 0000000..4775428
--- /dev/null
+++ b/apps/backend/app/research/desk_coverage.py
@@ -0,0 +1,69 @@
+"""Per-member x per-timeframe bar coverage over the latest universe snapshot (Era B "The Desk",
+Key Capability 2, J-02) -- the Product Shape's "Per-member bar coverage/freshness" row's ONE owner,
+served by ``GET /research/desk/coverage``.
+
+THIS MODULE computes NOTHING about bars themselves -- it is a pure READ over two already-canonical
+owners: the latest registered universe snapshot (``desk_universe.UniverseStore`` -- membership,
+J-01) and the durable bar-lookup index (``bar_index.BarIndex`` -- coverage/freshness, era-5 J-03).
+T-4 (goal.md's build anchors): coverage is read from ``bar_index`` ONLY, via
+``BarIndex.coverage()`` (a single indexed ``COUNT``+``MAX`` query per pair) -- it NEVER walks or
+re-hashes the checksummed JSON ``BarStore`` (the era-5C 31.4s mistake this anchor exists to avoid).
+
+**The pinned top-up timeframe set.** ``DESK_TOPUP_TIMEFRAMES`` is a plain structural constant (the
+``levels.PRIOR_PERIOD_TIMEFRAMES`` precedent) -- NOT a ``Config`` field, since it is derived
+entirely from the existing frozen contract rather than a new tunable knob. Re-verified live against
+the tree this iteration (goal-desk-iter-2 spec NOTES): ``Config.bar_timeframes``
+(``config.py:770``, the full 9-entry validation allowlist) intersected with what the Yahoo adapter
+actually serves (``providers/adapters/yahoo.py``'s ``_INTERVAL_MAP``, 5 direct entries -- ``1d``,
+``1w``, ``1h``, ``5m``, ``1m`` -- plus the locally-resampled ``4h``; ``8h``/``15m``/``1mo`` raise
+``UnsupportedTimeframe``) and further narrowed to the non-intraday-microscope subset a DAILY-CLOSE
+screen needs (excluding ``5m``/``1m`` per the desk-era's own explicit "no 5m/1m in the desk top-up"
+acceptance text; ``levels.PRIOR_PERIOD_TIMEFRAMES`` / ``config.py``'s ``sr_timeframe_weights``,
+``config.py:821``, confirm ``1d``/``1w`` are the long-term bucket these four timeframes feed) --
+leaving exactly ``{"1h", "4h", "1d", "1w"}``.
+
+**Honest empty.** Before any universe snapshot is ever registered, ``get_desk_coverage`` returns
+the SAME honest-empty shape ``GET /research/desk/universe`` uses (``universe_snapshot_id: None``,
+``members: []``) -- HTTP 200, never 404 or a fabricated row (mirrors J-01's own convention)."""
+
+from __future__ import annotations
+
+from .bar_index import BarIndex
+from .desk_universe import UniverseStore
+
+# The desk top-up's pinned timeframe set -- see module docstring for the full citation trail.
+# Order is the fixed iteration order both this module and ``desk_topup_compute.py`` use.
+DESK_TOPUP_TIMEFRAMES: tuple[str, ...] = ("1h", "4h", "1d", "1w")
+
+
+def get_desk_coverage(universe_store: UniverseStore, bar_index: BarIndex) -> dict:
+    """The latest universe snapshot's per-member x per-``DESK_TOPUP_TIMEFRAMES`` coverage, read
+    ENTIRELY from ``bar_index`` (T-4). Shape (Data-contract addition #1, goal-desk-iter-2 spec):
+    ``{"universe_snapshot_id": str | None, "timeframes": [...], "members": [{"symbol": str,
+    "per_timeframe": {"<tf>": {"has_bars": bool, "latest_window_end_utc": str | None}}}]}``.
+
+    Honest empty (``universe_snapshot_id: None``, ``members: []``) before any universe snapshot
+    has ever been registered -- the caller (the route) serves this as an HTTP 200, never a 404
+    (mirrors ``get_universe``'s convention, ``desk_routes.py``)."""
+    records, _errors = universe_store.list()
+    timeframes = list(DESK_TOPUP_TIMEFRAMES)
+    if not records:
+        return {"universe_snapshot_id": None, "timeframes": timeframes, "members": []}
+
+    latest = records[-1]
+    members: list[dict] = []
+    for symbol in latest["members"]:
+        per_timeframe: dict[str, dict] = {}
+        for timeframe in DESK_TOPUP_TIMEFRAMES:
+            has_bars, latest_window_end_utc = bar_index.coverage(symbol, timeframe)
+            per_timeframe[timeframe] = {
+                "has_bars": has_bars,
+                "latest_window_end_utc": latest_window_end_utc,
+            }
+        members.append({"symbol": symbol, "per_timeframe": per_timeframe})
+
+    return {
+        "universe_snapshot_id": latest["id"],
+        "timeframes": timeframes,
+        "members": members,
+    }
diff --git a/apps/backend/app/research/desk_topup_compute.py b/apps/backend/app/research/desk_topup_compute.py
new file mode 100644
index 0000000..6ebde21
--- /dev/null
+++ b/apps/backend/app/research/desk_topup_compute.py
@@ -0,0 +1,376 @@
+"""Era B "The Desk" (J-02) — the desk bar top-up: a single-flight, cancellable, progress-reporting
+background job that walks the latest universe snapshot's members x the pinned
+``desk_coverage.DESK_TOPUP_TIMEFRAMES`` set, in-process, through the SAME existing
+``record_bar_series`` fetch-and-record logic ``POST /research/bars`` already uses (store-first,
+resumable, unmodified) — never a second fetch-and-record implementation. Plus a CLI warmer that
+drives the SAME walk synchronously, in-process, for the operator's real ~100-symbol run.
+
+Mirrors ``edge_report_compute.EdgeReportComputeManager`` verbatim in shape: one in-flight job slot
+(``self._snapshot``), an in-memory, process-scoped progress snapshot
+(``id``/``state``/``started_utc``/``finished_utc``/``error``/``progress``), cooperative cancel, an
+atomic snapshot publish under a lock (a fresh dict rebound in ONE assignment, never mutated in
+place) so a concurrent reader's ``snapshot()`` call always sees a caller-safe, internally
+consistent copy. Job state is process-scoped bookkeeping — honestly lost on restart, never a
+research value (the SAME contract every compute manager in this app already carries).
+
+**THIS MODULE MUST NOT be imported by ``routes.py``.** ``record_bar_series`` — the fetch-and-record
+logic this module reuses — lives in ``routes.py``, so this module imports FROM ``routes.py`` (a
+one-way edge). If ``routes.py`` (or ``ResearchRegistry``) imported anything back from this module,
+that would be a circular import; consequently the ``DeskTopupComputeManager`` INSTANCE does NOT
+live on ``ResearchRegistry`` (unlike ``EdgeReportComputeManager``) — it lives as a module-level
+singleton behind a FastAPI dependency in ``desk_routes.py``, test-overridable exactly like
+``get_universe_fetcher``.
+
+**Resumability comes from ``record_bar_series``'s OWN store-first coordinator, not from job-level
+checkpoint bookkeeping.** A cancelled run's ``outcomes`` list simply has fewer than ``pairs_total``
+entries; a FRESH ``trigger()`` call (a new job, from scratch) walks every pair again, but every pair
+already recorded during the earlier attempt now answers "reused" with zero vendor calls — the SAME
+index-backed store-first hit ``POST /research/bars`` already guarantees. No separate "resume from
+pair N" bookkeeping exists, or is needed.
+
+**Determining "reused" vs "fetched" without re-deriving ``record_bar_series``'s own internal
+adapter/feed-resolution logic.** ``record_bar_series`` returns the SAME ``{"bar_series": meta}``
+shape whether it answered store-first or ran a real vendor fetch — so this module classifies the
+outcome by comparing the returned series' ``created_utc`` (stamped by ``BarStore.record`` at
+``datetime.now(timezone.utc)`` the instant a NEW series is written) against a timestamp captured
+immediately BEFORE the call: a store-first hit's ``created_utc`` necessarily predates that
+timestamp (the series already existed), while a freshly-written series' ``created_utc`` is stamped
+at or after it. This reads only the ALREADY-RETURNED ``created_utc`` field — it duplicates none of
+``record_bar_series``'s own adapter-selection/feed-derivation decisions, so it cannot drift out of
+sync with that logic."""
+
+from __future__ import annotations
+
+import argparse
+import sys
+import threading
+import uuid
+from datetime import datetime, timedelta, timezone
+from typing import Callable
+
+from fastapi import HTTPException
+
+from ..config import CONFIG
+from .bar_index import BarIndex
+from .bars import BarStore
+from .desk_coverage import DESK_TOPUP_TIMEFRAMES
+from .desk_universe import UniverseStore
+from .routes import (
+    BarRecordRequest,
+    ResearchRegistry,
+    get_bar_index,
+    get_bar_store,
+    record_bar_series,
+)
+from .store import JournalStore
+
+__all__ = ["DeskTopupComputeManager", "run_topup"]
+
+# The top-up's fetch horizon — a SINGLE wide lookback shared by all four pinned timeframes, chosen
+# to match the Yahoo adapter's OWN ``1h``/``4h`` retention ceiling
+# (``providers/adapters/yahoo.py:95`` — ``_INTERVAL_LIMITS["1h"] == (730, 730)``), so a ``1h``/
+# ``4h`` request asks for exactly what the vendor can serve; ``1d``/``1w`` are unlimited, but 730
+# days is already ample history for a daily-close screen (``levels.PRIOR_PERIOD_TIMEFRAMES`` only
+# ever needs the most recently CLOSED period). A plain module constant, not a ``Config`` field —
+# the SAME "not a fingerprint-stability field" rationale ``yahoo.py``'s own ``_INTERVAL_LIMITS``
+# carries: it shapes no persisted tape/backtest/study value, only which bars a top-up call happens
+# to ASK the vendor for; the adapter's OWN ``_clamp_to_retention`` still honestly trims/notes any
+# further shortfall, exactly as it already does for a manual ``POST /research/bars`` call. This
+# module needs no per-timeframe retention table of its own — the adapter already owns that.
+_TOPUP_LOOKBACK_DAYS = 730
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
+def _fetch_window_now() -> tuple[str, str]:
+    """The ``[start, end]`` ISO window every top-up pair requests: ``end`` = today (UTC calendar
+    date), ``start`` = ``_TOPUP_LOOKBACK_DAYS`` earlier. Deliberately wall-clock: an operator-run
+    top-up asking "what bars exist as of today" is the SAME act as a manual ``POST /research/bars``
+    call with today's date — goal.md's T-6 no-wall-clock rule scopes to a SCREEN's ``as_of``
+    (J-03's determinism contract), never to a plain bar-fetch window (which the vendor adapter's
+    own retention clamp already honestly bounds/notes)."""
+    now = datetime.now(timezone.utc)
+    end = now.date().isoformat() + "T00:00:00Z"
+    start = (now - timedelta(days=_TOPUP_LOOKBACK_DAYS)).date().isoformat() + "T00:00:00Z"
+    return start, end
+
+
+def _parse_iso(value: str) -> datetime:
+    return datetime.fromisoformat(value.replace("Z", "+00:00"))
+
+
+def _copy_snapshot(snapshot: dict) -> dict:
+    """A caller-safe copy (the ``progress.outcomes`` list is fresh too) so a reader mutating what
+    ``snapshot()`` returns can never poison ``DeskTopupComputeManager``'s own internal state (the
+    ``EdgeReportComputeManager._copy_snapshot`` precedent)."""
+    progress = snapshot["progress"]
+    return {
+        **snapshot,
+        "progress": {**progress, "outcomes": [dict(entry) for entry in progress["outcomes"]]},
+    }
+
+
+# --- the shared walker -- the SOLE computer of a top-up's outcomes; the manager and the CLI both
+# call this and nothing else --------------------------------------------------------------------
+
+
+def _run_one_pair(
+    symbol: str,
+    timeframe: str,
+    bar_store: BarStore,
+    bar_index: BarIndex,
+    registry: ResearchRegistry,
+) -> tuple[str, str | None]:
+    """Fetch+record ONE ``(symbol, timeframe)`` pair through ``record_bar_series`` (in-process —
+    never a second fetch-and-record implementation) and classify the honest outcome:
+
+      * ``"reused"``  — ``record_bar_series`` answered store-first (its own ``bar_index``-backed
+        coordinator), zero vendor calls.
+      * ``"fetched"`` — a real vendor call ran and a BRAND NEW series was recorded.
+      * ``"failed"``  — ``record_bar_series`` raised (the existing ``NoDataForWindow``/
+        ``VendorTimeout``/``UnsupportedTimeframe`` taxonomy, all converted to ``HTTPException``
+        inside ``record_bar_series``, or any other unexpected error) — the detail is preserved
+        verbatim, never swallowed, and the caller (``run_topup``) continues to the remaining pairs
+        rather than aborting the whole job."""
+    start, end = _fetch_window_now()
+    body = BarRecordRequest(symbol=symbol, timeframe=timeframe, start=start, end=end)
+    t_before = datetime.now(timezone.utc)
+    try:
+        result = record_bar_series(body=body, registry=registry, store=bar_store, index=bar_index)
+    except HTTPException as exc:
+        return "failed", str(exc.detail)
+    except Exception as exc:  # noqa: BLE001 -- never swallowed, never aborts the whole run (TC-14)
+        return "failed", str(exc)
+
+    created_utc = result["bar_series"].get("created_utc")
+    created = _parse_iso(created_utc) if created_utc else None
+    if created is not None and created >= t_before:
+        return "fetched", None
+    return "reused", None
+
+
+def run_topup(
+    members: list[str],
+    bar_store: BarStore,
+    bar_index: BarIndex,
+    registry: ResearchRegistry,
+    *,
+    progress: Callable[[dict], None] | None = None,
+    should_abort: Callable[[], bool] | None = None,
+) -> list[dict]:
+    """Walk ``members x DESK_TOPUP_TIMEFRAMES``, in order, calling ``_run_one_pair`` for each pair
+    — the SOLE walker; ``DeskTopupComputeManager`` and the CLI warmer both call this and nothing
+    else (the ``run_strategy_comparison_report`` precedent). Returns the list of per-pair outcome
+    dicts (``{"symbol", "timeframe", "outcome", "detail"}``), in iteration order.
+
+    ``progress``, if given, is called after EACH pair with the outcome dict just appended (so a
+    caller can publish incremental state). ``should_abort``, if given and it returns ``True``
+    BEFORE a pair starts, stops the walk early — the returned list is simply shorter than
+    ``len(members) * len(DESK_TOPUP_TIMEFRAMES)``; a cooperative stop, never a raise (there is no
+    cache-publish step here to protect, unlike ``run_strategy_comparison_report``'s
+    ``EdgeReportComputeCancelled``)."""
+    outcomes: list[dict] = []
+    for symbol in members:
+        for timeframe in DESK_TOPUP_TIMEFRAMES:
+            if should_abort is not None and should_abort():
+                return outcomes
+            outcome, detail = _run_one_pair(symbol, timeframe, bar_store, bar_index, registry)
+            entry = {"symbol": symbol, "timeframe": timeframe, "outcome": outcome, "detail": detail}
+            outcomes.append(entry)
+            if progress is not None:
+                progress(entry)
+    return outcomes
+
+
+class DeskTopupComputeManager:
+    """Owns the SINGLE in-flight (or last-terminal) desk top-up job. Construct with no arguments —
+    every ``trigger()`` call takes its stores/registry explicitly (the ``EdgeReportComputeManager``
+    per-call-injection precedent), so a test (or a future second registry) points this at any
+    hermetic store set with zero constructor plumbing."""
+
+    def __init__(self) -> None:
+        self._lock = threading.Lock()
+        self._snapshot: dict | None = None
+        self._cancel_event: threading.Event | None = None
+        self._thread: threading.Thread | None = None
+
+    def snapshot(self) -> dict | None:
+        """The current/last job's snapshot, or ``None`` if none has ever run — a caller-safe copy,
+        never a shared mutable reference."""
+        current = self._snapshot  # read-local-reference-before-inspect
+        if current is None:
+            return None
+        return _copy_snapshot(current)
+
+    def trigger(
+        self,
+        universe_store: UniverseStore,
+        bar_store: BarStore,
+        bar_index: BarIndex,
+        registry: ResearchRegistry,
+    ) -> dict:
+        """Start a NEW top-up job over the LATEST universe snapshot's members, or — if one is
+        already ``state == "running"`` — return it UNCHANGED (``started: False``, single-flight).
+        Once the current job is terminal (done/cancelled/failed, or none has ever run), the NEXT
+        call always starts a genuinely new job (a fresh id), discarding the prior snapshot. Never
+        blocks — the walk runs on a dedicated worker thread, off the caller's thread, so an HTTP
+        route calling this returns immediately. No universe snapshot registered yet -> an honest
+        zero-pair job (``pairs_total: 0``) that resolves ``"done"`` immediately, never an error."""
+        with self._lock:
+            current = self._snapshot
+            if current is not None and current["state"] == "running":
+                return {"started": False, "compute": _copy_snapshot(current)}
+
+            records, _errors = universe_store.list()
+            members: list[str] = list(records[-1]["members"]) if records else []
+            pairs_total = len(members) * len(DESK_TOPUP_TIMEFRAMES)
+
+            job_id = uuid.uuid4().hex
+            cancel_event = threading.Event()
+            self._cancel_event = cancel_event
+            snapshot = {
+                "id": job_id,
+                "state": "running",
+                "started_utc": _iso_utc_now(),
+                "finished_utc": None,
+                "error": None,
+                "progress": {"pairs_total": pairs_total, "pairs_done": 0, "outcomes": []},
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
+                        **progress,
+                        "pairs_done": progress["pairs_done"] + 1,
+                        "outcomes": [*progress["outcomes"], entry],
+                    },
+                }
+
+        def _work() -> None:
+            try:
+                run_topup(
+                    members, bar_store, bar_index, registry,
+                    progress=_publish, should_abort=cancel_event.is_set,
+                )
+            except Exception as exc:  # noqa: BLE001 -- a catastrophic, unexpected failure OUTSIDE
+                # any single pair (per-pair failures are already caught inside run_topup and
+                # recorded as "failed" outcomes -- this only fires for something run_topup itself
+                # cannot recover from) -- surfaced verbatim, never swallowed.
+                self._resolve(job_id, "failed", error=str(exc))
+                return
+            self._resolve(job_id, "cancelled" if cancel_event.is_set() else "done", error=None)
+
+        thread = threading.Thread(target=_work, name=f"desk-topup-compute:{job_id}", daemon=True)
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
+            self._snapshot = {
+                **current,
+                "state": state,
+                "finished_utc": _iso_utc_now(),
+                "error": error,
+            }
+
+    def cancel(self) -> None:
+        """Signal cooperative cancellation for the in-flight job — a harmless no-op if idle (the
+        ROUTE is the one that rejects an idle cancel with a 409 — see ``desk_routes.py``)."""
+        with self._lock:
+            cancel_event = self._cancel_event
+        if cancel_event is not None:
+            cancel_event.set()
+
+    def join_all(self, timeout: float = 30.0) -> None:
+        """Wait for the in-flight job thread, if any (test/shutdown hygiene — the
+        ``EdgeReportComputeManager.join_all`` precedent)."""
+        with self._lock:
+            thread = self._thread
+        if thread is not None:
+            thread.join(timeout=timeout)
+
+
+# --- The CLI warmer ------------------------------------------------------------------------------
+# Mirrors ``edge_report_compute.py``'s own CLI precedent: resolves the SAME env/config seams the
+# backend reads, runs ``run_topup`` to completion SYNCHRONOUSLY in-process (no manager, no
+# background thread — a CLI invocation IS the one caller; there is nothing else to serialize
+# against), and exits 0 (or 1 on any failed pair) with a summary. Deliberately does NOT go through
+# ``DeskTopupComputeManager`` (single-flight/cancel/progress-polling exist to serve CONCURRENT HTTP
+# callers; a one-shot CLI process has none) — it calls ``run_topup`` directly, exactly like
+# ``edge_report_compute.main()`` calls ``run_strategy_comparison_report`` directly.
+
+
+def _cli_progress_printer() -> Callable[[dict], None]:
+    def _printer(entry: dict) -> None:
+        suffix = f" -- {entry['detail']}" if entry.get("detail") else ""
+        print(f"[{entry['symbol']} {entry['timeframe']}] {entry['outcome']}{suffix}", flush=True)
+
+    return _printer
+
+
+def main() -> int:
+    """The CLI entry: ``python -m app.research.desk_topup_compute``. Runs the top-up to completion
+    against the operator's real universe/bar dirs, for the operator's real ~100-symbol run. Prints
+    one progress line per completed pair; exits 1 (nothing recorded is lost either way — every
+    successful pair up to a failure stays recorded) if any pair's outcome is ``"failed"``, else 0."""
+    parser = argparse.ArgumentParser(
+        description="Era B \"The Desk\" J-02 CLI warmer -- top up bars for every member of the "
+        "latest registered universe snapshot across the pinned DESK_TOPUP_TIMEFRAMES set "
+        "(1h/4h/1d/1w), store-first, through the SAME POST /research/bars fetch-and-record logic "
+        "the route uses."
+    )
+    parser.parse_args()
+
+    config = CONFIG
+    store = JournalStore(config.journal_db_path_resolved(), config)
+    try:
+        registry = ResearchRegistry(store, config)
+        bar_store = get_bar_store()
+        bar_index = get_bar_index()
+        universe_store = UniverseStore(config.desk_universe_dir_resolved())
+
+        records, _errors = universe_store.list()
+        if not records:
+            print(
+                "no universe snapshot is registered -- nothing to top up (run "
+                "POST /research/desk/universe/fetch first)",
+                file=sys.stderr,
+            )
+            return 1
+        members = list(records[-1]["members"])
+        print(
+            f"desk top-up: {len(members)} member(s) x {len(DESK_TOPUP_TIMEFRAMES)} "
+            f"timeframe(s) = {len(members) * len(DESK_TOPUP_TIMEFRAMES)} pair(s)",
+            flush=True,
+        )
+        outcomes = run_topup(members, bar_store, bar_index, registry, progress=_cli_progress_printer())
+    finally:
+        store.close()
+
+    n_fetched = sum(1 for o in outcomes if o["outcome"] == "fetched")
+    n_reused = sum(1 for o in outcomes if o["outcome"] == "reused")
+    n_failed = sum(1 for o in outcomes if o["outcome"] == "failed")
+    print(f"desk top-up complete: {n_fetched} fetched, {n_reused} reused, {n_failed} failed.")
+    return 0 if n_failed == 0 else 1
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_desk_coverage.py b/apps/backend/tests/test_desk_coverage.py
new file mode 100644
index 0000000..b50de0f
--- /dev/null
+++ b/apps/backend/tests/test_desk_coverage.py
@@ -0,0 +1,198 @@
+"""``desk_coverage.py`` (Era B "The Desk", J-02) — the coverage-read module's own contract: the
+pinned timeframe set, honest-empty pre-universe, the per-member truth-table, freshness exactness,
+and the index-only latency guard (T-4). Direct construction (no FastAPI/TestClient — the
+``tests/test_bar_index.py``/``tests/test_desk_universe.py`` precedent); the route wiring is
+covered in ``tests/test_desk_topup_compute.py`` alongside the top-up routes.
+"""
+
+from __future__ import annotations
+
+from app.config import CONFIG
+from app.providers.adapters.base import RawBar
+from app.research.bar_index import BarIndex
+from app.research.bars import BarStore
+from app.research.desk_coverage import DESK_TOPUP_TIMEFRAMES, get_desk_coverage
+from app.research.desk_universe import UniverseStore
+from app.research.levels import PRIOR_PERIOD_TIMEFRAMES
+
+FIVE_MEMBERS = ["AAA", "BBB", "CCC", "DDD", "EEE"]
+COVERED = ["AAA", "BBB"]
+START, END = "2026-06-01T00:00:00Z", "2026-06-04T00:00:00Z"
+_BASE_EPOCH = 1780358400.0  # 2026-06-01T00:00:00Z
+
+
+def _register_universe(tmp_path, members: list[str]) -> UniverseStore:
+    store = UniverseStore(tmp_path / "universe")
+    store.record(
+        members=sorted(members),
+        raw_members={m: m for m in members},
+        source_url="https://example.invalid/constituents",
+        min_members=1,
+        max_members=999,
+    )
+    return store
+
+
+def _bar(symbol: str, timeframe: str, epoch: float) -> RawBar:
+    return RawBar(symbol, timeframe, epoch, 1.0, 1.5, 0.5, 1.2, 100)
+
+
+def _record_series(
+    bar_store: BarStore,
+    index: BarIndex,
+    symbol: str,
+    timeframe: str,
+    start: str,
+    end: str,
+    epoch_base: float,
+) -> dict:
+    bars = [_bar(symbol, timeframe, epoch_base), _bar(symbol, timeframe, epoch_base + 86400.0)]
+    meta = bar_store.record(
+        symbol=symbol, timeframe=timeframe, window_start_utc=start, window_end_utc=end,
+        feed="yahoo", bars=bars,
+    )
+    index.insert(meta)
+    return meta
+
+
+# --- the pinned timeframe set (re-verified, not re-derived) ------------------------------------
+
+
+def test_pinned_timeframe_set_matches_the_verified_live_derivation():
+    """The desk top-up's pinned set is a plain structural constant, re-verified against the live
+    tree (goal-desk-iter-2 NOTES) — never re-derived per iteration. Excludes 5m/1m (the desk-era's
+    own explicit acceptance text); 1d/1w are inside the PRIOR_PERIOD_TIMEFRAMES long-term bucket
+    (minus 1mo, which the Yahoo adapter does not serve at all)."""
+    assert DESK_TOPUP_TIMEFRAMES == ("1h", "4h", "1d", "1w")
+    assert set(DESK_TOPUP_TIMEFRAMES) <= set(CONFIG.bar_timeframes)
+    assert set(DESK_TOPUP_TIMEFRAMES) & {"5m", "1m"} == set()
+    assert {"1d", "1w"} <= set(PRIOR_PERIOD_TIMEFRAMES)
+
+
+# --- honest empty (TC-1) ------------------------------------------------------------------------
+
+
+def test_no_universe_snapshot_is_an_honest_empty_payload(tmp_path):
+    universe_store = UniverseStore(tmp_path / "universe")
+    index = BarIndex(str(tmp_path / "index.db"))
+
+    coverage = get_desk_coverage(universe_store, index)
+
+    assert coverage == {
+        "universe_snapshot_id": None,
+        "timeframes": list(DESK_TOPUP_TIMEFRAMES),
+        "members": [],
+    }
+
+
+def test_universe_with_no_bars_at_all_reports_has_bars_false_for_every_member_and_timeframe(tmp_path):
+    """TC-2: an empty bar store — every member reports ``has_bars == False`` on all four pinned
+    timeframes, asserted per-member (never a bulk/aggregate assertion)."""
+    universe_store = _register_universe(tmp_path, FIVE_MEMBERS)
+    index = BarIndex(str(tmp_path / "index.db"))
+
+    coverage = get_desk_coverage(universe_store, index)
+
+    assert coverage["universe_snapshot_id"] is not None
+    by_symbol = {m["symbol"]: m for m in coverage["members"]}
+    assert set(by_symbol) == set(FIVE_MEMBERS)
+    for symbol in FIVE_MEMBERS:
+        for timeframe in DESK_TOPUP_TIMEFRAMES:
+            entry = by_symbol[symbol]["per_timeframe"][timeframe]
+            assert entry == {"has_bars": False, "latest_window_end_utc": None}, (symbol, timeframe)
+
+
+# --- per-member truth-table (TC-3) ---------------------------------------------------------------
+
+
+def test_truth_table_exactly_the_covered_members_report_has_bars_true_on_all_four_timeframes(tmp_path):
+    universe_store = _register_universe(tmp_path, FIVE_MEMBERS)
+    bar_store = BarStore(tmp_path / "bars")
+    index = BarIndex(str(tmp_path / "index.db"))
+    for symbol in COVERED:
+        for timeframe in DESK_TOPUP_TIMEFRAMES:
+            _record_series(bar_store, index, symbol, timeframe, START, END, _BASE_EPOCH)
+
+    coverage = get_desk_coverage(universe_store, index)
+    by_symbol = {m["symbol"]: m for m in coverage["members"]}
+
+    for symbol in COVERED:
+        for timeframe in DESK_TOPUP_TIMEFRAMES:
+            assert by_symbol[symbol]["per_timeframe"][timeframe]["has_bars"] is True, (symbol, timeframe)
+    for symbol in set(FIVE_MEMBERS) - set(COVERED):
+        for timeframe in DESK_TOPUP_TIMEFRAMES:
+            entry = by_symbol[symbol]["per_timeframe"][timeframe]
+            assert entry == {"has_bars": False, "latest_window_end_utc": None}, (symbol, timeframe)
+
+
+# --- freshness exactness (TC-4) -------------------------------------------------------------------
+
+
+def test_latest_window_end_utc_matches_the_exact_recorded_bar_index_value(tmp_path):
+    universe_store = _register_universe(tmp_path, FIVE_MEMBERS)
+    bar_store = BarStore(tmp_path / "bars")
+    index = BarIndex(str(tmp_path / "index.db"))
+    _record_series(bar_store, index, "AAA", "1d", START, END, _BASE_EPOCH)
+
+    coverage = get_desk_coverage(universe_store, index)
+    by_symbol = {m["symbol"]: m for m in coverage["members"]}
+
+    assert by_symbol["AAA"]["per_timeframe"]["1d"]["latest_window_end_utc"] == END
+
+
+def test_latest_window_end_utc_is_the_max_across_multiple_recorded_windows(tmp_path):
+    """A symbol recorded twice at the SAME timeframe (e.g. an earlier top-up, then a later one)
+    reports the MOST RECENT window_end_utc, never the first or an arbitrary one."""
+    universe_store = _register_universe(tmp_path, ["AAA"])
+    bar_store = BarStore(tmp_path / "bars")
+    index = BarIndex(str(tmp_path / "index.db"))
+    _record_series(bar_store, index, "AAA", "1d", START, END, _BASE_EPOCH)
+    later_start, later_end = "2026-06-05T00:00:00Z", "2026-06-08T00:00:00Z"
+    _record_series(bar_store, index, "AAA", "1d", later_start, later_end, _BASE_EPOCH + 4 * 86400.0)
+
+    coverage = get_desk_coverage(universe_store, index)
+    by_symbol = {m["symbol"]: m for m in coverage["members"]}
+
+    assert by_symbol["AAA"]["per_timeframe"]["1d"]["latest_window_end_utc"] == later_end
+
+
+# --- index-only latency (TC-5) --------------------------------------------------------------------
+
+
+def test_coverage_issues_zero_bar_store_calls(tmp_path, monkeypatch):
+    """T-4: coverage is read from ``bar_index`` only — ``get_desk_coverage`` takes no ``BarStore``
+    reference at all, but this proves it directly (a call-counting guard) rather than relying on
+    signature inspection alone, so a future regression that reaches for ``BarStore`` as a fallback
+    is caught."""
+    universe_store = _register_universe(tmp_path, FIVE_MEMBERS)
+    bar_store = BarStore(tmp_path / "bars")
+    index = BarIndex(str(tmp_path / "index.db"))
+    for symbol in COVERED:
+        for timeframe in DESK_TOPUP_TIMEFRAMES:
+            _record_series(bar_store, index, symbol, timeframe, START, END, _BASE_EPOCH)
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
+    get_desk_coverage(universe_store, index)
+
+    assert calls == []
+
+
+def test_bar_index_coverage_accessor_is_additive_and_index_only(tmp_path):
+    """``BarIndex.coverage()`` (the new accessor this iteration adds) answers directly from SQLite
+    — a fresh, empty index reports ``(False, None)`` for any pair, never an error."""
+    index = BarIndex(str(tmp_path / "index.db"))
+    assert index.coverage("ZZZZ", "1d") == (False, None)
diff --git a/apps/backend/tests/test_desk_topup_compute.py b/apps/backend/tests/test_desk_topup_compute.py
new file mode 100644
index 0000000..762282d
--- /dev/null
+++ b/apps/backend/tests/test_desk_topup_compute.py
@@ -0,0 +1,535 @@
+"""``desk_topup_compute.py`` (Era B "The Desk", J-02) — the desk bar top-up: manager mechanics
+(single-flight, cancel, atomic progress) plus the store-first/resumability guarantee, plus the
+three HTTP routes.
+
+Manager-mechanics tests substitute a FAKE ``_run_one_pair`` (monkeypatched onto this module's own
+imported name — the ``test_edge_report_compute.py`` fake-swap precedent) for deterministic,
+threading-free control over timing. The store-first/resumability guarantee and the honest-failure
+taxonomy are proven end to end against the REAL ``record_bar_series`` path, through
+``app.dependency_overrides[get_market_adapter]`` injecting ``FakeAdapter`` (the
+``test_bars_api.py`` seam) — zero real network calls anywhere in this file. Route-level tests
+(``TestClient``) cover GET-never-computes (TC-10), single-flight/cancel through HTTP, and idle
+cancel returning 409 (TC-15) — the manager itself never raises on an idle cancel (the
+``cancel_edge_report_compute`` precedent: the ROUTE owns the 409).
+"""
+
+from __future__ import annotations
+
+import threading
+import time
+
+import pytest
+from fastapi.testclient import TestClient
+
+from app.config import CONFIG
+from app.main import app, get_market_adapter, manager as ws_manager
+from app.providers.adapters.base import NoDataForWindow
+from app.research import desk_topup_compute
+from app.research.bar_index import BarIndex
+from app.research.bars import BarStore
+from app.research.desk_coverage import DESK_TOPUP_TIMEFRAMES
+from app.research.desk_routes import get_desk_topup_manager
+from app.research.desk_topup_compute import DeskTopupComputeManager, run_topup
+from app.research.desk_universe import UniverseStore
+from app.research.routes import ResearchRegistry, set_registry
+from app.research.store import JournalStore
+from fakes import FakeAdapter
+
+TWO_MEMBERS = ["AAA", "BBB"]
+FIVE_MEMBERS = ["AAA", "BBB", "CCC", "DDD", "EEE"]
+
+
+def _bars():
+    from app.providers.adapters.base import RawBar
+
+    return (
+        RawBar("X", "1d", 1780358400.0, 100.0, 101.0, 99.0, 100.5, 1000),
+        RawBar("X", "1d", 1780444800.0, 100.5, 102.0, 100.0, 101.5, 1100),
+    )
+
+
+def _register_universe(tmp_path, members: list[str]) -> UniverseStore:
+    store = UniverseStore(tmp_path / "universe")
+    store.record(
+        members=sorted(members), raw_members={m: m for m in members},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    return store
+
+
+def _wait_for_terminal(mgr: DeskTopupComputeManager, timeout: float = 5.0) -> dict:
+    deadline = time.time() + timeout
+    while time.time() < deadline:
+        snap = mgr.snapshot()
+        if snap is not None and snap["state"] != "running":
+            return snap
+        time.sleep(0.01)
+    raise AssertionError("desk top-up compute job never reached a terminal state")
+
+
+@pytest.fixture
+def manager_env(tmp_path):
+    """Manager-level tests: no ``TestClient``/``set_registry`` needed — every dependency is passed
+    explicitly to ``manager.trigger(...)`` (the ``EdgeReportComputeManager`` per-call-injection
+    precedent), so this fixture stays fully isolated from the global registry singleton."""
+    universe_store = UniverseStore(tmp_path / "universe")
+    bar_store = BarStore(tmp_path / "bars")
+    bar_index = BarIndex(str(tmp_path / "index.db"))
+    journal = JournalStore(str(tmp_path / "journal.db"), CONFIG)
+    registry = ResearchRegistry(journal, CONFIG)
+    yield universe_store, bar_store, bar_index, registry
+    journal.close()
+    app.dependency_overrides.pop(get_market_adapter, None)
+
+
+def _inject_adapter(**kwargs) -> FakeAdapter:
+    adapter = FakeAdapter(**kwargs)
+    app.dependency_overrides[get_market_adapter] = lambda: adapter
+    return adapter
+
+
+# ==================================================================================================
+# Manager mechanics -- a FAKE `_run_one_pair` gives deterministic, threading-free control (never
+# wall-clock luck).
+# ==================================================================================================
+
+
+def test_no_job_has_ever_run_snapshot_is_none():
+    assert DeskTopupComputeManager().snapshot() is None
+
+
+def test_trigger_with_no_universe_snapshot_is_an_honest_zero_pair_job_that_completes(manager_env):
+    universe_store, bar_store, bar_index, registry = manager_env
+    mgr = DeskTopupComputeManager()
+
+    result = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    assert result["started"] is True
+    assert result["compute"]["progress"]["pairs_total"] == 0
+
+    snap = _wait_for_terminal(mgr)
+    assert snap["state"] == "done"
+    assert snap["progress"]["outcomes"] == []
+    mgr.join_all(timeout=5)
+
+
+def test_trigger_shape_pairs_total_equals_members_times_four(manager_env, monkeypatch):
+    """TC-6 (shape): ``pairs_total == N * len(DESK_TOPUP_TIMEFRAMES)``, known synchronously at
+    trigger time (before the background thread even starts)."""
+    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store.record(
+        members=sorted(FIVE_MEMBERS), raw_members={m: m for m in FIVE_MEMBERS},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+
+    def fake_one_pair(symbol, timeframe, *_args):
+        return "fetched", None
+
+    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)
+
+    mgr = DeskTopupComputeManager()
+    result = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    assert result["compute"]["progress"]["pairs_total"] == len(FIVE_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
+
+    snap = _wait_for_terminal(mgr)
+    assert snap["state"] == "done"
+    outcomes = snap["progress"]["outcomes"]
+    assert len(outcomes) == len(FIVE_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
+    assert {o["outcome"] for o in outcomes} == {"fetched"}
+    assert {(o["symbol"], o["timeframe"]) for o in outcomes} == {
+        (s, tf) for s in FIVE_MEMBERS for tf in DESK_TOPUP_TIMEFRAMES
+    }
+    mgr.join_all(timeout=5)
+
+
+def test_second_trigger_while_running_returns_the_same_job_started_false(manager_env, monkeypatch):
+    """TC-9: single-flight."""
+    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store.record(
+        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    started = threading.Event()
+    release = threading.Event()
+
+    def fake_one_pair(symbol, timeframe, *_args):
+        started.set()
+        release.wait(timeout=5)
+        return "fetched", None
+
+    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)
+
+    mgr = DeskTopupComputeManager()
+    first = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    assert started.wait(timeout=5)
+
+    second = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    assert second["started"] is False
+    assert second["compute"]["id"] == first["compute"]["id"]
+
+    release.set()
+    _wait_for_terminal(mgr)
+    mgr.join_all(timeout=5)
+
+
+def test_trigger_after_a_terminal_job_starts_a_genuinely_new_job(manager_env, monkeypatch):
+    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store.record(
+        members=["AAA"], raw_members={"AAA": "AAA"},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", lambda *a: ("fetched", None))
+
+    mgr = DeskTopupComputeManager()
+    first = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    _wait_for_terminal(mgr)
+    mgr.join_all(timeout=5)
+
+    second = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    assert second["started"] is True
+    assert second["compute"]["id"] != first["compute"]["id"]
+    _wait_for_terminal(mgr)
+    mgr.join_all(timeout=5)
+
+
+def test_a_cancellation_signal_resolves_state_cancelled_with_the_partial_outcomes_recorded(
+    manager_env, monkeypatch
+):
+    """Cancellation mechanics: the worker observes ``should_abort`` BETWEEN pairs and stops early
+    -- the job resolves ``"cancelled"`` with exactly the outcomes recorded before the signal fired,
+    never a raise, never a fabricated remaining outcome."""
+    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store.record(
+        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    started = threading.Event()
+    release = threading.Event()
+    calls: list[tuple[str, str]] = []
+
+    def fake_one_pair(symbol, timeframe, *_args):
+        calls.append((symbol, timeframe))
+        if len(calls) == 2:
+            started.set()
+            release.wait(timeout=5)
+        return "fetched", None
+
+    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)
+
+    mgr = DeskTopupComputeManager()
+    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    assert started.wait(timeout=5)
+    mgr.cancel()
+    release.set()
+
+    snap = _wait_for_terminal(mgr)
+    assert snap["state"] == "cancelled"
+    assert snap["error"] is None
+    assert len(snap["progress"]["outcomes"]) == 2  # the 2 pairs already in flight when cancel fired
+    mgr.join_all(timeout=5)
+
+
+def test_an_unexpected_crash_outside_run_topup_resolves_state_failed(manager_env, monkeypatch):
+    """Safety net: a failure that ``run_topup`` itself cannot recover from (never a per-pair
+    outcome -- those are caught inside ``_run_one_pair``) resolves the WHOLE job ``"failed"``, the
+    message surfaced verbatim (the ``EdgeReportComputeManager`` precedent)."""
+    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store.record(
+        members=["AAA"], raw_members={"AAA": "AAA"},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+
+    def fake_run_topup(*args, **kwargs):
+        raise RuntimeError("synthetic catastrophic failure")
+
+    monkeypatch.setattr(desk_topup_compute, "run_topup", fake_run_topup)
+
+    mgr = DeskTopupComputeManager()
+    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    snap = _wait_for_terminal(mgr)
+
+    assert snap["state"] == "failed"
+    assert snap["error"] == "synthetic catastrophic failure"
+    mgr.join_all(timeout=5)
+
+
+def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_reference(manager_env, monkeypatch):
+    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store.record(
+        members=["AAA"], raw_members={"AAA": "AAA"},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", lambda *a: ("fetched", None))
+
+    mgr = DeskTopupComputeManager()
+    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    snap = _wait_for_terminal(mgr)
+    snap["progress"]["outcomes"].append({"poison": True})
+    snap["progress"]["outcomes"][0]["outcome"] = "POISONED"
+
+    fresh = mgr.snapshot()
+    assert len(fresh["progress"]["outcomes"]) == 4  # AAA x 4 timeframes -- the mutation above is invisible
+    assert all(o["outcome"] != "POISONED" for o in fresh["progress"]["outcomes"])
+    mgr.join_all(timeout=5)
+
+
+# ==================================================================================================
+# Store-first / resumability + honest failure -- against the REAL record_bar_series path, via
+# FakeAdapter (zero network).
+# ==================================================================================================
+
+
+def test_first_run_fetches_every_pair_and_records_it(manager_env):
+    """TC-6 mechanics (real path): a fresh store, every pair genuinely fetched."""
+    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store.record(
+        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    adapter = _inject_adapter(bars=_bars())
+
+    mgr = DeskTopupComputeManager()
+    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    snap = _wait_for_terminal(mgr)
+
+    assert snap["state"] == "done"
+    outcomes = snap["progress"]["outcomes"]
+    assert len(outcomes) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
+    assert {o["outcome"] for o in outcomes} == {"fetched"}
+    assert len(adapter.fetch_bars_calls) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
+    mgr.join_all(timeout=5)
+
+
+def test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls(manager_env):
+    """TC-7: store-first proven end to end."""
+    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store.record(
+        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    adapter = _inject_adapter(bars=_bars())
+
+    first_mgr = DeskTopupComputeManager()
+    first_mgr.trigger(universe_store, bar_store, bar_index, registry)
+    _wait_for_terminal(first_mgr)
+    first_mgr.join_all(timeout=5)
+    calls_after_first_run = len(adapter.fetch_bars_calls)
+    assert calls_after_first_run == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
+
+    second_mgr = DeskTopupComputeManager()
+    second_mgr.trigger(universe_store, bar_store, bar_index, registry)
+    snap = _wait_for_terminal(second_mgr)
+
+    assert snap["state"] == "done"
+    outcomes = snap["progress"]["outcomes"]
+    assert len(outcomes) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
+    assert {o["outcome"] for o in outcomes} == {"reused"}
+    assert len(adapter.fetch_bars_calls) == calls_after_first_run  # zero NEW vendor calls
+    second_mgr.join_all(timeout=5)
+
+
+def test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_resumability_guarantee(
+    manager_env,
+):
+    """TC-8 (the resumability GUARANTEE): resumability in this design comes entirely from
+    ``record_bar_series``'s own store-first coordinator, not from job-level "resume from pair N"
+    bookkeeping -- so this test proves the guarantee directly (deterministic, no threading): M
+    pairs are recorded FIRST (standing in for an earlier top-up run that was cancelled after
+    completing them), then a FRESH top-up trigger runs over ALL pairs. Those M pairs must report
+    "reused" with no growth in vendor calls; the rest must report "fetched". (The cancellation
+    MECHANISM itself -- state transitions to "cancelled" with a partial outcomes list -- is proven
+    separately, above, with a deterministic mocked fake.)"""
+    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store.record(
+        members=sorted(FIVE_MEMBERS), raw_members={m: m for m in FIVE_MEMBERS},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    adapter = _inject_adapter(bars=_bars())
+
+    # Pre-populate exactly the pairs an earlier, cancelled run would already have completed: every
+    # timeframe for the first 2 (of 5) members, in the SAME iteration order run_topup itself uses
+    # -- via the SAME real record_bar_series path (run_topup directly, zero shortcuts), standing
+    # in for what an earlier top-up job would have already written to the store before a cancel.
+    pre_populated = [(s, tf) for s in sorted(TWO_MEMBERS) for tf in DESK_TOPUP_TIMEFRAMES]
+    run_topup(sorted(TWO_MEMBERS), bar_store, bar_index, registry)
+    calls_after_prepopulate = len(adapter.fetch_bars_calls)
+    assert calls_after_prepopulate == len(pre_populated)
+
+    mgr = DeskTopupComputeManager()
+    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    snap = _wait_for_terminal(mgr)
+
+    assert snap["state"] == "done"
+    by_pair = {(o["symbol"], o["timeframe"]): o["outcome"] for o in snap["progress"]["outcomes"]}
+    for pair in pre_populated:
+        assert by_pair[pair] == "reused", pair
+    remaining = [(s, tf) for s in sorted(FIVE_MEMBERS) if s not in TWO_MEMBERS for tf in DESK_TOPUP_TIMEFRAMES]
+    for pair in remaining:
+        assert by_pair[pair] == "fetched", pair
+    # Only the REMAINING pairs made a new vendor call -- the pre-populated ones did not.
+    assert len(adapter.fetch_bars_calls) == calls_after_prepopulate + len(remaining)
+    mgr.join_all(timeout=5)
+
+
+def test_a_failing_pair_reports_failed_with_the_detail_preserved_and_the_run_continues(manager_env):
+    """TC-14: an honest per-pair vendor failure never aborts the whole job, and the detail is
+    preserved verbatim -- proven with a small local adapter double that fails on exactly ONE call
+    (never all of them), so "the run continues to the remaining pairs" is genuinely distinguishable
+    from "the job stopped after the first failure"."""
+
+    class _NthCallFailsAdapter:
+        name = "fake"
+
+        def __init__(self, bars, fail_on_call_index: int, exc: Exception) -> None:
+            self._bars = bars
+            self._fail_on = fail_on_call_index
+            self._exc = exc
+            self.fetch_bars_calls: list[tuple] = []
+
+        def is_available(self) -> bool:
+            return True
+
+        def fetch_bars(self, symbol, start, end, timeframe):
+            self.fetch_bars_calls.append((symbol, start, end, timeframe))
+            if len(self.fetch_bars_calls) == self._fail_on:
+                raise self._exc
... [diff_bound] apps/backend/tests/test_desk_topup_compute.py: 141 more diff lines omitted — Read the file for full detail
```
