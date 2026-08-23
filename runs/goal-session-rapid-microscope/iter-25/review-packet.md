# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 2. Shown in full: 2.

```diff
diff --git a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
index 0c332bb2..73862342 100644
--- a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
+++ b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
@@ -70,6 +70,15 @@
 # browser pass recorded. Uses a symbol (PGQA) distinct from the PG tick fixtures above so the two
 # seed steps' datasets never collide.
 #
+# goal-rapid-microscope-iter-25 extends this file once more, again in place: after every seed step
+# above, it also runs seed_micro_vault_iter25_sealed_fixture.py (a plain dataset + a REAL
+# vault.seal_shard() call that is NEVER assigned/exposed, never a hand-rolled JSON blob), giving
+# this rig a SECOND vault shard that stays permanently sealed alongside the iter-18 one's exposed
+# shard. Before this, the rig's Validation Vault table only ever showed an exposed row -- the
+# sealed-row opaque render branch (page.tsx:6810-6819) and the "Sealed at" bare-date cell
+# (page.tsx:6807) had no fixture data to trigger against for three browser-QA rounds. Uses a symbol
+# (PGVAULT) distinct from every other symbol this rig's other seed scripts use.
+#
 # Usage:
 #   bash apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh [root_dir] [port]
 #
@@ -136,6 +145,12 @@ export TAPEOLOGY_JOURNAL_DB="$JOURNAL_DB"
 # seed_micro_scout_iter24_j09_fixture.py's own docstring for the full sequence this exercises.
 "$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_micro_scout_iter24_j09_fixture.py" "$ROOT"
 
+# goal-rapid-microscope-iter-25 (J-06): seed ONE new REAL dataset + REAL vault.seal_shard() call
+# that is NEVER assigned/exposed -- see seed_micro_vault_iter25_sealed_fixture.py's own docstring
+# for the full reasoning. Gives this rig a second, permanently-sealed shard alongside the iter-18
+# seeder's exposed one.
+"$BACKEND_DIR/.venv/bin/python" "$SCRIPT_DIR/seed_micro_vault_iter25_sealed_fixture.py" "$ROOT"
+
 # goal-rapid-microscope-iter-19 (TC-9): the ONE list of store-root vars this launch bound the
 # backend to -- shared by the stderr echo below AND the durable manifest file, so the two can never
 # silently diverge. Closes iteration 18's evaluator finding ("the quality report states that the
diff --git a/apps/backend/tests/test_vault.py b/apps/backend/tests/test_vault.py
index dcc9ffcf..06ee5c8b 100644
--- a/apps/backend/tests/test_vault.py
+++ b/apps/backend/tests/test_vault.py
@@ -28,11 +28,14 @@ from pathlib import Path
 import pytest
 from fastapi.testclient import TestClient
 
+from app.config import CONFIG
 from app.main import app
 from app.providers.base import QuoteEvent, Side, TradeEvent
+from app.research import micro_accessor as ma
 from app.research import vault
 from app.research.datasets import DatasetStore
 from app.research.scout_ledger import compute_family_root_id as _scout_compute_family_root_id
+from scripts import seed_micro_vault_iter25_sealed_fixture as _iter25_seed_vault
 
 _FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "datasets"
 
@@ -3147,3 +3150,91 @@ def test_tr2_holds_when_one_non_selected_pool_position_is_publicly_disclosed(tmp
     # the counter-case, in the same arithmetic: disclose every non-selected position and certainty
     # DOES arrive -- so the assertion above is a measurement, not a tautology.
     assert len(expected_pairs) - len(non_selected) == still_selected
+
+
+# === Iteration 25 (J-06 close-out): the browser-QA rig's own new permanently-sealed fixture shard
+# is proven refused non-vacuously, using the SAME production seeder function the QA launcher's own
+# extension calls (``scripts/seed_micro_vault_iter25_sealed_fixture.py`` -- never a second,
+# divergent test-only construction of "a sealed shard"). TC-1/TC-8. =================================
+
+
+def test_tc1_iter25_the_qa_rigs_new_sealed_only_fixture_shard_serves_the_opaque_projection_only(
+    tmp_path, monkeypatch
+):
+    """TC-1: the iteration-25 QA-rig seeder plants a REAL dataset and calls the REAL
+    ``vault.seal_shard`` -- never ``assign_shard``/``expose_shard`` -- so
+    ``GET /research/desk/micro/vault`` must list it ``sealed`` with no
+    ``symbol``/``session_date``/``dataset_id``/``family_root_id`` populated. Runs the actual
+    production seeder against the same fixture-rig env-var scoping the browser-QA launcher itself
+    uses (``_scope_everything_to``), not a hand-rolled duplicate."""
+    _scope_everything_to(tmp_path, monkeypatch)
+    planted = _iter25_seed_vault.plant_sealed_shard(tmp_path)
+
+    with TestClient(app) as client:
+        state = client.get("/research/desk/micro/vault").json()
+    shards = {s["shard_id"]: s for s in state["shards"]}
+    assert planted["shard_id"] in shards, "the seeded shard never landed in the served vault state"
+    entry = shards[planted["shard_id"]]
+    assert entry["exposure_state"] == "sealed"
+    assert set(entry.keys()) == {
+        "shard_id", "universe_id", "size_bucket", "checksum_commitment", "sealed_at", "exposure_state",
+    }
+    for forbidden_key in ("symbol", "session_date", "dataset_id", "family_root_id"):
+        assert forbidden_key not in entry
+    assert planted["dataset_id"] not in json.dumps(entry)
+    assert planted["symbol"] not in json.dumps(entry)
+
+
+def test_tc8_iter25_the_qa_rigs_sealed_fixture_shard_is_refused_non_vacuously_on_every_non_vault_surface(
+    tmp_path, monkeypatch
+):
+    """TC-8: sweep every registered GET route (the same ``_sweepable_get_paths``/forbidden-token
+    machinery the TR-2 tests above already proved sound) against the LITERAL shard the QA rig's own
+    iteration-25 seeder plants, plus a direct ``MicroAccessor`` read -- proving the refusal actually
+    fires for THIS shard's id/symbol on every non-Vault surface, never merely that no exception
+    happened to occur. (The MCP surface is already covered structurally, not shard-by-shard, by
+    ``test_tr2_the_mcp_surface_is_closed_structurally_not_route_by_route`` above -- it proves route-
+    set equivalence with the REST sweep for ANY shard, this one included, so it is not re-swept
+    here.)"""
+    _scope_everything_to(tmp_path, monkeypatch)
+    planted = _iter25_seed_vault.plant_sealed_shard(tmp_path)
+    dataset_store = DatasetStore(tmp_path / "datasets")
+
+    forbidden_substrings = {
+        "dataset id": planted["dataset_id"],
+        "raw content checksum": planted["content_checksum"],
+        "symbol": planted["symbol"],
+    }
+
+    with TestClient(app) as client:
+        leaks: list[str] = []
+        swept: dict[str, int] = {}
+        for path in _sweepable_get_paths():
+            url = path.replace("{dataset_id}", planted["dataset_id"])
+            if "{" in url:
+                continue  # a parameterized path with no sealed-shard-reachable value to fill
+            response = client.get(url)
+            swept[path] = response.status_code
+            for name, token in forbidden_substrings.items():
+                if token in response.text:
+                    leaks.append(f"{path} serves the sealed shard's {name}")
+        assert leaks == [], "join-resistance breached:\n  " + "\n  ".join(leaks)
+        assert len(swept) >= 50, f"the sweep only reached {len(swept)} routes"
+        assert swept["/research/datasets/{dataset_id}"] == 403  # this exact shard's id, refused
+        assert swept["/research/desk/micro/vault"] == 200
+        assert swept["/research/desk/micro/readiness"] == 200
+
+    # non-vacuity: the seeder's own dataset really did land on disk -- proves the sweep above ran
+    # against a live surface with something real to withhold, not an empty route table.
+    listed = dataset_store.list()[0]
+    assert any(m["id"] == planted["dataset_id"] for m in listed), "the seeder's own dataset never landed on disk"
+
+    # direct accessor read: the SAME typed refusal micro_accessor.py already proves generically
+    # (test_micro_accessor.py TC-2), exercised here against THIS shard's literal id.
+    accessor = ma.MicroAccessor(
+        dataset_store, str(tmp_path / "snapshots"), CONFIG,
+        sealed_dataset_ids=frozenset({planted["dataset_id"]}),
+    )
+    with pytest.raises(ma.MicroAccessorSealedShardError) as excinfo:
+        accessor.read_snapshot_rows(planted["dataset_id"])
+    assert excinfo.value.opaque_metadata == {"shard_id": planted["dataset_id"], "status": "sealed"}
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/qa-scoped-backend-store-manifest.md        | 26 ++++++-------
 .../journey-scripts/J-06.json                      |  3 +-
 .../journey-scripts/J-08.json                      |  2 +-
 .../journey-scripts/J-10.json                      |  2 +-
 .../state/assumptions.md                           | 43 ++++++++++++++++++++++
 runs/goal-session-rapid-microscope/telemetry.jsonl |  6 +++
 .../trace/trace.jsonl                              |  1 +
 7 files changed, 67 insertions(+), 16 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
