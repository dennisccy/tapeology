"""``referee_stats.py`` (Era 6 "The Referee", J-03) — the statistics core's own mechanics: fast,
deterministic, hand-derivable unit tests. Test-first contract: TC-1 through TC-7, TC-16, TC-17,
TC-19 in ``docs/phases/goal-referee-iter-3.md``. The CALIBRATION/oracle suite (TC-8 through
TC-15, TC-18 — the six spec Sec6 cases plus the mutation fixture, all seeded simulations that must
fit inside ``REFEREE_ORACLE_BUDGET_SECONDS``) lives separately in ``test_referee_oracles.py``, so
this file's own tests stay fast and this file never risks the runtime budget.

**iter-4 additions** (``docs/phases/goal-referee-iter-4.md`` — its OWN, separate TC-numbering;
every iter-4 section below is explicitly labeled "iter-4" to avoid ambiguity with the iter-3 TC
numbers above): the exact-enumeration p-value floor fix's own proof (TC-1/TC-2), direct coverage
for `_draw_indices_without_replacement` (TC-7) and the seeded branch's `n2 == 1` fast path (TC-8),
and the version-bump attestation check (TC-5/TC-6).

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
    STATS_CORE_VERSION,
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


# === iter-4 TC-7: `_draw_indices_without_replacement` direct coverage ================================
#
# docs/phases/goal-referee-iter-4.md's OWN TC-numbering -- distinct from this file's iter-3 TC-1
# through TC-19 above (goal-referee-iter-3.md). Every iter-4 section in this file is explicitly
# labeled "iter-4" to avoid ambiguity with the pre-existing iter-3 TC numbers. Reviewer-flagged
# gap: zero direct assertions existed for this primitive before this iteration. KEPT, not deleted
# -- its own docstring already frames it as the documented without-replacement primitive J-04's
# real anchor draws are expected to reuse.


def test_iter4_tc7_draw_indices_without_replacement_is_deterministic_for_identical_seeds():
    """iter-4 TC-7 (determinism half): two INDEPENDENTLY-CONSTRUCTED `random.Random` instances,
    built from the identical seed, produce the byte-identical sorted k-element result -- k
    distinct indices in range(population)."""
    a = rs._draw_indices_without_replacement(random.Random("iter4-tc7-seed"), population=7, k=3)
    b = rs._draw_indices_without_replacement(random.Random("iter4-tc7-seed"), population=7, k=3)
    assert a == b
    assert a == sorted(a)
    assert len(set(a)) == 3
    assert all(0 <= idx < 7 for idx in a)


def test_iter4_tc7_draw_indices_without_replacement_covers_the_full_population_when_k_equals_it():
    """iter-4 TC-7 (full-population half): `k == population` returns every index in
    `range(population)` exactly once."""
    result = rs._draw_indices_without_replacement(
        random.Random("iter4-tc7-full-seed"), population=5, k=5
    )
    assert result == list(range(5))


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


# === iter-4 TC-1/TC-2: the exact-enumeration p-value floor guarantee =================================
#
# Fixes the evaluator's own reproduced defect (docs/phases/goal-referee-iter-4.md): the exact-
# enumeration branch's `g2_sum = total - g1_sum` could disagree with `_t_statistic`'s own direct
# `math.fsum(group2)` in the last representable digit, letting the TRUE observed grouping narrowly
# fail its own `_is_extreme` self-comparison and silently drop from the extreme count -- so the
# returned `p` could fall to HALF its own mathematical floor `2 / (draws_used + 1)` (the floor
# holds because the observed grouping is always one guaranteed member of the enumerated space).


def test_iter4_tc1_the_evaluators_exact_minimal_repro_now_hits_the_correct_floor():
    """iter-4 TC-1: the evaluator's own exact minimal reproduction -- one session, `sidedness=
    "greater"` -- now returns `p == 2/7` (`draws_used == 6`, the exact floor `2 / (draws_used +
    1)`), not the previously-served `1/7` the pre-fix subtraction bug produced."""
    g1 = [0.9571299431380904, 0.23675146939940733]
    g2 = [-0.2015364333714562, -0.47887435876092443]
    result = permutation_test({"s0": (g1, g2)}, "probe", sidedness="greater")
    assert result["enumeration"] is True
    assert result["draws_used"] == 6
    assert result["p"] == 2 / 7 == 0.2857142857142857


def test_iter4_tc2_the_exact_mode_floor_never_falls_below_its_own_mathematical_minimum():
    """iter-4 TC-2: a freshly seeded-generated property test across thousands of small
    enumeration-mode fixtures -- 2-vs-2, 1-vs-4, and 4-vs-1 group shapes (matching the evaluator's
    own reproduction shapes), 1 to 4 informative sessions (multi-session is where the pre-fix bug
    actually manifests -- a single-session fixture like TC-1's own repro can never trigger the
    CROSS-session accumulation half of the defect), all three `sidedness` values -- asserting
    `p >= 2 / (draws_used + 1)` with ZERO violations across the entire generated set. Every
    fixture is generated here from scratch (never derived from the module under test); every case
    is confirmed to genuinely enter the enumeration branch, the only branch this iteration's fix
    touches. (Re-run against the PRE-FIX code during development: this exact generator/seed finds
    12 violations in the first 3,000 cases -- proof this property test would have caught the
    original defect, not merely failed to exercise it.)"""
    rng = random.Random("iter4-tc2-property-seed-v1")
    shapes = [(2, 2), (1, 4), (4, 1)]
    sidedness_values = ("greater", "less", "two-sided")
    n_cases = 3000
    violations = []
    for i in range(n_cases):
        n_sessions = rng.randint(1, 4)
        n1, n2 = rng.choice(shapes)
        sidedness = rng.choice(sidedness_values)
        session_groups = {
            f"s{j:03d}": (
                [rng.gauss(0.0, 1.0) for _ in range(n1)],
                [rng.gauss(0.0, 1.0) for _ in range(n2)],
            )
            for j in range(n_sessions)
        }
        result = permutation_test(session_groups, f"iter4-tc2-case-{i}", sidedness=sidedness)
        assert result["enumeration"] is True, f"case {i} unexpectedly used the seeded branch"
        floor = 2.0 / (result["draws_used"] + 1)
        if result["p"] < floor:
            violations.append((i, n_sessions, (n1, n2), sidedness, result["p"], floor))
    assert violations == [], f"{len(violations)} floor violation(s), first 3: {violations[:3]}"


def test_iter4_tc2_the_exact_mode_floor_holds_in_the_extreme_tail_regime_too():
    """iter-4 TC-2 (audit rider, goal-referee-iter-4 audit finding T1): the SAME floor property as
    the test directly above, generated in the regime where the floor actually BINDS -- a strong
    separation between the two groups, so the OBSERVED grouping is very often the unique most
    extreme member of its own enumerated space (`p` sitting exactly at `2 / (draws_used + 1)`).

    Why this second block exists, when the null-regime one above already passes: under a pure null
    (both groups drawn from the identical zero-mean generator, as above) the observed grouping is
    the unique maximum with probability only `1 / draws_used`, so with `draws_used` in the hundreds
    or thousands the floor is essentially never approached and a floor bug has almost nothing to
    bite on. The fix this iteration ships has TWO halves -- the per-combination `g2_sum` direct
    complement accumulation AND the cross-session `math.fsum` combination of the weighted per-
    session terms -- and the null-regime generator above is only sensitive to the FIRST. Measured
    during the audit: reverting ONLY the cross-session half (keeping the `g2_sum` half) produces
    ZERO floor violations across the whole 3,000-case null set above, but 58 violations across
    this block's own 1,000 tail-regime cases (and ~8% of a 18,000-case independent sweep). Without
    this block the second half of the fix is shipped unguarded -- a later refactor could quietly
    restore the naive running `acc +=` and the entire suite would stay green.

    Everything else matches the block above: fixtures generated here from scratch, the same three
    group shapes, all three `sidedness` values, every case confirmed to enter the enumeration
    branch, and the identical assertion `p >= 2 / (draws_used + 1)` with zero violations."""
    rng = random.Random("iter4-tc2-tail-regime-seed-v1")
    shapes = [(2, 2), (1, 4), (4, 1)]
    sidedness_values = ("greater", "less", "two-sided")
    n_cases = 1000
    violations = []
    at_the_floor = 0
    for i in range(n_cases):
        n_sessions = rng.randint(2, 4)
        n1, n2 = rng.choice(shapes)
        sidedness = rng.choice(sidedness_values)
        # `less` needs the separation mirrored, so its own observed grouping is the extreme one
        # under ITS tail; `two-sided` binds under either orientation.
        shift = -3.0 if sidedness == "less" else 3.0
        session_groups = {
            f"s{j:03d}": (
                [rng.gauss(shift, 1.0) for _ in range(n1)],
                [rng.gauss(-shift, 1.0) for _ in range(n2)],
            )
            for j in range(n_sessions)
        }
        result = permutation_test(session_groups, f"iter4-tc2-tail-case-{i}", sidedness=sidedness)
        assert result["enumeration"] is True, f"case {i} unexpectedly used the seeded branch"
        floor = 2.0 / (result["draws_used"] + 1)
        if result["p"] < floor:
            violations.append((i, n_sessions, (n1, n2), sidedness, result["p"], floor))
        elif result["p"] == floor:
            at_the_floor += 1
    assert violations == [], f"{len(violations)} floor violation(s), first 3: {violations[:3]}"
    # The guard's own can-fail check: this generator must actually PUT cases on the floor,
    # otherwise it is testing the same insensitive regime as the block above and proves nothing.
    assert at_the_floor >= 100, (
        f"only {at_the_floor} of {n_cases} cases landed exactly on the floor -- this generator is "
        f"no longer in the tail regime, so it can no longer guard the cross-session half of the fix"
    )


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


# === iter-4 TC-8: the seeded branch's `n1 > 1, n2 == 1` fast path ====================================


def test_iter4_tc8_n2_equals_1_fast_path_matches_a_from_scratch_general_algorithm_reference():
    """iter-4 TC-8: n1=3, n2=1 -- the `elif n2 == 1` fast path -- across enough sessions to force
    the SEEDED (non-enumeration) branch, mirroring the `n1 == 1` fast path's own already-hand-
    verified equivalence (the reviewer's own check during development, and this function's own
    inline comment). The fast path consumes exactly ONE `stream.randrange` call per draw while the
    GENERAL Fisher-Yates algorithm consumes `n1` calls per draw, so a same-keyed-stream reference
    would diverge after the very first draw (verified during development -- it does: a materially
    different p). "Matches a from-scratch general-algorithm reference" therefore means the
    mathematically meaningful thing: both the module's own fast path AND an INDEPENDENTLY-coded
    general-algorithm reference (its own, unrelated stream) are unbiased Monte-Carlo estimators of
    the IDENTICAL exact target -- computed here by brute-force full enumeration (deterministic,
    zero RNG), exactly what the module's own `use_enumeration` path would compute if this
    fixture's space did not exceed `REFEREE_ENUMERATION_THRESHOLD`. Both estimates must land
    within a wide, honestly-derived (binomial standard-error) tolerance of that ground truth."""
    rng = random.Random("iter4-tc8-fixture-seed-v1")
    n_sessions = 7  # C(4,3)=4 per session; 4**7 = 16,384 > REFEREE_ENUMERATION_THRESHOLD (8,192)
    session_groups = {
        f"2026-10-{i + 1:02d}": ([rng.gauss(0, 1) for _ in range(3)], [rng.gauss(0, 1)])
        for i in range(n_sessions)
    }
    sidedness = "greater"

    # --- ground truth: brute-force full enumeration, independent of `permutation_test` ---
    sessions = sorted(session_groups)
    weight_by_s = {s: (3 * 1) / (3 + 1) for s in sessions}
    total_weight = sum(weight_by_s.values())
    delta_by_s = {
        s: sum(session_groups[s][0]) / 3 - sum(session_groups[s][1]) / 1 for s in sessions
    }
    t_obs_ref = sum(weight_by_s[s] * delta_by_s[s] for s in sessions) / total_weight
    pooled = {s: session_groups[s][0] + session_groups[s][1] for s in sessions}
    combos_by_session = [list(itertools.combinations(range(4), 3)) for _ in sessions]
    extreme_exact = 0
    total_combos = 0
    for joint in itertools.product(*combos_by_session):
        acc = 0.0
        for s, combo in zip(sessions, joint):
            values = pooled[s]
            g1 = sum(values[idx] for idx in combo)
            g2 = sum(values) - g1
            acc += weight_by_s[s] * (g1 / 3 - g2 / 1)
        if (acc / total_weight) >= t_obs_ref:
            extreme_exact += 1
        total_combos += 1
    assert total_combos == 4**n_sessions
    p_star = (1 + extreme_exact) / (total_combos + 1)

    # --- the module's own fast path ---
    b = 8000
    real = permutation_test(session_groups, "iter4-tc8-hyp", sidedness=sidedness, b=b)
    assert real["enumeration"] is False  # sanity: this fixture genuinely forces the seeded branch
    assert abs(real["t"] - t_obs_ref) < 1e-9

    # --- an INDEPENDENTLY-coded general-algorithm reference, its own unrelated stream ---
    streams = {s: random.Random(f"iter4-tc8-general-reference-seed:{s}") for s in sessions}
    extreme_general = 0
    for _ in range(b):
        acc = 0.0
        for s in sessions:
            values = pooled[s]
            n1, n = 3, 4
            rstream = streams[s]
            pool = list(range(n))
            for idx in range(n1):
                j = rstream.randrange(idx, n)
                pool[idx], pool[j] = pool[j], pool[idx]
            g1 = sum(values[idx] for idx in pool[:n1])
            g2 = sum(values) - g1
            acc += weight_by_s[s] * (g1 / n1 - g2 / (n - n1))
        if (acc / total_weight) >= t_obs_ref:
            extreme_general += 1
    p_general = (1 + extreme_general) / (b + 1)

    tolerance = 6.0 * math.sqrt(p_star * (1 - p_star) / b)
    assert abs(real["p"] - p_star) <= tolerance, (
        f"fast-path p={real['p']!r} strayed {abs(real['p'] - p_star):.5f} from ground truth "
        f"{p_star!r} (tolerance {tolerance:.5f})"
    )
    assert abs(p_general - p_star) <= tolerance, (
        f"general-algorithm reference p={p_general!r} strayed {abs(p_general - p_star):.5f} from "
        f"ground truth {p_star!r} (tolerance {tolerance:.5f})"
    )


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


# === iter-4 TC-5/TC-6: the version bump this iteration's fix makes real ================================


def test_iter4_tc5_tc6_the_version_bump_is_real_and_a_stale_version_is_rejected():
    """iter-4 TC-5: `STATS_CORE_VERSION` reads the bumped `"referee-stats-v2"` (a genuine
    algorithmic revision to this file's exact-enumeration branch -- the module's own documented
    policy: "bumped only on a genuine algorithmic revision... a named revision, never silently"),
    and `run_oracle_attestation()` embeds it; two independent calls return byte-identical `actual`
    values (re-verifying TC-16/TC-17's own byte-identity guarantee still holds post-fix).

    iter-4 TC-6: an attestation record identical to the current pin except `stats_core_version`
    reads the OLD `"referee-stats-v1"` string is rejected as version-stale by
    `verify_oracle_attestation`, even though `expected`/`tolerance`/`actual` all otherwise match
    the CURRENT build's own pin exactly -- the fail-closed discipline (T-8) this iteration's
    version bump makes real for the first time (before this iteration, no build had ever changed
    `STATS_CORE_VERSION`, so this rejection path was unexercised)."""
    assert STATS_CORE_VERSION == "referee-stats-v2"

    record_a = run_oracle_attestation()
    record_b = run_oracle_attestation()
    assert record_a["stats_core_version"] == "referee-stats-v2"
    assert record_a["actual"] == record_b["actual"]
    assert record_a["passed"] is True
    assert verify_oracle_attestation(record_a) is True

    stale = dict(record_a)
    stale["stats_core_version"] = "referee-stats-v1"
    assert verify_oracle_attestation(stale) is False
