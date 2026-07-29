# goal-desk-iter-19 Functional Test Plan

**Phase:** goal-desk-iter-19
**Date:** 2026-07-29
**Frontend Present:** yes

## Phase Goal

Fix the `/desk` ranked table's `opposite` column to name the wall genuinely nearest to price on the other side (distance-first) rather than the best-graded one, closing a 2-of-63-real-row divergence and re-filming the walkthrough over populated rows.

## Test Cases

### TC-01 — Select opposite band: distance-first over class

**Type:** api
**Preconditions:** Backend running; `_select_opposite_band` implemented with distance-first tie-break order

**Steps:**
1. Call `_select_opposite_band` with a bands list containing: the row's own selected band, a close-but-lower-class opposite-side band (e.g. 150 bps, class B), and a farther-but-higher-class opposite-side band (e.g. 300 bps, class A)

**Expected outcome:** Returns the closer band (150 bps class B), not the higher-class one (300 bps class A)
**Pass criteria:** `opposite_band.distance_bps == 150 and opposite_band.band_class == 'B'`

---

### TC-02 — Select opposite band: exact tie preserves served order

**Type:** api
**Preconditions:** Backend running; `_select_opposite_band` implemented

**Steps:**
1. Call `_select_opposite_band` with two exactly-tied opposite-side bands (same distance, class, score)
2. Call again with the same bands in reverse order
3. Repeat each call twice more

**Expected outcome:** Each call returns the first-served band in that order; repeated calls return the identical band every time
**Pass criteria:** First call returns bands[0], second call returns bands[0] of reversed list; all four calls are stable within their respective orderings

---

### TC-03 — Select opposite band: no opposite side returns None

**Type:** api
**Preconditions:** Backend running; `_select_opposite_band` implemented

**Steps:**
1. Call `_select_opposite_band` with a bands list where every band shares the row's own selected side

**Expected outcome:** Returns `None`
**Pass criteria:** `opposite_band == None`

---

### TC-04 — Golden fixture rows recompute correctly under new rule

**Type:** api
**Preconditions:** Fixture-scoped rig; `test_desk_screen.py` golden fixture loaded; `_select_opposite_band` corrected

**Steps:**
1. Run `test_opposite_band_golden_near_far_and_null_class_rows` from `test_desk_screen.py`
2. Verify each row's `opposite_band` value

**Expected outcome:** Each golden fixture row's `opposite_band` matches the nearest-by-distance opposite-side band; all assertions pass
**Pass criteria:** Test passes with zero failures; no pre-fix class-first assertions remain in the file

---

### TC-05 — Freshly computed screen: opposite_band byte-identical to tradability route

**Type:** api
**Preconditions:** Fixture-scoped rig; freshly computed screen; `GET /research/tradability` endpoint running

**Steps:**
1. Compute a new screen on fixture-scoped rig
2. For each ranked row, query `GET /research/tradability?symbol=<sym>&as_of=<as_of>` to get the `bands` list
3. Compare the row's `opposite_band` against that list's smallest-`distance_bps` band on the opposite side

**Expected outcome:** `opposite_band.side`, `band_class`, `price_low`, `price_high`, `band_score` are byte-identical to the tradability route's selected band; `distance_bps` reproduces the same formula
**Pass criteria:** All rows match; AAPL real-route cross-check test `test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route` passes unmodified

---

### TC-06 — Real data divergence: HONA and META rows correct their opposite selection

**Type:** api
**Preconditions:** Fixture-scoped rig with real or fixture-scoped-equivalent data reproducing iter-18's HONA/META divergence; `_select_opposite_band` corrected

**Steps:**
1. Compute screen under the corrected rule
2. Inspect HONA's `opposite_band` value
3. Inspect META's `opposite_band` value

**Expected outcome:** HONA's `opposite_band` shows the nearer class-B band (~153.67 bps) rather than the farther class-A band (~336.96 bps); META's shows the nearer class-C band (~92.05 bps) rather than the farther class-A band (~232.58 bps)
**Pass criteria:** `HONA.opposite_band.distance_bps ~= 153.67` and `HONA.opposite_band.band_class == 'B'`; `META.opposite_band.distance_bps ~= 92.05` and `META.opposite_band.band_class == 'C'`

---

### TC-07 — Same-side selection unchanged: _select_best_band passes unmodified

**Type:** api
**Preconditions:** `_select_best_band` suite unchanged; tests run after `_select_opposite_band` fix applied

**Steps:**
1. Run the full `_select_best_band` test suite from `test_desk_screen.py`

**Expected outcome:** Every test passes unmodified
**Pass criteria:** Suite reports 100% pass; zero failures

---

### TC-08 — Identical-pins recompute: no second file written

**Type:** api
**Preconditions:** Fixture-scoped rig; existing screen snapshot recorded under specific five pins

**Steps:**
1. Trigger a screen recompute under the SAME five pins (same universe snapshot id, screen date, as_of, bar-store signature, fingerprint)

