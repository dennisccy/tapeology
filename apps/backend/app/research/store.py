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
"""

from __future__ import annotations

import json
import queue
import sqlite3
import threading
from dataclasses import dataclass
from typing import Any, Callable

from ..config import Config

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
"""


@dataclass(frozen=True)
class ThesisRecord:
    """One persisted thesis row (read back as an immutable record).

    ``risk_flags`` (capability 26, J-49) is the frozen entry risk-flag set computed ONCE at
    declaration and stored verbatim — a list of ``{flag, label, evidence, measured}`` entries, or an
    empty list when assessed-but-nothing-fired. It is ``None`` ONLY for a pre-v4 thesis that was never
    risk-assessed (NULL in the DB, never backfilled): the projection then OMITS the ``risk_flags`` key
    entirely rather than read a dishonest empty list. Defaulted ``None`` so every existing call site /
    fixture stays valid (additive) and so the two honest-omission states (ABSENT vs EMPTY) never
    collapse."""

    id: str
    ticker: str
    setup_type: str
    direction: str
    invalidation_price: float
    level_price: float | None
    status: str
    bound_source: str
    data_feed: str
    config_fingerprint: str
    entry_context: dict
    statements: list[dict]
    created_logical_ts: float
    created_wall_ts: float
    risk_flags: list[dict] | None = None
    # ``execution_checks`` (capability 27, J-54) is the machine-derived execution-check result —
    # ``{"checks": [...], "suggested_mistake_tags": [...]}`` — computed ONCE at terminal resolution
    # from the recorded marks + the append-only timeline + the frozen thesis fields, and stored
    # verbatim. It is ``None`` until a thesis is resolved with the checks computed (a pre-v5 resolved
    # thesis stays ``None`` — NULL in the DB, never backfilled): the journal detail then OMITS the
    # ``execution_checks`` key entirely rather than fabricate a pass/fail at read. Defaulted ``None``
    # so every existing call site / fixture stays valid (additive) and the two honest-omission states
    # (ABSENT vs computed) never collapse.
    execution_checks: dict | None = None
    # --- v6 review-pillar fields (J-55 / J-56 / J-57), all persisted ONCE at their defining moment --
    # ``statement_final_statuses`` (J-55) is the list of per-statement FINAL statuses recorded ONCE at
    # terminal resolution — one ``{status}`` entry per frozen statement, in statement order (the
    # status is the monitor's last live evaluation at the terminal moment, or an explicit
    # ``not_evaluated`` enum where no live context exists — e.g. the restart-expiry sweep). It is
    # ``None`` until recorded (a pre-v6 resolution stays ``None`` — NULL in the DB, never backfilled):
    # the journal detail then renders the frozen statements WITHOUT a final-status badge (honest
    # omission). The frozen ``statements`` JSON itself is NEVER mutated — this is an additive parallel.
    statement_final_statuses: list[dict] | None = None
    # ``grades`` (J-56) is the outcome × process grade — ``{"outcome", "process", "process_evidence"}``
    # — computed ONCE at terminal resolution from the persisted execution checks + the frozen risk
    # flags + the resolution, and stored verbatim. ``None`` until computed (a pre-v6 resolution stays
    # ``None``): the journal detail/list then OMIT the grade keys (honest omission). ENUM labels only,
    # never a numeric score.
    grades: dict | None = None
    # ``review_tags`` / ``review_note`` / ``reviewed`` (J-57) are the user-CONFIRMED review, recorded
    # ONCE by ``POST …/review``. ``reviewed`` is ``False`` until the user saves a review; ``review_tags``
    # is the list of confirmed mistake-tag ids (distinct from the machine-SUGGESTED tags on
    # ``execution_checks``) and ``review_note`` the optional free text (required only for ``other``).
    review_tags: list[str] | None = None
    review_note: str | None = None
    reviewed: bool = False
    # ``excursions`` (capability 30, J-58) is the per-horizon excursion record —
    # ``{"tracked": bool, "populations": {confirmation?: {...}, entry?: {...}}}`` — measured ONCE at
    # the terminal resolution / stream-end (the proven persist-once seam) from the in-memory price
    # path and stored verbatim. The two populations (confirmation-anchored / entry-anchored) are
    # segregated and never pooled. It is ``None`` until measured (a pre-v7 resolution stays ``None`` —
    # NULL in the DB, never backfilled): the journal detail then OMITS the ``excursions`` key entirely
    # rather than fabricate numbers at read. A ``{"tracked": False}`` record is the explicit honest
    # marker persisted where no tracker existed at the persist moment (the restart-expiry sweep).
    # Defaulted ``None`` so every existing call site / fixture stays valid (additive) and the
    # honest-omission states (ABSENT vs measured vs not-tracked) never collapse.
    excursions: dict | None = None


