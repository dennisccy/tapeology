"""``desk_playbook_log.py`` (Era B2, J-02) — the playbook-run log's store discipline: checksum
verification, structural append-only-ness (no update/delete path, no content dedup — every call to
``record`` is a genuinely new file), the interrupted-run-leaves-no-record guarantee, the
per-session read, and the directory-resolution seam. Mirrors ``test_desk_forward_log.py``'s own
store-level test shape, with ONE deliberate divergence: this store's terminal-outcome set has no
``"cancelled"`` value at all (a cancelled playbook run leaves no row — see the module docstring).

The shared-writer contract itself (proving ``record_playbook_run`` is called from inside
``run_playbook_and_record``, the ONE entry point both ``DeskPlaybookComputeManager`` and the CLI
call) is exercised end to end in ``test_desk_playbook_compute.py`` — this file covers the store
module in isolation."""

from __future__ import annotations

import json

import pytest

from app.research.desk_playbook_log import (
    PlaybookRunIntegrityError,
    PlaybookRunStore,
    record_playbook_run,
    resolve_desk_playbook_log_dir,
)


def _record_sample(
    store: PlaybookRunStore,
    *,
    outcome: str = "recorded",
    started_at: str = "2026-08-10T22:37:02.000000Z",
    finished_at: str = "2026-08-10T22:37:26.000000Z",
    session_date: str = "2026-06-22",
    config_fingerprint: str = "08e471b10130e1e2",
    playbook_input_signature: str | None = "3ba0e5c0c85b7555",
    signals_recorded: int = 1,
    playbook_id: str | None = "playbook-2026-06-22-eccfa5dff487",
    error: str | None = None,
) -> dict:
    return record_playbook_run(
        store,
        session_date=session_date,
        config_fingerprint=config_fingerprint,
        playbook_input_signature=playbook_input_signature,
        started_at=started_at,
        finished_at=finished_at,
        outcome=outcome,
        signals_recorded=signals_recorded,
        playbook_id=playbook_id,
        error=error,
    )


# --- record: shape + provenance ------------------------------------------------------------------


def test_record_stores_every_field_verbatim(tmp_path):
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    meta = _record_sample(store)

    assert meta["run_id"].startswith("playbookrun-2026-08-10-")
    assert meta["session_date"] == "2026-06-22"
    assert meta["config_fingerprint"] == "08e471b10130e1e2"
    assert meta["playbook_input_signature"] == "3ba0e5c0c85b7555"
    assert meta["started_at"] == "2026-08-10T22:37:02.000000Z"
    assert meta["finished_at"] == "2026-08-10T22:37:26.000000Z"
    assert meta["outcome"] == "recorded"
    assert meta["signals_recorded"] == 1
    assert meta["playbook_id"] == "playbook-2026-06-22-eccfa5dff487"
    assert meta["error"] is None


def test_the_run_id_takes_its_date_from_when_the_run_started_not_the_session_date(tmp_path):
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    meta = _record_sample(store, session_date="2025-01-01", started_at="2026-08-10T22:37:02Z")
    assert meta["run_id"].startswith("playbookrun-2026-08-10-")


def test_record_rejects_a_non_terminal_outcome(tmp_path):
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    with pytest.raises(ValueError, match="invalid terminal outcome"):
        _record_sample(store, outcome="running")


def test_record_rejects_cancelled_as_an_outcome(tmp_path):
    """The one deliberate divergence from the forward-returns ledger: a cancelled playbook run is
    never logged at all (the CALLER never invokes this writer for one), so ``"cancelled"`` is not
    even a valid value on this store — a caller attempting it is a programming error, not a real
    terminal state to represent."""
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    with pytest.raises(ValueError, match="invalid terminal outcome"):
        _record_sample(store, outcome="cancelled")


def test_a_failed_run_carries_its_error_verbatim_and_names_no_record(tmp_path):
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    meta = _record_sample(
        store, outcome="failed", playbook_id=None, error="the bar store went away mid-walk",
        signals_recorded=0,
    )
    assert meta["outcome"] == "failed"
    assert meta["error"] == "the bar store went away mid-walk"
    assert meta["playbook_id"] is None


def test_a_refused_non_session_run_carries_the_refusal_sentence_and_names_no_record(tmp_path):
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    meta = _record_sample(
        store, outcome="refused_non_session", playbook_id=None, signals_recorded=0,
        playbook_input_signature=None, error="2026-06-21 is not a recorded trading session -- ...",
    )
    assert meta["outcome"] == "refused_non_session"
    assert meta["playbook_id"] is None
    assert meta["playbook_input_signature"] is None
    assert "not a recorded trading session" in meta["error"]


def test_a_reused_run_reports_the_existing_records_own_signal_count(tmp_path):
    """A reuse short-circuits the walk but is NOT an empty measurement: the count it reports is the
    one the walk it skipped produced, never a misleading zero."""
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    meta = _record_sample(store, outcome="reused", signals_recorded=3)
    assert meta["outcome"] == "reused"
    assert meta["signals_recorded"] == 3
    assert meta["playbook_id"] == "playbook-2026-06-22-eccfa5dff487"


# --- list / list_for_session -----------------------------------------------------------------------


def test_list_serves_the_stored_record_verbatim(tmp_path):
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    meta = _record_sample(store)
    records, errors = store.list()
    assert errors == []
    assert records == [meta]


def test_store_survives_a_reload_from_disk(tmp_path):
    root = tmp_path / "playbook_runs"
    meta = _record_sample(PlaybookRunStore(root))
    records, errors = PlaybookRunStore(root).list()
    assert errors == []
    assert records == [meta]


