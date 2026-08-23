# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

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
diff --git a/apps/backend/scripts/seed_micro_vault_iter25_sealed_fixture.py b/apps/backend/scripts/seed_micro_vault_iter25_sealed_fixture.py
new file mode 100644
index 00000000..6519103a
--- /dev/null
+++ b/apps/backend/scripts/seed_micro_vault_iter25_sealed_fixture.py
@@ -0,0 +1,134 @@
+"""Seed ONE permanently-sealed vault shard into a throwaway rig root, for J-06's browser-QA pass
+(Era "The Rapid Microscope", goal-rapid-microscope-iter-25).
+
+**Why this exists.** Every prior browser-QA rig carried exactly one vault shard -- the iter-18
+graduation seeder's ``iter18-qa-universe`` shard, which is sealed -> assigned -> exposed in the
+same script run. That leaves the rig's Validation Vault table with zero shards ever observed in
+the ``sealed`` state by the time a screenshot is taken, so the "a sealed row stays opaque" render
+branch (``page.tsx:6810-6819``, shipped since iteration 14) and its browser acceptance check
+(TC-2/TC-3) have had no fixture data to trigger against for three rounds. This script closes that
+gap the SAME way every other fixture in this ``scripts/`` directory does: it plants a REAL dataset
+through ``DatasetStore.record`` and calls the REAL ``vault.seal_shard`` -- never a hand-rolled
+JSON blob standing in for either -- and, critically, it NEVER calls ``vault.assign_shard`` or
+``vault.expose_shard``, so the shard it plants stays ``sealed`` for the lifetime of the rig.
+
+**What this plants.** ONE real tiny tick dataset (symbol ``PGVAULT`` -- deliberately distinct from
+every other symbol this rig's other seed scripts use: ``PG`` (the era-2 committed tick fixtures),
+``PGQA`` (the iter-18 graduation seeder's exposed shard), and whatever real PG dataset the iter-24
+J-09 seeder reuses -- so this shard can never collide with, or be confused for, any of them), then
+``vault.seal_shard(...)`` on it under its own fixture-only universe id
+(``iter25-qa-sealed-only-universe``, never registered against a ``VaultUniverseLedger`` row --
+``seal_shard`` records ``universe_id`` verbatim without looking one up, so no registration act is
+needed for a shard that is never assigned) and its own fixture-only HMAC secret (a literal, never
+the operator's real ``TAPEOLOGY_VAULT_SECRET_FILE`` -- no seed script in this repo ever reads that
+file). The result: ``GET /research/desk/micro/vault`` on this rig now lists TWO shards -- the
+iter-18 one (``exposed``, full provenance) and this one (``sealed``, opaque projection only,
+forever) -- exercising both branches of the Vault table's per-row render for the first time.
+
+**Never touches the real ``.data`` store.** Every path this script writes to is derived from the
+``root`` argument's own env-var scoping (``TAPEOLOGY_DATASET_DIR`` and the vault dir it resolves
+as a sibling of), exactly like every other seed script in this directory. **Never a production
+code path change** -- this script imports and calls the SAME ``DatasetStore.record``/
+``vault.seal_shard`` functions the shipped product uses; it adds no new module, no new endpoint,
+no new branch inside either of them.
+
+``plant_sealed_shard`` is exported (not just callable from ``main``) so
+``tests/test_vault.py`` can reuse the identical production seeding logic directly -- proving the
+sealed-shard refusal non-vacuously against the literal shard this rig plants, rather than a second,
+divergent test-only construction of "a sealed shard."
+
+Usage (normally through ``qa_playbook_iter7_fixture_scoped_backend.sh``, which exports
+``TAPEOLOGY_DATASET_DIR`` first, mirroring every other seed script's own convention):
+
+    TAPEOLOGY_DATASET_DIR=... .venv/bin/python scripts/seed_micro_vault_iter25_sealed_fixture.py ROOT
+"""
+
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+_SCRIPTS_DIR = Path(__file__).resolve().parent
+sys.path.insert(0, str(_SCRIPTS_DIR))
+sys.path.insert(0, str(_SCRIPTS_DIR.parent))
+
+from app.providers.base import QuoteEvent, Side, TradeEvent  # noqa: E402
+from app.research import vault  # noqa: E402
+from app.research.datasets import DatasetStore  # noqa: E402
+
+_SYMBOL = "PGVAULT"  # distinct from PG / PGQA / CALDR -- never collides with any other seed script
+_WINDOW_START_UTC = "2026-06-10T13:00:00Z"
+_WINDOW_END_UTC = "2026-06-10T13:01:00Z"
+
+_UNIVERSE_ID = "iter25-qa-sealed-only-universe"
+_SEALED_AT = "2026-06-07T00:00:00.000000Z"  # a fixed, arbitrary instant -- never wall-clock (T-3/T-7)
+_FIXTURE_VAULT_SECRET = b"goal-rapid-microscope-iter25-qa-only-sealed-fixture-vault-secret"
+
+
+def _events_for_store() -> list:
+    """A tiny, REAL trade/quote sequence -- the ``test_micro_observer.py``/
+    ``seed_micro_graduation_iter18_fixture.py`` ``_events_for_store`` shape, mirrored verbatim
+    (never re-derived): one quote, one aggressor-classified BUY, one SELL."""
+    return [
+        QuoteEvent(_SYMBOL, 0.0, 99.99, 100.02, 100, 100),
+        TradeEvent(_SYMBOL, 0.1, 100.03, 10, Side.UNKNOWN),  # >= ask -> engine classifies BUY
+        TradeEvent(_SYMBOL, 0.2, 99.99, 10, Side.UNKNOWN),  # <= bid -> engine classifies SELL
+    ]
+
+
+def plant_sealed_shard(root: Path) -> dict:
+    """Plants the dataset + seals the shard for real; returns the identifiers a caller (this
+    module's own ``main``, or a test) needs to assert against. NEVER calls ``assign_shard``/
+    ``expose_shard`` -- the shard this returns stays ``sealed`` for as long as the ledger it was
+    written into exists."""
+    dataset_dir = root / "datasets"
+    dataset_dir.mkdir(parents=True, exist_ok=True)
+    dataset_store = DatasetStore(dataset_dir)
+    vault_dir = vault.resolve_vault_dir(str(dataset_dir))
+
+    events = _events_for_store()
+    dataset_meta = dataset_store.record(
+        symbol=_SYMBOL, source="fixture", source_kind="fixture",
+        source_id="goal-rapid-microscope-iter25-qa-sealed-only",
+        split="train", window_start_utc=_WINDOW_START_UTC, window_end_utc=_WINDOW_END_UTC,
+        data_feed="sip", epoch_anchor=0.0, events=events,
+    )
+    dataset_id = dataset_meta["id"]
+
+    shard_ledger = vault.VaultShardLedger(vault_dir)
+    row = vault.seal_shard(
+        shard_ledger, dataset_id=dataset_id, universe_id=_UNIVERSE_ID,
+        content_checksum=dataset_meta["checksum"], event_count=len(events),
+        vault_secret=_FIXTURE_VAULT_SECRET, sealed_at=_SEALED_AT,
+    )
+    return {
+        "dataset_id": dataset_id,
+        "symbol": _SYMBOL,
+        "universe_id": _UNIVERSE_ID,
+        "shard_id": row["shard_id"],
+        "content_checksum": dataset_meta["checksum"],
+        "vault_dir": vault_dir,
+        "dataset_dir": str(dataset_dir),
+    }
+
+
+def main(root: Path) -> int:
+    planted = plant_sealed_shard(root)
+    print(
+        f"[seed-micro-vault-iter25] sealed (never assigned/exposed) shard_id={planted['shard_id']} "
+        f"for dataset_id={planted['dataset_id']} ({planted['symbol']}) "
+        f"universe_id={planted['universe_id']}",
+        file=sys.stderr,
+    )
+    if planted["symbol"] in planted["shard_id"] or planted["dataset_id"] == planted["shard_id"]:
+        print(
+            "[seed-micro-vault-iter25] ERROR: the served shard_id is not opaque -- it derives "
+            "from or equals the real dataset id/symbol",
+            file=sys.stderr,
+        )
+        return 1
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()))
```
