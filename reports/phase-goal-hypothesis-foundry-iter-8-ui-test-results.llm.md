# Phase goal-hypothesis-foundry-iter-8 — UI Test Results

**Phase:** goal-hypothesis-foundry-iter-8
**Date:** 2026-08-27
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 6/6 tests passed (0 skipped)

---

## Precondition verification (done myself, before testing)

- `curl -s -o /dev/null -w "%{http_code}" http://localhost:3301/desk` → `200`
- `curl -s http://localhost:8301/health` → `{"status":"ok"}`
- `curl -s http://127.0.0.1:9222/json/version` → responded (Chrome/151.0.7922.71, CDP reachable)
- Attached to the existing CDP endpoint on `:9222` per the operational note; did not launch a new browser.
- No service died during this run; no restart was needed.
- Confirmed `GET http://localhost:8301/research/desk/micro/foundry` returns HTTP 200 with a non-null
  `final_summary` key (precondition for UT-02) before running any browser steps.

## Known environment artifact encountered (as warned in the dispatch)

Deep-scroll Chrome-MCP screenshots of the Foundry subsections **did** come back blank in this run,
exactly as flagged. Concretely:
- `UT-01` acceptance state (Final Summary expanded, ~2480px down the page): Chrome-MCP `screenshot`
  action produced a uniform blank PNG (`grayscale extrema = (14, 14)`, i.e. one solid color, checked
  with PIL).
- A probe of the `UT-05` acceptance state (Runner/Checkpoint, ~7629px down the page) was also a
  uniform blank PNG (`extrema = (14, 14)`).
- A probe at `scrollY=0` (page top, no scroll) came back with real content (`extrema = (3, 255)`),
  confirming the artifact is specifically scroll-depth-triggered, not a general browser fault.
- Per the dispatch note, every DOM assertion below was corroborated with real `eval`/`get_text`
  reads of the live page (not screenshots), and screenshots for any acceptance state below the fold
  were captured via `python3 scripts/automation/lib/demo_runner.py --mode verify` (Playwright,
  headless, viewport 1280×800) instead of the Chrome-MCP deep-scroll path. Those replayed scripts
  are also this iteration's golden-replay deliverables (see below). `UT-04`'s acceptance state sits
  high enough on the page (no scroll needed after a fresh page load) that its Chrome-MCP screenshot
  came back with real content (`extrema = (14, 230)`) and was kept as-is.
- No verdict below was silently passed or failed on a blank image — every blank case is called out
  explicitly here and was replaced with a corroborated `demo_runner --mode verify` screenshot.

## Golden replay script (J-08)

