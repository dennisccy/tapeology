# Phase goal-structure_ui-iter-1 — UI Test Results

**Phase:** goal-structure_ui-iter-1
**Date:** 2026-07-07
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: UT-10 (P1) fails — see "Failed Tests" section. All other P1 tests (UT-01, 02, 04, 05, 06,
     07, 08, 09, 12, 13, 14) pass. -->

**Overall:** 14/15 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Page loads with header/framing/controls | smoke | P1 | "Structure" heading, exact subtitle + framing copy, Symbol/As-of/Load controls, no console errors | All text matched exactly (verified via DOM eval); labels `["Symbol","As-of (UTC, ISO-8601)"]`; as-of placeholder `2026-06-09T21:00:00Z`; Load button present and initially disabled; only console message was the React DevTools info line | PASS | `reports/qa/goal-structure_ui-iter-1-evidence/UT-01-page-loaded.png` |
| UT-02 | Idle state before Load + after refresh | smoke | P1 | Idle message before Load; same idle message + empty fields after refresh (no persisted query) | Idle message exact match both times; no chart/zone-row present before Load; after refresh both fields were empty and the identical idle message reappeared | PASS | `reports/qa/goal-structure_ui-iter-1-evidence/UT-02-idle-before.png`, `UT-02-idle-after-refresh.png` |
| UT-03 | Load button disabled until both fields filled | validation | P2 | Disabled (~40% opacity) with 0 or 1 field filled; enabled the instant both are filled; click triggers a real fetch | Confirmed via computed style: both empty → `disabled:true, opacity:"0.4", cursor:"not-allowed"`; symbol-only → disabled; as-of-only → disabled; both filled → `disabled:false, opacity:"1"`; click replaced idle state with a real result (no-bar-series state, since fixture wasn't seeded yet) | PASS | none (see UT-08 screenshot for the resulting state) |
| UT-04 | Nav link reachable + data-driven | ux | P1 | 5-link nav (`Cockpit,Journal,Studies,Performance,Structure`) on every page; `/meta/ui-routes`'s last entry is exactly `{"path":"/structure","label":"Structure","nav":true}`; link navigates to `/structure`; no hardcoded `href="/structure"` outside `NavBar.tsx` | Nav order confirmed identical on `/`, `/journal`, `/studies`, `/performance`, `/structure` (5 links, Structure last); fetched `/meta/ui-routes` from within the page origin — returned exactly the 5 pre-existing entries unchanged plus `{"path":"/structure","label":"Structure","nav":true}` as the last/only-new entry; clicking the nav link navigated to `http://localhost:3301/structure` (200, H1 "Structure"); `grep -rn 'href="/structure"'` across `apps/frontend` (excluding `NavBar.tsx`) returned zero matches — `NavBar.tsx` renders `href={route.path}` generically | PASS | `reports/qa/goal-structure_ui-iter-1-evidence/UT-04-nav-structure-link.png` |
| UT-05 | Loading placeholder while fetch in flight | smoke | P1 | Pulse-skeleton placeholder appears transiently, no fabricated content, then replaced by a real result with no blank/error flash | Local responses were too fast to catch by eye on the first attempt (an acceptable outcome per the test's own tolerance), so a QA-only fetch delay was added in the page's JS context (a monkey-patched `window.fetch`, reverted immediately after, no source files touched) to reliably capture the transient state: screenshot shows 3 horizontally-pulsing grey skeleton bars, no numbers/chart; the state then cleanly resolved to the real no-bar-series result | PASS | `reports/qa/goal-structure_ui-iter-1-evidence/UT-05-loading-state.png` |
| UT-06 | Populated: chart + 20 dashed level lines | happy-path | P1 | Candlestick chart, 9 candles, 20 dashed S/R level lines labelled timeframe+type+price, exact caption | Panel titled "Price chart — S/R levels" with a real `<canvas>`-based dark candlestick chart; caption exact match: "Candles: 1h series (9 of 9 recorded bars, as of the query time). Level lines span every recorded timeframe."; screenshot shows dashed lines with labels e.g. "1h swing-pivot 149.48", "1d prior-period-extreme 148.23" (timeframe+type+price, as specified); cross-checked `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z` returns exactly 20 level entries, and `StructureChart.tsx` draws one unconditional `createPriceLine` per entry in the `levels` prop (verbatim price/timeframe/type, no filtering) — code + API + visual evidence agree | PASS | `reports/qa/goal-structure_ui-iter-1-evidence/UT-06-populated-chart.png` |
| UT-07 | Populated: 6 zone cards, byte-for-byte values | happy-path | P1 | Exactly 6 zone cards (5 Class C, 1 Class B); the score-12 card's 3 member rows match the API exactly, including `140` not `140.00` | Extracted page text shows exactly 6 `zone-row` cards in order C(score 8), C(12), C(8), C(8), C(16), B(12) — 5×C + 1×B; the score-12 card's rows are `139.89/1d/prior-period-extreme`, `139.89/1d/swing-pivot`, `140/1d/prior-period-extreme` — a full byte-for-byte diff against the live `GET /research/levels` JSON (fetched directly via curl and via in-page `fetch`) confirms every zone, class, score, and member level renders identically, with no rounding/reformatting | PASS | `reports/qa/goal-structure_ui-iter-1-evidence/UT-06-populated-chart.png` (frames both panels, reused per test-plan's own allowance) |
| UT-08 | Honest state: no bar series recorded | error | P1 | Distinct message "No bar series recorded for PG." + "Recording historical bars needs provider credentials."; no chart/table/other message | Exact text match; verified `chartPresent:false`, `zoneCount:0`, and no other honest-state testid present simultaneously | PASS | `reports/qa/goal-structure_ui-iter-1-evidence/UT-08-no-bar-series.png` |
| UT-09 | Honest state: series but no levels | error | P1 | Distinct message "No levels found for PG as of 2026-05-01T00:00:00Z." + "A bar series is recorded, but nothing is derivable at this as-of time."; no chart/table | Exact text match, distinct wording from UT-08 confirmed; no chart, no zone rows | PASS | `reports/qa/goal-structure_ui-iter-1-evidence/UT-09-no-levels.png` |
| UT-10 | Honest state: levels but no zones (chart stays) | error | **P1** | Chart panel stays visible with 3 dashed level lines (138.86, 140.28, 141.82); zones panel (only) shows the distinct "No qualifying confluence zone..." message | Zones-panel message portion is correct (exact text, correctly scoped — whole-page `no-levels`/`no-bar-series` states were NOT triggered). **But the chart panel renders visually blank**: a full pixel scan of the entire chart box (`reports/qa/goal-structure_ui-iter-1-evidence/UT-10-no-zones.png`) found **zero** pixels matching the level-line color and **zero** pixels matching the "no recorded candle series" hint-text color, even though both elements are present in the DOM with correct computed styles (position, color, non-zero size, opacity 1). Root cause confirmed via `getComputedStyle`: the chart's internal `lightweight-charts` canvases have explicit `z-index:1`/`z-index:2` (`position:absolute`), while the app's own empty-state hint overlay has `z-index:auto` — CSS stacking order therefore always paints the (visually empty but opaque, solid-background) canvases over the hint, regardless of DOM order. Separately, with zero candles the price scale has no data to autorange from, so the created price lines are not rendered in any visible position either. Net effect: at this as-of, the user sees an unexplained blank chart box instead of "real level lines drawn, real disclosure that no candles apply yet." | **FAIL** | `reports/qa/goal-structure_ui-iter-1-evidence/UT-10-no-zones.png`, `UT-10-no-zones-recheck.png` |
| UT-11 | Malformed as-of → degraded panel | error | P2 | Degraded panel with backend's exact validation message, no crash, page stays interactive | Exact text "as_of must be an ISO date-time" + "Nothing cached and nothing fabricated is shown in its place."; no console errors; correcting the field and clicking Load again recovered normally (no-bar-series result) | PASS | `reports/qa/goal-structure_ui-iter-1-evidence/UT-11-malformed-asof-degraded.png` |
| UT-12 | Backend unreachable → degraded panel + nav | error | P1 | Nav shows "navigation unavailable — backend unreachable"; Load shows the backend-unreachable degraded panel; full recovery after backend restart | Backend stopped: nav rendered exactly `navigation unavailable — backend unreachable` with 0 nav links; clicking Load rendered the degraded panel with exact text "Backend unreachable — is the API running?" + the fixed second line; no console-crashing errors, no blank page; backend restarted → nav returned to the normal 5 links and `/structure` loaded PG's full populated state again (6 zones, chart) | PASS | `reports/qa/goal-structure_ui-iter-1-evidence/UT-12-nav-unavailable.png`, `UT-12-backend-unreachable-degraded.png` |
| UT-13 | Four pre-existing pages unchanged | regression | P1 | All 4 pages return 200, render pre-existing content unchanged, 5-link nav with Structure in 5th position | `/` shows Cockpit ticker input ("Ticker e.g. SIM-BUYER") + data-source buttons + Watch; `/journal` shows heading "Journal" + filters + honest empty journal list; `/studies` shows heading "Replay studies" + study form + empty list; `/performance` shows heading "Performance" + PnL ledger + champion pointer + profile registry, all fully populated; all 4 pages showed the same 5-link nav (`Cockpit,Journal,Studies,Performance,Structure`); no stray Structure content on any page; no console errors across the batch | PASS | none (see UT-04 screenshot for the shared nav) |
| UT-14 | Cockpit SIM-BUYER flow still works | regression | P1 | Watch → connecting → populated cockpit within ~10s, tape state resolves to `buyer_control` | "Simulated" confirmed default-selected (`aria-pressed:"true"`); typed `SIM-BUYER`, clicked Watch; cockpit populated with quote (Bid/Ask/Spread/Last), recent trades, features (10s/30s/60s/180s/300s), Tape State "Buyer Control" / Confidence 0.829, observations, and event log "Tape state changed to buyer_control" — never blank/stuck; no console errors | PASS | `reports/qa/goal-structure_ui-iter-1-evidence/UT-14-sim-buyer-cockpit.png` |
| UT-15 | Symbol field free-text entry works standalone | ux | P3 | Typing works regardless of dropdown; free-typed value submits correctly whether or not a suggestion is picked | Note: this environment DOES have live symbol-search data available (a real suggestions dropdown appeared for "PG" — the test plan's stated no-credentials assumption did not hold in this run; this is a documented non-blocker per the plan's own wording, since it only affects which of the two described branches is exercised). Typed "PG" one character at a time while a 20-item dropdown was open; clicked elsewhere to dismiss it without selecting any suggestion (value remained the free-typed "PG"); submitted with Load and got a normal result (no-bar-series state) — proving the free-typed value was used | PASS | none |

---

## Passed Tests

### UT-01 — Structure page loads with header, framing copy, and both controls
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-01-page-loaded.png`
- Heading, subtitle, and read-only framing line all matched the spec text exactly; Symbol/As-of controls and Load button present and correctly initially disabled; zero console errors.

### UT-02 — Idle placeholder shown before first Load, and again after a refresh
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-02-idle-before.png`, `UT-02-idle-after-refresh.png`
- Idle message present with no chart/table before Load; after typing values (without clicking Load) and refreshing, both fields were empty again and the identical idle message reappeared — confirms the page holds no cross-reload state, as intended.

### UT-03 — Load button is disabled until both Symbol and As-of are filled
**Verdict:** PASS
**Evidence:** none (state transition verified via computed styles; see UT-08 screenshot for the post-click result)
- `disabled`/opacity/cursor computed styles confirmed disabled with 0 or 1 field filled, enabled the instant both were filled; clicking then triggered a real fetch (not a no-op).

### UT-04 — Structure nav link is reachable from every page and is proven data-driven
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-04-nav-structure-link.png`
- 5-link nav confirmed identical across `/`, `/journal`, `/studies`, `/performance`, `/structure`; `GET /meta/ui-routes` (fetched from the page's own origin) returns the 5 pre-existing entries unchanged plus the new `/structure` entry as the sole addition, last in the array; source grep found no hardcoded `/structure` href outside `NavBar.tsx`'s generic `route.path` template.

### UT-05 — Loading placeholder appears while the fetch is in flight
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-05-loading-state.png`
- Local fetches resolved too quickly to catch by eye on the first pass (explicitly tolerated by the test); an in-page-only fetch delay (reverted immediately after, no source touched) reliably captured the 3-bar pulse-skeleton placeholder, which then cleanly resolved to a real result with no blank/error flash.

### UT-06 — Populated state: chart renders candles plus all 20 dashed S/R level lines
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-06-populated-chart.png`
- Candlestick chart rendered with the exact caption text; visible dashed reference lines labelled with timeframe+type+price (e.g. "1h swing-pivot 149.48"); cross-checked the live API (20 levels) against `StructureChart.tsx`'s unconditional one-price-line-per-level loop — code, API, and screenshot all agree.

### UT-07 — Populated state: confluence-zones table shows 6 zone cards with byte-for-byte values
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-06-populated-chart.png` (frames both panels)
- Exactly 6 zone cards (5 Class C, 1 Class B); the score-12 card's 3 member rows matched the live `GET /research/levels` JSON byte-for-byte, including the un-reformatted `140` (not `140.00`).

### UT-08 — Honest state: no_bar_series_for_symbol shows the distinct credentials-needed message
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-08-no-bar-series.png`
- Exact two-line message, no chart/table/other honest-state message present simultaneously.

### UT-09 — Honest state: series-but-no-levels shows the distinct "no levels found" message
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-09-no-levels.png`
- Exact two-line message with the correct as-of value interpolated; wording distinct from UT-08; no chart/table.

### UT-11 — Malformed as-of input renders the degraded panel, never a crash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-11-malformed-asof-degraded.png`
- Backend's own validation message ("as_of must be an ISO date-time") shown verbatim plus the fixed second line; no console errors; page remained interactive — correcting the field and reloading recovered normally.

### UT-12 — Backend unreachable renders the degraded panel and the nav's own degraded state, never a blank page
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-12-nav-unavailable.png`, `UT-12-backend-unreachable-degraded.png`
- Nav degraded to "navigation unavailable — backend unreachable" with 0 links; `/structure`'s Load produced the exact backend-unreachable degraded panel; after restarting the backend, the 5-link nav and full `/structure` functionality (6 zones + chart) returned — confirms transient, not permanent, degradation.

### UT-13 — The four pre-existing top-bar pages remain reachable and unchanged
**Verdict:** PASS
**Evidence:** none (see UT-04 screenshot for the shared nav; each page's content verified via `extract`)
- `/`, `/journal`, `/studies`, `/performance` all render their pre-existing content correctly (Cockpit controls; Journal filters + list; Replay studies form + list; Performance PnL ledger + champion), each with the same 5-link nav including Structure; no stray Structure content, no new console errors.

### UT-14 — Cockpit SIM-BUYER simulated-tape flow still works end to end
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-14-sim-buyer-cockpit.png`
- Watch on `SIM-BUYER` (Simulated mode, confirmed default-selected) populated the full cockpit (quote, trades, features, tape state, observations, event log) and resolved to `buyer_control`, matching pre-iteration behavior exactly.

### UT-15 — Symbol field accepts free-text entry with no dependency on autocomplete matches
**Verdict:** PASS
**Evidence:** none
- This environment actually has live symbol-search data (a real dropdown appeared, unlike the test plan's stated assumption — a documented non-blocking environmental difference). Typing was never blocked by the dropdown; dismissing it without selecting a suggestion preserved the free-typed value; Load submitted it successfully.

---

## Failed Tests

### UT-10 — Honest state: levels-but-no-zones shows the distinct message while the chart still renders
**Verdict:** FAIL
**Failure:** With `symbol=PG`, `as_of=2026-06-02T12:00:00Z` (levels present, zero recorded candles predate this as-of, zero confluence zones), the confluence-zones panel correctly and exclusively shows "No qualifying confluence zone among these levels." / "Levels exist, but none cluster closely enough across timeframes to form a zone." — that part of the test passes. However, the test's other explicit expected-result clause — "the chart panel IS still shown... with 3 dashed level lines at prices 138.86, 140.28, and 141.82" — does **not** hold: the chart panel renders as a visually blank box. Neither the 3 expected dashed level lines nor the "No recorded candle series available to draw for this symbol" fallback hint are visible to the user, even though both exist in the DOM with seemingly-correct computed CSS (the hint has `opacity:1`, correct `color:rgb(71,85,105)`, non-zero size, and a position rect that falls entirely inside the visible chart box).

A full pixel scan of the entire chart box in the saved screenshot (`reports/qa/goal-structure_ui-iter-1-evidence/UT-10-no-zones.png`, cross-checked against the byte-identical `UT-10-no-zones-recheck.png`) found:
- 0 pixels matching the level-line color (`rgb(148,163,184)`, the `#94a3b8` used by `StructureChart.tsx`'s `createPriceLine`)
- 0 pixels matching the hint-text color (`rgb(71,85,105)`, the `text-slate-600` `EmptyHint` uses)
- Only the chart's own static border/grid chrome (`rgb(30,41,59)`) is visible — i.e., an empty frame.

Root cause (confirmed via `getComputedStyle`, not speculation): the chart's internal `lightweight-charts` canvas elements have explicit `position:absolute; z-index:1` / `z-index:2`. The app's own empty-state hint overlay (`apps/frontend/components/StructureChart.tsx`'s `{!hasBars && <EmptyHint>...}` branch) is also `position:absolute` but has `z-index:auto`. Per CSS stacking rules, an element with an explicit non-negative `z-index` always paints above a sibling-subtree element at `z-index:auto`, regardless of DOM order — so the (visually empty, but opaque, solid-`#020617`-background) canvases always paint over the hint text, permanently occluding it whenever this state is reached. Separately, with `bars.length === 0` the candlestick series has no data to autoscale its price axis from (`chart.timeScale().fitContent()` is also skipped in this branch), so the 3 `createPriceLine` calls do not end up in any visible position on the price axis either — no axis price labels are visible at all in this screenshot, unlike the populated UT-06 screenshot, which shows a normal labelled price axis.

Net effect: an actual user reaching this exact combination (levels present, symbol has zero candles as-of this time) sees an unexplained blank chart box, not the "real level lines drawn, real disclosure that no candles apply yet" the test (and the phase's honest-state anti-goal) call for. No console error was thrown — the failure is silent.

**Evidence:** `reports/qa/goal-structure_ui-iter-1-evidence/UT-10-no-zones.png`, `reports/qa/goal-structure_ui-iter-1-evidence/UT-10-no-zones-recheck.png`

**Steps taken:**
1. Seeded the committed PG bar fixture into the backend's live bar directory (`apps/backend/.data/bars/`).
2. Navigated to `/structure`, entered `PG` / `2026-06-02T12:00:00Z`, clicked Load.
3. Verified via API (`GET /research/levels?symbol=PG&as_of=2026-06-02T12:00:00Z`) that the backend returns exactly 3 levels (138.86, 140.28, 141.82, all `1d prior-period-extreme`) and `confluence_zones: []` — matching the test's documented golden values.
4. Confirmed via DOM query that the zones-only honest message renders correctly, scoped only to the zones panel (`structure-no-levels` and `structure-no-bar-series` were both absent).
5. Confirmed via `getBoundingClientRect`/`getComputedStyle` that the chart container, the empty-candle hint wrapper, and the hint text itself all have correct, non-hidden, in-viewport computed styles.
6. Took full-page and viewport screenshots; visually inspected — no lines, no hint text visible in the chart box.
7. Programmatically sampled every pixel in the chart box's rendered region against the expected line-color, hint-text-color, and grid-color RGB values — 0 matches for the line/hint colors, confirming the visual absence is real, not a viewing artifact.
8. Inspected the chart's internal `<canvas>` elements' computed `position`/`z-index` — found explicit `z-index:1`/`2` on `position:absolute` canvases versus the hint's `z-index:auto`, which fully explains the occlusion per CSS stacking rules.

**Expected:** Chart panel visibly shows 3 dashed level lines at 138.86/140.28/141.82 (or, per the test's own fallback wording, at minimum a visible "No recorded candle series available to draw for this symbol" hint) while the zones panel shows its own distinct empty-zone message.

**Actual:** The zones panel message is correct and correctly scoped. The chart panel renders as a visually blank box — neither the level lines nor the fallback hint are visible to the user, due to a CSS z-index stacking conflict between the charting library's internal canvases and the app's own empty-state overlay, compounded by the price axis having no visible range to place the lines in given the absence of candle data.

---

## Skipped Tests

None — Chrome MCP was available and the frontend/backend were both reachable for the full run (the backend was intentionally stopped/restarted only as part of executing UT-12 itself).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (started/restarted directly via `scripts/start-backend.sh` with `CHAIN_BACKEND_PORT=8301`/`CHAIN_FRONTEND_PORT=3301` after the pre-existing shared-services backend process was found already stopped at the start of this run; healthy for the remainder except for the deliberate UT-12 outage)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-07
- **Evidence directory:** `reports/qa/goal-structure_ui-iter-1-evidence/`
- **Fixture handling:** the committed PG bar fixture (`apps/backend/tests/fixtures/bars/009371c9c02f46338bafef47148f92ad.json`, `b08b1a55ef4a45b2a1adad8fa82ccdf1.json`) was copied into the backend's live bar directory (`apps/backend/.data/bars/`) for UT-06/07/09/10 and the fixture-dependent half of UT-08's sequencing, then removed afterward — confirmed via a final API check that `no_bar_series_for_symbol` reverted to `true` for `PG`, leaving no test data behind.
- **Environmental note (non-blocking):** this run's backend actually has live symbol-search data available (`GET /symbols/search?q=PG` returns real matches), which differs from the test plan's stated assumption of no vendor credentials. This only changed which documented branch of UT-15 was exercised (the "dropdown appears" branch instead of the "no dropdown" branch) and did not affect any other test — `no_bar_series_for_symbol` (a separate, unrelated endpoint concern) still behaved exactly as specified in UT-08.
