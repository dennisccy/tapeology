# Goal Iteration 4 Functional Test Plan

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-4
**Date:** 2026-06-10
**Frontend Present:** yes

## Phase Goal

Implement the verdict-transition engine (J-40–J-46) that continuously judges the declared thesis against live tape with explicit verdict states (pending, confirming, weakening, rejecting, invalidated) and plain-language evidence, plus fix visual-evidence defects (J-38/J-39) by capturing thesis strip with correct framing.

## Test Cases

### TC-01 — J-40: Absorption Reversal confirms only on control flip, not sustained absorption

**Type:** browser
**Preconditions:** Browser loads the app; backend running; thesis strip visible on page.

**Steps:**
1. Stop any existing watch to clear thesis state.
2. Navigate to watch SIM-REVERSAL ticker.
3. Declare an absorption_reversal/long thesis during the absorption phase.
4. Scroll the thesis strip into view.
5. Take a screenshot showing verdict is `pending` with premise met / trigger not-yet evidence.
6. Continue watching through absorption; verify verdict remains `pending`.
7. Wait for buyer_control phase to begin (SIM-REVERSAL transitions).
8. Verify verdict transitions to `confirming` with evidence citing the flip (e.g., "buyers took control with real upward impact").
9. Check `GET /research/journal/{thesis_id}` contains both transitions in timeline with `rule_first_true` and `published_at` recorded.
10. Take screenshot showing thesis strip with `confirming` verdict and evidence visible.

**Expected outcome:** Verdict stays pending during absorption despite strong buy volume, transitions to confirming only after buyer control begins. Timeline persists both transitions with timestamps.
**Pass criteria:** Verdict shows exactly `pending → confirming` transition; evidence mentions flip, not just absorption; timeline JSON contains both events with `rule_first_true` ≠ `published_at`; screenshot visibly shows thesis strip.

---

### TC-02 — J-41: Trend Continuation shows rejecting when opposing control detected

**Type:** browser
**Preconditions:** Browser loaded; backend running.

**Steps:**
1. Stop any existing watch.
2. Navigate to SIM-SELLER ticker.
3. Declare trend_continuation/long with far invalidation price.
4. Wait for seller_control phase to establish.
5. Scroll strip into view; take screenshot showing verdict state.
6. Verify verdict state is `rejecting` with evidence citing seller control and impact.
7. Confirm thesis remains active (not resolved) on the strip.
8. Fetch `GET /research/journal/{thesis_id}` and verify the single `rejecting` entry.

**Expected outcome:** Verdict published as `rejecting` (not confirming) with opposing-control evidence; thesis stays active, not auto-resolved.
**Pass criteria:** Verdict displays `rejecting` state; evidence mentions seller control/impact; thesis not resolved; screenshot shows strip with verdict visible.

---

### TC-03 — J-42: Trend Continuation confirms and holds without flapping

**Type:** browser
**Preconditions:** Browser loaded; backend running.

**Steps:**
1. Stop any existing watch.
2. Navigate to SIM-BUYER ticker.
3. Declare trend_continuation/long thesis during buyer control phase.
4. Scroll strip into view; capture screenshot showing verdict progression.
5. Wait for the per-setup dwell period to elapse.
6. Verify verdict transitions to `confirming` after dwell.
7. Continue watching for at least 3 additional tick cycles.
8. Confirm verdict remains `confirming` with no reversion to `pending`.
9. Fetch timeline via `GET /research/journal/{thesis_id}` and verify single `confirming` entry, no oscillation.

**Expected outcome:** Verdict transitions to confirming after dwell and remains stable. No flapping or silent reverts to pending.
**Pass criteria:** Verdict shows `confirming` state; timeline has exactly one `confirming` entry; no pending state re-appears after confirmation; screenshot shows strip in confirming state.

---

### TC-04 — J-43: Confirmed thesis publishes weakening when supporting evidence fades

