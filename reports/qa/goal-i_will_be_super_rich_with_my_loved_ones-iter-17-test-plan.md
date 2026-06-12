# Goal Iteration 17 Functional Test Plan

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-17
**Date:** 2026-06-11
**Frontend Present:** yes

## Phase Goal

Make rolling-feature maintenance truly incremental across window evictions with byte-identical refresh-score values proven by a committed ~10-minute real SIP fixture replayed unpaced inside a CI-gated time budget, unblocking the replay-studies layer.

## Test Cases

### TC-01 — Structural No-Rescan After Evictions

**Type:** api
**Preconditions:** 
- Dense fixture (≈10-minute real SIP trades+quotes) committed at `apps/backend/tests/fixtures/alpaca/`
- Test harness can import `TapeEngine` and count `_refresh_fractions()` invocations
- Feature windows are configured at 10s, 30s, 60s, 180s, 300s; fixture window > 300s so all evict

**Steps:**
1. Start a fresh `TapeEngine` with the engine path (trades carrying `eff_bid`/`eff_ask`)
2. Replay the dense fixture events sequentially through `engine.process_trade()` and `engine.process_quote()`
3. Instrument the `_Window._refresh_fractions()` method to count invocations after the FIRST eviction occurs in any window
4. Record the final invocation count
5. Assert that at least one window underwent eviction during replay (guard against silently too-short fixture)

**Expected outcome:** The invocation count of `_refresh_fractions()` after evictions begin is zero (or a strictly bounded constant ≤ 2 with documented justification if design permits a bounded fallback)

**Pass criteria:** 
- `_refresh_fractions()` invocation count after first eviction ≤ documented constant
- At least one window evicted during replay (eviction_events > 0)
- Test log shows fixture replayed completely without errors

---

### TC-02 — Oracle Equivalence: Incremental vs Merge on Dense Fixture

**Type:** api
**Preconditions:**
- Dense fixture loaded and parsed
- `TapeEngine` instantiated on engine path
- `_Window._refresh_fractions()` method available and deterministic (test oracle)

**Steps:**
1. Replay dense fixture through the engine at every `process_trade()` and `process_quote()` call
2. At a dense sampled subset of ticks that provably includes many post-eviction compute() calls (e.g., every 10th tick after first eviction), capture the incremental `bid_refresh_score` and `ask_refresh_score` from the engine state
3. At the same tick, compute what `_refresh_fractions()` would return for the identical window contents
4. Compare the two values using exact equality (`==`, never approx)
5. Record any mismatches with tick timestamp and window

**Expected outcome:** Every sampled incremental refresh score exactly equals the oracle `_refresh_fractions()` output

**Pass criteria:** 
- Zero mismatches across all sampled ticks (mismatch_count == 0)
- Sample includes at least 50 ticks, at least 30 of which are post-eviction
- No NaN or infinity values in either stream

---

### TC-03 — Oracle Equivalence: Seeded Sim Scenario with Post-Eviction Coverage

**Type:** api
**Preconditions:**
- SimulatedProvider available with a seeded scenario that runs > 1000 ticks (sufficient to trigger multiple evictions on 10s window)
- `TapeEngine` instantiated with engine path (engine receives `eff_bid`/`eff_ask` from trades)
- Oracle comparator can sample post-eviction compute states

**Steps:**
1. Run a seeded sim scenario (e.g., existing SIM-BUYER or a custom deterministic scenario) with >1000 events
2. At every compute() call after the first eviction of any window, record incremental `bid_refresh_score` and `ask_refresh_score`
3. Compute oracle `_refresh_fractions()` for the same window at that tick
4. Assert exact equality for every sampled post-eviction tick
5. Confirm at least one 10s window evicted during the scenario

**Expected outcome:** All post-eviction refresh scores match the oracle exactly on seeded deterministic data

**Pass criteria:**
- Zero equality mismatches on post-eviction ticks
- At least one eviction confirmed in the test log
- Test completes deterministically (same seed ⇒ same result)

---

### TC-04 — CI Timing Gate: Dense Fixture Unpaced Replay

**Type:** api
**Preconditions:**
- Dense fixture committed and readable at configured path
- `dense_replay_time_budget_seconds` config key defined in `app/config.py`
- Budget documented with headroom (e.g., ≥5× measured dev-machine time)
- Test runs in CI without Alpaca credentials (uses committed fixture only)

**Steps:**
1. Start a fresh `TapeEngine` with empty state
2. Record wall-clock start time (time.time())
3. Replay entire dense fixture unpaced through the engine (no artificial delays between events)
4. Record wall-clock end time
5. Calculate elapsed_seconds = end - start
6. Read `dense_replay_time_budget_seconds` from config
7. Assert elapsed_seconds < config value

**Expected outcome:** Unpaced replay of dense fixture (≈10 minutes of real data) completes faster than the configured CI budget

