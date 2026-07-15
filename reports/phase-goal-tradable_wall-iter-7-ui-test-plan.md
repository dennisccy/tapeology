# Phase goal-tradable_wall-iter-7 — UI Test Plan

**Phase:** goal-tradable_wall-iter-7
**Date:** 2026-07-15
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Scope

This iteration is pure-frontend and touches exactly one route, the cockpit (`/`), plus a
regression-only smoke check of `/structure`. It adds three new display elements to the existing
"Price Chart — Tape-State Markers" panel: a tradable-band overlay, a descriptive confluence chip
(`data-testid="confluence-chip"`), and an honest "no tradable map" empty hint
(`data-testid="no-tradable-map"`). No new page, no new nav entry, no new button/form/control — this
is a display-only addition. Test cases below are grouped by the UI surface map row they verify.

API-level checks that do not require a browser (mapping-driven confirmation via direct endpoint
calls, no-lookahead `as_of` instrumentation, backend suite / `config_fingerprint` / `tsc` / copy-lint
checks) are already covered in `reports/qa/goal-tradable_wall-iter-7-test-plan.md` (TC-07, TC-08,
TC-11 through TC-16) and are **not** duplicated here — this plan covers only what an operator
observes in the browser.

<!-- Test IDs use UT-XX prefix to distinguish from the functional test plan's TC-XX IDs. -->
<!-- Each test has exact steps and specific expected results — no vague "test the form" steps. -->

---

## Test Cases

### UT-01 — Cockpit loads with the Price Chart panel visible in Simulated mode (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend running at `http://localhost:3301`; backend running at `http://localhost:8301`.
- No login is required anywhere in this app.
- No watch is currently active (fresh page load).

**Steps:**
1. Navigate to `http://localhost:3301/`.
2. Wait for the page to finish loading.
3. Confirm the "Simulated" button in the data-source control (top-left of the header, beside the
   "Tapeology" wordmark) is highlighted as selected by default.
4. Type `SIM-BUYER` into the field labeled "Ticker" (placeholder "Ticker e.g. SIM-BUYER").
5. Click the "Watch" button.

**Expected Result:**
- No red error banner appears below the header.
- Within a few seconds a panel titled "Price Chart — Tape-State Markers" appears on the page.
- Inside that panel, three bar-size buttons are visible reading "10s", "30s", "60s" — "10s" is
  highlighted as the selected one.
- A candlestick chart begins rendering below the bar-size buttons.
- Opening the browser DevTools Console shows zero red errors.

---

### UT-02 — SIM-BUYER shows the honest "no tradable map" hint, never a fabricated band (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Same as UT-01. Can continue directly from UT-01's watched SIM-BUYER session.

**Steps:**
1. Navigate to `http://localhost:3301/` (or continue from UT-01).
2. Confirm "Simulated" is selected in the data-source control; click it if not.
3. Type `SIM-BUYER` into the "Ticker" field.
4. Click "Watch".
5. Wait 5 seconds for the chart and the bands request to resolve.
6. Look directly below the chart canvas, still inside the "Price Chart — Tape-State Markers" panel.

**Expected Result:**
- The candlestick chart and its tape-state markers render normally, unaffected.
- Zero colored horizontal band lines are drawn on the chart (no rose or emerald solid lines).
- A small slate-gray line of text reading exactly `No tradable map for SIM-BUYER.` appears directly
  below the chart.
- No confluence chip (no slate-gray banner starting with "Inside R-band" or "Inside S-band") is
  present anywhere in the panel.

---

### UT-03 — Tradable-band overlay renders on the cockpit chart during a real historical replay (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running.
- Real market-data credentials are already configured on the backend in this environment (confirmed
  present via `docs/handoffs/goal-tradable_wall-iter-7-dev.md`'s Live Verification section —
  `GET /market/clock` returns `available: true`).
- AAPL's bar series has already been recorded through at least 2026-06-18 (established in prior
  iterations) — required for `/research/tradability` to resolve a non-empty band map.
- No watch is currently active.

**Steps:**
1. Navigate to `http://localhost:3301/`.
2. Click the "Historical" button in the data-source control.
3. Type `AAPL` into the field labeled "Symbol search" (placeholder "Symbol e.g. AAPL").
4. Type `22-06-2026` into the field labeled "Date" (placeholder "dd-MM-yyyy").
5. Click the button starting with "Full RTH 9:30–16:00 ET" (it may show an additional local-time
   annotation in parentheses once the date is entered — that is expected; it fills the Start/End
   time fields automatically).
