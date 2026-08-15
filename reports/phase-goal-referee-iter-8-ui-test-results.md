# UI Test Results (merged)

**Date:** 2026-08-15
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 12/12 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-referee-iter-8-evidence/J-10-verify.png |
| UT-01 | Desk page loads without errors | smoke | P1 | Page renders, "Desk" heading visible, nav has exactly Cockpit/Structure/Desk, no console errors | Page rendered fully; `[data-testid="desk-title"]` text = "Desk"; nav links = ["Cockpit","Structure","Desk"]; console showed only a React DevTools info line | PASS | `reports/qa/goal-referee-iter-8-evidence/UT-01-result.png` |
| UT-02 | Referee Registry expands, 5 shortlist rows render | smoke | P1 | Section expands (▸→▾), 5-row shortlist table S-1..S-5, Registered Hypotheses heading + empty state | `aria-expanded` flipped false→true, glyph "▾Referee Registry"; table rows exactly `referee-shortlist-row-S-1`..`S-5` in order, each with rationale + numeric columns; "REGISTERED HYPOTHESES / No hypotheses registered." rendered below | PASS | `reports/qa/goal-referee-iter-8-evidence/UT-02-result.png` |
| UT-03 | Zero-corpus candidates render honestly, never crash | smoke | P1 | S-4/S-5 rows render fully; Accrual/day "0.00"; Projected days "—"; no crash | S-4 row: estimand B, "range_trade:long (at_wall)", n=0, accrual "0.00", projected days "—". S-5 row: estimand C, same setup/side, same honest zero values. Page did not crash or blank | PASS | `reports/qa/goal-referee-iter-8-evidence/UT-03-result.png` |
| UT-04 | Select a candidate, review confirm panel | happy-path | P1 | Confirm panel appears with exact text; Confirm/Cancel buttons; no write yet | Panel text exactly "Register S-4 (range_trade:long, Estimand B)? This records a permanent, boundary-stamped hypothesis — the boundary is stamped at registration time and can never move."; both buttons present; hypotheses table still showed the empty state | PASS | `reports/qa/goal-referee-iter-8-evidence/UT-04-result.png` |
| UT-05 | Cancel a pending selection | happy-path | P1 | Panel disappears; S-4 button still "Select"; no write occurred | Panel removed from DOM; `referee-shortlist-select-S-4` text = "Select"; hypotheses table unchanged (still empty) | PASS | `reports/qa/goal-referee-iter-8-evidence/UT-05-result.png` |
| UT-06 | Complete registration end-to-end (real write) | happy-path | P1 | Panel closes; new row in Registered Hypotheses with boundary/origin/status; S-1 button becomes disabled "Registered" | Selected S-1, clicked Confirm Registration (real write against the confirmed-scoped fixture backend). Panel closed; `referee-hypotheses-row-S-1` = "S-1 / capitulation:long / 2026-08-15 / historical-exploration / active / 0 / 12 / 1 / 1 discovery (exploratory)"; `referee-shortlist-select-S-1` now reads "Registered" and is `disabled` | PASS | `reports/qa/goal-referee-iter-8-evidence/UT-06-result.png` |
| UT-07 | Discovery vs. accrual render distinctly | happy-path | P1 | Accrual "0 / 12"; Discovery > 0 with italic "discovery (exploratory)" label, visually distinct, never a badge | Accrual cell = "0 / 12"; `referee-discovery-S-1` = "1 / 1 discovery (exploratory)"; cell markup is `<td class="... text-slate-500"><span class="font-mono ...">1 / 1</span> <span class="italic">discovery (exploratory)</span></td>` — plain italic text in its own column, no badge/pill classes | PASS | `reports/qa/goal-referee-iter-8-evidence/UT-07-result.png` |
| UT-08 | Already-registered candidate can't be re-selected | validation | P2 | After reload, S-1 button reads "Registered", disabled; click has no effect | Reloaded `/desk`, re-expanded section: `referee-shortlist-select-S-1` outerHTML carries `disabled=""` and text "Registered"; clicking it opened no confirmation panel | PASS | `reports/qa/goal-referee-iter-8-evidence/UT-08-result.png` |
| UT-09 | Stale-tab duplicate registration shows inline error | error | P2 | Tab A's stale confirm is refused (409); inline red error with backend's own text; no crash | Tab A selected S-2 (panel open); Tab B (new tab) selected+confirmed S-2 successfully (`referee-hypotheses-row-S-2` appeared with historical-exploration origin); switching back to Tab A and clicking Confirm Registration on the stale panel produced `[data-testid="referee-registration-error"]` = "a hypothesis record with id 'S-2' is already recorded -- hypothesis records are immutable and are never re-recorded", styled `text-red-300`; the panel, shortlist table and rest of the section remained intact (no blank-out) | PASS | `reports/qa/goal-referee-iter-8-evidence/UT-09-result.png` |
| UT-10 | Playbook Evidence and prior sections unaffected | regression | P3 | Playbook Evidence expands with unchanged content; all pre-existing sections still present above Referee Registry | Expanded "Playbook Evidence": full real evidence table rendered (all setup/side/measure rows, signature/basis block, invalidation-breaches table) exactly as its own established shape. Section-header list confirms order `topupRuns, indexReconciliation, screenRuns, playbookEvidence, refereeRegistry` — every pre-existing section present, Referee Registry strictly last. No console errors | PASS | `reports/qa/goal-referee-iter-8-evidence/UT-10-result.png` |
| UT-11 | Referee Registry is discoverable | ux | P3 | Reachable via one scroll + one click; no separate nav item; plain-language intro text before the table | Nav bar carries only Cockpit/Structure/Desk (confirmed via UT-01's eval) — no dedicated Referee nav entry or hidden menu; the section lives on `/desk` itself (no undocumented URL); its header is the last `CollapsibleSection` on the page (one scroll away) and one click expands it (already exercised in UT-02/UT-08); its intro text — "Spec-pinned starter-family candidates (docs/referee-statistical-spec.md §7) beside their live sample-size readiness. Registering one writes a permanent, boundary-stamped hypothesis — historical observations before that boundary are discovery, never confirmation." — renders directly above the table | PASS | `reports/qa/goal-referee-iter-8-evidence/UT-11-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-15


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | J-01 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-02 | J-02 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-03 | J-03 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-04 | J-04 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-05 | J-05 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-06 | J-06 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
