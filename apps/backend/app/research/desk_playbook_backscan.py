"""The playbook back-scan (Era B2, J-07) -- one resumable, cancel-safe operator act that walks a
date range through the ONE existing shared ``run_playbook_and_record`` entry point
(``desk_playbook_compute.py:90``), so the playbook's own store fills in for every recorded session
instead of one date at a time via the existing Run Playbook control.

**Three concepts, one module (mirrors ``desk_deep_backfill.py``'s plan/walker/manager/ledger
quartet, re-chunked to one calendar day instead of one bar-window chunk):**

  * ``plan_backscan`` -- a PURE, metadata-only preview: every calendar day in ``[from_day, to_day]``
    classified ``recorded_at_current_signature`` (a playbook record already exists at THIS EXACT
    ``(day, playbook_input_signature)`` key) or ``missing_at_current_signature`` (it does not).
  * ``run_backscan`` -- the SOLE walker; the manager's worker thread and nothing else calls it. Per
    date it calls ``run_playbook_and_record`` (never a second implementation of detect+measure+
    record) and classifies the honest outcome -- ``reused`` / ``recorded`` / ``refused_non_session``
    / ``failed`` -- never aborting the whole walk on one date's failure. Cancel is cooperative,
    observed on a date boundary (a date already in flight finishes and is recorded -- it has already
    paid for its walk).
  * ``DeskPlaybookBackscanComputeManager`` + ``BackscanRunStore`` -- the single-flight, cancellable,
    progress-publishing job (the ``DeskPlaybookComputeManager``/``DeskDeepBackfillComputeManager``
    shape verbatim) and its durable, terminal-state-only run ledger.

**Why the plan walks EVERY calendar day, never ``desk_sessions.recorded_session_dates``.** That
function calls ``BarStore.merged_bars`` (real bar CONTENT reads, bounded to
``DESK_SESSION_ANCHOR_LIMIT`` members but still real reads) to prove session-ness -- exactly the
cost this plan promises never to pay (T-7: "the plan GET is metadata-only"). ``plan_backscan``
therefore does not try to know in advance which calendar days are genuine trading sessions at all;
it resolves ONE ``playbook_input_signature`` (``compute_playbook_input_signature`` -- itself
``list(include_bars=False)``-only, so ``BarStore`` is touched for record METADATA and never for bar
content) and then answers, for every calendar day in range, "does the playbook store already hold a
record at this exact key" -- a pure ``PlaybookStore`` file lookup, zero ``BarStore`` content reads.
Whether a "missing" day is a genuine trading session that has simply never been walked, or a
weekend/holiday that never will be, is not this GET's question to answer -- ``run_backscan``'s own
per-date call into ``run_playbook_and_record`` (which DOES call ``desk_sessions.
refuse_if_not_a_session``) is the one and only place that gets decided, and ``refused_non_session``
exists in the outcome vocabulary precisely because the plan does not pre-filter it away.

**Cancellation, and why it differs from the single-date playbook run log.**
``desk_playbook_log.PlaybookRunStore`` treats a cancelled run as though it never happened (no ledger
row at all) because a SINGLE-date compute that is cancelled mid-walk records nothing -- there is no
partial progress to disclose. A back-scan is different: it is N independent per-date attempts, so a
cancel after some dates have already completed genuinely measured something worth keeping (TC-5).
But a cancel BEFORE any date completes is, again, indistinguishable from a run that never started
(TC-10) -- so this module's ``BackscanRunStore`` writes a ``"cancelled"`` row only when
``completed >= 1``; ``"done"``/``"error"`` always write, mirroring
``desk_deep_backfill.DeepBackfillRunStore``'s three-terminal-state set exactly (never a fourth
``"cancelled-with-nothing"`` state -- it is simply not logged).

**Host-guard confinement (T-12).** The walk runs sequentially on ONE background worker thread inside
the already-running server process -- no new process, no worker pool -- so it automatically inherits
the process's own CPU affinity mask exactly the way ``desk_screen.py``'s bounded worker pool already
documents for its own children. There is nothing here for a host-guard wrapper to confine beyond
what already confines the whole process.

**No second implementation of the measurement rail, no second implementation of session honesty.**
Every date is walked through ``run_playbook_and_record`` verbatim; this module detects nothing,
measures nothing, and re-derives no threshold -- see that function's own docstring for the
detect/measure/record contract this module only orchestrates across a range.

**Storage dirs -- no new ``Config`` field.** ``resolve_desk_playbook_backscan_log_dir`` mirrors
``resolve_desk_playbook_log_dir``/``resolve_desk_deep_backfill_log_dir`` exactly: a bare
``TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR`` env-var override, else a directory co-located as a
SIBLING of the caller's own already-resolved universe directory."""

