# goal-fast_wall-iter-4 Functional Test Plan

**Phase:** goal-fast_wall-iter-4
**Date:** 2026-07-17
**Frontend Present:** yes

## Phase Goal

The operator can trigger the first-ever completed edge-report compute directly from `/structure` — a single-flight, cancellable, progress-reporting background job (button + CLI warmer) that never starts on any GET — and watch it reach a real report or an honest failure without leaving the page.

---

## Test Cases

### TC-01 — Initial compute trigger on cold cache

**Type:** api
**Preconditions:** No compute job has ever run; edge-report cache is cold (0 rows); dataset registry is non-empty.

**Steps:**
1. POST `/research/edge-report/compute` with an empty body `{}`
2. Capture the response's `started` field
3. Poll `GET /research/edge-report/compute` until the job reaches a terminal state
4. Record the final job snapshot (state, finished_utc, error)

**Expected outcome:** The initial POST returns `started: true`. After the job completes, `GET /research/edge-report/compute` returns `state: "done"`, a populated `finished_utc` (ISO-8601 string), and `error: null`.

**Pass criteria:** `started === true` AND final snapshot has `state === "done"` AND `finished_utc !== null` AND `error === null`.

---

### TC-02 — Single-flight: second trigger returns same job

**Type:** api
**Preconditions:** A compute job is deterministically held in flight (test harness blocks it mid-sweep using a threading.Event).

**Steps:**
1. Send first `POST /research/edge-report/compute` and confirm it returns `started: true`
2. **Before the first job finishes**, send a second `POST /research/edge-report/compute`
3. Compare the two responses' `job.id` fields and the `started` field from the second POST

**Expected outcome:** The second POST returns `started: false` and a job snapshot with the SAME `id` as the in-flight job. No second job is created.

**Pass criteria:** Second POST's `started === false` AND second POST's `job.id === first POST's job.id`.

---

### TC-03 — Cancel resolves to "cancelled"; no partial report published

**Type:** api
**Preconditions:** A compute job is held in flight via test harness.

**Steps:**
1. Send `POST /research/edge-report/compute/cancel` while the job is running
2. Poll `GET /research/edge-report/compute` until the job reaches a terminal state
3. Call `GET /research/edge-report` and inspect the payload (check for absence of a new `report` field)

**Expected outcome:** The cancel request succeeds. The job snapshot reaches `state: "cancelled"`. A subsequent `GET /research/edge-report` still returns the not-computed payload (no `report` key present), meaning the edge-report cache's hot slot and durable row are unchanged.

**Pass criteria:** Job snapshot `state === "cancelled"` AND `GET /research/edge-report` response has no `report` field (the `compute` field may be present, but no new report was published).

---

### TC-04 — Cancel while idle returns 409

**Type:** api
**Preconditions:** No job has ever run, or the last job already reached a terminal state (manager is idle).

**Steps:**
1. Send `POST /research/edge-report/compute/cancel` when the manager is idle
2. Capture the response status code

**Expected outcome:** The response status code is `409 Conflict`.

**Pass criteria:** Response HTTP status === 409.

---

### TC-05 — Force=true recomputes over a warm key

**Type:** api
**Preconditions:** The edge-report cache already holds a warm key from a prior completed compute (a durable row with `created_utc` recorded). A call-counting spy is attached to the underlying compute path.

**Steps:**
1. Record the cache's stored row's `created_utc` before the force
2. Send `POST /research/edge-report/compute` with body `{"force": true}`
3. Poll until the job reaches `state: "done"`
4. Record the cache's stored row's new `created_utc`
5. Inspect the spy's call count

**Expected outcome:** The force=true trigger initiates a fresh compute (spy records at least one new call). The cache's stored `created_utc` moves forward from its pre-force value.

**Pass criteria:** `created_utc` timestamp increased AND spy recorded at least one new call to the underlying compute path.

---

### TC-06 — Non-force trigger over warm key uses cache

**Type:** api
**Preconditions:** The edge-report cache holds a warm key from TC-05; the spy is still monitoring.

