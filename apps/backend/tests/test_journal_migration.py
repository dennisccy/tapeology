"""Versioned journal-store migration (capability 28) — the class of defect temp-DB unit tests
structurally cannot see (iter-5).

A fresh ``JournalStore`` creates the schema at the CURRENT version, so a temp-path test never
exercises the v1 -> v2 path. These tests open the store against a PRE-EXISTING v1 DB (built from the
committed ``fixtures/journal_v1_schema.sql`` — research records only, no tape data) and assert:

  * the v1 -> v2 migration adds ``verdict_events.rule_first_true_{ts,price}`` and bumps
    ``schema_version`` to 2;
  * pre-existing rows are INTACT and keep ``NULL`` rule_first_true (never backfilled — the timeline
    is append-only);
  * a thesis declares end-to-end against the migrated DB (no 503);
  * re-opening an already-v2 DB is idempotent (no crash, version stays 2);
  * a stale version row whose columns are ALREADY present does not crash the open;
  * a forced failure on the initial verdict-event insert leaves NO thesis row (atomic declaration);
  * the startup sweep resolves a zero-event active (orphan) thesis to ``expired`` (the SIM-BUYER /
    SIM-SELLER orphans the dev DB carries).
"""

import dataclasses
import sqlite3
from pathlib import Path

import pytest

from app.config import CONFIG
from app.research.store import ActionRecord, JournalStore, ThesisRecord, VerdictEventRecord

FIXTURE_SQL = Path(__file__).parent / "fixtures" / "journal_v1_schema.sql"
FIXTURE_V2_SQL = Path(__file__).parent / "fixtures" / "journal_v2_schema.sql"
FIXTURE_V3_SQL = Path(__file__).parent / "fixtures" / "journal_v3_schema.sql"
FIXTURE_V4_SQL = Path(__file__).parent / "fixtures" / "journal_v4_schema.sql"


def _build_v1_db(path: str) -> None:
    """Materialize the committed v1-schema SQL fixture into a real SQLite DB at ``path``."""
    sql = FIXTURE_SQL.read_text()
    conn = sqlite3.connect(path)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def _build_v2_db(path: str) -> None:
    """Materialize the committed v2-schema SQL fixture into a real SQLite DB at ``path``."""
    sql = FIXTURE_V2_SQL.read_text()
    conn = sqlite3.connect(path)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def _build_v3_db(path: str) -> None:
    """Materialize the committed v3-schema SQL fixture into a real SQLite DB at ``path``."""
    sql = FIXTURE_V3_SQL.read_text()
    conn = sqlite3.connect(path)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def _build_v4_db(path: str) -> None:
    """Materialize the committed v4-schema SQL fixture into a real SQLite DB at ``path``."""
    sql = FIXTURE_V4_SQL.read_text()
    conn = sqlite3.connect(path)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def _theses_columns(path: str) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {r[1] for r in conn.execute("PRAGMA table_info(theses)").fetchall()}
    finally:
        conn.close()


def _verdict_event_columns(path: str) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {r[1] for r in conn.execute("PRAGMA table_info(verdict_events)").fetchall()}
    finally:
        conn.close()


def _actions_columns(path: str) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {r[1] for r in conn.execute("PRAGMA table_info(actions)").fetchall()}
    finally:
        conn.close()


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


def _pending_event(tid: str = "t1") -> VerdictEventRecord:
    return VerdictEventRecord(
        thesis_id=tid,
        logical_ts=12.5,
        wall_ts=1700000000.0,
        verdict="pending",
        evidence="Thesis declared.",
        tape_state="bid_absorption",
        confidence=0.6,
        last=100.0,
    )


# --- the committed v1-schema fixture is real and v1 -------------------------------------------------

def test_fixture_starts_at_v1_without_the_new_columns(tmp_path):
    db = str(tmp_path / "v1.db")
    _build_v1_db(db)
    cols = _verdict_event_columns(db)
    assert "rule_first_true_ts" not in cols
    assert "rule_first_true_price" not in cols
    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT version FROM schema_version").fetchone()[0] == 1
        # The fixture carries research records ONLY — no tape-data tables.
        names = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    finally:
        conn.close()
    for forbidden in ("trades", "quotes", "candles", "features"):
        assert forbidden not in names


