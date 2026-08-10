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

import os
from datetime import date, datetime, timedelta, timezone
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..config import CONFIG
from .bar_index import BarIndex
from .bars import BarStore
from .datasets import DatasetStore
from .desk_coverage import get_desk_coverage
from .desk_deep_backfill import (
    DESK_DEEP_TIMEFRAMES,
    DeepBackfillRunStore,
    DeskDeepBackfillComputeManager,
    deep_window_ceiling,
    plan_deep_windows,
    resolve_desk_deep_backfill_log_dir,
)
from .desk_index_reconcile import (
    DeskIndexReconcileComputeManager,
    ReconcileRunStore,
    resolve_desk_index_reconcile_dir,
)
from .desk_forward import ForwardStore, resolve_desk_forward_dir
from .desk_forward_compute import DeskForwardComputeManager
from .desk_forward_log import ForwardRunStore, resolve_desk_forward_log_dir
from .desk_forward_pins import resolve_desk_forward_pins
from .desk_playbook import PlaybookStore, resolve_desk_playbook_dir
from .desk_playbook_compute import DeskPlaybookComputeManager
from .desk_playbook_log import PlaybookRunStore, resolve_desk_playbook_log_dir
from .desk_screen import ScreenStore, resolve_desk_screen_dir
from .desk_screen_compute import DeskScreenComputeManager
from .desk_screen_diff import ScreenDiffSelfCompareError, compute_screen_diff
from .desk_screen_log import ScreenRunStore, resolve_desk_screen_log_dir
from .desk_screen_pins import resolve_desk_screen_pins
from .desk_sessions import (
    is_known_non_session,
    recorded_session_dates,
    refuse_if_not_a_session,
    session_evidence,
)
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

# The desk forward-returns compute manager (forward-test era) — the SAME process-wide-singleton-
# behind-a-dependency shape as its three siblings above.
_desk_forward_compute_manager = DeskForwardComputeManager()

# The deep fine-bar backfill compute manager — the SAME shape as its four siblings above.
_desk_deep_backfill_manager = DeskDeepBackfillComputeManager()

# The desk playbook compute manager (Era B2, J-02) — the SAME process-wide-singleton-behind-a-
# dependency shape as its five siblings above.
_desk_playbook_compute_manager = DeskPlaybookComputeManager()


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
    return ScreenStore(
        resolve_desk_screen_dir(CONFIG.desk_universe_dir_resolved()),
        meta_cache_db_path=screen_meta_cache_db_path(),
    )


def screen_meta_cache_db_path() -> str:
    """The resolved durable screen meta-cache path — the ``bar_verify_cache_db_path`` resolver
    verbatim: the ``TAPEOLOGY_SCREEN_META_CACHE_DB`` env var if set, else a file co-located as a
    SIBLING of the screen directory (``.data/screen`` -> ``.data/screen_meta_cache.db``). A derived
    path, never a ``Config`` field, so ``config_fingerprint`` stays frozen — and hermetic for every
    existing test for free, since the default lands beside whatever screen dir a test points at."""
    override = os.environ.get("TAPEOLOGY_SCREEN_META_CACHE_DB")
    if override:
        return override
    screen_dir = resolve_desk_screen_dir(CONFIG.desk_universe_dir_resolved())
    return os.path.join(os.path.dirname(screen_dir), "screen_meta_cache.db")


def forward_meta_cache_db_path() -> str:
    """The forward store's own durable meta-cache path — ``screen_meta_cache_db_path``'s contract,
    a separate DB because the two store directories are independently relocatable
    (``.data/forward`` -> ``.data/forward_meta_cache.db``)."""
    override = os.environ.get("TAPEOLOGY_FORWARD_META_CACHE_DB")
    if override:
        return override
    forward_dir = resolve_desk_forward_dir(CONFIG.desk_universe_dir_resolved())
    return os.path.join(os.path.dirname(forward_dir), "forward_meta_cache.db")


def get_screen_run_store() -> ScreenRunStore:
    """goal-desk-iter-29 (J-18): the durable screen-run log store rooted at a bare
    env-var-or-sibling-of-the-universe-dir default (zero new ``Config`` field — see
    ``desk_screen_log.resolve_desk_screen_log_dir``) — the ``get_topup_run_store``/
    ``get_reconcile_run_store`` pattern. A FastAPI dependency so tests can point it at a temp dir
    via the env var or override it outright."""
    return ScreenRunStore(resolve_desk_screen_log_dir(CONFIG.desk_universe_dir_resolved()))


def get_forward_store() -> ForwardStore:
    """The forward store rooted at a bare env-var-or-sibling-of-the-universe-dir default (zero new
    ``Config`` field — see ``desk_forward.resolve_desk_forward_dir``) — the ``get_screen_store``
    pattern. A FastAPI dependency so tests can point it at a temp dir via the env var or override
    it outright.

    Declared HERE, above the screen routes rather than beside its own Forward-returns section
    below, for one mechanical reason: ``POST /research/desk/screen/compute`` now depends on it (a
    superseded snapshot's forward records go with it), and a ``Depends(...)`` default is evaluated
    at function-DEFINITION time — a dependency declared further down the module would be an
    unresolved name at import."""
    return ForwardStore(
        resolve_desk_forward_dir(CONFIG.desk_universe_dir_resolved()),
        meta_cache_db_path=forward_meta_cache_db_path(),
    )


