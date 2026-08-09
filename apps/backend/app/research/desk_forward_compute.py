"""Desk forward-returns compute (forward-test era) -- the single-flight, cancellable,
progress-reporting background job around ``desk_forward.compute_forward`` (the SOLE row walker;
this module computes nothing about forward moves itself), plus a CLI warmer that drives the SAME
run-and-record function synchronously, in-process, for a REQUIRED ``--screen-id``.

Mirrors ``desk_screen_compute.DeskScreenComputeManager`` verbatim in shape: one in-flight job slot
(``self._snapshot``), an in-memory process-scoped progress snapshot, cooperative cancel, an atomic
snapshot publish under a lock (a fresh dict rebound in ONE assignment, never mutated in place).
Job state is process-scoped bookkeeping -- honestly lost on restart, never a research value.

**Reuse, not a recompute.** ``run_forward_and_record`` resolves the run's 2-pin key BEFORE any
walk, using only metadata reads (``compute_forward_input_signature`` is
``list(include_bars=False)``-only -- the J-18 cheap-pre-check discipline): a
``ForwardStore.find_by_key`` hit short-circuits immediately with ``reused=True`` and ZERO
``merged_bars`` reads. A miss runs the full walk; a cancelled (partial) walk is NEVER recorded.

**Store-only.** The compute reads the frozen ``BarStore`` exactly as it stands -- it never issues
a vendor fetch (fine 1m/5m bars arrive via the desk top-up's own walk). The CLI below resolves
the real store singletons via ``routes.py``'s accessors -- the SAME legal one-way edge
(research module -> ``routes.py``) ``desk_screen_compute``'s own CLI already uses -- which is
also why the manager lives as a module-level singleton in ``desk_routes.py``, never on
``ResearchRegistry`` (the ``desk_topup_compute`` circular-import doctrine).

**The durable run log.** ``ForwardStore`` records only SUCCESSFUL measurements, so on its own it
cannot distinguish a snapshot whose measurement never ran from one that ran and found nothing --
the exact ambiguity a 51-day refresh chain hit on 2026-08-06, when every screen was recorded and
no forward record was. ``desk_forward_log.ForwardRunStore`` is the durable counterpart (the J-18
``desk_screen_log`` discipline verbatim): one record per terminal run, written once from inside
``run_forward_and_record`` below, carrying ``rows_absent_no_fine_bars`` -- the count that says a
measurement really did happen and really did find nothing to measure. It is OPTIONAL at every call
site (``forward_run_store=None`` skips it), so the compute path is unchanged for callers that do
not pass one."""

from __future__ import annotations

import argparse
import sys
import threading
import uuid
from datetime import datetime, timezone
from typing import Callable

from ..config import CONFIG, Config
from .bars import BarStore
from .desk_forward import (
    ForwardAlreadyRecorded,
    ForwardScreenNotFound,
    ForwardStore,
    compute_forward,
    compute_forward_input_signature,
    forward_row_counts,
    resolve_desk_forward_dir,
)
from .desk_forward_log import (
    ForwardRunStore,
    record_forward_run,
    resolve_desk_forward_log_dir,
)
from .desk_screen import ScreenStore, resolve_desk_screen_dir
from .routes import get_bar_store

__all__ = ["DeskForwardComputeManager", "run_forward_and_record"]


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _copy_snapshot(snapshot: dict) -> dict:
    """A caller-safe copy so a reader mutating what ``snapshot()`` returns can never poison the
    manager's own internal state (the ``DeskScreenComputeManager._copy_snapshot`` precedent)."""
    progress = snapshot["progress"]
    return {**snapshot, "progress": dict(progress)}


