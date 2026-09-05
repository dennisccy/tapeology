"""Observation Contract v1 -- Binding Execution Order step 1 (J-01; docs/goal.md).

Covers ``app/observation_contract.py``'s pure builder, schema constants, four-group partition
and the two hash laws. TC references below match the iteration spec
(``docs/phases/goal-observation-contract-iter-1.md``) and goal.md's J-01 Steps.4 list. Every
guard/law test ships a named ``test_counterexample_*`` proving it can fail (never a vacuous
assertion). No test in this module needs a running uvicorn server or network access (the route,
``GET /tape/{ticker}/observation``, is proven separately by ``test_tape_observation_route.py``).
"""

from __future__ import annotations

import ast
import copy
from dataclasses import replace
from pathlib import Path

import pytest

from app import observation_contract
from app.config import CONFIG, Config
from app.engine import classifier as classifier_module
from app.engine.snapshot import EngineSnapshot
from app.observation_contract import (
    ENGINE_SEMANTICS_VERSION,
    build_tape_observation,
    canonical_encode,
    compute_artifact_hash,
    compute_observation_hash,
    field_partition_map,
    resolve_implementation_provenance,
)

OBS_CONTRACT_PATH = Path(observation_contract.__file__)
SPEC_PATH = Path(__file__).resolve().parents[3] / "docs" / "observation-contract-spec.md"


# --- Fixtures / small builders -------------------------------------------------------------

def _make_snapshot(**overrides: object) -> EngineSnapshot:
    defaults: dict = dict(
        ticker="SIM-BIDABS",
        scenario="bid_absorption",
        timestamp=67.25,
        event_count=17,
        warm=True,
        stream_status="live",
        bid=149.01,
        ask=149.03,
        spread=0.02,
        last=149.02,
        features={"30s": {"aggressive_sell_ratio": 0.8, "bid_refresh_score": 0.7}},
        primary_window="30s",
        tape_state="bid_absorption",
        confidence=0.83,
        observations=("Heavy sell volume being absorbed",),
        paused=False,
        epoch_anchor=1704205800.0,
        delivery_lag_seconds=0.0,
    )
    defaults.update(overrides)
    return EngineSnapshot(**defaults)


def _valid_provenance() -> tuple[str, str | None, bool | None]:
    return ("a" * 64, "abc123def456", False)


def _build(snapshot: EngineSnapshot | None = None, **overrides: object) -> dict:
    snapshot = snapshot if snapshot is not None else _make_snapshot()
    kwargs: dict = dict(
        snapshot=snapshot,
        source_mode="sim",
        data_feed="sim",
        window_start_utc=None,
        window_end_utc=None,
        dataset_id=None,
        dataset_checksum=None,
        session_id="session-abc-123",
        session_started_at_utc="2026-09-02T13:04:59.000000Z",
        settled_at_utc="2026-09-02T13:05:41.104913Z",
        end_reason=None,
        generated_at_utc="2026-09-02T13:05:41.118204Z",
        profile_id="default",
        config=CONFIG,
        provenance=_valid_provenance(),
    )
    kwargs.update(overrides)
    return build_tape_observation(**kwargs)


# --- TC-1: sentinel mutation projected verbatim (no recomputation) -------------------------

def test_sentinel_mutation_projected_verbatim():
    snapshot = _make_snapshot(
        tape_state="bid_absorption",
        confidence=0.83,
        features={"30s": {"sentinel_feature": 12.5}},
    )
    observation = _build(snapshot=snapshot)
    assert observation["tape_state"] == "bid_absorption"
    assert observation["confidence"] == 0.83
    assert observation["features"] == {"30s": {"sentinel_feature": 12.5}}
    assert observation["warm"] is True
    assert observation["primary_window"] == "30s"


# --- TC-2: recompute guard (no classifier/feature import, no threshold literal) ------------

def _classifier_threshold_field_names() -> set[str]:
    """Every ``c.<name>`` attribute access inside classifier.py's source -- the classifier's
    OWN threshold/scale field names, read dynamically so this can never silently drift."""
    source = Path(classifier_module.__file__).read_text()
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "c":
            names.add(node.attr)
    return names


def _classifier_threshold_values() -> set[float]:
    values: set[float] = set()
    for name in _classifier_threshold_field_names():
        value = getattr(CONFIG, name, None)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values.add(float(value))
    return values


def _numeric_literals(source: str) -> set[float]:
    tree = ast.parse(source)
    literals: set[float] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(
            node.value, bool
        ):
            literals.add(float(node.value))
    return literals


