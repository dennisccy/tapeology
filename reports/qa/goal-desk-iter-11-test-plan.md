# goal-desk-iter-11 Functional Test Plan

**Phase:** goal-desk-iter-11 (Era B iteration 11)  
**Date:** 2026-07-28  
**Frontend Present:** yes

## Phase Goal

Provide a durable, append-only record of every top-up run's outcome (reused/fetched/failed pairs with vendor details and unreached-pair counts) surfaced on `/desk`, so run outcomes persist beyond the in-flight compute snapshot's lifetime.

## Test Cases

### TC-01 — Honest-empty runs endpoint before any run

**Type:** api  
**Preconditions:** A fixture-scoped backend with no top-up run ever executed; `GET /research/desk/topup/runs` endpoint available.

**Steps:**
1. Call `curl -s http://localhost:8301/research/desk/topup/runs`
2. Capture the response status code and body

**Expected outcome:** HTTP 200 with body `{"runs": [], "latest": null}`  
**Pass criteria:** Status is 200; body is exactly `{"runs": [], "latest": null}` (empty runs list, null latest).

---

### TC-02 — Manager-triggered run produces byte-identical outcomes

**Type:** api  
**Preconditions:** A fixture-scoped backend with a registered universe snapshot; no prior run recorded.

**Steps:**
1. Trigger a top-up run via `DeskTopupComputeManager.trigger()` and wait for completion.
2. Capture the return value of `run_topup()` during that run.
3. Call `curl -s http://localhost:8301/research/desk/topup/runs`
4. Compare the `latest.outcomes` list from the response to the captured `run_topup()` return value.

**Expected outcome:** The persisted `latest.outcomes` array is byte-identical (same `symbol`/`timeframe`/`outcome`/`detail` values in the same order) to `run_topup()`'s return for that walk.  
**Pass criteria:** Every entry in `outcomes` matches the corresponding entry from `run_topup()` in symbol, timeframe, outcome type, and detail string (where present).

---

### TC-03 — CLI-triggered run uses the same shared writer schema

**Type:** api  
**Preconditions:** A fixture-scoped backend with a registered universe snapshot; no prior run recorded.

**Steps:**
1. Run the CLI entry point: `python -m app.research.desk_topup_compute` in the fixture-scoped backend environment.
2. Wait for completion.
3. Call `curl -s http://localhost:8301/research/desk/topup/runs`
4. Inspect the `latest` record's field names and types.
5. Compare the schema to a known manager-triggered record's schema (field names, field types).

**Expected outcome:** The persisted run record's `outcomes` list has identical field names and types as a manager-triggered record's `outcomes` list.  
**Pass criteria:** Both records have the same set of fields (`symbol`, `timeframe`, `outcome`, `detail`) with identical types; proving one shared writer.

---

### TC-04 — Cancelled run records lower attempted count

**Type:** api  
**Preconditions:** A fixture-scoped backend with a registered universe snapshot; a top-up run in progress.

**Steps:**
1. Trigger a top-up run via `DeskTopupComputeManager.trigger()`.
2. Signal a cancel mid-walk (before all pairs are processed).
3. Wait for the cancel to complete.
4. Call `curl -s http://localhost:8301/research/desk/topup/runs`
5. Inspect `latest.state` and `latest.pairs_attempted` vs `latest.pairs_total`.

**Expected outcome:** The persisted record's `state` is exactly `"cancelled"` and `pairs_attempted` is strictly less than `pairs_total`.  
**Pass criteria:** `state == "cancelled"` and `pairs_attempted < pairs_total`.

---

### TC-05 — Failed pair recorded with verbatim detail; walk continues

**Type:** api  
**Preconditions:** A fixture-scoped backend with a registered universe snapshot and configured to induce a fetch failure on one pair (via monkeypatch using the existing Yahoo-adapter known failure taxonomy or the existing test fixture technique).

**Steps:**
1. Trigger a top-up run via `DeskTopupComputeManager.trigger()` or CLI.
2. Wait for the run to complete (despite the induced failure).
3. Call `curl -s http://localhost:8301/research/desk/topup/runs`
4. Inspect `latest.outcomes` for the failed pair's entry.
5. Verify that pairs after the failed pair are still present in `outcomes`.

**Expected outcome:** The failed pair's entry has `outcome: "failed"` with a `detail` string matching the induced error message verbatim; all pairs processed after the failure are still present in `outcomes`.  
**Pass criteria:** One entry has `outcome: "failed"` with non-empty `detail` matching the injected error; the `outcomes` list contains entries after it.

---

### TC-06 — Second run appends; first file checksum unchanged

**Type:** api  
**Preconditions:** A fixture-scoped backend with one already-persisted run record on disk (checksum known); a second run about to be triggered.

**Steps:**
1. Record the sha256 checksum of the first run's file on disk.
2. Trigger a second top-up run and wait for completion.
3. Call `curl -s http://localhost:8301/research/desk/topup/runs`
4. Verify the `runs` list has 2 entries.
5. Re-verify the first record's file on disk has its original sha256 checksum.
6. Confirm `latest` reflects the second (newer) run.

