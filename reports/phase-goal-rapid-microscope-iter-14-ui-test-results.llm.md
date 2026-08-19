# Phase goal-rapid-microscope-iter-14 — UI Test Results

**Phase:** goal-rapid-microscope-iter-14
**Date:** 2026-08-19
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 14/17 tests passed (3 skipped)

All 9 P1 tests pass. All smoke and happy-path tests pass (UT-05/UT-07 pass on the
reduced, button-state-only verification the pump's carried context designates
sufficient — see Notes). UT-06, UT-08, UT-09 are SKIPPED by design: the test plan
itself marks UT-06/UT-08 optional/non-blocking (P3, long-running against the live
corpus with no reliable fast cancel), UT-09 is conditional on an active run existing,
and this run's own binding instruction was not to click "Run Screen" / "Run
Walk-Forward" at all (see Notes). No test FAILED.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
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

---

## Passed Tests

### UT-01 — `/desk` loads, all headers present, collapsed
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-01-result.png`
- Navigated to `/desk`; full content rendered (Screen History, Forward Returns, Playbook Signals, and all 13 collapsible sections). All 4 named headers ("Microscope Readiness", "Scout Ledger", "Walk-Forward", "Validation Vault") present with the closed `▸` indicator. Console carried only the informational React DevTools line — no errors.

### UT-02 — View Scout Ledger contents
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-02-result.png`
- Expand toggled `aria-expanded` to `true`. Body text matched the real backend's current empty state exactly ("No candidates ledgered.", "No scout runs recorded yet."), plus "Ledger chain verification: ok". Confirmed via `attr` that the Run Screen trigger is enabled and no Cancel control exists pre-run.

### UT-03 — View Walk-Forward contents
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-03-result.png`
- The one real registered sequence (`seq-d39d20e47af24671`) rendered with its refused verdict, full 5-row/8-column fold table, and the Recency summary line, exercising the "refused" verdict path live (not just the happy path). Run History correctly empty.

### UT-04 — View Validation Vault contents, confirm read-only
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-04-result.png`
- Strongest evidence of the run: a programmatic DOM sweep for every interactive-control tag/role inside `[data-testid="validation-vault-section"]` returned zero matches, directly proving the section has no seal/assign/expose/compute control of any kind, not merely that none was visually spotted.

### UT-05 — Scout "Run Screen" starts + shows progress (fast slice)
**Verdict:** PASS (reduced scope — see Notes)
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-02-result.png`
- Per this run's binding carried-context instruction, the button was not clicked. Verified instead that `scout-ledger-trigger` renders with the exact label "Run Screen" and `disabled === false`.

### UT-07 — Walk-Forward "Run Walk-Forward" starts + shows progress (fast slice)
**Verdict:** PASS (reduced scope — see Notes)
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-03-result.png`
- Same treatment as UT-05: `walk-forward-trigger` renders with the exact label "Run Walk-Forward" and `disabled === false`; not clicked.

### UT-10 — Backend unreachable shows typed error
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-10-result.png`
- All three sections' amber panels carry byte-identical text and CSS class. See Notes for one minor, non-blocking DOM-structure observation surfaced while investigating an initially-failed selector on the Vault panel.

### UT-11 — Re-expand does not re-fetch
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-11-result.png`
- Verified with a `window.fetch` spy rather than timing/visual inference — the third (re-expand) click produced zero fetch calls.

### UT-12 — Microscope Readiness unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-12-result.png`

### UT-13 — Referee sections unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-13-result.png`

### UT-14 — Playbook sections unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-14-result.png`

### UT-15 — `/structure` unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-15-result.png`

### UT-16 — Cockpit unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-16-result.png`

