"""``/research/desk/*`` — Era B "The Desk" (J-01 + J-02 + J-03): universe ingestion, coverage, the
bar top-up, and the screen.

J-01 (unmodified this iteration): two routes over the universe subsystem (``desk_universe.py``) —
``POST /research/desk/universe/fetch`` (the explicit operator research action: fetch -> parse ->
validate -> register) and ``GET /research/desk/universe`` (snapshot list + latest membership,
honestly empty before any registration — never 404).

J-02 (unmodified this iteration) adds two more concepts under the SAME router:
``GET /research/desk/coverage`` (a pure read, ``desk_coverage.get_desk_coverage`` — no
compute-manager needed, mirrors ``GET /research/desk/universe``'s own single-synchronous-read
shape) and the desk bar top-up's three compute-manager routes (``POST``/``GET
/research/desk/topup/compute``, ``POST /research/desk/topup/compute/cancel`` — mirrors
``routes.py``'s ``/edge-report/compute`` trio verbatim).

J-03 (base shape unmodified; ``GET /research/desk/screen`` extended goal-desk-iter-16) adds the
screen: latest + ``?date=`` + ``?id=`` (J-12, below) + a lightweight meta-only snapshot list — never
full ``rows``/``skipped`` for every historical snapshot, see ``desk_screen.py``'s module docstring —
and the screen's own three compute-manager routes (``POST``/``GET /research/desk/screen/compute``,
``POST /research/desk/screen/compute/cancel`` — mirrors the top-up trio exactly). Kept as its own
module (mirroring the plan's stated preference) rather than folding into ``routes.py``, which is
already large; mounted separately in ``app/main.py``.

J-09 (base shape unmodified; response body extended goal-desk-iter-16) adds ONE new read:
``GET /research/desk/topup/runs`` (the durable, append-only top-up run log — ``desk_topup_log.py``'s
lightweight run-meta list + the latest full record + ``integrity_errors`` (J-12, below); honest-empty
``{"runs": [], "latest": null, "integrity_errors": []}`` before any run, never a 404). No new compute
manager, no new POST — the log is written by the ALREADY-existing top-up trigger/CLI paths
(``desk_topup_compute.py`` threads the write through internally); this route is a pure read,
mirroring ``GET /research/desk/universe``'s single-synchronous-read shape exactly.

J-10 (base shape from goal-desk-iter-14; response body extended goal-desk-iter-16) adds the
coverage-index reconciliation: a trigger/poll/cancel trio (``POST``/``GET
/research/desk/coverage/reconcile/compute``, ``POST /research/desk/coverage/reconcile/compute/cancel``
— mirrors the top-up trio exactly) plus ONE durable read (``GET
/research/desk/coverage/reconcile/runs`` — mirrors ``GET /research/desk/topup/runs``'s exact
honest-empty/meta-only-list/full-latest/``integrity_errors`` shape). All four routes are pure wiring
over ``desk_index_reconcile.py`` — see that module's own docstring for the classify/repair/record
mechanics. No new MCP tool (``get_endpoint``'s existing ``/research/`` allowlist already reaches the
new GET path); no new router, no ``main.py`` change.

J-12 (goal-desk-iter-16) is a pure additive-read + disclosure change, no new
module/route/MCP tool: (a) ``GET /research/desk/screen`` gains a sibling ``?id=`` read so an
EARLIER same-``screen_date`` recording — unreachable via ``?date=``, which always resolves to the
newest match — becomes individually addressable by its own id; supplying both ``?id=`` and
``?date=`` is an honest 4xx refusal. (b) ``get_topup_runs``/``get_desk_index_reconcile_runs`` stop
discarding their own ``store.list()``'s ``errors`` return — both now serve it as
``integrity_errors``, the identical key/shape ``get_screen``/``get_universe`` already used.

J-18 (this iteration, goal-desk-iter-29) adds ONE new read: ``GET /research/desk/screen/runs`` (the
durable, append-only screen-RUN log — ``desk_screen_log.py``'s lightweight run-meta list + the
latest full record + ``integrity_errors``; honest-empty ``{"runs": [], "latest": null,
"integrity_errors": []}`` before any run, never a 404) — the SAME shape its two siblings
(``get_topup_runs``/``get_desk_index_reconcile_runs``) already serve. No new compute manager, no
new POST — the log is written internally by ``run_screen_and_record`` (the single shared writer
both ``DeskScreenComputeManager`` and the CLI call), which also now resolves the screen's five pins
BEFORE the walk and short-circuits an identical-pin retrigger to the existing snapshot (zero
``compute_tradability`` calls) — see ``desk_screen_compute.py``'s own module docstring. This route
only threads a ``ScreenRunStore`` dependency through ``trigger_desk_screen_compute``; the route
itself is a pure read, mirroring ``GET /research/desk/topup/runs``'s single-synchronous-read shape
exactly. No new MCP tool (``get_endpoint``'s existing ``/research/`` allowlist already reaches the
new GET path); no new router, no ``main.py`` change.

J-20 (this iteration, goal-desk-iter-35) adds ONE new read: ``GET /research/desk/screen/compare``
(``?id=<compare id>&base=<base id>``) — how the named snapshot differs from the one recorded
immediately before it, computed entirely by the new ``desk_screen_diff.py`` over two records already
returned by ``get_screen_store``'s own ``ScreenStore.list()``. This route takes NO
``BarStore``/``bar_index``/``DatasetStore`` dependency at all — it is structurally incapable of
triggering ``compute_tradability`` or any other recompute. No new store, no new compute manager, no
new MCP tool (the existing ``/research/`` allowlist already reaches the new path); no new router, no
``main.py`` change.

J-21 (this iteration, goal-desk-iter-36) adds ONE new read: ``GET /research/desk/screen/pins``
(``screen_date`` REQUIRED query param) — the five pins a screen run for that date would resolve
RIGHT NOW, and whether a screen is already recorded under them, computed entirely by the new
``desk_screen_pins.py`` over the SAME accessors ``run_screen_and_record`` already uses. This route
takes a ``UniverseStore``/``BarIndex``/``ScreenStore`` dependency but NO ``BarStore``/
``DatasetStore``/compute-manager dependency at all — it is structurally incapable of triggering
``compute_tradability`` or any other recompute. An honest empty payload at HTTP 200 before any
universe snapshot is registered (never a 4xx/5xx). No new store, no new compute manager, no new
``Config`` field, no new MCP tool (the existing ``/research/`` allowlist already reaches the new
path); no new router, no ``main.py`` change.

**Compute managers are module-level singletons here, NOT ``ResearchRegistry`` properties.**
``DeskTopupComputeManager`` (``desk_topup_compute.py``) reuses ``routes.record_bar_series``
in-process, so it must import FROM ``routes.py`` — if ``ResearchRegistry`` held the manager (the
``EdgeReportComputeManager`` precedent), ``routes.py`` would need to import IT back, a circular
import. ``DeskScreenComputeManager`` (``desk_screen_compute.py``) and
``DeskIndexReconcileComputeManager`` (``desk_index_reconcile.py``, J-10) have no such constraint
(neither needs anything from ``routes.py``), but are placed here anyway for consistency with their
sibling — there is no functional reason to prefer the registry either. All three are FastAPI
dependencies instead (the ``get_universe_fetcher`` seam), test-overridable via
``app.dependency_overrides`` exactly like every other store/seam in this module."""

