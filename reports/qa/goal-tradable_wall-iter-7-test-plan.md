# Goal Iteration 7 — Cockpit Confluence Functional Test Plan

**Phase:** goal-tradable_wall-iter-7
**Date:** 2026-07-15
**Frontend Present:** yes

## Phase Goal

Pure-frontend iteration: overlay the watched symbol's tradable bands (from `/research/tradability`) on the cockpit `PriceChart` (sim/historical modes only; live stays hidden), and show a descriptive confluence chip when the last price is inside a band AND the current tape state matches the config-owned rejection/breakthrough mapping (read from `/research/strategies`). Zero client recomputation — all values read verbatim from owning endpoints.

## Test Cases

### TC-01 — Band overlay visible on cockpit chart with real symbol

**Type:** browser
**Preconditions:** Backend running; frontend running; a real symbol (e.g. AAPL) with stored bars loaded in historical mode.

**Steps:**
1. Navigate to the cockpit `/` route.
2. Select a real symbol with bars (e.g. `AAPL`) in the watch dropdown.
3. Switch to historical mode (date-picker).
4. Observe the `PriceChart` component rendering candles + tape-state markers.

**Expected outcome:** Solid price lines are drawn on the chart for each served tradable band (one line per band edge), colored rose (resistance) or emerald (support), positioned beside the existing tape-state markers.

**Pass criteria:** At least one band overlay line is visible on the chart; the line is solid (not dashed) and uses the correct color per side; the band is drawn at the price level matching the served `price_low`/`price_high` from `GET /research/tradability`.

---

### TC-02 — Confluence chip appears when price inside band AND tape state matches mapping

**Type:** browser
**Preconditions:** TC-01 conditions met; symbol with populated bands and recorded tape timeline available (AAPL with historical 2026-06-22 tape state data).

**Steps:**
1. Continue in historical mode on AAPL over a session with a band-touch event.
2. Navigate the chart timeline to a moment where the last price bar's close is inside a served band.
3. Observe the current tape state (from the tape-state markers or the passed `tapeState` prop).
4. Identify the band's side (`resistance` → short direction, `support` → long direction).
5. Look for the confluence chip in the chart panel.

**Expected outcome:** A descriptive chip appears near the band/price intersection, displaying the band side, price range, class, and the current tape state. Copy is descriptive (e.g., "Inside R-band 300.4–302.1 (class A) · tape: ask_absorption · measured history: edge report").

**Pass criteria:** Chip is visible; copy states band side/range/class + current tape state + citation to edge report; no imperative/predictive language in the copy; chip copy passes the source-literal lint test (no banned patterns from `_IMPERATIVE_PATTERNS` / `_PREDICTION_PATTERNS`).

---

### TC-03 — Confluence chip absent when price outside all bands

**Type:** browser
**Preconditions:** TC-01 conditions met; symbol with bands in a time window where price moves outside all band ranges.

**Steps:**
1. Navigate the chart timeline to a moment where the last price bar's close is NOT inside any served band.
2. Observe the chart.

**Expected outcome:** The band overlay lines remain visible, but the confluence chip is absent.

**Pass criteria:** No chip is rendered when price is outside every band.

---

### TC-04 — Confluence chip absent when tape state is unclear or unmapped

**Type:** browser
**Preconditions:** TC-01 conditions met; a tape state transition moment where the state becomes `unclear` or is not present in the served `/research/strategies` rejection/breakthrough mapping.

**Steps:**
1. Navigate the chart timeline to a moment where the tape state is `unclear` (no marker present for a mapped state).
2. Observe the chart (price may or may not be inside a band).

**Expected outcome:** The band overlay remains visible, but the confluence chip is absent.

**Pass criteria:** Chip is not rendered when the current tape state is `unclear` or unmapped (not in the served mapping).

---

### TC-05 — SIM ticker shows honest empty state, no fabricated bands

**Type:** browser
**Preconditions:** Frontend and backend running; a SIM ticker (e.g. `SIM-BUYER`) available in the watch dropdown.

