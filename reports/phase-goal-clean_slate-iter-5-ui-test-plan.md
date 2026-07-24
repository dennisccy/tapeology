# Phase goal-clean_slate-iter-5 — UI Test Plan

**Phase:** goal-clean_slate-iter-5
**Date:** 2026-07-24
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301

---

## Scope note

This iteration's ONE user-visible change is restoring the previously-hidden "Case Studies"
section on `/structure` (`SHOW_CASE_STUDIES` flipped `false`→`true`) plus one reinstated sentence
in the page's framing paragraph. Everything else on `/structure` and the Cockpit (`/`) is
unchanged code, but the phase's own Definition of Done requires a full browser walk of every kept
surface as this iteration's regression-sentinel evidence (both charts, the tradable wall band, the
Edge Report honest state, exact-two-item navigation). This test plan therefore covers the Case
Studies restoration as the primary happy-path/new-capability set (UT-01–UT-07), then the required
kept-surface regression walk (UT-08–UT-14), then copy/discoverability checks (UT-15–UT-16).

**Global preconditions for every test below:**
- Frontend is running at `http://localhost:3301`, freshly rebuilt this iteration
  (`rm -rf apps/frontend/.next` then rebuilt/restarted — a stale build would bake the wrong API
  base or serve a ghost page).
- Backend is running at `http://localhost:8301`.
- The AAPL `2026-06-22T21:00:00Z` recorded window (bars + scanned band-touch events) already
  exists in committed fixtures from a prior iteration — no live Yahoo/Alpaca fetch is required.

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test has exact steps and specific expected results — no vague steps. -->

---

## Test Cases

### UT-01 — `/structure` loads with the Case Studies section present (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend rebuilt fresh and running at http://localhost:3301; backend running at
  http://localhost:8301

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Structure" is visible at the top of the page
- Directly below it, a framing paragraph (starting "Tradable Map is the default view...") is
  visible
- A form is visible with a "Symbol" field (placeholder "e.g. PG"), an "As-of (UTC, ISO-8601)"
  field (placeholder "2026-06-09T21:00:00Z"), a "Today" button, and a "Load" button
- Scrolling down, section titles "Tradable Map", "Case Studies", "Edge Report", and "Fetch bars"
  are all present on the page — "Case Studies" is no longer missing
- No blank page, no crash screen, no unhandled error banner
- (Optional, if devtools are available) no red errors in the browser console

---

### UT-02 — Loading AAPL renders candles and the tradable wall band (happy-path / kept-surface regression)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- On a freshly-loaded `http://localhost:3301/structure`

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Click into the "Symbol" field (placeholder "e.g. PG") and type `AAPL`
3. Click into the "As-of (UTC, ISO-8601)" field (placeholder "2026-06-09T21:00:00Z") and type
   `2026-06-22T21:00:00Z`
4. Click the "Load" button
5. Wait up to 5 seconds

**Expected Result:**
- The "Tradable Map" section renders a candlestick chart with visible candle bars
- Below the chart, a table appears with at least one row
- Somewhere in that table's "range" column, the text `300.11` is visible (the pinned wall's lower
  bound)
- The message "The tradable map could not be loaded." does NOT appear
- The message "No bar series recorded for AAPL." does NOT appear

---

### UT-03 — Case Studies panel appears and lists band-touch events (happy-path — the restored capability)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- AAPL as-of `2026-06-22T21:00:00Z` already loaded (complete UT-02 first)

**Steps:**
1. From the loaded `/structure` page, scroll down past the "Tradable Map" section
2. Locate the "Show raw levels" button — the "Case Studies" section is the next titled section
   after it, whether or not raw levels are toggled on
3. Read the "Case Studies" section's description text
4. Inspect the table beneath the Symbol/Reaction filter fields

**Expected Result:**
- A section titled "Case Studies" is visible and is NOT hidden, collapsed, or blank
- Its description text begins "Every band-touch event this store has scanned..."
- A table is visible with column headers reading exactly: `symbol`, `session`, `band`, `reaction`,
  `forward returns`
