-- Committed iter-13 (schema v4) journal-DB fixture for the v4 -> v5 versioned-migration regression
-- test (capability 28 / J-54). RESEARCH RECORDS ONLY — explicitly allowed by the persistence
-- anti-goal as a committed test fixture; there is NO tape data (no trades/quotes/candles/feature
-- series) here.
--
-- This reproduces the EXACT v4 shape: theses ALREADY carries risk_flags (added by the v3 -> v4
-- migration), actions spread_at_mark, and verdict_events the v1 -> v2 dwell-timing columns — but the
-- theses table deliberately LACKS the execution_checks column that v5 adds. The test builds a temp
-- DB from this SQL, opens the JournalStore against it, and asserts the v4 -> v5 migration adds
-- theses.execution_checks, bumps schema_version to 5, and leaves the pre-existing RESOLVED thesis
-- row intact with NULL execution_checks (never backfilled — a pre-migration resolution never had its
-- checks computed, so the journal detail OMITS the execution_checks key rather than fabricate a
-- pass/fail at read). Committed as SQL (not a binary .db) so the fixture is human-readable and the
-- project's *.db gitignore rule holds.

PRAGMA foreign_keys=ON;

CREATE TABLE schema_version (
    version INTEGER NOT NULL
);

-- v4 theses: carries risk_flags (added by the v3 -> v4 migration) but NO execution_checks column
-- (added by the v5 ALTER).
CREATE TABLE theses (
    id                  TEXT PRIMARY KEY,
    ticker              TEXT NOT NULL,
    setup_type          TEXT NOT NULL,
    direction           TEXT NOT NULL,
    invalidation_price  REAL NOT NULL,
    level_price         REAL,
    status              TEXT NOT NULL,
    bound_source        TEXT NOT NULL,
    data_feed           TEXT NOT NULL,
    config_fingerprint  TEXT NOT NULL,
    entry_context       TEXT NOT NULL,
    statements          TEXT NOT NULL,
    created_logical_ts  REAL NOT NULL,
    created_wall_ts     REAL NOT NULL,
    risk_flags          TEXT
);

-- v4 verdict_events: ALREADY carries the dwell-timing columns (added by the v1 -> v2 migration).
CREATE TABLE verdict_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    thesis_id           TEXT NOT NULL,
    logical_ts          REAL NOT NULL,
    wall_ts             REAL NOT NULL,
    verdict             TEXT NOT NULL,
    evidence            TEXT NOT NULL,
    tape_state          TEXT,
    confidence          REAL,
    last                REAL,
    rule_first_true_ts     REAL,
    rule_first_true_price  REAL,
    FOREIGN KEY (thesis_id) REFERENCES theses (id)
);

CREATE TABLE hints (
    id                  TEXT PRIMARY KEY,
    ticker              TEXT NOT NULL,
    payload             TEXT NOT NULL,
    created_wall_ts     REAL NOT NULL
);

-- v4 actions: ALREADY carries spread_at_mark (added by the v2 -> v3 migration).
CREATE TABLE actions (
    id                  TEXT PRIMARY KEY,
    thesis_id           TEXT NOT NULL,
    kind                TEXT NOT NULL,
    price               REAL NOT NULL,
    logical_ts          REAL NOT NULL,
    wall_ts             REAL NOT NULL,
    spread_at_mark      REAL,
    FOREIGN KEY (thesis_id) REFERENCES theses (id)
);

CREATE TABLE studies (
    id                  TEXT PRIMARY KEY,
    payload             TEXT NOT NULL,
    created_wall_ts     REAL NOT NULL
);

CREATE TABLE study_occurrences (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    study_id            TEXT NOT NULL,
    payload             TEXT NOT NULL,
    FOREIGN KEY (study_id) REFERENCES studies (id)
);

-- v4 stamp.
INSERT INTO schema_version (version) VALUES (4);

-- One pre-existing RESOLVED thesis declared+resolved under v4 (no execution_checks column existed
-- when it was written) — it must survive the v4 -> v5 migration and read execution_checks = NULL
-- (never backfilled, never computed at read), so the journal detail OMITS the execution_checks key
-- (assessed-never vs assessed-at-resolution never collapse — the established honest-omission pattern).
-- It carries an empty risk_flags list (assessed at declaration, nothing fired) so the round-trip of
-- the v4 risk_flags column is also exercised.
INSERT INTO theses (
    id, ticker, setup_type, direction, invalidation_price, level_price,
    status, bound_source, data_feed, config_fingerprint,
    entry_context, statements, created_logical_ts, created_wall_ts, risk_flags
) VALUES (
    'v4thesis0001', 'SIM-BUYER', 'trend_continuation', 'long', 98.0, NULL,
    'played_out', 'buyer_control', 'sim', 'oldfingerprint04',
    '{"last": 100.0, "tape_state": "buyer_control"}',
    '[{"text": "Buyers keep control", "kind": "tape_state_is", "params": {"states": ["buyer_control"]}}]',
    12.5, 1700000000.0, '[]'
);

INSERT INTO verdict_events (
    thesis_id, logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last,
    rule_first_true_ts, rule_first_true_price
) VALUES
    ('v4thesis0001', 12.5, 1700000000.0, 'pending',
     'Thesis declared. The tape is being watched against it.', 'buyer_control', 0.8, 100.0,
     NULL, NULL),
    ('v4thesis0001', 30.0, 1700000060.0, 'played_out',
     'You resolved this thesis as played out — the idea has run its course.', 'buyer_control', 0.85,
     101.5, NULL, NULL);

-- A pre-existing entry action recorded under v4 (with a spread_at_mark) — survives the migration.
INSERT INTO actions (
    id, thesis_id, kind, price, logical_ts, wall_ts, spread_at_mark
) VALUES
    ('v4act0001', 'v4thesis0001', 'entry', 100.0, 15.0, 1700000050.0, 0.02);
