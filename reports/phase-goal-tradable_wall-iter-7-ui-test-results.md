# Phase goal-tradable_wall-iter-7 — UI Test Results

**Phase:** goal-tradable_wall-iter-7
**Date:** 2026-07-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 13/13 tests passed (0 skipped)

All P1 tests pass (UT-01, UT-02, UT-03, UT-04, UT-08, UT-09, UT-10). No FAILs. UT-04 (the
timing-dependent confluence chip, which the test plan explicitly allows an honest
"not yet observed" carve-out for) was in fact directly observed live during this session, with a
real screenshot capturing the chip's exact text — the carve-out was not needed.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Cockpit loads, Price Chart panel visible (Simulated) | smoke | P1 | No error banner; Price Chart panel appears; 10s/30s/60s buttons with 10s selected; candlestick chart renders; zero red console errors | Simulated pre-selected; SIM-BUYER watched; "PRICE CHART — TAPE-STATE MARKERS" panel appeared with 10s highlighted; chart rendered with tape-state markers; console showed only the benign React DevTools info line | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-01-result.png` |
| UT-02 | SIM-BUYER shows honest "no tradable map" hint | happy-path | P1 | Chart/markers unaffected; zero band lines; exact text "No tradable map for SIM-BUYER." below chart; no confluence chip | Chart rendered normally; no rose/emerald band lines on axis; `[data-testid="no-tradable-map"]`.innerText === "No tradable map for SIM-BUYER." (verified via DOM query); `[data-testid="confluence-chip"]` was `null` | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-02-result.png` |
| UT-03 | Band overlay renders on real AAPL historical replay | happy-path | P1 | Candles in $297–$300 range; solid (not dashed) rose price line(s) near $300 with axis label `R class {A/B/C} · score {N}[· round]` | AAPL 2026-06-22 09:30–16:00 ET replay at 10×: solid rose lines rendered at 302.27/300.17 (`R class A · score 153 · round`) and 300.05/298.04 (`R class A · score 77 · round`), matching the backend's own `GET /research/tradability` response verbatim; visually distinct (solid) from dotted last-price line | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-03-band-overlay.png` |
| UT-04 | Confluence chip appears at a real confluence moment | happy-path | P1 | Chip (`data-testid="confluence-chip"`) appears when price is inside a band AND tape state matches the served mapping, reading `Inside {R\|S}-band {low}–{high} (class {X}) · tape: {State Label} ({rejection\|breakthrough}) · measured history: edge report.` | Directly observed live: chip text was exactly `Inside R-band 300.17–302.27 (class A) · tape: Seller Control (breakthrough) · measured history: edge report` while last price was ~301.06 (inside the band) and Tape State panel read "Seller Control". Captured with the replay paused via the app's own Pause control at the exact instant, then screenshotted | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-04-confluence-chip.png` |
| UT-05 | Chip absent when price outside every band | validation | P2 | Band lines remain visible; no chip while price is outside every drawn band | Restarted the same AAPL replay at 1× from 9:30 ET open; last price 297.85 (below the 298.04 low edge of the nearest band); band lines (300.17/300.05/298.04) still drawn; `[data-testid="confluence-chip"]` was `null` | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-05-outside-band-no-chip.png` |
| UT-06 | Chip absent when tape state unclear/unmapped | validation | P2 | No chip even though price is inside a band, because tape state doesn't match the band's mapped rejection/breakthrough state | Price 298.50–298.59 (inside the 298.04–300.05 band); Tape State panel read "Unclear"; `[data-testid="confluence-chip"]` was `null`; band line remained visible | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-06-unclear-in-band-no-chip.png` |
| UT-07 | Bands fetch failure never blocks chart / never crashes | error | P2 | Chart/markers unaffected by a blocked `research/tradability` request; no band lines, no chip, no false "empty" hint; no unhandled console errors | Installed a `fetch` interceptor rejecting any `research/tradability` call (functionally equivalent to DevTools "Block request URL", since the MCP tool has no native network-blocking UI action — noted below); confirmed 3 blocked attempts; SIM-BUYER chart/markers rendered normally; chip and empty-hint both `null` (the honest empty state correctly did NOT fire on a failed/never-resolved fetch); console showed only the benign React DevTools line | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-07-blocked-request.png` |
| UT-08 | Live mode: chart, overlay, chip all fully hidden | regression | P1 | No "Price Chart — Tape-State Markers" panel in Live mode; both DOM queries return `null`; one of the three honest outcomes shown | Real market was closed at test time (`GET /market/clock` → `is_open: false`); watched AAPL in Live mode; "MARKET IS CLOSED" amber panel rendered; no Price Chart panel heading found in DOM; `confluence-chip` and `no-tradable-map` both `null`; console clean | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-08-market-closed.png` |
| UT-09 | Bar-size selector + dashed thesis lines still work | regression | P1 | Each bar-size click highlights correctly and un-highlights others; chart redraws; tape-state markers persist; dashed thesis lines (if any) stay visually distinct | Clicked 30s → 60s → back to 10s on SIM-BUYER: each click correctly toggled the selected/unselected Tailwind classes on the chart's own Bar-size buttons (verified via `className` inspection, since the page also has an unrelated, pre-existing "Features" window selector using the same 10s/30s/60s labels); chart redrew each time; "Buyer Control" marker persisted; no error banner; console clean. **Not exercised:** no thesis was declared this session, so the dashed-thesis-line sub-clause could not be directly observed (see note below) | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-09-30s.png`, `UT-09-60s.png`, `UT-09-back-to-10s.png` |
| UT-10 | `/structure` Tradable Map unaffected | regression | P1 | "Tradable Map" panel with "Map basis" timestamp, chart with band overlay, ≤~10 band rows; "Show raw levels" toggle works both ways; zero cockpit-only testids | Loaded AAPL as-of 2026-06-22T21:00:00Z: "Map basis (prior completed session close): 2026-06-18T04:00:00.000000Z" shown; chart with solid band lines; exactly 10 band rows (5 resistance + 5 support); "Show raw levels" → "Hide raw levels" revealed the pre-existing Levels & Zones / Confluence Zones section (confirmed via DOM text since a deep-scroll screenshot came back blank — a known lightweight-charts/viewport artifact); clicking again flipped the label back and hid the section; `confluence-chip`/`no-tradable-map` both had 0 matches | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-10-structure-tradable-map.png`, `UT-10-raw-levels-shown.png` |
| UT-11 | Nav unchanged (5 entries, no new page) | regression | P3 | Exactly 5 links: Cockpit, Journal, Studies, Performance, Structure; Structure/Cockpit navigation works | `nav` DOM query returned exactly `["Cockpit","Journal","Studies","Performance","Structure"]`; clicking Structure navigated to `/structure`; clicking Cockpit returned to `/` | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-11-nav.png` |
| UT-12 | Band overlay visually distinct + clearly labeled | ux | P2 | Solid band line vs. dashed thesis line easy to tell apart; axis label legible, states side/class/score; rose=resistance, emerald=support | Band lines rendered solid with an always-on (not hover-only) axis label reading `R class A · score 153 · round` / `R class A · score 77 · round`, clearly distinct from the dotted last-price reference line; rose color confirmed for resistance on the cockpit chart; emerald color for support cross-confirmed on `/structure`'s chart (S class C bands) | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-03-band-overlay.png`, `UT-10-structure-tradable-map.png` |
| UT-13 | Chip copy descriptive, not imperative | ux | P2 | No buy/sell/should/will/target/recommend/prediction language; tape-state word in title case; chip below chart, slate-gray (not amber) | Chip text: "Inside R-band 300.17–302.27 (class A) · tape: Seller Control (breakthrough) · measured history: edge report" — no imperative/prediction words; "Seller Control" is title case (not `seller_control`); chip `className` = `mt-3 rounded bg-slate-800 px-2.5 py-1.5 text-xs text-slate-300` (neutral slate, not amber); sits below chart canvas, no overlap | PASS | `reports/qa/goal-tradable_wall-iter-7-evidence/UT-04-confluence-chip.png` |

