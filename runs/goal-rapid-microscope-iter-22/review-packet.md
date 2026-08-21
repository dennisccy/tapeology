# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 40fe9cc..f6d3db7 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -56,7 +56,13 @@ from .micro_snapshots import (
     resolve_micro_snapshots_dir,
 )
 from .routes import get_bar_index, get_bar_store, get_dataset_store, get_registry, get_study_market_adapter
-from .scout import ScoutComputeManager, list_scout_families
+from .scout import (
+    GRID_SELECTOR_CAPITULATION_PILOT,
+    GRID_SELECTOR_DELTA_DIVERGENCE_PILOT,
+    GRID_SELECTOR_RANGE_WALL_PILOT,
+    ScoutComputeManager,
+    list_scout_families,
+)
 from .scout_ledger import ScoutLedger, resolve_scout_ledger_dir
 from .tick_recorder import (
     RecorderCheckpointStore,
@@ -262,14 +268,25 @@ def get_micro_exposure_registry_dir() -> str:
 class ScoutComputeRequest(BaseModel):
     """Body for ``POST /research/desk/micro/scout/compute`` (J-09, additive). ``grid`` defaults to
     ``None`` -- omitted (or the body omitted entirely, same as every pre-J-09 caller), this route's
-    behavior stays byte-identical: the unchanged default reference grid.
-    ``scout.GRID_SELECTOR_DELTA_DIVERGENCE_PILOT`` runs ONLY the ONE J-09 pilot candidate this era
-    screens (Studies 1/3 stay frozen-in-source only -- structurally unreachable through this
-    route)."""
+    behavior stays byte-identical: the unchanged default reference grid. As of iteration 22, each of
+    ``scout.GRID_SELECTOR_RANGE_WALL_PILOT`` / ``scout.GRID_SELECTOR_DELTA_DIVERGENCE_PILOT`` /
+    ``scout.GRID_SELECTOR_CAPITULATION_PILOT`` runs ONLY its own ONE predeclared pilot candidate --
+    never the 6-wide default grid, never more than one candidate per request."""
 
     grid: str | None = None
 
 
+# grid_selector -> which of resolver/playbook_store this route must construct for it -- the SAME
+# structure_context.kind split ``scout._PILOT_GRID_SELECTORS`` already encodes, read here by VALUE
+# (never a second, independently-maintained selector->kind table) so the route stays selector-aware
+# rather than "any non-default selector gets a resolver", which stopped being true the moment a
+# playbook_signal-kind selector existed.
+_BAND_TOUCH_PILOT_SELECTORS = frozenset(
+    {GRID_SELECTOR_RANGE_WALL_PILOT, GRID_SELECTOR_DELTA_DIVERGENCE_PILOT}
+)
+_PLAYBOOK_SIGNAL_PILOT_SELECTORS = frozenset({GRID_SELECTOR_CAPITULATION_PILOT})
+
+
 @router.post("/scout/compute")
 def trigger_scout_compute(
     body: ScoutComputeRequest | None = None,
@@ -277,6 +294,7 @@ def trigger_scout_compute(
     snapshots_dir: str = Depends(get_micro_snapshots_dir),
     ledger_dir: str = Depends(get_scout_ledger_dir),
     bar_store: BarStore = Depends(get_bar_store),
+    playbook_store: PlaybookStore = Depends(get_playbook_store),
     exposure_registry_dir: str = Depends(get_micro_exposure_registry_dir),
     manager: ScoutComputeManager = Depends(get_scout_compute_manager),
 ) -> dict:
@@ -285,18 +303,24 @@ def trigger_scout_compute(
     already running.
 
     J-09: ``body.grid`` selects ``ScoutComputeManager.trigger``'s own ``grid_selector`` -- see
-    that method's docstring. ``bar_store`` is an ADDITIVE dependency (the SAME
-    ``routes.get_bar_store`` the readiness route now also uses); constructing the
-    ``BandMapResolver`` it feeds is CONDITIONAL on a non-default selector -- this is a POST,
-    operator-triggered act (never a page-load GET), so the construction cost only lands on the
-    request that actually asks for it.
-
-    iter-21 audit fix B1: the pilot selector also carries the ``ExposureRegistry`` its walk-forward
-    floor check needs, so the operator-reachable run RECORDS that decision (a second ledger row
-    under the same ``candidate_id``) exactly as goal.md IN SCOPE item 6 requires -- previously that
-    stage existed in source but ran only inside a unit test."""
+    that method's docstring. ``bar_store``/``playbook_store`` are ADDITIVE dependencies (the SAME
+    ``routes.get_bar_store``/``desk_routes.get_playbook_store`` the readiness/walk-forward routes
+    already use); constructing the ``BandMapResolver`` a ``band_touch``-kind selector needs, or
+    passing the ``playbook_store`` a ``playbook_signal``-kind selector needs, is SELECTOR-AWARE
+    (iter-22: three pilot selectors now exist, spanning two different ``structure_context.kind``
+    values) -- this is a POST, operator-triggered act (never a page-load GET), so the construction
+    cost only lands on the request that actually asks for it.
+
+    iter-21 audit fix B1 (extended iter-22 to all three pilot selectors): every pilot selector also
+    carries the ``ExposureRegistry`` its walk-forward floor check needs, so the operator-reachable
+    run RECORDS that decision (a second ledger row under the same ``candidate_id``) exactly as
+    goal.md IN SCOPE item 6 requires -- previously that stage existed in source but ran only inside
+    a unit test."""
     grid_selector = body.grid if body is not None else None
-    resolver = BandMapResolver(bar_store, CONFIG) if grid_selector is not None else None
+    resolver = BandMapResolver(bar_store, CONFIG) if grid_selector in _BAND_TOUCH_PILOT_SELECTORS else None
+    playbook_store_for_trigger = (
+        playbook_store if grid_selector in _PLAYBOOK_SIGNAL_PILOT_SELECTORS else None
+    )
     # iter-21 audit fix B1: the pilot run's walk-forward floor-check stage reads the SAME durable
     # exposure registry `POST /walkforward/compute` already depends on (never a second, differently
     # rooted one). Constructed ONLY for a non-default selector -- the default grid's request path is
@@ -304,7 +328,8 @@ def trigger_scout_compute(
     exposure_registry = ExposureRegistry(exposure_registry_dir) if grid_selector is not None else None
     result = manager.trigger(
         dataset_store, CONFIG, snapshots_dir, ledger_dir,
-        grid_selector=grid_selector, resolver=resolver, exposure_registry=exposure_registry,
+        grid_selector=grid_selector, resolver=resolver, playbook_store=playbook_store_for_trigger,
+        exposure_registry=exposure_registry,
     )
     if result["state"] == "refused":
         return result
diff --git a/apps/backend/app/research/scout.py b/apps/backend/app/research/scout.py
index 0eeaadb..7f4a867 100644
--- a/apps/backend/app/research/scout.py
+++ b/apps/backend/app/research/scout.py
@@ -12,15 +12,18 @@ the two production-boundary rules that module deliberately does NOT (module docs
 anchor, with no playbook-signal or band-touch conditioning -- this era's OPERATOR-run production
 grid (the CLI, ``ScoutComputeManager``'s default trigger) is unchanged by J-09.
 
-**J-09 wires the other two ``structure_context.kind`` values, in a SEPARATE, frozen
-``pilot_study_candidate_grid``.** ``extract_anchors`` now supports ``"band_touch"`` (via
+**J-09 wires all three ``structure_context.kind`` combinations, in a SEPARATE, frozen
+``pilot_study_candidate_grid``.** ``extract_anchors`` supports ``"band_touch"`` (via
 ``micro_join.enumerate_band_touches`` + ``micro_join.join_band_touch``) and ``"playbook_signal"``
 (via ``micro_join.join_playbook_signal``) -- ``ScoutUnsupportedStructureContextError`` still guards
 any FUTURE, genuinely-unsupported value (there is none today: the closed
-``STRUCTURE_CONTEXT_KINDS`` set is now fully wired). Only ONE of the three predeclared pilot-study
-candidates (delta divergence at level tests) is taken through ``register_and_screen_candidate``
-this iteration -- the other two exist frozen-in-source only (goal.md OUT OF SCOPE, explicitly
-deferred per the era's own scope-pressure order).
+``STRUCTURE_CONTEXT_KINDS`` set is fully wired). As of iteration 22, all three predeclared
+pilot-study candidates (range-wall failed aggression, delta divergence at level tests, capitulation
+exhaustion) are taken through ``register_and_screen_candidate``, each via its own additive grid
+selector on ``ScoutComputeManager.trigger``/the CLI. Study 1's real screen still examines only its
+single ``failed_aggression_score`` feature -- the eventual opposite-side ``refill_consistent``
+co-occurrence condition remains T-1 (genuinely unbuilt, disclosed in the request's own frozen
+comment, never invented here).
 
 **Read-side law: no second outcome implementation.** Anchor extraction reads snapshot rows through
 ``micro_accessor.MicroAccessor`` (J-05 re-point, unfenced -- TR-3's import-ban; after
@@ -142,7 +145,9 @@ __all__ = [
     "register_and_screen_candidate",
     "default_fixture_grid",
     "pilot_study_candidate_grid",
+    "GRID_SELECTOR_RANGE_WALL_PILOT",
     "GRID_SELECTOR_DELTA_DIVERGENCE_PILOT",
+    "GRID_SELECTOR_CAPITULATION_PILOT",
     "run_scout_grid_and_record",
     "register_screen_and_walkforward_check",
     "list_scout_families",
@@ -1581,19 +1586,24 @@ def default_fixture_grid(dataset_store: DatasetStore, *, grid_version: int = 1)
 
 
 # === J-09: the three predeclared pilot-study candidate requests, frozen-in-source, in goal.md's
-# own stated priority order (Study 1, 2, 3) -- module docstring. Only Study 2 (delta divergence) is
-# taken through ``register_and_screen_candidate`` this iteration (below); Studies 1 and 3 exist
-# here, reviewable and unit-tested for shape (TC-4), but deliberately UNSCREENED (goal.md OUT OF
-# SCOPE, TC-7) -- named, not silently dropped, in the dev handoff.
+# own stated priority order (Study 1, 2, 3) -- module docstring. As of iteration 22, all three are
+# taken through ``register_and_screen_candidate`` (below), each via its own additive grid selector
+# -- Study 1's real screen still carries only its single ``failed_aggression_score`` feature (T-1:
+# the ``refill_consistent`` co-occurrence condition is genuinely unbuilt, disclosed in its own
+# frozen request comment below, not invented here).
 
 PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION = "range_wall_failed_aggression"
 PILOT_STUDY_DELTA_DIVERGENCE_LEVEL_TESTS = "delta_divergence_level_tests"
 PILOT_STUDY_CAPITULATION_EXHAUSTION = "capitulation_exhaustion"
 
-# ``ScoutComputeManager.trigger``/``main``'s own additive grid-selector value (below) -- the ONLY
-# pilot-grid value either accepts, so Studies 1/3 are structurally unreachable through the compute
-# manager or the CLI this iteration (goal.md OUT OF SCOPE).
+# ``ScoutComputeManager.trigger``/``main``'s own additive grid-selector values (below) -- one per
+# predeclared pilot study, each wired the SAME way (one-element grid, required
+# resolver/playbook_store, required exposure_registry) so every study's walk-forward floor-check
+# decision is recorded on the SAME operator-reachable path (CLI or ``POST /scout/compute``), never
+# only a unit test (the iter-21 audit's own B1 lesson, extended to all three this iteration).
+GRID_SELECTOR_RANGE_WALL_PILOT = "range_wall_failed_aggression_pilot"
 GRID_SELECTOR_DELTA_DIVERGENCE_PILOT = "delta_divergence_pilot"
+GRID_SELECTOR_CAPITULATION_PILOT = "capitulation_exhaustion_pilot"
 
 
 def pilot_study_candidate_grid(
@@ -1668,6 +1678,18 @@ def pilot_study_candidate_grid(
     }
 
 
+# Grid-selector -> (pilot_study_candidate_grid's own study id, structure_context.kind) -- the ONE
+# table ``ScoutComputeManager.trigger`` and the CLI's ``main()`` both read (never a second,
+# independently-maintained selector->study mapping); the kind decides which of resolver/
+# playbook_store the caller must supply (band_touch needs a resolver, playbook_signal needs a
+# playbook_store -- the two structure_context.kind values the three pilot studies actually span).
+_PILOT_GRID_SELECTORS: dict[str, tuple[str, str]] = {
+    GRID_SELECTOR_RANGE_WALL_PILOT: (PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION, "band_touch"),
+    GRID_SELECTOR_DELTA_DIVERGENCE_PILOT: (PILOT_STUDY_DELTA_DIVERGENCE_LEVEL_TESTS, "band_touch"),
+    GRID_SELECTOR_CAPITULATION_PILOT: (PILOT_STUDY_CAPITULATION_EXHAUSTION, "playbook_signal"),
+}
+
+
 def run_scout_grid_and_record(
     grid: list[dict],
     ledger: ScoutLedger,
@@ -1899,6 +1921,7 @@ class ScoutComputeManager:
         grid_version: int = 1,
         grid_selector: str | None = None,
         resolver: "BandMapResolver | None" = None,
+        playbook_store: "PlaybookStore | None" = None,
         exposure_registry: "ExposureRegistry | None" = None,
     ) -> dict:
         """Start a NEW screening run over ``default_fixture_grid`` (ensuring snapshots exist first,
@@ -1906,54 +1929,64 @@ class ScoutComputeManager:
         process-wide).
 
         ``grid_selector`` (J-09, default ``None``): ``None`` is BYTE-IDENTICAL to every pre-J-09
