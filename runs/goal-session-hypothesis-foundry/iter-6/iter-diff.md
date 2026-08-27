# Iteration diff (bounded)

Files changed: 16. Shown in full: 16.

```diff
diff --git a/apps/backend/app/research/foundry_freeze.py b/apps/backend/app/research/foundry_freeze.py
index 46aa4039..7b0a0d1a 100644
--- a/apps/backend/app/research/foundry_freeze.py
+++ b/apps/backend/app/research/foundry_freeze.py
@@ -165,9 +165,26 @@ def _local_sibling_imports(path: Path) -> set[str]:
     return names
 
 
+def _freeze_set_key(path: Path, repo_root: Path | None) -> str:
+    """goal-hypothesis-foundry-iter-6 (closes audit finding B1): when ``repo_root`` is given AND
+    ``path`` actually lives under it, the key is the REPO-RELATIVE POSIX path (portable across
+    checkouts/worktrees on the same commit -- the whole point of a Git-visible freeze). When
+    ``repo_root`` is omitted (every existing hermetic-fixture call site: ``test_foundry_freeze.py``,
+    this module's own ``freeze_integrity_fixture_dir``/``_first_read_lock`` fixtures) or ``path``
+    does not live under it (a fixture directory outside the repo, e.g. a pytest ``tmp_path`` under
+    the platform temp root), the key falls back to the ABSOLUTE path exactly as before -- so no
+    existing hermetic fixture/test changes behavior."""
+    if repo_root is not None:
+        try:
+            return path.resolve().relative_to(repo_root.resolve()).as_posix()
+        except ValueError:
+            pass
+    return str(path)
+
+
 def generate_freeze_set(
     research_dir: str | Path, *, required_names: Sequence[str] | None = None,
-    extra_paths: Sequence[str | Path] = (),
+    extra_paths: Sequence[str | Path] = (), repo_root: str | Path | None = None,
 ) -> dict:
     """The deterministic freeze-set generator (§8.4): starting from ``required_names`` (default
     ``FREEZE_SET_REQUIRED_MODULES``), transitively walks each covered file's own local sibling
@@ -177,8 +194,13 @@ def generate_freeze_set(
     closed, never silently omits). ``extra_paths`` lets a caller pin additional non-``.py``
     dependencies this scanner cannot discover via import parsing (e.g. a config/version source
     file) -- unused by every test/call site this iteration, present for forward compatibility with
-    the real J-06/J-07 freeze-set (§8.4's "snapshot identity/version/parameter sources")."""
+    the real J-06/J-07 freeze-set (§8.4's "snapshot identity/version/parameter sources").
+
+    ``repo_root``, when given, keys every entry REPO-RELATIVE rather than by absolute path -- see
+    ``_freeze_set_key``'s own docstring. Omitted (the default), this function's entry keys are
+    byte-identical to before this iteration."""
     research_dir = Path(research_dir)
+    repo_root_path = Path(repo_root) if repo_root is not None else None
     names = tuple(required_names) if required_names is not None else FREEZE_SET_REQUIRED_MODULES
 
     entries: dict[str, str] = {}
@@ -195,14 +217,14 @@ def generate_freeze_set(
                 f"required/transitive local science dependency missing on disk: {path} -- freeze "
                 "generation refuses rather than silently omitting it (spec §8.4)"
             )
-        entries[str(path)] = _sha256_file(path)
+        entries[_freeze_set_key(path, repo_root_path)] = _sha256_file(path)
         queue.extend(sorted(_local_sibling_imports(path) - seen))
 
     for extra in extra_paths:
         p = Path(extra)
         if not p.is_file():
             raise FreezeSetDependencyUnproven(f"declared local science dependency missing: {p}")
-        entries[str(p)] = _sha256_file(p)
+        entries[_freeze_set_key(p, repo_root_path)] = _sha256_file(p)
 
     freeze_set_hash = _sha256(_canonical(entries))
     return {"entries": entries, "freeze_set_hash": freeze_set_hash}
@@ -224,12 +246,20 @@ class FreezeRecord:
     scout_screen_source_hash: str
     config_fingerprint: str
     freeze_set_hash: str
+    # goal-hypothesis-foundry-iter-6 (closes audit finding B7): §8.4's own required field list
+    # names "the era-open evidence-class contract" alongside every other pinned hash -- this era is
+    # constitutionally locked to ONE evidence class for every real Foundry evaluation
+    # (`historical_exposed_diagnostic`, goal.md Success Criteria 16 / spec §10.1), so the frozen
+    # value is that literal contract string, not a hash (there is nothing to hash; the CONTRACT
+    # itself, not a file, is what this field pins).
+    era_open_evidence_class_contract: str
 
 
 def build_freeze_record(
     *, freeze_commit: str, manifest_hash: str, source_registry_hash: str, spec_hash: str,
     candidate_spec_schema_hash: str, compiler_hash: str, interpreter_hash: str, runner_hash: str,
     scout_screen_source_hash: str, config_fingerprint: str, freeze_set_hash: str,
+    era_open_evidence_class_contract: str,
 ) -> FreezeRecord:
     """A pure constructor pinning every hash §8.4 requires -- no derivation, no defaults; a caller
     missing one supplies an explicit falsy value and gets a record that visibly fails
@@ -241,6 +271,7 @@ def build_freeze_record(
         compiler_hash=compiler_hash, interpreter_hash=interpreter_hash, runner_hash=runner_hash,
         scout_screen_source_hash=scout_screen_source_hash, config_fingerprint=config_fingerprint,
         freeze_set_hash=freeze_set_hash,
+        era_open_evidence_class_contract=era_open_evidence_class_contract,
     )
 
 
@@ -265,17 +296,28 @@ class FreezeIntegrityHalt(Exception):
     ``FOUNDRY_INTEGRITY_HALT``, never silently patched-and-continued (TC-13)."""
 
 
-def verify_freeze_set_unchanged(freeze_set: Mapping[str, object]) -> None:
+def verify_freeze_set_unchanged(
+    freeze_set: Mapping[str, object], *, repo_root: str | Path | None = None,
+) -> None:
     """Recomputes sha256 for every path ``freeze_set['entries']`` ENUMERATES and compares against
     the pinned digest -- any mismatch, or a pinned path that no longer exists, raises
     ``FreezeIntegrityHalt``. Deliberately looks at NOTHING outside those enumerated paths: a Goal
     Mode session/handoff file or a non-scientific UI-only file was never added to ``entries`` by
     ``generate_freeze_set`` (§8.4's own module-set scope), so this function structurally cannot
     false-refuse on either (TC-13's second and third parts) -- there is no "everything else must
-    also be clean" check anywhere in this function."""
+    also be clean" check anywhere in this function.
+
+    ``repo_root``, when given, resolves a RELATIVE entry key against it before hashing (the
+    counterpart to ``generate_freeze_set(..., repo_root=...)``'s repo-relative keys). An entry key
+    that is already absolute is used exactly as recorded, whether or not ``repo_root`` is given --
+    the hermetic temp-dir fixtures every existing test/fixture uses (``test_foundry_freeze.py``,
+    this module's own ``_first_read_lock``) never pass ``repo_root`` and keep working unmodified."""
     entries = freeze_set["entries"]  # type: ignore[index]
+    repo_root_path = Path(repo_root) if repo_root is not None else None
     for path_str, expected_hash in entries.items():
         path = Path(path_str)
+        if not path.is_absolute() and repo_root_path is not None:
+            path = repo_root_path / path
         if not path.is_file():
             raise FreezeIntegrityHalt(f"freeze-set path missing after first-read lock: {path}")
         actual_hash = _sha256_file(path)
@@ -384,6 +426,7 @@ def _freeze_record() -> dict:
         compiler_hash="fixture-compiler-hash", interpreter_hash="fixture-interpreter-hash",
         runner_hash="fixture-runner-hash", scout_screen_source_hash="fixture-scout-screen-source-hash",
         config_fingerprint="fixture-config-fingerprint", freeze_set_hash=result["freeze_set_hash"],
+        era_open_evidence_class_contract="fixture-era-open-evidence-class-contract",
     )
     return {
         "freeze_set_target_path": "docs/hypothesis-foundry/freeze-set.json",
diff --git a/apps/backend/app/research/foundry_ledger.py b/apps/backend/app/research/foundry_ledger.py
index 6620c130..c35e4fb3 100644
--- a/apps/backend/app/research/foundry_ledger.py
+++ b/apps/backend/app/research/foundry_ledger.py
@@ -20,6 +20,7 @@ from .micro_chain_ledger import HashChainedLedger
 __all__ = [
     "ROW_KIND_INTENT",
     "ROW_KIND_TERMINAL",
+    "ROW_KIND_EPOCH_OPEN",
     "ROOT_DEFERRED_COMPOSITE",
     "ConflictingReplayRefused",
     "FoundryLedger",
@@ -31,6 +32,11 @@ _LEDGER_FILENAME = "foundry_trial_ledger.jsonl"
 
 ROW_KIND_INTENT = "evaluation_intent"
 ROW_KIND_TERMINAL = "terminal"
+# goal-hypothesis-foundry-iter-6 (J-07): §8.5's first-read-lock row -- appended exactly once, by
+# the real exhaust CLI, immediately BEFORE the first candidate outcome could ever be read. Shares
+# this SAME physical hash chain (never a second ledger/file) -- discriminated by `row_kind`, the
+# identical convention `ROW_KIND_INTENT`/`ROW_KIND_TERMINAL` already establish.
+ROW_KIND_EPOCH_OPEN = "epoch_open"
 
 # §5.5: "otherwise record the literal `root_deferred_composite`... no composite root is invented
 # in this era."
@@ -76,6 +82,18 @@ _TERMINAL_IDENTITY_FIELDS = (
     "rule_id", "prospective_root_status", "foundry_state",
 )
 
+# The epoch-opening row's own identity fields for the SAME "exact duplicate -> verify-and-return,
+# any difference -> refuse" discipline (§9.2), applied to the one first-read-lock row rather than a
+# per-candidate terminal row. Every pinned freeze hash plus the two facts only THIS invocation
+# supplies (`epoch_id`, `eligible_corpus_manifest_hash`) -- `recorded_at` is deliberately excluded
+# (a replay's own timestamp legitimately differs from the original; that is not a content conflict).
+_EPOCH_OPEN_IDENTITY_FIELDS = (
+    "epoch_id", "freeze_commit", "manifest_hash", "source_registry_hash", "spec_hash",
+    "candidate_spec_schema_hash", "compiler_hash", "interpreter_hash", "runner_hash",
+    "scout_screen_source_hash", "config_fingerprint", "freeze_set_hash",
+    "era_open_evidence_class_contract", "eligible_corpus_manifest_hash",
+)
+
 
 class FoundryLedger:
     """One Foundry epoch's complete trial record -- intent rows (§6 step 4 / §9.2's
@@ -104,6 +122,15 @@ class FoundryLedger:
                 return row
         return None
 
+    def epoch_open_row(self) -> dict | None:
+        """§8.5's first-read-lock row -- at most ONE ever exists per epoch (this ledger holds
+        exactly one epoch's trials, per §8.1's "at most one real epoch_id"). ``None`` before the
+        real exhaust CLI's first invocation -- the honest pre-lock state (T-8: never fabricated)."""
+        for row in reversed(self._chain.all_rows()):
+            if row["row_kind"] == ROW_KIND_EPOCH_OPEN:
+                return row
+        return None
+
     def record_intent(
         self, *, candidate_spec_hash: str, manifest_hash: str, econ_floor_bps: float | None,
         econ_floor_provenance: str, recorded_at: str | None = None,
@@ -123,6 +150,56 @@ class FoundryLedger:
             }
         )
 
+    def record_epoch_open(
+        self, *, epoch_id: str, freeze_commit: str, manifest_hash: str, source_registry_hash: str,
+        spec_hash: str, candidate_spec_schema_hash: str, compiler_hash: str, interpreter_hash: str,
+        runner_hash: str, scout_screen_source_hash: str, config_fingerprint: str, freeze_set_hash: str,
+        era_open_evidence_class_contract: str, eligible_corpus_manifest_hash: str,
+        recorded_at: str | None = None,
+    ) -> dict:
+        """§8.5: "Immediately before the first candidate outcome read, the Foundry ledger appends
+        an epoch-opening row that repeats all freeze hashes, records the resolved eligible
+        diagnostic-corpus manifest hash..., and marks the first-read boundary." Pins EVERY
+        ``freeze-record.json`` hash plus the resolved eligible-corpus ``(dataset_id, checksum)``
+        manifest hash the caller already computed (this method never computes it itself -- it only
+        persists whatever it is given, the same discipline ``record_intent``/``record_terminal``
+        already follow).
+
+        Idempotent on replay (§9.2's "already-terminal candidate -> verify and skip", applied here
+        to the ONE epoch-opening row rather than a per-candidate terminal row): a second call whose
+        every identity field matches the existing row returns that EXISTING row untouched (no
+        second first-read-lock row is ever appended -- TC-2). A call whose content differs from the
+        already-recorded row raises ``ConflictingReplayRefused`` -- mirroring ``record_terminal``'s
+        own refuse-rather-than-silently-overwrite discipline -- rather than silently accepting a
+        drifted resume as if it were the same epoch's own lock."""
+        candidate = {
+            "row_kind": ROW_KIND_EPOCH_OPEN,
+            "epoch_id": epoch_id,
+            "freeze_commit": freeze_commit,
+            "manifest_hash": manifest_hash,
+            "source_registry_hash": source_registry_hash,
+            "spec_hash": spec_hash,
+            "candidate_spec_schema_hash": candidate_spec_schema_hash,
+            "compiler_hash": compiler_hash,
+            "interpreter_hash": interpreter_hash,
+            "runner_hash": runner_hash,
+            "scout_screen_source_hash": scout_screen_source_hash,
+            "config_fingerprint": config_fingerprint,
+            "freeze_set_hash": freeze_set_hash,
+            "era_open_evidence_class_contract": era_open_evidence_class_contract,
+            "eligible_corpus_manifest_hash": eligible_corpus_manifest_hash,
+            "recorded_at": recorded_at or _iso_utc_now(),
+        }
+        existing = self.epoch_open_row()
+        if existing is not None:
+            if all(existing[f] == candidate[f] for f in _EPOCH_OPEN_IDENTITY_FIELDS):
+                return existing
+            raise ConflictingReplayRefused(
+                "an epoch-opening (first-read-lock) row already exists with different content -- "
+                "refused rather than appending a second first-read-lock row (spec §8.5/§9.2)"
+            )
+        return self._chain.append_row(candidate)
+
     def record_terminal(
         self, *, candidate_spec_hash: str, manifest_hash: str, foundry_family_id: str,
         foundry_family_variant_count: int, screen_result: dict, rule_id: str,
diff --git a/apps/backend/app/research/foundry_runner.py b/apps/backend/app/research/foundry_runner.py
index e2df19dd..b8b524b0 100644
--- a/apps/backend/app/research/foundry_runner.py
+++ b/apps/backend/app/research/foundry_runner.py
@@ -37,6 +37,8 @@ __all__ = [
     "run_family",
     "ConcurrentRunnerRefused",
     "SingleFlightLock",
+    "EXHAUST_LOCK_FILENAME",
+    "read_exhaust_progress",
 ]
 
 # --- §7.2's mechanical, closed Scout-decision -> Foundry-state mapping (TC-17) --------------------
@@ -209,3 +211,73 @@ class SingleFlightLock:
         finally:
             fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
             fh.close()
+
+
+# === goal-hypothesis-foundry-iter-6 (J-07/J-08): the `exhaust_progress` Foundry read-surface key ===
+# -- unlike `epoch_manifest` (a Git-tracked literal path, computed once at module-import time),
+# this reflects genuinely RUNTIME-scoped state: the Foundry trial ledger the real exhaust CLI
+# writes under `get_foundry_dir()`/`TAPEOLOGY_FOUNDRY_DIR`-scoped storage, which does not exist
+# until the operator's own exhaust-CLI act runs (the SAME "read verbatim, never fabricate, degrade
+# honestly before the recording act" convention `read_era_open_baseline` already establishes).
+# `micro_routes.get_foundry()` calls this PER REQUEST (via the same `Depends(get_foundry_dir)`
+# `era_open_baseline` already uses), never once at import time -- the whole point is that it must
+# see a LATER exhaust-CLI run without a server restart.
+
+EXHAUST_LOCK_FILENAME = "foundry_exhaust_runner.lock"
+
+
+def read_exhaust_progress(foundry_dir: str | Path, *, frozen_ready_total: int) -> dict:
+    """Reads the Foundry trial ledger under ``foundry_dir`` VERBATIM (no recomputation of any
+    scientific value) and combines it with ``frozen_ready_total`` (the caller's own read of the
+    Git-tracked manifest's total ``FROZEN_READY`` variant count -- this function never opens the
+    manifest itself, so there is exactly one reader of that file, matching every other Foundry
+    subview's single-canonical-owner discipline).
+
+    ``single_flight_status`` is a genuine LIVE probe (a real, immediately-released non-blocking
+    ``SingleFlightLock`` acquire attempt against the SAME lock path the real exhaust CLI uses) --
+    cheap, read-only, and structurally incapable of computing/evaluating anything scientific (it
+    either finds the OS advisory lock free or held; nothing else). ``freeze_integrity_verdict`` is
+    NOT recomputed here (a GET route must never re-verify freeze hashes/ancestry itself -- that is
+    the exhaust CLI's own job, per-invocation): its value is a direct historical fact -- the
+    epoch-opening row could only ever have been appended AFTER the CLI's own
+    ``verify_freeze_set_unchanged``/``verify_commit_is_ancestor`` passed, so the row's mere
+    presence already proves ``"green"`` at the moment it was written; absence honestly renders
+    ``"not_yet_verified"`` (a real state the two-value schema literal ``"green" | <halt code>``
+    does not name, but the pre-lock state is real and must be representable -- never silently
+    coerced to either)."""
+    ledger = fl.FoundryLedger(foundry_dir)
+    lock_path = Path(foundry_dir) / EXHAUST_LOCK_FILENAME
+    try:
+        with SingleFlightLock(lock_path).acquire():
+            single_flight_status = "idle"
+    except ConcurrentRunnerRefused:
+        single_flight_status = "running"
+
+    epoch_open = ledger.epoch_open_row()
+    if epoch_open is None:
+        return {
+            "first_read_lock_recorded": False,
+            "first_read_lock_at": None,
+            "eligible_corpus_manifest_hash": None,
+            "frozen_ready_total": frozen_ready_total,
+            "terminal_count": 0,
+            "checkpoint_ordinal": 0,
+            "protected_read_count": 0,
+            "single_flight_status": single_flight_status,
+            "freeze_integrity_verdict": "not_yet_verified",
+            "exhaust_complete": False,
+        }
+
+    terminal_count = len([r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL])
+    return {
+        "first_read_lock_recorded": True,
+        "first_read_lock_at": epoch_open["recorded_at"],
+        "eligible_corpus_manifest_hash": epoch_open["eligible_corpus_manifest_hash"],
+        "frozen_ready_total": frozen_ready_total,
+        "terminal_count": terminal_count,
+        "checkpoint_ordinal": terminal_count,
+        "protected_read_count": 0,
+        "single_flight_status": single_flight_status,
+        "freeze_integrity_verdict": "green",
+        "exhaust_complete": terminal_count >= frozen_ready_total,
+    }
diff --git a/apps/backend/app/research/micro_routes.py b/apps/backend/app/research/micro_routes.py
index 19651d0b..a18a6968 100644
--- a/apps/backend/app/research/micro_routes.py
+++ b/apps/backend/app/research/micro_routes.py
@@ -54,6 +54,7 @@ from .foundry_compiler import sources_compiler_hermetic_fixture_view
 from .foundry_freeze import freeze_integrity_hermetic_fixture_view, verify_commit_is_ancestor
 from .foundry_hermetic_summary import build_hermetic_oracles_summary
 from .foundry_interpreter import interpreter_hermetic_fixture_view
+from .foundry_runner import read_exhaust_progress
 from .foundry_source_registry import (
     foundry_era_identity,
     read_era_open_baseline,
@@ -893,6 +894,11 @@ _HERMETIC_ORACLES_VIEW = build_hermetic_oracles_summary()
 # goal-hypothesis-foundry-iter-5 (J-06): computed once, same convention, but reads real committed
 # files rather than hermetic literals -- see `read_epoch_manifest_view`'s own docstring.
 _EPOCH_MANIFEST_VIEW = read_epoch_manifest_view()
+# goal-hypothesis-foundry-iter-6 (J-07): the ONE Git-tracked fact `exhaust_progress` needs from the
+# real committed manifest -- the total `FROZEN_READY` variant count across every family. Derived
+# from the SAME `_EPOCH_MANIFEST_VIEW` object already computed above (no second manifest read), so
+# there remains exactly one canonical reader of the tracked manifest file.
+_FOUNDRY_FROZEN_READY_TOTAL = sum(f["variant_count"] for f in _EPOCH_MANIFEST_VIEW.get("families", []))
 
 
 @router.get("/foundry")
@@ -915,7 +921,13 @@ def get_foundry(foundry_dir: str = Depends(get_foundry_dir)) -> dict:
     goal-hypothesis-foundry-iter-5: one more additive top-level key, ``epoch_manifest`` -- the
     real, Git-tracked epoch (see ``read_epoch_manifest_view``'s own docstring for why it reads
     literal repo-relative paths rather than the dataset-scoped `foundry_dir` this handler still
-    receives for the (unrelated) era-open baseline)."""
+    receives for the (unrelated) era-open baseline).
+
+    goal-hypothesis-foundry-iter-6 (J-07): one more additive top-level key, ``exhaust_progress`` --
+    UNLIKE ``epoch_manifest``, this reflects genuinely runtime-scoped state (the Foundry trial
+    ledger the real exhaust CLI writes under this SAME ``foundry_dir``), so it is read PER REQUEST
+    (``foundry_runner.read_exhaust_progress``, verbatim, no recomputation of any scientific value)
+    rather than once at import time -- see that function's own docstring."""
     return {
         "era": foundry_era_identity(),
         "era_open_baseline": read_era_open_baseline(foundry_dir),
@@ -926,4 +938,5 @@ def get_foundry(foundry_dir: str = Depends(get_foundry_dir)) -> dict:
         "interpreter_fixtures": _INTERPRETER_FIXTURES_VIEW,
         "freeze_integrity": _FREEZE_INTEGRITY_VIEW,
         "hermetic_oracles": _HERMETIC_ORACLES_VIEW,
+        "exhaust_progress": read_exhaust_progress(foundry_dir, frozen_ready_total=_FOUNDRY_FROZEN_READY_TOTAL),
     }
diff --git a/apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py b/apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py
index 2fdbda93..972a363a 100644
--- a/apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py
+++ b/apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py
@@ -14,11 +14,17 @@ stderr, no implicit git operations: this script never runs ``git add``/``git com
 2. Runs ``foundry_compiler.compile_sources`` over this real batch (no new compiler module, no new
    disposition path -- the exact same mechanical §2 precedence the hermetic fixtures already prove).
 3. Calls ``foundry_freeze.generate_or_verify_manifest`` to mint (or verify/replay) the real
-   ``epoch_id``/``manifest_hash``, ``foundry_freeze.generate_freeze_set`` to build the enumerated
-   path+sha256 freeze-set manifest over the real ``apps/backend/app/research`` directory plus the
-   methodology spec, and ``foundry_freeze.build_freeze_record`` to pin every required hash.
-4. Writes ``docs/hypothesis-foundry/{source-registry,epoch-manifest,freeze-set,freeze-record}.json``
-   at the tracked §8.2 paths.
+   ``epoch_id``/``manifest_hash``.
+4. Writes ``source-registry.json``/``epoch-manifest.json`` FIRST (goal-hypothesis-foundry-iter-6:
+   moved ahead of the freeze-set/freeze-record step so both tracked JSONs already exist on disk
+   when ``foundry_freeze.generate_freeze_set`` scans and hashes them -- closes audit finding B7's
+   freeze-set half). Then calls ``generate_freeze_set`` (repo-relative keys, closing B1) over the
+   real ``apps/backend/app/research`` directory plus ``FREEZE_SET_EXTRA_PATHS`` (the spec, the two
+   just-written tracked JSONs, and both the generation/exhaust CLI scripts -- see that constant's
+   own module-level comment for why ``freeze-record.json``/``freeze-set.json`` themselves are
+   deliberately NOT among them), then ``build_freeze_record`` to pin every required hash plus the
+   §8.4 "era-open evidence-class contract" field (closing B7's freeze-record half), then writes
+   ``freeze-set.json``/``freeze-record.json``.
 5. Records this run's own outcome-access census (a dynamic call-trace over the actual compile/
    freeze-generation calls, counting every function CALL whose defining module is one of the
    forbidden Scout-ledger/walk-forward/Vault/Referee/PnL/Foundry-runner modules) -- must be ``0``,
@@ -80,6 +86,7 @@ load_env()
 from app.config import CONFIG  # noqa: E402
 from app.research import foundry_compiler as fc  # noqa: E402
 from app.research import foundry_freeze as fz  # noqa: E402
+from app.research import scout  # noqa: E402
 from app.research.foundry_source_registry import (  # noqa: E402
     DISPOSITION_ALIASED_VARIANT_VOCABULARY,
     DISPOSITION_EXCLUDED_GATE_CLOSED,
@@ -105,6 +112,21 @@ FREEZE_SET_PATH = FOUNDRY_DOCS_DIR / "freeze-set.json"
 FREEZE_RECORD_PATH = FOUNDRY_DOCS_DIR / "freeze-record.json"
 AUDIT_REPORT_PATH = FOUNDRY_REPORTS_DIR / "source-registry-audit.md"
 SPEC_PATH = REPO_ROOT / "docs" / "hypothesis-foundry-spec.md"
+# goal-hypothesis-foundry-iter-6 (closes audit finding B7's freeze-set half). §8.4's own text names
+# "the Foundry methodology/spec and tracked registry/manifest files" -- the tracked REGISTRY and
+# MANIFEST are `source-registry.json`/`epoch-manifest.json`, never `freeze-record.json`/
+# `freeze-set.json` themselves (§8.4 never names either of those two as freeze-set members, and
+# freeze-record.json COULD NOT be: its own content embeds `freeze_set_hash`, so including its file
+# hash inside the very freeze-set that hash is computed over is the identical self-reference
+# freeze-set.json is already, explicitly, excluded for -- just one hop removed). "every Foundry
+# scientific implementation module/CLI" additionally covers the real generation CLI (this script)
+# and the real exhaust CLI (`run_hypothesis_foundry_real_exhaust.py`) -- both science-affecting,
+# neither a sibling `app/research/*.py` import the scanner would auto-discover.
+EXHAUST_CLI_PATH = BACKEND_DIR / "scripts" / "run_hypothesis_foundry_real_exhaust.py"
+_THIS_GENERATION_CLI_PATH = Path(__file__).resolve()
+FREEZE_SET_EXTRA_PATHS = (
+    SPEC_PATH, SOURCE_REGISTRY_PATH, EPOCH_MANIFEST_PATH, _THIS_GENERATION_CLI_PATH, EXHAUST_CLI_PATH,
+)
 
 # --- §8.1's own import/IO tripwire: every module whose FUNCTIONS could hand this script a real
 # candidate outcome, Scout row, walk-forward result, Vault state, Referee result, or PnL scan.
@@ -855,12 +877,35 @@ def _existing_freeze_commit(path: Path) -> str | None:
     return payload.get("freeze_commit")
 
 
+class ManifestStoreMissingError(Exception):
+    """goal-hypothesis-foundry-iter-6 (TC-7). ``docs/hypothesis-foundry/epoch-manifest.json`` --
+    the ONLY state this script reads to decide "has an epoch already been generated" -- is absent,
+    but a SIBLING tracked artifact (``freeze-record.json``, always written in the SAME generation
+    run immediately after the manifest) proves a real generation already happened. Silently
+    treating this as "no epoch yet" would hand ``generate_or_verify_manifest`` an EMPTY store --
+    which accepts whatever the CURRENT inputs happen to be as if this were the first-ever
+    generation, with no drift check against what was actually frozen before (the drift check only
+    fires when an EXISTING slot disagrees with the new inputs -- an empty slot has nothing to
+    disagree with). That would silently overwrite ``epoch-manifest.json`` rather than genuinely
+    verifying/refusing. Refused instead: restore ``epoch-manifest.json`` from Git history before
+    re-running this script."""
+
+
 def _load_existing_manifest_store(path: Path) -> dict:
     """Reconstructs the ``generate_or_verify_manifest`` in-memory ``store`` from a previously
     written ``epoch-manifest.json`` (if present) -- so a re-run replay-verifies rather than
     silently starting from an empty store (which would look like "no epoch yet" and mint a new
-    one). Returns ``{}`` (a genuinely fresh store) when no file exists yet."""
+    one). Returns ``{}`` (a genuinely fresh store) only on the FIRST-EVER generation (neither this
+    file nor its sibling ``freeze-record.json`` exists yet); raises ``ManifestStoreMissingError``
+    when this file specifically has gone missing while ``freeze-record.json`` still stands as
+    evidence a generation already happened (TC-7) -- see that exception's own docstring."""
     if not path.exists():
+        if FREEZE_RECORD_PATH.exists():
+            raise ManifestStoreMissingError(
+                f"{path} is missing, but {FREEZE_RECORD_PATH} exists -- a prior real-epoch "
+                "generation is already on record and its own replay-detection state must not be "
+                "silently treated as a fresh install (spec §8.1: at most one real epoch_id ever)"
+            )
         return {}
     payload = json.loads(path.read_text(encoding="utf-8"))
     if "epoch_id" not in payload or "_inputs_hash" not in payload:
@@ -874,7 +919,25 @@ def _load_existing_manifest_store(path: Path) -> dict:
     return {"epoch": record}
 
 
-def main() -> int:
+def main(argv: list[str] | None = None) -> int:
+    import argparse
+
+    parser = argparse.ArgumentParser(description=__doc__)
+    parser.add_argument(
+        "--advance-freeze-commit", action="store_true",
+        help=(
+            "goal-hypothesis-foundry-iter-6 (closes audit finding B2): recompute `freeze_commit` "
+            "from the CURRENT `git rev-parse HEAD` instead of reusing the existing pinned value. "
+            "An explicit, disclosed operator act -- default OFF, so an ordinary replay/verify run "
+            "still treats `freeze_commit` as pinned once and never silently advanced. Pass this "
+            "flag ONLY for a deliberate freeze-bookkeeping repair, run strictly inside spec §7.3's "
+            "'before any real outcome has been read' window, immediately after the repairing code "
+            "changes have themselves been committed (so the new HEAD genuinely contains their "
+            "bytes) and strictly BEFORE the real exhaust CLI's first invocation."
+        ),
+    )
+    args = parser.parse_args(argv)
+
     records = build_real_source_records()
 
     # --- §1.4 mechanical lints + §2 dispositions + §8.1 outcome-access tripwire, all traced ------
@@ -909,36 +972,11 @@ def main() -> int:
         manifest_record = fz.generate_or_verify_manifest(store, generation_inputs)
         epoch_id = manifest_record.epoch_id
         is_replay = "epoch" in _load_existing_manifest_store(EPOCH_MANIFEST_PATH)
-
-        # --- §8.4 freeze-set: the real `apps/backend/app/research` directory + the spec. --------
-        freeze_set = fz.generate_freeze_set(
-            BACKEND_DIR / "app" / "research", extra_paths=(SPEC_PATH,)
-        )
-
-        # --- §8.4 freeze record: pins every required science hash. `candidate_spec_schema_hash`
-        # is deliberately equal to `compiler_hash` -- the CandidateSpec dataclass is defined
-        # INSIDE foundry_compiler.py and no separate schema module exists this era, so the
-        # schema's own identity IS that file's hash; a future era's genuine schema separation
-        # would produce a distinct value.
+        # `candidate_spec_schema_hash` is deliberately equal to `compiler_hash` -- the
+        # CandidateSpec dataclass is defined INSIDE foundry_compiler.py and no separate schema
+        # module exists this era, so the schema's own identity IS that file's hash; a future era's
+        # genuine schema separation would produce a distinct value.
         compiler_hash_value = fc.compiler_hash()
-        # `freeze_commit` is pinned ONCE, on the very first generation, and never recomputed on a
-        # later replay/verify run -- a freeze whose own commit identity silently advanced on every
-        # re-run would not be a freeze. `_existing_freeze_commit` is `None` only before the first
-        # generation this repository has ever produced.
-        freeze_commit = _existing_freeze_commit(FREEZE_RECORD_PATH) or _git("rev-parse", "HEAD")
-        freeze_record = fz.build_freeze_record(
-            freeze_commit=freeze_commit,
-            manifest_hash=manifest_record.manifest_hash,
-            source_registry_hash=result.source_registry_hash,
-            spec_hash=_hash_file(SPEC_PATH),
-            candidate_spec_schema_hash=compiler_hash_value,
-            compiler_hash=compiler_hash_value,
-            interpreter_hash=_hash_file(BACKEND_DIR / "app" / "research" / "foundry_interpreter.py"),
-            runner_hash=_hash_file(BACKEND_DIR / "app" / "research" / "foundry_runner.py"),
-            scout_screen_source_hash=_hash_file(BACKEND_DIR / "app" / "research" / "scout.py"),
-            config_fingerprint=CONFIG.config_fingerprint(),
-            freeze_set_hash=freeze_set["freeze_set_hash"],
-        )
 
     census = len(hits)
     if census != 0:
@@ -985,6 +1023,47 @@ def main() -> int:
         json.dumps(epoch_manifest_payload, indent=2, sort_keys=True), encoding="utf-8"
     )
 
+    # --- §8.4 freeze-set: goal-hypothesis-foundry-iter-6 (closes B1/B2/B7's freeze-set half). ------
+    # Computed AFTER `source-registry.json`/`epoch-manifest.json` are on disk (both are covered
+    # entries -- see `FREEZE_SET_EXTRA_PATHS`'s own module-level comment for why `freeze-record.json`
+    # is deliberately NOT one of them), and keyed REPO-RELATIVE (`repo_root=REPO_ROOT`) rather than
+    # by this machine's absolute path -- portable across checkouts/worktrees at the same commit.
+    freeze_set = fz.generate_freeze_set(
+        BACKEND_DIR / "app" / "research", extra_paths=FREEZE_SET_EXTRA_PATHS, repo_root=REPO_ROOT,
+    )
+
+    # --- §8.4 freeze record: pins every required science hash. `freeze_commit` is pinned ONCE, on
+    # the very first generation, and never recomputed on a later replay/verify run -- a freeze whose
+    # own commit identity silently advanced on every re-run would not be a freeze.
+    # `_existing_freeze_commit` is `None` only before the first generation this repository has ever
+    # produced. goal-hypothesis-foundry-iter-6 (closes B2): `--advance-freeze-commit` forces a
+    # fresh `git rev-parse HEAD` even when a prior pinned value exists -- this iteration's own
+    # regeneration passes it explicitly, run AFTER this iteration's code changes are committed (see
+    # NOTES in this module's own docstring), so the freshly-resolved `freeze_commit` is a real
+    # ancestor commit that already contains every pinned science file's bytes -- never a stale,
+    # pre-code-commit hash.
+    freeze_commit = (
+        _git("rev-parse", "HEAD") if args.advance_freeze_commit
+        else _existing_freeze_commit(FREEZE_RECORD_PATH) or _git("rev-parse", "HEAD")
+    )
+    freeze_record = fz.build_freeze_record(
+        freeze_commit=freeze_commit,
+        manifest_hash=manifest_record.manifest_hash,
+        source_registry_hash=result.source_registry_hash,
+        spec_hash=_hash_file(SPEC_PATH),
+        candidate_spec_schema_hash=compiler_hash_value,
+        compiler_hash=compiler_hash_value,
+        interpreter_hash=_hash_file(BACKEND_DIR / "app" / "research" / "foundry_interpreter.py"),
+        runner_hash=_hash_file(BACKEND_DIR / "app" / "research" / "foundry_runner.py"),
+        scout_screen_source_hash=_hash_file(BACKEND_DIR / "app" / "research" / "scout.py"),
+        config_fingerprint=CONFIG.config_fingerprint(),
+        freeze_set_hash=freeze_set["freeze_set_hash"],
+        # goal-hypothesis-foundry-iter-6 (closes B7's freeze-record half). §10.1/goal.md Success
+        # Criteria 16: every real Foundry evaluation this era is constitutionally locked to the ONE
+        # `historical_exposed_diagnostic` evidence class -- the frozen contract, not a hash.
+        era_open_evidence_class_contract=scout.EVIDENCE_CLASS_HISTORICAL_EXPOSED_DIAGNOSTIC,
+    )
+
     FREEZE_SET_PATH.write_text(json.dumps(freeze_set, indent=2, sort_keys=True), encoding="utf-8")
 
     freeze_record_payload = {
@@ -999,6 +1078,7 @@ def main() -> int:
         "scout_screen_source_hash": freeze_record.scout_screen_source_hash,
         "config_fingerprint": freeze_record.config_fingerprint,
         "freeze_set_hash": freeze_record.freeze_set_hash,
+        "era_open_evidence_class_contract": freeze_record.era_open_evidence_class_contract,
     }
     FREEZE_RECORD_PATH.write_text(
         json.dumps(freeze_record_payload, indent=2, sort_keys=True), encoding="utf-8"
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
diff --git a/apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py b/apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py
new file mode 100644
index 00000000..885e6003
--- /dev/null
+++ b/apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py
@@ -0,0 +1,308 @@
+"""Runs the Hypothesis Foundry's real deterministic exhaust pass (goal-hypothesis-foundry-iter-6,
+Binding Execution Order step 8, J-07) -- the resumable, single-flight CLI/manager operator act
+spec §9 requires, over the ONE real, Git-frozen epoch (§8.1) iter-5/iter-6 already committed.
+Following ``generate_hypothesis_foundry_real_epoch.py``'s own convention (argparse, prints a
+summary to stderr, no implicit git operations).
+
+**What this script does, in order (§9.1/§8.5):**
+
+1. Verifies freeze integrity: recomputes every pinned freeze-set path's sha256
+   (``foundry_freeze.verify_freeze_set_unchanged``) and proves ``freeze_commit`` is an ancestor of
+   ``HEAD`` (``foundry_freeze.verify_commit_is_ancestor``). Refuses BEFORE anything else runs.
+2. Acquires ``foundry_runner.SingleFlightLock`` -- a concurrent second invocation raises
+   ``foundry_runner.ConcurrentRunnerRefused`` and appends no ledger row.
+3. Computes the resolved eligible diagnostic-corpus ``(dataset_id, checksum)`` manifest hash
+   through the SAME sanctioned data door every other corpus-wide enumerator in this codebase
+   shares (``datasets.DatasetStore.list()`` + ``micro_snapshots.exclude_withheld`` --
+   ``pnl_scan._verified_corpus``'s own precedent) and ``micro_corpus.corpus_manifest_hash`` (the
+   EXISTING scientific-identity hash formula -- never a second one invented here). This reads ONLY
+   dataset METADATA (id, checksum, symbol, window) -- no snapshot row, no event, is ever read, so
+   this step alone already proves the era's own protected-read-zero property structurally.
+4. Appends the ONE epoch-opening / first-read-lock row (``foundry_ledger.FoundryLedger.
+   record_epoch_open``) BEFORE any candidate outcome could ever be read -- idempotent on replay
+   (a second invocation verifies and no-ops rather than appending a second lock row).
+5. Iterates every ``FROZEN_READY`` variant in the frozen manifest's own family/variant order
+   through ``foundry_runner.run_family``/``run_one_candidate`` -- the real runner+ledger path, not
+   a fixture stand-in. The one real epoch's own committed ``epoch-manifest.json`` carries
+   ``families: []`` (§8.1: every one of the 11 required sources disposed non-COMPILED), so this
+   step completes honestly with zero terminal evaluations -- see ``_default_frozen_ready_families``
+   and ``RealCandidateEvaluationUnsupported`` below for why real per-family CandidateSpec/anchor
+   reconstruction from the exposed corpus is a deliberately unbuilt, fail-closed path this era: it
+   is never reached against the real committed manifest, so building it now would be new
+   candidate-construction machinery for a state this era's one epoch cannot reach.
+6. Reports the checkpoint ordinal and a zero protected/withheld/sealed read census.
+
+**Repeat invocation.** Verifies and no-ops (TC-2): the epoch-opening row already exists, every
+already-terminal candidate is verified and skipped, no new ledger row is appended for anything
+that already reached a terminal state.
+
+**Resume-after-crash / fixture-backed proofs.** ``run_real_exhaust``'s ``frozen_ready_families``
+parameter lets a caller inject its own ``(FoundryFamily, [(CandidateSpec, anchors), ...])`` plan
+(hermetic fixture data, exactly the discipline ``foundry_hermetic_summary.py`` already uses) to
+exercise ``run_family``/``run_one_candidate``'s already-proven crash-resume/canonical-order
+machinery (``test_foundry_runner.py``'s ``test_tc15_...``/``test_tc16_...``) THROUGH this exact
+same freeze-verify -> single-flight -> corpus-hash -> epoch-open -> exhaust sequence, without
+requiring real anchor extraction from real snapshot data (which does not exist and is not needed
+this era -- see point 5 above). J-07 step 7 itself permits this: "do not attempt to simulate an
+interrupt against the real epoch, which has zero variants to interrupt mid-evaluation anyway."
+
+Run from ``apps/backend`` after the freeze-set/freeze-record regeneration has been committed:
+
+    .venv/bin/python scripts/run_hypothesis_foundry_real_exhaust.py
+"""
+
+from __future__ import annotations
+
+import argparse
+import json
+import subprocess
+import sys
+from pathlib import Path
+from typing import Callable, Sequence
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = Path(__file__).resolve().parents[3]
+sys.path.insert(0, str(BACKEND_DIR))
+
+from app.env import load_env  # noqa: E402
+
+load_env()
+
+from app.config import CONFIG  # noqa: E402
+from app.research import foundry_family as ffam  # noqa: E402
+from app.research import foundry_freeze as fz  # noqa: E402
+from app.research import foundry_ledger as fl  # noqa: E402
+from app.research import foundry_runner as fr  # noqa: E402
+from app.research import micro_corpus  # noqa: E402
+from app.research.datasets import DatasetStore  # noqa: E402
+from app.research.foundry_source_registry import resolve_foundry_dir  # noqa: E402
+from app.research.micro_snapshots import exclude_withheld  # noqa: E402
+
+FOUNDRY_DOCS_DIR = REPO_ROOT / "docs" / "hypothesis-foundry"
+EPOCH_MANIFEST_PATH = FOUNDRY_DOCS_DIR / "epoch-manifest.json"
+FREEZE_SET_PATH = FOUNDRY_DOCS_DIR / "freeze-set.json"
+FREEZE_RECORD_PATH = FOUNDRY_DOCS_DIR / "freeze-record.json"
+
+# The single-flight lock file lives beside the Foundry trial ledger itself (same runtime-scoped
+# storage, `get_foundry_dir()`/`TAPEOLOGY_FOUNDRY_DIR`). Defined ONCE, in `foundry_runner.py`
+# (`EXHAUST_LOCK_FILENAME`), so `micro_routes.py`'s own live lock probe for
+# `exhaust_progress.single_flight_status` targets the IDENTICAL filename this script uses -- never
+# a second, independently-typed literal that could silently drift out of sync.
+LOCK_FILENAME = fr.EXHAUST_LOCK_FILENAME
+
+# A placeholder econ-floor rule -- ONLY ever passed to `run_family` inside the (this epoch, always
+# empty) FROZEN_READY loop below; §6's real numeric-floor derivation is candidate-specific and this
+# era's one real epoch has no candidate to derive one for. Present so the call shape matches
+# `run_family`'s real signature; never read for a candidate that is never evaluated.
+_UNUSED_PLACEHOLDER_ECON_FLOOR = {
+    "floor_bps": 0.0, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 0.0,
+}
+
+
+class FreezeAncestryUnproven(Exception):
+    """§8.4: ``freeze_commit`` failed to verify as an ancestor of ``HEAD`` -- the pre-outcome
+    Git-visible commit barrier is not proven. Refused before any epoch-opening row is written
+    (never after -- see spec §7.3/§9.3: this is an integrity halt, not something to patch and
+    continue past)."""
+
+
+class DatasetIntegrityFailure(Exception):
+    """The sanctioned data door (``datasets.DatasetStore.list()``) reported a dataset file failing
+    checksum verification -- the eligible-corpus enumeration refuses rather than silently excluding
+    a corrupt/tampered file from the corpus it reports (the ``pnl_scan._verified_corpus`` precedent:
+    "a partial report is a misleading report")."""
+
+
+class RealCandidateEvaluationUnsupported(Exception):
+    """goal-hypothesis-foundry-iter-6: real per-family CandidateSpec/anchor reconstruction from the
+    exposed diagnostic corpus is deliberately unbuilt. The one real epoch this era will ever
+    generate (goal.md §8.1) is frozen with ``families: []`` (every one of the 11 required sources
+    disposed non-COMPILED this era -- see ``reports/hypothesis-foundry/source-registry-audit.md``),
+    so this exception is never raised against the real committed manifest; it exists purely so a
+    hypothetically widened manifest fails CLOSED rather than being silently mis-evaluated by
+    unbuilt, unproven logic. A future methodology era that compiles real candidates must implement
+    and hermetically prove real anchor extraction before this CLI can run its exhaust pass over
+    them -- that is new scientific-construction work this era's own "no candidate rescue" (§9.3)
+    and "no new science this epoch" boundaries explicitly place out of scope."""
+
+
+def _git_rev_parse_head(repo_root: Path) -> str | None:
+    try:
+        result = subprocess.run(
+            ["git", "rev-parse", "HEAD"], cwd=str(repo_root), capture_output=True, text=True
+        )
+    except OSError:
+        return None
+    return result.stdout.strip() if result.returncode == 0 else None
+
+
+def compute_eligible_corpus(dataset_dir: str) -> dict:
+    """§10.1: "use the sanctioned micro accessor/data door; call existing withheld exclusion
+    machinery" -- the SAME ``DatasetStore.list()`` + ``micro_snapshots.exclude_withheld`` choke
+    point every other corpus-wide enumerator in this codebase already shares
+    (``pnl_scan._verified_corpus``, ``desk_screen.py``, ``edge_report_cache.py``). Hashed with the
+    EXISTING ``micro_corpus.corpus_manifest_hash`` formula -- never a second one invented here.
+
+    Reads ONLY already-verified dataset METADATA (id, checksum, symbol, window) -- never a snapshot
+    row, never an event -- so this function alone already proves the era's own zero-protected-read
+    property structurally: nothing here can touch a sealed shard's content, because nothing here
+    ever calls ``micro_accessor.MicroAccessor.read_snapshot_rows``."""
+    store = DatasetStore(dataset_dir)
+    records, errors = store.list()
+    if errors:
+        raise DatasetIntegrityFailure(
+            f"{len(errors)} dataset file(s) failed integrity verification "
+            f"({[e['file'] for e in errors]}) -- the exhaust run stops before any epoch-opening row"
+        )
+    kept, withheld_excluded = exclude_withheld(records, store)
+    members = [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in kept]
+    return {
+        "manifest_hash": micro_corpus.corpus_manifest_hash(members),
+        "member_count": len(members),
+        "withheld_excluded": withheld_excluded,
+    }
+
+
+def _default_frozen_ready_families(
+    manifest: dict,
+) -> list[tuple[ffam.FoundryFamily, list]]:
+    """The default variant-plan resolver ``run_real_exhaust`` uses against the REAL committed
+    manifest. For every family entry the manifest carries: a family with zero variants reaches the
+    same honest, real ``run_family`` completion (called with an empty variant list) that
+    ``foundry_hermetic_summary._all_blocked_epoch_completed`` already proves for this exact shape;
+    a family carrying ANY variant raises ``RealCandidateEvaluationUnsupported`` (see that
+    exception's own docstring) rather than being silently skipped or mis-evaluated. The real
+    committed manifest's own ``families`` list is ``[]`` (§8.1), so this function's own loop body
+    never executes against real data -- present so the exhaust sequence's own generic shape is
+    real and testable against injected fixture plans (see this module's own docstring)."""
+    plan: list[tuple[ffam.FoundryFamily, list]] = []
+    for family_manifest in manifest.get("families", []):
+        variant_views = family_manifest.get("variants", [])
+        family_id = family_manifest["foundry_family_id"]
+        if variant_views:
+            raise RealCandidateEvaluationUnsupported(
+                f"family {family_id!r} carries {len(variant_views)} FROZEN_READY variant(s), but "
+                "real per-family CandidateSpec/anchor reconstruction was never built this era -- "
+                "refused rather than silently mis-evaluated"
+            )
+        family = ffam.build_family_registry({family_id: []})[family_id]
+        plan.append((family, []))
+    return plan
+
+
+def run_real_exhaust(
+    *,
+    tracked_dir: Path = FOUNDRY_DOCS_DIR,
+    repo_root: Path = REPO_ROOT,
+    dataset_dir: str | None = None,
+    foundry_dir: str | None = None,
+    lock_path: Path | None = None,
+    frozen_ready_families: Callable[[dict], list[tuple[ffam.FoundryFamily, Sequence]]] | None = None,
+) -> dict:
+    """The core, testable exhaust sequence (§9.1-§9.2/§8.5) -- see this module's own docstring for
+    the six ordered steps. Every path parameter defaults to the REAL production location; a test
+    overrides ``tracked_dir``/``repo_root``/``dataset_dir``/``foundry_dir``/``lock_path`` to point
+    at a hermetic fixture tree, and/or ``frozen_ready_families`` to inject a fixture variant plan,
+    without touching any real file."""
+    dataset_dir = dataset_dir if dataset_dir is not None else CONFIG.dataset_dir_resolved()
+    foundry_dir = foundry_dir if foundry_dir is not None else resolve_foundry_dir(dataset_dir)
+    lock_path = lock_path if lock_path is not None else Path(foundry_dir) / LOCK_FILENAME
+    resolver = frozen_ready_families or _default_frozen_ready_families
+
+    freeze_set = json.loads((tracked_dir / "freeze-set.json").read_text(encoding="utf-8"))
+    freeze_record = json.loads((tracked_dir / "freeze-record.json").read_text(encoding="utf-8"))
+    manifest = json.loads((tracked_dir / "epoch-manifest.json").read_text(encoding="utf-8"))
+
+    # --- step 1 (§9.1/§8.5): verify freeze integrity BEFORE anything else runs -------------------
+    fz.verify_freeze_set_unchanged(freeze_set, repo_root=repo_root)
+    head = _git_rev_parse_head(repo_root)
+    if not head or not fz.verify_commit_is_ancestor(freeze_record["freeze_commit"], head, cwd=repo_root):
+        raise FreezeAncestryUnproven(
+            f"freeze_commit {freeze_record.get('freeze_commit')!r} did not verify as an ancestor "
+            f"of HEAD ({head!r}) -- refused before any epoch-opening row is written"
+        )
+
+    frozen_ready_total = sum(len(fm.get("variants", [])) for fm in manifest.get("families", []))
+
+    # --- step 2 (§9): single-flight -- a concurrent second invocation raises here, no ledger row --
+    lock = fr.SingleFlightLock(lock_path)
+    with lock.acquire():
+        # --- step 3 (§10.1): resolved eligible-corpus manifest hash, sanctioned door only --------
+        corpus = compute_eligible_corpus(dataset_dir)
+
+        # --- step 4 (§8.5): the ONE epoch-opening / first-read-lock row, idempotent on replay ----
+        ledger = fl.FoundryLedger(foundry_dir)
+        epoch_open = ledger.record_epoch_open(
+            epoch_id=manifest["epoch_id"],
+            freeze_commit=freeze_record["freeze_commit"],
+            manifest_hash=freeze_record["manifest_hash"],
+            source_registry_hash=freeze_record["source_registry_hash"],
+            spec_hash=freeze_record["spec_hash"],
+            candidate_spec_schema_hash=freeze_record["candidate_spec_schema_hash"],
+            compiler_hash=freeze_record["compiler_hash"],
+            interpreter_hash=freeze_record["interpreter_hash"],
+            runner_hash=freeze_record["runner_hash"],
+            scout_screen_source_hash=freeze_record["scout_screen_source_hash"],
+            config_fingerprint=freeze_record["config_fingerprint"],
+            freeze_set_hash=freeze_record["freeze_set_hash"],
+            era_open_evidence_class_contract=freeze_record["era_open_evidence_class_contract"],
+            eligible_corpus_manifest_hash=corpus["manifest_hash"],
+        )
+
+        # --- step 5 (§9.1): exhaust every FROZEN_READY variant in canonical family/variant order -
+        family_variant_plan = resolver(manifest)
+        for family, variants in family_variant_plan:
+            fr.run_family(
+                family, variants, ledger=ledger, econ_floor=_UNUSED_PLACEHOLDER_ECON_FLOOR,
+                manifest_hash=freeze_record["manifest_hash"],
+            )
+
+        terminal_count = len([r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL])
+
+    return {
+        "epoch_id": manifest["epoch_id"],
+        "epoch_open": epoch_open,
+        "eligible_corpus_manifest_hash": corpus["manifest_hash"],
+        "eligible_corpus_member_count": corpus["member_count"],
+        "withheld_excluded": corpus["withheld_excluded"],
+        "frozen_ready_total": frozen_ready_total,
+        "terminal_count": terminal_count,
+        "checkpoint_ordinal": terminal_count,
+        # §10.2/§20: nothing above ever calls the snapshot-row accessor -- zero by construction,
+        # not by a runtime count that could silently drift from what actually happened.
+        "protected_read_count": 0,
+        "exhaust_complete": terminal_count >= frozen_ready_total,
+    }
+
+
+def main(argv: list[str] | None = None) -> int:
+    parser = argparse.ArgumentParser(description=__doc__)
+    parser.parse_args(argv)
+
+    try:
+        result = run_real_exhaust()
+    except fr.ConcurrentRunnerRefused as exc:
+        print(f"[run-hypothesis-foundry-real-exhaust] REFUSED (concurrent runner): {exc}", file=sys.stderr)
+        return 1
+    except (FreezeAncestryUnproven, fz.FreezeIntegrityHalt, DatasetIntegrityFailure) as exc:
+        print(f"[run-hypothesis-foundry-real-exhaust] INTEGRITY HALT: {exc}", file=sys.stderr)
+        return 1
+
+    print(
+        f"[run-hypothesis-foundry-real-exhaust] epoch_id={result['epoch_id']}\n"
+        f"  first_read_lock_recorded_at={result['epoch_open']['recorded_at']}\n"
+        f"  eligible_corpus_manifest_hash={result['eligible_corpus_manifest_hash']}\n"
+        f"  eligible_corpus_member_count={result['eligible_corpus_member_count']}\n"
+        f"  withheld_excluded={result['withheld_excluded']}\n"
+        f"  frozen_ready_total={result['frozen_ready_total']}\n"
+        f"  terminal_count={result['terminal_count']}\n"
+        f"  checkpoint_ordinal={result['checkpoint_ordinal']}\n"
+        f"  protected_read_count={result['protected_read_count']}\n"
+        f"  exhaust_complete={result['exhaust_complete']}",
+        file=sys.stderr,
+    )
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/apps/backend/tests/test_foundry_freeze.py b/apps/backend/tests/test_foundry_freeze.py
index cc3a4783..87de6660 100644
--- a/apps/backend/tests/test_foundry_freeze.py
+++ b/apps/backend/tests/test_foundry_freeze.py
@@ -6,6 +6,7 @@ the first-read-lock drift check (§8.5). TC-11/TC-12/TC-13 in
 from __future__ import annotations
 
 import subprocess
+from pathlib import Path
 
 import pytest
 
@@ -86,15 +87,54 @@ def test_tc12_freeze_record_pins_all_required_hashes_and_commit_ancestry():
         scout_screen_source_hash="ssh",
         config_fingerprint="fp",
         freeze_set_hash="fsh",
+        era_open_evidence_class_contract="historical_exposed_diagnostic",
     )
     for field in (
         "freeze_commit", "manifest_hash", "source_registry_hash", "spec_hash",
         "candidate_spec_schema_hash", "compiler_hash", "interpreter_hash", "runner_hash",
         "scout_screen_source_hash", "config_fingerprint", "freeze_set_hash",
+        "era_open_evidence_class_contract",
     ):
         assert getattr(record, field)
 
 
+# --- goal-hypothesis-foundry-iter-6 (closes audit finding B1): repo-relative freeze-set keys ------
+
+
+def test_repo_relative_freeze_set_keys_when_repo_root_is_given(tmp_path):
+    """``generate_freeze_set(..., repo_root=...)`` keys entries REPO-RELATIVE when the scanned
+    files live under that root, and ``verify_freeze_set_unchanged(..., repo_root=...)`` resolves
+    those relative keys back correctly."""
+    repo_root = tmp_path / "repo"
+    research_dir = repo_root / "apps" / "backend" / "app" / "research"
+    research_dir.mkdir(parents=True)
+    for name in fz.FREEZE_SET_REQUIRED_MODULES:
+        (research_dir / name).write_text("# stub\n", encoding="utf-8")
+
+    result = fz.generate_freeze_set(research_dir, repo_root=repo_root)
+    for key in result["entries"]:
+        assert not key.startswith("/"), f"expected a repo-relative key, got absolute: {key}"
+        assert key.startswith("apps/backend/app/research/"), key
+
+    fz.verify_freeze_set_unchanged(result, repo_root=repo_root)  # must not raise
+
+    (research_dir / fz.FREEZE_SET_REQUIRED_MODULES[0]).write_text("# tampered\n", encoding="utf-8")
+    with pytest.raises(fz.FreezeIntegrityHalt):
+        fz.verify_freeze_set_unchanged(result, repo_root=repo_root)
+
+
+def test_absolute_freeze_set_keys_are_unchanged_when_repo_root_is_omitted(tmp_path):
+    """Backward compatibility: every existing hermetic fixture (``freeze_integrity_fixture_dir``,
+    every other test in this file) never passes ``repo_root`` and must keep getting absolute keys,
+    verified the exact same way as before this iteration."""
+    for name in fz.FREEZE_SET_REQUIRED_MODULES:
+        (tmp_path / name).write_text("# stub\n", encoding="utf-8")
+    result = fz.generate_freeze_set(tmp_path)
+    for key in result["entries"]:
+        assert Path(key).is_absolute(), f"expected an absolute key, got: {key}"
+    fz.verify_freeze_set_unchanged(result)  # must not raise, no repo_root needed
+
+
 def test_commit_ancestry_verification_against_the_real_repo():
     repo_root = subprocess.run(
         ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
diff --git a/apps/backend/tests/test_foundry_ledger.py b/apps/backend/tests/test_foundry_ledger.py
index b1e5b817..3b81c37f 100644
--- a/apps/backend/tests/test_foundry_ledger.py
+++ b/apps/backend/tests/test_foundry_ledger.py
@@ -120,6 +120,55 @@ def test_tc19_deterministic_rule_id_and_cannot_be_renamed(tmp_path):
         )
 
 
+# === goal-hypothesis-foundry-iter-6 (J-07): the epoch-opening / first-read-lock row -- §8.5 ======
+
+
+def _epoch_open_kwargs(**overrides):
+    kwargs = dict(
+        epoch_id="epoch:fixture-e1", freeze_commit="fixture-commit-abc",
+        manifest_hash="fixture-manifest-hash", source_registry_hash="fixture-source-registry-hash",
+        spec_hash="fixture-spec-hash", candidate_spec_schema_hash="fixture-schema-hash",
+        compiler_hash="fixture-compiler-hash", interpreter_hash="fixture-interpreter-hash",
+        runner_hash="fixture-runner-hash", scout_screen_source_hash="fixture-scout-screen-hash",
+        config_fingerprint="fixture-config-fingerprint", freeze_set_hash="fixture-freeze-set-hash",
+        era_open_evidence_class_contract="historical_exposed_diagnostic",
+        eligible_corpus_manifest_hash="fixture-eligible-corpus-manifest-hash",
+    )
+    kwargs.update(overrides)
+    return kwargs
+
+
+def test_epoch_open_row_round_trips(tmp_path):
+    ledger = fl.FoundryLedger(tmp_path)
+    assert ledger.epoch_open_row() is None  # honest pre-lock state
+
+    row = ledger.record_epoch_open(**_epoch_open_kwargs())
+    assert row["row_kind"] == fl.ROW_KIND_EPOCH_OPEN
+    assert row["epoch_id"] == "epoch:fixture-e1"
+    assert row["eligible_corpus_manifest_hash"] == "fixture-eligible-corpus-manifest-hash"
+    assert ledger.epoch_open_row() == row
+    assert ledger.verify_chain()["ok"] is True
+
+
+def test_epoch_open_row_replay_is_idempotent_no_second_row_appended(tmp_path):
+    ledger = fl.FoundryLedger(tmp_path)
+    first = ledger.record_epoch_open(**_epoch_open_kwargs())
+    second = ledger.record_epoch_open(**_epoch_open_kwargs())
+    assert first == second
+    epoch_open_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_EPOCH_OPEN]
+    assert len(epoch_open_rows) == 1  # never a duplicate first-read-lock row
+
+
+def test_epoch_open_row_conflicting_replay_is_refused(tmp_path):
+    ledger = fl.FoundryLedger(tmp_path)
+    ledger.record_epoch_open(**_epoch_open_kwargs())
+    with pytest.raises(fl.ConflictingReplayRefused):
+        ledger.record_epoch_open(**_epoch_open_kwargs(eligible_corpus_manifest_hash="DIFFERENT"))
+    # the refused attempt appended nothing
+    epoch_open_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_EPOCH_OPEN]
+    assert len(epoch_open_rows) == 1
+
+
 def test_tc19_prospective_root_status_scalar_vs_composite():
     from app.research import foundry_compiler as fc
 
diff --git a/apps/backend/tests/test_foundry_real_epoch_artifacts.py b/apps/backend/tests/test_foundry_real_epoch_artifacts.py
index 1f031c26..d1b749e6 100644
--- a/apps/backend/tests/test_foundry_real_epoch_artifacts.py
+++ b/apps/backend/tests/test_foundry_real_epoch_artifacts.py
@@ -96,6 +96,112 @@ def _require_git_checkout() -> None:
         pytest.skip("not a git checkout -- the Git-visible freeze barrier cannot be verified here")
 
 
+@pytest.fixture(scope="module")
+def freeze_set() -> dict:
+    return _load_json("freeze-set.json")
+
+
+# === goal-hypothesis-foundry-iter-6 (closes audit findings B1/B2/B7): the regenerated freeze-set /
+# freeze-record bookkeeping. Same-iteration read-only guards over the COMMITTED bytes, per the
+# iter-5 lesson this iteration's own BACKGROUND explicitly carries forward. ==========================
+
+
+def test_b1_every_freeze_set_entry_is_repo_relative_not_absolute(freeze_set):
+    entries = freeze_set["entries"]
+    assert entries, "empty freeze set"
+    for key in entries:
+        assert not key.startswith("/"), f"expected a repo-relative freeze-set key, got absolute: {key}"
+
+
+def test_b7_freeze_set_covers_the_tracked_registry_and_manifest_plus_both_foundry_clis(freeze_set):
+    covered = set(freeze_set["entries"])
+    required_suffixes = (
+        "docs/hypothesis-foundry/source-registry.json",
+        "docs/hypothesis-foundry/epoch-manifest.json",
+        "apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py",
+        "apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py",
+    )
+    for suffix in required_suffixes:
+        assert any(entry.endswith(suffix) for entry in covered), f"freeze-set is missing {suffix}"
+    # goal.md §8.4 never names `freeze-record.json`/`freeze-set.json` as freeze-set members (only
+    # "the Foundry methodology/spec and tracked REGISTRY/MANIFEST files") -- and `freeze-record.json`
+    # genuinely CANNOT be a member: its own content embeds `freeze_set_hash`, so pinning its file
+    # hash inside the very freeze-set that hash is computed over is the identical self-reference
+    # `freeze-set.json` is already excluded for, one hop removed. Neither appears.
+    for excluded_suffix in (
+        "docs/hypothesis-foundry/freeze-record.json", "docs/hypothesis-foundry/freeze-set.json",
+    ):
+        assert not any(entry.endswith(excluded_suffix) for entry in covered), (
+            f"{excluded_suffix} must NOT be a freeze-set member (self-reference)"
+        )
+
+
+def test_b7_freeze_record_carries_the_era_open_evidence_class_contract(freeze_record):
+    # §10.1/goal.md Success Criteria 16: every real Foundry evaluation this era is
+    # constitutionally locked to ONE evidence class.
+    assert freeze_record["era_open_evidence_class_contract"] == "historical_exposed_diagnostic"
+
+
+def test_freeze_record_freeze_set_hash_matches_the_committed_freeze_set(freeze_record, freeze_set):
+    """goal-hypothesis-foundry-iter-6 audit addition (finding B1 in the iter-6 audit report).
+
+    ``freeze-record.json`` is deliberately NOT a freeze-set member (its own content embeds
+    ``freeze_set_hash``, so pinning its file hash inside the very freeze-set that hash is computed
+    over is genuinely circular -- see
+    ``test_b7_freeze_set_covers_the_tracked_registry_and_manifest_plus_both_foundry_clis``). The
+    iter-6 dev handoff justified that exclusion by asserting freeze-record.json's integrity "is
+    instead protected by the existing ``verify_commit_is_ancestor`` + ``freeze_set_hash``
+    field-equality check every reader (the route, the exhaust CLI) already performs" -- but no such
+    field-equality check existed anywhere in the repository: ``verify_freeze_set_unchanged`` only
+    re-hashes the paths ``entries`` enumerates, and neither ``micro_routes.read_epoch_manifest_view``
+    nor ``run_hypothesis_foundry_real_exhaust.run_real_exhaust`` ever compares the two files' own
+    ``freeze_set_hash`` values. This test IS that check, in the one place the era can still add one
+    without touching a frozen science file: a read-only guard over the committed bytes.
+
+    A hand-edit of ``freeze-record.json`` that swapped in a different ``freeze_set_hash`` (the value
+    copied verbatim into the era's one irreversible §8.5 epoch-opening ledger row) would otherwise
+    pass every existing check in this repository."""
+    assert freeze_record["freeze_set_hash"] == freeze_set["freeze_set_hash"], (
+        "freeze-record.json's pinned freeze_set_hash disagrees with the committed freeze-set.json "
+        "it claims to pin -- the two tracked artifacts have drifted apart"
+    )
+    # Belt and braces: the freeze-set's own hash is a pure function of its recorded entries, so the
+    # equality above transitively pins the freeze-record to the enumerated path+sha256 set itself.
+    assert fz._sha256(fz._canonical(freeze_set["entries"])) == freeze_record["freeze_set_hash"]
+
+
+def test_tc8_verify_freeze_set_unchanged_and_commit_ancestry_both_pass_against_the_new_freeze_commit(
+    freeze_record, freeze_set,
+):
+    _require_git_checkout()
+    fz.verify_freeze_set_unchanged(freeze_set, repo_root=REPO_ROOT)  # must not raise
+    head = _git("rev-parse", "HEAD").stdout.strip()
+    assert fz.verify_commit_is_ancestor(freeze_record["freeze_commit"], head, cwd=REPO_ROOT)
+
+
+def test_b2_every_freeze_set_path_hash_matches_the_freeze_commits_own_committed_bytes(freeze_record, freeze_set):
+    """The direct fix for B2: not just ancestry (``freeze_commit`` is *an* ancestor of ``HEAD``),
+    but genuine byte-completeness -- ``git show {freeze_commit}:{path}`` for every pinned entry
+    hashes to EXACTLY the pinned digest, proving ``freeze_commit`` really does contain the bytes
+    the freeze-set was computed over (not merely an unrelated earlier commit that happens to be an
+    ancestor)."""
+    _require_git_checkout()
+    freeze_commit = freeze_record["freeze_commit"]
+    mismatches = []
+    for rel_path, expected_hash in freeze_set["entries"].items():
+        show = _git("show", f"{freeze_commit}:{rel_path}")
+        if show.returncode != 0:
+            mismatches.append((rel_path, "missing from freeze_commit's own tree"))
+            continue
+        actual = hashlib.sha256(show.stdout.encode("utf-8")).hexdigest()
+        # `git show` normalizes line endings identically to how the file was hashed on write
+        # (both are plain `read_bytes()`/`read_text()` UTF-8 -- no CRLF translation anywhere in
+        # this pipeline), so a direct string-encode comparison is valid here.
+        if actual != expected_hash:
+            mismatches.append((rel_path, f"expected {expected_hash}, git show gives {actual}"))
+    assert mismatches == [], f"freeze_commit does not contain the pinned bytes for: {mismatches}"
+
+
 # === TC-1..TC-5: the frozen registry's own content ===============================================
 
 
@@ -218,15 +324,21 @@ def test_tc9_freeze_commit_is_an_ancestor_of_head(freeze_record):
     assert fz.verify_commit_is_ancestor(freeze_record["freeze_commit"], head, cwd=REPO_ROOT)
 
 
-def test_tc9_no_real_exhaust_runner_entrypoint_exists_to_read_a_candidate_outcome():
-    """J-07 is barred from this era's iteration 5: the real exhaust runner must not be able to run.
-    It is satisfied by absence -- no CLI, route, or ``__main__`` anywhere under ``apps/backend``
-    drives ``foundry_runner`` over real data. This guard fails the moment one appears, so the
-    barrier stops being an unexamined claim in a handoff."""
-    # The only non-test caller of the runner's candidate-evaluation entrypoints is the hermetic
-    # oracle summary, which drives purely synthetic fixture anchors. Anything else -- a CLI under
-    # `scripts/`, a route, a manager -- would be a path capable of reading a real outcome.
-    allowed = {"app/research/foundry_runner.py", "app/research/foundry_hermetic_summary.py"}
+def test_tc9_exactly_one_real_exhaust_runner_entrypoint_exists_and_it_is_freeze_gated():
+    """goal-hypothesis-foundry-iter-6 (J-07): this test USED TO be satisfied by absence (no real
+    exhaust entrypoint could exist before step 8 began). This iteration's entire purpose is to add
+    EXACTLY ONE legitimate such entrypoint -- ``scripts/run_hypothesis_foundry_real_exhaust.py`` --
+    so the guard EVOLVES into a positive check (per the iter-3 lesson: an end-to-end claim must be
+    grep-verified to cross the real module boundary, not asserted in prose): still zero offenders
+    beyond the one now-allowed file, AND that file's own call site is reached only AFTER its own
+    freeze-integrity verification and single-flight lock acquisition (line-order, since this
+    module's own real exhaust sequence is a plain top-to-bottom function body with no branching
+    that could reorder those three calls relative to each other)."""
+    allowed = {
+        "app/research/foundry_runner.py",
+        "app/research/foundry_hermetic_summary.py",
+        "scripts/run_hypothesis_foundry_real_exhaust.py",
+    }
     call_site = re.compile(r"\b(run_family|run_one_candidate)\s*\(")
     offenders = []
     for py_file in list((BACKEND_DIR / "app").rglob("*.py")) + list((BACKEND_DIR / "scripts").rglob("*.py")):
@@ -235,7 +347,16 @@ def test_tc9_no_real_exhaust_runner_entrypoint_exists_to_read_a_candidate_outcom
             continue
         if call_site.search(py_file.read_text(encoding="utf-8", errors="ignore")):
             offenders.append(rel)
-    assert offenders == [], f"a Foundry exhaust/runner entrypoint now exists: {offenders}"
+    assert offenders == [], f"an UNEXPECTED Foundry exhaust/runner entrypoint now exists: {offenders}"
+
+    exhaust_cli = (BACKEND_DIR / "scripts" / "run_hypothesis_foundry_real_exhaust.py").read_text(encoding="utf-8")
+    freeze_verify_idx = exhaust_cli.index("fz.verify_freeze_set_unchanged(")
+    single_flight_idx = exhaust_cli.index("fr.SingleFlightLock(")
+    run_family_idx = call_site.search(exhaust_cli).start()
+    assert freeze_verify_idx < single_flight_idx < run_family_idx, (
+        "the real exhaust CLI's own run_family/run_one_candidate call site must be reached only "
+        "AFTER its own freeze-integrity verification and single-flight lock acquisition"
+    )
 
 
 # === TC-10: replay verifies, drift refuses -- no second epoch ====================================
@@ -268,33 +389,92 @@ def test_tc10_drifted_generation_inputs_are_refused_rather_than_minting_epoch_2(
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
 
 
-def test_freeze_set_entries_still_match_the_science_files_in_this_checkout():
+def test_freeze_set_entries_still_match_the_science_files_in_this_checkout(freeze_set):
     """Recomputes sha256 for every enumerated freeze-set path and compares against the pinned
     digest -- the §8.5 "recomputed freeze-set hashes are the enforceable primitive" check, run over
     the real committed freeze-set.
 
-    Deliberately resolves each entry RELATIVE to this checkout's root rather than using the key
-    verbatim: the committed ``freeze-set.json`` records absolute, machine-local paths
-    (``/home/.../tapeology/apps/backend/app/research/...``), so ``foundry_freeze.
-    verify_freeze_set_unchanged`` -- which resolves the key literally -- cannot verify this
-    freeze-set from any other checkout, and in a second worktree ON THE SAME MACHINE would verify
-    the ORIGINAL tree's files while a runner executes the worktree's. That is an audit finding
-    against the artifact (see the iter-5 audit report, finding B1), not something this test can
-    repair; this test performs the portable equivalent so the drift guard exists in the meantime.
-    """
-    freeze_set = _load_json("freeze-set.json")
+    goal-hypothesis-foundry-iter-6 (closes audit finding B1): the committed ``freeze-set.json`` now
+    records REPO-RELATIVE paths (``apps/backend/app/research/...``, ``docs/...``), so every entry
+    resolves identically -- and portably, across any checkout/worktree of this same commit -- by
+    joining it directly onto ``REPO_ROOT``, with no marker-based workaround. See
+    ``test_tc8_verify_freeze_set_unchanged_and_commit_ancestry_both_pass_against_the_new_freeze_
+    commit`` for the equivalent check run through the real production ``verify_freeze_set_unchanged``
+    function rather than this test's own direct recompute."""
     entries = freeze_set["entries"]
     assert entries, "empty freeze set"
     # The pinned hash must be a pure function of the recorded entries.
     assert fz._sha256(fz._canonical(entries)) == freeze_set["freeze_set_hash"]
 
     drifted = []
-    for recorded_path, expected in entries.items():
-        marker = "apps/backend/" if "apps/backend/" in recorded_path else "docs/"
-        rel = recorded_path[recorded_path.index(marker):]
+    for rel, expected in entries.items():
+        assert not rel.startswith("/"), f"expected a repo-relative freeze-set key, got: {rel}"
         path = REPO_ROOT / rel
         assert path.is_file(), f"freeze-set path missing from this checkout: {rel}"
         if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
diff --git a/apps/backend/tests/test_foundry_route.py b/apps/backend/tests/test_foundry_route.py
index 0f37176e..64f76cd0 100644
--- a/apps/backend/tests/test_foundry_route.py
+++ b/apps/backend/tests/test_foundry_route.py
@@ -172,6 +172,72 @@ def test_tc13_route_serves_the_recorded_baseline_byte_identically_across_two_cal
     assert set(first["era_open_baseline"]["referee_module_sha256"]) == set(fsr.REFEREE_MODULES)
 
 
+# === goal-hypothesis-foundry-iter-6 (J-07/J-08): `exhaust_progress` -- genuinely runtime-scoped,
+# read PER REQUEST (unlike `epoch_manifest`), degrading honestly before the operator's own
+# exhaust-CLI act has ever run against this scoped `foundry_dir`. ==================================
+
+
+def test_exhaust_progress_degrades_honestly_before_any_exhaust_cli_run(tmp_path, monkeypatch):
+    _scope_dataset_dir(tmp_path, monkeypatch)
+    with TestClient(app) as client:
+        body = client.get("/research/desk/micro/foundry").json()
+    progress = body["exhaust_progress"]
+    assert progress["first_read_lock_recorded"] is False
+    assert progress["first_read_lock_at"] is None
+    assert progress["eligible_corpus_manifest_hash"] is None
+    assert progress["terminal_count"] == 0
+    assert progress["checkpoint_ordinal"] == 0
+    assert progress["protected_read_count"] == 0
+    assert progress["single_flight_status"] == "idle"
+    assert progress["freeze_integrity_verdict"] == "not_yet_verified"
+    assert progress["exhaust_complete"] is False
+
+
+def test_exhaust_progress_reflects_a_real_epoch_open_row_once_one_exists(tmp_path, monkeypatch):
+    """The scoped-runtime-storage discipline this iteration's own carried lesson names: writing
+    directly to the SAME ``foundry_dir`` the route resolves (via ``foundry_ledger.FoundryLedger``,
+    exactly what the real exhaust CLI does) must be visible on the very next GET -- no server
+    restart, no caching, since this key is read PER REQUEST."""
+    dataset_dir = _scope_dataset_dir(tmp_path, monkeypatch)
+    foundry_dir = fsr.resolve_foundry_dir(str(dataset_dir))
+    from app.research import foundry_ledger as fl
+
+    ledger = fl.FoundryLedger(foundry_dir)
+    ledger.record_epoch_open(
+        epoch_id="epoch:test-exhaust-progress", freeze_commit="c" * 40,
+        manifest_hash="mh", source_registry_hash="srh", spec_hash="sh",
+        candidate_spec_schema_hash="csh", compiler_hash="ch", interpreter_hash="ih",
+        runner_hash="rh", scout_screen_source_hash="ssh", config_fingerprint="fp",
+        freeze_set_hash="fsh", era_open_evidence_class_contract="historical_exposed_diagnostic",
+        eligible_corpus_manifest_hash="ecmh",
+    )
+
+    with TestClient(app) as client:
+        body = client.get("/research/desk/micro/foundry").json()
+    progress = body["exhaust_progress"]
+    assert progress["first_read_lock_recorded"] is True
+    assert progress["eligible_corpus_manifest_hash"] == "ecmh"
+    assert progress["freeze_integrity_verdict"] == "green"
+    assert progress["terminal_count"] == 0
+    # the real committed manifest has zero FROZEN_READY variants -- an honest, vacuous completion.
+    assert progress["frozen_ready_total"] == 0
+    assert progress["exhaust_complete"] is True
+
+
+def test_exhaust_progress_single_flight_status_reflects_a_live_held_lock(tmp_path, monkeypatch):
+    dataset_dir = _scope_dataset_dir(tmp_path, monkeypatch)
+    foundry_dir = fsr.resolve_foundry_dir(str(dataset_dir))
+    from pathlib import Path
+
+    from app.research import foundry_runner as fr
+
+    lock_path = Path(foundry_dir) / fr.EXHAUST_LOCK_FILENAME
+    with fr.SingleFlightLock(lock_path).acquire():
+        with TestClient(app) as client:
+            body = client.get("/research/desk/micro/foundry").json()
+    assert body["exhaust_progress"]["single_flight_status"] == "running"
+
+
 def test_foundry_route_is_get_only_no_mutation_endpoint_exists():
     """Product Shape / anti-goals: the Foundry surface is read-only this era -- there must be no
     ``POST``/``PUT``/``DELETE`` sibling under ``/research/desk/micro/foundry``."""
diff --git a/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py b/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
new file mode 100644
index 00000000..984583c9
--- /dev/null
+++ b/apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
@@ -0,0 +1,388 @@
+"""``scripts/run_hypothesis_foundry_real_exhaust.py`` (goal-hypothesis-foundry-iter-6, Binding
+Execution Order step 8, J-07): the resumable, single-flight real exhaust CLI. TC-1..TC-6 in
+``docs/phases/goal-hypothesis-foundry-iter-6.md``.
+
+Every test here loads the script as a plain module (``importlib.util``, the same convention
+``test_foundry_real_epoch_artifacts.py`` already uses for the generation script) rather than
+shelling out to a subprocess -- cheap, and lets a test inject its own ``frozen_ready_families``
+resolver / override paths directly.
+
+Two flavors of test live here, deliberately:
+
+* **Real-freeze tests** point ``tracked_dir``/``repo_root`` at the REAL committed
+  ``docs/hypothesis-foundry/`` artifacts and this real repository -- proving freeze-set/freeze-
+  record verification (B1/B2/B7's own fixes) genuinely passes against what is actually committed,
+  and that the real committed manifest's ``families: []`` reaches an honest, vacuous completion.
+  These use an ISOLATED ``foundry_dir``/``lock_path`` (``tmp_path``) and the small, fast,
+  already-committed ``tests/fixtures/datasets`` corpus -- never the real, shared runtime ledger.
+* **Fixture-freeze tests** build a synthetic ``tracked_dir`` from scratch (real
+  ``foundry_freeze.generate_freeze_set``/``build_freeze_record`` over a tiny synthetic module set,
+  pinned to a real commit of THIS repository for ancestry) so a test can inject an actual
+  ``frozen_ready_families`` variant plan and exercise crash-resume/canonical-order through the
+  exact same production sequence, per J-07 step 7's own explicit fixture allowance."""
+
+from __future__ import annotations
+
+import importlib.util
+import json
+import subprocess
+from pathlib import Path
+
+import pytest
+
+BACKEND_DIR = Path(__file__).resolve().parents[1]
+REPO_ROOT = BACKEND_DIR.parents[1]
+FOUNDRY_DOCS_DIR = REPO_ROOT / "docs" / "hypothesis-foundry"
+FIXTURE_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets"
+
+
+def _load_module():
+    spec = importlib.util.spec_from_file_location(
+        "_run_hypothesis_foundry_real_exhaust_under_test",
+        BACKEND_DIR / "scripts" / "run_hypothesis_foundry_real_exhaust.py",
+    )
+    module = importlib.util.module_from_spec(spec)
+    spec.loader.exec_module(module)
+    return module
+
+
+@pytest.fixture(scope="module")
+def exhaust_mod():
+    return _load_module()
+
+
+def _require_real_epoch_committed():
+    if not (FOUNDRY_DOCS_DIR / "freeze-record.json").is_file():
+        pytest.skip("the real Hypothesis Foundry epoch has not been generated in this checkout")
+
+
+# === compute_eligible_corpus: sanctioned door, metadata only, deterministic ========================
+
+
+def test_compute_eligible_corpus_hashes_only_metadata_and_matches_micro_corpus_formula(exhaust_mod):
+    from app.research import micro_corpus
+    from app.research.datasets import DatasetStore
+
+    result = exhaust_mod.compute_eligible_corpus(str(FIXTURE_DATASET_DIR))
+    assert result["withheld_excluded"] == 0  # no vault/universe registered over this fixture dir
+    store = DatasetStore(FIXTURE_DATASET_DIR)
+    records, errors = store.list()
+    assert errors == []
+    assert result["member_count"] == len(records)
+    expected_hash = micro_corpus.corpus_manifest_hash(
+        [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in records]
+    )
+    assert result["manifest_hash"] == expected_hash
+
+    # deterministic: a second call over the SAME corpus reproduces the identical hash.
+    again = exhaust_mod.compute_eligible_corpus(str(FIXTURE_DATASET_DIR))
+    assert again["manifest_hash"] == result["manifest_hash"]
+
+
+def test_compute_eligible_corpus_over_an_empty_dataset_dir_is_honest_and_deterministic(exhaust_mod, tmp_path):
+    empty = tmp_path / "empty-datasets"
+    empty.mkdir()
+    result = exhaust_mod.compute_eligible_corpus(str(empty))
+    assert result["member_count"] == 0
+    assert result["withheld_excluded"] == 0
+    assert result["manifest_hash"]  # a real, deterministic hash over an empty member list
+
+
+# === _default_frozen_ready_families: honest-empty vs fail-closed on a non-empty family ============
+
+
+def test_default_resolver_returns_empty_plan_for_the_real_zero_family_manifest_shape(exhaust_mod):
+    plan = exhaust_mod._default_frozen_ready_families({"families": []})
+    assert plan == []
+
+
+def test_default_resolver_honestly_completes_a_zero_variant_family_entry(exhaust_mod):
+    manifest = {"families": [{"foundry_family_id": "family:test-zero-variant", "variants": []}]}
+    plan = exhaust_mod._default_frozen_ready_families(manifest)
+    assert len(plan) == 1
+    family, variants = plan[0]
+    assert family.foundry_family_id == "family:test-zero-variant"
+    assert family.variant_count == 0
+    assert variants == []
+
+
+def test_default_resolver_refuses_a_non_empty_family_entry_rather_than_mis_evaluating(exhaust_mod):
+    manifest = {
+        "families": [
+            {"foundry_family_id": "family:test-non-empty", "variants": [{"variant_id": "family:test-non-empty:0"}]}
+        ]
+    }
+    with pytest.raises(exhaust_mod.RealCandidateEvaluationUnsupported):
+        exhaust_mod._default_frozen_ready_families(manifest)
+
+
+# === run_real_exhaust against the REAL committed freeze-set/freeze-record/manifest ================
+
+
+def test_tc1_tc3_tc4_first_invocation_against_the_real_manifest_writes_the_epoch_open_row(exhaust_mod, tmp_path):
+    _require_real_epoch_committed()
+    foundry_dir = tmp_path / "foundry"
+    lock_path = tmp_path / "exhaust.lock"
+
+    result = exhaust_mod.run_real_exhaust(
+        tracked_dir=FOUNDRY_DOCS_DIR, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
+        foundry_dir=str(foundry_dir), lock_path=lock_path,
+    )
+    assert result["epoch_open"]["row_kind"] == "epoch_open"
+    assert result["eligible_corpus_manifest_hash"]
+    # TC-4: nothing in this sequence ever reads a snapshot row -- zero by construction.
+    assert result["protected_read_count"] == 0
+    # TC-3: the real committed manifest has zero FROZEN_READY variants.
+    assert result["frozen_ready_total"] == 0
+    assert result["terminal_count"] == 0
+    assert result["exhaust_complete"] is True
+
+    from app.research import foundry_ledger as fl
+
+    ledger = fl.FoundryLedger(foundry_dir)
+    epoch_open_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_EPOCH_OPEN]
+    assert len(epoch_open_rows) == 1
+
+
+def test_tc2_second_invocation_verifies_and_appends_no_second_epoch_open_row(exhaust_mod, tmp_path):
+    _require_real_epoch_committed()
+    foundry_dir = tmp_path / "foundry"
+    lock_path = tmp_path / "exhaust.lock"
+    kwargs = dict(
+        tracked_dir=FOUNDRY_DOCS_DIR, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
+        foundry_dir=str(foundry_dir), lock_path=lock_path,
+    )
+    first = exhaust_mod.run_real_exhaust(**kwargs)
+    second = exhaust_mod.run_real_exhaust(**kwargs)
+    assert first["epoch_open"] == second["epoch_open"]
+
+    from app.research import foundry_ledger as fl
+
+    ledger = fl.FoundryLedger(foundry_dir)
+    epoch_open_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_EPOCH_OPEN]
+    assert len(epoch_open_rows) == 1  # no duplicate first-read-lock row
+
+
+def test_tc6_concurrent_invocation_is_refused_via_the_real_single_flight_lock(exhaust_mod, tmp_path):
+    _require_real_epoch_committed()
+    from app.research import foundry_runner as fr
+
+    foundry_dir = tmp_path / "foundry"
+    lock_path = tmp_path / "exhaust.lock"
+    with fr.SingleFlightLock(lock_path).acquire():
+        with pytest.raises(fr.ConcurrentRunnerRefused):
+            exhaust_mod.run_real_exhaust(
+                tracked_dir=FOUNDRY_DOCS_DIR, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
+                foundry_dir=str(foundry_dir), lock_path=lock_path,
+            )
+    # the refused attempt appended no ledger row at all.
+    from app.research import foundry_ledger as fl
+
+    ledger = fl.FoundryLedger(foundry_dir)
+    assert ledger.all_rows() == []
+
+
+def test_freeze_ancestry_unproven_when_freeze_commit_does_not_verify(exhaust_mod, tmp_path):
+    """A tampered ``freeze_commit`` (never an ancestor of HEAD) halts BEFORE the single-flight lock
+    is even acquired or any ledger row is written."""
+    _require_real_epoch_committed()
+    tracked_dir = tmp_path / "tracked"
+    tracked_dir.mkdir()
+    for name in ("freeze-set.json", "epoch-manifest.json"):
+        (tracked_dir / name).write_text((FOUNDRY_DOCS_DIR / name).read_text(encoding="utf-8"), encoding="utf-8")
+    real_freeze_record = json.loads((FOUNDRY_DOCS_DIR / "freeze-record.json").read_text(encoding="utf-8"))
+    tampered = {**real_freeze_record, "freeze_commit": "0" * 40}
+    (tracked_dir / "freeze-record.json").write_text(json.dumps(tampered), encoding="utf-8")
+
+    with pytest.raises(exhaust_mod.FreezeAncestryUnproven):
+        exhaust_mod.run_real_exhaust(
+            tracked_dir=tracked_dir, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
+            foundry_dir=str(tmp_path / "foundry"), lock_path=tmp_path / "exhaust.lock",
+        )
+
+
+# === fixture-backed crash-resume through the SAME real production sequence (J-07 step 7) ==========
+
+
+def _git(*args, cwd) -> str:
+    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True).stdout.strip()
+
+
+def _build_fixture_tracked_dir(tmp_path: Path) -> Path:
+    """A synthetic ``tracked_dir`` (real ``generate_freeze_set``/``build_freeze_record`` output,
+    over a tiny synthetic module directory, pinned to THIS repository's real current HEAD for a
+    genuinely provable ancestry check) plus a synthetic ``epoch-manifest.json`` carrying ONE
+    ``FROZEN_READY`` family/variant entry -- so a test can inject a matching
+    ``frozen_ready_families`` resolver and prove the crash-resume path through the real sequence."""
+    from app.research import foundry_freeze as fz
+
+    research_dir = tmp_path / "fixture_research"
+    research_dir.mkdir()
+    for name in fz.FREEZE_SET_REQUIRED_MODULES:
+        (research_dir / name).write_text(f"# fixture stub {name}\n", encoding="utf-8")
+    freeze_set = fz.generate_freeze_set(research_dir)
+
+    head = _git("rev-parse", "HEAD", cwd=REPO_ROOT)
+    freeze_record = fz.build_freeze_record(
+        freeze_commit=head, manifest_hash="fixture-manifest-hash",
+        source_registry_hash="fixture-source-registry-hash", spec_hash="fixture-spec-hash",
+        candidate_spec_schema_hash="fixture-schema-hash", compiler_hash="fixture-compiler-hash",
+        interpreter_hash="fixture-interpreter-hash", runner_hash="fixture-runner-hash",
+        scout_screen_source_hash="fixture-scout-screen-hash", config_fingerprint="fixture-config-fingerprint",
+        freeze_set_hash=freeze_set["freeze_set_hash"],
+        era_open_evidence_class_contract="historical_exposed_diagnostic",
+    )
+
+    tracked_dir = tmp_path / "tracked"
+    tracked_dir.mkdir()
+    (tracked_dir / "freeze-set.json").write_text(json.dumps(freeze_set), encoding="utf-8")
+    (tracked_dir / "freeze-record.json").write_text(
+        json.dumps(
+            {
+                "freeze_commit": freeze_record.freeze_commit, "manifest_hash": freeze_record.manifest_hash,
+                "source_registry_hash": freeze_record.source_registry_hash, "spec_hash": freeze_record.spec_hash,
+                "candidate_spec_schema_hash": freeze_record.candidate_spec_schema_hash,
+                "compiler_hash": freeze_record.compiler_hash, "interpreter_hash": freeze_record.interpreter_hash,
+                "runner_hash": freeze_record.runner_hash, "scout_screen_source_hash": freeze_record.scout_screen_source_hash,
+                "config_fingerprint": freeze_record.config_fingerprint, "freeze_set_hash": freeze_record.freeze_set_hash,
+                "era_open_evidence_class_contract": freeze_record.era_open_evidence_class_contract,
+            }
+        ),
+        encoding="utf-8",
+    )
+    (tracked_dir / "epoch-manifest.json").write_text(
+        json.dumps(
+            {
+                "epoch_id": "epoch:fixture-crash-resume",
+                "families": [
+                    {
+                        "foundry_family_id": "family:fixture-crash-resume",
+                        "variants": [{"variant_id": "family:fixture-crash-resume:0"}],
+                    }
+                ],
+            }
+        ),
+        encoding="utf-8",
+    )
+    return tracked_dir
+
+
+def _one_variant_resolver(manifest: dict):
+    """A test-only ``frozen_ready_families`` resolver matching ``_build_fixture_tracked_dir``'s
+    synthetic manifest: ONE family, ONE scalar candidate, synthetic anchors -- the same
+    ``foundry_compiler``/``foundry_family``/``foundry_interpreter`` construction
+    ``test_foundry_runner.py`` already proves, injected here so the crash-resume proof runs THROUGH
+    ``run_real_exhaust``'s own freeze-verify -> lock -> corpus-hash -> epoch-open -> exhaust
+    sequence rather than calling ``foundry_runner.run_one_candidate`` in isolation."""
+    from app.research import foundry_compiler as fc
+    from app.research import foundry_family as ffam
+    from app.research import foundry_interpreter as fi
+
+    family_id = "family:fixture-crash-resume"
+    family = ffam.build_family_registry({family_id: [f"{family_id}:0"]})[family_id]
+    coord = fc.CandidateCoordinate(
+        feature_construct_id="q", semantic_role="candidate_signal", transform_orientation="ge",
+        threshold_corner_predicate="q >= 1", threshold_provenance="natural_semantic_boundary",
+        aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
+    )
+    spec = fc.CandidateSpec(
+        foundry_spec_version="v1", epoch_id="epoch:fixture-crash-resume", source_ids=("s0",),
+        lineage_id="s0", foundry_family_id=family_id, variant_id=f"{family_id}:0", variant_ordinal=0,
+        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
+        coordinates=(coord,), relation=fc.CandidateRelation(kind="direct_scalar_membership"),
+        membership_corner="q >= 1", outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness="long"),
+        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=1,
+    ).with_hash()
+
+    anchors = []
+    for s in range(6):
+        session = f"2026-08-{10 + s:02d}"
+        for i in range(40):
+            member = i < 20
+            comp = fi.ComponentResolution("q", True, float(i), 1.0 if member else 0.0, member)
+            outcome = 40.0 + (i % 5) * 0.01 if member else -0.01 * (i % 5)
+            anchors.append(fi.PopulationAnchor(f"ds-{session}", "AAPL", session, i, "mid", None, outcome, "return_bps", (comp,)))
+
+    return [(family, [(spec, anchors)])]
+
+
+def test_j07_step7_fixture_backed_crash_resume_through_the_real_sequence(exhaust_mod, tmp_path):
+    tracked_dir = _build_fixture_tracked_dir(tmp_path)
+    foundry_dir = tmp_path / "foundry"
+    lock_path = tmp_path / "exhaust.lock"
+
+    # Simulate the crash: an intent row exists (as the real sequence would have written it), but
+    # no terminal row yet -- written directly to the ledger BEFORE the CLI ever runs.
+    from app.research import foundry_ledger as fl
+
+    _, [(spec, _anchors)] = _one_variant_resolver({})[0]
+    ledger = fl.FoundryLedger(foundry_dir)
+    ledger.record_intent(
+        candidate_spec_hash=spec.candidate_spec_hash, manifest_hash="fixture-manifest-hash",
+        econ_floor_bps=exhaust_mod._UNUSED_PLACEHOLDER_ECON_FLOOR["floor_bps"],
+        econ_floor_provenance=exhaust_mod._UNUSED_PLACEHOLDER_ECON_FLOOR["rule"],
+    )
+    assert ledger.terminal_row_for(spec.candidate_spec_hash) is None
+
+    result = exhaust_mod.run_real_exhaust(
+        tracked_dir=tracked_dir, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
+        foundry_dir=str(foundry_dir), lock_path=lock_path, frozen_ready_families=_one_variant_resolver,
+    )
+
+    assert result["frozen_ready_total"] == 1
+    assert result["terminal_count"] == 1
+    assert result["exhaust_complete"] is True
+
+    intent_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_INTENT]
+    terminal_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]
+    assert len(intent_rows) == 1  # no duplicate intent row appended on resume
+    assert len(terminal_rows) == 1
+    assert terminal_rows[0]["candidate_spec_hash"] == spec.candidate_spec_hash
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
diff --git a/apps/frontend/app/desk/page.tsx b/apps/frontend/app/desk/page.tsx
index ae91a7b5..e92ef348 100644
--- a/apps/frontend/app/desk/page.tsx
+++ b/apps/frontend/app/desk/page.tsx
@@ -89,6 +89,7 @@ import type {
   DeskFoundryResponse,
   DeskGraduationResponse,
   FoundryEpochManifest,
+  FoundryExhaustProgress,
   FoundryFreezeIntegrity,
   FoundryHermeticOracles,
   FoundryInterpreterFixtures,
@@ -7820,6 +7821,85 @@ function EpochManifestSubsection({ data }: { data: FoundryEpochManifest }) {
   );
 }
 
+// goal-hypothesis-foundry-iter-6 (J-07/J-08): Runner / Checkpoint -- the real exhaust CLI's own
+// checkpoint/completion state, rendered VERBATIM from `exhaust_progress`. UNLIKE
+// `EpochManifestSubsection` above (a Git-tracked literal path), this key is genuinely
+// runtime-scoped -- it can render honestly BOTH before the operator's exhaust-CLI act has ever run
+// (pre-first-read-lock) and after (the honest zero-candidate completion state this era's one real
+// epoch always reaches). No client-side computation anywhere in this component.
+function RunnerCheckpointSubsection({ data }: { data: FoundryExhaustProgress }) {
+  const freezeVerdictClass =
+    data.freeze_integrity_verdict === "green"
+      ? "text-emerald-400"
+      : data.freeze_integrity_verdict === "not_yet_verified"
+        ? "text-amber-400"
+        : "text-rose-400";
+  const singleFlightLabel: Record<FoundryExhaustProgress["single_flight_status"], string> = {
+    idle: "Idle — lock free",
+    running: "Running — lock held by another invocation",
+    refused_concurrent: "Refused — a concurrent invocation was rejected",
+  };
+  return (
+    <div data-testid="foundry-runner-checkpoint">
+      <RealEpochBanner testid="foundry-runner-checkpoint-real-banner" label="Real Epoch — not a fixture" />
+      {!data.first_read_lock_recorded ? (
+        <EmptyState
+          testid="foundry-runner-checkpoint-empty"
+          title="The real exhaust pass has not been run yet — the first-read lock has not been recorded."
+        />
+      ) : (
+        <div className="mb-3 space-y-0.5 text-[11px] text-slate-500">
+          <p data-testid="foundry-runner-first-read-lock">
+            First-read lock recorded at:{" "}
+            <span className="font-mono text-slate-300">{data.first_read_lock_at}</span>
+          </p>
+          <p data-testid="foundry-runner-eligible-corpus-hash">
+            Eligible-corpus manifest hash:{" "}
+            <span className="break-all font-mono text-[10px] text-slate-400">
+              {data.eligible_corpus_manifest_hash}
+            </span>
+          </p>
+        </div>
+      )}
+
+      <div data-testid="foundry-runner-checkpoint-counts" className="mb-3 space-y-0.5 text-[11px] text-slate-500">
+        <p data-testid="foundry-runner-checkpoint-ordinal">
+          Checkpoint:{" "}
+          <span className="font-mono text-slate-300">
+            {data.checkpoint_ordinal} of {data.frozen_ready_total}
+          </span>
+        </p>
+        <p data-testid="foundry-runner-protected-read-count">
+          Protected/withheld/sealed reads:{" "}
+          <span className={`font-mono ${data.protected_read_count === 0 ? "text-emerald-400" : "text-rose-400"}`}>
+            {data.protected_read_count}
+          </span>
+        </p>
+        <p data-testid="foundry-runner-single-flight-status">
+          Runner lock: <span className="font-mono text-slate-300">{singleFlightLabel[data.single_flight_status]}</span>
+        </p>
+        <p data-testid="foundry-runner-freeze-integrity-verdict">
+          Freeze integrity: <span className={`font-mono ${freezeVerdictClass}`}>{data.freeze_integrity_verdict}</span>
+        </p>
+      </div>
+
+      {data.exhaust_complete ? (
+        <p data-testid="foundry-runner-exhaust-complete" className="text-[11px] text-emerald-400">
+          Exhaust complete — every frozen candidate reached a terminal state
+          {data.frozen_ready_total === 0
+            ? " (zero FROZEN_READY variants this epoch — an honest, vacuous completion)."
+            : "."}
+        </p>
+      ) : (
+        <p data-testid="foundry-runner-exhaust-incomplete" className="text-[11px] text-amber-400">
+          Exhaust not yet complete — {data.terminal_count} of {data.frozen_ready_total} candidates
+          terminal.
+        </p>
+      )}
+    </div>
+  );
+}
+
 // goal-hypothesis-foundry-iter-4 (J-05): Hermetic Oracles -- the outcome-type coverage, denominator
 // -consistency/canonical-order flags, and the five named oracle pass/fail results, rendered
 // VERBATIM from `hermetic_oracles`.
@@ -8066,6 +8146,17 @@ function HypothesisFoundrySection({
         >
           <EpochManifestSubsection data={foundry.epoch_manifest} />
         </CollapsibleSection>
+
+        {/* goal-hypothesis-foundry-iter-6 (J-07): the real exhaust CLI's own checkpoint/completion
+            state -- distinct from the frozen manifest above (runtime-scoped, not Git-tracked). */}
+        <CollapsibleSection
+          id="foundry-runner-checkpoint-section"
+          title="Runner / Checkpoint"
+          open={openSubsections.has("runner-checkpoint")}
+          onToggle={() => toggleSubsection("runner-checkpoint")}
+        >
+          <RunnerCheckpointSubsection data={foundry.exhaust_progress} />
+        </CollapsibleSection>
       </div>
     </div>
   );
