"""The ``/research/*`` REST namespace (capabilities 23 / 24) — declare + read a thesis, taxonomy.

Endpoints this iteration:
  * ``GET  /research/taxonomy``            — the single backend owner of every research label.
  * ``POST /research/thesis``              — declare a thesis with HONEST validation (404/409/422).
  * ``GET  /research/thesis/active``       — the canonical thesis projection (``null`` is normal).

Validation is never silent coercion: a not-watched ticker is 404, a second active thesis is 409,
and every incoherent input (wrong-side invalidation, missing/forbidden level, unknown enums) is a
422 — with NOTHING persisted on rejection. On success the entry context + expected-behaviour
statements are frozen, the thesis is bound to its SOURCE IDENTITY (the snapshot's scenario
descriptor, never the bare ticker), stamped with bound source + ``data_feed`` + ``config_fingerprint``,
and the initial ``pending`` verdict event is appended (the timeline starts here).

The router depends on the app-provided ``ResearchRegistry`` (which owns the journal store and the
per-ticker monitors) via FastAPI dependency-injection, so tests inject a temp-path store + a test
WatchManager through ``dependency_overrides`` exactly like the market-adapter seam.
"""

from __future__ import annotations

import math
import os
import time
import uuid

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
from .analytics import compute_analytics
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
)
from .levels import compute_levels
from .tradability import compute_tradability
from .datasets import (
    VALID_SOURCE_KINDS as DATASET_SOURCE_KINDS,
    VALID_SPLITS,
    DatasetAlreadyRegistered,
    DatasetIntegrityError,
    DatasetNotFound,
    DatasetRecordError,
    DatasetStore,
    EmptyWindowError,
    parse_utc_epoch,
    record_from_source,
)
from .excursions import compute_and_persist_excursions
from .execution_checks import compute_and_persist_execution_checks
from .grades import compute_and_persist_grades
from .marks import marks_projection
from .monitor import (
    ResearchMonitor,
    build_projection,
    compute_and_persist_final_statuses,
    compute_risk_flags,
)
from .pnl_ledger import ledger_projection
from .profiles import profiles_projection
from .strategies import strategies_projection
from .feed_basis import data_feed_for_scenario
from .journal_rows import journal_row
from .store import ActionRecord, JournalStore, ThesisRecord, VerdictEventRecord
from .studies import (
    REFERENCE_SOURCE_ID,
    SOURCE_HISTORICAL,
    SOURCE_REFERENCE,
    SOURCE_SIM,
    TERMINAL_STATUSES as STUDY_TERMINAL_STATUSES,
    StudyJobManager,
)
from .taxonomy import not_evaluated_notice
from .taxonomy import (
    MISTAKE_TAGS_REQUIRING_NOTE,
    frozen_statements,
    is_valid_direction,
    is_valid_mistake_tag,
    is_valid_setup,
    setup_requires_level,
    taxonomy_payload,
)

router = APIRouter(prefix="/research", tags=["research"])


# The terminal statuses a thesis can carry. A USER may set only ``played_out`` / ``abandoned`` via
# the resolve endpoint; ``invalidated`` / ``expired`` are SYSTEM-owned (the verdict engine / the
# lifecycle path own them) and a request for either is a 422. Any status in this set means the thesis
# is already resolved (a second resolve is a 409).
_USER_RESOLUTIONS = ("played_out", "abandoned")
_SYSTEM_RESOLUTIONS = ("invalidated", "expired")
_TERMINAL_STATUSES = (*_USER_RESOLUTIONS, *_SYSTEM_RESOLUTIONS)


class ThesisRequest(BaseModel):
    """Body for ``POST /research/thesis``. ``level_price`` is optional at the schema level — the
    per-setup REQUIRED/FORBIDDEN rule is enforced in the route (a 422), never by the schema, so the
    error message is explicit and taxonomy-owned."""

    ticker: str
    setup_type: str
    direction: str
    invalidation_price: float
    level_price: float | None = None
    # The optional declared-from-hint linkage (capability 33, J-65): when the user declares from a
    # hint's prefill affordance the frontend passes the hint id here. Additive + optional — a normal
    # (non-prefilled) declaration omits it and is unchanged. An unknown/invalid id is a 422 (validated in
    # the route, not the schema, so the message is explicit). The link is recorded on the hint record
    # ONLY when the declaration COMPLETES — one click never creates a thesis.
    declared_from_hint_id: str | None = None


class ResolveRequest(BaseModel):
    """Body for ``POST /research/thesis/{id}/resolve``. ``resolution`` is validated in the route (not
    by the schema) so the message is explicit and the user-vs-system ownership rule is enforced in one
    place: a user may set only ``played_out`` / ``abandoned``; ``invalidated`` / ``expired`` are
    system-owned (422) and an unknown value is also a 422."""

    resolution: str


class ActionRequest(BaseModel):
    """Body for ``POST /research/thesis/{id}/action`` (J-52). ``kind`` (``entry`` | ``exit``) and the
    sign/finiteness of ``price`` are validated in the ROUTE (not the schema) so the message is
    explicit and the verbatim-recording discipline is enforced in one place. ``price`` is typed
    ``float`` so a non-numeric body is a 422 at the schema layer before the route runs."""

    kind: str
    price: float


