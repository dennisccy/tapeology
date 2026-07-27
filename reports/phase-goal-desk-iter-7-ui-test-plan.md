# Phase goal-desk-iter-7 — UI Test Plan

**Phase:** goal-desk-iter-7
**Date:** 2026-07-26
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301 (backend at http://localhost:8301)

---

## Scope note

This iteration ships no new page, panel, button, or route. Two things change that are testable
from a browser:

1. **Audit finding F2 (the hover-honesty fix).** On `/desk`, hovering a ranked or skipped row's
   drill-in anchor (`desk-row-drill-in` / `desk-skip-row-drill-in`, the `absolute inset-0` link
   that fills the whole row) now shows one composite tooltip carrying the row's full-precision
   `distance_bps`, full `band_score`, and each coverage timeframe's `latest_window_end_utc` — detail
   that used to live on several small per-cell `title`s but became pointer-unreachable once the
   drill-in anchor started covering the whole row. **Zero change** was made to the anchor's `href`,
   `absolute inset-0` class, or `data-testid` — this is the load-bearing constraint the tests below
   must protect (a click anywhere in the row must still navigate exactly as it did before this
   iteration).
2. **J-07 — the era's closing kept-product regression walk.** No code was added for this; it is a
   full browser pass over the Cockpit and Structure pages that have been shipped since earlier
   iterations, plus a check of the persistent nav. This is the primary evidence the era needs before
   it can be evaluated for closure, so the walk's exact steps are included below in full (UT-08
   through UT-12), not just referenced.

The second new capability this iteration adds — `desk_universe`/`desk_screen` as MCP tools — has no
browser surface (it is reachable only from a Claude/MCP conversation) and is excluded from this
plan; it is covered by `test_mcp_server.py`'s byte-identity tests in the functional test plan.

**Fixture data used throughout this plan** (present in the ambient store as of this writing; a
browser-QA pass MUST use a throw-away fixture-scoped copy, never the operator's real
`apps/backend/.data/` — same discipline as prior iterations):
- Two recorded screens exist: **2026-06-22** (the older one, NOT latest) and **2026-07-25** (the
  latest). The Screen History table shows both.