Wrote `runs/goal-session-hypothesis-foundry/journey-scripts/J-08.json` (4 steps: load `/desk` →
expand Hypothesis Foundry → expand Final Summary → expand the first source's Canonical provenance
`<details>`, asserting `"Zero diagnostic survivors exist for this epoch"` and
`"high aggression-into-the-wall"` as real post-load data values). Linted clean
(`demo_runner --mode lint`) and replayed clean (`demo_runner --mode verify`, rc=0, PASS, screenshot
`reports/qa/goal-hypothesis-foundry-iter-8-evidence/J-08-verify.png`).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Panel + Final Summary load without errors | smoke | P1 | Page renders without error; `foundry-era-open-baseline` visible after expanding Hypothesis Foundry; `foundry-final-summary` visible after expanding Final Summary, positioned above Sources/Compiler in the DOM; no console errors | All held: `foundry-era-open-baseline` found via `await_element`; `foundry-final-summary` found via `await_element`; `compareDocumentPosition` check returned `fsBeforeSc:true` (Final Summary precedes Sources/Compiler in DOM order); console log only carried an info-level React DevTools message, zero errors | PASS | `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-01-result.png` (via demo_runner verify; raw Chrome-MCP screenshot at this state was blank, see note above) |
| UT-02 | Full Final Summary + source drill-in read | happy-path | P1 | Disposition counts sum to 11 exactly as listed; Family/Variant/Frozen-ready/Evidence-class/Protected-reads/Freeze-integrity/Epoch-status lines render verbatim; zero-survivor and exhaust-complete sentences render as full sentences; pilot-study-1 row's Canonical provenance expands showing Mechanism/Audit note/Direction/Comparator/Threshold/Superseded/Alternatives/Source hash/quoted spans | `innerText` dump of `[data-testid="foundry-final-summary"]` matched every expected value exactly: `ALIASED_PROXY_ONLY: 2, BLOCKED_DIRECTION: 4, BLOCKED_SPEC_GAP: 1, ALIASED_VARIANT_VOCABULARY: 1, EXCLUDED_PREVIOUSLY_KILLED: 1, EXCLUDED_PREREQUISITE_UNMET: 1, EXCLUDED_GATE_CLOSED: 1` (sum 11); `Family count: 0`, `Variant count: 0`, `Frozen-ready total: 0`, `Evidence class: historical_exposed_diagnostic`, `Protected/withheld/sealed reads: 0`, `Freeze integrity: green`, `Epoch status: committed`; zero-survivor sentence and exhaust-complete sentence both rendered as full sentences (not bare "0"); expanding the first (`pilot-study-1-range-wall-failed-aggression`) row's Canonical provenance showed Mechanism, Audit note, `Direction derivation: BLOCKED_DIRECTION`, `Comparator derivation: complement_within_same_eligible_population`, `Threshold provenance: literal_ratified_threshold`, `Superseded fields: {}`, `Alternatives: (none)`, `Source hash: f6f6051eeaa9ddc8c0ac9a2581787b3a0361b7b6e91e785a0def8fd2ecb3aed2` (64-char hex), and all 3 `quoted_spans` entries as `"text" @ location` (`@ 0`, `@ 732`, `@ 816`) — cross-checked field-by-field against both `curl .../research/desk/micro/foundry` and `docs/hypothesis-foundry/source-registry.json`; byte-for-byte match (TC-5) | PASS | `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-02-result.png` (= J-08 golden replay screenshot, same DOM/API acceptance state; via demo_runner verify) |
| UT-03 | Missing optional field renders `(none)`, not blank | validation | P2 | For a real source record with `threshold_provenance: null` (verified `card-9.4-burst-climax-detection` against `source-registry.json`), the expanded detail shows `Threshold provenance: (none)`, and `Alternatives:`/`Superseded fields:` show `(none)`/`{}` rather than blank | Expanded `card-9.4-burst-climax-detection`'s Canonical provenance directly via Chrome-MCP eval: `Threshold provenance: (none)`, `Superseded fields: {}`, `Alternatives: (none)` — none blank, none the literal string `null`; confirmed underlying `source-registry.json` record has `threshold_provenance: None`, `alternatives: []`, `superseded_fields: {}`; independently re-confirmed via a scoped demo_runner replay (`li:has-text("card-9.4-burst-climax-detection") summary` → expect `"Threshold provenance: (none)"`, PASS) | PASS | `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-03-result.png` (via demo_runner verify) |
| UT-04 | Backend unreachable degrades honestly | error | P2 | Panel does not crash or blank; `foundry-panel-unavailable` shows an explicit error message; no `foundry-final-summary` renders (no fabricated/zeroed values) | Simulated a network failure by patching `window.fetch` (via `eval`) to reject any request to `/research/desk/micro/foundry` before expanding the panel (the Chrome-MCP tool has no native request-blocking action, so `fetch` interception was used as the equivalent of DevTools request-blocking called for in the plan). `foundry-panel-unavailable` appeared with text `"Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place."`; `foundry-final-summary` absent (`finalSummaryPresent:false`); page body still had 32,118 chars of text (not a blank/crashed page); console carried only the info-level React DevTools message | PASS | `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-04-result.png` (raw Chrome-MCP screenshot; this state needed no deep scroll and was NOT blank, `extrema=(14,230)`) |
| UT-05 | Six pre-existing Foundry subsections still render correctly | regression | P1 | Sources/Compiler, Interpreter Fixtures, Freeze/Integrity, Hermetic Oracles, Epoch/Manifest, Runner/Checkpoint all expand with no console errors; all 11 source-disposition rows still render in Epoch/Manifest; Runner/Checkpoint's freeze-integrity verdict and exhaust-completion state match what Final Summary shows | Clicked all six section headers in order; all expanded successfully (verified via a scoped demo_runner replay asserting each section's own root testid became visible: `foundry-sources-compiler`, `foundry-interpreter-fixtures`, `foundry-freeze-integrity`, `foundry-hermetic-oracles`, `foundry-epoch-source-disposition-rows`, `foundry-runner-freeze-integrity-verdict` — all PASS). Directly via Chrome-MCP eval: `foundry-epoch-source-disposition-rows` still lists all 11 `source_id — DISPOSITION` rows unchanged; `foundry-runner-freeze-integrity-verdict` reads `"Freeze integrity: green"` and `foundry-runner-exhaust-complete` reads `"Exhaust complete — every frozen candidate reached a terminal state (zero FROZEN_READY variants this epoch — an honest, vacuous completion)."` — both consistent with Final Summary's `freeze_integrity_verdict: "green"` / `exhaust_complete: true`; console carried only the info-level React DevTools message | PASS | `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-05-result.png` (via demo_runner verify; raw Chrome-MCP screenshot at this state was blank, see note above) |
| UT-06 | Final Summary discoverable within a few clicks from home | ux | P2 | "Desk" nav link visible and navigates to `/desk`; Hypothesis Foundry header visible and clearly labeled; Final Summary is the first subsection to expand, appearing before Sources/Compiler | Verified via a demo_runner replay from `/` (Cockpit): `app-nav` present at page load; clicking the "Desk" role=link navigated to `/desk` (confirmed by `"Hypothesis Foundry"` text appearing); expanding Hypothesis Foundry then Final Summary succeeded with `"Source counts by disposition"` rendering — matching the DOM-order check already done in UT-01 that Final Summary precedes Sources/Compiler, so no older subsection needs expanding first | PASS | `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-06-result.png` (via demo_runner verify) |