# --- v1 -> v2 migration on open --------------------------------------------------------------------

def test_open_migrates_v1_to_v2_adding_columns_and_bumping_version(tmp_path):
    db = str(tmp_path / "v1.db")
    _build_v1_db(db)
    store = JournalStore(db, CONFIG)
    try:
        # A v1 DB now migrates all the way up to the CURRENT target (v3); the v1 -> v2 columns are
        # present after the chained migration.
        assert store.schema_version() == CONFIG.journal_schema_version
        cols = _verdict_event_columns(db)
        assert "rule_first_true_ts" in cols
        assert "rule_first_true_price" in cols
    finally:
        store.close()


def test_migration_does_not_backfill_pre_existing_rows(tmp_path):
    # The append-only timeline is NEVER backfilled: the two pre-existing v1 verdict events keep NULL
    # rule_first_true after the column is added, and their other values are untouched.
    db = str(tmp_path / "v1.db")
    _build_v1_db(db)
    store = JournalStore(db, CONFIG)
    try:
        events = store.verdict_events("v1thesis0001")
        assert [e.verdict for e in events] == ["pending", "expired"]
        for e in events:
            assert e.rule_first_true_ts is None
            assert e.rule_first_true_price is None
        # Pre-existing values intact (not rewritten by the migration).
        assert events[0].tape_state == "bid_absorption"
        assert events[0].confidence == 0.6
        assert events[1].verdict == "expired"
        thesis = store.get_thesis("v1thesis0001")
        assert thesis is not None
        assert thesis.status == "expired"
        assert thesis.config_fingerprint == "oldfingerprint00"  # the old stamp is preserved
    finally:
        store.close()


def test_declare_succeeds_end_to_end_against_migrated_db(tmp_path):
    # The defining defect: a declaration against an OLD DB used to 503 at the initial verdict-event
    # INSERT (missing columns). After migration it must succeed and the timeline starts cleanly.
    db = str(tmp_path / "v1.db")
    _build_v1_db(db)
    store = JournalStore(db, CONFIG)
    try:
        store.insert_thesis_with_event(_thesis(tid="new1", ticker="SIM-BUYER"), _pending_event("new1"))
        active = store.get_active_thesis("SIM-BUYER")
        assert active is not None and active.id == "new1"
        events = store.verdict_events("new1")
        assert len(events) == 1
        assert events[0].verdict == "pending"
    finally:
        store.close()


# --- idempotency / stale-version guards ------------------------------------------------------------

def test_reopen_already_migrated_is_idempotent(tmp_path):
    db = str(tmp_path / "v1.db")
    _build_v1_db(db)
    JournalStore(db, CONFIG).close()  # first open migrates up to the current version
    store = JournalStore(db, CONFIG)  # second open must be a no-op, not a crash
    try:
        assert store.schema_version() == CONFIG.journal_schema_version
        cols = _verdict_event_columns(db)
        assert "rule_first_true_ts" in cols
        assert "rule_first_true_price" in cols
    finally:
        store.close()


def test_stale_version_row_with_columns_present_does_not_crash(tmp_path):
    # Belt-and-braces: a DB whose verdict_events ALREADY carries the v2 columns but whose version row
    # is stale at 1 (e.g. tables recreated at the new shape by CREATE TABLE but the version never
    # bumped). The PRAGMA table_info guard makes the ALTERs no-op and the open just bumps the version.
    db = str(tmp_path / "v1.db")
    _build_v1_db(db)
    conn = sqlite3.connect(db)
    try:
        conn.execute("ALTER TABLE verdict_events ADD COLUMN rule_first_true_ts REAL")
        conn.execute("ALTER TABLE verdict_events ADD COLUMN rule_first_true_price REAL")
        conn.commit()  # version row still says 1
    finally:
        conn.close()
    store = JournalStore(db, CONFIG)  # must not raise "duplicate column name"
    try:
        # The stale row at 1 with v2 columns present chains v1 -> v2 (no-op ALTERs) -> v3 cleanly.
        assert store.schema_version() == CONFIG.journal_schema_version
    finally:
        store.close()


