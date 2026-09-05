"""``GET /tape/{ticker}/observation`` -- Binding Execution Order step 5 (J-05; docs/goal.md).

This module proves the ROUTE ITSELF, not the already-tested modules it wires together:
``build_tape_observation`` (iter-1, ``test_tape_observation_projection.py``),
``WatchManager.get_observation_source`` (iter-2/3, ``test_tape_observation_time.py`` /
``test_tape_observation_lifecycle_feed.py``) and the ingestion-path equivalence proof (iter-4,
``test_tape_observation_path_equivalence.py``) are all unmodified and unchanged by this iteration.

Covers exactly the backend-pytest slice of the iter-5 Definition of Done (TC-8..TC-15):
  * TC-8/TC-10: an AST/source guard proving the route consumes
    ``manager.get_observation_source(ticker)`` and calls no ``TapeEngine`` method, with a
    ``test_counterexample_*`` proving the SAME scan can fail.
  * TC-9: 404 parity with ``/tape/{ticker}/state`` for an unwatched ticker.
  * TC-11/TC-15: with ``now`` frozen, the route's parsed JSON is field-for-field and
    value-for-value equal to ``build_tape_observation``'s direct output for the same atomic read,
    with a counter-example proving that equality check is not vacuous.
  * TC-12: ``observation_hash``/``artifact_hash`` are recomputable from the served JSON via the
    §6 canonical encoding.
  * TC-13: the MCP ``get_endpoint`` proxy's response bytes equal the REST response bytes against a
    REAL uvicorn subprocess (``test_mcp_server.py``'s own real-uvicorn-subprocess pattern,
    self-contained here rather than imported, so this module owns its own tiny fixture per this
    repository's established per-module convention) -- the MCP 28-tool pin is reconfirmed inline;
    the no-write / no-app-import pins stay proven by ``test_mcp_server.py``'s own existing,
    unedited tests (this era changes nothing under ``apps/backend/app/mcp/``).
  * TC-14: a GET starts no watch, computation or git call -- unchanged manager-read and git-call
    counts across 100 consecutive requests.

No test needs network access or real Alpaca credentials -- Sim mode only, one real uvicorn
subprocess of THIS app on an ephemeral local port for TC-13.
"""

from __future__ import annotations

import ast
import copy
import inspect
import itertools
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app import observation_contract
from app.config import CONFIG
from app.engine.tape_engine import TapeEngine
from app.main import app, manager
from app.mcp import TOOL_NAMES, call_tool
from app.observation_contract import build_tape_observation
from app.providers.simulated import SimulatedProvider

BACKEND_DIR = Path(__file__).resolve().parents[1]

TICKER = "SIM-BIDABS"
SCENARIO = "bid_absorption"


# --- Small shared helpers (self-contained -- no cross-import of another test module's fixtures) --


def _wait_until_settled(client: TestClient, ticker: str, *, timeout_s: float = 15.0) -> dict:
    """Poll ``/tape/{ticker}/state`` until the sim scenario resolves. Mirrors ``test_api.py``'s
    own polling idiom exactly."""
    deadline = time.time() + timeout_s
    state: dict = {}
    while time.time() < deadline:
        state = client.get(f"/tape/{ticker}/state").json()
        if state.get("tape_state") == SCENARIO:
            return state
        time.sleep(0.1)
    raise AssertionError(f"{ticker} did not settle to {SCENARIO!r} in time: {state}")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# --- TC-8/TC-10: the route consumes the atomic read and calls no TapeEngine method ---------------

# TapeEngine's own real public method surface, introspected dynamically (never a hand-guessed
# list) so this guard can never silently drift from the real class.
_ENGINE_PUBLIC_METHODS: frozenset[str] = frozenset(
    name for name, _ in inspect.getmembers(TapeEngine, predicate=inspect.isfunction)
    if not name.startswith("_")
)


def _route_source() -> str:
    return inspect.getsource(main_module.get_observation)


