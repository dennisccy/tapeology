# Iteration State — desk

**After iteration:** 20 · **Date:** 2026-07-29 · **Verdict:** CONTINUE

## Journeys

14 passing (J-01..J-14) · 0 failing · 0 partial · 0 unknown — 14 total (J-13/J-14 carry `evidence_makeup`: the walkthrough film is owed; J-12's picture debt is CLOSED)

## Active blockers

- dev/harness: the `[NEW]` walkthrough film over POPULATED `/desk` rows (J-13 price+close, J-14 opposite wall) is still unrecorded —
  iter-20's demo lane wrote `Demo Verdict: SKIPPED`, gallery EMPTY, because its own script `reports/phase-goal-desk-iter-20-demo.json`
  carries JS regex literals at lines 28/64/76 instead of JSON strings. Fix = quote those targets, model the `band`/`opposite` reveal as
  a container SCROLL (no "scroll…" button exists), parse-check before recording, treat SKIPPED as a hard lane failure.
- HUMAN (owner): J-14's acceptance demands a PHOTOGRAPH of the row hover hint (`apps/frontend/app/desk/page.tsx:346`, native HTML
  `title`). This rig cannot capture it — the browser paints it outside CDP's screenshot surface (3 runs tried). iter-19's second key
  (`runs/goal-session-desk/iter-19/eval-confirm.md`) REJECTED the finish on this clause. The owner must either reword it to "read out
  of the live DOM" or ask for an on-page panel.
- disclosed, not a defect: the evidence lane served the owner's real `apps/backend/.data` again instead of a scoped copy (its own
  spec's TC-1) — but READ-ONLY this time: zero files created, modified or removed there (verified by `find -newermt`).

## Last 2 verdicts

- iter 20: CONTINUE — zero product diff; J-12's full-page capture landed and I verified it against the stored snapshots, but the
  walkthrough film failed on a malformed script, and iter-19's second key had already refused the finish over that same film.
- iter 19: GOAL_ACHIEVED (first key) — distance-first `_select_opposite_band` proven on all 100 rows; the second key then REJECTED
  (missing film, missing tooltip photograph, ambient-store proof).

## Do not redo

- J-12 IS COMPLETE INCLUDING ITS PICTURES: `reports/qa/goal-desk-iter-20-evidence/UT-J-12-result.png` (full page) + iter-16's
  `UT-03-result.png` are the verified pair. Do not re-capture it; do not re-record the J-09/J-10/J-11/J-12 walkthroughs.
- J-13 and J-14 are COMPLETE IN CODE (fields, distance-first selection, render, tooltip line, tests, MCP proxy). Do not re-open the
  tie-break order, `_select_best_band`, or `_row_rank_key`. Only the FILM is owed. No legacy backfill: pre-iter-18 screens correctly
  carry no opposite-wall value.
- Never photograph a native `title` tooltip in this rig — read its text from the DOM instead.
- Never write a screen/universe snapshot or run a top-up into `apps/backend/.data`; never start a second `next dev` from
  `apps/frontend` while another runs (shared `.next`).
- Zero diff stays law for `engine/`, `config.py`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, both
  charts, `test_copy_discipline.py`; pin `08e471b10130e1e2`; exactly 17 MCP tools; no `/desk` "Universe ledger"; no CLI warmer.