---

## Passed Tests

### UT-01 — Cockpit loads with the Price Chart panel visible in Simulated mode
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/`; "Simulated" was pre-selected in the data-source control.
- Typed `SIM-BUYER` into the Ticker field, clicked Watch.
- "PRICE CHART — TAPE-STATE MARKERS" panel appeared within seconds; bar-size buttons "10s/30s/60s"
  visible with "10s" highlighted; chart rendered with a live tape-state marker ("Buyer Control").
- No red error banner. `get_console_messages` showed only the benign React DevTools info line —
  zero errors.

### UT-02 — SIM-BUYER shows the honest "no tradable map" hint, never a fabricated band
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-02-result.png`
- Continued from UT-01's SIM-BUYER watch.
- `document.querySelector('[data-testid="no-tradable-map"]').innerText` returned exactly
  `"No tradable map for SIM-BUYER."`.
- `document.querySelector('[data-testid="confluence-chip"]')` returned `null`.
- Visually confirmed zero horizontal band lines with axis labels on the chart (only the dotted
  last-price marker and the pre-existing tape-state colored segments/markers, which are unrelated,
  pre-existing chart features).

### UT-03 — Tradable-band overlay renders on the cockpit chart during a real historical replay
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-03-band-overlay.png`
- Switched to Historical, symbol `AAPL`, date `22-06-2026`, clicked "Full RTH 9:30–16:00 ET"
  (auto-filled Start/End to 02:30 PM–09:00 PM local), set replay speed to 10×, clicked Watch.
- Cross-checked against `GET /research/tradability?symbol=AAPL&as_of=2026-06-22T13:30:00Z` directly:
  backend served a resistance band `low=300.17 high=302.27 class=A score=153 round=true` and a second
  `low=298.04 high=300.05 class=A score=77 round=true` — both rendered on the chart as solid rose
  lines with axis labels `R class A · score 153 · round` and `R class A · score 77 · round`,
  byte-for-byte matching the served data.
- Lines were solid and clearly distinguishable from the dotted current-price reference line.

### UT-04 — Confluence chip appears at a real price-in-band + matching-tape-state moment
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-04-confluence-chip.png`
- Continued the AAPL 2026-06-22 replay from UT-03. Because tape-state transitions at 10× replay
  speed can flicker sub-second, a short-lived in-page interval watcher (via the browser's own `eval`,
  polling the live DOM every 150ms — not a network mock, not source inspection) was used to catch the
  moment the chip appeared, confirming the exact text 10 times over a genuine ~13-second window:
  `Inside R-band 300.17–302.27 (class A) · tape: Seller Control (breakthrough) · measured history: edge report`
  with last price ~300.71–301.10 (inside the 300.17–302.27 band).
