# Iteration diff (bounded)

Files changed: 6. Shown in full: 3.

**Truncated** (over the line caps; tail omitted, noted inline or fully skipped):
- `apps/backend/app/research/referee_stats.py` (317 lines not shown)
- `apps/backend/tests/test_referee_oracles.py` (55 lines not shown)
- `apps/backend/tests/test_referee_stats.py` (157 lines not shown)

```diff
diff --git a/apps/backend/tests/test_referee_evidence.py b/apps/backend/tests/test_referee_evidence.py
index 8d5f20e..1231577 100644
--- a/apps/backend/tests/test_referee_evidence.py
+++ b/apps/backend/tests/test_referee_evidence.py
@@ -24,15 +24,23 @@ from app.providers.base import Side, TradeEvent
 from app.research import desk_playbook as desk_playbook_module
 from app.research import referee_evidence as referee_evidence_module
 from app.research.datasets import SPLIT_HOLDOUT, SPLIT_TRAIN, DatasetStore
-from app.research.desk_playbook import PLAYBOOK_REGISTER, PlaybookStore, playbook_parameters
+from app.research.desk_playbook import (
+    PLAYBOOK_REGISTER,
+    PlaybookStore,
+    playbook_parameters,
+    resolve_desk_playbook_dir,
+)
 from app.research.desk_routes import get_playbook_store
 from app.research.referee_evidence import (
     REFEREE_FORMING_BAR_BASIS_CAVEAT,
+    REFEREE_SESSION_COMPLETE_ET,
     REFEREE_TICK_GATE_SYMBOL_DAYS,
     RefereeObservationCache,
+    _signal_reaches_session_complete,
     _tick_gate_state,
     current_playbook_detector_basis,
     playbook_observations,
+    resolve_referee_obs_cache_db_path,
     strategy_observations,
 )
 from app.research.routes import ResearchRegistry, get_dataset_store, set_registry
@@ -741,3 +749,100 @@ def test_adapters_write_nothing_to_any_pre_existing_store(client):
 
     assert after == before
     assert after_journal == before_journal
+
+
+# === goal-referee-iter-3 carried rider 1 -- TC-20: _signal_reaches_session_complete ==================
+#
+# Zero assertions existed for this function before this iteration (a gap-blind estimate J-06's
+# confirmatory-eligibility fold will lean on). ``REFEREE_SESSION_COMPLETE_ET`` = "15:55" ET.
+
+
+def _forward_signal(at_utc: str, minutes_to_close: float) -> dict:
+    """The minimal shape ``_signal_reaches_session_complete`` reads -- only
+    ``forward["at_utc"]``/``forward["minutes_to_close"]``, exactly as it is read off a real
+    already-measured signal's own ``forward`` block."""
+    return {"forward": {"at_utc": at_utc, "minutes_to_close": minutes_to_close}}
+
+
+def test_signal_reaches_session_complete_at_and_around_the_boundary():
+    """TC-20: a fixture signal engineered so its computed ``last_bar_epoch`` lands exactly at, one
+    second before, and one second after ``_session_complete_epoch(session_date)`` -- True at and
+    after the boundary, False strictly before it. The anchor (``at_utc``) is held FIXED across all
+    three cases; only ``minutes_to_close`` varies, isolating the boundary comparison from any other
+    variable."""
+    session_date = "2026-06-08"
+    boundary_epoch = referee_evidence_module._session_complete_epoch(session_date)
+    anchor_epoch = boundary_epoch - 600.0  # 10 minutes before the boundary
+    at_utc = referee_evidence_module._iso(anchor_epoch)
+
+    at_boundary = _forward_signal(at_utc, 10.0)
+    one_second_before = _forward_signal(at_utc, 10.0 - 1.0 / 60.0)
+    one_second_after = _forward_signal(at_utc, 10.0 + 1.0 / 60.0)
+
+    assert _signal_reaches_session_complete(at_boundary, session_date) is True
+    assert _signal_reaches_session_complete(one_second_before, session_date) is False
+    assert _signal_reaches_session_complete(one_second_after, session_date) is True
+
+
+def test_signal_reaches_session_complete_is_false_with_no_forward_block():
+    """A signal recorded before the (era-B2) forward-measurement pass existed carries no ``forward``
+    block at all -- an honest False, never a crash and never a fabricated True."""
+    assert _signal_reaches_session_complete({"symbol": "AAPL"}, "2026-06-08") is False
+
+
+def test_signal_reaches_session_complete_reads_bar_count_minutes_not_wall_clock_and_says_so():
+    """The disclosed bar-gap-blind limitation (module docstring), asserted as a real behavior
+    rather than left to pass silently: ``minutes_to_close`` is a BAR-COUNT-equivalent figure, not
+    measured wall-clock time, so this function is blind to any intra-session gap in the finest
+    measurement series. Two signals whose ``(anchor_epoch, minutes_to_close)`` PRODUCT is identical
+    are treated identically regardless of how much real wall-clock time actually elapsed on either
+    side of a gap -- exercised here by anchoring EARLIER in the session (23 minutes before the
+    boundary) with a bar-count-equivalent ``minutes_to_close`` that under-counts a gapped series and
+    still lands exactly one second short of the boundary: the same honest False as a gap-free
+    signal in the direct boundary test above, never a "corrected" True."""
+    session_date = "2026-06-08"
+    boundary_epoch = referee_evidence_module._session_complete_epoch(session_date)
+    anchor_epoch = boundary_epoch - 1380.0  # 23 minutes before the boundary (a gappier series)
+    at_utc = referee_evidence_module._iso(anchor_epoch)
+    gap_blind_minutes_to_close = (1380.0 - 1.0) / 60.0  # bar-count-equivalent, one second short
+
+    signal = _forward_signal(at_utc, gap_blind_minutes_to_close)
+
+    assert _signal_reaches_session_complete(signal, session_date) is False
+
+
+def test_referee_session_complete_et_is_the_pinned_1555_boundary():
+    """The boundary constant itself, pinned (spec Sec1): 15:55 ET."""
+    assert REFEREE_SESSION_COMPLETE_ET == "15:55"
+
+
+# === goal-referee-iter-3 carried rider 2 -- TC-21: resolve_referee_obs_cache_db_path =================
+#
+# Exported, never called, before this iteration.
+
+
+def test_resolve_referee_obs_cache_db_path_env_override_returns_verbatim(monkeypatch):
+    """TC-21 (env-var-override half): ``TAPEOLOGY_REFEREE_OBS_CACHE_DB`` set returns that EXACT
+    path, verbatim -- never joined, never normalized."""
+    monkeypatch.setenv("TAPEOLOGY_REFEREE_OBS_CACHE_DB", "/explicit/override/path/obs.db")
+
+    result = resolve_referee_obs_cache_db_path("/anything/universe/dir")
+
+    assert result == "/explicit/override/path/obs.db"
+
+
+def test_resolve_referee_obs_cache_db_path_defaults_to_a_sibling_of_the_playbook_dir(monkeypatch):
+    """TC-21 (sibling-of-playbook-dir default half): with the env var unset, the resolved path is
+    ``referee_obs_cache.db`` co-located as a SIBLING of ``resolve_desk_playbook_dir``'s own
+    resolved directory -- the ``playbook_evidence_cache_db_path`` resolver pattern verbatim, one
+    level up (this module has no dependency on ``desk_routes.py``)."""
+    monkeypatch.delenv("TAPEOLOGY_REFEREE_OBS_CACHE_DB", raising=False)
+    universe_dir = "/some/resolved/desk/universe"
+    playbook_dir = resolve_desk_playbook_dir(universe_dir)
+    expected = os.path.join(os.path.dirname(playbook_dir), "referee_obs_cache.db")
+
+    result = resolve_referee_obs_cache_db_path(universe_dir)
+
+    assert result == expected
+    assert os.path.basename(result) == "referee_obs_cache.db"
+    assert os.path.dirname(result) == os.path.dirname(playbook_dir)
diff --git a/apps/backend/tests/test_referee_guards.py b/apps/backend/tests/test_referee_guards.py
index b2557a6..2397188 100644
--- a/apps/backend/tests/test_referee_guards.py
+++ b/apps/backend/tests/test_referee_guards.py
@@ -210,3 +210,45 @@ def test_import_ban_guard_can_fail_on_a_seeded_violation():
     seeded_referee_imports = {"app.research.referee_evidence", "app.research.other"}
     hits = {name for name in seeded_referee_imports if name.split(".")[-1].startswith("referee_")}
     assert hits == {"app.research.referee_evidence"}
+
+
+# --- goal-referee-iter-3 TC-23: the referee_stats.py-scoped import ban -----------------------------
+#
+# IN SCOPE: "referee_stats.py imports none of desk_playbook_detect, desk_playbook_context,
+# desk_forward, levels, tradability (the stats core is estimand-agnostic -- it consumes plain
+# numeric/session arrays a future caller passes in, never rail/detector/context data directly)".
+# The bidirectional guard above already proves the first two (desk_playbook_detect/
+# desk_playbook_context) for EVERY referee_*.py module via `_referee_modules()`'s glob; this guard
+# is `referee_stats.py`-SCOPED and names all five banned modules explicitly, matching the iter
+# spec's own AST-structural pattern verbatim.
+
+_REFEREE_STATS_BANNED_MODULES = (
+    "desk_playbook_detect",
+    "desk_playbook_context",
+    "desk_forward",
+    "levels",
+    "tradability",
+)
+
+
+def test_referee_stats_module_imports_none_of_the_banned_rail_detector_context_modules():
+    """TC-23: zero imports of desk_playbook_detect/desk_playbook_context/desk_forward/levels/
+    tradability inside referee_stats.py -- the stats core is estimand-agnostic (it consumes plain
+    numeric/session arrays a caller passes in, never rail/detector/context data directly)."""
+    path = _RESEARCH_DIR / "referee_stats.py"
+    assert path.exists(), "referee_stats.py not found at the expected location -- has it moved?"
+    imported = _imported_module_names(path)
+    hits: set[str] = set()
+    for banned in _REFEREE_STATS_BANNED_MODULES:
+        hits |= _mentioning(imported, banned)
+    assert not hits, f"referee_stats.py imports the banned module(s) {hits}"
+
+
+def test_referee_stats_import_ban_guard_can_fail_on_a_seeded_violation():
+    """The lint CAN fail -- a lint that cannot fail proves nothing (TC-23's own can-fail
+    counter-test)."""
+    seeded_imports = {"app.research.desk_forward", "app.research.levels", "app.research.other"}
+    hits: set[str] = set()
+    for banned in _REFEREE_STATS_BANNED_MODULES:
+        hits |= _mentioning(seeded_imports, banned)
+    assert hits == {"app.research.desk_forward", "app.research.levels"}
diff --git a/docs/referee-statistical-spec.md b/docs/referee-statistical-spec.md
index 05d4a97..74fb279 100644
--- a/docs/referee-statistical-spec.md
+++ b/docs/referee-statistical-spec.md
@@ -98,6 +98,14 @@ genuine detector revision moves `detector_basis` and honestly splits the pool. C
 honesty: each pooled record carries its per-symbol coverage; when a newest record covers
 fewer symbols than a superseded one for the same date, a served disclosure names it.
 
+**`provenance.detector_basis` is `None` for every strategy-family observation, by design.** A
+strategy trade has no detector: `detector_basis` is populated only for
+`evidence_family: "playbook_occurrence"` (the pooling identity above) and is honestly `None` on
+every `strategy_trade` observation — the same "`None` when inapplicable" convention
+`context_algorithm_version` already uses. Standing for this era per the assumption ledger
+(`state/assumptions.md`, iter-2/iter-3): a documentation clarification of the contract as
+implemented, not a new field or a redefinition of any existing one.
+
 **Completed-session rule:** a record is confirmatory-eligible for a symbol only if that
 symbol's finest measurement series reaches `REFEREE_SESSION_COMPLETE_ET` (partial mid-day
 records are exploratory-only; the session guard fails open by design, so this predicate is
diff --git a/apps/backend/app/research/referee_stats.py b/apps/backend/app/research/referee_stats.py
new file mode 100644
index 0000000..9a58746
--- /dev/null
+++ b/apps/backend/app/research/referee_stats.py
@@ -0,0 +1,711 @@
+"""Era 6 "The Referee" (J-03) — the statistics core: the calibrated, seeded, oracle-proven
+library every later Referee journey (J-04 through J-08, per ``docs/goal.md``'s stated dependency
+order) imports for its real p/CI/BH math. Implements ``docs/referee-statistical-spec.md``
+Sec1/Sec3/Sec5/Sec6 verbatim.
+
+**What this module is, and is not.** This module is estimand-agnostic: every function here
+consumes plain numeric/session arrays a caller passes in (never rail, detector, or context data
+directly) — the import-ban guard in ``tests/test_referee_guards.py`` proves this structurally.
+It does not know what a Playbook occurrence or a strategy trade is, does not read any store, and
+writes nothing anywhere. J-04 (matched nulls), J-05 (the registry), and J-06 (the estimand
+engines + adjudication) are the callers that will feed real observations through these functions;
+this iteration ships the library and its own independent oracle-proof suite
+(``tests/test_referee_oracles.py``), unconsumed by any route or caller.
+
+**The seeded-stream discipline (spec Sec0, IN SCOPE).** Every random draw in this module goes
+through ``referee_stream(...)`` — the ONE stream constructor implementing
+``REFEREE_STREAM_RECIPE`` verbatim — followed by the hand-coded partial Fisher-Yates idiom
+(``desk_forward._draw_anchor_indices``'s discipline, matched exactly by
+``_draw_indices_without_replacement`` below) for without-replacement draws, or a hand-coded
+``rng.randrange`` loop for with-replacement draws. Never ``random.sample``, never a shared/global
+``random.Random()`` instance, never numpy's RNG for any seeded draw — proven by
+``tests/test_referee_oracles.py``'s TC-1 (stream determinism) and TC-19 (stdlib-only imports).
+
+**The combined statistic ``T`` (spec Sec3.4).** Both pre-registered weight forms —
+estimand A/C's harmonic ``n_s * K_s / (n_s + K_s)`` and estimand B's
+``n1_s * n2_s / (n1_s + n2_s)`` — are the SAME formula (a group-size-1 times group-size-2 over
+their sum), so ``_t_statistic`` below implements it ONCE or the two named estimand families would
+each have their own copy — single source of truth (CLAUDE.md anti-goal 6). Every function that
+needs the combined statistic (the primary permutation test, the session-clustered bootstrap CI)
+calls this ONE helper; nothing here re-derives the formula a second way.
+
+**CI-inversion is never a p-value (T-3, the era's central trap).** ``bootstrap_ci_occurrence``
+and ``bootstrap_ci_cluster`` below produce UNCERTAINTY INTERVALS ONLY — descriptive companions,
+never a decision rule. The ONLY function in this module that produces a confirmatory p-value from
+a null-calibrated randomization procedure is ``permutation_test`` (spec Sec3.4, the primary test).
+``sign_flip_result`` also produces a p, but it is a named ROBUSTNESS DISCLOSURE (spec Sec3.5) that
+feeds only the future ``fragile`` verdict rule (J-06 builds the verdict fold) — never a substitute
+decision. ``tests/test_referee_oracles.py``'s TC-10/TC-11 demonstrate mechanically why: an
+unclustered foil over-rejects, and the sign-flip variant mis-sizes on a skewed unequal-group case
+while the primary test holds size.
+
+**The fail-closed attestation (T-8).** ``run_oracle_attestation()`` executes a pinned tiny fixture
+through two of this module's own procedures and compares the result to a pinned expected/tolerance
+pair captured from THIS build (a version/regression pin, not independent statistical proof — the
+independent proof is ``tests/test_referee_oracles.py``'s own hand-derived and simulation-based
+oracle suite, a separate and much larger exercise). ``verify_oracle_attestation`` re-derives the
+live expected/tolerance from the CURRENT build's own pinned constants and re-checks ``actual``
+against them field by field — it never trusts a stored ``passed`` flag at face value, so a
+corrupted or hand-edited attestation record is caught even if its own ``passed`` field claims
+success (TC-17).
+"""
+
+from __future__ import annotations
+
+import itertools
+import math
+import random
+import statistics
+
+__all__ = [
+    "REFEREE_SEED",
+    "REFEREE_STREAM_RECIPE",
+    "REFEREE_B",
+    "REFEREE_ENUMERATION_THRESHOLD",
+    "REFEREE_CI_LEVEL",
+    "REFEREE_MIN_CLUSTERS_FOR_CI",
+    "REFEREE_ORACLE_B",
+    "REFEREE_ORACLE_REPLICATIONS",
+    "REFEREE_ORACLE_BUDGET_SECONDS",
+    "REFEREE_ORACLE_SIZE_TOLERANCE",
+    "INSUFFICIENT_SAMPLE",
+    "STATS_CORE_VERSION",
+    "referee_stream",
+    "bootstrap_ci_occurrence",
+    "bootstrap_ci_cluster",
+    "permutation_test",
+    "sign_flip_result",
+    "equal_weight_t",
+    "benjamini_hochberg",
+    "run_oracle_attestation",
+    "verify_oracle_attestation",
+    "referee_stats_parameters",
+]
+
+# === Sec1: pre-registered constants (module constants, never Config fields; read at call time) ====
+
+REFEREE_SEED: int = 271828
+
+# The ONE stream constructor's recipe, verbatim (spec Sec1) -- documentation-as-data, the same
+# character sequence the spec's own table shows (minus the f-prefix: stored as a literal template,
+# never evaluated as an f-string). `referee_stream` below implements exactly this, piece by piece,
+# since the optional bracketed segments cannot be expressed as a single `.format()` call.
+REFEREE_STREAM_RECIPE: str = "{REFEREE_SEED}:{hypothesis_id}:{purpose}[:{session_date}[:{i}]]"
+
+REFEREE_B: int = 10_000
+REFEREE_ENUMERATION_THRESHOLD: int = 8_192
+REFEREE_CI_LEVEL: float = 0.95
+REFEREE_MIN_CLUSTERS_FOR_CI: int = 8
+REFEREE_ORACLE_B: int = 2_000
+REFEREE_ORACLE_REPLICATIONS: int = 400
+REFEREE_ORACLE_BUDGET_SECONDS: int = 120
+
+# The `[0.5*alpha, 1.5*alpha]` calibration acceptance band at alpha=0.05 (spec Sec1) -- a plain
+# 2-tuple, not a dataclass: every caller in this file and its test suite reads it positionally
+# (`lo, hi = REFEREE_ORACLE_SIZE_TOLERANCE`), and a 2-element tuple is the whole shape.
+REFEREE_ORACLE_SIZE_TOLERANCE: tuple[float, float] = (0.025, 0.075)
+
+# The five purposes `REFEREE_STREAM_RECIPE` names, verbatim (spec Sec1) -- referee_stream() rejects
+# any other value rather than silently minting an un-auditable stream namespace.
+_REFEREE_STREAM_PURPOSES: frozenset[str] = frozenset(
+    {"null-draw", "perm", "flip", "boot-occ", "boot-cluster"}
+)
+
+# The literal sentinel state served in place of a fabricated interval/verdict whenever a floor is
+# unmet (spec Sec3.6, Sec5) -- a plain string, never an exception, never a null masquerading as a
+# real interval.
+INSUFFICIENT_SAMPLE: str = "insufficient_sample"
+
+# This module's own version, embedded in every attestation record (spec Sec6) -- bumped only on a
+# genuine algorithmic revision to this file (a named revision, never silently).
+STATS_CORE_VERSION: str = "referee-stats-v1"
+
+# z_{1-alpha} at alpha = 1 - REFEREE_CI_LEVEL (spec Sec3.6's MDE formula) -- derived from stdlib's
+# own `statistics.NormalDist` (available since Python 3.8; a documented, deterministic rational
+# approximation, not a hand-typed magic literal and not scipy) rather than hand-pinning the
+# standard-normal quantile as a bare float.
+_Z_ONE_SIDED: float = statistics.NormalDist().inv_cdf(REFEREE_CI_LEVEL)
+
+
+# === Sec0: the seeded per-row stream constructor ====================================================
+
+
+def referee_stream(
+    hypothesis_id: str,
+    purpose: str,
+    session_date: str | None = None,
+    i: int | str | None = None,
+) -> random.Random:
+    """The ONE stream constructor (spec Sec1's ``REFEREE_STREAM_RECIPE``, implemented verbatim):
+    ``f"{REFEREE_SEED}:{hypothesis_id}:{purpose}[:{session_date}[:{i}]]"``. ``i`` is only ever
+    meaningful nested inside a ``session_date`` (the recipe's own bracket nesting) -- passing ``i``
+    without ``session_date`` is rejected rather than silently building an unintended key. Two calls
+    with identical arguments always build the identical key string, so
+    ``random.Random(identical_key)`` always reproduces the identical draw sequence (TC-1) --
+    ``random.Random``'s own documented guarantee for a given CPython version/seed."""
+    if purpose not in _REFEREE_STREAM_PURPOSES:
+        raise ValueError(
+            f"referee_stream: unknown purpose {purpose!r}, expected one of "
+            f"{sorted(_REFEREE_STREAM_PURPOSES)}"
+        )
+    if i is not None and session_date is None:
+        raise ValueError("referee_stream: `i` requires `session_date` (the recipe's own nesting)")
+    key = f"{REFEREE_SEED}:{hypothesis_id}:{purpose}"
+    if session_date is not None:
+        key += f":{session_date}"
+        if i is not None:
+            key += f":{i}"
+    return random.Random(key)
+
+
+# --- hand-coded draw primitives (never random.sample, never a global/unseeded RNG) -------------------
+
+
+def _draw_indices_without_replacement(rng: random.Random, population: int, k: int) -> list[int]:
+    """``k`` distinct indices from ``range(population)`` via the explicitly-coded partial
+    Fisher-Yates over ``rng.randrange`` -- ``desk_forward._draw_anchor_indices``'s exact idiom,
+    matched here rather than imported (the import-ban guard: this module never imports
+    ``desk_forward``). Callers never pass ``k > population`` (the identical implicit contract
+    ``_draw_anchor_indices`` itself carries)."""
+    pool = list(range(population))
+    for idx in range(k):
+        j = rng.randrange(idx, population)
+        pool[idx], pool[j] = pool[j], pool[idx]
+    return sorted(pool[:k])
+
+
+def _draw_indices_with_replacement(rng: random.Random, population: int, k: int) -> list[int]:
+    """``k`` indices from ``range(population)``, WITH replacement -- the bootstrap resampling
+    primitive. A plain hand-coded ``rng.randrange`` loop, never ``random.choices`` (a stdlib
+    convenience whose own internal algorithm is not the pinned discipline)."""
+    return [rng.randrange(population) for _ in range(k)]
+
+
+# --- the percentile helper (stdlib-only; linear interpolation, numpy's own default convention) ------
+
+
+def _percentile(sorted_values: list[float], q: float) -> float:
+    """The ``q``-th percentile (``q`` in ``[0, 1]``) of an ALREADY-SORTED list via linear
+    interpolation between the two bracketing order statistics -- the same convention numpy's own
+    default ``'linear'`` method uses, reimplemented here in stdlib-only arithmetic (TC-19: this
+    module imports no numpy at all)."""
+    n = len(sorted_values)
+    if n == 1:
+        return sorted_values[0]
+    pos = q * (n - 1)
+    lo = math.floor(pos)
+    hi = math.ceil(pos)
+    if lo == hi:
+        return sorted_values[int(pos)]
+    frac = pos - lo
+    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac
+
+
+def _stdev(values: list[float]) -> float:
+    """Sample standard deviation (``n - 1`` denominator) via ``math.fsum``-class accumulation
+    (spec Sec0's determinism convention) -- ``0.0`` below ``n=2`` (a degenerate, never-crashing
+    absence rather than a ``ZeroDivisionError``)."""
+    n = len(values)
+    if n < 2:
+        return 0.0
+    mean = math.fsum(values) / n
+    variance = math.fsum((v - mean) ** 2 for v in values) / (n - 1)
+    return math.sqrt(variance)
+
+
+# === Sec3.4: the combined statistic T (shared by the primary test and the clustered CI) =============
+
+
+def _t_statistic(
+    session_groups: dict[str, tuple[list[float], list[float]]],
+    *,
+    equal_weight: bool = False,
+) -> tuple[float, dict[str, float], dict[str, float]]:
+    """``T = sum_s(w_s * delta_s) / sum_s(w_s)`` (spec Sec3.4) over INFORMATIVE sessions only (both
+    groups non-empty; a caller that has not already filtered gets a defensive re-filter here, never
+    a ``ZeroDivisionError``). ``w_s = n1_s * n2_s / (n1_s + n2_s)`` -- the ONE formula both
+    pre-registered weight forms (A/C's harmonic ``n_s * K_s / (n_s + K_s)``; B's
+    ``n1_s * n2_s / (n1_s + n2_s)``) reduce to, so estimand A/B/C all share this single
+    implementation. ``equal_weight=True`` is the Sec3.5 robustness variant (``w_s = 1`` for every
+    session). Returns ``(T, delta_by_session, weight_by_session)`` -- the per-session components are
+    returned too, since ``permutation_test``/``sign_flip_result`` reuse them directly rather than
+    recomputing."""
+    deltas: dict[str, float] = {}
+    weights: dict[str, float] = {}
+    for session, (group1, group2) in session_groups.items():
+        n1, n2 = len(group1), len(group2)
+        if n1 == 0 or n2 == 0:
+            continue
+        deltas[session] = math.fsum(group1) / n1 - math.fsum(group2) / n2
+        weights[session] = 1.0 if equal_weight else (n1 * n2) / (n1 + n2)
+    total_weight = math.fsum(weights.values())
+    if total_weight == 0.0:
+        return 0.0, deltas, weights
+    t = math.fsum(weights[s] * deltas[s] for s in deltas) / total_weight
+    return t, deltas, weights
+
+
+def _informative_sessions(
+    session_groups: dict[str, tuple[list[float], list[float]]],
+) -> dict[str, tuple[list[float], list[float]]]:
+    """Sessions carrying BOTH groups (spec Sec3.1/Sec3.2's "informative session" definition) --
+    one-group sessions contribute nothing and are silently dropped here (the caller may count them
+    separately from the ORIGINAL ``session_groups`` it passed in; this module does not own that
+    disclosure)."""
+    return {
+        session: (list(group1), list(group2))
+        for session, (group1, group2) in session_groups.items()
+        if group1 and group2
+    }
+
+
+def _is_extreme(t_star: float, t_obs: float, sidedness: str) -> bool:
+    if sidedness == "greater":
+        return t_star >= t_obs
+    if sidedness == "less":
+        return t_star <= t_obs
+    return abs(t_star) >= abs(t_obs)
+
+
+_SIDEDNESS_VALUES = frozenset({"greater", "less", "two-sided"})
+
+
+# === Sec3.6: percentile bootstrap confidence intervals ===============================================
+
+
+def bootstrap_ci_occurrence(
+    values: list[float],
+    hypothesis_id: str,
+    *,
+    ci_level: float = REFEREE_CI_LEVEL,
+    b: int = REFEREE_B,
+) -> dict:
+    """Occurrence-level percentile bootstrap CI (spec Sec3.6): resample ``values`` (the caller's
+    already-computed paired per-occurrence differences) WITH replacement, ``b`` seeded draws
+    (``purpose="boot-occ"``, one flat stream for the whole call -- no session structure at this
+    level), take the percentile bounds of the resampled means. Descriptive only: this function
+    returns an uncertainty interval, never a p-value (T-3)."""
+    n = len(values)
+    if n == 0:
+        return {"state": INSUFFICIENT_SAMPLE, "n": 0}
+    stream = referee_stream(hypothesis_id, "boot-occ")
+    means: list[float] = []
+    for _ in range(b):
+        idx = _draw_indices_with_replacement(stream, n, n)
+        means.append(math.fsum(values[i] for i in idx) / n)
+    means.sort()
+    lo_q = (1.0 - ci_level) / 2.0
+    hi_q = 1.0 - lo_q
+    return {
+        "state": "ok",
+        "n": n,
+        "point_estimate": math.fsum(values) / n,
+        "ci_level": ci_level,
+        "ci_low": _percentile(means, lo_q),
+        "ci_high": _percentile(means, hi_q),
+        "b": b,
+    }
+
+
+def bootstrap_ci_cluster(
+    session_groups: dict[str, tuple[list[float], list[float]]],
+    hypothesis_id: str,
+    *,
+    ci_level: float = REFEREE_CI_LEVEL,
+    b: int = REFEREE_B,
+    min_clusters: int = REFEREE_MIN_CLUSTERS_FOR_CI,
+) -> dict:
+    """Session-clustered percentile bootstrap CI (spec Sec3.6): resample INFORMATIVE sessions WITH
+    replacement (``purpose="boot-cluster"``) -- a drawn session carries ALL its own observations
+    (both groups), and the statistic recomputed on each resample is ``T`` (``_t_statistic``, the
+    SAME combined statistic the primary test uses). Below ``min_clusters`` informative sessions,
+    returns the literal ``insufficient_sample`` state, never a fabricated interval (TC-3). MDE
+    (``z_{1-alpha} * sd*(T)``) is served as the power disclosure alongside the interval."""
+    informative = _informative_sessions(session_groups)
+    n_clusters = len(informative)
+    if n_clusters < min_clusters:
+        return {
+            "state": INSUFFICIENT_SAMPLE,
+            "n_clusters": n_clusters,
+            "min_clusters_required": min_clusters,
+        }
+    t_point, _deltas, _weights = _t_statistic(informative)
+    sessions = sorted(informative)
+    stream = referee_stream(hypothesis_id, "boot-cluster")
+    t_stars: list[float] = []
+    for _ in range(b):
+        draw = _draw_indices_with_replacement(stream, n_clusters, n_clusters)
+        resample = {
+            f"{sessions[picked]}#{slot}": informative[sessions[picked]]
+            for slot, picked in enumerate(draw)
+        }
+        t_star, _d, _w = _t_statistic(resample)
+        t_stars.append(t_star)
+    t_stars.sort()
+    lo_q = (1.0 - ci_level) / 2.0
+    hi_q = 1.0 - lo_q
+    return {
+        "state": "ok",
+        "n_clusters": n_clusters,
+        "point_estimate": t_point,
+        "ci_level": ci_level,
+        "ci_low": _percentile(t_stars, lo_q),
+        "ci_high": _percentile(t_stars, hi_q),
+        "mde": _Z_ONE_SIDED * _stdev(t_stars),
+        "b": b,
+    }
+
+
+# === Sec3.4: the primary test -- within-session group-label permutation ("referee-test-perm-v1") ====
+
+
+def permutation_test(
+    session_groups: dict[str, tuple[list[float], list[float]]],
+    hypothesis_id: str,
+    *,
+    sidedness: str = "greater",
+    b: int = REFEREE_B,
+    enumeration_threshold: int = REFEREE_ENUMERATION_THRESHOLD,
+) -> dict:
+    """The primary confirmatory test (spec Sec3.4): independently WITHIN each informative session,
+    permute the group labels among that session's pooled eligible observations, PRESERVING group
+    sizes; recompute ``T*`` (``_t_statistic``); ``p = (1 + #{T* extreme}) / (draws + 1)`` (the
+    Phipson-Smyth ``+1`` convention, applied uniformly whether ``draws`` is the exact enumerated
+    space size or ``b`` seeded draws -- spec Sec3.4 states the one formula without a branch-specific
+    carve-out). Full enumeration when the total per-session-combination product is
+    ``<= enumeration_threshold`` (deterministic, zero RNG calls -- TC-4); otherwise exactly ``b``
+    seeded draws via independent PER-SESSION sub-streams (``purpose="perm"``, keyed by
+    ``session_date`` -- TC-5). Exact under within-session exchangeability of labels for ANY
+    group-size ratio and ANY skew (spec's own validity argument) -- this is why it is primary and
+    the session-level sign-flip (``sign_flip_result``) is not."""
+    if sidedness not in _SIDEDNESS_VALUES:
+        raise ValueError(f"permutation_test: unknown sidedness {sidedness!r}")
+    informative = _informative_sessions(session_groups)
+    if not informative:
+        return {"state": INSUFFICIENT_SAMPLE, "n_informative_sessions": 0}
+
+    t_obs, deltas, weights = _t_statistic(informative)
+    total_weight = math.fsum(weights.values())
+    sessions = sorted(informative)
+
+    # Per-session pooled values (group1 first, so its own TRUE membership is index 0..n1-1 --
+    # `_draw_indices_without_replacement`/`itertools.combinations` both then reproduce the OBSERVED
+    # grouping as one legitimate member of the enumerated/sampled space), plus what stays CONSTANT
+    # across every draw for that session.
... [diff_bound] apps/backend/app/research/referee_stats.py: 317 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_referee_oracles.py b/apps/backend/tests/test_referee_oracles.py
new file mode 100644
index 0000000..ef77a07
--- /dev/null
+++ b/apps/backend/tests/test_referee_oracles.py
@@ -0,0 +1,449 @@
+"""``referee_stats.py`` (Era 6 "The Referee", J-03) — the seeded oracle suite, per
+``docs/referee-statistical-spec.md`` Sec6. Test-first contract: TC-8 through TC-15, TC-18 in
+``docs/phases/goal-referee-iter-3.md``. This suite, not any fixture-only unit test, IS the
+acceptance for the statistics core (goal.md's own J-03 Acceptance sentence: "fixture-only tests
+prove nothing at small n").
+
+**What makes this an oracle, not a fixture test.** Every case below runs ``REFEREE_ORACLE_
+REPLICATIONS`` (400) independent simulated datasets through the module under test and checks a
+LONG-RUN, KNOWN-BY-CONSTRUCTION property of the resulting empirical rejection rate (or coverage
+rate) — never a single hand-typed input/output pair. The data GENERATORS below are written from
+scratch in this file (seeded ``random.Random`` instances distinct from ``referee_stream`` — this
+is TEST DATA GENERATION, not a referee statistical draw), and the DEMONSTRATED-FAILURE foils
+(case 3's unclustered pooled foil, the sign-flip-as-decision misuse, the mutation fixture) are
+each independently implemented HERE, never by calling into `referee_stats.py`'s own primary-test
+code path with a flag flipped — so a bug in the primary implementation could not accidentally also
+break its own foil in a way that hides the intended demonstrated failure.
+
+**Runtime budget (TC-18).** ``_oracle_suite_budget_guard`` below is a module-scoped, autouse
+fixture whose teardown (running once, after every test in this file has completed) asserts the
+WHOLE FILE's cumulative wall-clock time is <= ``REFEREE_ORACLE_BUDGET_SECONDS`` — the
+``test_dense_replay_gate.py::test_unpaced_replay_within_config_time_budget`` self-timing pattern,
+applied at file scope instead of a single call.
+
+**Case-to-test mapping (spec Sec6):**
+  1. Size, iid skewed (lognormal-shifted-to-zero-mean, n_s=1, K=4)      -> TC-8
+  2. Size, heavy-tailed (Student-t(3))                                  -> TC-9
+  3a. The unclustered pooled-label permutation foil over-rejects        -> TC-10
+  3b. The session-level sign-flip mis-sizes on a skewed unequal case    -> TC-11
+  4. Power at a +0.5*sd shift, S=40                                     -> TC-12
+  5. The 20-null + 1-positive BH sweep                                  -> TC-13
+  6. CI coverage at S=40, and the S=6 insufficient_sample case          -> TC-14
+  Mutation fixture (a mis-implemented test statistic fails calibration) -> TC-15
+"""
+
+from __future__ import annotations
+
+import math
+import random
+import time
+
+import pytest
+
+from app.research.referee_stats import (
+    REFEREE_ORACLE_B,
+    REFEREE_ORACLE_REPLICATIONS,
+    REFEREE_ORACLE_SIZE_TOLERANCE,
+    REFEREE_ORACLE_BUDGET_SECONDS,
+    _informative_sessions,
+    _is_extreme,
+    _t_statistic,
+    benjamini_hochberg,
+    bootstrap_ci_cluster,
+    permutation_test,
+    sign_flip_result,
+)
+
+ALPHA = 0.05
+_TOLERANCE_LOW, _TOLERANCE_HIGH = REFEREE_ORACLE_SIZE_TOLERANCE
+
+
+@pytest.fixture(scope="module", autouse=True)
+def _oracle_suite_budget_guard():
+    """TC-18: this FILE's own cumulative wall-clock time -- from the first test's setup through
+    the last test's teardown -- must not exceed ``REFEREE_ORACLE_BUDGET_SECONDS``. The start time
+    is captured HERE (in the fixture's own setup, before ``yield``), not at module import: a
+    module-scoped fixture's setup runs lazily, right before the first test in THIS module that
+    needs it -- never at collection time. Timing from module import instead would wrongly charge
+    this budget for however long pytest spent collecting/running every OTHER file first when this
+    suite runs as part of the full backend suite rather than in isolation (the bug an earlier
+    version of this fixture had: it captured ``_SUITE_START`` as a module-level assignment,
+    evaluated at import/collection time)."""
+    start = time.perf_counter()
+    yield
+    elapsed = time.perf_counter() - start
+    assert elapsed <= REFEREE_ORACLE_BUDGET_SECONDS, (
+        f"the oracle suite took {elapsed:.1f}s, over its {REFEREE_ORACLE_BUDGET_SECONDS}s budget"
+    )
+
+
+# === Data generators (test infrastructure -- seeded, but NOT `referee_stream`-scoped; these build
+# synthetic INPUT datasets fed into the module under test, never a referee statistical draw) =========
+
+
+def _lognormal_shifted_to_zero_mean(rng: random.Random, mu: float = 0.0, sigma: float = 1.0) -> float:
+    """A lognormal draw re-centered to mean zero: ``lognormvariate(mu, sigma) - E[lognormal]``,
+    ``E[lognormal] = exp(mu + sigma**2/2)`` (the closed-form lognormal mean). Right-skewed."""
+    return rng.lognormvariate(mu, sigma) - math.exp(mu + sigma**2 / 2.0)
+
+
+def _student_t(rng: random.Random, df: int = 3) -> float:
+    """A Student-t(df) draw via the standard normal-over-sqrt(chi-square/df) construction, using
+    only stdlib `random.gauss`/`random.gammavariate` (chi-square(df) == gamma(df/2, scale=2)) --
+    heavy-tailed, mean zero for df > 1."""
+    z = rng.gauss(0.0, 1.0)
+    chi2 = rng.gammavariate(df / 2.0, 2.0)
+    return z / math.sqrt(chi2 / df)
+
+
+def _iid_session_groups(rng, s, n1, k, generator, mean1=0.0, mean2=0.0):
+    """``s`` sessions, each an INDEPENDENT draw (no shared per-session structure): ``n1`` group1
+    values and ``k`` group2 values, ``generator(rng) + mean`` per value."""
+    sg = {}
+    for i in range(s):
+        g1 = [mean1 + generator(rng) for _ in range(n1)]
+        g2 = [mean2 + generator(rng) for _ in range(k)]
+        sg[f"s{i:04d}"] = (g1, g2)
+    return sg
+
+
+def _regime_clustered_session_groups(rng, s, n1, n2, regime_sd, noise_sd):
+    """``s`` sessions; EACH session draws its own ``regime_s ~ N(0, regime_sd)`` shared by BOTH
+    groups equally (so it cancels exactly in the within-session ``delta_s`` -- keeping the PRIMARY
+    within-session test calibrated), plus independent per-value Gaussian noise. A pure null (no
+    population-level mean difference either way) -- the "shared per-session regime shifts" the
+    spec's case 3 names."""
+    sg = {}
+    for i in range(s):
+        regime = rng.gauss(0.0, regime_sd)
+        g1 = [regime + rng.gauss(0.0, noise_sd) for _ in range(n1)]
+        g2 = [regime + rng.gauss(0.0, noise_sd) for _ in range(n2)]
+        sg[f"s{i:04d}"] = (g1, g2)
+    return sg
+
+
+def _empirical_rejection_rate(p_values: list[float], alpha: float = ALPHA) -> float:
+    return sum(1 for p in p_values if p <= alpha) / len(p_values)
+
+
+# === Case 1 (TC-8): size, iid skewed (lognormal-shifted-to-zero-mean, n_s=1, K=4) ====================
+
+
+def test_oracle_case1_size_iid_skewed_lognormal_holds_calibration():
+    """TC-8: 400 independent seeded replications, each S=16 sessions of n_s=1/K=4
+    lognormal-shifted-to-zero-mean occurrence/anchor values (a pure null: both groups drawn from
+    the identical zero-mean generator, independently -- no true effect). The empirical rejection
+    rate at alpha=0.05 must fall inside ``REFEREE_ORACLE_SIZE_TOLERANCE``."""
+    gen_rng = random.Random("oracle-case1-lognormal-seed")
+    p_values = []
+    for rep in range(REFEREE_ORACLE_REPLICATIONS):
+        sg = _iid_session_groups(gen_rng, 16, 1, 4, _lognormal_shifted_to_zero_mean)
+        result = permutation_test(sg, f"oracle-case1-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
+        p_values.append(result["p"])
+    rate = _empirical_rejection_rate(p_values)
+    assert _TOLERANCE_LOW <= rate <= _TOLERANCE_HIGH, (
+        f"case 1 (iid skewed) rejection rate {rate:.4f} outside "
+        f"[{_TOLERANCE_LOW}, {_TOLERANCE_HIGH}]"
+    )
+
+
+# === Case 2 (TC-9): size, heavy-tailed (Student-t(3)) =================================================
+
+
+def test_oracle_case2_size_heavy_tailed_student_t_holds_calibration():
+    """TC-9: identical structure to case 1, generator swapped for Student-t(3) (heavy-tailed, mean
+    zero)."""
+    gen_rng = random.Random("oracle-case2-student-t-seed")
+    p_values = []
+    for rep in range(REFEREE_ORACLE_REPLICATIONS):
+        sg = _iid_session_groups(gen_rng, 16, 1, 4, _student_t)
+        result = permutation_test(sg, f"oracle-case2-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
+        p_values.append(result["p"])
+    rate = _empirical_rejection_rate(p_values)
+    assert _TOLERANCE_LOW <= rate <= _TOLERANCE_HIGH, (
+        f"case 2 (heavy-tailed) rejection rate {rate:.4f} outside "
+        f"[{_TOLERANCE_LOW}, {_TOLERANCE_HIGH}]"
+    )
+
+
+# === Case 3a (TC-10): the unclustered pooled-label permutation foil over-rejects =====================
+
+
+def _unclustered_pseudoreplicated_foil_p(
+    session_groups: dict[str, tuple[list[float], list[float]]], seed: str, b: int
+) -> float:
+    """The DEMONSTRATED WRONG procedure (spec Sec6 case 3a), implemented independently of
+    ``permutation_test`` (never calls it, never imports its internals): the classic
+    pseudo-replication mistake. For EVERY session, compute ALL pairwise (occurrence - anchor)
+    differences (``n_s * K_s`` of them, ALL sharing that session's regime shock -- heavily
+    correlated); pool these pairwise differences across EVERY session as if they were independent
+    draws; test whether the pooled mean differs from zero via a naive sign-flip permutation over
+    the POOLED, UNCLUSTERED set. This ignores that entire blocks of pooled differences move
+    together (one shared per-session regime draw), understating the true variance and
+    over-rejecting."""
+    pooled_diffs: list[float] = []
+    for group1, group2 in session_groups.values():
+        for occurrence in group1:
+            for anchor in group2:
+                pooled_diffs.append(occurrence - anchor)
+    n = len(pooled_diffs)
+    t_obs = sum(pooled_diffs) / n
+    rng = random.Random(seed)
+    extreme = 0
+    for _ in range(b):
+        acc = 0.0
+        for diff in pooled_diffs:
+            acc += diff if rng.random() < 0.5 else -diff
+        if (acc / n) >= t_obs:
+            extreme += 1
+    return (1 + extreme) / (b + 1)
+
+
+def test_oracle_case3a_unclustered_foil_over_rejects_while_primary_holds_size():
+    """TC-10: a session-clustered null (shared per-session regime, cancelling exactly within each
+    session's own delta_s -- the primary test's own within-session pairing handles it correctly).
+    The PRIMARY test must hold size; the UNCLUSTERED pseudo-replicated foil, run on the IDENTICAL
+    400 datasets, must over-reject (rate ABOVE the tolerance band's ceiling) -- the recorded
+    evidence for why within-session permutation is the primary test."""
+    gen_rng = random.Random("oracle-case3a-regime-seed")
+    primary_p_values = []
+    foil_p_values = []
+    for rep in range(REFEREE_ORACLE_REPLICATIONS):
+        sg = _regime_clustered_session_groups(gen_rng, 20, 3, 3, regime_sd=2.0, noise_sd=0.3)
+        primary = permutation_test(sg, f"oracle-case3a-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
+        primary_p_values.append(primary["p"])
+        foil_p_values.append(
+            _unclustered_pseudoreplicated_foil_p(sg, f"oracle-case3a-foil-{rep}", b=REFEREE_ORACLE_B)
+        )
+
+    primary_rate = _empirical_rejection_rate(primary_p_values)
+    foil_rate = _empirical_rejection_rate(foil_p_values)
+
+    assert _TOLERANCE_LOW <= primary_rate <= _TOLERANCE_HIGH, (
+        f"the PRIMARY within-session test should hold size on the clustered null; got "
+        f"{primary_rate:.4f}"
+    )
+    assert foil_rate > _TOLERANCE_HIGH, (
+        f"the unclustered foil should OVER-reject (> {_TOLERANCE_HIGH}); got {foil_rate:.4f} -- "
+        "the demonstrated failure did not manifest"
+    )
+
+
+# === Case 3b (TC-11): the session-level sign-flip mis-sizes on a skewed n_s=1/K=3 case ================
+
+
+def test_oracle_case3b_sign_flip_mis_sizes_while_primary_holds_size():
+    """TC-11: a skewed (lognormal, sigma=2.0), unequal-group (n_s=1, K=3) one-sided fixture. The
+    session-level sign-flip variant, run AS IF it were the decision rule, must fall OUTSIDE the
+    tolerance band (mis-sized); the true within-session permutation, on the SAME 400 datasets in
+    the SAME test run, must hold size (inside the band)."""
+    gen_rng = random.Random("oracle-case3b-skew-seed")
+    primary_p_values = []
+    flip_p_values = []
+    for rep in range(REFEREE_ORACLE_REPLICATIONS):
+        sg = _iid_session_groups(
+            gen_rng, 16, 1, 3, lambda r: _lognormal_shifted_to_zero_mean(r, 0.0, 2.0)
+        )
+        primary = permutation_test(sg, f"oracle-case3b-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
+        primary_p_values.append(primary["p"])
+        flip = sign_flip_result(sg, f"oracle-case3b-flip-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
+        flip_p_values.append(flip["p"])
+
+    primary_rate = _empirical_rejection_rate(primary_p_values)
+    flip_rate = _empirical_rejection_rate(flip_p_values)
+
+    assert _TOLERANCE_LOW <= primary_rate <= _TOLERANCE_HIGH, (
+        f"the PRIMARY within-session permutation should hold size; got {primary_rate:.4f}"
+    )
+    assert not (_TOLERANCE_LOW <= flip_rate <= _TOLERANCE_HIGH), (
+        f"the sign-flip variant should MIS-SIZE (fall outside "
+        f"[{_TOLERANCE_LOW}, {_TOLERANCE_HIGH}]) on this skewed unequal-group case; got "
+        f"{flip_rate:.4f} -- the demonstrated failure did not manifest"
+    )
+
+
+# === Case 4 (TC-12): power at a +0.5*sd location shift, S=40 ==========================================
+
+# Captured from THIS build via the exact generator/seed below (a pinned golden, not a gate --
+# spec Sec6 case 4: "rejection rate reported and pinned as a golden"). Reproducing this file's own
+# generator with the SAME seed and SAME REFEREE_ORACLE_B/REFEREE_ORACLE_REPLICATIONS values always
+# reproduces this exact number (fully seeded, zero wall-clock dependence).
+_CASE4_POWER_GOLDEN = 0.8950
+_CASE4_POWER_TOLERANCE = 0.05
+
+
+def test_oracle_case4_power_at_half_sd_shift_matches_the_pinned_golden():
+    """TC-12: a +0.5*sd location shift (occurrence mean 0.5, anchor mean 0.0, both sd=1.0) at
+    S=40 informative sessions (n_s=1, K=4) -- the reported rejection rate must match the pinned
+    golden within its stated tolerance."""
+    gen_rng = random.Random("oracle-case4-power-seed")
+    p_values = []
+    for rep in range(REFEREE_ORACLE_REPLICATIONS):
+        sg = _iid_session_groups(gen_rng, 40, 1, 4, lambda r: r.gauss(0.0, 1.0), mean1=0.5, mean2=0.0)
+        result = permutation_test(sg, f"oracle-case4-{rep}", sidedness="greater", b=REFEREE_ORACLE_B)
+        p_values.append(result["p"])
+    rate = _empirical_rejection_rate(p_values)
+    assert abs(rate - _CASE4_POWER_GOLDEN) <= _CASE4_POWER_TOLERANCE, (
+        f"case 4 power {rate:.4f} does not match the pinned golden "
+        f"{_CASE4_POWER_GOLDEN} within {_CASE4_POWER_TOLERANCE}"
+    )
+    # A meaningful power golden: comfortably above alpha AND well below certainty (a real,
+    # informative power figure, not a degenerate 0 or 1).
+    assert 0.5 < rate < 1.0
+
+
+# === Case 5 (TC-13): the 20-null + 1-positive BH sweep =================================================
+
+_CASE5_N_NULL = 20
+_CASE5_SESSIONS_PER_HYPOTHESIS = 10
+_CASE5_Q = 0.10
+# Pinned goldens (captured from THIS build's own seeded run, spec Sec6 case 5: "matching the
+# pinned golden"). The false-admission rate is a per-null-CANDIDATE rate across all
+# REFEREE_ORACLE_REPLICATIONS * 20 null opportunities; the positive-admission rate is a
+# per-REPLICATION rate.
+_CASE5_FALSE_ADMISSION_GOLDEN = 0.0114
+_CASE5_FALSE_ADMISSION_TOLERANCE = 0.03
+_CASE5_POSITIVE_ADMITTED_GOLDEN = 0.9375
+_CASE5_POSITIVE_ADMITTED_TOLERANCE = 0.10
+
+
+def _case5_hypothesis_session_groups(rng, mean1):
+    return _iid_session_groups(
+        rng, _CASE5_SESSIONS_PER_HYPOTHESIS, 1, 4, lambda r: r.gauss(0.0, 1.0), mean1=mean1
+    )
+
+
+def test_oracle_case5_bh_sweep_admits_the_positive_and_controls_false_admissions():
+    """TC-13: per replication, 20 known-null candidates (no true shift) plus 1 known-positive
+    candidate (a strong +1.5 shift, needed for power at this case's deliberately small
+    per-hypothesis S=10) are each evaluated through the primary permutation test, then BH at
+    q=0.10 is applied to the family's m=21 checkpoint p-values. Across
+    REFEREE_ORACLE_REPLICATIONS replications: the false-admission rate (fraction of the 20*400
+    known-null opportunities that BH corroborates) stays within its binomial tolerance band of the
+    pinned golden, and the known-positive is admitted in the large majority of replications,
+    matching its own pinned golden."""
+    gen_rng = random.Random("oracle-case5-bh-sweep-seed")
+    false_admissions = 0
+    total_null_opportunities = 0
+    positive_admitted = 0
+    for rep in range(REFEREE_ORACLE_REPLICATIONS):
+        p_values = []
+        for null_idx in range(_CASE5_N_NULL):
+            sg = _case5_hypothesis_session_groups(gen_rng, mean1=0.0)
+            result = permutation_test(
+                sg, f"oracle-case5-null-{rep}-{null_idx}", sidedness="greater", b=REFEREE_ORACLE_B
+            )
+            p_values.append(result["p"])
+        sg_positive = _case5_hypothesis_session_groups(gen_rng, mean1=1.5)
+        positive_result = permutation_test(
+            sg_positive, f"oracle-case5-positive-{rep}", sidedness="greater", b=REFEREE_ORACLE_B
+        )
+        p_values.append(positive_result["p"])
+
+        bh = benjamini_hochberg(p_values, q=_CASE5_Q)
+        assert bh["m"] == _CASE5_N_NULL + 1
+        false_admissions += sum(1 for i in range(_CASE5_N_NULL) if bh["bh_pass"][i])
+        total_null_opportunities += _CASE5_N_NULL
+        if bh["bh_pass"][_CASE5_N_NULL]:
+            positive_admitted += 1
+
+    false_admission_rate = false_admissions / total_null_opportunities
+    positive_admitted_rate = positive_admitted / REFEREE_ORACLE_REPLICATIONS
+
+    assert false_admission_rate <= _CASE5_Q, (
+        f"false-admission rate {false_admission_rate:.4f} exceeds the family q={_CASE5_Q}"
+    )
+    assert abs(false_admission_rate - _CASE5_FALSE_ADMISSION_GOLDEN) <= _CASE5_FALSE_ADMISSION_TOLERANCE
+    assert positive_admitted_rate > 0.5, (
+        f"the known-positive should be admitted in the LARGE MAJORITY of replications; got "
+        f"{positive_admitted_rate:.4f}"
+    )
+    assert (
+        abs(positive_admitted_rate - _CASE5_POSITIVE_ADMITTED_GOLDEN)
+        <= _CASE5_POSITIVE_ADMITTED_TOLERANCE
+    )
+
+
+# === Case 6 (TC-14): CI coverage at S=40, and the S=6 insufficient_sample case ========================
+
+_CASE6_TRUE_EFFECT = 0.3
+_CASE6_COVERAGE_FLOOR = 0.88  # a wide but meaningful floor around the target 95% (400 reps' own
+# binomial noise at ~93-95% observed coverage; a badly miscalibrated CI would show coverage far
+# below this, e.g. 50-70%).
+
+
+def test_oracle_case6_clustered_ci_covers_the_true_effect_at_s40():
+    """TC-14 (S=40 half): 400 replications, each S=40 sessions (n_s=1, K=4) with a KNOWN true
+    session-mean effect (occurrence mean 0.3, anchor mean 0.0). The fraction of replications whose
+    clustered percentile CI contains the true effect (0.3) must be close to the nominal 95% level
+    (within a wide, meaningful tolerance -- a genuinely broken CI would show coverage far below
+    this floor, not a few points under 95%)."""
+    gen_rng = random.Random("oracle-case6-coverage-seed")
+    covered = 0
+    for rep in range(REFEREE_ORACLE_REPLICATIONS):
+        sg = _iid_session_groups(
+            gen_rng, 40, 1, 4, lambda r: r.gauss(0.0, 1.0), mean1=_CASE6_TRUE_EFFECT, mean2=0.0
+        )
+        ci = bootstrap_ci_cluster(sg, f"oracle-case6-{rep}", b=REFEREE_ORACLE_B)
+        assert ci["state"] == "ok"
+        if ci["ci_low"] <= _CASE6_TRUE_EFFECT <= ci["ci_high"]:
+            covered += 1
+    coverage_rate = covered / REFEREE_ORACLE_REPLICATIONS
+    assert coverage_rate >= _CASE6_COVERAGE_FLOOR, (
+        f"clustered CI coverage {coverage_rate:.4f} below the {_CASE6_COVERAGE_FLOOR} floor"
+    )
... [diff_bound] apps/backend/tests/test_referee_oracles.py: 55 more diff lines omitted — Read the file for full detail
diff --git a/apps/backend/tests/test_referee_stats.py b/apps/backend/tests/test_referee_stats.py
new file mode 100644
index 0000000..18c9c7b
--- /dev/null
+++ b/apps/backend/tests/test_referee_stats.py
@@ -0,0 +1,551 @@
+"""``referee_stats.py`` (Era 6 "The Referee", J-03) — the statistics core's own mechanics: fast,
+deterministic, hand-derivable unit tests. Test-first contract: TC-1 through TC-7, TC-16, TC-17,
+TC-19 in ``docs/phases/goal-referee-iter-3.md``. The CALIBRATION/oracle suite (TC-8 through
+TC-15, TC-18 — the six spec Sec6 cases plus the mutation fixture, all seeded simulations that must
+fit inside ``REFEREE_ORACLE_BUDGET_SECONDS``) lives separately in ``test_referee_oracles.py``, so
+this file's own tests stay fast and this file never risks the runtime budget.
+
+Every expected value below is derived independently of ``referee_stats.py``'s own implementation
+-- either by literal hand arithmetic (documented inline) or by a from-scratch reference
+computation written in this file using only ``random.Random``/``itertools``/plain arithmetic,
+never by calling the module under test and pasting back what it printed."""
+
+from __future__ import annotations
+
+import ast
+import inspect
+import itertools
+import math
+import random
+
+from app.research import referee_stats as rs
+from app.research.referee_stats import (
+    INSUFFICIENT_SAMPLE,
+    REFEREE_B,
+    REFEREE_CI_LEVEL,
+    REFEREE_MIN_CLUSTERS_FOR_CI,
+    REFEREE_SEED,
+    benjamini_hochberg,
+    bootstrap_ci_cluster,
+    bootstrap_ci_occurrence,
+    equal_weight_t,
+    permutation_test,
+    referee_stream,
+    run_oracle_attestation,
+    sign_flip_result,
+    verify_oracle_attestation,
+)
+
+# === TC-1: the seeded stream constructor =============================================================
+
+
+def test_referee_stream_is_deterministic_for_identical_arguments():
+    """TC-1: two calls with an identical (hypothesis_id, purpose, session_date, i) tuple produce
+    byte-identical `random.Random` draw sequences."""
+    a = referee_stream("hyp-1", "perm", session_date="2026-06-08", i=3)
+    b = referee_stream("hyp-1", "perm", session_date="2026-06-08", i=3)
+    assert [a.random() for _ in range(10)] == [b.random() for _ in range(10)]
+
+
+def test_referee_stream_differs_across_every_recipe_component():
+    """Changing hypothesis_id, purpose, session_date, or i each mints a genuinely different
+    stream -- the recipe's own namespacing is real, not decorative."""
+    base = referee_stream("hyp-1", "perm", session_date="2026-06-08", i=1).random()
+    variants = [
+        referee_stream("hyp-2", "perm", session_date="2026-06-08", i=1).random(),
+        referee_stream("hyp-1", "flip", session_date="2026-06-08", i=1).random(),
+        referee_stream("hyp-1", "perm", session_date="2026-06-09", i=1).random(),
+        referee_stream("hyp-1", "perm", session_date="2026-06-08", i=2).random(),
+        referee_stream("hyp-1", "perm").random(),  # no session_date at all
+    ]
+    assert len({base, *variants}) == 1 + len(variants)  # all six draws are pairwise distinct
+
+
+def test_referee_stream_recipe_matches_the_pinned_key_format():
+    """The recipe is exactly `f"{REFEREE_SEED}:{hypothesis_id}:{purpose}[:{session_date}[:{i}]]"`
+    (spec Sec1) -- verified by building the SAME key independently (plain string concatenation,
+    not calling `referee_stream`) and confirming `random.Random` on that independently-built key
+    reproduces the identical sequence `referee_stream` itself returns."""
+    independently_built_key = f"{REFEREE_SEED}:hyp-x:boot-occ:2026-06-08:7"
+    expected = random.Random(independently_built_key)
+    actual = referee_stream("hyp-x", "boot-occ", session_date="2026-06-08", i=7)
+    assert [expected.random() for _ in range(10)] == [actual.random() for _ in range(10)]
+
+
+def test_referee_stream_rejects_i_without_session_date():
+    try:
+        referee_stream("hyp-1", "perm", i=3)
+    except ValueError:
+        pass
+    else:
+        raise AssertionError("expected ValueError: i requires session_date")
+
+
+def test_referee_stream_rejects_an_unknown_purpose():
+    try:
+        referee_stream("hyp-1", "not-a-real-purpose")
+    except ValueError:
+        pass
+    else:
+        raise AssertionError("expected ValueError: unknown purpose")
+
+
+def test_referee_stats_module_never_calls_random_sample_or_an_unseeded_random_instance():
+    """TC-1's negative half, source-scanned (AST, not a regex a comment/string could
+    false-positive): zero `random.sample(...)` calls, zero `random.Random()` calls with NO seed
+    argument, and zero calls to the bare module-level `random.random`/`random.randrange`/
+    `random.choice`/`random.choices` (which implicitly use Python's own hidden global RNG instance
+    rather than a `referee_stream`-constructed one)."""
+    tree = ast.parse(inspect.getsource(rs))
+    banned_bare_random_functions = {"sample", "random", "randrange", "choice", "choices", "seed"}
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Call):
+            func = node.func
+            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
+                if func.value.id == "random" and func.attr in banned_bare_random_functions:
+                    raise AssertionError(f"banned bare random.{func.attr}(...) call found")
+                if func.value.id == "random" and func.attr == "Random":
+                    if not node.args and not node.keywords:
+                        raise AssertionError("random.Random() called with no seed argument")
+
+
+# === TC-19: stdlib-only imports =======================================================================
+
+
+def test_referee_stats_imports_only_stdlib_never_scipy_never_numpy():
+    """TC-19: `referee_stats.py` imports only stdlib modules (itertools, math, random,
+    statistics), never scipy, never numpy."""
+    tree = ast.parse(inspect.getsource(rs))
+    top_level_modules: set[str] = set()
+    for node in ast.walk(tree):
+        if isinstance(node, ast.Import):
+            for alias in node.names:
+                top_level_modules.add(alias.name.split(".")[0])
+        elif isinstance(node, ast.ImportFrom):
+            if node.module:
+                top_level_modules.add(node.module.split(".")[0])
+    # `__future__` is a language-syntax directive (`from __future__ import annotations`), not a
+    # runtime dependency -- excluded from the "imports only stdlib compute modules" check below.
+    top_level_modules.discard("__future__")
+    assert top_level_modules == {"itertools", "math", "random", "statistics"}
+    assert "numpy" not in top_level_modules
+    assert "scipy" not in top_level_modules
+
+
+# === TC-2: occurrence-level percentile bootstrap CI ===================================================
+
+
+def test_bootstrap_ci_occurrence_on_identical_values_collapses_to_the_exact_point_hand_derived():
+    """TC-2 (degenerate, fully hand-derivable fixture): every value in the fixture is IDENTICAL
+    (4.0), so EVERY possible with-replacement resample also averages to EXACTLY 4.0 regardless of
+    which indices are drawn or how many draws are made -- ci_low == ci_high == point_estimate ==
+    4.0 is true by hand arithmetic alone, for ANY seed and ANY b."""
+    values = [4.0] * 12
+    result = bootstrap_ci_occurrence(values, "hyp-ci-degenerate", b=500)
+    assert result == {
+        "state": "ok",
+        "n": 12,
+        "point_estimate": 4.0,
+        "ci_level": REFEREE_CI_LEVEL,
+        "ci_low": 4.0,
+        "ci_high": 4.0,
+        "b": 500,
+    }
+
+
+def test_bootstrap_ci_occurrence_matches_an_independently_reimplemented_reference():
+    """TC-2 (non-degenerate fixture): an INDEPENDENT reference implementation of the identical
+    algorithm -- built from scratch in this test file using only `random.Random` and plain
+    arithmetic, never calling any `referee_stats` resampling helper -- reproduces the module's own
+    ci_low/ci_high exactly. Two independent implementations of a fully-specified deterministic
+    algorithm agreeing is a stronger check than re-running the same code twice."""
+    values = [1.0, 2.0, 3.0, 10.0, -1.0]
+    hypothesis_id = "hyp-ci-reference"
+    b = 300
+    n = len(values)
+
+    # The independent reference: the SAME key format, built by hand, and a hand-written
+    # with-replacement resampling loop (not `_draw_indices_with_replacement`).
+    key = f"{REFEREE_SEED}:{hypothesis_id}:boot-occ"
+    ref_rng = random.Random(key)
+    means = []
+    for _ in range(b):
+        resample = [values[ref_rng.randrange(n)] for _ in range(n)]
+        means.append(sum(resample) / n)
+    means.sort()
+    lo_q = (1.0 - REFEREE_CI_LEVEL) / 2.0
+    hi_q = 1.0 - lo_q
+
+    def reference_percentile(sorted_vals, q):
+        pos = q * (len(sorted_vals) - 1)
+        lo = math.floor(pos)
+        hi = math.ceil(pos)
+        if lo == hi:
+            return sorted_vals[int(pos)]
+        frac = pos - lo
+        return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac
+
+    expected_ci_low = reference_percentile(means, lo_q)
+    expected_ci_high = reference_percentile(means, hi_q)
+
+    result = bootstrap_ci_occurrence(values, hypothesis_id, b=b)
+
+    assert result["ci_low"] == expected_ci_low
+    assert result["ci_high"] == expected_ci_high
+    assert result["point_estimate"] == sum(values) / n
+
+
+def test_bootstrap_ci_occurrence_reruns_are_byte_identical():
+    values = [0.5, -0.2, 3.1, 4.4, -1.0, 2.2]
+    a = bootstrap_ci_occurrence(values, "hyp-repro", b=200)
+    b = bootstrap_ci_occurrence(values, "hyp-repro", b=200)
+    assert a == b
+
+
+def test_bootstrap_ci_occurrence_on_empty_values_is_insufficient_sample():
+    assert bootstrap_ci_occurrence([], "hyp-empty")["state"] == INSUFFICIENT_SAMPLE
+
+
+# === TC-3: the session-clustered CI floor ==============================================================
+
+
+def _uniform_session_groups(n_sessions: int) -> dict[str, tuple[list[float], list[float]]]:
+    return {
+        f"2026-01-{i + 1:02d}": ([1.0 + 0.1 * i, 1.2 + 0.1 * i], [0.0, -0.1])
+        for i in range(n_sessions)
+    }
+
+
+def test_bootstrap_ci_cluster_below_the_floor_is_insufficient_sample():
+    """TC-3: fewer than REFEREE_MIN_CLUSTERS_FOR_CI (8) informative sessions -- the literal
+    `insufficient_sample` state, never a fabricated interval."""
+    sg = _uniform_session_groups(REFEREE_MIN_CLUSTERS_FOR_CI - 1)
+    result = bootstrap_ci_cluster(sg, "hyp-cluster-floor", b=100)
+    assert result == {
+        "state": INSUFFICIENT_SAMPLE,
+        "n_clusters": REFEREE_MIN_CLUSTERS_FOR_CI - 1,
+        "min_clusters_required": REFEREE_MIN_CLUSTERS_FOR_CI,
+    }
+
+
+def test_bootstrap_ci_cluster_at_the_floor_returns_a_real_interval_and_mde():
+    """TC-3: exactly REFEREE_MIN_CLUSTERS_FOR_CI (8) informative sessions crosses the floor -- a
+    real interval and a positive MDE disclosure are served."""
+    sg = _uniform_session_groups(REFEREE_MIN_CLUSTERS_FOR_CI)
+    result = bootstrap_ci_cluster(sg, "hyp-cluster-at-floor", b=300)
+    assert result["state"] == "ok"
+    assert result["n_clusters"] == REFEREE_MIN_CLUSTERS_FOR_CI
+    assert result["ci_low"] <= result["point_estimate"] <= result["ci_high"]
+    assert result["mde"] > 0.0
+    assert result["b"] == 300
+
+
+def test_bootstrap_ci_cluster_one_group_sessions_are_excluded_from_the_cluster_count():
+    """A session carrying only ONE of the two groups is not informative (spec Sec3.1/Sec3.2) and
+    is excluded from `n_clusters` -- 7 two-group sessions plus 3 one-group sessions still reads as
+    7 clusters, below the floor."""
+    sg = _uniform_session_groups(7)
+    sg["2026-02-01"] = ([1.0], [])  # group2 empty -- not informative
+    sg["2026-02-02"] = ([], [1.0])  # group1 empty -- not informative
+    result = bootstrap_ci_cluster(sg, "hyp-one-group", b=50)
+    assert result["state"] == INSUFFICIENT_SAMPLE
+    assert result["n_clusters"] == 7
+
+
+# === TC-4: full enumeration on a tiny, hand-computed fixture ===========================================
+
+
+def test_permutation_test_enumeration_matches_a_hand_computed_p_value():
+    """TC-4: a single-session fixture -- occurrence [5.0] vs anchors [1.0, 2.0] -- whose total
+    label-permutation space is C(3,1)=3, far below REFEREE_ENUMERATION_THRESHOLD. Hand
+    enumeration of all 3 ways to choose which ONE of {5.0, 1.0, 2.0} is "group1":
+      - group1={5.0}: delta* = 5.0 - mean(1.0,2.0) = 5.0 - 1.5 = 3.5   (== the OBSERVED grouping)
+      - group1={1.0}: delta* = 1.0 - mean(5.0,2.0) = 1.0 - 3.5 = -2.5
+      - group1={2.0}: delta* = 2.0 - mean(5.0,1.0) = 2.0 - 3.0 = -1.0
+    T_obs = 3.5 (single session, so T == its own delta regardless of weight). For "greater"
+    sidedness, #{T* >= 3.5} = 1 (only the observed grouping itself) -> p = (1+1)/(3+1) = 0.5."""
+    session_groups = {"2026-06-08": ([5.0], [1.0, 2.0])}
+    result = permutation_test(session_groups, "hyp-enum", sidedness="greater")
+    assert result["state"] == "ok"
+    assert result["enumeration"] is True
+    assert result["draws_used"] == 3
+    assert abs(result["t"] - 3.5) < 1e-9  # float division noise, not a rounding bug
+    assert result["p"] == 0.5
+    assert result["min_attainable_p"] == 0.25
+
+
+def test_permutation_test_enumeration_is_deterministic_with_zero_rng_draws():
+    """TC-4's "no seeded sampling" clause: two calls with DIFFERENT hypothesis_id (which would
+    seed a DIFFERENT stream in the seeded-draw branch) still produce the byte-identical result in
+    the enumeration branch, because enumeration never touches the RNG at all."""
+    session_groups = {"2026-06-08": ([5.0], [1.0, 2.0])}
+    a = permutation_test(session_groups, "hyp-a", sidedness="greater")
+    b = permutation_test(session_groups, "hyp-b-totally-different", sidedness="greater")
+    assert a == b
+
+
+# === TC-5: the seeded B-draw branch ====================================================================
+
+
+def test_permutation_test_seeded_branch_uses_exactly_b_draws_and_the_p_formula():
+    """TC-5: a fixture large enough to exceed REFEREE_ENUMERATION_THRESHOLD (4 sessions of
+    n1=3,n2=3 each: C(6,3)=20 per session, 20**4=160,000 total > 8,192) uses exactly `b` seeded
+    draws, and `p = (1 + #{T* >= T}) / (b + 1)` for "greater" sidedness -- verified by
+    independently recomputing the extreme count with a from-scratch reference permutation loop."""
+    rng = random.Random("tc5-fixture-seed")
+    session_groups = {
+        f"2026-03-{i + 1:02d}": (
+            [rng.gauss(0, 1) for _ in range(3)],
+            [rng.gauss(0, 1) for _ in range(3)],
+        )
+        for i in range(4)
+    }
+    b = 500
+    result = permutation_test(session_groups, "hyp-seeded", sidedness="greater", b=b)
+    assert result["enumeration"] is False
+    assert result["draws_used"] == b
+    assert result["min_attainable_p"] == 1.0 / (b + 1)
+
+    # Independent reference recomputation (a from-scratch permutation loop, not calling any
+    # `referee_stats` internals beyond the plain arithmetic every reader can verify).
+    sessions = sorted(session_groups)
+    n1_by_s = {s: len(session_groups[s][0]) for s in sessions}
+    n2_by_s = {s: len(session_groups[s][1]) for s in sessions}
+    weight_by_s = {
+        s: (n1_by_s[s] * n2_by_s[s]) / (n1_by_s[s] + n2_by_s[s]) for s in sessions
+    }
+    total_weight = sum(weight_by_s.values())
+    delta_by_s = {
+        s: sum(session_groups[s][0]) / n1_by_s[s] - sum(session_groups[s][1]) / n2_by_s[s]
+        for s in sessions
+    }
+    t_obs = sum(weight_by_s[s] * delta_by_s[s] for s in sessions) / total_weight
+    assert abs(result["t"] - t_obs) < 1e-9
+
+    extreme = 0
+    streams = {s: random.Random(f"{REFEREE_SEED}:hyp-seeded:perm:{s}") for s in sessions}
+    pooled = {s: session_groups[s][0] + session_groups[s][1] for s in sessions}
+    for _ in range(b):
+        acc = 0.0
+        for s in sessions:
+            values = pooled[s]
+            n1 = n1_by_s[s]
+            n = len(values)
+            rstream = streams[s]
+            pool = list(range(n))
+            for idx in range(n1):
+                j = rstream.randrange(idx, n)
+                pool[idx], pool[j] = pool[j], pool[idx]
+            g1_sum = sum(values[idx] for idx in pool[:n1])
+            g2_sum = sum(values) - g1_sum
+            delta_star = g1_sum / n1 - g2_sum / (n - n1)
+            acc += weight_by_s[s] * delta_star
+        t_star = acc / total_weight
+        if t_star >= t_obs:
+            extreme += 1
+    expected_p = (1 + extreme) / (b + 1)
+    assert result["p"] == expected_p
+
+
+def test_permutation_test_default_b_is_referee_b_when_not_overridden():
+    """A fixture whose space exceeds the enumeration threshold, called WITHOUT overriding `b`,
+    uses the production default REFEREE_B (10,000) -- proving the confirmatory default is wired,
+    not just an override-only parameter."""
+    rng = random.Random("tc5-default-b-seed")
+    session_groups = {
+        f"2026-04-{i + 1:02d}": (
+            [rng.gauss(0, 1) for _ in range(3)],
+            [rng.gauss(0, 1) for _ in range(3)],
+        )
+        for i in range(4)
+    }
+    result = permutation_test(session_groups, "hyp-default-b", sidedness="greater")
+    assert result["enumeration"] is False
+    assert result["draws_used"] == REFEREE_B
+
+
+def test_permutation_test_reruns_are_byte_identical():
+    rng = random.Random("tc5-repro-seed")
+    session_groups = {
+        f"2026-05-{i + 1:02d}": ([rng.gauss(0, 1)], [rng.gauss(0, 1) for _ in range(4)])
+        for i in range(10)
+    }
+    a = permutation_test(session_groups, "hyp-repro-perm", sidedness="greater", b=300)
+    b = permutation_test(session_groups, "hyp-repro-perm", sidedness="greater", b=300)
+    assert a == b
+
+
+def test_permutation_test_no_informative_sessions_is_insufficient_sample():
+    sg = {"2026-06-08": ([], [1.0, 2.0]), "2026-06-09": ([1.0], [])}
+    result = permutation_test(sg, "hyp-none-informative")
+    assert result == {"state": INSUFFICIENT_SAMPLE, "n_informative_sessions": 0}
+
+
+# === TC-6: robustness variants are served, never substituted ==========================================
+
+
+def test_sign_flip_and_equal_weight_are_served_alongside_and_never_change_the_primary_p():
+    """TC-6: a fixture engineered so the equal-weight T flips sign relative to the (precision-
+    weighted) primary T -- one heavily-weighted session pulls the primary T positive while the
+    unweighted average is negative. Both robustness values are returned, and the PRIMARY p/T is
+    identical whether or not the caller also computes the variants (no shared mutable state, no
+    substitution)."""
+    session_groups = {
+        # A fat session (n1=n2=20), delta=1.0, weight=20*20/40=10 -> contributes 10*1.0=10.0.
... [diff_bound] apps/backend/tests/test_referee_stats.py: 157 more diff lines omitted — Read the file for full detail
```
