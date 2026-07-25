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
``bars.py``/``datasets.py``'s own stat-keyed caches followed."""

from __future__ import annotations

import argparse
import threading
import uuid
from datetime import datetime, timezone
from typing import Callable

from ..config import CONFIG, Config
from .bar_index import BarIndex
from .bars import BarStore
from .datasets import DatasetStore
from .desk_screen import ScreenAlreadyRecorded, ScreenStore, compute_screen, resolve_desk_screen_dir
from .desk_universe import UniverseStore
from .routes import get_bar_index, get_bar_store, get_dataset_store

__all__ = ["DeskScreenComputeManager", "run_screen_and_record"]


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
) -> dict:
    """Compute ONE screen (``compute_screen`` -- the sole walker) and persist it, append-only. If
    an identical-pin screen is already recorded, the EXISTING snapshot's meta is returned (never a
    second file, never a rewrite) rather than raising -- ``ScreenAlreadyRecorded`` is caught here,
    not propagated, since reusing an already-recorded snapshot is a normal, expected outcome, not a
    failure. A cancelled (partial) walk is NEVER recorded -- returns ``None`` instead (the caller
    distinguishes "cancelled, nothing recorded" from "recorded/reused" by this ``None`` check)."""
    result = compute_screen(
        universe_store, bar_store, bar_index, dataset_store, config, screen_date,
        progress=progress, should_abort=should_abort,
    )
    if should_abort is not None and should_abort():
        return None
    try:
        return screen_store.record(
            screen_date=result["screen_date"],
            as_of=result["as_of"],
            universe_snapshot_id=result["universe_snapshot_id"],
            config_fingerprint=result["config_fingerprint"],
            bar_store_signature=result["bar_store_signature"],
            rows=result["rows"],
            skipped=result["skipped"],
        )
    except ScreenAlreadyRecorded as exc:
        existing = screen_store.find_by_key(
            result["screen_date"], result["as_of"], result["universe_snapshot_id"],
            result["config_fingerprint"], result["bar_store_signature"],
        )
        assert existing is not None and existing["id"] == exc.existing_id
        return existing


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
    ) -> dict:
        """Start a NEW screen compute job for ``screen_date``, or -- if one is already
        ``state == "running"`` -- return it UNCHANGED (``started: False``, single-flight, TC-7).
        Once the current job is terminal (done/cancelled/failed, or none has ever run), the NEXT
        call always starts a genuinely new job (a fresh id), discarding the prior snapshot. Never
        blocks -- the walk runs on a dedicated worker thread, off the caller's thread, so an HTTP
        route calling this returns immediately."""
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
                run_screen_and_record(
                    universe_store, bar_store, bar_index, dataset_store, config, screen_store,
                    screen_date, progress=_publish, should_abort=cancel_event.is_set,
                )
            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                self._resolve(job_id, "failed", error=str(exc))
                return
            self._resolve(job_id, "cancelled" if cancel_event.is_set() else "done", error=None)

        thread = threading.Thread(target=_work, name=f"desk-screen-compute:{job_id}", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return {"started": True, "compute": _copy_snapshot(snapshot)}

    def _resolve(self, job_id: str, state: str, *, error: str | None) -> None:
        with self._lock:
            current = self._snapshot
            if current is None or current["id"] != job_id:
                return  # superseded -- never resolve a job that is no longer the current one
            self._snapshot = {**current, "state": state, "finished_utc": _iso_utc_now(), "error": error}

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

    recorded = run_screen_and_record(
        universe_store, bar_store, bar_index, dataset_store, config, screen_store,
        args.date, progress=_cli_progress_printer(),
    )
    print(
        f"desk screen complete for {args.date}: {len(recorded['rows'])} ranked, "
        f"{len(recorded['skipped'])} skipped -- snapshot {recorded['id']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
