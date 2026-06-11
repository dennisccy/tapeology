-- Committed iter-7 (schema v2) journal-DB fixture for the v2 -> v3 versioned-migration regression
-- test (capability 28 / J-52). RESEARCH RECORDS ONLY — explicitly allowed by the persistence
-- anti-goal as a committed test fixture; there is NO tape data (no trades/quotes/candles/feature
-- series) here.
--
-- This reproduces the EXACT v2 shape: verdict_events ALREADY carries the v2 dwell-timing columns
-- (rule_first_true_ts / rule_first_true_price), but the actions table deliberately LACKS the
-- spread_at_mark column that v3 adds. The test builds a temp DB from this SQL, opens the
-- JournalStore against it, and asserts the v2 -> v3 migration adds actions.spread_at_mark, bumps
-- schema_version to 3, and leaves the pre-existing rows intact with NULL spread_at_mark on the
-- pre-existing action (never backfilled — a moment value is never recomputed). Committed as SQL (not
-- a binary .db) so the fixture is human-readable and the project's *.db gitignore rule holds.

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

-- v2 verdict_events: ALREADY carries the dwell-timing columns (added by the v1 -> v2 migration).
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

-- v2 actions: NO spread_at_mark column (added by the v3 ALTER).
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

-- v2 stamp.
INSERT INTO schema_version (version) VALUES (2);

-- One pre-existing thesis with an append-only timeline AND a pre-existing ENTRY action mark (so the
-- v3 migration is proven not to backfill the action's spread_at_mark — it must read NULL after).
INSERT INTO theses (
    id, ticker, setup_type, direction, invalidation_price, level_price,
    status, bound_source, data_feed, config_fingerprint,
    entry_context, statements, created_logical_ts, created_wall_ts
) VALUES (
    'v2thesis0001', 'SIM-BUYER', 'trend_continuation', 'long', 98.0, NULL,
    'active', 'buyer_control', 'sim', 'oldfingerprint02',
    '{"last": 100.0, "tape_state": "buyer_control"}',
    '[{"text": "Buyers keep control", "kind": "tape_state_is", "params": {"states": ["buyer_control"]}}]',
    12.5, 1700000000.0
);

INSERT INTO verdict_events (
    thesis_id, logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last,
    rule_first_true_ts, rule_first_true_price
) VALUES
    ('v2thesis0001', 12.5, 1700000000.0, 'pending',
     'Thesis declared. The tape is being watched against it.', 'buyer_control', 0.8, 100.0,
     NULL, NULL);

-- A pre-existing entry action recorded under v2 (no spread_at_mark column existed when it was
-- written) — must survive the migration and read spread_at_mark = NULL (never backfilled).
INSERT INTO actions (
    id, thesis_id, kind, price, logical_ts, wall_ts
) VALUES
    ('v2act0001', 'v2thesis0001', 'entry', 100.0, 15.0, 1700000050.0);
