# Phase goal-rapid-microscope-iter-17 — UI Test Results

**Phase:** goal-rapid-microscope-iter-17
**Date:** 2026-08-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 12/12 tests passed (0 skipped)

Note: J-01, J-04, J-05, J-08 were already re-verified this run via deterministic golden-script
replay (per the dispatch instructions) and are NOT re-tested or re-rowed here — their rows merge
into the results automatically after this run. This report covers the 11 UT-XX test-plan cases
plus the one additional regression journey assigned this run, J-07 (row `UT-J-07`).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads, zero console errors | smoke | P1 | Page renders, "Desk" heading visible, all section headers collapsed with "▸", zero red console errors | Navigated to `/desk`; heading "Desk" visible; all 8 sections (Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault) rendered collapsed with "▸"; console showed only the benign React DevTools info line, zero red errors | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-01-result.png` |
| UT-02 | Cockpit live tape + chart | regression | P1 | Chart renders, live tape updates for SIM-BUYER, no error banner | Typed `SIM-BUYER`, clicked Watch; tape state "Buyer Control" (confidence 0.877), live quote/spread, 15 recent trades, features panel, observations, and event log all rendered and updating; no error banner; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-02-result.png` |
| UT-03 | `/structure` load + Tradable Map | regression | P1 | No error banner; Tradable Map table renders bands or honest empty state; comparison dataset select present | Typed AAPL, filled As-of via "Today" button (2026-08-20 19:59:59), clicked Load; Tradable Map rendered 5 resistance + 5 support Class-A bands with range/score/members; `comparison-dataset-select` present with 2 dataset options; no error banner; console showed only benign Fast Refresh / DevTools lines | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-03-result.png` |
| UT-04 | Microscope Readiness renders | regression | P1 | Section expands (▸→▾), shows Corpus Totals table without throwing, zero new console errors | Clicked `desk-section-expand-microReadiness`; expanded to show Corpus Totals (1 symbol-day, 2 datasets, 1.75 RTH min), Sealed Tranche (0 sealed, honest zero state), Legacy Tick Shards (2 real rows), Pilot-Study Floors (3 studies, all `floor_unmet`); no throw; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-04-result.png` |
| UT-05 | Scout Ledger renders | regression | P1 | Section expands showing Run Screen button + empty-state or real rows; Run History shows empty or real rows; zero new console errors; Run Screen NOT clicked | Clicked `desk-section-expand-scoutLedger`; expanded showing "Ledger chain verification: ok", "No candidates ledgered.", "No scout runs recorded yet."; Run Screen button visible, not clicked; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-05-result.png` |
| UT-06 | Walk-Forward renders (either state acceptable) | regression | P1 | Section expands showing honest empty state or real fold spec/sequence; no client error/blank panel; zero new console errors; Run Walk-Forward NOT clicked | Clicked `desk-section-expand-walkForward`; expanded showing "Ledger chain verification: ok", "No fold specs registered.", "No walk-forward sequences run.", "No walk-forward runs recorded yet." (honest empty state, one of the two documented-acceptable outcomes); Run Walk-Forward button visible, not clicked; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-06-result.png` |
| UT-07 | Validation Vault renders, still read-only | regression | P1 | Section expands showing honest empty state or real rows; no compute/seal/assign/expose control present; zero new console errors | Clicked `desk-section-expand-validationVault`; expanded showing "Shard ledger chain verification: ok", "Universe ledger chain verification: ok", "No shards recorded.", "No universes registered."; full DOM dump confirmed no compute/seal/assign/expose control anywhere in the section; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-07-result.png` |
| UT-08 | All three Referee sections render | regression | P1 | Each of the three sections expands with its own table/content, no client error, zero new console errors | Clicked all three expand buttons (`refereeRegistry`, `refereeAdjudications`, `refereeRuns`); Registry showed 6 spec-pinned candidates (S-1..S-6) with N/sessions/accrual columns + "No hypotheses registered."; Adjudications showed "No hypotheses registered."; Runs showed Null Builds + Evaluations both honest-empty; no client error; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-08-result.png` |
| UT-09 | Graduation endpoint serves honest empty state | smoke | P1 | HTTP 200, raw parseable JSON, honest empty-state body `{"families": [], "message": "No candidates ledgered.", ...}`, no 500/stack-trace | Navigated directly to `http://localhost:8301/research/desk/micro/graduation`; body was exactly `{"families":[],"message":"No candidates ledgered.","chain_verification":{"ok":true,"failed_at_row":null,"reason":null}}`; cross-checked with `curl -s -o /dev/null -w "%{http_code}"` → `200`; valid JSON, no error page | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-09-result.png` |
| UT-10 | Nav bar unaffected | regression | P2 | Exactly 3 links: Cockpit, Structure, Desk | `document.querySelectorAll('[data-testid="nav-link"]')` on `/` returned exactly `["Cockpit","Structure","Desk"]` | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-10-result.png` |
| UT-11 | New sealed-verdict data stays invisible (by design) | ux | P3 | Zero matches for "sealed_evaluation", "SEALED_PASS_RULE", "confirmation_boundary" on rendered `/desk` page after all sections from UT-01–UT-08 expanded | With Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault, and all 3 Referee sections expanded, `document.body.innerText.includes(...)` returned `false` for all three strings | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-11-result.png` |
| UT-J-07 | J-07: Graduation — provenance in, nothing laundered out (goal-mode regression journey) | regression | P1 | Per the goal slice's J-07 acceptance and this round's own UI test plan/surface map notes: the only browser-observable evidence of `micro_sealed_evaluation.py` + `micro_graduation.py` being live and serving correctly is direct navigation to `GET /research/desk/micro/graduation` (no `/desk` section or MCP tool reads this endpoint) — same check as UT-09 | Same navigation/result as UT-09: HTTP 200, body `{"families":[],"message":"No candidates ledgered.","chain_verification":{"ok":true,"failed_at_row":null,"reason":null}}` — honest empty state, valid JSON, no error page. (Fixture-level pipeline behavior for J-07's `exploratory → walkforward_survivor → sealed_survivor → referee_handoff_ready` walk and refusal semantics is backend-only and out of browser-QA scope; this is J-07's own documented "no golden script, browser-observable-payload-only" check, unchanged since iteration 15) | PASS | `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-J-07-result.png` |

---

## Passed Tests

### UT-01 — `/desk` loads, zero console errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-01-result.png`
- "Desk" heading visible; all 8 sections rendered collapsed with "▸"; console showed only the benign React DevTools info line.

