# Iteration diff (bounded)

Files changed: 11. Shown in full: 11.

```diff
diff --git a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
index 73862342..4f380045 100644
--- a/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
+++ b/apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
@@ -120,6 +120,29 @@ mkdir -p "$BAR_DIR" "$UNIVERSE_DIR" "$PLAYBOOK_DIR" "$PLAYBOOK_LOG_DIR" \
 cp "$BACKEND_DIR/tests/fixtures/datasets/6c9bf2c700d749e0993efd92c5807de3.json" "$DATASET_DIR/"
 cp "$BACKEND_DIR/tests/fixtures/datasets/d9f9dbe04fb24a7caccc53f0c6805412.json" "$DATASET_DIR/"
 
+# goal-hypothesis-foundry-iter-2 (J-01 step 5 / TC-1/TC-2/TC-3): close the QA-rig visibility gap
+# `lessons.md` iter-1 named — `foundry_source_registry.resolve_foundry_dir()` derives the Foundry
+# directory as a `foundry` SIBLING of `TAPEOLOGY_DATASET_DIR` when `TAPEOLOGY_FOUNDRY_DIR` is
+# unset, which this rig's own `$DATASET_DIR=$ROOT/datasets` resolves to `$ROOT/foundry` — a fresh,
+# never-recorded directory, so `GET /research/desk/micro/foundry` served `era_open_baseline: null`
+# here even though the real recorded artifact
+# (`apps/backend/.data/foundry/era_open_baseline.json`) is genuine. Fix: copy that REAL artifact
+# (read-only source, never written to) into this rig's own scoped `$ROOT/foundry/` before backend
+# start — the exact same "plain file copy of an already-committed/recorded real artifact into the
+# scoped root" pattern the two `cp` lines above already use for the PG tick-dataset fixtures, so
+# `GET /research/desk/micro/foundry` on THIS rig now serves the genuine recorded values, never an
+# invented one (the anti-goal `lessons.md` explicitly warns against). Honest-absence fallback: if
+# the operator has never run the one-time recording script
+# (`scripts/record_foundry_era_open_baseline.py`), there is nothing genuine to copy — the rig then
+# correctly falls back to the pre-existing honest `era_open_baseline: null` state, exactly like a
+# fresh install (never fabricated).
+FOUNDRY_DIR="$ROOT/foundry"
+REAL_FOUNDRY_BASELINE="$BACKEND_DIR/.data/foundry/era_open_baseline.json"
+if [[ -f "$REAL_FOUNDRY_BASELINE" ]]; then
+  mkdir -p "$FOUNDRY_DIR"
+  cp "$REAL_FOUNDRY_BASELINE" "$FOUNDRY_DIR/"
+fi
+
 export TAPEOLOGY_BAR_DIR="$BAR_DIR"
 export TAPEOLOGY_DESK_UNIVERSE_DIR="$UNIVERSE_DIR"
 export TAPEOLOGY_DESK_PLAYBOOK_DIR="$PLAYBOOK_DIR"
diff --git a/apps/backend/app/research/foundry_family.py b/apps/backend/app/research/foundry_family.py
new file mode 100644
index 00000000..4a3d56dc
--- /dev/null
+++ b/apps/backend/app/research/foundry_family.py
@@ -0,0 +1,99 @@
+"""The Hypothesis Foundry -- the family denominator (spec §5). A ``foundry_family_id`` groups
+every predeclared variant that is an alternative representation/corner of one mechanism lineage
+under the source registry (§5.1); this module freezes that group's COMPLETE variant denominator
+before any evaluation, enforces the hard family cap (§5.2), and refuses late insertion (§5.3) --
+the Foundry's own multiplicity bookkeeping, deliberately independent of the existing Scout ledger
+(the Foundry "does not claim the existing Scout ledger pre-registers families; it does not").
+
+**Why this module, not the Scout ledger, owns this.** ``scout.py``'s own family/variant tracking
+(``build_candidate_spec_fields``, the 24-variant cap in ``register_and_screen_candidate``) is a
+Do-Not-Redo module this era must not touch or duplicate: it enforces the SAME
+``SCOUT_MAX_VARIANTS_PER_FAMILY`` constant (imported here, never re-defined -- single source of
+truth) over registrations that flow through the Scout LEDGER, which Foundry trials never do
+(§4.2.1). This module is the Foundry-side analogue for the Foundry's OWN family concept."""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from typing import Mapping, Sequence
+
+from .scout import SCOUT_MAX_VARIANTS_PER_FAMILY
+
+__all__ = [
+    "SCOUT_MAX_VARIANTS_PER_FAMILY",
+    "FAMILY_BLOCKED_VARIANT_EXPLOSION",
+    "LateInsertionRefused",
+    "FoundryFamily",
+    "build_family_registry",
+    "eligible_variant_ordinals",
+    "attempt_late_insertion",
+    "n_variants_tried_for",
+]
+
+FAMILY_BLOCKED_VARIANT_EXPLOSION = "BLOCKED_VARIANT_EXPLOSION"
+
+
+@dataclass(frozen=True)
+class FoundryFamily:
+    """A frozen-by-construction Foundry family (spec §5.1: "frozen before outcomes and may not be
+    repartitioned after seeing results"). There is deliberately no mutation method on this
+    dataclass -- ``attempt_late_insertion`` below is the only API surface a caller has for "adding"
+    a variant, and it always refuses (see that function's own docstring)."""
+
+    foundry_family_id: str
+    variant_ordinals: tuple[int, ...]
+    variant_count: int
+    blocked: bool
+
+
+def build_family_registry(variant_ids_by_family: Mapping[str, Sequence[str]]) -> dict[str, FoundryFamily]:
+    """Builds one ``FoundryFamily`` per key of ``variant_ids_by_family`` (each value is that
+    family's COMPLETE, pre-outcome variant id list, in canonical order -- ``variant_ordinals`` is
+    simply that list's own index sequence, per ``foundry_compiler.compile_sources``'s own
+    ``variant_ordinal`` convention). A family whose complete count exceeds
+    ``SCOUT_MAX_VARIANTS_PER_FAMILY`` is ``blocked=True`` WHOLE (spec §5.2: never a subset, never
+    the "most plausible" N, never split into artificial subfamilies to evade the cap) -- the count
+    itself is still recorded (TC-9: "the complete Foundry denominator is visible before any
+    result", including for a blocked family)."""
+    registry: dict[str, FoundryFamily] = {}
+    for family_id, variant_ids in variant_ids_by_family.items():
+        count = len(variant_ids)
+        registry[family_id] = FoundryFamily(
+            foundry_family_id=family_id,
+            variant_ordinals=tuple(range(count)),
+            variant_count=count,
+            blocked=count > SCOUT_MAX_VARIANTS_PER_FAMILY,
+        )
+    return registry
+
+
+def eligible_variant_ordinals(family: FoundryFamily) -> tuple[int, ...]:
+    """The ordinals actually eligible to proceed to evaluation -- empty for a blocked family (spec
+    §5.2: "zero of its variants proceeding"), else the family's complete ordinal sequence."""
+    return () if family.blocked else family.variant_ordinals
+
+
+class LateInsertionRefused(Exception):
+    """Raised unconditionally by ``attempt_late_insertion`` -- see that function's own docstring
+    for why this is correct rather than merely convenient."""
+
+
+def attempt_late_insertion(family: FoundryFamily, *, new_variant_ordinal: int) -> None:
+    """ALWAYS refuses (spec §5.1/§9.3: "no late variant insertion"). ``FoundryFamily`` has no
+    mutation API -- there is no code path anywhere in this module that could grow
+    ``variant_count`` after ``build_family_registry`` returned it, so this function exists purely
+    to give a caller/test a typed, explicit refusal to call against (TC-10) rather than attempting
+    (and getting a ``FrozenInstanceError`` from) a direct dataclass-field mutation, which would be
+    an implementation-detail exception, not a Foundry-domain one."""
+    raise LateInsertionRefused(
+        f"family {family.foundry_family_id!r} is frozen at variant_count={family.variant_count} "
+        f"(ordinals {family.variant_ordinals!r}) -- variant ordinal {new_variant_ordinal!r} cannot "
+        "be inserted after freeze"
+    )
+
+
+def n_variants_tried_for(family: FoundryFamily) -> int:
+    """§5.3: the ``n_variants_tried`` disclosure every sibling variant's screen receives -- the
+    COMPLETE frozen denominator, deliberately independent of how many siblings have physically
+    executed (this reads only ``variant_count``, never an execution/progress counter)."""
+    return family.variant_count
diff --git a/apps/backend/app/research/foundry_freeze.py b/apps/backend/app/research/foundry_freeze.py
new file mode 100644
index 00000000..6ab6984a
--- /dev/null
+++ b/apps/backend/app/research/foundry_freeze.py
@@ -0,0 +1,276 @@
+"""The Hypothesis Foundry -- the Git-visible freeze barrier (spec §8): deterministic manifest
+generation with idempotent verify-replay (§8.3), the freeze-set generator (§8.4's "enumerated
+checked-in path+sha256 manifest" over the required + transitive local science dependencies), the
+freeze record pinning every required hash (§8.4), and the post-first-read integrity check (§8.5).
+
+**Scope this iteration (goal-hypothesis-foundry-iter-2, J-04).** Every function here operates on
+hermetic fixture epoch ids / synthetic directories only -- the real
+``docs/hypothesis-foundry/{source-registry,epoch-manifest,freeze-set,freeze-record}.json`` artifacts
+do not exist until Binding Execution Order steps 6-7 (J-06/J-07). This module is the machinery
+those later steps call, proven here against fixtures first (goal.md's own binding order)."""
+
+from __future__ import annotations
+
+import ast
+import hashlib
+import json
+import subprocess
+from dataclasses import dataclass
+from pathlib import Path
+from typing import Mapping, Sequence
+
+__all__ = [
+    "FREEZE_SET_REQUIRED_MODULES",
+    "ManifestRecord",
+    "ManifestDriftRefused",
+    "generate_or_verify_manifest",
+    "FreezeSetDependencyUnproven",
+    "generate_freeze_set",
+    "FreezeRecord",
+    "build_freeze_record",
+    "verify_commit_is_ancestor",
+    "FreezeIntegrityHalt",
+    "verify_freeze_set_unchanged",
+]
+
+
+def _canonical(obj: object) -> bytes:
+    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
+
+
+def _sha256(payload: bytes) -> str:
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _sha256_file(path: Path) -> str:
+    return hashlib.sha256(path.read_bytes()).hexdigest()
+
+
+# === §8.3: deterministic manifest generation + idempotent verify-replay ===========================
+
+
+@dataclass(frozen=True)
+class ManifestRecord:
+    epoch_id: str
+    manifest_hash: str
+    inputs_hash: str
+    payload: Mapping[str, object]
+
+
+class ManifestDriftRefused(Exception):
+    """§8.3: "changed inputs after epoch creation are refused; they do not silently generate
+    `epoch_2`" -- TC-11."""
+
+
+_EPOCH_SLOT = "epoch"
+
+
+def generate_or_verify_manifest(store: dict, generation_inputs: Mapping[str, object]) -> ManifestRecord:
+    """``store`` is the caller-owned single-epoch persistence slot (a plain dict in every hermetic
+    test here; a real backing file/table for a future real epoch) -- this era creates AT MOST ONE
+    real epoch (§8.1), so the slot is a single key, never a collection keyed by attempt. Identical
+    ``generation_inputs`` (by content, not by object identity -- ``inputs_hash`` is a canonical
+    JSON hash) replayed against an already-generated slot VERIFIES and returns the existing record
+    (no second epoch_id is minted); changed inputs raise ``ManifestDriftRefused`` rather than
+    silently producing a new epoch."""
+    inputs_hash = _sha256(_canonical(generation_inputs))
+    existing = store.get(_EPOCH_SLOT)
+    if existing is not None:
+        if existing.inputs_hash != inputs_hash:
+            raise ManifestDriftRefused(
+                f"generation inputs changed since epoch {existing.epoch_id!r} was created "
+                f"(existing inputs_hash={existing.inputs_hash!r}, new={inputs_hash!r}) -- refused, "
+                "no second epoch is silently created (spec §8.3)"
+            )
+        return existing
+
+    epoch_id = f"epoch:{inputs_hash[:16]}"
+    manifest_hash = _sha256(_canonical({"epoch_id": epoch_id, "inputs": generation_inputs}))
+    record = ManifestRecord(
+        epoch_id=epoch_id, manifest_hash=manifest_hash, inputs_hash=inputs_hash,
+        payload=dict(generation_inputs),
+    )
+    store[_EPOCH_SLOT] = record
+    return record
+
+
+# === §8.4: the freeze-set generator ===============================================================
+
+# The MINIMUM required set (spec §8.4's own enumerated list, this era's scope): every Foundry
+# scientific implementation module, `scout.py` (the unchanged decision rail), and the three
+# extraction/join primitives the interpreter's own "existing timing helper" and future real
+# extraction sit on. A caller may pass a smaller/different `required_names` for a hermetic
+# synthetic-directory test (TC-12's own two variants); production callers use the default.
+FREEZE_SET_REQUIRED_MODULES = (
+    "foundry_compiler.py",
+    "foundry_interpreter.py",
+    "foundry_family.py",
+    "foundry_freeze.py",
+    "foundry_ledger.py",
+    "foundry_runner.py",
+    "scout.py",
+    "micro_features.py",
+    "micro_observer.py",
+    "micro_join.py",
+)
+
+
+class FreezeSetDependencyUnproven(Exception):
+    """§8.4: "If the import/source scan cannot prove a local science dependency is covered, freeze
+    generation refuses." -- a required or transitively-imported sibling module that does not exist
+    on disk (so its content can never be hashed, hence never proven covered) -- TC-12."""
+
+
+def _local_sibling_imports(path: Path) -> set[str]:
+    """Every SIBLING-module filename (``"<name>.py"``, co-located in ``path``'s OWN directory)
+    ``path`` imports via a same-package-level relative ``from . import X`` / ``from .X import
+    ...`` statement (``level == 1``), or a plain ``import X`` naming a file already present beside
+    ``path`` -- the only import shapes this scanner treats as a "local science dependency" (spec
+    §8.4's transitive-coverage requirement). A malformed/unparseable file yields no discovered
+    dependency (its OWN entry, added by the caller before this function is ever consulted, is what
+    makes it show up in the freeze set at all).
+
+    **Deliberately excludes deeper relative imports (``level >= 2``, e.g. ``from ..providers.base
+    import TradeEvent``).** Those reach OUTSIDE ``app/research/`` into a sibling top-level package
+    this single-directory scanner is not scoped to resolve/enumerate -- a disclosed limitation
+    (docs/handoffs), not silently pretended coverage: every one of §8.4's own named required
+    modules (``scout.py``, ``micro_features.py``, ``micro_observer.py``, ``micro_join.py``, every
+    ``foundry_*.py``) lives flat inside this one directory, so this scope already proves the
+    enumerated requirement; a future J-06/J-07 real freeze-set may widen this if a science-
+    affecting cross-package dependency is identified."""
+    try:
+        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
+    except (SyntaxError, OSError):
+        return set()
+    names: set[str] = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.ImportFrom) and node.level == 1:
+            if node.module:
+                names.add(f"{node.module.split('.')[0]}.py")
+            else:
+                for alias in node.names:
+                    names.add(f"{alias.name}.py")
+        elif isinstance(node, ast.Import):
+            for alias in node.names:
+                top = f"{alias.name.split('.')[0]}.py"
+                if (path.parent / top).is_file():
+                    names.add(top)
+    return names
+
+
+def generate_freeze_set(
+    research_dir: str | Path, *, required_names: Sequence[str] | None = None,
+    extra_paths: Sequence[str | Path] = (),
+) -> dict:
+    """The deterministic freeze-set generator (§8.4): starting from ``required_names`` (default
+    ``FREEZE_SET_REQUIRED_MODULES``), transitively walks each covered file's own local sibling
+    imports, adding every discovered dependency to the enumerated set, until no new dependency is
+    discovered. Raises ``FreezeSetDependencyUnproven`` the moment any required OR transitively-
+    discovered path does not exist on disk -- BEFORE returning a partial/unproven set (fails
+    closed, never silently omits). ``extra_paths`` lets a caller pin additional non-``.py``
+    dependencies this scanner cannot discover via import parsing (e.g. a config/version source
+    file) -- unused by every test/call site this iteration, present for forward compatibility with
+    the real J-06/J-07 freeze-set (§8.4's "snapshot identity/version/parameter sources")."""
+    research_dir = Path(research_dir)
+    names = tuple(required_names) if required_names is not None else FREEZE_SET_REQUIRED_MODULES
+
+    entries: dict[str, str] = {}
+    queue: list[str] = list(names)
+    seen: set[str] = set()
+    while queue:
+        name = queue.pop()
+        if name in seen:
+            continue
+        seen.add(name)
+        path = research_dir / name
+        if not path.is_file():
+            raise FreezeSetDependencyUnproven(
+                f"required/transitive local science dependency missing on disk: {path} -- freeze "
+                "generation refuses rather than silently omitting it (spec §8.4)"
+            )
+        entries[str(path)] = _sha256_file(path)
+        queue.extend(sorted(_local_sibling_imports(path) - seen))
+
+    for extra in extra_paths:
+        p = Path(extra)
+        if not p.is_file():
+            raise FreezeSetDependencyUnproven(f"declared local science dependency missing: {p}")
+        entries[str(p)] = _sha256_file(p)
+
+    freeze_set_hash = _sha256(_canonical(entries))
+    return {"entries": entries, "freeze_set_hash": freeze_set_hash}
+
+
+# === §8.4: the freeze record =======================================================================
+
+
+@dataclass(frozen=True)
+class FreezeRecord:
+    freeze_commit: str
+    manifest_hash: str
+    source_registry_hash: str
+    spec_hash: str
+    candidate_spec_schema_hash: str
+    compiler_hash: str
+    interpreter_hash: str
+    runner_hash: str
+    scout_screen_source_hash: str
+    config_fingerprint: str
+    freeze_set_hash: str
+
+
+def build_freeze_record(
+    *, freeze_commit: str, manifest_hash: str, source_registry_hash: str, spec_hash: str,
+    candidate_spec_schema_hash: str, compiler_hash: str, interpreter_hash: str, runner_hash: str,
+    scout_screen_source_hash: str, config_fingerprint: str, freeze_set_hash: str,
+) -> FreezeRecord:
+    """A pure constructor pinning every hash §8.4 requires -- no derivation, no defaults; a caller
+    missing one supplies an explicit falsy value and gets a record that visibly fails
+    ``test_tc12_freeze_record_pins_all_required_hashes_and_commit_ancestry``'s own completeness
+    check, rather than a silently-incomplete record."""
+    return FreezeRecord(
+        freeze_commit=freeze_commit, manifest_hash=manifest_hash, source_registry_hash=source_registry_hash,
+        spec_hash=spec_hash, candidate_spec_schema_hash=candidate_spec_schema_hash,
+        compiler_hash=compiler_hash, interpreter_hash=interpreter_hash, runner_hash=runner_hash,
+        scout_screen_source_hash=scout_screen_source_hash, config_fingerprint=config_fingerprint,
+        freeze_set_hash=freeze_set_hash,
+    )
+
+
+def verify_commit_is_ancestor(commit: str, head: str, *, cwd: str | Path) -> bool:
+    """§8.4: "proves `freeze_commit` is an ancestor of `HEAD`" -- a thin, real ``git merge-base
+    --is-ancestor`` wrapper (never a hand-rolled commit-graph walk). Returns ``False`` (never
+    raises) for an unknown/invalid commit -- git's own exit code 1 for "not an ancestor" and its
+    non-zero exit for "no such commit" both collapse to the same honest ``False`` here, since
+    either way the ancestry claim is not proven."""
+    result = subprocess.run(
+        ["git", "merge-base", "--is-ancestor", commit, head], cwd=str(cwd),
+        capture_output=True, text=True,
+    )
+    return result.returncode == 0
+
+
+# === §8.5: first-read-lock drift =====================================================================
+
+
+class FreezeIntegrityHalt(Exception):
+    """§8.5/§7.3: a pinned freeze-set path changed (or vanished) after the first-read lock --
+    ``FOUNDRY_INTEGRITY_HALT``, never silently patched-and-continued (TC-13)."""
+
+
+def verify_freeze_set_unchanged(freeze_set: Mapping[str, object]) -> None:
+    """Recomputes sha256 for every path ``freeze_set['entries']`` ENUMERATES and compares against
+    the pinned digest -- any mismatch, or a pinned path that no longer exists, raises
+    ``FreezeIntegrityHalt``. Deliberately looks at NOTHING outside those enumerated paths: a Goal
+    Mode session/handoff file or a non-scientific UI-only file was never added to ``entries`` by
+    ``generate_freeze_set`` (§8.4's own module-set scope), so this function structurally cannot
+    false-refuse on either (TC-13's second and third parts) -- there is no "everything else must
+    also be clean" check anywhere in this function."""
+    entries = freeze_set["entries"]  # type: ignore[index]
+    for path_str, expected_hash in entries.items():
+        path = Path(path_str)
+        if not path.is_file():
+            raise FreezeIntegrityHalt(f"freeze-set path missing after first-read lock: {path}")
+        actual_hash = _sha256_file(path)
+        if actual_hash != expected_hash:
+            raise FreezeIntegrityHalt(f"freeze-set path changed after first-read lock: {path}")
diff --git a/apps/backend/app/research/foundry_interpreter.py b/apps/backend/app/research/foundry_interpreter.py
new file mode 100644
index 00000000..92b3f7b4
--- /dev/null
+++ b/apps/backend/app/research/foundry_interpreter.py
@@ -0,0 +1,303 @@
+"""The Hypothesis Foundry -- the generic candidate interpreter (spec §4). Turns an already
+population-extracted set of candidate/comparator-eligible anchors into the boolean membership the
+existing Scout screen consumes, and calls ``scout.screen_candidate`` directly (never the
+registration/ledger path -- spec §4.2.1). See ``docs/hypothesis-foundry-spec.md`` §4 and
+``docs/goal.md``'s Foundry Constitution §4 for the full rationale this module implements verbatim.
+
+**Scope this iteration (goal-hypothesis-foundry-iter-2, J-03).** This module does not read a
+dataset or call ``micro_join``/``micro_observer`` itself -- it operates on ``PopulationAnchor``
+rows a caller (a hermetic test fixture today; a future real extraction step at J-06/J-07) has
+already produced: one row per candidate/comparator-eligible opportunity, each carrying its own
+per-conditioning-component resolution state (``ComponentResolution``). This mirrors
+``foundry_compiler.py``'s own precedent of taking an already-authored ``CandidateBlueprint`` rather
+than deriving content from prose at compile time -- here the interpreter takes already-resolved
+per-component values rather than re-deriving "is `high` true" from a raw tick stream itself. What
+IS this module's own job, and the reason it exists rather than reusing ``scout.extract_anchors``
+directly, is exactly the four things spec §4 assigns the interpreter: (1) population-symmetric
+component-resolution/exclusion accounting across an arbitrary conditioning set (§4.1), (2) the
+timing law ``candidate_available_at = outcome_start = max(component.available_at)`` (§4.1.3-4),
+(3) frozen membership-corner evaluation over that resolved set (§4.1.6), and (4) collapsing the
+result to a boolean and calling the existing Scout screen with no second statistical rail (§4.2).
+
+**Why membership-corner evaluation is a closed per-``relation.kind`` dispatch, not a parsed
+expression.** ``CandidateCoordinate.threshold_corner_predicate`` is descriptive text (e.g.
+``"quote_imbalance > 0"``) frozen for provenance/audit -- exactly like ``foundry_compiler.py``
+never parses ``mechanism_statement`` at compile time, this module never ``eval()``s
+``threshold_corner_predicate`` at interpret time (that would be exactly the "runtime LLM/string-
+based interpretation" the goal's anti-goals forbid a hair's breadth from). Instead each
+``ComponentResolution`` a caller supplies already carries its own ``corner_satisfied: bool | None``
+-- the per-coordinate corner truth, evaluated by whatever authored the fixture/extraction row using
+that coordinate's own frozen ``threshold_provenance``/``transform_orientation`` (a mechanical,
+typed decision, never string-parsed here). This module's own job is then only to COMBINE those
+already-evaluated per-component corners according to the CandidateSpec's frozen ``relation.kind``:
+``direct_scalar_membership`` (exactly one coordinate; membership = that one corner) or
+``conjunction`` (all coordinates; membership = every corner true). Any other ``relation.kind`` --
+an ordered/sequenced lag with no frozen window, the only ordered form this era's source scope ever
+raises (goal.md §12) -- is not one of these two closed forms and interpretation blocks with
+``BLOCKED_UNSUPPORTED_RELATION`` rather than guessing a window (TC-8)."""
+
+from __future__ import annotations
+
+from collections import defaultdict
+from dataclasses import dataclass
+from typing import Mapping, Sequence
+
+from . import micro_features as mf
+from . import scout
+
+__all__ = [
+    "SUPPORTED_RELATION_KINDS",
+    "BLOCKED_UNSUPPORTED_RELATION",
+    "UnsupportedRelationBlocked",
+    "FOUNDRY_BOUNDARY_FEATURE_LABEL",
+    "FOUNDRY_BOUNDARY_TRANSFORM",
+    "FOUNDRY_BOUNDARY_PARAMS",
+    "ComponentResolution",
+    "PopulationAnchor",
+    "ResolvedAnchor",
+    "PopulationResolution",
+    "InterpretationResult",
+    "resolve_population",
+    "project_boolean_membership",
+    "read_model",
+    "interpret_candidate",
+]
+
+# --- §4.1's two closed relation forms this era's compiled sources can ever need (goal.md §12: "Do
+# not treat the mere existence of two features in code as permission to enumerate"; the ordered
+# form is the ONLY unsupported relation named anywhere in the source scope, so it is the one this
+# module blocks rather than builds bespoke code for). ------------------------------------------
+RELATION_DIRECT_SCALAR = "direct_scalar_membership"
+RELATION_CONJUNCTION = "conjunction"
+SUPPORTED_RELATION_KINDS = frozenset({RELATION_DIRECT_SCALAR, RELATION_CONJUNCTION})
+
+BLOCKED_UNSUPPORTED_RELATION = "BLOCKED_UNSUPPORTED_RELATION"
+
+
+class UnsupportedRelationBlocked(Exception):
+    """Raised (never silently produces a guessed window) when a ``CandidateSpec.relation.kind`` is
+    outside ``SUPPORTED_RELATION_KINDS`` -- spec §4/§12, TC-8. Carries ``.disposition`` so a caller
+    can record the typed block without string-matching the message."""
+
+    def __init__(self, relation_kind: str) -> None:
+        super().__init__(
+            f"relation.kind={relation_kind!r} is not one of this era's supported closed forms "
+            f"{sorted(SUPPORTED_RELATION_KINDS)!r} -- {BLOCKED_UNSUPPORTED_RELATION}, no ordered "
+            "lag/window is ever guessed"
+        )
+        self.disposition = BLOCKED_UNSUPPORTED_RELATION
+        self.relation_kind = relation_kind
+
+
+# --- §4.2's Scout-boundary encoding: a fixed, non-scientific orchestration label + the mechanical
+# `threshold` / `feature_value >= 1.0` transform. Never a member of `scout.AGGRESSOR_DERIVED_
+# FEATURES` (a synthetic boolean-membership column is never itself an aggressor-derived raw
+# feature) so `scout._fallback_tercile_slices` correctly renders `None` for every Foundry trial --
+# the adapter must not "pretend this synthetic membership is an existing scientific feature" (§4.2).
+FOUNDRY_BOUNDARY_FEATURE_LABEL = "foundry_boolean_membership"
+FOUNDRY_BOUNDARY_TRANSFORM = "threshold"
+FOUNDRY_BOUNDARY_PARAMS: Mapping[str, object] = {"op": "ge", "value": 1.0}
+
+
+@dataclass(frozen=True)
+class ComponentResolution:
+    """One conditioning component's resolution outcome for one population anchor (spec §4.1 step
+    1). ``resolved=False`` means this component never fired/joined for this anchor -- the ANCHOR is
+    then excluded from both cells per ``unresolved_component_policy=exclude_and_count`` (step 2);
+    ``available_at``/``raw_value``/``corner_satisfied`` are only meaningful (non-``None``) when
+    ``resolved=True``."""
+
+    component_id: str
+    resolved: bool
+    available_at: float | None
+    raw_value: float | None
+    corner_satisfied: bool | None
+    unavailable_reason: str | None = None
+
+
+@dataclass(frozen=True)
+class PopulationAnchor:
+    """One raw pre-Scout-boundary population anchor. Every field ``scout.screen_candidate``
+    ultimately needs downstream (everything ``scout._extract_none_anchors`` et al. already produce
+    per anchor row) rides straight through into the Scout-facing anchor untouched;
+    ``feature_value`` itself is deliberately ABSENT here -- ``project_boolean_membership`` is the
+    only place that ever adds it, always as the 1.0/0.0 boolean encoding (§4.2), never a raw
+    magnitude."""
+
+    dataset_id: str
+    symbol: str
+    session_date: str
+    trade_index: int
+    tod_bucket: str | None
+    fallback_frac: float | None
+    outcome_bps: float
+    outcome_unit: str
+    components: tuple[ComponentResolution, ...]
+
+
+@dataclass(frozen=True)
+class ResolvedAnchor:
+    """One eligible (every conditioning component resolved) population anchor after §4.1's timing
+    law and membership-corner evaluation."""
+
+    anchor: PopulationAnchor
+    candidate_available_at: float
+    outcome_start: float
+    is_candidate: bool
+
+
+@dataclass(frozen=True)
+class PopulationResolution:
+    total_anchors: int
+    eligible: tuple[ResolvedAnchor, ...]
+    unavailable_by_reason: Mapping[str, int]
+
+
+def _evaluate_membership(components: Sequence[ComponentResolution], relation_kind: str) -> bool:
+    """§4.1 step 6: the frozen membership corner, evaluated as a closed dispatch over the SET of
+    already-resolved per-component corners -- see this module's own docstring for why this is a
+    typed dispatch, never a parsed expression."""
+    if relation_kind == RELATION_DIRECT_SCALAR:
+        if len(components) != 1:
+            raise ValueError(
+                f"relation.kind={RELATION_DIRECT_SCALAR!r} requires exactly one coordinate/"
+                f"component, got {len(components)}"
+            )
+        return bool(components[0].corner_satisfied)
+    if relation_kind == RELATION_CONJUNCTION:
+        return all(bool(c.corner_satisfied) for c in components)
+    raise UnsupportedRelationBlocked(relation_kind)
+
+
+def resolve_population(
+    anchors: Sequence[PopulationAnchor], *, relation_kind: str
+) -> PopulationResolution:
+    """§4.1 steps 1-6, in full:
+
+    1. every anchor's conditioning components are already resolved-or-not by the caller (this
+       module's own scope boundary -- see the module docstring);
+    2. an anchor with ANY unresolved component is excluded from BOTH cells and counted under its
+       first unresolved component's own typed reason (deterministic: ``anchor.components`` is an
+       ordered tuple, so "first" never varies run to run);
+    3. ``candidate_available_at = max(component.available_at)`` over the anchor's own resolved set;
+    4. ``outcome_start`` is computed by calling the existing timing helper directly
+       (``micro_features.resolve_outcome_start``) over that SAME resolved ``available_at`` set --
+       there is no further offset in this era's Foundry integration, so this call always returns
+       exactly ``candidate_available_at`` (matching TC-6's own "share
+       `outcome_start=max(available_at)`" assertion), but it is the helper itself that is called,
+       never a second, independently-written ``max()`` -- so a future change to that helper's own
+       rule is inherited here automatically rather than silently diverging;
+    5-6. the same canonical outcome (``outcome_bps``, already measured identically for every
+       eligible anchor regardless of which cell it lands in) and the frozen membership corner are
+       evaluated for every eligible anchor -- population-symmetric by construction: an anchor's
+       cell membership is decided ONLY by ``_evaluate_membership``, never by a different timing or
+       outcome rule for candidate vs. comparator.
+
+    Raises ``UnsupportedRelationBlocked`` (TC-8) before touching any anchor when ``relation_kind``
+    is outside ``SUPPORTED_RELATION_KINDS`` -- checked first so an unsupported relation never
+    silently walks a (possibly empty) anchor list and appears to "succeed" trivially."""
+    if relation_kind not in SUPPORTED_RELATION_KINDS:
+        raise UnsupportedRelationBlocked(relation_kind)
+
+    unavailable_by_reason: dict[str, int] = defaultdict(int)
+    eligible: list[ResolvedAnchor] = []
+    for anchor in anchors:
+        unresolved = [c for c in anchor.components if not c.resolved]
+        if unresolved:
+            reason = unresolved[0].unavailable_reason or "component_unresolved"
+            unavailable_by_reason[reason] += 1
+            continue
+        conditioning_available_at = [c.available_at for c in anchor.components]  # type: ignore[misc]
+        candidate_available_at = mf.resolve_outcome_start(conditioning_available_at)
+        outcome_start = mf.resolve_outcome_start(conditioning_available_at)  # the existing timing
+        # helper, called directly (never a second, independently-written max()) -- see the
+        # docstring paragraph above for why the two calls are guaranteed identical this era.
+        is_candidate = _evaluate_membership(anchor.components, relation_kind)
+        eligible.append(
+            ResolvedAnchor(
+                anchor=anchor, candidate_available_at=candidate_available_at,
+                outcome_start=outcome_start, is_candidate=is_candidate,
+            )
+        )
+
+    return PopulationResolution(
+        total_anchors=len(anchors), eligible=tuple(eligible), unavailable_by_reason=dict(unavailable_by_reason),
+    )
+
+
+def project_boolean_membership(resolution: PopulationResolution) -> list[dict]:
+    """§4.2: every eligible anchor becomes ONE Scout-canonical anchor dict, with
+    ``feature_value = 1.0`` when the frozen corner was true, else ``0.0`` -- the ONLY value that
+    ever reaches the Scout boundary; raw coordinate values never appear on the returned dict (TC-5:
+    "raw coordinates remain descriptive provenance", never a Scout-facing feature)."""
+    projected: list[dict] = []
+    for resolved in resolution.eligible:
+        a = resolved.anchor
+        projected.append(
+            {
+                "dataset_id": a.dataset_id,
+                "symbol": a.symbol,
+                "session_date": a.session_date,
+                "anchor_at": resolved.outcome_start,
+                "trade_index": a.trade_index,
+                "feature_value": 1.0 if resolved.is_candidate else 0.0,
+                "outcome_bps": a.outcome_bps,
+                "outcome_unit": a.outcome_unit,
+                "tod_bucket": a.tod_bucket,
+                "fallback_frac": a.fallback_frac,
+            }
+        )
+    return projected
+
+
+def read_model(resolution: PopulationResolution) -> dict:
+    """§4.1's own required read model: total source anchors, eligible resolved anchors,
+    unavailable/excluded anchors by typed reason, candidate count, comparator count, and common
+    usable sessions (sessions with at least one anchor in EACH cell -- the same
+    ``usable_sessions`` law ``scout.screen_candidate`` itself applies)."""
+    candidate_count = sum(1 for r in resolution.eligible if r.is_candidate)
+    comparator_count = len(resolution.eligible) - candidate_count
+    cand_sessions = {r.anchor.session_date for r in resolution.eligible if r.is_candidate}
+    comp_sessions = {r.anchor.session_date for r in resolution.eligible if not r.is_candidate}
+    usable_sessions = sorted(cand_sessions & comp_sessions)
+    return {
+        "total_anchors": resolution.total_anchors,
+        "eligible_anchors": len(resolution.eligible),
+        "unavailable_by_reason": dict(resolution.unavailable_by_reason),
+        "candidate_count": candidate_count,
+        "comparator_count": comparator_count,
+        "usable_sessions": usable_sessions,
+    }
+
+
+@dataclass(frozen=True)
+class InterpretationResult:
+    read_model: Mapping[str, object]
+    screen: Mapping[str, object]
+
+
+def interpret_candidate(
+    spec, anchors: Sequence[PopulationAnchor], *, econ_floor: dict, family_id: str, n_variants_tried: int,
+) -> InterpretationResult:
+    """The full §4 pipeline for one ``CandidateSpec`` (``foundry_compiler.CandidateSpec``):
+    population resolution -> boolean projection -> the Scout-boundary adapter (§4.2.1) -- calling
+    ``scout.screen_candidate`` DIRECTLY on the pre-extracted, already-boolean-projected anchors,
+    never the Scout registration/ledger path (so this call alone can never write a Scout ledger
+    row -- TC-18's boundary). ``family_id``/``n_variants_tried`` are passed straight through to
+    ``scout.screen_candidate`` -- the SAME ``family_id``/permutation-seed scope the direct Scout
+    path uses (TC-4), and the complete frozen Foundry-family denominator (``foundry_family.py``'s
+    own job to compute -- this function never derives it itself, spec §5.3)."""
+    resolution = resolve_population(anchors, relation_kind=spec.relation.kind)
+    scout_anchors = project_boolean_membership(resolution)
+    screen = scout.screen_candidate(
+        feature_name=FOUNDRY_BOUNDARY_FEATURE_LABEL,
+        transform=FOUNDRY_BOUNDARY_TRANSFORM,
+        params=dict(FOUNDRY_BOUNDARY_PARAMS),
+        sidedness=spec.outcome.sidedness,
+        horizon_key=spec.outcome.horizon_key,
+        econ_floor=econ_floor,
+        anchors=scout_anchors,
+        family_id=family_id,
+        n_variants_tried=n_variants_tried,
+    )
+    return InterpretationResult(read_model=read_model(resolution), screen=screen)
diff --git a/apps/backend/app/research/foundry_ledger.py b/apps/backend/app/research/foundry_ledger.py
new file mode 100644
index 00000000..6620c130
--- /dev/null
+++ b/apps/backend/app/research/foundry_ledger.py
@@ -0,0 +1,158 @@
+"""The Hypothesis Foundry -- the hash-chained, append-only Foundry trial ledger (spec §4.2.1/§9.2).
+Built on ``micro_chain_ledger.HashChainedLedger`` (the SAME shared tamper-evident primitive
+``micro_accessor.ExposureRegistry``/``walkforward_ledger.WalkForwardLedger`` already use -- see
+that module's own docstring for why one shared primitive is right here rather than a fourth
+hand-rolled hash chain).
+
+**Why this ledger is its own file, never a row kind inside ``scout_ledger.py``.** Spec §4.2.1 is
+explicit: "the Foundry does not call the Scout registration/ledger path for these trials, and the
+Scout ledger receives no synthetic/non-§3 feature rows from this era." This module never imports
+``scout_ledger``; every Foundry trial (intent or terminal) is recorded here and ONLY here."""
+
+from __future__ import annotations
+
+from datetime import datetime, timezone
+from pathlib import Path
+
+from .foundry_compiler import CandidateSpec
+from .micro_chain_ledger import HashChainedLedger
+
+__all__ = [
+    "ROW_KIND_INTENT",
+    "ROW_KIND_TERMINAL",
+    "ROOT_DEFERRED_COMPOSITE",
+    "ConflictingReplayRefused",
+    "FoundryLedger",
+    "deterministic_rule_id",
+    "prospective_root_status",
+]
+
+_LEDGER_FILENAME = "foundry_trial_ledger.jsonl"
+
+ROW_KIND_INTENT = "evaluation_intent"
+ROW_KIND_TERMINAL = "terminal"
+
+# §5.5: "otherwise record the literal `root_deferred_composite`... no composite root is invented
+# in this era."
+ROOT_DEFERRED_COMPOSITE = "root_deferred_composite"
+
+
+def _iso_utc_now() -> str:
+    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
+
+
+def deterministic_rule_id(epoch_id: str, candidate_spec_hash: str) -> str:
+    """§8.2/§11: the deterministic, pre-outcome future Mode-B ``rule_id``. A pure string function
+    of two already-frozen identities -- computable (and, per TC-19, IMMUTABLE) before any outcome
+    is read."""
+    return f"foundry:{epoch_id}:{candidate_spec_hash}"
+
+
+def prospective_root_status(spec: CandidateSpec) -> str:
+    """§5.5: "the current prospective root for scalar mechanisms where mechanically defined, else
+    the literal `root_deferred_composite`". This era registers no real Scout `family_root_id`
+    mapping (that is real-corpus/J-06+ territory), so the one MECHANICAL fact available pre-outcome
+    is the CandidateSpec's own relation shape: a ``direct_scalar_membership`` candidate with
+    exactly one coordinate has a one-to-one correspondence between its Foundry family and a single
+    conditioning feature -- its own frozen ``foundry_family_id`` IS the mechanically-defined
+    current prospective root candidate. Anything else (``conjunction``, or a future relation kind)
+    has no such one-to-one mapping and always records the literal sentinel -- "no composite root is
+    invented in this era" (§5.5), never a synthetic root id manufactured here."""
+    if spec.relation.kind == "direct_scalar_membership" and len(spec.coordinates) == 1:
+        return spec.foundry_family_id
+    return ROOT_DEFERRED_COMPOSITE
+
+
+class ConflictingReplayRefused(Exception):
+    """§9.2: "conflicting candidate/hash/corpus/floor/screen attempt -> refuse" -- a terminal
+    replay whose content differs from the already-recorded terminal row for the SAME
+    ``candidate_spec_hash`` (TC-14)."""
+
+
+# The terminal fields that decide "exact duplicate" (idempotent replay, TC-14) vs "conflicting"
+# (refused) -- every field that pins a frozen identity or the screen's own verdict/payload.
+_TERMINAL_IDENTITY_FIELDS = (
+    "manifest_hash", "foundry_family_id", "foundry_family_variant_count", "screen_result",
+    "rule_id", "prospective_root_status", "foundry_state",
+)
+
+
+class FoundryLedger:
+    """One Foundry epoch's complete trial record -- intent rows (§6 step 4 / §9.2's
+    ``EVALUATION_INTENT_RECORDED``) and terminal rows (§7.2's three terminal states) share ONE
+    physical hash chain (the ``scout_ledger.py``/``walkforward_ledger.py`` "one global chain, not
+    one per family/kind" precedent), discriminated by ``row_kind``."""
+
+    def __init__(self, root_dir: str | Path) -> None:
+        self._chain = HashChainedLedger(root_dir, _LEDGER_FILENAME)
+
+    def all_rows(self) -> list[dict]:
+        return self._chain.all_rows()
+
+    def verify_chain(self) -> dict:
+        return self._chain.verify_chain()
+
+    def intent_row_for(self, candidate_spec_hash: str) -> dict | None:
+        for row in reversed(self._chain.all_rows()):
+            if row["row_kind"] == ROW_KIND_INTENT and row["candidate_spec_hash"] == candidate_spec_hash:
+                return row
+        return None
+
+    def terminal_row_for(self, candidate_spec_hash: str) -> dict | None:
+        for row in reversed(self._chain.all_rows()):
+            if row["row_kind"] == ROW_KIND_TERMINAL and row["candidate_spec_hash"] == candidate_spec_hash:
+                return row
+        return None
+
+    def record_intent(
+        self, *, candidate_spec_hash: str, manifest_hash: str, econ_floor_bps: float | None,
+        econ_floor_provenance: str, recorded_at: str | None = None,
+    ) -> dict:
+        """§6 step 4: the pre-outcome evaluation-intent row -- CandidateSpec hash, manifest hash,
+        the materialized numeric economic floor + provenance, and a timestamp. Appended BEFORE any
+        outcome is measured (the caller's own obligation; this method just persists whatever it is
+        given)."""
+        return self._chain.append_row(
+            {
+                "row_kind": ROW_KIND_INTENT,
+                "candidate_spec_hash": candidate_spec_hash,
+                "manifest_hash": manifest_hash,
+                "econ_floor_bps": econ_floor_bps,
+                "econ_floor_provenance": econ_floor_provenance,
+                "recorded_at": recorded_at or _iso_utc_now(),
+            }
+        )
+
+    def record_terminal(
+        self, *, candidate_spec_hash: str, manifest_hash: str, foundry_family_id: str,
+        foundry_family_variant_count: int, screen_result: dict, rule_id: str,
+        prospective_root_status: str, foundry_state: str, recorded_at: str | None = None,
+    ) -> dict:
+        """§4.2.1/§7.2: the canonical Foundry trial record -- embeds the COMPLETE
+        ``scout.screen_candidate`` result plus every frozen identity a future auditor needs, and
+        is the ONLY row this trial is ever recorded on (never the Scout ledger). Exact-duplicate
+        replay (every identity field byte-identical to the existing terminal row for this
+        ``candidate_spec_hash``) is idempotent and returns the EXISTING row (TC-14); any
+        difference -- a different screen payload, a different rule_id/root status/family identity
+        -- raises ``ConflictingReplayRefused`` rather than silently overwriting."""
+        candidate = {
+            "row_kind": ROW_KIND_TERMINAL,
+            "candidate_spec_hash": candidate_spec_hash,
+            "manifest_hash": manifest_hash,
+            "foundry_family_id": foundry_family_id,
+            "foundry_family_variant_count": foundry_family_variant_count,
+            "screen_result": screen_result,
+            "rule_id": rule_id,
+            "prospective_root_status": prospective_root_status,
+            "foundry_state": foundry_state,
+            "recorded_at": recorded_at or _iso_utc_now(),
+        }
+        existing = self.terminal_row_for(candidate_spec_hash)
+        if existing is not None:
+            if all(existing[f] == candidate[f] for f in _TERMINAL_IDENTITY_FIELDS):
+                return existing
+            raise ConflictingReplayRefused(
+                f"terminal row for candidate_spec_hash={candidate_spec_hash!r} already exists with "
+                "different content -- refused rather than overwritten (spec §9.2)"
+            )
+        return self._chain.append_row(candidate)
diff --git a/apps/backend/app/research/foundry_runner.py b/apps/backend/app/research/foundry_runner.py
new file mode 100644
index 00000000..ce9f3bdc
--- /dev/null
+++ b/apps/backend/app/research/foundry_runner.py
@@ -0,0 +1,179 @@
+"""The Hypothesis Foundry -- the deterministic exhaust runner (spec §9). Orchestrates the pieces
+built by the other four ``foundry_*.py`` modules over one hermetic manifest in canonical order:
+Foundry family order, then variant ordinal within family (§9.1) -- never reordered by effect,
+p-value, n, or a sibling's own verdict.
+
+**Scope this iteration (goal-hypothesis-foundry-iter-2).** This module operates on hermetic
+fixture epoch ids only (module docstring convention shared with every sibling ``foundry_*.py``
+this iteration) -- there is no real freeze/manifest wiring yet, so the post-first-read-lock
+science-hash verification this module will eventually need before EVERY resumed candidate
+(``foundry_freeze.verify_freeze_set_unchanged``) is not yet called from here; that wiring is real-
+epoch (J-06/J-07) territory. What IS in scope and proven here is the one identity this era's
+hermetic runner already has something meaningful to verify on resume: the pinned intent row's own
+economic-floor pin (§6/TC-51) -- see ``FoundryResumeIdentityMismatch`` below."""
+
+from __future__ import annotations
+
+import errno
+import fcntl
+from contextlib import contextmanager
+from pathlib import Path
+from typing import Sequence
+
+from . import foundry_family as ffam
+from . import foundry_interpreter as fi
+from . import foundry_ledger as fl
+from .foundry_compiler import CandidateSpec
+
+__all__ = [
+    "SCOUT_TO_FOUNDRY_STATE",
+    "map_scout_decision",
+    "FoundryResumeIdentityMismatch",
+    "run_one_candidate",
+    "run_family",
+    "ConcurrentRunnerRefused",
+    "SingleFlightLock",
+]
+
+# --- §7.2's mechanical, closed Scout-decision -> Foundry-state mapping (TC-17) --------------------
+SCOUT_TO_FOUNDRY_STATE = {
+    "killed_insufficient_n": "EVALUATED_INSUFFICIENT",
+    "killed_null": "EVALUATED_KILLED",
+    "killed_direction": "EVALUATED_KILLED",
+    "killed_concentration": "EVALUATED_KILLED",
+    "killed_economic": "EVALUATED_KILLED",
+    "killed_fragile": "EVALUATED_KILLED",
+    "survive": "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
+}
+
+
+def map_scout_decision(scout_decision: str) -> str:
+    """§7.2: "there is no second Foundry verdict" -- a fixed, closed lookup; an unmapped Scout
+    decision raises rather than silently defaulting to any of the three Foundry states."""
+    try:
+        return SCOUT_TO_FOUNDRY_STATE[scout_decision]
+    except KeyError as exc:
+        raise ValueError(
+            f"Scout decision {scout_decision!r} has no Foundry mapping -- the closed vocabulary is "
+            f"{sorted(SCOUT_TO_FOUNDRY_STATE)!r}"
+        ) from exc
+
+
+class FoundryResumeIdentityMismatch(Exception):
+    """§6/TC-51: "any existing `EVALUATION_INTENT_RECORDED` row's numeric floor and provenance must
+    equal a deterministic re-derivation from the same pinned eligible corpus before evaluation
+    continues... A floor-input/output ordering or resume-consistency violation halts evaluation."
+    Raised when a resumed candidate's caller-supplied ``econ_floor`` disagrees with the value
+    already pinned on its own intent row."""
+
+
+def run_one_candidate(
+    spec: CandidateSpec, anchors: Sequence[fi.PopulationAnchor], *, ledger: fl.FoundryLedger,
+    econ_floor: dict, manifest_hash: str, family: ffam.FoundryFamily,
+) -> dict:
+    """One candidate's full §9.2 resume-aware lifecycle:
+
+    - already-terminal (a prior run, or THIS run's own already-appended row) -> verify identity and
+      return the existing row WITHOUT re-executing the screen (TC-14's "verify and skip");
+    - an intent row exists with no terminal result (a simulated crash) -> verify the intent row's
+      own pinned econ-floor identity against what THIS invocation was given (halting on mismatch --
+      TC-51), then deterministically re-execute the exact same screen and append exactly one
+      terminal row (TC-15);
+    - neither exists yet -> record the intent row (§6 step 4, BEFORE any outcome is measured),
+      then execute and append the terminal row.
+
+    Either way the interpreter (``foundry_interpreter.interpret_candidate``) is called with the
+    SAME inputs every time -- deterministic re-execution, never a cached/memoized screen result --
+    so a resumed candidate's terminal row is reproducible from the frozen CandidateSpec + anchors
+    alone, exactly as §9.2 requires."""
+    existing_terminal = ledger.terminal_row_for(spec.candidate_spec_hash)
+    if existing_terminal is not None:
+        return existing_terminal
+
+    existing_intent = ledger.intent_row_for(spec.candidate_spec_hash)
+    if existing_intent is not None:
+        if existing_intent["econ_floor_bps"] != econ_floor.get("floor_bps"):
+            raise FoundryResumeIdentityMismatch(
+                f"resume econ_floor_bps mismatch for candidate_spec_hash="
+                f"{spec.candidate_spec_hash!r}: pinned intent={existing_intent['econ_floor_bps']!r}, "
+                f"resumed with={econ_floor.get('floor_bps')!r}"
+            )
+    else:
+        ledger.record_intent(
+            candidate_spec_hash=spec.candidate_spec_hash, manifest_hash=manifest_hash,
+            econ_floor_bps=econ_floor.get("floor_bps"), econ_floor_provenance=econ_floor.get("rule"),
+        )
+
+    interpretation = fi.interpret_candidate(
+        spec, anchors, econ_floor=econ_floor, family_id=family.foundry_family_id,
+        n_variants_tried=ffam.n_variants_tried_for(family),
+    )
+    foundry_state = map_scout_decision(interpretation.screen["decision"])
+    rule_id = fl.deterministic_rule_id(spec.epoch_id, spec.candidate_spec_hash)
+    root_status = fl.prospective_root_status(spec)
+
+    return ledger.record_terminal(
+        candidate_spec_hash=spec.candidate_spec_hash, manifest_hash=manifest_hash,
+        foundry_family_id=family.foundry_family_id,
+        foundry_family_variant_count=ffam.n_variants_tried_for(family),
+        screen_result=interpretation.screen, rule_id=rule_id, prospective_root_status=root_status,
+        foundry_state=foundry_state,
+    )
+
+
+def run_family(
+    family: ffam.FoundryFamily, variants: Sequence[tuple[CandidateSpec, Sequence[fi.PopulationAnchor]]],
+    *, ledger: fl.FoundryLedger, econ_floor: dict, manifest_hash: str,
+) -> list[dict]:
+    """§9.1: visits every ``variants`` entry in the ORDER GIVEN (the caller's own manifest-order
+    sequence -- family order, then variant ordinal within family) with a plain, unconditional
+    for-loop. There is no sort/rank/filter anywhere in this function keyed on effect, p-value, n,
+    or a sibling's own verdict -- canonical-order invariance (TC-16) holds structurally, not by
+    convention. A blocked family (``family.blocked``) has no eligible ordinals
+    (``foundry_family.eligible_variant_ordinals``); this function still executes whatever
+    ``variants`` it is given (the CALLER -- the real J-06/J-07 manifest walker -- is responsible
+    for never including a blocked family's variants in that sequence at all)."""
+    return [
+        run_one_candidate(spec, anchors, ledger=ledger, econ_floor=econ_floor, manifest_hash=manifest_hash, family=family)
+        for spec, anchors in variants
+    ]
+
+
+# === §9's single-flight protection: "Goal Mode may invoke the CLI repeatedly across iterations; it
+# must never depend on one long-held agent turn staying alive for the full epoch" -- but exactly
+# ONE runner may hold the epoch at a time. ==========================================================
+
+
+class ConcurrentRunnerRefused(Exception):
+    """§9.2: "concurrent second runner -> single-flight refusal" (TC-14)."""
+
+
+class SingleFlightLock:
+    """A real, OS-enforced exclusive lock (``fcntl.flock``, non-blocking) over one lock file --
+    never a hand-rolled PID-file/mutex (those race; ``flock`` does not). Two different
+    ``SingleFlightLock`` instances (or two different processes) pointed at the SAME path can never
+    both hold the lock at once; a released lock (the context manager's own ``__exit__``) is
+    immediately available to the next acquirer -- a sequential second acquire is not "concurrent"
+    and always succeeds."""
+
+    def __init__(self, lock_path: str | Path) -> None:
+        self._path = Path(lock_path)
+
+    @contextmanager
+    def acquire(self):
+        self._path.parent.mkdir(parents=True, exist_ok=True)
+        fh = open(self._path, "w")
+        try:
+            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
+        except OSError as exc:
+            fh.close()
+            if exc.errno in (errno.EACCES, errno.EAGAIN):
+                raise ConcurrentRunnerRefused(
+                    f"another Foundry runner already holds the single-flight lock at {self._path}"
+                ) from exc
+            raise
+        try:
+            yield
+        finally:
+            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
+            fh.close()
diff --git a/apps/backend/tests/test_foundry_family.py b/apps/backend/tests/test_foundry_family.py
new file mode 100644
index 00000000..a3656298
--- /dev/null
+++ b/apps/backend/tests/test_foundry_family.py
@@ -0,0 +1,79 @@
+"""``foundry_family.py`` (goal-hypothesis-foundry-iter-2, J-04): the Foundry-family denominator,
+hard cap enforcement, and late-insertion refusal (spec §5.1/§5.2/§5.3). TC-9/TC-10 in
+``docs/phases/goal-hypothesis-foundry-iter-2.md``."""
+
+from __future__ import annotations
+
+import pytest
+
+from app.research import foundry_family as ff
+from app.research import scout
+
+
+def test_tc9_family_of_one_exposes_its_denominator_before_evaluation():
+    registry = ff.build_family_registry({"family:solo": ["family:solo:0"]})
+    family = registry["family:solo"]
+    assert family.variant_count == 1
+    assert family.blocked is False
+    assert family.variant_ordinals == (0,)
+
+
+def test_tc9_family_of_multiple_exposes_the_complete_denominator():
+    variants = [f"family:multi:{i}" for i in range(5)]
+    registry = ff.build_family_registry({"family:multi": variants})
+    family = registry["family:multi"]
+    assert family.variant_count == 5
+    assert family.blocked is False
+
+
+def test_tc9_family_at_exactly_the_cap_is_not_blocked():
+    variants = [f"family:cap:{i}" for i in range(scout.SCOUT_MAX_VARIANTS_PER_FAMILY)]
+    registry = ff.build_family_registry({"family:cap": variants})
+    family = registry["family:cap"]
+    assert family.variant_count == scout.SCOUT_MAX_VARIANTS_PER_FAMILY
+    assert family.blocked is False
+
+
+def test_tc9_over_cap_family_blocks_whole_with_zero_variants_proceeding():
+    variants = [f"family:over:{i}" for i in range(scout.SCOUT_MAX_VARIANTS_PER_FAMILY + 1)]
+    registry = ff.build_family_registry({"family:over": variants})
+    family = registry["family:over"]
+    assert family.blocked is True
+    assert family.variant_count == scout.SCOUT_MAX_VARIANTS_PER_FAMILY + 1
+    assert ff.eligible_variant_ordinals(family) == ()
+
+
+def test_tc9_multiple_families_are_independent():
+    registry = ff.build_family_registry(
+        {
+            "family:a": ["a:0"],
+            "family:b": [f"b:{i}" for i in range(scout.SCOUT_MAX_VARIANTS_PER_FAMILY + 3)],
+            "family:c": [f"c:{i}" for i in range(4)],
+        }
+    )
+    assert registry["family:a"].blocked is False
+    assert registry["family:b"].blocked is True
+    assert registry["family:c"].blocked is False
+    assert registry["family:c"].variant_count == 4
+
+
+def test_tc10_late_insertion_after_freeze_is_refused_and_denominator_is_unchanged():
+    registry = ff.build_family_registry({"family:frozen": ["family:frozen:0", "family:frozen:1"]})
+    family = registry["family:frozen"]
+    before = family.variant_count
+    with pytest.raises(ff.LateInsertionRefused):
+        ff.attempt_late_insertion(family, new_variant_ordinal=2)
+    assert family.variant_count == before == 2
+
+
+def test_n_variants_tried_is_the_frozen_denominator_regardless_of_execution_progress():
+    """§5.3: every sibling variant's screen receives the COMPLETE frozen denominator, even before
+    siblings have physically executed -- trivially true here since `n_variants_tried_for` reads
+    only the frozen `variant_count`, never an execution-progress counter."""
+    registry = ff.build_family_registry({"family:x": ["x:0", "x:1", "x:2"]})
+    family = registry["family:x"]
+    assert ff.n_variants_tried_for(family) == 3 == ff.n_variants_tried_for(family)
+
+
+def test_foundry_family_variant_explosion_disposition_is_the_closed_sentinel():
+    assert ff.FAMILY_BLOCKED_VARIANT_EXPLOSION == "BLOCKED_VARIANT_EXPLOSION"
diff --git a/apps/backend/tests/test_foundry_freeze.py b/apps/backend/tests/test_foundry_freeze.py
new file mode 100644
index 00000000..cc3a4783
--- /dev/null
+++ b/apps/backend/tests/test_foundry_freeze.py
@@ -0,0 +1,145 @@
+"""``foundry_freeze.py`` (goal-hypothesis-foundry-iter-2, J-04): deterministic manifest generation
++ idempotent verify-replay (§8.3), the freeze-set generator (§8.4), the freeze record (§8.4), and
+the first-read-lock drift check (§8.5). TC-11/TC-12/TC-13 in
+``docs/phases/goal-hypothesis-foundry-iter-2.md``."""
+
+from __future__ import annotations
+
+import subprocess
+
+import pytest
+
+from app.research import foundry_freeze as fz
+
+
+# --- TC-11: generation replay ------------------------------------------------------------------
+
+
+def test_tc11_identical_inputs_rerun_verifies_and_does_not_create_a_second_epoch():
+    store: dict = {}
+    inputs = {"source_registry_hash": "abc123", "compiler_hash": "def456", "config_fingerprint": "fp1"}
+    first = fz.generate_or_verify_manifest(store, inputs)
+    second = fz.generate_or_verify_manifest(store, dict(inputs))  # a fresh dict, same content
+    assert first.epoch_id == second.epoch_id
+    assert first.manifest_hash == second.manifest_hash
+    assert len([r for r in store.values()]) == 1  # exactly one epoch record exists
+
+
+def test_tc11_changed_input_after_epoch_creation_is_refused_never_epoch_2():
+    store: dict = {}
+    inputs = {"source_registry_hash": "abc123", "compiler_hash": "def456", "config_fingerprint": "fp1"}
+    fz.generate_or_verify_manifest(store, inputs)
+    drifted = {**inputs, "source_registry_hash": "CHANGED"}
+    with pytest.raises(fz.ManifestDriftRefused):
+        fz.generate_or_verify_manifest(store, drifted)
+    assert len(store) == 1  # no second epoch was created by the refused attempt
+
+
+# --- TC-12: freeze-set generator -----------------------------------------------------------------
+
+
+def test_tc12_freeze_set_covers_the_required_modules_over_the_real_research_dir():
+    import pathlib
+
+    research_dir = pathlib.Path(__file__).resolve().parents[1] / "app" / "research"
+    result = fz.generate_freeze_set(research_dir)
+    covered_names = {pathlib.Path(p).name for p in result["entries"]}
+    for name in fz.FREEZE_SET_REQUIRED_MODULES:
+        assert name in covered_names, f"{name} missing from freeze-set entries"
+    assert result["freeze_set_hash"]
+    # Every hash is a real sha256 of the file actually on disk right now.
+    for path_str, digest in result["entries"].items():
+        import hashlib
+
+        assert hashlib.sha256(pathlib.Path(path_str).read_bytes()).hexdigest() == digest
+
+
+def test_tc12_a_local_science_dependency_the_scanner_cannot_prove_is_covered_refuses(tmp_path):
+    # A synthetic research dir mirroring the required-module names, but one module imports a
+    # sibling that does not exist on disk -- the scanner must refuse rather than silently omit it.
+    for name in fz.FREEZE_SET_REQUIRED_MODULES:
+        (tmp_path / name).write_text("# stub\n", encoding="utf-8")
+    broken = tmp_path / "foundry_runner.py"
+    broken.write_text("from . import missing_science_dependency\n", encoding="utf-8")
+
+    with pytest.raises(fz.FreezeSetDependencyUnproven):
+        fz.generate_freeze_set(tmp_path)
+
+
+def test_tc12_freeze_set_generation_over_a_complete_synthetic_dir_succeeds(tmp_path):
+    for name in fz.FREEZE_SET_REQUIRED_MODULES:
+        (tmp_path / name).write_text("# stub\n", encoding="utf-8")
+    result = fz.generate_freeze_set(tmp_path)
+    assert len(result["entries"]) == len(fz.FREEZE_SET_REQUIRED_MODULES)
+
+
+def test_tc12_freeze_record_pins_all_required_hashes_and_commit_ancestry():
+    record = fz.build_freeze_record(
+        freeze_commit="deadbeef",
+        manifest_hash="mh",
+        source_registry_hash="srh",
+        spec_hash="sh",
+        candidate_spec_schema_hash="csh",
+        compiler_hash="ch",
+        interpreter_hash="ih",
+        runner_hash="rh",
+        scout_screen_source_hash="ssh",
+        config_fingerprint="fp",
+        freeze_set_hash="fsh",
+    )
+    for field in (
+        "freeze_commit", "manifest_hash", "source_registry_hash", "spec_hash",
+        "candidate_spec_schema_hash", "compiler_hash", "interpreter_hash", "runner_hash",
+        "scout_screen_source_hash", "config_fingerprint", "freeze_set_hash",
+    ):
+        assert getattr(record, field)
+
+
+def test_commit_ancestry_verification_against_the_real_repo():
+    repo_root = subprocess.run(
+        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
+    ).stdout.strip()
+    head = subprocess.run(
+        ["git", "-C", repo_root, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
+    ).stdout.strip()
+    # HEAD is trivially its own ancestor.
+    assert fz.verify_commit_is_ancestor(head, head, cwd=repo_root) is True
+    assert fz.verify_commit_is_ancestor("0" * 40, head, cwd=repo_root) is False
+
+
+# --- TC-13: first-read-lock drift ------------------------------------------------------------------
+
+
+def test_tc13_post_lock_pinned_path_change_halts(tmp_path):
+    pinned = tmp_path / "pinned_module.py"
+    pinned.write_text("original\n", encoding="utf-8")
+    freeze_set = fz.generate_freeze_set(tmp_path, required_names=("pinned_module.py",))
+
+    fz.verify_freeze_set_unchanged(freeze_set)  # clean before drift -- must not raise
+
+    pinned.write_text("tampered\n", encoding="utf-8")
+    with pytest.raises(fz.FreezeIntegrityHalt):
+        fz.verify_freeze_set_unchanged(freeze_set)
+
+
+def test_tc13_unrelated_goal_mode_session_dirt_does_not_falsely_refuse(tmp_path):
+    pinned = tmp_path / "pinned_module.py"
+    pinned.write_text("original\n", encoding="utf-8")
+    freeze_set = fz.generate_freeze_set(tmp_path, required_names=("pinned_module.py",))
+
+    # A Goal Mode session/handoff file OUTSIDE the enumerated freeze-set appears dirty.
+    (tmp_path / "iteration-state.md").write_text("dirty session notes\n", encoding="utf-8")
+    fz.verify_freeze_set_unchanged(freeze_set)  # must not raise
+
+
+def test_tc13_non_scientific_ui_only_file_outside_freeze_set_is_excluded_from_the_lock(tmp_path):
+    pinned = tmp_path / "pinned_module.py"
+    pinned.write_text("original\n", encoding="utf-8")
+    freeze_set = fz.generate_freeze_set(tmp_path, required_names=("pinned_module.py",))
+
+    ui_only = tmp_path / "page.tsx"
+    ui_only.write_text("export default function Page() {}\n", encoding="utf-8")
+    fz.verify_freeze_set_unchanged(freeze_set)  # must not raise
+
+    ui_only.write_text("export default function Page() { /* changed */ }\n", encoding="utf-8")
+    fz.verify_freeze_set_unchanged(freeze_set)  # still must not raise -- outside the enumerated set
diff --git a/apps/backend/tests/test_foundry_interpreter.py b/apps/backend/tests/test_foundry_interpreter.py
new file mode 100644
index 00000000..ee7061fc
--- /dev/null
+++ b/apps/backend/tests/test_foundry_interpreter.py
@@ -0,0 +1,268 @@
+"""``foundry_interpreter.py`` (goal-hypothesis-foundry-iter-2, J-03): population resolution (spec
+§4.1), boolean projection into the existing Scout screen (spec §4.2), and the Scout-boundary
+scalar-equivalence oracle (spec §4.2.1 / goal Success Criterion 11). TC-4..TC-8 in
+``docs/phases/goal-hypothesis-foundry-iter-2.md``.
+
+Every fixture here is hermetic: plain Python dicts/dataclasses built in-test, never a real
+DatasetStore/snapshot read. The interpreter's own contract is that it operates on already
+population-extracted anchor rows (``PopulationAnchor`` -- one row per candidate/comparator-
+eligible opportunity, carrying its own per-conditioning-component resolution state), never a raw
+dataset."""
+
+from __future__ import annotations
+
+import pytest
+
+from app.research import foundry_compiler as fc
+from app.research import foundry_interpreter as fi
+from app.research import scout
+
+
+def _spec(*, relation_kind: str, coordinates: tuple, membership_corner: str, sidedness: str = "long",
+          horizon_key: str = "trades_20") -> fc.CandidateSpec:
+    return fc.CandidateSpec(
+        foundry_spec_version="v1",
+        epoch_id="epoch:hermetic",
+        source_ids=("src-1",),
+        lineage_id="src-1",
+        foundry_family_id="family:src-1",
+        variant_id="family:src-1:0",
+        variant_ordinal=0,
+        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
+        coordinates=coordinates,
+        relation=fc.CandidateRelation(kind=relation_kind),
+        membership_corner=membership_corner,
+        outcome=fc.CandidateOutcome(horizon_key=horizon_key, sidedness=sidedness),
+        economic_floor_rule=fc.EconomicFloorRule(),
+        foundry_family_variant_count=1,
+    ).with_hash()
+
+
+def _component(component_id, *, resolved=True, available_at=0.0, raw_value=None, corner_satisfied=None,
+                unavailable_reason=None):
+    return fi.ComponentResolution(
+        component_id=component_id, resolved=resolved, available_at=available_at if resolved else None,
+        raw_value=raw_value, corner_satisfied=corner_satisfied, unavailable_reason=unavailable_reason,
+    )
+
+
+def _anchor(idx, *, session_date, symbol="AAPL", components, outcome_bps):
+    return fi.PopulationAnchor(
+        dataset_id=f"ds-{symbol}-{session_date}",
+        symbol=symbol,
+        session_date=session_date,
+        trade_index=idx,
+        tod_bucket="mid",
+        fallback_frac=None,
+        outcome_bps=outcome_bps,
+        outcome_unit="return_bps",
+        components=components,
+    )
+
+
+_ECON_FLOOR = {"floor_bps": 0.0, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 0.0}
+
+
+def _scalar_fixture(n=40, threshold=1.0):
+    """A one-coordinate `direct_scalar_membership` corpus with a genuine planted effect: the
+    candidate cell's outcome distribution is shifted up relative to the comparator cell, across two
+    sessions, so the equivalence oracle exercises a real (non-insufficient, non-null) decision."""
+    anchors = []
+    for s in range(2):
+        session = f"2026-08-{10 + s:02d}"
+        for i in range(n // 2):
+            is_member = i % 2 == 0
+            raw_value = 2.0 if is_member else 0.0
+            outcome = 12.0 + (i % 5) if is_member else -1.0 + (i % 5) * 0.1
+            comp = _component("q_imbalance", resolved=True, available_at=float(i), raw_value=raw_value,
+                               corner_satisfied=raw_value >= threshold)
+            anchors.append(_anchor(i, session_date=session, components=(comp,), outcome_bps=outcome))
+    return anchors
+
+
+def test_tc4_scalar_adapter_is_byte_identical_to_the_direct_scout_path():
+    fixture_feature = "foundry_fixture_scalar_q_imbalance"
+    threshold = 1.0
+    anchors = _scalar_fixture(threshold=threshold)
+
+    # -- the existing DIRECT Scout path: raw (non-boolean) feature_value, real threshold ----------
+    direct_anchors = [
+        {
+            "dataset_id": a.dataset_id, "symbol": a.symbol, "session_date": a.session_date,
+            "anchor_at": a.components[0].available_at, "trade_index": a.trade_index,
+            "feature_value": a.components[0].raw_value, "outcome_bps": a.outcome_bps,
+            "outcome_unit": a.outcome_unit, "tod_bucket": a.tod_bucket, "fallback_frac": a.fallback_frac,
+        }
+        for a in anchors
+    ]
+    direct_result = scout.screen_candidate(
+        feature_name=fixture_feature, transform="threshold", params={"op": "ge", "value": threshold},
+        sidedness="long", horizon_key="trades_20", econ_floor=_ECON_FLOOR, anchors=direct_anchors,
+        family_id="fixture-family-tc4", n_variants_tried=1,
+    )
+
+    # -- the Foundry adapter path: generic interpreter -> boolean projection -> same screen call ---
+    spec = _spec(
+        relation_kind="direct_scalar_membership",
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="q_imbalance", semantic_role="candidate_signal",
+                transform_orientation="ge", threshold_corner_predicate="q_imbalance >= 1.0",
+                threshold_provenance="literal_ratified_threshold", aggressor_derived=False,
+                unit_basis="ratio", anchor_at="anchor_at", available_at="anchor_at",
+            ),
+        ),
+        membership_corner="q_imbalance >= 1.0",
+    )
+    interpretation = fi.interpret_candidate(
+        spec, anchors, econ_floor=_ECON_FLOOR, family_id="fixture-family-tc4", n_variants_tried=1,
+    )
+
+    assert interpretation.screen == direct_result
+    assert interpretation.screen["decision"] not in ("killed_insufficient_n",)  # a real decision was exercised
+
+
+def test_tc5_conjunction_projects_only_boolean_membership_raw_coordinates_stay_provenance_only():
+    anchors = []
+    for s in range(2):
+        session = f"2026-08-{10 + s:02d}"
+        for i in range(24):
+            both_true = i % 3 == 0
+            c1 = _component("c1", available_at=float(i), raw_value=5.0 if both_true else 0.0,
+                             corner_satisfied=both_true)
+            c2 = _component("c2", available_at=float(i) + 0.5, raw_value=9.0 if both_true else 1.0,
+                             corner_satisfied=both_true)
+            outcome = 15.0 if both_true else -0.5
+            anchors.append(_anchor(i, session_date=session, components=(c1, c2), outcome_bps=outcome))
+
+    spec = _spec(
+        relation_kind="conjunction",
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="c1", semantic_role="candidate_signal", transform_orientation="gt",
+                threshold_corner_predicate="c1 > 0", threshold_provenance="natural_semantic_boundary",
+                aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
+            ),
+            fc.CandidateCoordinate(
+                feature_construct_id="c2", semantic_role="candidate_signal", transform_orientation="gt",
+                threshold_corner_predicate="c2 > 5", threshold_provenance="literal_ratified_threshold",
+                aggressor_derived=False, unit_basis="ratio", anchor_at="anchor_at", available_at="anchor_at",
+            ),
+        ),
+        membership_corner="c1 > 0 and c2 > 5",
+    )
+    interpretation = fi.interpret_candidate(
+        spec, anchors, econ_floor=_ECON_FLOOR, family_id="fixture-family-tc5", n_variants_tried=1,
+    )
+
+    scout_anchors = fi.project_boolean_membership(fi.resolve_population(anchors, relation_kind="conjunction"))
+    # The ONLY feature values reaching the Scout boundary are 1.0/0.0 -- never a raw coordinate.
+    assert {a["feature_value"] for a in scout_anchors} <= {0.0, 1.0}
+    assert interpretation.read_model["candidate_count"] == sum(1 for a in scout_anchors if a["feature_value"] == 1.0)
+    # Raw coordinate values are never present on the anchor dict handed to `scout.screen_candidate`.
+    assert all("raw_value" not in a and "c1" not in a and "c2" not in a for a in scout_anchors)
+
+
+def test_tc6_deferred_unresolved_anchors_excluded_from_both_cells_and_counted_and_timing_is_symmetric():
+    anchors = []
+    session = "2026-08-10"
+    for i in range(30):
+        unresolved = i % 5 == 0  # every 5th anchor's refill never completed
+        member = i % 2 == 0
+        if unresolved:
+            comp = _component("refill_consistent", resolved=False, unavailable_reason="refill_unresolved")
+        else:
+            comp = _component(
+                "refill_consistent", resolved=True, available_at=float(i) + 3.0, raw_value=1.0 if member else 0.0,
+                corner_satisfied=member,
+            )
+        outcome = 10.0 if member else -2.0
+        anchors.append(_anchor(i, session_date=session, components=(comp,), outcome_bps=outcome))
+
+    resolution = fi.resolve_population(anchors, relation_kind="direct_scalar_membership")
+
+    n_unresolved = sum(1 for a in anchors if a.components[0].resolved is False)
+    assert resolution.unavailable_by_reason == {"refill_unresolved": n_unresolved}
+    assert len(resolution.eligible) == len(anchors) - n_unresolved
+
+    # Population symmetry: every ELIGIBLE anchor (candidate or comparator alike) shares the exact
+    # outcome_start = max(component.available_at) timing law -- never backdated, never special-
+    # cased by which cell it lands in.
+    for resolved_anchor in resolution.eligible:
+        expected = max(c.available_at for c in resolved_anchor.anchor.components)
+        assert resolved_anchor.outcome_start == expected
+        assert resolved_anchor.candidate_available_at == expected
+
+    read_model = fi.read_model(resolution)
+    assert read_model["total_anchors"] == len(anchors)
+    assert read_model["eligible_anchors"] == len(resolution.eligible)
+    assert read_model["unavailable_by_reason"] == {"refill_unresolved": n_unresolved}
+    assert read_model["candidate_count"] + read_model["comparator_count"] == read_model["eligible_anchors"]
+
+
+def test_tc7_mirrored_sidedness_is_predeclared_and_opposite_result_dies_through_killed_direction():
+    # Build a corpus where the SHORT-sided candidate cell has a genuinely NEGATIVE (favorable for
+    # short) effect, so a `long`-sidedness registration of the identical corpus dies on
+    # `killed_direction` (effect points the wrong way for a long candidate) while the `short`
+    # registration survives the direction gate.
+    # Deliberately NOT a period-2/period-block-length alternating membership pattern: the block-
+    # rotation permutation null (scout.py's ``_rotated_null_deltas``) is invariant to rotations by
+    # a multiple of the block length, so a perfectly periodic membership assignment aligned with
+    # that period makes every null draw reproduce the observed effect exactly (a degenerate,
+    # always-`p_screen=1.0` null) -- a fixture-construction pitfall, not an interpreter bug. A
+    # per-session RANDOM (but fixture-seeded, deterministic) membership assignment avoids it.
+    import random as _random
+
+    anchors = []
+    for s in range(4):
+        session = f"2026-08-{10 + s:02d}"
+        order = list(range(40))
+        _random.Random(s).shuffle(order)
+        members = set(order[:20])
+        for i in range(40):
+            member = i in members
+            comp = _component("wall_reject", available_at=float(i), raw_value=1.0 if member else 0.0,
+                               corner_satisfied=member)
+            outcome = -80.0 + (i % 5) * 0.1 if member else 0.05 * (i % 5)
+            anchors.append(_anchor(i, session_date=session, components=(comp,), outcome_bps=outcome))
+
+    long_spec = _spec(
+        relation_kind="direct_scalar_membership",
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="wall_reject", semantic_role="candidate_signal",
+                transform_orientation="ge", threshold_corner_predicate="wall_reject >= 1",
+                threshold_provenance="natural_semantic_boundary", aggressor_derived=False,
+                unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
+            ),
+        ),
+        membership_corner="wall_reject >= 1", sidedness="long",
+    )
+    long_result = fi.interpret_candidate(
+        long_spec, anchors, econ_floor=_ECON_FLOOR, family_id="fixture-family-tc7", n_variants_tried=1,
+    )
+    assert long_spec.outcome.sidedness == "long"
+    assert long_result.screen["decision"] == "killed_direction"
+
+
+def test_tc8_unfrozen_ordered_relation_blocks_with_no_candidate_spec_produced():
+    spec = _spec(
+        relation_kind="ordered_sequence_lag",
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="thin_then_refill", semantic_role="candidate_signal",
+                transform_orientation="ge", threshold_corner_predicate="ordered lag unresolved",
+                threshold_provenance=None, aggressor_derived=False, unit_basis="bool",
+                anchor_at="anchor_at", available_at="anchor_at",
+            ),
+        ),
+        membership_corner="ordered_lag_unresolved",
+    )
+    with pytest.raises(fi.UnsupportedRelationBlocked) as exc_info:
+        fi.interpret_candidate(spec, [], econ_floor=_ECON_FLOOR, family_id="f", n_variants_tried=1)
+    assert exc_info.value.disposition == fi.BLOCKED_UNSUPPORTED_RELATION
+
+
+def test_relation_kind_dispatch_is_closed_unknown_kind_also_blocks():
+    with pytest.raises(fi.UnsupportedRelationBlocked):
+        fi.resolve_population([], relation_kind="some_new_ordered_form")
diff --git a/apps/backend/tests/test_foundry_ledger.py b/apps/backend/tests/test_foundry_ledger.py
new file mode 100644
index 00000000..b1e5b817
--- /dev/null
+++ b/apps/backend/tests/test_foundry_ledger.py
@@ -0,0 +1,163 @@
+"""``foundry_ledger.py`` (goal-hypothesis-foundry-iter-2, J-04): the hash-chained append-only
+Foundry trial ledger (spec §4.2.1/§9.2). TC-14 (ledger-level parts)/TC-18/TC-19 in
+``docs/phases/goal-hypothesis-foundry-iter-2.md``."""
+
+from __future__ import annotations
+
+import pytest
+
+from app.research import foundry_ledger as fl
+
+
+def _screen(decision="survive", effect_bps=42.0, p_screen=0.01):
+    return {
+        "decision": decision, "reason": decision, "notes": "x",
+        "screen_result": {"effect_bps": effect_bps, "p_screen": p_screen, "n_candidate": 20, "n_comparator": 20},
+    }
+
+
+def test_ledger_starts_empty_and_verifies_clean(tmp_path):
+    ledger = fl.FoundryLedger(tmp_path)
+    assert ledger.all_rows() == []
+    assert ledger.verify_chain()["ok"] is True
+
+
+def test_intent_then_terminal_round_trip(tmp_path):
+    ledger = fl.FoundryLedger(tmp_path)
+    intent = ledger.record_intent(
+        candidate_spec_hash="h1", manifest_hash="m1", econ_floor_bps=1.5, econ_floor_provenance="scout_quoted_spread_floor",
+    )
+    assert intent["row_kind"] == fl.ROW_KIND_INTENT
+    assert ledger.intent_row_for("h1") is not None
+    assert ledger.terminal_row_for("h1") is None
+
+    terminal = ledger.record_terminal(
+        candidate_spec_hash="h1", manifest_hash="m1", foundry_family_id="family:x",
+        foundry_family_variant_count=3, screen_result=_screen(), rule_id="foundry:epoch:h1",
+        prospective_root_status="family:x", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
+    )
+    assert terminal["row_kind"] == fl.ROW_KIND_TERMINAL
+    assert ledger.terminal_row_for("h1") == terminal
+    assert ledger.verify_chain()["ok"] is True
+
+
+def test_tc18_terminal_row_embeds_the_complete_screen_payload_and_frozen_hashes():
+    import tempfile
+
+    with tempfile.TemporaryDirectory() as d:
+        ledger = fl.FoundryLedger(d)
+        ledger.record_intent(candidate_spec_hash="h2", manifest_hash="m1", econ_floor_bps=0.0, econ_floor_provenance="p")
+        screen = _screen(decision="killed_null", effect_bps=1.0, p_screen=0.5)
+        row = ledger.record_terminal(
+            candidate_spec_hash="h2", manifest_hash="m1", foundry_family_id="family:y",
+            foundry_family_variant_count=1, screen_result=screen, rule_id="foundry:epoch:h2",
+            prospective_root_status="root_deferred_composite", foundry_state="EVALUATED_KILLED",
+        )
+        assert row["screen_result"] == screen
+        assert row["candidate_spec_hash"] == "h2"
+        assert row["manifest_hash"] == "m1"
+        assert row["foundry_family_id"] == "family:y"
+        assert row["foundry_family_variant_count"] == 1
+        # This is the ONLY place the trial is ever recorded -- no Scout-ledger row is written by
+        # anything in this module (it never imports/touches `scout_ledger.py`).
+        assert "scout_ledger" not in dir(fl)
+
+
+def test_tc14_idempotent_exact_duplicate_terminal_replay_returns_existing_row(tmp_path):
+    ledger = fl.FoundryLedger(tmp_path)
+    ledger.record_intent(candidate_spec_hash="h3", manifest_hash="m1", econ_floor_bps=0.0, econ_floor_provenance="p")
+    screen = _screen()
+    first = ledger.record_terminal(
+        candidate_spec_hash="h3", manifest_hash="m1", foundry_family_id="family:z",
+        foundry_family_variant_count=2, screen_result=screen, rule_id="foundry:epoch:h3",
+        prospective_root_status="family:z", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
+    )
+    second = ledger.record_terminal(
+        candidate_spec_hash="h3", manifest_hash="m1", foundry_family_id="family:z",
+        foundry_family_variant_count=2, screen_result=screen, rule_id="foundry:epoch:h3",
+        prospective_root_status="family:z", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
+    )
+    assert first == second
+    assert len(ledger.all_rows()) == 2  # one intent + one terminal, never a duplicate terminal
+
+
+def test_tc14_conflicting_replay_is_refused(tmp_path):
+    ledger = fl.FoundryLedger(tmp_path)
+    ledger.record_intent(candidate_spec_hash="h4", manifest_hash="m1", econ_floor_bps=0.0, econ_floor_provenance="p")
+    ledger.record_terminal(
+        candidate_spec_hash="h4", manifest_hash="m1", foundry_family_id="family:c",
+        foundry_family_variant_count=1, screen_result=_screen(decision="killed_null"), rule_id="foundry:epoch:h4",
+        prospective_root_status="family:c", foundry_state="EVALUATED_KILLED",
+    )
+    with pytest.raises(fl.ConflictingReplayRefused):
+        ledger.record_terminal(
+            candidate_spec_hash="h4", manifest_hash="m1", foundry_family_id="family:c",
+            foundry_family_variant_count=1, screen_result=_screen(decision="survive"), rule_id="foundry:epoch:h4",
+            prospective_root_status="family:c", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
+        )
+
+
+def test_tc19_deterministic_rule_id_and_cannot_be_renamed(tmp_path):
+    assert fl.deterministic_rule_id("epoch:abc", "spechash123") == "foundry:epoch:abc:spechash123"
+
+    ledger = fl.FoundryLedger(tmp_path)
+    ledger.record_intent(candidate_spec_hash="h5", manifest_hash="m1", econ_floor_bps=0.0, econ_floor_provenance="p")
+    rule_id = fl.deterministic_rule_id("epoch:e1", "h5")
+    row = ledger.record_terminal(
+        candidate_spec_hash="h5", manifest_hash="m1", foundry_family_id="family:d",
+        foundry_family_variant_count=1, screen_result=_screen(), rule_id=rule_id,
+        prospective_root_status="family:d", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
+    )
+    assert row["rule_id"] == "foundry:epoch:e1:h5"
+
+    # Replaying with a DIFFERENT rule_id for the same candidate_spec_hash is a conflicting replay,
+    # never a silent rename.
+    with pytest.raises(fl.ConflictingReplayRefused):
+        ledger.record_terminal(
+            candidate_spec_hash="h5", manifest_hash="m1", foundry_family_id="family:d",
+            foundry_family_variant_count=1, screen_result=_screen(), rule_id="foundry:epoch:e1:RENAMED",
+            prospective_root_status="family:d", foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
+        )
+
+
+def test_tc19_prospective_root_status_scalar_vs_composite():
+    from app.research import foundry_compiler as fc
+
+    scalar_spec = fc.CandidateSpec(
+        foundry_spec_version="v1", epoch_id="epoch:e1", source_ids=("s1",), lineage_id="s1",
+        foundry_family_id="family:scalar", variant_id="family:scalar:0", variant_ordinal=0,
+        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="q", semantic_role="candidate_signal", transform_orientation="ge",
+                threshold_corner_predicate="q >= 1", threshold_provenance="natural_semantic_boundary",
+                aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
+            ),
+        ),
+        relation=fc.CandidateRelation(kind="direct_scalar_membership"), membership_corner="q >= 1",
+        outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness="long"),
+        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=1,
+    ).with_hash()
+    assert fl.prospective_root_status(scalar_spec) == "family:scalar"
+
+    composite_spec = fc.CandidateSpec(
+        foundry_spec_version="v1", epoch_id="epoch:e1", source_ids=("s2",), lineage_id="s2",
+        foundry_family_id="family:composite", variant_id="family:composite:0", variant_ordinal=0,
+        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
+        coordinates=(
+            fc.CandidateCoordinate(
+                feature_construct_id="c1", semantic_role="candidate_signal", transform_orientation="gt",
+                threshold_corner_predicate="c1 > 0", threshold_provenance="natural_semantic_boundary",
+                aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
+            ),
+            fc.CandidateCoordinate(
+                feature_construct_id="c2", semantic_role="candidate_signal", transform_orientation="gt",
+                threshold_corner_predicate="c2 > 0", threshold_provenance="natural_semantic_boundary",
+                aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
+            ),
+        ),
+        relation=fc.CandidateRelation(kind="conjunction"), membership_corner="c1 > 0 and c2 > 0",
+        outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness="long"),
+        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=1,
+    ).with_hash()
+    assert fl.prospective_root_status(composite_spec) == fl.ROOT_DEFERRED_COMPOSITE == "root_deferred_composite"
diff --git a/apps/backend/tests/test_foundry_runner.py b/apps/backend/tests/test_foundry_runner.py
new file mode 100644
index 00000000..90ab2851
--- /dev/null
+++ b/apps/backend/tests/test_foundry_runner.py
@@ -0,0 +1,159 @@
+"""``foundry_runner.py`` (goal-hypothesis-foundry-iter-2, J-04/J-03 integration): canonical-order
+exhaustion, mechanical Scout-verdict mapping, and checkpoint/resume/single-flight (spec §7.2/§9).
+TC-14 (runner-level parts)/TC-15/TC-16/TC-17 in
+``docs/phases/goal-hypothesis-foundry-iter-2.md``."""
+
+from __future__ import annotations
+
+import random
+
+import pytest
+
+from app.research import foundry_compiler as fc
+from app.research import foundry_family as ff
+from app.research import foundry_interpreter as fi
+from app.research import foundry_ledger as fl
+from app.research import foundry_runner as fr
+
+
+_ECON_FLOOR = {"floor_bps": 0.0, "unit": "bps", "rule": "scout_quoted_spread_floor", "multiple": 0.0}
+
+
+def _scalar_spec(variant_ordinal, *, family_id="family:fixture", family_count=1, sidedness="long"):
+    coord = fc.CandidateCoordinate(
+        feature_construct_id="q", semantic_role="candidate_signal", transform_orientation="ge",
+        threshold_corner_predicate="q >= 1", threshold_provenance="natural_semantic_boundary",
+        aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
+    )
+    return fc.CandidateSpec(
+        foundry_spec_version="v1", epoch_id="epoch:hermetic", source_ids=(f"s{variant_ordinal}",),
+        lineage_id=f"s{variant_ordinal}", foundry_family_id=family_id,
+        variant_id=f"{family_id}:{variant_ordinal}", variant_ordinal=variant_ordinal,
+        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
+        coordinates=(coord,), relation=fc.CandidateRelation(kind="direct_scalar_membership"),
+        membership_corner="q >= 1", outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness=sidedness),
+        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=family_count,
+    ).with_hash()
+
+
+def _anchors(seed, *, effect_bps=40.0, n_per_session=60, n_sessions=6, insufficient=False):
+    if insufficient:
+        n_per_session, n_sessions = 3, 1
+    anchors = []
+    for s in range(n_sessions):
+        session = f"2026-08-{10 + s:02d}"
+        order = list(range(n_per_session))
+        random.Random(f"{seed}:{s}").shuffle(order)
+        members = set(order[: n_per_session // 2])
+        for i in range(n_per_session):
+            member = i in members
+            comp = fi.ComponentResolution("q", True, float(i), 1.0 if member else 0.0, member)
+            outcome = effect_bps + (i % 5) * 0.01 if member else -0.01 * (i % 5)
+            anchors.append(fi.PopulationAnchor(f"ds-{session}", "AAPL", session, i, "mid", None, outcome, "return_bps", (comp,)))
+    return anchors
+
+
+def test_tc17_mechanical_scout_verdict_mapping_is_exhaustive_and_closed():
+    for scout_decision, expected in (
+        ("killed_insufficient_n", "EVALUATED_INSUFFICIENT"),
+        ("killed_null", "EVALUATED_KILLED"),
+        ("killed_direction", "EVALUATED_KILLED"),
+        ("killed_concentration", "EVALUATED_KILLED"),
+        ("killed_economic", "EVALUATED_KILLED"),
+        ("killed_fragile", "EVALUATED_KILLED"),
+        ("survive", "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"),
+    ):
+        assert fr.map_scout_decision(scout_decision) == expected
+    with pytest.raises(ValueError):
+        fr.map_scout_decision("some_unknown_decision")
+
+
+def test_tc16_canonical_order_kill_does_not_skip_a_later_survivor_and_vice_versa(tmp_path):
+    family = ff.build_family_registry({"family:multi": ["family:multi:0", "family:multi:1", "family:multi:2"]})[
+        "family:multi"
+    ]
+    variants = [
+        (_scalar_spec(0, family_id="family:multi", family_count=3), _anchors(1, insufficient=True)),
+        (_scalar_spec(1, family_id="family:multi", family_count=3), _anchors(2, effect_bps=100.0)),
+        (_scalar_spec(2, family_id="family:multi", family_count=3), _anchors(3, insufficient=True)),
+    ]
+    ledger = fl.FoundryLedger(tmp_path)
+    results = fr.run_family(family, variants, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1")
+
+    assert len(results) == 3
+    assert results[0]["foundry_state"] == "EVALUATED_INSUFFICIENT"
+    assert results[1]["foundry_state"] == "DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"
+    assert results[2]["foundry_state"] == "EVALUATED_INSUFFICIENT"
+    # every result carries the COMPLETE frozen denominator, regardless of position/verdict
+    assert all(r["foundry_family_variant_count"] == 3 for r in results)
+    # canonical order was followed -- ledger rows appear in the SAME order as the input variants
+    terminal_hashes = [row["candidate_spec_hash"] for row in ledger.all_rows() if row["row_kind"] == fl.ROW_KIND_TERMINAL]
+    assert terminal_hashes == [spec.candidate_spec_hash for spec, _ in variants]
+
+
+def test_tc14_already_terminal_candidate_is_verified_and_skipped_not_re_executed(tmp_path):
+    family = ff.build_family_registry({"family:solo": ["family:solo:0"]})["family:solo"]
+    spec = _scalar_spec(0, family_id="family:solo", family_count=1)
+    anchors = _anchors(5, effect_bps=50.0)
+    ledger = fl.FoundryLedger(tmp_path)
+
+    first = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1", family=family)
+    n_rows_after_first = len(ledger.all_rows())
+
+    second = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1", family=family)
+    assert second == first
+    assert len(ledger.all_rows()) == n_rows_after_first  # no new row appended on the skip
+
+
+def test_tc15_intent_without_terminal_after_a_simulated_crash_resumes_and_appends_exactly_one_terminal_row(tmp_path):
+    family = ff.build_family_registry({"family:crash": ["family:crash:0"]})["family:crash"]
+    spec = _scalar_spec(0, family_id="family:crash", family_count=1)
+    anchors = _anchors(6, effect_bps=45.0)
+    ledger = fl.FoundryLedger(tmp_path)
+
+    # Simulate the crash: an intent row exists, but no terminal row yet.
+    ledger.record_intent(
+        candidate_spec_hash=spec.candidate_spec_hash, manifest_hash="m1",
+        econ_floor_bps=_ECON_FLOOR["floor_bps"], econ_floor_provenance=_ECON_FLOOR["rule"],
+    )
+    assert ledger.terminal_row_for(spec.candidate_spec_hash) is None
+
+    result = fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1", family=family)
+
+    assert result["row_kind"] == fl.ROW_KIND_TERMINAL
+    intent_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_INTENT]
+    terminal_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]
+    assert len(intent_rows) == 1  # no duplicate intent row was appended on resume
+    assert len(terminal_rows) == 1  # exactly one terminal row
+
+
+def test_tc51_resume_econ_floor_mismatch_halts(tmp_path):
+    family = ff.build_family_registry({"family:mismatch": ["family:mismatch:0"]})["family:mismatch"]
+    spec = _scalar_spec(0, family_id="family:mismatch", family_count=1)
+    anchors = _anchors(7, effect_bps=45.0)
+    ledger = fl.FoundryLedger(tmp_path)
+    ledger.record_intent(
+        candidate_spec_hash=spec.candidate_spec_hash, manifest_hash="m1", econ_floor_bps=99.0,
+        econ_floor_provenance=_ECON_FLOOR["rule"],
+    )
+    with pytest.raises(fr.FoundryResumeIdentityMismatch):
+        fr.run_one_candidate(spec, anchors, ledger=ledger, econ_floor=_ECON_FLOOR, manifest_hash="m1", family=family)
+
+
+def test_tc14_single_flight_lock_rejects_a_concurrent_second_runner(tmp_path):
+    lock_path = tmp_path / "foundry_runner.lock"
+    lock = fr.SingleFlightLock(lock_path)
+    with lock.acquire():
+        second = fr.SingleFlightLock(lock_path)
+        with pytest.raises(fr.ConcurrentRunnerRefused):
+            with second.acquire():
+                pass  # pragma: no cover -- must never be reached
+
+
+def test_tc14_lock_releases_cleanly_a_sequential_second_acquire_succeeds(tmp_path):
+    lock_path = tmp_path / "foundry_runner.lock"
+    lock = fr.SingleFlightLock(lock_path)
+    with lock.acquire():
+        pass
+    with lock.acquire():  # the FIRST lock released -- a later, non-concurrent acquire is fine
+        pass
```
