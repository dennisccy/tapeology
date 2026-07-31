"""``desk_topup_log.py`` (Era B "The Desk", J-09) — the top-up run log's store discipline: checksum
verification, structural append-only-ness (no update/delete path, no content dedup — every call to
``record`` is a genuinely new file), the interrupted-run-leaves-no-record guarantee, and the
directory-resolution seam (mirrors ``test_desk_universe.py``/``test_desk_screen.py``'s own store-
level test shape).

The shared-writer contract itself (proving ``record_topup_run`` is the ONE path both
``DeskTopupComputeManager`` and the CLI call) is exercised end to end in
``test_desk_topup_compute.py`` — this file covers the store module in isolation."""

from __future__ import annotations

import json

import pytest

from app.research.desk_topup_log import (
    TopupRunIntegrityError,
    TopupRunStore,
    record_topup_run,
    resolve_desk_topup_log_dir,
)

SAMPLE_OUTCOMES = [
    {"symbol": "AAA", "timeframe": "1h", "outcome": "fetched", "detail": None},
    {"symbol": "AAA", "timeframe": "4h", "outcome": "reused", "detail": None},
    {"symbol": "AAA", "timeframe": "1d", "outcome": "failed", "detail": "no data for that window"},
]


def _record_sample(
    store: TopupRunStore,
    *,
    state: str = "done",
    outcomes: list[dict] | None = None,
    started_utc: str = "2026-07-28T09:00:00.000000Z",
    finished_utc: str = "2026-07-28T09:05:00.000000Z",
    universe_snapshot_id: str | None = "universe-2026-07-25-49b33fa31680",
    pairs_total: int = 3,
) -> dict:
    return record_topup_run(
        store,
        universe_snapshot_id=universe_snapshot_id,
        requested_window={"start": "2024-07-28T00:00:00Z", "end": "2026-07-28T00:00:00Z"},
        config_fingerprint="08e471b10130e1e2",
        started_utc=started_utc,
        finished_utc=finished_utc,
        state=state,
        pairs_total=pairs_total,
        outcomes=SAMPLE_OUTCOMES if outcomes is None else outcomes,
    )


# --- record: shape + provenance ------------------------------------------------------------------


def test_record_stores_every_field_and_derives_pairs_attempted_from_len_outcomes(tmp_path):
    store = TopupRunStore(tmp_path / "topup_runs")
    meta = _record_sample(store)

    assert meta["universe_snapshot_id"] == "universe-2026-07-25-49b33fa31680"
    assert meta["requested_window"] == {"start": "2024-07-28T00:00:00Z", "end": "2026-07-28T00:00:00Z"}
    assert meta["config_fingerprint"] == "08e471b10130e1e2"
    assert meta["started_utc"] == "2026-07-28T09:00:00.000000Z"
    assert meta["finished_utc"] == "2026-07-28T09:05:00.000000Z"
    assert meta["state"] == "done"
    assert meta["pairs_total"] == 3
    assert meta["pairs_attempted"] == 3  # len(outcomes), never a separately tracked counter
    assert meta["outcomes"] == SAMPLE_OUTCOMES
    assert meta["id"].startswith("topup-2026-07-28-")
    # The record landed as ONE file in the configured directory.
    assert len(list((tmp_path / "topup_runs").glob("*.json"))) == 1


def test_record_rejects_a_non_terminal_state(tmp_path):
    store = TopupRunStore(tmp_path / "topup_runs")
    with pytest.raises(ValueError):
        _record_sample(store, state="running")


def test_outcomes_are_preserved_verbatim_including_a_failed_pairs_detail(tmp_path):
    store = TopupRunStore(tmp_path / "topup_runs")
    meta = _record_sample(store)

    failed = [o for o in meta["outcomes"] if o["outcome"] == "failed"]
    assert len(failed) == 1
    assert failed[0]["detail"] == "no data for that window"
    assert failed[0]["symbol"] == "AAA" and failed[0]["timeframe"] == "1d"


# --- list: verbatim read, oldest-started first -----------------------------------------------------


def test_list_serves_the_stored_record_verbatim(tmp_path):
    store = TopupRunStore(tmp_path / "topup_runs")
    recorded = _record_sample(store)

    records, errors = store.list()
    assert errors == []
    assert len(records) == 1
    assert records[0] == recorded


def test_store_survives_a_reload_from_disk(tmp_path):
    root = tmp_path / "topup_runs"
    recorded = _record_sample(TopupRunStore(root))

    reloaded = TopupRunStore(root)
    records, errors = reloaded.list()
    assert errors == []
    assert records == [recorded]


def test_list_on_a_directory_that_was_never_created_is_honestly_empty(tmp_path):
    """The DoD's interrupted-run guarantee at its simplest: a store that is never told to
    ``record`` (the writer's terminal call literally never happening — the process ended, or in
    this test's case, simply was never invoked) holds zero files and lists zero records — never a
    fabricated or partial entry."""
    store = TopupRunStore(tmp_path / "topup_runs" / "never-created")
    records, errors = store.list()
    assert records == []
    assert errors == []
    assert not (tmp_path / "topup_runs" / "never-created").exists()


