# Goal Session i_will_be_super_rich_with_my_loved_ones — Iteration 19 UI Test Results

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-19
**Date:** 2026-06-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass. UT-J-61-b previously FAIL (silent disable, no error shown) — fix shipped in iter-19 and re-verified live on 2026-06-12: level_break + blank level now fires POST and renders backend 422 inline. -->

**Overall:** 12/12 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-68-a | Cockpit unchanged — no thesis idle state | smoke | P1 | Cockpit loads at /, buyer_control form present, no thesis state unchanged | Cockpit loads, idle form visible, no thesis state unaffected | PASS | UT-J-68-cockpit-initial.png |
| UT-J-68-b | Studies nav entry enabled | smoke | P1 | Nav bar has Studies link clickable | Nav shows Cockpit/Journal/Studies all clickable | PASS | UT-J-68-cockpit-sim-buyer.png |
| UT-J-68-c | Nav round-trip: Cockpit → Studies → Journal → Cockpit | happy-path | P1 | All three nav links navigate correctly | All three pages reachable via nav | PASS | UT-J-68-journal-reachability.png |
| UT-J-60-a | Create study — queued→running progress | happy-path | P1 | Study transitions QUEUED→RUNNING with events-processed counter | Study showed RUNNING with "14000 events processed" progress | PASS | UT-J-60-study-running-progress.png |
| UT-J-60-b | Study results — n/occurrence rows, null baseline side-by-side | happy-path | P1 | trend_continuation n=2 rows, r_basis=[0.3,0.6], verdicts=[invalidated,confirming], null n=99, feed+fingerprint visible | n=2 confirmed, r_basis [0.3, 0.6], verdicts [invalidated, confirming], null n=99, feed=sip_pg_fixture, fingerprint=69f5231b0c7f6006, seed=1729 | PASS | UT-J-60-trend-continuation-results.png |
| UT-J-60-c | Re-run identical — same results byte-equal | happy-path | P1 | Re-run of same config produces identical n, r_basis, verdicts, fingerprint | Two runs (IDs 3177434f and 4b1e33c1) confirmed byte-identical results via REST | PASS | UT-J-60-rerun-running.png |
| UT-J-60-d | SIM-REVERSAL study — n=1, +1R at 60s and 120s, null n=100 | happy-path | P1 | SIM-REVERSAL absorption_reversal n=1, +1R at 60s and 120s horizons, null baseline n=100 | n=1 confirmed, +1R at both 60s and 120s horizons, null n=100 | PASS | UT-J-60-sim-reversal-study-results.png |
| UT-J-61-a | hindsight_level label on level setup | happy-path | P1 | level_break setup type shows hindsight_level label and exclusion note | hindsight_level label visible, "occurrences where the level was not yet known" exclusion note present | PASS | UT-J-61-level-break-hindsight-label.png |
| UT-J-61-b | Level-without-level 422 inline error | validation | P1 | Submitting level_break study with empty level field shows inline 422 error | Fix verified live (iter-19): Run button fires POST; backend 422 renders inline rose error "setup_type 'level_break' requires a level_price (a level is never guessed)". Prior FAIL (silent disable) corrected. | PASS | UT-J-61-b-level-break-blank-level-422-error.png |
| UT-J-61-c | Cancelled study shows PARTIAL warning | happy-path | P1 | Cancelled study results show PARTIAL banner | PARTIAL WARNING banner visible in cancelled study results | PASS | UT-J-61-cancelled-partial-results.png |
| UT-J-61-d | Failed study shows explicit error message | happy-path | P1 | Failed study results page shows explicit error message (not generic) | Explicit error message visible: "Error: ValueError: Unexpected symbol format: AAPL_2026-06-12" | PASS | UT-J-61-failed-study-explicit-error.png |
| UT-J-61-e | Multi-status badges visible in job list | happy-path | P1 | Job list shows DONE, CANCELLED, FAILED status badges | DONE (green), CANCELLED (gray), FAILED (red) status badges all visible | PASS | UT-J-61-multi-status-badges-list.png |

---

## Passed Tests

### UT-J-68-a — Cockpit unchanged — no thesis idle state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-68-cockpit-initial.png`
- Cockpit loads at http://localhost:3650/. Idle state confirmed: buyer_control form present, no active tape session. Studies iteration did not regress the cockpit idle state.

### UT-J-68-b — Studies nav entry enabled
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-68-cockpit-sim-buyer.png`
- Nav bar shows three links: Cockpit, Journal, Studies. All are clickable. Studies link navigates to /studies.

### UT-J-68-c — Nav round-trip: Cockpit → Studies → Journal → Cockpit
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-68-journal-reachability.png`
- Navigated Cockpit → Studies → Journal: journal page loaded with tape rows. Round-trip back to Cockpit confirmed.

