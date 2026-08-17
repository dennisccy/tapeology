# UI Test Results (merged)

**Date:** 2026-08-17
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/9 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-6-evidence/J-01-verify.png |
| UT-01 | `/desk` loads without errors | smoke | P1 | Heading "Playbook Signals" visible, no blank screen/error banner/console exception | Heading "Playbook Signals" rendered; all 10 collapsible sections present; no error banner; console showed only the benign React-DevTools notice | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-01-result.png` |
| UT-02 | Microscope Readiness shows real corpus data | regression | P1 | Corpus Totals: Distinct symbol-days=12, Distinct datasets=18; Legacy Tick Shards: exactly 18 rows, every row Split provenance=`hand_assigned`, Exposure state=`exploratory` | Corpus Totals: Distinct symbol-days=**1**, Distinct datasets=**2**; Legacy Tick Shards: **2** rows only (both symbol PG, session 2026-06-09); the 2 present rows DO show Split provenance=`hand_assigned` and Exposure state=`exploratory` | **FAIL** | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-02-fail.png` |
| UT-03 | Cockpit ticker watch still works | regression | P1 | "No ticker watched" before watch; "Buyer Control" after typing SIM-BUYER + clicking Watch | Both states observed exactly; tape state "Buyer Control", confidence 0.950, live quote/trades/features/observations all populated; no error toast | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-03-result.png` |
| UT-04 | `/structure` Tradable Map still loads | regression | P1 | "Tradable Map" on load; after AAPL + `2026-06-22 17:00:00` + Load, text "300.11–302.2" appears | "Tradable Map" visible on load; after Load, resistance band row `300.11–302.2 · Class A · score 171 · 849 members · round number` rendered exactly | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-04-result.png` |
| UT-05 | Playbook Evidence section still renders | regression | P1 | "Built from signature:" after expand; "recorded signals, none hidden" after typing date | Both strings found verbatim (record `playbook_2026_06_22_803fc798424e`, recorded at 2026-08-17 16:25:52 ET, session date 2026-06-22) | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-05-result.png` |
| UT-06 | Referee Registry shows frozen fingerprint | regression | P1 | Text "config fingerprint 08e471b10130e1e2" appears | Text found verbatim, matching TC-10's independent backend check | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-06-result.png` |
| UT-07 | Referee Adjudications/Runs honest-empty states | regression | P1 | "No hypotheses registered"; "No evaluation runs recorded yet." | Both empty-states found verbatim, no fabricated rows, no stuck spinner | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-07-result.png` |
| UT-08 | Microscope Readiness discoverable | ux | P2 | "Microscope Readiness" is the last section, directly below "Referee Runs", reachable by scroll alone | Confirmed: fresh `/desk` load section order ends `... ▸Referee Adjudications, ▸Referee Runs, ▸Microscope Readiness`; human-readable label, no code name | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-08-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-17


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | J-02 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-03 | J-03 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-04 | J-04 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |

## Auditor note (appended 2026-08-17, not written by the merge tool)

The headline above is wrong, and the reason is a tool defect, not a resolved failure. The LLM
browser lane's own record (`...-ui-test-results.llm.md`) states FAIL, and its UT-02 row states FAIL.
`merge_ui_test_results.py:64` matches a verdict cell only against the bare tokens PASS/FAIL/SKIP;
that row's cell is markdown-emphasised, so it parsed as no verdict at all, and `compute_overall`
then derived the headline from the surviving rows alone (the source file's own headline is consulted
only when NO row parses). Reproduced deterministically against these exact files. See
`docs/handoffs/goal-rapid-microscope-iter-6-audit.md` finding E1.

On the substance: UT-02's failure is an expectation defect in the UI test plan (it expects the real
store's 12 symbol-days / 18 datasets from a rig that seeds two PG fixture datasets by design), not a
product regression — the real store was re-derived live and still serves 12 / 18 / 3.0089 with all
18 shards `exploratory` + `hand_assigned`.
