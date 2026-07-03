# goal-tape_to_profit-iter-3 Dev Handoff

**Phase:** goal-tape_to_profit-iter-3
**Date:** 2026-07-03
**Agent:** developer
**Status:** complete

## What Was Built

J-03 — Strategy grammar v1 + the deterministic backtest engine. The product's first PnL
measurement machinery, machine-surface only (zero frontend change).

- **Strategy grammar v1 (Data Contract row 34, config-owned).** `Config.strategy_definition(STRATEGY_V1_ID)`
  in `app/config.py` is the single owner of the complete v1 definition: entries are the EXISTING
  state-native setup arming (trend_continuation / absorption_reversal × long / short, reusing the
  studies' sustained-premise rule and the `study_arm_sustain_seconds` / `study_arm_cooldown_seconds`
  constants — no new indicator, no new inline threshold); exits by invalidation R-stop (the studies'
  arm-instant synthetic invalidation, R via the shared `marks.r_basis`), time horizon
  (`strategy_exit_horizon_seconds`), state-flip (opposing control state), and the explicit
  deterministic `dataset_end` forced exit; an explicit fee model (`strategy_fee_per_share` +
  `strategy_fee_min_per_trade` per fill); an explicit slippage model
  (`strategy_slippage_spread_fraction` of the recorded spread, adverse at each fill); and the fixed
  `strategy_dollars_per_r` notional. Level setups are NOT in v1 (no state-native arming exists).
