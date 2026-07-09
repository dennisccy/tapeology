# Phase goal-yahoo_fetch-iter-2 — UI Test Plan

**Phase:** goal-yahoo_fetch-iter-2
**Date:** 2026-07-09
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301 (needed only for the curl setup steps in UT-05/UT-06 — this iteration's one reachable new capability has no UI trigger yet)

---

## Scope note (read before running)

This iteration shipped **zero frontend file changes** (`git diff --stat -- apps/frontend/` is empty
— confirmed independently by the ui-impact-analyst and the dev handoff). `Frontend Present: yes` is
set in the execution plan for one deliberate, mechanical reason: it makes the pipeline's browser-qa
lane run and emit evidence for two **required-still-passing** journeys this iteration must not
break — J-01 (Structure still renders real Yahoo candles) and J-06 (Cockpit/Journal/Studies/
Performance/Structure all render unbroken, feed badge still "Simulated").

Unlike iter-1 (whose backend change was 100% invisible from the browser), this iteration is not
purely inert: the backend now serves five more timeframes (`1w`, `1h`, `5m`, `1m`, plus the derived
`4h`) instead of only `1d`, and `/structure`'s **pre-existing, unmodified** series picker
(`pickRepresentativeSeries()` / `TIMEFRAME_ORDER` in `apps/frontend/app/structure/page.tsx`) and
chart caption already handle every timeframe string generically. So the first time one of these new
series is fetched for a symbol — today, only via a direct API call, since the `/structure` "Fetch
from Yahoo Finance" button itself is deferred to a later iteration (J-05) — the very next page load
renders it, with zero frontend code change. UT-05 and UT-06 below exercise exactly that
reachable-but-indirect capability (each with a one-line curl **setup** step); every other test case
is a regression check.

Regression coverage here is deliberately narrower than iter-1's (which, having no happy-path content
of its own, spread wide across nav links, the journal detail page, and studies form fields).
This iteration's actual diff touches only `providers/adapters/yahoo.py`, `providers/adapters/base.py`,
and `research/routes.py` — so regression coverage below is concentrated on the two surfaces with a
real dependency on that code (`/structure`'s chart/levels, and the Cockpit's feed-basis badge, which
shares the "which vendor served this data" concern) rather than re-walking every page interaction
iter-1 already proved works.

