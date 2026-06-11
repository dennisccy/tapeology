"""Journal store discipline (capability 28): WAL, writer queue, temp-path injection, schema_version,
append-only verdict_events repository."""

import dataclasses
import json

import pytest

from app.config import CONFIG
from app.research.store import (
    ActionRecord,
    JournalStore,
    ThesisRecord,
    VerdictEventRecord,
)


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


def test_startup_sweep_exempts_entry_marked_actives(store):
    # J-47 (and J-51's "entry-marked survives restart" leg, pre-built here): a backend restart MUST
    # NOT expire a surviving entry-marked active thesis — a real position is never orphaned. An
    # UNMARKED stale active is still expired with its explicit interruption reason.
    store.insert_thesis(_thesis(tid="marked", status="active"))
    store.insert_thesis(_thesis(tid="unmarked", status="active"))
    store.insert_action(
        ActionRecord(id="a1", thesis_id="marked", kind="entry", price=100.0,
                     logical_ts=1.0, wall_ts=1700000001.0, spread_at_mark=0.02)
    )
    affected = store.expire_stale_actives(1700000123.0)
    # Only the unmarked thesis is expired; the entry-marked one survives as active.
    assert affected == ["unmarked"]
    assert store.get_thesis("marked").status == "active"
    assert store.get_thesis("unmarked").status == "expired"
    # NO expiry event was appended for the surviving (exempt) thesis — nothing recorded while it
    # survives unwatched (append-only / no fabricated event).
    assert store.verdict_events("marked") == []
    # The unmarked thesis got its explicit interruption reason.
    unmarked_events = store.verdict_events("unmarked")
    assert unmarked_events[-1].verdict == "expired"
    assert "restart" in unmarked_events[-1].evidence


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


# --- user resolution path (J-50): atomic status flip + appended final event ----------------------

def test_resolve_thesis_with_event_flips_status_and_appends_final_event(store):
    store.insert_thesis(_thesis())
    store.append_verdict_event(
        VerdictEventRecord("t1", 1.0, 100.0, "pending", "declared", "bid_absorption", 0.8, 100.0)
    )
    store.resolve_thesis_with_event(
        "t1",
        "played_out",
        VerdictEventRecord(
            "t1", 5.0, 1700000500.0, "played_out", "you resolved it", "bid_absorption", 0.7, 100.4
        ),
    )
    assert store.get_thesis("t1").status == "played_out"
    events = store.verdict_events("t1")
    # The prior pending row is byte-identical (append-only); the resolution is a NEW appended row.
    assert [e.verdict for e in events] == ["pending", "played_out"]
    assert events[0].evidence == "declared"
    final = events[-1]
    assert final.verdict == "played_out"
    assert final.logical_ts == 5.0
    assert final.wall_ts == 1700000500.0
    assert final.last == 100.4


def test_resolve_with_event_is_atomic_failure_leaves_status_unflipped(store):
    # A failure during the resolve transaction rolls BOTH back — no half-state (status flipped but no
    # event, or vice-versa). Fault-inject on the verdict_events INSERT.
    store.insert_thesis(_thesis())
    real = store._write_conn
    store._write_conn = _FaultInjectingConn(real, "INSERT INTO verdict_events")
    with pytest.raises(Exception):
        store.resolve_thesis_with_event(
            "t1",
            "abandoned",
            VerdictEventRecord("t1", 5.0, 5.0, "abandoned", "x", None, None, None),
        )
    store._write_conn = real
    # Status NOT flipped and NO timeline event appended (clean rollback).
    assert store.get_thesis("t1").status == "active"
    assert store.verdict_events("t1") == []


def test_insert_and_read_actions_roundtrip(store):
    store.insert_thesis(_thesis())
    assert store.get_actions("t1") == []
    assert store.has_entry_mark("t1") is False
    store.insert_action(ActionRecord("a1", "t1", "entry", 100.25, 12.0, 1700000010.0))
    actions = store.get_actions("t1")
    assert len(actions) == 1
    assert actions[0].kind == "entry"
    assert actions[0].price == 100.25
    assert store.has_entry_mark("t1") is True


