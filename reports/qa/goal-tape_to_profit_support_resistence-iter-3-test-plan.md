# Goal Iteration 3 — Confluence Zones & A/B/C Classes Functional Test Plan

**Phase:** goal-tape_to_profit_support_resistence-iter-3
**Date:** 2026-07-06
**Frontend Present:** no

## Phase Goal

A researcher calling `GET /research/levels` receives, beside the raw support/resistance levels, the confluence zones that cluster those levels across timeframes — each zone carrying its member levels (with timeframes), a timeframe-weighted score, and an honest A/B/C conviction class, computed once, served from one canonical owner, and read verbatim by REST and MCP.

---

## Test Cases

### TC-01 — Levels within confluence band cluster into a single zone

**Type:** api
**Preconditions:**
- Backend is running with test fixtures loaded (PG 1h + 1d bars)
- Confluence band is set in `Config` (e.g., `sr_confluence_band_bps`)
- Levels have already been computed from the fixture bars

**Steps:**
1. Call `GET /research/levels?symbol=PG&as_of=<fixture_timestamp>`
2. Parse the response JSON for `confluence_zones` field
3. Identify all levels within the response
4. Group levels by price proximity (within the configured band)
5. Verify a single zone exists for levels that fall within the band

**Expected outcome:** 
A single confluence zone is returned with multiple member levels from different timeframes (e.g., 1h and 1d) whose prices fall within the configured tolerance band.

**Pass criteria:** 
The zone contains at least 2 member levels with distinct timeframes; all members' prices are within `sr_confluence_band_bps` of each other; no duplicate members in the zone.

---

### TC-02 — Levels outside the confluence band do not join the zone

**Type:** api
**Preconditions:**
- Backend is running with test fixtures loaded
- Multiple levels exist at different price points
- At least one level is outside the tolerance band

**Steps:**
1. Call `GET /research/levels?symbol=PG&as_of=<fixture_timestamp>`
2. Parse `confluence_zones` in the response
3. Calculate price differences between levels at different timeframes
4. Verify that levels outside the band are not members of the same zone

**Expected outcome:** 
Levels whose prices are beyond the configured tolerance band remain in separate zones (or as isolated levels).

**Pass criteria:** 
Each zone contains only members whose prices are within the tolerance band; levels outside the band do not appear as members of the same zone.

---

### TC-03 — Zone score is a timeframe-weighted sum of member levels' strengths

**Type:** api
**Preconditions:**
- A synthetic multi-timeframe fixture with known level strengths and timeframe weights is loaded
- Timeframe weights are configured (e.g., `sr_timeframe_weights`)
- Each level has a known strength value

**Steps:**
1. Call `GET /research/levels?symbol=<fixture_symbol>&as_of=<fixture_timestamp>`
2. Extract the confluence zone(s) and their member levels
3. For each member level, retrieve its strength value and corresponding timeframe weight
4. Manually compute the expected zone score: sum of (level_strength × timeframe_weight)
5. Compare the computed value to the returned zone `score` field

**Expected outcome:** 
The returned zone score matches the manually computed timeframe-weighted sum.

**Pass criteria:** 
Exact numeric match (or ±0.01 tolerance for floating-point rounding); formula correctness asserted on the synthetic fixture with exact known inputs.

---

### TC-04 — A/B/C grading: class A when config criteria are met

**Type:** api
**Preconditions:**
- A synthetic fixture with 3+ distinct timeframes (meeting the A-class criterion) is loaded
- All member levels fall within the confluence band
- At least one member is a long-term level (e.g., 1d or 1w)
- Config class thresholds are set to grade this zone as A

**Steps:**
1. Call `GET /research/levels?symbol=<fixture_symbol>&as_of=<fixture_timestamp>`
2. Extract the confluence zone(s)
3. Verify each zone's `class` field value

**Expected outcome:** 
A zone meeting the config A-class criteria (multiple timeframes including a long-term level within tolerance) is graded as class **A**.

**Pass criteria:** 
Exact class label "A" returned; criteria (distinct timeframes, long-term member presence, band fit) verified to be met in the fixture.

---

### TC-05 — A/B/C grading: honest B/C when criteria not met