**Pass criteria:**
- elapsed_seconds < dense_replay_time_budget_seconds
- elapsed_seconds logged for audit (must be well below budget, e.g., < 30 seconds for a typical development machine)
- No stall or timeout during replay

---

### TC-05 — Pinned Regression Anchors: Dense Fixture Final Values

**Type:** artifact
**Preconditions:**
- Dense fixture replayed successfully through the engine
- Final engine snapshot captured after all events processed
- At least one window of each size (10s, 30s, 60s, 180s, 300s) has evicted and recomputed

**Steps:**
1. Replay dense fixture to completion
2. Capture final engine state: `engine.current_snapshot()`
3. Extract exact final feature values: `bid_refresh_score`, `ask_refresh_score`, `buy_price_impact`, `sell_price_impact`, `absorption_score` for each window
4. Compare to committed anchor values (stored as test constants or a reference JSON file)
5. Assert equality (no tolerance; exact byte-identical or documented constant values)

**Expected outcome:** All pinned final-value anchors match the current implementation exactly

**Pass criteria:**
- All 5 refresh-score pairs (10s–300s windows) match pinned values
- At minimum buy/sell_price_impact and absorption_score also match
- No rounding or approx-equality; test fails on any mismatch
- Test file includes the exact anchor values with commit date and measurement context (symbol, date window, feed type)

---

### TC-06 — Error Case: Empty Window

**Type:** api
**Preconditions:**
- `TapeEngine` instantiated but no events processed yet
- Windows exist but contain zero trades and zero quotes

**Steps:**
1. Call `engine.current_snapshot()`
2. Access `bid_refresh_score` and `ask_refresh_score` from any window
3. Compare to oracle: call `_refresh_fractions()` on an empty window

**Expected outcome:** Refresh scores for an empty window match the oracle's empty-window behavior (typically 0 or NaN, byte-identical)

**Pass criteria:**
- Incremental refresh scores == oracle output for empty window
- No exception thrown; result is deterministic

---

### TC-07 — Error Case: Trades Before First Quote (No In-Effect Quote)

**Type:** api
**Preconditions:**
- `TapeEngine` on engine path
- Multiple trades are fed BEFORE any quote arrives

**Steps:**
1. Send 5–10 trades (each with arbitrary `eff_bid`/`eff_ask`) before sending the first quote
2. Compute refresh scores after all early trades, before any quote
3. Compare incremental values to oracle `_refresh_fractions()`
4. Send a quote; observe whether early trades (now without an in-effect quote in post-eviction logic) are SKIPPED in refresh evidence
5. Re-compare refresh scores to oracle

**Expected outcome:** 
- Early trades with no in-effect quote contribute zero refresh evidence (no fabrication)
- Incremental scores match the oracle's skip-behavior exactly

**Pass criteria:**
- Before quote arrives: refresh scores == oracle (both skip early trades)
- After quote arrives: only trades with in-window, in-effective quotes contribute evidence
- No exception; behavior is byte-identical to oracle

---

### TC-08 — Error Case: Quote Eviction Strips In-Effect Quote from Early Trade

**Type:** api
**Preconditions:**
- Window size configured (e.g., 10s for brevity)
- Engine at engine path
- An old trade T1 (t=0s) has an in-effect quote Q1 (t=0.5s)
- A newer quote Q2 (t=9s) arrives

**Steps:**
1. Send trade T1 at t=0s with `eff_bid`/`eff_ask` from Q1
2. Send quote Q2 at t=9s
3. Record refresh scores at t=9.1s (Q2 is in-window, T1 is in-window)
4. Advance time past t=10s so that Q1 evicts (only Q2 remains in-window)
5. At t=10.1s, compute refresh scores
6. Compare both snapshots (t=9.1 and t=10.1) to oracle `_refresh_fractions()`

**Expected outcome:** 
- At t=9.1s: both T1 (with Q1 in-effect) and newer trades contribute refresh evidence; matches oracle
- At t=10.1s: T1 now has no in-window quote (Q1 evicted), so T1 is SKIPPED; newer trades still contribute
- Both snapshots byte-identical to oracle

**Pass criteria:**
- Refresh scores at t=9.1 match oracle (T1 included)
- Refresh scores at t=10.1 match oracle (T1 skipped)
- No exception; behavior matches the merge oracle exactly

---

### TC-09 — Config Fingerprint Stability: Dense Replay Budget Key

**Type:** artifact
**Preconditions:**
- `config_fingerprint` method exists in `app/config.py`
- `dense_replay_time_budget_seconds` key is documented as excluded from fingerprinting (with rationale comment)
- A known classifier threshold (e.g., `confidence_threshold`) is included in fingerprinting

**Steps:**
1. Compute `config_fingerprint()` with current config (budget = 30)
2. Change `dense_replay_time_budget_seconds` to a different value (e.g., 45)
3. Recompute `config_fingerprint()`
4. Assert the two fingerprints are IDENTICAL (no change to hash/digest)
5. Change a real classifier threshold (e.g., `confidence_threshold` from 0.5 to 0.6)
6. Recompute `config_fingerprint()` again