def test_has_entry_mark_false_for_exit_only(store):
    store.insert_thesis(_thesis())
    store.insert_action(ActionRecord("x1", "t1", "exit", 101.0, 20.0, 1700000020.0))
    # An exit-only thesis carries no ENTRY mark (the anti-survivorship guard keys on entry).
    assert store.has_entry_mark("t1") is False


# --- journal LIST query (J-51): filters / pagination / ordering over persisted rows ------------
# The read-only list query that backs ``GET /research/journal``. Reads persisted rows VERBATIM (no
# recomputation), newest-declared-first, with the goal.md filters (ticker, setup_type, direction,
# resolution, status) + limit/offset. NO schema change (journal_schema_version stays 4).


def _declared_thesis(
    tid: str,
    *,
    ticker: str = "SIM-BUYER",
    setup_type: str = "trend_continuation",
    direction: str = "long",
    status: str = "active",
    created_wall_ts: float,
    bound_source: str = "buyer_control",
    data_feed: str = "sim",
) -> ThesisRecord:
    """A thesis with a distinct created_wall_ts so ordering is deterministic in the list tests."""
    return ThesisRecord(
        id=tid,
        ticker=ticker,
        setup_type=setup_type,
        direction=direction,
        invalidation_price=99.0,
        level_price=None,
        status=status,
        bound_source=bound_source,
        data_feed=data_feed,
        config_fingerprint="abc123",
        entry_context={"last": 100.0, "tape_state": "buyer_control"},
        statements=[{"text": "x", "kind": "tape_state_is", "params": {"states": ["buyer_control"]}}],
        created_logical_ts=12.5,
        created_wall_ts=created_wall_ts,
    )


def test_list_theses_empty_store_is_empty_list(store):
    assert store.list_theses() == []


def test_list_theses_orders_newest_declared_first(store):
    store.insert_thesis(_declared_thesis("old", created_wall_ts=1700000000.0))
    store.insert_thesis(_declared_thesis("mid", created_wall_ts=1700000100.0))
    store.insert_thesis(_declared_thesis("new", created_wall_ts=1700000200.0))
    rows = store.list_theses()
    assert [r.id for r in rows] == ["new", "mid", "old"]


def test_list_theses_filters_by_ticker(store):
    store.insert_thesis(_declared_thesis("a", ticker="SIM-BUYER", created_wall_ts=1.0))
    store.insert_thesis(_declared_thesis("b", ticker="SIM-SELLER", created_wall_ts=2.0))
    rows = store.list_theses(ticker="SIM-SELLER")
    assert [r.id for r in rows] == ["b"]


def test_list_theses_filters_by_setup_direction_status_resolution(store):
    store.insert_thesis(
        _declared_thesis("a", setup_type="trend_continuation", direction="long",
                         status="active", created_wall_ts=1.0)
    )
    store.insert_thesis(
        _declared_thesis("b", setup_type="absorption_reversal", direction="short",
                         status="played_out", created_wall_ts=2.0)
    )
    store.insert_thesis(
        _declared_thesis("c", setup_type="trend_continuation", direction="long",
                         status="expired", created_wall_ts=3.0)
    )
    assert [r.id for r in store.list_theses(setup_type="trend_continuation")] == ["c", "a"]
    assert [r.id for r in store.list_theses(direction="short")] == ["b"]
    assert [r.id for r in store.list_theses(status="active")] == ["a"]
    # ``resolution`` filters on the same terminal-status column (a resolution IS the terminal status).
    assert [r.id for r in store.list_theses(resolution="played_out")] == ["b"]


def test_list_theses_combined_filters_are_anded(store):
    store.insert_thesis(
        _declared_thesis("a", ticker="SIM-BUYER", setup_type="trend_continuation",
                         direction="long", created_wall_ts=1.0)
    )
    store.insert_thesis(
        _declared_thesis("b", ticker="SIM-BUYER", setup_type="trend_continuation",
                         direction="short", created_wall_ts=2.0)
    )
    rows = store.list_theses(ticker="SIM-BUYER", setup_type="trend_continuation", direction="long")
    assert [r.id for r in rows] == ["a"]


def test_list_theses_limit_and_offset_paginate(store):
    for i in range(5):
        store.insert_thesis(_declared_thesis(f"t{i}", created_wall_ts=float(i)))
    # Newest-first => t4, t3, t2, t1, t0.
    page1 = store.list_theses(limit=2, offset=0)
    page2 = store.list_theses(limit=2, offset=2)
    assert [r.id for r in page1] == ["t4", "t3"]
    assert [r.id for r in page2] == ["t2", "t1"]