None of the test cases below duplicate the functional/API test plan at
`reports/qa/goal-yahoo_fetch-iter-2-test-plan.md` (TC-01–TC-20, which already covers the interval
map, `4h` OHLC math, error-taxonomy status codes, and dependency/config-diff checks at the
API/pytest level) — everything here is what a person looking at a browser screen would actually see.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Structure `/structure` loads without errors (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend is running at http://localhost:3301 and the backend at http://localhost:8301
- No login is required (the app has no authentication)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load

**Expected Result:**
- The heading "Structure" is visible
- Below it, a sentence describing "Deterministic support/resistance levels and A/B/C confluence
  zones..." is visible
- A form is visible with a "Symbol" field (placeholder "e.g. PG"), an "As-of (UTC, ISO-8601)" field
  (placeholder "2026-06-09T21:00:00Z"), and a "Load" button
- The "Load" button appears greyed out / disabled (no symbol or as-of typed yet)
- Below the form, the message "Choose a symbol and an as-of time, then Load, to see its S/R levels
  and confluence zones." is visible
- Further down the page, a "Registry" panel is visible; within a few seconds it resolves to a
  "Champion" box showing "strategy" and "profile" values (or an honest amber "could not be loaded"
  panel only if the backend is genuinely unreachable — never a blank gap)
- Below that, a "Comparison" panel is visible
- No red error banner anywhere on the page; no blank white screen
- No errors in the browser console

---

### UT-02 — Cockpit `/` loads with Simulated mode active by default (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running
- No watch is currently active (fresh page load)

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Wait for the page to fully load

**Expected Result:**
- The top navigation bar is visible with 5 links: "Cockpit", "Journal", "Studies", "Performance",
  "Structure"
- A 3-way toggle with buttons "Live", "Historical", "Simulated" is visible; "Simulated" is already
  visually highlighted/pressed (no click needed)
- Since no ticker is watched, the main area shows the heading "No ticker watched" and the hint text
  "Try: SIM-BUYER"
- No red error banner is visible; no errors in the browser console

---

### UT-03 — Structure "Load" button stays disabled until both Symbol and As-of are filled (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Frontend and backend running

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Without typing anything, look at the "Load" button
3. Type `AAPL` into the "Symbol" field only; leave "As-of (UTC, ISO-8601)" empty
4. Look at the "Load" button again
5. Now also type `2026-07-02T00:00:00Z` into the "As-of (UTC, ISO-8601)" field
6. Look at the "Load" button a third time

**Expected Result:**
- Step 2: the "Load" button is greyed out and not clickable
- Step 4: the "Load" button is still greyed out — a Symbol alone is not enough to enable it
- Step 6: the "Load" button is now enabled (solid styling, clickable) — both fields carry text
- At no point does the page submit early or show an error while fields are incomplete

---

### UT-04 — Structure shows the explicit "no bar series recorded" honest state for a never-fetched symbol (error / honest-state)

**Type:** error
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- A symbol string that has never had any bar series fetched in this environment. `ZZTEST` is used
  below; if that string happens to already have data, substitute any other unused symbol.

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `ZZTEST` into the "Symbol" field
3. Type `2026-07-02T00:00:00Z` into the "As-of (UTC, ISO-8601)" field
4. Click the "Load" button

**Expected Result:**
- Within a few seconds, the message "No bar series recorded for ZZTEST." appears, with the detail
  line "Recording historical bars needs provider credentials."
- No candlestick chart and no "Confluence zones" panel appear; no crash, no blank page
- This is an intentional honest-empty state (distinct from the amber degraded-backend panel), not an
  error banner — confirms this iteration's backend change didn't disturb the pre-existing no-data
  path

---

### UT-05 — A freshly-fetched Yahoo `1h` series renders on Structure (happy path — the iteration's one reachable new capability; also serves as the J-01 regression check)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Backend running at http://localhost:8301; a terminal available to run curl commands
- Per the phase's Definition of Done, J-01 may be re-verified with either a `1d` or `1h` fetch —
  this test uses `1h` because it also demonstrates this iteration's actual new capability at the
  same time

**Steps:**
1. (Optional sanity check) Run: `curl -s http://localhost:8301/research/bars | grep -o
   "\"symbol\":\"AAPL\",\"timeframe\":\"1h\""` — if this returns a match, AAPL `1h` is already
   registered in this environment; you can skip straight to step 3
2. Run: `curl -s -X POST http://localhost:8301/research/bars -H "Content-Type: application/json" -d
   '{"symbol":"AAPL","timeframe":"1h","start":"2026-06-25T00:00:00Z","end":"2026-07-02T00:00:00Z"}'`
3. Navigate to `http://localhost:3301/structure`
4. Type `AAPL` into the "Symbol" field
5. Type `2026-07-02T00:00:00Z` into the "As-of (UTC, ISO-8601)" field
6. Click the "Load" button

**Expected Result:**
- Step 2: the curl response is HTTP 200 with a `bar_series` object whose `"feed"` field reads
  exactly `"yahoo"` and a non-empty `"bars"` array, **or** HTTP 409 ("already registered") — either
  means the data now exists and is ready to view. It must NOT be 422/503/504.
- Step 6: within a few seconds, a "Price chart — S/R levels" panel appears with a rendered
  candlestick chart showing multiple visible candles (not a blank canvas)
- The caption directly beneath the chart reads **"Candles: 1h series (N of M recorded bars, as of
  the query time). Level lines span every recorded timeframe."** — the word "1h" naming the
  timeframe is the key assertion: before this iteration only "1d" could ever appear here
- A "Confluence zones" panel appears below (either populated zone cards badged "Class A/B/C", or the
  honest message "No qualifying confluence zone among these levels.") — never a crash
- **Notes on environment variability (not defects if seen):**
  - If the message "No levels found for AAPL as of 2026-07-02T00:00:00Z." appears instead, the fetch
    itself still succeeded (the curl step already confirmed that) but this particular window
    produced no qualifying swing levels. Retry with a wider `start` (e.g. three weeks back) and
    repeat from step 4.
  - If the caption names a shorter timeframe than "1h" (e.g. "5m" or "1m"), AAPL already has an
    even-shorter series registered in this environment from earlier testing, and the page's
    pre-existing "shortest timeframe wins" picker is correctly preferring it. Substitute a symbol
    confirmed to have no existing series (check via the same `curl ... | grep` pattern as step 1)
    and repeat.
- No amber "could not be loaded" panel; no errors in the browser console

---

