# goal-desk-iter-18 Functional Test Plan

**Phase:** goal-desk-iter-18  
**Date:** 2026-07-29  
**Frontend Present:** yes

## Phase Goal

Every ranked row on `/desk` discloses the nearest wall on the side of price it did NOT select (`opposite_band`) plus a per-class count of bands (`bands_by_class`), making the 10,000×-wide spread between opposite-wall distances visible instead of invisible.

## Test Cases

### TC-01 — New ranked screen carries opposite_band and bands_by_class on every ranked row

**Type:** api  
**Preconditions:** 
- Fixture-scoped backend running with a registered universe snapshot and bar store
- No pre-existing screen snapshot for the target five pins (date/universe_id/as_of/bar_store_signature/schema_version)

**Steps:**
1. Compute a NEW screen for a screen_date not already recorded under the target five pins via `POST /research/desk/screen` (or internal `compute_screen()`)
2. Retrieve the computed screen via `GET /research/desk/screen?date=<screen_date>`
3. Extract the ranked rows from the response (non-skip rows)

**Expected outcome:** Every ranked row in the response carries an `opposite_band` field (either an object or `null`) and a `bands_by_class` field with keys `"A"`, `"B"`, `"C"`, `"unclassified"`.

**Pass criteria:** 100% of ranked rows have both fields present (not absent); `bands_by_class` object always has all four keys regardless of value.

---

### TC-02 — opposite_band values match the corresponding band in GET /research/tradability

**Type:** api  
**Preconditions:**
- TC-01 passed (new screen computed with opposite_band populated)
- Fixture-scoped backend running

**Steps:**
1. For each ranked row whose `opposite_band` is non-null, read the row's `symbol` and its snapshot's `as_of` value
2. Call `GET /research/tradability?symbol=<sym>&as_of=<as_of>` to fetch that symbol's tradability record
3. Find the band in the tradability response's `bands` list that matches the row's `opposite_band.side`, `band_class`, `price_low`, `price_high`, and `band_score`
4. Compare byte-for-byte

**Expected outcome:** Every non-null `opposite_band` found in the screen matches exactly one band in the corresponding tradability response.

**Pass criteria:** All non-null opposite_band records match byte-identically; zero mismatches or missing bands.

---

### TC-03 — opposite_band.distance_bps matches _distance_bps formula output

**Type:** api  
**Preconditions:**
- TC-01 passed (new screen with opposite_band computed)
- Fixture-scoped backend running

**Steps:**
1. For each ranked row with non-null `opposite_band`, extract `opposite_band.distance_bps`, the row's `reference_close`, and the opposite band's `price_low`/`price_high`
2. Apply the `_distance_bps(opposite_band_price_range, reference_close)` formula (same logic used in `_select_best_band`)
3. Compare computed distance to the stored `opposite_band.distance_bps`

**Expected outcome:** Computed distance matches stored value exactly.

**Pass criteria:** 100% of non-null opposite_band records have correct distance_bps.

---

### TC-04 — bands_by_class counts sum to total bands from tradability

**Type:** api  
**Preconditions:**
- TC-01 passed (new screen with bands_by_class populated)
- Fixture-scoped backend running

**Steps:**
1. For each ranked row, sum its `bands_by_class.A + bands_by_class.B + bands_by_class.C + bands_by_class.unclassified`
2. Call `GET /research/tradability?symbol=<sym>&as_of=<as_of>` to fetch that symbol's band list
3. Count the total bands in the tradability response

**Expected outcome:** Sum of bands_by_class equals the total band count from tradability.

**Pass criteria:** 100% of rows have bands_by_class counts summing to their symbol's total band count.

---

### TC-05 — Ranked row symbol sequence is byte-identical to pre-change fixture

