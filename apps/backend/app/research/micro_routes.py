"""``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold, J-02's three
snapshot routes, J-04's Scout routes, and J-05's three walk-forward routes. A fresh router/file
mounted separately in ``main.py``, mirroring ``referee_routes.py``'s own precedent and rationale
(that file's own docstring: "the SAME rationale desk_routes.py itself gives for splitting off
routes.py"). The era's own Data Contract table (``docs/goal.md``'s Product Shape) names THREE more
micro routes landing in later iterations (vault, recorder, graduation) under this SAME
``/research/desk/micro`` prefix -- a dedicated file is the right home from the start.

Depends on stores this route does NOT own: the dataset store dependency is imported verbatim from
``routes.get_dataset_store``, the universe/bar-store dependencies from ``desk_routes.
get_universe_store``/``routes.get_bar_store`` (never a second, redefined provider). The readiness
cache and every compute manager are this module's OWN wiring (the ``referee_routes.py`` precedent:
"this module owns its own wiring end to end") -- each manager lives as a module-level singleton
behind a ``Depends``-able accessor (the ``desk_routes.py`` ``get_desk_playbook_compute_manager``
precedent, so a test overrides the DEPENDENCY with a fresh manager, never reaches into the
module-level singleton directly).

``GET /readiness``, ``GET /snapshots``/``GET /snapshots/runs``, ``GET /scout``/``GET
/scout/runs``, and ``GET /walkforward``/``GET /walkforward/runs`` are all plain reads: page-load
GETs never compute (T-8) -- a build/screen/fold-evaluation RUN is always an explicit operator act
through its own ``POST .../compute``, exactly the same desk compute-manager pattern three times
over."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..config import CONFIG
from .bars import BarStore
from .datasets import DatasetStore
from .desk_playbook import PlaybookStore
from .desk_routes import get_playbook_store, get_universe_store
from .desk_universe import UniverseStore
from .micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir
from .micro_readiness import MicroReadinessCache, build_readiness, resolve_micro_readiness_cache_db_path
from .micro_snapshots import (
    MicroSnapshotComputeManager,
    list_snapshot_meta,
    read_run_log,
    resolve_micro_snapshots_dir,
)
from .routes import get_bar_store, get_dataset_store
from .scout import ScoutComputeManager, list_scout_families
from .scout_ledger import ScoutLedger, resolve_scout_ledger_dir
from . import walkforward as wf
from .walkforward_ledger import WalkForwardLedger

router = APIRouter(prefix="/research/desk/micro", tags=["micro"])


def get_micro_readiness_cache() -> MicroReadinessCache:
    """The durable ``fallback_frac`` cache -- a config-DERIVED, env-overridable path so
    ``config.py`` stays byte-identical (``config_fingerprint`` unaffected -- the
    ``get_edge_report_cache``/``get_bar_index`` rationale, reused verbatim): the
    ``TAPEOLOGY_MICRO_READINESS_CACHE_DB`` env var if set, else a file co-located as a SIBLING of
    the config-owned dataset directory. A FastAPI dependency so tests can override it outright or
    point it at a temp path via the env var -- the established pattern."""
    return MicroReadinessCache(resolve_micro_readiness_cache_db_path(CONFIG.dataset_dir_resolved()))


@router.get("/readiness")
def get_micro_readiness(
    dataset_store: DatasetStore = Depends(get_dataset_store),
    cache: MicroReadinessCache = Depends(get_micro_readiness_cache),
    playbook_store: PlaybookStore = Depends(get_playbook_store),
) -> dict:
    """J-01's corpus-truth fold: the honest per-shard inventory, corpus totals beside the
    referee's tick-gate figure, and the three pilot studies' floor table -- see
    ``micro_readiness.build_readiness``'s own docstring for the full contract. Never 404/500 on
    an empty corpus (the desk router's established never-404-on-absence convention) -- an empty
    ``shards`` list (``study_floors`` still carries its 3 rows, each read against a 0-session
    corpus) at HTTP 200.

    J-03: ``playbook_store`` is the EXISTING ``desk_routes.get_playbook_store`` dependency,
    reused verbatim (never a second, redefined provider) -- it feeds the ``joinable_corpus``
    field, computed by ``micro_join.joinable_corpus_counts``."""
    return build_readiness(
        dataset_store, cache, dataset_dir=CONFIG.dataset_dir_resolved(), playbook_store=playbook_store
    )


def get_micro_snapshots_dir() -> str:
    """The snapshot store's directory -- ``TAPEOLOGY_MICRO_SNAPSHOTS_DIR`` if set, else a
    SIBLING of the config-owned dataset directory (``micro_snapshots.resolve_micro_snapshots_dir``
    -- see that function's own docstring)."""
    return resolve_micro_snapshots_dir(CONFIG.dataset_dir_resolved())


# The single in-flight (or last-terminal) snapshot-build job for THIS process -- the
# ``desk_routes.py`` module-singleton-behind-a-Depends-accessor precedent (module docstring), never
# per-request-constructed (a fresh manager per request could never observe a job it just started).
_micro_snapshot_compute_manager = MicroSnapshotComputeManager()


def get_micro_snapshot_compute_manager() -> MicroSnapshotComputeManager:
    """A FastAPI dependency so a test overrides it outright with a fresh, isolated manager (the
    ``get_desk_playbook_compute_manager`` precedent) -- never reaches into the module-level
    singleton directly."""
    return _micro_snapshot_compute_manager


@router.get("/snapshots")
def get_micro_snapshots(
    dataset_store: DatasetStore = Depends(get_dataset_store),
    snapshots_dir: str = Depends(get_micro_snapshots_dir),
) -> dict:
    """BUILD METADATA only -- the identity tuple, ``row_count``, ``quote_size_unit``, timestamps
    -- for every CURRENTLY VALID (identity re-verified) snapshot; never raw per-event feature
    rows (the boundary note: an origin-fenced, event-level read is ``micro_accessor.py``'s
    exclusive door, J-05, not this route). Never 404/500 on zero built snapshots -- an honest
    empty list, the desk router's established convention."""
    return {"snapshots": list_snapshot_meta(snapshots_dir, dataset_store, CONFIG)}


@router.post("/snapshots/compute")
def trigger_micro_snapshots_compute(
    dataset_store: DatasetStore = Depends(get_dataset_store),
    snapshots_dir: str = Depends(get_micro_snapshots_dir),
    manager: MicroSnapshotComputeManager = Depends(get_micro_snapshot_compute_manager),
) -> dict:
    """Start a snapshot build for every dataset currently in the store (reusing any already-valid
    snapshot -- ``run_snapshot_build_and_record``'s own reuse-or-build discipline), or refuse
    (single-flight) if one is already running."""
    result = manager.trigger(dataset_store, CONFIG, snapshots_dir)
    if result["state"] == "refused":
        return result
    return {"state": result["state"], "run_id": result["run_id"]}


@router.get("/snapshots/compute")
def get_micro_snapshots_compute(
    manager: MicroSnapshotComputeManager = Depends(get_micro_snapshot_compute_manager),
) -> dict:
    """The current (or last-terminal) build job's progress -- never 404 (the ``_IDLE_SNAPSHOT``
    default before any job has ever run this process)."""
    snap = manager.snapshot()
    return {
        "state": snap["state"],
        "progress": snap["progress"],
        "started_utc": snap["started_utc"],
        "finished_utc": snap["finished_utc"],
        "error": snap["error"],
    }


@router.post("/snapshots/compute/cancel")
def cancel_micro_snapshots_compute(
    manager: MicroSnapshotComputeManager = Depends(get_micro_snapshot_compute_manager),
) -> dict:
    """Signal cooperative cancellation for the in-flight job -- a 409 for an idle manager (the
    ``desk_playbook`` "the ROUTE is the one that rejects an idle cancel with a 409" precedent),
    else ``{"state": "cancelled"}`` acknowledging the REQUEST (the worker itself settles at the
    next dataset boundary -- ``MicroSnapshotComputeManager.cancel``'s own docstring)."""
    if manager.snapshot()["state"] != "running":
        raise HTTPException(status_code=409, detail="no snapshot build is currently running")
    manager.cancel()
    return {"state": "cancelled"}


@router.get("/snapshots/runs")
def get_micro_snapshots_runs(snapshots_dir: str = Depends(get_micro_snapshots_dir)) -> dict:
    """The durable build-run history, newest first -- never 404 on zero runs (an honest empty
    list)."""
    return {"runs": read_run_log(snapshots_dir)}


# --- J-04: the Scout + exploratory candidate ledger (scout.py, scout_ledger.py) -----------------


def get_scout_ledger_dir() -> str:
    """The scout ledger's directory -- ``TAPEOLOGY_MICRO_SCOUT_DIR`` if set, else a SIBLING of the
    config-owned dataset directory (``scout_ledger.resolve_scout_ledger_dir`` -- see that
    function's own docstring)."""
    return resolve_scout_ledger_dir(CONFIG.dataset_dir_resolved())


# The single in-flight (or last-terminal) scout-screening job for THIS process -- the same
# module-singleton-behind-a-Depends-accessor precedent as the snapshot manager above.
_scout_compute_manager = ScoutComputeManager()


def get_scout_compute_manager() -> ScoutComputeManager:
    """A FastAPI dependency so a test overrides it outright with a fresh, isolated manager (the
    ``get_micro_snapshot_compute_manager`` precedent) -- never reaches into the module-level
    singleton directly."""
    return _scout_compute_manager


@router.get("/scout")
def get_scout(ledger_dir: str = Depends(get_scout_ledger_dir)) -> dict:
    """Every registered family's trials, verbatim as ledgered (``scout.list_scout_families`` --
    see that function's own docstring), BESIDE the ledger's own chain-verification verdict. Never
    404/500 on an empty ledger -- an honest empty ``families`` list, the desk router's established
    never-404-on-absence convention. Page-load GETs never compute (T-8): a screening RUN is an
    explicit operator act through ``POST /scout/compute``.

    ``chain_verification`` is ``ScoutLedger.verify_chain()`` verbatim (iter-4 audit fix): the
    ledger's tamper check existed but nothing that SERVED the ledger ever ran it, so a row whose
    ``decision`` had been flipped from ``killed_null`` to ``survive`` on disk was served as a
    survivor with no hint anything was wrong -- exactly the "no code path silently accepts the
    tampered chain" clause this iteration's own TC-3 requires. Surfaced beside the data rather
    than refused, the same discipline this iteration's ``playbook_integrity_errors`` passenger fix
    chose for a corrupt playbook record: a reader is handed the corruption, never denied the
    (honestly labelled) evidence. Verification is a cheap re-hash of the ledger file -- a read,
    never a compute (T-8)."""
    ledger = ScoutLedger(ledger_dir)
    return {
        "families": list_scout_families(ledger),
        "chain_verification": ledger.verify_chain(),
    }


@router.post("/scout/compute")
def trigger_scout_compute(
    dataset_store: DatasetStore = Depends(get_dataset_store),
    snapshots_dir: str = Depends(get_micro_snapshots_dir),
    ledger_dir: str = Depends(get_scout_ledger_dir),
    manager: ScoutComputeManager = Depends(get_scout_compute_manager),
) -> dict:
    """Start a Scout screening run over the bounded reference candidate grid (ensuring
    prerequisite snapshots exist first -- reuse-or-build), or refuse (single-flight) if one is
    already running."""
    result = manager.trigger(dataset_store, CONFIG, snapshots_dir, ledger_dir)
    if result["state"] == "refused":
        return result
    return {"state": result["state"], "run_id": result["run_id"]}


@router.get("/scout/compute")
def get_scout_compute(manager: ScoutComputeManager = Depends(get_scout_compute_manager)) -> dict:
    """The current (or last-terminal) screening job's progress -- never 404 (the idle default
    before any job has ever run this process)."""
    snap = manager.snapshot()
    return {
        "state": snap["state"],
        "progress": snap["progress"],
        "started_utc": snap["started_utc"],
        "finished_utc": snap["finished_utc"],
        "error": snap["error"],
    }


@router.post("/scout/compute/cancel")
def cancel_scout_compute(manager: ScoutComputeManager = Depends(get_scout_compute_manager)) -> dict:
    """Signal cooperative cancellation for the in-flight job -- a 409 for an idle manager (the
    snapshot-compute-cancel route's own precedent), else ``{"state": "cancelled"}`` acknowledging
    the REQUEST (the worker itself settles at the next candidate boundary)."""
    if manager.snapshot()["state"] != "running":
        raise HTTPException(status_code=409, detail="no scout screening run is currently running")
    manager.cancel()
    return {"state": "cancelled"}


@router.get("/scout/runs")
def get_scout_runs(ledger_dir: str = Depends(get_scout_ledger_dir)) -> dict:
    """The durable run history, newest first -- never 404 on zero runs (an honest empty list)."""
    return {"runs": read_run_log(ledger_dir)}


# --- J-05: the chronological walk-forward engine (walkforward.py, walkforward_ledger.py) --------


def get_walkforward_ledger_dir() -> str:
    """The walk-forward ledger's directory -- ``TAPEOLOGY_MICRO_WALKFORWARD_DIR`` if set, else a
    SIBLING of the config-owned dataset directory (``walkforward.resolve_walkforward_ledger_dir``
    -- see that function's own docstring)."""
    return wf.resolve_walkforward_ledger_dir(CONFIG.dataset_dir_resolved())


def get_micro_exposure_registry_dir() -> str:
    """The exposure registry's directory -- ``TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR`` if set, else
    a SIBLING of the config-owned dataset directory (``micro_accessor.resolve_micro_exposure_
    registry_dir`` -- see that function's own docstring). Shared by every J-05 caller that logs or
    reads exposure state, not owned exclusively by this route file."""
    return resolve_micro_exposure_registry_dir(CONFIG.dataset_dir_resolved())


# The single in-flight (or last-terminal) walk-forward job for THIS process -- the same
# module-singleton-behind-a-Depends-accessor precedent as the snapshot/scout managers above.
_walkforward_compute_manager = wf.WalkForwardComputeManager()


def get_walkforward_compute_manager() -> "wf.WalkForwardComputeManager":
    """A FastAPI dependency so a test overrides it outright with a fresh, isolated manager (the
    ``get_scout_compute_manager`` precedent) -- never reaches into the module-level singleton
    directly."""
    return _walkforward_compute_manager


@router.get("/walkforward")
def get_walkforward(ledger_dir: str = Depends(get_walkforward_ledger_dir)) -> dict:
    """Every registered fold spec plus every sequence's fold results, decay view, and sequence
    verdict (``wf.list_fold_specs``/``wf.list_walkforward_sequences`` -- see those functions' own
    docstrings), BESIDE the ledger's own chain-verification verdict (the ``GET /scout`` precedent:
    surfaced beside the data rather than refused, never silently accepted if tampered). Never
    404/500 on an empty ledger -- an honest empty ``fold_specs``/``sequences``, the desk router's
    established never-404-on-absence convention. Page-load GETs never compute (T-8): a fold-
    evaluation RUN is an explicit operator act through ``POST /walkforward/compute``."""
    ledger = WalkForwardLedger(ledger_dir)
    return {
        "fold_specs": wf.list_fold_specs(ledger),
        "sequences": wf.list_walkforward_sequences(ledger),
        "chain_verification": ledger.verify_chain(),
    }


@router.post("/walkforward/compute")
def trigger_walkforward_compute(
    ledger_dir: str = Depends(get_walkforward_ledger_dir),
    exposure_registry_dir: str = Depends(get_micro_exposure_registry_dir),
    universe_store: UniverseStore = Depends(get_universe_store),
    bar_store: BarStore = Depends(get_bar_store),
    playbook_store: PlaybookStore = Depends(get_playbook_store),
    manager: "wf.WalkForwardComputeManager" = Depends(get_walkforward_compute_manager),
) -> dict:
    """Start the diagnostic acceptance run (goal.md J-05 IN SCOPE item 8) against the operator's
    REAL playbook/universe/bar stores, or refuse (single-flight) if one is already running. The
    ONLY mode this iteration wires -- Mode A/pilot-study registrations are J-09's own scope."""
    ledger = WalkForwardLedger(ledger_dir)
    exposure_registry = ExposureRegistry(exposure_registry_dir)

    def _work(publish, should_abort) -> dict:
        result = wf.run_diagnostic_walkforward(
            ledger, exposure_registry, playbook_store, universe_store, bar_store, CONFIG,
            progress=publish, should_abort=should_abort,
        )
        return {
            "folds_evaluated": result["folds_evaluated"],
            # Disclosed beside the count above so a repeat trigger's run-log entry reads honestly:
            # a re-run replays the SAME folds' existing ledger rows rather than recording the same
            # evidence twice (``walkforward_ledger.append_fold_result``'s own docstring).
            "folds_replayed": result["folds_replayed"],
            "validation_sessions": result["validation_sessions"],
            "session_count": result["session_count"],
        }

    result = manager.trigger(_work, run_log_dir=ledger_dir, steps_total=1)
    if result["state"] == "refused":
        return result
    return {"state": result["state"], "run_id": result["run_id"]}


@router.get("/walkforward/compute")
def get_walkforward_compute(manager: "wf.WalkForwardComputeManager" = Depends(get_walkforward_compute_manager)) -> dict:
    """The current (or last-terminal) run's progress -- never 404 (the idle default before any job
    has ever run this process)."""
    snap = manager.snapshot()
    return {
        "state": snap["state"],
        "progress": snap["progress"],
        "started_utc": snap["started_utc"],
        "finished_utc": snap["finished_utc"],
        "error": snap["error"],
    }


@router.post("/walkforward/compute/cancel")
def cancel_walkforward_compute(manager: "wf.WalkForwardComputeManager" = Depends(get_walkforward_compute_manager)) -> dict:
    """Signal cooperative cancellation for the in-flight job -- a 409 for an idle manager (the
    snapshot/scout-compute-cancel routes' own precedent), else ``{"state": "cancelled"}``
    acknowledging the REQUEST (the worker itself settles at the next fold boundary)."""
    if manager.snapshot()["state"] != "running":
        raise HTTPException(status_code=409, detail="no walk-forward run is currently running")
    manager.cancel()
    return {"state": "cancelled"}


@router.get("/walkforward/runs")
def get_walkforward_runs(ledger_dir: str = Depends(get_walkforward_ledger_dir)) -> dict:
    """The durable run history, newest first -- never 404 on zero runs (an honest empty list)."""
    return {"runs": read_run_log(ledger_dir)}
