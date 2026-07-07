# Phase goal-structure_ui-iter-4 — UI Test Plan

**Phase:** goal-structure_ui-iter-4
**Date:** 2026-07-07
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL (cross-check steps only):** http://localhost:8301

---

## Scope & Priority Note

**This is a zero-diff evidence-capture iteration** — `git diff --stat -- apps/frontend` and `--
apps/backend` are both empty (confirmed by ui-impact-analyst and the dev handoff). Nothing below
tests a new capability; every case re-verifies a surface already shipped in iter-1 (J-01), iter-2
(J-02), or iter-3 (J-03). The point of running these cases is not "does the code exist" — it's
"does an independent, live, populated browser session prove it still renders honestly," which is
exactly what iter-3's browser-qa run failed to produce (SKIPPED 0/26, frontend unreachable at
dispatch time).

**Global precondition — blocks every case below:** `curl -sf http://localhost:3301` and
`curl -sf http://localhost:8301/health` must both return HTTP 200 before any case in this plan is
attempted. The functional test plan's TC-01/TC-02 own the exact curl mechanics and must pass
first; this plan assumes both already pass. If either is down, do not proceed — this is the exact
gap that produced iter-3's SKIP.

**Priority deviation (same rationale as iter-3's plan):** the test-design skill defaults
"regression tests with low risk" to P3. Here, the phase's Definition of Done names **J-01, J-02,
and J-04 as required-still-passing journeys** — a regression on any of them fails the phase. Cases
UT-12–UT-16 are therefore **P1**, not P3.

**Byte-match steps are this iteration's core Definition-of-Done requirement**, not a duplicate of
the functional test plan's own API-only checks (TC-01, TC-02, TC-13, TC-14 — pure curl/git-diff/log
checks with no browser action). UT-04, UT-05, UT-06, and UT-08 below embed a byte-match
cross-check because the phase spec explicitly requires proving "the UI recomputes nothing" via
live browser evidence, mirroring the ui-surface-map's own "What to Test" column for this iteration.
Each such case anchors its primary assertion in what's visually on screen first (an operator
reading the rendered card); the DevTools/curl step is the confirming cross-check, not the whole
test.

**Not re-litigated here:** the full historical set of error-state cases iter-3's plan already
covers (no-datasets-registered, backend-unreachable-at-load, POST-failure run-error, failed
backtest, cancelled backtest) — see `reports/phase-goal-structure_ui-iter-3-ui-test-plan.md`
UT-12–UT-17. This iteration's phase spec scopes only ONE such case back in, explicitly marked
"bonus, non-blocking" (UT-11 below), because iter-3's audit finding F1 named it as still
unexercised by any independent browser-qa run.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/structure` loads with all three sections (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Global precondition met (see above): both services confirmed up
- At least one dataset is registered on the backend (7 were registered as of iter-3's environment;
  verify count via the dropdown in UT-02)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load
3. Scroll from the very top of the page to the very bottom

**Expected Result:**
- The `<h1>` heading "Structure" is visible at the top
- Three stacked panels render in this order, top to bottom: "Levels & Zones", "Registry",
  "Comparison"
- No blank screen, no red/error banner anywhere on the page, no errors in the browser console
- This must render identically to iter-3's own equivalent check — any difference here is a
  regression, since zero frontend files changed this iteration

---

### UT-02 — Comparison section's idle-state elements render correctly (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure` (Comparison section)

**Preconditions:**
- UT-01 passing

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll to the bottom "Comparison" panel
3. Read the panel from top to bottom
4. Click the dropdown showing placeholder text "Choose a dataset…"
   (`data-testid="comparison-dataset-select"`) to open it

**Expected Result:**
- Top to bottom, the panel shows: a read-only disclaimer paragraph, a two-box row labeled
  "Champion (moved never by this view)" and "Founding baseline (PnL ledger)", the dataset
  dropdown, and a "Run comparison" button (`data-testid="comparison-run-button"`)
- The "Run comparison" button appears visually disabled (greyed out, not clickable) because no
  dataset is chosen yet
- Opening the dropdown shows "Choose a dataset…" as the first option, followed by one or more real
  dataset options each formatted as `<symbol> · <split> · <8-character id prefix>` (e.g.
  "AAPL · train · a1b2c3d4")
- No text reading "No datasets registered." appears (that is a different, non-default state — see
  the historical error cases referenced above if it does)

---

### UT-03 — User runs a full comparison end to end (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison section)

**Preconditions:**
- UT-02 passing
- Backend stays reachable for the whole duration of this test (do not stop it mid-run)

