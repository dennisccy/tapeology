# Phase goal-i_will_be_super_rich-iter-1 — UI Test Plan

**Phase:** goal-i_will_be_super_rich-iter-1
**Date:** 2026-06-04
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3650 (CHAIN_FRONTEND_URL offset; substitute `:3000` if running default)

---

## Conventions

- The entire app lives on a single screen `/`. There are no new routes.
- All tests assume **NO vendor credentials** are configured (`ALPACA_API_KEY` / `ALPACA_API_SECRET` absent from the backend environment) — this is the honest no-credentials state under test.
- "Data source selector" = the three-button segmented control (`role="group"`, aria-label `Data source`) holding `Live` / `Historical` / `Simulated`.
- These are UI (browser) tests. They do NOT duplicate the API/artifact tests in `reports/qa/goal-i_will_be_super_rich-iter-1-test-plan.md` (TC-01..TC-10).

---

## Test Cases

<!-- UT-XX prefix distinguishes these from the functional TC-XX IDs. -->

---

### UT-01 — Home screen loads with the data-source selector (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/` (TopBar)

**Preconditions:**
- Frontend running at http://localhost:3650
- Backend reachable

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Wait for the page to fully load

**Expected Result:**
- The "Tapeology" title is visible in the top bar
- A 3-button segmented control is visible immediately to the right of the title, showing exactly the buttons `Live`, `Historical`, and `Simulated` (in that order)
- The `Simulated` button is the active/highlighted one (darker background, `aria-pressed="true"`); `Live` and `Historical` are not pressed
- A single text input with placeholder `Ticker e.g. SIM-BUYER` and a green `Watch` button are visible
- No blank screen, no error banner, no console errors

---

### UT-02 — Selecting a mode highlights only that mode (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — `DataSourceSelector`

**Preconditions:**
- On `http://localhost:3650/`, `Simulated` is active (default)

**Steps:**
1. Click the `Live` button in the data-source selector
2. Observe which button is highlighted
3. Click the `Historical` button
4. Observe which button is highlighted
5. Click the `Simulated` button
6. Observe which button is highlighted

**Expected Result:**
- After step 1: only `Live` is highlighted (`aria-pressed="true"`); `Historical` and `Simulated` are not
- After step 3: only `Historical` is highlighted; the others are not
- After step 5: only `Simulated` is highlighted; the others are not
- At all times exactly one of the three buttons is active — never zero, never two

---

### UT-03 — Symbol/ticker input is mode-aware (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — TopBar symbol/ticker input

**Preconditions:**
- On `http://localhost:3650/`, `Simulated` is active

**Steps:**
1. Inspect the text input next to the selector while `Simulated` is active
2. Click the `Live` button
3. Inspect the same text input
4. Click the `Historical` button
5. Inspect the same text input
6. Click the `Simulated` button
7. Inspect the same text input

**Expected Result:**
- In Simulated (steps 1, 7): placeholder reads `Ticker e.g. SIM-BUYER` and the input's accessible label is `Ticker`
- In Live (step 3): placeholder reads `Symbol e.g. AAPL` and the accessible label is `Symbol search`
- In Historical (step 5): placeholder reads `Symbol e.g. AAPL` and the accessible label is `Symbol search`
- Any text already typed is preserved across the switch (the box is not destroyed)

---

### UT-04 — Historical mode reveals the replay-window controls (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — TopBar Historical controls

**Preconditions:**
- On `http://localhost:3650/`

**Steps:**
1. Click the `Historical` button
2. Inspect the controls inside the watch form (to the right of the symbol box, before the `Watch` button)
3. Open the replay-speed dropdown and read its options
4. Click the `Live` button
5. Inspect the form controls again
6. Click the `Simulated` button
7. Inspect the form controls again

**Expected Result:**
- After step 1: four extra inline controls appear — a date input (aria-label `Date`), a start-time input (aria-label `Start time`), an en-dash `–` separator, an end-time input (aria-label `End time`), and a speed dropdown (aria-label `Replay speed`)
- Step 3: the speed dropdown lists exactly `1×`, `2×`, `5×`, `10×` (default selection `1×`)
- After step 4 (Live): the date / start-time / end-time / speed controls are gone
- After step 6 (Simulated): those controls are also gone
- The `Watch` button remains visible in all three modes

---

### UT-05 — Live mode shows the honest market-status indicator (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` — TopBar market-status indicator

**Preconditions:**
- On `http://localhost:3650/`; no credentials configured

**Steps:**
1. Click the `Live` button
2. Look for a status pill in the top bar (after the Watch button)
3. Read the pill's text and dot color
4. Click the `Historical` button, then the `Simulated` button
5. Look for the pill again

**Expected Result:**
- After step 1: a small pill appears reading `market unavailable` with a small amber/yellow dot to its left
- The pill never reads `open`, `closed`, or any fabricated market state — only `unavailable`
- After step 4 (Historical and Simulated): the market-status pill is gone (it only exists in Live mode)

---

### UT-06 — Live watch with no credentials shows the provider-unavailable panel (happy path / error)

**Type:** happy-path
**Priority:** P1
**Surface:** `/` (main area) — `ProviderUnavailable`

**Preconditions:**
- On `http://localhost:3650/`; no credentials configured

**Steps:**
1. Click the `Live` button
2. Type `AAPL` into the symbol search box (placeholder `Symbol e.g. AAPL`)
3. Click the green `Watch` button
4. Observe the main area below the top bar

**Expected Result:**
- The main area shows an amber-bordered panel titled `Real-data provider unavailable`
- The panel contains a ⚠ icon and the exact lowercase phrase `real-data provider unavailable`
- The panel body mentions configuring the Alpaca API key/secret or switching to `Simulated`
- NO cockpit grid / tape panels are rendered (no fabricated tape, no prices, no event log)
- The app does NOT silently fall back to Simulated

