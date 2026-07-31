# Phase goal-desk-iter-34 — UI Test Results

**Phase:** goal-desk-iter-34
**Date:** 2026-07-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` Top-up Runs panel loads | smoke | P1 | Page renders, table with 5 named columns visible, latest-run detail heading visible, no console errors | Page rendered; `desk-topup-runs-table` had headers exactly `date, run, state, attempted / total, universe snapshot`; `desk-topup-run-latest-detail` heading "Latest run — 2026-07-31 · topup-2026-07-31-8fb5c9a1f737" visible; console showed only the React DevTools info line | PASS | `reports/qa/goal-desk-iter-34-evidence/UT-01-result.png` |
| UT-02 | Reach line and earlier list never share a day | happy-path | P1 | No earlier-row's printed date equals the newest-reach day; ambient run rows all print `2026-07-27` | Reach line read "newest recorded reach 2026-07-30 · 303 pairs reach it"; all 20 rendered earlier rows printed `2026-07-27`; a DOM check (`innerText.indexOf('2026-07-30')` over every earlier row) confirmed 0 matches | PASS | `reports/qa/goal-desk-iter-34-evidence/UT-02-result.png` |
| UT-03 | Cap disclosure shows "showing 20 of N" | happy-path | P1 | "showing 20 of 101" visible below the "Pairs recorded earlier (101)" heading; exactly 20 rows rendered | Heading read "Pairs recorded earlier (101)"; disclosure paragraph read exactly "showing 20 of 101"; `querySelectorAll` over `desk-topup-run-latest-reach-earlier-row` returned exactly 20 elements | PASS | `reports/qa/goal-desk-iter-34-evidence/UT-03-result.png` |
| UT-04 | No disclosure when true total ≤ 20 | validation | P2 | Live branch not exercisable on ambient run (true total 101 > 20, documented environment limitation); fallback pytest tests pass | Ran `pytest tests/test_desk_topup_library_reach_guard.py -k cap -v` — 4 passed, including `test_topup_library_reach_caps_the_earlier_list_and_preserves_the_true_total` and its render-wiring/seeded-violation counterparts | PASS (fallback) | none (no live screenshot possible — see note below) |
| UT-05 | Legacy run still shows honest fallback text | error | P2 | No qualifying legacy run on ambient store (documented environment limitation); fallback pytest test passes | Ran `pytest tests/test_desk_topup_library_reach_guard.py -k lacks_store_frozen_through_after -v` — 1 passed (`test_topup_library_reach_returns_null_when_any_outcome_lacks_store_frozen_through_after`) | PASS (fallback) | none (no live screenshot possible — see note below) |
| UT-06 | Summary table + adjacent pages unaffected | regression | P1 | Top-up Runs table keeps exactly its 5 original columns; Cockpit and Structure pages load without errors | Confirmed table headers unchanged (`date, run, state, attempted / total, universe snapshot`); navigated to `/` (Cockpit) — loaded, no console errors; navigated to `/structure` — "Structure" heading rendered, no console errors | PASS | `reports/qa/goal-desk-iter-34-evidence/UT-06-result.png` |
| UT-07 | Disclosure sentence is plain description | ux | P2 | Sentence contains only "showing" + two numbers, no advice/urgency language; styling matches existing muted fallback text | Sentence text: "showing 20 of 101" (nothing else); `className="mb-1 text-xs text-slate-400"` on the `<p>`, matching the sibling fallback line's `className="text-xs text-slate-400"` — same font size/color, no new badge/icon/color | PASS | `reports/qa/goal-desk-iter-34-evidence/UT-07-result.png` |

---

## Passed Tests

### UT-01 — `/desk` Top-up Runs panel loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-34-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/desk`, page loaded fully (headings: "Desk"). `desk-topup-runs-table` present with header row `date | run | state | attempted / total | universe snapshot`. `desk-topup-run-latest-detail` block present with heading "Latest run — 2026-07-31 · topup-2026-07-31-8fb5c9a1f737". Console messages captured (via `enable_console_logging` + fresh navigate) contained only the React DevTools informational line — no errors.

### UT-02 — Newest-reach line and "Pairs recorded earlier" list never name the same day
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-34-evidence/UT-02-result.png`
- `desk-topup-run-latest-reach` read: `newest recorded reach 2026-07-30 · 303 pairs reach it`. `desk-topup-run-latest-reach-earlier` heading read `Pairs recorded earlier (101)`. All 20 rendered rows (`desk-topup-run-latest-reach-earlier-row`) printed `... — 2026-07-27` (verified both visually in the screenshot and programmatically: `Array.from(rows).map(r=>r.innerText)` all contain `2026-07-27`, zero contain `2026-07-30`). Cross-checked the ground truth independently via `curl http://localhost:8301/research/desk/topup/runs` and a standalone day-grouping computation over all 404 raw outcomes: newest day `2026-07-30` (303 pairs), earlier day `2026-07-27` (101 pairs) — matches the rendered page exactly, confirming the day-precision grouping fix is live and correct, not a coincidence of the sample shown.

