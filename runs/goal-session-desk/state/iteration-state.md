# Iteration State — desk

**After iteration:** 16 · **Date:** 2026-07-29 · **Verdict:** GOAL_ACHIEVED

## Journeys

12 passing (J-01..J-12) · 0 failing · 0 unknown · 0 regressed — 12 total (J-03..J-11 by replay,
J-06 by its 17-tool contract, J-12 by fresh browser + walkthrough evidence; J-01/J-02 spot-checked)

## Active blockers

- none — no failing journey, no open anti-goal violation, coherence COHERENCE-PASS, nobody waited on.
- Carry-only (never an iteration goal): J-12 holds `evidence_makeup: true` — one full-page re-capture
  of the EARLIER same-date view makes NFLX's `1d` badge legible on both sides. NEVER cite
  `reports/qa/goal-desk-iter-16-evidence/UT-02-result.png` (an UNRELATED app); use `AUDIT-UT-02/03-…png`.

## Last 2 verdicts

- iter 16: GOAL_ACHIEVED — J-12 proven: the same-date 2026-07-27 pair is individually addressable by
  id and both run ledgers name their own damaged files on screen; suite 1426 pass / 8 skip / exit 0;
  fingerprint `08e471b10130e1e2`; 17 MCP tools; ZERO writes to `apps/backend/.data`.
- iter 15: GOAL_ACHIEVED — J-11's per-row `history` column built, filmed and proven off disk.

## Do not redo

- J-12 done: `?id=` branch + `id`+`date` 422 refusal (fires BEFORE `store.list()`) +
  `integrity_errors` on both run-ledger GETs (`desk_routes.py:281-296`, `:330-362`, `:527-542`;
  `?date=` still `matching[-1]`, byte-unchanged); frontend id-based history select/highlight,
  `recorded` column, Provenance `id`/`created_utc`, 3 `IntegrityErrorsNote` mounts.
- The `[NEW]` walkthrough is CORRECT (`Demo Verdict: RECORDED`, 7/7 flagged) — do NOT re-record it;
  the audit repaired it once and re-running risks the wrong-page frames.
- Do NOT build a `/desk` "Universe ledger" section: the iter-16 spec's four-ledger premise was
  factually wrong (no such section, no `DeskUniverseResult` type) and `docs/goal.md` never asked for
  one — correct the spec text; a Universe section would need its own journey.
- Every iter-14/iter-15 "do not redo" item stays binding (J-01..J-11 stacks; no legacy backfill; rank
  key `_row_rank_key` proven unmoved). Re-verified: fingerprint `08e471b10130e1e2`, 17 MCP tools, zero
  diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`desk_coverage.py`/`StructureChart.tsx`/
  `test_copy_discipline.py`/`engine/`.
- Carry, never forced: an all-corrupt screen store hides its integrity note behind the empty-state
  panel; run tables unbounded; keyboard access for history rows; `/desk` is eight long sections.