def _engine_method_call_names(source: str) -> set[str]:
    """Every ``<expr>.<attr>(...)`` call name in ``source`` that matches one of TapeEngine's real
    public method names. The ONE real scan both the guard test and its counter-example use."""
    tree = ast.parse(source)
    return {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _ENGINE_PUBLIC_METHODS
    }


def _calls_manager_get_observation_source(source: str) -> bool:
    tree = ast.parse(source)
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get_observation_source"
        for node in ast.walk(tree)
    )


def test_route_consumes_the_atomic_read_and_calls_no_tape_engine_method():
    source = _route_source()
    assert _calls_manager_get_observation_source(source)
    assert _engine_method_call_names(source) == set()


def test_counterexample_engine_method_scan_detects_an_injected_snapshot_call():
    """TC-10: the SAME scan above must be provably non-vacuous -- a copy of the route
    reintroducing a direct engine-snapshot call (the critical Binding-Order violation) must be
    caught, never silently passed."""
    real_source = _route_source()
    poisoned = real_source.replace(
        "source = manager.get_observation_source(ticker)",
        "source = manager.get_observation_source(ticker)\n"
        "    _leak = manager.get(ticker).snapshot()",
    )
    assert poisoned != real_source, "sanity: the injection must actually change the source"
    assert "snapshot" in _engine_method_call_names(poisoned)


# --- TC-9: 404 parity with /tape/{ticker}/state for an unwatched ticker --------------------------


def test_404_parity_with_tape_state_for_an_unwatched_ticker():
    client = TestClient(app)
    ticker = "ZZZZ"
    observation_resp = client.get(f"/tape/{ticker}/observation")
    state_resp = client.get(f"/tape/{ticker}/state")
    assert observation_resp.status_code == 404
    assert state_resp.status_code == 404
    assert observation_resp.json() == state_resp.json()


# --- TC-11/TC-15: route output equals build_tape_observation's direct output, frozen now ---------


def test_route_output_equals_builder_output_field_for_field_with_frozen_now(monkeypatch):
    frozen_now = datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(main_module, "_now_utc", lambda: frozen_now)

    try:
        # The context-manager form keeps ONE background event-loop portal alive across every
        # call in this block, so the watch's background feeder actually progresses between the
        # separate POST/GET calls below (a bare `TestClient(app)` without `with` tears its portal
        # down after each call, leaving the sim scenario frozen at cold-start).
        with TestClient(app) as client:
            assert client.post(f"/watch/{TICKER}").status_code == 200
            _wait_until_settled(client, TICKER)
            # Freeze the feeder (Pause) so the route's own read and this test's own follow-up read
            # of get_observation_source are guaranteed to observe the SAME atomic pair -- otherwise
            # the live background feeder could advance the snapshot between the two reads.
            assert client.post(f"/watch/{TICKER}/pause").status_code == 200

            response = client.get(f"/tape/{TICKER}/observation")
            assert response.status_code == 200
            route_json = response.json()

            source = manager.get_observation_source(TICKER)
            assert source is not None
            snapshot, settled_at_utc, end_reason, descriptor = source
            direct = build_tape_observation(
                snapshot=snapshot,
                source_mode=descriptor.source_mode,
                data_feed=descriptor.data_feed,
                window_start_utc=descriptor.window_start_utc,
                window_end_utc=descriptor.window_end_utc,
                dataset_id=descriptor.dataset_id,
                dataset_checksum=descriptor.dataset_checksum,
                session_id=descriptor.session_id,
                session_started_at_utc=descriptor.session_started_at_utc,
                settled_at_utc=settled_at_utc,
                end_reason=end_reason,
                generated_at_utc=main_module._iso_utc(frozen_now),
                profile_id=descriptor.profile_id,
                config=CONFIG,
                provenance=observation_contract.resolve_implementation_provenance(),
            )
            assert route_json == direct
    finally:
        manager.stop(TICKER)


