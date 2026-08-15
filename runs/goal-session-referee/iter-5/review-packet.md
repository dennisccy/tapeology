# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 4. Shown in full: 4.

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
 
 
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-referee/telemetry.jsonl   | 7 +++++++
 runs/goal-session-referee/trace/trace.jsonl | 1 +
 2 files changed, 8 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
