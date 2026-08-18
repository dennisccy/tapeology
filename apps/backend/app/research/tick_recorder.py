"""The tick recorder (Card 5.2, brought forward) -- era "The Rapid Microscope" J-06 step 2,
``docs/rapid-validation-spec.md`` section 7.1.

**What this closes.** Iteration 7 shipped the Card-5.1 storage CAPABILITY (optional preservation
fields on the event pipeline, ``schema_basis``/``quote_size_unit`` kwargs on ``DatasetStore.
record``) but built no caller that actually populates them. This module is that caller: a chunked,
throttled, resumable fetch through the EXISTING, UNCHANGED ``AlpacaAdapter.iter_historical_chunks``
generator, writing through the EXISTING, UNCHANGED ``DatasetStore.record``/``record_from_source``
under the same store discipline (append-only, checksummed, split frozen at registration).

**Chunk planning (mirrors ``desk_deep_backfill.plan_deep_windows``).** ``plan_recorder_chunks``
computes every 900s-scale sub-window a recording WOULD fetch, over an explicit ``(symbols, dates)``
universe, with ZERO store or vendor calls -- the SAME neutral ``split_window`` function
``iter_historical_chunks`` uses internally, applied to each date's 09:30-16:00 ET RTH session
window (this module's own private ``ZoneInfo`` constant, the ``micro_readiness.py``/
``referee_null.py`` per-module idiom -- mirrored, not imported).

**The walk (mirrors ``desk_deep_backfill._run_one_chunk``'s FOUR-value vocabulary, no second
one).** Chunks are walked in ``(symbol, date)`` groups. A day whose dataset already exists is
short-circuited entirely (every chunk reports ``"reused"``, zero store or vendor calls -- TC-3). A
day not yet recorded walks its own chunks in order: a checkpointed chunk (a PRIOR run's raw fetch,
persisted so a restart never re-pays a vendor call for a chunk that already succeeded) reports
``"reused"``; a fresh vendor pull reports ``"fetched"`` (checkpointed immediately, throttled to
``RECORDER_PAGE_BUDGET_PER_MINUTE``); a raised exception reports ``"failed"`` with its detail
preserved verbatim and marks the WHOLE day unfinalizable THIS run -- but the walk continues to
every remaining chunk (desk_deep_backfill's own "never aborts" discipline), and a future run
resumes only the missing chunk(s) via the checkpoint (TC-4/TC-5). Once every chunk of a
not-yet-recorded day has content in hand, its chunks are assembled (chronological, non-overlapping
by construction) into ONE dataset via ``record_from_source`` -- ``"unchanged"`` is reserved for the
rare race where that assembled content is already registered (``DatasetAlreadyRegistered``, caught
never propagated, mirroring the bar path's own 409 handling).

**TR-19 (spec section 7.1 r2) -- a HARD structural gate.** ``verify_preservation_capability``
inspects (``dataclasses.fields``) whether ``TradeEvent``/``QuoteEvent`` actually carry the Card-5.1
preservation field names, called as the FIRST thing ``run_tick_recording`` does -- before a single
chunk is planned into a fetch or a byte is read from any store. Simulating the capability absent
(a test passes a deliberately incomplete stand-in dataclass via the ``_trade_cls``/``_quote_cls``
override) proves the refusal fires; the real, already-shipped classes always satisfy it today.

**Section 2.6 -- the dated vendor-rule stamping.** ``ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`` (the
constant ``micro_features.py``'s own docstring reserves for this module) and
``quote_size_unit_for_session_date`` implement the frozen rule verbatim: Alpaca CTA/UTP displayed
quote sizes are SHARES for sessions on/after ``2025-11-03``, ROUND LOTS before -- validated (by
``DatasetStore.record`` itself) against the single existing ``micro_features.QUOTE_SIZE_UNITS``
tuple, never a second vocabulary.

**The split rule (spec section 7.3, Card 5.2 -- published, frozen, NOT this module's invention).**
``DatasetStore.record`` requires a split tag; ``recorder_split_for`` computes the EXISTING published
sha256 rule directly (holdout iff the last hex digit of ``sha256(f"{symbol}:{date}")`` in
``{0,1,2}``) so this iteration's recorder can call it. This is a DIFFERENT, older, already-public
axis from ``vault.py``'s NEW opaque HMAC seal assignment (J-06 step 3, out of scope this
iteration) -- computing the published split here is not vault.py scope creep, it is simply what
every dataset registration has always required.

**Bar pairing (unchanged machinery).** ``pair_bar_backfill_for_recorded_days`` calls the EXISTING,
UNCHANGED ``desk_deep_backfill.plan_deep_windows``/``run_deep_backfill`` for every symbol that got a
dataset this run, over exactly that symbol's own recorded date range -- no second bar-fetch
implementation.

**The recorder's own throttle.** ``RECORDER_PAGE_BUDGET_PER_MINUTE`` (spec section 1 table) paces
consecutive real vendor pulls the SAME way ``alpaca.py``'s own ``_throttle_bar_fetch`` paces the bar
path (a module-level last-call timestamp + ``time.sleep``), applied to the tick path for the first
time. Deliberately INDEPENDENT of ``Config.historical_chunk_seconds``/
``historical_chunk_max_concurrency`` -- those govern the cockpit's own on-demand historical replay,
a different caller; this module reads them nowhere.

**Confinement (the ``desk_deep_backfill.py`` precedent, mirrored).** This module never names an
Alpaca credential and never imports the Alpaca SDK -- it resolves its adapter through the EXISTING
``routes.get_study_market_adapter`` seam (test ``dependency_overrides``-aware) and passes real
requests through the vendor-neutral ``MarketDataAdapter`` interface only.

**No new ``Config`` field.** Every constant here (``RECORDER_PAGE_BUDGET_PER_MINUTE``,
``RECORDER_CHUNK_SECONDS``, ``ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE``, ``RECORDER_SCHEMA_BASIS``) is a
plain module constant; storage dirs are bare env-var-or-sibling defaults (the
``TAPEOLOGY_MICRO_RECORDER_*`` family) -- ``config_fingerprint()`` is untouched.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import threading
import time
import uuid
from datetime import date, datetime, time as dt_time, timezone
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from ..config import CONFIG, Config
from ..providers.adapters.base import HistoricalWindow, RawQuote, RawTrade, split_window
from ..providers.base import QuoteEvent, TradeEvent
from .datasets import (
    DatasetAlreadyRegistered,
    DatasetStore,
    SOURCE_HISTORICAL,
    SPLIT_HOLDOUT,
    SPLIT_TRAIN,
    record_from_source,
)
from .desk_deep_backfill import (
    DESK_DEEP_TIMEFRAMES,
    plan_deep_windows,
    run_deep_backfill,
)
from .micro_features import QUOTE_SIZE_UNITS
from .micro_snapshots import append_run_log

__all__ = [
    "RecorderPreservationCapabilityMissing",
    "ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE",
    "RECORDER_SCHEMA_BASIS",
    "RECORDER_PAGE_BUDGET_PER_MINUTE",
    "RECORDER_CHUNK_SECONDS",
    "verify_preservation_capability",
    "quote_size_unit_for_session_date",
    "recorder_split_for",
    "plan_recorder_chunks",
    "RecorderCheckpointStore",
    "run_tick_recording",
    "pair_bar_backfill_for_recorded_days",
    "TickRecorderComputeManager",
    "resolve_tick_recorder_checkpoint_dir",
    "resolve_tick_recorder_log_dir",
    "main",
]


# --- TR-19: the Card-5.1 preservation-field structural gate (spec section 7.1 r2) -----------------

_TRADE_PRESERVATION_FIELDS = frozenset({"conditions", "exchange", "tape", "trade_id"})
_QUOTE_PRESERVATION_FIELDS = frozenset({"conditions", "tape", "bid_exchange", "ask_exchange"})


class RecorderPreservationCapabilityMissing(Exception):
    """TR-19: the recorder refuses to record ANY chunk unless the Card-5.1 preservation fields
    are structurally present on the event dataclasses -- a typed, named refusal, never a silent
    recording of an under-specified schema."""


def verify_preservation_capability(
    *, trade_cls: type = TradeEvent, quote_cls: type = QuoteEvent
) -> None:
    """The TR-19 check itself: pure introspection (``dataclasses.fields``), zero I/O. Callers
    override ``trade_cls``/``quote_cls`` ONLY to simulate the capability's absence in a test --
    the real, already-shipped classes (the defaults) always satisfy this today."""
    trade_fields = {f.name for f in dataclasses.fields(trade_cls)}
    quote_fields = {f.name for f in dataclasses.fields(quote_cls)}
    missing_trade = sorted(_TRADE_PRESERVATION_FIELDS - trade_fields)
    missing_quote = sorted(_QUOTE_PRESERVATION_FIELDS - quote_fields)
    if missing_trade or missing_quote:
        raise RecorderPreservationCapabilityMissing(
            f"Card-5.1 preservation prerequisite missing (TR-19, spec section 7.1 r2): "
            f"{trade_cls.__name__} lacks {missing_trade}, {quote_cls.__name__} lacks "
            f"{missing_quote} -- recording refused until the preservation fields ship"
        )


# --- spec section 2.6: the dated vendor-rule stamping ----------------------------------------------

# Reserved by micro_features.py's own docstring for "the module that actually reads it"
# (tick_recorder.py) -- frozen verbatim from docs/rapid-validation-spec.md section 1's table.
ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE = "2025-11-03"

# Names that a recorded row's schema carries the Card-5.1 preservation fields (spec section 2.6's
# "schema_basis -- the event-row schema version, including whether the optional Card-5.1
# preservation fields ... are present"). A single frozen string -- every row this module ever
# writes ships WITH the fields (TR-19 refuses otherwise), so there is exactly one basis value.
RECORDER_SCHEMA_BASIS = "tick_recorder_v1_card_5_1_preservation_present"


def quote_size_unit_for_session_date(session_date: str) -> str:
    """Stamps ``quote_size_unit`` per the dated Alpaca CTA/UTP vendor rule (spec section 2.6):
    displayed quote sizes are SHARES for sessions on/after ``ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE``,
    ROUND LOTS before. ``session_date`` is an ISO ``YYYY-MM-DD`` string -- lexicographic comparison
    is chronological comparison for that format, so no date parsing is needed. Drawn from (and
    re-validated by ``DatasetStore.record`` against) the single existing
    ``micro_features.QUOTE_SIZE_UNITS`` tuple -- never a second vocabulary (TC-10)."""
    unit = "shares" if session_date >= ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE else "round_lots"
    assert unit in QUOTE_SIZE_UNITS  # sanity only -- DatasetStore.record re-validates regardless
    return unit


# --- spec section 7.3: the published sha256 split rule (Card 5.2, frozen, unchanged) --------------


def recorder_split_for(symbol: str, session_date: str) -> str:
    """The PUBLISHED split rule ``docs/rapid-validation-spec.md`` section 7.3 fixes (Card 5.2,
    unchanged): ``holdout`` iff the last hex digit of ``sha256(f"{symbol}:{YYYY-MM-DD}")`` is in
    ``{0, 1, 2}``, else ``train``. ``DatasetStore.record`` requires a split tag on every call; this
    is that PRE-EXISTING, already-public rule computed directly -- a DIFFERENT, older axis from
    ``vault.py``'s NEW opaque HMAC seal assignment (J-06 step 3, out of scope this iteration)."""
    digest = hashlib.sha256(f"{symbol}:{session_date}".encode("utf-8")).hexdigest()
    return SPLIT_HOLDOUT if int(digest[-1], 16) in (0, 1, 2) else SPLIT_TRAIN


