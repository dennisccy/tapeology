"""``GET /research/desk/micro/foundry`` (goal-hypothesis-foundry-iter-1, J-01). TC-13/TC-14/TC-15
in ``docs/phases/goal-hypothesis-foundry-iter-1.md``: the era-open baseline is recorded once and
served byte-identically across calls; the route never 404s/500s before the operator recording act
has run.

goal-hypothesis-foundry-iter-5: ``source_registry_hash``/``source_registry_status`` are no longer
permanently hard-coded to ``null``/``not_yet_generated`` -- they now render the real committed
epoch's own values once J-06's generation command has run (see ``test_iter5_...`` below and
``test_foundry_route_hermetic_views.py``'s TC-18-style checks). The ``not_yet_generated`` DEGRADE
path (this file's original TC-15 claim) is still real and still tested, but against a synthetic
empty tracked directory via ``read_epoch_manifest_view``'s own override parameters, since the
module-level cached view now reflects whatever real files this repository actually has on disk."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.research import foundry_source_registry as fsr
from app.research import micro_routes


def _scope_dataset_dir(tmp_path, monkeypatch):
    dataset_dir = tmp_path / "datasets"
    dataset_dir.mkdir()
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(dataset_dir))
    monkeypatch.delenv("TAPEOLOGY_FOUNDRY_DIR", raising=False)
    return dataset_dir


def test_foundry_route_before_any_recording_serves_a_null_baseline_never_a_404(tmp_path, monkeypatch):
    _scope_dataset_dir(tmp_path, monkeypatch)
    with TestClient(app) as client:
        response = client.get("/research/desk/micro/foundry")
    assert response.status_code == 200
    body = response.json()
    assert body["era_open_baseline"] is None
    assert body["era"]["previous_era"] == "rapid-microscope"
    assert body["era"]["previous_era_status"] == "closed"
    assert body["era"]["current_era"] == "hypothesis-foundry"
    assert body["era"]["current_era_status"] == "active"
    assert body["era"]["foundry_spec_version"] == fsr.FOUNDRY_SPEC_VERSION


def test_iter5_epoch_manifest_degrades_honestly_to_not_yet_generated_when_tracked_files_are_absent(tmp_path):
    """The missing-artifact degrade path (this file's original TC-15 claim), exercised against a
    synthetic EMPTY tracked directory -- never a fabricated placeholder value -- via
    ``read_epoch_manifest_view``'s own override parameters, since the module-level cached view the
    live route serves now reflects whatever real committed files this repository actually has."""
    empty_dir = tmp_path / "hypothesis-foundry-empty"
    empty_dir.mkdir()
    view = micro_routes.read_epoch_manifest_view(tracked_dir=empty_dir, repo_root=tmp_path)
    assert view["status"] == "not_yet_generated"
    assert view["epoch_id"] is None
    assert view["source_registry_hash"] is None
    assert view["manifest_hash"] is None
    assert view["freeze_set_hash"] is None
    assert view["freeze_commit"] is None
    assert view["outcome_access_census"] == 0
    assert view["source_dispositions"] == []
    assert view["families"] == []
    assert view["source_registry_audit"]["committed"] is False


def test_iter5_status_is_generated_uncommitted_when_tracked_files_exist_but_are_not_committed(tmp_path):
    """Regression test for a real bug caught while building this route: `freeze_commit` is pinned
    to whatever `git rev-parse HEAD` already was BEFORE generation (this iteration's own
    freeze_commit-ordering rule), so a naive `verify_commit_is_ancestor(freeze_commit, head)`
    check is trivially True even while the four tracked JSON files still sit as UNCOMMITTED
    working-tree changes -- `status` must not report "committed" until the tracked artifacts
    THEMSELVES are actually present in a Git commit (TC-9's own "all five files... in one
    commit")."""
    import json
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    tracked_dir = repo / "docs" / "hypothesis-foundry"
    tracked_dir.mkdir(parents=True)
    (tracked_dir / "source-registry.json").write_text("{}", encoding="utf-8")
    (tracked_dir / "epoch-manifest.json").write_text(
        json.dumps(
            {
                "epoch_id": "epoch:test", "source_registry_hash": "h", "manifest_hash": "m",
                "config_fingerprint": "fp", "outcome_access_census": 0, "source_dispositions": [],
                "families": [],
            }
        ),
        encoding="utf-8",
    )
    (tracked_dir / "freeze-set.json").write_text("{}", encoding="utf-8")
    (tracked_dir / "freeze-record.json").write_text(
        json.dumps({"freeze_commit": head, "freeze_set_hash": "fsh"}), encoding="utf-8"
    )
    # Deliberately NOT `git add`/`git commit` -- this is exactly the scenario the bug produced a
    # false "committed" for, because `freeze_commit == head` is trivially an ancestor of itself.

    view = micro_routes.read_epoch_manifest_view(tracked_dir=tracked_dir, repo_root=repo)
    assert view["status"] == "generated_uncommitted"
    assert view["epoch_id"] == "epoch:test"  # the manifest IS read -- only `status` differs

    # now actually commit the four tracked files (still NOT the audit report) -- status must stay
    # "generated_uncommitted" until every one of the five tracked artifacts is committed.
    subprocess.run(["git", "add", "docs/hypothesis-foundry"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "partial"], cwd=repo, check=True)
    view_partial = micro_routes.read_epoch_manifest_view(tracked_dir=tracked_dir, repo_root=repo)
    assert view_partial["status"] == "generated_uncommitted"

    # commit the audit report too -- now all five are committed.
    audit_dir = repo / "reports" / "hypothesis-foundry"
    audit_dir.mkdir(parents=True)
    (audit_dir / "source-registry-audit.md").write_text("audit\n", encoding="utf-8")
    subprocess.run(["git", "add", "reports/hypothesis-foundry"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "audit"], cwd=repo, check=True)
    view_full = micro_routes.read_epoch_manifest_view(tracked_dir=tracked_dir, repo_root=repo)
    assert view_full["status"] == "committed"


def test_iter5_source_registry_hash_and_status_are_sourced_from_the_same_epoch_manifest_read(tmp_path, monkeypatch):
    """``get_foundry()``'s top-level ``source_registry_hash``/``source_registry_status`` are the
    SAME values ``epoch_manifest`` itself carries -- no second calculation path for the same
    value (single source of truth)."""
    _scope_dataset_dir(tmp_path, monkeypatch)
    with TestClient(app) as client:
        first = client.get("/research/desk/micro/foundry").json()
        second = client.get("/research/desk/micro/foundry").json()
    for body in (first, second):
        assert body["source_registry_hash"] == body["epoch_manifest"]["source_registry_hash"]
        assert body["source_registry_status"] == body["epoch_manifest"]["status"]
    assert first == second


def test_tc13_route_serves_the_recorded_baseline_byte_identically_across_two_calls(tmp_path, monkeypatch):
    dataset_dir = _scope_dataset_dir(tmp_path, monkeypatch)
    foundry_dir = fsr.resolve_foundry_dir(str(dataset_dir))
    research_dir = str((tmp_path.parent / "app_research_stub"))
    import pathlib

    research_path = pathlib.Path(research_dir)
    research_path.mkdir(parents=True, exist_ok=True)
    for name in fsr.REFEREE_MODULES:
        (research_path / name).write_text(f"# stub {name}\n", encoding="utf-8")

    fsr.record_era_open_baseline(
        foundry_dir,
        suite_passed=3762,
        suite_skipped=8,
        suite_failed=0,
        tsc_error_count=0,
        config_fingerprint=CONFIG.config_fingerprint(),
        research_dir=research_path,
    )

    with TestClient(app) as client:
        first = client.get("/research/desk/micro/foundry").json()
        second = client.get("/research/desk/micro/foundry").json()

    assert first == second
    assert first["era_open_baseline"]["backend_suite"] == {"passed": 3762, "skipped": 8, "failed": 0}
    assert first["era_open_baseline"]["config_fingerprint"] == CONFIG.config_fingerprint()
    assert set(first["era_open_baseline"]["referee_module_sha256"]) == set(fsr.REFEREE_MODULES)


# === goal-hypothesis-foundry-iter-6 (J-07/J-08): `exhaust_progress` -- genuinely runtime-scoped,
# read PER REQUEST (unlike `epoch_manifest`), degrading honestly before the operator's own
# exhaust-CLI act has ever run against this scoped `foundry_dir`. ==================================


def test_exhaust_progress_degrades_honestly_before_any_exhaust_cli_run(tmp_path, monkeypatch):
    _scope_dataset_dir(tmp_path, monkeypatch)
    with TestClient(app) as client:
        body = client.get("/research/desk/micro/foundry").json()
    progress = body["exhaust_progress"]
    assert progress["first_read_lock_recorded"] is False
    assert progress["first_read_lock_at"] is None
    assert progress["eligible_corpus_manifest_hash"] is None
    assert progress["terminal_count"] == 0
    assert progress["checkpoint_ordinal"] == 0
    assert progress["protected_read_count"] == 0
    assert progress["single_flight_status"] == "idle"
    assert progress["freeze_integrity_verdict"] == "not_yet_verified"
    assert progress["exhaust_complete"] is False


def test_exhaust_progress_reflects_a_real_epoch_open_row_once_one_exists(tmp_path, monkeypatch):
    """The scoped-runtime-storage discipline this iteration's own carried lesson names: writing
    directly to the SAME ``foundry_dir`` the route resolves (via ``foundry_ledger.FoundryLedger``,
    exactly what the real exhaust CLI does) must be visible on the very next GET -- no server
    restart, no caching, since this key is read PER REQUEST."""
    dataset_dir = _scope_dataset_dir(tmp_path, monkeypatch)
    foundry_dir = fsr.resolve_foundry_dir(str(dataset_dir))
    from app.research import foundry_ledger as fl

    ledger = fl.FoundryLedger(foundry_dir)
    ledger.record_epoch_open(
        epoch_id="epoch:test-exhaust-progress", freeze_commit="c" * 40,
        manifest_hash="mh", source_registry_hash="srh", spec_hash="sh",
        candidate_spec_schema_hash="csh", compiler_hash="ch", interpreter_hash="ih",
        runner_hash="rh", scout_screen_source_hash="ssh", config_fingerprint="fp",
        freeze_set_hash="fsh", era_open_evidence_class_contract="historical_exposed_diagnostic",
        eligible_corpus_manifest_hash="ecmh",
    )

    with TestClient(app) as client:
        body = client.get("/research/desk/micro/foundry").json()
    progress = body["exhaust_progress"]
    assert progress["first_read_lock_recorded"] is True
    assert progress["eligible_corpus_manifest_hash"] == "ecmh"
    assert progress["freeze_integrity_verdict"] == "green"
    assert progress["terminal_count"] == 0
    # the real committed manifest has zero FROZEN_READY variants -- an honest, vacuous completion.
    assert progress["frozen_ready_total"] == 0
    assert progress["exhaust_complete"] is True


def test_exhaust_progress_single_flight_status_reflects_a_live_held_lock(tmp_path, monkeypatch):
    dataset_dir = _scope_dataset_dir(tmp_path, monkeypatch)
    foundry_dir = fsr.resolve_foundry_dir(str(dataset_dir))
    from pathlib import Path

    from app.research import foundry_runner as fr

    lock_path = Path(foundry_dir) / fr.EXHAUST_LOCK_FILENAME
    with fr.SingleFlightLock(lock_path).acquire():
        with TestClient(app) as client:
            body = client.get("/research/desk/micro/foundry").json()
    assert body["exhaust_progress"]["single_flight_status"] == "running"


def test_foundry_route_is_get_only_no_mutation_endpoint_exists():
    """Product Shape / anti-goals: the Foundry surface is read-only this era -- there must be no
    ``POST``/``PUT``/``DELETE`` sibling under ``/research/desk/micro/foundry``."""
    paths = app.openapi()["paths"]
    assert "/research/desk/micro/foundry" in paths
    ops = paths["/research/desk/micro/foundry"]
    assert set(ops.keys()) == {"get"}


# === goal-hypothesis-foundry-iter-8 (J-08): the real §1.4 provenance enrichment on
# `epoch_manifest.source_dispositions[]`, the new `exhaust_progress.diagnostic_survivor_count`, and
# the new top-level `final_summary` projection. ====================================================


def test_iter8_source_dispositions_carry_full_registry_provenance_verbatim():
    """TC-2/TC-3: every `source_dispositions[]` entry now carries the full §1.4 canonical
    provenance -- this test independently re-reads the SAME tracked `source-registry.json` directly
    (never trusting the route's own enrichment to check itself) and asserts every enriched field
    agrees exactly with the real committed record, for every one of the real epoch's 11 sources."""
    import json

    repo_root = Path(__file__).resolve().parents[3]
    registry_path = repo_root / "docs" / "hypothesis-foundry" / "source-registry.json"
    if not registry_path.is_file():
        pytest.skip("the real Hypothesis Foundry source registry has not been generated in this checkout")
    registry_records_by_id = {
        record["source_id"]: record for record in json.loads(registry_path.read_text(encoding="utf-8"))["records"]
    }

    view = micro_routes.read_epoch_manifest_view()
    assert view["source_dispositions"], "the real committed epoch has no source_dispositions to check"
    for entry in view["source_dispositions"]:
        record = registry_records_by_id[entry["source_id"]]
        for field in micro_routes._SOURCE_REGISTRY_PROVENANCE_FIELDS:
            assert entry[field] == record[field], (
                f"{entry['source_id']}.{field} does not match the real committed source-registry "
                "record -- the route enriched it from something other than a verbatim read"
            )


def test_iter8_source_dispositions_provenance_degrades_honestly_without_a_matching_registry_record(tmp_path):
    """Error case: a manifest `source_dispositions[]` entry with no matching registry record
    (should never happen for the real, generated-together epoch) must not crash, and every
    provenance field renders an explicit honest-absence value -- never a fabricated placeholder."""
    import json

    tracked_dir = tmp_path / "hypothesis-foundry"
    tracked_dir.mkdir()
    (tracked_dir / "source-registry.json").write_text(json.dumps({"records": []}), encoding="utf-8")
    (tracked_dir / "epoch-manifest.json").write_text(
        json.dumps(
            {
                "epoch_id": "epoch:test", "source_registry_hash": "h", "manifest_hash": "m",
                "config_fingerprint": "fp", "outcome_access_census": 0,
                "source_dispositions": [
                    {
                        "source_id": "unmatched-source", "disposition": "BLOCKED_SPEC_GAP",
                        "lineage_refs": [], "alias_refs": [],
                    }
                ],
                "families": [],
            }
        ),
        encoding="utf-8",
    )
    (tracked_dir / "freeze-set.json").write_text("{}", encoding="utf-8")
    (tracked_dir / "freeze-record.json").write_text(
        json.dumps({"freeze_commit": None, "freeze_set_hash": "fsh"}), encoding="utf-8"
    )

    view = micro_routes.read_epoch_manifest_view(tracked_dir=tracked_dir, repo_root=tmp_path)
    entry = view["source_dispositions"][0]
    assert entry["source_id"] == "unmatched-source"
    assert entry["quoted_spans"] == []
    assert entry["source_hash"] is None
    assert entry["mechanism_statement"] is None
    assert entry["operative_formula_refs"] == []
    assert entry["direction_derivation"] is None
    assert entry["comparator_derivation"] is None
    assert entry["threshold_provenance"] is None
    assert entry["superseded_fields"] == {}
    assert entry["alternatives"] == []
    assert entry["audit_note"] is None
    assert entry["lineage_id"] is None


def test_iter8_exhaust_progress_diagnostic_survivor_count_is_zero_before_any_exhaust_cli_run(tmp_path, monkeypatch):
    _scope_dataset_dir(tmp_path, monkeypatch)
    with TestClient(app) as client:
        body = client.get("/research/desk/micro/foundry").json()
    assert body["exhaust_progress"]["diagnostic_survivor_count"] == 0


def test_iter8_exhaust_progress_diagnostic_survivor_count_is_a_genuine_filter_not_a_copy_of_terminal_count(
    tmp_path, monkeypatch
):
    """The new count must be a REAL filter over terminal rows whose `foundry_state` is the survivor
    state -- proven with a ledger carrying TWO terminal rows, only ONE of which survived, so
    `terminal_count` (2) and `diagnostic_survivor_count` (1) genuinely disagree. A count that were
    secretly a copy of `terminal_count` would report 2, not 1, here."""
    dataset_dir = _scope_dataset_dir(tmp_path, monkeypatch)
    foundry_dir = fsr.resolve_foundry_dir(str(dataset_dir))
    from app.research import foundry_ledger as fl

    ledger = fl.FoundryLedger(foundry_dir)
    ledger.record_epoch_open(
        epoch_id="epoch:test-survivor-count", freeze_commit="c" * 40,
        manifest_hash="mh", source_registry_hash="srh", spec_hash="sh",
        candidate_spec_schema_hash="csh", compiler_hash="ch", interpreter_hash="ih",
        runner_hash="rh", scout_screen_source_hash="ssh", config_fingerprint="fp",
        freeze_set_hash="fsh", era_open_evidence_class_contract="historical_exposed_diagnostic",
        eligible_corpus_manifest_hash="ecmh",
    )
    ledger.record_terminal(
        candidate_spec_hash="spec-killed", manifest_hash="mh", foundry_family_id="family:test",
        foundry_family_variant_count=2, screen_result={"decision": "killed_null"},
        rule_id="foundry:epoch:test-survivor-count:spec-killed",
        prospective_root_status="root_deferred_composite", foundry_state="EVALUATED_KILLED",
    )
    ledger.record_terminal(
        candidate_spec_hash="spec-survived", manifest_hash="mh", foundry_family_id="family:test",
        foundry_family_variant_count=2, screen_result={"decision": "survive"},
        rule_id="foundry:epoch:test-survivor-count:spec-survived",
        prospective_root_status="root_deferred_composite",
        foundry_state="DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN",
    )

    with TestClient(app) as client:
        body = client.get("/research/desk/micro/foundry").json()
    progress = body["exhaust_progress"]
    assert progress["terminal_count"] == 2
    assert progress["diagnostic_survivor_count"] == 1


def test_iter8_final_summary_matches_tc1_values_against_the_real_committed_epoch(tmp_path, monkeypatch):
    """TC-1: given the real committed Foundry epoch plus a freshly-recorded first-read-lock row
    (isolated storage -- never the shared real runtime ledger), `final_summary` carries exactly the
    values TC-1 specifies -- source counts summing to 11, zero families/variants/survivors, green
    freeze integrity, zero protected reads, and an honest vacuous exhaust completion."""
    dataset_dir = _scope_dataset_dir(tmp_path, monkeypatch)
    foundry_dir = fsr.resolve_foundry_dir(str(dataset_dir))
    from app.research import foundry_ledger as fl

    ledger = fl.FoundryLedger(foundry_dir)
    ledger.record_epoch_open(
        epoch_id="epoch:test-final-summary", freeze_commit="c" * 40,
        manifest_hash="mh", source_registry_hash="srh", spec_hash="sh",
        candidate_spec_schema_hash="csh", compiler_hash="ch", interpreter_hash="ih",
        runner_hash="rh", scout_screen_source_hash="ssh", config_fingerprint="fp",
        freeze_set_hash="fsh", era_open_evidence_class_contract="historical_exposed_diagnostic",
        eligible_corpus_manifest_hash="ecmh",
    )

    with TestClient(app) as client:
        body = client.get("/research/desk/micro/foundry").json()
    summary = body["final_summary"]
    assert sum(summary["source_counts_by_disposition"].values()) == 11
    assert summary["family_count"] == 0
    assert summary["variant_count"] == 0
    assert summary["frozen_ready_total"] == 0
    assert summary["diagnostic_survivor_count"] == 0
    assert summary["freeze_integrity_verdict"] == "green"
    assert summary["evidence_class"] == "historical_exposed_diagnostic"
    assert summary["protected_read_count"] == 0
    assert summary["exhaust_complete"] is True
    assert summary["epoch_status"] == "committed"
    # The real registry's own known disposition mix (verified directly against the committed
    # docs/hypothesis-foundry/source-registry.json).
    assert summary["source_counts_by_disposition"] == {
        "BLOCKED_DIRECTION": 4,
        "ALIASED_PROXY_ONLY": 2,
        "BLOCKED_SPEC_GAP": 1,
        "ALIASED_VARIANT_VOCABULARY": 1,
        "EXCLUDED_PREVIOUSLY_KILLED": 1,
        "EXCLUDED_PREREQUISITE_UNMET": 1,
        "EXCLUDED_GATE_CLOSED": 1,
    }


def test_iter8_final_summary_copies_frozen_ready_total_verbatim_never_resums_families():
    """`compute_foundry_final_summary` reads the caller-supplied `frozen_ready_total` for BOTH
    `.variant_count` and `.frozen_ready_total` rather than independently re-summing
    `families[].variant_count` -- proven by passing a `frozen_ready_total` that deliberately
    disagrees with what an independent re-sum of a (deliberately non-empty) `families` list would
    produce. If this helper ever drifted into a second counting site, this test would catch the
    disagreement immediately."""
    fake_view = {
        "status": "committed",
        "source_dispositions": [{"source_id": "a", "disposition": "COMPILED"}],
        "families": [{"foundry_family_id": "f1", "variant_count": 99}],
    }
    fake_exhaust_progress = {
        "diagnostic_survivor_count": 3, "freeze_integrity_verdict": "green",
        "protected_read_count": 0, "exhaust_complete": True,
    }
    summary = micro_routes.compute_foundry_final_summary(
        fake_view, frozen_ready_total=5, exhaust_progress=fake_exhaust_progress
    )
    assert summary["variant_count"] == 5
    assert summary["frozen_ready_total"] == 5
    assert summary["family_count"] == 1
    assert summary["source_counts_by_disposition"] == {"COMPILED": 1}
    # And the exhaust_progress-derived fields are copied verbatim, never recomputed here either.
    assert summary["diagnostic_survivor_count"] == 3
    assert summary["freeze_integrity_verdict"] == "green"
    assert summary["exhaust_complete"] is True


def test_iter8_final_summary_degrades_honestly_when_the_epoch_has_not_been_generated(tmp_path):
    """Error case: `final_summary` on a `not_yet_generated` epoch status must not fabricate any
    count -- every field reflects the honestly-empty manifest view it was built from."""
    empty_dir = tmp_path / "hypothesis-foundry-empty"
    empty_dir.mkdir()
    not_yet_generated_view = micro_routes.read_epoch_manifest_view(tracked_dir=empty_dir, repo_root=tmp_path)
    assert not_yet_generated_view["status"] == "not_yet_generated"
    fake_exhaust_progress = {
        "diagnostic_survivor_count": 0, "freeze_integrity_verdict": "not_yet_verified",
        "protected_read_count": 0, "exhaust_complete": False,
    }
    summary = micro_routes.compute_foundry_final_summary(
        not_yet_generated_view, frozen_ready_total=0, exhaust_progress=fake_exhaust_progress
    )
    assert summary["source_counts_by_disposition"] == {}
    assert summary["family_count"] == 0
    assert summary["variant_count"] == 0
    assert summary["frozen_ready_total"] == 0
    assert summary["diagnostic_survivor_count"] == 0
    assert summary["freeze_integrity_verdict"] == "not_yet_verified"
    assert summary["exhaust_complete"] is False
    assert summary["epoch_status"] == "not_yet_generated"
