"""``micro_snapshots.py`` -- Era "The Rapid Microscope" J-02: snapshot identity + load-time

verification (``docs/rapid-validation-spec.md`` section 2.3), persistence, the single-flight
compute manager + CLI (the shipped desk pattern: ``desk_forward_compute.py`` /
``desk_playbook_compute.py`` -- one in-flight job slot, an in-memory progress snapshot, cooperative
cancel, no new pattern invented), and the section 2.4 granularity-benchmark helpers.

**Storage shape.** One snapshot = two sibling files under the resolved snapshots directory: a
row-oriented ``<dataset_id>.jsonl`` (one ``micro_observer.MicroObserver`` row per line -- JSONL,
not one giant JSON array, so a build WRITES streaming and a future reader can iterate without
loading the whole file) and a small ``<dataset_id>.meta.json`` sidecar (the identity tuple +
``row_count``/``bytes_on_disk``/``built_utc``/``quote_size_unit`` -- exactly what
``GET /research/desk/micro/snapshots`` serves; the boundary note in the iteration spec is explicit
that this route serves BUILD METADATA only, never raw per-event rows -- an origin-fenced,
event-level reader is ``micro_accessor.py``'s exclusive door, J-05, not built here).

**Derived, rebuildable, owns nothing** (spec section 2.3) -- exactly the ``dataset_index.py`` /
``tradability_cache.py`` discipline applied to a bigger artifact: losing every snapshot file loses
nothing irreplaceable, the next build reproduces it byte-identically from the immutable dataset +
the frozen algorithm. There is therefore no tamper checksum ON the meta file itself (unlike
``datasets.py``'s own irreplaceable recordings) -- staleness is instead caught by RE-VERIFYING the
three identity components spec section 2.3 names (``dataset_checksum``, ``config_fingerprint``,
``feature_source_hash``) against a FRESH computation on every load; any mismatch is an honest
cache MISS (rebuild), never a served stale value (TR-7)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from ..config import CONFIG, Config
from . import micro_features as mf
from . import micro_observer as mo
from . import vault
from .datasets import DatasetNotFound, DatasetStore
from .micro_observer import MicroObserver, MicroObserverFailure

__all__ = [
    "SNAPSHOT_FORMAT_VERSION",
    "MicroSnapshotIntegrityError",
    "MicroObserverFailure",
    "withheld_dataset_ids_for_store",
    "exclude_withheld",
    "resolve_micro_snapshots_dir",
    "feature_source_hash",
    "snapshot_identity",
    "quote_size_unit_for_dataset",
    "build_snapshot_rows",
    "write_snapshot",
    "read_snapshot_rows",
    "load_snapshot_meta",
    "list_snapshot_meta",
    "snapshot_meta_report",
    "run_snapshot_build_and_record",
    "MicroSnapshotComputeManager",
    "append_run_log",
    "read_run_log",
]

# spec section 2.4's benchmark pins this; see scripts/micro_snapshot_granularity_benchmark.py and
# the dev handoff's measured table.
SNAPSHOT_FORMAT_VERSION = "micro-snapshot-v1"

_SNAPSHOTS_DIR_ENV = "TAPEOLOGY_MICRO_SNAPSHOTS_DIR"

_IDENTITY_KEYS = (
    "dataset_checksum",
    "micro_algo_version",
    "snapshot_format_version",
    "feature_source_hash",
    "config_fingerprint",
    "params_hash",
)


class MicroSnapshotIntegrityError(Exception):
    """A snapshot meta file failed its on-load shape check -- corrupted or tampered, surfaced
    explicitly (the ``datasets.DatasetIntegrityError`` discipline, reused in spirit -- module
    docstring; a distinct class because a snapshot is a different failure domain, the codebase's
    own one-exception-class-per-module-domain convention)."""


# This module's own private ZoneInfo constant -- the micro_readiness.py/referee_evidence.py
# per-module idiom (mirrored, not imported: "each module that needs ET wall-clock resolution owns
# a private ZoneInfo constant"). Needed only so ``_pool_records`` below can test a record's own
# (symbol, session_date) against a registered vault universe's ``date_rule`` (spec section 7.5
# point 7, r5, iteration 11) -- generic ET arithmetic, not a research value, so duplicating it
# module-locally carries no single-source-of-truth risk (a session date is a stdlib timezone
# conversion, never a value this module could compute differently from any other).
_ET_ZONE = ZoneInfo("America/New_York")


def _et_session_date(window_start_utc: str) -> str:
    """A stored UTC ISO ``window_start_utc``, converted to its ET calendar date -- the SAME
    conversion ``micro_readiness._et_datetime`` performs, needed here only so
    ``vault.unresolved_pool_dataset_ids`` can test a record's ``(symbol, session_date)`` against a
    registered universe's ``date_rule``."""
    parsed = datetime.fromisoformat(window_start_utc.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(_ET_ZONE).date().isoformat()


def resolve_micro_snapshots_dir(dataset_dir_resolved: str) -> str:
    """``TAPEOLOGY_MICRO_SNAPSHOTS_DIR`` if set, else a ``micro_snapshots`` SIBLING of the
    caller's already-resolved dataset directory -- the ``resolve_desk_playbook_dir`` pattern,
    deliberately NOT a ``Config`` field (the ``TAPEOLOGY_MICRO_*`` family, goal.md Constraints)."""
    override = os.environ.get(_SNAPSHOTS_DIR_ENV)
    if override:
        return override
    return str(Path(dataset_dir_resolved).parent / "micro_snapshots")


def _pool_records(records: list[dict]) -> list[tuple[str, str, str, str]]:
    """Every record's own ``(dataset_id, symbol, session_date, created_utc)`` -- the shape
    ``vault.unresolved_pool_dataset_ids`` needs to test a dataset against a registered universe's
    rule (spec section 7.5 point 7, r5, iteration 11). Pure metadata arithmetic over
    already-loaded ``DatasetStore.list()`` records (``window_start_utc``/``created_utc``, both
    already-verified manifest fields) -- no event read, so this can never become an exploratory
    read of a withheld shard's tape."""
    return [
        (meta["id"], meta["symbol"], _et_session_date(meta["window_start_utc"]), meta.get("created_utc", ""))
        for meta in records
    ]


def _unresolved_pool_ids(dataset_store: DatasetStore, records: list[dict]) -> frozenset[str]:
    """The ONE choke point ``withheld_dataset_ids_for_store``/``exclude_withheld`` below share --
    resolves both vault ledgers off THIS store's own directory (never ``CONFIG``'s, so a
    ``tmp_path``-scoped caller never reads the operator's real vault) and delegates the actual
    withhold DECISION entirely to ``vault.unresolved_pool_dataset_ids`` (never a second, locally
    reimplemented predicate)."""
    root_dir = str(dataset_store.root)
    return vault.unresolved_pool_dataset_ids(
        vault.shard_ledger_for_dataset_dir(root_dir),
        vault.universe_ledger_for_dataset_dir(root_dir),
        _pool_records(records),
    )


def withheld_dataset_ids_for_store(dataset_store: DatasetStore) -> frozenset[str]:
    """Every dataset id that is part of an unresolved registered-universe pool -- spec section 7.5
    point 3 (r3, the ledger-tracked case) and point 7 (r5, iteration 11: the universe-RULE-tracked
    case too -- see ``vault.unresolved_pool_universe_by_dataset_id``'s own docstring for why the
    latter is needed at all). Resolved through the SAME ``vault.shard_ledger_for_dataset_dir``/
    ``vault.universe_ledger_for_dataset_dir`` resolvers every other vault consumer shares -- keyed
    on THIS store's own directory, never ``CONFIG``'s, so a ``tmp_path``-scoped caller never reads
    the operator's real vault.

    Snapshot building is where a withheld shard's raw EVENTS would be replayed, and the snapshot
    listing is where its ``dataset_id``/raw ``dataset_checksum``/``row_count``/``bytes_on_disk``
    would be re-published -- exactly the identity, exact counts and bytes section 7.5 withholds
    until exposure. Both are closed against this set (iter-9 audit finding B1, widened iteration
    11): the era's *(critical)* anti-goal is that a withheld shard's event data and outcome
    aggregates are "refused everywhere (routes, MCP, accessor, readiness) until its recorded
    exposure", and a screening/feature pass over withheld tape would destroy the held-out property
    the vault exists to create. Empty -- and therefore byte-identical to the pre-iter-9 behaviour
    -- until the first shard is ever sealed OR the first universe is ever registered."""
    records, _errors = dataset_store.list()
    return _unresolved_pool_ids(dataset_store, records)


def exclude_withheld(records: list[dict], dataset_store: DatasetStore) -> tuple[list[dict], int]:
    """Spec section 7.5 point 6 (r4): the ONE exclusion-and-disclosure primitive every corpus-wide
    enumerator shares. Returns ``(kept_records, withheld_excluded)`` -- the records whose shards
    are servable, and the COUNT (never the ids) of the ones this run left out.

    Owner ruling r4, stated as code: "a refusal wired only into a route is bypassed by any module
    that enumerates the store itself", so every enumerator filters at its single
    ``DatasetStore.list()`` choke point -- through THIS function, never a second predicate of its
    own (a divergent copy is exactly how the iter-9 audit's B2 leak survived the route-level fix,
    and exactly the class of leak iteration 11 closes again for a dataset a real recorder
    finalizes with no vault ledger row at all -- see ``vault.unresolved_pool_universe_by_dataset_
    id``). The count travels into the caller's report body and into any append-only row the run
    writes: **silent exclusion is forbidden** -- these call sites already hold that "a partial
    report is a misleading report", and the era's denominator rail forbids a corpus that shrinks
    without saying so.

    ``records`` is used AS GIVEN, never re-listed -- every existing call site already passes
    exactly ``dataset_store.list()``'s own record list, so re-listing here would be a redundant,
    potentially inconsistent second enumeration of the same store.

    Zero-cost and byte-identical while nothing is sealed and no universe is registered: neither
    predicate withholds anything, so ``kept is`` every record and the disclosed count is ``0``."""
    withheld = _unresolved_pool_ids(dataset_store, records)
    kept = [record for record in records if record["id"] not in withheld]
    return kept, len(records) - len(kept)


_IDENTITY_SOURCE_MODULES = (mf, mo)


def feature_source_hash() -> str:
    """sha256 over the source bytes of EVERY module a persisted row's values depend on, hashed in
    the fixed ``_IDENTITY_SOURCE_MODULES`` order -- the early-warning for ANY constant/formula
    change (TR-7); recomputed fresh on every call, never cached, since it must reflect whatever
    code is ACTUALLY running right now.

    Spec section 2.3 names "sha256 over the feature-module bytes"; the arithmetic lives in
    ``micro_features.py`` but the values that actually LAND in a row are produced by
    ``micro_observer.py``'s streaming state machine (the windows, the cumulative accumulators, the
    deferred-construct resolution, the section 2.6 emission gate). Hashing only the former left a
    real hole: an observer-only edit CHANGES every stored row's values while every stored identity
    still verifies, so the corpus would be served as valid against code that no longer produces it.
    Covering both is strictly MORE conservative than the spec's literal wording -- it can only ever
    turn a would-be hit into an honest MISS (rebuild), never the reverse -- which is the
    fail-closed direction section 2.3 exists to guarantee."""
    digest = hashlib.sha256()
    for module in _IDENTITY_SOURCE_MODULES:
        digest.update(Path(module.__file__).read_bytes())
    return digest.hexdigest()


def quote_size_unit_for_dataset(dataset_meta: dict) -> str:
    """spec section 2.6: every LEGACY dataset (none carries a recorded verification act) is
    ``"unverified"``. Forward-compatible with a FUTURE (J-06) recorder that stamps
    ``dataset_meta["quote_size_unit"]`` at record time -- read verbatim when present, defaulted to
    ``"unverified"`` when absent (every dataset on disk today)."""
    return dataset_meta.get("quote_size_unit", "unverified")


def snapshot_identity(dataset_meta: dict, config: Config) -> dict:
    """The section 2.3 seven-component identity tuple (as a dict; ``dataset_id`` plus the six
    ``_IDENTITY_KEYS`` re-verified on every load)."""
    return {
        "dataset_id": dataset_meta["id"],
        "dataset_checksum": dataset_meta["checksum"],
        "micro_algo_version": mf.MICRO_ALGO_VERSION,
        "snapshot_format_version": SNAPSHOT_FORMAT_VERSION,
        "feature_source_hash": feature_source_hash(),
        "config_fingerprint": config.config_fingerprint(),
        "params_hash": mf.micro_parameters_hash(),
    }


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _rows_path(root: Path, dataset_id: str) -> Path:
    return root / f"{dataset_id}.jsonl"


def _meta_path(root: Path, dataset_id: str) -> Path:
    return root / f"{dataset_id}.meta.json"


# --- build (the ONE replay pass, per the additive observer= seam) --------------------------------


def build_snapshot_rows(
    dataset_store: DatasetStore, dataset_id: str, config: Config, *, quote_size_unit: str
) -> list[dict]:
    """The ONE replay pass (spec section 2.1): attach a fresh ``MicroObserver`` to
    ``DatasetStore.replay``, drain it to completion, then ``finalize()`` to sweep any still-
    pending deferred construct into an honest ``unavailable`` close-out (module docstring of
    ``micro_observer.py``). Never a second replay implementation.

    Refuses (``MicroObserverFailure``) if the observer raised anywhere mid-stream: the engine
    isolates observer exceptions by design, so WITHOUT this check a failed stream would be
    persisted as a silently TRUNCATED snapshot and identity-verified as complete. Nothing is
    written on that path -- fail-closed, the compute manager surfaces it as ``state: "failed"``
    with the error verbatim."""
    observer = MicroObserver(quote_size_unit=quote_size_unit)
    for _snapshot in dataset_store.replay(dataset_id, config, observer=observer):
        pass
    if observer.failure is not None:
        raise MicroObserverFailure(
            f"the micro observer failed while streaming dataset '{dataset_id}' "
            f"({type(observer.failure).__name__}: {observer.failure}) -- refusing to persist a "
            "partial snapshot"
        ) from observer.failure
    observer.finalize()
    return observer.rows


def write_snapshot(root_dir: str, dataset_id: str, rows: list[dict], identity_and_unit: dict) -> dict:
    """Persist ONE snapshot: the JSONL rows file, then the meta sidecar (``row_count``/
    ``bytes_on_disk``/``built_utc`` computed from what was ACTUALLY written, never estimated)."""
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)
    rows_path = _rows_path(root, dataset_id)
    with rows_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True))
            fh.write("\n")
    meta = {
        **identity_and_unit,
        "row_count": len(rows),
        "bytes_on_disk": rows_path.stat().st_size,
        "built_utc": _iso_utc_now(),
    }
    _meta_path(root, dataset_id).write_text(json.dumps(meta, sort_keys=True))
    return meta