from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..config import CONFIG
from .bar_index import BarIndex
from .bars import BarStore
from .datasets import DatasetStore
from .desk_coverage import get_desk_coverage
from .desk_index_reconcile import (
    DeskIndexReconcileComputeManager,
    ReconcileRunStore,
    resolve_desk_index_reconcile_dir,
)
from .desk_screen import ScreenStore, resolve_desk_screen_dir
from .desk_screen_compute import DeskScreenComputeManager
from .desk_screen_diff import ScreenDiffSelfCompareError, compute_screen_diff
from .desk_screen_log import ScreenRunStore, resolve_desk_screen_log_dir
from .desk_screen_pins import resolve_desk_screen_pins
from .desk_topup_compute import DeskTopupComputeManager
from .desk_topup_log import TopupRunStore, resolve_desk_topup_log_dir
from .desk_universe import (
    UniverseAlreadyRegistered,
    UniverseFetchError,
    UniverseStore,
    UniverseValidationError,
    fetch_constituents_html,
    parse_constituents,
)
from .routes import ResearchRegistry, get_bar_index, get_bar_store, get_dataset_store, get_registry

router = APIRouter(prefix="/research/desk", tags=["desk"])

# The desk top-up compute manager — a process-wide singleton (constructed once at import time,
# mirroring how ``EdgeReportComputeManager`` lives for the life of the process). Exposed only
# through ``get_desk_topup_manager`` below so a test overrides it outright via
# ``app.dependency_overrides`` for complete test-to-test isolation (the ``get_universe_fetcher``
# pattern), rather than sharing in-flight job state across tests.
_desk_topup_manager = DeskTopupComputeManager()

