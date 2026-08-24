"""Regression coverage for ``scripts/seed_micro_snapshots_iter33_disclosure_fixture.py`` (Era
"The Rapid Microscope", goal-rapid-microscope-iter-33, J-12's "fixture-scoped" browser-QA capture,
TC-2) -- a guard for the FIXTURE SCRIPT itself, not for production code (the script imports and
calls ``micro_snapshots.py``/``vault.py`` exactly as shipped; see the phase spec's OUT OF SCOPE
list). Asserts the seed script's own fixture is well-formed end to end: the valid snapshot serves
every identity field, the stale meta never appears as a row, and the withheld member never appears
as a row -- with both disclosure counts exactly ``1`` -- and that the CLI entry point (``main``)
runs its own self-check and exits clean on a fresh root."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

import seed_micro_snapshots_iter33_disclosure_fixture as seed  # noqa: E402

from app.config import CONFIG  # noqa: E402
from app.research import micro_snapshots as ms  # noqa: E402
from app.research.datasets import DatasetStore  # noqa: E402


def _report_for(root: Path, planted: dict) -> dict:
    dataset_store = DatasetStore(Path(planted["dataset_dir"]))
    return ms.snapshot_meta_report(planted["snapshots_dir"], dataset_store, CONFIG)


def test_the_valid_snapshot_serves_every_identity_field_and_the_other_two_are_excluded(tmp_path):
    planted = seed.plant_disclosure_fixture(tmp_path)
    report = _report_for(tmp_path, planted)

    assert len(report["snapshots"]) == 1
    row = report["snapshots"][0]
    assert row["dataset_id"] == planted["valid_dataset_id"]
    for key in (
        "dataset_id", "dataset_checksum", "micro_algo_version", "snapshot_format_version",
        "feature_source_hash", "config_fingerprint", "params_hash", "quote_size_unit",
        "row_count", "bytes_on_disk", "built_utc",
    ):
        assert key in row, f"the valid snapshot's own served meta is missing {key!r}"

    served_ids = {r["dataset_id"] for r in report["snapshots"]}
    assert planted["stale_dataset_id"] not in served_ids
    assert planted["withheld_dataset_id"] not in served_ids
    assert report["stale_excluded"] == 1
    assert report["withheld_excluded"] == 1


def test_the_stale_meta_never_carries_its_stale_value_anywhere(tmp_path):
    """TR-7: `load_snapshot_meta` must MISS on the mutated meta, never re-serving the mutated
    (or the original, pre-mutation) identity as a current row."""
    planted = seed.plant_disclosure_fixture(tmp_path)
    dataset_store = DatasetStore(Path(planted["dataset_dir"]))
    loaded = ms.load_snapshot_meta(
        planted["snapshots_dir"], dataset_store, planted["stale_dataset_id"], CONFIG
    )
    assert loaded is None


def test_main_runs_its_own_self_check_and_exits_clean(tmp_path):
    """``main`` (the CLI entry point ``TAPEOLOGY_DATASET_DIR=... .venv/bin/python scripts/
    seed_micro_snapshots_iter33_disclosure_fixture.py ROOT`` actually invokes) plants the fixture
    AND runs its own self-check against the served report before returning -- exercised here
    exactly as a QA operator would invoke it, on a fresh root."""
    exit_code = seed.main(tmp_path)
    assert exit_code == 0
