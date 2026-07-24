"""Journal store discipline (capability 28): WAL, writer queue, temp-path injection, schema_version.

era-5D J-01 ("The Clean Slate" demolition interlude, I-8 UPDATE row): the journal-era thesis /
verdict-event / action / study / hint method coverage that used to live in this file was dropped
along with the deleted ``JournalStore`` methods and record dataclasses (``ThesisRecord``,
``ActionRecord``, ``VerdictEventRecord`` — I-3). This file KEEPS the generic store-infrastructure
coverage (WAL mode, schema presence including the now-dormant journal-era tables, writer-queue
serialization, closed-store write refusal, the persistence-scope guard) — none of it is
thesis-specific, and it stays true of the slimmed store. The backtest/PnL-ledger/champion-pointer
method coverage this file's docstring used to promise living alongside the thesis tests was never
actually here — it lives in ``test_backtests.py``/``test_pnl_ledger.py``/``test_pnl_history.py``,
all unmodified. The two generic infra tests below that used to write through a (now-deleted)
thesis method are reworked to write through the KEPT ``insert_backtest`` instead — same behaviour
under test, a different (kept) write vehicle."""

import pytest

from app.config import CONFIG
from app.research.store import BacktestRecord, JournalStore


def _backtest(bid: str = "b1") -> BacktestRecord:
    return BacktestRecord(
        id=bid,
        payload={"id": bid, "status": "queued"},
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
    # The FULL versioned schema is created at once (capability 28) — including the journal-era
    # tables (theses/verdict_events/hints/actions/studies/study_occurrences) that era-5D J-01 left
    # DORMANT rather than dropped (migrations are history; no v9; no table drops — T-4).
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
        "backtests",
        "pnl_ledger",
        "champion_pointer",
    ):
        assert table in names, f"missing table {table}"


def test_writer_queue_serializes_concurrent_writes(store):
    # Many writes enqueued from multiple threads must all land (single writer worker serializes them
    # under BEGIN IMMEDIATE — no "database is locked", no lost write).
    import threading

    n = 50
    errors = []

    def writer(i: int) -> None:
        try:
            store.insert_backtest(_backtest(bid=f"b{i}"))
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(store.list_backtests(limit=n + 10)) == n


def test_writes_after_close_raise(tmp_path):
    s = JournalStore(str(tmp_path / "j.db"), CONFIG)
    s.close()
    with pytest.raises(RuntimeError):
        s.insert_backtest(_backtest())


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
