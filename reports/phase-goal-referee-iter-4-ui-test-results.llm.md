# Phase goal-referee-iter-4 — UI Test Results

**Phase:** goal-referee-iter-4
**Date:** 2026-08-14
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 0/1 tests executed by this agent passed (1 FAIL, P2/non-blocking); 6 P1 tests
(UT-01–UT-06 = journey J-10) were confirmed PASS this iteration via deterministic golden replay
and are intentionally not re-executed or rowed here — see note below.

---

## Goal-mode regression-lane note (read before the table)

Per this run's dispatch instructions: "Deterministic replay has ALREADY re-verified... J-10. Do
NOT re-test them and do NOT emit rows for them — their rows merge into the results automatically
after your run."

`runs/goal-session-referee/journey-scripts/J-10.json` was read and confirmed to contain exactly
the 9 steps that implement **UT-01 through UT-06** (cockpit ticker-watch, structure pinned-AAPL
load, desk Playbook Evidence expand) verbatim, per the test plan's own framing ("UT-01 through
UT-06 collectively implement journey J-10 ... with exact steps taken verbatim from the project's
own stored golden replay script"). Per instruction, **UT-01 through UT-06 were NOT re-executed by
this agent and have no rows in this report** — their J-10 result merges in from the replay
automatically. This agent verified the frontend (`http://localhost:3301`, HTTP 200) and backend
(`http://localhost:8301/health`, HTTP 200) were both reachable before proceeding, and executed
**UT-07 only** — the one test-plan case whose steps go beyond what `J-10.json` checks (5 desk
sections it does not cover) and is explicitly marked supplementary/non-blocking.

No golden replay script was written or modified this run: UT-07 did not fully pass (see below),
and `J-10.json` — already verified via replay — was left completely untouched.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-07 | Remaining Desk reference sections still expand | regression (supplementary) | P2 | All 5 buttons (`topupRuns`, `indexReconciliation`, `screenRuns`, `screenComparison`, `provenance`) reach `aria-expanded="true"`, marker ▸→▾, body renders content/empty-state, no error toast, no permanently-blank panel | 3 of 5 sections (`topupRuns`, `indexReconciliation`, `screenRuns`) expanded correctly with explicit empty-state text and no errors; 2 of 5 (`screenComparison`, `provenance`) do not exist in the current DOM — confirmed pre-existing, data-state-gated (`latest !== null`), unrelated to this iteration's diff | FAIL | `reports/qa/goal-referee-iter-4-evidence/UT-07-fail.png` |

---

## Passed Tests

None executed directly by this agent this run. UT-01–UT-06 (journey J-10, all P1) are already
confirmed PASS via this iteration's deterministic golden replay — see the regression-lane note
above; their rows merge into the final results separately, not from this file.

---

## Failed Tests

### UT-07 — Remaining Desk reference sections still expand (regression, supplementary)
**Verdict:** FAIL
**Priority:** P2 (test plan's own Test Summary marks this "supplementary and non-blocking" —
does not affect the overall Browser QA Verdict, which is governed by P1 tests only)
**Evidence:** `reports/qa/goal-referee-iter-4-evidence/UT-07-fail.png`

**Steps taken (exactly as written in the test plan):**
1. Navigated to `http://localhost:3301/desk` (UT-05's precondition state) — confirmed "Playbook
   Signals" text visible.
2. Clicked `[data-testid="desk-section-expand-topupRuns"]` — succeeded. `aria-expanded` → `"true"`,
   marker ▸→▾, body (`#desk-section-body-topupRuns`) renders "No top-up runs recorded yet."
3. Clicked `[data-testid="desk-section-expand-indexReconciliation"]` — succeeded. `aria-expanded`
   → `"true"`, marker ▸→▾, body renders "No reconciliation run recorded yet."
4. Clicked `[data-testid="desk-section-expand-screenRuns"]` — succeeded. `aria-expanded` →
   `"true"`, marker ▸→▾; body briefly showed a loading skeleton
   (`data-testid="desk-screen-runs-loading"`), then resolved to "No screen runs recorded yet." on
   a follow-up `extract` a few seconds later (normal async fetch, not an error).
5. Clicked `[data-testid="desk-section-expand-screenComparison"]` — **element not found.**
   Recovery attempt 1 (alternative locator `//button[contains(., "Screen Comparison")]`) — also
   not found. Recovery attempt 2 (`extract` full-page text) — confirmed the string "Screen
   Comparison" does not appear anywhere on the rendered page.
6. Clicked `[data-testid="desk-section-expand-provenance"]` — **element not found** (same
   full-page-text extract from step 5 also confirmed "Provenance" does not appear anywhere on the
   page).

**Root cause (confirmed via source inspection, not speculation):**
`apps/frontend/app/desk/page.tsx` gates BOTH the "Screen Comparison" section (`id="screenComparison"`,
~line 9171) and the "Provenance" section (`id="provenance"`, ~line 9191) behind the identical
precondition `{latest !== null && (...)}` — they only mount once a desk screen has actually been
computed/recorded at least once (`DeskProvenance`'s own comment: "Same `latest !== null`
precondition ... as the Screen Comparison section directly above"). The live page text confirms
`latest === null` in the current environment: "Desk screen not computed yet." / "No screen has
been recorded yet for the registered universe." The gating code itself is old — its comment cites
`goal-desk-iter-35 (J-20)`, an unrelated prior era, not this iteration. This iteration's diff
(`referee_stats.py`, `referee_evidence.py`) touches neither `apps/frontend/` (zero frontend files
changed, confirmed by the ui-surface-map) nor any code path that could set `latest`. **This is not
a regression introduced by this iteration** — it is a pre-existing, correct, data-state-dependent
rendering behavior that the test plan's UT-07 did not anticipate (its preconditions only state
"UT-05 passed," not "a desk screen has been computed").

**Expected:** All 5 named sections expand and render content.
**Actual:** 3 of 5 expand and render correct empty-state content with no errors; 2 of 5
(`screenComparison`, `provenance`) are legitimately absent from the DOM in this environment's
current (no-screen-computed) data state.

**Console:** No errors during this test — only a benign React DevTools info message.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (health check: HTTP 200)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), attached to
  the pump-launched isolated headless Chrome on CDP `127.0.0.1:9222` (pinned; not launched or
  killed by this agent)
- **Test Date:** 2026-08-14
- **Evidence directory:** `reports/qa/goal-referee-iter-4-evidence/`