@dataclass(frozen=True)
class ActionRecord:
    """One persisted action mark (entry | exit) — recorded verbatim from the user (no inferred fill).

    ``price`` is recorded EXACTLY as the user submitted it (never an inferred/simulated fill);
    ``spread_at_mark`` is the snapshot's spread taken ONCE at recording (a moment value — ``None``
    when there was no quote — never recomputable later). The entry-mark UI is J-52; this record's
    ``spread_at_mark`` column arrives with the v2 → v3 migration. ``spread_at_mark`` is defaulted so
    every existing call site / fixture stays valid (additive) and a pre-v3 row reads ``None``."""

    id: str
    thesis_id: str
    kind: str
    price: float
    logical_ts: float
    wall_ts: float
    spread_at_mark: float | None = None


@dataclass(frozen=True)
class VerdictEventRecord:
    thesis_id: str
    logical_ts: float
    wall_ts: float
    verdict: str
    evidence: str
    tape_state: str | None
    confidence: float | None
    last: float | None
    # The verdict-transition timing record (capability 24): the first logical instant + price at which
    # the RAW rule began holding, distinct from ``logical_ts`` (the publication instant, after dwell).
    # Defaulted ``None`` so every existing call site / fixture stays valid (additive) and so the
    # initial ``pending`` / lifecycle rows (no raw rule) record no spurious timing.
    rule_first_true_ts: float | None = None
    rule_first_true_price: float | None = None


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

        # Future steps (current < 8, …) append here, each in its own BEGIN IMMEDIATE block.

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

    # --- writes (theses + verdict_events only this iteration) ------------------------------------
    @staticmethod
    def _encode_risk_flags(risk_flags: list[dict] | None) -> str | None:
        """Serialize the frozen risk-flag list to JSON, preserving the ABSENT/EMPTY distinction.

        ``None`` (never assessed) is stored as SQL ``NULL`` so the projection can OMIT the key; an
        empty list (assessed, nothing fired) is stored as ``"[]"`` so it reads back as an explicit
        empty list. The two honest-omission states never collapse."""
        return None if risk_flags is None else json.dumps(risk_flags)

    @staticmethod
    def _encode_execution_checks(execution_checks: dict | None) -> str | None:
        """Serialize the execution-check result to JSON, preserving the ABSENT/computed distinction.

        ``None`` (never computed — a pre-v5 resolution, or a thesis not yet resolved) is stored as SQL
        ``NULL`` so the journal detail can OMIT the key; a computed dict is stored as JSON so it reads
        back verbatim. The two honest-omission states never collapse (absent ≠ a computed-but-empty
        result)."""
        return None if execution_checks is None else json.dumps(execution_checks)

    @staticmethod
    def _encode_json_or_none(value: object | None) -> str | None:
        """Serialize a JSON-able value to a string, preserving the ABSENT (NULL) state.

        Used for the v6 ``statement_final_statuses`` / ``grades`` / ``review_tags`` columns — ``None``
        (never recorded/computed) stays SQL ``NULL`` so the journal surfaces OMIT the key; a value
        (incl. an empty list) is stored as JSON so it reads back verbatim. The ABSENT vs
        recorded-but-empty states never collapse (the established honest-omission discipline)."""
        return None if value is None else json.dumps(value)

    def insert_thesis(self, record: ThesisRecord) -> None:
        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                INSERT INTO theses (
                    id, ticker, setup_type, direction, invalidation_price, level_price,
                    status, bound_source, data_feed, config_fingerprint,
                    entry_context, statements, created_logical_ts, created_wall_ts, risk_flags,
                    execution_checks, statement_final_statuses, grades, review_tags, review_note,
                    reviewed, excursions
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    record.id,
                    record.ticker,
                    record.setup_type,
                    record.direction,
                    record.invalidation_price,
                    record.level_price,
                    record.status,
                    record.bound_source,
                    record.data_feed,
                    record.config_fingerprint,
                    json.dumps(record.entry_context),
                    json.dumps(record.statements),
                    record.created_logical_ts,
                    record.created_wall_ts,
                    self._encode_risk_flags(record.risk_flags),
                    self._encode_execution_checks(record.execution_checks),
                    self._encode_json_or_none(record.statement_final_statuses),
                    self._encode_json_or_none(record.grades),
                    self._encode_json_or_none(record.review_tags),
                    record.review_note,
                    1 if record.reviewed else 0,
                    self._encode_json_or_none(record.excursions),
                ),
            )

        self._do_write(_fn)

    def insert_thesis_with_event(
        self, thesis: ThesisRecord, event: VerdictEventRecord
    ) -> None:
        """Declare a thesis ATOMICALLY: the thesis row + its initial verdict event in ONE writer
        transaction (single ``BEGIN IMMEDIATE`` … commit, owned by the writer worker).

        A failure at any point rolls BOTH back — so a thesis row without its initial timeline event
        can no longer exist (the iter-4 two-transaction defect). This is the only declaration path the
        route uses; the standalone ``insert_thesis`` / ``append_verdict_event`` remain for the
        lifecycle/test paths that legitimately write one row at a time. The append-only guarantee is
        preserved (this only INSERTs; it never updates/deletes a verdict row)."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                INSERT INTO theses (
                    id, ticker, setup_type, direction, invalidation_price, level_price,
                    status, bound_source, data_feed, config_fingerprint,
                    entry_context, statements, created_logical_ts, created_wall_ts, risk_flags,
                    execution_checks, statement_final_statuses, grades, review_tags, review_note,
                    reviewed, excursions
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    thesis.id,
                    thesis.ticker,
                    thesis.setup_type,
                    thesis.direction,
                    thesis.invalidation_price,
                    thesis.level_price,
                    thesis.status,
                    thesis.bound_source,
                    thesis.data_feed,
                    thesis.config_fingerprint,
                    json.dumps(thesis.entry_context),
                    json.dumps(thesis.statements),
                    thesis.created_logical_ts,
                    thesis.created_wall_ts,
                    self._encode_risk_flags(thesis.risk_flags),
                    self._encode_execution_checks(thesis.execution_checks),
                    self._encode_json_or_none(thesis.statement_final_statuses),
                    self._encode_json_or_none(thesis.grades),
                    self._encode_json_or_none(thesis.review_tags),
                    thesis.review_note,
                    1 if thesis.reviewed else 0,
                    self._encode_json_or_none(thesis.excursions),
                ),
            )
            conn.execute(
                """
                INSERT INTO verdict_events (
                    thesis_id, logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last,
                    rule_first_true_ts, rule_first_true_price
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    event.thesis_id,
                    event.logical_ts,
                    event.wall_ts,
                    event.verdict,
                    event.evidence,
                    event.tape_state,
                    event.confidence,
                    event.last,
                    event.rule_first_true_ts,
                    event.rule_first_true_price,
                ),
            )

        self._do_write(_fn)

    def append_verdict_event(self, record: VerdictEventRecord) -> None:
        """Append ONE verdict event. There is deliberately NO update/delete counterpart — the
        timeline is append-only at the repository level (capability 28 / journal-integrity).

        A config-owned capacity CAP (``verdict_timeline_cap``) bounds an unbounded live watch: once a
        thesis exceeds the cap, the OLDEST surviving rows are pruned. This is capacity management, NOT
        an edit of a retained row — the surviving rows are never rewritten, so the append-only
        guarantee (no update/delete method exists) holds: there is no way to change what a kept row
        says. A pruned row is gone, never altered."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                INSERT INTO verdict_events (
                    thesis_id, logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last,
                    rule_first_true_ts, rule_first_true_price
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    record.thesis_id,
                    record.logical_ts,
                    record.wall_ts,
                    record.verdict,
                    record.evidence,
                    record.tape_state,
                    record.confidence,
                    record.last,
                    record.rule_first_true_ts,
                    record.rule_first_true_price,
                ),
            )
            self._prune_timeline(conn, record.thesis_id)

        self._do_write(_fn)

    def _prune_timeline(self, conn: sqlite3.Connection, thesis_id: str) -> None:
        """Enforce the config-owned per-thesis timeline cap by deleting the OLDEST rows over the cap.

        Runs INSIDE the same writer-queue transaction as the append (so the cap is maintained
        atomically off any hot path). Deletes only the oldest excess rows (by ascending ``id`` =
        insertion order); the kept rows are untouched. Capacity bound only — distinct from any
        update/delete of a RETAINED row, which the repository deliberately does not expose."""
        cap = self._config.verdict_timeline_cap
        count = conn.execute(
            "SELECT COUNT(*) FROM verdict_events WHERE thesis_id=?", (thesis_id,)
        ).fetchone()[0]
        if count <= cap:
            return
        conn.execute(
            """
            DELETE FROM verdict_events
            WHERE id IN (
                SELECT id FROM verdict_events WHERE thesis_id=? ORDER BY id ASC LIMIT ?
            )
            """,
            (thesis_id, count - cap),
        )

    def resolve_thesis(self, thesis_id: str, status: str) -> None:
        """Set a thesis's terminal status (played_out | abandoned | invalidated | expired).

        This updates the THESES row only — it is NOT an edit of any verdict_events row (those stay
        append-only); the resolution's timeline entry is a separately APPENDED verdict event. Used
        by the lifecycle-honesty path (expired-on-stop) and the startup sweep."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE theses SET status=? WHERE id=?",
                (status, thesis_id),
            )

        self._do_write(_fn)

    def set_execution_checks(self, thesis_id: str, execution_checks: dict) -> None:
        """Persist the machine-derived execution-check result on a thesis row ONCE at terminal
        resolution (capability 27, J-54).

        This updates the THESES row's ``execution_checks`` column only — it is NOT an edit of any
        ``verdict_events`` row (the append-only timeline is untouched; no update/delete is added).
        Called by every terminal-resolution path (user resolve, system invalidation, stream-end /
        stop expiry, and the restart-expiry sweep) right after the resolution, so the checks are
        computed and stored exactly ONCE at the defining moment — never recomputed at read. The write
        goes through the single writer queue (``BEGIN IMMEDIATE``), never from event processing or the
        WS serialization path."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE theses SET execution_checks=? WHERE id=?",
                (self._encode_execution_checks(execution_checks), thesis_id),
            )

        self._do_write(_fn)

    def set_statement_final_statuses(
        self, thesis_id: str, statement_final_statuses: list[dict]
    ) -> None:
        """Persist the per-statement FINAL statuses on a thesis row ONCE at terminal resolution (J-55).

        Updates the THESES row's ``statement_final_statuses`` column only — the frozen ``statements``
        JSON is NEVER mutated (this is an additive parallel column) and no ``verdict_events`` row is
        touched (the append-only timeline is untouched). Called by every terminal-resolution path
        right after the resolution, so the statuses are recorded exactly ONCE at the defining moment —
        never recomputed at read. The write goes through the single writer queue (``BEGIN IMMEDIATE``),
        never from event processing or the WS serialization path."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE theses SET statement_final_statuses=? WHERE id=?",
                (self._encode_json_or_none(statement_final_statuses), thesis_id),
            )

        self._do_write(_fn)

    def set_grades(self, thesis_id: str, grades: dict) -> None:
        """Persist the outcome × process grades on a thesis row ONCE at terminal resolution (J-56).

        Updates the THESES row's ``grades`` column only — no ``verdict_events`` row is touched (the
        append-only timeline is untouched; no update/delete is added). Called by every
        terminal-resolution path right after the execution checks are persisted (the process rule
        weighs those checks), so the grades are computed and stored exactly ONCE at the defining
        moment — never recomputed at read. The write goes through the single writer queue
        (``BEGIN IMMEDIATE``), never from event processing or the WS serialization path."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE theses SET grades=? WHERE id=?",
                (self._encode_json_or_none(grades), thesis_id),
            )

        self._do_write(_fn)

    def set_excursions(self, thesis_id: str, excursions: dict) -> None:
        """Persist the per-horizon excursion record on a thesis row ONCE at its defining moment (J-58).

        Updates the THESES row's ``excursions`` column only — no ``verdict_events`` row is touched (the
        append-only timeline is untouched; no update/delete is added) and NO tape data is persisted
        (the excursion record holds only R-unit summaries + anchors, never trades/quotes/candles).
        Called by every terminal-resolution path (user resolve, system invalidation, stream-end / stop
        expiry, restart-expiry sweep) AND the stream-end survival path for a surviving entry-marked
        thesis, right at the defining moment — so the excursions are measured and stored exactly ONCE,
        never recomputed at read. The write goes through the single writer queue (``BEGIN IMMEDIATE``),
        never from event processing or the WS serialization path."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE theses SET excursions=? WHERE id=?",
                (self._encode_json_or_none(excursions), thesis_id),
            )

        self._do_write(_fn)

    def save_review(
        self, thesis_id: str, *, tags: list[str], note: str | None
    ) -> None:
        """Persist the user-CONFIRMED review and flip the thesis to ``reviewed`` ONCE (J-57).

        Records the confirmed mistake tags + the optional note VERBATIM and sets ``reviewed=1`` in a
        single writer transaction. This touches the THESES row only — the append-only ``verdict_events``
        write surface is UNTOUCHED (journal integrity: a review never edits the timeline). The route
        enforces the validation matrix (resolved-only, unknown-tag/other-note 422, already-reviewed
        409) BEFORE calling this — so this is the persist step of a validated review only."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE theses SET review_tags=?, review_note=?, reviewed=1 WHERE id=?",
                (self._encode_json_or_none(tags), note, thesis_id),
            )

        self._do_write(_fn)

    def resolve_thesis_with_event(
        self, thesis_id: str, status: str, event: VerdictEventRecord
    ) -> None:
        """Resolve a thesis ATOMICALLY: flip the theses-row status AND append ONE final timeline
        event in a single ``BEGIN IMMEDIATE`` writer transaction (the user-resolution path, J-50).

        This is the single function the resolve route funnels through (so a later iteration can add
        grading/execution-check computation "once here" — data-contract row 19 — without a second
        path). The status flip touches ONLY the theses row; the resolution is recorded as an APPENDED
        verdict event (never an edit of a prior row — journal-integrity append-only guarantee). A
        failure rolls BOTH back, so a status flip without its timeline event (or vice versa) can never
        be left behind."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                "UPDATE theses SET status=? WHERE id=?",
                (status, thesis_id),
            )
            conn.execute(
                """
                INSERT INTO verdict_events (
                    thesis_id, logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last,
                    rule_first_true_ts, rule_first_true_price
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    event.thesis_id,
                    event.logical_ts,
                    event.wall_ts,
                    event.verdict,
                    event.evidence,
                    event.tape_state,
                    event.confidence,
                    event.last,
                    event.rule_first_true_ts,
                    event.rule_first_true_price,
                ),
            )
            self._prune_timeline(conn, thesis_id)

        self._do_write(_fn)

    def insert_action(self, record: ActionRecord) -> None:
        """Persist one action mark (entry | exit) VERBATIM (J-52). ``price`` is stored exactly as the
        user submitted it (never an inferred/simulated fill); ``spread_at_mark`` is the moment spread
        recorded once at marking. The write goes through the single writer queue (``BEGIN IMMEDIATE``),
        never from event processing or the WS serialization path."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                INSERT INTO actions (id, thesis_id, kind, price, logical_ts, wall_ts, spread_at_mark)
                VALUES (?,?,?,?,?,?,?)
                """,
                (
                    record.id,
                    record.thesis_id,
                    record.kind,
                    record.price,
                    record.logical_ts,
                    record.wall_ts,
                    record.spread_at_mark,
                ),
            )

        self._do_write(_fn)

    def expire_stale_actives(self, wall_ts: float) -> list[str]:
        """Startup sweep (J-47 / J-51 leg): resolve each UNMARKED thesis still ``active`` to
        ``expired`` and append a final ``expired`` timeline event — but EXEMPT an entry-marked
        active thesis: a real position is never orphaned, so it SURVIVES a backend restart as
        active-but-not-evaluated (its ``active`` row is left untouched; NO expiry event is appended).
        Returns the ids actually expired (the unmarked ones only).

        Entry-mark presence is queried in-transaction (``actions WHERE kind='entry'``) so the sweep
        is consistent with the persisted marks. Done as ONE queued write so the sweep is atomic and
        runs off any hot path; the surviving entry-marked thesis is re-attached only when its
        matching source is watched again (a fresh monitor adopts it with a ``watch_restarted`` gap
        event)."""

        def _fn(conn: sqlite3.Connection) -> list[str]:
            rows = conn.execute(
                "SELECT id FROM theses WHERE status = 'active'"
            ).fetchall()
            expired: list[str] = []
            for r in rows:
                tid = r["id"]
                # EXEMPT an entry-marked active thesis — a real position is never orphaned (J-47).
                marked = conn.execute(
                    "SELECT 1 FROM actions WHERE thesis_id=? AND kind='entry' LIMIT 1",
                    (tid,),
                ).fetchone()
                if marked is not None:
                    continue
                conn.execute("UPDATE theses SET status='expired' WHERE id=?", (tid,))
                conn.execute(
                    """
                    INSERT INTO verdict_events (
                        thesis_id, logical_ts, wall_ts, verdict, evidence,
                        tape_state, confidence, last
                    ) VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (
                        tid,
                        0.0,
                        wall_ts,
                        "expired",
                        "Thesis expired on restart — the watch that declared it is no longer running.",
                        None,
                        None,
                        None,
                    ),
                )
                expired.append(tid)
            return expired

        return self._do_write(_fn)

    # --- reads ----------------------------------------------------------------------------------
    def get_thesis(self, thesis_id: str) -> ThesisRecord | None:
        conn = self._read_conn()
        try:
            row = conn.execute(
                "SELECT * FROM theses WHERE id=?", (thesis_id,)
            ).fetchone()
            return self._row_to_thesis(row) if row is not None else None
        finally:
            conn.close()

    def get_active_thesis(self, ticker: str) -> ThesisRecord | None:
        conn = self._read_conn()
        try:
            row = conn.execute(
                "SELECT * FROM theses WHERE ticker=? AND status='active' "
                "ORDER BY created_wall_ts DESC LIMIT 1",
                (ticker,),
            ).fetchone()
            return self._row_to_thesis(row) if row is not None else None
        finally:
            conn.close()

    def list_theses(
        self,
        *,
        ticker: str | None = None,
        setup_type: str | None = None,
        direction: str | None = None,
        resolution: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ThesisRecord]:
        """The journal LIST read (J-51) — persisted thesis rows VERBATIM, newest-declared-first.

        A READ-ONLY query (NO schema change — ``journal_schema_version`` stays 4) that backs the
        single ``GET /research/journal`` serving path. Returns the SAME ``ThesisRecord`` shape
        ``get_thesis`` returns (ONE owner over the persisted ``theses`` rows — nothing is recomputed
        here; resolution / reasons / stamps / dates are all reads of already-persisted values), so the
        row-projection layer in routes.py has a single, consistent source.

        Filters (all optional, AND-combined; an absent filter does not constrain):
          * ``ticker`` / ``setup_type`` / ``direction`` — exact-match on those columns;
          * ``resolution`` AND ``status`` — both filter the SAME terminal-status column (a resolution
            IS the thesis's terminal status: ``played_out | abandoned | invalidated | expired``);
            ``status`` additionally matches the non-terminal ``active``. They are kept as two filter
            names because goal.md's API surface lists both; supplying both ANDs them (so an
            unsatisfiable combination like ``status=active&resolution=played_out`` returns nothing,
            never a coerced result).
        Ordering is ``created_wall_ts DESC, id DESC`` (newest-declared-first; ``id`` breaks ties
        deterministically). ``limit``/``offset`` paginate; ``limit=None`` returns all matches (the
        route applies the config-owned page-size policy before calling — the store imposes no cap of
        its own so a test can read the whole table)."""
        clauses: list[str] = []
        params: list[object] = []
        if ticker is not None:
            clauses.append("ticker = ?")
            params.append(ticker)
        if setup_type is not None:
            clauses.append("setup_type = ?")
            params.append(setup_type)
        if direction is not None:
            clauses.append("direction = ?")
            params.append(direction)
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if resolution is not None:
            clauses.append("status = ?")
            params.append(resolution)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            f"SELECT * FROM theses {where} "
            "ORDER BY created_wall_ts DESC, id DESC"
        )
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        elif offset:
            # OFFSET without LIMIT is not portable in sqlite; use the max-rows sentinel.
            sql += " LIMIT -1 OFFSET ?"
            params.append(offset)
        conn = self._read_conn()
        try:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_thesis(r) for r in rows]
        finally:
            conn.close()

    def list_row_context(
        self, thesis_ids: list[str]
    ) -> dict[str, tuple[str | None, bool, bool]]:
        """The per-thesis context the journal-ROW projection needs, read VERBATIM in two bulk queries.

        For each id in ``thesis_ids`` returns ``(resolution_reason, has_entry, has_exit)`` where:
          * ``resolution_reason`` is the ``evidence`` of the thesis's LAST appended verdict event (the
            terminal expired/interruption/resolution reason the engine/sweep already wrote) — read
            verbatim, NEVER recomputed; ``None`` if the thesis has no events yet;
          * ``has_entry`` / ``has_exit`` are the persisted action-mark presence facts.

        Bulk (one query per fact across all ids) so the list endpoint is not N+1. The row projection
        only USES the reason when the thesis is terminal (an active thesis's last event is its
        ``pending`` declaration, which the projection ignores), so passing the last-event evidence for
        every id is safe and keeps this a pure read."""
        if not thesis_ids:
            return {}
        placeholders = ",".join("?" for _ in thesis_ids)
        conn = self._read_conn()
        try:
            # Last appended event per thesis (MAX(id) = last inserted) → its evidence string.
            reason_rows = conn.execute(
                f"""
                SELECT ve.thesis_id AS tid, ve.evidence AS evidence
                FROM verdict_events ve
                JOIN (
                    SELECT thesis_id, MAX(id) AS max_id
                    FROM verdict_events
                    WHERE thesis_id IN ({placeholders})
                    GROUP BY thesis_id
                ) last ON ve.id = last.max_id
                """,
                thesis_ids,
            ).fetchall()
            reasons = {r["tid"]: r["evidence"] for r in reason_rows}
            # Mark presence per thesis (one row per kind that exists).
            mark_rows = conn.execute(
                f"""
                SELECT DISTINCT thesis_id, kind
                FROM actions
                WHERE thesis_id IN ({placeholders})
                """,
                thesis_ids,
            ).fetchall()
        finally:
            conn.close()
        entries: dict[str, bool] = {}
        exits: dict[str, bool] = {}
        for r in mark_rows:
            if r["kind"] == "entry":
                entries[r["thesis_id"]] = True
            elif r["kind"] == "exit":
                exits[r["thesis_id"]] = True
        return {
            tid: (reasons.get(tid), entries.get(tid, False), exits.get(tid, False))
            for tid in thesis_ids
        }

    def get_actions(self, thesis_id: str) -> list[ActionRecord]:
        """Every action mark recorded for a thesis, in insertion order. Used by the resolve route to
        enforce the anti-survivorship rule (an entry-marked thesis can never be abandoned)."""
        conn = self._read_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM actions WHERE thesis_id=? ORDER BY id ASC", (thesis_id,)
            ).fetchall()
            return [
                ActionRecord(
                    id=r["id"],
                    thesis_id=r["thesis_id"],
                    kind=r["kind"],
                    price=r["price"],
                    logical_ts=r["logical_ts"],
                    wall_ts=r["wall_ts"],
                    # ``spread_at_mark`` is keyed defensively: a pre-v3 row (read mid-migration in a
                    # belt-and-braces path) has no such column. The migration runs at open so file
                    # stores always have it; ``.keys()`` guards a hypothetical raw old row.
                    spread_at_mark=(
                        r["spread_at_mark"] if "spread_at_mark" in r.keys() else None
                    ),
                )
                for r in rows
            ]
        finally:
            conn.close()

    def has_entry_mark(self, thesis_id: str) -> bool:
        """True if the thesis carries at least one ``entry`` action mark (anti-survivorship guard)."""
        conn = self._read_conn()
        try:
            row = conn.execute(
                "SELECT 1 FROM actions WHERE thesis_id=? AND kind='entry' LIMIT 1",
                (thesis_id,),
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def verdict_events(self, thesis_id: str) -> list[VerdictEventRecord]:
        conn = self._read_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM verdict_events WHERE thesis_id=? ORDER BY id ASC",
                (thesis_id,),
            ).fetchall()
            return [
                VerdictEventRecord(
                    thesis_id=r["thesis_id"],
                    logical_ts=r["logical_ts"],
                    wall_ts=r["wall_ts"],
                    verdict=r["verdict"],
                    evidence=r["evidence"],
                    tape_state=r["tape_state"],
                    confidence=r["confidence"],
                    last=r["last"],
                    rule_first_true_ts=r["rule_first_true_ts"],
                    rule_first_true_price=r["rule_first_true_price"],
                )
                for r in rows
            ]
        finally:
            conn.close()

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

    @staticmethod
    def _row_to_thesis(row: sqlite3.Row) -> ThesisRecord:
        # ``risk_flags`` (v4, J-49): NULL (a pre-v4 thesis, never assessed) reads back as ``None`` so
        # the projection OMITS the key; a stored JSON list (incl. ``"[]"`` for assessed-nothing-fired)
        # decodes verbatim. Keyed defensively so a hypothetical raw pre-v4 row (read mid-migration) has
        # no such column — the migration runs at open so file stores always have it.
        raw_flags = row["risk_flags"] if "risk_flags" in row.keys() else None
        risk_flags = json.loads(raw_flags) if raw_flags is not None else None
        # ``execution_checks`` (v5, J-54): NULL (never computed — a pre-v5 resolution, or an
        # unresolved thesis) reads back as ``None`` so the journal detail OMITS the key; a stored JSON
        # object decodes verbatim. Keyed defensively so a hypothetical raw pre-v5 row (read
        # mid-migration) has no such column — the migration runs at open so file stores always have it.
        raw_checks = row["execution_checks"] if "execution_checks" in row.keys() else None
        execution_checks = json.loads(raw_checks) if raw_checks is not None else None
        # ``statement_final_statuses`` / ``grades`` / ``review_tags`` (v6, J-55/J-56/J-57): NULL
        # (never recorded/computed — a pre-v6 resolution, or an unreviewed thesis) reads back as
        # ``None`` so the journal surfaces OMIT each key; a stored JSON value decodes verbatim. Keyed
        # defensively (``.keys()``) so a hypothetical raw pre-v6 row (read mid-migration) has no such
        # column — the migration runs at open so file stores always have it.
        keys = row.keys()
        raw_final = row["statement_final_statuses"] if "statement_final_statuses" in keys else None
        statement_final_statuses = json.loads(raw_final) if raw_final is not None else None
        raw_grades = row["grades"] if "grades" in keys else None
        grades = json.loads(raw_grades) if raw_grades is not None else None
        raw_tags = row["review_tags"] if "review_tags" in keys else None
        review_tags = json.loads(raw_tags) if raw_tags is not None else None
        review_note = row["review_note"] if "review_note" in keys else None
        reviewed = bool(row["reviewed"]) if "reviewed" in keys and row["reviewed"] is not None else False
        # ``excursions`` (v7, J-58): NULL (never measured — a pre-v7 resolution, or an unresolved
        # thesis) reads back as ``None`` so the journal detail OMITS the key; a stored JSON object
        # (incl. the ``{"tracked": False}`` not-tracked marker) decodes verbatim. Keyed defensively so
        # a hypothetical raw pre-v7 row (read mid-migration) has no such column — the migration runs at
        # open so file stores always have it.
        raw_excursions = row["excursions"] if "excursions" in keys else None
        excursions = json.loads(raw_excursions) if raw_excursions is not None else None
        return ThesisRecord(
            id=row["id"],
            ticker=row["ticker"],
            setup_type=row["setup_type"],
            direction=row["direction"],
            invalidation_price=row["invalidation_price"],
            level_price=row["level_price"],
            status=row["status"],
            bound_source=row["bound_source"],
            data_feed=row["data_feed"],
            config_fingerprint=row["config_fingerprint"],
            entry_context=json.loads(row["entry_context"]),
            statements=json.loads(row["statements"]),
            created_logical_ts=row["created_logical_ts"],
            created_wall_ts=row["created_wall_ts"],
            risk_flags=risk_flags,
            execution_checks=execution_checks,
            statement_final_statuses=statement_final_statuses,
            grades=grades,
            review_tags=review_tags,
            review_note=review_note,
            reviewed=reviewed,
            excursions=excursions,
        )

    # --- lifecycle ------------------------------------------------------------------------------
    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._queue.put(_StopSentinel())
        self._worker.join(timeout=5.0)
        self._write_conn.close()
