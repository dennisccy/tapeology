-- Committed iter-4 (era-3, schema v8) journal-DB fixture for the v8 -> v9 versioned-migration
-- regression test (capability 28 / J-04 PnL ledger). RESEARCH RECORDS ONLY — explicitly allowed by
-- the persistence anti-goal as a committed test fixture; there is NO tape data (no
-- trades/quotes/candles/feature series) here.
--
-- This reproduces the EXACT v8 shape: theses ALREADY carries every column through the v6 -> v7
-- ``excursions`` addition AND the v7 -> v8 ``backtests`` table exists (with one pre-existing DONE
-- backtest row) — but the DB deliberately LACKS the v9 ``pnl_ledger`` table. The test builds a
-- temp DB from this SQL, opens the JournalStore against it, and asserts the v8 -> v9 migration
-- creates the ``pnl_ledger`` table (EMPTY — a migration never fabricates a ledger row), bumps
-- schema_version to 9, and leaves every pre-existing research row intact and verbatim.
-- Committed as SQL (not a binary .db) so the fixture is human-readable and the project's *.db
-- gitignore rule holds.

PRAGMA foreign_keys=ON;

CREATE TABLE schema_version (
    version INTEGER NOT NULL
);

-- v8 theses: carries risk_flags (v3 -> v4), execution_checks (v4 -> v5), the v6 review-pillar
-- columns, AND the v7 excursions column (the theses shape did not change at v8).
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

-- v8 verdict_events: ALREADY carries the dwell-timing columns (added by the v1 -> v2 migration).
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

-- v8 actions: ALREADY carries spread_at_mark (added by the v2 -> v3 migration).
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

-- v8 backtests: the table the v7 -> v8 migration added (payload-blob shape).
CREATE TABLE backtests (
    id                  TEXT PRIMARY KEY,
    payload             TEXT NOT NULL,
    created_wall_ts     REAL NOT NULL
);

-- NOTE: deliberately NO ``pnl_ledger`` table — that is exactly what the v8 -> v9 migration adds.

-- v8 stamp.
INSERT INTO schema_version (version) VALUES (8);

-- One pre-existing RESOLVED thesis written under v8 (with an excursions record ALREADY measured,
-- proving every pre-v9 column round-trips verbatim across the v8 -> v9 migration) — the v9 step
-- touches NO existing table, so every field must read back byte-identical after the open.
INSERT INTO theses (
    id, ticker, setup_type, direction, invalidation_price, level_price,
    status, bound_source, data_feed, config_fingerprint,
    entry_context, statements, created_logical_ts, created_wall_ts, risk_flags, execution_checks,
    statement_final_statuses, grades, review_tags, review_note, reviewed, excursions
) VALUES (
    'v8thesis0001', 'SIM-BUYER', 'trend_continuation', 'long', 98.0, NULL,
    'played_out', 'buyer_control', 'sim', 'oldfingerprint08',
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
    ('v8thesis0001', 12.5, 1700000000.0, 'pending',
     'Thesis declared. The tape is being watched against it.', 'buyer_control', 0.8, 100.0,
     NULL, NULL),
    ('v8thesis0001', 30.0, 1700000060.0, 'played_out',
     'You resolved this thesis as played out — the idea has run its course.', 'buyer_control', 0.85,
     101.5, NULL, NULL);

-- One pre-existing DONE study row so the v9 step is proven to leave the studies table untouched.
INSERT INTO studies (id, payload, created_wall_ts) VALUES (
    'v8study00001',
    '{"id": "v8study00001", "status": "done", "setup_type": "trend_continuation", "direction": "long", "data_feed": "sim", "config_fingerprint": "oldfingerprint08", "null_baseline_seed": 1729, "occurrences": [], "null_occurrences": [], "aggregates": {"setup": {"n": 0, "horizons": []}, "null_baseline": {"n": 0, "horizons": []}}}',
    1700000100.0
);

-- One pre-existing DONE backtest row (the v8 table's payload-blob shape) so the v9 step is proven
-- to leave the backtests table untouched and its row byte-identical.
INSERT INTO backtests (id, payload, created_wall_ts) VALUES (
    'v8backtest01',
    '{"id": "v8backtest01", "status": "done", "dataset_id": "d8", "strategy_id": "v1", "profile": "default", "null_baseline_seed": 1729, "config_fingerprint": "oldfingerprint08", "created_wall_ts": 1700000200.0, "result": {"register": "simulated — assumed fees/slippage — not indicative of live results", "trades": [], "aggregates": {"n": 0, "gross_r": 0.0, "net_r": 0.0, "gross_usd": 0.0, "net_usd": 0.0, "win_rate": null, "max_drawdown_r": null}}}',
    1700000200.0
);
