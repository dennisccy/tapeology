# Iteration diff (bounded)

Files changed: 9. Shown in full: 8.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_desk_topup_compute.py` (218 lines not shown)

```diff
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 5027fdd..dd834da 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -13,14 +13,21 @@ shape) and the desk bar top-up's three compute-manager routes (``POST``/``GET
 /research/desk/topup/compute``, ``POST /research/desk/topup/compute/cancel`` — mirrors
 ``routes.py``'s ``/edge-report/compute`` trio verbatim).
 
-J-03 (this iteration) adds the screen: ``GET /research/desk/screen`` (latest + ``?date=`` + a
-lightweight meta-only snapshot list — never full ``rows``/``skipped`` for every historical
+J-03 (unmodified this iteration) adds the screen: ``GET /research/desk/screen`` (latest + ``?date=``
++ a lightweight meta-only snapshot list — never full ``rows``/``skipped`` for every historical
 snapshot, see ``desk_screen.py``'s module docstring) and the screen's own three compute-manager
 routes (``POST``/``GET /research/desk/screen/compute``, ``POST
 /research/desk/screen/compute/cancel`` — mirrors the top-up trio exactly). Kept as its own module
 (mirroring the plan's stated preference) rather than folding into ``routes.py``, which is already
 large; mounted separately in ``app/main.py``.
 
+J-09 (this iteration) adds ONE new read: ``GET /research/desk/topup/runs`` (the durable, append-only
+top-up run log — ``desk_topup_log.py``'s lightweight run-meta list + the latest full record; honest-
+empty ``{"runs": [], "latest": null}`` before any run, never a 404). No new compute manager, no new
+POST — the log is written by the ALREADY-existing top-up trigger/CLI paths (``desk_topup_compute.py``
+threads the write through internally); this route is a pure read, mirroring ``GET
+/research/desk/universe``'s single-synchronous-read shape exactly.
+
 **Both compute managers are module-level singletons here, NOT ``ResearchRegistry`` properties.**
 ``DeskTopupComputeManager`` (``desk_topup_compute.py``) reuses ``routes.record_bar_series``
 in-process, so it must import FROM ``routes.py`` — if ``ResearchRegistry`` held the manager (the
@@ -46,6 +53,7 @@ from .desk_coverage import get_desk_coverage
 from .desk_screen import ScreenStore, resolve_desk_screen_dir
 from .desk_screen_compute import DeskScreenComputeManager
 from .desk_topup_compute import DeskTopupComputeManager
+from .desk_topup_log import TopupRunStore, resolve_desk_topup_log_dir
 from .desk_universe import (
     UniverseAlreadyRegistered,
     UniverseFetchError,
@@ -176,6 +184,14 @@ def get_desk_topup_manager() -> DeskTopupComputeManager:
     return _desk_topup_manager
 
 
+def get_topup_run_store() -> TopupRunStore:
+    """The top-up run log store rooted at a bare env-var-or-sibling-of-the-universe-dir default
+    (zero new ``Config`` field — J-09, see ``desk_topup_log.resolve_desk_topup_log_dir``) — the
+    ``get_screen_store`` pattern. A FastAPI dependency so tests can point it at a temp dir via the
+    env var or override it outright."""
+    return TopupRunStore(resolve_desk_topup_log_dir(CONFIG.desk_universe_dir_resolved()))
+
+
 @router.post("/topup/compute")
 def trigger_desk_topup_compute(
     universe_store: UniverseStore = Depends(get_universe_store),
@@ -183,13 +199,16 @@ def trigger_desk_topup_compute(
     bar_index: BarIndex = Depends(get_bar_index),
     registry: ResearchRegistry = Depends(get_registry),
     manager: DeskTopupComputeManager = Depends(get_desk_topup_manager),
+    topup_run_store: TopupRunStore = Depends(get_topup_run_store),
 ) -> dict:
     """Start the single-flight desk top-up job over the LATEST universe snapshot's members, or —
     if one is already running — return it UNCHANGED (``started: False``, never a second concurrent
     job). Returns ``{"started": bool, "compute": <snapshot>}``; the actual walk runs on a
     background worker thread, off this request, so this route returns immediately regardless of
-    how long the top-up takes."""
-    return manager.trigger(universe_store, bar_store, bar_index, registry)
+    how long the top-up takes. J-09: the job's terminal outcome is durably recorded into
+    ``topup_run_store`` once it resolves (inside ``DeskTopupComputeManager.trigger`` itself — see
+    that method's docstring) — this route only threads the store dependency through."""
+    return manager.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
 
 
 @router.get("/topup/compute")
@@ -216,6 +235,33 @@ def cancel_desk_topup_compute(
     return {"cancelling": True}
 
 
+# --- The top-up run log (J-09) — ONE read: a lightweight run-meta list + the latest full record.
+# No POST here: the log is written internally by the trigger/CLI paths above (the single shared
+# writer, `desk_topup_log.record_topup_run`) — this route is a pure read, never a trigger. --------
+
+
+def _topup_run_meta_only(record: dict) -> dict:
+    """The lightweight projection ``GET /research/desk/topup/runs``'s bulk list serves — every
+    field EXCEPT ``outcomes`` (mirrors ``_screen_meta_only``'s identical convention: a run record
+    carrying every pair's outcome is materially larger than its own summary, so the list call never
+    returns the full array for every historical run)."""
+    return {key: value for key, value in record.items() if key != "outcomes"}
+
+
+@router.get("/topup/runs")
+def get_topup_runs(store: TopupRunStore = Depends(get_topup_run_store)) -> dict:
+    """``{"runs": [...meta-only...], "latest": <full record>|null}`` — an explicit HTTP 200
+    honest-empty payload (``{"runs": [], "latest": null}``) before any top-up run has ever reached
+    its terminal state, never a 404 (the ``GET /research/desk/universe`` convention). ``latest`` is
+    the most recently STARTED run, verbatim from disk — never recomputed on the GET (the
+    ``GET /research/desk/screen`` convention: a plain read, triggers nothing)."""
+    records, _errors = store.list()
+    return {
+        "runs": [_topup_run_meta_only(r) for r in records],
+        "latest": records[-1] if records else None,
+    }
+
+
 # --- The screen (J-03) — GET (latest / ?date= / meta-only list) plus the screen compute's three
 # subpaths, mirroring the top-up trio above exactly. ------------------------------------------------
 
diff --git a/apps/backend/app/research/desk_topup_compute.py b/apps/backend/app/research/desk_topup_compute.py
index 6ebde21..40a281e 100644
--- a/apps/backend/app/research/desk_topup_compute.py
+++ b/apps/backend/app/research/desk_topup_compute.py
@@ -37,7 +37,24 @@ immediately BEFORE the call: a store-first hit's ``created_utc`` necessarily pre
 timestamp (the series already existed), while a freshly-written series' ``created_utc`` is stamped
 at or after it. This reads only the ALREADY-RETURNED ``created_utc`` field — it duplicates none of
 ``record_bar_series``'s own adapter-selection/feed-derivation decisions, so it cannot drift out of
-sync with that logic."""
+sync with that logic.
+
+**J-09 — the append-only run log.** Every run's OWN already-computed outcomes are persisted, once,
+at terminal state, by the single shared writer ``desk_topup_log.record_topup_run`` — called from
+BOTH ``_work``'s two exit paths below (the ``except`` branch for a whole-job ``"failed"``, and the
+normal ``"cancelled"``/``"done"`` path) and once more from the CLI's ``main()`` after ``run_topup``
+returns successfully. ``universe_snapshot_id`` and the run's ``requested_window`` (one
+``_fetch_window_now()`` call, captured ONCE per run in the caller — never re-derived inside the
+writer, never a second call inside ``_run_one_pair``, which keeps its own existing per-pair call
+byte-unchanged) are threaded through as plain local/closure values — never added as a new key on
+``self._snapshot`` (that dict stays exactly the J-02 shape; the run LOG is a separate, durable
+concern). A run-level ``state: "failed"`` (something escaped ``run_topup`` itself) is NOT the same
+thing as a per-pair ``outcome: "failed"`` (already caught inside ``_run_one_pair`` and folded into
+``outcomes`` — the job still resolves ``"done"``): the ``except`` branch below writes a record with
+whatever outcomes were published before the crash (a local ``collected`` list, independent of the
+shared ``self._snapshot`` to avoid any race with a superseding job); the CLI path has no cancel
+signal and normally only ever terminates ``"done"``, so an uncaught crash BEFORE its own writer
+call is the correct interrupted-run case — zero record, never a bug to guard against."""
 
 from __future__ import annotations
 
@@ -54,6 +71,7 @@ from ..config import CONFIG
 from .bar_index import BarIndex
 from .bars import BarStore
 from .desk_coverage import DESK_TOPUP_TIMEFRAMES
+from .desk_topup_log import TopupRunStore, record_topup_run, resolve_desk_topup_log_dir
 from .desk_universe import UniverseStore
 from .routes import (
     BarRecordRequest,
@@ -214,6 +232,7 @@ class DeskTopupComputeManager:
         bar_store: BarStore,
         bar_index: BarIndex,
         registry: ResearchRegistry,
+        topup_run_store: TopupRunStore,
     ) -> dict:
         """Start a NEW top-up job over the LATEST universe snapshot's members, or — if one is
         already ``state == "running"`` — return it UNCHANGED (``started: False``, single-flight).
@@ -221,30 +240,50 @@ class DeskTopupComputeManager:
         call always starts a genuinely new job (a fresh id), discarding the prior snapshot. Never
         blocks — the walk runs on a dedicated worker thread, off the caller's thread, so an HTTP
         route calling this returns immediately. No universe snapshot registered yet -> an honest
-        zero-pair job (``pairs_total: 0``) that resolves ``"done"`` immediately, never an error."""
+        zero-pair job (``pairs_total: 0``) that resolves ``"done"`` immediately, never an error.
+
+        J-09: ``topup_run_store`` is where this job's terminal outcome is durably recorded (once,
+        via ``desk_topup_log.record_topup_run`` — see the module docstring's J-09 section) — a
+        required per-call dependency (the ``bar_store``/``bar_index``/``registry`` precedent), never
+        a constructor-owned default, so a test points it at any hermetic store with zero plumbing."""
         with self._lock:
             current = self._snapshot
             if current is not None and current["state"] == "running":
                 return {"started": False, "compute": _copy_snapshot(current)}
 
             records, _errors = universe_store.list()
+            universe_snapshot_id = records[-1]["id"] if records else None
             members: list[str] = list(records[-1]["members"]) if records else []
             pairs_total = len(members) * len(DESK_TOPUP_TIMEFRAMES)
 
             job_id = uuid.uuid4().hex
+            started_utc = _iso_utc_now()
             cancel_event = threading.Event()
             self._cancel_event = cancel_event
             snapshot = {
                 "id": job_id,
                 "state": "running",
-                "started_utc": _iso_utc_now(),
+                "started_utc": started_utc,
                 "finished_utc": None,
                 "error": None,
                 "progress": {"pairs_total": pairs_total, "pairs_done": 0, "outcomes": []},
             }
             self._snapshot = snapshot
 
+        # J-09: the requested fetch window is captured ONCE here, before the walk starts -- never
+        # re-derived inside the writer or per-pair (`_run_one_pair` still calls its own
+        # `_fetch_window_now()`, unchanged, once per pair, for that pair's OWN fetch; this is a
+        # separate, record-keeping-only read of the same deterministic-per-UTC-day helper --
+        # goal-desk-iter-11 NOTES / assumptions.md iter-11 entry). `collected` is this job's own
+        # append-only mirror of every outcome `_publish` has seen so far, independent of
+        # `self._snapshot` -- so the crash-fallback write below (a whole-job failure) never risks
+        # reading a snapshot a NEWER job has already superseded.
+        _window_start, _window_end = _fetch_window_now()
+        requested_window = {"start": _window_start, "end": _window_end}
+        collected: list[dict] = []
+
         def _publish(entry: dict) -> None:
+            collected.append(entry)
             with self._lock:
                 current = self._snapshot
                 if current is None or current["id"] != job_id:
@@ -259,9 +298,22 @@ class DeskTopupComputeManager:
                     },
                 }
 
+        def _record_run(*, state: str, outcomes: list[dict]) -> None:
+            record_topup_run(
+                topup_run_store,
+                universe_snapshot_id=universe_snapshot_id,
+                requested_window=requested_window,
+                config_fingerprint=CONFIG.config_fingerprint(),
+                started_utc=started_utc,
+                finished_utc=_iso_utc_now(),
+                state=state,
+                pairs_total=pairs_total,
+                outcomes=outcomes,
+            )
+
         def _work() -> None:
             try:
-                run_topup(
+                outcomes = run_topup(
                     members, bar_store, bar_index, registry,
                     progress=_publish, should_abort=cancel_event.is_set,
                 )
@@ -270,8 +322,11 @@ class DeskTopupComputeManager:
                 # recorded as "failed" outcomes -- this only fires for something run_topup itself
                 # cannot recover from) -- surfaced verbatim, never swallowed.
                 self._resolve(job_id, "failed", error=str(exc))
+                _record_run(state="failed", outcomes=collected)
                 return
-            self._resolve(job_id, "cancelled" if cancel_event.is_set() else "done", error=None)
+            state = "cancelled" if cancel_event.is_set() else "done"
+            self._resolve(job_id, state, error=None)
+            _record_run(state=state, outcomes=outcomes)
 
         thread = threading.Thread(target=_work, name=f"desk-topup-compute:{job_id}", daemon=True)
         with self._lock:
@@ -346,6 +401,9 @@ def main() -> int:
         bar_store = get_bar_store()
         bar_index = get_bar_index()
         universe_store = UniverseStore(config.desk_universe_dir_resolved())
+        topup_run_store = TopupRunStore(
+            resolve_desk_topup_log_dir(config.desk_universe_dir_resolved())
+        )
 
         records, _errors = universe_store.list()
         if not records:
@@ -355,13 +413,37 @@ def main() -> int:
                 file=sys.stderr,
             )
             return 1
+        universe_snapshot_id = records[-1]["id"]
         members = list(records[-1]["members"])
+        pairs_total = len(members) * len(DESK_TOPUP_TIMEFRAMES)
         print(
             f"desk top-up: {len(members)} member(s) x {len(DESK_TOPUP_TIMEFRAMES)} "
-            f"timeframe(s) = {len(members) * len(DESK_TOPUP_TIMEFRAMES)} pair(s)",
+            f"timeframe(s) = {pairs_total} pair(s)",
             flush=True,
         )
+        # J-09: the requested fetch window is captured ONCE, before the walk starts -- the SAME
+        # record-keeping-only read `DeskTopupComputeManager.trigger` uses (see that method's own
+        # comment); `run_topup`/`_run_one_pair` still call `_fetch_window_now()` themselves,
+        # unchanged, once per pair, for that pair's OWN fetch.
+        window_start, window_end = _fetch_window_now()
+        started_utc = _iso_utc_now()
         outcomes = run_topup(members, bar_store, bar_index, registry, progress=_cli_progress_printer())
+        # The CLI has no cancel signal -- a run that reaches this line always terminates "done"
+        # (the module docstring's J-09 section). An uncaught crash ABOVE this line (inside
+        # `run_topup` itself, escaping its own per-pair try/except) is the correct interrupted-run
+        # case: the process exits without ever calling the writer below, so the ledger stays
+        # honestly empty for this attempt -- never guarded against here.
+        record_topup_run(
+            topup_run_store,
+            universe_snapshot_id=universe_snapshot_id,
+            requested_window={"start": window_start, "end": window_end},
+            config_fingerprint=config.config_fingerprint(),
+            started_utc=started_utc,
+            finished_utc=_iso_utc_now(),
+            state="done",
+            pairs_total=pairs_total,
+            outcomes=outcomes,
+        )
     finally:
         store.close()
 
diff --git a/apps/backend/tests/test_desk_topup_compute.py b/apps/backend/tests/test_desk_topup_compute.py
index 762282d..34b84bf 100644
--- a/apps/backend/tests/test_desk_topup_compute.py
+++ b/apps/backend/tests/test_desk_topup_compute.py
@@ -1,6 +1,7 @@
-"""``desk_topup_compute.py`` (Era B "The Desk", J-02) — the desk bar top-up: manager mechanics
-(single-flight, cancel, atomic progress) plus the store-first/resumability guarantee, plus the
-three HTTP routes.
+"""``desk_topup_compute.py`` (Era B "The Desk", J-02 + J-09) — the desk bar top-up: manager
+mechanics (single-flight, cancel, atomic progress) plus the store-first/resumability guarantee,
+plus the HTTP routes; and (J-09, this iteration) the append-only run-log writer wired into both the
+manager and the CLI.
 
 Manager-mechanics tests substitute a FAKE ``_run_one_pair`` (monkeypatched onto this module's own
 imported name — the ``test_edge_report_compute.py`` fake-swap precedent) for deterministic,
@@ -11,10 +12,16 @@ taxonomy are proven end to end against the REAL ``record_bar_series`` path, thro
 (``TestClient``) cover GET-never-computes (TC-10), single-flight/cancel through HTTP, and idle
 cancel returning 409 (TC-15) — the manager itself never raises on an idle cancel (the
 ``cancel_edge_report_compute`` precedent: the ROUTE owns the 409).
-"""
+
+J-09 tests are threaded through the SAME manager/route fixtures rather than a separate file's own
+fixture set, since every J-09 assertion is "and ALSO a run record landed correctly" on top of an
+existing J-02 scenario (cancelled, failing-pair, second-run, CLI) — the store module's OWN
+isolated discipline (checksum, corruption, no-dedup-append-only, interrupted-run) lives in
+``test_desk_topup_log.py``."""
 
 from __future__ import annotations
 
+import sys
 import threading
 import time
 
@@ -28,8 +35,9 @@ from app.research import desk_topup_compute
 from app.research.bar_index import BarIndex
 from app.research.bars import BarStore
 from app.research.desk_coverage import DESK_TOPUP_TIMEFRAMES
-from app.research.desk_routes import get_desk_topup_manager
+from app.research.desk_routes import get_desk_topup_manager, get_topup_run_store
 from app.research.desk_topup_compute import DeskTopupComputeManager, run_topup
+from app.research.desk_topup_log import TopupRunStore
 from app.research.desk_universe import UniverseStore
 from app.research.routes import ResearchRegistry, set_registry
 from app.research.store import JournalStore
@@ -71,13 +79,16 @@ def _wait_for_terminal(mgr: DeskTopupComputeManager, timeout: float = 5.0) -> di
 def manager_env(tmp_path):
     """Manager-level tests: no ``TestClient``/``set_registry`` needed — every dependency is passed
     explicitly to ``manager.trigger(...)`` (the ``EdgeReportComputeManager`` per-call-injection
-    precedent), so this fixture stays fully isolated from the global registry singleton."""
+    precedent), so this fixture stays fully isolated from the global registry singleton.
+    ``topup_run_store`` (J-09) is the 5th value every ``manager_env``-consuming test now threads
+    into ``.trigger(...)`` — the run-log store, hermetic per test."""
     universe_store = UniverseStore(tmp_path / "universe")
     bar_store = BarStore(tmp_path / "bars")
     bar_index = BarIndex(str(tmp_path / "index.db"))
     journal = JournalStore(str(tmp_path / "journal.db"), CONFIG)
     registry = ResearchRegistry(journal, CONFIG)
-    yield universe_store, bar_store, bar_index, registry
+    topup_run_store = TopupRunStore(tmp_path / "topup_runs")
+    yield universe_store, bar_store, bar_index, registry, topup_run_store
     journal.close()
     app.dependency_overrides.pop(get_market_adapter, None)
 
@@ -99,10 +110,10 @@ def test_no_job_has_ever_run_snapshot_is_none():
 
 
 def test_trigger_with_no_universe_snapshot_is_an_honest_zero_pair_job_that_completes(manager_env):
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     mgr = DeskTopupComputeManager()
 
-    result = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    result = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     assert result["started"] is True
     assert result["compute"]["progress"]["pairs_total"] == 0
 
@@ -115,7 +126,7 @@ def test_trigger_with_no_universe_snapshot_is_an_honest_zero_pair_job_that_compl
 def test_trigger_shape_pairs_total_equals_members_times_four(manager_env, monkeypatch):
     """TC-6 (shape): ``pairs_total == N * len(DESK_TOPUP_TIMEFRAMES)``, known synchronously at
     trigger time (before the background thread even starts)."""
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=sorted(FIVE_MEMBERS), raw_members={m: m for m in FIVE_MEMBERS},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -127,7 +138,7 @@ def test_trigger_shape_pairs_total_equals_members_times_four(manager_env, monkey
     monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)
 
     mgr = DeskTopupComputeManager()
-    result = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    result = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     assert result["compute"]["progress"]["pairs_total"] == len(FIVE_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
 
     snap = _wait_for_terminal(mgr)
@@ -143,7 +154,7 @@ def test_trigger_shape_pairs_total_equals_members_times_four(manager_env, monkey
 
 def test_second_trigger_while_running_returns_the_same_job_started_false(manager_env, monkeypatch):
     """TC-9: single-flight."""
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -159,10 +170,10 @@ def test_second_trigger_while_running_returns_the_same_job_started_false(manager
     monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)
 
     mgr = DeskTopupComputeManager()
-    first = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    first = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     assert started.wait(timeout=5)
 
-    second = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    second = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     assert second["started"] is False
     assert second["compute"]["id"] == first["compute"]["id"]
 
@@ -172,7 +183,7 @@ def test_second_trigger_while_running_returns_the_same_job_started_false(manager
 
 
 def test_trigger_after_a_terminal_job_starts_a_genuinely_new_job(manager_env, monkeypatch):
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=["AAA"], raw_members={"AAA": "AAA"},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -180,11 +191,11 @@ def test_trigger_after_a_terminal_job_starts_a_genuinely_new_job(manager_env, mo
     monkeypatch.setattr(desk_topup_compute, "_run_one_pair", lambda *a: ("fetched", None))
 
     mgr = DeskTopupComputeManager()
-    first = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    first = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     _wait_for_terminal(mgr)
     mgr.join_all(timeout=5)
 
-    second = mgr.trigger(universe_store, bar_store, bar_index, registry)
+    second = mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     assert second["started"] is True
     assert second["compute"]["id"] != first["compute"]["id"]
     _wait_for_terminal(mgr)
@@ -197,7 +208,7 @@ def test_a_cancellation_signal_resolves_state_cancelled_with_the_partial_outcome
     """Cancellation mechanics: the worker observes ``should_abort`` BETWEEN pairs and stops early
     -- the job resolves ``"cancelled"`` with exactly the outcomes recorded before the signal fired,
     never a raise, never a fabricated remaining outcome."""
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -216,7 +227,7 @@ def test_a_cancellation_signal_resolves_state_cancelled_with_the_partial_outcome
     monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)
 
     mgr = DeskTopupComputeManager()
-    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     assert started.wait(timeout=5)
     mgr.cancel()
     release.set()
@@ -227,12 +238,23 @@ def test_a_cancellation_signal_resolves_state_cancelled_with_the_partial_outcome
     assert len(snap["progress"]["outcomes"]) == 2  # the 2 pairs already in flight when cancel fired
     mgr.join_all(timeout=5)
 
+    # TC-4 (J-09): the persisted run record mirrors the cancelled state, with `pairs_attempted`
+    # strictly less than `pairs_total`.
+    records, errors = topup_run_store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0]["state"] == "cancelled"
+    assert records[0]["pairs_total"] == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
+    assert records[0]["pairs_attempted"] == 2
+    assert records[0]["pairs_attempted"] < records[0]["pairs_total"]
+    assert len(records[0]["outcomes"]) == 2
+
 
 def test_an_unexpected_crash_outside_run_topup_resolves_state_failed(manager_env, monkeypatch):
     """Safety net: a failure that ``run_topup`` itself cannot recover from (never a per-pair
     outcome -- those are caught inside ``_run_one_pair``) resolves the WHOLE job ``"failed"``, the
     message surfaced verbatim (the ``EdgeReportComputeManager`` precedent)."""
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=["AAA"], raw_members={"AAA": "AAA"},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -244,16 +266,71 @@ def test_an_unexpected_crash_outside_run_topup_resolves_state_failed(manager_env
     monkeypatch.setattr(desk_topup_compute, "run_topup", fake_run_topup)
 
     mgr = DeskTopupComputeManager()
-    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     snap = _wait_for_terminal(mgr)
 
     assert snap["state"] == "failed"
     assert snap["error"] == "synthetic catastrophic failure"
     mgr.join_all(timeout=5)
 
+    # J-09: a whole-job "failed" (something escaped run_topup itself) is a genuine terminal state
+    # reached WITHIN the process, so a record IS written -- distinct from the interrupted-run case
+    # (the process ending before the writer is ever called). `fake_run_topup` raises before
+    # publishing any pair, so the record's outcomes are honestly empty.
+    records, errors = topup_run_store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0]["state"] == "failed"
+    assert records[0]["outcomes"] == []
+    assert records[0]["pairs_attempted"] == 0
+    assert records[0]["pairs_total"] == len(DESK_TOPUP_TIMEFRAMES)  # 1 member x 4 timeframes
+
+
+@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
+def test_a_walk_interrupted_before_the_terminal_write_leaves_zero_run_record(
+    manager_env, monkeypatch
+):
+    """TC-7 (J-09), the NON-vacuous half: a run that genuinely WALKED pairs — publishing them into
+    the live progress snapshot — but whose process/thread ends before the writer's terminal call
+    persists NOTHING. ``SystemExit`` raised inside the walk is the simulation: ``_run_one_pair``'s
+    own ``except Exception`` does not catch it, ``run_topup`` propagates it, and ``_work``'s
+    ``except Exception`` does not catch it either — so neither ``_resolve`` nor the writer ever runs
+    and ``threading`` retires the worker silently, exactly as a killed process would. The store must
+    gain zero files even though two pairs were already attempted and recorded in memory — never a
+    fabricated, partial, or "pending" record (``test_desk_topup_log.py``'s store-level sibling test
+    proves the same for a store that was never touched at all; this one proves the MANAGER never
+    writes speculatively mid-walk)."""
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
+    universe_store.record(
+        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    calls: list[tuple[str, str]] = []
+
+    def fake_one_pair(symbol, timeframe, *_args):
+        calls.append((symbol, timeframe))
+        if len(calls) == 3:
+            raise SystemExit("simulated process death mid-walk")
+        return "fetched", None
+
+    monkeypatch.setattr(desk_topup_compute, "_run_one_pair", fake_one_pair)
+
+    mgr = DeskTopupComputeManager()
+    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
+    mgr.join_all(timeout=5)
+
+    assert len(calls) == 3  # the walk genuinely ran, and died on the third pair
+    snap = mgr.snapshot()
+    assert snap["state"] == "running"  # never resolved -- process-scoped state is honestly lost
+    assert len(snap["progress"]["outcomes"]) == 2  # two pairs really were attempted
+
+    records, errors = topup_run_store.list()
+    assert records == [] and errors == []
+    assert not (topup_run_store.root).exists()  # not even an empty/partial file was created
+
 
 def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_reference(manager_env, monkeypatch):
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=["AAA"], raw_members={"AAA": "AAA"},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -261,7 +338,7 @@ def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_referenc
     monkeypatch.setattr(desk_topup_compute, "_run_one_pair", lambda *a: ("fetched", None))
 
     mgr = DeskTopupComputeManager()
-    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     snap = _wait_for_terminal(mgr)
     snap["progress"]["outcomes"].append({"poison": True})
     snap["progress"]["outcomes"][0]["outcome"] = "POISONED"
@@ -272,6 +349,48 @@ def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_referenc
     mgr.join_all(timeout=5)
 
 
+def test_manager_triggered_runs_persisted_outcomes_are_byte_identical_to_run_topups_own_return(
+    manager_env, monkeypatch
+):
+    """TC-2 (J-09): the persisted run record's ``outcomes`` list is byte-identical (same values,
+    same order) to the list ``run_topup`` itself returned for that walk — proven with a spy
+    WRAPPING the REAL ``run_topup`` (never a fake substitute), capturing its actual return value
+    for direct comparison against what landed in the store."""
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
+    universe_store.record(
+        members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+    _inject_adapter(bars=_bars())
+
+    real_run_topup = desk_topup_compute.run_topup
+    captured: list[list[dict]] = []
+
+    def _spy(*args, **kwargs):
+        result = real_run_topup(*args, **kwargs)
+        captured.append(result)
+        return result
+
+    monkeypatch.setattr(desk_topup_compute, "run_topup", _spy)
+
+    mgr = DeskTopupComputeManager()
+    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
+    _wait_for_terminal(mgr)
+    mgr.join_all(timeout=5)
+
+    assert len(captured) == 1  # run_topup was called exactly once for this job
+    records, errors = topup_run_store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0]["outcomes"] == captured[0]  # byte-identical to run_topup's own return
+    assert records[0]["state"] == "done"
+    assert records[0]["pairs_total"] == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
+    assert records[0]["pairs_attempted"] == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
+    assert records[0]["universe_snapshot_id"] is not None
+    assert records[0]["requested_window"]["start"] < records[0]["requested_window"]["end"]
+    assert records[0]["config_fingerprint"] == CONFIG.config_fingerprint()
+
+
 # ==================================================================================================
 # Store-first / resumability + honest failure -- against the REAL record_bar_series path, via
 # FakeAdapter (zero network).
@@ -280,7 +399,7 @@ def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_referenc
 
 def test_first_run_fetches_every_pair_and_records_it(manager_env):
     """TC-6 mechanics (real path): a fresh store, every pair genuinely fetched."""
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -288,7 +407,7 @@ def test_first_run_fetches_every_pair_and_records_it(manager_env):
     adapter = _inject_adapter(bars=_bars())
 
     mgr = DeskTopupComputeManager()
-    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     snap = _wait_for_terminal(mgr)
 
     assert snap["state"] == "done"
@@ -301,7 +420,7 @@ def test_first_run_fetches_every_pair_and_records_it(manager_env):
 
 def test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls(manager_env):
     """TC-7: store-first proven end to end."""
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -309,14 +428,14 @@ def test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls(
     adapter = _inject_adapter(bars=_bars())
 
     first_mgr = DeskTopupComputeManager()
-    first_mgr.trigger(universe_store, bar_store, bar_index, registry)
+    first_mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     _wait_for_terminal(first_mgr)
     first_mgr.join_all(timeout=5)
     calls_after_first_run = len(adapter.fetch_bars_calls)
     assert calls_after_first_run == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
 
     second_mgr = DeskTopupComputeManager()
-    second_mgr.trigger(universe_store, bar_store, bar_index, registry)
+    second_mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     snap = _wait_for_terminal(second_mgr)
 
     assert snap["state"] == "done"
@@ -326,6 +445,16 @@ def test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls(
     assert len(adapter.fetch_bars_calls) == calls_after_first_run  # zero NEW vendor calls
     second_mgr.join_all(timeout=5)
 
+    # TC-6 (J-09): the second run appended a SECOND, distinct record -- the first stays exactly as
+    # it was (no dedup, no update; see test_desk_topup_log.py for the byte-level file-unchanged
+    # proof of this same guarantee at the store layer).
+    records, errors = topup_run_store.list()
+    assert errors == []
+    assert len(records) == 2
+    assert records[0]["id"] != records[1]["id"]
+    assert {o["outcome"] for o in records[0]["outcomes"]} == {"fetched"}  # the FIRST run's own record
+    assert {o["outcome"] for o in records[1]["outcomes"]} == {"reused"}  # the SECOND run's own record
+
 
 def test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_resumability_guarantee(
     manager_env,
@@ -338,7 +467,7 @@ def test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_
     "reused" with no growth in vendor calls; the rest must report "fetched". (The cancellation
     MECHANISM itself -- state transitions to "cancelled" with a partial outcomes list -- is proven
     separately, above, with a deterministic mocked fake.)"""
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=sorted(FIVE_MEMBERS), raw_members={m: m for m in FIVE_MEMBERS},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -355,7 +484,7 @@ def test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_
     assert calls_after_prepopulate == len(pre_populated)
 
     mgr = DeskTopupComputeManager()
-    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     snap = _wait_for_terminal(mgr)
 
     assert snap["state"] == "done"
@@ -394,7 +523,7 @@ def test_a_failing_pair_reports_failed_with_the_detail_preserved_and_the_run_con
                 raise self._exc
             return self._bars
 
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
... [diff_bound] apps/backend/tests/test_desk_topup_compute.py: 218 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 89b1355..4dfdb07 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -901,6 +901,25 @@ async def test_get_endpoint_profiles_byte_identical_on_the_live_200(mcp_env):
     assert result.content[0].text.encode("utf-8") == rest.content, "profiles not byte-identical"
 
 
+@pytest.mark.anyio
+async def test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool(mcp_env):
+    """goal-desk-iter-11 TC-9 (J-09): the NEW ``GET /research/desk/topup/runs`` route is reachable
+    through ``get_endpoint``'s existing ``/research/`` allowlist prefix with ZERO MCP code change —
+    no new tool, no ``_STATIC_PATHS`` entry — and the proxied body is byte-identical to its curl
+    equivalent (here the honest-empty ``{"runs": [], "latest": null}`` this module-scoped backend's
+    own temp desk dirs genuinely produce). The tool count assertion lives in
+    ``test_advertised_tool_set_is_exactly_capability_6``; this is the reachability half TC-9 names
+    separately."""
+    result = await call_tool("get_endpoint", {"path": "/research/desk/topup/runs"})
+    rest = httpx.get(f"{mcp_env}/research/desk/topup/runs", timeout=5.0)
+    assert rest.status_code == 200
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "topup/runs not byte-identical"
+    assert rest.json() == {"runs": [], "latest": None}
+    assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 17
+
+
 @pytest.mark.anyio
 async def test_get_endpoint_refuses_non_allowlisted_paths_without_any_request(monkeypatch):
     """Refusal is decided BEFORE any request: with the backend base pointing at a dead port,
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index ff49180..93a493b 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -9,6 +9,7 @@ import {
   fetchDeskScreenByDate,
   fetchDeskScreenCompute,
   fetchDeskTopupCompute,
+  fetchDeskTopupRuns,
   triggerDeskScreenCompute,
   triggerDeskTopupCompute,
 } from "@/lib/api";
@@ -20,6 +21,10 @@ import type {
   DeskScreenSkip,
   DeskScreenSnapshot,
   DeskTopupComputeSnapshot,
+  DeskTopupOutcome,
+  DeskTopupRun,
+  DeskTopupRunMeta,
+  DeskTopupRunsListResult,
 } from "@/lib/types";
 import { Metric, Panel } from "@/components/Panel";
 import { fmt } from "@/lib/format";
@@ -57,6 +62,16 @@ import { fmt } from "@/lib/format";
 // already held in `screenResult` state (no refetch). Every ranked/skip row is also a `Link` to
 // `/structure?symbol=<sym>&asof=<displayed snapshot's as_of>` — the era's one sanctioned additive
 // edit to `/structure` (its own query-param prefill, see that page's own comment).
+//
+// era-desk-iter-11 (J-09): a 4th mount-time GET — `/research/desk/topup/runs` — renders a
+// read-only, non-interactive "Top-up Runs" panel (no click-through, no new control; the OUT OF
+// SCOPE text for this iteration is explicit: read-only disclosure only). PLACEMENT: rendered
+// independent of whether a screen has EVER been computed (unlike Screen History, which lives only
+// inside the populated-screen view) — a top-up run is a wholly separate operator act from a screen
+// run, and the honest-empty/populated states this journey requires (TC-12/TC-13) never presuppose
+// a screen exists. This is a deliberate placement choice logged in
+// `runs/goal-session-desk/state/assumptions.md` (iter-11 entry), not the plan's own literal
+// "immediately after Screen History" suggestion (which that same plan text marks as non-binding).
 
 const NUMERIC_CELL = "px-2 py-1.5 text-right font-mono text-xs text-slate-200 whitespace-nowrap";
 const HEADER_CELL = "px-2 py-1 text-right text-[11px] font-medium text-slate-500";
@@ -490,6 +505,160 @@ function DeskHistoryTable({
   );
 }
 
+// --- Top-up run history (era-desk-iter-11, J-09) — a durable, append-only record of every top-up
+// run's outcome, read verbatim from `GET /research/desk/topup/runs` and nothing recomputed. Two
+// tiers, mirroring the meta-only-list / full-latest split the backend itself serves (the SAME
+// split `DeskHistoryTable` above uses for screens): `TopupRunsTable` renders every recorded run's
+// summary (date + id, universe snapshot, terminal state, attempted-of-total — the ONLY fields the
+// meta-only `runs` list carries), and `LatestTopupRunDetail` renders the full per-pair detail
+// (per-outcome counts, every failed pair's detail verbatim, the honest unreached-pairs count) for
+// the latest run ONLY — the one entry the backend's `latest` field actually carries `outcomes` for.
+// Read-only, no click-through, no new control (this iteration's own OUT OF SCOPE text). -----------
+
+function topupOutcomeCounts(outcomes: DeskTopupOutcome[]): {
+  reused: number;
+  fetched: number;
+  failed: number;
+} {
+  return {
+    reused: outcomes.filter((o) => o.outcome === "reused").length,
+    fetched: outcomes.filter((o) => o.outcome === "fetched").length,
+    failed: outcomes.filter((o) => o.outcome === "failed").length,
+  };
+}
+
+function TopupRunRow({ meta }: { meta: DeskTopupRunMeta }) {
+  return (
+    <tr data-testid="desk-topup-run-row" className="border-b border-slate-800/60 last:border-b-0">
+      <td className={LABEL_CELL}>{meta.started_utc.slice(0, 10)}</td>
+      <td className={LABEL_CELL} data-testid="desk-topup-run-id">
+        {meta.id}
+      </td>
+      <td className={LABEL_CELL} data-testid="desk-topup-run-state">
+        {meta.state}
+      </td>
+      <td className={NUMERIC_CELL} data-testid="desk-topup-run-attempted">
+        {meta.pairs_attempted} / {meta.pairs_total}
+      </td>
+      <td className={LABEL_CELL} data-testid="desk-topup-run-universe">
+        {meta.universe_snapshot_id ?? "—"}
+      </td>
+    </tr>
+  );
+}
+
+function TopupRunsTable({ runs }: { runs: DeskTopupRunMeta[] }) {
+  if (runs.length === 0) {
+    return <EmptyState testid="desk-topup-runs-empty" title="No top-up runs recorded yet." />;
+  }
+  return (
+    <div className="overflow-x-auto">
+      <table data-testid="desk-topup-runs-table" className="w-full border-collapse">
+        <thead>
+          <tr className="border-b border-slate-800">
+            <th className={HEADER_CELL_LEFT}>date</th>
+            <th className={HEADER_CELL_LEFT}>run</th>
+            <th className={HEADER_CELL_LEFT}>state</th>
+            <th className={HEADER_CELL}>attempted / total</th>
+            <th className={HEADER_CELL_LEFT}>universe snapshot</th>
+          </tr>
+        </thead>
+        <tbody>
+          {runs.map((meta) => (
+            <TopupRunRow key={meta.id} meta={meta} />
+          ))}
+        </tbody>
+      </table>
+    </div>
+  );
+}
+
+// The latest run's own full detail — attempted-of-total, per-outcome counts, every failed pair's
+// detail rendered VERBATIM and legible (never truncated — TC-13 requires it readable in one
+// screenshot), and the honest count of pairs the run never reached (`pairs_total -
+// pairs_attempted`, zero when the run reached every pair — never rendered as a false "0 not
+// reached" claim of completeness the run didn't make; it is simply omitted when zero).
+function LatestTopupRunDetail({ run }: { run: DeskTopupRun }) {
+  const counts = topupOutcomeCounts(run.outcomes);
+  const unreached = run.pairs_total - run.pairs_attempted;
+  const failedOutcomes = run.outcomes.filter((o) => o.outcome === "failed");
+  return (
+    <div
+      data-testid="desk-topup-run-latest-detail"
+      className="mt-4 space-y-3 border-t border-slate-800 pt-4"
+    >
+      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
+        Latest run — {run.started_utc.slice(0, 10)} · {run.id}
+      </h3>
+      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
+        <span data-testid="desk-topup-run-latest-state">state: {run.state}</span>
+        <span data-testid="desk-topup-run-latest-attempted">
+          {run.pairs_attempted} of {run.pairs_total} pairs attempted
+        </span>
+        <span data-testid="desk-topup-run-latest-counts">
+          {counts.reused} reused · {counts.fetched} fetched · {counts.failed} failed
+        </span>
+        {unreached > 0 && (
+          <span data-testid="desk-topup-run-latest-unreached" className="text-amber-200/70">
+            {unreached} pair{unreached === 1 ? "" : "s"} not reached
+          </span>
+        )}
+      </div>
+      {failedOutcomes.length > 0 && (
+        <div data-testid="desk-topup-run-latest-failed">
+          <h4 className="mb-1 text-[11px] font-medium text-slate-500">
+            Failed pairs ({failedOutcomes.length})
+          </h4>
+          <ul className="space-y-1">
+            {failedOutcomes.map((outcome, index) => (
+              <li
+                key={`${outcome.symbol}-${outcome.timeframe}-${index}`}
+                data-testid="desk-topup-run-latest-failed-row"
+                className="text-xs text-slate-400"
+              >
+                <span className="font-mono text-slate-300">
+                  {outcome.symbol} {outcome.timeframe}
+                </span>{" "}
+                —{" "}
+                <span data-testid="desk-topup-run-latest-failed-detail">
+                  {outcome.detail ?? "(no detail recorded)"}
+                </span>
+              </li>
+            ))}
+          </ul>
+        </div>
+      )}
+    </div>
+  );
+}
+
+// The section's own Loading/Unavailable/Populated states — independent of `screenResult` (a
+// top-up run's history is a separate concern from a screen's), fed by its own mount-time GET (see
+// `DeskPage` below). Mirrors the top-level ternary's exact three-state shape.
+function TopupRunsSection({
+  result,
+}: {
+  result: { ok: boolean; data: DeskTopupRunsListResult | null; error?: string } | null;
+}) {
+  if (result === null) {
+    return <LoadingPanel testid="desk-topup-runs-loading" />;
+  }
+  if (!result.ok || result.data === null) {
+    return (
+      <UnavailablePanel
+        testid="desk-topup-runs-unavailable"
+        message={result.error ?? "The top-up run history could not be loaded."}
+      />
+    );
+  }
+  return (
+    <div>
+      <TopupRunsTable runs={result.data.runs} />
+      {result.data.latest !== null && <LatestTopupRunDetail run={result.data.latest} />}
+    </div>
+  );
+}
+
 // --- Provenance line — universe snapshot id + date, as_of, config_fingerprint, and the pinned
 // bar-store signature. --------------------------------------------------------------------------
 //
@@ -867,6 +1036,15 @@ export default function DeskPage() {
   const [topupCancelRequested, setTopupCancelRequested] = useState(false);
   const [topupCancelError, setTopupCancelError] = useState<string | null>(null);
 
+  // era-desk-iter-11 (J-09): the durable top-up run log — independent of `screenResult`/
+  // `topupCompute` above (the latter is the CURRENT/last in-flight job's process-scoped progress;
+  // this is every COMPLETED run's persisted terminal outcome).
+  const [topupRunsResult, setTopupRunsResult] = useState<{
+    ok: boolean;
+    data: DeskTopupRunsListResult | null;
+    error?: string;
+  } | null>(null);
+
   // era-desk-iter-6 (J-05): the screen-history click-through. `viewingSnapshot` is `null` while
   // showing the top-level `latest` snapshot already held in `screenResult` (no refetch needed to
   // return to it — TC-2); once a history row is selected, it holds THAT date's own full snapshot,
@@ -876,9 +1054,10 @@ export default function DeskPage() {
   const [viewingSnapshot, setViewingSnapshot] = useState<DeskScreenSnapshot | null>(null);
   const [historyFetchError, setHistoryFetchError] = useState<string | null>(null);
 
-  // Mount: exactly three GETs, zero POSTs (TC-19) — the screen list/latest, and BOTH compute
-  // managers' current/last snapshot (seeds a page load mid-job or post-terminal without a
-  // spurious extra click — the /structure edge-report mount-seeding precedent).
+  // Mount: four GETs, zero POSTs (TC-19/TC-8) — the screen list/latest, BOTH compute managers'
+  // current/last snapshot (seeds a page load mid-job or post-terminal without a spurious extra
+  // click — the /structure edge-report mount-seeding precedent), and (era-desk-iter-11, J-09) the
+  // top-up run log's list + latest full record.
   useEffect(() => {
     let alive = true;
     fetchDeskScreen().then((result) => {
@@ -890,6 +1069,9 @@ export default function DeskPage() {
     fetchDeskTopupCompute().then((result) => {
       if (alive && result.ok) setTopupCompute(result.data);
     });
+    fetchDeskTopupRuns().then((result) => {
+      if (alive) setTopupRunsResult(result);
+    });
     return () => {
       alive = false;
     };
@@ -920,12 +1102,23 @@ export default function DeskPage() {
   }, [screenCompute]);
 
   // Poll the top-up job while running — independent of the screen compute poll above (the two
-  // compute managers are separate processes-scoped jobs).
+  // compute managers are separate processes-scoped jobs). era-desk-iter-11 (J-09): the instant a
+  // tick observes a terminal state, the run log is re-fetched exactly once — the SAME "on
+  // terminal, refresh the durable list" precedent the screen compute poll above already
+  // establishes — so the just-finished run's own record appears in Top-up Runs without a manual
+  // page reload. The SAME "keep the last known state, never fabricate one" discipline applies: a
+  // failed refetch here leaves whatever was already displayed untouched.
   useEffect(() => {
     if (topupCompute?.state !== "running") return;
     const handle = setInterval(async () => {
       const next = await fetchDeskTopupCompute();
       if (next.ok) setTopupCompute(next.data);
+      if (next.ok && next.data && next.data.state !== "running") {
+        const refreshed = await fetchDeskTopupRuns();
+        setTopupRunsResult((previous) =>
+          refreshed.ok || previous === null || !previous.ok ? refreshed : previous,
+        );
+      }
     }, 700);
     return () => clearInterval(handle);
   }, [topupCompute]);
@@ -1074,6 +1267,17 @@ export default function DeskPage() {
             topupControlProps={topupControlProps}
           />
         )}
+
+        {/* era-desk-iter-11 (J-09): rendered independent of the screen conditional above — a
+            top-up run's durable history exists (or honestly doesn't) regardless of whether a
+            screen has ever been computed; see this file's own top-of-file comment for why this
+            placement deliberately differs from the plan's "immediately after Screen History"
+            suggestion. */}
+        <section aria-label="Top-up runs" className="mt-6">
+          <Panel title="Top-up Runs">
+            <TopupRunsSection result={topupRunsResult} />
+          </Panel>
+        </section>
       </main>
     </div>
   );
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 65af472..2cecdca 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -10,6 +10,7 @@ import type {
   DeskScreenListResult,
   DeskScreenSnapshot,
   DeskTopupComputeSnapshot,
+  DeskTopupRunsListResult,
   EdgeReportComputeSnapshot,
   EdgeReportPayload,
   LevelsResponse,
@@ -1109,3 +1110,31 @@ export async function cancelDeskTopupCompute(): Promise<{ ok: boolean; error?: s
     return { ok: false, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// era-desk-iter-11 (J-09): GET /research/desk/topup/runs — the durable, append-only top-up run
+// log's meta-only list + the latest full record, served VERBATIM. Mirrors `fetchDeskScreen`'s
+// exact `{ok, data, error}` shape byte-for-byte. An honest-empty (`{runs: [], latest: null}`)
+// result is a valid `ok:true` outcome — the caller renders it as "No top-up runs recorded yet.",
+// never a failure; `data: null` is reserved for a genuine non-200 / unreachable backend.
+export async function fetchDeskTopupRuns(): Promise<{
+  ok: boolean;
+  data: DeskTopupRunsListResult | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/topup/runs`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskTopupRunsListResult };
+    }
+    let error = "The top-up run history could not be loaded.";
+    try {
+      const data = await res.json();
+      if (typeof data?.detail === "string") error = data.detail;
+    } catch {
+      /* keep default */
+    }
+    return { ok: false, data: null, error };
+  } catch {
+    return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
+  }
+}
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index 6a3ebc0..2f808ab 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -914,3 +914,37 @@ export interface DeskTopupComputeSnapshot {
   error: string | null;
   progress: DeskTopupComputeProgress;
 }
+
+// era-desk-iter-11 (J-09) -- the durable, append-only top-up run log, served by
+// `GET /research/desk/topup/runs`. Distinct from `DeskTopupComputeSnapshot` above: the compute
+// snapshot is the CURRENT/last in-flight job's process-scoped progress (lost on restart, replaced
+// the instant a newer run starts); this is every COMPLETED run's terminal outcome, persisted to
+// disk once and never rewritten. `requested_window`/`pairs_total`/`pairs_attempted` are the run's
+// own recorded provenance -- never recomputed client-side. `outcomes` reuses `DeskTopupOutcome`
+// verbatim (byte-identical shape to the live compute progress's own per-pair entries).
+export interface DeskTopupRunMeta {
+  id: string;
+  universe_snapshot_id: string | null;
+  requested_window: { start: string; end: string };
+  config_fingerprint: string;
+  started_utc: string;
+  finished_utc: string;
+  state: "done" | "cancelled" | "failed";
+  pairs_total: number;
+  pairs_attempted: number;
+}
+
+// The full persisted record -- `DeskTopupRunMeta` plus the per-pair `outcomes` array. Only
+// `latest` (below) ever carries this full shape; the bulk `runs` list is meta-only (mirrors
+// `DeskScreenSnapshot`/`DeskScreenMeta`'s identical split).
+export interface DeskTopupRun extends DeskTopupRunMeta {
+  outcomes: DeskTopupOutcome[];
+}
+
+// `GET /research/desk/topup/runs` -- honest-empty-or-populated, HTTP 200 always, never 404.
+// `latest === null` iff no top-up run has EVER reached a terminal state -- the page's ONE
+// discriminator for the "No top-up runs recorded yet." empty state.
+export interface DeskTopupRunsListResult {
+  runs: DeskTopupRunMeta[];
+  latest: DeskTopupRun | null;
+}
diff --git a/apps/backend/app/research/desk_topup_log.py b/apps/backend/app/research/desk_topup_log.py
new file mode 100644
index 0000000..b37222a
--- /dev/null
+++ b/apps/backend/app/research/desk_topup_log.py
@@ -0,0 +1,238 @@
+"""Top-up run log (Era B "The Desk", J-09) — an append-only, checksummed record of what every desk
+bar top-up run attempted, surviving past the next run superseding
+``DeskTopupComputeManager``'s in-flight/last-terminal snapshot (``desk_topup_compute.py``'s job
+state is explicitly process-scoped and "honestly lost on restart" — this module is the durable
+counterpart the goal.md J-09 journey adds beside it).
+
+THIS module computes NOTHING about bars, coverage, or per-pair outcomes itself — it is a pure
+PERSISTENCE lens over what ``run_topup`` (``desk_topup_compute.py:158``) already returns. A run
+record is written EXACTLY ONCE, at the run's terminal state, by the single shared writer
+(``record_topup_run`` below) — called from both ``DeskTopupComputeManager``'s worker resolve path
+and the CLI's ``main()`` (``desk_topup_compute.py``), and nowhere else.
+
+**Mirrors ``desk_universe.UniverseStore`` / ``desk_screen.ScreenStore``'s discipline** — a
+checksum-verified load on every read (``TopupRunIntegrityError`` on any mismatch, never silence,
+never a fabricated record), ``record()`` the only mutation, no update/delete function anywhere
+(immutability is structural, not policed). **UNLIKE those two stores, this one performs NO
+content-based deduplication**: every terminal run is its own genuinely distinct event — even an
+all-"reused" run over an unchanged store is a real, separate attempt with its own
+``started_utc``/``finished_utc`` — so ``record()`` always writes a brand-new file; there is no
+"already recorded" refusal concept here, and no key a caller could collide against.
+
+**Interrupted-run honesty (a DoD clause, structural by construction).** A run whose PROCESS ends
+before this module's writer is ever called (a crash, ``kill -9``, a power loss) leaves NO record —
+there is no "pending" or "partial" file ever written, because ``record()`` is the ONLY write path
+in this module and it is called exactly once, at the very end of a run's lifecycle, never earlier
+and never speculatively. This is proven by the store's own natural behavior: a store that is never
+told to ``record()`` holds zero files, full stop.
+
+**Storage dir — no new ``Config`` field.** ``resolve_desk_topup_log_dir`` mirrors
+``desk_screen.resolve_desk_screen_dir`` exactly: a bare ``TAPEOLOGY_DESK_TOPUP_LOG_DIR`` env-var
+override, else a directory co-located as a SIBLING of the caller's own already-resolved universe
+directory (the ``edge_report_cache.resolve_cache_db_path`` pattern) — an operational storage-
+location knob, never a value that shapes a served result, so ``config_fingerprint()`` stays
+untouched (the Constraints' own explicit sanction for "worker counts, timeouts, store dirs").
+
+**Records ATTEMPTS only.** Bar coverage/freshness keeps its existing single owner
+(``desk_coverage.py`` over ``bar_index``) — this module creates no second coverage path anywhere;
+it never reads a ``BarStore`` or ``BarIndex`` at all.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import os
+import uuid
+from pathlib import Path
+
+__all__ = [
+    "TopupRunIntegrityError",
+    "TopupRunStore",
+    "record_topup_run",
+    "resolve_desk_topup_log_dir",
+]
+
+# The store's own env-var override (the ``TAPEOLOGY_DESK_SCREEN_DIR``/``TAPEOLOGY_DESK_UNIVERSE_DIR``
+# pattern) — see ``resolve_desk_topup_log_dir``.
+_TOPUP_LOG_DIR_ENV = "TAPEOLOGY_DESK_TOPUP_LOG_DIR"
+
+# The three terminal states a run record may carry — never "running" (a record is written once, at
+# terminal state only; see the module docstring's "interrupted-run honesty" section).
+_TERMINAL_STATES = ("done", "cancelled", "failed")
+
+
+class TopupRunIntegrityError(Exception):
+    """An on-disk run-record file failed its checksum verification on load — corrupted or
+    tampered, surfaced explicitly (never silence, never a fabricated record)."""
+
+
+def resolve_desk_topup_log_dir(desk_universe_dir_resolved: str) -> str:
+    """The top-up run log's directory: the ``TAPEOLOGY_DESK_TOPUP_LOG_DIR`` env var if set, else a
+    directory co-located as a SIBLING of the CALLER's own already-resolved universe directory (the
+    ``desk_screen.resolve_desk_screen_dir`` pattern verbatim — takes a plain string, never imports
+    ``config.py``'s singleton, so the caller resolves its own universe directory first exactly as
+    ``desk_routes.py``/``desk_topup_compute.py`` already do). Deliberately NOT a
+    ``desk_topup_log_dir`` ``Config`` field (see the module docstring) — this keeps
+    ``config_fingerprint()`` untouched this iteration."""
+    override = os.environ.get(_TOPUP_LOG_DIR_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "topup_runs")
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding every checksum in this module hashes (stable across
+    processes: sorted keys, no whitespace) — the SAME encoding ``desk_universe.py``/
+    ``desk_screen.py`` hash."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+class TopupRunStore:
+    """File-based store rooted at the config-owned top-up-log directory — the ONE reader/writer.
+    Mirrors ``desk_universe.UniverseStore``/``desk_screen.ScreenStore``'s load/checksum discipline
+    exactly; unlike them, ``record`` performs no content-keyed dedup (see the module docstring) —
+    every call always persists a genuinely new file."""
+
+    def __init__(self, root: str | Path) -> None:
+        self._root = Path(root)
+
+    @property
+    def root(self) -> Path:
+        return self._root
+
+    def _path(self, run_id: str) -> Path:
+        return self._root / f"{run_id}.json"
+
+    def _load(self, path: Path) -> dict:
+        """Load ONE run-record file, verifying its whole-record checksum. Raises
+        ``TopupRunIntegrityError`` for any parse/shape/checksum failure — explicit, never silent."""
+        try:
+            data = json.loads(path.read_text())
+        except (OSError, ValueError) as exc:
+            raise TopupRunIntegrityError(
+                f"top-up run record file '{path.name}' is not parseable ({exc}) -- corrupted or "
+                f"tampered"
+            ) from exc
+        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
+            raise TopupRunIntegrityError(
+                f"top-up run record file '{path.name}' does not carry the expected record shape "
+                f"-- corrupted or tampered"
+            )
+        record = data["record"]
+        if _sha256(_canonical(record)) != data["file_checksum"]:
+            raise TopupRunIntegrityError(
+                f"top-up run record file '{path.name}' failed its integrity check (checksum "
+                f"mismatch) -- the file was corrupted or tampered with"
+            )
+        meta = record.get("meta")
+        if not isinstance(meta, dict):
+            raise TopupRunIntegrityError(
+                f"top-up run record file '{path.name}' does not carry the expected record shape "
+                f"-- corrupted or tampered"
+            )
+        return meta
+
+    def list(self) -> tuple[list[dict], list[dict]]:
+        """Every registered run's full content (each file verified), oldest-started first, plus an
+        EXPLICIT error row per file that failed verification — a corrupt file is surfaced, never
+        silently hidden and never served as data. A store whose directory was never created (no run
+        has ever been recorded) returns ``([], [])`` — the honest-empty case (DoD: "a run whose
+        process ends before the writer's terminal call leaves NO record"). Fresh copies of the
+        nested ``outcomes`` list on every call (the ``desk_universe.UniverseStore.list``
+        per-row-copy discipline), so a caller mutating a returned record can never poison a later
+        read."""
+        if not self._root.exists():
+            return [], []
+        records: list[dict] = []
+        errors: list[dict] = []
+        for path in sorted(self._root.glob("*.json")):
+            try:
+                meta = self._load(path)
+                records.append({**meta, "outcomes": [dict(o) for o in meta["outcomes"]]})
+            except TopupRunIntegrityError as exc:
+                errors.append({"file": path.name, "error": str(exc)})
+        records.sort(key=lambda meta: (meta.get("started_utc", ""), meta.get("id", "")))
+        return records, errors
+
+    def record(
+        self,
+        *,
+        universe_snapshot_id: str | None,
+        requested_window: dict,
+        config_fingerprint: str,
+        started_utc: str,
+        finished_utc: str,
+        state: str,
+        pairs_total: int,
+        outcomes: list[dict],
+    ) -> dict:
+        """Persist ONE new top-up run record (record + register in a single explicit action) —
+        ALWAYS a genuinely new file: no content-keyed dedup exists in this store (see the module
+        docstring), so a second call with identical field values still appends a second, distinct
+        record. ``pairs_attempted`` is derived HERE from ``len(outcomes)`` — never a separately
+        tracked counter (the plan's own trap #4)."""
+        if state not in _TERMINAL_STATES:
+            raise ValueError(
+                f"invalid terminal state {state!r} -- must be one of {_TERMINAL_STATES}"
+            )
+        date = started_utc[:10]  # started_utc is always an ISO-8601 UTC string -- a YYYY-MM-DD prefix
+        run_id = f"topup-{date}-{uuid.uuid4().hex[:12]}"
+        # A path collision is astronomically unlikely (a random 12-hex-char suffix), but this store
+        # never silently overwrites an existing file regardless of cause -- mirrors
+        # UniverseStore.record's/ScreenStore.record's identical defensive re-roll instead of a
+        # blind write.
+        while self._path(run_id).exists():
+            run_id = f"topup-{date}-{uuid.uuid4().hex[:12]}"
+        meta = {
+            "id": run_id,
+            "universe_snapshot_id": universe_snapshot_id,
+            "requested_window": dict(requested_window),
+            "config_fingerprint": config_fingerprint,
+            "started_utc": started_utc,
+            "finished_utc": finished_utc,
+            "state": state,
+            "pairs_total": pairs_total,
+            "pairs_attempted": len(outcomes),
+            "outcomes": [dict(o) for o in outcomes],
+        }
+        record = {"meta": meta}
+        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
+        self._root.mkdir(parents=True, exist_ok=True)
+        self._path(run_id).write_text(json.dumps(payload))
+        return dict(meta)
+
+
+def record_topup_run(
+    store: TopupRunStore,
+    *,
+    universe_snapshot_id: str | None,
+    requested_window: dict,
+    config_fingerprint: str,
+    started_utc: str,
+    finished_utc: str,
+    state: str,
+    pairs_total: int,
+    outcomes: list[dict],
+) -> dict:
+    """THE single shared writer (goal.md J-09 step 1 / this iteration's plan) — called exactly
+    once, at a run's terminal state, by BOTH ``DeskTopupComputeManager``'s worker resolve path and
+    the CLI's ``main()`` (``desk_topup_compute.py``), and nothing else. A thin, explicit free
+    function over ``TopupRunStore.record`` (rather than each call site invoking the method
+    directly) so both call sites import and call the exact SAME symbol — a future reader grepping
+    for ``record_topup_run`` finds both, and only, call sites; there is no second write path and no
+    second outcome shape anywhere in this codebase."""
+    return store.record(
+        universe_snapshot_id=universe_snapshot_id,
+        requested_window=requested_window,
+        config_fingerprint=config_fingerprint,
+        started_utc=started_utc,
+        finished_utc=finished_utc,
+        state=state,
+        pairs_total=pairs_total,
+        outcomes=outcomes,
+    )
diff --git a/apps/backend/tests/test_desk_topup_log.py b/apps/backend/tests/test_desk_topup_log.py
new file mode 100644
index 0000000..df9212c
--- /dev/null
+++ b/apps/backend/tests/test_desk_topup_log.py
@@ -0,0 +1,244 @@
+"""``desk_topup_log.py`` (Era B "The Desk", J-09) — the top-up run log's store discipline: checksum
+verification, structural append-only-ness (no update/delete path, no content dedup — every call to
+``record`` is a genuinely new file), the interrupted-run-leaves-no-record guarantee, and the
+directory-resolution seam (mirrors ``test_desk_universe.py``/``test_desk_screen.py``'s own store-
+level test shape).
+
+The shared-writer contract itself (proving ``record_topup_run`` is the ONE path both
+``DeskTopupComputeManager`` and the CLI call) is exercised end to end in
+``test_desk_topup_compute.py`` — this file covers the store module in isolation."""
+
+from __future__ import annotations
+
+import json
+
+import pytest
+
+from app.research.desk_topup_log import (
+    TopupRunIntegrityError,
+    TopupRunStore,
+    record_topup_run,
+    resolve_desk_topup_log_dir,
+)
+
+SAMPLE_OUTCOMES = [
+    {"symbol": "AAA", "timeframe": "1h", "outcome": "fetched", "detail": None},
+    {"symbol": "AAA", "timeframe": "4h", "outcome": "reused", "detail": None},
+    {"symbol": "AAA", "timeframe": "1d", "outcome": "failed", "detail": "no data for that window"},
+]
+
+
+def _record_sample(
+    store: TopupRunStore,
+    *,
+    state: str = "done",
+    outcomes: list[dict] | None = None,
+    started_utc: str = "2026-07-28T09:00:00.000000Z",
+    finished_utc: str = "2026-07-28T09:05:00.000000Z",
+    universe_snapshot_id: str | None = "universe-2026-07-25-49b33fa31680",
+    pairs_total: int = 3,
+) -> dict:
+    return record_topup_run(
+        store,
+        universe_snapshot_id=universe_snapshot_id,
+        requested_window={"start": "2024-07-28T00:00:00Z", "end": "2026-07-28T00:00:00Z"},
+        config_fingerprint="08e471b10130e1e2",
+        started_utc=started_utc,
+        finished_utc=finished_utc,
+        state=state,
+        pairs_total=pairs_total,
+        outcomes=SAMPLE_OUTCOMES if outcomes is None else outcomes,
+    )
+
+
+# --- record: shape + provenance ------------------------------------------------------------------
+
+
+def test_record_stores_every_field_and_derives_pairs_attempted_from_len_outcomes(tmp_path):
+    store = TopupRunStore(tmp_path / "topup_runs")
+    meta = _record_sample(store)
+
+    assert meta["universe_snapshot_id"] == "universe-2026-07-25-49b33fa31680"
+    assert meta["requested_window"] == {"start": "2024-07-28T00:00:00Z", "end": "2026-07-28T00:00:00Z"}
+    assert meta["config_fingerprint"] == "08e471b10130e1e2"
+    assert meta["started_utc"] == "2026-07-28T09:00:00.000000Z"
+    assert meta["finished_utc"] == "2026-07-28T09:05:00.000000Z"
+    assert meta["state"] == "done"
+    assert meta["pairs_total"] == 3
+    assert meta["pairs_attempted"] == 3  # len(outcomes), never a separately tracked counter
+    assert meta["outcomes"] == SAMPLE_OUTCOMES
+    assert meta["id"].startswith("topup-2026-07-28-")
+    # The record landed as ONE file in the configured directory.
+    assert len(list((tmp_path / "topup_runs").glob("*.json"))) == 1
+
+
+def test_record_rejects_a_non_terminal_state(tmp_path):
+    store = TopupRunStore(tmp_path / "topup_runs")
+    with pytest.raises(ValueError):
+        _record_sample(store, state="running")
+
+
+def test_outcomes_are_preserved_verbatim_including_a_failed_pairs_detail(tmp_path):
+    store = TopupRunStore(tmp_path / "topup_runs")
+    meta = _record_sample(store)
+
+    failed = [o for o in meta["outcomes"] if o["outcome"] == "failed"]
+    assert len(failed) == 1
+    assert failed[0]["detail"] == "no data for that window"
+    assert failed[0]["symbol"] == "AAA" and failed[0]["timeframe"] == "1d"
+
+
+# --- list: verbatim read, oldest-started first -----------------------------------------------------
+
+
+def test_list_serves_the_stored_record_verbatim(tmp_path):
+    store = TopupRunStore(tmp_path / "topup_runs")
+    recorded = _record_sample(store)
+
+    records, errors = store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0] == recorded
+
+
+def test_store_survives_a_reload_from_disk(tmp_path):
+    root = tmp_path / "topup_runs"
+    recorded = _record_sample(TopupRunStore(root))
+
+    reloaded = TopupRunStore(root)
+    records, errors = reloaded.list()
+    assert errors == []
+    assert records == [recorded]
+
+
+def test_list_on_a_directory_that_was_never_created_is_honestly_empty(tmp_path):
+    """The DoD's interrupted-run guarantee at its simplest: a store that is never told to
+    ``record`` (the writer's terminal call literally never happening — the process ended, or in
+    this test's case, simply was never invoked) holds zero files and lists zero records — never a
+    fabricated or partial entry."""
+    store = TopupRunStore(tmp_path / "topup_runs" / "never-created")
+    records, errors = store.list()
+    assert records == []
+    assert errors == []
+    assert not (tmp_path / "topup_runs" / "never-created").exists()
+
+
+# --- append-only: every call to record is a genuinely NEW file, never a dedup/update ---------------
+
+
+def test_two_calls_with_identical_field_values_still_append_two_distinct_records(tmp_path):
+    """UNLIKE UniverseStore/ScreenStore, this store performs no content-keyed dedup — two
+    back-to-back top-up runs over an unchanged store (e.g. both entirely "reused") are still TWO
+    real, distinct attempts and must both be recorded."""
+    store = TopupRunStore(tmp_path / "topup_runs")
+    first = _record_sample(store)
+    second = _record_sample(store)
+
+    assert first["id"] != second["id"]
+    records, errors = store.list()
+    assert errors == []
+    assert {r["id"] for r in records} == {first["id"], second["id"]}
+
+
+def test_a_second_run_appends_without_touching_the_first_files_bytes_on_disk(tmp_path):
+    """TC-6: the first record's file stays byte-unchanged (same sha256) after a second run
+    completes."""
+    root = tmp_path / "topup_runs"
+    store = TopupRunStore(root)
+    first = _record_sample(store, started_utc="2026-07-28T09:00:00Z", finished_utc="2026-07-28T09:05:00Z")
+    first_path = root / f"{first['id']}.json"
+    first_bytes_before = first_path.read_bytes()
+
+    second = _record_sample(
+        store,
+        started_utc="2026-07-28T10:00:00Z",
+        finished_utc="2026-07-28T10:05:00Z",
+        outcomes=[{"symbol": "BBB", "timeframe": "1h", "outcome": "fetched", "detail": None}],
+    )
+
+    assert first_path.read_bytes() == first_bytes_before  # byte-unchanged
+    records, errors = store.list()
+    assert errors == []
+    assert len(records) == 2
+    assert records[0]["id"] == first["id"]  # oldest-started first
+    assert records[1]["id"] == second["id"]
+
+
+def test_topup_run_store_has_no_update_or_delete_method():
+    """Structural immutability: the only mutation on this class is ``record`` — mirrors
+    ``UniverseStore``/``ScreenStore``'s own guard-by-absence discipline."""
+    public_methods = {name for name in dir(TopupRunStore) if not name.startswith("_")}
+    assert public_methods == {"root", "list", "record"}
+
+
+# --- interrupted-run honesty: a run whose terminal write never happens leaves zero record ---------
+
+
+def test_a_run_that_never_reaches_the_writer_call_leaves_the_store_untouched(tmp_path):
+    """Simulates a process that ends before the writer's terminal call: a store is constructed
+    exactly as a real caller would, but ``record``/``record_topup_run`` is deliberately never
+    invoked (standing in for a crash between the walk finishing and the writer call). The store
+    gains zero new file — never a fabricated or partial entry (DoD)."""
+    store = TopupRunStore(tmp_path / "topup_runs")
+    # ... the walk would happen here in a real run; the process ends before this line runs:
+    # record_topup_run(store, ...)
+    records, errors = store.list()
+    assert records == []
+    assert errors == []
+    assert not (tmp_path / "topup_runs").exists()
+
+
+# --- integrity: a corrupted file is explicit, never silent ----------------------------------------
+
+
+def test_corrupted_run_record_file_surfaces_explicitly_in_list_errors(tmp_path):
+    root = tmp_path / "topup_runs"
+    store = TopupRunStore(root)
+    _record_sample(store)
+    path = next(root.glob("*.json"))
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["pairs_total"] = 999  # tamper -- file_checksum now disagrees
+    path.write_text(json.dumps(data))
+
+    records, errors = store.list()
+    assert records == []
+    assert len(errors) == 1
+    assert path.name == errors[0]["file"]
+    assert "integrity" in errors[0]["error"]
+
+
+def test_load_raises_topup_run_integrity_error_for_unparseable_json(tmp_path):
+    root = tmp_path / "topup_runs"
+    root.mkdir(parents=True)
+    (root / "topup-2026-01-01-deadbeef0000.json").write_text("{not json")
+
+    store = TopupRunStore(root)
+    records, errors = store.list()
+    assert records == []
+    assert len(errors) == 1
+
+
+def test_corrupted_file_does_not_block_other_valid_records_from_listing(tmp_path):
+    root = tmp_path / "topup_runs"
+    store = TopupRunStore(root)
+    good = _record_sample(store)
+    bad_path = root / "topup-2026-01-01-deadbeef0000.json"
+    bad_path.write_text("{not json")
+
+    records, errors = store.list()
+    assert len(records) == 1 and records[0]["id"] == good["id"]
+    assert len(errors) == 1
+
+
+# --- resolve_desk_topup_log_dir -- zero new Config field -------------------------------------------
+
+
+def test_resolve_desk_topup_log_dir_defaults_to_a_sibling_of_the_universe_dir(monkeypatch):
+    monkeypatch.delenv("TAPEOLOGY_DESK_TOPUP_LOG_DIR", raising=False)
+    resolved = resolve_desk_topup_log_dir("/some/root/.data/universe")
+    assert resolved == "/some/root/.data/topup_runs"
+
+
+def test_resolve_desk_topup_log_dir_env_override(monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_DESK_TOPUP_LOG_DIR", "/tmp/custom-topup-log-dir")
+    assert resolve_desk_topup_log_dir("/some/root/.data/universe") == "/tmp/custom-topup-log-dir"
```