**Type:** browser
**Preconditions:** Browser loaded; backend running; SIM-SHIFT available.

**Steps:**
1. Stop any existing watch.
2. Navigate to SIM-SHIFT ticker.
3. Declare trend_continuation/long during strong buyer control phase.
4. Wait for dwell and verify verdict reaches `confirming`.
5. Scroll strip into view and capture confirming state.
6. Continue watching as SIM-SHIFT phase transitions (control weakens/becomes unclear).
7. Wait for weakening dwell period post-shift.
8. Verify verdict transitions to `weakening` with evidence mentioning faded support (e.g., "supporting evidence faded").
9. Fetch `GET /research/journal/{thesis_id}` and verify timeline has both `confirming` and `weakening` entries.
10. Capture screenshot showing `weakening` state on strip.

**Expected outcome:** Verdict shows explicit `weakening` transition (not silent revert to pending) with supporting-evidence-faded register. Timeline preserves both states.
**Pass criteria:** Verdict displays `weakening` state after control fades; evidence mentions "faded" or similar; timeline contains `confirming` then `weakening` events; screenshot shows strip in weakening state.

---

### TC-05 — J-44: Invalidation trigger fires robustly on qualifying print

**Type:** browser
**Preconditions:** Browser loaded; backend running.

**Steps:**
1. Stop any existing watch.
2. Navigate to SIM-SELLER ticker.
3. Declare any long thesis with invalidation price set just below current market level.
4. Scroll strip into view; capture initial thesis state.
5. Continue watching as price approaches invalidation level.
6. When a print occurs at or beyond the invalidation level (by ≥ configured ε or k-consecutive), verify verdict transitions to `invalidated`.
7. Confirm thesis displays terminal invalidated treatment (not idle declare affordance).
8. Verify thesis auto-resolved with state `invalidated` (not just pending conviction change).
9. Fetch `GET /research/journal/{thesis_id}` and verify final entry contains offending print price and logical timestamp.
10. Capture screenshot showing terminal invalidated strip treatment.

**Expected outcome:** Single qualifying print beyond invalidation triggers immediate verdict transition to `invalidated` and thesis auto-resolves. Terminal treatment shown on strip. Offending print recorded in timeline.
**Pass criteria:** Verdict state is `invalidated`; thesis shows resolved terminal treatment; journal timeline final entry contains price + logical_ts; screenshot visibly shows terminal invalidated state.

---

### TC-06 — J-44 robustness: Lone print inside guard does NOT invalidate

**Type:** api
**Preconditions:** Backend running; engine capable of synthetic event injection.

**Steps:**
1. Declare a thesis with invalidation guard (ε·spread) configured.
2. Inject a single print just inside the guard boundary (not meeting the ≥ε threshold).
3. Fetch `GET /research/journal/{thesis_id}` and verify no `invalidated` entry.
4. Verify thesis remains in its prior state (pending/confirming/etc.).
5. Inject a qualifying print (≥ε beyond guard).
6. Verify verdict immediately transitions to `invalidated` and thesis auto-resolves.

**Expected outcome:** Lone interior print does not trigger invalidation. Only prints meeting ≥ε or k-consecutive criterion invalidate.
**Pass criteria:** Step 4 shows no `invalidated` entry; step 6 shows `invalidated` entry present; thesis resolved only after qualifying print.

---

### TC-07 — J-45: Level Break latches: no confirm until level crossed

**Type:** browser
**Preconditions:** Browser loaded; backend running.

**Steps:**
1. Stop any existing watch.
2. Navigate to SIM-BUYER ticker.
3. Declare level_break/long thesis with declared level ABOVE current last price.
4. Scroll strip into view; capture screenshot showing level and pending verdict.
5. Wait for strong buyer control to establish (control alone does not confirm pre-cross).
6. Verify verdict remains `pending` with evidence noting cross statement not-yet or control insufficient.
7. Continue watching until price crosses the declared level.
8. Verify verdict transitions to `confirming` after cross + control hold, citing cross + control in evidence.
9. Fetch timeline and confirm single `confirming` entry after the cross event.
10. Capture screenshot showing confirming state post-cross.

