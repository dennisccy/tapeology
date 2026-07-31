# Iteration diff (bounded)

Files changed: 9. Shown in full: 9.

```diff
diff --git a/apps/backend/app/research/desk_routes.py b/apps/backend/app/research/desk_routes.py
index 13a7962..d4fe2e7 100644
--- a/apps/backend/app/research/desk_routes.py
+++ b/apps/backend/app/research/desk_routes.py
@@ -39,7 +39,7 @@ over ``desk_index_reconcile.py`` — see that module's own docstring for the cla
 mechanics. No new MCP tool (``get_endpoint``'s existing ``/research/`` allowlist already reaches the
 new GET path); no new router, no ``main.py`` change.
 
-J-12 (this iteration, goal-desk-iter-16) is a pure additive-read + disclosure change, no new
+J-12 (goal-desk-iter-16) is a pure additive-read + disclosure change, no new
 module/route/MCP tool: (a) ``GET /research/desk/screen`` gains a sibling ``?id=`` read so an
 EARLIER same-``screen_date`` recording — unreachable via ``?date=``, which always resolves to the
 newest match — becomes individually addressable by its own id; supplying both ``?id=`` and
@@ -47,6 +47,20 @@ newest match — becomes individually addressable by its own id; supplying both
 discarding their own ``store.list()``'s ``errors`` return — both now serve it as
 ``integrity_errors``, the identical key/shape ``get_screen``/``get_universe`` already used.
 
+J-18 (this iteration, goal-desk-iter-29) adds ONE new read: ``GET /research/desk/screen/runs`` (the
+durable, append-only screen-RUN log — ``desk_screen_log.py``'s lightweight run-meta list + the
+latest full record + ``integrity_errors``; honest-empty ``{"runs": [], "latest": null,
+"integrity_errors": []}`` before any run, never a 404) — the SAME shape its two siblings
+(``get_topup_runs``/``get_desk_index_reconcile_runs``) already serve. No new compute manager, no
+new POST — the log is written internally by ``run_screen_and_record`` (the single shared writer
+both ``DeskScreenComputeManager`` and the CLI call), which also now resolves the screen's five pins
+BEFORE the walk and short-circuits an identical-pin retrigger to the existing snapshot (zero
+``compute_tradability`` calls) — see ``desk_screen_compute.py``'s own module docstring. This route
+only threads a ``ScreenRunStore`` dependency through ``trigger_desk_screen_compute``; the route
+itself is a pure read, mirroring ``GET /research/desk/topup/runs``'s single-synchronous-read shape
+exactly. No new MCP tool (``get_endpoint``'s existing ``/research/`` allowlist already reaches the
+new GET path); no new router, no ``main.py`` change.
+
 **Compute managers are module-level singletons here, NOT ``ResearchRegistry`` properties.**
 ``DeskTopupComputeManager`` (``desk_topup_compute.py``) reuses ``routes.record_bar_series``
 in-process, so it must import FROM ``routes.py`` — if ``ResearchRegistry`` held the manager (the
@@ -77,6 +91,7 @@ from .desk_index_reconcile import (
 )
 from .desk_screen import ScreenStore, resolve_desk_screen_dir
 from .desk_screen_compute import DeskScreenComputeManager
+from .desk_screen_log import ScreenRunStore, resolve_desk_screen_log_dir
 from .desk_topup_compute import DeskTopupComputeManager
 from .desk_topup_log import TopupRunStore, resolve_desk_topup_log_dir
 from .desk_universe import (
@@ -309,6 +324,15 @@ def get_screen_store() -> ScreenStore:
     return ScreenStore(resolve_desk_screen_dir(CONFIG.desk_universe_dir_resolved()))
 
 
+def get_screen_run_store() -> ScreenRunStore:
+    """goal-desk-iter-29 (J-18): the durable screen-run log store rooted at a bare
+    env-var-or-sibling-of-the-universe-dir default (zero new ``Config`` field — see
+    ``desk_screen_log.resolve_desk_screen_log_dir``) — the ``get_topup_run_store``/
+    ``get_reconcile_run_store`` pattern. A FastAPI dependency so tests can point it at a temp dir
+    via the env var or override it outright."""
+    return ScreenRunStore(resolve_desk_screen_log_dir(CONFIG.desk_universe_dir_resolved()))
+
+
 def _screen_meta_only(record: dict) -> dict:
     """The lightweight projection ``GET /research/desk/screen``'s bulk list serves — id/pins/
     counts only, NEVER the full ``rows``/``skipped`` arrays (see ``desk_screen.py``'s module
@@ -388,6 +412,7 @@ def trigger_desk_screen_compute(
     dataset_store: DatasetStore = Depends(get_dataset_store),
     screen_store: ScreenStore = Depends(get_screen_store),
     manager: DeskScreenComputeManager = Depends(get_desk_screen_compute_manager),
+    screen_run_store: ScreenRunStore = Depends(get_screen_run_store),
 ) -> dict:
     """Start the single-flight desk screen compute job for ``body.screen_date``, or — if one is
     already running — return it UNCHANGED (``started: False``, never a second concurrent job).
@@ -403,7 +428,12 @@ def trigger_desk_screen_compute(
     of them failed its integrity check, so the refusal names that cause separately rather than
     telling the operator nothing is registered when something is (era-desk-iter-4 audit B2): the
     action a damaged snapshot needs (look at the named file) is not the action an absent one needs
-    (fetch a universe)."""
+    (fetch a universe).
+
+    goal-desk-iter-29 (J-18): ``screen_run_store`` is threaded straight through to
+    ``manager.trigger`` so this run's terminal outcome (done/cancelled/failed/reused) is durably
+    logged — this route only threads the dependency through; the pre-check/reuse-short-circuit and
+    the actual record write both live inside ``run_screen_and_record``."""
     records, errors = universe_store.list()
     if not records:
         if errors:
@@ -422,6 +452,7 @@ def trigger_desk_screen_compute(
         )
     return manager.trigger(
         body.screen_date, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store,
+        screen_run_store=screen_run_store,
     )
 
 
@@ -449,6 +480,39 @@ def cancel_desk_screen_compute(
     return {"cancelling": True}
 
 
+# --- The screen run log (goal-desk-iter-29, J-18) — ONE read: a lightweight run-meta list + the
+# latest full record. No POST here: the log is written internally by `run_screen_and_record` (the
+# single shared writer, `desk_screen_log.record_screen_run`) — this route is a pure read, mirroring
+# `GET /research/desk/topup/runs`'s exact honest-empty/meta-only-list/full-latest/
+# `integrity_errors` shape. -------------------------------------------------------------------------
+
+
+def _screen_run_meta_only(record: dict) -> dict:
+    """The lightweight projection ``GET /research/desk/screen/runs``'s bulk list serves — every
+    field EXCEPT ``ranked_count``/``skipped_by_reason``/``error``/``failed_member`` (mirrors
+    ``_topup_run_meta_only``'s identical convention)."""
+    heavy_keys = ("ranked_count", "skipped_by_reason", "error", "failed_member")
+    return {key: value for key, value in record.items() if key not in heavy_keys}
+
+
+@router.get("/screen/runs")
+def get_screen_runs(store: ScreenRunStore = Depends(get_screen_run_store)) -> dict:
+    """``{"runs": [...meta-only...], "latest": <full record>|null, "integrity_errors": [...]}`` —
+    an explicit HTTP 200 honest-empty payload (``{"runs": [], "latest": null,
+    "integrity_errors": []}``) before any screen run has ever reached its terminal state, never a
+    404 (the ``GET /research/desk/topup/runs`` convention). ``latest`` is the most recently STARTED
+    run, verbatim from disk — never recomputed on the GET. ``integrity_errors`` is ``store.list()``'s
+    own ``errors`` return, surfaced verbatim (the J-12 convention) — a corrupted run-record file
+    stays excluded from ``runs``/``latest`` either way, never fabricated, never crashes this
+    route."""
+    records, errors = store.list()
+    return {
+        "runs": [_screen_run_meta_only(r) for r in records],
+        "latest": records[-1] if records else None,
+        "integrity_errors": errors,
+    }
+
+
 # --- Coverage-index reconciliation (J-10, goal-desk-iter-14) — a trigger/poll/cancel trio mirroring
 # the top-up compute trio exactly, plus ONE durable read mirroring ``GET /research/desk/topup/runs``.
 # See ``desk_index_reconcile.py`` for the classify/repair/record mechanics this only wires up. -------
diff --git a/apps/backend/app/research/desk_screen_compute.py b/apps/backend/app/research/desk_screen_compute.py
index c55e0ec..e91e3c5 100644
--- a/apps/backend/app/research/desk_screen_compute.py
+++ b/apps/backend/app/research/desk_screen_compute.py
@@ -33,7 +33,30 @@ hard "zero recompute calls on retrigger" proof (unlike TC-15's explicit ``BarSto
 for ``bar_store_signature``); a future iteration can add a cheap pre-check (the five pins resolve
 synchronously before the walk, the SAME way ``members_total`` already does) if a real retrigger's
 latency is ever measured to matter -- the same "measure first, optimize later" discipline
-``bars.py``/``datasets.py``'s own stat-keyed caches followed."""
+``bars.py``/``datasets.py``'s own stat-keyed caches followed.
+
+**goal-desk-iter-29 (J-18) -- that future iteration, arrived.** ``run_screen_and_record`` now
+resolves the run's five pins BEFORE calling ``compute_screen`` at all, using ONLY existing
+accessors (``screen_as_of``, ``UniverseStore.list``, ``Config.config_fingerprint``,
+``desk_screen.compute_bar_store_signature`` over ``desk_coverage`` -- zero new derivation, zero new
+``BarStore`` read beyond the index-only coverage read that accessor itself makes). A
+``ScreenStore.find_by_key`` hit on those five pins short-circuits IMMEDIATELY: the existing
+snapshot is returned with ``reused=True``, ``compute_tradability`` is called ZERO times, and
+``compute_screen`` itself is never invoked. A miss runs the full walk exactly as it always has (zero
+behavior change to ``compute_screen``) -- the "structural backstop" ``ScreenStore.record``'s own
+``ScreenAlreadyRecorded`` refusal provides for the rare race where the store changes UNDER a running
+walk is untouched and still fires in that case.
+
+Independently, this function now also persists ONE durable, checksummed, append-only RUN record
+(``desk_screen_log.py``, mirrors the J-09/J-10 run-log discipline verbatim) at its own terminal
+outcome (done/cancelled/failed) via the single shared writer ``record_screen_run`` -- called from
+inside THIS function (the ONE shared entry point both ``DeskScreenComputeManager``'s resolve path
+and the CLI's ``main()`` already call), optional via the ``screen_run_store`` parameter (default
+``None`` -- a caller that does not supply one gets no durable record, so every EXISTING caller of
+this function keeps working unmodified; the real HTTP route and the CLI always supply a real
+store). This changes NOTHING about ``compute_screen``'s own walk semantics or ``ScreenStore``'s own
+recorded snapshot/row/skip shapes -- it only makes the RUN's own outcome legible, the same way
+``desk_topup_log.py``/``desk_index_reconcile.py`` already do for their own compute managers."""
 
 from __future__ import annotations
 
@@ -47,12 +70,36 @@ from ..config import CONFIG, Config
 from .bar_index import BarIndex
 from .bars import BarStore
 from .datasets import DatasetStore
-from .desk_screen import ScreenAlreadyRecorded, ScreenStore, compute_screen, resolve_desk_screen_dir
+from .desk_screen import (
+    ScreenAlreadyRecorded,
+    ScreenStore,
+    compute_bar_store_signature,
+    compute_screen,
+    resolve_desk_screen_dir,
+    screen_as_of,
+)
+from .desk_screen_log import ScreenRunStore, record_screen_run, resolve_desk_screen_log_dir
 from .desk_universe import UniverseStore
 from .routes import get_bar_index, get_bar_store, get_dataset_store
 
 __all__ = ["DeskScreenComputeManager", "run_screen_and_record"]
 
+# The two skip reasons ``compute_screen`` ever records (``desk_screen.py``'s own module docstring:
+# "Skip reasons -- exactly two, never conflated") -- the honest zero-tally a run log entry starts
+# from before counting a walk's (partial or full) own skipped rows.
+_EMPTY_SKIPPED_BY_REASON = {"no_bars": 0, "no_basis": 0}
+
+
+def _tally_skipped_by_reason(skipped: list[dict]) -> dict:
+    """A plain per-reason count of ``compute_screen``'s own ``skipped`` list -- goal-desk-iter-29
+    (J-18), the ``desk_screen._bands_by_class``-style "plain dict tally" construction, applied to
+    the two reasons ``desk_screen.py`` itself ever produces. Never a third bucket, never a
+    recomputation of WHY a member was skipped -- each entry's own ``reason`` is read verbatim."""
+    tally = dict(_EMPTY_SKIPPED_BY_REASON)
+    for entry in skipped:
+        tally[entry["reason"]] = tally.get(entry["reason"], 0) + 1
+    return tally
+
 
 def _iso_utc_now() -> str:
     return (
@@ -81,6 +128,7 @@ def run_screen_and_record(
     *,
     progress: Callable[[dict], None] | None = None,
     should_abort: Callable[[], bool] | None = None,
+    screen_run_store: ScreenRunStore | None = None,
 ) -> tuple[dict | None, bool]:
     """Compute ONE screen (``compute_screen`` -- the sole walker) and persist it, append-only.
     Returns ``(record, reused)``:
@@ -93,31 +141,147 @@ def run_screen_and_record(
         caught here, not propagated, since reusing an already-recorded snapshot is a normal,
         expected outcome, not a failure (era-desk-iter-4 J-04, audit B2: this ``reused`` flag is
         what lets a caller distinguish "this job's walk is what created the snapshot" from "this
-        job's walk found an already-recorded one and changed nothing")."""
-    result = compute_screen(
-        universe_store, bar_store, bar_index, dataset_store, config, screen_date,
-        progress=progress, should_abort=should_abort,
+        job's walk found an already-recorded one and changed nothing").
+
+    goal-desk-iter-29 (J-18): the five pins are resolved BEFORE any walk, using ONLY existing
+    accessors -- a ``ScreenStore.find_by_key`` hit short-circuits immediately (``reused=True``,
+    ``members_attempted=0``, ZERO ``compute_screen``/``compute_tradability`` calls); a miss runs
+    ``compute_screen`` exactly as before. If ``screen_run_store`` is given, this function ALSO
+    persists exactly one durable run record (``desk_screen_log.record_screen_run``) at its own
+    terminal outcome -- ``screen_run_store=None`` (the default) skips this entirely, so every
+    EXISTING caller that does not pass one keeps working unmodified."""
+    started_utc = _iso_utc_now()
+
+    as_of = screen_as_of(screen_date)
+    universe_records, _universe_errors = universe_store.list()
+    universe_snapshot_id = universe_records[-1]["id"] if universe_records else None
+    members = list(universe_records[-1]["members"]) if universe_records else []
+    members_total = len(members)
+    config_fingerprint = config.config_fingerprint()
+    bar_store_signature = compute_bar_store_signature(universe_store, bar_index)
+
+    # goal-desk-iter-29 audit (B1): the run log is written EXACTLY ONCE per run -- structurally, not
+    # by convention. Without this latch, a terminal write that itself RAISES (a full disk, a
+    # read-only log dir) would be caught by the outer `except Exception` below and re-entered as a
+    # SECOND, "failed" record for the same run -- a fabricated terminal state (the snapshot really
+    # was recorded) carrying the LEDGER's own I/O error as if it were a screen failure. With it, a
+    # failed terminal write leaves NO record at all (the module's own documented interrupted-run
+    # honesty) and the I/O error still propagates verbatim -- never silently swallowed.
+    logged = False
+
+    def _log(
+        *,
+        state: str,
+        reused: bool,
+        members_attempted: int,
+        ranked_count: int,
+        skipped_by_reason: dict,
+        screen_id: str | None,
+        error: str | None,
+        failed_member: str | None,
+    ) -> None:
+        nonlocal logged
+        if screen_run_store is None or logged:
+            return
+        logged = True
+        record_screen_run(
+            screen_run_store,
+            screen_date=screen_date,
+            universe_snapshot_id=universe_snapshot_id,
+            config_fingerprint=config_fingerprint,
+            bar_store_signature=bar_store_signature,
+            started_utc=started_utc,
+            finished_utc=_iso_utc_now(),
+            state=state,
+            reused=reused,
+            members_total=members_total,
+            members_attempted=members_attempted,
+            ranked_count=ranked_count,
+            skipped_by_reason=skipped_by_reason,
+            screen_id=screen_id,
+            error=error,
+            failed_member=failed_member,
+        )
+
+    # goal-desk-iter-29 (J-18) step 2: an already-recorded pin set is answered WITHOUT paying for
+    # the walk -- zero `compute_screen`/`compute_tradability` calls, no `BarStore` read beyond the
+    # index-only coverage read `compute_bar_store_signature` already made above.
+    existing = screen_store.find_by_key(
+        screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature
     )
-    if should_abort is not None and should_abort():
-        return None, False
-    try:
-        return screen_store.record(
-            screen_date=result["screen_date"],
-            as_of=result["as_of"],
-            universe_snapshot_id=result["universe_snapshot_id"],
-            config_fingerprint=result["config_fingerprint"],
-            bar_store_signature=result["bar_store_signature"],
-            rows=result["rows"],
-            skipped=result["skipped"],
-        ), False
-    except ScreenAlreadyRecorded as exc:
-        existing = screen_store.find_by_key(
-            result["screen_date"], result["as_of"], result["universe_snapshot_id"],
-            result["config_fingerprint"], result["bar_store_signature"],
+    if existing is not None:
+        _log(
+            state="done", reused=True, members_attempted=0, ranked_count=0,
+            skipped_by_reason=dict(_EMPTY_SKIPPED_BY_REASON), screen_id=existing["id"],
+            error=None, failed_member=None,
         )
-        assert existing is not None and existing["id"] == exc.existing_id
         return existing, True
 
+    attempted = 0
+
+    def _counting_progress(entry: dict) -> None:
+        nonlocal attempted
+        attempted += 1
+        if progress is not None:
+            progress(entry)
+
+    try:
+        result = compute_screen(
+            universe_store, bar_store, bar_index, dataset_store, config, screen_date,
+            progress=_counting_progress, should_abort=should_abort,
+        )
+
+        if should_abort is not None and should_abort():
+            _log(
+                state="cancelled", reused=False, members_attempted=attempted,
+                ranked_count=len(result["rows"]),
+                skipped_by_reason=_tally_skipped_by_reason(result["skipped"]),
+                screen_id=None, error=None, failed_member=None,
+            )
+            return None, False
+
+        try:
+            recorded = screen_store.record(
+                screen_date=result["screen_date"],
+                as_of=result["as_of"],
+                universe_snapshot_id=result["universe_snapshot_id"],
+                config_fingerprint=result["config_fingerprint"],
+                bar_store_signature=result["bar_store_signature"],
+                rows=result["rows"],
+                skipped=result["skipped"],
+            )
+            _log(
+                state="done", reused=False, members_attempted=attempted,
+                ranked_count=len(result["rows"]),
+                skipped_by_reason=_tally_skipped_by_reason(result["skipped"]),
+                screen_id=recorded["id"], error=None, failed_member=None,
+            )
+            return recorded, False
+        except ScreenAlreadyRecorded as exc:
+            existing2 = screen_store.find_by_key(
+                result["screen_date"], result["as_of"], result["universe_snapshot_id"],
+                result["config_fingerprint"], result["bar_store_signature"],
+            )
+            assert existing2 is not None and existing2["id"] == exc.existing_id
+            _log(
+                state="done", reused=True, members_attempted=attempted,
+                ranked_count=len(result["rows"]),
+                skipped_by_reason=_tally_skipped_by_reason(result["skipped"]),
+                screen_id=existing2["id"], error=None, failed_member=None,
+            )
+            return existing2, True
+    except Exception as exc:  # noqa: BLE001 -- any OTHER failure (a raising member inside
+        # `compute_screen`, or a `ScreenIntegrityError` from a damaged snapshot at this key) --
+        # logged as "failed", then RE-RAISED verbatim so every existing caller's own crash-handling
+        # (the manager's `_work` except-clause, an uncaught CLI crash) stays byte-unchanged.
+        failed_member = members[attempted] if attempted < len(members) else None
+        _log(
+            state="failed", reused=False, members_attempted=attempted, ranked_count=0,
+            skipped_by_reason=dict(_EMPTY_SKIPPED_BY_REASON), screen_id=None,
+            error=str(exc), failed_member=failed_member,
+        )
+        raise
+
 
 class DeskScreenComputeManager:
     """Owns the SINGLE in-flight (or last-terminal) desk screen compute job. Construct with no
@@ -147,13 +311,21 @@ class DeskScreenComputeManager:
         dataset_store: DatasetStore,
         config: Config,
         screen_store: ScreenStore,
+        *,
+        screen_run_store: ScreenRunStore | None = None,
     ) -> dict:
         """Start a NEW screen compute job for ``screen_date``, or -- if one is already
         ``state == "running"`` -- return it UNCHANGED (``started: False``, single-flight, TC-7).
         Once the current job is terminal (done/cancelled/failed, or none has ever run), the NEXT
         call always starts a genuinely new job (a fresh id), discarding the prior snapshot. Never
         blocks -- the walk runs on a dedicated worker thread, off the caller's thread, so an HTTP
-        route calling this returns immediately."""
+        route calling this returns immediately.
+
+        goal-desk-iter-29 (J-18): ``screen_run_store``, if given, is threaded straight through to
+        ``run_screen_and_record`` -- an OPTIONAL, keyword-only, per-call dependency (default
+        ``None``, unlike J-09/J-10's REQUIRED ``topup_run_store``/``reconcile_run_store``) so every
+        EXISTING test that calls ``trigger`` positionally with no run-store argument keeps passing
+        unmodified; the real HTTP route (``desk_routes.py``) always supplies a real store."""
         with self._lock:
             current = self._snapshot
             if current is not None and current["state"] == "running":
@@ -199,6 +371,7 @@ class DeskScreenComputeManager:
                 record, reused = run_screen_and_record(
                     universe_store, bar_store, bar_index, dataset_store, config, screen_store,
                     screen_date, progress=_publish, should_abort=cancel_event.is_set,
+                    screen_run_store=screen_run_store,
                 )
             except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                 self._resolve(job_id, "failed", error=str(exc))
@@ -290,10 +463,15 @@ def main() -> int:
     bar_index = get_bar_index()
     dataset_store = get_dataset_store()
     screen_store = ScreenStore(resolve_desk_screen_dir(config.desk_universe_dir_resolved()))
+    # goal-desk-iter-29 (J-18): the SAME single shared writer the HTTP route uses -- a run started
+    # from this CLI is durably logged exactly like one started from `/desk`'s Run Screen button.
+    screen_run_store = ScreenRunStore(
+        resolve_desk_screen_log_dir(config.desk_universe_dir_resolved())
+    )
 
     recorded, reused = run_screen_and_record(
         universe_store, bar_store, bar_index, dataset_store, config, screen_store,
-        args.date, progress=_cli_progress_printer(),
+        args.date, progress=_cli_progress_printer(), screen_run_store=screen_run_store,
     )
     print(
         f"desk screen complete for {args.date}: {len(recorded['rows'])} ranked, "
diff --git a/apps/backend/tests/test_desk_screen_compute.py b/apps/backend/tests/test_desk_screen_compute.py
index 889e8f9..ed3ad4b 100644
--- a/apps/backend/tests/test_desk_screen_compute.py
+++ b/apps/backend/tests/test_desk_screen_compute.py
@@ -25,13 +25,14 @@ from fastapi.testclient import TestClient
 from app.config import CONFIG
 from app.main import app, get_market_adapter, manager as ws_manager
 from app.providers.adapters.base import RawBar
-from app.research import desk_screen_compute
+from app.research import desk_screen, desk_screen_compute
 from app.research.bar_index import BarIndex
 from app.research.bars import BarStore
 from app.research.datasets import DatasetStore
 from app.research.desk_routes import get_desk_screen_compute_manager
 from app.research.desk_screen import ScreenStore
 from app.research.desk_screen_compute import DeskScreenComputeManager, run_screen_and_record
+from app.research.desk_screen_log import ScreenRunStore
 from app.research.desk_universe import UniverseStore
 from app.research.routes import ResearchRegistry, set_registry
 from app.research.store import JournalStore
@@ -729,3 +730,318 @@ def test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot(
     screen_store = ScreenStore(tmp_path / "screen")
     records, errors = screen_store.list()
     assert errors == [] and len(records) == 1  # no second file
+
+
+# ==================================================================================================
+# goal-desk-iter-29 (J-18) -- the screen-run log: the five-pin pre-check reuse short-circuit, and
+# ONE durable run record per terminal outcome (done/cancelled/failed), written by
+# `record_screen_run` from INSIDE `run_screen_and_record` (the one shared entry point both the
+# manager and the CLI call). TC-2 through TC-9 -- the three pre-existing tests named in the plan
+# (`test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file`,
+# `test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot`,
+# `test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite`, all
+# above) are untouched by this section.
+# ==================================================================================================
+
+
+@pytest.fixture
+def run_log_ctx(real_ctx, tmp_path):
+    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
+    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")
+    return universe_store, bar_store, bar_index, dataset_store, screen_store, screen_run_store
+
+
+def _skip_tally(skipped: list[dict]) -> dict:
+    tally = {"no_bars": 0, "no_basis": 0}
+    for entry in skipped:
+        tally[entry["reason"]] += 1
+    return tally
+
+
+def test_tc2_tc4_a_pin_miss_run_walks_every_member_and_records_a_matching_run_log_entry(run_log_ctx):
+    """TC-2/TC-4: a fresh pin set walks every member and records ONE run whose counts/pins/
+    ``screen_id`` are byte-identical to the snapshot it produced."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store, screen_run_store = run_log_ctx
+
+    recorded, reused = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+        screen_run_store=screen_run_store,
+    )
+    assert reused is False
+
+    records, errors = screen_run_store.list()
+    assert errors == [] and len(records) == 1
+    run = records[0]
+    assert run["state"] == "done"
+    assert run["reused"] is False
+    assert run["screen_date"] == recorded["screen_date"]
+    assert run["universe_snapshot_id"] == recorded["universe_snapshot_id"]
+    assert run["config_fingerprint"] == recorded["config_fingerprint"]
+    assert run["bar_store_signature"] == recorded["bar_store_signature"]
+    assert run["screen_id"] == recorded["id"]
+    assert run["members_total"] == run["members_attempted"]
+    assert run["ranked_count"] == len(recorded["rows"])
+    assert run["skipped_by_reason"] == _skip_tally(recorded["skipped"])
+    assert run["error"] is None and run["failed_member"] is None
+
+
+def test_tc3_an_identical_pin_retrigger_makes_zero_compute_tradability_calls_and_reuses(
+    run_log_ctx, monkeypatch,
+):
+    """TC-3: the reuse short-circuit resolves the five pins and hits ``ScreenStore.find_by_key``
+    BEFORE ``compute_screen`` (and therefore ``compute_tradability``) is ever called -- a real
+    call-counting wrapper around the REAL ``compute_tradability`` proves zero NEW calls on the
+    second, identical-pin invocation."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store, screen_run_store = run_log_ctx
+
+    calls = {"n": 0}
+    real_compute_tradability = desk_screen.compute_tradability
+
+    def _counting_compute_tradability(*args, **kwargs):
+        calls["n"] += 1
+        return real_compute_tradability(*args, **kwargs)
+
+    monkeypatch.setattr(desk_screen, "compute_tradability", _counting_compute_tradability)
+
+    first, first_reused = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+        screen_run_store=screen_run_store,
+    )
+    assert first_reused is False
+    calls_after_first = calls["n"]
+    assert calls_after_first > 0  # the fixture universe has more than zero members
+
+    second, second_reused = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+        screen_run_store=screen_run_store,
+    )
+    assert second_reused is True
+    assert second["id"] == first["id"]
+    assert calls["n"] == calls_after_first, "the retrigger must make ZERO new compute_tradability calls"
+
+    records, errors = screen_run_store.list()
+    assert errors == [] and len(records) == 2  # two DISTINCT run-log entries -- one per attempt
+    second_run = records[1]
+    assert second_run["reused"] is True
+    assert second_run["members_attempted"] == 0
+    assert second_run["screen_id"] == first["id"]
+
+    screen_records, screen_errors = screen_store.list()
+    assert screen_errors == [] and len(screen_records) == 1  # no second screen snapshot file
+
+
+def test_tc5_a_cancellation_mid_walk_records_state_cancelled_with_partial_attempts_and_no_snapshot(
+    manager_env, monkeypatch, tmp_path,
+):
+    """TC-5: a walk cancelled partway through records ``state: "cancelled"``,
+    ``members_attempted < members_total``, ``screen_id: null`` -- and no snapshot file."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")
+
+    def fake_compute_screen(_us, _bs, _bi, _ds, _cfg, _sd, *, progress=None, should_abort=None):
+        rows: list[dict] = []
+        skipped: list[dict] = []
+        for symbol in SMALL_MEMBERS:
+            if should_abort is not None and should_abort():
+                break
+            skipped.append(
+                {"symbol": symbol, "skipped": True, "reason": "no_bars", "coverage": {}, "tick_evidence": False}
+            )
+            if progress is not None:
+                progress({"symbol": symbol})
+        return {
+            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
+            "config_fingerprint": "y", "bar_store_signature": "z", "rows": rows, "skipped": skipped,
+        }
+
+    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
+
+    calls = {"n": 0}
+
+    def should_abort() -> bool:
+        calls["n"] += 1
+        return calls["n"] > 1  # let the first member through, abort before the second
+
+    result, reused = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+        should_abort=should_abort, screen_run_store=screen_run_store,
+    )
+    assert result is None
+    assert reused is False
+
+    records, errors = screen_run_store.list()
+    assert errors == [] and len(records) == 1
+    run = records[0]
+    assert run["state"] == "cancelled"
+    assert run["members_attempted"] < run["members_total"]
+    assert run["screen_id"] is None
+    assert run["error"] is None
+
+    screen_records, _errors = screen_store.list()
+    assert screen_records == []
+
+
+def test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member(
+    manager_env, monkeypatch, tmp_path,
+):
+    """TC-6: a member whose computation raises during the walk records ``state: "failed"`` with
+    the exception detail verbatim and the raising member's own name -- and no snapshot file. The
+    raise ALSO propagates out of ``run_screen_and_record`` itself (re-raised after logging), so the
+    manager's/CLI's own existing crash-handling stays byte-unchanged."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")
+
+    def fake_compute_screen(_us, _bs, _bi, _ds, _cfg, _sd, *, progress=None, should_abort=None):
+        for symbol in SMALL_MEMBERS:  # sorted: ["AAA", "BBB"]
+            if symbol == "BBB":
+                raise RuntimeError("synthetic raise on member BBB")
+            if progress is not None:
+                progress({"symbol": symbol})
+        raise AssertionError("unreachable -- BBB always raises before this point")
+
+    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
+
+    with pytest.raises(RuntimeError, match="synthetic raise on member BBB"):
+        run_screen_and_record(
+            universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+            screen_run_store=screen_run_store,
+        )
+
+    records, errors = screen_run_store.list()
+    assert errors == [] and len(records) == 1
+    run = records[0]
+    assert run["state"] == "failed"
+    assert run["error"] == "synthetic raise on member BBB"
+    assert run["failed_member"] == "BBB"
+    assert run["screen_id"] is None
+    assert run["reused"] is False
+
+    screen_records, _errors = screen_store.list()
+    assert screen_records == []
+
+
+def test_tc7_omitting_the_run_store_leaves_no_durable_record_for_that_run(real_ctx, tmp_path):
+    """TC-7: a process that ends before the writer's terminal call (simulated here by simply never
+    supplying a ``screen_run_store``) leaves the ledger with no entry for that run -- the SAME
+    "structural, not policed" guarantee ``test_desk_screen_log.py`` proves at the store level,
+    exercised here through the real run path."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = real_ctx
+
+    recorded, reused = run_screen_and_record(
+        universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+    )
+    assert recorded is not None and reused is False
+
+    # A store constructed AFTER the run, pointed at where a run log WOULD have lived, still finds
+    # nothing -- the run never called the writer, so nothing was ever written.
+    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")
+    records, errors = screen_run_store.list()
+    assert records == [] and errors == []
+
+
+# --- Route-level: TC-1 (honest empty) + TC-8 (two sequential runs) --------------------------------
+
+
+def test_tc1_get_screen_runs_before_any_run_is_an_honest_empty_200(route_ctx):
+    client, _mgr, _tmp_path = route_ctx
+    r = client.get("/research/desk/screen/runs")
+    assert r.status_code == 200
+    assert r.json() == {"runs": [], "latest": None, "integrity_errors": []}
+
+
+def test_tc8_two_sequential_triggers_append_two_run_records_first_file_byte_unchanged(route_ctx):
+    """TC-8: a second (genuinely distinct-pin) trigger appends a new run record while the first
+    run's own log file stays byte-identical on disk, and the meta-only ``runs`` list carries both."""
+    client, fresh_manager, tmp_path = route_ctx
+    UniverseStore(tmp_path / "universe").record(
+        members=["AAA"], raw_members={"AAA": "AAA"},
+        source_url="https://example.invalid/constituents", min_members=1, max_members=999,
+    )
+
+    def _trigger_and_wait(screen_date: str) -> dict:
+        resp = client.post("/research/desk/screen/compute", json={"screen_date": screen_date})
+        assert resp.status_code == 200
+        deadline = time.time() + 5
+        snap = None
+        while time.time() < deadline:
+            snap = client.get("/research/desk/screen/compute").json()
+            if snap is not None and snap["state"] != "running":
+                break
+            time.sleep(0.02)
+        assert snap is not None and snap["state"] == "done"
+        return snap
+
+    first_snap = _trigger_and_wait(SCREEN_DATE)
+    assert first_snap["reused"] is False
+
+    log_dir = tmp_path / "screen_runs"
+    first_files = sorted(log_dir.glob("*.json"))
+    assert len(first_files) == 1
+    first_bytes = first_files[0].read_bytes()
+
+    runs_after_first = client.get("/research/desk/screen/runs").json()
+    assert len(runs_after_first["runs"]) == 1
+    assert runs_after_first["latest"]["state"] == "done"
+    assert "ranked_count" in runs_after_first["latest"]
+    assert "ranked_count" not in runs_after_first["runs"][0]  # meta-only list omits the heavy fields
+
+    # A DIFFERENT screen_date is a genuine pin miss -- a second, distinct run.
+    second_snap = _trigger_and_wait("2026-06-23")
+    assert second_snap["reused"] is False
+
+    assert first_files[0].read_bytes() == first_bytes  # byte-unchanged
+    runs_after_second = client.get("/research/desk/screen/runs").json()
+    assert len(runs_after_second["runs"]) == 2
+    fresh_manager.join_all(timeout=5)
+
+
+def test_a_terminal_log_write_that_raises_is_never_re_logged_as_a_second_failed_record(
+    manager_env, monkeypatch, tmp_path,
+):
+    """goal-desk-iter-29 audit (B1): the run log is written EXACTLY ONCE per run even when the
+    write itself FAILS. A raising terminal write (a full disk, a read-only log dir) must NOT be
+    caught by ``run_screen_and_record``'s outer except-clause and re-entered as a SECOND, "failed"
+    record -- that record would claim a terminal state the run never had (the snapshot really was
+    recorded) and carry the LEDGER's own I/O error as if it were a screen failure. The run leaves
+    NO record (the module's documented interrupted-run honesty) and the error propagates verbatim,
+    never silently swallowed."""
+    universe_store, bar_store, bar_index, dataset_store, screen_store = manager_env
+    screen_run_store = ScreenRunStore(tmp_path / "screen_runs")
+
+    def fake_compute_screen(_us, _bs, _bi, _ds, _cfg, _sd, *, progress=None, should_abort=None):
+        skipped = []
+        for symbol in SMALL_MEMBERS:
+            skipped.append(
+                {"symbol": symbol, "skipped": True, "reason": "no_bars", "coverage": {},
+                 "tick_evidence": False}
+            )
+            if progress is not None:
+                progress({"symbol": symbol})
+        return {
+            "screen_date": SCREEN_DATE, "as_of": "2026-06-22T23:59:59Z", "universe_snapshot_id": "x",
+            "config_fingerprint": "y", "bar_store_signature": "z", "rows": [], "skipped": skipped,
+        }
+
+    monkeypatch.setattr(desk_screen_compute, "compute_screen", fake_compute_screen)
+
+    calls = {"n": 0}
+
+    def exploding_record_screen_run(*_args, **_kwargs):
+        calls["n"] += 1
+        raise OSError("[Errno 28] No space left on device: 'screen_runs'")
+
+    monkeypatch.setattr(desk_screen_compute, "record_screen_run", exploding_record_screen_run)
+
+    with pytest.raises(OSError, match="No space left on device"):
+        run_screen_and_record(
+            universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store, SCREEN_DATE,
+            screen_run_store=screen_run_store,
+        )
+
+    assert calls["n"] == 1, "a failed terminal write must never be re-entered as a second record"
+    records, errors = screen_run_store.list()
+    assert records == [] and errors == []  # no fabricated entry for a run whose write never landed
+    # The screen snapshot itself was still recorded before the ledger write was attempted -- the
+    # walk's own append-only result is untouched by this failure mode.
+    screen_records, screen_errors = screen_store.list()
+    assert screen_errors == [] and len(screen_records) == 1
diff --git a/apps/backend/tests/test_mcp_server.py b/apps/backend/tests/test_mcp_server.py
index 75253e8..0b2dd71 100644
--- a/apps/backend/tests/test_mcp_server.py
+++ b/apps/backend/tests/test_mcp_server.py
@@ -1084,6 +1084,25 @@ async def test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool(mcp_
     assert "desk_topup_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 17
 
 
+@pytest.mark.anyio
+async def test_get_endpoint_desk_screen_runs_byte_identical_with_no_new_tool(mcp_env):
+    """goal-desk-iter-29 TC-1 (J-18): the NEW ``GET /research/desk/screen/runs`` route is reachable
+    through ``get_endpoint``'s existing ``/research/`` allowlist prefix with ZERO MCP code change —
+    no new tool, no ``_STATIC_PATHS`` entry — and the proxied body is byte-identical to its curl
+    equivalent (here the honest-empty ``{"runs": [], "latest": null, "integrity_errors": []}`` this
+    module-scoped backend's own temp desk dirs genuinely produce -- no test in this module ever
+    triggers a screen compute). The tool count assertion lives in
+    ``test_advertised_tool_set_is_exactly_capability_6``; this is the reachability half."""
+    result = await call_tool("get_endpoint", {"path": "/research/desk/screen/runs"})
+    rest = httpx.get(f"{mcp_env}/research/desk/screen/runs", timeout=5.0)
+    assert rest.status_code == 200
+    assert result.isError is False
+    assert len(result.content) == 1
+    assert result.content[0].text.encode("utf-8") == rest.content, "screen/runs not byte-identical"
+    assert rest.json() == {"runs": [], "latest": None, "integrity_errors": []}
+    assert "desk_screen_runs" not in TOOL_NAMES and len(TOOL_NAMES) == 17
+
+
 @pytest.mark.anyio
 async def test_get_endpoint_refuses_non_allowlisted_paths_without_any_request(monkeypatch):
     """Refusal is decided BEFORE any request: with the backend base pointing at a dead port,
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index e56637b..aa75afe 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -11,6 +11,7 @@ import {
   fetchDeskScreen,
   fetchDeskScreenById,
   fetchDeskScreenCompute,
+  fetchDeskScreenRuns,
   fetchDeskTopupCompute,
   fetchDeskTopupRuns,
   triggerDeskReconcileCompute,
@@ -27,6 +28,9 @@ import type {
   DeskScreenListResult,
   DeskScreenMeta,
   DeskScreenRow,
+  DeskScreenRun,
+  DeskScreenRunMeta,
+  DeskScreenRunsListResult,
   DeskScreenSkip,
   DeskScreenSnapshot,
   DeskTopupComputeSnapshot,
@@ -167,6 +171,17 @@ const LABEL_CELL = "px-2 py-1.5 text-left text-xs text-slate-400 whitespace-nowr
 // (`desk-coverage-badge`'s non-conditional half, `TickEvidenceBadge`, and the `band_round_number`
 // badge already use this exact className) -- reused verbatim, never a new visual effect, for the
 // new class/distance chips.
+// goal-desk-iter-29 (J-18): a FOURTH durable, append-only history section — "Screen Runs" —
+// recording every screen run's own terminal outcome (done/cancelled/failed, reused or not),
+// mirroring "Top-up Runs"/"Index Reconciliation"'s exact section shape. A 7th mount-time GET
+// (`/research/desk/screen/runs`); the screen-compute poll's OWN terminal tick now also refreshes
+// this ledger once (the SAME "on terminal, refresh the durable list" precedent iter-11/iter-14
+// established for their own run logs). Rendered unconditionally as the fourth section, immediately
+// after "Index Reconciliation" — the SAME "independent of screen state" placement precedent its
+// three siblings already establish. No new ranked-table column, no new control: the existing Run
+// Screen button simply becomes cheaper on a duplicate-pin retrigger now that the backend resolves
+// the five pins before paying for the walk (`desk_screen_compute.py`'s own reuse short-circuit) —
+// that behavior change is invisible here beyond the new ledger disclosing it.
 const WRAP_LABEL_CELL = "px-1.5 py-1 text-left text-xs text-slate-400 align-top";
 // The ranked table's OWN cell padding -- `py-1` (4px, vertical) and `px-1.5` (6px, horizontal)
 // instead of the `py-1.5`/`px-2` the shared constants above keep for the history/top-up/
@@ -1207,6 +1222,169 @@ function ReconciliationSection({
   );
 }
 
+// --- Screen run history (goal-desk-iter-29, J-18) — a durable, append-only record of every screen
+// run's outcome — including ones that reused an already-recorded snapshot, were cancelled, or
+// failed — read verbatim from `GET /research/desk/screen/runs` and nothing recomputed. Mirrors the
+// Top-up Runs / Index Reconciliation split exactly: `ScreenRunsTable` renders every recorded run's
+// summary (date + id, terminal state, members attempted-of-total, and what it produced — the ONLY
+// fields the meta-only `runs` list carries), and `LatestScreenRunDetail` renders the full detail
+// (elapsed, ranked/skipped-by-reason counts, verbatim failure detail) for the latest run ONLY — the
+// one entry the backend's `latest` field actually carries them for. Read-only, no click-through, no
+// new control — the existing Run Screen button above simply becomes cheaper on a duplicate-pin
+// retrigger (the backend's own reuse short-circuit); that is not a new control. No new ranked-table
+// column, no change to the ranked table (J-16's measured width contract stays untouched). ----------
+
+// A run's own start→finish duration — a plain difference of two ALREADY-RECORDED timestamps (never
+// `Date.now()`, unlike `formatComputeElapsed` above which clocks a STILL-RUNNING job): a completed
+// run's elapsed time is itself a fixed, deterministic fact once both timestamps are on disk.
+function formatScreenRunElapsed(startedUtc: string, finishedUtc: string): string {
+  const ms = Date.parse(finishedUtc) - Date.parse(startedUtc);
+  if (!Number.isFinite(ms) || ms < 0) return "—";
+  const totalSeconds = Math.floor(ms / 1000);
+  const minutes = Math.floor(totalSeconds / 60);
+  const seconds = totalSeconds % 60;
+  return minutes > 0 ? `${minutes}m ${String(seconds).padStart(2, "0")}s` : `${seconds}s`;
+}
+
+// The one-line, honest statement of what a run produced -- a freshly-recorded snapshot's own id, a
+// reused run's plain "no walk was performed" note, or (cancelled/failed) "nothing recorded" -- never
+// a fabricated id for a run that produced none.
+function screenRunOutcomeText(meta: DeskScreenRunMeta): string {
+  if (meta.state === "done" && meta.reused) {
+    return `reused ${meta.screen_id ?? "—"} — no walk was performed`;
+  }
+  if (meta.state === "done") {
+    return meta.screen_id ?? "nothing recorded";
+  }
+  return "nothing recorded";
+}
+
+function ScreenRunRow({ meta }: { meta: DeskScreenRunMeta }) {
+  return (
+    <tr data-testid="desk-screen-run-row" className="border-b border-slate-800/60 last:border-b-0">
+      <td className={LABEL_CELL}>{meta.screen_date}</td>
+      <td className={LABEL_CELL} data-testid="desk-screen-run-id">
+        {meta.id}
+      </td>
+      <td className={LABEL_CELL} data-testid="desk-screen-run-state">
+        {meta.state}
+      </td>
+      <td className={NUMERIC_CELL} data-testid="desk-screen-run-attempted">
+        {meta.members_attempted} / {meta.members_total}
+      </td>
+      <td className={LABEL_CELL} data-testid="desk-screen-run-outcome">
+        {screenRunOutcomeText(meta)}
+      </td>
+    </tr>
+  );
+}
+
+function ScreenRunsTable({ runs }: { runs: DeskScreenRunMeta[] }) {
+  if (runs.length === 0) {
+    return <EmptyState testid="desk-screen-runs-empty" title="No screen runs recorded yet." />;
+  }
+  return (
+    <div className="overflow-x-auto">
+      <table data-testid="desk-screen-runs-table" className="w-full border-collapse">
+        <thead>
+          <tr className="border-b border-slate-800">
+            <th className={HEADER_CELL_LEFT}>date</th>
+            <th className={HEADER_CELL_LEFT}>run</th>
+            <th className={HEADER_CELL_LEFT}>state</th>
+            <th className={HEADER_CELL}>attempted / total</th>
+            <th className={HEADER_CELL_LEFT}>produced</th>
+          </tr>
+        </thead>
+        <tbody>
+          {runs.map((meta) => (
+            <ScreenRunRow key={meta.id} meta={meta} />
+          ))}
+        </tbody>
+      </table>
+    </div>
+  );
+}
+
+// The latest run's own full detail — state, attempted-of-total, elapsed, what it produced (or the
+// honest reused/nothing-recorded note), the ranked/skipped-by-reason counts on a completed walk,
+// and (state === "failed" only) the raising member's name plus the exception detail rendered
+// VERBATIM and legible (never truncated).
+function LatestScreenRunDetail({ run }: { run: DeskScreenRun }) {
+  const unreached = run.members_total - run.members_attempted;
+  return (
+    <div
+      data-testid="desk-screen-run-latest-detail"
+      className="mt-4 space-y-3 border-t border-slate-800 pt-4"
+    >
+      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
+        Latest run — {run.screen_date} · {run.id}
+      </h3>
+      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
+        <span data-testid="desk-screen-run-latest-state">state: {run.state}</span>
+        <span data-testid="desk-screen-run-latest-attempted">
+          {run.members_attempted} of {run.members_total} members attempted
+        </span>
+        <span data-testid="desk-screen-run-latest-elapsed">
+          {formatScreenRunElapsed(run.started_utc, run.finished_utc)} elapsed
+        </span>
+        <span data-testid="desk-screen-run-latest-outcome">{screenRunOutcomeText(run)}</span>
+        {unreached > 0 && (
+          <span data-testid="desk-screen-run-latest-unreached" className="text-amber-200/70">
+            {unreached} member{unreached === 1 ? "" : "s"} not reached
+          </span>
+        )}
+      </div>
+      {run.state === "done" && (
+        <div data-testid="desk-screen-run-latest-counts" className="text-xs text-slate-400">
+          {run.ranked_count} ranked · {run.skipped_by_reason.no_bars} skipped (no bars) ·{" "}
+          {run.skipped_by_reason.no_basis} skipped (no basis)
+        </div>
+      )}
+      {run.state === "failed" && (
+        <div data-testid="desk-screen-run-latest-failed" className="text-xs text-slate-400">
+          <span className="font-mono text-slate-300">
+            {run.failed_member ?? "(member not recorded)"}
+          </span>{" "}
+          —{" "}
+          <span data-testid="desk-screen-run-latest-failed-detail">
+            {run.error ?? "(no detail recorded)"}
+          </span>
+        </div>
+      )}
+    </div>
+  );
+}
+
+// The section's own Loading/Unavailable/Populated states — mirrors `TopupRunsSection`'s/
+// `ReconciliationSection`'s identical three-state shape, fed by its own mount-time GET.
+function ScreenRunsSection({
+  result,
+}: {
+  result: { ok: boolean; data: DeskScreenRunsListResult | null; error?: string } | null;
+}) {
+  if (result === null) {
+    return <LoadingPanel testid="desk-screen-runs-loading" />;
+  }
+  if (!result.ok || result.data === null) {
+    return (
+      <UnavailablePanel
+        testid="desk-screen-runs-unavailable"
+        message={result.error ?? "The screen run history could not be loaded."}
+      />
+    );
+  }
+  return (
+    <div>
+      <ScreenRunsTable runs={result.data.runs} />
+      {result.data.latest !== null && <LatestScreenRunDetail run={result.data.latest} />}
+      <IntegrityErrorsNote
+        errors={result.data.integrity_errors}
+        testid="desk-screen-runs-integrity-errors"
+      />
+    </div>
+  );
+}
+
 // --- Provenance line — snapshot id + recorded-at time, universe snapshot id + date, as_of,
 // config_fingerprint, and the pinned bar-store signature. -------------------------------------
 //
@@ -1730,6 +1908,17 @@ export default function DeskPage() {
     error?: string;
   } | null>(null);
 
+  // goal-desk-iter-29 (J-18): the durable, append-only SCREEN-run log — independent of
+  // `screenResult`/`screenCompute` above (the latter is the CURRENT/last in-flight job's
+  // process-scoped progress; this is every COMPLETED run's persisted terminal outcome, including
+  // reused/cancelled/failed ones) — mirrors the `topupRunsResult`/`reconcileRunsResult` hooks
+  // exactly.
+  const [screenRunsResult, setScreenRunsResult] = useState<{
+    ok: boolean;
+    data: DeskScreenRunsListResult | null;
+    error?: string;
+  } | null>(null);
+
   // era-desk-iter-6 (J-05): the screen-history click-through. `viewingSnapshot` is `null` while
   // showing the top-level `latest` snapshot already held in `screenResult` (no refetch needed to
   // return to it — TC-2); once a history row is selected, it holds THAT row's own full snapshot,
@@ -1740,11 +1929,12 @@ export default function DeskPage() {
   const [viewingSnapshot, setViewingSnapshot] = useState<DeskScreenSnapshot | null>(null);
   const [historyFetchError, setHistoryFetchError] = useState<string | null>(null);
 
-  // Mount: six GETs, zero POSTs (TC-19/TC-8, extended era-desk-iter-14) — the screen list/latest,
-  // ALL THREE compute managers' current/last snapshot (seeds a page load mid-job or post-terminal
-  // without a spurious extra click — the /structure edge-report mount-seeding precedent), the
-  // top-up run log's list + latest full record (era-desk-iter-11, J-09), and (era-desk-iter-14,
-  // J-10) the reconciliation run log's list + latest full record.
+  // Mount: seven GETs, zero POSTs (TC-19/TC-8, extended era-desk-iter-14/goal-desk-iter-29) — the
+  // screen list/latest, ALL THREE compute managers' current/last snapshot (seeds a page load
+  // mid-job or post-terminal without a spurious extra click — the /structure edge-report
+  // mount-seeding precedent), the top-up run log's list + latest full record (era-desk-iter-11,
+  // J-09), the reconciliation run log's list + latest full record (era-desk-iter-14, J-10), and
+  // (goal-desk-iter-29, J-18) the screen run log's list + latest full record.
   useEffect(() => {
     let alive = true;
     fetchDeskScreen().then((result) => {
@@ -1753,6 +1943,9 @@ export default function DeskPage() {
     fetchDeskScreenCompute().then((result) => {
       if (alive && result.ok) setScreenCompute(result.data);
     });
+    fetchDeskScreenRuns().then((result) => {
+      if (alive) setScreenRunsResult(result);
+    });
     fetchDeskTopupCompute().then((result) => {
       if (alive && result.ok) setTopupCompute(result.data);
     });
@@ -1774,6 +1967,10 @@ export default function DeskPage() {
   // reusing the PATTERN, not the endpoint). The instant a tick observes a terminal state, the
   // screen list is re-fetched exactly once so the briefing swaps in — zero new report-rendering
   // logic, the same "read verbatim, recompute nothing" discipline every section here follows.
+  // goal-desk-iter-29 (J-18): the SAME terminal tick also re-fetches the screen run log exactly
+  // once, so the just-finished run's own record appears in Screen Runs without a manual reload —
+  // the SAME "on terminal, refresh the durable list" precedent `topupRunsResult`/
+  // `reconcileRunsResult`'s own polls below already establish.
   useEffect(() => {
     if (screenCompute?.state !== "running") return;
     const handle = setInterval(async () => {
@@ -1789,6 +1986,10 @@ export default function DeskPage() {
         setScreenResult((previous) =>
           refreshed.ok || previous === null || !previous.ok ? refreshed : previous,
         );
+        const refreshedRuns = await fetchDeskScreenRuns();
+        setScreenRunsResult((previous) =>
+          refreshedRuns.ok || previous === null || !previous.ok ? refreshedRuns : previous,
+        );
       }
     }, 700);
     return () => clearInterval(handle);
@@ -2048,6 +2249,16 @@ export default function DeskPage() {
             <ReconciliationSection result={reconcileRunsResult} />
           </Panel>
         </section>
+
+        {/* goal-desk-iter-29 (J-18): a fourth ledger section, the SAME "always rendered,
+            independent of screen state" placement precedent as its two siblings above — a screen
+            run's durable history (including reused/cancelled/failed runs) exists, or honestly
+            doesn't, regardless of whether the ranked briefing above is currently populated. */}
+        <section aria-label="Screen Runs" className="mt-6">
+          <Panel title="Screen Runs">
+            <ScreenRunsSection result={screenRunsResult} />
+          </Panel>
+        </section>
       </main>
     </div>
   );
diff --git a/apps/frontend/lib/api.ts b/apps/frontend/lib/api.ts
index 5858863..c70b4cf 100644
--- a/apps/frontend/lib/api.ts
+++ b/apps/frontend/lib/api.ts
@@ -10,6 +10,7 @@ import type {
   DeskReconcileRunsListResult,
   DeskScreenComputeSnapshot,
   DeskScreenListResult,
+  DeskScreenRunsListResult,
   DeskScreenSnapshot,
   DeskTopupComputeSnapshot,
   DeskTopupRunsListResult,
@@ -1266,3 +1267,32 @@ export async function fetchDeskReconcileRuns(): Promise<{
     return { ok: false, data: null, error: "Backend unreachable — is the API running?" };
   }
 }
+
+// goal-desk-iter-29 (J-18): GET /research/desk/screen/runs — the durable, append-only SCREEN run
+// log's meta-only list + the latest full record, served VERBATIM. Mirrors `fetchDeskTopupRuns`'s/
+// `fetchDeskReconcileRuns`'s exact `{ok, data, error}` shape byte-for-byte. An honest-empty
+// (`{runs: [], latest: null, integrity_errors: []}`) result is a valid `ok:true` outcome — the
+// caller renders it as "No screen runs recorded yet.", never a failure; `data: null` is reserved
+// for a genuine non-200 / unreachable backend.
+export async function fetchDeskScreenRuns(): Promise<{
+  ok: boolean;
+  data: DeskScreenRunsListResult | null;
+  error?: string;
+}> {
+  try {
+    const res = await fetch(`${API_BASE}/research/desk/screen/runs`);
+    if (res.ok) {
+      return { ok: true, data: (await res.json()) as DeskScreenRunsListResult };
+    }
+    let error = "The screen run history could not be loaded.";
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
index c237b61..e534556 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -1093,3 +1093,51 @@ export interface DeskReconcileComputeSnapshot {
   error: string | null;
   progress: DeskReconcileComputeProgress;
 }
+
+// goal-desk-iter-29 (J-18) -- the durable, append-only SCREEN run log, served by
+// `GET /research/desk/screen/runs`. Distinct from `DeskScreenComputeSnapshot`: the compute
+// snapshot is the CURRENT/last in-flight job's process-scoped progress (lost on restart, replaced
+// the instant a newer run starts); this is every COMPLETED run's terminal outcome, persisted to
+// disk once and never rewritten. Mirrors `DeskTopupRunMeta`/`DeskReconcileRunMeta`'s identical
+// meta-only-list/full-latest split: the bulk `runs` list omits `ranked_count`/`skipped_by_reason`/
+// `error`/`failed_member` -- only `latest` (below) ever carries them.
+export interface DeskScreenRunMeta {
+  id: string;
+  screen_date: string;
+  universe_snapshot_id: string | null;
+  config_fingerprint: string;
+  bar_store_signature: string | null;
+  started_utc: string;
+  finished_utc: string;
+  state: "done" | "cancelled" | "failed";
+  reused: boolean;
+  members_total: number;
+  members_attempted: number;
+  screen_id: string | null;
+}
+
+export interface DeskScreenSkippedByReason {
+  no_bars: number;
+  no_basis: number;
+}
+
+// The full persisted record -- `DeskScreenRunMeta` plus the ranked/skipped-by-reason counts and
+// (failed runs only) the verbatim error + the member the walk was on when it raised. Only `latest`
+// (below) ever carries this full shape; the bulk `runs` list is meta-only.
+export interface DeskScreenRun extends DeskScreenRunMeta {
+  ranked_count: number;
+  skipped_by_reason: DeskScreenSkippedByReason;
+  error: string | null;
+  failed_member: string | null;
+}
+
+// `GET /research/desk/screen/runs` -- honest-empty-or-populated, HTTP 200 always, never 404.
+// `latest === null` iff no screen run has EVER reached a terminal state -- the page's ONE
+// discriminator for the "No screen runs recorded yet." empty state. `integrity_errors` mirrors
+// `DeskTopupRunsListResult`/`DeskReconcileRunsListResult`'s identical field -- surfaced from the
+// store's own `.list()` return, never silently dropped.
+export interface DeskScreenRunsListResult {
+  runs: DeskScreenRunMeta[];
+  latest: DeskScreenRun | null;
+  integrity_errors: { file: string; error: string }[];
+}
diff --git a/apps/backend/app/research/desk_screen_log.py b/apps/backend/app/research/desk_screen_log.py
new file mode 100644
index 0000000..50c6178
--- /dev/null
+++ b/apps/backend/app/research/desk_screen_log.py
@@ -0,0 +1,267 @@
+"""The screen run log (Era B "The Desk", goal-desk-iter-29, J-18) -- an append-only, checksummed
+record of what every desk SCREEN compute run attempted, surviving past the next run superseding
+``DeskScreenComputeManager``'s in-flight/last-terminal snapshot (``desk_screen_compute.py``'s job
+state is explicitly process-scoped and honestly lost on restart -- this module is the durable
+counterpart the goal.md J-18 journey adds beside it, mirroring the J-09 (``desk_topup_log.py``) /
+J-10 (``desk_index_reconcile.py``) run-log discipline verbatim).
+
+THIS module computes NOTHING about screens, bands, or ranking itself -- it is a pure PERSISTENCE
+lens over what ``run_screen_and_record`` (``desk_screen_compute.py``) already resolves/computes. A
+run record is written EXACTLY ONCE, at the run's terminal state, by the single shared writer
+(``record_screen_run`` below) -- called from inside ``run_screen_and_record`` itself (the ONE shared
+entry point both ``DeskScreenComputeManager``'s resolve path and the CLI's ``main()`` already call),
+and nowhere else.
+
+**Records the RUN only -- zero diff to what a screen snapshot itself records.** ``desk_screen.py``'s
+``ScreenStore`` stays the sole owner of screen snapshots/rows/skips/the five-pin key; this module
+never reads or writes a screen snapshot file, never re-derives a pin, and never duplicates
+``rows``/``skipped`` content -- only their COUNTS (``ranked_count``/``skipped_by_reason``) are
+recorded here, exactly the same "attempt-level summary, not content" split ``desk_topup_log.py``
+draws between a run's outcomes and a top-up's per-pair detail.
+
+**Mirrors ``desk_topup_log.TopupRunStore``/``desk_index_reconcile.ReconcileRunStore``'s discipline
+byte-for-byte** -- a checksum-verified load on every read (``ScreenRunIntegrityError`` on any
+mismatch, never silence, never a fabricated record), ``record()`` the only mutation, no
+update/delete function anywhere (immutability is structural, not policed), and NO content-based
+deduplication: every terminal run is its own genuinely distinct event -- even an all-``reused`` run
+over an unchanged store is a real, separate attempt with its own ``started_utc``/``finished_utc`` --
+so ``record()`` always writes a brand-new file.
+
+**Interrupted-run honesty (a DoD clause, structural by construction).** A run whose PROCESS ends
+before this module's writer is ever called (a crash, ``kill -9``, a power loss) leaves NO record --
+there is no "pending" or "partial" file ever written, because ``record()`` is the ONLY write path in
+this module and it is called exactly once, at the very end of a run's lifecycle, never earlier and
+never speculatively.
+
+**Storage dir -- no new ``Config`` field.** ``resolve_desk_screen_log_dir`` mirrors
+``resolve_desk_topup_log_dir``/``resolve_desk_screen_dir`` exactly: a bare
+``TAPEOLOGY_DESK_SCREEN_LOG_DIR`` env-var override, else a directory co-located as a SIBLING of the
+caller's own already-resolved universe directory -- an operational storage-location knob, never a
+value that shapes a served result, so ``config_fingerprint()`` stays untouched (the Constraints'
+own explicit sanction for "worker counts, timeouts, store dirs")."""
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
+    "ScreenRunIntegrityError",
+    "ScreenRunStore",
+    "record_screen_run",
+    "resolve_desk_screen_log_dir",
+]
+
+# The store's own env-var override (the ``TAPEOLOGY_DESK_TOPUP_LOG_DIR``/
+# ``TAPEOLOGY_DESK_INDEX_RECONCILE_DIR`` pattern) -- see ``resolve_desk_screen_log_dir``.
+_SCREEN_LOG_DIR_ENV = "TAPEOLOGY_DESK_SCREEN_LOG_DIR"
+
+# The three terminal states a run record may carry -- never "running" (a record is written once, at
+# terminal state only; see the module docstring's "interrupted-run honesty" section).
+_TERMINAL_STATES = ("done", "cancelled", "failed")
+
+
+class ScreenRunIntegrityError(Exception):
+    """An on-disk run-record file failed its checksum verification on load -- corrupted or
+    tampered, surfaced explicitly (never silence, never a fabricated record)."""
+
+
+def resolve_desk_screen_log_dir(desk_universe_dir_resolved: str) -> str:
+    """The screen run log's directory: the ``TAPEOLOGY_DESK_SCREEN_LOG_DIR`` env var if set, else a
+    directory co-located as a SIBLING of the CALLER's own already-resolved universe directory (the
+    ``resolve_desk_topup_log_dir`` pattern verbatim -- takes a plain string, never imports
+    ``config.py``'s singleton, so the caller resolves its own universe directory first exactly as
+    ``desk_routes.py``/``desk_screen_compute.py`` already do). Deliberately NOT a
+    ``desk_screen_log_dir`` ``Config`` field (see the module docstring) -- this keeps
+    ``config_fingerprint()`` untouched this iteration."""
+    override = os.environ.get(_SCREEN_LOG_DIR_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "screen_runs")
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding every checksum in this module hashes (stable across
+    processes: sorted keys, no whitespace) -- the SAME encoding ``desk_topup_log.py``/
+    ``desk_screen.py`` hash."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+class ScreenRunStore:
+    """File-based store rooted at the config-owned screen-run-log directory -- the ONE
+    reader/writer. Mirrors ``desk_topup_log.TopupRunStore``/``desk_index_reconcile.ReconcileRunStore``
+    load/checksum discipline exactly; like them, ``record`` performs no content-keyed dedup -- every
+    call always persists a genuinely new file."""
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
+        ``ScreenRunIntegrityError`` for any parse/shape/checksum failure -- explicit, never
+        silent."""
+        try:
+            data = json.loads(path.read_text())
+        except (OSError, ValueError) as exc:
+            raise ScreenRunIntegrityError(
+                f"screen run record file '{path.name}' is not parseable ({exc}) -- corrupted or "
+                f"tampered"
+            ) from exc
+        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
+            raise ScreenRunIntegrityError(
+                f"screen run record file '{path.name}' does not carry the expected record shape "
+                f"-- corrupted or tampered"
+            )
+        record = data["record"]
+        if _sha256(_canonical(record)) != data["file_checksum"]:
+            raise ScreenRunIntegrityError(
+                f"screen run record file '{path.name}' failed its integrity check (checksum "
+                f"mismatch) -- the file was corrupted or tampered with"
+            )
+        meta = record.get("meta")
+        if not isinstance(meta, dict):
+            raise ScreenRunIntegrityError(
+                f"screen run record file '{path.name}' does not carry the expected record shape "
+                f"-- corrupted or tampered"
+            )
+        return meta
+
+    def list(self) -> tuple[list[dict], list[dict]]:
+        """Every registered run's full content (each file verified), oldest-started first, plus an
+        EXPLICIT error row per file that failed verification -- a corrupt file is surfaced, never
+        silently hidden and never served as data. A store whose directory was never created (no run
+        has ever been recorded) returns ``([], [])`` -- the honest-empty case (DoD: "a run whose
+        process ends before the writer's terminal call leaves NO record"). A fresh dict copy of
+        every returned record's own ``skipped_by_reason`` (the ``desk_universe.UniverseStore.list``
+        per-row-copy discipline), so a caller mutating a returned record can never poison a later
+        read."""
+        if not self._root.exists():
+            return [], []
+        records: list[dict] = []
+        errors: list[dict] = []
+        for path in sorted(self._root.glob("*.json")):
+            try:
+                meta = self._load(path)
+                records.append({**meta, "skipped_by_reason": dict(meta["skipped_by_reason"])})
+            except ScreenRunIntegrityError as exc:
+                errors.append({"file": path.name, "error": str(exc)})
+        records.sort(key=lambda meta: (meta.get("started_utc", ""), meta.get("id", "")))
+        return records, errors
+
+    def record(
+        self,
+        *,
+        screen_date: str,
+        universe_snapshot_id: str | None,
+        config_fingerprint: str,
+        bar_store_signature: str | None,
+        started_utc: str,
+        finished_utc: str,
+        state: str,
+        reused: bool,
+        members_total: int,
+        members_attempted: int,
+        ranked_count: int,
+        skipped_by_reason: dict,
+        screen_id: str | None,
+        error: str | None,
+        failed_member: str | None,
+    ) -> dict:
+        """Persist ONE new screen-run record (record + register in a single explicit action) --
+        ALWAYS a genuinely new file: no content-keyed dedup exists in this store (see the module
+        docstring), so a second call with identical field values still appends a second, distinct
+        record."""
+        if state not in _TERMINAL_STATES:
+            raise ValueError(
+                f"invalid terminal state {state!r} -- must be one of {_TERMINAL_STATES}"
+            )
+        date = started_utc[:10]  # started_utc is always an ISO-8601 UTC string -- a YYYY-MM-DD prefix
+        run_id = f"screenrun-{date}-{uuid.uuid4().hex[:12]}"
+        # A path collision is astronomically unlikely (a random 12-hex-char suffix), but this store
+        # never silently overwrites an existing file regardless of cause -- mirrors
+        # TopupRunStore.record's/ReconcileRunStore.record's identical defensive re-roll instead of a
+        # blind write.
+        while self._path(run_id).exists():
+            run_id = f"screenrun-{date}-{uuid.uuid4().hex[:12]}"
+        meta = {
+            "id": run_id,
+            "screen_date": screen_date,
+            "universe_snapshot_id": universe_snapshot_id,
+            "config_fingerprint": config_fingerprint,
+            "bar_store_signature": bar_store_signature,
+            "started_utc": started_utc,
+            "finished_utc": finished_utc,
+            "state": state,
+            "reused": reused,
+            "members_total": members_total,
+            "members_attempted": members_attempted,
+            "ranked_count": ranked_count,
+            "skipped_by_reason": dict(skipped_by_reason),
+            "screen_id": screen_id,
+            "error": error,
+            "failed_member": failed_member,
+        }
+        record = {"meta": meta}
+        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
+        self._root.mkdir(parents=True, exist_ok=True)
+        self._path(run_id).write_text(json.dumps(payload))
+        return dict(meta)
+
+
+def record_screen_run(
+    store: ScreenRunStore,
+    *,
+    screen_date: str,
+    universe_snapshot_id: str | None,
+    config_fingerprint: str,
+    bar_store_signature: str | None,
+    started_utc: str,
+    finished_utc: str,
+    state: str,
+    reused: bool,
+    members_total: int,
+    members_attempted: int,
+    ranked_count: int,
+    skipped_by_reason: dict,
+    screen_id: str | None,
+    error: str | None,
+    failed_member: str | None,
+) -> dict:
+    """THE single shared writer (goal.md J-18 step 3) -- called exactly once, at a run's terminal
+    state, from inside ``run_screen_and_record`` (``desk_screen_compute.py``) -- the ONE shared
+    entry point both ``DeskScreenComputeManager``'s resolve path and the CLI's ``main()`` already
+    call -- and nothing else. A thin, explicit free function over ``ScreenRunStore.record`` (rather
+    than the call site invoking the method directly) so a future reader grepping for
+    ``record_screen_run`` finds the one call site -- the ``desk_topup_log.record_topup_run``/
+    ``desk_index_reconcile.record_reconcile_run`` precedent."""
+    return store.record(
+        screen_date=screen_date,
+        universe_snapshot_id=universe_snapshot_id,
+        config_fingerprint=config_fingerprint,
+        bar_store_signature=bar_store_signature,
+        started_utc=started_utc,
+        finished_utc=finished_utc,
+        state=state,
+        reused=reused,
+        members_total=members_total,
+        members_attempted=members_attempted,
+        ranked_count=ranked_count,
+        skipped_by_reason=skipped_by_reason,
+        screen_id=screen_id,
+        error=error,
+        failed_member=failed_member,
+    )
diff --git a/apps/backend/tests/test_desk_screen_log.py b/apps/backend/tests/test_desk_screen_log.py
new file mode 100644
index 0000000..296e3f0
--- /dev/null
+++ b/apps/backend/tests/test_desk_screen_log.py
@@ -0,0 +1,287 @@
+"""``desk_screen_log.py`` (Era B "The Desk", goal-desk-iter-29, J-18) — the screen-run log's store
+discipline: checksum verification, structural append-only-ness (no update/delete path, no content
+dedup — every call to ``record`` is a genuinely new file), the interrupted-run-leaves-no-record
+guarantee, and the directory-resolution seam (mirrors ``test_desk_topup_log.py``'s own store-level
+test shape).
+
+The shared-writer contract itself (proving ``record_screen_run`` is called from inside
+``run_screen_and_record``, the ONE entry point both ``DeskScreenComputeManager`` and the CLI call)
+is exercised end to end in ``test_desk_screen_compute.py`` — this file covers the store module in
+isolation."""
+
+from __future__ import annotations
+
+import json
+
+import pytest
+
+from app.research.desk_screen_log import (
+    ScreenRunIntegrityError,
+    ScreenRunStore,
+    record_screen_run,
+    resolve_desk_screen_log_dir,
+)
+
+SAMPLE_SKIPPED_BY_REASON = {"no_bars": 2, "no_basis": 1}
+
+
+def _record_sample(
+    store: ScreenRunStore,
+    *,
+    state: str = "done",
+    reused: bool = False,
+    started_utc: str = "2026-07-31T09:00:00.000000Z",
+    finished_utc: str = "2026-07-31T09:05:00.000000Z",
+    screen_date: str = "2026-07-31",
+    universe_snapshot_id: str | None = "universe-2026-07-25-49b33fa31680",
+    config_fingerprint: str = "08e471b10130e1e2",
+    bar_store_signature: str | None = "abcdef0123456789",
+    members_total: int = 3,
+    members_attempted: int = 3,
+    ranked_count: int = 2,
+    skipped_by_reason: dict | None = None,
+    screen_id: str | None = "screen-2026-07-31-deadbeef0000",
+    error: str | None = None,
+    failed_member: str | None = None,
+) -> dict:
+    return record_screen_run(
+        store,
+        screen_date=screen_date,
+        universe_snapshot_id=universe_snapshot_id,
+        config_fingerprint=config_fingerprint,
+        bar_store_signature=bar_store_signature,
+        started_utc=started_utc,
+        finished_utc=finished_utc,
+        state=state,
+        reused=reused,
+        members_total=members_total,
+        members_attempted=members_attempted,
+        ranked_count=ranked_count,
+        skipped_by_reason=SAMPLE_SKIPPED_BY_REASON if skipped_by_reason is None else skipped_by_reason,
+        screen_id=screen_id,
+        error=error,
+        failed_member=failed_member,
+    )
+
+
+# --- record: shape + provenance ------------------------------------------------------------------
+
+
+def test_record_stores_every_field_verbatim(tmp_path):
+    store = ScreenRunStore(tmp_path / "screen_runs")
+    meta = _record_sample(store)
+
+    assert meta["screen_date"] == "2026-07-31"
+    assert meta["universe_snapshot_id"] == "universe-2026-07-25-49b33fa31680"
+    assert meta["config_fingerprint"] == "08e471b10130e1e2"
+    assert meta["bar_store_signature"] == "abcdef0123456789"
+    assert meta["started_utc"] == "2026-07-31T09:00:00.000000Z"
+    assert meta["finished_utc"] == "2026-07-31T09:05:00.000000Z"
+    assert meta["state"] == "done"
+    assert meta["reused"] is False
+    assert meta["members_total"] == 3
+    assert meta["members_attempted"] == 3
+    assert meta["ranked_count"] == 2
+    assert meta["skipped_by_reason"] == SAMPLE_SKIPPED_BY_REASON
+    assert meta["screen_id"] == "screen-2026-07-31-deadbeef0000"
+    assert meta["error"] is None
+    assert meta["failed_member"] is None
+    assert meta["id"].startswith("screenrun-2026-07-31-")
+    # The record landed as ONE file in the configured directory.
+    assert len(list((tmp_path / "screen_runs").glob("*.json"))) == 1
+
+
+def test_record_rejects_a_non_terminal_state(tmp_path):
+    store = ScreenRunStore(tmp_path / "screen_runs")
+    with pytest.raises(ValueError):
+        _record_sample(store, state="running")
+
+
+def test_a_failed_run_carries_its_error_and_failed_member_verbatim(tmp_path):
+    store = ScreenRunStore(tmp_path / "screen_runs")
+    meta = _record_sample(
+        store, state="failed", screen_id=None, error="synthetic raise on member CCC",
+        failed_member="CCC", ranked_count=0, skipped_by_reason={"no_bars": 0, "no_basis": 0},
+    )
+    assert meta["state"] == "failed"
+    assert meta["error"] == "synthetic raise on member CCC"
+    assert meta["failed_member"] == "CCC"
+    assert meta["screen_id"] is None
+
+
+def test_a_reused_run_never_pays_for_the_walk_and_records_zero_members_attempted(tmp_path):
+    store = ScreenRunStore(tmp_path / "screen_runs")
+    meta = _record_sample(
+        store, reused=True, members_attempted=0, ranked_count=0,
+        skipped_by_reason={"no_bars": 0, "no_basis": 0},
+    )
+    assert meta["reused"] is True
+    assert meta["members_attempted"] == 0
+
+
+# --- list: verbatim read, oldest-started first -----------------------------------------------------
+
+
+def test_list_serves_the_stored_record_verbatim(tmp_path):
+    store = ScreenRunStore(tmp_path / "screen_runs")
+    recorded = _record_sample(store)
+
+    records, errors = store.list()
+    assert errors == []
+    assert len(records) == 1
+    assert records[0] == recorded
+
+
+def test_store_survives_a_reload_from_disk(tmp_path):
+    root = tmp_path / "screen_runs"
+    recorded = _record_sample(ScreenRunStore(root))
+
+    reloaded = ScreenRunStore(root)
+    records, errors = reloaded.list()
+    assert errors == []
+    assert records == [recorded]
+
+
+def test_list_on_a_directory_that_was_never_created_is_honestly_empty(tmp_path):
+    """TC-1 / TC-7 at the store level: a store that is never told to ``record`` (the writer's
+    terminal call literally never happening) holds zero files and lists zero records — never a
+    fabricated or partial entry."""
+    store = ScreenRunStore(tmp_path / "screen_runs" / "never-created")
+    records, errors = store.list()
+    assert records == []
+    assert errors == []
+    assert not (tmp_path / "screen_runs" / "never-created").exists()
+
+
+# --- append-only: every call to record is a genuinely NEW file, never a dedup/update ---------------
+
+
+def test_two_calls_with_identical_field_values_still_append_two_distinct_records(tmp_path):
+    """UNLIKE UniverseStore/ScreenStore, this store performs no content-keyed dedup — two
+    back-to-back screen runs over an unchanged store (e.g. both entirely "reused") are still TWO
+    real, distinct attempts and must both be recorded."""
+    store = ScreenRunStore(tmp_path / "screen_runs")
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
+    """TC-8: the first record's file stays byte-unchanged (same bytes) after a second run
+    completes, and ``list()`` carries both."""
+    root = tmp_path / "screen_runs"
+    store = ScreenRunStore(root)
+    first = _record_sample(
+        store, started_utc="2026-07-31T09:00:00Z", finished_utc="2026-07-31T09:05:00Z",
+    )
+    first_path = root / f"{first['id']}.json"
+    first_bytes_before = first_path.read_bytes()
+
+    second = _record_sample(
+        store, started_utc="2026-07-31T10:00:00Z", finished_utc="2026-07-31T10:05:00Z",
+        screen_id="screen-2026-07-31-cafef00d0000",
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
+def test_screen_run_store_has_no_update_or_delete_method():
+    """Structural immutability: the only mutation on this class is ``record`` — mirrors
+    ``TopupRunStore``/``ReconcileRunStore``'s own guard-by-absence discipline."""
+    public_methods = {name for name in dir(ScreenRunStore) if not name.startswith("_")}
+    assert public_methods == {"root", "list", "record"}
+
+
+# --- interrupted-run honesty: a run whose terminal write never happens leaves zero record ---------
+
+
+def test_a_run_that_never_reaches_the_writer_call_leaves_the_store_untouched(tmp_path):
+    """Simulates a process that ends before the writer's terminal call: a store is constructed
+    exactly as a real caller would, but ``record``/``record_screen_run`` is deliberately never
+    invoked (standing in for a crash between the walk finishing and the writer call). The store
+    gains zero new file — never a fabricated or partial entry (DoD, TC-7)."""
+    store = ScreenRunStore(tmp_path / "screen_runs")
+    # ... the walk would happen here in a real run; the process ends before this line runs:
+    # record_screen_run(store, ...)
+    records, errors = store.list()
+    assert records == []
+    assert errors == []
+    assert not (tmp_path / "screen_runs").exists()
+
+
+# --- integrity: a corrupted file is explicit, never silent ----------------------------------------
+
+
+def test_corrupted_run_record_file_surfaces_explicitly_in_list_errors(tmp_path):
+    root = tmp_path / "screen_runs"
+    store = ScreenRunStore(root)
+    _record_sample(store)
+    path = next(root.glob("*.json"))
+    data = json.loads(path.read_text())
+    data["record"]["meta"]["members_total"] = 999  # tamper -- file_checksum now disagrees
+    path.write_text(json.dumps(data))
+
+    records, errors = store.list()
+    assert records == []
+    assert len(errors) == 1
+    assert path.name == errors[0]["file"]
+    assert "integrity" in errors[0]["error"]
+
+
+def test_load_raises_screen_run_integrity_error_for_unparseable_json(tmp_path):
+    root = tmp_path / "screen_runs"
+    root.mkdir(parents=True)
+    (root / "screenrun-2026-01-01-deadbeef0000.json").write_text("{not json")
+
+    store = ScreenRunStore(root)
+    records, errors = store.list()
+    assert records == []
+    assert len(errors) == 1
+
+
+def test_corrupted_file_does_not_block_other_valid_records_from_listing(tmp_path):
+    root = tmp_path / "screen_runs"
+    store = ScreenRunStore(root)
+    good = _record_sample(store)
+    bad_path = root / "screenrun-2026-01-01-deadbeef0000.json"
+    bad_path.write_text("{not json")
+
+    records, errors = store.list()
+    assert len(records) == 1 and records[0]["id"] == good["id"]
+    assert len(errors) == 1
+
+
+def test_load_raises_screen_run_integrity_error_directly_for_a_missing_meta_shape(tmp_path):
+    """A file that parses as JSON but does not carry the expected ``{"file_checksum", "record":
+    {"meta": ...}}`` shape is also refused explicitly, never silently coerced."""
+    root = tmp_path / "screen_runs"
+    root.mkdir(parents=True)
+    path = root / "screenrun-2026-01-01-deadbeef0000.json"
+    path.write_text(json.dumps({"unexpected": "shape"}))
+
+    store = ScreenRunStore(root)
+    with pytest.raises(ScreenRunIntegrityError):
+        store._load(path)  # noqa: SLF001 -- direct unit test of the private loader's own raise
+
+
+# --- resolve_desk_screen_log_dir -- zero new Config field -------------------------------------------
+
+
+def test_resolve_desk_screen_log_dir_defaults_to_a_sibling_of_the_universe_dir(monkeypatch):
+    monkeypatch.delenv("TAPEOLOGY_DESK_SCREEN_LOG_DIR", raising=False)
+    resolved = resolve_desk_screen_log_dir("/some/root/.data/universe")
+    assert resolved == "/some/root/.data/screen_runs"
+
+
+def test_resolve_desk_screen_log_dir_env_override(monkeypatch):
+    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_LOG_DIR", "/tmp/custom-screen-log-dir")
+    assert resolve_desk_screen_log_dir("/some/root/.data/universe") == "/tmp/custom-screen-log-dir"
```
