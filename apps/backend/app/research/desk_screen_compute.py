"""Era B "The Desk" (J-03) -- the desk screen compute manager: a single-flight, cancellable,
progress-reporting background job around ``desk_screen.compute_screen`` (the SOLE row-computation
walker; this module computes nothing about tradable structure itself), plus a CLI warmer that
drives the SAME function synchronously, in-process, for a REQUIRED ``--date``.

Mirrors ``desk_topup_compute.DeskTopupComputeManager``/``edge_report_compute.EdgeReportComputeManager``
verbatim in shape: one in-flight job slot (``self._snapshot``), an in-memory, process-scoped
progress snapshot (``id``/``state``/``screen_date``/``started_utc``/``finished_utc``/``error``/
``progress``), cooperative cancel, an atomic snapshot publish under a lock (a fresh dict rebound in
ONE assignment, never mutated in place). Job state is process-scoped bookkeeping -- honestly lost
on restart, never a research value.

**Unlike ``DeskTopupComputeManager``, this manager needs nothing from ``routes.py``** --
``desk_screen.compute_screen`` reuses only ``tradability.py``/``desk_coverage.py``/``datasets.py``,
none of which live in ``routes.py``. So there is no circular-import constraint forcing this off
``ResearchRegistry`` -- it is STILL a module-level singleton behind a FastAPI dependency in
``desk_routes.py`` (the ``get_desk_topup_manager`` pattern, for placement consistency with its
sibling and full test-to-test isolation via ``app.dependency_overrides``), simply because there is
no functional reason to prefer the registry either.

**Append-only reuse, not a pre-compute skip.** ``trigger`` ALWAYS runs the full member walk (via
``compute_screen``) rather than pre-checking the store before paying for it. ``compute_screen``
calls ``compute_tradability`` DIRECTLY (never through the durable ``TradabilityCache``
``GET /research/tradability`` uses -- this module has no reason to import from ``routes.py``, the
module that owns that cache), so an identical-pin retrigger genuinely repeats the CPU work, not a
cheap cache hit -- live-verified (see the dev handoff's "Known Issues"): a real ~100-member walk's
first symbol can take several seconds, cold. This is a DELIBERATE, logged trade-off (not an
oversight): the row content is a pure, deterministic function of the five pins (TC-10), so
repeating the computation changes nothing observable, and the APPEND-ONLY guarantee (never a
second file, never a rewrite) is enforced STRUCTURALLY by ``ScreenStore.record`` itself
(``ScreenAlreadyRecorded``) regardless of whether the walk was "worth" repeating. No TC requires a
hard "zero recompute calls on retrigger" proof (unlike TC-15's explicit ``BarStore``-call-counting
for ``bar_store_signature``); a future iteration can add a cheap pre-check (the five pins resolve
synchronously before the walk, the SAME way ``members_total`` already does) if a real retrigger's
latency is ever measured to matter -- the same "measure first, optimize later" discipline
``bars.py``/``datasets.py``'s own stat-keyed caches followed.

**goal-desk-iter-29 (J-18) -- that future iteration, arrived.** ``run_screen_and_record`` now
resolves the run's five pins BEFORE calling ``compute_screen`` at all, using ONLY existing
accessors (``screen_as_of``, ``UniverseStore.list``, ``Config.config_fingerprint``,
``desk_screen.compute_bar_store_signature`` over ``desk_coverage`` -- zero new derivation, zero new
``BarStore`` read beyond the index-only coverage read that accessor itself makes). A
``ScreenStore.find_by_key`` hit on those five pins short-circuits IMMEDIATELY: the existing
snapshot is returned with ``reused=True``, ``compute_tradability`` is called ZERO times, and
``compute_screen`` itself is never invoked. A miss runs the full walk exactly as it always has (zero
behavior change to ``compute_screen``) -- the "structural backstop" ``ScreenStore.record``'s own
``ScreenAlreadyRecorded`` refusal provides for the rare race where the store changes UNDER a running
walk is untouched and still fires in that case.

Independently, this function now also persists ONE durable, checksummed, append-only RUN record
(``desk_screen_log.py``, mirrors the J-09/J-10 run-log discipline verbatim) at its own terminal
outcome (done/cancelled/failed) via the single shared writer ``record_screen_run`` -- called from
inside THIS function (the ONE shared entry point both ``DeskScreenComputeManager``'s resolve path
and the CLI's ``main()`` already call), optional via the ``screen_run_store`` parameter (default
``None`` -- a caller that does not supply one gets no durable record, so every EXISTING caller of
this function keeps working unmodified; the real HTTP route and the CLI always supply a real
store). This changes NOTHING about ``compute_screen``'s own walk semantics or ``ScreenStore``'s own
recorded snapshot/row/skip shapes -- it only makes the RUN's own outcome legible, the same way
``desk_topup_log.py``/``desk_index_reconcile.py`` already do for their own compute managers."""

