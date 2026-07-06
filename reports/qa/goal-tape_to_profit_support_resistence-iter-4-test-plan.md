# J-04: Tape-Confirmed Structure Entries Functional Test Plan

**Phase:** goal-tape_to_profit_support_resistence-iter-4  
**Date:** 2026-07-06  
**Frontend Present:** no

## Phase Goal

Register a tape-confirmed `structure_tape` strategy as an additive entry beside the frozen `v1`, wired into the backtest runner to arm only where a classified support/resistance level and a confirming tape read coincide, served via `GET /research/strategies` and MCP, with strategy id and level provenance stamped on each trade.

## Test Cases

### TC-01 — Strategy Registry Lists Exact Order and Champion

**Type:** api  
**Preconditions:** Backend running, no prior `structure_tape` registry; `v1` is registered and frozen.

**Steps:**
1. Call `GET /research/strategies` on the running backend
2. Parse the JSON response
3. Verify the strategy list array length
4. Verify the first strategy id equals `"v1"`
5. Verify the second strategy id equals `"structure_tape"`
6. Verify the champion strategy id is present in the response
7. Verify the champion strategy id matches a value in the strategy registry

**Expected outcome:** Response contains exactly two strategies in registration order (`v1` first, `structure_tape` second), plus a champion strategy id that is one of the two registered ids.

**Pass criteria:** HTTP 200, `{"strategies": [{"id": "v1", ...}, {"id": "structure_tape", ...}], "champion": {"strategy_id": "v1" or "structure_tape", ...}}`, champion id is not null and matches a registered strategy.

---

### TC-02 — Config Strategy Registry Method Mirrored from Profile Registry

**Type:** api  
**Preconditions:** Backend code loaded; `Config` class available.

**Steps:**
1. Create a `Config()` instance
2. Call `Config().strategy_registry()`
3. Verify the return is a list/tuple of strategy definitions
4. Iterate and verify each definition has an id field
5. Verify length is exactly 2
6. Extract all id values and sort comparison

**Expected outcome:** `Config.strategy_registry()` returns exactly two strategy definitions with ids `["v1", "structure_tape"]` in that order.

**Pass criteria:** `config.strategy_registry()` length == 2, ids match `["v1", "structure_tape"]`.

---

### TC-03 — V1 Strategy Definition Byte-Identical

**Type:** api  
**Preconditions:** Backend code loaded; prior iteration's v1 definition known.

**Steps:**
1. Call `Config().strategy_definition("v1")`
2. Serialize the result to JSON
3. Compare SHA256 hash to the pre-iteration hash (from committed test fixture or prior run)

**Expected outcome:** `strategy_definition("v1")` returns the exact same grammar as before this iteration — no mutations to the v1 branch.

**Pass criteria:** JSON hash of v1 definition is unchanged (committed test value or documented prior hash).

---

### TC-04 — Config Fingerprint Unchanged at 4d665603569b9dbf

**Type:** api  
**Preconditions:** Backend code loaded with new `structure_tape` config fields added.

**Steps:**
1. Call `Config().config_fingerprint()`
2. Verify the returned fingerprint

**Expected outcome:** The fingerprint remains pinned at the iteration-0 value `4d665603569b9dbf`, confirming all new `structure_tape` fields are in the `excluded` set.

**Pass criteria:** `Config().config_fingerprint() == "4d665603569b9dbf"`.

---

### TC-05 — Structure Tape Entry Arms at Classified Level with Rejection Tape State (Long)

**Type:** api  
**Preconditions:** A fixture dataset with recorded bars and precomputed levels + A/B/C confluence; a tape event stream with `bid_absorption` at a classified support level; backtest runner can call `compute_levels()`.

**Steps:**
1. Run a backtest with `strategy_id="structure_tape"` on the fixture dataset
2. Extract trades from the backtest result
3. Filter trades for entries at the support level with `bid_absorption` tape state
4. Verify an entry trade exists at that bar/tick

**Expected outcome:** A long entry fires at the moment price enters a classified support level's proximity band and tape reads `bid_absorption` (rejection = fade).

**Pass criteria:** At least one trade with `direction="long"`, `entry_reason` includes "structure_tape", the trade's level provenance equals the support level's price/timeframe/class.