diff --git a/apps/frontend/lib/types.ts b/apps/frontend/lib/types.ts
index c07b5e79..73fde0f6 100644
--- a/apps/frontend/lib/types.ts
+++ b/apps/frontend/lib/types.ts
@@ -3165,6 +3165,25 @@ export interface FoundryEpochManifest {
   source_registry_audit: { path: string; committed: boolean };
 }
 
+// goal-hypothesis-foundry-iter-6 (J-07/J-08): the exhaust CLI's own checkpoint/completion state --
+// UNLIKE `epoch_manifest` (a Git-tracked literal path), this reflects genuinely RUNTIME-scoped
+// state (the Foundry trial ledger the real exhaust CLI writes) and is read PER REQUEST by the
+// backend, never cached at import time. Rendered verbatim -- no client-side computation.
+export interface FoundryExhaustProgress {
+  first_read_lock_recorded: boolean;
+  first_read_lock_at: string | null;
+  eligible_corpus_manifest_hash: string | null;
+  frozen_ready_total: number;
+  terminal_count: number;
+  checkpoint_ordinal: number;
+  protected_read_count: number;
+  single_flight_status: "idle" | "running" | "refused_concurrent";
+  // The backend's own two-value schema is `"green" | <typed halt code>`; `"not_yet_verified"` is
+  // the honest additional state before the exhaust CLI has ever run (never coerced to either).
+  freeze_integrity_verdict: string;
+  exhaust_complete: boolean;
+}
+
 export interface DeskFoundryResponse {
   era: FoundryEraIdentity;
   // `null` on a fresh install before the operator's one-time recording act has run -- never
@@ -3181,4 +3200,6 @@ export interface DeskFoundryResponse {
   hermetic_oracles: FoundryHermeticOracles;
   // goal-hypothesis-foundry-iter-5 (J-06): the real epoch -- see `FoundryEpochManifest`'s own doc.
   epoch_manifest: FoundryEpochManifest;
+  // goal-hypothesis-foundry-iter-6 (J-07): the real exhaust pass's own checkpoint/completion state.
+  exhaust_progress: FoundryExhaustProgress;
 }
diff --git a/docs/hypothesis-foundry/freeze-record.json b/docs/hypothesis-foundry/freeze-record.json
index 49997760..82be7269 100644
--- a/docs/hypothesis-foundry/freeze-record.json
+++ b/docs/hypothesis-foundry/freeze-record.json
@@ -2,11 +2,12 @@
   "candidate_spec_schema_hash": "dc3a283eb8a4fb2c7a9eb8120a5637af012ec1dd2a5e9d8b896a3f7152465332",
   "compiler_hash": "dc3a283eb8a4fb2c7a9eb8120a5637af012ec1dd2a5e9d8b896a3f7152465332",
   "config_fingerprint": "08e471b10130e1e2",
-  "freeze_commit": "55c42ee3ebc33eda9eaf14da8fd753d90640fa2c",
-  "freeze_set_hash": "70fcd30237b463d5e61ea31ec80987995886531047c9031990a8269da7bb35b2",
+  "era_open_evidence_class_contract": "historical_exposed_diagnostic",
+  "freeze_commit": "5b41d9ef68410a6a11221f7317e21abed6754a5e",
+  "freeze_set_hash": "0b5a8364589ed06f44b3c3dc47f5454bb3fb57daa08748da744bee56719d5e12",
   "interpreter_hash": "9f024c28c30baf0a9f310ba2191ddf4bc5f4572b5b7e623ead3dda5e8f74ca8f",
   "manifest_hash": "fc22781ce4319968e40dc5b0ee976e5b76382d7f95a89dfa9ce22977690005cb",
-  "runner_hash": "83f340abe577d966fe6e538e29b0857d8e4f93ccb7b739f91be25c685a9131b5",
+  "runner_hash": "64130765e1338ca2f0a3e11f279cac3ad2e1b6ba1c8123c0044aa55effe015b8",
   "scout_screen_source_hash": "7fede1f37d688385c83b53c279b63c143cb9664e35ebf4154e8e908056b47ea8",
   "source_registry_hash": "ed40dbc25e8fdb961258512dc01ccbaa4633e0ddb6f374288c6c78d681bd098d",
   "spec_hash": "17beb618be5c325144e03eb760ef03e91771456a2e965f5f821009058df8ce82"
diff --git a/docs/hypothesis-foundry/freeze-set.json b/docs/hypothesis-foundry/freeze-set.json
index 410668fb..a66474b4 100644
--- a/docs/hypothesis-foundry/freeze-set.json
+++ b/docs/hypothesis-foundry/freeze-set.json
@@ -1,60 +1,64 @@
 {
   "entries": {
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/algorithm_version.py": "ee28e8cfd1bd3583cf66002078204197bf0363eb8511816e01fe65bacfca6dc9",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/backtests.py": "c9536ba894fb1bf1e524c2dcced5868c426fd78ec2cc6a502569e47eaeea53e9",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/bar_index.py": "a40695360fe60307b73f29a092cfe816d92cd687eaf9fde57c701b9e07342a96",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/bar_verify_cache.py": "3a6945c0a6409d4cf2dc5df80b3981db295132ec223dd70f16df26f2bec71716",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/bars.py": "00d23951aa24ef1b307daaf51bfbbf6cda7343e459656da1071a8a046a1c5fbb",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/dataset_index.py": "deeaa13cd608573bb3635b3274de88129b44bbcbdb09be982335278eea88a72c",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/datasets.py": "0c14f2852d8e4f5bf9b1cc28d3b2073bd3c63f2d94ed15d988a186f6d94508cf",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/desk_forward.py": "70ee85a54902bdaddd11d6c80bc75a4c8d7671eabd1038150e845f95bbc3f0c9",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/desk_meta_cache.py": "8f94c7b3e7dcfca3756dfd3fa945e3ad5d2c2f282cc4561a9d6d431648519d35",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/desk_playbook.py": "f059dcba80a7f09db8bcf74c4d2234c28aee5df2fb6bca32685cb30f8ba55bea",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/desk_playbook_context.py": "75537d161661b9660cf82896c56b60d92acdf3179fd77bd041c38ae45530fc23",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/desk_playbook_detect.py": "134e55a5e420d695ee79777d559994d94b4bd26392b563448c25e1c761a0e78c",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/desk_playbook_features.py": "ac9e9547a8c9a54a77c13dee0d5d6faeab8090cb92fce3743e94bf3fc4717e30",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/desk_sessions.py": "b1a3ba25118fae91ca7c450f19a7d51da53c703f4c03d6f6caf04d15cf18e84f",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/desk_universe.py": "56e63e96cf9fb93b844ee619af26e16d38ba75d755644671e0c95bcc2b88fbb8",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/edge_report.py": "f525154520be0aaece7fa116431dd76c5fb773de25a179614151397ecf77b207",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/edge_report_backtest_cache.py": "48fcdd26aa49152f862e4f69ea88371321e609c22e7c7abaa44334610670b831",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/edge_report_cache.py": "864ad668063aab1a7864ec69f0f69c4b25424e25cee7d91de3b564ca7c3e413c",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/edge_report_compute.py": "153f2a16cce854e26012009ac26b38f1c7581fa773caf653ea3da02fcc31920b",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/feed_basis.py": "949a024c76e2026104644d383d3e34204c52f8ff58899dcb6a403b620b21c9dc",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/foundry_compiler.py": "dc3a283eb8a4fb2c7a9eb8120a5637af012ec1dd2a5e9d8b896a3f7152465332",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/foundry_family.py": "b2c658e2429c16cafd1eba7e09bfc657018d2ba41b536b775e1ae8f896b7691d",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/foundry_freeze.py": "fbaae051783d5c579b2cf04e671c5e9c4552cbd46bd1a86e7201d00c3f7cf425",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/foundry_interpreter.py": "9f024c28c30baf0a9f310ba2191ddf4bc5f4572b5b7e623ead3dda5e8f74ca8f",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/foundry_ledger.py": "ddda14fb6c3b0c2ea29af9b19505891651bd751a3dcaa67bd6c8be6f78f0f4d1",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/foundry_runner.py": "83f340abe577d966fe6e538e29b0857d8e4f93ccb7b739f91be25c685a9131b5",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/foundry_source_registry.py": "c026938d75a42c5d4b1083b98972c8adf36275e877ccc24ee6be9476df1c4f80",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/levels.py": "dc3f518ccc78bb68359caef43d86b2cfa5796312dcad45e7d190a591f5b8265a",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/micro_accessor.py": "5f04efc3ad5dcfe6fbaca8f0a20a554b61aa54d8a9aa645f93d0faac7b538fdf",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/micro_chain_ledger.py": "c8e86991ba229dadad4b76342bd97c5ead1fe62d6373e5db94fdf053ccaebaff",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/micro_corpus.py": "563be84a24b731c672bb78921183acc8b28f90e8ec2968bcc77d9292f0f2b4ef",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/micro_features.py": "9c62be116d4cfcec37c89946fd89f5cc4b1c4219d87d9a93c798d816d4e297e5",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/micro_join.py": "7b6614b49df38ec97f04bdc4050bdb48e0f8d47ce056595f2a58a020561e54f4",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/micro_observer.py": "daf5c73f5cf3d9d8cd5dea96b7a65430b043cbb1d162d57e5d15ce787f2a6ad2",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/micro_readiness.py": "907acca0d17a907cd7a24cf73d3466ae26583217e7d576da19081310f6659f4b",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/micro_snapshots.py": "8b278395150c5b81d90773b21c8d0a0e738181a41fcaff3da4e9544fa4c1a9a1",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/pnl_ledger.py": "c2993326123aa83fa88c8771952a2a252d3153968a13d3752dc527a869870f7d",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/profiles.py": "8e43b1af01ec9ac337d19ffcce126a80a4d4deee231b2e84b6d1dd55a21c1884",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/referee_evidence.py": "482f38a11740bc839038290fc2a0e131f649a23f17265cbca0f2aa19fe07e1c5",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/referee_null.py": "34917e381e4169aa029f5d0e18228fde75e4d3db5acec516f937e3ef3b371603",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/referee_stats.py": "fba8816a5d4901ea1eeb7faa71e350538f546a2a3af1f9edb5f6f5aa1ec5271c",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/routes.py": "a52dfa246692926b5db476bffd5670b82c0f711773a456b5faf8affc50a40395",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/scout.py": "7fede1f37d688385c83b53c279b63c143cb9664e35ebf4154e8e908056b47ea8",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/scout_ledger.py": "1da1c689608bcad026d58f2f1acadeb12bd71a02ce806f3b6427291c0a31f0e3",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/setups.py": "be0938c81317871df37bd361b70f83099345bdf4e97adb7ea66e78519db16e51",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/setups_scan_cache.py": "68e1d0d0e00859005bdc3661ae89ba9c3e4babc5019e7b6be8602335f7098d47",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/store.py": "b0576a1c5c11c586e73d06ab735a17efa06a4bd24818c5b10167afc10d546a46",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/strategies.py": "1d8065b6c48b74257ae9d0dddfa617b53bd04922618e5afa7dc56d05eda209ff",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/taxonomy.py": "ed23c457b86070dca19afeb013437ca1c942d356407bed980ebff62a78e54166",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/tradability.py": "325e8ffc5ebd417b58c527f87247bee41c0290195df787184eef928ef668fa96",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/tradability_cache.py": "68b1d17c0e87bc96bb30c045fbb159f327fad534a8bc10b655e863bb98ce6102",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/vault.py": "4eae1054d631cf1ac27ec7b94a4417619d9ced24a0e2097d8c051bad1d803b0e",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/walkforward.py": "cd8ef818dc01011b1b736795abf74848a1c07dca54265db620c1fd366f6e3ddc",
-    "/home/dennis-chan/Git/tapeology/apps/backend/app/research/walkforward_ledger.py": "88f6062081987cc866b49a381ee70ec0804389a72fca9a5481cfe000e3f3f40d",
-    "/home/dennis-chan/Git/tapeology/docs/hypothesis-foundry-spec.md": "17beb618be5c325144e03eb760ef03e91771456a2e965f5f821009058df8ce82"
+    "apps/backend/app/research/algorithm_version.py": "ee28e8cfd1bd3583cf66002078204197bf0363eb8511816e01fe65bacfca6dc9",
+    "apps/backend/app/research/backtests.py": "c9536ba894fb1bf1e524c2dcced5868c426fd78ec2cc6a502569e47eaeea53e9",
+    "apps/backend/app/research/bar_index.py": "a40695360fe60307b73f29a092cfe816d92cd687eaf9fde57c701b9e07342a96",
+    "apps/backend/app/research/bar_verify_cache.py": "3a6945c0a6409d4cf2dc5df80b3981db295132ec223dd70f16df26f2bec71716",
+    "apps/backend/app/research/bars.py": "00d23951aa24ef1b307daaf51bfbbf6cda7343e459656da1071a8a046a1c5fbb",
+    "apps/backend/app/research/dataset_index.py": "deeaa13cd608573bb3635b3274de88129b44bbcbdb09be982335278eea88a72c",
+    "apps/backend/app/research/datasets.py": "0c14f2852d8e4f5bf9b1cc28d3b2073bd3c63f2d94ed15d988a186f6d94508cf",
+    "apps/backend/app/research/desk_forward.py": "70ee85a54902bdaddd11d6c80bc75a4c8d7671eabd1038150e845f95bbc3f0c9",
+    "apps/backend/app/research/desk_meta_cache.py": "8f94c7b3e7dcfca3756dfd3fa945e3ad5d2c2f282cc4561a9d6d431648519d35",
+    "apps/backend/app/research/desk_playbook.py": "f059dcba80a7f09db8bcf74c4d2234c28aee5df2fb6bca32685cb30f8ba55bea",
+    "apps/backend/app/research/desk_playbook_context.py": "75537d161661b9660cf82896c56b60d92acdf3179fd77bd041c38ae45530fc23",
+    "apps/backend/app/research/desk_playbook_detect.py": "134e55a5e420d695ee79777d559994d94b4bd26392b563448c25e1c761a0e78c",
+    "apps/backend/app/research/desk_playbook_features.py": "ac9e9547a8c9a54a77c13dee0d5d6faeab8090cb92fce3743e94bf3fc4717e30",
+    "apps/backend/app/research/desk_sessions.py": "b1a3ba25118fae91ca7c450f19a7d51da53c703f4c03d6f6caf04d15cf18e84f",
+    "apps/backend/app/research/desk_universe.py": "56e63e96cf9fb93b844ee619af26e16d38ba75d755644671e0c95bcc2b88fbb8",
+    "apps/backend/app/research/edge_report.py": "f525154520be0aaece7fa116431dd76c5fb773de25a179614151397ecf77b207",
+    "apps/backend/app/research/edge_report_backtest_cache.py": "48fcdd26aa49152f862e4f69ea88371321e609c22e7c7abaa44334610670b831",
+    "apps/backend/app/research/edge_report_cache.py": "864ad668063aab1a7864ec69f0f69c4b25424e25cee7d91de3b564ca7c3e413c",
+    "apps/backend/app/research/edge_report_compute.py": "153f2a16cce854e26012009ac26b38f1c7581fa773caf653ea3da02fcc31920b",
+    "apps/backend/app/research/feed_basis.py": "949a024c76e2026104644d383d3e34204c52f8ff58899dcb6a403b620b21c9dc",
+    "apps/backend/app/research/foundry_compiler.py": "dc3a283eb8a4fb2c7a9eb8120a5637af012ec1dd2a5e9d8b896a3f7152465332",
+    "apps/backend/app/research/foundry_family.py": "b2c658e2429c16cafd1eba7e09bfc657018d2ba41b536b775e1ae8f896b7691d",
+    "apps/backend/app/research/foundry_freeze.py": "12dfeb6ac5205c94ddd63fab5fe769105e50f7cc656c3047f9360426a5adb807",
+    "apps/backend/app/research/foundry_interpreter.py": "9f024c28c30baf0a9f310ba2191ddf4bc5f4572b5b7e623ead3dda5e8f74ca8f",
+    "apps/backend/app/research/foundry_ledger.py": "6a23bab81b9dd86f22c757dc71c8a7da6e37800f0c03c89c6cd1d891ee33c14f",
+    "apps/backend/app/research/foundry_runner.py": "64130765e1338ca2f0a3e11f279cac3ad2e1b6ba1c8123c0044aa55effe015b8",
+    "apps/backend/app/research/foundry_source_registry.py": "c026938d75a42c5d4b1083b98972c8adf36275e877ccc24ee6be9476df1c4f80",
+    "apps/backend/app/research/levels.py": "dc3f518ccc78bb68359caef43d86b2cfa5796312dcad45e7d190a591f5b8265a",
+    "apps/backend/app/research/micro_accessor.py": "5f04efc3ad5dcfe6fbaca8f0a20a554b61aa54d8a9aa645f93d0faac7b538fdf",
+    "apps/backend/app/research/micro_chain_ledger.py": "c8e86991ba229dadad4b76342bd97c5ead1fe62d6373e5db94fdf053ccaebaff",
+    "apps/backend/app/research/micro_corpus.py": "563be84a24b731c672bb78921183acc8b28f90e8ec2968bcc77d9292f0f2b4ef",
+    "apps/backend/app/research/micro_features.py": "9c62be116d4cfcec37c89946fd89f5cc4b1c4219d87d9a93c798d816d4e297e5",
+    "apps/backend/app/research/micro_join.py": "7b6614b49df38ec97f04bdc4050bdb48e0f8d47ce056595f2a58a020561e54f4",
+    "apps/backend/app/research/micro_observer.py": "daf5c73f5cf3d9d8cd5dea96b7a65430b043cbb1d162d57e5d15ce787f2a6ad2",
+    "apps/backend/app/research/micro_readiness.py": "907acca0d17a907cd7a24cf73d3466ae26583217e7d576da19081310f6659f4b",
+    "apps/backend/app/research/micro_snapshots.py": "8b278395150c5b81d90773b21c8d0a0e738181a41fcaff3da4e9544fa4c1a9a1",
+    "apps/backend/app/research/pnl_ledger.py": "c2993326123aa83fa88c8771952a2a252d3153968a13d3752dc527a869870f7d",
+    "apps/backend/app/research/profiles.py": "8e43b1af01ec9ac337d19ffcce126a80a4d4deee231b2e84b6d1dd55a21c1884",
+    "apps/backend/app/research/referee_evidence.py": "482f38a11740bc839038290fc2a0e131f649a23f17265cbca0f2aa19fe07e1c5",
+    "apps/backend/app/research/referee_null.py": "34917e381e4169aa029f5d0e18228fde75e4d3db5acec516f937e3ef3b371603",
+    "apps/backend/app/research/referee_stats.py": "fba8816a5d4901ea1eeb7faa71e350538f546a2a3af1f9edb5f6f5aa1ec5271c",
+    "apps/backend/app/research/routes.py": "a52dfa246692926b5db476bffd5670b82c0f711773a456b5faf8affc50a40395",
+    "apps/backend/app/research/scout.py": "7fede1f37d688385c83b53c279b63c143cb9664e35ebf4154e8e908056b47ea8",
+    "apps/backend/app/research/scout_ledger.py": "1da1c689608bcad026d58f2f1acadeb12bd71a02ce806f3b6427291c0a31f0e3",
+    "apps/backend/app/research/setups.py": "be0938c81317871df37bd361b70f83099345bdf4e97adb7ea66e78519db16e51",
+    "apps/backend/app/research/setups_scan_cache.py": "68e1d0d0e00859005bdc3661ae89ba9c3e4babc5019e7b6be8602335f7098d47",
+    "apps/backend/app/research/store.py": "b0576a1c5c11c586e73d06ab735a17efa06a4bd24818c5b10167afc10d546a46",
+    "apps/backend/app/research/strategies.py": "1d8065b6c48b74257ae9d0dddfa617b53bd04922618e5afa7dc56d05eda209ff",
+    "apps/backend/app/research/taxonomy.py": "ed23c457b86070dca19afeb013437ca1c942d356407bed980ebff62a78e54166",
+    "apps/backend/app/research/tradability.py": "325e8ffc5ebd417b58c527f87247bee41c0290195df787184eef928ef668fa96",
+    "apps/backend/app/research/tradability_cache.py": "68b1d17c0e87bc96bb30c045fbb159f327fad534a8bc10b655e863bb98ce6102",
+    "apps/backend/app/research/vault.py": "4eae1054d631cf1ac27ec7b94a4417619d9ced24a0e2097d8c051bad1d803b0e",
+    "apps/backend/app/research/walkforward.py": "cd8ef818dc01011b1b736795abf74848a1c07dca54265db620c1fd366f6e3ddc",
+    "apps/backend/app/research/walkforward_ledger.py": "88f6062081987cc866b49a381ee70ec0804389a72fca9a5481cfe000e3f3f40d",
+    "apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py": "9188fc370c0f391df6dbbebd78b5e52340d8429cc2b4826e6e31f48253f32f92",
+    "apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py": "a7a1e63b3e8a959db9ae1c9a7330650d97ba74b2e1ff06062ceb00d7d2263ff3",
+    "docs/hypothesis-foundry-spec.md": "17beb618be5c325144e03eb760ef03e91771456a2e965f5f821009058df8ce82",
+    "docs/hypothesis-foundry/epoch-manifest.json": "49d8de3f2608b9176af8a4b75124570ec90b60ba9a7b13227d6738cd4867d0c2",
+    "docs/hypothesis-foundry/source-registry.json": "d3bea09c93eb1298e14e60eff0178f52269461f746350e19c2e0d3b4c6165adb"
   },
-  "freeze_set_hash": "70fcd30237b463d5e61ea31ec80987995886531047c9031990a8269da7bb35b2"
+  "freeze_set_hash": "0b5a8364589ed06f44b3c3dc47f5454bb3fb57daa08748da744bee56719d5e12"
 }
\ No newline at end of file
```
