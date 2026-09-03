# Iteration diff (bounded)

Files changed: 3. Shown in full: 1.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/observation_contract.py` (8 lines not shown)
- `apps/backend/tests/test_tape_observation_projection.py` (109 lines not shown)

```diff
diff --git a/apps/backend/app/engine/tape_engine.py b/apps/backend/app/engine/tape_engine.py
index 121abc64..a513d911 100644
--- a/apps/backend/app/engine/tape_engine.py
+++ b/apps/backend/app/engine/tape_engine.py
@@ -29,6 +29,14 @@ from .snapshot import EngineSnapshot, TradeRow
 # research type, so logging a failure leaks no research concept into the engine.
 logger = logging.getLogger(__name__)
 
+# The engine's SEMANTIC identity (Observation Contract v1, Constitution §6/§7): bumped ONLY by
+# an explicit owner act when classifier, feature, aggressor or warm-up semantics change -- never
+# by an automated inference. `app/observation_contract.py`'s `engine_identity.engine_semantics_
+# version` reads this constant verbatim (never a second copy). It is distinct from
+# `implementation_provenance.engine_source_hash` (exact source bytes, changes on comment edits
+# too): a changed source hash never by itself claims a semantic change.
+ENGINE_SEMANTICS_VERSION = "tape-engine-v1"
+
 
 class TapeEngine:
     def __init__(
diff --git a/apps/backend/app/observation_contract.py b/apps/backend/app/observation_contract.py
new file mode 100644
index 00000000..6d078b52
--- /dev/null
+++ b/apps/backend/app/observation_contract.py
@@ -0,0 +1,402 @@
+"""``TapeObservation`` v1 -- the pure projection builder, schema constants and the two hash
+laws (Observation Contract v1, Binding Execution Order step 1; docs/goal.md).
+
+This module is a free-standing, in-process building block. Nothing here is served by any route
+yet -- the ``GET /tape/{ticker}/observation`` route is step 5 (a later iteration). This module
+contains, and only:
+
+  * the schema constants (``OBSERVATION_SCHEMA_VERSION``, ``PROVIDER``);
+  * the four-group field partition (Constitution §6) as dotted leaf-path tuples;
+  * the canonical encoding and both hash laws (``canonical_encode``,
+    ``compute_observation_hash``, ``compute_artifact_hash``);
+  * the once-per-process implementation-provenance resolver
+    (``resolve_implementation_provenance``);
+  * the one pure builder (``build_tape_observation``).
+
+RECOMPUTE GUARD (Constitution §10 / era anti-goal, proven by
+``tests/test_tape_observation_projection.py``'s AST guard): this module imports NO name from
+``app.engine.classifier`` and no name from ``app.engine.features``, and computes no tape
+feature, state, confidence or classifier threshold. ``tape_state``, ``confidence``,
+``warm``, and ``features`` are read VERBATIM from the caller-supplied ``EngineSnapshot`` --
+never recomputed. The classifier's closed state vocabulary is therefore duplicated here as a
+literal string tuple (a name list, not logic and not a threshold);
+``tests/test_tape_observation_projection.py::test_tape_state_vocabulary_matches_classifier_states``
+cross-checks it against ``app.engine.classifier``'s own ``STATE_*`` constants every run, so
+drift is caught by a test rather than by this guarded module importing the classifier.
+
+CLOCK / GIT GUARD: ``build_tape_observation`` itself reads no clock and makes no git call --
+every instant it returns is either a verbatim caller input or a pure function of
+``EngineSnapshot.epoch_anchor`` + ``EngineSnapshot.timestamp``. Git is invoked only inside
+``resolve_implementation_provenance``, at most once per process (module-level memoization).
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+import subprocess
+from datetime import datetime, timezone
+from pathlib import Path
+
+from .config import CONFIG, PROFILE_DEFAULT, Config
+from .engine.snapshot import EngineSnapshot
+from .engine.tape_engine import ENGINE_SEMANTICS_VERSION
+
+# --- Schema constants (Constitution §1, frozen at era open) ------------------------------
+OBSERVATION_SCHEMA_VERSION = "tape-observation-v1"
+PROVIDER = "tapeology"
+
+# --- Closed tape-state vocabulary ---------------------------------------------------------
+# A literal duplicate of app.engine.classifier's five STATE_* string values -- NOT logic, NOT a
+# threshold -- required because this module imports nothing from classifier.py (recompute
+# guard, TC-2). Cross-checked against classifier.py's own constants by
+# test_tape_state_vocabulary_matches_classifier_states in the projection test module.
+TAPE_STATE_VOCABULARY: tuple[str, ...] = (
+    "buyer_control",
+    "seller_control",
+    "bid_absorption",
+    "ask_absorption",
+    "unclear",
+)
+
+# --- Four-group field partition (Constitution §6) -- every leaf path exactly once --------
+MACHINE_OBSERVATION_SEMANTIC_FIELDS: tuple[str, ...] = (
+    "schema_version",
+    "provider",
+    "ticker",
+    "tape_state",
+    "confidence",
+    "warm",
+    "primary_window",
+    "features",
+    "trade_event_count",
+    "market.bid",
+    "market.ask",
+    "market.spread",
+    "market.last",
+    "observed_at_utc",
+    "timing.logical_timestamp",
+    "timing.epoch_anchor",
+    "engine_identity.engine_semantics_version",
+    "engine_identity.config_fingerprint",
+    "engine_identity.profile_id",
+    "engine_identity.tape_state_vocabulary",
+    "engine_identity.windows",
+    "engine_identity.warmup_min_events",
+)
+
+PROVENANCE_SOURCE_LIFECYCLE_METADATA_FIELDS: tuple[str, ...] = (
+    "available_at_utc",
+    "availability_basis",
+    "generated_at_utc",
+    "timing.settled_at_utc",
+    "timing.delivery_lag_seconds",
+    "lifecycle.stream_status",
+    "lifecycle.paused",
+    "lifecycle.end_reason",
+    "source.source_mode",
+    "source.data_feed",
+    "source.scenario",
+    "source.window_start_utc",
+    "source.window_end_utc",
+    "source.dataset_id",
+    "source.dataset_checksum",
+    "source.session_id",
+    "source.session_started_at_utc",
+    "implementation_provenance.engine_source_hash",
+    "implementation_provenance.source_revision",
+    "implementation_provenance.worktree_dirty",
+)
+
+EXPLANATORY_METADATA_FIELDS: tuple[str, ...] = ("observations",)
+
+INTEGRITY_FIELDS: tuple[str, ...] = ("observation_hash", "artifact_hash")
+
+# Ordered (group_name, leaf_paths) pairs -- the SINGLE source both the coverage test and the
+# doc-lint test read (never a second hand-copied table).
+FIELD_PARTITION_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
+    ("semantic", MACHINE_OBSERVATION_SEMANTIC_FIELDS),
+    ("metadata", PROVENANCE_SOURCE_LIFECYCLE_METADATA_FIELDS),
+    ("explanatory", EXPLANATORY_METADATA_FIELDS),
+    ("integrity", INTEGRITY_FIELDS),
+)
+
+
+def field_partition_map() -> dict[str, str]:
+    """``{leaf_path: partition_name}``, built from ``FIELD_PARTITION_GROUPS`` above."""
+    result: dict[str, str] = {}
+    for partition_name, paths in FIELD_PARTITION_GROUPS:
+        for path in paths:
+            result[path] = partition_name
+    return result
+
+
+# --- Canonical encoding and the two hash laws (Constitution §6) --------------------------
+
+def canonical_encode(obj: object) -> bytes:
+    """The one canonical encoding every hash in this module (and this repo's ``research/*``
+    checksums, e.g. ``app/research/bars.py``) is computed over: sorted keys, no whitespace --
+    stable across processes and independent of Python dict insertion order."""
+    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
+
+
+def _project(observation: dict, paths: tuple[str, ...]) -> dict:
+    """A nested dict containing only ``paths`` (dotted leaf paths) of ``observation``, with the
+    same nesting shape -- so its canonical encoding depends only on the selected values, never
+    on which OTHER fields exist alongside them."""
+    projected: dict = {}
+    for path in paths:
+        parts = path.split(".")
+        value = observation
+        for part in parts:
+            value = value[part]
+        cursor = projected
+        for part in parts[:-1]:
+            cursor = cursor.setdefault(part, {})
+        cursor[parts[-1]] = value
+    return projected
+
+
+def compute_observation_hash(observation: dict) -> str:
+    """sha256 hex of the canonical encoding of the machine-observation semantic set ONLY
+    (Constitution §6) -- the machine-observation EQUIVALENCE identity."""
+    semantic = _project(observation, MACHINE_OBSERVATION_SEMANTIC_FIELDS)
+    return hashlib.sha256(canonical_encode(semantic)).hexdigest()
+
+
+def compute_artifact_hash(observation: dict) -> str:
+    """sha256 hex of the canonical encoding of the whole artifact minus ``artifact_hash``
+    itself (Constitution §6) -- the exact-evidence-instance identity. Intentionally distinct on
+    every projection (it includes ``generated_at_utc`` and every provenance/session field)."""
+    whole = {key: value for key, value in observation.items() if key != "artifact_hash"}
+    return hashlib.sha256(canonical_encode(whole)).hexdigest()
+
+
+# --- Implementation provenance resolver (Constitution §6/§7), resolved once per process --
+
+_ENGINE_DIR = Path(__file__).resolve().parent / "engine"
+_REPO_ROOT = Path(__file__).resolve().parents[3]
+
+# The fixed, explicitly-ordered tuple of app/engine/*.py modules the source hash is computed
+# over. tests/test_tape_observation_projection.py asserts this equals
+# ``sorted(p.name for p in <app/engine>.glob("*.py"))`` so nothing is silently omitted.
+ENGINE_SOURCE_MODULES: tuple[str, ...] = (
+    "__init__.py",
+    "aggressor.py",
+    "classifier.py",
+    "features.py",
+    "history.py",
+    "market_state.py",
+    "observations.py",
+    "snapshot.py",
+    "tape_engine.py",
+)
+
+_provenance_cache: tuple[str, str | None, bool | None] | None = None
+
+
+def _engine_source_hash() -> str:
+    payload = b"".join((_ENGINE_DIR / name).read_bytes() for name in ENGINE_SOURCE_MODULES)
+    return hashlib.sha256(payload).hexdigest()
+
+
+def _run_git(args: tuple[str, ...]) -> subprocess.CompletedProcess | None:
+    """One git subprocess call, or ``None`` when git itself is unavailable (never raises)."""
+    try:
+        return subprocess.run(
+            ["git", *args],
+            cwd=_REPO_ROOT,
+            capture_output=True,
+            text=True,
+            timeout=5,
+            check=False,
+        )
+    except (OSError, subprocess.SubprocessError):
+        return None
+
+
+def resolve_implementation_provenance() -> tuple[str, str | None, bool | None]:
+    """``(engine_source_hash, source_revision, worktree_dirty)`` -- resolved AT MOST ONCE per
+    process (module-level memoization); repeated calls never re-invoke git (no git call per
+    request, Constitution §7 / Constraints). Never invents ``source_revision`` or
+    ``worktree_dirty``: both are ``None`` when git is unavailable, while ``engine_source_hash``
+    (computed independently of git, over source bytes only) is still a valid 64-hex string in
+    every case -- clean, dirty, or git-unavailable."""
+    global _provenance_cache
+    if _provenance_cache is not None:
+        return _provenance_cache
+
+    engine_source_hash = _engine_source_hash()
+
+    rev = _run_git(("rev-parse", "HEAD"))
+    source_revision = rev.stdout.strip() if rev is not None and rev.returncode == 0 else None
+
+    # The declared dirty-state check (Constitution §7): tracked backend source only, so run and
+    # doc artifacts elsewhere in the worktree neither mask code drift nor cry wolf.
+    status = _run_git(("status", "--porcelain", "--untracked-files=no", "--", "apps/backend/app"))
+    worktree_dirty: bool | None
+    if status is not None and status.returncode == 0:
+        worktree_dirty = bool(status.stdout.strip())
+    else:
+        worktree_dirty = None
+
+    _provenance_cache = (engine_source_hash, source_revision, worktree_dirty)
+    return _provenance_cache
+
+
+def _reset_provenance_cache_for_tests() -> None:
+    """Test-only seam: clears the module-level memo so a test can exercise clean / dirty /
+    git-unavailable resolution in isolation. Never called by production code (nothing under
+    ``app/`` besides this module references it)."""
+    global _provenance_cache
+    _provenance_cache = None
+
+
+# --- The pure builder (Constitution §1 / §2 / §3) -----------------------------------------
+
+_AVAILABILITY_BASIS_BY_SOURCE_MODE = {
+    "live": "live_settled_wall_clock",
+    "historical": "historical_arrival_unknown",
+    "dataset_replay": "historical_arrival_unknown",
+    "sim": "simulated_not_applicable",
+}
+
+
+def _iso_utc(epoch: float) -> str:
+    """The repository's pinned ISO instant format (matches ``app/research/bars.py``'s
+    ``_iso_utc``): UTC, microseconds, a ``Z`` suffix -- never a hand-formatted string."""
+    return (
+        datetime.fromtimestamp(epoch, tz=timezone.utc)
+        .isoformat(timespec="microseconds")
+        .replace("+00:00", "Z")
+    )
+
+
+def _observed_at_utc(snapshot: EngineSnapshot) -> str | None:
+    """``iso(epoch_anchor + timestamp)``; null iff ``epoch_anchor`` is null OR no event has
+    been processed yet (``bid``, ``ask`` and ``last`` all null -- Constitution §2). Not "last
+    trade time" and not "time the tape state last changed"."""
+    if snapshot.epoch_anchor is None:
+        return None
+    if snapshot.bid is None and snapshot.ask is None and snapshot.last is None:
+        return None
+    return _iso_utc(snapshot.epoch_anchor + snapshot.timestamp)
+
+
+def _availability(source_mode: str, settled_at_utc: str | None) -> tuple[str | None, str]:
+    """``(available_at_utc, availability_basis)`` per the Constitution §2 table, keyed off
+    ``source_mode``. Never derives ``available_at_utc`` from event time or from
+    ``observed_at_utc + delivery_lag_seconds``; on the live basis it is exactly the caller's
+    ``settled_at_utc`` (null until the first settled event)."""
+    basis = _AVAILABILITY_BASIS_BY_SOURCE_MODE.get(source_mode)
+    if basis is None:
+        raise ValueError(f"unknown source_mode: {source_mode!r}")
+    if basis == "live_settled_wall_clock":
+        return settled_at_utc, basis
+    return None, basis
+
+
+def build_tape_observation(
+    snapshot: EngineSnapshot,
+    *,
+    source_mode: str,
+    data_feed: str,
+    window_start_utc: str | None,
+    window_end_utc: str | None,
+    dataset_id: str | None,
+    dataset_checksum: str | None,
+    session_id: str | None,
+    session_started_at_utc: str | None,
+    settled_at_utc: str | None,
+    end_reason: str | None,
+    generated_at_utc: str,
+    profile_id: str,
+    config: Config,
+    provenance: tuple[str, str | None, bool | None],
+) -> dict:
+    """The one pure projection of an ``EngineSnapshot`` plus already-resolved caller inputs
+    into a ``TapeObservation`` v1 dict (Constitution §1). No clock read, no git call, no
+    engine-internal import, no classifier/feature-computation import (recompute guard).
+
+    ``source.*`` descriptor fields (``window_start_utc`` .. ``session_started_at_utc``),
+    ``settled_at_utc``, ``end_reason``, ``generated_at_utc`` and ``provenance`` are verbatim
+    pass-through of the caller's already-resolved inputs -- this iteration computes the time/
+    availability LAW correctly from them; the machinery that makes them genuinely atomic/live-
+    correct (the manager's settled pair, ``get_observation_source``) is a later iteration.
+    ``source.scenario`` is read from ``snapshot.scenario`` (its Constitution §1 owner), never
+    accepted as a second, possibly-divergent parameter.
+
+    Raises ``ValueError`` (the profile refusal, Constitution §3) when ``profile_id`` is
+    ``"default"`` but ``config.config_fingerprint()`` differs from the process ``CONFIG``
+    fingerprint -- it never invents a profile string for the mismatch.
+    """
+    if profile_id == PROFILE_DEFAULT and config.config_fingerprint() != CONFIG.config_fingerprint():
+        raise ValueError(
+            "profile_id='default' claimed under a config_fingerprint "
+            f"({config.config_fingerprint()}) that differs from the process CONFIG "
+            f"fingerprint ({CONFIG.config_fingerprint()})"
+        )
+
+    engine_source_hash, source_revision, worktree_dirty = provenance
+    available_at_utc, availability_basis = _availability(source_mode, settled_at_utc)
+
+    observation: dict = {
+        "schema_version": OBSERVATION_SCHEMA_VERSION,
+        "provider": PROVIDER,
+        "ticker": snapshot.ticker,
+        "observed_at_utc": _observed_at_utc(snapshot),
+        "available_at_utc": available_at_utc,
+        "availability_basis": availability_basis,
+        "generated_at_utc": generated_at_utc,
+        "tape_state": snapshot.tape_state,
+        "confidence": snapshot.confidence,
+        "warm": snapshot.warm,
+        "primary_window": snapshot.primary_window,
+        "features": snapshot.features,
+        "trade_event_count": snapshot.event_count,
+        "market": {
+            "bid": snapshot.bid,
+            "ask": snapshot.ask,
+            "spread": snapshot.spread,
+            "last": snapshot.last,
+        },
+        "observations": list(snapshot.observations),
+        "lifecycle": {
+            "stream_status": snapshot.stream_status,
+            "paused": snapshot.paused,
+            "end_reason": end_reason,
+        },
+        "timing": {
+            "logical_timestamp": snapshot.timestamp,
+            "epoch_anchor": snapshot.epoch_anchor,
+            "settled_at_utc": settled_at_utc,
+            "delivery_lag_seconds": snapshot.delivery_lag_seconds,
+        },
+        "source": {
+            "source_mode": source_mode,
+            "data_feed": data_feed,
+            "scenario": snapshot.scenario,
+            "window_start_utc": window_start_utc,
+            "window_end_utc": window_end_utc,
+            "dataset_id": dataset_id,
+            "dataset_checksum": dataset_checksum,
+            "session_id": session_id,
+            "session_started_at_utc": session_started_at_utc,
+        },
+        "engine_identity": {
+            "engine_semantics_version": ENGINE_SEMANTICS_VERSION,
+            "config_fingerprint": config.config_fingerprint(),
+            "profile_id": profile_id,
+            "tape_state_vocabulary": list(TAPE_STATE_VOCABULARY),
+            "windows": [config.window_label(window) for window in config.windows],
+            "warmup_min_events": config.warmup_min_events,
+        },
+        "implementation_provenance": {
... [diff_bound] apps/backend/app/observation_contract.py: 8 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_tape_observation_projection.py b/apps/backend/tests/test_tape_observation_projection.py
new file mode 100644
index 00000000..b9211476
--- /dev/null
+++ b/apps/backend/tests/test_tape_observation_projection.py
@@ -0,0 +1,503 @@
+"""Observation Contract v1 -- Binding Execution Order step 1 (J-01; docs/goal.md).
+
+Covers ``app/observation_contract.py``'s pure builder, schema constants, four-group partition
+and the two hash laws. TC references below match the iteration spec
+(``docs/phases/goal-observation-contract-iter-1.md``) and goal.md's J-01 Steps.4 list. Every
+guard/law test ships a named ``test_counterexample_*`` proving it can fail (never a vacuous
+assertion). No test in this module needs a running uvicorn server or network access (the route
+does not exist until a later iteration -- ``/tape/SIM-BIDABS/observation`` still 404s).
+"""
+
+from __future__ import annotations
+
+import ast
+import copy
+from dataclasses import replace
+from pathlib import Path
+
+import pytest
+
+from app import observation_contract
+from app.config import CONFIG, Config
+from app.engine import classifier as classifier_module
+from app.engine.snapshot import EngineSnapshot
+from app.observation_contract import (
+    ENGINE_SEMANTICS_VERSION,
+    build_tape_observation,
+    canonical_encode,
+    compute_artifact_hash,
+    compute_observation_hash,
+    field_partition_map,
+    resolve_implementation_provenance,
+)
+
+OBS_CONTRACT_PATH = Path(observation_contract.__file__)
+SPEC_PATH = Path(__file__).resolve().parents[3] / "docs" / "observation-contract-spec.md"
+
+
+# --- Fixtures / small builders -------------------------------------------------------------
+
+def _make_snapshot(**overrides: object) -> EngineSnapshot:
+    defaults: dict = dict(
+        ticker="SIM-BIDABS",
+        scenario="bid_absorption",
+        timestamp=67.25,
+        event_count=17,
+        warm=True,
+        stream_status="live",
+        bid=149.01,
+        ask=149.03,
+        spread=0.02,
+        last=149.02,
+        features={"30s": {"aggressive_sell_ratio": 0.8, "bid_refresh_score": 0.7}},
+        primary_window="30s",
+        tape_state="bid_absorption",
+        confidence=0.83,
+        observations=("Heavy sell volume being absorbed",),
+        paused=False,
+        epoch_anchor=1704205800.0,
+        delivery_lag_seconds=0.0,
+    )
+    defaults.update(overrides)
+    return EngineSnapshot(**defaults)
+
+
+def _valid_provenance() -> tuple[str, str | None, bool | None]:
+    return ("a" * 64, "abc123def456", False)
+
+
+def _build(snapshot: EngineSnapshot | None = None, **overrides: object) -> dict:
+    snapshot = snapshot if snapshot is not None else _make_snapshot()
+    kwargs: dict = dict(
+        snapshot=snapshot,
+        source_mode="sim",
+        data_feed="sim",
+        window_start_utc=None,
+        window_end_utc=None,
+        dataset_id=None,
+        dataset_checksum=None,
+        session_id="session-abc-123",
+        session_started_at_utc="2026-09-02T13:04:59.000000Z",
+        settled_at_utc="2026-09-02T13:05:41.104913Z",
+        end_reason=None,
+        generated_at_utc="2026-09-02T13:05:41.118204Z",
+        profile_id="default",
+        config=CONFIG,
+        provenance=_valid_provenance(),
+    )
+    kwargs.update(overrides)
+    return build_tape_observation(**kwargs)
+
+
+# --- TC-1: sentinel mutation projected verbatim (no recomputation) -------------------------
+
+def test_sentinel_mutation_projected_verbatim():
+    snapshot = _make_snapshot(
+        tape_state="bid_absorption",
+        confidence=0.83,
+        features={"30s": {"sentinel_feature": 12.5}},
+    )
+    observation = _build(snapshot=snapshot)
+    assert observation["tape_state"] == "bid_absorption"
+    assert observation["confidence"] == 0.83
+    assert observation["features"] == {"30s": {"sentinel_feature": 12.5}}
+    assert observation["warm"] is True
+    assert observation["primary_window"] == "30s"
+
+
+# --- TC-2: recompute guard (no classifier/feature import, no threshold literal) ------------
+
+def _classifier_threshold_field_names() -> set[str]:
+    """Every ``c.<name>`` attribute access inside classifier.py's source -- the classifier's
+    OWN threshold/scale field names, read dynamically so this can never silently drift."""
+    source = Path(classifier_module.__file__).read_text()
+    tree = ast.parse(source)
+    names: set[str] = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "c":
+            names.add(node.attr)
+    return names
+
+
+def _classifier_threshold_values() -> set[float]:
+    values: set[float] = set()
+    for name in _classifier_threshold_field_names():
+        value = getattr(CONFIG, name, None)
+        if isinstance(value, (int, float)) and not isinstance(value, bool):
+            values.add(float(value))
+    return values
+
+
+def _numeric_literals(source: str) -> set[float]:
+    tree = ast.parse(source)
+    literals: set[float] = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(
+            node.value, bool
+        ):
+            literals.add(float(node.value))
+    return literals
+
+
+def _recompute_guard_violations(source: str) -> list[str]:
+    violations: list[str] = []
+    tree = ast.parse(source)
+    for node in ast.walk(tree):
+        if isinstance(node, ast.ImportFrom) and node.module:
+            if node.module.endswith("engine.classifier") or node.module.endswith("engine.features"):
+                violations.append(f"import from {node.module}")
+        if isinstance(node, ast.Import):
+            for alias in node.names:
+                if alias.name.endswith("engine.classifier") or alias.name.endswith("engine.features"):
+                    violations.append(f"import {alias.name}")
+    thresholds = _classifier_threshold_values()
+    for literal in _numeric_literals(source):
+        if literal in thresholds:
+            violations.append(f"numeric literal {literal} matches a classifier threshold")
+    return violations
+
+
+def test_recompute_guard_no_classifier_or_feature_import_or_threshold_literal():
+    source = OBS_CONTRACT_PATH.read_text()
+    assert _recompute_guard_violations(source) == []
+
+
+def test_counterexample_recompute_guard_detects_classifier_import():
+    fixture_source = "from app.engine.classifier import STATE_BUYER_CONTROL\nX = STATE_BUYER_CONTROL\n"
+    assert _recompute_guard_violations(fixture_source) != []
+
+
+def test_counterexample_recompute_guard_detects_threshold_literal():
+    threshold_value = CONFIG.min_aggressive_buy_ratio
+    fixture_source = f"THRESHOLD = {threshold_value!r}\n"
+    assert _recompute_guard_violations(fixture_source) != []
+
+
+def test_tape_state_vocabulary_matches_classifier_states():
+    classifier_states = {
+        classifier_module.STATE_BUYER_CONTROL,
+        classifier_module.STATE_SELLER_CONTROL,
+        classifier_module.STATE_BID_ABSORPTION,
+        classifier_module.STATE_ASK_ABSORPTION,
+        classifier_module.STATE_UNCLEAR,
+    }
+    assert set(observation_contract.TAPE_STATE_VOCABULARY) == classifier_states
+
+
+# --- TC-3: trade_event_count verbatim, no re-count ------------------------------------------
+
+def test_trade_event_count_equals_snapshot_event_count_verbatim():
+    snapshot = _make_snapshot(event_count=17)
+    observation = _build(snapshot=snapshot)
+    assert observation["trade_event_count"] == 17
+
+
+def test_source_scan_builder_has_no_loop_over_trade_data():
+    source = OBS_CONTRACT_PATH.read_text()
+    # Deliberately-excluded panel fields (Constitution §1) -- their mere presence as a string
+    # in this module would already be suspicious; their absence also proves no re-count over
+    # either list is possible here.
+    assert "recent_trades" not in source
+    assert "event_log" not in source
+    tree = ast.parse(source)
+    builder = next(
+        node
+        for node in ast.walk(tree)
+        if isinstance(node, ast.FunctionDef) and node.name == "build_tape_observation"
+    )
+    assert not any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(builder))
+
+
+# --- TC-4: both hashes recomputable; key-order permutation changes neither -----------------
+
+def _reverse_dict_order(obj: object) -> object:
+    if isinstance(obj, dict):
+        return {key: _reverse_dict_order(obj[key]) for key in reversed(list(obj.keys()))}
+    if isinstance(obj, list):
+        return [_reverse_dict_order(item) for item in obj]
+    return obj
+
+
+def test_hashes_recomputable_and_key_order_independent():
+    observation = _build()
+    recomputed_observation_hash = compute_observation_hash(observation)
+    recomputed_artifact_hash = compute_artifact_hash(observation)
+    assert recomputed_observation_hash == observation["observation_hash"]
+    assert recomputed_artifact_hash == observation["artifact_hash"]
+
+    reversed_observation = _reverse_dict_order(observation)
+    assert compute_observation_hash(reversed_observation) == observation["observation_hash"]
+    assert compute_artifact_hash(reversed_observation) == observation["artifact_hash"]
+
+
+def test_counterexample_hash_functions_are_not_vacuously_constant():
+    observation_a = _build()
+    observation_b = _build(snapshot=_make_snapshot(tape_state="seller_control", confidence=0.71))
+    assert compute_observation_hash(observation_a) != compute_observation_hash(observation_b)
+    assert compute_artifact_hash(observation_a) != compute_artifact_hash(observation_b)
+
+
+# --- TC-5: observation_hash changes with engine_semantics_version/config_fingerprint/profile_id
+
+def test_observation_hash_changes_with_engine_semantics_version():
+    observation = _build()
+    mutated = copy.deepcopy(observation)
+    mutated["engine_identity"]["engine_semantics_version"] = "tape-engine-v2"
+    assert compute_observation_hash(mutated) != compute_observation_hash(observation)
+
+
+def test_observation_hash_changes_with_config_fingerprint():
+    observation = _build()
+    mutated = copy.deepcopy(observation)
+    mutated["engine_identity"]["config_fingerprint"] = "deadbeefdeadbeef"
+    assert compute_observation_hash(mutated) != compute_observation_hash(observation)
+
+
+def test_observation_hash_changes_with_profile_id():
+    observation = _build()
+    mutated = copy.deepcopy(observation)
+    mutated["engine_identity"]["profile_id"] = "candidate_faster_warmup"
+    assert compute_observation_hash(mutated) != compute_observation_hash(observation)
+
+
+# --- TC-6 / TC-7: metadata mutations leave observation_hash unchanged, change artifact_hash -
+
+def _apply_metadata_mutation(observation: dict, name: str) -> dict:
+    mutated = copy.deepcopy(observation)
+    if name == "engine_source_hash":
+        mutated["implementation_provenance"]["engine_source_hash"] = "b" * 64
+    elif name == "worktree_dirty":
+        mutated["implementation_provenance"]["worktree_dirty"] = not mutated["implementation_provenance"][
+            "worktree_dirty"
+        ]
+    elif name == "observations_wording":
+        mutated["observations"] = ["A completely different explanatory sentence."]
+    elif name == "generated_at_utc":
+        mutated["generated_at_utc"] = "2026-01-01T00:00:00.000000Z"
+    elif name == "session_id":
+        mutated["source"]["session_id"] = "session-different-999"
+    elif name == "settled_at_utc":
+        mutated["timing"]["settled_at_utc"] = "2026-01-01T00:00:01.000000Z"
+    else:  # pragma: no cover - guards against a typo in the mutation name table
+        raise AssertionError(f"unknown mutation {name!r}")
+    return mutated
+
+
+@pytest.mark.parametrize(
+    "mutation_name",
+    ["engine_source_hash", "worktree_dirty", "observations_wording", "generated_at_utc", "session_id", "settled_at_utc"],
+)
+def test_observation_hash_unchanged_by_metadata_mutation(mutation_name: str):
+    observation = _build()
+    mutated = _apply_metadata_mutation(observation, mutation_name)
+    assert compute_observation_hash(mutated) == compute_observation_hash(observation)
+
+
+@pytest.mark.parametrize(
+    "mutation_name",
+    ["engine_source_hash", "worktree_dirty", "observations_wording", "generated_at_utc", "session_id", "settled_at_utc"],
+)
+def test_artifact_hash_changes_with_metadata_mutation(mutation_name: str):
+    observation = _build()
+    mutated = _apply_metadata_mutation(observation, mutation_name)
+    assert compute_artifact_hash(mutated) != compute_artifact_hash(observation)
+
+
+# --- TC-8 / TC-9: provenance resolution (clean / dirty / git-unavailable; memoized) ---------
+
+class _FakeCompletedProcess:
+    def __init__(self, returncode: int, stdout: str = "") -> None:
+        self.returncode = returncode
+        self.stdout = stdout
+
+
+@pytest.fixture(autouse=True)
+def _clean_provenance_cache_after_each_test():
+    yield
+    observation_contract._reset_provenance_cache_for_tests()
+
+
+def test_provenance_clean_dirty_git_unavailable_distinct_source_hash_identical(monkeypatch):
+    def _clean_run(cmd, **kwargs):
+        if cmd[1:] == ["rev-parse", "HEAD"]:
+            return _FakeCompletedProcess(0, "abc123\n")
+        if cmd[1] == "status":
+            return _FakeCompletedProcess(0, "")
+        raise AssertionError(f"unexpected git command: {cmd}")
+
+    monkeypatch.setattr(observation_contract.subprocess, "run", _clean_run)
+    observation_contract._reset_provenance_cache_for_tests()
+    clean = resolve_implementation_provenance()
+
+    def _dirty_run(cmd, **kwargs):
+        if cmd[1:] == ["rev-parse", "HEAD"]:
+            return _FakeCompletedProcess(0, "abc123\n")
+        if cmd[1] == "status":
+            return _FakeCompletedProcess(0, " M apps/backend/app/observation_contract.py\n")
+        raise AssertionError(f"unexpected git command: {cmd}")
+
+    monkeypatch.setattr(observation_contract.subprocess, "run", _dirty_run)
+    observation_contract._reset_provenance_cache_for_tests()
+    dirty = resolve_implementation_provenance()
+
+    def _unavailable_run(cmd, **kwargs):
+        raise FileNotFoundError("git not found")
+
+    monkeypatch.setattr(observation_contract.subprocess, "run", _unavailable_run)
+    observation_contract._reset_provenance_cache_for_tests()
+    unavailable = resolve_implementation_provenance()
+
+    assert clean[1:] == ("abc123", False)
+    assert dirty[1:] == ("abc123", True)
+    assert unavailable[1:] == (None, None)
+    # engine_source_hash is computed independently of git -- identical in every case.
+    assert clean[0] == dirty[0] == unavailable[0]
+    assert len(clean[0]) == 64
+    int(clean[0], 16)  # valid hex
+
+
+def test_provenance_resolver_memoized_across_repeated_calls(monkeypatch):
+    calls: list = []
+
+    def _counting_run(cmd, **kwargs):
+        calls.append(tuple(cmd))
+        if cmd[1:] == ["rev-parse", "HEAD"]:
+            return _FakeCompletedProcess(0, "abc123\n")
+        return _FakeCompletedProcess(0, "")
+
+    monkeypatch.setattr(observation_contract.subprocess, "run", _counting_run)
+    observation_contract._reset_provenance_cache_for_tests()
+
+    resolve_implementation_provenance()
+    calls_after_first_resolution = len(calls)
+    assert calls_after_first_resolution > 0
+
+    for _ in range(4):
+        resolve_implementation_provenance()
+
+    # Memoized -- calling 4 more times issues ZERO additional git subprocess invocations.
+    assert len(calls) == calls_after_first_resolution
+
+
+# --- TC-10: engine-source module tuple equals the sorted app/engine/*.py glob --------------
+
+def test_engine_source_modules_equals_sorted_glob():
+    actual = sorted(p.name for p in observation_contract._ENGINE_DIR.glob("*.py"))
+    assert list(observation_contract.ENGINE_SOURCE_MODULES) == actual
+
+
+def test_counterexample_engine_source_modules_detects_extra_module(tmp_path):
+    for name in observation_contract.ENGINE_SOURCE_MODULES:
+        (tmp_path / name).write_text("# copy\n")
+    (tmp_path / "zzz_throwaway.py").write_text("# should be detected as drift\n")
+    actual = sorted(p.name for p in tmp_path.glob("*.py"))
+    assert list(observation_contract.ENGINE_SOURCE_MODULES) != actual
... [diff_bound] apps/backend/tests/test_tape_observation_projection.py: 109 more diff lines omitted — Read the file for full detail
```
