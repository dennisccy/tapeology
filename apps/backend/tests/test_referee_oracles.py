"""``referee_stats.py`` (Era 6 "The Referee", J-03) — the seeded oracle suite, per
``docs/referee-statistical-spec.md`` Sec6. Test-first contract: TC-8 through TC-15, TC-18 in
``docs/phases/goal-referee-iter-3.md``. This suite, not any fixture-only unit test, IS the
acceptance for the statistics core (goal.md's own J-03 Acceptance sentence: "fixture-only tests
prove nothing at small n").

**What makes this an oracle, not a fixture test.** Every case below runs ``REFEREE_ORACLE_
REPLICATIONS`` (400) independent simulated datasets through the module under test and checks a
LONG-RUN, KNOWN-BY-CONSTRUCTION property of the resulting empirical rejection rate (or coverage
rate) — never a single hand-typed input/output pair. The data GENERATORS below are written from
scratch in this file (seeded ``random.Random`` instances distinct from ``referee_stream`` — this
is TEST DATA GENERATION, not a referee statistical draw), and the DEMONSTRATED-FAILURE foils
(case 3's unclustered pooled foil, the sign-flip-as-decision misuse, the mutation fixture) are
each independently implemented HERE, never by calling into `referee_stats.py`'s own primary-test
code path with a flag flipped — so a bug in the primary implementation could not accidentally also
break its own foil in a way that hides the intended demonstrated failure.

**Runtime budget (TC-18).** ``_oracle_suite_budget_guard`` below is a module-scoped, autouse
fixture whose teardown (running once, after every test in this file has completed) asserts the
WHOLE FILE's cumulative wall-clock time is <= ``REFEREE_ORACLE_BUDGET_SECONDS`` — the
``test_dense_replay_gate.py::test_unpaced_replay_within_config_time_budget`` self-timing pattern,
applied at file scope instead of a single call.

**Case-to-test mapping (spec Sec6):**
  1. Size, iid skewed (lognormal-shifted-to-zero-mean, n_s=1, K=4)      -> TC-8
  2. Size, heavy-tailed (Student-t(3))                                  -> TC-9
  3a. The unclustered pooled-label permutation foil over-rejects        -> TC-10
  3b. The session-level sign-flip mis-sizes on a skewed unequal case    -> TC-11
  4. Power at a +0.5*sd shift, S=40                                     -> TC-12
  5. The 20-null + 1-positive BH sweep                                  -> TC-13
  6. CI coverage at S=40, and the S=6 insufficient_sample case          -> TC-14
  Mutation fixture (a mis-implemented test statistic fails calibration) -> TC-15

**iter-4 additions** (``docs/phases/goal-referee-iter-4.md`` — its OWN, separate TC-numbering;
every iter-4 test below is explicitly labeled "iter-4" to avoid ambiguity with the iter-3 TC
numbers above). Closes the exact coverage hole ``lessons.md``'s iter-3 entry names: every case
above uses S>=16 sessions, so the deterministic ENUMERATION branch (the one this iteration's own
floor-violation fix touches) is NEVER exercised anywhere in this suite before iter-4:
  iter-4 TC-3. A calibration case small enough to genuinely enter the enumeration branch on
               every replication — checked for calibration AND the exact-mode floor property.
  iter-4 TC-4. A SECOND mutation fixture, independently reproducing the PRE-FIX subtraction bug
               (the anti-conservative direction — makes results look MORE significant than
               warranted) — paired with the existing TC-15 mutant (which fails in the OVER-
               cautious direction, always p=1.0) to prove this suite catches BOTH directions.
"""

from __future__ import annotations

import itertools
import math
import random
import time

import pytest

from app.research.referee_stats import (
    REFEREE_ORACLE_B,
    REFEREE_ORACLE_REPLICATIONS,
    REFEREE_ORACLE_SIZE_TOLERANCE,
    REFEREE_ORACLE_BUDGET_SECONDS,
    _informative_sessions,
    _is_extreme,
    _t_statistic,
    benjamini_hochberg,
    bootstrap_ci_cluster,
    permutation_test,
    sign_flip_result,
)

ALPHA = 0.05
_TOLERANCE_LOW, _TOLERANCE_HIGH = REFEREE_ORACLE_SIZE_TOLERANCE


