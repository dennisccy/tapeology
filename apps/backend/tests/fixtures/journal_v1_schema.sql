-- Committed iter-2 (schema v1) journal-DB fixture for the versioned-migration regression test
-- (capability 28). RESEARCH RECORDS ONLY — explicitly allowed by the persistence anti-goal as a
-- committed test fixture; there is NO tape data (no trades/quotes/candles/feature series) here.
--
-- This reproduces the EXACT v1 verdict_events shape: it deliberately LACKS the two capability-24
-- columns (rule_first_true_ts / rule_first_true_price) that v2 adds. The test builds a temp DB from
-- this SQL, opens the JournalStore against it, and asserts the v1 -> v2 migration adds the columns,
-- bumps schema_version to 2, and leaves the pre-existing rows intact with NULL rule_first_true
-- (never backfilled — the timeline is append-only). Committed as SQL rather than a binary .db so the
-- fixture is human-readable and the project's *.db gitignore rule stays in force.

PRAGMA foreign_keys=ON;

CREATE TABLE schema_version (
    version INTEGER NOT NULL
);

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

-- v1 verdict_events: NO rule_first_true_ts / rule_first_true_price columns (added by the v2 ALTER).
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
    FOREIGN KEY (thesis_id) REFERENCES theses (id)
);

CREATE TABLE hints (
    id                  TEXT PRIMARY KEY,
    ticker              TEXT NOT NULL,
    payload             TEXT NOT NULL,
    created_wall_ts     REAL NOT NULL
);

CREATE TABLE actions (
    id                  TEXT PRIMARY KEY,
    thesis_id           TEXT NOT NULL,
    kind                TEXT NOT NULL,
    price               REAL NOT NULL,
    logical_ts          REAL NOT NULL,
    wall_ts             REAL NOT NULL,
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

-- v1 stamp.
INSERT INTO schema_version (version) VALUES (1);

-- One pre-existing, terminally-resolved thesis with its append-only timeline (a pending row + an
-- expired row). These rows must survive the migration untouched and keep NULL rule_first_true.
INSERT INTO theses (
    id, ticker, setup_type, direction, invalidation_price, level_price,
    status, bound_source, data_feed, config_fingerprint,
    entry_context, statements, created_logical_ts, created_wall_ts
) VALUES (
    'v1thesis0001', 'SIM-BIDABS', 'absorption_reversal', 'long', 99.0, NULL,
    'expired', 'bid_absorption', 'sim', 'oldfingerprint00',
    '{"last": 100.0, "tape_state": "bid_absorption"}',
    '[{"text": "Sellers are being absorbed", "kind": "tape_state_is", "params": {"states": ["bid_absorption"]}}]',
    12.5, 1700000000.0
);

INSERT INTO verdict_events (
    thesis_id, logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last
) VALUES
    ('v1thesis0001', 12.5, 1700000000.0, 'pending',
     'Thesis declared. The tape is being watched against it.', 'bid_absorption', 0.6, 100.0),
    ('v1thesis0001', 40.0, 1700000200.0, 'expired',
     'Thesis expired on restart — the watch that declared it is no longer running.', NULL, NULL, 100.0);
