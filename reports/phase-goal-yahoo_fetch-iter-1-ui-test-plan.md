# Phase goal-yahoo_fetch-iter-1 — UI Test Plan

**Phase:** goal-yahoo_fetch-iter-1
**Date:** 2026-07-09
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301 (referenced only where a test needs it — see UT-14)

---

## Scope note (read before running)

This iteration shipped **zero frontend file changes** (`git status --short apps/frontend/` is
empty) and **zero new on-screen capability** — the new Yahoo Finance bar adapter is REST/MCP-only
by explicit design (the `/structure` "Fetch from Yahoo Finance" button ships in a later
iteration, J-05). Per the phase spec, `Frontend Present: yes` is set anyway solely so the
browser-qa lane runs a **J-06 foundation regression spot-check**: proving the new `yfinance`
runtime dependency and the backend bar-fetch vendor-selector change did not break any existing
rendered surface, and did not leak the new `feed="yahoo"` value into any UI label ahead of J-05.

Consequently, this plan contains **no "happy path for a new capability" test** — fabricating one
would misrepresent what shipped. In its place, UT-06 (Cockpit) and UT-07 (Structure) carry P1
weight as the two named highest-risk regression checks, and UT-14 is an optional, informational
exploratory test that shows a tester the one real (if invisible) way this iteration's new data can
already reach a browser screen today.

All test cases below trace to the plan's "Key Test Scenarios" (`runs/goal-yahoo_fetch-iter-1/plan.md`)
and the phase spec's "Browser (J-06 regression spot-check)" testing requirement
(`docs/phases/goal-yahoo_fetch-iter-1.md`). None of these duplicate the functional/API test plan
at `reports/qa/goal-yahoo_fetch-iter-1-test-plan.md` (TC-01–TC-22) — those are pure REST/pytest
checks; everything here is browser-observable.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Cockpit `/` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend is running at http://localhost:3301 and the backend at http://localhost:8301
- No login is required (the app has no auth)
- No watch is currently active (fresh page load / no ticker being watched)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Wait for the page to fully load

**Expected Result:**
- The top navigation bar (`data-testid="app-nav"`) is visible with exactly 5 links: "Cockpit",
  "Journal", "Studies", "Performance", "Structure"
- Below the nav, the header shows "Tapeology" and a 3-way data-source toggle with buttons "Live",
  "Historical", "Simulated" — "Simulated" is already highlighted/active (no click needed)
- Since no ticker is watched, the main content area shows the heading "No ticker watched" and the
  hint text "Try: SIM-BUYER"
- No red error banner is visible anywhere on the page
- No errors appear in the browser console

---

### UT-02 — Structure `/structure` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend are running

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Structure" is visible (`data-testid="structure-title"`)
- A form is visible with a "Symbol" field (placeholder "e.g. PG"), an "As-of (UTC, ISO-8601)"
  field (placeholder "2026-06-09T21:00:00Z"), and a "Load" button
  (`data-testid="structure-load-button"`) that is greyed out/disabled until both fields have text
- Below the form, the empty-state message "Choose a symbol and an as-of time, then Load, to see
  its S/R levels and confluence zones." is visible
- Further down the page, a "Registry" panel is visible; within a few seconds it resolves to show a
  "Champion" box with "strategy" and "profile" values (or an honest "could not be loaded" amber
  panel if the backend is genuinely unreachable — never a blank gap)
- No red error banner is visible; no errors in the browser console

---

### UT-03 — Journal `/journal` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/journal`

**Preconditions:**
- Frontend and backend are running

**Steps:**
1. Navigate to `http://localhost:3301/journal`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Journal" is visible
- A three-tab view toggle is visible (`data-testid="journal-view-toggle"`): "Theses" (active by
  default, highlighted), "Analytics", and a third hint-log tab
- Below the toggle, either a populated table (`data-testid="journal-table"`) or the honest empty
  state (`data-testid="journal-empty"`) is shown — never a blank white area
- No red error banner is visible; no errors in the browser console

---

### UT-04 — Studies `/studies` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/studies`

**Preconditions:**
- Frontend and backend are running

**Steps:**
1. Navigate to `http://localhost:3301/studies`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Replay studies" is visible (`data-testid="studies-title"`)
- A study-creation form is visible on the left (`data-testid="study-create-form"`) with a
  "Run study" button (`data-testid="study-create-button"`)
- The right-hand results panel shows either a previously selected study, or the placeholder text
  "Create a study, or select one from the list, to read its results."
  (`data-testid="studies-no-selection"`)
- No red error banner is visible; no errors in the browser console

