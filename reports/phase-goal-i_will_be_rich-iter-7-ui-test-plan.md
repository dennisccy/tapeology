# Phase N — UI Test Plan

**Phase:** goal-i_will_be_rich-iter-7
**Date:** 2026-06-03
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Scope

This iteration adds a single net-new user-facing control — a **Stop** button in the top bar — that ends the current watch (`DELETE /watch/{ticker}`), returns the body to the idle/empty state, and lets the user re-watch the same ticker from a cold start. All surfaces live on the one route `/`. There are no new pages or navigation changes.

These UI tests cover the browser-observable behavior. Pure API/contract checks (404 reads, 4404 WS, determinism) live in the functional test plan (`reports/qa/goal-i_will_be_rich-iter-7-test-plan.md`, TC-01–TC-09) and are not duplicated here.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Home cockpit loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running at http://localhost:8000
- No ticker watched yet (fresh page load)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error overlay
- The "Tapeology" wordmark is visible at the top-left of the top bar
- A "Ticker e.g. SIM-BUYER" input field and a green "Watch" button are visible in the top bar
- The body shows the idle state: a "▦" glyph and the heading "No ticker watched"
- The status indicator at the top-right reads "idle" with a grey dot
- No "Stop" button is visible anywhere in the top bar
- No console errors

---

### UT-02 — Stop button is absent on the idle screen (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` — `TopBar`

**Preconditions:**
- Frontend running at http://localhost:3650
- No ticker is currently watched (idle state)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Inspect the top bar from left to right (wordmark → ticker input → Watch button → status dot)

**Expected Result:**
- There is NO "Stop" button and NO "Watching …" label anywhere in the top bar
- The only buttons present in the top bar are the green "Watch" button
- The body still reads "No ticker watched"

---

### UT-03 — Stop button appears while a ticker is watched (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` — `TopBar`

**Preconditions:**
- Frontend running at http://localhost:3650; backend running
- No ticker watched (start from idle)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the "Ticker e.g. SIM-BUYER" input field
3. Click the green "Watch" button
4. Wait for the top bar to update

**Expected Result:**
- The top bar now shows the label "Watching" followed by `SIM-BUYER` in monospaced text
- A "Stop" button appears immediately after the `SIM-BUYER` label
- The "Stop" button renders as a rose-outlined ghost button (rose text, rose border, transparent fill)
- The body switches from the idle state to the populated cockpit (panels begin rendering)

---

### UT-04 — User can stop a live watch and return to idle (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `TopBar` → page body

**Preconditions:**
- Frontend + backend running
- `SIM-BUYER` freshly watched and the status dot reads "live" with cockpit panels populated
- (Optional, to widen the live window) backend started with `TAPEOLOGY_FEED_PACE=0.12`

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait until the top-right status dot reads "live" (green) and the cockpit panels show numeric values
4. Click the "Stop" button next to the "Watching SIM-BUYER" label promptly, while the dot still reads "live"

**Expected Result:**
- The body immediately replaces the populated cockpit with the idle state showing "No ticker watched"
- The "Watching SIM-BUYER" label and the "Stop" button both disappear from the top bar
- The status dot returns to "idle" (grey)
- No stale numbers and no frozen last cockpit frame remain on screen
- No further snapshot updates arrive (values do not keep changing after Stop)

---

### UT-05 — Full watch lifecycle on one page without reload (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend + backend running, starting from idle

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input, click "Watch", and wait for the cockpit to populate
3. Click "Stop" and confirm the body shows "No ticker watched"
4. Type `SIM-SELLER` into the ticker input and click "Watch"
5. Wait for the cockpit to populate, then click "Stop" again
6. Do NOT reload the browser at any point during steps 2–5

**Expected Result:**
- Each "Watch" populates the cockpit for the entered ticker; the top bar shows "Watching <that ticker>"
- Each "Stop" returns the body to "No ticker watched" and removes the Stop button
- The entire start → read → stop → start-again → stop cycle completes without a page reload
- No errors appear in the top bar error row at any point

---

### UT-06 — Re-watch the same ticker gives a fresh cold-start read (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `Cockpit` (re-watch path)

**Preconditions:**
- Frontend + backend running, starting from idle

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER`, click "Watch", and wait for the cockpit to populate (status dot "live")
3. Click "Stop"; confirm the body reads "No ticker watched"
4. Type `SIM-BUYER` again into the ticker input and click "Watch"
5. Observe the status dot and cockpit panels through the transition

**Expected Result:**
- The status dot progresses from a connecting/idle affordance toward "live" — i.e. a cold start
- The cockpit repopulates from scratch with fresh values, NOT a frozen or "closed" leftover frame
- The status dot does NOT immediately show "closed" (rose) — the re-watch builds a brand-new engine
- The scenario chip (if shown) resolves to `buyer_control` for `SIM-BUYER` (proves a genuine fresh read)

---

### UT-07 — Stop while stream already closed still returns to idle (error / edge)

**Type:** error
**Priority:** P2
**Surface:** `/` — `TopBar` error row + page body

**Preconditions:**
- Frontend + backend running
- A watched ticker whose bounded sim stream has already exhausted (status dot reads "closed", rose) so the backend `DELETE` may return 404 (effectively-stopped)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER`, click "Watch", and wait until the status dot reads "closed" (rose) — i.e. the bounded stream has exhausted
3. Click the "Stop" button

