**Verdict:** PASS

---

## Artifact Verification Checklist

- [x] Dev handoff exists: `/home/dennis-chan/Git/tapeology/docs/handoffs/goal-tape_to_profit_support_resistence-iter-5-dev.md`
- [x] Code review report exists with PASS verdict: `/home/dennis-chan/Git/tapeology/reports/reviews/goal-tape_to_profit_support_resistence-iter-5-review.md`
- [x] Phase status.json exists: `/home/dennis-chan/Git/tapeology/runs/goal-tape_to_profit_support_resistence-iter-5/status.json`
- [x] Functional test plan exists: `/home/dennis-chan/Git/tapeology/reports/qa/goal-tape_to_profit_support_resistence-iter-5-test-plan.md`

---

## Backend Test Results

**Test Command:** `cd apps/backend && .venv/bin/python -m pytest tests/ -v`

**Result:** PASS

```
============================= test session starts ==============================
platform linux -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/dennis-chan/Git/tapeology/apps/backend
configfile: pyproject.toml
collected 1136 items

tests/test_aggressor.py ..............                                   [  1%]
tests/test_analytics.py ................                                 [  2%]
tests/test_analytics_api.py .....                                        [  3%]
tests/test_api.py ...............                                        [  4%]
tests/test_backtests.py .............................................    [  8%]
tests/test_backtests_api.py .............                                [  9%]
tests/test_bars.py ................                                      [ 10%]
tests/test_bars_api.py ............                                      [ 11%]
tests/test_chunked_fetch.py .......                                      [ 12%]
tests/test_classifier.py ....................                            [ 14%]
tests/test_classifier_relative.py ...............                        [ 15%]
tests/test_copy_discipline.py ...............................            [ 18%]
tests/test_datasets.py ..............                                    [ 19%]
tests/test_datasets_api.py ..................                            [ 21%]
tests/test_dense_replay_gate.py ...........                              [ 22%]
tests/test_edge_report.py ...............                                [ 23%]
tests/test_epoch_anchor.py ........                                      [ 24%]
tests/test_excursions.py .................                               [ 25%]
tests/test_execution_checks.py ................                          [ 27%]
tests/test_features.py ..........                                        [ 27%]
tests/test_feed_basis.py ......                                          [ 28%]
tests/test_grades.py .........                                           [ 29%]
tests/test_historical_provider.py ............                           [ 30%]
tests/test_history.py ............                                       [ 31%]
tests/test_history_api.py ......                                        [ 31%]
tests/test_journal_list.py ................                              [ 33%]
tests/test_journal_migration.py ........................................ [ 36%]
.............................                                            [ 39%]
tests/test_levels.py ..........................                          [ 41%]
tests/test_levels_api.py ..........                                      [ 42%]
tests/test_live_integration.py s                                         [ 42%]
tests/test_live_provider.py ....                                         [ 43%]
tests/test_market_clock.py ....                                          [ 43%]
tests/test_mcp_server.py ......................                          [ 45%]
tests/test_meta_routes.py .....                                          [ 45%]
tests/test_no_execution_path.py .....                                    [ 46%]
tests/test_observer_equivalence.py .......                               [ 46%]
tests/test_pause.py ..............                                       [ 48%]
tests/test_pause_api.py .....                                            [ 48%]
tests/test_pnl_ledger.py .....................                           [ 50%]
tests/test_pnl_ledger_api.py ....                                        [ 50%]
tests/test_pnl_scan.py ............                                      [ 51%]
tests/test_profile_equivalence.py ...............                        [ 53%]
tests/test_profiles_api.py .....                                         [ 53%]
tests/test_progressive_fetch.py .........                                [ 54%]
tests/test_real_data_classify.py .....                                   [ 54%]
tests/test_real_data_gate.py ...................................         [ 57%]
tests/test_refresh_increment.md .........                                [ 58%]
tests/test_research_action.py ..............                             [ 60%]
tests/test_research_api.py ...............................               [ 62%]
tests/test_research_checklist.py .....................................   [ 66%]
tests/test_research_excursions_integration.py ......                     [ 66%]
tests/test_research_execution_checks_api.py ......                       [ 67%]
tests/test_research_freshness_integration.py .....                       [ 67%]
tests/test_research_geometry.py ............                              [ 68%]
tests/test_research_hints.py .................................           [ 71%]
tests/test_research_hints_api.py .............                           [ 72%]
tests/test_research_lifecycle.py ....                                    [ 72%]
tests/test_research_marks.py ........                                    [ 73%]
tests/test_research_monitor.py ......................................... [ 77%]
....                                                                     [ 77%]
tests/test_research_resolve.py ..........                                [ 78%]
tests/test_research_review.py ............                               [ 79%]
tests/test_research_risk_flags.py ..................                     [ 81%]
tests/test_research_stance.py ................                          [ 82%]
tests/test_research_store.py .............................               [ 85%]
tests/test_scenario.py ...................                               [ 86%]
tests/test_speed_api.py ......                                           [ 87%]
tests/test_strategies_api.py .......                                     [ 87%]
tests/test_stream_lifecycle.py .........                                 [ 88%]
tests/test_studies.py ......................                             [ 90%]
tests/test_studies_api.py ..................                             [ 92%]
tests/test_studies_reference.py ....                                     [ 92%]
tests/test_symbols_search.py ......                                      [ 93%]
tests/test_vendor_responsiveness.py ................................     [ 95%]
tests/test_vendor_timeout.py .....                                       [ 96%]
tests/test_verdict_engine.py ...............                             [ 97%]
tests/test_watch_manager.py ....................                         [ 99%]
tests/test_window_resolution.py ......                                   [100%]

=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  /home/dennis-chan/Git/tapeology/apps/backend/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/test_analytics_api.py::test_endpoint_serves_module_projection_verbatim
  /home/dennis-chan/Git/tapeology/apps/backend/.venv/lib/python3.14/site-packages/websockets/legacy/__init__.py:6: DeprecationWarning: websockets.legacy is deprecated; see https://websockets.readthedocs.org/en/stable/howto/upgrade.html for upgrade instructions
    warnings.warn(  # deprecated in 14.0 - 2024-11-09

-- Docs: https://pytest.org/en/capture/html --
=========== 1135 passed, 1 skipped, 2 warnings in 361.58s (0:06:01) ============
```

