# UI Test Results (merged)

**Date:** 2026-08-10
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-10 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-playbook-iter-3-evidence/J-10-verify.png |
| UT-J-03 | The Playbook lands on `/desk` | happy-path | P1 | Empty state + enabled Run Playbook; a fixture-scoped run renders the populated signals table with chips/disclosures/forward cells/provenance; an in-flight second trigger is refused (single-flight); a non-session date shows the refusal copy verbatim; a legacy (payload_version 1) record shows the literal absence string; every shipped `/desk` section renders exactly as shipped in the same pass | All six sub-states verified live against the real backend (fixture-scoped session dates within its recorded range): TC-1 empty state, TC-2 populated table (TXN open_low_break signal, full forward/invalidation/baseline detail, provenance line), TC-3 single-flight refusal surfaced ("Refused — a playbook compute is already running..."), TC-4 non-session refusal copy verbatim (`2024-01-06 is not a recorded trading session -- ...`), TC-5 legacy record shows `"measurement not recorded in this record"` in all three cells (forward/invalidation/baseline), TC-6 all 10 shipped `/desk` section headings present and rendering unchanged alongside the new Playbook Signals section | PASS | `reports/qa/goal-playbook-iter-3-evidence/J-03-TC1-empty-state.png`, `J-03-TC2-populated-table.png`, `J-03-TC3-single-flight-refusal.png`, `J-03-TC4-non-session-refusal.png`, `J-03-TC5-legacy-record-absence.png`, `J-03-TC6-shipped-sections-intact.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-10


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | J-01 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-02 | J-02 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
