"""The ``/research/*`` REST namespace — the kept research surfaces: taxonomy (feed-basis labels),
historical tape datasets, the multi-timeframe bar store, deterministic support/resistance levels +
the tradable-level map, the touch-event/case-study registry, deterministic backtests, the PnL
ledger, the profile + strategy registries, and the 3-way strategy-comparison edge report.

era-5D J-01 ("The Clean Slate" demolition interlude) removed the journal-era thesis-declaration,
replay-studies, and analytics routes from this file (14 route handlers total — see
``docs/goal.md``'s I-1 inventory) — the manual-journaling product surfaces the operator judged not
useful for digging the edge. Every route below is read-only-safe apart from the explicit,
research-action POSTs (record a dataset, record a bar series, create a backtest, trigger an
edge-report compute) — none of them execute a trade (``tests/test_no_execution_path.py`` is the
tier-1 guard).

The router depends on the app-provided ``ResearchRegistry`` (which owns the journal store and the
backtest/edge-compute job managers) via FastAPI dependency-injection, so tests inject a temp-path
store + a test WatchManager through ``dependency_overrides`` exactly like the market-adapter seam.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..config import CONFIG, Config
from ..providers.adapters.base import (
    NoDataForWindow,
    SymbolNotTradable,
    UnsupportedTimeframe,
    VendorTimeout,
)
from ..providers.adapters.yahoo import YahooAdapter
from .backtests import (
    BacktestJobManager,
    PROFILE_DEFAULT,
    TERMINAL_STATUSES as BACKTEST_TERMINAL_STATUSES,
)
from .bar_index import BarIndex
from .bars import (
    BarSeriesAlreadyRegistered,
    BarSeriesIntegrityError,
    BarSeriesNotFound,
    BarStore,
    EmptyBarWindowError,
    NonFiniteBarPriceError,
)
from .edge_report import EdgeReportError, peek_strategy_comparison_report
from .edge_report_backtest_cache import EdgeReportBacktestCache, resolve_backtest_cache_db_path
from .edge_report_cache import EdgeReportCache, _config_content_hash, resolve_cache_db_path
from .edge_report_compute import EdgeReportComputeManager
from .levels import compute_levels
from .setups import BROKE, CHOPPED, REJECTED, compute_setups, enrich_with_tape_timeline
from .tradability import basis_day_key, compute_tradability
from .tradability_cache import (
    TradabilityCache,
    resolve_tradability_cache_db_path,
    symbol_store_signature,
    tradability_cache_key,
)
from .dataset_index import resolve_dataset_index_db_path
from .datasets import (
    VALID_SOURCE_KINDS as DATASET_SOURCE_KINDS,
    VALID_SPLITS,
    DatasetAlreadyRegistered,
    DatasetIntegrityError,
    DatasetNotFound,
    DatasetRecordError,
    DatasetStore,
    EmptyWindowError,
    REFERENCE_SOURCE_ID,
    SOURCE_HISTORICAL,
    SOURCE_REFERENCE,
    parse_utc_epoch,
    record_from_source,
)
from .pnl_ledger import ledger_projection
from .profiles import profiles_projection
from .strategies import strategies_projection
from .feed_basis import data_feed_for_scenario
from .store import JournalStore
from .taxonomy import taxonomy_payload
from . import micro_snapshots
from . import vault

router = APIRouter(prefix="/research", tags=["research"])


class BacktestRequest(BaseModel):
    """Body for ``POST /research/backtests`` (era-3 capability 4, J-03) — exactly the Product
    Shape's three fields: the dataset id, the strategy id, and the profile. ``profile`` defaults
    to ``default``; any id registered in the config-owned profile registry
    (``Config.profile_definition`` — J-06) is accepted. The strategy/profile/dataset validation
    is enforced in the ROUTE (not the schema) so every refusal is explicit — never silent
    coercion. A missing/mis-typed field is a 422 at the schema layer before the route runs (the
    malformed-body case)."""

    dataset_id: str
    strategy_id: str
    profile: str = PROFILE_DEFAULT


class DatasetRecordRequest(BaseModel):
    """Body for ``POST /research/datasets`` (era-3 capability 1, J-02) — the explicit record +
    register research action. ``source_kind`` (``reference`` | ``historical``; datasets are
    HISTORICAL tape, so ``sim`` is not accepted), ``source_id`` (the symbol for a historical
    record; optional for the committed reference window), the immutable ``split`` tag
    (``train`` | ``holdout``, frozen at registration), and an optional ``[start, end)`` UTC
    sub-window (REQUIRED for a historical record). All validation is enforced in the ROUTE (not
    the schema) so every refusal is explicit — never silent coercion."""

    source_kind: str
    source_id: str = ""
    split: str
    start: str | None = None
    end: str | None = None


class BarRecordRequest(BaseModel):
    """Body for ``POST /research/bars`` (era-4 capability 1, J-01; era-5 J-01 makes Yahoo the
    default vendor) — the explicit record + register research action. All four fields are
    required: ``symbol``, ``timeframe`` (validated against the config-owned ``bar_timeframes`` set
    in the ROUTE — out-of-set is a 422, never silently coerced), and the UTC ``start``/``end``
    window fetched through the adapter seam (``fetch_bars`` — Yahoo by default, keyless; Alpaca
    stays selectable). ``end`` is INCLUSIVE by UTC calendar date: fetching with ``end`` on a given
    day includes that whole day's bars (the ROUTE extends the vendor window through the end of
    ``end``'s UTC day — the underlying yfinance ``end`` is exclusive, compensated once, in one
    place). ``start == end`` is thus a valid single-day window; only ``end`` strictly before
    ``start`` is a 422. Unlike a dataset there is only one source per request, so there is no
    ``source_kind`` here.

    ``vendor`` (optional, default ``"yahoo"``) picks which adapter serves THIS request. It exists
    because Yahoo caps intraday history (1m to the last 30 days, 5m to 60, 1h to 730 — the adapter's
    own ``_INTERVAL_LIMITS`` carries the measured evidence), while Alpaca serves the same bars years
    back: a caller that wants the deeper range asks for it explicitly, per request. One request still
    records exactly ONE series from exactly ONE vendor, so the stored ``feed`` stays honest — a
    recording is never a silent blend of two sources."""

    symbol: str
    timeframe: str
    start: str
    end: str
    vendor: str | None = None


class EdgeReportComputeRequest(BaseModel):
    """Body for ``POST /research/edge-report/compute`` (era-fast_wall J-04) — the operator/CLI
    "run this now" trigger. ``force`` (default ``False``) recomputes even over an already-warm
    cache key and republishes (``EdgeReportCache.compute_and_publish`` — J-01's already-shipped
    write half); the default dispatches through the existing ``get_or_compute`` (a warm key serves
    instantly with zero recompute; a cold key computes once)."""

    force: bool = False


class ResearchRegistry:
    """Owns the journal store and the backtest/edge-compute background job managers.

    era-5D J-01 ("The Clean Slate" demolition interlude): this registry previously also attached a
    ``ResearchMonitor`` to every freshly-built watch engine (the WatchManager's
    ``on_engine_created`` hook) and ran a startup expiry sweep over stale theses — both were removed
    along with the journal-era thesis-declaration surfaces, so ``main.py`` no longer wires either
    one up. J-01 kept ``_monitors``/``monitor_for``/``projection_for``/``_surviving_projection``/
    ``hint_projection_for`` alive as inert, ``None``-returning stubs because ``app/main.py``'s WS
    ``thesis``/``hint`` frame merge still called them. era-5D J-02 removed that WS merge — its last
    caller — so this registry now owns exactly what its name says: the store and the two background
    job managers, nothing else.
    """

    def __init__(self, store: JournalStore, config: Config) -> None:
        self._store = store
        self._config = config
        self._fingerprint = config.config_fingerprint()
        # The backtest background-job manager (era-3 capability 4, J-03): cancellable worker threads
        # OFF the event loop, persistence through the SAME single writer queue, in-flight jobs
        # honestly lost on restart (never silently done).
        self._backtest_jobs = BacktestJobManager(store, config)
        # The edge-report compute manager (era-fast_wall J-04) — a single-flight, cancellable,
        # progress-reporting background job around ``run_strategy_comparison_report``. Unlike
        # ``_backtest_jobs`` it needs no ``store``/``config`` at construction time (every
        # ``trigger()`` call takes its store/dataset_store/bar_store/config/cache explicitly) —
        # process-scoped, in-memory-only bookkeeping, honestly lost on restart, never a research
        # value.
        self._edge_report_compute = EdgeReportComputeManager()

    @property
    def store(self) -> JournalStore:
        return self._store

    @property
    def backtest_jobs(self) -> BacktestJobManager:
        return self._backtest_jobs

    @property
    def edge_report_compute(self) -> EdgeReportComputeManager:
        return self._edge_report_compute

    @property
    def config(self) -> Config:
        return self._config


# The app sets this in lifespan (or a test injects one via dependency_overrides). A module-level
# holder keeps the dependency simple while still overridable.
_registry: ResearchRegistry | None = None


def set_registry(registry: ResearchRegistry | None) -> None:
    global _registry
    _registry = registry


def get_registry() -> ResearchRegistry:
    if _registry is None:
        raise HTTPException(status_code=503, detail="research store unavailable")
    return _registry


def get_registry_or_none() -> ResearchRegistry | None:
    """The current registry without raising — used by the app lifespan to decide whether to build a
    default file-store registry or leave a test-injected one in place."""
    return _registry


# Injected so tests can override the WatchManager the routes read (mirrors the adapter seam). The
# default resolves the app's module-level manager lazily to avoid an import cycle at module load.
def get_watch_manager():
    from ..main import manager

    return manager


@router.get("/taxonomy")
def get_taxonomy() -> dict:
    """The feed-basis label catalog — the single backend owner of the feed-basis display copy
    (era-5D J-01 slimmed this route's payload from the full research-label catalog down to just
    this block; see ``app/research/taxonomy.py``'s module docstring)."""
    return taxonomy_payload()


# --- Historical tape datasets (era-3 capability 1, J-02) -----------------------------------------
# Exactly THREE routes (Product Shape): record/register, list, detail. There is NO PATCH / PUT /
# DELETE — a dataset is immutable and its split tag is frozen at registration (structurally: the
# store exposes no update path at all; re-recording registered content is the 409 below). The
# dataset store module is the ONE reader/writer of dataset files; these routes serve its
# metadata VERBATIM (the MCP ``datasets`` tool proxies the list byte-identically).


# The market adapter for an ARBITRARY-WINDOW historical dataset recording — resolved through the SAME
# neutral seam the watch path uses, honoring test ``dependency_overrides`` (a hermetic test injects
# its FakeAdapter; a credentialless run fails explicitly, never fixture-substituted). Lazy import
# avoids an import cycle. era-5D J-01: relocated here (this file's dataset-routes section) from beside
# the now-deleted ``POST /research/studies`` route, its ORIGINAL sole other caller — ``record_dataset``
# below is now its only consumer. A pure move: same name, same body, same behaviour.
def get_study_market_adapter():
    from ..main import app, get_market_adapter

    return app.dependency_overrides.get(get_market_adapter, get_market_adapter)()


def _build_historical_fetch(adapter, symbol: str, start: str, end: str):
    """A blocking fetch callable the runner invokes ON ITS WORKER THREAD (off the event loop) for an
    arbitrary-window historical record. It uses the EXISTING adapter ``fetch_historical`` so
    credentials / no-data / untradable / timeout each surface the existing explicit errors (the
    caller maps them to the explicit dataset-recording error — never fabricated, never
    fixture-substituted)."""
    from datetime import datetime, timezone

    def _parse(value: str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)

    start_dt = _parse(start)
    end_dt = _parse(end)

    def _fetch():
        return adapter.fetch_historical(symbol, start_dt, end_dt)

    return _fetch


def get_dataset_store() -> DatasetStore:
    """The dataset store rooted at the config-owned directory (``TAPEOLOGY_DATASET_DIR``
    override, package-anchored default). A FastAPI dependency so tests can point it at a temp
    dir via the env var or override it outright (the adapter-seam pattern).

    era-fast_wall J-02: also wires the durable metadata index (``dataset_index.py``) — a
    config-DERIVED, env-overridable path so ``config.py`` stays byte-identical
    (``config_fingerprint`` unaffected, the identical ``get_bar_index`` rationale): the
    ``TAPEOLOGY_DATASET_INDEX_DB`` env var if set, else a file co-located as a SIBLING of the
    resolved dataset directory (``.data/datasets`` -> ``.data/dataset_index.db`` — the SAME
    ``get_bar_index`` env-else-sibling shape, mirrored exactly). Every existing test keeps this
    hermetically for free, since the derived default lives right beside whatever
    ``TAPEOLOGY_DATASET_DIR`` a test points at."""
    # r14: the resolution moved to `dataset_index.py`, which OWNS the index -- so this route and
    # every CLI/module path now land on the SAME file instead of two independently-spelled rules.
    # Byte-identical to the inline version it replaces (env var, else sibling of the dataset dir).
    dataset_dir = CONFIG.dataset_dir_resolved()
    return DatasetStore(dataset_dir, index_db_path=resolve_dataset_index_db_path(dataset_dir))


@router.post("/datasets")
def record_dataset(
    body: DatasetRecordRequest,
    registry: ResearchRegistry = Depends(get_registry),
    store: DatasetStore = Depends(get_dataset_store),
) -> dict:
    """Record + register ONE historical tape dataset (the explicit research action — recording
    is never ambient). Full validation (422, never silent coercion):
      * unknown ``split`` (a dataset is registered ``train`` or ``holdout``) or ``source_kind``
        (``reference`` | ``historical`` — a seeded sim stream reproduces on demand, so ``sim``
        is not recordable);
      * a historical record missing its symbol or its ``start``/``end`` window, a malformed
        ISO date-time, ``end`` not after ``start``, or only one bound of the pair;
      * an empty requested window (nothing is written, nothing fabricated).
    Content already registered — under ANY split — is the 409-style re-tag refusal. A
    credentialless historical record is an explicit 422 (never fixture-substituted)."""
    if body.split not in VALID_SPLITS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown split '{body.split}' — a dataset is registered 'train' or 'holdout'",
        )
    if body.source_kind not in DATASET_SOURCE_KINDS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"unknown source_kind '{body.source_kind}' — datasets record 'reference' or "
                f"'historical' tape (a sim stream reproduces on demand and is not recordable)"
            ),
        )
    if (body.start is None) != (body.end is None):
        raise HTTPException(status_code=422, detail="start and end must be given together")
    if body.start is not None and body.end is not None:
        try:
            start_epoch = parse_utc_epoch(body.start)
            end_epoch = parse_utc_epoch(body.end)
        except ValueError:
            raise HTTPException(status_code=422, detail="start and end must be ISO date-times")
        if end_epoch <= start_epoch:
            raise HTTPException(status_code=422, detail="end must be after start")

    historical_fetch = None
    source_id = body.source_id
    if body.source_kind == SOURCE_REFERENCE:
        if body.source_id not in ("", REFERENCE_SOURCE_ID):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"unknown reference source '{body.source_id}' — the committed reference "
                    f"window is '{REFERENCE_SOURCE_ID}'"
                ),
            )
        source_id = REFERENCE_SOURCE_ID
    else:  # SOURCE_HISTORICAL — an arbitrary real window through the EXISTING adapter seam.
        if not body.source_id:
            raise HTTPException(status_code=422, detail="a historical record requires a symbol")
        if body.start is None or body.end is None:
            raise HTTPException(
                status_code=422, detail="a historical record requires start and end"
            )
        adapter = get_study_market_adapter()
        if not adapter.is_available():
            raise HTTPException(
                status_code=422,
                detail="real-data provider unavailable — a historical record needs credentials",
            )
        historical_fetch = _build_historical_fetch(adapter, body.source_id, body.start, body.end)

    try:
        meta = record_from_source(
            store,
            source_kind=body.source_kind,
            source_id=source_id,
            split=body.split,
            start=body.start,
            end=body.end,
            config=registry.config,
            historical_fetch=historical_fetch,
        )
    except DatasetAlreadyRegistered as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except EmptyWindowError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except DatasetRecordError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except SymbolNotTradable:
        raise HTTPException(
            status_code=422, detail=f"symbol '{body.source_id}' is not tradable"
        )
    except NoDataForWindow:
        raise HTTPException(status_code=422, detail="no data for that window")
    except VendorTimeout as exc:
        raise HTTPException(status_code=504, detail=exc.detail)
    return {"dataset": meta}


