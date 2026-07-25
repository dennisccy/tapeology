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
sync with that logic."""

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
from .desk_universe import UniverseStore
from .routes import (
    BarRecordRequest,
    ResearchRegistry,
    get_bar_index,
    get_bar_store,
    record_bar_series,
)
from .store import JournalStore

__all__ = ["DeskTopupComputeManager", "run_topup"]

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


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _fetch_window_now() -> tuple[str, str]:
    """The ``[start, end]`` ISO window every top-up pair requests: ``end`` = today (UTC calendar
    date), ``start`` = ``_TOPUP_LOOKBACK_DAYS`` earlier. Deliberately wall-clock: an operator-run
    top-up asking "what bars exist as of today" is the SAME act as a manual ``POST /research/bars``
    call with today's date — goal.md's T-6 no-wall-clock rule scopes to a SCREEN's ``as_of``
    (J-03's determinism contract), never to a plain bar-fetch window (which the vendor adapter's
    own retention clamp already honestly bounds/notes)."""
    now = datetime.now(timezone.utc)
    end = now.date().isoformat() + "T00:00:00Z"
    start = (now - timedelta(days=_TOPUP_LOOKBACK_DAYS)).date().isoformat() + "T00:00:00Z"
    return start, end


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


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

      * ``"reused"``  — ``record_bar_series`` answered store-first (its own ``bar_index``-backed
        coordinator), zero vendor calls.
      * ``"fetched"`` — a real vendor call ran and a BRAND NEW series was recorded.
      * ``"failed"``  — ``record_bar_series`` raised (the existing ``NoDataForWindow``/
        ``VendorTimeout``/``UnsupportedTimeframe`` taxonomy, all converted to ``HTTPException``
        inside ``record_bar_series``, or any other unexpected error) — the detail is preserved
        verbatim, never swallowed, and the caller (``run_topup``) continues to the remaining pairs
        rather than aborting the whole job."""
    start, end = _fetch_window_now()
    body = BarRecordRequest(symbol=symbol, timeframe=timeframe, start=start, end=end)
    t_before = datetime.now(timezone.utc)
    try:
        result = record_bar_series(body=body, registry=registry, store=bar_store, index=bar_index)
    except HTTPException as exc:
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
    dicts (``{"symbol", "timeframe", "outcome", "detail"}``), in iteration order.

    ``progress``, if given, is called after EACH pair with the outcome dict just appended (so a
    caller can publish incremental state). ``should_abort``, if given and it returns ``True``
    BEFORE a pair starts, stops the walk early — the returned list is simply shorter than
    ``len(members) * len(DESK_TOPUP_TIMEFRAMES)``; a cooperative stop, never a raise (there is no
    cache-publish step here to protect, unlike ``run_strategy_comparison_report``'s
    ``EdgeReportComputeCancelled``)."""
    outcomes: list[dict] = []
    for symbol in members:
        for timeframe in DESK_TOPUP_TIMEFRAMES:
            if should_abort is not None and should_abort():
                return outcomes
            outcome, detail = _run_one_pair(symbol, timeframe, bar_store, bar_index, registry)
            entry = {"symbol": symbol, "timeframe": timeframe, "outcome": outcome, "detail": detail}
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
    ) -> dict:
        """Start a NEW top-up job over the LATEST universe snapshot's members, or — if one is
        already ``state == "running"`` — return it UNCHANGED (``started: False``, single-flight).
        Once the current job is terminal (done/cancelled/failed, or none has ever run), the NEXT
        call always starts a genuinely new job (a fresh id), discarding the prior snapshot. Never
        blocks — the walk runs on a dedicated worker thread, off the caller's thread, so an HTTP
        route calling this returns immediately. No universe snapshot registered yet -> an honest
        zero-pair job (``pairs_total: 0``) that resolves ``"done"`` immediately, never an error."""
        with self._lock:
            current = self._snapshot
            if current is not None and current["state"] == "running":
                return {"started": False, "compute": _copy_snapshot(current)}

            records, _errors = universe_store.list()
            members: list[str] = list(records[-1]["members"]) if records else []
            pairs_total = len(members) * len(DESK_TOPUP_TIMEFRAMES)

            job_id = uuid.uuid4().hex
            cancel_event = threading.Event()
            self._cancel_event = cancel_event
            snapshot = {
                "id": job_id,
                "state": "running",
                "started_utc": _iso_utc_now(),
                "finished_utc": None,
                "error": None,
                "progress": {"pairs_total": pairs_total, "pairs_done": 0, "outcomes": []},
            }
            self._snapshot = snapshot

        def _publish(entry: dict) -> None:
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

        def _work() -> None:
            try:
                run_topup(
                    members, bar_store, bar_index, registry,
                    progress=_publish, should_abort=cancel_event.is_set,
                )
            except Exception as exc:  # noqa: BLE001 -- a catastrophic, unexpected failure OUTSIDE
                # any single pair (per-pair failures are already caught inside run_topup and
                # recorded as "failed" outcomes -- this only fires for something run_topup itself
                # cannot recover from) -- surfaced verbatim, never swallowed.
                self._resolve(job_id, "failed", error=str(exc))
                return
            self._resolve(job_id, "cancelled" if cancel_event.is_set() else "done", error=None)

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

        records, _errors = universe_store.list()
        if not records:
            print(
                "no universe snapshot is registered -- nothing to top up (run "
                "POST /research/desk/universe/fetch first)",
                file=sys.stderr,
            )
            return 1
        members = list(records[-1]["members"])
        print(
            f"desk top-up: {len(members)} member(s) x {len(DESK_TOPUP_TIMEFRAMES)} "
            f"timeframe(s) = {len(members) * len(DESK_TOPUP_TIMEFRAMES)} pair(s)",
            flush=True,
        )
        outcomes = run_topup(members, bar_store, bar_index, registry, progress=_cli_progress_printer())
    finally:
        store.close()

    n_fetched = sum(1 for o in outcomes if o["outcome"] == "fetched")
    n_reused = sum(1 for o in outcomes if o["outcome"] == "reused")
    n_failed = sum(1 for o in outcomes if o["outcome"] == "failed")
    print(f"desk top-up complete: {n_fetched} fetched, {n_reused} reused, {n_failed} failed.")
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