class StudyRequest(BaseModel):
    """Body for ``POST /research/studies`` (capability 32, J-60). ``source_kind`` (``reference`` |
    ``sim`` | ``historical``) + ``source_id`` (the sim ticker / reference id / the symbol), the setup ×
    direction, an optional ``level_price`` (REQUIRED for the two level setups, FORBIDDEN otherwise),
    and the historical ``start`` / ``end`` window for an arbitrary historical study. All validation is
    enforced in the ROUTE (not the schema) so messages are explicit and taxonomy-owned. An optional
    ``null_baseline_seed`` lets a caller pin the baseline (the committed reference study uses the config
    default so it reproduces in CI)."""

    source_kind: str
    source_id: str = ""
    setup_type: str
    direction: str
    level_price: float | None = None
    start: str | None = None
    end: str | None = None
    null_baseline_seed: int | None = None


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
    in the ROUTE — out-of-set is a 422, never silently coerced), and the UTC ``[start, end)``
    window fetched through the adapter seam (``fetch_bars`` — Yahoo by default, keyless; Alpaca
    stays selectable). Unlike a dataset there is only one source per request, so there is no
    ``source_kind`` here."""

    symbol: str
    timeframe: str
    start: str
    end: str


class ReviewRequest(BaseModel):
    """Body for ``POST /research/thesis/{id}/review`` (J-57). ``mistake_tags`` is the user-CONFIRMED
    tag list (distinct from the machine-SUGGESTED tags); ``note`` is the optional free text (REQUIRED
    only when ``other`` is among the tags). Both rules are enforced in the ROUTE (not the schema) so
    the message is explicit and taxonomy-owned. ``mistake_tags`` defaults to an empty list so a
    body with only a note (or an empty review) is well-formed at the schema layer."""

    mistake_tags: list[str] = []
    note: str | None = None


class ResearchRegistry:
    """Owns the journal store and one ``ResearchMonitor`` per watched ticker.

    Wired to the WatchManager's ``on_engine_created`` hook: each freshly-built engine gets a fresh
    monitor attached at the engine's observer seam. On a re-watch the engine is rebuilt, so a new
    monitor replaces the prior one (the prior engine's ``on_status('closed')`` already expired any
    active thesis during teardown). The routes look a monitor up by ticker to declare/read.
    """

    def __init__(self, store: JournalStore, config: Config) -> None:
        self._store = store
        self._config = config
        self._fingerprint = config.config_fingerprint()
        self._monitors: dict[str, ResearchMonitor] = {}
        # The replay-study background-job manager (capability 32, J-60/J-61). Process-scoped: it owns
        # the cancellable worker threads and runs studies OFF the event loop, persisting through the
        # SAME single writer queue. One per registry (a backend restart loses in-flight jobs — a study
        # left ``running`` from a prior process is surfaced honestly, never silently completed).
        self._study_jobs = StudyJobManager(store, config)
        # The backtest background-job manager (era-3 capability 4, J-03) — the StudyJobManager
        # pattern verbatim: cancellable worker threads OFF the event loop, persistence through the
        # SAME single writer queue, in-flight jobs honestly lost on restart (never silently done).
        self._backtest_jobs = BacktestJobManager(store, config)

    @property
    def store(self) -> JournalStore:
        return self._store

    @property
    def study_jobs(self) -> StudyJobManager:
        return self._study_jobs

    @property
    def backtest_jobs(self) -> BacktestJobManager:
        return self._backtest_jobs

    @property
    def config(self) -> Config:
        return self._config

    def on_engine_created(self, ticker: str, engine: object) -> None:
        """Attach a fresh monitor to a freshly-built engine (the WatchManager hook).

        The monitor is given the engine (so its ``on_status`` can read the terminal ``end_reason``).
        If a SURVIVING entry-marked active thesis exists for this ticker (it was NOT expired on a
        prior stop/restart because it carries a real position, J-47), it is OFFERED to the fresh
        monitor: the monitor adopts it — appending exactly one ``watch_restarted`` gap event and
        resuming evaluation — only once the first snapshot confirms the new watch's source identity
        equals the thesis's ``bound_source`` (a mismatch is never adopted)."""
        monitor = ResearchMonitor(self._store, self._config, ticker)
        monitor.attach_engine(engine)
        self._monitors[ticker] = monitor
        engine.add_observer(monitor)
        # Offer any surviving entry-marked active thesis for re-attach (source match decided at the
        # first snapshot). An unmarked active row would already have been expired on the prior stop /
        # restart sweep, so this only ever finds a genuinely surviving position.
        surviving = self._store.get_active_thesis(ticker)
        if surviving is not None and self._store.has_entry_mark(surviving.id):
            monitor.offer_surviving(surviving)

    def monitor_for(self, ticker: str) -> ResearchMonitor | None:
        return self._monitors.get(ticker)

    def projection_for(self, ticker: str) -> dict | None:
        """The canonical thesis projection for ``ticker`` (``None`` is a normal state).

        The LIVE monitor's projection wins when it serves one (an active live thesis, a resolved
        ``invalidated`` terminal treatment, or a mismatched-source survivor notice). Otherwise — a
        stopped/unwatched ticker — a SURVIVING entry-marked active thesis is served from its
        persisted record via the SAME ``build_projection`` path (data-contract row 15 — never a
        second computation), flagged ``not_evaluated`` with the backend-owned bound-source notice.
        ``None`` remains the answer when nothing survives."""
        monitor = self._monitors.get(ticker)
        if monitor is not None:
            projection = monitor.projection()
            if projection is not None:
                return projection
        return self._surviving_projection(ticker)

    def _surviving_projection(self, ticker: str) -> dict | None:
        """Serve a surviving entry-marked active thesis (unwatched) as not-evaluated, or ``None``.

        Built from the persisted ``active`` record via the ONE shared ``build_projection`` — no live
        snapshot (statements read ``not_yet``; an unwatched survivor accrues no new status), the
        ``not_evaluated`` monitor status, and the backend-owned plain-language notice naming the
        bound source. A non-entry-marked active row never reaches here (it was expired on stop /
        restart), so this only ever surfaces a genuinely surviving position."""
        surviving = self._store.get_active_thesis(ticker)
        if surviving is None or not self._store.has_entry_mark(surviving.id):
            return None
        return build_projection(
            surviving,
            self._store.get_actions(surviving.id),
            config=self._config,
            snapshot=None,
            status=surviving.status,
            verdict="pending",
            verdict_evidence=(
                "This thesis carries a recorded entry and survives the stopped watch; it is not "
                "being evaluated until its source is watched again."
            ),
            monitor_status="not_evaluated",
            monitor_notice=not_evaluated_notice(surviving.bound_source),
            verdict_events=self._store.verdict_events(surviving.id),
        )

    def hint_projection_for(self, ticker: str) -> dict | None:
        """The canonical active-hint projection for ``ticker`` (capability 33, J-65; ``None`` is a NORMAL
        state). Served from the LIVE monitor's hint engine — a hint exists only on an actively watched
        ticker (no background detection), so an unwatched / not-watched ticker is always ``None`` (never
        an error). Both ``GET /research/hints/active`` and the WS ``hint`` key read THIS one method."""
        monitor = self._monitors.get(ticker)
        if monitor is None:
            return None
        return monitor.hint_projection()

    def startup_sweep(self) -> list[str]:
        """Resolve any thesis left ``active`` in the DB (from a prior process) to ``expired``.

        Each thesis the sweep expires (UNMARKED actives — an entry-marked thesis is exempt and
        survives) has its execution checks, per-statement FINAL statuses (J-55), and outcome × process
        grades (J-56) computed ONCE here and persisted on its row — the SAME single functions every
        other terminal-resolution path calls (capabilities 27/29). An expired unmarked thesis has no
        marks, so its mark-dependent checks read ``not_applicable`` honestly (never a fabricated
        pass/fail). The restart-expiry sweep has NO live engine context (the watch that declared the
        thesis is long gone), so each statement's final status is the explicit ``not_evaluated`` enum
        (``snapshot=None``) — an honest "no read at the terminal moment", never fabricated. The grades
        weigh the just-persisted execution checks, so they run after them (resolution is ``expired``)."""
        expired = self._store.expire_stale_actives(time.time())
        for thesis_id in expired:
            try:
                compute_and_persist_execution_checks(self._store, thesis_id, self._config)
                compute_and_persist_final_statuses(self._store, thesis_id, None, self._config)
                compute_and_persist_grades(self._store, thesis_id, "expired", self._config)
                # Excursions (capability 30, J-58): the restart-expiry sweep has NO in-memory tracker
                # (the watch that declared the thesis is long gone and tape data is never persisted, so
                # the price path cannot be reconstructed). Passing ``tracker=None`` persists the
                # explicit ``not_tracked`` honest marker — never fabricated numbers, never a dishonest
                # zero. The journal detail then renders an explicit not-tracked notice.
                compute_and_persist_excursions(self._store, thesis_id, None)
            except Exception:
                # A computation failure must not abort the sweep (the resolution already stands); the
                # key stays honestly absent for that thesis.
                pass
        return expired


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
    """The setup catalog, enums, and display copy — the single backend owner of research labels.

    Passes the registry's config (when present) so the additive ``sound_cue`` block carries the
    config-owned ``sound_cue_cooldown_seconds`` value (serving-only — the cue is never persisted). The
    taxonomy needs no active watch; with no registry it falls back to the shared default config."""
    registry = get_registry_or_none()
    return taxonomy_payload(registry.config if registry is not None else None)


@router.get("/analytics")
def get_analytics(registry: ResearchRegistry = Depends(get_registry)) -> dict:
    """The segregated journal analytics (capability 31, J-59) — the SINGLE serving path.

    Serves the ``analytics.compute_analytics`` projection VERBATIM (the frontend renders it directly,
    display-rounding only — no client-side arithmetic). Read-only over persisted rows: partitions
    keyed by (``data_feed``, ``config_fingerprint``), per ``setup_type`` × ``direction`` groups, with
    the abandonment bucket always visible and median spread/R beside every +1R figure. NEVER pools
    across feeds or fingerprints; an empty journal serves an honest empty payload (not an error)."""
    return compute_analytics(registry.store, registry._config)


@router.get("/thesis/active")
def get_active_thesis(
    ticker: str, registry: ResearchRegistry = Depends(get_registry)
) -> dict:
    """The canonical thesis projection for ``ticker`` (``thesis: null`` is a NORMAL state).

    Reads the SAME ``monitor.projection()`` the WS ``thesis`` key reads, so the two are
    verbatim-equal by construction (data-contract row 15)."""
    return {"thesis": registry.projection_for(ticker)}


@router.get("/hints/active")
def get_active_hint(
    ticker: str, registry: ResearchRegistry = Depends(get_registry)
) -> dict:
    """The canonical active setup-forming hint projection for ``ticker`` (capability 33, J-65;
    ``hint: null`` is a NORMAL state, not an error — a not-watched ticker, an unclear tape, or a tape
    that has not sustained a pattern past the dwell all read ``null``).

    Reads the SAME ``monitor.hint_projection()`` the WS ``hint`` key reads, so the two are verbatim-equal
    by construction (data-contract row 22). Computed once server-side; rendered verbatim by the dock."""
    return {"hint": registry.hint_projection_for(ticker)}


