# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-4 — UI Test Plan

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-4
**Date:** 2026-06-10
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — Cockpit home loads with thesis strip visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running (verify with `curl http://localhost:8000/health`)
- No active thesis exists (stop any watch before starting)

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load (spinner disappears)
3. Locate the thesis strip area — it sits between the chart and the panel grid
4. Look for the idle declare affordance (a button or prompt labeled "Declare a thesis" or similar)

**Expected Result:**
- The cockpit page renders without a blank screen or error message
- The thesis strip area is visible on the page
- The idle declare affordance ("Declare a thesis" or equivalent) is visible in the strip
- No red error banner appears in the header or strip area
- Browser console shows no uncaught JavaScript errors

---

### UT-02 — Verdict chip transitions from "pending" to "confirming" on SIM-BUYER (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- No active thesis exists — stop any prior watch first
- SIM-BUYER ticker is available in the ticker selector

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "SIM-BUYER" from the ticker selector at the top of the cockpit
3. Click the "Watch" (or "Start watching") button to begin the tape stream
4. When the tape is streaming, click the "Declare a thesis" button in the thesis strip
5. In the declaration form, select setup type "trend_continuation" and direction "long"
6. Set the invalidation price to a value well below the current last price (e.g., current last minus 5 points)
7. Submit the declaration form (click "Declare" or "Confirm")
8. Observe the verdict chip in the top-right area of the active-thesis row in the thesis strip
9. Confirm the chip initially shows "Pending" in a slate (grey) color
10. Wait approximately 3–5 seconds of tape time while the buyer-control phase runs
11. Observe the verdict chip again

**Expected Result:**
- After declaration, the verdict chip reads "Pending" with a slate (grey) background
- After approximately 3–5 seconds of buyer-control tape, the chip transitions to "Confirming" with an emerald (green) background
- The `data-testid="verdict-chip"` element is present in the DOM
- The chip's `data-verdict` attribute reads `confirming` after the transition
- No page reload occurs during the transition — the chip updates in place

---

### UT-03 — Evidence sentence appears beneath the verdict chip for every verdict state (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- An active thesis has been declared (follow steps 1–7 from UT-02, using SIM-BUYER and trend_continuation/long)

**Steps:**
1. Navigate to `http://localhost:3650` with an active thesis (declared via steps in UT-02)
2. Observe the thesis strip for an evidence sentence below the verdict chip
3. While the verdict is "Pending" (slate chip), look for a sentence immediately beneath the chip
4. Wait for the verdict to transition to "Confirming" (emerald chip)
5. Read the evidence sentence that appears beneath the chip
6. Confirm the sentence is written in plain English present-tense (not imperative, not predictive)

**Expected Result:**
- A non-empty evidence sentence is visible beneath the verdict chip at all times, including while the verdict is "Pending"
- The `data-testid="verdict-evidence"` element is present in the DOM and has non-empty text content
- While "Pending": the sentence describes current tape state (e.g., "buyers are pressing price up" or "awaiting confirming signal")
- While "Confirming": the sentence is emerald-colored and mentions buyer control and/or price impact (e.g., "buyers keep pressing price up (buy_price_impact +0.4000); the tape confirms your thesis")
- The sentence color matches the chip color (emerald for confirming, slate for pending)
- The sentence does NOT contain imperative phrases like "wait for" or predictive phrases like "price will"

---

### UT-04 — Verdict chip shows amber "Weakening" state on SIM-SHIFT (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- No active thesis exists — stop any prior watch
- SIM-SHIFT ticker is available

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "SIM-SHIFT" from the ticker selector
3. Click "Watch" to start the tape stream
4. When the tape is streaming in the buyer-control phase, click "Declare a thesis"
5. In the declaration form, select setup type "trend_continuation" and direction "long"
6. Set the invalidation price well below current last price
7. Submit the declaration (click "Declare" or "Confirm")
8. Observe the verdict chip — wait for it to reach "Confirming" (emerald) as the buyer phase runs
9. Continue watching as SIM-SHIFT transitions the tape to a seller-control or neutral phase
10. Observe the verdict chip after the tape shifts

