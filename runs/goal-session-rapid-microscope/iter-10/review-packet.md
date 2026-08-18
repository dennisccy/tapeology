# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 220a509..1f07a4c 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -1,11 +1,17 @@
 """``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold, J-02's three
 snapshot routes, J-04's Scout routes, J-05's three walk-forward routes, J-06 step 2's recorder
-routes, and J-06 step 3's ONE read-only vault route. A fresh router/file mounted separately in
-``main.py``, mirroring ``referee_routes.py``'s own precedent and rationale (that file's own
-docstring: "the SAME rationale desk_routes.py itself gives for splitting off routes.py"). The
-era's own Data Contract table (``docs/goal.md``'s Product Shape) names ONE more micro route
-landing in a later iteration (graduation) under this SAME ``/research/desk/micro`` prefix -- a
-dedicated file is the right home from the start.
+routes, J-06 step 3's ONE read-only vault route, and J-07's ONE read-only graduation route. A
+fresh router/file mounted separately in ``main.py``, mirroring ``referee_routes.py``'s own
+precedent and rationale (that file's own docstring: "the SAME rationale desk_routes.py itself
+gives for splitting off routes.py"). The era's own Data Contract table (``docs/goal.md``'s Product
+Shape) named this exact route ("graduation states + export bundles") as landing in a later
+iteration under this SAME ``/research/desk/micro`` prefix -- this file was always its right home.
+
+``GET /graduation`` is GET-only this iteration, exactly like ``GET /vault`` above it -- J-07 is
+keyless/automated (no operator compute act triggers graduation; a candidate's state is read back
+from whatever ``micro_graduation.py``'s own evaluation functions have already recorded, called
+directly -- by a test today, by a future J-08/J-09 wiring later), so it needs no compute manager
+and no ``POST``/cancel sibling routes.
 
 ``GET /vault`` is GET-only this iteration -- no ``/vault/compute`` route and no CLI (the phase
 spec's own OUT OF SCOPE: "no operator act in this iteration or the next calls registration
@@ -40,6 +46,7 @@ from .desk_playbook import PlaybookStore
 from .desk_routes import get_playbook_store, get_universe_store
 from .desk_universe import UniverseStore
 from .micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir
+from .micro_graduation import EMPTY_LEDGER_MESSAGE, GraduationLedger, list_graduation_families, resolve_micro_graduation_dir
 from .micro_readiness import MicroReadinessCache, build_readiness, resolve_micro_readiness_cache_db_path
 from .micro_snapshots import (
     MicroSnapshotComputeManager,
@@ -531,3 +538,35 @@ def get_vault(vault_dir: str = Depends(get_vault_dir)) -> dict:
     before any universe is ever registered (registration is a step-4, operator-attended act, out of THIS iteration's
     scope)."""
     return vault.build_vault_state(vault.VaultShardLedger(vault_dir), vault.VaultUniverseLedger(vault_dir))
+
+
+# --- J-07: Graduation (micro_graduation.py) -- GET-only this iteration ------------------------------
+
+
+def get_micro_graduation_dir() -> str:
+    """The graduation ledger's directory -- ``TAPEOLOGY_MICRO_GRADUATION_DIR`` if set, else a
+    SIBLING of the config-owned dataset directory (``micro_graduation.resolve_micro_graduation_dir``
+    -- see that function's own docstring)."""
+    return resolve_micro_graduation_dir(CONFIG.dataset_dir_resolved())
+
+
+@router.get("/graduation")
+def get_graduation(graduation_dir: str = Depends(get_micro_graduation_dir)) -> dict:
+    """Serves ``micro_graduation.py``'s own recorded state verbatim (``list_graduation_families`` --
+    see that function's own docstring): every family_root_id ever recorded here, each with its
+    current stage-vocabulary state, complete transition history, and complete sealed-evaluation
+    history -- beside the ledger's own chain-verification verdict (the ``GET /scout``/``GET
+    /walkforward``/``GET /vault`` precedent: surfaced beside the data, never silently accepted if
+    tampered). Never 404/500 on an empty ledger (TC-9) -- no operator has run graduation yet on a
+    fresh install, so an honest ``EMPTY_LEDGER_MESSAGE`` ("No candidates ledgered.", goal.md's own
+    Design Direction example) accompanies the empty ``families`` list at HTTP 200, never a
+    fabricated row. Page-load GETs never compute (T-8): J-07 is keyless/automated -- a candidate's
+    state is recorded by calling ``micro_graduation.py``'s evaluation functions directly (a test
+    today; a future J-08/J-09 wiring act later), never by this route."""
+    ledger = GraduationLedger(graduation_dir)
+    families = list_graduation_families(ledger)
+    return {
+        "families": families,
+        "message": None if families else EMPTY_LEDGER_MESSAGE,
+        "chain_verification": ledger.verify_chain(),
+    }
diff --git a/docs/research-directions.md b/docs/research-directions.md
index 1ec5739..7d37fa2 100644
--- a/docs/research-directions.md
+++ b/docs/research-directions.md
@@ -1748,6 +1748,15 @@ so in the purchase decision: a dead L1 imbalance LOWERS the depth prior).
 > `historical_oos`-class evidence there, which both raises the depth prior and becomes 15.3's
 > named comparison baseline. Those families dying at the Scout LOWERS the prior, exactly as
 > Card 9.3's kill note already says. Diagnostic-class results count for neither direction.)*
+>
+> *(Follow-up 2026-08-18, "The Rapid Microscope" J-07 step 3, documentation-only — no code, no
+> threshold, no purchase decision: the mechanism the amendment above promised now exists.
+> `micro_graduation.py` (`docs/rapid-validation-spec.md` §8) implements the literal
+> `walkforward_survivor`/`sealed_survivor` states this amendment names as the Depth-purchase
+> evidence; either verdict for an L1 liquidity-family candidate — including a diagnostic-class
+> `no survivor` at the Scout, which counts for neither direction per the amendment above and this
+> era's own §10 disclosed L1-only-measurement limits — reads directly off that ledger when a
+> future Era-15 kickoff needs it, rather than requiring re-derivation.)*
 
 ---
 
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-rapid-microscope/telemetry.jsonl   | 6 ++++++
 runs/goal-session-rapid-microscope/trace/trace.jsonl | 1 +
 2 files changed, 7 insertions(+)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