### UT-J-60-a — Create study — queued→running progress
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-60-study-running-progress.png`
- New absorption_reversal study transitioned from QUEUED to RUNNING. Progress indicator showed "14000 events processed" in the running state before completing.

### UT-J-60-b — Study results — n/occurrence rows, null baseline side-by-side
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-60-trend-continuation-results.png`
- Reference trend_continuation study (PG SIP fixture) results confirmed:
  - n=2
  - r_basis=[0.3, 0.6]
  - verdicts=[invalidated, confirming]
  - Null baseline: n=99
  - feed=sip_pg_fixture, config_fingerprint=69f5231b0c7f6006, seed=1729
  - Both study and null baseline columns visible side-by-side in results table

### UT-J-60-c — Re-run identical — same results byte-equal
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-60-rerun-running.png`
- Re-run identical button triggered for trend_continuation study. REST cross-check of two completed runs (study IDs 3177434f and 4b1e33c1) confirmed identical results: same n, r_basis, verdicts, fingerprint, and all occurrence-level data.

### UT-J-60-d — SIM-REVERSAL study — n=1, +1R at 60s and 120s, null n=100
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-60-sim-reversal-study-results.png`
- SIM-REVERSAL absorption_reversal study results confirmed:
  - n=1
  - +1R outcome at both 60s and 120s horizons
  - Null baseline: n=100
  - Matches spec exactly

### UT-J-61-a — hindsight_level label on level setup
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-61-level-break-hindsight-label.png`
- level_break setup type selected in study form. Results page shows "hindsight_level" label and accompanying exclusion note: occurrences where the level was not yet known at event time are excluded from count.

### UT-J-61-b — Level-without-level 422 inline error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-61-b-level-break-blank-level-422-error.png`
- This is the critical fix verified live in this iteration. level_break selected, level field left blank, "Run study" clicked. POST fired to backend; backend returned HTTP 422; inline rose error banner rendered: "setup_type 'level_break' requires a level_price (a level is never guessed)". No silent no-op, no disabled button with no feedback. The banner is clearly visible in the screenshot with the amber hindsight notice above it and the rose error below.

### UT-J-61-c — Cancelled study shows PARTIAL warning
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-61-cancelled-partial-results.png`
- Selected a cancelled study from the job list. Results page showed "PARTIAL" warning banner indicating the study was interrupted and results are incomplete.

### UT-J-61-d — Failed study shows explicit error message
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-61-failed-study-explicit-error.png`
- Created a study with invalid symbol AAPL_2026-06-12 via REST API. Failed study results page showed explicit error message: "Error: ValueError: Unexpected symbol format: AAPL_2026-06-12". Not a generic error — the specific exception text is surfaced.

### UT-J-61-e — Multi-status badges visible in job list
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-61-multi-status-badges-list.png`
- Studies job list shows all three status badge variants: DONE (green), CANCELLED (gray), FAILED (red). Badges are visually distinct and correctly applied per study state.

---

## Failed Tests

None.

---

## Previously-Failed Test — Now Passing (iter-19 fix)

### UT-J-61-b — Level-without-level 422 inline error
**Prior verdict (iter-19 first run):** FAIL — UI silently disabled the Run button when level_break was selected with a blank level; no POST was fired, no error shown.
**Current verdict:** PASS — Fix applied in iter-19 (StudyCreateForm.tsx: removed silent disable for empty-level/level_break case). Re-verified live on 2026-06-12:
1. Navigated to /studies
2. Selected "Level break-and-go" (level_break) from setup dropdown
3. Left the level price field blank
4. Clicked "Run study"
5. POST fired; backend returned 422; inline rose error banner rendered: "setup_type 'level_break' requires a level_price (a level is never guessed)"

**Evidence:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/UT-J-61-b-level-break-blank-level-422-error.png`

---

## Skipped Tests

None.

---

## Regression Spot-Checks (Required-Still-Passing)

These were spot-checked during the same browser session per the iteration spec:

| Journey | Check | Result |
|---------|-------|--------|
| J-01 (Watch ticker) | SIM-BUYER Watch → buyer_control visible in UI | PASS |
| J-08 (REST state) | GET /tape/SIM-BUYER/state → `{"scenario":"buyer_control","confidence":0.95,"warm":true}` | PASS |
| J-09 (Stop watching) | Stop button clicked → UI returns to idle (Watch button reappears), REST returns "not being watched" | PASS |
| J-17/J-19 (Journal reachability) | Journal page loads with tape rows | PASS |

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Backend URL:** http://localhost:8650
- **Browser:** Chrome via MCP (tab_index=1, Tapeology tab)
- **Test Date:** 2026-06-12 (initial run: FAIL on J-61-b; re-run after iter-19 fix: all 12 PASS)
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich_with_my_loved_ones-iter-19-evidence/`
- **New evidence from re-run:** `UT-J-61-b-level-break-blank-level-422-error.png`, `UT-J-68-cockpit-no-thesis-idle-fresh.png`, `UT-J-68-nav-roundtrip-back-to-cockpit.png`
