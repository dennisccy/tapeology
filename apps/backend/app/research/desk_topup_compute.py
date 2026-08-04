"""Era B "The Desk" (J-02) — the desk bar top-up: a single-flight, cancellable, progress-reporting
background job that walks the latest universe snapshot's members x the pinned
``desk_coverage.DESK_TOPUP_TIMEFRAMES`` set, in-process, through the SAME existing
``record_bar_series`` fetch-and-record logic ``POST /research/bars`` already uses (store-first,
resumable, unmodified) — never a second fetch-and-record implementation. Plus a CLI warmer that
drives the SAME walk synchronously, in-process, for the operator's real ~100-symbol run.

Mirrors ``edge_report_compute.EdgeReportComputeManager`` verbatim in shape: one in-flight job slot
(``self._snapshot``), an in-memory, process-scoped progress snapshot
(``id``/``state``/``started_utc``/``finished_utc``/``error``/``progress``), cooperative cancel, an
atomic snapshot publish under a lock (a fresh dict rebound in ONE assignment, never mutated in
place) so a concurrent reader's ``snapshot()`` call always sees a caller-safe, internally
consistent copy. Job state is process-scoped bookkeeping — honestly lost on restart, never a
research value (the SAME contract every compute manager in this app already carries).

**THIS MODULE MUST NOT be imported by ``routes.py``.** ``record_bar_series`` — the fetch-and-record
logic this module reuses — lives in ``routes.py``, so this module imports FROM ``routes.py`` (a
one-way edge). If ``routes.py`` (or ``ResearchRegistry``) imported anything back from this module,
that would be a circular import; consequently the ``DeskTopupComputeManager`` INSTANCE does NOT
live on ``ResearchRegistry`` (unlike ``EdgeReportComputeManager``) — it lives as a module-level
singleton behind a FastAPI dependency in ``desk_routes.py``, test-overridable exactly like
``get_universe_fetcher``.

**Resumability comes from ``record_bar_series``'s OWN store-first coordinator, not from job-level
checkpoint bookkeeping.** A cancelled run's ``outcomes`` list simply has fewer than ``pairs_total``
entries; a FRESH ``trigger()`` call (a new job, from scratch) walks every pair again, but every pair
already recorded during the earlier attempt now answers "reused" with zero vendor calls — the SAME
index-backed store-first hit ``POST /research/bars`` already guarantees. No separate "resume from
pair N" bookkeeping exists, or is needed.

**Determining "reused" vs "fetched" without re-deriving ``record_bar_series``'s own internal
adapter/feed-resolution logic.** ``record_bar_series`` returns the SAME ``{"bar_series": meta}``
shape whether it answered store-first or ran a real vendor fetch — so this module classifies the
outcome by comparing the returned series' ``created_utc`` (stamped by ``BarStore.record`` at
``datetime.now(timezone.utc)`` the instant a NEW series is written) against a timestamp captured
immediately BEFORE the call: a store-first hit's ``created_utc`` necessarily predates that
timestamp (the series already existed), while a freshly-written series' ``created_utc`` is stamped
at or after it. This reads only the ALREADY-RETURNED ``created_utc`` field — it duplicates none of
``record_bar_series``'s own adapter-selection/feed-derivation decisions, so it cannot drift out of
sync with that logic.

**goal-desk-iter-26, J-17 — a per-pair fetch window derived from the store's OWN content, plus the
honest ``"unchanged"`` outcome.** ``_pair_window`` (below) reads ONE pair's own frozen bars via the
SAME canonical ``BarStore.merged_bars`` accessor ``desk_screen.py``'s reference-close/history walk
already uses (never ``bar_index``'s ``window_end_utc``, which records what an EARLIER run ASKED
for, not what the store can prove) and picks one of two windows: the byte-identical full
``_TOPUP_LOOKBACK_DAYS`` window ``_fetch_window_now()`` already asks for today (nothing frozen yet,
or a frozen history that does not reach back that far — short histories keep deepening exactly as
they do today), or — once the pair's frozen history reaches the lookback start — a TAIL window
``[that pair's own newest frozen bar's UTC date, today]``, so the boundary session is always
re-requested and re-merged, never assumed complete. ``_run_one_pair`` calls it once, internally, to
build the actual fetch body; ``run_topup`` calls it again, independently, immediately BEFORE
calling ``_run_one_pair`` for the SAME pair, purely to capture the pre-fetch provenance
(``requested_window``/``store_frozen_from``/``store_frozen_through``/``window_basis``) for that
pair's outcome entry — both reads see identical content because nothing is written to the store
between them, so the two calls always agree. ``_run_one_pair``'s own call signature/return contract
is UNCHANGED (still ``(symbol, timeframe, bar_store, bar_index, registry) -> (outcome, str|None)``)
so every existing test that monkeypatches it wholesale keeps working unmodified.

A tail window makes the vendor's "you already have this" answer — ``record_bar_series``'s own 409
(``BarSeriesAlreadyRegistered``, ``routes.py:681``) — the NORMAL weekend/holiday response, not a
failure: ``_run_one_pair`` now classifies a 409 specifically as ``"unchanged"`` (a vendor call ran
and returned only bars already frozen), distinct from ``"reused"`` (a store-first exact-key hit,
ZERO vendor calls — unchanged meaning). Every OTHER refusal keeps its verbatim detail and its
``"failed"`` label.

**J-09 — the append-only run log.** Every run's OWN already-computed outcomes are persisted, once,
at terminal state, by the single shared writer ``desk_topup_log.record_topup_run`` — called from
BOTH ``_work``'s two exit paths below (the ``except`` branch for a whole-job ``"failed"``, and the
normal ``"cancelled"``/``"done"`` path) and once more from the CLI's ``main()`` after ``run_topup``
returns successfully. ``universe_snapshot_id`` and the run's ``requested_window`` (one
``_fetch_window_now()`` call, captured ONCE per run in the caller — never re-derived inside the
writer, never a second call inside ``_run_one_pair``, which keeps its own existing per-pair call
byte-unchanged) are threaded through as plain local/closure values — never added as a new key on
``self._snapshot`` (that dict stays exactly the J-02 shape; the run LOG is a separate, durable
concern). A run-level ``state: "failed"`` (something escaped ``run_topup`` itself) is NOT the same
thing as a per-pair ``outcome: "failed"`` (already caught inside ``_run_one_pair`` and folded into
``outcomes`` — the job still resolves ``"done"``): the ``except`` branch below writes a record with
whatever outcomes were published before the crash (a local ``collected`` list, independent of the
shared ``self._snapshot`` to avoid any race with a superseding job); the CLI path has no cancel
signal and normally only ever terminates ``"done"``, so an uncaught crash BEFORE its own writer
call is the correct interrupted-run case — zero record, never a bug to guard against.

**goal-desk-iter-32, J-19 — the date each pair's frozen history actually reaches AFTER the run.**
Every recorded run's own artifact (``requested_window``/``store_frozen_from``/
``store_frozen_through``) describes the store's content BEFORE that pair's own fetch attempt —
nothing anywhere records what the pair's frozen history reaches once the attempt ENDS. ``run_topup``
closes that gap with ONE additive field, ``store_frozen_through_after``: immediately after
``_run_one_pair`` returns for a pair, a SECOND, independent call to the SAME pure accessor,
``_pair_window(bar_store, symbol, timeframe)`` (never a new accessor, never ``bar_index``'s
``window_end_utc``, never arithmetic over bars), reads that pair's newest frozen bar as it stands
right now and the value is copied onto the outcome entry verbatim. For a ``"reused"``/``"unchanged"``/
``"failed"`` pair nothing was written to the store between the two calls, so the two reads always
agree byte-for-byte with the pair's own pre-fetch ``store_frozen_through``; for a ``"fetched"`` pair
the store gained a brand new series between the two calls, so the second read genuinely differs
(later) from the first. The value is ``null`` only when the pair holds no frozen bars at all (never
fetched anything, or fetched and failed) — exactly the shape ``store_frozen_through`` already uses.
This is a strictly LOCAL, per-pair, attempt-time OBSERVATION — it states nothing about current
coverage or freshness generally (that stays ``desk_coverage.get_desk_coverage`` over ``bar_index``,
untouched), creates no second coverage path, and adds no new accessor, fetch, store, route, Config
field, or MCP tool. ``_run_one_pair``'s own two-value return contract
(``(symbol, timeframe, bar_store, bar_index, registry) -> (outcome, str | None)``) is UNCHANGED, so
every existing test that monkeypatches it wholesale keeps working unmodified — the new field is
computed entirely inside ``run_topup`` itself, one level above the fake boundary. The append-only
writer, ``desk_topup_log.record_topup_run``, needs no change (a pure, schema-agnostic passthrough):
a run recorded BEFORE this field existed keeps its outcome entries exactly as recorded, served
verbatim, and ``/desk`` renders their absence as the honest ``"library reach not recorded in this
run"`` fallback — never a computed or backfilled value."""

