# goal-structure_ui-iter-4 Functional Test Plan

**Phase:** goal-structure_ui-iter-4 (evidence-capture / hardening iteration)
**Date:** 2026-07-07
**Frontend Present:** yes

## Phase Goal

Capture independent, populated-state browser evidence that the `/structure` Comparison section renders the `structure_tape`-vs-`v1` comparison honestly, flipping J-03 from `unknown` to `passing` and clearing iter-3's standing CLOSURE-FAIL — so all four Must-have journeys are green. **No new code is expected; this iteration re-runs browser-qa and full audits after confirming services are up.**

## Test Cases

### TC-01 — Precondition: Frontend service is reachable

**Type:** api
**Preconditions:** Development environment configured; `scripts/dev.sh` executed to start services.

**Steps:**
1. Run `curl -sf http://localhost:3301 -o /dev/null -w "%{http_code}"` to check frontend health.
2. Verify the HTTP status code response.

**Expected outcome:** Frontend responds with HTTP 200 within 10 seconds of the curl request.
**Pass criteria:** Status code is `200` (exact match). Failure to reach the frontend before dispatching browser-qa is the root cause of iter-3's SKIPPED 0/26 and must be caught here.

---

### TC-02 — Precondition: Backend service is reachable

**Type:** api
**Preconditions:** Development environment configured; `scripts/dev.sh` executed to start services.

**Steps:**
1. Run `curl -sf http://localhost:8301/health -o /dev/null -w "%{http_code}"` to check backend health.
2. Verify the HTTP status code response.

**Expected outcome:** Backend `/health` endpoint responds with HTTP 200 within 10 seconds of the curl request.
**Pass criteria:** Status code is `200` (exact match). Both TC-01 and TC-02 must pass before browser-qa-agent is dispatched.

---

### TC-03 — J-03 populated: Dataset selection and backtest initiation

**Type:** browser
**Preconditions:** Both TC-01 and TC-02 pass; frontend is loaded; user is on `/structure` page; at least one dataset is registered.

**Steps:**
1. Navigate to `/structure` page.
2. In the Comparison section, locate and click the dataset selector dropdown.
3. Select a registered dataset (e.g., the reference dataset used in iter-3 testing).
4. Verify "Run comparison" button is visible and enabled.
5. Click "Run comparison" button.
6. Observe the UI poll both the `v1` and `structure_tape` backtest jobs.

**Expected outcome:** Dataset is selected; "Run comparison" button triggers polling of both backtest jobs. The UI should display "running" or similar status while jobs are in-flight.
**Pass criteria:** The dataset selector changes from empty/placeholder to the selected dataset name; the "Run comparison" button is clickable and does not error; the backtest jobs enter a polled state (expected `state` values: `queued` or `running`).

---

### TC-04 — J-03 populated: Backtests reach `done` state

**Type:** browser
**Preconditions:** TC-03 passes; both backtest jobs are polled and in-flight.

**Steps:**
1. Wait for the UI to poll both backtest jobs to completion (expected timeout: ≤120 seconds; set realistic polling interval based on app implementation).
2. Observe the status indicators for both `v1` and `structure_tape` jobs.
3. Verify both jobs have transitioned to `done` state.
4. Take screenshot of the populated Comparison section showing both backtests complete.

**Expected outcome:** Both `v1` and `structure_tape` backtests complete polling and reach `done` state. No error or timeout state observed.
**Pass criteria:** Both job status indicators show `done` (or equivalent success state); no error or timeout banners visible; the Comparison table begins to render with aggregates.

---

### TC-05 — J-03 populated: Aggregates byte-match backend

**Type:** browser
**Preconditions:** TC-04 passes; both backtests are in `done` state; Comparison section displays populated aggregates.

**Steps:**
1. Extract the displayed aggregates from the Comparison section: `n` (sample count), `net_r` (net R in points), `net_usd` (net $ PnL), `win_rate` (%), `max_drawdown_r`.
2. Retrieve the backtest result via `curl http://localhost:8301/research/backtests/<id>` for both `v1` and `structure_tape` IDs.
3. Compare the displayed values with the JSON payload's `aggregates` object for each backtest.
4. Verify exact byte-for-byte match (no rounding, no client-side reformatting that alters the underlying value).

**Expected outcome:** Displayed aggregates (n, net_r, net_usd, win_rate, max_drawdown_r) for both `v1` and `structure_tape` match the backend JSON payload exactly.
**Pass criteria:** All five aggregate fields match between the UI display and the backend API response for both strategies (10 fields total: 5 per strategy). A mismatch on any field is a FAIL.

---

### TC-06 — J-03 populated: Per-class insufficient_sample flags render verbatim

**Type:** browser
**Preconditions:** TC-04 passes; Comparison section shows per-class A/B/C breakdown table.