6. Change the "Replay speed" dropdown from "1×" to "10×".
7. Click "Watch".
8. Wait up to 30 seconds for the chart to render candles and for the band overlay to load.

**Expected Result:**
- The "Price Chart — Tape-State Markers" panel shows candlesticks in the $297–$300 range.
- At least one **solid** (not dashed) horizontal price line is drawn on the chart near the $300
  level.
- The line is rose-colored if it is a resistance band, or emerald-colored if support.
- Hovering near the line's price-axis label shows text of the form
  `{R|S} class {A/B/C} · score {number}[ · round]` — e.g. the last-verified reference reading was
  `R class A · score 153 · round` near 300.17. Treat any similarly-structured label near the $300
  level as a pass; the exact score number may drift as the underlying data store changes (a
  documented, expected behavior from this project's own prior iteration — do not fail the test over
  a different score number alone).
- This solid line is visually distinguishable from any dashed thesis price-line also present.

---

### UT-04 — Confluence chip appears at a real price-in-band + matching-tape-state moment (happy-path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Same as UT-03; continue the same AAPL Historical watch from UT-03 (do not click Stop).

**Steps:**
1. With the AAPL 2026-06-22 replay from UT-03 still running at "10×" speed, keep the tab open and
   watch the chart.
2. Watch for up to 5 minutes as the replay progresses and price moves in and out of the drawn
   band(s).
3. Each time price is inside a drawn band, check directly below the chart canvas for a new
   slate-gray banner.

