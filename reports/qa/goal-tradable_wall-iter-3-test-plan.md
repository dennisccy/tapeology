# goal-tradable_wall-iter-3 Functional Test Plan

**Phase:** goal-tradable_wall-iter-3
**Date:** 2026-07-14
**Frontend Present:** no

## Phase Goal

Deliver the keyless event-window recording + tape-at-the-wall join substrate: a recording driver captures event-window trade/quote datasets around the top-ranked band-touch events with config-owned padding, and each recorded window's tape timeline is joined onto the case-study drill-in via the frozen TapeEngine replay, CI-verified keyless with committed fixture, credentialed recording honestly gated behind Alpaca credentials (expected blocked in this environment).

## Test Cases

### TC-01 — Event-window recording driver selects and records top-ranked events

**Type:** artifact
**Preconditions:** Recording driver script exists at `apps/backend/scripts/record_event_windows.py`; `GET /research/setups` returns a registry of scan events; the existing `record_from_source` path is functional

**Steps:**
1. Inspect `apps/backend/scripts/record_event_windows.py` to verify it enumerates top-ranked events from `GET /research/setups`
2. Verify it computes event windows with config-owned padding (touch −60 min … +90 min)
3. Verify it calls `record_from_source` to register each window as a `DatasetStore` dataset
4. Verify AAPL 2026-06-22 ~300 pinned event is always included in selection

**Expected outcome:** The driver script exists and demonstrates the recording flow: enumerate → compute windows → register via existing recorder

**Pass criteria:** Script file exists; contains calls to `compute_setups()`, window computation with config padding constants, `record_from_source()` calls, and explicit inclusion of pinned AAPL event

---

### TC-02 — Registered datasets are append-only, checksummed, feed-stamped verbatim, split-frozen

**Type:** api
**Preconditions:** At least one test dataset registered via `record_from_source` with keyless `SOURCE_REFERENCE` / committed-fixture path

**Steps:**
1. Run keyless integration test that registers a dataset via `record_from_source(historical_fetch=...)`
2. Verify dataset metadata contains: symbol, feed stamp (from adapter tier), window_start_utc, window_end_utc, checksum, split assignment
3. Attempt to re-register the same dataset (duplicate key/symbol/window); verify rejection
4. Verify dataset's feed stamp matches the adapter's advertised feed (e.g., `iex` for free tier)
5. Verify split assignment is deterministic (same input → same split)

**Expected outcome:** Dataset registry enforces immutable-data discipline: append-only, checksummed, feed-stamped verbatim from adapter tier, split frozen at registration

**Pass criteria:** 
- `test_datasets.py` or `test_datasets_api.py` includes an explicit immutability test
- Re-registration attempt raises an error (no silent overwrite)
- Feed stamp extracted from adapter matches test expectations
- Split assignment passes a deterministic seeding test

---

### TC-03 — Tape-at-the-wall join: recorded event returns non-empty five-state timeline

**Type:** api
**Preconditions:** ONE new small committed tick-fixture slice under `apps/backend/tests/fixtures/` with a recorded event window; fixture is honestly feed-stamped (`iex` or `sip`); `GET /research/setups/{id}` join logic wired into `get_setup` route

**Steps:**
1. Seed the test database with the committed fixture dataset (via keyless `FakeAdapter` or direct `historical_fetch` override)
2. Create a setups event whose touch_ts falls within the fixture dataset's window (symbol match + time containment)
3. Call `GET /research/setups/{event_id}` for that event
4. Inspect the returned `tape_timeline` field

**Expected outcome:** The drill-in returns a non-empty array of state-transition records; each record has: tape_state (one of `buyer_control`, `seller_control`, `bid_absorption`, `ask_absorption`, `unclear`), timestamp, and optionally transition-time delta

**Pass criteria:**
- Response status: 200
- `tape_timeline` is a non-empty list (length ≥ 1)
- First timeline entry matches the first state transition at or after the touch_ts
- States appear in chronological order
- No reimplemented tape logic in `setups.py` (join calls `DatasetStore.replay()` verbatim)

---

### TC-04 — Non-recorded event's tape_timeline remains empty

**Type:** api
**Preconditions:** A setups event exists whose touch_ts does NOT fall within any registered dataset window; `get_setup` join logic is in place

**Steps:**
1. Query `GET /research/setups/{event_id}` for an event with no matching recorded dataset
2. Inspect the `tape_timeline` field