from __future__ import annotations

import argparse
import sys
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable

from fastapi import HTTPException

from ..config import CONFIG
from .bar_index import BarIndex
from .bars import BarStore
from .desk_coverage import DESK_TOPUP_TIMEFRAMES
from .desk_topup_log import TopupRunStore, record_topup_run, resolve_desk_topup_log_dir
from .desk_universe import UniverseStore
from .routes import (
    BarRecordRequest,
    ResearchRegistry,
    get_bar_index,
    get_bar_store,
    record_bar_series,
)
from .store import JournalStore

__all__ = [
    "DESK_TOPUP_FINE_TIMEFRAMES",
    "DeskTopupComputeManager",
    "TOPUP_WALK_TIMEFRAMES",
    "run_topup",
]

# The top-up's fetch horizon — a SINGLE wide lookback shared by all four pinned timeframes, chosen
# to match the Yahoo adapter's OWN ``1h``/``4h`` retention ceiling
# (``providers/adapters/yahoo.py:95`` — ``_INTERVAL_LIMITS["1h"] == (730, 730)``), so a ``1h``/
# ``4h`` request asks for exactly what the vendor can serve; ``1d``/``1w`` are unlimited, but 730
# days is already ample history for a daily-close screen (``levels.PRIOR_PERIOD_TIMEFRAMES`` only
# ever needs the most recently CLOSED period). A plain module constant, not a ``Config`` field —
# the SAME "not a fingerprint-stability field" rationale ``yahoo.py``'s own ``_INTERVAL_LIMITS``
# carries: it shapes no persisted tape/backtest/study value, only which bars a top-up call happens
# to ASK the vendor for; the adapter's OWN ``_clamp_to_retention`` still honestly trims/notes any
# further shortfall, exactly as it already does for a manual ``POST /research/bars`` call. This
# module needs no per-timeframe retention table of its own — the adapter already owns that.
_TOPUP_LOOKBACK_DAYS = 730

