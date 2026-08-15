# Iteration State — referee

**After iteration:** 4 · **Date:** 2026-08-15 · **Verdict:** CONTINUE

## Journeys

3 passing (J-01 J-02 J-03) · 6 failing (J-04..J-09) · 1 partial (J-10 — kept half green; era-end
clauses wait on J-09) — 10 total

## Active blockers

- none blocking the build. Riders for J-04 (dev): (1) OWNER RULING — `min_attainable_p` is served
  as `1/(draws_used+1)` in exact mode, half what the fixed method can reach (`referee_stats.py`,
  `permutation_test`'s return dict); spec:168 reads both ways; settle before J-04–J-08 read it.
  (2) non-finite (NaN/inf) observations silently break the exact-mode floor guarantee — J-04's
  adapters are the first producers: reject at the door, count the exclusion. (3) TC-8's `n2==1`
  fast-path test asserts only a wide ~6-SE band.
- carried from J-02, open under T-1, needs a ruling before J-06: `_strategy_observation()`'s
  `epoch_anchor = dataset.get("epoch_anchor") or 0.0` turns a legitimate `None` into a 1969
  session date (`referee_evidence.py`).
- human-owned, non-blocking: a "fill in" placeholder in `what-to-click.md` ended iteration 4 as
  `closure_failed`, leaving its 5 source files UNCOMMITTED; trendora's port-8255 backend is down.

## Last 2 verdicts

- iter 4: CONTINUE — J-03 fixed and independently re-proven (exact repro now 2/7 not 1/7; my own
  2,500-case sweep, 0 violations / 448 exactly on the floor); suite 2,505 pass / 8 skip.
- iter 3: ESCALATE — the statistics core's exact-enumeration p could fall below its own floor.

## Do not redo

- The exact-enumeration floor fix is DONE and proven both directions (`referee_stats.py`
  `permutation_test`); do not rewrite the module, re-derive its constants, or touch the seeded
  branch. `STATS_CORE_VERSION` is already v2 with the attestation re-pinned — do not re-bump.
- Lead 1 is CLOSED: shared `_is_stale_basis` + additive `stale_basis_dates` on both call sites; do
  NOT change the newest-then-filter order (that IS spec T-6's identity).
- The oracle suite now enters the enumeration branch (TC-3) with an anti-conservative mutant (TC-4)
  and a tail-regime floor guard; 83s of the 120s budget — new cases must fit ~37s.
- J-01/J-02 are green with unchanged served values; ride as Required-still-passing, never re-target.
- UT-07's FAIL is a mis-specified supplementary check (two Desk panels render only once a screen is recorded), not a regression.