---

### UT-05 — Performance `/performance` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/performance`

**Preconditions:**
- Frontend and backend are running

**Steps:**
1. Navigate to `http://localhost:3301/performance`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Performance" is visible (`data-testid="performance-title"`)
- A "PnL ledger" section is visible on the left — either populated rows or the honest empty
  message "The PnL ledger is empty — no enhancement has been validated yet."
- A "Champion" section is visible on the right (`data-testid="champion-summary"`) showing
  "strategy" and "profile" values
- No red error banner is visible; no errors in the browser console

---

### UT-06 — Cockpit Simulated Watch completes end-to-end; feed badge reads "Simulated", never "yahoo" (regression — crux risk check)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend are running
- No watch is currently active

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Confirm the "Simulated" button in the data-source toggle is highlighted/active (click it if it
   is not)
3. Click into the field labeled "Ticker" (placeholder "Ticker e.g. SIM-BUYER") and type `SIM-BUYER`
4. Click the "Watch" button
5. Observe the page immediately after clicking
6. Wait up to 10 seconds and observe the page again

**Expected Result:**
- Step 5: The main area immediately shows "Connecting to SIM-BUYER…" with a pulsing amber dot
  (`data-testid="connecting-state"`) — never a frozen blank screen
- Step 6: The connecting state resolves into the full cockpit panel grid: a "Watching" label next
  to "SIM-BUYER" in the header, a "Stop" button, and six panels — "Tape State" (showing a state
  name plus a "Confidence" value), "Quote", "Recent Trades", "Features", "Observations", and
  "Event Log"
- A small badge reading "feed" then a value is visible next to the "Watching SIM-BUYER" indicator
  (`data-testid="feed-basis"`, label text in `data-testid="feed-basis-label"`). **That label text
  must read exactly "Simulated" — never "yahoo", never "sip", never blank.** This is the single
  most important assertion in this plan: it proves the new Yahoo-default bar-**fetch** vendor
  selector (`get_bar_fetch_adapter()`, confined to `POST /research/bars`) did not leak into or
  alter the separate live/simulated tape accessor (`get_adapter()`), which this iteration was
  required to leave untouched.
- No red error banner appears; no errors in the browser console

---

### UT-07 — Structure page renders an existing symbol's chart, levels, and zones unbroken (regression — crux risk check)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- A symbol with an already-registered bar series and computable S/R levels exists. If none is
  known ahead of time, run UT-14 first (it registers one via a live Yahoo fetch for `AAPL`), or
  query `GET http://localhost:8301/research/bars` to find any `symbol` already present.
- An as-of timestamp inside that symbol's recorded bar window (ISO-8601 UTC).

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Click into the "Symbol" field and type the chosen symbol (e.g. `AAPL`)
3. Click into the "As-of (UTC, ISO-8601)" field and type a timestamp inside that symbol's recorded
   window (e.g. `2026-06-05T00:00:00Z` if using UT-14's fetch)
4. Click the "Load" button

**Expected Result:**
- Within a few seconds, a "Price chart — S/R levels" panel appears containing a rendered
  candlestick chart (`data-testid="structure-chart-canvas"`) with visible candles — not a blank
  canvas
- A caption below the chart reads "Candles: `<timeframe>` series (`<N>` of `<M>` recorded bars, as
  of the query time). Level lines span every recorded timeframe."
- A "Confluence zones" panel appears below, showing either one or more zone cards
  (`data-testid="zone-row"`, each carrying a "Class A/B/C" badge) or the honest message "No
  qualifying confluence zone among these levels." — never a crash or blank area
- No amber degraded-state panel ("The levels could not be loaded" / similar) appears; no errors in
  the browser console

---

### UT-08 — Top navigation is unchanged: exactly 5 links, correct labels and destinations (regression)

**Type:** regression
**Priority:** P1
**Surface:** navigation (all pages)

**Preconditions:**
- Frontend and backend are running

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Look at the top navigation bar
3. Click each nav link in this order: "Journal", "Studies", "Performance", "Structure", then
   "Cockpit"

**Expected Result:**
- The nav bar shows exactly 5 links, in this order: "Cockpit", "Journal", "Studies",
  "Performance", "Structure" — no 6th link, and specifically no new "Yahoo" / "Fetch" /
  "Provenance"-named link has appeared
- Clicking each link navigates to its matching route (`/journal`, `/studies`, `/performance`,
  `/structure`, `/`) and that link visually highlights as the active page
  (`aria-current="page"`)
- The nav never shows its degraded state, "navigation unavailable — backend unreachable"
  (`data-testid="nav-unavailable"`)

