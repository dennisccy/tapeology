# Phase goal-rapid-microscope-iter-9 — UI Test Results

**Phase:** goal-rapid-microscope-iter-9
**Date:** 2026-08-18
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 8/8 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Validation Vault section genuinely absent from `/desk` | smoke | P1 | No "Validation Vault" text, no `desk-section-expand-vault` element, "Microscope Readiness" is the last section, no console error | `/desk` loaded ("Playbook Signals" heading present); `document.querySelector('[data-testid="desk-section-expand-vault"]')` = null; `document.body.innerText.includes('Validation Vault')` = false; last `h2/h3` on page = "MICROSCOPE READINESS"; console clean (only benign React DevTools info line) | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-01-result.png` |
| UT-02 | No "Scout Ledger"/"Walk-Forward" section on `/desk` | regression | P1 | All 8 always-rendered section headers present; no "Scout Ledger"/"Walk-Forward" section | `document.querySelectorAll('[data-testid^="desk-section-expand-"]')` returned exactly `["desk-section-expand-topupRuns","desk-section-expand-indexReconciliation","desk-section-expand-screenRuns","desk-section-expand-playbookEvidence","desk-section-expand-refereeRegistry","desk-section-expand-refereeAdjudications","desk-section-expand-refereeRuns","desk-section-expand-microReadiness"]` — all 8 required headers present, no scoutLedger/walkforward/vault; full-page markdown extract confirms "Screen Comparison"/"Provenance" correctly absent (no screen computed this rig session) | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-02-result.png` |
| UT-03 | Microscope Readiness shows fixture-rig corpus data, no new columns | regression | P1 | Distinct symbol-days=1, Distinct datasets=2; 2 shard rows PG/2026-06-09, `hand_assigned`/`exploratory`; exactly 12 columns, no new column for the two new §2.6 fields | Corpus Totals: "Distinct symbol-days"=1, "Distinct datasets"=2, RTH minutes covered=1.75, Session-equivalents=0.0045 (both non-empty numeric); Legacy Tick Shards `tbody` (`data-testid="micro-readiness-shard-rows"`) contains exactly 2 `<tr>`, both Symbol=PG, Session date=2026-06-09, non-empty Feed/Window/Trades/Quotes/Bytes/Coverage gaps/Fallback frac/Checksum, Split provenance=`hand_assigned`, Exposure state=`exploratory` on both; header row = exactly `["Symbol","Session date","Feed","Window (ET)","Trades","Quotes","Bytes","Coverage gaps","Fallback frac","Checksum","Split provenance","Exposure state"]` (12 columns, exact order, no `quote_size_unit_rule_text`/`quote_size_unit_verification_note` column) | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-03-result.png` |
| UT-04 | Cockpit ticker watch still works | regression | P1 | "No ticker watched" before watch; "Buyer Control" after Watch click; no error toast/blank panel | Navigated to `/`, "No ticker watched" visible pre-watch; typed `SIM-BUYER` into `input[aria-label="Ticker"]`, clicked "Watch" button; `await_text` found "Buyer Control" (Tape State panel shows "Buyer Control", confidence 0.924); live tape, quote, features, recent trades, observations, and event log all rendering; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-04-result.png` |
| UT-05 | `/structure` Tradable Map still loads | regression | P1 | "Tradable Map" on load; after Load click, exact band text "300.11–302.2" appears; no error | Navigated to `/structure`, "Tradable Map" visible; filled Structure symbol=AAPL, as-of=`2026-06-22 17:00:00`, clicked Load; `await_text` found "300.11" and `document.body.innerText.includes('300.11–302.2')` = true; Tradable Map table's first resistance row reads exactly `300.11-302.2 · Class A · score 171 · round number`; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-05-result.png` |
| UT-06 | Playbook Evidence section still renders real signals | regression | P1 | "Built from signature:" after expand; "recorded signals, none hidden" after date filter | Navigated to `/desk`, "Playbook Signals" heading present; clicked `desk-section-expand-playbookEvidence`, `await_text` found "Built from signature:"; typed `2026-06-22` into `desk-playbook-date-input`, `await_text` found "recorded signals, none hidden"; console clean | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-06-result.png` |
| UT-07 | Referee Registry section still shows the frozen fingerprint | regression | P1 | "config fingerprint 08e471b10130e1e2" appears | Clicked `desk-section-expand-refereeRegistry`; `await_text` found exact string "config fingerprint 08e471b10130e1e2" — matches the dev handoff's independently re-verified `Config().config_fingerprint()` value | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-07-result.png` |
| UT-08 | Referee Adjudications and Runs sections still render honest-empty states | regression | P1 | "No hypotheses registered"; "No evaluation runs recorded yet." | Clicked `desk-section-expand-refereeAdjudications`, `await_text` found "No hypotheses registered"; clicked `desk-section-expand-refereeRuns`, `await_text` found "No evaluation runs recorded yet."; neither section showed a fabricated row or stuck spinner | PASS | `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-08-result.png` |

---

## Passed Tests

### UT-01 — Validation Vault section genuinely absent from `/desk`
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-01-result.png`
- This is the iteration's genuinely new check and J-06's own acceptance proof: `vault.py` and `GET /research/desk/micro/vault` are fully built and tested this iteration (backend), but nothing on `/desk` renders them — confirmed absent by both a full-page text scan and a direct DOM query for `[data-testid="desk-section-expand-vault"]`.
- Confirmed via `eval`: `{"vaultTestId":false,"vaultTextAnywhere":false,"lastH2":"▸\nMICROSCOPE READINESS", ...}`.
- No blank screen, no error banner, browser console showed only the benign React DevTools info line.

### UT-02 — No "Scout Ledger"/"Walk-Forward" section on `/desk`
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-02-result.png`
- All 8 always-rendered section headers present (Top-up Runs, Index Reconciliation, Screen Runs, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness); "Screen Comparison"/"Provenance" correctly absent (no screen computed in this fresh rig session, as expected).
- No "Scout Ledger" or "Walk-Forward" section exists — satisfies J-02/J-03/J-04/J-05's "no dedicated UI element of their own" regression check per the surface map.