def test_fresh_temp_db_is_created_at_current_version_no_migration(tmp_path):
    store = JournalStore(str(tmp_path / "fresh.db"), CONFIG)
    try:
        assert store.schema_version() == CONFIG.journal_schema_version
        cols = _verdict_event_columns(str(tmp_path / "fresh.db"))
        assert {"rule_first_true_ts", "rule_first_true_price"} <= cols
        # A fresh DB created at the current version already carries the v3 action column.
        actions_cols = _actions_columns(str(tmp_path / "fresh.db"))
        assert "spread_at_mark" in actions_cols
        # ...and the v4 theses.risk_flags column (J-49).
        assert "risk_flags" in _theses_columns(str(tmp_path / "fresh.db"))
    finally:
        store.close()


# --- v2 -> v3 migration on open (J-52: actions.spread_at_mark) -------------------------------------

def test_v2_fixture_starts_at_v2_without_spread_at_mark(tmp_path):
    db = str(tmp_path / "v2.db")
    _build_v2_db(db)
    cols = _actions_columns(db)
    assert "spread_at_mark" not in cols
    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT version FROM schema_version").fetchone()[0] == 2
        names = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    finally:
        conn.close()
    for forbidden in ("trades", "quotes", "candles", "features"):
        assert forbidden not in names


def test_open_migrates_v2_to_v3_adding_spread_column_and_bumping_version(tmp_path):
    db = str(tmp_path / "v2.db")
    _build_v2_db(db)
    store = JournalStore(db, CONFIG)
    try:
        # A v2 DB now chains all the way up to the CURRENT target (v4); the v2 -> v3 spread column is
        # present after the chained migration.
        assert store.schema_version() == CONFIG.journal_schema_version
        assert "spread_at_mark" in _actions_columns(db)
        # The pre-existing v2 dwell columns are untouched (the v2 -> v3 step only touches actions).
        assert {"rule_first_true_ts", "rule_first_true_price"} <= _verdict_event_columns(db)
    finally:
        store.close()


def test_v3_migration_does_not_backfill_pre_existing_action(tmp_path):
    # The append-only discipline extends to action marks: the pre-existing v2 entry mark keeps NULL
    # spread_at_mark after the column is added (a moment value is never recomputed), and its verbatim
    # price/timestamps are intact.
    db = str(tmp_path / "v2.db")
    _build_v2_db(db)
    store = JournalStore(db, CONFIG)
    try:
        actions = store.get_actions("v2thesis0001")
        assert len(actions) == 1
        a = actions[0]
        assert a.kind == "entry"
        assert a.price == 100.0  # verbatim, intact
        assert a.logical_ts == 15.0
        assert a.spread_at_mark is None  # never backfilled
        # has_entry still works against the migrated DB (the anti-survivorship guard reads it).
        assert store.has_entry_mark("v2thesis0001") is True
    finally:
        store.close()


def test_action_records_end_to_end_against_migrated_v2_db(tmp_path):
    # A NEW action (with a spread) records cleanly against the migrated DB and reads back verbatim.
    db = str(tmp_path / "v2.db")
    _build_v2_db(db)
    store = JournalStore(db, CONFIG)
    try:
        store.insert_action(
            ActionRecord("new-exit", "v2thesis0001", "exit", 101.5, 20.0, 1700000099.0, 0.03)
        )
        actions = store.get_actions("v2thesis0001")
        assert {a.kind for a in actions} == {"entry", "exit"}
        new_exit = next(a for a in actions if a.kind == "exit")
        assert new_exit.price == 101.5
        assert new_exit.spread_at_mark == 0.03
    finally:
        store.close()


def test_reopen_already_v3_is_idempotent_from_v2(tmp_path):
    db = str(tmp_path / "v2.db")
    _build_v2_db(db)
    JournalStore(db, CONFIG).close()  # first open migrates v2 -> v3 -> v4 (chained to current)
    store = JournalStore(db, CONFIG)  # second open must be a no-op
    try:
        assert store.schema_version() == CONFIG.journal_schema_version
        assert "spread_at_mark" in _actions_columns(db)
    finally:
        store.close()


