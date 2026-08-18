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
| UT-J-10 | The kept product stands — traps armed, sentinel green | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-7-evidence/J-10-verify.png |
| UT-01 | `/desk` loads, all sections present, no Scout Ledger section | smoke | P1 | "Playbook Signals" heading visible; no blank/error; 8 collapsible section headers present in order (Top-up Runs, Index Reconciliation, Screen Runs, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness last); no Scout Ledger/Walk-Forward/Validation Vault section | Page loaded with all content rendered; "Playbook Signals" heading visible; the 8 non-conditional section headers appeared in exactly that order (Screen Comparison/Provenance correctly absent — no screen computed this rig); no Scout Ledger/Walk-Forward/Validation Vault text anywhere; console showed only the benign React DevTools info line, no errors | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-01-result.png` |
| UT-02 | Microscope Readiness shows fixture-rig corpus data, no new columns | regression | P1 | Corpus Totals: Distinct symbol-days=1, Distinct datasets=2 (not 12/18); Legacy Tick Shards: exactly 2 rows, both Symbol=PG, Session date=2026-06-09, Split provenance=hand_assigned, Exposure state=exploratory; shard table header has exactly 12 columns, no new column for conditions/exchange/tape/trade_id/schema_basis/quote_size_unit | `micro-readiness-totals-table` read "Distinct symbol-days 1", "Distinct datasets 2", RTH minutes covered 1.75, Session-equivalents 0.0045 (non-empty); `micro-readiness-shards-table` had exactly 2 PG/2026-06-09 rows, both hand_assigned / exploratory, all cells non-empty; header row had exactly the 12 named columns verbatim, no preservation-field column present | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-02-result.png` |
| UT-03 | Cockpit ticker watch still works | regression | P1 | "No ticker watched" before watch; after typing SIM-BUYER and clicking Watch, "Buyer Control" appears; no error toast/blank panel | "No ticker watched" visible pre-watch; typed SIM-BUYER into the Ticker field (aria-label="Ticker"), clicked Watch, "Buyer Control" appeared; no console errors, no error toast | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-03-result.png` |
| UT-04 | `/structure` Tradable Map still loads | regression | P1 | "Tradable Map" visible on load; after AAPL + `2026-06-22 17:00:00` + Load, text "300.11–302.2" appears; no error message | "TRADABLE MAP" heading visible pre-load; filled Structure symbol=AAPL, `structure-as-of-input`=`2026-06-22 17:00:00`, clicked `structure-load-button`; "300.11–302.2" appeared; no console errors | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-04-result.png` |
| UT-05 | Playbook Evidence section still renders real signals | regression | P1 | After expanding, "Built from signature:" appears; after typing `2026-06-22`, "recorded signals, none hidden" appears | Expanded `playbookEvidence`; "Built from signature:" appeared; filled `desk-playbook-date-input`=`2026-06-22`; "recorded signals, none hidden" appeared | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-05-result.png` |
| UT-06 | Referee Registry shows frozen fingerprint | regression | P1 | "config fingerprint 08e471b10130e1e2" appears | Expanded `refereeRegistry`; text "config fingerprint 08e471b10130e1e2" appeared verbatim, matching the fingerprint this iteration's backend check independently re-verifies | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-06-result.png` |
| UT-07 | Referee Adjudications/Runs honest-empty states | regression | P1 | "No hypotheses registered" and "No evaluation runs recorded yet." appear, no fabricated rows/spinners/errors | Expanded `refereeAdjudications` → "No hypotheses registered" appeared; expanded `refereeRuns` → "No evaluation runs recorded yet." appeared; no console errors | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-07-result.png` |
| UT-08 | Microscope Readiness discoverable | ux | P2 | "Microscope Readiness" section visible as last section, directly below Referee Runs, reachable by scrolling alone, human-readable label | Scrolled down (no Ctrl+F); confirmed page-bottom (`atBottom: true`); last four section headers in DOM order were Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness — Microscope Readiness last, plain-English label | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-08-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-18

