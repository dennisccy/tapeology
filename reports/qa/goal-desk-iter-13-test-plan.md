# goal-desk-iter-13 Functional Test Plan

**Phase:** goal-desk-iter-13  
**Date:** 2026-07-28  
**Frontend Present:** yes

## Phase Goal

Produce the one remaining artifact `docs/goal.md`'s J-09 acceptance text requires: a `[NEW]`-flagged demo-narrator walkthrough that shows the honest "No top-up runs recorded yet." state and a populated Top-up Runs state (attempted-of-total, per-outcome counts, a failed pair's detail) in ONE artifact, in sequence — with zero product-code change. Key fix: correct capture order (boot frontend BEFORE recording runs, capture empty state on live rig BEFORE any write).

## Test Cases

### TC-01 — Fresh scoped root with both processes booted, zero runs recorded

**Type:** api  
**Preconditions:** 
- A fresh scoped root (`desk-iter13-scoped-qa`) has been seeded via `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh`
- Both scoped backend (`:8301`) and scoped frontend (`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301`) are booted and ready
- No top-up run has been recorded into this rig

**Steps:**
1. Run `curl -s http://localhost:8301/research/desk/topup/runs | jq .` on the scoped backend
2. Verify the response contains exactly `{"runs": [], "latest": null}`
3. Verify the `/desk` page is live and reachable at `http://localhost:3301/desk`
4. Take a browser screenshot of the `/desk` page showing the Top-up Runs section

**Expected outcome:** 
- Backend endpoint returns empty runs list with null latest
- Frontend `/desk` page renders the honest "No top-up runs recorded yet." state
- Screenshot legibly shows the empty panel

**Pass criteria:** 
- HTTP 200 status code
- Response JSON contains `"runs": []` and `"latest": null` exactly
- Screenshot clearly shows "No top-up runs recorded yet." text
- Frontend was booted and alive at the moment the screenshot was captured (not before)

---

### TC-02 — Same rig, three checkpoint runs recorded, state persists on rig

**Type:** api  
**Preconditions:** 
- TC-01's rig is still live and serving both backend and frontend
- The scoped rig's store is still empty (no runs yet)

**Steps:**
1. Record three checkpoint top-up runs into the SAME scoped root via in-process `DeskTopupComputeManager.trigger()`:
   - Run 1: ordinary run with all pairs successful (`pairs_attempted == pairs_total`, `state: done`, all outcomes `"fetched"` or `"reused"`)
   - Run 2: run cancelled mid-walk (`pairs_attempted < pairs_total`, `state: cancelled`)
   - Run 3: run with at least one induced `failed` pair carrying non-null verbatim `detail` (via monkeypatched adapter)
2. After all three runs are recorded, run `curl -s http://localhost:8301/research/desk/topup/runs | jq '.runs | length'` to count the runs
3. Run `curl -s http://localhost:8301/research/desk/topup/runs | jq '.latest.outcomes[] | select(.outcome == "failed") | .detail'` to extract a failed pair's detail
4. Confirm the backend and frontend processes are still the same (no restart/swap)

**Expected outcome:** 
- Backend returns a list of exactly 3 runs
- The latest run (run 3) has outcomes including at least one `"failed"` entry with non-null `detail`
- The same scoped rig (same processes, same root) continues to serve the frontend
- All three runs are persisted in the scoped root's `topup_runs` ledger file

**Pass criteria:** 
- `GET /research/desk/topup/runs` returns exactly 3 entries in the `runs` array
- `latest.outcomes` includes at least one entry with `outcome: "failed"` and non-null, non-empty `detail` string
- The same backend PID and frontend PID are still running
- No process restart log entries between TC-01's capture and this test

---

### TC-03 — Same rig, same frontend still live, `/desk` reloaded shows populated state

**Type:** browser  
**Preconditions:** 
- TC-02's three runs are recorded into the scoped rig
- The scoped frontend (`:3301`) is still running and has never been restarted since TC-01
- The scoped backend (`:8301`) is still running and has never been restarted

