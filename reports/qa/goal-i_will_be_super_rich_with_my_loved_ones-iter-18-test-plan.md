# Iteration 18 Functional Test Plan — Replay-Study Layer

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-18
**Date:** 2026-06-12
**Frontend Present:** yes

## Phase Goal

Enable users to create, monitor, cancel, and re-run deterministic replay studies of the setup grammar over chosen windows — with results reported side-by-side against a seeded random-arm-time null baseline — and validate the entire evidence layer by pinning a committed reference study that reproduces exact results in CI without credentials.

---

## Test Cases

### TC-01 — Study Runner Determinism (Same Fixture + Fingerprint + Seed → Byte-Identical Results)

**Type:** api
**Preconditions:** Backend running; PG SIP fixture at `apps/backend/tests/fixtures/alpaca/PG_20260609_170000_171000_sip.json` exists; config fingerprint stable.

**Steps:**
1. Run study creation: `POST /research/studies` with reference-window source, absorption_reversal setup, long direction, config-owned null-arm seed (e.g., seed=12345).
2. Capture response: study ID, occurrence rows, null-baseline arm counts, aggregates, baseline seed.
3. Re-run identical study: same source, fingerprint, seed.
4. Capture second run: occurrence rows, baseline arm counts, aggregates.
5. Compare byte-by-byte: both run results.

**Expected outcome:** Both runs produce identical occurrence rows, identical null-baseline arm times, identical aggregate counts, identical ternary excursion outcomes.
**Pass criteria:** `md5(results1) == md5(results2)` for the full study result payload; no row re-ordering; seed value persisted and identical.

---

### TC-02 — Seeded Null Baseline Reproducibility

**Type:** api
**Preconditions:** Backend running; config key `study_null_arm_count` defined and in fingerprint; baseline seed recorded on study creation.

**Steps:**
1. Create study with seed S1 (e.g., S1=12345): `POST /research/studies` with null-arm-time baseline.
2. Record null-baseline arm times from response.
3. Create second study with same (source, fingerprint) but different seed S2 (e.g., S2=99999).
4. Verify null-baseline arm times differ.
5. Re-create first study with S1 again.
6. Verify null-baseline arm times match the first run exactly.

**Expected outcome:** Same seed → identical random arm times; different seed → different arm times; re-using S1 reproduces the first baseline.
**Pass criteria:** `baseline_arms_1 == baseline_arms_3` and `baseline_arms_1 != baseline_arms_2`; seeds correctly persisted and retrieved.

---

### TC-03 — Never-Pool Across `data_feed` and `config_fingerprint`

**Type:** artifact
**Preconditions:** At least two studies created with different `data_feed` or `config_fingerprint` values; persistent dev DB with multi-fingerprint records.

**Steps:**
1. Query `studies` table in SQLite: verify each study record carries `data_feed`, `config_fingerprint` stamps.
2. Query `study_occurrences` table: verify no aggregation query unions/pools results across distinct `data_feed` or `config_fingerprint` values.
3. Open `/studies` page in browser: view results view; verify feed + fingerprint stamps visible on each result.
4. Verify aggregates are always per-fingerprint (no cross-fingerprint sums).

**Expected outcome:** Every study is stamped with its source feed and config fingerprint; UI displays these stamps; aggregates never pool across distinct fingerprints/feeds.
**Pass criteria:** Artifact check: `data_feed` and `config_fingerprint` columns visible in study record; UI renders both stamps; no SQL aggregation ignores fingerprint/feed in WHERE clause.

---

### TC-04 — API Validation Matrix: Unknown Setup → 422

**Type:** api
**Preconditions:** Backend running; study endpoints wired.

**Steps:**
1. `POST /research/studies` with `setup="unknown_setup"`, valid source, direction.
2. Capture response status and body.

**Expected outcome:** HTTP 422; error message indicates invalid setup name.
**Pass criteria:** Status code = 422; response body contains "setup" and "unknown" or "invalid".

---

### TC-05 — API Validation Matrix: Unknown Direction → 422

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `POST /research/studies` with valid setup, `direction="sideways"`, valid source.
2. Capture response status and body.

