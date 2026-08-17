"""``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold, the era's
first route. A fresh router/file mounted separately in ``main.py``, mirroring
``referee_routes.py``'s own precedent and rationale (that file's own docstring: "the SAME
rationale desk_routes.py itself gives for splitting off routes.py"). The era's own Data Contract
table (``docs/goal.md``'s Product Shape) names six MORE micro routes landing in later iterations
(snapshots, scout, walkforward, vault, recorder, graduation) under this SAME
``/research/desk/micro`` prefix -- a dedicated file is the right home from the start.

Depends on a store this route does NOT own: the dataset store dependency is imported verbatim
from ``routes.get_dataset_store`` (never a second, redefined provider). The readiness cache is
this module's OWN wiring (the ``referee_routes.py`` precedent: "this module owns its own wiring
end to end") -- a config-derived, env-overridable path exactly like every sibling durable cache's
own FastAPI dependency (``get_edge_report_cache``/``get_bar_index`` in ``routes.py``).

``GET /readiness`` is a plain read: it triggers nothing but the readiness fold's own documented
one-time-then-cached per-shard classification (page-load GETs never compute a SECOND time, T-8;
the module itself is the ONE place, this route only wires it)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..config import CONFIG
from .datasets import DatasetStore
from .micro_readiness import MicroReadinessCache, build_readiness, resolve_micro_readiness_cache_db_path
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
) -> dict:
    """J-01's corpus-truth fold: the honest per-shard inventory, corpus totals beside the
    referee's tick-gate figure, and the three pilot studies' floor table -- see
    ``micro_readiness.build_readiness``'s own docstring for the full contract. Never 404/500 on
    an empty corpus (the desk router's established never-404-on-absence convention) -- an empty
    ``shards`` list (``study_floors`` still carries its 3 rows, each read against a 0-session
    corpus) at HTTP 200."""
    return build_readiness(dataset_store, cache, dataset_dir=CONFIG.dataset_dir_resolved())
