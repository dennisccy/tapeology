# Goal Iteration 27 Functional Test Plan

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-27  
**Date:** 2026-06-13  
**Frontend Present:** yes

## Phase Goal

Verify and capture evidence for off-hours-verifiable real-data journey legs (J-11, J-14, J-16, J-18, J-20, J-22, J-23, J-27, J-29, J-32) using historical replay, committed fixtures, and honest-failure scenarios. No new product capability; byte-identical code (unless a genuine defect surfaces and is fixed in-scope). Live-only legs (J-15, J-67 live-IEX pixels) deferred to Monday market hours.

---

## Test Cases

### TC-01 — Backend Full Suite Green (J-01–J-37 Regression)

**Type:** api  
**Preconditions:** Backend environment set up; `.env` file present; test database seeded.

**Steps:**
1. Run the full backend test suite from the project root.
2. Capture exact pass/skip/fail counts and exit code.
3. Verify the anchor suites for target journeys pass:
   - `test_historical_provider.py` (J-11)
   - `test_aggressor.py` (J-16)
   - `test_history.py` + `test_history_api.py` (J-18)
   - `test_vendor_timeout.py` + `test_vendor_responsiveness.py` (J-22/J-28)
   - `test_stream_lifecycle.py` (J-23/J-27)
   - `test_progressive_fetch.py` + `test_chunked_fetch.py` (J-29)
   - `test_speed_api.py` (J-32)
4. Verify J-36/J-37 committed real-data fixtures are included and passing.

**Expected outcome:** All tests pass with 848 passed + 1 skipped, exit code 0, no re-pins.

**Pass criteria:** `exit 0` AND exactly `848 passed / 1 skipped` AND each anchor suite is cited by name and count in the dev handoff AND no source files in `apps/backend/` have been modified.

---

### TC-02 — Credential State Probe (Prerequisite for Credentialed Historical Legs)

**Type:** api  
**Preconditions:** Backend running; environment loaded.

**Steps:**
1. Call `GET /market/clock` to probe provider credential state.
2. Alternatively, attempt a `POST /watch/{ticker}` with a known symbol (e.g., AAPL) in historical mode and observe the response.
3. Check the response for `has_credentials: true` or fallback to inspecting the error message for "provider unavailable."

**Expected outcome:** Either `has_credentials: true` (both ALPACA_API_KEY and ALPACA_API_SECRET present) or explicit "provider unavailable" response.

**Pass criteria:** The credential state is positively determined and documented in the dev handoff. If both credentials are present, proceed to TC-03–TC-09 with live credentialed replays. If only the key is present, substitute J-11/J-16/J-18/J-20/J-29/J-32 with SIP real-data fixture replays (J-36/J-37 path) and document the substitution explicitly.

---

### TC-03 — J-11 Historical Replay (Credentialed or Fixture)

**Type:** browser  
**Preconditions:** Frontend dev server running and fresh-content verified; backend running; credentials or fixtures available.

**Steps:**
1. Open the Cockpit at `/`.
2. Set source selector to "Historical" mode.
3. Enter a liquid symbol (AAPL or TSLA) in the symbol search.
4. Enter a past intraday RTH date (e.g., a recent trading day) via the `dd-MM-yyyy` date input, OR use `POST /watch/{ticker}` REST call with historical body and capture the resulting cockpit state.
5. Select a time window (e.g., 14:30–14:40 BST = 09:30–09:40 ET) using the picker.
6. Verify the cockpit panels populate with real historical values (tape state, confidence, 14 features, bid/ask/spread/last, recent-trade side).
7. Capture a screenshot showing the populated cockpit with recent-trades side column visible.

**Expected outcome:** Cockpit panels render with real historical data; recent-trades shows buy/sell sides resolved; `unknown` fraction is far lower than quote-only baseline.

**Pass criteria:** Screenshot visibly contains the recent-trades side column with resolved buy/sell sides AND the cockpit panels show non-zero populated values matching the historical replay AND `unknown` fraction is demonstrably lower than baseline.

---