**Expected outcome:** HTTP 422; error message indicates invalid direction.
**Pass criteria:** Status code = 422; response body contains "direction" and the invalid value.

---

### TC-06 — API Validation Matrix: Level Setup Without Level → 422

**Type:** api
**Preconditions:** Backend running; level_break and failed_move_fade setups registered.

**Steps:**
1. `POST /research/studies` with `setup="level_break"`, direction, source, **omit** `level` field or set to null.
2. Capture response status and body.

**Expected outcome:** HTTP 422; error message indicates level is required.
**Pass criteria:** Status code = 422; response body contains "level" and "required".

---

### TC-07 — API Validation Matrix: Future Window → 422 or Failed Status

**Type:** api
**Preconditions:** Backend running; current date/time known.

**Steps:**
1. `POST /research/studies` with reference-window source, `start_date` = tomorrow's date, `end_date` = tomorrow's date + 1 hour.
2. Capture response: status code and body.

**Expected outcome:** Either HTTP 422 (validation rejects future window) OR study created with `status="failed"` and an explicit error message.
**Pass criteria:** Status = 422 (window rejected) OR (status code = 201 AND study.status = "failed" AND study.error_message contains "future" or "invalid window").

---

### TC-08 — API Validation Matrix: Empty Window → 422 or Failed Status

**Type:** api
**Preconditions:** Backend running; symbol chosen that has no data in the window (e.g., a weekend or after-hours window).

**Steps:**
1. `POST /research/studies` with arbitrary-symbol source, symbol="TEST", start and end both in a known empty period.
2. Capture response: status code and body.

**Expected outcome:** Either HTTP 422 (validation rejects empty) OR study created with `status="failed"` and explicit message.
**Pass criteria:** Status = 422 OR (status code = 201 AND study.status = "failed" AND error_message contains "no data" or "empty").

---

### TC-09 — API: Unknown Study ID → 404 on Cancel

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. `POST /research/studies/{id}/cancel` with a non-existent UUID (e.g., "00000000-0000-0000-0000-000000000000").
2. Capture response status and body.

**Expected outcome:** HTTP 404; body indicates study not found.
**Pass criteria:** Status code = 404; response body contains "not found" or "unknown".

---

### TC-10 — API: Cancel Terminal Study → 409

**Type:** api
**Preconditions:** Backend running; a completed (or failed) study exists.

**Steps:**
1. Create a reference-window study and wait for `status="done"`.
2. `POST /research/studies/{id}/cancel` on the done study.
3. Capture response status and body.

**Expected outcome:** HTTP 409; body indicates study is terminal and cannot be cancelled.
**Pass criteria:** Status code = 409; response body contains "terminal" or "already completed" or "cannot cancel".

---

### TC-11 — Study Status Progression: Queued → Running → Done

**Type:** browser
**Preconditions:** Backend running (started after dev); frontend running; `/studies` page reachable; persistent dev DB available.

**Steps:**
1. Navigate to `/studies` page.
2. Create study with reference-window quick-pick, absorption_reversal, long direction.
3. Click "Run" or "Create" button.
4. Observe status immediately after submission (should show `queued` or `running`).
5. Poll `GET /research/studies/{id}` or refresh page; observe status transitions to `running`.
6. Wait for job to complete; observe final status = `done`.
7. Click "View Results" or expand results row; verify occurrence rows + aggregates + null baseline rendered.

**Expected outcome:** Status visibly progresses from queued → running → done; results become visible on completion.
**Pass criteria:** Page shows "Queued", then "Running" with progress indicator, then "Done" with clickable results; full-page non-blank screenshot of results view (scrolled into view); re-run identical study reproducibly.

---

### TC-12 — J-60: Reference-Window Quick-Pick Creates and Re-runs Identically

**Type:** browser
**Preconditions:** Backend running; frontend running; `/studies` page reachable; reference-window SIP fixture loaded into backend.

