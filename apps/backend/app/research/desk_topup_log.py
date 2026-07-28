"""Top-up run log (Era B "The Desk", J-09) — an append-only, checksummed record of what every desk
bar top-up run attempted, surviving past the next run superseding
``DeskTopupComputeManager``'s in-flight/last-terminal snapshot (``desk_topup_compute.py``'s job
state is explicitly process-scoped and "honestly lost on restart" — this module is the durable
counterpart the goal.md J-09 journey adds beside it).

THIS module computes NOTHING about bars, coverage, or per-pair outcomes itself — it is a pure
PERSISTENCE lens over what ``run_topup`` (``desk_topup_compute.py:158``) already returns. A run
record is written EXACTLY ONCE, at the run's terminal state, by the single shared writer
(``record_topup_run`` below) — called from both ``DeskTopupComputeManager``'s worker resolve path
and the CLI's ``main()`` (``desk_topup_compute.py``), and nowhere else.

**Mirrors ``desk_universe.UniverseStore`` / ``desk_screen.ScreenStore``'s discipline** — a
checksum-verified load on every read (``TopupRunIntegrityError`` on any mismatch, never silence,
never a fabricated record), ``record()`` the only mutation, no update/delete function anywhere
(immutability is structural, not policed). **UNLIKE those two stores, this one performs NO
content-based deduplication**: every terminal run is its own genuinely distinct event — even an
all-"reused" run over an unchanged store is a real, separate attempt with its own
``started_utc``/``finished_utc`` — so ``record()`` always writes a brand-new file; there is no
"already recorded" refusal concept here, and no key a caller could collide against.

**Interrupted-run honesty (a DoD clause, structural by construction).** A run whose PROCESS ends
before this module's writer is ever called (a crash, ``kill -9``, a power loss) leaves NO record —
there is no "pending" or "partial" file ever written, because ``record()`` is the ONLY write path
in this module and it is called exactly once, at the very end of a run's lifecycle, never earlier
and never speculatively. This is proven by the store's own natural behavior: a store that is never
told to ``record()`` holds zero files, full stop.

**Storage dir — no new ``Config`` field.** ``resolve_desk_topup_log_dir`` mirrors
``desk_screen.resolve_desk_screen_dir`` exactly: a bare ``TAPEOLOGY_DESK_TOPUP_LOG_DIR`` env-var
override, else a directory co-located as a SIBLING of the caller's own already-resolved universe
directory (the ``edge_report_cache.resolve_cache_db_path`` pattern) — an operational storage-
location knob, never a value that shapes a served result, so ``config_fingerprint()`` stays
untouched (the Constraints' own explicit sanction for "worker counts, timeouts, store dirs").

**Records ATTEMPTS only.** Bar coverage/freshness keeps its existing single owner
(``desk_coverage.py`` over ``bar_index``) — this module creates no second coverage path anywhere;
it never reads a ``BarStore`` or ``BarIndex`` at all.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path

__all__ = [
    "TopupRunIntegrityError",
    "TopupRunStore",
    "record_topup_run",
    "resolve_desk_topup_log_dir",
]

# The store's own env-var override (the ``TAPEOLOGY_DESK_SCREEN_DIR``/``TAPEOLOGY_DESK_UNIVERSE_DIR``
# pattern) — see ``resolve_desk_topup_log_dir``.
_TOPUP_LOG_DIR_ENV = "TAPEOLOGY_DESK_TOPUP_LOG_DIR"

# The three terminal states a run record may carry — never "running" (a record is written once, at
# terminal state only; see the module docstring's "interrupted-run honesty" section).
_TERMINAL_STATES = ("done", "cancelled", "failed")


class TopupRunIntegrityError(Exception):
    """An on-disk run-record file failed its checksum verification on load — corrupted or
    tampered, surfaced explicitly (never silence, never a fabricated record)."""


def resolve_desk_topup_log_dir(desk_universe_dir_resolved: str) -> str:
    """The top-up run log's directory: the ``TAPEOLOGY_DESK_TOPUP_LOG_DIR`` env var if set, else a
    directory co-located as a SIBLING of the CALLER's own already-resolved universe directory (the
    ``desk_screen.resolve_desk_screen_dir`` pattern verbatim — takes a plain string, never imports
    ``config.py``'s singleton, so the caller resolves its own universe directory first exactly as
    ``desk_routes.py``/``desk_topup_compute.py`` already do). Deliberately NOT a
    ``desk_topup_log_dir`` ``Config`` field (see the module docstring) — this keeps
    ``config_fingerprint()`` untouched this iteration."""
    override = os.environ.get(_TOPUP_LOG_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "topup_runs")


def _canonical(obj: object) -> bytes:
    """The one canonical JSON encoding every checksum in this module hashes (stable across
    processes: sorted keys, no whitespace) — the SAME encoding ``desk_universe.py``/
    ``desk_screen.py`` hash."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