**Expected outcome:** Verdict stays pending despite strong control until price crosses declared level. Confirms only after cross + control hold.
**Pass criteria:** Verdict shows `pending` pre-cross despite buyer control; transitions to `confirming` post-cross; evidence mentions cross and control; screenshot shows strip with level and verdict visible.

---

### TC-08 — J-46: Failed Move Fade confirms during absorption, stays confirming through reclaim

**Type:** browser
**Preconditions:** Browser loaded; backend running.

**Steps:**
1. Stop any existing watch.
2. Navigate to SIM-REVERSAL ticker.
3. Declare failed_move_fade/long thesis during absorption phase.
4. Scroll strip into view; capture absorption state.
5. Verify verdict transitions to `confirming` DURING the absorption (expected behaviour for failed-move absorption).
6. Capture screenshot showing confirming state during absorption.
7. Continue watching through reclaim phase (price recovers from failed move).
8. Verify verdict remains `confirming` (no revert to pending or transition to weakening).
9. Fetch timeline and confirm single `confirming` entry, no oscillation.
10. Capture screenshot showing confirming state post-reclaim.

**Expected outcome:** Verdict confirms during absorption (not pending); remains confirming through reclaim. Asymmetric from J-40 (absorption_reversal requires flip).
**Pass criteria:** Verdict shows `confirming` during absorption; no state change through reclaim; timeline has single `confirming` entry; screenshots show strip in confirming state at both phases.

---

### TC-09 — J-38: Active thesis render with thesis strip visibly in frame

**Type:** browser
**Preconditions:** Browser loaded; backend running.

**Steps:**
1. Stop any existing watch to ensure clean state.
2. Navigate to a supported ticker and watch it.
3. Declare a thesis.
4. Scroll the thesis strip into the viewport (do NOT capture with strip below fold).
5. Take a full-page screenshot or scroll screenshot ensuring strip is visible in pixels.
6. Verify screenshot contains: thesis declaration, current verdict state, evidence line, strip styling.
7. REST call to `GET /research/thesis/active` cross-checks thesis data returned.

**Expected outcome:** Thesis strip renders on cockpit; screenshot visibly shows all active thesis elements.
**Pass criteria:** Screenshot PNG contains thesis strip with visible content; REST response matches UI render; no viewport-top capture of below-fold strip.

---

### TC-10 — J-39: Thesis declaration 422 error with form values preserved and error message inline

**Type:** browser
**Preconditions:** Browser loaded; backend running.

**Steps:**
1. Open thesis declaration form.
2. Enter invalid thesis data (e.g., missing required field or contradictory level/invalidation).
3. Submit the form.
4. Scroll the error message into view (do NOT capture with message below fold).
5. Take a screenshot showing error message, form state, and filled values preserved.
6. Verify form fields retain user-entered values (not cleared).
7. Verify error message is inline on the form or in a visible alert.

**Expected outcome:** 422 error displayed inline; form values preserved; screenshot visibly shows both error and form state.
**Pass criteria:** Screenshot PNG shows error message and form values in the same frame; values not cleared; no hidden-below-fold error.

---

### TC-11 — J-68: Thesis strip idle declare affordance captured visibly

**Type:** browser
**Preconditions:** Browser loaded; backend running; no active thesis.

**Steps:**
1. Stop any active watch or ensure thesis is resolved.
2. Navigate to cockpit.
3. Verify thesis strip shows idle declare affordance (e.g., "declare a thesis" button/prompt).
4. Scroll the declare affordance into viewport.
5. Take a screenshot showing the idle strip with declare button/prompt visibly in frame.

