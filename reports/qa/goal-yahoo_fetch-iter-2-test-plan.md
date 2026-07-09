# goal-yahoo_fetch-iter-2 Functional Test Plan

**Phase:** goal-yahoo_fetch-iter-2 (J-02 — multi-timeframe Yahoo fetch with deterministic 4h resample)
**Date:** 2026-07-09
**Frontend Present:** yes

## Phase Goal

The operator can fetch every era-5 Yahoo timeframe — `1w, 1d, 4h, 1h, 5m, 1m` — as real OHLCV bars, with `4h` deterministically resampled from real `1h` bars and honestly labelled as derived, and with out-of-retention windows and Yahoo-unsupported timeframes each returning an explicit, distinct neutral error that never fabricates a bar.

## Test Cases

### TC-01 — Interval Map: Five Direct Timeframes Resolve

**Type:** api
**Preconditions:** Backend running; Yahoo adapter initialized with expanded `_INTERVAL_MAP`.

**Steps:**
1. Call `POST /research/bars` with `symbol="AAPL"`, `timeframe="1w"`, `start_date="2026-06-01"`, `end_date="2026-07-09"`.
2. Verify HTTP 200 response with non-empty bars array.
3. Repeat step 1–2 for timeframes: `1d`, `1h`, `5m`, `1m`.
4. Assert each response has `feed="yahoo"` in metadata.

**Expected outcome:** All five directly-fetched timeframes return HTTP 200 with real bars from Yahoo Finance.

**Pass criteria:** Six API calls (one per timeframe) all return HTTP 200; each response has `bars.length > 0`; each bar has `feed="yahoo"`.

---

### TC-02 — Interval Map: Unmapped Timeframe 1d is Byte-Identical to J-01

**Type:** api
**Preconditions:** J-01 fixture and J-02 implementation both available; same symbol/window as J-01 test.

**Steps:**
1. Fetch `AAPL` daily bars with the same `start_date` / `end_date` as the J-01 committed fixture.
2. Compare the response OHLCV values, bar timestamps, and feed label to the J-01 expected output.

**Expected outcome:** J-02 daily fetch is byte-identical to J-01 daily fetch (proves no regression in the mapped `1d` path).

**Pass criteria:** Response JSON matches J-01 fixture candle-for-candle (open, high, low, close, volume, timestamp, feed).

---

### TC-03 — 4h Resample: OHLC Aggregation Exact

**Type:** api
**Preconditions:** Backend running; committed `1h` fixture available at `apps/backend/tests/fixtures/yahoo/`.

**Steps:**
1. Call `POST /research/bars` with `symbol="AAPL"`, `timeframe="4h"`, using a date window that the committed `1h` fixture covers.
2. Verify HTTP 200 response.
3. Extract the first 4h candle from the response.
4. Manually compute the expected 4h candle from the committed `1h` fixture: open=first, high=max, low=min, close=last, volume=sum.
5. Assert the response 4h candle matches the manual computation exactly.

**Expected outcome:** The 4h resample computes OHLC aggregation correctly: open is the first 1h open, high is the max of four 1h highs, low is the min of four 1h lows, close is the last 1h close, volume is the sum of four 1h volumes.

**Pass criteria:** At least one full 4h bucket in the response matches the manually-computed values exactly (to the candle).

---

### TC-04 — 4h Resample: Bucket Alignment to Session Boundary

**Type:** api
**Preconditions:** Backend running; committed `1h` fixture with timestamps covering at least one US market open (09:30 ET) and close (16:00 ET).

**Steps:**
1. Call `POST /research/bars` with `symbol="AAPL"`, `timeframe="4h"`, using the fixture date window.
2. Extract the timestamps of the 4h candles.
3. Verify that each 4h bucket aligns to the session boundary (e.g., 09:30, 13:30, or the market close), not naive wall-clock modulo-4.

**Expected outcome:** 4h buckets are aligned to regular market hours (09:30 ET open boundary), not arbitrary wall-clock 4-hour intervals.

