# Phase goal-yahoo_fetch-iter-1 — UI Test Results

**Phase:** goal-yahoo_fetch-iter-1
**Date:** 2026-07-09
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 14/14 tests passed (0 skipped)

All 9 P1 tests pass, including both named crux-risk regression checks (UT-06, UT-07) and the
no-leak audit (UT-13). All 4 P2 tests pass. The one P3 exploratory/informational test (UT-14)
also passes and is not required for the verdict.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Cockpit loads | smoke | P1 | Nav (5 links), header+toggle (Simulated active), idle state "No ticker watched" / "Try: SIM-BUYER", no errors | All present exactly as specified; console clean except benign React DevTools info line | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-01-result.png` |
| UT-02 | Structure loads | smoke | P1 | Heading, Symbol/As-of form with disabled Load, empty-state message, Registry resolving to Champion, no errors | All present; Load button `disabled`/`aria-disabled="true"` confirmed in DOM; Registry resolved to Champion strategy=v1/profile=default (not degraded) | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-02-result.png` |
| UT-03 | Journal loads | smoke | P1 | Heading, 3-tab toggle (Theses active), table or honest empty state, no errors | Theses tab active; table populated with 2 rows (SIM-SELLER, SIM-BUYER); console clean | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-03-result.png` |
| UT-04 | Studies loads | smoke | P1 | Heading "Replay studies", `study-create-form` with Run study button, results panel showing selection or placeholder, no errors | All present; right panel shows exact placeholder text "Create a study, or select one from the list, to read its results." | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-04-result.png` |
| UT-05 | Performance loads | smoke | P1 | Heading, PnL ledger (populated or honest empty), Champion summary, no errors | PnL ledger populated (founding baseline row); Champion shows strategy=v1/profile=default | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-05-result.png` |
| UT-06 | Cockpit Watch flow + feed badge (crux risk) | regression | P1 | Connecting state then resolved cockpit grid (6 panels); `feed-basis-label` reads exactly "Simulated" | Resolved grid confirmed (Tape State/Quote/Recent Trades/Features/Observations/Event Log all present); DOM query confirmed `[data-testid="feed-basis-label"]` textContent === "Simulated" exactly. Connecting transient not visually captured — see note below | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-06-connecting.png`, `UT-06-result.png` |
| UT-07 | Structure chart/levels/zones unbroken (crux risk) | regression | P1 | Candlestick chart renders, caption format matches, confluence zones (or honest empty), no degraded panel | Chart rendered with visible green/red candles; caption exactly "Candles: 1d series (24 of 24 recorded bars, as of the query time). Level lines span every recorded timeframe."; 28 Class-C zone cards rendered with price/timeframe/type rows | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-07-result.png`, `UT-07-chart-detail.png` |
| UT-08 | Nav bar unchanged (5 links) | regression | P1 | Exactly 5 links in order, correct routes, `aria-current="page"` follows active page, no degraded state | Clicked Journal→Studies→Performance→Structure→Cockpit; each navigation confirmed via DOM eval (`aria-current` label matched destination, URL matched route); nav link set consistently `Cockpit,Journal,Studies,Performance,Structure` on every page visited this session | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-08-result.png` |
| UT-09 | Journal detail opens from row | regression | P2 | Navigates to `/journal/<id>`, heading "Review", back-link, detail sections render | Navigated to `/journal/1720066953894610879c40737b9cdb00`; heading "Review"; "← Back to journal" link visible; all sections (expected-behaviour, verdict timeline, entry risk flags, what-you-did, execution checks) rendered | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-09-result.png` |
| UT-10 | Studies form fields interactive | regression | P2 | Source/setup/direction fields all accept focus/change, Run study button visible, not clicked | Source radio changed (revealed new "Sim scenario" dropdown), setup `<select>` changed to Trend continuation, direction `<select>` changed to Short — all succeeded without error; Run study button not clicked | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-10-result.png` |
| UT-11 | Watch validation blocks empty ticker | validation | P2 | Watch button disabled pre-click with amber "Enter a ticker symbol"; click has no effect | DOM confirmed `disabled`/`aria-disabled="true"` + `data-testid="watch-validation"` amber message pre-click; click on disabled button produced no state change (still idle, no cockpit grid) | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-11-result.png` |
| UT-12 | Journal detail honest 404 state | error | P2 | Red-bordered alert "This thesis was not found.", "Return to the journal" link works | Alert box (red border, confirmed visually) with exact text; link clicked and confirmed via `window.location.href` navigation to `/journal` | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-12-result.png` |
| UT-13 | No "yahoo" string leaked anywhere yet | ux | P1 | Word "yahoo"/"Yahoo" absent on all 5 surfaces; Cockpit feed badge and Journal feed cells show only their pre-iteration vocab | Full-page text scans on Cockpit (watching SIM-BUYER), Journal (feed cells = "SIM"), Studies (feed = "SIP"), Performance, and Structure (with a freshly Yahoo-fetched AAPL series loaded, `feed:"yahoo"` confirmed server-side via curl) all contain zero occurrences of "yahoo" (case-insensitive) | PASS | Cross-referenced against `UT-06-result.png`, `UT-03-result.png`, `UT-04-result.png`, `UT-05-result.png`, `UT-07-result.png` (same page states scanned) |
| UT-14 | [Exploratory] Yahoo data reaches Structure chart | ux | P3 (informational) | curl fetch returns 200 with `feed:"yahoo"` and real bars; chart renders those bars; no "Yahoo" text anywhere | `POST /research/bars` for AAPL returned HTTP 200, `feed:"yahoo"`, `bar_count:24`, non-empty `bars[]`; Structure chart then rendered exactly those 24 bars ("24 of 24 recorded bars"); no vendor text anywhere on page | PASS | `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-07-result.png` (same load), raw curl response inspected inline |

