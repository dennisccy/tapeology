# goal-desk-iter-17 Functional Test Plan

**Phase:** goal-desk-iter-17 (J-13 — Every ranked row discloses the price its wall sits at)
**Date:** 2026-07-29
**Frontend Present:** yes

## Phase Goal

Every ranked row on `/desk` shows the exact price its wall sits at (`reference_close`) beside the `price_low`–`price_high` band range it was measured against, making "the price is inside the wall" a visible fact instead of unrecoverable arithmetic.

## Test Cases

### TC-01 — New screen snapshot binds `reference_close` on every ranked row

**Type:** api
**Preconditions:** A fixture-scoped rig with a registered universe snapshot and bar store exists; no prior screen snapshot recorded for the test five pins (universe, screen_date, as_of, timeframe, bar_store_signature).

**Steps:**
1. POST to `/research/desk/screen` with the test five pins to compute a new screen snapshot
2. Parse the response's `ranked_rows` array
3. Extract the `reference_close` value from each ranked row

**Expected outcome:** Every ranked row's `reference_close` equals the `close` value `_resolve_reference_close_and_history` returns for that row's own `basis_as_of`.

**Pass criteria:** 
```
200 OK response; 100% of ranked rows carry a `reference_close` field; 
each `reference_close` value matches the close from the row's basis bar at `basis_as_of`
```

---

### TC-02 — `reference_close` cross-checks byte-identical against `/research/candles`

**Type:** api
**Preconditions:** A new screen snapshot (from TC-01) has been recorded; each ranked row carries `reference_close` and `basis_as_of`; `/research/candles` endpoint is available.

**Steps:**
1. For each ranked row in the screen snapshot, extract `symbol`, `reference_close`, and `basis_as_of`
2. Call `GET /research/candles?symbol=<symbol>&timeframe=1d`
3. Find the bar dated at `basis_as_of`
4. Extract the bar's `close` value

**Expected outcome:** For every ranked row, the `reference_close` value is byte-identical to the `close` field of the 1d bar dated at that row's own `basis_as_of`.

**Pass criteria:**
```
For all ranked rows: reference_close == candles[basis_as_of].close (floating-point byte match)
```

---

### TC-03 — Ranked-row symbol sequence unchanged after adding `reference_close`

**Type:** api
**Preconditions:** A pre-change golden fixture snapshot for the same five pins exists; the new code (iter-17) has been deployed; `_row_rank_key` source appears only as unchanged CONTEXT in `git diff`.

**Steps:**
1. Replay the screen computation on the same five pins under the new code
2. Extract the ranked-row symbol sequence from the new result
3. Extract the ranked-row symbol sequence from the pre-change golden fixture
4. Compare byte-for-byte

**Expected outcome:** The two symbol sequences are byte-identical; rank order is unchanged by the addition of `reference_close`.

**Pass criteria:**
```
new_snapshot.ranked_rows[*].symbol == golden_fixture.ranked_rows[*].symbol for all rows in order
```

---

### TC-04 — Re-run under identical pins returns already-recorded snapshot, byte-identical

**Type:** api
**Preconditions:** A screen snapshot has been computed and written to the store (from TC-01); the same five pins (universe, screen_date, as_of, timeframe, bar_store_signature) are available.

**Steps:**
1. POST to `/research/desk/screen` with the identical five pins a second time
2. Capture the response and its HTTP status
3. Verify no new file was written to disk in the store directory

**Expected outcome:** The endpoint returns the previously-recorded snapshot byte-identical without writing a new file.

**Pass criteria:**
```
200 OK; response body matches first compute byte-for-byte; 
disk modification time of the snapshot file unchanged since TC-01
```

---

### TC-05 — Legacy (pre-iteration) snapshot carries no `reference_close` key

**Type:** api
**Preconditions:** A screen snapshot recorded before iter-17's code was deployed exists in the store; the file's on-disk checksum is known.