# The desk screen compute manager (J-03) — the SAME process-wide-singleton-behind-a-dependency
# shape as ``_desk_topup_manager`` immediately above.
_desk_screen_compute_manager = DeskScreenComputeManager()

# The desk coverage-index reconciliation compute manager (J-10) — the SAME process-wide-singleton-
# behind-a-dependency shape as its two siblings above.
_desk_index_reconcile_manager = DeskIndexReconcileComputeManager()


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


def get_topup_run_store() -> TopupRunStore:
    """The top-up run log store rooted at a bare env-var-or-sibling-of-the-universe-dir default
    (zero new ``Config`` field — J-09, see ``desk_topup_log.resolve_desk_topup_log_dir``) — the
    ``get_screen_store`` pattern. A FastAPI dependency so tests can point it at a temp dir via the
    env var or override it outright."""
    return TopupRunStore(resolve_desk_topup_log_dir(CONFIG.desk_universe_dir_resolved()))


@router.post("/topup/compute")
def trigger_desk_topup_compute(
    universe_store: UniverseStore = Depends(get_universe_store),
    bar_store: BarStore = Depends(get_bar_store),
    bar_index: BarIndex = Depends(get_bar_index),
    registry: ResearchRegistry = Depends(get_registry),
    manager: DeskTopupComputeManager = Depends(get_desk_topup_manager),
    topup_run_store: TopupRunStore = Depends(get_topup_run_store),
) -> dict:
    """Start the single-flight desk top-up job over the LATEST universe snapshot's members, or —
    if one is already running — return it UNCHANGED (``started: False``, never a second concurrent
    job). Returns ``{"started": bool, "compute": <snapshot>}``; the actual walk runs on a
    background worker thread, off this request, so this route returns immediately regardless of
    how long the top-up takes. J-09: the job's terminal outcome is durably recorded into
    ``topup_run_store`` once it resolves (inside ``DeskTopupComputeManager.trigger`` itself — see
    that method's docstring) — this route only threads the store dependency through."""
    return manager.trigger(universe_store, bar_store, bar_index, registry, topup_run_store=topup_run_store)


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


# --- The top-up run log (J-09) — ONE read: a lightweight run-meta list + the latest full record.
# No POST here: the log is written internally by the trigger/CLI paths above (the single shared
# writer, `desk_topup_log.record_topup_run`) — this route is a pure read, never a trigger. --------


