# Phase goal-i_will_be_super_rich-iter-3 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-3
**Date:** 2026-06-04
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650

---

> **Wall-clock note.** The market-status states are session-dependent. At handoff the US market was
> **closed**, so the closed / next-open branch and the "Market is closed" panel are directly
> browser-verifiable. If you run these tests *during* US market hours (weekday 09:30–16:00 ET), the
> indicator shows **open** and a Live watch returns the honest "streaming not implemented" state
> instead of the closed panel — in that case mark the closed-branch tests (UT-06, UT-07, UT-15) as
> "deferred to backend TC-06" and document the observed branch.
>
> **Credentials note.** Tests UT-03 / UT-06 require valid Alpaca vendor credentials configured in the
> backend env (so the clock reports a real session). Without credentials, the indicator and panel
> correctly show the *unavailable* path instead — that is UT-05, not a failure.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Home screen loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running and reachable

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Wait for the page to fully load
3. Open browser DevTools → Console

**Expected Result:**
- The "Tapeology" title is visible in the top bar
- The 3-way data-source selector with buttons "Live", "Historical", "Simulated" is visible
- The symbol/ticker input and the green "Watch" button are visible
- The center area shows the idle state (no cockpit, no error panel)
- No red errors in the browser console

---

### UT-02 — Market-status indicator appears only in Live mode (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` — `TopBar` / `MarketStatusIndicator`

**Preconditions:**
- On `http://localhost:3650/`
- Default mode is **Simulated**

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Confirm the data-source selector shows **Simulated** as the active (highlighted) button
3. Observe the top bar — note there is **no** pill reading "market …"
4. Click the **Live** button in the data-source selector
5. Observe the top bar again

**Expected Result:**
- In Simulated mode: there is **no** "market" status pill in the top bar
- After clicking **Live**: a small pill appears in the top bar reading `market` followed by a status word (`…`, `open`, `closed`, or `unavailable`)

---

### UT-03 — Live indicator shows the real session status (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `MarketStatusIndicator`

**Preconditions:**
- Valid Alpaca credentials configured in the backend env
- On `http://localhost:3650/`

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Click the **Live** button in the data-source selector
3. Wait up to ~3 seconds for the "market" pill to resolve past the `…` placeholder
4. Read the status word in the pill

**Expected Result:**
- The pill shows one real session status — either:
  - green dot + **`market open`** (US market open right now), or
  - amber dot + **`market closed — next open <time>`** (US market closed; a `font-mono` next-open time follows)
- The status matches the actual US session at run time
- It is **never** the old static "unavailable" stub when credentials are present, and it never shows "open" before the first fetch resolves
- Document which branch (open / closed) you observed

---

### UT-04 — Indicator shows a placeholder before first fetch resolves (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — `MarketStatusIndicator` placeholder state

**Preconditions:**
- On `http://localhost:3650/` in Simulated mode (so Live has not yet mounted)

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Click the **Live** button
3. Watch the "market" pill on its very first paint (immediately after clicking Live)

**Expected Result:**
- On first paint the pill briefly shows a slate (grey) dot and the label `…` ("Checking market status…" tooltip on hover)
- It then resolves to a real status (`open` / `closed` / `unavailable`)
- It never flashes `open` or `closed` first before the real value loads

---

### UT-05 — Indicator shows honest "unavailable" with no credentials (error)

**Type:** error
**Priority:** P2
**Surface:** `/` — `MarketStatusIndicator` unavailable state

**Preconditions:**
- Backend running with **no** vendor credentials configured (or credentials invalid)
- On `http://localhost:3650/`

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Click the **Live** button
3. Wait for the "market" pill to resolve
4. Hover over the pill to read its tooltip

**Expected Result:**
- The pill shows an amber dot and the label **`market unavailable`**
- Tooltip reads "Live market status needs vendor credentials (not configured)"
- It is **never** a fabricated `open` or `closed` when credentials are absent

---

### UT-06 — Live watch while market closed shows "Market is closed" panel (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `ProviderUnavailable` `market_closed` variant

**Preconditions:**
- Valid Alpaca credentials configured
- US market is **closed** at run time (see wall-clock note)
- On `http://localhost:3650/`

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Click the **Live** button in the data-source selector
3. Type `AAPL` into the "Symbol search" input (placeholder "Symbol e.g. AAPL")
4. Click the green **Watch** button
5. Observe the center area of the page