def get_withheld_dataset_ids(store: DatasetStore = Depends(get_dataset_store)) -> frozenset[str]:
    """Every dataset id that is part of an unresolved registered-universe pool — spec §7.5 point 3
    (r3, the ledger-tracked case) and point 7 (r5, era iteration 11: the universe-RULE-tracked
    case too — see ``vault.unresolved_pool_universe_by_dataset_id``'s own docstring for the full
    reasoning). Delegated entirely to ``micro_snapshots.withheld_dataset_ids_for_store`` — THE one
    choke point every other corpus-wide consumer already shares — never a second, locally
    reimplemented predicate for this listing/detail/backtest-creation surface specifically.

    **Iteration 11 closes a real gap here, not a hypothetical one.** This is the era's own
    ``GET /research/datasets`` — the SAME surface docs/phases/goal-rapid-microscope-iter-11.md's
    own BACKGROUND section names explicitly: "The instant a real recording under a registered
    universe finalizes a dataset, it becomes fully identifiable in `GET /research/datasets` and
    in readiness's `shards` list". Before this iteration, this dependency called
    ``vault.withheld_dataset_ids`` directly (the ledger-row-only predicate) — a real recording
    finalized under a registered universe but never explicitly sealed would have been fully
    identifiable right here, on the single most public dataset-listing surface in the product.

    A FastAPI dependency (resolved through the SAME ``get_dataset_store`` dependency
    ``list_datasets``/``get_dataset`` themselves already use, so there is exactly one store
    resolution path) so tests can override it outright.

    Empty — and therefore a provable no-op for every existing behaviour — until the first shard is
    ever sealed OR the first universe is ever registered."""
    return micro_snapshots.withheld_dataset_ids_for_store(store)


