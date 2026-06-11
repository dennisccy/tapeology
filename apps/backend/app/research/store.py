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
    created_wall_ts     REAL NOT NULL
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
    price               REAL NOT NULL,
    logical_ts          REAL NOT NULL,
    wall_ts             REAL NOT NULL,
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
    """One persisted thesis row (read back as an immutable record)."""

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


@dataclass(frozen=True)
class ActionRecord:
    """One persisted action mark (entry | exit) — recorded verbatim from the user (no inferred fill).

    The entry-mark UI is a later iteration (J-52); this record exists now so the resolve path can
    enforce the anti-survivorship rule (an entry-marked thesis can never be abandoned) and so a unit
    test can inject an action row directly to prove the guard."""

    id: str
    thesis_id: str
    kind: str
    price: float
    logical_ts: float
    wall_ts: float


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

        # Future steps (current < 3, …) append here, each in its own BEGIN IMMEDIATE block.

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
    def insert_thesis(self, record: ThesisRecord) -> None:
        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                INSERT INTO theses (
                    id, ticker, setup_type, direction, invalidation_price, level_price,
                    status, bound_source, data_feed, config_fingerprint,
                    entry_context, statements, created_logical_ts, created_wall_ts
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
                    entry_context, statements, created_logical_ts, created_wall_ts
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
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
        """Persist one action mark (entry | exit). The entry-mark UI is J-52; this writer exists now so
        a unit test can inject an action row directly to prove the resolve route's
        entry-marked-refuses-abandon guard."""

        def _fn(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                INSERT INTO actions (id, thesis_id, kind, price, logical_ts, wall_ts)
                VALUES (?,?,?,?,?,?)
                """,
                (
                    record.id,
                    record.thesis_id,
                    record.kind,
                    record.price,
                    record.logical_ts,
                    record.wall_ts,
                ),
            )

        self._do_write(_fn)

    def expire_stale_actives(self, wall_ts: float) -> list[str]:
        """Startup sweep: resolve every thesis still ``active`` to ``expired`` and append a final
        ``expired`` timeline event for each (no entry marks exist yet, so there is no
        survives-with-entry-mark exception to honor). Returns the affected thesis ids.

        Done as ONE queued write so the sweep is atomic and runs off any hot path."""

        def _fn(conn: sqlite3.Connection) -> list[str]:
            rows = conn.execute(
                "SELECT id FROM theses WHERE status = 'active'"
            ).fetchall()
            ids = [r["id"] for r in rows]
            for tid in ids:
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
            return ids

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
        )

    # --- lifecycle ------------------------------------------------------------------------------
    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._queue.put(_StopSentinel())
        self._worker.join(timeout=5.0)
        self._write_conn.close()
