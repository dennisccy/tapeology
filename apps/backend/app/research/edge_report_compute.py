"""era-fast_wall J-04 — the operator-run compute: a single-flight, cancellable, progress-reporting
background job around ``edge_report.run_strategy_comparison_report``'s five additive keyword-only
hooks (``force``/``progress``/``should_abort``/``sub_cache``/``workers`` — see that function's own
docstring), plus a CLI warmer that drives the SAME hooks synchronously, in-process.

THIS MODULE computes NOTHING itself — ``run_strategy_comparison_report`` (and, through it,
``EdgeReportCache.get_or_compute``/``compute_and_publish``, both already shipped at J-01) stay the
SOLE computer and the SOLE cache writer. ``EdgeReportComputeManager`` is pure job bookkeeping: it
decides WHEN to call that one function (single-flight — never a second concurrent call), tracks
WHETHER it is running/done/cancelled/failed, and republishes an atomic progress snapshot as the
call's own ``progress``/``should_abort`` hooks fire. Process-scoped, in-memory-only state — a
backend restart honestly loses it (the SAME "in-flight jobs lost on restart" contract
``StudyJobManager``/``BacktestJobManager`` already carry); it is never a research value (goal.md's
own Data Contract: "Job state is process-scoped bookkeeping... never a research value").

**Single-flight, deliberately simpler than ``StudyJobManager``/``BacktestJobManager``'s per-id
dict.** There is only ever ONE "the edge report compute" — one job slot (``self._snapshot``), not a
dict keyed by id. A ``trigger()`` while the current job's ``state == "running"`` returns that SAME
job unchanged (``started: False``); once terminal, the NEXT ``trigger()`` starts a genuinely NEW job
(a fresh id), discarding the old snapshot.

**Publish only after the compute function returns normally — true BY CONSTRUCTION, not by a special
case here.** ``EdgeReportCache.get_or_compute``/``compute_and_publish`` (both UNTOUCHED, J-01) only
ever call ``self._insert``/rebind ``self._hot`` AFTER their ``compute_fn`` argument returns — a
``compute_fn`` that raises (whether ``edge_report.EdgeReportComputeCancelled`` from a fired
``should_abort``, or any genuine failure) leaves BOTH cache layers exactly as they were. This
module's worker thread simply distinguishes the TWO exception shapes at its own outer boundary:
``EdgeReportComputeCancelled`` resolves ``state: "cancelled"``; anything else resolves
``state: "failed"`` with the exception's message surfaced verbatim (never swallowed, never generic).

**Atomic snapshot publish — the ``EdgeReportCache._hot`` / ``setups.py`` ``_SCAN_CACHE``
discipline, applied to job bookkeeping instead of a computed result.** Every snapshot mutation
(progress patch, terminal resolution) builds a FRESH dict and rebinds ``self._snapshot`` in ONE
assignment under ``self._lock`` — a concurrent reader (``snapshot()``) takes ONE local reference
before inspecting it and is handed its OWN shallow copy (so a caller mutating what it read can never
poison the manager's own state — the ``BarStore.get``/``list`` "served rows are copies" precedent).
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..config import CONFIG, Config
from .bars import BarStore
from .datasets import DatasetStore
from .edge_report import EdgeReportComputeCancelled, EdgeReportError, run_strategy_comparison_report
from .edge_report_cache import EdgeReportCache, resolve_cache_db_path
from .store import JournalStore

__all__ = ["EdgeReportComputeManager"]

# Mirrors goal.md's own CLI usage string (``--workers N``, default 4) — accepted this iteration,
# currently INERT (see ``run_strategy_comparison_report``'s own docstring; J-05 gives it effect).
_DEFAULT_WORKERS = 4


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _idle_progress() -> dict:
    """The progress sub-dict a freshly-triggered job starts with, before ``_compute_strategy_
    comparison_report`` has even resolved ``events`` (and therefore has no ``backtests_total`` to
    report yet) — an honest ``0``, never a fabricated estimate."""
    return {
        "phase": "starting", "backtests_total": 0, "backtests_done": 0,
        "backtests_from_cache": 0, "current": None,
    }


def _copy_snapshot(snapshot: dict) -> dict:
    """A caller-safe copy (two levels deep — the ``progress`` sub-dict and its own ``current``
    sub-dict, the full nesting this shape ever carries) so a reader mutating what ``snapshot()``
    returns can never poison ``EdgeReportComputeManager``'s own internal state."""
    progress = snapshot["progress"]
    current = progress.get("current")
    return {
        **snapshot,
        "progress": {**progress, "current": dict(current) if current is not None else None},
    }


class EdgeReportComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) edge-report compute job. Construct with no
    arguments — unlike ``BacktestJobManager``/``StudyJobManager`` (which bind one ``store``/
    ``config`` for their whole lifetime), every ``trigger()`` call takes its store/dataset_store/
    bar_store/config/cache explicitly, the SAME per-call injection ``BacktestJobManager.start``
    already uses for ``dataset_store``/``bar_store`` — so a test (or a future second registry)
    points this at any hermetic store pair with zero constructor plumbing."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict | None = None
        self._cancel_event: threading.Event | None = None
        self._thread: threading.Thread | None = None

    def snapshot(self) -> dict | None:
        """The current/last job's snapshot, or ``None`` if none has ever run — a caller-safe copy
        (see ``_copy_snapshot``), never a shared mutable reference."""
        current = self._snapshot  # read-local-reference-before-inspect
        if current is None:
            return None
        return _copy_snapshot(current)

    def trigger(
        self,
        store: JournalStore,
        dataset_store: DatasetStore,
        bar_store: BarStore,
        config: Config,
        cache: EdgeReportCache,
        *,
        force: bool = False,
    ) -> dict:
        """Start a NEW compute job, or — if one is already ``state == "running"`` — return it
        UNCHANGED (``started: False``, the SAME job's own ``force``, never the just-requested one).
        Once the current job is terminal (done/cancelled/failed, or none has ever run), the NEXT
        call always starts a genuinely new job (a fresh id), discarding the prior snapshot. Never
        blocks on the compute itself — the actual sweep runs on a dedicated worker thread, OFF the
        caller's thread (the ``BacktestJobManager.start`` precedent), so an HTTP route calling this
        returns immediately."""
        with self._lock:
            current = self._snapshot
            if current is not None and current["state"] == "running":
                return {"started": False, "compute": _copy_snapshot(current)}

            job_id = uuid.uuid4().hex
            cancel_event = threading.Event()
            self._cancel_event = cancel_event
            snapshot = {
                "id": job_id,
                "state": "running",
                "force": force,
                "started_utc": _iso_utc_now(),
                "finished_utc": None,
                "error": None,
                "progress": _idle_progress(),
            }
            self._snapshot = snapshot

        def _publish_progress(patch: dict) -> None:
            fields = {k: v for k, v in patch.items() if k != "event"}
            with self._lock:
                current = self._snapshot
                if current is None or current["id"] != job_id:
                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
                self._snapshot = {
                    **current,
                    "progress": {**current["progress"], **fields},
                }

        def _work() -> None:
            try:
                run_strategy_comparison_report(
                    store, dataset_store, bar_store, config,
                    cache=cache, force=force, progress=_publish_progress,
                    should_abort=cancel_event.is_set,
                )
            except EdgeReportComputeCancelled:
                self._resolve(job_id, "cancelled", error=None)
            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                self._resolve(job_id, "failed", error=str(exc))
            else:
                self._resolve(job_id, "done", error=None)

        thread = threading.Thread(target=_work, name=f"edge-report-compute:{job_id}", daemon=True)
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
        ROUTE is the one that rejects an idle cancel with a 409, mirroring ``cancel_backtest``'s
        own check-then-call split; see ``routes.py``)."""
        with self._lock:
            cancel_event = self._cancel_event
        if cancel_event is not None:
            cancel_event.set()

    def join_all(self, timeout: float = 30.0) -> None:
        """Wait for the in-flight job thread, if any (test/shutdown hygiene — the
        ``BacktestJobManager.join_all`` precedent, applied to this manager's single thread)."""
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)