**Expected outcome:** Returns the existing snapshot unchanged rather than writing a second file
**Pass criteria:** File count unchanged; byte-identical re-run test `test_opposite_band_stays_byte_identical_on_a_recompute_under_identical_pins` passes

---

### TC-09 — Cross-symbol rank order unchanged: _row_rank_key byte-identical

**Type:** api
**Preconditions:** Screen computed before and after the fix under identical pins

**Steps:**
1. Compare the cross-symbol ranked-row order (`_row_rank_key`) before and after the fix

**Expected outcome:** Order is byte-identical
**Pass criteria:** No reordering; compare yields zero diffs

---

### TC-10 — MCP proxy byte-identity: desk_screen tool and GET endpoint match

**Type:** api
**Preconditions:** Backend running; MCP server running; fixture screen post-fix

**Steps:**
1. Query the MCP `desk_screen` tool against the fixture screen
2. Query `GET /research/desk/screen` endpoint against the same screen
3. Query `get_endpoint` proxy against the same screen
4. Compare `opposite_band` and `bands_by_class` fields across all three responses

**Expected outcome:** All three return byte-identical `opposite_band`/`bands_by_class`; MCP tool count remains exactly 17
**Pass criteria:** All three responses match; test `test_desk_screen_opposite_band_and_bands_by_class_fields_proxy_verbatim` passes; tool count is 17

---

### TC-11 — Backend suite green: full suite passes, fingerprint frozen, copy-discipline clean

**Type:** api
**Preconditions:** Full backend suite ready to run

**Steps:**
1. Run full backend test suite
2. Verify `Config().config_fingerprint()` output
3. Run `test_copy_discipline.py`

**Expected outcome:** All tests pass; fingerprint prints `08e471b10130e1e2`; copy-discipline clean
**Pass criteria:** Suite: zero failures; fingerprint: `08e471b10130e1e2`; copy-discipline: unmodified passing

---

### TC-12 — Protected modules zero diff: tradability, levels, bars, bar_index, StructureChart, desk_coverage

**Type:** artifact
**Preconditions:** Git diff available; iteration changes applied

**Steps:**
1. Diff the following files against pre-iteration tree: `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `StructureChart.tsx`, `desk_coverage.py`

**Expected outcome:** Each file shows zero changes
**Pass criteria:** All six diffs are empty

---

### TC-13 — Browser: /desk opposite column shows both near and far rows legible

**Type:** browser
**Preconditions:** Fixture-scoped rig; `rm -rf apps/frontend/.next` + rebuild completed; freshly computed screen; frontend running on http://localhost:3000

**Steps:**
1. Navigate to `http://localhost:3000/desk`
2. Locate ranked table's `opposite` column
3. Take a screenshot showing at least one row with `distance_bps` within 25 bps and one beyond 1,000 bps, both legible in frame
4. Hover over a row's tooltip to show `bands_by_class` line
5. Take a second screenshot of the tooltip

**Expected outcome:** `opposite` column visible; near row (≤25 bps) and far row (>1,000 bps) both present and readable in one screenshot; tooltip displays `bands_by_class`
**Pass criteria:** Screenshot TC-13-near-far-rows.png shows both distance ranges legible; screenshot TC-13-tooltip-bands.png shows `bands_by_class` text rendered

---

### TC-14 — Demo walkthrough: [NEW]-flagged re-film over populated /desk rows

**Type:** artifact
**Preconditions:** Fixture-scoped rig with freshly computed, populated screen; demo-narrator script executed

**Steps:**
1. Review the `[NEW]`-flagged demo-narrator walkthrough in `reports/demo/goal-desk-iter-19/`
2. Verify each step narrates the opposite-wall disclosure
3. Verify all screenshots show `/desk` page content, never `/structure`
4. Verify walkthrough runs end to end without breaks

**Expected outcome:** Demo narrates opposite-wall disclosure over populated ranked rows; every screenshot is from `/desk`; walkthrough closes both J-14's own walkthrough clause and iter-17's carried J-13 `RECORDED_WITH_NOTES` gap
**Pass criteria:** All steps show `/desk` (zero `/structure` screenshots); narrative covers the opposite-band selection rule over real rows; demo file exists in `reports/demo/goal-desk-iter-19/` and is properly tagged as `[NEW]`

---

## Summary

**Total test cases:** 14
- **API tests:** 12 (TC-01 through TC-12)
- **Browser tests:** 1 (TC-13)
- **Artifact checks:** 1 (TC-14)

**Key areas verified:**
- Tie-break order correction: distance first, then class rank, then band score (TC-01, TC-02)
- Edge cases: no opposite side (TC-03), exact ties (TC-02), null classes (TC-04)
- Real data validation: HONA/META divergence correction (TC-06)
- Stability: unchanged same-side selection, rank order, and MCP proxy (TC-07, TC-09, TC-10)
- Immutability: identical-pins recompute (TC-08), fingerprint frozen (TC-11), protected modules (TC-12)
- Browser verification: correct column rendering with distance range evidence (TC-13)
- Walkthrough closure: re-filmed demo-narrator artifact (TC-14)