- At least one row is populated with real values (a symbol, a session date, a band range/side, a
  reaction, and forward-return figures)
- This section sits after "Tradable Map"/the raw-levels toggle and before "Edge Report"

---

### UT-04 — Clicking a Case Studies row opens a working drill-in (happy-path — the restored capability)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Case Studies table is populated with at least one row (UT-03 passed)

**Steps:**
1. Click anywhere on the first row of the Case Studies table
2. Wait up to 2 seconds
3. Look for a new panel below the table
4. Click a second, different row (if more than one row exists)

**Expected Result:**
- After step 2: a panel titled "Case Studies — drill-in" appears, showing a "symbol / session"
  line, a "band" line, a "reaction" line, and a "forward returns" line matching the clicked row
- Under a "Tape timeline" label, either (a) a chronological list of tape-state entries is shown,
  or (b) the exact text "No recorded tape for this event." is shown
- No JavaScript error banner and no blank drill-in panel
- After step 4 (if applicable): the drill-in's contents update to the newly-clicked row's data —
  it is not stuck showing the first row

---

### UT-05 — Case Studies filters narrow the table by symbol and reaction (happy-path)

**Type:** happy-path
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Case Studies table is populated with at least one row (UT-03 passed)

**Steps:**
1. Click into the "Symbol" field directly above the Case Studies table (placeholder "e.g. AAPL"
   — distinct from the page-level Symbol field above the chart)
2. Type `AAPL`
3. Observe the table
4. Clear the Symbol field completely
5. Click the "Reaction" dropdown (options: All, rejected, broke, chopped)
6. Select `chopped`
7. Observe the table

**Expected Result:**
- After step 3: only rows whose `symbol` column reads `AAPL` remain visible
- After step 7: only rows whose `reaction` column reads `chopped` remain visible (or the honest
  "No events match these filters." message if zero rows match that reaction — see UT-06)
- Filtering happens instantly in place, with no page reload and no navigation away from
  `/structure`

---

### UT-06 — Case Studies filter combination with no matches shows an honest message (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Case Studies table is populated with at least one row (UT-03 passed)

**Steps:**
1. Click into the Case Studies "Symbol" field and type a symbol with zero recorded band-touch
   events, e.g. `ZZZNONE`
2. Observe the table area

**Expected Result:**
- The table is replaced with the exact text "No events match these filters."
- Directly below it, the detail text "The registry has rows — this filter combination simply
  matches none." is visible
- No blank area, broken table, or JavaScript error appears

---

### UT-07 — Case Studies shows an honest "unavailable" state when the backend is unreachable (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Requires stopping the backend process temporarily — coordinate before running, and restart the
  backend immediately afterward

**Steps:**
1. Stop the backend process so `http://localhost:8301` no longer responds
2. Navigate to `http://localhost:3301/structure` (a fresh load, so the Case Studies fetch fails)
3. Observe the Case Studies section
4. Restart the backend process

**Expected Result:**
- The Case Studies section shows an amber-bordered panel with a message (either a specific
  backend error, or the fallback text "The case-study registry could not be loaded.")
- Directly below that message, the text "Nothing cached and nothing fabricated is shown in its
  place." is visible
- The section does NOT show a blank area or a raw JavaScript stack trace

---

### UT-08 — Edge Report panel shows its honest current state (kept-surface regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- AAPL as-of `2026-06-22T21:00:00Z` loaded (UT-02)

**Steps:**
1. Scroll down to the "Edge Report" section (below "Case Studies")
2. Inspect its contents

**Expected Result:** exactly one of the following is true (never a blank or endlessly-spinning
panel):
- (a) A "Train" table and a "Hold-out" table are visible, each listing per-cell comparison rows,
  OR
- (b) The text "No edge-report cells yet." is visible, OR
- (c) The text "Edge report not computed yet." is visible next to a button labeled "Compute edge
  report"
- If (c): clicking "Compute edge report" changes its label to "Computing…" and a progress line
  appears — confirms the control is wired up; you do not need to wait for it to finish

