# UI Test Results (merged)

**Date:** 2026-08-19
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-12-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-12-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-12-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-12-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-12-evidence/J-05-verify.png |
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth (evidence retake for prior UT-04) | regression | P1 | `/desk` loads with "Playbook Signals" visible; Microscope Readiness section expands showing Corpus Totals, Legacy Tick Shards table, Pilot-Study Floors, and "No integrity errors." — unchanged by this iteration's vault-ledger `verify_chain()` gating work (informational surface only, not newly wired to UI) | Desk loaded, section expanded on click, readiness table rendered with 1 distinct symbol-day / 2 distinct datasets / 150 referee tick-gate, 2 PG shard rows, 3 floor_unmet pilot-study rows, "No integrity errors." present — matches prior known-good content, no regression | PASS | `reports/qa/goal-rapid-microscope-iter-12-evidence/UT-J-06-result.png` |
| UT-J-07 | Graduation — provenance in, nothing laundered out (TC-15 servable-surface screenshot) | smoke | P1 | `GET /research/desk/micro/graduation`'s honest empty state renders `{"families":[],"message":"No candidates ledgered.",...}` — J-07's only browser-servable surface this iteration (no `/desk` section exists for graduation; J-08 is unbuilt) | Navigated directly to the backend route (no frontend page/proxy exists for it); response body rendered exactly `{"families":[],"message":"No candidates ledgered.","chain_verification":{"ok":true,"failed_at_row":null,"reason":null}}` | PASS | `reports/qa/goal-rapid-microscope-iter-12-evidence/UT-J-07-result.png` |
| UT-J-10 | The kept product stands — traps armed, sentinel green (whole-product safety walk, evidence retake for prior UT-09) | regression | P1 | Cockpit ticker-watch → Structure load → Desk Playbook Evidence + all three Referee sections all render as shipped, with the fingerprint reading `08e471b10130e1e2` | All 13 steps passed: Cockpit "No ticker watched" → watch SIM-BUYER → "Buyer Control"; Structure load AAPL @ 2026-06-22 17:00:00 ET → "300.11–302.2"; Desk → Playbook Evidence "Built from signature:" → date 2026-06-22 → "recorded signals, none hidden"; Referee Registry → "config fingerprint 08e471b10130e1e2"; Referee Adjudications → "No hypotheses registered"; Referee Runs → "No evaluation runs recorded yet." | PASS | `reports/qa/goal-rapid-microscope-iter-12-evidence/UT-J-10-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-19

