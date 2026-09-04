# Goal Iteration goal-observation-contract-iter-4 — UI Test Results

**Phase:** goal-observation-contract-iter-4
**Date:** 2026-09-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

Scope note (read before the table): iter-4's own spec (`docs/phases/goal-observation-contract-iter-4.md`)
is explicit that **J-04's full journey Acceptance cannot be newly satisfied this iteration** — the
Acceptance depends on comparing real `observation_hash` / `generated_at_utc` / `artifact_hash` values from
the served JSON at `/tape/SIM-BIDABS/observation`, and that route does not exist until iteration 5 (Binding
Execution Order step 5). This iteration touches zero files under `apps/backend/app/`
(`Frontend Present: no`), so its own Testing Requirements + Definition of Done define the actual browser-qa
deliverable for this round as a **regression smoke check**: confirm `/tape/SIM-BIDABS/observation` still
answers "Not Found" across two reloads, confirm `/structure` and `/desk` render unchanged, and confirm
Watch → Pause → Resume → Stop on `/` still transition the status dot through `live` → `paused` → `live` →
closed, in that order. UT-J-04 below is scored on that regression-smoke scope, which is what this
iteration's spec explicitly asks browser-qa to confirm — not on J-04's full merged acceptance, which
correctly remains unmet until the route ships (the spec's own words: "expected, correct, not a defect").
This matches the exact convention iter-3 established for UT-J-03 (same route-absence situation, same
scoring approach).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-04 | Ingestion-path equivalence under an identical valid event stream (regression-smoke scope: watch lifecycle transitions + honest 404 persistence of the not-yet-built route across two reloads) | regression/smoke | P1 | Watch→live, Pause→paused, Resume→live, Stop→closed(idle); `/tape/SIM-BIDABS/observation` answers 404 on both of two reloads (route not yet built, per iter-4 scope); `/structure`/`/desk` render unchanged | All transitions occurred exactly as expected on `/`; `/tape/SIM-BIDABS/observation` returned "404" / "This page could not be found." on both reloads (checked in an isolated tab, then reloaded once more); the Cockpit tab was unaffected by the other tab's navigation (still showed "paused" throughout); `/structure` and `/desk` loaded normally with their existing headings and controls, no crash, no new panel. The JSON-content assertions in J-04's literal steps (`observation_hash`, `generated_at_utc`, `artifact_hash`) could not be read from the browser because the endpoint does not exist yet — expected and correct per the iter-4 spec, not a defect | PASS | `reports/qa/goal-observation-contract-iter-4-evidence/UT-J-04-result.png` |

---

## Passed Tests

### UT-J-04 — Ingestion-path equivalence under an identical valid event stream (iter-4 regression-smoke scope)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-observation-contract-iter-4-evidence/UT-J-04-result.png` (screenshot taken at
the second reload of `/tape/SIM-BIDABS/observation`, showing the "404" heading and "This page could not be
found." body — the core, iteration-specific fact this round needs confirmed: the route's absence persists
unchanged)

Executed against the goal file's J-04 steps (`runs/goal-session-observation-contract/iter-4/goal-slice-bqa.md`,
"Must-have user journeys" → J-04) plus this iteration's Testing Requirements section, using two tabs so that
checking the (currently 404) observation endpoint never disturbed the Cockpit's live/paused watch state — the
same tab-isolation technique iter-3's UT-J-03 established was necessary (a hard `navigate` on the Cockpit tab
itself resets its client-side watch UI to "No ticker watched"; this is pre-existing SPA behavior unrelated to
this iteration's test-only changes, not a regression):

1. **Baseline:** Visited `/`. Confirmed idle state via page text: "No ticker watched. Enter a ticker above
   and click Watch...".
2. **Watch (Step 1, first half):** Clicked `Simulated` (button text confirmed via DOM query:
   `["Live","Historical","Simulated","Watch"]`), typed `SIM-BIDABS` into the ticker input
   (`input[placeholder="Ticker e.g. SIM-BUYER"]`, value confirmed set), clicked `Watch`. Used `await_text`
   for `"live"` (succeeded within timeout), then confirmed via DOM query: status text `"live"`, button set
   `["Watch","Pause","Stop"]`.
3. **Pause (Step 1, second half):** Clicked `Pause`. Confirmed via DOM query: status text `"paused"`, button
   set `["Watch","Resume","Stop"]`.