# --- the plain row reader (J-03: micro_join.py's ONLY door onto a snapshot's persisted rows) ------


def read_snapshot_rows(root_dir: str, dataset_id: str) -> list[dict]:
    """Every persisted row of ONE snapshot, in their ORIGINAL append (ascending ``anchor_at``)
    order -- a plain JSONL iterator, co-located with the writer (module docstring) since both read
    and write the identical on-disk shape. Callers MUST have already established the snapshot is
    CURRENT (``load_snapshot_meta`` -- TR-7's re-verification) before calling this: unlike that
    function, this reader performs no identity check of its own and raises ``FileNotFoundError``
    verbatim for a dataset with no snapshot on disk, never a silent empty list.

    This is deliberately a PLAIN reader, not an origin-fenced one -- ``micro_accessor.py`` (J-05)
    becomes the sole, origin-fenced, sealed-shard-aware door onto snapshot AND vault event data
    (the era's "the accessor is the only door" rail); until it exists, the still-fully-exploratory
    legacy corpus this iteration reads has no sealed shard to protect, and the iteration's own
    NOTES record this boundary as an explicit, later re-pointing (J-05 is expected to route
    ``micro_join.py``'s reads through the accessor once it lands, not to duplicate this reader)."""
    rows: list[dict] = []
    with _rows_path(Path(root_dir), dataset_id).open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# --- load, with re-verification (TR-7) ------------------------------------------------------------