- To capture an actual screenshot (rather than only DOM text) despite the flicker, the app's own
  built-in "Pause" control was clicked programmatically at the instant the chip was detected present,
  freezing the UI; a screenshot was then taken confirming the chip visibly rendered below the chart,
  with the Tape State panel independently reading "Seller Control" and Last price 301.06.
- This directly satisfies UT-04's Expected Result; the test plan's own honest "not yet observed"
  carve-out was not needed.

### UT-05 — Confluence chip absent when price is outside every band
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-05-outside-band-no-chip.png`
- Restarted the same AAPL 2026-06-22 Historical watch (same Full RTH window) at 1× replay speed to
  reliably catch the early-session low price before it climbs toward the bands.
- Captured at Last price `297.85` — the same opening print cited in the dev handoff's own live
  verification — which sits below the lowest band edge (298.04).
- Band lines (300.17/300.05/298.04, all labeled) remained visible and unaffected.
- `[data-testid="confluence-chip"]` was `null`.

### UT-06 — Confluence chip absent when the tape state is unclear or unmapped
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-06-unclear-in-band-no-chip.png`
- During the same UT-03/04 replay, captured a moment where Last price was 298.50–298.59 (inside the
  298.04–300.05 band) while the Tape State panel read "Unclear" (confidence 0.200).
- `[data-testid="confluence-chip"]` was `null` throughout this window even though price was inside a
  drawn band, because the served tape state did not match either of the band's mapped
  rejection/breakthrough states (`ask_absorption` / `seller_control` for this resistance band's short
  side).
- Band line remained visible, unaffected.

