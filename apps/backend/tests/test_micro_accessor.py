"""``micro_accessor.py`` (Era "The Rapid Microscope" J-05) -- the origin-fenced accessor. Test-
first contract: TC-1, TC-2, TC-3, TC-14 in ``docs/phases/goal-rapid-microscope-iter-5.md``."""

from __future__ import annotations

import ast
import pathlib

import pytest

from app.config import CONFIG
from app.research import micro_accessor as ma
from app.research.datasets import DatasetNotFound, DatasetStore
from app.research.micro_snapshots import build_snapshot_rows, resolve_micro_snapshots_dir, write_snapshot, snapshot_identity
from tests.test_micro_observer import _events_for_store

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_APP_DIR = pathlib.Path(__file__).resolve().parent.parent / "app"
_RESEARCH_DIR = _APP_DIR / "research"


def _plant_dataset_and_snapshot(
    dataset_store: DatasetStore, snapshots_dir: str, *, symbol: str, window_start_utc: str, window_end_utc: str
) -> dict:
    """A tiny, REAL dataset (via ``DatasetStore.record``, the ``test_micro_snapshots.py`` ``_plant``
    precedent) plus its already-built snapshot on disk -- so ``MicroAccessor.read_snapshot_rows``
    has real rows to serve on the un-fenced-out path."""
    dataset_meta = dataset_store.record(
        symbol=symbol, source="fixture", source_kind="fixture", source_id="fixture",
        split="train", window_start_utc=window_start_utc, window_end_utc=window_end_utc,
        data_feed="sip", epoch_anchor=0.0, events=_events_for_store(),
    )
    rows = build_snapshot_rows(dataset_store, dataset_meta["id"], CONFIG, quote_size_unit="unverified")
    identity = snapshot_identity(dataset_meta, CONFIG)
    write_snapshot(snapshots_dir, dataset_meta["id"], rows, {**identity, "quote_size_unit": "unverified"})
    return dataset_meta


@pytest.fixture
def rig(tmp_path):
    dataset_store = DatasetStore(tmp_path / "datasets")
    snapshots_dir = resolve_micro_snapshots_dir(str(tmp_path / "datasets"))
    return dataset_store, snapshots_dir


# === TC-1: the origin fence ==========================================================================


def test_tc1_a_read_at_or_before_origin_succeeds(rig):
    dataset_store, snapshots_dir = rig
    before = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="AAA",
        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
    )
    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin="2026-06-09")
    rows = accessor.read_snapshot_rows(before["id"])
    assert len(rows) > 0


def test_tc1_a_read_strictly_after_origin_raises_a_typed_error_never_empty(rig):
    dataset_store, snapshots_dir = rig
    _before = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="AAA",
        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
    )
    after = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="BBB",
        window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z",
    )
    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin="2026-06-09")
    with pytest.raises(ma.MicroAccessorOriginFenceError):
        accessor.read_snapshot_rows(after["id"])


def test_tc1_origin_equal_to_the_dataset_session_date_is_visible_the_fence_is_inclusive(rig):
    dataset_store, snapshots_dir = rig
    same_day = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="CCC",
        window_start_utc="2026-06-09T13:00:00Z", window_end_utc="2026-06-09T13:01:00Z",
    )
    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin="2026-06-09")
    rows = accessor.read_snapshot_rows(same_day["id"])
    assert len(rows) > 0


def test_tc1_unfenced_mode_origin_none_serves_every_session_date(rig):
    """The disclosed unfenced mode (``micro_join.py``/``scout.py``'s own re-point) -- ``origin=None``
    is the explicit default, never a silent no-op."""
    dataset_store, snapshots_dir = rig
    after = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="DDD",
        window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z",
    )
    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin=None)
    rows = accessor.read_snapshot_rows(after["id"])
    assert len(rows) > 0