# --- the recorder's own throttle (spec section 1: RECORDER_PAGE_BUDGET_PER_MINUTE = 200) ----------

RECORDER_PAGE_BUDGET_PER_MINUTE = 200

# Process-lifetime timestamp (monotonic) of the last REAL recorder vendor call, read/written only
# by ``_throttle_recorder_fetch`` -- the ``alpaca.py`` ``_LAST_BAR_FETCH_MONOTONIC`` pattern,
# applied to the tick path for the first time (this module never touches that bar-path global).
_LAST_RECORDER_FETCH_MONOTONIC: float | None = None


def _throttle_recorder_fetch() -> None:
    """Space consecutive REAL recorder vendor calls at least ``60 / RECORDER_PAGE_BUDGET_PER_
    MINUTE`` seconds apart -- the ``alpaca._throttle_bar_fetch`` shape verbatim, independent
    constant. The very first call in a process never waits."""
    global _LAST_RECORDER_FETCH_MONOTONIC
    min_interval = 60.0 / RECORDER_PAGE_BUDGET_PER_MINUTE
    now = time.monotonic()
    if _LAST_RECORDER_FETCH_MONOTONIC is not None:
        remaining = min_interval - (now - _LAST_RECORDER_FETCH_MONOTONIC)
        if remaining > 0:
            time.sleep(remaining)
    _LAST_RECORDER_FETCH_MONOTONIC = time.monotonic()


