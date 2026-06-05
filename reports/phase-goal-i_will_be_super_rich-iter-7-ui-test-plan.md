# Phase goal-i_will_be_super_rich-iter-7 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-7
**Date:** 2026-06-05
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Home page loads with watch controls visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load (no loading spinner)

**Expected Result:**
- The page renders without a blank screen or error message
- The top bar (`<header>`) is visible with a ticker/provider input area and a "Watch" button
- No red error banner or console crash messages are visible
- The cockpit panels (Quote, Recent Trades, Feature Counters, Tape State) area is present (may be empty/idle before any watch is started)

---

### UT-02 — Pause button appears when a SIM-BUYER watch goes live (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` — `TopBar` watch-control cluster

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running at http://localhost:8000
- SIM-BUYER provider dataset is available

**Steps:**
1. Navigate to `http://localhost:3650`
2. Locate the provider selector in the top bar and select or confirm `SIM-BUYER`
3. Click the "Watch" button
4. Wait up to 5 seconds for the stream-status indicator in the top-right corner to show a pulsing green dot labeled "live" or a yellow dot labeled "connecting"

**Expected Result:**
- An amber-bordered button labeled "Pause" appears in the top bar to the left of the "Stop" button
- The "Stop" button remains visible
- No "Resume" button is visible at this point
- The page does not crash or go blank

---

### UT-03 — No Pause or Resume button shown before any watch is started (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` — `TopBar` idle state

**Preconditions:**
- Frontend running at http://localhost:3650
- No watch has been started (fresh page load or after a Stop)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Do not click "Watch"
3. Inspect the top bar for any Pause or Resume buttons

**Expected Result:**
- Neither a "Pause" button nor a "Resume" button is present in the top bar
- The "Watching [TICKER] …" cluster is not shown
- The stream-status dot in the top-right shows no "paused", "live", or "connecting" indicator (idle state)

---

### UT-04 — Clicking Pause freezes the watch and shows the PAUSED indicator (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `TopBar` Pause button

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running at http://localhost:8000
- SIM-BUYER is being watched and the stream-status dot shows "live" (green pulsing dot)
- The cockpit shows at least some recent trades (wait ~3 seconds after clicking Watch)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select provider `SIM-BUYER` and click the "Watch" button
3. Wait 3 seconds until the stream-status dot in the top-right shows "live" (green)
4. Note the current trade count displayed in the Recent Trades panel
5. Click the amber "Pause" button in the top bar

**Expected Result:**
- The "Pause" button is immediately replaced by an amber-bordered "Resume" button in the same position
- The stream-status dot in the top-right changes to an amber (non-pulsing) dot with the label "paused" — it does NOT still read "live" or "connecting"
- The "Stop" button remains visible and unchanged beside "Resume"
- The cockpit panels (Quote, Recent Trades, Feature Counters, Tape State) remain visible with the data they showed at the moment of the pause — they do not clear or go blank
- The prediction chart (if visible) continues to show the same candles it had at pause time — no new candles appear

---

### UT-05 — Paused cockpit stays frozen while paused (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — Cockpit panels (freeze behavior while paused)

**Preconditions:**
- A SIM-BUYER watch has been paused (UT-04 completed successfully)
- The stream-status dot shows "paused" (amber)

**Steps:**
1. After clicking Pause (as in UT-04), note the exact number shown in the Recent Trades panel as `T1`
2. Wait 5 seconds without clicking anything
3. Check the Recent Trades panel count again (record as `T2`)
4. Check the prediction chart — count the number of visible candles (record as `C1` before, `C2` after the wait)

**Expected Result:**
- `T2` equals `T1` — the trade count did not increment during the 5-second pause
- `C2` equals `C1` — no new candles were added to the chart during the pause
- The PAUSED amber dot and "paused" label are still visible in the top-right throughout
- No loading spinner or "reconnecting" message appeared

---

### UT-06 — Clicking Resume continues the stream from the frozen point (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `TopBar` Resume button

**Preconditions:**
- A SIM-BUYER watch is currently paused (UT-05 completed)
- The stream-status dot shows "paused" (amber)
- The trade count at pause time is known (call it `T_paused`)

**Steps:**
1. Confirm the "Resume" button is visible in amber beside "Stop"
2. Note the current Recent Trades count as `T_paused`
3. Click the amber "Resume" button
4. Observe the stream-status dot in the top-right corner immediately after clicking Resume
5. Wait 3 seconds
6. Note the new Recent Trades count as `T_after`