def _topup_run_meta_only(record: dict) -> dict:
    """The lightweight projection ``GET /research/desk/topup/runs``'s bulk list serves — every
    field EXCEPT ``outcomes`` (mirrors ``_screen_meta_only``'s identical convention: a run record
    carrying every pair's outcome is materially larger than its own summary, so the list call never
    returns the full array for every historical run)."""
    return {key: value for key, value in record.items() if key != "outcomes"}


@router.get("/topup/runs")
def get_topup_runs(store: TopupRunStore = Depends(get_topup_run_store)) -> dict:
    """``{"runs": [...meta-only...], "latest": <full record>|null, "integrity_errors": [...]}`` —
    an explicit HTTP 200 honest-empty payload (``{"runs": [], "latest": null,
    "integrity_errors": []}``) before any top-up run has ever reached its terminal state, never a
    404 (the ``GET /research/desk/universe`` convention). ``latest`` is the most recently STARTED
    run, verbatim from disk — never recomputed on the GET (the ``GET /research/desk/screen``
    convention: a plain read, triggers nothing). ``integrity_errors`` is ``store.list()``'s own
    ``errors`` return, surfaced verbatim (goal-desk-iter-16, J-12) — the identical key/shape
    ``get_screen``/``get_universe`` already use; a corrupted run-record file stays excluded from
    ``runs``/``latest`` either way, this only stops silently dropping the store's own honesty
    channel."""
    records, errors = store.list()
    return {
        "runs": [_topup_run_meta_only(r) for r in records],
        "latest": records[-1] if records else None,
        "integrity_errors": errors,
    }


# --- The screen (J-03) — GET (latest / ?date= / meta-only list) plus the screen compute's three
# subpaths, mirroring the top-up trio above exactly. ------------------------------------------------


def get_screen_store() -> ScreenStore:
    """The screen store rooted at a bare env-var-or-sibling-of-the-universe-dir default (zero new
    ``Config`` field — see ``desk_screen.resolve_desk_screen_dir``) — the ``get_universe_store``
    pattern. A FastAPI dependency so tests can point it at a temp dir via the env var or override
    it outright."""
    return ScreenStore(resolve_desk_screen_dir(CONFIG.desk_universe_dir_resolved()))


def get_screen_run_store() -> ScreenRunStore:
    """goal-desk-iter-29 (J-18): the durable screen-run log store rooted at a bare
    env-var-or-sibling-of-the-universe-dir default (zero new ``Config`` field — see
    ``desk_screen_log.resolve_desk_screen_log_dir``) — the ``get_topup_run_store``/
    ``get_reconcile_run_store`` pattern. A FastAPI dependency so tests can point it at a temp dir
    via the env var or override it outright."""
    return ScreenRunStore(resolve_desk_screen_log_dir(CONFIG.desk_universe_dir_resolved()))


def _screen_meta_only(record: dict) -> dict:
    """The lightweight projection ``GET /research/desk/screen``'s bulk list serves — id/pins/
    counts only, NEVER the full ``rows``/``skipped`` arrays (see ``desk_screen.py``'s module
    docstring: a screen snapshot is materially larger than a universe snapshot, so returning full
    content for every historical snapshot in one list call risks the era-5C latency mistake)."""
    return {
        "id": record["id"],
        "screen_date": record["screen_date"],
        "as_of": record["as_of"],
        "universe_snapshot_id": record["universe_snapshot_id"],
        "config_fingerprint": record["config_fingerprint"],
        "bar_store_signature": record["bar_store_signature"],
        "created_utc": record["created_utc"],
        "counts": {"rows": len(record["rows"]), "skipped": len(record["skipped"])},
    }


