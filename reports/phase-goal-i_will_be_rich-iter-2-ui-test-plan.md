# Phase goal-i_will_be_rich-iter-2 — UI Test Plan

**Phase:** goal-i_will_be_rich-iter-2
**Date:** 2026-06-02
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

> **Iteration type: verification-closure (zero frontend code change).** No new route, panel, control,
> or displayed value was added. Every test below re-verifies an **existing iter-1 surface** that
> iter-1 SKIPPED (all 18 UI tests skipped on a cached HTTP 500). The goal is to *browser-prove with
> screenshots* that the `SIM-BUYER` cockpit works end-to-end (J-01 / J-02 / J-08) and that the two
> behavior-preserving backend cleanups caused no visible regression. API/test-suite checks
> (TC-01…TC-06, REST half of TC-10) live in the functional test plan and are **not duplicated here.**
>
> **Mandatory precondition gate (UT-01).** If `/` does not return HTTP 200 after the `.next` clear +
> dev-server restart, the entire browser run is **INVALID** — a SKIP must NOT be recorded as a pass.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Cockpit shell loads without the iter-1 HTTP 500 (smoke / precondition gate)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Backend running on the QA-harness offset port (e.g. `:8650`).
- `rm -rf apps/frontend/.next` was performed, then the managed frontend dev server (re)started with
  `NEXT_PUBLIC_API_URL` pointed at the running backend.
- Frontend running at http://localhost:3650.

**Steps:**
1. Navigate to `http://localhost:3650/`.
2. Wait for the page to fully load.

**Expected Result:**
- Page returns **HTTP 200** (not the iter-1 HTTP 500) and renders the cockpit shell.
- The top bar shows the bold title **"Tapeology"**, a ticker input with placeholder
  **"Ticker e.g. SIM-BUYER"**, and a green **"Watch"** button.
- Before watching, the center reads **"No ticker watched"** with the hint **"Try: SIM-BUYER"**.
- The footer reads **"Tapeology reads and classifies the live tape for a single ticker. Descriptive
  only — not trading advice."**
- No blank screen, no Next.js error overlay, no uncaught console errors.
- **If this fails (500 / unreachable / blank), STOP — the browser run is INVALID. Do not record SKIP as PASS.**

---

### UT-02 — Watch SIM-BUYER and the cockpit populates live (happy path / J-01)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → `TopBar` watch form + `Cockpit`

**Preconditions:**
- UT-01 passed (page serves 200).

**Steps:**
1. Navigate to `http://localhost:3650/`.
2. Click the ticker input (placeholder **"Ticker e.g. SIM-BUYER"**) and type `SIM-BUYER`.
3. Click the green **"Watch"** button.
4. Wait for the stream to connect (the **"Connecting to the tape stream…"** state may flash first).
5. Observe the six panels render: **Tape State**, **Quote**, **Features**, **Recent Trades**,
   **Observations**, **Event Log**.

**Expected Result:**
- The top bar shows **"Watching"** followed by `SIM-BUYER` in monospace.
- The **Quote** panel shows monospaced numbers for **Bid**, **Ask**, **Spread**, and **Last**
  (not "—" placeholders).
- The **Recent Trades** panel shows a table with **Price / Size / Side** columns and at least one row
  (no "No trades yet." after warm-up).
- The **Features** panel shows numeric readouts (not all "—").
- The **Event Log** panel shows at least one line (not "No events yet.").
- No crash, no blank panel.

---

### UT-03 — Values update over WebSocket without a page reload (happy path / J-01)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → `Cockpit` (live WS)

**Preconditions:**
- UT-02 done; `SIM-BUYER` is watched and panels are populated.

**Steps:**
1. With `SIM-BUYER` watched, note the current **Last** value in the Quote panel and the top row of
   the **Recent Trades** table.
2. Wait ~3–5 seconds. **Do NOT reload the page.**
3. Re-read the **Last** value and the **Recent Trades** top row.

**Expected Result:**
- At least one value changes on its own — e.g. **Last** updates, or a new row appears at the top of
  **Recent Trades** — with **no page reload** and no manual re-click of "Watch".
- The stream-status dot stays in its connected/live state during the update (does not flip to error).

---