### TC-04 — J-16 Historical Replay with Aggressor Detection (Credentialed or Fixture)

**Type:** browser  
**Preconditions:** Same as TC-03; backend fixture or live credentials available.

**Steps:**
1. Execute a historical replay of AAPL or TSLA over a known past RTH window (same as TC-03).
2. Verify the recent-trades list shows aggressor side (buy/sell) resolved from the vendor tape.
3. Capture a screenshot showing recent-trades with aggressor side information visible.
4. Verify via `GET /state` that the tape state reflects the correct aggressor/direction signals.

**Expected outcome:** Recent-trades display resolved aggressor sides; tape state reflects correct direction/confidence.

**Pass criteria:** Screenshot visibly shows recent-trades side column with buy/sell classification AND `GET /state` response shows consistent tape-state + confidence values.

---

### TC-05 — J-18 Historical Chart Match and History API (Credentialed or Fixture)

**Type:** browser  
**Preconditions:** Frontend and backend running; credentials or fixtures available.

**Steps:**
1. Execute a historical replay of AAPL or TSLA over a past RTH intraday window.
2. Set the candlestick chart to multiple bar sizes (e.g., 1-min, 5-min, 30-min).
3. Verify the chart candlesticks match the values returned by `GET /history?interval=<bar_size>`.
4. Verify tape-state transition markers are rendered at the correct bar positions.
5. Capture a screenshot of the chart showing markers and candlesticks.

**Expected outcome:** Chart candlesticks match the `/history` API response for each bar size; markers appear at correct transitions.

**Pass criteria:** Screenshot visibly shows candlestick chart with markers at transitions AND `GET /history?interval=<size>` response matches the chart rendering for each tested bar size.

---

### TC-06 — J-20 Historical Picker Zone Label and Quick-Picks (Credentialed or Fixture)

**Type:** browser  
**Preconditions:** Frontend and backend running; credentials or fixtures available.

**Steps:**
1. Execute a historical replay with the picker visible.
2. Verify the picker shows the local-zone label and quick-pick time presets.
3. Verify the fetched data window matches the selected local window (accounting for timezone).
4. Capture a screenshot of the picker showing zone label and quick-picks.

**Expected outcome:** Picker displays local timezone label and quick-picks; fetched window matches selected window.

**Pass criteria:** Screenshot visibly shows the picker zone label and quick-picks AND the fetched window size matches the selected window per the `dd-MM-yyyy hh:mm:ss` bounds.

---

### TC-07 — J-29 Progressive and Chunked Fetch (Credentialed or Fixture)

**Type:** browser  
**Preconditions:** Frontend and backend running; credentials or fixtures available; a large historical window is available.

**Steps:**
1. Execute a historical replay over a large intraday window (e.g., a full RTH session, 6.5+ hours).
2. Verify the busy window loads within the configured client-side timeout bound.
3. Measure the time to populate and verify it is within the bound (expected < 5s for a typical fixture).
4. Trigger a re-watch of the same window and verify it is nearly instant (near-zero fetch).
5. Capture a screenshot showing the fully populated chart and panels.

**Expected outcome:** Large window loads within the configured bound; re-watch is near-instant.

**Pass criteria:** Load time is measurably < configured bound AND re-watch latency is < 500ms AND screenshot shows fully populated chart and panels.

---

### TC-08 — J-32 Speed Control Continuity (Credentialed or Fixture)

**Type:** browser  
**Preconditions:** Frontend and backend running; credentials or fixtures available; historical replay is active.

**Steps:**
1. Start a historical replay of AAPL or TSLA.
2. Begin playback at 1× speed (real-time candlestick progression).
3. While playback is in progress, change the speed to 10× (10x real-time).
4. Verify the chart and tape-state progression continue from the current position without a re-Watch or re-fetch.
5. Capture a screenshot showing the chart at 10× speed with active markers/progression.

**Expected outcome:** Speed change applies immediately; no re-watch triggered; chart progression continues from current position.