@router.get("/screen")
def get_screen(
    date: str | None = None, id: str | None = None, store: ScreenStore = Depends(get_screen_store)
) -> dict:
    """Three shapes, selected by ``?date=``/``?id=`` (Data Contract addition #1, extended
    goal-desk-iter-16 J-12):

      * neither given: ``{"screens": [...meta-only...], "latest": <full snapshot>|null,
        "integrity_errors": [...]}`` — an explicit HTTP 200 honest-empty payload
        (``{"screens": [], "latest": null, "integrity_errors": []}``) before any screen has ever
        been computed, never a 404 (the ``GET /research/desk/universe`` convention).
      * ``date=YYYY-MM-DD`` (``id`` absent): ``{"screen": <the exact persisted snapshot for the
        latest recording on that date, verbatim>|null}`` — a plain read, NEVER recomputed on the
        GET (TC-6). Byte-unchanged by this iteration.
      * ``id=<snapshot id>`` (``date`` absent): ``{"screen": <that exact persisted snapshot,
        verbatim>|null}`` — the only way to reach an EARLIER same-``screen_date`` recording once a
        later one exists (``?date=`` always resolves to the newest match); an unknown ``id`` is an
        honest ``null`` at HTTP 200, never a 404 (the ``?date=`` convention, mirrored).
      * ``id`` and ``date`` both given: an honest 4xx refusal — never a silent precedence rule."""
    if id is not None and date is not None:
        raise HTTPException(
            status_code=422, detail="only one of `id` or `date` may be supplied, not both"
        )
    records, errors = store.list()
    if id is not None:
        found = next((r for r in records if r["id"] == id), None)
        return {"screen": found}
    if date is not None:
        matching = [r for r in records if r["screen_date"] == date]
        return {"screen": matching[-1] if matching else None}
    return {
        "screens": [_screen_meta_only(r) for r in records],
        "latest": records[-1] if records else None,
        "integrity_errors": errors,
    }


@router.get("/screen/compare")
def get_screen_compare(
    id: str, base: str | None = None, store: ScreenStore = Depends(get_screen_store)
) -> dict:
    """goal-desk-iter-35 (J-20): how the snapshot named by ``id`` differs from the snapshot recorded
    immediately before it (or from ``base``, when given) — Data Contract addition, see
    ``desk_screen_diff.py``'s module docstring for the full computation. A plain read over
    ``store.list()`` only: this route takes NO ``BarStore``/``bar_index``/``DatasetStore``
    dependency, so it is structurally incapable of triggering a ``compute_tradability`` call or any
    other recompute (TC-9). ``id == base`` is refused as an honest 422 (``ScreenDiffSelfCompareError``
    — "a snapshot compared with itself", never a silent zero-diff no-op); an unresolved ``id`` is an
    honest ``{"compare": null, ...}`` at HTTP 200, mirroring ``GET /research/desk/screen?id=``'s own
    unknown-id convention (never a 404)."""
    try:
        return compute_screen_diff(store, id, base)
    except ScreenDiffSelfCompareError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/screen/pins")
def get_desk_screen_pins(
    screen_date: str,
    universe_store: UniverseStore = Depends(get_universe_store),
    bar_index: BarIndex = Depends(get_bar_index),
    screen_store: ScreenStore = Depends(get_screen_store),
) -> dict:
    """goal-desk-iter-36 (J-21): the five pins a screen run for ``screen_date`` would resolve RIGHT
    NOW, and whether a screen is already recorded under them — see ``desk_screen_pins.py``'s module
    docstring. ``screen_date`` is a REQUIRED query param (FastAPI 422s a missing one — mirrors
    ``ScreenComputeRequest.screen_date``'s own required convention; this endpoint never defaults to
    the current wall-clock date, T-6). A plain read: writes nothing, triggers nothing, recomputes
    nothing — this route takes no ``BarStore``/``DatasetStore``/compute-manager dependency at all,
    so it is structurally incapable of a ``compute_tradability`` call or a ``BarStore`` read. An
    honest empty payload at HTTP 200 before any universe snapshot is registered (never a 4xx/5xx —
    mirrors ``get_universe``/``get_coverage``'s own honest-empty convention)."""
    return resolve_desk_screen_pins(screen_date, universe_store, bar_index, CONFIG, screen_store)