**Expected outcome:** The drill-in returns an empty tape_timeline (empty list or null, per API contract)

**Pass criteria:**
- Response status: 200
- `tape_timeline` is empty (`[]` or `null`)
- No error raised; event drill-in is otherwise complete

---

### TC-05 — Join function calls frozen TapeEngine replay, never reimplements state machine

**Type:** artifact
**Preconditions:** `apps/backend/app/research/setups.py` contains a new tape-timeline join function

**Steps:**
1. Inspect `setups.py` source for the tape-timeline join function
2. Verify it calls `DatasetStore.replay(dataset_id, config)` to generate the replay stream
3. Verify it does NOT contain any conditional logic that reimplements the five tape states
4. Verify it does NOT contain any hardcoded state-transition rules
5. Add a behavioral test that mocks `DatasetStore.replay()` and asserts it is called exactly once per join

**Expected outcome:** The join function acts as a thin adapter: match event to dataset, call the frozen replay, collapse transitions, return the timeline

**Pass criteria:**
- Join function inspection finds no duplicated state-machine logic
- Behavioral test confirms `DatasetStore.replay()` is called and its output is used verbatim
- No new tape-state enum or transition rules in `setups.py`

---

### TC-06 — Frozen foundations byte-identity: TapeEngine, recorder, adapter absent from diff

**Type:** artifact
**Preconditions:** Implementation is complete; git diff is available

**Steps:**
1. Run `git diff HEAD -- apps/backend/app/engine/` (TapeEngine) and verify no changes
2. Run `git diff HEAD -- apps/backend/app/research/datasets.py` (recorder/DatasetStore) and verify no changes to existing methods
3. Run `git diff HEAD -- apps/backend/adapters/` (Alpaca adapter) and verify no changes
4. Run `git diff HEAD -- apps/backend/app/research/levels.py` and verify no changes

**Expected outcome:** Frozen files remain byte-identical; new recording/join logic is additive only

**Pass criteria:**
- All four git diff commands return empty (no lines changed)
- Any new code in datasets.py is clearly additive (new methods only, no modification of `replay()`, `record()`, or schema)

---

### TC-07 — config_fingerprint stays 4d665603569b9dbf; new constants in exclusion set

**Type:** api
**Preconditions:** `apps/backend/app/config.py` has been modified to add new constants (padding, cap, split rule) and the fingerprint exclusion set

**Steps:**
1. Call the fingerprint computation function (via existing test or direct call)
2. Verify the computed fingerprint equals `4d665603569b9dbf`
3. Inspect `config.py` fingerprint method to verify new era-5B constants are in the exclusion set
4. Verify the exclusion set follows the `tradability_*`/`setups_*` precedent (rationale comment included)

**Expected outcome:** Fingerprint remains frozen; new config additions are scoped to exclusion set

**Pass criteria:**
- Fingerprint test passes and yields `4d665603569b9dbf`
- Config file review finds new constants with comments explaining why they're excluded
- No changes to frozen constants (tape thresholds, profile defaults, etc.)

---

### TC-08 — No credential literal appears in source, fixtures, logs, test artifacts, or reports

**Type:** artifact
**Preconditions:** A grep-based test exists (new test file or added to existing test suite)

**Steps:**
1. Run a grep scan over `apps/backend/` (source), `apps/backend/tests/fixtures/` (fixtures), `.` (logs/reports) looking for regex patterns matching Alpaca credentials:
   - Patterns: `ALPACA_API_KEY`, `ALPACA_API_SECRET`, `sk_live`, `pk_live`, any 40+ hex string near "alpaca"
2. Verify the scan explicitly includes fixtures and test artifacts (unlike `test_no_execution_path.py` which excludes fixtures)
3. Record the exact grep command and output

**Expected outcome:** No credential literal is found anywhere in the scanned paths

**Pass criteria:**
- Grep test exists and is explicitly marked to scan fixtures/logs/reports
- Grep output is empty (no matches)
- Test is reproducible (uses fixed regex patterns)

---

### TC-09 — Required journeys J-01, J-02, J-07 remain green

**Type:** api
**Preconditions:** Full backend suite runs successfully; fingerprint is verified; frozen-foundation byte-identity is confirmed

