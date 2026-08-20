# Phase goal-rapid-microscope-iter-16 — UI Test Results

**Phase:** goal-rapid-microscope-iter-16
**Date:** 2026-08-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 9/10 tests passed (1 skipped, 0 failed)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
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

---

## Passed Tests

### UT-01 — `/desk` loads cleanly with zero console errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-16-evidence/UT-01-result.png`
- Fresh navigation to `/desk`, `data-testid="desk-title"` textContent "Desk", all 11 always-rendered collapsible sections present and collapsed ("▸"). Console held only the standard React DevTools info line — no errors.

### UT-02 — Microscope Readiness carries its testid in all 3 render states
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-16-evidence/UT-02-result.png`
- **Loaded state:** expanded on a fresh load; `document.querySelector('[data-testid="micro-readiness-section"]')` present; text confirmed "Distinct symbol-days" → 1, "Distinct datasets" → 2, exactly 2 `PG` rows in the Legacy Tick Shards table (byte-consistent with the carried-context real-store figures).
- **Unavailable state:** the test plan's steps 4–7 call for stopping the real backend process. Killing it (via `kill`, `pkill`, or any process-termination command) was **blocked by this sandbox's auto-mode classifier** on every attempted invocation, and the instructions governing that denial explicitly disallow working around it via alternate destructive commands. Rather than skip this half of the test, I reached the identical code path safely and precisely: `fetchMicroReadiness()` (`apps/frontend/lib/api.ts:2164-2185`) wraps its `fetch()` call in try/catch and returns the exact same `{ok:false, data:null, error:"Backend unreachable — is the API running?"}` on ANY fetch rejection, whether from a dead backend or any other transport failure. I installed a one-line `window.fetch` override (via `eval`, undone by the next full navigation) that rejects only requests to `/research/desk/micro/readiness`, then triggered a first-expand fetch. This drove the component into its real, production `!readinessResult.ok` render branch through its actual code path — not a mocked DOM state. Result: `data-testid="micro-readiness-section"` present, panel text "Backend unreachable — is the API running?\nNothing cached and nothing fabricated is shown in its place." rendered verbatim, console clean (the simulated rejection was caught gracefully, no uncaught exception). The real backend process (PID 1557297) was never touched and stayed continuously healthy throughout (verified before, during, and after via `/health` — same PID, uninterrupted uptime).
- **Loading state:** confirmed via direct source read rather than a live capture — a local-backend fetch resolves in single-digit milliseconds, well under a paintable frame, making a reliable screenshot of this state impractical. `page.tsx:5891-5896` shows the `readinessResult === null` branch also wraps `<div data-testid="micro-readiness-section"><LoadingPanel .../></div>` — structurally identical in shape to the two branches verified live.

### UT-03 — Scout Ledger renders the real honest-empty state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-16-evidence/UT-03-result.png`
- "Run Screen" (`scout-ledger-trigger`) visible, not clicked. "Ledger chain verification: ok". `scout-ledger-families-empty` = "No candidates ledgered.". `scout-ledger-runs-empty` = "No scout runs recorded yet.". Zero console errors.

### UT-05 — Console clean across every collapsible Desk section
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-16-evidence/UT-05-result.png`
- Clicked, in order, every section the plan names that actually exists in the current DOM: Top-up Runs, Index Reconciliation, Screen Runs, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness (covered under UT-02), Scout Ledger, Walk-Forward, Validation Vault — 11 of 13. `get_console_messages` was checked after each click (individually, then in small batches); the only line ever present was the one-time React DevTools info message from initial page load — no red errors, no hydration warnings, at any point.
- **Finding, not a defect:** "Screen Comparison" and "Provenance" (2 of the plan's 13 names) do not exist in the DOM at all today. Source inspection (`page.tsx:11931` and `:11950`) shows both are conditionally rendered only when `latest !== null` (i.e., only after a screen has been computed at least once). The real store has never had a screen run — confirmed by the "Desk screen not computed yet." panel visible at the top of every screenshot this round — so their absence is expected, pre-existing behavior unrelated to this round's diff (which touches only `MicroReadinessSection` and the Scout table's two reads). This is not a regression and does not affect the verdict.
- Note: the evidence screenshot for this test is a full-page capture with all 13 checked sections expanded simultaneously; because Referee Registry renders a large table, the resulting image is ~17,000px tall and not easily human-legible at a glance — the per-section screenshots for UT-03/UT-06/UT-07 (shorter, individually expanded) are the more readable references for those sections' actual content.

### UT-06 — Walk-Forward / Validation Vault unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-16-evidence/UT-06-result.png`
- Walk-Forward: "Run Walk-Forward" visible, not clicked; "Ledger chain verification: ok"; `walk-forward-fold-specs-empty` = "No fold specs registered."; `walk-forward-sequences-empty` = "No walk-forward sequences run.".
- Validation Vault: "Shard ledger chain verification: ok", "Universe ledger chain verification: ok"; `validation-vault-shards-empty` = "No shards recorded."; `validation-vault-universes-empty` = "No universes registered."; a direct DOM query for `<button>` elements inside `[data-testid="validation-vault-section"]` returned an empty array — no compute/seal/expose control anywhere in the section, confirming it is read-only as designed.

### UT-07 — Playbook / Referee sections unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-16-evidence/UT-07-result.png`
- "Playbook Signals" renders its description and "Playbook not computed for this session." panel immediately, above the fold, no click required.
- "Referee Registry" expanded with 2,877 characters of real content and zero console errors (then re-collapsed to keep the evidence screenshot legible).
- "Referee Adjudications" expanded: real explanatory copy plus "No hypotheses registered." empty state.
- "Referee Runs" expanded: "Null Builds" → "No hypotheses registered — nothing to build a null for yet." / "No null-build runs recorded yet."; "Evaluations" → "No hypotheses registered — nothing to evaluate yet." / "No evaluation runs recorded yet.". No error panel anywhere, console clean throughout.

