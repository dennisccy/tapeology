# Iteration State — referee

**After iteration:** 5 · **Date:** 2026-08-15 · **Verdict:** ESCALATE

## Journeys

4 passing (J-01 J-02 J-03 J-04) · 5 failing (J-05 J-06 J-07 J-08 J-09) · 1 partial (J-10 — kept
half green, era-end clauses wait on J-09) — 10 total

## Active blockers

- none blocking the build. J-05 is unblocked and buildable today (keyless, fixture-based).
- human, non-blocking, outside this project: trendora's backend on port 8255 is still down since
  iteration 2 and needs a person to restart it.
- process: iteration 5 asked for full depth in its own spec and was demoted to lean
  (`depth_demoted`, `reason: full-cap`), so permanent append-only machinery shipped without the
  hard-audit lane — the reason this verdict is ESCALATE.

## Last 2 verdicts

- iter 5: ESCALATE — J-04 matched nulls verified passing (suite 2,545 passed / 8 skipped, own
  run; own probe proved the seeded subset draw is real), but next depth must be full.
- iter 4: CONTINUE — J-03 statistics core moved partial → passing after the exact-mode p floor
  fix was independently re-proven.

## Do not redo

- J-04 is DONE: `app/research/referee_null.py` (both variants, three signature-bearing spec ids,
  append-only store + run ledger + compute manager + CLI) and its 5 `/research/desk/referee/nulls*`
  routes in `referee_routes.py`. Do not rebuild or re-scope them.
- `min_attainable_p` is SETTLED: `2/(draws_used+1)` exact, `1/(draws_used+1)` seeded
  (`referee_stats.py`; ruling in `state/assumptions.md`). No `STATS_CORE_VERSION` bump is owed.
- The non-finite fail-loud guard exists at `_t_statistic` / `bootstrap_ci_occurrence` /
  `bootstrap_ci_cluster`; the null adapter excludes-and-counts instead. Both are correct as-is.
- The import-topology guard split in `tests/test_referee_guards.py` matches goal.md's Read-side
  law — do not re-widen or re-merge it. TC-8 is already tightened 6.0 → 3.5 SE with a mutation test.
- STILL OPEN (do not treat as done): no shipped test discriminates the seeded SUBSET draw (every
  fixture has eligible ≤ K); `window_overlap_fraction`'s formula is gated by no test; the J-02
  `epoch_anchor or 0.0` lead must be settled before J-06.