**Steps:**
1. Navigate to the cockpit `/` route.
2. Select a SIM ticker (e.g. `SIM-BUYER`) from the watch dropdown.
3. Switch to historical mode.
4. Observe the `PriceChart` component.

**Expected outcome:** The chart renders with candles and tape-state markers. An explicit "no tradable map" empty state message is displayed (no band overlay lines, no chip). No fabricated bands are drawn.

**Pass criteria:** Chart and markers render; an honest empty state or message appears (e.g., via the `EmptyHint` component); zero band lines are drawn; chip is absent.

---

### TC-06 — Live mode unchanged (chart and overlay fully hidden)

**Type:** browser
**Preconditions:** Frontend and backend running; a real symbol available.

**Steps:**
1. Navigate to the cockpit `/` route.
2. Select a real symbol (e.g. `AAPL`).
3. Switch to live mode (toggle or nav).
4. Observe the cockpit layout.

**Expected outcome:** The `PriceChart` component and all its children (candles, markers, band overlay, chip) are unmounted/hidden. The rest of the cockpit layout (tape state summary, order panel, etc.) remains visible and unchanged.

**Pass criteria:** No price chart is rendered in live mode; no band overlay lines or chip are visible; the existing live-mode gating condition (`mode === "sim" || mode === "historical"`) keeps the chart hidden.

---

### TC-07 — Mapping-driven confirmation: changing served mapping changes chip visibility

**Type:** api
**Preconditions:** Backend running; frontend running with a real symbol in historical mode, price inside a band, and a tape state currently NOT matching the served rejection/breakthrough mapping.

**Steps:**
1. Call `GET /research/strategies` and record the current `structure_tape_map` entry's `rejection_states` and `breakthrough_states`.
2. Observe the cockpit chart — the chip is absent.
3. Update the configuration to change the rejection/breakthrough mapping (e.g., manually inject a different `structure_tape_map` entry or mock the endpoint response).
4. Refresh the cockpit or trigger a re-fetch of strategies.
5. Observe the chart again.

**Expected outcome:** If the tape state now matches the new served mapping (price still inside band), the chip appears. The chip's visibility is driven by the served endpoint, not hardcoded.

**Pass criteria:** Changing the served `/research/strategies` mapping changes chip visibility; no tape-state confirmation vocabulary (`bid_absorption`, `ask_absorption`, `buyer_control`, `seller_control`) is hardcoded in the component's confirmation-matching logic (source-grep confirms no hardcoded literals used in the matching branch, outside the pre-existing `MARKER_COLORS`/`STATE_LABELS` cosmetics).

---

### TC-08 — Morning-markup / no-lookahead: cockpit bands are as-of prior session close

**Type:** api
**Preconditions:** Backend running; frontend running; a symbol with bars spanning multiple sessions; the frontmost bar is from an incomplete/forming session.

**Steps:**
1. Instrument the `PriceChart` component or the frontend network request to inspect the `as_of` parameter passed to `fetchTradability(symbol, as_of)`.
2. Record the current wall-clock time or a time within the current forming session.
3. Call `fetchTradability` (or observe the component fetch).
4. Inspect the passed `as_of` value.
5. Verify that the backend's `_resolve_basis` resolves it to the prior completed session's close.
6. Confirm the rendered bands match that prior-session-close basis (no newer bars influenced the band computation).

**Expected outcome:** The `as_of` parameter is the current wall-clock time (or close to it), verbatim; the backend resolves it to the prior completed session's close via the existing `_resolve_basis` logic; no forming-bar band is computed or rendered.

**Pass criteria:** The frontend passes `as_of` as current time; the served bands are consistent with bars through the prior session close; no forming-bar data enters the overlay or chip.

---

### TC-09 — Regression: J-05 `/structure` map still defaults correctly

**Type:** browser
**Preconditions:** Frontend and backend running; AAPL with 2026-06-22 bars available.

