# goal-fast_wall-iter-3 Dev Handoff

**Phase:** goal-fast_wall-iter-3
**Date:** 2026-07-17
**Agent:** developer
**Status:** complete

## What Was Built

Target journey **J-03** ("The arm memo — per-tick levels recompute becomes ~100 memo hits per
session"). Backend-only, zero frontend files touched (`Frontend Present: no`, confirmed by diff).

- **`levels.py`**: new `level_change_points(store, symbol) -> tuple[float, ...]` — a safe superset
  of every instant at which `compute_levels` could change for `symbol`: the union of every healthy
  selected series' own bar epochs, plus, for each `PRIOR_PERIOD_TIMEFRAMES` (`1d`/`1w`/`1mo`)
  series' bar, its `epoch + period_seconds` close instant. Mirrors `compute_levels`'s own
  healthy-series enumeration exactly (`store.list()`'s healthy half,
  `_select_one_series_per_timeframe`, `PRIOR_PERIOD_TIMEFRAMES`/`_PERIOD_SECONDS`) so it can never
  omit a series `compute_levels` itself reads. Zero change to `compute_levels`'s or
  `compute_confluence_zones`'s existing bodies — appended at the end of the file.
- **`tradability.py`**: new `basis_day_key(as_of_epoch) -> str` — the UTC session-date key
  `_resolve_basis`'s chosen prior session is constant for, returned as `_session_date(...).isoformat()`
  (reuses the existing `_session_date` helper verbatim — never a second date derivation). Zero
  change to `compute_tradability`'s or `_resolve_basis`'s existing bodies — appended at the end of
  the file.
- **`backtests.py`**: new `_StructureArmMemo` class (placed immediately before `class
  BacktestRunner`) — `levels_at(as_of_epoch)` buckets by `bisect.bisect_right` into a
  `level_change_points(...)` tuple resolved once at construction (cache miss falls back to the
  literal `compute_levels(` owner call); `tradability_at(as_of_epoch)` buckets by
  `basis_day_key(as_of_epoch)` (cache miss falls back to the literal `compute_tradability(` owner
  call). Exactly one memo instance is built per run, inside `_structure_tape_trades` (right after
  the existing `bar_store`/`symbol`/`epoch_anchor` guard) and inside `_structure_tape_map_trades`
  (same spot) — never shared across runs, never persisted. Threaded into `_structure_tape_arm` and
  `_structure_tape_map_arm` as a new keyword-only `memo=None` parameter; every pre-existing direct
  caller (including the two internal loop call sites before this diff, and the existing test that
  calls `_structure_tape_map_arm` directly) that does not pass `memo` gets today's exact
  uncached-direct-call behavior byte-for-byte. `BacktestRunner.run()`'s public signature is
  unchanged; v1's branch is untouched and never sees a memo.

## Files Changed

- `apps/backend/app/research/levels.py` — added `level_change_points(store, symbol)`. No other
  line changed.
- `apps/backend/app/research/tradability.py` — added `basis_day_key(as_of_epoch)`. No other line
  changed.
- `apps/backend/app/research/backtests.py` — added `import bisect`; added `level_change_points`/
  `basis_day_key` to the existing `.levels`/`.tradability` imports; added `_StructureArmMemo`;
  threaded `memo=None` keyword-only param through `_structure_tape_arm` and
  `_structure_tape_map_arm` (docstrings extended, bodies gain the `if memo is not None: ... else:
  <today's literal compute_*( call>` branch); `_structure_tape_trades` and
  `_structure_tape_map_trades` each build one memo and pass `memo=memo` at their call site. No
  change to `run()`'s signature or v1's branch.
- `apps/backend/tests/test_levels.py` — added `level_change_points` to the import block; appended
  3 tests (TC-1, TC-2, plus an honest-empty-tuple test for a never-recorded symbol) reusing the
  existing `_confluence_fixture`.
- `apps/backend/tests/test_tradability.py` — added `basis_day_key` to the import block; appended 3
  tests (TC-3, TC-4, plus a direct-computation cross-check that the SAME boundary where the key
  changes is where `compute_tradability` itself resolves a different `basis_as_of`), reusing the
  existing `_SYN_AS_OF`/`_seed_synthetic` fixture.
- `apps/backend/tests/test_backtests.py` — added `compute_levels`/`level_change_points`/
  `compute_tradability` imports; appended a new "The arm memo" section (~360 lines): a
  `_NoCacheArmMemo` stand-in class + `_run_unmemoized` helper (swaps `_StructureArmMemo` for a
  zero-caching equivalent via monkeypatch, so the byte-identity comparisons exercise the EXACT
  production interleave loop, never a hand-duplicated copy of it) — TC-5, TC-6; a dedicated bar
  fixture (`_memo_bust_level_bar_fixture`) engineering a 1d period-close instant strictly between
  two intraday bar epochs, with both a direct-call non-vacuous proof and a full-run byte-identity
  proof — TC-7; a `structure_tape_map` UTC-midnight-boundary test reusing `confluence_bar_store` —
  TC-8; a monotonic-bars fixture (`_many_interval_bar_fixture`, never forms a pivot) driving a
  `compute_levels` call-counting spy — TC-9; an empty-bar-store `compute_tradability` call-counting
  spy across a UTC midnight (day-key is a pure function of `as_of` alone, so this needs no bar
  fixture at all) — TC-10; a multi-interval fixture (`_multi_interval_trade_bar_fixture`) proving a
  >=5-change-point-interval run completes in well under the 10s budget with a real trade — TC-11.
- `docs/handoffs/goal-fast_wall-iter-3-dev.md` — this handoff.

**Zero diff** (verified via `git status`): `edge_report.py`, `edge_report_cache.py`, `bars.py`,
`datasets.py`, `dataset_index.py`, `routes.py`, `config.py`, and every frontend file — exactly the
plan's expected scope.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (the exact command iter-1/iter-2
used; `.claude/project-template.md` is still the framework's generic, unfilled template — see Known
Issues, carried forward from iter-2's own identical finding, not new).

Targeted run (the three touched modules only): `pytest tests/test_levels.py tests/test_tradability.py
tests/test_backtests.py -rA` → **114 passed, 0 failed, 0 skipped in 9.48s**, including all 13 new
tests (TC-1 through TC-11, plus 2 extra direct-computation cross-checks) and both
source-introspection guard tests (`test_structure_tape_reads_levels_from_the_one_canonical_compute_levels_owner`,
`test_structure_tape_map_reads_tradability_never_recomputes_levels_or_zones`).

Full suite result: **1440 passed, 7 skipped, 0 failed** (1447 collected total) — up from iter-2's
own baseline of 1427 passed / 7 skipped / 1434 collected by exactly the 13 new tests this iteration
adds (3 in `test_levels.py`, 3 in `test_tradability.py`, 7 in `test_backtests.py`); skip count is
byte-identical to iter-2's own (0 newly skipped or deleted). Verified three independent ways: (a)
the background run's own exit code 0 with zero `FAILED` occurrences anywhere in its captured
output, (b) a character-level count of the run's own dot/`s` progress markers (`1440` `.` + `7`
`s`, zero `F`), (c) a fresh `--collect-only -q` run summed per-file to confirm the `1447` total
independently. (A stray `.pytest_cache/v/cache/lastfailed` entry naming two tests from an
unrelated, much older session was checked directly — both node ids no longer exist in the
codebase at all, i.e. stale cache cruft predating this run, not a real failure.)