### UT-06 — A freshly-derived Yahoo `4h` series renders on Structure, honestly labelled `4h` (happy path — the era's single named new backend computation)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Backend running at http://localhost:8301; a terminal available
- A live manual test of exactly this MSFT/`4h` combination is already recorded as working in this
  codebase's dev handoff (`docs/handoffs/goal-yahoo_fetch-iter-2-dev.md`: HTTP 200, `feed="yahoo"`,
  `bar_count=20`, real candles) — this test reproduces that same check through the browser

**Steps:**
1. Run: `curl -s -X POST http://localhost:8301/research/bars -H "Content-Type: application/json" -d
   '{"symbol":"MSFT","timeframe":"4h","start":"2026-06-25T00:00:00Z","end":"2026-07-02T00:00:00Z"}'`
2. Confirm the response is HTTP 200 (or 409 if this exact window is already registered) with a
   `bar_series` object whose `"timeframe"` field reads exactly `"4h"` — never a 422 "not served by
   Yahoo Finance" error (`4h` IS supported this era; it is simply not a native Yahoo interval, so the
   backend builds it from real `1h` bars)
3. Navigate to `http://localhost:3301/structure`
4. Type `MSFT` into the "Symbol" field
5. Type `2026-07-02T00:00:00Z` into the "As-of (UTC, ISO-8601)" field
6. Click the "Load" button

**Expected Result:**
- Step 2: HTTP 200 (or 409), `"timeframe":"4h"` in the response — confirms the backend accepted and
  resampled the request rather than rejecting it
- Step 6: the "Price chart — S/R levels" panel renders a candlestick chart
- The caption beneath the chart reads **"Candles: 4h series (...)"** — the word "4h" must appear,
  proving this derived-from-`1h` series is honestly labelled with its own timeframe string, never
  silently shown as "1h" or "1d"
- The candles are visibly wider/fewer over the same calendar window than UT-05's `1h` chart (each
  candle spans 4 real trading hours instead of 1)
- **Notes on environment variability (not defects if seen):**
  - If the caption instead names a shorter timeframe (e.g. "1h"), MSFT already has a
    shorter-timeframe series registered in this environment from earlier testing, and the
    "shortest timeframe wins" picker is correctly preferring it — not a bug. Substitute a symbol
    confirmed to have no existing series and repeat.
  - If "No levels found for MSFT as of ..." appears instead of a chart, retry with a wider `start`
    date, same as UT-05's equivalent note.
- No error panel; no crash

---

### UT-07 — Cockpit's feed badge still reads exactly "Simulated" after a Simulated watch, never "yahoo" (regression — J-06 crux check)

**Type:** regression
**Priority:** P1
**Surface:** `/`

**Preconditions:**
- Frontend and backend running; no watch currently active

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Confirm the "Simulated" button in the Live / Historical / Simulated toggle is highlighted (click
   it if it is not)
3. Type `SIM-BUYER` into the ticker field (placeholder "Ticker e.g. SIM-BUYER")
4. Click the "Watch" button
5. Wait up to 10 seconds for the full cockpit panel grid to appear
6. Look at the small badge reading "feed" next to the "Watching SIM-BUYER" indicator near the top of
   the page

**Expected Result:**
- Step 5: the page settles into the full cockpit grid — "Watching" plus "SIM-BUYER", a "Stop"
  button, and panels for Tape State, Quote, Recent Trades, Features, Observations, and Event Log
- Step 6: the feed badge's value reads **exactly "Simulated"** — it must not read "yahoo", "sip", or
  be blank. This is the key regression assertion: it proves this iteration's Yahoo-vendor bar-fetch
  change (confined to `POST /research/bars`, via `get_bar_fetch_adapter()`) did not leak into the
  separate live/simulated tape-watching code path (`get_adapter()`, never touched this iteration)
- No red error banner; no errors in the browser console

---

### UT-08 — Journal, Studies, and Performance pages still load without errors (regression — J-06)

**Type:** regression
**Priority:** P1
**Surface:** `/journal`, `/studies`, `/performance`

**Preconditions:**
- Frontend and backend running

**Steps:**
1. Navigate to `http://localhost:3301/journal`; wait for the page to load
2. Navigate to `http://localhost:3301/studies`; wait for the page to load
3. Navigate to `http://localhost:3301/performance`; wait for the page to load

**Expected Result:**
- Step 1: the heading "Journal" is visible; a three-tab view toggle is visible ("Theses" active by
  default); below it, either a populated table or an honest empty-state message is shown — never a
  blank area
