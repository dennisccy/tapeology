# Phase goal-rapid-microscope-iter-6 — UI Test Results

**Phase:** goal-rapid-microscope-iter-6
**Date:** 2026-08-17
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: UT-02 is a P1 regression test and it fails. Per ui-test-plan.md's own closing note: "P1 tests must all pass for browser QA verdict to be PASS." -->

**Overall:** 7/8 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | Heading "Playbook Signals" visible, no blank screen/error banner/console exception | Heading "Playbook Signals" rendered; all 10 collapsible sections present; no error banner; console showed only the benign React-DevTools notice | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-01-result.png` |
| UT-02 | Microscope Readiness shows real corpus data | regression | P1 | Corpus Totals: Distinct symbol-days=12, Distinct datasets=18; Legacy Tick Shards: exactly 18 rows, every row Split provenance=`hand_assigned`, Exposure state=`exploratory` | Corpus Totals: Distinct symbol-days=**1**, Distinct datasets=**2**; Legacy Tick Shards: **2** rows only (both symbol PG, session 2026-06-09); the 2 present rows DO show Split provenance=`hand_assigned` and Exposure state=`exploratory` | **FAIL** | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-02-fail.png` |
| UT-03 | Cockpit ticker watch still works | regression | P1 | "No ticker watched" before watch; "Buyer Control" after typing SIM-BUYER + clicking Watch | Both states observed exactly; tape state "Buyer Control", confidence 0.950, live quote/trades/features/observations all populated; no error toast | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-03-result.png` |
| UT-04 | `/structure` Tradable Map still loads | regression | P1 | "Tradable Map" on load; after AAPL + `2026-06-22 17:00:00` + Load, text "300.11–302.2" appears | "Tradable Map" visible on load; after Load, resistance band row `300.11–302.2 · Class A · score 171 · 849 members · round number` rendered exactly | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-04-result.png` |
| UT-05 | Playbook Evidence section still renders | regression | P1 | "Built from signature:" after expand; "recorded signals, none hidden" after typing date | Both strings found verbatim (record `playbook_2026_06_22_803fc798424e`, recorded at 2026-08-17 16:25:52 ET, session date 2026-06-22) | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-05-result.png` |
| UT-06 | Referee Registry shows frozen fingerprint | regression | P1 | Text "config fingerprint 08e471b10130e1e2" appears | Text found verbatim, matching TC-10's independent backend check | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-06-result.png` |
| UT-07 | Referee Adjudications/Runs honest-empty states | regression | P1 | "No hypotheses registered"; "No evaluation runs recorded yet." | Both empty-states found verbatim, no fabricated rows, no stuck spinner | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-07-result.png` |
| UT-08 | Microscope Readiness discoverable | ux | P2 | "Microscope Readiness" is the last section, directly below "Referee Runs", reachable by scroll alone | Confirmed: fresh `/desk` load section order ends `... ▸Referee Adjudications, ▸Referee Runs, ▸Microscope Readiness`; human-readable label, no code name | PASS | `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-08-result.png` |

---

## Passed Tests

### UT-01 — `/desk` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-01-result.png`
- Navigated to `/desk`; the "Playbook Signals" heading and all ten collapsible section headers (Top-up Runs, Index Reconciliation, Screen Runs, Playbook Signals, Backscan, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness) rendered with no blank screen and no error banner. Console logging enabled immediately after; polled across the whole session and the only message ever seen was the benign "Download the React DevTools…" info line — zero JS exceptions.

### UT-03 — Cockpit ticker watch still works
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-03-result.png`
- `/` showed "No ticker watched" before any ticker was set. Typed `SIM-BUYER` into the field with `aria-label="Ticker"`, clicked the "Watch" button (saw the transient "Connecting to SIM-BUYER…" state), then `await_text` resolved "Buyer Control" within the timeout. Screenshot shows Tape State = Buyer Control (confidence 0.950), live Quote/Recent Trades/Features/Observations/Event Log all populated for the simulated feed. No error toast or blank panel.

### UT-04 — `/structure` Tradable Map still loads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-04-result.png`
- `/structure` showed the "Tradable Map" section on load. Typed `AAPL` into `aria-label="Structure symbol"`, typed `2026-06-22 17:00:00` into `data-testid="structure-as-of-input"`, clicked `data-testid="structure-load-button"`. The resistance row `300.11–302.2 · Class A · score 171 · 849 members` rendered with the "round number" flag — byte-identical to the pinned example this iteration's Anti-goals require to stay frozen. No error message replaced the band.

