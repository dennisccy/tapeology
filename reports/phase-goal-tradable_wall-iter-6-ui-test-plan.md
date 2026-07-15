# Phase goal-tradable_wall-iter-6 — UI Test Plan

**Phase:** goal-tradable_wall-iter-6 (J-05: `/structure` decluttered — Tradable Map default + Case Studies + Edge Report)
**Date:** 2026-07-15
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301 (referenced only for the "is it running" troubleshooting check — every test below is driven through the frontend)

---

## Shared Reference Data

These values were live-verified by the developer against the operator's real, already-populated
12-symbol panel store (see `docs/handoffs/goal-tradable_wall-iter-6-dev.md`, "Live smoke test").
Tests below reference them; if your environment's data has changed since this plan was written
(e.g. new bars/events recorded), the exact numbers may drift slightly — the STRUCTURE of each
expected result (band count, honest-state copy, field presence) should not.

- Pinned case: symbol `AAPL`, as-of `2026-06-22T15:00:00Z` → Tradable Map returns exactly **10
  bands**; the top resistance band spans **300.17–302.27**, `class: "A"`, `round_number: true`,
  `quality_score: 153.0` (highest of all 10; runner-up is 82.67).
- `GET /research/setups` currently holds **801** events; **13** carry
  `reaction_boundary_truncated: true`. The two AAPL `2026-06-22` events both have `reaction:
  "rejected"` with negative forward returns at both configured horizons (**78** and **234** bars).
- A recency-boundary example: AAPL dated **2026-07-13** → `reaction: "chopped"`,
  `reaction_boundary_truncated: true`, `effective_reaction_horizon_bars: 77`, `tape_timeline: []`.
- `GET /research/edge-report` is currently **honestly empty** on the operator's real store (the
  only recorded datasets are for symbol `PG`, which is not a watchlist symbol) — this is the
  CORRECT, expected render right now, not a defect.
- The 12 watchlist symbols are: `AAPL, MSFT, NVDA, TSLA, AMZN, GOOGL, META, AMD, NFLX, SPY, QQQ,
  JPM`.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->
<!-- Each test MUST have exact steps and specific expected results. -->

---

### UT-01 — `/structure` loads with every section present, no crashes (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend is running at http://localhost:3301 and the backend is reachable
- No login is required (this application has no authentication)
- Fresh page load — no symbol/as-of has been submitted yet this browser session

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to finish loading (network activity settles)
3. Read the page from top to bottom without clicking anything

**Expected Result:**
- The heading "Structure" is visible at the top of the page
- Directly below it, a paragraph beginning "Load a symbol and an as-of time to see its tradable level map…" is visible
- A Load form is visible with a "Symbol" field, an "As-of (UTC, ISO-8601)" field, and a "Load" button
- A "Tradable Map" panel is visible showing the text "Choose a symbol and an as-of time, then Load, to see its tradable level map." — no bands table and no chart are rendered
- A "Show raw levels" button is visible directly below the Tradable Map panel; no "Price chart — S/R levels" or "Confluence zones" panel is visible below it
- A "Case Studies" panel is visible below that — either a brief pulsing loading placeholder or (once it resolves within a second or two) a table of events; no red/amber error text
- An "Edge Report" panel is visible below Case Studies — either a brief loading placeholder or (once resolved) content; no error text
- Scrolling further down, "Fetch from Yahoo Finance", "Registry", and "Comparison" panels are all present
- No blank white screen, no "Application error" text, and no unhandled crash appears anywhere on the page

---

### UT-02 — Loading a pinned symbol renders the Tradable Map as the default view (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Continuing from UT-01, or a fresh load of `http://localhost:3301/structure`
- The backend's bar store has AAPL data recorded through at least 2026-06-22 (true on the operator's populated 12-symbol panel store)

**Steps:**
1. Type `AAPL` into the "Symbol" field of the Load form (top of the page)
2. Type `2026-06-22T15:00:00Z` into the "As-of (UTC, ISO-8601)" field beside it
3. Click the "Load" button
4. Wait for the "Tradable Map" panel to finish loading
5. In the bands table beneath the chart, count the visible rows, then find the row whose range falls between roughly 300 and 302

