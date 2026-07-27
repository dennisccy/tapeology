# Goal-Desk-Iter-9 Functional Test Plan

**Phase:** goal-desk-iter-9 (Era B, Journey J-08)
**Date:** 2026-07-27
**Frontend Present:** yes

## Phase Goal

Add `basis_as_of` and `basis_age_days` fields to every ranked row on `/desk`, enabling operators to see how old the price reading behind each distance measurement is — so a same-day wall and an 11-day-old one are no longer indistinguishable on the ranked table's single sort key.

## Test Cases

### TC-01 — New Ranked Row basis_as_of Byte-Identity

**Type:** api
**Preconditions:** Fixture-scoped backend running; `compute_tradability` instrumented with call-counting.

**Steps:**
1. Start a fixture-scoped backend (own `.data/` copy, never ambient store).
2. Run `POST /research/desk/screen` with fixture universe and screen date.
3. Extract a ranked row from the response.
4. Query `GET /research/tradability?symbol=<row_symbol>&as_of=<snapshot_as_of>`.

**Expected outcome:** The row's `basis_as_of` is byte-identical to the tradability endpoint's `basis_as_of` for the same symbol and as-of.

**Pass criteria:** `row["basis_as_of"] == tradability_response["basis_as_of"]` (exact string match).

---

### TC-02 — basis_age_days Exact Calendar-Date Difference

**Type:** api
**Preconditions:** Fixture-scoped backend running; a ranked row with `basis_as_of` present.

**Steps:**
1. Extract `basis_as_of` (ISO date string, e.g., "2026-07-13") and the snapshot's own `as_of` from the screen response.
2. Compute calendar-day difference: `(as_of_date - basis_as_of_date).days`.
3. Compare with the row's `basis_age_days` field.

**Expected outcome:** The fields match exactly. Example: basis 2026-07-13, as-of 2026-07-25 → `basis_age_days == 12`.

**Pass criteria:** Computed difference equals row's `basis_age_days` for every ranked row in the fixture screen.

---

### TC-03 — Same-Pins Re-Run Byte-Identity, No New File

**Type:** api
**Preconditions:** Fixture-scoped backend; a screen already computed with specific pins (screen_date, as_of, universe snapshot id, config fingerprint, bar-store signature).

**Steps:**
1. Capture the snapshot id and all rows from the first screen run.
2. Re-run `POST /research/desk/screen` with identical pins.
3. Check the response's snapshot id and rows.
4. List files under `.data/screen/` before and after the re-run.

**Expected outcome:** Snapshot id unchanged; rows byte-identical including the two new fields; no new file written.

**Pass criteria:** `snapshot_id_1 == snapshot_id_2` and `rows_1 == rows_2` and `file_count_before == file_count_after`.

---

### TC-04 — Legacy Snapshot Files Byte-Identical, Fields Absent on Read

**Type:** artifact
**Preconditions:** Two real screen snapshot files recorded before this iteration exist in `.data/screen/`; SHA-256 checksum tool available.

**Steps:**
1. Compute SHA-256 checksum for each legacy snapshot file before applying this iteration's changes.
2. Apply the full iteration 9 change set.
3. Recompute checksums for the same files.
4. Query `GET /research/desk/screen?date=<legacy_date>` for each legacy snapshot.

**Expected outcome:** Checksums unchanged; response rows have `basis_as_of` and `basis_age_days` absent (not present with null, but entirely missing from the JSON keys).

**Pass criteria:** All checksums match; every legacy row lacks both keys (check with `"basis_as_of" not in row and "basis_age_days" not in row`).

---

### TC-05 — Ranked Table Basis Column Rendered for Fresh Rows

**Type:** browser
**Preconditions:** Clean rebuild (`rm -rf apps/frontend/.next` + restart both services); `/desk` loaded with a newly computed screen containing ranked rows with basis data.

**Steps:**
1. Navigate to `/desk`.
2. Locate the ranked-rows table header.
3. Verify the "basis" column is present (8th column after rank, symbol, class, distance, score, coverage, evidence).
4. Inspect a ranked row cell under the basis column for a row with `basis_age_days ≤ 2`.

**Expected outcome:** Column header reads "basis"; cell shows descriptive text like "basis 2026-07-25 · 0 d before as-of" (or similar ISO format with day count).