---

## Passed Tests

### UT-01 — Panel + Final Summary load without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-01-result.png`
- `/desk` loaded; expanding "Hypothesis Foundry" revealed `foundry-era-open-baseline`; expanding
  "Final Summary" revealed `foundry-final-summary`, confirmed via DOM `compareDocumentPosition` to sit
  before the Sources/Compiler section header. Zero console errors.

### UT-02 — Full Final Summary + source drill-in read
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-02-result.png`
- Every `final_summary` field rendered verbatim and matched the served
  `GET /research/desk/micro/foundry` JSON exactly. The `pilot-study-1-range-wall-failed-aggression`
  detail drill-in rendered its full §1.4 provenance, matching `source-registry.json` byte-for-byte
  (mechanism statement, audit note, direction/comparator derivation, threshold provenance, superseded
  fields, alternatives, 64-char source hash, all 3 quoted spans with locations).

### UT-03 — Missing optional field renders `(none)`, not blank
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-03-result.png`
- `card-9.4-burst-climax-detection` (real `threshold_provenance: null` record, confirmed against
  `source-registry.json`) rendered `Threshold provenance: (none)`, `Superseded fields: {}`,
  `Alternatives: (none)` — no blank field, no literal `null`.

### UT-04 — Backend unreachable degrades honestly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-04-result.png`
- With `/research/desk/micro/foundry` fetches forced to reject, the panel showed
  `foundry-panel-unavailable`: "Backend unreachable — is the API running? Nothing cached and nothing
  fabricated is shown in its place." No `foundry-final-summary` rendered; page did not crash or blank.

### UT-05 — Six pre-existing Foundry subsections still render correctly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-05-result.png`
- All six pre-existing subsections expanded cleanly; the 11 source-disposition rows in Epoch/Manifest
  are unchanged; Runner/Checkpoint's freeze-integrity verdict ("green") and exhaust-completion text
  are consistent with the new Final Summary's own values (same backend-owned fields, not independently
  recomputed).

### UT-06 — Final Summary discoverable within a few clicks from home
**Verdict:** PASS
**Evidence:** `reports/qa/goal-hypothesis-foundry-iter-8-evidence/UT-06-result.png`
- From `/`, the "Desk" nav link led to `/desk`; Hypothesis Foundry expanded cleanly; Final Summary was
  reachable as the very next click, immediately after the era-identity/baseline block, with no need to
  open any of the six older subsections first.

---

## Failed Tests

None.

---

## Skipped Tests

None. (J-01–J-07 were already re-verified by the deterministic golden-replay lane before this dispatch
per the pump's instructions and are intentionally not re-tested or re-reported here — their rows merge
into the final results separately.)

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (CDP `:9222`, existing pinned instance, attached not launched) for
  interactive DOM verification; Chromium via Playwright (`demo_runner.py --mode verify`, headless,
  1280×800) for below-the-fold screenshot evidence, per the environment note in the test plan.
- **Test Date:** 2026-08-27
- **Evidence directory:** `reports/qa/goal-hypothesis-foundry-iter-8-evidence/`
- **Golden replay script written this iteration:** `runs/goal-session-hypothesis-foundry/journey-scripts/J-08.json`
