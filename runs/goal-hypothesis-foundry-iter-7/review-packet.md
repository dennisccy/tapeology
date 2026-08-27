# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index a18a6968..808d1a66 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -898,7 +898,29 @@ _EPOCH_MANIFEST_VIEW = read_epoch_manifest_view()
 # real committed manifest -- the total `FROZEN_READY` variant count across every family. Derived
 # from the SAME `_EPOCH_MANIFEST_VIEW` object already computed above (no second manifest read), so
 # there remains exactly one canonical reader of the tracked manifest file.
-_FOUNDRY_FROZEN_READY_TOTAL = sum(f["variant_count"] for f in _EPOCH_MANIFEST_VIEW.get("families", []))
+def compute_frozen_ready_total(epoch_manifest_view: dict) -> int:
+    """Sole canonical owner of ``exhaust_progress.frozen_ready_total``
+    (goal-hypothesis-foundry-iter-7 consolidation --
+    ``runs/goal-session-hypothesis-foundry/iter-6/coherence.md``, Blocking violation 1). Sums each
+    family's own ``variant_count`` field -- the field the real ``epoch-manifest.json``'s own family
+    entries already carry, exactly as passed through by ``read_epoch_manifest_view``'s ``families``
+    list (itself ``manifest_payload.get("families", [])`` verbatim, never re-derived) -- across
+    every family in the epoch manifest view.
+
+    Before this iteration this was an inline expression at this same call site; iter-7 extracted it
+    into this one named function so this Data-Contract value has exactly one implementation
+    anywhere in the (non-sealed) codebase. The sealed CLI
+    ``apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225`` computes the identical
+    concept independently, keyed on a different manifest field (``len(variants)`` vs.
+    ``variant_count``); that file has been frozen since the era's first-read lock
+    (2026-08-27T06:55:51Z, ``docs/hypothesis-foundry/freeze-set.json``) and may not be edited to
+    call this helper. ``test_run_hypothesis_foundry_real_exhaust.py``'s equivalence-pinning test
+    instead proves, permanently, that the sealed CLI's own (transcribed, unedited) formula agrees
+    with this function's output on the real, frozen manifest."""
+    return sum(f["variant_count"] for f in epoch_manifest_view.get("families", []))
+
+
+_FOUNDRY_FROZEN_READY_TOTAL = compute_frozen_ready_total(_EPOCH_MANIFEST_VIEW)
 
 
 @router.get("/foundry")
diff --git a/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py b/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
index 984583c9..3e9b4ce8 100644
--- a/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
+++ b/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
@@ -163,6 +163,43 @@ def test_tc2_second_invocation_verifies_and_appends_no_second_epoch_open_row(exh
     assert len(epoch_open_rows) == 1  # no duplicate first-read-lock row
 
 
+def test_frozen_ready_total_sealed_cli_formula_agrees_with_the_canonical_helper():
+    """goal-hypothesis-foundry-iter-7 equivalence-pinning test (retires
+    ``runs/goal-session-hypothesis-foundry/iter-6/coherence.md``'s DUPLICATE-COMPUTATION FAIL on
+    ``exhaust_progress.frozen_ready_total``): the sealed CLI
+    ``apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py`` (one of the 59 entries in
+    ``docs/hypothesis-foundry/freeze-set.json``, sealed since 2026-08-27T06:55:51Z) computes this
+    same concept independently of the canonical serving path in
+    ``app/research/micro_routes.py``. The sealed file may not be edited or even imported for this
+    check (the spec's explicit instruction), so the formula at its line 225 is TRANSCRIBED
+    LITERALLY, unedited, below -- a future reader can visually diff this line against the frozen
+    source to confirm it has not silently drifted from what the sealed file actually says.
+
+    This test loads the real, committed ``docs/hypothesis-foundry/epoch-manifest.json`` directly
+    via ``json`` (never via ``exhaust_mod``/``importlib`` on the sealed script) and asserts the
+    transcribed sealed formula agrees with ``micro_routes.compute_frozen_ready_total`` -- the new
+    sole canonical owner -- on that same real data. Today this is vacuously ``0 == 0`` (the frozen
+    manifest's ``families`` list is ``[]``); the test's permanent value is pinning agreement for
+    this frozen, unchangeable manifest, not proving a non-trivial case."""
+    _require_real_epoch_committed()
+    manifest = json.loads((FOUNDRY_DOCS_DIR / "epoch-manifest.json").read_text(encoding="utf-8"))
+
+    # --- transcribed VERBATIM from apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py:225
+    # (sealed; do not import/refactor that file for this comparison -- see docstring above) --------
+    sealed_cli_frozen_ready_total = sum(len(fm.get("variants", [])) for fm in manifest.get("families", []))
+    # -------------------------------------------------------------------------------------------------
+
+    from app.research import micro_routes
+
+    canonical_frozen_ready_total = micro_routes.compute_frozen_ready_total(manifest)
+
+    assert sealed_cli_frozen_ready_total == canonical_frozen_ready_total
+    # Documents today's expected value so a future manifest regeneration that changes `families`
+    # cannot silently pass this test with both sides wrong in the same new way without a reviewer
+    # noticing the changed literal below.
+    assert canonical_frozen_ready_total == 0
+
+
 def test_tc6_concurrent_invocation_is_refused_via_the_real_single_flight_lock(exhaust_mod, tmp_path):
     _require_real_epoch_committed()
     from app.research import foundry_runner as fr
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-hypothesis-foundry/telemetry.jsonl   | 7 +++++++
 runs/goal-session-hypothesis-foundry/trace/trace.jsonl | 2 ++
 2 files changed, 9 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
