# Phase N — UI Test Plan

**Phase:** goal-i_will_be_rich-iter-6
**Date:** 2026-06-03
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Scope note

No frontend code changed this iteration. All test cases below exercise **existing** components on
the single `/` cockpit route whose **displayed data now changes** because `SIM-CHOP` streams a
driven choppy tape (previously it emitted zero events). The headline new capability is: watching
`SIM-CHOP` produces a warmed, honest **"Unclear"** read. The regression cases guard the four
already-resolving states and the single-source-of-truth equality (J-08).

There is **no form** beyond the single ticker input, so classic field-by-field validation is
replaced by ticker-input handling tests (unknown ticker error surface).

---

## Test Cases

<!-- UT-XX prefix distinguishes from functional test plan TC-XX IDs. -->

---

### UT-01 — Cockpit loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running and reachable
- User is not required to log in (no auth)

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen or error overlay
- The "Tapeology" wordmark is visible in the top-left of the header
- A ticker input with placeholder text "Ticker e.g. SIM-BUYER" and a green "Watch" button are visible in the header
- Below the header an idle state is shown (no panels populated yet because nothing is watched)
- No uncaught errors appear in the browser console

---

### UT-02 — Watching SIM-CHOP warms to an "Unclear" read (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (Tape State panel)

**Preconditions:**
- Cockpit loaded at http://localhost:3650/
- Backend running

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Click into the ticker input (placeholder "Ticker e.g. SIM-BUYER") in the header
3. Type `SIM-CHOP` into the ticker input
4. Click the green "Watch" button (or press Enter)
5. Wait up to ~10 seconds for the stream to warm up

**Expected Result:**
- The header shows "Watching" followed by `SIM-CHOP` in monospace
- The "Tape State" panel headline reads **"Unclear"**
- The "Tape State" panel "Confidence" value reads **0.200** (monospace), not 0.100
- The "Warming up — collecting tape data…" amber hint is **no longer shown** once warmed (it may flash briefly at cold start)
- The connection dot in the top-right reads "live" (emerald) while the stream is active
- No error text appears under the header

---

### UT-03 — "Unclear" headline and confidence bar render in amber (happy path / visual)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (Tape State panel)

**Preconditions:**
- `SIM-CHOP` is being watched (complete UT-02 first)

**Steps:**
1. With `SIM-CHOP` watched, locate the "Tape State" panel
2. Inspect the "Unclear" headline element's color
3. Inspect the confidence bar fill color

**Expected Result:**
- The "Unclear" headline uses the amber text class (`text-amber-400`) — verify via a **base-selector probe** (`.text-amber-400{`, excluding `:hover`/variant forms) plus `getComputedStyle`, not by eyeballing or grep substring
- The confidence bar fill uses the amber background class (`bg-amber-500`) — verify the same way
- The bar fill width corresponds to ~20% (confidence 0.20), i.e. a short bar, not full

---

### UT-04 — Cockpit makes no decisive / absorption call on SIM-CHOP (happy path / honesty)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (Tape State + Observations panels)

**Preconditions:**
- `SIM-CHOP` is being watched (complete UT-02 first)

**Steps:**
1. With `SIM-CHOP` watched, read the "Tape State" panel headline
2. Read the "Observations" panel content

**Expected Result:**
- The headline reads **"Unclear"** — it does **NOT** read "Buyer Control", "Seller Control", "Bid Absorption", or "Ask Absorption" anywhere on the page
- The "Observations" panel shows an honest non-call rationale such as "Mixed or weak evidence — no clear side in control"
- No emerald (buyer) or rose (seller) decisive headline appears

---

### UT-05 — Features panel shows genuine non-decisive readouts on SIM-CHOP (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (Features panel)

**Preconditions:**
- `SIM-CHOP` is being watched (complete UT-02 first)

**Steps:**
1. With `SIM-CHOP` watched, locate the "Features" panel
2. Read the `aggressive_buy_ratio` and `aggressive_sell_ratio` values
3. Read the `average_spread` value
4. Read the `buy_price_impact` and `sell_price_impact` values

**Expected Result:**
- `aggressive_buy_ratio` displays **< 0.60** (≈ 0.50)
- `aggressive_sell_ratio` displays **< 0.60** (≈ 0.50)
- `average_spread` displays **> 0.06** (a wide spread)
- `buy_price_impact` displays **0.0**
- `sell_price_impact` displays **0.0**
- Numeric values are monospaced

---

### UT-06 — Quote panel shows a wide, jittery spread on SIM-CHOP (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/` (Quote panel)

**Preconditions:**
- `SIM-CHOP` is being watched (complete UT-02 first)

**Steps:**
1. With `SIM-CHOP` watched, locate the "Quote" panel
2. Observe the displayed spread value
3. Observe the bid/ask near side across two or more live updates