def run_forward_and_record(
    screen_store: ScreenStore,
    bar_store: BarStore,
    config: Config,
    forward_store: ForwardStore,
    screen_id: str,
    *,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
    forward_run_store: ForwardRunStore | None = None,
) -> tuple[dict | None, bool]:
    """Compute ONE forward record (``compute_forward`` -- the sole walker) and persist it,
    append-only. Returns ``(record, reused)``:

      * an unknown ``screen_id`` raises ``ForwardScreenNotFound`` (the route pre-checks and 422s
        before ever reaching here -- this is the belt-and-braces rail for the race);
      * an identical 2-pin key already recorded returns the EXISTING record with
        ``(record, True)`` -- resolved BEFORE the walk, zero bar reads;
      * a cancelled (partial) walk is NEVER recorded -- returns ``(None, False)``;
      * a freshly persisted record returns ``(record, False)``; the record-time
        ``ForwardAlreadyRecorded`` race resolves to the existing record with ``(record, True)``.

    If ``forward_run_store`` is given, this function ALSO persists exactly one durable run record
    (``desk_forward_log.record_forward_run``) at its own terminal outcome --
    ``forward_run_store=None`` (the default) skips this entirely, so every existing caller and test
    keeps working unmodified."""
    started_utc = _iso_utc_now()
    config_fingerprint = config.config_fingerprint()

    # The run log is written EXACTLY ONCE per run -- structurally, not by convention (the
    # ``run_screen_and_record`` B1 latch verbatim). Without it, a terminal write that itself RAISES
    # (a full disk, a read-only log dir) would be caught by the outer ``except`` below and
    # re-entered as a SECOND, "failed" record for the same run -- a fabricated terminal state (the
    # forward record really was persisted) carrying the LEDGER's own I/O error as if it were a
    # measurement failure. With it, a failed terminal write leaves NO record at all (the log
    # module's own documented interrupted-run honesty) and the I/O error still propagates verbatim.
    logged = False

    def _log(
        *,
        state: str,
        reused: bool,
        rows: list[dict],
        rows_total: int,
        rows_with_touches: int,
        total_touches: int,
        screen_date: str | None,
        forward_input_signature: str | None,
        forward_id: str | None,
        error: str | None,
    ) -> None:
        nonlocal logged
        if forward_run_store is None or logged:
            return
        logged = True
        counts = forward_row_counts(rows)
        record_forward_run(
            forward_run_store,
            screen_id=screen_id,
            screen_date=screen_date,
            config_fingerprint=config_fingerprint,
            forward_input_signature=forward_input_signature,
            started_utc=started_utc,
            finished_utc=_iso_utc_now(),
            state=state,
            reused=reused,
            # The run's SCOPE, not the walk's progress: a cancelled run reports how many rows it was
            # measuring, and the two count fields below report how far it actually got.
            rows_total=rows_total,
            rows_measured=counts["rows_measured"],
            rows_absent_no_fine_bars=counts["rows_absent_no_fine_bars"],
            rows_with_touches=rows_with_touches,
            total_touches=total_touches,
            forward_id=forward_id,
            error=error,
        )

    screen_records, _screen_errors = screen_store.list()
    screen = next((record for record in screen_records if record["id"] == screen_id), None)
    if screen is None:
        message = (
            f"no recorded screen snapshot has id '{screen_id}' -- nothing to measure forward from"
        )
        # A real trigger against an id nothing resolves is a real terminal outcome, so it leaves a
        # real row -- with the honest `screen_date: None` of a date that was never resolvable.
        _log(
            state="failed", reused=False, rows=[], rows_total=0, rows_with_touches=0,
            total_touches=0, screen_date=None, forward_input_signature=None, forward_id=None,
            error=message,
        )
        raise ForwardScreenNotFound(message)

    screen_date = screen["screen_date"]
    rows_total = len(screen["rows"])

    try:
        symbols = [row["symbol"] for row in screen["rows"]]
        signature = compute_forward_input_signature(bar_store, symbols, config_fingerprint)
        existing = forward_store.find_by_key(screen_id, signature)
        if existing is not None:
            # A reuse is a real attempt with its own timestamps, and its counts are the ones the
            # walk it short-circuited produced -- never zeroes, which would read as an empty result.
            _log(
                state="done", reused=True, rows=existing["rows"], rows_total=rows_total,
                rows_with_touches=existing["rows_with_touches"],
                total_touches=existing["total_touches"], screen_date=screen_date,
                forward_input_signature=signature, forward_id=existing["id"], error=None,
            )
            return existing, True

        result = compute_forward(
            screen, bar_store, config_fingerprint,
            progress=progress, should_abort=should_abort,
        )
        if should_abort is not None and should_abort():
            # Nothing is persisted, but the cancel WAS observed by the walk -- so unlike a crash
            # this leaves a row, naming how far the partial walk got before it stopped.
            _log(
                state="cancelled", reused=False, rows=result["rows"], rows_total=rows_total,
                rows_with_touches=result["rows_with_touches"],
                total_touches=result["total_touches"], screen_date=screen_date,
                forward_input_signature=result["forward_input_signature"], forward_id=None,
                error=None,
            )
            return None, False

        try:
            recorded = forward_store.record(
                screen_id=result["screen_id"],
                screen_date=result["screen_date"],
                as_of=result["as_of"],
                config_fingerprint=result["config_fingerprint"],
                forward_input_signature=result["forward_input_signature"],
                payload_version=result["payload_version"],
                parameters=result["parameters"],
                register=result["register"],
                rows=result["rows"],
                summary=result["summary"],
                rows_with_touches=result["rows_with_touches"],
                total_touches=result["total_touches"],
            )
        except ForwardAlreadyRecorded as exc:
            raced = forward_store.find_by_key(screen_id, result["forward_input_signature"])
            assert raced is not None and raced["id"] == exc.existing_id
            _log(
                state="done", reused=True, rows=raced["rows"], rows_total=rows_total,
                rows_with_touches=raced["rows_with_touches"],
                total_touches=raced["total_touches"], screen_date=screen_date,
                forward_input_signature=result["forward_input_signature"],
                forward_id=raced["id"], error=None,
            )
            return raced, True
    except Exception as exc:  # noqa: BLE001 -- logged, then re-raised VERBATIM, never swallowed
        _log(
            state="failed", reused=False, rows=[], rows_total=rows_total, rows_with_touches=0,
            total_touches=0, screen_date=screen_date, forward_input_signature=None,
            forward_id=None, error=str(exc),
        )
        raise

    _log(
        state="done", reused=False, rows=recorded["rows"], rows_total=rows_total,
        rows_with_touches=recorded["rows_with_touches"],
        total_touches=recorded["total_touches"], screen_date=screen_date,
        forward_input_signature=recorded["forward_input_signature"], forward_id=recorded["id"],
        error=None,
    )
    return recorded, False


class DeskForwardComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) desk forward compute job. Construct with no
    arguments -- every ``trigger()`` call takes its stores/config explicitly (the
    ``DeskScreenComputeManager`` per-call-injection precedent)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict | None = None
        self._cancel_event: threading.Event | None = None
        self._thread: threading.Thread | None = None

    def snapshot(self) -> dict | None:
        """The current/last job's snapshot, or ``None`` if none has ever run -- a caller-safe
        copy, never a shared mutable reference."""
        current = self._snapshot  # read-local-reference-before-inspect
        if current is None:
            return None
        return _copy_snapshot(current)

    def trigger(
        self,
        screen_id: str,
        screen_store: ScreenStore,
        bar_store: BarStore,
        config: Config,
        forward_store: ForwardStore,
        forward_run_store: ForwardRunStore | None = None,
    ) -> dict:
        """Start a NEW forward compute job for ``screen_id``, or -- if one is already
        ``state == "running"`` -- return it UNCHANGED (``started: False``, single-flight). Once
        the current job is terminal, the NEXT call always starts a genuinely new job. Never
        blocks -- the walk runs on a dedicated worker thread."""
        with self._lock:
            current = self._snapshot
            if current is not None and current["state"] == "running":
                return {"started": False, "compute": _copy_snapshot(current)}

            # rows_total resolved synchronously, before any background work starts (the
            # members_total/pairs_total precedent). An unknown id here yields 0 -- the worker's
            # own ForwardScreenNotFound resolves the job "failed" with the naming error.
            screen_records, _errors = screen_store.list()
            screen = next(
                (record for record in screen_records if record["id"] == screen_id), None
            )
            rows_total = len(screen["rows"]) if screen is not None else 0

            job_id = uuid.uuid4().hex
            cancel_event = threading.Event()
            self._cancel_event = cancel_event
            snapshot = {
                "id": job_id,
                "state": "running",
                "screen_id": screen_id,
                "started_utc": _iso_utc_now(),
                "finished_utc": None,
                "error": None,
                # Honest until a terminal state resolves: nothing recorded yet.
                "reused": False,
                "forward_id": None,
                "progress": {"rows_total": rows_total, "rows_done": 0, "current": None},
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
                        "rows_done": progress["rows_done"] + 1,
                        "current": entry["symbol"],
                    },
                }

        def _work() -> None:
            try:
                record, reused = run_forward_and_record(
                    screen_store, bar_store, config, forward_store, screen_id,
                    progress=_publish, should_abort=cancel_event.is_set,
                    forward_run_store=forward_run_store,
                )
            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                self._resolve(job_id, "failed", error=str(exc))
                return
            # ``record is None`` -> the walk observed the cancel before persisting anything. The
            # converse race (cancel landing after the record) honestly reports the recorded id --
            # the DeskScreenComputeManager B3 precedent verbatim.
            self._resolve(
                job_id, "cancelled" if cancel_event.is_set() else "done", error=None,
                reused=reused, forward_id=record["id"] if record is not None else None,
            )

        thread = threading.Thread(target=_work, name=f"desk-forward-compute:{job_id}", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return {"started": True, "compute": _copy_snapshot(snapshot)}

    def _resolve(
        self, job_id: str, state: str, *, error: str | None,
        reused: bool = False, forward_id: str | None = None,
    ) -> None:
        with self._lock:
            current = self._snapshot
            if current is None or current["id"] != job_id:
                return  # superseded -- never resolve a job that is no longer the current one
            self._snapshot = {
                **current, "state": state, "finished_utc": _iso_utc_now(), "error": error,
                "reused": reused, "forward_id": forward_id,
            }

    def cancel(self) -> None:
        """Signal cooperative cancellation for the in-flight job -- a harmless no-op if idle (the
        ROUTE is the one that rejects an idle cancel with a 409)."""
        with self._lock:
            cancel_event = self._cancel_event
        if cancel_event is not None:
            cancel_event.set()

    def join_all(self, timeout: float = 30.0) -> None:
        """Wait for the in-flight job thread, if any (test/shutdown hygiene)."""
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)