from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from .bars import BarStore
from .desk_playbook import (
    PlaybookSessionRefused,
    PlaybookStore,
    compute_playbook_input_signature,
)
from .desk_playbook_compute import run_playbook_and_record
from .desk_universe import UniverseStore

__all__ = [
    "BackscanRunIntegrityError",
    "BackscanRunStore",
    "DeskPlaybookBackscanComputeManager",
    "PlaybookNotScopedError",
    "malformed_days",
    "plan_backscan",
    "record_backscan_run",
    "resolve_desk_playbook_backscan_log_dir",
    "run_backscan",
]

# The back-scan run log's own env-var override (the ``TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR`` pattern).
_BACKSCAN_LOG_DIR_ENV = "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR"

# The COMPLETE terminal-state set a ledger row may ever be written under -- mirrors
# ``DeepBackfillRunStore``'s own three-state set (never a fourth "cancelled-with-nothing" state;
# see the module docstring's cancellation section for when "cancelled" is skipped entirely).
_TERMINAL_STATES = ("done", "cancelled", "error")

# The COMPLETE per-date outcome vocabulary -- matches the Data Contract's own ``outcomes`` keys
# exactly (never a fifth value).
_OUTCOME_KEYS = ("reused", "recorded", "refused_non_session", "failed")

# TC-13's positive scoping guard: the FIVE env vars every playbook/back-scan test or browser-QA rig
# must scope together (the session ledger's own lesson -- reading a raw ``config.*_dir`` field or
# scoping the store dir without its log-dir siblings silently orphans writes into the real store).
# goal-playbook-iter-12 (J-11 passenger): ``TAPEOLOGY_BAR_INDEX_DB`` joins the other four -- the
# derived bar-lookup index (``routes.py.get_bar_index``) lives under ``.data/`` by default too, so a
# rig that scopes every OTHER store but leaves this one ambient would still touch the real
# ``bar_index.db`` on any compute path that reads it. Every real scoped-rig launcher already exports
# it (``qa_playbook_iter7_fixture_scoped_backend.sh`` and its siblings); this closes the gap between
# what those scripts already DO and what this guard actually CHECKS.
_SCOPING_ENV_VARS = (
    "TAPEOLOGY_DESK_PLAYBOOK_DIR",
    "TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR",
    "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR",
    "TAPEOLOGY_DESK_UNIVERSE_DIR",
    "TAPEOLOGY_BAR_INDEX_DB",
)


class PlaybookNotScopedError(Exception):
    """Raised by ``_assert_scoped`` -- a test/browser-QA rig's environment does not carve out a
    dedicated, scoped root for every playbook/back-scan store directory."""


class BackscanRunIntegrityError(Exception):
    """An on-disk back-scan run-record file failed its checksum verification on load -- corrupted
    or tampered, surfaced explicitly (never silence, never a fabricated record)."""


def resolve_desk_playbook_backscan_log_dir(desk_universe_dir_resolved: str) -> str:
    """The back-scan run log's directory: the ``TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR`` env var
    if set, else a ``playbook_backscan_runs`` SIBLING of the caller's own already-resolved universe
    directory -- the ``resolve_desk_playbook_log_dir`` pattern verbatim. Deliberately NOT a
    ``Config`` field (an operational storage-location knob, never a value that shapes a served
    result -- ``config_fingerprint()`` stays untouched)."""
    override = os.environ.get(_BACKSCAN_LOG_DIR_ENV)
    if override:
        return override
    return os.path.join(os.path.dirname(desk_universe_dir_resolved), "playbook_backscan_runs")


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _empty_outcomes() -> dict:
    return {key: 0 for key in _OUTCOME_KEYS}


# --- TC-13: the positive scoping guard ------------------------------------------------------------