---

### UT-09 — Journal detail page opens from a table row (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/journal/[id]`

**Preconditions:**
- At least one thesis row exists in the Journal table (`data-testid="journal-row"`). If the table
  is empty, this test cannot run in this environment — record that as a precondition gap, not a
  failure caused by this iteration's change.

**Steps:**
1. Navigate to `http://localhost:3301/journal`
2. Confirm the "Theses" tab is active and at least one row is visible in the table
   (`data-testid="journal-table"`)
3. Click the ticker link in the first row (`data-testid="journal-row-link"`)

**Expected Result:**
- The page navigates to `/journal/<id>` and the heading changes to "Review"
- A "← Back to journal" link is visible at the top (`data-testid="back-to-journal"`)
- The thesis detail sections (expected-behaviour statements, verdict timeline, entry risk-flag
  chips, action marks, execution checks) render below with no crash and no blank page
- No red error banner appears; no errors in the browser console

---

### UT-10 — Studies "Run study" form opens and its fields are interactive (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/studies`

**Preconditions:**
- Frontend and backend are running

**Steps:**
1. Navigate to `http://localhost:3301/studies`
2. Locate the study-creation form on the left (`data-testid="study-create-form"`)
3. Click each visible field in the form (the source selector, the setup field
   `data-testid="study-setup"`, the direction field `data-testid="study-direction"`) without
   submitting

**Expected Result:**
- Every field accepts focus and, where it is a dropdown, opens its options — no field is frozen or
  unresponsive
- The "Run study" button (`data-testid="study-create-button"`) is visible; it does not need to be
  clicked for this test (submission exercises `SOURCE_HISTORICAL` / `get_study_market_adapter()`,
  a code path this iteration explicitly did not change — see plan Risk 1)
- No red error banner appears; no errors in the browser console

---

### UT-11 — Cockpit Watch validation still blocks an empty ticker (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend and backend are running; no watch is currently active

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Leave the field labeled "Ticker" empty
3. Observe the "Watch" button
4. Click directly on the "Watch" button anyway

**Expected Result:**
- Before clicking: the "Watch" button already appears visually disabled (greyed out), and an
  inline amber message "Enter a ticker symbol" is visible beside it
  (`data-testid="watch-validation"`)
- After clicking: nothing is submitted — the page stays on the "No ticker watched" idle state; no
  cockpit grid appears and no "Connecting…" state is shown

---

### UT-12 — Journal detail shows an honest error for an unknown thesis id (error)

**Type:** error
**Priority:** P2
**Surface:** `/journal/[id]`

**Preconditions:**
- Frontend and backend are running

**Steps:**
1. Navigate directly to `http://localhost:3301/journal/does-not-exist-12345`
2. Wait for the page to finish loading

**Expected Result:**
- The page shows a red-bordered alert box (`data-testid="detail-error"`) with the text "This
  thesis was not found." — never a blank page, a raw stack trace, or an infinite loading spinner
- A "Return to the journal" link is visible and, when clicked, navigates back to `/journal`

---

### UT-13 — No page renders the raw "yahoo" feed string; the new vendor stays invisible until J-05 (ux)

**Type:** ux
**Priority:** P1
**Surface:** all 6 surfaces (`/`, `/journal`, `/journal/[id]`, `/studies`, `/performance`,
`/structure`)

