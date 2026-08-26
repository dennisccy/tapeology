"""The Hypothesis Foundry -- the Git-visible freeze barrier (spec §8): deterministic manifest
generation with idempotent verify-replay (§8.3), the freeze-set generator (§8.4's "enumerated
checked-in path+sha256 manifest" over the required + transitive local science dependencies), the
freeze record pinning every required hash (§8.4), and the post-first-read integrity check (§8.5).

**Scope this iteration (goal-hypothesis-foundry-iter-2, J-04).** Every function here operates on
hermetic fixture epoch ids / synthetic directories only -- the real
``docs/hypothesis-foundry/{source-registry,epoch-manifest,freeze-set,freeze-record}.json`` artifacts
do not exist until Binding Execution Order steps 6-7 (J-06/J-07). This module is the machinery
those later steps call, proven here against fixtures first (goal.md's own binding order)."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

__all__ = [
    "FREEZE_SET_REQUIRED_MODULES",
    "ManifestRecord",
    "ManifestDriftRefused",
    "generate_or_verify_manifest",
    "FreezeSetDependencyUnproven",
    "generate_freeze_set",
    "FreezeRecord",
    "build_freeze_record",
    "verify_commit_is_ancestor",
    "FreezeIntegrityHalt",
    "verify_freeze_set_unchanged",
]


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# === §8.3: deterministic manifest generation + idempotent verify-replay ===========================


@dataclass(frozen=True)
class ManifestRecord:
    epoch_id: str
    manifest_hash: str
    inputs_hash: str
    payload: Mapping[str, object]


class ManifestDriftRefused(Exception):
    """§8.3: "changed inputs after epoch creation are refused; they do not silently generate
    `epoch_2`" -- TC-11."""


_EPOCH_SLOT = "epoch"


def generate_or_verify_manifest(store: dict, generation_inputs: Mapping[str, object]) -> ManifestRecord:
    """``store`` is the caller-owned single-epoch persistence slot (a plain dict in every hermetic
    test here; a real backing file/table for a future real epoch) -- this era creates AT MOST ONE
    real epoch (§8.1), so the slot is a single key, never a collection keyed by attempt. Identical
    ``generation_inputs`` (by content, not by object identity -- ``inputs_hash`` is a canonical
    JSON hash) replayed against an already-generated slot VERIFIES and returns the existing record
    (no second epoch_id is minted); changed inputs raise ``ManifestDriftRefused`` rather than
    silently producing a new epoch."""
    inputs_hash = _sha256(_canonical(generation_inputs))
    existing = store.get(_EPOCH_SLOT)
    if existing is not None:
        if existing.inputs_hash != inputs_hash:
            raise ManifestDriftRefused(
                f"generation inputs changed since epoch {existing.epoch_id!r} was created "
                f"(existing inputs_hash={existing.inputs_hash!r}, new={inputs_hash!r}) -- refused, "
                "no second epoch is silently created (spec §8.3)"
            )
        return existing

    epoch_id = f"epoch:{inputs_hash[:16]}"
    manifest_hash = _sha256(_canonical({"epoch_id": epoch_id, "inputs": generation_inputs}))
    record = ManifestRecord(
        epoch_id=epoch_id, manifest_hash=manifest_hash, inputs_hash=inputs_hash,
        payload=dict(generation_inputs),
    )
    store[_EPOCH_SLOT] = record
    return record


# === §8.4: the freeze-set generator ===============================================================

# The MINIMUM required set (spec §8.4's own enumerated list, this era's scope): every Foundry
# scientific implementation module, `scout.py` (the unchanged decision rail), and the three
# extraction/join primitives the interpreter's own "existing timing helper" and future real
# extraction sit on. A caller may pass a smaller/different `required_names` for a hermetic
# synthetic-directory test (TC-12's own two variants); production callers use the default.
FREEZE_SET_REQUIRED_MODULES = (
    "foundry_compiler.py",
    "foundry_interpreter.py",
    "foundry_family.py",
    "foundry_freeze.py",
    "foundry_ledger.py",
    "foundry_runner.py",
    "scout.py",
    "micro_features.py",
    "micro_observer.py",
    "micro_join.py",
)


