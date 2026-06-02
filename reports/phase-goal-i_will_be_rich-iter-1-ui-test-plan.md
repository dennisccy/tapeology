# Phase goal-i_will_be_rich-iter-1 — UI Test Plan

**Phase:** goal-i_will_be_rich-iter-1
**Date:** 2026-06-02
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650
**Backend URL:** http://localhost:8000 (used only for the single-source-of-truth comparison in UT-12)

---

## Test Cases

<!-- UT-XX IDs distinguish these from the functional test plan's TC-XX IDs. -->
<!-- All surfaces are new (greenfield first build); the only route is `/`. -->

---

### UT-01 — Cockpit `/` loads with idle state and no fabricated data (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` (`IdleState`)

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend running at http://localhost:8000
- No ticker has been watched in this session (fresh load / hard refresh)

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen, error page, or crash
- The top bar shows the app name **Tapeology**, a ticker input (placeholder `Ticker e.g. SIM-BUYER`), and a **Watch** button
- The center shows the idle state: heading **"No ticker watched"**, helper text ending in **"Try: SIM-BUYER"**
- The footer reads **"Tapeology reads and classifies the live tape for a single ticker. Descriptive only — not trading advice."**
- NO bid/ask/spread/last numbers, NO tape-state label, NO confidence value, and NO trade rows appear anywhere (no fabricated values)
- The stream-status indicator at the top-right reads **"idle"** with a slate/grey dot
- No console errors

---

### UT-02 — User can watch SIM-BUYER and the stream goes live (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (`TopBar` ticker input + **Watch**, `Cockpit`)

**Preconditions:**
- Fresh load of `http://localhost:3650/` (idle state showing)
- Backend running and the `SIM-BUYER` scenario available

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Click the ticker input field (placeholder `Ticker e.g. SIM-BUYER`)
3. Type `SIM-BUYER` into the field
4. Click the green **Watch** button (or press Enter)
5. Observe the top bar and the panel area for up to ~10 seconds

**Expected Result:**
- A label **"Watching"** followed by `SIM-BUYER` (monospace) appears in the top bar
- The stream-status indicator transitions from **idle** → **connecting** (amber, pulsing dot) → **live** (green dot, text "live")
- The idle "No ticker watched" message is replaced by the six-panel grid: **Tape State**, **Quote**, **Features**, **Recent Trades**, **Observations**, **Event Log**
- A scenario chip reading **"scenario: buyer_control"** appears in the top bar
- No error message appears in the top bar

---

### UT-03 — Quote panel shows live bid/ask/spread/last with spread == ask − bid (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (`QuotePanel`)

**Preconditions:**
- `SIM-BUYER` is being watched and the stream is **live** (after UT-02)

**Steps:**
1. With `SIM-BUYER` live, locate the **Quote** panel
2. Read the **Bid**, **Ask**, **Spread**, and **Last** values
3. Compute `Ask − Bid` by hand and compare to the **Spread** value

**Expected Result:**
- **Bid** is a number rendered in green; **Ask** is a number rendered in red
- **Spread** and **Last** are numbers (not `—`)
- `Spread` equals `Ask − Bid` (allowing for the displayed 2-decimal rounding)
- No value reads `—` once the stream is live and warmed up

---

### UT-04 — Recent Trades table shows price/size/side color-coded by aggressor (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (`RecentTradesPanel`)

**Preconditions:**
- `SIM-BUYER` is being watched and live; warm-up has produced trades

**Steps:**
1. Locate the **Recent Trades** panel
2. Inspect the table header and the trade rows

**Expected Result:**
- The table header shows three columns: **PRICE**, **SIZE**, **SIDE**
- At least one trade row is present, each showing a numeric price, a numeric size, and a side label
- The **Side** cell is colored: green for `buy`, red for `sell`, slate/grey for `unknown`
- For `SIM-BUYER`, most/visible rows are `buy` (green), consistent with a buyer-controlled tape
- The "No trades yet." empty hint is NOT shown

---

### UT-05 — Features panel shows the nine named features with buy-side dominance (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (`FeaturesPanel`)

**Preconditions:**
- `SIM-BUYER` is being watched and live; warm-up complete

**Steps:**
1. Locate the **Features** panel
2. Read each labeled metric row

**Expected Result:**
- Nine rows are present with these labels: **Trade speed**, **Volume speed**, **Aggressive buy ratio**, **Aggressive sell ratio**, **Net aggressive volume**, **Buy price impact**, **Sell price impact**, **Average spread**, **Large prints**
- Each row shows a numeric value (not `—`) once warmed up
- **Aggressive buy ratio** reads high (clearly greater than **Aggressive sell ratio**)
- **Buy price impact** reads a positive number and is rendered in green
- **Net aggressive volume** is positive (green)

---

### UT-06 — Features window selector changes the displayed values (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/` (`FeaturesPanel` window selector)

**Preconditions:**
- `SIM-BUYER` is being watched and live; Features panel populated