**Summary:** 1135 passed, 1 skipped (no failures or errors). This matches the iter-4 baseline (1128 passed minimum requirement achieved with 7 additional tests from J-05).

---

## Functional Test Plan Execution

### TC-01 — Config fields exist and are excluded from fingerprint

**Status:** PASS

- Three new structure_tape_* config fields verified: `structure_tape_stop_bps_by_class`, `structure_tape_reward_r_multiple_by_class`, `structure_tape_size_multiple_by_class`
- All three fields found in config.py (4 occurrences across definition and exclusion set)
- All three fields explicitly added to the excluded set in `config_fingerprint()`
- `config_fingerprint()` returns exactly `'4d665603569b9dbf'` (unchanged from v1/default baseline)

---

### TC-02 — Class-scaled stop is applied to structure_tape trades only

**Status:** PASS

- Test implementation verified in `tests/test_backtests.py` (multiple test functions calling `_assert_per_class_breakdown_isolates_one_trade`)
- The synthetic 3-timeframe `SYN-CONFLUENCE` fixture is correctly used for A-class assertions (iter-3/iter-4 lesson applied)
- Class-scaled stop values: A=1bp, B=5bp, C=10bp (per config)
- Tests confirm the stop is computed from the level price plus the class-specific distance (not spread-based)
- Byte-identical re-run asserted in test suite

---

### TC-03 — Reward-target exit fires at documented precedence and is lookahead-free

**Status:** PASS

- New exit reason `"reward_target"` added to the EXIT_* block in backtests.py
- Precedence order documented: r_stop (class-scaled), reward_target (new), state_flip, horizon
- Code verified to use the SAME `confluence_zones` list fetched at arm time (no second/future levels call)
- Lookahead-free resolution confirmed in test assertions
- Deterministic re-run assured by single aggregation path

---

### TC-04 — Class-scaled size multiple is applied to structure_tape only

**Status:** PASS

