# goal-i_will_be_super_rich-iter-14 Functional Test Plan

**Phase:** goal-i_will_be_super_rich-iter-14
**Date:** 2026-06-09
**Frontend Present:** no

## Phase Goal

Close two real-data defects: J-36 (a genuine directional move stuck on perpetual `unclear`) and J-37 (a long/dense historical window times out into "very high-volume" error), by tuning the classifier to treat spread as a graded confidence factor for clearly-directional moves, selecting the SIP feed for historical fetch, and restructuring the historical fetch+replay seam to stream chunks progressively — each proven by a committed-real-data CI test that runs without live credentials.

## Test Cases

### TC-01 — J-36 gate: GME SIP real fixture resolves to seller_control at the drop

**Type:** api
**Preconditions:** 
- The committed **GME SIP** real fixture exists at `apps/backend/tests/fixtures/alpaca/GME_*_sip.json`
- The fixture covers the GME 14-05-2024 13:30–13:40 UTC drop (>10% move into LULD halt) with real SIP quotes
- The fixture is self-documented with `source: alpaca`, `feed: sip`, `note: REAL … not synthesized`

**Steps:**
1. Load the committed GME SIP fixture using `load_fixture_window()`
2. Create a `HistoricalProvider` and `TapeEngine` with the fixture data
3. Replay the fixture through the engine, advancing to the transition point of the drop
4. Query the engine's `tape_state` and `confidence_score`

**Expected outcome:** 
The tape state resolves to `seller_control` at the drop with confidence ≥ `reasonable_confidence`, with seller markers clearly present at the transition point.

**Pass criteria:** 
```
tape_state == 'seller_control' AND confidence_score >= reasonable_confidence AND 'seller' in markers
```

---

### TC-02 — J-36 mirror rally: real SIP fixture resolves to buyer_control (if captured)

**Type:** api
**Preconditions:** 
- A committed **real SIP fixture** for a mirror rally (comparable fast upward move) exists at `apps/backend/tests/fixtures/alpaca/` if it was captured with real credentials
- If not captured, the test documents why in the handoff and gracefully skips

**Steps:**
1. Load the committed mirror rally SIP fixture (if available)
2. Create a `HistoricalProvider` and `TapeEngine` with the fixture data
3. Replay the fixture through the engine to the transition point of the rally
4. Query the engine's `tape_state` and `confidence_score`

**Expected outcome:** 
The tape state resolves to `buyer_control` at the rally with confidence ≥ `reasonable_confidence`, with buyer markers clearly present.

**Pass criteria:** 
```
tape_state == 'buyer_control' AND confidence_score >= reasonable_confidence AND 'buyer' in markers
```

---

### TC-03 — J-36 negative guard: wide relative spread on weak tape still reads unclear

**Type:** api
**Preconditions:** 
- The existing J-06 / J-33 weak/mixed-tape fixtures with wide relative spreads are loaded
- The classifier's directional-override logic is implemented and config-driven

**Steps:**
1. Load a fixture with weak tape (low one-sided aggression ratio or no proportionate price impact) and a wide *relative* spread
2. Create a `HistoricalProvider` and `TapeEngine` with the fixture
3. Replay the fixture and query the engine's `tape_state`

**Expected outcome:** 
The tape state reads `unclear` or absorption (not forced to control/buyer_control/seller_control by the directional override), since the override engages only when ratio ≥ floor AND impact cutoff AND speed ≥ floor.

**Pass criteria:** 
```
tape_state in ['unclear', 'bid_absorption', 'ask_absorption']
```

---

### TC-04 — J-36 keystone: absorption gates remain exact complement of control impact condition

**Type:** api
**Preconditions:** 
- A shared boundary fixture covering both the control and absorption edge cases is loaded
- The classifier's control and absorption logic is present

**Steps:**
1. Load the shared boundary fixture
2. Replay through the engine at various window points spanning the boundary between control and absorption states
3. For each window, verify that the control condition (ratio ≥ floor AND impact cutoff AND speed ≥ floor) and the absorption condition are exact complements
4. Assert that features (spread, impact, price) are read only from the canonical feature engine (no second computation)