**Steps:**
1. Navigate to `/structure`.
2. Confirm the default view shows the Tradable Map (≤10 bands, not 1,800 raw levels).
3. Click the "raw levels" toggle (if present) and confirm it restores the all-levels view.
4. Observe the map table and chart rendering.

**Expected outcome:** `/structure` defaults to the Tradable Map; the chart shows ≤10 band overlays; the AAPL 2026-06-22 map includes the ~300–302 resistance band in the top 2 by quality score; clicking the toggle switches to the raw 1,800-level view (regression check).

**Pass criteria:** `/structure` Tradable Map view is unchanged from J-05; the raw levels toggle works; the quality scoring and band selection are stable.

---

### TC-10 — Regression: navigation unchanged (no new nav entry)

**Type:** browser
**Preconditions:** Frontend running.

**Steps:**
1. Inspect the top navigation bar or nav menu.
2. Count and list all nav entries.

**Expected outcome:** The nav entries are: Cockpit `/`, Journal `/journal`, Studies `/studies`, Performance `/performance`, Structure `/structure`. No new nav entry is added; the nav is frozen for Era 5B.

**Pass criteria:** No new page or nav entry is present; the navigation structure is unchanged.

---

### TC-11 — Unit/integration: chip mapping reads served rejection/breakthrough states

**Type:** artifact
**Preconditions:** Source code available; `apps/frontend/components/PriceChart.tsx` implemented.

**Steps:**
1. Search the `PriceChart.tsx` source for the confirmation-mapping logic (the section that decides whether to show the chip based on tape state).
2. Verify that the decision compares `currentTapeState` against values read from the fetched `structure_tape_map` entry's `rejection_states[direction]` and `breakthrough_states[direction]`.
3. Confirm no hardcoded literals like `"bid_absorption"`, `"ask_absorption"`, `"buyer_control"`, or `"seller_control"` are used for the matching decision (cosmetics in `MARKER_COLORS` / `STATE_LABELS` dicts are allowed; only the matching branch is checked).

**Expected outcome:** The confirmation logic reads the served mapping, never a client-hardcoded value.

**Pass criteria:** Source grep finds NO hardcoded state-name literals in the matching branch (outside pre-existing cosmetics); the mapping is read from the fetched strategies payload.

---

### TC-12 — Unit/integration: band overlay renders served bands verbatim, empty state when no bands

**Type:** artifact
**Preconditions:** Source code available; `apps/frontend/components/PriceChart.tsx` implemented.

**Steps:**
1. Search the `PriceChart.tsx` source for the band overlay rendering logic.
2. Verify that the component draws one price line per served band (no reordering, filtering, or re-scoring client-side).
3. Confirm that when the served `bands` array is empty or `no_bar_series_for_symbol` is true, an honest empty state (e.g., `EmptyHint` with "no tradable map" message) is shown, never a fabricated band.

**Expected outcome:** Bands render verbatim; empty state is explicit when no bands are served.

**Pass criteria:** Band rendering uses served `side`/`price_low`/`price_high`/`class`/`quality_score` fields without recomputation; when `bands.length === 0`, an `EmptyHint` is rendered instead of fabricated bands.

---

### TC-13 — Unit/integration: no-lookahead assertion — as_of is current time, not derived date-math

**Type:** artifact
**Preconditions:** Source code available; `apps/frontend/components/PriceChart.tsx` implemented.

**Steps:**
1. Locate the data effect that fetches tradability bands.
2. Verify the `as_of` parameter passed to `fetchTradability(ticker, as_of)`.
3. Confirm it is `new Date().toISOString()` or similar (current wall-clock time), NOT a computed/derived date representing "the prior session close."

**Expected outcome:** The frontend passes current time verbatim; the backend's `_resolve_basis` owns the session-close resolution (existing pattern from `/structure`'s own Load flow).

**Pass criteria:** `as_of` in the fetch call is `new Date().toISOString()` or equivalent; no client-side date-math for session resolution; the frontend trusts the backend's existing `_resolve_basis` logic.

---

