# Phase goal-hypothesis-foundry-iter-5 — UI Test Results

**Phase:** goal-hypothesis-foundry-iter-5
**Date:** 2026-08-27
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 9/9 tests passed (0 skipped)

Regression lanes J-01, J-03, J-04 were already re-verified by deterministic golden replay per the
dispatch note and are NOT re-tested or re-scored here (no rows emitted for them; their rows merge
in automatically). This report covers the 9 UT-XX cases in the test plan, which exercise this
iteration's target journeys J-02 (Sources/Compiler), J-05 (Hermetic Oracles), and J-06
(Epoch/Manifest, new), plus UT-08's Cockpit/Structure sentinel check.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads, Hypothesis Foundry reachable | smoke | P1 | Page renders, "Hypothesis Foundry" section header visible and expandable, no console error | Page loaded, section expanded via `[data-testid="desk-section-expand-hypothesisFoundry"]`, panel content rendered (Era-Open Baseline, five nested rows) | PASS | `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-01-result.png` |
| UT-02 | Epoch / Manifest shows the real committed epoch | happy-path | P1 | Emerald "Real Epoch — not a fixture" banner, Status=Committed, non-empty identity hashes, `outcome_access_census: 0`, 11 source-disposition rows, "Compiled families (0)" honest empty text, audit-report reference "(committed)" | All confirmed verbatim via DOM text extraction + screenshot: banner "REAL EPOCH — NOT A FIXTURE" (emerald border/text), "Status: Committed — Git-visible pre-outcome barrier crossed", `epoch_id: epoch:afd19e9c11a6534f`, all 6 identity hashes non-empty, `outcome_access_census: 0`, exactly 11 disposition rows, "Compiled families (0)" → "Zero compiled candidates this epoch — every required source disposed non-COMPILED.", audit line with "(committed)" in emerald | PASS | `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-02-result.png` |
| UT-03 | Sources/Compiler shows both siblings + 3 fields | happy-path | P1 | Amber fixture banner, audit-report reference line, exactly 8 fixture rows incl. `fixture-variant-a`/`fixture-variant-b` with mutual "Alternatives:", all rows show the 3 additive fields, `fixture-unsupported-stat` shows "(none)", `fixture-alias-older` shows the exact supersession string | All confirmed via DOM text extraction: amber "HERMETIC FIXTURE — NOT THE REAL EPOCH" banner, "Real registry audit report: reports/hypothesis-foundry/source-registry-audit.md (committed alongside the real epoch — see Epoch / Manifest below)." present verbatim, exactly 8 `<li>` fixture rows counted (natural-boundary, variant-a, variant-b, magnitude-word, proxy, unsupported-stat, alias-older, directionless), variant-a/variant-b show reciprocal "Alternatives:", all 8 rows show "Operative formula refs:"/"Superseded fields:"/"Aliases/lineage ids:", `fixture-unsupported-stat` → "Operative formula refs: (none)", `fixture-alias-older` → "Superseded fields: event_time_window → docs/rapid-validation-spec.md#feature-windows" | PASS | `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-03-result.png` |
| UT-04 | Hermetic Oracles shows kill-type mapping + best-of-N | happy-path | P1 | 7-row `<label> → <FOUNDRY_STATE>` list incl. fragile/survive rows, non-blank `best_of_n_disclosure` line, five named oracles still PASS | Confirmed via DOM text extraction: exactly 7 kill-type-mapping rows ("insufficient → EVALUATED_INSUFFICIENT" ... "survive → DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"), including "fragile → EVALUATED_KILLED" and "survive → DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN"; "Best-of-N disclosure: n_variants_tried=7 · threshold_bps=0.1569542572940126" (numeric, non-blank); all five named oracles (All-blocked epoch completed, All-killed epoch completed, Multi-survivor preserved all, Crash-resume at scale verified, Protected-data trip fails closed / evidence class immutable) show PASS | PASS | `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-04-result.png` |
| UT-05 | Empty-families state renders honestly | validation | P2 | "Zero compiled candidates..." renders as visible body text, no red/rose error text anywhere in the subsection | Confirmed: text renders as plain body text under "Compiled families (0)" (not a spinner/blank/error banner); a DOM-wide scripted scan for red/rose-toned leaf-text elements (`r>150 && r>1.4g && r>1.4b`) across the entire page returned zero matches | PASS | `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-05-result.png` |
| UT-06 | Foundry panel degrades honestly on API failure | error | P2 | Panel shows `data-testid="foundry-panel-unavailable"` with readable prose (not a stack trace); after unblocking + refresh, panel returns to normal | Blocked `*/research/desk/micro/foundry*` client-side (`window.fetch` override — the MCP tool has no native network-interception action, so a script-level fetch/XHR block was used as the "equivalent network-interception call" the test plan permits), then clicked to expand Hypothesis Foundry (first deferred GET). `[data-testid="foundry-panel-unavailable"]` appeared showing "Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place." — readable prose, no stack trace. A fresh navigation (which drops the injected fetch override) plus re-expand confirmed the panel returns to normal (UT-02's "Era-Open Baseline" text reappeared) | PASS | `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-06-result.png` |
| UT-07 | J-01/J-03/J-04 subsections still render | regression | P1 | "Source registry hash:" shows real hex (not `not_yet_generated`); Interpreter Fixtures shows amber banner + non-empty scenario rows; Freeze/Integrity shows amber banner + Family Denominator table; no console errors | "Source registry hash: ed40dbc25e8fdb961258512dc01ccbaa4633e0ddb6f374288c6c78d681bd098d" (real hex, confirmed NOT the literal `not_yet_generated`); Interpreter Fixtures expanded, `[data-testid="foundry-interpreter-scenario-rows"]` found with 5 `<li>` rows, amber "Hermetic Fixture — not the real epoch" banner text present (case-insensitive match); Freeze/Integrity expanded, page text contains "Family Denominator" table heading | PASS | `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-07-result.png` |
| UT-08 | Cockpit and Structure pages still load | regression | P1 | Both pages render normal content, no blank screen, no error banner | `/` (Cockpit) loaded: nav, ticker watch form, "Try: SIM-BUYER" placeholder content all present, no error banner. `/structure` loaded: "Structure" heading, Symbol/As-of form, Tradable Map / Case Studies / Edge Report panels all present with honest empty states ("Choose a symbol...", "Edge report not computed yet." — expected, not errors) | PASS | `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-08-result.png` |
| UT-09 | Epoch / Manifest discoverable in 2 clicks | ux | P3 | Five row headers read, top to bottom: Sources / Compiler, Interpreter Fixtures, Freeze / Integrity, Hermetic Oracles, Epoch / Manifest | Confirmed via the UT-01 DOM extraction: the collapsed row-header order under Hypothesis Foundry reads exactly "SOURCES / COMPILER", "INTERPRETER FIXTURES", "FREEZE / INTEGRITY", "HERMETIC ORACLES", "EPOCH / MANIFEST" top to bottom — Epoch/Manifest is the last row, 2 clicks from `/desk` | PASS | `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-01-result.png` (same expand state; no separate screenshot needed) |

---

## Passed Tests

### UT-01 — `/desk` loads and the Hypothesis Foundry section is reachable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-01-result.png`
- Navigated to `/desk`, located the "HYPOTHESIS FOUNDRY" section header, clicked `[data-testid="desk-section-expand-hypothesisFoundry"]`. Panel expanded showing the era-boundary header, Era-Open Baseline block, and the five nested row headers. No blank screen or error message.

### UT-02 — Operator can open Epoch / Manifest and see the real committed epoch
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-02-result.png`
- Clicked the "Epoch / Manifest" row header. Banner reads "Real Epoch — not a fixture" with a visibly green/emerald border and text (screenshot-confirmed, distinct from the amber banners elsewhere on the panel). Status line, all six identity hashes, `outcome_access_census: 0`, 11-row source-disposition list, the honest "Compiled families (0)" empty state, and the "(committed)" audit-report reference all verified verbatim against the test plan's exact expected strings.

### UT-03 — Sources / Compiler shows both alias-family siblings and the three additive fields
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-03-result.png`
- Clicked "Sources / Compiler". Counted exactly 8 `<li>` rows in the fixture list (previously 7 per the surface map's noted row-count change). `fixture-variant-a` and `fixture-variant-b` both appear as independent rows, each naming the other under "Alternatives:". Every row shows "Operative formula refs:", "Superseded fields:", and "Aliases/lineage ids:"; the two spot-checked exact strings (`fixture-unsupported-stat` → "(none)", `fixture-alias-older` → the supersession string) matched byte-for-byte.

### UT-04 — Hermetic Oracles shows the kill-type mapping and best-of-N disclosure
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-04-result.png`
- Clicked "Hermetic Oracles". `kill_type_mapping` list shows exactly 7 rows including the two spot-checked ones; `best_of_n_disclosure` line shows a real numeric `threshold_bps` value (not "—"/blank). All five named oracle checks still show PASS, confirming no regression from the backend's `outcome_types_present` and reassignment-removal changes.

### UT-05 — Epoch / Manifest empty-families state renders honestly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-05-result.png`
- With Epoch / Manifest expanded, the "Compiled families (0)" heading is immediately followed by visible plain-colored body text ("Zero compiled candidates this epoch — every required source disposed non-COMPILED."), not a spinner or blank area. A scripted full-page scan for reddish/rose leaf-text nodes returned zero matches, confirming no error styling anywhere on the page.

### UT-06 — Foundry panel shows an honest unavailable state if the API call fails
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-06-result.png`
- The Chrome MCP tool in this environment exposes no dedicated network-blocking action (confirmed via its `help` listing), so the block was implemented client-side by overriding `window.fetch` (and `XMLHttpRequest`) to reject any request matching `/research/desk/micro/foundry` before triggering the panel's first deferred GET — the test plan explicitly allows "an equivalent network-interception call." After the override, expanding "Hypothesis Foundry" produced `[data-testid="foundry-panel-unavailable"]` with the text "Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place." — readable prose, not a raw stack trace. A subsequent fresh page navigation (which discards the injected override, standing in for "removing the network block") followed by re-expanding the section showed the panel back to its normal UT-02 state ("Era-Open Baseline" text present again).

### UT-07 — Prior-iteration Foundry subsections (J-01, J-03, J-04) still render correctly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-07-result.png`
- Panel header's "Source registry hash:" line reads a real hex value (`ed40dbc25e8f...`), confirmed NOT the literal `not_yet_generated`. Interpreter Fixtures subsection expands with the amber fixture banner and a non-empty `foundry-interpreter-scenario-rows` list (5 rows). Freeze / Integrity subsection expands with the amber banner and a populated "Family Denominator" table.

### UT-08 — Cockpit and Structure pages still load
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-08-result.png`
- `/` (Cockpit) and `/structure` both render their normal content with no blank screen and no error banner, confirming this iteration's Foundry-only backend/frontend changes did not regress the rest of the app.

### UT-09 — Epoch / Manifest is discoverable one click below Hermetic Oracles
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-5-evidence/UT-01-result.png` (same DOM state captured for UT-01)
- With Hypothesis Foundry expanded and no subsection opened, the five row headers read top to bottom exactly: "SOURCES / COMPILER", "INTERPRETER FIXTURES", "FREEZE / INTEGRITY", "HERMETIC ORACLES", "EPOCH / MANIFEST" — matching the required order, with Epoch / Manifest reachable in exactly 2 clicks from `/desk`.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Notes on tooling / methodology

- **Console-error checking:** the Chrome MCP tool's console-log capture in this environment returns `# TODO: Console logging not yet implemented` for every action's auto-captured `-console.txt` file, and `get_console_messages` returns no messages even after `enable_console_logging`. Console-error assertions in the test plan (UT-01, UT-07) could therefore not be verified through the console API; absence of visible error banners/broken rendering in the DOM and screenshots was used as the practical signal instead. This is a tooling limitation, not a product finding, and is reported here for transparency rather than silently claimed as "zero console errors."
- **Intermittent blank screenshots:** as flagged in the dispatch note, `screenshot` (viewport-only, no `fullpage`) returned a blank dark image twice during this run (first attempts at UT-05 and UT-06). Both were corroborated by DOM/`extract` text (and, for UT-06, an `await_element` confirming the target testid rendered) before the acceptance state was scored, then successfully re-captured with `fullpage: true`, which produced valid non-blank images used as the final evidence.
- **UT-06 network blocking:** the MCP tool exposes no first-class request-blocking/interception action (verified via its `help` output — only navigate/click/type/eval/etc.). A `window.fetch`/`XMLHttpRequest` override injected via `eval` was used as the test plan's permitted "equivalent network-interception call."

## Golden replay scripts written this run

- `runs/goal-session-hypothesis-foundry/journey-scripts/J-06.json` — new script for J-06 (Epoch / Manifest), lint-checked clean via `demo_runner.py --mode lint`.
- `J-02.json` and `J-05.json` already existed in that directory from a prior iteration and were verified still valid against this iteration's live DOM (their asserted strings — "Hashes match — outcome-blind compilation proven." and "Protected-data trip fails closed / evidence class immutable" — are both still present and unchanged) and re-linted clean; left unmodified.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Headless Chrome via MCP (CDP endpoint 127.0.0.1:9222, pre-launched by the pump; not self-launched)
- **Test Date:** 2026-08-27
- **Evidence directory:** `reports/qa/goal-hypothesis-foundry-iter-5-evidence/`
