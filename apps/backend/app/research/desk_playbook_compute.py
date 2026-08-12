"""Desk playbook compute (Era B2, J-02) -- the single-flight, cancellable, progress-reporting
background job around ``desk_playbook.compute_playbook`` (the SOLE detect+measure walker; this
module computes nothing about signals or measurements itself), plus a CLI warmer that drives the
SAME run-and-record function synchronously, in-process, for a REQUIRED ``--session-date``.

Mirrors ``desk_forward_compute.DeskForwardComputeManager``/``run_forward_and_record`` verbatim in
shape: one in-flight job slot (``self._snapshot``), an in-memory process-scoped progress snapshot,
cooperative cancel, an atomic snapshot publish under a lock (a fresh dict rebound in ONE assignment,
never mutated in place). Job state is process-scoped bookkeeping -- honestly lost on restart, never
a research value.

**Reuse, not a recompute.** ``run_playbook_and_record`` resolves the run's 2-pin key BEFORE any
walk, using only metadata reads (``compute_playbook_input_signature`` is
``list(include_bars=False)``-only, the same cheap-pre-check discipline ``compute_forward_input_
signature`` follows): a ``PlaybookStore.find_by_key`` hit short-circuits immediately with
``reused=True`` and ZERO ``merged_bars`` reads. A miss runs the full detect+measure walk; a
cancelled (partial) walk is NEVER recorded.

**Session honesty, twice, on purpose.** The HTTP route (``desk_routes.trigger_desk_playbook_
compute``) pre-checks ``desk_sessions.refuse_if_not_a_session`` BEFORE ever calling
``DeskPlaybookComputeManager.trigger`` -- a bad ``session_date`` never creates a job or a ledger row
by that path (the ``trigger_desk_screen_compute`` precedent). ``run_playbook_and_record`` ALSO
checks it directly (not merely relying on ``compute_playbook``'s own internal check), for the CLI
path -- which carries no separate pre-check layer -- and for the rare race between the route's
check and the walk's start; this second check DOES log an honest ``"refused_non_session"`` ledger
row, since the CLI has no earlier gate to make that outcome invisible.

**Cancellation leaves no trace, deliberately -- both here AND in the ledger.** Unlike
``desk_forward_compute``'s manager (whose snapshot settles on a distinct ``"cancelled"`` state),
this manager's ``status`` enum (``idle``/``running``/``cancelling``/``done``/``error``) has no
sixth value for a completed cancel: once the walk observes the cancel and stops, the snapshot
reverts to the SAME idle shape it started from, and ``desk_playbook_log.py``'s writer is never
called for it either (see that module's docstring). A cancelled playbook run is treated as though
it never happened, everywhere it is visible -- not merely absent from the durable store (true of
every compute path in this codebase) but absent from the ephemeral progress view too. The ONE
exception, added 2026-08-12 for the refresh chain's sixth step: the reverted snapshot keeps the
cancelled job's own ``id``, so a waiter can tell a completed cancel apart from a backend restart
(``_resolve_cancelled`` states the full reasoning). Every value describing the RUN still reverts.

**Store-only.** The compute reads the frozen ``BarStore``/``UniverseStore`` exactly as they stand
-- it never issues a vendor fetch, never triggers a universe refresh. The CLI below resolves the
real store singletons via ``routes.py``'s accessors (the same legal one-way edge
``desk_forward_compute``'s own CLI already uses), which is also why the manager lives as a
module-level singleton in ``desk_routes.py``, never on ``ResearchRegistry``.

**The durable run log.** ``PlaybookStore`` records only SUCCESSFUL measurements, so on its own it
cannot distinguish a session whose playbook never ran from one that ran and found nothing to
record. ``desk_playbook_log.PlaybookRunStore`` is the durable counterpart (the
``desk_forward_log``/``desk_topup_log`` discipline), written once from inside
``run_playbook_and_record`` below for every TERMINAL outcome except a cancel. It is OPTIONAL at
every call site (``playbook_run_store=None`` skips it), so the compute path is unchanged for
callers that do not pass one."""

from __future__ import annotations

import argparse
import sys
import threading
import uuid
from datetime import datetime, timezone
from typing import Callable

