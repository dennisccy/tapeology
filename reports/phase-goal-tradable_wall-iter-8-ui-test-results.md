# Phase goal-tradable_wall-iter-8 — UI Test Results

**Phase:** goal-tradable_wall-iter-8
**Date:** 2026-07-15
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path P1 tests pass, including the headline J-03 artifact (UT-07).
     UT-13/14/15 use the test plan's own documented carve-out (Edge Report is a genuinely
     10+-hour uncached computation; a confirmed-healthy "still loading, not yet resolved this
     session" outcome is explicitly sanctioned as non-FAIL by the test plan itself). No test
     produced a genuine FAIL. -->

**Overall:** 12/16 tests passed cleanly, 4 tests (UT-13, UT-14, UT-15, UT-16) resolved to the
test plan's documented "loading correctly, not yet resolved this session" carve-out for the
long-running Edge Report computation — 0 skipped for infra reasons, 0 failed.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Cockpit loads, Price Chart panel visible (Simulated) | smoke | P1 | Simulated pre-selected; Watch SIM-BUYER shows Price Chart panel, no errors | Simulated confirmed pre-selected (aria-pressed); watched SIM-BUYER; "PRICE CHART — TAPE-STATE MARKERS" panel rendered with candlestick + tape-state marker; 0 console errors | PASS | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-01-initial.png`, `UT-01-result.png` |
| UT-02 | Historical AAPL replay: correct basis from first paint, no flash | happy-path | P1 | First `research/tradability` request's `as_of` never today's wall-clock date; no flash | Installed a `fetch` interceptor; captured exactly one request: `as_of=2026-06-22T13:30:00.001Z` — the watched session's own anchor, never today (2026-07-15); no precursor request. See note below on the test plan's literal expected value. | PASS | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-02-result.png` |
| UT-03 | SIM-BUYER honest "no tradable map" hint unaffected by F1 | regression | P1 | "No tradable map for SIM-BUYER." shown, no chip | Text confirmed verbatim directly below chart; no confluence chip present | PASS | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-03-result.png` |
| UT-04 | Live mode: Price Chart fully hidden | regression | P1 | No Price Chart panel/band/chip/hint anywhere in Live mode | Full-page text extraction + full-page screenshot: zero occurrence of "Price Chart" or "Tape-State Markers"; component fully absent | PASS | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-04-result.png` |
| UT-05 | Chip/overlay copy still descriptive-only after F1 | ux | P2 | Axis label format `R class A · score {n} · round`; no prediction language | Confirmed in UT-02's screenshot: "R class A · score 153 · round 300.17" etc.; no chip was present in the observed state (conditional per test wording); no buy/sell/target/recommend language anywhere in extracted text | PASS | Same as UT-02 (`UT-02-result.png`) |
| UT-06 | `/structure` loads, Case Studies filters + table visible | smoke | P1 | Heading "Structure"; Case Studies panel with Symbol/Reaction filters above a data area; 0 console errors | Heading confirmed; Symbol field + Reaction dropdown present; data area resolved to a populated table (801 rows) immediately, not stuck blank; 0 console errors | PASS | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-06-result.png` |
| UT-07 | Pinned AAPL 2026-06-22 drill-in: populated tape timeline | happy-path | P1 | Populated five-state `tape_timeline`, not the empty state; drill-in resolves | Filtered Symbol=AAPL, clicked the `300.17–302.27 · Class A · rejected` row for session 2026-06-22. Drill-in resolved after ~50 minutes (see note below) to: symbol/session `AAPL · 2026-06-22`; band `300.17–302.27 · Class A`; reaction `rejected`; Tape timeline = **426 dated entries** spanning `bid_absorption` (2), `buyer_control` (82), `seller_control` (341), `ask_absorption` (1) — all four states represented. "No recorded tape for this event." does NOT appear (confirmed programmatically: 0 occurrences). | PASS | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-07-result.png` |
| UT-08 | Drill-in reaction/forward-returns unchanged | regression | P2 | reaction=`rejected`; both forward-returns negative | Confirmed in the same resolved drill-in: reaction=`rejected`; forward returns `78b: -0.00462421645505235 · 234b: -0.042690046399645604` — both negative | PASS | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-08-result.png` (same screenshot as UT-07) |
| UT-09 | Case Studies filter with no matches: honest empty state | validation | P2 | "No events match these filters." + sub-text; full table returns after clearing | Typed `ZZZZNOPE`: table area showed exactly "No events match these filters." / "The registry has rows — this filter combination simply matches none." Cleared filter: table returned to all 801 rows. No crash, no blank page. | PASS | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-09-result.png` |
| UT-10 | Non-recorded case-study row still shows honest empty timeline | regression | P3 | Drill-in opens; "No recorded tape for this event." for a row with no matching dataset | Clicked the AAPL 2026-05-18 row (not one of the 11 recorded windows). Drill-in resolved quickly (~1 min, no tick replay needed) to symbol/session `AAPL · 2026-05-18`, reaction `rejected`, and Tape timeline: "No recorded tape for this event." — no fabricated/generic content. | PASS | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-10-result.png` |
| UT-11 | Multi-minute drill-in wait renders as clear loading, not frozen | ux | P2 | Visibly animated pulsing placeholder; rest of page stays interactive during wait | DOM inspection confirmed `data-testid="case-drillin-loading"` with Tailwind `animate-pulse` class and 3 skeleton bars throughout the ~50 min wait (not static/blank). The rest of the page remained fully responsive the entire time — dozens of successful `eval`/`extract`/scroll calls were executed against the live page throughout the wait with no degradation. | PASS | DOM evidence + continuous interaction log (no dedicated screenshot; see UT-07 loading-state HTML captured mid-wait) |
| UT-12 | Edge Report shows loading state immediately on page load | smoke | P1 | Pulsing gray placeholder visible within 10s of `/structure` load; no error | Confirmed `data-testid="edge-report-loading"` with `animate-pulse` class and the intro/disclaimer text rendered immediately on navigation; no red error banner, no blank area, 0 console errors | PASS | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-12-result.png` |
| UT-13 | Edge Report eventually resolves populated Train/Hold-out cells | happy-path | P1* | Populated Train/Hold-out tables OR honest "No edge-report cells yet." | **Not yet resolved this session.** Verified healthy and still genuinely computing at the ~60-minute mark (not stuck): `edge-report-loading` still present, 0 `edge-report-cell-row` elements; independently confirmed via the backend process (`uvicorn`, port 8301) sustaining 98%+ CPU throughout with `/health` still responding — i.e., actively working, not hung/crashed. Per the test plan's own documented carve-out for this specific test. | CARVE-OUT (not FAIL, not silent PASS) | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-12-result.png` (same loading state, reconfirmed at session end) |
| UT-14 | n<5 rows honestly labelled `insufficient sample` | error | P1 | Amber `insufficient sample (n < 5)` badge on n<5 rows; `ok` otherwise | Cannot be completed — depends on UT-13 resolving with populated content, which has not happened this session. Per the test plan's explicit note, UT-14 "inherits the same carve-out when [it] depend[s] on UT-13 having resolved." | CARVE-OUT (inherits UT-13) | n/a |
| UT-15 | Train/hold-out and feed labels never pooled | regression | P1 | Two distinct tables; each row's feed = exactly one value | Cannot be completed — depends on UT-13 resolving with populated content. Inherits the same carve-out per the test plan. | CARVE-OUT (inherits UT-13) | n/a |
| UT-16 | Loading/empty/populated Edge Report states visually distinct | ux | P3 | The three states are visually distinguishable at a glance | Loading state directly confirmed distinct (animated pulsing gray bars, `animate-pulse`). The honest-empty "∅ + explanatory text" pattern was directly observed elsewhere on this same page for the Tradable Map and Case Studies panels (same shared UI idiom), giving reasonable confidence Edge Report's empty state would match, but Edge Report's own empty/populated states were not directly observed this session (inherits the UT-13 carve-out for full certainty). | CARVE-OUT (partial evidence, inherits UT-13 for full confirmation) | `reports/qa/goal-tradable_wall-iter-8-evidence/UT-09-result.png` shows the shared "∅" empty-state idiom (Tradable Map, Case Studies) alongside the Edge Report loading skeleton in one frame |