**Expected Result:**
- The displayed spread is wide (> 0.06)
- The quote's near side visibly jitters (changes) across successive live updates
- Numeric values are monospaced

---

### UT-07 — Recent Trades panel shows constant-price chop prints (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/` (Recent Trades panel)

**Preconditions:**
- `SIM-CHOP` is being watched (complete UT-02 first)

**Steps:**
1. With `SIM-CHOP` watched, locate the "Recent Trades" panel
2. Read the trade price column for several recent trades
3. Read the side column for several recent trades

**Expected Result:**
- Every trade price reads exactly **100.00** (the "no price progress" signal)
- Trade sides are mixed (a combination of buy / sell / unknown across the list)

---

### UT-08 — Top-bar scenario indicator reads `unclear_chop` (happy path / discoverability)

**Type:** happy-path
**Priority:** P2
**Surface:** `/` (Top-bar scenario indicator)

**Preconditions:**
- `SIM-CHOP` is being watched (complete UT-02 first)

**Steps:**
1. With `SIM-CHOP` watched, look at the header to the right of the "Watching SIM-CHOP" label

**Expected Result:**
- A small badge reads `scenario:` followed by `unclear_chop` in monospace

---

### UT-09 — SIM-CHOP read streams live over WebSocket without reload (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (live WebSocket stream, all panels)

**Preconditions:**
- Cockpit loaded at http://localhost:3650/, backend running

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Type `SIM-CHOP` into the ticker input and click "Watch"
3. Do **NOT** reload the page
4. Watch the panels for ~10 seconds

**Expected Result:**
- The "Tape State" headline transitions from cold start to a warmed **"Unclear"** at confidence **0.200** without any page reload
- The Quote, Features, and Recent Trades panels update in real time (values change) without a reload
- The connection dot reads "live"

---

### UT-10 — No spurious transition line appears for SIM-CHOP (happy path / honesty)

**Type:** happy-path
**Priority:** P2
**Surface:** `/` (Event-log panel, negative case)

**Preconditions:**
- `SIM-CHOP` is being watched (complete UT-02 first)

**Steps:**
1. With `SIM-CHOP` watched, locate the "Event Log" panel
2. Read every line in the event log

**Expected Result:**
- **No** line reading "Tape state changed to …" appears for `SIM-CHOP`
- (Cold-start unclear → warmed unclear is not a state change; the honest absence of a transition line is correct, not a bug)

---

### UT-11 — Unknown ticker shows an explicit error, not a fabricated read (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` (ticker input + header error line)

**Preconditions:**
- Cockpit loaded at http://localhost:3650/

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Type `NOPE-XYZ` into the ticker input
3. Click the "Watch" button

**Expected Result:**
- A rose-colored error line appears under the header containing the text `'NOPE-XYZ' could not be watched` (or the backend-returned error message)
- No panels populate; the cockpit does **not** fabricate a tape state for the unknown ticker

---

### UT-12 — Live cold-start transition appears for SIM-BUYER (regression, J-07)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Event-log panel)

**Preconditions:**
- **Fresh backend** (restarted, no prior watch this session)
- Cockpit loaded at http://localhost:3650/

**Steps:**
1. Restart the backend so no ticker has been watched yet
2. Navigate to `http://localhost:3650/`
3. Type `SIM-BUYER` into the ticker input and click "Watch" (this is the first watch)
4. Do **NOT** reload; watch the "Event Log" panel for ~10 seconds

**Expected Result:**
- A line reading **"Tape state changed to buyer_control"** appears **live** in the Event Log (no reload)
- The "Tape State" headline reads "Buyer Control" in emerald

---

### UT-13 — Live cold-start transition appears for SIM-SELLER (regression, J-07)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Event-log panel)

**Preconditions:**
- **Fresh backend** (restarted, no prior watch this session)
- Cockpit loaded at http://localhost:3650/

**Steps:**
1. Restart the backend so no ticker has been watched yet
2. Navigate to `http://localhost:3650/`
3. Type `SIM-SELLER` into the ticker input and click "Watch" (first watch)
4. Do **NOT** reload; watch the "Event Log" panel for ~10 seconds

**Expected Result:**
- A line reading **"Tape state changed to seller_control"** appears **live** in the Event Log
- The "Tape State" headline reads "Seller Control" in rose
- (Together with UT-12 this confirms ≥2 distinct live transitions from cold start)

---

### UT-14 — SIM-BUYER still reads Buyer Control / emerald (regression, J-01/J-02)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Tape State + all six panels)

**Preconditions:**
- Cockpit loaded at http://localhost:3650/, backend running

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Type `SIM-BUYER` into the ticker input and click "Watch"
3. Wait for warm-up (~10s)