---

### TC-06 — Structure Tape Entry Arms at Classified Level with Rejection Tape State (Short)

**Type:** api  
**Preconditions:** Same as TC-05; resistance level with `ask_absorption` tape event.

**Steps:**
1. Run the same backtest, filter for entries at resistance level with `ask_absorption`
2. Verify a short entry exists

**Expected outcome:** A short entry fires when price enters a classified resistance level's proximity band and tape reads `ask_absorption`.

**Pass criteria:** At least one trade with `direction="short"`, level provenance matches the resistance level.

---

### TC-07 — Structure Tape Entry Arms at Classified Level with Breakthrough Tape State (Long)

**Type:** api  
**Preconditions:** Fixture with a resistance level and a tape event showing `buyer_control` with real price impact (breakthrough condition).

**Steps:**
1. Run backtest, filter for long entries at resistance with `buyer_control` breakthrough
2. Verify entry exists

**Expected outcome:** A long entry fires when price enters a resistance level's proximity band and tape reads `buyer_control` with price impact crossing the level (follow).

**Pass criteria:** Trade exists with `direction="long"`, entry at resistance level, tape state confirms breakthrough.

---

### TC-08 — Structure Tape Entry Arms at Classified Level with Breakthrough Tape State (Short)

**Type:** api  
**Preconditions:** Fixture with support level and `seller_control` breakthrough event.

**Steps:**
1. Run backtest, filter for short entries at support with `seller_control` breakthrough
2. Verify entry exists

**Expected outcome:** A short entry fires at support level with `seller_control` breakthrough.

**Pass criteria:** Trade with `direction="short"`, entry stamped with support level provenance.

---

### TC-09 — No Entry When Level Absent (Honest Empty)

**Type:** api  
**Preconditions:** A fixture dataset with a symbol that has no computed levels (or a symbol without any confluence-classified zones).

**Steps:**
1. Run a `structure_tape` backtest on that symbol
2. Extract trade list from result
3. Count `structure_tape`-strategy trades

**Expected outcome:** Zero `structure_tape` trades fire; the backtest completes with no entries and an honest empty result (not fallback to v1, not fabricated data).

**Pass criteria:** Trade list is empty or contains zero `structure_tape` entries, result status is not `failed`.

---

### TC-10 — No Entry When Tape State Unconfirmed

**Type:** api  
**Preconditions:** A fixture with a classified level but tape readings at that level show `unclear` or do not match the rejection/breakthrough criteria.

**Steps:**
1. Run backtest on data where price enters a level but tape is unconfirmed
2. Count entries at that moment

**Expected outcome:** No entry fires; the strategy correctly requires both the level AND the confirming tape state.

**Pass criteria:** No trade enters at the unconfirmed moment.

---

### TC-11 — Level Provenance Stamped on Each Trade

**Type:** api  
**Preconditions:** A backtest with at least one `structure_tape` entry.

**Steps:**
1. Run the backtest
2. Extract a `structure_tape` trade
3. Verify the trade dict contains level provenance (price, timeframe, class)

**Expected outcome:** Each `structure_tape` trade record includes the triggering level's price, timeframe, and A/B/C class.

**Pass criteria:** Trade dict has fields like `level_price`, `level_timeframe`, `level_class` (or equivalent naming), with non-null values matching a known level.

---

### TC-12 — Backtest Determinism: Byte-Identical Re-Run

**Type:** api  
**Preconditions:** A fixture backtest dataset, backtest runner using seeded RNG.

**Steps:**
1. Run a `structure_tape` backtest
2. Capture the full JSON response (all trades, R, $, provenance)
3. Re-run the identical backtest
4. Compare the two JSON strings (after canonicalizing field order)

**Expected outcome:** Two back-to-back runs of the same backtest produce byte-identical JSON output.

**Pass criteria:** SHA256(run1_json) == SHA256(run2_json) after canonicalizing JSON (sorted keys).

---

### TC-13 — Unregistered Strategy ID Returns 422

**Type:** api  
**Preconditions:** A fixture dataset, backtest endpoint available.

**Steps:**
1. Call `POST /research/backtests` with `strategy_id="unknown_strategy"`
2. Capture the HTTP response code and error body