### UT-17 — New sections discoverable, correctly ordered
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-14-evidence/UT-17-result.png`

---

## Failed Tests

None.

---

## Skipped Tests

### UT-06 — Scout Cancel reaches terminal state (long-running)
**Verdict:** SKIPPED
**Reason:** No Scout run was started this pass (see Notes — "Run Screen" was deliberately not clicked), so the cancel-to-terminal-state flow has no run to act on. The test plan itself scores this P3/optional and states it is "not required for a PASS verdict."

### UT-08 — Walk-Forward Cancel reaches terminal state (long-running)
**Verdict:** SKIPPED
**Reason:** Same as UT-06 — no Walk-Forward run was started this pass. P3/optional per the test plan.

### UT-09 — Second trigger click is refused, not ignored
**Verdict:** SKIPPED
**Reason:** Explicitly conditional on "a run already active from UT-05/06 or UT-07/08." No run was ever started this pass, so the precondition was never met.

---

## Notes

**Binding instruction not to click the compute triggers.** This session's carried
context (established earlier in the same goal-mode pump run, before this dispatch)
directed: "DO NOT click 'Run Screen' or 'Run Walk-Forward'. They start a real
computation that ran past 25 minutes without finishing a single candidate, on the
shared backend, with no reliable fast cancel... Verifying the control renders and is
enabled is sufficient." This is stricter than the test plan's own UT-05/UT-07 steps
(which say to click and observe only the first 1–2 seconds), so the stricter,
more-recent, session-specific instruction was followed: UT-05 and UT-07 were scored
PASS on the reduced (render + enabled-state) check only, and UT-06/UT-08/UT-09 —
which all depend on a run actually being started — were SKIPPED rather than executed
in any partial form. Nothing in this run POSTed to either compute-trigger route.

**Backend infrastructure.** The QA backend (`:8301`) was not running when this
dispatch began (`curl /health` → connection refused, no process on the port, no log
file). It was brought up via the project's own `scripts/start-backend.sh` with
`CHAIN_BACKEND_PORT=8301 CHAIN_FRONTEND_PORT=3301` (the same port-derivation
convention `browser-qa-phase.sh` itself uses) and confirmed healthy before any test
ran. The readiness endpoint it served (12 symbol-days / 18 datasets / one populated
Walk-Forward sequence / zero Scout families / zero Vault shards) matches the phase
spec's own description of "the real, live state" this test plan is written against,
so this is the correct backend, not a substitute. It was intentionally stopped and
restarted again as UT-10's own precondition/postcondition.

**New, minor finding (not one of the 3 pre-disclosed ones).** During UT-10, querying
`[data-testid="validation-vault-section"]` while the backend was down returned
"element not found," while `[data-testid="scout-ledger-section"]` and
`[data-testid="walk-forward-section"]` both still resolved (wrapping their own
"Backend unreachable" content) in the same state. Investigation confirmed this is
real: the Vault's error path renders only `[data-testid="validation-vault-unavailable"]`
without its usual `validation-vault-section` outer wrapper testid, while Scout and
Walk-Forward keep their outer `-section` wrapper present in both the loaded and
error states. The user-visible text and amber styling are byte-identical across all
three sections (confirmed programmatically) — this is a DOM-structure/testability
inconsistency only (it would only affect an automated selector scoped to the wrapper,
never a human operator), not a functional or content defect, and not a P1/blocking
issue. Filed here for visibility per this run's own instruction not to paper over a
defect a test happens to surface.

**Transient selector miss (not a defect).** The first `extract` against
`[data-testid="referee-registry-section"]` during UT-13 returned "Element not found"
immediately after the expand click; an `eval` DOM query one call later confirmed the
element existed and a same-selector retry then returned its full content correctly.
This reads as a render-timing race between the click and the extract, not a
reproducible page defect — flagged here for transparency, not scored as a failure,
per the skill's 2-recovery-attempt allowance.

**Pre-existing known issues (not re-tested).** Per the test plan's own "Known Issues"
section and this run's carried context, three findings remain open from code review
and are not independently re-triggerable against today's live data state: Scout's
family-header omission of `family_root_id` (no live family row exists to inspect —
zero registered families), Walk-Forward's empty-state copy reusing Scout's "No
candidates ledgered." wording (unreachable — the live Walk-Forward ledger is
non-empty), and the Scout/Walk-Forward compute poll loops not stopping on navigation
(no single-tab user-visible symptom). None of these were re-filed as new findings;
none were newly confirmed or newly contradicted this run.

**J-08 scope.** This run exercised J-08's panel half only (Scout Ledger, Walk-Forward,
Validation Vault rendering — UT-01–UT-04, UT-10–UT-17), matching the phase spec's own
"J-08 scored `partial` this iteration" framing (the four MCP proxy tools are iteration
15's half). No golden replay script was written for J-08 this run, since a golden is
only written for a journey verified fully PASS, and J-08's own acceptance is not yet
complete by design.

**J-01–J-05 (replay-covered) and J-07 (no UI surface).** Per the dispatch's
GOAL-MODE REGRESSION LANES note, J-01–J-05 were already re-verified this iteration by
the deterministic replay lane from stored golden scripts and are not re-tested or
re-rowed here. J-07 ("Graduation") has no UI test case in this iteration's test plan
and none was invented — its acceptance (`docs/goal.md`) is a backend
fixture-pipeline/module-provenance check with no `/desk` or other UI surface, so it
is out of scope for browser QA by nature, consistent with this agent's rule to never
browse a page the plan does not name.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome (headless) via Chrome MCP, attached to the pinned CDP endpoint at `127.0.0.1:9222`
- **Test Date:** 2026-08-19
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-14-evidence/`
