# Phase goal-i_will_be_rich-iter-4 — UI Test Plan

**Phase:** goal-i_will_be_rich-iter-4
**Date:** 2026-06-03
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

> This iteration adds **0 frontend code edits**. All UI changes are *content*: the backend now
> emits `seller_control` for `SIM-SELLER`, and the existing already-generic, rose-ready cockpit
> components render it. There is one route (`/`) and no navigation. Tests below verify the new
> seller read renders correctly, that the buyer read did not regress, and that the no-fabrication
> error path still holds. API/pytest coverage lives in the functional test plan
> (`reports/qa/goal-i_will_be_rich-iter-4-test-plan.md`) and is NOT duplicated here.

**Exact-label reference (from source, so steps are unambiguous):**
- Ticker field: `<input aria-label="Ticker">`, placeholder text `Ticker e.g. SIM-BUYER` (top-left header, next to the **Watch** button).
- Watch button: green button labelled **Watch**.
- Tape State panel: header **Tape State**; large headline shows **Seller Control** / **Buyer Control** / **Unclear**; below it the line `Confidence 0.xxx` (3 decimals); then a thin horizontal confidence bar.
- Features panel: header **Features**; rows include **Aggressive sell ratio**, **Sell price impact**, **Aggressive buy ratio**, **Buy price impact** (each row shows a value to 3 decimals).
- Observations panel: header **Observations** (bulleted list; empty shows "No observations yet.").
- Event Log panel: header **Event Log**; **newest entry first**; empty shows "No events yet.".
- Error surface: rose-colored text line directly under the header bar.
- Connection dot + status word (top-right): `idle` (grey) → `connecting` (amber, pulsing) → `live` (green) → `closed` (red).

**Color RGB reference (for `getComputedStyle` assertions):**
- Rose headline `text-rose-400` = `rgb(251, 113, 133)`
- Rose bar fill `bg-rose-500` = `rgb(244, 63, 94)`
- Rose cell `text-rose-400` (negative impact) = `rgb(251, 113, 133)`
- Buyer green headline `text-emerald-400` = `rgb(74, 222, 128)`
- Buyer green bar fill `bg-emerald-500` = `rgb(16, 185, 129)`
- Warm-up / unclear amber `text-amber-400` = `rgb(251, 191, 36)`

---

## Test Cases

<!-- UT-XX IDs distinguish these from the functional plan's TC-XX. -->

---

### UT-01 — Cockpit page loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650; backend up.
- No ticker watched yet (fresh load).

**Steps:**
1. Navigate to `http://localhost:3650/`.
2. Wait for the page to fully load.

**Expected Result:**
- The header shows the title **Tapeology**, a ticker input with placeholder **Ticker e.g. SIM-BUYER**, and a green **Watch** button.
- The top-right connection indicator shows the word **idle** next to a grey dot.
- No blank screen, no error overlay, no red error text under the header.
- Browser console shows no uncaught errors.

---

### UT-02 — Watch SIM-SELLER resolves to Seller Control (happy path — primary J-03 gate)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `TapeStatePanel`, `FeaturesPanel`, `ObservationsPanel`, `EventLogPanel`

**Preconditions:**
- Fresh load of `http://localhost:3650/`.
- Backend `SIM-SELLER` provider wired (this iteration).

**Steps:**
1. Navigate to `http://localhost:3650/`.
2. Click the ticker input (placeholder **Ticker e.g. SIM-BUYER**) and type `SIM-SELLER`.
3. Click the **Watch** button.
4. Observe the top-right status word transition `connecting` → `live`.
5. Wait up to ~6 seconds for the warm-up to resolve (the amber "Warming up — collecting tape data…" line under the confidence bar disappears).

**Expected Result:**
- The **Tape State** headline reads **Seller Control** (NOT "Unclear", NOT "Buyer Control").
- The **Confidence** line shows a value **≥ 0.600** (3 decimals).
- The confidence bar is filled (non-zero width).
- The **Features** panel shows **Aggressive sell ratio** ≥ 0.600 and **Sell price impact** as a **negative** number (e.g. `-0.0xx`).
- The **Observations** panel lists three bullets: **Seller aggression increasing**, **Price falling on sell prints**, **Spread stable and narrow**.
- The **Event Log** panel (newest first) contains the line **Tape state changed to seller_control**.

---

### UT-03 — Seller Control renders in rose, not green or amber (happy path — measured color)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `TapeStatePanel` headline + confidence bar fill, `FeaturesPanel` sell-impact cell

**Preconditions:**
- UT-02 completed in this tab; headline reads **Seller Control**.

**Steps:**
1. Open the browser devtools console.
2. Run, on the headline element:
   `getComputedStyle(document.querySelector('.text-2xl.font-bold')).color`