**Expected outcome:** 
For any window, either the control condition is true (tape_state ∈ {buyer_control, seller_control}) XOR the absorption condition is true (tape_state ∈ {bid_absorption, ask_absorption}), never both, never neither. Features are single-source.

**Pass criteria:** 
```
(control_condition XOR absorption_condition) == True for all windows
AND feature_engine_read_count == 1 per window
```

---

### TC-05 — J-36 fallback fixtures byte-identical: absolute-fallback sim fixtures preserve confidence

**Type:** artifact
**Preconditions:** 
- The absolute-fallback sim fixtures (J-01–J-09 scenarios) are regenerated with the new classifier logic
- The pinned confidence baseline from iter-13 is available for comparison

**Steps:**
1. Run `pytest tests/test_scenario.py -v` and capture the engine outputs for each scenario
2. Serialize the resulting `tape_state`, `confidence_score`, and all core features to JSON
3. Compare byte-for-byte with the baseline JSON fixture stored at `apps/backend/tests/fixtures/scenarios/` for each scenario

**Expected outcome:** 
All scenario fixtures match the baseline exactly (same tape_state, same confidence_score, same feature values).

**Pass criteria:** 
```
JSON(generated_output) == JSON(baseline_fixture) for all 5 scenarios
```

---

### TC-06 — Per-mode vendor feed: fetch_historical uses SIP, stream_live uses IEX

**Type:** api
**Preconditions:** 
- The per-mode feed config (`historical_feed='sip'`, `live_feed='iex'`) is present in `apps/backend/app/config.py`
- The adapter `apps/backend/app/providers/adapters/alpaca.py` reads the config to select the feed
- No vendor `DataFeed` enum leaks outside the adapter

**Steps:**
1. Call `adapter.fetch_historical(symbol, start_time, end_time)` with a real symbol and window
2. Verify that the internal feed selection inside the adapter is `sip` (check logs or mock the vendor SDK call)
3. Call `adapter.stream_live(symbol)` (or mock it)
4. Verify that the internal feed selection inside the adapter is `iex`
5. Inspect the adapter's public interface to confirm no `DataFeed` enum is exposed

**Expected outcome:** 
`fetch_historical` internally uses SIP, `stream_live` internally uses IEX, and the feed enum stays private to the adapter.

**Pass criteria:** 
```
'sip' in fetch_historical_logs AND 'iex' in stream_live_logs AND DataFeed not in adapter_public_api
```

---

### TC-07 — ALPACA_FEED env override still honored

**Type:** api
**Preconditions:** 
- The `ALPACA_FEED` environment variable support is preserved in the adapter
- The config-driven per-mode feed is the default

**Steps:**
1. Set `ALPACA_FEED=iex` in the environment
2. Call `adapter.fetch_historical(symbol, start_time, end_time)`
3. Verify that the feed selection is overridden to `iex` despite the config default being `sip`
4. Clear the env var
5. Call `adapter.fetch_historical()` again
6. Verify that the feed selection reverts to `sip` from config

**Expected outcome:** 
The `ALPACA_FEED` env var, when set, overrides the config default. When unset, config default is used.

**Pass criteria:** 
```
(env_var_set AND feed == override_value) OR (env_var_unset AND feed == config_value)
```

---

### TC-08 — J-37 gate: first chunk consumed before whole window is fetched

**Type:** api
**Preconditions:** 
- The committed **long/dense real fixture** exists at `apps/backend/tests/fixtures/alpaca/` (tens of thousands of events)
- The adapter exposes a chunk-by-chunk fetch (generator/iterator of `HistoricalWindow` sub-windows)
- The `HistoricalProvider` consumes chunks progressively instead of materializing the whole window before replay

**Steps:**
1. Load the committed long/dense fixture configuration (start/end epochs, expected chunk count)
2. Call `adapter.fetch_historical_chunks(symbol, start_time, end_time)` (or equivalent generator)
3. Measure the wall-clock time from initiating the fetch to consuming the **first chunk**
4. Verify that this time is within the configured backend budget (< `HISTORICAL_FETCH_BUDGET_MS`)
5. Verify that the **second+ chunks are still being fetched in the background** while replay continues