**Expected outcome:** The `runs` list has exactly 2 entries; the first record's file is unchanged on disk (same sha256); `latest` ID matches the second run.  
**Pass criteria:** `len(runs) == 2`; first file sha256 unchanged; `latest.id` differs from `runs[0].id`.

---

### TC-07 — Interrupted run (no terminal write) leaves zero record

**Type:** api  
**Preconditions:** A fixture-scoped backend; ability to simulate a process exit before the writer's terminal call.

**Steps:**
1. Trigger a top-up run via `DeskTopupComputeManager.trigger()` or CLI.
2. Simulate a process termination before the writer's terminal call completes (e.g., via mock/monkeypatch that prevents the write).
3. Call `curl -s http://localhost:8301/research/desk/topup/runs`
4. Inspect the `runs` list.

**Expected outcome:** The `runs` list has zero entries for that interrupted run (no fabricated or partial record created).  
**Pass criteria:** `len(runs) == 0` (or unchanged from before the interrupted run).

---

### TC-08 — GET never triggers an auto-compute

**Type:** api  
**Preconditions:** A fixture-scoped backend with zero runs recorded.

**Steps:**
1. Call `curl -s http://localhost:8301/research/desk/topup/runs` multiple times.
2. After each call, check the in-flight compute snapshot by calling `curl -s http://localhost:8301/research/desk/topup/compute`

**Expected outcome:** The compute snapshot remains `null` after any number of `GET /research/desk/topup/runs` calls.  
**Pass criteria:** `GET .../topup/compute` returns `null` every time (no side-effect compute triggered).

---

### TC-09 — MCP tool count unchanged; get_endpoint reaches new path

**Type:** api  
**Preconditions:** A fixture-scoped backend with the MCP server running; `test_mcp_server.py` available.

**Steps:**
1. Run `pytest tests/test_mcp_server.py::test_mcp_tools_contract -v` (or the MCP tool registry check in the test suite).
2. Verify `EXPECTED_TOOLS` count is exactly 17.
3. Call the MCP `get_endpoint` function with `path="/research/desk/topup/runs"`.
4. Compare the returned JSON body to a direct `GET /research/desk/topup/runs` call (curl).

**Expected outcome:** The MCP tool count is exactly 17 (unchanged); `get_endpoint` with the new path returns identical JSON to a direct HTTP GET.  
**Pass criteria:** Tool count == 17; MCP response body == HTTP GET response body (byte-identical JSON).

---

### TC-10 — Suite, config, and frozen files unchanged

**Type:** api  
**Preconditions:** A fixture-scoped backend with all code changes applied.

**Steps:**
1. Run the full backend test suite: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
2. Run `Config().config_fingerprint()` and capture output.
3. Run `git diff --stat tradability.py levels.py bars.py StructureChart.tsx` from the repo root.

**Expected outcome:** Suite passes at or above 1346 passing / 8 skipped with 0 failures; config fingerprint is exactly `08e471b10130e1e2`; git diff is empty for all four frozen files.  
**Pass criteria:** pytest exit code 0; fingerprint output == `08e471b10130e1e2`; git diff shows no lines changed for any of the four files.

---

### TC-11 — Copy discipline unchanged

**Type:** api  
**Preconditions:** The new "Top-up Runs" section added to `/desk`; `test_copy_discipline.py` available.

**Steps:**
1. Run `pytest tests/test_copy_discipline.py -v`
2. Capture the output.