-        call (the unchanged default grid). ``GRID_SELECTOR_DELTA_DIVERGENCE_PILOT`` selects a
-        ONE-ELEMENT grid -- the SAME frozen delta-divergence request
-        ``pilot_study_candidate_grid`` carries, with ``resolver`` (REQUIRED, a plain ``ValueError``
-        when omitted) attached -- so the pilot candidate is CLI/manager-runnable beside the default
-        grid, never a second endpoint. Studies 1 and 3 are structurally UNREACHABLE through this
-        selector (goal.md OUT OF SCOPE): no other pilot-grid value exists here.
-
-        ``exposure_registry`` (iter-21 audit fix B1) is REQUIRED beside ``resolver`` for the pilot
-        selector and IGNORED for the default grid: it is what lets the pilot run record its
-        walk-forward floor-check decision as a second ledger row under the SAME ``candidate_id``
-        (goal.md IN SCOPE item 6), instead of leaving that stage reachable only from a unit test."""
-        if grid_selector is not None and grid_selector != GRID_SELECTOR_DELTA_DIVERGENCE_PILOT:
+        call (the unchanged default grid). Each of ``GRID_SELECTOR_RANGE_WALL_PILOT`` /
+        ``GRID_SELECTOR_DELTA_DIVERGENCE_PILOT`` / ``GRID_SELECTOR_CAPITULATION_PILOT`` (iter-22:
+        all three predeclared pilot studies, `_PILOT_GRID_SELECTORS`) selects a ONE-ELEMENT grid --
+        the matching frozen request ``pilot_study_candidate_grid`` carries -- so every pilot
+        candidate is CLI/manager-runnable beside the default grid, never a second endpoint. The two
+        ``band_touch``-kind selectors (range-wall, delta-divergence) require ``resolver`` (a plain
+        ``ValueError`` when omitted); the ``playbook_signal``-kind selector (capitulation) requires
+        ``playbook_store`` instead -- selector-aware, since the three studies span two different
+        ``structure_context.kind`` values.
+
+        ``exposure_registry`` (iter-21 audit fix B1, extended iter-22 to all three selectors) is
+        REQUIRED beside ``resolver``/``playbook_store`` for every pilot selector and IGNORED for
+        the default grid: it is what lets the pilot run record its walk-forward floor-check
+        decision as a second ledger row under the SAME ``candidate_id`` (goal.md IN SCOPE item 6),
+        instead of leaving that stage reachable only from a unit test."""
+        if grid_selector is not None and grid_selector not in _PILOT_GRID_SELECTORS:
             raise ValueError(f"ScoutComputeManager.trigger: unknown grid_selector {grid_selector!r}")