**Steps:**
1. Navigate to `http://localhost:3301/structure` and scroll to the Comparison section
2. Click the dataset dropdown (`data-testid="comparison-dataset-select"`) and select any dataset
   other than the "Choose a dataset…" placeholder
3. Click the "Run comparison" button (`data-testid="comparison-run-button"`)
4. Observe the button and the area below it immediately after clicking
5. Wait until neither result card reads "Queued…" or "Running…" anymore (typically well under 30
   seconds)

**Expected Result:**
- Immediately after step 3: the button's label changes to "Running…" and the button becomes
  disabled (prevents a double-submit)
- Two card slots appear side by side, labeled "v1 (champion strategy)" and "structure_tape", each
  initially showing "Queued…" or "Running…" (a "Running…" card also shows a live events-processed
  count)
- Once both finish, each card shows a definition list of numbers, a "Per-class (A/B/C)" table, and
  an amber register line — neither card is left spinning indefinitely
- **This is the primary evidence this iteration exists to capture** — screenshot this finished
  state for `reports/qa/goal-structure_ui-iter-4-evidence/`

---

### UT-04 — Side-by-side aggregates render and byte-match the backend (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison result cards)

**Preconditions:**
- UT-03 completed; both cards reached their finished state
- Browser DevTools available (Network tab), or terminal access to `curl` as an alternative

**Steps:**
1. On the finished "v1 (champion strategy)" card, read the five values under
   `data-testid="comparison-v1-n"`, `comparison-v1-net-r`, `comparison-v1-net-usd`,
   `comparison-v1-win_rate`, `comparison-v1-max-drawdown-r`
2. On the finished "structure_tape" card, read the same five fields under the matching
   `comparison-structure-tape-*` testids
3. Open DevTools → Network tab and find the `GET /research/backtests/{id}` request(s) the page
   already made for each id (or run `curl http://localhost:8301/research/backtests/<id>` for each
   id if you have terminal access), then open the JSON response
4. Compare each of the 10 on-screen values (5 per strategy) against the response's `aggregates`
   object field-for-field

**Expected Result:**
- Every field shows a real value — a number, or the honest text "no trades (n=0)" for
  `win_rate`/`max drawdown (R)` when a strategy took zero trades — never blank, "undefined", or
  "NaN"
- All 10 values match their corresponding `aggregates` field in the API response byte-for-byte — no
  rounding, reformatting, or divergence in either direction
- A mismatch on any single field is a FAIL — the app must never recompute or reformat a number the
  backend already computed

---

### UT-05 — Per-class A/B/C table renders and `insufficient_sample` byte-matches the backend (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison per-class table)

**Preconditions:**
- UT-03 completed; both cards reached their finished state

**Steps:**
1. Below the "v1 (champion strategy)" card's definition list, locate its "Per-class (A/B/C)" table
   and its three `data-testid="comparison-class-row"` rows
2. Below the "structure_tape" card, locate its own three `comparison-class-row` rows
3. For each row showing the chip `data-testid="comparison-insufficient-sample"`, note which class
   (A/B/C) and which strategy it belongs to
4. Using the same `GET /research/backtests/{id}` response from UT-04, compare each row's n/net
   R/net $ and `insufficient_sample` boolean against the matching entry in the response's
   `aggregates_by_class` array

**Expected Result:**
- Exactly three rows render per card, labeled "Class A", "Class B", "Class C" — always all three,
  even if a class took zero trades
- Every row's `insufficient_sample` chip state (present or absent) matches its
  `aggregates_by_class[i].insufficient_sample` value in the API response — no inverted or
  fabricated flag
- A row below the minimum sample size shows the chip "insufficient sample (n < 5)" in amber; a row
  at or above the minimum shows "ok" in that column instead

---

### UT-06 — Register line renders verbatim from the backend payload (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison register line)

**Preconditions:**
- UT-03 completed; both cards reached their finished state

**Steps:**
1. Below the "v1 (champion strategy)" card's per-class table, read the amber-bordered line under
   `data-testid="comparison-v1-register"`
2. Below the "structure_tape" card's per-class table, read the amber-bordered line under
   `data-testid="comparison-structure-tape-register"`
3. Compare both strings against the `register` field in each strategy's
   `GET /research/backtests/{id}` response (same call as UT-04)

