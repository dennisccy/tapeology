# UI Test Results (merged)

**Date:** 2026-09-05
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 1/5 journeys passed (4 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The artifact is a pure projection with semantic identity, provenance and integrity | smoke | P1 | Served JSON at `/tape/SIM-BIDABS/observation` shows `schema_version` `tape-observation-v1`, `engine_semantics_version` `tape-engine-v1`, `config_fingerprint` `08e471b10130e1e2`, non-empty `session_id`, 64-hex `observation_hash`/`artifact_hash`; `test_tape_observation_projection.py` 0 failures | Out of scope this dispatch (see scope note). Pre-existing evidence inspected: `UT-J-01-result.png` (already on disk) shows genuine correct content matching every Expected clause, fetched from the backend origin. See Notes. | SKIP | `reports/qa/goal-observation-contract-iter-5-evidence/UT-J-01-result.png` (pre-existing, not captured this dispatch) |
| UT-J-02 | Market-event time, measured availability and generation time are three distinct, honest instants, read atomically | smoke | P1 | Served JSON shows `observed_at_utc` starting `2024-01-02T14:3`, `available_at_utc` null, `availability_basis` `simulated_not_applicable`, `timing.settled_at_utc`/`generated_at_utc` on today's date; `test_tape_observation_time.py` 0 failures | Out of scope this dispatch (see scope note). Pre-existing evidence inspected: only `J-02-verify.png` exists, an idle "No ticker watched" baseline screenshot — it does not show the observation endpoint's time fields at all. See Notes. | SKIP | `reports/qa/goal-observation-contract-iter-5-evidence/J-02-verify.png` (pre-existing, incomplete — see Notes) |
| UT-J-03 | Lifecycle, feed basis and session identity stay honest | smoke | P1 | `lifecycle.stream_status` moves live→paused→live, `tape_state`/`settled_at_utc` unchanged across pause, 404 after Stop, re-watch shows new `session_id`; `test_tape_observation_lifecycle_feed.py` 0 failures | Out of scope this dispatch (see scope note). Pre-existing evidence inspected: `UT-J-03-result.png` (already on disk) shows genuine correct live content (`stream_status":"live"`, full field set) fetched from the backend origin. See Notes. | SKIP | `reports/qa/goal-observation-contract-iter-5-evidence/UT-J-03-result.png` (pre-existing, not captured this dispatch) |
| UT-J-04 | Ingestion-path equivalence under an identical valid event stream | smoke | P1 | Two reloads of a paused observation show identical `observation_hash`, different `generated_at_utc`/`artifact_hash`; `test_tape_observation_path_equivalence.py` 0 failures | Out of scope this dispatch (see scope note). Pre-existing evidence inspected: `J-04-verify.png` (already on disk) shows Next.js's own "404 — This page could not be found" page — that verification attempt hit the wrong origin (frontend, not backend) and never actually observed real content. See Notes (structural finding). | SKIP | `reports/qa/goal-observation-contract-iter-5-evidence/J-04-verify.png` (pre-existing, shows a wrong-origin miss — see Notes) |
| UT-J-05 | One read-only machine path | smoke | P1 | `/tape/SIM-BIDABS/observation` renders JSON with `"schema_version":"tape-observation-v1"`; `/tape/ZZZZ/observation` renders a 404 body (same shape as `/tape/ZZZZ/state`); `tests/test_tape_observation_route.py` passes with 0 failures incl. `test_counterexample_*` | Watched `SIM-BIDABS` on Cockpit (confirmed "live" text), then opened `http://localhost:8301/tape/SIM-BIDABS/observation` directly (the backend origin — see Notes on why not `:3301`) and confirmed `"schema_version":"tape-observation-v1"` plus the full field set; opened `http://localhost:8301/tape/ZZZZ/observation`, confirmed body `{"detail":"Ticker 'ZZZZ' is not being watched"}`, byte-identical (curl-verified) to `/tape/ZZZZ/state`'s 404 body; ran `pytest apps/backend/tests/test_tape_observation_route.py` → "8 passed, 2 warnings in 16.25s", 0 failed, including both `test_counterexample_*` tests | PASS | `reports/qa/goal-observation-contract-iter-5-evidence/UT-J-05-result.png` |

## Skipped Tests

### UT-J-01 — The artifact is a pure projection with semantic identity, provenance and integrity

**Verdict:** SKIPPED
**Reason:** Out of scope this dispatch (see scope note). Pre-existing evidence inspected: `UT-J-01-result.png` (already on disk) shows genuine correct content matching every Expected clause, fetched from the backend origin. See Notes.

### UT-J-02 — Market-event time, measured availability and generation time are three distinct, honest instants, read atomically

**Verdict:** SKIPPED
**Reason:** Out of scope this dispatch (see scope note). Pre-existing evidence inspected: only `J-02-verify.png` exists, an idle "No ticker watched" baseline screenshot — it does not show the observation endpoint's time fields at all. See Notes.

### UT-J-03 — Lifecycle, feed basis and session identity stay honest

**Verdict:** SKIPPED
**Reason:** Out of scope this dispatch (see scope note). Pre-existing evidence inspected: `UT-J-03-result.png` (already on disk) shows genuine correct live content (`stream_status":"live"`, full field set) fetched from the backend origin. See Notes.

### UT-J-04 — Ingestion-path equivalence under an identical valid event stream

**Verdict:** SKIPPED
**Reason:** Out of scope this dispatch (see scope note). Pre-existing evidence inspected: `J-04-verify.png` (already on disk) shows Next.js's own "404 — This page could not be found" page — that verification attempt hit the wrong origin (frontend, not backend) and never actually observed real content. See Notes (structural finding).

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-09-05


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | J-06 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