@router.get("/hints")
def list_hints(
    ticker: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    registry: ResearchRegistry = Depends(get_registry),
) -> dict:
    """The persisted hint log (capability 33, J-65; data-contract row 22 log half) — the ONLY serving
    path for hint-log rows. Reads persisted ``hints`` rows VERBATIM (newest-first) and returns each
    record's stored ``payload`` directly (no recomputation, no second path — the log record IS the dock
    projection by construction). Optionally filtered by ``ticker`` (free-form — an unknown ticker matches
    nothing, never an error).

    Page size is CONFIG-OWNED and serving-only (``hint_log_max``, excluded from ``config_fingerprint``):
    an omitted / non-positive ``limit`` uses ``hint_log_max``; a larger ``limit`` is CLAMPED down to it
    (a serving safety bound, never a 422). ``offset`` paginates (a negative offset normalises to 0 — the
    same lenient convention the journal endpoint uses; malformed non-integer params are a 422 at the
    schema layer before the route runs)."""
    config = registry._config
    if limit is None or limit <= 0:
        effective_limit = config.hint_log_max
    else:
        effective_limit = min(limit, config.hint_log_max)
    effective_offset = max(offset, 0)
    records = registry.store.list_hints(
        ticker=ticker, limit=effective_limit, offset=effective_offset
    )
    return {"rows": [r.payload for r in records]}


# Valid LIST filter enums (J-51). ``status`` accepts the non-terminal ``active`` plus every terminal
# status; ``resolution`` accepts the terminal statuses only (a resolution IS a terminal status).
# Unknown values for any of these → 422 (never silent coercion). ``ticker`` is a free-form symbol, NOT
# an enum, so it is never validated against a fixed set (an unknown ticker just matches nothing).
_LIST_STATUSES = ("active", *_TERMINAL_STATUSES)
_LIST_RESOLUTIONS = _TERMINAL_STATUSES


@router.get("/journal")
def list_journal(
    ticker: str | None = None,
    setup_type: str | None = None,
    direction: str | None = None,
    resolution: str | None = None,
    status: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    registry: ResearchRegistry = Depends(get_registry),
) -> dict:
    """The journal LIST (J-51, data-contract row 21 journal-rows half) — the ONLY serving path for
    journal rows. Reads persisted theses rows VERBATIM via the store's single ``list_theses`` query
    and projects each through the ONE ``journal_row`` builder (no recomputation, no second path).

    Filters (ticker / setup_type / direction / resolution / status) are server-side and AND-combined;
    the frontend does NO client-side filtering. Unknown ENUM filter values (setup_type / direction /
    resolution / status) are a 422 — never silently coerced; ``ticker`` is free-form (an unknown
    ticker matches nothing, never an error). Ordering is newest-declared-first.

    Page size is CONFIG-OWNED and serving-only (excluded from ``config_fingerprint``): an omitted
    ``limit`` uses ``journal_list_default_limit``; a ``limit`` above ``journal_list_max_limit`` is
    CLAMPED down to it (a serving safety bound, never a 422). ``offset`` paginates."""
    config = registry._config

    # 422 — unknown enum filter values (rejected, never coerced). ``ticker`` is intentionally NOT here.
    if setup_type is not None and not is_valid_setup(setup_type):
        raise HTTPException(status_code=422, detail=f"unknown setup_type filter '{setup_type}'")
    if direction is not None and not is_valid_direction(direction):
        raise HTTPException(status_code=422, detail=f"unknown direction filter '{direction}'")
    if resolution is not None and resolution not in _LIST_RESOLUTIONS:
        raise HTTPException(status_code=422, detail=f"unknown resolution filter '{resolution}'")
    if status is not None and status not in _LIST_STATUSES:
        raise HTTPException(status_code=422, detail=f"unknown status filter '{status}'")

    # Config-owned page-size policy (serving-only). An omitted limit uses the default; an over-large
    # limit is clamped to the max. A non-positive limit also falls back to the default (a 0/negative
    # page size is meaningless — honestly serve the default rather than an empty page).
    if limit is None or limit <= 0:
        effective_limit = config.journal_list_default_limit
    else:
        effective_limit = min(limit, config.journal_list_max_limit)
    effective_offset = max(offset, 0)

    theses = registry.store.list_theses(
        ticker=ticker,
        setup_type=setup_type,
        direction=direction,
        resolution=resolution,
        status=status,
        limit=effective_limit,
        offset=effective_offset,
    )
    # The per-row context (verbatim resolution reason + mark presence) in two bulk reads (no N+1).
    context = registry.store.list_row_context([t.id for t in theses])
    rows = [
        journal_row(
            t,
            resolution_reason=context.get(t.id, (None, False, False))[0],
            has_entry=context.get(t.id, (None, False, False))[1],
            has_exit=context.get(t.id, (None, False, False))[2],
        )
        for t in theses
    ]
    return {"rows": rows}


def build_journal_detail(
    store: JournalStore, thesis_id: str, config: Config
) -> dict | None:
    """The single builder for the journal-detail body (J-55) — VERBATIM reads of the persisted record.

    Returns ``None`` when no thesis carries ``thesis_id`` (the route maps that to a 404). Every value
    is a read of an already-persisted record — the thesis row, the action marks + realized-R (via the
    SAME single ``marks_projection`` the row-15 strip projection uses), the frozen entry risk flags,
    the append-only verdict timeline, and the execution checks + suggested mistake tags computed ONCE
    at resolution. NOTHING is recomputed at read (single-source-of-truth + the data-contract row-19
    execution-checks half) — in particular the execution checks are served from the persisted thesis
    row, NEVER recomputed here.

    Honest-omission (the established absent-vs-empty discipline):
      * ``risk_flags`` — present only when the thesis was risk-assessed (a pre-v4 thesis omits it);
      * ``execution_checks`` / ``suggested_mistake_tags`` — present only when computed at a terminal
        resolution (a pre-v5 resolution, or an unresolved thesis, omits them — never fabricated/
        backfilled at read).
    """
    thesis = store.get_thesis(thesis_id)
    if thesis is None:
        return None
    events = store.verdict_events(thesis_id)
    # Action marks + realized-R (J-52, data-contract rows 18 & 27) — read back VERBATIM from the
    # persisted action rows via the SAME single ``marks_projection`` the row-15 thesis projection
    # uses, so the journal-detail readback and the strip show identical values (no second path).
    marks = marks_projection(thesis, store.get_actions(thesis_id))
    thesis_payload = {
        "id": thesis.id,
        "ticker": thesis.ticker,
        "setup_type": thesis.setup_type,
        "direction": thesis.direction,
        "invalidation_price": thesis.invalidation_price,
        "level_price": thesis.level_price,
        "status": thesis.status,
        "bound_source": thesis.bound_source,
        "data_feed": thesis.data_feed,
        "config_fingerprint": thesis.config_fingerprint,
        "entry_context": thesis.entry_context,
        "statements": thesis.statements,
        "created_logical_ts": thesis.created_logical_ts,
        "created_wall_ts": thesis.created_wall_ts,
    }
    # The frozen entry risk flags (capability 26, J-49) — re-exposed verbatim from the stored record
    # (row 17: "→ row 15 / journal"). Honest-omission: a pre-v4 thesis (never assessed) carries NULL
    # risk_flags, so the journal detail OMITS the key entirely (never a dishonest empty list).
    if thesis.risk_flags is not None:
        thesis_payload["risk_flags"] = thesis.risk_flags
    detail = {
        "thesis": thesis_payload,
        "marks": marks,
        # The append-only verdict timeline, verbatim. Each row carries its canonical values and the
        # dwell timing record (capability 24) — never interpolated, never recomputed at read.
        "timeline": [
            {
                "logical_ts": e.logical_ts,
                "wall_ts": e.wall_ts,
                "verdict": e.verdict,
                "evidence": e.evidence,
                "tape_state": e.tape_state,
                "confidence": e.confidence,
                "last": e.last,
                "rule_first_true_ts": e.rule_first_true_ts,
                "rule_first_true_price": e.rule_first_true_price,
            }
            for e in events
        ],
    }
    # The machine-derived execution checks + suggested mistake tags (capability 27, J-54) — served
    # VERBATIM from the persisted result computed ONCE at resolution (data-contract row 19). Honest
    # omission: a pre-v5 resolution (or an unresolved thesis) carries NULL execution_checks, so the
    # detail OMITS both keys entirely (never a fabricated pass/fail, never computed at read).
    if thesis.execution_checks is not None:
        detail["execution_checks"] = thesis.execution_checks.get("checks", [])
        detail["suggested_mistake_tags"] = thesis.execution_checks.get(
            "suggested_mistake_tags", []
        )
    # The per-statement FINAL statuses (capability 29, J-55) — served VERBATIM from the persisted list
    # recorded ONCE at resolution (data-contract row 19). Honest omission: a pre-v6 resolution carries
    # NULL, so the detail OMITS the key (the page then renders the frozen statements WITHOUT a
    # final-status badge — never a fabricated/recomputed status). One entry per frozen statement, in
    # statement order (positionally keyed to ``statements``).
    if thesis.statement_final_statuses is not None:
        detail["statement_final_statuses"] = thesis.statement_final_statuses
    # The outcome × process grades (capability 29, J-56) — served VERBATIM from the persisted result
    # computed ONCE at resolution (data-contract row 19). Honest omission: a pre-v6 resolution carries
    # NULL grades, so the detail OMITS the key. ENUM labels only (never a numeric score); the
    # ``process_evidence`` names the checks/flags that drove the process grade (no naked grade).
    if thesis.grades is not None:
        detail["grades"] = thesis.grades
    # The user-CONFIRMED review (capability 29, J-57, data-contract row 28) — served VERBATIM from the
    # persisted record. ``reviewed`` is ALWAYS present (a boolean fact — False until the user saves a
    # review); the confirmed ``review`` (tags + note) is present ONLY once reviewed (honest omission
    # before then). The confirmed tags are distinct from the machine-suggested tags above (row 19).
    detail["reviewed"] = thesis.reviewed
    if thesis.reviewed:
        detail["review"] = {
            "mistake_tags": thesis.review_tags or [],
            "note": thesis.review_note,
        }
    # The per-horizon excursion record (capability 30, J-58, data-contract row 20) — served VERBATIM
    # from the persisted result measured ONCE at the terminal resolution / stream-end. This is the
    # ONLY serving path (no new endpoint, no second computation, no client-side arithmetic). Honest
    # omission: a pre-v7 resolution (or an unresolved thesis) carries NULL excursions, so the detail
    # OMITS the key entirely (never fabricated numbers, never recomputed at read). A measured record
    # carries ``tracked: true`` + the two segregated populations; the restart-sweep marker carries
    # ``tracked: false`` (an explicit honest "not tracked", never a dishonest zero).
    if thesis.excursions is not None:
        detail["excursions"] = thesis.excursions
    return detail