**Pass criteria:** Chart continues animating at 10× speed from the pre-change position (no rewind to start) AND no additional `/watch` or `/history` request is issued after the speed change AND screenshot shows the chart in motion at the new speed.

---

### TC-09 — J-14 Closed-Market Honest Panel (Live Mode, Natural State)

**Type:** browser  
**Preconditions:** Frontend and backend running; market is naturally closed (Saturday 2026-06-13); no backdating required.

**Steps:**
1. Open the Cockpit at `/`.
2. Set source selector to "Live" mode (or leave the natural default).
3. Enter a symbol (e.g., AAPL) in the symbol search.
4. Observe the honest-state panel that appears because the market is closed.
5. Verify the panel displays: "market is closed" + next market open: 15-06-2026 14:30 UTC+01:00.
6. Capture a screenshot showing the closed-market honest-state panel.

**Expected outcome:** An explicit "market is closed" panel with the correct next-open time is rendered.

**Pass criteria:** Screenshot visibly contains the text "market is closed" AND the next open time "15-06-2026 14:30 UTC+01:00" is displayed AND no fabricated cockpit data is rendered (no fake live tape state).

---

### TC-10 — J-14 Unknown Symbol Honest Panel

**Type:** browser  
**Preconditions:** Frontend and backend running; credentials or fixtures available.

**Steps:**
1. Open the Cockpit at `/`.
2. Attempt to watch a non-existent or non-tradable symbol (e.g., "NOTREAL" or "INVALID").
3. Observe the honest-state panel response.
4. Verify the panel displays: "not a tradable symbol".
5. Capture a screenshot showing the unknown-symbol honest panel.

**Expected outcome:** An explicit "not a tradable symbol" panel is rendered.

**Pass criteria:** Screenshot visibly contains the text "not a tradable symbol" AND no cockpit data is rendered (no fake panels).

---

### TC-11 — J-14 Empty Window Honest Panel

**Type:** browser  
**Preconditions:** Frontend and backend running; credentials or fixtures available.

**Steps:**
1. Open the Cockpit at `/` in Historical mode.
2. Enter a valid symbol (e.g., AAPL).
3. Select a time window OUTSIDE market hours (e.g., 22:00–23:00 UTC on a weekend or a holiday) or a window with no available data.
4. Observe the honest-state panel response.
5. Verify the panel displays: "no data for that window".
6. Capture a screenshot showing the empty-window honest panel.

**Expected outcome:** An explicit "no data for that window" panel is rendered.

**Pass criteria:** Screenshot visibly contains the text "no data for that window" AND no cockpit data is rendered (no empty panels).

---

### TC-12 — J-22 Vendor Timeout Error (Backend Timeout < Frontend Client Timeout)

**Type:** browser + api  
**Preconditions:** Backend running with timeout configuration; `/watch` endpoint configured with a client-side timeout > backend timeout.

**Steps:**
1. Start a watch request that intentionally times out at the vendor-call boundary (e.g., by simulating a slow provider response).
2. Verify the backend timeout is enforced (< 30s, typical ~10s) before the frontend client timeout (~60s).
3. Observe the error response and the UI error banner.
4. Capture a screenshot showing the error banner with the timeout message.
5. Verify the error is distinct and actionable (not a generic "failed").

**Expected outcome:** Backend timeout fires first; UI displays a distinct timeout/unreachable error within the configured client-side bound.

**Pass criteria:** The error message is displayed in the UI AND the error is distinct from other failure modes AND backend timeout is enforced at the vendor-call boundary (verified via `test_vendor_timeout.py` + `test_vendor_responsiveness.py` unit tests with exact pass counts cited).

---

### TC-13 — J-23 Backend Killed Mid-Watch (Explicit Stream Failure)

**Type:** browser + api  
**Preconditions:** Frontend and backend running; backend can be killed cleanly during a watch.

**Steps:**
1. Start a live watch request on the Cockpit.
2. While the watch is in progress (stream is connecting or connected), kill the backend process (e.g., `pkill -f uvicorn`).
3. Observe the UI response: the stream-status dot and any error panels.
4. Verify the UI displays an explicit "couldn't connect to the tape stream" or similar failure message within bounds (no infinite spinner).
5. Capture a screenshot showing the error state.
6. Restart the backend.