- **Backtest runner (Data Contract row 31's single computer)** — new `app/research/backtests.py`.
  Deterministic, seeded, unpaced, single-threaded per run: consumes `DatasetStore.replay` ONLY (the
  public API — a source-scan test forbids any second dataset reader in the module), arms entries per
  the strategy (one open trade at a time, exits processed before arming, declared-order tie-break),
  simulates fills at recorded prices adjusted adversely by the slippage model, applies the fee
  model, and persists the report ONCE. Report: per-trade list (setup, direction, entry/exit logical
  ts + recorded prices + fill prices + spreads, exit reason `r_stop | horizon | state_flip |
  dataset_end`, gross/net R and $, fees, slippage) and aggregates (net AND gross R AND $, win rate,
  max drawdown (R), n) beside a seeded random-entry null baseline (same exits/fees/slippage, seed
  recorded, `backtest_null_entry_count` entries with seeded directions, each labeled `random_null`).
  Provenance: full dataset metadata verbatim (id + checksum + window + feed + counts), the strategy
  config echoed verbatim, profile id (`default`), `config_fingerprint`. Every report carries the
  visible register "simulated — assumed fees/slippage — not indicative of live results". A window
  arming zero trades yields an honest n=0 done report (empty trades; win rate / drawdown `None`).
- **Byte-identical re-runs.** The payload separates run-identity metadata (id, status,
  created_wall_ts, request echo) from the deterministic `result` block; identical requests
  reproduce `result` byte-for-byte (asserted at manager level, over the API, and live via curl —
  59,844 identical bytes on the full PG train dataset).
- **Cancellable job manager** (`BacktestJobManager`) mirroring `StudyJobManager` exactly:
  queued → running → done | cancelled | failed persisted through the single writer queue;
  cooperative cancel between events; a cancelled backtest carries NO result block (a partial
  simulated PnL is never served); a corrupt dataset (integrity error from the store) persists an
  explicit `failed` record carrying the error.
- **Persistence: schema v7 → v8.** New `backtests` table (the studies payload-blob shape) added
  under the versioned on-open migration discipline, proven against a NEW committed old-schema
  fixture (`tests/fixtures/journal_v7_schema.sql`): table arrives empty (a migration never
  fabricates a report), pre-existing rows round-trip verbatim, stale-version-row reopen is
  idempotent, rows survive store reload. The live check incidentally migrated the previous
  iteration's real v7 journal DB to v8 on startup without issue.
- **Routes — exactly four, on the existing research router** (Product Shape):
  `POST /research/backtests` (create + start; body: dataset_id, strategy_id, profile),
  `GET /research/backtests` (list, serving-only `backtest_list_max` cap),
  `GET /research/backtests/{id}` (detail), `POST /research/backtests/{id}/cancel`. GET serves
  stored rows verbatim. Validation: unknown dataset → 404; unknown strategy → 422; non-`default`
  profile → 422 (the profile registry is J-06); malformed body → 422; cancel unknown → 404 /
  terminal → 409.
- **Grep-style no-broker gate** — new `tests/test_no_execution_path.py`: a repo-wide (`apps/`)
  scan for order-placement / account-management / broker-execution-SDK patterns (compound
  identifiers with documented rationale, two tiers: universally forbidden vs the one documented
  read-only `TradingClient` home in the market-data adapter), proven non-vacuous and
  signal-bearing against a seeded counter-example.
- **MCP:** `app/mcp/__init__.py` diff is EXACTLY the two now-stale tool description strings
  (`datasets` and `backtests` no longer claim "404 until…"); zero proxy/transport/handler logic
  changes — the `backtests` tool flipped to live data by construction (verified byte-identical to
  REST both in the suite and live). `tests/test_mcp_server.py`: `backtests` moved out of the
  honest-404 premise, a byte-identity test on a non-empty 200 list added (polling the job to
  `done` first so byte comparisons cannot flap), the stdio honest-404 example switched to
  `pnl_ledger`.
- **Fingerprint discipline:** the seven new strategy/fee/slippage/null-baseline knobs ENTER
  `config_fingerprint` (the intended shift — tested knob by knob); the serving-only
  `backtest_list_max` is EXCLUDED with the documented pattern + pinning tests.

## Files Changed

- `apps/backend/app/config.py` -- STRATEGY_V1_ID + `strategy_definition()`; 7 fingerprint-entering strategy/backtest knobs + serving-only `backtest_list_max` (excluded, documented); `journal_schema_version` 7 → 8 with the v8 docstring entry
- `apps/backend/app/research/backtests.py` -- NEW: BacktestRunner + BacktestJobManager (row 31's single computer; reuses studies' statuses, `_premise_state`, `_control_state`, `_synthetic_invalidation`, `_PathPoint`, progress cadence, and `marks.r_basis`)
- `apps/backend/app/research/store.py` -- `backtests` table in the base schema; v7 → v8 migration step; `BacktestRecord` + insert/update/set_result/get/list methods (single writer queue)
- `apps/backend/app/research/routes.py` -- `BacktestRequest`; `ResearchRegistry.backtest_jobs`; the four backtest routes with the honest 404/422/409 matrix
- `apps/backend/app/main.py` -- shutdown drains backtest jobs beside study jobs (writer-queue safety)
- `apps/backend/app/mcp/__init__.py` -- exactly the two stale description strings (datasets, backtests)
- `apps/backend/tests/test_backtests.py` -- NEW: 26 runner/manager tests (config-owned definition, all four exit reasons deterministically calibrated on recorded sim/synthetic streams through the REAL store path, exact fill/fee/R/$ arithmetic, byte-identity, seeded null, n=0 honesty, committed fixture pair keyless e2e, lifecycle incl. corrupt-dataset failed, reload persistence, fingerprint matrix, single-R-formula/one-dataset-reader source discipline)
- `apps/backend/tests/test_backtests_api.py` -- NEW: 12 REST tests (happy path with full provenance, verbatim serving, list, API-level byte-identical re-run, full error matrix, mid-run cancel without result)
- `apps/backend/tests/test_no_execution_path.py` -- NEW: 4 tests — the repo-wide no-broker/order/account gate
- `apps/backend/tests/fixtures/journal_v7_schema.sql` -- NEW: committed v7 old-schema fixture DB (research records only) for the v7 → v8 migration proof
- `apps/backend/tests/test_journal_migration.py` -- 7 new v7 → v8 tests; the two literal current-version asserts updated for v8 (no test deleted or weakened)
- `apps/backend/tests/test_mcp_server.py` -- backtests out of NOT_YET_SHIPPED; non-empty-200 byte-identity test; stdio example → pnl_ledger

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **951 passed, 1 skipped** (was 901 passed / 1 skipped at iter-2 — +50 tests, none deleted or weakened; engine equivalence suite 7/7 inside the run)

Command: `cd apps/frontend && npm run build`
Result: **passes** (type-check + compile; zero frontend changes, page sizes unchanged)

Live verification (real uvicorn, keyless):
- `GET /research/backtests` → **200** `{"backtests":[]}` (the baseline-404 flip)
- keyless PG reference dataset → `POST /research/backtests` → polled to `done`; report carries the
  register, dataset id + checksum, strategy echo, profile `default`, fingerprint, seeded null
  (seed 1729, n=99 — one draw honestly skipped before the first recorded price), and one real
  trade (trend_continuation short, `dataset_end` exit) with net/gross R and $
- identical re-POST → **byte-identical** result payloads (59,844 bytes)
- error legs live: unknown dataset → 404, non-default profile → 422, unknown strategy → 422
- MCP `backtests` tool live vs REST → byte-identical, `isError: false`
- `scripts/start-backend.sh` start → stop → start again: healthy both times, no port conflict,
  port released cleanly; all test/verification servers killed afterwards

## Known Issues

- The null baseline can honestly serve fewer than `backtest_null_entry_count` trades when a seeded
  draw lands before the first recorded price (no price → no honest fill → skipped); the report
  records both `entry_count` (the configured draw count) and per-population `n` (the honest count).
- A trade armed at the very last recorded event closes at that same event as `dataset_end`
  (zero-move, costs-only) — deterministic and documented in the runner, listed here for review
  visibility.
- `config_fingerprint` shifts this iteration (the seven new research knobs) — intended, not a
  defect: the same shift discipline as every prior research-config addition; serving-only
  `backtest_list_max` is excluded with pinning tests.
- No frontend change by design (`Frontend Present: no`); browser evidence for J-03 is the
  machine-surface flow via in-page fetch per the iter-2 lesson — browser-qa's job, with the live
  curl evidence above as the dev-side proof.

## Suggested Next Phase

J-04 (the append-only PnL ledger): its founding baseline row evaluates strategy v1 on profile
`default` over the committed fixture train AND hold-out datasets using exactly this iteration's
backtest reports — `GET /research/pnl/ledger` plus the pure-rendered `reports/pnl/pnl-history.md`,
flipping the MCP `pnl_ledger` tool from its honest 404 the same way `datasets` and `backtests`
flipped.
