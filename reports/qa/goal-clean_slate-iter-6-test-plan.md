# goal-clean_slate-iter-6 Functional Test Plan

**Phase:** goal-clean_slate-iter-6  
**Date:** 2026-07-24  
**Frontend Present:** yes

## Phase Goal

Delete 5 orphaned Pydantic request-body classes from `routes.py`, add a structural source-introspection guard test, run an expanded orphan sweep to confirm no other dead code remains, and re-certify J-05 (regression sentinel) plus J-01–J-04 (required still-passing journeys) to close the demolition interlude with zero residue.

## Test Cases

### TC-1 — Orphaned Pydantic classes deleted

**Type:** artifact  
**Preconditions:** `apps/backend/app/research/routes.py` contains the 5 orphaned classes before deletion

**Steps:**
1. Delete `ThesisRequest` class definition (line 85) from routes.py
2. Delete `ResolveRequest` class definition (line 103) from routes.py
3. Delete `ActionRequest` class definition (line 112) from routes.py
4. Delete `StudyRequest` class definition (line 122) from routes.py
5. Delete `ReviewRequest` class definition (line 208) from routes.py
6. Run grep: `grep -c "class ThesisRequest\|class ResolveRequest\|class ActionRequest\|class StudyRequest\|class ReviewRequest" apps/backend/app/research/routes.py`

**Expected outcome:** All 5 classes removed from the file; grep returns 0 matches

**Pass criteria:** `grep -c` command output is exactly `0`

---

### TC-2 — Remaining request classes are referenced

**Type:** api  
**Preconditions:** The 5 orphaned classes have been deleted; remaining `BaseModel` classes in routes.py are: `BacktestRequest`, `DatasetRecordRequest`, `BarRecordRequest`, `EdgeReportComputeRequest`

**Steps:**
1. Run: `grep -n "^class .*BaseModel" apps/backend/app/research/routes.py` to list all remaining classes
2. For each remaining class, run: `grep -c "ClassName" apps/backend/app/research/routes.py`
3. Verify each class shows exactly 2 occurrences (its definition line + at least one live `body:` route parameter)

**Expected outcome:** Every remaining `BaseModel` class occurs 2 or more times; zero classes show exactly 1 occurrence

**Pass criteria:** All 4 remaining classes show 2+ occurrences; no class shows a single occurrence

---

### TC-3 — Deleted module symbols are unreferenced

**Type:** api  
**Preconditions:** Routes have been cleaned up; the 11 deleted modules are no longer imported anywhere

**Steps:**
1. Run grep across `apps/` (excluding `reports/`, `runs/`, `docs/goal-archive/`): `grep -r "ThesisRecord\|VerdictEventRecord\|ActionRecord\|StudyRecord\|HintRecord\|study_jobs\|hint_projection_for\|startup_sweep" apps/ --include="*.py" --include="*.ts" --include="*.tsx" | grep -v docstring | grep -v comment`
2. Run grep for I-7 deleted frontend types: `grep -r "ThesisVerdict\|ThesisStatement\|ThesisMarks\|ThesisGeometry\|ThesisProjection\|Hint" apps/frontend/lib/types.ts apps/frontend/lib/api.ts apps/frontend/app/ --include="*.ts" --include="*.tsx" | grep -v docstring | grep -v comment`

**Expected outcome:** Zero live (non-docstring/non-comment) references to any deleted-module symbols

**Pass criteria:** Both greps return zero hits (or only hits in comments/docstrings)

---

### TC-4 — New guard test catches orphaned classes

**Type:** api  
**Preconditions:** New file `apps/backend/tests/test_routes_no_orphaned_request_models.py` exists and contains a structural guard test

