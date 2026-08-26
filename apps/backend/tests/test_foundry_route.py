"""``GET /research/desk/micro/foundry`` (goal-hypothesis-foundry-iter-1, J-01). TC-13/TC-14/TC-15
in ``docs/phases/goal-hypothesis-foundry-iter-1.md``: the era-open baseline is recorded once and
served byte-identically across calls; ``source_registry_hash`` always renders ``null`` with an
explicit ``not_yet_generated`` status (the real registry does not exist until J-06); the route
never 404s/500s before the operator recording act has run."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app
from app.research import foundry_source_registry as fsr


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


def test_tc15_source_registry_hash_renders_null_not_yet_generated_on_two_calls(tmp_path, monkeypatch):
    _scope_dataset_dir(tmp_path, monkeypatch)
    with TestClient(app) as client:
        first = client.get("/research/desk/micro/foundry").json()
        second = client.get("/research/desk/micro/foundry").json()
    for body in (first, second):
        assert body["source_registry_hash"] is None
        assert body["source_registry_status"] == "not_yet_generated"


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
