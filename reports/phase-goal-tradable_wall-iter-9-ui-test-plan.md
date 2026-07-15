# Phase goal-tradable_wall-iter-9 — UI Test Plan

**Phase:** goal-tradable_wall-iter-9
**Date:** 2026-07-15
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Scope

This iteration ships **zero changes under `apps/frontend/`** (confirmed via `git status` in the dev
handoff). The entire diff is a backend result cache (`EdgeReportCache`) wrapped around the existing
`GET /research/edge-report` computation. The **only** thing an operator can observe differently in a
browser is **how long the existing `/structure` Edge Report panel takes to resolve** — the same
markup, same fields, same endpoint, just faster once an operator has warmed the cache once. Everything
else on this test plan is a **regression re-verification** of already-shipped, code-unchanged surfaces
(J-05's page shell, J-06's cockpit chip/overlay), required by this iteration's own TESTING
REQUIREMENTS because they share the `/structure` page with the one thing that did change.

**Two legitimate states this environment may be in when these tests run — both are correct, neither
is a bug:**
1. **Cold** — nobody has ever let a full `GET /research/edge-report` compute finish against the
   backend currently running. This is the expected, unchanged-since-iter-8 state if this is a fresh
   checkout: the panel shows its loading placeholder and stays there (the real corpus takes ~10+
   hours). Per the dev handoff, this was deliberately never triggered during development.
2. **Warm** — either (a) someone previously let a full compute finish and its result is persisted at
   `.data/edge_report_cache.db` (sibling of the dataset directory) or the path named by env var
   `TAPEOLOGY_EDGE_REPORT_CACHE_DB`, surviving backend restarts; or (b) the backend was started
   against a small/scoped dataset directory (env var `TAPEOLOGY_DATASET_DIR`) so its first-ever
   compute finished in well under a minute and was cached the same way. Path (b) is the realistic way
   to actually observe UT-02 (the headline test) inside a normal QA session without waiting out the
   real corpus — the phase spec's own interpretation call treats this keyless warm-cache render as
   part of J-08's required passing bar, distinct from the real ~10+h corpus compute (which is an
   explicit operator-gated carry, out of scope here).

**Not retested here (zero code touched, already covered):**
- The Case Studies row drill-in's full tape-replay (`GET /research/setups/{id}`, ~13–50 minutes
  uncached) — this is iter-8's UT-07, already PASSED with 426 real timeline entries, and this
  iteration's own TESTING REQUIREMENTS scope the J-05 re-verify to the **page shell** (Tradable Map
  default + toggle + Case Studies present), not a fresh drill-in replay. If you want to re-confirm the
  drill-in itself, see `reports/phase-goal-tradable_wall-iter-8-ui-test-plan.md` UT-07.
- Pure backend/API-level determinism, concurrency, durability, and key-busting proofs — these are
  already covered as automated tests in `reports/qa/goal-tradable_wall-iter-9-test-plan.md` (TC-03
  through TC-07) and in the dev's own new `test_edge_report_cache.py` suite. This plan only covers
  what an operator observes in a browser.

**Known, previously-caught trap (do not repeat):** `reports/qa/goal-tradable_wall-iter-8-test-plan.md`
used a fictional tape-state vocabulary (`{INIT, RESTING, TRACKING, TRIGGERED, RESET}`) and confused the
32-hex **dataset** id with the 16-hex **setup/event** id in a `GET /research/setups/{id}` example
(flagged as audit finding T3). The real vocabulary is `{buyer_control, seller_control, bid_absorption,
ask_absorption, unclear}` (rendered Title Case as `Buyer Control` / `Seller Control` / `Bid Absorption`
/ `Ask Absorption` / `Unclear`), and the real route is `GET /research/setups/{setup_id}` where
`setup_id` is a 16-hex event id (e.g. `13e24a2f185b1299`), never the 32-hex dataset id. This plan uses
only click-driven navigation (never a hand-typed id), so this trap does not apply to the steps below,
but is noted here for anyone extending this plan with a direct API call.

