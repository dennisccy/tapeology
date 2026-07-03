# goal-tape_to_profit-iter-7 Dev Handoff

**Phase:** goal-tape_to_profit-iter-7
**Date:** 03-07-2026
**Agent:** developer
**Status:** complete

## What Was Built

J-07 — the candidate-sweep harness, `python -m app.research.pnl_scan --out <path>`:

- **`app/research/pnl_scan.py` (new).** The sweep engine + `__main__` CLI entry. Enumerates every
  registered candidate profile (`Config.profile_registry()` filtered to non-default entries),
  backtests each against the current persisted champion (strategy held constant, profile varied)
  over every registered train dataset, then validates on every registered hold-out dataset — all
  through the EXISTING `BacktestJobManager.create` + `run_sync` path (no second computation path).
  Computes per-candidate `survivor` (hold-out net R AND net $ both beat champion, with candidate
  n ≥ `promotion_min_sample_size`), `robustness` (`robust` iff positive on every individual train
  dataset, else `speculative`), and `overfit` (positive train, failing the hold-out gate — the
  phase spec's own definition). On a genuine survivor, promotes inline: appends exactly one
  PnL-ledger row via the existing single writer (`pnl_ledger.append_validation_row`) THEN moves
  the champion pointer — in that order specifically, so a mid-promotion crash leaves a durable
  ledger row and an explicit, detectable (never silent) inconsistency on retry rather than a
  permanently silent orphan. Zero candidates or zero survivors is an honest, exit-0 outcome; a
  corrupt dataset or a non-`done` backtest aborts with an explicit error and nothing written. The
  `--out` report never contains a wall-clock field or a freshly-minted (per-run-random) backtest
  report id, so two independent fresh-state runs of an identical non-promoting scenario produce
  byte-identical bytes.
- **The persisted, movable champion pointer.** `app/research/store.py` gained a `champion_pointer`
  singleton-row table (schema migration v9→v10, `Config.journal_schema_version` bumped 9→10),
  seeded to the founding `{v1, default}` pair unconditionally at store-open (covers both a
  fresh-create and a migrate-from-v9 store; never re-seeds over an already-moved pointer), plus
  `get_champion_pointer()` / `set_champion_pointer(...)` accessors (the setter goes through the
  single writer queue, same discipline as every other write). `set_champion_pointer` is called
  from exactly one source file (`pnl_scan.py`), enforced by a source-scan test.
- **`app/research/profiles.py`** now reads the champion from the store
  (`profiles_projection(store, config)`) instead of the retired hardcoded
  `{STRATEGY_V1_ID, PROFILE_DEFAULT}` constant — `GET /research/profiles` (hence `/performance`
  and the MCP `get_endpoint` proxy) automatically reflects a real promotion with zero frontend
  changes. The served JSON shape is unchanged.
- **`GET /research/profiles`** (`app/research/routes.py`) now depends on `ResearchRegistry` (it
  previously took no dependency) and passes `registry.store` / `registry.config` into
  `profiles_projection`.
- **Config: `promotion_min_sample_size`** (`app/config.py`, default `5`) — the config-owned
  promotion-minimum-n gate, a dedicated field (not a reuse of `pnl_min_sample_size`, since the two
  thresholds gate different things: display labeling vs. promotion eligibility). Excluded from
  `config_fingerprint` (a judgment call, documented in the field's own docstring and flagged for
  reviewer attention — see Known Issues). The pinned default fingerprint `4d665603569b9dbf` is
  unchanged.

## Files Changed

- `apps/backend/app/research/pnl_scan.py` (new) — the sweep engine + CLI entry.
- `apps/backend/app/config.py` — `promotion_min_sample_size` field (+ fingerprint exclusion);
  `journal_schema_version` bumped 9→10 to match the new migration step.
- `apps/backend/app/research/store.py` — `champion_pointer` table, v9→v10 migration, seeding,
  `get_champion_pointer` / `set_champion_pointer`.
- `apps/backend/app/research/profiles.py` — reads the champion from the store instead of a
  hardcoded constant; `profiles_projection` now takes `(store, config)`.
- `apps/backend/app/research/routes.py` — `GET /research/profiles` gains a `ResearchRegistry`
  dependency.
- `apps/backend/tests/test_pnl_scan.py` (new) — 12 tests: fixture-sweep baseline, controlled
  survivor + promotion, min-n gate both ways, determinism, robust/speculative, overfit, the
  one-setter-call-site source-scan guard, honest empty/failure states (zero candidates, corrupt
  dataset, mid-promotion crash recovery), and a real CLI `main()` invocation.
- `apps/backend/tests/test_profiles_api.py` — migrated to the store-backed `ctx` fixture pattern
  (`test_pnl_ledger_api.py` precedent); added a case asserting the served champion reflects a
  moved pointer. All 4 original tests kept (no deletions), 1 new test added.
- `apps/backend/tests/test_no_execution_path.py` — added `pnl_scan.py` to the explicit
  non-vacuous-scan path assertions.
- `apps/backend/tests/test_journal_migration.py` — fixed two pre-existing assertions that
  over-specified a literal `9` alongside `CONFIG.journal_schema_version` (they would have gone
  stale at every future migration step, not just this one — brought in line with the ~28 other
  assertions in the same file that already used the self-adapting relative form); added the
  symmetric 8-test v9→v10 group (fixture-starts-at-v9, migrates-and-bumps, seeds-and-leaves-other-
  rows-verbatim, persists-end-to-end, reopen-idempotent, reopen-after-promotion-never-re-seeds,
  stale-version-row-does-not-crash, fresh-db-carries-the-table) mirroring the existing v8→v9
  group's exact shape — this file's own established pattern for every schema change.
- `apps/backend/tests/fixtures/journal_v9_schema.sql` (new) — committed v9-schema fixture (mirrors
  `journal_v8_schema.sql`, adds a pre-existing `pnl_ledger` row) for the new migration test group.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1025 passed, 1 skipped** (0 failed, 0 errors) — up from the iter-6 baseline of 1004
passed / 1 skipped (net +21 new tests: 12 in `test_pnl_scan.py`, 8 in `test_journal_migration.py`,
1 in `test_profiles_api.py`). No test deletions (verified via diff of test function names in every
changed test file). `tests/test_observer_equivalence.py`: 7/7 passed.

Frontend: `cd apps/frontend && npm run build` — exit 0, all 6 routes (incl. `/performance`)
compiled and type-checked cleanly with no source changes.

Live verification (not just tests):
- `python -m app.research.pnl_scan --out <path>` run directly against the real
  `TAPEOLOGY_JOURNAL_DB` / `TAPEOLOGY_DATASET_DIR` (the operator's actual journal, already at
  schema v9 with a real founding ledger row from a prior iteration) — the v9→v10 migration ran
  live, preserved the existing founding row byte-for-byte, seeded the champion pointer, and the
  sweep exited 0 with an honest zero-survivor report.
- Backend started via `scripts/start-backend.sh`, `GET /health` and `GET /research/profiles`
  verified over real HTTP, then stopped and restarted on the same port with no conflicts (port
  released cleanly both times).
- Determinism (two independent fresh-state runs of the fixture-pair scan, driven through the real
  CLI `main()`) verified byte-identical `--out` file contents.

## Known Issues

- **Flagged judgment call: `promotion_min_sample_size` is excluded from `config_fingerprint`.**
  The plan's design notes explicitly called this out as the iteration's single riskiest small
  decision (a `config.py:920` comment could be read either way). I excluded it, matching the
  `pnl_min_sample_size` precedent (a threshold that decides which candidate gets promoted/labeled,
  never the content of a persisted trade/fill/aggregate). Verified against the pinned default
  fingerprint test (`4d665603569b9dbf`, unchanged). A reviewer should re-check this reasoning
  explicitly, per the plan's own instruction.
- **Automatic promotion supports exactly one train + one hold-out dataset.** `pnl_ledger.
  append_validation_row` (reused verbatim, per the plan's explicit "out of scope: any change to
  `pnl_ledger.py`") structurally composes a row from exactly one train report + one hold-out
  report. The SCAN itself fully evaluates and reports every registered dataset per split (summed
  deltas, per-dataset breakdown) regardless of count, matching the "over all train datasets" /
  "hold-out dataset(s)" spec wording — but if an operator later registers a second train or
  hold-out dataset, automatic promotion is explicitly skipped with an honest note in the report
  rather than guessing which pair to cite. This matches today's shipped state exactly (one train,
  one hold-out) and is not exercised by any required test scenario; flagging it as a forward-
  looking design note rather than a gap in current behavior.
- **`journal_schema_version` bump (9→10) was not called out in the execution plan's file list**
  but is a required consequence of adding the `champion_pointer` table — every prior schema
  addition in this codebase bumped this same field, and skipping it broke 30 pre-existing tests in
  `tests/test_journal_migration.py` / `tests/test_research_store.py` (caught and fixed during
  implementation, see Tests Run). Flagging because it touches a field the plan didn't explicitly
  mention, even though it's a mechanical, precedented, and required part of "schema migration
  v9→v10" as specified.
- No other gaps against the phase spec's Definition of Done — all fixture-sweep, controlled-
  survivor, min-n-gate, determinism, robustness/overfit, single-source, and honest-failure-state
  clauses are covered by passing, exact-value-asserting tests (see `test_pnl_scan.py`).