def _screen_meta_only(record: dict) -> dict:
    """The lightweight projection ``GET /research/desk/screen``'s bulk list serves — id/pins/
    counts only, NEVER the full ``rows``/``skipped`` arrays (see ``desk_screen.py``'s module
    docstring: a screen snapshot is materially larger than a universe snapshot, so returning full
    content for every historical snapshot in one list call risks the era-5C latency mistake).

    Takes a META projection (``ScreenStore.list_meta``), whose ``counts`` are the ``len()``s of the
    very ``rows``/``skipped`` lists this projection exists to leave behind — so the served body is
    unchanged while the arrays are never materialised for the list at all."""
    return {
        "id": record["id"],
        "screen_date": record["screen_date"],
        "as_of": record["as_of"],
        "universe_snapshot_id": record["universe_snapshot_id"],
        "config_fingerprint": record["config_fingerprint"],
        "bar_store_signature": record["bar_store_signature"],
        "created_utc": record["created_utc"],
        "counts": {
            "rows": record["counts"]["rows"],
            "skipped": record["counts"]["skipped"],
        },
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
    # Both keyed shapes read only the files they serve (`ScreenStore.get`/`find_by_date`), never the
    # whole store: this route is hit once per history click, and re-verifying every recorded
    # snapshot to hand back one of them was the bulk of that click's ~14s.
    if id is not None:
        return {"screen": store.get(id)}
    if date is not None:
        return {"screen": store.find_by_date(date)}
    # The bulk list is a META read (`list_meta`): it serves counts and pins, never the `rows`/
    # `skipped` arrays, so it leaves them on disk and is backed by the durable stat-keyed cache.
    # `latest` is still read from ITS OWN file, freshly verified in full on every request — nothing
    # a caller receives as snapshot CONTENT ever comes from a remembered row.
    metas, errors = store.list_meta()
    # The latest SCREEN, not the latest RECORDING: ordered by `screen_date` first, `created_utc`
    # only as the tie-break. Recording order alone meant that re-running an OLD date made that old
    # date the desk's default view — 2026-07-27 outranking a recorded 2026-08-04 purely because it
    # was walked more recently. That was always latent, but one snapshot per date turns "re-run an
    # incomplete older date" from a rarity into the routine act the refresh flow is built around
    # (`desk_screen_decision`), so the wrong reading now surfaces constantly. The tie-break keeps
    # two same-date copies (pre-cleanup, or a crash-interrupted supersede) resolving to the newer
    # recording exactly as before. The walk down the ranking is for the one race the meta read
    # opens: a file listed a moment ago can be gone (a cleanup) by the time it is opened, and the
    # honest answer is then the next-latest screen, not a null.
    latest = None
    for meta in sorted(
        metas, key=lambda r: (r["screen_date"], r.get("created_utc", ""), r["id"]), reverse=True
    ):
        latest = store.get(meta["id"])
        if latest is not None:
            break
    return {
        "screens": [_screen_meta_only(r) for r in metas],
        "latest": latest,
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


@router.get("/sessions")
def get_desk_sessions(
    from_day: str | None = None,
    to_day: str | None = None,
    universe_store: UniverseStore = Depends(get_universe_store),
    bar_store: BarStore = Depends(get_bar_store),
) -> dict:
    """Which dates in ``[from_day, to_day]`` are RECORDED trading sessions — the one owner of that
    question (``desk_sessions.py``), derived from recorded daily bars rather than any hardcoded
    calendar. Both query params are optional; omitting them serves the anchors' whole recorded
    span.

    Serves ``{"sessions": [...], "non_sessions": [...], "evidence": {...}}``, where
    ``non_sessions`` lists only the dates in range that are PROVABLY not sessions (inside the
    evidence bounds and absent from the set) — a date after the last recorded daily bar appears in
    neither list, because daily bars cannot prove anything about a session that has not been
    recorded yet.

    ``evidence.anchor_symbols == []`` is the honest-unknown state: no member holds a daily series,
    so both lists come back empty and every caller falls back to the behaviour it had before this
    route existed (fail open). A plain read: writes nothing, triggers nothing, recomputes nothing,
    and never reads the wall clock."""
    universe_records, _errors = universe_store.list()
    members = list(universe_records[-1]["members"]) if universe_records else []
    evidence = session_evidence(bar_store, members)
    sessions = recorded_session_dates(bar_store, members)

    in_range = sorted(
        day
        for day in sessions
        if (from_day is None or day >= from_day) and (to_day is None or day <= to_day)
    )
    non_sessions: list[str] = []
    if from_day is not None and to_day is not None:
        cursor = date.fromisoformat(from_day)
        last = date.fromisoformat(to_day)
        while cursor <= last:
            day = cursor.isoformat()
            if is_known_non_session(day, sessions, evidence):
                non_sessions.append(day)
            cursor += timedelta(days=1)

    return {"sessions": in_range, "non_sessions": non_sessions, "evidence": evidence}


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
    forward_store: ForwardStore = Depends(get_forward_store),
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

    Refuses a SECOND way — 422, again before any job starts — when ``screen_date`` is provably not
    a trading session (``desk_sessions.refuse_if_not_a_session``: the daily bars on file bracket
    the date and record nothing on it). This is the same defect class as the no-universe refusal:
    a screen for a Saturday, a market holiday or a date that has not happened yet is permanent,
    useless and structurally unmeasurable — ~280 of the 939 snapshots on disk on 2026-08-08 were
    exactly that. It fails OPEN by construction: with no daily bars recorded, nothing is refused
    and the route behaves exactly as it did before. The CLI carries the identical guard, so the
    terminal is not a way around it.

    goal-desk-iter-29 (J-18): ``screen_run_store`` is threaded straight through to
    ``manager.trigger`` so this run's terminal outcome (done/cancelled/failed/reused) is durably
    logged — this route only threads the dependency through; the pre-check/reuse-short-circuit and
    the actual record write both live inside ``run_screen_and_record``. ``forward_store`` is
    threaded through for the same reason: superseding a snapshot (one per date) drops the forward
    records measured against it, and the store that owns them is resolved here, not in there."""
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
    refusal = refuse_if_not_a_session(
        body.screen_date, bar_store, list(records[-1]["members"])
    )
    if refusal is not None:
        raise HTTPException(status_code=422, detail=refusal)
    return manager.trigger(
        body.screen_date, universe_store, bar_store, bar_index, dataset_store, CONFIG, screen_store,
        screen_run_store=screen_run_store, forward_store=forward_store,
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


# --- Forward returns (forward-test era) — the append-only, touch-anchored measurement of what
# recorded intraday price did at each ranked row's own wall DURING THE SCREEN DATE'S OWN SESSION
# (the map's basis reads sessions strictly before that date — ``tradability._resolve_basis`` — so
# that session is out-of-sample by construction): per-row, per-touch horizon returns + long/short
# max drawdowns through that same session's close. One read (latest-overall list / ?screen_id=
# newest + versions) plus the standard trigger/poll/cancel compute trio. See ``desk_forward.py``
# for the computation itself. ---------------------------------------------------------------------


def get_desk_forward_compute_manager() -> DeskForwardComputeManager:
    """The desk forward compute manager — a FastAPI dependency (the
    ``get_desk_screen_compute_manager`` pattern) so a test overrides it outright via
    ``app.dependency_overrides`` for complete test-to-test isolation."""
    return _desk_forward_compute_manager


def get_forward_run_store() -> ForwardRunStore:
    """The durable forward-run log store rooted at a bare env-var-or-sibling-of-the-universe-dir
    default (zero new ``Config`` field — see ``desk_forward_log.resolve_desk_forward_log_dir``) —
    the ``get_screen_run_store`` pattern. A FastAPI dependency so tests can point it at a temp dir
    via the env var or override it outright."""
    return ForwardRunStore(resolve_desk_forward_log_dir(CONFIG.desk_universe_dir_resolved()))


def _forward_meta_only(record: dict) -> dict:
    """The lightweight projection ``GET /research/desk/forward``'s bulk list serves — id/pins/
    parameters/counts only, NEVER the full ``rows``/``summary`` payloads (the
    ``_screen_meta_only`` convention: a forward record carries ~101 rows of nested per-touch
    dicts)."""
    return {
        "id": record["id"],
        "screen_id": record["screen_id"],
        "screen_date": record["screen_date"],
        "as_of": record["as_of"],
        "config_fingerprint": record["config_fingerprint"],
        "forward_input_signature": record["forward_input_signature"],
        "payload_version": record["payload_version"],
        "parameters": record["parameters"],
        "created_utc": record["created_utc"],
        "counts": {
            "rows": record["counts"]["rows"],
            "rows_with_touches": record["rows_with_touches"],
            "total_touches": record["total_touches"],
        },
    }


@router.get("/forward")
def get_forward(
    screen_id: str | None = None, store: ForwardStore = Depends(get_forward_store)
) -> dict:
    """Two shapes, selected by ``?screen_id=`` (the ``GET /research/desk/screen`` convention):

      * absent: ``{"forwards": [...meta-only...], "latest": <full newest record>|null,
        "integrity_errors": [...]}`` — an explicit HTTP 200 honest-empty payload before any
        forward record has ever been computed, never a 404.
      * ``screen_id=``: ``{"forward": <that screen's NEWEST full record>|null, "versions": <how
        many records that screen has ever accumulated>}`` — new bars arriving move the input
        signature, so a re-compute records a new version and every older one is kept; an unknown
        ``screen_id`` is an honest ``null``/``0`` at HTTP 200, never a 404.

    A plain read: writes nothing, triggers nothing, recomputes nothing (GET-never-computes)."""
    if screen_id is not None:
        newest, versions = store.newest_for_screen(screen_id)
        return {"forward": newest, "versions": versions}
    # `list_meta`, for `GET /screen`'s reasons verbatim. `latest` here is the newest RECORDING
    # (`records[-1]`, i.e. `(created_utc, id)` order) rather than the screen route's date-first
    # ordering — a deliberate difference, kept: a forward record is an ATTEMPT, and the latest one
    # is the one most recently made. It is still read from its own file and verified in full.
    metas, errors = store.list_meta()
    latest = None
    for meta in reversed(metas):
        latest = store.get(meta["id"])
        if latest is not None:
            break
    return {
        "forwards": [_forward_meta_only(r) for r in metas],
        "latest": latest,
        "integrity_errors": errors,
    }


class ForwardComputeRequest(BaseModel):
    """Body for ``POST /research/desk/forward/compute`` — ``screen_id`` is REQUIRED (FastAPI 422s
    a missing/absent body before the route handler runs); this endpoint never defaults to the
    latest screen."""

    screen_id: str


@router.post("/forward/compute")
def trigger_desk_forward_compute(
    body: ForwardComputeRequest,
    screen_store: ScreenStore = Depends(get_screen_store),
    bar_store: BarStore = Depends(get_bar_store),
    forward_store: ForwardStore = Depends(get_forward_store),
    forward_run_store: ForwardRunStore = Depends(get_forward_run_store),
    manager: DeskForwardComputeManager = Depends(get_desk_forward_compute_manager),
) -> dict:
    """Start the single-flight desk forward compute job for ``body.screen_id``, or — if one is
    already running — return it UNCHANGED (``started: False``, never a second concurrent job).
    Returns ``{"started": bool, "compute": <snapshot>}``; the walk runs on a background worker
    thread, off this request, so this route returns immediately.

    Refuses — 422, naming the unknown snapshot, never starting a job — when ``screen_id`` matches
    no recorded screen (the ``trigger_desk_screen_compute`` no-universe refusal precedent: a
    forward run over a nonexistent screen would fail anyway; refusing up front names the cause).
    A screen store whose FILES all failed their integrity check is named separately, mirroring
    that precedent's own two-cause honesty."""
    # The refusal's two-cause message needs the store's integrity errors, so it still walks -- but
    # only when the id did NOT resolve. A trigger for a real snapshot (the only case that starts a
    # job) now costs one file read; the walk is paid for exclusively by the branch that reports it.
    if screen_store.get(body.screen_id) is None:
        records, errors = screen_store.list()
        if errors and not records:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"no READABLE screen snapshot is registered -- nothing to measure forward: "
                    f"{len(errors)} snapshot file(s) failed their integrity check and are excluded "
                    "(" + "; ".join(f"{e['file']}: {e['error']}" for e in errors) + ")"
                ),
            )
        raise HTTPException(
            status_code=422,
            detail=f"no recorded screen snapshot has id '{body.screen_id}' -- nothing to measure "
            "forward from",
        )
    return manager.trigger(
        body.screen_id, screen_store, bar_store, CONFIG, forward_store, forward_run_store
    )


