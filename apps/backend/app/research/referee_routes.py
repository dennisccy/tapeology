"""``/research/desk/referee/*`` — Era 6 "The Referee" (J-01): the readiness fold, the FIRST
concrete Referee artifact. See ``referee_evidence.py``'s own module docstring for the fold's
mechanics; this file is pure wiring.

A fresh router/file rather than folding into ``desk_routes.py`` (already 1600+ lines) — the SAME
rationale ``desk_routes.py`` itself gives for splitting off ``routes.py``: "mounted separately ...
rather than folding into routes.py, which is already large." The era's own Data Contract table
(``docs/goal.md``'s Product Shape) names five MORE referee routes landing in later iterations
(nulls, registry, evaluations, adjudications) under this SAME ``/research/desk/referee`` prefix —
a dedicated file is the right home from the start.

Depends on stores this route does NOT own: the playbook store dependency is imported verbatim from
``desk_routes.get_playbook_store`` and the dataset store dependency from ``routes.get_dataset_store``
(never a second, redefined provider for either) — the ``JournalStore`` (for backtest reports) comes
through the existing ``ResearchRegistry`` (``routes.get_registry``), the SAME seam
``GET /research/backtests`` already reads. A plain read: triggers nothing, recomputes nothing
(GET-never-computes) — this route takes no compute-manager dependency at all."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..config import CONFIG
from .datasets import DatasetStore
from .desk_playbook import PlaybookStore
from .desk_routes import get_playbook_store
from .referee_evidence import referee_evidence
from .routes import ResearchRegistry, get_dataset_store, get_registry

router = APIRouter(prefix="/research/desk/referee", tags=["referee"])


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