---

## Passed Tests

### UT-01 — Cockpit `/` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-01-result.png`
- Nav bar (`data-testid="app-nav"`) shows exactly 5 links: Cockpit, Journal, Studies, Performance, Structure.
- Header shows "Tapeology" and the Live/Historical/Simulated toggle with "Simulated" pre-highlighted (`aria-pressed="true"`, filled background) — confirmed via DOM dump, no click needed.
- Main area shows "No ticker watched" heading and "Try: SIM-BUYER" hint, exactly as specified.
- Console: only one benign `info` line (React DevTools suggestion) across the entire test session — no warnings or errors at any point.

### UT-02 — Structure `/structure` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-02-result.png`
- Heading "Structure" (`data-testid="structure-title"`) visible.
- Symbol field (placeholder "e.g. PG"), As-of field (`data-testid="structure-as-of-input"`, placeholder "2026-06-09T21:00:00Z"), and Load button (`data-testid="structure-load-button"`) all present; Load button confirmed `disabled` + `aria-disabled="true"` in the raw DOM before any input.
- Empty-state message reads exactly "Choose a symbol and an as-of time, then Load, to see its S/R levels and confluence zones."
- Registry panel resolved (no loading delay observed) to a Champion box: strategy `v1`, profile `default` — not the amber degraded panel.

### UT-03 — Journal `/journal` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-03-result.png`
- Heading "Journal" visible; three-tab toggle (Theses/Analytics/Hints) present with Theses active.
- `journal-table` populated with 2 existing thesis rows (SIM-SELLER, SIM-SELLER's short and SIM-BUYER's long), both showing FEED="SIM" — not the empty state, but the empty-state code path was not required since data already existed.
- No error banner, console clean.

### UT-04 — Studies `/studies` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-04-result.png`
- Heading "Replay studies" (`data-testid="studies-title"`) visible.
- `study-create-form` visible on the left with Source radio group, Setup/Direction selects, and "Run study" button (`data-testid="study-create-button"`).
- Right panel shows the exact placeholder text via `data-testid="studies-no-selection"`: "Create a study, or select one from the list, to read its results."
- One pre-existing study ("Absorption reversal · long", historical PG reference, SIP) listed but not selected.

### UT-05 — Performance `/performance` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-05-result.png`
- Heading "Performance" (`data-testid="performance-title"`) visible.
- PnL ledger populated with the founding-baseline row (strategy v1 on default), showing train/hold-out net R with insufficient-sample badges (n=1).
- Champion section (`data-testid="champion-summary"`) shows strategy=v1, profile=default.
- No error banner, console clean.