**Pass criteria:** All 4h candle timestamps align to valid market-session start times (bucket=first 1h bar's session time + 0h/4h/8h offset from open).

---

### TC-05 — 4h Resample: Partial Trailing Bucket from Completed 1h Bars Only

**Type:** api
**Preconditions:** Backend running; committed `1h` fixture with a date window that ends mid-market-day (incomplete trailing 4h bucket).

**Steps:**
1. Call `POST /research/bars` with `symbol="AAPL"`, `timeframe="4h"`, using a window ending in the middle of a trading session.
2. Extract the last (trailing) 4h candle.
3. Count the `1h` bars that actually fall into the trailing bucket's timestamp range.
4. Verify the trailing 4h candle is computed from only those completed `1h` bars (e.g., if 2 of 4 are completed, use only those 2).

**Expected outcome:** The partial trailing bucket is emitted without padding, forward-filling, or using future bars — only from completed `1h` bars within its window.

**Pass criteria:** The last 4h candle's volume equals the sum of only the `1h` bars that fall within its range (not padded or forward-filled); no bar is synthesized.

---

### TC-06 — 4h Resample: Byte-Identical Across Two Identical Requests

**Type:** api
**Preconditions:** Backend running; committed `1h` fixture available.

**Steps:**
1. Call `POST /research/bars` with `symbol="AAPL"`, `timeframe="4h"`, `start_date="2026-06-01"`, `end_date="2026-06-15"`.
2. Store the full response body (bars array + metadata).
3. Repeat the identical call with the same parameters.
4. Compare the two response bodies byte-for-byte.

**Expected outcome:** Both responses are bit-for-bit identical (deterministic resample, no wall-clock read, no unseeded state).

**Pass criteria:** Response JSON is identical in both calls (including bar order, precision, and metadata).

---

### TC-07 — Error Taxonomy: Unsupported Timeframe Returns Distinct Error

**Type:** api
**Preconditions:** Backend running; timeframe `8h`, `1mo`, or `15m` configured as valid but not in era-5 Yahoo-supported list.

**Steps:**
1. Call `POST /research/bars` with `symbol="AAPL"`, `timeframe="8h"`, `start_date="2026-06-01"`, `end_date="2026-07-09"`.
2. Capture the HTTP status code and response body detail.
3. Repeat with `timeframe="1mo"` and `timeframe="15m"`.
4. Verify the error message explicitly names the timeframe as unsupported by Yahoo.

**Expected outcome:** HTTP response with a distinct, named unsupported-timeframe error (NOT a generic empty-window 422; the detail text should say "timeframe X not served by Yahoo Finance" or equivalent).

**Pass criteria:** HTTP response status is distinct from out-of-retention errors; response `detail` mentions "unsupported" or names the timeframe; zero bars are written to the store.

---

### TC-08 — Error Taxonomy: Out-of-Retention Window Returns Distinct Error

**Type:** api
**Preconditions:** Backend running; network connectivity to Yahoo Finance; a date window beyond Yahoo's retention (e.g., `1m` bars from two years ago).

**Steps:**
1. Call `POST /research/bars` with `symbol="AAPL"`, `timeframe="1m"`, `start_date="2024-01-01"`, `end_date="2024-01-02"` (outside 1m retention).
2. Capture the HTTP status code and response body detail.
3. Verify the error message indicates "no data for that window" or "out of retention."

**Expected outcome:** HTTP response with a distinct no-data-for-window error (different status/detail from unsupported-timeframe; uses `NoDataForWindow` exception or equivalent).

**Pass criteria:** HTTP response is distinct from unsupported-timeframe error; response `detail` mentions "no data" or "window"; zero bars are written to the store.

---

### TC-09 — Error Taxonomy: Unsupported vs. Out-of-Retention are Observably Distinct

**Type:** api
**Preconditions:** Backend running; both unsupported timeframe (`8h`) and out-of-retention window (`1m` two years ago) scenarios.

**Steps:**
1. Call `POST /research/bars` with unsupported timeframe `8h` (recent window).
2. Call `POST /research/bars` with `1m` timeframe and out-of-retention date range.
3. Compare the two HTTP responses: status code, exception type (if visible in detail), and error message text.

**Expected outcome:** The two errors are observably different in at least one of: status code, exception class name, or detail message text.

**Pass criteria:** Unsupported-timeframe error and out-of-retention error have different HTTP status codes OR distinctly different `detail` text; the difference is machine-parseable (not just wording variation).

---

### TC-10 — Error Taxonomy: Network Timeout Returns VendorTimeout (504)

**Type:** api
**Preconditions:** Backend running; a way to simulate or trigger a network timeout (e.g., unreachable host, firewall block, or a mock that injects timeout).

**Steps:**
1. Call `POST /research/bars` under a network-failure condition.
2. Capture the HTTP status code and response body.
3. Verify the status is 504 and the detail mentions vendor timeout or network failure.

**Expected outcome:** HTTP 504 with `detail` referencing `VendorTimeout` or network error.

**Pass criteria:** HTTP status is 504; response indicates a vendor timeout (not generic empty-window error).

---

### TC-11 — No Fabricated Bars: Unsupported Timeframe Path

**Type:** api
**Preconditions:** Backend running; unsupported timeframe `8h`; `BarStore` monitoring or verification.

**Steps:**
1. Call `POST /research/bars` with unsupported timeframe `8h`.
2. Inspect the `BarStore` directory for any new bar series file with `feed="yahoo"`.
3. Verify no file was created or written.

**Expected outcome:** The unsupported-timeframe error is raised before any bar is stored; `BarStore` remains unchanged.

**Pass criteria:** No new bar series file is written to `apps/backend/app/research/store/` after the failed unsupported-timeframe request.

---

### TC-12 — No Fabricated Bars: Out-of-Retention Path

**Type:** api
**Preconditions:** Backend running; out-of-retention window (`1m` two years ago); `BarStore` monitoring.

**Steps:**
1. Call `POST /research/bars` with out-of-retention window.
2. Inspect the `BarStore` directory for any new bar series file with `feed="yahoo"`.
3. Verify no file was created or written.

**Expected outcome:** The out-of-retention error is returned; zero bars are stored.

**Pass criteria:** No new bar series file is written to the `BarStore` after the failed out-of-retention request.

---

### TC-13 — Browser Regression: J-01 — Real Yahoo Fetch Still Renders on /structure

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; backend running at http://localhost:8000; committed AAPL daily fixture available.

**Steps:**
1. Open http://localhost:3000/structure in Chrome.
2. Verify the Structure page loads without errors.
3. Initiate a fetch for AAPL, 1d timeframe, recent date window (via the fetch control, if available, or via MCP to /research/bars).
4. Wait for candles to render on the chart.
5. Take a screenshot of the chart with candles.
6. Inspect the chart element for the presence of candlestick data.

**Expected outcome:** The Structure page renders real candles on a Yahoo `1d` fetch (confirming J-01 regression test: daily still works).

**Pass criteria:** Chart displays at least 5 candlesticks; screenshot shows candles rendered in the chart area; no error message is visible.

---

### TC-14 — Browser Regression: J-06 — Cockpit Feed Badge Still "Simulated"

**Type:** browser
**Preconditions:** Frontend running; backend running.

**Steps:**
1. Open http://localhost:3000 (Cockpit) in Chrome.
2. Inspect the feed-badge area (usually top-right or status bar).
3. Verify the badge displays "Simulated" (not "Yahoo" or "Yahoo Finance").
4. Take a screenshot of the feed badge.

**Expected outcome:** The Cockpit feed badge remains "Simulated" (J-01/J-02 fetches do not change the cockpit's live feed).

**Pass criteria:** Badge text is "Simulated"; screenshot confirms badge label is unchanged from J-01.

---

### TC-15 — Browser Regression: Existing Surfaces Unbroken

**Type:** browser
**Preconditions:** Frontend running at http://localhost:3000; backend running.

**Steps:**
1. Navigate to each of the following routes and verify page load and basic rendering:
   - `/` (Cockpit)
   - `/journal`
   - `/studies`
   - `/performance`
   - `/structure`
2. Take a screenshot of each page.
3. Inspect for any unintended "yahoo" text or leakage outside the bar-fetch path.

**Expected outcome:** All existing pages render without visible errors; no unintended Yahoo references appear in non-bar-fetch surfaces.

**Pass criteria:** All 5 pages load successfully (HTTP 200-level status via browser); no console errors; no visible "yahoo" text outside the Structure chart/fetch area.

---

### TC-16 — Dependency Discipline: yfinance Only New Runtime Package

**Type:** artifact
**Preconditions:** Git repo with J-02 changes; `requirements.txt` and `install-security-policy.json` accessible.

**Steps:**
1. Read `apps/backend/requirements.txt` and search for `yfinance`.
2. Verify `yfinance` is pinned to a specific version (e.g., `yfinance==0.2.X`).
3. Read `config/install-security-policy.json` and verify `yfinance` is in the Python allowlist.
4. Diff J-02 vs. J-01 for `requirements.txt` and `install-security-policy.json`.
5. Verify only `yfinance` was added; no other new runtime dependency appears.

**Expected outcome:** `yfinance` is pinned and allowlisted; no other new package is added; J-01 → J-02 diff shows only `yfinance` entry.

**Pass criteria:** `yfinance` version is pinned (not dynamic); it is present in both `requirements.txt` and `install-security-policy.json`; diff shows zero other new runtime packages.

---

### TC-17 — No Regression: config_fingerprint Unchanged

**Type:** artifact
**Preconditions:** Git repo with J-02 changes; `apps/backend/app/config.py` and a way to compute `config_fingerprint` (hash-based or known value).

**Steps:**
1. Read the current `config_fingerprint` value (from config.py or via test output).
2. Verify it equals the expected J-01 fingerprint: `4d665603569b9dbf`.
3. Diff `apps/backend/app/config.py` against J-01 and verify zero changes.

**Expected outcome:** `config_fingerprint` stays `4d665603569b9dbf`; `config.py` is byte-identical to J-01.

**Pass criteria:** `config_fingerprint == "4d665603569b9dbf"`; git diff shows zero changes in `config.py`.

---

### TC-18 — No Regression: Alpaca Adapter Byte-Identical

**Type:** artifact
**Preconditions:** Git repo with J-02 changes; `apps/backend/app/providers/adapters/alpaca.py` accessible.

**Steps:**
1. Diff `apps/backend/app/providers/adapters/alpaca.py` against J-01.
2. Verify zero changes (byte-identical).

**Expected outcome:** The Alpaca adapter is untouched and remains selectable (opt-in).

**Pass criteria:** `git diff -- apps/backend/app/providers/adapters/alpaca.py` returns no output (or `0 insertions, 0 deletions`).

---

### TC-19 — No Regression: research/levels.py Byte-Identical

**Type:** artifact
**Preconditions:** Git repo with J-02 changes; `apps/backend/app/research/levels.py` accessible.

**Steps:**
1. Diff `apps/backend/app/research/levels.py` against J-01.
2. Verify zero changes (byte-identical).

**Expected outcome:** Levels computation is not altered; it remains the sole owner of S/R and confluence computation.

**Pass criteria:** `git diff -- apps/backend/app/research/levels.py` returns no output.

---

### TC-20 — No Regression: Frontend Files Untouched

**Type:** artifact
**Preconditions:** Git repo with J-02 changes; `apps/frontend/` directory accessible.

**Steps:**
1. Run: `git diff --stat -- apps/frontend/`
2. Verify output shows "0 files changed" or is empty.

**Expected outcome:** No frontend files were modified this iteration (J-05 owns the `/structure` fetch control UI).

**Pass criteria:** `git diff --stat -- apps/frontend/` returns empty or "0 files changed".

---

## Summary

**Total test cases:** 20

**By type:**
- **API tests:** 12 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12)
- **Browser tests:** 4 (TC-13, TC-14, TC-15, and live integration screenshot evidence)
- **Artifact checks:** 4 (TC-16, TC-17, TC-18, TC-19, TC-20)

**Key coverage areas:**
- ✓ All six era-5 timeframes resolve via API (five direct + 4h resample)
- ✓ 4h resample correctness (OHLC, session alignment, partial bucket, determinism)
- ✓ Error taxonomy (unsupported vs. out-of-retention vs. network timeout) distinctness
- ✓ No fabricated bars (both error paths)
- ✓ J-01 regression (daily fetch still works, renders on Structure)
- ✓ J-06 regression (Cockpit feed badge, existing surfaces unbroken)
- ✓ Dependency discipline (yfinance only)
- ✓ Frozen invariants (config_fingerprint, Alpaca adapter, levels, no frontend changes)
