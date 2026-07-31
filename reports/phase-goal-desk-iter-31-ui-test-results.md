# UI Test Results (merged)

**Date:** 2026-07-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 16/16 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Universe ingestion — fetched, registered, honest | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-31-evidence/J-01-verify.png |
| UT-J-02 | Coverage + explicit bar top-up over the universe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-31-evidence/J-02-verify.png |
| UT-J-03 | The screen — pinned inputs, append-only snapshot, deterministic rank | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-31-evidence/J-03-verify.png |
| UT-J-04 | The /desk briefing page | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-31-evidence/J-04-verify.png |
| UT-J-06 | MCP contract v3 — 17 read-only tools | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-31-evidence/J-06-verify.png |
| UT-J-07 | The kept product stands — regression sentinel | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-31-evidence/J-07-verify.png |
| UT-J-09 | Every top-up run leaves an append-only record of what it attempted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-31-evidence/J-09-verify.png |
| UT-J-10 | The coverage the briefing shows is the coverage the frozen store can prove | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-31-evidence/J-10-verify.png |
| UT-J-12 | Every recorded screen the ledger lists can be read back — snapshots are addressable by id | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-31-evidence/J-12-verify.png |
| UT-J-16 | The briefing fits the page it is read on — every recorded disclosure legible without a sideways scroll | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-desk-iter-31-evidence/J-16-verify.png |
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders with `desk-title`="Desk" heading and a "Screen Runs" panel; no console errors | Page loaded; `desk-title` heading "Desk" visible, "Screen Runs" panel visible with full DOM content; console only showed a benign React DevTools info line, no errors | PASS | `reports/qa/goal-desk-iter-31-evidence/UT-01-result.png` |
| UT-02 | Reused latest run suppresses note/counts | happy-path | P1 | `desk-screen-run-latest-outcome` reads "reused screen-2026-07-31-c169546856c7 — no walk was performed"; no `desk-screen-run-latest-unreached`; no `desk-screen-run-latest-counts`; `desk-screen-run-latest-attempted` reads "0 of 101 members attempted" | Ambient latest run confirmed `screenrun-2026-07-31-fe0829e64a0d` (state done, reused true, members_attempted 0) via API and DOM. `eval` query over the four testids returned exactly: outcome text matches verbatim, `desk-screen-run-latest-unreached` count=0, `desk-screen-run-latest-counts` count=0, attempted text matches verbatim | PASS | `reports/qa/goal-desk-iter-31-evidence/UT-02-result.png` |
| UT-03 | History table retains full append-only record | regression | P1 | At least one row "101 / 101"; at least one row contains "no walk was performed"; table unaffected by the latest-run fix | `desk-screen-runs-table` has 3 rows: `screenrun-2026-07-31-725c4ec2bfcd` "101 / 101" / `screen-2026-07-31-c169546856c7`; two reused rows "0 / 101" / "reused screen-2026-07-31-c169546856c7 — no walk was performed" — all three ambient runs still present, nothing removed | PASS | `reports/qa/goal-desk-iter-31-evidence/UT-03-result.png` |
| UT-04 | Crash-before-any-attempt records null `failed_member` | error | P2 | `pytest -k "test_tc1_a_crash_before_any_member_is_attempted_records_failed_member_null or test_tc6_a_raising_member_records_state_failed_with_verbatim_error_and_failed_member"` → 2 passed | Ran the exact command in `apps/backend`: `2 passed, 35 deselected, 1 warning in 0.38s` | PASS | none (backend-only test, no UI to screenshot) |
| UT-05 | `/desk` discoverable from top nav | ux | P2 | "Desk" nav-link visible in `app-nav`; clicking navigates to `/desk` and becomes active | `app-nav` links = Cockpit(/), Structure(/structure), Desk(/desk). Clicked Desk link → `location.href` = `http://localhost:3301/desk`, link now has `aria-current="page"` and active classes (`bg-slate-800 text-emerald-300`) | PASS | `reports/qa/goal-desk-iter-31-evidence/UT-05-result.png` |
| UT-06 | `done && !reused` counts line byte-unchanged | regression | P3 | Only diff vs. `48c5fc2` is the two added boolean guards; JSX content inside both blocks identical | `git diff 48c5fc2 -- apps/frontend/app/desk/page.tsx` shows exactly two changed lines: `{unreached > 0 && (` → `{unreached > 0 && !(run.state === "done" && run.reused) && (` and `{run.state === "done" && (` → `{run.state === "done" && !run.reused && (`. No other lines differ | PASS | none (code-read verification, no UI to screenshot) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-31

