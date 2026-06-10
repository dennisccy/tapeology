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

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..config import Config
from .monitor import ResearchMonitor, data_feed_for_scenario
from .store import JournalStore, ThesisRecord, VerdictEventRecord
from .taxonomy import (
    frozen_statements,
    is_valid_direction,
    is_valid_setup,
    setup_requires_level,
    taxonomy_payload,
)

router = APIRouter(prefix="/research", tags=["research"])


class ThesisRequest(BaseModel):
    """Body for ``POST /research/thesis``. ``level_price`` is optional at the schema level — the
    per-setup REQUIRED/FORBIDDEN rule is enforced in the route (a 422), never by the schema, so the
    error message is explicit and taxonomy-owned."""

    ticker: str
    setup_type: str
    direction: str
    invalidation_price: float
    level_price: float | None = None


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

    @property
    def store(self) -> JournalStore:
        return self._store

    def on_engine_created(self, ticker: str, engine: object) -> None:
        """Attach a fresh monitor to a freshly-built engine (the WatchManager hook)."""
        monitor = ResearchMonitor(self._store, self._config)
        self._monitors[ticker] = monitor
        engine.add_observer(monitor)

    def monitor_for(self, ticker: str) -> ResearchMonitor | None:
        return self._monitors.get(ticker)

    def projection_for(self, ticker: str) -> dict | None:
        monitor = self._monitors.get(ticker)
        return monitor.projection() if monitor is not None else None

    def startup_sweep(self) -> list[str]:
        """Resolve any thesis left ``active`` in the DB (from a prior process) to ``expired``."""
        return self._store.expire_stale_actives(time.time())


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
    """The setup catalog, enums, and display copy — the single backend owner of research labels."""
    return taxonomy_payload()


@router.get("/thesis/active")
def get_active_thesis(
    ticker: str, registry: ResearchRegistry = Depends(get_registry)
) -> dict:
    """The canonical thesis projection for ``ticker`` (``thesis: null`` is a NORMAL state).

    Reads the SAME ``monitor.projection()`` the WS ``thesis`` key reads, so the two are
    verbatim-equal by construction (data-contract row 15)."""
    return {"thesis": registry.projection_for(ticker)}


@router.get("/journal/{thesis_id}")
def get_journal_entry(
    thesis_id: str, registry: ResearchRegistry = Depends(get_registry)
) -> dict:
    """The blueprint row-16 registered serving endpoint: a thesis record + its persisted, append-only
    verdict timeline, served VERBATIM from the store (never recomputed at read time).

    Minimal projection only this iteration — NO list endpoint, NO analytics, NO review fields (those
    are later iterations). 404 for an unknown id. The timeline rows are returned in insertion order
    (the append-only sequence) with the canonical per-row values the verdict engine recorded,
    including the dwell timing record (``rule_first_true``)."""
    thesis = registry.store.get_thesis(thesis_id)
    if thesis is None:
        raise HTTPException(status_code=404, detail=f"no thesis with id '{thesis_id}'")
    events = registry.store.verdict_events(thesis_id)
    return {
        "thesis": {
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
        },
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
    # Source identity is the snapshot's scenario descriptor (sim scenario / historical window / live
    # SYMBOL) — NEVER the bare ticker string (binding anti-goal).
    bound_source = snap.scenario
    data_feed = data_feed_for_scenario(snap.scenario)
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
        monitor = ResearchMonitor(registry.store, config)
        registry._monitors[ticker] = monitor
        engine.add_observer(monitor)
    monitor.set_thesis(thesis)

    projection = monitor.projection()
    return {"thesis": projection}