@router.get("/datasets")
def list_datasets(
    store: DatasetStore = Depends(get_dataset_store),
    withheld_ids: frozenset[str] = Depends(get_withheld_dataset_ids),
) -> dict:
    """List every registered dataset's metadata (each file checksum-verified on load), oldest
    first. A file that fails verification is surfaced EXPLICITLY in ``integrity_errors`` — never
    silently hidden, never served as data. The MCP ``datasets`` tool proxies this byte-for-byte.

    Sealed-shard withholding (spec §7.5 point 3, r3): a dataset whose vault shard has not yet
    reached ``exposed`` is OMITTED from ``datasets`` — its manifest carries the symbol, session
    window and exact event counts §7.5 withholds, and this listing is the join surface the iter-9
    audit's finding B1 demonstrated. The omission is DISCLOSED, never silent: ``sealed_withheld``
    counts how many stored datasets were withheld, so a reader can always tell "nothing recorded"
    from "recorded and sealed". The count alone reveals no shard identity, and the shards
    themselves are served — opaquely — by their own canonical endpoint,
    ``GET /research/desk/micro/vault``."""
    records, errors = store.list()
    served = [meta for meta in records if meta["id"] not in withheld_ids]
    return {
        "datasets": served,
        "integrity_errors": errors,
        "sealed_withheld": len(records) - len(served),
    }


@router.get("/datasets/{dataset_id}")
def get_dataset(
    dataset_id: str,
    store: DatasetStore = Depends(get_dataset_store),
    withheld_ids: frozenset[str] = Depends(get_withheld_dataset_ids),
) -> dict:
    """One dataset's stored metadata, verbatim (checksum-verified on load). 404 for an unknown
    id; an explicit 500 integrity error for a corrupted/tampered file (never a fabricated
    dataset); and — spec §7.5 point 3 (r3) — a typed 403 refusal for a dataset whose vault shard
    has not yet reached ``exposed``, checked BEFORE the file is even opened (fail-closed). The
    refusal states only that the id is sealed: never the symbol, window, counts, or universe
    (``vault.SealedShardWithheldError`` owns the single wording)."""
    if dataset_id in withheld_ids:
        raise HTTPException(
            status_code=403, detail=str(vault.SealedShardWithheldError(dataset_id))
        )
    try:
        meta = store.get(dataset_id)
    except DatasetNotFound:
        raise HTTPException(status_code=404, detail=f"no dataset with id '{dataset_id}'")
    except DatasetIntegrityError as exc:
        raise HTTPException(status_code=500, detail=f"dataset integrity check failed: {exc}")
    return {"dataset": meta}


# --- Multi-timeframe OHLC bar store (era-4 capability 1, J-01) --------------------------------------
# Exactly THREE routes (mirroring the ``/datasets`` trio above): record/register, list, detail.
# There is NO PATCH/PUT/DELETE — a bar series is immutable (structurally: the store exposes no
# update path at all; re-recording registered content is the 409 below). The bar store module is
# the ONE reader/writer of bar-series files; these routes serve its metadata + candles VERBATIM
# (the MCP ``bars`` tool proxies the list byte-identically).


def get_bar_store() -> BarStore:
    """The bar store rooted at the config-owned directory (``TAPEOLOGY_BAR_DIR`` override,
    package-anchored default). A FastAPI dependency so tests can point it at a temp dir via the
    env var or override it outright (the ``get_dataset_store`` pattern).

    Also wires the durable stat-keyed verified-metadata cache (``bar_verify_cache.py``) on the
    SAME config-DERIVED, env-overridable shape ``get_bar_index``/``get_dataset_store`` use — the
    ``TAPEOLOGY_BAR_VERIFY_CACHE_DB`` env var if set, else a file co-located as a SIBLING of the
    resolved bar directory (``.data/bars`` -> ``.data/bar_verify_cache.db``). ``config.py`` stays
    byte-identical, so ``config_fingerprint`` is unaffected; and every existing test gets this
    hermetically for free, since the derived default lives beside whatever ``TAPEOLOGY_BAR_DIR``
    the test points at."""
    return BarStore(CONFIG.bar_dir_resolved(), verify_cache_db_path=bar_verify_cache_db_path())


def bar_verify_cache_db_path() -> str:
    """The resolved durable bar-verify-cache path — the ONE resolver every entry point shares
    (the FastAPI dependency above, the desk CLI warmers, and each worker process of a parallel
    screen walk), so a worker can never end up re-verifying a store the server already remembers."""
    override = os.environ.get("TAPEOLOGY_BAR_VERIFY_CACHE_DB")
    if override:
        return override
    return os.path.join(os.path.dirname(CONFIG.bar_dir_resolved()), "bar_verify_cache.db")


def get_bar_index() -> BarIndex:
    """The derived SQLite bar-lookup index (era-5 J-03) — a config-DERIVED, env-overridable path
    so ``config.py`` stays byte-identical (``config_fingerprint`` unaffected, the spec's preferred
    path over a fingerprint-excluded field): the ``TAPEOLOGY_BAR_INDEX_DB`` env var if set, else a
    file co-located as a SIBLING of the config-owned bar directory (``get_bar_store``'s own
    ``bar_dir_resolved()``, e.g. ``.data/bars`` -> ``.data/bar_index.db``). A FastAPI dependency so
    tests can override it outright, exactly like ``get_bar_store`` — though every existing bar
    test already gets this hermetically for free, since the derived default lives right beside
    whatever ``TAPEOLOGY_BAR_DIR`` a test points at."""
    override = os.environ.get("TAPEOLOGY_BAR_INDEX_DB")
    db_path = override if override else os.path.join(os.path.dirname(CONFIG.bar_dir_resolved()), "bar_index.db")
    return BarIndex(db_path)


def get_edge_report_cache() -> EdgeReportCache:
    """The persisted, rebuildable 3-way strategy-comparison result cache (era-5B J-08) — a
    config-DERIVED, env-overridable path so ``config.py`` stays byte-identical
    (``config_fingerprint`` unaffected — the identical ``get_bar_index`` rationale): the
    ``TAPEOLOGY_EDGE_REPORT_CACHE_DB`` env var if set, else a file co-located as a SIBLING of the
    config-owned dataset directory (``get_dataset_store``'s own ``dataset_dir_resolved()``, e.g.
    ``.data/datasets`` -> ``.data/edge_report_cache.db`` — the SAME ``.data/`` directory
    ``bar_index.db`` already lives in). A FastAPI dependency so tests can override it outright or
    point it at a temp path via the env var — the ``get_bar_index`` pattern, exactly.

    era-fast_wall J-01: the path policy itself now lives in ONE shared ``edge_report_cache.
    resolve_cache_db_path`` function — this dependency's whole body is just resolving-then-
    constructing — so a future CLI caller (J-04's warmer) resolves the IDENTICAL path with zero
    duplicated logic. This function's own resolved path is unchanged for every existing test."""
    return EdgeReportCache(resolve_cache_db_path(CONFIG.dataset_dir_resolved()))


def get_edge_report_backtest_cache() -> EdgeReportBacktestCache:
    """The persisted, rebuildable per-(dataset x strategy)-pair backtest sub-cache (era-fast_wall
    J-05) — the ``get_edge_report_cache`` precedent, mirrored for a DIFFERENT durable file: the
    ``TAPEOLOGY_EDGE_SWEEP_CACHE_DB`` env var if set, else a file co-located as a SIBLING of the
    config-owned dataset directory (``resolve_backtest_cache_db_path`` — the shared resolver, the
    ``resolve_cache_db_path`` pattern). A FastAPI dependency so tests can override it outright or
    point it at a temp path via the env var."""
    return EdgeReportBacktestCache(resolve_backtest_cache_db_path(CONFIG.dataset_dir_resolved()))


def get_bar_fetch_adapter(vendor: str | None = None):
    """The market adapter for the BAR-FETCH path ONLY (``POST /research/bars`` — era-5 J-01).

    ``vendor="alpaca"`` explicitly selects the credentialed Alpaca adapter for THIS request — the
    deep-history path for windows Yahoo caps (1m beyond 30 days, 5m beyond 60). Any other value (or
    none) keeps the pre-existing behaviour below verbatim, so every existing caller and test is
    unaffected. The test override still wins for BOTH branches: a suite that injects a FakeAdapter
    on ``get_market_adapter`` keeps getting it whichever vendor a request names, so this never opens
    a hidden real-network path in tests.

    Defaults to the keyless ``YahooAdapter`` (era-5's headline capability) while STILL honoring any
    existing test override on ``get_market_adapter`` — the SAME dependency key every
    ``test_bars_api.py`` test already injects a ``FakeAdapter`` through — so every pre-iteration
    test keeps passing UNMODIFIED (Alpaca/fake stays selectable, opt-in, byte-identical).
    Deliberately DISTINCT from ``get_study_market_adapter()`` above (used by ``create_study``
    SOURCE_HISTORICAL and historical-dataset recording, both of which call ``fetch_historical`` — a
    capability Yahoo honestly does not have): flipping THAT shared resolver's own default to Yahoo
    would silently break those two paths, a real J-06 regression. Lazy import avoids an import
    cycle (mirrors ``get_study_market_adapter``)."""
    from ..main import app, get_market_adapter

    if vendor == "alpaca" and get_market_adapter not in app.dependency_overrides:
        from ..providers.adapters.alpaca import AlpacaAdapter

        return AlpacaAdapter()
    return app.dependency_overrides.get(get_market_adapter, YahooAdapter)()