def test_list_theses_reads_rows_verbatim(store):
    store.insert_thesis(
        _declared_thesis("v", bound_source="historical AAPL 2024-01-02", data_feed="sip",
                         created_wall_ts=1700000000.0)
    )
    [row] = store.list_theses()
    # The list returns the SAME ThesisRecord shape get_thesis returns (one owner over persisted rows).
    assert row.bound_source == "historical AAPL 2024-01-02"
    assert row.data_feed == "sip"
    assert row.config_fingerprint == "abc123"
    assert row.created_wall_ts == 1700000000.0


# --- restart simulation (J-51): byte-identical readback across a store close / reopen ----------


def test_resolved_thesis_timeline_byte_identical_across_reopen(tmp_path):
    # J-51's defining honesty: a backend restart loses NOTHING and rewrites NOTHING. Persist a
    # resolved thesis + its timeline, CLOSE the store (process end), REOPEN against the same file,
    # and read back the SAME rows byte-for-byte (nothing recomputed at read).
    db = str(tmp_path / "restart.db")
    s1 = JournalStore(db, CONFIG)
    s1.insert_thesis(_declared_thesis("r", status="active", created_wall_ts=1700000000.0))
    s1.append_verdict_event(
        VerdictEventRecord("r", 1.0, 1700000001.0, "pending", "declared", "buyer_control", 0.8, 100.0)
    )
    s1.resolve_thesis_with_event(
        "r",
        "played_out",
        VerdictEventRecord("r", 5.0, 1700000005.0, "played_out", "you resolved it",
                           "buyer_control", 0.7, 100.4),
    )
    before_thesis = s1.get_thesis("r")
    before_events = s1.verdict_events("r")
    s1.close()

    s2 = JournalStore(db, CONFIG)
    try:
        after_thesis = s2.get_thesis("r")
        after_events = s2.verdict_events("r")
        # Byte-identical: the dataclasses compare equal field-for-field across the reopen.
        assert after_thesis == before_thesis
        assert after_events == before_events
        assert after_thesis.status == "played_out"
        assert [e.verdict for e in after_events] == ["pending", "played_out"]
        # The schema version did NOT advance on reopen (no migration triggered — already current).
        assert s2.schema_version() == CONFIG.journal_schema_version == 4
    finally:
        s2.close()


def test_unmarked_active_expires_with_reason_on_reopen_then_sweep(tmp_path):
    # An UNMARKED previously-active thesis is expired (with its explicit interruption reason) by the
    # startup sweep the registry runs on reopen; an ENTRY-MARKED active thesis SURVIVES untouched.
    db = str(tmp_path / "sweep.db")
    s1 = JournalStore(db, CONFIG)
    s1.insert_thesis(_declared_thesis("unmarked", status="active", created_wall_ts=1.0))
    s1.insert_thesis(_declared_thesis("marked", status="active", created_wall_ts=2.0))
    s1.insert_action(ActionRecord("a1", "marked", "entry", 100.0, 1.0, 1700000001.0, 0.02))
    s1.close()

    s2 = JournalStore(db, CONFIG)
    try:
        affected = s2.expire_stale_actives(1700000123.0)
        assert affected == ["unmarked"]
        assert s2.get_thesis("unmarked").status == "expired"
        assert "restart" in s2.verdict_events("unmarked")[-1].evidence
        # The entry-marked position survives as active-but-not-evaluated (never orphaned).
        assert s2.get_thesis("marked").status == "active"
        assert s2.verdict_events("marked") == []
    finally:
        s2.close()


class _FaultInjectingConn:
    """Proxy that raises on a targeted INSERT (``sqlite3.Connection`` is an immutable C type)."""

    def __init__(self, conn, fail_on: str) -> None:
        import sqlite3 as _sqlite3

        self._conn = conn
        self._fail_on = fail_on
        self._OperationalError = _sqlite3.OperationalError

    def execute(self, sql, *args, **kwargs):
        if isinstance(sql, str) and self._fail_on in sql:
            raise self._OperationalError("injected fault")
        return self._conn.execute(sql, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._conn, name)