### UT-03 — Honest cap disclosure appears when more than 20 pairs are earlier
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-34-evidence/UT-03-result.png`
- Heading `Pairs recorded earlier (101)` (M=101 > 20). Disclosure paragraph `desk-topup-run-latest-reach-earlier-cap` present, text exactly `showing 20 of 101`, positioned directly below the heading and above the first row. `document.querySelectorAll('[data-testid="desk-topup-run-latest-reach-earlier-row"]').length === 20` — exactly 20 rows rendered despite the heading's true count of 101.

### UT-04 — No cap-disclosure sentence when the true earlier-pairs total is ≤ 20
**Verdict:** PASS (fallback — live branch not exercisable, per the test plan's own documented environment limitation: ambient run's true total is 101, not ≤ 20)
**Evidence:** none (test-plan-sanctioned fallback path; no screenshot claimed)
- Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_topup_library_reach_guard.py -k cap -v` → `4 passed, 7 deselected`, confirming `test_topup_library_reach_caps_the_earlier_list_and_preserves_the_true_total` and its companion assertions (including the seeded-violation counterpart) all pass — the disclosure is structurally impossible to render when the true total is at or below the 20-row cap.

### UT-05 — Legacy run (no recorded reach data) still shows the honest fallback text
**Verdict:** PASS (fallback — no qualifying legacy run exists on the ambient store, per the test plan's own documented environment limitation)
**Evidence:** none (test-plan-sanctioned fallback path; no screenshot claimed)
- Ran `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_topup_library_reach_guard.py -k lacks_store_frozen_through_after -v` → `1 passed`, confirming `test_topup_library_reach_returns_null_when_any_outcome_lacks_store_frozen_through_after` passes unmodified.

### UT-06 — Top-up Runs summary table and adjacent pages are unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-34-evidence/UT-06-result.png`
- `desk-topup-runs-table` header cells read exactly `["date","run","state","attempted / total","universe snapshot"]` — 5 columns, no new column. Clicked "Cockpit" nav link → `location.href` became `http://localhost:3301/` and the page rendered (Live/Historical/Simulated toggle, watch form) with only the React DevTools info console line. Clicked "Structure" nav link → `location.href` became `http://localhost:3301/structure`, "Structure" heading rendered, no console errors.

### UT-07 — Cap-disclosure sentence reads as plain description, not advice
**Verdict:** PASS
**Evidence:** `reports/qa/goal-desk-iter-34-evidence/UT-07-result.png`
- Sentence text is exactly `showing 20 of 101` — no other words, no "warning"/"should"/"recommend" language. `className` on the `<p>` is `mb-1 text-xs text-slate-400`, matching the sibling `window-basis` fallback line's `text-xs text-slate-400` — same muted font size/color, no new color, icon, or badge introduced.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Additional verification (beyond the test plan)

- **Backend regression guard suite:** `pytest tests/test_desk_topup_library_reach_guard.py -v` → **11 passed** (day-truncation assertion + seeded-violation counterpart, cap assertion + seeded-violation counterpart, render-wiring, and the pre-existing legacy-run tests) — matches DEFINITION OF DONE.
- **Copy/UI guard suites (unmodified):** `pytest tests/test_copy_discipline.py tests/test_desk_ui_guards.py tests/test_desk_hover_tooltip_guard.py -v` → **47 passed**, 0 failures.
- **J-19 golden replay script:** `runs/goal-session-desk/journey-scripts/J-19.json` (already repointed by the developer this iteration) was checked against the live page and matches: step 2 (`reach it` substring) and step 3 (`Pairs recorded earlier` substring) and step 4/5 (existence-only checks on `desk-topup-run-latest-reach-earlier-row` / `-cap`) all verified true against the current ambient DOM. Linted clean: `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-desk/journey-scripts --journeys J-19` → `J-19 ok`. No changes needed; left as-is (it no longer pins the bug's contradictory row text or any drifting date/count, matching the DEFINITION OF DONE).
- **Required-still-passing journeys (J-04, J-07, J-09, J-16, J-17):** per the dispatch instructions, these were already re-verified by deterministic golden-script replay before this run and were NOT re-tested here (no rows emitted for them, per instructions).

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (headless, CDP 127.0.0.1:9222)
- **Test Date:** 2026-07-31
- **Evidence directory:** `reports/qa/goal-desk-iter-34-evidence/`
- **Ambient top-up run under test:** `topup-2026-07-31-8fb5c9a1f737` (404/404 pairs, state `done`), independently confirmed via `GET /research/desk/topup/runs`: newest day `2026-07-30` (303 pairs), earlier day `2026-07-27` (101 pairs) — exactly the inverse split of the bug this iteration fixes.
