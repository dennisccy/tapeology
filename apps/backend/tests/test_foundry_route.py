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


def test_foundry_route_is_get_only_no_mutation_endpoint_exists():
    """Product Shape / anti-goals: the Foundry surface is read-only this era -- there must be no
    ``POST``/``PUT``/``DELETE`` sibling under ``/research/desk/micro/foundry``."""
    paths = app.openapi()["paths"]
    assert "/research/desk/micro/foundry" in paths
    ops = paths["/research/desk/micro/foundry"]
    assert set(ops.keys()) == {"get"}