**Expected Result:**
- The body returns to the idle state "No ticker watched" despite the backend `DELETE` returning 404
- The "Watching SIM-BUYER" label and Stop button disappear
- No error banner is left displayed in the top bar error row (a 404 is treated as effectively-stopped)
- The status dot returns to "idle" (grey)

---

### UT-08 — Backend-unreachable Stop still empties the UI (error)

**Type:** error
**Priority:** P2
**Surface:** `/` — page body

**Preconditions:**
- Frontend running; a ticker (`SIM-BUYER`) is currently watched
- Backend then stopped/unreachable (simulate by stopping the backend process before clicking Stop)

**Steps:**
1. With `SIM-BUYER` watched and the cockpit visible, stop the backend so `DELETE /watch/SIM-BUYER` cannot succeed
2. Click the "Stop" button

**Expected Result:**
- The body still returns to the idle state "No ticker watched" (idle is the truthful end state regardless of the call result)
- The Stop button disappears
- The UI does not crash or hang; no stale cockpit frame remains

---

### UT-09 — Watch ticker still works after this phase (regression — J-01)

**Type:** regression
**Priority:** P1
**Surface:** `/` — Watch form → `Cockpit`

**Preconditions:**
- Frontend + backend running, starting from idle

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait for the cockpit to render

**Expected Result:**
- The cockpit renders with its panels (quote, recent trades, features, tape state + confidence, observations, event log)
- The status dot progresses to "live" (green) for a fresh sim stream
- The "Watch" workflow is unchanged from prior iterations — no new obstacle introduced by the Stop control

---

### UT-10 — UI value equals REST value on the active read (regression — J-08)

**Type:** regression
**Priority:** P1
**Surface:** `/` — `Cockpit`

**Preconditions:**
- Frontend + backend running
- `SIM-BUYER` watched and live

**Steps:**
1. Navigate to `http://localhost:3650`, watch `SIM-BUYER`, and wait for the cockpit to populate
2. Note one displayed value (e.g. the tape state / scenario label, or a feature value such as `buy_price_impact`)
3. In a terminal, run `curl -s http://localhost:8000/tape/SIM-BUYER/summary` (or the relevant `/state`/`/features` read)
4. Compare the displayed value to the corresponding REST value

**Expected Result:**
- The value shown in the UI matches the REST response exactly (single source of truth — no recomputation)
- The scenario for `SIM-BUYER` reads `buyer_control` in both the UI and the REST response

---

### UT-11 — Stop button is discoverable and clearly labeled (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — `TopBar`

**Preconditions:**
- Frontend + backend running, starting from idle

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-BUYER` and click "Watch"
3. Without prior instructions, look for a way to stop watching

**Expected Result:**
- The "Stop" button is visible within the top bar, directly beside the "Watching SIM-BUYER" label — found in 0 extra clicks (it is on the same screen)
- The button text reads "Stop" and carries an accessible label "Stop watching" (`aria-label`)
- Its rose color visually signals a stop/teardown action, distinct from the green "Watch" button
- A keyboard user can Tab to the Stop button and activate it with Enter/Space (it is a real `<button>` with a focus ring)

---

### UT-12 — No stale/fabricated data after Stop (ux / anti-goal)

**Type:** ux
**Priority:** P1
**Surface:** `/` — page body

**Preconditions:**
- Frontend + backend running
- `SIM-BUYER` watched with the cockpit showing populated numbers

**Steps:**
1. Navigate to `http://localhost:3650`, watch `SIM-BUYER`, and let the cockpit populate
2. Click "Stop"
3. Examine the entire body area carefully

**Expected Result:**
- The body shows ONLY the idle state "No ticker watched" with its prompt to enter a ticker
- There are NO leftover numbers, NO frozen quote/trades panels, and NO synthesized values anywhere on screen
- The status dot reads "idle" (grey), not a stale "live" or a frozen "closed"

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home cockpit loads | smoke | P1 | `/` |
| UT-02 | Stop absent when idle | smoke | P1 | `/` TopBar |
| UT-03 | Stop appears when watching | smoke | P1 | `/` TopBar |
| UT-04 | Stop live watch → idle | happy-path | P1 | `/` TopBar+body |
| UT-05 | Full watch lifecycle, no reload | happy-path | P1 | `/` |
| UT-06 | Re-watch = fresh cold read | happy-path | P1 | `/` Cockpit |
| UT-07 | Stop on closed stream → idle (404) | error | P2 | `/` TopBar |
| UT-08 | Backend-unreachable Stop empties UI | error | P2 | `/` body |
| UT-09 | Watch still works (J-01) | regression | P1 | `/` form+Cockpit |
| UT-10 | UI ≡ REST value (J-08) | regression | P1 | `/` Cockpit |
| UT-11 | Stop discoverable & labeled | ux | P2 | `/` TopBar |
| UT-12 | No stale/fabricated data after Stop | ux | P1 | `/` body |

**P1 tests must all pass for browser QA verdict to be PASS.**