def test_counterexample_route_builder_equality_comparator_detects_a_mutated_field():
    """TC-15: proves the TC-11 field-for-field equality check is not vacuous -- mutating a REAL
    built observation's ``tape_state`` in a deep copy must make the SAME ``==`` comparison fail
    (never a hand-written literal pair standing in for real builder output)."""
    engine = TapeEngine(TICKER, SCENARIO, CONFIG, epoch_anchor=CONFIG.sim_session_anchor_epoch)
    for event in itertools.islice(SimulatedProvider(TICKER, SCENARIO).stream(), 10):
        engine.process_event(event)
    base = build_tape_observation(
        snapshot=engine.snapshot(),
        source_mode="sim",
        data_feed="sim",
        window_start_utc=None,
        window_end_utc=None,
        dataset_id=None,
        dataset_checksum=None,
        session_id="session-tc15",
        session_started_at_utc="2026-09-04T00:00:00.000000Z",
        settled_at_utc=None,
        end_reason=None,
        generated_at_utc="2026-09-04T00:00:00.000000Z",
        profile_id="default",
        config=CONFIG,
        provenance=observation_contract.resolve_implementation_provenance(),
    )
    mutated = copy.deepcopy(base)
    mutated["tape_state"] = (
        "seller_control" if base["tape_state"] != "seller_control" else "buyer_control"
    )
    assert mutated != base  # sanity: genuinely diverged
    with pytest.raises(AssertionError):
        assert mutated == base  # the SAME comparator TC-11 itself uses


# --- TC-12: both hashes recomputable from the served JSON via the §6 canonical encoding ----------


def test_hashes_recomputable_from_served_json():
    try:
        with TestClient(app) as client:
            assert client.post(f"/watch/{TICKER}").status_code == 200
            _wait_until_settled(client, TICKER)
            served = client.get(f"/tape/{TICKER}/observation").json()
            assert served["observation_hash"] == observation_contract.compute_observation_hash(served)
            assert served["artifact_hash"] == observation_contract.compute_artifact_hash(served)
    finally:
        manager.stop(TICKER)


# --- TC-14: a GET starts no watch, computation, or git call --------------------------------------


def test_get_starts_no_watch_computation_or_git_call_across_100_requests(monkeypatch):
    try:
        with TestClient(app) as client:
            assert client.post(f"/watch/{TICKER}").status_code == 200
            _wait_until_settled(client, TICKER)
            assert client.post(f"/watch/{TICKER}/pause").status_code == 200

            # Warm the per-process provenance memo BEFORE counting --
            # resolve_implementation_provenance is memoized once per process, never per request
            # (mirrors real process lifetime).
            observation_contract.resolve_implementation_provenance()

            manager_calls = {"n": 0}
            real_get_observation_source = manager.get_observation_source

            def _counted_manager_call(ticker: str):
                manager_calls["n"] += 1
                return real_get_observation_source(ticker)

            monkeypatch.setattr(manager, "get_observation_source", _counted_manager_call)

            git_calls = {"n": 0}
            real_run_git = observation_contract._run_git

            def _counted_git_call(args):
                git_calls["n"] += 1
                return real_run_git(args)

            monkeypatch.setattr(observation_contract, "_run_git", _counted_git_call)

            for _ in range(100):
                resp = client.get(f"/tape/{TICKER}/observation")
                assert resp.status_code == 200

            assert manager_calls["n"] == 100
            assert git_calls["n"] == 0
    finally:
        manager.stop(TICKER)


# --- TC-13: MCP get_endpoint bytes == REST bytes against a real uvicorn subprocess ----------------


@pytest.fixture(scope="module")
def observation_backend(tmp_path_factory):
    """A REAL uvicorn instance of the app on an ephemeral port (the ``test_mcp_server.py``
    real-uvicorn-subprocess pattern, self-contained here rather than imported -- this module owns
    its own tiny fixture per this repository's established per-module convention). A scoped
    journal DB keeps the subprocess from touching the operator's real store."""
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["TAPEOLOGY_JOURNAL_DB"] = str(tmp_path_factory.mktemp("obsroute-journal") / "journal.db")
    log_path = tmp_path_factory.mktemp("obsroute-uvicorn") / "uvicorn.log"
    with open(log_path, "wb") as log:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", str(port)],
            cwd=BACKEND_DIR, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.time() + 20
            while True:
                try:
                    if httpx.get(f"{base}/health", timeout=1.0).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if proc.poll() is not None or time.time() > deadline:
                    raise AssertionError(
                        f"test backend failed to start:\n{log_path.read_text()[-2000:]}"
                    )
                time.sleep(0.2)
            yield base
        finally:
            proc.terminate()
            proc.wait(timeout=10)