- History row **2026-06-22**, selected via the "Screen History" table: 10 ranked rows, 91 skipped
  rows, `as_of = 2026-06-22T23:59:59Z`.
  - Ranked row 1 = **AAPL**: side `resistance`, `band_class A`, `distance_bps
    0.33523150389608725`, `band_score 97`, `price_low 298.02`, `price_high 300.1001`, coverage
    `1h`/`4h`/`1d`/`1w` all `has_bars: true` with `latest_window_end_utc: "2026-07-23"` on every
    timeframe.
    - Its composite drill-in tooltip (the F2 fix's exact output) reads:
      `distance 0.33523150389608725 bps · score 97 · 1h window last requested: 2026-07-23 · 4h
      window last requested: 2026-07-23 · 1d window last requested: 2026-07-23 · 1w window last
      requested: 2026-07-23`
    - Its DISPLAYED (rounded) cells read `0.34 bps` (distance) and `97.00` (score) — the rounded
      display is unchanged by this iteration; only the full-precision detail's location moved.
  - Skipped row 1 = **ABBV**, reason `no_bars`, coverage `1h`/`4h`/`1d`/`1w` all `has_bars: false`
    with `latest_window_end_utc: null` on every timeframe.
    - Its composite drill-in tooltip reads:
      `1h window last requested: never · 4h window last requested: never · 1d window last
      requested: never · 1w window last requested: never`
      — no `distance`/`score` segment at all (a skipped member has neither field).
- Structure page fixture: **AAPL as-of `2026-06-22T21:00:00Z`** renders a tradable band whose range
  includes the value **`300.11`** (the pinned 300–302.4-region wall this era's browser passes have
  used since iteration 4).

**A note on native tooltips.** The composite `title` is a plain HTML attribute, rendered by the
browser's own OS-level tooltip — not a custom on-page element. It can be slow or inconsistent to
capture in a screenshot (some browsers wait ~1–1.5s before showing it, and Chrome MCP's synthetic
hover does not always trigger it the same way a real mouse does). Wherever a test below asks you to
verify tooltip text, BOTH of these count as valid evidence:
- A screenshot clearly showing the OS tooltip text after hovering and waiting at least 1.5 seconds, OR
- Inspecting the anchor element's `title` attribute value directly (browser DevTools Elements panel,
  or a DOM/attribute query) — this is the more reliable method and should be preferred when the
  visual tooltip does not reliably screenshot.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/desk` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Frontend running at http://localhost:3301, backend at http://localhost:8301
- Backend has at least one recorded desk screen (the ambient store already has
  `screen-2026-06-22` and `screen-2026-07-25`)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Wait for the page to finish loading (the pulsing loading skeleton, `data-testid="desk-screen-loading"`, disappears)

**Expected Result:**
- Page renders without a blank screen or crash
- The heading "Desk" is visible (`data-testid="desk-title"`)
- A "Provenance" panel, a "Briefing" panel, a "Skipped Members" panel, and a "Screen History"
  panel are all visible, in that order
- No browser console errors

---

### UT-02 — Hovering a ranked row shows the full composite tooltip on the drill-in anchor (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded and showing either screen; the "Screen History" table is visible
- Backend has `screen-2026-06-22` recorded (fixture-scoped copy — see Scope note)

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. In the "Screen History" table (`data-testid="desk-history-table"`), click the row whose "date"
   column reads exactly `2026-06-22` (`data-testid="desk-history-row"` with
   `data-screen-date="2026-06-22"`)
3. Wait for the "Viewing the recorded screen for 2026-06-22 — not the latest." banner to appear
   (`data-testid="desk-viewing-indicator"`)
4. In the "Briefing" table, find the row whose "symbol" column reads `AAPL`
   (`data-testid="desk-screen-row"` with `data-symbol="AAPL"`)
5. Move the mouse pointer to hover over the row's "side" cell (`data-testid="desk-row-side"`, the
   cell reading `resistance`) — deliberately NOT the small distance or score numbers, to prove the
   tooltip is reachable from a plain cell that carries no `title` of its own
6. Wait at least 1.5 seconds, then capture the tooltip (screenshot, or inspect the row's
   `data-testid="desk-row-drill-in"` anchor's `title` attribute directly — see the Scope note above)

**Expected Result:**
- The tooltip/attribute text is exactly:
  `distance 0.33523150389608725 bps · score 97 · 1h window last requested: 2026-07-23 · 4h window
  last requested: 2026-07-23 · 1d window last requested: 2026-07-23 · 1w window last requested:
  2026-07-23`
- The tooltip appears from hovering the "side" cell (not just the distance/score numbers), proving
  the whole row now carries the detail, not just a few small spots

---

### UT-03 — Hovering a skipped row's tooltip shows only coverage, never a fabricated distance/score (validation)

**Type:** validation
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- Continuing from UT-02 (the 2026-06-22 screen is displayed) or freshly navigated and the
  2026-06-22 history row re-selected
- The "Skipped — no bars (91)" section is visible with `ABBV` as its first row

**Steps:**
1. In the "Skipped Members" section, find the row whose "symbol" column reads `ABBV`
   (`data-testid="desk-skip-row"` with `data-symbol="ABBV"`)
2. Move the mouse pointer to hover anywhere within that row (e.g. over the "reason" cell reading
   `no bars`)
3. Wait at least 1.5 seconds, then capture the tooltip (screenshot, or inspect the row's
   `data-testid="desk-skip-row-drill-in"` anchor's `title` attribute directly)

**Expected Result:**
- The tooltip/attribute text is exactly:
  `1h window last requested: never · 4h window last requested: never · 1d window last requested:
  never · 1w window last requested: never`
- The text does NOT contain the word "distance" or "score", and does NOT contain any numeric
  distance/score value — a skipped member has neither field, and the tooltip must not invent one

---

### UT-04 — Clicking anywhere in a ranked row still navigates to `/structure`, anchor markup unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → `/structure`

**Preconditions:**
- The 2026-06-22 screen is displayed on `/desk` (repeat UT-02 steps 1–2 first if starting fresh)
- The AAPL ranked row is visible

**Steps:**
1. Before clicking, inspect the AAPL row's `<Link data-testid="desk-row-drill-in">` element (e.g.
   via DevTools) and note its `href` and `className`
2. Click anywhere in the AAPL row EXCEPT the symbol text itself — e.g. click on the "band-class"
   cell reading "Class A" (`data-testid="desk-row-band-class"`), to prove the whole row (not just
   the symbol) is still the click target
3. Wait for the browser to navigate and the new page to finish loading

**Expected Result:**
- The anchor's `href` was `/structure?symbol=AAPL&asof=2026-06-22T23%3A59%3A59Z` (or the
  unescaped-colon equivalent) and its `className` included `absolute inset-0` — both byte-unchanged
  from before this iteration
- The browser navigates to that same URL; the address bar shows
  `http://localhost:3301/structure?symbol=AAPL&asof=2026-06-22T23:59:59Z` (colon may show
  URL-escaped as `%3A`)
