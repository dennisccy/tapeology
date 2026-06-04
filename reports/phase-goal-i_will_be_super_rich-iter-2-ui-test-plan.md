# Phase goal-i_will_be_super_rich-iter-2 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-2
**Date:** 2026-06-04
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

## Scope

All affected surfaces live on the single route `/` (Watch — HOME). No new page or route was added.
This iteration adds: a debounced **symbol-search** box in Live/Historical mode (J-13), a **real-data
Historical replay** that feeds the existing cockpit (J-11), and three **distinct honest non-cockpit
panels** keyed off the failure reason (J-14). Simulated mode is unchanged.

> **Environment note on real data.** A successful Historical replay (UT-06/UT-07) and live symbol
> suggestions (UT-02/UT-03) require the backend to have Alpaca credentials configured **or** a
> fixture-backed historical path reachable. Where the QA environment cannot reach the vendor, the
> dropdown stays empty and Historical watches return `provider_unavailable`. Those tests are marked
> **operator-gated** — record SKIPPED-not-reachable, do **not** FAIL on that basis. The free-text
> fallback (UT-04), the no-creds honest panel (UT-10), Simulated regression (UT-12/UT-13), and all
> smoke/UX cases run regardless of credentials.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Home page loads with default Simulated mode (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running at http://localhost:8000

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Wait for the page to fully load

**Expected Result:**
- The "Tapeology" wordmark is visible in the top-left of the header
- A 3-way segmented control with buttons "Live", "Historical", and "Simulated" is visible; "Simulated" is the active (highlighted) button
- A symbol input with placeholder text "Ticker e.g. SIM-BUYER" is visible
- A green "Watch" button is visible
- The main area shows the idle state: a heading "No ticker watched" with the helper text starting "Enter a ticker above and click Watch…"
- No blank screen, no error banner, no console errors

---

### UT-02 — Symbol search dropdown shows real matches in Historical mode (happy path)

**Type:** happy-path
**Priority:** P1 (operator-gated: requires backend symbol-search returning matches)
**Surface:** `/` — `SymbolSearch`

**Preconditions:**
- Backend reachable with credentials so `GET /symbols/search?q=AAP` returns matches
- On `http://localhost:3650/`

**Steps:**
1. Click the "Historical" button in the data-source segmented control
2. Click into the symbol input (placeholder now reads "Symbol e.g. AAPL")
3. Type `AAP` into the symbol input
4. Wait ~¼ second (debounce) without typing further

**Expected Result:**
- A dropdown list appears directly below the symbol input
- Each row shows a monospaced ticker on the left (e.g. `AAPL`) and a lighter company name on the right (e.g. `Apple Inc`)
- The rows are real matches for `AAP` (ticker contains/starts with the typed query)
- No cockpit and no error banner appear

---

### UT-03 — Selecting a suggestion fills the symbol box and closes the dropdown (happy path)

**Type:** happy-path
**Priority:** P1 (operator-gated: requires search matches)
**Surface:** `/` — `SymbolSearch` dropdown row

**Preconditions:**
- UT-02 dropdown is showing matches for `AAP` in Historical mode

**Steps:**
1. With the `AAP` dropdown open, click the row whose ticker reads `AAPL`

**Expected Result:**
- The symbol input is filled with `AAPL`
- The dropdown closes immediately (no list visible below the input)
- No watch starts yet (cockpit is not shown; idle "No ticker watched" still in main area)

---

### UT-04 — Free-text symbol Watch works without using the dropdown (happy path / fallback)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `SymbolSearch` free-text fallback

**Preconditions:**
- On `http://localhost:3650/`, Historical mode selected
- A valid past UTC window and speed will be supplied (see UT-06 for window values); for a pure
  free-text-acceptance check, any window is acceptable

**Steps:**
1. Click "Historical"
2. Type `F` directly into the symbol input
3. Do NOT click any dropdown row (ignore or dismiss the dropdown)
4. Fill the "Date" field, the "Start time" field, and the "End time" field, and leave "Replay speed" at `1×`
5. Click the green "Watch" button

**Expected Result:**
- The Watch request is submitted for symbol `F` (the typed free text), not blocked by the dropdown
- One of: the cockpit populates (if the window has real data), OR a distinct honest amber panel appears (UT-08/UT-09/UT-10) — never a silent no-op
- The header shows "Watching" followed by `F` once a watch succeeds

---

### UT-05 — Short / cleared query shows no dropdown, no stale rows (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` — `SymbolSearch` empty/short query

**Preconditions:**
- On `http://localhost:3650/`, Historical mode selected

**Steps:**
1. Type `AAP` into the symbol input and wait for the dropdown to appear (operator-gated; if no
   matches in this env, skip to step 2 and verify empty-state only)
2. Select all text in the symbol input and delete it so the field is empty
3. Observe the area directly below the input

**Expected Result:**
- When the field is empty, NO dropdown is shown (no stale rows from the previous query)
- Typing a query that returns nothing leaves no dropdown rows visible (no leftover suggestions)

---

### UT-06 — Historical watch populates the full cockpit with real values (happy path)

**Type:** happy-path
**Priority:** P1 (operator-gated: requires real/fixture-backed historical data)
**Surface:** `/` — `Cockpit` (Historical watch)

**Preconditions:**
- Backend reachable for a known-good historical window for symbol `F` (a regular-market-hours
  past UTC window known to contain trades)
- On `http://localhost:3650/`

**Steps:**
1. Click "Historical"
2. Type `F` into the symbol input
3. Set "Date" to the known-good past date
4. Set "Start time" and "End time" to the known-good window
5. Choose `10×` in the "Replay speed" dropdown
6. Click "Watch"
7. Wait for the cockpit to fill (a few seconds at 10×)

**Expected Result:**
- The cockpit renders with **real** values: a bid, ask, spread, and last price (all non-empty/non-zero)
- A "recent trades" list shows rows with price, size, and side
- The feature readouts populate (non-empty)
- A tape state with a confidence value is shown
- An observations section and an event log populate
- No amber honest panel and no error banner appear alongside the cockpit

---

### UT-07 — Source label reads `historical <SYM> <window>` after a historical watch (happy path)

**Type:** happy-path
**Priority:** P2 (operator-gated: depends on UT-06 succeeding)
**Surface:** `/` — `TopBar` scenario chip

**Preconditions:**
- A historical watch for `F` succeeded (UT-06)

**Steps:**
1. After the cockpit fills, look at the header chip that begins with "scenario:"

**Expected Result:**
- The chip reads `scenario:` followed by a monospaced string beginning `historical F` and including the window (e.g. `historical F …`)
- The string comes from the engine snapshot (it matches the `scenario` field of `GET /tape/F/state`) — not a fabricated client value

---

### UT-08 — Untradable symbol shows the "Symbol not tradable" honest panel (error)

**Type:** error
**Priority:** P1 (operator-gated: requires creds OR DI fake returning not-tradable)
**Surface:** `/` — `ProviderUnavailable` `symbol_not_tradable`

**Preconditions:**
- Backend reachable and able to classify a bogus symbol as not tradable
- On `http://localhost:3650/`, Historical mode

**Steps:**
1. Click "Historical"
2. Type `ZZZZNOPE` into the symbol input
3. Fill "Date", "Start time", "End time" with any valid past window; leave speed at `1×`
4. Click "Watch"

**Expected Result:**
- An amber-bordered panel titled "Symbol not tradable" appears in the main area, in place of the cockpit
- The panel shows a ⚠ icon and the emphasized phrase "not a tradable symbol"
- Helper text explains the symbol isn't a tradable US equity and that no tape is fabricated
- NO cockpit panels (bid/ask, trades, event log) are visible
- The header does NOT show "Watching ZZZZNOPE" (no engine was created)

---

### UT-09 — Empty window shows the "No data for that window" honest panel (error)

**Type:** error
**Priority:** P1 (operator-gated: requires creds OR DI fake returning empty window)
**Surface:** `/` — `ProviderUnavailable` `no_data_for_window`

**Preconditions:**
- Backend reachable; a valid symbol over a window known to contain no trades (e.g. a weekend/closed window)
- On `http://localhost:3650/`, Historical mode

**Steps:**
1. Click "Historical"
2. Type a valid symbol (e.g. `F`) into the symbol input
3. Set "Date" to a weekend / market-closed date and any "Start time"/"End time"
4. Leave speed at `1×` and click "Watch"

**Expected Result:**
- An amber-bordered panel titled "No data for that window" appears in place of the cockpit
- The panel shows a ⚠ icon and the emphasized phrase "no data for that window"
- Helper text suggests trying a different window during regular market hours
- NO cockpit panels are visible

---

### UT-10 — No credentials shows the "Real-data provider unavailable" honest panel (error / regression)

**Type:** error
**Priority:** P1
**Surface:** `/` — `ProviderUnavailable` `provider_unavailable`

**Preconditions:**
- Backend running WITHOUT Alpaca credentials configured (the common QA-env state)
- On `http://localhost:3650/`, Historical mode

**Steps:**
1. Click "Historical"
2. Type `AAPL` into the symbol input
3. Fill "Date", "Start time", "End time" with any valid past window; leave speed at `1×`
4. Click "Watch"

**Expected Result:**
- An amber-bordered panel titled "Real-data provider unavailable" appears in place of the cockpit
- The panel shows a ⚠ icon and the emphasized phrase "real-data provider unavailable"
- Helper text mentions setting the Alpaca API key/secret or switching to Simulated
- NO cockpit appears; the app does NOT silently fall back to Simulated data

---

### UT-11 — Each failure reason routes to its own panel; cockpit never shown alongside (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` — `page.tsx` failure routing

**Preconditions:**
- Ability to trigger the failure reasons reachable in the current env (at minimum
  `provider_unavailable` via UT-10; the other two are operator-gated)

**Steps:**
1. Trigger the no-creds case (UT-10) and note the panel title
2. Switch to Simulated and back to Historical to clear state, then trigger the untradable case (UT-08) if reachable
3. Clear state again and trigger the empty-window case (UT-09) if reachable

**Expected Result:**
- Each trigger shows exactly ONE amber panel matching its reason ("Real-data provider unavailable" / "Symbol not tradable" / "No data for that window")
- In every case the cockpit (bid/ask/trades/event log) is absent — the honest panel fully replaces it
- No two panels appear at once; no panel appears alongside a cockpit

---

### UT-12 — Simulated mode keeps the plain ticker input (no search dropdown) (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — `TopBar` symbol input (Simulated mode)

**Preconditions:**
- On `http://localhost:3650/`

**Steps:**
1. Confirm "Simulated" is selected (default), or click "Simulated"
2. Click into the symbol input
3. Type `SIM` into the input and wait ~½ second

**Expected Result:**
- The symbol input placeholder reads "Ticker e.g. SIM-BUYER"
- NO suggestions dropdown appears below the input (Simulated uses the plain field, not `SymbolSearch`)
- The Historical-only controls (Date / Start time / End time / Replay speed) are NOT shown in Simulated mode

---

### UT-13 — SIM-BUYER watch still classifies and Stop returns to idle (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — `Cockpit`, Stop button (J-01/J-02/J-09)

**Preconditions:**
- On `http://localhost:3650/`, Simulated mode, backend running

**Steps:**
1. Click "Simulated"
2. Type `SIM-BUYER` into the symbol input
3. Click "Watch"
4. Wait for the cockpit to populate
5. Click the red "Stop" button in the header

**Expected Result:**
- After step 3–4 the header shows "Watching SIM-BUYER" and the cockpit populates; the tape state reaches `buyer_control` as the sim stream plays
- After clicking "Stop" the cockpit is removed and the main area returns to the idle "No ticker watched" state
- No error banner appears

---

### UT-14 — Switching data source tears down the active watch (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/` — `DataSourceSelector` + watch lifecycle

**Preconditions:**
- A SIM-BUYER watch is active (UT-13 steps 1–4, do not stop)

**Steps:**
1. With SIM-BUYER watching and the cockpit visible, click the "Historical" button

**Expected Result:**
- The header no longer shows "Watching SIM-BUYER"
- The cockpit is removed; the main area returns to idle ("No ticker watched") or a fresh Historical state
- The Historical controls (Date / Start time / End time / Replay speed) now appear
- No orphaned "Watching" chip or stale cockpit remains

---

### UT-15 — Search box / honest panels are discoverable from the one screen (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/` — discoverability

**Preconditions:**
- On `http://localhost:3650/`

**Steps:**
1. Load `http://localhost:3650/` as a new user
2. Click "Historical" in the visible data-source control
3. Observe the symbol input and the controls that appear

**Expected Result:**
- The data-source control ("Live / Historical / Simulated") is visible without scrolling — switching to real data is at most one click from the home screen
- In Historical mode the symbol input, Date, Start time, End time, Replay speed, and Watch are all visible on the one screen `/`
- No hidden navigation is required — the entire J-11/J-13/J-14 feature set is reachable from `/`

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home loads, Simulated default | smoke | P1 | `/` |
| UT-02 | Search dropdown shows real matches | happy-path | P1 (gated) | `/` SymbolSearch |
| UT-03 | Selecting a suggestion fills the box | happy-path | P1 (gated) | `/` SymbolSearch |
| UT-04 | Free-text Watch works | happy-path | P1 | `/` SymbolSearch |
| UT-05 | Short/cleared query → no dropdown | validation | P2 | `/` SymbolSearch |
| UT-06 | Historical watch fills cockpit (real) | happy-path | P1 (gated) | `/` Cockpit |
| UT-07 | Scenario chip `historical <SYM> <window>` | happy-path | P2 (gated) | `/` TopBar |
| UT-08 | "Symbol not tradable" panel | error | P1 (gated) | `/` ProviderUnavailable |
| UT-09 | "No data for that window" panel | error | P1 (gated) | `/` ProviderUnavailable |
| UT-10 | "Real-data provider unavailable" panel | error | P1 | `/` ProviderUnavailable |
| UT-11 | Reason routing; cockpit never alongside | validation | P2 | `/` page.tsx |
| UT-12 | Simulated keeps plain input | regression | P1 | `/` TopBar |
| UT-13 | SIM-BUYER classifies; Stop → idle | regression | P1 | `/` Cockpit |
| UT-14 | Source switch tears down watch | regression | P2 | `/` selector |
| UT-15 | Feature discoverable from `/` | ux | P3 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.** Operator-gated P1 tests (UT-02, UT-03,
UT-06, UT-08, UT-09) PASS when real/fixture data is reachable; if the QA env cannot reach the vendor,
record them SKIPPED-not-reachable (not FAIL) and rely on UT-04, UT-10, UT-12, UT-13 plus the backend
fixture tests (TC-01/02/03) for J-11/J-14 evidence.
