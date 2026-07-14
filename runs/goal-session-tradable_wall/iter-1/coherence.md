# Iteration 1 — Coherence Audit

**Iteration:** goal-tradable_wall-iter-1
**Date:** 2026-07-14
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Tradable level map — bands (NEW, pre-registered) | OK | Sole owner `apps/backend/app/research/tradability.py:321` (`compute_tradability`); sole endpoint `apps/backend/app/research/routes.py:193-213` (`GET /research/tradability`, returns module output verbatim); MCP `tradability` is a byte-identical read-only proxy sharing the `levels` request-building branch, `apps/backend/app/mcp/__init__.py:114-118,127-146,155-164`, proven byte-identical by `apps/backend/tests/test_mcp_server.py:249-287` |
| Raw levels + A/B/C confluence zones (existing owner `levels.py`) | OK — read verbatim | `tradability.py:98` imports only `compute_levels` from `.levels`; called exactly once at `tradability.py:361`, output (`levels_result["levels"]`, `levels_result["confluence_zones"]`) used unmutated at `tradability.py:362-363`. `levels.py` itself is untouched (absent from `git status`). Static-analysis guard `test_tradability_module_is_a_lens_never_a_second_levels_engine` (`apps/backend/tests/test_tradability.py:353-383`) asserts no call into any `levels.py` internal (`_swing_pivots`, `_prior_period_extremes`, `_bars_as_of`, `_select_one_series_per_timeframe`, `_cluster_levels`, `_grade_zone`) and no read of the frozen `sr_pivot_lookback`/`sr_touch_tolerance_bps` thresholds. Byte-identity regressions: `test_aapl_frozen_levels_output_is_byte_identical_to_before` (`test_tradability.py:515-527`) and `test_frozen_levels_output_is_byte_identical_after_a_tradability_request` (`test_tradability_api.py:187-204`) |
| Band `class` (A/B/C, inherited from `levels.py`) | OK — projection only | `_best_zone_class` (`tradability.py:245-259`) reads `zone["class"]` verbatim and picks the best by rank/score; no grading/mutation |
| `config_fingerprint` (frozen `4d665603569b9dbf`) | OK | 5 new `tradability_*` constants added to `Config` (`apps/backend/app/config.py:19-67`) and to the exclusion set (`config.py:87-91` region, i.e. the fingerprint's excluded-fields list); stability + real-threshold counter-test at `test_tradability.py:331-347` |

No new function/endpoint computes any registered value independently of its canonical owner; no new UI surface fetches a value from a non-canonical source. The one new served value is exactly the blueprint's pre-registered "Tradable level map — bands" row — nothing unregistered was introduced.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `GET /research/tradability` + MCP `tradability` | N/A (no UI surface this iteration) | `reports/phase-goal-tradable_wall-iter-1-ui-surface-map.md` (analyst-confirmed "N/A — Backend-only phase... No UI surfaces affected"); `git status` shows zero frontend files touched; iter spec is `Frontend Present: no` |

This iteration is backend + API + MCP only (by design — the map's UI home, `/structure` → Tradable Map, is deferred to J-05). Nav is frozen per the blueprint and untouched. No page/route/component was added to any nav shell, so nav-path, reachability, duplicate-home, and parallel-shell checks do not apply.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Minor, backend-internal only — not a Data Contract violation.** `tradability.py`'s `_select_daily_series` (`apps/backend/app/research/tradability.py:151-172`) re-implements — rather than imports — the exact "most-recently-created `1d` series wins" tie-break `levels.py`'s own internal `_select_one_series_per_timeframe` performs (the module's own docstring at `tradability.py:153-158` names this coupling explicitly). The actual served levels/zones are still 100% sourced from `compute_levels`'s own selection over the same unfiltered `store.list()` (`_PriorSessionBarView.list()` delegates unchanged, `tradability.py:144-145`), so no displayed value is duplicated today, and both selections are currently verified identical by direct code reading. But it is a private duplicated algorithm: if `levels.py`'s own tie-break rule ever changes without a matching change here, `tradability.py`'s `prior_bar`/`basis_as_of` could silently diverge from the series `compute_levels` actually reads. No test currently seeds two competing `"1d"` series for the same symbol to prove the two selections agree (`test_tradability.py`'s `_seed_synthetic` deliberately records only one series per test). Non-blocking; a future cleanup could extract the shared tie-break into one helper both modules call, or add a two-series regression test — left for the decomposer/developer to pick up opportunistically, not required to progress the goal.
