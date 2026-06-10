"""Journal store discipline (capability 28): WAL, writer queue, temp-path injection, schema_version,
append-only verdict_events repository."""

import dataclasses
import json

import pytest

from app.config import CONFIG
from app.research.store import JournalStore, ThesisRecord, VerdictEventRecord


def _thesis(tid: str = "t1", ticker: str = "SIM-BIDABS", status: str = "active") -> ThesisRecord:
    return ThesisRecord(
        id=tid,
        ticker=ticker,
        setup_type="absorption_reversal",
        direction="long",
        invalidation_price=99.0,
        level_price=None,
        status=status,
        bound_source="bid_absorption",
        data_feed="sim",
        config_fingerprint="abc123",
        entry_context={"last": 100.0, "tape_state": "bid_absorption"},
        statements=[{"text": "x", "kind": "tape_state_is", "params": {"states": ["bid_absorption"]}}],
        created_logical_ts=12.5,
        created_wall_ts=1700000000.0,
    )


@pytest.fixture
def store(tmp_path):
    s = JournalStore(str(tmp_path / "journal.db"), CONFIG)
    yield s
    s.close()


def test_temp_path_injection_creates_the_db(tmp_path):
    db = tmp_path / "injected.db"
    s = JournalStore(str(db), CONFIG)
    try:
        assert db.exists()
    finally:
        s.close()


def test_wal_journal_mode_enabled(store):
    assert store.journal_mode().lower() == "wal"


def test_schema_version_present_and_matches_config(store):
    assert store.schema_version() == CONFIG.journal_schema_version


def test_full_schema_tables_exist(store):
    conn = store._read_conn()
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {r["name"] for r in rows}
    finally:
        conn.close()
    for table in (
        "schema_version",
        "theses",
        "verdict_events",
        "hints",
        "actions",
        "studies",
        "study_occurrences",
    ):
        assert table in names, f"missing table {table}"


def test_insert_and_read_thesis_roundtrip(store):
    rec = _thesis()
    store.insert_thesis(rec)
    read = store.get_thesis("t1")
    assert read is not None
    assert read.id == "t1"
    assert read.ticker == "SIM-BIDABS"
    assert read.invalidation_price == 99.0
    assert read.entry_context == {"last": 100.0, "tape_state": "bid_absorption"}
    assert read.statements[0]["kind"] == "tape_state_is"
    assert read.data_feed == "sim"
    assert read.config_fingerprint == "abc123"


def test_get_active_thesis_returns_only_active(store):
    store.insert_thesis(_thesis(tid="a", status="expired"))
    assert store.get_active_thesis("SIM-BIDABS") is None
    store.insert_thesis(_thesis(tid="b", status="active"))
    active = store.get_active_thesis("SIM-BIDABS")
    assert active is not None and active.id == "b"


def test_append_verdict_events_are_ordered_and_readable(store):
    store.insert_thesis(_thesis())
    store.append_verdict_event(
        VerdictEventRecord("t1", 1.0, 100.0, "pending", "declared", "bid_absorption", 0.8, 100.0)
    )
    store.append_verdict_event(
        VerdictEventRecord("t1", 2.0, 200.0, "expired", "stopped", None, None, 100.0)
    )
    events = store.verdict_events("t1")
    assert [e.verdict for e in events] == ["pending", "expired"]
    assert events[0].evidence == "declared"
    assert events[1].tape_state is None


def test_verdict_events_repository_is_append_only():
    # The append-only discipline is a REPOSITORY-level guarantee: the store exposes NO update/delete
    # method for verdict_events. Assert the surface, not just behaviour.
    public = {n for n in dir(JournalStore) if not n.startswith("_")}
    for forbidden in (
        "update_verdict_event",
        "delete_verdict_event",
        "edit_verdict_event",
        "remove_verdict_event",
    ):
        assert forbidden not in public, f"repository must not expose {forbidden}"
    # The only verdict_events mutator is the append.
    assert "append_verdict_event" in public