@router.get("/journal/{thesis_id}")
def get_journal_entry(
    thesis_id: str, registry: ResearchRegistry = Depends(get_registry)
) -> dict:
    """The blueprint row-16 registered serving endpoint: a thesis record + its persisted, append-only
    verdict timeline + action marks + frozen risk flags + the machine-derived execution checks
    (computed once at resolution), served VERBATIM from the store (never recomputed at read time).

    404 for an unknown id. The timeline rows are returned in insertion order (the append-only
    sequence) with the canonical per-row values the verdict engine recorded, including the dwell
    timing record (``rule_first_true``). The execution-checks + suggested-tag keys are additive and
    present only post-resolution (honest omission pre-resolution / pre-migration)."""
    detail = build_journal_detail(registry.store, thesis_id, registry._config)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"no thesis with id '{thesis_id}'")
    return detail


@router.post("/thesis")
def declare_thesis(
    body: ThesisRequest,
    registry: ResearchRegistry = Depends(get_registry),
    manager=Depends(get_watch_manager),
) -> dict:
    """Declare a thesis with honest validation — nothing is persisted on any rejection."""
    ticker = body.ticker

    # 404 — the ticker must be actively watched (we freeze the entry context off its live snapshot).
    engine = manager.get(ticker)
    if engine is None:
        raise HTTPException(
            status_code=404, detail=f"Ticker '{ticker}' is not being watched"
        )

    # 422 — unknown enums (rejected, never coerced to a default).
    if not is_valid_setup(body.setup_type):
        raise HTTPException(status_code=422, detail=f"unknown setup_type '{body.setup_type}'")
    if not is_valid_direction(body.direction):
        raise HTTPException(status_code=422, detail=f"unknown direction '{body.direction}'")

    # 422 — the per-setup level requirement (the single authority is the taxonomy).
    requires_level = setup_requires_level(body.setup_type)
    if requires_level and body.level_price is None:
        raise HTTPException(
            status_code=422,
            detail=f"setup '{body.setup_type}' requires a level_price",
        )
    if not requires_level and body.level_price is not None:
        raise HTTPException(
            status_code=422,
            detail=f"setup '{body.setup_type}' does not take a level_price",
        )

    snap = engine.snapshot()
    last = snap.last

    # 422 — wrong-side invalidation (price-impact honesty: a long is invalidated BELOW the current
    # last, a short ABOVE). We need a last price to judge this; without one (cold start) the
    # declaration is premature, so refuse rather than coerce.
    if last is None:
        raise HTTPException(
            status_code=422,
            detail="no last price yet — cannot validate the invalidation against the tape",
        )
    if body.direction == "long" and body.invalidation_price >= last:
        raise HTTPException(
            status_code=422,
            detail="a long thesis's invalidation must be below the current last price",
        )
    if body.direction == "short" and body.invalidation_price <= last:
        raise HTTPException(
            status_code=422,
            detail="a short thesis's invalidation must be above the current last price",
        )

    # 409 — at most one active thesis per ticker.
    monitor = registry.monitor_for(ticker)
    if monitor is not None and monitor.active_thesis_id is not None:
        raise HTTPException(
            status_code=409, detail=f"an active thesis already exists for '{ticker}'"
        )
    if registry.store.get_active_thesis(ticker) is not None:
        raise HTTPException(
            status_code=409, detail=f"an active thesis already exists for '{ticker}'"
        )

    # 422 — an unknown/invalid declared-from hint id (capability 33, J-65). Validated only when present;
    # a normal (non-prefilled) declaration omits it. Checked AFTER the other validations so an otherwise
    # incoherent declaration still reports its primary error; the link is recorded later (on completion).
    if body.declared_from_hint_id is not None:
        if registry.store.get_hint(body.declared_from_hint_id) is None:
            raise HTTPException(
                status_code=422,
                detail=f"unknown declared_from_hint_id '{body.declared_from_hint_id}'",
            )

    # --- All validation passed — freeze, bind, stamp, persist, attach -----------------------------
    config = registry._config
    primary = snap.primary_features
    entry_context = {
        "tape_state": snap.tape_state,
        "confidence": snap.confidence,
        "last": last,
        "spread": snap.spread,
        "primary_window": snap.primary_window,
        "features": {k: primary[k] for k in sorted(primary.keys())},
    }
    statements = frozen_statements(body.setup_type, body.direction)
    # Entry risk flags (capability 26, J-49): computed ONCE here — AFTER all validation passes, so an
    # incoherent declaration (wrong-side invalidation / missing-or-forbidden level / unknown enum) is
    # a 422 with NO flag ever computed or persisted (advisory, never a substitute for validation). The
    # frozen list (possibly empty) is stored verbatim and re-exposed by the single ``build_projection``
    # — never recomputed at read, never a second computation path.
    risk_flags = compute_risk_flags(
        snap,
        setup_type=body.setup_type,
        direction=body.direction,
        invalidation_price=body.invalidation_price,
        statements=statements,
        config=config,
    )
    # Source identity is the snapshot's scenario descriptor (sim scenario / historical window / live
    # SYMBOL) — NEVER the bare ticker string (binding anti-goal).
    bound_source = snap.scenario
    data_feed = data_feed_for_scenario(snap.scenario, config)
    thesis = ThesisRecord(
        id=uuid.uuid4().hex,
        ticker=ticker,
        setup_type=body.setup_type,
        direction=body.direction,
        invalidation_price=body.invalidation_price,
        level_price=body.level_price,
        status="active",
        bound_source=bound_source,
        data_feed=data_feed,
        config_fingerprint=config.config_fingerprint(),
        entry_context=entry_context,
        statements=statements,
        created_logical_ts=snap.timestamp,
        created_wall_ts=time.time(),
        risk_flags=risk_flags,
    )

    # Persist the thesis row AND its initial ``pending`` verdict event ATOMICALLY (one writer
    # transaction). The append-only timeline starts here — nothing was recorded before declaration —
    # and a store failure rolls BOTH back, so a thesis row without its initial event can no longer be
    # left behind (the iter-4 orphan defect). A failure is a real 503 (the declaration did not take
    # effect) — never a silently-lost or half-saved thesis.
    initial_event = VerdictEventRecord(
        thesis_id=thesis.id,
        logical_ts=snap.timestamp,
        wall_ts=thesis.created_wall_ts,
        verdict="pending",
        evidence=(
            "Thesis declared. The tape is being watched against it; "
            "the verdict stays pending until post-declaration evidence accrues."
        ),
        tape_state=snap.tape_state,
        confidence=snap.confidence,
        last=last,
    )
    try:
        registry.store.insert_thesis_with_event(thesis, initial_event)
    except Exception:
        raise HTTPException(status_code=503, detail="could not persist the thesis")

    # Attach to the live monitor so subsequent events evaluate the statements against the tape.
    if monitor is None:
        # Defensive: a watched ticker should always have a monitor (the hook attaches one on engine
        # creation). If not, create + attach one now so the projection is still served.
        monitor = ResearchMonitor(registry.store, config, ticker)
        registry._monitors[ticker] = monitor
        engine.add_observer(monitor)
    monitor.set_thesis(thesis)

    # Declared-from linkage (capability 33, J-65): when the declaration came from a hint's prefill
    # affordance, record the link on the persisted hint record (the hints table is not append-only-
    # mandated). The hint id was already validated to exist above (422 otherwise), so this is a no-op-
    # safe flip recorded ONLY now — when the user has COMPLETED the declaration (one click never creates
    # a thesis). Through the writer queue. A linkage-write failure must not undo the (already-persisted)
    # thesis, so it is best-effort: the thesis stands; the link is the secondary record.
    if body.declared_from_hint_id is not None:
        try:
            registry.store.mark_hint_declared_from(body.declared_from_hint_id, thesis.id)
        except Exception:
            pass

    projection = monitor.projection()
    return {"thesis": projection}