**Steps:**
1. Call `GET /research/desk/screen?date=<that-date>` to fetch the legacy snapshot
2. Inspect each ranked row in the response
3. Check the on-disk file's SHA256 checksum
4. Fetch `/desk` in a browser and verify the rendered fallback text

**Expected outcome:** 
- The `reference_close` key is entirely absent from every ranked row (not `null`, not `undefined` — the key does not exist)
- The file's on-disk checksum matches its pre-iteration value
- The `/desk` page renders `"close not recorded in this snapshot"` for each row

**Pass criteria:**
```
GET response ranked rows: "reference_close" not in row (key entirely absent);
on-disk SHA256 unchanged; browser DOM contains fallback text for all rows
```

---

### TC-06 — `/desk` ranked table displays `band` column with legible `reference_close` and band range

**Type:** browser
**Preconditions:** The dev server is running at http://localhost:3000; a screen snapshot with `reference_close` data is available; the snapshot contains at least one row where `reference_close` lies INSIDE its `price_low`–`price_high` band and one row where it lies OUTSIDE.

**Steps:**
1. Navigate to http://localhost:3000/desk
2. Wait for the ranked-rows table to render
3. Locate the new `band` column header
4. Scroll to find a row whose `distance_bps` is 0.0 (close inside band) and a row whose `distance_bps` is non-zero (close outside band)
5. Take a screenshot capturing at least one row of each type in the same view

**Expected outcome:** The ranked table displays a new `band` column showing, for each row, the formatted band range (`price_low`–`price_high`) and the close value (e.g., `band 488.50–490.85 · close 490.85`). Both in-band and out-of-band rows are legible in a single screenshot.

**Pass criteria:**
```
Column header "<th>band</th>" present; each row's band cell displays formatted band and close;
at least one row with distance_bps == 0.0 shows close inside band;
at least one row with distance_bps != 0.0 shows close outside band; both visible in one screenshot
```

---

### TC-07 — `BarStore.merged_bars()` invoked exactly once per symbol, no additional reads

**Type:** api
**Preconditions:** Unit test framework is set up; the `test_desk_screen.py` test suite can be run.

**Steps:**
1. Run the test `test_reference_close_fields_add_zero_extra_merged_bars_calls` (or equivalent guard test)
2. Mock or instrument `BarStore.merged_bars()` to count invocations per symbol
3. Compute a screen for N symbols with bars
4. Verify the call count

**Expected outcome:** `BarStore.merged_bars(symbol, "1d")` is invoked exactly once per symbol, with no additional store reads beyond the one existing walk in `compute_screen`.

**Pass criteria:**
```
For each symbol in the screen: call_count(merged_bars(symbol, "1d")) == 1;
total call count == number of ranked symbols; no additional BarStore accessor calls
```

---

### TC-08 — No client-side recomputation of price via arithmetic on band fields

**Type:** artifact
**Preconditions:** The source code for `apps/frontend/app/desk/page.tsx` is available; the source-scan guard test exists.

**Steps:**
1. Run the test `test_desk_ui_guards.py` (or equivalent source-introspection guard)
2. Scan `apps/frontend/app/desk/page.tsx` for any arithmetic expressions (e.g., `+`, `-`, `*`, `/`) involving `distance_bps`, `price_low`, or `price_high` outside the existing band-range display cell
3. Verify no derived-price expressions exist

**Expected outcome:** The frontend renders only what the backend endpoint serves; no price value is derived via client-side arithmetic on band fields.

**Pass criteria:**
```
Source scan finds zero arithmetic expressions on distance_bps/price_low/price_high 
outside the existing DeskRow band cell; test passes unmodified
```

---

### TC-09 — Fingerprint, Config fields, and protected modules unchanged

**Type:** api
**Preconditions:** The full backend suite has been run; the fingerprint and module diffs can be inspected.

