"""``desk_forward_log.py`` (forward-test era) — the forward-run log's store discipline: checksum
verification, structural append-only-ness (no update/delete path, no content dedup — every call to
``record`` is a genuinely new file), the interrupted-run-leaves-no-record guarantee, the
per-snapshot read, and the directory-resolution seam. Mirrors ``test_desk_screen_log.py``'s own
store-level test shape.

The shared-writer contract itself (proving ``record_forward_run`` is called from inside
``run_forward_and_record``, the ONE entry point both ``DeskForwardComputeManager`` and the CLI
call) is exercised end to end in ``test_desk_forward_compute.py`` — this file covers the store
module in isolation."""

from __future__ import annotations

import json

import pytest

from app.research.desk_forward_log import (
    ForwardRunIntegrityError,
    ForwardRunStore,
    record_forward_run,
    resolve_desk_forward_log_dir,
)


def _record_sample(
    store: ForwardRunStore,
    *,
    state: str = "done",
    reused: bool = False,
    started_utc: str = "2026-08-06T22:37:02.000000Z",
    finished_utc: str = "2026-08-06T22:37:26.000000Z",
    screen_id: str = "screen-2025-01-01-6d607a07fae6",
    screen_date: str | None = "2025-01-01",
    config_fingerprint: str = "08e471b10130e1e2",
    forward_input_signature: str | None = "3ba0e5c0c85b7555",
    rows_total: int = 100,
    rows_measured: int = 2,
    rows_absent_no_fine_bars: int = 98,
    rows_with_touches: int = 1,
    total_touches: int = 1,
    forward_id: str | None = "forward-2025-01-01-eccfa5dff487",
    error: str | None = None,
) -> dict:
    return record_forward_run(
        store,
        screen_id=screen_id,
        screen_date=screen_date,
        config_fingerprint=config_fingerprint,
        forward_input_signature=forward_input_signature,
        started_utc=started_utc,
        finished_utc=finished_utc,
        state=state,
        reused=reused,
        rows_total=rows_total,
        rows_measured=rows_measured,
        rows_absent_no_fine_bars=rows_absent_no_fine_bars,
        rows_with_touches=rows_with_touches,
        total_touches=total_touches,
        forward_id=forward_id,
        error=error,
    )


# --- record: shape + provenance ------------------------------------------------------------------


def test_record_stores_every_field_verbatim(tmp_path):
    store = ForwardRunStore(tmp_path / "forward_runs")
    meta = _record_sample(store)

    assert meta["id"].startswith("forwardrun-2026-08-06-")
    assert meta["screen_id"] == "screen-2025-01-01-6d607a07fae6"
    assert meta["screen_date"] == "2025-01-01"
    assert meta["config_fingerprint"] == "08e471b10130e1e2"
    assert meta["forward_input_signature"] == "3ba0e5c0c85b7555"
    assert meta["started_utc"] == "2026-08-06T22:37:02.000000Z"
    assert meta["finished_utc"] == "2026-08-06T22:37:26.000000Z"
    assert meta["state"] == "done"
    assert meta["reused"] is False
    assert meta["rows_total"] == 100
    assert meta["rows_measured"] == 2
    assert meta["rows_absent_no_fine_bars"] == 98
    assert meta["rows_with_touches"] == 1
    assert meta["total_touches"] == 1
    assert meta["forward_id"] == "forward-2025-01-01-eccfa5dff487"
    assert meta["error"] is None


def test_the_run_id_takes_its_date_from_when_the_run_started_not_the_screen_date(tmp_path):
    """A 2025 screen date measured in 2026 files under the RUN's own date — the ledger is a log of
    attempts, and an id keyed on the measured date would sort a year of back-runs into the past."""
    store = ForwardRunStore(tmp_path / "forward_runs")
    meta = _record_sample(store, screen_date="2025-01-01", started_utc="2026-08-06T22:37:02Z")

    assert meta["id"].startswith("forwardrun-2026-08-06-")


def test_record_rejects_a_non_terminal_state(tmp_path):
    store = ForwardRunStore(tmp_path / "forward_runs")
    with pytest.raises(ValueError, match="invalid terminal state"):
        _record_sample(store, state="running")


def test_a_failed_run_carries_its_error_verbatim_and_names_no_record(tmp_path):
    store = ForwardRunStore(tmp_path / "forward_runs")
    meta = _record_sample(
        store, state="failed", forward_id=None, error="the bar store went away mid-walk",
        rows_measured=0, rows_absent_no_fine_bars=0, rows_with_touches=0, total_touches=0,
    )

    assert meta["state"] == "failed"
    assert meta["error"] == "the bar store went away mid-walk"
    assert meta["forward_id"] is None