**Expected Result:**
- Both lines read exactly: "simulated — assumed fees/slippage — not indicative of live results"
- Neither line reads a shorter or reworded variant (e.g. "simulated — not indicative of live
  results") — that would indicate a hardcoded frontend literal instead of the live payload value
- Both on-screen strings byte-match their respective `result.register` field in the API response

---

### UT-07 — Champion cross-check panel stays `v1`/`default` and is unmoved by running a comparison (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison Champion box)

**Preconditions:**
- UT-02 passing (page loaded, before running any comparison)

**Steps:**
1. Before clicking "Run comparison", read `data-testid="comparison-champion-strategy"` and
   `comparison-champion-profile` inside the "Champion (moved never by this view)" box
   (`data-testid="comparison-champion"`)
2. Confirm there is no button, link, dropdown, or other interactive control inside this box
3. Run a full comparison to completion (as in UT-03)
4. After both cards finish, re-read `comparison-champion-strategy` and `comparison-champion-profile`
   again
5. Compare both readings against the Registry section's own `champion-strategy`/`champion-profile`
   badge further up the page

**Expected Result:**
- Both before and after running the comparison, the box reads "v1" (strategy) and "default"
  (profile) — unchanged by the run
- Both values match the Registry section's own champion badge exactly
- No interactive control exists inside the Champion box — confirming there is no promotion path
  from this view

---

### UT-08 — Founding-baseline panel renders one of its two honest states (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison Founding-baseline box)

**Preconditions:**
- UT-02 passing

**Steps:**
1. Navigate to `http://localhost:3301/structure` and scroll to the Comparison section's "Founding
   baseline (PnL ledger)" box (`data-testid="comparison-founding-baseline"`) — no need to run a
   comparison first, this box loads independently on page mount
2. Read its contents

**Expected Result:**
- Exactly one of the following two states renders:
  (a) a populated `data-testid="comparison-founding-row"` showing a title, "candidate train net R",
      and "candidate hold-out net R" values, or
  (b) `data-testid="comparison-no-founding-row"` showing the exact text "No founding row yet — the
      PnL ledger is empty."
- Never a blank box, a permanently-spinning loader, or a fabricated number
- If (a), cross-check both net-R values against `GET /research/pnl/ledger`'s
  `rows.find(r => r.founding)` entry — they must match exactly

---

### UT-09 — Keyless `structure_tape` run shows the honest non-survivor outcome (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` (Comparison result cards)

**Preconditions:**
- UT-03 passing (comparison mechanics work)
- The backend's committed keyless reference dataset is registered in the dropdown. This test does
  not require knowing its exact name in advance — step 4 below is a self-check.

**Steps:**
1. Navigate to `http://localhost:3301/structure` and scroll to the Comparison section
2. Select a dataset from the dropdown and click "Run comparison"
3. Wait for both cards to finish, then inspect the "structure_tape" card's Per-class (A/B/C) table
   and its `comparison-structure-tape-win_rate` / `comparison-structure-tape-max-drawdown-r` fields
4. If the "structure_tape" card instead shows populated, non-insufficient numbers, repeat steps 2–3
   with a different dataset from the dropdown until the outcome below is observed at least once

**Expected Result:**
- On the correct reference dataset: all three `comparison-class-row` rows in the "structure_tape"
  card show the `comparison-insufficient-sample` chip, and `comparison-structure-tape-win_rate` /
  `comparison-structure-tape-max-drawdown-r` both read the literal text "no trades (n=0)" — never a
  bare "0"
- The Champion box (per UT-07) still reads "v1"/"default", unchanged
- **This is the specific evidence named in this iteration's Definition of Done** — screenshot this
  exact card state for `reports/qa/goal-structure_ui-iter-4-evidence/`

---

### UT-10 — "Run comparison" button stays disabled until a dataset is chosen (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure` (Comparison dataset select + Run button)

**Preconditions:**
- UT-02 passing

**Steps:**
1. Navigate to `http://localhost:3301/structure` and scroll to the Comparison section
2. Without touching the dataset dropdown, attempt to click "Run comparison"
   (`data-testid="comparison-run-button"`)
3. Open the dataset dropdown (`data-testid="comparison-dataset-select"`) and select any real
   dataset (not the "Choose a dataset…" placeholder)
4. Attempt to click "Run comparison" again

**Expected Result:**
- In step 2: the button does not respond — visually disabled, no backtests are created (confirm
  via the DevTools Network tab that no `POST /research/backtests` request fires)
- In step 4: the button is now clickable, and clicking it starts the comparison (label changes to
  "Running…")

---

### UT-11 — Bonus (non-blocking): an honest degraded state not yet independently photographed (error)

**Type:** error
**Priority:** P3 — explicitly named "bonus, non-blocking" in the phase spec; do not fail the phase
verdict over this case alone
**Surface:** `/structure` (Comparison poll loop / per-side terminal states)

**Preconditions:**
- A comparison is running, or you have the ability to stop/restart the backend process mid-poll

**Steps:**
1. Start a comparison (select a dataset, click "Run comparison")
2. While at least one card still shows "Queued…" or "Running…", stop the backend process
3. Wait about 1 second and read the Comparison section
4. Restart the backend and wait a few seconds
   — OR, as an alternative degraded state to try instead: while one backtest is still
   `queued`/`running`, issue `POST http://localhost:8301/research/backtests/{that_id}/cancel` (curl,
   or the browser's fetch console) and observe that side's card

**Expected Result:**
- Poll-error path: within roughly 700ms of the backend stopping, the text "Backend unreachable
  while polling — showing the last known status." appears; the last-known state stays visible (not
  blanked); after the backend restarts, the notice disappears on its own and polling resumes with
  no manual page refresh
- Cancel path: that side's card shows exactly "This backtest was cancelled before it finished. A
  partial simulated result is never served — no result is shown." with no aggregates, no per-class
  table, and no register line for that side; the other side continues normally
- Either outcome, if captured, clears iter-3's audit finding F1 (these states were still
  unexercised by any independent browser-qa run) — non-blocking if not practical to trigger in this
  environment