**Steps:**
1. Navigate to `/studies`.
2. In create form, select source = "Reference Window (committed SIP fixture)".
3. Select setup = absorption_reversal, direction = long.
4. Click Create/Run.
5. Wait for `status="done"`.
6. Capture screenshot of results view (occurrence rows, aggregates, null baseline side-by-side, feed + fingerprint stamps).
7. Note the exact aggregate counts (e.g., "8/13 +1R_first; baseline: 41/100").
8. In the job list, click "Re-run" on the completed study (or submit an identical new study).
9. Wait for second run to complete.
10. Capture screenshot of second run's results.
11. Compare aggregate counts visually + via REST API.

**Expected outcome:** Both runs show identical occurrence counts, identical ternary outcomes, identical null-baseline counts; results fully rendered with no blank areas.
**Pass criteria:** Visual comparison: counts on-screen match exactly; REST `/research/studies/{id}` returns identical aggregate JSON; screenshots are full-page, non-blank, sane size (1280+ width).

---

### TC-13 — J-61: Manual-Level Study Shows `hindsight_level` Label

**Type:** browser
**Preconditions:** Backend running; frontend running; `/studies` page reachable.

**Steps:**
1. Navigate to `/studies`.
2. Create study with setup = level_break (or failed_move_fade), direction = long.
3. Form should show "Level" input field; enter a level value (e.g., 150.50).
4. Include `hindsight_level=true` warning/label in the form.
5. Submit study.
6. Wait for completion.
7. View results; look for label "level chosen with hindsight — illustrative" (or similar from taxonomy).
8. Verify this label appears near the level value in the results.

**Expected outcome:** Manual-level study results display a hindsight warning label; label is visible and distinct.
**Pass criteria:** Full-page screenshot shows the hindsight label; label text includes "hindsight" and "illustrative"; backend test confirms hindsight-level studies are excluded from cross-study aggregates (code inspection or unit test result).

---

### TC-14 — J-61: Truncated Occurrences Flagged and Counted Separately

**Type:** api
**Preconditions:** Backend running; a study over a window where some occurrence horizons extend beyond window end (truncated).

**Steps:**
1. Create study over a window where at least one occurrence's horizon end-time is after the window end-time.
2. Wait for completion.
3. `GET /research/studies/{id}` and inspect `study_occurrences` array.
4. Look for rows with `truncated=true` flag.
5. Verify truncated rows are counted separately in aggregates (e.g., "5/10 (3 truncated)" or similar honest notation).

**Expected outcome:** Truncated occurrences explicitly flagged; aggregate counts distinguish between full and truncated outcomes.
**Pass criteria:** JSON response includes `truncated` boolean on relevant occurrence rows; aggregate summary includes a truncated count or caveat (never silently omits truncated rows).

---

### TC-15 — J-61: Cancel Running Study → Explicit `cancelled` Status with Partial-Marked Results

**Type:** browser
**Preconditions:** Backend running; frontend running; a study source with a long-running job (e.g., sim with large window or a credentialed real-data window).

**Steps:**
1. Create a long-running study (e.g., SIM-REVERSAL with a large window).
2. Immediately click the "Cancel" button while status is still `running`.
3. Wait briefly for cancellation to take effect.
4. Refresh or poll the study detail; observe status = `cancelled`.
5. View results: if partial results exist, look for a caveat like "Partial results — study was cancelled" or similar.
6. Verify writer queue remains intact (backend not crashed, subsequent studies can be created and run).

**Expected outcome:** Study transitions to `cancelled` status; partial results marked as such; no server crash or writer-queue corruption.
**Pass criteria:** Page shows "Cancelled" status; results view includes caveat text (if results exist); backend stays responsive; subsequent study can be created immediately.

---

### TC-16 — J-61: Failing Study (No Data / Provider Error) → Explicit Error, Never Empty Success

**Type:** api
**Preconditions:** Backend running; a symbol or window known to have no available data (e.g., untraded symbol, or a future date with no mock data).

**Steps:**
1. Create a study with arbitrary-symbol source, symbol="NOTRADE" (or a symbol with no fixture), a past window.
2. Wait for job to complete (or reach terminal state).
3. `GET /research/studies/{id}` and inspect the response.

**Expected outcome:** Study reaches `status="failed"`; response includes explicit `error_message` field describing the failure (e.g., "No data available" or "Provider error: …").
**Pass criteria:** Status = "failed" (never "done"); `error_message` field is non-empty and describes the issue; results array is empty or absent (never contains fake data).

