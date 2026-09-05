"""``TapeObservation`` v1 -- the pure projection builder, schema constants and the two hash
laws (Observation Contract v1, Binding Execution Order step 1; docs/goal.md).

This module is a free-standing, in-process building block: the pure ``TapeObservation`` v1
projection plus its hash and provenance semantics, and nothing else. It is served by exactly one
route, ``GET /tape/{ticker}/observation`` (``app/main.py``; Binding Execution Order step 5,
implemented). That route is transport ONLY: it consumes the ONE atomic managed-observation read
(``WatchManager.get_observation_source`` -- the owner of the settled snapshot, its settled time
and the per-watch source/session descriptor) and passes those values verbatim into
``build_tape_observation``; the route computes no Tapeology semantics, and this module knows
nothing about any route. This module contains, and only:

  * the schema constants (``OBSERVATION_SCHEMA_VERSION``, ``PROVIDER``);
  * the four-group field partition (Constitution §6) as dotted leaf-path tuples;
  * the canonical encoding and both hash laws (``canonical_encode``,
    ``compute_observation_hash``, ``compute_artifact_hash``);
  * the once-per-process implementation-provenance resolver
    (``resolve_implementation_provenance``);
  * the one pure builder (``build_tape_observation``).

RECOMPUTE GUARD (Constitution §10 / era anti-goal, proven by
``tests/test_tape_observation_projection.py``'s AST guard): this module imports NO name from
``app.engine.classifier`` and no name from ``app.engine.features``, and computes no tape
feature, state, confidence or classifier threshold. ``tape_state``, ``confidence``,
``warm``, and ``features`` are read VERBATIM from the caller-supplied ``EngineSnapshot`` --
never recomputed. The classifier's closed state vocabulary is therefore duplicated here as a
literal string tuple (a name list, not logic and not a threshold);
``tests/test_tape_observation_projection.py::test_tape_state_vocabulary_matches_classifier_states``
cross-checks it against ``app.engine.classifier``'s own ``STATE_*`` constants every run, so
drift is caught by a test rather than by this guarded module importing the classifier.

CLOCK / GIT GUARD: ``build_tape_observation`` itself reads no clock and makes no git call --
every instant it returns is either a verbatim caller input or a pure function of
``EngineSnapshot.epoch_anchor`` + ``EngineSnapshot.timestamp``. Git is invoked only inside
``resolve_implementation_provenance``, at most once per process (module-level memoization).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .config import CONFIG, PROFILE_DEFAULT, Config
from .engine.snapshot import EngineSnapshot
from .engine.tape_engine import ENGINE_SEMANTICS_VERSION

# --- Schema constants (Constitution §1, frozen at era open) ------------------------------
OBSERVATION_SCHEMA_VERSION = "tape-observation-v1"
PROVIDER = "tapeology"

# --- Closed tape-state vocabulary ---------------------------------------------------------
# A literal duplicate of app.engine.classifier's five STATE_* string values -- NOT logic, NOT a
# threshold -- required because this module imports nothing from classifier.py (recompute
# guard, TC-2). Cross-checked against classifier.py's own constants by
# test_tape_state_vocabulary_matches_classifier_states in the projection test module.
TAPE_STATE_VOCABULARY: tuple[str, ...] = (
    "buyer_control",
    "seller_control",
    "bid_absorption",
    "ask_absorption",
    "unclear",
)

# --- Four-group field partition (Constitution §6) -- every leaf path exactly once --------
MACHINE_OBSERVATION_SEMANTIC_FIELDS: tuple[str, ...] = (
    "schema_version",
    "provider",
    "ticker",
    "tape_state",
    "confidence",
    "warm",
    "primary_window",
    "features",
    "trade_event_count",
    "market.bid",
    "market.ask",
    "market.spread",
    "market.last",
    "observed_at_utc",
    "timing.logical_timestamp",
    "timing.epoch_anchor",
    "engine_identity.engine_semantics_version",
    "engine_identity.config_fingerprint",
    "engine_identity.profile_id",
    "engine_identity.tape_state_vocabulary",
    "engine_identity.windows",
    "engine_identity.warmup_min_events",
)

PROVENANCE_SOURCE_LIFECYCLE_METADATA_FIELDS: tuple[str, ...] = (
    "available_at_utc",
    "availability_basis",
    "generated_at_utc",
    "timing.settled_at_utc",
    "timing.delivery_lag_seconds",
    "lifecycle.stream_status",
    "lifecycle.paused",
    "lifecycle.end_reason",
    "source.source_mode",
    "source.data_feed",
    "source.scenario",
    "source.window_start_utc",
    "source.window_end_utc",
    "source.dataset_id",
    "source.dataset_checksum",
    "source.session_id",
    "source.session_started_at_utc",
    "implementation_provenance.engine_source_hash",
    "implementation_provenance.source_revision",
    "implementation_provenance.worktree_dirty",
)

EXPLANATORY_METADATA_FIELDS: tuple[str, ...] = ("observations",)

INTEGRITY_FIELDS: tuple[str, ...] = ("observation_hash", "artifact_hash")

# Ordered (group_name, leaf_paths) pairs -- the SINGLE source both the coverage test and the
# doc-lint test read (never a second hand-copied table).
FIELD_PARTITION_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("semantic", MACHINE_OBSERVATION_SEMANTIC_FIELDS),
    ("metadata", PROVENANCE_SOURCE_LIFECYCLE_METADATA_FIELDS),
    ("explanatory", EXPLANATORY_METADATA_FIELDS),
    ("integrity", INTEGRITY_FIELDS),
)


def field_partition_map() -> dict[str, str]:
    """``{leaf_path: partition_name}``, built from ``FIELD_PARTITION_GROUPS`` above."""
    result: dict[str, str] = {}
    for partition_name, paths in FIELD_PARTITION_GROUPS:
        for path in paths:
            result[path] = partition_name
    return result


# --- Canonical encoding and the two hash laws (Constitution §6) --------------------------

def canonical_encode(obj: object) -> bytes:
    """The one canonical encoding every hash in this module (and this repo's ``research/*``
    checksums, e.g. ``app/research/bars.py``) is computed over: sorted keys, no whitespace --
    stable across processes and independent of Python dict insertion order."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _project(observation: dict, paths: tuple[str, ...]) -> dict:
    """A nested dict containing only ``paths`` (dotted leaf paths) of ``observation``, with the
    same nesting shape -- so its canonical encoding depends only on the selected values, never
    on which OTHER fields exist alongside them."""
    projected: dict = {}
    for path in paths:
        parts = path.split(".")
        value = observation
        for part in parts:
            value = value[part]
        cursor = projected
        for part in parts[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[parts[-1]] = value
    return projected


def compute_observation_hash(observation: dict) -> str:
    """sha256 hex of the canonical encoding of the machine-observation semantic set ONLY
    (Constitution §6) -- the machine-observation EQUIVALENCE identity."""
    semantic = _project(observation, MACHINE_OBSERVATION_SEMANTIC_FIELDS)
    return hashlib.sha256(canonical_encode(semantic)).hexdigest()


def compute_artifact_hash(observation: dict) -> str:
    """sha256 hex of the canonical encoding of the whole artifact minus ``artifact_hash``
    itself (Constitution §6) -- the exact-evidence-instance identity. Intentionally distinct on
    every projection (it includes ``generated_at_utc`` and every provenance/session field)."""
    whole = {key: value for key, value in observation.items() if key != "artifact_hash"}
    return hashlib.sha256(canonical_encode(whole)).hexdigest()


# --- Implementation provenance resolver (Constitution §6/§7), resolved once per process --

_ENGINE_DIR = Path(__file__).resolve().parent / "engine"
_REPO_ROOT = Path(__file__).resolve().parents[3]

# The fixed, explicitly-ordered tuple of app/engine/*.py modules the source hash is computed
# over. tests/test_tape_observation_projection.py asserts this equals
# ``sorted(p.name for p in <app/engine>.glob("*.py"))`` so nothing is silently omitted.
ENGINE_SOURCE_MODULES: tuple[str, ...] = (
    "__init__.py",
    "aggressor.py",
    "classifier.py",
    "features.py",
    "history.py",
    "market_state.py",
    "observations.py",
    "snapshot.py",
    "tape_engine.py",
)

_provenance_cache: tuple[str, str | None, bool | None] | None = None


def _engine_source_hash() -> str:
    payload = b"".join((_ENGINE_DIR / name).read_bytes() for name in ENGINE_SOURCE_MODULES)
    return hashlib.sha256(payload).hexdigest()


def _run_git(args: tuple[str, ...]) -> subprocess.CompletedProcess | None:
    """One git subprocess call, or ``None`` when git itself is unavailable (never raises)."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def resolve_implementation_provenance() -> tuple[str, str | None, bool | None]:
    """``(engine_source_hash, source_revision, worktree_dirty)`` -- resolved AT MOST ONCE per
    process (module-level memoization); repeated calls never re-invoke git (no git call per
    request, Constitution §7 / Constraints). Never invents ``source_revision`` or
    ``worktree_dirty``: both are ``None`` when git is unavailable, while ``engine_source_hash``
    (computed independently of git, over source bytes only) is still a valid 64-hex string in
    every case -- clean, dirty, or git-unavailable."""
    global _provenance_cache
    if _provenance_cache is not None:
        return _provenance_cache

    engine_source_hash = _engine_source_hash()

    rev = _run_git(("rev-parse", "HEAD"))
    source_revision = rev.stdout.strip() if rev is not None and rev.returncode == 0 else None

    # The declared dirty-state check (Constitution §7): tracked backend source only, so run and
    # doc artifacts elsewhere in the worktree neither mask code drift nor cry wolf.
    status = _run_git(("status", "--porcelain", "--untracked-files=no", "--", "apps/backend/app"))
    worktree_dirty: bool | None
    if status is not None and status.returncode == 0:
        worktree_dirty = bool(status.stdout.strip())
    else:
        worktree_dirty = None

    _provenance_cache = (engine_source_hash, source_revision, worktree_dirty)
    return _provenance_cache


def _reset_provenance_cache_for_tests() -> None:
    """Test-only seam: clears the module-level memo so a test can exercise clean / dirty /
    git-unavailable resolution in isolation. Never called by production code (nothing under
    ``app/`` besides this module references it)."""
    global _provenance_cache
    _provenance_cache = None


# --- The pure builder (Constitution §1 / §2 / §3) -----------------------------------------

_AVAILABILITY_BASIS_BY_SOURCE_MODE = {
    "live": "live_settled_wall_clock",
    "historical": "historical_arrival_unknown",
    "dataset_replay": "historical_arrival_unknown",
    "sim": "simulated_not_applicable",
}


def _iso_utc(epoch: float) -> str:
    """The repository's pinned ISO instant format (matches ``app/research/bars.py``'s
    ``_iso_utc``): UTC, microseconds, a ``Z`` suffix -- never a hand-formatted string."""
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _observed_at_utc(snapshot: EngineSnapshot) -> str | None:
    """``iso(epoch_anchor + timestamp)``; null iff ``epoch_anchor`` is null OR no event has
    been processed yet (``bid``, ``ask`` and ``last`` all null -- Constitution §2). Not "last
    trade time" and not "time the tape state last changed"."""
    if snapshot.epoch_anchor is None:
        return None
    if snapshot.bid is None and snapshot.ask is None and snapshot.last is None:
        return None
    return _iso_utc(snapshot.epoch_anchor + snapshot.timestamp)


