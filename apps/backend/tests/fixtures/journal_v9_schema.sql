-- Committed iter-7 (era-3, schema v9) journal-DB fixture for the v9 -> v10 versioned-migration
-- regression test (capability 28 / J-07 champion pointer). RESEARCH RECORDS ONLY — explicitly
-- allowed by the persistence anti-goal as a committed test fixture; there is NO tape data (no
-- trades/quotes/candles/feature series) here.
--
-- This reproduces the EXACT v9 shape: theses/actions/verdict_events carry every column through
-- the v6 -> v7 ``excursions`` addition, the v7 -> v8 ``backtests`` table exists, AND the v8 -> v9
-- ``pnl_ledger`` table exists (with one pre-existing row) — but the DB deliberately LACKS the v10
-- ``champion_pointer`` table. The test builds a temp DB from this SQL, opens the JournalStore
-- against it, and asserts the v9 -> v10 migration creates the ``champion_pointer`` table, SEEDS
-- it to the founding ``v1``/``default`` pair (the ONE table this era's migrations ever seed —
-- every other addition arrives empty), bumps schema_version to 10, and leaves every pre-existing
-- research row (incl. the pnl_ledger row) intact and verbatim.
-- Committed as SQL (not a binary .db) so the fixture is human-readable and the project's *.db
-- gitignore rule holds.

PRAGMA foreign_keys=ON;

CREATE TABLE schema_version (
    version INTEGER NOT NULL
);

-- v9 theses: unchanged since v8 (the v9 step only adds the pnl_ledger table).
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

CREATE TABLE backtests (
    id                  TEXT PRIMARY KEY,
    payload             TEXT NOT NULL,
    created_wall_ts     REAL NOT NULL
);

-- v9 pnl_ledger: the table the v8 -> v9 migration added (payload-blob shape), carrying one
-- pre-existing row (proving IT round-trips verbatim across the v9 -> v10 migration too).
CREATE TABLE pnl_ledger (
    enhancement_id      TEXT PRIMARY KEY,
    payload             TEXT NOT NULL,
    created_wall_ts     REAL NOT NULL
);

-- NOTE: deliberately NO ``champion_pointer`` table — that is exactly what the v9 -> v10
-- migration adds (and, uniquely among this era's table additions, SEEDS rather than leaves empty).

-- v9 stamp.
INSERT INTO schema_version (version) VALUES (9);

-- One pre-existing RESOLVED thesis written under v9, proving every pre-v10 column round-trips
-- verbatim across the v9 -> v10 migration (that step touches NO existing table).
INSERT INTO theses (
    id, ticker, setup_type, direction, invalidation_price, level_price,
    status, bound_source, data_feed, config_fingerprint,
    entry_context, statements, created_logical_ts, created_wall_ts, risk_flags, execution_checks,
    statement_final_statuses, grades, review_tags, review_note, reviewed, excursions
) VALUES (
    'v9thesis0001', 'SIM-BUYER', 'trend_continuation', 'long', 98.0, NULL,
    'played_out', 'buyer_control', 'sim', 'oldfingerprint09',
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
    ('v9thesis0001', 12.5, 1700000000.0, 'pending',
     'Thesis declared. The tape is being watched against it.', 'buyer_control', 0.8, 100.0,
     NULL, NULL),
    ('v9thesis0001', 30.0, 1700000060.0, 'played_out',
     'You resolved this thesis as played out — the idea has run its course.', 'buyer_control', 0.85,
     101.5, NULL, NULL);

-- One pre-existing DONE study row so the v10 step is proven to leave the studies table untouched.
INSERT INTO studies (id, payload, created_wall_ts) VALUES (
    'v9study00001',
    '{"id": "v9study00001", "status": "done", "setup_type": "trend_continuation", "direction": "long", "data_feed": "sim", "config_fingerprint": "oldfingerprint09", "null_baseline_seed": 1729, "occurrences": [], "null_occurrences": [], "aggregates": {"setup": {"n": 0, "horizons": []}, "null_baseline": {"n": 0, "horizons": []}}}',
    1700000100.0
);

-- One pre-existing DONE backtest row so the v10 step is proven to leave the backtests table
-- untouched and its row byte-identical.
INSERT INTO backtests (id, payload, created_wall_ts) VALUES (
    'v9backtest01',
    '{"id": "v9backtest01", "status": "done", "dataset_id": "d9", "strategy_id": "v1", "profile": "default", "null_baseline_seed": 1729, "config_fingerprint": "oldfingerprint09", "created_wall_ts": 1700000200.0, "result": {"register": "simulated — assumed fees/slippage — not indicative of live results", "trades": [], "aggregates": {"n": 0, "gross_r": 0.0, "net_r": 0.0, "gross_usd": 0.0, "net_usd": 0.0, "win_rate": null, "max_drawdown_r": null}}}',
    1700000200.0
);

-- One pre-existing PnL-ledger row (the v8 -> v9 table's payload-blob shape) so the v10 step is
-- proven to leave the pnl_ledger table untouched and its row byte-identical (the ledger's
-- append-only guarantee must hold across a migration too).
INSERT INTO pnl_ledger (enhancement_id, payload, created_wall_ts) VALUES (
    'v9-founding-row',
    '{"enhancement_id": "v9-founding-row", "title": "pre-v10 founding row", "founding": true, "baseline": null, "candidate": {"train": {"net_r": -0.1, "net_usd": -10.0, "n": 2}, "holdout": {"net_r": 0.2, "net_usd": 20.0, "n": 2}}, "created_wall_ts": 1700000250.0}',
    1700000250.0
);
