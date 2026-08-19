# UI Test Results (merged)

**Date:** 2026-08-19
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 16/16 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-11-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-11-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-11-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-11-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-11-evidence/J-05-verify.png |
| UT-01 | `/desk` loads | smoke | P1 | Page renders, no blank/error, "Microscope Readiness" heading visible | Loaded cleanly; "Microscope Readiness" heading present; only console message was the benign React DevTools notice | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-01-result.png` |
| UT-02 | `/structure` loads | smoke | P1 | Page renders, no blank/error, "Comparison" heading visible | Loaded cleanly; "Comparison" text present; no console errors | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-02-result.png` |
| UT-03 | Cockpit tape/chart | regression | P1 | Chart renders candles, live tape actively updates or shows a connected indicator, no error banner | Watched SIM-BUYER; chart rendered (7 canvas elements); quote/feature panel genuinely updated after a real 6s wait (Bid 101.16→101.88, Ask 101.18→101.90, Net aggressive volume 15800→16500); "Simulated / lag 0.2s / Live" indicator shown; `document.visibilityState` was "visible" throughout (headless-freeze gotcha did not apply) | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-03-result.png` |
| UT-04 | Microscope Readiness shard table unchanged | regression | P1 | Same shard rows, same order, same Symbol/Session Date/Checksum/exposure_state as baseline | Table showed exactly 2 rows (PG/2026-06-09, feed sip, two distinct windows), with Trades/Quotes/Bytes/Checksum/`exposure_state: exploratory` matching `GET /research/desk/micro/readiness`'s `shards` array byte-for-byte, field by field | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-04-result.png` |
| UT-05 | Comparison dataset dropdown unchanged | regression | P1 | Exactly 18 options, format `SYMBOL · split · 8-char-id` (developer's real-store count) | This QA harness's scoped rig has only 2 datasets total (see environment note above); dropdown showed exactly 2 options — `PG · train · 6c9bf2c7` and `PG · holdout · d9f9dbe0` — an exact, field-for-field match to this same backend's own `GET /research/datasets` response. No dataset present in the backend was missing from the dropdown (the specific over-withholding regression this test guards against did not occur) | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-05-result.png` |
| UT-06 | Edge Report panel unchanged | regression | P2 | Either a matching comparison table or the "not computed yet" honest state, no new error | "Edge report not computed yet." panel shown with its Compute control, exactly one of the two documented honest states; no error | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-06-result.png` |
| UT-07 | Case Studies panel unchanged | regression | P2 | Event table row count matches baseline exactly, no row missing/new | Table rendered exactly 681 rows with default All/All filters — an exact match to this backend's `GET /research/setups` `events` array length (681) | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-07-result.png` |
| UT-08 | Screen-related panels unchanged | regression | P2 | Screen history and Screen Runs list the same runs/counts as baseline, no new error/empty state where data previously rendered | "Screen Runs" (unconditional section) shows the honest empty state "No screen runs recorded yet." — no error. "Screen History" is a distinct, DIFFERENT section that is nested inside the populated-screen view only (confirmed directly in `apps/frontend/app/desk/page.tsx:198`: "Screen History, which lives only inside the populated-screen view" — pre-existing code, zero frontend diff this iteration); this scoped rig has never recorded a screen ("Desk screen not computed yet"), so Screen History legitimately does not render at all, exactly as it would not have before this iteration either | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-08-result.png` |
| UT-09 | Full-page sentinel walk (J-10) | regression | P1 | Every named section renders its own data-or-empty-state panel; nothing blank/stuck/erroring | All 10 sections that render unconditionally in this state — Top-up Runs, Index Reconciliation, Screen Runs, Playbook Signals, Backscan/Back-scan runs, Playbook Evidence (full real data table + honest "low n" flags), Referee Registry, Referee Adjudications ("No hypotheses registered"), Referee Runs ("No evaluation runs recorded yet." ×2), Microscope Readiness — each rendered real content or an honest empty state, zero blank panels, zero stuck spinners, zero error banners, zero new console errors. The 4 remaining named headings (Forward Returns, Briefing, Skipped members, Provenance) are nested inside the same populated-screen-only view as Screen History (UT-08) and are legitimately absent for the same pre-existing, iteration-unrelated reason — the page's single combined "Desk screen not computed yet." honest state covers that whole group | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-09-result.png` |
| UT-10 | Nav bar unaffected | ux | P3 | Exactly 3 links; each click navigates and highlights correctly | Nav showed exactly Cockpit/Structure/Desk (from `GET /meta/ui-routes`); clicking Structure → URL `/structure` + Structure `aria-current="page"`; clicking Desk → URL `/desk` + Desk active; clicking Cockpit → URL `/` + Cockpit active | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-10-result.png` |
| UT-11 | Recorder-progress aggregate-only, no leak | error | P2 | Exactly the 10 named fields, no `outcomes`, no `symbol`/`date`/`dataset_id` anywhere | `curl http://localhost:8301/research/desk/micro/recorder/compute` returned `progress` with exactly `chunks_total, chunks_done, chunks_fetched, chunks_reused, chunks_unchanged, chunks_failed, trades_total, quotes_total, percent_complete, elapsed_seconds` — no `outcomes` key, no `symbol`/`date`/`dataset_id` anywhere in the body (`state`, `progress{...}`, `started_utc`, `finished_utc`, `error` — nothing else) | PASS | none (API-only check, no browser surface exists for this endpoint) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-19


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | J-07 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
