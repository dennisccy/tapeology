# Phase goal-desk-iter-31 — UI Test Results

**Phase:** goal-desk-iter-31
**Date:** 2026-07-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 6/6 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders with `desk-title`="Desk" heading and a "Screen Runs" panel; no console errors | Page loaded; `desk-title` heading "Desk" visible, "Screen Runs" panel visible with full DOM content; console only showed a benign React DevTools info line, no errors | PASS | `reports/qa/goal-desk-iter-31-evidence/UT-01-result.png` |
| UT-02 | Reused latest run suppresses note/counts | happy-path | P1 | `desk-screen-run-latest-outcome` reads "reused screen-2026-07-31-c169546856c7 — no walk was performed"; no `desk-screen-run-latest-unreached`; no `desk-screen-run-latest-counts`; `desk-screen-run-latest-attempted` reads "0 of 101 members attempted" | Ambient latest run confirmed `screenrun-2026-07-31-fe0829e64a0d` (state done, reused true, members_attempted 0) via API and DOM. `eval` query over the four testids returned exactly: outcome text matches verbatim, `desk-screen-run-latest-unreached` count=0, `desk-screen-run-latest-counts` count=0, attempted text matches verbatim | PASS | `reports/qa/goal-desk-iter-31-evidence/UT-02-result.png` |
| UT-03 | History table retains full append-only record | regression | P1 | At least one row "101 / 101"; at least one row contains "no walk was performed"; table unaffected by the latest-run fix | `desk-screen-runs-table` has 3 rows: `screenrun-2026-07-31-725c4ec2bfcd` "101 / 101" / `screen-2026-07-31-c169546856c7`; two reused rows "0 / 101" / "reused screen-2026-07-31-c169546856c7 — no walk was performed" — all three ambient runs still present, nothing removed | PASS | `reports/qa/goal-desk-iter-31-evidence/UT-03-result.png` |
| UT-04 | Crash-before-any-attempt records null `failed_member` | error | P2 | `pytest -k "test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null or test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member"` → 2 passed | Ran the exact command in `apps/backend`: `2 passed, 35 deselected, 1 warning in 0.38s` | PASS | none (backend-only test, no UI to screenshot) |
| UT-05 | `/desk` discoverable from top nav | ux | P2 | "Desk" nav-link visible in `app-nav`; clicking navigates to `/desk` and becomes active | `app-nav` links = Cockpit(/), Structure(/structure), Desk(/desk). Clicked Desk link → `location.href` = `http://localhost:3301/desk`, link now has `aria-current="page"` and active classes (`bg-slate-800 text-emerald-300`) | PASS | `reports/qa/goal-desk-iter-31-evidence/UT-05-result.png` |
| UT-06 | `done && !reused` counts line byte-unchanged | regression | P3 | Only diff vs. `48c5fc2` is the two added boolean guards; JSX content inside both blocks identical | `git diff 48c5fc2 -- apps/frontend/app/desk/page.tsx` shows exactly two changed lines: `{unreached > 0 && (` → `{unreached > 0 && !(run.state === "done" && run.reused) && (` and `{run.state === "done" && (` → `{run.state === "done" && !run.reused && (`. No other lines differ | PASS | none (code-read verification, no UI to screenshot) |

---

## Passed Tests

### UT-01 — `/desk` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-31-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/desk`. DOM extract confirmed heading "Desk", a "Screen Runs" panel with provenance, briefing table, skipped members, screen history, run-screen/top-up/reconcile index, and the Screen Runs history table all rendered. `get_console_messages` returned only a benign React DevTools info line — no errors.

### UT-02 — Reused latest run suppresses the "not reached" note and the counts line (core fix)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-31-evidence/UT-02-result.png`
- Confirmed via `GET /research/desk/screen/runs` that the ambient store's `latest` run is `screenrun-2026-07-31-fe0829e64a0d` (state `done`, `reused: true`, `members_attempted: 0` of 101, `screen_id: screen-2026-07-31-c169546856c7`) — matches the test plan's precondition exactly, no re-derivation needed.
- Ran an `eval` query over `[data-testid="desk-screen-run-latest-outcome"|"...-unreached"|"...-counts"|"...-attempted"]`:
  - `desk-screen-run-latest-outcome`: 1 element, text = `"reused screen-2026-07-31-c169546856c7 — no walk was performed"` (exact match to expected)
  - `desk-screen-run-latest-unreached`: 0 elements (amber "N members not reached" note absent, as required by the fix)
  - `desk-screen-run-latest-counts`: 0 elements (zeroed-counts line absent, as required by the fix)
  - `desk-screen-run-latest-attempted`: 1 element, text = `"0 of 101 members attempted"` (unaffected element, unchanged as expected)
