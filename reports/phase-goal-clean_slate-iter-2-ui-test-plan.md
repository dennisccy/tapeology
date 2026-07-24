# Phase goal-clean_slate-iter-2 — UI Test Plan

**Phase:** goal-clean_slate-iter-2 (J-02: "Frontend + WS demolition — the two-page product")
**Date:** 2026-07-24
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Scope note

This iteration is **subtractive only** — no new page, button, or capability was added. Most tests
below are therefore **absence checks** (confirming deleted UI is truly gone, not just hidden) and
**regression checks** (confirming the two surviving pages — Cockpit and Structure — still work
exactly as before). There is no dedicated "new feature" happy-path test because none exists this
iteration; UT-08 and UT-10 are labeled happy-path because they exercise the core surviving cockpit
workflow end to end, now that the thesis/hint/sound layer has been stripped out of it.

## Environment Preconditions (apply to every test below unless noted otherwise)

- Backend is running and reachable at `http://localhost:8301`.
- Frontend is running and reachable at `http://localhost:3301`, and was **rebuilt clean** after
  this iteration's code changes (`rm -rf apps/frontend/.next`, rebuild, restart — T-9). A stale
  `.next` build will show the OLD pre-iteration UI (5 nav links, thesis strip, etc.) and produce
  false failures in this plan.
- No login is required anywhere in this app.
- Browser devtools (F12 / right-click → Inspect) are available for UT-12 only; every other test
  needs nothing beyond the page itself.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Cockpit (`/`) loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- No ticker is currently being watched (fresh page load).

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Wait for the page to fully load

**Expected Result:**
- Page renders without a blank screen, crash overlay, or client-side error page
- The top nav bar shows "Tapeology" and exactly two links: "Cockpit" and "Structure"
- The header shows a 3-way source selector ("Live" / "Historical" / "Simulated", with "Simulated"
  highlighted by default), a ticker field (shows placeholder text "Ticker e.g. SIM-BUYER"), and a
  "Watch" button
- The main content area shows the heading "No ticker watched" and, below it, text starting "Enter
  a ticker above and click Watch to see its live tape read…", plus the hint "Try: SIM-BUYER"
- No thesis strip, hint panel, or sound-toggle control appears anywhere on the page
- No browser console errors

---

### UT-02 — Structure (`/structure`) loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- None — a fresh, unloaded visit to the page.

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load

**Expected Result:**
- Page renders the heading "Structure"
- Top nav bar shows exactly "Cockpit" and "Structure", with "Structure" shown highlighted/active
- A form is visible with a "Symbol" field (placeholder "e.g. PG"), an "As-of (UTC, ISO-8601)" field
  (placeholder "2026-06-09T21:00:00Z"), a "Today" button, and a "Load" button
- The "Tradable Map" panel shows the empty-state prompt "Choose a symbol and an as-of time, then
  Load, to see its tradable level map." — no chart, no crash, no infinite spinner
- No browser console errors

---

### UT-03 — Top nav shows exactly two links on every kept page (regression)

**Type:** regression
**Priority:** P1
**Surface:** nav (global — present on `/` and `/structure`)

**Preconditions:**
- Backend reachable (the nav loads its links from `GET /meta/ui-routes` at runtime; there is no
  hardcoded fallback list).

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Look at the top navigation bar, directly below the "Tapeology" wordmark
3. Navigate to `http://localhost:3301/structure`
4. Look at the top navigation bar again

**Expected Result:**
- On both pages the nav bar shows **exactly two** links, labeled "Cockpit" and "Structure" — no
  "Journal", "Studies", "Performance", or any other label, and no extra unlabeled icons
- On `/`, "Cockpit" appears visually highlighted (darker pill background, light-green text) as the
  active link; on `/structure`, "Structure" is the one highlighted instead