---

### TC-17 — Arbitrary-Symbol Window Without Credentials → Explicit Unavailable Error

**Type:** api
**Preconditions:** Backend running without Alpaca/real credentials configured (or with credentials intentionally unavailable); arbitrary-symbol source selected.

**Steps:**
1. Create study with arbitrary-symbol source, real symbol (e.g., "AAPL"), a past window.
2. Do NOT provide credentials.
3. Wait for job to complete.
4. `GET /research/studies/{id}` and inspect response.

**Expected outcome:** Study reaches `status="failed"` with error_message indicating credentials unavailable or data source unreachable.
**Pass criteria:** Status = "failed"; error message contains "credential", "unavailable", or "unreachable"; never substitutes fixture data or returns empty success.

---

### TC-18 — Config Fingerprint Includes New Study Keys

**Type:** artifact
**Preconditions:** Backend code changes include new config keys (`study_null_arm_count`, arming thresholds, occurrence-R spread multiple); config.py updated.

**Steps:**
1. Inspect `app/config.py`: verify new study keys are present and documented.
2. Inspect `app/research/store.py` or `app/config.py`: verify `config_fingerprint` computation includes these new keys.
3. Run a unit test: create two studies with identical setup but different config values (e.g., different `study_null_arm_count`).
4. Verify the two studies have different `config_fingerprint` values.
5. Create a third study identical to the first; verify it has the same fingerprint.

**Expected outcome:** New config keys are part of fingerprint computation; changing a key value changes the fingerprint.
**Pass criteria:** Artifact check: new keys listed in fingerprint-building code; unit test passes (different config → different fingerprint, same config → same fingerprint).

---

### TC-19 — Observer Equivalence: Engine Untouched by Study Observer

**Type:** api
**Preconditions:** Backend running; `test_observer_equivalence.py` test file exists.

**Steps:**
1. Run `pytest apps/backend/tests/test_observer_equivalence.py -v` (or equivalent; check project-template.md for exact test command).
2. Capture exit code and output.

**Expected outcome:** All 7 observer-equivalence assertions pass; engine produces byte-identical state/confidence/features/history whether or not a study observer is attached.
**Pass criteria:** Exit code = 0; test output shows "7 passed"; no engine mutations detected by observer.

---

### TC-20 — Dense Replay Gate Unchanged and Green

**Type:** api
**Preconditions:** Backend running; `test_dense_replay_gate.py` test file exists (iter-17 performance gate).

**Steps:**
1. Run `pytest apps/backend/tests/test_dense_replay_gate.py -v` (verify in project-template.md).
2. Capture exit code and output.

**Expected outcome:** All tests pass; replay of PG SIP fixture stays within `dense_replay_time_budget_seconds` (≈10 s).
**Pass criteria:** Exit code = 0; no performance regressions; all assertions pass.

---

### TC-21 — Pinned Reference Study (J-62): CI Test Reproduces Exact Results

**Type:** api
**Preconditions:** Backend running; committed test file exists (e.g., `test_reference_study.py` or equivalent); PG SIP fixture available; CI environment.

**Steps:**
1. Run the pinned reference-study test in CI (or locally without credentials): `pytest apps/backend/tests/test_reference_study.py -v` (exact name per project-template.md).
2. Capture output: exact occurrence row counts, aggregate counts, null-baseline counts, ternary outcomes.
3. Document the pinned numbers.
4. Run the test a second time (identical environment).
5. Capture output again.
6. Compare byte-by-byte.

**Expected outcome:** First and second run produce identical occurrence rows, identical aggregates, identical baseline arm counts; test passes both times; no re-pins needed.
**Pass criteria:** Exit code = 0 (both runs); pinned occurrence counts match (e.g., "8/13" for setup occurrences); baseline counts match (e.g., "41/100"); test output shows no differences between runs; within config budget (≈10 s per replay).

---

### TC-22 — Pinned Reference Study Covers Both PG SIP Fixture and Seeded Sim

**Type:** api
**Preconditions:** Pinned reference-study test includes at least two source scenarios (fixture + sim).