<!-- Test IDs use UT-XX prefix to distinguish from the functional test plan's TC-XX IDs. -->
<!-- Each test has exact steps and specific expected results — no vague "test the form" steps. -->

---

## Test Cases

### UT-01 — `/structure` loads with the Edge Report panel visible in its loading state immediately (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at `http://localhost:3301`; backend running at `http://localhost:8301`.
- No login is required anywhere in this app.
- Fresh navigation to `/structure` (a hard reload or new tab) — the Edge Report fetch begins
  automatically the instant the page mounts, exactly as it did before this iteration; no button click
  starts it.

**Steps:**
1. Navigate to `http://localhost:3301/structure`.
2. Wait for the page's initial render to finish (a couple of seconds).
3. Confirm the heading "Structure" (`data-testid="structure-title"`) is visible near the top of the
   page.
4. Scroll down past the "Tradable Map" and "Case Studies" panels to the panel titled "Edge Report".
5. Observe the Edge Report panel for the first 5–10 seconds.

**Expected Result:**
- The "Edge Report" panel (an `<h2>`) is visible with its caption text beginning "The v1 /
  structure_tape / structure_tape_map comparison over recorded event windows…".
- Immediately below that caption, a pulsing gray loading placeholder (`data-testid="edge-report-
  loading"`) is visible — confirming the fetch to `GET /research/edge-report` started automatically.
- No red error banner, no blank white area anywhere on the page.
- Opening the browser DevTools Console shows zero red errors.
- This step alone does not distinguish a warm from a cold cache — both look identical at this instant.
  UT-02 below is what tells them apart.

---

### UT-02 — Warm-cache Edge Report resolves to the full 3-way register within an interactive time budget (happy-path — THE headline J-08 test)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- The edge-report cache is **warm** before this test begins — see Scope above for the two acceptable
  ways to reach this state (a previously-completed real compute now persisted, or a fast compute
  against a scoped-down dataset directory). If this environment is still cold and no fast-path warm-up
  is available, see the Carve-out below instead of attempting to wait out the real ~10+ hour corpus.
- Frontend running at `http://localhost:3301`, pointed at that same warmed backend.

**Steps:**
1. Navigate to `http://localhost:3301/structure` (a fresh navigation/hard reload, so the fetch fires
   from a clean page mount).
2. Scroll to the "Edge Report" panel.
3. Start a stopwatch the moment step 1's navigation begins.
4. Wait for the pulsing gray loading placeholder (`data-testid="edge-report-loading"`) to be replaced
   by real content.
5. Reload the page (F5) once more and repeat the stopwatch measurement.

**Expected Result:**
- The loading placeholder resolves within an interactive time budget — well under a minute, never the
  ~10+ hours the same panel required on every request before this iteration.
- Once resolved, the amber-bordered register banner (`data-testid="edge-report-register"`) reads
  exactly: `simulated — assumed fees/slippage — not indicative of live results`.
- Below it, either:
  (a) two separate table sections labeled "Train" and "Hold-out" (never merged into one table), each
  with columns `strategy | class | side | reaction | feed | n | net R | net $ | win_rate | sample`; or
  (b) if the warmed store genuinely produced no classified scan event, the honest empty state titled
  "No edge-report cells yet." (`data-testid="edge-report-empty"`) — an equally valid, non-failing
  outcome per this project's own anti-goal ("an empty or all-`insufficient_sample` report is an honest,
  valid outcome").
- `data-testid="edge-report-unavailable"` does **not** appear in either outcome.
- Step 5's second reload resolves just as fast as the first — proving this is the durable, persisted
  cache surviving a normal page reload, not a one-off browser-side fluke.

