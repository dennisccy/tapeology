"""``foundry_freeze.py`` (goal-hypothesis-foundry-iter-2, J-04): deterministic manifest generation
+ idempotent verify-replay (§8.3), the freeze-set generator (§8.4), the freeze record (§8.4), and
the first-read-lock drift check (§8.5). TC-11/TC-12/TC-13 in
``docs/phases/goal-hypothesis-foundry-iter-2.md``."""

from __future__ import annotations

import subprocess

import pytest

from app.research import foundry_freeze as fz


# --- TC-11: generation replay ------------------------------------------------------------------


def test_tc11_identical_inputs_rerun_verifies_and_does_not_create_a_second_epoch():
    store: dict = {}
    inputs = {"source_registry_hash": "abc123", "compiler_hash": "def456", "config_fingerprint": "fp1"}
    first = fz.generate_or_verify_manifest(store, inputs)
    second = fz.generate_or_verify_manifest(store, dict(inputs))  # a fresh dict, same content
    assert first.epoch_id == second.epoch_id
    assert first.manifest_hash == second.manifest_hash
    assert len([r for r in store.values()]) == 1  # exactly one epoch record exists


def test_tc11_changed_input_after_epoch_creation_is_refused_never_epoch_2():
    store: dict = {}
    inputs = {"source_registry_hash": "abc123", "compiler_hash": "def456", "config_fingerprint": "fp1"}
    fz.generate_or_verify_manifest(store, inputs)
    drifted = {**inputs, "source_registry_hash": "CHANGED"}
    with pytest.raises(fz.ManifestDriftRefused):
        fz.generate_or_verify_manifest(store, drifted)
    assert len(store) == 1  # no second epoch was created by the refused attempt


# --- TC-12: freeze-set generator -----------------------------------------------------------------


def test_tc12_freeze_set_covers_the_required_modules_over_the_real_research_dir():
    import pathlib

    research_dir = pathlib.Path(__file__).resolve().parents[1] / "app" / "research"
    result = fz.generate_freeze_set(research_dir)
    covered_names = {pathlib.Path(p).name for p in result["entries"]}
    for name in fz.FREEZE_SET_REQUIRED_MODULES:
        assert name in covered_names, f"{name} missing from freeze-set entries"
    assert result["freeze_set_hash"]
    # Every hash is a real sha256 of the file actually on disk right now.
    for path_str, digest in result["entries"].items():
        import hashlib

        assert hashlib.sha256(pathlib.Path(path_str).read_bytes()).hexdigest() == digest


def test_tc12_a_local_science_dependency_the_scanner_cannot_prove_is_covered_refuses(tmp_path):
    # A synthetic research dir mirroring the required-module names, but one module imports a
    # sibling that does not exist on disk -- the scanner must refuse rather than silently omit it.
    for name in fz.FREEZE_SET_REQUIRED_MODULES:
        (tmp_path / name).write_text("# stub\n", encoding="utf-8")
    broken = tmp_path / "foundry_runner.py"
    broken.write_text("from . import missing_science_dependency\n", encoding="utf-8")

    with pytest.raises(fz.FreezeSetDependencyUnproven):
        fz.generate_freeze_set(tmp_path)


def test_tc12_freeze_set_generation_over_a_complete_synthetic_dir_succeeds(tmp_path):
    for name in fz.FREEZE_SET_REQUIRED_MODULES:
        (tmp_path / name).write_text("# stub\n", encoding="utf-8")
    result = fz.generate_freeze_set(tmp_path)
    assert len(result["entries"]) == len(fz.FREEZE_SET_REQUIRED_MODULES)


def test_tc12_freeze_record_pins_all_required_hashes_and_commit_ancestry():
    record = fz.build_freeze_record(
        freeze_commit="deadbeef",
        manifest_hash="mh",
        source_registry_hash="srh",
        spec_hash="sh",
        candidate_spec_schema_hash="csh",
        compiler_hash="ch",
        interpreter_hash="ih",
        runner_hash="rh",
        scout_screen_source_hash="ssh",
        config_fingerprint="fp",
        freeze_set_hash="fsh",
    )
    for field in (
        "freeze_commit", "manifest_hash", "source_registry_hash", "spec_hash",
        "candidate_spec_schema_hash", "compiler_hash", "interpreter_hash", "runner_hash",
        "scout_screen_source_hash", "config_fingerprint", "freeze_set_hash",
    ):
        assert getattr(record, field)


def test_commit_ancestry_verification_against_the_real_repo():
    repo_root = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True
    ).stdout.strip()
    head = subprocess.run(
        ["git", "-C", repo_root, "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    # HEAD is trivially its own ancestor.
    assert fz.verify_commit_is_ancestor(head, head, cwd=repo_root) is True
    assert fz.verify_commit_is_ancestor("0" * 40, head, cwd=repo_root) is False


# --- TC-13: first-read-lock drift ------------------------------------------------------------------


def test_tc13_post_lock_pinned_path_change_halts(tmp_path):
    pinned = tmp_path / "pinned_module.py"
    pinned.write_text("original\n", encoding="utf-8")
    freeze_set = fz.generate_freeze_set(tmp_path, required_names=("pinned_module.py",))

    fz.verify_freeze_set_unchanged(freeze_set)  # clean before drift -- must not raise

    pinned.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(fz.FreezeIntegrityHalt):
        fz.verify_freeze_set_unchanged(freeze_set)


def test_tc13_unrelated_goal_mode_session_dirt_does_not_falsely_refuse(tmp_path):
    pinned = tmp_path / "pinned_module.py"
    pinned.write_text("original\n", encoding="utf-8")
    freeze_set = fz.generate_freeze_set(tmp_path, required_names=("pinned_module.py",))

    # A Goal Mode session/handoff file OUTSIDE the enumerated freeze-set appears dirty.
    (tmp_path / "iteration-state.md").write_text("dirty session notes\n", encoding="utf-8")
    fz.verify_freeze_set_unchanged(freeze_set)  # must not raise


def test_tc13_non_scientific_ui_only_file_outside_freeze_set_is_excluded_from_the_lock(tmp_path):
    pinned = tmp_path / "pinned_module.py"
    pinned.write_text("original\n", encoding="utf-8")
    freeze_set = fz.generate_freeze_set(tmp_path, required_names=("pinned_module.py",))

    ui_only = tmp_path / "page.tsx"
    ui_only.write_text("export default function Page() {}\n", encoding="utf-8")
    fz.verify_freeze_set_unchanged(freeze_set)  # must not raise

    ui_only.write_text("export default function Page() { /* changed */ }\n", encoding="utf-8")
    fz.verify_freeze_set_unchanged(freeze_set)  # still must not raise -- outside the enumerated set
