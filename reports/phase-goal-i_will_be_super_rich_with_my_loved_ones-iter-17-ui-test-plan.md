# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-17 — UI Test Plan

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-17
**Date:** 2026-06-12
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Context

This iteration is a backend-only engine performance gate (capability-34: incremental `_RefreshSide` merge). No UI surface changed. `Frontend Present: yes` exists solely to run two regression sentinels that confirm the refactored engine still produces byte-identical output visible in the cockpit:

- **J-68**: SIM-BUYER no-thesis cockpit renders all panels with the same values as before the engine change.
- **J-08**: REST endpoint `/tape/SIM-BUYER/state` agrees with what the cockpit displays.

There are no new features, no new routes, no new form fields, and no navigation changes. All test cases below are regression sentinels only.

---

## Test Cases

---

### UT-01 — SIM-BUYER cockpit loads without errors (smoke / J-68 prerequisite)

**Type:** smoke
**Priority:** P1
**Surface:** `/cockpit/SIM-BUYER`

**Preconditions:**
- Frontend is running and reachable at `http://localhost:3650`
- Backend is running and reachable at `http://localhost:8000/health` (returns HTTP 200)
- No prior watch session for SIM-BUYER is open in the browser

**Steps:**
1. Navigate to `http://localhost:3650` in a browser
2. Locate the ticker input field on the home/watch page
3. Type `SIM-BUYER` into the ticker input field
4. Click the "Watch" button (or equivalent primary CTA that starts a sim watch)
5. Wait up to 15 seconds for the cockpit page at `/cockpit/SIM-BUYER` to fully render

**Expected Result:**
- Page loads at a URL containing `/cockpit/SIM-BUYER` (or the equivalent cockpit route for that symbol)
- No blank white page, no "Error" banner, no "500" or "Cannot connect" message
- At least one visible panel heading or label appears in the cockpit layout (e.g., "Confidence", "Observations", "Event Log", or "Tape State")
- Browser developer console contains no uncaught JavaScript errors

---

### UT-02 — J-68 Sentinel: All five cockpit panels render with valid content (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/cockpit/SIM-BUYER`

**Preconditions:**
- UT-01 completed successfully (cockpit page is open and loaded)
- SIM-BUYER watch session has been running for at least 10 seconds (allow the engine to stabilize)

**Steps:**
1. On the open `/cockpit/SIM-BUYER` page, locate the **chart panel** — the main price/tape chart that shows a "Control" marker or similar tape-state annotation
2. Confirm the chart canvas is non-blank: at least one colored line, bar, or marker is drawn on the chart area (not an empty white rectangle)
3. Locate the **Confidence** display element (labeled "Confidence", "confidence", or shown as a percentage/decimal badge)
4. Read the confidence value displayed — it must be a non-zero decimal number greater than 0 and less than or equal to 1.0 (expected approximately 0.86 for SIM-BUYER in buyer_control state)
5. Locate the **tape state / classification label** displayed alongside or below the confidence value
6. Confirm the label reads `buyer_control` (not blank, not "undefined", not "error", not "0")
7. Scroll down to locate the **Observations panel** (labeled "Observations" or similar)
8. Confirm it contains at least one observation entry — a non-empty text row (not the text "undefined", not a blank row, not an empty-state placeholder like "No observations")
9. Locate the **Event Log panel** (labeled "Event Log", "Events", or similar)
10. Confirm the event log contains at least one timestamped event entry (e.g., a row showing a time value and an event description) and does not show an error state or empty-state placeholder

**Expected Result:**
- Chart panel: visible content, at least one Control or tape-state marker drawn
- Confidence display: shows a decimal value in the range (0, 1], approximately 0.86
- State label: reads `buyer_control`
- Observations panel: at least one non-blank observation row visible
- Event log panel: at least one timestamped event row visible, no error state shown

---

### UT-03 — J-08 Sentinel: REST `/tape/SIM-BUYER/state` matches cockpit display (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/tape/:symbol/state` REST endpoint + `/cockpit/SIM-BUYER` cockpit display

**Preconditions:**
- UT-02 completed successfully (cockpit is open, showing a stable `buyer_control` classification and a confidence value)
- Backend REST API is accessible at `http://localhost:8000`
- A terminal or browser address bar is available to make an HTTP GET request

**Steps:**
1. With the `/cockpit/SIM-BUYER` cockpit page open, note the exact classification label shown — write it down (expected: `buyer_control`)
2. Note the exact confidence value displayed on the cockpit — write it down (expected: approximately 0.86, displayed as a decimal or percentage)
3. Open a new browser tab and navigate to `http://localhost:8000/tape/SIM-BUYER/state`
   - Alternatively, run in a terminal: `curl http://localhost:8000/tape/SIM-BUYER/state`
4. Confirm the HTTP response status is 200 (not 404, not 500)
5. In the JSON response body, locate the `classification` field
6. Confirm that `classification` equals `buyer_control` — the same value noted in step 1
7. In the JSON response body, locate the `confidence` field
8. Confirm that the `confidence` value (as a float) matches the cockpit's displayed confidence value within normal display rounding (e.g., if cockpit shows 0.86, REST `confidence` must be in the range 0.855–0.865)
9. Confirm the JSON response body contains no error key or error message at the top level

**Expected Result:**
- `GET /tape/SIM-BUYER/state` returns HTTP 200
- `classification` field in response equals `buyer_control`
- `confidence` field in response agrees with the cockpit's displayed confidence value within display rounding
- No error fields present in the JSON body

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | SIM-BUYER cockpit loads without errors | smoke | P1 | `/cockpit/SIM-BUYER` |
| UT-02 | J-68: All five cockpit panels render with valid content | regression | P1 | `/cockpit/SIM-BUYER` |
| UT-03 | J-08: REST state endpoint matches cockpit display | regression | P1 | `/tape/SIM-BUYER/state` + `/cockpit/SIM-BUYER` |

**P1 tests must all pass for browser QA verdict to be PASS.**

No new features were added this iteration. No happy-path, validation, error, or UX test cases apply — all three cases above are regression sentinels confirming the pre-existing cockpit is unaffected by the engine performance refactor.
