# Iteration State — desk

**After iteration:** 23 · **Date:** 2026-07-30 · **Verdict:** GOAL_ACHIEVED

## Journeys

15 passing (J-01..J-15) · 0 failing/partial/unknown — 15 total; no `evidence_makeup`, no `pending_infra`.

## Active blockers

- none. J-15 (built this iteration) is verified: one frame shows a 2-level, a 5-level and a 609-level row plus the `round number` badge; all 100 ranked rows re-derived against the canonical owner.
- Open design question (no goal.md clause, not blocking): `/desk`'s ranked table is now 12 columns and `opposite`+`levels` need a sideways scroll at 1440px (UT-07 FAIL, pre-existing since iter-18) — the next proposer cycle should treat "how the briefing surfaces disclosure" as its own journey.
- Harness bugs, not product: `closure_gate.py`'s bare `backend-only` substring guard false-fails CLOSURE on an honest report; `goal_gate.py results`' `| FAIL |` regex misses `| **FAIL** |`.
- Disclosed deviation, NOT a goal.md violation (8th run, 2nd that WROTE): evidence lanes used the ambient `.data`/`:3301`-`:8301` rig and appended one real 100-row screen; cause = the NOTES recipe is missing from `runs/<iter>/goal-slice-bqa.md`. Also still running: the qa-rig (`xrig.sh down`).

## Last 2 verdicts

- iter 23: GOAL_ACHIEVED — J-15 shipped and proven (100/100 rows match `compute_tradability`, key order included); rank order unmoved; legacy rows honest; suite 1454 pass/8 skip; `08e471b10130e1e2`; 17 tools; COHERENCE-PASS; scan CLEAN; 4-file product diff.
- iter 22: GOAL_ACHIEVED — the owed native-tooltip photograph captured on the owner-approved T-10a rig; the session's last picture debt closed; zero product diff.

## Do not redo

- J-15 COMPLETE: `desk_screen.py`'s `_band_member_timeframes` + 3 verbatim row fields, `/desk`'s `levels` column reusing `/structure`'s `tradable-band-round-number` badge, `lib/types.ts` fields, legacy "composition not recorded in this snapshot". J-12/J-13/J-14 complete including their photographs.
- Do NOT delete or backfill `.data/screen/screen-2026-07-30-bad6387963ef.json` (a valid pinned append — removing it breaches the immutable-data rail and destroys J-15's evidence); do NOT revert the iter-23 J-09 golden repair ("404 of 404 pairs attempted"); do not re-open J-01..J-14 beyond the replay check.
- Zero diff stays law: `engine/`, `config.py`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, both charts, `test_copy_discipline.py`, `_row_rank_key`, `_select_best_band`, `_select_opposite_band`; pin `08e471b10130e1e2`; 17 MCP tools; do not edit `docs/goal.md`.
- Never write a screen/universe snapshot or top-up into `apps/backend/.data` — put the scoped-rig recipe in the browser-qa AND demo slices; never run two `next dev` from `apps/frontend` at once.
- Carried non-defects (only if an iteration already touches them): replay frames collapse to one first-view image, demo click targets match all 100 rows, `/desk` 8 sections, unbounded run tables, history rows not keyboard-reachable, goal.md's stale host-mask paragraph.