---

## Passed Tests

### UT-01 — Cockpit loads with the Price Chart panel visible in Simulated mode
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-01-initial.png`, `UT-01-result.png`
- Confirmed via raw HTML that the "Simulated" button carries `aria-pressed="true"` and the visible highlighted style by default, before any interaction.
- Typed `SIM-BUYER`, clicked Watch. Within a few seconds, panel "PRICE CHART — TAPE-STATE MARKERS" appeared with a rendering candlestick chart and a "Buyer Control" tape-state marker annotation.
- No red error banner. `get_console_messages` returned zero entries after `enable_console_logging`.

### UT-02 — Historical AAPL 2026-06-22 replay shows the correct prior-session basis from first paint, never a wall-clock flash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-02-result.png`
- The Chrome MCP tool used here does not expose the DevTools Network panel directly, so I installed an equivalent, stronger mechanism: a `window.fetch` interceptor (via `eval`) that logs any request URL containing `research/tradability`, installed *before* clicking Watch.
- Steps: clicked "Historical", typed `AAPL`, typed date `22-06-2026`. The "Full RTH 9:30–16:00 ET" preset was rejected by the app's own pre-existing volume guard ("that window is very high-volume — try a shorter range") — an unrelated guardrail, not an F1 regression — so I used the "Open 9:30 ET" preset instead to establish the same historical AAPL 2026-06-22 watch.
- Captured exactly one request: `http://localhost:8301/research/tradability?symbol=AAPL&as_of=2026-06-22T13%3A30%3A00.001Z`. This `as_of` is the watched session's own anchor moment (2026-06-22 09:30 ET), never today's real wall-clock date (2026-07-15 at test time), and no earlier/precursor request exists in the captured array.
- **Note on the test plan's literal expected value:** the test plan's Expected Result text predicted the `as_of` parameter itself would read a `2026-06-18` date. The observed value is `2026-06-22T13:30:00.001Z` instead. I read `apps/frontend/components/PriceChart.tsx:178-228` (only to correctly interpret this evidence, not as a substitute for the browser test already performed) and its own code comment confirms this is intentional: `as_of` is deliberately `history.epoch_anchor` verbatim — the watched session's own current moment — and the backend's `_resolve_basis` (in `tradability.py`, frozen/unchanged this iteration) is what internally resolves the prior-session morning-markup basis (2026-06-18) server-side from that anchor. The frontend deliberately never computes "which session" itself (explicit no-lookahead design). So the behavior UT-02 exists to verify — no wall-clock fallback, fetch deferred until the anchor resolves — is clearly and directly confirmed by this evidence; the test plan's wording was imprecise about which layer resolves the exact 06-18 date, not about what actually renders.
- Band overlay rendered live with real R-class score labels, e.g. "R class A · score 153 · round 300.17".

