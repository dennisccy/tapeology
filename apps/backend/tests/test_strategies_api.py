"""``GET /research/strategies`` (Data Contract row 40, serving side; era-4 capability 4, J-04).

Row 40 assigns the strategy registry AND the champion pointer to this ONE endpoint — mirroring
``test_profiles_api.py`` exactly (row 33's precedent, now applied to strategies): the registry is
config-owned (``v1`` plus the additive ``structure_tape``) and the champion pointer is read
VERBATIM from the ONE persisted source (``JournalStore.get_champion_pointer``) — the SAME single
pointer ``GET /research/profiles`` reads (one pointer, two read views, never a second source).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG, PROFILE_CANDIDATE_FASTER_WARMUP, PROFILE_DEFAULT, STRATEGY_TAPE_ID, STRATEGY_V1_ID
from app.main import app, manager
from app.research.routes import ResearchRegistry, set_registry
from app.research.store import JournalStore


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DATASET_DIR", str(tmp_path / "datasets"))
    monkeypatch.setenv("TAPEOLOGY_BAR_DIR", str(tmp_path / "bars"))
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


def test_strategies_lists_v1_and_structure_tape_in_registration_order(ctx):
    """The exact config-owned registry state, pinned: ``v1`` (frozen) plus the additive
    ``structure_tape`` — a registry, never a single hard-coded strategy."""
    client, _store = ctx
    response = client.get("/research/strategies")
    assert response.status_code == 200
    payload = response.json()
    assert [s["strategy_id"] for s in payload["strategies"]] == [STRATEGY_V1_ID, STRATEGY_TAPE_ID]
    assert payload["strategies"][0] == CONFIG.strategy_definition(STRATEGY_V1_ID)
    assert payload["strategies"][1] == CONFIG.strategy_definition(STRATEGY_TAPE_ID)


def test_strategies_serves_the_founding_champion(ctx):
    """A fresh store's champion pointer is the founding ``v1``/``default`` pair (seeded at
    store-open, never a hardcoded constant on THIS route)."""
    client, _store = ctx
    payload = client.get("/research/strategies").json()
    assert payload["champion"] == {"strategy_id": STRATEGY_V1_ID, "profile": PROFILE_DEFAULT}


def test_strategies_champion_reflects_a_moved_pointer_the_same_pointer_profiles_reads(ctx):
    """Moving the ONE persisted champion pointer is visible on THIS endpoint immediately (never
    cached/hardcoded), and is the identical value ``GET /research/profiles`` serves — one pointer,
    two read views, never a second champion source."""
    client, store = ctx
    store.set_champion_pointer(
        strategy_id=STRATEGY_V1_ID, profile=PROFILE_CANDIDATE_FASTER_WARMUP, wall_ts=1234.0
    )
    strategies_payload = client.get("/research/strategies").json()
    profiles_payload = client.get("/research/profiles").json()
    assert strategies_payload["champion"] == profiles_payload["champion"] == {
        "strategy_id": STRATEGY_V1_ID,
        "profile": PROFILE_CANDIDATE_FASTER_WARMUP,
    }
    # The registry list itself is unaffected by a champion move (config-owned, independent axis).
    assert [s["strategy_id"] for s in strategies_payload["strategies"]] == [
        STRATEGY_V1_ID,
        STRATEGY_TAPE_ID,
    ]


def test_non_get_verbs_are_405_no_write_surface_exists(ctx):
    client, _store = ctx
    for method in ("post", "put", "patch", "delete"):
        response = getattr(client, method)("/research/strategies")
        assert response.status_code == 405, f"{method.upper()} must be Method Not Allowed"


def test_strategies_module_carries_no_second_copy_of_the_id_strings():
    """The serving module reuses the existing constants — a literal id string in its source
    would be exactly the duplicated-id drift the single-source contract bans."""
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1] / "app" / "research" / "strategies.py"
    ).read_text()
    for literal in ('"v1"', "'v1'", f'"{STRATEGY_TAPE_ID}"', f"'{STRATEGY_TAPE_ID}'"):
        assert literal not in source, f"duplicated id literal {literal} in app/research/strategies.py"


def test_backtest_accepts_structure_tape_strategy_id(ctx):
    """``POST /research/backtests`` previously 422'd on any non-``v1`` strategy_id; registering
    ``structure_tape`` makes it accepted with NO route-validation change (Config.strategy_definition
    is the one registry both this route and GET /research/strategies consult)."""
    client, _store = ctx
    dataset = client.post(
        "/research/datasets",
        json={
            "source_kind": "reference",
            "split": "train",
            "start": "2026-06-09T17:00:00Z",
            "end": "2026-06-09T17:00:30Z",
        },
    ).json()["dataset"]
    r = client.post(
        "/research/backtests",
        json={"dataset_id": dataset["id"], "strategy_id": STRATEGY_TAPE_ID, "profile": PROFILE_DEFAULT},
    )
    assert r.status_code == 200, r.text
    created = r.json()["backtest"]
    assert created["strategy_id"] == STRATEGY_TAPE_ID

    import time

    deadline = time.time() + 30
    payload = None
    while time.time() < deadline:
        payload = client.get(f"/research/backtests/{created['id']}").json()["backtest"]
        if payload["status"] in ("done", "failed", "cancelled"):
            break
        time.sleep(0.05)
    assert payload["status"] == "done", payload.get("error")
    assert payload["result"]["strategy_id"] == STRATEGY_TAPE_ID
    # No classified levels were ever recorded for this symbol in this test -- an honest empty
    # trade list (zero fabricated arms), never a fallback to v1-like behaviour.
    assert payload["result"]["trades"] == []
    # era-4 J-05 (Data Contract row 42): the per-class breakdown is served on this SAME route --
    # no new endpoint -- honestly all-empty here (zero trades, so zero classified), never omitted.
    by_class = payload["result"]["aggregates_by_class"]
    assert set(by_class) == {"A", "B", "C"}
    for cls in ("A", "B", "C"):
        assert by_class[cls]["n"] == 0
        assert by_class[cls]["insufficient_sample"] is True


def test_unregistered_strategy_id_is_still_422_never_coerced(ctx):
    client, _store = ctx
    dataset = client.post(
        "/research/datasets",
        json={
            "source_kind": "reference",
            "split": "train",
            "start": "2026-06-09T17:00:00Z",
            "end": "2026-06-09T17:00:30Z",
        },
    ).json()["dataset"]
    r = client.post(
        "/research/backtests",
        json={"dataset_id": dataset["id"], "strategy_id": "v2", "profile": PROFILE_DEFAULT},
    )
    assert r.status_code == 422
    assert "v1" in r.json()["detail"] and STRATEGY_TAPE_ID in r.json()["detail"]