@pytest.fixture(scope="module", autouse=True)
def _oracle_suite_budget_guard():
    """TC-18: this FILE's own cumulative wall-clock time -- from the first test's setup through
    the last test's teardown -- must not exceed ``REFEREE_ORACLE_BUDGET_SECONDS``. The start time
    is captured HERE (in the fixture's own setup, before ``yield``), not at module import: a
    module-scoped fixture's setup runs lazily, right before the first test in THIS module that
    needs it -- never at collection time. Timing from module import instead would wrongly charge
    this budget for however long pytest spent collecting/running every OTHER file first when this
    suite runs as part of the full backend suite rather than in isolation (the bug an earlier
    version of this fixture had: it captured ``_SUITE_START`` as a module-level assignment,
    evaluated at import/collection time)."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    assert elapsed <= REFEREE_ORACLE_BUDGET_SECONDS, (
        f"the oracle suite took {elapsed:.1f}s, over its {REFEREE_ORACLE_BUDGET_SECONDS}s budget"
    )


# === Data generators (test infrastructure -- seeded, but NOT `referee_stream`-scoped; these build
# synthetic INPUT datasets fed into the module under test, never a referee statistical draw) =========


def _lognormal_shifted_to_zero_mean(rng: random.Random, mu: float = 0.0, sigma: float = 1.0) -> float:
    """A lognormal draw re-centered to mean zero: ``lognormvariate(mu, sigma) - E[lognormal]``,
    ``E[lognormal] = exp(mu + sigma**2/2)`` (the closed-form lognormal mean). Right-skewed."""
    return rng.lognormvariate(mu, sigma) - math.exp(mu + sigma**2 / 2.0)


def _student_t(rng: random.Random, df: int = 3) -> float:
    """A Student-t(df) draw via the standard normal-over-sqrt(chi-square/df) construction, using
    only stdlib `random.gauss`/`random.gammavariate` (chi-square(df) == gamma(df/2, scale=2)) --
    heavy-tailed, mean zero for df > 1."""
    z = rng.gauss(0.0, 1.0)
    chi2 = rng.gammavariate(df / 2.0, 2.0)
    return z / math.sqrt(chi2 / df)


def _iid_session_groups(rng, s, n1, k, generator, mean1=0.0, mean2=0.0):
    """``s`` sessions, each an INDEPENDENT draw (no shared per-session structure): ``n1`` group1
    values and ``k`` group2 values, ``generator(rng) + mean`` per value."""
    sg = {}
    for i in range(s):
        g1 = [mean1 + generator(rng) for _ in range(n1)]
        g2 = [mean2 + generator(rng) for _ in range(k)]
        sg[f"s{i:04d}"] = (g1, g2)
    return sg


def _regime_clustered_session_groups(rng, s, n1, n2, regime_sd, noise_sd):
    """``s`` sessions; EACH session draws its own ``regime_s ~ N(0, regime_sd)`` shared by BOTH
    groups equally (so it cancels exactly in the within-session ``delta_s`` -- keeping the PRIMARY
    within-session test calibrated), plus independent per-value Gaussian noise. A pure null (no
    population-level mean difference either way) -- the "shared per-session regime shifts" the
    spec's case 3 names."""
    sg = {}
    for i in range(s):
        regime = rng.gauss(0.0, regime_sd)
        g1 = [regime + rng.gauss(0.0, noise_sd) for _ in range(n1)]
        g2 = [regime + rng.gauss(0.0, noise_sd) for _ in range(n2)]
        sg[f"s{i:04d}"] = (g1, g2)
    return sg


def _empirical_rejection_rate(p_values: list[float], alpha: float = ALPHA) -> float:
    return sum(1 for p in p_values if p <= alpha) / len(p_values)


# === Case 1 (TC-8): size, iid skewed (lognormal-shifted-to-zero-mean, n_s=1, K=4) ====================


