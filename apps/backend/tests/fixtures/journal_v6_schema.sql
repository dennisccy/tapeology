-- Committed iter-14 (schema v6) journal-DB fixture for the v6 -> v7 versioned-migration regression
-- test (capability 28 / J-58 excursions). RESEARCH RECORDS ONLY — explicitly allowed by the
-- persistence anti-goal as a committed test fixture; there is NO tape data (no
-- trades/quotes/candles/feature series) here.
--
-- This reproduces the EXACT v6 shape: theses ALREADY carries risk_flags (v3 -> v4),
-- execution_checks (v4 -> v5), and the v6 review-pillar columns (statement_final_statuses, grades,
-- review_tags, review_note, reviewed) — but deliberately LACKS the v7 ``excursions`` column. The
-- test builds a temp DB from this SQL, opens the JournalStore against it, and asserts the v6 -> v7
-- migration adds the single ``excursions`` column, bumps schema_version to 7, and leaves the
-- pre-existing RESOLVED thesis row intact with NULL excursions (never backfilled — a pre-migration
-- resolution never had its excursions measured, so the journal detail OMITS the key rather than
-- fabricate numbers at read). Committed as SQL (not a binary .db) so the fixture is human-readable
-- and the project's *.db gitignore rule holds.

PRAGMA foreign_keys=ON;

CREATE TABLE schema_version (
    version INTEGER NOT NULL
);

-- v6 theses: carries risk_flags (v3 -> v4), execution_checks (v4 -> v5), AND the v6 review-pillar
-- columns — but NOT the v7 excursions column.
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
    reviewed            INTEGER NOT NULL DEFAULT 0
);

-- v6 verdict_events: ALREADY carries the dwell-timing columns (added by the v1 -> v2 migration).
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

-- v6 actions: ALREADY carries spread_at_mark (added by the v2 -> v3 migration).
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

-- v6 stamp.
INSERT INTO schema_version (version) VALUES (6);

-- One pre-existing RESOLVED thesis declared+resolved+reviewed under v6 (with execution_checks,
-- statement_final_statuses, grades, and a saved review ALREADY computed, but the v7 excursions column
-- did NOT exist when it was written) — it must survive the v6 -> v7 migration and read excursions =
-- NULL (never backfilled, never measured at read), so the journal detail OMITS the excursions key
-- (the established honest-omission pattern). It carries a full v6 review payload so the round-trip of
-- the v6 columns is also exercised across the migration.
INSERT INTO theses (
    id, ticker, setup_type, direction, invalidation_price, level_price,
    status, bound_source, data_feed, config_fingerprint,
    entry_context, statements, created_logical_ts, created_wall_ts, risk_flags, execution_checks,
    statement_final_statuses, grades, review_tags, review_note, reviewed
) VALUES (
    'v6thesis0001', 'SIM-BUYER', 'trend_continuation', 'long', 98.0, NULL,
    'played_out', 'buyer_control', 'sim', 'oldfingerprint06',
    '{"last": 100.0, "tape_state": "buyer_control"}',
    '[{"text": "Buyers keep control", "kind": "tape_state_is", "params": {"states": ["buyer_control"]}}]',
    12.5, 1700000000.0, '[]',
    '{"checks": [{"check": "entered_before_confirmation", "status": "not_applicable", "evidence": "No entry was recorded."}], "suggested_mistake_tags": []}',
    '[{"status": "met"}]',
    '{"outcome": "thesis_held", "process": "clean", "process_evidence": "No execution check failed and no entry risk flag fired."}',
    '[]', NULL, 1
);

INSERT INTO verdict_events (
    thesis_id, logical_ts, wall_ts, verdict, evidence, tape_state, confidence, last,
    rule_first_true_ts, rule_first_true_price
) VALUES
    ('v6thesis0001', 12.5, 1700000000.0, 'pending',
     'Thesis declared. The tape is being watched against it.', 'buyer_control', 0.8, 100.0,
     NULL, NULL),
    ('v6thesis0001', 30.0, 1700000060.0, 'played_out',
     'You resolved this thesis as played out — the idea has run its course.', 'buyer_control', 0.85,
     101.5, NULL, NULL);