def _clamped_window_may_have_grown(stored: dict) -> bool:
    """Whether a store-first hit should be RE-FETCHED rather than served.

    True only for a recording that a vendor cap actually shortened (``vendor_limit`` set) AND that
    was created on an earlier UTC day than today. Those caps are rolling windows measured in days
    (Yahoo keeps 1m for the last 30 days, 5m for 60), so a recording made yesterday is missing days
    that exist now, while one made earlier today is not — re-fetching within the same UTC day would
    burn a vendor call to receive the identical bars. A recording served in full is never re-fetched
    (immutable content, immutable answer), so the fast path is unchanged for every complete window.
    """
    if not stored.get("vendor_limit"):
        return False
    created = str(stored.get("created_utc", ""))[:10]
    if not created:
        return False
    from datetime import datetime, timezone

    return created < datetime.now(timezone.utc).date().isoformat()


@router.post("/bars")
def record_bar_series(
    body: BarRecordRequest,
    registry: ResearchRegistry = Depends(get_registry),
    store: BarStore = Depends(get_bar_store),
    index: BarIndex = Depends(get_bar_index),
) -> dict:
    """Record + register ONE multi-timeframe OHLC bar series (era-4 J-01, era-5 J-01/J-02 — the
    explicit research action; recording is never ambient). Full validation (422, never silent
    coercion): an out-of-set ``timeframe`` (the config-owned ``bar_timeframes`` set), a missing
    symbol, a malformed ISO ``start``/``end``, or ``end`` strictly before ``start``. The bar-fetch
    vendor defaults to the KEYLESS Yahoo adapter (``get_bar_fetch_adapter`` — era-5 J-01); Alpaca
    stays selectable via the existing ``get_market_adapter`` override, where missing credentials
    still surface the EXISTING explicit unavailable (503) state — never fabricated bars. Content
    already registered (a DIFFERENT window whose fetched content happens to match content already on
    file) is still the 409-style refusal from the frozen ``store.record``.

    Era-5C: the UTC window's ``end`` is INCLUSIVE by calendar date. The vendor fetch below runs
    through the END of ``end``'s UTC day (the adapter/yfinance ``end`` stays half-open; the route
    compensates once — see ``vendor_end_dt`` below), so bars ON ``end``'s date are included and
    ``start == end`` is a valid single-day window. The stored ``window_start_utc``/``window_end_utc``
    remain the VERBATIM request strings (never the extended vendor bound), so the store-first index
    key is unchanged. CAVEAT: a byte-identical ``(symbol, timeframe, start, end)`` window RECORDED
    before this inclusive-end contract keeps serving its original (exclusive-era) content store-first
    — no honest automatic invalidation exists (an inclusive fetch ending on a weekend legitimately
    has no end-date bars, indistinguishable from stale content); re-record under any different window
    string to fetch fresh.

    Era-5 J-02: the Yahoo path's honest-error taxonomy is now THREE observably distinct 4xx/5xx
    states (each nothing-written, nothing-fabricated) — a config-valid timeframe Yahoo does not
    serve (``UnsupportedTimeframe``, 422, e.g. ``8h``/``1mo``/``15m``), a mapped/servable timeframe
    whose specific symbol/window returns nothing from the vendor (``NoDataForWindow``, 422 — an
    unknown symbol or a window outside that timeframe's retention), and a real vendor timeout
    (``VendorTimeout``, 504, unchanged). A non-Yahoo adapter (e.g. Alpaca/fake, via the
    ``get_market_adapter`` override) that returns an empty tuple directly still hits the existing,
    unchanged ``EmptyBarWindowError`` 422 path below — this taxonomy is additive, not a
    replacement.

    Era-5 J-03: a STORE-FIRST coordinator runs immediately after validation, BEFORE any adapter is
    touched — an exact-key ``(symbol, timeframe, window_start, window_end)`` index hit returns the
    ALREADY-STORED series (checksum-verified via ``store.get``) with ZERO adapter/network calls,
    so an identical repeat POST is served instantly and never re-hits Yahoo. On a miss — or on a
    hit whose indexed series the canonical JSON store can no longer verify (deleted or corrupted
    since indexing) — the fetch flow below runs exactly as before, then additively updates the
    index once ``store.record`` succeeds. The index is a derived cache ONLY; it never substitutes
    for the checksum-verified JSON read, and its own loss/corruption never fabricates a series."""
    if body.timeframe not in CONFIG.bar_timeframes:
        raise HTTPException(
            status_code=422,
            detail=(
                f"unknown timeframe '{body.timeframe}' — the registered timeframes are "
                f"{list(CONFIG.bar_timeframes)}"
            ),
        )
    if not body.symbol:
        raise HTTPException(status_code=422, detail="a bar recording requires a symbol")
    try:
        start_epoch = parse_utc_epoch(body.start)
        end_epoch = parse_utc_epoch(body.end)
    except ValueError:
        raise HTTPException(status_code=422, detail="start and end must be ISO date-times")
    if end_epoch < start_epoch:
        # ``end`` is INCLUSIVE by UTC calendar date (see the route docstring), so ``start == end``
        # is a valid single-day window — only a strictly-earlier ``end`` is a 422.
        raise HTTPException(status_code=422, detail="end must be on or after start")

    # Normalized HERE (era-5 J-03 moves this earlier than the pre-J-03 code) so the store-first
    # lookup key below matches EXACTLY what a successful fetch later stores — an unnormalized
    # lookup key would silently never hit.
    symbol = body.symbol.strip().upper()

    # The adapter is resolved BEFORE the store-first lookup because the lookup key now includes the
    # feed this request would record under: a Yahoo recording of a window must not answer a lookup
    # for the same window from Alpaca (different session coverage, different tape). Construction is
    # cheap and does no I/O, and the availability check stays BELOW the lookup so an already-stored
    # window is still served without credentials.
    adapter = get_bar_fetch_adapter(body.vendor)
    # feed provenance (era-5 J-01): sourced from the ADAPTER — its single owner — only when Yahoo
    # served this fetch; otherwise the EXISTING config-owned historical feed, byte-identical to
    # every pre-iteration stamp. NOT ``adapter.name`` applied uniformly: ``AlpacaAdapter.name ==
    # "alpaca"``, not ``"sip"`` — doing so would silently rename Alpaca's stamp and break the
    # frozen ``test_post_records_and_registers_a_bar_series`` assertion.
    feed = adapter.name if isinstance(adapter, YahooAdapter) else registry.config.historical_feed

    stale_clamped: dict | None = None
    hit = index.lookup(symbol, body.timeframe, body.start, body.end, feed)
    if hit is not None:
        try:
            stored = store.get(hit.series_id)
            if not _clamped_window_may_have_grown(stored):
                return {"bar_series": stored}
            stale_clamped = stored
            # A CLAMPED recording (the vendor served less than was asked for, because the window
            # reached past its rolling retention) is NOT served store-first: that retention window
            # has since moved, so days that did not exist when it was recorded may exist now.
            # Falling through re-fetches and records them as a new immutable series; the merged
            # candle read stitches the two by timestamp. A fully-covered recording still returns
            # instantly, exactly as before.
        except (BarSeriesNotFound, BarSeriesIntegrityError):
            # The index pointed at a series the canonical JSON store can no longer verify
            # (deleted or corrupted since indexing) -- never fabricate or serve partial data.
            # Fall through and treat this exactly like a first-time miss; a real re-fetch below
            # additively overwrites this stale entry once it succeeds.
            pass

    if not adapter.is_available():
        # No credentials -> the EXISTING explicit unavailable (503) state (never a fabricated bar
        # series) — the DoD-mandated status for this gap, distinct from the historical-dataset
        # path's 422 for the analogous case. Yahoo is always available (keyless); this only fires
        # when an override (e.g. a credentialless Alpaca selection) reports unavailable.
        raise HTTPException(
            status_code=503,
            detail="real-data provider unavailable — a historical bar recording needs credentials",
        )

    from datetime import datetime, timedelta, timezone

    start_dt = datetime.fromtimestamp(start_epoch, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_epoch, tz=timezone.utc)
    # Era-5C: ``end`` is INCLUSIVE by UTC calendar date. The adapter (and yfinance beneath it) keeps
    # its pure half-open ``[start, end)`` vendor contract, so we compensate HERE — floor ``end`` to
    # its UTC day and add one day, giving a vendor window that includes every bar ON ``end``'s date
    # and none after it, regardless of any time component the caller passed. The store/index below
    # still key on the VERBATIM ``body.start``/``body.end`` strings, so the store-first key is
    # unchanged (a repeat of the same request still hits store-first).
    vendor_end_dt = (
        datetime(end_dt.year, end_dt.month, end_dt.day, tzinfo=timezone.utc) + timedelta(days=1)
    )
    try:
        raw_bars = adapter.fetch_bars(symbol, start_dt, vendor_end_dt, body.timeframe)
    except VendorTimeout as exc:
        raise HTTPException(status_code=504, detail=exc.detail)
    except UnsupportedTimeframe as exc:
        # Era-5 J-02, error-taxonomy case 1: a config-valid timeframe this VENDOR does not serve
        # (e.g. "8h"/"1mo"/"15m") — statically distinct from "no data for that window" below
        # (different detail text; the adapter raised this with zero vendor call). Nothing written.
        raise HTTPException(status_code=422, detail=str(exc))
    except NoDataForWindow as exc:
        # Era-5 J-02, error-taxonomy case 2: a MAPPED/servable timeframe whose specific
        # symbol/window genuinely returned nothing from the vendor (out of retention, or an
        # unknown symbol) — observably distinct from the unsupported-timeframe case above. Nothing
        # written (mirrors the analogous ``record_dataset`` mapping above for the same exception).
        raise HTTPException(status_code=422, detail=str(exc))

    # The vendor's OWN account of any cap that shortened this fetch (Yahoo's per-interval retention
    # — see its `_INTERVAL_LIMITS`). Optional adapter capability: an adapter that declares no caps
    # simply has no method, and the recording carries `vendor_limit: null` — meaning "served in
    # full", never "unknown". Asked BEFORE recording so the reason is stored WITH the short series.
    limit_probe = getattr(adapter, "bar_fetch_limit", None)
    vendor_limit = limit_probe(body.timeframe, start_dt, vendor_end_dt) if limit_probe else None

    try:
        meta = store.record(
            symbol=symbol,
            timeframe=body.timeframe,
            window_start_utc=body.start,
            window_end_utc=body.end,
            feed=feed,
            bars=list(raw_bars),
            vendor_limit=vendor_limit,
        )
    except BarSeriesAlreadyRegistered as exc:
        if stale_clamped is not None:
            # This fetch only ran because a CLAMPED recording of the same window might have grown
            # (see the store-first branch above) — and it turns out it has not: the vendor served
            # content already on file. Serving that recording is the honest answer to "give me this
            # window" (the data exists, unchanged); a 409 here would report a conflict where the
            # caller only asked for data it already has.
            try:
                return {"bar_series": store.get(exc.existing_id)}
            except (BarSeriesNotFound, BarSeriesIntegrityError):
                pass
        raise HTTPException(status_code=409, detail=str(exc))
    except EmptyBarWindowError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except NonFiniteBarPriceError as exc:
        # The store's priceless-bar rail refused the write (era-desk-iter-4 audit B1). Unreachable
        # through a Yahoo fetch now that the adapter drops such rows at the vendor seam, so this maps
        # the OTHER adapters' (and any future caller's) case to the same honest 422 the empty-window
        # refusal uses — a caller-visible refusal naming the row, never an opaque 500.
        raise HTTPException(status_code=422, detail=str(exc))
    # Era-5 J-03: additively index the freshly-recorded series ONLY after store.record succeeds —
    # using the returned meta dict's fields (the values that actually got written), never
    # re-derived from the request body.
    index.insert(meta)
    return {"bar_series": meta}