**Expected Result:**
- At some point while the last traded price sits inside a drawn band **and** the tape-state reading
  (visible elsewhere in the cockpit's tape-state panel) matches that band's configured confirming
  state, a chip (`data-testid="confluence-chip"`) appears below the chart reading in the exact form:
  `Inside {R|S}-band {low}–{high} (class {X}) · tape: {State Label} ({rejection|breakthrough}) ·
  measured history: edge report.` — e.g. `Inside R-band 300.05–300.17 (class A) · tape: Ask
  Absorption (rejection) · measured history: edge report.`
- The chip text contains no buy/sell/prediction language — only a description of the current
  condition.
- The chip disappears again once price exits the band or the tape state changes to `unclear` or an
  unmapped state.

**If the chip does not appear within the 5-minute window:** this is a known timing-dependent
condition, not necessarily a defect — per `docs/handoffs/goal-tradable_wall-iter-7-dev.md`'s "Known
Issues" section, the developer's own live verification session also did not personally catch the
exact firing moment during this same replay. Do not report an outright FAIL on this basis alone.
Instead: (a) restart the replay targeting a narrower window closer to a touch of the ~300 level, or
re-run at a different replay speed to change the sampling of tape-state transitions; and (b) if still
not observed after a second attempt, report honestly as "not yet observed this session," citing
UT-03's overlay evidence and the 9 keyless source-inspection tests in
`apps/backend/tests/test_price_chart_confluence.py` as the structural evidence the mechanism is
wired correctly. Never fabricate or narrate a chip screenshot that was not actually captured.

---

### UT-05 — Confluence chip absent when price is outside every band (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Same AAPL Historical watch as UT-03 (or a fresh one set up the same way).

**Steps:**
1. Watch the AAPL 2026-06-22 replay at a moment early in the session when price is still below
   $298 — well outside the ~$300 band drawn in UT-03.
2. Look directly below the chart canvas.

**Expected Result:**
- The band overlay line(s) remain visible on the chart, unaffected.
- No confluence chip (`data-testid="confluence-chip"`) is present below the chart while price sits
  outside every drawn band.

---

### UT-06 — Confluence chip absent when the tape state is unclear or unmapped (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Same AAPL Historical watch, at a moment where price **is** inside a drawn band (per UT-03) but the
  tape-state indicator elsewhere in the cockpit currently reads a state other than the two states
  mapped to that band's side (most reliably: `Unclear`).

**Steps:**
1. Watch the replay until price is inside a drawn band.
2. Check the tape-state indicator elsewhere in the cockpit (the tape-state panel).
3. The moment it reads "Unclear" (or any state not matching this band's mapped rejection/breakthrough
   state) while price is still inside the band, look directly below the chart canvas.

**Expected Result:**
- No confluence chip is present, even though price is inside a band, because the tape-state half of
  the display conjunction is not satisfied.
- The band overlay line remains visible, unaffected.

---

### UT-07 — A bands/strategies fetch failure never blocks the chart or crashes the page (error)

**Type:** error
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Frontend and backend running.
- Chrome DevTools available.

**Steps:**
1. Navigate to `http://localhost:3301/`.
2. Open DevTools → Network tab. Reload once so requests are visible, then right-click any request
   and choose "Block request URL," adding a rule matching `research/tradability`.
3. Select "Simulated" mode, type `SIM-BUYER` into "Ticker", click "Watch".
4. Observe the chart and the Console tab for 10 seconds.
5. Remove the block rule afterward so later tests are unaffected.

**Expected Result:**
- The candlestick chart and tape-state markers render exactly as in UT-01/UT-02, completely
  unaffected by the blocked request.
- No band overlay lines appear (expected — the request never resolved) and no confluence chip
  appears.
- No "no tradable map" hint is shown either — the honest empty hint only renders once the fetch
  genuinely resolves to a served-empty response; a blocked/failed request stays in a distinct
  `error`/non-resolved phase, which renders nothing extra rather than a false "empty" claim.
- No unhandled-exception (red) errors appear in the Console. Network-level errors for the
  intentionally blocked request itself are expected and acceptable.

---

### UT-08 — Live mode: Price Chart, band overlay, and chip all stay fully hidden (regression — critical)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running.
- No watch currently active.

**Steps:**
1. Navigate to `http://localhost:3301/`.
2. Click the "Live" button in the data-source control.
3. Type `AAPL` into the "Symbol search" field.
4. Click "Watch".
5. Wait for the watch to resolve (a few seconds).
6. Scroll the full page top to bottom. Then open DevTools → Console and run
   `document.querySelector('[data-testid="confluence-chip"]')` and
   `document.querySelector('[data-testid="no-tradable-map"]')`.

**Expected Result:**
- No section or panel titled "Price Chart — Tape-State Markers" appears anywhere on the page.
- Both DevTools queries return `null`.
- Exactly one of the following honest outcomes is shown instead — all three are correct, and none of
  them shows a price chart:
  (a) if the real US market is open and credentials are configured, the live cockpit grid renders
  with tape-state panels but no price chart;
  (b) if the market is closed, an amber panel titled "Market is closed" renders;
  (c) if credentials are not configured, an amber panel titled "Real-data provider unavailable"
  renders.
- This must be byte-identical to pre-iteration behavior — this iteration's diff never touched the
  `(mode === "sim" || mode === "historical")` gate in `page.tsx` that hides the whole component in
  Live mode.

---

### UT-09 — Cockpit chart's pre-existing bar-size selector and dashed thesis lines still work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running. `PriceChart.tsx` is the file most heavily modified this iteration
  (+204/-4 lines), so its pre-existing behavior is the highest-risk regression surface.

**Steps:**
1. Navigate to `http://localhost:3301/`.
2. Confirm "Simulated" mode is selected, type `SIM-BUYER` into "Ticker", click "Watch".
3. In the "Price Chart — Tape-State Markers" panel, click the "30s" bar-size button.
4. Wait 2 seconds, then click the "60s" button.
5. Click back to "10s".

**Expected Result:**
- Each click immediately highlights the clicked button (darker slate background, lighter text) and
  un-highlights the others.
- The candlestick chart redraws with wider/narrower bars matching the selected bar size each time,
  with no error banner and no blank chart.
- Tape-state markers (small colored down-arrows above the bars) continue to render at their
  transition points after each bar-size change.
- If a thesis has been declared for the watched ticker (via the Thesis strip below the chart),
  dashed price-lines for the declared invalidation/level prices continue to render, visually distinct
  (dashed) from any solid band-overlay line also on the chart.

---

### UT-10 — `/structure`'s Tradable Map is unaffected by this iteration (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running.
- AAPL bar series already recorded (established in prior iterations).

**Steps:**
1. Navigate to `http://localhost:3301/structure`.
2. Confirm the heading "Structure" is visible.
3. Type `AAPL` into the field labeled "Symbol" (placeholder "e.g. PG").
4. Type `2026-06-22T21:00:00Z` into the field labeled "As-of (UTC, ISO-8601)" (placeholder
   "2026-06-09T21:00:00Z").
5. Click the "Load" button.
6. Wait for the page to finish loading.

**Expected Result:**
- A panel titled "Tradable Map" renders, showing a "Map basis (prior completed session close):"
  line followed by a timestamp, a price chart with band overlay lines, and a table of at most
  roughly 10 band rows (never hundreds/thousands of raw levels).
- A button reading "Show raw levels" (not yet clicked) is visible below the Tradable Map panel.
- Clicking "Show raw levels" reveals the pre-existing Levels & Zones section and the button's label
  flips to "Hide raw levels"; clicking it again hides that section and flips the label back.
- No cockpit-only element appears on this page: `data-testid="confluence-chip"` and
  `data-testid="no-tradable-map"` both return zero matches (those are additions to the cockpit's
  `PriceChart` only; `/structure` was not touched this iteration).

---

### UT-11 — Top navigation is unchanged (regression)

**Type:** regression
**Priority:** P3
**Surface:** navigation (all pages)

**Preconditions:**
- Frontend running.

**Steps:**
1. Navigate to `http://localhost:3301/`.
2. Look at the sticky navigation bar at the very top of the page (above the "Tapeology" header row).

**Expected Result:**
- Exactly 5 links are present, in this order: "Cockpit", "Journal", "Studies", "Performance",
  "Structure".
- No 6th link or new entry is present.
- Clicking "Structure" navigates to `http://localhost:3301/structure`; clicking "Cockpit" returns to
  `http://localhost:3301/`.

---

### UT-12 — Band overlay is visually distinct and clearly labeled (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- Same AAPL Historical watch as UT-03, with a band visible on the chart.

**Steps:**
1. With the band overlay visible on the chart (per UT-03), visually compare the band line to any
   dashed thesis price-line also present on the same chart.
2. Hover the mouse near the right-hand price axis where the band line's label sits.

**Expected Result:**
- The band line is drawn solid; any thesis price-line is drawn dashed — the two are easy to tell
  apart at a glance without reading any label.
- The axis label beside the band line is legible and states the band's side/class/score (e.g.,
  "R class A · score 153 · round") — a first-time viewer can understand this refers to a resistance
  level without consulting documentation, since the same R/S convention is already used consistently
  on `/structure`'s own chart.