**Type:** api
**Preconditions:**
- The PG fixture (1h + 1d only, 2 timeframes) is loaded
- If the A-class criterion requires 3+ timeframes, the real PG fixture cannot produce a class A zone
- Config class thresholds are properly set

**Steps:**
1. Call `GET /research/levels?symbol=PG&as_of=<fixture_timestamp>`
2. Extract the confluence zone(s) returned
3. Verify the class of any zone(s) returned

**Expected outcome:** 
Zones that do not meet the A-class criteria are honestly graded as **B or C**, never as fabricated A.

**Pass criteria:** 
Class label is B or C (exact label per config); the honest non-A grading reflects the actual timeframe count / long-term presence in the real fixture; no fabricated zones.

---

### TC-06 — Byte-identical deterministic re-runs with explicit total order

**Type:** api
**Preconditions:**
- Backend is running
- Fixture data and config are unchanged
- Zones are sorted by an explicit total order (e.g., price, then timeframe)

**Steps:**
1. Call `GET /research/levels?symbol=PG&as_of=<fixture_timestamp>` — capture response JSON as run 1
2. Call the same endpoint again with identical parameters — capture response JSON as run 2
3. Compute SHA-256 hash of the entire `confluence_zones` array (or full response) for each run
4. Compare the hashes and the JSON structure (member order, field values)

**Expected outcome:** 
Both calls return byte-identical JSON; the order of zones and member levels within each zone is consistent across runs.

**Pass criteria:** 
JSON hashes match exactly; `confluence_zones` array order is stable (e.g., zones sorted by lowest member price, ties broken by timeframe); all numeric values identical.

---

### TC-07 — No-lookahead: zones/classes at as-of T use only bars ≤ T

**Type:** api
**Preconditions:**
- A fixture with bar data spanning a known range (e.g., bars for timestamps t0, t1, t2, ..., tN)
- Zones are computed with as-of time = t_k (a point in the middle of the range)

**Steps:**
1. Call `GET /research/levels?symbol=<fixture_symbol>&as_of=t_k` (truncation point in the middle)
2. Record the zones and their member levels returned
3. Call the same endpoint with as_of = t_N (all bars available)
4. Compare the two zone results

**Expected outcome:** 
The zones at as-of t_k are identical to what was computed when all bars at or before t_k were known; adding bars after t_k does not change any zone or class computed at t_k.

**Pass criteria:** 
Zones returned for as_of=t_k are unchanged when later bars are added; lookahead property verified via physical truncation test (same style as J-02 test_lookahead_free_...).

---

### TC-08 — MCP `levels` tool remains byte-identical to REST response

**Type:** api
**Preconditions:**
- Backend MCP server is running
- `GET /research/levels` is reachable
- MCP `levels` tool is available

**Steps:**
1. Call `GET /research/levels?symbol=PG&as_of=<fixture_timestamp>` via REST
2. Call the MCP `levels` tool with the same parameters (symbol, as_of)
3. Compare the returned JSON payloads

**Expected outcome:** 
The MCP response is byte-identical to the REST response, including the new `confluence_zones` field.

**Pass criteria:** 
JSON hashes match; no field reordering or value divergence; single source of truth confirmed (REST ≡ MCP).

---

### TC-09 — No-magic-numbers introspection: confluence config fields in code

**Type:** artifact
**Preconditions:**
- Source files exist: `apps/backend/app/config.py`, `apps/backend/app/research/levels.py`

**Steps:**
1. Read `apps/backend/app/config.py`
2. Identify the confluence band field(s) (e.g., `sr_confluence_band_bps`)
3. Identify the A/B/C class threshold field(s) (e.g., score cutoffs, criteria names)
4. Read `apps/backend/app/research/levels.py`
5. Grep for literal numeric thresholds (e.g., `if score > 0.75:`, `if num_timeframes >= 3:`)
6. Verify all thresholds reference config fields, not hardcoded numbers

**Expected outcome:** 
All confluence parameters are defined in `Config` and referenced by name in `levels.py`; no literal threshold numbers appear in the clustering/grading logic.

**Pass criteria:** 
Grep returns zero matches for patterns like `if.*score\s*[><=].*\d` or `if.*timeframes.*\d` in `levels.py`; every threshold is a `Config` or `self.config` attribute access.

---

### TC-10 — Config fingerprint unchanged; new fields in excluded set