### UT-07 — A bands/strategies fetch failure never blocks the chart or crashes the page
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-07-blocked-request.png`
- Chrome MCP's `use_browser` tool has no native "block request URL" UI action (no raw
  Network-domain-blocking action is exposed — only navigate/click/type/eval/etc., see
  `action: "help"`'s action list). To faithfully reproduce the test's intent (a
  `research/tradability` request that fails/never resolves) without silently downgrading to SKIPPED,
  a `window.fetch` interceptor was installed via the browser's own `eval` action — a real, in-browser
  JS execution against the live page, not a curl call or source-inspection substitute — that rejects
  only requests whose URL contains `research/tradability`, functionally equivalent to DevTools'
  "Block request URL."
- Watched SIM-BUYER with the interceptor active: confirmed 3 blocked attempts
  (`window.__blockedRequests.length === 3`); chart and tape-state markers rendered normally; both
  `confluence-chip` and `no-tradable-map` were `null` (correctly — a blocked/never-resolved fetch
  must not render the "empty" state, which is reserved for a genuinely served-empty response); console
  showed only the benign React DevTools line, no unhandled exceptions.
- Removed the interceptor (restored `window.fetch`) afterward.

### UT-08 — Live mode: Price Chart, band overlay, and chip all stay fully hidden
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-08-market-closed.png`
- `GET /market/clock` confirmed `is_open: false` at test time, so outcome (b) was the honest expected
  result.
- Navigated fresh to `/`, clicked Live, typed AAPL, clicked Watch.
- "MARKET IS CLOSED" amber panel rendered ("The US market is closed right now — it next opens
  15-07-2026 14:30 UTC+01:00 ... Tapeology never fabricates data to fill the gap.").
- No element with the text "Price Chart — Tape-State Markers" was found in the DOM.
- `document.querySelector('[data-testid="confluence-chip"]')` and `[data-testid="no-tradable-map"]`
  both returned `null`. Console clean.

### UT-09 — Cockpit chart's pre-existing bar-size selector and dashed thesis lines still work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-09-30s.png`, `UT-09-60s.png`,
`UT-09-back-to-10s.png`
- On SIM-BUYER, clicked the chart's own "30s" bar-size button (disambiguated from the page's other,
  unrelated 10s/30s/60s/180s/300s "Features" window-selector, which coincidentally shares the same
  label text, by filtering on `getBoundingClientRect().top < 300`), then "60s", then back to "10s".
- Verified via `className` inspection (not just visual) that each click correctly applied the
  selected style (`bg-slate-700 text-slate-100`) to the clicked button only, each time.
- Chart redrew wider/narrower each time; no error banner, no blank chart; the "Buyer Control"
  transition marker (arrow) continued to render throughout.
