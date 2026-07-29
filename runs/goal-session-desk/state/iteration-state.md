# Iteration State — desk

**After iteration:** 18 · **Date:** 2026-07-29 · **Verdict:** CONTINUE

## Journeys

13 passing (J-01..J-13) · 1 partial (J-14) — 14 total (J-01..J-12 replay 12/12, J-06 by its 17-tool contract, J-14 by browser UT-03/05/06 + the evaluator's own 6-row re-derivation)

## Active blockers

- J-14 selection rule (owner: dev) — `desk_screen.py:269` `_select_opposite_band` delegates to
  `_select_best_band` (class-first), but `docs/goal.md` J-14's title + step 1 ask for the NEAREST
  opposite band (distance first, class as tie-break). Evaluator measured it against
  `compute_tradability` on the real 63-row screen (as_of 2026-07-29): 2 rows differ — HONA (shipped
  class A 336.96 bps vs nearest class B 153.67 bps), META (class A 232.58 vs class C 92.05). Fix the
  key + goldens + the two "nearest" comments (`desk_screen.py:89`, `app/desk/page.tsx:273`), OR
  amend goal.md to stop claiming "nearest". Everything else in J-14 is verified correct.
- Carry-only captures (NEVER an iteration goal): a `[NEW]` walkthrough over POPULATED rows for J-14
  (iter-18's frames show `/structure`) — the same re-film clears J-13's; a full-page Screen History
  frame clears J-12's. Framework: keep `Required-still-passing journeys:` on ONE physical line.

## Last 2 verdicts

- iter 18: CONTINUE — J-14 built, stored, byte-identical to `compute_tradability`, but names the
  best-GRADED opposite wall, not the NEAREST, on 2 of 63 real rows; walkthrough filmed the wrong
  page. Suite green, fingerprint `08e471b10130e1e2`, 17 tools, zero ambient writes, COHERENCE-PASS.
- iter 17: GOAL_ACHIEVED — J-13 proven (`reference_close` + each row's own band range, 63/63).

## Do not redo

- J-14 fields/storage/render/tests/MCP proxy are DONE and verified (`_select_opposite_band`,
  `_bands_by_class`, `lib/types.ts`, `app/desk/page.tsx` opposite cell + tooltip line,
  `test_desk_screen.py`, `test_desk_ui_guards.py`, `test_mcp_server.py`) — only the ORDER is open.
- The `[NEW]` walkthroughs for J-09/J-10/J-11/J-12 are CORRECT — do NOT re-record them. Never write
  a screen/universe snapshot into `apps/backend/.data`; evidence computes use a fixture-scoped rig
  (iter-18: `…/iad.goal-desk-iter-18.3302867/scoped-rig-desk18`).
- No `/desk` "Universe ledger" section; no CLI warmer for the new fields. Every iter-14..17 "do not
  redo" item stays binding (no legacy backfill; `_row_rank_key` unmoved; zero diff to every
  protected module, `config.py` and `engine/` included). Never start a second `next dev` from
  `apps/frontend` while the ambient one runs (shared `.next`).