class ScreenComputeRequest(BaseModel):
    """Body for ``POST /research/desk/screen/compute`` — ``screen_date`` is REQUIRED (FastAPI 422s
    a missing/absent body before the route handler runs, TC-9); this endpoint never defaults to
    the current wall-clock date (T-6)."""

    screen_date: str


def get_desk_screen_compute_manager() -> DeskScreenComputeManager:
    """The desk screen compute manager — a FastAPI dependency (the ``get_desk_topup_manager``
    pattern) so a test overrides it outright via ``app.dependency_overrides`` for complete
    test-to-test isolation. The default resolves the process-wide singleton constructed at module
    import time."""
    return _desk_screen_compute_manager


@router.post("/screen/compute")
def trigger_desk_screen_compute(
    body: ScreenComputeRequest,
    universe_store: UniverseStore = Depends(get_universe_store),
    bar_store: BarStore = Depends(get_bar_store),
    bar_index: BarIndex = Depends(get_bar_index),
    dataset_store: DatasetStore = Depends(get_dataset_store),
    screen_store: ScreenStore = Depends(get_screen_store),
    manager: DeskScreenComputeManager = Depends(get_desk_screen_compute_manager),
    screen_run_store: ScreenRunStore = Depends(get_screen_run_store),
) -> dict:
    """Start the single-flight desk screen compute job for ``body.screen_date``, or — if one is
    already running — return it UNCHANGED (``started: False``, never a second concurrent job).
    Returns ``{"started": bool, "compute": <snapshot>}``; the actual walk runs on a background
    worker thread, off this request, so this route returns immediately.

    Refuses — 422, naming the missing universe, never starting a job or persisting anything — when
    no universe snapshot is registered yet (mirrors the top-up CLI's own no-universe message,
    ``desk_topup_compute.py:352-356``; closes audit B4: a screen run with no universe would
    otherwise persist a permanent, useless honest-empty snapshot every time it's re-triggered).

    ``UniverseStore.list()`` also reports ``records == []`` when snapshot FILES exist but every one
    of them failed its integrity check, so the refusal names that cause separately rather than
    telling the operator nothing is registered when something is (era-desk-iter-4 audit B2): the
    action a damaged snapshot needs (look at the named file) is not the action an absent one needs
    (fetch a universe).

    goal-desk-iter-29 (J-18): ``screen_run_store`` is threaded straight through to
    ``manager.trigger`` so this run's terminal outcome (done/cancelled/failed/reused) is durably
    logged — this route only threads the dependency through; the pre-check/reuse-short-circuit and
    the actual record write both live inside ``run_screen_and_record``."""
    records, errors = universe_store.list()
    if not records:
        if errors:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"no READABLE universe snapshot is registered -- nothing to screen: "
                    f"{len(errors)} snapshot file(s) failed their integrity check and are excluded "
                    "(" + "; ".join(f"{e['file']}: {e['error']}" for e in errors) + ")"
                ),
            )
        raise HTTPException(
            status_code=422,
            detail="no universe snapshot is registered -- nothing to screen (run "
            "POST /research/desk/universe/fetch first)",
        )
    return manager.trigger(
        body.screen_date, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store,
        screen_run_store=screen_run_store,
    )


@router.get("/screen/compute")
def get_desk_screen_compute(
    manager: DeskScreenComputeManager = Depends(get_desk_screen_compute_manager),
) -> dict | None:
    """The screen compute job's current/last snapshot, served VERBATIM — or ``null`` if no screen
    compute has ever run this process. A plain read: never triggers a compute as a side effect
    (GET-never-computes)."""
    return manager.snapshot()


