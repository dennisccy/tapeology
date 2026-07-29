# Iteration State — desk

**After iteration:** 15 · **Date:** 2026-07-29 · **Verdict:** GOAL_ACHIEVED

## Journeys

11 passing (J-01..J-11) · 0 failing · 0 unknown · 0 regressed — 11 total (J-03..J-10 by replay,
J-06 by its 17-tool contract, J-11 by fresh browser + walkthrough evidence; J-01/J-02 spot-checked)

## Active blockers

- none — no failing journey, no open anti-goal violation, coherence COHERENCE-PASS, nobody waited on.
- Owner-facing, not blocking: this run again wrote to the real `apps/backend/.data` (+1 snapshot
  `screen-2026-07-28-ac07c9581a4f`, 2 rebuildable caches; 0 of 369 price files touched, nothing
  rewritten). Irreversible by design; disclosed in eval.md + assumptions.

## Last 2 verdicts

- iter 15: GOAL_ACHIEVED — J-11's `history` column built, filmed and proven; the evaluator
  re-derived both fields for all 63 ranked rows from `BarStore.merged_bars` with 0 mismatches;
  suite 1418 pass / 8 skip / exit 0; fingerprint `08e471b10130e1e2`; 17 MCP tools.
- iter 14: GOAL_ACHIEVED — J-10 built, proven off disk (345→369 rows repaired) and filmed.

## Do not redo

- J-11 done end to end: `desk_screen.py::_resolve_reference_close_and_history` (both fields from the
  ONE `merged_bars(symbol,"1d")` walk), `/desk` `history` column + `deskRowDrillInTitle`
  (`page.tsx:328/365`), `types.ts:819-820`, +239 test lines in `test_desk_screen.py`, and the
  `[NEW]` walkthrough `reports/demo/goal-desk-iter-15/` — do NOT re-record it (audit already did).
- Every iter-14 "do not redo" item stays binding (J-01..J-10 stacks, TC-17/TC-18 evidence, the six
  deferred backlog items B2–B6/F1/T5).
- Do NOT backfill legacy screen rows or touch the rank key (`_row_rank_key` proven unmoved).
- Evaluator re-ran the sentinels: zero diff on `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/
  `config.py`/`meta.py`/`mcp/__init__.py`/`StructureChart.tsx`/`PriceChart.tsx`/`app/engine/`/
  `test_copy_discipline.py`. FUTURE `[NEW]`-walkthrough journeys run `full` and must assert
  `Demo Verdict: RECORDED` + a non-empty gallery, never a replay script (iter-15 lesson).
- Carry: rig "scoping" was ports-only (no `TAPEOLOGY_*` override) though a report claims otherwise;
  no MCP `desk_screen` pass-through test; `TC-09-tooltip.png` paints no tooltip; "history" counts
  DAILY bars only — never threshold it; `/desk` is eight long sections; keyboard access for history
  rows; same-day screens indistinguishable by date-only lookup.