**Expected outcome:** Thesis strip declare affordance captured with visible UI element in screenshot.
**Pass criteria:** Screenshot PNG contains idle thesis strip with declare affordance visible in pixels; not below fold.

---

### TC-12 — J-38/J-39 REST cross-check: GET /research/thesis/active projection matches UI

**Type:** api
**Preconditions:** Active thesis exists; backend running.

**Steps:**
1. Declare a thesis via browser UI.
2. Call `GET /research/thesis/active` REST endpoint.
3. Verify response includes thesis fields: id, setup_type, direction, invalidation, current verdict (if evaluated).
4. Compare REST response data against values visible in the thesis strip screenshot from TC-09.
5. Verify no field mismatch.

**Expected outcome:** REST projection and UI render show identical thesis data.
**Pass criteria:** REST response JSON contains thesis id, setup_type, invalidation; verdict field matches strip display; no 404 or mismatched data.

---

### TC-13 — J-40–J-46 verdict event appending: `GET /research/journal/{id}` returns append-only timeline

**Type:** api
**Preconditions:** Thesis declared; verdicts evaluated; backend running.

**Steps:**
1. Declare a thesis and let verdicts evaluate over multiple phases (e.g., SIM-REVERSAL: pending → confirming).
2. Call `GET /research/journal/{thesis_id}`.
3. Verify response contains `thesis` object + `verdict_events` array.
4. Verify each event has: `logical_ts`, `wall_ts`, `verdict`, `evidence`, `tape_state`, `confidence`, `last`, `rule_first_true`, `published_at`.
5. Verify events are ordered chronologically (logical_ts ascending).
6. Verify no event appears out of order or is duplicated.
7. Verify evidence strings are present-tense, descriptive, thesis-attributed (e.g., "buyers took control…").

**Expected outcome:** Timeline returns verbatim persisted rows in append order. No recomputation, no stale copy, no fabricated events.
**Pass criteria:** Response contains `verdict_events` array with ≥1 event; events ordered by logical_ts; each event has all required fields; evidence strings are descriptive, not predictive; no duplicate timestamps.

---

### TC-14 — Journal endpoint 404 on unknown thesis id

**Type:** api
**Preconditions:** Backend running.

**Steps:**
1. Call `GET /research/journal/nonexistent-thesis-id`.
2. Verify response status code is 404.
3. Verify error message indicates thesis not found.

**Expected outcome:** Unknown thesis id returns 404 Not Found.
**Pass criteria:** HTTP status code 404; error body present and informative.

---

### TC-15 — Verdict dwell semantics: pre-declaration rule-hold does not confirm

**Type:** api
**Preconditions:** Backend running; deterministic replay available.

**Steps:**
1. Start a deterministic engine replay (unpaced, pytest harness).
2. Inject events that establish a confirming condition (e.g., buyer control).
3. Declare a thesis AFTER the confirming condition is already established.
4. Verify verdict remains `pending` until the dwell period elapses post-declaration.
5. Verify `rule_first_true` timestamp is earlier than `published_at` timestamp.
6. Verify `published_at` is after thesis declaration + dwell.

**Expected outcome:** Dwell timer resets at thesis declaration. Pre-declaration rule-hold does not confirm. Timestamps prove the delay.
**Pass criteria:** Verdict does not transition to confirming until post-dwell; `rule_first_true` < `published_at`; timeline entry shows both timestamps.

---

### TC-16 — Observer equivalence: engine outputs byte-identical with/without verdict evaluation

**Type:** api
**Preconditions:** Backend running; test harness with observer isolation.

**Steps:**
1. Run a deterministic engine replay WITHOUT any thesis or verdict evaluation active.
2. Capture engine snapshot output at each tick (tape state, features, confidence).
3. Run the SAME event stream WITH an active thesis and verdict evaluation.
4. Capture engine snapshot at each tick.
5. Compare outputs tick-by-tick (byte-for-byte on snapshot fields).
6. Verify no divergence in tape state, features, confidence, or last price.