**Steps:**
1. Locate the per-class breakdown table showing rows for classes A, B, C.
2. For each class row, check for the `insufficient_sample` chip/flag.
3. Extract the displayed `insufficient_sample` boolean value for each class.
4. Retrieve the backtest result via `curl http://localhost:8301/research/backtests/<id>` for the `structure_tape` strategy.
5. Verify the `aggregates_by_class` array in the JSON shows the same `insufficient_sample` boolean for each class.

**Expected outcome:** The `insufficient_sample` chip/flag for each class (A/B/C) in the UI matches the backend's `aggregates_by_class[i].insufficient_sample` value.
**Pass criteria:** All three class rows (A, B, C) show the correct `insufficient_sample` state (e.g., all three are `true` for the reference dataset's `structure_tape` keyless non-survivor). UI display must not invert or fabricate the value.

---

### TC-07 — J-03 populated: Register string is verbatim from payload

**Type:** browser
**Preconditions:** TC-04 passes; Comparison section displays the register string/disclaimer.

**Steps:**
1. Locate the "register" or disclaimer text in the Comparison section (expected: "simulated — not indicative of live results" or similar, as registered in iter-3).
2. Extract the exact displayed text.
3. Retrieve the backtest result via `curl http://localhost:8301/research/backtests/<id>` for both strategies and check the `register` field in the JSON.
4. Compare the displayed register string with both backend payloads' `register` field.

**Expected outcome:** The displayed register string is byte-identical to the backend's `register` field (no rewording, no capitalization changes, no truncation).
**Pass criteria:** The register string matches the backend payload exactly. If the register appears in multiple places on the page (e.g., once per strategy), each occurrence must match its corresponding strategy's backend `register` field.

---

### TC-08 — J-03 populated: Champion pointer remains `v1`/`default`

**Type:** browser
**Preconditions:** TC-04 passes; Comparison section is visible with both strategy results.

**Steps:**
1. Locate the champion badge/indicator on the Comparison page (expected: `v1`/`default` strategy marked as champion).
2. Verify the badge still points to the `v1` strategy and the `default` profile.
3. Retrieve the current champion via `curl http://localhost:8301/research/strategies` or the champion endpoint (per blueprint).
4. Confirm the UI-displayed champion matches the backend pointer.

**Expected outcome:** The champion badge in the Comparison section shows `v1`/`default` (unchanged from iter-3). The backend champion pointer is still `v1`/`default` (no promotion occurred).
**Pass criteria:** The champion badge displays `v1`/`default` and matches the live backend champion pointer. No `set_champion_pointer` call was made during this test run (auditor will verify this via code scan).

---

### TC-09 — J-03 populated: Keyless non-survivor `structure_tape` shows honest outcome

**Type:** browser
**Preconditions:** TC-04 passes; the `structure_tape` strategy for the reference dataset has `n=0` (keyless, no trades).

**Steps:**
1. Locate the `structure_tape` strategy row or section in the Comparison table.
2. Verify the displayed `n` (sample/trade count) is `0` or "no trades (n=0)".
3. Verify all per-class A/B/C rows for `structure_tape` show `insufficient_sample=true`.
4. Verify no fabricated trade, fill, or PnL figure appears (all numeric fields should be absent, zero, or grayed out).

**Expected outcome:** The `structure_tape` strategy honestly shows its keyless non-survivor outcome: `n=0`, "no trades (n=0)" label, all per-class flags `insufficient_sample=true`, and no fabricated metrics.
**Pass criteria:** The UI displays the exact honest outcome: `n=0`, the per-class breakdown is entirely marked `insufficient_sample=true`, and no hidden or fabricated PnL/trade data appears on the page.

---

### TC-10 — J-01 re-verify: Levels & Zones chart renders with A/B/C confluence zones

**Type:** browser
**Preconditions:** Frontend is running; user is on `/structure` page; chart data is populated.

**Steps:**
1. Navigate to the Levels & Zones section on the `/structure` page.
2. Verify the price chart (lightweight-charts) is rendered and displays candlesticks/OHLC bars.
3. Verify horizontal S/R level lines are overlaid on the chart (expected: support and resistance lines at key price levels).
4. Verify the A/B/C confluence zone table below the chart is visible and populated.
5. Take screenshot of the chart and zone table.
6. Verify the empty-state overlay (if any) is NOT obscuring the chart itself (z-index issue from iter-1).

**Expected outcome:** The chart renders with visible OHLC data, S/R levels, and confluence zones. No empty-state overlay is occluding the chart canvases.
**Pass criteria:** Chart is visible and un-occluded; S/R level lines are drawn above the candlesticks; A/B/C confluence zone table is readable below the chart. Screenshot confirms no z-index occlusion (compare against iter-3 evidence for regression).

---

### TC-11 — J-02 re-verify: Registry cards display `v1` and `structure_tape` with class-scaled maps

**Type:** browser
**Preconditions:** Frontend is running; user is on `/structure` page; registry data is populated.

**Steps:**
1. Navigate to the Registry section on the `/structure` page.
2. Locate the strategy cards for `v1` and `structure_tape`.
3. Verify each card displays stop, reward, and size maps scaled by class (A/B/C).
4. Verify the `v1` card is badged as the champion ("Champion" badge or similar).
5. Verify the `structure_tape` card is NOT badged as the champion.
6. Verify each card's test ID is distinct and does not collide with other champion indicators on the page (iter-2 audit finding T2).

**Expected outcome:** Both `v1` and `structure_tape` cards are visible with class-scaled metrics; `v1` is clearly badged as champion; no duplicate or overlapping test IDs.
**Pass criteria:** Both cards render with distinct test IDs; `v1` has a champion badge; `structure_tape` does not; all three map types (stop, reward, size) are displayed for both strategies.

---

### TC-12 — J-04 regression: 5-link navigation intact and `/performance` reachable

**Type:** browser
**Preconditions:** Frontend is running; user is on any page within the app.

**Steps:**
1. Verify the persistent navigation bar/sidebar displays 5 links: Cockpit, Journal, Studies, Performance, Structure.
2. Click on the "Performance" link.
3. Verify the `/performance` page loads without error.
4. Take screenshot of the nav and `/performance` page.

**Expected outcome:** All 5 nav links are present; clicking "Performance" navigates to a valid `/performance` page with no error.
**Pass criteria:** The nav bar displays exactly 5 links; `/performance` page is reachable and renders correctly. No 404 or error state.

---

### TC-13 — J-04 regression: Backend diff stays empty and config_fingerprint matches

**Type:** api
**Preconditions:** Both TC-01 and TC-02 pass; backend service is running.

**Steps:**
1. Run `git diff --stat -- apps/backend` from the repository root.
2. Verify the output is empty (no files changed).
3. Run `curl http://localhost:8301/meta` or retrieve the config fingerprint from the backend startup logs.
4. Verify the `config_fingerprint` matches the expected value: `4d665603569b9dbf`.

**Expected outcome:** Backend code is unchanged (diff is empty); the config fingerprint recomputes to the expected value.
**Pass criteria:** `git diff --stat -- apps/backend` produces no output (empty diff); backend `/meta` or config endpoint returns `config_fingerprint: "4d665603569b9dbf"` (byte-exact match).

---

### TC-14 — Anti-goal: No champion promotion or PnL ledger write

**Type:** api
**Preconditions:** All other tests pass; backend logs and code are available for inspection.

**Steps:**
1. Review backend logs for any `set_champion_pointer` or `promote_champion` calls during the test run.
2. Check the PnL ledger via `curl http://localhost:8301/research/pnl/ledger` to confirm no new entries were written.
3. Verify the ledger's last entry timestamp is before the test run started (no writes during tests).
4. Scan the frontend code for any imperative `set_champion_pointer` or `ledger.write` calls in the UI flow.

**Expected outcome:** No champion promotion calls are logged; PnL ledger is unmodified (no new entries written during tests).
**Pass criteria:** Backend logs show zero `set_champion_pointer` calls during the test run; PnL ledger's most recent entry is timestamped before the test started; frontend code inspection reveals no ledger-write calls in the UI event handlers.

---

### TC-15 — Anti-goal: No vocabulary drift or fabricated states

**Type:** browser
**Preconditions:** All J-01–J-04 browser tests pass; full page source and copy are available.

**Steps:**
1. Search the rendered UI for forbidden vocabulary: "paper trading", "shadow trading", "annualized", "expected profit", "should", "will", "certain".
2. Verify all simulated PnL/size figures carry the visible "simulated — not indicative of live results" register.
3. Verify all error/degraded states (no datasets, backtest failed, insufficient sample, backend unreachable) are explicitly labeled (not silently hidden or fabricated as 0).

**Expected outcome:** No forbidden vocabulary appears anywhere on the rendered `/structure` page; all simulated figures are registered; all failure states are explicit and distinct.
**Pass criteria:** Full-page text search finds zero instances of forbidden vocabulary; every simulated metric is prefixed or suffixed with the register string or a warning label; no fabricated (zero or placeholder) metrics appear where data is unavailable.

---

## Summary

**Total test cases:** 15
- **API tests:** 5 (TC-01, TC-02, TC-05, TC-13, TC-14)
- **Browser tests:** 9 (TC-03, TC-04, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12)
- **Anti-goal checks:** 1 (TC-15)

**Key testing principles:**
1. **Precondition gate (TC-01, TC-02):** Both services must be confirmed reachable before any browser tests run. This is the iter-3 root-cause lesson.
2. **J-03 evidence (TC-03–TC-09):** The primary deliverable is independent, populated-state browser verification of the Comparison section.
3. **Regression check (TC-10–TC-12):** All three existing journeys (J-01, J-02, J-04) must remain green.
4. **Anti-goal compliance (TC-13–TC-15):** Zero backend mutations, no champion promotion, no vocabulary drift, honest degraded states only.

All tests are **driven from the user's perspective** (dataset selection → backtest polling → result verification), not implementation details. Every test case maps to a specific DEFINITION OF DONE item or anti-goal requirement from the phase spec.