-        if grid_selector == GRID_SELECTOR_DELTA_DIVERGENCE_PILOT and resolver is None:
-            raise ValueError(
-                "ScoutComputeManager.trigger: grid_selector="
-                f"{GRID_SELECTOR_DELTA_DIVERGENCE_PILOT!r} requires a resolver"
-            )
-        # iter-21 audit fix B1: the pilot run RECORDS its walk-forward floor-check decision
-        # (goal.md IN SCOPE item 6) -- so the registry that decides `historical_oos` eligibility is
-        # as REQUIRED here as the resolver is, never an optional extra a caller could forget and
-        # silently get a screen-only run back.
-        if grid_selector == GRID_SELECTOR_DELTA_DIVERGENCE_PILOT and exposure_registry is None:
-            raise ValueError(
-                "ScoutComputeManager.trigger: grid_selector="
-                f"{GRID_SELECTOR_DELTA_DIVERGENCE_PILOT!r} requires an exposure_registry"
-            )
+        if grid_selector is not None:
+            _study_id, _structure_kind = _PILOT_GRID_SELECTORS[grid_selector]
+            if _structure_kind == "band_touch" and resolver is None:
+                raise ValueError(
+                    f"ScoutComputeManager.trigger: grid_selector={grid_selector!r} requires a "
+                    "resolver"
+                )
+            if _structure_kind == "playbook_signal" and playbook_store is None:
+                raise ValueError(
+                    f"ScoutComputeManager.trigger: grid_selector={grid_selector!r} requires a "
+                    "playbook_store"
+                )
+            # iter-21 audit fix B1 (extended iter-22 to all three pilot selectors): the pilot run
+            # RECORDS its walk-forward floor-check decision (goal.md IN SCOPE item 6) -- so the
+            # registry that decides `historical_oos` eligibility is as REQUIRED here as
+            # resolver/playbook_store, never an optional extra a caller could forget and silently
+            # get a screen-only run back.
+            if exposure_registry is None:
+                raise ValueError(
+                    f"ScoutComputeManager.trigger: grid_selector={grid_selector!r} requires an "
+                    "exposure_registry"
+                )
         with self._lock:
             if self._snapshot["state"] == "running":
                 return {"state": "refused", "reason": "already_running"}
 
