# Review packet — bounded diff vs HEAD
Pre-built by build_review_packet (lib/common.sh): the dispatch prompt's git diff
commands, already run for you. Truncations and exclusions are NAMED below — run
the git commands ONLY for files marked truncated or excluded, if they matter.

# Iteration diff (bounded)

Files changed: 3. Shown in full: 3.

```diff
diff --git a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
index 4f380045..43c9d278 100644
--- a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
+++ b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
@@ -143,6 +143,32 @@ if [[ -f "$REAL_FOUNDRY_BASELINE" ]]; then
   cp "$REAL_FOUNDRY_BASELINE" "$FOUNDRY_DIR/"
 fi
 
+# goal-hypothesis-foundry-iter-6 (J-07 / TC-9): the SAME visibility gap, one artifact later. The new
+# `exhaust_progress` key of `GET /research/desk/micro/foundry` is read per-request by
+# `foundry_runner.read_exhaust_progress(foundry_dir, ...)` through the identical
+# `get_foundry_dir()`-scoped resolver the era-open baseline above uses — so the real Foundry trial
+# ledger the real exhaust CLI wrote (`apps/backend/.data/foundry/foundry_trial_ledger.jsonl` + its
+# `.chain_head.json` tail-anchor sidecar) is INVISIBLE to this rig unless it is copied in, and the
+# rig would otherwise render the honest-but-wrong pre-first-read-lock EmptyState instead of the real
+# completed-exhaust state. Fix: the identical plain-file-copy-of-a-real-recorded-artifact pattern.
+# Both files are copied together and only together — the sidecar anchors the hash chain of the exact
+# ledger bytes beside it, so copying one without the other would hand this rig a mismatched chain.
+# The transient single-flight lock file (`foundry_exhaust_runner.lock`) is deliberately NOT copied:
+# it is live OS-advisory-lock state belonging to the machine that ran the CLI, not recorded
+# evidence, and this rig's own live probe re-creates it. Honest-absence fallback: if the operator
+# has never run `scripts/run_hypothesis_foundry_real_exhaust.py`, there is nothing genuine to copy —
+# the rig then correctly falls back to the honest pre-lock `first_read_lock_recorded: false` state,
+# exactly like a fresh install (never fabricated).
+REAL_FOUNDRY_LEDGER="$BACKEND_DIR/.data/foundry/foundry_trial_ledger.jsonl"
+REAL_FOUNDRY_LEDGER_HEAD="$REAL_FOUNDRY_LEDGER.chain_head.json"
+if [[ -f "$REAL_FOUNDRY_LEDGER" ]]; then
+  mkdir -p "$FOUNDRY_DIR"
+  cp "$REAL_FOUNDRY_LEDGER" "$FOUNDRY_DIR/"
+  if [[ -f "$REAL_FOUNDRY_LEDGER_HEAD" ]]; then
+    cp "$REAL_FOUNDRY_LEDGER_HEAD" "$FOUNDRY_DIR/"
+  fi
+fi
+
 export TAPEOLOGY_BAR_DIR="$BAR_DIR"
 export TAPEOLOGY_DESK_UNIVERSE_DIR="$UNIVERSE_DIR"
 export TAPEOLOGY_DESK_PLAYBOOK_DIR="$PLAYBOOK_DIR"
diff --git a/apps/backend/tests/test_foundry_real_epoch_artifacts.py b/apps/backend/tests/test_foundry_real_epoch_artifacts.py
index 936755d7..3a05fb9d 100644
--- a/apps/backend/tests/test_foundry_real_epoch_artifacts.py
+++ b/apps/backend/tests/test_foundry_real_epoch_artifacts.py
@@ -361,6 +361,69 @@ def test_tc10_drifted_generation_inputs_are_refused_rather_than_minting_epoch_2(
         fz.generate_or_verify_manifest(fresh, drifted)
 
 
+# === goal-hypothesis-foundry-iter-6 TC-7: a DELETED manifest store refuses rather than silently
+# minting a second epoch. The drift guard directly above only fires when an EXISTING slot disagrees
+# with the new inputs -- an EMPTY store has nothing to disagree with, so before this iteration's fix
+# a missing `epoch-manifest.json` looked exactly like a first-ever generation and would have been
+# silently overwritten with whatever the current inputs happened to be. These are the tests that
+# make the refusal itself a standing guarantee rather than a one-time manual verification. ==========
+
+
+def _load_generation_module():
+    """Loads the real generation CLI as a module -- the same importlib load
+    ``test_tc1_registry_hash_and_dispositions_are_reproduced_by_the_real_generator`` performs, so
+    these tests exercise the SHIPPED function rather than a copy. Import-time side effects: none
+    beyond constant/dataclass definition (the script's own work all sits inside ``main``)."""
+    spec = importlib.util.spec_from_file_location(
+        "_generate_real_epoch_for_tc7_test",
+        BACKEND_DIR / "scripts" / "generate_hypothesis_foundry_real_epoch.py",
+    )
+    module = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(module)
+    return module
+
+
+def test_tc7_deleted_manifest_store_refuses_instead_of_silently_minting_a_new_epoch(tmp_path, monkeypatch):
+    """The refusal half of TC-7: ``epoch-manifest.json`` gone while its SIBLING
+    ``freeze-record.json`` (written in the same generation run, immediately after it) still stands
+    as proof a real generation already happened -> typed ``ManifestStoreMissingError``, never an
+    empty store. Fully hermetic: both paths point into ``tmp_path``; the real tracked artifacts are
+    never read, written, or deleted by this test."""
+    module = _load_generation_module()
+    missing_manifest = tmp_path / "epoch-manifest.json"
+    standing_freeze_record = tmp_path / "freeze-record.json"
+    standing_freeze_record.write_text(json.dumps({"freeze_commit": "0" * 40}), encoding="utf-8")
+    monkeypatch.setattr(module, "FREEZE_RECORD_PATH", standing_freeze_record)
+
+    assert not missing_manifest.exists()
+    with pytest.raises(module.ManifestStoreMissingError):
+        module._load_existing_manifest_store(missing_manifest)
+
+
+def test_tc7_first_ever_generation_still_gets_a_genuinely_fresh_store(tmp_path, monkeypatch):
+    """The other half of TC-7 -- the refusal must NOT be a blanket one, or the very first real
+    generation could never run: with NEITHER file on disk (a true fresh install), the loader still
+    returns an empty store."""
+    module = _load_generation_module()
+    monkeypatch.setattr(module, "FREEZE_RECORD_PATH", tmp_path / "freeze-record.json")
+    assert module._load_existing_manifest_store(tmp_path / "epoch-manifest.json") == {}
+
+
+def test_tc7_the_real_committed_manifest_reconstructs_a_populated_replay_store(manifest):
+    """Positive control over the REAL committed artifact (read-only): the loader reconstructs the
+    populated one-slot store that makes a re-run replay-VERIFY, and every reconstructed field is the
+    committed one -- so the refusal above is guarding a path that genuinely works when the file is
+    present."""
+    module = _load_generation_module()
+    store = module._load_existing_manifest_store(module.EPOCH_MANIFEST_PATH)
+    assert list(store) == ["epoch"]
+    record = store["epoch"]
+    assert record.epoch_id == manifest["epoch_id"]
+    assert record.manifest_hash == manifest["manifest_hash"]
+    assert record.inputs_hash == manifest["_inputs_hash"]
+    assert record.payload == manifest["_generation_inputs"]
+
+
 # === §8.4/§8.5: the freeze-set actually pins the science files in THIS checkout ===================
 
 
diff --git a/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py b/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
index df092aca..984583c9 100644
--- a/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
+++ b/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
@@ -338,3 +338,51 @@ def test_j07_step7_fixture_backed_crash_resume_through_the_real_sequence(exhaust
     assert len(intent_rows) == 1  # no duplicate intent row appended on resume
     assert len(terminal_rows) == 1
     assert terminal_rows[0]["candidate_spec_hash"] == spec.candidate_spec_hash
+
+
+# === TC-4, literally: a real call counter over the sanctioned protected-read door ==================
+
+
+def test_tc4_instrumented_micro_accessor_counter_records_zero_protected_reads(exhaust_mod, tmp_path, monkeypatch):
+    """TC-4's literal wording ("given the sanctioned ``micro_accessor`` is instrumented with a call
+    counter"). ``run_real_exhaust`` reports ``protected_read_count`` as a structural ``0`` -- true
+    by construction today (nothing in its call path reaches ``MicroAccessor.read_snapshot_rows``,
+    the ONE door to protected snapshot rows), and already guarded statically by the entrypoint-
+    allowlist test in ``test_foundry_real_epoch_artifacts.py``. This test adds the RUNTIME half:
+    a genuine counter wrapped around that door, so a future refactor that silently introduces a
+    protected read fails here instead of quietly turning the reported ``0`` into a lie.
+
+    Both flavors of run are instrumented under the SAME counter, deliberately: the real committed
+    manifest's vacuous zero-variant pass, and the fixture-backed ONE-variant pass -- the latter is
+    the only one that actually crosses ``run_family``/``run_one_candidate`` into the interpreter,
+    i.e. the code path where such a read could plausibly appear later. Fully isolated: both use a
+    ``tmp_path`` ledger/lock and the committed ``tests/fixtures/datasets`` corpus, never the real
+    runtime Foundry directory."""
+    _require_real_epoch_committed()
+    from app.research import micro_accessor as ma
+
+    calls: list[tuple] = []
+    original = ma.MicroAccessor.read_snapshot_rows
+
+    def _counting_read_snapshot_rows(self, dataset_id, *args, **kwargs):
+        calls.append((dataset_id, args, kwargs))
+        return original(self, dataset_id, *args, **kwargs)
+
+    monkeypatch.setattr(ma.MicroAccessor, "read_snapshot_rows", _counting_read_snapshot_rows)
+
+    real_result = exhaust_mod.run_real_exhaust(
+        tracked_dir=FOUNDRY_DOCS_DIR, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
+        foundry_dir=str(tmp_path / "real-foundry"), lock_path=tmp_path / "real-exhaust.lock",
+    )
+    assert real_result["protected_read_count"] == 0
+    assert calls == [], f"the real-manifest exhaust pass read protected snapshot rows: {calls}"
+
+    fixture_result = exhaust_mod.run_real_exhaust(
+        tracked_dir=_build_fixture_tracked_dir(tmp_path), repo_root=REPO_ROOT,
+        dataset_dir=str(FIXTURE_DATASET_DIR), foundry_dir=str(tmp_path / "fixture-foundry"),
+        lock_path=tmp_path / "fixture-exhaust.lock", frozen_ready_families=_one_variant_resolver,
+    )
+    # The variant really was evaluated end-to-end (otherwise "zero reads" would be vacuous).
+    assert fixture_result["terminal_count"] == 1
+    assert fixture_result["protected_read_count"] == 0
+    assert calls == [], f"the one-variant exhaust pass read protected snapshot rows: {calls}"
```

## Excluded-path stat (dependency/lockfile visibility)

 reports/qa-scoped-backend-store-manifest.md        | 26 +++++++++++-----------
 .../telemetry.jsonl                                | 15 +++++++++++++
 .../trace/trace.jsonl                              |  4 ++++
 3 files changed, 32 insertions(+), 13 deletions(-)

(if a dependency lockfile appears above, review the matching package.json/pyproject
edit in the main diff — never lockfile hunks; runs/ reports/ docs/handoffs/ churn is
harness bookkeeping, outside review scope)