**Carve-out (only if the cache is genuinely cold and no fast-path warm-up per Scope is available in
this environment):** report this test's status as "loading correctly, not yet resolved this session" —
mirroring `reports/phase-goal-tradable_wall-iter-8-ui-test-plan.md`'s UT-13 carve-out — citing UT-01's
evidence that the fetch started correctly. This must never be silently reported as a PASS without an
actually observed fast resolution, and the reason no fast-path warm-up was reachable must be stated
explicitly, not silently omitted.

---

### UT-03 — Populated Edge Report cells honestly label `insufficient sample` vs `ok`, and Train/Hold-out/feed are never pooled (error / anti-goal)

**Type:** error
**Priority:** P1 (inherits UT-02's carve-out if UT-02 did not resolve with populated content)

**Surface:** `/structure`

**Preconditions:**
- UT-02 resolved with outcome (a) — at least one populated row in the Train or Hold-out table. If
  UT-02 instead resolved with outcome (b) (the honest all-empty state), this test has nothing to
  check — record it as vacuously satisfied (the empty state can never mislabel a row that does not
  exist), not as a failure. If UT-02 landed in its carve-out, this test inherits the same carve-out.

**Steps:**
1. With the resolved Edge Report panel from UT-02 still visible, scan the rightmost "sample" column
   of every row in the Train table (`data-testid="edge-report-train-table"`) and the Hold-out table
   (`data-testid="edge-report-holdout-table"`).
2. For each row, compare its "n" column value against its "sample" column value.
3. Confirm "Train" and "Hold-out" render as two visually separate table sections, never merged into
   one combined table.
4. Read the "feed" column value for every visible row in both tables.

**Expected Result:**
- Every row whose `n` is below the report's minimum sample size shows an amber pill
  (`data-testid="edge-report-insufficient-sample"`) reading exactly `insufficient sample (n < 5)`
  (the number matches this report's configured minimum, expected `5`).
- Every row whose `n` meets or exceeds that minimum shows the plain text `ok` in the sample column
  instead — never a blank cell, never a hidden/omitted row.
- "Train" and "Hold-out" are always two distinct tables (even if one individually resolves empty and
  shows "No cells in this split." — `data-testid="edge-report-train-table-empty"` or
  `"edge-report-holdout-table-empty"`).
- Every row's "feed" cell shows exactly **one** feed name (e.g. `sip`) — no cell shows a
  comma-separated or combined list of feeds.

---

### UT-04 — Cold / never-warmed cache shows the honest loading state, never a fabricated or partial result (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- The edge-report cache is deliberately **cold**: point the backend at a fresh, never-used cache path
  (set env var `TAPEOLOGY_EDGE_REPORT_CACHE_DB` to a new, empty temp file path, or delete any existing
  `.data/edge_report_cache.db`) and (re)start the backend so it carries no persisted or in-process
  cache entry.

**Steps:**
1. Navigate to `http://localhost:3301/structure`.
2. Scroll to the "Edge Report" panel.
3. Observe the panel continuously for the first 15–20 seconds without reloading.

**Expected Result:**
- The panel shows `data-testid="edge-report-loading"` (pulsing gray placeholder) and stays in that
  state for the entire observation window — a cold cache always re-triggers the real compute, so this
  is the only correct thing to see this soon after a cold start.
- `data-testid="edge-report-unavailable"` does **not** appear (that state means the backend explicitly
  errored — its fixed reassurance line reads "Nothing cached and nothing fabricated is shown in its
  place." — which is a different situation from "still genuinely computing").
- No table, no row, and no populated register banner text appears yet — nothing partial or fabricated
  is shown while the compute is still running.
- Optional cross-check if backend shell access is available: `curl http://localhost:8301/health`
  continues returning a healthy response throughout, confirming the backend is genuinely still
  computing, not crashed or hung.

---

### UT-05 — Cache correctly invalidates after a dataset or config change; a stale render never lingers (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- A warm cache is already in place (per UT-02).
- Backend-side access to register one additional dataset, or to change a cache-key-affecting config
  field (e.g. `pnl_min_sample_size`) — this step requires backend tooling, not just the browser; an
  operator without backend access cannot execute this test and should skip it (not fail it).

**Steps:**
1. Load `http://localhost:3301/structure` and confirm the Edge Report panel is already resolved
   (populated tables, or "No edge-report cells yet." per UT-02).
2. Note the exact register banner text and the first visible row's values (or the empty-state text) as
   the "before" state.
3. On the backend (outside the browser), register one additional dataset, or change a
   cache-key-affecting config field such as `pnl_min_sample_size`.
4. Reload `http://localhost:3301/structure` (F5).

**Expected Result:**
- After the reload, the Edge Report panel returns to the `data-testid="edge-report-loading"`
  placeholder — it does **not** immediately re-show the exact same "before" content from step 2.
- This confirms the underlying change was not silently ignored by a stale cache: the page never
  continues to show a cached view of the old state after something the report depends on has
  demonstrably changed.

---

### UT-06 — Loading, empty, and populated Edge Report states remain visually distinct (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/structure`

**Preconditions:**
- Able to observe the panel in at least two of its three states (e.g., compare UT-01's loading capture
  against UT-02's resolved capture).

**Steps:**
1. Compare the panel's appearance while loading (the animated pulsing gray placeholder, from UT-01)
   against its appearance once resolved (from UT-02).
2. If either split resolved individually empty, note how "No cells in this split." is displayed
   compared to both the loading placeholder and a populated table.

**Expected Result:**
- The three states — the animated loading skeleton, the honest-empty message, and populated data
  tables — are each visually distinguishable from one another at a glance; an operator unfamiliar with
  this feature can tell which one they are looking at without reading fine print.
- Nothing changed to produce this distinction this iteration (zero frontend files touched) — this test
  simply re-confirms the existing, already-shipped visual language still holds now that the panel can
  actually be observed resolving quickly instead of only ever being seen mid-load.

---

### UT-07 — Case Studies panel still renders its filters and table/empty-state (regression — J-05 page shell)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running.

**Steps:**
1. Navigate to `http://localhost:3301/structure`.
2. Scroll to the panel titled "Case Studies".
3. Confirm a "Symbol" text field (placeholder "e.g. AAPL") and a "Reaction" dropdown (default option
   "All", other options `rejected`/`broke`/`chopped`) are visible above a data area.
4. Type `ZZZZNOPE` into the "Symbol" field.
5. Clear the "Symbol" field back to empty.

**Note:** this test deliberately does **not** click into a row to open the drill-in — that full
tape-replay flow (~13–50 minutes, unchanged since iter-8) is out of this iteration's re-verification
scope (zero code touched; already passing per iter-8's UT-07 evidence — see Scope above).

**Expected Result:**
- Within a few seconds of step 2, the data area resolves to either a populated table (columns `symbol
  | session | band | reaction | forward returns`, `data-testid="case-studies-table"`) or the honest
  message "No band-touch events scanned yet." (`data-testid="case-studies-empty"`) — never a blank
  white area.
- After step 4 (assuming the unfiltered table was non-empty in step 3): the table area shows exactly
  "No events match these filters." with the sub-text "The registry has rows — this filter combination
  simply matches none." (`data-testid="case-studies-no-match"`).
- After step 5: the full unfiltered table (or its honest empty state) returns.
- No console errors at any point.

---

### UT-08 — Tradable Map still defaults correctly and the raw-levels toggle stays off by default (regression — J-05 page shell headline)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running.
- AAPL's bar series has already been recorded through at least 2026-06-18 (established in prior
  iterations).

**Steps:**
1. Navigate to `http://localhost:3301/structure`.
2. Confirm the panel titled "Tradable Map" shows the message "Choose a symbol and an as-of time, then
   Load, to see its tradable level map." (`data-testid="tradable-map-idle"`) before taking any action —
   its default, pre-Load state.
3. Confirm a button reading exactly "Show raw levels" is visible (`data-testid="raw-levels-toggle"`) —
   **not** "Hide raw levels" — proving the raw-levels view is off by default.
4. Type `AAPL` into the "Symbol" field near the top of the page, type `2026-06-22T21:00:00Z` into the
   "As-of (UTC, ISO-8601)" field (`data-testid="structure-as-of-input"`), then click the "Load" button
   (`data-testid="structure-load-button"`). (This exact as-of value is the one iter-7's own browser QA
   independently verified against this same pinned case.)
5. Wait for the Tradable Map panel to resolve (a few seconds).

**Expected Result:**
- A line reading "Map basis (prior completed session close): 2026-06-18T04:00:00.000000Z"
  (`data-testid="tradable-map-basis"`) appears — confirming the morning-markup basis is the PRIOR
  session's close, never same-session data.
- The Tradable Map panel shows a table (`data-testid="tradable-map-table"`, columns `side | range |
  class | score | members`, plus a trailing round-number-flag column) listing **10 or fewer rows
  total** (the goal's own acceptance cap is `≤10`; iter-7's own browser QA independently observed
  exactly 10 rows — 5 resistance + 5 support — for this exact pinned case, so expect that same count
  here absent any data change).
- At least one row's "range" column (`data-testid="tradable-band-range"`) spans a value between
  roughly 300 and 302 (the pinned resistance band), with its "class" column
  (`data-testid="tradable-band-class"`) reading "Class A".
- The "Show raw levels" button from step 3 is **still** visible reading "Show raw levels" (not
  auto-flipped to "Hide raw levels") — loading the Tradable Map never changes the toggle's own state.
- The candlestick chart above the table renders with solid (not dashed) band lines, without a console
  error.

---

### UT-09 — Raw-levels toggle still reveals the pre-existing all-levels view, unchanged from before this iteration (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Continue directly from UT-08 (AAPL 2026-06-22 already loaded).

**Steps:**
1. Click the "Show raw levels" button.
2. Observe the newly-revealed section.
3. Click the same button again (it now reads "Hide raw levels").

**Expected Result:**
- After step 1, the button's label flips to "Hide raw levels", and a section titled "Price chart —
  S/R levels" plus a "Confluence zones" panel appears below it, showing the full pre-J-05 raw-levels
  view (`aria-label="Levels and zones"`).
- After step 3, the button flips back to "Show raw levels" and the raw-levels section disappears — the
  Tradable Map section above is unaffected throughout.

---

### UT-10 — Cockpit: SIM honest empty state and Live-mode hiding remain unregressed (regression — J-06)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running.
- No watch currently active (fresh page load).

**Steps:**
1. Navigate to `http://localhost:3301/`.
2. Confirm the "Simulated" button in the data-source control (top area, beside the "Tapeology"
   wordmark) is already selected/highlighted by default.
3. Type `SIM-BUYER` into the field labeled "Ticker" (placeholder "Ticker e.g. SIM-BUYER"), then click
   the "Watch" button.
4. Wait a few seconds for the "Price Chart — Tape-State Markers" panel to render its chart.
5. Click the "Stop" button (`aria-label="Stop watching"`), then click "Live", type `AAPL` into the
   symbol field, and click "Watch".
6. Scroll the full page top to bottom.

**Expected Result:**
- After step 4: a candlestick chart renders inside "Price Chart — Tape-State Markers"; directly below
  it, a small gray line of text reads exactly `No tradable map for SIM-BUYER.`
  (`data-testid="no-tradable-map"`) — SIM tickers never have a tradable map, so no colored band
  overlay line and no confluence chip (`data-testid="confluence-chip"`) appear.
- After step 6 (Live mode): no section or panel titled "Price Chart — Tape-State Markers" appears
  anywhere on the page — the entire component (chart, band overlay, chip) is completely absent, exactly
  as before this iteration.
- The nav bar at the top still reads exactly "Cockpit, Journal, Studies, Performance, Structure" (5
  items, unchanged) — no new entry was added for this iteration's cache work.
- No console errors at any point in this test.

---

### UT-11 — Historical AAPL replay still shows the tradable-band overlay and a descriptive-only confluence chip (regression — J-06, credentialed)

**Type:** regression
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Real market-data credentials already configured on this backend (established in prior iterations).
- AAPL's bar series has already been recorded through at least 2026-06-18.
- No watch currently active.

**Steps:**
1. Navigate to `http://localhost:3301/`.
2. Click the "Historical" button in the data-source control.
3. Type `AAPL` into the "Symbol search" field; type a date resolving to the 2026-06-22 session into
   the "Date" field.
4. Choose a time-window preset that does **not** trigger the app's own high-volume guard (e.g. an
   "Open 9:30 ET"-style preset rather than the full RTH 9:30–16:00 window, which this app refuses with
   its own unrelated "try a shorter range" guard).
5. Click "Watch".
6. Wait a few seconds for the chart to render, then look for colored horizontal band lines on the
   chart and, if present, a chip banner directly below the chart.

**Expected Result:**
- The candlestick chart and tape-state markers render normally.
- If a band-overlay line is visible, its price-axis label reads a form like `R class A · score
  {number}` (optionally ending `· round`, with no trailing price value after the word "round") — e.g.
  iter-7's own verified real example: `R class A · score 153 · round`. No prediction language
  anywhere.
- If a confluence chip banner (`data-testid="confluence-chip"`) is visible, its text reads the exact
  form `Inside {R|S}-band {low}–{high} (class {X}) · tape: {State Label} ({rejection|breakthrough}) ·
  measured history: edge report` (no trailing period) — e.g. iter-7's own verified real example:
  `Inside R-band 300.17–302.27 (class A) · tape: Seller Control (breakthrough) · measured history:
  edge report`. Containing no "buy", "sell", "should", "will", "target", "recommend", or
  dollar/percentage prediction language anywhere.
- This confirms the chip/overlay rendering and copy are unchanged from before this iteration (zero
  code touched in `PriceChart.tsx` or `tradability.py` this iteration).

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/structure` loads, Edge Report loading state visible immediately | smoke | P1 | `/structure` |
| UT-02 | Warm-cache Edge Report resolves within interactive time (headline) | happy-path | P1 | `/structure` |
| UT-03 | Populated cells honestly label `insufficient sample`/`ok`, no pooling | error | P1 | `/structure` |
| UT-04 | Cold/never-warmed cache shows honest loading, never fabricated | error | P2 | `/structure` |
| UT-05 | Cache busts after dataset/config change, no stale render lingers | validation | P2 | `/structure` |
| UT-06 | Loading/empty/populated Edge Report states visually distinct | ux | P3 | `/structure` |
| UT-07 | Case Studies filters + table/empty-state unregressed | regression | P1 | `/structure` |
| UT-08 | Tradable Map default + raw-toggle off by default unregressed | regression | P1 | `/structure` |
| UT-09 | Raw-levels toggle reveals unchanged pre-existing view | regression | P2 | `/structure` |
| UT-10 | Cockpit SIM honest empty state + Live-mode hiding unregressed | regression | P1 | `/` |
| UT-11 | Historical AAPL band overlay + confluence chip unregressed | regression | P2 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-02 carries an explicit,
project-documented carve-out (see its own Expected Result) mirroring iter-8's UT-13: a "not yet
resolved this session" outcome is acceptable ONLY if genuinely no fast-path warm-up (per Scope) was
reachable in this environment — it must never be silently reported as a PASS without an actual observed
fast resolution, and must never be skipped without an explicit note of why. UT-03 inherits the same
carve-out when it depends on UT-02 having resolved with populated content.
