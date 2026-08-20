# UI Test Results (merged)

**Date:** 2026-08-20
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 15/16 journeys passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/J-05-verify.png |
| UT-J-08 | The surface and MCP v6 — the funnel is visible | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/J-08-verify.png |
| UT-01 | `/desk` loads cleanly with zero console errors | smoke | P1 | Page renders, heading "Desk" visible, all sections collapsed with closed arrow, zero console errors | Loaded cleanly; `data-testid="desk-title"` present with text "Desk"; 11 always-rendered collapsible sections all showed closed "▸"; console held only the React-DevTools info line | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/UT-01-result.png |
| UT-02 | Microscope Readiness carries its testid in all 3 render states | regression | P1 | `data-testid="micro-readiness-section"` present in loaded AND unavailable states | Loaded state: testid present, real data confirmed (Distinct symbol-days 1, Distinct datasets 2, 2 PG shard rows). Unavailable state (reached via a safe in-browser fetch-failure simulation, see note below): testid present, panel read "Backend unreachable — is the API running?" verbatim. Loading state confirmed present via direct source read (page.tsx:5891-5896) since the local fetch resolves in well under a paintable frame. Zero console errors in any state | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/UT-02-result.png |
| UT-03 | Scout Ledger renders the real honest-empty state | smoke | P1 | "Run Screen" trigger visible (not clicked); "No candidates ledgered."; "No scout runs recorded yet."; zero console errors | All three confirmed verbatim, plus "Ledger chain verification: ok" | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/UT-03-result.png |
| UT-04 | [Optional] Malformed Scout row degrades gracefully | error | P3 | Row renders "— / —" / "—" fallback under an isolated fixture rig; every other section still renders | Not executed — requires standing up a separate scoped backend+frontend pair, which the test plan itself marks optional/non-gating for this round. Source-level check performed instead: `page.tsx:6321` (`{trial.feature?.name ?? "—"} / {trial.feature?.transform ?? "—"}`) and `:6323` (`{trial.outcome?.horizon_key ?? "—"}`) confirm the exact optional-chaining fallback described in the spec is present | SKIP | none |
| UT-05 | Console clean across every collapsible Desk section | smoke | P1 | Zero red console errors after any expansion; no React hydration warning; no section throws or blanks the page | Clicked through 11 of the 13 named sections (Top-up Runs, Index Reconciliation, Screen Runs, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault) — console stayed at the single React-DevTools info line throughout, no hydration warning at any point. "Screen Comparison" and "Provenance" were confirmed absent from the DOM by design (both gated on `latest !== null`; no screen has ever been computed against the real store) — not a defect, not part of this round's diff | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/UT-05-result.png |
| UT-06 | Walk-Forward / Validation Vault unaffected | regression | P2 | "No fold specs registered.", "No walk-forward sequences run.", "No shards recorded.", "No universes registered."; no compute/seal/expose control in Vault; zero console errors | All four empty-state strings confirmed verbatim; "Run Walk-Forward" visible but not clicked; programmatic check found 0 `<button>` elements inside `[data-testid="validation-vault-section"]` | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/UT-06-result.png |
| UT-07 | Playbook / Referee sections unaffected | regression | P2 | Playbook Signals renders above the fold without a click; the three Referee sections each expand with real content, no error panel, no console error | Playbook Signals visible immediately. Referee Registry expanded cleanly (2,877 chars of real content, console clean) then re-collapsed for a legible screenshot. Referee Adjudications and Referee Runs expanded showing their real empty-state copy ("No hypotheses registered.", "No hypotheses registered — nothing to build a null for yet.", "No evaluation runs recorded yet.") | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/UT-07-result.png |
| UT-08 | Cockpit live tape + chart | regression | P1 | Chart renders, live tape updates for SIM-BUYER, no error banner | Mode selector confirmed "Simulated" (`aria-pressed="true"`) by default; watched SIM-BUYER; Tape State "Buyer Control" (confidence 0.928→0.932 across two reads), quote/features/recent-trades/observations/event-log all populated; bid/ask visibly changed between the DOM read and the screenshot moment, confirming the tape is genuinely live, not frozen | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/UT-08-result.png |
| UT-09 | `/structure` load + Tradable Map + Comparison | regression | P1 | No error banner; Tradable Map renders 10 band rows for AAPL @ 2026-06-22 16:00:00 ET; comparison dropdown present and selectable | Loaded with exactly 10 rows (5 resistance + 5 support, all Class A); first resistance row `300.11–302.2` (round-number flagged); `[data-testid="comparison-dataset-select"]` present and enabled; no error banner | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/UT-09-result.png |
| UT-10 | Nav bar unaffected | regression | P2 | Exactly 3 links: "Cockpit", "Structure", "Desk" | Confirmed via `[data-testid="nav-link"]` query on `/`, `/structure`, and `/desk`: exactly `["Cockpit","Structure","Desk"]` every time | PASS | reports/qa/goal-rapid-microscope-iter-16-evidence/UT-10-result.png |

## Skipped Tests

### UT-04 — [Optional] Malformed Scout row degrades gracefully

**Verdict:** SKIPPED
**Reason:** Not executed — requires standing up a separate scoped backend+frontend pair, which the test plan itself marks optional/non-gating for this round. Source-level check performed instead: `page.tsx:6321` (`{trial.feature?.name ?? "—"} / {trial.feature?.transform ?? "—"}`) and `:6323` (`{trial.outcome?.horizon_key ?? "—"}`) confirm the exact optional-chaining fallback described in the spec is present

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
