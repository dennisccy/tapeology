"""``/research/desk/*`` — Era B "The Desk" (J-01 + J-02): universe ingestion, coverage, and the
bar top-up.

J-01 (unmodified this iteration): two routes over the universe subsystem (``desk_universe.py``) —
``POST /research/desk/universe/fetch`` (the explicit operator research action: fetch -> parse ->
validate -> register) and ``GET /research/desk/universe`` (snapshot list + latest membership,
honestly empty before any registration — never 404).

J-02 (this iteration) adds two more concepts under the SAME router: ``GET /research/desk/coverage``
(a pure read, ``desk_coverage.get_desk_coverage`` — no compute-manager needed, mirrors
``GET /research/desk/universe``'s own single-synchronous-read shape) and the desk bar top-up's
three compute-manager routes (``POST``/``GET /research/desk/topup/compute``,
``POST /research/desk/topup/compute/cancel`` — mirrors ``routes.py``'s
``/edge-report/compute`` trio verbatim). Kept as its own module (mirroring the plan's stated
preference) rather than folding into ``routes.py``, which is already large; mounted separately in
``app/main.py``.

**The top-up manager is a module-level singleton here, NOT a ``ResearchRegistry`` property.**
``DeskTopupComputeManager`` (``desk_topup_compute.py``) reuses ``routes.record_bar_series``
in-process, so it must import FROM ``routes.py`` — if ``ResearchRegistry`` held the manager (the
``EdgeReportComputeManager`` precedent), ``routes.py`` would need to import IT back, a circular
import. ``get_desk_topup_manager`` is a FastAPI dependency instead (the ``get_universe_fetcher``
seam), test-overridable via ``app.dependency_overrides`` exactly like every other store/seam in
this module."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException

from ..config import CONFIG
from .bar_index import BarIndex
from .bars import BarStore
from .desk_coverage import get_desk_coverage
from .desk_topup_compute import DeskTopupComputeManager
from .desk_universe import (
    UniverseAlreadyRegistered,
    UniverseFetchError,
    UniverseStore,
    UniverseValidationError,
    fetch_constituents_html,
    parse_constituents,
)
from .routes import ResearchRegistry, get_bar_index, get_bar_store, get_registry

router = APIRouter(prefix="/research/desk", tags=["desk"])

# The desk top-up compute manager — a process-wide singleton (constructed once at import time,
# mirroring how ``EdgeReportComputeManager`` lives for the life of the process). Exposed only
# through ``get_desk_topup_manager`` below so a test overrides it outright via
# ``app.dependency_overrides`` for complete test-to-test isolation (the ``get_universe_fetcher``
# pattern), rather than sharing in-flight job state across tests.
_desk_topup_manager = DeskTopupComputeManager()


def get_universe_store() -> UniverseStore:
    """The universe store rooted at the config-owned directory (``TAPEOLOGY_DESK_UNIVERSE_DIR``
    override, package-anchored default) — the ``get_bar_store``/``get_dataset_store`` pattern. A
    FastAPI dependency so tests can point it at a temp dir via the env var or override it
    outright."""
    return UniverseStore(CONFIG.desk_universe_dir_resolved())


def get_universe_fetcher() -> Callable[[str], str]:
    """The universe-page HTML fetch — a FastAPI dependency so a hermetic test overrides it
    outright via ``app.dependency_overrides`` (the ``get_bar_store``/``get_dataset_store`` seam)
    and injects fixture HTML with ZERO network calls. The default is the real keyless HTTP GET
    (``fetch_constituents_html``) bound to the existing vendor-call budget
    (``CONFIG.vendor_http_timeout_seconds`` — the same deadline every adapter already honors)."""

    def _fetch(source_url: str) -> str:
        return fetch_constituents_html(source_url, timeout=CONFIG.vendor_http_timeout_seconds)

    return _fetch


@router.post("/universe/fetch")
def fetch_universe(
    store: UniverseStore = Depends(get_universe_store),
    fetcher: Callable[[str], str] = Depends(get_universe_fetcher),
) -> dict:
    """Fetch -> parse -> validate -> register ONE new universe snapshot — the explicit operator
    research action; nothing here runs on a schedule or a page load. Three honest, distinct
    failure states (mirrors the ``POST /research/bars`` taxonomy):
      * the vendor fetch itself fails (unreachable / non-200) -> 503, naming the source
        (``UniverseFetchError`` — never a fabricated or cached fallback page);
      * a parse/charset/bounds failure -> 422, naming the specific problem
        (``UniverseValidationError`` — T-1, never a partial or guessed list);
      * content identical to an already-registered snapshot -> 409, naming the existing snapshot
        (``UniverseAlreadyRegistered`` — snapshots are immutable, never rewritten)."""
    source_url = CONFIG.desk_universe_source_url
    try:
        html = fetcher(source_url)
    except UniverseFetchError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    try:
        parsed = parse_constituents(
            html,
            min_members=CONFIG.desk_universe_min_members,
            max_members=CONFIG.desk_universe_max_members,
        )
    except UniverseValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    try:
        meta = store.record(
            members=parsed.members,
            raw_members=parsed.raw_members,
            source_url=source_url,
            min_members=CONFIG.desk_universe_min_members,
            max_members=CONFIG.desk_universe_max_members,
        )
    except UniverseAlreadyRegistered as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"universe": meta}


@router.get("/universe")
def get_universe(store: UniverseStore = Depends(get_universe_store)) -> dict:
    """Snapshot list + latest membership, verbatim (checksum-verified on load). An explicit HTTP
    200 EMPTY payload before any registration — never a 404 (the ``GET /research/bars`` /
    ``GET /research/datasets`` no-data convention). ``latest`` is the most recently created
    snapshot (``None`` before any registration) — never recomputed, always the stored record."""
    records, errors = store.list()
    latest = records[-1] if records else None
    return {"snapshots": records, "latest": latest, "integrity_errors": errors}


# --- Coverage (J-02) --------------------------------------------------------------------------
# A single synchronous read — no compute-manager needed (unlike the top-up below): coverage is
# always index-fast (T-4), never a multi-second operation.


@router.get("/coverage")
def get_coverage(
    store: UniverseStore = Depends(get_universe_store),
    index: BarIndex = Depends(get_bar_index),
) -> dict:
    """Per-member x per-``DESK_TOPUP_TIMEFRAMES`` bar coverage for the LATEST universe snapshot,
    read entirely from ``bar_index`` (T-4 — never re-hashes ``BarStore``). An explicit HTTP 200
    honest-empty payload (``universe_snapshot_id: null``, ``members: []``) before any universe
    snapshot exists — never a 404 (the ``GET /research/desk/universe`` convention). See
    ``desk_coverage.get_desk_coverage`` for the exact shape."""
    return get_desk_coverage(store, index)


# --- The operator-run bar top-up (J-02) — three subpaths, mirrors ``routes.py``'s
# ``/edge-report/compute`` trio (``routes.py:1268/1293/1302``) exactly: ``POST
# /research/desk/topup/compute`` (single-flight trigger), ``GET /research/desk/topup/compute``
# (poll the snapshot), ``POST /research/desk/topup/compute/cancel`` (409 when idle). ---------------


def get_desk_topup_manager() -> DeskTopupComputeManager:
    """The desk top-up compute manager — a FastAPI dependency (the ``get_universe_store``/
    ``get_universe_fetcher`` pattern) so a test overrides it outright via
    ``app.dependency_overrides`` for complete test-to-test isolation. The default resolves the
    process-wide singleton constructed at module import time."""
    return _desk_topup_manager


@router.post("/topup/compute")
def trigger_desk_topup_compute(
    universe_store: UniverseStore = Depends(get_universe_store),
    bar_store: BarStore = Depends(get_bar_store),
    bar_index: BarIndex = Depends(get_bar_index),
    registry: ResearchRegistry = Depends(get_registry),
    manager: DeskTopupComputeManager = Depends(get_desk_topup_manager),
) -> dict:
    """Start the single-flight desk top-up job over the LATEST universe snapshot's members, or —
    if one is already running — return it UNCHANGED (``started: False``, never a second concurrent
    job). Returns ``{"started": bool, "compute": <snapshot>}``; the actual walk runs on a
    background worker thread, off this request, so this route returns immediately regardless of
    how long the top-up takes."""
    return manager.trigger(universe_store, bar_store, bar_index, registry)


@router.get("/topup/compute")
def get_desk_topup_compute(
    manager: DeskTopupComputeManager = Depends(get_desk_topup_manager),
) -> dict | None:
    """The top-up job's current/last snapshot, served VERBATIM — or ``null`` if no top-up has ever
    run this process. A plain read: never triggers a compute as a side effect (GET-never-computes,
    TC-10)."""
    return manager.snapshot()


@router.post("/topup/compute/cancel")
def cancel_desk_topup_compute(
    manager: DeskTopupComputeManager = Depends(get_desk_topup_manager),
) -> dict:
    """Cancel the in-flight desk top-up (cooperative — observed between pairs). ``409`` when idle
    (no job has ever run, or the last job already reached a terminal state) — mirrors
    ``cancel_edge_report_compute``'s own 409-when-terminal shape."""
    snapshot = manager.snapshot()
    if snapshot is None or snapshot["state"] != "running":
        raise HTTPException(status_code=409, detail="no desk top-up compute is currently running")
    manager.cancel()
    return {"cancelling": True}