**Expected outcome:** Engine behavior unchanged by verdict evaluation. Verdict layer reads frozen snapshots only.
**Pass criteria:** Both runs produce identical snapshots; no feature recomputation; no state divergence attributable to verdict evaluation.

---

### TC-17 — Config: verdict dwell, invalidation ε, k-consecutive, timeline cap all present in app/config.py

**Type:** artifact
**Preconditions:** Codebase ready.

**Steps:**
1. Read `apps/backend/app/config.py`.
2. Verify presence of config keys (or class attributes) for:
   - Verdict dwell (per setup type): `VERDICT_DWELL_*` or equivalent
   - Invalidation spread-multiple (ε): `VERDICT_INVALIDATION_EPSILON` or equivalent
   - K-consecutive threshold: `VERDICT_INVALIDATION_K_CONSECUTIVE` or equivalent
   - Timeline cap: `VERDICT_TIMELINE_CAP` or equivalent
3. Verify all are documented (inline comment or docstring).
4. Verify they are included in `config_fingerprint` hash.

**Expected outcome:** All config parameters present, documented, and included in fingerprint.
**Pass criteria:** File contains all four config keys; each has a documented default value; config_fingerprint computation includes them.

---

### TC-18 — Unit tests: verdict sequences per setup type (absorption_reversal, trend_continuation, level_break, failed_move_fade)

**Type:** api
**Preconditions:** Backend tests running; pytest available.

**Steps:**
1. Run `cd apps/backend && .venv/bin/python -m pytest tests/test_verdict_engine.py -v`.
2. Verify test class/function exists for each setup type.
3. Verify each test injects deterministic seeded events and asserts the expected verdict transitions.
4. Verify J-40 trap test: sustained absorption alone never confirms `absorption_reversal` (requires flip).
5. Verify J-45 latch test: no confirm pre-cross despite control for `level_break`.
6. Verify all tests pass with no errors or failures.

**Expected outcome:** Unit test suite covers all four setup types with correct verdict sequences. J-40 trap and J-45 latch asserted.
**Pass criteria:** Test file exists; all setup type tests pass; trap/latch tests explicitly present and passing; pytest output shows zero failures.

---

### TC-19 — Required journeys J-01–J-09, J-17, J-19, J-21, J-24 remain passing

**Type:** api
**Preconditions:** Backend tests running; test suite includes prior journey tests.

**Steps:**
1. Run `cd apps/backend && .venv/bin/python -m pytest tests/ -v -k "J_01 or J_02 or ... or J_24"`.
2. Verify all required journey tests pass.
3. Record exact test counts: passing, failing, skipped.

**Expected outcome:** All required journeys green; no regressions.
**Pass criteria:** Test output shows 0 failures for listed journey tests; backend suite maintains ≥332 passed / 1 skipped.

---

## Summary

**Total test cases: 19**
- **Browser tests: 7** (TC-01, TC-02, TC-03, TC-04, TC-05, TC-07, TC-08, TC-09, TC-10, TC-11)
- **API tests: 9** (TC-06, TC-12, TC-13, TC-14, TC-15, TC-16, TC-18, TC-19)
- **Artifact checks: 1** (TC-17)

**Key binding constraints (from phase spec):**
- Every thesis-strip assertion backed by a screenshot with strip visibly in frame (no below-fold captures).
- Verdict dwell restarts at thesis declaration; pre-declaration rule-hold never confirms.
- Invalidation: lone interior print does not trigger; only ≥ε or k-consecutive prints trigger (robust).
- Observer equivalence maintained: engine outputs byte-identical with/without verdict evaluation.
- No magic numbers: all thresholds in `app/config.py`, included in `config_fingerprint`.
- Evidence strings: present-tense, descriptive, thesis-attributed; no prediction/imperative language.
