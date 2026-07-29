"""Coverage-index reconciliation (Era B "The Desk", J-10, goal-desk-iter-14) — classifies drift
between the frozen, checksummed JSON ``BarStore`` and the derived, rebuildable ``bar_index`` SQLite
index, repairs it through the EXISTING ``BarIndex.reindex()`` (``bar_index.py:198`` — the only
repair path; this module never builds a second one), and persists a durable, append-only record of
what was wrong before and what is right after — the goal-proposer's own measurement (2026-07-28)
found that repair path was reachable by nothing outside its own test; this module is exactly what
closes that gap.

THIS MODULE computes NOTHING new about bars or coverage — it is a pure READ-then-REPAIR lens over
two already-canonical owners' EXISTING public methods: ``BarStore.list(include_bars=False)`` (its
``records``/``errors`` split) and ``BarIndex.list()``/``BarIndex.reindex()``. Zero diff to either
file — no new accessor, no schema change (see ``classify_drift``'s docstring for the filename-stem
insight that makes this possible with zero new accessor). ``desk_coverage.get_desk_coverage`` keeps
its single existing ownership of coverage/freshness and needs no code change to reflect a repair —
once ``reindex()`` adds a missing row, the NEXT ``bar_index.coverage()`` call already sees it.

**Three honest drift buckets** (goal.md J-10 step 1), built from ``BarStore._path(id) ==
root/f"{id}.json"`` (``bars.py:273-274`` — a file's name IS its series_id with ``.json`` stripped,
so ``{Path(e["file"]).stem for e in errors}`` gives the set of series_ids whose file exists but is
corrupted, with zero new ``bars.py`` accessor):

  * ``unindexed_series`` — a HEALTHY record whose id has no ``bar_index.list()`` hit at all
    (attributed to that record's own ``symbol``/``timeframe``);
  * ``orphan_index_rows`` — an indexed ``series_id`` that is neither a healthy record NOR a
    corrupted-file stem (no file on disk at all, healthy or corrupt) — reported by ``series_id``
    alone (no symbol/timeframe attached — there is nothing on disk to attribute one from);
  * ``stale_checksum_rows`` — an indexed ``series_id`` that IS a corrupted-file stem (a file exists
    on disk under that id, but the store can no longer verify/report it) — reported by
    ``series_id`` alone.

Since ``BarStore.list()`` puts each file in ``healthy`` XOR ``errors``, never both, buckets (b)/(c)
are mutually exclusive by construction — no extra tie-breaking logic is needed, and no ``series_id``
can ever land in two buckets.

**The single repair walker.** ``run_reconcile`` is the SOLE caller of ``BarIndex.reindex()`` outside
tests — mirrors ``desk_topup_compute.run_topup``'s "one walker, every caller uses it" shape. It
classifies (phase ``"classifying"``), repairs (phase ``"reindexing"`` — ``reindex()`` is DROP-and-
repopulate over HEALTHY records only, so a corrupt file the rebuilt index therefore cannot carry is
disclosed on the record via ``store_errors``, never silently dropped), and re-verifies (phase
``"verifying"``) — publishing each phase transition through an optional ``progress`` callback (the
``run_topup`` precedent) so the compute manager below can surface live state. An optional
``should_abort`` callback, checked once BEFORE the repair phase starts, gives a genuine cooperative
cancel point: if it fires there, the repair is skipped entirely and the returned dict reports
``drift_after == drift_before`` / ``rows_indexed_after == rows_indexed_before`` / ``aborted: True`` —
never a raise, never a fabricated partial repair.

**The durable run-record store.** ``ReconcileRunStore`` mirrors ``desk_topup_log.TopupRunStore``'s
discipline byte-for-byte: a checksum-verified load on every read (``ReconcileRunIntegrityError`` on
any mismatch, never silence, never a fabricated record), ``record()`` the only mutation, no
update/delete method anywhere, and — like ``TopupRunStore``, unlike ``UniverseStore``/
``ScreenStore`` — NO content-based dedup: every terminal reconciliation is its own genuinely
distinct event, so ``record()`` always writes a brand-new file. A run whose PROCESS ends before this
module's writer is ever called leaves NO record — there is no "pending"/"partial" file, because
``record()`` is the ONLY write path and it is called exactly once, at the very end of a run's
lifecycle.

**Storage dir — no new ``Config`` field.** ``resolve_desk_index_reconcile_dir`` mirrors
``desk_topup_log.resolve_desk_topup_log_dir`` exactly: a bare
``TAPEOLOGY_DESK_INDEX_RECONCILE_DIR`` env-var override, else a directory co-located as a SIBLING of
the caller's own already-resolved universe directory — an operational storage-location knob, never a
value that shapes a served result, so ``config_fingerprint()`` stays untouched.

**The compute manager.** ``DeskIndexReconcileComputeManager`` mirrors ``DeskTopupComputeManager``'s
shape (one in-flight job slot, atomic snapshot publish under a lock, cooperative cancel, process-
scoped state honestly lost on restart) but has a SIMPLER dependency surface: reconciliation never
touches universe membership or ``record_bar_series``, so — unlike ``DeskTopupComputeManager``, which
must import FROM ``routes.py`` to reuse ``record_bar_series`` — this module has NO reason to import
anything from ``routes.py`` and carries no circular-import constraint. It is still placed as a
module-level singleton behind a FastAPI dependency in ``desk_routes.py`` for consistency with its
two siblings. No CLI warmer ships this iteration (goal.md's J-10 text never names one, unlike
J-02/J-03 — the repair is a fast, local, no-network rebuild, so the POST route itself already serves
the "real operator run" role)."""