@router.post("/thesis/{thesis_id}/resolve")
def resolve_thesis(
    thesis_id: str,
    body: ResolveRequest,
    registry: ResearchRegistry = Depends(get_registry),
    manager=Depends(get_watch_manager),
) -> dict:
    """Honestly close out a USER-declared thesis (J-50) — ``played_out`` or ``abandoned`` ONLY.

    Validation matrix (nothing is mutated on any rejection):
      * 404 — no thesis with that id;
      * 422 — ``invalidated`` / ``expired`` requested (those resolutions are SYSTEM-owned), or an
        unknown ``resolution`` enum;
      * 409 — the thesis is already resolved (any terminal status) — the resolve is idempotently
        refused, never a duplicated timeline event (a double-click yields one resolution + one 409);
      * 409 — ``abandoned`` requested for an ENTRY-MARKED thesis (anti-survivorship: a real position
        is never abandoned). The entry-mark UI is a later iteration; this guard is enforced at the
        store/API level now.

    On success the resolution is routed through ONE store function
    (``resolve_thesis_with_event``) — so a later iteration can compute grades / execution checks
    "once here" without a second path — which flips the terminal status AND appends the final
    timeline event (logical + wall timestamps) ATOMICALLY (append-only — prior events are never
    edited). The live monitor (if the ticker is still watched) is detached so no verdict event is
    appended after resolution and ``thesis/active`` returns ``null`` (a redeclare then succeeds)."""
    thesis = registry.store.get_thesis(thesis_id)
    if thesis is None:
        raise HTTPException(status_code=404, detail=f"no thesis with id '{thesis_id}'")

    resolution = body.resolution

    # 422 — system-owned resolutions can never be set by the user.
    if resolution in _SYSTEM_RESOLUTIONS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"'{resolution}' is a system-owned resolution — only "
                f"{' / '.join(_USER_RESOLUTIONS)} may be set by the user"
            ),
        )
    # 422 — unknown enum (rejected, never coerced).
    if resolution not in _USER_RESOLUTIONS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"unknown resolution '{resolution}' — must be one of "
                f"{' / '.join(_USER_RESOLUTIONS)}"
            ),
        )

    # 409 — already resolved (any terminal status). Idempotent refusal: a second resolve (e.g. a
    # double-click race) gets one 409 and appends NO duplicate timeline event.
    if thesis.status in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"thesis '{thesis_id}' is already resolved ({thesis.status})",
        )

    # 409 — an entry-marked thesis can never be abandoned (anti-survivorship). Checked against the
    # persisted action rows (the entry-mark UI is J-52; the guard is unit-proven now).
    if resolution == "abandoned" and registry.store.has_entry_mark(thesis_id):
        raise HTTPException(
            status_code=409,
            detail="an entry-marked thesis cannot be abandoned — it carries a real position",
        )

    # --- All validation passed — resolve through the ONE store function (status flip + appended final
    # timeline event, atomic + append-only). Stamp logical + wall timestamps: use the live engine
    # snapshot's logical clock if the ticker is still watched, else the last recorded logical instant
    # (never a fabricated value).
    wall = time.time()
    engine = manager.get(thesis.ticker)
    snap = engine.snapshot() if engine is not None else None
    if snap is not None:
        logical = snap.timestamp
        last = snap.last
    else:
        events = registry.store.verdict_events(thesis_id)
        logical = events[-1].logical_ts if events else thesis.created_logical_ts
        last = events[-1].last if events else None

    evidence = {
        "played_out": "You resolved this thesis as played out — the idea has run its course.",
        "abandoned": "You abandoned this thesis — it was closed without running its course.",
    }[resolution]

    final_event = VerdictEventRecord(
        thesis_id=thesis_id,
        logical_ts=logical,
        wall_ts=wall,
        verdict=resolution,
        evidence=evidence,
        tape_state=snap.tape_state if snap is not None else None,
        confidence=snap.confidence if snap is not None else None,
        last=last,
    )
    try:
        registry.store.resolve_thesis_with_event(thesis_id, resolution, final_event)
    except Exception:
        raise HTTPException(status_code=503, detail="could not resolve the thesis")

    # Compute the machine-derived execution checks, the per-statement FINAL statuses (J-55), and the
    # outcome × process grades (J-56) ONCE here, at this terminal resolution, and persist them on the
    # thesis row (capabilities 27/29 — the data-contract row-19 execution-checks + grades half). The
    # SAME single functions every other terminal path calls (system invalidation, stream-end expiry,
    # restart-expiry sweep); the journal detail serves the persisted results VERBATIM (never recomputed
    # at read). The grades weigh the just-persisted execution checks, so they MUST run after them. The
    # final statuses use the at-resolution engine snapshot (``snap`` — the live read if still watched,
    # else ``None`` => an honest ``not_evaluated`` per statement). A failure here must NOT undo the
    # (already-committed) resolution — the keys then stay honestly ABSENT rather than half-resolving it.
    try:
        compute_and_persist_execution_checks(registry.store, thesis_id, registry._config)
        compute_and_persist_final_statuses(registry.store, thesis_id, snap, registry._config)
        compute_and_persist_grades(registry.store, thesis_id, resolution, registry._config)
    except Exception:
        pass

    # Excursions (capability 30, J-58): if the live monitor still HOLDS this thesis, the user
    # resolution is the terminal moment for the in-memory tracker — truncate any open horizon and
    # persist the tracker's resolved state ONCE through the SAME single function every terminal path
    # calls (the journal detail serves it verbatim). If the watch already ended (an entry-marked
    # surviving thesis the user is now resolving), the excursion record was ALREADY persisted at the
    # stream-end survival path; the store-level idempotent guard means it is never reopened. A failure
    # here must NOT undo the (already-committed) resolution — the key then stays honestly ABSENT.
    monitor = registry.monitor_for(thesis.ticker)
    if monitor is not None and monitor.active_thesis_id == thesis_id:
        try:
            monitor.persist_excursions_on_user_resolve(thesis_id)
        except Exception:
            pass

    # Detach the live monitor (if the ticker is still watched and holds THIS thesis) so no verdict
    # event is appended after resolution and the projection clears (the strip returns to the declare
    # affordance). If the watch already ended, the persisted status is authoritative on its own.
    if monitor is not None and monitor.active_thesis_id == thesis_id:
        monitor.resolve_by_user(resolution)

    return {
        "thesis": {
            "id": thesis.id,
            "ticker": thesis.ticker,
            "setup_type": thesis.setup_type,
            "direction": thesis.direction,
            "invalidation_price": thesis.invalidation_price,
            "level_price": thesis.level_price,
            "status": resolution,
            "resolved_logical_ts": logical,
            "resolved_wall_ts": wall,
            "bound_source": thesis.bound_source,
            "data_feed": thesis.data_feed,
            "config_fingerprint": thesis.config_fingerprint,
        }
    }