**Expected Result:**
- The Tradable Map panel's idle message is replaced by a "Map basis (prior completed session close):" line showing a date/time earlier than 2026-06-22 (e.g. 2026-06-18)
- A candlestick price chart appears directly below the basis line
- Below the chart, a table lists **exactly 10 rows** — not more, not the old raw ~1,800-line list
- The ~300–302 row shows: range text such as "300.17–302.27", class column reading "Class A", a "round number" badge, and the **highest score value of all 10 rows** (153.0)
- The "Show raw levels" button below still reads "Show raw levels" (unchanged, still off) — this Load action did not toggle it

---

### UT-03 — Band lines render solid and color-coded on the chart (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Continuing directly from UT-02 (AAPL, `2026-06-22T15:00:00Z` already loaded, Tradable Map populated)

**Steps:**
1. Look at the candlestick chart inside the "Tradable Map" panel
2. Locate the horizontal lines crossing the chart near the 300–302 price level
3. Note whether a text label reading something like "R class A · score 153 · round" is visible directly on or beside that line (if not immediately visible, look at the price axis on the right edge of the chart, which carries a colored price tag for each line)

**Expected Result:**
- The lines crossing the chart at band prices are **solid** (unbroken), not dashed
- Resistance-side lines (like the ~300–302 one) are rose/pink; any support-side lines are emerald/green
- The candlesticks themselves use the same rose (down candles) / emerald (up candles) color pair, so the chart reads as one visual family
- A label describing the band (side, class, score, and "round" where applicable) is discoverable at or near the line, e.g. "R class A · score 153 · round"

---

### UT-04 — "Show raw levels" toggle reveals/hides the unchanged prior view (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Continuing from UT-02/UT-03 (AAPL, `2026-06-22T15:00:00Z` loaded; Tradable Map populated)

**Steps:**
1. Confirm the button below the Tradable Map panel currently reads "Show raw levels", and that no "Price chart — S/R levels" or "Confluence zones" panel is visible
2. Click the "Show raw levels" button
3. Wait for the page to re-render, then scroll to inspect the newly revealed content
4. Click the same button again (it should now read "Hide raw levels")

**Expected Result (immediately after step 2):**
- The button's label changes from "Show raw levels" to "Hide raw levels"
- A "Price chart — S/R levels" panel appears, containing its own candlestick chart with **dashed** gray level lines (not solid colored band lines) and a "feed" badge reading "Yahoo Finance" above the chart
- Directly below it, a "Confluence zones" panel appears listing zone cards, each labeled "Class A", "Class B", or "Class C" with a "score" value, and a table of member levels (price / timeframe / type columns)
- This view looks exactly as it did before this phase's changes — same chart style, same zone cards, same data

**Expected Result (after step 4):**
- The "Price chart — S/R levels" and "Confluence zones" panels disappear
- The button label reverts to "Show raw levels"
- The Tradable Map above remains visible and populated throughout — unaffected by the toggle

---