---

### UT-07 — Historical watch with no credentials shows the provider-unavailable panel (error)

**Type:** error
**Priority:** P1
**Surface:** `/` (main area) — `ProviderUnavailable`

**Preconditions:**
- On `http://localhost:3650/`; no credentials configured

**Steps:**
1. Click the `Historical` button
2. Type `MSFT` into the symbol search box
3. Pick any date in the `Date` field, any `Start time`, any `End time`, and leave speed at `1×`
4. Click the green `Watch` button
5. Observe the main area

**Expected Result:**
- The same amber `Real-data provider unavailable` panel renders, with the phrase `real-data provider unavailable` and the ⚠ icon
- The body text references `Historical` data needing vendor credentials
- NO cockpit grid is shown; no fabricated data; no fall-back to Simulated

---

### UT-08 — Simulated SIM-BUYER watch still populates the cockpit (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (main area) — `Cockpit`

**Preconditions:**
- On `http://localhost:3650/`; backend running; `Simulated` is active (default)

**Steps:**
1. Confirm the `Simulated` button is highlighted
2. Type `SIM-BUYER` into the ticker input (placeholder `Ticker e.g. SIM-BUYER`)
3. Click the green `Watch` button
4. Wait up to ~10 seconds for the stream to connect and panels to populate
5. Read the tape-state panel and the status dot at the far right of the top bar

**Expected Result:**
- The cockpit grid populates with live values over the WebSocket (no empty/blank cockpit)
- A `Watching SIM-BUYER` indicator with a `Stop` button appears in the top bar
- The tape state resolves to `buyer_control`
- The status dot (far right) shows `live` (green) while streaming
- The provider-unavailable panel does NOT appear in Simulated mode

---

### UT-09 — Switching source/symbol tears down the prior watch (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` — `page.tsx` watch lifecycle / status dot

**Preconditions:**
- A Simulated watch on `SIM-BUYER` is live (complete UT-08 first)

**Steps:**
1. With `SIM-BUYER` actively watched (cockpit populated), click the `Live` button in the selector
2. Observe the top bar and main area immediately after switching
3. (Optional) Type `AAPL` and click `Watch` in Live mode

**Expected Result:**
- The `Watching SIM-BUYER` indicator clears (the prior watch is dropped)
- The status dot returns to `idle` or `connecting` during the handover — it does not stay stuck on the prior `live` SIM-BUYER stream
- The cockpit for SIM-BUYER is gone; no leftover SIM-BUYER updates continue
- After step 3, the new Live watch produces the provider-unavailable panel (clean new watch, no orphaned prior watch)

---

### UT-10 — Stop button ends an active simulated watch (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/` — TopBar Stop control

**Preconditions:**
- A Simulated watch on `SIM-BUYER` is live (complete UT-08 first)

**Steps:**
1. With `SIM-BUYER` watched, click the `Stop` button (red-outlined, aria-label `Stop watching`) in the top bar
2. Observe the top bar and main area

**Expected Result:**
- The `Watching SIM-BUYER` indicator and `Stop` button disappear
- The cockpit clears / returns to the idle empty state
- The status dot returns to `idle` (grey) or `closed`
- No console errors

---

### UT-11 — Empty symbol in Live mode does not fabricate a cockpit (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/` — TopBar form

**Preconditions:**
- On `http://localhost:3650/`; no credentials configured

**Steps:**
1. Click the `Live` button
2. Leave the symbol search box empty
3. Click the green `Watch` button
4. Observe the main area

**Expected Result:**
- The app does NOT render a populated cockpit with fabricated tape data
- Either the provider-unavailable panel appears or an inline error message is shown (amber/rose text), or the watch simply does not start — in no case is real or fake tape data shown
- The app remains on `/` with no crash or blank page

---

### UT-12 — Real-data feature is discoverable and clearly labeled (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/` — TopBar

**Preconditions:**
- On `http://localhost:3650/` as a first-time user

**Steps:**
1. Navigate to `http://localhost:3650/`
2. Without prior knowledge, look at the top bar for a way to choose live/historical market data

**Expected Result:**
- The `Live` / `Historical` / `Simulated` choice is visible within the first view (no scrolling, no hidden menu) — discoverable in 0 clicks
- The labels `Live`, `Historical`, `Simulated` make the data-source intent clear
- When a real mode is chosen with no credentials, the unavailable panel explains the next action (set Alpaca credentials or switch to Simulated) in plain language — the user is never left guessing why no tape appears

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Home loads with selector | smoke | P1 | `/` TopBar |
| UT-02 | Mode selection highlights one | happy-path | P1 | DataSourceSelector |
| UT-03 | Mode-aware symbol/ticker input | happy-path | P1 | TopBar input |
| UT-04 | Historical replay controls reveal | happy-path | P1 | TopBar Historical controls |
| UT-05 | Live market-status indicator | happy-path | P1 | TopBar market status |
| UT-06 | Live no-creds → unavailable panel | happy-path | P1 | ProviderUnavailable |
| UT-07 | Historical no-creds → unavailable panel | error | P1 | ProviderUnavailable |
| UT-08 | SIM-BUYER cockpit populates | regression | P1 | Cockpit |
| UT-09 | Switching source tears down prior watch | regression | P1 | page.tsx lifecycle |
| UT-10 | Stop ends active watch | regression | P2 | TopBar Stop |
| UT-11 | Empty Live symbol no fabrication | validation | P2 | TopBar form |
| UT-12 | Real-data feature discoverable | ux | P3 | TopBar |

**P1 tests (UT-01..UT-09) must all pass for the browser QA verdict to be PASS.**