@router.get("/forward/compute")
def get_desk_forward_compute(
    manager: DeskForwardComputeManager = Depends(get_desk_forward_compute_manager),
) -> dict | None:
    """The forward compute job's current/last snapshot, served VERBATIM — or ``null`` if no
    forward compute has ever run this process. A plain read: never triggers a compute as a side
    effect (GET-never-computes)."""
    return manager.snapshot()


@router.post("/forward/compute/cancel")
def cancel_desk_forward_compute(
    manager: DeskForwardComputeManager = Depends(get_desk_forward_compute_manager),
) -> dict:
    """Cancel the in-flight desk forward compute (cooperative — observed between rows). ``409``
    when idle — mirrors ``cancel_desk_screen_compute``'s own 409-when-terminal shape."""
    snapshot = manager.snapshot()
    if snapshot is None or snapshot["state"] != "running":
        raise HTTPException(status_code=409, detail="no desk forward compute is currently running")
    manager.cancel()
    return {"cancelling": True}


@router.get("/forward/runs")
def get_forward_runs(
    screen_id: str | None = None, store: ForwardRunStore = Depends(get_forward_run_store)
) -> dict:
    """``{"runs": [...], "latest": <record>|null, "integrity_errors": [...]}`` — the durable log of
    what every forward measurement attempted, surviving the compute manager's process-scoped
    snapshot (see ``desk_forward_log.py``). ``?screen_id=`` narrows to one snapshot's own runs (the
    ``GET /research/desk/forward`` convention), and then ``latest`` is that snapshot's newest run
    rather than the store's.

    An explicit HTTP 200 honest-empty payload before any forward run has ever reached its terminal
    state, never a 404 (the ``GET /research/desk/screen/runs`` convention). ``latest`` is the most
    recently STARTED run, verbatim from disk — never recomputed on the GET. ``integrity_errors`` is
    ``store.list()``'s own ``errors`` return, surfaced verbatim — a corrupted run-record file stays
    excluded from ``runs``/``latest`` either way, never fabricated, never crashes this route.

    An absent row here and an absent forward record together mean the measurement never ran; an
    absent forward record BESIDE a ``done`` row means it ran and found nothing to measure. Telling
    those two apart is the reason this endpoint exists."""
    records, errors = store.list()
    if screen_id is not None:
        records = [record for record in records if record.get("screen_id") == screen_id]
    return {
        "runs": records,
        "latest": records[-1] if records else None,
        "integrity_errors": errors,
    }