- The Symbol field shows "AAPL" and the "As-of (UTC, ISO-8601)" field
  (`data-testid="structure-as-of-input"`) shows exactly `2026-06-22T23:59:59Z` — no manual click on
  "Load" was needed
- The Tradable Map panel shows a populated bands table (`data-testid="tradable-map-table"`), not an
  empty/idle state

---

### UT-05 — Clicking anywhere in a skipped row still navigates to `/structure`, anchor markup unchanged (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk` → `/structure`

**Preconditions:**
- The 2026-06-22 screen is displayed on `/desk`, with `ABBV` visible in the "Skipped — no bars (91)"
  section

**Steps:**
1. Before clicking, inspect the ABBV row's `<Link data-testid="desk-skip-row-drill-in">` element
   and note its `href` and `className`
2. Click anywhere in the ABBV row except the symbol text — e.g. click on the "reason" cell reading
   "no bars" (`data-testid="desk-skip-reason"`)
3. Wait for the browser to navigate and the new page to finish loading

**Expected Result:**
- The anchor's `href` was `/structure?symbol=ABBV&asof=2026-06-22T23%3A59%3A59Z` (or unescaped) and
  its `className` included `absolute inset-0` — byte-unchanged from before this iteration
- The browser navigates to `http://localhost:3301/structure?symbol=ABBV&asof=2026-06-22T23:59:59Z`
- The Symbol field shows "ABBV"; the page does not crash and does not show a blank page
- The Tradable Map panel shows the honest empty state — `data-testid="tradable-map-no-bar-series"`
  ("No bar series recorded for ABBV.") — never a fabricated band

---

### UT-06 — `/desk` rows look unchanged at rest; the tooltip only appears on hover (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded, showing a populated screen (latest or the 2026-06-22 history selection)