# Forward-test era: the fine intraday set the WALKER additionally tops up, so the desk forward
# measurement (``desk_forward.py``) has 1m/5m paths to read. Deliberately a SEPARATE constant from
# ``desk_coverage.DESK_TOPUP_TIMEFRAMES``, which stays byte-identical: that constant feeds the
# coverage payload's shape AND ``desk_screen._bar_store_signature``'s hashed tuple set, both
# frozen — recording 1m/5m series is structurally invisible to the signature, so no recorded
# screen's pins move. (The desk era's own "no 5m/1m in the desk top-up" acceptance text scoped to
# the DAILY-CLOSE screen's needs; this union is the forward-era's additive decision, changing
# nothing about what the screen itself reads.)
DESK_TOPUP_FINE_TIMEFRAMES: tuple[str, ...] = ("1m", "5m")

# The walker's full iteration set — coarse (pinned) first, fine appended.
TOPUP_WALK_TIMEFRAMES: tuple[str, ...] = DESK_TOPUP_TIMEFRAMES + DESK_TOPUP_FINE_TIMEFRAMES

# Per-timeframe lookback floor for the REQUESTED window: fine timeframes ask only for what the
# vendor can actually serve (``yahoo.py``'s ``_INTERVAL_LIMITS``: 1m ≈ the last 30 days, 5m ≈ 60),
# so ``_pair_window``'s EXISTING tail logic engages the day after the first fine fetch — the
# frozen history already reaches a 30/60-day lookback start. Without this floor the full 730-day
# request start could never be reached by frozen fine history, every daily run would re-request
# (and re-record) the whole clamped span, and the append-only store would grow by ~1MB per symbol
# per timeframe per day for data the store already holds.
_TOPUP_FINE_LOOKBACK_DAYS: dict[str, int] = {"1m": 30, "5m": 60}


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _fetch_window_now(lookback_days: int = _TOPUP_LOOKBACK_DAYS) -> tuple[str, str]:
    """The ``[start, end]`` ISO window every top-up pair requests: ``end`` = today (UTC calendar
    date), ``start`` = ``lookback_days`` earlier (the shared ``_TOPUP_LOOKBACK_DAYS`` default for
    the coarse four; the fine timeframes pass their own retention floor — see
    ``_TOPUP_FINE_LOOKBACK_DAYS``). Deliberately wall-clock: an operator-run top-up asking "what
    bars exist as of today" is the SAME act as a manual ``POST /research/bars`` call with today's
    date — goal.md's T-6 no-wall-clock rule scopes to a SCREEN's ``as_of`` (J-03's determinism
    contract), never to a plain bar-fetch window (which the vendor adapter's own retention clamp
    already honestly bounds/notes)."""
    now = datetime.now(timezone.utc)
    end = now.date().isoformat() + "T00:00:00Z"
    start = (now - timedelta(days=lookback_days)).date().isoformat() + "T00:00:00Z"
    return start, end


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _iso_bar_epoch(epoch: float) -> str:
    """The SAME epoch -> ISO formatting ``bars.py``'s own ``_iso_utc``/``desk_screen.py``'s own
    ``_iso`` use — kept as a local copy (this project's per-module tiny-helper convention) so a
    pair's OWN frozen-bar timestamps are formatted identically wherever they are read."""
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _pair_window(bar_store: BarStore, symbol: str, timeframe: str) -> dict:
    """goal-desk-iter-26, J-17 — derive ONE pair's fetch window from that pair's OWN frozen
    content, read via the SAME canonical ``BarStore.merged_bars`` accessor (``bars.py:557``) —
    never ``bar_index``'s ``window_end_utc``. A single ascending ``merged_bars`` read decides one
    of three cases:

      * nothing frozen for this pair -> the byte-identical full ``_TOPUP_LOOKBACK_DAYS`` window
        ``_fetch_window_now()`` already asks for today (``window_basis: "full_lookback"``).
      * the pair's frozen history does NOT reach back to that lookback start -> the SAME full
        window (``"full_lookback"``) — short histories keep deepening exactly as they do today.
      * the pair's frozen history reaches the lookback start -> a tail window
        ``[that pair's own newest frozen bar's UTC date, today]`` (``"tail"``). The end bound stays
        ``_fetch_window_now()``'s wall-clock today either way.

    Returns ``{"requested_window": {"start", "end"}, "store_frozen_from", "store_frozen_through",
    "window_basis"}`` — ``store_frozen_from``/``store_frozen_through`` are that pair's own
    earliest/newest frozen bar (full ISO timestamp), both ``None`` together when nothing is
    frozen. A PURE read (zero vendor calls, zero writes) — safe to call more than once against the
    same pre-fetch store state (see the module docstring's J-17 section)."""
    # Forward-test era: a FINE timeframe's lookback start is its own vendor-retention floor
    # (``_TOPUP_FINE_LOOKBACK_DAYS``), not the shared 730 days — so after the first fine fetch the
    # frozen history already reaches the start and the tail branch below engages, exactly as it
    # always has for the coarse four.
    lookback_days = _TOPUP_FINE_LOOKBACK_DAYS.get(timeframe, _TOPUP_LOOKBACK_DAYS)
    lookback_start, today = _fetch_window_now(lookback_days)
    bars = bar_store.merged_bars(symbol, timeframe)
    if not bars:
        return {
            "requested_window": {"start": lookback_start, "end": today},
            "store_frozen_from": None,
            "store_frozen_through": None,
            "window_basis": "full_lookback",
        }
    frozen_from = _iso_bar_epoch(bars[0].epoch)
    frozen_through = _iso_bar_epoch(bars[-1].epoch)
    if frozen_from[:10] > lookback_start[:10]:
        # The pair's OWN earliest frozen bar is more recent than the lookback start -- its
        # history does not reach back that far yet. Keep asking for the same full window so a
        # short history keeps deepening exactly as it does today.
        return {
            "requested_window": {"start": lookback_start, "end": today},
            "store_frozen_from": frozen_from,
            "store_frozen_through": frozen_through,
            "window_basis": "full_lookback",
        }
    tail_start = frozen_through[:10] + "T00:00:00Z"
    return {
        "requested_window": {"start": tail_start, "end": today},
        "store_frozen_from": frozen_from,
        "store_frozen_through": frozen_through,
        "window_basis": "tail",
    }


