# Goal Desk Iter-14 Functional Test Plan

**Phase:** goal-desk-iter-14  
**Date:** 2026-07-28  
**Frontend Present:** yes

## Phase Goal

The operator can trigger a reconciliation of the derived bar-coverage index against the frozen bar store from `/desk`, watch it repair itself through the existing `BarIndex.reindex()`, and see before/after drift on a durable, append-only run record plus on the briefing's own coverage badges, making the coverage badges independently checkable instead of silently trusted.

## Test Cases

### TC-01 — Unindexed series drift classification

**Type:** api  
**Preconditions:** A scoped `BarStore` holds a recorded series (symbol, timeframe, series_id) with no matching row in `bar_index.db`.

**Steps:**
1. Call `classify_drift(store, bar_index)` with the above state.

**Expected outcome:** The returned drift dict contains exactly one entry in `unindexed_series` naming that symbol and timeframe (and series_id), with zero entries in `orphan_index_rows` and `stale_checksum_rows` for that pair.

**Pass criteria:** `drift["unindexed_series"]` has length 1 with the correct `{"series_id", "symbol", "timeframe"}` shape.

---

### TC-02 — Orphan index row drift classification

**Type:** api  
**Preconditions:** `bar_index.db` holds a row with a `series_id` that matches no file in the scoped `BarStore` (neither healthy nor corrupt).

**Steps:**
1. Call `classify_drift(store, bar_index)` with the above state.

**Expected outcome:** The returned drift dict contains exactly one entry in `orphan_index_rows` naming that `series_id` alone (no symbol or timeframe), with zero entries in the other two buckets for that id.

**Pass criteria:** `drift["orphan_index_rows"]` has length 1 with `{"series_id"}` only, no symbol/timeframe attached.

---

### TC-03 — Stale-checksum index row drift classification

**Type:** api  
**Preconditions:** A bar-series file is corrupted so `BarStore.list()` reports it in `errors` while a `bar_index.db` row still points at its `series_id`.

**Steps:**
1. Call `classify_drift(store, bar_index)` with the above state.

**Expected outcome:** The returned drift dict contains exactly one entry in `stale_checksum_rows` naming that `series_id`, with zero entries in the other two buckets for that id.

**Pass criteria:** `drift["stale_checksum_rows"]` has length 1 with `{"series_id"}` only.

---

### TC-04 — Reconciliation run repairs unindexed series

**Type:** api  
**Preconditions:** TC-01's drift state exists (unindexed series). A `DeskReconcileComputeManager` and `ReconcileRunStore` are initialized for the scoped rig.

**Steps:**
1. Trigger a reconciliation run via `POST /research/desk/coverage/reconcile/compute`.
2. Poll until the run reaches a terminal state (`"done"`, `"cancelled"`, or `"failed"`).
3. Verify the run record was persisted.
4. Call `GET /research/desk/coverage` for the affected (symbol, timeframe) pair before and after.

**Expected outcome:** The run resolves with `state: "done"`. Before the run, `has_bars: false`. After the run, `has_bars: true`. The recorded run's `drift_before` names that exact pair while `drift_after` no longer does.

**Pass criteria:** POST returns `started: true`; run state is `"done"`; coverage toggles false→true; drift_before contains the pair, drift_after does not.

---

### TC-05 — Reconciliation run handles corrupt file repair and error reporting

**Type:** api  
**Preconditions:** TC-03's drift state exists (corrupted file with stale-checksum index row).

**Steps:**
1. Trigger a reconciliation run via `POST /research/desk/coverage/reconcile/compute`.
2. Poll until terminal.
3. Inspect the returned run record's `store_errors` field.
4. Verify `BarIndex.reindex()` was called and the rebuilt index carries no row for the corrupted file's `series_id`.

**Expected outcome:** The run resolves with `state: "done"`. The `store_errors` field lists the corrupted file's name and error message verbatim, matching `BarStore.list()`'s own `errors` entry byte-for-byte. The rebuilt index has no row for that `series_id`.

**Pass criteria:** `store_errors` list is non-empty and matches BarStore's errors exactly; index query returns no row for the corrupted series_id.

---

### TC-06 — Honest empty reconcile runs endpoint

**Type:** api  
**Preconditions:** No reconciliation run has ever been recorded on a fresh scoped store.

**Steps:**
1. Call `GET /research/desk/coverage/reconcile/runs`.

**Expected outcome:** Returns HTTP 200 with `{"runs": [], "latest": null}`.

**Pass criteria:** Status code is 200; `runs` array is empty; `latest` is `null`.

---

### TC-07 — Reconcile runs store is append-only

**Type:** api  
**Preconditions:** One reconciliation run has been successfully recorded and returned via the runs endpoint.

**Steps:**
1. Note the first run's record and its file checksum.
2. Trigger a second reconciliation run and wait for it to complete.
3. Call `GET /research/desk/coverage/reconcile/runs` again.
4. Verify the first run file's checksum is unchanged.

