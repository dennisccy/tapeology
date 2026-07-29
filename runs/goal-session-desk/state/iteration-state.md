# Iteration State — desk

**After iteration:** 21 · **Date:** 2026-07-30 · **Verdict:** STALLED

## Journeys

14 passing (J-01..J-14) · 0 failing · 0 partial · 0 unknown — 14 total (only J-14 keeps `evidence_makeup`: the un-photographable tooltip; J-13's film debt is CLOSED)

## Active blockers

- HUMAN (owner), the ONLY blocker: `docs/goal.md` J-14 demands "one screenshot of a row tooltip
  carrying its `bands_by_class` line (T-10: no screenshot ⇒ `unknown`, never `passing`)". It is a
  native browser tooltip (`apps/frontend/app/desk/page.tsx:346`, `deskRowDrillInTitle` :278) drawn
  outside CDP's capture surface — 3 runs tried. Owner picks: reword to "read out of the live DOM"
  (cheapest) · on-page panel instead of `title` (needs lean depth) · approve a desktop-capture rig ·
  accept as-is. iter-19's second key (`iter-19/eval-confirm.md`) REJECTED the finish on this clause.
- disclosed deviation, NOT a goal.md violation (6th run): both evidence lanes served the ambient
  `apps/backend/.data`, not a scoped copy (uvicorn :8301 has no data-dir override per
  `/proc/2071190/environ`); READ-ONLY this run. Fix = a rail proving the SERVING process uses a copy.

## Last 2 verdicts

- iter 21: STALLED — the owed `[NEW]` walkthrough was RECORDED (narration verified number-by-number
  against `screen-2026-07-20-ca185294a384` on disk); only the human-owned tooltip clause remains.
- iter 20: CONTINUE — zero product diff; J-12's capture landed, demo lane wrote `SKIPPED`.

## Do not redo

- J-13/J-14 COMPLETE IN CODE and their `[NEW]` walkthrough IS RECORDED
  (`reports/demo/goal-desk-iter-21/`, Demo Verdict RECORDED). Do not re-open `_select_opposite_band`,
  `_select_best_band`, `_row_rank_key`; never make re-filming an iteration GOAL again.
- J-12 complete including pictures; J-04/J-05/J-07/J-12 replayed green and fingerprint
  `08e471b10130e1e2` + exactly 17 MCP tools re-counted at iter-21.
- Never photograph a native `title` tooltip here (impossible — read the DOM text); never write a
  screen/universe snapshot or top-up into `apps/backend/.data`; never run two `next dev` from
  `apps/frontend` at once (shared `.next`).
- Zero diff stays law for `engine/`, `config.py`, `tradability.py`, `levels.py`, `bars.py`,
  `bar_index.py`, `desk_coverage.py`, both charts, `test_copy_discipline.py`; no `/desk` "Universe
  ledger"; no CLI warmer. Carried non-defects, only if an iteration already touches `/desk`: 8
  stacked sections, unbounded run tables, no keyboard access on history rows, shallow goldens.
