# Phase goal-structure_ui-iter-3 — UI Test Plan

**Phase:** goal-structure_ui-iter-3
**Date:** 2026-07-07
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL (error-injection steps only):** http://localhost:8000 (this project's default backend port; adjust if your environment differs — not overridden for this task)

---

## Scope & Priority Note

This plan covers the new **Comparison** section added to the existing `/structure` page (dataset
selector, dual `v1`-vs-`structure_tape` backtest run + poll, side-by-side aggregates, per-class
A/B/C table, register line, read-only champion badge, founding-baseline row, and six-plus honest
states), plus the regression checks the execution plan calls out by name.

**Deviation from the test-design skill's default priority assignment:** the skill defaults
"regression tests with low risk" to P3. Here, the phase's own Definition of Done names **J-01,
J-02, and J-04 as required-still-passing journeys** — a regression on any of them fails the phase,
not merely degrades it. Regression cases UT-18–UT-23 are therefore elevated to **P1**. The
testid-collision check (UT-21) is elevated for the same reason: the execution plan names it a
specific, already-anticipated risk (iter-2 audit finding T2 — Registry and Comparison render the
champion badge twice on the same page and must not collide).

This plan intentionally does **not** duplicate the existing functional test plan's curl/pytest/git-diff
checks (`reports/qa/goal-structure_ui-iter-3-test-plan.md`); every test case below is something an
operator verifies by looking at the rendered page (occasionally cross-checked with the browser's
own element inspector or a direct API call where a state can't be produced through the UI alone).

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — `/structure` loads with all three sections (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301
- Backend running and reachable
- At least one dataset is registered (true by default — 7 datasets exist on this environment)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load
3. Scroll from the top to the bottom of the page

**Expected Result:**
- The page renders three stacked panels in this order: "Levels & Zones" (top), "Registry"
  (middle), "Comparison" (bottom)
- No blank screen, no red/error banner, no browser console errors
- The `<h1>` heading "Structure" is visible at the top

---

### UT-02 — Comparison section renders all its static elements (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure` (Comparison section)

**Preconditions:**
- UT-01 passing

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll to the bottom "Comparison" panel

**Expected Result:**
- A panel titled "Comparison" is visible, containing top to bottom: a read-only disclaimer
  paragraph, a two-box row labeled "Champion (moved never by this view)" and "Founding baseline
  (PnL ledger)", a dataset dropdown, and a "Run comparison" button
- The "Run comparison" button appears visually disabled (greyed out / not clickable) since no
  dataset is chosen yet

---

### UT-03 — Dataset selector populates with real registered datasets (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure` (Comparison dataset select)

**Preconditions:**
- UT-02 passing
- At least one dataset registered

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll to the Comparison section
3. Click the dataset dropdown (shows placeholder text "Choose a dataset…")

**Expected Result:**
- The dropdown's first option reads exactly "Choose a dataset…" and selecting it (or leaving it
  selected) keeps "Run comparison" disabled
- One or more additional options are listed below it, each formatted as
  `<symbol> · <split> · <8-character id prefix>` (e.g. "AAPL · train · a1b2c3d4")
- The number of additional options matches the number of datasets registered on the backend
  (7 on this environment by default)

---

### UT-04 — User runs a full comparison end to end (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison section)

**Preconditions:**
- UT-03 passing
- Backend reachable for the whole duration of this test

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll to the Comparison section
3. Click the dataset dropdown and select any dataset other than the placeholder
4. Click the "Run comparison" button
5. Observe the button and the area below it for the next few seconds
6. Wait until neither result slot reads "Queued…" or "Running…" anymore (typically well under 30
   seconds)

**Expected Result:**
- Immediately after step 4: the button's label changes to "Running…" and it becomes disabled (no
  double-submit)
- Two card slots appear side by side, labeled "v1 (champion strategy)" and "structure_tape", each
  initially showing "Queued…" or "Running…" (a "Running…" card also shows a live
  events-processed count)
- Once both finish: both cards show a definition list of numbers, a "Per-class (A/B/C)" table, and
  an amber register line — no card is left permanently spinning

---

### UT-05 — Side-by-side aggregates render for both strategies (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison result cards)

**Preconditions:**
- UT-04 completed; both cards reached their finished state

**Steps:**
1. On the finished "v1 (champion strategy)" card, read its definition list
2. On the finished "structure_tape" card, read its definition list