def load_snapshot_meta(
    root_dir: str, dataset_store: DatasetStore, dataset_id: str, config: Config
) -> dict | None:
    """The stored meta dict IFF it exists AND its identity still matches a FRESH computation of
    the dataset's current checksum + the current ``config_fingerprint`` + the current
    ``feature_source_hash`` (and the algo/format-version/params-hash components too, for full
    honesty) -- else ``None``, an honest cache MISS meaning "rebuild, never serve stale" (TR-7).
    A malformed meta FILE (present but unparseable) is a distinct, louder failure -- corruption,
    not staleness -- surfaced as ``MicroSnapshotIntegrityError``, never silently treated as a
    miss."""
    meta_path = _meta_path(Path(root_dir), dataset_id)
    if not meta_path.exists():
        return None
    try:
        stored = json.loads(meta_path.read_text())
    except (OSError, ValueError) as exc:
        raise MicroSnapshotIntegrityError(
            f"snapshot meta file for '{dataset_id}' is not parseable ({exc}) -- corrupted or tampered"
        ) from exc
    try:
        dataset_meta = dataset_store.get(dataset_id)
    except DatasetNotFound:
        return None  # the underlying dataset vanished -- nothing to verify against; an honest miss
    current = snapshot_identity(dataset_meta, config)
    for key in _IDENTITY_KEYS:
        if stored.get(key) != current[key]:
            return None  # MISS -- rebuild rather than serve stale (TR-7)
    return stored