@router.get("/bars")
def list_bar_series(
    symbol: str | None = None,
    timeframe: str | None = None,
    include_bars: bool = True,
    store: BarStore = Depends(get_bar_store),
    index: BarIndex = Depends(get_bar_index),
) -> dict:
    """List registered bar series' metadata + candles (each file checksum-verified on load),
    oldest first. A file that fails verification is surfaced EXPLICITLY in ``integrity_errors`` —
    never silently hidden, never served as data. The MCP ``bars`` tool proxies the NO-PARAM call
    byte-for-byte.

    Era-5 J-03: optional ``?symbol=`` / ``?timeframe=`` query params (either or both, independently
    combinable) serve an ADDITIVE filter through the index — same response shape, just narrowed.
    With NEITHER param present the response is BYTE-IDENTICAL to before this iteration: still
    ``store.list()`` verbatim, and the index is never consulted on that path. ``symbol`` is
    normalized the SAME way the record path stores it (stripped + uppercased) so the filter is
    case-insensitive; an indexed hit whose series the JSON store can no longer verify (deleted or
    corrupted since indexing) is skipped and surfaced in ``integrity_errors`` — never fabricated or
    silently dropped.

    Era-5 J-05 (audit carry-forward B2 fix): the blank-string normalization runs BEFORE the
    no-param short-circuit test, so a blank ``?symbol=`` and/or ``?timeframe=`` (present but empty)
    normalizes to ``None`` and is treated as ABSENT — taking the exact same byte-identical
    ``store.list()`` path as a true no-param call. Previously the short-circuit tested the raw
    (un-normalized) params, so a blank ``?symbol=`` fell through to ``index.list(None, None)``
    instead — silently missing any series the index never learned of (e.g. a legacy un-indexed
    record). The real-filter path's behavior below is unchanged.

    Optional ``?include_bars=false`` (ADDITIVE, default ``true``) serves the SAME verified records
    with the per-series ``bars`` key OMITTED — the metadata-only projection a viewport-sized chart
    reads before paging candles in through ``GET /research/bars/{id}/candles``. It changes only the
    projection, never which series are served nor which code path selects them (the no-param and
    indexed-filter branches below are structurally untouched), so ``include_bars=true`` — and any
    call that omits the param — stays byte-identical to before."""
    normalized_symbol = symbol.strip().upper() if symbol else None
    normalized_timeframe = timeframe.strip() if timeframe else None
    if normalized_symbol is None and normalized_timeframe is None:
        records, errors = store.list(include_bars=include_bars)
        return {"bar_series": records, "integrity_errors": errors}

    records: list[dict] = []
    errors: list[dict] = []
    for hit in index.list(symbol=normalized_symbol, timeframe=normalized_timeframe):
        try:
            records.append(store.get(hit.series_id, include_bars=include_bars))
        except BarSeriesNotFound:
            errors.append(
                {
                    "file": f"{hit.series_id}.json",
                    "error": f"indexed series '{hit.series_id}' no longer exists in the store",
                }
            )
        except BarSeriesIntegrityError as exc:
            errors.append({"file": f"{hit.series_id}.json", "error": str(exc)})
    records.sort(key=lambda meta: (meta.get("created_utc", ""), meta.get("id", "")))
    return {"bar_series": records, "integrity_errors": errors}


@router.get("/bars/{bar_series_id}")
def get_bar_series(bar_series_id: str, store: BarStore = Depends(get_bar_store)) -> dict:
    """One bar series' stored metadata + candles, verbatim (checksum-verified on load). 404 for an
    unknown id; an explicit 500 integrity error for a corrupted/tampered file (never a fabricated
    series)."""
    try:
        meta = store.get(bar_series_id)
    except BarSeriesNotFound:
        raise HTTPException(status_code=404, detail=f"no bar series with id '{bar_series_id}'")
    except BarSeriesIntegrityError as exc:
        raise HTTPException(status_code=500, detail=f"bar series integrity check failed: {exc}")
    return {"bar_series": meta}


# The bounded candle-slice read: the paging seam the `/structure` charts scroll through instead of
# pulling a whole series into the browser. It serves the SAME verified store rows the detail route
# above serves — just a window of them — so there is no second candle source and nothing here is
# recomputed, re-binned, or gap-filled. Cursor semantics (both INCLUSIVE, at most one at a time) and
# the two "more exist" flags are owned by `BarStore.candles`; this route only parses/validates the
# query params and serves that method's output verbatim.
_MAX_CANDLE_LIMIT = 5000


@router.get("/bars/{bar_series_id}/candles")
def get_bar_series_candles(
    bar_series_id: str,
    limit: int = 500,
    before_ts: float | None = None,
    after_ts: float | None = None,
    store: BarStore = Depends(get_bar_store),
) -> dict:
    """A bounded window of one bar series' stored candles, verbatim (checksum-verified on load).

    ``before_ts`` serves the LAST ``limit`` rows at or before that epoch-seconds instant;
    ``after_ts`` the FIRST ``limit`` rows at or after it; neither serves the newest ``limit`` rows.
    Both cursors at once is a 422 (they anchor opposite ends — silently picking one would be a lie
    about what was asked). ``limit`` outside ``1..5000`` is a 422 rather than a silent clamp.
    ``has_more_before`` / ``has_more_after`` say honestly whether stored rows exist outside the
    served window on that side, so a caller knows when to stop paging. Unknown id -> 404; a
    corrupted/tampered file -> an explicit 500 (never a fabricated or partial series) — the SAME
    taxonomy the detail route above uses."""
    if limit < 1 or limit > _MAX_CANDLE_LIMIT:
        raise HTTPException(
            status_code=422, detail=f"limit must be between 1 and {_MAX_CANDLE_LIMIT}"
        )
    if before_ts is not None and after_ts is not None:
        raise HTTPException(
            status_code=422,
            detail="pass at most one of before_ts / after_ts — they anchor opposite ends",
        )
    try:
        meta = store.get(bar_series_id, include_bars=False)
        rows, has_more_before, has_more_after = store.candles(
            bar_series_id, before_ts=before_ts, after_ts=after_ts, limit=limit
        )
    except BarSeriesNotFound:
        raise HTTPException(status_code=404, detail=f"no bar series with id '{bar_series_id}'")
    except BarSeriesIntegrityError as exc:
        raise HTTPException(status_code=500, detail=f"bar series integrity check failed: {exc}")
    return {
        "bar_series_id": bar_series_id,
        "symbol": meta.get("symbol"),
        "timeframe": meta.get("timeframe"),
        "bar_count": meta.get("bar_count"),
        "bars": rows,
        "has_more_before": has_more_before,
        "has_more_after": has_more_after,
    }