def test_a_cancelled_run_is_recorded_and_names_no_record(tmp_path):
    """An operator cancel is a real terminal outcome the walk OBSERVED, so it leaves a record —
    unlike a crash, which reaches the writer not at all."""
    store = ForwardRunStore(tmp_path / "forward_runs")
    meta = _record_sample(store, state="cancelled", forward_id=None)

    assert meta["state"] == "cancelled"
    assert meta["forward_id"] is None


def test_a_reused_run_reports_the_existing_records_own_counts(tmp_path):
    """A reuse short-circuits the walk but is NOT an empty measurement: the counts it reports are
    the ones the walk it skipped produced, so a ledger reader sees what that snapshot actually
    holds rather than a misleading row of zeroes."""
    store = ForwardRunStore(tmp_path / "forward_runs")
    meta = _record_sample(store, reused=True)

    assert meta["reused"] is True
    assert (meta["rows_total"], meta["rows_measured"], meta["rows_absent_no_fine_bars"]) == (100, 2, 98)
    assert meta["forward_id"] == "forward-2025-01-01-eccfa5dff487"


def test_the_absent_row_count_is_what_distinguishes_an_empty_run_from_no_run(tmp_path):
    """The field this whole store exists for. A snapshot whose fine bars were never fetched records
    a run with every row absent; a snapshot never measured at all records NOTHING. The two are only
    distinguishable because the first leaves this row on disk."""
    store = ForwardRunStore(tmp_path / "forward_runs")
    _record_sample(
        store, screen_id="screen-2025-01-02-8151c52082a5", screen_date="2025-01-02",
        rows_total=100, rows_measured=2, rows_absent_no_fine_bars=98,
    )

    measured = store.list_for_screen("screen-2025-01-02-8151c52082a5")
    never_measured = store.list_for_screen("screen-2025-01-03-4c28990d7f94")

    assert len(measured) == 1 and measured[0]["rows_absent_no_fine_bars"] == 98
    assert never_measured == []


# --- list / list_for_screen -----------------------------------------------------------------------


def test_list_serves_the_stored_record_verbatim(tmp_path):
    store = ForwardRunStore(tmp_path / "forward_runs")
    meta = _record_sample(store)

    records, errors = store.list()
    assert errors == []
    assert records == [meta]


def test_store_survives_a_reload_from_disk(tmp_path):
    root = tmp_path / "forward_runs"
    meta = _record_sample(ForwardRunStore(root))

    records, errors = ForwardRunStore(root).list()
    assert errors == []
    assert records == [meta]


def test_list_on_a_directory_that_was_never_created_is_honestly_empty(tmp_path):
    store = ForwardRunStore(tmp_path / "forward_runs")
    assert store.list() == ([], [])


def test_list_for_screen_filters_to_one_snapshot_oldest_first(tmp_path):
    store = ForwardRunStore(tmp_path / "forward_runs")
    older = _record_sample(store, started_utc="2026-08-06T22:00:00Z")
    newer = _record_sample(store, started_utc="2026-08-06T23:00:00Z", reused=True)
    _record_sample(store, screen_id="screen-2026-08-05-8a9b267a5ac9", screen_date="2026-08-05")

    for_screen = store.list_for_screen("screen-2025-01-01-6d607a07fae6")
    assert [record["id"] for record in for_screen] == [older["id"], newer["id"]]


def test_list_for_screen_on_an_unknown_snapshot_is_honestly_empty(tmp_path):
    store = ForwardRunStore(tmp_path / "forward_runs")
    _record_sample(store)
    assert store.list_for_screen("screen-2026-01-01-000000000000") == []


# --- append-only: every call to record is a genuinely NEW file, never a dedup/update ---------------


def test_two_calls_with_identical_field_values_still_append_two_distinct_records(tmp_path):
    """This store performs no content-keyed dedup — two back-to-back measurements of one snapshot
    (e.g. both "reused") are still TWO real, distinct attempts and must both be recorded."""
    store = ForwardRunStore(tmp_path / "forward_runs")
    first = _record_sample(store)
    second = _record_sample(store)

    assert first["id"] != second["id"]
    records, errors = store.list()
    assert errors == []
    assert {r["id"] for r in records} == {first["id"], second["id"]}