def snapshot_meta_report(root_dir: str, dataset_store: DatasetStore, config: Config) -> dict:
    """The ONE walk this module's listing surface performs (goal-rapid-microscope-iter-33, J-12) --
    ``list_snapshot_meta`` (below, existing callers, list-only) and ``GET /research/desk/micro/
    snapshots`` (the disclosure-aware route) both read off THIS single enumeration, never two
    divergent walks of the same directory. Returns ``{"snapshots": [...], "withheld_excluded":
    int, "stale_excluded": int}``, sorted by ``dataset_id`` for deterministic ordering.

    ``withheld_excluded`` is POOL-derived -- the SAME choke point (``_unresolved_pool_ids``) every
    other corpus-wide enumerator in this module already shares (``withheld_dataset_ids_for_store``/
    ``exclude_withheld``), counted over the store's FULL ``list()`` record set. It is deliberately
    **NEVER** a count of which withheld ids happen to have a ``*.meta.json`` file present on disk:
    a withheld shard's snapshot build never runs at all (``run_snapshot_build_and_record``'s own
    filter), so "does a meta file exist for this withheld id" is never an honest question to ask --
    answering it would leak sealed-pool build state (TC-7, spec section 7.5 point 6/point 3, r4/r3).

    ``stale_excluded`` is computed AFTER the withheld filter, over the meta files actually present
    on disk: a meta file whose id is withheld is silently skipped (as before -- iter-9 audit B1 --
    it never entered the corpus this route serves at all, so it is neither a "current" row nor a
    "stale" one, and is never counted twice). Every OTHER meta file counts as stale iff
    ``load_snapshot_meta``'s identity re-verification misses (TR-7) -- "built, then invalidated" by
    an algo/format/feature-source/fingerprint move, never "never built". The stale VALUE itself is
    never carried anywhere, only its count."""
    records, _errors = dataset_store.list()
    # The one choke point `withheld_dataset_ids_for_store`/`exclude_withheld` already share --
    # reused directly (never a second, divergent predicate, and never a second `dataset_store.
    # list()` call: `records` is used AS GIVEN, the `exclude_withheld` precedent).
    withheld = _unresolved_pool_ids(dataset_store, records)
    withheld_excluded = sum(1 for record in records if record["id"] in withheld)

    root = Path(root_dir)
    snapshots: list[dict] = []
    stale_excluded = 0
    if root.exists():
        for meta_file in sorted(root.glob("*.meta.json")):
            dataset_id = meta_file.name[: -len(".meta.json")]
            if dataset_id in withheld:
                # Spec section 7.5 point 3 (r3), iter-9 audit B1: a withheld shard's meta carries
                # its `dataset_id`, its RAW `dataset_checksum`, its exact `row_count` and
                # `bytes_on_disk` -- the identity, counts and bytes withheld until exposure.
                # Omitted here even if a snapshot file for it exists on disk (a shard sealed AFTER
                # its snapshot was built), so the withholding is fail-closed rather than dependent
                # on build order.
                continue
            meta = load_snapshot_meta(root_dir, dataset_store, dataset_id, config)
            if meta is not None:
                snapshots.append(meta)
            else:
                stale_excluded += 1
    snapshots.sort(key=lambda m: m["dataset_id"])
    return {"snapshots": snapshots, "withheld_excluded": withheld_excluded, "stale_excluded": stale_excluded}