def test_tc1_a_dataset_id_that_does_not_exist_raises_dataset_not_found_never_swallowed(rig):
    dataset_store, snapshots_dir = rig
    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin="2026-06-09")
    with pytest.raises(DatasetNotFound):
        accessor.read_snapshot_rows("does-not-exist")


# === TR-3: the accessor origin-fence -- explicitly-labeled trap-suite entry (spec section 9) ========
# goal-rapid-microscope-iter-16 (J-10): TR-3 requires three proven clauses. (a) The single-read
# origin fence is proven by the TC-1 tests directly above -- test_tc1_a_read_at_or_before_origin_
# succeeds / test_tc1_a_read_strictly_after_origin_raises_a_typed_error_never_empty / test_tc1_
# origin_equal_to_the_dataset_session_date_is_visible_the_fence_is_inclusive -- folded in
# unchanged, never re-derived. (b) The multi-session AGGREGATE-boundary proof lives in
# test_walkforward.py (test_tr3_an_origin_fenced_loop_over_several_sessions_returns_exactly_the_
# set_le_origin) -- see that file's own TR-3 note for why: direct code inspection found no
# production call site actually constructs MicroAccessor(origin=...) today (both micro_join.py/
# scout.py pass origin=None; walkforward.py's build_folds never touches the accessor), so this is
# a NEW test, not a pointer to existing code, and production edits to micro_accessor.py/
# walkforward.py are out of scope this round. (c) The import-ban is proven by the TC-3 section
# below -- test_tc3_no_module_other_than_micro_accessor_imports_read_snapshot_rows / test_tc3_the_
# guard_also_catches_a_module_qualified_call_that_imports_no_banned_name / test_tc3_micro_join_
# and_scout_no_longer_import_read_snapshot_rows_directly / test_tc3_import_ban_guard_can_fail_on_a_
# seeded_violation (its own non-vacuity proof, already existing) -- folded in unchanged. The test
# immediately below is the ORIGIN-FENCE clause's own non-vacuity mutation-proof (this round's
# binding rule -- iteration 15's own opaque-pool regression test was proven structurally unable to
# fail; every new trap this round must prove the opposite). Deliberately unnumbered (no bare
# "tcN" prefix): this file's own TC-2/TC-3/TC-4 already name OTHER, unrelated concepts (sealed-
# shard invisibility; the micro_join/scout re-point) under this era's historical per-file
# numbering, so this round's new tests carry only the globally-unambiguous "tr3"/"tr22"/"tr26"
# spec-trap tags, never a reused bare TC number.


def test_tr3_weakening_the_origin_fence_comparison_makes_the_guarding_assertion_fail_restoring_it_passes(
    rig, monkeypatch
):
    """Deliberately defeat the origin-fence comparison (monkeypatch the session-date resolver so
    EVERY dataset reports a date at/before any origin -- the exact effect of a comparison that never
    refuses) and show the read TC-1 requires to be REFUSED instead silently SUCCEEDS, leaking the
    strictly-after-origin dataset's rows; restore (``monkeypatch.undo()``) and show the refusal
    fires again, byte-identically to the shipped fence."""
    dataset_store, snapshots_dir = rig
    after = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="LEAK",
        window_start_utc="2026-06-10T13:00:00Z", window_end_utc="2026-06-10T13:01:00Z",
    )
    accessor = ma.MicroAccessor(dataset_store, snapshots_dir, CONFIG, origin="2026-06-09")

    # Sanity: the shipped fence genuinely refuses this read before any mutation.
    with pytest.raises(ma.MicroAccessorOriginFenceError):
        accessor.read_snapshot_rows(after["id"])

    # Weaken: defeat the comparison by making the session-date resolver always report a date
    # at/before the origin -- the exact effect of the defect TR-3 exists to catch.
    monkeypatch.setattr(ma, "_session_date_for_dataset", lambda dataset_meta: "2000-01-01")
    leaked_rows = accessor.read_snapshot_rows(after["id"])  # would raise if the fence still worked
    assert leaked_rows, "the weakened fence leaked the strictly-after-origin dataset's rows"

    # Restore: undo the monkeypatch and prove the fence refuses again, byte-identically.
    monkeypatch.undo()
    with pytest.raises(ma.MicroAccessorOriginFenceError):
        accessor.read_snapshot_rows(after["id"])


