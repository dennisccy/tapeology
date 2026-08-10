# UI Test Results (merged)

**Date:** 2026-08-10
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 1/3 journeys passed (2 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-2-evidence/J-10-verify.png |
| UT-J-01 | The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered | regression (carried, required-still-passing) | P1 | Not applicable to browser QA — acceptance is `GET /research/desk/playbook` payload shape, fixture-rig re-run byte-identity, lookahead property test, non-session refusal, backend suite green; goal.md tags the journey `(Keyless; automated.)` | No browser-observable steps exist for this journey. `/desk` was loaded and confirmed to render the kept product (Screen History, Forward Returns, Refresh Data) with no Playbook section, matching iter-2's own "Frontend Present: no" / "None visible in the UI this iteration" scope statement. | SKIP | `reports/qa/goal-playbook-iter-2-evidence/J-01-J-02-desk-no-ui-change.png` |
| UT-J-02 | Every signal measured — the rail's own conventions, anchored at the trigger bar | smoke/regression (target journey) | P1 | Not applicable to browser QA — acceptance is the `forward`/`invalidation_breached`/`baseline_anchors`/`summary` payload extension, convention-identity test, embedded-constants counter-test, run-ledger discipline, backend suite green; goal.md tags the journey `(Keyless; automated.)` | Iter-2 spec states explicitly: "New user-facing capability: None visible in the UI this iteration (J-02 stays backend-only; Frontend Present: no)." and "UI surface changes: None." No steps in J-02's own numbered list touch the browser. `/desk` confirmed unchanged (same sections as J-01 baseline, no console errors). | SKIP | `reports/qa/goal-playbook-iter-2-evidence/J-01-J-02-desk-no-ui-change.png` |

## Skipped Tests

### UT-J-01 — The signal contract — opening-range breaks end to end, lookahead-clean and pre-registered

**Verdict:** SKIPPED
**Reason:** No browser-observable steps exist for this journey. `/desk` was loaded and confirmed to render the kept product (Screen History, Forward Returns, Refresh Data) with no Playbook section, matching iter-2's own "Frontend Present: no" / "None visible in the UI this iteration" scope statement.

### UT-J-02 — Every signal measured — the rail's own conventions, anchored at the trigger bar

**Verdict:** SKIPPED
**Reason:** Iter-2 spec states explicitly: "New user-facing capability: None visible in the UI this iteration (J-02 stays backend-only; Frontend Present: no)." and "UI surface changes: None." No steps in J-02's own numbered list touch the browser. `/desk` confirmed unchanged (same sections as J-01 baseline, no console errors).

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-10