def list_snapshot_meta(root_dir: str, dataset_store: DatasetStore, config: Config) -> list[dict]:
    """Every CURRENTLY VALID (identity re-verified) snapshot's meta, sorted by ``dataset_id`` for
    deterministic ordering. A stale meta file (present but no longer identity-matching) is
    silently excluded -- exactly the honest "never serve stale" TR-7 discipline applied to the
    listing surface, not merely the single-dataset loader.

    Delegates to ``snapshot_meta_report`` above (goal-rapid-microscope-iter-33, J-12) -- the SAME
    single walk, list-only for this function's existing callers (none of which need the two
    disclosure counts)."""
    return snapshot_meta_report(root_dir, dataset_store, config)["snapshots"]


# --- the run-and-record orchestration (reuse-or-build per dataset) -------------------------------


def run_snapshot_build_and_record(
    dataset_store: DatasetStore,
    config: Config,
    root_dir: str,
    dataset_ids: list[str] | None = None,
    *,
    progress: Callable[[str], None] | None = None,
    should_abort: Callable[[], bool] | None = None,
) -> list[dict]:
    """Builds (or REUSES, if a currently-valid snapshot already exists -- ``load_snapshot_meta``)
    a snapshot for every id in ``dataset_ids`` (default: every dataset currently in the store, in
    ``DatasetStore.list()``'s own oldest-first order), returning each result's meta dict in order.
    A requested abort is honoured at DATASET boundaries only -- the current dataset's build always
    completes or is skipped-as-already-done; nothing is ever recorded half-built."""
    if dataset_ids is None:
        records, _errors = dataset_store.list()
        dataset_ids = [r["id"] for r in records]
    # Spec section 7.4/7.5 + the era's *(critical)* anti-goal, iter-9 audit B1: a sealed (or
    # merely `assigned`) shard's raw events are NEVER replayed. Applied to an EXPLICITLY passed
    # id list too, not only the default enumeration -- this is the one place snapshot rows are
    # built, so it is the one place the guarantee can be fail-closed rather than dependent on
    # every caller remembering to filter.
    withheld = withheld_dataset_ids_for_store(dataset_store)
    dataset_ids = [dataset_id for dataset_id in dataset_ids if dataset_id not in withheld]
    results: list[dict] = []
    for dataset_id in dataset_ids:
        if should_abort is not None and should_abort():
            break
        existing = load_snapshot_meta(root_dir, dataset_store, dataset_id, config)
        if existing is not None:
            results.append(existing)
        else:
            dataset_meta = dataset_store.get(dataset_id)
            quote_size_unit = quote_size_unit_for_dataset(dataset_meta)
            rows = build_snapshot_rows(dataset_store, dataset_id, config, quote_size_unit=quote_size_unit)
            identity = snapshot_identity(dataset_meta, config)
            meta = write_snapshot(root_dir, dataset_id, rows, {**identity, "quote_size_unit": quote_size_unit})
            results.append(meta)
        if progress is not None:
            progress(dataset_id)
    return results