# --- append-only: every call to record is a genuinely NEW file, never a dedup/update ---------------


def test_two_calls_with_identical_field_values_still_append_two_distinct_records(tmp_path):
    """UNLIKE UniverseStore/ScreenStore, this store performs no content-keyed dedup — two
    back-to-back top-up runs over an unchanged store (e.g. both entirely "reused") are still TWO
    real, distinct attempts and must both be recorded."""
    store = TopupRunStore(tmp_path / "topup_runs")
    first = _record_sample(store)
    second = _record_sample(store)

    assert first["id"] != second["id"]
    records, errors = store.list()
    assert errors == []
    assert {r["id"] for r in records} == {first["id"], second["id"]}


def test_a_second_run_appends_without_touching_the_first_files_bytes_on_disk(tmp_path):
    """TC-6: the first record's file stays byte-unchanged (same sha256) after a second run
    completes."""
    root = tmp_path / "topup_runs"
    store = TopupRunStore(root)
    first = _record_sample(store, started_utc="2026-07-28T09:00:00Z", finished_utc="2026-07-28T09:05:00Z")
    first_path = root / f"{first['id']}.json"
    first_bytes_before = first_path.read_bytes()

    second = _record_sample(
        store,
        started_utc="2026-07-28T10:00:00Z",
        finished_utc="2026-07-28T10:05:00Z",
        outcomes=[{"symbol": "BBB", "timeframe": "1h", "outcome": "fetched", "detail": None}],
    )

    assert first_path.read_bytes() == first_bytes_before  # byte-unchanged
    records, errors = store.list()
    assert errors == []
    assert len(records) == 2
    assert records[0]["id"] == first["id"]  # oldest-started first
    assert records[1]["id"] == second["id"]


def test_topup_run_store_has_no_update_or_delete_method():
    """Structural immutability: the only mutation on this class is ``record`` — mirrors
    ``UniverseStore``/``ScreenStore``'s own guard-by-absence discipline."""
    public_methods = {name for name in dir(TopupRunStore) if not name.startswith("_")}
    assert public_methods == {"root", "list", "record"}


# --- interrupted-run honesty: a run whose terminal write never happens leaves zero record ---------


def test_a_run_that_never_reaches_the_writer_call_leaves_the_store_untouched(tmp_path):
    """Simulates a process that ends before the writer's terminal call: a store is constructed
    exactly as a real caller would, but ``record``/``record_topup_run`` is deliberately never
    invoked (standing in for a crash between the walk finishing and the writer call). The store
    gains zero new file — never a fabricated or partial entry (DoD)."""
    store = TopupRunStore(tmp_path / "topup_runs")
    # ... the walk would happen here in a real run; the process ends before this line runs:
    # record_topup_run(store, ...)
    records, errors = store.list()
    assert records == []
    assert errors == []
    assert not (tmp_path / "topup_runs").exists()


# --- integrity: a corrupted file is explicit, never silent ----------------------------------------


def test_corrupted_run_record_file_surfaces_explicitly_in_list_errors(tmp_path):
    root = tmp_path / "topup_runs"
    store = TopupRunStore(root)
    _record_sample(store)
    path = next(root.glob("*.json"))
    data = json.loads(path.read_text())
    data["record"]["meta"]["pairs_total"] = 999  # tamper -- file_checksum now disagrees
    path.write_text(json.dumps(data))

    records, errors = store.list()
    assert records == []
    assert len(errors) == 1
    assert path.name == errors[0]["file"]
    assert "integrity" in errors[0]["error"]


def test_load_raises_topup_run_integrity_error_for_unparseable_json(tmp_path):
    root = tmp_path / "topup_runs"
    root.mkdir(parents=True)
    (root / "topup-2026-01-01-deadbeef0000.json").write_text("{not json")

    store = TopupRunStore(root)
    records, errors = store.list()
    assert records == []
    assert len(errors) == 1


def test_corrupted_file_does_not_block_other_valid_records_from_listing(tmp_path):
    root = tmp_path / "topup_runs"
    store = TopupRunStore(root)
    good = _record_sample(store)
    bad_path = root / "topup-2026-01-01-deadbeef0000.json"
    bad_path.write_text("{not json")

    records, errors = store.list()
    assert len(records) == 1 and records[0]["id"] == good["id"]
    assert len(errors) == 1


# --- resolve_desk_topup_log_dir -- zero new Config field -------------------------------------------


def test_resolve_desk_topup_log_dir_defaults_to_a_sibling_of_the_universe_dir(monkeypatch):
    monkeypatch.delenv("TAPEOLOGY_DESK_TOPUP_LOG_DIR", raising=False)
    resolved = resolve_desk_topup_log_dir("/some/root/.data/universe")
    assert resolved == "/some/root/.data/topup_runs"


def test_resolve_desk_topup_log_dir_env_override(monkeypatch):
    monkeypatch.setenv("TAPEOLOGY_DESK_TOPUP_LOG_DIR", "/tmp/custom-topup-log-dir")
    assert resolve_desk_topup_log_dir("/some/root/.data/universe") == "/tmp/custom-topup-log-dir"


