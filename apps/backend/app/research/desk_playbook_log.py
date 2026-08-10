"""The playbook run log (Era B2, J-02) -- an append-only, checksummed record of what every desk
PLAYBOOK compute run attempted, surviving past the next run superseding
``DeskPlaybookComputeManager``'s in-flight/last-terminal snapshot (``desk_playbook_compute.py``'s
job state is process-scoped and honestly lost on restart, exactly like its forward-returns
sibling). Mirrors ``desk_forward_log.py``/``desk_topup_log.py``'s discipline: a checksum-verified
load on every read (``PlaybookRunIntegrityError`` on any mismatch, never silence, never a
fabricated record), ``record()`` the only mutation, no update/delete function anywhere, and NO
content-based deduplication -- every terminal run is its own genuinely distinct event.

**Terminal-state-only, and "terminal" EXCLUDES cancelled (the one deliberate divergence from
``desk_forward_log.py``, matching ``desk_topup_log.py``'s OBSERVED behaviour instead).** A run
whose PROCESS ends before this module's writer is ever called (a crash, ``kill -9``, a power loss)
leaves NO record -- there is no "pending"/"partial" file ever written, because ``record()`` is the
ONLY write path here and it is called at most once, at the very end of a run's lifecycle. An
OPERATOR-cancelled run leaves NO record EITHER: unlike the forward-returns ledger (which logs a
``"cancelled"`` state), ``run_playbook_and_record`` (``desk_playbook_compute.py``) simply never
calls this module's writer when the walk observed a cancel -- unmeasured, partial work is not a
reportable attempt outcome for the playbook, it is exactly as if the run had not happened. The four
``outcome`` values below (``recorded``/``reused``/``refused_non_session``/``failed``) are therefore
the COMPLETE terminal-state set; there is no fifth.

**Records the RUN only -- zero diff to what a playbook record itself records.**
``desk_playbook.py``'s ``PlaybookStore`` stays the sole owner of playbook records/signals/the 2-pin
key; this module never reads or writes a playbook record file, never re-derives a pin, and never
duplicates ``signals``/``absences``/``diagnostics`` content -- only a COUNT of what a successful
run measured, the same "attempt-level summary, not content" split every sibling run-log draws.

**Storage dir -- no new ``Config`` field.** ``resolve_desk_playbook_log_dir`` mirrors
``resolve_desk_forward_log_dir`` exactly: a bare ``TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`` env-var
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
    "PlaybookRunIntegrityError",
    "PlaybookRunStore",
    "record_playbook_run",
    "resolve_desk_playbook_log_dir",
]

# The store's own env-var override (the ``TAPEOLOGY_DESK_FORWARD_LOG_DIR`` pattern) -- see
# ``resolve_desk_playbook_log_dir``.
_PLAYBOOK_LOG_DIR_ENV = "TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR"

# The COMPLETE terminal-outcome set (the module docstring's "terminal excludes cancelled" rule) --
# matches the Data Contract's own ``outcome`` enum exactly. Never "cancelled": a cancelled run
# writes no row at all (the caller, ``run_playbook_and_record``, simply never calls ``record()``
# for one).
_TERMINAL_OUTCOMES = ("recorded", "reused", "refused_non_session", "failed")


class PlaybookRunIntegrityError(Exception):
    """An on-disk run-record file failed its checksum verification on load -- corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated record)."""


def resolve_desk_playbook_log_dir(desk_universe_dir_resolved: str) -> str:
    """The playbook run log's directory: the ``TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`` env var if set,
    else a directory co-located as a SIBLING of the CALLER's own already-resolved universe
    directory (the ``resolve_desk_forward_log_dir`` pattern verbatim). Deliberately NOT a
    ``desk_playbook_log_dir`` ``Config`` field (see the module docstring) -- this keeps
    ``config_fingerprint()`` untouched."""
    override = os.environ.get(_PLAYBOOK_LOG_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "playbook_runs")


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum in this module hashes (stable across
    processes: sorted keys, no whitespace) -- the SAME encoding ``desk_forward_log.py``/
    ``desk_playbook.py`` hash."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class PlaybookRunStore:
    """File-based store rooted at the resolved playbook-run-log directory -- the ONE
    reader/writer. Mirrors ``desk_forward_log.ForwardRunStore``'s load/checksum discipline exactly;
    like it, ``record`` performs no content-keyed dedup -- every call always persists a genuinely
    new file."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.json"

    def _load(self, path: Path) -> dict:
        """Load ONE run-record file, verifying its whole-record checksum. Raises
        ``PlaybookRunIntegrityError`` for any parse/shape/checksum failure -- explicit, never
        silent."""
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise PlaybookRunIntegrityError(
                f"playbook run record file '{path.name}' is not parseable ({exc}) -- corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise PlaybookRunIntegrityError(
                f"playbook run record file '{path.name}' does not carry the expected record shape "
                f"-- corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise PlaybookRunIntegrityError(
                f"playbook run record file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise PlaybookRunIntegrityError(
                f"playbook run record file '{path.name}' does not carry the expected record shape "
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
            except PlaybookRunIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("started_at", ""), meta.get("run_id", "")))
        return records, errors

    def list_for_session(self, session_date: str) -> list[dict]:
        """Every recorded run FOR one session date, oldest-started first -- a plain filter over
        ``list()``'s verified records (integrity errors stay excluded there, never re-surfaced as
        data here)."""
        records, _errors = self.list()
        return [record for record in records if record.get("session_date") == session_date]

    def record(
        self,
        *,
        session_date: str,
        config_fingerprint: str,
        playbook_input_signature: str | None,
        started_at: str,
        finished_at: str,
        outcome: str,
        signals_recorded: int,
        playbook_id: str | None,
        error: str | None,
    ) -> dict:
        """Persist ONE new playbook-run record (record + register in a single explicit action) --
        ALWAYS a genuinely new file: no content-keyed dedup exists in this store (see the module
        docstring), so a second call with identical field values still appends a second, distinct
        record.

        ``signals_recorded`` is the count of signals the resulting record HOLDS (its own recorded
        or already-recorded-and-reused count, never a partial-walk count -- a cancelled/interrupted
        run never reaches this call at all)."""
        if outcome not in _TERMINAL_OUTCOMES:
            raise ValueError(
                f"invalid terminal outcome {outcome!r} -- must be one of {_TERMINAL_OUTCOMES}"
            )
        date = started_at[:10]  # started_at is always an ISO-8601 UTC string -- a YYYY-MM-DD prefix
        run_id = f"playbookrun-{date}-{uuid.uuid4().hex[:12]}"
        # A path collision is astronomically unlikely (a random 12-hex-char suffix), but this store
        # never silently overwrites an existing file regardless of cause -- mirrors
        # ForwardRunStore.record's identical defensive re-roll instead of a blind write.
        while self._path(run_id).exists():
            run_id = f"playbookrun-{date}-{uuid.uuid4().hex[:12]}"
        meta = {
            "run_id": run_id,
            "session_date": session_date,
            "config_fingerprint": config_fingerprint,
            "playbook_input_signature": playbook_input_signature,
            "started_at": started_at,
            "finished_at": finished_at,
            "outcome": outcome,
            "signals_recorded": signals_recorded,
            "playbook_id": playbook_id,
            "error": error,
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(run_id).write_text(json.dumps(payload))
        return dict(meta)


def record_playbook_run(
    store: PlaybookRunStore,
    *,
    session_date: str,
    config_fingerprint: str,
    playbook_input_signature: str | None,
    started_at: str,
    finished_at: str,
    outcome: str,
    signals_recorded: int,
    playbook_id: str | None,
    error: str | None,
) -> dict:
    """THE single shared writer -- called AT MOST once per run, at a run's terminal state (and
    never at all for a cancel -- see the module docstring), from inside ``run_playbook_and_record``
    (``desk_playbook_compute.py``) -- the ONE shared entry point both
    ``DeskPlaybookComputeManager``'s worker and the CLI's ``main()`` call -- and nothing else. A
    thin, explicit free function over ``PlaybookRunStore.record`` (rather than the call site
    invoking the method directly) so a future reader grepping for ``record_playbook_run`` finds the
    one call site (the ``record_forward_run``/``record_topup_run`` precedent)."""
    return store.record(
        session_date=session_date,
        config_fingerprint=config_fingerprint,
        playbook_input_signature=playbook_input_signature,
        started_at=started_at,
        finished_at=finished_at,
        outcome=outcome,
        signals_recorded=signals_recorded,
        playbook_id=playbook_id,
        error=error,
    )