# --- the durable run log (GET .../snapshots/runs) --------------------------------------------------


def _runs_log_path(root_dir: str) -> Path:
    return Path(root_dir) / "runs.jsonl"


def append_run_log(root_dir: str, entry: dict) -> None:
    """Append ONE terminal run outcome -- a plain JSONL append-only history (a build-run log, not
    a research evidence ledger; no hash-chaining -- that discipline belongs to ledgers research
    CLAIMS depend on, e.g. ``scout_ledger.py``, not this operational build-progress record)."""
    path = _runs_log_path(root_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True))
        fh.write("\n")


def read_run_log(root_dir: str, *, limit: int = 50) -> list[dict]:
    """The most recent ``limit`` runs, NEWEST FIRST. A missing/corrupted log is an honest empty
    list (a build-run history is convenience bookkeeping, never a claim of record -- unlike a
    dataset or a ledger, losing it loses nothing the snapshots themselves do not already prove)."""
    path = _runs_log_path(root_dir)
    if not path.exists():
        return []
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return []
    out: list[dict] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    out.reverse()
    return out[:limit]


# --- the single-flight compute manager (the desk_forward_compute / desk_playbook_compute pattern) -


_IDLE_SNAPSHOT: dict = {
    "run_id": None,
    "state": "idle",
    "progress": {"datasets_total": 0, "datasets_done": 0, "current_dataset_id": None},
    "started_utc": None,
    "finished_utc": None,
    "error": None,
    # Spec section 7.5 point 6 (r4): the disclosure of what this build left out. `0` on an idle
    # manager is a true statement (no run has excluded anything yet), never a placeholder.
    "withheld_excluded": 0,
}