from __future__ import annotations

import argparse
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Callable

from ..config import CONFIG, Config
from .bar_index import BarIndex
from .bars import BarStore
from .datasets import DatasetStore
from .desk_forward import ForwardStore, resolve_desk_forward_dir
from .desk_screen import (
    ScreenAlreadyRecorded,
    ScreenStore,
    _screen_workers,
    compute_screen,
    resolve_desk_screen_dir,
    resolve_screen_pins,
    screen_as_of,
)
from .desk_screen_decision import resolve_screen_decision
from .desk_screen_log import ScreenRunStore, record_screen_run, resolve_desk_screen_log_dir
from .desk_sessions import refuse_if_not_a_session
from .desk_universe import UniverseStore
from .routes import get_bar_index, get_bar_store, get_dataset_store

__all__ = ["DeskScreenComputeManager", "run_screen_and_record"]

# The two skip reasons ``compute_screen`` ever records (``desk_screen.py``'s own module docstring:
# "Skip reasons -- exactly two, never conflated") -- the honest zero-tally a run log entry starts
# from before counting a walk's (partial or full) own skipped rows.
_EMPTY_SKIPPED_BY_REASON = {"no_bars": 0, "no_basis": 0}


def _tally_skipped_by_reason(skipped: list[dict]) -> dict:
    """A plain per-reason count of ``compute_screen``'s own ``skipped`` list -- goal-desk-iter-29
    (J-18), the ``desk_screen._bands_by_class``-style "plain dict tally" construction, applied to
    the two reasons ``desk_screen.py`` itself ever produces. Never a third bucket, never a
    recomputation of WHY a member was skipped -- each entry's own ``reason`` is read verbatim."""
    tally = dict(_EMPTY_SKIPPED_BY_REASON)
    for entry in skipped:
        tally[entry["reason"]] = tally.get(entry["reason"], 0) + 1
    return tally


def _iso_utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _copy_snapshot(snapshot: dict) -> dict:
    """A caller-safe copy so a reader mutating what ``snapshot()`` returns can never poison
    ``DeskScreenComputeManager``'s own internal state (the ``EdgeReportComputeManager._copy_snapshot``
    precedent)."""
    progress = snapshot["progress"]
    return {**snapshot, "progress": dict(progress)}