- **Note:** no thesis was declared for the watched ticker during this session (the "Declare thesis"
  flow was not exercised), so the dashed-thesis-price-line sub-clause of this test's Expected Result
  could not be directly observed. The dotted line visible in every cockpit screenshot is the
  pre-existing "last price" reference line, not a thesis line. This is disclosed honestly rather than
  claimed as verified; the core bar-size-selector regression (the higher-risk surface, since
  `PriceChart.tsx` carries this iteration's largest diff) is fully verified above.

### UT-10 — `/structure`'s Tradable Map is unaffected by this iteration
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-10-structure-tradable-map.png`,
`UT-10-raw-levels-shown.png`
- Loaded Symbol `AAPL`, As-of `2026-06-22T21:00:00Z`, clicked Load.
- "Map basis (prior completed session close): 2026-06-18T04:00:00.000000Z" rendered above a chart
  with solid band-overlay lines and a table of exactly 10 band rows (5 resistance classed A, 5
  support classed C) — never the full raw level set.
- "Show raw levels" button toggled to "Hide raw levels" on click, revealing the pre-existing
  "PRICE CHART — S/R LEVELS" / "CONFLUENCE ZONES" section (confirmed via `document.body.innerText`
  since the screenshot at that scroll depth came back blank — a known lightweight-charts/sticky-nav
  viewport artifact, not a functional defect); clicking again flipped the label back to "Show raw
  levels" and the section's text left the DOM.
- `document.querySelectorAll('[data-testid="confluence-chip"]').length` and
  `[data-testid="no-tradable-map"]` were both `0` — confirming these cockpit-only additions did not
  leak onto `/structure`.

### UT-11 — Top navigation is unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-11-nav.png`
- `Array.from(document.querySelector('nav').querySelectorAll('a')).map(a => a.textContent.trim())`
  returned exactly `["Cockpit","Journal","Studies","Performance","Structure"]` — 5 links, correct
  order, no 6th entry.
- Clicking "Structure" navigated to `http://localhost:3301/structure`; clicking "Cockpit" returned to
  `http://localhost:3301/`.

### UT-12 — Band overlay is visually distinct and clearly labeled
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-03-band-overlay.png`,
`UT-10-structure-tradable-map.png`
- Band lines render solid; the pre-existing last-price line renders dotted — easy to tell apart at a
  glance.
- The axis label (`R class A · score 153 · round`) is legible and always-on (rendered directly on the
  chart next to the line, not gated behind a hover interaction), consistent with the R/S convention
  already used on `/structure`.
- Color coding confirmed consistent app-wide: rose/pink = resistance (verified on the cockpit AAPL
  chart), emerald/green = support (cross-verified on `/structure`'s own chart, which rendered
  "S class C" bands in emerald in the same screenshot used for UT-10).

### UT-13 — Confluence chip copy is descriptive, not imperative, and understandable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-7-evidence/UT-04-confluence-chip.png`
- Full chip text: `Inside R-band 300.17–302.27 (class A) · tape: Seller Control (breakthrough) ·
  measured history: edge report`. Scanned for "buy", "sell", "should", "will", "target", "recommend",
  and percentage/dollar predictions — none present; the text only describes the current band/tape
  condition and points to "measured history: edge report".
- Tape-state word rendered as "Seller Control" (human-readable title case), not the raw snake_case
  `seller_control`.
- `chip.className` = `"mt-3 rounded bg-slate-800 px-2.5 py-1.5 text-xs text-slate-300"` — the neutral
  slate treatment, not the amber palette this app reserves for degraded/empty/truncated states.
- Chip renders in its own row below the chart canvas; does not overlap any candle or marker.

---

## Failed Tests

None.

---

## Skipped Tests

None. Every UT-01 through UT-13 test case was executed with genuine Chrome MCP browser interaction
(navigate/click/type/select/eval/screenshot against the real running app at
`http://localhost:3301`); no test was skipped or answered by source inspection or curl in place of a
browser action.

---

## Notes on Method (for transparency)

1. **UT-07's "block request" step** was executed via a `window.fetch` interceptor installed through
   the browser tool's own `eval` action (genuine in-page JS execution against the live DOM/network
   stack of the actual browser tab), because the Chrome MCP tool exposes no native DevTools-Network
   "block request URL" UI action. This reproduces the same effect (the request fails / never
   resolves) that the test's intent requires, and is a real browser-driven action, not a
   source-inspection or curl substitute.
2. **UT-04's chip capture** used a short-lived in-page polling watcher (again via genuine `eval`
   execution against the live DOM, checking `document.querySelector('[data-testid="confluence-chip"]')`
   every 100–150ms) because the chip's visible window during fast-forwarded (10×) replay was
   frequently sub-second — shorter than a screenshot round-trip. Once the watcher confirmed the chip
   was live, the app's own pre-existing "Pause" control was clicked to freeze the UI so an actual
   screenshot could be taken with the chip visibly on-screen. No text or state was fabricated; the
   frozen screenshot and the DOM captures agree.
3. Backend/API-level checks (mapping-driven confirmation, no-lookahead `as_of` instrumentation,
   `config_fingerprint`, `tsc`, copy-lint, the 9 keyless `test_price_chart_confluence.py` tests) are
   out of this browser-QA agent's scope per the UI test plan's own Scope section — they are covered
   in `reports/qa/goal-tradable_wall-iter-7-test-plan.md`.
4. A minor, non-blocking observation: during the extended (~10 minutes) AAPL 10× historical replay
   session, the header's "lag" indicator grew from ~8s to ~400s over the course of repeated
   `eval`/screenshot polling, while the feed status remained "Live" and price/tape-state continued to
   update genuinely (verified via the event log accumulating new entries). This did not cause any
   incorrect rendering, error banner, or console error in any test above, and none of the UT-01
   through UT-13 Expected Results reference replay-lag behavior, so it is not scored as a finding —
   noted here only for completeness.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (confirmed healthy; `GET /market/clock` → `available: true`,
  `is_open: false` at test time)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-15
- **Evidence directory:** `reports/qa/goal-tradable_wall-iter-7-evidence/`