def _assert_scoped(root: str | Path) -> None:
    """A TEST/BROWSER-QA-LANE-ONLY positive guard -- NEVER called from the live HTTP routes below.
    An operator's REAL compute legitimately runs with none of the five ``_SCOPING_ENV_VARS`` set,
    resolving to the ambient ``.data/`` store; wiring this into the route would wrongly refuse every
    genuine production compute. Instead, a test fixture or browser-QA rig calls this BEFORE
    triggering any playbook or back-scan compute against a scoped root, so a scoping mistake is
    refused loudly, in the rig itself, before it ever reaches ``run_playbook_and_record``.

    Raises ``PlaybookNotScopedError`` unless EVERY one of the five scoping env vars is set AND
    resolves to a path rooted under ``root`` and outside any ``.data/`` directory. Mirrors
    ``scripts/seed_playbook_fixture_rig.py``'s own ``_assert_scoped`` helper (that script's own,
    narrower three-directory version predates this one and is left as-is); this module's version is
    the one both this iteration's extended fixture script and the dedicated TC-13 unit test call, so
    the exact rule under test is exercised directly rather than re-derived."""
    root_resolved = Path(root).resolve()
    problems: list[str] = []
    for name in _SCOPING_ENV_VARS:
        value = os.environ.get(name)
        if not value:
            problems.append(f"{name} is unset -- resolves to the ambient default store")
            continue
        path = Path(value).resolve()
        if ".data" in path.parts:
            problems.append(f"{name}={path} is inside a .data/ store")
        elif root_resolved not in path.parents and path != root_resolved:
            problems.append(f"{name}={path} is outside the scoped root {root_resolved}")
    if problems:
        raise PlaybookNotScopedError(
            "playbook/back-scan compute REFUSED -- store directories are not scoped:\n  "
            + "\n  ".join(problems)
            + "\nExport TAPEOLOGY_DESK_PLAYBOOK_DIR / TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR / "
              "TAPEOLOGY_DESK_PLAYBOOK_BACKSCAN_LOG_DIR / TAPEOLOGY_DESK_UNIVERSE_DIR / "
              "TAPEOLOGY_BAR_INDEX_DB (all five) at the scoped root first."
        )


# --- the plan (pure, metadata-only) ----------------------------------------------------------------


def _is_calendar_day(value: str) -> bool:
    """Whether ``value`` parses as a real ``yyyy-MM-dd`` calendar day -- the ONE parse rule both the
    tolerant plan read (``_planned_dates``) and the trigger's own refusal (``malformed_days``)
    share, so "what counts as a real date" is never defined a second way."""
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def malformed_days(from_day: str, to_day: str) -> list[str]:
    """Which of the two boundary strings is NOT a parseable calendar day -- ``[]`` when both are.

    The WRITE-side companion to ``_planned_dates``' read-side tolerance (goal-playbook-iter-8 audit,
    B1). Reading a plan for a half-typed date is an honest empty plan; STARTING a back-scan over one
    is not the same act: a job planned from an uninterpretable string walks zero dates and then
    finalizes ``"done"``, appending a permanently un-prunable ledger row that claims a completed run
    over a range nothing could parse. An INVERTED range is deliberately NOT malformed -- both of its
    boundaries are real days, it simply names an empty span (TC-17), and that stays a legitimate,
    honestly-empty walk."""
    return [value for value in (from_day, to_day) if not _is_calendar_day(value)]


def _planned_dates(from_day: str, to_day: str) -> list[str]:
    """Every calendar day in ``[from_day, to_day]`` inclusive, ``yyyy-MM-dd`` ascending -- pure date
    arithmetic, no store touched at all (the ``plan_deep_windows`` precedent). An inverted range
    (``from_day > to_day``) is an honest empty list, never an error (TC-17). A malformed/partial
    date (e.g. a half-typed ``2026-06-2``, mid-keystroke in the Backscan panel's own From/To boxes)
    is the SAME honest empty list rather than a raised ``ValueError`` -- T-5 ("fail closed, disclose
    the absence") is the governing rail here, since a not-yet-a-real-date string describes no
    calendar range at all, exactly like an inverted one (iter-8's own carried defect fix: this used
    to propagate the ``ValueError`` straight into an HTTP 500 at the route). NOTE this tolerance is
    a READ-side rule only: the TRIGGER route refuses a malformed boundary outright (see
    ``malformed_days``) rather than starting a phantom zero-date job over a string nothing could
    interpret."""
    if not _is_calendar_day(from_day) or not _is_calendar_day(to_day):
        return []
    start = date.fromisoformat(from_day)
    end = date.fromisoformat(to_day)
    if start > end:
        return []
    dates: list[str] = []
    cursor = start
    while cursor <= end:
        dates.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return dates


