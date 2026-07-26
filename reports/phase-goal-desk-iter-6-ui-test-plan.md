# Phase goal-desk-iter-6 — UI Test Plan

**Phase:** goal-desk-iter-6
**Date:** 2026-07-26
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301 (backend at http://localhost:8301)

---

## Scope note

This iteration wires two new interaction paths onto already-shipped backend data: `/desk`'s
Screen History list becomes clickable (read-back of a past snapshot, no recompute), every
Briefing/Skipped row becomes a drill-in link into `/structure`, and `/structure` gains additive
query-param prefill + auto-Load. No new page, no new backend route. Test cases below cover only
what changed this iteration; `/desk`'s Run Screen/Top-up controls and `/structure`'s existing
Load-form/Tradable-Map/Case-Studies/Edge-Report behavior are prior-iteration surfaces and are only
touched here as regression checks (UT-09, UT-10).

**Fixture data used throughout this plan** (present in the ambient store as of this writing;
a browser-QA pass MUST use a throw-away fixture-scoped copy, never the operator's real
`apps/backend/.data/` — see Preconditions on each test case):
- History row **2026-06-22**: 10 ranked rows, 91 skipped rows. Row 1 = `AAPL`, side
  `resistance`, `band_class A`, `distance_bps 0.33523150389608725`, `price_low 298.02`,
  `price_high 300.1001`. First skipped row = `ABBV`, reason `no_bars`.
  `as_of = 2026-06-22T23:59:59Z`.
- History row **2026-07-25**: the other recorded screen (used as a second, distinct history
  entry — any value differing from 2026-06-22's is sufficient to prove a real display swap).

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend is running at http://localhost:3301, backend at http://localhost:8301
- Backend has at least one recorded desk screen (the ambient store already has
  `screen-2026-06-22` and `screen-2026-07-25`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to finish loading (the pulsing loading skeleton disappears)

**Expected Result:**
- Page renders without a blank screen or crash
- The heading "Desk" is visible (element with `data-testid="desk-title"`)
- A "Provenance" panel, a "Briefing" panel, a "Skipped Members" panel, and a "Screen History"
  panel are all visible
- No browser console errors

---

### UT-02 — `/structure` loads without errors, no params (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to finish loading

**Expected Result:**
- Page renders without a blank screen or crash
- The heading "Structure" is visible (element with `data-testid="structure-title"`)
- The Symbol field (labeled "Symbol", `aria-label="Structure symbol"`) is empty
- The "As-of (UTC, ISO-8601)" field (`data-testid="structure-as-of-input"`) is empty
- No browser console errors

---

### UT-03 — Click a Screen History row renders that exact snapshot (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded and showing the latest screen (2026-07-25), with the "Screen History" table
  visible showing at least the two rows dated `2026-06-22` and `2026-07-25`
- Backend is the fixture-scoped copy seeded with `screen-2026-06-22` and its real AAPL bars (per
  the phase spec's persistence-discipline note — never the operator's real ambient `.data/`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Screen History" table (`data-testid="desk-history-table"`), locate the row where the
   "date" column reads exactly `2026-06-22`
3. Click anywhere on that row (`data-testid="desk-history-row"` with
   `data-screen-date="2026-06-22"`)
4. Wait for the page to re-render (this is a same-page state swap, not a navigation — should be
   near-instant)

**Expected Result:**
- A banner appears above the Provenance panel reading exactly "Viewing the recorded screen for
  2026-06-22 — not the latest." (`data-testid="desk-viewing-indicator"`), with a "Latest" button
  next to it
- The clicked row now shows a highlighted background (its `data-selected` attribute is `true`)
- The "Briefing" table's first row shows: symbol `AAPL`, side `resistance`, class chip reading
  "Class A", distance `0.34 bps` (hover/title shows the full `0.33523150389608725`)
- The "Skipped Members" section shows a "Skipped — no bars (91)" heading (exact count `91`) with
  `ABBV` as its first listed symbol
- The browser's network log shows exactly one new GET request to
  `/research/desk/screen?date=2026-06-22` and zero new POST requests

---

### UT-04 — "Latest" control reverts to the newest screen (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Continuing directly from UT-03: the 2026-06-22 screen is currently displayed, the viewing
  banner and "Latest" button are visible

**Steps:**
1. Click the button reading exactly "Latest" (`data-testid="desk-history-latest-button"`)
2. Wait for the page to re-render

**Expected Result:**
- The "Viewing the recorded screen for 2026-06-22 — not the latest." banner disappears entirely
- The Briefing table now shows the 2026-07-25 snapshot's own rows (not the AAPL/2026-06-22 row
  values from UT-03), matching exactly what was on screen before UT-03's click
- No new history row shows a highlighted/selected background
- The browser's network log shows zero new requests (the "Latest" click is a pure client-side
  state change — the `latest` snapshot was already held in memory from the initial page load)

---

### UT-05 — Click a Briefing row drills into `/structure` with prefill and auto-load (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → `/structure`

**Preconditions:**
- The 2026-06-22 screen is displayed on `/desk` (repeat UT-03's steps 1–4 first if starting fresh)
- The AAPL ranked row is visible in the Briefing table
- Backend is the fixture-scoped copy that also has AAPL's real recorded bars (needed so
  `/structure` can actually draw a band — see the phase spec's TC-3/TC-10 persistence note)

**Steps:**
1. Click anywhere on the AAPL row in the Briefing table (the row's `data-testid="desk-screen-row"`
   with `data-symbol="AAPL"` — clicking the symbol cell itself is sufficient, the whole row is a
   click target)
2. Wait for the browser to navigate and for the new page to finish loading

**Expected Result:**
- The browser's address bar shows exactly
  `http://localhost:3301/structure?symbol=AAPL&asof=2026-06-22T23%3A59%3A59Z` (or the
  unescaped-colon equivalent `.../structure?symbol=AAPL&asof=2026-06-22T23:59:59Z`)
- The Symbol field shows "AAPL"
- The "As-of (UTC, ISO-8601)" field (`data-testid="structure-as-of-input"`) shows exactly
  `2026-06-22T23:59:59Z`
- No manual click on the "Load" button was needed — the Tradable Map panel already shows a
  populated bands table (`data-testid="tradable-map-table"`), not the "Choose a symbol..." empty
  state
- A band row's range column (`data-testid="tradable-band-range"`) reads `298.02–300.1001`

---

### UT-06 — Click a Skipped Members row also drills into `/structure` (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk` → `/structure`

**Preconditions:**
- The 2026-06-22 screen is displayed on `/desk`, with the "Skipped — no bars (91)" section visible
  and `ABBV` listed as a row

**Steps:**
1. Click anywhere on the `ABBV` row in the Skipped Members table
   (`data-testid="desk-skip-row"` with `data-symbol="ABBV"`)
2. Wait for the browser to navigate and for the new page to finish loading

**Expected Result:**
- The browser's address bar shows `http://localhost:3301/structure?symbol=ABBV&asof=2026-06-22T23:59:59Z`
  (colon may be URL-escaped as `%3A`)
- The Symbol field shows "ABBV"
- The As-of field shows exactly `2026-06-22T23:59:59Z`
- The page does not crash and does not show a blank page
- The Tradable Map panel shows the honest empty state — either
  `data-testid="tradable-map-no-bar-series"` ("No bar series recorded for ABBV.") or
  `data-testid="tradable-map-no-bands"`, never a fabricated band

---

### UT-07 — History click for a date with no matching screen leaves the UI unchanged (error)

**Type:** error
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded, showing either the latest screen or a previously-selected history screen
- No recorded screen exists for `2020-01-01` (or any other date not present in the "Screen
  History" table)

**Steps:**
1. Note the currently-displayed Briefing table's first row and "Screen History" table contents
2. Using browser devtools (Network tab → "Copy as fetch", or a manual `fetch()` call in the
   console) issue `fetch("http://localhost:8301/research/desk/screen?date=2020-01-01")` to
   simulate what a click on a non-existent history date would trigger (there is no rendered row
   for a date with no recorded screen, so this step reproduces the same code path
   `handleSelectHistoryScreen` runs)
3. Observe the page after the response resolves — if testing via a real UI click is possible
   (e.g. a test harness that can inject an arbitrary date), click that row instead of using devtools

**Expected Result:**
- The page does not crash and does not go blank
- The Briefing table's first row is unchanged from step 1 (still showing whatever was displayed
  before)
- An amber inline note appears reading "No recorded screen matches 2020-01-01 — still showing the
  previously displayed screen." (`data-testid="desk-history-fetch-error"`)
- No JavaScript error is thrown in the console

---

### UT-08 — `/structure?symbol=AAPL` with `asof` omitted behaves as if neither param were present (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- None (direct navigation)

**Steps:**
1. Navigate to `http://localhost:3301/structure?symbol=AAPL`
2. Wait for the page to fully render (at least 2 seconds, to rule out a delayed auto-load)

**Expected Result:**
- The Symbol field is empty (NOT prefilled with "AAPL")
- The As-of field is empty
- No load has been triggered — the Tradable Map panel shows the idle empty state
  ("Choose a symbol and an as-of time, then Load, to see its tradable level map.",
  `data-testid="tradable-map-idle"`)
- Page state is otherwise identical to UT-02's no-params baseline

---

### UT-09 — `/structure?asof=...` with `symbol` omitted behaves as if neither param were present (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- None (direct navigation)

**Steps:**
1. Navigate to `http://localhost:3301/structure?asof=2026-06-22T23:59:59Z`
2. Wait for the page to fully render (at least 2 seconds)

**Expected Result:**
- The Symbol field is empty
- The As-of field is empty (NOT prefilled with `2026-06-22T23:59:59Z`)
- No load has been triggered — `data-testid="tradable-map-idle"` is shown
- Page state is otherwise identical to UT-02's no-params baseline

---

### UT-10 — `/structure`'s manual Load flow still works unaided (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- `/structure` opened with no query params (fresh, per UT-02)
- Backend has a recorded bar series for AAPL

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type "AAPL" into the Symbol field (`aria-label="Structure symbol"`)
3. Click the "Today" button (`data-testid="structure-as-of-today-button"`) to fill the As-of
   field, or type a known-good ISO-8601 UTC timestamp directly into the "As-of (UTC, ISO-8601)"
   field
4. Click the "Load" button (`data-testid="structure-load-button"`)

**Expected Result:**
- The Tradable Map panel transitions from idle to a loading state and then to a populated bands
  table (or an honest empty state if AAPL truly has no bands at that as-of — either is acceptable,
  a crash or stuck-loading state is not)
- This confirms the manual Load path (`handleSubmit` → `handleLoad`) still functions exactly as
  before this iteration's additive prefill code was added

---

### UT-11 — `/desk`'s Run Screen / Top-up controls still render (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded, showing a populated screen (latest or any history selection)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Scroll to the "Run Screen / Top-up" panel at the bottom of the page

**Expected Result:**
- A button reading "Run Screen" (`data-testid="desk-run-screen-button"`) is visible and enabled
- A button reading "Top-up" (`data-testid="desk-topup-button"`) is visible and enabled
- Neither button's presence or label has changed as a result of this iteration's history/drill-in
  work (do NOT click either button in this test — clicking "Run Screen" is a write action and is
  explicitly out of scope for this iteration's replay/QA per the phase spec's persistence
  discipline)

---

### UT-12 — Screen History and drill-in links are discoverable without instructions (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded, showing a populated screen with at least one history row and one Briefing row

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Without any prior explanation, hover the mouse over a row in the "Screen History" table

**Expected Result:**
- The row's background highlights on hover and the cursor changes to a pointer, signaling it is
  clickable (no separate "click me" label is required, but the affordance must be visually
  apparent)
3. Hover the mouse over a row in the "Briefing" table
- **Expected Result:** The row also highlights on hover with a pointer cursor, signaling it too
  is clickable — a first-time user can discover both new interactions within two hovers, with no
  documentation

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads without errors | smoke | P1 | `/desk` |
| UT-02 | `/structure` loads without errors, no params | smoke | P1 | `/structure` |
| UT-03 | Click history row renders that exact snapshot | happy-path | P1 | `/desk` |
| UT-04 | "Latest" control reverts to newest screen | happy-path | P1 | `/desk` |
| UT-05 | Briefing row drills into `/structure` with prefill+auto-load | happy-path | P1 | `/desk` → `/structure` |
| UT-06 | Skipped row also drills into `/structure` | happy-path | P1 | `/desk` → `/structure` |
| UT-07 | History click, no matching screen, UI unchanged | error | P2 | `/desk` |
| UT-08 | `/structure?symbol=` only, no partial prefill | validation | P2 | `/structure` |
| UT-09 | `/structure?asof=` only, no partial prefill | validation | P2 | `/structure` |
| UT-10 | Manual Load flow still works | regression | P1 | `/structure` |
| UT-11 | Run Screen / Top-up controls still render | regression | P2 | `/desk` |
| UT-12 | History/drill-in rows discoverable via hover | ux | P2 | `/desk` |

**P1 tests must all pass for browser QA verdict to be PASS.**