def test_list_on_a_directory_that_was_never_created_is_honestly_empty(tmp_path):
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    assert store.list() == ([], [])


def test_list_for_session_filters_to_one_date_oldest_first(tmp_path):
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    older = _record_sample(store, started_at="2026-08-10T22:00:00Z")
    newer = _record_sample(store, started_at="2026-08-10T23:00:00Z", outcome="reused")
    _record_sample(store, session_date="2026-06-19")

    for_session = store.list_for_session("2026-06-22")
    assert [record["run_id"] for record in for_session] == [older["run_id"], newer["run_id"]]


def test_list_for_session_on_an_unknown_date_is_honestly_empty(tmp_path):
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    _record_sample(store)
    assert store.list_for_session("2099-01-01") == []


# --- append-only: every call to record is a genuinely NEW file, never a dedup/update ---------------


def test_two_calls_with_identical_field_values_still_append_two_distinct_records(tmp_path):
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    first = _record_sample(store)
    second = _record_sample(store)
    assert first["run_id"] != second["run_id"]
    records, errors = store.list()
    assert errors == []
    assert {r["run_id"] for r in records} == {first["run_id"], second["run_id"]}


def test_a_second_run_appends_without_touching_the_first_files_bytes_on_disk(tmp_path):
    root = tmp_path / "playbook_runs"
    store = PlaybookRunStore(root)
    first = _record_sample(store, started_at="2026-08-10T22:00:00Z")
    first_path = root / f"{first['run_id']}.json"
    first_bytes_before = first_path.read_bytes()

    second = _record_sample(store, started_at="2026-08-10T23:00:00Z", outcome="reused")

    assert first_path.read_bytes() == first_bytes_before  # byte-unchanged
    records, errors = store.list()
    assert errors == []
    assert [record["run_id"] for record in records] == [first["run_id"], second["run_id"]]


def test_playbook_run_store_has_no_update_or_delete_method():
    """Structural immutability: the only mutation on this class is ``record``."""
    public_methods = {name for name in dir(PlaybookRunStore) if not name.startswith("_")}
    assert public_methods == {"root", "list", "list_for_session", "record"}


# --- interrupted/cancelled-run honesty: BOTH leave zero record --------------------------------------


def test_a_run_that_never_reaches_the_writer_call_leaves_the_store_untouched(tmp_path):
    """Stands in for a crash AND for a cooperative cancel alike — both never call
    ``record_playbook_run`` (the module docstring's terminal-excludes-cancelled contract) — the
    store gains zero new file either way."""
    store = PlaybookRunStore(tmp_path / "playbook_runs")
    # ... the walk would happen here in a real run; the process ends (or the walk is cancelled)
    # before this line runs: record_playbook_run(store, ...)
    records, errors = store.list()
    assert records == []
    assert errors == []
    assert not (tmp_path / "playbook_runs").exists()


# --- integrity: a corrupted file is explicit, never silent ----------------------------------------


def test_corrupted_run_record_file_surfaces_explicitly_in_list_errors(tmp_path):
    root = tmp_path / "playbook_runs"
    store = PlaybookRunStore(root)
    _record_sample(store)
    path = next(root.glob("*.json"))
    data = json.loads(path.read_text())
    data["record"]["meta"]["signals_recorded"] = 999  # tamper -- file_checksum now disagrees
    path.write_text(json.dumps(data))

    records, errors = store.list()
    assert records == []
    assert len(errors) == 1
    assert path.name == errors[0]["file"]
    assert "integrity" in errors[0]["error"]


def test_load_raises_playbook_run_integrity_error_for_unparseable_json(tmp_path):
    root = tmp_path / "playbook_runs"
    root.mkdir(parents=True)
    (root / "playbookrun-2026-01-01-deadbeef0000.json").write_text("{not json")

    records, errors = PlaybookRunStore(root).list()
    assert records == []
    assert len(errors) == 1


def test_corrupted_file_does_not_block_other_valid_records_from_listing(tmp_path):
    root = tmp_path / "playbook_runs"
    store = PlaybookRunStore(root)
    good = _record_sample(store)
    (root / "playbookrun-2026-01-01-deadbeef0000.json").write_text("{not json")

    records, errors = store.list()
    assert len(records) == 1 and records[0]["run_id"] == good["run_id"]
    assert len(errors) == 1


def test_load_raises_playbook_run_integrity_error_directly_for_a_missing_meta_shape(tmp_path):
    root = tmp_path / "playbook_runs"
    root.mkdir(parents=True)
    path = root / "playbookrun-2026-01-01-deadbeef0000.json"
    path.write_text(json.dumps({"unexpected": "shape"}))

    store = PlaybookRunStore(root)
    with pytest.raises(PlaybookRunIntegrityError):
        store._load(path)  # noqa: SLF001 -- direct unit test of the private loader's own raise


# --- resolve_desk_playbook_log_dir -- zero new Config field ------------------------------------------


def test_resolve_desk_playbook_log_dir_defaults_to_a_sibling_of_the_universe_dir(monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", raising=False)
    resolved = resolve_desk_playbook_log_dir("/some/root/.data/universe")
    assert resolved == "/some/root/.data/playbook_runs"


def test_resolve_desk_playbook_log_dir_env_override(monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_PLAYBOOK_LOG_DIR", "/tmp/custom-playbook-log-dir")
    assert resolve_desk_playbook_log_dir("/some/root/.data/universe") == "/tmp/custom-playbook-log-dir"