**Expected Result:**
- After the tape shifts away from buyer control, the verdict chip transitions from "Confirming" (emerald) to "Weakening" (amber)
- The chip text reads "Weakening" and the background is amber (yellow-orange)
- The evidence sentence beneath the chip is also amber-colored
- The evidence sentence mentions faded support (e.g., "supporting evidence faded" or "control is no longer clearly with buyers")
- The thesis remains active — the "Declare a thesis" idle affordance does NOT reappear
- No "Thesis invalidated — resolved" line appears (the thesis is still active, just weakening)

---

### UT-05 — Verdict chip shows rose "Rejecting" state on SIM-SELLER with far invalidation (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- No active thesis exists — stop any prior watch
- SIM-SELLER ticker is available

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "SIM-SELLER" from the ticker selector
3. Click "Watch" to start the tape stream
4. When the tape is streaming, click "Declare a thesis"
5. In the declaration form, select setup type "trend_continuation" and direction "long"
6. Set the invalidation price to a value WELL below the current last price (e.g., 10+ points below) so invalidation does not trigger
7. Submit the declaration (click "Declare" or "Confirm")
8. Observe the verdict chip while the seller-control phase runs

**Expected Result:**
- The verdict chip transitions to "Rejecting" with a rose (red/pink) background
- The chip text reads "Rejecting"
- The evidence sentence beneath the chip is also rose-colored and mentions seller control and/or price impact (e.g., "sellers are driving price down; the tape rejects your thesis")
- The thesis remains active (no "Thesis invalidated — resolved" notice appears)
- The idle "Declare a thesis" affordance does NOT reappear — the thesis is still ongoing

---

### UT-06 — Terminal invalidated treatment appears and persists on SIM-SELLER (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- No active thesis exists — stop any prior watch
- SIM-SELLER ticker is available

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "SIM-SELLER" from the ticker selector
3. Click "Watch" to start the tape stream
4. Note the current last price shown in the tape display
5. Click "Declare a thesis"
6. In the declaration form, select setup type "trend_continuation" and direction "long"
7. Set the invalidation price just 1–2 points ABOVE the current last price (so the next downward print will breach it)
8. Submit the declaration (click "Declare" or "Confirm")
9. Observe the thesis strip as the tape continues printing prices
10. Wait for a print that triggers invalidation (a price at or below the invalidation level)
11. Observe the verdict chip, the "resolved" notice, and the evidence sentence

**Expected Result:**
- The verdict chip transitions to "Invalidated" with a rose (red/pink) background and a heavier ringed rose border
- The chip text shows a "✕" prefix (e.g., "✕ Invalidated")
- A second line reading "Thesis invalidated — resolved" appears in rose below the evidence sentence
- The evidence sentence mentions the offending print price (e.g., "price printed through your invalidation level at 123.45")
- The idle "Declare a thesis" affordance does NOT reappear — the strip retains the terminal invalidated treatment
- Refreshing the page (press F5) still shows the terminal invalidated treatment, not the idle declare affordance

---

### UT-07 — Expired (watch-stopped) thesis reverts to idle, invalidated thesis does not (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- Complete UT-06 first to have a known-invalidated thesis state

**Steps:**
1. After completing UT-06, confirm the terminal invalidated treatment is visible in the thesis strip
2. Stop the watch by clicking the "Stop watching" (or "Stop") button
3. Observe the thesis strip immediately after stopping the watch
4. Now stop the current state — navigate to `http://localhost:3650` fresh
5. Select "SIM-BUYER" from the ticker selector and start a new watch
6. Declare a new thesis (trend_continuation/long with a far invalidation)
7. Observe the verdict chip transition to "Confirming"
8. Click "Stop watching" to stop the watch (without triggering invalidation)
9. Observe the thesis strip after stopping