### UT-08 — Cockpit live tape + chart
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-16-evidence/UT-08-result.png`
- Mode selector default confirmed "Simulated" via `aria-pressed="true"` (Live/Historical both `"false"`). Typed `SIM-BUYER`, clicked Watch. "Watching SIM-BUYER" / "Live" (green dot) / "Tape State: Buyer Control" rendered; Quote, Features, Recent Trades, Observations, and Event Log panels all populated with real-looking simulated values. Bid/ask and confidence values visibly differed between the interim DOM read (100.36/100.38, confidence 0.932) and the screenshot moment (100.68/100.70, confidence 0.928) — direct proof the tape is actively live-updating, not a frozen capture. No error banner.

### UT-09 — `/structure` load + Tradable Map + Comparison
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-16-evidence/UT-09-result.png`
- Symbol `AAPL`, As-of `2026-06-22 16:00:00`, clicked Load. `[data-testid="tradable-map-table"]` rendered with exactly 10 `tbody` rows (5 resistance + 5 support, all Class A). First resistance row read `300.11–302.2 | Class A | 171 | 849 | round number` verbatim. `[data-testid="comparison-dataset-select"]` present and not disabled. No error banner, console clean.

### UT-10 — Nav bar unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-16-evidence/UT-10-result.png`
- `Array.from(document.querySelectorAll('[data-testid="nav-link"]')).map(a => a.dataset.label)` returned exactly `["Cockpit","Structure","Desk"]` — checked on `/`, `/structure`, and `/desk`.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-04 — [Optional] Malformed Scout row degrades gracefully
**Verdict:** SKIPPED
**Reason:** The test plan itself marks this P3 case optional and non-gating for this round ("Include only if the executing lane can stand up an isolated, scoped backend/frontend pair separate from the shared dev instance"). Standing up a second, separately-scoped backend+frontend pair is outside a QA pass's normal scope and was not attempted. As a partial substitute, I read the actual shipped code: `apps/frontend/app/desk/page.tsx:6321` (`{trial.feature?.name ?? "—"} / {trial.feature?.transform ?? "—"}`) and `:6323` (`{trial.outcome?.horizon_key ?? "—"}`) show exactly the optional-chaining-plus-"—"-fallback pattern the spec describes, matching the expected-result text verbatim ("— / —" and "—"). This is source verification only, not a live browser confirmation, so the row stays SKIPPED rather than PASS.

---

## Goal-Mode Journey Lane (in addition to the UT test plan)

### J-10 — The kept product stands — traps armed, sentinel green (target journey)
**Verdict:** PASS
**Scope note:** this agent verified the sentinel's browser-visible surfaces only — the full backend suite count, config fingerprint computation, and referee-module SHA-256 listing are backend/auditor territory, not browser QA.
- Cockpit `/`: live tape + chart confirmed live-updating for SIM-BUYER (see UT-08).
- `/structure`: load + Tradable Map confirmed, AAPL @ 2026-06-22 16:00:00 ET → 10 bands (see UT-09).
- Every shipped `/desk` section, including all three Referee sections, rendered without error (see UT-01, UT-02, UT-05, UT-06, UT-07).
- The one browser-visible fragment of TC-17 (the config fingerprint string) was confirmed rendered verbatim inside Referee Registry: `"config fingerprint 08e471b10130e1e2"` — matches the required value exactly.
- Golden replay script written to `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` (overwritten; the prior version's `/structure` step used a 17:00:00 as-of and a 10s timeout — the new script uses this round's carried-context time of 16:00:00, a 20s timeout given today's host load, and adds explicit assertions for the four Rapid-Microscope sections plus Referee Registry/Adjudications/Runs). Linted clean: `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-rapid-microscope/journey-scripts --journeys J-10` → `J-10 ok`.

### J-07 — Graduation — provenance in, nothing laundered out (LLM fallback, no golden by design)
**Verdict:** PASS
- Direct-endpoint navigation to `http://localhost:8301/research/desk/micro/graduation` (confirmed HTTP 200 via `curl` also). Body: `{"families":[],"message":"No candidates ledgered.","chain_verification":{"ok":true,"failed_at_row":null,"reason":null}}` — an honestly-empty, correctly-shaped response consistent with every other never-touched ledger on this store, with the chain-verification mechanism itself confirmed intact (`ok:true`). Screenshot: `reports/qa/goal-rapid-microscope-iter-16-evidence/J-07-verify.png`. No golden replay script written for this journey — the dispatch instructions state none exists for it "by design" (a raw JSON endpoint check doesn't fit the demo_runner's click/fill journey format).

### Required-still-passing journeys (J-01, J-02, J-03, J-04, J-05, J-08)
Not re-tested per the dispatch instructions — deterministic replay from stored golden scripts already re-verified these this iteration; their result rows merge in automatically. No rows emitted for them here, per instruction.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (store-scoped rig; PID 1557297, continuously healthy throughout this run — never restarted)
- **Browser:** Chrome/151.0.7922.71 (headless), attached to the pre-existing CDP endpoint at 127.0.0.1:9222 per carried instructions — not launched or killed by this agent
- **Test Date:** 2026-08-20
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-16-evidence/`
- **Host load note:** a concurrent pytest suite (this project) plus an unrelated project's suite were both running on this host during the pass; one `/structure` load was given a 20-30s timeout budget for this reason. No timeout was actually hit.
