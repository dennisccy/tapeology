# Iteration State — desk

**After iteration:** 12 · **Date:** 2026-07-28 · **Verdict:** ESCALATE

## Journeys

8 passing (J-01 J-02 J-03 J-04 J-05 J-06 J-07 J-08) · 1 partial (J-09) · 0 failing · 0 regressed — 9 total

## Active blockers

- J-09's last clause (goal.md: "a `[NEW]`-flagged demo-narrator walkthrough covers the top-up-run
  disclosure end to end") has NO artifact: no `reports/phase-goal-desk-iter-12-demo.json`, no
  `reports/demo/goal-desk-iter-12/`. Owner: pipeline, NOT a person. Cause (`trace/trace.jsonl`):
  LEAN runs demo-narrator AFTER the evaluator (iter-10: 09:44 → 09:59), FULL runs it BEFORE
  (iter-11: 13:18 → 14:17). **Iteration 13 MUST be full.**
- Rig is down: frontend :3301 gone, empty rig :8302/:3302 stopped; leftover backend PID 1180202
  still ~78% CPU (affinity 4-7,12-15, inside host-guard caps) — kill it, then reseed ONE root.
- Capture ORDER is the fix: seed → boot frontend → photograph the empty panel → record the 3 runs
  → photograph the populated panel. Deleting records to re-create "empty" breaches append-only.

## Last 2 verdicts

- iter 12: ESCALATE — J-09 partial a 2nd consecutive time; its one missing artifact comes from a
  lane lean depth runs AFTER scoring. Zero product diff; all 8 other journeys re-verified passing.
- iter 11: CONTINUE — J-09 built and clause-proven, but its walkthrough showed only the empty panel.

## Do not redo

- **J-09's product code is DONE and clause-verified** — `desk_topup_log.py`, `GET
  /research/desk/topup/runs`, the `/desk` panel, the tests. Iteration 13 films only: **no program
  change** (iter-12's whole diff was one README bullet).
- **J-09's two standalone browser frames are DONE**, evaluator-opened
  (`reports/qa/goal-desk-iter-12-evidence/UT-J-09-empty|populated-topup-section.png`) — only the
  narrated walkthrough is owed.
- **J-01–J-08 DONE**, re-verified passing in iter-12 (7 by golden replay on the scoped rig, J-06 by
  its 17-tool contract + the evaluator's own source count). Do not re-derive.
- **Settled:** R-1's eight ratified files (`docs/goal.md` line 106ff); zero new `Config` field;
  suite 1369/8; pin `08e471b10130e1e2`; `UI_ROUTES` = 3; MCP = 17 tools; the 3-checkpoint recipe.
- **Carried, do not force:** run list drops `integrity_errors` (`desk_routes.py:258`); auto-refresh
  race (`app/desk/page.tsx:1116`); no run-table cap; six stacked sections; same-date screens; keys.
