# Iteration State — desk

**After iteration:** 22 · **Date:** 2026-07-30 · **Verdict:** GOAL_ACHIEVED

## Journeys

14 passing (J-01..J-14) · 0 failing/partial/unknown — 14 total; no `evidence_makeup`, no `pending_infra`.

## Active blockers

- none. J-14's native-tooltip photograph (the only open item since iter-19) is CAPTURED:
  `reports/qa/goal-desk-iter-22-evidence/J-14-tooltip.png` + `-crop.png`, owner-approved rig
  `project-extensions/qa-rig/` (T-10a). Only the owner's confirm of the finish is outstanding.
- Housekeeping (human, not blocking): the qa-rig is still RUNNING (Xvfb 3462046 + Chrome 3462134,
  inside the host-guard mask `0-3,8-11`) — `xrig.sh down` when convenient.
- Disclosed deviation, NOT a goal.md violation (7th run): evidence lanes served the ambient `.data`/`:3301`-`:8301` rig, not a scoped copy; READ-ONLY, verified file by file.

## Last 2 verdicts

- iter 22: GOAL_ACHIEVED — zero product diff; the owed tooltip photograph exists (both frames opened);
  numbers re-derived from `screen-2026-07-20-ca185294a384.json` (checksum recomputes); J-14 re-verified
  against the CHANGED goal text (T-10a), new `spec_hash`; COHERENCE-PASS; `08e471b10130e1e2`; 17 tools.
- iter 21: STALLED — that photograph was then impossible in a headless/CDP rig (human-owned unblock);
  the owner has since acted (T-10a + the rig).

## Do not redo

- J-14 COMPLETE INCLUDING ITS PHOTOGRAPH; J-12/J-13 complete including pictures + the iter-21 `[NEW]`
  walkthrough (`RECORDED`). Never re-attempt these captures, never make re-filming an iteration GOAL,
  do not re-open `_select_opposite_band`, `_select_best_band`, `_row_rank_key`.
- Do not re-litigate T-10a (screenshot bar stands, the rig is how it is met, DOM read-out is a
  cross-check only); do not edit `docs/goal.md`.
- Zero diff stays law for `engine/`, `config.py`, `tradability.py`, `levels.py`, `bars.py`,
  `bar_index.py`, `desk_coverage.py`, both charts, `test_copy_discipline.py`; pin
  `08e471b10130e1e2`; 17 MCP tools; no `/desk` "Universe ledger"; no CLI warmer.
- Never write a screen/universe snapshot or top-up into `apps/backend/.data`; never run two
  `next dev` from `apps/frontend` at once (shared `.next`).
- Carried non-defects, only if an iteration already touches them: replay/demo frames collapse to one
  first-view image (`demo_runner.py --mode verify`), `/desk` 8 sections, unbounded run tables, history
  rows not keyboard-reachable, shallow goldens, goal.md's stale host-mask paragraph.