def plan_backscan(
    from_day: str,
    to_day: str,
    bar_store: BarStore,
    members: list[str],
    config_fingerprint: str,
    playbook_store: PlaybookStore,
) -> dict:
    """What a back-scan over ``[from_day, to_day]`` would find, said before anything is clicked --
    PURE and metadata-only (TC-9): ONE ``playbook_input_signature`` resolution
    (``compute_playbook_input_signature`` -- ``list(include_bars=False)``-only, so this never reads
    a single bar's CONTENT) plus a ``PlaybookStore`` file-stat lookup per calendar day. Every day in
    range is classified ``"recorded_at_current_signature"`` (a record already exists at this exact
    ``(day, signature)`` key) or ``"missing_at_current_signature"`` (it does not) -- see the module
    docstring for why this never tries to pre-classify which days are genuine trading sessions.

    Shape:: {"from", "to", "playbook_input_signature", "dates": [{"session_date", "status"}, ...],
    "total", "missing"}."""
    signature = compute_playbook_input_signature(bar_store, members, config_fingerprint)
    dates: list[dict] = []
    missing = 0
    for day in _planned_dates(from_day, to_day):
        recorded = playbook_store.find_by_key(day, signature) is not None
        status = "recorded_at_current_signature" if recorded else "missing_at_current_signature"
        if not recorded:
            missing += 1
        dates.append({"session_date": day, "status": status})
    return {
        "from": from_day,
        "to": to_day,
        "playbook_input_signature": signature,
        "dates": dates,
        "total": len(dates),
        "missing": missing,
    }


# --- the shared walker -------------------------------------------------------------------------------