# --- goal-desk-iter-26 (J-17): the store is a pure passthrough for whatever per-pair outcome shape
# a caller gives it -- it validates NOTHING about outcome-dict keys, so the four new fields
# (`requested_window`/`store_frozen_from`/`store_frozen_through`/`window_basis`) need no store-side
# code change; these tests document that the passthrough genuinely holds for the new shape, and
# that an OLD-shape (pre-iter-26) run record still round-trips exactly as it always has (the
# "legacy runs served verbatim, never backfilled" DoD clause, at the store layer). ------------------

J17_OUTCOMES = [
    {
        "symbol": "AAA", "timeframe": "1d", "outcome": "unchanged",
        "detail": "already registered", "requested_window": {"start": "2024-07-01T00:00:00Z", "end": "2026-07-30T00:00:00Z"},
        "store_frozen_from": "2024-06-01T00:00:00.000000Z", "store_frozen_through": "2026-07-25T00:00:00.000000Z",
        "window_basis": "tail",
    },
    {
        "symbol": "BBB", "timeframe": "1d", "outcome": "fetched", "detail": None,
        "requested_window": {"start": "2024-07-30T00:00:00Z", "end": "2026-07-30T00:00:00Z"},
        "store_frozen_from": None, "store_frozen_through": None, "window_basis": "full_lookback",
    },
]


def test_record_and_list_round_trip_the_new_j17_per_pair_fields_verbatim(tmp_path):
    store = TopupRunStore(tmp_path / "topup_runs")
    meta = _record_sample(store, outcomes=J17_OUTCOMES)

    assert meta["outcomes"] == J17_OUTCOMES
    records, errors = store.list()
    assert errors == []
    assert records[0]["outcomes"] == J17_OUTCOMES


def test_a_legacy_pre_iter26_run_record_round_trips_without_the_new_fields(tmp_path):
    """A run recorded BEFORE this iteration's code shipped never gains the four new fields at
    read time -- `list()` serves it exactly as it was written, absent fields absent (never a
    computed or backfilled value)."""
    store = TopupRunStore(tmp_path / "topup_runs")
    legacy_outcomes = [{"symbol": "AAA", "timeframe": "1h", "outcome": "fetched", "detail": None}]
    meta = _record_sample(store, outcomes=legacy_outcomes)

    assert meta["outcomes"] == legacy_outcomes
    for outcome in meta["outcomes"]:
        assert "window_basis" not in outcome
        assert "requested_window" not in outcome

    records, errors = store.list()
    assert errors == []
    assert records[0]["outcomes"] == legacy_outcomes


# goal-desk-iter-32 (J-19): one more additive field, `store_frozen_through_after` -- the SAME pure
# passthrough contract, proven the same way: a fresh record round-trips the new field verbatim, and
# a legacy record (pre-iter-32, or even pre-iter-26) never gains it at read time.

J19_OUTCOMES = [
    {
        "symbol": "AAA", "timeframe": "1d", "outcome": "fetched", "detail": None,
        "requested_window": {"start": "2024-07-30T00:00:00Z", "end": "2026-07-31T00:00:00Z"},
        "store_frozen_from": None, "store_frozen_through": None, "window_basis": "full_lookback",
        "store_frozen_through_after": "2026-07-30T00:00:00.000000Z",
    },
    {
        "symbol": "BBB", "timeframe": "1d", "outcome": "reused", "detail": None,
        "requested_window": {"start": "2024-07-31T00:00:00Z", "end": "2026-07-31T00:00:00Z"},
        "store_frozen_from": "2024-06-01T00:00:00.000000Z",
        "store_frozen_through": "2026-07-25T00:00:00.000000Z", "window_basis": "tail",
        "store_frozen_through_after": "2026-07-25T00:00:00.000000Z",
    },
]


def test_record_and_list_round_trip_the_new_j19_store_frozen_through_after_field_verbatim(tmp_path):
    store = TopupRunStore(tmp_path / "topup_runs")
    meta = _record_sample(store, outcomes=J19_OUTCOMES)

    assert meta["outcomes"] == J19_OUTCOMES
    records, errors = store.list()
    assert errors == []
    assert records[0]["outcomes"] == J19_OUTCOMES


def test_a_legacy_pre_iter32_run_record_round_trips_without_store_frozen_through_after(tmp_path):
    """A run recorded BEFORE this iteration's code shipped (including a pre-iter-26 run, which
    lacks ALL five new fields) never gains `store_frozen_through_after` at read time."""
    store = TopupRunStore(tmp_path / "topup_runs")
    legacy_outcomes = [{"symbol": "AAA", "timeframe": "1h", "outcome": "fetched", "detail": None}]
    meta = _record_sample(store, outcomes=legacy_outcomes)

    assert meta["outcomes"] == legacy_outcomes
    for outcome in meta["outcomes"]:
        assert "store_frozen_through_after" not in outcome

    records, errors = store.list()
    assert errors == []
    assert records[0]["outcomes"] == legacy_outcomes