from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..config import CONFIG
from .bar_index import BarIndex
from .bars import BarStore

__all__ = [
    "DeskIndexReconcileComputeManager",
    "ReconcileRunIntegrityError",
    "ReconcileRunStore",
    "classify_drift",
    "record_reconcile_run",
    "resolve_desk_index_reconcile_dir",
    "run_reconcile",
]

_EMPTY_DRIFT: dict = {"unindexed_series": [], "orphan_index_rows": [], "stale_checksum_rows": []}


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


# --- classify_drift / run_reconcile -- the pure composition + the sole repair walker --------------


def classify_drift(store: BarStore, bar_index: BarIndex) -> tuple[dict, list[dict]]:
    """Pure composition of ``store.list(include_bars=False)`` and ``bar_index.list()`` (called with
    NO symbol/timeframe filter — every indexed row) into the three honest buckets described in the
    module docstring. Returns ``(drift, store_errors)`` — ``store_errors`` is ``BarStore.list()``'s
    OWN ``errors`` list, passed through unchanged (never re-derived, never dropped) so a caller
    never has to call ``store.list()`` a second time just to learn what this call already saw.

    Every bucket is returned in a DETERMINISTIC order: ``unindexed_series`` follows
    ``store.list()``'s own oldest-first order; ``orphan_index_rows``/``stale_checksum_rows`` are
    sorted by ``series_id`` — never raw set-iteration order, which is not reproducible across
    processes."""
    healthy, errors = store.list(include_bars=False)
    indexed = bar_index.list()

    healthy_ids = {record["id"] for record in healthy}
    corrupt_ids = {Path(error["file"]).stem for error in errors}
    indexed_ids = {hit.series_id for hit in indexed}

    unindexed_series = [
        {"series_id": record["id"], "symbol": record["symbol"], "timeframe": record["timeframe"]}
        for record in healthy
        if record["id"] not in indexed_ids
    ]
    sorted_hits = sorted(indexed, key=lambda hit: hit.series_id)
    orphan_index_rows = [
        {"series_id": hit.series_id}
        for hit in sorted_hits
        if hit.series_id not in healthy_ids and hit.series_id not in corrupt_ids
    ]
    stale_checksum_rows = [
        {"series_id": hit.series_id} for hit in sorted_hits if hit.series_id in corrupt_ids
    ]

    drift = {
        "unindexed_series": unindexed_series,
        "orphan_index_rows": orphan_index_rows,
        "stale_checksum_rows": stale_checksum_rows,
    }
    return drift, errors