- This is the exact behavior specified in the phase's IN SCOPE frontend fix and DEFINITION OF DONE / TC-4.

### UT-03 — Screen Runs history table still shows the full append-only record
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-31-evidence/UT-03-result.png`
- `eval` over `desk-screen-runs-table`'s rows returned 3 rows total: `101 / 101` / `screen-2026-07-31-c169546856c7` (the full-walk run), and two `0 / 101` / `"reused screen-2026-07-31-c169546856c7 — no walk was performed"` rows. Both required substrings ("101 / 101" and "no walk was performed") present; nothing removed from the append-only history — confirms the "Latest run" detail fix (UT-02) did not touch the history table.
- This also independently exercises J-18's own golden-replay assertions (see Golden Replay Scripts section below).

## Backend-only test (no browser screenshot applicable)

### UT-04 — Crash-before-any-attempt no longer fabricates a `failed_member`
**Verdict:** PASS
- Command run (repo root, with `TMPDIR`/`TMP`/`TEMP` exported per dispatch instructions):
  `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_screen_compute.py -k "test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null or test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member" -q`
- Result: `2 passed, 35 deselected, 1 warning in 0.38s`. Confirms TC-1 (attempted==0 crash → `failed_member: null`) and the TC-2/TC-6 regression guard (attempted>0 crash → `failed_member = members[attempted]`, unchanged).

### UT-05 — `/desk` is discoverable from the top navigation
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-31-evidence/UT-05-result.png`
- From Cockpit (`/`), `app-nav` contained nav-links Cockpit, Structure, Desk. Clicked the Desk link via CSS selector `[data-testid="app-nav"] a[href="/desk"]`; post-click `location.href` was `http://localhost:3301/desk` and the same link element now carried `aria-current="page"` with active styling classes — unchanged behavior, as expected (this iteration adds no nav entries).

### UT-06 — `done && !reused` counts line stays byte-unchanged
**Verdict:** PASS
- `git diff 48c5fc2 -- apps/frontend/app/desk/page.tsx` shows exactly two `+`/`-` line pairs, both adding a boolean guard clause to existing conditionals (`{unreached > 0 && (` and `{run.state === "done" && (`). All JSX content inside both blocks, and every other line of `LatestScreenRunDetail`, is character-for-character identical to the pre-iteration source.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Golden Replay Scripts

- **J-18** (target journey this iteration): `runs/goal-session-desk/journey-scripts/J-18.json` is explicitly OUT OF SCOPE to re-pin this iteration (already hardened to stable substrings, per the phase spec's Do-not-redo list) and the phase's own DEFINITION OF DONE requires it stay "unchanged." Left unmodified. Verified green via the deterministic runner instead of rewriting it:
  `python3 scripts/automation/lib/demo_runner.py --mode verify --base-url http://localhost:3301 --scripts-dir runs/goal-session-desk/journey-scripts --journeys J-18` → `[demo_runner] verify: 1 journey(s), 0 failed (verdict: PASS)`.
  This, combined with the live UT-02/UT-03 checks above (which directly exercise the same `desk-screen-runs-table` substrings the script asserts, plus the live "Latest run" detail suppression TC-4 requires), satisfies both DEFINITION OF DONE clauses for J-18.
- No other journeys were driven this iteration (J-01, J-02, J-03, J-04, J-06, J-07, J-09, J-10, J-12, J-16 were already re-verified via stored golden scripts per the dispatch note, and this test plan names no other journey), so no other golden script was written or updated.

---

## Notes

- **Screenshot capture quirk (tooling, not product):** viewport screenshots taken at a scrolled position (`window.scrollY > 0`, reached via `eval`-based `scrollTo`, the native `scroll` action, or an element `click`) rendered fully blank/black in this headless Chrome MCP session, even though DOM/`extract`/`eval` confirmed the target element was genuinely laid out inside the viewport bounds at that scroll offset. A `fullpage: true` screenshot (which does not rely on the scrolled-viewport capture path) rendered correctly at every offset, including the exact region containing the Screen Runs table and Latest run detail block. UT-02 and UT-03 evidence screenshots were taken via this fullpage-crop method after the plain scrolled-viewport screenshot came back blank twice (recovery attempts exhausted per the skill's 2-attempt budget before falling back to fullpage). This is a browser-automation capture artifact, not a rendering defect in the app — the `extract`/`eval` DOM checks (the actual PASS/FAIL evidence for both tests) were unaffected and are the primary basis for both verdicts.

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (headless, pinned CDP profile, attached to existing instance on port 9222 per environment note)
- **Test Date:** 2026-07-31
- **Evidence directory:** `reports/qa/goal-desk-iter-31-evidence/`