**Expected Result:**
- The "Resume" button is immediately replaced by the amber "Pause" button (reverting to the live-watch control state)
- The stream-status dot changes from "paused" (amber) back to "live" (green pulsing) — it does NOT jump to "connecting" or show a flash of an unexpected state
- `T_after` is greater than `T_paused` by approximately 1–3 trades (normal streaming cadence of ~1 trade/second for 3 seconds) — NOT a sudden jump of 10+ trades that would indicate fabricated backfill
- The prediction chart begins accumulating new candles again at its normal cadence

---

### UT-07 — Stop after Pause fully closes the session (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `TopBar` Stop button (called on a paused watch)

**Preconditions:**
- A SIM-BUYER watch is currently paused
- The stream-status dot shows "paused" (amber)
- The "Stop" and "Resume" buttons are both visible in the top bar

**Steps:**
1. Confirm the watch is paused: stream-status dot shows "paused" and "Resume" button is visible
2. Click the "Stop" button
3. Wait 2 seconds

**Expected Result:**
- The entire "Watching SIM-BUYER … Pause Resume Stop" cluster disappears from the top bar — no stale buttons remain
- The cockpit panels (Quote, Recent Trades, Feature Counters, Tape State) return to idle/empty state — no data from the previous session remains visible
- The prediction chart is hidden or cleared
- The stream-status dot no longer shows "paused" or "live" — it shows either nothing or an idle state (e.g., no dot)
- Starting a new watch by clicking "Watch" again succeeds without error

---

### UT-08 — PAUSED status dot is amber and non-pulsing; Live dot is green and pulsing (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — Stream-status dot in `TopBar` top-right

**Preconditions:**
- Frontend running at http://localhost:3650
- SIM-BUYER can be watched

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select SIM-BUYER and click "Watch"
3. Wait 3 seconds until the stream-status dot shows "live"
4. Observe the dot: note its color and whether it pulses/animates
5. Click the "Pause" button
6. Observe the dot immediately after pausing: note its color and animation

**Expected Result:**
- While live: the dot is **green** and visually pulses/animates; the text label reads "live"
- While paused: the dot is **amber** and does **not** pulse or animate (it is static); the text label reads "paused" — NOT "live", NOT "stale"
- The color change from green to amber is immediately visible without a page refresh

---

### UT-09 — Pause button has amber styling matching Stop button size (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — `TopBar` watch-control cluster

**Preconditions:**
- A SIM-BUYER watch is live (stream-status shows "live")
- Both "Pause" and "Stop" buttons are visible in the top bar

**Steps:**
1. With an active live SIM-BUYER watch, observe the watch-control area in the top bar
2. Compare the visual size and shape of the "Pause" button to the "Stop" button
3. Note the border and text color of the "Pause" button

**Expected Result:**
- The "Pause" button has amber text and an amber border (visually distinct from the "Stop" button which has its own color)
- Both "Pause" and "Stop" buttons are similar in size and padding (they use the same `px-2.5 py-1 text-xs font-semibold rounded border` pattern — neither is much larger than the other)
- The "Pause" label is clearly readable at normal screen size

---

### UT-10 — Resume button replaces Pause; Stop remains when paused (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — `TopBar` watch-control cluster while paused

**Preconditions:**
- A SIM-BUYER watch is currently paused (stream-status shows "paused")

**Steps:**
1. Confirm the watch is paused
2. Count the buttons visible in the top bar watch-control cluster

**Expected Result:**
- Exactly two action buttons are visible: "Resume" and "Stop"
- "Pause" is NOT visible (it has been replaced by "Resume")
- The button order is: "Resume" then "Stop" (Pause/Resume sits beside Stop as described)
- Both "Resume" and "Stop" are clearly labeled with readable text

---

### UT-11 — Watch, Pause, Stop cycle can be repeated without error (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — full watch lifecycle

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running at http://localhost:8000
- SIM-BUYER available

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select SIM-BUYER and click "Watch"
3. Wait 3 seconds until stream shows "live"
4. Click "Pause" — confirm stream-status shows "paused"
5. Click "Stop" — confirm the cockpit returns to idle and the watch-control cluster disappears
6. Select SIM-BUYER again and click "Watch" a second time
7. Wait 3 seconds