**Expected Result:**
- Both cards show all five fields: `n`, `net R`, `net $`, `win_rate`, `max drawdown (R)`
- Every field shows a value — a number, or the honest text "no trades (n=0)" for
  `win_rate`/`max drawdown (R)` when the strategy took zero trades — never blank, "undefined", or
  "NaN"

---

### UT-06 — Per-class A/B/C breakdown table renders under each result (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison per-class table)

**Preconditions:**
- UT-04 completed; both cards reached their finished state

**Steps:**
1. Below the "v1 (champion strategy)" card's definition list, locate the "Per-class (A/B/C)" table
2. Below the "structure_tape" card's definition list, locate its own "Per-class (A/B/C)" table

**Expected Result:**
- Each table has exactly three rows, labeled "Class A", "Class B", "Class C" (always all three,
  even if a class took zero trades)
- Each row shows columns for n, net R, net $, and a "sample" column
- Any row whose sample column shows the chip "insufficient sample (n < 5)" is amber-colored; a row
  at or above the minimum shows "ok" in that column instead

---

### UT-07 — Simulated register line renders under each result (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison register line)

**Preconditions:**
- UT-04 completed; both cards reached their finished state

**Steps:**
1. Below the "v1 (champion strategy)" card's per-class table, read the amber-bordered line of text
2. Below the "structure_tape" card's per-class table, read its amber-bordered line of text

**Expected Result:**
- Both lines read exactly: "simulated — assumed fees/slippage — not indicative of live results"
- Neither line reads the shorter "simulated — not indicative of live results" (that shorter phrase
  would indicate a hardcoded, incorrect frontend literal instead of the real payload value)

---

### UT-08 — Founding baseline row renders in the Founding-baseline box (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison Founding-baseline box)

**Preconditions:**
- UT-02 passing

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll to the Comparison section
3. Read the "Founding baseline (PnL ledger)" box (no need to click "Run comparison" first — this
   box loads independently on page mount)

**Expected Result:**
- If a founding ledger row exists: the box shows the row's title plus its "candidate train net R"
  and "candidate hold-out net R" values
- If no founding row exists yet: the box instead shows the exact text "No founding row yet — the
  PnL ledger is empty."
- Either outcome is correct as long as it's one of these two — never a blank box, a spinner that
  never resolves, or a fabricated number

---

### UT-09 — Champion panel in Comparison shows read-only v1/default (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison Champion box)

**Preconditions:**
- UT-02 passing

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll to the Comparison section's "Champion (moved never by this view)" box
3. Read the strategy and profile values shown
4. Look for any button, link, dropdown, or other interactive control inside this box

**Expected Result:**
- The box shows "v1" as the strategy and "default" as the profile
- These values match the Registry section's own champion badge further up the page
- No interactive control exists inside the Champion box — it is text only, confirming there is no
  promotion path from this view

---

### UT-10 — Reference dataset produces the honest non-survivor outcome for structure_tape (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison result cards)

**Preconditions:**
- UT-04 passing (comparison mechanics work)
- The backend's committed keyless reference dataset is registered. This test does not depend on
  knowing its exact name in advance — see step 3's self-check.