def _recompute_guard_violations(source: str) -> list[str]:
    violations: list[str] = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.endswith("engine.classifier") or node.module.endswith("engine.features"):
                violations.append(f"import from {node.module}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.endswith("engine.classifier") or alias.name.endswith("engine.features"):
                    violations.append(f"import {alias.name}")
    thresholds = _classifier_threshold_values()
    for literal in _numeric_literals(source):
        if literal in thresholds:
            violations.append(f"numeric literal {literal} matches a classifier threshold")
    return violations


def test_recompute_guard_no_classifier_or_feature_import_or_threshold_literal():
    source = OBS_CONTRACT_PATH.read_text()
    assert _recompute_guard_violations(source) == []


def test_counterexample_recompute_guard_detects_classifier_import():
    fixture_source = "from app.engine.classifier import STATE_BUYER_CONTROL\nX = STATE_BUYER_CONTROL\n"
    assert _recompute_guard_violations(fixture_source) != []


def test_counterexample_recompute_guard_detects_threshold_literal():
    threshold_value = CONFIG.min_aggressive_buy_ratio
    fixture_source = f"THRESHOLD = {threshold_value!r}\n"
    assert _recompute_guard_violations(fixture_source) != []


def test_tape_state_vocabulary_matches_classifier_states():
    classifier_states = {
        classifier_module.STATE_BUYER_CONTROL,
        classifier_module.STATE_SELLER_CONTROL,
        classifier_module.STATE_BID_ABSORPTION,
        classifier_module.STATE_ASK_ABSORPTION,
        classifier_module.STATE_UNCLEAR,
    }
    assert set(observation_contract.TAPE_STATE_VOCABULARY) == classifier_states


# --- TC-3: trade_event_count verbatim, no re-count ------------------------------------------

def test_trade_event_count_equals_snapshot_event_count_verbatim():
    snapshot = _make_snapshot(event_count=17)
    observation = _build(snapshot=snapshot)
    assert observation["trade_event_count"] == 17


def test_source_scan_builder_has_no_loop_over_trade_data():
    source = OBS_CONTRACT_PATH.read_text()
    # Deliberately-excluded panel fields (Constitution §1) -- their mere presence as a string
    # in this module would already be suspicious; their absence also proves no re-count over
    # either list is possible here.
    assert "recent_trades" not in source
    assert "event_log" not in source
    tree = ast.parse(source)
    builder = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "build_tape_observation"
    )
    assert not any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(builder))


# --- TC-4: both hashes recomputable; key-order permutation changes neither -----------------

def _reverse_dict_order(obj: object) -> object:
    if isinstance(obj, dict):
        return {key: _reverse_dict_order(obj[key]) for key in reversed(list(obj.keys()))}
    if isinstance(obj, list):
        return [_reverse_dict_order(item) for item in obj]
    return obj


def test_hashes_recomputable_and_key_order_independent():
    observation = _build()
    recomputed_observation_hash = compute_observation_hash(observation)
    recomputed_artifact_hash = compute_artifact_hash(observation)
    assert recomputed_observation_hash == observation["observation_hash"]
    assert recomputed_artifact_hash == observation["artifact_hash"]

    reversed_observation = _reverse_dict_order(observation)
    assert compute_observation_hash(reversed_observation) == observation["observation_hash"]
    assert compute_artifact_hash(reversed_observation) == observation["artifact_hash"]


def test_counterexample_hash_functions_are_not_vacuously_constant():
    observation_a = _build()
    observation_b = _build(snapshot=_make_snapshot(tape_state="seller_control", confidence=0.71))
    assert compute_observation_hash(observation_a) != compute_observation_hash(observation_b)
    assert compute_artifact_hash(observation_a) != compute_artifact_hash(observation_b)


# --- TC-5: observation_hash changes with engine_semantics_version/config_fingerprint/profile_id

def test_observation_hash_changes_with_engine_semantics_version():
    observation = _build()
    mutated = copy.deepcopy(observation)
    mutated["engine_identity"]["engine_semantics_version"] = "tape-engine-v2"
    assert compute_observation_hash(mutated) != compute_observation_hash(observation)


def test_observation_hash_changes_with_config_fingerprint():
    observation = _build()
    mutated = copy.deepcopy(observation)
    mutated["engine_identity"]["config_fingerprint"] = "deadbeefdeadbeef"
    assert compute_observation_hash(mutated) != compute_observation_hash(observation)


def test_observation_hash_changes_with_profile_id():
    observation = _build()
    mutated = copy.deepcopy(observation)
    mutated["engine_identity"]["profile_id"] = "candidate_faster_warmup"
    assert compute_observation_hash(mutated) != compute_observation_hash(observation)


# --- TC-6 / TC-7: metadata mutations leave observation_hash unchanged, change artifact_hash -