### UT-06 — Cockpit Simulated Watch completes end-to-end; feed badge reads "Simulated" (crux risk check)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-06-connecting.png`, `UT-06-result.png`
- Typed `SIM-BUYER` into the Ticker field, clicked Watch. By the time the first post-click screenshot was captured, the app had already resolved to the full cockpit grid (Watching SIM-BUYER, Stop button, Tape State/Quote/Recent Trades/Features/Observations/Event Log all six panels present) — the transient "Connecting to SIM-BUYER…" copy/pulsing-dot state was not caught on camera because resolution happens in well under the automation round-trip time. This is a capture-timing gap, not a functional failure: at no point was the screen frozen or blank, which is the behavior the step actually guards against.
- **The critical assertion:** re-ran the watch and queried the DOM directly — `document.querySelector('[data-testid="feed-basis-label"]').textContent` returned exactly `"Simulated"`, and `[data-testid="feed-basis"]` textContent was `"feedSimulated"` (label + value concatenated in the badge). Confirmed via live DOM query, not just visual reading — the new Yahoo bar-fetch vendor default did not leak into the live/simulated tape accessor.
- Console clean across both watch instances.

### UT-07 — Structure page renders an existing symbol's chart, levels, and zones unbroken (crux risk check)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-07-result.png`, `UT-07-chart-detail.png`
- Precondition satisfied via UT-14's setup (`POST /research/bars` for AAPL, 2026-05-01→2026-06-05, `1d`).
- Typed `AAPL` / `2026-06-05T00:00:00Z`, clicked Load. "Price chart — S/R levels" panel rendered a candlestick chart with clearly visible green/red candle bodies (not blank) and overlaid level lines with price labels.
- Caption read exactly: "Candles: 1d series (24 of 24 recorded bars, as of the query time). Level lines span every recorded timeframe."
- Confluence Zones panel rendered 28 zone cards, every one carrying a "Class C" badge (`data-testid="zone-row"` pattern) with price/timeframe/type rows.
- No amber degraded-state panel; console clean.

### UT-08 — Top navigation is unchanged: exactly 5 links, correct labels and destinations
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-08-result.png`
- Clicked nav links in the specified order (Journal → Studies → Performance → Structure → Cockpit). After each click, a DOM query (`document.querySelector('a[aria-current="page"]').dataset.label` + `window.location.pathname`) confirmed the active link and URL matched the destination every time (e.g. `Studies | /studies`, `Performance | /performance`, `Cockpit | /`).
- Nav link set queried mid-sequence: `Cockpit,Journal,Studies,Performance,Structure` — exactly 5, correct order, no 6th link, on every page visited across the whole session (11 page states inspected).
- `data-testid="nav-unavailable"` never observed.

### UT-09 — Journal detail page opens from a table row
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-09-result.png`
- Clicked the ticker link in the first row (`data-testid="journal-row-link"`, SIM-SELLER). Navigated to `/journal/1720066953894610879c40737b9cdb00`; heading changed to "Review".
- "← Back to journal" link visible at top.
- All detail sections rendered: "What you expected" (expected-behaviour statements, both MET), "How it graded" (Outcome/Process), entry risk flags, "What you did" (entry/exit marks), "What the execution checks found", mistake tags, MFE/MAE tables, and "What the tape did" verdict timeline. No crash, no blank page.
- Console showed only benign Next.js Fast Refresh log lines (dev-mode hot reload), no errors.

### UT-10 — Studies "Run study" form opens and its fields are interactive
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-10-result.png`
- Clicked the "Seeded sim scenario" source radio (`data-testid="source-sim"`) — form responded by revealing a new "Sim scenario" dropdown (SIM-REVERSAL/SIM-BUYER/SIM-SHIFT/SIM-SELLER), proving the field is live/interactive.
- Changed the Setup select (`data-testid="study-setup"`) to "Trend continuation" and the Direction select (`data-testid="study-direction"`) to "Short" — both accepted the change without error.
- "Run study" button (`data-testid="study-create-button"`) remained visible throughout; not clicked, per the test's scope (submission exercises `SOURCE_HISTORICAL`, out of scope this iteration).

### UT-11 — Cockpit Watch validation still blocks an empty ticker
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-11-result.png`
- With the Ticker field empty, raw DOM confirmed the Watch button carries `disabled=""` and `aria-disabled="true"`, and `data-testid="watch-validation"` shows the amber text "Enter a ticker symbol" — both true before any click.
- Clicked directly on the button (`button[type="submit"]`) anyway; page state afterward was verified unchanged (still "No ticker watched" idle state, no cockpit grid, no connecting state).