**Steps:**
1. Run the full backend test suite (`pytest apps/backend/tests/` or equivalent)
2. Filter results for J-01, J-02, J-07 test markers (if present) or verify their core tests pass:
   - J-01: tradability module tests (if any) and levels byte-identity
   - J-02: setups registry tests (existing registry contract remains)
   - J-07: regression/sentinel tests (fingerprint, frozen files, foundational surfaces)
3. Verify no test is skipped or marked xfail that was passing before

**Expected outcome:** All required journeys remain passing; no regressions in frozen foundations

**Pass criteria:**
- Test suite exit code: 0 (full pass)
- All J-01/J-02/J-07 tests pass
- No new failures in levels.py, existing setups logic, or tape engine equivalence tests

---

### TC-10 — Committed fixture slice is small, feed-stamped, join path passes keyless in CI

**Type:** artifact
**Preconditions:** A new fixture file exists under `apps/backend/tests/fixtures/` with recorded event-window tick data

**Steps:**
1. Locate the new fixture file (likely named something like `event_window_*.json` or similar)
2. Verify it is a small slice (e.g., < 100 events, ~1-5 minute window)
3. Inspect the fixture JSON to confirm it contains a `feed` field with a verbatim adapter stamp (e.g., `iex`)
4. Run a test that uses this fixture to exercise the join path:
   - Register the fixture dataset via `record_from_source(historical_fetch=FakeAdapter(window=fixture))`
   - Create a matching event with touch_ts in the fixture window
   - Call `GET /research/setups/{id}` and verify tape_timeline is non-empty
5. Confirm this test passes in CI (keyless, no credentials required)

**Expected outcome:** Fixture is small, feed-stamped, and the join path is fully tested keyless

**Pass criteria:**
- Fixture file exists under `apps/backend/tests/fixtures/`
- Fixture size is ≤ 5 MB (small slice)
- Fixture JSON contains a `feed` field with a non-null value
- Join-path test exists and passes without credentials
- No test skip or xfail for the join-path test

---

### TC-11 — Integration test: credentialed recording skips honestly when keys are absent

**Type:** api
**Preconditions:** A new `@pytest.mark.integration` test exists (likely in a new file like `test_credentialed_recording.py`); environment has no Alpaca credentials set (`ALPACA_API_KEY`, `ALPACA_API_SECRET`, `TAPEOLOGY_LIVE_INTEGRATION` all unset)

**Steps:**
1. Run the integration test suite with pytest markers: `pytest -m integration apps/backend/tests/`
2. Inspect the test's logic to verify it:
   - Checks if `TAPEOLOGY_LIVE_INTEGRATION=1` is set
   - Calls `adapter.is_available()` to verify Alpaca adapter readiness
   - If unavailable, calls `pytest.skip()` with a clear reason message
3. Verify the test produces a SKIPPED result (not a FAIL or PASS)
4. Inspect the skip message to confirm it is honest and descriptive (e.g., "Alpaca credentials not configured")

**Expected outcome:** Integration test runs, detects missing credentials, and skips with an honest reason

**Pass criteria:**
- Integration test file exists and uses `@pytest.mark.integration`
- Test output shows "SKIPPED" (1 skipped test)
- Skip message clearly states why (credentials absent, keys not found, etc.)
- Test does NOT fabricate credentials or use fixtures as a substitute
- No credential literal in the skip message or test source

---

### TC-12 — Error case: empty recording window raises EmptyWindowError

**Type:** api
**Preconditions:** Recording driver is available; event window exists with no tick data in it

**Steps:**
1. Create a time window (e.g., touch_ts ± 2 hours) that contains no tick events in any source
2. Attempt to record this window via `record_from_source(symbol, start, end, historical_fetch=...)`
3. Inspect the exception raised

**Expected outcome:** The existing `EmptyWindowError` is raised; no silent dataset creation or default data injection

**Pass criteria:**
- Exception type: `EmptyWindowError`
- Exception message is clear (e.g., "No events in window [start, end]")
- No dataset is registered for an empty window

---

### TC-13 — Error case: missing credentials on historical source returns 422 (never fabricated)

**Type:** api
**Preconditions:** Recording driver script is invoked without Alpaca credentials in environment; keyless `SOURCE_REFERENCE` is disabled in this test

**Steps:**
1. Invoke the recording driver script with `ALPACA_API_KEY` explicitly unset
2. Attempt to record a window that would require credentialed Alpaca fetch
3. Inspect the result

**Expected outcome:** The driver records the attempt, detects `adapter.is_available() == False`, and reports the event as "blocked" rather than completing the recording

