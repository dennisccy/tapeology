"""``GET /research/profiles`` (Data Contract row 33, serving side — landed minimally at J-05).

Row 33 assigns the indicator-profile registry AND the champion pointer to this ONE endpoint —
the J-05 champion summary panel reads it verbatim (inferring the champion from ledger provenance
or hardcoding it in a page would be a second computation path). Until J-06 registers a candidate
and J-07 ships promotion mechanics, the served values are the config-owned initial state: exactly
one profile (the frozen ``default``) and the founding champion (strategy ``v1`` on ``default``).

Disciplines locked here:
  * The payload values ARE the existing single-copy constants (``STRATEGY_V1_ID`` in
    ``app/config.py``, ``PROFILE_DEFAULT`` in ``app/research/backtests.py``) — the serving module
    imports them and carries NO second copy of either id string (asserted over its source).
  * GET only — the registry is config-owned, so NO write surface exists: any non-GET verb is
    FastAPI's default 405 (no handler exists at all).

Uses a lifespan-less ``TestClient`` (the ``test_meta_routes.py`` precedent): the projection is
config-owned with no registry/engine/store dependency, so no injection is needed.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import STRATEGY_V1_ID
from app.main import app
from app.research.backtests import PROFILE_DEFAULT

client = TestClient(app)


def test_profiles_serves_the_frozen_default_and_the_founding_champion():
    """The exact config-owned initial state, pinned: one profile (``default``, frozen, the
    default) and the founding champion pointer (strategy ``v1`` on profile ``default``)."""
    response = client.get("/research/profiles")
    assert response.status_code == 200
    assert response.json() == {
        "profiles": [{"id": PROFILE_DEFAULT, "frozen": True, "is_default": True}],
        "champion": {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT},
    }


def test_profiles_registry_lists_exactly_one_profile_before_j06():
    """No candidate exists yet (J-06): the registry honestly lists ONE profile — never a
    placeholder candidate to make the list look populated."""
    payload = client.get("/research/profiles").json()
    assert len(payload["profiles"]) == 1
    assert payload["profiles"][0]["id"] == PROFILE_DEFAULT


def test_non_get_verbs_are_405_no_write_surface_exists():
    """The registry is config-owned: no POST/PUT/PATCH/DELETE handler exists on the path."""
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)("/research/profiles")
        assert response.status_code == 405, f"{method.upper()} must be Method Not Allowed"


def test_profiles_module_carries_no_second_copy_of_the_id_strings():
    """The serving module reuses the existing constants — a literal ``"default"`` or ``"v1"``
    in its source would be exactly the duplicated-id drift the single-source contract bans."""
    source = (
        Path(__file__).resolve().parents[1] / "app" / "research" / "profiles.py"
    ).read_text()
    for literal in ('"default"', "'default'", '"v1"', "'v1'"):
        assert literal not in source, f"duplicated id literal {literal} in app/research/profiles.py"