def test_a_second_run_appends_without_touching_the_first_files_bytes_on_disk(tmp_path):
    root = tmp_path / "forward_runs"
    store = ForwardRunStore(root)
    first = _record_sample(store, started_utc="2026-08-06T22:00:00Z")
    first_path = root / f"{first['id']}.json"
    first_bytes_before = first_path.read_bytes()

    second = _record_sample(store, started_utc="2026-08-06T23:00:00Z", reused=True)

    assert first_path.read_bytes() == first_bytes_before  # byte-unchanged
    records, errors = store.list()
    assert errors == []
    assert [record["id"] for record in records] == [first["id"], second["id"]]  # oldest first


def test_forward_run_store_has_no_update_or_delete_method():
    """Structural immutability: the only mutation on this class is ``record`` — mirrors
    ``ScreenRunStore``'s own guard-by-absence discipline."""
    public_methods = {name for name in dir(ForwardRunStore) if not name.startswith("_")}
    assert public_methods == {"root", "list", "list_for_screen", "record"}


# --- interrupted-run honesty: a run whose terminal write never happens leaves zero record ---------


def test_a_run_that_never_reaches_the_writer_call_leaves_the_store_untouched(tmp_path):
    """Simulates a process that ends before the writer's terminal call: a store is constructed
    exactly as a real caller would, but ``record``/``record_forward_run`` is deliberately never
    invoked (standing in for a crash, or for a browser tab that closed before the chain's forward
    step ever ran). The store gains zero new file — never a fabricated or partial entry."""
    store = ForwardRunStore(tmp_path / "forward_runs")
    # ... the walk would happen here in a real run; the process ends before this line runs:
    # record_forward_run(store, ...)
    records, errors = store.list()
    assert records == []
    assert errors == []
    assert not (tmp_path / "forward_runs").exists()


# --- integrity: a corrupted file is explicit, never silent ----------------------------------------


def test_corrupted_run_record_file_surfaces_explicitly_in_list_errors(tmp_path):
    root = tmp_path / "forward_runs"
    store = ForwardRunStore(root)
    _record_sample(store)
    path = next(root.glob("*.json"))
    data = json.loads(path.read_text())
    data["record"]["meta"]["rows_total"] = 999  # tamper -- file_checksum now disagrees
    path.write_text(json.dumps(data))

    records, errors = store.list()
    assert records == []
    assert len(errors) == 1
    assert path.name == errors[0]["file"]
    assert "integrity" in errors[0]["error"]


def test_load_raises_forward_run_integrity_error_for_unparseable_json(tmp_path):
    root = tmp_path / "forward_runs"
    root.mkdir(parents=True)
    (root / "forwardrun-2026-01-01-deadbeef0000.json").write_text("{not json")

    records, errors = ForwardRunStore(root).list()
    assert records == []
    assert len(errors) == 1


def test_corrupted_file_does_not_block_other_valid_records_from_listing(tmp_path):
    root = tmp_path / "forward_runs"
    store = ForwardRunStore(root)
    good = _record_sample(store)
    (root / "forwardrun-2026-01-01-deadbeef0000.json").write_text("{not json")

    records, errors = store.list()
    assert len(records) == 1 and records[0]["id"] == good["id"]
    assert len(errors) == 1


def test_load_raises_forward_run_integrity_error_directly_for_a_missing_meta_shape(tmp_path):
    root = tmp_path / "forward_runs"
    root.mkdir(parents=True)
    path = root / "forwardrun-2026-01-01-deadbeef0000.json"
    path.write_text(json.dumps({"unexpected": "shape"}))

    store = ForwardRunStore(root)
    with pytest.raises(ForwardRunIntegrityError):
        store._load(path)  # noqa: SLF001 -- direct unit test of the private loader's own raise


# --- resolve_desk_forward_log_dir -- zero new Config field ------------------------------------------


def test_resolve_desk_forward_log_dir_defaults_to_a_sibling_of_the_universe_dir(monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_DESK_FORWARD_LOG_DIR", raising=False)
    resolved = resolve_desk_forward_log_dir("/some/root/.data/universe")
    assert resolved == "/some/root/.data/forward_runs"


def test_resolve_desk_forward_log_dir_env_override(monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_FORWARD_LOG_DIR", "/tmp/custom-forward-log-dir")
    assert resolve_desk_forward_log_dir("/some/root/.data/universe") == "/tmp/custom-forward-log-dir"