**Steps:**
1. Navigate to `/desk` on the still-live scoped frontend
2. Reload the page (`F5` or `Cmd+R`)
3. Wait for the Top-up Runs section to render
4. Take a screenshot capturing the populated Top-up Runs panel

**Expected outcome:** 
- The `/desk` page loads successfully
- The Top-up Runs section displays:
  - A visible list of runs (at least 3 rows)
  - The latest run's attempted-of-total pair count (e.g., "3 of 3 pairs attempted")
  - Per-outcome counts (number of reused, fetched, failed pairs)
  - The failed pair's recorded detail text, legible in the same screenshot

**Pass criteria:** 
- Screenshot shows the attempted-of-total count visible on the latest run row
- Screenshot shows at least three distinct outcome-count labels (reused, fetched, failed)
- Screenshot shows non-empty detail text for at least one failed pair
- All text is legible and not obscured or clipped

---

### TC-04 — Demo-narrator walkthrough assembled, both captures in sequence

**Type:** artifact  
**Preconditions:** 
- TC-01's empty-state screenshot is on disk
- TC-03's populated-state screenshot is on disk
- Both screenshots were captured from the same scoped rig

**Steps:**
1. Locate the demo-narrator walkthrough artifact (`reports/phase-goal-desk-iter-11-demo.json`, `reports/phase-goal-desk-iter-13-demo.json`, or another equivalent)
2. Verify it contains a `[NEW]`-flagged J-09 step (or steps) for this iteration
3. Extract the J-09 section and confirm it includes both screenshots
4. Verify the screenshots are ordered: empty state first, populated state second
5. Read the narration text for each step

**Expected outcome:** 
- The walkthrough artifact contains at least one J-09 entry marked `[NEW]`
- Both the empty and populated screenshots are referenced
- The screenshots are in the correct order (empty before populated)
- The narration matches what each paired screenshot actually displays

**Pass criteria:** 
- The artifact is valid JSON with no parse errors
- The J-09 section contains exactly two steps (or one step with two substeps) showing both states
- The `[NEW]` flag is present on the J-09 entry
- The step order is: empty state narration + empty screenshot, then populated state narration + populated screenshot
- Narration text for empty state mentions "No top-up runs" or similar
- Narration text for populated state mentions the run counts, outcomes, or detail text visible in the screenshot

---

### TC-05 — Demo report and QA evidence report both name the scoped-root path

**Type:** artifact  
**Preconditions:** 
- The demo/showcase report has been written (`reports/phase-goal-desk-iter-13-demo.json` or equivalent)
- A browser-QA/evidence report has been written (if applicable)

**Steps:**
1. Open the demo report file
2. Search for an absolute filesystem path string (e.g., `/home/.../.../desk-iter13-scoped-qa` or similar)
3. Confirm the path is mentioned explicitly at least once
4. Open the browser-QA/evidence report (if it exists)
5. Search for the same or similar scoped-root path

**Expected outcome:** 
- Both reports explicitly state the absolute path of the scoped data root used for the walkthrough captures
- The path appears in plain text, not just in a code snippet or filename

**Pass criteria:** 
- Demo report contains a line stating the scoped-root path (e.g., "Scoped root: /absolute/path/to/desk-iter13-scoped-qa")
- QA evidence report (if written) also states the same scoped-root path
- Both paths refer to the same directory used for TC-01 through TC-03

---

### TC-06 — Ambient data tree unchanged (file listing and SHA-256 checksums identical before and after)

**Type:** api  
**Preconditions:** 
- A SHA-256 checksum of every file in `apps/backend/.data/` was captured BEFORE iteration 13 began
- All work in TC-01 through TC-05 has completed

**Steps:**
1. Run `find apps/backend/.data -type f -exec sha256sum {} \; | sort > /tmp/after-iter13.txt`
2. Compare the current listing against the pre-iteration baseline (e.g., `diff /tmp/before-iter13.txt /tmp/after-iter13.txt`)
3. Verify there are no differences in the output
4. Confirm no new directories (e.g., no new `topup_runs` or equivalent under the ambient tree)

