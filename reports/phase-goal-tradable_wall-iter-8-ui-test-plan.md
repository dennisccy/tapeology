# Phase goal-tradable_wall-iter-8 — UI Test Plan

**Phase:** goal-tradable_wall-iter-8
**Date:** 2026-07-15
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301

---

## Scope

This iteration ships exactly one small frontend code change — `PriceChart.tsx`'s tradability-fetch
effect now early-returns and stays in its `loading` phase until `history.epoch_anchor` is known,
closing iter-7 audit finding F1 (no more wall-clock-basis flash on the cockpit chart before a
watched session's own anchor resolves). Everything else tested below is **verification of
already-built UI now serving real data for the first time**: the Case Studies drill-in and the Edge
Report sections on `/structure` run identical code to iter-7 — the operator's 11 newly-persisted
credentialed recordings simply let their existing, unmodified read paths resolve populated content
instead of the honest-empty placeholders they showed before. No new page, button, form, or nav
entry was added.

**Two known, DOCUMENTED long-running operations are covered below and must never be treated as a
failure purely for taking a long time:**

1. **Case Studies row drill-in** (`GET /research/setups/{id}`) replays its entire recorded tick
   window from scratch on every row click — nothing is cached. Measured at ~13 minutes on a cold
   run; test steps below budget up to 20 minutes.
2. **Edge Report** (`GET /research/edge-report`) recomputes from scratch, uncached, on every single
   `/structure` page load or reload — it fetches automatically the moment the page mounts, no
   button click required. Estimated at "on the order of 10+ hours" on a cold backend process, with
   no progress indicator beyond a generic pulsing gray placeholder. Reloading `/structure` restarts
   this computation from zero, so tests below explicitly warn against reloading while waiting.

API-level checks that do not require a browser (dataset-store enumeration, `GET
/research/setups/{id}` JSON shape, `GET /research/edge-report` JSON shape, credential-scan,
`config_fingerprint`, feed-pooling verified via `jq`) are already covered in
`reports/qa/goal-tradable_wall-iter-8-test-plan.md` (TC-03 through TC-06, TC-13 through TC-15) and
are **not** duplicated here — this plan covers only what an operator observes in the browser.

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
3. Confirm the "Simulated" button in the data-source control (top area, beside the "Tapeology"
   wordmark) is already highlighted as selected by default.
4. Type `SIM-BUYER` into the field labeled "Ticker" (placeholder "Ticker e.g. SIM-BUYER").
5. Click the "Watch" button.

**Expected Result:**
- No red error banner appears below the header.
- Within a few seconds a panel titled "Price Chart — Tape-State Markers" appears.
- A candlestick chart begins rendering inside that panel.
- Opening the browser DevTools Console shows zero red errors.

---

### UT-02 — Historical AAPL 2026-06-22 replay shows the correct prior-session basis from first paint, never a wall-clock flash (happy-path — verifies F1)

**Type:** happy-path
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running.
- Real market-data credentials are already configured on this backend (established in prior
  iterations).
- AAPL's bar series has already been recorded through at least 2026-06-18.
- No watch is currently active.

**Steps:**
1. Navigate to `http://localhost:3301/`.
2. Open DevTools → Network tab. Clear existing entries, then type `tradability` into the filter box.
3. Click the "Historical" button in the data-source control.
4. Type `AAPL` into the field labeled "Symbol search"; type `22-06-2026` into the "Date" field.
5. Click the button starting with "Full RTH 9:30–16:00 ET".
6. Click "Watch".
7. Watch the Network tab for the first request whose URL contains `research/tradability` (it may
   take a moment to appear, or may not fire in the first second at all — that is the expected,
   fixed behavior).
8. Click that first request and inspect its `as_of` query parameter.

**Expected Result:**
- If/when a `research/tradability` request appears, its `as_of` value already reads a `2026-06-18`
  date-time on the very first such request — never today's real-world date. No earlier request
  carrying today's date precedes it.
- Visually, no band-overlay line or confluence chip flashes into view and then immediately
  changes or disappears within the first second after clicking "Watch" — if a band renders, it
  renders once, correctly, and stays.
- The candlestick chart and tape-state markers render normally, unaffected by this change.

---

### UT-03 — SIM-BUYER still shows the honest "no tradable map" hint, unaffected by the F1 fetch-gating change (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Same as UT-01. Can continue directly from UT-01's watched SIM-BUYER session.

**Steps:**
1. Navigate to `http://localhost:3301/` (or continue from UT-01).
2. Confirm "Simulated" is selected in the data-source control; click it if not.
3. Type `SIM-BUYER` into the "Ticker" field; click "Watch".
4. Wait 5 seconds for the chart and the bands request to resolve.
5. Look directly below the chart canvas, still inside the "Price Chart — Tape-State Markers" panel.

**Expected Result:**
- The candlestick chart renders normally, unaffected.
- A small slate-gray line of text reading exactly `No tradable map for SIM-BUYER.` appears directly
  below the chart.
- No confluence chip is present.
- This confirms the F1 fetch-gating change (early-return while `epoch_anchor` is null) did not
  suppress or delay the honest empty state — SIM providers always set a non-null `epoch_anchor`, so
  this path is unaffected end-to-end.

---

### UT-04 — Live mode still fully hides the Price Chart panel (regression — critical)

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
6. Scroll the full page top to bottom.

**Expected Result:**
- No section or panel titled "Price Chart — Tape-State Markers" appears anywhere on the page.
- No band overlay, no confluence chip, and no "no tradable map" hint render anywhere — the entire
  component is absent, byte-identical to pre-iteration behavior (F1 only touched the fetch effect
  *inside* the component; it never touched the `mode === "sim" || mode === "historical"` mount gate
  that hides the whole component in Live mode).

---

### UT-05 — Confluence chip and band-overlay copy remain descriptive-only after the F1 change (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/`

**Preconditions:**
- A band overlay line and/or a confluence chip is visible (per UT-02), or continue the same watch.

**Steps:**
1. If a band-overlay line is visible on the chart, hover near its price-axis label.
2. If a confluence chip banner is visible below the chart, read its full text top to bottom.

**Expected Result:**
- The axis label reads a form like `R class A · score {number}[ · round]` — legible, no prediction
  language.
- The chip, if present, reads only a factual description (`Inside {R|S}-band {low}–{high} ... tape:
  {State} ({rejection|breakthrough}) · measured history: edge report`) — no "buy", "sell", "should",
  "will", "target", "recommend", or any percentage/dollar prediction anywhere in the text.
- This confirms F1's timing-only change did not alter the chip/overlay's rendered copy, only when
  the underlying fetch is allowed to fire.

---

### UT-06 — `/structure` loads with Case Studies filters and table visible (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running.

**Steps:**
1. Navigate to `http://localhost:3301/structure`.
2. Wait for the page to finish loading.
3. Confirm the heading "Structure" is visible near the top of the page.
4. Scroll down to the panel titled "Case Studies".

**Expected Result:**
- The "Case Studies" panel is visible with a "Symbol" text field (placeholder "e.g. AAPL") and a
  "Reaction" dropdown, above a data area.
- Within a few seconds that data area resolves to either a table of rows or the honest message "No
  band-touch events scanned yet." — never stuck as a blank white area.
- Opening the browser DevTools Console shows zero red errors.

---

### UT-07 — Pinned AAPL 2026-06-22 drill-in shows the populated five-state tape timeline (happy-path — THE headline J-03 test)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running.
- The operator's 11 persisted recorded datasets exist at `apps/backend/.data/datasets/`, including
  the pinned AAPL 2026-06-22 window (`5c7f1a44…`).
- **Known slow step ahead** — this drill-in replays the entire recorded window from scratch on this
  click; nothing is cached. Budget up to 20 minutes for this single test (see Scope).

**Steps:**
1. Navigate to `http://localhost:3301/structure`.
2. Type `AAPL` into the field labeled "Symbol" inside the "Case Studies" panel.
3. In the resulting table, locate the row whose "session" column reads `2026-06-22` (its "band"
   column should read a range near `300.17–302.27`).
4. Click anywhere on that row.
5. A new panel titled "Case Studies — drill-in" appears below the table, showing a pulsing gray
   loading placeholder.
6. Wait for this loading placeholder to resolve. **Do NOT reload the page, click a different Case
   Studies row, or navigate away while waiting** — any of these abandons this fetch and you would
   need to start over. Allow up to 20 minutes.

**Expected Result:**
- The loading placeholder eventually resolves — never stays frozen indefinitely under normal
  conditions, and does not show a red "could not be loaded" panel.
- The drill-in panel shows a "symbol / session" row reading `AAPL · 2026-06-22`, plus "band",
  "reaction", and "forward returns" rows.
- Below that, under the label "Tape timeline", a list of **multiple** dated entries appears, each
  showing a timestamp, a state name (one of `buyer_control` / `seller_control` / `bid_absorption` /
  `ask_absorption`), and a confidence value.
- The text "No recorded tape for this event." does **NOT** appear — this is the specific
  empty-state text this test must not see.

---

### UT-08 — Drill-in's reaction and forward-return fields are unchanged from before this iteration (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Continue directly from UT-07's resolved drill-in.

**Steps:**
1. With the AAPL 2026-06-22 drill-in panel still open from UT-07, locate the "reaction" row.
2. Locate the "forward returns" row.

**Expected Result:**
- "reaction" reads exactly `rejected`.
- Both forward-return values shown are negative numbers.
- These two values are unchanged from what earlier iterations already showed for this event — this
  iteration's diff never touched the reaction/forward-return computation, only the previously-empty
  tape timeline underneath them is newly populated.

---

### UT-09 — Case Studies symbol filter with no matches shows the honest empty state, not a crash (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- `/structure` page loaded, Case Studies table populated (per UT-06).

**Steps:**
1. Clear the "Symbol" field in the Case Studies panel if it already has a value.
2. Type `ZZZZNOPE` into the "Symbol" field.
3. Clear the field back to empty.

**Expected Result:**
- After step 2, the table is replaced with the message "No events match these filters." (with the
  sub-text "The registry has rows — this filter combination simply matches none.").
- No error banner, no blank page, no crash.
- After step 3, the full unfiltered table returns.

---

### UT-10 — A case-study row without a recorded dataset still shows the honest empty tape timeline (regression)

**Type:** regression
**Priority:** P3
**Surface:** `/structure`

**Preconditions:**
- Case Studies table populated with more than one visible row.

**Steps:**
1. In the Case Studies table, click a row for a session date that is **not** `2026-06-22` (any
   other visible row — clear the Symbol filter first if needed to see more rows).
2. Wait for the drill-in panel to resolve.

**Expected Result:**
- The drill-in still opens successfully (no crash).
- Under "Tape timeline", the text "No recorded tape for this event." appears — **unless** this row
  coincidentally happens to be one of the operator's other 10 recorded windows, in which case a
  populated list is equally correct. What must **never** happen is a fabricated/generic timeline
  shown for a row that genuinely has no matching recorded dataset.

---

### UT-11 — The multi-minute drill-in wait renders as a clear loading state, not a frozen/broken page (ux)

**Type:** ux
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Same setup as UT-07, observed during the wait.

**Steps:**
1. Immediately after clicking the AAPL 2026-06-22 row (UT-07 step 4), observe the drill-in area for
   the first 30 seconds.
2. Continue to periodically glance at it every few minutes during the wait.
3. While waiting, try scrolling the page and clicking on an unrelated element (e.g. the nav bar).

**Expected Result:**
- The loading area shows a visibly **animated** (pulsing) gray placeholder block — not a static gray
  box and not a blank area — signaling to an operator unfamiliar with this feature's known slowness
  that the page is still working, not frozen.
- The rest of the page (nav bar, the Case Studies table above, other panels) remains fully
  interactive during the wait.

---

### UT-12 — Edge Report panel appears with its loading state immediately after `/structure` loads (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running.
- Fresh navigation to `/structure` (this fetch starts automatically on every page load — see Scope).

**Steps:**
1. Navigate to `http://localhost:3301/structure`.
2. Scroll down past "Case Studies" to the panel titled "Edge Report".
3. Observe the panel for the first 10 seconds.

**Expected Result:**
- The "Edge Report" panel is visible with its introductory description text and an amber disclaimer
  line above the tables.
- Below that, a pulsing gray loading placeholder is visible — this fetch began automatically the
  moment the page loaded; no button click is required to start it.
- No red error banner, no blank white area, no console error.
- **Do not reload `/structure` repeatedly** while continuing other tests in this session — every
  reload restarts this computation from zero (see Scope's long-running note).

---

### UT-13 — Edge Report eventually resolves to populated Train/Hold-out cells with real counts (happy-path — long-running, THE second headline J-03 test)

**Type:** happy-path
**Priority:** P1 (documented carve-out below)
**Surface:** `/structure`

**Preconditions:**
- Same browser tab/session as UT-12, left open and untouched (no reload, no navigating away) since
  the Edge Report fetch began.
- At least one of the operator's 11 recorded panel-symbol datasets exists.
- **KNOWN, DOCUMENTED estimate: "on the order of 10+ hours" on a cold backend process**, with no
  progress indicator beyond the generic pulsing placeholder. This test cannot complete within a
  standard QA session — execute it as a separate, long-duration background check (e.g. leave the
  tab open overnight, or accept a next-day check-in knowing a reload restarts the clock).

**Steps:**
1. Continuing from UT-12 (or a fresh `/structure` load if starting this check independently), leave
   the browser tab open on `/structure` without reloading or navigating away.
2. Periodically (e.g., once per hour) glance at the "Edge Report" panel without reloading the page.
3. Once the loading placeholder resolves, inspect the panel content.

**Expected Result:**
- The panel resolves to one of two honest, non-error outcomes:
  (a) a section titled "Train" followed by a table, and a section titled "Hold-out" followed by a
  second, **separate** table (never merged into one), each with columns `strategy` / `class` /
  `side` / `reaction` / `feed` / `n` / `net R` / `net $` / `win_rate` / `sample`; or
  (b) if genuinely no dataset resolved an owning classified scan event, the message "No edge-report
  cells yet." — this is explicitly documented as an equally valid, honest outcome, never a failure.
- If outcome (a): at least one row shows a real, non-placeholder number in the `n` column.
- Never a partial/malformed render (e.g. a table missing columns, or a JavaScript error where the
  tables should be).

**Carve-out (mirrors this project's documented pattern for other timing-dependent P1 tests):** if
this test has not resolved by the end of the standard QA session's practical time budget, report its
status as "loading correctly, not yet resolved this session" rather than FAIL — cite UT-12's
evidence that the fetch started correctly and the panel is in its documented loading state, not
stuck/broken. This must never be silently reported as a PASS without an actual observed resolution,
and must never be skipped without a note.

---

### UT-14 — Rows with n < 5 are honestly labelled "insufficient sample," never manufactured into a survivor (error / anti-goal)

**Type:** error
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Edge Report has resolved with at least one populated table (per UT-13 outcome (a)), OR has
  resolved as fully empty (per UT-13 outcome (b)). If UT-13 has not yet resolved this session, this
  test also cannot be completed yet — report the same "not yet resolved this session" status.

**Steps:**
1. If the Edge Report resolved with populated Train/Hold-out tables, scan the rightmost "sample"
   column of every visible row in both tables.
2. If the Edge Report instead resolved as "No edge-report cells yet.", treat this as the honest
   outcome and skip to the Expected Result's last bullet.

**Expected Result:**
- Every row whose `n` value is below 5 shows an amber badge reading exactly `insufficient sample (n
  < 5)` in the "sample" column — never a blank cell, never a hidden row.
- Every row whose `n` value is 5 or higher shows the plain text `ok` in that column instead.
- An Edge Report that is entirely empty, or where every row reads `insufficient sample`, is
  confirmed as an accepted, valid, publishable outcome — not a bug, and not something the UI
  attempts to hide, pad, or route around.

---

### UT-15 — Train and hold-out splits, and feed labels, are never pooled together (regression — feed-honesty anti-goal)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Edge Report resolved with at least one populated table (per UT-13 outcome (a)). If not yet
  resolved this session, this test also cannot be completed yet.

**Steps:**
1. Confirm "Train" and "Hold-out" render as two visually separate tables, each under its own
   heading, never merged into a single combined table.
2. Read the "feed" column value for every visible row in both tables.

**Expected Result:**
- "Train" and "Hold-out" are always two distinct tables (even if one individually resolves empty
  and shows "No cells in this split.").
- Every row's "feed" cell shows exactly **one** feed name (expect `sip` for this operator's
  recordings) — no cell shows a combined/comma-separated list of feeds, and no row's numbers appear
  to describe a mix of feeds.

---

### UT-16 — Loading, empty, and populated Edge Report states are visually distinct (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/structure`

**Preconditions:**
- Able to observe the Edge Report panel at different points in time (e.g. compare its appearance
  during UT-12 against its appearance once UT-13 resolves).

**Steps:**
1. Compare the panel's appearance while still loading (pulsing gray placeholder, from UT-12) against
   its appearance once resolved (from UT-13).
2. If either split resolves individually empty, note how "No cells in this split." is displayed
   compared to the loading placeholder.

**Expected Result:**
- The loading state (animated pulsing gray bars), the honest-empty state (a message with a "∅"
  symbol and explanatory text), and the populated state (data tables) are each visually
  distinguishable from one another at a glance — an operator can tell which of the three they are
  looking at without needing to read fine print.

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Cockpit loads, Price Chart panel visible (Simulated) | smoke | P1 | `/` |
| UT-02 | Historical AAPL replay: correct basis from first paint, no flash | happy-path | P1 | `/` |
| UT-03 | SIM-BUYER honest "no tradable map" hint unaffected by F1 | regression | P1 | `/` |
| UT-04 | Live mode: Price Chart fully hidden | regression | P1 | `/` |
| UT-05 | Chip/overlay copy still descriptive-only after F1 | ux | P2 | `/` |
| UT-06 | `/structure` loads, Case Studies filters + table visible | smoke | P1 | `/structure` |
| UT-07 | Pinned AAPL 2026-06-22 drill-in: populated tape timeline | happy-path | P1 | `/structure` |
| UT-08 | Drill-in reaction/forward-returns unchanged | regression | P2 | `/structure` |
| UT-09 | Case Studies filter with no matches: honest empty state | validation | P2 | `/structure` |
| UT-10 | Non-recorded case-study row still shows honest empty timeline | regression | P3 | `/structure` |
| UT-11 | Multi-minute drill-in wait renders as clear loading, not frozen | ux | P2 | `/structure` |
| UT-12 | Edge Report shows loading state immediately on page load | smoke | P1 | `/structure` |
| UT-13 | Edge Report eventually resolves populated Train/Hold-out cells | happy-path | P1* | `/structure` |
| UT-14 | n<5 rows honestly labelled `insufficient sample`, never faked | error | P1 | `/structure` |
| UT-15 | Train/hold-out and feed labels never pooled | regression | P1 | `/structure` |
| UT-16 | Loading/empty/populated Edge Report states visually distinct | ux | P3 | `/structure` |

**P1 tests must all pass for browser QA verdict to be PASS.** UT-13 carries an explicit,
project-documented carve-out (marked P1\* — see its own Expected Result): a "not yet resolved this
session" outcome, backed by UT-12's evidence that the fetch started correctly, is an acceptable
non-FAIL outcome for that test alone given its documented 10+ hour estimate — it must never be
reported as a silent PASS without an actual observed resolution. UT-14 and UT-15 inherit the same
carve-out when they depend on UT-13 having resolved.