def _availability(source_mode: str, settled_at_utc: str | None) -> tuple[str | None, str]:
    """``(available_at_utc, availability_basis)`` per the Constitution §2 table, keyed off
    ``source_mode``. Never derives ``available_at_utc`` from event time or from
    ``observed_at_utc + delivery_lag_seconds``; on the live basis it is exactly the caller's
    ``settled_at_utc`` (null until the first settled event)."""
    basis = _AVAILABILITY_BASIS_BY_SOURCE_MODE.get(source_mode)
    if basis is None:
        raise ValueError(f"unknown source_mode: {source_mode!r}")
    if basis == "live_settled_wall_clock":
        return settled_at_utc, basis
    return None, basis


def build_tape_observation(
    snapshot: EngineSnapshot,
    *,
    source_mode: str,
    data_feed: str,
    window_start_utc: str | None,
    window_end_utc: str | None,
    dataset_id: str | None,
    dataset_checksum: str | None,
    session_id: str | None,
    session_started_at_utc: str | None,
    settled_at_utc: str | None,
    end_reason: str | None,
    generated_at_utc: str,
    profile_id: str,
    config: Config,
    provenance: tuple[str, str | None, bool | None],
) -> dict:
    """The one pure projection of an ``EngineSnapshot`` plus already-resolved caller inputs
    into a ``TapeObservation`` v1 dict (Constitution §1). No clock read, no git call, no
    engine-internal import, no classifier/feature-computation import (recompute guard).

    ``source.*`` descriptor fields (``window_start_utc`` .. ``session_started_at_utc``),
    ``settled_at_utc``, ``end_reason``, ``generated_at_utc`` and ``provenance`` are verbatim
    pass-through of the caller's already-resolved inputs -- this function computes only the time/
    availability LAW from them; the machinery that makes them genuinely atomic and live-correct
    is ``WatchManager``'s settled pair + source descriptor, read together by
    ``get_observation_source`` and handed in unchanged by ``GET /tape/{ticker}/observation``.
    ``source.scenario`` is read from ``snapshot.scenario`` (its Constitution §1 owner), never
    accepted as a second, possibly-divergent parameter.

    Raises ``ValueError`` (the profile refusal, Constitution §3) when ``profile_id`` is
    ``"default"`` but ``config.config_fingerprint()`` differs from the process ``CONFIG``
    fingerprint -- it never invents a profile string for the mismatch.
    """
    if profile_id == PROFILE_DEFAULT and config.config_fingerprint() != CONFIG.config_fingerprint():
        raise ValueError(
            "profile_id='default' claimed under a config_fingerprint "
            f"({config.config_fingerprint()}) that differs from the process CONFIG "
            f"fingerprint ({CONFIG.config_fingerprint()})"
        )

    engine_source_hash, source_revision, worktree_dirty = provenance
    available_at_utc, availability_basis = _availability(source_mode, settled_at_utc)

    observation: dict = {
        "schema_version": OBSERVATION_SCHEMA_VERSION,
        "provider": PROVIDER,
        "ticker": snapshot.ticker,
        "observed_at_utc": _observed_at_utc(snapshot),
        "available_at_utc": available_at_utc,
        "availability_basis": availability_basis,
        "generated_at_utc": generated_at_utc,
        "tape_state": snapshot.tape_state,
        "confidence": snapshot.confidence,
        "warm": snapshot.warm,
        "primary_window": snapshot.primary_window,
        "features": snapshot.features,
        "trade_event_count": snapshot.event_count,
        "market": {
            "bid": snapshot.bid,
            "ask": snapshot.ask,
            "spread": snapshot.spread,
            "last": snapshot.last,
        },
        "observations": list(snapshot.observations),
        "lifecycle": {
            "stream_status": snapshot.stream_status,
            "paused": snapshot.paused,
            "end_reason": end_reason,
        },
        "timing": {
            "logical_timestamp": snapshot.timestamp,
            "epoch_anchor": snapshot.epoch_anchor,
            "settled_at_utc": settled_at_utc,
            "delivery_lag_seconds": snapshot.delivery_lag_seconds,
        },
        "source": {
            "source_mode": source_mode,
            "data_feed": data_feed,
            "scenario": snapshot.scenario,
            "window_start_utc": window_start_utc,
            "window_end_utc": window_end_utc,
            "dataset_id": dataset_id,
            "dataset_checksum": dataset_checksum,
            "session_id": session_id,
            "session_started_at_utc": session_started_at_utc,
        },
        "engine_identity": {
            "engine_semantics_version": ENGINE_SEMANTICS_VERSION,
            "config_fingerprint": config.config_fingerprint(),
            "profile_id": profile_id,
            "tape_state_vocabulary": list(TAPE_STATE_VOCABULARY),
            "windows": [config.window_label(window) for window in config.windows],
            "warmup_min_events": config.warmup_min_events,
        },
        "implementation_provenance": {
            "engine_source_hash": engine_source_hash,
            "source_revision": source_revision,
            "worktree_dirty": worktree_dirty,
        },
    }
    observation["observation_hash"] = compute_observation_hash(observation)
    observation["artifact_hash"] = compute_artifact_hash(observation)
    return observation