def run_screen_and_record(
    universe_store: UniverseStore,
    bar_store: BarStore,
    bar_index: BarIndex,
    dataset_store: DatasetStore,
    config: Config,
    screen_store: ScreenStore,
    screen_date: str,
    *,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
    screen_run_store: ScreenRunStore | None = None,
    forward_store: ForwardStore | None = None,
) -> tuple[dict | None, bool]:
    """Compute ONE screen (``compute_screen`` -- the sole walker) and persist it. Returns
    ``(record, reused)``:

      * a cancelled (partial) walk is NEVER recorded -- returns ``(None, False)`` (the caller
        distinguishes "cancelled, nothing recorded" from "recorded/reused" by the ``None`` check);
      * a freshly-persisted snapshot returns ``(record, False)``;
      * a date already holding that date's full data returns the EXISTING snapshot's meta with
        ``(record, True)`` (never a second file, never a rewrite) -- ``ScreenAlreadyRecorded`` is
        caught here, not propagated, since reusing an already-recorded snapshot is a normal,
        expected outcome, not a failure (era-desk-iter-4 J-04, audit B2: this ``reused`` flag is
        what lets a caller distinguish "this job's walk is what created the snapshot" from "this
        job's walk found an already-recorded one and changed nothing").

    goal-desk-iter-29 (J-18): the pins are resolved BEFORE any walk, using ONLY existing accessors
    -- a reuse short-circuits immediately (``reused=True``, ``members_attempted=0``, ZERO
    ``compute_screen``/``compute_tradability`` calls); anything else runs ``compute_screen`` exactly
    as before.

    **One snapshot per date.** The reuse question is now asked by ``resolve_screen_decision`` (its
    module docstring owns the rule) against ``ScreenStore.find_by_date`` rather than by an exact
    5-pin ``find_by_key`` match, because that match read a top-up of LATER days' bars -- which
    cannot change one row of an earlier date -- as a brand-new key and wrote a second file for that
    date. Whenever this function settles a date it prunes that date's other copies: after a fresh
    record (the replacement is on disk FIRST, so an interrupted supersede leaves two copies and
    never zero) and equally after a reuse (a date reached by a re-trigger converges even when no
    walk was needed). Superseding a snapshot also drops the forward records measured against it --
    they key on ``screen_id`` and would otherwise point at an id nothing can resolve -- which is
    what ``forward_store`` is for; omitting it (the default) leaves them in place, so every EXISTING
    caller keeps working unmodified.

    If ``screen_run_store`` is given, this function ALSO persists exactly one durable run record
    (``desk_screen_log.record_screen_run``) at its own terminal outcome -- ``screen_run_store=None``
    (the default) skips this entirely."""
    started_utc = _iso_utc_now()

    as_of = screen_as_of(screen_date)
    universe_records, _universe_errors = universe_store.list()
    universe_snapshot_id = universe_records[-1]["id"] if universe_records else None
    members = list(universe_records[-1]["members"]) if universe_records else []
    members_total = len(members)
    config_fingerprint = config.config_fingerprint()
    pins = resolve_screen_pins(universe_store, bar_index, as_of)
    bar_store_signature = pins["bar_store_signature"]

    # goal-desk-iter-29 audit (B1): the run log is written EXACTLY ONCE per run -- structurally, not
    # by convention. Without this latch, a terminal write that itself RAISES (a full disk, a
    # read-only log dir) would be caught by the outer `except Exception` below and re-entered as a
    # SECOND, "failed" record for the same run -- a fabricated terminal state (the snapshot really
    # was recorded) carrying the LEDGER's own I/O error as if it were a screen failure. With it, a
    # failed terminal write leaves NO record at all (the module's own documented interrupted-run
    # honesty) and the I/O error still propagates verbatim -- never silently swallowed.
    logged = False

    def _log(
        *,
        state: str,
        reused: bool,
        members_attempted: int,
        ranked_count: int,
        skipped_by_reason: dict,
        screen_id: str | None,
        error: str | None,
        failed_member: str | None,
        superseded_screen_ids: list[str] | None = None,
    ) -> None:
        nonlocal logged
        if screen_run_store is None or logged:
            return
        logged = True
        record_screen_run(
            screen_run_store,
            screen_date=screen_date,
            universe_snapshot_id=universe_snapshot_id,
            config_fingerprint=config_fingerprint,
            bar_store_signature=bar_store_signature,
            started_utc=started_utc,
            finished_utc=_iso_utc_now(),
            state=state,
            reused=reused,
            members_total=members_total,
            members_attempted=members_attempted,
            ranked_count=ranked_count,
            skipped_by_reason=skipped_by_reason,
            screen_id=screen_id,
            error=error,
            failed_member=failed_member,
            superseded_screen_ids=superseded_screen_ids,
        )

    def _settle_date(keep_id: str) -> list[str]:
        """Collapse ``screen_date`` down to the ONE snapshot ``keep_id``, dropping the forward
        records measured against every copy removed. Returns the removed screen ids."""
        superseded = screen_store.prune_superseded(screen_date, keep_id)
        if forward_store is not None:
            for superseded_id in superseded:
                forward_store.prune_for_screen(superseded_id)
        return superseded

    # goal-desk-iter-29 (J-18) step 2: a date that already holds its own full data is answered
    # WITHOUT paying for the walk -- zero `compute_screen`/`compute_tradability` calls, no
    # `BarStore` read beyond the index-only coverage read `resolve_screen_pins` already made above.
    existing = screen_store.find_by_date(screen_date)
    decision = resolve_screen_decision(
        existing, pins, screen_date=screen_date,
        universe_snapshot_id=universe_snapshot_id, config_fingerprint=config_fingerprint,
    )
    if decision["action"] == "reuse":
        assert existing is not None  # `reuse` is only ever returned for a snapshot that exists
        # A reuse settles the date too: a re-trigger over a date still carrying pre-cleanup copies
        # converges on one file even though nothing needed re-walking.
        superseded = _settle_date(existing["id"])
        _log(
            state="done", reused=True, members_attempted=0, ranked_count=0,
            skipped_by_reason=dict(_EMPTY_SKIPPED_BY_REASON), screen_id=existing["id"],
            error=None, failed_member=None, superseded_screen_ids=superseded,
        )
        return existing, True

    attempted = 0

    def _counting_progress(entry: dict) -> None:
        nonlocal attempted
        attempted += 1
        if progress is not None:
            progress(entry)

    try:
        result = compute_screen(
            universe_store, bar_store, bar_index, dataset_store, config, screen_date,
            progress=_counting_progress, should_abort=should_abort,
        )

        if should_abort is not None and should_abort():
            _log(
                state="cancelled", reused=False, members_attempted=attempted,
                ranked_count=len(result["rows"]),
                skipped_by_reason=_tally_skipped_by_reason(result["skipped"]),
                screen_id=None, error=None, failed_member=None,
            )
            return None, False

        try:
            recorded = screen_store.record(
                screen_date=result["screen_date"],
                as_of=result["as_of"],
                universe_snapshot_id=result["universe_snapshot_id"],
                config_fingerprint=result["config_fingerprint"],
                bar_store_signature=result["bar_store_signature"],
                screen_coverage_signature=result["screen_coverage_signature"],
                rows=result["rows"],
                skipped=result["skipped"],
            )
            # The replacement is on disk BEFORE its predecessors are removed, and the run is logged
            # `done` even if the prune itself raises (a full disk, a read-only dir): the snapshot
            # genuinely WAS recorded, so re-entering the outer handler and calling this run "failed"
            # would be a fabrication. The `logged` latch makes that structural -- the error still
            # propagates verbatim, it just never rewrites this run's own honest outcome.
            superseded: list[str] = []
            try:
                superseded = _settle_date(recorded["id"])
            finally:
                _log(
                    state="done", reused=False, members_attempted=attempted,
                    ranked_count=len(result["rows"]),
                    skipped_by_reason=_tally_skipped_by_reason(result["skipped"]),
                    screen_id=recorded["id"], error=None, failed_member=None,
                    superseded_screen_ids=superseded,
                )
            return recorded, False
        except ScreenAlreadyRecorded as exc:
            existing2 = screen_store.find_by_key(
                result["screen_date"], result["as_of"], result["universe_snapshot_id"],
                result["config_fingerprint"], result["bar_store_signature"],
            )
            assert existing2 is not None and existing2["id"] == exc.existing_id
            superseded = _settle_date(existing2["id"])
            _log(
                state="done", reused=True, members_attempted=attempted,
                ranked_count=len(result["rows"]),
                skipped_by_reason=_tally_skipped_by_reason(result["skipped"]),
                screen_id=existing2["id"], error=None, failed_member=None,
                superseded_screen_ids=superseded,
            )
            return existing2, True
    except Exception as exc:  # noqa: BLE001 -- any OTHER failure (a raising member inside
        # `compute_screen`, or a `ScreenIntegrityError` from a damaged snapshot at this key) --
        # logged as "failed", then RE-RAISED verbatim so every existing caller's own crash-handling
        # (the manager's `_work` except-clause, an uncaught CLI crash) stays byte-unchanged.
        failed_member = members[attempted] if 0 < attempted < len(members) else None
        _log(
            state="failed", reused=False, members_attempted=attempted, ranked_count=0,
            skipped_by_reason=dict(_EMPTY_SKIPPED_BY_REASON), screen_id=None,
            error=str(exc), failed_member=failed_member,
        )
        raise


class DeskScreenComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) desk screen compute job. Construct with no
    arguments -- every ``trigger()`` call takes its stores/config explicitly (the
    ``EdgeReportComputeManager``/``DeskTopupComputeManager`` per-call-injection precedent)."""

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
        screen_date: str,
        universe_store: UniverseStore,
        bar_store: BarStore,
        bar_index: BarIndex,
        dataset_store: DatasetStore,
        config: Config,
        screen_store: ScreenStore,
        *,
        screen_run_store: ScreenRunStore | None = None,
        forward_store: ForwardStore | None = None,
    ) -> dict:
        """Start a NEW screen compute job for ``screen_date``, or -- if one is already
        ``state == "running"`` -- return it UNCHANGED (``started: False``, single-flight, TC-7).
        Once the current job is terminal (done/cancelled/failed, or none has ever run), the NEXT
        call always starts a genuinely new job (a fresh id), discarding the prior snapshot. Never
        blocks -- the walk runs on a dedicated worker thread, off the caller's thread, so an HTTP
        route calling this returns immediately.

        goal-desk-iter-29 (J-18): ``screen_run_store``, if given, is threaded straight through to
        ``run_screen_and_record`` -- an OPTIONAL, keyword-only, per-call dependency (default
        ``None``, unlike J-09/J-10's REQUIRED ``topup_run_store``/``reconcile_run_store``) so every
        EXISTING test that calls ``trigger`` positionally with no run-store argument keeps passing
        unmodified; the real HTTP route (``desk_routes.py``) always supplies a real store.
        ``forward_store`` is threaded through the same way, for the same reason -- see
        ``run_screen_and_record``'s own "One snapshot per date" section."""
        with self._lock:
            current = self._snapshot
            if current is not None and current["state"] == "running":
                return {"started": False, "compute": _copy_snapshot(current)}

            records, _errors = universe_store.list()
            members_total = len(records[-1]["members"]) if records else 0

            job_id = uuid.uuid4().hex
            cancel_event = threading.Event()
            self._cancel_event = cancel_event
            snapshot = {
                "id": job_id,
                "state": "running",
                "screen_date": screen_date,
                "started_utc": _iso_utc_now(),
                "finished_utc": None,
                "error": None,
                # era-desk-iter-4 J-04 (audit B2): honest until a terminal state resolves --
                # "initial/running: reused false, screen_id null" (nothing recorded yet).
                "reused": False,
                "screen_id": None,
                "progress": {"members_total": members_total, "members_done": 0, "current": None},
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
                        **progress, "members_done": progress["members_done"] + 1,
                        "current": entry["symbol"],
                    },
                }

        def _work() -> None:
            try:
                record, reused = run_screen_and_record(
                    universe_store, bar_store, bar_index, dataset_store, config, screen_store,
                    screen_date, progress=_publish, should_abort=cancel_event.is_set,
                    screen_run_store=screen_run_store, forward_store=forward_store,
                )
            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                self._resolve(job_id, "failed", error=str(exc))
                return
            # ``record is None`` means the walk observed the cancel BEFORE persisting anything, so
            # `screen_id`/`reused` fall out to null/False -- nothing was recorded.
            #
            # The converse does NOT hold, and the snapshot deliberately reports the truth rather
            # than the tidier rule (era-desk-iter-4 audit B3): a cancel that lands in the window
            # between `run_screen_and_record`'s own should_abort() check and this line resolves
            # `state: "cancelled"` WITH a non-null `screen_id` (and `reused: true` if that pin was
            # already on file). Something really was recorded in that race, and saying so is more
            # honest than reporting null for a snapshot the operator can go and read.
            self._resolve(
                job_id, "cancelled" if cancel_event.is_set() else "done", error=None,
                reused=reused, screen_id=record["id"] if record is not None else None,
            )

        thread = threading.Thread(target=_work, name=f"desk-screen-compute:{job_id}", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return {"started": True, "compute": _copy_snapshot(snapshot)}

    def _resolve(
        self, job_id: str, state: str, *, error: str | None,
        reused: bool = False, screen_id: str | None = None,
    ) -> None:
        with self._lock:
            current = self._snapshot
            if current is None or current["id"] != job_id:
                return  # superseded -- never resolve a job that is no longer the current one
            self._snapshot = {
                **current, "state": state, "finished_utc": _iso_utc_now(), "error": error,
                "reused": reused, "screen_id": screen_id,
            }

    def cancel(self) -> None:
        """Signal cooperative cancellation for the in-flight job -- a harmless no-op if idle (the
        ROUTE is the one that rejects an idle cancel with a 409 -- see ``desk_routes.py``)."""
        with self._lock:
            cancel_event = self._cancel_event
        if cancel_event is not None:
            cancel_event.set()

    def join_all(self, timeout: float = 30.0) -> None:
        """Wait for the in-flight job thread, if any (test/shutdown hygiene -- the
        ``EdgeReportComputeManager.join_all`` precedent)."""
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)


