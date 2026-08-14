# goal-referee-iter-3 Dev Handoff

**Phase:** goal-referee-iter-3
**Date:** 2026-08-14
**Agent:** developer
**Status:** complete

## What Was Built

- **`apps/backend/app/research/referee_stats.py`** (new) — the calibrated statistics core (J-03),
  implementing `docs/referee-statistical-spec.md` §1/§3.4–§3.6/§5/§6 verbatim:
  - Module constants per spec §1: `REFEREE_SEED`, `REFEREE_STREAM_RECIPE`, `REFEREE_B`,
    `REFEREE_ENUMERATION_THRESHOLD`, `REFEREE_CI_LEVEL`, `REFEREE_MIN_CLUSTERS_FOR_CI`,
    `REFEREE_ORACLE_B`, `REFEREE_ORACLE_REPLICATIONS`, `REFEREE_ORACLE_BUDGET_SECONDS`,
    `REFEREE_ORACLE_SIZE_TOLERANCE` — plain module constants, never `Config` fields.
  - `referee_stream(hypothesis_id, purpose, session_date=None, i=None)` — the one seeded stream
    constructor implementing the pinned recipe verbatim; rejects an unknown `purpose` and rejects
    `i` without `session_date`.
  - `_draw_indices_without_replacement`/`_draw_indices_with_replacement` — the hand-coded
    `rng.randrange`-based draw primitives (the `desk_forward._draw_anchor_indices` discipline,
    matched exactly rather than imported — the import-ban guard proves this module never imports
    `desk_forward`). Never `random.sample`, never a global/unseeded `random.Random()` instance,
    never numpy for any seeded draw (verified by AST source-scan tests).
  - `bootstrap_ci_occurrence` / `bootstrap_ci_cluster` — percentile bootstrap CIs at
    `REFEREE_CI_LEVEL`, both clustering levels. The clustered CI returns the literal
    `insufficient_sample` state below `REFEREE_MIN_CLUSTERS_FOR_CI` (8) informative sessions,
    never a fabricated interval; above the floor it serves a real interval plus an MDE disclosure
    (`z_{1-alpha} * sd*(T)`, `z` derived from stdlib `statistics.NormalDist` rather than a
    hand-pinned magic literal or scipy).
  - `permutation_test` — the primary confirmatory test (`referee-test-perm-v1`'s algorithm): the
    combined statistic `T = sum(w_s*delta_s)/sum(w_s)` with `w_s = n1_s*n2_s/(n1_s+n2_s)` (the
    ONE formula both pre-registered weight forms, A/C's harmonic and B's, reduce to — implemented
    once in `_t_statistic`, shared by the permutation test and the clustered CI). Full enumeration
    (deterministic, zero RNG) when the total per-session combination product is
    `<= REFEREE_ENUMERATION_THRESHOLD`; otherwise exactly `b` (default `REFEREE_B`) seeded draws
    via independent per-session sub-streams. `p = (1 + #extreme) / (draws + 1)` for "greater"
    sidedness (mirrored for "less"; `|T*| >= |T|` for "two-sided"), with the minimum-attainable p
    served beside every p. A performance fast-path (mathematically proven equivalent to the
    general Fisher-Yates algorithm for the `n1==1`/`n2==1` cases) keeps the oracle suite's
    replication-heavy calls inside budget — documented inline in the function body.
  - `sign_flip_result` / `equal_weight_t` — the two named robustness disclosures (spec §3.5),
    computed and served alongside the primary result but never substituted for it; the primary
    call's own `p`/`t` is provably unaffected by also computing the variants (unit-tested).
  - `benjamini_hochberg` — BH at a caller-supplied `q` over a caller-supplied `p_values` list
    (`len(p_values)` IS `m`; the caller folds an unevaluated/withdrawn candidate in as the literal
    `p=1.0` before calling — this function never drops anything from `m`), plus
    Benjamini-Yekutieli-adjusted values as a separate, non-deciding disclosure.
  - `run_oracle_attestation()` / `verify_oracle_attestation()` — the fail-closed attestation: a
    pinned tiny fixture run through the permutation test and the occurrence CI, compared against a
    pinned expected/tolerance pair captured from this build. `verify_oracle_attestation`
    re-derives the live expected/tolerance from the CURRENT build's own constants and re-checks
    `actual` field by field — it never trusts a stored `passed` flag, so a corrupted/hand-edited
    record is caught even when its own `passed` field claims success.
  - `referee_stats_parameters()` — a small stub aggregator scoped to this module's own constants
    (per the iteration's NOTES: the full `referee_parameters()` embedding-and-hashing pattern
    arrives with J-04, not blocked on here).

- **`apps/backend/tests/test_referee_oracles.py`** (new) — the seeded oracle suite per spec §6,
  all 6 cases plus the mutation fixture (9 test functions total, including the runtime-budget
  guard):
  1. Size, iid-skewed (lognormal-shifted-to-zero-mean, n_s=1/K=4, S=16) — holds calibration.
  2. Size, heavy-tailed (Student-t(3), same shape) — holds calibration.
  3a. An unclustered pooled-label permutation foil (the classic pseudo-replication mistake — every
      pairwise occurrence-minus-anchor difference within a session pooled as if independent,
      ignoring that they share one session-level regime draw) over-rejects on a session-clustered
      null, while the PRIMARY within-session test — run on the identical 400 datasets — holds
      size.
  3b. The session-level sign-flip variant mis-sizes on a skewed (lognormal sigma=2.0), unequal
      (n_s=1/K=3) one-sided fixture, while the primary permutation on the same fixture holds size.
  4. Power at a +0.5*sd shift, S=40 — rejection rate matches a pinned golden (0.8950 ± 0.05).
  5. The 20-null + 1-positive BH sweep (m=21, q=0.10) — false-admission rate and positive-admitted
     rate both match pinned goldens (0.0114 / 0.9375, within tolerance).
  6. Clustered CI coverage at S=40 (>=0.88, target ~95%) and the S=6 `insufficient_sample` case.
  - Mutation fixture — a deliberately mis-implemented test statistic (the permuted indices are
    drawn and the stream IS advanced, but the recomputed statistic accidentally reuses the
    unpermuted per-session deltas every draw — a realistic "forgot to apply the draw" bug)
    substituted into case 1's own generator/seed: rejection rate = 0.0 exactly, provably outside
    the tolerance band — proving the suite would catch a wrong implementation.
  - Every foil/mutant is implemented from scratch in the test file (never by calling into
    `referee_stats.py`'s own code with a flag flipped), so a bug in the primary implementation
    could not accidentally also break its own foil.
  - A module-scoped, autouse `_oracle_suite_budget_guard` fixture asserts the file's own
    wall-clock time (first test's setup through the last test's teardown) stays within
    `REFEREE_ORACLE_BUDGET_SECONDS` (120s). **Measured twice in isolation: 74.7s and 76.7s**, and
    confirmed again inside the full 2503-test suite run (0 errors, 0 failures reported for this
    file).

- **`apps/backend/tests/test_referee_stats.py`** (new) — 32 fast, deterministic mechanics tests
  covering TC-1 through TC-7, TC-16, TC-17, TC-19: stream determinism + purpose/argument
  validation + a source-scan proving no `random.sample`/unseeded-`Random()` call exists; a
  degenerate-fixture CI test (all-identical values, hand-derivable to an exact point) plus an
  independently-reimplemented reference bootstrap (a from-scratch resampling loop built in the
  test file, not calling any `referee_stats` resampling helper) that reproduces the module's own
  CI bounds exactly; the clustered-CI floor at exactly 7 vs 8 informative sessions; a
  hand-enumerated 3-permutation fixture with a hand-derived p=0.5; a from-scratch reference
  permutation loop cross-checking the seeded B-draw branch's exact extreme count; BH's k* on a
  hand-computed 5-candidate family plus the unevaluated-candidate-folds-as-p=1 case (m grows from
  5 to 6, never drops); byte-identical full-computation reruns; oracle-attestation round-trip and
  four distinct corruption-detection cases (`actual`, `stats_core_version`, `expected`, non-dict
  input).

- **Carried rider 1** — `apps/backend/tests/test_referee_evidence.py` gains real assertions for
  `_signal_reaches_session_complete` (previously zero coverage): a fixture signal engineered so
  its computed `last_bar_epoch` lands exactly at, one second before, and one second after the
  `REFEREE_SESSION_COMPLETE_ET` (15:55 ET) boundary — True at/after, False strictly before; plus
  the no-`forward`-block absence case and a dedicated test naming the disclosed bar-gap-blind
  limitation (the function reads `minutes_to_close` as bar-count-equivalent, not true wall-clock
  time) as an asserted behavior.

- **Carried rider 2** — the same test file gains real assertions for
  `resolve_referee_obs_cache_db_path` (exported, never called before this iteration): the
  `TAPEOLOGY_REFEREE_OBS_CACHE_DB` env-var override returns verbatim; unset, it defaults to
  `referee_obs_cache.db` as a sibling of `resolve_desk_playbook_dir`'s own resolved directory.

- **Carried rider 3** — one clarifying sentence added to `docs/referee-statistical-spec.md` §2,
  documenting that `provenance.detector_basis` is `None` for every strategy-family observation by
  design (ratifying iteration 2's already-accepted convention as standing for this era, per the
  fresh `## iter-3 — goal-decomposer` entry already present in
  `runs/goal-session-referee/state/assumptions.md`). Documentation-only: zero `.py` diff for this
  rider.

- **`apps/backend/tests/test_referee_guards.py`** extended with a `referee_stats.py`-scoped
  import-ban guard (AST-structural, the file's own established pattern): zero imports of
  `desk_playbook_detect`, `desk_playbook_context`, `desk_forward`, `levels`, or `tradability`
  inside `referee_stats.py`, plus a seeded can-fail counter-test.

## Files Changed

- `apps/backend/app/research/referee_stats.py` -- new: the statistics core (streams, CI,
  permutation test, robustness disclosures, BH/BY, oracle attestation).
- `apps/backend/tests/test_referee_oracles.py` -- new: the seeded oracle suite (6 spec §6 cases +
  mutation fixture), self-timed against the 120s budget.
- `apps/backend/tests/test_referee_stats.py` -- new: fast mechanics unit tests for
  `referee_stats.py`'s own API.
- `apps/backend/tests/test_referee_evidence.py` -- extended with the two carried-rider test
  functions (`_signal_reaches_session_complete`, `resolve_referee_obs_cache_db_path`); zero
  change to `referee_evidence.py`'s own source.
- `apps/backend/tests/test_referee_guards.py` -- extended with the `referee_stats.py`-scoped
  import-ban guard + its counter-test.
- `docs/referee-statistical-spec.md` -- one clarifying sentence in §2 (documentation-only rider).

No other file changed. Confirmed via `git diff --stat`: zero diff to `referee_evidence.py`'s own
source, `desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`, `setups.py`,
`pnl_scan.py`, `app/config.py`, `app/main.py`, or any route file. No new `Config` field, no new
runtime dependency (`requirements.txt`/`pyproject.toml` untouched); `referee_stats.py` itself
imports only `itertools`, `math`, `random`, `statistics` (verified by an AST source-scan test) --
never `scipy`, never `numpy`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=<tmp>/suite.xml`

Result: **2495 passed, 0 failed, 0 errors, 8 skipped** (2503 collected; runtime 240.5s). This
exceeds iteration 2's recorded floor of >= 2,446 pass / 8 skip -- 2446 + 49 new tests (32 in
`test_referee_stats.py` + 9 in `test_referee_oracles.py` + 2 guard tests + 6 rider tests) = 2495
exactly, confirming zero regressions and every new test counted.

Isolated re-runs for reproducibility (per the DoD's "reproduced independently" requirement):
- `test_referee_oracles.py` alone: 9 passed, run twice, 74.7s then 76.7s (both well inside the
  120s `REFEREE_ORACLE_BUDGET_SECONDS`).
- `test_referee_stats.py` alone: 32 passed in 0.16s.
- `test_referee_evidence.py` alone: 23 passed (17 pre-existing + 6 new).
- `test_referee_guards.py` alone: 13 passed (11 pre-existing + 2 new).

Anti-goal / fingerprint checks (all re-verified after the full suite run, not just claimed):
- `Config().config_fingerprint()` == `08e471b10130e1e2` (unchanged).
- `test_mcp_server.EXPECTED_TOOLS` == 20 tools, byte-identical list (unchanged).
- `git diff --stat` scoped to exactly the 3 modified files listed above (plus the pipeline's own
  `telemetry.jsonl`, not a developer edit).
- App import sanity: `import app.main` succeeds cleanly with `referee_stats.py` present
  (unconsumed by any route this iteration, so nothing new is wired into startup).

## Known Issues

- **No live-server / browser verification performed this iteration**, by design: J-03 is
  backend-only and unconsumed by any route, page, or MCP tool (`referee_stats.py` is imported by
  no other module yet). The iter spec's own TESTING REQUIREMENTS section states J-03 "has no live
  endpoint to smoke" and its entire acceptance runs against the seeded oracle suite. The
  already-running pinned backend (`:8301`)/frontend (`:3301`) were left untouched -- no server was
  started, stopped, or restarted for this iteration, consistent with "not touching what a lean
  backend-only iteration doesn't need to touch" and the explicit instruction to avoid
  pattern-based process kills. J-10's browser regression sentinel (cockpit, `/structure` AAPL
  Load, every shipped `/desk` section) is this iteration's Required-still-passing item but is a
  QA-stage responsibility per the pipeline's own division of labor, not a developer-stage check.
- **The oracle suite's case 6 (CI coverage) tolerance is a wide floor (>=0.88), not a tight band
  around 95%.** Measured coverage at the pinned seed is ~0.93; a floor of 0.88 comfortably absorbs
  normal Monte Carlo noise at 400 replications while still catching a genuinely broken CI (which
  would show coverage far lower, e.g. 50-70%). This is a deliberate, documented tolerance choice
  (spec Sec6 case 6 only requires "≈ 95% within tolerance", not an exact value), not a defect.
- **One implementation bug was found and fixed during this session's own verification, not left
  for review**: the oracle suite's runtime-budget guard fixture originally captured its start time
  at MODULE IMPORT (pytest's collection phase), which — when the file runs as part of the FULL
  backend suite rather than in isolation — wrongly counted every OTHER test file's collection and
  execution time against the 120s budget, causing a spurious teardown failure. Fixed by moving the
  `time.perf_counter()` capture into the fixture's own setup (before `yield`), which pytest
  evaluates lazily right before the first test in that module runs. Re-verified: the full suite
  now reports 0 errors / 0 failures with this file included. This is disclosed here per the
  agent's "Known Issues -- be honest" instruction, even though it was self-caught and fixed, since
  a reviewer should be aware the budget-guard design had this subtlety.
- **Performance fast-path in `permutation_test`'s seeded-draw branch.** For the common `n1==1` or
  `n2==1` shapes (which dominate the oracle suite's own size/power generators, and are also the
  realistic shape for estimand A/C with a single occurrence vs several ToD-matched anchors), the
  function bypasses the general Fisher-Yates loop with a direct `rng.randrange(n)` call —
  mathematically proven equivalent in distribution (not merely "close enough") to the general
  algorithm for those two cases, verified by an exact p-value match against the general-path
  implementation during development. This is documented inline in the function body and is a pure
  performance optimization with zero behavior change; the general (non-fast-path) branch is still
  exercised whenever `n1 > 1` and `n2 > 1` (e.g. `test_referee_stats.py`'s TC-5 fixture uses
  n1=n2=3).
