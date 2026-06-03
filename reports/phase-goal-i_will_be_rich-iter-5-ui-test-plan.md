# Phase N — UI Test Plan

**Phase:** goal-i_will_be_rich-iter-5
**Date:** 2026-06-03
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- The app is a single-page cockpit at `/`. There is no navigation/router; a "watch" is started -->
<!-- by typing a ticker into the top-bar Ticker field and clicking the green "Watch" button. -->
<!-- All updates arrive live over WebSocket — do NOT reload to force a state; wait past warm-up. -->

---

### UT-01 — Cockpit loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend running at http://localhost:8000
- Frontend running at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650`
2. Wait for the page to fully load

**Expected Result:**
- The "Tapeology" wordmark is visible top-left
- A "Ticker e.g. SIM-BUYER" input field and a green "Watch" button are visible in the top bar
- A small status dot and label appear at the top-right (label reads "idle" before any watch)
- No blank screen, no error banner, no console errors

---

### UT-02 — SIM-BIDABS settles on "Bid Absorption" in amber (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → `TapeStatePanel`

**Preconditions:**
- Cockpit loaded at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650`
2. Click the "Ticker e.g. SIM-BUYER" field and type `SIM-BIDABS`
3. Click the green "Watch" button
4. Wait ~10–20s past warm-up (do NOT reload); watch the "Tape State" panel resolve

**Expected Result:**
- The "Tape State" panel headline reads exactly **Bid Absorption** (not "Seller Control", not "Unclear", not "Warming up")
- The headline text is amber (`text-amber-400`) and the confidence bar fill is amber (`bg-amber-500`)
- The "Confidence" value below the headline is a 3-decimal number at or above the reasonable-confidence threshold (clearly > 0)

---

### UT-03 — SIM-ASKABS settles on "Ask Absorption" in amber (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → `TapeStatePanel`

**Preconditions:**
- Cockpit loaded at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650`
2. Type `SIM-ASKABS` into the "Ticker e.g. SIM-BUYER" field
3. Click the green "Watch" button
4. Wait ~10–20s past warm-up (do NOT reload); watch the "Tape State" panel resolve

**Expected Result:**
- The "Tape State" panel headline reads exactly **Ask Absorption** (not "Buyer Control", not "Unclear")
- The headline text is amber and the confidence bar fill is amber
- The "Confidence" value is a 3-decimal number clearly above zero

---

### UT-04 — Features panel shows the three new absorption rows (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → `FeaturesPanel`

**Preconditions:**
- SIM-BIDABS has been watched and the Tape State has resolved (UT-02 done)

**Steps:**
1. With SIM-BIDABS resolved, locate the "Features" panel
2. Scroll/read the rows below the "Large prints" row

**Expected Result:**
- Three rows appear in this order below "Large prints": **Absorption score**, **Bid refresh score**, **Ask refresh score**
- Each value is a monospaced 3-decimal number in neutral slate (NOT green/red color-by-sign)
- "Bid refresh score" reads elevated (≈ 1.000)
- The nine existing rows above (Trade speed … Large prints) are still present and unchanged — twelve rows total

---

### UT-05 — Absorption message appears in the Event log (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → `EventLogPanel` / `ObservationsPanel`

**Preconditions:**
- SIM-BIDABS has been watched and the Tape State has resolved to Bid Absorption (UT-02 done)

**Steps:**
1. With SIM-BIDABS resolved, locate the "Event log" panel
2. Read the most recent log lines

**Expected Result:**
- A line reading "Tape state changed to bid_absorption" (or equivalent state-change line) is present
- An absorption-specific line is present, e.g. "Large sell print absorbed"
- A bid-refresh line with a real in-window price is present, e.g. "Bid refreshing at 100.00" (a concrete number, not "<price>" or a placeholder)

---

### UT-06 — Status dot turns "closed" when a bounded stream exhausts (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → `TopBar` status dot

**Preconditions:**
- Cockpit loaded; the watched scenario is a bounded sim stream (e.g. SIM-BIDABS)

**Steps:**
1. Navigate to `http://localhost:3650`, watch `SIM-BIDABS`
2. Observe the top-right dot transition from amber "connecting" to emerald "live"
3. Leave the page open (do NOT reload) until the bounded stream finishes
4. Observe the dot after the stream ends

**Expected Result:**
- During streaming, dot is emerald with label "live"
- After the stream exhausts, the dot turns rose with label "closed" — it does NOT remain a false "live"
- The label matches the `stream_status` field of `GET http://localhost:8000/tape/SIM-BIDABS/summary`

---

### UT-07 — SIM-BUYER stays "Buyer Control" with a stable live dot (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` → `TapeStatePanel` + `TopBar`

