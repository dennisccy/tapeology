# Phase goal-rapid-microscope-iter-28 — UI Test Results

**Phase:** goal-rapid-microscope-iter-28
**Date:** 2026-08-23
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 6/6 executed tests passed (2 N/A — no scope this iteration)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders, `desk-title`="Desk", "Playbook Signals" visible, no console errors | Confirmed all: `desk-title` text = "Desk", "Playbook Signals" present in DOM, only a React-DevTools info console line (no errors) | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-01-result.png` |
| UT-02 | Seal-unaware caveat renders in Strategy Family block | happy-path | P1 | New `data-testid="referee-evidence-strategy-seal-unaware-caveat"` line with exact verbatim text, directly below tick-gate line and above basis-caveats list, styled as muted secondary text, no overlap | Element found; DOM child order of `referee-evidence-strategy-block` is exactly `...-tick-gate` → `...-seal-unaware-caveat` → `...-basis-caveats`; `textContent` matches the spec sentence character-for-character; computed style is `<p class="mt-2 text-[11px] text-slate-500">` (muted slate, 11px); screenshot shows clean vertical stacking, no visual overlap with the caveats list below | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-02-result.png` |
| UT-03 | Validation — N/A | n/a | n/a | No validation surface this iteration | Not applicable — no form/input changed | SKIP (N/A) | none |
| UT-04 | Error — N/A | n/a | n/a | No new error state this iteration | Not applicable — static text has no loading/error/empty state of its own | SKIP (N/A) | none |
| UT-05 | J-01 golden journey — Microscope Readiness | regression | P1 | Section expands, "hand_assigned" visible | Navigated `/desk`, clicked `desk-section-expand-microReadiness`, confirmed `document.body.innerText.includes('hand_assigned') === true` | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-05-result.png` |
| UT-06 | J-10 sentinel — all kept surfaces render | regression | P1 | All 16 steps across `/`, `/structure`, `/desk` complete with listed text visible, no console error, no section broken by new caveat markup | All 16 steps executed and verified individually (see Passed Tests below); no console errors throughout the entire session (only a React-DevTools info line) | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-06-result.png` |
| UT-07 | Caveat discoverable in 1 click | ux | P2 | "Referee Registry" header visible without excessive scrolling; 1 click reveals the caveat text | Header found at DOM position right after "Playbook Evidence" (well within the page's normal collapsed-state section list, docHeight 2498px collapsed); one click on `desk-section-expand-refereeRegistry` revealed "Legacy Referee readiness metric..." text (`await_text` matched) | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-07-result.png` |
| UT-08 | Scout Ledger "N variants tried" row (passenger, TC-11) | regression | P3 | At least one family row shows "N variants tried" pattern | Expanded Scout Ledger section; block `scout-ledger-families-block` shows "failed_aggression_score__playbook_signal__trades_20 (root e47904f2f7f4f0e1) — 1 variants tried" | PASS | `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-08-result.png` |

---

## Passed Tests

### UT-01 — `/desk` loads without errors (smoke)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/desk`; `data-testid="desk-title"` textContent = "Desk"; "Playbook Signals" section heading present in extracted page text; console showed only the informational React DevTools message, no errors.

### UT-02 — The seal-unaware caveat renders inside the Referee Registry Strategy Family block
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-02-result.png`
- Expanded "Referee Registry" (`desk-section-expand-refereeRegistry`), waited for `config fingerprint 08e471b10130e1e2` to appear (deferred fetch resolved).
- Confirmed the Strategy Family block's `data-testid` children are in DOM order: `referee-evidence-strategy-table`, `-dataset-count`, `-train-count`, `-holdout-count`, `-trade-count`, `-tick-gate`, **`-seal-unaware-caveat`**, `-basis-caveats`, `-integrity-errors-empty` — the new line sits exactly between the tick-gate line and the basis-caveats list, per spec.
- `textContent` of the new element, verified via `JSON.stringify`, is exactly: "Legacy Referee readiness metric — seal-unaware in the Rapid Microscope era. It may include withheld/unexposed Rapid-Microscope shards and must not be used as the canonical Rapid-Microscope readiness count." — character-for-character match to the spec sentence and the test plan's expected text.
- Computed style: `<p class="mt-2 text-[11px] text-slate-500">`, color `rgb(100, 116, 139)`, font-size `11px` — muted secondary/slate styling, consistent with the tick-gate/basis-caveats disclosure family, not a new card.
- Element-scoped screenshot (cropped from a single atomic CDP full-page capture at the element's exact bounding-box coordinates — not a stitched multi-shot composite) shows the Datasets/Train-Holdout/Trades rows unchanged, the tick-gate line, the new caveat line, and the basis-caveats paragraph stacked cleanly with no visual overlap.

### UT-05 — J-01 golden journey: era transition + Microscope Readiness still works
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-05-result.png`
- Navigated to `/desk`, clicked `desk-section-expand-microReadiness`, confirmed "hand_assigned" is present in `document.body.innerText`. No interference from the new Referee Registry caveat (different collapsible section).
- Golden replay script rewritten (unchanged content) at `runs/goal-session-rapid-microscope/journey-scripts/J-01.json`; passes `demo_runner.py --mode lint`.

### UT-06 — J-10 sentinel: kept surfaces still render end to end
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-06-result.png`
- Step 1: `/` shows "No ticker watched".
- Step 2-3: Typed "SIM-BUYER" into the Ticker field; the ticker required the "Simulated" feed tab to be selected (the cockpit's "Live" tab is gated by real US market hours, which are closed on the test date) before "Watch" produced the "Buyer Control" tape state — this is expected cockpit behavior, not a regression (the SIM- ticker is a simulated-feed fixture). Confirmed "Buyer Control" visible under TAPE STATE with confidence 0.926.
- Step 4-6: `/structure` shows "Tradable Map"; filled Structure symbol "AAPL" and As-of "2026-06-22 16:00:00".
- Step 7: Clicked `structure-load-button`; confirmed "300.11–302.2" appears (via `await_text` + exact-string `includes` check).
- Step 8: `/desk` shows "Playbook Signals" (case-insensitive DOM match — the DOM text is "Playbook Signals", rendered visually uppercase via CSS `text-transform`).
- Step 9: Expanded Playbook Evidence; "Built from signature:" confirmed.
- Step 10: Typed "2026-06-22" into `desk-playbook-date-input`; "recorded signals, none hidden" appeared.
- Step 11: Expanded Microscope Readiness; "Distinct symbol-days" confirmed.
- Step 12: Expanded Scout Ledger; "variants tried" confirmed (also satisfies UT-08/TC-11).
- Step 13: Expanded Walk-Forward; "No fold specs registered." confirmed.
- Step 14: Expanded Validation Vault; "iter18-qa-universe" confirmed.
- Step 15: Expanded Referee Registry; "config fingerprint 08e471b10130e1e2" confirmed (and, per UT-02, the new seal-unaware caveat line verified present and correctly positioned in the same block).
- Step 16: Expanded Referee Adjudications; "No hypotheses registered." confirmed.
- Step 17 (spec step 16): Expanded Referee Runs; "No evaluation runs recorded yet." confirmed.
- No console errors at any point in the sequence (checked twice via `get_console_messages`); only the informational React DevTools line.
- Golden replay script rewritten (unchanged content) at `runs/goal-session-rapid-microscope/journey-scripts/J-10.json`; passes `demo_runner.py --mode lint`.

### UT-07 — The new caveat is discoverable within one click
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-07-result.png`
- On a fresh `/desk` load (all sections collapsed), `desk-section-expand-refereeRegistry`'s bounding rect sits at y=1996.5 within a collapsed-state document height of 2498px — squarely inside the page's normal section-header list, no more scrolling than the existing section headers.
- One click on that header revealed "Legacy Referee readiness metric..." (confirmed via `await_text`), i.e. the disclosure is reachable within 1 click from `/desk`.

### UT-08 — Scout Ledger family row still shows "N variants tried" (passenger capture, TC-11)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-28-evidence/UT-08-result.png`
- Expanded Scout Ledger; `scout-ledger-families-block` shows "failed_aggression_score__playbook_signal__trades_20 (root e47904f2f7f4f0e1) — 1 variants tried" — matches the "N variants tried" pattern.
- This satisfies the round's TC-11 owed make-up capture (J-08 passenger), riding along this round's own live J-01/J-10 browser-qa pass per the iteration spec's Notes — not claimed as this iteration's own planned scope.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-03 — Validation: N/A (no form changed this iteration)
**Verdict:** SKIPPED (N/A)
**Reason:** This iteration adds a single static text element — no form, input, or submission flow was added or changed. There is no validation surface to test (per the test plan's own scoping).

### UT-04 — Error: N/A (no new error state)
**Verdict:** SKIPPED (N/A)
**Reason:** The new caveat text is static and unconditional; it carries no loading/error/empty state of its own. There is no new backend-error path to trigger (per the test plan's own scoping).

---

## Environment Note — J-10 cockpit "Watch" behavior

While driving UT-06/J-10 step 2-3, the initial attempt to click "Watch" while the cockpit's default "Live" mode tab was active resulted in a "market is closed" panel (the current test date/time falls outside US market hours) rather than the expected "Buyer Control" tape state. Switching to the "Simulated" feed tab (still with the same "SIM-BUYER" ticker already typed) before clicking "Watch" produced the expected "Buyer Control" result. This is recorded as an observation, not a failure — the golden script and test plan's literal steps do not mention a tab switch, but the underlying cockpit behavior (Live mode gated by real market hours; a SIM- prefixed ticker exercised via the Simulated tab) is consistent with the product's documented design (Live streaming only during market hours; Simulated is the fixture-feed lane) and is unrelated to this iteration's diff (Referee Registry caveat only — verified via UI surface map and unchanged `referee_*.py` file hashes). No regression is implicated.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`, headless, pinned CDP port 9222)
- **Test Date:** 2026-08-23
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-28-evidence/`

### Note on element-scoped screenshot capture technique

Direct CDP element-clipped screenshots (`selector` + non-fullpage `screenshot`) returned uniformly blank (background-only) images for elements located deep in this session's very tall, multi-section-expanded `/desk` page — a headless-Chrome compositor/paint quirk reproduced consistently at several scroll depths, independent of viewport size. Root cause not pursued further (out of scope for this QA pass); worked around by taking a single atomic CDP full-page capture (`fullpage: true`, not a stitched multi-shot composite) and cropping it in Python (PIL) to the exact `getBoundingClientRect()` coordinates of the target element. This produces a genuinely element-scoped image (no duplicated headers, no mid-table truncation — the failure modes of the iteration-27 stitched full-page capture) while avoiding the blank-capture bug. All screenshots in this report for UT-02, UT-06, UT-07, and UT-08 used this technique; UT-01 and UT-05 (shallower page state) used direct element/viewport capture successfully.