def _apply_metadata_mutation(observation: dict, name: str) -> dict:
    mutated = copy.deepcopy(observation)
    if name == "engine_source_hash":
        mutated["implementation_provenance"]["engine_source_hash"] = "b" * 64
    elif name == "worktree_dirty":
        mutated["implementation_provenance"]["worktree_dirty"] = not mutated["implementation_provenance"][
            "worktree_dirty"
        ]
    elif name == "observations_wording":
        mutated["observations"] = ["A completely different explanatory sentence."]
    elif name == "generated_at_utc":
        mutated["generated_at_utc"] = "2026-01-01T00:00:00.000000Z"
    elif name == "session_id":
        mutated["source"]["session_id"] = "session-different-999"
    elif name == "settled_at_utc":
        mutated["timing"]["settled_at_utc"] = "2026-01-01T00:00:01.000000Z"
    else:  # pragma: no cover - guards against a typo in the mutation name table
        raise AssertionError(f"unknown mutation {name!r}")
    return mutated


@pytest.mark.parametrize(
    "mutation_name",
    ["engine_source_hash", "worktree_dirty", "observations_wording", "generated_at_utc", "session_id", "settled_at_utc"],
)
def test_observation_hash_unchanged_by_metadata_mutation(mutation_name: str):
    observation = _build()
    mutated = _apply_metadata_mutation(observation, mutation_name)
    assert compute_observation_hash(mutated) == compute_observation_hash(observation)


@pytest.mark.parametrize(
    "mutation_name",
    ["engine_source_hash", "worktree_dirty", "observations_wording", "generated_at_utc", "session_id", "settled_at_utc"],
)
def test_artifact_hash_changes_with_metadata_mutation(mutation_name: str):
    observation = _build()
    mutated = _apply_metadata_mutation(observation, mutation_name)
    assert compute_artifact_hash(mutated) != compute_artifact_hash(observation)


# --- TC-8 / TC-9: provenance resolution (clean / dirty / git-unavailable; memoized) ---------

class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


@pytest.fixture(autouse=True)
def _clean_provenance_cache_after_each_test():
    yield
    observation_contract._reset_provenance_cache_for_tests()


def test_provenance_clean_dirty_git_unavailable_distinct_source_hash_identical(monkeypatch):
    def _clean_run(cmd, **kwargs):
        if cmd[1:] == ["rev-parse", "HEAD"]:
            return _FakeCompletedProcess(0, "abc123\n")
        if cmd[1] == "status":
            return _FakeCompletedProcess(0, "")
        raise AssertionError(f"unexpected git command: {cmd}")

    monkeypatch.setattr(observation_contract.subprocess, "run", _clean_run)
    observation_contract._reset_provenance_cache_for_tests()
    clean = resolve_implementation_provenance()

    def _dirty_run(cmd, **kwargs):
        if cmd[1:] == ["rev-parse", "HEAD"]:
            return _FakeCompletedProcess(0, "abc123\n")
        if cmd[1] == "status":
            return _FakeCompletedProcess(0, " M apps/backend/app/observation_contract.py\n")
        raise AssertionError(f"unexpected git command: {cmd}")

    monkeypatch.setattr(observation_contract.subprocess, "run", _dirty_run)
    observation_contract._reset_provenance_cache_for_tests()
    dirty = resolve_implementation_provenance()

    def _unavailable_run(cmd, **kwargs):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr(observation_contract.subprocess, "run", _unavailable_run)
    observation_contract._reset_provenance_cache_for_tests()
    unavailable = resolve_implementation_provenance()

    assert clean[1:] == ("abc123", False)
    assert dirty[1:] == ("abc123", True)
    assert unavailable[1:] == (None, None)
    # engine_source_hash is computed independently of git -- identical in every case.
    assert clean[0] == dirty[0] == unavailable[0]
    assert len(clean[0]) == 64
    int(clean[0], 16)  # valid hex


def test_provenance_resolver_memoized_across_repeated_calls(monkeypatch):
    calls: list = []

    def _counting_run(cmd, **kwargs):
        calls.append(tuple(cmd))
        if cmd[1:] == ["rev-parse", "HEAD"]:
            return _FakeCompletedProcess(0, "abc123\n")
        return _FakeCompletedProcess(0, "")

    monkeypatch.setattr(observation_contract.subprocess, "run", _counting_run)
    observation_contract._reset_provenance_cache_for_tests()

    resolve_implementation_provenance()
    calls_after_first_resolution = len(calls)
    assert calls_after_first_resolution > 0

    for _ in range(4):
        resolve_implementation_provenance()

    # Memoized -- calling 4 more times issues ZERO additional git subprocess invocations.
    assert len(calls) == calls_after_first_resolution


# --- TC-10: engine-source module tuple equals the sorted app/engine/*.py glob --------------

def test_engine_source_modules_equals_sorted_glob():
    actual = sorted(p.name for p in observation_contract._ENGINE_DIR.glob("*.py"))
    assert list(observation_contract.ENGINE_SOURCE_MODULES) == actual


