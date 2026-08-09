"""The forward run log (forward-test era) -- an append-only, checksummed record of what every desk
FORWARD compute run attempted, surviving past the next run superseding
``DeskForwardComputeManager``'s in-flight/last-terminal snapshot (``desk_forward_compute.py``'s job
state is explicitly process-scoped and honestly lost on restart). The durable counterpart that
module's own docstring named as missing -- "No run-log store in v1" -- mirroring the J-09
(``desk_topup_log.py``) / J-10 (``desk_index_reconcile.py``) / J-18 (``desk_screen_log.py``)
run-log discipline verbatim.

**Why it exists.** Without it, an absent forward record is AMBIGUOUS after a reload: a snapshot
with no measurement looks identical whether the compute never ran or ran and found nothing to
measure. On 2026-08-06 a refresh chain recorded 51 screens for 2025-01-01..2025-02-20 and then
produced zero forward records, and there was no way to tell from the product which of the two had
happened. ``rows_absent_no_fine_bars`` is the field that answers it: a run that measured a date
whose fine bars were never fetched records 98-of-100 absent rows, where a run that never happened
records nothing at all.

THIS module computes NOTHING about forward moves, touches, or horizons itself -- it is a pure
PERSISTENCE lens over what ``run_forward_and_record`` (``desk_forward_compute.py``) already
resolves. A run record is written EXACTLY ONCE, at the run's terminal state, by the single shared
writer (``record_forward_run`` below) -- called from inside ``run_forward_and_record`` itself (the
ONE shared entry point both ``DeskForwardComputeManager``'s worker and the CLI's ``main()`` already
call), and nowhere else.

**Records the RUN only -- zero diff to what a forward record itself records.**
``desk_forward.py``'s ``ForwardStore`` stays the sole owner of forward records/rows/touches/the
2-pin key; this module never reads or writes a forward record file, never re-derives a pin, and
never duplicates ``rows``/``summary`` content -- only their COUNTS, the same "attempt-level
summary, not content" split ``desk_screen_log.py`` draws.

**Mirrors ``ScreenRunStore``'s discipline byte-for-byte** -- a checksum-verified load on every read
(``ForwardRunIntegrityError`` on any mismatch, never silence, never a fabricated record),
``record()`` the only mutation, no update/delete function anywhere (immutability is structural, not
policed), and NO content-based deduplication: every terminal run is its own genuinely distinct
event -- even an all-``reused`` run over an unchanged store is a real, separate attempt with its own
``started_utc``/``finished_utc`` -- so ``record()`` always writes a brand-new file.

**Interrupted-run honesty (structural by construction).** A run whose PROCESS ends before this
module's writer is ever called (a crash, ``kill -9``, a power loss) leaves NO record -- there is no
"pending" or "partial" file ever written, because ``record()`` is the ONLY write path in this
module and it is called exactly once, at the very end of a run's lifecycle, never earlier and never
speculatively. A run the OPERATOR cancels does leave one (state ``"cancelled"``), because the walk
observed the cancel and returned rather than dying.

**Storage dir -- no new ``Config`` field.** ``resolve_desk_forward_log_dir`` mirrors
``resolve_desk_screen_log_dir`` exactly: a bare ``TAPEOLOGY_DESK_FORWARD_LOG_DIR`` env-var
override, else a directory co-located as a SIBLING of the caller's own already-resolved universe
directory -- an operational storage-location knob, never a value that shapes a served result, so
``config_fingerprint()`` stays untouched."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path

__all__ = [
    "ForwardRunIntegrityError",
    "ForwardRunStore",
    "record_forward_run",
    "resolve_desk_forward_log_dir",
]

# The store's own env-var override (the ``TAPEOLOGY_DESK_SCREEN_LOG_DIR`` pattern) -- see
# ``resolve_desk_forward_log_dir``.
_FORWARD_LOG_DIR_ENV = "TAPEOLOGY_DESK_FORWARD_LOG_DIR"

# The three terminal states a run record may carry -- never "running" (a record is written once, at
# terminal state only; see the module docstring's "interrupted-run honesty" section).
_TERMINAL_STATES = ("done", "cancelled", "failed")


class ForwardRunIntegrityError(Exception):
    """An on-disk run-record file failed its checksum verification on load -- corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated record)."""


def resolve_desk_forward_log_dir(desk_universe_dir_resolved: str) -> str:
    """The forward run log's directory: the ``TAPEOLOGY_DESK_FORWARD_LOG_DIR`` env var if set, else
    a directory co-located as a SIBLING of the CALLER's own already-resolved universe directory (the
    ``resolve_desk_screen_log_dir`` pattern verbatim -- takes a plain string, never imports
    ``config.py``'s singleton, so the caller resolves its own universe directory first exactly as
    ``desk_routes.py``/``desk_forward_compute.py`` already do). Deliberately NOT a
    ``desk_forward_log_dir`` ``Config`` field (see the module docstring) -- this keeps
    ``config_fingerprint()`` untouched."""
    override = os.environ.get(_FORWARD_LOG_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "forward_runs")


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum in this module hashes (stable across
    processes: sorted keys, no whitespace) -- the SAME encoding ``desk_screen_log.py``/
    ``desk_forward.py`` hash."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class ForwardRunStore:
    """File-based store rooted at the resolved forward-run-log directory -- the ONE reader/writer.
    Mirrors ``desk_screen_log.ScreenRunStore``'s load/checksum discipline exactly; like it,
    ``record`` performs no content-keyed dedup -- every call always persists a genuinely new
    file."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.json"

    def _load(self, path: Path) -> dict:
        """Load ONE run-record file, verifying its whole-record checksum. Raises
        ``ForwardRunIntegrityError`` for any parse/shape/checksum failure -- explicit, never
        silent."""
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise ForwardRunIntegrityError(
                f"forward run record file '{path.name}' is not parseable ({exc}) -- corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise ForwardRunIntegrityError(
                f"forward run record file '{path.name}' does not carry the expected record shape "
                f"-- corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise ForwardRunIntegrityError(
                f"forward run record file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise ForwardRunIntegrityError(
                f"forward run record file '{path.name}' does not carry the expected record shape "
                f"-- corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every registered run's full content (each file verified), oldest-started first, plus an
        EXPLICIT error row per file that failed verification -- a corrupt file is surfaced, never
        silently hidden and never served as data. A store whose directory was never created (no run
        has ever been recorded) returns ``([], [])`` -- the honest-empty case."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                records.append(dict(self._load(path)))
            except ForwardRunIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("started_utc", ""), meta.get("id", "")))
        return records, errors

    def list_for_screen(self, screen_id: str) -> list[dict]:
        """Every recorded run FOR one screen snapshot, oldest-started first -- the read the forward
        panel needs, since that panel describes exactly one snapshot at a time. A plain filter over
        ``list()``'s verified records (integrity errors stay excluded there, never re-surfaced as
        data here)."""
        records, _errors = self.list()
        return [record for record in records if record.get("screen_id") == screen_id]

    def record(
        self,
        *,
        screen_id: str,
        screen_date: str | None,
        config_fingerprint: str,
        forward_input_signature: str | None,
        started_utc: str,
        finished_utc: str,
        state: str,
        reused: bool,
        rows_total: int,
        rows_measured: int,
        rows_absent_no_fine_bars: int,
        rows_with_touches: int,
        total_touches: int,
        forward_id: str | None,
        error: str | None,
    ) -> dict:
        """Persist ONE new forward-run record (record + register in a single explicit action) --
        ALWAYS a genuinely new file: no content-keyed dedup exists in this store (see the module
        docstring), so a second call with identical field values still appends a second, distinct
        record.

        ``rows_absent_no_fine_bars`` is the count of ranked rows the walk could not measure because
        no 1m/5m bars are recorded for that session -- the field that distinguishes "this ran and
        found nothing" from "this never ran". A ``reused`` run reports the EXISTING record's own
        counts (the walk it short-circuited is the walk those counts came from), never zeroes."""
        if state not in _TERMINAL_STATES:
            raise ValueError(
                f"invalid terminal state {state!r} -- must be one of {_TERMINAL_STATES}"
            )
        date = started_utc[:10]  # started_utc is always an ISO-8601 UTC string -- a YYYY-MM-DD prefix
        run_id = f"forwardrun-{date}-{uuid.uuid4().hex[:12]}"
        # A path collision is astronomically unlikely (a random 12-hex-char suffix), but this store
        # never silently overwrites an existing file regardless of cause -- mirrors
        # ScreenRunStore.record's identical defensive re-roll instead of a blind write.
        while self._path(run_id).exists():
            run_id = f"forwardrun-{date}-{uuid.uuid4().hex[:12]}"
        meta = {
            "id": run_id,
            "screen_id": screen_id,
            "screen_date": screen_date,
            "config_fingerprint": config_fingerprint,
            "forward_input_signature": forward_input_signature,
            "started_utc": started_utc,
            "finished_utc": finished_utc,
            "state": state,
            "reused": reused,
            "rows_total": rows_total,
            "rows_measured": rows_measured,
            "rows_absent_no_fine_bars": rows_absent_no_fine_bars,
            "rows_with_touches": rows_with_touches,
            "total_touches": total_touches,
            "forward_id": forward_id,
            "error": error,
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(run_id).write_text(json.dumps(payload))
        return dict(meta)


def record_forward_run(
    store: ForwardRunStore,
    *,
    screen_id: str,
    screen_date: str | None,
    config_fingerprint: str,
    forward_input_signature: str | None,
    started_utc: str,
    finished_utc: str,
    state: str,
    reused: bool,
    rows_total: int,
    rows_measured: int,
    rows_absent_no_fine_bars: int,
    rows_with_touches: int,
    total_touches: int,
    forward_id: str | None,
    error: str | None,
) -> dict:
    """THE single shared writer -- called exactly once, at a run's terminal state, from inside
    ``run_forward_and_record`` (``desk_forward_compute.py``) -- the ONE shared entry point both
    ``DeskForwardComputeManager``'s worker and the CLI's ``main()`` already call -- and nothing
    else. A thin, explicit free function over ``ForwardRunStore.record`` (rather than the call site
    invoking the method directly) so a future reader grepping for ``record_forward_run`` finds the
    one call site -- the ``desk_screen_log.record_screen_run``/``desk_topup_log.record_topup_run``
    precedent."""
    return store.record(
        screen_id=screen_id,
        screen_date=screen_date,
        config_fingerprint=config_fingerprint,
        forward_input_signature=forward_input_signature,
        started_utc=started_utc,
        finished_utc=finished_utc,
        state=state,
        reused=reused,
        rows_total=rows_total,
        rows_measured=rows_measured,
        rows_absent_no_fine_bars=rows_absent_no_fine_bars,
        rows_with_touches=rows_with_touches,
        total_touches=total_touches,
        forward_id=forward_id,
        error=error,
    )