def test_stale_v2_version_row_with_spread_column_present_does_not_crash(tmp_path):
    # Belt-and-braces: a DB whose actions ALREADY carries spread_at_mark but whose version row is
    # stale at 2. The PRAGMA table_info guard makes the ALTER a no-op and the open just bumps to v3.
    db = str(tmp_path / "v2.db")
    _build_v2_db(db)
    conn = sqlite3.connect(db)
    try:
        conn.execute("ALTER TABLE actions ADD COLUMN spread_at_mark REAL")
        conn.commit()  # version row still says 2
    finally:
        conn.close()
    store = JournalStore(db, CONFIG)  # must not raise "duplicate column name"
    try:
        # The stale row at 2 with the v3 column present chains v2 -> v3 (no-op ALTER) -> v4 cleanly.
        assert store.schema_version() == CONFIG.journal_schema_version
    finally:
        store.close()


# --- v3 -> v4 migration on open (J-49: theses.risk_flags) -----------------------------------------

def test_v3_fixture_starts_at_v3_without_risk_flags(tmp_path):
    db = str(tmp_path / "v3.db")
    _build_v3_db(db)
    cols = _theses_columns(db)
    assert "risk_flags" not in cols
    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT version FROM schema_version").fetchone()[0] == 3
        names = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    finally:
        conn.close()
    for forbidden in ("trades", "quotes", "candles", "features"):
        assert forbidden not in names


def test_open_migrates_v3_to_v4_adding_risk_flags_column_and_bumping_version(tmp_path):
    db = str(tmp_path / "v3.db")
    _build_v3_db(db)
    store = JournalStore(db, CONFIG)
    try:
        # A v3 DB now chains all the way up to the CURRENT target (v5); the v3 -> v4 risk_flags
        # column is present after the chained migration.
        assert store.schema_version() == CONFIG.journal_schema_version
        assert "risk_flags" in _theses_columns(db)
        # The pre-existing v2/v3 columns are untouched (the v3 -> v4 step only touches theses).
        assert "spread_at_mark" in _actions_columns(db)
        assert {"rule_first_true_ts", "rule_first_true_price"} <= _verdict_event_columns(db)
    finally:
        store.close()


def test_v4_migration_does_not_backfill_pre_existing_thesis(tmp_path):
    # The append-only discipline extends to the frozen risk flags: the pre-existing v3 thesis keeps
    # NULL risk_flags after the column is added (a pre-migration thesis was never risk-assessed — its
    # flags are never fabricated), and its verbatim fields are intact.
    db = str(tmp_path / "v3.db")
    _build_v3_db(db)
    store = JournalStore(db, CONFIG)
    try:
        thesis = store.get_thesis("v3thesis0001")
        assert thesis is not None
        assert thesis.risk_flags is None  # NULL -> None: never assessed, never backfilled
        # Verbatim fields intact (not rewritten by the migration).
        assert thesis.setup_type == "trend_continuation"
        assert thesis.invalidation_price == 98.0
        assert thesis.config_fingerprint == "oldfingerprint03"
        assert thesis.status == "active"
    finally:
        store.close()


def test_pre_migration_thesis_projection_omits_risk_flags_key(tmp_path):
    # Honest-omission semantics: a pre-v4 thesis (NULL risk_flags) is served through the SAME single
    # build_projection — and its projection OMITS the risk_flags key entirely (an absent key means
    # "never assessed"; an empty list would dishonestly mean "assessed, nothing fired").
    from app.research.monitor import build_projection

    db = str(tmp_path / "v3.db")
    _build_v3_db(db)
    store = JournalStore(db, CONFIG)
    try:
        thesis = store.get_thesis("v3thesis0001")
        proj = build_projection(
            thesis,
            store.get_actions(thesis.id),
            config=CONFIG,
            snapshot=None,
            status=thesis.status,
            verdict="pending",
            verdict_evidence="ev",
            monitor_status="ok",
            verdict_events=store.verdict_events(thesis.id),
        )
        assert "risk_flags" not in proj  # absent, NOT an empty list
    finally:
        store.close()