**Steps:**
1. Send `POST /research/edge-report/compute` with no `force` flag (or `{"force": false}`)
2. Poll until the job reaches a terminal state
3. Inspect the spy's call count (should be zero new calls since TC-05)
4. Verify the job snapshot's `state` and the returned report

**Expected outcome:** The job reaches `state: "done"` serving the already-cached result. The call-counting spy records zero additional calls (no re-compute).

**Pass criteria:** Job `state === "done"` AND spy call count === 0 (no new compute calls) AND returned data matches the cached result from TC-05.

---

### TC-07 — Completed report byte-identical to uncached compute

**Type:** api
**Preconditions:** A compute job has reached `state: "done"`; the edge-report cache holds the published report.

**Steps:**
1. Call `GET /research/edge-report` (serving from the manager's published cache)
2. Call `_compute_strategy_comparison_report(store, dataset_store, bar_store, config)` directly via test API (the fresh uncached compute path)
3. Serialize both results via `json.dumps(..., sort_keys=True)`
4. Compare the two serialized strings byte-for-byte

**Expected outcome:** The cached report and the fresh uncached compute produce identical JSON (same keys, same values, same order).

**Pass criteria:** `json.dumps(cached_report, sort_keys=True) === json.dumps(fresh_report, sort_keys=True)`.

---

### TC-08 — Not-computed payload's compute field mirrors the manager snapshot

**Type:** api
**Preconditions:** No compute job has ever run (cold cache).

**Steps:**
1. Call `GET /research/edge-report` on a cold cache and record the payload's `compute` field (should be `null`)
2. Trigger a compute via `POST /research/edge-report/compute`
3. While the job is in flight, poll both `GET /research/edge-report` and `GET /research/edge-report/compute`
4. Compare the two responses' `compute` (from edge-report endpoint) and the entire snapshot (from compute endpoint)
5. Verify they carry identical job metadata in every state

**Expected outcome:** On cold cache, `compute === null`. Once a job is triggered, `GET /research/edge-report`'s embedded `compute` field matches `GET /research/edge-report/compute`'s full snapshot byte-for-byte in shape and content, in every state (running, done, failed, etc.).

**Pass criteria:** Cold cache `compute === null` AND `GET /research/edge-report`'s `compute` field shape matches `GET /research/edge-report/compute` snapshot shape in all states AND both carry identical values.

---

### TC-09 — Non-GET verbs on /research/edge-report stay 405

**Type:** api
**Preconditions:** After the iteration's diff is applied.

**Steps:**
1. Send `POST` to `/research/edge-report` (not a subpath)
2. Send `PUT` to `/research/edge-report`
3. Send `PATCH` to `/research/edge-report`
4. Send `DELETE` to `/research/edge-report`
5. Run the existing test `test_non_get_verbs_are_405_no_write_surface_exists` (byte-unmodified source)

**Expected outcome:** All four non-GET verbs return HTTP 405 Method Not Allowed. The existing guard test passes with its original source intact.

**Pass criteria:** POST/PUT/PATCH/DELETE all return status 405 AND `test_non_get_verbs_are_405_no_write_surface_exists` passes.

---

### TC-10 — MCP tool list unchanged (18 tools)

**Type:** api
**Preconditions:** After the iteration's diff is applied.

**Steps:**
1. Run the test `test_advertised_tool_set_is_exactly_capability_6` (byte-unmodified source)
2. Verify `TOOL_NAMES` and `EXPECTED_TOOLS` in `apps/backend/app/mcp/__init__.py` are still exactly 18

**Expected outcome:** The test passes. The source code contains no new MCP tool registration, and the byte-unmodified source confirms no drift.

**Pass criteria:** Test passes AND source file has zero diff in the tool-registration section.

---

### TC-11 — CLI warmer runs on fixtures and prints progress

**Type:** api
**Preconditions:** The committed fixture dataset registry is available (`apps/backend/tests/fixtures/datasets_j03` or `apps/backend/tests/fixtures/datasets`).

**Steps:**
1. Run `python -m app.research.edge_report_compute` with no flags (uses fixture config)
2. Capture stdout and stderr
3. Check the exit code
4. Verify progress output (one line per completed backtest)
5. Confirm the durable edge-report cache published a row
6. Call `GET /research/edge-report` and compare the served report to the CLI's published cache

**Expected outcome:** The CLI exits with code 0. stdout contains at least one progress line per completed backtest (format: "[dataset_id] [strategy_id] done"). The published cache row is byte-identical to what `GET /research/edge-report` subsequently serves.

**Pass criteria:** Exit code === 0 AND stdout contains progress lines (at least 1 line) AND published cache row === served report (byte-identical JSON).

---

### TC-12 — CLI warmer repeat on warm key exits in <5s

**Type:** api
**Preconditions:** The CLI warmer already ran once (TC-11's warm state is in place).

**Steps:**
1. Measure wall-clock time
2. Run `python -m app.research.edge_report_compute` a second time (without `--force`)
3. Measure elapsed time
4. Inspect the call-counting spy (should show zero backtests re-run)
5. Verify the summary output reflects the already-warm result

**Expected outcome:** The CLI exits in under 5 seconds of wall-clock time. The spy confirms zero backtests re-run (all served from the warm cache). The printed summary reflects the cached result (e.g., "served from cache" or equivalent message).

**Pass criteria:** Elapsed time < 5 seconds AND spy records zero backtest re-runs AND summary indicates cache hit.

---

### TC-13 — Failed compute surfaces error verbatim; no partial report

**Type:** api
**Preconditions:** A test-injected exception is arranged inside the compute path (e.g., a simulated store failure mid-sweep).

**Steps:**
1. Trigger a compute via `POST /research/edge-report/compute` with the injected failure active
2. Poll `GET /research/edge-report/compute` until the job reaches `state: "failed"`
3. Record the snapshot's `error` field
4. Call `GET /research/edge-report` and verify the payload has no new `report` key (no partial report was published)

**Expected outcome:** The job snapshot reaches `state: "failed"`. The `error` field carries the exception's message verbatim. A subsequent `GET /research/edge-report` returns the not-computed payload (no new report was published).

**Pass criteria:** Job `state === "failed"` AND `error` field contains the exception message (verbatim, not generic) AND `GET /research/edge-report` has no `report` field.

---

### TC-14 — Five new hooks are genuinely wired (not decorative)

**Type:** api
**Preconditions:** The five new keyword-only parameters are added to `run_strategy_comparison_report` (force, progress, should_abort, sub_cache, workers).

**Steps:**

**Part A (default-path byte-identity):**
1. Call `run_strategy_comparison_report` via the default path (all new kwargs at their defaults)
2. Call the SAME function a second time with `progress=` and `should_abort=` hooks actively supplied but never triggered to abort
3. Serialize both results via `json.dumps(..., sort_keys=True)`
4. Compare byte-for-byte

**Part B (non-vacuous should_abort proof):**
5. Call `run_strategy_comparison_report` a third time with a `should_abort` hook that DOES fire mid-run
6. Record the result's state (should be cancelled/nothing published per TC-3's pattern)
7. Compare to the results from parts A and B: the third result should differ observably

**Expected outcome:**
- Part A: The unused-default path and the actively-supplied-but-never-triggered hooks path produce byte-identical JSON reports.
- Part B: A `should_abort` that DOES fire produces an observable change (the compute is cancelled and nothing is published), proving the hook is genuinely wired, not a decorative no-op.

**Pass criteria:** 
- Part A: `json.dumps(default_path_result, sort_keys=True) === json.dumps(unused_hooks_result, sort_keys=True)`
- Part B: Abort result differs from Part A result (observable difference: cancelled state, no publish).

---

### TC-15 — Browser: compute lifecycle on scoped backend/frontend

**Type:** browser
**Preconditions:** 
- A SCOPED backend/frontend pair is running (fresh temp journal/dataset/bar dirs, backend port 8391 / frontend port 3391)
- `TAPEOLOGY_DATASET_DIR` is pointed at a small committed fixture (e.g., `apps/backend/tests/fixtures/datasets_j03` or `apps/backend/tests/fixtures/datasets`, **never** the default `.data/datasets`)
- `/structure` is loaded with a cold edge-report cache (no prior compute)
- The page displays the not-computed panel with the "Compute edge report" button

**Steps:**
1. Click the "Compute edge report" button
2. Observe the panel's progress counts updating (backtests_done / backtests_total / backtests_from_cache)
3. Wait for the job to reach a terminal state (within 90 seconds)
4. Verify the panel transitions to either:
   - The existing `EdgeReportBody` render (if there are computed cells), OR
   - The honest all-empty-cells state (if the report has no data)
5. Confirm no full-page reload occurred during the process

**Expected outcome:** The progress counts update at least once while `state === "running"`. Within 90 seconds of the click, the not-computed panel is replaced by the report render or the honest empty state. The page remains on `/structure` throughout (no reload).

**Pass criteria:** 
- Progress updated >= 1 time while running
- Job reached terminal state within 90 seconds
- Panel transitioned to report or empty-cells render
- No full-page reload (same URL, no hard refresh event)

---

### TC-16 — Browser: failed state renders error verbatim

**Type:** browser
**Preconditions:** 
- A SCOPED backend/frontend pair is running (same as TC-15)
- A compute snapshot already at `state: "failed"` with a known `error` string is pre-arranged on the backend (via a direct test call, mirroring iter-1 QA's arrangement pattern)
- The page has not yet been navigated to `/structure`

**Steps:**
1. Navigate to `/structure`
2. Wait for the not-computed panel to render (or observe the poll tick firing)
3. Inspect the panel's rendered content for the exact `error` string
4. Take a screenshot of the error message

**Expected outcome:** The not-computed panel visibly renders the exact `error` string from the backend snapshot. The message is verbatim (not truncated, not generic), and the panel remains in a failed state (showing the error and an enabled retry button if applicable).

**Pass criteria:** 
- Error string renders verbatim in the panel
- Exact text match (case-sensitive) with the backend snapshot's `error` field
- Screenshot captures the rendered error message

---

### TC-17 — Regression: J-01 not-computed render frozen

**Type:** browser
**Preconditions:** A SCOPED backend/frontend pair is running (same fixture setup as TC-15). No compute job has ever been triggered.

**Steps:**
1. Navigate to `/structure`
2. Inspect the not-computed panel's headline, detail text, and register section
3. Take a screenshot of the panel in its idle state (button visible, no progress)
4. Compare the render to a baseline screenshot from a prior iteration (frozen J-01 rendering)

**Expected outcome:** The not-computed panel's headline ("Edge report not computed yet."), detail text, and register layout remain byte-identical to J-01's shipped render. Only the button and progress line are new additions.

**Pass criteria:** 
- Headline text unchanged
- Detail text unchanged
- Register section layout unchanged
- Button and progress line are the only visible new elements

---

### TC-18 — Regression: J-07 structure page surfaces unchanged

**Type:** browser
**Preconditions:** A SCOPED backend/frontend pair is running (same fixture setup as TC-15).

**Steps:**
1. Navigate to `/structure`
2. Scroll through all major sections: Tradable Map, Case Studies, Registry, Comparison, Edge Report
3. Take screenshots of each section
4. Verify no regressions in layout, text, or visual state
5. Confirm the backend suite (full green, config_fingerprint still `4d665603569b9dbf`)

**Expected outcome:** All sections render exactly as shipped in prior iterations. The Tradable Map, Case Studies, Registry, and Comparison sections show no changes. The Edge Report section shows only the new button + progress line additions in the not-computed panel.

**Pass criteria:** 
- All 4 non-Edge-Report sections render without changes
- Config fingerprint still `4d665603569b9dbf`
- Full backend test suite passes with zero regressions

---

## Summary

**Total test cases:** 18
- **API tests:** 10 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14)
- **Browser tests:** 4 (TC-15, TC-16, TC-17, TC-18)
- **Artifact/integration checks:** Regression verification embedded in browser tests

**Key testing strategy:**
- API tests cover the manager's single-flight/cancel/force/progress lifecycle and the REST routes' request/response shapes
- Browser tests verify the user-visible button, progress rendering, and error handling on a scoped backend/frontend pair (never the real corpus)
- Regression tests (TC-17, TC-18) ensure J-01, J-02, J-03, J-07 remain passing and byte-identical
- All tests respect the critical anti-goal: **no compute on page load — operator-run only**
