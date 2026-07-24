"""Journal-scoped SQLite store (capability 28) — research records ONLY, never tape data.

Discipline mandated by the goal doc and re-stated in the iteration spec:
  * stdlib ``sqlite3`` only;
  * **WAL** journal mode + a **busy_timeout** so a reader never fails on brief writer contention;
  * every write runs under **BEGIN IMMEDIATE** in **ONE writer queue** (a single background worker
    thread) — the actual disk write NEVER happens on the engine's event-processing path or the WS
    serialization path: it is enqueued onto and executed by the dedicated writer worker. The
    enqueuing caller (e.g. the monitor's observer callback) is synchronous-but-fast — it waits only
    for the worker's result handoff, NOT for any reader/WS contention — and a write failure is
    surfaced to it (raised) so the monitor can flip ``monitor_status: failed`` rather than crash the
    feeder. Verdict writes are rare (dwell-gated transitions), so this synchronous handoff is not an
    observable latency source on the hot path;
  * ``verdict_events`` is **append-only at the repository level** — the repository exposes NO update
    or delete for it (the only way history changes is appending a new row);
  * the FULL versioned schema is created at once (theses, verdict_events, hints, actions, studies,
    study_occurrences, schema_version) even though only ``theses`` + ``verdict_events`` are written
    this iteration;
  * **versioned, on-open migrations** carry an OLDER DB up to the current
    ``Config.journal_schema_version`` (capability 28): each pending step runs inside ONE
    ``BEGIN IMMEDIATE`` writer transaction, is idempotent (``PRAGMA table_info`` guards a re-run),
    and NEVER backfills existing rows (the timeline is append-only — old verdict events keep
    ``NULL`` for any column added later). The migration is proven against a committed old-schema
    fixture (research records only), not just freshly-created temp DBs.

The store is constructed with an explicit DB path (the operator's ``TAPEOLOGY_JOURNAL_DB`` or a
test's temp path), so persistence is dependency-injected and hermetic in tests.

era-5D J-01 ("The Clean Slate" demolition interlude): the journal-era THESIS/HINT/STUDY read+write
methods and their record dataclasses were deleted from this class (the ``theses``, ``verdict_events``,
``hints``, ``actions``, ``studies``, ``study_occurrences`` tables stay — dormant, untouched, per the
"migrations are history" discipline: no v9, no table drops, no backfill). This store now serves the
KEPT research surfaces only: backtests, the PnL ledger, and the champion pointer.
"""

from __future__ import annotations

import json
import queue
import sqlite3
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

from ..config import Config, PROFILE_DEFAULT, STRATEGY_V1_ID

# --- Full versioned schema (capability 28) ------------------------------------------------------
# Created at once. Only theses + verdict_events are written this iteration; the rest exist so the
# schema is complete and ``schema_version`` is meaningful from day one. Research records only — no
# trades / quotes / candles / feature series are ever persisted here.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS theses (
    id                  TEXT PRIMARY KEY,
    ticker              TEXT NOT NULL,
    setup_type          TEXT NOT NULL,
    direction           TEXT NOT NULL,
    invalidation_price  REAL NOT NULL,
    level_price         REAL,
    status              TEXT NOT NULL,          -- active | played_out | abandoned | invalidated | expired
    bound_source        TEXT NOT NULL,          -- the snapshot's scenario descriptor (source identity)
    data_feed           TEXT NOT NULL,          -- sim | sip | iex
    config_fingerprint  TEXT NOT NULL,
    entry_context       TEXT NOT NULL,          -- JSON: frozen state/confidence/last/spread/features
    statements          TEXT NOT NULL,          -- JSON: frozen expected-behaviour statements
    created_logical_ts  REAL NOT NULL,
    created_wall_ts     REAL NOT NULL,
    risk_flags          TEXT,                   -- v4: JSON list of frozen entry risk flags (J-49); NULL = never assessed (pre-v4 thesis)
    execution_checks    TEXT,                   -- v5: JSON {checks, suggested_mistake_tags} computed ONCE at resolution (J-54); NULL = never computed (pre-v5 resolution)
    statement_final_statuses TEXT,              -- v6: JSON list of per-statement FINAL statuses persisted ONCE at resolution (J-55); NULL = never recorded (pre-v6 resolution)
    grades              TEXT,                   -- v6: JSON {outcome, process, process_evidence} computed ONCE at resolution (J-56); NULL = never computed (pre-v6 resolution)
    review_tags         TEXT,                   -- v6: JSON list of user-confirmed mistake tags (J-57); NULL = never reviewed
    review_note         TEXT,                   -- v6: the user's free-text review note (J-57); NULL = none / never reviewed
    reviewed            INTEGER NOT NULL DEFAULT 0, -- v6: 1 once the user saved a review (J-57); 0 otherwise
    excursions          TEXT                    -- v7: JSON excursion record {tracked, populations} computed ONCE at terminal resolution / stream-end (J-58); NULL = never measured (pre-v7 resolution)
);