### UT-05 — Playbook Evidence section still renders
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-05-result.png`
- On `/desk`, expanded `data-testid="desk-section-expand-playbookEvidence"`; "Built from signature:" appeared (record `playbook_2026_06_22_803fc798424e`, recorded at 2026-08-17 16:25:52 ET). Typed `2026-06-22` into `data-testid="desk-playbook-date-input"`; "recorded signals, none hidden" appeared, confirming the date filter still serves the full unfiltered signal set.

### UT-06 — Referee Registry shows frozen fingerprint
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-06-result.png`
- Expanded `data-testid="desk-section-expand-refereeRegistry"`; text "config fingerprint 08e471b10130e1e2" appeared verbatim — the same value this iteration's own TC-10 independently re-checks via `Config().config_fingerprint()` in the backend suite. No drift in the frozen foundation.

### UT-07 — Referee Adjudications/Runs honest-empty states
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-07-result.png`
- Expanded `data-testid="desk-section-expand-refereeAdjudications"` → "No hypotheses registered". Expanded `data-testid="desk-section-expand-refereeRuns"` → "No evaluation runs recorded yet." Both honest-empty states rendered exactly, no fabricated row and no stuck spinner.

### UT-08 — Microscope Readiness discoverable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-08-result.png`
- Fresh navigation to `/desk` (all sections collapsed by default). Scrolling down (no Ctrl+F) reaches the section order: … ▸Playbook Evidence, ▸Referee Registry, ▸Referee Adjudications, ▸Referee Runs, ▸Microscope Readiness — the last section on the page, human-readable label, no internal code name.

---

## Failed Tests

### UT-02 — Microscope Readiness shows real, non-fabricated corpus data (regression — J-01)
**Verdict:** FAIL
**Failure:** The Corpus Totals table reads "Distinct symbol-days" = **1** and "Distinct datasets" = **2** (expected 12 and 18). The Legacy Tick Shards table renders exactly **2** data rows, not 18 — both rows are the same symbol (PG) and the same session date (2026-06-09), not 12 distinct symbol-days.
**Evidence:** `reports/qa/goal-rapid-microscope-iter-6-evidence/UT-02-fail.png` (full-page capture with Microscope Readiness expanded)

**Steps taken:**
1. Navigated to `http://localhost:3301/desk` (UT-01 state reused).
2. Clicked `data-testid="desk-section-expand-microReadiness"`.
3. Read `data-testid="micro-readiness-totals-table"` and `data-testid="micro-readiness-shards-table"` via DOM `innerText` (bounding-rect confirmed both tables are genuinely rendered and populated, not empty/loading).
4. Cross-checked against `curl http://localhost:8301/research/desk/micro/readiness` directly — the JSON response is **byte-consistent with the UI** (`totals.distinct_symbol_days: 1, totals.distinct_datasets: 2`, `shards` array has exactly 2 entries, both `symbol: "PG"`, `session_date: "2026-06-09"`). This is not a frontend rendering defect — the UI is faithfully rendering exactly what its canonical endpoint serves; the backend this QA rig is pointed at (`:8301`) is itself serving a materially smaller tick corpus than expected.

**Expected:** Corpus Totals shows 12 distinct symbol-days / 18 distinct datasets; Legacy Tick Shards renders 18 rows, each with non-empty Symbol/Session date/Checksum/Coverage gaps/Fallback frac, every row's Split provenance = `hand_assigned`, every row's Exposure state = `exploratory`.