**Expected outcome:** All tests pass (zero advice/imperative/prediction-language literals flagged in the new panel's copy).  
**Pass criteria:** pytest reports 0 failures; all assertions pass.

---

### TC-12 — Browser: Honest empty Top-up Runs state (no run recorded)

**Type:** browser  
**Preconditions:** A fixture-scoped backend with a registered universe snapshot and zero top-up runs recorded; `/desk` page accessible at `http://localhost:3000/desk`.

**Steps:**
1. Navigate to `http://localhost:3000/desk` on the fixture-scoped rig.
2. Wait for the page to fully load.
3. Locate the "Top-up Runs" section on the page.
4. Take a screenshot of the section showing the empty state.
5. Verify the empty-state text is visible and no run rows are rendered.

**Expected outcome:** A screenshot shows the "Top-up Runs" section with honest empty-state descriptive copy and zero run rows.  
**Pass criteria:** Screenshot file saved to `reports/qa/goal-desk-iter-11-evidence/TC-12-empty-topup-runs.png`; the section title and empty-state message are both legible.

---

### TC-13 — Browser: Populated Top-up Runs with failed pair detail legible

**Type:** browser  
**Preconditions:** A fixture-scoped backend with one completed top-up run that includes at least one `failed` pair (failure induced via monkeypatch per TC-05 technique); `/desk` page accessible.

**Steps:**
1. Trigger the fixture-scoped top-up run (with induced failure) via the manager or CLI if not already done.
2. Navigate to `http://localhost:3000/desk` on the fixture-scoped rig.
3. Wait for the page to fully load and the new run data to render.
4. Locate the "Top-up Runs" section.
5. Verify the run row displays: date+id, universe snapshot id, terminal state, attempted-of-total pairs, counts by outcome.
6. Verify the latest run's failed pair's detail text is rendered and fully legible (not truncated).
7. Take a screenshot capturing the run row and the failed pair's detail in one image.

**Expected outcome:** A screenshot shows the "Top-up Runs" section with one run row containing all metadata and the failed pair's verbatim detail string legible.  
**Pass criteria:** Screenshot file saved to `reports/qa/goal-desk-iter-11-evidence/TC-13-populated-topup-runs.png`; the following are all visible: run date, run id, universe snapshot id, state (`done`/`cancelled`/`failed`), attempted/total pairs, per-outcome counts, and the failed pair's detail string (not truncated or hidden).

---

### TC-14 — Store directory resolves correctly; no new Config field

**Type:** api  
**Preconditions:** A fixture-scoped backend; `desk_universe_dir_resolved()` and the new store's resolution function available.

**Steps:**
1. Call `resolve_desk_topup_log_dir(desk_universe_dir_resolved())` or equivalent.
2. Verify the returned directory is a sibling of `desk_universe_dir_resolved()` (follows `resolve_desk_screen_dir` pattern).
3. Run `Config().config_fingerprint()` and verify it still outputs `08e471b10130e1e2`.
4. Confirm no new `Config` field was added in `app/config.py`.

**Expected outcome:** The store directory is a sibling of the universe dir; the config fingerprint is unchanged; no new field added to `Config`.  
**Pass criteria:** Store dir path contains the same parent as universe dir; fingerprint output == `08e471b10130e1e2`; git diff for config.py shows no new field in the class definition.

---

### TC-15 — J-09 golden replay verifies without errors

**Type:** artifact  
**Preconditions:** `runs/goal-session-desk/journey-scripts/J-09.json` recorded this iteration; a fixture-scoped backend matching the golden's scope.

**Steps:**
1. Run the deterministic replay in verify mode: `--mode verify --journeys J-09` against the fixture-scoped backend.
2. Capture the exit code and results file output.
3. Inspect the results report for any failed steps.

**Expected outcome:** The replay reports 0 failed steps; results file is saved successfully.  
**Pass criteria:** Exit code 0; results JSON file contains no "failed" entries; the report summary shows "PASS".

---

### TC-16 — Demo-narrator [NEW] walkthrough for top-up-run disclosure

**Type:** artifact  
**Preconditions:** The iteration's showcase artifacts to be generated; `[NEW]`-flagged entries expected.

**Steps:**
1. Check the generated demo-narrator walkthrough (e.g., `runs/goal-session-desk/showcase/demo-narrative.json` or similar).
2. Search for entries flagged with `[NEW]`.
3. Verify one entry describes the top-up-run disclosure end to end (empty run history state → populated with a failed pair).

**Expected outcome:** A `[NEW]`-flagged walkthrough entry exists describing the top-up-run disclosure.  
**Pass criteria:** The showcase artifacts file contains at least one `"[NEW]"` entry with a narrative covering the empty state and the populated state with failed pair detail.

---

### TC-17 — J-01–J-08 smoke-replay passes against scoped rig

**Type:** browser  
**Preconditions:** The same fixture-scoped backend used for TC-12/TC-13; `journey-scripts/J-01.json` through `J-08.json` available; deterministic replay lane ready.

**Steps:**
1. Run the deterministic replay lane for J-01–J-08 against the fixture-scoped backend named explicitly in the dispatch.
2. Capture the results for each journey.
3. Verify no write-path side effect on the ambient `.data/` store (check file timestamps/sizes before and after).

**Expected outcome:** All eight journeys report PASS (or LLM fallback PASS where no golden exists); no changes to ambient `.data/` store files.  
**Pass criteria:** Each of J-01–J-08 has a passing verdict; `.data/` directory contents remain unchanged (checksum or file timestamp comparison shows no mutations).

---

## Summary

| Category | Count |
|----------|-------|
| **Total test cases** | 17 |
| **API tests** | 11 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11) |
| **Browser tests** | 2 (TC-12, TC-13) |
| **Artifact checks** | 4 (TC-14, TC-15, TC-16, TC-17) |

**Key test coverage:**
- **Endpoint behavior:** Honest-empty state, correct response shape, no auto-compute side effects, MCP compatibility
- **Data integrity:** Byte-identical outcomes, shared writer contract (manager + CLI), append-only discipline, checksum preservation
- **Error handling:** Cancelled runs, failed pairs with detail preservation, interrupted runs leave no record
- **UI visibility:** Empty state and populated state with failed pair detail legible in browser
- **Regression:** Suite passes, frozen files unchanged, copy discipline maintained, J-01–J-08 remain green