**Steps:**
1. Inspect test file: verify it creates studies for (a) reference-window (PG SIP fixture) and (b) at least one seeded sim (e.g., SIM-REVERSAL, SIM-BUYER).
2. Run the test; capture results for both sources.
3. Verify both sources have pinned assertions (exact row/aggregate counts).

**Expected outcome:** Test covers both fixture and sim; both sources have pinned, byte-stable results.
**Pass criteria:** Test file includes assertions for fixture and at least one sim; assertions are specific counts (not just "passes" or "has results").

---

### TC-23 — Full Backend Suite Passes (629+ Tests, Zero Re-pins)

**Type:** api
**Preconditions:** Backend running; all changes committed; project-template.md specifies full test command.

**Steps:**
1. Run full test suite: `pytest apps/backend/tests/ -q` (or per project-template.md; note: `-q` flag may double-suppress with backend's addopts, verify by exit code).
2. Capture exit code and output.
3. Count: total tests passed; any re-pins or changes to snapshot/fixture files (should be zero).

**Expected outcome:** All tests pass (≥629); exit code = 0; no snapshot re-pins; no engine-layer changes introduced.
**Pass criteria:** Exit code = 0; full suite green (verify by running the command, not by summary); zero re-pins or schema changes.

---

### TC-24 — Frontend Builds Clean

**Type:** api
**Preconditions:** Frontend code finalized; build command in project-template.md.

**Steps:**
1. Run build: `npm run build` (or per project-template.md) in `apps/frontend/`.
2. Capture exit code and output.

**Expected outcome:** Build succeeds with no errors or TypeScript violations.
**Pass criteria:** Exit code = 0; no "error" or "failed" messages in output.

---

### TC-25 — Studies Nav Entry Enabled, Page Reachable in ≤2 Clicks

**Type:** browser
**Preconditions:** Frontend running; backend running (canary probe: `GET /research/taxonomy` must include studies copy).

**Steps:**
1. Start backend: verify `curl -s http://localhost:8000/research/taxonomy` returns 200 and includes "studies" or "hindsight" labels.
2. Start frontend (if not already running).
3. Navigate to home page (`http://localhost:3000`).
4. Count clicks to reach `/studies` page.
5. Verify NavBar shows "Studies" entry and it is **enabled** (not disabled).

**Expected outcome:** Studies nav entry is enabled (clickable); `/studies` page reachable in 1 click from home; page loads without error.
**Pass criteria:** Full-page screenshot of home page shows enabled "Studies" link; clicking it navigates to `/studies` page successfully; page does not 404 or show error.

---

### TC-26 — Studies Page: Create Form Shows All Required Fields

**Type:** browser
**Preconditions:** Frontend running; `/studies` page accessible.

**Steps:**
1. Navigate to `/studies`.
2. Look for create form (or form panel).
3. Verify the form includes:
   - Source picker (reference-window quick-pick, sim scenarios, arbitrary-symbol + date)
   - Setup dropdown (absorption_reversal, trend_continuation, level_break, failed_move_fade)
   - Direction dropdown (long, short)
   - Level input (visible only for level setups; with hindsight warning)
4. Verify all fields are required (or clearly marked).

**Expected outcome:** All expected fields present; form validation is clear; level input is conditionally shown.
**Pass criteria:** Full-page screenshot shows all fields; form is non-blank and properly laid out; conditional level field appears/disappears when setup changes.

---

### TC-27 — Studies Page: Job List Shows Status and Cancel Control

**Type:** browser
**Preconditions:** Frontend running; at least one study created and in progress or completed.

**Steps:**
1. Navigate to `/studies`.
2. Look for job list (or study list table/panel).
3. For a running study, verify the list shows:
   - Study name/ID
   - Status (e.g., "Running", "Queued", "Done", "Cancelled", "Failed")
   - Progress indicator (if running)
   - Cancel button (if running/queued)
4. Click Cancel on a running study; observe status changes to "Cancelled".

**Expected outcome:** Job list is visible, status is readable, Cancel button is present and functional.
**Pass criteria:** Full-page screenshot shows job list; status labels are distinct; Cancel button is clickable and responsive.

---

### TC-28 — Studies Page: Results View Shows Occurrence Rows and Null Baseline Side-by-Side

**Type:** browser
**Preconditions:** Frontend running; a completed study available.

**Steps:**
1. Navigate to `/studies`.
2. Click on a completed study (or expand its results row).
3. Look for results view (table or panel).
4. Verify the view includes:
   - Occurrence rows (arm time, verdict summary, per-horizon excursion outcomes)
   - Aggregates (setup occurrence counts, e.g., "8/13 +1R_first")
   - Null-baseline side-by-side (e.g., "random-time baseline: 41/100")
   - Feed and fingerprint stamps (visible but not obtrusive)
   - Sample count (n) and caveats
   - Hindsight label (if applicable)
   - Truncated count (if any truncations)

**Expected outcome:** Results view is complete, readable, and arranged side-by-side (not stacked).
**Pass criteria:** Full-page, non-blank screenshot of results view (scrolled into view); all elements present; layout is sane and professional; no abbreviated or truncated text.

---

### TC-29 — Studies Display Copy Is Descriptive and Honest (No Edge Claims)

**Type:** artifact
**Preconditions:** Taxonomy copy written to `GET /research/taxonomy` response; frontend pages use this copy.

**Steps:**
1. `GET http://localhost:8000/research/taxonomy` and extract studies-related copy.
2. Inspect all status labels (queued, running, done, cancelled, failed, truncated).
3. Inspect all study-related messages (hindsight warning, null-baseline caption, journaled-measurements framing, per-status honest-absence copy).
4. Search for prohibited phrases: "edge", "win rate", "predic", "recommend", "buy", "sell", imperative verbs.
5. Verify all copy uses: present tense, measurement framing, n/caveats always visible.

**Expected outcome:** No edge claims, no predictions, no imperative language; all copy is descriptive and measurement-framed.
**Pass criteria:** Artifact check: no prohibited phrases found in study copy; every result statement includes n or caveat; "Descriptive only — not trading advice" or similar register present somewhere on the results view.

---

### TC-30 — J-68 Sentinel: Cockpit Unchanged Except Studies Nav Entry

**Type:** browser
**Preconditions:** Frontend running; a live/sim session open on the cockpit.

**Steps:**
1. Open cockpit page (home with a watched symbol, or sim running).
2. Verify no new elements, colors, or controls on the cockpit itself (the chart, tape, state display, thesis panel, etc.).
3. Verify NavBar is the only place where a change is visible: the Studies entry is now enabled.
4. Take a full-page screenshot of the cockpit (with no-thesis SIM-BUYER sim running, per the spec).

**Expected outcome:** Cockpit visually identical to previous iteration, except Studies entry is enabled in NavBar.
**Pass criteria:** Full-page screenshot shows no new cockpit elements; NavBar shows enabled Studies link; rest of UI is unchanged.

---

---

## Summary

**Total test cases:** 30
- **API tests:** 17 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-16, TC-17, TC-19, TC-20, TC-21, TC-22, TC-23)
- **Browser tests:** 9 (TC-11, TC-12, TC-13, TC-15, TC-25, TC-26, TC-27, TC-28, TC-30)
- **Artifact checks:** 4 (TC-03, TC-14, TC-18, TC-29)
- **Integration/Regression:** 0 (covered within API/browser scope)

**Key validation gates:**
1. **Determinism & reproducibility** — TC-01, TC-02, TC-21, TC-22 pin exact reference-study results
2. **Never-pool discipline** — TC-03 verifies feed/fingerprint stamps and no cross-fingerprint aggregation
3. **API validation matrix** — TC-04 through TC-10 cover all error paths
4. **User flows** — TC-11, TC-12 end-to-end (create → run → results); TC-15 cancellation; TC-16 failure handling
5. **Frontend visibility** — TC-25 through TC-30 ensure `/studies` page is discoverable, complete, and honest
6. **Anti-goal compliance** — TC-29 verifies no edge/prediction language; TC-30 confirms cockpit untouched (J-68 sentinel)
7. **Regression assurance** — TC-19, TC-20, TC-23, TC-24 confirm engine and full suite remain green