**Expected outcome:** 
- The ambient `apps/backend/.data/` tree has zero new, modified, or deleted files
- No new top-up-run records or equivalent have been written to the ambient store
- The checksums are identical before and after

**Pass criteria:** 
- The diff output is empty (no added, removed, or modified files)
- No new subdirectories appear under `apps/backend/.data/`
- The ambient tree's file count and total size are unchanged

---

### TC-07 — Regression replay: J-01–J-05, J-07, J-08 all pass against scoped backend

**Type:** browser  
**Preconditions:** 
- A fresh scoped backend is available (same or different from TC-01's rig, deterministic replay does not care about rig state)
- The regression golden scripts exist: `runs/goal-session-desk/journey-scripts/J-01.json` through `J-05.json`, `J-07.json`, `J-08.json`

**Steps:**
1. Replay each golden script deterministically against the scoped backend:
   - `python -m apps.backend.scripts.replay runs/goal-session-desk/journey-scripts/J-01.json --backend-url http://localhost:8301`
   - (repeat for J-02, J-03, J-04, J-05, J-07, J-08)
2. For any step that reaches a compute/fetch/Run control, confirm it targets the scoped backend, not the ambient one
3. Collect the output of each replay

**Expected outcome:** 
- Each replay reports PASS with 0 failed steps
- No replay step hangs or times out
- No step deviates from the recorded interaction

**Pass criteria:** 
- All 7 replays (J-01–J-05, J-07, J-08) report PASS
- Each replay logs "0 failed steps" or equivalent
- No regression from prior iterations

---

### TC-08 — MCP contract re-confirmed: EXPECTED_TOOLS has exactly 17 entries

**Type:** api  
**Preconditions:** 
- The backend test suite `tests/test_mcp_server.py` exists and is runnable

**Steps:**
1. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_mcp_server.py -v`
2. Locate the output that reports the tool count assertion
3. Confirm `EXPECTED_TOOLS` contains exactly 17 entries
4. Verify the test passes

**Expected outcome:** 
- The test suite runs without error
- The `EXPECTED_TOOLS` assertion passes with exactly 17 tools
- J-06 (MCP surface verification) is confirmed without a browser pass

**Pass criteria:** 
- Test exits with code 0 (success)
- Output includes "17" as the expected tool count
- No reduction in tool count from prior iterations

---

### TC-09 — Full backend test suite passes: ≥1369 passed, 8 skipped, 0 failed; fingerprint `08e471b10130e1e2`

**Type:** api  
**Preconditions:** 
- The backend environment is set up with dependencies installed

**Steps:**
1. Run `cd apps/backend && .venv/bin/python -m pytest tests/ -v 2>&1 | tee /tmp/pytest-output.txt`
2. Capture the final summary line (required `-v` flag for reliable display in this environment)
3. Extract pass/skip/fail counts
4. Run `python -c "from app.config import Config; print(Config().config_fingerprint())"`
5. Compare the fingerprint output

**Expected outcome:** 
- Full suite runs to completion
- Summary line shows ≥1369 passed, 8 skipped, 0 failed
- Fingerprint print statement outputs exactly `08e471b10130e1e2`
- No test takes an excessive time (timeout on individual tests)

**Pass criteria:** 
- Exit code 0 (all tests pass)
- Reported counts: passed ≥1369, skipped = 8, failed = 0
- Fingerprint output is exactly `08e471b10130e1e2` (no drift)
- No regressions from prior iterations

---

### TC-10 — Repository diff: zero changes to 16 named product files

**Type:** artifact  
**Preconditions:** 
- The iteration's start-of-run snapshot has been captured (git index or similar)

**Steps:**
1. Run `git diff --stat HEAD` to show the accumulated diff for this iteration
2. Search for any changes to:
   - `apps/backend/app/research/desk_topup_log.py`
   - `apps/backend/app/research/desk_topup_compute.py`
   - `apps/backend/app/research/desk_routes.py`
   - `apps/backend/app/research/desk_screen.py`
   - `apps/backend/app/research/desk_coverage.py`
   - `apps/backend/app/research/tradability.py`
   - `apps/backend/app/research/levels.py`
   - `apps/backend/app/research/bars.py`
   - `apps/backend/app/mcp/__init__.py`
   - `apps/backend/app/config.py`
   - `apps/backend/app/meta.py`
   - `apps/frontend/app/desk/page.tsx`
   - `apps/frontend/lib/types.ts`
   - `apps/frontend/lib/api.ts`
   - `apps/frontend/components/StructureChart.tsx`
   - `apps/frontend/components/PriceChart.tsx`
3. Verify none of these files have any diff lines

**Expected outcome:** 
- The cumulative diff touches ONLY:
  - Documentation files (handoffs, reports)
  - Evidence/showcase artifacts (screenshots, demo walkthrough JSON)
  - QA results (test reports, evidence)
- Zero diff on all 16 named product/application files

**Pass criteria:** 
- `git diff --stat` shows no modifications to any of the 16 files listed above
- The only changed files are in `docs/handoffs/`, `reports/qa/`, `reports/phase-`, or similar non-product directories

---

### TC-11 — Prior iteration's scoped processes stopped before this iteration's rig is seeded

**Type:** api  
**Preconditions:** 
- This iteration's environment setup is about to begin
- Previous iterations may have left scoped processes running on `:8301`/`:3301` or `:8302`/`:3302`

**Steps:**
1. Run `ss -tlnp | grep -E ':(8301|3301|8302|3302)'` to inventory processes on the scoped-rig ports
2. For each process found, note its PID and check its CPU mask: `taskset -pc <pid>`
3. Confirm the mask is within host-guard bounds `4-7,12-15` (or similar; verify it never ran outside the guard)
4. Kill any process found: `pkill -f "<process-name>"` or `kill <pid>`
5. Verify the ports are clear: `ss -tlnp | grep -E ':(8301|3301|8302|3302)'` (should produce no output)
6. Document the finding in the dev handoff

**Expected outcome:** 
- Any prior iteration's scoped processes are identified and confirmed stopped
- If no processes were found, that is also documented
- The ports `:8301`, `:3301`, `:8302`, `:3302` are all free and ready for this iteration's rig
- The dev handoff states the outcome (e.g., "No leftover processes found" or "Stopped PID XXXX (uvicorn), verified within host-guard mask")

**Pass criteria:** 
- `ss -tlnp` on the specified ports produces no output after cleanup
- The dev handoff includes a statement about the port inventory and cleanup result
- No prior iteration's rig is still consuming resources at the start of this iteration

---

## Summary

**Total test cases:** 11  
**API tests:** 5 (TC-01, TC-02, TC-06, TC-08, TC-09, TC-11)  
**Browser tests:** 3 (TC-03, TC-07)  
**Artifact checks:** 3 (TC-04, TC-05, TC-10)

### Execution Notes

- **Critical sequencing:** TC-01 must complete before TC-02 (same rig); TC-02 must complete before TC-03 (same rig, same processes). TC-04 depends on both TC-01 and TC-03 captures. TC-05 depends on TC-04 completion.
- **No product code change expected:** TC-10 verifies zero diff on 16 named files. This is a hard requirement, not a default.
- **Ambient tree isolation:** TC-06 proves no writes landed in the ambient `apps/backend/.data/` store, enforcing the scoped-rig discipline across the entire iteration.
- **Regression smoke set:** TC-07 confirms J-01–J-05, J-07, J-08 still pass; J-06 is verified via its MCP contract (TC-08) with no browser pass required.
- **Fingerprint pin:** TC-09 confirms the pin `08e471b10130e1e2` is unchanged, enforcing the foundation invariant.
- **Port hygiene:** TC-11 must run BEFORE any new rig is seeded (i.e., early in the developer lane's execution).