def test_thesis_with_risk_flags_records_end_to_end_against_migrated_v3_db(tmp_path):
    # A NEW thesis WITH frozen risk flags records cleanly against the migrated DB and reads back
    # verbatim (the empty-list vs absent distinction is preserved through the round-trip).
    db = str(tmp_path / "v3.db")
    _build_v3_db(db)
    store = JournalStore(db, CONFIG)
    try:
        flags = [
            {
                "flag": "before_warmup",
                "label": "Declared before warm-up",
                "evidence": "declared after 5 trades, below the 40-trade warm-up",
                "measured": {"trade_count": 5, "warmup_min_events": 40},
            }
        ]
        store.insert_thesis(
            dataclasses.replace(
                _thesis(tid="flagged1", ticker="SIM-CHOP", status="active"),
                risk_flags=flags,
            )
        )
        back = store.get_thesis("flagged1")
        assert back.risk_flags == flags  # verbatim round-trip
        # An assessed-nothing-fired thesis round-trips as an EMPTY list (distinct from None/absent).
        store.insert_thesis(
            dataclasses.replace(
                _thesis(tid="clean1", ticker="SIM-SELLER", status="active"),
                risk_flags=[],
            )
        )
        clean = store.get_thesis("clean1")
        assert clean.risk_flags == []  # assessed, nothing fired — NOT None
    finally:
        store.close()


def test_reopen_already_v4_is_idempotent_from_v3(tmp_path):
    db = str(tmp_path / "v3.db")
    _build_v3_db(db)
    JournalStore(db, CONFIG).close()  # first open migrates v3 -> v4 -> v5 (chained to current)
    store = JournalStore(db, CONFIG)  # second open must be a no-op
    try:
        assert store.schema_version() == CONFIG.journal_schema_version
        assert "risk_flags" in _theses_columns(db)
    finally:
        store.close()


def test_stale_v3_version_row_with_risk_flags_column_present_does_not_crash(tmp_path):
    # Belt-and-braces: a DB whose theses ALREADY carries risk_flags but whose version row is stale at
    # 3. The PRAGMA table_info guard makes the ALTER a no-op and the open just bumps to v4.
    db = str(tmp_path / "v3.db")
    _build_v3_db(db)
    conn = sqlite3.connect(db)
    try:
        conn.execute("ALTER TABLE theses ADD COLUMN risk_flags TEXT")
        conn.commit()  # version row still says 3
    finally:
        conn.close()
    store = JournalStore(db, CONFIG)  # must not raise "duplicate column name"
    try:
        # The stale row at 3 with the v4 column present chains v3 -> v4 (no-op ALTER) -> v5 cleanly.
        assert store.schema_version() == CONFIG.journal_schema_version
    finally:
        store.close()


# --- atomic declaration ----------------------------------------------------------------------------

class _FaultInjectingConn:
    """A thin proxy around a real sqlite3 connection that raises on a targeted INSERT.

    ``sqlite3.Connection`` is an immutable C type (cannot be monkeypatched), so we wrap the store's
    write connection in this proxy to fault-inject the initial verdict-event INSERT — exercising the
    rollback of the single declaration transaction.
    """

    def __init__(self, conn: sqlite3.Connection, fail_on: str) -> None:
        self._conn = conn
        self._fail_on = fail_on

    def execute(self, sql, *args, **kwargs):
        if isinstance(sql, str) and self._fail_on in sql:
            raise sqlite3.OperationalError("injected fault on the initial verdict-event insert")
        return self._conn.execute(sql, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._conn, name)