**Expected Result:**
- A centered amber panel titled **"Market is closed"** appears in place of the cockpit
- It shows the emphasized phrase **"market is closed"**
- It shows help text including "The US market is closed right now — it next opens \<time\>" and "You can replay a past session with Historical instead."
- **No** cockpit appears alongside it — no quote panel, no trades list, no state panel
- The top bar still shows the `market closed — next open <time>` pill

---

### UT-07 — Next-open time renders in local timezone with explicit zone label (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` — `ProviderUnavailable` / `MarketStatusIndicator` next-open formatting

**Preconditions:**
- Same as UT-06 ("Market is closed" panel is showing); market closed; creds present

**Steps:**
1. Reach the "Market is closed" panel (UT-06 steps 1–4)
2. Read the next-open time in the panel help text
3. Read the next-open time in the top-bar `market closed — next open <time>` pill

**Expected Result:**
- Both next-open times are formatted like `Jun 5, 09:30 AM EDT` (month, day, hour:minute, explicit short zone label)
- The zone label matches the operator's local timezone
- The time is **not** shown as raw UTC ending in `Z` (e.g. not `2026-06-05T13:30:00Z`)

---

### UT-08 — Indicator mounts/unmounts cleanly when toggling modes (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — `TopBar` conditional mount

**Preconditions:**
- On `http://localhost:3650/`

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Click **Live** — confirm the "market" pill appears
3. Click **Historical** — observe the top bar
4. Click **Simulated** — observe the top bar
5. Click **Live** again — observe the top bar

**Expected Result:**
- The "market" pill appears **only** while **Live** is the active mode
- It disappears when switching to Historical or Simulated
- It re-appears when returning to Live
- In Historical mode the date / start-time / end-time / speed inputs appear (and no market pill); in Simulated the ticker box reads placeholder "Ticker e.g. SIM-BUYER"

---

### UT-09 — Poll stops after leaving Live (resource-leak regression)

**Type:** regression
**Priority:** P2
**Surface:** `/` — `MarketStatusIndicator` poll cleanup

**Preconditions:**
- On `http://localhost:3650/`
- Browser DevTools → Network tab open, filter by `clock`

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Click **Live** — confirm a request to `/market/clock` fires
3. Click **Simulated** to leave Live mode
4. Clear the Network log, then wait ~70 seconds (longer than the 60s poll interval)
5. Inspect the Network tab for any new `/market/clock` requests

**Expected Result:**
- After leaving Live mode, **zero** new requests to `/market/clock` appear during the wait
- No console errors about state updates on an unmounted component
- The poll interval was cleared on mode-change (iter-0 leak lesson)

---

### UT-10 — Existing three honest panels unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — `ProviderUnavailable` provider_unavailable / symbol_not_tradable / no_data_for_window

**Preconditions:**
- On `http://localhost:3650/`

**Steps:**
1. **provider_unavailable:** Ensure backend has **no** creds. Select **Live**, type `AAPL`, click **Watch**.
2. Note the panel title and emphasized phrase.
3. **symbol_not_tradable:** With creds present and market open (or via backend trigger), select **Live**, type a bogus symbol such as `ZZZZINVALID`, click **Watch**.
4. Note the panel title and phrase.
5. **no_data_for_window:** Select **Historical**, type `AAPL`, choose a date with no trades (e.g. a weekend) and a narrow window, click **Watch**.
6. Note the panel title and phrase.

**Expected Result:**
- provider_unavailable → centered amber panel titled **"Real-data provider unavailable"**, phrase "real-data provider unavailable"
- symbol_not_tradable → panel titled **"Symbol not tradable"**, phrase "not a tradable symbol"
- no_data_for_window → panel titled **"No data for that window"**, phrase "no data for that window"
- All three are byte-for-byte the same copy as before this phase; only `market_closed` carries a next-open time

---

### UT-11 — Simulated watch still classifies correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — Cockpit (J-01/J-02/J-10)

**Preconditions:**
- On `http://localhost:3650/`

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Confirm/select **Simulated** mode
3. Type `SIM-BUYER` into the "Ticker" input (placeholder "Ticker e.g. SIM-BUYER")
4. Click the green **Watch** button
5. Wait for the cockpit to populate