# The MERGED candle read — the same bounded window, but over every recorded series for one
# (symbol, timeframe) instead of one series id. A symbol accumulates many overlapping immutable
# recordings, so a chart paging a single series runs out of history while a longer recording of the
# same symbol/timeframe sits on disk; this is the view that lets a zoomed-out chart keep filling.
# The fold (dedupe by timestamp, most-recently-created series wins a disagreement, disagreements
# counted) is owned by `BarStore.merged_candles` — this route parses/validates query params and
# serves that method's output verbatim, exactly as the per-series route above does.
#
# Deliberately a TOP-LEVEL `/research/candles` path rather than `/research/bars/candles`: the latter
# would sit in the same segment position as `/bars/{bar_series_id}` and be resolved by declaration
# order — a silent, order-dependent trap for anyone who later reorders these routes.


@router.get("/candles")
def get_merged_candles(
    symbol: str,
    timeframe: str,
    limit: int = 500,
    before_ts: float | None = None,
    after_ts: float | None = None,
    store: BarStore = Depends(get_bar_store),
) -> dict:
    """A bounded window of one symbol+timeframe's recorded candles, merged across every registered
    series for that pair (each file checksum-verified on load), served verbatim.

    Cursor/limit semantics and the ``has_more_before`` / ``has_more_after`` flags are IDENTICAL to
    ``GET /research/bars/{id}/candles`` (see that route) — only the row source differs. ``symbol`` is
    normalized the same way the record path stores it (stripped + uppercased); ``timeframe`` is
    stripped. ``series_count`` / ``series_ids`` name every recording that contributed;
    ``revised_timestamps`` counts the timestamps where two recordings disagreed on values (a
    vendor revision between fetches — resolved in favour of the most recently created series and
    reported here, never silently hidden); ``bar_count`` is the merged total available behind this
    window. A symbol+timeframe with nothing recorded is an honest empty payload (``bars: []``,
    ``series_count: 0``), never a 404 — the absence of a recording is a fact, not an error. A
    corrupted file is surfaced in ``integrity_errors`` and excluded from the merge, exactly as
    ``GET /research/bars`` surfaces it."""
    if limit < 1 or limit > _MAX_CANDLE_LIMIT:
        raise HTTPException(
            status_code=422, detail=f"limit must be between 1 and {_MAX_CANDLE_LIMIT}"
        )
    if before_ts is not None and after_ts is not None:
        raise HTTPException(
            status_code=422,
            detail="pass at most one of before_ts / after_ts — they anchor opposite ends",
        )
    if not symbol.strip() or not timeframe.strip():
        raise HTTPException(status_code=422, detail="symbol and timeframe must both be non-empty")
    rows, has_more_before, has_more_after, meta = store.merged_candles(
        symbol, timeframe, before_ts=before_ts, after_ts=after_ts, limit=limit
    )
    return {
        "symbol": symbol.strip().upper(),
        "timeframe": timeframe.strip(),
        "bars": rows,
        "bar_count": meta["bar_count"],
        "series_count": len(meta["series_ids"]),
        "series_ids": meta["series_ids"],
        "revised_timestamps": meta["revised_timestamps"],
        "has_more_before": has_more_before,
        "has_more_after": has_more_after,
        "integrity_errors": meta["integrity_errors"],
    }


# --- Deterministic support/resistance levels + confluence zones (era-4 capabilities 2 + 3, J-02 +
# J-03) -------------------------------------------------------------------------------------------
# ONE route: GET /research/levels?symbol=<S>&as_of=<ISO-T>. The S/R module (research/levels.py) is
# the sole computer of levels AND their confluence zones/A-B-C classes; this route only
# parses/validates the query params and serves the module's output VERBATIM (single source of
# truth -- the MCP `levels` tool proxies this byte-identically; no second computation path).
# `confluence_zones` (J-03) is now an additive field beside `levels` / `no_bar_series_for_symbol` --
# no route-body change was needed since the route already spreads `compute_levels`'s dict verbatim.


@router.get("/levels")
def get_levels(symbol: str, as_of: str, store: BarStore = Depends(get_bar_store)) -> dict:
    """Deterministic, lookahead-free support/resistance levels, PLUS their confluence zones and
    A/B/C conviction classes (J-02 + J-03), for ``symbol`` as of ``as_of``. ``symbol``/``as_of``
    are both REQUIRED query params (FastAPI 422s a missing one before this body runs); an empty
    ``symbol`` or a malformed ``as_of`` are explicit 422s here (never a silent "now" default,
    which would leak lookahead). A symbol with no recorded bar series at all, and a symbol with
    series but nothing derivable at this instant, are TWO distinct honest states -- see
    ``compute_levels``' ``no_bar_series_for_symbol`` flag -- never one ambiguous bare empty
    ``levels`` array; ``confluence_zones`` is ``[]`` in both cases (never fabricated)."""
    if not symbol:
        raise HTTPException(status_code=422, detail="a levels query requires a symbol")
    try:
        as_of_epoch = parse_utc_epoch(as_of)
    except ValueError:
        raise HTTPException(status_code=422, detail="as_of must be an ISO date-time")
    normalized_symbol = symbol.strip().upper()
    result = compute_levels(store, normalized_symbol, as_of_epoch, CONFIG)
    return {"symbol": normalized_symbol, "as_of": as_of, **result}


# --- The tradable level map (era-5B capability 1, J-01) ----------------------------------------
# ONE route: GET /research/tradability?symbol=<S>&as_of=<ISO-T>. ``research/tradability.py`` is the
# sole computer of the tradable level map -- a LENS over ``compute_levels``' frozen output (never a
# second levels engine); this route only parses/validates the query params and serves the module's
# output VERBATIM (single source of truth -- the MCP `tradability` tool proxies this
# byte-identically; no second computation path). Mirrors ``get_levels`` immediately above
# byte-for-byte in structure (parse-ISO-once-then-return-verbatim).


@router.get("/tradability")
def get_tradability(symbol: str, as_of: str, store: BarStore = Depends(get_bar_store)) -> dict:
    """The tradable level map (bands: price range, side, quality score, member levels,
    round-number flag, inherited A/B/C class) for ``symbol`` as of ``as_of``, computed under
    morning-markup as-of discipline from the frozen ``compute_levels`` output. ``symbol``/``as_of``
    are both REQUIRED query params (FastAPI 422s a missing one before this body runs); an empty
    ``symbol`` or a malformed ``as_of`` are explicit 422s here (never a silent "now" default, which
    would leak lookahead) -- the identical ``get_levels`` discipline. A symbol with no recorded bar
    series at all, and a symbol with series but nothing derivable (no daily series to resolve a
    basis from, or no prior session yet), are honest distinct states -- see
    ``compute_tradability``'s ``no_bar_series_for_symbol`` flag and ``basis_as_of`` (``null`` when
    no basis could be resolved) -- never one ambiguous bare empty ``bands`` array.

    Served through the durable ``TradabilityCache`` (this route is its ONLY caller): the key is
    (symbol, ``basis_day_key(as_of)``, this symbol's own store signature, whole-config content
    hash), so a repeat of an already-computed session is a ~10ms read that survives restarts,
    while ANY new/changed recording of the symbol, any config-content change, or an algorithm
    version bump recomputes through the unchanged ``compute_tradability`` path — byte-identical
    either way (the cache stores the module result verbatim; the ``as_of`` echo below is applied
    per-request, so same-UTC-day requests share one row yet each echoes its own instant). The
    cache DB lives beside the INJECTED store's own root (``resolve_tradability_cache_db_path``),
    so a test store under ``tmp_path`` gets a hermetic cache for free — the ``SetupsScanCache``
    property ``conftest.py`` documents."""
    if not symbol:
        raise HTTPException(status_code=422, detail="a tradability query requires a symbol")
    try:
        as_of_epoch = parse_utc_epoch(as_of)
    except ValueError:
        raise HTTPException(status_code=422, detail="as_of must be an ISO date-time")
    normalized_symbol = symbol.strip().upper()
    records, _integrity_errors = store.list()
    cache = TradabilityCache(resolve_tradability_cache_db_path(str(store.root)))
    cache_key = tradability_cache_key(
        symbol=normalized_symbol,
        basis_day=basis_day_key(as_of_epoch),
        store_signature=symbol_store_signature(records, normalized_symbol),
        config_content_hash=_config_content_hash(CONFIG),
    )
    result = cache.lookup(cache_key)
    if result is None:
        result = compute_tradability(store, normalized_symbol, as_of_epoch, CONFIG)
        cache.publish(cache_key, result)
    return {"symbol": normalized_symbol, "as_of": as_of, **result}


# --- The touch-event scanner + case-study registry (era-5B capability 2, J-02) ------------------
# TWO routes (list + detail, the ``/datasets``/``/bars`` trio's read half): ``research/setups.py``
# is the sole computer of the touch-event/case-registry value -- a scanner over
# ``compute_tradability``'s frozen output (never a second map/levels computation); these routes
# only parse/validate the optional filter params and serve the module's output VERBATIM (single
# source of truth -- the MCP `setups` tool proxies the UNFILTERED list byte-identically; no second
# computation path). Unlike ``get_levels``/``get_tradability`` immediately above, NEITHER route
# takes a required ``symbol``/``as_of`` -- the scan itself already walks every config-owned panel
# symbol and every session in its stored ``"5m"`` series, so ``GET /research/setups`` takes no
# required params at all (the ``list_bar_series`` optional-filter shape, era-5 J-03).