class FreezeSetDependencyUnproven(Exception):
    """§8.4: "If the import/source scan cannot prove a local science dependency is covered, freeze
    generation refuses." -- a required or transitively-imported sibling module that does not exist
    on disk (so its content can never be hashed, hence never proven covered) -- TC-12."""


def _local_sibling_imports(path: Path) -> set[str]:
    """Every SIBLING-module filename (``"<name>.py"``, co-located in ``path``'s OWN directory)
    ``path`` imports via a same-package-level relative ``from . import X`` / ``from .X import
    ...`` statement (``level == 1``), or a plain ``import X`` naming a file already present beside
    ``path`` -- the only import shapes this scanner treats as a "local science dependency" (spec
    §8.4's transitive-coverage requirement). A malformed/unparseable file yields no discovered
    dependency (its OWN entry, added by the caller before this function is ever consulted, is what
    makes it show up in the freeze set at all).

    **Deliberately excludes deeper relative imports (``level >= 2``, e.g. ``from ..providers.base
    import TradeEvent``).** Those reach OUTSIDE ``app/research/`` into a sibling top-level package
    this single-directory scanner is not scoped to resolve/enumerate -- a disclosed limitation
    (docs/handoffs), not silently pretended coverage: every one of §8.4's own named required
    modules (``scout.py``, ``micro_features.py``, ``micro_observer.py``, ``micro_join.py``, every
    ``foundry_*.py``) lives flat inside this one directory, so this scope already proves the
    enumerated requirement; a future J-06/J-07 real freeze-set may widen this if a science-
    affecting cross-package dependency is identified."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, OSError):
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            if node.module:
                names.add(f"{node.module.split('.')[0]}.py")
            else:
                for alias in node.names:
                    names.add(f"{alias.name}.py")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                top = f"{alias.name.split('.')[0]}.py"
                if (path.parent / top).is_file():
                    names.add(top)
    return names


def generate_freeze_set(
    research_dir: str | Path, *, required_names: Sequence[str] | None = None,
    extra_paths: Sequence[str | Path] = (),
) -> dict:
    """The deterministic freeze-set generator (§8.4): starting from ``required_names`` (default
    ``FREEZE_SET_REQUIRED_MODULES``), transitively walks each covered file's own local sibling
    imports, adding every discovered dependency to the enumerated set, until no new dependency is
    discovered. Raises ``FreezeSetDependencyUnproven`` the moment any required OR transitively-
    discovered path does not exist on disk -- BEFORE returning a partial/unproven set (fails
    closed, never silently omits). ``extra_paths`` lets a caller pin additional non-``.py``
    dependencies this scanner cannot discover via import parsing (e.g. a config/version source
    file) -- unused by every test/call site this iteration, present for forward compatibility with
    the real J-06/J-07 freeze-set (§8.4's "snapshot identity/version/parameter sources")."""
    research_dir = Path(research_dir)
    names = tuple(required_names) if required_names is not None else FREEZE_SET_REQUIRED_MODULES

    entries: dict[str, str] = {}
    queue: list[str] = list(names)
    seen: set[str] = set()
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        path = research_dir / name
        if not path.is_file():
            raise FreezeSetDependencyUnproven(
                f"required/transitive local science dependency missing on disk: {path} -- freeze "
                "generation refuses rather than silently omitting it (spec §8.4)"
            )
        entries[str(path)] = _sha256_file(path)
        queue.extend(sorted(_local_sibling_imports(path) - seen))

    for extra in extra_paths:
        p = Path(extra)
        if not p.is_file():
            raise FreezeSetDependencyUnproven(f"declared local science dependency missing: {p}")
        entries[str(p)] = _sha256_file(p)

    freeze_set_hash = _sha256(_canonical(entries))
    return {"entries": entries, "freeze_set_hash": freeze_set_hash}


# === §8.4: the freeze record =======================================================================


@dataclass(frozen=True)
class FreezeRecord:
    freeze_commit: str
    manifest_hash: str
    source_registry_hash: str
    spec_hash: str
    candidate_spec_schema_hash: str
    compiler_hash: str
    interpreter_hash: str
    runner_hash: str
    scout_screen_source_hash: str
    config_fingerprint: str
    freeze_set_hash: str


def build_freeze_record(
    *, freeze_commit: str, manifest_hash: str, source_registry_hash: str, spec_hash: str,
    candidate_spec_schema_hash: str, compiler_hash: str, interpreter_hash: str, runner_hash: str,
    scout_screen_source_hash: str, config_fingerprint: str, freeze_set_hash: str,
) -> FreezeRecord:
    """A pure constructor pinning every hash §8.4 requires -- no derivation, no defaults; a caller
    missing one supplies an explicit falsy value and gets a record that visibly fails
    ``test_tc12_freeze_record_pins_all_required_hashes_and_commit_ancestry``'s own completeness
    check, rather than a silently-incomplete record."""
    return FreezeRecord(
        freeze_commit=freeze_commit, manifest_hash=manifest_hash, source_registry_hash=source_registry_hash,
        spec_hash=spec_hash, candidate_spec_schema_hash=candidate_spec_schema_hash,
        compiler_hash=compiler_hash, interpreter_hash=interpreter_hash, runner_hash=runner_hash,
        scout_screen_source_hash=scout_screen_source_hash, config_fingerprint=config_fingerprint,
        freeze_set_hash=freeze_set_hash,
    )


def verify_commit_is_ancestor(commit: str, head: str, *, cwd: str | Path) -> bool:
    """§8.4: "proves `freeze_commit` is an ancestor of `HEAD`" -- a thin, real ``git merge-base
    --is-ancestor`` wrapper (never a hand-rolled commit-graph walk). Returns ``False`` (never
    raises) for an unknown/invalid commit -- git's own exit code 1 for "not an ancestor" and its
    non-zero exit for "no such commit" both collapse to the same honest ``False`` here, since
    either way the ancestry claim is not proven."""
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, head], cwd=str(cwd),
        capture_output=True, text=True,
    )
    return result.returncode == 0


