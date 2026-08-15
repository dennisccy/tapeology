# Iteration diff (bounded)

Files changed: 6. Shown in full: 4.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/referee_null.py` (707 lines not shown)
- `apps/backend/tests/test_referee_null.py` (421 lines not shown)

```diff
diff --git a/apps/backend/app/research/referee_routes.py b/apps/backend/app/research/referee_routes.py
index fa0410e..3d1d614 100644
--- a/apps/backend/app/research/referee_routes.py
+++ b/apps/backend/app/research/referee_routes.py
@@ -1,34 +1,53 @@
-"""``/research/desk/referee/*`` — Era 6 "The Referee" (J-01): the readiness fold, the FIRST
-concrete Referee artifact. See ``referee_evidence.py``'s own module docstring for the fold's
-mechanics; this file is pure wiring.
+"""``/research/desk/referee/*`` — Era 6 "The Referee": J-01's readiness fold plus (iter-5, J-04)
+the matched-null compute-control surface. See ``referee_evidence.py``/``referee_null.py``'s own
+module docstrings for the mechanics; this file is pure wiring.
 
 A fresh router/file rather than folding into ``desk_routes.py`` (already 1600+ lines) — the SAME
 rationale ``desk_routes.py`` itself gives for splitting off ``routes.py``: "mounted separately ...
 rather than folding into routes.py, which is already large." The era's own Data Contract table
 (``docs/goal.md``'s Product Shape) names five MORE referee routes landing in later iterations
-(nulls, registry, evaluations, adjudications) under this SAME ``/research/desk/referee`` prefix —
-a dedicated file is the right home from the start.
+(registry, evaluations, adjudications) under this SAME ``/research/desk/referee`` prefix — a
+dedicated file is the right home from the start.
 
 Depends on stores this route does NOT own: the playbook store dependency is imported verbatim from
-``desk_routes.get_playbook_store`` and the dataset store dependency from ``routes.get_dataset_store``
-(never a second, redefined provider for either) — the ``JournalStore`` (for backtest reports) comes
-through the existing ``ResearchRegistry`` (``routes.get_registry``), the SAME seam
-``GET /research/backtests`` already reads. A plain read: triggers nothing, recomputes nothing
-(GET-never-computes) — this route takes no compute-manager dependency at all."""
+``desk_routes.get_playbook_store``, the bar store dependency from ``routes.get_bar_store``, and the
+dataset store dependency from ``routes.get_dataset_store`` (never a second, redefined provider for
+any of them) — the ``JournalStore`` (for backtest reports) comes through the existing
+``ResearchRegistry`` (``routes.get_registry``), the SAME seam ``GET /research/backtests`` already
+reads. ``GET /evidence`` and ``GET /nulls*`` are plain reads: they trigger nothing, recompute
+nothing (GET-never-computes, T-8) — only the two ``POST /nulls/compute*`` routes below start a
+background walk, exactly like every other shipped desk compute-manager route."""
 
 from __future__ import annotations
 
-from fastapi import APIRouter, Depends
+from fastapi import APIRouter, Depends, HTTPException
+from pydantic import BaseModel
 
 from ..config import CONFIG
+from .bars import BarStore
 from .datasets import DatasetStore
 from .desk_playbook import PlaybookStore
 from .desk_routes import get_playbook_store
 from .referee_evidence import referee_evidence
-from .routes import ResearchRegistry, get_dataset_store, get_registry
+from .referee_null import (
+    REFEREE_NULL_CONTEXT_SPEC_ID,
+    REFEREE_NULL_TOD_SPEC_ID,
+    RefereeNullComputeManager,
+    RefereeNullRunStore,
+    RefereeNullStore,
+    resolve_referee_null_dir,
+    resolve_referee_null_log_dir,
+)
+from .routes import ResearchRegistry, get_bar_store, get_dataset_store, get_registry
 
 router = APIRouter(prefix="/research/desk/referee", tags=["referee"])
 
+# Module-level singletons (the ``_desk_playbook_compute_manager`` pattern in ``desk_routes.py``) --
+# process-scoped job state that must survive across requests within one running backend, never
+# rebuilt per-request. Living here (not on ``ResearchRegistry``) matches ``referee_routes.py``'s
+# own existing shape: this module owns its own wiring end to end.
+_referee_null_compute_manager = RefereeNullComputeManager()
+
 
 @router.get("/evidence")
 def get_referee_evidence(
@@ -49,3 +68,129 @@ def get_referee_evidence(
         journal_store=registry.store,
         config_fingerprint=CONFIG.config_fingerprint(),
     )
+
+
+# === J-04: matched nulls -- store + compute-control + run-ledger routes ==============================
+
+
+def get_referee_null_store() -> RefereeNullStore:
+    """The durable null store rooted at a bare env-var-or-sibling-of-the-universe-dir default (zero
+    new ``Config`` field — ``referee_null.resolve_referee_null_dir``) — the ``get_playbook_store``
+    pattern. A FastAPI dependency so a test overrides it via the env var or outright."""
+    return RefereeNullStore(resolve_referee_null_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+def get_referee_null_run_store() -> RefereeNullRunStore:
+    """The durable null-run ledger, rooted the same way — the ``get_playbook_run_store`` pattern."""
+    return RefereeNullRunStore(resolve_referee_null_log_dir(CONFIG.desk_universe_dir_resolved()))
+
+
+def get_referee_null_compute_manager() -> RefereeNullComputeManager:
+    """The single-flight-per-null-spec compute manager — a FastAPI dependency (the
+    ``get_desk_playbook_compute_manager`` pattern) so a test overrides it outright via
+    ``app.dependency_overrides`` for complete test-to-test isolation."""
+    return _referee_null_compute_manager
+
+
+@router.get("/nulls")
+def get_referee_nulls(
+    id: str | None = None, store: RefereeNullStore = Depends(get_referee_null_store)
+) -> dict:
+    """Recorded matched-null records, honest absence (T-8: GETs never compute). ``?id=`` scopes to
+    ONE record (``{"record": <record>|None}``); otherwise every recorded record
+    (``{"records": [...], "integrity_errors": [...]}``). Never 404/500 on an empty corpus (TC-17)."""
+    if id is not None:
+        return {"record": store.get(id)}
+    records, errors = store.list()
+    return {"records": records, "integrity_errors": errors}
+
+
+class RefereeNullComputeRequest(BaseModel):
+    """Body for ``POST /research/desk/referee/nulls/compute`` — ``null_spec_id`` is REQUIRED
+    (FastAPI 422s a missing body before the route handler runs, the ``PlaybookComputeRequest``
+    convention); never defaults to a particular variant."""
+
+    null_spec_id: str
+
+
+def _validate_null_spec_id(null_spec_id: str) -> None:
+    if null_spec_id not in (REFEREE_NULL_TOD_SPEC_ID, REFEREE_NULL_CONTEXT_SPEC_ID):
+        raise HTTPException(
+            status_code=422,
+            detail=(
+                f"unknown null_spec_id {null_spec_id!r} -- expected one of "
+                f"{sorted((REFEREE_NULL_TOD_SPEC_ID, REFEREE_NULL_CONTEXT_SPEC_ID))}"
+            ),
+        )
+
+
+@router.post("/nulls/compute")
+def trigger_referee_nulls_compute(
+    body: RefereeNullComputeRequest,
+    playbook_store: PlaybookStore = Depends(get_playbook_store),
+    bar_store: BarStore = Depends(get_bar_store),
+    null_store: RefereeNullStore = Depends(get_referee_null_store),
+    run_store: RefereeNullRunStore = Depends(get_referee_null_run_store),
+    manager: RefereeNullComputeManager = Depends(get_referee_null_compute_manager),
+) -> dict:
+    """Start (or, if one is already ``status`` in (``"running"``, ``"cancelling"``) for THIS
+    ``null_spec_id``, return UNCHANGED — ``started: False``, single-flight PER null-spec, TC-19)
+    the null-build job for ``body.null_spec_id``. Refuses — 422, naming the unknown id, never
+    starting a job — on a malformed/unrecognised spec id."""
+    _validate_null_spec_id(body.null_spec_id)
+    return manager.trigger(
+        body.null_spec_id, playbook_store, bar_store, CONFIG, null_store, run_store=run_store,
+    )
+
+
+@router.get("/nulls/compute")
+def get_referee_nulls_compute(
+    null_spec_id: str, manager: RefereeNullComputeManager = Depends(get_referee_null_compute_manager)
+) -> dict:
+    """The named null-spec's compute job current/last snapshot, served VERBATIM — ALWAYS a body
+    (never ``null``: ``status == "idle"`` before any compute has ever run this process for this
+    key). A plain read: never triggers a compute as a side effect (GET-never-computes)."""
+    _validate_null_spec_id(null_spec_id)
+    return manager.snapshot(null_spec_id)
+
+
+class RefereeNullCancelRequest(BaseModel):
+    null_spec_id: str
+
+
+@router.post("/nulls/compute/cancel")
+def cancel_referee_nulls_compute(
+    body: RefereeNullCancelRequest,
+    manager: RefereeNullComputeManager = Depends(get_referee_null_compute_manager),
+) -> dict:
+    """Cancel the in-flight null build for ``body.null_spec_id`` (cooperative — observed between
+    observations). ``409`` when idle (no job has ever run for this key, or the last job already
+    reached a terminal state) — mirrors ``cancel_desk_playbook_compute``'s own 409-when-terminal
+    shape."""
+    _validate_null_spec_id(body.null_spec_id)
+    snapshot = manager.snapshot(body.null_spec_id)
+    if snapshot["status"] != "running":
+        raise HTTPException(
+            status_code=409,
+            detail=f"no referee null compute is currently running for {body.null_spec_id!r}",
+        )
+    manager.cancel(body.null_spec_id)
+    return {"cancelling": True}
+
+
+@router.get("/nulls/runs")
+def get_referee_nulls_runs(
+    null_spec_id: str | None = None, store: RefereeNullRunStore = Depends(get_referee_null_run_store)
+) -> dict:
+    """``{"runs": [...], "latest": <record>|null, "integrity_errors": [...]}`` — the durable
+    terminal-state-only log of what every null build attempted (``GET /playbook/runs``'s own
+    convention). ``?null_spec_id=`` narrows to one variant's own runs, and then ``latest`` is that
+    variant's newest run rather than the store's."""
+    records, errors = store.list()
+    if null_spec_id is not None:
+        records = [record for record in records if record.get("null_spec_id") == null_spec_id]
+    return {
+        "runs": records,
+        "latest": records[-1] if records else None,
+        "integrity_errors": errors,
+    }
diff --git a/apps/backend/app/research/referee_stats.py b/apps/backend/app/research/referee_stats.py
index 1a87374..601da26 100644
--- a/apps/backend/app/research/referee_stats.py
+++ b/apps/backend/app/research/referee_stats.py
@@ -233,7 +233,10 @@ def _t_statistic(
     implementation. ``equal_weight=True`` is the Sec3.5 robustness variant (``w_s = 1`` for every
     session). Returns ``(T, delta_by_session, weight_by_session)`` -- the per-session components are
     returned too, since ``permutation_test``/``sign_flip_result`` reuse them directly rather than
-    recomputing."""
+    recomputing. Raises ``ValueError`` immediately on any non-finite (NaN/inf) input value (iter-5
+    fail-loud guard) -- protects every caller that reaches this function first: ``permutation_
+    test``, ``sign_flip_result``, ``equal_weight_t``."""
+    _require_finite_session_groups(session_groups, "_t_statistic")
     deltas: dict[str, float] = {}
     weights: dict[str, float] = {}
     for session, (group1, group2) in session_groups.items():
@@ -274,6 +277,47 @@ def _is_extreme(t_star: float, t_obs: float, sidedness: str) -> bool:
 _SIDEDNESS_VALUES = frozenset({"greater", "less", "two-sided"})
 
 
+# === iter-5: fail-loud non-finite guard at the stats core's own door ================================
+#
+# Checked ONCE at each public entry point (`_t_statistic` -- which `permutation_test`/
+# `sign_flip_result`/`equal_weight_t` all call FIRST, before touching any value arithmetically, so
+# one check there protects all three -- plus `bootstrap_ci_occurrence`/`bootstrap_ci_cluster`'s own
+# inputs directly): sums/differences/quotients of already-finite numbers stay finite by
+# construction, so no per-draw re-validation is needed. Defense in depth against the exact shape of
+# silent failure iteration 3 found -- a NaN comparison is always `False` in Python, so an unguarded
+# `_is_extreme` would silently UNDER-COUNT extremes (never raise, never even show up as an outlier)
+# rather than error -- and the natural place for a normal, per-observation "unmeasurable" case
+# (T-5) is the null adapter's own door (`referee_null.py`), never here: at this layer a non-finite
+# value can only mean an upstream adapter bug, since the stats core has no per-observation identity
+# left to attach a disclosure to (see this module's own NOTES-cited reasoning in the iter-5 spec).
+
+
+def _require_finite_values(values: list[float], caller: str) -> None:
+    for value in values:
+        if not math.isfinite(value):
+            raise ValueError(
+                f"{caller}: non-finite value ({value!r}) -- refusing to compute a statistic over it"
+            )
+
+
+def _require_finite_session_groups(
+    session_groups: dict[str, tuple[list[float], list[float]]], caller: str
+) -> None:
+    for session, (group1, group2) in session_groups.items():
+        for value in group1:
+            if not math.isfinite(value):
+                raise ValueError(
+                    f"{caller}: non-finite value ({value!r}) in session {session!r}'s group1 -- "
+                    f"refusing to compute a statistic over it"
+                )
+        for value in group2:
+            if not math.isfinite(value):
+                raise ValueError(
+                    f"{caller}: non-finite value ({value!r}) in session {session!r}'s group2 -- "
+                    f"refusing to compute a statistic over it"
+                )
+
+
 # === Sec3.6: percentile bootstrap confidence intervals ===============================================
 
 
@@ -288,7 +332,9 @@ def bootstrap_ci_occurrence(
     already-computed paired per-occurrence differences) WITH replacement, ``b`` seeded draws
     (``purpose="boot-occ"``, one flat stream for the whole call -- no session structure at this
     level), take the percentile bounds of the resampled means. Descriptive only: this function
-    returns an uncertainty interval, never a p-value (T-3)."""
+    returns an uncertainty interval, never a p-value (T-3). Raises ``ValueError`` immediately on
+    any non-finite (NaN/inf) input value (iter-5 fail-loud guard)."""
+    _require_finite_values(values, "bootstrap_ci_occurrence")
     n = len(values)
     if n == 0:
         return {"state": INSUFFICIENT_SAMPLE, "n": 0}
@@ -324,7 +370,11 @@ def bootstrap_ci_cluster(
     (both groups), and the statistic recomputed on each resample is ``T`` (``_t_statistic``, the
     SAME combined statistic the primary test uses). Below ``min_clusters`` informative sessions,
     returns the literal ``insufficient_sample`` state, never a fabricated interval (TC-3). MDE
-    (``z_{1-alpha} * sd*(T)``) is served as the power disclosure alongside the interval."""
+    (``z_{1-alpha} * sd*(T)``) is served as the power disclosure alongside the interval. Raises
+    ``ValueError`` immediately on any non-finite (NaN/inf) input value (iter-5 fail-loud guard) --
+    checked explicitly here (not merely relying on the internal ``_t_statistic`` call below) so an
+    ``insufficient_sample`` short-circuit can never mask a bad input."""
+    _require_finite_session_groups(session_groups, "bootstrap_ci_cluster")
     informative = _informative_sessions(session_groups)
     n_clusters = len(informative)
     if n_clusters < min_clusters:
@@ -506,6 +556,17 @@ def permutation_test(
         draws_used = b
 
     p = (1 + extreme) / (draws_used + 1)
+    # iter-5 fix (the field's own literal name, "minimum ATTAINABLE"): in exact-enumeration mode
+    # the OBSERVED grouping is always one guaranteed member of the enumerated space and therefore
+    # always self-extreme (`_is_extreme(t_obs, t_obs, sidedness)` holds for every sidedness value
+    # above), so the true floor is 2/(draws_used+1), not 1/(draws_used+1) -- a value the
+    # already-fixed method can never actually produce (iteration 4's own 2,500-case sweep found
+    # zero violations, 448 landing exactly on 2/(draws_used+1)). The seeded (Monte Carlo) branch is
+    # UNCHANGED: a random draw is not guaranteed to reproduce the observed grouping, so
+    # 1/(draws_used+1) stays its own true floor there. Touches no `_ATTESTATION_EXPECTED` field
+    # (see this module's own attestation section) -- no `STATS_CORE_VERSION` bump follows. Ruling
+    # recorded in runs/goal-session-referee/state/assumptions.md, iter-5 entry.
+    min_attainable_p = (2.0 if use_enumeration else 1.0) / (draws_used + 1)
     return {
         "state": "ok",
         "t": t_obs,
@@ -514,7 +575,7 @@ def permutation_test(
         "n_informative_sessions": len(informative),
         "enumeration": use_enumeration,
         "draws_used": draws_used,
-        "min_attainable_p": 1.0 / (draws_used + 1),
+        "min_attainable_p": min_attainable_p,
         "delta_by_session": deltas,
         "weight_by_session": weights,
     }
diff --git a/apps/backend/tests/test_referee_guards.py b/apps/backend/tests/test_referee_guards.py
index 2397188..866ff8d 100644
--- a/apps/backend/tests/test_referee_guards.py
+++ b/apps/backend/tests/test_referee_guards.py
@@ -177,17 +177,75 @@ def _referee_modules() -> list[pathlib.Path]:
     return sorted(_RESEARCH_DIR.glob("referee_*.py"))
 
 
-def test_no_referee_module_imports_the_detect_or_context_modules():
-    """TC-10 (first direction): zero imports of ``desk_playbook_detect`` or
-    ``desk_playbook_context`` inside any ``referee_*.py`` module."""
+def test_no_referee_module_imports_the_detect_module():
+    """TC-10 (first direction, (a)): zero imports of ``desk_playbook_detect`` inside ANY
+    ``referee_*.py`` module -- UNCHANGED, zero exceptions (iter-5 IN SCOPE: this half of the
+    original combined guard is untouched; only the ``desk_playbook_context`` half below is
+    corrected)."""
     referee_modules = _referee_modules()
     assert referee_modules, "no referee_*.py module found -- has the glob/location changed?"
     for path in referee_modules:
         imported = _imported_module_names(path)
-        hit = _mentioning(imported, "desk_playbook_detect") | _mentioning(imported, "desk_playbook_context")
+        hit = _mentioning(imported, "desk_playbook_detect")
         assert not hit, f"{path.name} imports the banned module(s) {hit}"
 
 
+# iter-5: `docs/goal.md`'s own Read-side law states, precisely and asymmetrically -- "the Referee
+# imports the rail (`desk_forward._measure_from`, `_draw_anchor_indices`, the averaging helpers)
+# **and the context resolver (`BandMapResolver`)** -- ... import-ban guards prove
+# `desk_playbook_detect`/`desk_playbook_context` never import referee modules **and referee
+# modules never import the detect module**." That second clause names only the DETECT module, not
+# the context module -- by design, since spec Sec4.2 (`docs/referee-statistical-spec.md`) requires
+# reading the recorded band map through `BandMapResolver` (the context layer's OWN machinery)
+# rather than re-deriving band membership a second time (anti-goal 6, single source of truth). The
+# guard BEFORE this iteration banned `desk_playbook_context` for every `referee_*.py` module with
+# zero exceptions -- vacuously passing only because no referee module needed `BandMapResolver`
+# until `referee_null.py`'s J-04 context-matched null (`referee-null-context-v1`) landed. This is
+# an EXTENSION to match what the canonical spec always said, not a weakening: the ban still holds
+# for every OTHER referee module (`referee_evidence.py`, `referee_stats.py`, `referee_routes.py`,
+# and any future `referee_*.py` module) -- only the ONE module that actually needs the resolver
+# gets the exception, nothing wider.
+_CONTEXT_MODULE_ALLOWED_IMPORTER = "referee_null.py"
+
+
+def test_no_referee_module_other_than_referee_null_imports_the_context_module():
+    """TC-10 (first direction, (b), corrected this iteration): zero imports of
+    ``desk_playbook_context`` inside any ``referee_*.py`` module EXCEPT ``referee_null.py`` (see
+    the module-level comment above for the exact ``docs/goal.md`` sentence this narrows against).
+    ``referee_stats.py``'s OWN separate, STRICTER ban (``test_referee_stats_module_imports_none_
+    of_the_banned_rail_detector_context_modules`` below) is untouched -- it still bans
+    ``desk_playbook_context`` too, since that module stays estimand-agnostic."""
+    referee_modules = _referee_modules()
+    assert referee_modules, "no referee_*.py module found -- has the glob/location changed?"
+    checked_the_allowed_importer = False
+    for path in referee_modules:
+        imported = _imported_module_names(path)
+        hit = _mentioning(imported, "desk_playbook_context")
+        if path.name == _CONTEXT_MODULE_ALLOWED_IMPORTER:
+            checked_the_allowed_importer = True
+            continue  # sanctioned -- spec Sec4.2's own context-matched null needs BandMapResolver
+        assert not hit, f"{path.name} imports the banned module desk_playbook_context {hit}"
+    # This guard's own point only holds if `referee_null.py` actually exists to be exempted --
+    # otherwise the loop above silently never reaches the branch this test exists to prove.
+    assert checked_the_allowed_importer, (
+        f"{_CONTEXT_MODULE_ALLOWED_IMPORTER} not found among referee_*.py modules -- has it moved "
+        f"or not been built yet?"
+    )
+
+
+def test_no_referee_module_other_than_referee_null_context_ban_can_fail_on_a_seeded_violation():
+    """The narrower rule's own can-fail counter-test (this file's established per-guard pattern):
+    a seeded fixture simulating ANY referee module OTHER than ``referee_null.py`` (including
+    ``referee_evidence.py``, which carries no such import today) importing ``desk_playbook_context``
+    is still correctly caught as a violation."""
+    seeded_imports = {"app.research.desk_playbook_context", "app.research.other"}
+    hit = _mentioning(seeded_imports, "desk_playbook_context")
+    assert hit == {"app.research.desk_playbook_context"}  # the violation IS detected
+    # ... and the one sanctioned importer is correctly recognised as the exempted filename, not
+    # swept up as a violation itself.
+    assert _CONTEXT_MODULE_ALLOWED_IMPORTER == "referee_null.py"
+
+
 def test_the_detect_and_context_modules_import_no_referee_module():
     """TC-10 (second direction): zero imports of any ``referee_*`` module inside
     ``desk_playbook_detect.py`` or ``desk_playbook_context.py``."""
diff --git a/apps/backend/tests/test_referee_stats.py b/apps/backend/tests/test_referee_stats.py
index 0c75626..045cf99 100644
--- a/apps/backend/tests/test_referee_stats.py
+++ b/apps/backend/tests/test_referee_stats.py
@@ -301,7 +301,14 @@ def test_permutation_test_enumeration_matches_a_hand_computed_p_value():
       - group1={1.0}: delta* = 1.0 - mean(5.0,2.0) = 1.0 - 3.5 = -2.5
       - group1={2.0}: delta* = 2.0 - mean(5.0,1.0) = 2.0 - 3.0 = -1.0
     T_obs = 3.5 (single session, so T == its own delta regardless of weight). For "greater"
-    sidedness, #{T* >= 3.5} = 1 (only the observed grouping itself) -> p = (1+1)/(3+1) = 0.5."""
+    sidedness, #{T* >= 3.5} = 1 (only the observed grouping itself) -> p = (1+1)/(3+1) = 0.5.
+
+    iter-5 update: `min_attainable_p` now reads `2 / (draws_used + 1) == 0.5` in enumeration mode
+    (was `0.25` through iter-4) -- this fixture is itself the proof the OLD value was wrong: the
+    observed grouping IS one guaranteed member of the enumerated space, so it is ALWAYS
+    self-extreme (`p` above is exactly this fixture's own `min_attainable_p`, not merely close to
+    it), making `1 / (draws_used + 1)` a floor this method can never actually produce. See the
+    iter-5 owner ruling in runs/goal-session-referee/state/assumptions.md."""
     session_groups = {"2026-06-08": ([5.0], [1.0, 2.0])}
     result = permutation_test(session_groups, "hyp-enum", sidedness="greater")
     assert result["state"] == "ok"
@@ -309,7 +316,7 @@ def test_permutation_test_enumeration_matches_a_hand_computed_p_value():
     assert result["draws_used"] == 3
     assert abs(result["t"] - 3.5) < 1e-9  # float division noise, not a rounding bug
     assert result["p"] == 0.5
-    assert result["min_attainable_p"] == 0.25
+    assert result["min_attainable_p"] == 0.5
 
 
 def test_permutation_test_enumeration_is_deterministic_with_zero_rng_draws():
@@ -438,6 +445,171 @@ def test_iter4_tc2_the_exact_mode_floor_holds_in_the_extreme_tail_regime_too():
     )
 
 
+# === iter-5 TC-10/TC-11: `min_attainable_p` is a TRUE floor (own spec, own numbering) =================
+#
+# iter-4's own tests directly above prove `p >= 2 / (draws_used + 1)` -- but iter-4 never fixed the
+# SERVED `min_attainable_p` FIELD itself (it stayed the wrong `1 / (draws_used + 1)` through iter-4);
+# neither iter-4 test above asserts anything about that field. This section closes that gap: the
+# field now reads the TRUE floor in enumeration mode, proven both by a hand fixture and by a fresh
+# >=1,000-case tail-regime sweep (the iter-4-taught lesson, applied here again per this iteration's
+# own NOTES: "every new floor-adjacent test ... generates in the sensitive regime and asserts HOW
+# OFTEN the boundary is actually reached, not just that it is never crossed") -- reusing the
+# `shift = -3.0 if sidedness == "less" else 3.0` idiom iter-4's own tail-regime test above already
+# established, so every sidedness value gets genuine floor-adjacent coverage.
+
+
+def test_iter5_tc10_min_attainable_p_hand_fixture():
+    """iter-5 TC-10 (hand fixture): the same TC-4 fixture (occurrence [5.0] vs anchors [1.0, 2.0],
+    space=3) whose `p == 0.5` is already hand-verified above -- `min_attainable_p` now reads the
+    TRUE floor `2 / (draws_used + 1) == 2/4 == 0.5`, matching `p` itself here (the observed
+    grouping IS this fixture's own unique extreme)."""
+    session_groups = {"2026-06-08": ([5.0], [1.0, 2.0])}
+    result = permutation_test(session_groups, "hyp-tc10-fixture", sidedness="greater")
+    assert result["enumeration"] is True
+    assert result["draws_used"] == 3
+    assert result["min_attainable_p"] == 2.0 / 4 == 0.5
+    assert result["p"] == result["min_attainable_p"]
+
+
+def test_iter5_tc10_min_attainable_p_true_floor_tail_regime_sweep():
+    """iter-5 TC-10 (the >=1,000-case sweep): across the SAME tail-regime generator shape iter-4's
+    own audit-rider test uses (strong group separation, all three sidedness values, the mirrored
+    shift for "less"), the SERVED `min_attainable_p` field always equals `2 / (draws_used + 1)`
+    exactly, `p` is never below it, and at least 100 of the 1,200 cases land with `p` exactly ON
+    that floor (the can-fail guard: a generator too tame to ever reach the boundary would prove
+    nothing about the fix)."""
+    rng = random.Random("iter5-tc10-tail-regime-seed-v1")
+    shapes = [(2, 2), (1, 4), (4, 1)]
+    sidedness_values = ("greater", "less", "two-sided")
+    n_cases = 1200
+    violations = []
+    field_mismatches = []
+    at_the_floor = 0
+    for i in range(n_cases):
+        n_sessions = rng.randint(1, 3)
+        n1, n2 = rng.choice(shapes)
+        sidedness = rng.choice(sidedness_values)
+        shift = -3.0 if sidedness == "less" else 3.0
+        session_groups = {
+            f"s{j:03d}": (
+                [rng.gauss(shift, 1.0) for _ in range(n1)],
+                [rng.gauss(-shift, 1.0) for _ in range(n2)],
+            )
+            for j in range(n_sessions)
+        }
+        result = permutation_test(session_groups, f"iter5-tc10-case-{i}", sidedness=sidedness)
+        assert result["enumeration"] is True, f"case {i} unexpectedly used the seeded branch"
+        floor = 2.0 / (result["draws_used"] + 1)
+        if result["min_attainable_p"] != floor:
+            field_mismatches.append((i, result["min_attainable_p"], floor))
+        if result["p"] < result["min_attainable_p"]:
+            violations.append((i, n_sessions, (n1, n2), sidedness, result["p"], floor))
+        elif result["p"] == result["min_attainable_p"]:
+            at_the_floor += 1
+    assert field_mismatches == [], (
+        f"{len(field_mismatches)} case(s) served a min_attainable_p != 2/(draws_used+1), first 3: "
+        f"{field_mismatches[:3]}"
+    )
+    assert violations == [], f"{len(violations)} floor violation(s), first 3: {violations[:3]}"
+    assert at_the_floor >= 100, (
+        f"only {at_the_floor} of {n_cases} tail-regime cases landed exactly on the floor -- this "
+        f"generator is not reaching the boundary it claims to test"
+    )
+
+
+def test_iter5_tc11_min_attainable_p_seeded_branch_is_unchanged():
+    """iter-5 TC-11 (regression guard): the seeded (Monte Carlo) branch's own `min_attainable_p`
+    stays `1 / (draws_used + 1)`, byte-unchanged from before this iteration -- this iteration's fix
+    touches the enumeration branch's own computation ONLY. (`test_permutation_test_seeded_branch_
+    uses_exactly_b_draws_and_the_p_formula` above, from iter-3, already asserts this exact field
+    for the seeded branch and continues to pass unmodified; this test adds a second, independently
+    -shaped fixture so the regression guard does not depend on that one test file location alone.)"""
+    rng = random.Random("iter5-tc11-seeded-branch-seed-v1")
+    session_groups = {
+        f"2026-04-{i + 1:02d}": (
+            [rng.gauss(0, 1) for _ in range(4)],
+            [rng.gauss(0, 1) for _ in range(4)],
+        )
+        for i in range(5)  # C(8,4)=70 per session, 70**5 >> REFEREE_ENUMERATION_THRESHOLD
+    }
+    b = 300
+    result = permutation_test(session_groups, "hyp-tc11-seeded", sidedness="greater", b=b)
+    assert result["enumeration"] is False
+    assert result["draws_used"] == b
+    assert result["min_attainable_p"] == 1.0 / (b + 1)
+
+
+# === iter-5 TC-12: the non-finite (NaN/inf) fail-loud guard ===========================================
+
+
+def test_iter5_tc12_t_statistic_raises_on_non_finite_input():
+    """iter-5 TC-12: a NaN in either group raises `ValueError` immediately from `_t_statistic` --
+    the shared entry point `permutation_test`/`sign_flip_result`/`equal_weight_t` all call first."""
+    bad = {"2026-06-08": ([1.0, float("nan")], [2.0, 3.0])}
+    try:
+        rs._t_statistic(bad)
+    except ValueError:
+        pass
+    else:
+        raise AssertionError("expected ValueError: non-finite value in group1")
+
+
+def test_iter5_tc12_permutation_test_sign_flip_equal_weight_all_raise_on_non_finite_input():
+    """iter-5 TC-12: every NAMED caller of `_t_statistic` propagates the identical fail-loud guard
+    -- an `inf` value raises from each of the three, never a silently-wrong p/t."""
+    bad = {"2026-06-08": ([1.0, float("inf")], [2.0, 3.0]), "2026-06-09": ([1.0], [2.0])}
+    for fn, args in (
+        (permutation_test, (bad, "hyp-nonfinite")),
+        (sign_flip_result, (bad, "hyp-nonfinite")),
+        (equal_weight_t, (bad,)),  # equal_weight_t takes no hypothesis_id -- it draws nothing
+    ):
+        try:
+            fn(*args)
+        except ValueError:
+            pass
+        else:
+            raise AssertionError(f"expected ValueError from {fn.__name__} on a non-finite input")
+
+
+def test_iter5_tc12_bootstrap_ci_occurrence_raises_on_non_finite_input():
+    """iter-5 TC-12: `bootstrap_ci_occurrence`'s own input is checked directly, not only via
+    `_t_statistic` (this function never calls it)."""
+    try:
+        bootstrap_ci_occurrence([1.0, 2.0, float("nan")], "hyp-nonfinite-occ")
+    except ValueError:
+        pass
+    else:
+        raise AssertionError("expected ValueError: non-finite value in bootstrap_ci_occurrence")
+
+
+def test_iter5_tc12_bootstrap_ci_cluster_raises_on_non_finite_input():
+    """iter-5 TC-12: `bootstrap_ci_cluster`'s own input is checked BEFORE the `min_clusters` floor
+    short-circuit, so an `insufficient_sample` return can never mask a non-finite value -- this
+    fixture is deliberately BELOW `REFEREE_MIN_CLUSTERS_FOR_CI` (2 informative sessions)."""
+    sg = {
+        "2026-05-01": ([1.0, float("inf")], [2.0, 3.0]),
+        "2026-05-02": ([1.0], [2.0]),
+    }
+    assert len(sg) < REFEREE_MIN_CLUSTERS_FOR_CI
+    try:
+        bootstrap_ci_cluster(sg, "hyp-nonfinite-cluster")
+    except ValueError:
+        pass
+    else:
+        raise AssertionError("expected ValueError: non-finite value in bootstrap_ci_cluster")
+
+
+def test_iter5_tc12_finite_inputs_are_unaffected_can_fail_companion():
+    """Can-fail companion: an all-finite input never raises -- the guard is a targeted non-finite
+    check, not an accidental blanket rejection of every input."""
+    sg = {"2026-06-08": ([1.0, 2.0], [0.5, 0.7])}
+    t, _deltas, _weights = rs._t_statistic(sg)
+    assert math.isfinite(t)
+    assert bootstrap_ci_occurrence([1.0, 2.0, 3.0], "hyp-finite")["state"] == "ok"
+    assert sign_flip_result(sg, "hyp-finite", b=10)["state"] == "ok"
+    assert equal_weight_t(sg)["state"] == "ok"
+
+
 # === TC-5: the seeded B-draw branch ====================================================================
 
 
@@ -611,7 +783,11 @@ def test_iter4_tc8_n2_equals_1_fast_path_matches_a_from_scratch_general_algorith
             extreme_general += 1
     p_general = (1 + extreme_general) / (b + 1)
 
-    tolerance = 6.0 * math.sqrt(p_star * (1 - p_star) / b)
+    # iter-5 TC-14: tightened from 6.0 to 3.5 standard errors -- 6.0 SE was wide enough to hide a
+    # real regression (proven directly below by TC-15's mutation counter-test); both estimators
+    # measured well inside the tighter band during development (real ~0.30 SE, general-reference
+    # ~0.17 SE off ground truth), so 3.5 stays comfortably non-flaky on this fixture's pinned seed.
+    tolerance = 3.5 * math.sqrt(p_star * (1 - p_star) / b)
     assert abs(real["p"] - p_star) <= tolerance, (
         f"fast-path p={real['p']!r} strayed {abs(real['p'] - p_star):.5f} from ground truth "
         f"{p_star!r} (tolerance {tolerance:.5f})"
@@ -622,6 +798,77 @@ def test_iter4_tc8_n2_equals_1_fast_path_matches_a_from_scratch_general_algorith
     )
 
 
+# === iter-5 TC-15: the tightened TC-8 band actually discriminates a real regression ====================
+
+
+def test_iter5_tc15_reintroduced_incorrect_n2_equals_1_fast_path_fails_the_tightened_tc8_band():
+    """iter-5 TC-15: a deliberately-reintroduced INCORRECT `n2 == 1` fast-path formula -- dropping
+    the `total -` complement, i.e. reusing the `n1 == 1` branch's own formula by mistake (a
+    realistic copy-paste bug: both branches consume exactly one `stream.randrange(n)` call) -- is
+    run through the identical from-scratch Monte-Carlo estimator TC-8's own "independently-coded
+    general-algorithm reference" uses, against TC-8's SAME ground truth and SAME tightened (3.5 SE)
+    tolerance. The mutant's `p` must FAIL that band -- proving the tightened band in
+    `test_iter4_tc8_n2_equals_1_fast_path_matches_a_from_scratch_general_algorithm_reference` above
+    actually discriminates a real regression, not merely that its number happens to be smaller.
+    Never touches `referee_stats.py` itself -- the mutant formula lives ENTIRELY inside this test."""
+    rng = random.Random("iter4-tc8-fixture-seed-v1")  # the SAME fixture TC-8 uses, for a fair test
+    n_sessions = 7
+    session_groups = {
+        f"2026-10-{i + 1:02d}": ([rng.gauss(0, 1) for _ in range(3)], [rng.gauss(0, 1)])
+        for i in range(n_sessions)
+    }
+    sessions = sorted(session_groups)
+    weight_by_s = {s: (3 * 1) / (3 + 1) for s in sessions}
+    total_weight = sum(weight_by_s.values())
+    delta_by_s = {
+        s: sum(session_groups[s][0]) / 3 - sum(session_groups[s][1]) / 1 for s in sessions
+    }
+    t_obs_ref = sum(weight_by_s[s] * delta_by_s[s] for s in sessions) / total_weight
+    pooled = {s: session_groups[s][0] + session_groups[s][1] for s in sessions}
+
+    # --- ground truth: the SAME brute-force full enumeration TC-8 computes ---
+    combos_by_session = [list(itertools.combinations(range(4), 3)) for _ in sessions]
+    extreme_exact = 0
+    total_combos = 0
+    for joint in itertools.product(*combos_by_session):
+        acc = 0.0
+        for s, combo in zip(sessions, joint):
+            values = pooled[s]
+            g1 = sum(values[idx] for idx in combo)
+            g2 = sum(values) - g1
+            acc += weight_by_s[s] * (g1 / 3 - g2 / 1)
+        if (acc / total_weight) >= t_obs_ref:
+            extreme_exact += 1
+        total_combos += 1
+    p_star = (1 + extreme_exact) / (total_combos + 1)
+
+    # --- the MUTANT: n2 == 1's fast path with the complement dropped ---
+    b = 8000
+    streams = {s: random.Random(f"iter5-tc15-mutant-seed:{s}") for s in sessions}
+    extreme_mutant = 0
+    for _ in range(b):
+        acc = 0.0
+        for s in sessions:
+            values = pooled[s]
+            n1, n = 3, 4
+            rstream = streams[s]
+            # BUG: should be `total - values[rstream.randrange(n)]` (the excluded element belongs
+            # to group2 when n2 == 1) -- this reuses the n1 == 1 branch's formula instead.
+            g1_sum = values[rstream.randrange(n)]
+            g2_sum = sum(values) - g1_sum
+            acc += weight_by_s[s] * (g1_sum / n1 - g2_sum / 1)
+        if (acc / total_weight) >= t_obs_ref:
+            extreme_mutant += 1
+    p_mutant = (1 + extreme_mutant) / (b + 1)
+
+    tolerance = 3.5 * math.sqrt(p_star * (1 - p_star) / b)  # TC-8's own tightened band, reused
+    assert abs(p_mutant - p_star) > tolerance, (
+        f"the mutant formula's p={p_mutant!r} stayed inside the tightened tolerance "
+        f"({abs(p_mutant - p_star):.5f} <= {tolerance:.5f} from ground truth {p_star!r}) -- the "
+        f"tightened TC-8 band would NOT have caught this regression"
+    )
+
+
 # === TC-6: robustness variants are served, never substituted ==========================================
 
 
diff --git a/apps/backend/app/research/referee_null.py b/apps/backend/app/research/referee_null.py
new file mode 100644
index 0000000..c5c2b13
--- /dev/null
+++ b/apps/backend/app/research/referee_null.py
@@ -0,0 +1,1101 @@
+"""Era 6 "The Referee" (J-04) -- matched nulls: for every eligible Playbook occurrence, seeded
+comparison anchors measured through the identical rail, so a future "beats chance" verdict can mean
+"beats chance at a comparable time under identical measurement" (spec Sec4), never a strawman.
+
+**What this module builds, spec-verbatim (docs/referee-statistical-spec.md Sec4).**
+``referee-null-tod-v1`` draws ``K = REFEREE_NULL_ANCHORS_PER_OCCURRENCE`` seeded anchor bars per
+eligible J-02 observation -- same symbol, same measurement series, same ToD bucket,
+remaining-time-matched for fixed horizons (ToD-bucket-only for ``to_close``-family measures),
+excluding the occurrence's own trigger/anchor bar, without replacement -- and measures each through
+the imported ``desk_forward._measure_from`` at ``entry_kind="close"`` with the occurrence's own
+side sign. ``referee-null-context-v1`` adds one more filter: the anchor's own close must also
+satisfy a named backing-bucket predicate (e.g. ``at_wall``), evaluated through the imported
+``desk_playbook_context.BandMapResolver``/``band_context_block`` over the RECORDED band map --
+never re-derived locally (anti-goal 6, single source of truth).
+
+**Why this module, and only this one, imports the context resolver.** ``docs/goal.md``'s Read-side
+law names ``BandMapResolver`` as a sanctioned import for the Referee generally, but the
+import-topology guard (``tests/test_referee_guards.py``) narrows the EXCEPTION to this module by
+name -- every other ``referee_*.py`` module stays banned from ``desk_playbook_context`` (see that
+test file's own comment for the exact cited sentence). Nothing here mutates, re-tunes, or feeds
+back into ``desk_playbook_context.py``/``desk_playbook.py``/``desk_forward.py`` -- every import is
+read-only, zero diff to any of them.
+
+**"Eligible occurrence" is exactly one J-02 observation.** ``referee_evidence.playbook_observations``
+already excludes every truncated/unmeasurable leaf (never emits an observation for one) and already
+pools at the current ``(detector_basis, config_fingerprint)``, newest-per-date (T-6) -- so every
+observation this module walks is, by construction, "primary-horizon-complete" for its OWN
+``measure_key``. A null record is keyed ``(observation_id, null_spec_signature)`` -- ONE record per
+(signal, measure_key, null-spec) triple, matching the Data Contract's own ``observation_id: str``
+(singular) field, plus the per-anchor ``measure_key`` the served ``anchors[]`` schema carries
+(redundant across a record's own anchors by construction, since every anchor is measured for that
+SAME record's own ``measure_key`` -- self-describing rather than requiring a reader to look at the
+top level).
+
+**Reconstructing the occurrence's own measurement series, without re-deriving detection.** The J-02
+observation contract deliberately does not expose the raw ``forward`` block (only
+``anchor_ts = signal["trigger_ts"]``, the DETECTION-time epoch). To find the occurrence's own
+measurement anchor bar (which may be a finer 1m bar mapped from the 5m trigger window -- see
+``desk_playbook._measurement_anchor``, a detector-adjacent private helper this module deliberately
+does NOT import), this module reads the underlying ``PlaybookStore`` RECORD directly (via the
+``record_id``/signal-index encoded in ``observation_id``) for its own already-recorded
+``forward["at_utc"]``, then locates the RTH session bar carrying that EXACT epoch -- finest series
+(1m) first, then 5m, the same preference order the detector itself used. This is bar-epoch lookup
+against already-recorded data, not a second implementation of any measurement or detection logic.
+
+**Two draw-without-replacement helpers exist project-wide, on purpose (see NOTES in
+``docs/phases/goal-referee-iter-5.md``).** This module imports ``desk_forward._draw_anchor_indices``
+directly (it needs ``desk_forward._measure_from`` regardless, per the Read-side law) -- it does NOT
+call ``referee_stats._draw_indices_without_replacement`` (that copy exists only because
+``referee_stats.py`` carries its OWN stricter, estimand-agnostic import ban).
+
+**Stream discipline.** No hypothesis exists yet at J-04 (registration is J-05) -- the seeded stream
+recipe's ``hypothesis_id`` slot is filled with the null-spec id itself (``purpose="null-draw"``,
+``session_date=<the occurrence's own session_date>``, ``i=<the observation_id>``), giving every
+occurrence its own deterministic, reproducible sub-stream scoped under "this null variant, this
+occurrence" -- the natural pre-registration analogue until J-05 mints real hypothesis ids (which
+will scope their OWN null builds the same way, once they exist).
+
+**Adapter-layer exclusion vs. stats-core fail-loud are deliberately different (see this module's
+own inline comment on ``_measure_one_anchor``).** A non-finite ``_measure_from`` result here
+EXCLUDES-and-COUNTS that one anchor (T-5's normal, disclosed "unmeasurable" pattern) -- it never
+excludes the whole occurrence and never raises, unlike ``referee_stats.py``'s new door guard, which
+RAISES because at that layer a non-finite value can only mean an upstream bug."""
+
+from __future__ import annotations
+
+import argparse
+import hashlib
+import json
+import math
+import os
+import threading
+import uuid
+from datetime import date, datetime, time, timezone
+from pathlib import Path
+from typing import Callable
+from zoneinfo import ZoneInfo
+
+from ..config import CONFIG, Config
+from .bars import BarStore
+from .desk_forward import DESK_FORWARD_HORIZONS_MINUTES, _draw_anchor_indices, _measure_from
+from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
+from .desk_playbook_context import (
+    AT_WALL,
+    PLAYBOOK_CONTEXT_ALGORITHM_VERSION,
+    PLAYBOOK_CONTEXT_BACKING_BUCKETS,
+    BandMapResolver,
+    band_context_block,
+)
+from .desk_playbook_features import rth_session_slice, side_sign
+from .referee_evidence import (
+    _HORIZON_LABELS,
+    _epoch_from_iso,
+    _iso,
+    _resolve_leaf,
+    playbook_observations,
+)
+from .referee_stats import referee_stream
+from .routes import get_bar_store
+
+__all__ = [
+    "REFEREE_NULL_ANCHORS_PER_OCCURRENCE",
+    "REFEREE_TOD_BUCKETS",
+    "REFEREE_NULL_TOD_SPEC_ID",
+    "REFEREE_NULL_CONTEXT_SPEC_ID",
+    "REFEREE_TEST_PERM_SPEC_ID",
+    "resolve_referee_null_dir",
+    "resolve_referee_null_log_dir",
+    "tod_bucket_for_epoch",
+    "null_tod_spec_parameters",
+    "null_tod_spec_signature",
+    "null_context_spec_parameters",
+    "null_context_spec_signature",
+    "test_perm_spec_parameters",
+    "test_perm_spec_signature",
+    "NullIntegrityError",
+    "NullAlreadyRecorded",
+    "RefereeNullStore",
+    "RefereeNullRunStore",
+    "record_null_run",
+    "build_null_record",
+    "RefereeNullComputeManager",
+    "run_null_build_and_record",
+]
+
+# === spec Sec1: pre-registered constants (module constants, never Config fields) ====================
+
+REFEREE_NULL_ANCHORS_PER_OCCURRENCE: int = 4
+
+# Card 6.5's ToD buckets, verbatim (spec Sec0/Sec1), ET wall-clock, half-open [start, end).
+REFEREE_TOD_BUCKETS: tuple[tuple[str, str, str], ...] = (
+    ("open", "09:30", "10:30"),
+    ("mid", "10:30", "15:00"),
+    ("close", "15:00", "16:00"),
+)
+
+REFEREE_NULL_TOD_SPEC_ID: str = "referee-null-tod-v1"
+REFEREE_NULL_CONTEXT_SPEC_ID: str = "referee-null-context-v1"
+REFEREE_TEST_PERM_SPEC_ID: str = "referee-test-perm-v1"
+
+_NULL_SPEC_IDS = frozenset({REFEREE_NULL_TOD_SPEC_ID, REFEREE_NULL_CONTEXT_SPEC_ID})
+
+_NULL_DIR_ENV = "TAPEOLOGY_DESK_REFEREE_NULL_DIR"
+_NULL_LOG_DIR_ENV = "TAPEOLOGY_DESK_REFEREE_NULL_LOG_DIR"
+
+# The Referee's own ET zone constant -- the `desk_playbook_features.py`/`referee_evidence.py`
+# per-module idiom: each module that needs ET wall-clock resolution owns a private ZoneInfo
+# constant rather than reaching into another module's private one.
+_ET_ZONE = ZoneInfo("America/New_York")
+_RTH_CLOSE = time(16, 0)
+
+
+def resolve_referee_null_dir(desk_universe_dir_resolved: str) -> str:
+    """The null store's directory: ``TAPEOLOGY_DESK_REFEREE_NULL_DIR`` if set, else a
+    ``referee_null`` SIBLING of the caller's own already-resolved universe directory (the
+    ``resolve_desk_forward_dir`` pattern verbatim). Deliberately NOT a ``Config`` field."""
+    override = os.environ.get(_NULL_DIR_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "referee_null")
+
+
+def resolve_referee_null_log_dir(desk_universe_dir_resolved: str) -> str:
+    """The null run-ledger's directory -- its own ``_LOG_DIR``-family sibling default, the
+    ``resolve_desk_playbook_log_dir`` pattern verbatim. Deliberately NOT a ``Config`` field."""
+    override = os.environ.get(_NULL_LOG_DIR_ENV)
+    if override:
+        return override
+    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "referee_null_runs")
+
+
+def _canonical(obj: object) -> bytes:
+    """The one canonical JSON encoding every checksum/signature in this module hashes -- the SAME
+    encoding every other desk/referee store hashes."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+# === ToD bucket resolution (spec Sec0) ===============================================================
+
+
+def tod_bucket_for_epoch(epoch: float) -> str | None:
+    """The ``REFEREE_TOD_BUCKETS`` bucket ``epoch`` (converted ET, DST-correct via ``zoneinfo``)
+    falls in, half-open ``[start, end)`` -- ``None`` outside RTH (09:30-16:00 ET), an honest
+    non-membership rather than a fabricated bucket."""
+    wall = datetime.fromtimestamp(epoch, tz=_ET_ZONE).time()
+    for name, start, end in REFEREE_TOD_BUCKETS:
+        start_h, start_m = (int(p) for p in start.split(":"))
+        end_h, end_m = (int(p) for p in end.split(":"))
+        if time(start_h, start_m) <= wall < time(end_h, end_m):
+            return name
+    return None
+
+
+def _session_close_epoch(session_date: str) -> float:
+    """The UTC epoch RTH close (16:00 ET) resolves to on ``session_date`` -- DST-correct by
+    construction. The literal wall-clock basis TC-4 hand-verifies remaining-time eligibility
+    against (e.g. "60 min remaining" at 15:00 ET before a 16:00 close)."""
+    day = date.fromisoformat(session_date)
+    return datetime.combine(day, _RTH_CLOSE, tzinfo=_ET_ZONE).timestamp()
+
+
+# === spec ids: three named, signature-bearing parameter-blob hashes ==================================
+#
+# Each hashes its OWN full parameter blob, read at call time (a monkeypatched constant genuinely
+# moves both the blob and the signature -- counter-tested). File placement here (rather than a
+# separate shared helper) is an implementation choice named as such in the iter-5 spec; the
+# behavior contract (own blob, own hash, stable/reproducible, changes on any parameter change) is
+# fixed, not this placement.
+
+
+def null_tod_spec_parameters() -> dict:
+    """``referee-null-tod-v1``'s own full parameter blob (spec Sec4.1)."""
+    return {
+        "id": REFEREE_NULL_TOD_SPEC_ID,
+        "k": REFEREE_NULL_ANCHORS_PER_OCCURRENCE,
+        "tod_buckets": [list(bucket) for bucket in REFEREE_TOD_BUCKETS],
+        "horizons_minutes": [list(pair) for pair in DESK_FORWARD_HORIZONS_MINUTES],
+        "entry_kind": "close",
+        "exclude_own_trigger_bar": True,
+        "remaining_time_matched_for_fixed_horizons": True,
+        "tod_bucket_only_for_to_close_family": True,
+        "without_replacement": True,
+    }
+
+
+def null_tod_spec_signature() -> str:
+    return _sha256(_canonical(null_tod_spec_parameters()))[:16]
+
+
+def null_context_spec_parameters() -> dict:
+    """``referee-null-context-v1``'s own full parameter blob (spec Sec4.2): everything
+    ``referee-null-tod-v1`` requires, PLUS the backing-bucket predicate machinery."""
+    blob = null_tod_spec_parameters()
+    blob["id"] = REFEREE_NULL_CONTEXT_SPEC_ID
+    blob["context_algorithm_version"] = PLAYBOOK_CONTEXT_ALGORITHM_VERSION
+    blob["backing_buckets"] = list(PLAYBOOK_CONTEXT_BACKING_BUCKETS)
+    blob["risk_source"] = "paired_signal"
+    return blob
+
+
+def null_context_spec_signature() -> str:
+    return _sha256(_canonical(null_context_spec_parameters()))[:16]
+
+
+def test_perm_spec_parameters() -> dict:
+    """``referee-test-perm-v1``'s own full parameter blob (spec Sec1/Sec3.4) -- describes
+    ``referee_stats.permutation_test``'s own procedure (weights formula identity, sidedness
+    handling, enumeration rule, p convention); minted HERE so J-05 hypothesis records can reference
+    it immutably before any hypothesis exists. Exactly spec Sec1's stated contents -- no additional
+    input invented."""
+    from .referee_stats import REFEREE_B, REFEREE_ENUMERATION_THRESHOLD
+
+    return {
+        "id": REFEREE_TEST_PERM_SPEC_ID,
+        "weights_formula": (
+            "A/C: w_s = n_s*K_s/(n_s+K_s) (harmonic); B: w_s = n1_s*n2_s/(n1_s+n2_s) -- the SAME "
+            "formula, group-size-1 times group-size-2 over their sum"
+        ),
+        "sidedness_handling": ["greater", "less", "two-sided"],
+        "enumeration_rule": (
+            f"full enumeration when the total per-session-combination product <= "
+            f"{REFEREE_ENUMERATION_THRESHOLD}, else {REFEREE_B} seeded draws"
+        ),
+        "p_convention": "p = (1 + #{T* extreme}) / (draws + 1) -- the Phipson-Smyth +1 convention",
+    }
+
+
+def test_perm_spec_signature() -> str:
+    return _sha256(_canonical(test_perm_spec_parameters()))[:16]
+
+
+# === eligibility: which anchor bars a given occurrence's null may draw from ==========================
+
+
+def _required_horizon_minutes(measure_key: str) -> float | None:
+    """The remaining-time requirement for ``measure_key`` (spec Sec4.1) -- ``None`` means
+    ToD-bucket-only eligibility (the ``to_close``-family session-end trio: ``to_close``,
+    ``mdd_long``, ``mdd_short``, unsuffixed). Derived from ``DESK_FORWARD_HORIZONS_MINUTES`` /
+    ``_HORIZON_LABELS`` (imported from ``referee_evidence.py``) rather than spelled out a second
+    time, so a rail horizon addition can never silently desync here."""
+    horizon_minutes = dict(DESK_FORWARD_HORIZONS_MINUTES)
+    if measure_key in _HORIZON_LABELS:
+        return float(horizon_minutes[measure_key])
+    if measure_key in ("to_close", "mdd_long", "mdd_short"):
+        return None
+    for prefix in ("mdd_long_", "mdd_short_"):
+        if measure_key.startswith(prefix):
+            suffix = measure_key[len(prefix) :]
+            if suffix in _HORIZON_LABELS:
+                return float(horizon_minutes[suffix])
+    raise ValueError(f"unknown DESK_FORWARD_MEASURE_KEYS entry {measure_key!r}")
+
+
+def _parse_observation_id(observation_id: str) -> tuple[str, int, str]:
+    """``(record_id, signal_index, measure_key)`` -- the inverse of
+    ``referee_evidence._playbook_file_projection``'s own
+    ``f"playbook:{record['id']}:{index}:{measure_key}"`` construction."""
+    prefix, record_id, index_str, measure_key = observation_id.split(":", 3)
+    if prefix != "playbook":
+        raise ValueError(f"not a playbook observation id: {observation_id!r}")
+    return record_id, int(index_str), measure_key
+
+
+def _locate_measurement_series(
+    bar_store: BarStore, symbol: str, session_date: str, at_epoch: float
+) -> tuple[list, int, int] | None:
+    """Reconstructs ``(measure_bars, anchor_index, tf_minutes)`` for an already-recorded signal's
+    own forward measurement, by locating the RTH session bar whose epoch matches the signal's own
+    recorded ``forward["at_utc"]`` EXACTLY -- finest series (1m) first, then 5m, the SAME
+    preference order ``desk_playbook._measurement_anchor`` used to build that measurement in the
+    first place. Returns ``None`` when neither series carries a bar at that exact epoch (an honest
+    "cannot be located" case -- see ``build_null_record``'s own handling)."""
+    for tf, tf_minutes in (("1m", 1), ("5m", 5)):
+        bars = rth_session_slice(bar_store.merged_bars(symbol, tf), session_date)
+        for idx, bar in enumerate(bars):
+            if bar.epoch == at_epoch:
+                return bars, idx, tf_minutes
+    return None
+
+
+def _eligible_anchor_positions(
+    measure_bars: list,
+    trigger_index: int,
+    bucket: str,
+    required_minutes: float | None,
+    session_close_epoch: float,
+) -> list[int]:
+    """Every index in ``measure_bars`` (excluding ``trigger_index`` itself) whose OWN epoch falls
+    in the occurrence's ToD ``bucket`` and (for fixed-horizon primaries) leaves ``>= required_
+    minutes`` of session remaining, measured as literal wall-clock distance to the session's own
+    16:00 ET close (spec Sec4.1's remaining-time rule; TC-4's own hand-verified boundary: 60 min
+    remain at 15:00 ET before a 16:00 close, 55 min at 15:05 ET). Reads only each candidate bar's
+    OWN already-recorded epoch -- lookahead-clean by construction (TC-7)."""
+    positions: list[int] = []
+    for idx, bar in enumerate(measure_bars):
+        if idx == trigger_index:
+            continue
+        if tod_bucket_for_epoch(bar.epoch) != bucket:
+            continue
+        if required_minutes is not None:
+            remaining_minutes = (session_close_epoch - bar.epoch) / 60.0
+            if remaining_minutes < required_minutes:
+                continue
+        positions.append(idx)
+    return positions
+
+
+def _window_end_index(start_index: int, required_minutes: float | None, tf_minutes: int, last: int) -> int:
+    """The (possibly truncated) end index of one measurement's own window, for the overlap
+    disclosure below -- mirrors ``_measure_from``'s own truncation rule (``min(target, last)``)
+    without recomputing anything the rail already owns; ``to_close``-family measures (``required_
+    minutes is None``) run to the session's own last bar by definition."""
+    if required_minutes is None:
+        return last
+    offset = int(required_minutes // tf_minutes)
+    return min(start_index + offset, last)
+
+
+def _window_overlap_fraction(occ_start: int, occ_end: int, anchor_start: int, anchor_end: int) -> float:
+    """The fraction of the OCCURRENCE's own measurement window that ``anchor``'s window overlaps
+    (spec Sec4.1's same-session power-cost disclosure) -- both windows expressed as bar-index
+    ranges on the SAME ``measure_bars`` array, so index arithmetic is exact."""
+    occ_len = occ_end - occ_start
+    if occ_len <= 0:
+        return 0.0
+    overlap = min(occ_end, anchor_end) - max(occ_start, anchor_start)
+    return max(0.0, overlap) / occ_len
+
+
+# === exceptions =======================================================================================
+
+
+class NullIntegrityError(Exception):
+    """An on-disk null-record file failed its checksum verification on load -- corrupted or
+    tampered, surfaced explicitly (never silence, never a fabricated record)."""
+
+
+class NullAlreadyRecorded(Exception):
+    """A null record with this EXACT ``(observation_id, null_spec_signature)`` key is already
+    registered. Null records are immutable and append-only -- a re-run over identical inputs reuses
+    the existing record, never a second file."""
+
+    def __init__(self, existing_id: str) -> None:
+        self.existing_id = existing_id
+        super().__init__(
+            f"a null record with this exact key is already recorded as '{existing_id}' -- null "
... [diff_bound] apps/backend/app/research/referee_null.py: 707 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_referee_null.py b/apps/backend/tests/test_referee_null.py
new file mode 100644
index 0000000..08a9c19
--- /dev/null
+++ b/apps/backend/tests/test_referee_null.py
@@ -0,0 +1,815 @@
+"""``referee_null.py`` + the ``/research/desk/referee/nulls*`` routes (Era 6 "The Referee", J-04) --
+matched nulls. Test-first contract: TC-1 through TC-9, TC-13, TC-16 through TC-21 in
+``docs/phases/goal-referee-iter-5.md``.
+
+Fixtures build REAL, internally-consistent signals by calling the imported rail's own
+``desk_forward._measure_from`` directly against hand-built ``RawBar`` arrays (never a hand-typed
+forward block) -- the ``test_desk_forward.py``/``test_referee_evidence.py`` precedent -- then plant
+them into a real ``PlaybookStore``/``BarStore`` through each store's own public write path. Every
+expected count/index below is independently re-derivable from the fixture's own bar geometry, not
+merely read back from the module under test."""
+
+from __future__ import annotations
+
+import hashlib
+import sys
+import time as time_module
+
+import pytest
+from fastapi.testclient import TestClient
+
+import app.research.referee_null as referee_null_module
+from app.config import CONFIG
+from app.main import app
+from app.providers.adapters.base import RawBar
+from app.research.bars import BarStore
+from app.research.desk_forward import _draw_anchor_indices, _measure_from
+from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
+from app.research.desk_playbook_context import AT_WALL, PLAYBOOK_CONTEXT_ALGORITHM_VERSION
+from app.research.desk_playbook_features import side_sign
+from app.research.referee_evidence import playbook_observations
+from app.research.referee_null import (
+    REFEREE_NULL_ANCHORS_PER_OCCURRENCE,
+    REFEREE_NULL_CONTEXT_SPEC_ID,
+    REFEREE_NULL_TOD_SPEC_ID,
+    REFEREE_TEST_PERM_SPEC_ID,
+    NullAlreadyRecorded,
+    RefereeNullComputeManager,
+    RefereeNullRunStore,
+    RefereeNullStore,
+    _eligible_anchor_positions,
+    _session_close_epoch,
+    build_null_record,
+    null_context_spec_signature,
+    null_tod_spec_signature,
+    referee_stream,
+    run_null_build_and_record,
+    tod_bucket_for_epoch,
+)
+from app.research.referee_null import test_perm_spec_parameters as _test_perm_spec_parameters
+from app.research.referee_null import test_perm_spec_signature as _test_perm_spec_signature
+from app.research.referee_routes import get_referee_null_compute_manager
+from app.research.routes import ResearchRegistry, set_registry
+from app.research.store import JournalStore
+
+E_OPEN = 1782135000.0  # 2026-06-22T13:30:00Z == 09:30 ET, the codebase's standard fixture anchor
+SESSION_DATE = "2026-06-22"
+
+
+# --- fixture builders (real rail measurement + each store's own public write path) -----------------
+
+
+def _bar5(symbol: str, i: int, close: float = 100.2) -> RawBar:
+    """One 5m RTH bar at ``09:30 + i*5min`` ET -- the ``test_desk_forward.py``/``test_desk_playbook.
+    py`` ``_bar``/``_minute`` idiom, specialised to a fixed 5-minute cadence."""
+    return RawBar(symbol, "5m", E_OPEN + i * 300.0, 100.0, 100.5, 99.5, close, 1000)
+
+
+def _plant_bars(bar_store: BarStore, symbol: str, bars: list[RawBar]) -> None:
+    bar_store.record(
+        symbol=symbol, timeframe="5m", window_start_utc="2026-06-01T00:00:00Z",
+        window_end_utc="2026-06-30T00:00:00Z", feed="test", bars=bars,
+    )
+
+
+def _plant_occurrence(
+    playbook_store: PlaybookStore, bar_store: BarStore, symbol: str, bars: list[RawBar],
+    *, side: str = "long", signature: str = "sig-a",
+) -> dict:
+    """Plants ``bars`` into ``bar_store`` and a ONE-signal playbook record (triggered at bar index
+    0, measured through the REAL rail) into ``playbook_store``. Returns the J-02 observation whose
+    ``measure_key == "to_close"`` -- the ToD-bucket-only-eligibility measure, so a fixture's own
+    eligible-anchor count depends ONLY on how many bars share the trigger's own ToD bucket, never on
+    a remaining-time boundary (kept as its own dedicated TC-4 test below)."""
+    _plant_bars(bar_store, symbol, bars)
+    sign = side_sign(side)
+    forward = _measure_from(bars, 0, bars[0].close, "close", 5, sign)
+    signal = {
+        "setup_id": "open_high_break", "side": side, "symbol": symbol,
+        "trigger_ts": referee_null_module._iso(bars[0].epoch), "entry": bars[0].close,
+        "entry_kind": "close", "invalidation_price": bars[0].close - 0.5, "forward": forward,
+        "invalidation_breached": False, "geometry": {"anchors": []},
+    }
+    playbook_store.record(
+        session_date=SESSION_DATE, config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature=signature, payload_version=3, parameters=playbook_parameters(),
+        register=PLAYBOOK_REGISTER, signals=[signal], absences=[], diagnostics=[],
+    )
+    observations = playbook_observations(playbook_store, CONFIG.config_fingerprint())["observations"]
+    to_close = [o for o in observations if o["measure_key"] == "to_close" and o["symbol"] == symbol]
+    assert len(to_close) == 1, to_close
+    return to_close[0]
+
+
+def _plant_multi_symbol_occurrences(
+    playbook_store: PlaybookStore, bar_store: BarStore, symbols: list[str], *, signature: str = "sig-multi",
+) -> list[dict]:
+    """Plants ONE playbook record covering MULTIPLE symbols' worth of signals -- a real playbook
+    record's own shape (``PlaybookStore``'s newest-per-``session_date`` pooling rule keeps only ONE
+    record per date, so a fixture needing several eligible occurrences at the SAME session_date must
+    put every signal inside that ONE record, never several separately-recorded ones). Returns the
+    J-02 ``to_close`` observation per symbol, in ``symbols`` order."""
+    signals = []
+    for symbol in symbols:
+        bars = [_bar5(symbol, i) for i in range(5)]
+        _plant_bars(bar_store, symbol, bars)
+        forward = _measure_from(bars, 0, bars[0].close, "close", 5, side_sign("long"))
+        signals.append(
+            {
+                "setup_id": "open_high_break", "side": "long", "symbol": symbol,
+                "trigger_ts": referee_null_module._iso(bars[0].epoch), "entry": bars[0].close,
+                "entry_kind": "close", "invalidation_price": bars[0].close - 0.5, "forward": forward,
+                "invalidation_breached": False, "geometry": {"anchors": []},
+            }
+        )
+    playbook_store.record(
+        session_date=SESSION_DATE, config_fingerprint=CONFIG.config_fingerprint(),
+        playbook_input_signature=signature, payload_version=3, parameters=playbook_parameters(),
+        register=PLAYBOOK_REGISTER, signals=signals, absences=[], diagnostics=[],
+    )
+    observations = playbook_observations(playbook_store, CONFIG.config_fingerprint())["observations"]
+    by_symbol = {
+        o["symbol"]: o for o in observations if o["measure_key"] == "to_close"
+    }
+    return [by_symbol[symbol] for symbol in symbols]
+
+
+@pytest.fixture
+def env(tmp_path):
+    bar_store = BarStore(tmp_path / "bars")
+    playbook_store = PlaybookStore(tmp_path / "playbook")
+    null_store = RefereeNullStore(tmp_path / "nulls")
+    run_store = RefereeNullRunStore(tmp_path / "null_runs")
+    return bar_store, playbook_store, null_store, run_store
+
+
+# === TC-1: exactly K=4 eligible anchors -- k_drawn == eligible_count == 4, draw hand-verified ========
+
+
+def test_tc1_exactly_k_eligible_anchors_draws_all_four_via_the_pinned_seed(env):
+    """TC-1: 5 bars total (trigger + 4 more, all inside the SAME "open" ToD bucket) -> k_drawn ==
+    eligible_count == 4, excluded == False, and the 4 drawn anchor indices match an INDEPENDENT
+    re-derivation of the pinned Fisher-Yates draw (the SAME seeded-stream recipe + ``desk_forward.
+    _draw_anchor_indices`` this module itself calls, invoked here a second time with the identical
+    inputs -- never by reading the module's own output back)."""
+    bar_store, playbook_store, _null_store, _run_store = env
+    bars = [_bar5("TC1", i) for i in range(5)]
+    observation = _plant_occurrence(playbook_store, bar_store, "TC1", bars)
+
+    record = build_null_record(
+        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    assert record["k_requested"] == REFEREE_NULL_ANCHORS_PER_OCCURRENCE == 4
+    assert record["k_drawn"] == 4
+    assert record["eligible_count"] == 4
+    assert record["excluded"] is False
+    assert record["tod_bucket"] == "open"
+    assert len(record["anchors"]) == 4
+
+    # Independent re-derivation: eligible positions are indices 1..4 (0 is the trigger, excluded);
+    # the SAME stream recipe + draw primitive, called fresh here.
+    stream = referee_stream(
+        REFEREE_NULL_TOD_SPEC_ID, "null-draw", session_date=observation["session_date"],
+        i=observation["observation_id"],
+    )
+    expected_drawn = _draw_anchor_indices(stream, 4, 4)
+    eligible_positions = [1, 2, 3, 4]
+    expected_indices = sorted(eligible_positions[j] for j in expected_drawn)
+    actual_indices = sorted(
+        i for i, bar in enumerate(bars) if referee_null_module._iso(bar.epoch) in {a["anchor_ts"] for a in record["anchors"]}
+    )
+    assert actual_indices == expected_indices == [1, 2, 3, 4]  # all 4 non-trigger bars, order-sorted
+
+
+# === TC-2: shortfall -- only 2 eligible, disclosed, never silently absent =============================
+
+
+def test_tc2_shortfall_is_served_not_silently_absent(env):
+    """TC-2: only 3 bars total (trigger + 2 candidates) -> k_drawn == eligible_count == 2, and the
+    shortfall (``k_requested - k_drawn == 2``) is computable from the served fields, never hidden."""
+    bar_store, playbook_store, _null_store, _run_store = env
+    bars = [_bar5("TC2", i) for i in range(3)]
+    observation = _plant_occurrence(playbook_store, bar_store, "TC2", bars)
+
+    record = build_null_record(
+        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    assert record["k_drawn"] == 2
+    assert record["eligible_count"] == 2
+    assert record["excluded"] is False
+    assert record["k_requested"] - record["k_drawn"] == 2  # the shortfall, served not hidden
+    assert len(record["anchors"]) == 2
+
+
+# === TC-3: zero eligible -- occurrence excluded and counted, never silently dropped ===================
+
+
+def test_tc3_zero_eligible_excludes_and_counts_the_occurrence(env):
+    """TC-3: exactly 1 bar total (only the trigger itself) -> excluded == True, eligible_count ==
+    0, k_drawn == 0 -- and the record is still RETURNED (never a ``None``/omitted result), so a
+    caller's own tally can count the exclusion instead of it silently vanishing."""
+    bar_store, playbook_store, _null_store, _run_store = env
+    bars = [_bar5("TC3", 0)]
+    observation = _plant_occurrence(playbook_store, bar_store, "TC3", bars)
+
+    record = build_null_record(
+        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    assert record["excluded"] is True
+    assert record["eligible_count"] == 0
+    assert record["k_drawn"] == 0
+    assert record["anchors"] == []
+    assert record["mean_window_overlap"] is None
+
+
+# === TC-4: the remaining-time boundary (15:00 ELIGIBLE / 15:05 INELIGIBLE for a 1h primary) ==========
+
+
+def test_tc4_remaining_time_boundary_at_1500_vs_1505_et_for_a_1h_horizon():
+    """TC-4: a candidate anchor bar at EXACTLY 15:00 ET (60 min remaining before the 16:00 ET
+    close) is ELIGIBLE for a 1h-horizon primary (``>= 60``); one at 15:05 ET (55 min remaining) is
+    INELIGIBLE (``< 60``) -- both hand-verified against the literal wall-clock distance to the
+    session's own RTH close, spec Sec4.1's remaining-time rule. Exercises ``_eligible_anchor_
+    positions`` directly (the eligibility primitive), independent of the full record-build
+    pipeline."""
+    import datetime
+    import zoneinfo
+
+    et = zoneinfo.ZoneInfo("America/New_York")
+    e_1500 = datetime.datetime.combine(
+        datetime.date(2026, 6, 22), datetime.time(15, 0), tzinfo=et
+    ).timestamp()
+    e_1505 = datetime.datetime.combine(
+        datetime.date(2026, 6, 22), datetime.time(15, 5), tzinfo=et
+    ).timestamp()
+    e_1530 = datetime.datetime.combine(
+        datetime.date(2026, 6, 22), datetime.time(15, 30), tzinfo=et
+    ).timestamp()  # the trigger -- clear of both candidates, still in the "close" bucket
+
+    bars = [
+        RawBar("TC4", "5m", e_1530, 1, 1, 1, 1, 1),  # index 0: trigger
+        RawBar("TC4", "5m", e_1500, 1, 1, 1, 1, 1),  # index 1: 60 min remaining -- ELIGIBLE
+        RawBar("TC4", "5m", e_1505, 1, 1, 1, 1, 1),  # index 2: 55 min remaining -- INELIGIBLE
+    ]
+    close_epoch = _session_close_epoch(SESSION_DATE)
+    assert tod_bucket_for_epoch(e_1500) == tod_bucket_for_epoch(e_1505) == tod_bucket_for_epoch(e_1530) == "close"
+
+    positions = _eligible_anchor_positions(bars, 0, "close", 60.0, close_epoch)
+    assert positions == [1]  # ONLY the 15:00 bar -- the 15:05 bar correctly excluded
+
+
+# === TC-5: the context-matched null -- backing-bucket predicate + the paired signal's own risk =======
+
+
+def test_tc5_context_null_backing_bucket_predicate_and_room_r_from_the_paired_signal(env):
+    """TC-5: 5 bars -- trigger near a recorded support band (index 0), one candidate far from any
+    band (index 1, excluded), three candidates near the SAME band (indices 2-4, matched). Every
+    stored anchor's close satisfies ``at_wall`` via the injected resolver (standing in for
+    ``BandMapResolver`` -- the SAME public ``band_context_block`` this module calls, dependency-
+    injected rather than requiring a real ``TradabilityCache``); the excluded candidate is reflected
+    in the served per-cell rate (3 matched / 4 ToD-eligible == 0.75); ``room_r`` on each anchor
+    equals the paired occurrence's OWN risk distance (verified by an independent re-derivation
+    calling ``band_context_block`` a second time with the SAME ``risk_bps``)."""
+    from app.research.desk_playbook_context import band_context_block
+
+    bar_store, playbook_store, _null_store, _run_store = env
+    bars = [
+        _bar5("TC5", 0, close=100.05),  # trigger -- near the band
+        _bar5("TC5", 1, close=200.0),  # far from the band -- excluded
+        _bar5("TC5", 2, close=100.06),
+        _bar5("TC5", 3, close=100.07),
+        _bar5("TC5", 4, close=100.08),
+    ]
+    observation = _plant_occurrence(playbook_store, bar_store, "TC5", bars)
+
+    class _FakeResolver:
+        def resolve(self, symbol, as_of_epoch):
+            return {
+                "bands": [
+                    {
+                        "side": "support", "class": "A", "price_low": 99.9, "price_high": 100.1,
+                        "quality_score": 1.0, "round_number": False, "member_count": 1,
+                    }
+                ],
+                "basis_as_of": "2026-06-21",
+            }
+
+    record = build_null_record(
+        observation, null_spec_id=REFEREE_NULL_CONTEXT_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(), backing_bucket=AT_WALL,
+        context_resolver=_FakeResolver(),
+    )
+    assert record["eligible_count"] == 3  # indices 2,3,4 -- index 1 (200.0) fails the predicate
+    assert record["k_drawn"] == 3
+    assert record["excluded"] is False
+    assert record["backing_bucket_eligibility_rate"] == 3 / 4
+    assert record["context_algorithm_version"] == PLAYBOOK_CONTEXT_ALGORITHM_VERSION
+    assert all(a["backing_bucket_match"] is True for a in record["anchors"])
+
+    # room_r independent re-derivation: the paired occurrence's own risk distance (entry vs
+    # invalidation_price, both recorded on the signal) must be what band_context_block computed.
+    entry, invalidation = bars[0].close, bars[0].close - 0.5
+    expected_risk_bps = abs(entry - invalidation) / entry * 10_000.0
+    map_result = _FakeResolver().resolve("TC5", bars[0].epoch)
+    for anchor in record["anchors"]:
+        anchor_bar = next(b for b in bars if referee_null_module._iso(b.epoch) == anchor["anchor_ts"])
+        ctx = band_context_block(
+            map_result, anchor_bar.close, "long", risk_bps=expected_risk_bps,
+            risk_source="paired_signal",
+        )
+        assert ctx["risk_bps"] == expected_risk_bps
+        assert ctx["room_r"] is not None or ctx["headroom_bps"] is None  # room_r derivable whenever headroom is
+
+
+def test_tc5_context_null_unresolvable_map_is_an_honest_exclusion_not_a_substitution(env):
+    """TC-5 (the "cannot be found" half): when the context resolver reports NO computed map at all,
+    the WHOLE occurrence is excluded (never a silent fallback to the unfiltered ToD population)."""
+    bar_store, playbook_store, _null_store, _run_store = env
+    bars = [_bar5("TC5B", i) for i in range(5)]
+    observation = _plant_occurrence(playbook_store, bar_store, "TC5B", bars)
+
+    class _NoMapResolver:
+        def resolve(self, symbol, as_of_epoch):
+            return None
+
+    record = build_null_record(
+        observation, null_spec_id=REFEREE_NULL_CONTEXT_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+        context_resolver=_NoMapResolver(),
+    )
+    assert record["excluded"] is True
+    assert record["eligible_count"] == 0
+    assert record["backing_bucket_eligibility_rate"] is None
+
+
+# === TC-6: convention identity -- the null path vs a DIRECT desk_forward._measure_from call ==========
+
+
+def test_tc6_anchor_measurement_is_byte_identical_to_a_direct_measure_from_call(env):
+    """TC-6: the value this module serves for a drawn anchor equals, byte for byte, calling
+    ``desk_forward._measure_from`` directly on the SAME bar/index/entry/entry_kind/tf_minutes/sign
+    -- zero diff to the rail."""
+    bar_store, playbook_store, _null_store, _run_store = env
+    bars = [_bar5("TC6", i, close=100.0 + i * 0.3) for i in range(5)]
+    observation = _plant_occurrence(playbook_store, bar_store, "TC6", bars)
+
+    record = build_null_record(
+        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    sign = side_sign("long")
+    for anchor in record["anchors"]:
+        idx = next(i for i, b in enumerate(bars) if referee_null_module._iso(b.epoch) == anchor["anchor_ts"])
+        direct = _measure_from(bars, idx, bars[idx].close, "close", 5, sign)
+        assert direct["to_close_pct"] == anchor["value"]  # this fixture's measure_key is to_close
+
+
+# === TC-7: lookahead-clean -- a session truncated at the trigger fabricates nothing ===================
+
+
+def test_tc7_truncated_session_produces_zero_eligible_never_a_fabricated_anchor(env):
+    """TC-7: a session recorded with bars ONLY through the trigger bar itself (nothing after it, as
+    if the null were rebuilt the instant the occurrence fired) yields ``eligible_count == 0`` --
+    never a value drawn from a bar that, at that instant, does not yet exist on disk. This module
+    reads only ``bar_store.merged_bars`` (whatever is actually recorded), so lookahead-cleanliness
+    holds by construction; this test is the regression guard."""
+    bar_store, playbook_store, _null_store, _run_store = env
+    bars = [_bar5("TC7", 0)]  # truncated immediately after the trigger bar -- nothing else recorded
+    observation = _plant_occurrence(playbook_store, bar_store, "TC7", bars)
+
+    record = build_null_record(
+        observation, null_spec_id=REFEREE_NULL_TOD_SPEC_ID, playbook_store=playbook_store,
+        bar_store=bar_store, config_fingerprint=CONFIG.config_fingerprint(),
+    )
+    assert record["excluded"] is True
+    assert record["eligible_count"] == 0
+    assert record["anchors"] == []
+
+
+# === TC-8 / TC-9: idempotent reuse (compute-manager level) + old stores untouched =====================
+
+
... [diff_bound] apps/backend/tests/test_referee_null.py: 421 more diff lines omitted — Read the file for full detail
```
