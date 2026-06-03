# Phase N — UI Test Results

**Phase:** goal-i_will_be_rich-iter-7
**Date:** 2026-06-03
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** SKIPPED

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 0/12 tests passed (12 skipped)

**Reason:** Frontend not running. A precondition check found `http://localhost:3650` unreachable (HTTP `000`). The backend at `http://localhost:8650/health` responded `200`, but browser UI tests require the frontend, so no UI test case could be executed. No browser automation was attempted, per the not-available directive.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Home cockpit loads without errors | smoke | P1 | Idle cockpit renders: wordmark, ticker input + green Watch button, "▦ No ticker watched", idle status dot, no Stop button, no console errors | Not executed — frontend unreachable at http://localhost:3650 | SKIP | none |
| UT-02 | Stop button is absent on the idle screen | smoke | P1 | No "Stop" button or "Watching …" label in the top bar; only the green Watch button; body reads "No ticker watched" | Not executed — frontend unreachable | SKIP | none |
| UT-03 | Stop button appears while a ticker is watched | smoke | P1 | After watching SIM-BUYER, top bar shows "Watching SIM-BUYER" + rose-outlined ghost "Stop" button; body switches to populated cockpit | Not executed — frontend unreachable | SKIP | none |
| UT-04 | User can stop a live watch and return to idle | happy-path | P1 | Clicking Stop replaces cockpit with idle "No ticker watched"; Watching label + Stop disappear; status dot → idle; no stale numbers; no further updates | Not executed — frontend unreachable | SKIP | none |
| UT-05 | Full watch lifecycle on one page without reload | happy-path | P1 | Watch SIM-BUYER → Stop → Watch SIM-SELLER → Stop, all without page reload; each Watch populates cockpit, each Stop returns to idle; no error row | Not executed — frontend unreachable | SKIP | none |
| UT-06 | Re-watch the same ticker gives a fresh cold-start read | happy-path | P1 | Re-watching SIM-BUYER after Stop yields a cold start → live (not "closed"); cockpit repopulates fresh; scenario chip resolves to buyer_control | Not executed — frontend unreachable | SKIP | none |
| UT-07 | Stop while stream already closed still returns to idle (404) | error | P2 | After a "closed" stream, clicking Stop returns body to idle despite backend DELETE 404; label + Stop disappear; no error banner; status dot → idle | Not executed — frontend unreachable | SKIP | none |
| UT-08 | Backend-unreachable Stop still empties the UI | error | P2 | With backend stopped, clicking Stop still returns body to idle "No ticker watched"; Stop disappears; no crash/hang; no stale frame | Not executed — frontend unreachable | SKIP | none |
| UT-09 | Watch ticker still works after this phase (J-01) | regression | P1 | Watching SIM-BUYER renders full cockpit panels; status dot → live; Watch workflow unchanged by the new Stop control | Not executed — frontend unreachable | SKIP | none |
| UT-10 | UI value equals REST value on the active read (J-08) | regression | P1 | Displayed value matches `/tape/SIM-BUYER/summary` REST value exactly; scenario reads buyer_control in both UI and REST | Not executed — frontend unreachable | SKIP | none |
| UT-11 | Stop button is discoverable and clearly labeled | ux | P2 | Stop visible beside "Watching SIM-BUYER" in 0 extra clicks; text "Stop" + aria-label "Stop watching"; rose color; keyboard-focusable real `<button>` | Not executed — frontend unreachable | SKIP | none |
| UT-12 | No stale/fabricated data after Stop | ux | P1 | After Stop, body shows ONLY idle "No ticker watched"; no leftover numbers/frozen panels/synthesized values; status dot idle | Not executed — frontend unreachable | SKIP | none |

---

## Passed Tests

None. No tests were executed because the frontend was not running.

---

## Failed Tests

None. No tests were executed, so none can be marked FAIL. (Per agent rules, browser-unavailability is recorded as SKIPPED, not FAIL.)

---

## Skipped Tests

All 12 test cases were skipped for the same reason: the frontend at `http://localhost:3650` was unreachable (HTTP `000`) at the time of the precondition check, so no browser UI test could be executed. No Chrome MCP browser session was started, per the not-available directive.

### UT-01 — Home cockpit loads without errors
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

### UT-02 — Stop button is absent on the idle screen
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

### UT-03 — Stop button appears while a ticker is watched
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

### UT-04 — User can stop a live watch and return to idle
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

### UT-05 — Full watch lifecycle on one page without reload
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

### UT-06 — Re-watch the same ticker gives a fresh cold-start read
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

### UT-07 — Stop while stream already closed still returns to idle (404)
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

### UT-08 — Backend-unreachable Stop still empties the UI
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

### UT-09 — Watch ticker still works after this phase (J-01)
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

### UT-10 — UI value equals REST value on the active read (J-08)
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

### UT-11 — Stop button is discoverable and clearly labeled
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

### UT-12 — No stale/fabricated data after Stop
**Verdict:** SKIPPED
**Reason:** frontend not running (http://localhost:3650 returned HTTP 000)

---

## Environment

- **Frontend URL:** http://localhost:3650 — **unreachable (HTTP 000)**
- **Backend URL:** http://localhost:8650/health — reachable (HTTP 200)
- **Browser:** Chrome via MCP — not started (frontend unavailable)
- **Test Date:** 2026-06-03
- **Evidence directory:** `reports/qa/goal-i_will_be_rich-iter-7-evidence/` (empty — no screenshots captured)

---

## Notes

- This iteration's net-new UI surface is a single **Stop** button in the top bar (`DELETE /watch/{ticker}` → return to idle, re-watchable from cold start). None of its browser-observable behavior (UT-03 through UT-08, UT-11, UT-12) could be verified here because the frontend was down.
- Pure API/contract checks (404 reads, 4404 WS, determinism) are covered separately in the functional test plan `reports/qa/goal-i_will_be_rich-iter-7-test-plan.md` (TC-01–TC-09) and are out of scope for this browser run.
- Recommended follow-up: re-run `./scripts/automation/browser-qa-phase.sh goal-i_will_be_rich-iter-7` with the frontend up (the script auto-manages services at ports 3650/8650) to obtain real PASS/FAIL evidence for the P1 cases UT-01–UT-06, UT-09, UT-10, UT-12.
