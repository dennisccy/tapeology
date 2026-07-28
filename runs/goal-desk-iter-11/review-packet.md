# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 7. Shown in full: 6.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/tests/test_desk_topup_compute.py` (175 lines not shown)

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
index 762282d..43ab09e 100644
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
@@ -244,16 +266,28 @@ def test_an_unexpected_crash_outside_run_topup_resolves_state_failed(manager_env
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
 
 def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_reference(manager_env, monkeypatch):
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=["AAA"], raw_members={"AAA": "AAA"},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -261,7 +295,7 @@ def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_referenc
     monkeypatch.setattr(desk_topup_compute, "_run_one_pair", lambda *a: ("fetched", None))
 
     mgr = DeskTopupComputeManager()
-    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     snap = _wait_for_terminal(mgr)
     snap["progress"]["outcomes"].append({"poison": True})
     snap["progress"]["outcomes"][0]["outcome"] = "POISONED"
@@ -272,6 +306,48 @@ def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_referenc
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
@@ -280,7 +356,7 @@ def test_snapshot_returns_are_independent_copies_never_a_shared_mutable_referenc
 
 def test_first_run_fetches_every_pair_and_records_it(manager_env):
     """TC-6 mechanics (real path): a fresh store, every pair genuinely fetched."""
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -288,7 +364,7 @@ def test_first_run_fetches_every_pair_and_records_it(manager_env):
     adapter = _inject_adapter(bars=_bars())
 
     mgr = DeskTopupComputeManager()
-    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     snap = _wait_for_terminal(mgr)
 
     assert snap["state"] == "done"
@@ -301,7 +377,7 @@ def test_first_run_fetches_every_pair_and_records_it(manager_env):
 
 def test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls(manager_env):
     """TC-7: store-first proven end to end."""
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -309,14 +385,14 @@ def test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls(
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
@@ -326,6 +402,16 @@ def test_second_run_over_the_same_universe_is_all_reused_with_zero_vendor_calls(
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
@@ -338,7 +424,7 @@ def test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_
     "reused" with no growth in vendor calls; the rest must report "fetched". (The cancellation
     MECHANISM itself -- state transitions to "cancelled" with a partial outcomes list -- is proven
     separately, above, with a deterministic mocked fake.)"""
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=sorted(FIVE_MEMBERS), raw_members={m: m for m in FIVE_MEMBERS},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -355,7 +441,7 @@ def test_pairs_already_recorded_report_reused_while_the_rest_report_fetched_the_
     assert calls_after_prepopulate == len(pre_populated)
 
     mgr = DeskTopupComputeManager()
-    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     snap = _wait_for_terminal(mgr)
 
     assert snap["state"] == "done"
@@ -394,7 +480,7 @@ def test_a_failing_pair_reports_failed_with_the_detail_preserved_and_the_run_con
                 raise self._exc
             return self._bars
 
-    universe_store, bar_store, bar_index, registry = manager_env
+    universe_store, bar_store, bar_index, registry, topup_run_store = manager_env
     universe_store.record(
         members=sorted(TWO_MEMBERS), raw_members={m: m for m in TWO_MEMBERS},
         source_url="https://example.invalid/constituents", min_members=1, max_members=999,
@@ -405,7 +491,7 @@ def test_a_failing_pair_reports_failed_with_the_detail_preserved_and_the_run_con
     app.dependency_overrides[get_market_adapter] = lambda: adapter
 
     mgr = DeskTopupComputeManager()
-    mgr.trigger(universe_store, bar_store, bar_index, registry)
+    mgr.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)
     snap = _wait_for_terminal(mgr)
 
     assert snap["state"] == "done"  # the JOB completes even though one pair failed
@@ -418,6 +504,19 @@ def test_a_failing_pair_reports_failed_with_the_detail_preserved_and_the_run_con
     mgr.join_all(timeout=5)
     app.dependency_overrides.pop(get_market_adapter, None)
 
+    # TC-5 (J-09): the persisted record's failed pair carries its detail verbatim, and every OTHER
+    # pair (both before and after it in iteration order) is still present -- the run-level state is
+    # still "done" (a per-pair failure never demotes the run itself; see the module docstring's
+    # trap #2 distinction).
+    records, errors = topup_run_store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0]["state"] == "done"
+    persisted_failed = [o for o in records[0]["outcomes"] if o["outcome"] == "failed"]
+    assert len(persisted_failed) == 1
+    assert persisted_failed[0]["detail"] == failed[0]["detail"]
+    assert len(records[0]["outcomes"]) == len(TWO_MEMBERS) * len(DESK_TOPUP_TIMEFRAMES)
+
 
 # ==================================================================================================
 # Routes -- GET-never-computes, single-flight/cancel through HTTP, idle-cancel 409 (TC-15).
@@ -533,3 +632,186 @@ def test_cancel_while_running_succeeds_and_a_subsequent_cancel_is_409(route_ctx,
 
     idle_cancel = client.post("/research/desk/topup/compute/cancel")
     assert idle_cancel.status_code == 409
+
+
+# ==================================================================================================
+# GET /research/desk/topup/runs (J-09) -- honest-empty before any run, GET-never-computes,
+# meta-only list + full latest record, and the store's directory resolution (TC-14: already
+# scoped by `route_ctx`'s own `TAPEOLOGY_DESK_UNIVERSE_DIR` override -- `resolve_desk_topup_log_dir`
+# defaults to a SIBLING of it, exactly like `resolve_desk_screen_dir`, so no separate env var is
+# needed here).
... [diff_bound] apps/backend/tests/test_desk_topup_compute.py: 175 more diff lines omitted — Read the file for full detail
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
diff --git a/docs/goal.md b/docs/goal.md
index d914c31..b1c5879 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -564,6 +564,69 @@ order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding con
     `screen-2026-07-25-e184a7dc2f86` ranks NFLX #2 on `distance_bps 0.0` with no basis field in any
     row, so an 11-day spread of reading ages is invisible on one rank scale.)*
 
+- **J-09: Every top-up run leaves an append-only record of what it attempted**
+  - Steps:
+    1. Persist the top-up's OWN per-pair outcomes — the list `run_topup` already returns
+       (`desk_topup_compute.py:158`; entries `{"symbol", "timeframe", "outcome":
+       "reused"|"fetched"|"failed", "detail"}` built at :184, with the vendor/HTTP detail preserved
+       verbatim at :147) — as ONE frozen, checksummed, append-only run record per run, written once at
+       the run's terminal state by a SINGLE shared writer that BOTH callers use (the manager worker's
+       resolve path, :262/:282, and the CLI's `main`, :329): never two write paths, never a second
+       outcome shape, zero change to what `run_topup` itself computes. Recorded with it: run id,
+       universe snapshot id, the requested fetch window, `config_fingerprint`, started/finished UTC,
+       terminal state (`done`/`cancelled`/`failed`), `pairs_total` and `pairs_attempted` — so
+       "attempted and failed" and "never attempted" are distinct on the record, never conflated.
+    2. Own it exactly once: a new desk module (name at build discretion, e.g.
+       `app/research/desk_topup_log.py`) as the ONLY owner and `GET /research/desk/topup/runs` as the
+       ONLY serving endpoint (lightweight run-meta list + the latest full record; honest-empty
+       `{"runs": [], "latest": null}`, HTTP 200, before any run) — registered as a NEW row in the
+       blueprint's Data Contract BEFORE the code lands, storage dir a bare env-var-or-sibling default
+       like the screen store's (deliberately NOT a new `Config` field — the iter-3 precedent). The
+       record describes ATTEMPTS only: bar presence and freshness keep their single owner
+       (`desk_coverage` over `bar_index`) and no second coverage path is created anywhere.
+    3. Keep every era rail: page-load GETs never trigger a top-up (the 5C lesson); a record is never
+       rewritten, backfilled, or recomputed — a second run appends a new one; a run whose process ends
+       before its terminal write records NOTHING and the ledger never invents an entry for it (its
+       honest limit, asserted by a test); and NO MCP tool is added — J-06's exactly-17-tool contract
+       stays green and `get_endpoint`'s `/research/` allowlist already reaches the new path.
+    4. Surface it on `/desk`: a read-only "top-up runs" section beside the existing screen-history
+       table (same pattern, no recompute), each run showing date + id, universe snapshot id, terminal
+       state, attempted-of-total pairs and counts by outcome, and — for the latest run — every
+       `failed` pair with its recorded detail rendered verbatim plus the honest count of pairs the run
+       never reached; an honest empty state when no run is recorded; copy = descriptive measurement
+       only (no advice, imperative, urgency, or prediction language).
+    5. Test fixture-scoped: recorded outcomes byte-identical to `run_topup`'s return for the same
+       walk; a cancelled run recorded as `cancelled` with `pairs_attempted < pairs_total`; a failed
+       pair's detail stored verbatim; a second run appending without touching the first file; the GET
+       honest-empty before any run and triggering nothing.
+  - Acceptance: on the fixture-scoped rig `GET /research/desk/topup/runs` serves the honest empty
+    payload before any run and, after a fixture-scoped top-up, one record whose per-pair
+    `outcome`/`detail` values are byte-identical to what `run_topup` returned for that walk
+    (**single source of truth**: the run record is registered in the Data Contract with the new desk
+    module as its only owner and `GET /research/desk/topup/runs` as its only serving endpoint, it
+    records attempts only, and coverage/freshness still comes solely from `desk_coverage` over
+    `bar_index` — this SSOT criterion stands in place of a PnL-ledger append, which this era's
+    Non-Goals forbid); a cancelled run records `cancelled` with `pairs_attempted < pairs_total`, and a
+    run interrupted before its terminal write leaves the ledger honestly empty rather than a
+    fabricated entry; a second run appends a new record while every previously recorded file stays
+    byte-identical on disk (checksums unchanged); in a real browser after the T-9 clean rebuild,
+    `/desk` shows the honest no-run-recorded state in one screenshot and, after a fixture-scoped run,
+    the top-up-runs section with attempted-of-total, per-outcome counts and at least one `failed`
+    pair's recorded detail legible in another (T-10: no screenshot ⇒ `unknown`, never `passing`); a
+    **`[NEW]`-flagged demo-narrator walkthrough** covers the top-up-run disclosure end to end; and the
+    full backend suite is green with `Config().config_fingerprint()` still `08e471b10130e1e2`, zero
+    new `Config` fields, the `default` profile and `v1` byte-identical (engine equivalence green), the
+    MCP surface still exactly 17 tools, zero diff to
+    `tradability.py`/`levels.py`/`bars.py`/`StructureChart.tsx`, and `tests/test_copy_discipline.py`
+    green unmodified. *(Keyless core; browser-verifiable. Why: measured live 2026-07-28 —
+    `GET /research/desk/topup/compute` returns `null`, so the real ~100-symbol run that populated the
+    store left no trace anywhere; the frozen `BarStore` holds series for 65 symbols and 38 of the 101
+    members of `universe-2026-07-25-49b33fa31680` (the alphabetical tail `MA`…`XOM`) hold none —
+    exactly the 38 `skipped: no bars` rows of `screen-2026-07-27-936543601e75` (63 ranked / 38
+    skipped) — while 5 further members (AXP, BAC, DIS, HD, LMT) rank with `1h` dark beside a `4h`
+    series the era-5 contract resamples from that same `1h` fetch, so whether a pair was attempted,
+    refused, or never reached is unknowable today.)*
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-desk/state/assumptions.md        | 78 ++++++++++++++++++++++
 runs/goal-session-desk/state/blueprint.md          | 32 ++++++++-
 .../state/enhancement-proposals.jsonl              |  1 +
 runs/goal-session-desk/state/proposer-result.json  |  8 +--
 runs/goal-session-desk/telemetry.jsonl             | 19 ++++++
 runs/goal-session-desk/trace/trace.jsonl           |  5 ++
 6 files changed, 133 insertions(+), 10 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