**Steps:**
1. Run the new guard test: `pytest apps/backend/tests/test_routes_no_orphaned_request_models.py -v`
2. Confirm the test passes with the current (post-cleanup) routes.py
3. Manually verify the test's logic: parse routes.py for all `class X(BaseModel):` definitions and all route-handler parameters using those classes
4. Re-apply the test logic to a copy of pre-cleanup routes.py (with the 5 orphaned classes present)
5. Verify the test logic would have flagged all 5 just-deleted classes as unreferenced

**Expected outcome:** Test passes on current routes.py; test logic (if re-applied to pre-cleanup version) would catch the 5 orphaned classes

**Pass criteria:** (1) `pytest` exit code 0; (2) test constructs its assertions structurally, never by hardcoding class names as strings; (3) manual re-application confirms it would have failed on pre-cleanup file

---

### TC-5 — Full backend test suite passes

**Type:** api  
**Preconditions:** All code changes (deletion of 5 classes, new guard test) are complete; backend is running on committed fixtures

**Steps:**
1. Run: `cd apps/backend && pytest --tb=short 2>&1`
2. Capture full stdout/stderr
3. Count passed/failed/skipped test results

**Expected outcome:** All tests pass; exit code 0; `0 failed` in output

**Pass criteria:** Exit code is 0; output contains `0 failed` and shows no FAILED markers

---

### TC-6 — Config fingerprint unchanged

**Type:** api  
**Preconditions:** Backend is running; Config class is initialized on current codebase

**Steps:**
1. Run Python: `python3 -c "from apps.backend.app.config import Config; print(Config().config_fingerprint())"`
2. Compare result to expected value `08e471b10130e1e2`

**Expected outcome:** Fingerprint matches exactly `08e471b10130e1e2`

**Pass criteria:** Printed fingerprint is exactly `08e471b10130e1e2` (byte-identical)

---

### TC-7 — Guard and chart-guard test files unchanged

**Type:** api  
**Preconditions:** All named test files exist; git repository is clean before iteration

**Steps:**
1. Run in isolation: `pytest apps/backend/tests/test_no_execution_path.py -v`
2. Run in isolation: `pytest apps/backend/tests/test_no_credential_in_artifacts.py -v`
3. Run in isolation: `pytest apps/backend/tests/test_cockpit_chart_upgrade.py -v`
4. Run in isolation: `pytest apps/backend/tests/test_structure_chart_viewport.py -v`
5. Run in isolation: `pytest apps/backend/tests/test_price_chart_confluence.py -v`
6. Run in isolation: `pytest apps/backend/tests/test_backtests.py::*guard* -v` (pinned guard blocks)
7. Run in isolation: `pytest apps/backend/tests/test_setups.py::*guard* -v` (pinned guard blocks)
8. For each file, run: `git diff apps/backend/tests/<filename>`

**Expected outcome:** All tests pass; `git diff` output is empty on each file

**Pass criteria:** Each test exits 0 (PASS); each `git diff` is empty (zero bytes changed)

---

### TC-8 — Deleted module imports absent

**Type:** api  
**Preconditions:** All code cleanup complete

**Steps:**
1. Run: `grep -r "from.*\(journal_rows\|monitor\|hints\|stance\|verdict\|grades\|marks\|excursions\|execution_checks\|analytics\|studies\)" apps/ --include="*.py"`

**Expected outcome:** Zero import statements found for any of the 11 deleted modules

**Pass criteria:** Grep returns zero hits

---

### TC-9 — J-05 golden replay passes

**Type:** browser  
**Preconditions:** Frontend built fresh (`rm -rf apps/frontend/.next`); backend running; `journey-scripts/J-05.json` exists with golden replay steps

