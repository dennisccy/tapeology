"""``GET /research/profiles`` (Data Contract row 33, serving side).

Row 33 assigns the indicator-profile registry AND the champion pointer to this ONE endpoint —
the J-05 champion summary panel reads it verbatim (inferring the champion from ledger provenance
or hardcoding it in a page would be a second computation path). J-06 registers the FIRST
additive candidate beside the frozen ``default``; the served champion pointer is unmoved (still
the founding strategy ``v1`` on ``default`` — no promotion exists yet, only a hold-out survivor
may ever move it, J-07).

Disciplines locked here:
  * The payload values ARE the existing single-copy constants + the config-owned registry
    (``STRATEGY_V1_ID`` / ``PROFILE_DEFAULT`` / ``PROFILE_CANDIDATE_FASTER_WARMUP`` in
    ``app/config.py``, projected through ``Config.profile_registry``) — the serving module
    imports them and carries NO second copy of any id string (asserted over its source).
  * GET only — the registry is config-owned, so NO write surface exists: any non-GET verb is
    FastAPI's default 405 (no handler exists at all).
  * ONE registry source: this projection and the backtest route's validation both consult
    ``Config.profile_definition`` — never a second allowlist (registry/resolution unit tests
    live in ``tests/test_profile_equivalence.py``).

Uses a lifespan-less ``TestClient`` (the ``test_meta_routes.py`` precedent): the projection is
config-owned with no registry/engine/store dependency, so no injection is needed.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import PROFILE_CANDIDATE_FASTER_WARMUP, PROFILE_DEFAULT, STRATEGY_V1_ID
from app.main import app

client = TestClient(app)


def test_profiles_serves_the_frozen_default_and_the_registered_candidate():
    """The exact config-owned registry state, pinned: ``default`` (frozen) plus the ONE J-06
    candidate (additive, non-frozen, non-default, self-documenting its base + override) — and
    the founding champion pointer, unmoved (no promotion exists yet)."""
    response = client.get("/research/profiles")
    assert response.status_code == 200
    payload = response.json()
    assert payload["champion"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}
    assert payload["profiles"][0] == {"id": PROFILE_DEFAULT, "frozen": True, "is_default": True}
    candidate = payload["profiles"][1]
    assert candidate["id"] == PROFILE_CANDIDATE_FASTER_WARMUP
    assert candidate["frozen"] is False
    assert candidate["is_default"] is False
    assert candidate["based_on"] == PROFILE_DEFAULT
    assert "overrides" in candidate and candidate["overrides"]


def test_profiles_registry_lists_default_and_exactly_one_candidate():
    """J-06 registers exactly the ONE candidate needed to prove the mechanism (registering more
    than needed is explicitly out of scope) — never a placeholder to make the list look
    populated."""
    payload = client.get("/research/profiles").json()
    assert [p["id"] for p in payload["profiles"]] == [
        PROFILE_DEFAULT,
        PROFILE_CANDIDATE_FASTER_WARMUP,
    ]


def test_non_get_verbs_are_405_no_write_surface_exists():
    """The registry is config-owned: no POST/PUT/PATCH/DELETE handler exists on the path."""
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)("/research/profiles")
        assert response.status_code == 405, f"{method.upper()} must be Method Not Allowed"


def test_profiles_module_carries_no_second_copy_of_the_id_strings():
    """The serving module reuses the existing constants — a literal id string in its source
    would be exactly the duplicated-id drift the single-source contract bans."""
    source = (
        Path(__file__).resolve().parents[1] / "app" / "research" / "profiles.py"
    ).read_text()
    for literal in (
        '"default"',
        "'default'",
        '"v1"',
        "'v1'",
        f'"{PROFILE_CANDIDATE_FASTER_WARMUP}"',
        f"'{PROFILE_CANDIDATE_FASTER_WARMUP}'",
    ):
        assert literal not in source, f"duplicated id literal {literal} in app/research/profiles.py"
