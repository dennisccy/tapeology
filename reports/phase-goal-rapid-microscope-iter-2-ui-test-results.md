# UI Test Results (merged)

**Date:** 2026-08-17
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 6/9 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-10 | The kept product stands — traps armed, sentinel green (browser-testable sentinel subset: cockpit `/`, `/structure` load + Tradable Map, every shipped `/desk` section) | regression | P1 | Cockpit, `/structure`, and every shipped `/desk` section render exactly as shipped — the rollup of UT-05/06/07/08 | 2 of the 4 named surfaces (`/structure` Tradable Map, `/desk` Playbook Signals filters) do not meet their literal expected result on this rig's current data state (see UT-06/UT-07); cockpit and the three Referee sections are clean. The prior replay's specific complaint (step 9, signature hash `b06e0bc289c54d77` not appearing) is CONFIRMED a stale/volatile assertion — see note below — but the journey still does not pass this run for the two reasons above. | FAIL | see UT-05/06/07/08 evidence above |
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders, "Desk" heading visible, Microscope Readiness section visible at bottom, collapsed | `desk-title` = "Desk" confirmed in DOM; Microscope Readiness is the last section, `aria-expanded="false"`, "▸" marker; no error boundary; no blank screen | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-01-result.png` |
| UT-02 | Microscope Readiness shows real 2-row PG data | happy-path | P1 | Distinct symbol-days=1, distinct datasets=2, 2 shard rows (PG/sip/2026-06-09), floors table populated, "No integrity errors." | All values matched exactly: `distinct-symbol-days`="1", `distinct-datasets`="2", 2 shard rows both PG/sip/2026-06-09, 3-row floors table (all `floor_unmet`), integrity-errors empty state present | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-02-result.png` |
| UT-03 | Microscope Readiness discoverability | ux | P2 | Reachable by scroll alone, collapsed by default like sibling sections, one click reveals data | Confirmed: last of 5 collapsible sections (Top-up Runs/Index Reconciliation/Screen Runs/Playbook Evidence/Referee Registry/Referee Adjudications/Referee Runs/Microscope Readiness), all "▸" on fresh load, in DOM order, no extra nav | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-03-result.png` |
| UT-04 | Backend-down honest unavailable state | error | P2 | Shipped `micro-readiness-unavailable` component renders a readable message, no blank/crash | Simulated fetch failure (see methodology note below) produced `data-testid="micro-readiness-unavailable"` with "Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place." No blank screen, no stack trace | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-04-result.png` |
| UT-05 | Cockpit watch flow unaffected | regression | P1 | Live cockpit chart renders within seconds, no error banner | Typed SIM-BUYER, clicked Watch: "Watching SIM-BUYER", Tape State "Buyer Control" 0.950, live 10s chart with candles+volume, Quote/Features/Recent Trades/Observations/Event Log all populated, no error banner | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-05-result.png` |
| UT-06 | Structure Tradable Map load unaffected | regression | P1 | Tradable Map panel renders bands/levels for PG with no error message | As literally specified (symbol PG, "Today"→2026-08-17 19:59:59, Load): panel shows "No bar series recorded for PG. Recording historical bars needs provider credentials." — an honest empty state, not bands. See Failed Tests for corroboration that `/structure` itself is not broken. | FAIL | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-06-fail.png` |
| UT-07 | Playbook Signals filters + Playbook Evidence unaffected | regression | P1 | Filters narrow the signals table (N≤M); Playbook Evidence expands with no error boundary | On the default/blank session date, `desk-playbook-band-filter`/`desk-playbook-inside-filter` do not exist in the DOM at all ("Playbook not computed for this session."). See Failed Tests for corroboration that the filters work correctly (0 of 5) once a session with recorded signals is selected; Playbook Evidence itself expanded correctly in both states. | FAIL | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-07-result.png` |
| UT-08 | Referee Registry/Adjudications/Runs unaffected | regression | P1 | Each of the 3 panels expands with no error boundary, no testid/heading changes | All 3 expand correctly: Registry shows 6-candidate table + Evidence Readiness (config fingerprint `08e471b10130e1e2`, matches frozen pin); Adjudications "No hypotheses registered."; Runs shows Null Builds/Evaluations honest empty states. No collisions with Microscope Readiness | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-08-result.png` |

## Failed Tests

### UT-J-10 — The kept product stands — traps armed, sentinel green (browser-testable sentinel subset: cockpit `/`, `/structure` load + Tradable Map, every shipped `/desk` section)

**Verdict:** FAIL
**Failure:** 2 of the 4 named surfaces (`/structure` Tradable Map, `/desk` Playbook Signals filters) do not meet their literal expected result on this rig's current data state (see UT-06/UT-07); cockpit and the three Referee sections are clean. The prior replay's specific complaint (step 9, signature hash `b06e0bc289c54d77` not appearing) is CONFIRMED a stale/volatile assertion — see note below — but the journey still does not pass this run for the two reasons above.
**Evidence:** `see UT-05/06/07/08 evidence above`

### UT-06 — Structure Tradable Map load unaffected

**Verdict:** FAIL
**Failure:** As literally specified (symbol PG, "Today"→2026-08-17 19:59:59, Load): panel shows "No bar series recorded for PG. Recording historical bars needs provider credentials." — an honest empty state, not bands. See Failed Tests for corroboration that `/structure` itself is not broken.
**Evidence:** ``reports/qa/goal-rapid-microscope-iter-2-evidence/UT-06-fail.png``

### UT-07 — Playbook Signals filters + Playbook Evidence unaffected

**Verdict:** FAIL
**Failure:** On the default/blank session date, `desk-playbook-band-filter`/`desk-playbook-inside-filter` do not exist in the DOM at all ("Playbook not computed for this session."). See Failed Tests for corroboration that the filters work correctly (0 of 5) once a session with recorded signals is selected; Playbook Evidence itself expanded correctly in both states.
**Evidence:** ``reports/qa/goal-rapid-microscope-iter-2-evidence/UT-07-result.png``

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-17

