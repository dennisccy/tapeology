# goal-fast_wall-iter-3 Execution Plan

Target journey: **J-03 — The arm memo** (`structure_tape`/`structure_tape_map` backtests stop
re-running the full levels/tradability pipeline on every confirming tick). Backend-only, keyless,
automated. Depth: full (touches three frozen-foundation research files at once — see phase spec
BACKGROUND). Required-still-passing: J-01, J-02, J-07 — carried forward via mechanical byte-identity
proof (TC-15), not a fresh browser pass, per the iter-2 lesson naming J-03 explicitly.

Alignment check: this iteration is a direct, verbatim build-out of `docs/goal.md`'s Key Capability 3
("The arm memo") and sits exactly where the goal's own dependency order (J-01 → J-02 → J-03 → …)
places it. No drift or scope creep detected against goal.md or the interlude's anti-goals.

## What to Build

- `level_change_points(store, symbol) -> tuple[float, ...]` in `levels.py`: sorted, deduplicated
  union of every healthy series' own bar epochs for `symbol` plus, for each
  `PRIOR_PERIOD_TIMEFRAMES` (`1d`/`1w`/`1mo`) series' bar, its `epoch + period_seconds` close
  instant — mirroring `compute_levels`'s own `_select_one_series_per_timeframe` enumeration.
  Documents the contract: between two consecutive change points, `compute_levels` is a constant
  function of `as_of` (a superset of true change points is always safe; a subset never is). Zero
  change to `compute_levels`'s or `compute_confluence_zones`'s existing bodies.
- `basis_day_key(as_of_epoch) -> str` in `tradability.py`: the UTC session-date key, reusing the
  existing `_session_date` helper (never a second date derivation). Zero change to
  `compute_tradability`'s or `_resolve_basis`'s existing bodies.
- `_StructureArmMemo` in `backtests.py`: `levels_at(as_of_epoch)` keyed by `bisect_right` into a
  `level_change_points(...)` tuple resolved once at construction (miss/out-of-range falls back to
  the literal `compute_levels(` owner call); `tradability_at(as_of_epoch)` keyed by
  `basis_day_key(as_of_epoch)` (miss falls back to the literal `compute_tradability(` owner call).
  Exactly one memo instance built per run inside `_structure_tape_trades` and
  `_structure_tape_map_trades` (never shared across runs, never persisted). Threaded into
  `_structure_tape_arm` (call site ~line 695) and `_structure_tape_map_arm` (call site ~line 807)
  as a new keyword-only `memo=None` parameter — every existing caller/test keeps calling with
  `memo=None` and gets today's exact direct-call behavior byte-for-byte. `BacktestRunner.run()`'s
  public signature is unchanged; v1's branch is untouched and never sees a memo.
- Full test-first contract TC-1 through TC-15 (phase spec's own enumeration is authoritative;
  summarized under Key Test Scenarios below), including both goal.md-named memo-bust legs, both
  counting spies, and the mechanical TC-15 byte-identity gate that stands in for J-01/J-02/J-07's
  skipped browser pass this `Frontend Present: no` iteration.
- Dev handoff at `docs/handoffs/goal-fast_wall-iter-3-dev.md`.

## Agents Required

- backend-data: yes -- implement `level_change_points`, `basis_day_key`, `_StructureArmMemo`, and
  the full TC-1..TC-15 test suite exactly as scoped below; verify TC-12/TC-13/TC-14/TC-15 hold with
  zero edits to any pre-existing test body or to the two source-introspection guard tests.
- frontend-ux: no -- J-03 ships no UI surface; `Frontend Present: no` per the phase spec's Goal Mode
  Metadata; zero frontend files touched.

