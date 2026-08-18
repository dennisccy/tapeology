# UI Test Results (merged)

**Date:** 2026-08-18
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 3/3 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-8-evidence/J-01-verify.png |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-8-evidence/J-10-verify.png |
| UT-J-06 | J-06 — The recorder and the Vault — new tape, sealed at birth (step-2 regression check) | regression | P1 | Iteration 8 ships J-06 step 2 (`tick_recorder.py`) with zero new frontend surface (`Frontend Present: yes` is declared solely to keep this regression lane running); the pre-existing Microscope Readiness section on `/desk` (built by J-01) must keep rendering correctly and honestly through the exact backend surfaces this iteration touched (`datasets.py`, `providers/base.py` TradeEvent/QuoteEvent hash fix, `walkforward.py` fold-ledger reorder + `_tick_dataset_session_dates` errors-channel fix) — QA-rig fixture-scoped values of 1 symbol-day / 2 datasets / 2 legacy-shard rows, the readiness gate reading unmet against the 150-symbol-day floor, an honest "No integrity errors." line, both shards still `exposure_state: exploratory` — and no premature Recorder/Vault UI section (that lands with J-08) | Navigated to `/desk`, expanded Microscope Readiness (`data-testid=desk-section-expand-microReadiness`). Rendered Corpus Totals: Distinct symbol-days 1, Distinct datasets 2, RTH minutes covered 1.75, Session-equivalents 0.0045, Referee tick-gate (symbol-days) 150. Legacy Tick Shards: exactly 2 rows (PG 2026-06-09 ×2), both `exposure_state` "exploratory", split provenance "hand_assigned", checksums rendered verbatim. Pilot-Study Floors: all 3 studies (range_wall_failed_aggression, delta_divergence_level_tests, capitulation_exhaustion) status "floor_unmet" (60 required vs 1 available). "No integrity errors." served at section foot. All values byte-match a direct `curl GET /research/desk/micro/readiness` taken in the same session. Full-page text/markdown extraction of `/desk` confirms no Scout Ledger / Walk-Forward / Validation Vault section exists yet (only the pre-existing Screen, Playbook Signals, Backscan, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, and Microscope Readiness sections render) — correctly matching this iteration's declared zero frontend delta. Zero console errors/warnings captured across the whole browser session. | PASS | `reports/qa/goal-rapid-microscope-iter-8-evidence/UT-J-06-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-18


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | J-02 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-03 | J-03 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-04 | J-04 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-05 | J-05 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