def test_atomic_declare_rolls_back_both_on_event_insert_failure(tmp_path):
    # Force a failure DURING the single declaration transaction, after the thesis INSERT but on the
    # verdict-event INSERT. The whole transaction must roll back: NO thesis row, NO event — never a
    # half-saved orphan (the iter-4 two-transaction defect that left active theses with zero events).
    db = str(tmp_path / "fresh.db")
    store = JournalStore(db, CONFIG)
    try:
        # Swap the writer connection for a proxy that raises on the initial verdict-event INSERT.
        store._write_conn = _FaultInjectingConn(store._write_conn, "INSERT INTO verdict_events")
        with pytest.raises(sqlite3.OperationalError):
            store.insert_thesis_with_event(_thesis(tid="x1", ticker="SIM-BUYER"), _pending_event("x1"))
        # Restore the real connection so the reads below (and close) work normally.
        store._write_conn = store._write_conn._conn
        # NO partial save: neither the thesis row nor any verdict event survives.
        assert store.get_thesis("x1") is None
        assert store.get_active_thesis("SIM-BUYER") is None
        assert store.verdict_events("x1") == []
    finally:
        store.close()


def test_atomic_declare_persists_both_rows_in_one_go(tmp_path):
    db = str(tmp_path / "fresh.db")
    store = JournalStore(db, CONFIG)
    try:
        store.insert_thesis_with_event(
            _thesis(tid="ok1", ticker="SIM-BUYER"),
            dataclasses.replace(_pending_event("ok1"), rule_first_true_ts=None),
        )
        assert store.get_thesis("ok1") is not None
        events = store.verdict_events("ok1")
        assert len(events) == 1 and events[0].verdict == "pending"
        # The initial pending row records no spurious rule_first_true timing.
        assert events[0].rule_first_true_ts is None
        assert events[0].rule_first_true_price is None
    finally:
        store.close()


# --- startup sweep over a zero-event active (orphan) thesis ---------------------------------------

def test_startup_sweep_expires_zero_event_active_orphan(tmp_path):
    # The dev DB carried active theses with ZERO verdict events (the orphan defect). The generic
    # "active -> expired" sweep must resolve them regardless of event count and append the final
    # expired event — leaving the row visible (no survivorship pruning) so a fresh declaration on the
    # same ticker no longer 409s.
    db = str(tmp_path / "fresh.db")
    store = JournalStore(db, CONFIG)
    try:
        store.insert_thesis(_thesis(tid="orphan", ticker="SIM-BUYER", status="active"))  # NO event
        assert store.verdict_events("orphan") == []
        assert store.get_active_thesis("SIM-BUYER") is not None
        affected = store.expire_stale_actives(1700000999.0)
        assert affected == ["orphan"]
        assert store.get_thesis("orphan").status == "expired"  # row retained, not deleted
        assert store.get_active_thesis("SIM-BUYER") is None  # a fresh declare no longer 409s
        events = store.verdict_events("orphan")
        assert len(events) == 1 and events[-1].verdict == "expired"
    finally:
        store.close()


def _execution_checks_columns(path: str) -> set[str]:
    conn = sqlite3.connect(path)
    try:
        return {r[1] for r in conn.execute("PRAGMA table_info(theses)").fetchall()}
    finally:
        conn.close()


# --- v4 -> v5 migration on open (J-54: theses.execution_checks) -----------------------------------

def test_v4_fixture_starts_at_v4_without_execution_checks(tmp_path):
    db = str(tmp_path / "v4.db")
    _build_v4_db(db)
    cols = _theses_columns(db)
    assert "execution_checks" not in cols
    # The v4 risk_flags column IS present (added by the v3 -> v4 migration).
    assert "risk_flags" in cols
    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT version FROM schema_version").fetchone()[0] == 4
        names = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
    finally:
        conn.close()
    for forbidden in ("trades", "quotes", "candles", "features"):
        assert forbidden not in names


def test_open_migrates_v4_to_v5_adding_execution_checks_column_and_bumping_version(tmp_path):
    db = str(tmp_path / "v4.db")
    _build_v4_db(db)
    store = JournalStore(db, CONFIG)
    try:
        assert store.schema_version() == 5 == CONFIG.journal_schema_version
        assert "execution_checks" in _theses_columns(db)
        # The pre-existing v2/v3/v4 columns are untouched (the v4 -> v5 step only touches theses).
        assert "risk_flags" in _theses_columns(db)
        assert "spread_at_mark" in _actions_columns(db)
        assert {"rule_first_true_ts", "rule_first_true_price"} <= _verdict_event_columns(db)
    finally:
        store.close()