def _copy_snapshot(snapshot: dict) -> dict:
    """A caller-safe copy (the ``progress.outcomes`` list is fresh too) so a reader mutating what
    ``snapshot()`` returns can never poison ``DeskTopupComputeManager``'s own internal state (the
    ``EdgeReportComputeManager._copy_snapshot`` precedent)."""
    progress = snapshot["progress"]
    return {
        **snapshot,
        "progress": {**progress, "outcomes": [dict(entry) for entry in progress["outcomes"]]},
    }


# --- the shared walker -- the SOLE computer of a top-up's outcomes; the manager and the CLI both
# call this and nothing else --------------------------------------------------------------------


def _run_one_pair(
    symbol: str,
    timeframe: str,
    bar_store: BarStore,
    bar_index: BarIndex,
    registry: ResearchRegistry,
) -> tuple[str, str | None]:
    """Fetch+record ONE ``(symbol, timeframe)`` pair through ``record_bar_series`` (in-process —
    never a second fetch-and-record implementation) and classify the honest outcome:

      * ``"reused"``    — ``record_bar_series`` answered store-first (its own ``bar_index``-backed
        coordinator), zero vendor calls.
      * ``"fetched"``   — a real vendor call ran and a BRAND NEW series was recorded.
      * ``"unchanged"`` — goal-desk-iter-26 (J-17): a real vendor call ran (this pair's derived
        window, see ``_pair_window``) and the vendor answered with content already registered —
        ``record_bar_series``'s own 409 (``BarSeriesAlreadyRegistered``). A genuine vendor call, so
        never conflated with ``"reused"``'s zero-vendor-calls meaning.
      * ``"failed"``    — ``record_bar_series`` raised any OTHER error (the existing
        ``NoDataForWindow``/``VendorTimeout``/``UnsupportedTimeframe`` taxonomy, all converted to
        ``HTTPException`` inside ``record_bar_series``, or any other unexpected error) — the detail
        is preserved verbatim, never swallowed, and the caller (``run_topup``) continues to the
        remaining pairs rather than aborting the whole job.

    The fetch window itself is this pair's OWN derived window (``_pair_window`` — goal-desk-iter-26,
    J-17), never the run-wide wall-clock window unconditionally."""
    window = _pair_window(bar_store, symbol, timeframe)
    start = window["requested_window"]["start"]
    end = window["requested_window"]["end"]
    body = BarRecordRequest(symbol=symbol, timeframe=timeframe, start=start, end=end)
    t_before = datetime.now(timezone.utc)
    try:
        result = record_bar_series(body=body, registry=registry, store=bar_store, index=bar_index)
    except HTTPException as exc:
        if exc.status_code == 409:
            return "unchanged", str(exc.detail)
        return "failed", str(exc.detail)
    except Exception as exc:  # noqa: BLE001 -- never swallowed, never aborts the whole run (TC-14)
        return "failed", str(exc)

    created_utc = result["bar_series"].get("created_utc")
    created = _parse_iso(created_utc) if created_utc else None
    if created is not None and created >= t_before:
        return "fetched", None
    return "reused", None