# --- The CLI warmer --------------------------------------------------------------------------------


def _cli_progress_printer() -> Callable[[dict], None]:
    def _print(entry: dict) -> None:
        print(f"  measured {entry['symbol']}", flush=True)

    return _print


def main() -> int:
    """The CLI entry: ``python -m app.research.desk_forward_compute --screen-id <id>``. Runs the
    forward measurement to completion against the operator's real screen/bar/forward dirs,
    publishing to the SAME durable forward store ``GET /research/desk/forward`` serves."""
    parser = argparse.ArgumentParser(
        description="Desk forward-returns CLI warmer -- measure ONE recorded screen snapshot's "
        "ranked rows at their walls (touch-anchored per-horizon returns in percent + per-touch "
        "long/short max drawdown, with the seeded random-minute baseline) and "
        "persist the result append-only to the SAME durable forward store "
        "GET /research/desk/forward serves."
    )
    parser.add_argument(
        "--screen-id", required=True,
        help="the recorded screen snapshot id (e.g. screen-2026-08-03-48b5b0c5e94c) to measure "
        "forward -- REQUIRED; never defaults to the latest screen.",
    )
    args = parser.parse_args()

    config = CONFIG
    screen_store = ScreenStore(resolve_desk_screen_dir(config.desk_universe_dir_resolved()))
    bar_store = get_bar_store()
    forward_store = ForwardStore(resolve_desk_forward_dir(config.desk_universe_dir_resolved()))
    forward_run_store = ForwardRunStore(
        resolve_desk_forward_log_dir(config.desk_universe_dir_resolved())
    )

    try:
        recorded, reused = run_forward_and_record(
            screen_store, bar_store, config, forward_store, args.screen_id,
            progress=_cli_progress_printer(), forward_run_store=forward_run_store,
        )
    except ForwardScreenNotFound as exc:
        print(str(exc), file=sys.stderr)
        return 1

    assert recorded is not None  # no cancel path exists in the CLI
    print(
        f"forward measurement complete for {args.screen_id}: {len(recorded['rows'])} rows, "
        f"{recorded['total_touches']} touch(es) -- "
        f"record {recorded['id']} ({'reused existing' if reused else 'newly recorded'})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
