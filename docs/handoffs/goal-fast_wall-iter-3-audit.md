# goal-fast_wall-iter-3 Audit Report

**Date:** 2026-07-17
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

J-03's per-run `_StructureArmMemo` is implemented exactly as scoped and is provably correct: I traced both memoization keys against their owner functions and confirmed each is a sound, byte-identity-preserving accelerator, then ran a mutation-testing probe that proves the byte-identity tests genuinely bite (a stale-serving memo produces 0 trades where the correct memo produces 1). All 15 TCs hold, the full suite is green (1440 passed / 7 skipped / 0 failed, independently re-run), the config fingerprint is frozen at `4d665603569b9dbf`, the scope is surgical (3 product + 3 test files, frozen bodies byte-unchanged), and every critical anti-goal is respected. No critical, important, or gap-level issues found; no fixes required.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): structure-arming reads `self._config`, not the profile-resolved `run_config`**
`_structure_tape_trades` (`backtests.py:697`) and `_structure_tape_map_trades` (`:809`) bind `config = self._config` and build the memo with `self._config` (`:693`, `:805`), while `run()` computes `run_config = self._config.resolved_for_profile(...)` (`:488`) for the fingerprint/replay. For a non-default profile this means structure arming would use the default config. This is **pre-existing** (v1's branch does the identical `config = self._config` at `:611`), entirely outside J-03's scope, and — critically — **does not affect this iteration's byte-identity contract**: the memo and the `memo=None` fallback both use `self._config`, so they agree. For the frozen `default` profile (the only one exercised and pinned), `resolved_for_profile(PROFILE_DEFAULT)` returns `self._config` unchanged, so there is no observable difference at all. Noted for completeness only; fixing it here would be scope creep into a pre-existing, unrelated area.

### Frontend Findings

None — `Frontend Present: no`. Zero frontend files touched (confirmed via `git status`); J-03 is a backend-only accelerator with no UI surface, matching the blueprint's pre-registered "no dedicated UI panel" home.

### Test Findings

**T1 — OBSERVATION (observation): TC-8 omits the `len(trades) >= 1` non-vacuity assert its siblings carry**
`test_structure_tape_map_memo_bust_utc_date_boundary` (`test_backtests.py:1651`) asserts byte-identity (memoized == direct) plus a direct-compute `basis_as_of` differs across the boundary, but — unlike TC-5/TC-6/TC-7 — does not assert the run produces at least one trade. Per the spec's own acceptance ("...AND the tradability basis genuinely differs...") this is sufficient, and I verified the assertion is currently **non-vacuous**: my audit mutation probe showed TC-8's exact scenario yields 1 trade under the correct memo and 0 trades under a stale-serving memo, so the byte-identity assertion genuinely catches a cross-boundary stale-serve bug today. Adding `assert len(memoized["result"]["trades"]) >= 1` would lock that non-vacuity against future fixture drift. Minor robustness nit only; the delivered capability is correct and fully guarded.

---

## 3. Domain Assessment

The core domain logic is correct, and I verified it by tracing the owner functions rather than trusting the handoff.

**`level_change_points` (levels.py:325) is a sound safe-superset.** `compute_levels` depends on `as_of_epoch` through exactly two paths: bar visibility via `_bars_as_of` (`b.epoch <= as_of`) and prior-period completion via `_prior_period_extremes` (`b.epoch + period_seconds > as_of`). The helper enumerates every selected series' bar epochs plus, for each `PRIOR_PERIOD_TIMEFRAMES` bar, its `epoch + period_seconds` close instant — mirroring `compute_levels`'s own `store.list()` healthy half + `_select_one_series_per_timeframe` enumeration verbatim. It reads the untruncated full series (a superset is always safe), so it can never omit a true change point. Combined with the memo's `bisect_right` bucketing, two `as_of` in one bucket provably yield byte-identical `compute_levels` output (no bar epoch and no period-close instant lies strictly between them). Config correctly does not enter this helper — `compute_levels`'s as_of-change-instants are structural (bar timing), never config-dependent.

**`basis_day_key` (tradability.py:384) memoization is provably exact — the crux of this iteration.** I proved `compute_tradability` depends on `as_of_epoch` only through `_resolve_basis`. In `_resolve_basis` the candidate filter is `b.epoch <= as_of_epoch AND _session_date(b.epoch) < requested_date`. For any `as_of` on UTC date D, the second clause forces `b.epoch < midnight(D) <= as_of`, so the first clause is **redundant** — the candidate set (and thus `prior_bar`, `resolved_as_of_epoch`, and everything `compute_tradability` derives downstream via the `_PriorSessionBarView`) is a pure function of `_session_date(as_of)`. Therefore keying the tradability cache on `basis_day_key = _session_date(as_of).isoformat()` is exact, not an approximation. No lookahead is introduced: the memo's change-point tuple uses full-series epochs only as bucket boundaries; the value served is always `compute_levels/compute_tradability(as_of)`, which does its own as-of truncation, and ticks are processed in chronological order so the cached value is the earliest-in-bucket computation (byte-identical to every later tick's own).