def test_v5_migration_does_not_backfill_pre_existing_resolved_thesis(tmp_path):
    # The append-only/honest-omission discipline extends to execution checks: the pre-existing v4
    # RESOLVED thesis keeps NULL execution_checks after the column is added (a pre-migration
    # resolution never had its checks computed — they are never fabricated/backfilled at read), and
    # its verbatim fields are intact.
    db = str(tmp_path / "v4.db")
    _build_v4_db(db)
    store = JournalStore(db, CONFIG)
    try:
        thesis = store.get_thesis("v4thesis0001")
        assert thesis is not None
        assert thesis.execution_checks is None  # NULL -> None: never computed, never backfilled
        # Verbatim fields intact (not rewritten by the migration).
        assert thesis.setup_type == "trend_continuation"
        assert thesis.invalidation_price == 98.0
        assert thesis.config_fingerprint == "oldfingerprint04"
        assert thesis.status == "played_out"
        # The v4 risk_flags round-trips: an empty list (assessed, nothing fired) — NOT None.
        assert thesis.risk_flags == []
    finally:
        store.close()


def test_pre_migration_thesis_detail_omits_execution_checks_key(tmp_path):
    # Honest-omission semantics on the served detail: a pre-v5 resolved thesis (NULL
    # execution_checks) — read through the SAME GET /research/journal/{id} serving path — OMITS the
    # execution_checks key entirely (absent means "never computed"; an empty object would dishonestly
    # mean "computed, no checks fired").
    from app.research.routes import build_journal_detail

    db = str(tmp_path / "v4.db")
    _build_v4_db(db)
    store = JournalStore(db, CONFIG)
    try:
        detail = build_journal_detail(store, "v4thesis0001", CONFIG)
        assert detail is not None
        assert "execution_checks" not in detail
        assert "suggested_mistake_tags" not in detail
    finally:
        store.close()


def test_thesis_with_execution_checks_records_end_to_end_against_migrated_v4_db(tmp_path):
    # A thesis whose execution checks are SET (the resolution path) records cleanly against the
    # migrated DB and reads back verbatim (the absent vs present distinction is preserved).
    db = str(tmp_path / "v4.db")
    _build_v4_db(db)
    store = JournalStore(db, CONFIG)
    try:
        checks = {
            "checks": [
                {
                    "check": "entered_before_confirmation",
                    "status": "failed",
                    "evidence": "entry at 12.5 precedes the first confirming publish at 18.0",
                }
            ],
            "suggested_mistake_tags": ["entered_before_confirmation"],
        }
        store.set_execution_checks("v4thesis0001", checks)
        back = store.get_thesis("v4thesis0001")
        assert back.execution_checks == checks  # verbatim round-trip
    finally:
        store.close()


def test_reopen_already_v5_is_idempotent_from_v4(tmp_path):
    db = str(tmp_path / "v4.db")
    _build_v4_db(db)
    JournalStore(db, CONFIG).close()  # first open migrates v4 -> v5
    store = JournalStore(db, CONFIG)  # second open must be a no-op
    try:
        assert store.schema_version() == 5
        assert "execution_checks" in _theses_columns(db)
    finally:
        store.close()


def test_stale_v4_version_row_with_execution_checks_column_present_does_not_crash(tmp_path):
    # Belt-and-braces: a DB whose theses ALREADY carries execution_checks but whose version row is
    # stale at 4. The PRAGMA table_info guard makes the ALTER a no-op and the open just bumps to v5.
    db = str(tmp_path / "v4.db")
    _build_v4_db(db)
    conn = sqlite3.connect(db)
    try:
        conn.execute("ALTER TABLE theses ADD COLUMN execution_checks TEXT")
        conn.commit()  # version row still says 4
    finally:
        conn.close()
    store = JournalStore(db, CONFIG)  # must not raise "duplicate column name"
    try:
        assert store.schema_version() == 5
    finally:
        store.close()