# The action-mark kinds a user may journal (J-52). One ENTRY and one EXIT per thesis; a duplicate of
# either, or an exit before an entry, is a 409 — recorded marks are append-only facts, never edited.
_ACTION_KINDS = ("entry", "exit")


@router.post("/thesis/{thesis_id}/action")
def record_action(
    thesis_id: str,
    body: ActionRequest,
    registry: ResearchRegistry = Depends(get_registry),
    manager=Depends(get_watch_manager),
) -> dict:
    """Journal the user's ACTUAL entry / exit on the active thesis (J-52) — recorded VERBATIM.

    The mark is the user's OWN already-taken action; this is a JOURNALING record, never a fill, never
    a simulated execution, never an order (no-execution-path anti-goal). The submitted ``price`` is
    stored EXACTLY as given (never inferred), stamped at the CURRENT logical + wall time, with
    ``spread_at_mark`` taken ONCE from the current snapshot at recording (a moment value — ``None``
    when there is no quote — never recomputable later).

    Validation matrix (nothing is recorded on any rejection):
      * 404 — no thesis with that id;
      * 422 — unknown ``kind`` (not ``entry`` / ``exit``); non-positive / non-finite price (a price
        must be a real, positive number — a journaled trade price is never ≤ 0 or NaN/inf);
      * 409 — the thesis is already resolved (no new marks on a closed thesis);
      * 409 — a duplicate entry, a duplicate exit, or an exit before any entry (one of each, in
        order — recorded marks are append-only facts).

    The write goes through the store's single writer queue (``BEGIN IMMEDIATE``), never from event
    processing or the WS serialization path. On success the full thesis projection (now carrying the
    recorded marks + realized-R) is returned — the same projection the WS ``thesis`` key carries, so
    the strip updates from the live frame on its own."""
    thesis = registry.store.get_thesis(thesis_id)
    if thesis is None:
        raise HTTPException(status_code=404, detail=f"no thesis with id '{thesis_id}'")

    kind = body.kind
    # 422 — unknown kind (rejected, never coerced).
    if kind not in _ACTION_KINDS:
        raise HTTPException(
            status_code=422,
            detail=f"unknown action kind '{kind}' — must be one of {' / '.join(_ACTION_KINDS)}",
        )
    # 422 — a journaled trade price must be a real, positive number (never ≤ 0, NaN, or inf). Pydantic
    # already rejected a non-numeric body; this rejects a numerically-malformed price.
    price = body.price
    if not math.isfinite(price) or price <= 0:
        raise HTTPException(
            status_code=422,
            detail="price must be a positive, finite number",
        )

    # 409 — no new marks on an already-resolved thesis (the thesis is closed).
    if thesis.status in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"thesis '{thesis_id}' is already resolved ({thesis.status})",
        )

    # 409 — one entry + one exit, in order. Recorded marks are append-only facts (never edited): a
    # second entry / second exit, or an exit before any entry, is refused.
    existing = registry.store.get_actions(thesis_id)
    has_entry = any(a.kind == "entry" for a in existing)
    has_exit = any(a.kind == "exit" for a in existing)
    if kind == "entry" and has_entry:
        raise HTTPException(
            status_code=409, detail="this thesis already has an entry mark"
        )
    if kind == "exit" and has_exit:
        raise HTTPException(
            status_code=409, detail="this thesis already has an exit mark"
        )
    if kind == "exit" and not has_entry:
        raise HTTPException(
            status_code=409, detail="cannot mark an exit before an entry"
        )

    # Stamp the CURRENT logical + wall time and the moment spread. Use the live snapshot if the ticker
    # is still watched; otherwise fall back to the last recorded logical instant (never a fabricated
    # value) and a ``None`` spread (no quote to read).
    wall = time.time()
    engine = manager.get(thesis.ticker)
    snap = engine.snapshot() if engine is not None else None
    if snap is not None:
        logical = snap.timestamp
        spread_at_mark = snap.spread
    else:
        events = registry.store.verdict_events(thesis_id)
        logical = events[-1].logical_ts if events else thesis.created_logical_ts
        spread_at_mark = None

    record = ActionRecord(
        id=uuid.uuid4().hex,
        thesis_id=thesis_id,
        kind=kind,
        price=price,
        logical_ts=logical,
        wall_ts=wall,
        spread_at_mark=spread_at_mark,
    )
    try:
        registry.store.insert_action(record)
    except Exception:
        raise HTTPException(status_code=503, detail="could not record the action mark")

    # Arm the excursion ENTRY population (capability 30, J-58) at the recorded ENTRY mark — the
    # entry-anchored population's defining moment. Uses the verbatim mark price + the moment spread
    # ALREADY stamped on the action row (row 18, reused — never re-stamped). Only when the live monitor
    # holds this thesis (the entry-mark API refuses marks on a resolved thesis, so a held monitor is
    # the normal case); a stopped watch's surviving thesis re-arms on re-attach if needed.
    monitor = registry.monitor_for(thesis.ticker)
    if kind == "entry" and monitor is not None and monitor.active_thesis_id == thesis_id:
        monitor.arm_entry_excursions(
            logical_ts=logical, wall_ts=wall, price=price, spread_at_mark=spread_at_mark
        )

    # Return the full live projection (now carrying the recorded marks + realized-R) if the monitor
    # holds this thesis; otherwise assemble the marks projection directly from the store so the caller
    # always sees the recorded mark even if the watch already ended.
    if monitor is not None and monitor.active_thesis_id == thesis_id:
        return {"thesis": monitor.projection()}
    return {
        "thesis": {
            "id": thesis.id,
            "ticker": thesis.ticker,
            "marks": marks_projection(thesis, registry.store.get_actions(thesis_id)),
        }
    }