@router.get("/forward/pins")
def get_desk_forward_pins(
    screen_id: str,
    screen_store: ScreenStore = Depends(get_screen_store),
    bar_index: BarIndex = Depends(get_bar_index),
    forward_store: ForwardStore = Depends(get_forward_store),
    bar_store: BarStore = Depends(get_bar_store),
) -> dict:
    """How much of the snapshot named by ``screen_id`` a forward measurement could POSSIBLY reach
    right now — how many of its ranked members hold a recorded 1m/5m series whose window covers the
    screen date's own session — plus where that screen date sits relative to the daily bars on file
    (``session.state``) and whether a measurement is already recorded. See
    ``desk_forward_pins.py``'s module docstring; ``members_with_fine_series`` is an explicit UPPER
    bound, never a prediction of what a run would measure.

    ``screen_id`` is a REQUIRED query param (FastAPI 422s a missing one — the
    ``ForwardComputeRequest.screen_id`` convention; this endpoint never defaults to the latest
    screen). A plain read: writes nothing, triggers nothing, recomputes nothing — the ``BarStore``
    dependency reaches exactly one accessor (``merged_bars(symbol, "1d")``, over a bounded handful
    of anchor members) and no compute manager, so this route remains structurally incapable of a
    walk. An unresolved ``screen_id`` is an honest all-zero body at HTTP 200, never a 404."""
    return resolve_desk_forward_pins(
        screen_id, screen_store, bar_index, forward_store, bar_store=bar_store
    )