### UT-05 — Case Studies registry loads and filters by symbol and reaction (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301, backend reachable
- The backend has already scanned band-touch events (true on the operator's real store — 801 events)
- No Load-form submission is required — Case Studies fetches automatically when the page loads

**Steps:**
1. Navigate to `http://localhost:3301/structure` (or continue from an already-open tab)
2. Scroll down to the "Case Studies" panel and wait for its table to finish loading
3. Count the visible rows — note the total
4. Type `AAPL` into the "Symbol" field directly above the Case Studies table (NOT the Load form's Symbol field at the top of the page)
5. Observe the table
6. Select `rejected` from the "Reaction" dropdown directly beside that Symbol field
7. Observe the table again
8. Clear the Symbol field (delete "AAPL") and reset the Reaction dropdown to "All"

**Expected Result:**
- After step 3: the table shows columns "symbol", "session", "band", "reaction", "forward returns", with far more than 10 rows (dozens+)
- After step 5: only rows whose "symbol" column reads "AAPL" remain
- After step 7: only AAPL rows whose "reaction" column reads "rejected" remain (any "broke"/"chopped" AAPL rows disappear)
- After step 8: the full, unfiltered row count from step 3 returns instantly, with no page reload or flicker (this is a client-side filter over already-loaded data, not a fresh network round-trip)

---

### UT-06 — Case Studies drill-in shows the pinned AAPL 2026-06-22 event (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- The Case Studies table is loaded and visible (continue from UT-05)

**Steps:**
1. Type `AAPL` into the Case Studies Symbol filter field to narrow the list
2. Find the row with session date `2026-06-22` (there are two such rows)
3. Click anywhere on that row
4. Wait for the "Case Studies — drill-in" panel to open below the table

**Expected Result:**
- A "Case Studies — drill-in" panel opens showing a "symbol / session" line reading "AAPL · 2026-06-22", a "band" line describing the touched price range, and a "reaction" value reading `rejected`
- A "forward returns" line shows two values labeled `78b:` and `234b:`, and **both display a leading minus sign** (negative numbers)
- Below that, a "Tape timeline" label is visible, followed by either a list of tape-state entries or the exact text "No recorded tape for this event." — either is a valid, honest result; the area must never be blank
- Clicking a different Case Studies row updates this same drill-in panel to the newly selected event

---

### UT-07 — Drill-in honestly discloses a truncated-horizon (recency-boundary) event (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- The Case Studies table is loaded; filters are clear (showing the full list)

**Steps:**
1. Type `AAPL` into the Case Studies Symbol filter field
2. Scan the filtered rows for one carrying a small amber badge reading "truncated horizon" next to its reaction value — on the operator's real store this is the row dated `2026-07-13` (the most recent stored AAPL session)
3. Click that row
4. Wait for the drill-in panel to update

**Expected Result:**
- The row's "reaction" column shows a reaction value (e.g. `chopped`) immediately followed by a small amber "truncated horizon" badge
- The opened drill-in shows an amber notice beginning "Reaction read at a truncated 77-bar horizon — the store does not yet hold the full configured horizon past this touch." (the exact bar count may differ if store data has grown since this plan was written — the sentence must still start with "Reaction read at a truncated")
- The drill-in's forward-returns line shows a dash (`—`) for horizons the store does not yet reach, rather than a fabricated number
- The "Tape timeline" section for this event shows the text "No recorded tape for this event."
- This is visibly different from the pinned 2026-06-22 event opened in UT-06, which shows no truncation notice at all

---

### UT-08 — Case Studies distinguishes "no match" from "nothing exists yet" (UX)

**Type:** ux
**Priority:** P3
**Surface:** `/structure`

**Preconditions:**
- The Case Studies table is loaded with its full, real (non-empty) event list

**Steps:**
1. Reset the Reaction dropdown to "All"
2. Type `ZZZZZ` (a symbol that does not exist in the registry) into the Case Studies Symbol filter field
3. Read the panel content
4. Clear the Symbol field afterward to restore the full list

**Expected Result:**
- The table disappears, replaced by the message "No events match these filters." with the detail line "The registry has rows — this filter combination simply matches none."
- This wording is visibly distinct from the message that would appear if the registry itself had zero events ("No band-touch events scanned yet.", with no detail line) — the two states never share identical copy
- After step 4, the full table returns

---

### UT-09 — An invalid as-of value is rejected honestly, not silently defaulted (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301, backend reachable

**Steps:**
1. Navigate to `http://localhost:3301/structure` (a fresh load, or clear the existing As-of field)
2. Type `AAPL` into the Load form's "Symbol" field
3. Type `not-a-date` into the Load form's "As-of (UTC, ISO-8601)" field
4. Click the "Load" button
5. Wait for the Tradable Map panel to respond

**Expected Result:**
- The Tradable Map panel does **not** silently load data for "now" or any other fallback date
- An amber panel appears in place of the map showing the exact text "as_of must be an ISO date-time"
- Directly beneath that message, the text "Nothing cached and nothing fabricated is shown in its place." is visible
- No bands table and no chart render

---

### UT-10 — A symbol with no recorded bar history shows an honest empty state (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301, backend reachable
- Pick a symbol you are confident has never been fetched on this environment — not one of the 12 watchlist symbols (`AAPL, MSFT, NVDA, TSLA, AMZN, GOOGL, META, AMD, NFLX, SPY, QQQ, JPM`) and not previously typed into the "Fetch from Yahoo Finance" panel on this environment. This plan uses `IBM` as an example.

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `IBM` into the Load form's "Symbol" field
3. Type `2026-06-22T15:00:00Z` into the "As-of (UTC, ISO-8601)" field
4. Click the "Load" button
5. Wait for the Tradable Map panel to respond

**Expected Result:**
- The Tradable Map panel shows the text "No bar series recorded for IBM." with the detail line "Recording historical bars needs provider credentials."
- No bands table, no chart, and no crash/blank area appears
- If instead a populated Tradable Map appears, `IBM` was already recorded on this environment — repeat the test with a different symbol you are certain is unfetched

---

### UT-11 — Edge Report renders its honest empty state, not a blank or endless spinner (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301, backend reachable
- On the operator's current real data store, no watchlist-symbol trade recordings exist yet, so the honest empty state below is the CORRECT current outcome (see "Shared Reference Data" above)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll down to the "Edge Report" panel (below Case Studies)
3. Wait a few seconds for it to finish loading

**Expected Result:**
- An amber disclosure line reading "simulated — assumed fees/slippage — not indicative of live results" is visible
- Below it, the message "No edge-report cells yet." appears, with detail text "No recorded dataset has resolved an owning, classified scan event — an honest, valid outcome, never hidden."
- The panel does **not** show a spinner that never resolves, and does **not** show a blank area
- (If a credentialed trade recording has since been added for a watchlist symbol, this panel may instead show populated "Train"/"Hold-out" tables with strategy/class/side/reaction rows — that is also a valid outcome; either way the panel must show real content, never a blank space)

---

### UT-12 — Era-5 "Fetch from Yahoo Finance" control and provenance badge still work (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301, backend reachable, outbound internet access available for the keyless Yahoo Finance fetch

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll down past Tradable Map, Case Studies, and Edge Report to the "Fetch from Yahoo Finance" panel
3. Type `AAPL` into its "Symbol" field
4. Select `1d` from the "Timeframe" dropdown
5. Type `2026-06-01T00:00:00Z` into "Start (UTC, ISO-8601)"
6. Type `2026-06-04T00:00:00Z` into "End (UTC, ISO-8601)"
7. Click the "Fetch from Yahoo Finance" button
8. Wait for the button label to stop reading "Fetching…"
9. Scroll back up and turn on "Show raw levels" (if not already on)

**Expected Result:**
- No error panel appears below the fetch form after the fetch completes
- The Tradable Map and (once toggled on) raw-levels chart automatically reload with the AAPL window just fetched
- A "feed" badge reading "Yahoo Finance" is visible directly above the raw-levels chart
- The framing text above the Fetch form reads "...the Tradable Map and Levels & Zones sections above load the fetched symbol and window automatically." — confirming the copy was updated for its new lower position on the page

---

### UT-13 — Era-5 Registry section still lists strategies and the champion (regression)

**Type:** regression
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301, backend reachable

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll down to the "Registry" panel (below "Fetch from Yahoo Finance")

**Expected Result:**
- A "Champion" box shows a "strategy" value and a "profile" value (e.g. `v1` / `default`)
- Below it, three strategy cards are listed for `v1`, `structure_tape`, and `structure_tape_map`
- Each card shows "entry rule", "r_stop", "state_flip", "horizon (seconds)", and "dataset_end" values (plus "reward_target" where the strategy carries one)
- No error panel or blank area appears in place of this content

---

### UT-14 — Era-5 Comparison section still runs a structure_tape-vs-v1 comparison (regression)

**Type:** regression
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301, backend reachable
- At least one dataset is registered (true on the operator's real store)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Scroll to the bottom "Comparison" panel
3. Select any dataset from the "Dataset" dropdown
4. Click the "Run comparison" button
5. Wait for the button to stop reading "Running…"

**Expected Result:**
- Two side-by-side result panels appear, labeled "v1 (champion strategy)" and "structure_tape"
- Each panel shows n / net R / net $ / win_rate values, or an in-progress/failed/cancelled status if the job hasn't reached a terminal state yet (wait a few more seconds and re-check if so)
- No error panel replaces both result panels
- The "Champion (moved never by this view)" box and "Founding baseline (PnL ledger)" box above the form still show data, unchanged from before this phase

---

### UT-15 — "Structure" remains reachable from top navigation with no new nav entry (UX)

**Type:** ux
**Priority:** P2
**Surface:** navigation / `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301

**Steps:**
1. Navigate to `http://localhost:3301` (or any other page in the app)
2. Look at the top navigation bar
3. Click the "Structure" link in it

**Expected Result:**
- The top navigation bar shows the same set of links as before this phase — no new item was added for "Tradable Map", "Case Studies", or "Edge Report"
- Clicking "Structure" navigates to `http://localhost:3301/structure`
- All three new sections are reachable simply by landing on this one existing page — no additional navigation is required to find them

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | `/structure` loads with every section present | smoke | P1 | `/structure` |
| UT-02 | Load AAPL 2026-06-22 renders Tradable Map (≤10 bands, pinned band) | happy-path | P1 | `/structure` |
| UT-03 | Band lines render solid and color-coded on the chart | happy-path | P1 | `/structure` |
| UT-04 | "Show raw levels" toggle reveals/hides the unchanged prior view | happy-path | P1 | `/structure` |
| UT-05 | Case Studies registry loads and filters by symbol/reaction | happy-path | P1 | `/structure` |
| UT-06 | Case Studies drill-in shows the pinned AAPL 2026-06-22 event | happy-path | P1 | `/structure` |
| UT-07 | Drill-in discloses a truncated-horizon (boundary) event honestly | happy-path | P1 | `/structure` |
| UT-08 | Case Studies distinguishes "no match" from "nothing exists yet" | ux | P3 | `/structure` |
| UT-09 | Invalid as-of value is rejected, not silently defaulted | validation | P2 | `/structure` |
| UT-10 | Unfetched symbol shows an honest "no bar series" state | error | P2 | `/structure` |
| UT-11 | Edge Report renders its honest empty state | happy-path | P1 | `/structure` |
| UT-12 | Era-5 Fetch-from-Yahoo control + provenance badge still work | regression | P1 | `/structure` |
| UT-13 | Era-5 Registry section still lists strategies + champion | regression | P2 | `/structure` |
| UT-14 | Era-5 Comparison section still runs a comparison | regression | P1 | `/structure` |
| UT-15 | "Structure" nav entry unchanged; new sections need no extra navigation | ux | P2 | navigation / `/structure` |

**P1 tests must all pass for browser QA verdict to be PASS.** (UT-01, UT-02, UT-03, UT-04, UT-05,
UT-06, UT-07, UT-11, UT-12, UT-14 — 10 of 15.)

**Out of scope for this plan** (covered instead by `reports/qa/goal-tradable_wall-iter-6-test-plan.md`
or by non-browser gates): the `setups.py` cache-atomicity concurrency test (TC-01/TC-18, backend-only,
no UI surface); the malformed-`as_of` 422 at the raw HTTP layer (TC-12, covered here at the UI layer
instead by UT-09); TypeScript compilation (TC-19); DevTools/network-tab zero-recomputation tracing
(TC-17) — the coherence-auditor covers zero-recomputation at the code level, and every expected
result above already asserts the on-screen value against its known-correct backend figure.
