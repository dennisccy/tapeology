# Phase goal-referee-iter-8 — UI Test Results

**Phase:** goal-referee-iter-8
**Date:** 2026-08-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 11/11 tests passed (0 skipped)

Precondition check before any write-path test: `apps/backend/.venv/bin/python
apps/backend/scripts/assert_scoped_qa_backend.py` returned exit 0 ("SCOPED ... this backend
serves the fixture rig"), so UT-06 through UT-09 (the real, irreversible registry writes) were
run normally per the dispatch instructions.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
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

---

## Passed Tests

### UT-01 — Desk page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-8-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/desk`; page rendered with heading "Desk" and the full set of pre-existing sections. `document.querySelector('[data-testid="desk-title"]').textContent` = "Desk". Nav links (`nav a`) = exactly `["Cockpit","Structure","Desk"]`. Console held only the standard React DevTools info line — no errors.

### UT-02 — Referee Registry section expands and shows all 5 shortlist candidates
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-8-evidence/UT-02-result.png`
- Clicked `[data-testid="desk-section-expand-refereeRegistry"]`. `aria-expanded` went `false`→`true`, header text became "▾Referee Registry". `referee-shortlist-table` rendered with rows `referee-shortlist-row-S-1` through `S-5` in that exact order, each carrying a non-empty rationale and numeric n/Sessions/Accrual/Projected-days values. "REGISTERED HYPOTHESES" heading followed by "No hypotheses registered." (matching the live, pre-write registry state confirmed via `curl http://localhost:8301/research/desk/referee/registry` → `hypotheses: []`).

### UT-03 — Zero-corpus candidates render honest placeholder values, never a crash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-8-evidence/UT-03-result.png`
- Row `referee-shortlist-row-S-4`: "S-4 / B / range_trade:long (at_wall) / 1h / ... / 0 / 0 / 0.00 / —". Row `referee-shortlist-row-S-5`: "S-5 / C / range_trade:long (at_wall) / 1h / ... / 0 / 0 / 0.00 / —". Both rows rendered completely (never missing/blank), Accrual/day showed "0.00" (not NaN/Infinity/blank), Projected days showed the em dash "—" (not "0"/NaN/Infinity). No error message, no crash.

### UT-04 — Operator selects a candidate and reviews the confirmation panel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-8-evidence/UT-04-result.png`
- Clicked `referee-shortlist-select-S-4`. `referee-registration-confirm-panel` text (verified via `textContent`) was exactly: "Register S-4 (range_trade:long, Estimand B)? This records a permanent, boundary-stamped hypothesis — the boundary is stamped at registration time and can never move." Both "Confirm Registration" and "Cancel" buttons present. `referee-hypotheses-empty` still showed "No hypotheses registered." — confirming no write occurred yet.

### UT-05 — Operator cancels a pending selection
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-8-evidence/UT-05-result.png`
- Clicked `referee-registration-cancel-button`. Confirmation panel removed from the DOM immediately. `referee-shortlist-select-S-4` text remained "Select" (not "Registered"). Hypotheses empty-state text unchanged from before the selection.

### UT-06 — Operator completes registration end-to-end (real write)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-8-evidence/UT-06-result.png`
- Confirmed the QA backend is the fixture-scoped rig (`assert_scoped_qa_backend.py` exit 0) before running this test. Selected S-1, clicked "Confirm Registration". Panel closed on success. New row `referee-hypotheses-row-S-1` appeared: Hypothesis "S-1", Setup/Side "capitulation:long", Boundary "2026-08-15" (today), Origin "historical-exploration", Status "active", Accrual "0 / 12", Discovery "1 / 1 discovery (exploratory)". `referee-shortlist-select-S-1` now reads "Registered" and carries the `disabled` attribute.

### UT-07 — Discovery vs. accrual counts render distinctly on a registered hypothesis
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-8-evidence/UT-07-result.png`
- On the S-1 row registered in UT-06: Accrual cell = "0 / 12" (zero post-boundary sessions so far, target 12). `referee-discovery-S-1` cell = "1 / 1 discovery (exploratory)", markup `<td class="... text-right text-slate-500"><span class="font-mono text-slate-400">1 / 1</span> <span class="italic">discovery (exploratory)</span></td>` — a separate `<td>` from the Accrual column, plain italic text, no colored-badge classes (no `bg-*`/`rounded-full`/pill styling).

### UT-08 — Already-registered candidate cannot be re-selected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-8-evidence/UT-08-result.png`
- Reloaded `http://localhost:3301/desk`, re-expanded Referee Registry. `referee-shortlist-select-S-1` outerHTML carried `disabled=""` and text "Registered". Clicking it (attempted anyway) produced no `referee-registration-confirm-panel` in the DOM — no effect.

### UT-09 — Stale-tab duplicate registration attempt surfaces the backend's refusal inline
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-8-evidence/UT-09-result.png`
- Tab A: selected S-2, left its confirm panel open (did not confirm). Tab B (new tab, same URL, Referee Registry re-expanded): selected S-2, clicked Confirm Registration — succeeded; `referee-hypotheses-row-S-2` appeared in Tab B with origin "historical-exploration". Switched back to Tab A (stale — its shortlist and hypotheses views never re-fetched) and clicked "Confirm Registration" on the still-open S-2 panel. Result: `referee-registration-error` rendered inside the panel with text "a hypothesis record with id 'S-2' is already recorded -- hypothesis records are immutable and are never re-recorded" (the backend's own explanation, not a generic client message), styled with `text-red-300` (red). The panel, the shortlist table, and the rest of the Referee Registry section remained intact — no crash, no blank-out.

### UT-10 — "Playbook Evidence" and prior /desk sections are unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-8-evidence/UT-10-result.png`
- Reloaded `/desk`, clicked "Playbook Evidence" header. It expanded to its full, pre-existing content: the signature/basis block, the complete setup×side×measure evidence table (real recorded data, e.g. `open_high_break long 5m` rows with real median/p25/p75/mean figures), the "BY LOCATION RELATIVE TO THE TRADABLE BAND MAP" block, and the "INVALIDATION BREACHES" table — all rendering exactly as their own established shape, no missing data, no broken layout. Section-testid enumeration confirmed order `desk-section-expand-topupRuns, -indexReconciliation, -screenRuns, -playbookEvidence, -refereeRegistry` — every pre-existing collapsible section still present, positioned above the new Referee Registry section as the surface map specifies. No console errors during this pass.

### UT-11 — Referee Registry section is discoverable without prior knowledge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-referee-iter-8-evidence/UT-11-result.png`
- Fresh navigation to `/desk`. Top nav bar carries exactly "Cockpit", "Structure", "Desk" — no dedicated Referee nav item, no hidden menu (confirmed earlier via UT-01's DOM check, re-verified visually in this test's screenshot). The Referee Registry header is the last section on the page (one scroll away) and expands with the single click already exercised in UT-02/UT-08. Its intro text — "Spec-pinned starter-family candidates (docs/referee-statistical-spec.md §7) beside their live sample-size readiness. Registering one writes a permanent, boundary-stamped hypothesis — historical observations before that boundary are discovery, never confirmation." — renders directly above the shortlist table, in plain language, before any table needs to be read (captured verbatim during UT-02's page-text extraction).

---

## Failed Tests

None.

---

## Skipped Tests

None. The QA backend was confirmed to be the fixture-scoped rig before any write-path test ran, so UT-06 through UT-09 were exercised normally rather than skipped.

---

## Notes on evidence capture

This headless Chrome session exhibited intermittent screenshot-capture flakiness unrelated to
the application under test: a `screenshot` call taken shortly after a DOM-mutating click
occasionally returned a blank (all-background) image, and one `fullpage: true` capture produced
a visibly duplicated/stitched image. In every such case a `document.body.scrollHeight` /
`data-testid` count check confirmed the live DOM had exactly one copy of the content (no real
double-render), and a retry (or switching between `fullpage: true` and plain viewport capture)
produced a clean image. All PASS verdicts above are grounded first in direct DOM assertions
(`eval`/`extract` reading `data-testid` attributes, `textContent`, `disabled`, and CSS classes)
captured at the time of each action, with the saved screenshot as corroborating, not sole,
evidence — consistent with the skill's guidance to verify element/text state directly rather
than relying on pixels alone. No test's PASS verdict rests only on a screenshot that could not
also be confirmed via a DOM read.

## Golden replay script

Wrote `runs/goal-session-referee/journey-scripts/J-07.json` (schema_version 1, 4 steps:
navigate → expand section → select S-1 → confirm registration, asserting "discovery
(exploratory)" on the final step). Linted clean via
`python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
runs/goal-session-referee/journey-scripts --journeys J-07` → "J-07 ok". Note for future replay:
this script's step 3 assumes candidate S-1 is still unregistered at replay time; since UT-06 of
this same run performed a real, permanent registration of S-1 against the fixture rig, a replay
against a fixture rig that has NOT been reseeded since this run will find S-1 already
"Registered" and the script will correctly fail fast at step 3 rather than silently pass on a
stale assumption — in that case J-07 falls back to a live browser-qa pass next time, per the
documented best-effort contract.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (confirmed scoped fixture rig via `assert_scoped_qa_backend.py`, exit 0, `source_url='fixture-rig-iter8-replay'`)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned CDP profile/port per environment (pump-launched headless Chrome on 127.0.0.1:9222)
- **Test Date:** 2026-08-15
- **Evidence directory:** `reports/qa/goal-referee-iter-8-evidence/`