def run_reconcile(
    store: BarStore,
    bar_index: BarIndex,
    *,
    progress: Callable[[str], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> dict:
    """The SOLE walker (mirrors ``desk_topup_compute.run_topup``): classify -> repair through
    ``BarIndex.reindex(store)`` (the ONLY repair path, never a second one) -> re-classify. Returns
    ``{"series_on_disk", "rows_indexed_before", "rows_indexed_after", "drift_before", "drift_after",
    "store_errors", "aborted"}``.

    ``progress``, if given, is called with the phase name after each phase transition
    (``"classifying"`` -> ``"reindexing"`` -> ``"verifying"``) — the ``run_topup`` per-pair progress
    callback precedent, applied to this operation's own three phases. ``should_abort``, if given and
    it returns ``True`` before the repair phase starts, skips ``reindex()`` entirely: the returned
    dict reports ``drift_after == drift_before``, ``rows_indexed_after == rows_indexed_before``, and
    ``aborted: True`` — a cooperative stop, never a raise, never a fabricated partial repair."""
    if progress is not None:
        progress("classifying")
    drift_before, store_errors = classify_drift(store, bar_index)
    rows_indexed_before = len(bar_index.list())
    healthy, _errors = store.list(include_bars=False)
    series_on_disk = len(healthy)

    if should_abort is not None and should_abort():
        return {
            "series_on_disk": series_on_disk,
            "rows_indexed_before": rows_indexed_before,
            "rows_indexed_after": rows_indexed_before,
            "drift_before": drift_before,
            "drift_after": drift_before,
            "store_errors": store_errors,
            "aborted": True,
        }

    if progress is not None:
        progress("reindexing")
    bar_index.reindex(store)

    if progress is not None:
        progress("verifying")
    drift_after, _errors_after = classify_drift(store, bar_index)
    rows_indexed_after = len(bar_index.list())

    return {
        "series_on_disk": series_on_disk,
        "rows_indexed_before": rows_indexed_before,
        "rows_indexed_after": rows_indexed_after,
        "drift_before": drift_before,
        "drift_after": drift_after,
        "store_errors": store_errors,
        "aborted": False,
    }


# --- the durable, append-only run-record store (mirrors desk_topup_log.py byte-for-byte) ----------

_RECONCILE_LOG_DIR_ENV = "TAPEOLOGY_DESK_INDEX_RECONCILE_DIR"
_TERMINAL_STATES = ("done", "cancelled", "failed")


class ReconcileRunIntegrityError(Exception):
    """An on-disk reconciliation run-record file failed its checksum verification on load —
    corrupted or tampered, surfaced explicitly (never silence, never a fabricated record)."""


def resolve_desk_index_reconcile_dir(desk_universe_dir_resolved: str) -> str:
    """The reconciliation run log's directory: the ``TAPEOLOGY_DESK_INDEX_RECONCILE_DIR`` env var
    if set, else a directory co-located as a SIBLING of the CALLER's own already-resolved universe
    directory (the ``desk_topup_log.resolve_desk_topup_log_dir`` pattern verbatim — takes a plain
    string, never imports ``config.py``'s singleton). Deliberately NOT a ``Config`` field (see the
    module docstring) — this keeps ``config_fingerprint()`` untouched this iteration."""
    override = os.environ.get(_RECONCILE_LOG_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "index_reconcile_runs")


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding this module's checksums hash (stable across processes:
    sorted keys, no whitespace) — the SAME encoding ``desk_topup_log.py``/``desk_screen.py`` hash
    (each module owns its own copy of this tiny helper per this project's established convention)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _copy_drift(drift: dict) -> dict:
    """A fresh, independent copy of a drift dict's three nested lists — so a caller mutating a
    returned record can never poison a later read (the ``desk_universe.UniverseStore.list``
    per-row-copy discipline, applied to this module's own nested shape)."""
    return {
        "unindexed_series": [dict(entry) for entry in drift["unindexed_series"]],
        "orphan_index_rows": [dict(entry) for entry in drift["orphan_index_rows"]],
        "stale_checksum_rows": [dict(entry) for entry in drift["stale_checksum_rows"]],
    }


def _copy_meta(meta: dict) -> dict:
    return {
        **meta,
        "drift_before": _copy_drift(meta["drift_before"]),
        "drift_after": _copy_drift(meta["drift_after"]),
        "store_errors": [dict(error) for error in meta["store_errors"]],
    }


class ReconcileRunStore:
    """File-based store rooted at the config-owned reconciliation-log directory — the ONE
    reader/writer. Mirrors ``desk_topup_log.TopupRunStore``'s load/checksum discipline exactly;
    like that store (unlike ``UniverseStore``/``ScreenStore``), ``record`` performs no content-keyed
    dedup — every call always persists a genuinely new file, since every terminal reconciliation is
    its own distinct event."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.json"

    def _load(self, path: Path) -> dict:
        """Load ONE run-record file, verifying its whole-record checksum. Raises
        ``ReconcileRunIntegrityError`` for any parse/shape/checksum failure — explicit, never
        silent."""
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise ReconcileRunIntegrityError(
                f"index reconciliation run record file '{path.name}' is not parseable ({exc}) -- "
                f"corrupted or tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise ReconcileRunIntegrityError(
                f"index reconciliation run record file '{path.name}' does not carry the expected "
                f"record shape -- corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise ReconcileRunIntegrityError(
                f"index reconciliation run record file '{path.name}' failed its integrity check "
                f"(checksum mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise ReconcileRunIntegrityError(
                f"index reconciliation run record file '{path.name}' does not carry the expected "
                f"record shape -- corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every registered run's full content (each file verified), oldest-started first, plus an
        EXPLICIT error row per file that failed verification — a corrupt file is surfaced, never
        silently hidden and never served as data. A store whose directory was never created (no run
        has ever been recorded) returns ``([], [])`` — the honest-empty case."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                meta = self._load(path)
                records.append(_copy_meta(meta))
            except ReconcileRunIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("started_utc", ""), meta.get("id", "")))
        return records, errors

    def record(
        self,
        *,
        config_fingerprint: str,
        started_utc: str,
        finished_utc: str,
        state: str,
        series_on_disk: int,
        rows_indexed_before: int,
        rows_indexed_after: int,
        drift_before: dict,
        drift_after: dict,
        store_errors: list[dict],
    ) -> dict:
        """Persist ONE new reconciliation run record — ALWAYS a genuinely new file: no content-keyed
        dedup exists in this store, so a second call with identical field values still appends a
        second, distinct record."""
        if state not in _TERMINAL_STATES:
            raise ValueError(f"invalid terminal state {state!r} -- must be one of {_TERMINAL_STATES}")
        date = started_utc[:10]  # started_utc is always an ISO-8601 UTC string -- a YYYY-MM-DD prefix
        run_id = f"reconcile-{date}-{uuid.uuid4().hex[:12]}"
        # A path collision is astronomically unlikely, but this store never silently overwrites an
        # existing file regardless of cause -- mirrors TopupRunStore.record's identical defensive
        # re-roll instead of a blind write.
        while self._path(run_id).exists():
            run_id = f"reconcile-{date}-{uuid.uuid4().hex[:12]}"
        meta = {
            "id": run_id,
            "config_fingerprint": config_fingerprint,
            "started_utc": started_utc,
            "finished_utc": finished_utc,
            "state": state,
            "series_on_disk": series_on_disk,
            "rows_indexed_before": rows_indexed_before,
            "rows_indexed_after": rows_indexed_after,
            "drift_before": _copy_drift(drift_before),
            "drift_after": _copy_drift(drift_after),
            "store_errors": [dict(error) for error in store_errors],
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(run_id).write_text(json.dumps(payload))
        return _copy_meta(meta)


def record_reconcile_run(
    store: ReconcileRunStore,
    *,
    config_fingerprint: str,
    started_utc: str,
    finished_utc: str,
    state: str,
    series_on_disk: int,
    rows_indexed_before: int,
    rows_indexed_after: int,
    drift_before: dict,
    drift_after: dict,
    store_errors: list[dict],
) -> dict:
    """THE single shared writer — called exactly once, at a run's terminal state, by
    ``DeskIndexReconcileComputeManager``'s worker resolve path, and nothing else. A thin, explicit
    free function over ``ReconcileRunStore.record`` (rather than the call site invoking the method
    directly) so a future reader grepping for ``record_reconcile_run`` finds the one call site — the
    ``desk_topup_log.record_topup_run`` precedent."""
    return store.record(
        config_fingerprint=config_fingerprint,
        started_utc=started_utc,
        finished_utc=finished_utc,
        state=state,
        series_on_disk=series_on_disk,
        rows_indexed_before=rows_indexed_before,
        rows_indexed_after=rows_indexed_after,
        drift_before=drift_before,
        drift_after=drift_after,
        store_errors=store_errors,
    )


# --- the compute manager (mirrors DeskTopupComputeManager's shape) --------------------------------


def _copy_snapshot(snapshot: dict) -> dict:
    """A caller-safe copy (``progress`` is a fresh dict too) so a reader mutating what
    ``snapshot()`` returns can never poison ``DeskIndexReconcileComputeManager``'s own internal
    state (the ``EdgeReportComputeManager._copy_snapshot`` precedent)."""
    return {**snapshot, "progress": dict(snapshot["progress"])}


class DeskIndexReconcileComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) coverage-index reconciliation job. Construct
    with no arguments — every ``trigger()`` call takes its stores explicitly (the
    ``EdgeReportComputeManager``/``DeskTopupComputeManager`` per-call-injection precedent), so a
    test (or a future second registry) points this at any hermetic store set with zero constructor
    plumbing. Simpler dependency surface than ``DeskTopupComputeManager``'s: reconciliation touches
    only a ``BarStore``/``BarIndex``/``ReconcileRunStore`` — no ``UniverseStore``, no
    ``ResearchRegistry``, no import from ``routes.py``."""

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
        bar_store: BarStore,
        bar_index: BarIndex,
        reconcile_run_store: ReconcileRunStore,
    ) -> dict:
        """Start a NEW reconciliation job, or — if one is already ``state == "running"`` — return it
        UNCHANGED (``started: False``, single-flight). Never blocks — the walk runs on a dedicated
        worker thread, off the caller's thread. The job's terminal outcome is durably recorded into
        ``reconcile_run_store`` once it resolves, via the single shared writer
        ``record_reconcile_run`` (called from ``_work``'s two exit paths below)."""
        with self._lock:
            current = self._snapshot
            if current is not None and current["state"] == "running":
                return {"started": False, "compute": _copy_snapshot(current)}

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
                "progress": {"phase": "classifying"},
            }
            self._snapshot = snapshot

        def _publish_phase(phase: str) -> None:
            with self._lock:
                current = self._snapshot
                if current is None or current["id"] != job_id:
                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
                self._snapshot = {**current, "progress": {"phase": phase}}

        def _record_run(*, state: str, result: dict | None) -> None:
            record_reconcile_run(
                reconcile_run_store,
                config_fingerprint=CONFIG.config_fingerprint(),
                started_utc=started_utc,
                finished_utc=_iso_utc_now(),
                state=state,
                series_on_disk=result["series_on_disk"] if result else 0,
                rows_indexed_before=result["rows_indexed_before"] if result else 0,
                rows_indexed_after=result["rows_indexed_after"] if result else 0,
                drift_before=result["drift_before"] if result else _EMPTY_DRIFT,
                drift_after=result["drift_after"] if result else _EMPTY_DRIFT,
                store_errors=result["store_errors"] if result else [],
            )

        def _work() -> None:
            try:
                result = run_reconcile(
                    bar_store, bar_index, progress=_publish_phase, should_abort=cancel_event.is_set,
                )
            except Exception as exc:  # noqa: BLE001 -- a catastrophic, unexpected failure, never
                # swallowed (the DeskTopupComputeManager precedent).
                self._resolve(job_id, "failed", error=str(exc))
                _record_run(state="failed", result=None)
                return
            state = "cancelled" if result["aborted"] else "done"
            self._resolve(job_id, state, error=None)
            _record_run(state=state, result=result)

        thread = threading.Thread(
            target=_work, name=f"desk-index-reconcile-compute:{job_id}", daemon=True
        )
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
                **current, "state": state, "finished_utc": _iso_utc_now(), "error": error,
            }

    def cancel(self) -> None:
        """Signal cooperative cancellation for the in-flight job — a harmless no-op if idle (the
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