**Expected Result:**
- After stopping the watch in step 2 (post-invalidation): the terminal invalidated treatment remains visible — it does NOT revert to the idle "Declare a thesis" affordance
- After stopping the watch in step 8 (non-invalidated expired thesis): the strip DOES revert to the idle "Declare a thesis" affordance — the thesis simply expired
- These two behaviors are distinct: invalidated = terminal treatment stays; expired (watch stopped) = strip clears to idle

---

### UT-08 — Verdict chip uses taxonomy-owned labels, not raw enum strings (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- No active thesis exists — stop any prior watch

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "SIM-BUYER" from the ticker selector and start watching
3. Declare a thesis (trend_continuation/long with a far invalidation)
4. Do NOT open the declaration form again — simply close and reopen the page in the browser (Cmd+W then navigate back to `http://localhost:3650`)
5. Observe the verdict chip after the page reloads and the thesis reattaches
6. Wait for the verdict to transition to "Confirming"
7. Read the text on the verdict chip

**Expected Result:**
- The verdict chip shows "Confirming" (capitalized, human-readable taxonomy label) — NOT the raw lowercase enum string `confirming`
- The same applies for other states: "Weakening" not `weakening`, "Rejecting" not `rejecting`, "Pending" not `pending`
- Taxonomy labels load immediately when the thesis is active — the chip does NOT briefly show the raw enum string before the taxonomy data arrives

---

### UT-09 — Pending state shows evidence sentence before any verdict fires (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- No active thesis exists

**Steps:**
1. Navigate to `http://localhost:3650`
2. Select "SIM-BUYER" from the ticker selector and start watching
3. Click "Declare a thesis"
4. In the declaration form, select setup type "level_break" and direction "long"
5. Set the declared level price ABOVE the current last price (so the level has not been crossed yet)
6. Set the invalidation price well below current last
7. Submit the declaration (click "Declare" or "Confirm")
8. Immediately after submission, observe the thesis strip before any verdict transition occurs
9. Look for the evidence sentence beneath the verdict chip while the chip is still showing "Pending" (slate)

**Expected Result:**
- The verdict chip shows "Pending" in a slate (grey) background immediately after declaration
- An evidence sentence IS visible beneath the chip even while "Pending" — it is not empty, not a placeholder, and not hidden
- The evidence sentence text is in plain English (e.g., "awaiting price cross above declared level" or similar present-tense description)
- The `data-testid="verdict-evidence"` element exists in the DOM with non-empty text content

---

### UT-10 — Rejecting state does not auto-resolve the thesis (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- Complete UT-05 first (SIM-SELLER, trend_continuation/long, far invalidation, reached "Rejecting" state)

**Steps:**
1. After the verdict chip shows "Rejecting" (from UT-05), observe the full thesis strip
2. Look for the "Declare a thesis" idle affordance in the strip
3. Look for any "Thesis invalidated — resolved" or "Thesis expired" notice
4. Look for the thesis declaration details (setup type, direction, invalidation price) that were visible before

**Expected Result:**
- The "Declare a thesis" idle affordance does NOT appear — the thesis is still active
- No "Thesis invalidated — resolved" notice appears — rejecting is a judgment, not a resolution
- The thesis declaration details remain visible in the strip
- The verdict chip shows "Rejecting" in rose but WITHOUT the heavier ringed border and WITHOUT the "✕" prefix (those are reserved for "Invalidated")

---

### UT-11 — Verdict chip color semantics match specification (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- Access to both SIM-BUYER and SIM-SELLER tickers