def test_oracle_case1_size_iid_skewed_lognormal_holds_calibration():
    """TC-8: 400 independent seeded replications, each S=16 sessions of n_s=1/K=4
    lognormal-shifted-to-zero-mean occurrence/anchor values (a pure null: both groups drawn from
    the identical zero-mean generator, independently -- no true effect). The empirical rejection
    rate at alpha=0.05 must fall inside ``REFEREE_ORACLE_SIZE_TOLERANCE``."""
    gen_rng = random.Random("oracle-case1-lognormal-seed")
    p_values = []
    for rep in range(REFEREE_ORACLE_REPLICATIONS):
        sg = _iid_session_groups(gen_rng, 16, 1, 4, _lognormal_shifted_to_zero_mean)
        result = permutation_test(sg, f"oracle-case1-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
        p_values.append(result["p"])
    rate = _empirical_rejection_rate(p_values)
    assert _TOLERANCE_LOW <= rate <= _TOLERANCE_HIGH, (
        f"case 1 (iid skewed) rejection rate {rate:.4f} outside "
        f"[{_TOLERANCE_LOW}, {_TOLERANCE_HIGH}]"
    )


# === Case 2 (TC-9): size, heavy-tailed (Student-t(3)) =================================================


def test_oracle_case2_size_heavy_tailed_student_t_holds_calibration():
    """TC-9: identical structure to case 1, generator swapped for Student-t(3) (heavy-tailed, mean
    zero)."""
    gen_rng = random.Random("oracle-case2-student-t-seed")
    p_values = []
    for rep in range(REFEREE_ORACLE_REPLICATIONS):
        sg = _iid_session_groups(gen_rng, 16, 1, 4, _student_t)
        result = permutation_test(sg, f"oracle-case2-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
        p_values.append(result["p"])
    rate = _empirical_rejection_rate(p_values)
    assert _TOLERANCE_LOW <= rate <= _TOLERANCE_HIGH, (
        f"case 2 (heavy-tailed) rejection rate {rate:.4f} outside "
        f"[{_TOLERANCE_LOW}, {_TOLERANCE_HIGH}]"
    )


# === Case 3a (TC-10): the unclustered pooled-label permutation foil over-rejects =====================


def _unclustered_pseudoreplicated_foil_p(
    session_groups: dict[str, tuple[list[float], list[float]]], seed: str, b: int
) -> float:
    """The DEMONSTRATED WRONG procedure (spec Sec6 case 3a), implemented independently of
    ``permutation_test`` (never calls it, never imports its internals): the classic
    pseudo-replication mistake. For EVERY session, compute ALL pairwise (occurrence - anchor)
    differences (``n_s * K_s`` of them, ALL sharing that session's regime shock -- heavily
    correlated); pool these pairwise differences across EVERY session as if they were independent
    draws; test whether the pooled mean differs from zero via a naive sign-flip permutation over
    the POOLED, UNCLUSTERED set. This ignores that entire blocks of pooled differences move
    together (one shared per-session regime draw), understating the true variance and
    over-rejecting."""
    pooled_diffs: list[float] = []
    for group1, group2 in session_groups.values():
        for occurrence in group1:
            for anchor in group2:
                pooled_diffs.append(occurrence - anchor)
    n = len(pooled_diffs)
    t_obs = sum(pooled_diffs) / n
    rng = random.Random(seed)
    extreme = 0
    for _ in range(b):
        acc = 0.0
        for diff in pooled_diffs:
            acc += diff if rng.random() < 0.5 else -diff
        if (acc / n) >= t_obs:
            extreme += 1
    return (1 + extreme) / (b + 1)


def test_oracle_case3a_unclustered_foil_over_rejects_while_primary_holds_size():
    """TC-10: a session-clustered null (shared per-session regime, cancelling exactly within each
    session's own delta_s -- the primary test's own within-session pairing handles it correctly).
    The PRIMARY test must hold size; the UNCLUSTERED pseudo-replicated foil, run on the IDENTICAL
    400 datasets, must over-reject (rate ABOVE the tolerance band's ceiling) -- the recorded
    evidence for why within-session permutation is the primary test."""
    gen_rng = random.Random("oracle-case3a-regime-seed")
    primary_p_values = []
    foil_p_values = []
    for rep in range(REFEREE_ORACLE_REPLICATIONS):
        sg = _regime_clustered_session_groups(gen_rng, 20, 3, 3, regime_sd=2.0, noise_sd=0.3)
        primary = permutation_test(sg, f"oracle-case3a-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
        primary_p_values.append(primary["p"])
        foil_p_values.append(
            _unclustered_pseudoreplicated_foil_p(sg, f"oracle-case3a-foil-{rep}", b=REFEREE_ORACLE_B)
        )

    primary_rate = _empirical_rejection_rate(primary_p_values)
    foil_rate = _empirical_rejection_rate(foil_p_values)

    assert _TOLERANCE_LOW <= primary_rate <= _TOLERANCE_HIGH, (
        f"the PRIMARY within-session test should hold size on the clustered null; got "
        f"{primary_rate:.4f}"
    )
    assert foil_rate > _TOLERANCE_HIGH, (
        f"the unclustered foil should OVER-reject (> {_TOLERANCE_HIGH}); got {foil_rate:.4f} -- "
        "the demonstrated failure did not manifest"
    )


# === Case 3b (TC-11): the session-level sign-flip mis-sizes on a skewed n_s=1/K=3 case ================


def test_oracle_case3b_sign_flip_mis_sizes_while_primary_holds_size():
    """TC-11: a skewed (lognormal, sigma=2.0), unequal-group (n_s=1, K=3) one-sided fixture. The
    session-level sign-flip variant, run AS IF it were the decision rule, must fall OUTSIDE the
    tolerance band (mis-sized); the true within-session permutation, on the SAME 400 datasets in
    the SAME test run, must hold size (inside the band)."""
    gen_rng = random.Random("oracle-case3b-skew-seed")
    primary_p_values = []
    flip_p_values = []
    for rep in range(REFEREE_ORACLE_REPLICATIONS):
        sg = _iid_session_groups(
            gen_rng, 16, 1, 3, lambda r: _lognormal_shifted_to_zero_mean(r, 0.0, 2.0)
        )
        primary = permutation_test(sg, f"oracle-case3b-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
        primary_p_values.append(primary["p"])
        flip = sign_flip_result(sg, f"oracle-case3b-flip-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
        flip_p_values.append(flip["p"])

    primary_rate = _empirical_rejection_rate(primary_p_values)
    flip_rate = _empirical_rejection_rate(flip_p_values)

    assert _TOLERANCE_LOW <= primary_rate <= _TOLERANCE_HIGH, (
        f"the PRIMARY within-session permutation should hold size; got {primary_rate:.4f}"
    )
    assert not (_TOLERANCE_LOW <= flip_rate <= _TOLERANCE_HIGH), (
        f"the sign-flip variant should MIS-SIZE (fall outside "
        f"[{_TOLERANCE_LOW}, {_TOLERANCE_HIGH}]) on this skewed unequal-group case; got "
        f"{flip_rate:.4f} -- the demonstrated failure did not manifest"
    )


# === Case 4 (TC-12): power at a +0.5*sd location shift, S=40 ==========================================

# Captured from THIS build via the exact generator/seed below (a pinned golden, not a gate --
# spec Sec6 case 4: "rejection rate reported and pinned as a golden"). Reproducing this file's own
# generator with the SAME seed and SAME REFEREE_ORACLE_B/REFEREE_ORACLE_REPLICATIONS values always
# reproduces this exact number (fully seeded, zero wall-clock dependence).
_CASE4_POWER_GOLDEN = 0.8950
_CASE4_POWER_TOLERANCE = 0.05


def test_oracle_case4_power_at_half_sd_shift_matches_the_pinned_golden():
    """TC-12: a +0.5*sd location shift (occurrence mean 0.5, anchor mean 0.0, both sd=1.0) at
    S=40 informative sessions (n_s=1, K=4) -- the reported rejection rate must match the pinned
    golden within its stated tolerance."""
    gen_rng = random.Random("oracle-case4-power-seed")
    p_values = []
    for rep in range(REFEREE_ORACLE_REPLICATIONS):
        sg = _iid_session_groups(gen_rng, 40, 1, 4, lambda r: r.gauss(0.0, 1.0), mean1=0.5, mean2=0.0)
        result = permutation_test(sg, f"oracle-case4-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
        p_values.append(result["p"])
    rate = _empirical_rejection_rate(p_values)
    assert abs(rate - _CASE4_POWER_GOLDEN) <= _CASE4_POWER_TOLERANCE, (
        f"case 4 power {rate:.4f} does not match the pinned golden "
        f"{_CASE4_POWER_GOLDEN} within {_CASE4_POWER_TOLERANCE}"
    )
    # A meaningful power golden: comfortably above alpha AND well below certainty (a real,
    # informative power figure, not a degenerate 0 or 1).
    assert 0.5 < rate < 1.0


# === Case 5 (TC-13): the 20-null + 1-positive BH sweep =================================================

_CASE5_N_NULL = 20
_CASE5_SESSIONS_PER_HYPOTHESIS = 10
_CASE5_Q = 0.10
# Pinned goldens (captured from THIS build's own seeded run, spec Sec6 case 5: "matching the
# pinned golden"). The false-admission rate is a per-null-CANDIDATE rate across all
# REFEREE_ORACLE_REPLICATIONS * 20 null opportunities; the positive-admission rate is a
# per-REPLICATION rate.
_CASE5_FALSE_ADMISSION_GOLDEN = 0.0114
_CASE5_FALSE_ADMISSION_TOLERANCE = 0.03
_CASE5_POSITIVE_ADMITTED_GOLDEN = 0.9375
_CASE5_POSITIVE_ADMITTED_TOLERANCE = 0.10


def _case5_hypothesis_session_groups(rng, mean1):
    return _iid_session_groups(
        rng, _CASE5_SESSIONS_PER_HYPOTHESIS, 1, 4, lambda r: r.gauss(0.0, 1.0), mean1=mean1
    )


def test_oracle_case5_bh_sweep_admits_the_positive_and_controls_false_admissions():
    """TC-13: per replication, 20 known-null candidates (no true shift) plus 1 known-positive
    candidate (a strong +1.5 shift, needed for power at this case's deliberately small
    per-hypothesis S=10) are each evaluated through the primary permutation test, then BH at
    q=0.10 is applied to the family's m=21 checkpoint p-values. Across
    REFEREE_ORACLE_REPLICATIONS replications: the false-admission rate (fraction of the 20*400
    known-null opportunities that BH corroborates) stays within its binomial tolerance band of the
    pinned golden, and the known-positive is admitted in the large majority of replications,
    matching its own pinned golden."""
    gen_rng = random.Random("oracle-case5-bh-sweep-seed")
    false_admissions = 0
    total_null_opportunities = 0
    positive_admitted = 0
    for rep in range(REFEREE_ORACLE_REPLICATIONS):
        p_values = []
        for null_idx in range(_CASE5_N_NULL):
            sg = _case5_hypothesis_session_groups(gen_rng, mean1=0.0)
            result = permutation_test(
                sg, f"oracle-case5-null-{rep}-{null_idx}", sidedness="greater", b=REFEREE_ORACLE_B
            )
            p_values.append(result["p"])
        sg_positive = _case5_hypothesis_session_groups(gen_rng, mean1=1.5)
        positive_result = permutation_test(
            sg_positive, f"oracle-case5-positive-{rep}", sidedness="greater", b=REFEREE_ORACLE_B
        )
        p_values.append(positive_result["p"])

        bh = benjamini_hochberg(p_values, q=_CASE5_Q)
        assert bh["m"] == _CASE5_N_NULL + 1
        false_admissions += sum(1 for i in range(_CASE5_N_NULL) if bh["bh_pass"][i])
        total_null_opportunities += _CASE5_N_NULL
        if bh["bh_pass"][_CASE5_N_NULL]:
            positive_admitted += 1

    false_admission_rate = false_admissions / total_null_opportunities
    positive_admitted_rate = positive_admitted / REFEREE_ORACLE_REPLICATIONS

    assert false_admission_rate <= _CASE5_Q, (
        f"false-admission rate {false_admission_rate:.4f} exceeds the family q={_CASE5_Q}"
    )
    assert abs(false_admission_rate - _CASE5_FALSE_ADMISSION_GOLDEN) <= _CASE5_FALSE_ADMISSION_TOLERANCE
    assert positive_admitted_rate > 0.5, (
        f"the known-positive should be admitted in the LARGE MAJORITY of replications; got "
        f"{positive_admitted_rate:.4f}"
    )
    assert (
        abs(positive_admitted_rate - _CASE5_POSITIVE_ADMITTED_GOLDEN)
        <= _CASE5_POSITIVE_ADMITTED_TOLERANCE
    )


# === Case 6 (TC-14): CI coverage at S=40, and the S=6 insufficient_sample case ========================

_CASE6_TRUE_EFFECT = 0.3
_CASE6_COVERAGE_FLOOR = 0.88  # a wide but meaningful floor around the target 95% (400 reps' own
# binomial noise at ~93-95% observed coverage; a badly miscalibrated CI would show coverage far
# below this, e.g. 50-70%).


def test_oracle_case6_clustered_ci_covers_the_true_effect_at_s40():
    """TC-14 (S=40 half): 400 replications, each S=40 sessions (n_s=1, K=4) with a KNOWN true
    session-mean effect (occurrence mean 0.3, anchor mean 0.0). The fraction of replications whose
    clustered percentile CI contains the true effect (0.3) must be close to the nominal 95% level
    (within a wide, meaningful tolerance -- a genuinely broken CI would show coverage far below
    this floor, not a few points under 95%)."""
    gen_rng = random.Random("oracle-case6-coverage-seed")
    covered = 0
    for rep in range(REFEREE_ORACLE_REPLICATIONS):
        sg = _iid_session_groups(
            gen_rng, 40, 1, 4, lambda r: r.gauss(0.0, 1.0), mean1=_CASE6_TRUE_EFFECT, mean2=0.0
        )
        ci = bootstrap_ci_cluster(sg, f"oracle-case6-{rep}", b=REFEREE_ORACLE_B)
        assert ci["state"] == "ok"
        if ci["ci_low"] <= _CASE6_TRUE_EFFECT <= ci["ci_high"]:
            covered += 1
    coverage_rate = covered / REFEREE_ORACLE_REPLICATIONS
    assert coverage_rate >= _CASE6_COVERAGE_FLOOR, (
        f"clustered CI coverage {coverage_rate:.4f} below the {_CASE6_COVERAGE_FLOOR} floor"
    )
    assert coverage_rate <= 1.0


def test_oracle_case6_clustered_ci_below_the_floor_serves_insufficient_sample():
    """TC-14 (S=6 half): the identical call shape at S=6 (below REFEREE_MIN_CLUSTERS_FOR_CI=8)
    instead returns the literal `insufficient_sample` state, never a fabricated interval."""
    rng = random.Random("oracle-case6-s6-seed")
    sg = _iid_session_groups(rng, 6, 1, 4, lambda r: r.gauss(0.0, 1.0), mean1=_CASE6_TRUE_EFFECT)
    ci = bootstrap_ci_cluster(sg, "oracle-case6-s6", b=200)
    assert ci["state"] == "insufficient_sample"
    assert ci["n_clusters"] == 6


# === iter-4 TC-3: a calibration case that genuinely ENTERS the enumeration branch ====================
#
# Every case above uses S>=16 sessions of shape n_s=1/K=4 (space per session = C(5,1) = 5;
# 5**16 is astronomically over REFEREE_ENUMERATION_THRESHOLD), so `permutation_test`'s
# deterministic `use_enumeration` path -- the ONE branch this iteration's own floor-violation fix
# touches -- is NEVER exercised anywhere in this suite before this case. S=5 (same n1=1, K=4 shape,
# same generator style as cases 1/2) keeps every replication's space at 5**5 == 3,125, comfortably
# under the 8,192 threshold, so every one of REFEREE_ORACLE_REPLICATIONS runs full enumeration.

_CASE_ENUM_SESSIONS = 5
_CASE_ENUM_N1 = 1
_CASE_ENUM_K = 4


def test_oracle_iter4_tc3_enumeration_branch_holds_calibration_and_the_exact_floor():
    """iter-4 TC-3: a pure null (both groups drawn from the SAME zero-mean generator,
    independently -- no true effect) at S small enough to force full enumeration on EVERY
    replication. Checks BOTH the calibration property every other case in this file checks
    (empirical rejection rate inside REFEREE_ORACLE_SIZE_TOLERANCE) AND the exact-mode floor
    property this whole iteration exists to guarantee (no single replication's `p` below its own
    `2 / (draws_used + 1)` floor) -- now proven inside the oracle suite itself, not only the
    fixture-level property test in `test_referee_stats.py` (goal.md's own J-03 acceptance: "the
    oracle suite IS the acceptance")."""
    gen_rng = random.Random("oracle-case-enum-branch-seed")
    p_values = []
    for rep in range(REFEREE_ORACLE_REPLICATIONS):
        sg = _iid_session_groups(
            gen_rng, _CASE_ENUM_SESSIONS, _CASE_ENUM_N1, _CASE_ENUM_K, lambda r: r.gauss(0.0, 1.0)
        )
        result = permutation_test(
            sg, f"oracle-case-enum-{rep}", sidedness="greater", b=REFEREE_ORACLE_B
        )
        assert result["enumeration"] is True, (
            f"replication {rep} did not enter the enumeration branch -- this case's own space "
            f"bound is wrong"
        )
        floor = 2.0 / (result["draws_used"] + 1)
        assert result["p"] >= floor, (
            f"replication {rep}: p={result['p']!r} fell below its own exact-mode floor {floor!r}"
        )
        p_values.append(result["p"])
    rate = _empirical_rejection_rate(p_values)
    assert _TOLERANCE_LOW <= rate <= _TOLERANCE_HIGH, (
        f"the enumeration-branch calibration case's rejection rate {rate:.4f} outside "
        f"[{_TOLERANCE_LOW}, {_TOLERANCE_HIGH}]"
    )


# === Mutation fixture (TC-15): a deliberately mis-implemented test statistic fails calibration =======


def _mutant_permutation_p_ignores_the_permutation(
    session_groups: dict[str, tuple[list[float], list[float]]], b: int, sidedness: str = "greater"
) -> float:
    """The mutation fixture: a REALISTIC implementation bug distinct from both case 3a (unclustered
    pooling) and case 3b (sign-flip-as-decision) -- the permuted label indices are drawn (the
    stream IS advanced, matching real code that "looks right" at a glance) but the recomputed
    statistic accidentally reuses the ORIGINAL (unpermuted) per-session deltas every single draw --
    a classic "forgot to apply the draw's own result" bug. Every T* therefore equals T_obs exactly,
    so p = (1 + b) / (b + 1) = 1.0 on every call, regardless of the data -- the empirical rejection
    rate is 0.0, always, deterministically outside the tolerance band's floor."""
    informative = _informative_sessions(session_groups)
    t_obs, deltas, weights = _t_statistic(informative)
    total_weight = sum(weights.values())
    rng = random.Random("mutant-stream-advances-but-is-never-read")
    extreme = 0
    for _ in range(b):
        rng.random()  # the stream IS advanced, mimicking real (buggy) code that looks plausible
        t_star = sum(weights[s] * deltas[s] for s in deltas) / total_weight  # BUG: == t_obs, always
        if _is_extreme(t_star, t_obs, sidedness):
            extreme += 1
    return (1 + extreme) / (b + 1)


def test_mutation_fixture_fails_calibration():
    """TC-15: the deliberately mis-implemented test statistic above, substituted into case 1's own
    null-calibration generator/seed, must fail calibration -- its empirical rejection rate falls
    OUTSIDE the tolerance band (in fact at exactly 0.0, since every mutant p equals 1.0 by
    construction) -- proving this suite would catch a wrong implementation."""
    gen_rng = random.Random("oracle-case1-lognormal-seed")  # the SAME generator/seed as case 1
    p_values = []
    for _rep in range(REFEREE_ORACLE_REPLICATIONS):
        sg = _iid_session_groups(gen_rng, 16, 1, 4, _lognormal_shifted_to_zero_mean)
        p_values.append(_mutant_permutation_p_ignores_the_permutation(sg, b=REFEREE_ORACLE_B))
    rate = _empirical_rejection_rate(p_values)
    assert rate == 0.0
    assert not (_TOLERANCE_LOW <= rate <= _TOLERANCE_HIGH), (
        f"the mutant should FAIL calibration (fall outside "
        f"[{_TOLERANCE_LOW}, {_TOLERANCE_HIGH}]); got {rate:.4f}"
    )


# === iter-4 TC-4: a SECOND mutation fixture -- the PRE-FIX subtraction bug, ANTI-conservative =========
#
# TC-15 above demonstrates the OVER-cautious direction (a mutant that always reports p=1.0 --
# never significant, never dangerous). This case demonstrates the OPPOSITE, ANTI-conservative
# direction: a mutant that can make a result look MORE significant than it legitimately is -- the
# actual PRE-FIX shipped defect this iteration's own fix corrects (`permutation_test`'s exact-
# enumeration branch computing group-2's sum by subtracting from a separately-accumulated session
# total instead of a direct accumulation over the complement). Reproduced independently HERE
# (never by calling into `referee_stats.py`'s own enumeration code path with a flag flipped -- this
# file's own stated convention), reusing only the UNCHANGED, non-buggy `_t_statistic`/`_is_extreme`/
# `_informative_sessions` helpers exactly as the existing TC-15 mutant above already does.


def _prefix_bug_enumeration_p(
    session_groups: dict[str, tuple[list[float], list[float]]], sidedness: str
) -> tuple[float, int]:
    """Independent reproduction of the ACTUAL pre-iter-4 shipped defect: each enumerated
    combination's group-2 sum computed as `total - g1_sum` (a separately `math.fsum`-accumulated
    session total, minus the combination's own g1_sum) instead of a direct accumulation over the
    combination's own complement values -- the exact bug `permutation_test`'s own inline comment
    now documents. Returns `(p, draws_used)`."""
    informative = _informative_sessions(session_groups)
    t_obs, deltas, weights = _t_statistic(informative)
    total_weight = math.fsum(weights.values())
    sessions = sorted(informative)
    combos_by_session = []
    for session in sessions:
        group1, group2 = informative[session]
        values = group1 + group2
        n1 = len(group1)
        total = math.fsum(values)  # the buggy separately-accumulated session total (PRE-FIX)
        combos_by_session.append(
            (values, n1, total, list(itertools.combinations(range(len(values)), n1)))
        )
    extreme = 0
    draws_used = 0
    for joint in itertools.product(*(c[3] for c in combos_by_session)):
        acc = 0.0
        for session, combo, (values, n1, total, _combos) in zip(sessions, joint, combos_by_session):
            g1_sum = math.fsum(values[idx] for idx in combo)
            g2_sum = total - g1_sum  # THE PRE-FIX BUG (never a direct complement accumulation)
            n2 = len(values) - n1
            delta_star = g1_sum / n1 - g2_sum / n2
            acc += weights[session] * delta_star
        t_star = acc / total_weight
        draws_used += 1
        if _is_extreme(t_star, t_obs, sidedness):
            extreme += 1
    return (1 + extreme) / (draws_used + 1), draws_used


def _small_enumeration_fixtures(rng, n_cases, max_sessions=4):
    """Freshly seeded-generated small enumeration-mode fixtures -- 2-vs-2, 1-vs-4, and 4-vs-1
    group shapes (matching the evaluator's own reproduction shapes, `test_referee_stats.py`'s
    iter-4 TC-2 property test's own design), 1 to `max_sessions` informative sessions, all three
    `sidedness` values. Independent of that file's own generator (this file's own "written from
    scratch HERE" convention) -- same design, separately seeded."""
    shapes = [(2, 2), (1, 4), (4, 1)]
    sidedness_values = ("greater", "less", "two-sided")
    for i in range(n_cases):
        n_sessions = rng.randint(1, max_sessions)
        n1, n2 = rng.choice(shapes)
        sidedness = rng.choice(sidedness_values)
        session_groups = {
            f"s{j:03d}": (
                [rng.gauss(0.0, 1.0) for _ in range(n1)],
                [rng.gauss(0.0, 1.0) for _ in range(n2)],
            )
            for j in range(n_sessions)
        }
        yield session_groups, sidedness


def test_oracle_iter4_tc4_the_anti_conservative_mutant_is_detected():
    """iter-4 TC-4: the pre-fix subtraction-bug mutant, run over a batch of freshly seeded small
    enumeration-mode fixtures (the SAME style TC-2's own property test in `test_referee_stats.py`
    uses), is DETECTED via at least one floor violation -- `p` falling below its own exact-mode
    floor `2 / (draws_used + 1)`, which can never legitimately happen (the observed grouping is
    always one guaranteed member of the enumerated space). Proves this suite catches an OVER-
    confident implementation bug, not only TC-15's existing over-cautious one. (Re-run against the
    FIXED `permutation_test` on the identical generator/seed as a sanity check during development:
    zero floor violations -- confirming this is a property of the MUTANT, not the fixture design.)
    """
    rng = random.Random("iter4-tc4-mutant-batch-seed-v1")
    violations = []
    for i, (session_groups, sidedness) in enumerate(_small_enumeration_fixtures(rng, n_cases=3000)):
        p, draws_used = _prefix_bug_enumeration_p(session_groups, sidedness)
        floor = 2.0 / (draws_used + 1)
        if p < floor:
            violations.append((i, p, floor))
    assert len(violations) >= 1, (
        "the anti-conservative mutant should produce at least one exact-mode floor violation "
        "across this batch -- none found, the mutant went undetected"
    )