def test_counterexample_engine_source_modules_detects_extra_module(tmp_path):
    for name in observation_contract.ENGINE_SOURCE_MODULES:
        (tmp_path / name).write_text("# copy\n")
    (tmp_path / "zzz_throwaway.py").write_text("# should be detected as drift\n")
    actual = sorted(p.name for p in tmp_path.glob("*.py"))
    assert list(observation_contract.ENGINE_SOURCE_MODULES) != actual


# --- TC-11: profile refusal --------------------------------------------------------------

def test_profile_refusal_raises_on_fingerprint_mismatch():
    mismatched_config = replace(CONFIG, warmup_min_events=CONFIG.warmup_min_events + 1)
    with pytest.raises(ValueError):
        _build(profile_id="default", config=mismatched_config)


def test_profile_default_with_matching_fingerprint_returns_normally():
    observation = _build(profile_id="default", config=CONFIG)
    assert observation["engine_identity"]["profile_id"] == "default"
    assert observation["engine_identity"]["config_fingerprint"] == CONFIG.config_fingerprint()


# --- TC-12: four-group partition covers every leaf path exactly once -----------------------

def test_field_partition_has_no_duplicates_and_covers_every_field():
    all_paths = [path for _name, paths in observation_contract.FIELD_PARTITION_GROUPS for path in paths]
    assert len(all_paths) == len(set(all_paths))
    assert len(all_paths) == len(field_partition_map())


def test_counterexample_field_partition_duplicate_detection():
    # "observation_hash" already lives in INTEGRITY_FIELDS; duplicating it into the semantic
    # group must make the no-duplicate check above fail on data shaped like this.
    mutated_groups = (
        ("semantic", observation_contract.MACHINE_OBSERVATION_SEMANTIC_FIELDS + ("observation_hash",)),
        ("metadata", observation_contract.PROVENANCE_SOURCE_LIFECYCLE_METADATA_FIELDS),
        ("explanatory", observation_contract.EXPLANATORY_METADATA_FIELDS),
        ("integrity", observation_contract.INTEGRITY_FIELDS),
    )
    all_paths = [path for _name, paths in mutated_groups for path in paths]
    assert len(all_paths) != len(set(all_paths))


def test_build_tape_observation_has_every_partitioned_field_reachable():
    observation = _build()
    for path in field_partition_map():
        parts = path.split(".")
        value = observation
        for part in parts:
            value = value[part]  # raises KeyError if the leaf path is not actually served


# --- TC-13: schema constants / field-owner table equal the spec doc; artifact_hash rule ----

_PARTITION_NAMES = {"semantic", "metadata", "explanatory", "integrity"}


def _parse_spec_field_table(spec_text: str) -> dict[str, str]:
    """``{leaf_path: partition}`` parsed from docs/observation-contract-spec.md's
    '## 4. Fields and owners' markdown table -- the doc-lint's independent reference."""
    section = spec_text.split("## 4. Fields and owners", 1)[1]
    section = section.split("\n## 5.", 1)[0]
    result: dict[str, str] = {}
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 3:
            continue
        field_cell, _owner_cell, partition_cell = cells
        if field_cell == "Field" or field_cell.strip("-") == "":
            continue
        partition = partition_cell.strip()
        if partition not in _PARTITION_NAMES:
            continue
        for raw_field in field_cell.split(","):
            raw_field = raw_field.strip().strip("`").rstrip("[]")
            if raw_field:
                result[raw_field] = partition
    return result


def test_doclint_schema_constants_and_field_table_match_spec():
    spec_text = SPEC_PATH.read_text()
    assert f'`schema_version = "{observation_contract.OBSERVATION_SCHEMA_VERSION}"`' in spec_text
    assert f'`provider = "{observation_contract.PROVIDER}"`' in spec_text

    spec_field_table = _parse_spec_field_table(spec_text)
    assert field_partition_map() == spec_field_table


def test_doclint_spec_states_artifact_hash_is_the_evidence_reference():
    spec_text = SPEC_PATH.read_text()
    assert "references `artifact_hash`" in spec_text


# --- ENGINE_SEMANTICS_VERSION constant (tape_engine.py) -------------------------------------

def test_engine_semantics_version_constant():
    assert ENGINE_SEMANTICS_VERSION == "tape-engine-v1"
    observation = _build()
    assert observation["engine_identity"]["engine_semantics_version"] == "tape-engine-v1"


# --- Error cases -----------------------------------------------------------------------------

def test_incomplete_engine_snapshot_rejected_by_dataclass_typing():
    with pytest.raises(TypeError):
        EngineSnapshot()  # type: ignore[call-arg]


def test_canonical_encode_is_sorted_and_compact():
    encoded = canonical_encode({"b": 1, "a": 2})
    assert encoded == b'{"a":2,"b":1}'