---

### UT-12 — J-01 regression: Levels & Zones chart and confluence zones render, un-occluded (regression)

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
4. Observe the chart canvas (`data-testid="structure-chart-canvas"`) and the zones table below it
5. Scroll the page down past the Registry and Comparison sections and back up to the chart

**Expected Result:**
- The chart renders candles and dashed S/R level lines, exactly as before this iteration (zero
  frontend files changed)
- No empty-state or loading overlay covers the chart canvas at any point — the overlay's z-index
  must sit above the `lightweight-charts` canvas per the iter-1 fix, never the reverse
- The confluence-zones table renders below the chart with `data-testid="zone-row"` rows, each
  showing a `zone-class-badge` (A/B/C) and a `zone-score`
- No layout shift, error, or blank area caused by the Comparison section further down the page

---

### UT-13 — J-02 regression: Registry section renders correctly with no champion-badge testid collision (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure` (Registry section)

**Preconditions:**
- UT-01 passing

**Steps:**
1. Navigate to `http://localhost:3301/structure` and scroll to the middle "Registry" section
2. Confirm two `data-testid="strategy-card"` elements render, one for `v1` and one for
   `structure_tape`, each showing its class-scaled stop/reward/size maps
3. Read `data-testid="champion-strategy"` and `champion-profile` in this section
4. Open the browser DevTools element inspector and search the full page DOM for
   `[data-testid="champion-strategy"]` and separately for
   `[data-testid="comparison-champion-strategy"]`

**Expected Result:**
- Both strategy cards render with distinct parameters, matching their pre-iter-4 (and pre-iter-3)
  values exactly
- The Registry's own champion badge reads "v1" (strategy) / "default" (profile)
- Exactly one element matches `[data-testid="champion-strategy"]` (in Registry) and exactly one
  matches `[data-testid="comparison-champion-strategy"]` (in Comparison) — no duplicates of either,
  confirming iter-2's audit finding T2 has not regressed

---

### UT-14 — J-04 regression: Top navigation still shows exactly five links (regression)

**Type:** regression
**Priority:** P1
**Surface:** top navigation bar (all pages)

**Preconditions:**
- None

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Locate the top navigation bar (`data-testid="app-nav"`)
3. Count the `data-testid="nav-link"` elements inside it and read each one's visible label
4. Click each link in turn and confirm it navigates to the expected route with no console error

**Expected Result:**
- Exactly five links render, labeled (in order) Cockpit, Journal, Studies, Performance, Structure
- Each link's `href` matches the live `GET /meta/ui-routes` payload
- Clicking each link navigates there successfully with no console error, no missing, duplicated, or
  renamed link

---

### UT-15 — J-04 regression: `/performance` is unaffected by `/structure` changes (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/performance`

**Preconditions:**
- None

**Steps:**
1. Navigate directly to `http://localhost:3301/performance` by typing the URL (not by clicking
   through from `/structure`)
2. Read the `data-testid="champion-summary"` block

**Expected Result:**
- The page loads normally with no console errors
- `champion-summary` shows `champion-strategy` = "v1" and `champion-profile` = "default"
- Nothing on this page references or is affected by any `/structure`-only testid (`comparison-*`)

---

### UT-16 — J-04 regression: Cockpit sim-ticker flows (SIM-BUYER / SIM-SELLER) still settle correctly (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/` (Cockpit)