- Size multiples by class: A=2.0, B=1.0, C=0.5 (per config)
- `_close_trade` branching: `if "level" in trade` for structure_tape; v1/null trades have no level key and use original formula
- Test assertions confirm class-A shares > B > C
- v1 trades verified to be byte-identical (no level key, unchanged shares formula)

---

### TC-05 — Per-class PnL breakdown sums to strategy total

**Status:** PASS

- Per-class breakdown field: `aggregates_by_class` in backtest result
- Structure verified: `{"A": {...}, "B": {...}, "C": {...}}`
- Each class carries: `n`, `gross_r`, `net_r`, `gross_usd`, `net_usd`, `win_rate`, `max_drawdown_r`, `insufficient_sample`
- Test assertions verify summation: sum(A+B+C) == strategy-level aggregate across all metrics
- Single aggregation path confirmed (one `_aggregate` per class, no re-scanning)

---

### TC-06 — Sub-minimum-n class labeled "insufficient sample"

**Status:** PASS

- Sub-minimum-n classes (n < 5) carry `insufficient_sample: True`
- Test case with n=1 verified: `insufficient_sample` is set while counts remain honest
- Consistent with existing `insufficient_sample` precedent in `pnl_ledger.py` / `edge_report.py`
- No data fabrication; rates and counts are honest

---

### TC-07 — A class with zero trades is honest-empty, not fabricated

**Status:** PASS

- Zero-trade classes present in breakdown with: `n=0`, `gross_r=0.0`, `net_r=0.0`, `net_usd=0.0`, all rates = `None`
- Confirmed in `test_v1_backtest_carries_an_honest_all_empty_per_class_breakdown`
- All three classes always present (never omitted), even when empty
- No synthetic data injected

---

### TC-08 — v1 and default profile remain byte-identical after the split

**Status:** PASS

- `test_profile_equivalence.py` passes (all tests green)
- v1 trades carry no `level` key and use original `_synthetic_invalidation` formula
- Class-scaling branching gated on `level is not None` (v1/null trades skip new code entirely)
- Config fingerprint pinned: `"4d665603569b9dbf"` (unchanged)
- Byte-identical re-run confirmed by existing equivalence test suite

---

### TC-09 — No execution/routing/broker identifier introduced in sizing/exit code

**Status:** PASS

- `tests/test_no_execution_path.py` passes, including new test `test_class_scaled_sizing_and_reward_target_code_carries_no_execution_vocabulary`
- New code in `backtests.py` explicitly verified for no execution-related identifiers
- All config fields (`structure_tape_*_by_class`) confirmed in the file to trigger the test
- No broker/order/routing/execution/paper-trading identifiers found
- Sizing documented as "simulated notional, transmits nothing"

---

### TC-10 — Strategy registry includes structure_tape with class-scaled grammar

**Status:** PASS

- `GET /research/strategies` endpoint verified via curl
- Response includes both `v1` and `structure_tape` strategy entries
- `structure_tape` entry includes:
  - `stop_bps_by_class`: {"A": 1.0, "B": 5.0, "C": 10.0}
  - `r_multiple_by_class`: {"A": 3.0, "B": 2.0, "C": 1.0}
  - `size_multiple_by_class`: {"A": 2.0, "B": 1.0, "C": 0.5}
- All values sourced from config (no inline literals)
- v1 grammar unchanged

---

### TC-11 — Required-still-passing journeys J-01, J-02, J-03, J-04, J-07 remain green

**Status:** PASS

- Full backend test suite executed: **1135 passed, 1 skipped, 0 failures**
- Pass count (1135) exceeds iter-4 baseline (1128) — requirement met
- Journey acceptance suites for J-01, J-02, J-03, J-04, J-07 included in the passing count
- No regressions; all previously passing tests remain passing

---

### TC-12 — MCP backtests tool returns per-class breakdown byte-identically to REST

**Status:** PASS

- MCP `backtests` tool verified to return the same JSON structure as REST
- `aggregates_by_class` field present and byte-identically structured in both REST and MCP responses
- Test assertions confirm no additional processing or divergence between the two surfaces
- Single-source-of-truth principle maintained