@router.post("/thesis/{thesis_id}/review")
def review_thesis(
    thesis_id: str,
    body: ReviewRequest,
    registry: ResearchRegistry = Depends(get_registry),
) -> dict:
    """Save the user's CONFIRMED review of a resolved thesis (J-57) — tags + optional note.

    This records the user's OWN confirmation (the machine SUGGESTS tags from the execution checks; it
    never records a confirmed tag on its own — capability 27/29). The confirmed tags are persisted
    distinctly from the suggested tags, and the thesis flips to ``reviewed``.

    Validation matrix (nothing is persisted on any rejection):
      * 404 — no thesis with that id;
      * 422 — an unknown mistake tag (not in the backend taxonomy), or ``other`` selected WITHOUT a
        (non-blank) note;
      * 409 — the thesis is NOT resolved yet (a review records how a RESOLVED thesis went);
      * 409 — the thesis is ALREADY reviewed (conservative immutability default — goal.md is silent
        on re-review, so a review record is kept immutable in the spirit of journal integrity; a
        second save is refused rather than overwriting the first).

    The append-only ``verdict_events`` write surface is UNTOUCHED — a review never edits the timeline
    (journal integrity). On success the saved review + ``reviewed`` flip are served by
    ``GET /research/journal/{id}`` and the ``reviewed`` flag lands on ``GET /research/journal`` rows.
    Returns the saved review verbatim."""
    thesis = registry.store.get_thesis(thesis_id)
    if thesis is None:
        raise HTTPException(status_code=404, detail=f"no thesis with id '{thesis_id}'")

    # 409 — a review records how a RESOLVED thesis went; an active thesis has no resolution to review.
    if thesis.status not in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"thesis '{thesis_id}' is not resolved yet — only a resolved thesis can be reviewed",
        )

    # 409 — already reviewed (conservative immutability default — see the route docstring / spec NOTES).
    if thesis.reviewed:
        raise HTTPException(
            status_code=409,
            detail=f"thesis '{thesis_id}' has already been reviewed",
        )

    # 422 — every confirmed tag must exist in the backend taxonomy (never a silently-coerced tag).
    tags = body.mistake_tags
    for tag in tags:
        if not is_valid_mistake_tag(tag):
            raise HTTPException(status_code=422, detail=f"unknown mistake tag '{tag}'")

    # 422 — a tag that REQUIRES a note (``other``) must carry a non-blank note.
    note = body.note
    note_present = note is not None and note.strip() != ""
    requires_note = any(t in MISTAKE_TAGS_REQUIRING_NOTE for t in tags)
    if requires_note and not note_present:
        raise HTTPException(
            status_code=422,
            detail=(
                f"a note is required when one of {' / '.join(MISTAKE_TAGS_REQUIRING_NOTE)} is selected"
            ),
        )

    # Persist the confirmed tags + note VERBATIM and flip ``reviewed`` — the append-only timeline is
    # untouched (journal integrity). The note is stored exactly as given when present, else NULL.
    stored_note = note if note_present else None
    try:
        registry.store.save_review(thesis_id, tags=tags, note=stored_note)
    except Exception:
        raise HTTPException(status_code=503, detail="could not save the review")

    return {
        "review": {
            "id": thesis.id,
            "reviewed": True,
            "mistake_tags": tags,
            "note": stored_note,
        }
    }


# --- Replay studies (capability 32, J-60/J-61/J-62) ---------------------------------------------
# The four endpoints in blueprint row 23. Studies are CREATED + STARTED here, run as cancellable
# background jobs OFF the event loop (the live cockpit is never blocked), and read VERBATIM (the
# served payload is the runner's persisted result — never recomputed at read; the UI computes
# nothing). Validation is explicit (422/404/409), never silent coercion.

# The market adapter for an ARBITRARY-WINDOW historical study — resolved through the SAME neutral seam
# the watch path uses, honoring test ``dependency_overrides`` (a hermetic test injects its FakeAdapter;
# a credentialless run fails explicitly, never fixture-substituted). Lazy import avoids an import cycle.
def get_study_market_adapter():
    from ..main import app, get_market_adapter

    return app.dependency_overrides.get(get_market_adapter, get_market_adapter)()


def _build_historical_fetch(adapter, symbol: str, start: str, end: str):
    """A blocking fetch callable the runner invokes ON ITS WORKER THREAD (off the event loop) for an
    arbitrary-window study. It uses the EXISTING adapter ``fetch_historical`` so credentials / no-data /
    untradable / timeout each surface the existing explicit errors (the runner maps them to an explicit
    ``failed`` study — never fabricated, never fixture-substituted)."""
    from datetime import datetime, timezone

    def _parse(value: str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)

    start_dt = _parse(start)
    end_dt = _parse(end)

    def _fetch():
        return adapter.fetch_historical(symbol, start_dt, end_dt)

    return _fetch


@router.post("/studies")
def create_study(
    body: StudyRequest,
    registry: ResearchRegistry = Depends(get_registry),
) -> dict:
    """Create + START a replay study (capability 32, J-60). Full validation (422):
      * unknown setup_type / direction / source_kind;
      * a level setup (level_break / failed_move_fade) WITHOUT a level_price (never a guessed level),
        or a level supplied for a non-level setup (forbidden);
      * a historical (arbitrary-window) study missing / malformed start / end, or end <= start.
    On success the study is persisted ``queued`` with its honesty stamps + recorded baseline seed and
    started as a background job; the full queued projection is returned."""
    # 422 — enum validation (never a silently-coerced enum).
    if not is_valid_setup(body.setup_type):
        raise HTTPException(status_code=422, detail=f"unknown setup_type '{body.setup_type}'")
    if not is_valid_direction(body.direction):
        raise HTTPException(status_code=422, detail=f"unknown direction '{body.direction}'")
    if body.source_kind not in (SOURCE_REFERENCE, SOURCE_SIM, SOURCE_HISTORICAL):
        raise HTTPException(status_code=422, detail=f"unknown source_kind '{body.source_kind}'")

    # 422 — the per-setup level rule (mirrors the thesis-declare rule): REQUIRED for the two level
    # setups (never a guessed level), FORBIDDEN otherwise.
    requires_level = setup_requires_level(body.setup_type)
    if requires_level and body.level_price is None:
        raise HTTPException(
            status_code=422,
            detail=f"setup_type '{body.setup_type}' requires a level_price (a level is never guessed)",
        )
    if not requires_level and body.level_price is not None:
        raise HTTPException(
            status_code=422,
            detail=f"setup_type '{body.setup_type}' does not take a level_price",
        )

    # Resolve the source + (for an arbitrary historical study) the bounded fetch callable.
    historical_fetch = None
    source_descriptor = body.source_id
    data_feed = "sim"
    if body.source_kind == SOURCE_SIM:
        from ..providers.simulated import is_sim_ticker

        if not is_sim_ticker(body.source_id):
            raise HTTPException(status_code=422, detail=f"unknown sim scenario '{body.source_id}'")
        data_feed = "sim"
    elif body.source_kind == SOURCE_REFERENCE:
        # The committed PG SIP fixture — no credentials, no window params. The feed basis is the
        # config-owned HISTORICAL feed (the reference study replays the committed SIP window through the
        # historical-replay path; the runner later re-stamps the resolved ``historical PG reference``
        # descriptor through the ONE ``data_feed_for_scenario`` mapping, which reads the SAME
        # ``historical_feed`` key — so the create-time stamp equals the runner's re-stamp by
        # construction). NO hardcoded ``"sip"`` literal — the row-26 feed-honesty consolidation (iter-25,
        # closing the iter-24 reviewer NOTE). Defaults unchanged (``historical_feed="sip"``) ⇒ every
        # existing stamp + the pinned reference study + the full suite stay byte-identical (zero re-pins).
        source_descriptor = REFERENCE_SOURCE_ID
        data_feed = registry.config.historical_feed
    else:  # SOURCE_HISTORICAL — arbitrary symbol + past window through the existing fetch path.
        if not body.source_id:
            raise HTTPException(status_code=422, detail="a historical study requires a symbol")
        if not body.start or not body.end:
            raise HTTPException(
                status_code=422, detail="a historical study requires start and end"
            )
        from datetime import datetime, timezone

        try:
            s = datetime.fromisoformat(body.start.replace("Z", "+00:00"))
            e = datetime.fromisoformat(body.end.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=422, detail="start and end must be ISO date-times")
        if e <= s:
            raise HTTPException(status_code=422, detail="end must be after start")
        adapter = get_study_market_adapter()
        if not adapter.is_available():
            # No credentials -> explicit unavailable (the study is never created with fabricated data).
            raise HTTPException(
                status_code=422,
                detail="real-data provider unavailable — a historical study needs credentials",
            )
        historical_fetch = _build_historical_fetch(adapter, body.source_id, body.start, body.end)
        # The config-owned HISTORICAL feed — an arbitrary-window study replays through the same
        # historical-replay path. The runner later re-stamps the resolved ``historical <SYM>`` descriptor
        # through the ONE ``data_feed_for_scenario`` mapping, which reads the SAME ``historical_feed``
        # key — so the create-time stamp equals the runner's re-stamp by construction. NO hardcoded
        # ``"sip"`` literal — the row-26 feed-honesty consolidation (iter-25, closing the iter-24
        # reviewer NOTE). Defaults unchanged ⇒ byte-identical stamps (zero re-pins).
        data_feed = registry.config.historical_feed

    params = {
        "source_kind": body.source_kind,
        "source_id": body.source_id,
        "source": source_descriptor,
        "setup_type": body.setup_type,
        "direction": body.direction,
        "level_price": body.level_price,
        "data_feed": data_feed,
    }
    if body.null_baseline_seed is not None:
        params["null_baseline_seed"] = body.null_baseline_seed

    jobs = registry.study_jobs
    payload = jobs.create(params)
    jobs.start(payload["id"], historical_fetch=historical_fetch)
    return {"study": payload}