3. Run, on the confidence bar fill (the inner filled div inside the Tape State panel's bar):
   `getComputedStyle(document.querySelector('.h-2.rounded.bg-rose-500, .h-2.rounded')).backgroundColor`
   (select the inner bar `div` with an inline `width` style under the "Tape State" panel).
4. Locate the **Sell price impact** row in the Features panel and read its text color.

**Expected Result:**
- Headline `color` computes to **`rgb(251, 113, 133)`** (rose) — explicitly NOT emerald `rgb(74, 222, 128)` and NOT amber `rgb(251, 191, 36)`.
- Confidence-bar fill `backgroundColor` computes to **`rgb(244, 63, 94)`** (rose) — NOT emerald `rgb(16, 185, 129)` and NOT amber.
- The **Sell price impact** negative value renders rose `rgb(251, 113, 133)` (colored by sign via `impactColor`).

---

### UT-04 — Live WebSocket update without page reload (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `Cockpit` live WS stream

**Preconditions:**
- Fresh load of `http://localhost:3650/`.

**Steps:**
1. Navigate to `http://localhost:3650/`.
2. Type `SIM-SELLER` into the ticker input and click **Watch**.
3. Without refreshing, watch the **Confidence** value and the confidence bar for ~6 seconds during warm-up.
4. Do NOT press F5 / reload at any point.

**Expected Result:**
- The **Confidence** number and bar width change/climb on their own as the rolling window fills, with no page reload.
- The status word stays **live** (green dot) throughout.
- New lines appear in the **Event Log** over time (e.g. the `seller_control` transition line appears mid-stream, not only after a manual reload).

---

### UT-05 — SIM-BUYER still resolves to Buyer Control in green (regression — J-01/J-02)

**Type:** regression
**Priority:** P1
**Surface:** `/` — `TapeStatePanel`, `FeaturesPanel`

**Preconditions:**
- Fresh load of `http://localhost:3650/` (reload the tab to clear the prior SIM-SELLER watch).

**Steps:**
1. Navigate to `http://localhost:3650/`.
2. Type `SIM-BUYER` into the ticker input and click **Watch**.
3. Wait up to ~6 seconds for warm-up to resolve.
4. In the console run:
   `getComputedStyle(document.querySelector('.text-2xl.font-bold')).color`

**Expected Result:**
- The **Tape State** headline reads **Buyer Control** at **Confidence ≥ 0.600**.
- The **Features** panel shows **Aggressive buy ratio** high and **Buy price impact** as a **positive** number.
- The **Event Log** contains **Tape state changed to buyer_control**.
- Headline `color` computes to **`rgb(74, 222, 128)`** (emerald green) — NOT rose, NOT amber. The new seller branch did not perturb the buyer read.

---

### UT-06 — Unknown ticker is rejected with a visible error, no fabricated snapshot (error)

**Type:** error
**Priority:** P2
**Surface:** `/` — `TopBar` error surface

**Preconditions:**
- Fresh load of `http://localhost:3650/`.

**Steps:**
1. Navigate to `http://localhost:3650/`.
2. Type `NOPE123` into the ticker input and click **Watch**.
3. Wait ~2 seconds.

**Expected Result:**
- A rose-colored error line appears directly under the header (the UI surfaces the `400` from `POST /watch/NOPE123`).
- The **Tape State** panel does NOT render a fabricated state — it shows no "Seller Control"/"Buyer Control" read for `NOPE123` (no synthesized confidence/features/observations).
- The app does not crash; the page remains usable (you can type another ticker).

---

### UT-07 — Heavy selling with no price drop stays Unclear (validation — keystone anti-goal, observational)

**Type:** validation
**Priority:** P2
**Surface:** `/` — `TapeStatePanel`

**Preconditions:**
- Reserved sims that are intentionally still silent exist (`SIM-BIDABS`, `SIM-ASKABS`, `SIM-CHOP`).
- This is the UI-visible proxy for "aggression without price progress ≠ control"; the precise guard is covered by API tests TC-02/TC-03.

**Steps:**
1. Navigate to `http://localhost:3650/`.
2. Type `SIM-BIDABS` into the ticker input and click **Watch**.
3. Wait ~6 seconds.

**Expected Result:**
- The ticker is accepted (no error line — Watch returns 200), but the **Tape State** headline does NOT read **Seller Control**; it stays **Unclear** (amber) / warming up.
- No "Tape state changed to seller_control" line ever appears for this ticker.
- Confirms the product only declares "Seller Control" when price is actually being pushed down — it does not over-fire on a non-seller stream.

---

### UT-08 — Ticker input accepts both SIM tickers and is discoverable (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/` — `TopBar` ticker input + Watch button

**Preconditions:**
- Fresh load of `http://localhost:3650/`.

**Steps:**
1. Navigate to `http://localhost:3650/`.
2. Confirm the ticker input with placeholder **Ticker e.g. SIM-BUYER** is visible in the header without scrolling.
3. Type `SIM-SELLER`, click **Watch**, and confirm the **Watching SIM-SELLER** indicator appears in the header.
4. Reload, type `SIM-BUYER`, click **Watch**, confirm **Watching SIM-BUYER** appears.

**Expected Result:**
- The single ticker input is the obvious entry point — reachable in 0 clicks from `/` (it is always visible in the header).
- The header shows **Watching** followed by the watched ticker for each.
- Free-text entry accepts both `SIM-SELLER` and `SIM-BUYER`; no separate menu or navigation is required to switch tickers.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit loads | smoke | P1 | `/` |
| UT-02 | SIM-SELLER → Seller Control read | happy-path | P1 | `/` |
| UT-03 | Seller Control renders rose (measured) | happy-path | P1 | `/` |
| UT-04 | Live WS update, no reload | happy-path | P1 | `/` |
| UT-05 | SIM-BUYER still Buyer Control (green) | regression | P1 | `/` |
| UT-06 | Unknown ticker error, no fabrication | error | P2 | `/` |
| UT-07 | Silent sim stays Unclear (no over-fire) | validation | P2 | `/` |
| UT-08 | Ticker input discoverable / accepts both | ux | P3 | `/` |

**P1 tests (UT-01–UT-05) must all pass for the browser QA verdict to be PASS.**
**Primary J-03 gate:** UT-02 + UT-03 (Seller Control read + measured rose color).
**Regression guard:** UT-05 (buyer read unchanged).
**Anti-goal coverage (UI-visible):** UT-06 (no fabricated snapshot), UT-07 (no over-firing without price progress).
