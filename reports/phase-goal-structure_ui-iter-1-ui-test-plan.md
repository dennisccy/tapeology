# Phase goal-structure_ui-iter-1 — UI Test Plan

**Phase:** goal-structure_ui-iter-1
**Date:** 2026-07-07
**Written by:** ui-test-designer
**Frontend URL:** http://localhost:3301
**Backend URL:** http://localhost:8301 (this environment's paired backend — the deterministic offset pairs frontend `3000+301` with backend `8000+301`; adjust both if your environment uses a different offset)

---

## Conventions

- This iteration ships exactly ONE new route, `/structure`, plus one new top-bar nav link. Nothing else in the app changed.
- The Structure page holds NO state across a reload — it always starts at the idle placeholder. There are no query-string parameters to deep-link a symbol/as-of; every test starts from a fresh navigation or a click on the nav link.
- **This environment appears to run without market-data vendor credentials configured** (`GET /symbols/search` returns `[]` with no credentials — confirmed in `apps/backend/app/main.py`'s `symbols_search` handler). That is expected and is itself the exact condition `no_bar_series_for_symbol` tests for (UT-08). It does not block anything below: every "Symbol" field in this app accepts free-text entry whether or not a suggestions dropdown appears.
- These are browser (UI) tests. They intentionally do NOT re-run the curl/API checks already covered in `reports/qa/goal-structure_ui-iter-1-test-plan.md` (TC-01 route registry, TC-09 service startup, TC-11 config fingerprint). Where a test below needs to confirm an on-screen value against the API (the phase's "no second source of truth" requirement), the exact expected values are given directly (already live-verified per the dev handoff) so no separate curl step is required.
- Every screenshot referenced below should be saved to `reports/qa/goal-structure_ui-iter-1-evidence/` using the suggested filename — the phase spec's Definition of Done treats an unphotographed "it rendered" claim as `unknown`, not `passing`.

### Data-testid quick reference (from `apps/frontend/app/structure/page.tsx` and `StructureChart.tsx`)

| `data-testid` | What it marks |
|---|---|
| `structure-title` | The `<h1>Structure</h1>` heading |
| `structure-framing` | The "Read-only: every level..." disclosure line |
| `structure-as-of-input` | The as-of text field |
| `structure-load-button` | The `Load` button |
| `structure-idle` | Idle placeholder (before first Load) |
| `structure-loading` | Loading pulse-skeleton (levels fetch in flight) |
| `structure-degraded` | Degraded/error panel (network failure or non-200, incl. malformed `as_of`) |
| `structure-no-bar-series` | Honest state: `no_bar_series_for_symbol: true` |
| `structure-no-levels` | Honest state: series exists, `levels: []` |
| `structure-no-zones` | Honest state (zones panel only): `confluence_zones: []` |
| `structure-chart-canvas` | The chart's container div |
| `structure-chart-loading` / `structure-chart-unavailable` | Chart-panel-local loading/error (the `/research/bars` fetch, independent of the levels fetch) |
| `zone-row` (+ `data-zone-class="A"\|"B"\|"C"`) | One confluence-zone card |
| `zone-class-badge` | The "Class X" badge inside a zone card |
| `zone-score` | The numeric score inside a zone card |
| `zone-member-level` | One member-level row inside a zone's nested table |
| `app-nav` / `nav-link` (+ `data-label`) / `nav-unavailable` | The shared top-bar (pre-existing, unchanged this iteration) |

---

## Test Data Setup

Five of the tests below (UT-06, UT-07, UT-09, UT-10, and the "before/after" half of UT-08) need the **committed PG bar-series fixture** seeded into the live backend. This is the same fixture pair the backend's own `test_levels.py` and the dev handoff's live verification used — the resulting level/zone values are deterministic and already confirmed below.

**Fixture files:** `apps/backend/tests/fixtures/bars/009371c9c02f46338bafef47148f92ad.json` (symbol `PG`, timeframe `1h`, window `2026-06-09T13:00:00Z`–`2026-06-09T21:00:00Z`, 9 bars) and `apps/backend/tests/fixtures/bars/b08b1a55ef4a45b2a1adad8fa82ccdf1.json` (symbol `PG`, timeframe `1d`, window `2026-06-01T00:00:00Z`–`2026-06-06T00:00:00Z`, 5 bars).

**To seed (pick one):**
- (a) Start/restart the backend with the environment variable `TAPEOLOGY_BAR_DIR=apps/backend/tests/fixtures/bars` so it reads the fixtures directly (cleanest — no copying, no cleanup needed), **or**
- (b) Copy both files into the backend's live bar directory (default `apps/backend/.data/bars/`) while it is running, then delete them when finished with the fixture-dependent tests below (seed → verify → remove; never leave test data behind).

**Golden values at `symbol=PG`, `as_of=2026-06-09T21:00:00Z`** (live-verified in the dev handoff, `docs/handoffs/goal-structure_ui-iter-1-dev.md`): `no_bar_series_for_symbol: false`, **20 levels**, **6 confluence zones (5 badged Class C, 1 badged Class B, 0 badged Class A** — a 2-timeframe fixture cannot reach Class A, which is expected, not a gap**)**. The representative chart series is always the `1h` one (9 of 9 recorded bars are `<= as_of`, since `as_of` equals the 1h window's own end instant).

**Sequencing:** run UT-08 (`no_bar_series_for_symbol`) either *before* seeding anything, or *after* removing the fixture files — never while the fixture is seeded, since seeding is exactly what flips that state to false.

---

## Test Cases

<!-- Test IDs use UT-XX prefix to distinguish from functional test plan TC-XX IDs. -->

---

### UT-01 — Structure page loads with header, framing copy, and both controls (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running at http://localhost:3301, backend reachable
- No fixture needs to be seeded for this test

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Wait for the page to fully load

**Expected Result:**
- Page returns HTTP 200 (not a 404 or blank screen)
- A heading reading exactly "Structure" is visible (`data-testid="structure-title"`)
- Directly below it, a subtitle reads "Deterministic support/resistance levels and A/B/C confluence zones for a chosen symbol and as-of time."
- Below that, a smaller disclosure line reads "Read-only: every level, zone class, and score below is read verbatim from GET /research/levels — nothing here is recomputed in the browser." (`data-testid="structure-framing"`)
- A control row is visible with a "Symbol" labeled field, an "As-of (UTC, ISO-8601)" labeled field (placeholder text `2026-06-09T21:00:00Z`), and a "Load" button
- No console errors

---

### UT-02 — Idle placeholder shown before first Load, and again after a refresh (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Frontend running; fresh navigation (no prior Load clicked this session)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Observe the area below the controls, before typing or clicking anything
3. Type `PG` into the Symbol field and `2026-06-09T21:00:00Z` into the As-of field (do NOT click Load yet)
4. Refresh the page (F5)
5. Observe the area below the controls again

**Expected Result:**
- Step 2: the message "Choose a symbol and an as-of time, then Load, to see its S/R levels and confluence zones." is visible (`data-testid="structure-idle"`), with no chart and no table present
- Step 5 (after refresh): both the Symbol and As-of fields are empty again, and the SAME idle message from step 2 reappears — the page does not remember the previous query (this is intended, not a bug)

---

### UT-03 — Load button is disabled until both Symbol and As-of are filled (validation)

**Type:** validation
**Priority:** P2
**Surface:** `/structure` controls

**Preconditions:**
- Fresh navigation to `/structure`

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Observe the "Load" button's appearance (both fields empty)
3. Type `PG` into the Symbol field only; observe the Load button
4. Clear the Symbol field; type `2026-06-09T21:00:00Z` into the As-of field only; observe the Load button
5. Type `PG` into the Symbol field as well (both fields now filled); observe the Load button
6. Click "Load"

**Expected Result:**
- Steps 2–4: the "Load" button is visibly greyed out/dimmed and does not respond to clicks (`disabled`, ~40% opacity)
- Step 5: the "Load" button becomes fully opaque/enabled the instant BOTH fields are non-empty
- Step 6: clicking now triggers a fetch (the idle message is replaced by a loading or result state) — the form did not silently no-op

---

### UT-04 — Structure nav link is reachable from every page and is proven data-driven (ux)

**Type:** ux
**Priority:** P1 *(elevated from the default ux priority — this is an explicit Definition-of-Done bullet: "Browser QA confirms the Structure nav link is served by GET /meta/ui-routes, not a hardcoded client link.")*
**Surface:** shared top-bar `NavBar` (all pages)

**Preconditions:**
- Frontend and backend both running

**Steps:**
1. Navigate to `http://localhost:3301/` (Cockpit)
2. Read the top-bar nav links, left to right
3. Open browser dev tools → Network tab, then reload the page and find the request to `/meta/ui-routes`
4. Inspect that response's JSON body
5. Click the "Structure" link in the top bar
6. Repeat steps 1–2 from `/journal`, `/studies`, and `/performance` instead of `/`

**Expected Result:**
- Step 2: the top bar reads, in order: `Cockpit`, `Journal`, `Studies`, `Performance`, `Structure` — five links total, with `Structure` last (immediately after `Performance`)
- Step 4: the response body's `routes` array's LAST entry is exactly `{"path": "/structure", "label": "Structure", "nav": true}`, and it is the ONLY new entry (the five entries before it are byte-identical to their pre-iteration values)
- Step 5: the browser navigates to `http://localhost:3301/structure` with HTTP 200
- Step 6: the exact same 5-link nav (with Structure present) renders from every other existing page — it is not specific to the home page
- (For an engineer confirming "not hardcoded," not required for a non-technical operator): searching the frontend source for a literal `href="/structure"` or `Link href="/structure"` string finds none outside `NavBar.tsx`'s generic `route.path` template — the link exists purely because the backend's list grew by one entry
- Screenshot: save a capture of the top bar (from any page) showing the 5-link nav with "Structure" visible to `reports/qa/goal-structure_ui-iter-1-evidence/UT-04-nav-structure-link.png`

---

### UT-05 — Loading placeholder appears while the fetch is in flight (smoke)

**Type:** smoke
**Priority:** P1
**Surface:** `/structure`

**Preconditions:**
- Fresh navigation to `/structure`; backend running (a slight delay helps this test — e.g. backend under normal load — since a very fast local response can make this state hard to catch by eye)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `PG` into Symbol and `2026-06-09T21:00:00Z` into As-of
3. Click "Load" and immediately look at the result area (within the first fraction of a second)

**Expected Result:**
- Immediately after clicking, a pulse-animated grey skeleton placeholder appears (`data-testid="structure-loading"`) — three horizontally-pulsing bars, no fabricated numbers or chart shown while waiting
- This state is transient and is replaced by a real result within a couple of seconds; if the local network is too fast to catch it by eye, that is acceptable (not a failure) as long as no error or blank flash occurs in its place

---

### UT-06 — Populated state: chart renders candles plus all 20 dashed S/R level lines (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` — price chart panel

**Preconditions:**
- **PG fixture seeded** (see Test Data Setup above)
- Fresh navigation to `/structure`

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `PG` into the Symbol field
3. Type `2026-06-09T21:00:00Z` into the As-of field
4. Click "Load"
5. **Wait at least 1–2 seconds after the page updates before inspecting the chart** — the chart's `lightweight-charts` import and draw are asynchronous and can lag slightly behind the rest of the page (a documented timing quirk from the dev handoff, not a defect); an instant screenshot can show a blank canvas even when the chart is about to render correctly
6. Inspect the "Price chart — S/R levels" panel

**Expected Result:**
- A panel titled "Price chart — S/R levels" is visible, containing a dark candlestick chart (green/rose candles on a near-black background)
- The chart shows **9 candles** (the fixture's full 1h series)
- **20 dashed horizontal reference lines** are drawn across the chart (one per S/R level) — some may fall outside the visible candle range since a level can come from a longer timeframe (1d) than the charted series (1h); that is expected, not a bug
- Hovering/inspecting a line shows a label combining timeframe + type (e.g. a "1h" or "1d" line labelled with a type such as "swing-pivot" or "prior-period-extreme") plus a price value on the right-hand axis
- Directly below the chart, a caption reads: "Candles: 1h series (9 of 9 recorded bars, as of the query time). Level lines span every recorded timeframe."
- No "no bar series" / "no levels" / degraded message is shown — this is the fully populated state
- Screenshot: save to `reports/qa/goal-structure_ui-iter-1-evidence/UT-06-populated-chart.png` (this same screenshot, if it also frames the zones table below, satisfies UT-07's screenshot too)

---

### UT-07 — Populated state: confluence-zones table shows 6 zone cards with byte-for-byte values (happy path)

**Type:** happy-path
**Priority:** P1
**Surface:** `/structure` — confluence-zones table

**Preconditions:**
- Same as UT-06 (PG fixture seeded, symbol `PG`, as-of `2026-06-09T21:00:00Z`, Load already clicked)

**Steps:**
1. With the populated state from UT-06 on screen, scroll to the "Confluence zones" panel below the chart
2. Count the zone cards
3. Read each card's "Class X" badge
4. Locate the card whose "zone N · score" line reads "score 12" — expand/read its member-levels table
5. Compare that card's member rows against the known values below

**Expected Result:**
- Exactly **6 zone cards** are rendered (`data-testid="zone-row"`, one `<article>` per card)
- Exactly **5 cards** show the badge "Class C" and exactly **1 card** shows the badge "Class B" — none show "Class A" (expected on this 2-timeframe fixture, not a gap)
- The card with "score 12" has a nested table (headers "price" / "timeframe" / "type", lowercase) with exactly these 3 member rows, matching `GET /research/levels` byte-for-byte:
  - `139.89` / `1d` / `prior-period-extreme`
  - `139.89` / `1d` / `swing-pivot`
  - `140` / `1d` / `prior-period-extreme` (note: displayed as `140`, not `140.00` — the page never reformats a served number)
- No zone card shows a fabricated or rounded value that isn't one of the raw numbers above
- Screenshot: save to `reports/qa/goal-structure_ui-iter-1-evidence/UT-07-populated-zones-table.png` (or reuse UT-06's screenshot if it already frames both panels)

---

### UT-08 — Honest state: no_bar_series_for_symbol shows the distinct credentials-needed message (error)

**Type:** error
**Priority:** P1 *(Definition-of-Done acceptance state (c))*
**Surface:** `/structure`

**Preconditions:**
- **PG fixture NOT currently seeded** (run this either before seeding, or after removing it — see Test Data Setup's sequencing note)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `PG` into the Symbol field
3. Type `2026-06-09T21:00:00Z` into the As-of field
4. Click "Load"

**Expected Result:**
- The message "No bar series recorded for PG." is shown as the title, with "Recording historical bars needs provider credentials." as a second line (`data-testid="structure-no-bar-series"`)
- No chart, no zones table, and no other message is shown
- This wording is visibly different from every other empty/error state below (never the same copy reused)
- Screenshot: save to `reports/qa/goal-structure_ui-iter-1-evidence/UT-08-no-bar-series.png`

---

### UT-09 — Honest state: series-but-no-levels shows the distinct "no levels found" message (error)

**Type:** error
**Priority:** P1 *(Definition-of-Done acceptance state (d))*
**Surface:** `/structure`

**Preconditions:**
- **PG fixture seeded** (see Test Data Setup)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `PG` into the Symbol field
3. Type `2026-05-01T00:00:00Z` into the As-of field (before either recorded window opens)
4. Click "Load"

**Expected Result:**
- The message "No levels found for PG as of 2026-05-01T00:00:00Z." is shown as the title, with "A bar series is recorded, but nothing is derivable at this as-of time." as a second line (`data-testid="structure-no-levels"`)
- No chart, no zones table
- Wording is distinct from UT-08's message (different copy, not a reused "nothing here" string)
- Screenshot: save to `reports/qa/goal-structure_ui-iter-1-evidence/UT-09-no-levels.png`

---

### UT-10 — Honest state: levels-but-no-zones shows the distinct message while the chart still renders (error)

**Type:** error
**Priority:** P1 *(Definition-of-Done acceptance state (e))*
**Surface:** `/structure`

**Preconditions:**
- **PG fixture seeded** (see Test Data Setup)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `PG` into the Symbol field
3. Type `2026-06-02T12:00:00Z` into the As-of field
4. Click "Load"
5. Inspect the "Price chart — S/R levels" panel AND the "Confluence zones" panel separately

**Expected Result:**
- The "Price chart — S/R levels" panel IS still shown (not replaced by an empty-state message) with **3 dashed level lines** at prices 138.86, 140.28, and 141.82
- Note: at this as-of, none of the fixture's 1h candles predate the query time (the 1h window starts 2026-06-09, after this as-of), so the chart's caption may read "Candles: 1h series (0 of 9 recorded bars...)" and a small "No recorded candle series available to draw for this symbol" hint may overlay the (candle-less) chart area — this is an honest, expected combination (real level lines drawn, real disclosure that no candles apply yet), not a defect
- Below it, the "Confluence zones" panel (only) shows: "No qualifying confluence zone among these levels." with "Levels exist, but none cluster closely enough across timeframes to form a zone." as a second line (`data-testid="structure-no-zones"`)
- This is the only state where a message panel and real chart content appear together — confirm the message is scoped to the zones panel, not the whole page
- Screenshot: save to `reports/qa/goal-structure_ui-iter-1-evidence/UT-10-no-zones.png`

---

### UT-11 — Malformed as-of input renders the degraded panel, never a crash (error)

**Type:** error
**Priority:** P2
**Surface:** `/structure`

**Preconditions:**
- Fresh navigation to `/structure`; no fixture needed (the 422 happens before any bar lookup)

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Type `PG` into the Symbol field
3. Type `not-a-date` into the As-of field
4. Click "Load"

**Expected Result:**
- The amber-bordered degraded panel appears (`data-testid="structure-degraded"`) reading exactly "as_of must be an ISO date-time" (the backend's own validation message, shown verbatim, not a generic "something went wrong")
- A fixed second line reads "Nothing cached and nothing fabricated is shown in its place."
- No JavaScript crash, no blank page, no fabricated chart or table
- The page remains fully interactive (you can correct the As-of field and click Load again)

---

### UT-12 — Backend unreachable renders the degraded panel and the nav's own degraded state, never a blank page (error)

**Type:** error
**Priority:** P1 *(cross-cutting reliability guarantee spanning both the new page and the pre-existing NavBar pattern — an explicit Testing Requirement in the phase spec)*
**Surface:** `/structure` + shared `NavBar`

**Preconditions:**
- Frontend running; you are able to stop the backend process (the one at http://localhost:8301 in this environment) and restart it afterward
- On `/structure`, with `PG` / `2026-06-09T21:00:00Z` already typed into the fields (do not click Load yet)

**Steps:**
1. Stop the backend process
2. Refresh the browser page (F5) — this forces the top-bar nav to re-fetch its route list and fail
3. Observe the top bar
4. Re-type `PG` into Symbol and `2026-06-09T21:00:00Z` into As-of (the refresh cleared them), then click "Load"
5. Observe the result area
6. Restart the backend, then refresh the page once more to confirm recovery

**Expected Result:**
- Step 3: the top bar shows the brand name but no nav links — instead the text "navigation unavailable — backend unreachable" appears (`data-testid="nav-unavailable"`) — never a blank/crashed bar, never a fabricated link list
- Step 5: the amber degraded panel appears (`data-testid="structure-degraded"`) reading "Backend unreachable — is the API running?" with the same fixed "Nothing cached and nothing fabricated is shown in its place." second line
- No console-crashing error, no blank white page, at any point
- Step 6: after restarting the backend and refreshing, the normal 5-link nav returns and `/structure` behaves normally again (confirms this was a transient degraded state, not a permanently broken page)

---

### UT-13 — The four pre-existing top-bar pages remain reachable and unchanged (regression)

**Type:** regression
**Priority:** P1 *(J-04 is the phase's explicit "critical" required-still-passing regression sentinel)*
**Surface:** `/`, `/journal`, `/studies`, `/performance`

**Preconditions:**
- Frontend and backend running normally (fixture seeded or not — does not matter for this check)

**Steps:**
1. Navigate to `http://localhost:3301/` — confirm the Cockpit (ticker input + Watch button) loads
2. Navigate to `http://localhost:3301/journal` — confirm a heading reading "Journal" and a journal list/table load
3. Navigate to `http://localhost:3301/studies` — confirm a heading (`data-testid="studies-title"`, default text "Replay studies" unless configured otherwise) and the studies list load
4. Navigate to `http://localhost:3301/performance` — confirm a heading reading exactly "Performance" (`data-testid="performance-title"`) and its scorekeeping content load
5. On each of the 4 pages, confirm the top bar still shows all 5 links (`Cockpit`, `Journal`, `Studies`, `Performance`, `Structure`)

**Expected Result:**
- All four pages return HTTP 200 and render their pre-existing content with no visual change and no new console errors
- None of the four pages' own layout, tables, or forms show any trace of the Structure work (no stray levels/zones content bled into another page)
- The top bar on every one of them includes the new "Structure" link in the same 5th position

---

### UT-14 — Cockpit SIM-BUYER simulated-tape flow still works end to end (regression)

**Type:** regression
**Priority:** P1 *(explicitly named in the execution plan's J-04 regression scenario: "sim cockpit flows (SIM-BUYER/SIM-SELLER)")*
**Surface:** `/` (Cockpit)

**Preconditions:**
- Frontend and backend running; on `/`, the data-source selector already defaults to "Simulated"

**Steps:**
1. Navigate to `http://localhost:3301/`
2. Confirm the ticker input shows placeholder text "Ticker e.g. SIM-BUYER"
3. Type `SIM-BUYER` into that ticker input
4. Click the green "Watch" button
5. Wait up to ~10 seconds

**Expected Result:**
- Immediately after clicking Watch, a "Connecting to SIM-BUYER…" message appears
- Within ~10 seconds, the cockpit populates with a live simulated tape read (quote, recent trades, core features, tape state/confidence, observations, event log) — never a blank or stuck cockpit
- The tape state resolves to `buyer_control`
- This flow behaves identically to how it behaved before this iteration (nothing about the Structure work touches the cockpit's code path)

---

### UT-15 — Symbol field accepts free-text entry with no dependency on autocomplete matches (ux)

**Type:** ux
**Priority:** P3
**Surface:** `/structure` — Symbol field

**Preconditions:**
- Fresh navigation to `/structure`

**Steps:**
1. Navigate to `http://localhost:3301/structure`
2. Click into the Symbol field and type `PG` one character at a time
3. Whether or not a suggestions dropdown appears, do NOT click any suggestion — instead type the As-of value directly and click "Load"

**Expected Result:**
- Typing into the Symbol field is never blocked or altered by the (possible) absence of a suggestions dropdown
- If a dropdown DOES appear, it lists symbol + name pairs and closes without error if you click elsewhere or ignore it
- If NO dropdown appears (e.g. no market-data credentials configured in this environment), typing and submitting the free-typed value still works exactly the same as if a suggestion had been picked — this is the deliberate, documented design (`SymbolSearch`'s own free-text fallback), not a defect
- Clicking "Load" proceeds normally regardless of which path was taken

---

## Test Summary

| ID | Name | Type | Priority | Surface |
|----|------|------|----------|---------|
| UT-01 | Page loads with header/framing/controls | smoke | P1 | `/structure` |
| UT-02 | Idle state before Load + after refresh | smoke | P1 | `/structure` |
| UT-03 | Load button disabled until both fields filled | validation | P2 | `/structure` controls |
| UT-04 | Nav link reachable + data-driven | ux | P1 | `NavBar` (all pages) |
| UT-05 | Loading placeholder while fetch in flight | smoke | P1 | `/structure` |
| UT-06 | Populated: chart + 20 dashed level lines | happy-path | P1 | `/structure` chart panel |
| UT-07 | Populated: 6 zone cards, byte-for-byte values | happy-path | P1 | `/structure` zones table |
| UT-08 | Honest state: no bar series recorded | error | P1 | `/structure` |
| UT-09 | Honest state: series but no levels | error | P1 | `/structure` |
| UT-10 | Honest state: levels but no zones (chart stays) | error | P1 | `/structure` |
| UT-11 | Malformed as-of → degraded panel | error | P2 | `/structure` |
| UT-12 | Backend unreachable → degraded panel + nav | error | P1 | `/structure` + `NavBar` |
| UT-13 | Four pre-existing pages unchanged | regression | P1 | `/`, `/journal`, `/studies`, `/performance` |
| UT-14 | Cockpit SIM-BUYER flow still works | regression | P1 | `/` (Cockpit) |
| UT-15 | Symbol field free-text entry works standalone | ux | P3 | `/structure` Symbol field |

**P1 tests (UT-01, 02, 04, 05, 06, 07, 08, 09, 10, 12, 13, 14) must all pass for the browser QA verdict to be PASS.** UT-03 and UT-11 (P2) and UT-15 (P3) are important but non-blocking.