## Frontend Present
Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/research/levels.py` -- add `level_change_points(store, symbol)`; no other
  change.
- `apps/backend/app/research/tradability.py` -- add `basis_day_key(as_of_epoch)`; no other change.
- `apps/backend/app/research/backtests.py` -- add `_StructureArmMemo`; thread `memo=None`
  keyword-only param through `_structure_tape_arm` (~695) and `_structure_tape_map_arm` (~807);
  build one memo instance each inside `_structure_tape_trades` (~607) and
  `_structure_tape_map_trades` (~714). No change to `run()`'s signature or v1's branch.
- `apps/backend/tests/test_levels.py` -- add TC-1, TC-2 (`level_change_points` union/superset +
  constant-between-change-points contract).
- `apps/backend/tests/test_tradability.py` -- add TC-3, TC-4 (`basis_day_key` same-date stability +
  cross-boundary distinctness).
- `apps/backend/tests/test_backtests.py` -- add TC-5..TC-11 (memo determinism x2, both memo-bust
  legs, both counting spies, the multi-interval interactive-budget fixture). TC-12..TC-15 are
  verification-only: every pre-existing test body in this file plus `test_levels.py`/
  `test_tradability.py`, and both source-introspection guard tests
  (`test_backtests.py:1500-1508`, `:932-943`), must pass with a zero/additions-only git diff.
- `docs/handoffs/goal-fast_wall-iter-3-dev.md` -- new dev handoff.

Expected **zero diff**: `edge_report.py`, `edge_report_cache.py`, `bars.py`, `datasets.py`,
`dataset_index.py`, `routes.py`, `config.py`, and every frontend file. A wider diff than the three
product files + three test files above is a signal the memo has leaked outside its intended
per-run, in-memory scope (phase spec's own scope-discipline note).

## Key Test Scenarios

- TC-1/TC-2: `level_change_points` returns a sorted, deduped superset including every healthy
  series' bar epochs plus each prior-period bar's close instant; `compute_levels` is byte-identical
  (`json.dumps(..., sort_keys=True)`) for two `as_of` instants strictly between the same two
  consecutive change points.
- TC-3/TC-4: `basis_day_key` returns the identical key for two `as_of_epoch` values on the same UTC
  date, and different keys across a UTC midnight boundary.
- TC-5/TC-6: a memoized `structure_tape` run and a memoized `structure_tape_map` run are each
  byte-identical to the same run with `memo=None`.
- TC-7/TC-8 (memo-bust legs): a daily-period close instant falling strictly between two intraday bar
  epochs, and a run spanning a UTC date boundary — each proven byte-identical memoized vs.
  unmemoized AND proven non-vacuous (the arming decision or resolved basis genuinely differs across
  the boundary).
- TC-9/TC-10 (counting spies): `compute_levels` called exactly once per distinct
  `level_change_points` interval actually visited (never per tick); `compute_tradability` called
  exactly once per distinct `basis_day_key` actually visited (never per tick).
- TC-11: a new fixture crossing >= 5 change-point intervals completes the memoized backtest in
  under 10s wall-clock with a non-empty `trades` list.
- TC-12/TC-13: every existing `structure_tape`/`structure_tape_map` pinned-value/arming test (lines
  ~349-970) and both source-introspection guard tests pass with byte-unmodified source
  (additions-only git diff).
- TC-14: full backend suite green, 0 newly-skipped/deleted tests, `config.config_fingerprint()`
  still `4d665603569b9dbf`.
- TC-15 (required mechanical stand-in for J-01/J-02/J-07 non-regression — no browser pass this
  iteration): every existing pinned-value test in `test_levels.py`/`test_tradability.py` passes with
  byte-unmodified source, proving `compute_levels`'s/`compute_tradability`'s served bytes are
  unchanged for `/structure`'s Tradable Map and Case Studies readers.

## Guardrails (highest risk this iteration)

- The memo must never become a second computation path: both source-introspection guard tests
  (forbidding `_swing_pivots`, `_prior_period_extremes`, `_cluster_levels`, `_grade_zone` anywhere in
  `backtests.py`, and requiring the literal `compute_levels(`/`compute_tradability(` owner calls stay
  present) must pass unmodified.
- The memo is in-memory, one instance per `BacktestRunner.run()` call, never persisted, never shared
  — matches `runs/goal-session-fast_wall/state/blueprint.md`'s pre-registered "Rebuildable
  accelerators" row verbatim; no blueprint edit expected.
- No `Config` field, no new runtime dependency (`bisect` is stdlib) — fingerprint must stay
  `4d665603569b9dbf`.
