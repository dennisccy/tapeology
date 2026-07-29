# Iteration State — desk

**After iteration:** 17 · **Date:** 2026-07-29 · **Verdict:** GOAL_ACHIEVED

## Journeys

13 passing (J-01..J-13) · 0 failing · 0 unknown · 0 regressed — 13 total (J-01..J-12 by replay,
J-06 by its 17-tool contract; J-13 by browser UT-05 + the evaluator's own 63-row re-derivation)

## Active blockers

- none — no failing journey, no open anti-goal violation, coherence COHERENCE-PASS, nobody waited on.
- Carry-only (NEVER an iteration goal): J-13 `evidence_makeup` — the `[NEW]` demo film was recorded
  on the AMBIENT store before audit fix F1, so its 8 frames show no price at all; re-film on a
  fixture-scoped rig with a fresh screen. Plus carried J-12 `evidence_makeup` (one full-page
  re-capture of the EARLIER same-date view; never cite iter-16's `UT-02-result.png` — wrong app).
- Framework, human-owned: `replay_lane_spec_journeys` (`scripts/automation/lib/replay-lane.sh:70`)
  truncates a WRAPPED journey-set line — keep `Required-still-passing journeys:` on ONE line.

## Last 2 verdicts

- iter 17: GOAL_ACHIEVED — J-13 proven: `reference_close` copied verbatim from the one walk
  `desk_screen.py` already makes, rendered beside each row's own band range; UT-05 shows an in-band
  and an out-of-band row in ONE frame; all 63 values re-derived from the stored `1d` bars with zero
  mismatches; suite exit 0 / 8 skip; fingerprint `08e471b10130e1e2`; 17 MCP tools; ZERO ambient writes.
- iter 16: GOAL_ACHIEVED — J-12 proven: the same-date pair is addressable by id, both run ledgers
  name their own damaged files on screen.

## Do not redo

- J-13 done: `"reference_close": close` at `desk_screen.py:401` (zero new `BarStore` read); the
  `band` column + `<th>` in `DeskRow`/`DeskRowsTable` and the `bandLine` in `deskRowDrillInTitle`;
  audit fix F1 — legacy rows keep their OWN `band <low>–<high>` range PLUS `close not recorded in
  this snapshot` (never collapse that back to the bare string).
- The `[NEW]` walkthroughs for J-09/J-10/J-11/J-12 are CORRECT — do NOT re-record them; only J-13's
  needs re-filming, as a passenger task. Do NOT build a `/desk` "Universe ledger" section.
- Every iter-14/15/16 "do not redo" item stays binding (J-01..J-12 stacks; no legacy backfill; rank key
  `_row_rank_key` unmoved; zero diff to every protected module, `config.py` and `engine/` included).
- Never start a second `next dev` from `apps/frontend` while the ambient one runs — they share `.next`
  and the ambient page silently starts serving the scoped backend's API base.
