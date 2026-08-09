"""The deep fine-bar backfill: 1m/5m history from the credentialed Alpaca adapter, for the years
Yahoo will not serve.

**The wall this exists to break.** A forward return is measured ONLY from 1m or 5m bars inside the
screen date's own session (``desk_forward.DESK_FORWARD_TOUCH_TIMEFRAMES``). The desk top-up fetches
those from Yahoo, which retains roughly the last 30 days of 1m and 60 of 5m
(``providers/adapters/yahoo.py``'s ``_INTERVAL_LIMITS``), and the walk floors at exactly those
(``desk_topup_compute._TOPUP_FINE_LOOKBACK_DAYS``) because -- for THAT vendor -- there is nothing to
deepen into. Every screen date older than the floor is therefore structurally unmeasurable: on
2026-08-08 the desk had 938 dates with a finished forward run, of which 507 measured ZERO rows and
only 35 measured all 101. Averaged per month out of 101 members: 0.0 through all of 2024, 1.3-1.7
through 2025, 2.1-4.3 through 2026-01..05, then 58.0 in June and 71.7 in July as the Yahoo top-up
finally reached them.

**Why a second vendor rather than a bigger Yahoo window.** ``AlpacaAdapter`` has no retention table
at all: no ``_INTERVAL_LIMITS``, no ``bar_fetch_limit``. Its only clamp is the recency embargo on
the END bound (``_bar_fetch_end_clamp``, ~900s), and the START bound is never trimmed. The whole
mechanism to reach it already shipped and has never had a caller: ``BarRecordRequest.vendor``
(``routes.py``) selects the adapter, the recording is stamped ``feed="sip"``, and ``feed`` is part
of both the content checksum and the ``bar_index`` primary key -- so an Alpaca series can never
collide with, or be mistaken for, a Yahoo one. This module is only the caller.

**The overlap rule, and why it is not optional.** ``BarStore.merged_bars`` de-duplicates by
timestamp with MOST-RECENTLY-CREATED-SERIES-WINS. A deep Alpaca fetch that reached into the region
Yahoo already recorded would therefore silently replace the recent tape's Yahoo split/dividend-
adjusted prices with SIP raw ones, for every contested minute, in a store where nothing can be
deleted or re-tagged. So every window this module plans is clamped to END BEFORE the Yahoo-covered
region begins (``_TOPUP_FINE_LOOKBACK_DAYS`` per timeframe, the exact same constant the top-up
floors at). The two vendors' regions meet and never overlap.

**Month chunks, and why.** One immutable file per (symbol, timeframe, month) rather than one
multi-year series: a chunk is ~1-2MB instead of tens, a single bad row or vendor timeout scopes its
failure to one month instead of losing a whole symbol, and the walk is resumable for free -- a
re-run of an already-recorded chunk is answered store-first with ZERO vendor calls (Alpaca records
carry ``vendor_limit: None``, so ``_clamped_window_may_have_grown`` is always false).

**Confinement.** This module never names an Alpaca credential and never imports the Alpaca SDK
(``test_real_data_gate.py``'s two confinement rails: both are permitted in exactly ONE module,
``providers/adapters/alpaca.py``). It passes the string ``"alpaca"`` and nothing else; a missing
credential surfaces as ``record_bar_series``'s existing 503, classified here as a per-chunk
``"failed"`` outcome with the detail preserved verbatim.

**No new ``Config`` field.** Every constant here is a plain module constant and the storage dir is
a bare env-var-or-sibling default (the ``desk_topup_log.resolve_desk_topup_log_dir`` pattern), so
``config_fingerprint()`` is untouched.

**What a backfill re-keys.** ``desk_forward.compute_forward_input_signature`` hashes the 1m/5m
series on file, so new fine bars produce a NEW forward key: the affected dates need their forward
measurement re-run (nothing is rewritten -- the old record stays, and the new one is a new version).
Recorded SCREEN pins do not move: ``desk_screen._bar_store_signature`` covers the coarse four only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
import time
import uuid
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from fastapi import HTTPException

from ..config import CONFIG
from .bar_index import BarIndex
from .bars import BarStore
from .desk_topup_compute import _TOPUP_FINE_LOOKBACK_DAYS
from .desk_universe import UniverseStore
from .routes import (
    BarRecordRequest,
    ResearchRegistry,
    get_bar_index,
    get_bar_store,
    get_registry,
    record_bar_series,
)

__all__ = [
    "DESK_DEEP_TIMEFRAMES",
    "DESK_DEEP_VENDOR",
    "DeskDeepBackfillComputeManager",
    "DeepBackfillRunStore",
    "plan_deep_windows",
    "record_deep_backfill_run",
    "resolve_desk_deep_backfill_log_dir",
    "run_deep_backfill",
]

# The timeframes a forward measurement can actually read (``desk_forward``'s touch ladder). Anything
# coarser reaches back years through Yahoo already and needs no second vendor; anything finer this
# product does not model. A plain structural constant, NOT a ``Config`` field.
DESK_DEEP_TIMEFRAMES: tuple[str, ...] = ("1m", "5m")

# The adapter selector passed to ``record_bar_series``. A bare string on purpose -- naming the
# adapter class here would drag the Alpaca SDK import out of its one permitted module.
DESK_DEEP_VENDOR = "alpaca"

# Chunk size. Days rather than calendar months so a window's length never depends on which month it
# starts in -- 28 keeps a 1m chunk (~390 bars/session x ~20 sessions ≈ 8k bars) comfortably inside
# one or two SDK pages.
DESK_DEEP_CHUNK_DAYS = 28

# How many chunks may be in flight at once. Mirrors the top-up walk's own default and ceiling: a
# chunk is dominated by vendor round-trips, and a vendor that starts rate-limiting should not be
# hammered harder. ``=1`` restores a strictly serial walk.
_DEEP_WORKERS_ENV = "TAPEOLOGY_DESK_DEEP_BACKFILL_WORKERS"
_DEFAULT_DEEP_WORKERS = 4
_MAX_DEEP_WORKERS = 8

# The run log's own env-var override (the ``TAPEOLOGY_DESK_TOPUP_LOG_DIR`` pattern).
_DEEP_LOG_DIR_ENV = "TAPEOLOGY_DESK_DEEP_BACKFILL_LOG_DIR"

_TERMINAL_STATES = ("done", "cancelled", "failed")


class DeepBackfillRunIntegrityError(Exception):
    """An on-disk run-record file failed its checksum verification on load — corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated record)."""


def resolve_desk_deep_backfill_log_dir(desk_universe_dir_resolved: str) -> str:
    """The deep-backfill run log's directory: the ``TAPEOLOGY_DESK_DEEP_BACKFILL_LOG_DIR`` env var
    if set, else a sibling of the caller's already-resolved universe directory. The
    ``resolve_desk_topup_log_dir`` pattern verbatim — an operational storage-location knob, never a
    value that shapes a served result, so ``config_fingerprint()`` stays untouched."""
    override = os.environ.get(_DEEP_LOG_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "deep_backfill_runs")


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _deep_workers() -> int:
    raw = os.environ.get(_DEEP_WORKERS_ENV)
    if raw is None:
        return _DEFAULT_DEEP_WORKERS
    try:
        value = int(raw)
    except ValueError:
        return _DEFAULT_DEEP_WORKERS
    return max(1, min(_MAX_DEEP_WORKERS, value))


# --- window planning -----------------------------------------------------------------------------


def deep_window_ceiling(timeframe: str, today: date) -> str:
    """The first date this module must NOT reach, for one timeframe: where the Yahoo-covered region
    begins (``today - _TOPUP_FINE_LOOKBACK_DAYS[timeframe]``, the exact constant the top-up floors
    at). Reusing that one constant is what guarantees the two vendors' regions meet without
    overlapping — a separate number here would drift and start silently overwriting Yahoo's recent
    tape.

    EXCLUSIVE, and the distinction is load-bearing: ``POST /research/bars`` treats ``end`` as
    INCLUSIVE by UTC calendar date (it floors ``end`` to its day and adds one for the vendor call),
    so the last date a planned window may name is the day BEFORE this one."""
    lookback = _TOPUP_FINE_LOOKBACK_DAYS.get(timeframe)
    if lookback is None:
        raise ValueError(
            f"{timeframe!r} has no fine-bar retention floor -- this module backfills only "
            f"{DESK_DEEP_TIMEFRAMES}, the timeframes a forward measurement can read"
        )
    return (today - timedelta(days=lookback)).isoformat()


def plan_deep_windows(
    members: list[str],
    timeframes: tuple[str, ...] | list[str],
    from_day: str,
    to_day: str,
    today: date,
) -> list[dict]:
    """Every chunk a backfill WOULD fetch, computed without touching a store or a vendor:
    ``[{"symbol", "timeframe", "start", "end"}, ...]`` in ``(symbol, timeframe, start)`` order.

    ``start`` and ``end`` are both INCLUSIVE UTC dates, matching what ``POST /research/bars``
    actually does with them — so consecutive chunks abut at ``next.start == prev.end + 1 day``
    rather than sharing a boundary date, and the last chunk ends the day BEFORE
    ``deep_window_ceiling``. Getting that one day wrong would put every planned sweep one session
    inside the Yahoo-covered region, where the newest-created-series-wins merge would replace
    Yahoo's prices with SIP ones permanently.

    A caller asking for a ``to_day`` inside the Yahoo-covered region gets the honest truncated plan
    rather than an overlap, and a timeframe whose whole requested range sits above its ceiling
    contributes no chunks at all — the correct answer, not an error: those bars are already on file
    from the top-up.

    Pure and clock-free: ``today`` is passed in, so a dry run and the apply that follows it plan
    identically rather than drifting across a date boundary."""
    plan: list[dict] = []
    for symbol in members:
        for timeframe in timeframes:
            # Both bounds carried as EXCLUSIVE dates through the walk (half-open arithmetic is what
            # makes contiguity checkable), then emitted inclusive on the way out.
            last_exclusive = min(
                date.fromisoformat(to_day) + timedelta(days=1),
                date.fromisoformat(deep_window_ceiling(timeframe, today)),
            )
            cursor = date.fromisoformat(from_day)
            while cursor < last_exclusive:
                chunk_end_exclusive = min(
                    cursor + timedelta(days=DESK_DEEP_CHUNK_DAYS), last_exclusive
                )
                plan.append(
                    {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "start": f"{cursor.isoformat()}T00:00:00Z",
                        "end": f"{(chunk_end_exclusive - timedelta(days=1)).isoformat()}T00:00:00Z",
                    }
                )
                cursor = chunk_end_exclusive
    return plan


# --- the shared walker ---------------------------------------------------------------------------


def _run_one_chunk(
    chunk: dict,
    bar_store: BarStore,
    bar_index: BarIndex,
    registry: ResearchRegistry,
) -> tuple[str, str | None, int]:
    """Fetch+record ONE chunk through ``record_bar_series`` (in-process — never a second
    fetch-and-record implementation) and classify the honest outcome, mirroring
    ``desk_topup_compute._run_one_pair``'s own four-value vocabulary:

      * ``"reused"``    — answered store-first, zero vendor calls (this is what makes an
        interrupted backfill cheap to resume).
      * ``"fetched"``   — a real vendor call ran and a BRAND NEW series was recorded.
      * ``"unchanged"`` — a real vendor call ran and returned content already registered (409).
      * ``"failed"``    — anything else, detail preserved verbatim, and the walk continues to the
        remaining chunks rather than aborting. A missing credential lands here as the adapter's
        existing 503, once per chunk, saying so plainly.

    The third return value is the recorded bar count (``0`` for every non-``"fetched"`` outcome), so
    the run ledger can state what a backfill actually put on disk rather than how many calls it
    made."""
    body = BarRecordRequest(
        symbol=chunk["symbol"],
        timeframe=chunk["timeframe"],
        start=chunk["start"],
        end=chunk["end"],
        vendor=DESK_DEEP_VENDOR,
    )
    t_before = datetime.now(timezone.utc)
    try:
        result = record_bar_series(body=body, registry=registry, store=bar_store, index=bar_index)
    except HTTPException as exc:
        if exc.status_code == 409:
            return "unchanged", str(exc.detail), 0
        return "failed", str(exc.detail), 0
    except Exception as exc:  # noqa: BLE001 -- never swallowed, never aborts the whole run
        return "failed", str(exc), 0

    meta = result["bar_series"]
    created_utc = meta.get("created_utc")
    created = (
        datetime.fromisoformat(created_utc.replace("Z", "+00:00")) if created_utc else None
    )
    if created is not None and created >= t_before:
        return "fetched", None, int(meta.get("bar_count") or 0)
    return "reused", None, 0


def run_deep_backfill(
    chunks: list[dict],
    bar_store: BarStore,
    bar_index: BarIndex,
    registry: ResearchRegistry,
    *,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> list[dict]:
    """Walk ``chunks`` in order, calling ``_run_one_chunk`` for each — the SOLE walker; the manager
    and the CLI both call this and nothing else (the ``run_topup`` precedent). Returns the per-chunk
    outcome dicts in iteration order: the planned chunk's own four fields plus ``"outcome"``,
    ``"detail"`` and ``"bars_recorded"``.

    ``progress``, if given, is called after EACH chunk with the entry just appended.
    ``should_abort``, if given and true BEFORE a chunk starts, stops the walk early — the returned
    list is simply shorter than ``len(chunks)``. A cooperative stop, never a raise: a chunk already
    in flight is allowed to finish and be recorded, since it has already paid for its vendor call.
    """

    def walk_one(chunk: dict) -> dict:
        outcome, detail, bars = _run_one_chunk(chunk, bar_store, bar_index, registry)
        return {**chunk, "outcome": outcome, "detail": detail, "bars_recorded": bars}

    outcomes: list[dict] = []
    workers = _deep_workers()

    if workers <= 1:
        for chunk in chunks:
            if should_abort is not None and should_abort():
                return outcomes
            entry = walk_one(chunk)
            outcomes.append(entry)
            if progress is not None:
                progress(entry)
        return outcomes

    # Overlapped walk, results consumed STRICTLY in plan order so `outcomes` and every `progress`
    # call are byte-identical in content and sequence to the serial walk above -- only the
    # wall-clock differs (the `run_topup` overlapped-walk shape verbatim).
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="desk-deep") as pool:
        inflight: deque[Future] = deque()
        dispatched = 0
        while True:
            aborted = should_abort is not None and should_abort()
            while not aborted and dispatched < len(chunks) and len(inflight) < workers:
                inflight.append(pool.submit(walk_one, chunks[dispatched]))
                dispatched += 1
            if not inflight:
                return outcomes
            entry = inflight.popleft().result()
            outcomes.append(entry)
            if progress is not None:
                progress(entry)


# --- the durable run ledger ----------------------------------------------------------------------


class DeepBackfillRunStore:
    """File-based store rooted at the deep-backfill log directory — the ONE reader/writer. Mirrors
    ``desk_topup_log.TopupRunStore`` exactly: checksum-verified load on every read, ``record`` the
    only mutation, no update/delete anywhere, and NO content-keyed dedup (every terminal run is a
    genuinely distinct event, even an all-``"reused"`` one over an unchanged store).

    A run whose process ends before the writer is called leaves NO record — ``record()`` is the only
    write path and it runs exactly once, at terminal state. There is no "pending" or "partial" file
    ever written."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.json"

    def _load(self, path: Path) -> dict:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise DeepBackfillRunIntegrityError(
                f"deep-backfill run record file '{path.name}' is not parseable ({exc}) -- "
                f"corrupted or tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise DeepBackfillRunIntegrityError(
                f"deep-backfill run record file '{path.name}' does not carry the expected record "
                f"shape -- corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise DeepBackfillRunIntegrityError(
                f"deep-backfill run record file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise DeepBackfillRunIntegrityError(
                f"deep-backfill run record file '{path.name}' does not carry the expected record "
                f"shape -- corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every registered run's full content (each file verified), oldest-started first, plus an
        EXPLICIT error row per file that failed verification. A directory that was never created
        returns ``([], [])`` — the honest-empty case."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                meta = self._load(path)
                records.append({**meta, "outcomes": [dict(o) for o in meta["outcomes"]]})
            except DeepBackfillRunIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("started_utc", ""), meta.get("id", "")))
        return records, errors

    def record(
        self,
        *,
        vendor: str,
        requested_window: dict,
        timeframes: list[str],
        members_total: int,
        config_fingerprint: str,
        started_utc: str,
        finished_utc: str,
        state: str,
        chunks_total: int,
        outcomes: list[dict],
    ) -> dict:
        """Persist ONE new deep-backfill run record — ALWAYS a genuinely new file. Every count is
        DERIVED here from ``outcomes`` rather than tracked separately, so a summary can never
        disagree with the rows it summarises."""
        if state not in _TERMINAL_STATES:
            raise ValueError(
                f"invalid terminal state {state!r} -- must be one of {_TERMINAL_STATES}"
            )
        run_date = started_utc[:10]
        run_id = f"deepbackfill-{run_date}-{uuid.uuid4().hex[:12]}"
        while self._path(run_id).exists():
            run_id = f"deepbackfill-{run_date}-{uuid.uuid4().hex[:12]}"
        meta = {
            "id": run_id,
            "vendor": vendor,
            "requested_window": dict(requested_window),
            "timeframes": list(timeframes),
            "members_total": members_total,
            "config_fingerprint": config_fingerprint,
            "started_utc": started_utc,
            "finished_utc": finished_utc,
            "state": state,
            "chunks_total": chunks_total,
            "chunks_attempted": len(outcomes),
            "chunks_fetched": sum(1 for o in outcomes if o["outcome"] == "fetched"),
            "chunks_reused": sum(1 for o in outcomes if o["outcome"] == "reused"),
            "chunks_unchanged": sum(1 for o in outcomes if o["outcome"] == "unchanged"),
            "chunks_failed": sum(1 for o in outcomes if o["outcome"] == "failed"),
            "bars_recorded": sum(int(o.get("bars_recorded") or 0) for o in outcomes),
            "outcomes": [dict(o) for o in outcomes],
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(run_id).write_text(json.dumps(payload))
        return dict(meta)


def record_deep_backfill_run(store: DeepBackfillRunStore, **fields) -> dict:
    """THE single shared writer — called exactly once, at a run's terminal state, by BOTH the
    manager's worker resolve path and the CLI's ``main()``, and nothing else (the
    ``record_topup_run`` precedent: one grep finds both, and only, call sites)."""
    return store.record(**fields)


# --- the compute manager -------------------------------------------------------------------------


def _copy_snapshot(snapshot: dict) -> dict:
    progress = snapshot["progress"]
    return {
        **snapshot,
        "progress": {**progress, "outcomes": [dict(entry) for entry in progress["outcomes"]]},
    }


class DeskDeepBackfillComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) deep-backfill job — the
    ``DeskTopupComputeManager`` shape verbatim: constructed with no arguments, every ``trigger()``
    takes its stores/registry explicitly, single-flight, cancellable, progress-publishing, and the
    walk runs on a worker thread so an HTTP route returns immediately.

    Cancel and resume are load-bearing here rather than a nicety: a full 1m+5m sweep back to 2025 is
    tens of millions of bars over hours of sequential vendor pagination, and every chunk already
    recorded is answered store-first on the next run."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict | None = None
        self._cancel_event: threading.Event | None = None
        self._thread: threading.Thread | None = None

    def snapshot(self) -> dict | None:
        current = self._snapshot
        if current is None:
            return None
        return _copy_snapshot(current)

    def trigger(
        self,
        universe_store: UniverseStore,
        bar_store: BarStore,
        bar_index: BarIndex,
        registry: ResearchRegistry,
        run_store: DeepBackfillRunStore,
        *,
        from_day: str,
        to_day: str,
        timeframes: tuple[str, ...] | list[str] = DESK_DEEP_TIMEFRAMES,
        today: date | None = None,
    ) -> dict:
        """Start a NEW deep-backfill job over the LATEST universe snapshot's members for
        ``[from_day, to_day]``, or — if one is already running — return it UNCHANGED
        (``started: False``, single-flight). No universe snapshot registered yet resolves to an
        honest zero-chunk job that finishes immediately, never an error.

        ``today`` defaults to the wall-clock UTC date and exists so a test can pin the overlap
        ceiling. It bounds only WHICH windows are asked for, never any recorded value."""
        with self._lock:
            current = self._snapshot
            if current is not None and current["state"] == "running":
                return {"started": False, "compute": _copy_snapshot(current)}

            records, _errors = universe_store.list()
            members: list[str] = list(records[-1]["members"]) if records else []
            chunks = plan_deep_windows(
                members,
                timeframes,
                from_day,
                to_day,
                today or datetime.now(timezone.utc).date(),
            )

            job_id = uuid.uuid4().hex
            started_utc = _iso_utc_now()
            cancel_event = threading.Event()
            self._cancel_event = cancel_event
            snapshot = {
                "id": job_id,
                "state": "running",
                "started_utc": started_utc,
                "finished_utc": None,
                "error": None,
                "requested_window": {"start": from_day, "end": to_day},
                "timeframes": list(timeframes),
                "progress": {
                    "chunks_total": len(chunks),
                    "chunks_done": 0,
                    "bars_recorded": 0,
                    "outcomes": [],
                },
            }
            self._snapshot = snapshot

        members_total = len({chunk["symbol"] for chunk in chunks})
        collected: list[dict] = []

        def _publish(entry: dict) -> None:
            collected.append(entry)
            with self._lock:
                current = self._snapshot
                if current is None or current["id"] != job_id:
                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
                progress = current["progress"]
                self._snapshot = {
                    **current,
                    "progress": {
                        **progress,
                        "chunks_done": progress["chunks_done"] + 1,
                        "bars_recorded": progress["bars_recorded"]
                        + int(entry.get("bars_recorded") or 0),
                        "outcomes": [*progress["outcomes"], entry],
                    },
                }

        def _record_run(*, state: str, outcomes: list[dict]) -> None:
            record_deep_backfill_run(
                run_store,
                vendor=DESK_DEEP_VENDOR,
                requested_window={"start": from_day, "end": to_day},
                timeframes=list(timeframes),
                members_total=members_total,
                config_fingerprint=CONFIG.config_fingerprint(),
                started_utc=started_utc,
                finished_utc=_iso_utc_now(),
                state=state,
                chunks_total=len(chunks),
                outcomes=outcomes,
            )

        def _work() -> None:
            try:
                outcomes = run_deep_backfill(
                    chunks, bar_store, bar_index, registry,
                    progress=_publish, should_abort=cancel_event.is_set,
                )
            except Exception as exc:  # noqa: BLE001 -- a failure OUTSIDE any single chunk
                self._resolve(job_id, "failed", error=str(exc))
                _record_run(state="failed", outcomes=collected)
                return
            state = "cancelled" if cancel_event.is_set() else "done"
            self._resolve(job_id, state, error=None)
            _record_run(state=state, outcomes=outcomes)

        thread = threading.Thread(target=_work, name=f"desk-deep-backfill:{job_id}", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return {"started": True, "compute": _copy_snapshot(snapshot)}

    def _resolve(self, job_id: str, state: str, *, error: str | None) -> None:
        with self._lock:
            current = self._snapshot
            if current is None or current["id"] != job_id:
                return  # superseded -- never resolve a job that is no longer the current one
            self._snapshot = {
                **current,
                "state": state,
                "finished_utc": _iso_utc_now(),
                "error": error,
            }

    def cancel(self) -> None:
        """Signal cooperative cancellation for the in-flight job — a harmless no-op if idle (the
        ROUTE rejects an idle cancel with a 409)."""
        with self._lock:
            cancel_event = self._cancel_event
        if cancel_event is not None:
            cancel_event.set()

    def join_all(self, timeout: float = 30.0) -> None:
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)


