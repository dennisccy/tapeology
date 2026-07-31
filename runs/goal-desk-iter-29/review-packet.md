# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 8. Shown in full: 8.

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
index c55e0ec..b263c9b 100644
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
@@ -93,31 +141,136 @@ def run_screen_and_record(
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
+        if screen_run_store is None:
+            return
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
@@ -147,13 +300,21 @@ class DeskScreenComputeManager:
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
@@ -199,6 +360,7 @@ class DeskScreenComputeManager:
                 record, reused = run_screen_and_record(
                     universe_store, bar_store, bar_index, dataset_store, config, screen_store,
                     screen_date, progress=_publish, should_abort=cancel_event.is_set,
+                    screen_run_store=screen_run_store,
                 )
             except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                 self._resolve(job_id, "failed", error=str(exc))
@@ -290,10 +452,15 @@ def main() -> int:
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
index 889e8f9..2d93222 100644
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
@@ -729,3 +730,266 @@ def test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot(
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
diff --git a/docs/goal.md b/docs/goal.md
index 10c797f..5f51789 100644
--- a/docs/goal.md
+++ b/docs/goal.md
@@ -1401,6 +1401,156 @@ order: J-01 → J-02 → J-03 → J-04 → J-05 → J-06, with J-07 guarding con
     as `failed` — so without the `unchanged` outcome a weekend run would print a wall of false
     failures.)*
 
+- **J-18: Every screen run leaves an append-only record of what it attempted — and a re-run under identical pins says so before it walks**
+  - Steps:
+    1. Resolve the run's five pins BEFORE the walk, using ONLY accessors that already exist and are
+       already each pin's single owner: `desk_screen.screen_as_of` (`desk_screen.py:233`), the
+       universe store's own latest record id (`UniverseStore.list()`'s `records[-1]["id"]` — the
+       identical read `compute_screen` makes at `:441`), `Config.config_fingerprint()`, and
+       `desk_screen.compute_bar_store_signature` (`:255`, which exists precisely "so a caller (or a
+       test) can resolve the 5-pin key's `bar_store_signature` component WITHOUT running the full
+       per-member walk", over `desk_coverage.get_desk_coverage`'s index-only read, T-4). **No new
+       derivation of any pin, no new value**: the signature keeps its single owner
+       (`_bar_store_signature` over `desk_coverage`), and `compute_screen` keeps resolving its own
+       pins exactly as it does today — the same functions over the same immutable store, so the two
+       resolutions cannot disagree.
+    2. Answer an already-recorded pin set without paying for the walk: inside the ONE shared entry
+       point both callers already use (`run_screen_and_record`, `desk_screen_compute.py:73`), a
+       `ScreenStore.find_by_key` hit on those five pins (`desk_screen.py:602` — the SAME lookup that
+       path already performs at `desk_screen_compute.py:114`, one line AFTER the walk it could have
+       avoided) returns the existing snapshot with `reused=True` immediately: zero
+       `compute_tradability` calls and no `BarStore` read beyond the index-only coverage read the pin
+       resolution already made. Nothing else moves — the manager's
+       `GET /research/desk/screen/compute` poll shape stays byte-unchanged (`state`/`reused`/
+       `screen_id` keep their exact recorded meanings; `progress.members_done` simply stays 0),
+       `ScreenStore.record` remains the ONLY writer and its `ScreenAlreadyRecorded` refusal remains
+       the structural backstop for the race where the store changes under a running walk, and a
+       trigger whose pins MISS runs the full walk byte-identically to today.
+    3. Persist ONE frozen, checksummed, append-only run record per run, written EXACTLY ONCE at the
+       run's terminal state by a SINGLE shared writer BOTH callers use — the manager's resolve path
+       (`desk_screen_compute.py:197`/`:226`) and the CLI's `main` (`:271`) — the J-09/J-10
+       `record_topup_run`/`record_reconcile_run` discipline verbatim. Recorded with it: run id,
+       `screen_date`, the five pins as resolved (each honestly `null` when a run failed before
+       resolving it), started/finished UTC, terminal state (`done`/`cancelled`/`failed`), `reused`
+       (true when step 2 short-circuited), `members_total` and `members_attempted` (so "attempted"
+       and "never reached" stay distinct — the J-09 rule), the walk's own outcome counts (ranked,
+       `skipped: no_bars`, `skipped: no_basis`), the resulting `screen_id` or an honest `null`, and —
+       on `failed` — the exception detail VERBATIM plus the member the walk was on when it raised.
+       This journey changes NO walk behavior: `compute_screen`'s member loop (`desk_screen.py:455`)
+       keeps its shipped semantics (no per-member guard is added, no error skip row is invented, a
+       cancelled partial walk is still never recorded) — the record makes the outcome legible, it
+       does not alter it. A run whose process ends before the terminal write records NOTHING and the
+       ledger never invents an entry for it (J-09's honest limit, asserted by a test).
+    4. Own it exactly once: a new desk module (name at build discretion, e.g.
+       `app/research/desk_screen_log.py`) as the ONLY owner and `GET /research/desk/screen/runs` as
+       the ONLY serving endpoint (lightweight run-meta list + the latest full record; honest-empty
+       `{"runs": [], "latest": null}`, HTTP 200, before any run), serving its own store's
+       verification errors as `integrity_errors` in the same key and shape its four sibling desk GETs
+       already use (the J-12 rule) — registered as a NEW row in the blueprint's Data Contract BEFORE
+       the code lands, storage dir a bare env-var-or-sibling default (the `resolve_desk_screen_dir`/
+       `resolve_desk_topup_log_dir` precedent — deliberately NOT a new `Config` field). The record
+       describes the RUN only: screen rows, skip rows and the five-pin snapshot key keep their single
+       owner (`desk_screen.ScreenStore`) and their single serving endpoint
+       (`GET /research/desk/screen`), and nothing about what a snapshot records, how it is keyed, or
+       how rows are ranked changes. No new MCP tool (J-06's exactly-17-tool contract stays green and
+       `get_endpoint`'s `/research/` allowlist already reaches the new path), no scheduler, no
+       auto-refresh, no retry loop — a screen run stays an explicit operator act and page-load GETs
+       trigger nothing.
+    5. Surface it on `/desk`: a read-only "Screen Runs" section beside the shipped Screen History,
+       Top-up Runs and Index Reconciliation sections (the same table-plus-latest-detail pattern, no
+       recompute, NO new control), each run showing its date + id, terminal state, members
+       attempted-of-total, the ranked/skipped counts, its own recorded start→finish elapsed and the
+       snapshot id it produced — or the honest "reused <id> — no walk was performed" and "nothing
+       recorded" states — with the latest run's failure detail rendered verbatim when it failed, an
+       honest no-run-recorded empty state, and its ledger's `integrity_errors` line. **No new
+       ranked-table column and no change to the ranked table**, so J-16's measured width contract and
+       every stored golden replay script stand untouched. Copy = descriptive measurement only: the
+       page states what a run attempted and what it produced, never advice, imperative, urgency,
+       prediction, or any saving/waste/efficiency/speed claim; `tests/test_copy_discipline.py` stays
+       green unmodified.
+    6. Test fixture-scoped: a completed run's recorded counts are byte-identical to its own
+       snapshot's `len(rows)` and its skip counts by reason; an identical-pin re-trigger records
+       `reused: true` with `members_attempted: 0`, makes provably ZERO `compute_tradability` calls
+       (assert the call count — the J-11/J-13/J-14/J-15 precedent), returns the SAME `screen_id` and
+       writes no second snapshot file; a cancelled run records `cancelled` with
+       `members_attempted < members_total` and `screen_id: null` while still recording no snapshot; a
+       raising member records `failed` with the detail verbatim and that member named, and no
+       snapshot; a second run appends a new record while the first record file stays byte-identical;
+       the GET is honest-empty before any run and triggers nothing; and every EXISTING test in
+       `test_desk_screen_compute.py` and `test_desk_screen.py` passes UNMODIFIED — in particular
+       `test_second_run_with_identical_pins_reuses_the_existing_snapshot_no_second_file` (:373),
+       `test_cli_second_invocation_with_identical_pins_reuses_the_existing_snapshot` (:718) and
+       `test_a_corrupted_snapshot_at_the_same_key_resolves_state_failed_never_a_silent_overwrite`
+       (:287), whose outcomes the pre-check must reproduce exactly (if one genuinely pins a full walk
+       on an identical-pin retrigger, disclose it in the iteration record rather than edit it — the
+       J-17 precedent).
+  - Acceptance: on the fixture-scoped rig `GET /research/desk/screen/runs` serves the honest empty
+    payload before any run and, after one fixture-scoped screen run, ONE record whose `members_total`/
+    `members_attempted`, ranked and skip-by-reason counts, five pins and `screen_id` are byte-identical
+    to the snapshot that run recorded (**single source of truth**: the run record is registered in the
+    Data Contract with the new desk module as its only owner and `GET /research/desk/screen/runs` as
+    its only serving endpoint; it records the RUN only — rows, skip rows, the five-pin key and the rank
+    order keep `desk_screen.ScreenStore` as their sole owner and `GET /research/desk/screen` as their
+    sole serving endpoint, with zero change to any recorded snapshot shape — and every pin is resolved
+    through the accessor that already owns it (`screen_as_of`, `UniverseStore.list`,
+    `Config.config_fingerprint`, `compute_bar_store_signature` over `desk_coverage`), never a second
+    derivation; this SSOT criterion stands in place of a PnL-ledger append, which this era's Non-Goals
+    forbid); a re-trigger under identical pins returns the SAME `screen_id` with `reused: true`,
+    records `members_attempted: 0`, makes zero `compute_tradability` calls and writes no second
+    snapshot file, while a trigger whose pins MISS still walks every member and records a snapshot
+    byte-identical to what those same pins produce today (a golden comparison proves the recorded rows
+    and their order unmoved); a cancelled run records `cancelled` with
+    `members_attempted < members_total`, `screen_id: null` and no snapshot; a run interrupted before
+    its terminal write leaves the ledger honestly empty rather than a fabricated entry; a second run
+    appends a new record while every previously recorded universe, screen, top-up and reconciliation
+    file is proven byte-identical on disk (SHA-256 listing — nothing backfilled, repaired or
+    rewritten); in a real browser after the T-9 clean rebuild, `/desk` shows the honest
+    no-run-recorded state in one screenshot and, after a fixture-scoped run, the Screen Runs section
+    with attempted-of-total, the ranked/skipped counts, the elapsed and the produced snapshot id
+    legible in another, plus one screenshot in which a `reused` run's own row states that no walk was
+    performed — all at a 1440×900 viewport with no horizontal scroll and the ranked briefing table
+    rendering exactly as J-16 shipped it (T-10: no screenshot ⇒ `unknown`, never `passing`; no native
+    `title` tooltip is required by this journey, so the T-10a headed rig is not needed); a
+    **`[NEW]`-flagged demo-narrator walkthrough** covers the screen-run disclosure end to end,
+    narrated over a populated ledger; and the full backend suite is green with
+    `Config().config_fingerprint()` still `08e471b10130e1e2`, zero new `Config` fields, the `default`
+    profile and `v1` byte-identical (engine equivalence green), the MCP surface still exactly 17
+    tools, zero diff to
+    `desk_screen.py`'s recorded row/snapshot shapes and to
+    `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`desk_coverage.py`/`desk_topup_log.py`/`StructureChart.tsx`,
+    and `tests/test_copy_discipline.py` + `tests/test_desk_ui_guards.py` +
+    `tests/test_desk_hover_tooltip_guard.py` green unmodified. *(Keyless core; browser-verifiable. A
+    real ~101-member screen run stays an operator-run act, reported honestly as run-or-not-run — never
+    a CI gate. Why: measured 2026-07-31 from the desk's own artifacts. **The desk's central act is the
+    only compute whose runs vanish.** `.data/screen` holds 11 recorded snapshots and every one carries
+    exactly `{id, screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature,
+    created_utc, rows, skipped}` — no start time, no duration, no members-attempted count, no terminal
+    state — while its two lesser siblings each keep a durable ledger: `.data/topup_runs` holds
+    `topup-2026-07-29-5de907c83fc4` (404 pairs, `12:00:29.889748Z` → `12:04:53.521809Z` = 4m23.6s) and
+    `.data/index_reconcile_runs` holds two reconcile records (5.5 s and 10.8 s), each with its own
+    state, counts and timings. `DeskScreenComputeManager`'s state is process-scoped and "honestly lost
+    on restart" (its own docstring, `desk_screen_compute.py:9-11`), so every screen run that failed,
+    was cancelled, or found its pins already recorded left NOTHING on disk anywhere; the only runs with
+    any trace are the 11 that happened to write a NEW snapshot, and even they cannot say how long they
+    took — the four recorded back-to-back on 2026-07-29 (`created_utc` 12:06:52.688, 12:15:46.801,
+    12:22:19.019, 12:24:33.312) sit 8m54s, 6m32s and 2m14s apart, which bounds nothing. **The silence
+    is paid for on every duplicate click.** `/desk`'s Run Screen always submits today's UTC date
+    (`todayUtcDate`, `apps/frontend/app/desk/page.tsx:204/209`) and `trigger` "ALWAYS runs the full
+    member walk … rather than pre-checking the store before paying for it"
+    (`desk_screen_compute.py:21`), calling `compute_tradability` DIRECTLY — never through the 128 MB
+    durable `tradability_cache.db` that `GET /research/tradability` reads (`:23-27`) — across all 101
+    members of `universe-2026-07-25-49b33fa31680`, after which `ScreenStore.record` refuses the
+    duplicate; iter-3's own dev handoff live-verified the first symbol alone taking several seconds
+    cold. **And the fix needs no new machinery:** the same docstring names it ("a future iteration can
+    add a cheap pre-check (the five pins resolve synchronously before the walk, the SAME way
+    `members_total` already does)"), `compute_bar_store_signature` (`desk_screen.py:255`) exists for
+    exactly that purpose, and `find_by_key` (`:602`) is already called on that path one line after the
+    walk. **When a run does die, the record is the only place the reason could live:**
+    `compute_screen`'s member loop (`desk_screen.py:455`) has no per-member guard and
+    `_resolve_reference_close_and_history` raises on its own invariant (`:378`), so one member's
+    exception discards all 100 ranked rows already computed — today into a process-scoped snapshot the
+    next restart erases.)*
+
 <!-- /AUTO:journeys -->
 
 ## Anti-goals
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-desk/state/assumptions.md        | 33 ++++++++++++++++++++++
 runs/goal-session-desk/state/blueprint.md          |  6 +++-
 .../state/enhancement-proposals.jsonl              |  2 ++
 runs/goal-session-desk/state/proposer-result.json  |  2 +-
 runs/goal-session-desk/telemetry.jsonl             | 22 +++++++++++++++
 runs/goal-session-desk/trace/trace.jsonl           |  4 +++
 6 files changed, 67 insertions(+), 2 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
