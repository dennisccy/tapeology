# goal-referee-iter-4 Dev Handoff

**Phase:** goal-referee-iter-4
**Date:** 2026-08-14
**Agent:** developer
**Status:** complete

## What Was Built

Target journey J-03 (a prior-iteration ESCALATE fix, not a new journey) plus one additive
disclosure riding along per the evaluator's own carry-forward instruction. Zero new routes, zero
new UI, zero new Config fields, zero new runtime dependency.

- **Fixed the exact-enumeration p-value floor bug in `permutation_test`**
  (`apps/backend/app/research/referee_stats.py`, inside the `if use_enumeration:` block). The
  bug: each enumerated combination's group-2 sum was computed as
  `g2_sum = total - g1_sum` (subtracting from a separately `math.fsum`-accumulated session
  total), while the OBSERVED statistic (`_t_statistic`) computes group-2's sum via a direct
  `math.fsum(group2)`. Both are independently correctly-rounded results, but their difference is
  not guaranteed to equal a third independently-rounded sum — so for the TRUE observed grouping
  (which must always legitimately count as "at least as extreme as itself" in exact-enumeration
  mode), the two computations could disagree in the last representable digit, letting the
  self-comparison narrowly fail and silently drop the observed grouping from the extreme count.
  Consequence: the returned `p` could fall to HALF its own mathematical floor
  `2 / (draws_used + 1)`.
  - **Fix, part 1 (matches the plan's literal instruction):** each combination's group-2 sum is
    now a DIRECT `math.fsum` accumulation over that combination's own complement indices — never
    a subtraction from a separately-accumulated total.
  - **Fix, part 2 (an extension beyond the plan's literal text — see "Scope decision" below):**
    the per-session weighted-delta terms are now combined via `math.fsum` (matching
    `_t_statistic`'s own numerator computation) instead of the previous running `acc +=`. This
    was **empirically necessary**, not optional polish: fixing only part 1 still left ~7% of
    randomly-generated 3-to-5-session enumeration fixtures able to violate the floor (naive
    left-to-right addition is not guaranteed to reproduce `_t_statistic`'s own
    `math.fsum(...)`-based numerator even when every per-session term is itself bit-identical).
    With both parts applied, 20,000+ seeded property-test cases (spanning 1–5 sessions, three
    group shapes, three sidedness values) show zero floor violations.
  - The seeded (non-enumeration) `b`-draws branch's own analogous `g2_sum = total - g1_sum` is
    UNTOUCHED, exactly as the plan specifies (its floating-point disagreement is far below
    Monte-Carlo sampling error at `REFEREE_B` draws, and the `+1` convention never needs the
    observed grouping to bit-match itself there).
- **Re-pinned the oracle attestation and bumped `STATS_CORE_VERSION`** from `"referee-stats-v1"`
  to `"referee-stats-v2"` (a genuine algorithmic revision to the file, per the module's own
  documented policy). Re-ran `run_oracle_attestation()` against the FIXED code: the numeric
  values (`permutation_p`, `ci_low`, `ci_high`) are byte-identical to the pre-fix pin for this
  specific tiny 3-session attestation fixture — the floor-violation defect is empirically rare
  and this fixture's own data does not happen to trigger it — so only the version string moved.
  Documented explicitly in the module (this was re-verified by actually running the fixed build,
  never assumed unchanged).
- **Closed the oracle coverage hole** in `apps/backend/tests/test_referee_oracles.py`: every
  existing calibration case uses S>=16 sessions, so the deterministic enumeration branch was never
  exercised anywhere in the oracle suite before this iteration. Added a calibration case
  (S=5, n1=1, K=4 — same generator style as cases 1/2, small enough that every one of the 400
  replications genuinely enters full enumeration) checked for both calibration (empirical
  rejection rate inside `REFEREE_ORACLE_SIZE_TOLERANCE`) and the exact floor property on every
  single replication.
- **Added a second, paired mutation fixture** (the ANTI-conservative direction) to the oracle
  suite: an independent reproduction of the actual pre-fix subtraction bug, run against a batch of
  3,000 freshly seeded small-enumeration fixtures, detected via at least one floor violation —
  proving the suite catches an over-confident implementation bug, not only the existing
  over-cautious mutant (TC-15, which always reports p=1.0).
- **Closed two reviewer-flagged same-file test gaps** in `test_referee_stats.py`:
  - Direct coverage for `_draw_indices_without_replacement` (determinism under identical seeds;
    full-population coverage when `k == population`). The function itself is untouched — kept as
    the documented without-replacement primitive J-04's real anchor draws are expected to reuse.
  - The seeded branch's `n1 > 1, n2 == 1` fast path (`permutation_test`'s `elif n2 == 1` shortcut),
    verified via brute-force full enumeration as an independent ground truth, checked against
    both the module's own fast-path result and a from-scratch general-Fisher-Yates-algorithm
    reference (see "Design decision: TC-8" below for why a byte-identical draw-sequence match is
    mathematically impossible here, and what "matches" means instead).
- **Closed Lead 1** in `apps/backend/app/research/referee_evidence.py`, additive-only: one shared
  `_is_stale_basis(...)` predicate now implements the `(detector_basis, config_fingerprint)`
  staleness check both `playbook_occurrence_readiness()` and `playbook_observations()` previously
  implemented as two independent copies. Both functions now additionally serve
  `stale_basis_dates: [{"session_date", "record_detector_basis"}, ...]` — every date whose
  newest record's own basis/fingerprint doesn't match the live values, named explicitly instead
  of silently contributing zero. Zero change to any currently-served field's value; the list is
  empty (`[]`) on every fixture with no stale-basis record, including today's real corpus.
- Lead 2 (the strategy adapter's `epoch_anchor = dataset.get("epoch_anchor") or 0.0` fallback) was
  explicitly NOT touched, per the plan's own T-1 drop decision. Verified via `git diff`: zero
  lines changed in `_strategy_observation`, `strategy_observations`, or `edge_report.py`.

## Scope decision: extending the enumeration-branch fix beyond the plan's literal text

The plan's own instruction named only the `g2_sum` computation. Before implementing, I
empirically verified (a standalone script against the real, unmodified `_t_statistic`/
`_is_extreme` helpers, 20,000 seeded multi-session cases) that fixing `g2_sum` ALONE still left
1,424 of 20,000 cases (~7.1%) able to violate the floor — always at 3+ informative sessions, where
naive left-to-right `acc +=` summation is not guaranteed to reproduce `_t_statistic`'s own
`math.fsum`-based numerator, even when every per-session term is bit-identical. Adding the second
`math.fsum` (combining terms across sessions, matching `_t_statistic`'s own method) closed this to
zero violations across the same 20,000 cases, and across a further 5,000+ cases run through the
real fixed module directly.

I extended the fix to include this second change because:
1. It is empirically required for the DoD's own unconditional claim ("the returned p can never
   fall below the exact mode's own mathematical floor") to actually hold for realistic
   multi-session fixtures — not just the evaluator's own single-session minimal repro.
2. It is backed by the spec's own blanket rule (`docs/referee-statistical-spec.md`'s Determinism
   paragraph): "Persisted aggregate numbers use `math.fsum`-class accumulation, not
   platform/version-sensitive vectorized reductions."
3. It stays strictly inside the enumeration branch — zero diff to the seeded branch, to
   `_t_statistic`, or to the spec itself, matching every named guardrail.

This is disclosed here per the "be honest, don't hide extra fixes" principle. The full reasoning
and the empirical verification method are documented inline in `referee_stats.py`'s own comment
at the fix site.

## Design decision: TC-8 (the `n2 == 1` fast-path test)

The DoD asks for TC-8 to check the fast path's result "matches a from-scratch general-algorithm
reference." I verified empirically that a literal byte-for-byte match is mathematically
impossible to construct here: the fast path consumes exactly ONE `stream.randrange()` call per
draw, while the general Fisher-Yates algorithm consumes `n1` calls per draw — so even a reference
built from an IDENTICALLY-KEYED stream diverges from the module's own internal stream state after
the very first draw (confirmed: a same-keyed general-algorithm reference produces a materially
different `p`, 0.619 vs the module's own 0.524, on a test fixture). The two computations are
"equivalent in distribution" (the code's own inline comment), not identical in RNG consumption.

The test instead verifies the mathematically meaningful claim: both the module's own fast path
AND an independently-coded general-algorithm reference (its own, unrelated stream) are unbiased
Monte-Carlo estimators of the IDENTICAL exact target, computed via brute-force full enumeration
(deterministic, zero RNG) as ground truth. Both land within a wide, honestly-derived
(binomial-standard-error) tolerance of that ground truth — proven correct via a specific fixture
(S=7 sessions, n1=3/n2=1, B=8,000): ground truth p*=0.8522, fast path p=0.8543 (0.53 SE away),
general reference p=0.8473 (1.24 SE away), against a 6-SE tolerance.

## Files Changed

- `apps/backend/app/research/referee_stats.py` — the enumeration-branch fix (g2_sum direct
  accumulation + cross-session `math.fsum`), `STATS_CORE_VERSION` bump to `"referee-stats-v2"`,
  re-pinned attestation comment (values unchanged, re-verified honestly). Seeded branch
  byte-unchanged.
- `apps/backend/tests/test_referee_stats.py` — added: the exact minimal-repro regression test and
  a 3,000-case floor-guarantee property test (iter-4 TC-1/TC-2); direct coverage for
  `_draw_indices_without_replacement` (iter-4 TC-7); the `n2==1` fast-path ground-truth test
  (iter-4 TC-8); the version-bump + stale-version-rejection test (iter-4 TC-5/TC-6). Every
  pre-existing test's assertions are unchanged. New sections are explicitly labeled "iter-4" to
  avoid ambiguity with this file's own pre-existing iter-3 TC-numbering (iter-3's phase spec used
  TC-1 through TC-19 across this file, `test_referee_oracles.py`, and
  `test_referee_evidence.py`; iter-4's phase spec restarts its OWN TC-1 through TC-15 — the labels
  are per-spec-document, not globally unique, so every new section names its owning iteration).
- `apps/backend/tests/test_referee_oracles.py` — added: an enumeration-branch calibration case
  (iter-4 TC-3, S=5/n1=1/K=4) and a paired anti-conservative mutation fixture run against 3,000
  small-enumeration fixtures (iter-4 TC-4). Whole file: 83.3s, within the 120s budget (baseline
  was 78.2s; +5.1s added by these two cases).
- `apps/backend/app/research/referee_evidence.py` — additive-only: the shared `_is_stale_basis`
  predicate; `stale_basis_dates` added to both `playbook_occurrence_readiness()` and
  `playbook_observations()`'s return dicts; module docstring updated with a short Lead-1 section.
- `apps/backend/tests/test_referee_evidence.py` — extended the existing D3 stale-basis fixture
  test with the new `stale_basis_dates` assertion (iter-4 TC-9); added one new sibling test for
  `playbook_observations()` (iter-4 TC-10). Every other pre-existing assertion in this file is
  unchanged.
- `docs/handoffs/goal-referee-iter-4-dev.md` — this handoff.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/`
Result: **2504 passed, 8 skipped, 0 failed, 0 errors** in 257.0s — exceeds the required
`>= 2,495 pass / 8 skip` floor (iteration 3's own recorded floor plus this iteration's net +9
tests: +6 in `test_referee_stats.py`, +2 in `test_referee_oracles.py`, +1 in
`test_referee_evidence.py`). Exit code 0.

Targeted runs during development (all green):
- `tests/test_referee_stats.py`: 38 passed in 2.2s (was ~32 before this iteration's 6 new tests).
- `tests/test_referee_oracles.py`: 11 passed in 83.3s (was 9; budget 120s).
- `tests/test_referee_evidence.py`: 24 passed (was 23; 1 extended + 1 new).
- `tests/test_referee_guards.py`, `tests/test_copy_discipline.py`, `tests/test_mcp_server.py`: all
  green (import-ban guard unmodified-pass confirmed; `EXPECTED_TOOLS` still 20 entries).
- `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged).
- `import app.main` → clean (app import sanity, matching iter-3's own precedent for a
  backend-only, unconsumed-by-any-route iteration).
- `git diff --stat` against every named frozen module (`app/config.py`, `app/main.py`,
  `desk_playbook*.py`, `desk_forward.py`, `levels.py`, `tradability.py`, `setups.py`,
  `edge_report*.py`, `backtests.py`, `pnl_scan.py`, any route file,
  `docs/referee-statistical-spec.md`) → empty (zero diff, confirmed).
- `git status --porcelain` → exactly the 5 files this plan named, no store files, no `.env`, no
  secrets.

## Known Issues

- **No live browser verification performed this iteration, by design** — matching iter-3's own
  established precedent for the identical shape of iteration. Every target/rider item this
  iteration is backend-only and unconsumed by any route, page, or MCP tool
  (`referee_stats.py`/`referee_evidence.py`'s `stale_basis_dates` field remain unconsumed by any
  route wiring — J-09, several iterations away, is the first UI/route consumer). J-10's browser
  regression walk (cockpit, `/structure` AAPL Load, every shipped `/desk` section) is this
  iteration's Required-still-passing item but is a QA-stage responsibility per the pipeline's own
  division of labor, not a developer-stage check — no server was started, stopped, or restarted
  for this iteration (the pinned QA backend/frontend were left untouched).
- **The oracle suite's runtime grew from ~78.2s to ~83.3s** (the two new cases add ~5.1s combined:
  ~3.8s for the TC-3 calibration case at 400 replications of full enumeration, ~0.9s for the TC-4
  mutant-detection batch). Still comfortably inside the 120s `REFEREE_ORACLE_BUDGET_SECONDS`
  budget (~37s headroom), but later iterations (J-04+) that add their own oracle cases should be
  aware the margin is shrinking as this suite grows.
- **The re-pinned attestation's numeric values happen to be unchanged** by the fix (see "What Was
  Built" above) — this is an honest empirical fact about this one small fixture's specific data,
  not evidence the fix does nothing; the fix is independently proven by TC-1 (the evaluator's own
  minimal repro, `p` moves from `1/7` to `2/7`), TC-2 (3,000-case property test, zero violations),
  and TC-3/TC-4 (the oracle suite's own new enumeration-branch case and paired mutant).
- **TC-2's property test is capped at 1–4 informative sessions** (not the full evaluator-style
  1–5) purely for per-file runtime economy in `test_referee_stats.py` (a "fast, hand-derivable"
  test file by its own stated convention) — verified this cap still reliably catches the pre-fix
  bug (12 violations across 3,000 cases on the identical generator/seed, run against a faithful
  reproduction of the pre-fix code during development).