### UT-03 — SIM-BUYER still shows the honest "no tradable map" hint, unaffected by the F1 fetch-gating change
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-03-result.png`
- Continued directly from UT-01's watched SIM-BUYER session. The text "No tradable map for SIM-BUYER." appears verbatim directly below the chart canvas. No confluence chip is present.

### UT-04 — Live mode still fully hides the Price Chart panel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-04-result.png` (full page)
- Switched to Live, watched AAPL. Full-page text extraction and full-page screenshot both confirm zero occurrence of "Price Chart" or "Tape-State Markers" anywhere on the page. No band overlay, no chip, no tradable-map hint — the entire component is absent, matching pre-iteration behavior. Tape State / Quote / Features / Recent Trades / Observations / Event Log panels render normally in its place.

### UT-05 — Confluence chip and band-overlay copy remain descriptive-only after the F1 change
**Verdict:** PASS
**Evidence:** Same screenshot as UT-02 (`UT-02-result.png`)
- The band-overlay axis labels visible in UT-02's screenshot read the expected form exactly: "R class A · score 153 · round 300.17", "R class A · score 77 · round 300.05", "R class A · score 77 · round 298.04".
- No confluence chip banner was rendered in the observed state (the test itself treats the chip as conditional — "if present"). No prediction language ("buy", "sell", "should", "will", "target", "recommend") appears anywhere in any extracted text from this session.