# === §8.5: first-read-lock drift =====================================================================


class FreezeIntegrityHalt(Exception):
    """§8.5/§7.3: a pinned freeze-set path changed (or vanished) after the first-read lock --
    ``FOUNDRY_INTEGRITY_HALT``, never silently patched-and-continued (TC-13)."""


def verify_freeze_set_unchanged(freeze_set: Mapping[str, object]) -> None:
    """Recomputes sha256 for every path ``freeze_set['entries']`` ENUMERATES and compares against
    the pinned digest -- any mismatch, or a pinned path that no longer exists, raises
    ``FreezeIntegrityHalt``. Deliberately looks at NOTHING outside those enumerated paths: a Goal
    Mode session/handoff file or a non-scientific UI-only file was never added to ``entries`` by
    ``generate_freeze_set`` (§8.4's own module-set scope), so this function structurally cannot
    false-refuse on either (TC-13's second and third parts) -- there is no "everything else must
    also be clean" check anywhere in this function."""
    entries = freeze_set["entries"]  # type: ignore[index]
    for path_str, expected_hash in entries.items():
        path = Path(path_str)
        if not path.is_file():
            raise FreezeIntegrityHalt(f"freeze-set path missing after first-read lock: {path}")
        actual_hash = _sha256_file(path)
        if actual_hash != expected_hash:
            raise FreezeIntegrityHalt(f"freeze-set path changed after first-read lock: {path}")