**Expected outcome:** The endpoint rejects the unknown strategy with HTTP 422.

**Pass criteria:** HTTP 422, error message references the unregistered strategy id.

---

### TC-14 — MCP Strategies Tool Byte-Identical to REST

**Type:** api  
**Preconditions:** MCP server running, `strategies` tool available.

**Steps:**
1. Call `GET /research/strategies` via REST (curl)
2. Call the MCP `strategies` tool via the MCP interface
3. Compare JSON responses (canonicalized)

**Expected outcome:** Both return exactly the same JSON data (registry + champion).

**Pass criteria:** JSON content is byte-identical; HTTP 200 and MCP success both present.

---

### TC-15 — MCP Strategies Returns Error When Backend Down

**Type:** api  
**Preconditions:** MCP server running, backend stopped.

**Steps:**
1. Ensure backend is unreachable
2. Call the MCP `strategies` tool
3. Capture the error response

**Expected outcome:** The tool returns an explicit error (not a cached/fabricated response).

**Pass criteria:** MCP tool error raised, message indicates backend unreachable, no fabricated strategy list returned.

---

### TC-16 — No-Execution Grep Guard Passes

**Type:** artifact  
**Preconditions:** All new code committed.

**Steps:**
1. Run `test_no_execution_path.py` (or the grep-guard test suite)
2. Capture the test result

**Expected outcome:** The guard confirms no broker, order, routing, execution, or paper-trading code exists in the codebase, including the new `structure_tape` position-size field.

**Pass criteria:** Test passes, grep confirms no `brokerage`, `order`, `execution`, `paper_trading`, or equivalent identifier in backend code.

---

### TC-17 — Full Backend Test Suite Green

**Type:** api  
**Preconditions:** All implementation code written.

**Steps:**
1. Run the full backend test suite: `cd apps/backend && python -m pytest`
2. Capture test count and pass/fail summary

**Expected outcome:** All tests pass; no regressions from prior iteration baseline (1107 passed, 1 skipped).

**Pass criteria:** Test exit code 0, passed count >= 1107, skipped count == 1, no failures or errors.

---

### TC-18 — Engine Equivalence Suite Green (V1/Default Byte-Identical)

**Type:** api  
**Preconditions:** Equivalence test suite present (e.g., `test_profile_equivalence.py`).

**Steps:**
1. Run the engine equivalence suite
2. Verify default profile output matches the archived tape engine output

**Expected outcome:** The equivalence test confirms `default` profile tape state / confidence / features / history is byte-identical to the pre-iteration version.

**Pass criteria:** Equivalence test passes, no divergence in default profile outputs.

---

### TC-19 — New GET /research/strategies Endpoint Exists and Mirrors Profile Shape

**Type:** api  
**Preconditions:** Backend running, routes implemented.

**Steps:**
1. Call `GET /research/strategies`
2. Verify HTTP 200
3. Verify response schema mirrors `GET /research/profiles` (strategy registry array + champion summary)

**Expected outcome:** The endpoint is reachable and returns the expected shape.

**Pass criteria:** HTTP 200, response has `strategies` array and `champion` object with `strategy_id` field.

---

### TC-20 — Frontend Changes Empty (Frozen Front-End Guard)

**Type:** artifact  
**Preconditions:** Phase complete.

**Steps:**
1. Run `git diff -- apps/frontend/`
2. Verify no changes

**Expected outcome:** No modifications to `apps/frontend/` (consistent with J-07 frozen-frontend guard).

**Pass criteria:** `git diff -- apps/frontend/` output is empty.

---

## Summary

**Total test cases:** 20  
**API tests:** 18 (strategies, entries, determinism, MCP, grep-guard, backend suite, equivalence)  
**Artifact checks:** 2 (frontend empty, grep-guard)  
**Browser tests:** 0 (Frontend Present: no — machine surface only)

All tests derive directly from the phase spec DEFINITION OF DONE, IN SCOPE sections, and TESTING REQUIREMENTS. The tape-confirmed entry logic is exercised via both rejection (fade) and breakthrough (follow) in both long and short directions, with no-arm conditions verified. Determinism, byte-identity of v1/default/fingerprint, and single-source-of-truth guards (MCP, levels provenance, config-owned registry) are all covered.
