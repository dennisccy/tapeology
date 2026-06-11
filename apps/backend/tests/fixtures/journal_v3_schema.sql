-- Committed iter-11 (schema v3) journal-DB fixture for the v3 -> v4 versioned-migration regression
-- test (capability 28 / J-49). RESEARCH RECORDS ONLY — explicitly allowed by the persistence
-- anti-goal as a committed test fixture; there is NO tape data (no trades/quotes/candles/feature
-- series) here.
--
-- This reproduces the EXACT v3 shape: actions ALREADY carries spread_at_mark and verdict_events the
-- v2 dwell-timing columns, but the theses table deliberately LACKS the risk_flags column that v4
-- adds. The test builds a temp DB from this SQL, opens the JournalStore against it, and asserts the
-- v3 -> v4 migration adds theses.risk_flags, bumps schema_version to 4, and leaves the pre-existing
-- thesis row intact with NULL risk_flags (never backfilled — a pre-migration thesis was never
-- risk-assessed, so its projection OMITS the risk_flags key rather than read a dishonest empty
-- list). Committed as SQL (not a binary .db) so the fixture is human-readable and the project's
-- *.db gitignore rule holds.

PRAGMA foreign_keys=ON;

CREATE TABLE schema_version (
    version INTEGER NOT NULL
);

-- v3 theses: NO risk_flags column (added by the v4 ALTER).
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
    created_wall_ts     REAL NOT NULL
);

-- v3 verdict_events: ALREADY carries the dwell-timing columns (added by the v1 -> v2 migration).
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

-- v3 actions: ALREADY carries spread_at_mark (added by the v2 -> v3 migration).
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

-- v3 stamp.
INSERT INTO schema_version (version) VALUES (3);

-- One pre-existing thesis declared under v3 (no risk_flags column existed when it was written) — it
-- must survive the v3 -> v4 migration and read risk_flags = NULL (never backfilled), so its
-- projection OMITS the risk_flags key (assessed-never vs assessed-nothing-fired never collapse).
INSERT INTO theses (
    id, ticker, setup_type, direction, invalidation_price, level_price,
    status, bound_source, data_feed, config_fingerprint,
    entry_context, statements, created_logical_ts, created_wall_ts
) VALUES (
    'v3thesis0001', 'SIM-BUYER', 'trend_continuation', 'long', 98.0, NULL,
    'active', 'buyer_control', 'sim', 'oldfingerprint03',
    '{"last": 100.0, "tape_state": "buyer_control"}',
    '[{"text": "Buyers keep control", "kind": "tape_state_is", "params": {"states": ["buyer_control"]}}]',
    12.5, 1700000000.0
);

INSERT INTO verdict_events (
    thesis_id, logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last,
    rule_first_true_ts, rule_first_true_price
) VALUES
    ('v3thesis0001', 12.5, 1700000000.0, 'pending',
     'Thesis declared. The tape is being watched against it.', 'buyer_control', 0.8, 100.0,
     NULL, NULL);

-- A pre-existing entry action recorded under v3 (with a spread_at_mark) — survives the migration.
INSERT INTO actions (
    id, thesis_id, kind, price, logical_ts, wall_ts, spread_at_mark
) VALUES
    ('v3act0001', 'v3thesis0001', 'entry', 100.0, 15.0, 1700000050.0, 0.02);