**Preconditions:**
- Cockpit loaded at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650`, type `SIM-BUYER`, click "Watch"
2. Wait past warm-up for the Tape State to resolve

**Expected Result:**
- Tape State headline reads "Buyer Control" in green — NOT "Ask Absorption", NOT amber
- The top-right dot stays emerald "live" while the stream is active (no false "closed"/"stale" flicker)
- All six cockpit panels render and update

---

### UT-08 — SIM-SELLER stays "Seller Control", not bid_absorption (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` → `TapeStatePanel`

**Preconditions:**
- Cockpit loaded at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650`, type `SIM-SELLER`, click "Watch"
2. Wait past warm-up for resolution

**Expected Result:**
- Tape State headline reads "Seller Control" in rose — NOT "Bid Absorption", NOT amber
- The dot stays emerald "live" during the active stream

---

### UT-09 — Unknown / no-data ticker stays honest (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` → `TopBar` + `TapeStatePanel`

**Preconditions:**
- Cockpit loaded at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650`, type `NOPE` into the Ticker field, click "Watch"
2. Observe the top bar
3. In a second check, watch `SIM-CHOP` (a known ticker that produces no data) and wait past warm-up

**Expected Result:**
- For `NOPE`: an error message appears in red below the top bar (rejected unknown ticker); no fabricated tape state
- For `SIM-CHOP`: the Tape State reads "Unclear" — NOT an absorption state, NOT fabricated; absorption is never claimed without real refresh evidence

---

### UT-10 — Empty / whitespace ticker does not start a watch (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` → `TopBar`

**Preconditions:**
- Cockpit loaded at http://localhost:3650

**Steps:**
1. Navigate to `http://localhost:3650`
2. Leave the "Ticker e.g. SIM-BUYER" field empty and click the green "Watch" button

**Expected Result:**
- No new watch starts and no cockpit panels populate with data; the dot does not move to "live"
- The page does not crash or show a blank screen (an error/no-op is acceptable; a crash is not)

---

### UT-11 — UI values equal REST values, no client recompute (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/` → `FeaturesPanel` / `TapeStatePanel`

**Preconditions:**
- SIM-BIDABS watched and resolved to Bid Absorption

**Steps:**
1. Read the on-screen "Bid refresh score" value and the Tape State / Confidence value
2. In a terminal, run `curl -s http://localhost:8000/tape/SIM-BIDABS/features` and `curl -s http://localhost:8000/tape/SIM-BIDABS/state`
3. Compare the on-screen numbers to the REST `bid_refresh_score`, `tape_state`, and `confidence`

**Expected Result:**
- On-screen "Bid refresh score" equals REST `bid_refresh_score`
- On-screen Tape State / Confidence equal REST `tape_state` / `confidence` (no divergence — single source of truth)

---

### UT-12 — Absorption read is discoverable and labels are clear (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/` → `TapeStatePanel` / `FeaturesPanel` / `EventLogPanel`

**Preconditions:**
- SIM-BIDABS watched and resolved

**Steps:**
1. As a first-time operator, look at the resolved SIM-BIDABS cockpit without prior knowledge
2. Judge whether the absorption read and its justifying numbers are self-explanatory

**Expected Result:**
- The amber "Bid Absorption" headline plus the elevated "Bid refresh score" / "Absorption score" rows and the plain-language event-log line ("Large sell print absorbed") together make the call understandable
- No raw enum strings (e.g. literal "bid_absorption") leak into the headline — the headline is the human label "Bid Absorption"

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit loads | smoke | P1 | `/` |
| UT-02 | SIM-BIDABS → Bid Absorption (amber) | happy-path | P1 | `TapeStatePanel` |
| UT-03 | SIM-ASKABS → Ask Absorption (amber) | happy-path | P1 | `TapeStatePanel` |
| UT-04 | Three new Features rows | happy-path | P1 | `FeaturesPanel` |
| UT-05 | Absorption message in Event log | happy-path | P1 | `EventLogPanel` |
| UT-06 | Dot turns "closed" on stream end | happy-path | P1 | `TopBar` |
| UT-07 | SIM-BUYER stays Buyer Control + live dot | regression | P1 | `TapeStatePanel`/`TopBar` |
| UT-08 | SIM-SELLER stays Seller Control | regression | P1 | `TapeStatePanel` |
| UT-09 | Unknown/no-data ticker stays honest | validation | P2 | `TopBar`/`TapeStatePanel` |
| UT-10 | Empty ticker no-op | validation | P2 | `TopBar` |
| UT-11 | UI ≡ REST values | regression | P2 | `FeaturesPanel`/`TapeStatePanel` |
| UT-12 | Absorption read discoverable | ux | P3 | cockpit |

**P1 tests must all pass for browser QA verdict to be PASS.**