**Expected outcome:** Both runs appear in the runs list, with the newest as `latest`. The first run's persisted file's SHA-256 checksum is identical to before the second run.

**Pass criteria:** `runs` length is 2; `latest.id` matches the second run; checksum of first run's file is unchanged.

---

### TC-08 — Reconciliation run does not modify bar store or other durable files

**Type:** api  
**Preconditions:** A scoped rig has recorded universe, screen, and top-up run files present before a reconciliation run.

**Steps:**
1. Checksum every `.data/bars/*.json` series file.
2. Checksum every previously recorded universe/screen/top-up-run file.
3. Trigger a reconciliation run and wait for completion.
4. Re-checksum all the same files.

**Expected outcome:** Every `.data/bars/*.json` file's SHA-256 is unchanged. Every previously recorded universe/screen/top-up-run file's checksum is unchanged (nothing backfilled or rewritten).

**Pass criteria:** All checksums match before and after; no new files created in .data/bars/; .data/ structure unchanged except for new reconcile run record.

---

### TC-09 — Idle poll on reconcile compute never triggers a run

**Type:** api  
**Preconditions:** No reconciliation job has ever run in the current process.

**Steps:**
1. Call `GET /research/desk/coverage/reconcile/compute`.

**Expected outcome:** Returns `null` and no reconciliation run is started as a side effect.

**Pass criteria:** Response is `null`; no run record is created; no background process started.

---

### TC-10 — Single-flight reconcile compute manager

**Type:** api  
**Preconditions:** A reconciliation job is already running (state: `"running"`).

**Steps:**
1. Issue a second `POST /research/desk/coverage/reconcile/compute` request.

**Expected outcome:** Returns `started: false` with the existing job's unchanged snapshot. No second concurrent job is started.

**Pass criteria:** Response includes `started: false`; returned snapshot id/state match the first job.

---

### TC-11 — Cancel reconcile compute returns 409 when idle

**Type:** api  
**Preconditions:** Either no reconciliation job has ever run, or the last one is terminal.

**Steps:**
1. Call `POST /research/desk/coverage/reconcile/compute/cancel`.

**Expected outcome:** Returns HTTP 409 with a message indicating that no reconciliation compute is currently running.

**Pass criteria:** Status code is 409; response body names the idle condition.

---

### TC-12 — Post-repair screen is a new append-only snapshot

**Type:** api  
**Preconditions:** The drift state of TC-04 has been repaired by one reconciliation run. A screen snapshot was computed before the repair and recorded.

**Steps:**
1. Note the pre-repair screen snapshot file and its `bar_store_signature`.
2. Trigger a second screen compute for the same universe and as-of date.
3. Note the new screen snapshot file and its `bar_store_signature`.
4. Verify both files exist and checksums match their recorded state.

**Expected outcome:** The new screen is a new append-only file under a new `bar_store_signature`. The previously recorded (pre-repair) screen snapshot file's checksum is unchanged on disk.

**Pass criteria:** `bar_store_signature` values differ between pre-repair and post-repair screens; both files exist; pre-repair file's checksum is unchanged.

---

### TC-13 — Full backend suite passes with sentinel checks

**Type:** api  
**Preconditions:** All backend code for this iteration is implemented.

**Steps:**
1. Run the full backend test suite: `pytest apps/backend/tests -v`.
2. Verify `Config().config_fingerprint()` output.
3. Check `apps/backend/app/config.py` exclusion set for new fields.

**Expected outcome:** Suite passes with ≥1369 tests passed / 8 skipped / 0 failed. `Config().config_fingerprint()` outputs `08e471b10130e1e2`. Exclusion set carries no new field.

**Pass criteria:** Test count matches expected (0 failures); fingerprint is exactly `08e471b10130e1e2`; no new Config fields added.

---

### TC-14 — MCP tool count remains 17

**Type:** api  
**Preconditions:** All backend code is implemented.

**Steps:**
1. Parse `apps/backend/tests/test_mcp_server.py`'s `EXPECTED_TOOLS` constant.
2. Run the test suite to verify the MCP server.

**Expected outcome:** `EXPECTED_TOOLS` still names exactly 17 tools, with no reconcile-named tool added.

**Pass criteria:** MCP tool count is 17; no new tool in the list.

---

### TC-15 — Zero diff on foundation files

**Type:** artifact  
**Preconditions:** All code changes are committed.

**Steps:**
1. Run `git diff --stat` scoped to `apps/backend/app/research/bar_index.py`, `bars.py`, `tradability.py`, `levels.py`, `desk_coverage.py`, `apps/frontend/components/StructureChart.tsx`.
2. Verify against iter-13 baseline.

**Expected outcome:** All five files show zero changes.

**Pass criteria:** `git diff --stat` output is empty for all named files.