**Steps:**
1. Clear frontend build: `rm -rf apps/frontend/.next`
2. Start frontend: `npm run dev` from `apps/frontend/` (or via the project's start-frontend.sh)
3. Start backend: `uvicorn --port 8301` from `apps/backend/` (or via the project's start script)
4. Run deterministic replay: `python3 scripts/automation/replay_journey.py runs/goal-session-clean_slate/journey-scripts/J-05.json`
5. Verify each step: cockpit shows "Buyer Control" text after watching SIM-BUYER; tape-bar-size control shows "Logical 30s bars built live from the tape."; "Stop watching" returns to "No ticker watched"; /structure Load for AAPL as-of 2026-06-22T21:00:00Z shows "300.11"; clicking a case-studies-row opens case-drillin element

**Expected outcome:** All replay steps pass; no assertion failures

**Pass criteria:** Replay script exits 0; every step in J-05.json achieves its expected condition

---

### TC-10 — Edge Report honest state visible

**Type:** browser  
**Preconditions:** Backend and frontend running; `/structure` page loads; Edge Report section is visible

**Steps:**
1. Navigate to `/structure` in the running frontend
2. Scroll to Edge Report section
3. Take a screenshot of the Edge Report panel
4. Verify panel shows either: (a) populated edge cells with data, or (b) the exact text "Edge report not computed yet." with a visible Compute button

**Expected outcome:** Edge Report panel is rendered and shows one of the two honest states

**Pass criteria:** Screenshot saved to `reports/qa/goal-clean_slate-iter-6-evidence/TC-10-edge-report.png`; panel text contains "Edge report not computed yet." OR edge cells are populated; Compute button is visible if no cells are populated

---

### TC-11 — Top navigation shows two items

**Type:** browser  
**Preconditions:** Frontend rebuilt and running; `/` (Cockpit) page loads

**Steps:**
1. Navigate to `/` (Cockpit page)
2. Inspect top navigation bar
3. Count the rendered navigation items
4. Take a screenshot

**Expected outcome:** Exactly 2 nav items are visible: "Cockpit" and "Structure"

**Pass criteria:** Screenshot saved to `reports/qa/goal-clean_slate-iter-6-evidence/TC-11-nav.png`; visual count is exactly 2; no additional nav items present

---

### TC-12 — Deleted routes return 404; slimmed taxonomy returns 200

**Type:** api  
**Preconditions:** Backend running; routes have been deleted per spec

**Steps:**
1. For each of the 14 deleted I-1 routes (e.g., GET /research/journal, GET /research/analytics, POST /research/studies), run: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8301/<route>`
2. Run: `curl -s http://localhost:8301/research/taxonomy | jq .`
3. Verify taxonomy response contains only `feed_basis` and `source` labels fields

**Expected outcome:** All 14 deleted routes return HTTP 404; /research/taxonomy returns HTTP 200 with slimmed payload

**Pass criteria:** All 14 curl status codes are 404; taxonomy response is 200 and contains feed_basis + source_labels only (no journal, analytics, studies fields)

---

### TC-13 — MCP tool list matches spec

**Type:** api  
**Preconditions:** MCP server initialized; backend running

**Steps:**
1. Run: `python3 -c "from apps.backend.mcp_server import list_tools; print(list_tools())"`
2. Count the number of tools returned
3. Verify all tool names match the I-6 specification (15 tools: bars, backtests, datasets, edge_report, get_endpoint, levels, pnl_ledger, setups, strategies, tape_features, tape_history, tape_state, taxonomy, tradability, ui_route_map)

**Expected outcome:** Exactly 15 tools returned; no journal, analytics, studies, monitor, or other deleted-module tools present

**Pass criteria:** Tool count is 15; all returned tool names are in the I-6 approved list; no extra tools

---

### TC-14 — Metadata and fingerprint test files pass

**Type:** api  
**Preconditions:** All named test files exist; backend is running on committed fixtures

**Steps:**
1. Run in isolation: `pytest apps/backend/tests/test_mcp_server.py -v`
2. Run in isolation: `pytest apps/backend/tests/test_meta_routes.py -v`
3. Run in isolation the 8 fingerprint-pin-site test files (identified in iter-5 cleanup)
4. For each file, run: `git diff apps/backend/tests/<filename>`

**Expected outcome:** All tests pass; git diff shows zero changes on each file

**Pass criteria:** Each test exits 0 (PASS); each `git diff` is empty

---

### TC-15 — Diff-vs-inventory crosscheck is clean

**Type:** artifact  
**Preconditions:** `runs/goal-session-clean_slate/iter-5/diff-vs-inventory-crosscheck.md` exists as the prior baseline; this iteration's cleanup is complete

**Steps:**
1. Regenerate `runs/goal-session-clean_slate/iter-6/diff-vs-inventory-crosscheck.md`, extending iter-5's version
2. Add this iteration's orphan-sweep results (TC-3 grep output)
3. Add routes.py delta (the 5 deleted classes + docstrings)
4. Add the one new test file (`test_routes_no_orphaned_request_models.py`)
5. Verify every file in the cumulative diff matches an inventory entry from I-1 through I-9, plus the new guard test

**Expected outcome:** All changes in the crosscheck align with known deletions and the one new test file; zero unexpected/out-of-inventory changes

**Pass criteria:** Crosscheck document explicitly states "zero out-of-inventory changes" or equivalent; every listed file is accounted for in the inventory

---

### TC-16 — README stale prose removed

**Type:** artifact  
**Preconditions:** `README.md` exists; planning-time grep found zero "pending an operator decision" occurrences (already clean)

**Steps:**
1. Run: `grep -c "pending an operator decision" README.md`
2. If count is 0: record as "verified, no edit needed"
3. If count is > 0: locate the 3 sentences (~lines 51, 55, 56) and reword to accurately describe Case Studies and Edge Report as rendered, reachable `/structure` sections

**Expected outcome:** Zero occurrences of "pending an operator decision" in the file

**Pass criteria:** `grep -c` command output is `0`

---

### TC-17 — Historical records untouched

**Type:** artifact  
**Preconditions:** All code changes are complete; git diff is ready to inspect

**Steps:**
1. Run: `git diff docs/goal-archive/`
2. Run: `git diff runs/goal-session-clean_slate/iter-0/ runs/goal-session-clean_slate/iter-1/ ... runs/goal-session-clean_slate/iter-5/`
3. Run: `git diff reports/pnl/pnl-history.md` (check only pre-iteration-6 rows)
4. Verify all three diffs are empty

**Expected outcome:** Zero bytes changed in any historical directory or record

**Pass criteria:** All three `git diff` outputs are empty (no output or "no changes")

---

### TC-18 — Required-still-passing journeys (J-01, J-02, J-03, J-04) pass

**Type:** browser  
**Preconditions:** Backend running; existing golden replays exist for J-01–J-04

**Steps:**
1. For J-02 and J-05: run deterministic replay of existing `journey-scripts/J-0X.json` golden scripts
2. For J-01, J-03, J-04 (keyless surfaces with no dedicated golden replay): perform LLM-fallback confirmatory touch: nav item count, MCP tool count, 404 sweep for deleted routes
3. Verify no regression in kept surfaces

**Expected outcome:** J-02 and J-05 replay passes; J-01/J-03/J-04 confirmatory checks pass (nav shows Cockpit/Structure, MCP list has 15 tools, deleted routes return 404)

**Pass criteria:** Replay exits 0 for J-02/J-05; LLM-fallback checks confirm no regression on J-01/J-03/J-04

---

## Summary

**Total test cases:** 18  
**API tests:** 9 (TC-2, TC-3, TC-4, TC-5, TC-6, TC-8, TC-12, TC-13, TC-14)  
**Browser tests:** 4 (TC-9, TC-10, TC-11, TC-18)  
**Artifact checks:** 5 (TC-1, TC-7, TC-15, TC-16, TC-17)

All test cases derive directly from the DEFINITION OF DONE section of the phase spec and are designed to verify the complete removal of orphaned code, the addition of a durable guard test, and full regression coverage of the kept journeys (J-01–J-05).