@router.post("/screen/compute/cancel")
def cancel_desk_screen_compute(
    manager: DeskScreenComputeManager = Depends(get_desk_screen_compute_manager),
) -> dict:
    """Cancel the in-flight desk screen compute (cooperative — observed between members). ``409``
    when idle (no job has ever run, or the last job already reached a terminal state) — mirrors
    ``cancel_desk_topup_compute``'s own 409-when-terminal shape."""
    snapshot = manager.snapshot()
    if snapshot is None or snapshot["state"] != "running":
        raise HTTPException(status_code=409, detail="no desk screen compute is currently running")
    manager.cancel()
    return {"cancelling": True}


# --- The screen run log (goal-desk-iter-29, J-18) — ONE read: a lightweight run-meta list + the
# latest full record. No POST here: the log is written internally by `run_screen_and_record` (the
# single shared writer, `desk_screen_log.record_screen_run`) — this route is a pure read, mirroring
# `GET /research/desk/topup/runs`'s exact honest-empty/meta-only-list/full-latest/
# `integrity_errors` shape. -------------------------------------------------------------------------


def _screen_run_meta_only(record: dict) -> dict:
    """The lightweight projection ``GET /research/desk/screen/runs``'s bulk list serves — every
    field EXCEPT ``ranked_count``/``skipped_by_reason``/``error``/``failed_member`` (mirrors
    ``_topup_run_meta_only``'s identical convention)."""
    heavy_keys = ("ranked_count", "skipped_by_reason", "error", "failed_member")
    return {key: value for key, value in record.items() if key not in heavy_keys}


@router.get("/screen/runs")
def get_screen_runs(store: ScreenRunStore = Depends(get_screen_run_store)) -> dict:
    """``{"runs": [...meta-only...], "latest": <full record>|null, "integrity_errors": [...]}`` —
    an explicit HTTP 200 honest-empty payload (``{"runs": [], "latest": null,
    "integrity_errors": []}``) before any screen run has ever reached its terminal state, never a
    404 (the ``GET /research/desk/topup/runs`` convention). ``latest`` is the most recently STARTED
    run, verbatim from disk — never recomputed on the GET. ``integrity_errors`` is ``store.list()``'s
    own ``errors`` return, surfaced verbatim (the J-12 convention) — a corrupted run-record file
    stays excluded from ``runs``/``latest`` either way, never fabricated, never crashes this
    route."""
    records, errors = store.list()
    return {
        "runs": [_screen_run_meta_only(r) for r in records],
        "latest": records[-1] if records else None,
        "integrity_errors": errors,
    }


# --- Coverage-index reconciliation (J-10, goal-desk-iter-14) — a trigger/poll/cancel trio mirroring
# the top-up compute trio exactly, plus ONE durable read mirroring ``GET /research/desk/topup/runs``.
# See ``desk_index_reconcile.py`` for the classify/repair/record mechanics this only wires up. -------


def get_reconcile_run_store() -> ReconcileRunStore:
    """The reconciliation run log store rooted at a bare env-var-or-sibling-of-the-universe-dir
    default (zero new ``Config`` field — see ``desk_index_reconcile.resolve_desk_index_reconcile_dir``)
    — the ``get_topup_run_store`` pattern. A FastAPI dependency so tests can point it at a temp dir
    via the env var or override it outright."""
    return ReconcileRunStore(resolve_desk_index_reconcile_dir(CONFIG.desk_universe_dir_resolved()))


def get_desk_reconcile_manager() -> DeskIndexReconcileComputeManager:
    """The desk coverage-index reconciliation compute manager — a FastAPI dependency (the
    ``get_desk_topup_manager`` pattern) so a test overrides it outright via
    ``app.dependency_overrides`` for complete test-to-test isolation. The default resolves the
    process-wide singleton constructed at module import time."""
    return _desk_index_reconcile_manager


