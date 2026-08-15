"""``/research/desk/referee/*`` — Era 6 "The Referee": J-01's readiness fold plus (iter-5, J-04)
the matched-null compute-control surface. See ``referee_evidence.py``/``referee_null.py``'s own
module docstrings for the mechanics; this file is pure wiring.

A fresh router/file rather than folding into ``desk_routes.py`` (already 1600+ lines) — the SAME
rationale ``desk_routes.py`` itself gives for splitting off ``routes.py``: "mounted separately ...
rather than folding into routes.py, which is already large." The era's own Data Contract table
(``docs/goal.md``'s Product Shape) names five MORE referee routes landing in later iterations
(registry, evaluations, adjudications) under this SAME ``/research/desk/referee`` prefix — a
dedicated file is the right home from the start.

Depends on stores this route does NOT own: the playbook store dependency is imported verbatim from
``desk_routes.get_playbook_store``, the bar store dependency from ``routes.get_bar_store``, and the
dataset store dependency from ``routes.get_dataset_store`` (never a second, redefined provider for
any of them) — the ``JournalStore`` (for backtest reports) comes through the existing
``ResearchRegistry`` (``routes.get_registry``), the SAME seam ``GET /research/backtests`` already
reads. ``GET /evidence`` and ``GET /nulls*`` are plain reads: they trigger nothing, recompute
nothing (GET-never-computes, T-8) — only the two ``POST /nulls/compute*`` routes below start a
background walk, exactly like every other shipped desk compute-manager route."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..config import CONFIG
from .bars import BarStore
from .datasets import DatasetStore
from .desk_playbook import PlaybookStore
from .desk_routes import get_playbook_store
from .referee_evidence import referee_evidence
from .referee_null import (
    REFEREE_NULL_CONTEXT_SPEC_ID,
    REFEREE_NULL_TOD_SPEC_ID,
    RefereeNullComputeManager,
    RefereeNullRunStore,
    RefereeNullStore,
    resolve_referee_null_dir,
    resolve_referee_null_log_dir,
)
from .routes import ResearchRegistry, get_bar_store, get_dataset_store, get_registry

router = APIRouter(prefix="/research/desk/referee", tags=["referee"])

# Module-level singletons (the ``_desk_playbook_compute_manager`` pattern in ``desk_routes.py``) --
# process-scoped job state that must survive across requests within one running backend, never
# rebuilt per-request. Living here (not on ``ResearchRegistry``) matches ``referee_routes.py``'s
# own existing shape: this module owns its own wiring end to end.
_referee_null_compute_manager = RefereeNullComputeManager()


@router.get("/evidence")
def get_referee_evidence(
    playbook_store: PlaybookStore = Depends(get_playbook_store),
    dataset_store: DatasetStore = Depends(get_dataset_store),
    registry: ResearchRegistry = Depends(get_registry),
) -> dict:
    """J-01's readiness fold: exactly how much Playbook and strategy evidence already exists —
    per-``(setup, side)`` occurrence/session counts at the current detector basis, plus strategy
    dataset/split/trade counts and the honest tick-gate-unmet statement. Never 404/500 on an empty
    corpus — an honest all-zero shape at HTTP 200 (the desk router's established
    never-404-on-absence convention). Pure aggregation: this route neither detects nor measures
    anything — it only reads what ``desk_playbook.py``/``datasets.py``/``store.py`` already
    recorded."""
    return referee_evidence(
        playbook_store=playbook_store,
        dataset_store=dataset_store,
        journal_store=registry.store,
        config_fingerprint=CONFIG.config_fingerprint(),
    )


# === J-04: matched nulls -- store + compute-control + run-ledger routes ==============================


def get_referee_null_store() -> RefereeNullStore:
    """The durable null store rooted at a bare env-var-or-sibling-of-the-universe-dir default (zero
    new ``Config`` field — ``referee_null.resolve_referee_null_dir``) — the ``get_playbook_store``
    pattern. A FastAPI dependency so a test overrides it via the env var or outright."""
    return RefereeNullStore(resolve_referee_null_dir(CONFIG.desk_universe_dir_resolved()))


def get_referee_null_run_store() -> RefereeNullRunStore:
    """The durable null-run ledger, rooted the same way — the ``get_playbook_run_store`` pattern."""
    return RefereeNullRunStore(resolve_referee_null_log_dir(CONFIG.desk_universe_dir_resolved()))


def get_referee_null_compute_manager() -> RefereeNullComputeManager:
    """The single-flight-per-null-spec compute manager — a FastAPI dependency (the
    ``get_desk_playbook_compute_manager`` pattern) so a test overrides it outright via
    ``app.dependency_overrides`` for complete test-to-test isolation."""
    return _referee_null_compute_manager


@router.get("/nulls")
def get_referee_nulls(
    id: str | None = None, store: RefereeNullStore = Depends(get_referee_null_store)
) -> dict:
    """Recorded matched-null records, honest absence (T-8: GETs never compute). ``?id=`` scopes to
    ONE record (``{"record": <record>|None}``); otherwise every recorded record
    (``{"records": [...], "integrity_errors": [...]}``). Never 404/500 on an empty corpus (TC-17)."""
    if id is not None:
        return {"record": store.get(id)}
    records, errors = store.list()
    return {"records": records, "integrity_errors": errors}


class RefereeNullComputeRequest(BaseModel):
    """Body for ``POST /research/desk/referee/nulls/compute`` — ``null_spec_id`` is REQUIRED
    (FastAPI 422s a missing body before the route handler runs, the ``PlaybookComputeRequest``
    convention); never defaults to a particular variant."""

    null_spec_id: str


def _validate_null_spec_id(null_spec_id: str) -> None:
    if null_spec_id not in (REFEREE_NULL_TOD_SPEC_ID, REFEREE_NULL_CONTEXT_SPEC_ID):
        raise HTTPException(
            status_code=422,
            detail=(
                f"unknown null_spec_id {null_spec_id!r} -- expected one of "
                f"{sorted((REFEREE_NULL_TOD_SPEC_ID, REFEREE_NULL_CONTEXT_SPEC_ID))}"
            ),
        )


@router.post("/nulls/compute")
def trigger_referee_nulls_compute(
    body: RefereeNullComputeRequest,
    playbook_store: PlaybookStore = Depends(get_playbook_store),
    bar_store: BarStore = Depends(get_bar_store),
    null_store: RefereeNullStore = Depends(get_referee_null_store),
    run_store: RefereeNullRunStore = Depends(get_referee_null_run_store),
    manager: RefereeNullComputeManager = Depends(get_referee_null_compute_manager),
) -> dict:
    """Start (or, if one is already ``status`` in (``"running"``, ``"cancelling"``) for THIS
    ``null_spec_id``, return UNCHANGED — ``started: False``, single-flight PER null-spec, TC-19)
    the null-build job for ``body.null_spec_id``. Refuses — 422, naming the unknown id, never
    starting a job — on a malformed/unrecognised spec id."""
    _validate_null_spec_id(body.null_spec_id)
    return manager.trigger(
        body.null_spec_id, playbook_store, bar_store, CONFIG, null_store, run_store=run_store,
    )


@router.get("/nulls/compute")
def get_referee_nulls_compute(
    null_spec_id: str, manager: RefereeNullComputeManager = Depends(get_referee_null_compute_manager)
) -> dict:
    """The named null-spec's compute job current/last snapshot, served VERBATIM — ALWAYS a body
    (never ``null``: ``status == "idle"`` before any compute has ever run this process for this
    key). A plain read: never triggers a compute as a side effect (GET-never-computes)."""
    _validate_null_spec_id(null_spec_id)
    return manager.snapshot(null_spec_id)


class RefereeNullCancelRequest(BaseModel):
    null_spec_id: str


@router.post("/nulls/compute/cancel")
def cancel_referee_nulls_compute(
    body: RefereeNullCancelRequest,
    manager: RefereeNullComputeManager = Depends(get_referee_null_compute_manager),
) -> dict:
    """Cancel the in-flight null build for ``body.null_spec_id`` (cooperative — observed between
    observations). ``409`` when idle (no job has ever run for this key, or the last job already
    reached a terminal state) — mirrors ``cancel_desk_playbook_compute``'s own 409-when-terminal
    shape."""
    _validate_null_spec_id(body.null_spec_id)
    snapshot = manager.snapshot(body.null_spec_id)
    if snapshot["status"] != "running":
        raise HTTPException(
            status_code=409,
            detail=f"no referee null compute is currently running for {body.null_spec_id!r}",
        )
    manager.cancel(body.null_spec_id)
    return {"cancelling": True}


@router.get("/nulls/runs")
def get_referee_nulls_runs(
    null_spec_id: str | None = None, store: RefereeNullRunStore = Depends(get_referee_null_run_store)
) -> dict:
    """``{"runs": [...], "latest": <record>|null, "integrity_errors": [...]}`` — the durable
    terminal-state-only log of what every null build attempted (``GET /playbook/runs``'s own
    convention). ``?null_spec_id=`` narrows to one variant's own runs, and then ``latest`` is that
    variant's newest run rather than the store's."""
    records, errors = store.list()
    if null_spec_id is not None:
        records = [record for record in records if record.get("null_spec_id") == null_spec_id]
    return {
        "runs": records,
        "latest": records[-1] if records else None,
        "integrity_errors": errors,
    }
