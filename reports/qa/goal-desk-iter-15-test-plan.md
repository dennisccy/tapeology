# goal-desk-iter-15 Functional Test Plan

**Phase:** goal-desk-iter-15  
**Date:** 2026-07-29  
**Frontend Present:** yes

## Phase Goal

Disclose on every ranked row of the `/desk` briefing how many completed daily sessions (and from what start date) its wall was measured over, so the operator can distinguish short-history listings (e.g., 27 sessions) from long-history ones (e.g., 500 sessions) without leaving the page.

## Test Cases

### TC-01 — History fields derived correctly in first ranked row

**Type:** api  
**Preconditions:**  
- Fixture-scoped rig with a computed screen snapshot  
- Ranked row with `basis_as_of` resolving to a bar in a series with N bars at or before that date  

**Steps:**
1. Compute screen via `POST /research/desk/screen` or equivalent backend call
2. Retrieve the screen snapshot via `GET /research/desk/screen?date=<snapshot-date>`
3. Extract the first ranked row's `history_sessions` and `history_start` fields

**Expected outcome:**  
Ranked row carries `history_sessions == N` (where N is the count of merged 1d bars at or before `basis_as_of`) and `history_start` is the earliest such bar's timestamp formatted via the same `_iso` helper as `basis_as_of`.

**Pass criteria:**  
- `history_sessions` is a non-negative integer
- `history_start` is an ISO 8601 date-time string
- Both values correctly reflect the ascending walk over `BarStore.merged_bars(symbol, "1d")`

---

### TC-02 — Short-history and long-history rows show visibly different session counts

**Type:** api  
**Preconditions:**  
- Fixture-scoped rig with a computed screen snapshot
- Same screen includes both a member with ≤5–60 recorded daily bars and a member with ≥400 recorded daily bars

**Steps:**
1. Compute screen with two members of different history lengths
2. Extract the ranked rows for both members
3. Compare their `history_sessions` values

**Expected outcome:**  
Both rows are present in the same snapshot with visibly different (at least 10× different) `history_sessions` values reflecting each member's own recorded series length.

**Pass criteria:**  
- Short-history member's `history_sessions ≤ 60`
- Long-history member's `history_sessions ≥ 400`
- Both values present in the same JSON response, byte-identical on re-run

---

### TC-03 — Identical pins return existing snapshot unchanged, byte-identical history fields

**Type:** api  
**Preconditions:**  
- First compute completed with fixed pins (screen_date, as_of, universe_snapshot_id, config_fingerprint, bar_store_signature)
- All pins repeated exactly in a second compute call

**Steps:**
1. Run first screen compute and record snapshot filename
2. Call `GET /research/desk/screen` with identical pins
3. Record the second response and confirm no new file was written
4. Compare `history_sessions`/`history_start` on every ranked row between runs

**Expected outcome:**  
Endpoint returns the existing snapshot unchanged (same filename, no duplicate), and every ranked row's `history_sessions`/`history_start` are byte-identical to the first recording.

**Pass criteria:**  
- No new snapshot file created
- Response JSON is byte-identical
- `history_sessions` and `history_start` match exactly on all rows

---

### TC-04 — Legacy rows (pre-iteration) omit both keys entirely, never null

**Type:** api  
**Preconditions:**  
- Screen snapshot recorded BEFORE iteration 15 (no `history_sessions`/`history_start` keys on its rows)
- Legacy snapshot date known

**Steps:**
1. Call `GET /research/desk/screen?date=<legacy-date>`
2. Inspect ranked rows in the response
3. Check for presence of `history_sessions` and `history_start` keys

**Expected outcome:**  
Each ranked row in the legacy response omits both keys entirely (never present as `null`). Frontend renders such rows as `"history not recorded in this snapshot"`.

**Pass criteria:**  
- `history_sessions` key absent from every ranked row (not null)
- `history_start` key absent from every ranked row (not null)
- Legacy snapshot date confirmed < iteration 15 deployment date

---

### TC-05 — Skip rows carry neither history field

**Type:** api  
**Preconditions:**  
- Computed screen with at least one skip row (reason: `"no_bars"` or `"no_basis"`)

**Steps:**
1. Compute screen that produces skip rows
2. Extract skip rows from the response
3. Check for `history_sessions` and `history_start` fields

**Expected outcome:**  
Every skip row carries neither `history_sessions` nor `history_start` (matching the J-08 precedent for basis fields).

**Pass criteria:**  
- Skip rows have no `history_sessions` key
- Skip rows have no `history_start` key
- Ranked rows continue to carry both fields normally

---

### TC-06 — Zero extra BarStore reads per symbol

**Type:** api  
**Preconditions:**  
- Test harness can instrument `BarStore.merged_bars` calls
- Fixture-scoped screen compute with at least 5 ranked symbols

**Steps:**
1. Instrument `BarStore.merged_bars(symbol, "1d")` call counter
2. Compute screen and track calls per symbol
3. Compare call count to iteration 14 baseline

**Expected outcome:**  
Each ranked symbol shows exactly ONE `merged_bars(symbol, "1d")` call, identical to iteration 14 (no additional store read was added to derive the new fields).

**Pass criteria:**  
- Call count per symbol unchanged from baseline
- No duplicate or nested `merged_bars` calls for history derivation
- Total store reads match iteration 14 or earlier

---