**Expected outcome:** After backend kill, the UI surfaces an explicit, bounded failure state (not an infinite spinner or swallowed rejection).

**Pass criteria:** Screenshot visibly shows an error message indicating stream failure AND the error appears within the configured timeout (e.g., < 60s) AND no infinite loading spinner is present AND the exact behavior matches `test_stream_lifecycle.py` unit evidence.

---

### TC-14 — J-27 No-First-Event / Feeder-Failure Stream State (Explicit Honest State)

**Type:** browser + api  
**Preconditions:** Frontend and backend running; a fixture or test scenario that triggers a no-first-event condition is available.

**Steps:**
1. Start a watch request that will receive no initial tape event (feeder failure or delayed event).
2. Observe the stream-status indicator and any honest-state panels.
3. Verify the stream-status field shows one of: `stale`, `closed`, `no-data`, or an explicit error state (owned by `stream_status`).
4. Verify the state is NOT fabricated as `live` and is NOT stuck as `connecting`.
5. Capture a screenshot showing the stream-status dot and honest-state panel.

**Expected outcome:** Stream-status resolves to an explicit honest state (stale/closed/no-data/error) rather than a fabricated or indeterminate state.

**Pass criteria:** Screenshot visibly shows a stream-status value that is one of `stale`, `closed`, `no-data`, or an explicit error AND the value is NOT `live` AND NOT `connecting` AND the behavior matches `test_stream_lifecycle.py` unit evidence.

---

### TC-15 — Pre-Capture Frontend Hygiene (Fresh Content Canary)

**Type:** artifact  
**Preconditions:** Frontend dev server running; any build step has completed.

**Steps:**
1. Verify the frontend dev server is responding on `http://localhost:3000` with `curl -I http://localhost:3000`.
2. Check the HTTP response headers for cache-control and content-length (verify content is being served, not cached from a stale build).
3. Open the Cockpit in a fresh browser tab and verify the page loads and is interactive.
4. If a build was run during the pipeline, verify the served bundle is fresh by inspecting the Last-Modified or ETag header and comparing to the build time.

**Expected outcome:** Frontend dev server is live; served content is fresh (post-dates any build run).

**Pass criteria:** `curl http://localhost:3000` returns HTTP 200 AND the page loads and is interactive AND if a build was run, the served bundle ETag or Last-Modified is newer than the build timestamp.

---

### TC-16 — Byte-Identity Check (Backend Code Unchanged)

**Type:** artifact  
**Preconditions:** Git repository with clean working tree.

**Steps:**
1. Run `git status` to check for modifications in `apps/backend/`.
2. Run `git diff apps/backend/` to capture any staged or unstaged changes.

**Expected outcome:** No changes to backend source files (unless a genuine defect fix was applied and documented).

**Pass criteria:** `git diff apps/backend/` is empty (no modifications) OR any modifications are justified in the dev handoff as a minimal, config-owned, real-data defect fix that leaves J-01–J-09 sims + classifier suite green.

---

### TC-17 — Byte-Identity Check (Frontend Code Unchanged)

**Type:** artifact  
**Preconditions:** Git repository with clean working tree.

**Steps:**
1. Run `git diff apps/frontend/` to capture any staged or unstaged changes.

**Expected outcome:** No changes to frontend source files (unless a genuine defect fix was applied and documented).

**Pass criteria:** `git diff apps/frontend/` is empty (no modifications) OR any modifications are justified in the dev handoff as a minimal, config-owned UI defect fix (e.g., honest-state message not rendering) on an existing surface (error banner / failure panel / status dot), reusing backend taxonomy copy, with no new component or hardcoded copy.

---

### TC-18 — Anti-Goal Compliance: No Fabricated Data or Trading Advice

**Type:** artifact  
**Preconditions:** All honest-failure captures (TC-09 through TC-14) have been completed.