---

### TC-16 — Copy discipline lint stays green

**Type:** api  
**Preconditions:** Frontend code with new Reconciliation section copy is implemented.

**Steps:**
1. Run `tests/test_copy_discipline.py` unmodified.

**Expected outcome:** Test passes with zero banned advice/imperative/prediction terms found in the new Reconciliation section's copy.

**Pass criteria:** Test passes; no banned terms detected in new copy.

---

### TC-17 — Browser: honest empty reconciliation state screenshot

**Type:** browser  
**Preconditions:** A fixture-scoped `/desk` environment is set up with one screen already computed showing a ranked row with a dark coverage badge (TC-01 drifted pair). NO reconciliation run has been triggered yet. This is the one-way-door capture.

**Steps:**
1. Open `/desk` in Chrome.
2. Locate the Index Reconciliation section.
3. Locate the ranked table row for the TC-01 pair.
4. Capture a screenshot showing both the empty Reconciliation section and the dark badge.

**Expected outcome:** The Index Reconciliation section displays "no reconciliation run recorded yet" or equivalent empty state, legible. The ranked table row's coverage badge for the drifted timeframe renders dark, legible.

**Pass criteria:** Screenshot shows honest empty state text; coverage badge is dark and visible; both in one frame.

---

### TC-18 — Browser: populated reconciliation state after run

**Type:** browser  
**Preconditions:** TC-17 screenshot has been captured on the same scoped rig. One reconciliation run has been triggered and completed. One NEW screen run has been computed (same universe/as-of). The same rig is still live.

**Steps:**
1. Open `/desk` in Chrome.
2. Locate the Index Reconciliation section.
3. Verify it shows the latest run's `series_on_disk`, `rows_indexed_before`/`after` counts, affected symbol×timeframe pairs, and any `store_errors`.
4. Locate the same ranked table row from TC-17.
5. Capture a screenshot showing the populated Reconciliation section and the now-lit badge.

**Expected outcome:** The Index Reconciliation section displays the run's counts and affected pairs, all legible. The same ranked table row's coverage badge now renders lit.

**Pass criteria:** Reconciliation section shows counts/affected-pairs text; badge is lit and visible; both in one frame; matches TC-17 row.

---

### TC-19 — Demo-narrator walkthrough: J-10 reconciliation journey

**Type:** browser  
**Preconditions:** The demo-narrator lane is dispatched at full depth. TC-17 and TC-18 have been captured on the same scoped rig. The rig is still live.

**Steps:**
1. Record the demo-narrator JSON walkthrough against the still-live scoped rig.
2. Capture frames for each step narrating: (a) empty state (honesty text), (b) reconciliation trigger, (c) populated state (counts, affected pairs, lit badge).
3. Ensure frames match their narration step-by-step.

**Expected outcome:** A valid demo-narrator JSON with `[NEW]` flag. Each frame's content matches its narration. Empty state step precedes populated state step. All frames captured on the same rig.

**Pass criteria:** J-10.json exists and is valid JSON; steps are in order (empty→populated); frame content matches narration text; `[NEW]` flag present.

---

### TC-20 — Corrupted run-record file surfaced as explicit error

**Type:** api  
**Preconditions:** One genuine reconciliation run record exists on disk. A deliberately corrupted second run-record file is placed in the same directory.

**Steps:**
1. Call `GET /research/desk/coverage/reconcile/runs`.
2. Inspect the response's `runs` list and any error field.

**Expected outcome:** The genuine record still appears in `runs` and `latest`. The corrupted file's verification failure is surfaced as an explicit, named error in the response. The error is never silently dropped or served as data.

**Pass criteria:** Genuine run appears in list; corrupted file is NOT in runs/latest; an error message names the corrupted file and failure reason.

---

## Summary

**Total test cases:** 20  
**API tests:** TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-10, TC-11, TC-12, TC-13, TC-14, TC-20 (15 tests)  
**Browser tests:** TC-17, TC-18, TC-19 (3 tests)  
**Artifact checks:** TC-15, TC-16 (2 tests)

**Key requirements verified:**
- Drift classification: three independent buckets (unindexed/orphan/stale-checksum) — TC-01, TC-02, TC-03
- Reconciliation repair workflow: end-to-end run with before/after verification — TC-04, TC-05
- Data durability: append-only store, honest empty state, no side effects — TC-06, TC-07, TC-08, TC-09
- Compute manager contract: single-flight, cancel idempotency — TC-10, TC-11
- Immutability proof: pre-repair screen checksum unchanged — TC-12
- Sentinel contracts: fingerprint, MCP tools, foundational files — TC-13, TC-14, TC-15, TC-16
- Browser-visible capability: honest empty state, then populated state on same rig — TC-17, TC-18
- Demo-narrator walkthrough with NEW flag — TC-19
- Error transparency: corrupted records surfaced, not dropped — TC-20