**Steps:**
1. Run `Config().config_fingerprint()` and capture its output
2. Run `git diff --stat` for `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `StructureChart.tsx`
3. Scan the Config class for any new field definitions
4. Count the MCP tools via `EXPECTED_TOOLS` in `test_mcp_server.py`
5. Verify the full backend suite passes (baseline 1426 passed / 8 skipped per iter-16)

**Expected outcome:** 
- Fingerprint prints exactly `08e471b10130e1e2` (unchanged)
- Zero diff to protected modules
- Zero new `Config` fields
- MCP tool count is exactly 17
- Full backend suite passes (≥1426 passed, tests only grow)

**Pass criteria:**
```
fingerprint == "08e471b10130e1e2";
git diff --stat tradability.py/levels.py/bars.py/bar_index.py/StructureChart.tsx is empty;
no new Config fields; EXPECTED_TOOLS count == 17; suite pass count >= 1426
```

---

### TC-10 — MCP `desk_screen` tool response byte-identical to direct GET endpoint

**Type:** api
**Preconditions:** The MCP `desk_screen` tool is available; the backend `/research/desk/screen` endpoint is running.

**Steps:**
1. Call the MCP `desk_screen` tool with no arguments (or the same arguments as the endpoint)
2. Call `GET /research/desk/screen` directly with the same snapshot query parameters
3. Serialize both responses as JSON and compare byte-for-byte

**Expected outcome:** The MCP tool's response is byte-identical to the direct GET response; the new `reference_close` field is proxied transparently with zero code change.

**Pass criteria:**
```
json.dumps(mcp_response, sort_keys=True) == json.dumps(get_response, sort_keys=True);
response includes reference_close field; tool count remains exactly 17
```

---

### TC-11 — Copy-discipline lint passes unmodified

**Type:** artifact
**Preconditions:** The test `tests/test_copy_discipline.py` exists and is configured to scan the frontend copy; the new `band` and `close` copy strings have been added to `page.tsx`.

**Steps:**
1. Run `tests/test_copy_discipline.py` without any modifications to the lint file itself
2. Scan the new `band` column copy (`"band X–Y · close Z"`) and the tooltip fallback (`"close not recorded in this snapshot"`)
3. Verify no advice, imperative, prediction, or ranking language is present

**Expected outcome:** The test passes unmodified; the new copy strings contain no advice, imperative, prediction, or action-implying language.

**Pass criteria:**
```
test_copy_discipline.py exit code 0; new strings pass lint without edits;
zero instances of "buy", "watch", "opportunity", "should", or similar imperative language
```

---

### TC-12 — Demo-narrator records `[NEW]`-flagged J-13 walkthrough with gallery

**Type:** browser
**Preconditions:** Demo-narrator lane runs at `full` depth (before scoring); a browser-ready test environment with `/desk` page rendering is available.

**Steps:**
1. Verify the demo-narrator outputs `Demo Verdict: RECORDED` for J-13
2. Verify a screenshot gallery directory is created (non-empty)
3. Inspect gallery images for:
   - The ranked table's new `band` column header and cells
   - At least one row whose `reference_close` lies inside its band (distance_bps 0.0)
   - At least one row whose `reference_close` lies outside its band (distance_bps != 0.0)
   - A legacy row showing the honest `"close not recorded in this snapshot"` fallback

**Expected outcome:** The walkthrough is recorded as `[NEW]`-flagged (not a replay of an earlier walkthrough); the gallery contains at least four distinct screenshots narrating the required states.

**Pass criteria:**
```
Demo Verdict: RECORDED; gallery directory is non-empty; 
4+ screenshots showing band column, in-band row, out-of-band row, legacy row fallback;
[NEW] flag in demo-script.json; no reuse of pre-recorded walkthrough
```

---

## Summary

**Total test cases:** 12

**API tests:** 8 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-07, TC-09, TC-10)

**Browser tests:** 2 (TC-06, TC-12)

**Artifact checks:** 2 (TC-08, TC-11)

All test cases derive directly from the phase spec's TESTING REQUIREMENTS and TEST-FIRST CONTRACT sections, covering the new `reference_close` field binding, serialization consistency, legacy-row handling, UI display, performance guards, anti-goal compliance, copy discipline, and demo-narrator evidence.