**Expected outcome:**
- Fingerprint unchanged when budget key changes
- Fingerprint CHANGED when a real threshold changes
- Rationale comment in code explains why budget is excluded ("CI gate value never enters persisted computation")

**Pass criteria:**
- fingerprint(budget=30) == fingerprint(budget=45)
- fingerprint(threshold=0.5) ≠ fingerprint(threshold=0.6)
- Exclusion documented with iter-16 pattern (rationale + stability test + counter-test in same test file)

---

### TC-10 — Whole Existing Suite Stays Green

**Type:** api
**Preconditions:**
- All existing test files present:
  - `tests/test_features.py`
  - `tests/test_observer_equivalence.py` (7 test cases)
  - `tests/test_real_data_classify.py` (5 pinned scenarios)
  - `tests/test_real_data_gate.py` (35 test cases)
  - `tests/test_scenario.py` (determinism, SIM-BUYER, SIM-SELLER, etc.)

**Steps:**
1. Run full backend test suite: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
2. Capture exit code and pass/fail summary
3. Verify all 607+ tests pass (no re-pins, no relaxed assertions)

**Expected outcome:** All existing tests pass; no test count decrease; no feature value re-pins

**Pass criteria:**
- Exit code == 0
- Test count >= 607
- No tests skipped
- No changes to test assertions (review ensures no silent re-pins)

---

### TC-11 — Browser Sentinel: J-68 SIM-BUYER No-Thesis Cockpit Identical

**Type:** browser
**Preconditions:**
- Frontend started via `bash scripts/start-frontend.sh` (after dev completes)
- Backend started via `bash scripts/start-backend.sh` (after dev completes)
- Both services healthy (frontend reachable at http://localhost:3000, backend at http://localhost:8000/health)
- A prior engine snapshot of SIM-BUYER (no thesis declared) available for comparison (or taken pre-dev)

**Steps:**
1. Navigate to frontend home
2. Enter ticker: `SIM-BUYER`
3. Click Watch (in sim mode)
4. Wait for the cockpit to stabilize (confidence plateau, event log shows stable entries)
5. Take a full-page screenshot of the cockpit (scrolled to show panels, chart, observations, event log, confidence)
6. Verify the screenshot is non-blank and shows all expected panels
7. Compare visually to a baseline screenshot (or assert key elements are present: chart, state label, confidence score, observations, event log)

**Expected outcome:** 
- SIM-BUYER cockpit displays without error
- Panels render: state, confidence, chart with markers, observations, event log
- Visual composition identical to pre-dev baseline (no layout shifts, color changes, or missing elements due to engine change)

**Pass criteria:**
- Screenshot file saved at `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-17-evidence/TC-11-sim-buyer-cockpit.png`
- Screenshot file size > 50 KB (non-blank sanity check)
- All expected visual elements present (state label, chart, confidence bar, observations, event log)
- No JavaScript errors in browser console

---

### TC-12 — Browser: J-08 REST vs UI Agreement Spot Check

**Type:** browser
**Preconditions:**
- Frontend and backend running
- SIM-BUYER or a sim scenario already watched via browser
- Backend REST endpoint `/tape/SIM-BUYER` accessible

**Steps:**
1. Fetch the tape state via REST: `curl http://localhost:8000/tape/SIM-BUYER`
2. Parse JSON response: extract `state`, `confidence`, `bid_refresh_score`, `ask_refresh_score`
3. On the same browser UI, note the visually displayed state and confidence
4. Compare: REST state == UI displayed state
5. Compare: REST confidence (as a float) matches the confidence bar/label on UI
6. Compare: REST refresh scores are consistent with the engine view (sanity check, no specific display requirement but value must be present in REST)

**Expected outcome:** REST response and UI display show identical tape state and confidence for the same snapshot

**Pass criteria:**
- state value from REST == tape state label on UI
- confidence from REST matches the UI confidence display (within rounding)
- No REST errors (HTTP 200)
- Response JSON includes all required fields

---

## Summary

**Total test cases:** 12
- **API tests:** 8 (TC-01, TC-02, TC-03, TC-04, TC-06, TC-07, TC-08, TC-10)
- **Browser tests:** 2 (TC-11, TC-12)
- **Artifact tests:** 2 (TC-05, TC-09)

**Coverage:**
- Structural no-rescan (incremental complexity claim) — TC-01
- Oracle equivalence (byte-identity proof) — TC-02, TC-03
- CI timing gate (performance gate) — TC-04
- Regression anchors (pinned feature values) — TC-05
- Error cases (empty window, trades before quote, quote eviction strip) — TC-06, TC-07, TC-08
- Config discipline (fingerprint stability + counter) — TC-09
- Existing suite regression — TC-10
- Browser regression sentinel (J-68 and J-08) — TC-11, TC-12
