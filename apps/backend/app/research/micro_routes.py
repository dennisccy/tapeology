"""``/research/desk/micro/*`` -- Era "The Rapid Microscope": J-01's readiness fold, J-02's three
snapshot routes, J-04's Scout routes, J-05's three walk-forward routes, J-06 step 2's recorder
routes, J-06 step 3's ONE read-only vault route, and J-07's ONE read-only graduation route. A
fresh router/file mounted separately in ``main.py``, mirroring ``referee_routes.py``'s own
precedent and rationale (that file's own docstring: "the SAME rationale desk_routes.py itself
gives for splitting off routes.py"). The era's own Data Contract table (``docs/goal.md``'s Product
Shape) named this exact route ("graduation states + export bundles") as landing in a later
iteration under this SAME ``/research/desk/micro`` prefix -- this file was always its right home.

``GET /graduation`` is GET-only this iteration, exactly like ``GET /vault`` above it -- J-07 is
keyless/automated (no operator compute act triggers graduation; a candidate's state is read back
from whatever ``micro_graduation.py``'s own evaluation functions have already recorded, called
directly -- by a test today, by a future J-08/J-09 wiring later), so it needs no compute manager
and no ``POST``/cancel sibling routes.

``GET /vault`` is GET-only this iteration -- no ``/vault/compute`` route and no CLI (the phase
spec's own OUT OF SCOPE: "no operator act in this iteration or the next calls registration
standalone; that lands with step 4"), so it needs no compute manager and no ``POST``/cancel
sibling routes, unlike the sections above it.

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

import json
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..config import CONFIG
from .bar_index import BarIndex
from .bars import BarStore
from .datasets import DatasetStore
from .desk_playbook import PlaybookStore
from .desk_playbook_context import BandMapResolver
from .desk_routes import get_playbook_store, get_universe_store
from .desk_universe import UniverseStore
from .foundry_compiler import sources_compiler_hermetic_fixture_view
from .foundry_freeze import freeze_integrity_hermetic_fixture_view, verify_commit_is_ancestor
from .foundry_hermetic_summary import build_hermetic_oracles_summary
from .foundry_interpreter import interpreter_hermetic_fixture_view
from .foundry_source_registry import (
    foundry_era_identity,
    read_era_open_baseline,
    resolve_foundry_dir,
)
from .micro_accessor import ExposureRegistry, resolve_micro_exposure_registry_dir
from .micro_graduation import EMPTY_LEDGER_MESSAGE, GraduationLedger, list_graduation_families, resolve_micro_graduation_dir
from .micro_readiness import (
    MicroBandTouchCache,
    MicroReadinessCache,
    build_readiness,
    resolve_micro_band_touch_cache_db_path,
    resolve_micro_readiness_cache_db_path,
)
from .micro_snapshots import (
    MicroSnapshotComputeManager,
    read_run_log,
    resolve_micro_snapshots_dir,
    snapshot_meta_report,
)
from .routes import get_bar_index, get_bar_store, get_dataset_store, get_registry, get_study_market_adapter
from .scout import (
    ScoutComputeManager,
    list_scout_families,
    _PILOT_GRID_SELECTORS,
)
from .scout_ledger import ScoutLedger, resolve_scout_ledger_dir
from .tick_recorder import (
    RecorderCheckpointStore,
    TickRecorderComputeManager,
    resolve_tick_recorder_checkpoint_dir,
    resolve_tick_recorder_log_dir,
)
from . import vault
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


def get_micro_band_touch_cache() -> MicroBandTouchCache:
    """iter-26: the durable per-``(dataset checksum, resolver.map_key(...))`` band-touch-count
    cache -- the SAME config-derived, env-overridable path shape as
    ``get_micro_readiness_cache`` above, under its own ``TAPEOLOGY_MICRO_BAND_TOUCH_CACHE_DB`` env
    var (never reusing that sibling's env var -- ``micro_readiness.py``'s own module docstring, the
    ``TAPEOLOGY_MICRO_*`` family). A FastAPI dependency so tests can override it outright or point
    it at a temp path via the env var -- the established pattern."""
    return MicroBandTouchCache(
        resolve_micro_band_touch_cache_db_path(CONFIG.dataset_dir_resolved())
    )


@router.get("/readiness")
def get_micro_readiness(
    dataset_store: DatasetStore = Depends(get_dataset_store),
    cache: MicroReadinessCache = Depends(get_micro_readiness_cache),
    band_touch_cache: MicroBandTouchCache = Depends(get_micro_band_touch_cache),
    playbook_store: PlaybookStore = Depends(get_playbook_store),
    bar_store: BarStore = Depends(get_bar_store),
) -> dict:
    """J-01's corpus-truth fold: the honest per-shard inventory, corpus totals beside the
    referee's tick-gate figure, and the three pilot studies' floor table -- see
    ``micro_readiness.build_readiness``'s own docstring for the full contract. Never 404/500 on
    an empty corpus (the desk router's established never-404-on-absence convention) -- an empty
    ``shards`` list (``study_floors`` still carries its 3 rows, each read against a 0-session
    corpus) at HTTP 200.

    J-03: ``playbook_store`` is the EXISTING ``desk_routes.get_playbook_store`` dependency,
    reused verbatim (never a second, redefined provider) -- it feeds the ``joinable_corpus``
    field, computed by ``micro_join.joinable_corpus_counts``.

    J-09: ``resolver`` is constructed HERE, per request, from the EXISTING ``routes.get_bar_store``
    dependency plus ``CONFIG`` -- the ``desk_routes.py`` ``GET .../playbook/{id}/context`` route's
    OWN construction call, verbatim (``BandMapResolver(bar_store, CONFIG)`` defaults to
    ``compute=False``, so this GET never computes a tradable map it does not already hold -- T-8).
    It materializes ``joinable_corpus.band_touch_count`` from the ``not_enumerated`` sentinel to a
    real int (``micro_join.py``'s own docstring); nothing else in this payload changes shape.

    iter-26: ``band_touch_cache`` is threaded straight through to ``build_readiness`` -- only the
    warm-path LATENCY of that materialization changes (the ~22s-and-growing uncached
    ``enumerate_band_touches`` walk over every joinable dataset's raw event stream); the served
    ``band_touch_count`` value is byte-identical either way."""
    resolver = BandMapResolver(bar_store, CONFIG)
    return build_readiness(
        dataset_store,
        cache,
        dataset_dir=CONFIG.dataset_dir_resolved(),
        playbook_store=playbook_store,
        resolver=resolver,
        band_touch_cache=band_touch_cache,
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
    empty list, the desk router's established convention.

    goal-rapid-microscope-iter-33 (J-12): grows to ``{"snapshots": [...], "withheld_excluded":
    int, "stale_excluded": int}`` -- existing ``snapshots`` key byte-identical, no second
    computation path, no new endpoint. Both disclosure counts are ``snapshot_meta_report``'s own
    (see that function's docstring): ``withheld_excluded`` is pool-derived, never a count of which
    withheld ids happen to have a meta file on disk; ``stale_excluded`` counts a present-but-no-
    longer-identity-matching meta file, never carrying the stale VALUE itself."""
    return snapshot_meta_report(snapshots_dir, dataset_store, CONFIG)


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
    default before any job has ever run this process).

    ``withheld_excluded`` (spec section 7.5 point 6, r4) is this run's own disclosure of how many
    Validation-Vault shards the build enumeration left out -- a COUNT only, never an id, and never
    silently omitted. ``0`` whenever the vault holds nothing withheld, which is every run today."""
    snap = manager.snapshot()
    return {
        "state": snap["state"],
        "progress": snap["progress"],
        "started_utc": snap["started_utc"],
        "finished_utc": snap["finished_utc"],
        "error": snap["error"],
        "withheld_excluded": snap["withheld_excluded"],
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


def get_micro_exposure_registry_dir() -> str:
    """The exposure registry's directory -- ``TAPEOLOGY_MICRO_EXPOSURE_REGISTRY_DIR`` if set, else
    a SIBLING of the config-owned dataset directory (``micro_accessor.resolve_micro_exposure_
    registry_dir`` -- see that function's own docstring). Shared by every J-05 caller that logs or
    reads exposure state, not owned exclusively by this route file."""
    return resolve_micro_exposure_registry_dir(CONFIG.dataset_dir_resolved())


class ScoutComputeRequest(BaseModel):
    """Body for ``POST /research/desk/micro/scout/compute`` (J-09, additive). ``grid`` defaults to
    ``None`` -- omitted (or the body omitted entirely, same as every pre-J-09 caller), this route's
    behavior stays byte-identical: the unchanged default reference grid. As of iteration 22, each of
    ``scout.GRID_SELECTOR_RANGE_WALL_PILOT`` / ``scout.GRID_SELECTOR_DELTA_DIVERGENCE_PILOT`` /
    ``scout.GRID_SELECTOR_CAPITULATION_PILOT`` runs ONLY its own ONE predeclared pilot candidate --
    never the 6-wide default grid, never more than one candidate per request."""

    grid: str | None = None


# grid_selector -> which of resolver/playbook_store this route must construct for it -- the SAME
# structure_context.kind split ``scout._PILOT_GRID_SELECTORS`` already encodes. iter-26: derived by
# FILTERING that one canonical table (never a second, independently-maintained selector->kind
# literal -- rail 6, single source of truth) so the route stays selector-aware rather than "any
# non-default selector gets a resolver", which stopped being true the moment a playbook_signal-kind
# selector existed.
def _pilot_selectors_by_kind(
    kind: str, source: "dict[str, tuple[str, str]] | None" = None
) -> frozenset[str]:
    """The selector set for one ``structure_context.kind``, filter-derived from ``source`` (default
    ``None`` -- the LIVE ``scout._PILOT_GRID_SELECTORS`` table, the real route path) each time it
    is called. Deliberately a function called at each use site, never a module-level literal
    computed once at import -- a frozen-at-import constant would only happen to equal today's
    values rather than genuinely tracking the source table (a test extending a LOCAL COPY of
    ``scout._PILOT_GRID_SELECTORS`` and passing it as ``source`` proves this: the derived set grows
    to include the synthetic entry, which a constant snapshot could never do)."""
    table = _PILOT_GRID_SELECTORS if source is None else source
    return frozenset(
        selector for selector, (_study_id, selector_kind) in table.items() if selector_kind == kind
    )


@router.post("/scout/compute")
def trigger_scout_compute(
    body: ScoutComputeRequest | None = None,
    dataset_store: DatasetStore = Depends(get_dataset_store),
    snapshots_dir: str = Depends(get_micro_snapshots_dir),
    ledger_dir: str = Depends(get_scout_ledger_dir),
    bar_store: BarStore = Depends(get_bar_store),
    playbook_store: PlaybookStore = Depends(get_playbook_store),
    exposure_registry_dir: str = Depends(get_micro_exposure_registry_dir),
    manager: ScoutComputeManager = Depends(get_scout_compute_manager),
) -> dict:
    """Start a Scout screening run over the bounded reference candidate grid (ensuring
    prerequisite snapshots exist first -- reuse-or-build), or refuse (single-flight) if one is
    already running.

    J-09: ``body.grid`` selects ``ScoutComputeManager.trigger``'s own ``grid_selector`` -- see
    that method's docstring. ``bar_store``/``playbook_store`` are ADDITIVE dependencies (the SAME
    ``routes.get_bar_store``/``desk_routes.get_playbook_store`` the readiness/walk-forward routes
    already use); constructing the ``BandMapResolver`` a ``band_touch``-kind selector needs, or
    passing the ``playbook_store`` a ``playbook_signal``-kind selector needs, is SELECTOR-AWARE
    (iter-22: three pilot selectors now exist, spanning two different ``structure_context.kind``
    values) -- this is a POST, operator-triggered act (never a page-load GET), so the construction
    cost only lands on the request that actually asks for it.

    iter-21 audit fix B1 (extended iter-22 to all three pilot selectors): every pilot selector also
    carries the ``ExposureRegistry`` its walk-forward floor check needs, so the operator-reachable
    run RECORDS that decision (a second ledger row under the same ``candidate_id``) exactly as
    goal.md IN SCOPE item 6 requires -- previously that stage existed in source but ran only inside
    a unit test."""
    grid_selector = body.grid if body is not None else None
    resolver = (
        BandMapResolver(bar_store, CONFIG)
        if grid_selector in _pilot_selectors_by_kind("band_touch")
        else None
    )
    playbook_store_for_trigger = (
        playbook_store if grid_selector in _pilot_selectors_by_kind("playbook_signal") else None
    )
    # iter-21 audit fix B1: the pilot run's walk-forward floor-check stage reads the SAME durable
    # exposure registry `POST /walkforward/compute` already depends on (never a second, differently
    # rooted one). Constructed ONLY for a non-default selector -- the default grid's request path is
    # byte-identical to before this fix.
    exposure_registry = ExposureRegistry(exposure_registry_dir) if grid_selector is not None else None
    result = manager.trigger(
        dataset_store, CONFIG, snapshots_dir, ledger_dir,
        grid_selector=grid_selector, resolver=resolver, playbook_store=playbook_store_for_trigger,
        exposure_registry=exposure_registry,
    )
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


# --- J-06 step 2: the tick recorder (tick_recorder.py) --------------------------------------------


def get_tick_recorder_checkpoint_dir() -> str:
    """The recorder's per-chunk checkpoint cache directory -- ``TAPEOLOGY_MICRO_RECORDER_
    CHECKPOINT_DIR`` if set, else a SIBLING of the config-owned dataset directory
    (``tick_recorder.resolve_tick_recorder_checkpoint_dir`` -- see that function's own
    docstring)."""
    return resolve_tick_recorder_checkpoint_dir(CONFIG.dataset_dir_resolved())


def get_tick_recorder_checkpoint_store() -> RecorderCheckpointStore:
    """A FastAPI dependency so a test overrides it outright or points it at a temp path via the
    env var -- the ``get_micro_snapshots_dir``-style pattern, one level up (the STORE itself,
    since the checkpoint cache has no other public accessor)."""
    return RecorderCheckpointStore(get_tick_recorder_checkpoint_dir())


def get_tick_recorder_log_dir() -> str:
    """The recorder's run-log directory -- ``TAPEOLOGY_MICRO_RECORDER_LOG_DIR`` if set, else a
    SIBLING of the config-owned dataset directory (``tick_recorder.resolve_tick_recorder_log_dir``
    -- see that function's own docstring). The run log persists through the SAME
    ``micro_snapshots.append_run_log``/``read_run_log`` the scout/walk-forward sections above
    already reuse (no second run-log implementation)."""
    return resolve_tick_recorder_log_dir(CONFIG.dataset_dir_resolved())


# The single in-flight (or last-terminal) recording job for THIS process -- the same
# module-singleton-behind-a-Depends-accessor precedent as the snapshot/scout/walk-forward managers
# above.
_tick_recorder_compute_manager = TickRecorderComputeManager()


def get_tick_recorder_compute_manager() -> TickRecorderComputeManager:
    """A FastAPI dependency so a test overrides it outright with a fresh, isolated manager (the
    ``get_walkforward_compute_manager`` precedent) -- never reaches into the module-level
    singleton directly."""
    return _tick_recorder_compute_manager


class TickRecorderComputeRequest(BaseModel):
    """Body for ``POST /research/desk/micro/recorder/compute``. Both fields are REQUIRED -- this
    endpoint never defaults to an implicit universe, because exactly which symbols/dates to record
    is what an operator is deciding (the ``DeepBackfillComputeRequest`` precedent)."""

    symbols: list[str]
    dates: list[str]


@router.post("/recorder/compute")
def trigger_tick_recorder_compute(
    body: TickRecorderComputeRequest,
    dataset_store: DatasetStore = Depends(get_dataset_store),
    checkpoint_store: RecorderCheckpointStore = Depends(get_tick_recorder_checkpoint_store),
    adapter=Depends(get_study_market_adapter),
    bar_store: BarStore = Depends(get_bar_store),
    bar_index: BarIndex = Depends(get_bar_index),
    registry=Depends(get_registry),
    run_log_dir: str = Depends(get_tick_recorder_log_dir),
    manager: TickRecorderComputeManager = Depends(get_tick_recorder_compute_manager),
) -> dict:
    """Start a NEW tick recording over ``body.symbols`` x ``body.dates`` -- chunked, throttled,
    resumable (``tick_recorder.run_tick_recording``, TR-19 first), writing through the unchanged
    ``DatasetStore.record`` and pairing a 1m/5m bar backfill for every symbol-day actually
    recorded -- or, if one is already running, return it UNCHANGED (``started: False``,
    single-flight, never a second job). Refuses -- 422, before starting anything -- when
    ``symbols`` or ``dates`` is empty (the ``trigger_desk_deep_backfill_compute`` precedent: a
    recording's scope is exactly what an operator is deciding, never an implicit default)."""
    if not body.symbols or not body.dates:
        raise HTTPException(
            status_code=422,
            detail="both symbols and dates are required and must be non-empty -- an operator "
            "names exactly which symbol-days to record, never an implicit universe",
        )
    return manager.trigger(
        dataset_store, checkpoint_store, adapter, bar_store, bar_index, registry, CONFIG, run_log_dir,
        symbols=body.symbols, dates=body.dates,
    )


@router.get("/recorder/compute")
def get_tick_recorder_compute(
    manager: TickRecorderComputeManager = Depends(get_tick_recorder_compute_manager),
) -> dict:
    """The current (or last-terminal) recording job's progress -- never 404 (the idle default
    before any job has ever run this process).

    Aggregate-only AND composition-safe, at every point during a run (spec section 7.1 r5/r7 +
    TR-32, owner ruling 2026-08-21). ``progress`` never carries a symbol, a date, a dataset id, or
    any other per-chunk field -- and, since TR-32, it carries no OUTCOME-TYPED field either:
    ``chunks_total``/``chunks_done``/``percent_complete``/``elapsed_seconds``/
    ``chunks_per_minute`` only.

    TR-32 closed a COMPOSED leak that field-level opacity alone did not: an observer polling often
    enough that ``chunks_done`` advances by exactly one could difference the former
    ``chunks_fetched``/``chunks_reused``/``chunks_unchanged``/``chunks_failed`` counters against
    the known deterministic plan and reconstruct that specific chunk's realized outcome (verified:
    a whole run was reconstructed exactly). The former ``trades_total_bucket``/
    ``quotes_total_bucket`` leaked the same way by existence rather than magnitude -- running
    totals advance ONLY on a ``fetched`` chunk, so a bucket transition across a single-chunk
    advance proved that chunk was fetched. Both are gone from live progress; exact counts survive
    internally and in the TERMINAL run-log row, where TR-4 positively requires the disclosed
    per-chunk/per-symbol failure list.

    ``manager.snapshot()`` already projects it that way (``tick_recorder._copy_recorder_snapshot``/
    ``_progress_view``, an explicit whitelist and the ONE canonical serving owner both live
    transports share), so this route forwards it VERBATIM -- no second computation, and
    deliberately no operator-only bypass parameter, header, or role claim on this route (r5: using
    one would itself be a human exposure event that destroys the tranche's blindness). TR-2's
    widened inference trap (``test_vault.py``) sweeps this exact path."""
    snap = manager.snapshot()
    return {
        "state": snap["state"],
        "progress": snap["progress"],
        "started_utc": snap["started_utc"],
        "finished_utc": snap["finished_utc"],
        "error": snap["error"],
    }


@router.post("/recorder/compute/cancel")
def cancel_tick_recorder_compute(
    manager: TickRecorderComputeManager = Depends(get_tick_recorder_compute_manager),
) -> dict:
    """Signal cooperative cancellation for the in-flight recording -- a 409 for an idle manager
    (the snapshot/scout/walk-forward-compute-cancel routes' own precedent), else
    ``{"state": "cancelled"}`` acknowledging the REQUEST (the worker itself settles once the
    in-flight chunk finishes)."""
    if manager.snapshot()["state"] != "running":
        raise HTTPException(status_code=409, detail="no tick recording is currently running")
    manager.cancel()
    return {"state": "cancelled"}


@router.get("/recorder/runs")
def get_tick_recorder_runs(run_log_dir: str = Depends(get_tick_recorder_log_dir)) -> dict:
    """The durable run history, newest first -- never 404 on zero runs (an honest empty list)."""
    return {"runs": read_run_log(run_log_dir)}


# --- J-06 step 3: the Validation Vault (vault.py) -- GET-only this iteration ------------------------


def get_vault_dir() -> str:
    """The vault's storage directory -- ``TAPEOLOGY_MICRO_VAULT_DIR`` if set, else a SIBLING of
    the config-owned dataset directory (``vault.resolve_vault_dir`` -- see that function's own
    docstring)."""
    return vault.resolve_vault_dir(CONFIG.dataset_dir_resolved())


@router.get("/vault")
def get_vault(vault_dir: str = Depends(get_vault_dir)) -> dict:
    """Serves ``vault.py``'s own state verbatim (``vault.build_vault_state`` -- no second
    computation in this handler): every shard's CURRENT lifecycle state (opaque-only while
    ``sealed``, full symbol/date/family provenance from ``assigned`` onward -- section 7.5, TR-2),
    every registered universe (never the raw secret, only its commitment -- and, while any member
    of that universe's ORIGINAL registered pool is still unresolved, only the NONCED
    ``rule_commitment``/sizes rather than the ``symbol_rule``/``date_rule`` LISTS or the nonce
    itself, since those minus the public dataset listing would spell out the sealed tranche by
    subtraction: iter-9 audit third pass, widened iteration 12/r7 TR-27,
    ``vault._serialize_universe``), and both ledgers' own chain-verification verdicts. Never
    404/500 on an empty vault -- the desk
    router's established never-404-on-absence convention: an honest empty ``shards``/``universes``
    before any universe is ever registered (registration is a step-4, operator-attended act, out of THIS iteration's
    scope)."""
    return vault.build_vault_state(vault.VaultShardLedger(vault_dir), vault.VaultUniverseLedger(vault_dir))


# --- J-07: Graduation (micro_graduation.py) -- GET-only this iteration ------------------------------


def get_micro_graduation_dir() -> str:
    """The graduation ledger's directory -- ``TAPEOLOGY_MICRO_GRADUATION_DIR`` if set, else a
    SIBLING of the config-owned dataset directory (``micro_graduation.resolve_micro_graduation_dir``
    -- see that function's own docstring)."""
    return resolve_micro_graduation_dir(CONFIG.dataset_dir_resolved())


@router.get("/graduation")
def get_graduation(graduation_dir: str = Depends(get_micro_graduation_dir)) -> dict:
    """Serves ``micro_graduation.py``'s own recorded state verbatim (``list_graduation_families`` --
    see that function's own docstring): every family_root_id ever recorded here, each with its
    current stage-vocabulary state, complete transition history, and complete sealed-evaluation
    history -- beside the ledger's own chain-verification verdict (the ``GET /scout``/``GET
    /walkforward``/``GET /vault`` precedent: surfaced beside the data, never silently accepted if
    tampered). Never 404/500 on an empty ledger (TC-9) -- no operator has run graduation yet on a
    fresh install, so an honest ``EMPTY_LEDGER_MESSAGE`` ("No candidates ledgered.", goal.md's own
    Design Direction example) accompanies the empty ``families`` list at HTTP 200, never a
    fabricated row. Page-load GETs never compute (T-8): J-07 is keyless/automated -- a candidate's
    state is recorded by calling ``micro_graduation.py``'s evaluation functions directly (a test
    today; a future J-08/J-09 wiring act later), never by this route.

    **Why this route has no golden REPLAY script (iteration 12, TC-15).** J-07 has no frontend
    page this iteration (J-08's unbuilt scope), so its only browser-verifiable surface is this
    RAW backend JSON URL, visited directly (``http://<backend-host>:<port>/research/desk/micro/
    graduation``). The deterministic replay runner's own ``normalize_url`` (``incredible_auto_
    dev/scripts/automation/lib/demo_runner.py``) FORCIBLY rewrites any localhost absolute URL onto
    the run's single frontend ``base_url`` host:port -- there is no per-step override in the
    replay schema -- so a golden script cannot express "navigate to the backend origin" at all; it
    would silently 404 against the frontend instead. This is therefore genuinely infeasible, not
    merely unbuilt: the gap is disclosed at ``runs/goal-session-rapid-microscope/state/golden-
    gaps`` (``J-07``) rather than left to silently disappear, and this surface is re-verified each
    iteration through the LLM browser-qa lane instead (iteration-10's own ``UT-J-07`` precedent:
    navigate the browser directly to the backend URL, read the extracted body text)."""
    ledger = GraduationLedger(graduation_dir)
    families = list_graduation_families(ledger)
    return {
        "families": families,
        "message": None if families else EMPTY_LEDGER_MESSAGE,
        "chain_verification": ledger.verify_chain(),
    }


# --- Era "The Hypothesis Foundry" -- J-01: the panel header (era identity + era-open baseline) --
# GET-only this iteration, exactly like every sibling route above (T-8: page-load GETs never
# compute). This route's OWN scope this iteration (goal-hypothesis-foundry-iter-1) is deliberately
# narrow: era/session identity, the Foundry methodology spec version, and the era-open baseline
# block -- see `docs/phases/goal-hypothesis-foundry-iter-1.md` IN SCOPE. `source_registry_hash`
# renders `null` with an explicit `not_yet_generated` status (goal.md: "the real registry does not
# exist until Binding Execution Order step 6 / J-06") -- never a fabricated placeholder hash. The
# CandidateSpec/compiler machinery this iteration DOES build (`foundry_source_registry.py`/
# `foundry_compiler.py`) is proven hermetically by its own test suite and is NOT yet served here --
# the consolidated Foundry read surface (Sources/Compiler and every other subview) is a later,
# single iteration per the goal's own Binding Execution Order step 5 (state/assumptions.md's
# iter-1 entry).


def get_foundry_dir() -> str:
    """The era-open baseline snapshot's storage directory -- ``TAPEOLOGY_FOUNDRY_DIR`` if set,
    else a ``foundry`` SIBLING of the config-owned dataset directory
    (``foundry_source_registry.resolve_foundry_dir`` -- see that function's own docstring)."""
    return resolve_foundry_dir(CONFIG.dataset_dir_resolved())


# goal-hypothesis-foundry-iter-5 (J-06): the real committed epoch. Read from the literal
# Git-TRACKED repo-relative `docs/hypothesis-foundry/`/`reports/hypothesis-foundry/` paths --
# deliberately NEVER through `get_foundry_dir()`/`resolve_foundry_dir()` above, which is
# `TAPEOLOGY_FOUNDRY_DIR`/dataset-directory-SCOPED RUNTIME storage for the era-open baseline only
# (goal.md carried lesson: reading the real epoch through that resolver would reproduce the exact
# iter-0/iter-1 QA-invisibility failure for this whole evidence base, since a real artifact under
# the runtime-scoped directory is invisible to the scoped `:8301` QA rig). The tracked artifacts
# are a Git-committed repo path, checked out identically by every rig at the same commit.
_REPO_ROOT = Path(__file__).resolve().parents[4]
_FOUNDRY_TRACKED_DIR = _REPO_ROOT / "docs" / "hypothesis-foundry"
_FOUNDRY_AUDIT_REPORT_REL_PATH = "reports/hypothesis-foundry/source-registry-audit.md"


def _git_rev_parse_head(repo_root: Path) -> str | None:
    """``None`` (never raises, never fabricates) if this is not a real git checkout or the command
    fails for any reason -- an honest degrade, matching this module's own never-404 convention."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(repo_root), capture_output=True, text=True
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _git_path_committed_at_head(repo_root: Path, rel_path: str) -> bool:
    """``True`` only if ``rel_path`` exists in HEAD's own committed tree -- ``git cat-file -e``,
    never a plain filesystem existence check (which would also be true for an uncommitted file)."""
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{rel_path}"], cwd=str(repo_root), capture_output=True
        )
    except OSError:
        return False
    return result.returncode == 0


def read_epoch_manifest_view(*, tracked_dir: Path | None = None, repo_root: Path | None = None) -> dict:
    """Reads the real, Git-tracked ``docs/hypothesis-foundry/`` artifacts VERBATIM -- the literal
    repo-relative paths (see the module comment above). Computed ONCE at module import time
    (T-8 / goal.md anti-goal 10), never per request, consistent with the four hermetic views above.
    Missing/absent tracked artifacts degrade honestly to ``status: "not_yet_generated"`` -- never a
    fabricated placeholder value (this iteration's own error-case requirement).

    ``tracked_dir``/``repo_root`` default to the real repo-relative paths; a test may override
    either to exercise the missing-artifact degrade path against a synthetic empty directory
    without needing to relocate/hide the actual committed repo files."""
    tracked_dir = tracked_dir if tracked_dir is not None else _FOUNDRY_TRACKED_DIR
    repo_root = repo_root if repo_root is not None else _REPO_ROOT
    not_yet_generated = {
        "status": "not_yet_generated",
        "epoch_id": None,
        "source_registry_hash": None,
        "manifest_hash": None,
        "freeze_set_hash": None,
        "freeze_commit": None,
        "config_fingerprint": None,
        "outcome_access_census": 0,
        "source_dispositions": [],
        "families": [],
        "source_registry_audit": {"path": _FOUNDRY_AUDIT_REPORT_REL_PATH, "committed": False},
    }

    manifest_path = tracked_dir / "epoch-manifest.json"
    freeze_record_path = tracked_dir / "freeze-record.json"
    source_registry_path = tracked_dir / "source-registry.json"
    if not (manifest_path.is_file() and freeze_record_path.is_file() and source_registry_path.is_file()):
        return not_yet_generated

    try:
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        freeze_record_payload = json.loads(freeze_record_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return not_yet_generated

    freeze_commit = freeze_record_payload.get("freeze_commit")
    head = _git_rev_parse_head(repo_root)
    # "committed" means the TRACKED ARTIFACTS THEMSELVES are present in HEAD's own committed tree
    # (TC-9's "all five files appear together in one commit") -- NOT merely that `freeze_commit`
    # (which is pinned to whatever HEAD already was BEFORE generation, per this iteration's own
    # freeze_commit-ordering rule) is an ancestor of the current HEAD, which would be trivially
    # true even while the four JSON files still sit as uncommitted working-tree changes (a real
    # bug caught while building this route: `freeze_commit == head` before the first commit ever
    # happens, since nothing has advanced HEAD yet). Both checks are still verified together:
    # ancestry as the freeze-barrier identity proof, tracked-file presence as the actual
    # "did the operator commit it" fact.
    tracked_rel_paths = (
        "docs/hypothesis-foundry/source-registry.json",
        "docs/hypothesis-foundry/epoch-manifest.json",
        "docs/hypothesis-foundry/freeze-set.json",
        "docs/hypothesis-foundry/freeze-record.json",
    )
    audit_committed = _git_path_committed_at_head(repo_root, _FOUNDRY_AUDIT_REPORT_REL_PATH)
    tracked_files_committed = all(_git_path_committed_at_head(repo_root, p) for p in tracked_rel_paths)
    ancestry_proven = bool(freeze_commit) and head is not None and verify_commit_is_ancestor(
        freeze_commit, head, cwd=repo_root
    )
    is_committed = tracked_files_committed and audit_committed and ancestry_proven

    return {
        "status": "committed" if is_committed else "generated_uncommitted",
        "epoch_id": manifest_payload.get("epoch_id"),
        "source_registry_hash": manifest_payload.get("source_registry_hash"),
        "manifest_hash": manifest_payload.get("manifest_hash"),
        "freeze_set_hash": freeze_record_payload.get("freeze_set_hash"),
        "freeze_commit": freeze_commit,
        "config_fingerprint": manifest_payload.get("config_fingerprint"),
        "outcome_access_census": manifest_payload.get("outcome_access_census", 0),
        "source_dispositions": manifest_payload.get("source_dispositions", []),
        "families": manifest_payload.get("families", []),
        "source_registry_audit": {"path": _FOUNDRY_AUDIT_REPORT_REL_PATH, "committed": audit_committed},
    }


# goal-hypothesis-foundry-iter-4 (J-02/J-03/J-04/J-05): the four consolidated Foundry read-surface
# subviews -- computed EXACTLY ONCE, here, at module import time, from purely hermetic literals
# (never real dataset/session state), and served verbatim on every request thereafter. This is
# what keeps the route itself GET-never-computes (T-8 / goal.md anti-goal 10): the compiler/
# interpreter/family/freeze/ledger/runner machinery those four builders invoke runs ONCE per
# process, not once per request -- TC-19's own "two GET responses are byte-identical" proof holds
# structurally (the same frozen dict object is returned both times), not by chance.
_SOURCES_COMPILER_VIEW = sources_compiler_hermetic_fixture_view()
_INTERPRETER_FIXTURES_VIEW = interpreter_hermetic_fixture_view()
_FREEZE_INTEGRITY_VIEW = freeze_integrity_hermetic_fixture_view()
_HERMETIC_ORACLES_VIEW = build_hermetic_oracles_summary()
# goal-hypothesis-foundry-iter-5 (J-06): computed once, same convention, but reads real committed
# files rather than hermetic literals -- see `read_epoch_manifest_view`'s own docstring.
_EPOCH_MANIFEST_VIEW = read_epoch_manifest_view()


@router.get("/foundry")
def get_foundry(foundry_dir: str = Depends(get_foundry_dir)) -> dict:
    """Serves era/session identity (``foundry_source_registry.foundry_era_identity`` -- a static
    dict, never derived per-request), the persisted era-open baseline snapshot VERBATIM
    (``read_era_open_baseline`` -- ``None`` until the operator's one-time recording act has run,
    never fabricated), and the real ``epoch_manifest`` view (``source_registry_hash``/
    ``source_registry_status`` below are sourced from that SAME read -- no second calculation path
    for the same value). Never 404/500 before that recording act runs -- the desk router's own
    never-404-on-absence convention: an honest ``era_open_baseline: null`` on a fresh install,
    exactly like ``GET /vault``'s honest empty ``shards``/``universes`` before the first
    registration.

    goal-hypothesis-foundry-iter-4: four ADDITIVE top-level keys -- ``sources_compiler``,
    ``interpreter_fixtures``, ``freeze_integrity``, ``hermetic_oracles`` -- each served VERBATIM
    from the module-level frozen views built once above; this handler never calls any compiler/
    interpreter/family/freeze/runner function itself.

    goal-hypothesis-foundry-iter-5: one more additive top-level key, ``epoch_manifest`` -- the
    real, Git-tracked epoch (see ``read_epoch_manifest_view``'s own docstring for why it reads
    literal repo-relative paths rather than the dataset-scoped `foundry_dir` this handler still
    receives for the (unrelated) era-open baseline)."""
    return {
        "era": foundry_era_identity(),
        "era_open_baseline": read_era_open_baseline(foundry_dir),
        "source_registry_hash": _EPOCH_MANIFEST_VIEW["source_registry_hash"],
        "source_registry_status": _EPOCH_MANIFEST_VIEW["status"],
        "epoch_manifest": _EPOCH_MANIFEST_VIEW,
        "sources_compiler": _SOURCES_COMPILER_VIEW,
        "interpreter_fixtures": _INTERPRETER_FIXTURES_VIEW,
        "freeze_integrity": _FREEZE_INTEGRITY_VIEW,
        "hermetic_oracles": _HERMETIC_ORACLES_VIEW,
    }
