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
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..config import Config
from .marks import marks_projection
from .monitor import (
    ResearchMonitor,
    build_projection,
    compute_risk_flags,
    data_feed_for_scenario,
)
from .journal_rows import journal_row
from .store import ActionRecord, JournalStore, ThesisRecord, VerdictEventRecord
from .taxonomy import not_evaluated_notice
from .taxonomy import (
    frozen_statements,
    is_valid_direction,
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
        """Attach a fresh monitor to a freshly-built engine (the WatchManager hook).

        The monitor is given the engine (so its ``on_status`` can read the terminal ``end_reason``).
        If a SURVIVING entry-marked active thesis exists for this ticker (it was NOT expired on a
        prior stop/restart because it carries a real position, J-47), it is OFFERED to the fresh
        monitor: the monitor adopts it — appending exactly one ``watch_restarted`` gap event and
        resuming evaluation — only once the first snapshot confirms the new watch's source identity
        equals the thesis's ``bound_source`` (a mismatch is never adopted)."""
        monitor = ResearchMonitor(self._store, self._config)
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
    # Action marks + realized-R (J-52, data-contract rows 18 & 27) — read back VERBATIM from the
    # persisted action rows via the SAME single ``marks_projection`` the row-15 thesis projection
    # uses, so the journal-detail readback and the strip show identical values (no second path).
    marks = marks_projection(thesis, registry.store.get_actions(thesis_id))
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
    return {
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
        monitor = ResearchMonitor(registry.store, config)
        registry._monitors[ticker] = monitor
        engine.add_observer(monitor)
    monitor.set_thesis(thesis)

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

    # Detach the live monitor (if the ticker is still watched and holds THIS thesis) so no verdict
    # event is appended after resolution and the projection clears (the strip returns to the declare
    # affordance). If the watch already ended, the persisted status is authoritative on its own.
    monitor = registry.monitor_for(thesis.ticker)
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

    # Return the full live projection (now carrying the recorded marks + realized-R) if the monitor
    # holds this thesis; otherwise assemble the marks projection directly from the store so the caller
    # always sees the recorded mark even if the watch already ended.
    monitor = registry.monitor_for(thesis.ticker)
    if monitor is not None and monitor.active_thesis_id == thesis_id:
        return {"thesis": monitor.projection()}
    return {
        "thesis": {
            "id": thesis.id,
            "ticker": thesis.ticker,
            "marks": marks_projection(thesis, registry.store.get_actions(thesis_id)),
        }
    }