**Preconditions:**
- None — `SIM-BUYER` and `SIM-SELLER` are built-in reserved simulation tickers that run a scripted
  scenario without external market data

**Steps:**
1. Navigate to `http://localhost:3301/` (Cockpit)
2. Type "SIM-BUYER" into the TopBar's symbol/ticker field (the idle-state hint text reads "Try:
   SIM-BUYER") and submit it (press Enter, or click the field's adjacent load control if one is
   shown)
3. Observe the idle placeholder area
4. Let the scenario run until it closes
5. Repeat steps 2–4 typing "SIM-SELLER" instead

**Expected Result:**
- After submitting, the idle placeholder is replaced by a populated `data-testid="thesis-strip"`
  with a visible `entry-checklist` — no `watch-validation` error message appears, and no
  `delivery-lag` indicator gets stuck showing
- Once the scenario closes, `data-testid="realized-r"` and `recorded-marks` populate with an actual
  value — neither stays blank nor shows an error
- Both `SIM-BUYER` and `SIM-SELLER` complete this same way — this flow shares no code with
  `/structure`, so any failure here is a genuine, unrelated regression, not something this
  iteration's zero-diff work could have caused

---

### UT-17 — Comparison section is reachable in one click with no hidden controls (ux)

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
- The Comparison section is reachable purely by scrolling — no extra click, hidden tab, or
  collapsed accordion is needed to reveal it
- The section's own controls (dataset dropdown, "Run comparison" button) are immediately visible
  without further interaction

---

### UT-18 — Insufficient-sample chip and honest "no trades" text are clearly labeled (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/structure` (Comparison per-class table)

**Preconditions:**
- UT-05 or UT-09 passing (at least one class row shows an insufficient sample, or a keyless run
  shows "no trades")

**Steps:**
1. With a finished comparison on screen showing at least one insufficient-sample row, read its
   "sample" column
2. On the same or a different finished card, read the `win_rate`/`max drawdown (R)` fields for a
   strategy that took zero trades

**Expected Result:**
- The sample column chip reads exactly "insufficient sample (n < 5)" — the same literal text used
  consistently throughout the section — and is amber/warning-colored, visually distinct from the
  "ok" label used on qualifying rows
- The zero-trade fields read exactly "no trades (n=0)" rather than a bare "0" or a blank cell — an
  operator unfamiliar with the codebase can tell at a glance this is an honest "nothing happened"
  state, not a broken or missing number

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/structure` loads with 3 sections | smoke | P1 | `/structure` |
| UT-02 | Comparison idle-state elements render | smoke | P1 | `/structure` |
| UT-03 | Full comparison run end to end | happy-path | P1 | `/structure` |
| UT-04 | Aggregates byte-match backend | happy-path | P1 | `/structure` |
| UT-05 | Per-class table + insufficient_sample byte-match | happy-path | P1 | `/structure` |
| UT-06 | Register line verbatim | happy-path | P1 | `/structure` |
| UT-07 | Champion cross-check unmoved | happy-path | P1 | `/structure` |
| UT-08 | Founding-baseline honest state | happy-path | P1 | `/structure` |
| UT-09 | Keyless non-survivor honest outcome | happy-path | P1 | `/structure` |
| UT-10 | Run button disabled until dataset chosen | validation | P2 | `/structure` |
| UT-11 | Bonus degraded state (poll-error/cancelled) | error | P3 | `/structure` |
| UT-12 | J-01 chart/zones un-occluded | regression | P1 | `/structure` |
| UT-13 | J-02 registry + no testid collision | regression | P1 | `/structure` |
| UT-14 | J-04 5-link nav intact | regression | P1 | all pages |
| UT-15 | J-04 `/performance` unaffected | regression | P1 | `/performance` |
| UT-16 | J-04 Cockpit SIM-BUYER/SIM-SELLER | regression | P1 | `/` |
| UT-17 | Comparison reachable in 1 click | ux | P3 | nav → `/structure` |
| UT-18 | Insufficient-sample/no-trades labeling clear | ux | P3 | `/structure` |

**P1 tests must all pass for browser QA verdict to be PASS.** Per this phase's Definition of Done,
that includes not only smoke/happy-path but also the five regression checks (UT-12–UT-16), since
J-01/J-02/J-04 are named required-still-passing journeys, not merely low-risk carryovers. UT-03 and
UT-09 are the two highest-value screenshots for `reports/qa/goal-structure_ui-iter-4-evidence/` —
they are the direct evidence this iteration's Definition of Done requires to flip J-03 from
`unknown` to `passing`.