### UT-03 — Microscope Readiness shows fixture-rig corpus data, no new columns
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-03-result.png`
- Corpus Totals and Legacy Tick Shards values match the store-scoped rig's 2-fixture corpus exactly (1 symbol-day / 2 datasets / 2 shard rows), per context note 2 — not the real store's 12/18.
- Load-bearing assertion for this iteration confirmed: the shard table header row has exactly the pre-existing 12 columns in the pre-existing order — no new column for `quote_size_unit_rule_text` or `quote_size_unit_verification_note`, proving those two new optional manifest fields are not surfaced anywhere in the UI.

### UT-04 — Cockpit ticker watch still works
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-04-result.png`
- Full watch flow completed end to end; live tape (quote, recent trades, features, observations, event log) rendering normally, unaffected by this iteration's vault/tick-recording backend changes.

### UT-05 — `/structure` Tradable Map still loads
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-05-result.png`
- The pinned AAPL 2026-06-22 17:00:00 ET resistance band rendered byte-identically (`300.11-302.2`, Class A, score 171, round number flag), proving the Yahoo/BarStore bar pipeline is untouched by this iteration's diff.

### UT-06 — Playbook Evidence section still renders real signals
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-06-result.png`
- Section reads a real, already-computed playbook signature; date-filtered view still serves the full, unfiltered signal set for 2026-06-22.

### UT-07 — Referee Registry section still shows the frozen fingerprint
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-07-result.png`
- Fingerprint `08e471b10130e1e2` on screen matches the dev handoff's independently re-verified `Config().config_fingerprint()` — the frozen foundation did not move this iteration.

### UT-08 — Referee Adjudications and Runs sections still render honest-empty states
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-9-evidence/UT-08-result.png`
- Both empty-state messages appeared exactly as specified; no fabricated rows, no stuck spinners, no error messages.

---

## Failed Tests

None — all 8 executed tests passed.

---

## Skipped Tests

None — frontend, backend, and Chrome MCP were all available; all 8 test-plan cases executed.

---

## Golden Replay Scripts

Per the goal-mode regression-speedup convention, self-contained deterministic replay scripts were
written/overwritten at `runs/goal-session-rapid-microscope/journey-scripts/` for every journey
verified PASS this run, and lint-checked clean via `demo_runner.py --mode lint`:

- `J-06.json` (target journey — this iteration's step-3 vault build) — 2 steps: load `/desk`,
  expand Microscope Readiness, expect "No integrity errors." **Caveat:** the replay schema
  (goto/click/fill + a single positive `expect.text` per step) has no way to encode UT-01's actual
  load-bearing assertion — the ABSENCE of "Validation Vault" text/element. This script therefore
  only re-proves the page loads and Microscope Readiness still expands correctly; it does **not**
  replay the absence check itself. A future iteration relying on this golden for J-06 regression
  should be aware the absence proof still needs an LLM-lane (or explicitly negative-assertion-aware)
  pass if that specific guarantee matters again — flagging this rather than silently overstating
  the golden's coverage.
- `J-10.json` (kept-product sentinel, unmodified this iteration) — all 13 steps re-verified fresh
  end to end (cockpit watch → `/structure` load → three `/desk` sections); rewritten byte-identical
  to the pre-existing script since every step's assertion was independently reconfirmed.
- `J-01.json` (Microscope Readiness / corpus truth) — rewritten byte-identical to the pre-existing
  script; the `hand_assigned` assertion was independently reconfirmed this run via UT-03's deeper
  read of the same section (this row supersedes the iteration's earlier deterministic replay per
  the dispatch note).
- `J-02.json`, `J-03.json`, `J-04.json`, `J-05.json` (NEW — none existed before this run) — each a
  single-step `/desk` load check asserting one of the always-rendered section headers ("Top-up
  Runs", "Index Reconciliation", "Screen Runs", "Playbook Signals" respectively), matching the
  surface map's framing that none of these four journeys has a dedicated UI element of its own;
  UT-02's whole-page check is their only browser-facing regression surface.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (store-scoped QA rig — 2 committed PG fixture datasets by
  design, not the real 18-dataset/12-symbol-day corpus)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless,
  pinned profile/port per environment
- **Test Date:** 2026-08-18
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-9-evidence/`

---

## Notes

- This iteration's diff is backend-only (5 source files including new `vault.py`, 4 test files
  including new `test_vault.py`, 0 frontend files) — confirmed by the ui-surface-map. All 8 test
  cases were run for real through Chrome MCP per the dispatch's explicit instruction not to
  blanket-skip; none was skipped.
- UT-01 is an absence check by design: the "Validation Vault" section is J-08 scope, not this
  iteration's. Its PASS proves OUT OF SCOPE held, not that a new feature works.
- UT-03's expected values (1 symbol-day / 2 datasets / 2 shard rows) are the store-scoped rig's own
  fixture data, not the real store's 12/18, per context note 2 and the test plan's own correction
  carried forward from iteration 6/7's spurious failure.
- All verdict cells above are written as bare tokens (PASS/FAIL/SKIP) per instruction — no bold or
  emphasis markup.
