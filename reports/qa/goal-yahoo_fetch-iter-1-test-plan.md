# goal-yahoo_fetch-iter-1 Functional Test Plan

**Phase:** goal-yahoo_fetch-iter-1
**Date:** 2026-07-09
**Frontend Present:** yes

## Phase Goal

Deliver a keyless Yahoo Finance bar adapter that fetches real historical OHLCV bars without credentials, stores them through the canonical `BarStore` with `feed="yahoo"`, and returns them byte-for-byte via REST and MCP, while keeping the Alpaca path unchanged and the live/tick/search surfaces unaffected.

## Test Cases

### TC-01 — Yahoo adapter exports correct name and availability

**Type:** api
**Preconditions:** `apps/backend/app/providers/adapters/yahoo.py` is implemented and imported.

**Steps:**
1. Import `YahooAdapter` from the adapters module.
2. Instantiate the adapter: `adapter = YahooAdapter()`.
3. Assert `adapter.name == "yahoo"`.
4. Assert `adapter.is_available()` returns `True` with no credentials configured.

**Expected outcome:** The adapter correctly identifies itself and declares keyless availability.
**Pass criteria:** `adapter.name == "yahoo"` and `adapter.is_available() is True`.

---

### TC-02 — Yahoo adapter volume coercion

**Type:** api
**Preconditions:** Yahoo adapter is implemented; a mocked `yfinance` call returns bars with float volumes.

**Steps:**
1. Call `adapter.fetch_bars("AAPL", start_date, end_date, timeframe="1d")` with mocked yfinance.
2. Inspect the returned bars' `volume` field.
3. Assert all volumes are `int` type, not float.

**Expected outcome:** Volume values are coerced to integers.
**Pass criteria:** All bars have `volume` of type `int`.

---

### TC-03 — Yahoo adapter timeframe mapping for daily

**Type:** api
**Preconditions:** Yahoo adapter is implemented; yfinance library is available.

**Steps:**
1. Call `adapter.fetch_bars("AAPL", "2024-01-01", "2024-01-31", timeframe="1d")` with a mocked yfinance call.
2. Verify the mocked call was made with `yfinance` interval `"1d"`.

**Expected outcome:** Neutral timeframe `"1d"` maps correctly to yfinance `"1d"`.
**Pass criteria:** Mock shows `yfinance.download()` called with `interval="1d"`.

---

### TC-04 — Yahoo adapter tick/live/search honestly raise or return empty

**Type:** api
**Preconditions:** Yahoo adapter is instantiated.

**Steps:**
1. Call `adapter.fetch_historical()` and expect it to raise or return empty.
2. Call `adapter.stream_live()` and expect it to raise or return empty.
3. Call `adapter.search_symbols("A")` and expect it to raise or return empty.

**Expected outcome:** Non-bar methods do not fabricate data for Yahoo.
**Pass criteria:** Each method either raises or returns an empty/neutral value without data.

---

### TC-05 — Keyless fetch stores series with feed="yahoo" through BarStore

**Type:** api
**Preconditions:** `FakeAdapter` injected via `dependency_overrides` returns a known bar series; BarStore is available.

**Steps:**
1. POST to `/research/bars` with `symbol="AAPL"`, `start="2024-01-01"`, `end="2024-01-31"`, `timeframe="1d"`, `adapter_name="yahoo"`.
2. Capture the response status and body.
3. Query `GET /research/bars` to retrieve all stored series.
4. Inspect the stored series' `meta.feed` field.

**Expected outcome:** The series is stored with `feed="yahoo"` and retrieves byte-for-byte.
**Pass criteria:** Status code is 201 or 200; returned series has `meta.feed == "yahoo"`; `GET /research/bars/{id}` returns identical JSON.

---

### TC-06 — feed value sourced from adapter, not config.historical_feed

**Type:** api
**Preconditions:** Config has `historical_feed="sip"`; a Yahoo fetch completes.

**Steps:**
1. Fetch and store a Yahoo daily series.
2. Verify the stored series has `feed="yahoo"`.
3. Fetch and store an Alpaca daily series (by explicitly selecting Alpaca).
4. Verify the Alpaca series has `feed="sip"` (from `config.historical_feed`), not `"alpaca"`.

**Expected outcome:** Yahoo sources `feed` from the adapter; Alpaca sources from config (unchanged).
**Pass criteria:** Yahoo series has `feed=="yahoo"`; Alpaca series has `feed=="sip"`; no hardcoded route literals.

---

### TC-07 — Duplicate content returns 409 BarSeriesAlreadyRegistered