### UT-04 — Spread equals ask − bid after the spread-producer cleanup (validation / J-01)

**Type:** validation
**Priority:** P1
**Surface:** `/` → `QuotePanel` + `FeaturesPanel`

**Preconditions:**
- UT-02 done; `SIM-BUYER` watched and Quote panel populated.

**Steps:**
1. In the **Quote** panel, read **Bid**, **Ask**, and **Spread**.
2. Compute `Ask − Bid` by hand.
3. In the **Features** panel, read **Average spread**.

**Expected Result:**
- The displayed **Spread** equals **Ask − Bid** within display rounding (e.g. Spread ≈ `0.02` when
  Ask ≈ `100.26` and Bid ≈ `100.24`).
- **Average spread** displays a small positive number (≈ `0.020`), consistent with the live spread —
  confirming the `tape_engine.py:54` single-producer cleanup is behavior-preserving (no jump,
  negative, or "—").

---

### UT-05 — Tape state settles on buyer_control with confidence bar (happy path / J-02)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → `TapeStatePanel`

**Preconditions:**
- UT-02 done; `SIM-BUYER` watched; allow the stream to stabilize (warm-up complete — the amber
  "Warming up — collecting tape data…" note has cleared).

**Steps:**
1. Let the stream run until the warm-up note disappears.
2. Read the large state label at the top of the **Tape State** panel.
3. Read the **Confidence** value (monospace, 3 decimals) and observe the confidence bar width.

**Expected Result:**
- The **Tape State** panel reads **buyer_control** (label "Buyer Control") in its accent color.
- **Confidence** reads a value ≥ the reasonable threshold (≈ **0.80**), and the confidence bar is
  filled to roughly that proportion (≈ 80% width), not empty or pinned at 0.

---

### UT-06 — Feature evidence supports buyer_control (validation / J-02)

**Type:** validation
**Priority:** P1
**Surface:** `/` → `FeaturesPanel`

**Preconditions:**
- UT-05 reached `buyer_control`.

**Steps:**
1. In the **Features** panel, read **Aggressive buy ratio**.
2. Read **Buy price impact**.

**Expected Result:**
- **Aggressive buy ratio** reads **high** (≈ `0.90`, between 0 and 1).
- **Buy price impact** reads **positive** (≈ `+0.41`) and is rendered in the positive/emerald color
  (sign-colored) — confirming the price-impact evidence behind buyer_control is intact (the guard
  was not relaxed).

---

### UT-07 — Event log records the buyer_control transition (happy path / J-02)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` → `EventLogPanel`

**Preconditions:**
- UT-05 reached `buyer_control`.

**Steps:**
1. In the **Event Log** panel, scan the entries (newest first).

**Expected Result:**
- The log contains the line **"Tape state changed to buyer_control"** (exact phrase).
- Entries are monospace and the list is non-empty (not "No events yet.").

---

### UT-08 — UI matches REST exactly for SIM-BUYER (happy path / J-08, single source of truth)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (UI panels) vs REST `/tape/SIM-BUYER/state` + `/tape/SIM-BUYER/features`

**Preconditions:**
- UT-05 reached `buyer_control`; cockpit still showing `SIM-BUYER`.

**Steps:**
1. Keep the cockpit tab open on `SIM-BUYER`.
2. In a second browser tab, open `http://localhost:<backend-port>/tape/SIM-BUYER/state`.
3. In a third tab (or same), open `http://localhost:<backend-port>/tape/SIM-BUYER/features`.
4. Compare, for the same moment: **tape_state** and **confidence** (from `/state`) against the
   Tape State panel; **aggressive_buy_ratio**, **buy_price_impact**, **average_spread** (from
   `/features`) against the Features panel.

**Expected Result:**
- **tape_state** in the JSON equals the UI's state label (`buyer_control`).
- **confidence** matches the UI's Confidence value within display rounding.
- Each compared feature value (aggressive_buy_ratio, buy_price_impact, average_spread) matches the
  UI's Features panel within display rounding.
- **No divergence** between the UI and REST for the same ticker — one engine value per metric.

---

### UT-09 — Idle state renders before any ticker is watched (regression / J-01)

**Type:** regression
**Priority:** P2
**Surface:** `/` → `IdleState`

