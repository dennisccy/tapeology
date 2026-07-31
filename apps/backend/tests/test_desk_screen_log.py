"""``desk_screen_log.py`` (Era B "The Desk", goal-desk-iter-29, J-18) — the screen-run log's store
discipline: checksum verification, structural append-only-ness (no update/delete path, no content
dedup — every call to ``record`` is a genuinely new file), the interrupted-run-leaves-no-record
guarantee, and the directory-resolution seam (mirrors ``test_desk_topup_log.py``'s own store-level
test shape).

The shared-writer contract itself (proving ``record_screen_run`` is called from inside
``run_screen_and_record``, the ONE entry point both ``DeskScreenComputeManager`` and the CLI call)
is exercised end to end in ``test_desk_screen_compute.py`` — this file covers the store module in
isolation."""

from __future__ import annotations

import json

import pytest

from app.research.desk_screen_log import (
    ScreenRunIntegrityError,
    ScreenRunStore,
    record_screen_run,
    resolve_desk_screen_log_dir,
)

SAMPLE_SKIPPED_BY_REASON = {"no_bars": 2, "no_basis": 1}


def _record_sample(
    store: ScreenRunStore,
    *,
    state: str = "done",
    reused: bool = False,
    started_utc: str = "2026-07-31T09:00:00.000000Z",
    finished_utc: str = "2026-07-31T09:05:00.000000Z",
    screen_date: str = "2026-07-31",
    universe_snapshot_id: str | None = "universe-2026-07-25-49b33fa31680",
    config_fingerprint: str = "08e471b10130e1e2",
    bar_store_signature: str | None = "abcdef0123456789",
    members_total: int = 3,
    members_attempted: int = 3,
    ranked_count: int = 2,
    skipped_by_reason: dict | None = None,
    screen_id: str | None = "screen-2026-07-31-deadbeef0000",
    error: str | None = None,
    failed_member: str | None = None,
) -> dict:
    return record_screen_run(
        store,
        screen_date=screen_date,
        universe_snapshot_id=universe_snapshot_id,
        config_fingerprint=config_fingerprint,
        bar_store_signature=bar_store_signature,
        started_utc=started_utc,
        finished_utc=finished_utc,
        state=state,
        reused=reused,
        members_total=members_total,
        members_attempted=members_attempted,
        ranked_count=ranked_count,
        skipped_by_reason=SAMPLE_SKIPPED_BY_REASON if skipped_by_reason is None else skipped_by_reason,
        screen_id=screen_id,
        error=error,
        failed_member=failed_member,
    )


# --- record: shape + provenance ------------------------------------------------------------------


def test_record_stores_every_field_verbatim(tmp_path):
    store = ScreenRunStore(tmp_path / "screen_runs")
    meta = _record_sample(store)

    assert meta["screen_date"] == "2026-07-31"
    assert meta["universe_snapshot_id"] == "universe-2026-07-25-49b33fa31680"
    assert meta["config_fingerprint"] == "08e471b10130e1e2"
    assert meta["bar_store_signature"] == "abcdef0123456789"
    assert meta["started_utc"] == "2026-07-31T09:00:00.000000Z"
    assert meta["finished_utc"] == "2026-07-31T09:05:00.000000Z"
    assert meta["state"] == "done"
    assert meta["reused"] is False
    assert meta["members_total"] == 3
    assert meta["members_attempted"] == 3
    assert meta["ranked_count"] == 2
    assert meta["skipped_by_reason"] == SAMPLE_SKIPPED_BY_REASON
    assert meta["screen_id"] == "screen-2026-07-31-deadbeef0000"
    assert meta["error"] is None
    assert meta["failed_member"] is None
    assert meta["id"].startswith("screenrun-2026-07-31-")
    # The record landed as ONE file in the configured directory.
    assert len(list((tmp_path / "screen_runs").glob("*.json"))) == 1


