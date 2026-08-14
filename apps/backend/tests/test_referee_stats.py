"""``referee_stats.py`` (Era 6 "The Referee", J-03) — the statistics core's own mechanics: fast,
deterministic, hand-derivable unit tests. Test-first contract: TC-1 through TC-7, TC-16, TC-17,
TC-19 in ``docs/phases/goal-referee-iter-3.md``. The CALIBRATION/oracle suite (TC-8 through
TC-15, TC-18 — the six spec Sec6 cases plus the mutation fixture, all seeded simulations that must
fit inside ``REFEREE_ORACLE_BUDGET_SECONDS``) lives separately in ``test_referee_oracles.py``, so
this file's own tests stay fast and this file never risks the runtime budget.

Every expected value below is derived independently of ``referee_stats.py``'s own implementation
-- either by literal hand arithmetic (documented inline) or by a from-scratch reference
computation written in this file using only ``random.Random``/``itertools``/plain arithmetic,
never by calling the module under test and pasting back what it printed."""

from __future__ import annotations

import ast
import inspect
import itertools
import math
import random

from app.research import referee_stats as rs
from app.research.referee_stats import (
    INSUFFICIENT_SAMPLE,
    REFEREE_B,
    REFEREE_CI_LEVEL,
    REFEREE_MIN_CLUSTERS_FOR_CI,
    REFEREE_SEED,
    benjamini_hochberg,
    bootstrap_ci_cluster,
    bootstrap_ci_occurrence,
    equal_weight_t,
    permutation_test,
    referee_stream,
    run_oracle_attestation,
    sign_flip_result,
    verify_oracle_attestation,
)

# === TC-1: the seeded stream constructor =============================================================


def test_referee_stream_is_deterministic_for_identical_arguments():
    """TC-1: two calls with an identical (hypothesis_id, purpose, session_date, i) tuple produce
    byte-identical `random.Random` draw sequences."""
    a = referee_stream("hyp-1", "perm", session_date="2026-06-08", i=3)
    b = referee_stream("hyp-1", "perm", session_date="2026-06-08", i=3)
    assert [a.random() for _ in range(10)] == [b.random() for _ in range(10)]


def test_referee_stream_differs_across_every_recipe_component():
    """Changing hypothesis_id, purpose, session_date, or i each mints a genuinely different
    stream -- the recipe's own namespacing is real, not decorative."""
    base = referee_stream("hyp-1", "perm", session_date="2026-06-08", i=1).random()
    variants = [
        referee_stream("hyp-2", "perm", session_date="2026-06-08", i=1).random(),
        referee_stream("hyp-1", "flip", session_date="2026-06-08", i=1).random(),
        referee_stream("hyp-1", "perm", session_date="2026-06-09", i=1).random(),
        referee_stream("hyp-1", "perm", session_date="2026-06-08", i=2).random(),
        referee_stream("hyp-1", "perm").random(),  # no session_date at all
    ]
    assert len({base, *variants}) == 1 + len(variants)  # all six draws are pairwise distinct


def test_referee_stream_recipe_matches_the_pinned_key_format():
    """The recipe is exactly `f"{REFEREE_SEED}:{hypothesis_id}:{purpose}[:{session_date}[:{i}]]"`
    (spec Sec1) -- verified by building the SAME key independently (plain string concatenation,
    not calling `referee_stream`) and confirming `random.Random` on that independently-built key
    reproduces the identical sequence `referee_stream` itself returns."""
    independently_built_key = f"{REFEREE_SEED}:hyp-x:boot-occ:2026-06-08:7"
    expected = random.Random(independently_built_key)
    actual = referee_stream("hyp-x", "boot-occ", session_date="2026-06-08", i=7)
    assert [expected.random() for _ in range(10)] == [actual.random() for _ in range(10)]


def test_referee_stream_rejects_i_without_session_date():
    try:
        referee_stream("hyp-1", "perm", i=3)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError: i requires session_date")