# --- The Playbook (Era B2) — pre-registered, lookahead-clean intraday setups detected on the
# desk's own recorded 5m/1m bars (docs/playbook-detector-spec.md). J-01 shipped detection only (no
# measurement, no compute-manager/trigger route, no CLI) plus the ONE read below; see
# desk_playbook.py for the computation, store, and parameters/signature recipe this route only
# serves verbatim. J-02 (this iteration) extends `compute_playbook` to MEASURE every signal in the
# same walk (see desk_playbook.py's own docstring) and adds the compute trigger/poll/cancel trio +
# the durable run ledger, below the GET route — mirrors the forward-returns trio exactly; see
# desk_playbook_compute.py / desk_playbook_log.py. ---------------------------------------------------


def get_playbook_store() -> PlaybookStore:
    """The playbook store rooted at a bare env-var-or-sibling-of-the-universe-dir default (zero new
    ``Config`` field — see ``desk_playbook.resolve_desk_playbook_dir``) — the ``get_forward_store``
    pattern. A FastAPI dependency so tests can point it at a temp dir via the env var or override
    it outright."""
    return PlaybookStore(resolve_desk_playbook_dir(CONFIG.desk_universe_dir_resolved()))


def _playbook_meta_only(record: dict) -> dict:
    """The lightweight projection the bulk list serves — id/pins/parameters/counts only, never the
    full ``signals``/``absences``/``diagnostics`` lists (the ``_forward_meta_only`` convention)."""
    return {
        "id": record["id"],
        "session_date": record["session_date"],
        "config_fingerprint": record["config_fingerprint"],
        "playbook_input_signature": record["playbook_input_signature"],
        "payload_version": record["payload_version"],
        "parameters": record["parameters"],
        "recorded_at": record["recorded_at"],
        "counts": {
            "signals": len(record["signals"]),
            "absences": len(record["absences"]),
            "diagnostics": len(record["diagnostics"]),
        },
    }


@router.get("/playbook")
def get_playbook(
    date: str | None = None, id: str | None = None, store: PlaybookStore = Depends(get_playbook_store)
) -> dict:
    """Three shapes, selected by ``?date=``/``?id=`` (the ``GET /research/desk/screen`` convention):

      * neither given: ``{"playbooks": [...meta-only...], "latest": <full record>|null,
        "integrity_errors": [...]}`` — an explicit HTTP 200 honest-empty payload
        (``{"playbooks": [], "latest": null, "integrity_errors": []}``) before any playbook has
        ever been computed, never a 404. ``latest`` is the most recently RECORDED playbook (a
        playbook, like a forward measurement and unlike a screen, is an ATTEMPT that can carry
        several versions per date as parameters change — ``desk_forward``'s ``latest`` convention,
        not ``desk_screen``'s date-first one).
      * ``date=YYYY-MM-DD`` (``id`` absent): ``{"playbook": <newest record for that date>|null,
        "versions": <how many records that date has ever accumulated>}`` — a plain read, never
        recomputed on the GET; an unknown date is an honest ``null``/``0`` at HTTP 200.
      * ``id=<record id>`` (``date`` absent): ``{"playbook": <that exact persisted record>|null}``
        — the only way to reach an EARLIER same-date recording once a later one exists (``?date=``
        always resolves to the newest match); an unknown id is an honest ``null``, never a 404.
      * ``id`` and ``date`` both given: an honest 4xx refusal — never a silent precedence rule.

    A plain read: writes nothing, triggers nothing, recomputes nothing (GET-never-computes) — this
    route takes no ``BarStore``/``UniverseStore``/compute-manager dependency at all, so it is
    structurally incapable of triggering ``compute_playbook``."""
    if id is not None and date is not None:
        raise HTTPException(
            status_code=422, detail="only one of `id` or `date` may be supplied, not both"
        )
    if id is not None:
        return {"playbook": store.get(id)}
    if date is not None:
        newest, versions = store.newest_for_date(date)
        return {"playbook": newest, "versions": versions}
    records, errors = store.list()
    return {
        "playbooks": [_playbook_meta_only(r) for r in records],
        "latest": records[-1] if records else None,
        "integrity_errors": errors,
    }