**Steps:**
1. Navigate to `http://localhost:3301/structure` and scroll to the Comparison section
2. Select a dataset from the dropdown (if `docs/handoffs/goal-structure_ui-iter-3-dev.md` names the
   reference dataset's id/symbol, pick that one; otherwise start with any one) and click "Run
   comparison"
3. Wait for both cards to finish, then inspect the "structure_tape" card's Per-class (A/B/C) table
   and its `win_rate`/`max drawdown (R)` fields

**Expected Result:**
- On the correct reference dataset: all three rows (Class A, B, C) in the "structure_tape" card's
  table show the "insufficient sample (n < 5)" chip, and its `win_rate`/`max drawdown (R)` fields
  read "no trades (n=0)" — never a bare "0"
- The Champion box (per UT-09) still reads "v1"/"default", unchanged by running this comparison
- If instead `structure_tape` shows populated, non-insufficient numbers, the selected dataset was
  not the no-signal reference fixture — repeat steps 2–3 with a different dataset from the list
  until the insufficient-sample outcome above is observed at least once

---

### UT-11 — "Run comparison" button stays disabled until a dataset is chosen (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure` (Comparison dataset select + Run button)

**Preconditions:**
- UT-02 passing

**Steps:**
1. Navigate to `http://localhost:3301/structure` and scroll to the Comparison section
2. Without touching the dataset dropdown, attempt to click "Run comparison"
3. Open the dataset dropdown and select any real dataset (not the "Choose a dataset…" placeholder)
4. Attempt to click "Run comparison" again

**Expected Result:**
- In step 2: the button does not respond (visually disabled, takes no action — no backtests are
  created)
- In step 4: the button is now clickable and clicking it starts the comparison (label changes to
  "Running…")

---

### UT-12 — No datasets registered shows an explicit empty state (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure` (Comparison dataset area)

**Preconditions:**
- An isolated/test backend environment with zero registered datasets (a temp-dir override or fresh
  `.data/datasets/` directory — the live dev environment has 7 datasets registered by default, so
  this state needs an isolated environment to exercise, per the iter-1 fixture-seeding precedent)

**Steps:**
1. Navigate to `http://localhost:3301/structure` against the zero-dataset backend
2. Scroll to the Comparison section

**Expected Result:**
- The dataset area shows the exact text "No datasets registered." plus a hint about recording new
  data
- Neither a dataset `<select>` dropdown nor the "Run comparison" button is rendered

---

### UT-13 — Backend unreachable at page load shows explicit messages (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure` (Comparison section, page load)

**Preconditions:**
- Frontend running at http://localhost:3301
- Backend process stopped (however your environment normally starts it — e.g., Ctrl-C the terminal
  running it, or stop its container/process) before loading the page

**Steps:**
1. With the backend stopped, navigate to `http://localhost:3301/structure`
2. Scroll to the Comparison section
3. Read both the dataset area and the Champion box

**Expected Result:**
- The dataset area shows an explicit unreachable message (e.g., "Backend unreachable — is the API
  running?" or a specific fetch-error message) instead of a selector
- The Champion box shows "Champion not yet loaded (see the Registry section above)" instead of
  "v1"/"default"
- No part of the page shows a fabricated champion, dataset, or result

---

### UT-14 — Backend failure on POST shows an explicit run-error message (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure` (Comparison run action)

**Preconditions:**
- Comparison section loaded successfully with datasets visible (backend was reachable at page load)
- Backend stopped immediately before clicking "Run comparison" (to fail only the POST, not the
  initial page load)

**Steps:**
1. With the Comparison section already loaded and a dataset selected, stop the backend
2. Click the "Run comparison" button
3. Observe the area where result cards would normally appear

**Expected Result:**
- An amber panel appears with a message ending in "...could not be started." (or a more specific
  backend error if one is available)
- Neither the "v1 (champion strategy)" card nor the "structure_tape" card shows a result, an
  in-progress state, or any fabricated data

---

### UT-15 — Backend unreachable mid-poll shows a transient notice and recovers (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure` (Comparison poll loop)

**Preconditions:**
- A comparison is running (at least one card still shows "Queued…" or "Running…")

**Steps:**
1. Start a comparison (select a dataset, click "Run comparison")
2. While at least one card still shows "Queued…" or "Running…", stop the backend
3. Wait about 1 second and read the Comparison section
4. Restart the backend and wait a few seconds

**Expected Result:**
- Within roughly 700ms of the backend stopping, the text "Backend unreachable while polling —
  showing the last known status." appears
- The last-known per-side state (e.g., "Running…" or any partial info already shown) stays visible
  — it is not blanked or reset
- After the backend restarts, the notice disappears on its own and polling resumes with no manual
  page refresh

---

### UT-16 — A failed backtest shows a distinct failed card (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure` (Comparison per-side failed state)

**Preconditions:**
- One of the two backtests reaches `status: "failed"`. This is the hardest honest state to trigger
  from the UI alone — there is no UI control that forces a runner failure. If you cannot reproduce
  a genuine failure in your environment, a direct code read of the failed-state branch in
  `apps/frontend/app/structure/page.tsx` is an acceptable substitute confirmation; note that live
  reproduction was not possible rather than silently skipping this row.

**Steps:**
1. Trigger one side's backtest into a `failed` status (see Preconditions)
2. Observe that side's card while the other side continues normally

**Expected Result:**
- The failed side's card shows a rose-colored (not amber, not grey) border and the message "This
  backtest could not produce a result..." followed by the backend's own error text
- The other side's card is unaffected and continues to poll/render independently (it does not also
  show failed)

---

### UT-17 — A cancelled backtest shows a distinct cancelled card with no partial result (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure` (Comparison per-side cancelled state)

**Preconditions:**
- A comparison is running; you have terminal or browser dev-tools access to issue a direct API
  call (there is no in-UI cancel button by design)

**Steps:**
1. Start a comparison (select a dataset, click "Run comparison") and note both returned backtest
   ids (visible via `GET http://localhost:8000/research/backtests` or the browser's Network tab)
2. While one of the two backtests is still `queued` or `running`, issue
   `POST http://localhost:8000/research/backtests/{that_id}/cancel` (curl, or the browser's own
   fetch console)
3. Observe that side's card in the Comparison section

**Expected Result:**
- That side's card shows exactly: "This backtest was cancelled before it finished. A partial
  simulated result is never served — no result is shown."
- No aggregates, no per-class table, and no register line render for that side — the other side
  continues normally

---

### UT-18 — J-01 Levels & Zones section still works (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (Levels & Zones section)

**Preconditions:**
- A symbol/as-of combination with recorded bars and levels is known (any previously-used one from
  J-01 testing)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll to the top "Levels & Zones" section
3. Enter a known symbol and as-of time, then click the section's Load button
4. Observe the chart and the zones table below it

**Expected Result:**
- A price chart renders with candles and dashed level lines, exactly as it did before this
  iteration
- A confluence-zones table renders below the chart with correct A/B/C class labels
- No layout shift, error, or blank area caused by the new Comparison section further down the page

---

### UT-19 — J-01 chart is not visually occluded by the new Comparison section (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (Levels & Zones chart)

**Preconditions:**
- UT-18 passing (chart is rendered with data)

**Steps:**
1. With the chart rendered, hover over or interact with the chart (scroll/zoom if supported)
2. Look for any tooltip, legend, or overlay the chart produces
3. Scroll the page up and down past the Comparison section and back to the chart

**Expected Result:**
- The chart remains fully interactive (scroll/zoom responds) throughout
- Any tooltip or overlay the chart produces appears on top of the chart, never hidden behind it or
  behind the Comparison section
- No part of the Comparison section visually overlaps or clips the chart at any scroll position

---

### UT-20 — J-02 Registry section and champion still render correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (Registry section)

**Preconditions:**
- None beyond UT-01

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll to the middle "Registry" section
3. Read the two strategy cards and the champion badge

**Expected Result:**
- Two strategy cards are visible for `v1` and `structure_tape`, each showing their parameters as
  before this iteration
- The Registry section's own champion badge shows "v1" and "default"
- Nothing in this section's layout or values differs from its pre-iter-3 behavior

---

### UT-21 — No DOM testid collision between Registry's and Comparison's champion badges (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (both Registry and Comparison champion badges)

**Preconditions:**
- Both the Registry section and the Comparison section's Champion box are rendered on the same
  page load

**Steps:**
1. Navigate to `http://localhost:3301/structure` and wait for the full page to load
2. Right-click the Registry section's champion strategy value and choose "Inspect" (or use your
   browser's element inspector / a testid-search extension)
3. Confirm its `data-testid` attribute reads `champion-strategy`
4. Repeat for the Comparison section's Champion box strategy value and confirm its `data-testid`
   reads `comparison-champion-strategy`
5. Search the full page DOM for elements with `data-testid="champion-strategy"` and separately for
   `data-testid="comparison-champion-strategy"`

**Expected Result:**
- Exactly one element matches `data-testid="champion-strategy"` (in Registry) and exactly one
  matches `data-testid="comparison-champion-strategy"` (in Comparison) — no duplicates of either
- Both elements display the same value ("v1"), confirming they read the same underlying data
  through two distinct, non-colliding DOM identities

---

### UT-22 — Top navigation still shows exactly five links (regression)

**Type:** regression
**Priority:** P1
**Surface:** top navigation bar (all pages)

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Look at the top navigation bar

**Expected Result:**
- Exactly five links/tabs are visible: Cockpit, Journal, Studies, Performance, and Structure
- Each is clickable and none are missing, duplicated, or renamed

---

### UT-23 — `/performance` page unaffected by `/structure` changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/performance`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/performance` directly (typing the URL, not by clicking
   through from `/structure`)
2. Observe the page

**Expected Result:**
- The page loads normally with its champion summary block showing "v1"/"default"
- No console errors; nothing on this page references or is affected by any `/structure`-only
  testid (`comparison-*`)

---

### UT-24 — Header subtitle previews all three `/structure` sections (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/structure` (header)

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Read the paragraph directly under the "Structure" heading
3. Read the disclaimer line below that paragraph

**Expected Result:**
- The intro paragraph ends with "...the registered strategies and current champion, and a
  structure_tape-vs-v1 backtest comparison." (not stopping earlier, at "...for a chosen symbol and
  as-of time.")
- The disclaimer line opens with "Read-only, in three sections:" and goes on to name all three
  sections (levels/zones, registry/champion, and the structure_tape-vs-v1 comparison) — not just
  the first one

---

### UT-25 — Insufficient-sample chip is clearly labeled and visually distinct (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/structure` (Comparison per-class table)

**Preconditions:**
- UT-06 passing; at least one class row shows an insufficient sample

**Steps:**
1. With a finished comparison on screen, locate a per-class table row whose sample size is below
   the minimum
2. Read its "sample" column

**Expected Result:**
- The chip reads exactly "insufficient sample (n < 5)" — the same literal text used consistently
  throughout the Comparison section
- The chip is amber/warning-colored, visually distinct from the "ok" label used on rows at or above
  the minimum, and sits next to the row's real n/net R/net $ numbers (not in place of them)

---

### UT-26 — Comparison section is reachable in one click, no hidden controls (ux)

**Type:** ux
**Priority:** P3
**Surface:** navigation → `/structure`

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301` (home)
2. Click "Structure" in the top navigation bar
3. Scroll down the resulting page until the Comparison section is visible

**Expected Result:**
- Clicking "Structure" from home (1 click) lands on `http://localhost:3301/structure` with no
  further navigation required
- The Comparison section is reachable purely by scrolling — no additional click, hidden tab, or
  collapsed accordion is needed to reveal it
- The section's own controls (dataset dropdown, "Run comparison" button) are immediately visible
  without further interaction

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Structure page loads with 3 sections | smoke | P1 | `/structure` |
| UT-02 | Comparison section static elements render | smoke | P1 | `/structure` |
| UT-03 | Dataset selector populates | smoke | P1 | `/structure` |
| UT-04 | Full comparison run end to end | happy-path | P1 | `/structure` |
| UT-05 | Side-by-side aggregates render | happy-path | P1 | `/structure` |
| UT-06 | Per-class A/B/C table renders | happy-path | P1 | `/structure` |
| UT-07 | Register line renders | happy-path | P1 | `/structure` |
| UT-08 | Founding baseline row renders | happy-path | P1 | `/structure` |
| UT-09 | Champion panel read-only v1/default | happy-path | P1 | `/structure` |
| UT-10 | Reference dataset honest non-survivor outcome | happy-path | P1 | `/structure` |
| UT-11 | Run button disabled until dataset chosen | validation | P2 | `/structure` |
| UT-12 | No datasets registered empty state | error | P2 | `/structure` |
| UT-13 | Backend unreachable at page load | error | P2 | `/structure` |
| UT-14 | Backend failure on POST (run-error) | error | P2 | `/structure` |
| UT-15 | Backend unreachable mid-poll | error | P2 | `/structure` |
| UT-16 | Failed backtest distinct card | error | P2 | `/structure` |
| UT-17 | Cancelled backtest distinct card | error | P2 | `/structure` |
| UT-18 | J-01 Levels & Zones still works | regression | P1 | `/structure` |
| UT-19 | J-01 chart not occluded | regression | P1 | `/structure` |
| UT-20 | J-02 Registry/champion still renders | regression | P1 | `/structure` |
| UT-21 | No champion testid collision | regression | P1 | `/structure` |
| UT-22 | 5-link nav intact | regression | P1 | all pages |
| UT-23 | /performance unaffected | regression | P1 | `/performance` |
| UT-24 | Header subtitle previews 3 sections | ux | P3 | `/structure` |
| UT-25 | Insufficient-sample chip clear | ux | P3 | `/structure` |
| UT-26 | Comparison reachable in 1 click | ux | P3 | nav → `/structure` |

**P1 tests must all pass for browser QA verdict to be PASS.** Per this phase's Definition of Done,
that includes not only smoke/happy-path but also the six regression checks (UT-18–UT-23), since
J-01/J-02/J-04 are named required-still-passing journeys, not merely low-risk carryovers.