**Expected Result:**
- The cockpit appears with live quote / trades / state panels
- The classification resolves to **buyer_control**
- The top bar shows "Watching SIM-BUYER" with a **Stop** button; **no** market pill (Simulated mode)

---

### UT-12 — Historical replay still populates the cockpit (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — Cockpit (J-11)

**Preconditions:**
- On `http://localhost:3650/`; creds present for historical data

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Click **Historical**
3. Type `AAPL` into the "Symbol search" input
4. Choose a valid past trading **Date**, a **Start time** and **End time** within market hours, and a replay speed (e.g. `5×`)
5. Click the green **Watch** button

**Expected Result:**
- The cockpit populates with replayed trades and quote/state panels
- The top bar stream dot animates / reads a live/closed status as the replay proceeds
- No "Market is closed" or "provider unavailable" panel appears for a valid window

---

### UT-13 — Symbol search fills the ticker box (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/` — `SymbolSearch` (J-13)

**Preconditions:**
- On `http://localhost:3650/`; creds present

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Click **Live** (or **Historical**)
3. Type `AAP` into the "Symbol search" input
4. Wait for the suggestion dropdown
5. Click a suggested result (e.g. "AAPL")

**Expected Result:**
- A suggestions dropdown appears as you type
- Clicking a suggestion fills the symbol input with the picked symbol (e.g. `AAPL`)
- The pick is ready to use with the **Watch** button

---

### UT-14 — Stop returns to idle (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — Stop button (J-09)

**Preconditions:**
- An active watch is running (complete UT-11 first so `SIM-BUYER` is watched)

**Steps:**
1. With `SIM-BUYER` actively watched (cockpit visible), locate the **Stop** button next to "Watching SIM-BUYER" in the top bar
2. Click the **Stop** button

**Expected Result:**
- The cockpit disappears and the center returns to the idle state
- "Watching SIM-BUYER" and the **Stop** button disappear from the top bar
- No error panel appears

---

### UT-15 — "Market is closed" panel is clear and actionable (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` — `ProviderUnavailable` `market_closed`

**Preconditions:**
- Market closed; creds present; "Market is closed" panel showing (UT-06)

**Steps:**
1. Reach the "Market is closed" panel (UT-06)
2. Read the full panel copy as a first-time user

**Expected Result:**
- The user can understand, without developer knowledge, that: (a) the market is closed, (b) when it next opens, (c) no fabricated tape is shown, and (d) Historical replay is the suggested alternative
- The amber ⚠ icon, title, and phrase make the honest-failure nature obvious
- The next-open time is human-readable in local time (per UT-07)

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home screen loads | smoke | P1 | `/` |
| UT-02 | Indicator only in Live mode | smoke | P1 | `/` TopBar |
| UT-03 | Real session status shown | happy-path | P1 | `/` MarketStatusIndicator |
| UT-04 | Placeholder before first fetch | ux | P2 | `/` MarketStatusIndicator |
| UT-05 | Unavailable with no creds | error | P2 | `/` MarketStatusIndicator |
| UT-06 | Live+closed → Market is closed panel | happy-path | P1 | `/` ProviderUnavailable |
| UT-07 | Next-open in local zone | validation | P2 | `/` ProviderUnavailable |
| UT-08 | Mount/unmount on mode toggle | ux | P2 | `/` TopBar |
| UT-09 | Poll stops after leaving Live | regression | P2 | `/` MarketStatusIndicator |
| UT-10 | Existing 3 panels unchanged | regression | P1 | `/` ProviderUnavailable |
| UT-11 | Simulated classification | regression | P1 | `/` Cockpit |
| UT-12 | Historical replay | regression | P1 | `/` Cockpit |
| UT-13 | Symbol search fills box | regression | P2 | `/` SymbolSearch |
| UT-14 | Stop → idle | regression | P1 | `/` Stop |
| UT-15 | Closed panel clarity | ux | P2 | `/` ProviderUnavailable |

**P1 tests must all pass for browser QA verdict to be PASS.**

> Session-dependent P1 caveat: UT-03 and UT-06 depend on creds + wall-clock. If creds are absent,
> UT-03 collapses into UT-05 (unavailable) and UT-06 cannot run — cite backend TC-06 for the closed
> branch and document the environment.
