"""``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold plus J-02's
three snapshot routes. A fresh router/file mounted separately in ``main.py``, mirroring
``referee_routes.py``'s own precedent and rationale (that file's own docstring: "the SAME
rationale desk_routes.py itself gives for splitting off routes.py"). The era's own Data Contract
table (``docs/goal.md``'s Product Shape) names four MORE micro routes landing in later iterations
(scout, walkforward, vault, recorder, graduation) under this SAME ``/research/desk/micro`` prefix
-- a dedicated file is the right home from the start.

Depends on a store this route does NOT own: the dataset store dependency is imported verbatim
from ``routes.get_dataset_store`` (never a second, redefined provider). The readiness cache and
the snapshot-compute manager are this module's OWN wiring (the ``referee_routes.py`` precedent:
"this module owns its own wiring end to end") -- the manager lives as a module-level singleton
behind a ``Depends``-able accessor (the ``desk_routes.py`` ``get_desk_playbook_compute_manager``
precedent, so a test overrides the DEPENDENCY with a fresh manager, never reaches into the
module-level singleton directly).

``GET /readiness`` and ``GET /snapshots``/``GET /snapshots/runs`` are plain reads: page-load GETs
never compute (T-8) -- a snapshot BUILD is an explicit operator act through
``POST /snapshots/compute``, exactly like the desk's own compute-manager pattern."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..config import CONFIG
from .datasets import DatasetStore
from .desk_playbook import PlaybookStore
from .desk_routes import get_playbook_store
from .micro_readiness import MicroReadinessCache, build_readiness, resolve_micro_readiness_cache_db_path
from .micro_snapshots import (
    MicroSnapshotComputeManager,
    list_snapshot_meta,
    read_run_log,
    resolve_micro_snapshots_dir,
)
from .routes import get_dataset_store

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