**Steps:**
1. Navigate to `http://localhost:3301/desk` and let the page settle, mouse pointer resting outside
   the Briefing/Skipped tables entirely (e.g. over the page's left margin)
2. Take a screenshot of the Briefing and Skipped Members tables
3. Compare against the row layout described in the surface map: symbol / side / class / distance /
   score / coverage badges / tick-evidence columns, in that order, same cell text and badge colors
   as before this iteration

**Expected Result:**
- No visible tooltip, popup, or layout shift is present anywhere on the page while the mouse is not
  hovering a row
- The table's columns, row heights, badge colors, and cell text are visually identical to the
  pre-iteration shape — the ONLY difference this iteration makes is reachable exclusively through
  hovering, never visible "at rest"

---

### UT-07 — Screen History still selects the row by date, not by table position (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/desk`

**Preconditions:**
- `/desk` loaded, showing the "Screen History" table with both `2026-06-22` and `2026-07-25` rows
  visible

**Steps:**
1. Navigate to `http://localhost:3301/desk`
2. Note which row is listed FIRST in the "Screen History" table (by default DOM/render order — do
   not assume it is `2026-06-22`)
3. Click the row whose "date" column reads exactly `2026-06-22`, regardless of whether it is first
   or second in the table
4. Wait for the page to re-render

**Expected Result:**
- The banner reads exactly "Viewing the recorded screen for 2026-06-22 — not the latest."
- The clicked row (`data-testid="desk-history-row"` with `data-screen-date="2026-06-22"`) shows
  `data-selected="true"`
- The Briefing table's first row shows symbol `AAPL` — confirming the click selected the row by its
  own `data-screen-date` attribute, not by its position in the table (this protects the golden fix
  to `journey-scripts/J-05.json` step 2)

---

### UT-08 — Cockpit: watching SIM-BUYER settles the "Buyer Control" readout (regression — kept product)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Cockpit)

**Preconditions:**
- Frontend running at http://localhost:3301, backend running at http://localhost:8301
- No prior watch active (fresh page load)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. In the data-source selector (`role="group"`, `aria-label="Data source"`), click the button
   labeled exactly "Simulated" (it is the default-active mode, but click it explicitly)
3. Type `SIM-BUYER` into the ticker field (`aria-label="Ticker"`, placeholder "Ticker e.g.
   SIM-BUYER")
4. Click the "Watch" button (the submit button reading exactly "Watch")
5. Wait until the "Connecting to SIM-BUYER…" acknowledgement (`data-testid="connecting-state"`) and
   any `data-testid="waiting-state"` panel are both gone

**Expected Result:**
- The panel grid renders with a "Tape State" panel showing the large bold text "Buyer Control" (not
  "Connecting…", not "Waiting for the first trade…", and not the amber "Warming up — collecting
  tape data…" sub-line)
- The status dot in the top bar reads "live" (green dot, label "live")
- A screenshot at this point shows the full settled panel grid: Tape State, Quote, Features, Recent
  Trades, Observations, and Event Log panels all visibly populated (not blank, not a spinner)

---

### UT-09 — Structure: Load AAPL as-of 2026-06-22T21:00:00Z renders the pinned wall (regression — kept product)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running; AAPL's recorded bars for this era's pinned window are present in
  the backend's data store

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. In the "Symbol" field (`aria-label="Structure symbol"`), type `AAPL`
3. In the "As-of (UTC, ISO-8601)" field (`data-testid="structure-as-of-input"`), type
   `2026-06-22T21:00:00Z`
4. Click the "Load" button (`data-testid="structure-load-button"`)
5. Wait up to 20 seconds for the Tradable Map panel to populate, then wait an additional 4 seconds
   for the chart to finish drawing

**Expected Result:**
- The Tradable Map panel shows a populated bands table (`data-testid="tradable-map-table"`)
  containing the text `300.11` (the pinned wall's band boundary)
- The chart caption (`data-testid="tradable-map-chart-caption"`) also shows the text `300.11`
- The chart canvas (inside `data-testid="structure-chart-canvas"`) renders an actual `<canvas>`
  element — not a blank area or an error message

---

### UT-10 — Structure: Case Studies drill-in opens and renders (regression — kept product)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Continuing from UT-09 (AAPL as-of 2026-06-22T21:00:00Z already loaded) — the Case Studies
  section's registry is populated for AAPL, or filter by symbol `AAPL` if the unfiltered registry
  has rows for other symbols first

**Steps:**
1. Scroll down to the "Case Studies" panel
2. If the table (`data-testid="case-studies-table"`) has more than one row, optionally type `AAPL`
   into the "Symbol" filter field (`data-testid="case-studies-filter-symbol"`) to narrow it
3. Click anywhere on a row in the table (`data-testid="case-studies-row"`)
4. Wait for the drill-in to render inline below the table

**Expected Result:**
- A new sub-panel titled "Case Studies — drill-in" appears directly below the table, inside the
  same "Case Studies" panel (NOT a separate page or a modal)
- The drill-in content (`data-testid="case-drillin"`) shows symbol/session, band, a "reaction" value
  (`data-testid="case-drillin-reaction"`), forward returns, and a "Tape timeline" sub-section
  showing either a populated list (`data-testid="case-drillin-tape-timeline"`) or the honest text
  "No recorded tape for this event." (`data-testid="case-drillin-tape-timeline-empty"`)
- The clicked row shows a highlighted background (its `aria-selected` attribute is `true`)

---

### UT-11 — Structure: Edge Report panel renders its honest computed-or-not-computed state (regression — kept product)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- `/structure` loaded (with or without a symbol loaded — the Edge Report panel is not
  symbol-scoped)

**Steps:**
1. Scroll down to the "Edge Report" panel
2. Observe its current state without clicking anything

**Expected Result:** exactly ONE of the following two honest states is shown — never a blank panel,
never a fabricated cell, never a raw error dump:
- **Not yet computed**: an amber panel (`data-testid="edge-report-not-computed"`) with the text
  "Edge report not computed yet." followed by a detail line, and a button reading "Compute edge
  report" (`data-testid="edge-report-compute-button"`) — do NOT click this button (triggering a
  compute is a write action and is out of scope for this regression check)
- **Computed**: a register line (`data-testid="edge-report-register"`) followed by either
  "Train"/"Hold-out" cell tables (`data-testid="edge-report-train-table"` /
  `edge-report-holdout-table"`) or, if both splits are empty, the honest text "No edge-report cells
  yet." (`data-testid="edge-report-empty"`)

Take a screenshot of whichever state is showing.

---

### UT-12 — Nav shows exactly three routes: Cockpit, Structure, Desk (ux)

**Type:** ux
**Priority:** P2
**Surface:** nav (all pages)

**Preconditions:**
- Frontend and backend running

**Steps:**
1. Navigate to `http://localhost:3301/` (or any page — the nav bar is persistent)
2. Look at the top navigation bar (`data-testid="app-nav"`)
3. Count the visible links and read their text

**Expected Result:**
- Exactly three links are visible, reading exactly "Cockpit", "Structure", and "Desk" (each
  `data-testid="nav-link"`, distinguished by `data-label`), in that order
- No `data-testid="nav-unavailable"` degraded-state message is shown
- Clicking "Desk" navigates to `http://localhost:3301/desk` and highlights that link as active

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/desk` loads without errors | smoke | P1 | `/desk` |
| UT-02 | Hovering ranked row shows full composite tooltip | happy-path | P1 | `/desk` |
| UT-03 | Hovering skipped row shows coverage-only, no fabrication | validation | P1 | `/desk` |
| UT-04 | Ranked row click still navigates, anchor unchanged | regression | P1 | `/desk` → `/structure` |
| UT-05 | Skipped row click still navigates, anchor unchanged | regression | P1 | `/desk` → `/structure` |
| UT-06 | Rows unchanged at rest; tooltip is hover-only | ux | P2 | `/desk` |
| UT-07 | History selects by date, not table position | regression | P1 | `/desk` |
| UT-08 | Cockpit: SIM-BUYER settles to "Buyer Control" | regression | P1 | `/` |
| UT-09 | Structure: Load AAPL as-of 2026-06-22 renders wall | regression | P1 | `/structure` |
| UT-10 | Structure: Case Studies drill-in opens and renders | regression | P1 | `/structure` |
| UT-11 | Structure: Edge Report honest state renders | regression | P1 | `/structure` |
| UT-12 | Nav shows exactly 3 routes | ux | P2 | nav |

**P1 tests must all pass for browser QA verdict to be PASS.**