**Expected outcome:** 
The first chunk is available and replayed within budget. Subsequent chunks arrive while replay advances.

**Pass criteria:** 
```
time_to_first_chunk <= HISTORICAL_FETCH_BUDGET_MS AND background_chunks_streaming == True
```

---

### TC-09 — J-37 gate: no "very high-volume" error on advertised Full RTH path

**Type:** api
**Preconditions:** 
- The committed long/dense fixture is loaded
- The "Full RTH" quick-pick (e.g., 09:30–16:00 ET) is the selected window
- The backend bound is < the frontend `WATCH_REQUEST_TIMEOUT_MS` (typically 30 s)

**Steps:**
1. Issue a historical watch request with the "Full RTH" window for a liquid symbol
2. Capture the response status code and body
3. Verify that the response includes valid tape state and features (not a "very high-volume" error)
4. Verify that the response completes within the backend budget

**Expected outcome:** 
The request succeeds with a 200 status and valid tape state, without the "very high-volume — try a shorter range" error.

**Pass criteria:** 
```
response.status == 200 AND response.tape_state exists AND 'very high-volume' not in response AND elapsed_time <= WATCH_REQUEST_TIMEOUT_MS
```

---

### TC-10 — J-37 gate: streamed record set equals single-shot set in epoch order

**Type:** api
**Preconditions:** 
- The committed long/dense fixture is loaded
- The progressive chunk-streaming fetch is implemented
- A single-shot fetch (entire window at once) is still supported for comparison

**Steps:**
1. Fetch the long/dense window via the **progressive chunk-by-chunk** route (consuming chunks as they arrive)
2. Collect all trades and quotes from the streamed chunks in epoch order
3. Fetch the **same window via a single-shot** call (for comparison)
4. Collect all trades and quotes from the single-shot response in epoch order
5. Compare the two record sets for equality: same records, same epoch order, no fabrication/drop/reorder/dedup

**Expected outcome:** 
Both routes yield the same set of records in the same epoch order. No records are added, dropped, reordered, or duplicated.

**Pass criteria:** 
```
streamed_records == single_shot_records AND streamed_epochs == single_shot_epochs AND len(streamed_records) == len(single_shot_records)
```

---

### TC-11 — J-37 quote-before-trade ordering preserved across chunk boundary

**Type:** api
**Preconditions:** 
- The long/dense fixture contains a chunk boundary near a trade/quote pair with equal or near-equal epochs
- The `HistoricalProvider` preserves quote-before-trade ordering per chunk and across the stitch boundary

**Steps:**
1. Load the long/dense fixture with focus on the chunk boundary region
2. Identify a trade and quote pair at/near the boundary with equal or nearly-equal timestamps
3. Replay the chunks progressively through the engine
4. Verify that the quote is processed before the trade (or assert the expected ordering if different)
5. Verify that the engine's feature computation reflects the correct quote-before-trade state at the boundary

**Expected outcome:** 
Quote events are processed before trade events at the same epoch, even across the chunk-stitch boundary.

**Pass criteria:** 
```
quote.timestamp <= trade.timestamp AND quote_processed_before_trade == True
```

---

### TC-12 — J-37 determinism: progressive chunks vs. single-shot yield identical features

**Type:** api
**Preconditions:** 
- The long/dense fixture is loaded
- Both the progressive chunk-by-chunk and single-shot fetch routes are implemented
- The engine is deterministic (no randomness, seeded if needed)

**Steps:**
1. Fetch and replay the long/dense window via the **progressive chunk route**
2. Capture the engine's final `tape_state`, `confidence_score`, and all core features
3. Fetch and replay the **same window via single-shot route**
4. Capture the engine's final `tape_state`, `confidence_score`, and all core features
5. Compare the two captures for byte-for-byte equality

**Expected outcome:** 
Both routes produce identical tape state, confidence, and all feature values. Chunk boundaries do not perturb the engine.

**Pass criteria:** 
```
progressive_tape_state == single_shot_tape_state AND progressive_confidence == single_shot_confidence AND progressive_features == single_shot_features
```

