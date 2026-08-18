# Phase goal-rapid-microscope-iter-7 — UI Test Results

**Phase:** goal-rapid-microscope-iter-7
**Date:** 2026-08-18
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 8/8 tests passed (0 skipped)

**Scope note:** this iteration's own diff is backend/CLI-only (optional trade/quote preservation
fields on `datasets.py`'s row/manifest pipeline, plus a new `--family tick_legacy` CLI flag on
`walkforward.py`) — neither has any UI wiring, per the test plan's own "Absent Test Categories"
section, so no browser test targets them directly. All 8 UT cases below are regression checks of
pre-existing, unmodified surfaces, run for real against the store-scoped `:8301`/`:3301` rig (not
skipped): UT-01 stands in for J-02/J-03/J-04 (no dedicated UI of their own — whole-page load, no
Scout Ledger/Walk-Forward/Validation Vault section); UT-02 re-verifies J-01's Microscope Readiness
panel and is this iteration's highest-stakes check, since J-06 step 1 touches the exact
`datasets.py` serialization code this panel's data flows through; UT-03 through UT-07 collectively
re-run all 13 steps of the `journey-scripts/J-10.json` kept-product sentinel by surface; UT-08 is a
P2 UX discoverability check. UT-02's expected corpus numbers (1 symbol-day / 2 datasets / 2 shard
rows) are pinned to what this fixture-scoped rig actually seeds, per this iteration's own test plan
correction of iteration 6's spurious 12/18 assertion — not the real store's numbers.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads, all sections present, no Scout Ledger section | smoke | P1 | "Playbook Signals" heading visible; no blank/error; 8 collapsible section headers present in order (Top-up Runs, Index Reconciliation, Screen Runs, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness last); no Scout Ledger/Walk-Forward/Validation Vault section | Page loaded with all content rendered; "Playbook Signals" heading visible; the 8 non-conditional section headers appeared in exactly that order (Screen Comparison/Provenance correctly absent — no screen computed this rig); no Scout Ledger/Walk-Forward/Validation Vault text anywhere; console showed only the benign React DevTools info line, no errors | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-01-result.png` |
| UT-02 | Microscope Readiness shows fixture-rig corpus data, no new columns | regression | P1 | Corpus Totals: Distinct symbol-days=1, Distinct datasets=2 (not 12/18); Legacy Tick Shards: exactly 2 rows, both Symbol=PG, Session date=2026-06-09, Split provenance=hand_assigned, Exposure state=exploratory; shard table header has exactly 12 columns, no new column for conditions/exchange/tape/trade_id/schema_basis/quote_size_unit | `micro-readiness-totals-table` read "Distinct symbol-days 1", "Distinct datasets 2", RTH minutes covered 1.75, Session-equivalents 0.0045 (non-empty); `micro-readiness-shards-table` had exactly 2 PG/2026-06-09 rows, both hand_assigned / exploratory, all cells non-empty; header row had exactly the 12 named columns verbatim, no preservation-field column present | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-02-result.png` |
| UT-03 | Cockpit ticker watch still works | regression | P1 | "No ticker watched" before watch; after typing SIM-BUYER and clicking Watch, "Buyer Control" appears; no error toast/blank panel | "No ticker watched" visible pre-watch; typed SIM-BUYER into the Ticker field (aria-label="Ticker"), clicked Watch, "Buyer Control" appeared; no console errors, no error toast | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-03-result.png` |
| UT-04 | `/structure` Tradable Map still loads | regression | P1 | "Tradable Map" visible on load; after AAPL + `2026-06-22 17:00:00` + Load, text "300.11–302.2" appears; no error message | "TRADABLE MAP" heading visible pre-load; filled Structure symbol=AAPL, `structure-as-of-input`=`2026-06-22 17:00:00`, clicked `structure-load-button`; "300.11–302.2" appeared; no console errors | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-04-result.png` |
| UT-05 | Playbook Evidence section still renders real signals | regression | P1 | After expanding, "Built from signature:" appears; after typing `2026-06-22`, "recorded signals, none hidden" appears | Expanded `playbookEvidence`; "Built from signature:" appeared; filled `desk-playbook-date-input`=`2026-06-22`; "recorded signals, none hidden" appeared | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-05-result.png` |
| UT-06 | Referee Registry shows frozen fingerprint | regression | P1 | "config fingerprint 08e471b10130e1e2" appears | Expanded `refereeRegistry`; text "config fingerprint 08e471b10130e1e2" appeared verbatim, matching the fingerprint this iteration's backend check independently re-verifies | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-06-result.png` |
| UT-07 | Referee Adjudications/Runs honest-empty states | regression | P1 | "No hypotheses registered" and "No evaluation runs recorded yet." appear, no fabricated rows/spinners/errors | Expanded `refereeAdjudications` → "No hypotheses registered" appeared; expanded `refereeRuns` → "No evaluation runs recorded yet." appeared; no console errors | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-07-result.png` |
| UT-08 | Microscope Readiness discoverable | ux | P2 | "Microscope Readiness" section visible as last section, directly below Referee Runs, reachable by scrolling alone, human-readable label | Scrolled down (no Ctrl+F); confirmed page-bottom (`atBottom: true`); last four section headers in DOM order were Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness — Microscope Readiness last, plain-English label | PASS | `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-08-result.png` |

---

## Passed Tests

### UT-01 — `/desk` loads, all sections present, no Scout Ledger section
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-01-result.png`
- Navigated to `/desk`; page markdown extraction confirmed "Playbook Signals" heading and, top to
  bottom, the section headers Top-up Runs → Index Reconciliation → Screen Runs → Playbook Evidence →
  Referee Registry → Referee Adjudications → Referee Runs → Microscope Readiness (8 of the 10
  possible collapsible sections; Screen Comparison/Provenance correctly absent since "Desk screen
  not computed yet" for this rig). No "Scout Ledger", "Walk-Forward", or "Validation Vault" text
  anywhere on the page. Console log showed only the benign React DevTools info line.

### UT-02 — Microscope Readiness shows fixture-rig corpus data, no new columns
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-02-result.png`
- Expanded `data-testid="desk-section-expand-microReadiness"`. `micro-readiness-totals-table` text
  extraction: "Distinct symbol-days 1", "Distinct datasets 2", "RTH minutes covered 1.75",
  "Session-equivalents 0.0045", "Referee tick-gate (symbol-days) 150" — matching the fixture rig's
  known 1/2 corpus, not the real store's 12/18 (per this iteration's plan correction of iteration
  6's spurious assertion). `micro-readiness-shards-table` extraction showed exactly 2 data rows,
  both Symbol=PG, Session date=2026-06-09, feed=sip, non-empty Window/Trades/Quotes/Bytes/Coverage
  gaps/Fallback frac/Checksum, both Split provenance=`hand_assigned`, both Exposure
  state=`exploratory`. Header row text confirmed exactly 12 columns in the named order — no
  `conditions`/`exchange`/`tape`/`trade_id`/`schema_basis`/`quote_size_unit` column — proving J-06
  step 1's new optional preservation fields are not surfaced in the UI, as scoped.
- Golden replay script written/confirmed: `runs/goal-session-rapid-microscope/journey-scripts/J-01.json`.

### UT-03 — Cockpit ticker watch still works
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-03-result.png`
- Navigated to `/`; markdown extraction confirmed "No ticker watched" pre-watch. Typed `SIM-BUYER`
  into `input[aria-label="Ticker"]`, clicked the "Watch" button, then `await_text` confirmed "Buyer
  Control" rendered within 10s. No console errors, no error toast.

### UT-04 — `/structure` Tradable Map still loads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-04-result.png`
- Navigated to `/structure`; page text confirmed "TRADABLE MAP" heading pre-load. Filled Structure
  symbol=`AAPL` (`input[aria-label="Structure symbol"]`),
  `data-testid="structure-as-of-input"`=`2026-06-22 17:00:00`, clicked
  `data-testid="structure-load-button"`; `await_text` confirmed "300.11–302.2" rendered within 15s —
  the pinned real S/R band for AAPL as-of that timestamp, proving the structure engine (Yahoo/
  BarStore pipeline, unrelated to this iteration's Alpaca trade/quote diff) still serves
  byte-identical output. No console errors.

### UT-05 — Playbook Evidence section still renders real signals
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-05-result.png`
- On `/desk`, expanded `data-testid="desk-section-expand-playbookEvidence"`; `await_text` confirmed
  "Built from signature:" rendered. Filled `data-testid="desk-playbook-date-input"`=`2026-06-22`;
  `await_text` confirmed "recorded signals, none hidden" rendered, confirming the date-filtered view
  still serves the full, unfiltered signal set.

### UT-06 — Referee Registry shows frozen fingerprint
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-06-result.png`
- Expanded `data-testid="desk-section-expand-refereeRegistry"`; `await_text` confirmed "config
  fingerprint 08e471b10130e1e2" rendered verbatim — the exact fingerprint this iteration's own
  backend check (TC-4/TC-10, `Config().config_fingerprint()`) independently re-verifies, confirming
  the frozen foundation did not move.

### UT-07 — Referee Adjudications/Runs honest-empty states
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-07-result.png`
- Expanded `data-testid="desk-section-expand-refereeAdjudications"`; `await_text` confirmed "No
  hypotheses registered". Expanded `data-testid="desk-section-expand-refereeRuns"`; `await_text`
  confirmed "No evaluation runs recorded yet." Neither section showed a fabricated row, stuck
  spinner, or error message. No console errors.
- Golden replay script written/confirmed for the full J-10 sentinel (UT-03 through UT-07 together
  re-ran all 13 of its steps, all passing):
  `runs/goal-session-rapid-microscope/journey-scripts/J-10.json`.

### UT-08 — Microscope Readiness discoverable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-7-evidence/UT-08-result.png`
- On `/desk`, scrolled down (mouse-wheel scroll actions only, no Ctrl+F search) to the bottom of the
  page (`window.scrollY` + `innerHeight` >= `document.body.scrollHeight`, confirmed via eval). The
  last four section headers in DOM order were "▸Referee Registry", "▸Referee Adjudications",
  "▸Referee Runs", "▸Microscope Readiness" — Microscope Readiness is the last section, directly
  below Referee Runs, reachable by scrolling alone, with a plain human-readable label (not an
  internal code name).

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3301 (store-scoped QA rig; backend http://localhost:8301)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned
  profile/CDP port, headless
- **Test Date:** 2026-08-18
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-7-evidence/`