**Pass criteria:**
- Driver's log or return output includes "blocked" or "skipped" for that event
- No fabricated tick data in any dataset
- The route's 422 response (adapter unavailable) is the underlying signal
- Dev handoff mentions the blocked state

---

### TC-14 — Error case: unknown setup_id returns 404

**Type:** api
**Preconditions:** `GET /research/setups/{id}` endpoint exists

**Steps:**
1. Call `GET /research/setups/nonexistent-id`
2. Inspect the HTTP response

**Expected outcome:** HTTP 404 Not Found; no fabricated event drill-in

**Pass criteria:**
- Response status: 404
- Error message indicates the setup ID was not found
- No default/empty event is returned

---

### TC-15 — Error case: malformed padding or selection config is rejected at config load

**Type:** artifact
**Preconditions:** Config constants are defined in `apps/backend/app/config.py` with type hints and validation

**Steps:**
1. Inspect config.py for the new constants: recording window padding, event-selection cap, split-rule ratio
2. Verify each has a type hint and a valid default value
3. Create a test that loads config with an invalid value (e.g., negative padding, cap > total events)
4. Verify the config load fails with a clear error message

**Expected outcome:** Malformed config is rejected before the app starts or during config validation

**Pass criteria:**
- Config constants are defined with type hints
- Validation test exists and fails on invalid inputs
- Error message is clear (e.g., "padding must be positive")
- App startup fails gracefully if config is corrupt

---

### TC-16 — Dev handoff explicitly states whether credentialed recording ran or was blocked

**Type:** artifact
**Preconditions:** `docs/handoffs/goal-tradable_wall-iter-3-dev.md` exists

**Steps:**
1. Read the dev handoff file
2. Locate the section describing the credentialed recording outcome
3. Verify it explicitly states:
   - Either "Credentialed recording completed: ≥10 datasets recorded across ≥5 symbols" (if keys were set)
   - Or "Credentialed recording blocked: Alpaca credentials not configured in environment" (if keys were absent)
4. Verify the pinned AAPL 06-22 event is mentioned by name (not just "one of the events")

**Expected outcome:** Handoff is transparent about the credential state and honestly documents the outcome

**Pass criteria:**
- Handoff file exists at `docs/handoffs/goal-tradable_wall-iter-3-dev.md`
- Handoff contains an explicit statement of the credentialed recording result
- Pinned AAPL event is named or clearly identified
- No hedging language (not "attempted", not "may have"; either "ran" or "blocked")

---

## Summary

**Total test cases:** 16

**Breakdown by type:**
- **API tests:** 6 (TC-03, TC-04, TC-09, TC-11, TC-12, TC-13, TC-14)
- **Artifact checks:** 9 (TC-01, TC-02, TC-05, TC-06, TC-07, TC-08, TC-10, TC-15, TC-16)
- **Error case tests:** 3 (TC-12, TC-13, TC-14, TC-15)

**Key coverage:**

- **Recording driver:** TC-01 (exists and wires events → windows → registration)
- **Dataset immutability:** TC-02 (append-only, checksum, feed-stamp, split-frozen)
- **Tape-at-the-wall join:** TC-03 (recorded event returns non-empty timeline), TC-04 (non-recorded stays empty)
- **Single-source-of-truth:** TC-05 (join calls frozen engine, never reimplements)
- **Frozen foundations:** TC-06 (no changes to engine, recorder, adapter, levels), TC-07 (fingerprint frozen, new constants excluded)
- **Credential discipline:** TC-08 (no literal keys anywhere), TC-11 (integration test skips honestly when absent), TC-13 (missing credentials blocked, never fabricated)
- **Fixtures and error cases:** TC-10 (committed fixture small and feed-stamped), TC-12/TC-13/TC-14/TC-15 (error paths handled correctly)
- **Regression guard:** TC-09 (required journeys J-01/J-02/J-07 stay green)
- **Transparency:** TC-16 (handoff documents the credentialed outcome explicitly)

All tests are **keyless by default** (hermetic, using committed fixtures or `FakeAdapter`); the integration test (TC-11) **honestly skips when credentials are absent** and documents the skip reason, never simulates or fabricates the credentialed step. This matches the spec's explicitly stated expectation: J-03 ships as its keyless substrate in this environment, with the credentialed headline honestly blocked until operator Alpaca keys are configured.