-            if grid_selector == GRID_SELECTOR_DELTA_DIVERGENCE_PILOT:
+            if grid_selector is not None:
+                study_id, structure_kind = _PILOT_GRID_SELECTORS[grid_selector]
                 request = dict(
-                    pilot_study_candidate_grid(dataset_store, grid_version=grid_version)[
-                        PILOT_STUDY_DELTA_DIVERGENCE_LEVEL_TESTS
-                    ]
+                    pilot_study_candidate_grid(dataset_store, grid_version=grid_version)[study_id]
                 )
-                request["resolver"] = resolver
+                if structure_kind == "band_touch":
+                    request["resolver"] = resolver
+                else:
+                    request["playbook_store"] = playbook_store
                 grid = [request]
             else:
                 grid = default_fixture_grid(dataset_store, grid_version=grid_version)
             # The DEFAULT grid stays screen-only, byte-identical to every pre-J-09 run (one ledger
-            # row per candidate); only the pilot selector carries the floor-check stage.
-            floor_check_registry = (
-                exposure_registry
-                if grid_selector == GRID_SELECTOR_DELTA_DIVERGENCE_PILOT
-                else None
-            )
+            # row per candidate); only a pilot selector carries the floor-check stage.
+            floor_check_registry = exposure_registry if grid_selector is not None else None
             run_id = uuid.uuid4().hex
             self._run_id = run_id
             cancel_event = threading.Event()
@@ -2058,12 +2091,15 @@ def _cli_progress_printer() -> Callable[[str], None]:
 
 
 def main() -> int:
-    """``python -m app.research.scout [--grid-version N] [--grid {default,delta_divergence_pilot}]``
-    -- registers and screens this era's bounded reference candidate grid against the operator's
-    REAL dataset/snapshot/ledger directories, synchronously, in-process (the ``micro_snapshots``
+    """``python -m app.research.scout [--grid-version N] [--grid {default,range_wall_failed_
+    aggression_pilot,delta_divergence_pilot,capitulation_exhaustion_pilot}]`` -- registers and
+    screens this era's bounded reference candidate grid against the operator's REAL
+    dataset/snapshot/ledger directories, synchronously, in-process (the ``micro_snapshots``
     CLI-warmer precedent), persisting through the SAME ledger ``GET /research/desk/micro/scout``
     serves. ``--grid`` (J-09, default ``default``) mirrors ``ScoutComputeManager.trigger``'s own
-    ``grid_selector`` -- omitted, byte-identical to every pre-J-09 invocation."""
+    ``grid_selector`` -- omitted, byte-identical to every pre-J-09 invocation; any of the three
+    pilot-study values (iter-22: all three are wired, `_PILOT_GRID_SELECTORS`) runs that ONE
+    predeclared candidate through the SAME operator-reachable path the route uses."""
     parser = argparse.ArgumentParser(
         description="Scout screening CLI warmer -- registers and screens the era's bounded "
         "reference candidate grid, ensuring prerequisite snapshots exist first."
@@ -2072,9 +2108,10 @@ def main() -> int:
         "--grid-version", type=int, default=1, help="the grid_version to stamp on this run's rows."
     )
     parser.add_argument(
-        "--grid", choices=("default", GRID_SELECTOR_DELTA_DIVERGENCE_PILOT), default="default",
-        help="'default' (unchanged) or 'delta_divergence_pilot' (the ONE J-09 pilot candidate "
-        "this era screens -- Studies 1/3 stay frozen-in-source only, never reachable here).",
+        "--grid", choices=("default", *_PILOT_GRID_SELECTORS), default="default",
+        help="'default' (unchanged) or one of the three J-09 pilot-study grid selectors -- "
+        "'range_wall_failed_aggression_pilot', 'delta_divergence_pilot', "
+        "'capitulation_exhaustion_pilot' -- each screening its ONE predeclared candidate.",
     )
     args = parser.parse_args()
 