# --- The playbook compute (Era B2, J-02) — trigger/poll/cancel trio mirroring the forward-returns
# trio exactly, plus ONE durable read mirroring `GET /research/desk/forward/runs`. See
# `desk_playbook_compute.py` for the single-flight manager + `run_playbook_and_record` mechanics
# and `desk_playbook_log.py` for the run ledger this wires up. ---------------------------------------


def get_desk_playbook_compute_manager() -> DeskPlaybookComputeManager:
    """The desk playbook compute manager — a FastAPI dependency (the
    ``get_desk_forward_compute_manager`` pattern) so a test overrides it outright via
    ``app.dependency_overrides`` for complete test-to-test isolation."""
    return _desk_playbook_compute_manager


def get_playbook_run_store() -> PlaybookRunStore:
    """The durable playbook-run log store rooted at a bare env-var-or-sibling-of-the-universe-dir
    default (zero new ``Config`` field — see ``desk_playbook_log.resolve_desk_playbook_log_dir``) —
    the ``get_forward_run_store`` pattern. A FastAPI dependency so tests can point it at a temp dir
    via the env var or override it outright."""
    return PlaybookRunStore(resolve_desk_playbook_log_dir(CONFIG.desk_universe_dir_resolved()))


class PlaybookComputeRequest(BaseModel):
    """Body for ``POST /research/desk/playbook/compute`` — ``session_date`` is REQUIRED (FastAPI
    422s a missing/absent body before the route handler runs, the ``ForwardComputeRequest``/
    ``ScreenComputeRequest`` convention); this endpoint never defaults to the current wall-clock
    date (T-6) or to the latest recorded session."""

    session_date: str


@router.post("/playbook/compute")
def trigger_desk_playbook_compute(
    body: PlaybookComputeRequest,
    universe_store: UniverseStore = Depends(get_universe_store),
    bar_store: BarStore = Depends(get_bar_store),
    playbook_store: PlaybookStore = Depends(get_playbook_store),
    manager: DeskPlaybookComputeManager = Depends(get_desk_playbook_compute_manager),
    playbook_run_store: PlaybookRunStore = Depends(get_playbook_run_store),
) -> dict:
    """Start the single-flight desk playbook compute job for ``body.session_date``, or — if one is
    already ``status`` in (``"running"``, ``"cancelling"``) — return it UNCHANGED
    (``started: False``, never a second concurrent job). Returns
    ``{"started": bool, "compute": <snapshot>}``; the walk runs on a background worker thread, off
    this request, so this route returns immediately.

    Refuses — 422, naming the non-session date, never starting a job or writing a ledger row — when
    ``body.session_date`` is provably not a trading session (``desk_sessions.
    refuse_if_not_a_session`` — the ``trigger_desk_screen_compute`` precedent). This is a PRE-check:
    ``run_playbook_and_record`` carries the identical guard internally too (for the CLI path, which
    has no route in front of it, and for the race), but reaching it from this route would mean a
    job was already created and a "refused_non_session" ledger row already written for a date this
    route could have refused for free."""
    records, _errors = universe_store.list()
    members = list(records[-1]["members"]) if records else []
    refusal = refuse_if_not_a_session(body.session_date, bar_store, members)
    if refusal is not None:
        raise HTTPException(status_code=422, detail=refusal)
    return manager.trigger(
        body.session_date, universe_store, bar_store, CONFIG, playbook_store,
        playbook_run_store=playbook_run_store,
    )


@router.get("/playbook/compute")
def get_desk_playbook_compute(
    manager: DeskPlaybookComputeManager = Depends(get_desk_playbook_compute_manager),
) -> dict:
    """The playbook compute job's current/last snapshot, served VERBATIM —
    ``{"status", "session_date", "signals_done", "signals_total", "error"}``, ALWAYS a body (never
    ``null``: ``status == "idle"`` before any compute has ever run this process). A plain read:
    never triggers a compute as a side effect (GET-never-computes)."""
    return manager.snapshot()