# --- The CLI warmer --------------------------------------------------------------------------------
# Mirrors ``desk_topup_compute.py``'s own CLI precedent: resolves the SAME env/config seams the
# backend reads, runs ``run_screen_and_record`` to completion SYNCHRONOUSLY in-process (no manager,
# no background thread -- a CLI invocation IS the one caller), and exits 0 with a summary.
# ``--date`` is REQUIRED (``argparse``'s own ``required=True`` exits non-zero with a usage error on
# a missing value) -- this CLI never defaults to today's wall-clock date (T-6).


def _cli_progress_printer() -> Callable[[dict], None]:
    def _printer(entry: dict) -> None:
        print(f"[{entry['symbol']}] done", flush=True)

    return _printer


def main() -> int:
    """The CLI entry: ``python -m app.research.desk_screen_compute --date YYYY-MM-DD``. Runs the
    screen to completion against the operator's real universe/bar/dataset dirs, publishing to the
    SAME durable screen store ``GET /research/desk/screen`` serves."""
    parser = argparse.ArgumentParser(
        description="Era B \"The Desk\" J-03 CLI warmer -- compute the desk screen for a REQUIRED "
        "--date (never defaults to today), over the latest registered universe snapshot, and "
        "persist it append-only to the SAME durable screen store GET /research/desk/screen serves."
    )
    parser.add_argument(
        "--date", required=True,
        help="the screen date (YYYY-MM-DD) to compute the screen for -- REQUIRED; never defaults "
        "to today's wall-clock date (T-6).",
    )
    args = parser.parse_args()

    config = CONFIG
    universe_store = UniverseStore(config.desk_universe_dir_resolved())
    bar_store = get_bar_store()
    bar_index = get_bar_index()
    dataset_store = get_dataset_store()
    screen_store = ScreenStore(resolve_desk_screen_dir(config.desk_universe_dir_resolved()))
    # goal-desk-iter-29 (J-18): the SAME single shared writer the HTTP route uses -- a run started
    # from this CLI is durably logged exactly like one started from `/desk`'s Run Screen button.
    screen_run_store = ScreenRunStore(
        resolve_desk_screen_log_dir(config.desk_universe_dir_resolved())
    )
    # Superseding a snapshot drops the forward records measured against it -- the CLI settles a
    # date exactly the way the HTTP route does, or a run started from the terminal would leave
    # forward records pointing at an id nothing can resolve.
    forward_store = ForwardStore(resolve_desk_forward_dir(config.desk_universe_dir_resolved()))

    # The identical non-session refusal ``POST /research/desk/screen/compute`` applies, so the
    # terminal is not a way around it (a screen for a Saturday, a market holiday, or a date that
    # has not happened yet is permanent, useless and structurally unmeasurable). Fails OPEN: with
    # no daily bars recorded nothing is refused, and this CLI behaves exactly as it did before.
    universe_records, _universe_errors = universe_store.list()
    if universe_records:
        refusal = refuse_if_not_a_session(
            args.date, bar_store, list(universe_records[-1]["members"])
        )
        if refusal is not None:
            print(f"refused: {refusal}")
            return 2

    walk_started = time.perf_counter()
    recorded, reused = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, config, screen_store,
        args.date, progress=_cli_progress_printer(), screen_run_store=screen_run_store,
        forward_store=forward_store,
    )
    # Printed, never recorded: how long a walk took is a property of this machine on this day, not
    # of the screen it resolved, and the run record's own started/finished pair already bounds it.
    print(
        f"desk screen complete for {args.date}: {len(recorded['rows'])} ranked, "
        f"{len(recorded['skipped'])} skipped -- snapshot {recorded['id']} "
        f"({'reused existing' if reused else 'newly recorded'}) "
        f"in {time.perf_counter() - walk_started:.1f}s "
        f"({_screen_workers()} worker process(es))."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