def _reset_recorder_throttle_for_tests() -> None:
    """Test-only: resets the throttle's process-lifetime clock so tests never wait behind a PRIOR
    test's last call (the ``alpaca._clear_caches`` precedent, narrowed to this one global)."""
    global _LAST_RECORDER_FETCH_MONOTONIC
    _LAST_RECORDER_FETCH_MONOTONIC = None


# --- chunk planning (mirrors desk_deep_backfill.plan_deep_windows) --------------------------------

# This module's own private ZoneInfo/RTH constants -- the micro_readiness.py/referee_null.py
# per-module idiom (mirrored, not imported: "each module that needs ET wall-clock resolution owns
# a private ZoneInfo constant"). RTH bounds are the spec's own "09:30-16:00 ET" (section 0).
_ET_ZONE = ZoneInfo("America/New_York")
_RTH_OPEN = dt_time(9, 30)
_RTH_CLOSE = dt_time(16, 0)

# The recorder's OWN page-size constant -- deliberately INDEPENDENT of
# Config.historical_chunk_seconds/historical_chunk_max_concurrency (module docstring: "a different
# caller"). Matches the vendor's own natural page size so a planned chunk ordinarily corresponds
# to exactly one real iter_historical_chunks page.
RECORDER_CHUNK_SECONDS = 900.0