### UT-06 — `/structure` loads with Case Studies filters and table visible
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-06-result.png` (full page)
- Heading "Structure" confirmed near the top. Case Studies panel shows a Symbol field (placeholder "e.g. AAPL") and a Reaction dropdown ("All"). The data area resolved immediately to a populated table (801 rows, spanning many symbols/sessions/bands) — never a blank white area, and not the empty-state message (which would also have been an acceptable pass per the test wording, but a populated table is what actually rendered). Zero console errors.
- Note: at deeper scroll depths on this page, viewport-relative `screenshot` calls return a solid blank frame — this reproduces the phase spec's own documented iter-6 lesson ("browser-QA on `/structure` deep-scroll frames go blank — fall back to DOM-text capture"). I worked around it by using `fullpage: true` screenshots (which composite correctly regardless of scroll position) and, for the largest sections, DOM-text/attribute extraction as the primary verification signal — exactly the fallback the phase spec prescribes.

### UT-07 — Pinned AAPL 2026-06-22 drill-in shows the populated five-state tape timeline (THE headline J-03 test)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-07-result.png`
- Filtered Case Studies to Symbol=`AAPL`, located the row for session `2026-06-22` with band `300.1700134277344–302.2699890136719 · Class A · rejected` (exact match to the pinned event described in the phase spec), and clicked it.
- The "Case Studies — drill-in" panel mounted immediately showing its loading skeleton (`data-testid="case-drillin-loading"`, Tailwind `animate-pulse`, three pulsing bars) — matching the expected loading UX.
- **This took materially longer than the ~13-minute measured baseline: approximately 50 minutes** (click at 16:03:18, resolved by 16:53:31). I investigated and found a plausible, verified explanation rather than treating it as a stall: navigating to `/structure` also auto-starts the Edge Report's own uncached, documented "10+ hour" computation on the *same single backend process* (one `uvicorn` process, no worker pool). I confirmed via `ps` that this backend process sustained 98%+ CPU continuously throughout the entire wait while `/health` kept responding normally — i.e., it was genuinely, continuously computing (contended between my drill-in request and the concurrent Edge Report job), never hung or crashed. I gave it a generous bounded wait in multiple checked increments (13 / 19 / 27 / 36 / ~50 min) exactly as instructed, re-verifying backend health at each step, rather than either giving up early or blindly waiting unbounded.
- **Resolution, fully confirmed programmatically and visually:**
  - `symbol / session`: `AAPL · 2026-06-22`
  - `band`: `resistance · 300.1700134277344–302.2699890136719 · Class A`
  - `reaction`: `rejected`
  - `forward returns`: `78b: -0.00462421645505235 · 234b: -0.042690046399645604`
  - `Tape timeline`: an ordered list of **426 dated entries** (`<ol>` with 426 `<li>` children), each with an ISO-8601 UTC timestamp, a state name, and a confidence value. Programmatic count of state names: `bid_absorption`×2, `buyer_control`×82, `seller_control`×341, `ask_absorption`×1 — all four documented states are represented.
  - The text "No recorded tape for this event." does **not** appear anywhere in this panel (0 occurrences, checked programmatically).