- The amber message "navigation unavailable — backend unreachable" does **not** appear (that would
  indicate a different failure — the backend being unreachable — not this iteration's own change)

---

### UT-04 — `/journal` renders the app's not-found page (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/journal`

**Preconditions:**
- None.

**Steps:**
1. Navigate to `http://localhost:3301/journal`
2. Wait for the page to finish loading

**Expected Result:**
- The page shows a "404" heading and, below it, the text "This page could not be found."
- The top nav bar above it still renders normally, showing "Cockpit" and "Structure"
- This is **NOT** a blank white/empty page, **NOT** the browser's own offline / "can't reach this
  page" network-error screen, and **NOT** the old filterable trade-journal table or hint-activity
  log

---

### UT-05 — `/studies` renders the app's not-found page (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/studies`

**Preconditions:**
- None.

**Steps:**
1. Navigate to `http://localhost:3301/studies`
2. Wait for the page to finish loading

**Expected Result:**
- Same not-found treatment as UT-04: "404" heading, "This page could not be found." text, nav bar
  still intact above it
- **NOT** the old "Replay studies" heading; **NOT** a "Create Study" form; **NOT** a study-results
  list anywhere on screen

---

### UT-06 — `/performance` renders the app's not-found page (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/performance`

**Preconditions:**
- None.

**Steps:**
1. Navigate to `http://localhost:3301/performance`
2. Wait for the page to finish loading

**Expected Result:**
- Same not-found treatment as UT-04: "404" heading, "This page could not be found." text, nav bar
  still intact above it
- **NOT** the old "Performance" heading; **NOT** any analytics chart or table anywhere on screen

---

### UT-07 — `/journal/<id>` (nonexistent id) fails gracefully, not a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/journal/[id]`

**Preconditions:**
- None — `1` is not expected to be a real id since the whole journal surface is deleted.

**Steps:**
1. Navigate to `http://localhost:3301/journal/1`
2. Wait for the page to finish loading

**Expected Result:**
- Same not-found treatment as UT-04: "404" heading, "This page could not be found." text
- **NOT** a crash, **NOT** a blank detail-view shell, **NOT** a raw JavaScript error / stack trace
  in the page body

---

### UT-08 — Sim cockpit flow settles Buyer Control with no thesis/hint/sound UI (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- No ticker is currently being watched.
- "Simulated" is the selected data source (it is the default; if not, click "Simulated" in the
  3-way selector at the top-left of the header first).

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Click into the ticker field (placeholder "Ticker e.g. SIM-BUYER") and type `SIM-BUYER`
3. Click the green "Watch" button
4. Observe the page immediately after clicking (before any data has arrived)
5. Wait for the cockpit panel grid to appear
6. Continue waiting (typically a minute or two) while watching the "Tape State" panel's large
   heading, until it reads "Buyer Control"

**Expected Result:**
- Step 4: the page briefly shows "Connecting to SIM-BUYER…" (not a frozen blank screen)
- Step 5: a grid of six panels appears, titled "Tape State", "Quote", "Features", "Recent Trades",
  "Observations", and "Event Log", with a candlestick price chart panel above the grid
- At every point from step 3 onward — during connecting, during the live watch, and once
  "Buyer Control" is reached — **none** of the following render anywhere on the page:
  - A thesis strip between the chart and the panel grid (no "Declare thesis" button, no verdict /
    stance / grade text)
  - A hint panel under the "Tape State" panel (no "SETUP FORMING" card, no "Prefill a thesis from
    this hint" button)
  - A sound/mute toggle icon anywhere on the page (previously nested inside the thesis strip)
- Step 6: the "Tape State" panel's heading eventually reads "Buyer Control" in bold green text,
  with a "Confidence" readout and a horizontal progress bar beneath it

---

### UT-09 — Stop always returns to the plain idle screen (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Continue directly from UT-08 (SIM-BUYER watched, ideally once "Buyer Control" is showing — but
  this check is valid at any tape state).

**Steps:**
1. With SIM-BUYER watched, click the red "Stop" button in the top-right area of the header (next
   to the "Watching SIM-BUYER" text)

**Expected Result:**
- The page returns directly to the same plain screen as UT-01: heading "No ticker watched", the
  "Enter a ticker above and click Watch…" body text, and the hint "Try: SIM-BUYER"
- No intermediate "surviving thesis" panel, banner, or card appears at any point after clicking
  Stop — this holds regardless of which tape state (Buyer Control, Seller Control, an absorption
  state, etc.) was showing at the moment Stop was clicked

---

### UT-10 — Cockpit PriceChart: candles, timeframe switch, live bars, no thesis markers (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- SIM-BUYER is currently being watched (repeat steps 1–3 of UT-08 if needed).

**Steps:**
1. With SIM-BUYER watched, look at the "Price Chart — Recorded History + Live Tape" panel above
   the cockpit grid
2. Confirm candlesticks are drawn on the chart
3. In the "Tape" button group (left side of the chart panel's header row), click the "30s" button
4. Wait about 10–15 seconds and observe the right edge of the chart
5. Click the "60s" button in the same "Tape" button group

**Expected Result:**
- Step 2: candlesticks are visible on the chart — not a blank chart area
- Step 3: the chart redraws using 30-second bars; the "30s" button now shows as selected
  (highlighted background); no error appears
- Step 4: new bars continue to appear at the right edge of the chart as the tape streams — the
  chart is actively moving, not static/frozen
- Step 5: the chart redraws again using 60-second bars, and "60s" now shows as selected instead
- At no point during this test does a small circle marker or an up-arrow marker appear on or below
  any bar (the old thesis-verdict / entry-exit markers), and no dashed horizontal reference line
  crosses the chart (the old invalidation/level price lines) — only down-arrow tape-state markers
  (colored green/red/amber) may appear above bars, which is expected and unchanged
- No browser console errors

---

### UT-11 — Historical AAPL replay: S/R band overlay + provenance badge (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- The backend has real-market vendor (Alpaca) credentials configured, and AAPL already has a
  recorded bar series covering 2026-06-22 (both true in the standard environment as of this
  session). **If credentials are missing**, step 7 below will instead show an amber "Real-data
  provider unavailable" panel — that is a pre-existing environment condition, not a defect
  introduced by this iteration; note it and move on rather than failing this test.
- No ticker is currently being watched (click "Stop" first if one is active).

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Click the "Historical" button in the 3-way data-source selector (top-left of the header)
3. Type `AAPL` into the symbol field (placeholder "Symbol e.g. AAPL")
4. Type `22-06-2026` into the "Date" field (placeholder "dd-MM-yyyy")
5. Click the "Open 9:30 ET" quick-pick button (it fills the start/end time fields for you)
6. Change the "Replay speed" dropdown from "1×" to "10×"
7. Click the green "Watch" button
8. Once the cockpit panel grid appears, look at the price chart's "History" button group and click
   the "1h" button
9. Look at the small chip near the "Watching AAPL" text in the header, labeled "feed"

**Expected Result:**
- Step 7: the cockpit loads normally for AAPL (see the Preconditions note if an amber "Real-data
  provider unavailable" or "No data for that window" panel appears instead)
- Step 8: one or more shaded horizontal band region(s) (the support/resistance overlay) are drawn
  directly on the price chart, behind the candles. (A small text chip reading "Inside R-band …" or
  "Inside S-band …" may also appear below the chart — this is a bonus state that only shows if the
  live price happens to be trading inside a band at that exact moment; its absence alone is **not**
  a failure as long as the shaded band region itself is visible on the chart.)
- Step 9: the "feed" chip's value reads "SIP (consolidated)" — **not** "Simulated"
- No thesis markers (circles/up-arrows) or dashed thesis price lines appear on the chart (same
  check as UT-10)

---

### UT-12 — `/structure` Load still renders the unchanged 300–302-class wall band (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- AAPL already has a recorded bar series and previously-computed S/R levels (this iteration does
  not fetch or compute anything new). If the backend's data directory is completely fresh/empty,
  Load may instead show "No bar series recorded for AAPL." — that would indicate an unrelated
  environment/data gap, not a defect to attribute to this iteration's code changes.

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `AAPL` into the "Symbol" field
3. Click into the "As-of (UTC, ISO-8601)" field and type `2026-06-22T21:00:00Z`
4. Click the "Load" button
5. Wait for the "Tradable Map" panel and the chart below it to finish loading

**Expected Result:**
- The "Tradable Map" panel's table shows a resistance band whose range falls within approximately
  300–302.4, labeled "Class A", with a round-number badge/flag visible on that row
- The same band is drawn directly on the candle chart below, with price-line labels near
  approximately 300.1 and 302.2 on the price axis
- The rendered band matches this same Symbol/As-of combination's appearance from before this
  iteration (no shift in price range, class, or score) — this page's own chart code
  (`StructureChart.tsx`) was not touched this iteration, so any visible difference here is a
  high-severity regression, not an expected side effect
- No browser console errors; the chart is not blank

---

### UT-13 — Captured WS frame has no `thesis`/`hint` key (regression)

**Type:** regression
**Priority:** P1
**Surface:** N/A — WebSocket payload (`/tape/{ticker}/stream`)

**Preconditions:**
- Browser devtools available.

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Open browser devtools (press F12, or right-click anywhere on the page → Inspect)
3. Click the "Network" tab inside devtools
4. In the Network panel's filter bar, select/type "WS" so only WebSocket connections are shown
5. Type `SIM-BUYER` into the ticker field and click "Watch"
6. In the Network panel, click the row for the connection to `/tape/SIM-BUYER/stream`
7. Within that connection's detail pane, click the "Messages" tab (Chrome) or "Frames" tab
   (Firefox)
8. Click on any received message (an incoming, greyed/green-highlighted row) to view its JSON
9. Read through the top-level keys of that JSON object

**Expected Result:**
- The frame JSON contains keys such as `ticker`, `stream_status`, `tape_state`, `features`,
  `recent_trades`, `market`, `confidence`, `event_log`, and `data_feed`
- The frame JSON does **NOT** contain a `thesis` key, and does **NOT** contain a `hint` key, at the
  top level

*(Alternative for operators comfortable with a terminal: run
`websocat ws://localhost:8301/tape/SIM-BUYER/stream` while SIM-BUYER is watched, and inspect the
printed JSON lines the same way.)*

---

### UT-14 — Watch button disables and explains itself on an empty ticker (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- "Simulated" is the selected data source (the default).
- No ticker is currently being watched, and the ticker field is empty.

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Leave the ticker field empty and look at the "Watch" button and the space immediately to its
   right
3. Click into the ticker field and type any single character, e.g. `A`

**Expected Result:**
- Step 2: the "Watch" button already appears disabled (dimmed/greyed styling), and the amber text
  "Enter a ticker symbol" is already visible next to it — even before any click is attempted
- Step 3: as soon as a character is typed, the dimmed styling and the amber message both disappear,
  and the "Watch" button becomes normal/clickable

---

### UT-15 — Structure is reachable from Cockpit in one click; nav labels are unambiguous (ux)

**Type:** ux
**Priority:** P2
**Surface:** nav

**Preconditions:**
- None.

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Without any prior knowledge of the app, look at the top of the screen for a way to reach a
   second page
3. Click "Structure" in the nav bar

**Expected Result:**
- The word "Structure" is visible in the top nav bar within one glance — no menu needs to be
  opened first, no scrolling is required
- Clicking it navigates to `http://localhost:3301/structure`, and the "Structure" link is now shown
  highlighted as the active link
- No greyed-out, disabled, or "coming soon" label for "Journal", "Studies", or "Performance"
  appears anywhere near the nav — there is no visual hint that a removed feature ever existed there

---

### UT-16 — No dead references to deleted pages/features anywhere in the kept UI (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/`, `/structure` (global scan)

**Preconditions:**
- None.

**Steps:**
1. Navigate to `http://localhost:3301/` and visually scan every visible button, link, badge, and
   menu on the page
2. Navigate to `http://localhost:3301/structure` and repeat the same visual scan
3. On both pages, look specifically for the words "Journal", "Studies", "Performance", "Declare
   thesis", "Hint", "Prefill", or any sound/mute icon

**Expected Result:**
- None of the above labels, links, or controls appear anywhere on either page
- The only two navigable destinations referenced anywhere in the UI are "Cockpit" and "Structure"

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit loads without errors | smoke | P1 | `/` |
| UT-02 | Structure loads without errors | smoke | P1 | `/structure` |
| UT-03 | Top nav shows exactly two links | regression | P1 | nav |
| UT-04 | `/journal` renders not-found | regression | P1 | `/journal` |
| UT-05 | `/studies` renders not-found | regression | P1 | `/studies` |
| UT-06 | `/performance` renders not-found | regression | P1 | `/performance` |
| UT-07 | `/journal/<id>` fails gracefully | error | P2 | `/journal/[id]` |
| UT-08 | Sim cockpit flow, no thesis/hint/sound | happy-path | P1 | `/` |
| UT-09 | Stop returns to plain idle screen | regression | P1 | `/` |
| UT-10 | PriceChart candles/timeframe/live bars | happy-path | P1 | `/` |
| UT-11 | Historical AAPL band overlay + badge | regression | P1 | `/` |
| UT-12 | `/structure` wall band unchanged | regression | P1 | `/structure` |
| UT-13 | WS frame has no thesis/hint key | regression | P1 | WS stream |
| UT-14 | Empty-ticker Watch validation | validation | P2 | `/` |
| UT-15 | Nav discoverability | ux | P2 | nav |
| UT-16 | No dead references anywhere | ux | P3 | `/`, `/structure` |

**P1 tests must all pass for browser QA verdict to be PASS.** (UT-01 through UT-06, UT-08 through
UT-13 — 12 of the 16 tests are P1 in this iteration, reflecting that a subtractive/demolition phase
lives or dies on regression + absence checks rather than a single new happy path.)