**Preconditions:**
- Fresh page load with no ticker watched (open a new tab / hard-reload before watching).

**Steps:**
1. Navigate to `http://localhost:3650/`.
2. Do NOT type or click Watch.

**Expected Result:**
- The center reads **"No ticker watched"** with the ▦ glyph and the body text instructing to enter a
  ticker and click **Watch**.
- The hint **"Try: SIM-BUYER"** is visible.
- No panels are rendered and no error is shown.

---

### UT-10 — Bad ticker shows a watch-error, not a crash (error / J-01)

**Type:** error
**Priority:** P2
**Surface:** `/` → `TopBar` watch form + error banner

**Preconditions:**
- UT-01 passed; page on `/`.

**Steps:**
1. Navigate to `http://localhost:3650/`.
2. Type `NOPE_UNKNOWN` into the ticker input.
3. Click the green **"Watch"** button.

**Expected Result:**
- A rose/red error message appears under the top bar (e.g. an "unknown ticker" / 400 message).
- The app does **not** crash, the screen does **not** go blank, and no half-populated cockpit appears
  for the bad ticker.
- The user can still type a valid ticker afterward.

---

### UT-11 — Color semantics, monospace numerics, and "not trading advice" disclaimer intact (ux / regression)

**Type:** ux
**Priority:** P2
**Surface:** `/` → global (TopBar dot, panels, footer)

**Preconditions:**
- UT-02 done; `SIM-BUYER` watched and live.

**Steps:**
1. Observe the stream-status dot at the top-right of the top bar and its text label.
2. Observe the **Recent Trades** Side column colors and the **Buy price impact** color.
3. Scroll to the footer.

**Expected Result:**
- The stream-status dot is **emerald** (live) with the label "Live" once warmed (not the slate "idle"
  or rose "closed" dot).
- Buy-side trades / positive impacts render emerald; sell-side / negative render rose; numeric
  readouts are monospaced.
- The footer disclaimer **"Descriptive only — not trading advice."** is present (no regression, no
  profit/advice language anywhere).

---

### UT-12 — No new route, panel, or control was introduced (regression / scope guard)

**Type:** regression
**Priority:** P2
**Surface:** `/` (whole page)

**Preconditions:**
- UT-02 done; `SIM-BUYER` watched.

**Steps:**
1. Scan the entire cockpit for any new navigation item, route link, panel, button, or input beyond
   iter-1's set (top bar: Ticker input + Watch button + status dot; six panels; footer disclaimer).

**Expected Result:**
- Exactly the iter-1 surfaces exist — **six panels** (Tape State, Quote, Features, Recent Trades,
  Observations, Event Log), one watch form, one status dot, one footer.
- **No new** page, route, panel, control, label, or displayed value was added (this is a
  verification-closure iteration with zero frontend code change).

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Shell loads (no HTTP 500) — precondition gate | smoke | P1 | `/` |
| UT-02 | Watch SIM-BUYER → cockpit populates | happy-path | P1 | `/` TopBar + Cockpit |
| UT-03 | Live WS updates without reload | happy-path | P1 | `/` Cockpit |
| UT-04 | Spread = ask − bid after cleanup | validation | P1 | `/` Quote + Features |
| UT-05 | Tape state settles on buyer_control | happy-path | P1 | `/` TapeStatePanel |
| UT-06 | Feature evidence supports buyer_control | validation | P1 | `/` FeaturesPanel |
| UT-07 | Event log records the transition | happy-path | P1 | `/` EventLogPanel |
| UT-08 | UI matches REST exactly (J-08) | happy-path | P1 | `/` vs REST |
| UT-09 | Idle state renders pre-watch | regression | P2 | `/` IdleState |
| UT-10 | Bad ticker → watch-error, no crash | error | P2 | `/` TopBar |
| UT-11 | Colors, monospace, disclaimer intact | ux | P2 | `/` global |
| UT-12 | No new route/panel/control (scope guard) | regression | P2 | `/` |

**P1 tests (UT-01 … UT-08) must all pass — and each of UT-02, UT-05, UT-08 must produce an end-state
screenshot (not a failure shot) — for the browser QA verdict to be PASS.** UT-01 is the mandatory
precondition gate: if it fails, the browser run is INVALID and a SKIP must not be recorded as a pass.