4. **Two reloads of the observation route (Step 1, core assertion):** Opened
   `/tape/SIM-BIDABS/observation` in a **new tab** (to leave the Cockpit tab's paused state undisturbed).
   `extract` (text format) showed: `Tapeology / Cockpit / Structure / Desk / 404 / This page could not be
   found.` — reload #1 confirms 404, exactly as expected (route ships iteration 5, per this iteration's own
   Out of Scope section). Navigated the same tab to the identical URL again (reload #2): DOM summary showed
   `Headings: "404"` again — confirmed unchanged. Screenshot taken at this point (evidence file above).
   The literal Step-1 comparison of `observation_hash`/`generated_at_utc`/`artifact_hash` across the two
   loads is not observable from the browser this iteration (no JSON is served); that comparison is the
   subject of the new `test_tape_observation_path_equivalence.py` pytest module, which is outside
   browser-qa's scope and was not re-run here (verified by the developer/reviewer pipeline stage).
5. **Cockpit-tab isolation check:** Switched back to the Cockpit tab (still at `/`) and re-queried its DOM:
   status text was still `"paused"`, button set still `["Watch","Resume","Stop"]` — confirms the second
   tab's navigation did not disturb the Cockpit's watch state, and that the paused watch was genuinely still
   live server-side underneath.
6. **Resume (this iteration's Testing Requirements regression check):** Clicked `Resume`. Confirmed via DOM
   query: status text `"live"`, button set `["Watch","Pause","Stop"]`.
7. **Stop:** Clicked `Stop`. Page text returned to the idle placeholder: "No ticker watched. Enter a ticker
   above and click Watch...". DOM query confirmed status text `"idle"` and button set back to
   `["Live","Historical","Simulated","Watch"]` — this app-level label for the closed/no-watch state is
   `"idle"` (not the literal word "closed"), matching iter-3's independent finding for the same control;
   pre-existing behavior, unrelated to any change this iteration (this iteration touches zero files under
   `apps/backend/app/` and zero frontend files).
8. **`/structure` regression spot-check:** Navigated to `/structure`. DOM summary: heading `"Structure"`,
   5 buttons, 7 inputs, 2 forms — renders normally, no crash, no new panel/link/control versus the
   established baseline.
9. **`/desk` regression spot-check:** Navigated to `/desk`. DOM summary: heading `"Desk"`, 21 buttons,
   7 inputs — renders normally, no crash, no new panel/link/control.

Both spot-checks (8-9) and the lifecycle-transition checks (2, 3, 6, 7) are named explicitly in this
iteration's own Testing Requirements/Definition of Done as the correct browser-qa deliverable when
`Frontend Present: no` and the route is still absent — not a separate UT row, folded into UT-J-04's scope
alongside J-04's own literal double-reload check.

**Out of browser-qa scope this iteration** (verified by the developer/reviewer pipeline stage instead, per
this iteration's own Testing Requirements): running
`cd apps/backend && .venv/bin/python -m pytest tests/test_tape_observation_path_equivalence.py -q` and its
`test_counterexample_*` mutation proof; confirming `field_partition_map()`'s four groups are unchanged from
iteration 1; the full backend suite baseline count; `tsc --noEmit`.

**Golden replay script written:** `runs/goal-session-observation-contract/journey-scripts/J-04.json`
(lint-checked clean via `demo_runner.py --mode lint`). Like iter-3's `J-03.json`, it performs the full
click-based Watch → Pause → Resume → Stop cycle **before** the two `goto` reloads of the observation route,
rather than interleaving the reloads between Pause and Resume as J-04's literal step order reads: the
replay runner drives one continuous browser context per journey with no multi-tab primitive, and a hard
`goto` away from `/` resets the Cockpit's client-side watch indicator (the same constraint iter-3 documented
for `J-03.json`). Placing both observation-route reloads last preserves the Watch→Pause→Resume→Stop chain
intact while still proving the route stays absent — checked twice in a row, immediately after a real
Stop — which is at least as strong a check of "the route is honestly still not built" as the literal
mid-pause ordering.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (headless, pinned profile/CDP port)
- **Test Date:** 2026-09-04
- **Evidence directory:** `reports/qa/goal-observation-contract-iter-4-evidence/`
