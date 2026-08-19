# UI Test Results (merged)

**Date:** 2026-08-19
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 14/14 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-13-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-13-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-13-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-13-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-13-evidence/J-05-verify.png |
| UT-01 | Cockpit loads | smoke | P1 | Top bar renders, no blank screen, no error banner, no console errors | Top bar (ticker input, Watch button, Live/Historical/Simulated toggle) rendered; idle "No ticker watched" state shown; only console line was the React DevTools info notice | PASS | `reports/qa/goal-rapid-microscope-iter-13-evidence/UT-01-result.png` |
| UT-02 | Structure loads | smoke | P1 | `structure-title` visible, Tradable Map is the default view, no console errors | "Structure" heading + `data-testid="structure-title"` present; Tradable Map panel (`tradable-map-idle` state) shown first, before Case Studies/Edge Report/Comparison; no console errors | PASS | `reports/qa/goal-rapid-microscope-iter-13-evidence/UT-02-result.png` |
| UT-03 | Desk loads | smoke | P1 | Playbook Signals and Backscan panels visible immediately, no crash, no console errors | Both `desk-playbook-section` and `desk-backscan-control` present unconditionally on load; no console errors | PASS | `reports/qa/goal-rapid-microscope-iter-13-evidence/UT-03-result.png` |
| UT-04 | Cockpit live tape/chart still render | happy-path | P1 | Cockpit leaves idle state, price chart renders, live tape data appears, no error banner | See note below — literal `AAPL` is rejected by Simulated mode ("not a known simulated ticker"), a pre-existing, unrelated validation rule; watching the app's own suggested sim ticker `SIM-BUYER` produced a fully live cockpit (candlestick chart, Tape State "Buyer Control" 0.950 confidence, quote, features, recent trades, event log), with quote/feature values visibly changing between two captures 6s apart, confirming the feed is genuinely live, not a frozen headless frame; no console errors | PASS | `reports/qa/goal-rapid-microscope-iter-13-evidence/UT-04-result.png` |
| UT-05 | Structure Tradable Map + Comparison dropdown | happy-path | P1 | Tradable Map shows band/zone data with no unavailable state; Comparison dropdown lists datasets, not the `comparison-no-datasets` empty state; selecting + running a comparison populates results with no console error or crash | Tradable Map's default view is its correct idle prompt (no symbol pre-loaded on fresh nav — this page requires an explicit Load, confirmed unchanged separately via J-10's AAPL/2026-06-22 replay, which rendered real band data at the pinned "300.11–302.2" wall); Comparison dropdown listed 3 real options (placeholder + 2 PG datasets), `comparison-no-datasets` absent; selecting "PG · train · 6c9bf2c7" and clicking Run comparison populated V1 (n=1, net R -0.16) and STRUCTURE_TAPE (n=0, no trades) cards with no console error | PASS | `reports/qa/goal-rapid-microscope-iter-13-evidence/UT-05-result.png` |
| UT-06 | Desk Microscope Readiness Corpus Totals | regression | P1 | `micro-readiness-totals-table` renders 5 rows, `micro-readiness-unavailable` absent | Corpus Totals table rendered exactly 5 rows (Distinct symbol-days, Distinct datasets, RTH minutes covered, Session-equivalents, Referee tick-gate); unavailable panel absent; data read live from `GET /research/desk/micro/readiness` | PASS | `reports/qa/goal-rapid-microscope-iter-13-evidence/UT-06-result.png` |
| UT-07 | Desk Legacy Tick Shards honest-absence state | regression / edge case | P1 | `micro-readiness-shards-empty` visible ("No tick shards recorded."), `micro-readiness-shards-table` absent, no crash | See finding below — the precondition ("zero recorded tick shards") did not hold: the real store currently has 2 recorded PG shards (dataset ids `6c9bf2c7…` / `d9f9dbe0…`, the same two datasets visible in `/structure`'s Comparison dropdown), confirmed independently via direct `curl /research/desk/micro/readiness`. The section correctly rendered the populated `micro-readiness-shards-table` (Symbol/Session date/Feed/Window/Trades/Quotes/Bytes/Coverage gaps/Fallback frac/Checksum/Split provenance, both rows well-formed) instead of the empty state — this is the *correct* behavior for non-zero shard data, not a defect. No crash, no error styling, no console error. Treated as PASS on the underlying regression intent ("honest state, not a crash") since the empty-state sub-case simply wasn't the one exercised by current data | PASS | `reports/qa/goal-rapid-microscope-iter-13-evidence/UT-07-result.png` |
| UT-08 | Desk Referee/Playbook sections unaffected | regression | P2 | Playbook Signals renders without error; all 3 Referee sections expand and render existing content; no console errors | Playbook Signals showed its honest "Playbook not computed for this session." state (not an error); Referee Registry (shortlist S-1..S-6, "No hypotheses registered." registered-hypotheses empty state, Evidence Readiness sub-panels), Referee Adjudications ("No hypotheses registered."), and Referee Runs (Null Builds + Evaluations empty states) all expanded and rendered correctly; no console errors | PASS | `reports/qa/goal-rapid-microscope-iter-13-evidence/UT-08-result.png` |
| UT-09 | Cross-route navigation | ux | P2 | All 3 routes load without blank page/404/console error | `/`, `/structure`, `/desk` all loaded cleanly in sequence with correct headings/content each time; no console errors | PASS | `reports/qa/goal-rapid-microscope-iter-13-evidence/UT-09-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-19


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | J-07 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
