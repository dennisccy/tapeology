"""Execution checks computed ONCE at resolution + served by GET /research/journal/{id} (J-54/J-55).

End-to-end against the real engine (a watched SIM ticker) + a hermetic temp-path journal store:
declare a thesis, journal a real entry/exit mark, resolve it, and assert that:
  * the execution checks are computed ONCE at resolution and persisted (read the detail twice ->
    byte-identical execution_checks);
  * the additive keys (execution_checks, suggested_mistake_tags) are PRESENT post-resolution and
    ABSENT pre-resolution (honest omission);
  * the keys are served VERBATIM from the persisted record (a re-read never recomputes them);
  * an unknown id is 404; the timeline shape stays additive-only (the iter-12 keys are unchanged).

Each test injects a TEMP-PATH store + registry via the existing dependency-override pattern.
"""

import time

import pytest
from fastapi.testclient import TestClient

from app.config import CONFIG
from app.main import app, manager
from app.research.routes import ResearchRegistry, set_registry


@pytest.fixture
def client(tmp_path):
    from app.research.store import JournalStore

    store = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    registry = ResearchRegistry(store, CONFIG)
    set_registry(registry)
    manager.set_on_engine_created(registry.on_engine_created)
    with TestClient(app) as c:
        yield c, store
    for ticker in list(manager._engines.keys()):
        manager.stop(ticker)
    manager.set_on_engine_created(None)
    set_registry(None)
    store.close()


def _watch_until_state(client: TestClient, ticker: str, state: str, timeout: float = 12.0) -> float:
    r = client.post(f"/watch/{ticker}")
    assert r.status_code == 200
    deadline = time.time() + timeout
    while time.time() < deadline:
        summary = client.get(f"/tape/{ticker}/summary").json()
        last = summary.get("market", {}).get("last")
        if last is not None and summary.get("tape_state") == state:
            return last
        time.sleep(0.1)
    raise AssertionError(f"{ticker} did not warm to {state} in time")


def _declare(client: TestClient, ticker: str, last: float) -> str:
    r = client.post(
        "/research/thesis",
        json={
            "ticker": ticker,
            "setup_type": "trend_continuation",
            "direction": "long",
            "invalidation_price": round(last - 0.5, 2),
        },
    )
    assert r.status_code == 200, r.text
    return r.json()["thesis"]["id"]


def _mark(client: TestClient, tid: str, kind: str, price: float) -> None:
    r = client.post(f"/research/thesis/{tid}/action", json={"kind": kind, "price": price})
    assert r.status_code == 200, r.text


def _resolve(client: TestClient, tid: str, resolution: str = "played_out") -> None:
    r = client.post(f"/research/thesis/{tid}/resolve", json={"resolution": resolution})
    assert r.status_code == 200, r.text


# --- honest omission pre-resolution ---------------------------------------------------------------

def test_detail_omits_execution_checks_before_resolution(client):
    c, _store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    detail = c.get(f"/research/journal/{tid}").json()
    # Pre-resolution: the execution-checks keys are ABSENT (computed only at terminal resolution).
    assert "execution_checks" not in detail
    assert "suggested_mistake_tags" not in detail
    # The pre-existing detail shape is intact (additive-only).
    assert detail["thesis"]["id"] == tid
    assert detail["timeline"][0]["verdict"] == "pending"
    assert "marks" in detail


# --- computed once at resolution + served verbatim ------------------------------------------------

def test_execution_checks_present_after_resolution_and_byte_identical_on_reread(client):
    c, _store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    _mark(c, tid, "entry", round(last, 2))
    _resolve(c, tid)

    d1 = c.get(f"/research/journal/{tid}").json()
    assert "execution_checks" in d1
    assert "suggested_mistake_tags" in d1
    # All four named checks are present, each with an enum status + non-empty evidence (no score).
    by_name = {ch["check"] for ch in d1["execution_checks"]}
    assert by_name == {
        "entered_before_confirmation",
        "chased_entry",
        "exited_beyond_invalidation",
        "cut_confirming_early",
    }
    for ch in d1["execution_checks"]:
        assert ch["status"] in ("failed", "passed", "not_applicable")
        assert isinstance(ch["evidence"], str) and ch["evidence"]
        assert "score" not in ch
    # Computed ONCE + served verbatim: a second read is byte-identical (never recomputed at read).
    d2 = c.get(f"/research/journal/{tid}").json()
    assert d2["execution_checks"] == d1["execution_checks"]
    assert d2["suggested_mistake_tags"] == d1["suggested_mistake_tags"]


def test_exit_only_thesis_has_not_applicable_exit_checks(client):
    # A thesis with an entry but NO exit: the exit-dependent checks read not_applicable honestly.
    c, _store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    _mark(c, tid, "entry", round(last, 2))
    _resolve(c, tid)
    detail = c.get(f"/research/journal/{tid}").json()
    checks = {ch["check"]: ch for ch in detail["execution_checks"]}
    assert checks["exited_beyond_invalidation"]["status"] == "not_applicable"
    assert checks["cut_confirming_early"]["status"] == "not_applicable"


def test_no_marks_thesis_all_mark_checks_not_applicable_at_resolution(client):
    # Resolve WITHOUT any marks: every mark-dependent check reads not_applicable (never fabricated).
    c, _store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    _resolve(c, tid)
    detail = c.get(f"/research/journal/{tid}").json()
    checks = {ch["check"]: ch for ch in detail["execution_checks"]}
    for name in (
        "entered_before_confirmation",
        "chased_entry",
        "exited_beyond_invalidation",
        "cut_confirming_early",
    ):
        assert checks[name]["status"] == "not_applicable", name
    assert detail["suggested_mistake_tags"] == []


def test_unknown_id_is_404(client):
    c, _store = client
    assert c.get("/research/journal/does-not-exist").status_code == 404


def test_timeline_rows_are_additive_only_shape(client):
    # The execution-checks addition must not change the existing timeline row keys (additive-only).
    c, _store = client
    last = _watch_until_state(c, "SIM-BUYER", "buyer_control")
    tid = _declare(c, "SIM-BUYER", last)
    _resolve(c, tid)
    detail = c.get(f"/research/journal/{tid}").json()
    for row in detail["timeline"]:
        assert set(row.keys()) == {
            "logical_ts",
            "wall_ts",
            "verdict",
            "evidence",
            "tape_state",
            "confidence",
            "last",
            "rule_first_true_ts",
            "rule_first_true_price",
        }
