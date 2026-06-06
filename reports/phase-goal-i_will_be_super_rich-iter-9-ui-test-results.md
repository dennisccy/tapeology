# Phase goal-i_will_be_super_rich-iter-9 — UI Test Results

**Phase:** goal-i_will_be_super_rich-iter-9
**Date:** 2026-06-06
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

**Overall:** 0/18 tests passed (18 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Main cockpit page loads without errors | smoke | P1 | Page renders with header, mode selector, symbol input, Watch button, idle cockpit | Frontend not running | SKIP | none |
| UT-02 | ConnectingState appears immediately on Watch click in Simulated mode | happy-path | P1 | Amber pulsing dot and "Connecting to SIM-BUYER…" appears within 1 second | Frontend not running | SKIP | none |
| UT-03 | ConnectingState appears immediately on Watch click in Live mode | happy-path | P1 | Amber pulsing dot and "Connecting to AAPL…" appears within 1 second | Frontend not running | SKIP | none |
| UT-04 | ConnectingState appears immediately on Watch click in Historical mode | happy-path | P1 | Amber pulsing dot and "Connecting to AAPL…" appears within 1 second | Frontend not running | SKIP | none |
| UT-05 | StreamFailedState panel appears when tape connection fails | happy-path | P1 | Error panel with rose warning icon, "Couldn't connect to the tape stream", "Try Watch again" | Frontend not running | SKIP | none |
| UT-06 | TopBar status dot shows "failed" state after stream connection failure | happy-path | P1 | Status dot shows rose color with "failed" label | Frontend not running | SKIP | none |
| UT-07 | TopBar error banner shows timeout message when backend is unreachable | error | P1 | Error banner with rose background shows "timed out" or "Couldn't connect" within 12 seconds | Frontend not running | SKIP | none |
| UT-08 | Watch button is disabled and shows inline message when symbol field is empty | validation | P1 | Watch button grayed out, amber "Enter a ticker symbol" message visible | Frontend not running | SKIP | none |
| UT-09 | Inline validation message appears with whitespace-only input | validation | P1 | Watch button grayed out, amber "Enter a ticker symbol" message visible | Frontend not running | SKIP | none |
| UT-10 | Watch button is disabled when Historical time window is missing | validation | P1 | Watch button grayed out, amber "Choose a valid time window" message visible | Frontend not running | SKIP | none |
| UT-11 | Inline validation message clears immediately when user types a valid symbol | validation | P1 | Amber message disappears immediately upon typing "A", Watch button becomes active | Frontend not running | SKIP | none |
| UT-12 | Mode switch while connecting clears the ConnectingState | regression | P1 | Cockpit returns to idle state, "Connecting to SIM-BUYER…" no longer visible | Frontend not running | SKIP | none |
| UT-13 | Simulated cockpit populates successfully end-to-end | regression | P1 | Cockpit transitions from connecting to populated with tape rows and confidence score | Frontend not running | SKIP | none |
| UT-14 | Stop button returns cockpit to idle state | regression | P1 | Cockpit clears to idle state, tape rows gone, idle placeholder reappears | Frontend not running | SKIP | none |
| UT-15 | Mode switching updates TopBar controls correctly | regression | P1 | LIVE mode shows no date fields; HIST mode shows start/end date fields | Frontend not running | SKIP | none |
| UT-16 | ConnectingState is discoverable and labels are clear | ux | P2 | Symbol input and Watch button visible without scrolling; connecting text clearly labels symbol name | Frontend not running | SKIP | none |
| UT-17 | StreamFailedState panel is clear and actionable | ux | P2 | Panel heading and "Try Watch again" instruction clearly communicated | Frontend not running | SKIP | none |
| UT-18 | Inline validation messages are visible and positioned near the Watch button | ux | P2 | Amber message positioned close to Watch button, visually distinct | Frontend not running | SKIP | none |

---

## Passed Tests

None.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-01 — Main cockpit page loads without errors
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-02 — ConnectingState appears immediately on Watch click in Simulated mode
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-03 — ConnectingState appears immediately on Watch click in Live mode
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-04 — ConnectingState appears immediately on Watch click in Historical mode
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-05 — StreamFailedState panel appears when tape connection fails
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-06 — TopBar status dot shows "failed" state after stream connection failure
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-07 — TopBar error banner shows timeout message when backend is unreachable
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-08 — Watch button is disabled and shows inline message when symbol field is empty
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-09 — Inline validation message appears with whitespace-only input
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-10 — Watch button is disabled when Historical time window is missing
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-11 — Inline validation message clears immediately when user types a valid symbol
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-12 — Mode switch while connecting clears the ConnectingState
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-13 — Simulated cockpit populates successfully end-to-end
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-14 — Stop button returns cockpit to idle state
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-15 — Mode switching updates TopBar controls correctly
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-16 — ConnectingState is discoverable and labels are clear
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-17 — StreamFailedState panel is clear and actionable
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

### UT-18 — Inline validation messages are visible and positioned near the Watch button
**Verdict:** SKIPPED
**Reason:** Frontend not running at http://localhost:3650

---

## Environment

- **Frontend URL:** http://localhost:3650
- **Browser:** Chrome via MCP (not used)
- **Test Date:** 2026-06-06
- **Evidence directory:** `reports/qa/goal-i_will_be_super_rich-iter-9-evidence/`
- **Skip reason:** Frontend was not running at http://localhost:3650 when browser-qa-agent was invoked. The `browser-qa-phase.sh` script manages service startup, but the frontend was unavailable at execution time.