**Type:** api
**Preconditions:** A Yahoo series is already stored.

**Steps:**
1. Fetch the same symbol/date/timeframe again (store-first logic should detect duplicate checksum).
2. Capture the response status.

**Expected outcome:** A 409 conflict is returned without storing duplicate content.
**Pass criteria:** Status code is 409; error message mentions duplicate or already registered.

---

### TC-08 — Unservable symbol/window returns clean neutral error

**Type:** api
**Preconditions:** Yahoo adapter is configured; yfinance cannot service a request (e.g., out-of-retention intraday).

**Steps:**
1. POST to `/research/bars` with an intraday timeframe far in the past where Yahoo has no retention.
2. Capture the response status and body.

**Expected outcome:** A clean error response (422 or similar) with an explicit error message; no empty-but-present bars, no fabrication.
**Pass criteria:** Status code is 422 or 400; error message is explicit (e.g., "NoDataForWindow" or "out of retention"); response body has no bars.

---

### TC-09 — MCP bars tool returns stored Yahoo series byte-for-byte

**Type:** api
**Preconditions:** A Yahoo series is stored via REST; MCP server is running.

**Steps:**
1. Fetch a series via `GET /research/bars/{id}`.
2. Call the MCP `bars` tool with the same series ID.
3. Compare the JSON outputs.

**Expected outcome:** MCP proxy returns byte-for-byte identical data.
**Pass criteria:** `json.dumps(rest_result, sort_keys=True) == json.dumps(mcp_result, sort_keys=True)`.

---

### TC-10 — Bar-fetch path defaults to Yahoo; Alpaca stays opt-in

**Type:** api
**Preconditions:** No adapter override in test; `get_market_adapter` is the default resolver.

**Steps:**
1. POST to `/research/bars` with no explicit `adapter_name` parameter.
2. Verify the adapter used is Yahoo (by checking `feed=="yahoo"` in the stored series).
3. POST again with explicit `adapter_name="alpaca"`.
4. Verify the adapter used is Alpaca (by checking `feed=="sip"`).

**Expected outcome:** Yahoo is the default for bar fetch; Alpaca is opt-in.
**Pass criteria:** Default fetch produces `feed=="yahoo"`; explicit Alpaca selection produces `feed=="sip"`.

---

### TC-11 — Live/tick/search paths unchanged (get_adapter not modified)

**Type:** api
**Preconditions:** Backend is running; `get_adapter()` is the live-path accessor.

**Steps:**
1. Call the endpoint that uses `get_adapter()` for live data (e.g., `/meta/clock` or `/live/quote`).
2. Verify it still uses the original adapter (Alpaca or simulated), not Yahoo.

**Expected outcome:** Live paths are unaffected by the vendor selector.
**Pass criteria:** Live/tick/search endpoints continue to work with their original adapter chain.

---

### TC-12 — GET /research/bars unchanged for existing Alpaca data

**Type:** api
**Preconditions:** Pre-existing Alpaca bar series are stored in the database from prior iterations.

**Steps:**
1. Query `GET /research/bars` with no filters.
2. Verify all pre-existing Alpaca series are present with unchanged structure.
3. Confirm no additional fields or mutations to the response shape.

**Expected outcome:** The no-param `GET /research/bars` call is byte-identical to before (additive filter only).
**Pass criteria:** Response includes all existing series; no renamed fields; no deleted properties.

---

### TC-13 — Browser J-06 regression: Cockpit renders unbroken after backend change

**Type:** browser
**Preconditions:** Frontend is running; backend change is deployed.

**Steps:**
1. Navigate to `http://localhost:3000/` (Cockpit).
2. Verify the page loads without errors.
3. Verify the live panel, tape display, and controls are rendered and interactive.
4. Take a screenshot.

**Expected outcome:** The Cockpit page renders exactly as before; no layout breaks, no missing elements.
**Pass criteria:** Page loads with 200 status; all key UI elements are visible and positioned correctly.

---

### TC-14 — Browser J-06 regression: Structure page renders unbroken

**Type:** browser
**Preconditions:** Frontend is running; backend change is deployed.

**Steps:**
1. Navigate to `http://localhost:3000/structure`.
2. Verify the page loads without errors.
3. Verify the chart canvas, existing level annotations, and any pre-loaded structure data are rendered.
4. Take a screenshot.

**Expected outcome:** The Structure page renders exactly as before; no regression in existing display.
**Pass criteria:** Page loads with 200 status; chart and zones render; no JavaScript errors in console.

---

### TC-15 — Browser J-06 regression: Journal page renders unbroken