class TopupRunStore:
    """File-based store rooted at the config-owned top-up-log directory — the ONE reader/writer.
    Mirrors ``desk_universe.UniverseStore``/``desk_screen.ScreenStore``'s load/checksum discipline
    exactly; unlike them, ``record`` performs no content-keyed dedup (see the module docstring) —
    every call always persists a genuinely new file."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.json"

    def _load(self, path: Path) -> dict:
        """Load ONE run-record file, verifying its whole-record checksum. Raises
        ``TopupRunIntegrityError`` for any parse/shape/checksum failure — explicit, never silent."""
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise TopupRunIntegrityError(
                f"top-up run record file '{path.name}' is not parseable ({exc}) -- corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise TopupRunIntegrityError(
                f"top-up run record file '{path.name}' does not carry the expected record shape "
                f"-- corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise TopupRunIntegrityError(
                f"top-up run record file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise TopupRunIntegrityError(
                f"top-up run record file '{path.name}' does not carry the expected record shape "
                f"-- corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every registered run's full content (each file verified), oldest-started first, plus an
        EXPLICIT error row per file that failed verification — a corrupt file is surfaced, never
        silently hidden and never served as data. A store whose directory was never created (no run
        has ever been recorded) returns ``([], [])`` — the honest-empty case (DoD: "a run whose
        process ends before the writer's terminal call leaves NO record"). Fresh copies of the
        nested ``outcomes`` list on every call (the ``desk_universe.UniverseStore.list``
        per-row-copy discipline), so a caller mutating a returned record can never poison a later
        read."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                meta = self._load(path)
                records.append({**meta, "outcomes": [dict(o) for o in meta["outcomes"]]})
            except TopupRunIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("started_utc", ""), meta.get("id", "")))
        return records, errors

    def record(
        self,
        *,
        universe_snapshot_id: str | None,
        requested_window: dict,
        config_fingerprint: str,
        started_utc: str,
        finished_utc: str,
        state: str,
        pairs_total: int,
        outcomes: list[dict],
    ) -> dict:
        """Persist ONE new top-up run record (record + register in a single explicit action) —
        ALWAYS a genuinely new file: no content-keyed dedup exists in this store (see the module
        docstring), so a second call with identical field values still appends a second, distinct
        record. ``pairs_attempted`` is derived HERE from ``len(outcomes)`` — never a separately
        tracked counter (the plan's own trap #4)."""
        if state not in _TERMINAL_STATES:
            raise ValueError(
                f"invalid terminal state {state!r} -- must be one of {_TERMINAL_STATES}"
            )
        date = started_utc[:10]  # started_utc is always an ISO-8601 UTC string -- a YYYY-MM-DD prefix
        run_id = f"topup-{date}-{uuid.uuid4().hex[:12]}"
        # A path collision is astronomically unlikely (a random 12-hex-char suffix), but this store
        # never silently overwrites an existing file regardless of cause -- mirrors
        # UniverseStore.record's/ScreenStore.record's identical defensive re-roll instead of a
        # blind write.
        while self._path(run_id).exists():
            run_id = f"topup-{date}-{uuid.uuid4().hex[:12]}"
        meta = {
            "id": run_id,
            "universe_snapshot_id": universe_snapshot_id,
            "requested_window": dict(requested_window),
            "config_fingerprint": config_fingerprint,
            "started_utc": started_utc,
            "finished_utc": finished_utc,
            "state": state,
            "pairs_total": pairs_total,
            "pairs_attempted": len(outcomes),
            "outcomes": [dict(o) for o in outcomes],
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(run_id).write_text(json.dumps(payload))
        return dict(meta)


def record_topup_run(
    store: TopupRunStore,
    *,
    universe_snapshot_id: str | None,
    requested_window: dict,
    config_fingerprint: str,
    started_utc: str,
    finished_utc: str,
    state: str,
    pairs_total: int,
    outcomes: list[dict],
) -> dict:
    """THE single shared writer (goal.md J-09 step 1 / this iteration's plan) — called exactly
    once, at a run's terminal state, by BOTH ``DeskTopupComputeManager``'s worker resolve path and
    the CLI's ``main()`` (``desk_topup_compute.py``), and nothing else. A thin, explicit free
    function over ``TopupRunStore.record`` (rather than each call site invoking the method
    directly) so both call sites import and call the exact SAME symbol — a future reader grepping
    for ``record_topup_run`` finds both, and only, call sites; there is no second write path and no
    second outcome shape anywhere in this codebase."""
    return store.record(
        universe_snapshot_id=universe_snapshot_id,
        requested_window=requested_window,
        config_fingerprint=config_fingerprint,
        started_utc=started_utc,
        finished_utc=finished_utc,
        state=state,
        pairs_total=pairs_total,
        outcomes=outcomes,
    )
