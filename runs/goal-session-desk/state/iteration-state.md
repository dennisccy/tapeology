# Iteration State — desk

**After iteration:** 35 · **Date:** 2026-07-31 · **Verdict:** GOAL_ACHIEVED

## Journeys

20 passing (J-01..J-20) · 0 failing/partial/unknown · 0 `DEFERRED-BUDGET` · 0 `pending_infra` · 1 `evidence_makeup` (J-20, film only) — 20 total; all 20 `spec_hash` values re-derived from `docs/goal.md` and matching; no `journeys-changed.md`; 4 historical anti-goal items all `resolved`, none new; scan CLEAN; coherence COHERENCE-PASS.

## Active blockers

- **none blocking.** One owed ARTIFACT, not a product fault: J-20's `[NEW]`-flagged demo-narrator walkthrough was never recorded — the engine dispatched `depth=lean` against a spec asking `Depth: full` (third such shortening this session, after iters 32/33), so no demo-narrator step ran and `reports/demo/goal-desk-iter-35/` does not exist. Rides a `Depth: evidence` pass as a passenger; NEVER the reason for a build run.
- Awaiting the second-key confirm only. If it REJECTS, the follow-ups below are the candidate work — nothing else is open.

## Last 2 verdicts

- iter 35: GOAL_ACHIEVED — J-20's screen-comparison disclosure landed and was proven three ways by the evaluator personally: three per-state screenshots opened (identical / churned / no-earlier); the whole comparison re-derived by hand in Python over the 12 frozen files in `apps/backend/.data/screen`, reproducing every count, symbol, order and value exactly; and the served fields checked byte-for-byte against `ScreenStore.list()`'s recorded rows — 0 mismatches both directions, both pairs. Suite 1551 pass/8 skip/0 fail, pin `08e471b10130e1e2`, MCP 17, replay 10/10 with ZERO script edits, nothing under `.data` newer than the run's start.
- iter 34: GOAL_ACHIEVED — J-19's top-up reach panel stopped contradicting itself (calendar-day grouping + 20-row cap); confirmed by the second key (`iter-34/eval-confirm.md` = CONFIRM_ACHIEVED).

## Do not redo

- **J-20 is DONE, front to back**: `apps/backend/app/research/desk_screen_diff.py` (sole owner), `GET /research/desk/screen/compare` (`desk_routes.py:400`, sole endpoint), the `/desk` Screen Comparison section (`app/desk/page.tsx:2598` — renders LAST, own `desk-screen-compare-*` testid namespace), `tests/test_desk_screen_diff.py` + `tests/test_desk_screen_compare_ui_guard.py` (31 tests), `journey-scripts/J-20.json` (stable substrings). Do not rebuild, re-own, re-path or move any of it.
- **J-19 stays DONE** (record half + display fix + its guard tests); `J-17.json`/`J-19.json` are already repointed to stable substrings — do not re-point either.
- **Do NOT click Top-up or Run Screen, and do NOT stand up a scoped rig**: the ambient store is untouched (1163 bar series, 1 universe, 12 screens, 3 screen-run, 2 top-up, 2 reconciliation records) and already carries all three J-20 states.
- **Do NOT run a capture-only iteration** and do not re-verify J-01..J-19 as an iteration goal. Presentation facts on non-gating lanes (deep-scroll captures returning black → crops from full-page; replay verify frames sharing one md5) are accepted tooling behaviour, not product faults.
- Zero diff stays law: `engine/`, `config.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`, `tradability.py`, `levels.py`, `desk_topup_log.py`, `desk_topup_compute.py`, `meta.py`, `mcp/__init__.py`, both charts, the guard test files; pin `08e471b10130e1e2`; 17 MCP tools; zero new `Config` fields. `test_desk_ui_guards.py` reads `journey-scripts/J-13.json`+`J-14.json` — archiving that folder breaks the suite.
- **New follow-ups, explicitly never an iteration goal on their own:** (1) `/desk` prints "The compared snapshots' ranked rows are identical." when only its 5 compared fields match — for that pair all 100 rows differ in `basis_age_days` (4 vs 3), which the briefing table above renders as "4 d before as-of"; one-line copy fix, and `docs/goal.md` step 5 dictates the current wording; (2) unknown-id returns a 4th `base_resolution` value (`null`) the Data Contract does not enumerate; (3) only 10 of 19 goldens were replayed (zero edited; the other 9 proved collision-free by static sweep). Plus iter-34's seven owner-optional notes, all still non-blocking.