---

### TC-13 — J-37 determinism: epoch anchor remains first real record across chunks

**Type:** api
**Preconditions:** 
- The long/dense fixture is loaded with its first real record's epoch well-defined
- The progressive chunk fetch is implemented

**Steps:**
1. Fetch the long/dense window via progressive chunks
2. Identify the first real trade or quote record's epoch from the streamed chunks
3. Verify that the engine's epoch anchor (canonical display time origin) is set to this first real epoch
4. Verify that the epoch anchor does not shift as subsequent chunks arrive
5. Repeat with a single-shot fetch and compare anchors

**Expected outcome:** 
The epoch anchor is the first real record's epoch in both routes and does not shift as chunks stream in.

**Pass criteria:** 
```
progressive_anchor == first_real_epoch AND single_shot_anchor == first_real_epoch AND anchor_stable == True
```

---

### TC-14 — J-37 no "very high-volume" error when first chunk loads on time

**Type:** api
**Preconditions:** 
- The long/dense fixture is loaded
- The "shorter range" backstop is triggered only when the **first chunk itself** cannot load within budget

**Steps:**
1. Mock or intercept the first-chunk fetch to complete within budget
2. Issue a historical watch request for the long/dense window
3. Verify that the response does NOT include the "very high-volume — try a shorter range" error
4. Repeat by making the first-chunk fetch exceed the budget and verify the error fires

**Expected outcome:** 
When the first chunk loads on time, no error. When the first chunk exceeds budget, the error fires.

**Pass criteria:** 
```
(first_chunk_on_time AND 'very high-volume' not in response) OR (first_chunk_timeout AND 'very high-volume' in response)
```

---

### TC-15 — Config constants: no magic numbers in engine/classifier/adapter code

**Type:** artifact
**Preconditions:** 
- The config file `apps/backend/app/config.py` is the source of truth for thresholds
- The engine, classifier, and adapter modules are inspected for hardcoded threshold literals

**Steps:**
1. Grep the engine/classifier/adapter code for numeric literals that represent thresholds (spread bounds, ratio cutoffs, speed floors, displayed-series caps, etc.)
2. For each literal found, verify that it corresponds to a `config.*` constant in `config.py`
3. Verify that the config docstring explains what each constant controls

**Expected outcome:** 
No magic numbers appear in engine/classifier/adapter code. All thresholds are config-driven with documented purpose.

**Pass criteria:** 
```
grep(engine_classifier_adapter, r'\d+\s*(?:<=|>=|<|>|==)') == [] AND all_thresholds_in_config == True
```

---

### TC-16 — Regression: all J-01–J-09 sim scenarios still pass (zero regression)

**Type:** api
**Preconditions:** 
- The five sim scenarios (buyer_control, seller_control, bid_absorption, ask_absorption, unclear_chop) are defined in `tests/test_scenario.py`
- The baseline passing count from iter-13 is 259 tests + 1 credential-gated skip

**Steps:**
1. Run `pytest tests/test_scenario.py -v` to execute all scenario tests
2. Capture the pass/fail counts
3. Run the full backend test suite (`pytest tests/ -v`) and capture all results
4. Verify that the count is ≥ (259 + count_of_new_tests) passed, with zero regressions

**Expected outcome:** 
All scenario tests pass. The full test count grows by exactly the number of new J-36/J-37 tests, with no decline in other tests.

**Pass criteria:** 
```
pytest_exit_code == 0 AND passed_count >= (259 + new_test_count) AND regressed_count == 0
```

---

### TC-17 — Regression: J-33 relative gates remain green (narrow gates on weak/mixed tape)

**Type:** api
**Preconditions:** 
- The J-33 relative-gates test suite is present (tests for honest uncertainty on genuinely weak/mixed tape)
- The baseline passing count from iter-13 includes these tests

**Steps:**
1. Run `pytest tests/test_classifier_relative.py -v` to execute the relative-gates tests
2. Capture the pass/fail counts
3. Verify that all tests pass with no change in expected behavior

**Expected outcome:** 
All J-33 relative-gates tests pass. No regression in honest-uncertainty detection on weak tape.

