"""The screen run log (Era B "The Desk", goal-desk-iter-29, J-18) -- an append-only, checksummed
record of what every desk SCREEN compute run attempted, surviving past the next run superseding
``DeskScreenComputeManager``'s in-flight/last-terminal snapshot (``desk_screen_compute.py``'s job
state is explicitly process-scoped and honestly lost on restart -- this module is the durable
counterpart the goal.md J-18 journey adds beside it, mirroring the J-09 (``desk_topup_log.py``) /
J-10 (``desk_index_reconcile.py``) run-log discipline verbatim).

THIS module computes NOTHING about screens, bands, or ranking itself -- it is a pure PERSISTENCE
lens over what ``run_screen_and_record`` (``desk_screen_compute.py``) already resolves/computes. A
run record is written EXACTLY ONCE, at the run's terminal state, by the single shared writer
(``record_screen_run`` below) -- called from inside ``run_screen_and_record`` itself (the ONE shared
entry point both ``DeskScreenComputeManager``'s resolve path and the CLI's ``main()`` already call),
and nowhere else.

**Records the RUN only -- zero diff to what a screen snapshot itself records.** ``desk_screen.py``'s
``ScreenStore`` stays the sole owner of screen snapshots/rows/skips/the five-pin key; this module
never reads or writes a screen snapshot file, never re-derives a pin, and never duplicates
``rows``/``skipped`` content -- only their COUNTS (``ranked_count``/``skipped_by_reason``) are
recorded here, exactly the same "attempt-level summary, not content" split ``desk_topup_log.py``
draws between a run's outcomes and a top-up's per-pair detail.

**Mirrors ``desk_topup_log.TopupRunStore``/``desk_index_reconcile.ReconcileRunStore``'s discipline
byte-for-byte** -- a checksum-verified load on every read (``ScreenRunIntegrityError`` on any
mismatch, never silence, never a fabricated record), ``record()`` the only mutation, no
update/delete function anywhere (immutability is structural, not policed), and NO content-based
deduplication: every terminal run is its own genuinely distinct event -- even an all-``reused`` run
over an unchanged store is a real, separate attempt with its own ``started_utc``/``finished_utc`` --
so ``record()`` always writes a brand-new file.

**Interrupted-run honesty (a DoD clause, structural by construction).** A run whose PROCESS ends
before this module's writer is ever called (a crash, ``kill -9``, a power loss) leaves NO record --
there is no "pending" or "partial" file ever written, because ``record()`` is the ONLY write path in
this module and it is called exactly once, at the very end of a run's lifecycle, never earlier and
never speculatively.

**Storage dir -- no new ``Config`` field.** ``resolve_desk_screen_log_dir`` mirrors
``resolve_desk_topup_log_dir``/``resolve_desk_screen_dir`` exactly: a bare
``TAPEOLOGY_DESK_SCREEN_LOG_DIR`` env-var override, else a directory co-located as a SIBLING of the
caller's own already-resolved universe directory -- an operational storage-location knob, never a
value that shapes a served result, so ``config_fingerprint()`` stays untouched (the Constraints'
own explicit sanction for "worker counts, timeouts, store dirs")."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path

__all__ = [
    "ScreenRunIntegrityError",
    "ScreenRunStore",
    "record_screen_run",
    "resolve_desk_screen_log_dir",
]

# The store's own env-var override (the ``TAPEOLOGY_DESK_TOPUP_LOG_DIR``/
# ``TAPEOLOGY_DESK_INDEX_RECONCILE_DIR`` pattern) -- see ``resolve_desk_screen_log_dir``.
_SCREEN_LOG_DIR_ENV = "TAPEOLOGY_DESK_SCREEN_LOG_DIR"

# The three terminal states a run record may carry -- never "running" (a record is written once, at
# terminal state only; see the module docstring's "interrupted-run honesty" section).
_TERMINAL_STATES = ("done", "cancelled", "failed")


class ScreenRunIntegrityError(Exception):
    """An on-disk run-record file failed its checksum verification on load -- corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated record)."""


def resolve_desk_screen_log_dir(desk_universe_dir_resolved: str) -> str:
    """The screen run log's directory: the ``TAPEOLOGY_DESK_SCREEN_LOG_DIR`` env var if set, else a
    directory co-located as a SIBLING of the CALLER's own already-resolved universe directory (the
    ``resolve_desk_topup_log_dir`` pattern verbatim -- takes a plain string, never imports
    ``config.py``'s singleton, so the caller resolves its own universe directory first exactly as
    ``desk_routes.py``/``desk_screen_compute.py`` already do). Deliberately NOT a
    ``desk_screen_log_dir`` ``Config`` field (see the module docstring) -- this keeps
    ``config_fingerprint()`` untouched this iteration."""
    override = os.environ.get(_SCREEN_LOG_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "screen_runs")


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum in this module hashes (stable across
    processes: sorted keys, no whitespace) -- the SAME encoding ``desk_topup_log.py``/
    ``desk_screen.py`` hash."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class ScreenRunStore:
    """File-based store rooted at the config-owned screen-run-log directory -- the ONE
    reader/writer. Mirrors ``desk_topup_log.TopupRunStore``/``desk_index_reconcile.ReconcileRunStore``
    load/checksum discipline exactly; like them, ``record`` performs no content-keyed dedup -- every
    call always persists a genuinely new file."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.json"

    def _load(self, path: Path) -> dict:
        """Load ONE run-record file, verifying its whole-record checksum. Raises
        ``ScreenRunIntegrityError`` for any parse/shape/checksum failure -- explicit, never
        silent."""
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise ScreenRunIntegrityError(
                f"screen run record file '{path.name}' is not parseable ({exc}) -- corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise ScreenRunIntegrityError(
                f"screen run record file '{path.name}' does not carry the expected record shape "
                f"-- corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise ScreenRunIntegrityError(
                f"screen run record file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise ScreenRunIntegrityError(
                f"screen run record file '{path.name}' does not carry the expected record shape "
                f"-- corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every registered run's full content (each file verified), oldest-started first, plus an
        EXPLICIT error row per file that failed verification -- a corrupt file is surfaced, never
        silently hidden and never served as data. A store whose directory was never created (no run
        has ever been recorded) returns ``([], [])`` -- the honest-empty case (DoD: "a run whose
        process ends before the writer's terminal call leaves NO record"). A fresh dict copy of
        every returned record's own ``skipped_by_reason`` (the ``desk_universe.UniverseStore.list``
        per-row-copy discipline), so a caller mutating a returned record can never poison a later
        read."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                meta = self._load(path)
                records.append({**meta, "skipped_by_reason": dict(meta["skipped_by_reason"])})
            except ScreenRunIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("started_utc", ""), meta.get("id", "")))
        return records, errors

    def record(
        self,
        *,
        screen_date: str,
        universe_snapshot_id: str | None,
        config_fingerprint: str,
        bar_store_signature: str | None,
        started_utc: str,
        finished_utc: str,
        state: str,
        reused: bool,
        members_total: int,
        members_attempted: int,
        ranked_count: int,
        skipped_by_reason: dict,
        screen_id: str | None,
        error: str | None,
        failed_member: str | None,
    ) -> dict:
        """Persist ONE new screen-run record (record + register in a single explicit action) --
        ALWAYS a genuinely new file: no content-keyed dedup exists in this store (see the module
        docstring), so a second call with identical field values still appends a second, distinct
        record."""
        if state not in _TERMINAL_STATES:
            raise ValueError(
                f"invalid terminal state {state!r} -- must be one of {_TERMINAL_STATES}"
            )
        date = started_utc[:10]  # started_utc is always an ISO-8601 UTC string -- a YYYY-MM-DD prefix
        run_id = f"screenrun-{date}-{uuid.uuid4().hex[:12]}"
        # A path collision is astronomically unlikely (a random 12-hex-char suffix), but this store
        # never silently overwrites an existing file regardless of cause -- mirrors
        # TopupRunStore.record's/ReconcileRunStore.record's identical defensive re-roll instead of a
        # blind write.
        while self._path(run_id).exists():
            run_id = f"screenrun-{date}-{uuid.uuid4().hex[:12]}"
        meta = {
            "id": run_id,
            "screen_date": screen_date,
            "universe_snapshot_id": universe_snapshot_id,
            "config_fingerprint": config_fingerprint,
            "bar_store_signature": bar_store_signature,
            "started_utc": started_utc,
            "finished_utc": finished_utc,
            "state": state,
            "reused": reused,
            "members_total": members_total,
            "members_attempted": members_attempted,
            "ranked_count": ranked_count,
            "skipped_by_reason": dict(skipped_by_reason),
            "screen_id": screen_id,
            "error": error,
            "failed_member": failed_member,
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(run_id).write_text(json.dumps(payload))
        return dict(meta)


def record_screen_run(
    store: ScreenRunStore,
    *,
    screen_date: str,
    universe_snapshot_id: str | None,
    config_fingerprint: str,
    bar_store_signature: str | None,
    started_utc: str,
    finished_utc: str,
    state: str,
    reused: bool,
    members_total: int,
    members_attempted: int,
    ranked_count: int,
    skipped_by_reason: dict,
    screen_id: str | None,
    error: str | None,
    failed_member: str | None,
) -> dict:
    """THE single shared writer (goal.md J-18 step 3) -- called exactly once, at a run's terminal
    state, from inside ``run_screen_and_record`` (``desk_screen_compute.py``) -- the ONE shared
    entry point both ``DeskScreenComputeManager``'s resolve path and the CLI's ``main()`` already
    call -- and nothing else. A thin, explicit free function over ``ScreenRunStore.record`` (rather
    than the call site invoking the method directly) so a future reader grepping for
    ``record_screen_run`` finds the one call site -- the ``desk_topup_log.record_topup_run``/
    ``desk_index_reconcile.record_reconcile_run`` precedent."""
    return store.record(
        screen_date=screen_date,
        universe_snapshot_id=universe_snapshot_id,
        config_fingerprint=config_fingerprint,
        bar_store_signature=bar_store_signature,
        started_utc=started_utc,
        finished_utc=finished_utc,
        state=state,
        reused=reused,
        members_total=members_total,
        members_attempted=members_attempted,
        ranked_count=ranked_count,
        skipped_by_reason=skipped_by_reason,
        screen_id=screen_id,
        error=error,
        failed_member=failed_member,
    )