# === TC-2: sealed-shard invisibility =================================================================


def test_tc2_a_sealed_dataset_id_raises_and_carries_only_opaque_metadata_never_rows(rig):
    dataset_store, snapshots_dir = rig
    sealed = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="EEE",
        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
    )
    accessor = ma.MicroAccessor(
        dataset_store, snapshots_dir, CONFIG, sealed_dataset_ids=frozenset({sealed["id"]})
    )
    with pytest.raises(ma.MicroAccessorSealedShardError) as excinfo:
        accessor.read_snapshot_rows(sealed["id"])
    assert excinfo.value.opaque_metadata == {"shard_id": sealed["id"], "status": "sealed"}
    assert "rows" not in vars(excinfo.value) and not hasattr(excinfo.value, "rows")


def test_tc2_an_unsealed_dataset_is_unaffected_by_an_unrelated_sealed_id(rig):
    dataset_store, snapshots_dir = rig
    open_one = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="FFF",
        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
    )
    accessor = ma.MicroAccessor(
        dataset_store, snapshots_dir, CONFIG, sealed_dataset_ids=frozenset({"some-other-id"})
    )
    rows = accessor.read_snapshot_rows(open_one["id"])
    assert len(rows) > 0


def test_tc2_sealed_check_takes_priority_over_the_origin_fence(rig):
    """A sealed dataset dated BEFORE origin is still refused as sealed, not silently let through
    because it would have passed the fence -- sealed invisibility is unconditional."""
    dataset_store, snapshots_dir = rig
    sealed = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="GGG",
        window_start_utc="2026-06-01T13:00:00Z", window_end_utc="2026-06-01T13:01:00Z",
    )
    accessor = ma.MicroAccessor(
        dataset_store, snapshots_dir, CONFIG, origin="2026-06-09",
        sealed_dataset_ids=frozenset({sealed["id"]}),
    )
    with pytest.raises(ma.MicroAccessorSealedShardError):
        accessor.read_snapshot_rows(sealed["id"])


# === TC-3: the import-ban source-scan (the test_referee_guards.py AST precedent) ====================