**Type:** browser
**Preconditions:** Frontend is running; at least one journal entry exists.

**Steps:**
1. Navigate to `http://localhost:3000/journal`.
2. Verify the journal list loads and displays entries.
3. Click on an entry to view its detail page.
4. Take a screenshot of both list and detail pages.

**Expected outcome:** Journal list and detail pages render without regression.
**Pass criteria:** Both pages load; entries are clickable; no layout breaks.

---

### TC-16 — Browser J-06 regression: Performance page renders unbroken

**Type:** browser
**Preconditions:** Frontend is running; backtest/performance data is available.

**Steps:**
1. Navigate to `http://localhost:3000/performance`.
2. Verify the performance dashboard loads and displays data/charts.
3. Take a screenshot.

**Expected outcome:** The page renders exactly as before.
**Pass criteria:** Dashboard loads; charts are visible; no missing sections.

---

### TC-17 — Committed Yahoo fixture proves store/read with no network

**Type:** artifact
**Preconditions:** A committed fixture file exists at `apps/backend/tests/fixtures/bars/yahoo_fixture.json` (or similar).

**Steps:**
1. Read the fixture file.
2. Verify it contains valid bar data with `feed="yahoo"` and a valid SHA256 checksum.
3. Verify the fixture is used by a fixture-based unit test that does NOT call yfinance.

**Expected outcome:** The fixture is a valid, committed, deterministic prove of the store/read path.
**Pass criteria:** Fixture file exists; contains bars with `feed="yahoo"`; test using it does not mock or call yfinance.

---

### TC-18 — yfinance pinned in requirements.txt with confined-to-adapter comment

**Type:** artifact
**Preconditions:** `apps/backend/requirements.txt` is present.

**Steps:**
1. Read `apps/backend/requirements.txt`.
2. Search for the line `yfinance==<version>`.
3. Verify it includes a comment like "# Confined to app/providers/adapters/yahoo.py".

**Expected outcome:** The dependency is pinned and clearly marked as confined.
**Pass criteria:** Line exists with exact version pin and confinement comment.

---

### TC-19 — yfinance added to install-security-policy allowlist

**Type:** artifact
**Preconditions:** `config/install-security-policy.json` is present.

**Steps:**
1. Read `config/install-security-policy.json`.
2. Parse the JSON and inspect the `python.allowlist` array.
3. Verify `"yfinance"` is present in the list.

**Expected outcome:** yfinance is explicitly allowlisted for supply-chain gate.
**Pass criteria:** `"yfinance"` appears in `python.allowlist` array.

---

### TC-20 — config_fingerprint unchanged (remains 4d665603569b9dbf)

**Type:** artifact
**Preconditions:** `apps/backend/app/config.py` is present; the iteration has completed.

**Steps:**
1. Compute the config fingerprint (SHA256 of key config fields).
2. Verify it matches the frozen value `4d665603569b9dbf`.

**Expected outcome:** Configuration is unchanged; frozen foundation is preserved.
**Pass criteria:** Computed fingerprint == `4d665603569b9dbf`.

---

### TC-21 — Full backend test suite passes

**Type:** api
**Preconditions:** All tests are executable; no test files are deleted or weakened.

**Steps:**
1. Run `cd apps/backend && .venv/bin/python -m pytest tests/ -v`.
2. Capture exit code and test counts.

**Expected outcome:** All tests pass (or expected skips remain skipped).
**Pass criteria:** Exit code 0; no test deleted or assertion weakened; count >= prior baseline (1146+ in iter-0).

---

### TC-22 — Engine equivalence test proves byte-identical default output

**Type:** api
**Preconditions:** Engine equivalence test is defined and executable.

**Steps:**
1. Run the equivalence test that compares engine state/confidence/features between prior and current.
2. Verify all assertions pass.

**Expected outcome:** Engine output is byte-identical for the `default` profile.
**Pass criteria:** Test passes; no state/confidence/feature divergence.

---

## Summary

**Total test cases:** 22
**API tests:** 14 (TC-01 to TC-12, TC-21, TC-22)
**Browser tests:** 4 (TC-13 to TC-16)
**Artifact checks:** 4 (TC-17 to TC-20)

All test cases verify acceptance criteria from the phase spec (DEFINITION OF DONE) and TESTING REQUIREMENTS. Browser tests focus on J-06 regression (existing surfaces remain unbroken). API tests verify the keyless Yahoo adapter, bar-vendor selector, feed sourcing, store/read, and unchanged live paths. Artifact tests confirm pinned dependencies, allowlist entry, config fingerprint, and committed fixture.
