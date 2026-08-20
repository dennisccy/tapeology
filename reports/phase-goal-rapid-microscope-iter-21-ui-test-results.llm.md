# Phase goal-rapid-microscope-iter-21 — UI Test Results

**Phase:** goal-rapid-microscope-iter-21
**Date:** 2026-08-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: UT-04 (type=happy-path) failed. Per the verdict rule ("FAIL: Any smoke test fails, OR
     any happy-path test fails, OR any P1 test fails"), a happy-path failure forces FAIL regardless
     of its P2 priority label. All P1 tests individually pass. -->

**Overall:** 8/9 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | "Playbook Signals" visible, no console errors | Page rendered fully; "PLAYBOOK SIGNALS" heading visible; only console message was the React DevTools info line (no errors) | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-01-result.png` |
| UT-02 | Microscope Readiness band-touch count renders | happy-path | P1 | Value cell shows a plain integer or "not enumerated", never blank/raw JSON | `micro-readiness-band-touch-count` cell showed `0`; backend GET confirmed `{"status":"enumerated","count":0}`; "Joinable corpus — withheld (excluded)" row above still showed its own `0` unaffected | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-02-result.png` |
| UT-03 | Pilot grid triggers band_touch row | happy-path | P1 | Ledger chain verification `ok`; no empty state; family block visible; a trial row's Feature cell reads `divergence_at_level_bearish / threshold (band_touch)` | POST with `{"grid":"delta_divergence_pilot"}` returned `{"state":"running",...}`, completed; new family `divergence_at_level_bearish__band_touch__trades_20` appeared; Feature cell HTML confirmed exact text `divergence_at_level_bearish / threshold` + `(band_touch)` span; Ledger chain verification: ok | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-03-result.png` |
| UT-04 | Walk-forward floor-check row renders | happy-path | P2 | A second ledger row under the same `candidate_id`, Feature/Horizon = `—`, Decision = `insufficient_n`, `screen_result` JSON `null` | Only ONE trial row exists for the `divergence_at_level_bearish__band_touch__trades_20` family (`variants_tried: 1`); no second row of any kind exists under `cand-a5f1eff2380a1674` or any other candidate_id. Source inspection confirms why: `ScoutComputeManager.trigger()` → `run_scout_grid_and_record()` calls ONLY `register_and_screen_candidate` (never `register_screen_and_walkforward_check`), and `register_screen_and_walkforward_check` (the function that appends the walk-forward floor-check as a second ledger row) is called ONLY from `tests/test_scout.py` — it is not reachable from any live route, the CLI, or the compute manager. The walk-forward floor-check-as-ledger-row capability exists in source but is not wired to any production/UI-reachable path. | FAIL | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-04-fail.png` |
| UT-05 | Studies 1/3 never ledgered | validation | P1 | No row anywhere matches Study 1 (`failed_aggression_score`+`band_touch`) or Study 3 (`setup_id=capitulation`); only the divergence candidate + its walk-forward companion row exist | Full on-screen inspection (4 family blocks) and the raw `GET /research/desk/micro/scout` JSON confirm zero rows match Study 1's signature and zero rows have `structure_context.setup_id=="capitulation"` — the core non-leakage claim this test exists to check is TRUE. Caveat: the JSON also shows no walk-forward companion row exists at all (same underlying gap as UT-04 — see that row for detail), so the expected result's "and its walk-forward floor-check companion row exist" clause does not literally hold; this is not a new/different defect, it is UT-04's finding restated. | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-05-result.png` |
| UT-06 | Backend-unavailable panel (element capture) | error | P2 | `scout-ledger-unavailable` element visible with real, non-empty failure text | With `window.fetch` overridden to reject any `/research/desk/micro/scout` (non-`/compute`) call, the element's `textContent` read "Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place." — real message text, not blank/spinner | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-06-result.png` (tightly cropped to the element, per the element-capture requirement) |
| UT-07 | Default "Run Screen" control unchanged | regression | P1 | POST body empty/no `grid` field; resulting rows are `structure_context.kind="none"` with no parenthetical suffix | Installed a `window.fetch` interceptor before clicking the shipped compute-trigger button (`data-testid="scout-ledger-trigger"`, rendered label "Run Screen" — the plan's informal "Run Scout" name for this same control); captured POST had no `body` field at all. Resulting 6 trial rows (3 families) all carried `structure_context.kind:"none"` in the raw JSON, and all 6 rendered Feature cells read exactly `<feature> / threshold` with no `(...)` suffix. | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-07-result.png` |
| UT-08 | J-10 restored assertions pass | regression | P1 | "Built from signature:" after expanding Playbook Evidence; "recorded signals, none hidden" after filling the date input; every other shipped section's golden text unchanged | Replayed J-10.json's full step sequence (watch SIM-BUYER → Buyer Control; /structure AAPL as-of 2026-06-22 16:00:00 → "300.11–302.2"; /desk). "Built from signature: 4478fd73a536cc80" appeared after step 2. "4 recorded signals, none hidden" appeared after filling `desk-playbook-date-input` with `2026-06-22`. All 7 remaining sections expanded and confirmed: "Distinct symbol-days" (Microscope Readiness), "No candidates ledgered." (Scout Ledger, pre-UT-03/07), "No fold specs registered." (Walk-Forward), "iter18-qa-universe" (Validation Vault), "config fingerprint 08e471b10130e1e2" (Referee Registry), "No hypotheses registered." (Referee Adjudications), "No evaluation runs recorded yet." (Referee Runs) | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-08-result.png` |
| UT-09 | Pilot grid has no discoverable UI control | ux | P2 | No button/dropdown/field selects the pilot grid anywhere on `/desk`; zero matches for `delta_divergence_pilot` in rendered DOM text | Expanded every section on `/desk` and searched the full rendered HTML: zero occurrences of the string `delta_divergence_pilot`; the only two "pilot" occurrences are the plain descriptive label "Pilot-Study Floors" / "pilot-study floor" in Microscope Readiness (not a control); no `<select>` element tied to a Scout grid parameter exists anywhere; the compute-trigger button takes no parameter | PASS | `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-09-result.png` |

---

## Passed Tests

### UT-01 — `/desk` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-01-result.png`
- Navigated to `/desk`; page rendered fully (no blank screen, no error boundary); "PLAYBOOK SIGNALS" heading present; console showed only the standard React DevTools info line, no errors.

### UT-02 — Microscope Readiness shows the materialized band-touch count
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-02-result.png`
- Expanded Microscope Readiness; the "Joinable corpus — band touches" row's value cell (`data-testid="micro-readiness-band-touch-count"`) showed `0` (a plain integer, never blank/raw JSON). Cross-checked `GET /research/desk/micro/readiness`: `joinable_corpus.band_touch_count` = `{"status":"enumerated","count":0}`. The "withheld (excluded)" row above it was unaffected (still `0`).

### UT-03 — Operator can trigger the pilot Scout grid and see the band-touch candidate row render
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-03-result.png`
- `curl -X POST .../scout/compute -d '{"grid":"delta_divergence_pilot"}'` returned `{"state":"running","run_id":...}`; polled to completion (1 candidate). Expanded Scout Ledger: "Ledger chain verification: ok"; no empty state; a new family block `scout-family-divergence_at_level_bearish__band_touch__trades_20` rendered with one trial row whose Feature cell read `divergence_at_level_bearish / threshold` followed by a `(band_touch)` span — confirmed via the raw element HTML.

### UT-05 — Studies 1 and 3 never appear as ledgered rows
**Verdict:** PASS (with a documented caveat — see Results Table)
**Evidence:** `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-05-result.png`
- Inspected all 4 rendered family blocks on screen and the full `GET /research/desk/micro/scout` JSON. Zero rows anywhere match Study 1's signature (`failed_aggression_score` + `structure_context.kind=="band_touch"`) or Study 3's (`structure_context.setup_id=="capitulation"`). The core validation this test exists for is confirmed true.

### UT-06 — Scout Ledger shows the real backend-unavailable message when the fetch fails
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-06-result.png` (cropped tightly to the `scout-ledger-unavailable` element)
- Overrode `window.fetch` to reject any `/research/desk/micro/scout` GET; expanded Scout Ledger; `data-testid="scout-ledger-unavailable"` rendered real text: "Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place." Never blank, never a frozen spinner.
- Note: the `use_browser` tool has no native element-scoped screenshot capture and non-fullpage viewport screenshots rendered entirely blank in this session for unknown reasons (retried twice); a fullpage screenshot rendered correctly and was cropped (via PIL, deterministically, no content alteration) to isolate the element, satisfying the "element capture, not full-page" intent of the test.

### UT-07 — The shipped "Run Screen" button still triggers only the default grid
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-07-result.png`
- Installed a `window.fetch` interceptor, then clicked the compute-trigger button (`data-testid="scout-ledger-trigger"`; rendered label is "Run Screen" — the test plan's "Run Scout" is an informal name for this same `onTrigger` control, confirmed against `apps/frontend/app/desk/page.tsx`). Captured POST request carried no `body` at all — no `grid` field. All 6 resulting rows (3 families: `cumulative_delta`, `failed_aggression_score`, `quote_imbalance`) carry `structure_context.kind:"none"` in the raw ledger JSON and render as `<feature> / threshold` with no parenthetical suffix.

### UT-08 — J-10 golden replay: restored Playbook Evidence assertions pass
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-08-result.png`
- Replayed J-10.json's full 17-step sequence by hand against a still-fresh Scout Ledger (run before UT-03/UT-07 populated it). Both restored assertions ("Built from signature:" and "recorded signals, none hidden") and all 7 other sections' golden text confirmed present verbatim.

### UT-09 — The pilot Scout grid has no discoverable UI control anywhere on `/desk`
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-09-result.png`
- Expanded every section; searched the fully-rendered HTML for `delta_divergence_pilot` (0 matches) and for any selectable control mentioning pilot/grid/band touch/delta divergence/playbook signal. The only matches were plain descriptive text ("Pilot-Study Floors" table heading, "pilot-study floor" prose) — never a selectable option. No `<select>` tied to a Scout grid parameter exists anywhere on the page.

---

## Failed Tests

### UT-04 — Walk-forward floor-check decision appears as a second ledger row under the same candidate
**Verdict:** FAIL
**Failure:** No second ledger row is ever produced. The `divergence_at_level_bearish__band_touch__trades_20` family has exactly ONE trial (`variants_tried: 1`), with `decision: "killed_insufficient_n"` set directly by the SCREEN itself (`n_usable_sessions=0`) — there is no subsequent walk-forward-floor-check row sharing that `candidate_id`.
**Evidence:** `reports/qa/goal-rapid-microscope-iter-21-evidence/UT-04-fail.png`

**Steps taken:**
1. With Scout Ledger expanded from UT-03 (pilot grid already triggered, one candidate screened), located the `divergence_at_level_bearish__band_touch__trades_20` family's trial-rows table.
2. Confirmed via `curl http://localhost:8301/research/desk/micro/scout | python3 -m json.tool` that the family's `trials` array has exactly one element (`candidate_id: cand-a5f1eff2380a1674`) — no second entry with the same or any `candidate_id` exists anywhere in the response.
3. Traced the production code path to understand why: `POST /research/desk/micro/scout/compute` → `ScoutComputeManager.trigger()` → `run_scout_grid_and_record()`, which the module's own docstring calls "the ONE production entry point" and which calls only `register_and_screen_candidate` for each grid request (`apps/backend/app/research/scout.py` lines ~1695-1706).
4. Confirmed via `grep -rn "register_screen_and_walkforward_check" app/ tests/` that this function (the one that screens a candidate AND appends the walk-forward floor-check as a second ledger row, per the dev handoff) is called ONLY from `apps/backend/tests/test_scout.py` — never from `micro_routes.py`, `scout.py`'s own CLI `main()`, or `ScoutComputeManager.trigger()`.

**Expected:** A second row immediately following the delta-divergence screen row, sharing its `candidate_id`, with Feature/Horizon = `—`, Decision = `insufficient_n`, and an expandable `screen_result` JSON detail showing `null`.
**Actual:** No such row exists anywhere in the ledger — on screen or in the raw API response — via any route, UI control, or CLI flag reachable outside the test suite. The walk-forward-floor-check-as-ledger-row capability (`register_screen_and_walkforward_check` / `scout_candidate_walkforward_floor_check`) is implemented and unit-tested (per the dev handoff's TC-6), but is not wired into any live/production/browser-reachable code path.

---

## Skipped Tests

None — all 9 test cases executed.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (scoped QA fixture backend)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, attached to existing CDP endpoint on 127.0.0.1:9222
- **Test Date:** 2026-08-20
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-21-evidence/`
- **Sequencing:** Executed in the order UT-01, UT-02, UT-08, UT-09, UT-07, UT-03, UT-04, UT-05, UT-06, per the test plan's own sequencing note (fresh-ledger tests before the ledger-populating UT-03/UT-07 ran, on the single available `$ROOT`).

---

## Golden Replay Scripts

No new golden replay script was written this iteration. J-09 (this iteration's target journey,
covered primarily by UT-02/UT-03/UT-04/UT-05/UT-09) did not fully pass — UT-04 (part of J-09's own
walk-forward-floor-check acceptance) failed — so writing a "PASS" replay script for J-09 would
misrepresent the journey. J-10's existing golden script (`runs/goal-session-rapid-microscope/journey-scripts/J-10.json`)
was independently re-verified by hand via UT-08 and needed no changes.