**Preconditions:**
- Frontend and backend are running
- Complete UT-06 first (Cockpit's feed badge needs an active watch to be visible at all)

**Steps:**
1. With SIM-BUYER still being watched from UT-06, visually scan the Cockpit page for any text
   containing "yahoo" (any case)
2. Navigate to `http://localhost:3301/journal` and scan the theses table, including any visible
   "feed" column/cell (`data-testid="journal-feed"`), for the text "yahoo"
3. Navigate to `http://localhost:3301/studies` and scan the page for the text "yahoo"
4. Navigate to `http://localhost:3301/performance` and scan the page for the text "yahoo"
5. Navigate to `http://localhost:3301/structure` and scan the page (including any loaded chart,
   registry, and comparison sections) for the text "yahoo"

**Expected Result:**
- The word "Yahoo" (or "yahoo") appears on NONE of the 5 surfaces — not as a badge, not as a table
  value, not as a tooltip, not in any error message
- The Cockpit's feed badge (from UT-06) reads only "Simulated" / "IEX (live)" / "SIP
  (consolidated)" — the taxonomy-owned `FEED_BASIS_LABELS` set, unchanged by this iteration
- The Journal table's per-row "feed" cell (`data-testid="journal-feed"`), if any rows exist, shows
  only "sim" / "iex" / "sip" values — never "yahoo" — because thesis capture reads a completely
  different, untouched mapping (`research/feed_basis.py`) from the bar-series `feed` field this
  iteration changed
- This absence is **expected and correct**, not a gap to fix: J-05 (a later iteration) adds the
  first human-visible "Yahoo Finance" label. Its premature appearance here would indicate an
  accidental leak of the raw `feed` string into a component this iteration was not scoped to touch
  — a genuine coherence/single-source-of-truth violation worth failing this test over.

---

### UT-14 — [Exploratory] A Yahoo-fetched series reaches the Structure chart with no vendor indicator (ux)

**Type:** ux
**Priority:** P3 (informational — not required for a PASS verdict; documents a real but
intentionally-incomplete UI gap named in the ui-impact-analyst's report)

**Surface:** `/structure` (setup step calls the REST API directly — this is unavoidable: no UI
button to trigger a Yahoo fetch exists yet, that is J-05's job)

**Preconditions:**
- Frontend and backend are running; a terminal is available to the tester
- Confirm `AAPL` has no bar series already registered: `curl -s http://localhost:8301/research/bars
  | grep -o "\"symbol\":\"AAPL\""` returns nothing. (At the time this plan was written, this
  backend's bar store was empty, so `AAPL` is expected to be clean.) If it DOES return a match,
  substitute a different liquid symbol (e.g. `MSFT`) throughout this test instead.

**Steps:**
1. Run: `curl -s -X POST http://localhost:8301/research/bars -H "Content-Type: application/json"
   -d '{"symbol":"AAPL","timeframe":"1d","start":"2026-05-01T00:00:00Z","end":"2026-06-05T00:00:00Z"}'`
2. Confirm the JSON response is HTTP 200 with a `bar_series` object whose `feed` field reads
   exactly `"yahoo"`, and whose `bars` array is non-empty
3. Navigate to `http://localhost:3301/structure`
4. Type `AAPL` into the "Symbol" field and `2026-06-05T00:00:00Z` into the "As-of (UTC, ISO-8601)"
   field
5. Click "Load"

**Expected Result:**
- Step 2: The curl response is a 200 with real OHLCV bars and `"feed": "yahoo"` — proving the
  keyless fetch is real, not a stub
- Step 5: The "Price chart — S/R levels" panel renders a candlestick chart built from those very
  bars (the caption's bar count should roughly match the ~35-day window just fetched) — this is
  the one place in the entire product where this iteration's new data reaches a real browser
  screen today
- Nowhere on the page does any badge, caption, or tooltip indicate this data came from Yahoo
  specifically — no "Yahoo" text anywhere (confirms UT-13's finding also holds for freshly-fetched
  Yahoo data, not just pre-existing data)
- This is the documented, expected gap (per `reports/phase-goal-yahoo_fetch-iter-1-user-visible-changes.md`,
  "Not Visible Yet") — **not a bug**. When a future test of this same scenario, after J-05 ships,
  shows a "Yahoo Finance" badge, that is the intended improvement, not a regression to flag.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit loads | smoke | P1 | `/` |
| UT-02 | Structure loads | smoke | P1 | `/structure` |
| UT-03 | Journal loads | smoke | P1 | `/journal` |
| UT-04 | Studies loads | smoke | P1 | `/studies` |
| UT-05 | Performance loads | smoke | P1 | `/performance` |
| UT-06 | Cockpit Watch flow + feed badge (crux risk) | regression | P1 | `/` |
| UT-07 | Structure chart/levels/zones unbroken (crux risk) | regression | P1 | `/structure` |
| UT-08 | Nav bar unchanged (5 links) | regression | P1 | nav (all pages) |
| UT-09 | Journal detail opens from row | regression | P2 | `/journal/[id]` |
| UT-10 | Studies form fields interactive | regression | P2 | `/studies` |
| UT-11 | Watch validation blocks empty ticker | validation | P2 | `/` |
| UT-12 | Journal detail honest 404 state | error | P2 | `/journal/[id]` |
| UT-13 | No "yahoo" string leaked anywhere yet | ux | P1 | all 6 surfaces |
| UT-14 | [Exploratory] Yahoo data reaches Structure chart | ux | P3 | `/structure` |

**P1 tests must all pass for browser QA verdict to be PASS.** (9 of 14 tests are P1 this
iteration — higher than a typical phase — because a zero-new-UI, backend-vendor-selector change
makes "did nothing break" the entire verdict; there is no new-capability happy-path test to
counterbalance it.)