**Type:** api
**Preconditions:**
- Backend is running
- `Config().config_fingerprint()` is callable
- Source file `apps/backend/app/config.py` is accessible

**Steps:**
1. Call the backend route or directly invoke `Config().config_fingerprint()`
2. Record the returned fingerprint hash
3. Read `apps/backend/app/config.py` and locate the `config_fingerprint()` method
4. Verify that new confluence config fields (e.g., `sr_confluence_band_bps`, class thresholds) are listed in the `excluded` set
5. Compare the returned hash to the expected value: `4d665603569b9dbf`

**Expected outcome:** 
The `config_fingerprint()` returns exactly `4d665603569b9dbf` (iter-1 pinned value); new confluence fields are present in the `excluded` set, same pattern as existing `sr_*` fields.

**Pass criteria:** 
Fingerprint hash matches `4d665603569b9dbf`; all new confluence fields are in the `excluded` set; a counter-test (removing a field from `excluded`) would change the hash, proving the exclusion is active.

---

### TC-11 — Honest empty zones: no_bar_series_for_symbol behavior unchanged

**Type:** api
**Preconditions:**
- A symbol with no bar series in the store is queried
- Backend is running

**Steps:**
1. Call `GET /research/levels?symbol=NOSUCHSYMBOL&as_of=<any_timestamp>`
2. Parse the response for `no_bar_series_for_symbol` and `confluence_zones` fields

**Expected outcome:** 
Response includes `no_bar_series_for_symbol: true` and `confluence_zones: []` (empty list, not null or absent).

**Pass criteria:** 
Both fields present; `no_bar_series_for_symbol` is true; `confluence_zones` is an empty array; no fabricated zone or class.

---

### TC-12 — Honest empty zones: levels but no qualifying cluster

**Type:** api
**Preconditions:**
- A symbol has levels at multiple price points with no cluster (prices far apart, outside the band)
- At most one level exists per timeframe, or no combination qualifies for clustering

**Steps:**
1. Call `GET /research/levels?symbol=<isolated_fixture_symbol>&as_of=<fixture_timestamp>`
2. Parse the response for `levels` and `confluence_zones` fields

**Expected outcome:** 
Response includes a non-empty `levels` array and an empty `confluence_zones` array (not null, not fabricated zones).

**Pass criteria:** 
`levels` is non-empty; `confluence_zones` is present and an empty array; explicit distinction between "no levels at all" and "levels but no cluster" maintained.

---

### TC-13 — Frontend files unchanged (zero diff)

**Type:** artifact
**Preconditions:**
- Git repository is available
- Iteration baseline snapshot exists (or main branch is used as baseline)

**Steps:**
1. Run: `git diff <baseline>..HEAD -- apps/frontend/`
2. Capture the output

**Expected outcome:** 
The diff is empty — no changes to any file in `apps/frontend/`.

**Pass criteria:** 
`git diff` returns no output; exit code is 0; confirms backend-only iteration (no UI change, as per spec).

---

### TC-14 — No second computation path: grep-guard for `structure_tape` and J-04 code

**Type:** artifact
**Preconditions:**
- Source files exist across the backend codebase

**Steps:**
1. Run: `grep -r "structure_tape" apps/backend/app/research/ --include="*.py"` (excluding tests and comments)
2. Run: `grep -r "GET /research/strategies" apps/backend/app/ --include="*.py"` (excluding tests)
3. Run: `grep -r "class_scaled\|scaled_by_class" apps/backend/app/research/ --include="*.py"`
4. Record any matches

**Expected outcome:** 
No matches (or only in comments/docstrings explicitly marking as "J-04, out of scope").

**Pass criteria:** 
Zero matches in active code; confirms single-source-of-truth discipline and no premature J-04 implementation.

---

## Summary

**Total test cases:** 14
- **API tests:** 8 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-10)
- **Artifact tests:** 6 (TC-09, TC-11, TC-12, TC-13, TC-14)

All tests verify the core requirements:
- Deterministic clustering and byte-identical re-runs
- Correct timeframe-weighted scoring
- Honest A/B/C grading per config criteria
- No lookahead
- Single source of truth (REST ≡ MCP)
- Config ownership (no magic numbers)
- Honest empty states
- Zero frontend change
- Grep-guarded separation from J-04