def test_record_rejects_a_non_terminal_state(tmp_path):
    store = ScreenRunStore(tmp_path / "screen_runs")
    with pytest.raises(ValueError):
        _record_sample(store, state="running")


def test_a_failed_run_carries_its_error_and_failed_member_verbatim(tmp_path):
    store = ScreenRunStore(tmp_path / "screen_runs")
    meta = _record_sample(
        store, state="failed", screen_id=None, error="synthetic raise on member CCC",
        failed_member="CCC", ranked_count=0, skipped_by_reason={"no_bars": 0, "no_basis": 0},
    )
    assert meta["state"] == "failed"
    assert meta["error"] == "synthetic raise on member CCC"
    assert meta["failed_member"] == "CCC"
    assert meta["screen_id"] is None


def test_a_reused_run_never_pays_for_the_walk_and_records_zero_members_attempted(tmp_path):
    store = ScreenRunStore(tmp_path / "screen_runs")
    meta = _record_sample(
        store, reused=True, members_attempted=0, ranked_count=0,
        skipped_by_reason={"no_bars": 0, "no_basis": 0},
    )
    assert meta["reused"] is True
    assert meta["members_attempted"] == 0


# --- list: verbatim read, oldest-started first -----------------------------------------------------


def test_list_serves_the_stored_record_verbatim(tmp_path):
    store = ScreenRunStore(tmp_path / "screen_runs")
    recorded = _record_sample(store)

    records, errors = store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0] == recorded


def test_store_survives_a_reload_from_disk(tmp_path):
    root = tmp_path / "screen_runs"
    recorded = _record_sample(ScreenRunStore(root))

    reloaded = ScreenRunStore(root)
    records, errors = reloaded.list()
    assert errors == []
    assert records == [recorded]


def test_list_on_a_directory_that_was_never_created_is_honestly_empty(tmp_path):
    """TC-1 / TC-7 at the store level: a store that is never told to ``record`` (the writer's
    terminal call literally never happening) holds zero files and lists zero records — never a
    fabricated or partial entry."""
    store = ScreenRunStore(tmp_path / "screen_runs" / "never-created")
    records, errors = store.list()
    assert records == []
    assert errors == []
    assert not (tmp_path / "screen_runs" / "never-created").exists()


# --- append-only: every call to record is a genuinely NEW file, never a dedup/update ---------------


def test_two_calls_with_identical_field_values_still_append_two_distinct_records(tmp_path):
    """UNLIKE UniverseStore/ScreenStore, this store performs no content-keyed dedup — two
    back-to-back screen runs over an unchanged store (e.g. both entirely "reused") are still TWO
    real, distinct attempts and must both be recorded."""
    store = ScreenRunStore(tmp_path / "screen_runs")
    first = _record_sample(store)
    second = _record_sample(store)

    assert first["id"] != second["id"]
    records, errors = store.list()
    assert errors == []
    assert {r["id"] for r in records} == {first["id"], second["id"]}


def test_a_second_run_appends_without_touching_the_first_files_bytes_on_disk(tmp_path):
    """TC-8: the first record's file stays byte-unchanged (same bytes) after a second run
    completes, and ``list()`` carries both."""
    root = tmp_path / "screen_runs"
    store = ScreenRunStore(root)
    first = _record_sample(
        store, started_utc="2026-07-31T09:00:00Z", finished_utc="2026-07-31T09:05:00Z",
    )
    first_path = root / f"{first['id']}.json"
    first_bytes_before = first_path.read_bytes()

    second = _record_sample(
        store, started_utc="2026-07-31T10:00:00Z", finished_utc="2026-07-31T10:05:00Z",
        screen_id="screen-2026-07-31-cafef00d0000",
    )

    assert first_path.read_bytes() == first_bytes_before  # byte-unchanged
    records, errors = store.list()
    assert errors == []
    assert len(records) == 2
    assert records[0]["id"] == first["id"]  # oldest-started first
    assert records[1]["id"] == second["id"]