- Color coding is consistent with the rest of the app: rose/pink = resistance (a ceiling), emerald/
  green = support (a floor).

---

### UT-13 — Confluence chip copy is descriptive, not imperative, and understandable (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- A confluence chip is visible (per UT-04). If timing prevented a live observation, inspect the
  rendered text via `document.querySelector('[data-testid="confluence-chip"]').innerText` in
  DevTools Console during a moment price is inside a band (chip may be absent — this check needs the
  chip actually present).

**Steps:**
1. Read the full text of the confluence chip banner top to bottom.
2. Check the wording for any of: "buy", "sell", "should", "will", "target", "recommend", or any
   percentage/dollar prediction.

**Expected Result:**
- The chip's text only describes the CURRENT condition (band side/range/class, current tape-state
  reading) and points to "measured history: edge report" — it never tells the operator what to do
  next and never predicts a future price or outcome.
- The tape-state word in the chip (e.g., "Ask Absorption") is human-readable title case, not a raw
  snake_case value like `ask_absorption`.
- The chip sits below the chart, does not overlap or obscure any candle/marker, and its slate-gray
  coloring (not amber) reads as a neutral factual note rather than a warning — consistent with this
  app's established convention that amber is reserved for degraded/empty/truncated states elsewhere
  (e.g. `FeedBasisBadge.tsx`, the "Market is closed" panel).

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit loads, Price Chart panel visible (Simulated) | smoke | P1 | `/` |
| UT-02 | SIM-BUYER shows honest "no tradable map" hint | happy-path | P1 | `/` |
| UT-03 | Band overlay renders on real AAPL historical replay | happy-path | P1 | `/` |
| UT-04 | Confluence chip appears at a real confluence moment | happy-path | P1 | `/` |
| UT-05 | Chip absent when price outside every band | validation | P2 | `/` |
| UT-06 | Chip absent when tape state unclear/unmapped | validation | P2 | `/` |
| UT-07 | Bands fetch failure never blocks chart / never crashes | error | P2 | `/` |
| UT-08 | Live mode: chart, overlay, chip all fully hidden | regression | P1 | `/` |
| UT-09 | Bar-size selector + dashed thesis lines still work | regression | P1 | `/` |
| UT-10 | `/structure` Tradable Map unaffected | regression | P1 | `/structure` |
| UT-11 | Nav unchanged (5 entries, no new page) | regression | P3 | nav |
| UT-12 | Band overlay visually distinct + clearly labeled | ux | P2 | `/` |
| UT-13 | Chip copy descriptive, not imperative | ux | P2 | `/` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-04 carries an explicit,
project-documented honest-uncertainty carve-out (see its own Expected Result) — a "not yet observed
this session" outcome backed by UT-03's overlay evidence and the keyless source-inspection tests is
an acceptable non-FAIL outcome for that one test only; it must never be reported as a silent PASS
without an actual observation or a documented honest-blocked note.
