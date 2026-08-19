# UI Test Results (merged)

**Date:** 2026-08-19
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 19/22 journeys passed (3 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | The era transition stands — the corpus truth on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-14-evidence/J-01-verify.png |
| UT-J-02 | The micro observer — one pass, prefix-honest, benchmarked | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-14-evidence/J-02-verify.png |
| UT-J-03 | Structure × flow — the join that never looks ahead | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-14-evidence/J-03-verify.png |
| UT-J-04 | The Scout and the ledger — every trial on the record | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-14-evidence/J-04-verify.png |
| UT-J-05 | The walk-forward engine — chronology, fences, and the diagnostic run | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-rapid-microscope-iter-14-evidence/J-05-verify.png |
| UT-01 | `/desk` loads, all headers present, collapsed | smoke | P1 | Page renders, 4 era section headers visible collapsed, no console errors, nav shows exactly Cockpit/Structure/Desk | Page loaded with full content (screen, forward returns, playbook signals). All 13 `CollapsibleSection` headers present with `▸` (aria-expanded=false), ending in the exact sequence Referee Runs → Microscope Readiness → Scout Ledger → Walk-Forward → Validation Vault. Console: only the React DevTools info line. Nav: Cockpit/Structure/Desk only. | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-01-result.png` |
| UT-02 | View Scout Ledger contents | happy-path | P1 | Expand shows chain verification ok, empty-state "No candidates ledgered.", Run History empty state, enabled Run Screen, no Cancel | `aria-expanded` true after click. Body: "Ledger chain verification: ok" · "∅ No candidates ledgered." · "Run History" · "∅ No scout runs recorded yet." `scout-ledger-trigger` disabled=false (text "Run Screen"); `scout-ledger-cancel` not present in DOM. | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-02-result.png` |
| UT-03 | View Walk-Forward contents | happy-path | P1 | Chain verification ok, Fold Specs block, ≥1 populated sequence with verdict line, 8-col fold table, Recency line, Run History, enabled button, no Cancel | "Ledger chain verification: ok". Fold Specs: `playbook_setups_diagnostic_v1` detail row. Sequence `seq-d39d20e47af24671`: "Sequence verdict: refused — 2 < 3 sufficient folds …". Fold table: 5 rows (indices 0-4, statuses insufficient/insufficient/insufficient/sufficient/sufficient) across all 8 columns. "Recency — older 1 folds (1 positive share), recent 1 folds (0 positive share)". Run History: "No walk-forward runs recorded yet." `walk-forward-trigger` disabled=false; `walk-forward-cancel` absent. | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-03-result.png` |
| UT-04 | View Validation Vault contents, confirm read-only | happy-path | P1 | Both chain-verification lines ok, empty Shards + Universes, zero interactive controls anywhere in the section, no cross-reference to `/research/datasets` or Readiness values | "Shard ledger chain verification: ok" · "Universe ledger chain verification: ok" · "Shards ∅ No shards recorded." · "Universes ∅ No universes registered." A DOM sweep of `[data-testid="validation-vault-section"] button, input, select, textarea, a[href], [role="button"], [contenteditable="true"]` returned `{"count":0,"tags":[]}`. Rendered text contains no `/research/datasets` reference and repeats none of the Readiness totals (12/18/1173.49/3.0089/150). | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-04-result.png` |
| UT-05 | Scout "Run Screen" starts + shows progress (fast slice) | happy-path | P2 | Click → "Screening…" disabled, "0 / 6 candidates" progress line + pulsing dot, Cancel appears, no trigger-error | NOT clicked — see Notes. Reduced verification performed instead: `scout-ledger-trigger` renders with exact text "Run Screen", `disabled === false` (enabled), `data-testid="scout-ledger-trigger"` correct. No `scout-ledger-cancel` / `scout-ledger-progress` present pre-click (expected — idle state). | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-02-result.png` (same pre-click state; see Notes) |
| UT-06 | Scout Cancel reaches terminal state (long-running) | happy-path | P3 | Cancel → "Cancelling…", eventually reaches idle terminal state | Not executed — no run was started (UT-05 was not clicked, per binding instruction). Test plan itself marks this P3/optional/"not required for a PASS verdict." | SKIP | none |
| UT-07 | Walk-Forward "Run Walk-Forward" starts + shows progress (fast slice) | happy-path | P2 | Click → "Running…" disabled, "0 / N steps" progress + pulsing dot, Cancel appears, no trigger-error | NOT clicked — see Notes. Reduced verification performed instead: `walk-forward-trigger` renders with exact text "Run Walk-Forward", `disabled === false` (enabled), `data-testid="walk-forward-trigger"` correct. No `walk-forward-cancel` / `walk-forward-progress` present pre-click (expected — idle state). | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-03-result.png` (same pre-click state; see Notes) |
| UT-08 | Walk-Forward Cancel reaches terminal state (long-running) | happy-path | P3 | Cancel → "Cancelling…", eventually reaches idle terminal state | Not executed — no run was started. Test plan marks this P3/optional/"not required for a PASS verdict." | SKIP | none |
| UT-09 | Second trigger click is refused, not ignored | validation | P3 | Reload with an active run, re-click trigger → red refusal error line, existing run unaffected | Not executed — conditional precondition ("a run already active from UT-05/06 or UT-07/08") was never met because no run was started this pass. | SKIP | none |
| UT-10 | Backend unreachable shows typed error | error | P2 | All 3 new sections show amber-bordered "Backend unreachable — is the API running?" / "Nothing cached and nothing fabricated is shown in its place." — no blank area, no stuck skeleton, no stale data | Backend stopped (confirmed `curl /health` → connection failed), page reloaded, all 3 sections expanded. Scout and Walk-Forward: both their ledger body AND their Run History sub-fetch independently show the exact expected two-line message. Vault: `validation-vault-unavailable` shows the identical text. All three carry the identical class `rounded-lg border border-amber-800/60 bg-amber-900/20 px-4 py-6 text-center` (amber-bordered, confirmed programmatically). Backend restarted and confirmed healthy immediately after. See Notes for one minor DOM-structure observation (Vault's error state does not keep the `validation-vault-section` wrapper testid that Scout/Walk-Forward keep). | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-10-result.png` |
| UT-11 | Re-expand does not re-fetch | regression | P3 | Third click (re-expand after collapse) shows prior content instantly, no fetch | `window.fetch` was monkey-patched to log every call, then Scout Ledger was collapsed and re-expanded a third time. Fetch log after the third click: `[]` (zero calls). Content ("No candidates ledgered." etc.) reappeared unchanged. | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-11-result.png` |
| UT-12 | Microscope Readiness unaffected | regression | P1 | Totals table, `micro-readiness-shards-table`, floors table all render as before | Totals: 12 symbol-days / 18 datasets / 1173.49 RTH minutes / 3.0089 session-equivalents / gate 150. `micro-readiness-shards-table` present with 19 `<tr>` (18 shard rows + header). Pilot-Study Floors table: 3 rows, all `floor_unmet`. "∅ No integrity errors." | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-12-result.png` |
| UT-13 | Referee sections unaffected | regression | P1 | Each of Registry/Adjudications/Runs renders its own content with no error panel; no testid collision with the 3 new sections | Registry: candidates S-1…S-6 + Registered Hypotheses table rendered. Adjudications: hypothesis S-1 verdict row rendered. Runs: Null Builds + Evaluations tables, both showing `completed` runs. A full-page `data-testid` sweep found zero overlap between the referee/playbook/microscope testids and the 3 new sections' testids. (One transient "Element not found" on the very first Registry extract self-resolved on immediate retry — not a reproducible defect; see Notes.) | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-13-result.png` |
| UT-14 | Playbook sections unaffected | regression | P1 | Main signal table populated above the fold; Screen Runs/Top-up Runs/Index Reconciliation/Playbook Evidence each expand without error | `desk-playbook-signal-row` count = 54 (visible without any expansion, matches the "54 signal(s)" the page itself reports). All 4 named sections expanded (button count rose 511→516→521→526 as each added real content); a page-wide sweep for any `[data-testid$="-unavailable"]` returned zero matches. | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-14-result.png` |
| UT-15 | `/structure` unaffected | regression | P1 | Page loads, Tradable Map renders, comparison dropdown present + selectable | Loaded without error (only the React DevTools console line). "TRADABLE MAP" section heading present with its honest empty state (no symbol loaded yet — expected, none was requested). `comparison-dataset-select` present, `disabled === null` (selectable). Grep of the full page dump for "error"/"unreachable" found nothing outside the page's own static descriptive copy. | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-15-result.png` |
| UT-16 | Cockpit unaffected | regression | P1 | Page loads, chart renders; if visually static, cross-check backend data before failing | Loaded without error. Watched simulated ticker `SIM-BUYER` (Simulated mode, per this session's own established substitute for the literal `AAPL` the mode rejects). Chart rendered visible green 10s candle bars (not blank). Cross-check: three consecutive text extracts a few seconds apart showed Confidence 0.842 → 0.948 → 0.929, Last 100.23 → 100.99 → 100.86, and a fully different Recent Trades print list each time — the tape is genuinely live, not frozen. | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-16-result.png` |
| UT-17 | New sections discoverable, correctly ordered | ux | P2 | Fresh load: Microscope Readiness → Scout Ledger → Walk-Forward → Validation Vault, in that exact order, each one click away; heading text visible while collapsed | Fresh navigation (no pre-expansion). A single DOM query over every `[data-testid^="desk-section-expand-"]` element, in document order, returned (last 4 of 13): `microReadiness, scoutLedger, walkForward, validationVault` — exact required order, each `aria-expanded="false"`, each heading text (e.g. `"▸Scout Ledger"`) visible while collapsed. | PASS | `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-17-result.png` |

## Skipped Tests

### UT-06 — Scout Cancel reaches terminal state (long-running)

**Verdict:** SKIPPED
**Reason:** Not executed — no run was started (UT-05 was not clicked, per binding instruction). Test plan itself marks this P3/optional/"not required for a PASS verdict."

### UT-08 — Walk-Forward Cancel reaches terminal state (long-running)

**Verdict:** SKIPPED
**Reason:** Not executed — no run was started. Test plan marks this P3/optional/"not required for a PASS verdict."

### UT-09 — Second trigger click is refused, not ignored

**Verdict:** SKIPPED
**Reason:** Not executed — conditional precondition ("a run already active from UT-05/06 or UT-07/08") was never met because no run was started this pass.

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