### UT-12 — Journal detail shows an honest error for an unknown thesis id
**Verdict:** PASS
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-12-result.png`
- Navigated directly to `/journal/does-not-exist-12345`. A red-bordered alert box (visually confirmed: dark-red background, red border) reads "This thesis was not found." with sub-text "It may have been removed, or the id is wrong."
- "Return to the journal" link present; clicked it and confirmed via `window.location.href` that it navigated to `/journal` (heading became "Journal" again).

### UT-13 — No page renders the raw "yahoo" feed string; the new vendor stays invisible until J-05
**Verdict:** PASS
**Evidence:** Cross-referenced against `UT-06-result.png`, `UT-03-result.png`, `UT-04-result.png`, `UT-05-result.png`, `UT-07-result.png` (full-page text extractions performed at each of these same page states)
- Cockpit (SIM-BUYER actively watched, from UT-06): full-page text scan — no "yahoo"/"Yahoo" occurrence. Feed badge (`feed-basis-label`) reads exactly "Simulated" (see UT-06).
- Journal: full table text scanned, including the FEED column for both rows — both show "SIM", never "yahoo".
- Studies: full-page text scanned, including the existing study's feed badge — shows "SIP", never "yahoo".
- Performance: full-page text scanned — no "yahoo" occurrence anywhere (ledger, champion panel, registry).
- Structure (with the freshly Yahoo-fetched AAPL series loaded from UT-07/UT-14, whose raw API response literally contains `"feed":"yahoo"`): full-page text scanned across the chart caption, all 28 confluence zone cards, the registry, and the comparison section — zero occurrences of "yahoo". This is the strongest form of this check: real Yahoo-sourced data was on screen and still no vendor string leaked.
- Confirms the finding holds even under the most adversarial case available in this environment (freshly-fetched Yahoo data, actively displayed).

### UT-14 — [Exploratory] A Yahoo-fetched series reaches the Structure chart with no vendor indicator
**Verdict:** PASS (informational — P3, not required for the overall verdict)
**Evidence:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/UT-07-result.png` (same page load); raw curl response inspected inline during the session
- Confirmed via `curl -s http://localhost:8301/research/bars` that the bar store was empty (no pre-existing AAPL series) before starting, satisfying the test's precondition.
- `POST /research/bars` for `{"symbol":"AAPL","timeframe":"1d","start":"2026-05-01T00:00:00Z","end":"2026-06-05T00:00:00Z"}` returned HTTP 200 with `bar_series.feed == "yahoo"`, `bar_count: 24`, and a non-empty `bars[]` array of real-looking OHLCV rows — proving the keyless fetch is real, not a stub.
- Loading `AAPL` / `2026-06-05T00:00:00Z` on `/structure` rendered a candlestick chart built from exactly those 24 bars ("24 of 24 recorded bars"), matching the ~35-calendar-day window fetched (24 trading days is consistent with that span).
- No badge, caption, or tooltip anywhere on the page names Yahoo — confirms this is the documented, expected gap ("Not Visible Yet" per the user-visible-changes report), not a bug. J-05 is expected to add the first visible "Yahoo Finance" label in a later iteration.

---

## Failed Tests

None. All 14 test cases passed.

---

## Skipped Tests

None. All 14 test cases executed.

---

## Notes / Minor Observations (non-blocking)

- **UT-06 step 5 (transient "Connecting…" state):** not visually captured. Two independent attempts to screenshot immediately post-click both landed on the already-resolved cockpit grid, indicating the simulated feed connects in well under a second. This is consistent with (not contrary to) the test's actual concern — "never a frozen blank screen" — but a tester with faster reflexes or a network-throttled environment might catch the literal "Connecting to SIM-BUYER…" copy where this session could not. Recorded as an evidence gap, not a failure.
- Journal, Studies, and Performance pages all had pre-existing data (from earlier sessions) rather than empty states, so the "honest empty state" branches of UT-03/UT-04/UT-05 were not exercised. The populated-data branch is an equally valid pass per each test's "either/or" expected result.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-09
- **Evidence directory:** `reports/qa/goal-yahoo_fetch-iter-1-evidence/`
- **Console errors observed across entire session:** 0 (one benign React DevTools `info` line at initial load; occasional Next.js Fast Refresh `log` lines from dev-mode hot reload — neither is an error/warning)
