# Iteration State — desk

**After iteration:** 33 · **Date:** 2026-07-31 · **Verdict:** ESCALATE

## Journeys

18 passing (J-01..J-18) · 1 partial (J-19 — record half proven, on-page disclosure fails) · 0 failing/unknown · 0 `DEFERRED-BUDGET` · 0 `pending_infra` · 0 `evidence_makeup` — 19 total; all 19 `spec_hash` values re-derived from `docs/goal.md` and matching; 4 historical anti-goal items all `resolved`; scan CLEAN; coherence COHERENCE-PASS.

## Active blockers

- **J-19 step 4 — owner: dev (THE reason for the next iteration).** `topupLibraryReach` (`apps/frontend/app/desk/page.tsx:894-897`) compares `store_frozen_through_after` as FULL microsecond timestamps while `:996`/`:1014` print `.slice(0,10)`, so the page reads "newest recorded reach 2026-07-30 · 101 pairs reach it" directly above "Pairs recorded earlier (303)" whose first rows print that SAME day (`reports/qa/goal-desk-iter-33-evidence/UT-J-19-fail.png`). Group at calendar-day granularity; cap the rendered `desk-topup-run-latest-reach-earlier-row` list at 20, keep the TRUE total in the heading, add a plain "showing N of M" line only when total > 20. Frontend + its guard test only.
- **`journey-scripts/J-19.json` — owner: dev/browser-qa.** Still pins today's exact figures and its step 4 asserts `"AAPL 4h — 2026-07-30"` AS an earlier row, i.e. it enshrines the bug. Repoint at stable substrings ("reach it", "Pairs recorded earlier") in the SAME iteration as the fix. `J-17.json` was ALREADY refreshed at iter-33 (uncommitted) — do not redo it.
- **J-19's `[NEW]` walkthrough — owner: demo-narrator, passenger task only.** `reports/phase-goal-desk-iter-33-demo-script.md` narrates the fix as shipped ("now agree with each other", "now capped") while its own frames show the unfixed page, and `step-03.png`/`step-04.png` are one image. Re-record AFTER the fix, narrated from the rendered page — never an iteration's reason to exist.
- **Depth — owner: engine/decomposer.** Iters 32 and 33 both specced `full` and both ran shorter (`depth_demoted` budget-breach → `depth_evidence_override`, the latter only because J-19 was recorded `passing`), dropping the developer twice. J-19 is now `partial` and this ESCALATE grants `run-goal.sh:2368`'s full pass: the next iteration MUST dispatch a developer.
- Coupling to watch: `test_desk_ui_guards.py` reads `journey-scripts/J-13.json` + `J-14.json` — archiving that folder breaks the backend suite.

## Last 2 verdicts

- iter 33: ESCALATE — dispatched `evidence`, product diff EMPTY, no developer; the confirm-rejected J-19 display defect verified unchanged at source AND in a screenshot the evaluator opened. Nothing regressed (byte-identical build); the iter-32 `passing` mark was an evaluator over-score, corrected to `partial`.
- iter 32: GOAL_ACHIEVED (first key) — REJECTed by the second key (`iter-32/eval-confirm.md` finding 3) on that same J-19 defect; engine recorded the iteration as CONTINUE.

## Do not redo

- **J-19's RECORD half is DONE**: `store_frozen_through_after` byte-identical to `BarStore.merged_bars` for all 404 pairs, single owner `_pair_window`/`desk_topup_log`, single endpoint `GET /research/desk/topup/runs`, legacy "library reach not recorded in this run" fallback intact. Do not rebuild or re-verify it; the fix is FRONTEND-ONLY.
- **Do NOT run a capture-only iteration**, and do NOT re-verify J-01..J-18 as an iteration goal. J-04/J-07/J-09/J-16/J-17 were re-checked at iter-33; the rest carry forward on valid evidence (product diff empty).
- J-16 layout is DONE and measured (`table-fixed` + 13-col `<colgroup>`): no 14th column, no width re-tuning, `band `/`opposite ` in-cell prefixes stay. Never script a `click` inside a `/desk` ranked/skipped row (stretched `absolute inset-0` anchor) — `expect`-only; demo/replay scripts stay READ-ONLY over the ambient store.
- Zero diff stays law: `engine/`, `config.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `research/routes.py`, `desk_topup_log.py`, `desk_topup_compute.py`, `meta.py`, `mcp/__init__.py`, both charts, the guard test files; pin `08e471b10130e1e2`; 17 MCP tools; zero new `Config` fields.
- Owner-optional, never a new iteration: iter-31's B1 / F1 / T3 / demo scroll-anchor. (Iter-32's two wording notes are SUBSUMED by the J-19 fix above.) Accepted non-defect: replay-frame duplication (tooling) — `J-04`/`J-09`/`J-16`/`J-17` verify frames share one md5.