### TC-07 — Single-source-of-truth cross-check with candles endpoint

**Type:** api  
**Preconditions:**  
- Computed screen snapshot with at least one ranked row
- `GET /research/candles?symbol=<sym>&timeframe=1d` endpoint accessible

**Steps:**
1. For a ranked row, extract `symbol` and `basis_as_of`
2. Call `GET /research/candles?symbol=<sym>&timeframe=1d`
3. Filter candles response to bars at or before `basis_as_of`
4. Count bars and extract earliest timestamp
5. Compare to the row's `history_sessions` and `history_start`

**Expected outcome:**  
Row's `history_sessions` equals the filtered candles count, and `history_start` equals the filtered response's earliest bar timestamp (proof of single source of truth).

**Pass criteria:**  
- `history_sessions == len(filtered_bars)`
- `history_start == earliest_bar.timestamp` (same format)
- Consistency holds for at least 3 different symbols

---

### TC-08 — Browser: History column visible with short and long rows in one screenshot

**Type:** browser  
**Preconditions:**  
- Frontend running after T-9 clean rebuild (`rm -rf apps/frontend/.next && npm run dev`)
- Backend serving a computed screen with both short-history (≤60) and long-history (≥400) members
- Screen snapshot pinned in the rig or fetched on demand

**Steps:**
1. Navigate to `http://localhost:3000/desk` in Chrome
2. Wait for ranked table to load
3. Scroll to ensure both a short-history and long-history row are visible in viewport
4. Take screenshot of ranked table

**Expected outcome:**  
Ranked table displays a `history` column (new in this iteration) with at least one row showing `history_sessions ≤ 60` and at least one row showing `history_sessions ≥ 400`, both legible in the same screenshot.

**Pass criteria:**  
- Column header labeled "history"
- At least two rows with distinct session counts (≤60 and ≥400) visible
- Session count and start date both readable in one line or via tooltip
- No layout shift or broken styling

---

### TC-09 — Browser: Composite tooltip includes history_start without click-geometry change

**Type:** browser  
**Preconditions:**  
- Frontend running after T-9 clean rebuild
- Same rig as TC-08 with computed screen loaded

**Steps:**
1. Hover over a ranked row's drill-in anchor (the row's leftmost symbol/name link)
2. Observe the composite tooltip that appears
3. Take screenshot of tooltip
4. Click the anchor to verify navigation works

**Expected outcome:**  
Composite tooltip includes that row's own `history_start` date alongside existing basis/distance/score details. Click geometry is unchanged (no new clickable element, same target area).

**Pass criteria:**  
- Tooltip displays `history_start` (ISO date-time format)
- Tooltip also shows existing fields (basis_as_of, distance, score)
- Clicking the anchor navigates as before
- No accidental input capture or expanded hit area

---

### TC-10 — Backend suite green, fingerprint unchanged, no new Config fields, MCP count stable

**Type:** api  
**Preconditions:**  
- Full backend test suite runnable
- Config sentinel and MCP tool inventory accessible

**Steps:**
1. Run backend tests: `pytest apps/backend/tests/ -v`
2. Check `Config().config_fingerprint()` output
3. Count MCP tools via `GET /research/tools` or equivalent
4. Run `tests/test_copy_discipline.py` separately
5. Verify no new Config fields introduced

**Expected outcome:**  
Full backend suite passes; `Config().config_fingerprint()` outputs `08e471b10130e1e2` (unchanged); MCP tool count is exactly 17; `tests/test_copy_discipline.py` passes unmodified.

**Pass criteria:**  
- All backend tests pass (0 failures)
- Fingerprint string matches `08e471b10130e1e2` exactly
- MCP tool count = 17
- Copy discipline lint green
- No new Config fields in `config.py`

---

### TC-11 — Demo-narrator walkthrough: New history disclosure end-to-end

**Type:** artifact  
**Preconditions:**  
- `[NEW]`-flagged demo-narrator walkthrough script recorded at `full` depth
- Fixture-scoped rig with computed screen including short- and long-history rows
- Demo-narrator lane dispatched BEFORE goal-evaluator (full depth guarantee)

**Steps:**
1. Review the recorded demo-narrator script (`runs/goal-session-desk/journey-scripts/J-11.json`)
2. Verify it contains steps narrating the history disclosure flow
3. Verify `[NEW]` flags on newly-added steps
4. Check accompanying screenshot gallery for `/desk` ranked table with history column

**Expected outcome:**  
Demo-narrator walkthrough narrates and screenshots the `/desk` briefing's history disclosure end-to-end, showing at least one short-history and one long-history row visible in the same screenshot.

**Pass criteria:**  
- Script file exists and is valid JSON
- Steps include navigation to `/desk` and observation of history column
- Screenshots show the history column with values
- At least one row with `history_sessions ≤ 60` and one with `≥ 400` both present
- No blurred or obscured data

---

## Summary

**Total test cases:** 11

**By type:**
- API tests: 7 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-10)
- Browser tests: 2 (TC-08, TC-09)
- Artifact checks: 2 (TC-11, plus TC-10 for config/fingerprint artifacts)

**Coverage:**
- Backend derivation: TC-01, TC-02, TC-03, TC-06, TC-07
- Frontend rendering: TC-08, TC-09
- Legacy compatibility: TC-04
- Skip-row edge case: TC-05
- Integrity checks: TC-10
- Product walkthrough: TC-11
