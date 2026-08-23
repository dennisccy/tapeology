# UI Test Results (merged)

**Date:** 2026-08-23
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 13/15 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-28-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-28-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-28-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-28-evidence/J-05-verify.png |
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-28-evidence/J-06-verify.png |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-28-evidence/J-08-verify.png |
| UT-J-09 | The pilot studies — three predeclared questions, honest answers | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-28-evidence/J-09-verify.png |
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders, `desk-title`="Desk", "Playbook Signals" visible, no console errors | Confirmed all: `desk-title` text = "Desk", "Playbook Signals" present in DOM, only a React-DevTools info console line (no errors) | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-01-result.png` |
| UT-02 | Seal-unaware caveat renders in Strategy Family block | happy-path | P1 | New `data-testid="referee-evidence-strategy-seal-unaware-caveat"` line with exact verbatim text, directly below tick-gate line and above basis-caveats list, styled as muted secondary text, no overlap | Element found; DOM child order of `referee-evidence-strategy-block` is exactly `...-tick-gate` → `...-seal-unaware-caveat` → `...-basis-caveats`; `textContent` matches the spec sentence character-for-character; computed style is `<p class="mt-2 text-[11px] text-slate-500">` (muted slate, 11px); screenshot shows clean vertical stacking, no visual overlap with the caveats list below | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-02-result.png` |
| UT-03 | Validation — N/A | n/a | n/a | No validation surface this iteration | Not applicable — no form/input changed | SKIP (N/A) | none |
| UT-04 | Error — N/A | n/a | n/a | No new error state this iteration | Not applicable — static text has no loading/error/empty state of its own | SKIP (N/A) | none |
| UT-05 | J-01 golden journey — Microscope Readiness | regression | P1 | Section expands, "hand_assigned" visible | Navigated `/desk`, clicked `desk-section-expand-microReadiness`, confirmed `document.body.innerText.includes('hand_assigned') === true` | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-05-result.png` |
| UT-06 | J-10 sentinel — all kept surfaces render | regression | P1 | All 16 steps across `/`, `/structure`, `/desk` complete with listed text visible, no console error, no section broken by new caveat markup | All 16 steps executed and verified individually (see Passed Tests below); no console errors throughout the entire session (only a React-DevTools info line) | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-06-result.png` |
| UT-07 | Caveat discoverable in 1 click | ux | P2 | "Referee Registry" header visible without excessive scrolling; 1 click reveals the caveat text | Header found at DOM position right after "Playbook Evidence" (well within the page's normal collapsed-state section list, docHeight 2498px collapsed); one click on `desk-section-expand-refereeRegistry` revealed "Legacy Referee readiness metric..." text (`await_text` matched) | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-07-result.png` |
| UT-08 | Scout Ledger "N variants tried" row (passenger, TC-11) | regression | P3 | At least one family row shows "N variants tried" pattern | Expanded Scout Ledger section; block `scout-ledger-families-block` shows "failed_aggression_score__playbook_signal__trades_20 (root e47904f2f7f4f0e1) — 1 variants tried" | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-08-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-23


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | J-07 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
