-- Committed iter-3 (era-3, schema v7) journal-DB fixture for the v7 -> v8 versioned-migration
-- regression test (capability 28 / J-03 backtests). RESEARCH RECORDS ONLY — explicitly allowed by
-- the persistence anti-goal as a committed test fixture; there is NO tape data (no
-- trades/quotes/candles/feature series) here.
--
-- This reproduces the EXACT v7 shape: theses ALREADY carries every column through the v6 -> v7
-- ``excursions`` addition — but the DB deliberately LACKS the v8 ``backtests`` table. The test
-- builds a temp DB from this SQL, opens the JournalStore against it, and asserts the v7 -> v8
-- migration creates the ``backtests`` table (EMPTY — a migration never fabricates a backtest),
-- bumps schema_version to 8, and leaves every pre-existing research row intact and verbatim.
-- Committed as SQL (not a binary .db) so the fixture is human-readable and the project's *.db
-- gitignore rule holds.

PRAGMA foreign_keys=ON;

CREATE TABLE schema_version (
    version INTEGER NOT NULL
);

-- v7 theses: carries risk_flags (v3 -> v4), execution_checks (v4 -> v5), the v6 review-pillar
-- columns, AND the v7 excursions column.
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
    risk_flags          TEXT,
    execution_checks    TEXT,
    statement_final_statuses TEXT,
    grades              TEXT,
    review_tags         TEXT,
    review_note         TEXT,
    reviewed            INTEGER NOT NULL DEFAULT 0,
    excursions          TEXT
);

-- v7 verdict_events: ALREADY carries the dwell-timing columns (added by the v1 -> v2 migration).
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

-- v7 actions: ALREADY carries spread_at_mark (added by the v2 -> v3 migration).
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

-- NOTE: deliberately NO ``backtests`` table — that is exactly what the v7 -> v8 migration adds.

-- v7 stamp.
INSERT INTO schema_version (version) VALUES (7);

-- One pre-existing RESOLVED thesis written under v7 (with an excursions record ALREADY measured,
-- proving the v7 column round-trips verbatim across the v7 -> v8 migration) — the v8 step touches
-- NO existing table, so every field must read back byte-identical after the open.
INSERT INTO theses (
    id, ticker, setup_type, direction, invalidation_price, level_price,
    status, bound_source, data_feed, config_fingerprint,
    entry_context, statements, created_logical_ts, created_wall_ts, risk_flags, execution_checks,
    statement_final_statuses, grades, review_tags, review_note, reviewed, excursions
) VALUES (
    'v7thesis0001', 'SIM-BUYER', 'trend_continuation', 'long', 98.0, NULL,
    'played_out', 'buyer_control', 'sim', 'oldfingerprint07',
    '{"last": 100.0, "tape_state": "buyer_control"}',
    '[{"text": "Buyers keep control", "kind": "tape_state_is", "params": {"states": ["buyer_control"]}}]',
    12.5, 1700000000.0, '[]',
    '{"checks": [{"check": "entered_before_confirmation", "status": "not_applicable", "evidence": "No entry was recorded."}], "suggested_mistake_tags": []}',
    '[{"status": "met"}]',
    '{"outcome": "thesis_held", "process": "clean", "process_evidence": "No execution check failed and no entry risk flag fired."}',
    '[]', NULL, 1,
    '{"tracked": false, "populations": {}}'
);

INSERT INTO verdict_events (
    thesis_id, logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last,
    rule_first_true_ts, rule_first_true_price
) VALUES
    ('v7thesis0001', 12.5, 1700000000.0, 'pending',
     'Thesis declared. The tape is being watched against it.', 'buyer_control', 0.8, 100.0,
     NULL, NULL),
    ('v7thesis0001', 30.0, 1700000060.0, 'played_out',
     'You resolved this thesis as played out — the idea has run its course.', 'buyer_control', 0.85,
     101.5, NULL, NULL);

-- One pre-existing DONE study row so the v8 step is proven to leave the studies table untouched.
INSERT INTO studies (id, payload, created_wall_ts) VALUES (
    'v7study00001',
    '{"id": "v7study00001", "status": "done", "setup_type": "trend_continuation", "direction": "long", "data_feed": "sim", "config_fingerprint": "oldfingerprint07", "null_baseline_seed": 1729, "occurrences": [], "null_occurrences": [], "aggregates": {"setup": {"n": 0, "horizons": []}, "null_baseline": {"n": 0, "horizons": []}}}',
    1700000100.0
);