### TC-14 — Full regression: backend suite passes, config_fingerprint unchanged

**Type:** api
**Preconditions:** Full environment set up; test command configured in `.claude/project-template.md`.

**Steps:**
1. Run the backend test suite: `python -m pytest apps/backend/tests/ -xvs` (or equivalent per project-template.md).
2. Capture the exit code and the pass/fail summary.
3. Verify `config_fingerprint` in `apps/backend/app/config.py` is still `4d665603569b9dbf`.
4. Run: `git diff --name-only -- apps/backend/` and confirm it is EMPTY (no backend file changed).

**Expected outcome:** All tests pass; config_fingerprint is unchanged; no backend file is modified.

**Pass criteria:** Test exit code = 0; `config_fingerprint` = `4d665603569b9dbf`; `git diff --name-only -- apps/backend/` returns nothing.

---

### TC-15 — Frontend TypeScript type safety

**Type:** api
**Preconditions:** Frontend code written; TypeScript configured.

**Steps:**
1. Run TypeScript type check: `npx tsc --noEmit -p tsconfig.json` (or equivalent from project-template.md).
2. Capture the exit code.

**Expected outcome:** No type errors.

**Pass criteria:** `tsc` exit code = 0.

---

### TC-16 — Copy discipline: chip copy passes lint

**Type:** api
**Preconditions:** Backend test suite configured; chip copy written in `PriceChart.tsx`.

**Steps:**
1. Run the copy-discipline lint test: `python -m pytest apps/backend/tests/test_copy_discipline.py::test_lint_frontend_source_literals_are_clean -xvs`.
2. Capture the exit code.

**Expected outcome:** The test passes; no banned imperative/predictive patterns in the chip copy.

**Pass criteria:** Test exit code = 0.

---

### TC-17 — Operator-gated: credentialed AAPL 2026-06-22 replay (honest-blocked if keys absent)

**Type:** browser
**Preconditions:** Alpaca credentials configured in environment (J-03's credentialed recording is available); AAPL 2026-06-22 tick-data exists; backend and frontend running.

**Steps:**
1. Verify Alpaca credentials are configured (check env variable or attempt a credentialed API call).
2. If credentials are absent, skip to "Pass criteria — honest block."
3. If credentials are present:
   a. Navigate to the cockpit `/`.
   b. Select AAPL.
   c. Use the date picker to open a historical-mode view over 2026-06-22 around 09:30–15:30 (the 300-test window).
   d. Observe the price chart, band overlay, tape-state markers, and confluence chip.
4. Take a screenshot of the chart with the band overlay and chip visible during a tape-state confluence moment (price inside the 300–302 band, tape state matching the served mapping).

**Expected outcome:** If credentials are present: the band overlay is visible, the confluence chip appears at the 300-test moment with descriptive copy, and a real screenshot can be captured. If credentials are absent: the test is honestly blocked/deferred.

**Pass criteria:** **If credentials configured:** chip is present at the confluence moment with descriptive copy, and a real screenshot exists (artifact required per iter-3 lesson; never accept a handoff narration in place of evidence). **If credentials absent:** the test is marked BLOCKED/DEFERRED, not simulated.

---

## Summary

**Total test cases:** 17
- **Browser tests:** 7 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-09, TC-10, TC-17)
- **API tests:** 4 (TC-07, TC-14, TC-15, TC-16)
- **Artifact (source-code verification) tests:** 4 (TC-08, TC-11, TC-12, TC-13)
- **Regression/structural tests:** 2 (TC-09, TC-10)

**Key test coverage:**
- Band overlay rendering (live, empty state)
- Confluence chip logic (price-in-band + tape-state mapping + descriptive copy)
- Morning-markup / no-lookahead discipline
- Endpoint-driven mapping (zero client hardcoding)
- Live-mode gating (byte-identical, unchanged)
- Full regression (backend suite, config, J-05 `/structure`, nav)
- Copy discipline (no imperative/predictive language)
- Type safety
- Operator-gated credentialed case with honest blocking

---