**Anti-goals upheld.** Frozen foundations: `compute_levels`/`compute_confluence_zones`/`compute_tradability`/`_resolve_basis` bodies are byte-unchanged (git diff shows pure appends to `levels.py`/`tradability.py`; `backtests.py` arm bodies gain only the spec-required `if memo is not None` branch with the literal owner call preserved in the `else`). No divergent accelerator output: TC-5–TC-8 byte-identity, re-verified plus mutation-tested. Rebuildable/single-owner/never-persisted: the memo is a local variable built once per `_..._trades` method (`:693`, `:805`), never stored, never shared across runs; source-introspection guards (no `_swing_pivots`/`_prior_period_extremes`/`_cluster_levels`/`_grade_zone`; `compute_levels(`/`compute_tradability(` present) pass unmodified. No new Config field; fingerprint frozen. No compute-on-page-load concern (no route touched; the memo lives only inside `BacktestRunner.run()`).

**Test quality is high.** Assertions are tight and use direct computation, not hand-waving: TC-1 pins the exact change-point count (14) and membership; TC-9 asserts `len(calls) == len(change_points) == 7` (exact, not "fewer than ticks" alone); TC-10 asserts exactly 2 tradability calls across the boundary. The TC-5/TC-6 byte-identity comparison swaps in a genuinely non-caching `_NoCacheArmMemo` via monkeypatch so the EXACT production interleave loop runs on both sides — a faithful stand-in for the pre-iteration direct-call path. My independent mutation probe (poisoning the memo to serve stale values) confirmed the TC-7/TC-8 guards are non-vacuous.

---

## 4. Fixes Applied During This Audit

None. No critical or important issues were found; the two observations above are documentation/robustness nits whose repair would be scope creep. Working tree left unchanged apart from the transient audit probe, which was deleted (`git status` confirms only the 3 product + 3 test files modified, matching the plan's expected scope).

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied |

---

## 5. Recommended Next Step

Proceed to **J-04** ("The operator-run compute — button, background job, CLI warmer") per goal.md's dependency order (J-01 → J-02 → J-03 → J-04 → J-05), as the dev handoff and phase BACKGROUND both recommend. J-03 lays down the correct, byte-identical throughput fix (per-tick `compute_levels`/`compute_tradability` recomputes collapse to one per real change-point interval / UTC session date) that J-04's compute trigger needs to make a real edge-report sweep progress at a sane rate. J-04 touches new files only and does not further modify `levels.py`/`tradability.py`/`backtests.py`, carrying a lower frozen-foundation risk profile than this iteration.

**Audit evidence log:**
- Targeted suite `tests/test_levels.py tests/test_tradability.py tests/test_backtests.py`: **114 passed in 9.43s**.
- Full backend suite `pytest tests/`: **1440 passed, 7 skipped, 0 failed in 428.30s** (independently re-run; matches QA).
- `config.config_fingerprint()` → `4d665603569b9dbf` (confirmed).
- Source-introspection guards run explicitly: **2 passed**; forbidden level-internal substrings absent, `compute_levels(`/`compute_tradability(` owner calls present.
- Mutation probe (temporary, deleted): stale-tradability memo → 0 trades vs correct 1 trade (TC-8); stale-levels memo → 0 trades vs correct 1 trade (TC-7) — byte-identity assertions proven to genuinely bite.
- `git diff` deletions: test files touch only the `tradability` import line (zero pre-existing test-body edits); `levels.py`/`tradability.py` pure appends; `backtests.py` changes limited to spec-required memo threading.