def _imported_module_names(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
            for alias in node.names:
                names.add(alias.name)
                if node.module:
                    names.add(f"{node.module}.{alias.name}")
    return names


def _dotted_source(node: ast.AST) -> str | None:
    """``micro_snapshots.read_snapshot_rows`` -> ``"micro_snapshots"`` for the attribute's OWN
    value; ``None`` when the value is not a plain dotted name (e.g. ``MicroAccessor(...).read_
    snapshot_rows(...)``, whose value is a Call -- the LEGAL door, never a raw-opener reference)."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _raw_opener_references(path: pathlib.Path) -> set[str]:
    """Every reference to the RAW snapshot-row opener in one source file: an import of the name
    itself (``from .micro_snapshots import read_snapshot_rows``, ``import ...read_snapshot_rows``)
    OR a module-qualified attribute call on the module that defines it
    (``micro_snapshots.read_snapshot_rows(...)`` -- the bypass a pure import-scan misses, since
    ``from . import micro_snapshots`` imports no banned NAME at all)."""
    references = {name for banned in _BANNED_RAW_OPENERS for name in _imported_module_names(path) if name.split(".")[-1] == banned}
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in _BANNED_RAW_OPENERS:
            source = _dotted_source(node.value)
            if source is not None and source.split(".")[-1] == _RAW_OPENER_DEFINER:
                references.add(f"{source}.{node.attr}")
    return references


_BANNED_RAW_OPENERS = ("read_snapshot_rows",)
_RAW_OPENER_DEFINER = "micro_snapshots"
_ALLOWED_IMPORTER = "micro_accessor.py"


def test_tc3_no_module_other_than_micro_accessor_imports_read_snapshot_rows():
    """TC-3, verbatim: "given the FULL BACKEND SOURCE TREE ... no module other than
    ``micro_accessor.py`` contains an import of ``read_snapshot_rows``". Scanned over ALL of
    ``app/`` recursively (``engine/``, ``mcp/``, ``providers/``, ``research/``, and the package
    root alike) -- not ``app/research/*.py`` alone, which would leave every other package free to
    open the raw reader with the guard still green."""
    app_files = sorted(p for p in _APP_DIR.rglob("*.py") if "__pycache__" not in p.parts)
    assert len(app_files) > 50, f"only {len(app_files)} app modules scanned -- has the tree moved?"
    assert any(p.parent.name == "engine" for p in app_files), "app/engine not covered -- scan is too narrow"
    checked_the_allowed_importer = False
    violations: dict[str, set[str]] = {}
    for path in app_files:
        references = _raw_opener_references(path)
        if path.name == _ALLOWED_IMPORTER:
            checked_the_allowed_importer = True
            continue
        if references:
            violations[str(path.relative_to(_APP_DIR))] = references
    assert not violations, f"raw snapshot-row opener referenced outside micro_accessor.py: {violations}"
    assert checked_the_allowed_importer, f"{_ALLOWED_IMPORTER} not found -- has it moved?"


def test_tc3_the_guard_also_catches_a_module_qualified_call_that_imports_no_banned_name(tmp_path):
    """The bypass a pure import-scan cannot see: ``from . import micro_snapshots`` imports only the
    MODULE name (never ``read_snapshot_rows``), then calls the raw opener as an attribute. The
    guard must flag it -- and must NOT flag the LEGAL ``MicroAccessor(...).read_snapshot_rows(...)``
    call ``micro_join.py``/``scout.py`` now make."""
    bypass = tmp_path / "bypass.py"
    bypass.write_text(
        "from . import micro_snapshots\n"
        "def read(d, i):\n"
        "    return micro_snapshots.read_snapshot_rows(d, i)\n"
    )
    assert _raw_opener_references(bypass) == {"micro_snapshots.read_snapshot_rows"}

    legal = tmp_path / "legal.py"
    legal.write_text(
        "from .micro_accessor import MicroAccessor\n"
        "def read(store, d, cfg, i):\n"
        "    return MicroAccessor(store, d, cfg).read_snapshot_rows(i)\n"
    )
    assert _raw_opener_references(legal) == set()


def test_tc3_micro_join_and_scout_no_longer_import_read_snapshot_rows_directly():
    """The concrete re-point this iteration performs (TC-4/TC-5's own precondition) -- named
    explicitly so a reviewer sees the two call sites the plan identified are actually gone,
    not merely covered by the generic glob above."""
    for filename in ("micro_join.py", "scout.py"):
        path = _RESEARCH_DIR / filename
        imported = _imported_module_names(path)
        hit = {name for name in imported if name.split(".")[-1] == "read_snapshot_rows"}
        assert not hit, f"{filename} still imports read_snapshot_rows directly: {hit}"


def test_tc3_import_ban_guard_can_fail_on_a_seeded_violation():
    """The lint CAN fail -- a lint that cannot fail proves nothing (the test_referee_guards.py
    precedent, this codebase's own established per-guard pattern)."""
    seeded_imports = {"app.research.micro_snapshots.read_snapshot_rows", "app.research.other"}
    hits = {name for banned in _BANNED_RAW_OPENERS for name in seeded_imports if name.split(".")[-1] == banned}
    assert hits == {"app.research.micro_snapshots.read_snapshot_rows"}


# === ExposureRegistry: log/query + r2 initialization (TC-14) ========================================


def test_exposure_registry_log_and_query_roundtrip(tmp_path):
    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
    registry.log_exposure(
        corpus_id="legacy_tick", window="2026-06-08", surface="test",
        logged_at="2026-06-09T00:00:00.000000Z",
    )
    assert registry.is_exposed_before(
        corpus_id="legacy_tick", window="2026-06-08", instant="2026-06-10T00:00:00.000000Z"
    )
    assert not registry.is_exposed_before(
        corpus_id="legacy_tick", window="2026-06-08", instant="2026-06-08T00:00:00.000000Z"
    )
    assert not registry.is_exposed_before(
        corpus_id="OTHER_CORPUS", window="2026-06-08", instant="2026-06-10T00:00:00.000000Z"
    )


def test_exposure_registry_chain_is_verified(tmp_path):
    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
    registry.log_exposure(corpus_id="c", window="2026-06-08", surface="s", logged_at="2026-06-09T00:00:00Z")
    assert registry.verify_chain()["ok"] is True


def test_tc14_r2_initialization_pre_marks_every_named_window_exposed_before_any_serving_act(tmp_path):
    """given a freshly initialized exposure registry, when any window of the (here, a small
    stand-in) corpus is queried for its exposure state, then it reads already-exposed from r2
    initialization, before any explicit serving act in this run."""
    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
    windows = ["2026-06-08", "2026-06-09", "2026-06-10"]
    n = ma.initialize_r2_exposure_registry(registry, corpus_id="legacy_tick", windows=windows)
    assert n == 3
    for window in windows:
        # ANY later instant reads already-exposed -- no explicit log_exposure call happened this run.
        assert registry.is_exposed_before(
            corpus_id="legacy_tick", window=window, instant="2026-08-17T00:00:00.000000Z"
        )
    # A window this corpus never named is honestly NOT pre-marked.
    assert not registry.is_exposed_before(
        corpus_id="legacy_tick", window="2099-01-01", instant="2026-08-17T00:00:00.000000Z"
    )
    # A genuinely new corpus_id this run never initialized starts clean.
    assert not registry.is_exposed_before(
        corpus_id="brand_new_synthetic_corpus", window="2026-06-08",
        instant="2026-08-17T00:00:00.000000Z",
    )


# === the "two callers, two disciplines" exposure-logging boundary (module docstring) ================


def test_unfenced_mode_never_logs_exposure_even_when_a_registry_is_supplied(rig, tmp_path):
    dataset_store, snapshots_dir = rig
    dataset_meta = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="HHH",
        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
    )
    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
    accessor = ma.MicroAccessor(
        dataset_store, snapshots_dir, CONFIG, origin=None,
        exposure_registry=registry, corpus_id="legacy_tick",
    )
    accessor.read_snapshot_rows(dataset_meta["id"])
    assert registry.all_rows() == []


def test_origin_fenced_mode_with_a_registry_logs_exactly_one_exposure_entry(rig, tmp_path):
    dataset_store, snapshots_dir = rig
    dataset_meta = _plant_dataset_and_snapshot(
        dataset_store, snapshots_dir, symbol="III",
        window_start_utc="2026-06-08T13:00:00Z", window_end_utc="2026-06-08T13:01:00Z",
    )
    registry = ma.ExposureRegistry(str(tmp_path / "exposure"))
    accessor = ma.MicroAccessor(
        dataset_store, snapshots_dir, CONFIG, origin="2026-06-09",
        exposure_registry=registry, corpus_id="a_corpus", surface="walkforward_test",
    )
    accessor.read_snapshot_rows(dataset_meta["id"], logged_at="2026-06-09T05:00:00.000000Z")
    rows = registry.all_rows()
    assert len(rows) == 1
    assert rows[0]["corpus_id"] == "a_corpus"
    assert rows[0]["window"] == "2026-06-08"
    assert rows[0]["surface"] == "walkforward_test"
    assert rows[0]["logged_at"] == "2026-06-09T05:00:00.000000Z"