def _session_window_utc(session_date: str) -> tuple[datetime, datetime]:
    """The 09:30-16:00 ET RTH window for one session date, in UTC -- the SAME conversion
    ``micro_readiness.py``'s own ``_et_datetime``/``_rth_overlap`` use, applied in the other
    direction (ET wall-clock -> UTC instants) so the planner never touches a store to learn what a
    session's clock bounds are."""
    day = date.fromisoformat(session_date)
    open_et = datetime.combine(day, _RTH_OPEN, tzinfo=_ET_ZONE)
    close_et = datetime.combine(day, _RTH_CLOSE, tzinfo=_ET_ZONE)
    return open_et.astimezone(timezone.utc), close_et.astimezone(timezone.utc)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plan_recorder_chunks(
    symbols: list[str], dates: list[str], *, chunk_seconds: float = RECORDER_CHUNK_SECONDS
) -> list[dict]:
    """Every chunk a recording WOULD fetch, computed WITHOUT touching a store or a vendor (TC-1):
    ``[{"symbol", "date", "start", "end"}, ...]`` in ``(symbol, date, start)`` order -- symbol
    outer, date inner, matching ``plan_deep_windows``'s own nesting shape. Sub-window boundaries
    within each date's RTH session come from the SAME neutral ``split_window`` function
    ``iter_historical_chunks`` uses internally (imported from the adapter base, never
    re-implemented), so this planner's own chunk count matches exactly what the walker will later
    pull."""
    plan: list[dict] = []
    for symbol in symbols:
        for session_date in dates:
            start_utc, end_utc = _session_window_utc(session_date)
            for sub_start, sub_end in split_window(start_utc, end_utc, chunk_seconds):
                plan.append(
                    {
                        "symbol": symbol,
                        "date": session_date,
                        "start": _iso_utc(sub_start),
                        "end": _iso_utc(sub_end),
                    }
                )
    return plan


# --- per-chunk checkpoint persistence (resumability plumbing, NOT a dataset) -----------------------


