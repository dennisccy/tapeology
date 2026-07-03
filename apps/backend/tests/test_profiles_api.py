"""``GET /research/profiles`` (Data Contract row 33, serving side).

Row 33 assigns the indicator-profile registry AND the champion pointer to this ONE endpoint —
the J-05 champion summary panel reads it verbatim (inferring the champion from ledger provenance
or hardcoding it in a page would be a second computation path). J-06 registers the FIRST
additive candidate beside the frozen ``default``; J-07 turns the champion pointer from a
hardcoded constant into the ONE persisted, movable source (``JournalStore.get_champion_pointer``)
— seeded to the founding strategy ``v1`` on ``default``, moved ONLY by a genuine hold-out
survivor (``app/research/pnl_scan.py``).

Disciplines locked here:
  * The registry payload IS the config-owned projection (``Config.profile_registry`` in
    ``app/config.py``) — the serving module carries NO second copy of any id string (asserted
    over its source).
  * GET only — any non-GET verb is FastAPI's default 405 (no handler exists at all).
  * ONE registry source: this projection and the backtest route's validation both consult
    ``Config.profile_definition`` — never a second allowlist (registry/resolution unit tests
    live in ``tests/test_profile_equivalence.py``).
  * ONE champion source: the served champion pointer reflects whatever
    ``JournalStore.get_champion_pointer`` reads — proven here by moving it directly through the
    store and re-reading it over THIS endpoint (never a second, route-local copy).

Uses the store-backed ``ctx`` fixture (the ``test_pnl_ledger_api.py`` precedent): the route now
depends on ``ResearchRegistry`` (J-07 — the champion pointer is store-owned, not config-only), so
a registry/store injection is required (the prior lifespan-less bare ``TestClient`` no longer
applies).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG, PROFILE_CANDIDATE_FASTER_WARMUP, PROFILE_DEFAULT, STRATEGY_V1_ID
from app.main import app, manager
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    with TestClient(app) as c:
        yield c, store
    registry.backtest_jobs.join_all(timeout=10.0)
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    set_registry(None)
    store.close()


def test_profiles_serves_the_frozen_default_and_the_registered_candidate(ctx):
    """The exact config-owned registry state, pinned: ``default`` (frozen) plus the ONE J-06
    candidate (additive, non-frozen, non-default, self-documenting its base + override) — and
    the founding champion pointer, seeded (no promotion has happened yet in a fresh store)."""
    client, _store = ctx
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


def test_profiles_registry_lists_default_and_exactly_one_candidate(ctx):
    """J-06 registers exactly the ONE candidate needed to prove the mechanism (registering more
    than needed is explicitly out of scope) — never a placeholder to make the list look
    populated."""
    client, _store = ctx
    payload = client.get("/research/profiles").json()
    assert [p["id"] for p in payload["profiles"]] == [
        PROFILE_DEFAULT,
        PROFILE_CANDIDATE_FASTER_WARMUP,
    ]


def test_non_get_verbs_are_405_no_write_surface_exists(ctx):
    client, _store = ctx
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)("/research/profiles")
        assert response.status_code == 405, f"{method.upper()} must be Method Not Allowed"


def test_profiles_module_carries_no_second_copy_of_the_id_strings():
    """The serving module reuses the existing constants — a literal id string in its source
    would be exactly the duplicated-id drift the single-source contract bans."""
    from pathlib import Path

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


def test_served_champion_reflects_a_moved_pointer(ctx):
    """J-07: the served champion is NOT a frozen constant — moving the ONE persisted pointer
    (exactly as a genuine promotion would) is visible on THIS endpoint immediately, proving
    ``GET /research/profiles`` reads the store verbatim rather than caching or hardcoding the
    founding pair."""
    client, store = ctx
    store.set_champion_pointer(
        strategy_id=STRATEGY_V1_ID, profile=PROFILE_CANDIDATE_FASTER_WARMUP, wall_ts=1234.0
    )
    payload = client.get("/research/profiles").json()
    assert payload["champion"] == {
        "strategy_id": STRATEGY_V1_ID,
        "profile": PROFILE_CANDIDATE_FASTER_WARMUP,
    }
    # The registry list itself is unaffected by a champion move (config-owned, independent axis).
    assert [p["id"] for p in payload["profiles"]] == [
        PROFILE_DEFAULT,
        PROFILE_CANDIDATE_FASTER_WARMUP,
    ]