**Steps:**
1. In the **Features** panel, note the currently highlighted window tab and the displayed feature values
2. Click the **10s** window tab
3. Click the **300s** window tab
4. Compare the feature values shown under **10s** vs **300s**

**Expected Result:**
- A row of window tabs is visible: **10s**, **30s**, **60s**, **180s**, **300s**
- Clicking a tab visually highlights it (lighter background) and de-highlights the previously selected tab
- At least one feature value (e.g. **Trade speed** or **Aggressive buy ratio**) differs between the **10s** and **300s** windows
- No crash or `—`-only state appears when switching windows

---

### UT-07 — Tape State resolves to Buyer Control with confidence and green color (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (`TapeStatePanel`)

**Preconditions:**
- `SIM-BUYER` is being watched and live; allow ~10–20s past warm-up

**Steps:**
1. Locate the **Tape State** panel
2. Read the large state label, the **Confidence** number, and observe the confidence bar

**Expected Result:**
- The large label reads **"Buyer Control"** and is rendered in green (emerald)
- A **Confidence** value (a decimal between 0 and 1, e.g. `0.82`) is shown in monospace
- A horizontal confidence bar is filled green, its width proportional to the confidence
- The "Warming up — collecting tape data…" note is NOT present once resolved

---

### UT-08 — Honest warm-up: no premature directional call (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` (`TapeStatePanel` warm-up note)

**Preconditions:**
- Fresh load; `SIM-BUYER` about to be watched

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Type `SIM-BUYER`, click **Watch**
3. Immediately (within the first 1–3 seconds) read the **Tape State** panel

**Expected Result:**
- During warm-up the Tape State panel shows **"Unclear"** (amber) at a low confidence, and/or the note **"Warming up — collecting tape data…"** in amber
- It does NOT show **"Buyer Control"** instantly on the first tick (no fabricated directional call before warm-up completes)
- The state later resolves to **Buyer Control** (as verified in UT-07)

---

### UT-09 — Observations panel lists human-readable evidence (happy path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/` (`ObservationsPanel`)

**Preconditions:**
- `SIM-BUYER` watched and live, warmed up

**Steps:**
1. Locate the **Observations** panel
2. Read the listed bullet items

**Expected Result:**
- At least one bullet observation is shown (plain-language evidence, e.g. about buyer aggression / positive buy impact)
- The "No observations yet." empty hint is NOT shown once warmed up
- Text is descriptive (no profit predictions, no "buy/sell now" advice)

---

### UT-10 — Event Log shows the buyer_control transition, newest first (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (`EventLogPanel`)

**Preconditions:**
- `SIM-BUYER` watched and live, resolved to Buyer Control (after UT-07)

**Steps:**
1. Locate the **Event Log** panel
2. Read the list of log lines

**Expected Result:**
- The log contains the line **"Tape state changed to buyer_control"**
- Entries are ordered newest-first (the most recent transition is at the top)
- The "No events yet." empty hint is NOT shown

---

### UT-11 — Live updates over WebSocket without page reload (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (`Cockpit` live WS updates)

**Preconditions:**
- `SIM-BUYER` watched and live

**Steps:**
1. Note the current **Recent Trades** top row and the **Trade speed** value in the Features panel
2. Wait ~5–10 seconds WITHOUT refreshing the page or navigating
3. Re-read the same two values

**Expected Result:**
- At least one of the observed values changes (new trade rows appear / feature numbers update) without any page reload
- The browser does NOT navigate or flash a full reload (URL stays `http://localhost:3650/`)
- The stream-status indicator stays **live** (green) throughout

---

### UT-12 — UI values match REST exactly (single source of truth) (regression / integrity)

**Type:** regression
**Priority:** P1
**Surface:** `/` (`Cockpit` vs backend REST)

**Preconditions:**
- `SIM-BUYER` watched, live, and warmed up
- A terminal with `curl` access to the backend at http://localhost:8000

**Steps:**
1. In the UI, read the **Tape State** label, **Confidence**, and the **Buy price impact** / **Aggressive buy ratio** feature values for the currently selected window
2. In a terminal run: `curl -s http://localhost:8000/tape/SIM-BUYER/state`
3. In a terminal run: `curl -s http://localhost:8000/tape/SIM-BUYER/features`
4. Compare the UI readouts to the JSON for the same window

**Expected Result:**
- The UI state and confidence match the `/state` JSON exactly (UI does not recompute or round differently beyond display precision)
- The UI feature values match the corresponding values in `/features` for the selected window
- No divergence in spread, ratios, impacts, or confidence between the UI and REST

---

### UT-13 — Unknown ticker surfaces an explicit error, no fabricated data (error)

**Type:** error
**Priority:** P1
**Surface:** `/` (`TopBar` watch error message)

**Preconditions:**
- Fresh load of `http://localhost:3650/` (idle state)

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Type `NOPE` into the ticker input
3. Click the **Watch** button

