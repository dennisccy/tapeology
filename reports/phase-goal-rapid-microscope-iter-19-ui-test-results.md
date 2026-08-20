# UI Test Results (merged)

**Date:** 2026-08-20
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 13/13 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-19-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-19-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-19-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-19-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-19-evidence/J-05-verify.png |
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-19-evidence/J-06-verify.png |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-19-evidence/J-08-verify.png |
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders, "Playbook Signals" heading visible, no console errors | Navigated to `/desk`; page rendered fully (Desk heading, Screen/Backfill/Playbook Signals sections all present); "Playbook Signals" heading visible; console showed only the standard React DevTools info line, no errors | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-01-result.png` |
| UT-06 | J-10 kept-product sentinel, end to end | regression | P1 | Every confirm step (Cockpit → Structure → Desk) passes in order, no navigation error/blank page/console error | Full 11-confirm flow executed live: `/` showed "No ticker watched" → typed SIM-BUYER → clicked Watch → "Buyer Control" appeared (via await, tape state moved off "Warming up") → `/structure` showed "Tradable Map" → typed AAPL + as-of "2026-06-22 16:00:00" → clicked Load → "300.11–302.2" resistance band appeared → `/desk` showed "Playbook Signals" → Microscope Readiness expand showed "Distinct symbol-days" (=2) → Scout Ledger expand showed "No candidates ledgered." → Walk-Forward expand showed "No fold specs registered." No console errors at any step | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-06-result.png` |
| UT-07 | Validation Vault + Referee sections still render correctly | regression | P1 | All four confirm steps pass, text unchanged from prior iterations | In the same `/desk` session as UT-06: Validation Vault expand showed "iter18-qa-universe"; Referee Registry expand showed "config fingerprint 08e471b10130e1e2"; Referee Adjudications expand showed "No hypotheses registered."; Referee Runs expand showed "No evaluation runs recorded yet." | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-07-result.png` |
| UT-08 | Section headings stay visible while collapsed | ux | P2 | All 7 named headings visible with "▸" markers, none missing/blank | Fresh `/desk` load, no clicks: extracted page text showed all of Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault each preceded by a "▸" marker | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-08-result.png` |
| UT-09 | Expand/collapse mounts and unmounts section body | ux | P2 | Heading stays visible through both clicks; body mounts on expand, unmounts on collapse | Clicked Microscope Readiness expand: marker flipped to "▾", body appeared (Corpus Totals, Joinable Corpus table with "Joinable corpus — withheld (excluded)" = 0, Legacy Tick Shards table with "Fallback frac" column showing 0.77/0.75/0.00, "No integrity errors."). Clicked again: marker returned to "▸" and the entire body (all of the above) was absent from the extracted page text — heading remained visible throughout | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-09-result.png` |
| UT-10 | Backend-unavailable shows the real error panel, not fabricated ledger text | error | P2 | `data-testid="scout-ledger-unavailable"` panel with an error message appears; "Ledger chain verification:" text does NOT appear | Installed a `window.fetch` override via `eval` (browser-side; the real backend process was never stopped) that rejects only requests to `/research/desk/micro/scout`, then clicked the Scout Ledger section header. Rendered panel text: "Backend unreachable — is the API running?" / "Nothing cached and nothing fabricated is shown in its place." (both the section body and its Run History sub-panel). `data-testid="scout-ledger-unavailable"` confirmed present in the captured HTML. Grep of the captured page text for "Ledger chain verification" returned 0 matches | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-10-result.png` |

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