# --- The CLI warmer ---------------------------------------------------------------------------------
# Mirrors ``edge_report.py``'s own ``main()`` CLI precedent: resolves the SAME env/config seams the
# backend reads (journal, dataset dir, bar dir, the edge-report cache DB), runs to completion
# SYNCHRONOUSLY in-process (no manager, no background thread — a CLI invocation IS the one caller;
# there is nothing else to serialize against), and exits 0 with a summary. Deliberately does NOT go
# through ``EdgeReportComputeManager`` (single-flight/cancel/progress-polling exist to serve
# CONCURRENT HTTP callers; a one-shot CLI process has none) -- it calls the SAME ``run_strategy_
# comparison_report`` hooks directly, exactly like the era-3 J-09 CLI calls ``run_edge_report``
# directly. The existing era-3 J-09 ``edge_report.main()`` CLI stays byte-untouched.


def _cli_progress_printer() -> Callable[[dict], None]:
    """One progress LINE per completed backtest (TC-11), plus one summary line announcing the
    total up front — a pure formatting closure over the SAME ``_ProgressReporter``-shaped patches
    the compute manager consumes (the ``"event"`` key disambiguates a start-of-run announcement
    from a per-pair update; see ``edge_report._ProgressReporter``)."""
    state = {"total": 0}

    def _printer(patch: dict) -> None:
        event = patch.get("event")
        if event == "total":
            state["total"] = patch["backtests_total"]
            print(f"edge-report compute: {state['total']} backtest(s) to run", flush=True)
        elif event == "pair_done":
            current = patch.get("current")  # already cleared back to None by _ProgressReporter
            done = patch["backtests_done"]
            print(f"[{done}/{state['total']}] backtest complete{'' if current is None else f' ({current})'}", flush=True)

    return _printer


def main() -> int:
    """The CLI entry: ``python -m app.research.edge_report_compute --workers N [--force]
    [--out report.json]``. Runs the 3-way strategy-comparison sweep to completion against the
    operator's journal/dataset/bar dirs, publishing to the SAME durable edge-report cache
    ``GET /research/edge-report`` serves (``resolve_cache_db_path`` — the identical resolver the
    route's own dependency uses). An ``EdgeReportError`` (a corrupt dataset) prints an explicit
    message to stderr and exits 1 with nothing published — the existing ``get_or_compute``/
    ``compute_and_publish`` discipline (nothing is ever cached on an exception)."""
    parser = argparse.ArgumentParser(
        description="era-fast_wall J-04 CLI warmer -- run the 3-way v1/structure_tape/"
        "structure_tape_map edge-report sweep to completion, publishing to the SAME durable "
        "cache GET /research/edge-report serves."
    )
    parser.add_argument(
        "--workers", type=int, default=_DEFAULT_WORKERS,
        help="accepted for the future parallel sweep (J-05); INERT this iteration -- every "
        "compute runs strictly sequentially regardless of this value.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="recompute even over an already-warm cache key and republish.",
    )
    parser.add_argument("--out", default=None, help="optional path to also write the report JSON")
    args = parser.parse_args()

    config = CONFIG
    store = JournalStore(config.journal_db_path_resolved(), config)
    try:
        dataset_store = DatasetStore(config.dataset_dir_resolved())
        bar_store = BarStore(config.bar_dir_resolved())
        cache = EdgeReportCache(resolve_cache_db_path(config.dataset_dir_resolved()))

        try:
            report = run_strategy_comparison_report(
                store, dataset_store, bar_store, config,
                cache=cache, force=args.force, progress=_cli_progress_printer(),
                workers=args.workers,
            )
        except EdgeReportError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    finally:
        store.close()

    n_train = len(report["train"]["cells"])
    n_holdout = len(report["holdout"]["cells"])
    print(
        f"edge report compute complete: {n_train} train cell(s), {n_holdout} hold-out cell(s) "
        f"published to the durable cache."
    )
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"report written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
