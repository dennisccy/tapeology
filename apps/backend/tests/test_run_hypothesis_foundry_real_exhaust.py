"""``scripts/run_hypothesis_foundry_real_exhaust.py`` (goal-hypothesis-foundry-iter-6, Binding
Execution Order step 8, J-07): the resumable, single-flight real exhaust CLI. TC-1..TC-6 in
``docs/phases/goal-hypothesis-foundry-iter-6.md``.

Every test here loads the script as a plain module (``importlib.util``, the same convention
``test_foundry_real_epoch_artifacts.py`` already uses for the generation script) rather than
shelling out to a subprocess -- cheap, and lets a test inject its own ``frozen_ready_families``
resolver / override paths directly.

Two flavors of test live here, deliberately:

* **Real-freeze tests** point ``tracked_dir``/``repo_root`` at the REAL committed
  ``docs/hypothesis-foundry/`` artifacts and this real repository -- proving freeze-set/freeze-
  record verification (B1/B2/B7's own fixes) genuinely passes against what is actually committed,
  and that the real committed manifest's ``families: []`` reaches an honest, vacuous completion.
  These use an ISOLATED ``foundry_dir``/``lock_path`` (``tmp_path``) and the small, fast,
  already-committed ``tests/fixtures/datasets`` corpus -- never the real, shared runtime ledger.
* **Fixture-freeze tests** build a synthetic ``tracked_dir`` from scratch (real
  ``foundry_freeze.generate_freeze_set``/``build_freeze_record`` over a tiny synthetic module set,
  pinned to a real commit of THIS repository for ancestry) so a test can inject an actual
  ``frozen_ready_families`` variant plan and exercise crash-resume/canonical-order through the
  exact same production sequence, per J-07 step 7's own explicit fixture allowance."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parents[1]
FOUNDRY_DOCS_DIR = REPO_ROOT / "docs" / "hypothesis-foundry"
FIXTURE_DATASET_DIR = Path(__file__).parent / "fixtures" / "datasets"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "_run_hypothesis_foundry_real_exhaust_under_test",
        BACKEND_DIR / "scripts" / "run_hypothesis_foundry_real_exhaust.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def exhaust_mod():
    return _load_module()


def _require_real_epoch_committed():
    if not (FOUNDRY_DOCS_DIR / "freeze-record.json").is_file():
        pytest.skip("the real Hypothesis Foundry epoch has not been generated in this checkout")


# === compute_eligible_corpus: sanctioned door, metadata only, deterministic ========================


def test_compute_eligible_corpus_hashes_only_metadata_and_matches_micro_corpus_formula(exhaust_mod):
    from app.research import micro_corpus
    from app.research.datasets import DatasetStore

    result = exhaust_mod.compute_eligible_corpus(str(FIXTURE_DATASET_DIR))
    assert result["withheld_excluded"] == 0  # no vault/universe registered over this fixture dir
    store = DatasetStore(FIXTURE_DATASET_DIR)
    records, errors = store.list()
    assert errors == []
    assert result["member_count"] == len(records)
    expected_hash = micro_corpus.corpus_manifest_hash(
        [{"dataset_id": r["id"], "checksum": r["checksum"]} for r in records]
    )
    assert result["manifest_hash"] == expected_hash

    # deterministic: a second call over the SAME corpus reproduces the identical hash.
    again = exhaust_mod.compute_eligible_corpus(str(FIXTURE_DATASET_DIR))
    assert again["manifest_hash"] == result["manifest_hash"]


def test_compute_eligible_corpus_over_an_empty_dataset_dir_is_honest_and_deterministic(exhaust_mod, tmp_path):
    empty = tmp_path / "empty-datasets"
    empty.mkdir()
    result = exhaust_mod.compute_eligible_corpus(str(empty))
    assert result["member_count"] == 0
    assert result["withheld_excluded"] == 0
    assert result["manifest_hash"]  # a real, deterministic hash over an empty member list


# === _default_frozen_ready_families: honest-empty vs fail-closed on a non-empty family ============


def test_default_resolver_returns_empty_plan_for_the_real_zero_family_manifest_shape(exhaust_mod):
    plan = exhaust_mod._default_frozen_ready_families({"families": []})
    assert plan == []


def test_default_resolver_honestly_completes_a_zero_variant_family_entry(exhaust_mod):
    manifest = {"families": [{"foundry_family_id": "family:test-zero-variant", "variants": []}]}
    plan = exhaust_mod._default_frozen_ready_families(manifest)
    assert len(plan) == 1
    family, variants = plan[0]
    assert family.foundry_family_id == "family:test-zero-variant"
    assert family.variant_count == 0
    assert variants == []


def test_default_resolver_refuses_a_non_empty_family_entry_rather_than_mis_evaluating(exhaust_mod):
    manifest = {
        "families": [
            {"foundry_family_id": "family:test-non-empty", "variants": [{"variant_id": "family:test-non-empty:0"}]}
        ]
    }
    with pytest.raises(exhaust_mod.RealCandidateEvaluationUnsupported):
        exhaust_mod._default_frozen_ready_families(manifest)


# === run_real_exhaust against the REAL committed freeze-set/freeze-record/manifest ================


def test_tc1_tc3_tc4_first_invocation_against_the_real_manifest_writes_the_epoch_open_row(exhaust_mod, tmp_path):
    _require_real_epoch_committed()
    foundry_dir = tmp_path / "foundry"
    lock_path = tmp_path / "exhaust.lock"

    result = exhaust_mod.run_real_exhaust(
        tracked_dir=FOUNDRY_DOCS_DIR, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
        foundry_dir=str(foundry_dir), lock_path=lock_path,
    )
    assert result["epoch_open"]["row_kind"] == "epoch_open"
    assert result["eligible_corpus_manifest_hash"]
    # TC-4: nothing in this sequence ever reads a snapshot row -- zero by construction.
    assert result["protected_read_count"] == 0
    # TC-3: the real committed manifest has zero FROZEN_READY variants.
    assert result["frozen_ready_total"] == 0
    assert result["terminal_count"] == 0
    assert result["exhaust_complete"] is True

    from app.research import foundry_ledger as fl

    ledger = fl.FoundryLedger(foundry_dir)
    epoch_open_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_EPOCH_OPEN]
    assert len(epoch_open_rows) == 1


def test_tc2_second_invocation_verifies_and_appends_no_second_epoch_open_row(exhaust_mod, tmp_path):
    _require_real_epoch_committed()
    foundry_dir = tmp_path / "foundry"
    lock_path = tmp_path / "exhaust.lock"
    kwargs = dict(
        tracked_dir=FOUNDRY_DOCS_DIR, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
        foundry_dir=str(foundry_dir), lock_path=lock_path,
    )
    first = exhaust_mod.run_real_exhaust(**kwargs)
    second = exhaust_mod.run_real_exhaust(**kwargs)
    assert first["epoch_open"] == second["epoch_open"]

    from app.research import foundry_ledger as fl

    ledger = fl.FoundryLedger(foundry_dir)
    epoch_open_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_EPOCH_OPEN]
    assert len(epoch_open_rows) == 1  # no duplicate first-read-lock row


def test_tc6_concurrent_invocation_is_refused_via_the_real_single_flight_lock(exhaust_mod, tmp_path):
    _require_real_epoch_committed()
    from app.research import foundry_runner as fr

    foundry_dir = tmp_path / "foundry"
    lock_path = tmp_path / "exhaust.lock"
    with fr.SingleFlightLock(lock_path).acquire():
        with pytest.raises(fr.ConcurrentRunnerRefused):
            exhaust_mod.run_real_exhaust(
                tracked_dir=FOUNDRY_DOCS_DIR, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
                foundry_dir=str(foundry_dir), lock_path=lock_path,
            )
    # the refused attempt appended no ledger row at all.
    from app.research import foundry_ledger as fl

    ledger = fl.FoundryLedger(foundry_dir)
    assert ledger.all_rows() == []


def test_freeze_ancestry_unproven_when_freeze_commit_does_not_verify(exhaust_mod, tmp_path):
    """A tampered ``freeze_commit`` (never an ancestor of HEAD) halts BEFORE the single-flight lock
    is even acquired or any ledger row is written."""
    _require_real_epoch_committed()
    tracked_dir = tmp_path / "tracked"
    tracked_dir.mkdir()
    for name in ("freeze-set.json", "epoch-manifest.json"):
        (tracked_dir / name).write_text((FOUNDRY_DOCS_DIR / name).read_text(encoding="utf-8"), encoding="utf-8")
    real_freeze_record = json.loads((FOUNDRY_DOCS_DIR / "freeze-record.json").read_text(encoding="utf-8"))
    tampered = {**real_freeze_record, "freeze_commit": "0" * 40}
    (tracked_dir / "freeze-record.json").write_text(json.dumps(tampered), encoding="utf-8")

    with pytest.raises(exhaust_mod.FreezeAncestryUnproven):
        exhaust_mod.run_real_exhaust(
            tracked_dir=tracked_dir, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
            foundry_dir=str(tmp_path / "foundry"), lock_path=tmp_path / "exhaust.lock",
        )


# === fixture-backed crash-resume through the SAME real production sequence (J-07 step 7) ==========


def _git(*args, cwd) -> str:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True).stdout.strip()


def _build_fixture_tracked_dir(tmp_path: Path) -> Path:
    """A synthetic ``tracked_dir`` (real ``generate_freeze_set``/``build_freeze_record`` output,
    over a tiny synthetic module directory, pinned to THIS repository's real current HEAD for a
    genuinely provable ancestry check) plus a synthetic ``epoch-manifest.json`` carrying ONE
    ``FROZEN_READY`` family/variant entry -- so a test can inject a matching
    ``frozen_ready_families`` resolver and prove the crash-resume path through the real sequence."""
    from app.research import foundry_freeze as fz

    research_dir = tmp_path / "fixture_research"
    research_dir.mkdir()
    for name in fz.FREEZE_SET_REQUIRED_MODULES:
        (research_dir / name).write_text(f"# fixture stub {name}\n", encoding="utf-8")
    freeze_set = fz.generate_freeze_set(research_dir)

    head = _git("rev-parse", "HEAD", cwd=REPO_ROOT)
    freeze_record = fz.build_freeze_record(
        freeze_commit=head, manifest_hash="fixture-manifest-hash",
        source_registry_hash="fixture-source-registry-hash", spec_hash="fixture-spec-hash",
        candidate_spec_schema_hash="fixture-schema-hash", compiler_hash="fixture-compiler-hash",
        interpreter_hash="fixture-interpreter-hash", runner_hash="fixture-runner-hash",
        scout_screen_source_hash="fixture-scout-screen-hash", config_fingerprint="fixture-config-fingerprint",
        freeze_set_hash=freeze_set["freeze_set_hash"],
        era_open_evidence_class_contract="historical_exposed_diagnostic",
    )

    tracked_dir = tmp_path / "tracked"
    tracked_dir.mkdir()
    (tracked_dir / "freeze-set.json").write_text(json.dumps(freeze_set), encoding="utf-8")
    (tracked_dir / "freeze-record.json").write_text(
        json.dumps(
            {
                "freeze_commit": freeze_record.freeze_commit, "manifest_hash": freeze_record.manifest_hash,
                "source_registry_hash": freeze_record.source_registry_hash, "spec_hash": freeze_record.spec_hash,
                "candidate_spec_schema_hash": freeze_record.candidate_spec_schema_hash,
                "compiler_hash": freeze_record.compiler_hash, "interpreter_hash": freeze_record.interpreter_hash,
                "runner_hash": freeze_record.runner_hash, "scout_screen_source_hash": freeze_record.scout_screen_source_hash,
                "config_fingerprint": freeze_record.config_fingerprint, "freeze_set_hash": freeze_record.freeze_set_hash,
                "era_open_evidence_class_contract": freeze_record.era_open_evidence_class_contract,
            }
        ),
        encoding="utf-8",
    )
    (tracked_dir / "epoch-manifest.json").write_text(
        json.dumps(
            {
                "epoch_id": "epoch:fixture-crash-resume",
                "families": [
                    {
                        "foundry_family_id": "family:fixture-crash-resume",
                        "variants": [{"variant_id": "family:fixture-crash-resume:0"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return tracked_dir


def _one_variant_resolver(manifest: dict):
    """A test-only ``frozen_ready_families`` resolver matching ``_build_fixture_tracked_dir``'s
    synthetic manifest: ONE family, ONE scalar candidate, synthetic anchors -- the same
    ``foundry_compiler``/``foundry_family``/``foundry_interpreter`` construction
    ``test_foundry_runner.py`` already proves, injected here so the crash-resume proof runs THROUGH
    ``run_real_exhaust``'s own freeze-verify -> lock -> corpus-hash -> epoch-open -> exhaust
    sequence rather than calling ``foundry_runner.run_one_candidate`` in isolation."""
    from app.research import foundry_compiler as fc
    from app.research import foundry_family as ffam
    from app.research import foundry_interpreter as fi

    family_id = "family:fixture-crash-resume"
    family = ffam.build_family_registry({family_id: [f"{family_id}:0"]})[family_id]
    coord = fc.CandidateCoordinate(
        feature_construct_id="q", semantic_role="candidate_signal", transform_orientation="ge",
        threshold_corner_predicate="q >= 1", threshold_provenance="natural_semantic_boundary",
        aggressor_derived=False, unit_basis="bool", anchor_at="anchor_at", available_at="anchor_at",
    )
    spec = fc.CandidateSpec(
        foundry_spec_version="v1", epoch_id="epoch:fixture-crash-resume", source_ids=("s0",),
        lineage_id="s0", foundry_family_id=family_id, variant_id=f"{family_id}:0", variant_ordinal=0,
        population=fc.CandidatePopulation(structure_context_kind="none", side_filter=None, setup_context_id=None),
        coordinates=(coord,), relation=fc.CandidateRelation(kind="direct_scalar_membership"),
        membership_corner="q >= 1", outcome=fc.CandidateOutcome(horizon_key="trades_20", sidedness="long"),
        economic_floor_rule=fc.EconomicFloorRule(), foundry_family_variant_count=1,
    ).with_hash()

    anchors = []
    for s in range(6):
        session = f"2026-08-{10 + s:02d}"
        for i in range(40):
            member = i < 20
            comp = fi.ComponentResolution("q", True, float(i), 1.0 if member else 0.0, member)
            outcome = 40.0 + (i % 5) * 0.01 if member else -0.01 * (i % 5)
            anchors.append(fi.PopulationAnchor(f"ds-{session}", "AAPL", session, i, "mid", None, outcome, "return_bps", (comp,)))

    return [(family, [(spec, anchors)])]


def test_j07_step7_fixture_backed_crash_resume_through_the_real_sequence(exhaust_mod, tmp_path):
    tracked_dir = _build_fixture_tracked_dir(tmp_path)
    foundry_dir = tmp_path / "foundry"
    lock_path = tmp_path / "exhaust.lock"

    # Simulate the crash: an intent row exists (as the real sequence would have written it), but
    # no terminal row yet -- written directly to the ledger BEFORE the CLI ever runs.
    from app.research import foundry_ledger as fl

    _, [(spec, _anchors)] = _one_variant_resolver({})[0]
    ledger = fl.FoundryLedger(foundry_dir)
    ledger.record_intent(
        candidate_spec_hash=spec.candidate_spec_hash, manifest_hash="fixture-manifest-hash",
        econ_floor_bps=exhaust_mod._UNUSED_PLACEHOLDER_ECON_FLOOR["floor_bps"],
        econ_floor_provenance=exhaust_mod._UNUSED_PLACEHOLDER_ECON_FLOOR["rule"],
    )
    assert ledger.terminal_row_for(spec.candidate_spec_hash) is None

    result = exhaust_mod.run_real_exhaust(
        tracked_dir=tracked_dir, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
        foundry_dir=str(foundry_dir), lock_path=lock_path, frozen_ready_families=_one_variant_resolver,
    )

    assert result["frozen_ready_total"] == 1
    assert result["terminal_count"] == 1
    assert result["exhaust_complete"] is True

    intent_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_INTENT]
    terminal_rows = [r for r in ledger.all_rows() if r["row_kind"] == fl.ROW_KIND_TERMINAL]
    assert len(intent_rows) == 1  # no duplicate intent row appended on resume
    assert len(terminal_rows) == 1
    assert terminal_rows[0]["candidate_spec_hash"] == spec.candidate_spec_hash


# === TC-4, literally: a real call counter over the sanctioned protected-read door ==================


def test_tc4_instrumented_micro_accessor_counter_records_zero_protected_reads(exhaust_mod, tmp_path, monkeypatch):
    """TC-4's literal wording ("given the sanctioned ``micro_accessor`` is instrumented with a call
    counter"). ``run_real_exhaust`` reports ``protected_read_count`` as a structural ``0`` -- true
    by construction today (nothing in its call path reaches ``MicroAccessor.read_snapshot_rows``,
    the ONE door to protected snapshot rows), and already guarded statically by the entrypoint-
    allowlist test in ``test_foundry_real_epoch_artifacts.py``. This test adds the RUNTIME half:
    a genuine counter wrapped around that door, so a future refactor that silently introduces a
    protected read fails here instead of quietly turning the reported ``0`` into a lie.

    Both flavors of run are instrumented under the SAME counter, deliberately: the real committed
    manifest's vacuous zero-variant pass, and the fixture-backed ONE-variant pass -- the latter is
    the only one that actually crosses ``run_family``/``run_one_candidate`` into the interpreter,
    i.e. the code path where such a read could plausibly appear later. Fully isolated: both use a
    ``tmp_path`` ledger/lock and the committed ``tests/fixtures/datasets`` corpus, never the real
    runtime Foundry directory."""
    _require_real_epoch_committed()
    from app.research import micro_accessor as ma

    calls: list[tuple] = []
    original = ma.MicroAccessor.read_snapshot_rows

    def _counting_read_snapshot_rows(self, dataset_id, *args, **kwargs):
        calls.append((dataset_id, args, kwargs))
        return original(self, dataset_id, *args, **kwargs)

    monkeypatch.setattr(ma.MicroAccessor, "read_snapshot_rows", _counting_read_snapshot_rows)

    real_result = exhaust_mod.run_real_exhaust(
        tracked_dir=FOUNDRY_DOCS_DIR, repo_root=REPO_ROOT, dataset_dir=str(FIXTURE_DATASET_DIR),
        foundry_dir=str(tmp_path / "real-foundry"), lock_path=tmp_path / "real-exhaust.lock",
    )
    assert real_result["protected_read_count"] == 0
    assert calls == [], f"the real-manifest exhaust pass read protected snapshot rows: {calls}"

    fixture_result = exhaust_mod.run_real_exhaust(
        tracked_dir=_build_fixture_tracked_dir(tmp_path), repo_root=REPO_ROOT,
        dataset_dir=str(FIXTURE_DATASET_DIR), foundry_dir=str(tmp_path / "fixture-foundry"),
        lock_path=tmp_path / "fixture-exhaust.lock", frozen_ready_families=_one_variant_resolver,
    )
    # The variant really was evaluated end-to-end (otherwise "zero reads" would be vacuous).
    assert fixture_result["terminal_count"] == 1
    assert fixture_result["protected_read_count"] == 0
    assert calls == [], f"the one-variant exhaust pass read protected snapshot rows: {calls}"