class MicroSnapshotComputeManager:
    """Owns the SINGLE in-flight (or last-terminal) snapshot-build job for this process. Construct
    with no arguments -- every ``trigger()`` call takes its stores/config/dataset-ids explicitly
    (the ``DeskPlaybookComputeManager`` per-call-injection precedent)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot: dict = dict(_IDLE_SNAPSHOT)
        self._run_id: str | None = None
        self._cancel_event: threading.Event | None = None
        self._thread: threading.Thread | None = None

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._snapshot)

    def trigger(
        self,
        dataset_store: DatasetStore,
        config: Config,
        root_dir: str,
        dataset_ids: list[str] | None = None,
    ) -> dict:
        """Start a NEW build job, or -- if one is already ``state == "running"`` -- refuse
        (single-flight, process-wide). Never blocks: the walk runs on a dedicated worker thread."""
        with self._lock:
            if self._snapshot["state"] == "running":
                return {"state": "refused", "reason": "already_running"}

            if dataset_ids is None:
                records, _errors = dataset_store.list()
                resolved_ids = [r["id"] for r in records]
            else:
                resolved_ids = list(dataset_ids)
            # iter-9 audit B1: the published progress block below carries
            # `current_dataset_id`, so an unfiltered enumeration would serve a sealed shard's
            # dataset id on `GET /snapshots/compute` for the duration of the run. Filtered here
            # as well as in `run_snapshot_build_and_record` (which is authoritative for what is
            # actually READ) so `datasets_total` counts what the walk will really do. The count
            # of what was left out is DISCLOSED below and in this run's own append-only run-log
            # row (spec section 7.5 point 6, r4) -- never silently dropped.
            withheld = withheld_dataset_ids_for_store(dataset_store)
            kept_ids = [dataset_id for dataset_id in resolved_ids if dataset_id not in withheld]
            withheld_excluded = len(resolved_ids) - len(kept_ids)
            resolved_ids = kept_ids

            run_id = uuid.uuid4().hex
            self._run_id = run_id
            cancel_event = threading.Event()
            self._cancel_event = cancel_event
            self._snapshot = {
                "run_id": run_id,
                "state": "running",
                "progress": {
                    "datasets_total": len(resolved_ids),
                    "datasets_done": 0,
                    "current_dataset_id": resolved_ids[0] if resolved_ids else None,
                },
                "started_utc": _iso_utc_now(),
                "finished_utc": None,
                "error": None,
                "withheld_excluded": withheld_excluded,
            }
            published = dict(self._snapshot)

        def _publish(dataset_id: str) -> None:
            with self._lock:
                if self._run_id != run_id:
                    return  # a NEWER job already replaced this one -- a stale reporter, ignored
                current = self._snapshot
                self._snapshot = {
                    **current,
                    "progress": {
                        **current["progress"],
                        "datasets_done": current["progress"]["datasets_done"] + 1,
                        "current_dataset_id": dataset_id,
                    },
                }

        def _work() -> None:
            try:
                run_snapshot_build_and_record(
                    dataset_store, config, root_dir, resolved_ids,
                    progress=_publish, should_abort=cancel_event.is_set,
                )
            except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, never swallowed
                self._resolve_terminal(run_id, root_dir, "failed", error=str(exc))
                return
            if cancel_event.is_set():
                self._resolve_terminal(run_id, root_dir, "cancelled")
            else:
                self._resolve_terminal(run_id, root_dir, "done")

        thread = threading.Thread(target=_work, name=f"micro-snapshot-compute:{run_id}", daemon=True)
        with self._lock:
            self._thread = thread
        thread.start()
        return published

    def _resolve_terminal(self, run_id: str, root_dir: str, state: str, *, error: str | None = None) -> None:
        with self._lock:
            if self._run_id != run_id:
                return  # superseded -- never resolve a job that is no longer the current one
            current = self._snapshot
            finished_utc = _iso_utc_now()
            self._snapshot = {**current, "state": state, "finished_utc": finished_utc, "error": error}
            entry = {
                "run_id": run_id,
                "state": state,
                "started_utc": current["started_utc"],
                "finished_utc": finished_utc,
                "datasets_done": current["progress"]["datasets_done"],
                "datasets_total": current["progress"]["datasets_total"],
                "error": error,
                # Spec section 7.5 point 6 (r4): the append-only row this run writes discloses how
                # many withheld shards the walk excluded -- the count only, never an id.
                "withheld_excluded": current["withheld_excluded"],
            }
        append_run_log(root_dir, entry)

    def cancel(self) -> dict:
        """Signal cooperative cancellation. Idempotent (a no-op if not running). The manager's
        visible ``state`` stays ``"running"`` until the worker actually observes the abort at the
        next dataset boundary and resolves to ``"cancelled"`` -- the CALLER (the route) is the one
        that always answers a cancel REQUEST with ``{"state": "cancelled"}`` regardless (module
        docstring); this method just arms the event."""
        with self._lock:
            cancel_event = self._cancel_event
            is_running = self._snapshot["state"] == "running"
        if cancel_event is not None:
            cancel_event.set()
        return {"state": "cancelled", "accepted": is_running}

    def join_all(self, timeout: float = 30.0) -> None:
        """Wait for the in-flight job thread, if any (test/shutdown hygiene)."""
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)


# --- the CLI ----------------------------------------------------------------------------------------


def _cli_progress_printer() -> Callable[[str], None]:
    done = {"n": 0}

    def _print(dataset_id: str) -> None:
        done["n"] += 1
        print(f"  [{done['n']}] snapshot ready for dataset {dataset_id}", flush=True)

    return _print


def main() -> int:
    """``python -m app.research.micro_snapshots [--dataset-id ID ...] [--all]`` -- builds (or
    reuses) snapshots against the operator's REAL dataset/snapshot directories, synchronously, in-
    process (the ``desk_playbook_compute`` CLI-warmer precedent). ``--all`` (the default with no
    ``--dataset-id`` given) builds every dataset currently in the store."""
    parser = argparse.ArgumentParser(
        description="Micro-observer snapshot CLI warmer -- build (or reuse) the prefix-honest "
        "flow/response/liquidity feature snapshot for one or more real recorded tick datasets, "
        "persisting through the SAME store GET /research/desk/micro/snapshots serves."
    )
    parser.add_argument(
        "--dataset-id", action="append", dest="dataset_ids", default=None,
        help="a specific dataset id to build (repeatable); omit (or pass --all) to build every "
        "dataset currently registered in the store.",
    )
    parser.add_argument("--all", action="store_true", help="build every registered dataset (the default).")
    args = parser.parse_args()

    config = CONFIG
    dataset_store = DatasetStore(config.dataset_dir_resolved())
    root_dir = resolve_micro_snapshots_dir(config.dataset_dir_resolved())

    dataset_ids = None if (args.all or not args.dataset_ids) else args.dataset_ids
    results = run_snapshot_build_and_record(
        dataset_store, config, root_dir, dataset_ids, progress=_cli_progress_printer()
    )
    # Spec section 7.5 point 6 (r4): what this run left out is stated, never silently dropped.
    records, _errors = dataset_store.list()
    _kept, withheld_excluded = exclude_withheld(records, dataset_store)
    print(
        f"snapshot build complete: {len(results)} dataset(s) processed "
        f"({withheld_excluded} withheld vault shard(s) excluded); store={root_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