def test_referee_stream_rejects_an_unknown_purpose():
    try:
        referee_stream("hyp-1", "not-a-real-purpose")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError: unknown purpose")


def test_referee_stats_module_never_calls_random_sample_or_an_unseeded_random_instance():
    """TC-1's negative half, source-scanned (AST, not a regex a comment/string could
    false-positive): zero `random.sample(...)` calls, zero `random.Random()` calls with NO seed
    argument, and zero calls to the bare module-level `random.random`/`random.randrange`/
    `random.choice`/`random.choices` (which implicitly use Python's own hidden global RNG instance
    rather than a `referee_stream`-constructed one)."""
    tree = ast.parse(inspect.getsource(rs))
    banned_bare_random_functions = {"sample", "random", "randrange", "choice", "choices", "seed"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if func.value.id == "random" and func.attr in banned_bare_random_functions:
                    raise AssertionError(f"banned bare random.{func.attr}(...) call found")
                if func.value.id == "random" and func.attr == "Random":
                    if not node.args and not node.keywords:
                        raise AssertionError("random.Random() called with no seed argument")


# === TC-19: stdlib-only imports =======================================================================


def test_referee_stats_imports_only_stdlib_never_scipy_never_numpy():
    """TC-19: `referee_stats.py` imports only stdlib modules (itertools, math, random,
    statistics), never scipy, never numpy."""
    tree = ast.parse(inspect.getsource(rs))
    top_level_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level_modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top_level_modules.add(node.module.split(".")[0])
    # `__future__` is a language-syntax directive (`from __future__ import annotations`), not a
    # runtime dependency -- excluded from the "imports only stdlib compute modules" check below.
    top_level_modules.discard("__future__")
    assert top_level_modules == {"itertools", "math", "random", "statistics"}
    assert "numpy" not in top_level_modules
    assert "scipy" not in top_level_modules


# === TC-2: occurrence-level percentile bootstrap CI ===================================================


def test_bootstrap_ci_occurrence_on_identical_values_collapses_to_the_exact_point_hand_derived():
    """TC-2 (degenerate, fully hand-derivable fixture): every value in the fixture is IDENTICAL
    (4.0), so EVERY possible with-replacement resample also averages to EXACTLY 4.0 regardless of
    which indices are drawn or how many draws are made -- ci_low == ci_high == point_estimate ==
    4.0 is true by hand arithmetic alone, for ANY seed and ANY b."""
    values = [4.0] * 12
    result = bootstrap_ci_occurrence(values, "hyp-ci-degenerate", b=500)
    assert result == {
        "state": "ok",
        "n": 12,
        "point_estimate": 4.0,
        "ci_level": REFEREE_CI_LEVEL,
        "ci_low": 4.0,
        "ci_high": 4.0,
        "b": 500,
    }


def test_bootstrap_ci_occurrence_matches_an_independently_reimplemented_reference():
    """TC-2 (non-degenerate fixture): an INDEPENDENT reference implementation of the identical
    algorithm -- built from scratch in this test file using only `random.Random` and plain
    arithmetic, never calling any `referee_stats` resampling helper -- reproduces the module's own
    ci_low/ci_high exactly. Two independent implementations of a fully-specified deterministic
    algorithm agreeing is a stronger check than re-running the same code twice."""
    values = [1.0, 2.0, 3.0, 10.0, -1.0]
    hypothesis_id = "hyp-ci-reference"
    b = 300
    n = len(values)

    # The independent reference: the SAME key format, built by hand, and a hand-written
    # with-replacement resampling loop (not `_draw_indices_with_replacement`).
    key = f"{REFEREE_SEED}:{hypothesis_id}:boot-occ"
    ref_rng = random.Random(key)
    means = []
    for _ in range(b):
        resample = [values[ref_rng.randrange(n)] for _ in range(n)]
        means.append(sum(resample) / n)
    means.sort()
    lo_q = (1.0 - REFEREE_CI_LEVEL) / 2.0
    hi_q = 1.0 - lo_q

    def reference_percentile(sorted_vals, q):
        pos = q * (len(sorted_vals) - 1)
        lo = math.floor(pos)
        hi = math.ceil(pos)
        if lo == hi:
            return sorted_vals[int(pos)]
        frac = pos - lo
        return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac

    expected_ci_low = reference_percentile(means, lo_q)
    expected_ci_high = reference_percentile(means, hi_q)

    result = bootstrap_ci_occurrence(values, hypothesis_id, b=b)

    assert result["ci_low"] == expected_ci_low
    assert result["ci_high"] == expected_ci_high
    assert result["point_estimate"] == sum(values) / n


def test_bootstrap_ci_occurrence_reruns_are_byte_identical():
    values = [0.5, -0.2, 3.1, 4.4, -1.0, 2.2]
    a = bootstrap_ci_occurrence(values, "hyp-repro", b=200)
    b = bootstrap_ci_occurrence(values, "hyp-repro", b=200)
    assert a == b


def test_bootstrap_ci_occurrence_on_empty_values_is_insufficient_sample():
    assert bootstrap_ci_occurrence([], "hyp-empty")["state"] == INSUFFICIENT_SAMPLE


# === TC-3: the session-clustered CI floor ==============================================================


def _uniform_session_groups(n_sessions: int) -> dict[str, tuple[list[float], list[float]]]:
    return {
        f"2026-01-{i + 1:02d}": ([1.0 + 0.1 * i, 1.2 + 0.1 * i], [0.0, -0.1])
        for i in range(n_sessions)
    }


def test_bootstrap_ci_cluster_below_the_floor_is_insufficient_sample():
    """TC-3: fewer than REFEREE_MIN_CLUSTERS_FOR_CI (8) informative sessions -- the literal
    `insufficient_sample` state, never a fabricated interval."""
    sg = _uniform_session_groups(REFEREE_MIN_CLUSTERS_FOR_CI - 1)
    result = bootstrap_ci_cluster(sg, "hyp-cluster-floor", b=100)
    assert result == {
        "state": INSUFFICIENT_SAMPLE,
        "n_clusters": REFEREE_MIN_CLUSTERS_FOR_CI - 1,
        "min_clusters_required": REFEREE_MIN_CLUSTERS_FOR_CI,
    }


def test_bootstrap_ci_cluster_at_the_floor_returns_a_real_interval_and_mde():
    """TC-3: exactly REFEREE_MIN_CLUSTERS_FOR_CI (8) informative sessions crosses the floor -- a
    real interval and a positive MDE disclosure are served."""
    sg = _uniform_session_groups(REFEREE_MIN_CLUSTERS_FOR_CI)
    result = bootstrap_ci_cluster(sg, "hyp-cluster-at-floor", b=300)
    assert result["state"] == "ok"
    assert result["n_clusters"] == REFEREE_MIN_CLUSTERS_FOR_CI
    assert result["ci_low"] <= result["point_estimate"] <= result["ci_high"]
    assert result["mde"] > 0.0
    assert result["b"] == 300


def test_bootstrap_ci_cluster_one_group_sessions_are_excluded_from_the_cluster_count():
    """A session carrying only ONE of the two groups is not informative (spec Sec3.1/Sec3.2) and
    is excluded from `n_clusters` -- 7 two-group sessions plus 3 one-group sessions still reads as
    7 clusters, below the floor."""
    sg = _uniform_session_groups(7)
    sg["2026-02-01"] = ([1.0], [])  # group2 empty -- not informative
    sg["2026-02-02"] = ([], [1.0])  # group1 empty -- not informative
    result = bootstrap_ci_cluster(sg, "hyp-one-group", b=50)
    assert result["state"] == INSUFFICIENT_SAMPLE
    assert result["n_clusters"] == 7


# === TC-4: full enumeration on a tiny, hand-computed fixture ===========================================


def test_permutation_test_enumeration_matches_a_hand_computed_p_value():
    """TC-4: a single-session fixture -- occurrence [5.0] vs anchors [1.0, 2.0] -- whose total
    label-permutation space is C(3,1)=3, far below REFEREE_ENUMERATION_THRESHOLD. Hand
    enumeration of all 3 ways to choose which ONE of {5.0, 1.0, 2.0} is "group1":
      - group1={5.0}: delta* = 5.0 - mean(1.0,2.0) = 5.0 - 1.5 = 3.5   (== the OBSERVED grouping)
      - group1={1.0}: delta* = 1.0 - mean(5.0,2.0) = 1.0 - 3.5 = -2.5
      - group1={2.0}: delta* = 2.0 - mean(5.0,1.0) = 2.0 - 3.0 = -1.0
    T_obs = 3.5 (single session, so T == its own delta regardless of weight). For "greater"
    sidedness, #{T* >= 3.5} = 1 (only the observed grouping itself) -> p = (1+1)/(3+1) = 0.5."""
    session_groups = {"2026-06-08": ([5.0], [1.0, 2.0])}
    result = permutation_test(session_groups, "hyp-enum", sidedness="greater")
    assert result["state"] == "ok"
    assert result["enumeration"] is True
    assert result["draws_used"] == 3
    assert abs(result["t"] - 3.5) < 1e-9  # float division noise, not a rounding bug
    assert result["p"] == 0.5
    assert result["min_attainable_p"] == 0.25


def test_permutation_test_enumeration_is_deterministic_with_zero_rng_draws():
    """TC-4's "no seeded sampling" clause: two calls with DIFFERENT hypothesis_id (which would
    seed a DIFFERENT stream in the seeded-draw branch) still produce the byte-identical result in
    the enumeration branch, because enumeration never touches the RNG at all."""
    session_groups = {"2026-06-08": ([5.0], [1.0, 2.0])}
    a = permutation_test(session_groups, "hyp-a", sidedness="greater")
    b = permutation_test(session_groups, "hyp-b-totally-different", sidedness="greater")
    assert a == b


# === TC-5: the seeded B-draw branch ====================================================================


def test_permutation_test_seeded_branch_uses_exactly_b_draws_and_the_p_formula():
    """TC-5: a fixture large enough to exceed REFEREE_ENUMERATION_THRESHOLD (4 sessions of
    n1=3,n2=3 each: C(6,3)=20 per session, 20**4=160,000 total > 8,192) uses exactly `b` seeded
    draws, and `p = (1 + #{T* >= T}) / (b + 1)` for "greater" sidedness -- verified by
    independently recomputing the extreme count with a from-scratch reference permutation loop."""
    rng = random.Random("tc5-fixture-seed")
    session_groups = {
        f"2026-03-{i + 1:02d}": (
            [rng.gauss(0, 1) for _ in range(3)],
            [rng.gauss(0, 1) for _ in range(3)],
        )
        for i in range(4)
    }
    b = 500
    result = permutation_test(session_groups, "hyp-seeded", sidedness="greater", b=b)
    assert result["enumeration"] is False
    assert result["draws_used"] == b
    assert result["min_attainable_p"] == 1.0 / (b + 1)

    # Independent reference recomputation (a from-scratch permutation loop, not calling any
    # `referee_stats` internals beyond the plain arithmetic every reader can verify).
    sessions = sorted(session_groups)
    n1_by_s = {s: len(session_groups[s][0]) for s in sessions}
    n2_by_s = {s: len(session_groups[s][1]) for s in sessions}
    weight_by_s = {
        s: (n1_by_s[s] * n2_by_s[s]) / (n1_by_s[s] + n2_by_s[s]) for s in sessions
    }
    total_weight = sum(weight_by_s.values())
    delta_by_s = {
        s: sum(session_groups[s][0]) / n1_by_s[s] - sum(session_groups[s][1]) / n2_by_s[s]
        for s in sessions
    }
    t_obs = sum(weight_by_s[s] * delta_by_s[s] for s in sessions) / total_weight
    assert abs(result["t"] - t_obs) < 1e-9

    extreme = 0
    streams = {s: random.Random(f"{REFEREE_SEED}:hyp-seeded:perm:{s}") for s in sessions}
    pooled = {s: session_groups[s][0] + session_groups[s][1] for s in sessions}
    for _ in range(b):
        acc = 0.0
        for s in sessions:
            values = pooled[s]
            n1 = n1_by_s[s]
            n = len(values)
            rstream = streams[s]
            pool = list(range(n))
            for idx in range(n1):
                j = rstream.randrange(idx, n)
                pool[idx], pool[j] = pool[j], pool[idx]
            g1_sum = sum(values[idx] for idx in pool[:n1])
            g2_sum = sum(values) - g1_sum
            delta_star = g1_sum / n1 - g2_sum / (n - n1)
            acc += weight_by_s[s] * delta_star
        t_star = acc / total_weight
        if t_star >= t_obs:
            extreme += 1
    expected_p = (1 + extreme) / (b + 1)
    assert result["p"] == expected_p


def test_permutation_test_default_b_is_referee_b_when_not_overridden():
    """A fixture whose space exceeds the enumeration threshold, called WITHOUT overriding `b`,
    uses the production default REFEREE_B (10,000) -- proving the confirmatory default is wired,
    not just an override-only parameter."""
    rng = random.Random("tc5-default-b-seed")
    session_groups = {
        f"2026-04-{i + 1:02d}": (
            [rng.gauss(0, 1) for _ in range(3)],
            [rng.gauss(0, 1) for _ in range(3)],
        )
        for i in range(4)
    }
    result = permutation_test(session_groups, "hyp-default-b", sidedness="greater")
    assert result["enumeration"] is False
    assert result["draws_used"] == REFEREE_B


def test_permutation_test_reruns_are_byte_identical():
    rng = random.Random("tc5-repro-seed")
    session_groups = {
        f"2026-05-{i + 1:02d}": ([rng.gauss(0, 1)], [rng.gauss(0, 1) for _ in range(4)])
        for i in range(10)
    }
    a = permutation_test(session_groups, "hyp-repro-perm", sidedness="greater", b=300)
    b = permutation_test(session_groups, "hyp-repro-perm", sidedness="greater", b=300)
    assert a == b


def test_permutation_test_no_informative_sessions_is_insufficient_sample():
    sg = {"2026-06-08": ([], [1.0, 2.0]), "2026-06-09": ([1.0], [])}
    result = permutation_test(sg, "hyp-none-informative")
    assert result == {"state": INSUFFICIENT_SAMPLE, "n_informative_sessions": 0}


# === TC-6: robustness variants are served, never substituted ==========================================


def test_sign_flip_and_equal_weight_are_served_alongside_and_never_change_the_primary_p():
    """TC-6: a fixture engineered so the equal-weight T flips sign relative to the (precision-
    weighted) primary T -- one heavily-weighted session pulls the primary T positive while the
    unweighted average is negative. Both robustness values are returned, and the PRIMARY p/T is
    identical whether or not the caller also computes the variants (no shared mutable state, no
    substitution)."""
    session_groups = {
        # A fat session (n1=n2=20), delta=1.0, weight=20*20/40=10 -> contributes 10*1.0=10.0.
        "2026-07-01": ([2.0] * 20, [1.0] * 20),
        # A thin session (n1=n2=1), delta=-3.0, weight=1*1/2=0.5 -> contributes 0.5*-3.0=-1.5.
        "2026-07-02": ([-1.0], [2.0]),
    }
    # Precision-weighted T = (10.0 + -1.5) / (10 + 0.5) = 8.5 / 10.5 > 0 (the fat session wins).
    # Equal-weight T = mean(1.0, -3.0) = -1.0 < 0 (the thin session's larger delta wins) -- the
    # engineered sign flip.
    primary_before = permutation_test(session_groups, "hyp-tc6", sidedness="greater", b=200)
    equal = equal_weight_t(session_groups)
    flip = sign_flip_result(session_groups, "hyp-tc6", sidedness="greater", b=200)
    primary_after = permutation_test(session_groups, "hyp-tc6", sidedness="greater", b=200)

    assert primary_before["p"] == primary_after["p"]
    assert primary_before["t"] == primary_after["t"]
    assert primary_before["t"] > 0.0  # the fat session's positive effect dominates
    assert equal["state"] == "ok"
    assert equal["t"] < 0.0  # equal weighting lets the thin session's negative effect dominate
    assert flip["state"] == "ok"
    assert "p" in flip and "t" in flip
    assert flip["t"] == primary_before["t"]  # sign-flip reuses the SAME T, a different null only


def test_equal_weight_t_matches_a_hand_computed_value():
    """Hand arithmetic: two informative sessions, delta_1=2.0, delta_2=-6.0; equal-weight
    T = mean(2.0, -6.0) = -2.0 (w_s=1 for both, regardless of group sizes)."""
    session_groups = {
        "2026-08-01": ([12.0, 12.0], [10.0, 10.0]),  # mean 12 - mean 10 = 2.0
        "2026-08-02": ([1.0], [7.0]),  # 1.0 - 7.0 = -6.0
    }
    result = equal_weight_t(session_groups)
    assert result["t"] == -2.0
    assert result["n_informative_sessions"] == 2


# === TC-7: Benjamini-Hochberg, hand-computed ============================================================


def test_benjamini_hochberg_k_star_matches_a_hand_computed_boundary():
    """TC-7: p = [0.01, 0.04, 0.03, 0.20, 0.50], q=0.10, m=5. Sorted ascending:
    [0.01, 0.03, 0.04, 0.20, 0.50] (original indices [0, 2, 1, 3, 4]).
    Thresholds (k/m)*q: rank1=0.02, rank2=0.04, rank3=0.06, rank4=0.08, rank5=0.10.
    0.01<=0.02 T; 0.03<=0.04 T; 0.04<=0.06 T; 0.20<=0.08 F; 0.50<=0.10 F -> k*=3 (ranks 1..3
    corroborated: original indices 0, 2, 1)."""
    p_values = [0.01, 0.04, 0.03, 0.20, 0.50]
    result = benjamini_hochberg(p_values, q=0.10)
    assert result["m"] == 5
    assert result["k_star"] == 3
    assert result["bh_pass"] == [True, True, True, False, False]


def test_benjamini_hochberg_unevaluated_candidate_folds_as_p_1_and_stays_inside_m():
    """TC-7 (the "never dropped from m" half): the SAME family as above, plus one
    unevaluated/withdrawn candidate folded in as the literal p=1.0. m becomes 6 (never 5), and the
    p=1 candidate is never corroborated."""
    p_values = [0.01, 0.04, 0.03, 0.20, 0.50, 1.0]
    result = benjamini_hochberg(p_values, q=0.10)
    assert result["m"] == 6
    assert result["bh_pass"][5] is False
    # Hand-recomputed at m=6: thresholds (k/6)*0.10 = 0.0167, 0.0333, 0.05, 0.0667, 0.0833, 0.10.
    # 0.01<=0.0167 T; 0.03<=0.0333 T; 0.04<=0.05 T; 0.20<=0.0667 F; 0.50<=0.0833 F; 1.0<=0.10 F.
    assert result["k_star"] == 3
    assert result["bh_pass"] == [True, True, True, False, False, False]


def test_benjamini_yekutieli_adjusted_p_is_served_as_a_separate_non_deciding_field():
    """BY-adjusted p-values are monotone non-decreasing by rank and never drive `bh_pass` (BH
    alone does, per spec Sec5)."""
    p_values = [0.01, 0.04, 0.03, 0.20, 0.50]
    result = benjamini_hochberg(p_values, q=0.10)
    order = sorted(range(5), key=lambda i: p_values[i])
    by_sorted = [result["by_adjusted_p"][i] for i in order]
    assert by_sorted == sorted(by_sorted)  # non-decreasing by ascending-p rank
    assert all(0.0 <= v <= 1.0 for v in result["by_adjusted_p"])


def test_benjamini_hochberg_rejects_an_empty_family():
    try:
        benjamini_hochberg([], q=0.10)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError: m must be >= 1")


# === TC-16: full-computation byte-identical reruns ======================================================


def test_full_ci_p_bh_computation_is_byte_identical_across_two_separate_runs():
    """TC-16: identical seeds and inputs, the full CI + p + BH computation run twice as SEPARATE
    top-level calls (not a cached/memoized single call) -- every returned p and every CI bound is
    byte-identical."""
    rng = random.Random("tc16-fixture-seed")
    session_groups = {
        f"2026-09-{i + 1:02d}": (
            [rng.gauss(1.0, 1.0) for _ in range(2)],
            [rng.gauss(0.0, 1.0) for _ in range(4)],
        )
        for i in range(10)
    }
    hypothesis_id = "hyp-tc16"

    def run_all():
        perm = permutation_test(session_groups, hypothesis_id, sidedness="greater", b=400)
        occ_values = [1.0, 2.0, -1.0, 3.5, 0.2, -0.8]
        ci_occ = bootstrap_ci_occurrence(occ_values, hypothesis_id, b=400)
        ci_cluster = bootstrap_ci_cluster(session_groups, hypothesis_id, b=400)
        bh = benjamini_hochberg([perm["p"], 0.2, 0.03, 1.0], q=0.10)
        return perm, ci_occ, ci_cluster, bh

    run1 = run_all()
    run2 = run_all()
    assert run1 == run2


# === TC-17: the oracle attestation, round-trip and corruption detection ================================


def test_run_oracle_attestation_round_trips():
    """TC-17: `run_oracle_attestation()` returns `passed=True` on the pinned known-answer subset,
    and `verify_oracle_attestation` independently agrees."""
    record = run_oracle_attestation()
    assert record["passed"] is True
    assert set(record) == {"expected", "actual", "tolerance", "passed", "stats_core_version"}
    assert verify_oracle_attestation(record) is True


def test_verify_oracle_attestation_detects_a_corrupted_actual_field():
    record = run_oracle_attestation()
    corrupted = dict(record)
    corrupted["actual"] = dict(record["actual"])
    corrupted["actual"]["ci_low"] = record["actual"]["ci_low"] + 1.0
    corrupted["passed"] = True  # a tampered record that LIES about its own passed field
    assert verify_oracle_attestation(corrupted) is False


def test_verify_oracle_attestation_detects_a_mismatched_stats_core_version():
    record = run_oracle_attestation()
    corrupted = dict(record)
    corrupted["stats_core_version"] = "referee-stats-v0-fake"
    assert verify_oracle_attestation(corrupted) is False


def test_verify_oracle_attestation_detects_a_hand_edited_expected_field():
    """Even if `actual` and `expected` are mutually consistent with each other, an `expected` that
    no longer matches THIS BUILD's own pinned constant is rejected -- the verifier re-derives
    expected from the live build, it never trusts the stored record's own `expected`."""
    record = run_oracle_attestation()
    corrupted = dict(record)
    corrupted["expected"] = dict(record["expected"])
    corrupted["expected"]["ci_low"] = record["expected"]["ci_low"] + 0.5  # a genuine alteration
    assert verify_oracle_attestation(corrupted) is False


def test_verify_oracle_attestation_rejects_a_non_dict_input():
    assert verify_oracle_attestation(None) is False
    assert verify_oracle_attestation({}) is False
    assert verify_oracle_attestation("not a dict") is False