# --- The CLI -------------------------------------------------------------------------------------


def _print_plan(chunks: list[dict]) -> None:
    if not chunks:
        print(
            "Nothing to fetch: every requested window sits inside the region the Yahoo top-up "
            "already covers, so a deep fetch would only contest bars already on file."
        )
        return
    by_timeframe: dict[str, int] = {}
    for chunk in chunks:
        by_timeframe[chunk["timeframe"]] = by_timeframe.get(chunk["timeframe"], 0) + 1
    symbols = {chunk["symbol"] for chunk in chunks}
    print(
        f"{len(chunks)} chunk(s) over {len(symbols)} symbol(s): "
        + ", ".join(f"{tf} {count}" for tf, count in sorted(by_timeframe.items()))
    )
    print(f"  first  {chunks[0]['symbol']} {chunks[0]['timeframe']}  {chunks[0]['start']} -> {chunks[0]['end']}")
    print(f"  last   {chunks[-1]['symbol']} {chunks[-1]['timeframe']}  {chunks[-1]['start']} -> {chunks[-1]['end']}")


def main() -> int:
    """``python -m app.research.desk_deep_backfill --from YYYY-MM-DD --to YYYY-MM-DD
    [--symbols A,B] [--timeframes 1m,5m] [--dry-run]`` against the operator's real stores."""
    parser = argparse.ArgumentParser(
        description="Backfill deep 1m/5m history from the credentialed Alpaca adapter, for the "
        "years the Yahoo top-up cannot reach. Every window is clamped to end before the "
        "Yahoo-covered region, so the two vendors' bars meet without overlapping."
    )
    parser.add_argument("--from", dest="from_day", required=True, help="first date (YYYY-MM-DD).")
    parser.add_argument("--to", dest="to_day", required=True, help="last date (YYYY-MM-DD).")
    parser.add_argument(
        "--symbols", default=None,
        help="comma-separated symbols; default is the latest universe snapshot's whole membership.",
    )
    parser.add_argument(
        "--timeframes", default=",".join(DESK_DEEP_TIMEFRAMES),
        help=f"comma-separated timeframes; default {','.join(DESK_DEEP_TIMEFRAMES)}.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print the window plan and exit having issued no vendor call and written nothing.",
    )
    args = parser.parse_args()

    universe_dir = CONFIG.desk_universe_dir_resolved()
    if args.symbols:
        members = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        records, _errors = UniverseStore(universe_dir).list()
        members = list(records[-1]["members"]) if records else []
    timeframes = tuple(t.strip() for t in args.timeframes.split(",") if t.strip())

    chunks = plan_deep_windows(
        members, timeframes, args.from_day, args.to_day, datetime.now(timezone.utc).date()
    )
    if args.dry_run:
        print(f"DRY RUN -- no vendor call will be issued and nothing will be written.")
        _print_plan(chunks)
        print("\nRe-run without --dry-run to carry this out.")
        return 0

    _print_plan(chunks)
    bar_store = get_bar_store()
    bar_index = get_bar_index()
    run_store = DeepBackfillRunStore(resolve_desk_deep_backfill_log_dir(universe_dir))
    started_utc = _iso_utc_now()
    walk_started = time.perf_counter()

    done = 0

    def _tick(entry: dict) -> None:
        nonlocal done
        done += 1
        print(
            f"  [{done}/{len(chunks)}] {entry['symbol']} {entry['timeframe']} "
            f"{entry['start'][:10]} -> {entry['outcome']}"
            + (f" ({entry['bars_recorded']} bars)" if entry["bars_recorded"] else "")
            + (f" -- {entry['detail']}" if entry["detail"] else "")
        )

    outcomes = run_deep_backfill(
        chunks, bar_store, bar_index, get_registry(), progress=_tick
    )
    meta = record_deep_backfill_run(
        run_store,
        vendor=DESK_DEEP_VENDOR,
        requested_window={"start": args.from_day, "end": args.to_day},
        timeframes=list(timeframes),
        members_total=len({c["symbol"] for c in chunks}),
        config_fingerprint=CONFIG.config_fingerprint(),
        started_utc=started_utc,
        finished_utc=_iso_utc_now(),
        state="done",
        chunks_total=len(chunks),
        outcomes=outcomes,
    )
    print(
        f"\ndeep backfill complete: {meta['chunks_fetched']} fetched · "
        f"{meta['chunks_reused']} reused · {meta['chunks_unchanged']} unchanged · "
        f"{meta['chunks_failed']} failed · {meta['bars_recorded']} bars recorded "
        f"in {time.perf_counter() - walk_started:.1f}s -- run {meta['id']}."
    )
    return 1 if meta["chunks_failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