class RecorderCheckpointStore:
    """A per-chunk raw-fetch cache keyed on a chunk's own ``(symbol, date, start, end)`` -- purely
    resumability plumbing, never a dataset and never research evidence: losing a checkpoint just
    means the next run re-fetches it (a mild cost, never a correctness problem, since a dataset is
    ONLY ever finalized from a day whose every chunk succeeded THIS run's walk or a prior one). A
    checkpoint that fails to parse is treated as a MISS, never a hard crash -- nothing permanent
    depends on it, unlike a registered dataset."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, symbol: str, session_date: str, start: str, end: str) -> Path:
        key = hashlib.sha256(f"{symbol}:{session_date}:{start}:{end}".encode("utf-8")).hexdigest()
        return self._root / f"{key}.json"

    def get(self, symbol: str, session_date: str, start: str, end: str) -> HistoricalWindow | None:
        path = self._path(symbol, session_date, start, end)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            trades = tuple(RawTrade(**t) for t in data["trades"])
            quotes = tuple(RawQuote(**q) for q in data["quotes"])
            return HistoricalWindow(data["symbol"], trades, quotes)
        except (OSError, ValueError, TypeError, KeyError):
            return None  # a bad checkpoint is a MISS -- the chunk is simply re-fetched

    def put(self, symbol: str, session_date: str, start: str, end: str, window: HistoricalWindow) -> None:
        path = self._path(symbol, session_date, start, end)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "symbol": window.symbol,
            "trades": [dataclasses.asdict(t) for t in window.trades],
            "quotes": [dataclasses.asdict(q) for q in window.quotes],
        }
        path.write_text(json.dumps(payload))


def resolve_tick_recorder_checkpoint_dir(dataset_dir_resolved: str) -> str:
    """``TAPEOLOGY_MICRO_RECORDER_CHECKPOINT_DIR`` if set, else a SIBLING of the caller's
    already-resolved dataset directory -- the ``resolve_desk_deep_backfill_log_dir``/
    ``TAPEOLOGY_MICRO_*`` family pattern (goal.md Constraints; deliberately NOT a ``Config``
    field)."""
    override = os.environ.get("TAPEOLOGY_MICRO_RECORDER_CHECKPOINT_DIR")
    if override:
        return override
    return str(Path(dataset_dir_resolved).parent / "micro_recorder_checkpoints")


def resolve_tick_recorder_log_dir(dataset_dir_resolved: str) -> str:
    """``TAPEOLOGY_MICRO_RECORDER_LOG_DIR`` if set, else a SIBLING of the caller's already-resolved
    dataset directory -- the same ``TAPEOLOGY_MICRO_*`` family pattern. The run log persists
    through ``micro_snapshots.append_run_log``/``read_run_log`` (the SAME shared, non-hash-chained
    build-run-history utility ``micro_routes.py`` already reuses for the scout/walk-forward
    sections' own run logs) -- convenience bookkeeping, never a claim of record (that role belongs
    to the datasets themselves and, for a run's raw fetched content, the checkpoint store above)."""
    override = os.environ.get("TAPEOLOGY_MICRO_RECORDER_LOG_DIR")
    if override:
        return override
    return str(Path(dataset_dir_resolved).parent / "micro_recorder_runs")


# --- the shared walker (mirrors desk_deep_backfill._run_one_chunk's outcome vocabulary) -----------


def _group_chunks_by_symbol_day(chunks: list[dict]) -> list[tuple[str, str, list[dict]]]:
    """Groups an ALREADY-(symbol, date, start)-ordered chunk plan into consecutive
    ``(symbol, date, [chunks])`` runs -- pure grouping, no I/O. Correct only when fed a plan in
    ``plan_recorder_chunks``'s own emitted order (its contract, documented there)."""
    groups: list[tuple[str, str, list[dict]]] = []
    for chunk in chunks:
        if groups and (groups[-1][0], groups[-1][1]) == (chunk["symbol"], chunk["date"]):
            groups[-1][2].append(chunk)
        else:
            groups.append((chunk["symbol"], chunk["date"], [chunk]))
    return groups


def _existing_dataset_for_day(
    dataset_store: DatasetStore, symbol: str, window_start_iso: str, window_end_iso: str
) -> dict | None:
    """Whether a dataset already covers this EXACT (symbol, day-window) -- the day-level
    short-circuit (TC-3): checked BEFORE any chunk of the day is even looked at, so a
    fully-recorded day costs zero ``DatasetStore.record`` calls, zero vendor calls, and zero
    checkpoint reads."""
    records, _errors = dataset_store.list()
    for meta in records:
        if (
            meta["symbol"] == symbol
            and meta["window_start_utc"] == window_start_iso
            and meta["window_end_utc"] == window_end_iso
        ):
            return meta
    return None


def _fetch_one_planned_chunk(adapter, symbol: str, start_iso: str, end_iso: str) -> HistoricalWindow:
    """ONE real vendor pull for a single planned chunk, throttled to
    ``RECORDER_PAGE_BUDGET_PER_MINUTE``. Drains ``iter_historical_chunks`` fully and concatenates
    whatever it yields into one ``HistoricalWindow`` -- ordinarily exactly one internal sub-window
    (``RECORDER_CHUNK_SECONDS`` matches the vendor's own natural page size), but concatenating
    means this never silently drops data even if an adapter yields more for one call."""
    _throttle_recorder_fetch()
    start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
    trades: list = []
    quotes: list = []
    for window in adapter.iter_historical_chunks(symbol, start_dt, end_dt):
        trades.extend(window.trades)
        quotes.extend(window.quotes)
    return HistoricalWindow(symbol, tuple(trades), tuple(quotes))


def _finalize_day(
    dataset_store: DatasetStore,
    symbol: str,
    session_date: str,
    window_start_iso: str,
    window_end_iso: str,
    day_windows: list[HistoricalWindow],
    config: Config,
) -> tuple[str | None, str | None]:
    """Assembles one symbol-day's successfully-fetched-or-reused chunk windows into ONE dataset via
    ``record_from_source`` (never a second fetch-and-record implementation), stamped with the
    section 2.6 ``schema_basis``/``quote_size_unit`` and the section 7.3 published split. Returns
    ``(dataset_id, "recorded")`` on a genuine new write, ``(existing_id, "unchanged")`` on the rare
    race where the assembled content is ALREADY registered (``DatasetAlreadyRegistered``, caught,
    never propagated -- the bar path's own 409 handling, mirrored), or ``(None, None)`` when every
    chunk was honestly empty (e.g. a holiday) -- nothing fabricated, nothing recorded."""
    trades = tuple(t for w in day_windows for t in w.trades)
    quotes = tuple(q for w in day_windows for q in w.quotes)
    assembled = HistoricalWindow(symbol, trades, quotes)
    if not assembled.trades and not assembled.quotes:
        return None, None
    split = recorder_split_for(symbol, session_date)
    try:
        meta = record_from_source(
            dataset_store,
            source_kind=SOURCE_HISTORICAL,
            source_id=symbol,
            split=split,
            start=window_start_iso,
            end=window_end_iso,
            config=config,
            historical_fetch=lambda: assembled,
            schema_basis=RECORDER_SCHEMA_BASIS,
            quote_size_unit=quote_size_unit_for_session_date(session_date),
        )
    except DatasetAlreadyRegistered as exc:
        return exc.existing_id, "unchanged"
    return meta["id"], "recorded"


def _chunk_entry(chunk: dict, outcome: str, detail: str | None = None) -> dict:
    return {**chunk, "outcome": outcome, "detail": detail, "dataset_id": None, "dataset_outcome": None}


def run_tick_recording(
    chunks: list[dict],
    dataset_store: DatasetStore,
    checkpoint_store: RecorderCheckpointStore,
    adapter,
    config: Config,
    *,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
    _trade_cls: type = TradeEvent,
    _quote_cls: type = QuoteEvent,
) -> list[dict]:
    """Walk ``chunks`` (a plan from ``plan_recorder_chunks``) in ``(symbol, date)`` groups,
    classifying each chunk's outcome exactly as ``desk_deep_backfill._run_one_chunk`` does
    (``reused``/``fetched``/``unchanged``/``failed``, no second vocabulary) and finalizing ONE
    dataset per symbol-day once every one of its chunks has content in hand. TR-19 first --
    structurally refuses the WHOLE walk before a single chunk is planned into a fetch.

    Returns the per-chunk outcome dicts in plan order: each planned chunk's own fields plus
    ``"outcome"``, ``"detail"``, ``"dataset_id"`` (populated ONLY on the row whose processing
    finalized that symbol-day's dataset), and ``"dataset_outcome"`` (``"recorded"``/``"unchanged"``
    alongside it, ``None`` everywhere else).

    ``_trade_cls``/``_quote_cls`` are TEST-ONLY overrides for ``verify_preservation_capability`` --
    every production caller uses the real, already-shipped classes (the defaults)."""
    verify_preservation_capability(trade_cls=_trade_cls, quote_cls=_quote_cls)
    outcomes: list[dict] = []
    for symbol, session_date, day_chunks in _group_chunks_by_symbol_day(chunks):
        window_start_iso = day_chunks[0]["start"]
        window_end_iso = day_chunks[-1]["end"]
        existing = _existing_dataset_for_day(dataset_store, symbol, window_start_iso, window_end_iso)

        if existing is not None:
            for chunk in day_chunks:
                if should_abort is not None and should_abort():
                    return outcomes
                entry = _chunk_entry(chunk, "reused")
                outcomes.append(entry)
                if progress is not None:
                    progress(entry)
            continue

        day_windows: list[HistoricalWindow] = []
        day_failed = False
        for chunk in day_chunks:
            if should_abort is not None and should_abort():
                return outcomes
            cached = checkpoint_store.get(chunk["symbol"], chunk["date"], chunk["start"], chunk["end"])
            if cached is not None:
                day_windows.append(cached)
                entry = _chunk_entry(chunk, "reused")
            else:
                try:
                    fetched = _fetch_one_planned_chunk(adapter, chunk["symbol"], chunk["start"], chunk["end"])
                except Exception as exc:  # noqa: BLE001 -- never aborts the walk, detail preserved
                    day_failed = True
                    entry = _chunk_entry(chunk, "failed", detail=str(exc))
                    outcomes.append(entry)
                    if progress is not None:
                        progress(entry)
                    continue
                checkpoint_store.put(chunk["symbol"], chunk["date"], chunk["start"], chunk["end"], fetched)
                day_windows.append(fetched)
                entry = _chunk_entry(chunk, "fetched")
            outcomes.append(entry)
            if progress is not None:
                progress(entry)

        if day_failed:
            continue  # no partial dataset record -- a future run resumes only the missing chunk(s)

        dataset_id, dataset_outcome = _finalize_day(
            dataset_store, symbol, session_date, window_start_iso, window_end_iso, day_windows, config,
        )
        if dataset_id is not None:
            outcomes[-1] = {**outcomes[-1], "dataset_id": dataset_id, "dataset_outcome": dataset_outcome}
    return outcomes


# --- bar pairing (Card 5.2: "paired bar backfill so band context joins") --------------------------


def pair_bar_backfill_for_recorded_days(
    tick_outcomes: list[dict], bar_store, bar_index, registry, *, today: date | None = None,
) -> list[dict]:
    """Every symbol whose tick recording produced (or confirmed) a dataset this run also gets its
    1m/5m bars backfilled through the EXISTING, UNCHANGED ``desk_deep_backfill.plan_deep_windows``/
    ``run_deep_backfill`` (no second bar-fetch implementation) -- so a recorded tick window can
    immediately join band context. Only symbols that actually finalized a dataset are backfilled
    (never every requested symbol regardless of outcome); the date range backfilled per symbol is
    exactly the min..max of ITS OWN recorded dates this run. Honestly empty (``[]``, never an
    error) when nothing was recorded."""
    by_symbol: dict[str, list[str]] = {}
    for entry in tick_outcomes:
        if entry.get("dataset_id"):
            by_symbol.setdefault(entry["symbol"], []).append(entry["date"])
    if not by_symbol:
        return []
    resolved_today = today or datetime.now(timezone.utc).date()
    outcomes: list[dict] = []
    for symbol, dates in sorted(by_symbol.items()):
        chunks = plan_deep_windows([symbol], DESK_DEEP_TIMEFRAMES, min(dates), max(dates), resolved_today)
        outcomes.extend(run_deep_backfill(chunks, bar_store, bar_index, registry))
    return outcomes


# --- the compute manager (mirrors MicroSnapshotComputeManager's shape) -----------------------------


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


_IDLE_RECORDER_SNAPSHOT: dict = {
    "run_id": None,
    "state": "idle",
    "progress": {"chunks_total": 0, "chunks_done": 0, "outcomes": []},
    "started_utc": None,
    "finished_utc": None,
    "error": None,
}


def _copy_recorder_snapshot(snapshot: dict) -> dict:
    progress = snapshot["progress"]
    return {**snapshot, "progress": {**progress, "outcomes": [dict(o) for o in progress["outcomes"]]}}


def _run_log_entry(
    run_id: str, state: str, started_utc: str, finished_utc: str, chunks_total: int,
    tick_outcomes: list[dict], bar_outcomes: list[dict], error: str | None,
) -> dict:
    """THE single shared run-log-entry builder -- called by BOTH the manager's worker resolve path
    and the CLI's ``main()`` (the ``record_deep_backfill_run`` "one shared writer" precedent),
    so a run's summary counts can never disagree between the two entry points."""
    return {
        "run_id": run_id,
        "state": state,
        "started_utc": started_utc,
        "finished_utc": finished_utc,
        "chunks_total": chunks_total,
        "chunks_done": len(tick_outcomes),
        "chunks_fetched": sum(1 for o in tick_outcomes if o["outcome"] == "fetched"),
        "chunks_reused": sum(1 for o in tick_outcomes if o["outcome"] == "reused"),
        "chunks_unchanged": sum(1 for o in tick_outcomes if o["outcome"] == "unchanged"),
        "chunks_failed": sum(1 for o in tick_outcomes if o["outcome"] == "failed"),
        "datasets_recorded": sum(1 for o in tick_outcomes if o.get("dataset_outcome") == "recorded"),
        "bars_recorded": sum(int(o.get("bars_recorded") or 0) for o in bar_outcomes),
        "error": error,
    }


class TickRecorderComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) recording job for this process -- the
    ``MicroSnapshotComputeManager``/``DeskDeepBackfillComputeManager`` shape: constructed with no
    arguments, every ``trigger()`` call takes its stores/adapter/config explicitly, single-flight,
    cancellable, the walk runs on a worker thread so an HTTP route returns immediately. Pairs bar
    backfill (module-level ``pair_bar_backfill_for_recorded_days``) into the SAME worker run,
    sequentially after the tick walk."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict = dict(_IDLE_RECORDER_SNAPSHOT)
        self._run_id: str | None = None
        self._cancel_event: threading.Event | None = None
        self._thread: threading.Thread | None = None

    def snapshot(self) -> dict:
        with self._lock:
            return _copy_recorder_snapshot(self._snapshot)

    def trigger(
        self,
        dataset_store: DatasetStore,
        checkpoint_store: RecorderCheckpointStore,
        adapter,
        bar_store,
        bar_index,
        registry,
        config: Config,
        run_log_dir: str,
        *,
        symbols: list[str],
        dates: list[str],
    ) -> dict:
        """Start a NEW recording job over ``symbols`` x ``dates``, or -- if one is already running
        -- return it UNCHANGED (``started: False``, single-flight, never a second job)."""
        with self._lock:
            if self._snapshot["state"] == "running":
                return {"started": False, "compute": _copy_recorder_snapshot(self._snapshot)}

            chunks = plan_recorder_chunks(symbols, dates)
            run_id = uuid.uuid4().hex
            self._run_id = run_id
            cancel_event = threading.Event()
            self._cancel_event = cancel_event
            self._snapshot = {
                "run_id": run_id,
                "state": "running",
                "progress": {"chunks_total": len(chunks), "chunks_done": 0, "outcomes": []},
                "started_utc": _iso_utc_now(),
                "finished_utc": None,
                "error": None,
            }
            published = _copy_recorder_snapshot(self._snapshot)

        def _publish(entry: dict) -> None:
            with self._lock:
                if self._run_id != run_id:
                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
                current = self._snapshot
                self._snapshot = {
                    **current,
                    "progress": {
                        **current["progress"],
                        "chunks_done": current["progress"]["chunks_done"] + 1,
                        "outcomes": [*current["progress"]["outcomes"], entry],
                    },
                }

        def _work() -> None:
            try:
                tick_outcomes = run_tick_recording(
                    chunks, dataset_store, checkpoint_store, adapter, config,
                    progress=_publish, should_abort=cancel_event.is_set,
                )
            except Exception as exc:  # noqa: BLE001 -- a failure OUTSIDE any single chunk (e.g. TR-19)
                self._resolve_terminal(run_id, run_log_dir, "failed", started_utc=published["started_utc"], error=str(exc))
                return
            bar_outcomes: list[dict] = []
            if not cancel_event.is_set():
                bar_outcomes = pair_bar_backfill_for_recorded_days(tick_outcomes, bar_store, bar_index, registry)
            state = "cancelled" if cancel_event.is_set() else "done"
            self._resolve_terminal(
                run_id, run_log_dir, state, started_utc=published["started_utc"],
                tick_outcomes=tick_outcomes, bar_outcomes=bar_outcomes,
            )

        thread = threading.Thread(target=_work, name=f"tick-recorder-compute:{run_id}", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return {"started": True, "compute": published}

    def _resolve_terminal(
        self, run_id: str, run_log_dir: str, state: str, *, started_utc: str,
        tick_outcomes: list[dict] | None = None, bar_outcomes: list[dict] | None = None,
        error: str | None = None,
    ) -> None:
        with self._lock:
            if self._run_id != run_id:
                return  # superseded -- never resolve a job that is no longer the current one
            current = self._snapshot
            finished_utc = _iso_utc_now()
            chunks_total = current["progress"]["chunks_total"]
            resolved_outcomes = tick_outcomes if tick_outcomes is not None else current["progress"]["outcomes"]
            self._snapshot = {**current, "state": state, "finished_utc": finished_utc, "error": error}
        entry = _run_log_entry(
            run_id, state, started_utc, finished_utc, chunks_total,
            resolved_outcomes, bar_outcomes or [], error,
        )
        append_run_log(run_log_dir, entry)

    def cancel(self) -> dict:
        """Signal cooperative cancellation for the in-flight job -- a harmless no-op if idle (the
        ROUTE rejects an idle cancel with a 409)."""
        with self._lock:
            cancel_event = self._cancel_event
            is_running = self._snapshot["state"] == "running"
        if cancel_event is not None:
            cancel_event.set()
        return {"state": "cancelled", "accepted": is_running}

    def join_all(self, timeout: float = 30.0) -> None:
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)