@@ -2086,24 +2123,29 @@ def main() -> int:
     run_snapshot_build_and_record(dataset_store, config, snapshots_dir, None)
     ledger = ScoutLedger(ledger_dir)
     exposure_registry = None
-    if args.grid == GRID_SELECTOR_DELTA_DIVERGENCE_PILOT:
+    if args.grid in _PILOT_GRID_SELECTORS:
         from .bars import BarStore
+        from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
         from .desk_playbook_context import BandMapResolver
         from .micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir
 
-        resolver = BandMapResolver(BarStore(config.bar_dir_resolved()), config)
-        # iter-21 audit fix B1: the SAME durable registry `POST /walkforward/compute` already reads
-        # (`resolve_micro_exposure_registry_dir` -- never a second, differently-rooted one), so the
-        # pilot run's floor check reads the operator's real exposure state.
+        study_id, structure_kind = _PILOT_GRID_SELECTORS[args.grid]
+        # iter-21 audit fix B1 (extended iter-22 to all three pilot selectors): the SAME durable
+        # registry `POST /walkforward/compute` already reads (`resolve_micro_exposure_registry_dir`
+        # -- never a second, differently-rooted one), so the pilot run's floor check reads the
+        # operator's real exposure state.
         exposure_registry = ExposureRegistry(
             resolve_micro_exposure_registry_dir(config.dataset_dir_resolved())
         )
         request = dict(
-            pilot_study_candidate_grid(dataset_store, grid_version=args.grid_version)[
-                PILOT_STUDY_DELTA_DIVERGENCE_LEVEL_TESTS
-            ]
+            pilot_study_candidate_grid(dataset_store, grid_version=args.grid_version)[study_id]
         )
-        request["resolver"] = resolver
+        if structure_kind == "band_touch":
+            request["resolver"] = BandMapResolver(BarStore(config.bar_dir_resolved()), config)
+        else:
+            request["playbook_store"] = PlaybookStore(
+                resolve_desk_playbook_dir(config.desk_universe_dir_resolved())
+            )
         grid = [request]
     else:
         grid = default_fixture_grid(dataset_store, grid_version=args.grid_version)
diff --git a/apps/backend/tests/test_scout.py b/apps/backend/tests/test_scout.py
index b38253a..4bf3704 100644
--- a/apps/backend/tests/test_scout.py
+++ b/apps/backend/tests/test_scout.py
@@ -1329,20 +1329,49 @@ def test_tc4_setup_id_omitted_from_structure_context_when_not_given():
     assert spec["structure_context"] == {"kind": "none"}
 
 
-def test_tc7_range_wall_and_capitulation_are_frozen_but_never_screened(tmp_path):
-    """TC-7: range-wall-failed-aggression and capitulation-exhaustion exist in the frozen grid but
-    are NOT passed through ``register_and_screen_candidate`` this iteration -- no partial ledger
-    row for either. This test proves the negative directly: an empty scout ledger stays empty
-    after only INSPECTING the frozen grid (never calling the registration entry point for those
-    two study ids)."""
+def test_range_wall_and_capitulation_are_now_screened_with_recorded_decisions_iter22(tmp_path):
+    """Retires iter-21's own negative TC-7 proof ("frozen but never screened") -- as of iteration
+    22 that claim is FALSE: both range-wall-failed-aggression and capitulation-exhaustion ARE taken
+    through the screening entry point (``register_and_screen_candidate``), each producing a real,
+    closed-vocabulary ledger row. Rewritten rather than deleted (see the iter-22 dev handoff's own
+    'Known Issues'/'What Was Built' sections for why): a stale negative assertion left in place
+    would silently start lying about the shipped behavior the moment this iteration landed.
+
+    Renamed off the old ``test_tc7_...`` identifier -- this iteration's OWN phase spec defines a
+    DIFFERENT TC-7 (the CLI-path test, see ``test_iter22_cli_range_wall_pilot_grid_...`` below);
+    keeping the old name here would collide in spirit even though pytest itself only cares about
+    literal name uniqueness."""
     store = _combined_fixture_store(tmp_path)
+    snapshots_dir = str(tmp_path / "snapshots")
+    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)
     ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
     grid = scout.pilot_study_candidate_grid(store)
 
-    # Inspecting the frozen requests never writes anything.
-    assert grid[scout.PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION]
-    assert grid[scout.PILOT_STUDY_CAPITULATION_EXHAUSTION]
-    assert ledger.all_rows() == []
+    range_wall_request = dict(grid[scout.PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION])
+    range_wall_request["resolver"] = _touch_resolver(tmp_path)
+    range_wall_row = scout.register_and_screen_candidate(
+        ledger=ledger, dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
+        **range_wall_request,
+    )
+    assert range_wall_row["decision"] in scout_ledger.CLOSED_DECISIONS
+    assert range_wall_row["structure_context"]["kind"] == "band_touch"
+
+    capitulation_request = dict(grid[scout.PILOT_STUDY_CAPITULATION_EXHAUSTION])
+    first_dataset_id = capitulation_request["corpus_manifest"][0]["dataset_id"]
+    first_meta = store.get(first_dataset_id)
+    capitulation_request["playbook_store"] = _plant_capitulation_signal(tmp_path, dataset_meta=first_meta)
+    capitulation_row = scout.register_and_screen_candidate(
+        ledger=ledger, dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
+        **capitulation_request,
+    )
+    assert capitulation_row["decision"] in scout_ledger.CLOSED_DECISIONS
+    assert capitulation_row["structure_context"] == {"kind": "playbook_signal", "setup_id": "capitulation"}
+
+    rows = ledger.all_rows()
+    assert len(rows) == 2
+    assert {r["candidate_id"] for r in rows} == {
+        range_wall_row["candidate_id"], capitulation_row["candidate_id"],
+    }
 
 
 # === TC-5/TC-6 (goal-rapid-microscope-iter-21, J-09): the delta-divergence candidate, screened +