**Steps:**
1. Review each error/honest-state capture (closed-market, unknown-symbol, empty-window, timeout, stream-down, no-first-event).
2. Verify that no trades, quotes, prices, or tape-state values are synthesized in error states.
3. Verify that no chart or cockpit data is rendered when an honest-failure state is active.
4. Verify that no trading advice or P&L implication is present in any copy.

**Expected outcome:** All error states display only explicit failure messages; no fabricated data is rendered.

**Pass criteria:** Every honest-failure capture shows ONLY the error message or honest-state panel AND zero synthesized trades/quotes/prices/tape-state AND the dev handoff explicitly notes "no fabricated data in error states."

---

### TC-19 — Anti-Goal Compliance: Single-Source-of-Truth (Canonical Endpoints)

**Type:** api  
**Preconditions:** Historical replay is active (TC-03 through TC-08); backend is responding.

**Steps:**
1. Capture the chart rendering showing candlesticks at a given bar size (e.g., 5-min).
2. Call `GET /history?interval=5m` and verify the returned OHLC values match the chart rendering.
3. Capture the cockpit panels showing tape state, confidence, features, bid/ask/spread.
4. Call `GET /state`, `GET /features`, `GET /summary` and verify the rendered values match the API responses exactly (no UI-side recomputation).
5. Document the endpoint mapping in the dev handoff.

**Expected outcome:** Chart candlesticks and cockpit values are read verbatim from canonical endpoints; no UI-side recomputation.

**Pass criteria:** Chart OHLC values match `/history` response at each bar size AND cockpit tape-state/confidence/features match `/state` + `/features` responses AND no UI-side transformations are detected AND dev handoff explicitly lists the canonical endpoints read.

---

### TC-20 — Dev Handoff Completeness and Honesty Stamp

**Type:** artifact  
**Preconditions:** All test cases TC-01 through TC-19 have been executed.

**Steps:**
1. Verify the dev handoff file exists at `docs/handoffs/goal-i_will_be_super_rich_with_my_loved_ones-iter-27-dev.md`.
2. Check that the handoff includes, per test case:
   - Backend suite pass/skip/fail counts and exit code.
   - Per-leg verification result (credentialed-historical, fixture, or REST substitution).
   - Credential state (both API key + secret present, or secret missing).
   - Any deferred live legs (J-15, J-67 live-IEX pixels) with explicit gating reason and Monday 15-06-2026 14:30 UTC+01:00 market open time.
   - No vague "operator-gated" notes; every off-hours-verifiable leg is marked with concrete evidence.
3. Verify that the handoff is signed by the dev agent.

**Expected outcome:** Handoff is complete, honest, and cites concrete evidence for every in-scope leg.

**Pass criteria:** The handoff file exists AND includes exact pass/skip counts by anchor suite AND documents the credential state explicitly AND every deferred live leg is named with Monday 15-06-2026 14:30 UTC+01:00 gating time AND no "operator-gated" vague notes exist for off-hours-verifiable legs.

---

## Summary

**Total test cases:** 20  
**Browser tests:** 12 (TC-03 through TC-14)  
**API/REST tests:** 5 (TC-01, TC-02, TC-12, TC-13, TC-19)  
**Artifact checks:** 3 (TC-15, TC-16, TC-17, TC-18, TC-20)

**Scope:** Verification and evidence capture for off-hours-verifiable real-data journey legs (J-11, J-14, J-16, J-18, J-20, J-22, J-23, J-27, J-29, J-32). No new product capability; byte-identical code (or minimal config-owned defect fix if surfaced). Live legs (J-15, J-67 live-IEX pixels) deferred to Monday market hours.

**Key dependencies:**
- Credentials (ALPACA_API_KEY + ALPACA_API_SECRET) must be present for live credentialed replay, or fallback to SIP real-data fixtures.
- Frontend dev server must be fresh and live before any browser capture.
- Backend suite must pass with 848 passed / 1 skipped, exit 0.
- All honest-failure captures must show no fabricated data.
- Dev handoff must document credential state, per-leg evidence, and deferred live legs with explicit Monday gating time.