def test_resolve_thesis_updates_status_without_touching_timeline(store):
    store.insert_thesis(_thesis())
    store.append_verdict_event(
        VerdictEventRecord("t1", 1.0, 100.0, "pending", "declared", "bid_absorption", 0.8, 100.0)
    )
    store.resolve_thesis("t1", "expired")
    assert store.get_thesis("t1").status == "expired"
    # The existing timeline row is untouched (append-only) — still exactly one event.
    assert len(store.verdict_events("t1")) == 1


def test_startup_sweep_expires_stale_actives_and_appends_event(store):
    store.insert_thesis(_thesis(tid="stale", status="active"))
    store.insert_thesis(_thesis(tid="done", status="played_out"))
    affected = store.expire_stale_actives(1700000123.0)
    assert affected == ["stale"]
    assert store.get_thesis("stale").status == "expired"
    assert store.get_thesis("done").status == "played_out"
    # A final expired event was appended for the swept thesis.
    events = store.verdict_events("stale")
    assert events[-1].verdict == "expired"


def test_writer_queue_serializes_concurrent_writes(store):
    # Many writes enqueued from multiple threads must all land (single writer worker serializes them
    # under BEGIN IMMEDIATE — no "database is locked", no lost write).
    import threading

    store.insert_thesis(_thesis())
    n = 50
    errors = []

    def writer(i: int) -> None:
        try:
            store.append_verdict_event(
                VerdictEventRecord("t1", float(i), float(i), "pending", f"e{i}", None, None, None)
            )
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(store.verdict_events("t1")) == n


def test_writes_after_close_raise(tmp_path):
    s = JournalStore(str(tmp_path / "j.db"), CONFIG)
    s.close()
    with pytest.raises(RuntimeError):
        s.insert_thesis(_thesis())


def test_verdict_event_timing_record_roundtrips(store):
    # The capability-24 dwell timing record (rule_first_true) persists + reads back verbatim.
    store.insert_thesis(_thesis())
    store.append_verdict_event(
        VerdictEventRecord(
            "t1", 12.0, 100.0, "confirming", "the tape confirms", "buyer_control", 0.9, 100.5,
            rule_first_true_ts=9.0, rule_first_true_price=100.2,
        )
    )
    e = store.verdict_events("t1")[0]
    assert e.verdict == "confirming"
    assert e.rule_first_true_ts == 9.0
    assert e.rule_first_true_price == 100.2
    assert e.logical_ts == 12.0  # publication instant, distinct from rule_first_true_ts


def test_timeline_cap_prunes_oldest_rows(tmp_path):
    # The config-owned timeline cap bounds an unbounded watch: once over the cap, the OLDEST rows are
    # pruned and only the most-recent ``cap`` survive — in order, never edited (capacity management,
    # distinct from any update/delete of a retained row).
    small = dataclasses.replace(CONFIG, verdict_timeline_cap=5)
    s = JournalStore(str(tmp_path / "capped.db"), small)
    try:
        s.insert_thesis(_thesis())
        for i in range(12):
            s.append_verdict_event(
                VerdictEventRecord("t1", float(i), float(i), "pending", f"e{i}", None, None, None)
            )
        events = s.verdict_events("t1")
        assert len(events) == 5  # capped
        # The SURVIVORS are the most-recent five, in insertion order (oldest pruned).
        assert [e.evidence for e in events] == ["e7", "e8", "e9", "e10", "e11"]
    finally:
        s.close()


def test_no_tape_data_columns_in_schema(store):
    # Persistence is scoped to research records — there is no trades/quotes/candles table.
    conn = store._read_conn()
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {r["name"] for r in rows}
    finally:
        conn.close()
    for forbidden in ("trades", "quotes", "candles", "features", "events"):
        assert forbidden not in names, f"tape-data table {forbidden} must not exist"