**Type:** artifact  
**Preconditions:**
- New screen computed on the fixture-scoped rig with opposite_band/bands_by_class added
- Pre-change golden fixture file available (recorded before this iteration's code landed)

**Steps:**
1. Extract the symbol sequence from the new screen's ranked rows (in order)
2. Extract the symbol sequence from the pre-change golden fixture's ranked rows
3. Compare sequences byte-for-byte
4. Inspect the git diff of `_row_rank_key` function — it must appear only as unchanged context, no edits

**Expected outcome:** Symbol sequences match exactly; rank key unchanged.

**Pass criteria:** Symbol sequences are byte-identical; git diff shows `_row_rank_key` only in unchanged context (no modifications).

---

### TC-06 — Re-run under identical pins returns already-recorded response, no new file written

**Type:** api  
**Preconditions:**
- TC-01 passed (first screen compute with opposite_band)
- Fixture-scoped backend running with the same five pins as the first compute

**Steps:**
1. Trigger a second screen compute for the exact same screen_date and five pins
2. Retrieve the response
3. Compare to the first response byte-for-byte
4. Verify no new file was written to the store (check store filesystem or call history)

**Expected outcome:** Second response is byte-identical to first; no new file created on disk.

**Pass criteria:** Byte-identical responses; store returns cached result instead of recomputing.

---

### TC-07 — Legacy screen snapshot rows carry no opposite_band/bands_by_class keys; fallback renders correctly

**Type:** artifact + browser  
**Preconditions:**
- A pre-iteration screen snapshot file exists in the fixture-scoped store (recorded before opposite_band/bands_by_class code landed)
- Frontend running on the fixture-scoped backend

**Steps:**
1. Call `GET /research/desk/screen?date=<legacy_snapshot_date>` to retrieve the legacy snapshot
2. Inspect a ranked row from the response — verify `opposite_band` and `bands_by_class` keys are entirely absent (not present, not `null`)
3. Verify the on-disk file's checksum is unchanged from before this iteration
4. Call the screen again (re-run) and confirm no new file was written
5. Load `/desk` in a browser and select the legacy snapshot
6. Inspect a ranked row's `opposite` cell rendering

**Expected outcome:** Legacy rows have absent (not null) opposite_band/bands_by_class keys; checksum unchanged; re-run does not write a new file; UI renders `"opposite wall not recorded in this snapshot"` for legacy rows.

**Pass criteria:** Keys entirely absent on legacy rows (not null); file unchanged on re-run; UI fallback string appears in browser.

---

### TC-08 — opposite_band is null when compute_tradability returns bands on only ONE side of price

**Type:** api  
**Preconditions:**
- Fixture-scoped backend with a symbol whose `compute_tradability` returns bands on only one side (e.g., only resistance, no support)
- New screen computed including that symbol

**Steps:**
1. Retrieve the new screen via `GET /research/desk/screen?date=<date>`
2. Find the ranked row for the symbol with one-sided bands
3. Inspect its `opposite_band` field

**Expected outcome:** `opposite_band` is `null` (never an invented or wrong-side band).

**Pass criteria:** opposite_band is null; no fabricated band appears.

---

### TC-09 — Tie-break is stable across repeated calls on a tied fixture

**Type:** api  
**Preconditions:**
- Fixture-scoped backend with a symbol whose bands list contains two or more bands tied on `(class, distance_bps, quality_score)` on the opposite side of the selected band
- New screen computed

**Steps:**
1. Trigger the `_select_opposite_band` selector (or equivalent) twice on the same tied bands list
2. Compare the returned band both times

**Expected outcome:** Both calls return the same band (first-of-tie stability via `min()`).

**Pass criteria:** Identical results on repeated calls; tie-break is deterministic.

---

### TC-10 — No additional BarStore or compute_tradability calls beyond iteration 17 baseline

**Type:** api  
**Preconditions:**
- Fixture-scoped backend running
- Call-count instrumentation available (e.g., mocks or instrumented code)

**Steps:**
1. Compute a new screen for N symbols with bars
2. Assert call counts via guards/instrumentation
3. Verify exactly one `compute_tradability(symbol)` per symbol
4. Verify exactly one `BarStore.merged_bars(symbol, "1d")` per symbol

**Expected outcome:** No additional calls beyond the iteration-17 baseline.

**Pass criteria:** Guard test passes; call counts match expected (1× per symbol for both).

---

### TC-11 — Frontend performs no arithmetic deriving opposite_band or bands_by_class values

**Type:** artifact  
**Preconditions:**
- Frontend source code available (`apps/frontend/app/desk/page.tsx`)

**Steps:**
1. Scan the source for any arithmetic expressions or derived calculations involving `distance`, `price`, `band`, or class-related values in the context of the `opposite` column or `bands_by_class` line
2. Verify no expressions compute an opposite-band or bands-by-class value outside the already-existing rendered fields

**Expected outcome:** The frontend renders only values served by the endpoint; no client-side computation.

**Pass criteria:** No arithmetic expressions found computing opposite-band or bands-by-class values; source scan confirms frontend renders served fields only.

---

### TC-12 — Browser: opposite_band displayed with near and far examples, tooltip shows bands_by_class

**Type:** browser  
**Preconditions:**
- Frontend running on fixture-scoped backend (verified not serving any other app's base URL)
- New screen snapshot with populated opposite_band data loaded (contains rows with ≤25 bps and >1,000 bps opposite distances)
- Page fully loaded and table rendered

**Steps:**
1. Load `/desk` in Chrome browser
2. Select a snapshot date that contains the new screen (opposite_band populated)
3. Take screenshot of the ranked-rows table showing the `opposite` column
4. Verify at least one row with nearest opposite wall ≤25 bps is visible and legible
5. Verify at least one row with nearest opposite wall >1,000 bps is visible and legible
6. Hover over a ranked row to reveal its drill-in tooltip
7. Take screenshot of the tooltip showing the `bands_by_class` line (e.g., `10 bands · A 10 · B 0 · C 0 · unclassified 0`)

**Expected outcome:** `opposite` column renders correctly with both near and far examples legible; tooltip shows full-precision `bands_by_class` line.

**Pass criteria:** Screenshots show the new column with both near (≤25 bps) and far (>1,000 bps) examples; tooltip displays `bands_by_class` counts correctly.

---

### TC-13 — Config fingerprint unchanged, no diff to protected files, zero new Config fields

**Type:** api  
**Preconditions:**
- Full backend suite built and tests run

**Steps:**
1. Run `python3 -c "from app.config import Config; print(Config().config_fingerprint())"`
2. Verify output is exactly `08e471b10130e1e2`
3. Run `git diff HEAD` and filter for `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `StructureChart.tsx`
4. Verify no diff exists for any of those files
5. Scan the `Config` class for new fields added this iteration

**Expected outcome:** Fingerprint unchanged; protected files have zero diff; no new Config fields.

**Pass criteria:** Fingerprint is `08e471b10130e1e2`; all protected files unchanged in git diff; Config class unchanged.

---

### TC-14 — MCP tool count is 17; desk_screen and get_endpoint proxy byte-identical to GET response

**Type:** api  
**Preconditions:**
- Full backend suite run
- MCP server running (or testable via test suite)

**Steps:**
1. Retrieve `EXPECTED_TOOLS` contract count from `apps/backend/tests/test_mcp_server.py`
2. Call the MCP `desk_screen` tool (no args) or run the test that invokes it
3. Call `GET /research/desk/screen?date=<date>` directly via HTTP for the same snapshot
4. Compare the two responses byte-for-byte
5. Verify the MCP tool count is exactly 17

**Expected outcome:** MCP tool count unchanged at 17; `desk_screen` tool response byte-identical to direct HTTP GET; both include new fields.

**Pass criteria:** Tool count is exactly 17; responses match byte-for-byte including opposite_band and bands_by_class.

---

### TC-15 — test_copy_discipline.py passes unmodified

**Type:** api  
**Preconditions:**
- Backend test suite running after the `opposite` column and `bands_by_class` tooltip line land

**Steps:**
1. Run `pytest apps/backend/tests/test_copy_discipline.py -v`
2. Verify zero failures
3. Confirm no edits were made to the lint file itself

**Expected outcome:** All tests pass; lint file unchanged.

**Pass criteria:** Test suite passes; zero copy-discipline violations in new strings (no advice/imperative/prediction language).

---

### TC-16 — Demo-narrator [NEW] walkthrough recorded with populated screen on fixture-scoped rig

**Type:** browser (demo-narrator artifact)  
**Preconditions:**
- Full-depth goal-mode dispatch running demo-narrator BEFORE scoring
- Fixture-scoped rig with freshly computed screen snapshot (opposite_band populated)
- Demo-narrator lane configured to produce `[NEW]`-flagged walkthrough for J-14

**Steps:**
1. Demo-narrator lane runs and records a walkthrough narrating the opposite-wall disclosure
2. Walkthrough captures the ranked table's new `opposite` column
3. Walkthrough includes at least one row whose nearest opposite wall is ≤25 bps
4. Walkthrough includes at least one row whose nearest opposite wall is >1,000 bps
5. Walkthrough includes a row's tooltip showing its `bands_by_class` line
6. Walkthrough includes a legacy row showing the honest `"opposite wall not recorded in this snapshot"` fallback
7. Verify the recording is done on fixture-scoped rig (no write to `apps/backend/.data`)
8. Verify target store was checked for existing snapshot under the same five pins before computing (no collision, or collision disclosed in results)

**Expected outcome:** `Demo Verdict: RECORDED` with a non-empty screenshot gallery narrating all required scenarios.

**Pass criteria:** Demo Verdict is RECORDED; gallery includes all four narrative elements (new column, near example, far example, tooltip, legacy fallback); recorded on fixture-scoped rig; collision (if any) disclosed.

---

## Summary

**Total test cases:** 16  
**API tests:** 11 (TC-01, TC-02, TC-03, TC-04, TC-06, TC-08, TC-09, TC-10, TC-13, TC-14, TC-15)  
**Browser tests:** 2 (TC-12, TC-16)  
**Artifact checks:** 3 (TC-05, TC-07, TC-11)

**Key regression journeys** (J-01 through J-13) verified via deterministic replay + LLM fallback in the goal-evaluator lane (not separate test cases here).