### UT-02 — Cockpit live tape + chart
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-02-result.png`
- Watched SIM-BUYER; tape state "Buyer Control" with live quote, trades, features, observations, event log all rendering; no error banner; console clean.

### UT-03 — `/structure` load + Tradable Map
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-03-result.png`
- Loaded AAPL as-of 2026-08-20 19:59:59; Tradable Map rendered 10 real Class-A bands; comparison dataset select present with 2 datasets; console clean.

### UT-04 — Microscope Readiness renders
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-04-result.png`
- Corpus Totals, Sealed Tranche, Legacy Tick Shards, and Pilot-Study Floors all rendered without throwing; console clean.

### UT-05 — Scout Ledger renders
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-05-result.png`
- Honest empty state ("No candidates ledgered.", "No scout runs recorded yet."); Run Screen not clicked; console clean.

### UT-06 — Walk-Forward renders
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-06-result.png`
- Honest empty state ("No fold specs registered.", "No walk-forward sequences run."); Run Walk-Forward not clicked; console clean.

### UT-07 — Validation Vault renders, still read-only
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-07-result.png`
- Honest empty state ("No shards recorded.", "No universes registered."); confirmed no compute/seal/assign/expose control present anywhere in the section; console clean.

### UT-08 — All three Referee sections render
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-08-result.png`
- Referee Registry (6 spec-pinned candidates), Referee Adjudications (honest empty), Referee Runs (Null Builds + Evaluations honest empty) all rendered without a client error; console clean.

### UT-09 — Graduation endpoint serves honest empty state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-09-result.png`
- Direct navigation to `http://localhost:8301/research/desk/micro/graduation` returned HTTP 200 with body `{"families":[],"message":"No candidates ledgered.","chain_verification":{"ok":true,"failed_at_row":null,"reason":null}}`, matching the exact expected honest-empty-state wording. Cross-checked with curl (HTTP 200, identical body).

### UT-10 — Nav bar unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-10-result.png`
- Exactly 3 nav links: Cockpit, Structure, Desk.

### UT-11 — New sealed-verdict data stays invisible (by design)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-11-result.png`
- Zero matches for "sealed_evaluation", "SEALED_PASS_RULE", "confirmation_boundary" on the rendered `/desk` page with all relevant sections expanded — confirms this round's new tri-state verdict/lineage-boundary derivation is served (UT-09) but by design not surfaced in the UI yet.

### UT-J-07 — J-07: Graduation — provenance in, nothing laundered out
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-17-evidence/UT-J-07-result.png`
- Same direct-endpoint check as UT-09 (J-07's own documented "no golden script, browser-observable-payload-only" check — no `/desk` section or MCP tool reads `GET /research/desk/micro/graduation`): HTTP 200, honest empty-state JSON, valid, no stack trace. No golden replay script written for this journey — it is by design a direct-backend-navigation check that falls back to the LLM lane each run (confirmed in the plan's own notes, "carried unchanged since iteration 15").

---

## Failed Tests

None.

---

## Skipped Tests

None. Frontend and backend were both running and Chrome MCP (CDP on 127.0.0.1:9222) was available for the full run.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome/151.0.7922.71 (headless) via MCP, CDP port 9222 (pre-existing pinned instance, not launched by this agent)
- **Test Date:** 2026-08-20
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-17-evidence/`