@router.post("/playbook/compute/cancel")
def cancel_desk_playbook_compute(
    manager: DeskPlaybookComputeManager = Depends(get_desk_playbook_compute_manager),
) -> dict:
    """Cancel the in-flight desk playbook compute (cooperative — observed between members). ``409``
    when idle (no job has ever run, or the last job already reached a terminal state) — mirrors
    ``cancel_desk_forward_compute``'s own 409-when-terminal shape."""
    snapshot = manager.snapshot()
    if snapshot["status"] != "running":
        raise HTTPException(status_code=409, detail="no desk playbook compute is currently running")
    manager.cancel()
    return {"cancelling": True}


@router.get("/playbook/runs")
def get_playbook_runs(
    session_date: str | None = None, store: PlaybookRunStore = Depends(get_playbook_run_store)
) -> dict:
    """``{"runs": [...], "latest": <record>|null, "integrity_errors": [...]}`` — the durable log of
    what every playbook compute attempted, surviving the compute manager's process-scoped snapshot
    (see ``desk_playbook_log.py``). ``?session_date=`` narrows to one date's own runs (the
    ``GET /research/desk/forward/runs?screen_id=`` convention), and then ``latest`` is that date's
    newest run rather than the store's.

    An explicit HTTP 200 honest-empty payload before any playbook run has ever reached a LOGGED
    terminal state, never a 404. ``latest`` is the most recently STARTED run, verbatim from disk —
    never recomputed on the GET. ``integrity_errors`` is ``store.list()``'s own ``errors`` return,
    surfaced verbatim — a corrupted run-record file stays excluded from ``runs``/``latest`` either
    way, never fabricated, never crashes this route. A cancelled attempt never appears here at all
    (``desk_playbook_log.py``'s own terminal-excludes-cancelled contract) — its absence looks
    identical to a run that never happened, by design."""
    records, errors = store.list()
    if session_date is not None:
        records = [record for record in records if record.get("session_date") == session_date]
    return {
        "runs": records,
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


# --- The deep fine-bar backfill — a trigger/poll/cancel trio mirroring the top-up trio exactly,
# plus ONE durable read mirroring ``GET /research/desk/topup/runs``, plus a pre-click plan
# disclosure. See ``desk_deep_backfill.py`` for the window-clamp and chunking mechanics this only
# wires up. ------------------------------------------------------------------------------------


def get_desk_deep_backfill_manager() -> DeskDeepBackfillComputeManager:
    """The deep-backfill compute manager — a FastAPI dependency (the ``get_desk_topup_manager``
    pattern) so a test overrides it outright via ``app.dependency_overrides`` for complete
    test-to-test isolation."""
    return _desk_deep_backfill_manager


def get_deep_backfill_run_store() -> DeepBackfillRunStore:
    """The deep-backfill run log store rooted at a bare env-var-or-sibling-of-the-universe-dir
    default (zero new ``Config`` field) — the ``get_topup_run_store`` pattern."""
    return DeepBackfillRunStore(
        resolve_desk_deep_backfill_log_dir(CONFIG.desk_universe_dir_resolved())
    )


class DeepBackfillComputeRequest(BaseModel):
    """Body for ``POST /research/desk/backfill/compute``. Both dates are REQUIRED — this endpoint
    never defaults to a wall-clock-derived range, because a backfill's range is exactly the thing an
    operator is deciding. ``timeframes`` defaults to the touch ladder a forward measurement can
    actually read."""

    from_day: str
    to_day: str
    timeframes: list[str] | None = None


@router.get("/backfill/plan")
def get_desk_deep_backfill_plan(
    from_day: str,
    to_day: str,
    universe_store: UniverseStore = Depends(get_universe_store),
) -> dict:
    """What a backfill over ``[from_day, to_day]`` WOULD fetch, said before anything is clicked:
    how many chunks, over how many symbols, per timeframe, and the effective end each timeframe
    clamps to.

    The clamp is the load-bearing disclosure. Every window ends before the region the Yahoo top-up
    already covers (~30 days back for 1m, ~60 for 5m), because ``BarStore.merged_bars`` resolves a
    contested timestamp in favour of the most recently CREATED series — so an overlapping deep fetch
    would silently replace the recent tape's Yahoo prices with SIP ones, permanently. A caller
    asking for a range inside that region gets an honest zero-chunk plan rather than an overlap.

    A plain read: writes nothing, triggers nothing, issues no vendor call, and never reads a
    ``BarStore``."""
    records, _errors = universe_store.list()
    members = list(records[-1]["members"]) if records else []
    today = datetime.now(timezone.utc).date()
    chunks = plan_deep_windows(members, DESK_DEEP_TIMEFRAMES, from_day, to_day, today)
    per_timeframe = {
        timeframe: {
            "chunks": sum(1 for c in chunks if c["timeframe"] == timeframe),
            "clamped_end": deep_window_ceiling(timeframe, today),
        }
        for timeframe in DESK_DEEP_TIMEFRAMES
    }
    return {
        "requested_window": {"start": from_day, "end": to_day},
        "timeframes": list(DESK_DEEP_TIMEFRAMES),
        "members_total": len(members),
        "chunks_total": len(chunks),
        "per_timeframe": per_timeframe,
    }


@router.post("/backfill/compute")
def trigger_desk_deep_backfill_compute(
    body: DeepBackfillComputeRequest,
    universe_store: UniverseStore = Depends(get_universe_store),
    bar_store: BarStore = Depends(get_bar_store),
    bar_index: BarIndex = Depends(get_bar_index),
    registry: ResearchRegistry = Depends(get_registry),
    manager: DeskDeepBackfillComputeManager = Depends(get_desk_deep_backfill_manager),
    run_store: DeepBackfillRunStore = Depends(get_deep_backfill_run_store),
) -> dict:
    """Start the single-flight deep fine-bar backfill over the LATEST universe snapshot's members
    for ``[from_day, to_day]``, or — if one is already running — return it UNCHANGED
    (``started: False``, never a second concurrent job). Returns
    ``{"started": bool, "compute": <snapshot>}``; the walk runs on a background worker thread, so
    this route returns immediately however long the backfill takes.

    Refuses — 422, before starting anything — when no universe snapshot is registered (the
    ``trigger_desk_screen_compute`` precedent) or when ``timeframes`` names something outside the
    touch ladder this module backfills.

    This is an explicit, credentialed, expensive operator act: a full 1m+5m sweep back to 2025 is
    ~3,900 chunks and tens of millions of bars over hours of sequential vendor pagination. Cancel is
    real, and every chunk already recorded is answered store-first on the next run — so an
    interrupted sweep resumes rather than restarting."""
    records, errors = universe_store.list()
    if not records:
        if errors:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"no READABLE universe snapshot is registered -- nothing to backfill: "
                    f"{len(errors)} snapshot file(s) failed their integrity check and are excluded "
                    "(" + "; ".join(f"{e['file']}: {e['error']}" for e in errors) + ")"
                ),
            )
        raise HTTPException(
            status_code=422,
            detail="no universe snapshot is registered -- nothing to backfill (run "
            "POST /research/desk/universe/fetch first)",
        )
    timeframes = tuple(body.timeframes) if body.timeframes else DESK_DEEP_TIMEFRAMES
    unsupported = [t for t in timeframes if t not in DESK_DEEP_TIMEFRAMES]
    if unsupported:
        raise HTTPException(
            status_code=422,
            detail=(
                f"cannot deep-backfill {unsupported} -- this path serves only "
                f"{list(DESK_DEEP_TIMEFRAMES)}, the timeframes a forward measurement reads; the "
                "coarse timeframes already reach back years through the ordinary top-up"
            ),
        )
    return manager.trigger(
        universe_store, bar_store, bar_index, registry, run_store,
        from_day=body.from_day, to_day=body.to_day, timeframes=timeframes,
    )