`config.config_fingerprint()` confirmed still `4d665603569b9dbf` by direct computation (no `Config`
field added — `bisect` is stdlib; `level_change_points`/`basis_day_key`/`_StructureArmMemo` are
pure functions/objects over existing inputs).

`git diff` confirmed additions-only against every pre-existing test function body across all three
test files (the only line removed anywhere in the three test files is the `tradability.py` import
statement gaining `basis_day_key` — never a test body).

## Pre-handoff verification

- **Service startup**: this iteration touches zero routes/config/startup-relevant files (`routes.py`
  and `config.py` both have zero diff — confirmed above). Instead of a full `scripts/dev.sh` port-
  binding cycle (unnecessary risk/cost for a change with no service-surface impact), verified the
  FastAPI app itself still imports and instantiates cleanly through the modified `backtests.py`
  (`routes.py` imports `BacktestJobManager`/`BacktestRunner` from it): `from app.main import app` →
  `Tapeology 0.1.0`, 20 routes registered, no import/startup error. The full suite's own
  `*_api.py` test modules (which build the real FastAPI `TestClient` against this same app) also
  passed, independently confirming the import chain end-to-end. No server process was started or
  left running.
- **External integrations**: N/A — this iteration adds no adapter/scraper/external API surface
  (pure in-memory memoization over existing in-process function calls).
- **Native dependency binaries**: N/A — `bisect` is stdlib, no new runtime dependency (matches the
  interlude's own anti-goal).

## Known Issues

- `.claude/project-template.md` resolves to the framework's generic, unfilled template (same finding
  iter-2's dev handoff already recorded) — inferred the real test command from
  `apps/backend/pyproject.toml`'s `[tool.pytest.ini_options]` and iter-1/iter-2's own handoffs
  instead. Not a gap introduced by this iteration.
- This iteration ships no UI surface and adds no operator-run compute trigger (J-04, not yet built),
  so the memo's throughput win is not yet observable from `/structure` — it is latent infrastructure
  for J-04/J-05's sweep, exactly as scoped. The counting-spy tests (TC-9, TC-10) are the mechanical
  proof the speedup is real; there is no user-facing artifact to screenshot this iteration.

## Suggested Next Phase

J-04 ("The operator-run compute — button, background job, CLI warmer") per goal.md's own
dependency order (J-01 → J-02 → J-03 → J-04 → J-05) and the phase spec's own BACKGROUND section,
which explicitly recommends it next: with J-03's memo now collapsing the per-tick recompute this
iteration's own goal.md Vision measured as the ≥400× catastrophic-slowdown culprit, a J-04 compute
trigger built on top of it should finally let a real edge-report sweep progress at a sane rate
instead of the memo-less code shipping a fast-looking button that still never finishes. J-04
touches new files only (`edge_report_compute.py` + three new routes + a CLI + the `/structure`
button/poll wiring) — it does not modify `levels.py`, `tradability.py`, or `backtests.py` further,
so it carries a different (lower) frozen-foundation risk profile than this iteration.
