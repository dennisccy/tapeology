# Phase goal-i_will_be_super_rich-iter-8 — UI Test Results

**Phase:** goal-i_will_be_super_rich-iter-8
**Date:** 2026-06-05
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/18 tests passed (18 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Home page loads in Historical mode without errors | smoke | P1 | Page renders without errors, Historical mode controls visible | Frontend not running | SKIP | none |
| UT-02 | Timezone label appears immediately on entering Historical mode | smoke | P1 | Timezone label shows IANA timezone name | Frontend not running | SKIP | none |
| UT-03 | Quick-pick buttons are visible in Historical mode without a date | smoke | P1 | Three quick-pick buttons visible and disabled when no date entered | Frontend not running | SKIP | none |
| UT-04 | Quick-pick buttons activate and show local annotations when a date is entered | happy-path | P1 | Buttons activate with local-time annotations | Frontend not running | SKIP | none |
| UT-05 | "Open 9:30 ET" quick-pick fills start and end time inputs | happy-path | P1 | Start/end inputs populated with local equivalent of 9:30 ET | Frontend not running | SKIP | none |
| UT-06 | "Close 16:00 ET" quick-pick fills start and end time inputs | happy-path | P1 | Start/end inputs populated with local equivalent of 16:00 ET | Frontend not running | SKIP | none |
| UT-07 | "Full RTH 9:30–16:00 ET" quick-pick fills the complete RTH window | happy-path | P1 | Start/end inputs span full RTH window in local time | Frontend not running | SKIP | none |
| UT-08 | Historical Watch POST body contains tz-aware UTC instants | happy-path | P1 | POST body `start`/`end` are ISO-8601 strings with Z or offset | Frontend not running | SKIP | none |
| UT-09 | Manual time entry after quick-pick overrides the quick-pick in the POST body | validation | P2 | POST body reflects manually entered time, not quick-pick | Frontend not running | SKIP | none |
| UT-10 | Quick-pick buttons are no-op when date field is empty | validation | P2 | Click does nothing; cursor shows not-allowed | Frontend not running | SKIP | none |
| UT-11 | End time earlier than start time is rejected | validation | P2 | Validation error shown; no data rendered | Frontend not running | SKIP | none |
| UT-12 | Real-historical Ford chart renders with populated candlesticks | happy-path | P1 | Candlestick bars rendered from Ford fixture | Frontend not running | SKIP | none |
| UT-13 | Bar-size selector re-renders the real-historical chart at 10s, 30s, 60s | happy-path | P1 | Chart re-renders at each bar size without crash | Frontend not running | SKIP | none |
| UT-14 | Empty historical window shows no fabricated data | error | P2 | No candlestick bars; explicit no-data message | Frontend not running | SKIP | none |
| UT-15 | Simulated mode still renders chart after Historical picker changes | regression | P1 | Chart renders for SIM-BUYER scenario | Frontend not running | SKIP | none |
| UT-16 | Pause and resume still work after this iteration's changes | regression | P1 | Cockpit freezes on Pause; resumes updating on Resume | Frontend not running | SKIP | none |
| UT-17 | Historical mode controls are discoverable within 2 clicks from home | ux | P2 | All Historical controls visible after one click | Frontend not running | SKIP | none |
| UT-18 | Timezone label is correct for the browser's local timezone | ux | P2 | Label matches system IANA timezone exactly | Frontend not running | SKIP | none |

---

## Passed Tests

None.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-01 — Home page loads in Historical mode without errors
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-02 — Timezone label appears immediately on entering Historical mode
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-03 — Quick-pick buttons are visible in Historical mode without a date
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-04 — Quick-pick buttons activate and show local annotations when a date is entered
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-05 — "Open 9:30 ET" quick-pick fills start and end time inputs
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-06 — "Close 16:00 ET" quick-pick fills start and end time inputs
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-07 — "Full RTH 9:30–16:00 ET" quick-pick fills the complete RTH window
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-08 — Historical Watch POST body contains tz-aware UTC instants
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-09 — Manual time entry after quick-pick overrides the quick-pick in the POST body
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-10 — Quick-pick buttons are no-op when date field is empty
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-11 — End time earlier than start time is rejected
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-12 — Real-historical Ford chart renders with populated candlesticks
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-13 — Bar-size selector re-renders the real-historical chart at 10s, 30s, 60s
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-14 — Empty historical window shows no fabricated data
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-15 — Simulated mode still renders chart after Historical picker changes
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-16 — Pause and resume still work after this iteration's changes
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-17 — Historical mode controls are discoverable within 2 clicks from home
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-18 — Timezone label is correct for the browser's local timezone
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Browser:** Chrome via MCP (not used — frontend unavailable)
- **Test Date:** 2026-06-05
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-8-evidence/`