@router.get("/backfill/compute")
def get_desk_deep_backfill_compute(
    manager: DeskDeepBackfillComputeManager = Depends(get_desk_deep_backfill_manager),
) -> dict | None:
    """The backfill job's current/last snapshot, served VERBATIM — or ``null`` if none has ever run
    this process. A plain read: never triggers a compute as a side effect (GET-never-computes)."""
    return manager.snapshot()


@router.post("/backfill/compute/cancel")
def cancel_desk_deep_backfill_compute(
    manager: DeskDeepBackfillComputeManager = Depends(get_desk_deep_backfill_manager),
) -> dict:
    """Cancel the in-flight backfill (cooperative — observed between chunks). ``409`` when idle,
    mirroring ``cancel_desk_topup_compute``. Chunks already in flight finish and are recorded: they
    have already paid for their vendor call."""
    snapshot = manager.snapshot()
    if snapshot is None or snapshot["state"] != "running":
        raise HTTPException(status_code=409, detail="no deep backfill is currently running")
    manager.cancel()
    return {"cancelling": True}


def _deep_backfill_run_meta_only(record: dict) -> dict:
    """The lightweight projection the bulk list serves — every field EXCEPT ``outcomes`` (mirrors
    ``_topup_run_meta_only``: a run over ~3,900 chunks carries a per-chunk list far larger than its
    own summary, so the list call never returns it for every historical run)."""
    return {key: value for key, value in record.items() if key != "outcomes"}


@router.get("/backfill/runs")
def get_desk_deep_backfill_runs(store: DeepBackfillRunStore = Depends(get_deep_backfill_run_store)) -> dict:
    """``{"runs": [...meta-only...], "latest": <full record>|null, "integrity_errors": [...]}`` —
    an explicit HTTP 200 honest-empty payload before any backfill has reached a terminal state,
    never a 404 (the ``GET /research/desk/topup/runs`` convention). ``latest`` is the most recently
    STARTED run, verbatim from disk — never recomputed on the GET."""
    records, errors = store.list()
    return {
        "runs": [_deep_backfill_run_meta_only(r) for r in records],
        "latest": records[-1] if records else None,
        "integrity_errors": errors,
    }
