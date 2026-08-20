# UI Test Results (merged)

**Date:** 2026-08-20
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 16/17 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-21-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-21-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-21-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-21-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-21-evidence/J-05-verify.png |
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-21-evidence/J-06-verify.png |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-21-evidence/J-08-verify.png |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-21-evidence/J-10-verify.png |
| UT-01 | `/desk` loads without errors | smoke | P1 | "Playbook Signals" visible, no console errors | Page rendered fully; "PLAYBOOK SIGNALS" heading visible; only console message was the React DevTools info line (no errors) | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-01-result.png` |
| UT-02 | Microscope Readiness band-touch count renders | happy-path | P1 | Value cell shows a plain integer or "not enumerated", never blank/raw JSON | `micro-readiness-band-touch-count` cell showed `0`; backend GET confirmed `{"status":"enumerated","count":0}`; "Joinable corpus — withheld (excluded)" row above still showed its own `0` unaffected | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-02-result.png` |
| UT-03 | Pilot grid triggers band_touch row | happy-path | P1 | Ledger chain verification `ok`; no empty state; family block visible; a trial row's Feature cell reads `divergence_at_level_bearish / threshold (band_touch)` | POST with `{"grid":"delta_divergence_pilot"}` returned `{"state":"running",...}`, completed; new family `divergence_at_level_bearish__band_touch__trades_20` appeared; Feature cell HTML confirmed exact text `divergence_at_level_bearish / threshold` + `(band_touch)` span; Ledger chain verification: ok | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-03-result.png` |
| UT-04 | Walk-forward floor-check row renders | happy-path | P2 | A second ledger row under the same `candidate_id`, Feature/Horizon = `—`, Decision = `insufficient_n`, `screen_result` JSON `null` | Only ONE trial row exists for the `divergence_at_level_bearish__band_touch__trades_20` family (`variants_tried: 1`); no second row of any kind exists under `cand-a5f1eff2380a1674` or any other candidate_id. Source inspection confirms why: `ScoutComputeManager.trigger()` → `run_scout_grid_and_record()` calls ONLY `register_and_screen_candidate` (never `register_screen_and_walkforward_check`), and `register_screen_and_walkforward_check` (the function that appends the walk-forward floor-check as a second ledger row) is called ONLY from `tests/test_scout.py` — it is not reachable from any live route, the CLI, or the compute manager. The walk-forward floor-check-as-ledger-row capability exists in source but is not wired to any production/UI-reachable path. | FAIL | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-04-fail.png` |
| UT-05 | Studies 1/3 never ledgered | validation | P1 | No row anywhere matches Study 1 (`failed_aggression_score`+`band_touch`) or Study 3 (`setup_id=capitulation`); only the divergence candidate + its walk-forward companion row exist | Full on-screen inspection (4 family blocks) and the raw `GET /research/desk/micro/scout` JSON confirm zero rows match Study 1's signature and zero rows have `structure_context.setup_id=="capitulation"` — the core non-leakage claim this test exists to check is TRUE. Caveat: the JSON also shows no walk-forward companion row exists at all (same underlying gap as UT-04 — see that row for detail), so the expected result's "and its walk-forward floor-check companion row exist" clause does not literally hold; this is not a new/different defect, it is UT-04's finding restated. | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-05-result.png` |
| UT-06 | Backend-unavailable panel (element capture) | error | P2 | `scout-ledger-unavailable` element visible with real, non-empty failure text | With `window.fetch` overridden to reject any `/research/desk/micro/scout` (non-`/compute`) call, the element's `textContent` read "Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place." — real message text, not blank/spinner | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-06-result.png` (tightly cropped to the element, per the element-capture requirement) |
| UT-07 | Default "Run Screen" control unchanged | regression | P1 | POST body empty/no `grid` field; resulting rows are `structure_context.kind="none"` with no parenthetical suffix | Installed a `window.fetch` interceptor before clicking the shipped compute-trigger button (`data-testid="scout-ledger-trigger"`, rendered label "Run Screen" — the plan's informal "Run Scout" name for this same control); captured POST had no `body` field at all. Resulting 6 trial rows (3 families) all carried `structure_context.kind:"none"` in the raw JSON, and all 6 rendered Feature cells read exactly `<feature> / threshold` with no `(...)` suffix. | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-07-result.png` |
| UT-08 | J-10 restored assertions pass | regression | P1 | "Built from signature:" after expanding Playbook Evidence; "recorded signals, none hidden" after filling the date input; every other shipped section's golden text unchanged | Replayed J-10.json's full step sequence (watch SIM-BUYER → Buyer Control; /structure AAPL as-of 2026-06-22 16:00:00 → "300.11–302.2"; /desk). "Built from signature: 4478fd73a536cc80" appeared after step 2. "4 recorded signals, none hidden" appeared after filling `desk-playbook-date-input` with `2026-06-22`. All 7 remaining sections expanded and confirmed: "Distinct symbol-days" (Microscope Readiness), "No candidates ledgered." (Scout Ledger, pre-UT-03/07), "No fold specs registered." (Walk-Forward), "iter18-qa-universe" (Validation Vault), "config fingerprint 08e471b10130e1e2" (Referee Registry), "No hypotheses registered." (Referee Adjudications), "No evaluation runs recorded yet." (Referee Runs) | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-08-result.png` |
| UT-09 | Pilot grid has no discoverable UI control | ux | P2 | No button/dropdown/field selects the pilot grid anywhere on `/desk`; zero matches for `delta_divergence_pilot` in rendered DOM text | Expanded every section on `/desk` and searched the full rendered HTML: zero occurrences of the string `delta_divergence_pilot`; the only two "pilot" occurrences are the plain descriptive label "Pilot-Study Floors" / "pilot-study floor" in Microscope Readiness (not a control); no `<select>` element tied to a Scout grid parameter exists anywhere; the compute-trigger button takes no parameter | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-09-result.png` |

## Failed Tests

### UT-04 — Walk-forward floor-check row renders

**Verdict:** FAIL
**Failure:** Only ONE trial row exists for the `divergence_at_level_bearish__band_touch__trades_20` family (`variants_tried: 1`); no second row of any kind exists under `cand-a5f1eff2380a1674` or any other candidate_id. Source inspection confirms why: `ScoutComputeManager.trigger()` → `run_scout_grid_and_record()` calls ONLY `register_and_screen_candidate` (never `register_screen_and_walkforward_check`), and `register_screen_and_walkforward_check` (the function that appends the walk-forward floor-check as a second ledger row) is called ONLY from `tests/test_scout.py` — it is not reachable from any live route, the CLI, or the compute manager. The walk-forward floor-check-as-ledger-row capability exists in source but is not wired to any production/UI-reachable path.
**Evidence:** ``reports/qa/goal-rapid-microscope-iter-21-evidence/UT-04-fail.png``

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-20


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | J-07 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
