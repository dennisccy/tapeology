# UI Test Results (merged)

**Date:** 2026-08-18
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 9/9 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-9-evidence/J-01-verify.png |
| UT-01 | Validation Vault section genuinely absent from `/desk` | smoke | P1 | No "Validation Vault" text, no `desk-section-expand-vault` element, "Microscope Readiness" is the last section, no console error | `/desk` loaded ("Playbook Signals" heading present); `document.querySelector('[data-testid="desk-section-expand-vault"]')` = null; `document.body.innerText.includes('Validation Vault')` = false; last `h2/h3` on page = "MICROSCOPE READINESS"; console clean (only benign React DevTools info line) | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-01-result.png` |
| UT-02 | No "Scout Ledger"/"Walk-Forward" section on `/desk` | regression | P1 | All 8 always-rendered section headers present; no "Scout Ledger"/"Walk-Forward" section | `document.querySelectorAll('[data-testid^="desk-section-expand-"]')` returned exactly `["desk-section-expand-topupRuns","desk-section-expand-indexReconciliation","desk-section-expand-screenRuns","desk-section-expand-playbookEvidence","desk-section-expand-refereeRegistry","desk-section-expand-refereeAdjudications","desk-section-expand-refereeRuns","desk-section-expand-microReadiness"]` — all 8 required headers present, no scoutLedger/walkforward/vault; full-page markdown extract confirms "Screen Comparison"/"Provenance" correctly absent (no screen computed this rig session) | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-02-result.png` |
| UT-03 | Microscope Readiness shows fixture-rig corpus data, no new columns | regression | P1 | Distinct symbol-days=1, Distinct datasets=2; 2 shard rows PG/2026-06-09, `hand_assigned`/`exploratory`; exactly 12 columns, no new column for the two new §2.6 fields | Corpus Totals: "Distinct symbol-days"=1, "Distinct datasets"=2, RTH minutes covered=1.75, Session-equivalents=0.0045 (both non-empty numeric); Legacy Tick Shards `tbody` (`data-testid="micro-readiness-shard-rows"`) contains exactly 2 `<tr>`, both Symbol=PG, Session date=2026-06-09, non-empty Feed/Window/Trades/Quotes/Bytes/Coverage gaps/Fallback frac/Checksum, Split provenance=`hand_assigned`, Exposure state=`exploratory` on both; header row = exactly `["Symbol","Session date","Feed","Window (ET)","Trades","Quotes","Bytes","Coverage gaps","Fallback frac","Checksum","Split provenance","Exposure state"]` (12 columns, exact order, no `quote_size_unit_rule_text`/`quote_size_unit_verification_note` column) | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-03-result.png` |
| UT-04 | Cockpit ticker watch still works | regression | P1 | "No ticker watched" before watch; "Buyer Control" after Watch click; no error toast/blank panel | Navigated to `/`, "No ticker watched" visible pre-watch; typed `SIM-BUYER` into `input[aria-label="Ticker"]`, clicked "Watch" button; `await_text` found "Buyer Control" (Tape State panel shows "Buyer Control", confidence 0.924); live tape, quote, features, recent trades, observations, and event log all rendering; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-04-result.png` |
| UT-05 | `/structure` Tradable Map still loads | regression | P1 | "Tradable Map" on load; after Load click, exact band text "300.11–302.2" appears; no error | Navigated to `/structure`, "Tradable Map" visible; filled Structure symbol=AAPL, as-of=`2026-06-22 17:00:00`, clicked Load; `await_text` found "300.11" and `document.body.innerText.includes('300.11–302.2')` = true; Tradable Map table's first resistance row reads exactly `300.11-302.2 · Class A · score 171 · round number`; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-05-result.png` |
| UT-06 | Playbook Evidence section still renders real signals | regression | P1 | "Built from signature:" after expand; "recorded signals, none hidden" after date filter | Navigated to `/desk`, "Playbook Signals" heading present; clicked `desk-section-expand-playbookEvidence`, `await_text` found "Built from signature:"; typed `2026-06-22` into `desk-playbook-date-input`, `await_text` found "recorded signals, none hidden"; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-06-result.png` |
| UT-07 | Referee Registry section still shows the frozen fingerprint | regression | P1 | "config fingerprint 08e471b10130e1e2" appears | Clicked `desk-section-expand-refereeRegistry`; `await_text` found exact string "config fingerprint 08e471b10130e1e2" — matches the dev handoff's independently re-verified `Config().config_fingerprint()` value | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-07-result.png` |
| UT-08 | Referee Adjudications and Runs sections still render honest-empty states | regression | P1 | "No hypotheses registered"; "No evaluation runs recorded yet." | Clicked `desk-section-expand-refereeAdjudications`, `await_text` found "No hypotheses registered"; clicked `desk-section-expand-refereeRuns`, `await_text` found "No evaluation runs recorded yet."; neither section showed a fabricated row or stuck spinner | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-08-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-18


## Deferred (iteration budget)

_The wall-clock iteration budget was exceeded (SPEED-15 trim rung 2): the
no-golden regression journeys below were NOT re-verified this iteration and
keep their prior recorded status. They are re-queued for a later iteration_

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | J-02 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-03 | J-03 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-04 | J-04 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
| UT-J-05 | J-05 regression re-check | regression | P2 | re-verify per goal.md | not run this iteration | DEFERRED-BUDGET | deferred: over iteration wall-clock budget |
