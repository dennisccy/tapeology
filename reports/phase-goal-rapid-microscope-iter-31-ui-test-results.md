# UI Test Results (merged)

**Date:** 2026-08-24
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 9/9 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-31-evidence/J-01-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-31-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-31-evidence/J-05-verify.png |
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-31-evidence/J-06-verify.png |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-31-evidence/J-08-verify.png |
| UT-J-09 | The pilot studies — three predeclared questions, honest answers | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-31-evidence/J-09-verify.png |
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-31-evidence/J-10-verify.png |
| UT-J-11 | Graduation gets a surface — the funnel's last state stops being invisible | happy-path | P1 | A read-only Graduation section renders directly below Validation Vault on `/desk`, fetched from `GET /research/desk/micro/graduation` on expand, rendering the served payload verbatim (family_root_id, stage token, transitions, sealed_evaluations, chain_verification) with no client-side aggregation, and no compute/POST control | Section confirmed as the last `<section aria-label>` on the page, immediately after "Validation Vault" (DOM order: Walk-Forward, Validation Vault, Graduation). Expanding it fetched the endpoint and rendered the live payload byte-for-byte: family `240dd966c1aceca2 — exploratory`, "No transitions recorded.", one Sealed evaluations row (dataset `ed6f24e0adc44171bc52af0da3f0890e`, verdict `pass`, n=30, evaluated_at rendered as `2026-06-09 20:00 ET`) matching a direct `curl` of the route exactly, "Ledger chain verification: ok", and 0 `<button>` elements inside the section (read-only confirmed). See "Known Limitation" below for two sub-scenarios not independently exercised. | PASS | `reports/qa/goal-rapid-microscope-iter-31-evidence/J-11-result.png` |
| UT-J-07 | Graduation — provenance in, nothing laundered out | regression/surface | P1 | The graduation fixture-walk logic (states, class-2-only advancement, single-shot sealed transitions, export-bundle provenance) stays proven by backend fixtures (`test_micro_graduation.py`, unchanged/green); this iteration gives J-07 its first on-page surface via the new Graduation section, closing its long-standing golden-replay gap | Confirmed the same Graduation section (built this iteration for J-11) is J-07's on-page surface: its static description copy ("...graduation transitions are not a UI act...") and its rendered per-family stage/provenance data are visible after one click from `/desk`. `apps/backend/tests/test_micro_graduation.py` is untouched this iteration per the dev handoff (no graduation computation change) and was confirmed green in the full-suite run (3495 passed / 8 skipped, reviewer-verified). Wrote and verified `journey-scripts/J-07.json`; `demo_runner.py --mode verify` passed it. | PASS | `reports/qa/goal-rapid-microscope-iter-31-evidence/J-07-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-24

