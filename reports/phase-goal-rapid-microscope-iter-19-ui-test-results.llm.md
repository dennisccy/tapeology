# Phase goal-rapid-microscope-iter-19 — UI Test Results

**Phase:** goal-rapid-microscope-iter-19
**Date:** 2026-08-20
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 6/6 executed tests passed (0 failed). UT-02, UT-03, UT-04, UT-05 were not
re-executed by this agent per the goal-mode dispatch instruction — deterministic golden
replay already re-verified their target journeys (J-02, J-03, J-04, J-05) before this run,
and the dispatch note explicitly said not to re-test them or emit rows for them ("their rows
merge into the results automatically after your run"). No row is emitted for them below.
All values these four journeys assert (Fallback frac, Joinable corpus — withheld (excluded),
both sections' "Ledger chain verification:" lines) were also incidentally observed live and
correct during UT-06/UT-09's own browser session (see notes in Passed Tests), consistent
with the replay's own PASS.

**Backend under test:** the fixture-scoped QA backend on port 8301, launched by
`apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`. Per its manifest at
`reports/qa-scoped-backend-store-manifest.md` (launched_at_utc 2026-08-20T13:34:48Z), this
process is bound to `TAPEOLOGY_DATASET_DIR=.../tapeology-store-scope-qa/rig/datasets` and
sibling store-root vars under `/home/dennis-chan/.cache/iad/iad.goal-rapid-m-1efe448c.2777839/tapeology-store-scope-qa/rig/`
— NOT the real/ambient data store. This browser lane exercised the fixture-scoped store; no
statement in this report should be read as "real data store."

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders, "Playbook Signals" heading visible, no console errors | Navigated to `/desk`; page rendered fully (Desk heading, Screen/Backfill/Playbook Signals sections all present); "Playbook Signals" heading visible; console showed only the standard React DevTools info line, no errors | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-01-result.png` |
| UT-06 | J-10 kept-product sentinel, end to end | regression | P1 | Every confirm step (Cockpit → Structure → Desk) passes in order, no navigation error/blank page/console error | Full 11-confirm flow executed live: `/` showed "No ticker watched" → typed SIM-BUYER → clicked Watch → "Buyer Control" appeared (via await, tape state moved off "Warming up") → `/structure` showed "Tradable Map" → typed AAPL + as-of "2026-06-22 16:00:00" → clicked Load → "300.11–302.2" resistance band appeared → `/desk` showed "Playbook Signals" → Microscope Readiness expand showed "Distinct symbol-days" (=2) → Scout Ledger expand showed "No candidates ledgered." → Walk-Forward expand showed "No fold specs registered." No console errors at any step | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-06-result.png` |
| UT-07 | Validation Vault + Referee sections still render correctly | regression | P1 | All four confirm steps pass, text unchanged from prior iterations | In the same `/desk` session as UT-06: Validation Vault expand showed "iter18-qa-universe"; Referee Registry expand showed "config fingerprint 08e471b10130e1e2"; Referee Adjudications expand showed "No hypotheses registered."; Referee Runs expand showed "No evaluation runs recorded yet." | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-07-result.png` |
| UT-08 | Section headings stay visible while collapsed | ux | P2 | All 7 named headings visible with "▸" markers, none missing/blank | Fresh `/desk` load, no clicks: extracted page text showed all of Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault each preceded by a "▸" marker | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-08-result.png` |
| UT-09 | Expand/collapse mounts and unmounts section body | ux | P2 | Heading stays visible through both clicks; body mounts on expand, unmounts on collapse | Clicked Microscope Readiness expand: marker flipped to "▾", body appeared (Corpus Totals, Joinable Corpus table with "Joinable corpus — withheld (excluded)" = 0, Legacy Tick Shards table with "Fallback frac" column showing 0.77/0.75/0.00, "No integrity errors."). Clicked again: marker returned to "▸" and the entire body (all of the above) was absent from the extracted page text — heading remained visible throughout | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-09-result.png` |
| UT-10 | Backend-unavailable shows the real error panel, not fabricated ledger text | error | P2 | `data-testid="scout-ledger-unavailable"` panel with an error message appears; "Ledger chain verification:" text does NOT appear | Installed a `window.fetch` override via `eval` (browser-side; the real backend process was never stopped) that rejects only requests to `/research/desk/micro/scout`, then clicked the Scout Ledger section header. Rendered panel text: "Backend unreachable — is the API running?" / "Nothing cached and nothing fabricated is shown in its place." (both the section body and its Run History sub-panel). `data-testid="scout-ledger-unavailable"` confirmed present in the captured HTML. Grep of the captured page text for "Ledger chain verification" returned 0 matches | PASS | `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-10-result.png` |

**Not re-executed (golden-replay-covered, per dispatch instruction — no row emitted):** UT-02 (J-02), UT-03 (J-03), UT-04 (J-04), UT-05 (J-05).

---

## Passed Tests

### UT-01 — `/desk` loads without errors (smoke)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/desk`; page loaded fully with no blank screen or error message.
- "Playbook Signals" section heading visible in the page text.
- Console messages checked via `get_console_messages`: only the standard "Download the React DevTools" info line — no errors.

### UT-06 — J-10 kept-product sentinel: Cockpit → Structure → Desk, end to end (regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-06-result.png`
- `/`: "No ticker watched" confirmed before watching.
- Typed "SIM-BUYER" into the ticker input, clicked the Watch submit button; tape state started at "Unclear / Warming up" and, per `await_text` (20s budget), settled to show "Buyer Control".
- `/structure`: "Tradable Map" heading confirmed. Typed "AAPL" into the symbol input (`aria-label="Structure symbol"`) and "2026-06-22 16:00:00" into `data-testid="structure-as-of-input"`, clicked `data-testid="structure-load-button"`. The resistance band row "300.11–302.2 · Class A · score 171 · 849 members · round number" appeared (confirmed via `await_text` and a full-page text extract).
- `/desk`: "Playbook Signals" confirmed. Expanded Microscope Readiness ("Distinct symbol-days" = 2 among Corpus Totals), Scout Ledger ("No candidates ledgered.", "Ledger chain verification: ok"), Walk-Forward ("No fold specs registered.", "Ledger chain verification: ok").
- No console errors observed at any point (checked after the full sequence).
- Golden replay script rewritten/confirmed at `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` (lint-clean via `demo_runner.py --mode lint`).

### UT-07 — Validation Vault and all three Referee sections still render correctly (regression)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-07-result.png`
- Expanded Validation Vault: "iter18-qa-universe" visible (confirmed via `await_text` after an initial capture raced ahead of the section's own data fetch).
- Expanded Referee Registry: "config fingerprint 08e471b10130e1e2" visible.
- Expanded Referee Adjudications: "No hypotheses registered." visible.
- Expanded Referee Runs: "No evaluation runs recorded yet." visible.

### UT-08 — Section headings stay visible while collapsed (ux)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-08-result.png`
- Fresh `/desk` load, no clicks. Full-page text extract confirmed all of: Top-up Runs, Index Reconciliation, Screen Runs, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness, Scout Ledger, Walk-Forward, Validation Vault are visible, each preceded by a "▸" collapsed marker. No heading missing or replaced by blank space.

### UT-09 — Expanding then re-collapsing a section hides its body but keeps the heading (ux)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-09-result.png`
- First click on Microscope Readiness header: marker flipped "▸"→"▾"; body content appeared (Corpus Totals, Sealed Tranche, Legacy Tick Shards table with "Fallback frac" column, Pilot-Study Floors, "No integrity errors.").
- Second click on the same header: marker returned to "▸"; a full-page text re-extract showed none of the above body content anywhere on the page — confirming unmount, not merely CSS-hidden — while the "Microscope Readiness" heading itself remained visible throughout.

### UT-10 — Backend-unavailable state shows the real error panel, not fabricated ledger text (error)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-19-evidence/UT-10-result.png`
- Method note: rather than stopping the shared fixture-scoped backend process (which other concurrent goal-mode lanes may depend on) or restarting the app, this was simulated client-side: an `eval`-injected `window.fetch` override rejected only requests whose URL contains `/research/desk/micro/scout`, leaving every other request (and the real backend process) untouched. This is equivalent in effect to the test plan's own suggested "block the route via devtools network throttling" approach.
- After installing the override and clicking the Scout Ledger section header, the section rendered `data-testid="scout-ledger-unavailable"` (confirmed present in captured HTML) with the text "Backend unreachable — is the API running?" / "Nothing cached and nothing fabricated is shown in its place." for both the ledger body and its Run History sub-panel.
- Grepped the captured page markdown for "Ledger chain verification" — 0 matches, confirming UT-04's assertion is not vacuous: the `UnavailablePanel` branch renders genuinely different text.
- Page was reloaded (fresh navigate to `/desk`) immediately afterward to clear the fetch override and leave the shared browser in a clean state.

---

## Failed Tests

None.

---

## Skipped Tests

None — frontend, backend, and Chrome MCP were all available for the full run. UT-02–UT-05 were intentionally not re-executed per explicit goal-mode dispatch instruction (already re-verified via deterministic golden replay of J-02–J-05 before this run began); they are not counted as SKIPPED test-plan rows here, per that instruction's "do NOT emit rows for them."

---

## Notes for the merge / evaluator

- This agent's Chrome session hit one transient race: two section-expand clicks issued back-to-back without an intervening wait once produced a stale/short DOM capture (once even appearing to echo `/structure` page content while `list_tabs` confirmed the single tab was still at `/desk`). Recovery: reloaded `/desk` fresh and re-ran the affected clicks sequentially with `await_text` after each, which resolved cleanly every time. No product defect — a browser-automation timing artifact, noted per the "console error vs FAIL" honesty rule; it did not affect any recorded verdict.
- `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` was rewritten (content-identical to what was already present, all 15 steps freshly re-verified against the running app) and lints clean.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (fixture-scoped QA backend; see manifest note above)
- **Browser:** Headless Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), attached to existing CDP endpoint on 127.0.0.1:9222
- **Test Date:** 2026-08-20
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-19-evidence/`
