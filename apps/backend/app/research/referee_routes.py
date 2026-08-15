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

from typing import Optional

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
from .referee_registry import (
    CertificateStore,
    ConfirmationRequired,
    FamilyAlreadyRecorded,
    FamilyStore,
    HypothesisAlreadyRecorded,
    HypothesisMalformed,
    HypothesisStore,
    RetroactiveBoundary,
    UnknownSpecId,
    WithdrawalStore,
    register_hypothesis,
    registry_response,
    resolve_referee_registry_dir,
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


# === J-05: the registry -- family/hypothesis/withdrawal/certificate stores + routes ===================
#
# See ``referee_registry.py``'s own module docstring for the mechanics (family+hypothesis
# registered together through ONE act; withdrawal and certificate seeding stay library/CLI-only
# this iteration -- the Data Contract names exactly one POST route). GET never computes (T-8):
# the accrual fold below is a pure read over already-recorded stores.


def get_referee_family_store() -> FamilyStore:
    """The durable family store, rooted at the SAME resolved registry directory as the other
    three registry stores (zero new ``Config`` field — ``referee_registry.resolve_referee_
    registry_dir``) — a FastAPI dependency so a test overrides it via the env var or outright."""
    return FamilyStore(resolve_referee_registry_dir(CONFIG.desk_universe_dir_resolved()))


def get_referee_hypothesis_store() -> HypothesisStore:
    return HypothesisStore(resolve_referee_registry_dir(CONFIG.desk_universe_dir_resolved()))


def get_referee_withdrawal_store() -> WithdrawalStore:
    return WithdrawalStore(resolve_referee_registry_dir(CONFIG.desk_universe_dir_resolved()))


def get_referee_certificate_store() -> CertificateStore:
    return CertificateStore(resolve_referee_registry_dir(CONFIG.desk_universe_dir_resolved()))


@router.get("/registry")
def get_referee_registry(
    family_store: FamilyStore = Depends(get_referee_family_store),
    hypothesis_store: HypothesisStore = Depends(get_referee_hypothesis_store),
    withdrawal_store: WithdrawalStore = Depends(get_referee_withdrawal_store),
    certificate_store: CertificateStore = Depends(get_referee_certificate_store),
    playbook_store: PlaybookStore = Depends(get_playbook_store),
) -> dict:
    """The pinned four-key registry fold (``families``/``hypotheses``/``withdrawals``/
    ``certificates``) — every hypothesis served with its read-side ``status``/``accrual``
    additions, never persisted on the record itself. Never 404/500 on an empty registry."""
    return registry_response(
        family_store=family_store,
        hypothesis_store=hypothesis_store,
        withdrawal_store=withdrawal_store,
        certificate_store=certificate_store,
        playbook_store=playbook_store,
        config_fingerprint=CONFIG.config_fingerprint(),
    )


class RefereeHypothesisRegistrationRequest(BaseModel):
    """Body for ``POST /research/desk/referee/registry/hypotheses`` — every field optional at the
    pydantic level (``register_hypothesis`` itself is the ONE place that validates presence/
    vocabulary/floors, so CLI, POST, and tests all refuse through the identical distinct-error
    paths rather than FastAPI's own built-in 422 shape for some fields and a custom one for
    others). ``confirm`` must be explicitly ``True`` before any write (the desk pattern's
    "explicit confirmation required" made a literal field).

    **``registered_at`` is deliberately NOT a field here** (iter-6 audit, finding B1): the
    boundary is DERIVED from the registration instant (spec Sec5), so a caller-supplied instant
    would be a caller-chosen ``confirmation_start_boundary`` — the exact thing
    ``RetroactiveBoundary`` refuses on the sibling ``confirmation_start_boundary`` field, and a
    direct breach of the era's "the historical atlas is exploratory forever" anti-goal (a
    backdated boundary makes already-recorded historical sessions count as post-boundary
    accrual). The server always stamps the real instant. ``register_hypothesis``'s own
    payload-level override survives as a hermetic TEST seam only (TC-8's 23:30-ET fixture);
    neither operator-reachable surface (this route, the CLI) can reach it."""

    confirm: bool = False
    hypothesis_id: Optional[str] = None
    family_id: Optional[str] = None
    family_q: Optional[float] = None
    family_candidate_hypothesis_ids: Optional[list[str]] = None
    evidence_family: Optional[str] = None
    estimand: Optional[str] = None
    setup_id: Optional[str] = None
    side: Optional[str] = None
    context_predicate: Optional[dict] = None
    primary_measure_key: Optional[str] = None
    primary_horizon: Optional[str] = None
    sidedness: Optional[str] = None
    null_spec_id: Optional[str] = None
    test_spec_id: Optional[str] = None
    target_sessions: Optional[int] = None
    min_occurrences: Optional[int] = None
    confirmation_start_boundary: Optional[str] = None


@router.post("/registry/hypotheses")
def post_referee_registry_hypothesis(
    body: RefereeHypothesisRegistrationRequest,
    family_store: FamilyStore = Depends(get_referee_family_store),
    hypothesis_store: HypothesisStore = Depends(get_referee_hypothesis_store),
) -> dict:
    """The registration act (goal.md J-05 Step 2): registers one hypothesis (through its family,
    create-if-absent/verify-if-present — see ``referee_registry.py``). Refuses — 422, naming the
    distinct reason, never starting a write — on malformed fields, an unrecognised spec id, a
    retroactive boundary, a family-definition mismatch, or a missing ``confirm``; 409 on a
    duplicate ``family_id``/``hypothesis_id`` (append-only, never a silent overwrite). The
    registration instant is server-stamped, never caller-supplied — see the request model."""
    payload = body.model_dump(exclude={"confirm"})
    try:
        record = register_hypothesis(family_store, hypothesis_store, payload, confirm=body.confirm)
    except (HypothesisMalformed, UnknownSpecId, RetroactiveBoundary, ConfirmationRequired) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (FamilyAlreadyRecorded, HypothesisAlreadyRecorded) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return record