**Actual:** Corpus Totals shows 1 distinct symbol-day / 2 distinct datasets. Legacy Tick Shards renders 2 rows only (PG / 2026-06-09 x2). The 2 rows present DO individually satisfy the per-row shape checks — non-empty Symbol/Session date/Checksum/Coverage gaps/Fallback frac, Split provenance = `hand_assigned`, Exposure state = `exploratory` on both — so TC-7's specific concern (this iteration's exposure-registry seeding fix leaking `historical_oos`/`hand_assigned` into the readiness-served `exposure_state`) is NOT observed; the failure is purely the corpus being far smaller than specified, not a conflation of the two mechanisms.

**Context for triage (observation, not diagnosis):** `runs/goal-session-rapid-microscope/state/journey-history.json`'s J-01 entry records the iteration-5 evaluator calling `micro_routes.get_micro_readiness()` directly against "the operator's real `.data/datasets` + playbook stores" and getting `{distinct_symbol_days: 12, distinct_datasets: 18, rth_minutes_covered: 1173.49, session_equivalents: 3.0089}` with 18 shards, all `exploratory`/`hand_assigned`, all three `study_floors` `floor_unmet` at `11/60`. The `:8301` QA-rig backend I tested against right now returns `rth_minutes_covered: 1.75`, `session_equivalents: 0.0045`, and `study_floors` availability `1/60` — a much smaller corpus than the 12/18 figure already established against the real store two iterations ago, and smaller than what this iteration's own UI test plan and DEFINITION OF DONE (TC-8) assume the store-scoped rig would serve. Whether this is a QA-rig dataset-seeding gap (this specific `:8301` process instance pointed at a thinner fixture than intended) or a genuine backend regression is outside what browser QA can distinguish — flagging the exact discrepancy (with both endpoints' raw figures above) for dev/auditor root-cause.

**Note on the deterministic-replay lane:** the dispatch noted J-01 was "already re-verified" this iteration via `journey-scripts/J-01.json` replay. That script's step 2 only asserts the substring `hand_assigned` is present on the page — which it is (both of the 2 real rows carry that value) — so the shallow replay assertion cannot see the count mismatch this deeper test-plan check (UT-02) surfaces. Per the dispatch instructions, this row supersedes the replay's for J-01. I did not overwrite `journey-scripts/J-01.json` with a new golden (the golden-script instructions only ask for one on a verified PASS); the existing shallow script is left as-is.

---

## Skipped Tests

None. Frontend (`http://localhost:3301`) and backend (`http://localhost:8301/health` → `{"status":"ok"}`) were both up before testing began, and Chrome MCP was available throughout (after self-recovering from one blank-viewport-screenshot quirk — see Notes).

---

## Notes

- **Screenshot capture quirk (tooling, not product):** in this headless session, a plain viewport screenshot (`fullpage: false`) taken while the page was scrolled away from the top (`scrollY > 0`) consistently returned a blank/uniform-navy image, even though `eval`-based `getBoundingClientRect()` checks proved the target content was genuinely rendered and on-screen at those coordinates. `fullpage: true` captures were reliable at any scroll position and were used for every screenshot taken after the first section-expand action (UT-02 onward). Two stray blank PNGs from an apparent earlier/interrupted attempt at this same iteration's browser pass (`UT-02-microscope-readiness`, `UT-02-microscope-readiness-final.png`, plus `J-01-verify.png` from the deterministic-replay lane) were found already present in the evidence directory before this run started; they were left in place untouched but are not this report's evidence — only the `UT-0X-result.png` / `UT-02-fail.png` files listed in the Results Table above were produced by this run.
- **Golden replay script:** `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` (13 steps, covering UT-03 through UT-07) was re-verified step-by-step this run and re-written byte-identical to what was actually exercised; linted clean via `demo_runner.py --mode lint`. `J-01.json` was intentionally NOT touched (see UT-02 above — the journey did not pass this run's deeper check).
- Every P1 regression test other than UT-02 reproduced its pinned/frozen value exactly (structure band `300.11–302.2`, config fingerprint `08e471b10130e1e2`, both Referee honest-empty strings) — i.e., this is a narrow, isolated finding scoped to the tick-corpus size served by the readiness endpoint on this QA rig, not a broad regression across the kept product surface.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (store-scoped rig)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile/CDP port
- **Test Date:** 2026-08-17
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-6-evidence/`