**Steps:**
1. Navigate to `http://localhost:3650`, select SIM-BUYER, start watching, declare a trend_continuation/long thesis with far invalidation
2. Wait for the verdict chip to reach "Confirming" — observe the chip background color
3. Stop the watch, start a new watch on SIM-SHIFT, declare trend_continuation/long, wait for "Confirming" then wait for the shift to produce "Weakening" — observe the chip color when showing "Weakening"
4. Stop the watch, start a new watch on SIM-SELLER, declare trend_continuation/long with far invalidation, wait for "Rejecting" — observe the chip color
5. Stop the watch, start a new watch on SIM-SELLER, declare trend_continuation/long with invalidation just above current last, wait for "Invalidated" — observe the chip color and border

**Expected Result:**
- "Confirming": chip background is emerald (green) — clearly distinct from amber, rose, or slate
- "Weakening": chip background is amber (yellow-orange) — clearly distinct from emerald, rose, or slate
- "Rejecting": chip background is rose (red/pink) — clearly distinct from emerald, amber, or slate; NO heavier ringed border; NO "✕" prefix
- "Invalidated": chip background is rose AND has a heavier ringed rose border (ring-1 ring-rose-500/50) AND shows "✕" prefix — visually distinct from merely "Rejecting"
- "Pending": chip background is slate (grey)
- Evidence sentence color matches chip color in all five states

---

### UT-12 — Cockpit chart and panel grid are unaffected by thesis strip changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3650
- Backend is running
- An active thesis has been declared (follow UT-02 steps 1–7)

**Steps:**
1. Navigate to `http://localhost:3650` with an active thesis showing "Confirming"
2. Observe the chart area above the thesis strip
3. Observe the panel grid below the thesis strip
4. Verify the "Descriptive only — not trading advice" disclaimer line is still present in the strip
5. Scroll the page up and down to confirm no layout reflow has occurred

**Expected Result:**
- The chart renders normally — no blank chart area, no missing price bars
- The panel grid renders normally — all existing panels (tape features, etc.) are visible
- The thesis strip sits between the chart and panel grid as before — no reflow, no overlap
- The "Descriptive only — not trading advice" line is still present and readable
- The thesis strip does not occupy more vertical space than before this phase's changes

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit home loads with thesis strip visible | smoke | P1 | `/` |
| UT-02 | Verdict chip transitions pending→confirming on SIM-BUYER | happy-path | P1 | `/` |
| UT-03 | Evidence sentence appears for every verdict state | happy-path | P1 | `/` |
| UT-04 | Verdict chip shows amber "Weakening" on SIM-SHIFT | happy-path | P1 | `/` |
| UT-05 | Verdict chip shows rose "Rejecting" on SIM-SELLER with far invalidation | happy-path | P1 | `/` |
| UT-06 | Terminal invalidated treatment appears and persists | happy-path | P1 | `/` |
| UT-07 | Expired thesis reverts to idle; invalidated thesis does not | regression | P1 | `/` |
| UT-08 | Verdict chip uses taxonomy-owned labels, not raw enums | regression | P1 | `/` |
| UT-09 | Pending state shows evidence sentence before any verdict fires | validation | P2 | `/` |
| UT-10 | Rejecting state does not auto-resolve the thesis | validation | P2 | `/` |
| UT-11 | Verdict chip color semantics match specification | ux | P2 | `/` |
| UT-12 | Cockpit chart and panel grid unaffected by thesis strip changes | regression | P1 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.**

**Coverage map vs. UI surface map:**

| UI Surface Map Row | Covered by |
|-------------------|-----------|
| Verdict chip `data-testid="verdict-chip"` live color transitions | UT-02, UT-04, UT-05, UT-11 |
| Verdict evidence line `data-testid="verdict-evidence"` | UT-03, UT-09 |
| Terminal invalidated treatment (✕ chip, "resolved" notice, rose ring) | UT-06, UT-07, UT-10 |
| Taxonomy fetch on active state (labels not raw enums) | UT-08 |
| Weakening and rejecting states (new visual representations) | UT-04, UT-05, UT-10, UT-11 |