# --- the CLI ----------------------------------------------------------------------------------------


def _print_plan(chunks: list[dict]) -> None:
    if not chunks:
        print("Nothing to fetch: the requested symbols/dates plan produced zero chunks.")
        return
    symbol_days = sorted({(c["symbol"], c["date"]) for c in chunks})
    print(f"{len(chunks)} chunk(s) over {len(symbol_days)} symbol-day(s).")
    print(f"  first  {chunks[0]['symbol']} {chunks[0]['date']}  {chunks[0]['start']} -> {chunks[0]['end']}")
    print(f"  last   {chunks[-1]['symbol']} {chunks[-1]['date']}  {chunks[-1]['start']} -> {chunks[-1]['end']}")


def main() -> int:
    """``python -m app.research.tick_recorder --symbols AAPL,MSFT --dates 2026-06-01,2026-06-02
    [--dry-run]`` against the operator's real stores -- hermetic and fixture-driven only via this
    iteration's own tests; a real invocation issues real credentialed Alpaca vendor calls (J-06
    step 4, a later, explicit, operator-attended act -- not run by this CLI's own tests)."""
    parser = argparse.ArgumentParser(
        description="Record real Alpaca historical trades+quotes for an explicit symbols x dates "
        "universe -- chunked, throttled, resumable, writing through the unchanged DatasetStore. "
        "Pairs a 1m/5m bar backfill for every symbol-day actually recorded."
    )
    parser.add_argument("--symbols", required=True, help="comma-separated symbols.")
    parser.add_argument("--dates", required=True, help="comma-separated ET session dates (YYYY-MM-DD).")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print the chunk plan and exit having issued no vendor call and written nothing.",
    )
    args = parser.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    dates = [d.strip() for d in args.dates.split(",") if d.strip()]
    chunks = plan_recorder_chunks(symbols, dates)
    if args.dry_run:
        print("DRY RUN -- no vendor call will be issued and nothing will be written.")
        _print_plan(chunks)
        print("\nRe-run without --dry-run to carry this out.")
        return 0

    _print_plan(chunks)
    try:
        verify_preservation_capability()
    except RecorderPreservationCapabilityMissing as exc:
        print(f"recording refused: {exc}")
        return 1

    from .bars import BarStore
    from .routes import get_bar_index, get_registry, get_study_market_adapter

    dataset_dir = CONFIG.dataset_dir_resolved()
    dataset_store = DatasetStore(dataset_dir)
    checkpoint_store = RecorderCheckpointStore(resolve_tick_recorder_checkpoint_dir(dataset_dir))
    run_log_dir = resolve_tick_recorder_log_dir(dataset_dir)
    adapter = get_study_market_adapter()
    bar_store = BarStore(CONFIG.bar_dir_resolved())
    bar_index = get_bar_index()  # the SAME TAPEOLOGY_BAR_INDEX_DB-aware resolver the routes use
    registry = get_registry()

    started_utc = _iso_utc_now()
    walk_started = time.perf_counter()
    done = 0

    def _tick(entry: dict) -> None:
        nonlocal done
        done += 1
        print(
            f"  [{done}/{len(chunks)}] {entry['symbol']} {entry['date']} {entry['start'][11:16]} "
            f"-> {entry['outcome']}" + (f" -- {entry['detail']}" if entry["detail"] else "")
        )

    tick_outcomes = run_tick_recording(
        chunks, dataset_store, checkpoint_store, adapter, CONFIG, progress=_tick,
    )
    bar_outcomes = pair_bar_backfill_for_recorded_days(tick_outcomes, bar_store, bar_index, registry)
    finished_utc = _iso_utc_now()
    failed = sum(1 for o in tick_outcomes if o["outcome"] == "failed")
    run_id = uuid.uuid4().hex
    entry = _run_log_entry(
        run_id, "done", started_utc, finished_utc, len(chunks), tick_outcomes, bar_outcomes, None,
    )
    append_run_log(run_log_dir, entry)
    print(
        f"\ntick recording complete: {entry['chunks_fetched']} fetched · "
        f"{entry['chunks_reused']} reused · {entry['chunks_unchanged']} unchanged · "
        f"{entry['chunks_failed']} failed · {entry['datasets_recorded']} dataset(s) recorded · "
        f"{entry['bars_recorded']} bar(s) paired in {time.perf_counter() - walk_started:.1f}s -- "
        f"run {run_id}."
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
