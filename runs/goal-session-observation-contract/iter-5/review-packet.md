# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/app/main.py b/apps/backend/app/main.py
index 4082e32b..b69d477c 100644
--- a/apps/backend/app/main.py
+++ b/apps/backend/app/main.py
@@ -30,6 +30,7 @@ from pydantic import BaseModel
 from .config import CONFIG
 from .env import load_env
 from .meta import router as meta_router
+from .observation_contract import build_tape_observation, resolve_implementation_provenance
 from .providers.adapters import MarketDataAdapter, get_adapter
 from .providers.adapters.base import (
     NoDataForWindow,
@@ -273,6 +274,16 @@ def _iso_utc(dt: datetime) -> str:
     return dt.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
 
 
+def _now_utc() -> datetime:
+    """The wall clock ``GET /tape/{ticker}/observation`` reads for ``generated_at_utc``
+    (Observation Contract v1 Constitution §2: "the wall clock at which this artifact projection
+    was generated") -- the ONLY clock read that route performs; ``build_tape_observation`` itself
+    reads no clock. A tiny per-module seam (mirrors ``_iso_utc``'s own convention) so a test can
+    freeze it via ``monkeypatch.setattr(main, "_now_utc", ...)`` rather than patching the stdlib
+    ``datetime`` class."""
+    return datetime.now(timezone.utc)
+
+
 @app.get("/health")
 def health() -> dict:
     return {"status": "ok"}
@@ -635,6 +646,43 @@ def get_history(
     return serialize_history(engine.history, effective_bar, epoch_anchor=engine.epoch_anchor)
 
 
+@app.get("/tape/{ticker}/observation")
+def get_observation(ticker: str) -> dict:
+    """``GET /tape/{ticker}/observation`` -- Observation Contract v1 Binding Execution Order step 5
+    (J-05; docs/goal.md Constitution §7), the one read-only machine path for the ``TapeObservation``
+    v1 artifact. Transport ONLY: the route consumes the ONE atomic managed-observation read
+    (``manager.get_observation_source``) and calls ``build_tape_observation`` with the route's own
+    ``now`` -- it calls no ``TapeEngine`` method, performs no computation, and recomputes no field
+    (the critical Binding-Order violation this route must never commit: a direct engine-snapshot
+    read here -- ``tests/test_tape_observation_route.py``'s AST guard proves it never happens).
+    404s in the exact ``_engine_or_404`` shape for a not-currently-watched ticker (never
+    fabricated) -- ``get_observation_source`` returns ``None`` under the identical
+    ``self._engines.get(ticker) is None`` condition ``_engine_or_404`` itself checks, so this
+    mirrors every other ``/tape/*`` sibling above byte-for-byte.
+    """
+    source = manager.get_observation_source(ticker)
+    if source is None:
+        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' is not being watched")
+    snapshot, settled_at_utc, end_reason, descriptor = source
+    return build_tape_observation(
+        snapshot=snapshot,
+        source_mode=descriptor.source_mode,
+        data_feed=descriptor.data_feed,
+        window_start_utc=descriptor.window_start_utc,
+        window_end_utc=descriptor.window_end_utc,
+        dataset_id=descriptor.dataset_id,
+        dataset_checksum=descriptor.dataset_checksum,
+        session_id=descriptor.session_id,
+        session_started_at_utc=descriptor.session_started_at_utc,
+        settled_at_utc=settled_at_utc,
+        end_reason=end_reason,
+        generated_at_utc=_iso_utc(_now_utc()),
+        profile_id=descriptor.profile_id,
+        config=CONFIG,
+        provenance=resolve_implementation_provenance(),
+    )
+
+
 @app.websocket("/tape/{ticker}/stream")
 async def stream(websocket: WebSocket, ticker: str) -> None:
     engine = manager.get(ticker)
diff --git a/apps/backend/tests/test_tape_observation_path_equivalence.py b/apps/backend/tests/test_tape_observation_path_equivalence.py
index fb9dff9e..9bb2704e 100644
--- a/apps/backend/tests/test_tape_observation_path_equivalence.py
+++ b/apps/backend/tests/test_tape_observation_path_equivalence.py
@@ -398,10 +398,17 @@ def test_field_partition_groups_are_unchanged_from_iteration_1():
     assert observation_contract.INTEGRITY_FIELDS == _FROZEN_INTEGRITY_FIELDS
 
 
-def test_counterexample_field_partition_drift_is_detected():
-    # Proves the check above is non-vacuous: a widened semantic-fields tuple (one metadata field
-    # smuggled in, the "manufacture equivalence by widening the partition" anti-goal) must NOT
-    # equal the frozen reference.
-    widened = _FROZEN_SEMANTIC_FIELDS + ("source.session_id",)
+def test_counterexample_field_partition_drift_is_detected(monkeypatch):
+    # TC-16 (iter-5 fix): the prior version of this counter-example built a `widened` tuple and
+    # compared it only to a second hand-written literal (`_FROZEN_SEMANTIC_FIELDS`), never touching
+    # the real subject -- vacuous (the iter-4 evaluator finding; the lessons entry: "the
+    # counter-example must perturb ... the REAL constant, not a second copy of the literal").
+    # Perturb the REAL `observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS` attribute (one
+    # metadata field smuggled in, the "manufacture equivalence by widening the partition"
+    # anti-goal) via monkeypatch, and show the module's OWN real partition-equality check --
+    # `test_field_partition_groups_are_unchanged_from_iteration_1`'s own assertion -- fails against
+    # the perturbed value.
+    widened = observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS + ("source.session_id",)
+    monkeypatch.setattr(observation_contract, "MACHINE_OBSERVATION_SEMANTIC_FIELDS", widened)
     with pytest.raises(AssertionError):
-        assert widened == _FROZEN_SEMANTIC_FIELDS
+        assert observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS == _FROZEN_SEMANTIC_FIELDS
```

## Excluded-path stat (dependency/lockfile visibility)

 runs/goal-session-observation-contract/journey-scripts/J-01.json | 2 +-
 runs/goal-session-observation-contract/journey-scripts/J-03.json | 2 +-
 runs/goal-session-observation-contract/journey-scripts/J-04.json | 6 ++----
 runs/goal-session-observation-contract/telemetry.jsonl           | 6 ++++++
 runs/goal-session-observation-contract/trace/trace.jsonl         | 1 +
 5 files changed, 11 insertions(+), 6 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