**Pass criteria:** 
```
pytest_exit_code == 0 AND test_classifier_relative_passed_count == baseline
```

---

### TC-18 — Regression: J-11/J-16/J-17/J-18 historical+chart tests remain green

**Type:** api
**Preconditions:** 
- The historical, aggressor-side, and chart tests (J-11/J-16/J-17/J-18) are present
- The baseline passing count from iter-13 includes these tests

**Steps:**
1. Run `pytest tests/test_historical_provider.py tests/test_aggressor_side.py tests/test_chart*.py -v`
2. Capture the pass/fail counts
3. Verify that all tests pass

**Expected outcome:** 
All historical/chart tests pass. No regression in historical replay, aggressor-side classification, or chart rendering.

**Pass criteria:** 
```
pytest_exit_code == 0 AND historical_chart_tests_passed == baseline
```

---

### TC-19 — Regression: J-28/J-29/J-34 vendor-responsiveness tests remain green

**Type:** api
**Preconditions:** 
- The vendor-responsiveness and live-streaming tests (J-28/J-29/J-34) are present
- The baseline passing count from iter-13 includes these tests

**Steps:**
1. Run `pytest tests/test_vendor*.py tests/test_live*.py -v`
2. Capture the pass/fail counts
3. Verify that all tests pass

**Expected outcome:** 
All vendor-responsiveness tests pass. No regression in live streaming, feed switching, or chunked parallelization.

**Pass criteria:** 
```
pytest_exit_code == 0 AND vendor_responsiveness_tests_passed == baseline
```

---

### TC-20 — Error case: empty/anchorless window yields empty chart + honest read

**Type:** api
**Preconditions:** 
- An empty fixture (no trades, no quotes) or an anchorless fixture (no real-world epoch anchor) is available

**Steps:**
1. Load the empty or anchorless fixture
2. Create a `HistoricalProvider` and `TapeEngine` with the fixture
3. Replay and query the engine's state
4. Verify that the chart buffer is empty and the tape state is honest (e.g., `unclear` or an explicit "no data" marker)

**Expected outcome:** 
An empty chart and an honest read (not a fabricated tape state).

**Pass criteria:** 
```
chart_buffer.length == 0 AND tape_state in ['unclear', 'no_data'] AND not fabricated
```

---

### TC-21 — Error case: first chunk timeout → "shorter range" backstop

**Type:** api
**Preconditions:** 
- The "shorter range" backstop message is configured to fire when the first chunk cannot load within budget
- A mock or test fixture that simulates a slow first-chunk fetch is available

**Steps:**
1. Mock the first-chunk fetch to exceed the backend budget
2. Issue a historical watch request for a long window
3. Capture the response
4. Verify that the response includes the "very high-volume — try a shorter range" error message

**Expected outcome:** 
When the first chunk times out, the backend returns the actionable "shorter range" error.

**Pass criteria:** 
```
response.error_message == 'very high-volume — try a shorter range' OR response.status_code == 413
```

---

### TC-22 — Error case: genuinely illiquid/mixed real tape reads unclear/absorption

**Type:** api
**Preconditions:** 
- A real fixture with weak evidence (low one-sided ratio OR no proportionate price impact) is available
- The directional override is implemented and does NOT force a control call on weak evidence

**Steps:**
1. Load a weak/mixed real fixture
2. Create a `HistoricalProvider` and `TapeEngine` with the fixture
3. Replay and query the engine's `tape_state`
4. Verify that the state is NOT forced to control despite any wide spread

**Expected outcome:** 
The tape state reads `unclear` or absorption (honest uncertainty), not control.

**Pass criteria:** 
```
tape_state in ['unclear', 'bid_absorption', 'ask_absorption'] AND confidence_score_reflects_uncertainty
```

---

## Summary

**Total test cases:** 22
**API tests:** 20
**Artifact checks:** 2

All test cases are derived from the spec's DEFINITION OF DONE, TESTING REQUIREMENTS, and explicit failure-path guidance (anti-goal #20: no synthetic stand-ins, real-data fixtures required, tests must fail loudly until present).
