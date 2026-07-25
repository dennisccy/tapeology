"""``/research/desk/*`` — Era B "The Desk" (J-01): universe ingestion.

THIS is the first desk-era route module: two routes over the new universe subsystem
(``desk_universe.py``) — ``POST /research/desk/universe/fetch`` (the explicit operator research
action: fetch -> parse -> validate -> register) and ``GET /research/desk/universe`` (snapshot
list + latest membership, honestly empty before any registration — never 404). Kept as its own
module (mirroring the plan's stated preference) rather than folding into ``routes.py``, which is
already large; mounted separately in ``app/main.py``.

The fetch is a single synchronous vendor call, so — unlike the longer-running J-02/J-03 top-up and
screen runs — it needs no compute-manager (that pattern lands with those later journeys)."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException

from ..config import CONFIG
from .desk_universe import (
    UniverseAlreadyRegistered,
    UniverseFetchError,
    UniverseStore,
    UniverseValidationError,
    fetch_constituents_html,
    parse_constituents,
)

router = APIRouter(prefix="/research/desk", tags=["desk"])


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