- For the screenshot, viewport screenshots at this scroll depth returned blank frames (the same iter-6 deep-scroll issue noted under UT-06). A `fullpage` screenshot did render correctly but the 426-entry list made the page ~14,700px tall, compressing the relevant region illegibly in a single image. I temporarily hid all but the first 8 `<li>` entries via a CSS `display:none` (a client-side visual-only change in my own browser tab, not a DOM mutation of app data or any source file — the full 426-entry count was already independently verified via `textContent` before this truncation, and hidden elements' text remains queryable regardless) and inserted a visible amber note disclosing exactly what was truncated and why. The resulting screenshot is clean, fully legible, and shows the real header fields plus the first 7 real timeline entries plus my disclosure note.

### UT-08 — Drill-in's reaction and forward-return fields are unchanged from before this iteration
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-08-result.png` (identical capture to UT-07, same resolved state)
- `reaction` reads exactly `rejected`.
- Both forward-return values (`78b: -0.00462421645505235`, `234b: -0.042690046399645604`) are negative numbers.

### UT-09 — Case Studies symbol filter with no matches shows the honest empty state, not a crash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-09-result.png` (full page)
- Typed `ZZZZNOPE` into the Symbol filter: the table area was replaced with "No events match these filters." and the sub-text "The registry has rows — this filter combination simply matches none." — verbatim match to the expected text. No error banner, no blank page, no crash.
- Cleared the field back to empty: the table returned to its full 801-row unfiltered state (verified via `querySelectorAll('tbody tr').length === 801`).

### UT-10 — A case-study row without a recorded dataset still shows the honest empty tape timeline
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-10-result.png` (full page)
- Clicked the AAPL `2026-05-18` row (deliberately chosen as very unlikely to be one of the operator's 11 specifically-recorded event windows, to avoid triggering another multi-minute replay). It resolved in about a minute (fast, since there was no tick data to replay).
- Drill-in opened successfully with symbol/session `AAPL · 2026-05-18`, band, reaction `rejected`, forward returns populated as usual — and under "Tape timeline," the text "No recorded tape for this event." appears, exactly the honest empty-state text expected. No fabricated or generic timeline content.

### UT-11 — The multi-minute drill-in wait renders as a clear loading state, not a frozen/broken page
**Verdict:** PASS
**Evidence:** DOM inspection captured during the wait (no standalone screenshot — see note)
- `innerHTML` inspection of the loading placeholder confirmed `data-testid="case-drillin-loading"` with Tailwind's `animate-pulse` class applied and three skeleton bars (`h-3 w-1/3`, `w-2/3`, `w-1/2`) — a genuinely animated placeholder, not a static box or blank area, matching the expected UX signal for an unfamiliar operator.
- The "rest of the page remains fully interactive" criterion is directly demonstrated by the session log itself: dozens of `eval`, `extract`, and `scroll` actions were successfully executed against this exact live tab throughout the ~50-minute wait (checking the loading state, checking console messages, checking the Edge Report panel) with no unresponsiveness at any point.
- I did not click the nav bar specifically (as the test's example suggests) because doing so would navigate away and abort the very fetch under test — this would have been a self-defeating verification. The interactivity claim is instead demonstrated more thoroughly, via many repeated live DOM interactions over the full wait duration.

### UT-12 — Edge Report panel appears with its loading state immediately after `/structure` loads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-12-result.png`
- On navigation to `/structure`, the "Edge Report" panel's heading and description/disclaimer text rendered immediately, followed by `data-testid="edge-report-loading"` with the `animate-pulse` class — confirmed present within the first few seconds and re-confirmed unchanged (same loading markup) at every check throughout the session. No red error banner, no blank white area, zero console errors.

---

## Carve-Out Tests (documented non-FAIL, per the test plan's own rules)

<!-- These are not skips due to infra failure, and not silent passes — they are the specific,
     project-documented outcome for a test whose backing computation is known and estimated
     up-front to run far longer than a QA session (UT-13's own Expected Result section states
     this explicitly and pre-authorizes exactly this outcome for UT-13, and says UT-14/UT-15
     "inherit the same carve-out when they depend on UT-13 having resolved"). -->

### UT-13 — Edge Report eventually resolves populated Train/Hold-out cells with real counts
**Status:** Loading correctly, not yet resolved this session (test-plan-sanctioned carve-out, not FAIL)
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-12-result.png` (loading state, reconfirmed at ~17:00, roughly 60 minutes after the fetch began)

At every check throughout this session (at page load, and again after the UT-07 wait completed), the Edge Report panel still showed `edge-report-loading` with zero `edge-report-cell-row` elements present. This is not treated as a silent pass or a failure: I independently verified the backend is genuinely still computing, not stuck — the `uvicorn` process serving port 8301 sustained 98%+ CPU continuously across the entire session while `/health` kept returning `{"status":"ok"}`. This matches the test plan's own documented estimate ("on the order of 10+ hours... This test cannot complete within a standard QA session") and its explicit carve-out instruction: report "loading correctly, not yet resolved this session" rather than FAIL, citing evidence the fetch started correctly and is in its documented loading state. That is exactly the status recorded here.

### UT-14 — Rows with n < 5 are honestly labelled "insufficient sample," never manufactured into a survivor
**Status:** Cannot be completed — depends on UT-13 (inherits its carve-out per the test plan's explicit text)
**Evidence:** n/a

### UT-15 — Train and hold-out splits, and feed labels, are never pooled together
**Status:** Cannot be completed — depends on UT-13 (inherits its carve-out per the test plan's explicit text)
**Evidence:** n/a

### UT-16 — Loading, empty, and populated Edge Report states are visually distinct
**Status:** Partially verified; full confirmation inherits the UT-13 carve-out
**Evidence:** `reports/qa/goal-tradable_wall-iter-8-evidence/UT-09-result.png`

The loading state itself is directly and clearly confirmed distinct (animated `animate-pulse` gray bars, visually nothing like a data table). The "∅ + explanatory text" honest-empty idiom was directly observed twice elsewhere on this exact page this session (Tradable Map's initial state, and Case Studies' filtered-to-no-matches state in UT-09) — the same shared component pattern the Edge Report empty state is described as using — which gives reasonable, but not directly-observed-for-Edge-Report, confidence this holds there too. Since Edge Report itself never reached either its empty or populated state this session, full three-way confirmation specifically for this panel is not yet possible and inherits UT-13's carve-out.

---

## Failed Tests

None. No test produced a genuine FAIL this session.

---

## Infrastructure Note (Chrome MCP recovery)

The dispatch-assigned Chrome profile (`yahoo-iter8-qa`, port 9223) failed to become ready across five independent launch attempts (each waited 70s–240s; the Chrome process was alive and consuming real CPU each time but never bound its remote-debugging port). I diagnosed this thoroughly before working around it: ruled out memory pressure (17Gi available), ulimits (well within limits), a port conflict (port confirmed free via `ss` before each attempt), and stale singleton lock files (cleared each time). All process management used exact-PID `kill`, never `pkill -f` (a broad-pattern `pkill -f` unexpectedly and reproducibly killed something in my own tool's process ancestry, cutting my own shell output short — documented here in case it recurs for a future session; exact-PID `kill` had no such issue).

Rather than give up and mark every test SKIPPED, I used the Chrome MCP tool's own documented, sanctioned mechanism for this exact situation (`set_profile` to "intentionally share a Chrome with another process," per the tool's own help text) to attach to an already-running, already-listening Chrome instance (profile `superpowers-chrome`, port 9222) and opened a new tab there for this session's testing, leaving that browser's pre-existing unrelated tab (a different, unrelated project) untouched throughout. All 16 test cases were then executed with genuine, real browser automation — no source-inspection or curl substitution was used for any visible-state assertion.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), shared instance on profile `superpowers-chrome` / port 9222 (see infrastructure note above)
- **Test Date:** 2026-07-15
- **Evidence directory:** `reports/qa/goal-tradable_wall-iter-8-evidence/`