from ..config import CONFIG, Config
from .bars import BarStore
from .desk_playbook import (
    PlaybookAlreadyRecorded,
    PlaybookSessionRefused,
    PlaybookStore,
    compute_playbook,
    compute_playbook_input_signature,
    resolve_desk_playbook_dir,
)
from .desk_playbook_log import (
    PlaybookRunStore,
    record_playbook_run,
    resolve_desk_playbook_log_dir,
)
from .desk_sessions import refuse_if_not_a_session
from .desk_universe import UniverseStore
from .routes import get_bar_store

__all__ = ["DeskPlaybookComputeManager", "run_playbook_and_record"]

_IDLE_SNAPSHOT: dict = {
    "id": None, "status": "idle", "session_date": None,
    "signals_done": 0, "signals_total": 0, "error": None,
}


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def run_playbook_and_record(
    universe_store: UniverseStore,
    bar_store: BarStore,
    config: Config,
    playbook_store: PlaybookStore,
    session_date: str,
    *,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
    playbook_run_store: PlaybookRunStore | None = None,
) -> tuple[dict | None, bool]:
    """Detect+measure ONE session (``compute_playbook`` -- the sole walker) and persist it,
    append-only. Returns ``(record, reused)``:

      * a provably non-session ``session_date`` raises ``PlaybookSessionRefused`` (belt-and-braces
        -- the route pre-checks and 422s before ever reaching here for the HTTP path; this is the
        rail for the CLI path and for the race);
      * an identical 2-pin key already recorded returns the EXISTING record with
        ``(record, True)`` -- resolved BEFORE the walk, zero bar reads;
      * a cancelled (partial) walk is NEVER recorded -- returns ``(None, False)``;
      * a freshly persisted record returns ``(record, False)``; the record-time
        ``PlaybookAlreadyRecorded`` race resolves to the existing record with ``(record, True)``.

    If ``playbook_run_store`` is given, this function ALSO persists exactly one durable run record
    (``desk_playbook_log.record_playbook_run``) at its own terminal outcome -- EXCEPT for a cancel,
    which is never logged at all (module docstring). ``playbook_run_store=None`` (the default)
    skips logging entirely, so every existing caller/test keeps working unmodified."""
    started_at = _iso_utc_now()
    config_fingerprint = config.config_fingerprint()

    # Written EXACTLY ONCE per run -- structurally, not by convention (the `run_forward_and_record`
    # B1 latch verbatim): without this, a terminal write that itself raises would be caught by the
    # outer `except` below and re-entered as a SECOND, fabricated "failed" record.
    logged = False

    def _log(
        *, outcome: str, signals_recorded: int, playbook_input_signature: str | None,
        playbook_id: str | None, error: str | None,
    ) -> None:
        nonlocal logged
        if playbook_run_store is None or logged:
            return
        logged = True
        record_playbook_run(
            playbook_run_store,
            session_date=session_date,
            config_fingerprint=config_fingerprint,
            playbook_input_signature=playbook_input_signature,
            started_at=started_at,
            finished_at=_iso_utc_now(),
            outcome=outcome,
            signals_recorded=signals_recorded,
            playbook_id=playbook_id,
            error=error,
        )

    universe_records, _errors = universe_store.list()
    members = list(universe_records[-1]["members"]) if universe_records else []

    refusal = refuse_if_not_a_session(session_date, bar_store, members)
    if refusal is not None:
        _log(
            outcome="refused_non_session", signals_recorded=0, playbook_input_signature=None,
            playbook_id=None, error=refusal,
        )
        raise PlaybookSessionRefused(refusal)

    try:
        signature = compute_playbook_input_signature(bar_store, members, config_fingerprint)
        existing = playbook_store.find_by_key(session_date, signature)
        if existing is not None:
            # A reuse is a real attempt with its own timestamps, and its counts are the ones the
            # walk it short-circuited produced -- never zeroes, which would read as an empty result.
            _log(
                outcome="reused", signals_recorded=len(existing["signals"]),
                playbook_input_signature=signature, playbook_id=existing["id"], error=None,
            )
            return existing, True

        result = compute_playbook(
            universe_store, bar_store, config_fingerprint, session_date,
            progress=progress, should_abort=should_abort,
        )
        if should_abort is not None and should_abort():
            # Nothing is persisted AND nothing is logged -- a cancelled playbook run leaves no
            # trace anywhere (module docstring), unlike the forward-returns ledger's "cancelled"
            # row.
            return None, False

        try:
            recorded = playbook_store.record(**result)
        except PlaybookAlreadyRecorded as exc:
            raced = playbook_store.find_by_key(session_date, result["playbook_input_signature"])
            assert raced is not None and raced["id"] == exc.existing_id
            _log(
                outcome="reused", signals_recorded=len(raced["signals"]),
                playbook_input_signature=result["playbook_input_signature"],
                playbook_id=raced["id"], error=None,
            )
            return raced, True
    except PlaybookSessionRefused as exc:
        # The rare race: bars/universe changed between the up-front check above and the walk's own
        # internal one inside `compute_playbook`.
        _log(
            outcome="refused_non_session", signals_recorded=0, playbook_input_signature=None,
            playbook_id=None, error=str(exc),
        )
        raise
    except Exception as exc:  # noqa: BLE001 -- logged, then re-raised VERBATIM, never swallowed
        _log(
            outcome="failed", signals_recorded=0, playbook_input_signature=None,
            playbook_id=None, error=str(exc),
        )
        raise

    _log(
        outcome="recorded", signals_recorded=len(recorded["signals"]),
        playbook_input_signature=recorded["playbook_input_signature"],
        playbook_id=recorded["id"], error=None,
    )
    return recorded, False


class DeskPlaybookComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) desk playbook compute job. Construct with no
    arguments -- every ``trigger()`` call takes its stores/config explicitly (the
    ``DeskForwardComputeManager`` per-call-injection precedent)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict | None = None
        self._job_id: str | None = None
        self._cancel_event: threading.Event | None = None
        self._thread: threading.Thread | None = None

    def snapshot(self) -> dict:
        """The current/last job's snapshot -- ``{"id", "status", "session_date", "signals_done",
        "signals_total", "error"}``, ALWAYS a real dict (never ``None``): before any job has ever
        run this process, ``status == "idle"`` and ``id is None``. A caller-safe copy, never a
        shared mutable reference."""
        current = self._snapshot
        return dict(current) if current is not None else dict(_IDLE_SNAPSHOT)

    def trigger(
        self,
        session_date: str,
        universe_store: UniverseStore,
        bar_store: BarStore,
        config: Config,
        playbook_store: PlaybookStore,
        playbook_run_store: PlaybookRunStore | None = None,
    ) -> dict:
        """Start a NEW playbook compute job for ``session_date``, or -- if one is already
        ``status`` in (``"running"``, ``"cancelling"``) -- return it UNCHANGED (``started: False``,
        single-flight, process-wide -- never per-``session_date``). Once the current job is
        terminal, the NEXT call always starts a genuinely new job. Never blocks -- the walk runs on
        a dedicated worker thread. Callers are expected to have ALREADY refused a non-session date
        (the route's own pre-check) -- this method does not repeat that check itself; a bad date
        still resolves honestly (``status: "error"``) via ``run_playbook_and_record``'s own guard."""
        with self._lock:
            current = self._snapshot
            if current is not None and current["status"] in ("running", "cancelling"):
                return {"started": False, "compute": dict(current)}

            # signals_total resolved synchronously, before any background work starts (the
            # rows_total/members_total precedent) -- the universe's own member count, the upper
            # bound on how many symbols this walk will visit.
            universe_records, _errors = universe_store.list()
            signals_total = len(universe_records[-1]["members"]) if universe_records else 0

            job_id = uuid.uuid4().hex
            self._job_id = job_id
            cancel_event = threading.Event()
            self._cancel_event = cancel_event
            snapshot = {
                "id": job_id, "status": "running", "session_date": session_date,
                "signals_done": 0, "signals_total": signals_total, "error": None,
            }
            self._snapshot = snapshot

        def _publish(_entry: dict) -> None:
            with self._lock:
                if self._job_id != job_id:
                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
                current = self._snapshot
                if current is None:
                    return
                self._snapshot = {**current, "signals_done": current["signals_done"] + 1}

        def _work() -> None:
            try:
                run_playbook_and_record(
                    universe_store, bar_store, config, playbook_store, session_date,
                    progress=_publish, should_abort=cancel_event.is_set,
                    playbook_run_store=playbook_run_store,
                )
            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                self._resolve_error(job_id, str(exc))
                return
            if cancel_event.is_set():
                self._resolve_cancelled(job_id)
            else:
                self._resolve_done(job_id)

        thread = threading.Thread(target=_work, name=f"desk-playbook-compute:{job_id}", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return {"started": True, "compute": dict(snapshot)}

    def _resolve_done(self, job_id: str) -> None:
        with self._lock:
            current = self._snapshot
            if current is None or self._job_id != job_id:
                return  # superseded -- never resolve a job that is no longer the current one
            self._snapshot = {**current, "status": "done", "error": None}

    def _resolve_error(self, job_id: str, error: str) -> None:
        with self._lock:
            current = self._snapshot
            if current is None or self._job_id != job_id:
                return
            self._snapshot = {**current, "status": "error", "error": error}

    def _resolve_cancelled(self, job_id: str) -> None:
        """A completed cancel leaves NO trace (module docstring): the snapshot reverts to the same
        idle shape it started from, rather than a distinct terminal state nothing was recorded
        under.

        2026-08-12 (refresh-chain steps 6-7, operator decision): the reverted snapshot KEEPS the
        cancelled job's own ``id``. Everything the walk produced is still erased -- the status, the
        session date and both counters revert, and the ledger writer is still never called -- so
        "leaves no trace" holds for every value that describes the RUN. The id is not one of those:
        it is ephemeral, process-scoped bookkeeping that names WHICH job the revert belongs to, and
        an external waiter needs exactly that to tell "the cancel I asked for completed" (idle, my
        id) from "the backend restarted under me" (idle, ``id is None``). Without it the refresh
        chain's id-keyed waiter cannot distinguish the two and reports a cancel as a lost job."""
        with self._lock:
            if self._job_id != job_id:
                return
            self._snapshot = {**_IDLE_SNAPSHOT, "id": job_id}

    def cancel(self) -> None:
        """Signal cooperative cancellation for the in-flight job -- flips the visible ``status`` to
        ``"cancelling"`` immediately (distinct from a walk still unaware of the request), a
        harmless no-op if idle (the ROUTE is the one that rejects an idle cancel with a 409)."""
        with self._lock:
            cancel_event = self._cancel_event
            current = self._snapshot
            if current is not None and current["status"] == "running":
                self._snapshot = {**current, "status": "cancelling"}
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
        print(f"  walked {entry['symbol']}", flush=True)

    return _print


def main() -> int:
    """The CLI entry: ``python -m app.research.desk_playbook_compute --session-date <yyyy-MM-dd>``.
    Runs the playbook detect+measure walk to completion against the operator's real universe/bar/
    playbook dirs, publishing to the SAME durable playbook store ``GET /research/desk/playbook``
    serves. ``--session-date`` is REQUIRED and never defaults to the current wall-clock date (T-6)."""
    parser = argparse.ArgumentParser(
        description="Desk playbook CLI warmer -- detect the opening-range-break family and measure "
        "every signal with the desk forward rail's own conventions (horizons, dual max drawdown, "
        "truncation honesty, the seeded random-anchor baseline) for ONE recorded session, and "
        "persist the result append-only to the SAME durable playbook store "
        "GET /research/desk/playbook serves."
    )
    parser.add_argument(
        "--session-date", required=True,
        help="the recorded trading session date (yyyy-MM-dd) to detect and measure -- REQUIRED; "
        "never defaults to the current date.",
    )
    args = parser.parse_args()

    config = CONFIG
    universe_store = UniverseStore(config.desk_universe_dir_resolved())
    bar_store = get_bar_store()
    playbook_store = PlaybookStore(resolve_desk_playbook_dir(config.desk_universe_dir_resolved()))
    playbook_run_store = PlaybookRunStore(
        resolve_desk_playbook_log_dir(config.desk_universe_dir_resolved())
    )

    try:
        recorded, reused = run_playbook_and_record(
            universe_store, bar_store, config, playbook_store, args.session_date,
            progress=_cli_progress_printer(), playbook_run_store=playbook_run_store,
        )
    except PlaybookSessionRefused as exc:
        print(str(exc), file=sys.stderr)
        return 1

    assert recorded is not None  # no cancel path exists in the CLI
    print(
        f"playbook compute complete for {args.session_date}: {len(recorded['signals'])} signal(s), "
        f"{len(recorded['absences'])} absence(s) -- record {recorded['id']} "
        f"({'reused existing' if reused else 'newly recorded'})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