_VALID_REACTIONS = (REJECTED, BROKE, CHOPPED)
_VALID_BAND_CLASSES = ("A", "B", "C")


@router.get("/setups")
def list_setups(
    symbol: str | None = None,
    reaction: str | None = None,
    band_class: str | None = None,
    store: BarStore = Depends(get_bar_store),
) -> dict:
    """The touch-event/case-study registry (J-02): every band-touch event ``compute_setups`` finds
    across the config-owned 12-symbol panel's stored ``"5m"`` bars, served VERBATIM -- one scan,
    filtered in-memory (never a second, per-filter computation). Filters (``symbol`` / ``reaction``
    / ``band_class``) are server-side and AND-combined when more than one is given.

    ``reaction`` and ``band_class`` are FIXED enums: an unknown value is an explicit 422, never
    silently coerced (the ``list_journal`` ``setup_type``/``direction``/``resolution``/``status``
    discipline). ``symbol`` is free-form (the ``ticker`` precedent): a blank ``?symbol=`` normalizes
    to ABSENT (the ``list_bar_series`` era-5 J-05 audit-fixed precedent -- taking the exact same
    byte-identical no-filter path as a true no-param call), and a well-formed but unmatched symbol
    honestly returns zero events, never an error (the ``no_bar_series_for_symbol`` analog: a symbol
    outside the panel, or one with no stored bars yet, simply never emits any event)."""
    if reaction is not None and reaction not in _VALID_REACTIONS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown reaction filter '{reaction}' -- valid reactions are {list(_VALID_REACTIONS)}",
        )
    if band_class is not None and band_class not in _VALID_BAND_CLASSES:
        raise HTTPException(
            status_code=422,
            detail=f"unknown band_class filter '{band_class}' -- valid classes are {list(_VALID_BAND_CLASSES)}",
        )
    normalized_symbol = symbol.strip().upper() if symbol else None

    events = compute_setups(store, CONFIG)["events"]
    if normalized_symbol is not None:
        events = [e for e in events if e["symbol"] == normalized_symbol]
    if reaction is not None:
        events = [e for e in events if e["reaction"] == reaction]
    if band_class is not None:
        events = [e for e in events if e["band"]["class"] == band_class]
    return {"events": events}


@router.get("/setups/{setup_id}")
def get_setup(
    setup_id: str,
    store: BarStore = Depends(get_bar_store),
    dataset_store: DatasetStore = Depends(get_dataset_store),
) -> dict:
    """One touch event's drill-in -- band, reaction, forward returns, and the ``tape_timeline``
    field, served VERBATIM. 404 for an unknown id (never a fabricated event). The tape join
    (era-5B J-03) happens ONLY here, never inside ``compute_setups``'s shared scan loop
    (``list_setups`` above stays byte-identical, unenriched): a recorded ``DatasetStore`` dataset
    whose window covers this event's ``touch_ts`` is replayed through the frozen ``TapeEngine`` and
    joined onto ``tape_timeline``; an event with no recorded dataset keeps it honestly empty."""
    events = compute_setups(store, CONFIG)["events"]
    event = next((e for e in events if e["id"] == setup_id), None)
    if event is None:
        raise HTTPException(status_code=404, detail=f"no setup event with id '{setup_id}'")
    event = enrich_with_tape_timeline(event, dataset_store, CONFIG)
    return {"event": event}


# --- Deterministic backtests (era-3 capability 4, J-03) --------------------------------------------
# Exactly FOUR routes (Product Shape): create+start, list, detail, cancel — mirroring studies.
# The backtest runner (app/research/backtests.py) is Data Contract row 31's single computer; these
# routes serve its persisted payloads VERBATIM (never recomputed at read; the MCP ``backtests``
# tool proxies the list byte-identically). Validation is honest and distinct: unknown dataset id
# -> 404-style refusal; unknown strategy id -> 422 (only the registered v1 exists); an
# UNREGISTERED profile -> 422 (``Config.profile_definition`` — the SAME registry
# ``GET /research/profiles`` lists, J-06 — never a second allowlist); malformed body -> 422 at the
# schema layer.


@router.post("/backtests")
def create_backtest(
    body: BacktestRequest,
    registry: ResearchRegistry = Depends(get_registry),
    store: DatasetStore = Depends(get_dataset_store),
    bar_store: BarStore = Depends(get_bar_store),
    withheld_ids: frozenset[str] = Depends(get_withheld_dataset_ids),
) -> dict:
    """Create + START a deterministic backtest job (J-03; era-4 J-04 adds the additive
    ``structure_tape`` strategy) over one registered dataset under ``default`` or a registered
    candidate profile (J-06). On success the job is persisted ``queued`` with its identity stamps
    (request echo, recorded null-baseline seed, config fingerprint of the RESOLVED per-run profile
    config) and started as a cancellable background job; the queued payload is returned. Nothing
    is persisted on any rejection. ``bar_store`` (era-4 J-04) is threaded through to the runner
    exactly like ``store`` (the dataset store) — v1 ignores it; ``structure_tape`` reads it for
    the row-39 levels its entries arm against."""
    # 422 — only a REGISTERED strategy exists (never a silently-coerced default strategy).
    if registry.config.strategy_definition(body.strategy_id) is None:
        known_strategies = [s["strategy_id"] for s in registry.config.strategy_registry()]
        raise HTTPException(
            status_code=422,
            detail=(
                f"unknown strategy_id '{body.strategy_id}' — the registered strategies are "
                f"{known_strategies}"
            ),
        )
    # 422 — the profile must be REGISTERED (Config.profile_definition — the ONE registry this
    # route and GET /research/profiles both consult; never a second allowlist). ``default`` is
    # always registered; a candidate is registered iff profile_definition returns non-None.
    if registry.config.profile_definition(body.profile) is None:
        known = [p["id"] for p in registry.config.profile_registry()]
        raise HTTPException(
            status_code=422,
            detail=f"unknown profile '{body.profile}' — the registered profiles are {known}",
        )
    # 403 — a sealed shard is never READ (spec §7.5/§7.4 and the era's own *(critical)* anti-goal:
    # "Event data and outcome aggregates of a `sealed` shard are refused everywhere ... fail-
    # closed"). A backtest is exactly an outcome aggregate over a dataset's events, and its
    # RESULT re-publishes the dataset's full manifest through `GET /research/backtests` and
    # `GET /research/pnl/ledger` — so this refusal is what keeps those two surfaces provably clean
    # for a sealed shard (TR-2's sweep asserts both). Checked before the dataset is even opened.
    if body.dataset_id in withheld_ids:
        raise HTTPException(
            status_code=403, detail=str(vault.SealedShardWithheldError(body.dataset_id))
        )
    # 404-style — the dataset must exist (a checksum-verified load; never a fabricated dataset).
    try:
        store.get(body.dataset_id)
    except DatasetNotFound:
        raise HTTPException(status_code=404, detail=f"no dataset with id '{body.dataset_id}'")
    except DatasetIntegrityError as exc:
        raise HTTPException(status_code=500, detail=f"dataset integrity check failed: {exc}")

    jobs = registry.backtest_jobs
    payload = jobs.create(
        {"dataset_id": body.dataset_id, "strategy_id": body.strategy_id, "profile": body.profile}
    )
    jobs.start(payload["id"], dataset_store=store, bar_store=bar_store)
    return {"backtest": payload}


@router.get("/backtests")
def list_backtests(registry: ResearchRegistry = Depends(get_registry)) -> dict:
    """List backtests most-recent-first (capped at the serving-only ``backtest_list_max``).
    Each row is the runner's persisted payload, served VERBATIM (never recomputed). The MCP
    ``backtests`` tool proxies this byte-for-byte."""
    records = registry.store.list_backtests(limit=registry.config.backtest_list_max)
    return {"backtests": [r.payload for r in records]}


@router.get("/backtests/{backtest_id}")
def get_backtest(
    backtest_id: str, registry: ResearchRegistry = Depends(get_registry)
) -> dict:
    """One backtest's status + stored report, served VERBATIM. 404 for an unknown id."""
    record = registry.store.get_backtest(backtest_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"no backtest with id '{backtest_id}'")
    return {"backtest": record.payload}


@router.post("/backtests/{backtest_id}/cancel")
def cancel_backtest(
    backtest_id: str, registry: ResearchRegistry = Depends(get_registry)
) -> dict:
    """Cancel a running/queued backtest (J-03, mirroring studies). 404 unknown id; 409 if the
    backtest is already terminal (done / cancelled / failed). Cancellation is cooperative — the
    running job observes it between events and resolves to explicit ``cancelled`` WITHOUT a
    result block (a partially computed simulated PnL is never served)."""
    record = registry.store.get_backtest(backtest_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"no backtest with id '{backtest_id}'")
    status = record.payload.get("status")
    if status in BACKTEST_TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409, detail=f"backtest '{backtest_id}' is already {status} — cannot cancel"
        )
    registry.backtest_jobs.cancel(backtest_id)
    return {"backtest_id": backtest_id, "cancelling": True}


# --- The PnL ledger (era-3 capability 5, J-04) ------------------------------------------------------
# Exactly ONE route, GET only (Product Shape): the ledger has NO REST write surface — rows are
# appended solely by the validation path (today the founding-baseline seeding CLI), so any non-GET
# verb on the path is FastAPI's default 405 (no handler exists). The route serves the stored rows
# VERBATIM through the ONE ``ledger_projection`` read (app/research/pnl_ledger.py) — the same
# function the committed markdown render walks, and the surface the MCP ``pnl_ledger`` tool
# proxies byte-identically (Data Contract row 32: one computation, every surface reads it).