**Expected Result:**
- The "Tape State" headline reads **"Buyer Control"** in emerald (`text-emerald-400`)
- All six panels (Tape State, Quote, Features, Observations, Event Log, Recent Trades) are populated and updating live

---

### UT-15 — SIM-SELLER still reads Seller Control / rose (regression, J-03)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Tape State panel)

**Preconditions:**
- Cockpit loaded at http://localhost:3650/, backend running

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Type `SIM-SELLER` into the ticker input and click "Watch"
3. Wait for warm-up (~10s)

**Expected Result:**
- The "Tape State" headline reads **"Seller Control"** in rose

---

### UT-16 — SIM-BIDABS still reads Bid Absorption / amber (regression, J-04)

**Type:** regression
**Priority:** P2
**Surface:** `/` (Tape State panel)

**Preconditions:**
- Cockpit loaded at http://localhost:3650/, backend running

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Type `SIM-BIDABS` into the ticker input and click "Watch"
3. Wait for warm-up (~10s)

**Expected Result:**
- The "Tape State" headline reads **"Bid Absorption"** in amber

---

### UT-17 — SIM-ASKABS still reads Ask Absorption / amber (regression, J-05)

**Type:** regression
**Priority:** P2
**Surface:** `/` (Tape State panel)

**Preconditions:**
- Cockpit loaded at http://localhost:3650/, backend running

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Type `SIM-ASKABS` into the ticker input and click "Watch"
3. Wait for warm-up (~10s)

**Expected Result:**
- The "Tape State" headline reads **"Ask Absorption"** in amber

---

### UT-18 — UI read for SIM-CHOP equals backend single source of truth (regression, J-08)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Tape State + Features panels vs backend API)

**Preconditions:**
- `SIM-CHOP` is being watched (complete UT-02 first)

**Steps:**
1. With `SIM-CHOP` watched and warmed, read the UI "Tape State" headline + Confidence value and the "Features" panel readouts
2. In a separate tab or via curl, request `GET /tape/SIM-CHOP/state` and `GET /tape/SIM-CHOP/features` from the backend
3. Compare the UI values against the API response

**Expected Result:**
- The UI state (`unclear`) and confidence (0.200) **exactly match** `GET /tape/SIM-CHOP/state`
- The UI feature readouts **exactly match** `GET /tape/SIM-CHOP/features` (within display rounding)
- No value is recomputed client-side — the UI mirrors the backend

---

### UT-19 — Five-state taxonomy is observable on one cockpit (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` (Tape State panel across tickers)

**Preconditions:**
- Cockpit loaded at http://localhost:3650/, backend running

**Steps:**
1. In sequence, watch `SIM-BUYER`, then `SIM-SELLER`, then `SIM-BIDABS`, then `SIM-ASKABS`, then `SIM-CHOP` (type each into the input and click "Watch")
2. After each, note the "Tape State" headline

**Expected Result:**
- The five headlines observed are: "Buyer Control", "Seller Control", "Bid Absorption", "Ask Absorption", and "Unclear" — the complete five-state taxonomy is reachable through the existing ticker input, including the honest non-call on `SIM-CHOP`

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit loads | smoke | P1 | `/` |
| UT-02 | SIM-CHOP warms to Unclear | happy-path | P1 | `/` Tape State |
| UT-03 | Unclear renders amber | happy-path | P1 | `/` Tape State |
| UT-04 | No decisive/absorption call | happy-path | P1 | `/` Tape State + Observations |
| UT-05 | Features non-decisive readouts | happy-path | P1 | `/` Features |
| UT-06 | Quote wide/jittery | happy-path | P2 | `/` Quote |
| UT-07 | Recent Trades constant price | happy-path | P2 | `/` Recent Trades |
| UT-08 | Scenario reads unclear_chop | happy-path | P2 | `/` Top bar |
| UT-09 | Live stream no reload | happy-path | P1 | `/` WebSocket |
| UT-10 | No spurious transition line | happy-path | P2 | `/` Event Log |
| UT-11 | Unknown ticker error | validation | P2 | `/` input |
| UT-12 | Live transition SIM-BUYER | regression | P1 | `/` Event Log |
| UT-13 | Live transition SIM-SELLER | regression | P1 | `/` Event Log |
| UT-14 | SIM-BUYER buyer_control/emerald | regression | P1 | `/` Tape State |
| UT-15 | SIM-SELLER seller_control/rose | regression | P1 | `/` Tape State |
| UT-16 | SIM-BIDABS bid_absorption/amber | regression | P2 | `/` Tape State |
| UT-17 | SIM-ASKABS ask_absorption/amber | regression | P2 | `/` Tape State |
| UT-18 | UI == backend (J-08) | regression | P1 | `/` vs API |
| UT-19 | Five-state taxonomy observable | ux | P2 | `/` Tape State |

**P1 tests must all pass for browser QA verdict to be PASS.**