@router.post("/coverage/reconcile/compute")
def trigger_desk_index_reconcile_compute(
    bar_store: BarStore = Depends(get_bar_store),
    bar_index: BarIndex = Depends(get_bar_index),
    manager: DeskIndexReconcileComputeManager = Depends(get_desk_reconcile_manager),
    reconcile_run_store: ReconcileRunStore = Depends(get_reconcile_run_store),
) -> dict:
    """Start the single-flight coverage-index reconciliation job, or — if one is already running —
    return it UNCHANGED (``started: False``, never a second concurrent job). Returns
    ``{"started": bool, "compute": <snapshot>}``; the actual classify-repair-verify walk runs on a
    background worker thread, off this request, so this route returns immediately. The job's
    terminal outcome is durably recorded into ``reconcile_run_store`` once it resolves (inside
    ``DeskIndexReconcileComputeManager.trigger`` itself) — this route only threads the store
    dependency through. Needs no ``UniverseStore``/``ResearchRegistry`` — reconciliation never
    touches universe membership or the bar-fetch path."""
    return manager.trigger(bar_store, bar_index, reconcile_run_store)


@router.get("/coverage/reconcile/compute")
def get_desk_index_reconcile_compute(
    manager: DeskIndexReconcileComputeManager = Depends(get_desk_reconcile_manager),
) -> dict | None:
    """The reconciliation job's current/last snapshot, served VERBATIM — or ``null`` if no
    reconciliation has ever run this process. A plain read: never triggers a compute as a side
    effect (GET-never-computes)."""
    return manager.snapshot()


@router.post("/coverage/reconcile/compute/cancel")
def cancel_desk_index_reconcile_compute(
    manager: DeskIndexReconcileComputeManager = Depends(get_desk_reconcile_manager),
) -> dict:
    """Cancel the in-flight reconciliation (cooperative — observed once, before the repair phase
    starts). ``409`` when idle (no job has ever run, or the last job already reached a terminal
    state) — mirrors ``cancel_desk_topup_compute``'s own 409-when-terminal shape."""
    snapshot = manager.snapshot()
    if snapshot is None or snapshot["state"] != "running":
        raise HTTPException(
            status_code=409, detail="no desk index reconciliation compute is currently running"
        )
    manager.cancel()
    return {"cancelling": True}


def _reconcile_run_meta_only(record: dict) -> dict:
    """The lightweight projection ``GET /research/desk/coverage/reconcile/runs``'s bulk list serves
    — every field EXCEPT ``drift_before``/``drift_after``/``store_errors`` (mirrors
    ``_topup_run_meta_only``'s identical convention: a run record carrying full before/after drift
    detail is materially larger than its own summary, so the list call never returns the full detail
    for every historical run)."""
    heavy_keys = ("drift_before", "drift_after", "store_errors")
    return {key: value for key, value in record.items() if key not in heavy_keys}


@router.get("/coverage/reconcile/runs")
def get_desk_index_reconcile_runs(store: ReconcileRunStore = Depends(get_reconcile_run_store)) -> dict:
    """``{"runs": [...meta-only...], "latest": <full record>|null, "integrity_errors": [...]}`` —
    an explicit HTTP 200 honest-empty payload (``{"runs": [], "latest": null,
    "integrity_errors": []}``) before any reconciliation has ever reached its terminal state, never
    a 404 (the ``GET /research/desk/topup/runs`` convention). ``latest`` is the most recently
    STARTED run, verbatim from disk — never recomputed on the GET. A corrupted run-record file is
    excluded from ``runs``/``latest`` (never fabricated, never crashes this route) —
    ``ReconcileRunStore.list()``'s own ``errors`` return is now surfaced verbatim as
    ``integrity_errors`` (goal-desk-iter-16, J-12) — the identical key/shape ``get_screen``/
    ``get_universe``/``get_topup_runs`` already use, instead of being silently discarded."""
    records, errors = store.list()
    return {
        "runs": [_reconcile_run_meta_only(r) for r in records],
        "latest": records[-1] if records else None,
        "integrity_errors": errors,
    }