---

### UT-09 — Sim cockpit SIM-BUYER watch settles and charts live (kept-surface regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- On a freshly-loaded `http://localhost:3301/`; no ticker currently watched

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Confirm the data-source selector (top of page) shows "Simulated" as the active/highlighted
   mode (it is the default)
3. Click into the ticker field (placeholder "Ticker e.g. SIM-BUYER") and type `SIM-BUYER`
4. Click the green "Watch" button
5. Wait up to 3 seconds

**Expected Result:**
- A panel titled "Tape State" shows the large text "Buyer Control"
- A panel titled "Price Chart — Recorded History + Live Tape" appears above the cockpit grid,
  rendering candlestick bars
- No error banner appears at the top of the page

---

### UT-10 — Cockpit chart timeframe switch re-renders at a new bar width (kept-surface regression)

**Type:** regression
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Cockpit watching `SIM-BUYER` (UT-09 completed)

**Steps:**
1. In the "Price Chart — Recorded History + Live Tape" panel, locate the "Tape" button group
   (buttons "10s", "30s", "60s")
2. Note which button is currently highlighted (default: "10s")
3. Click the "30s" button
4. Observe the chart and the caption text beneath it

**Expected Result:**
- The "30s" button becomes visibly highlighted/pressed and "10s" is no longer
- The chart visibly redraws with wider/fewer candle bars than before
- The caption text below the chart reads "Logical 30s bars built live from the tape."
- No error panel appears

---

### UT-11 — Live tape bars visibly move as new ticks stream in (kept-surface regression)

**Type:** regression
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Cockpit watching `SIM-BUYER` (UT-09 completed); the simulated tape is actively streaming

**Steps:**
1. In the "Price Chart — Recorded History + Live Tape" panel, note the shape/position of the
   rightmost candle bar
2. Wait 5–10 seconds without clicking anything
3. Look at the rightmost candle bar again

**Expected Result:**
- The rightmost candle bar has visibly changed (its high/low/close moved) and/or a new bar has
  appeared to its right — the chart is not frozen
- If a gray "Inside S-band..."/"Inside R-band..." chip is visible beneath the chart, its price
  range text stays the same before and after — the band overlay does not drift
- It is expected (not a defect) that NO band chip appears for `SIM-BUYER` — a simulated ticker has
  no real tradable map, so the muted hint "No tradable map for SIM-BUYER." may show instead

---

### UT-12 — Cockpit Stop button clears the watch (kept-surface regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Cockpit watching `SIM-BUYER` (UT-09 completed)

**Steps:**
1. Locate the "Stop" button in the top bar, next to the text "Watching SIM-BUYER"
2. Click "Stop"

**Expected Result:**
- The page returns to the idle state: the heading "No ticker watched" is visible
- The hint text "Try: SIM-BUYER" is visible below it
- The "Price Chart" panel and the cockpit grid are no longer shown

---

### UT-13 — Top navigation shows exactly "Cockpit" and "Structure" (kept-surface regression)

**Type:** regression
**Priority:** P1
**Surface:** navigation (all pages)

**Preconditions:**
- Frontend running at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Inspect the top navigation bar directly under the "Tapeology" wordmark
3. Count the links/items in it
4. Click "Structure", then click "Cockpit"

**Expected Result:**
- Exactly two nav items are visible: "Cockpit" and "Structure"
- No "Journal", "Studies", or "Performance" link appears anywhere in the nav bar or page
- The nav bar does NOT show the text "navigation unavailable — backend unreachable"
- Clicking "Structure" navigates to `http://localhost:3301/structure`; clicking "Cockpit"
  navigates back to `http://localhost:3301/`

---

### UT-14 — Direct navigation to a deleted route shows a 404, not a stale page (kept-surface regression)

**Type:** regression
**Priority:** P3
**Surface:** `/journal`, `/studies`, `/performance` (deleted routes)

**Steps:**
1. Navigate to `http://localhost:3301/journal`
2. Observe the page
3. Navigate to `http://localhost:3301/studies`
4. Observe the page
5. Navigate to `http://localhost:3301/performance`
6. Observe the page