**Expected Result:**
- An explicit error message appears in the top bar in red (e.g. **"'NOPE' could not be watched"** or the backend's detail message)
- The cockpit panels do NOT appear and NO bid/ask/state/confidence/trade values are rendered
- The "Watching" label does NOT switch to `NOPE`
- The view remains the idle state (or stays empty) — no fabricated snapshot is shown

---

### UT-14 — Ticker input is normalized (trim + uppercase) (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` (`TopBar` ticker input)

**Preconditions:**
- Fresh load of `http://localhost:3650/`

**Steps:**
1. Type `  sim-buyer  ` (lowercase, with leading/trailing spaces) into the ticker input
2. Click **Watch**

**Expected Result:**
- The watch succeeds and the **"Watching"** label shows `SIM-BUYER` (uppercased, trimmed)
- The scenario chip reads **"scenario: buyer_control"** and panels populate as in UT-02

---

### UT-15 — Empty ticker submission is a no-op (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` (`TopBar` ticker input)

**Preconditions:**
- Fresh load of `http://localhost:3650/` (idle state)

**Steps:**
1. Leave the ticker input empty (or type only spaces)
2. Click the **Watch** button

**Expected Result:**
- Nothing happens: no error message, no "Watching" label, no panels
- The idle state ("No ticker watched") remains
- No network watch request is fired (the form submit is ignored for empty input)

---

### UT-16 — Reserved scenario stays Unclear, no fabricated direction (error / honesty)

**Type:** error
**Priority:** P2
**Surface:** `/` (`Cockpit`, `TapeStatePanel`)

**Preconditions:**
- Fresh load; backend running

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Type `SIM-SELLER` and click **Watch**
3. Wait ~10 seconds and read the **Tape State** panel and **Event Log**

**Expected Result:**
- The watch is accepted (it is a registered sim ticker) and the "Watching" label shows `SIM-SELLER`
- The **Tape State** stays **"Unclear"** (amber) at low confidence — it does NOT fabricate `Seller Control` or any directional call (that target state is deferred to a later journey)
- No fabricated bid/ask/feature values are presented as a directional verdict

---

### UT-17 — Color semantics and no trading-advice language (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/` (all panels + footer)

**Preconditions:**
- `SIM-BUYER` watched, live, in Buyer Control

**Steps:**
1. Scan the **Tape State** (green), **Quote** Bid (green) / Ask (red), **Recent Trades** side colors, and **Buy/Sell price impact** colors
2. Read all visible text including the footer

**Expected Result:**
- Buy-side / positive-impact readouts render **green**; sell-side / negative-impact render **red**; unclear/absorption render **amber**
- The footer disclaimer **"Descriptive only — not trading advice."** is present
- NO text anywhere claims profit, returns, "buy/sell now", price targets, or any trading advice

---

### UT-18 — Cockpit is discoverable as the single home (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/` (`IdleState`, `TopBar`)

**Preconditions:**
- Fresh load of `http://localhost:3650/`

**Steps:**
1. Navigate to `http://localhost:3650/`
2. As a first-time user, look for how to start watching a ticker

**Expected Result:**
- The idle state explicitly instructs the user: enter a ticker above and click **Watch**, with the hint **"Try: SIM-BUYER"**
- The ticker input and **Watch** button are visible without scrolling, in the top bar
- A new user can start the core flow within one action (type + Watch) — no hidden menu or extra navigation required

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Idle cockpit loads, no fabricated data | smoke | P1 | `/` |
| UT-02 | Watch SIM-BUYER, stream goes live | happy-path | P1 | `/` |
| UT-03 | Quote panel bid/ask/spread/last | happy-path | P1 | `/` |
| UT-04 | Recent Trades color-coded by side | happy-path | P1 | `/` |
| UT-05 | Features panel nine named metrics | happy-path | P1 | `/` |
| UT-06 | Features window selector changes values | happy-path | P2 | `/` |
| UT-07 | Tape State resolves to Buyer Control | happy-path | P1 | `/` |
| UT-08 | Honest warm-up, no premature call | validation | P2 | `/` |
| UT-09 | Observations evidence list | happy-path | P2 | `/` |
| UT-10 | Event Log buyer_control transition | happy-path | P1 | `/` |
| UT-11 | Live WS updates, no reload | happy-path | P1 | `/` |
| UT-12 | UI matches REST (single source) | regression | P1 | `/` |
| UT-13 | Unknown ticker error, no fabrication | error | P1 | `/` |
| UT-14 | Ticker normalized (trim + uppercase) | validation | P2 | `/` |
| UT-15 | Empty submission is a no-op | validation | P2 | `/` |
| UT-16 | Reserved scenario stays Unclear | error | P2 | `/` |
| UT-17 | Color semantics, no advice language | ux | P2 | `/` |
| UT-18 | Cockpit discoverable as single home | ux | P3 | `/` |

**P1 tests must all pass for the browser QA verdict to be PASS:** UT-01, UT-02, UT-03, UT-04, UT-05, UT-07, UT-10, UT-11, UT-12, UT-13.