**Expected Result:**
- The second watch starts successfully: stream-status dot shows "live" and the "Pause" button reappears
- The cockpit repopulates with fresh data (Recent Trades count restarts from a low number, not carrying over from the prior session)
- No error banner, crash overlay, or frozen UI state appears between or after the two watch cycles

---

### UT-12 — Stop without pausing first still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — `TopBar` Stop button (unpaused watch)

**Preconditions:**
- A SIM-BUYER watch is live (stream-status shows "live")
- The "Pause" and "Stop" buttons are visible

**Steps:**
1. With an active live SIM-BUYER watch, click "Stop" directly without clicking "Pause" first
2. Wait 2 seconds

**Expected Result:**
- The watch-control cluster disappears from the top bar (same behavior as before this iteration)
- The cockpit returns to idle/empty
- The stream-status dot no longer shows "live" or any active state
- No error message appears

---

### UT-13 — Prediction chart (PriceChart) remains visible and populated after Pause and Resume (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — `PriceChart` component (SIM mode)

**Preconditions:**
- Frontend running at http://localhost:3650
- A SIM-BUYER watch has been running for at least 5 seconds (chart has at least 3 visible candles)

**Steps:**
1. Navigate to `http://localhost:3650`, select SIM-BUYER, click "Watch"
2. Wait 5 seconds — confirm the prediction chart shows multiple candlestick bars
3. Note the number of candles visible (`C_before`)
4. Click "Pause" and wait 2 seconds
5. Confirm the chart still shows the same candles (`C_before`) — no candles added, none removed
6. Click "Resume" and wait 3 seconds
7. Confirm the chart shows more candles than `C_before`

**Expected Result:**
- After Pause: chart still shows exactly `C_before` candles — the chart did not clear, did not show a blank canvas, and did not show a loading spinner
- After Resume: chart shows `C_before + N` candles where N >= 1 (new candles are being added again)
- The chart colors (emerald dots for buyer_control on SIM-BUYER) are still visible after both Pause and Resume

---

### UT-14 — Cockpit does not clear or flash when Pause is clicked (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/` — Cockpit panels (quote, recent trades, features, tape state)

**Preconditions:**
- A SIM-BUYER watch is live and the cockpit shows populated data (quote price visible, trades listed)

**Steps:**
1. With a populated SIM-BUYER watch running, observe the Quote panel (confirm a price is displayed)
2. Click the "Pause" button
3. Immediately observe all cockpit panels (Quote, Recent Trades, Feature Counters, Tape State) in the 1 second after clicking Pause

**Expected Result:**
- None of the cockpit panels flash blank, show a loading spinner, or show an error message when Pause is clicked
- The quote price that was showing before Pause is still showing after Pause — it did not reset to "--" or "0"
- The Recent Trades list shows the same entries it had at pause time — it was not cleared

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home page loads with watch controls visible | smoke | P1 | `/` |
| UT-02 | Pause button appears when SIM-BUYER watch goes live | smoke | P1 | `/` TopBar |
| UT-03 | No Pause or Resume button before any watch is started | smoke | P1 | `/` TopBar idle |
| UT-04 | Clicking Pause freezes the watch and shows PAUSED indicator | happy-path | P1 | `/` TopBar |
| UT-05 | Paused cockpit stays frozen while paused | happy-path | P1 | `/` Cockpit panels |
| UT-06 | Clicking Resume continues the stream from the frozen point | happy-path | P1 | `/` TopBar |
| UT-07 | Stop after Pause fully closes the session | happy-path | P1 | `/` TopBar |
| UT-08 | PAUSED dot is amber and non-pulsing; Live dot is green and pulsing | ux | P2 | `/` stream-status dot |
| UT-09 | Pause button has amber styling matching Stop button size | ux | P2 | `/` TopBar |
| UT-10 | Resume button replaces Pause; Stop remains when paused | ux | P2 | `/` TopBar |
| UT-11 | Watch, Pause, Stop cycle can be repeated without error | regression | P1 | `/` |
| UT-12 | Stop without pausing first still works | regression | P1 | `/` TopBar |
| UT-13 | Prediction chart remains visible and populated after Pause and Resume | regression | P1 | `/` PriceChart |
| UT-14 | Cockpit does not clear or flash when Pause is clicked | regression | P2 | `/` Cockpit panels |

**P1 tests must all pass for browser QA verdict to be PASS.**
