# Phase goal-i_will_be_super_rich-iter-10 — UI Test Results

**Phase:** goal-i_will_be_super_rich-iter-10
**Date:** 2026-06-07
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/15 tests passed (15 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Home page loads without errors | smoke | P1 | Page renders with symbol input and Watch button | Frontend not running | SKIP | none |
| UT-02 | WaitingState renders when stream connects with no trade | happy-path | P1 | Waiting treatment screen visible with ticker and mode label | Frontend not running | SKIP | none |
| UT-03 | TopBar status dot shows amber "waiting" label | happy-path | P1 | Amber pulsing dot labelled "waiting" in TopBar | Frontend not running | SKIP | none |
| UT-04 | Snapshot-borne failed state renders StreamFailedState and error banner | happy-path | P1 | StreamFailedState component and error banner visible | Frontend not running | SKIP | none |
| UT-05 | TopBar status dot shows rose "failed" label for snapshot-borne failure | happy-path | P1 | Rose dot labelled "failed" in TopBar | Frontend not running | SKIP | none |
| UT-06 | Price chart is hidden during waiting state | happy-path | P1 | No price/tape chart visible during waiting state | Frontend not running | SKIP | none |
| UT-07 | Price chart is hidden during snapshot-borne failed state | error | P1 | No price/tape chart visible during failed state | Frontend not running | SKIP | none |
| UT-08 | Empty Watch shows inline validation | validation | P2 | Validation message or disabled Watch button | Frontend not running | SKIP | none |
| UT-09 | Whitespace-only ticker shows validation | validation | P2 | Validation message or no transition to connecting state | Frontend not running | SKIP | none |
| UT-10 | Idle screen leaves within ~1 second of clicking Watch | regression | P1 | Idle screen replaced within ~1 second | Frontend not running | SKIP | none |
| UT-11 | SIM-BUYER still resolves to full cockpit with buyer_control | regression | P1 | Full cockpit with buyer_control TapeState | Frontend not running | SKIP | none |
| UT-12 | Mode selector switches between modes without regression | regression | P1 | Mode selector works for Live, Historical, Simulated | Frontend not running | SKIP | none |
| UT-13 | Connecting state appears immediately after clicking Watch | regression | P1 | Connecting message appears within ~1 second | Frontend not running | SKIP | none |
| UT-14 | Waiting treatment screen is discoverable and labels are clear | ux | P2 | Ticker, mode, and waiting reason clearly visible | Frontend not running | SKIP | none |
| UT-15 | Snapshot-borne failed error banner is readable and actionable | ux | P2 | Error banner with clear failure message visible | Frontend not running | SKIP | none |

---

## Passed Tests

None.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-01 — Home page loads without errors
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-02 — WaitingState renders when stream connects with no trade
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-03 — TopBar status dot shows amber "waiting" label
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-04 — Snapshot-borne failed state renders StreamFailedState and error banner
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-05 — TopBar status dot shows rose "failed" label for snapshot-borne failure
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-06 — Price chart is hidden during waiting state
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-07 — Price chart is hidden during snapshot-borne failed state
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-08 — Empty Watch shows inline validation
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-09 — Whitespace-only ticker shows validation
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-10 — Idle screen leaves within ~1 second of clicking Watch
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-11 — SIM-BUYER still resolves to full cockpit with buyer_control
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-12 — Mode selector switches between modes without regression
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-13 — Connecting state appears immediately after clicking Watch
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-14 — Waiting treatment screen is discoverable and labels are clear
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

### UT-15 — Snapshot-borne failed error banner is readable and actionable
**Verdict:** SKIPPED
**Reason:** Frontend not running. HTTP check to http://localhost:3650 returned no response.

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Browser:** Chrome via MCP (not launched — frontend unavailable)
- **Test Date:** 2026-06-07
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-10-evidence/` (not created — no tests ran)