**Expected Result:**
- All three URLs show Next.js's standard "This page could not be found." 404 page (or equivalent
  not-found page) — never the old Journal/Studies/Performance UI, never a blank white page
- If a nav bar renders on the 404 page, it still reads only "Cockpit" and "Structure"

---

### UT-15 — Framing paragraph reads the exact reinstated Case Studies sentence (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/structure`

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Read the small gray paragraph directly under the page's introductory sentence, below the
   "Structure" heading

**Expected Result:**
- The paragraph reads, in this exact order: "...toggle "Show raw levels" for the underlying S/R
  levels and confluence zones (off by default). Case Studies lists every band-touch event with
  its reaction, forward returns, and — once recorded — its tape timeline; Edge Report compares
  v1, structure_tape, and structure_tape_map over recorded windows..."
- The Case Studies sentence appears immediately before the Edge Report sentence, with no other
  sentence between them

---

### UT-16 — Case Studies is discoverable without developer knowledge (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/structure`

**Steps:**
1. As a first-time visitor with no prior knowledge of this page, navigate to
   `http://localhost:3301/structure`
2. Load symbol `AAPL`, as-of `2026-06-22T21:00:00Z` (type into the fields and click "Load")
3. Scroll down the page from top to bottom, reading section titles only

**Expected Result:**
- A section clearly titled "Case Studies" is reached within a few seconds of scrolling — it sits
  between "Tradable Map"/the raw-levels toggle and "Edge Report"
- Its purpose is clear from its own description text ("Every band-touch event this store has
  scanned...") without needing to ask a developer
- The "Symbol" and "Reaction" filter fields are clearly labeled and their purpose is obvious
  without documentation

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/structure` loads with Case Studies present | smoke | P1 | `/structure` |
| UT-02 | Load AAPL renders candles + wall band | happy-path | P1 | `/structure` |
| UT-03 | Case Studies panel appears, populated | happy-path | P1 | `/structure` |
| UT-04 | Case Studies row opens drill-in | happy-path | P1 | `/structure` |
| UT-05 | Case Studies filters narrow the table | happy-path | P2 | `/structure` |
| UT-06 | Filter combo with no matches → honest message | validation | P2 | `/structure` |
| UT-07 | Case Studies unavailable state when backend down | error | P2 | `/structure` |
| UT-08 | Edge Report shows honest current state | regression | P1 | `/structure` |
| UT-09 | Sim cockpit SIM-BUYER watch + chart | regression | P1 | `/` |
| UT-10 | Cockpit chart timeframe switch | regression | P2 | `/` |
| UT-11 | Live tape bars move as ticks stream | regression | P2 | `/` |
| UT-12 | Cockpit Stop clears the watch | regression | P1 | `/` |
| UT-13 | Nav shows exactly Cockpit + Structure | regression | P1 | nav |
| UT-14 | Deleted routes show 404 | regression | P3 | `/journal`, `/studies`, `/performance` |
| UT-15 | Framing paragraph exact sentence | ux | P2 | `/structure` |
| UT-16 | Case Studies discoverability | ux | P3 | `/structure` |

**P1 tests must all pass for browser QA verdict to be PASS.**

Traceability: UT-01–UT-07 and UT-15–UT-16 cover this iteration's one literal capability change
(phase spec's "New user-facing capability" + TC-10, TC-16). UT-08–UT-13 cover the phase's own
required browser-observable kept-surface regression walk (phase spec / functional-test-plan
TC-4–TC-11), rewritten here at operator-click precision. UT-14 adds a browser-level complement to
TC-12 (the functional test plan's TC-12 only curls the 15 deleted routes and checks the raw HTTP
status; UT-14 checks what a human actually sees in the browser at those same URLs, which the
curl-only check cannot observe). This plan intentionally does NOT duplicate the functional test
plan's remaining API/pytest/grep/artifact-only cases (TC-01, TC-02, TC-03, TC-13–TC-17), which
have no browser-observable surface.
