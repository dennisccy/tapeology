# Iteration State — desk

**After iteration:** 19 · **Date:** 2026-07-29 · **Verdict:** GOAL_ACHIEVED

## Journeys

14 passing (J-01..J-14) · 0 failing · 0 partial · 0 unknown — 14 total (J-12/J-13/J-14 carry `evidence_makeup`: pictures owed, product proven)

## Active blockers

- none. Two capture items owed, neither blocking nor a program change: the `[NEW]` walkthrough film over POPULATED `/desk` rows
  (also clears J-13's iter-17 film and J-12's iter-16 full-length frame), and J-14's hover-hint photograph, which this rig CANNOT
  take — the hint is a native HTML `title` (`app/desk/page.tsx:346`) painted outside CDP's screenshot surface; its text was read
  from the live DOM and is correct.
- disclosed, not a defect: the evidence lane again used `apps/backend/.data` instead of a copy — a real top-up (390 new bar series,
  record `topup-2026-07-29-5de907c83fc4.json`) plus 4 new screens landed there; nothing rewritten, all 10 screen checksums
  recompute, 369 older bar files untouched. The Desk now ranks 100 members instead of 63.

## Last 2 verdicts

- iter 19: GOAL_ACHIEVED — `_select_opposite_band` is distance-first now; the evaluator re-derived all 100 ranked rows of
  `screen-2026-07-20-ca185294a384` against `compute_tradability` with 0 mismatches, and HONA (0.00 bps class B vs the old rule's
  265.56 bps class A) proves the fix live.
- iter 18: CONTINUE — J-14 named the best-GRADED opposite wall, not the nearest; 2 of 63 real rows diverged.

## Do not redo

- J-14 is COMPLETE: fields, storage, distance-first selection, render, tooltip line, tests, MCP proxy (`desk_screen.py`
  `_select_opposite_band`/`_bands_by_class`, `app/desk/page.tsx`, `test_desk_screen.py`, `test_desk_ui_guards.py`,
  `test_mcp_server.py`). Do not re-open the tie-break order.
- `_select_best_band` (same-side, class-first) and `_row_rank_key` stay UNCHANGED — this journey discloses, it never re-ranks. No
  legacy backfill: the 6 pre-iter-18 screens correctly carry no opposite-wall value; never rewrite or recompute a recorded snapshot.
- The `[NEW]` walkthroughs for J-09/J-10/J-11/J-12 are CORRECT — do NOT re-record them. Never photograph a native `title` tooltip;
  read its text from the DOM instead.
- Never write a screen/universe snapshot or run a top-up into `apps/backend/.data`; never start a second `next dev` from
  `apps/frontend` while another runs (shared `.next`).
- Zero diff stays law for `engine/`, `config.py`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, both
  charts, `test_copy_discipline.py`; pin `08e471b10130e1e2`; exactly 17 MCP tools; no `/desk` "Universe ledger"; no CLI warmer.