@router.get("/pnl/ledger")
def get_pnl_ledger(registry: ResearchRegistry = Depends(get_registry)) -> dict:
    """The append-only PnL ledger (J-04): every stored row verbatim, in append order, wrapped
    with the visible simulated register and the config-owned ``insufficient_sample`` labels
    (``n`` always present). An empty ledger is an honest 200 empty list — never an error."""
    return ledger_projection(registry.store, registry.config)


# --- Indicator profiles + champion pointer (Data Contract row 33; J-05 shipped the serving side,
# J-06 registers the first candidate, J-07 turns the champion into a real persisted pointer) --------
# Exactly ONE route, GET only: the registry is config-owned and the champion pointer is read
# VERBATIM from the ONE persisted store source (app/research/profiles.py), so there is NO write
# surface on THIS route — any non-GET verb is FastAPI's default 405 (no handler exists). J-07's
# pnl_scan.py is the only code that may ever move the champion (a hold-out survivor).


@router.get("/profiles")
def get_profiles(registry: ResearchRegistry = Depends(get_registry)) -> dict:
    """The profile registry (``default`` plus every registered candidate) + the current champion
    pointer — the founding strategy ``v1`` on profile ``default`` until a genuine hold-out
    survivor moves it (J-07) — served verbatim from the ONE projection. The J-05 champion summary
    and the MCP ``get_endpoint`` proxy read THIS — never an inferred or duplicated copy."""
    return profiles_projection(registry.store, registry.config)


# --- The strategy registry + champion pointer (Data Contract row 40; era-4 capability 4, J-04) ------
# Exactly ONE route, GET only, mirroring ``GET /research/profiles`` above verbatim: the registry is
# config-owned (``v1`` + the additive ``structure_tape``) and the champion pointer is read VERBATIM
# from the SAME persisted store source ``profiles_projection`` reads (app/research/strategies.py) —
# never a second champion source. No write surface exists on this route — any non-GET verb is
# FastAPI's default 405. A hold-out promotion (J-06, out of scope this iteration) is the only future
# path that ever moves the champion.


@router.get("/strategies")
def get_strategies(registry: ResearchRegistry = Depends(get_registry)) -> dict:
    """The strategy registry (``v1`` plus the additive ``structure_tape``, in registration order)
    + the current champion pointer — the founding strategy ``v1`` on profile ``default`` until a
    genuine hold-out survivor moves it (J-06) — served verbatim from the ONE projection, reading
    the SAME single ``store.get_champion_pointer()`` source ``GET /research/profiles`` reads."""
    return strategies_projection(registry.store, registry.config)


# --- The 3-way strategy-comparison edge report (era-5B capability 6, J-04; Data Contract row
# "edge-report cells") ---------------------------------------------------------------------------
# Exactly ONE route, GET only, mirroring ``GET /research/strategies`` immediately above in shape:
# ``research/edge_report.py``'s ``peek_strategy_comparison_report`` (era-fast_wall J-01) is the
# SOLE computer this route calls; this route only wires the four existing dependency seams
# (journal store, dataset store, bar store, cache) and serves the module's output VERBATIM (the
# MCP ``edge_report`` tool proxies this byte-identically; no second computation path). J-01: a GET
# NEVER computes the sweep — a cold cache key on a non-empty registry returns the honest
# ``status: "not_computed"`` payload instead of starting it; only the future operator/CLI compute
# (J-04) ever calls ``run_strategy_comparison_report``'s always-compute path. No write surface
# exists on this route — any non-GET verb is FastAPI's default 405. This route never reads or
# moves the champion pointer — see the module's own "no champion, no promotion" docstring.


@router.get("/edge-report")
def get_edge_report(
    registry: ResearchRegistry = Depends(get_registry),
    dataset_store: DatasetStore = Depends(get_dataset_store),
    bar_store: BarStore = Depends(get_bar_store),
    cache: EdgeReportCache = Depends(get_edge_report_cache),
) -> dict:
    """The 3-way strategy-comparison report (``v1`` / ``structure_tape`` / ``structure_tape_map``)
    aggregated into per strategy x class x side x reaction x feed cells over every registered
    event-window dataset that resolves an owning, classified scan event — served VERBATIM from
    ``peek_strategy_comparison_report`` (era-fast_wall J-01; the rebuildable result cache DI-wired
    through the SAME seam shape ``get_bar_index`` uses). era-fast_wall J-01: this GET NEVER
    computes the sweep — a warm cache key answers instantly with the report; a cold key on a
    non-empty registry answers instantly too, with the honest ``status: "not_computed"`` payload,
    rather than starting the multi-hour compute inside this request. An empty dataset registry
    keeps the pre-J-01 O(1), zero-backtest full-report shape. A dataset failing integrity
    verification aborts the whole report with an explicit 500 (the ``create_backtest``/
    ``EdgeReportError`` precedent) — partial results are never served, and never cached. An
    all-empty or all-``insufficient_sample`` WARM report is a valid 200, never an error.

    era-fast_wall J-04: the not-computed payload's ``compute`` field is now the registry's compute
    manager's OWN current/last snapshot (``registry.edge_report_compute.snapshot()`` — replacing
    J-01's always-``None`` placeholder) — the SAME snapshot ``GET /research/edge-report/compute``
    itself serves (TC-8), read here through the SAME already-injected ``registry``, no second
    store/manager construction path."""
    try:
        return peek_strategy_comparison_report(
            registry.store, dataset_store, bar_store, registry.config, cache=cache,
            compute=registry.edge_report_compute.snapshot(),
        )
    except EdgeReportError as exc:
        raise HTTPException(status_code=500, detail=f"edge report could not complete: {exc}")


# --- The operator-run compute (era-fast_wall J-04) — three subpaths of the section above ---------
# ``POST /research/edge-report/compute`` (single-flight trigger), ``GET /research/edge-report/
# compute`` (poll the snapshot), ``POST /research/edge-report/compute/cancel`` (409 when idle).
# Resolved through the SAME FOUR existing dependency seams ``get_edge_report`` above already uses
# (``get_registry``/``get_dataset_store``/``get_bar_store``/``get_edge_report_cache``) — no second
# store/cache construction path anywhere. These are SUBPATHS of ``/edge-report``, so non-GET verbs
# on ``/research/edge-report`` itself remain structurally unaffected (FastAPI's default 405 stands
# — no handler exists for them, exactly as before this iteration). No MCP tool is added for this
# surface (the critical "No MCP write surface" anti-goal) — ``app/mcp/__init__.py`` is untouched.


@router.post("/edge-report/compute")
def trigger_edge_report_compute(
    body: EdgeReportComputeRequest,
    registry: ResearchRegistry = Depends(get_registry),
    dataset_store: DatasetStore = Depends(get_dataset_store),
    bar_store: BarStore = Depends(get_bar_store),
    cache: EdgeReportCache = Depends(get_edge_report_cache),
    sub_cache: EdgeReportBacktestCache = Depends(get_edge_report_backtest_cache),
) -> dict:
    """Start the single-flight edge-report compute job, or — if one is already running — return it
    UNCHANGED (``started: False``, never a second concurrent job). Returns
    ``{"started": bool, "compute": <snapshot>}``; the actual sweep runs on a background worker
    thread, off this request (``EdgeReportComputeManager.trigger`` — the ``create_backtest``/
    ``jobs.start`` precedent), so this route returns immediately regardless of how long the sweep
    takes.

    era-fast_wall J-05: also injects the durable per-pair sub-cache
    (``get_edge_report_backtest_cache``), threaded into ``trigger()`` so a browser-triggered
    compute is resumable too — a killed-and-retriggered job skips already-published pairs."""
    return registry.edge_report_compute.trigger(
        registry.store, dataset_store, bar_store, registry.config, cache,
        force=body.force, sub_cache=sub_cache,
    )


@router.get("/edge-report/compute")
def get_edge_report_compute(registry: ResearchRegistry = Depends(get_registry)) -> dict | None:
    """The compute job's current/last snapshot, served VERBATIM — or ``null`` if no compute has
    ever run this process. The SAME snapshot embedded as the not-computed edge-report payload's
    ``compute`` field (TC-8) — one owner (``EdgeReportComputeManager``), one read
    (``registry.edge_report_compute.snapshot()``), two callers."""
    return registry.edge_report_compute.snapshot()


@router.post("/edge-report/compute/cancel")
def cancel_edge_report_compute(registry: ResearchRegistry = Depends(get_registry)) -> dict:
    """Cancel the in-flight edge-report compute (cooperative — observed between dataset x strategy
    pairs; a cancelled run publishes NOTHING to the edge-report cache, by construction — see
    ``EdgeReportComputeCancelled``'s own docstring). ``409`` when idle (no job has ever run, or the
    last job already reached a terminal state) — mirrors ``cancel_backtest``'s own 409-when-
    terminal shape."""
    snapshot = registry.edge_report_compute.snapshot()
    if snapshot is None or snapshot["state"] != "running":
        raise HTTPException(status_code=409, detail="no edge-report compute is currently running")
    registry.edge_report_compute.cancel()
    return {"cancelling": True}