**Pass criteria:** The basis column is visible and renders descriptive text matching the pattern `basis YYYY-MM-DD · N d before as-of`.

---

### TC-06 — Legacy Rows Show Honest Fallback Text

**Type:** browser
**Preconditions:** `/desk` loaded; a historical screen (recorded before this iteration) selected from the history list contains ranked rows.

**Steps:**
1. Open the screen-history list on `/desk`.
2. Click a past screen recorded before this iteration.
3. Inspect a ranked row under the basis column.

**Expected outcome:** Cell displays the honest text "basis not recorded in this snapshot" (not blank, not a dash, not a computed value).

**Pass criteria:** Exact fallback text is visible and identical for every legacy row's basis column.

---

### TC-07 — Row Anchor Tooltip Includes Full-Precision Basis Detail

**Type:** browser
**Preconditions:** `/desk` with a ranked row that has basis data; row's anchor drill-in (`absolute inset-0`) is topmost (iter-6 lesson).

**Steps:**
1. Hover over any cell in a ranked row with basis data.
2. Capture the composite tooltip (row anchor's `title` attribute).
3. Verify it contains the existing distance, score, coverage text plus basis detail.
4. Hit-test with `document.elementFromPoint` at the basis column cell's center to confirm the anchor is topmost.

**Expected outcome:** Tooltip includes text like "distance 123.45 bps, score 171, basis 2026-07-25, coverage ..." and the anchor is the topmost element at the cell center.

**Pass criteria:** Tooltip text contains basis date; hit-test element tag is the drill-in anchor (`<a>` or equivalent), not the `<td>`.

---

### TC-08 — Zero Additional compute_tradability Calls

**Type:** api
**Preconditions:** Fixture-scoped backend; `compute_tradability` call-counting monkeypatch (mirrors `test_bar_store_signature_issues_zero_bar_store_calls`).

**Steps:**
1. Instrument `compute_tradability` with call counter.
2. Run `POST /research/desk/screen` with N members in the universe.
3. Record the total call count.

**Expected outcome:** Call count equals exactly N (one per member, zero extra for basis derivation).

**Pass criteria:** `call_count == universe_member_count`; no call accumulates during basis field assignment.

---

### TC-09 — Full Backend Suite Green, Fingerprint Unchanged

**Type:** api
**Preconditions:** Iteration 9 changes applied; Python test environment ready.

**Steps:**
1. Run `cd apps/backend && .venv/bin/python -m pytest tests/ -q` (full suite).
2. Check exit code and pass/skip counts.
3. Run `Config().config_fingerprint()` and capture output.

**Expected outcome:** All tests pass at or above 1341 passing / 8 skipped floor; no failures; fingerprint is exactly `08e471b10130e1e2`.

**Pass criteria:** `pytest` exit code 0; fingerprint matches literal `08e471b10130e1e2`.

---

### TC-10 — MCP desk_screen Tool Byte-Identity, 17-Tool Contract

**Type:** api
**Preconditions:** MCP server running; `test_mcp_server.py` test suite available.

**Steps:**
1. Run `tests/test_mcp_server.py` with focus on MCP tool count.
2. Call `GET /research/desk/screen` and `mcp desk_screen` with identical params.
3. Compare JSON outputs.

**Expected outcome:** Tool list reports exactly 17 tools; `desk_screen` output byte-identical to REST call; no code change to `desk_routes.py` (dict pass-through verified).

**Pass criteria:** Tool count == 17; REST and MCP JSON responses are byte-identical; test passes.

---

### TC-11 — Copy Discipline Lint Green Unmodified

**Type:** api
**Preconditions:** Test suite available; new `/desk` basis column copy added to source.

**Steps:**
1. Run `tests/test_copy_discipline.py` (frontend-literal lint).
2. Check for advice/imperative/prediction language in the new basis copy.

**Expected outcome:** Linter passes; the new column text ("basis 2026-07-25 · 12 d before as-of") contains only descriptive measurement, no urgency or action language.

**Pass criteria:** Test passes unmodified; no new lint violations detected.

---

### TC-12 — Screenshot: Fresh + Stale Rows Legible Together

**Type:** browser
**Preconditions:** Clean rebuild (`rm -rf apps/frontend/.next` + restart); scoped backend copy with natural basis-age spread (AAPL ~1d, MSFT ~4d, META/NFLX/NVDA ~12d per proposer measurement).

**Steps:**
1. Run the screen compute against the scoped backend.
2. Load `/desk` with the latest screen.
3. Take a full-page screenshot of the ranked-rows table.
4. Verify at least one row with `basis_age_days ≤ 2` and one row with `basis_age_days ≥ 10` are visible and legible in the same screenshot.

**Expected outcome:** Both fresh and stale rows visible; basis column text is readable; no overlap or clipping.

**Pass criteria:** Screenshot contains a ≤2d row (e.g., "basis 2026-07-27 · 0 d") and a ≥10d row (e.g., "basis 2026-07-15 · 12 d") with clear column headers and row identifiers.

---

### TC-13 — Smoke Replay J-01–J-07 Against Fixture

**Type:** api
**Preconditions:** Journey-scripts J-01 through J-07 exist; fixture-scoped backend available.

**Steps:**
1. Run `--mode verify --journeys J-01,J-02,J-03,J-04,J-05,J-06,J-07` against the fixture-scoped rig.
2. Check results file for pass/fail status.
3. Verify no write-path side effect on ambient `.data/`.

**Expected outcome:** Every journey reports PASS; results file exists; no new files written to the ambient `.data/` directory.

**Pass criteria:** Results show 7/7 passing; no `.data/` modifications; deterministic replay succeeds.

---

### TC-14 — J-08 Deterministic Replay Against Fixture

**Type:** api
**Preconditions:** `runs/goal-session-desk/journey-scripts/J-08.json` recorded this iteration; fixture-scoped backend ready.

**Steps:**
1. Run `--mode verify --journeys J-08` against the fixture-scoped backend.
2. Check the results file for pass status and recorded output.
3. Verify a post-match liveness assertion (the page is alive after the first matching string).

**Expected outcome:** J-08 reports PASS; results file contains the expected basis-disclosure evidence; no .data/ side effect on ambient store.

**Pass criteria:** Journey status PASS; results file exists and contains basis data; fixture backend remains clean.

---

### TC-15 — [NEW]-Flagged Demo Walkthrough of Basis Disclosure

**Type:** artifact
**Preconditions:** Demo-narrator walkthrough generation complete; `runs/goal-session-desk/` contains showcase artifacts.

**Steps:**
1. Locate the `[NEW]`-flagged walkthrough entry.
2. Verify it describes the basis-disclosure flow end-to-end.
3. Check that it covers both fresh and stale rows.

**Expected outcome:** A demo-script JSON (or text summary) exists with `[NEW]` flag, narrating the basis column and honest fallback.

**Pass criteria:** Walkthrough exists, is explicitly flagged `[NEW]`, and covers at minimum: (1) viewing a fresh row's basis age, (2) viewing a stale row's basis age, (3) legacy row fallback text.

---

### TC-16 — Zero Diff to Frozen Files

**Type:** artifact
**Preconditions:** This iteration's full diff available; `git diff` or file comparison tool ready.

**Steps:**
1. Run `git diff` and filter for `tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`.
2. Verify each file shows no changes (0 lines added/deleted).

**Expected outcome:** Each frozen file is untouched; no diff output for any of the four.

**Pass criteria:** `git diff -- tradability.py levels.py bars.py StructureChart.tsx` returns empty output.

---

## Summary

**Total test cases:** 16

| Type | Count |
|------|-------|
| API | 8 (TC-01, TC-02, TC-03, TC-04, TC-08, TC-09, TC-10, TC-11, TC-13, TC-14) |
| Browser | 4 (TC-05, TC-06, TC-07, TC-12) |
| Artifact | 4 (TC-04 checksum, TC-15, TC-16) |

**Coverage:**
- **Data model:** TC-01, TC-02, TC-03, TC-04 (schema, determinism, immutability)
- **Frontend rendering:** TC-05, TC-06, TC-07, TC-12 (column, fallback, tooltip, legibility)
- **Performance/integrity:** TC-08, TC-09, TC-10, TC-11 (call count, suite, MCP, copy)
- **Regression:** TC-13, TC-14, TC-15, TC-16 (smoke replay, new journey, walkthrough, frozen files)

**Critical path:** TC-01 → TC-02 → TC-03 → TC-04 (data integrity) + TC-05 → TC-06 (UI visibility) + TC-08 (no performance regression) + TC-09 (suite green) + TC-12 (browser proof).