@@ -1574,3 +1603,265 @@ def test_evaluate_mode_b_fold_is_never_called_by_the_walkforward_floor_check_pat
 
     assert "evaluate_mode_b_fold" not in inspect.getsource(scout.register_screen_and_walkforward_check)
     assert "evaluate_mode_b_fold" not in inspect.getsource(wf.scout_candidate_walkforward_floor_check)
+
+
+# === goal-rapid-microscope-iter-22, J-09: Studies 1 and 3 taken through the SAME operator-reachable
+# path Study 2 already uses (register_screen_and_walkforward_check via the CLI / POST /scout/compute
+# grid-selector) -- no second screening implementation, no second fixture family. ====================
+
+
+def test_iter22_study1_range_wall_screens_with_real_band_touch_anchors(pg_snapshot_store, tmp_path):
+    """TC-6 (byte-identity) + the genuine-screen half of TC-1/TC-2: Study 1's frozen request
+    (``failed_aggression_score``, ``op: "ge", value: 0.5``, ``band_touch``) is passed to
+    ``register_screen_and_walkforward_check`` against the committed hermetic band-touch fixture --
+    reusing the EXACT ``pg_snapshot_store`` + ``_touch_resolver`` pattern iter-21's own TC-1 test
+    already built for this SAME generic single-touch path (a WIDE band over the real PG price range
+    148.80-149.20, no second fixture implementation), producing a genuine, non-vacuous screen over
+    real fixture touches, plus its own walk-forward floor-check row under the same ``candidate_id``.
+
+    (``divergence_fixture`` was tried first and does not work here: it is deliberately built with
+    ``epoch_anchor=0.0`` so Study 2's own PAIRED-touch path never needs a per-touch
+    ``resolver.resolve()``/covering-snapshot round trip -- Study 1's GENERIC single-touch path
+    (``_extract_band_touch_anchors`` -> ``join_band_touch``) DOES need both, keyed on each touch's
+    own real absolute epoch, which a near-1970 ``epoch_anchor`` can never satisfy. ``pg_snapshot_
+    store`` -- the SAME fixture TC-1 already proves resolves real touches through this exact code
+    path -- is the genuinely-reusable committed fixture for THIS study, not the divergence one.)"""
+    from app.research.micro_accessor import ExposureRegistry
+
+    store, snapshots_dir, manifest = pg_snapshot_store
+    resolver = _touch_resolver(tmp_path)
+    first_meta = store.get(manifest[0]["dataset_id"])
+    window_start_epoch = parse_utc_epoch(first_meta["window_start_utc"])
+    resolver._cache.publish(
+        resolver.map_key("PG", window_start_epoch),
+        {"basis_day": "2026-06-08", "bands": [{"side": "resistance", "price_low": 148.80, "price_high": 149.20}]},
+    )
+
+    request = scout.pilot_study_candidate_grid(store)[scout.PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION]
+    # TC-6: byte-identical to the iter-21-frozen values -- no invented co-occurrence field.
+    assert request["feature_name"] == "failed_aggression_score"
+    assert request["params"] == {"op": "ge", "value": 0.5}
+    assert request["structure_context_kind"] == "band_touch"
+
+    ledger = scout_ledger.ScoutLedger(tempfile.mkdtemp())
+    exposure_registry = ExposureRegistry(tempfile.mkdtemp())
+    result = scout.register_screen_and_walkforward_check(
+        ledger=ledger, dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
+        exposure_registry=exposure_registry, resolver=resolver,
+        feature_name=request["feature_name"], transform=request["transform"],
+        params=request["params"], structure_context_kind=request["structure_context_kind"],
+        horizon_key=request["horizon_key"], corpus_manifest=request["corpus_manifest"],
+        grid_version=request["grid_version"], sidedness=request["sidedness"],
+        fitting_rule=request["fitting_rule"], withheld_excluded=request["withheld_excluded"],
+    )
+
+    screen_row = result["screen_row"]
+    assert screen_row["structure_context"] == {"kind": "band_touch"}
+    assert screen_row["decision"] in scout_ledger.CLOSED_DECISIONS
+    # Non-vacuous: real band touches were actually joined and fed the screen (never a hollow
+    # zero-anchor pass-through) -- the SAME fixture TC-1 already proves resolves real touches.
+    screen_result = screen_row["screen_result"]
+    assert screen_result["n_candidate"] + screen_result["n_comparator"] > 0
+
+    wf_row = result["walkforward_row"]
+    assert wf_row["candidate_id"] == screen_row["candidate_id"]
+    assert wf_row["stage"] == "walkforward_floor_check"
+    assert wf_row["decision"] == "killed_insufficient_n"
+    assert wf_row["walkforward_floor_check"]["oos_session_count"] == 0
+    family_rows = ledger.rows_for_family(screen_row["family_id"])
+    assert len(family_rows) == 2
+    assert scout_ledger.distinct_variant_count(family_rows) == 1
+
+
+def test_iter22_study3_capitulation_screens_with_real_playbook_signal_anchor(pg_snapshot_store, tmp_path):
+    """The genuine-screen half of TC-3/TC-4: Study 3's frozen request (``failed_aggression_score``,
+    ``op: "ge", value: 0.7``, ``playbook_signal``/``setup_id="capitulation"``) is passed to
+    ``register_screen_and_walkforward_check`` against a hermetic ``PlaybookStore`` fixture carrying
+    ONE ``setup_id="capitulation"`` signal -- reusing the EXACT ``pg_snapshot_store`` +
+    ``_plant_capitulation_signal(tmp_path, dataset_meta=...)`` pattern iter-21's own TC-1/TC-2 tests
+    already built (no second fixture implementation)."""
+    from app.research.micro_accessor import ExposureRegistry
+
+    store, snapshots_dir, manifest = pg_snapshot_store
+    first_meta = store.get(manifest[0]["dataset_id"])
+    playbook_store = _plant_capitulation_signal(tmp_path, dataset_meta=first_meta)
+
+    request = scout.pilot_study_candidate_grid(store)[scout.PILOT_STUDY_CAPITULATION_EXHAUSTION]
+    assert request["feature_name"] == "failed_aggression_score"
+    assert request["params"] == {"op": "ge", "value": 0.7}
+    assert request["structure_context_kind"] == "playbook_signal"
+    assert request["setup_id"] == "capitulation"
+
+    ledger = scout_ledger.ScoutLedger(tempfile.mkdtemp())
+    exposure_registry = ExposureRegistry(tempfile.mkdtemp())
+    result = scout.register_screen_and_walkforward_check(
+        ledger=ledger, dataset_store=store, snapshots_dir=snapshots_dir, config=CONFIG,
+        exposure_registry=exposure_registry, playbook_store=playbook_store,
+        feature_name=request["feature_name"], transform=request["transform"],
+        params=request["params"], structure_context_kind=request["structure_context_kind"],
+        horizon_key=request["horizon_key"], corpus_manifest=request["corpus_manifest"],
+        grid_version=request["grid_version"], sidedness=request["sidedness"],
+        fitting_rule=request["fitting_rule"], setup_id=request["setup_id"],
+        withheld_excluded=request["withheld_excluded"],
+    )
+
+    screen_row = result["screen_row"]
+    assert screen_row["structure_context"] == {"kind": "playbook_signal", "setup_id": "capitulation"}
+    assert screen_row["decision"] in scout_ledger.CLOSED_DECISIONS
+
+    wf_row = result["walkforward_row"]
+    assert wf_row["candidate_id"] == screen_row["candidate_id"]
+    assert wf_row["stage"] == "walkforward_floor_check"
+    assert wf_row["decision"] == "killed_insufficient_n"
+    family_rows = ledger.rows_for_family(screen_row["family_id"])
+    assert len(family_rows) == 2
+    assert scout_ledger.distinct_variant_count(family_rows) == 1
+
+
+def test_iter22_default_grid_still_writes_exactly_one_row_per_candidate_no_floor_check_row(tmp_path):
+    """TC-5 regression guard, restated directly against ``run_scout_grid_and_record`` (the route's
+    own ``test_iter21_audit_b1_default_grid_run_is_still_screen_only`` already covers this at the
+    HTTP layer; this is the same guarantee at the function layer the CLI and the manager both call
+    through): the unchanged default reference grid never carries a ``walkforward_floor_check``
+    stage row, regardless of whether an ``exposure_registry`` is even supplied."""
+    store = _combined_fixture_store(tmp_path)
+    snapshots_dir = str(tmp_path / "snapshots")
+    run_snapshot_build_and_record(store, CONFIG, snapshots_dir, None)
+    ledger = scout_ledger.ScoutLedger(tmp_path / "ledger")
+    grid = scout.default_fixture_grid(store, grid_version=1)
+
+    rows = scout.run_scout_grid_and_record(grid, ledger, store, snapshots_dir, CONFIG)
+
+    assert len(rows) == len(grid)
+    all_ledgered_rows = ledger.all_rows()
+    assert len(all_ledgered_rows) == len(grid)
+    assert all(row.get("stage") != "walkforward_floor_check" for row in all_ledgered_rows)
+
+
+# --- route-level: POST /scout/compute {"grid": ...} for the two NEW selectors, mirroring
+# test_iter21_audit_b1_pilot_route_records_the_walkforward_floor_check_row exactly. Hermetic: an
+# EMPTY bar store / EMPTY playbook store (no band map / no signal ever resolves -> an honest
+# zero-anchor screen) and a fresh, never-initialized exposure registry (zero historical_oos
+# sessions -> the honest insufficient_n refusal) -- never the operator's real stores. ---------------
+
+
+def test_iter22_range_wall_pilot_route_records_the_walkforward_floor_check_row(scout_client, tmp_path):
+    """TC-1/TC-2: the operator-reachable range-wall pilot run (``POST /scout/compute
+    {"grid": "range_wall_failed_aggression_pilot"}``) reaches ``state: "done"`` and records both a
+    screen-stage row (closed-vocabulary decision, ``structure_context.kind == "band_touch"``) and a
+    walk-forward floor-check row under the SAME ``candidate_id``."""
+    from app.research.bars import BarStore
+    from app.research.micro_routes import get_micro_exposure_registry_dir
+    from app.research.routes import get_bar_store
+
+    c, store, snapshots_dir, ledger_dir, manager = scout_client
+    app.dependency_overrides[get_bar_store] = lambda: BarStore(str(tmp_path / "audit_bars"))
+    app.dependency_overrides[get_micro_exposure_registry_dir] = lambda: str(tmp_path / "audit_exposure")
+    try:
+        resp = c.post(
+            "/research/desk/micro/scout/compute",
+            json={"grid": scout.GRID_SELECTOR_RANGE_WALL_PILOT},
+        )
+        assert resp.status_code == 200
+        assert resp.json()["state"] == "running"
+        manager.join_all(timeout=60.0)
+        assert manager.snapshot()["state"] == "done", manager.snapshot()["error"]
+    finally:
+        app.dependency_overrides.pop(get_bar_store, None)
+        app.dependency_overrides.pop(get_micro_exposure_registry_dir, None)
+
+    rows = scout_ledger.ScoutLedger(ledger_dir).all_rows()
+    assert len(rows) == 2, [r.get("stage") for r in rows]
+    screen_row, wf_row = rows
+    assert wf_row["candidate_id"] == screen_row["candidate_id"]
+    assert screen_row["structure_context"]["kind"] == "band_touch"
+    assert screen_row["decision"] in scout_ledger.CLOSED_DECISIONS
+    assert wf_row["stage"] == "walkforward_floor_check"
+    assert wf_row["decision"] == "killed_insufficient_n"
+    assert wf_row["walkforward_floor_check"]["status"] == "insufficient_n"
+    assert wf_row["walkforward_floor_check"]["oos_session_count"] == 0
+
+    body = c.get("/research/desk/micro/scout").json()
+    assert len(body["families"]) == 1
+    assert body["families"][0]["trials"][0]["feature"]["name"] == "failed_aggression_score"
+
+
+def test_iter22_capitulation_pilot_route_records_the_walkforward_floor_check_row(scout_client, tmp_path):
+    """TC-3/TC-4: the operator-reachable capitulation pilot run (``POST /scout/compute
+    {"grid": "capitulation_exhaustion_pilot"}``) reaches ``state: "done"`` and records both a
+    screen-stage row (``structure_context == {"kind": "playbook_signal", "setup_id":
+    "capitulation"}``) and a walk-forward floor-check row under the SAME ``candidate_id``."""
+    from app.research.desk_playbook import PlaybookStore
+    from app.research.desk_routes import get_playbook_store
+    from app.research.micro_routes import get_micro_exposure_registry_dir
+
+    c, store, snapshots_dir, ledger_dir, manager = scout_client
+    app.dependency_overrides[get_playbook_store] = lambda: PlaybookStore(tmp_path / "audit_playbook")
+    app.dependency_overrides[get_micro_exposure_registry_dir] = lambda: str(tmp_path / "audit_exposure")
+    try:
+        resp = c.post(
+            "/research/desk/micro/scout/compute",
+            json={"grid": scout.GRID_SELECTOR_CAPITULATION_PILOT},
+        )
+        assert resp.status_code == 200
+        assert resp.json()["state"] == "running"
+        manager.join_all(timeout=60.0)
+        assert manager.snapshot()["state"] == "done", manager.snapshot()["error"]
+    finally:
+        app.dependency_overrides.pop(get_playbook_store, None)
+        app.dependency_overrides.pop(get_micro_exposure_registry_dir, None)
+
+    rows = scout_ledger.ScoutLedger(ledger_dir).all_rows()
+    assert len(rows) == 2, [r.get("stage") for r in rows]
+    screen_row, wf_row = rows
+    assert wf_row["candidate_id"] == screen_row["candidate_id"]
+    assert screen_row["structure_context"] == {"kind": "playbook_signal", "setup_id": "capitulation"}
+    assert screen_row["decision"] in scout_ledger.CLOSED_DECISIONS
+    assert wf_row["stage"] == "walkforward_floor_check"
+    assert wf_row["decision"] == "killed_insufficient_n"
+
+    body = c.get("/research/desk/micro/scout").json()
+    assert len(body["families"]) == 1
+    assert body["families"][0]["trials"][0]["structure_context"] == {
+        "kind": "playbook_signal", "setup_id": "capitulation",
+    }
+
+
+# --- CLI path: python -m app.research.scout --grid <new selector> -- proves the CLI, not only a
+# unit test or the HTTP route, produces both rows (TC-7). Mirrors
+# test_tc11_the_cli_main_produces_the_same_grid_against_a_pointed_dataset_dir exactly, extended
+# with the additional env-var-pointed bar/exposure directories the pilot branch now needs. --------
+
+
+def test_iter22_cli_range_wall_pilot_grid_produces_the_screen_and_floor_check_rows(
+    tmp_path, monkeypatch, capsys
+):
+    """TC-7: ``python -m app.research.scout --grid range_wall_failed_aggression_pilot`` against the
+    committed fixture prints ``1 candidate(s) processed`` and the on-disk ledger holds both the
+    screen row and the walk-forward floor-check row -- proving the CLI path, not only a unit test
+    or the HTTP route, produces them."""
+    import sys
+
+    _combined_fixture_store(tmp_path)
+    dataset_dir = str(tmp_path / "datasets")
+    scout_dir = str(tmp_path / "cli_scout")
+    bar_dir = str(tmp_path / "cli_bars")
+    exposure_dir = str(tmp_path / "cli_exposure")
+    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", dataset_dir)
+    monkeypatch.setenv("TAPEOLOGY_MICRO_SCOUT_DIR", scout_dir)
+    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", bar_dir)
+    monkeypatch.setenv("TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR", exposure_dir)
+    monkeypatch.setattr(sys, "argv", ["scout.py", "--grid", scout.GRID_SELECTOR_RANGE_WALL_PILOT])
+
+    exit_code = scout.main()
+    assert exit_code == 0
+
+    captured = capsys.readouterr()
+    assert "1 candidate(s) processed" in captured.out
+
+    rows = scout_ledger.ScoutLedger(scout_dir).all_rows()
+    assert len(rows) == 2, [r.get("stage") for r in rows]
+    screen_row, wf_row = rows
+    assert screen_row["structure_context"]["kind"] == "band_touch"
+    assert wf_row["stage"] == "walkforward_floor_check"
+    assert wf_row["candidate_id"] == screen_row["candidate_id"]
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 7 +++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 2 ++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