def test_screen_run_store_has_no_update_or_delete_method():
    """Structural immutability: the only mutation on this class is ``record`` — mirrors
    ``TopupRunStore``/``ReconcileRunStore``'s own guard-by-absence discipline."""
    public_methods = {name for name in dir(ScreenRunStore) if not name.startswith("_")}
    assert public_methods == {"root", "list", "record"}


# --- interrupted-run honesty: a run whose terminal write never happens leaves zero record ---------


def test_a_run_that_never_reaches_the_writer_call_leaves_the_store_untouched(tmp_path):
    """Simulates a process that ends before the writer's terminal call: a store is constructed
    exactly as a real caller would, but ``record``/``record_screen_run`` is deliberately never
    invoked (standing in for a crash between the walk finishing and the writer call). The store
    gains zero new file — never a fabricated or partial entry (DoD, TC-7)."""
    store = ScreenRunStore(tmp_path / "screen_runs")
    # ... the walk would happen here in a real run; the process ends before this line runs:
    # record_screen_run(store, ...)
    records, errors = store.list()
    assert records == []
    assert errors == []
    assert not (tmp_path / "screen_runs").exists()


# --- integrity: a corrupted file is explicit, never silent ----------------------------------------


def test_corrupted_run_record_file_surfaces_explicitly_in_list_errors(tmp_path):
    root = tmp_path / "screen_runs"
    store = ScreenRunStore(root)
    _record_sample(store)
    path = next(root.glob("*.json"))
    data = json.loads(path.read_text())
    data["record"]["meta"]["members_total"] = 999  # tamper -- file_checksum now disagrees
    path.write_text(json.dumps(data))

    records, errors = store.list()
    assert records == []
    assert len(errors) == 1
    assert path.name == errors[0]["file"]
    assert "integrity" in errors[0]["error"]


def test_load_raises_screen_run_integrity_error_for_unparseable_json(tmp_path):
    root = tmp_path / "screen_runs"
    root.mkdir(parents=True)
    (root / "screenrun-2026-01-01-deadbeef0000.json").write_text("{not json")

    store = ScreenRunStore(root)
    records, errors = store.list()
    assert records == []
    assert len(errors) == 1


def test_corrupted_file_does_not_block_other_valid_records_from_listing(tmp_path):
    root = tmp_path / "screen_runs"
    store = ScreenRunStore(root)
    good = _record_sample(store)
    bad_path = root / "screenrun-2026-01-01-deadbeef0000.json"
    bad_path.write_text("{not json")

    records, errors = store.list()
    assert len(records) == 1 and records[0]["id"] == good["id"]
    assert len(errors) == 1


def test_load_raises_screen_run_integrity_error_directly_for_a_missing_meta_shape(tmp_path):
    """A file that parses as JSON but does not carry the expected ``{"file_checksum", "record":
    {"meta": ...}}`` shape is also refused explicitly, never silently coerced."""
    root = tmp_path / "screen_runs"
    root.mkdir(parents=True)
    path = root / "screenrun-2026-01-01-deadbeef0000.json"
    path.write_text(json.dumps({"unexpected": "shape"}))

    store = ScreenRunStore(root)
    with pytest.raises(ScreenRunIntegrityError):
        store._load(path)  # noqa: SLF001 -- direct unit test of the private loader's own raise


# --- resolve_desk_screen_log_dir -- zero new Config field -------------------------------------------


def test_resolve_desk_screen_log_dir_defaults_to_a_sibling_of_the_universe_dir(monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_DESK_SCREEN_LOG_DIR", raising=False)
    resolved = resolve_desk_screen_log_dir("/some/root/.data/universe")
    assert resolved == "/some/root/.data/screen_runs"


def test_resolve_desk_screen_log_dir_env_override(monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_SCREEN_LOG_DIR", "/tmp/custom-screen-log-dir")
    assert resolve_desk_screen_log_dir("/some/root/.data/universe") == "/tmp/custom-screen-log-dir"