def run_topup(
    members: list[str],
    bar_store: BarStore,
    bar_index: BarIndex,
    registry: ResearchRegistry,
    *,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> list[dict]:
    """Walk ``members x DESK_TOPUP_TIMEFRAMES``, in order, calling ``_run_one_pair`` for each pair
    — the SOLE walker; ``DeskTopupComputeManager`` and the CLI warmer both call this and nothing
    else (the ``run_strategy_comparison_report`` precedent). Returns the list of per-pair outcome
    dicts, in iteration order: ``{"symbol", "timeframe", "outcome", "detail"}`` plus (goal-desk-
    iter-26, J-17) ``"requested_window"``, ``"store_frozen_from"``, ``"store_frozen_through"``,
    ``"window_basis"`` — that pair's own pre-fetch provenance, captured via ``_pair_window``
    IMMEDIATELY before ``_run_one_pair`` runs (so it reflects the store's content BEFORE this run's
    fetch, exactly as the Data Contract requires) and independent of whatever ``_run_one_pair``
    itself is (real or a test fake) — see the module docstring's J-17 section; plus (goal-desk-
    iter-32, J-19) ``"store_frozen_through_after"`` — that SAME pair's own newest frozen bar AFTER
    the attempt, read via a SECOND, independent ``_pair_window`` call immediately AFTER
    ``_run_one_pair`` returns, ``null`` only when the pair holds nothing at all — see the module
    docstring's J-19 section.

    ``progress``, if given, is called after EACH pair with the outcome dict just appended (so a
    caller can publish incremental state). ``should_abort``, if given and it returns ``True``
    BEFORE a pair starts, stops the walk early — the returned list is simply shorter than
    ``len(members) * len(TOPUP_WALK_TIMEFRAMES)``; a cooperative stop, never a raise (there is no
    cache-publish step here to protect, unlike ``run_strategy_comparison_report``'s
    ``EdgeReportComputeCancelled``)."""
    outcomes: list[dict] = []
    for symbol in members:
        for timeframe in TOPUP_WALK_TIMEFRAMES:
            if should_abort is not None and should_abort():
                return outcomes
            window = _pair_window(bar_store, symbol, timeframe)
            outcome, detail = _run_one_pair(symbol, timeframe, bar_store, bar_index, registry)
            # goal-desk-iter-32 (J-19): a SECOND, independent call to the SAME pure accessor,
            # immediately after the attempt, captures what this pair's frozen history actually
            # reaches AFTER the walk -- never bar_index's window_end_utc (what the run ASKED for),
            # never a new accessor, never arithmetic over bars. For "reused"/"unchanged"/"failed"
            # pairs nothing was written between the two calls, so the two reads always agree; for
            # a "fetched" pair the store gained a new series, so this second read genuinely
            # reflects it. `null` only when the pair holds nothing at all (see the module
            # docstring's J-19 section).
            window_after = _pair_window(bar_store, symbol, timeframe)
            entry = {
                "symbol": symbol,
                "timeframe": timeframe,
                "outcome": outcome,
                "detail": detail,
                "requested_window": window["requested_window"],
                "store_frozen_from": window["store_frozen_from"],
                "store_frozen_through": window["store_frozen_through"],
                "window_basis": window["window_basis"],
                "store_frozen_through_after": window_after["store_frozen_through"],
            }
            outcomes.append(entry)
            if progress is not None:
                progress(entry)
    return outcomes


class DeskTopupComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) desk top-up job. Construct with no arguments —
    every ``trigger()`` call takes its stores/registry explicitly (the ``EdgeReportComputeManager``
    per-call-injection precedent), so a test (or a future second registry) points this at any
    hermetic store set with zero constructor plumbing."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict | None = None
        self._cancel_event: threading.Event | None = None
        self._thread: threading.Thread | None = None

    def snapshot(self) -> dict | None:
        """The current/last job's snapshot, or ``None`` if none has ever run — a caller-safe copy,
        never a shared mutable reference."""
        current = self._snapshot  # read-local-reference-before-inspect
        if current is None:
            return None
        return _copy_snapshot(current)

    def trigger(
        self,
        universe_store: UniverseStore,
        bar_store: BarStore,
        bar_index: BarIndex,
        registry: ResearchRegistry,
        topup_run_store: TopupRunStore,
    ) -> dict:
        """Start a NEW top-up job over the LATEST universe snapshot's members, or — if one is
        already ``state == "running"`` — return it UNCHANGED (``started: False``, single-flight).
        Once the current job is terminal (done/cancelled/failed, or none has ever run), the NEXT
        call always starts a genuinely new job (a fresh id), discarding the prior snapshot. Never
        blocks — the walk runs on a dedicated worker thread, off the caller's thread, so an HTTP
        route calling this returns immediately. No universe snapshot registered yet -> an honest
        zero-pair job (``pairs_total: 0``) that resolves ``"done"`` immediately, never an error.

        J-09: ``topup_run_store`` is where this job's terminal outcome is durably recorded (once,
        via ``desk_topup_log.record_topup_run`` — see the module docstring's J-09 section) — a
        required per-call dependency (the ``bar_store``/``bar_index``/``registry`` precedent), never
        a constructor-owned default, so a test points it at any hermetic store with zero plumbing."""
        with self._lock:
            current = self._snapshot
            if current is not None and current["state"] == "running":
                return {"started": False, "compute": _copy_snapshot(current)}

            records, _errors = universe_store.list()
            universe_snapshot_id = records[-1]["id"] if records else None
            members: list[str] = list(records[-1]["members"]) if records else []
            pairs_total = len(members) * len(TOPUP_WALK_TIMEFRAMES)

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
                "progress": {"pairs_total": pairs_total, "pairs_done": 0, "outcomes": []},
            }
            self._snapshot = snapshot

        # J-09: the requested fetch window is captured ONCE here, before the walk starts -- never
        # re-derived inside the writer or per-pair (`_run_one_pair` still calls its own
        # `_fetch_window_now()`, unchanged, once per pair, for that pair's OWN fetch; this is a
        # separate, record-keeping-only read of the same deterministic-per-UTC-day helper --
        # goal-desk-iter-11 NOTES / assumptions.md iter-11 entry). `collected` is this job's own
        # append-only mirror of every outcome `_publish` has seen so far, independent of
        # `self._snapshot` -- so the crash-fallback write below (a whole-job failure) never risks
        # reading a snapshot a NEWER job has already superseded.
        _window_start, _window_end = _fetch_window_now()
        requested_window = {"start": _window_start, "end": _window_end}
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
                        "pairs_done": progress["pairs_done"] + 1,
                        "outcomes": [*progress["outcomes"], entry],
                    },
                }

        def _record_run(*, state: str, outcomes: list[dict]) -> None:
            record_topup_run(
                topup_run_store,
                universe_snapshot_id=universe_snapshot_id,
                requested_window=requested_window,
                config_fingerprint=CONFIG.config_fingerprint(),
                started_utc=started_utc,
                finished_utc=_iso_utc_now(),
                state=state,
                pairs_total=pairs_total,
                outcomes=outcomes,
            )

        def _work() -> None:
            try:
                outcomes = run_topup(
                    members, bar_store, bar_index, registry,
                    progress=_publish, should_abort=cancel_event.is_set,
                )
            except Exception as exc:  # noqa: BLE001 -- a catastrophic, unexpected failure OUTSIDE
                # any single pair (per-pair failures are already caught inside run_topup and
                # recorded as "failed" outcomes -- this only fires for something run_topup itself
                # cannot recover from) -- surfaced verbatim, never swallowed.
                self._resolve(job_id, "failed", error=str(exc))
                _record_run(state="failed", outcomes=collected)
                return
            state = "cancelled" if cancel_event.is_set() else "done"
            self._resolve(job_id, state, error=None)
            _record_run(state=state, outcomes=outcomes)

        thread = threading.Thread(target=_work, name=f"desk-topup-compute:{job_id}", daemon=True)
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
        ROUTE is the one that rejects an idle cancel with a 409 — see ``desk_routes.py``)."""
        with self._lock:
            cancel_event = self._cancel_event
        if cancel_event is not None:
            cancel_event.set()

    def join_all(self, timeout: float = 30.0) -> None:
        """Wait for the in-flight job thread, if any (test/shutdown hygiene — the
        ``EdgeReportComputeManager.join_all`` precedent)."""
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)


# --- The CLI warmer ------------------------------------------------------------------------------
# Mirrors ``edge_report_compute.py``'s own CLI precedent: resolves the SAME env/config seams the
# backend reads, runs ``run_topup`` to completion SYNCHRONOUSLY in-process (no manager, no
# background thread — a CLI invocation IS the one caller; there is nothing else to serialize
# against), and exits 0 (or 1 on any failed pair) with a summary. Deliberately does NOT go through
# ``DeskTopupComputeManager`` (single-flight/cancel/progress-polling exist to serve CONCURRENT HTTP
# callers; a one-shot CLI process has none) — it calls ``run_topup`` directly, exactly like
# ``edge_report_compute.main()`` calls ``run_strategy_comparison_report`` directly.


def _cli_progress_printer() -> Callable[[dict], None]:
    def _printer(entry: dict) -> None:
        suffix = f" -- {entry['detail']}" if entry.get("detail") else ""
        print(f"[{entry['symbol']} {entry['timeframe']}] {entry['outcome']}{suffix}", flush=True)

    return _printer


def main() -> int:
    """The CLI entry: ``python -m app.research.desk_topup_compute``. Runs the top-up to completion
    against the operator's real universe/bar dirs, for the operator's real ~100-symbol run. Prints
    one progress line per completed pair; exits 1 (nothing recorded is lost either way — every
    successful pair up to a failure stays recorded) if any pair's outcome is ``"failed"``, else 0."""
    parser = argparse.ArgumentParser(
        description="Era B \"The Desk\" J-02 CLI warmer -- top up bars for every member of the "
        "latest registered universe snapshot across the pinned DESK_TOPUP_TIMEFRAMES set "
        "(1h/4h/1d/1w), store-first, through the SAME POST /research/bars fetch-and-record logic "
        "the route uses."
    )
    parser.parse_args()

    config = CONFIG
    store = JournalStore(config.journal_db_path_resolved(), config)
    try:
        registry = ResearchRegistry(store, config)
        bar_store = get_bar_store()
        bar_index = get_bar_index()
        universe_store = UniverseStore(config.desk_universe_dir_resolved())
        topup_run_store = TopupRunStore(
            resolve_desk_topup_log_dir(config.desk_universe_dir_resolved())
        )

        records, _errors = universe_store.list()
        if not records:
            print(
                "no universe snapshot is registered -- nothing to top up (run "
                "POST /research/desk/universe/fetch first)",
                file=sys.stderr,
            )
            return 1
        universe_snapshot_id = records[-1]["id"]
        members = list(records[-1]["members"])
        pairs_total = len(members) * len(TOPUP_WALK_TIMEFRAMES)
        print(
            f"desk top-up: {len(members)} member(s) x {len(TOPUP_WALK_TIMEFRAMES)} "
            f"timeframe(s) = {pairs_total} pair(s)",
            flush=True,
        )
        # J-09: the requested fetch window is captured ONCE, before the walk starts -- the SAME
        # record-keeping-only read `DeskTopupComputeManager.trigger` uses (see that method's own
        # comment); `run_topup`/`_run_one_pair` still call `_fetch_window_now()` themselves,
        # unchanged, once per pair, for that pair's OWN fetch.
        window_start, window_end = _fetch_window_now()
        started_utc = _iso_utc_now()
        outcomes = run_topup(members, bar_store, bar_index, registry, progress=_cli_progress_printer())
        # The CLI has no cancel signal -- a run that reaches this line always terminates "done"
        # (the module docstring's J-09 section). An uncaught crash ABOVE this line (inside
        # `run_topup` itself, escaping its own per-pair try/except) is the correct interrupted-run
        # case: the process exits without ever calling the writer below, so the ledger stays
        # honestly empty for this attempt -- never guarded against here.
        record_topup_run(
            topup_run_store,
            universe_snapshot_id=universe_snapshot_id,
            requested_window={"start": window_start, "end": window_end},
            config_fingerprint=config.config_fingerprint(),
            started_utc=started_utc,
            finished_utc=_iso_utc_now(),
            state="done",
            pairs_total=pairs_total,
            outcomes=outcomes,
        )
    finally:
        store.close()

    n_fetched = sum(1 for o in outcomes if o["outcome"] == "fetched")
    n_reused = sum(1 for o in outcomes if o["outcome"] == "reused")
    n_unchanged = sum(1 for o in outcomes if o["outcome"] == "unchanged")
    n_failed = sum(1 for o in outcomes if o["outcome"] == "failed")
    print(
        f"desk top-up complete: {n_fetched} fetched, {n_reused} reused, {n_unchanged} unchanged, "
        f"{n_failed} failed."
    )
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
