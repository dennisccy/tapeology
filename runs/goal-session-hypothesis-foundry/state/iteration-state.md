# Iteration State — hypothesis-foundry

**After iteration:** 8 · **Date:** 2026-08-27 · **Verdict:** STALLED

## Journeys

8 passing (J-01..J-08) · 0 failing · 0 unknown — 8 total. J-08 newly passing; zero regressions (evaluator re-ran all 8 goldens itself after the audit's late frontend fix: 8/8 PASS).

## Active blockers

- **OWNER** — "No second real generation epoch" (iter-5, MINOR, blocking): ratify or reject the
  discarded first `epoch_id`. No code can discharge it; the recurrence guard already landed.
- **OWNER** — "Persistence stays scoped" (iter-6, MINOR, blocking): a page-load GET truncates
  `.data/foundry/foundry_exhaust_runner.lock`; re-verified live at iter-8, and the sole repair site
  (`foundry_runner.py` `SingleFlightLock.acquire`) is SEALED with no skip parameter. Options: an
  `owner_disposition`, or an owner-sanctioned seal break; routing around it recreates the
  single-source-of-truth violation iter-7 closed.
- Both entries sit in `state/journey-history.json`; counts total=4 / resolved=2 / blocking=2 / non-blocking=0 / critical=0. The evaluator may never write an `owner_disposition` itself.
- Non-blocking, carry to closure (never an iteration goal): B2 second per-request ledger read · B3 §8.2 sweep misses the enriched served body (verified clean) · F2 Final Summary needs its own expand · F3 `unresolved_magnitude_words` dangling ref · blueprint names sealed `foundry_runner.py` as owner of `diagnostic_survivor_count` (real owner `micro_routes.py`) · QA-report defects P1/P2 · walkthrough defective (demo script clicks non-existent `desk-section-expand-*` testids; J-08 has `evidence_makeup: true`).

## Last 2 verdicts

- iter 8: STALLED — all 8 journeys pass, nothing regressed, but the only blockers left are two
  owner-owned anti-goal rulings; no legal Goal Mode work remains.
- iter 7: ESCALATE — the duplicated count got its one legal owner, but the QA lane passed without
  the browser proof its own checklist demanded.

## Do not redo

- J-08 Final Summary + per-source provenance drill-in — shipped (`micro_routes.py`
  `compute_foundry_final_summary`; `desk/page.tsx:8264+`).
- Freeze set 59/59 byte-identical (re-hashed at iter-8). `foundry_runner.py` and
  `foundry_source_registry.py` ARE sealed — the iter-8 spec and plan both wrongly routed work there.
- `frozen_ready_total` single-owner fix (iter-7) + pinning test — settled; the sealed CLI's second
  formula is permanently un-editable, not a defect to re-fix.
- Store-scope CLEAN (11395 files); no second real epoch; no post-lock science change; screenshot
  Foundry via `demo_runner --mode verify`, never Chrome-MCP deep-scroll.