- Step 2: the heading "Replay studies" is visible; a study-creation form is visible on the left with
  a "Run study" button; the right panel shows either a selected study's results or the placeholder
  text "Create a study, or select one from the list, to read its results."
- Step 3: the heading "Performance" is visible; a "PnL ledger" section and a "Champion" section
  (with "strategy"/"profile" values) are both visible
- None of the three pages shows a red error banner or a blank white screen; no console errors on any
  of them

---

### UT-09 — No "yahoo" text leaks onto any surface outside the fetched-data caption (ux)

**Type:** ux
**Priority:** P1
**Surface:** `/`, `/journal`, `/studies`, `/performance`, `/structure`

**Preconditions:**
- Complete UT-05 first, so at least one Yahoo-fetched series exists to load on `/structure`
- A Simulated watch is active from UT-07 (or start a fresh one)

**Steps:**
1. On the Cockpit page (from UT-07), visually scan for the text "yahoo" (any case) anywhere on
   screen
2. Navigate to `http://localhost:3301/journal` and scan the whole page for "yahoo"
3. Navigate to `http://localhost:3301/studies` and scan the whole page for "yahoo"
4. Navigate to `http://localhost:3301/performance` and scan the whole page for "yahoo"
5. Navigate to `http://localhost:3301/structure`, reload the AAPL `1h` data from UT-05, and scan the
   entire page — chart, caption, Registry, and Comparison sections — for "yahoo"

**Expected Result:**
- The word "Yahoo"/"yahoo" appears on **none** of the 5 surfaces — not in a badge, table cell,
  tooltip, or caption. The Structure chart caption names only the timeframe ("1h series"), never the
  vendor
- This absence is correct, not a gap: the "Yahoo Finance" provenance badge and
  `taxonomy.FEED_BASIS_LABELS` entry are intentionally deferred to a later iteration (J-05). Its
  premature appearance here would mean the raw `feed` value leaked into a surface this iteration was
  not scoped to touch — worth failing this test over if seen

---

### UT-10 — No fetch-trigger control exists anywhere in the UI yet (ux — confirms the J-05 deferral is intentional, not a missing/broken feature)

**Type:** ux
**Priority:** P3
**Surface:** `/structure`, `/`

**Preconditions:**
- Frontend and backend running

**Steps:**
1. Navigate to `http://localhost:3301/structure` and look for any button, link, or field labelled
   "Fetch", "Yahoo", or "Import" anywhere on the page
2. Navigate to `http://localhost:3301/` and repeat the same visual scan

**Expected Result:**
- No such control exists anywhere in the UI on either page — the only way to fetch new Yahoo bar
  data today is the direct API call used in UT-05/UT-06, never a UI click
- This is the expected, already-documented state for this iteration (the fetch-trigger button ships
  in a future iteration, J-05) — its absence here is not a defect to report

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Structure loads | smoke | P1 | `/structure` |
| UT-02 | Cockpit loads, Simulated default | smoke | P1 | `/` |
| UT-03 | Load button validation | validation | P2 | `/structure` |
| UT-04 | Honest "no bar series" state | error | P2 | `/structure` |
| UT-05 | `1h` series renders (new capability + J-01) | happy-path | P1 | `/structure` |
| UT-06 | `4h` derived series renders, honestly labelled | happy-path | P1 | `/structure` |
| UT-07 | Feed badge stays "Simulated" (J-06 crux) | regression | P1 | `/` |
| UT-08 | Journal/Studies/Performance unbroken | regression | P1 | `/journal`, `/studies`, `/performance` |
| UT-09 | No "yahoo" text leakage | ux | P1 | all 5 surfaces |
| UT-10 | No fetch-trigger UI yet (expected) | ux | P3 | `/structure`, `/` |

**P1 tests must all pass for browser QA verdict to be PASS.** 7 of 10 tests are P1 this iteration:
2 smoke, 2 happy-path (both reachable only via a one-line curl precondition, since the fetch-trigger
UI itself is deferred to J-05), and 3 regression/leakage checks matching the phase's explicit
"Required-still-passing: J-01, J-06" gate — the leakage scan (UT-09) is elevated from the generic
UX-informational default to P1 for the same reason iter-1's analogous check (UT-13) was: a premature
"yahoo" string anywhere is a genuine single-source-of-truth/anti-goal violation, not a cosmetic
nit. UT-03/UT-04 (pre-existing, unchanged validation/honest-state logic) and UT-10 (an expected,
documented absence) stay lower priority because they exercise code this iteration did not touch.