CREATE TABLE IF NOT EXISTS verdict_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    thesis_id           TEXT NOT NULL,
    logical_ts          REAL NOT NULL,
    wall_ts             REAL NOT NULL,
    verdict             TEXT NOT NULL,
    evidence            TEXT NOT NULL,          -- plain-language evidence (no naked verdicts)
    tape_state          TEXT,
    confidence          REAL,
    last                REAL,
    rule_first_true_ts     REAL,                -- first logical instant the raw rule held (capability 24)
    rule_first_true_price  REAL,                -- price at rule_first_true_ts
    FOREIGN KEY (thesis_id) REFERENCES theses (id)
);

CREATE TABLE IF NOT EXISTS hints (
    id                  TEXT PRIMARY KEY,
    ticker              TEXT NOT NULL,
    payload             TEXT NOT NULL,
    created_wall_ts     REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS actions (
    id                  TEXT PRIMARY KEY,
    thesis_id           TEXT NOT NULL,
    kind                TEXT NOT NULL,          -- entry | exit
    price               REAL NOT NULL,          -- recorded VERBATIM from the user (never an inferred fill)
    logical_ts          REAL NOT NULL,
    wall_ts             REAL NOT NULL,
    spread_at_mark      REAL,                   -- v3: snapshot spread at recording (moment value; NULL when no quote)
    FOREIGN KEY (thesis_id) REFERENCES theses (id)
);

CREATE TABLE IF NOT EXISTS studies (
    id                  TEXT PRIMARY KEY,
    payload             TEXT NOT NULL,
    created_wall_ts     REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS study_occurrences (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    study_id            TEXT NOT NULL,
    payload             TEXT NOT NULL,
    FOREIGN KEY (study_id) REFERENCES studies (id)
);

CREATE TABLE IF NOT EXISTS backtests (
    id                  TEXT PRIMARY KEY,
    payload             TEXT NOT NULL,
    created_wall_ts     REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS pnl_ledger (
    enhancement_id      TEXT PRIMARY KEY,
    payload             TEXT NOT NULL,
    created_wall_ts     REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS champion_pointer (
    id                  INTEGER PRIMARY KEY,   -- always 1: a singleton row, the ONE persisted pointer
    strategy_id         TEXT NOT NULL,
    profile             TEXT NOT NULL,
    updated_wall_ts     REAL                    -- NULL = never moved (the seeded founding pointer)
);
"""


@dataclass(frozen=True)
class BacktestRecord:
    """One persisted backtest row (era-3 capability 4, J-03) — read back as an immutable record.

    The ``backtests`` table (added by the v7 -> v8 migration) uses the PAYLOAD-BLOB shape the
    ``studies`` table proved: a backtest's ENTIRE served state lives in the ``payload`` JSON —
    run-identity metadata (id, status, request echo, created timestamp) at the top level and, at
    completion, the DETERMINISTIC ``result`` block (trades, aggregates, seeded null baseline,
    provenance, the simulated register) nested under it, so an identical request re-run is
    byte-identical on exactly that ``result`` unit. The backtest runner
    (``app/research/backtests.py``) is the single owner that computes and builds the payload ONCE
    (Data Contract row 31); the routes + the MCP ``backtests`` proxy serve it VERBATIM (never
    recomputed at read). NO tape data is persisted here — a trade row holds fills, costs, and
    R/$ summaries, never trades/quotes/candles (the persistence-scope anti-goal)."""

    id: str
    payload: dict
    created_wall_ts: float


@dataclass(frozen=True)
class PnlLedgerRecord:
    """One persisted PnL-ledger row (era-3 capability 5, J-04) — read back as an immutable record.

    The ``pnl_ledger`` table (added by the v8 -> v9 migration) uses the PAYLOAD-BLOB shape the
    ``studies`` / ``backtests`` tables proved, keyed by the ENHANCEMENT id (one honest row per
    enhancement — uniqueness is structural, enforced by the primary key; a duplicate append is the
    explicit :class:`DuplicateEnhancementError` refusal, never an update). The ``payload`` carries
    the complete row-32 record composed ONCE at validation time by ``app/research/pnl_ledger.py``
    (the single writer): enhancement id + title, the baseline-vs-candidate net R AND net $ on
    train AND hold-out SEPARATELY (verbatim copies of the persisted row-31 backtest aggregates —
    never recomputed), n per split, full provenance (per-split source backtest report id +
    dataset id + checksum; strategy id, profile id, ``config_fingerprint``), and the timestamp.

    APPEND-ONLY at the repository level — the ``verdict_events`` standard: the repository exposes
    NO update and NO delete for ledger rows; the only way the ledger changes is appending a new
    row for a NEW enhancement. The routes, the markdown render, and the MCP ``pnl_ledger`` proxy
    all serve these stored rows VERBATIM (labels are presentation applied at read)."""

    enhancement_id: str
    payload: dict
    created_wall_ts: float


class DuplicateEnhancementError(Exception):
    """A ledger row for this enhancement id already exists — the append is REFUSED explicitly
    (one honest row per enhancement; uniqueness enforcement is not an update path)."""


class _StopSentinel:
    """Enqueued on close so the writer thread exits its loop cleanly."""


class JournalStore:
    """A journal-scoped SQLite store with a single background writer queue.

    Reads run on the caller's thread against a short-lived read connection (WAL lets readers proceed
    concurrently with the single writer). Writes are enqueued to ONE writer worker thread that owns
    the only write connection and wraps each write in ``BEGIN IMMEDIATE`` — so writes are serialized,
    never racing, and never executed on the feeder/WS path. A write enqueued from an observer
    callback returns immediately; the monitor surfaces a write failure as ``monitor_status: failed``
    rather than blocking or killing the feed.
    """

    def __init__(self, db_path: str, config: Config) -> None:
        self._db_path = db_path
        self._config = config
        # check_same_thread=False because the writer connection lives on the worker thread, not the
        # constructing thread; all writes still go through the ONE worker, so there is no real
        # cross-thread sharing of a connection mid-statement.
        self._write_conn = sqlite3.connect(db_path, check_same_thread=False)
        self._write_conn.row_factory = sqlite3.Row
        self._apply_pragmas(self._write_conn)
        self._create_schema()

        self._queue: "queue.Queue[tuple[Callable, queue.Queue] | _StopSentinel]" = queue.Queue()
        self._closed = False
        self._worker = threading.Thread(
            target=self._writer_loop, name=f"journal-writer:{db_path}", daemon=True
        )
        self._worker.start()

    # --- connection setup -----------------------------------------------------------------------
    def _apply_pragmas(self, conn: sqlite3.Connection) -> None:
        # WAL + busy_timeout are the capability-28 discipline. ``:memory:`` does not support WAL, so
        # apply it defensively (a memory store is only used in-process by a single test).
        if self._db_path != ":memory:":
            conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"PRAGMA busy_timeout={self._config.journal_busy_timeout_ms}")
        conn.execute("PRAGMA foreign_keys=ON")

    def _create_schema(self) -> None:
        # Ensure every table exists (idempotent — CREATE TABLE IF NOT EXISTS). On a brand-new DB this
        # also stamps the schema_version row at the CURRENT version, so a freshly-created store needs
        # no migration. On a PRE-EXISTING older DB the CREATE-IF-NOT-EXISTS no-ops (the tables already
        # exist with the old column set) and the stored version row is left untouched here — the
        # versioned migration below is what carries it up.
        with self._write_conn:
            self._write_conn.executescript(_SCHEMA)
            row = self._write_conn.execute(
                "SELECT version FROM schema_version LIMIT 1"
            ).fetchone()
            if row is None:
                self._write_conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (self._config.journal_schema_version,),
                )
        self._migrate()
        self._ensure_champion_pointer_seeded()

    def _ensure_champion_pointer_seeded(self) -> None:
        """Seed the champion pointer to the founding ``{v1, default}`` pair iff no row exists yet
        (J-07, era-3 capability 7) — runs UNCONDITIONALLY on every open, covering BOTH a
        brand-new store (the table arrives empty via ``_SCHEMA``; a fresh DB is already at the
        target version, so the version-gated v9->v10 migration step never runs) and a store
        migrated from a pre-v10 snapshot (that step creates the table empty). Idempotent — never
        overwrites an existing (possibly promoted) pointer. ``updated_wall_ts`` is left ``NULL``
        for the SEEDED row (it was never moved — a fabricated wall-clock instant for something
        that did not happen would violate the no-fabricated-data discipline); ``set_champion_pointer``
        stamps a real value only for an ACTUAL promotion move."""
        with self._write_conn:
            row = self._write_conn.execute(
                "SELECT 1 FROM champion_pointer WHERE id = 1"
            ).fetchone()
            if row is None:
                self._write_conn.execute(
                    "INSERT INTO champion_pointer (id, strategy_id, profile, updated_wall_ts) "
                    "VALUES (1, ?, ?, NULL)",
                    (STRATEGY_V1_ID, PROFILE_DEFAULT),
                )

    def _column_exists(self, table: str, column: str) -> bool:
        """True if ``column`` is present on ``table`` (drives the idempotent migration guards)."""
        cols = {r["name"] for r in self._write_conn.execute(f"PRAGMA table_info({table})").fetchall()}
        return column in cols

    def _migrate(self) -> None:
        """Carry an older journal DB up to ``Config.journal_schema_version`` (capability 28).

        Reads the stored ``schema_version`` and applies each pending step in order, INSIDE ONE
        ``BEGIN IMMEDIATE`` writer transaction per step (so a failure rolls back cleanly and the
        version row only advances once the columns exist). Every step is idempotent — a
        ``PRAGMA table_info`` guard makes "columns already present but a stale version row" a no-op
        rather than a crash (e.g. a DB whose tables were re-created at the new shape by a newer
        ``CREATE TABLE`` but whose version row was never bumped). NO step backfills existing rows: the
        verdict timeline is append-only, so a column added in a migration stays ``NULL`` on every row
        written before it (never fabricated, never recomputed).
        """
        target = self._config.journal_schema_version
        row = self._write_conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
        current = row["version"] if row is not None else target

        # --- v1 → v2: add the capability-24 dwell timing columns to verdict_events ---------------
        if current < 2:
            self._write_conn.execute("BEGIN IMMEDIATE")
            try:
                # ALTER TABLE ADD COLUMN is not itself idempotent (a re-add errors), so guard each
                # with table_info: a DB that already carries the columns (only the version row is
                # stale) skips straight to bumping the version — no crash.
                if not self._column_exists("verdict_events", "rule_first_true_ts"):
                    self._write_conn.execute(
                        "ALTER TABLE verdict_events ADD COLUMN rule_first_true_ts REAL"
                    )
                if not self._column_exists("verdict_events", "rule_first_true_price"):
                    self._write_conn.execute(
                        "ALTER TABLE verdict_events ADD COLUMN rule_first_true_price REAL"
                    )
                self._write_conn.execute("UPDATE schema_version SET version = 2")
                self._write_conn.commit()
            except Exception:
                self._write_conn.rollback()
                raise
            current = 2

        # --- v2 → v3: add the J-52 action-mark spread column to actions --------------------------
        if current < 3:
            self._write_conn.execute("BEGIN IMMEDIATE")
            try:
                # Idempotent guard (same discipline as v1 → v2): a DB that already carries the column
                # (only the version row is stale) skips straight to bumping the version. NO backfill —
                # any pre-existing action row keeps ``NULL`` spread_at_mark (a moment value is never
                # recomputed after the fact).
                if not self._column_exists("actions", "spread_at_mark"):
                    self._write_conn.execute(
                        "ALTER TABLE actions ADD COLUMN spread_at_mark REAL"
                    )
                self._write_conn.execute("UPDATE schema_version SET version = 3")
                self._write_conn.commit()
            except Exception:
                self._write_conn.rollback()
                raise
            current = 3

        # --- v3 → v4: add the J-49 entry risk-flags column to theses -----------------------------
        if current < 4:
            self._write_conn.execute("BEGIN IMMEDIATE")
            try:
                # Idempotent guard (same discipline as v1 → v2 → v3): a DB that already carries the
                # column (only the version row is stale) skips straight to bumping the version. NO
                # backfill — any pre-existing thesis row keeps ``NULL`` risk_flags (it was never
                # risk-assessed; its projection OMITS the key rather than read a dishonest empty list).
                if not self._column_exists("theses", "risk_flags"):
                    self._write_conn.execute(
                        "ALTER TABLE theses ADD COLUMN risk_flags TEXT"
                    )
                self._write_conn.execute("UPDATE schema_version SET version = 4")
                self._write_conn.commit()
            except Exception:
                self._write_conn.rollback()
                raise
            current = 4

        # --- v4 → v5: add the J-54 execution-checks column to theses -----------------------------
        if current < 5:
            self._write_conn.execute("BEGIN IMMEDIATE")
            try:
                # Idempotent guard (same discipline as v1 → v2 → v3 → v4): a DB that already carries
                # the column (only the version row is stale) skips straight to bumping the version. NO
                # backfill — any pre-existing RESOLVED thesis keeps ``NULL`` execution_checks (its
                # checks were never computed; the journal detail OMITS the key rather than fabricate a
                # pass/fail at read).
                if not self._column_exists("theses", "execution_checks"):
                    self._write_conn.execute(
                        "ALTER TABLE theses ADD COLUMN execution_checks TEXT"
                    )
                self._write_conn.execute("UPDATE schema_version SET version = 5")
                self._write_conn.commit()
            except Exception:
                self._write_conn.rollback()
                raise
            current = 5

        # --- v5 → v6: add the J-55/J-56/J-57 review-pillar columns to theses (ONE bump) -----------
        if current < 6:
            self._write_conn.execute("BEGIN IMMEDIATE")
            try:
                # Idempotent guard (same discipline as every prior step): a DB that already carries a
                # column (only the version row is stale) skips it and bumps the version. NO backfill —
                # any pre-existing RESOLVED thesis keeps ``NULL`` for the new columns (its final
                # statuses / grades were never computed and it was never reviewed; the journal detail
                # OMITS each key rather than fabricate a value at read). ``reviewed`` is added with a
                # ``DEFAULT 0`` so a pre-existing row reads back ``False`` (never reviewed) — that is
                # not a backfill of a computed value, it is the honest default for "no review exists".
                if not self._column_exists("theses", "statement_final_statuses"):
                    self._write_conn.execute(
                        "ALTER TABLE theses ADD COLUMN statement_final_statuses TEXT"
                    )
                if not self._column_exists("theses", "grades"):
                    self._write_conn.execute("ALTER TABLE theses ADD COLUMN grades TEXT")
                if not self._column_exists("theses", "review_tags"):
                    self._write_conn.execute("ALTER TABLE theses ADD COLUMN review_tags TEXT")
                if not self._column_exists("theses", "review_note"):
                    self._write_conn.execute("ALTER TABLE theses ADD COLUMN review_note TEXT")
                if not self._column_exists("theses", "reviewed"):
                    self._write_conn.execute(
                        "ALTER TABLE theses ADD COLUMN reviewed INTEGER NOT NULL DEFAULT 0"
                    )
                self._write_conn.execute("UPDATE schema_version SET version = 6")
                self._write_conn.commit()
            except Exception:
                self._write_conn.rollback()
                raise
            current = 6

        # --- v6 → v7: add the J-58 excursion-record column to theses (ONE additive column) --------
        if current < 7:
            self._write_conn.execute("BEGIN IMMEDIATE")
            try:
                # Idempotent guard (same discipline as every prior step): a DB that already carries the
                # column (only the version row is stale) skips it and bumps the version. NO backfill —
                # any pre-existing RESOLVED thesis keeps ``NULL`` excursions (its excursions were never
                # measured; the journal detail OMITS the key rather than fabricate numbers at read).
                if not self._column_exists("theses", "excursions"):
                    self._write_conn.execute(
                        "ALTER TABLE theses ADD COLUMN excursions TEXT"
                    )
                self._write_conn.execute("UPDATE schema_version SET version = 7")
                self._write_conn.commit()
            except Exception:
                self._write_conn.rollback()
                raise
            current = 7

        # --- v7 -> v8: create the J-03 backtests table (era-3 capability 4) -----------------------
        if current < 8:
            self._write_conn.execute("BEGIN IMMEDIATE")
            try:
                # A NEW payload-blob table (the ``studies`` shape) — ``CREATE TABLE IF NOT EXISTS``
                # is idempotent by construction, so a DB that already carries the table (only the
                # version row is stale — e.g. the fresh-schema executescript above just created it)
                # skips straight to bumping the version. The table arrives EMPTY and NO existing
                # table or row is touched: a migration never fabricates a backtest report.
                self._write_conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS backtests (
                        id                  TEXT PRIMARY KEY,
                        payload             TEXT NOT NULL,
                        created_wall_ts     REAL NOT NULL
                    )
                    """
                )
                self._write_conn.execute("UPDATE schema_version SET version = 8")
                self._write_conn.commit()
            except Exception:
                self._write_conn.rollback()
                raise
            current = 8

        # --- v8 -> v9: create the J-04 pnl_ledger table (era-3 capability 5, row 32) --------------
        if current < 9:
            self._write_conn.execute("BEGIN IMMEDIATE")
            try:
                # A NEW payload-blob table keyed by the ENHANCEMENT id (one honest row per
                # enhancement — uniqueness is structural). ``CREATE TABLE IF NOT EXISTS`` is
                # idempotent by construction, so a DB that already carries the table (only the
                # version row is stale) skips straight to bumping the version. The table arrives
                # EMPTY and NO existing table or row is touched: a migration never fabricates a
                # PnL-ledger row (the founding row is appended ONLY by the explicit seeding CLI).
                self._write_conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pnl_ledger (
                        enhancement_id      TEXT PRIMARY KEY,
                        payload             TEXT NOT NULL,
                        created_wall_ts     REAL NOT NULL
                    )
                    """
                )
                self._write_conn.execute("UPDATE schema_version SET version = 9")
                self._write_conn.commit()
            except Exception:
                self._write_conn.rollback()
                raise
            current = 9

        # --- v9 -> v10: create the J-07 champion_pointer table (era-3 capability 7, row 33) --------
        if current < 10:
            self._write_conn.execute("BEGIN IMMEDIATE")
            try:
                # A NEW singleton-row table — the ONE persisted, movable champion pointer that
                # replaces the retired hardcoded ``{STRATEGY_V1_ID, PROFILE_DEFAULT}`` constant in
                # ``app/research/profiles.py``. ``CREATE TABLE IF NOT EXISTS`` is idempotent by
                # construction, so a DB that already carries the table (only the version row is
                # stale) skips straight to bumping the version. The table arrives EMPTY here — the
                # founding seed (below, ``_ensure_champion_pointer_seeded``) runs UNCONDITIONALLY
                # after migration on every open (fresh-create included, where a fresh DB is already
                # at the target version and this block never runs at all), so seeding is NOT done
                # inside this version-gated step: a DB migrated straight from an old snapshot must
                # seed too, exactly once, regardless of which path created the table.
                self._write_conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS champion_pointer (
                        id                  INTEGER PRIMARY KEY,
                        strategy_id         TEXT NOT NULL,
                        profile             TEXT NOT NULL,
                        updated_wall_ts     REAL
                    )
                    """
                )
                self._write_conn.execute("UPDATE schema_version SET version = 10")
                self._write_conn.commit()
            except Exception:
                self._write_conn.rollback()
                raise
            current = 10

        # Future steps (current < 11, …) append here, each in its own BEGIN IMMEDIATE block.

    def _read_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        self._apply_pragmas(conn)
        return conn

    # --- writer queue ---------------------------------------------------------------------------
    def _writer_loop(self) -> None:
        while True:
            item = self._queue.get()
            if isinstance(item, _StopSentinel):
                return
            fn, result_q = item
            try:
                # BEGIN IMMEDIATE: take the write lock up front so two queued writes never deadlock
                # mid-transaction; the single worker makes contention impossible anyway, but the
                # mandated discipline is explicit.
                self._write_conn.execute("BEGIN IMMEDIATE")
                value = fn(self._write_conn)
                self._write_conn.commit()
                result_q.put((True, value))
            except Exception as exc:  # surfaced to the enqueuing caller (never swallowed)
                self._write_conn.rollback()
                result_q.put((False, exc))

    def _do_write(self, fn: Callable[[sqlite3.Connection], Any]) -> Any:
        """Enqueue ``fn`` onto the single writer worker and wait for its result.

        Raises if ``fn`` raised on the worker (so the monitor can mark ``monitor_status: failed``)
        or if the store is closed. The wait is the only blocking part — but it blocks the CALLING
        thread (the monitor's observer callback runs on the feeder thread, so see the note in
        monitor.py for why the monitor enqueues without awaiting a result on the hot path)."""
        if self._closed:
            raise RuntimeError("journal store is closed")
        result_q: "queue.Queue" = queue.Queue(maxsize=1)
        self._queue.put((fn, result_q))
        ok, payload = result_q.get()
        if not ok:
            raise payload
        return payload

    # --- backtests (era-3 capability 4, J-03) — payload-blob writes to the backtests table ---------
    def insert_backtest(self, record: BacktestRecord) -> None:
        """Persist a NEW backtest row at CREATION (J-03): the queued payload with its identity
        stamps (dataset/strategy/profile echo, the recorded null-baseline seed, the config
        fingerprint). The write goes through the single writer queue (``BEGIN IMMEDIATE``), never
        from event processing or the WS serialization path."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                "INSERT INTO backtests (id, payload, created_wall_ts) VALUES (?,?,?)",
                (record.id, json.dumps(record.payload), record.created_wall_ts),
            )

        self._do_write(_fn)

    def update_backtest_payload(self, backtest_id: str, payload: dict) -> None:
        """Replace a backtest's served payload (J-03). Used for the running-status flip and the
        throttled progress heartbeat — cheap, infrequent status writes, NOT a hot path. The FINAL
        result lands ONCE via :meth:`set_backtest_result`."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE backtests SET payload=? WHERE id=?",
                (json.dumps(payload), backtest_id),
            )

        self._do_write(_fn)

    def set_backtest_result(self, backtest_id: str, payload: dict) -> None:
        """Persist a backtest's FINAL payload ONCE at its defining moment (J-03, Data Contract
        row 31): the terminal status plus — for ``done`` — the complete deterministic ``result``
        block computed once by the runner. One ``BEGIN IMMEDIATE`` writer transaction; the routes
        and the MCP proxy serve this stored row VERBATIM ever after (no recomputation on read)."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE backtests SET payload=? WHERE id=?",
                (json.dumps(payload), backtest_id),
            )

        self._do_write(_fn)

    def get_backtest(self, backtest_id: str) -> BacktestRecord | None:
        """One backtest read back as an immutable record (the served projection is its payload)."""
        conn = self._read_conn()
        try:
            row = conn.execute(
                "SELECT * FROM backtests WHERE id=?", (backtest_id,)
            ).fetchone()
            if row is None:
                return None
            return BacktestRecord(
                id=row["id"],
                payload=json.loads(row["payload"]),
                created_wall_ts=row["created_wall_ts"],
            )
        finally:
            conn.close()

    def list_backtests(self, *, limit: int) -> list[BacktestRecord]:
        """Backtests most-recent-first, capped at ``limit`` (the serving-only
        ``backtest_list_max``). Read VERBATIM — the list route renders each record's payload
        directly (never recomputed)."""
        conn = self._read_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM backtests ORDER BY created_wall_ts DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                BacktestRecord(
                    id=r["id"],
                    payload=json.loads(r["payload"]),
                    created_wall_ts=r["created_wall_ts"],
                )
                for r in rows
            ]
        finally:
            conn.close()

    # --- the PnL ledger (era-3 capability 5, J-04, row 32) — APPEND-ONLY, the verdict_events standard
    def append_pnl_ledger_row(self, record: PnlLedgerRecord) -> None:
        """Append ONE PnL-ledger row (J-04). There is deliberately NO update/delete counterpart —
        the ledger is append-only at the repository level (the ``verdict_events`` standard,
        capability 28 / journal-integrity): the only way the product's honesty record changes is
        appending a new row for a NEW enhancement. A row whose enhancement id already exists is
        the explicit :class:`DuplicateEnhancementError` refusal (one honest row per enhancement —
        the primary key makes uniqueness structural; nothing is overwritten, nothing mutates).
        The write goes through the single writer queue (``BEGIN IMMEDIATE``), never from event
        processing or the WS serialization path."""

        def _fn(conn: sqlite3.Connection) -> None:
            try:
                conn.execute(
                    "INSERT INTO pnl_ledger (enhancement_id, payload, created_wall_ts) VALUES (?,?,?)",
                    (record.enhancement_id, json.dumps(record.payload), record.created_wall_ts),
                )
            except sqlite3.IntegrityError as exc:
                raise DuplicateEnhancementError(
                    f"a PnL-ledger row for enhancement '{record.enhancement_id}' already exists — "
                    f"the ledger is append-only (one honest row per enhancement), so the append is "
                    f"refused"
                ) from exc

        self._do_write(_fn)

    def get_pnl_ledger_row(self, enhancement_id: str) -> PnlLedgerRecord | None:
        """One ledger row read back as an immutable record (the served projection is its payload)."""
        conn = self._read_conn()
        try:
            row = conn.execute(
                "SELECT * FROM pnl_ledger WHERE enhancement_id=?", (enhancement_id,)
            ).fetchone()
            if row is None:
                return None
            return PnlLedgerRecord(
                enhancement_id=row["enhancement_id"],
                payload=json.loads(row["payload"]),
                created_wall_ts=row["created_wall_ts"],
            )
        finally:
            conn.close()

    def list_pnl_ledger(self) -> list[PnlLedgerRecord]:
        """Every ledger row in INSERTION order (rowid ascending — the honest chronology of an
        append-only table that structurally has no delete: the record reads oldest-first, one row
        per enhancement, exactly as appended). Read VERBATIM — the route, the markdown render, and
        the MCP proxy all consume THIS one read (never recomputed, never a second query path).
        No serving cap: the ledger grows one row per validated enhancement (a human-scale count),
        and the honesty record is only honest when served whole."""
        conn = self._read_conn()
        try:
            rows = conn.execute("SELECT * FROM pnl_ledger ORDER BY rowid ASC").fetchall()
            return [
                PnlLedgerRecord(
                    enhancement_id=r["enhancement_id"],
                    payload=json.loads(r["payload"]),
                    created_wall_ts=r["created_wall_ts"],
                )
                for r in rows
            ]
        finally:
            conn.close()

    # --- the champion pointer (era-3 capability 7, J-07, row 33) — the ONE persisted, movable ------
    # source ``profiles_projection`` reads. Seeded to the founding ``{v1, default}`` pair at
    # store-open (``_ensure_champion_pointer_seeded``); ``set_champion_pointer`` is the ONE mutation
    # path, called ONLY by ``app/research/pnl_scan.py`` (source-scan-guard-enforced) on a genuine
    # hold-out survivor. Unlike the append-only ``pnl_ledger`` / ``verdict_events`` tables, this row
    # is INTENTIONALLY mutable (there is exactly one pointer, and promotion moves it) — the SAME
    # single-writer-queue discipline still applies (``BEGIN IMMEDIATE``, never off the hot path).
    def get_champion_pointer(self) -> dict:
        """The single persisted champion pointer — ``{"strategy_id", "profile"}`` — never absent
        (seeded at store-open). Every surface (``GET /research/profiles``, hence ``/performance``
        and MCP) reads THIS verbatim; no surface may infer the champion from ledger provenance or
        carry a second copy."""
        conn = self._read_conn()
        try:
            row = conn.execute(
                "SELECT strategy_id, profile FROM champion_pointer WHERE id = 1"
            ).fetchone()
            if row is None:
                # An internal invariant violation (seeding runs at every store-open), not a normal
                # empty state — surfaced explicitly rather than silently substituting a default.
                raise RuntimeError(
                    "champion pointer row missing — the store failed to seed it at open"
                )
            return {"strategy_id": row["strategy_id"], "profile": row["profile"]}
        finally:
            conn.close()

    def set_champion_pointer(self, *, strategy_id: str, profile: str, wall_ts: float) -> None:
        """Move the persisted champion pointer (J-07's ONE mutation path). Goes through the single
        writer queue (``BEGIN IMMEDIATE``), the SAME discipline as every other write. ``wall_ts`` is
        supplied by the CALLER (the sweep's own persist-once moment) — this method never reads the
        wall clock itself, matching every other store write."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                "INSERT OR REPLACE INTO champion_pointer (id, strategy_id, profile, updated_wall_ts) "
                "VALUES (1, ?, ?, ?)",
                (strategy_id, profile, wall_ts),
            )

        self._do_write(_fn)

    def schema_version(self) -> int | None:
        conn = self._read_conn()
        try:
            row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
            return row["version"] if row is not None else None
        finally:
            conn.close()

    def journal_mode(self) -> str:
        """The active SQLite journal_mode (``wal`` for a file store) — used by the discipline test."""
        conn = self._read_conn()
        try:
            return conn.execute("PRAGMA journal_mode").fetchone()[0]
        finally:
            conn.close()

    # --- lifecycle ------------------------------------------------------------------------------
    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._queue.put(_StopSentinel())
        self._worker.join(timeout=5.0)
        self._write_conn.close()