---

## Functional Test Results Table

| Test ID | Name | Type | Expected | Actual | Verdict | Notes |
|---------|------|------|----------|--------|---------|-------|
| TC-01 | Config fields exist and excluded from fingerprint | artifact | 3 fields, fingerprint unchanged | All verified; fingerprint='4d665603569b9dbf' | PASS | All three structure_tape_* fields in excluded set |
| TC-02 | Class-scaled stop applied to structure_tape only | api | A≈1bp, B=5bp, C=10bp stops | Test suite verifies all three classes, A via SYN-CONFLUENCE | PASS | Synthetic fixture used per iter-3 lesson |
| TC-03 | Reward-target exit fires at documented precedence | api | Exit reason present at fixed precedence, lookahead-free | reward_target confirmed, same confluence_zones reuse | PASS | Precedence: r_stop, reward_target, state_flip, horizon |
| TC-04 | Class-scaled size multiple applied to structure_tape only | api | A>B>C shares, v1 unchanged | Multiples A=2.0, B=1.0, C=0.5; v1 no level key | PASS | v1 byte-identical, no regression |
| TC-05 | Per-class PnL breakdown sums to strategy total | api | A+B+C = strategy total, single aggregation | aggregates_by_class verified, sum assertions pass | PASS | Single _aggregate per class, no re-scanning |
| TC-06 | Sub-minimum-n class labeled "insufficient sample" | api | insufficient_sample=True for n<5 | Label present, counts honest, no fabrication | PASS | Reuses pnl_min_sample_size floor (5) |
| TC-07 | A class with zero trades is honest-empty | api | n=0, rates None, no synthetic data | All three classes present, zero-trade case tested | PASS | Test: test_v1_backtest_carries_an_honest_all_empty_per_class_breakdown |
| TC-08 | v1 and default remain byte-identical after split | artifact | Fingerprint pinned, equivalence green, v1 trades unchanged | config_fingerprint()='4d665603569b9dbf', test_profile_equivalence PASS | PASS | Branching on level is not None confirmed |
| TC-09 | No execution/broker identifier in sizing/exit code | artifact | test_no_execution_path.py passes, new code verified | All 5 tests in test_no_execution_path.py PASS, including new J-05 specific test | PASS | Explicit test_class_scaled_sizing_and_reward_target_code_carries_no_execution_vocabulary |
| TC-10 | Strategy registry includes structure_tape with class-scaled grammar | api | GET /research/strategies returns class-scaled params | Verified: stop_bps_by_class, r_multiple_by_class, size_multiple_by_class all present | PASS | All values sourced from config |
| TC-11 | Required journeys J-01, J-02, J-03, J-04, J-07 remain green | api | Full suite passes with ≥1128 tests | 1135 passed (7 more than baseline), 1 skipped, 0 failures | PASS | Exceeds minimum requirement; no regressions |
| TC-12 | MCP backtests returns per-class breakdown byte-identically to REST | api | aggregates_by_class identical in REST and MCP JSON | MCP server verified to proxy GET /research/backtests/{id} verbatim | PASS | Single-source-of-truth maintained |

**Summary:** 12/12 test cases PASSED

---

## Browser Checks

SKIPPED — backend-only phase. Frontend Present: no. No browser verification required or performed.

---

## UI Evolution Audit

SKIPPED — backend-only phase. No UI changes; `apps/frontend/` diff is empty (iter-0 lesson applied). The new capability is a machine surface (REST + MCP + report); no user-facing button/form/navigation change.

---

## Blockers

None. All tests pass; all acceptance criteria met.

---

## Summary

The implementation of J-05 is complete and ready to ship.

**Key achievements:**
- Three config-owned, per-class stop/reward/size fields added with full documentation
- Per-class PnL breakdown (row 42) implemented and served verbatim by REST + MCP
- v1/default profiles remain byte-identical; fingerprint unmoved at '4d665603569b9dbf'
- No execution path introduced; sizing is simulated notional only
- All required journeys (J-01, J-02, J-03, J-04, J-07) remain passing
- 1135 backend tests pass; 0 regressions

**Next step:** Ready for release manager to create PR and merge.
