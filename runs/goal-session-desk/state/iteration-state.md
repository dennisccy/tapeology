# Iteration State — desk

**After iteration:** 0 · **Date:** 2026-07-25 · **Verdict:** CONTINUE

## Journeys

0 passing · 6 failing (J-01 J-02 J-03 J-04 J-05 J-06) · 1 partial (J-07) — 7 total

## Active blockers

- none human-owned. Dev-owned: the whole desk subsystem is unbuilt — J-01 (universe seam/parser/
  store/fixture + `GET`/`POST /research/desk/universe*`) gates J-02–J-06. New code lands in
  `apps/backend/app/research/desk_universe.py` (new), `app/config.py` (Path-A fields),
  `apps/backend/tests/fixtures/` (fixture snapshot).
- Operational hazard: `journey-scripts/J-07.json` step 8 asserts async text `300.11` on a 15 s
  timeout — fix before the replay lane guards J-07 (see lessons.md).

## Last 2 verdicts

- iter 0: CONTINUE — honest baseline: desk era confirmed unbuilt (6 failing), kept product intact
  (J-07 partial: suite 1169p/7s, pin `08e471b10130e1e2`, all browser steps screenshotted).
- n/a — first evaluated iteration

## Do not redo

- Baseline absence probes for J-01–J-06 are DONE and re-verified by the evaluator (404 routes, zero
  `desk` greps in `apps/backend/app/`, `UI_ROUTES` = 2, `EXPECTED_TOOLS` = 15, no `desk_universe_*`
  field, no `.data/universe/`, no `useSearchParams` in `structure/page.tsx`). Do not re-probe; build.
- Kept-product browser walk DONE this iteration: sim cockpit → Buyer Control, live tape bars +
  10s→30s switch, historical AAPL 1d candles + 302.20/300.10 band overlay, `/structure` AAPL as-of
  2026-06-22 → `300.11–302.2 Class A`, Case Study drill-in, honest Edge Report panel —
  `reports/qa/goal-desk-iter-0-evidence/`.
- Suite + pin baseline RECORDED: 1169 pass / 7 skip / 0 fail; `08e471b10130e1e2`. Suite may grow,
  never shrink; the pin must not move (Path A only).
- `blueprint.md` is DRAFTED at `runs/goal-session-desk/state/blueprint.md` (3-route target nav +
  five desk-owned Data Contract rows). Extend it; do not redraft.
- J-07 is `partial` BY DECISION (its "nav = 3 routes" / "MCP = 17 tools" clauses land with
  J-04/J-06) — see `state/assumptions.md`. Do not re-litigate or score it `passing` until they hold.
- Next target settled: **J-01 alone, at `full` depth** (new store format + first Path-A Config
  fields + parser-honesty contract). Reasons in `iter-0/eval.md`.