def run_backscan(
    planned_dates: list[str],
    universe_store: UniverseStore,
    bar_store: BarStore,
    config,
    playbook_store: PlaybookStore,
    *,
    progress: Callable[[dict], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> list[dict]:
    """Walk ``planned_dates`` in order, calling ``run_playbook_and_record`` for EACH -- the SOLE
    walker; the manager and nothing else calls this (the ``run_deep_backfill`` precedent). Returns
    the per-date outcome dicts in walk order: ``{"session_date", "outcome", "detail"}``, where
    ``outcome`` is one of ``reused`` / ``recorded`` / ``refused_non_session`` / ``failed`` -- the
    COMPLETE vocabulary, never a fifth value.

    A per-date failure (a refusal or any other exception) is classified and the walk CONTINUES to
    the remaining dates -- one bad date never aborts the whole back-scan (the ``run_deep_backfill``
    per-chunk catch-and-continue precedent). ``progress``, if given, is called after EACH date with
    the entry just appended. ``should_abort``, if given and true BEFORE a date starts, stops the walk
    early (cooperative -- a date already in flight finishes and is recorded; the returned list is
    simply shorter than ``len(planned_dates)``)."""
    outcomes: list[dict] = []
    for session_date in planned_dates:
        if should_abort is not None and should_abort():
            return outcomes
        try:
            _record, reused = run_playbook_and_record(
                universe_store, bar_store, config, playbook_store, session_date,
            )
        except PlaybookSessionRefused as exc:
            entry = {"session_date": session_date, "outcome": "refused_non_session", "detail": str(exc)}
        except Exception as exc:  # noqa: BLE001 -- classified per-date; the walk continues
            entry = {"session_date": session_date, "outcome": "failed", "detail": str(exc)}
        else:
            entry = {
                "session_date": session_date,
                "outcome": "reused" if reused else "recorded",
                "detail": None,
            }
        outcomes.append(entry)
        if progress is not None:
            progress(entry)
    return outcomes


# --- the durable run ledger --------------------------------------------------------------------------


class BackscanRunStore:
    """File-based store rooted at the back-scan run-log directory -- the ONE reader/writer. Mirrors
    ``DeepBackfillRunStore``'s discipline: checksum-verified load on every read, ``record()`` the
    only mutation, no update/delete anywhere, and NO content-keyed dedup (every terminal run is a
    genuinely distinct event). See the module docstring's cancellation section for WHEN a
    ``"cancelled"`` state is written at all -- ``record()`` itself performs no such filtering; that
    decision is the caller's (``DeskPlaybookBackscanComputeManager``'s)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def _path(self, run_id: str) -> Path:
        return self._root / f"{run_id}.json"

    def _load(self, path: Path) -> dict:
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise BackscanRunIntegrityError(
                f"back-scan run record file '{path.name}' is not parseable ({exc}) -- corrupted or "
                f"tampered"
            ) from exc
        if not isinstance(data, dict) or "file_checksum" not in data or "record" not in data:
            raise BackscanRunIntegrityError(
                f"back-scan run record file '{path.name}' does not carry the expected record shape "
                f"-- corrupted or tampered"
            )
        record = data["record"]
        if _sha256(_canonical(record)) != data["file_checksum"]:
            raise BackscanRunIntegrityError(
                f"back-scan run record file '{path.name}' failed its integrity check (checksum "
                f"mismatch) -- the file was corrupted or tampered with"
            )
        meta = record.get("meta")
        if not isinstance(meta, dict):
            raise BackscanRunIntegrityError(
                f"back-scan run record file '{path.name}' does not carry the expected record shape "
                f"-- corrupted or tampered"
            )
        return meta

    def list(self) -> tuple[list[dict], list[dict]]:
        """Every registered run's full content (each file verified), oldest-started first, plus an
        EXPLICIT error row per file that failed verification. A directory that was never created
        (no run has ever reached a logged terminal state) returns ``([], [])`` -- the honest-empty
        case."""
        if not self._root.exists():
            return [], []
        records: list[dict] = []
        errors: list[dict] = []
        for path in sorted(self._root.glob("*.json")):
            try:
                records.append(dict(self._load(path)))
            except BackscanRunIntegrityError as exc:
                errors.append({"file": path.name, "error": str(exc)})
        records.sort(key=lambda meta: (meta.get("started_at", ""), meta.get("run_id", "")))
        return records, errors

    def record(
        self,
        *,
        from_day: str,
        to_day: str,
        config_fingerprint: str,
        started_at: str,
        finished_at: str,
        status: str,
        planned_total: int,
        outcomes: dict,
    ) -> dict:
        """Persist ONE new back-scan run record -- ALWAYS a genuinely new file: no content-keyed
        dedup exists in this store, so a second call with identical field values still appends a
        second, distinct record."""
        if status not in _TERMINAL_STATES:
            raise ValueError(f"invalid terminal status {status!r} -- must be one of {_TERMINAL_STATES}")
        run_date = started_at[:10]  # started_at is always an ISO-8601 UTC string
        run_id = f"backscanrun-{run_date}-{uuid.uuid4().hex[:12]}"
        while self._path(run_id).exists():
            run_id = f"backscanrun-{run_date}-{uuid.uuid4().hex[:12]}"
        meta = {
            "run_id": run_id,
            "from": from_day,
            "to": to_day,
            "config_fingerprint": config_fingerprint,
            "started_at": started_at,
            "finished_at": finished_at,
            "status": status,
            "planned_total": planned_total,
            "outcomes": dict(outcomes),
        }
        record = {"meta": meta}
        payload = {"file_checksum": _sha256(_canonical(record)), "record": record}
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(run_id).write_text(json.dumps(payload))
        return dict(meta)


def record_backscan_run(store: BackscanRunStore, **fields) -> dict:
    """THE single shared writer -- called AT MOST once per run, at its terminal state (module
    docstring's cancellation rule decides whether a ``"cancelled"`` terminal state is written at
    all), from inside ``DeskPlaybookBackscanComputeManager`` and nothing else."""
    return store.record(**fields)


# --- the compute manager -------------------------------------------------------------------------

_IDLE_SNAPSHOT: dict = {
    "id": None,
    "status": "idle",
    "from": None,
    "to": None,
    "planned_total": 0,
    "completed": 0,
    "outcomes": {"reused": 0, "recorded": 0, "refused_non_session": 0, "failed": 0},
    "current_date": None,
    "error": None,
}


def _copy_snapshot(snapshot: dict) -> dict:
    return {**snapshot, "outcomes": dict(snapshot["outcomes"])}


class DeskPlaybookBackscanComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) back-scan job -- the
    ``DeskPlaybookComputeManager``/``DeskDeepBackfillComputeManager`` shape verbatim: constructed
    with no arguments, every ``trigger()`` call takes its stores/config explicitly, single-flight,
    cancellable, progress-publishing, the walk runs on a dedicated worker thread so an HTTP route
    returns immediately, and cancel carries no distinct visible ``"cancelling"`` status (the
    ``DeskDeepBackfillComputeManager`` shape -- the Data Contract's own 5-state enum has no such
    state either)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict | None = None
        self._job_id: str | None = None
        self._cancel_event: threading.Event | None = None
        self._thread: threading.Thread | None = None

    def snapshot(self) -> dict:
        """The current/last job's snapshot, ALWAYS a real dict (never ``None``) -- ``status ==
        "idle"`` and ``id is None`` before any job has ever run this process. A caller-safe copy,
        never a shared mutable reference.

        2026-08-12: ``id`` is the job's own ephemeral, process-scoped uuid, published so an
        external waiter (the refresh chain's seventh step) can tell THIS job's terminal snapshot
        from a later job's -- the ``DeskScreenComputeManager``/``DeskForwardComputeManager`` shape
        those steps already wait on. It names no recorded value and reaches no store."""
        current = self._snapshot
        return _copy_snapshot(current) if current is not None else dict(_IDLE_SNAPSHOT)

    def trigger(
        self,
        from_day: str,
        to_day: str,
        universe_store: UniverseStore,
        bar_store: BarStore,
        config,
        playbook_store: PlaybookStore,
        run_store: BackscanRunStore,
    ) -> dict:
        """Start a NEW back-scan job over ``[from_day, to_day]``, or -- if one is already
        ``"running"`` -- return it UNCHANGED (``started: False``, single-flight). Once the current
        job is terminal, the NEXT call always starts a genuinely new job (re-triggering the SAME
        range resumes: every already-recorded date short-circuits to ``"reused"`` inside
        ``run_playbook_and_record``, zero detector calls)."""
        with self._lock:
            current = self._snapshot
            if current is not None and current["status"] == "running":
                return {"started": False, "compute": _copy_snapshot(current)}

            planned = _planned_dates(from_day, to_day)
            job_id = uuid.uuid4().hex
            started_at = _iso_utc_now()
            cancel_event = threading.Event()
            self._cancel_event = cancel_event
            self._job_id = job_id
            snapshot = {
                "id": job_id,
                "status": "running",
                "from": from_day,
                "to": to_day,
                "planned_total": len(planned),
                "completed": 0,
                "outcomes": _empty_outcomes(),
                "current_date": None,
                "error": None,
            }
            self._snapshot = snapshot

        def _publish(entry: dict) -> None:
            with self._lock:
                if self._job_id != job_id:
                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
                current = self._snapshot
                if current is None:
                    return
                outcomes = dict(current["outcomes"])
                outcomes[entry["outcome"]] = outcomes.get(entry["outcome"], 0) + 1
                self._snapshot = {
                    **current,
                    "completed": current["completed"] + 1,
                    "outcomes": outcomes,
                    "current_date": entry["session_date"],
                }

        def _finalize(status: str, error: str | None) -> None:
            with self._lock:
                current = self._snapshot
                if current is None or self._job_id != job_id:
                    return  # superseded -- never resolve a job that is no longer the current one
                self._snapshot = {**current, "status": status, "error": error}
                completed = current["completed"]
                outcomes = dict(current["outcomes"])
            if status == "cancelled" and completed == 0:
                # A cancel that measured NOTHING leaves no trace -- indistinguishable from a run
                # that never started (TC-10; the module docstring's cancellation section).
                return
            record_backscan_run(
                run_store,
                from_day=from_day,
                to_day=to_day,
                config_fingerprint=config.config_fingerprint(),
                started_at=started_at,
                finished_at=_iso_utc_now(),
                status=status,
                planned_total=len(planned),
                outcomes=outcomes,
            )

        def _work() -> None:
            try:
                run_backscan(
                    planned, universe_store, bar_store, config, playbook_store,
                    progress=_publish, should_abort=cancel_event.is_set,
                )
            except Exception as exc:  # noqa: BLE001 -- a failure OUTSIDE any single date
                _finalize("error", str(exc))
                return
            _finalize("cancelled" if cancel_event.is_set() else "done", None)

        thread = threading.Thread(target=_work, name=f"desk-playbook-backscan:{job_id}", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return {"started": True, "compute": _copy_snapshot(snapshot)}

    def cancel(self) -> None:
        """Signal cooperative cancellation for the in-flight job -- a harmless no-op if idle (the
        ROUTE rejects an idle cancel with a 409). No distinct visible ``"cancelling"`` status is set
        here (the ``DeskDeepBackfillComputeManager`` shape) -- ``status`` stays ``"running"`` until
        the walk observes the cancel and the job resolves."""
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