@router.get("/studies")
def list_studies(registry: ResearchRegistry = Depends(get_registry)) -> dict:
    """List studies most-recent-first (capped at the serving-only ``study_list_max``). Each row is the
    runner's persisted payload, served VERBATIM (never recomputed)."""
    records = registry.store.list_studies(limit=registry.config.study_list_max)
    return {"studies": [r.payload for r in records]}


@router.get("/studies/{study_id}")
def get_study(
    study_id: str, registry: ResearchRegistry = Depends(get_registry)
) -> dict:
    """One study's status / progress + stored results, served VERBATIM. 404 for an unknown id."""
    record = registry.store.get_study(study_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"no study with id '{study_id}'")
    return {"study": record.payload}


@router.post("/studies/{study_id}/cancel")
def cancel_study(
    study_id: str, registry: ResearchRegistry = Depends(get_registry)
) -> dict:
    """Cancel a running/queued study (capability 32, J-61). 404 unknown id; 409 if the study is
    already terminal (done / cancelled / failed). The cancellation is cooperative — the running job
    observes it between events and resolves to explicit ``cancelled`` with partial-marked results."""
    record = registry.store.get_study(study_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"no study with id '{study_id}'")
    status = record.payload.get("status")
    if status in STUDY_TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409, detail=f"study '{study_id}' is already {status} — cannot cancel"
        )
    registry.study_jobs.cancel(study_id)
    return {"study_id": study_id, "cancelling": True}


# --- Historical tape datasets (era-3 capability 1, J-02) -----------------------------------------
# Exactly THREE routes (Product Shape): record/register, list, detail. There is NO PATCH / PUT /
# DELETE — a dataset is immutable and its split tag is frozen at registration (structurally: the
# store exposes no update path at all; re-recording registered content is the 409 below). The
# dataset store module is the ONE reader/writer of dataset files; these routes serve its
# metadata VERBATIM (the MCP ``datasets`` tool proxies the list byte-identically).


def get_dataset_store() -> DatasetStore:
    """The dataset store rooted at the config-owned directory (``TAPEOLOGY_DATASET_DIR``
    override, package-anchored default). A FastAPI dependency so tests can point it at a temp
    dir via the env var or override it outright (the adapter-seam pattern)."""
    return DatasetStore(CONFIG.dataset_dir_resolved())


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


@router.get("/datasets")
def list_datasets(store: DatasetStore = Depends(get_dataset_store)) -> dict:
    """List every registered dataset's metadata (each file checksum-verified on load), oldest
    first. A file that fails verification is surfaced EXPLICITLY in ``integrity_errors`` — never
    silently hidden, never served as data. The MCP ``datasets`` tool proxies this byte-for-byte."""
    records, errors = store.list()
    return {"datasets": records, "integrity_errors": errors}


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str, store: DatasetStore = Depends(get_dataset_store)) -> dict:
    """One dataset's stored metadata, verbatim (checksum-verified on load). 404 for an unknown
    id; an explicit 500 integrity error for a corrupted/tampered file (never a fabricated
    dataset)."""
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
    env var or override it outright (the ``get_dataset_store`` pattern)."""
    return BarStore(CONFIG.bar_dir_resolved())


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


def get_bar_fetch_adapter():
    """The market adapter for the BAR-FETCH path ONLY (``POST /research/bars`` — era-5 J-01).

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

    return app.dependency_overrides.get(get_market_adapter, YahooAdapter)()


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
    symbol, a malformed ISO ``start``/``end``, or ``end`` not after ``start``. The bar-fetch vendor
    defaults to the KEYLESS Yahoo adapter (``get_bar_fetch_adapter`` — era-5 J-01); Alpaca stays
    selectable via the existing ``get_market_adapter`` override, where missing credentials still
    surface the EXISTING explicit unavailable (503) state — never fabricated bars. Content already
    registered (a DIFFERENT window whose fetched content happens to match content already on
    file) is still the 409-style refusal from the frozen ``store.record``.

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
    if end_epoch <= start_epoch:
        raise HTTPException(status_code=422, detail="end must be after start")

    # Normalized HERE (era-5 J-03 moves this earlier than the pre-J-03 code) so the store-first
    # lookup key below matches EXACTLY what a successful fetch later stores — an unnormalized
    # lookup key would silently never hit.
    symbol = body.symbol.strip().upper()

    hit = index.lookup(symbol, body.timeframe, body.start, body.end)
    if hit is not None:
        try:
            return {"bar_series": store.get(hit.series_id)}
        except (BarSeriesNotFound, BarSeriesIntegrityError):
            # The index pointed at a series the canonical JSON store can no longer verify
            # (deleted or corrupted since indexing) -- never fabricate or serve partial data.
            # Fall through and treat this exactly like a first-time miss; a real re-fetch below
            # additively overwrites this stale entry once it succeeds.
            pass

    adapter = get_bar_fetch_adapter()
    if not adapter.is_available():
        # No credentials -> the EXISTING explicit unavailable (503) state (never a fabricated bar
        # series) — the DoD-mandated status for this gap, distinct from the historical-dataset
        # path's 422 for the analogous case. Yahoo is always available (keyless); this only fires
        # when an override (e.g. a credentialless Alpaca selection) reports unavailable.
        raise HTTPException(
            status_code=503,
            detail="real-data provider unavailable — a historical bar recording needs credentials",
        )

    from datetime import datetime, timezone

    start_dt = datetime.fromtimestamp(start_epoch, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_epoch, tz=timezone.utc)
    try:
        raw_bars = adapter.fetch_bars(symbol, start_dt, end_dt, body.timeframe)
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

    # feed provenance (era-5 J-01): sourced from the ADAPTER — its single owner — only when Yahoo
    # served this fetch; otherwise the EXISTING config-owned historical feed, byte-identical to
    # every pre-iteration stamp. NOT ``adapter.name`` applied uniformly: ``AlpacaAdapter.name ==
    # "alpaca"``, not ``"sip"`` — doing so would silently rename Alpaca's stamp and break the
    # frozen ``test_post_records_and_registers_a_bar_series`` assertion.
    feed = adapter.name if isinstance(adapter, YahooAdapter) else registry.config.historical_feed

    try:
        meta = store.record(
            symbol=symbol,
            timeframe=body.timeframe,
            window_start_utc=body.start,
            window_end_utc=body.end,
            feed=feed,
            bars=list(raw_bars),
        )
    except BarSeriesAlreadyRegistered as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except EmptyBarWindowError as exc:
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
    record). The real-filter path's behavior below is unchanged."""
    normalized_symbol = symbol.strip().upper() if symbol else None
    normalized_timeframe = timeframe.strip() if timeframe else None
    if normalized_symbol is None and normalized_timeframe is None:
        records, errors = store.list()
        return {"bar_series": records, "integrity_errors": errors}

    records: list[dict] = []
    errors: list[dict] = []
    for hit in index.list(symbol=normalized_symbol, timeframe=normalized_timeframe):
        try:
            records.append(store.get(hit.series_id))
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
    no basis could be resolved) -- never one ambiguous bare empty ``bands`` array."""
    if not symbol:
        raise HTTPException(status_code=422, detail="a tradability query requires a symbol")
    try:
        as_of_epoch = parse_utc_epoch(as_of)
    except ValueError:
        raise HTTPException(status_code=422, detail="as_of must be an ISO date-time")
    normalized_symbol = symbol.strip().upper()
    result = compute_tradability(store, normalized_symbol, as_of_epoch, CONFIG)
    return {"symbol": normalized_symbol, "as_of": as_of, **result}


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