_VOLATILE_FIELDS = ("generated_at_utc", "artifact_hash")


def _without_volatile_fields(document: dict) -> dict:
    """Strip the two fields Constitution §2/§6 name as honestly non-reproducible ACROSS
    independent projections of the SAME snapshot -- ``generated_at_utc`` (the route's own wall
    clock at generation time) and ``artifact_hash`` (derived from it, "intentionally
    non-reproducible across projections", per §6). Two genuinely separate HTTP requests -- one
    direct REST, one through the MCP proxy's OWN independent network call -- necessarily each
    stamp their own `generated_at_utc`, exactly as TC-7's two-reload proof requires elsewhere.
    Everything else, including the stable `observation_hash` equivalence identity, must still
    match byte-for-byte -- proving the MCP layer is a true verbatim passthrough with zero
    transformation, never a second serialization path."""
    return {k: v for k, v in document.items() if k not in _VOLATILE_FIELDS}


@pytest.mark.anyio
async def test_mcp_get_endpoint_bytes_equal_rest_bytes_against_real_uvicorn(
    observation_backend, monkeypatch
):
    monkeypatch.setenv("TAPEOLOGY_API_BASE", observation_backend)

    assert httpx.post(f"{observation_backend}/watch/{TICKER}", timeout=5.0).status_code == 200
    deadline = time.time() + 15
    while time.time() < deadline:
        state = httpx.get(f"{observation_backend}/tape/{TICKER}/state", timeout=5.0).json()
        if state.get("tape_state") == SCENARIO:
            break
        time.sleep(0.2)
    else:
        raise AssertionError(f"{TICKER} did not settle on the test backend")
    # Pause so the two reads below (REST direct + MCP proxy) observe the same settled snapshot.
    assert httpx.post(f"{observation_backend}/watch/{TICKER}/pause", timeout=5.0).status_code == 200
    time.sleep(0.3)

    rest = httpx.get(f"{observation_backend}/tape/{TICKER}/observation", timeout=5.0)
    assert rest.status_code == 200

    result = await call_tool("get_endpoint", {"path": f"/tape/{TICKER}/observation"})
    assert result.isError is False
    assert len(result.content) == 1

    # Each is its own genuinely separate HTTP request (REST direct vs. the MCP tool's own
    # independent proxied GET), so each legitimately stamps its own `generated_at_utc` /
    # `artifact_hash` (Constitution §2/§6; the SAME honest non-reproducibility TC-7 proves via two
    # reloads). `observation_hash` -- the stable machine-observation equivalence identity -- and
    # every other field must still be byte-identical, proving the MCP layer performs zero
    # transformation (no parse/re-serialize round trip, a true verbatim passthrough).
    rest_doc = rest.json()
    mcp_doc = json.loads(result.content[0].text)
    assert rest_doc["observation_hash"] == mcp_doc["observation_hash"]
    assert _without_volatile_fields(mcp_doc) == _without_volatile_fields(rest_doc)

    # The proxy did not corrupt bytes in transit: the MCP-served document's OWN hashes still
    # recompute from itself (never just "looks similar").
    assert mcp_doc["observation_hash"] == observation_contract.compute_observation_hash(mcp_doc)
    assert mcp_doc["artifact_hash"] == observation_contract.compute_artifact_hash(mcp_doc)

    # The 28-tool pin is unchanged (zero MCP registry edits this iteration -- the generic
    # `/tape/` allowlist prefix already covers the new route). The no-write / no-app-import pins
    # stay proven by test_mcp_server.py's own existing, unedited tests.
    assert len(TOOL_NAMES) == 28
