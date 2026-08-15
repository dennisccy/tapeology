# Iteration State — referee

**After iteration:** 7 · **Date:** 2026-08-15 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01..J-06) · 3 failing (J-07 J-08 J-09) · 1 partial (J-10 — kept half green with fresh evidence; era-end clauses wait on J-09) — 10 total

## Active blockers

- dev: a failed oracle attestation still mints the ONE permanent checkpoint snapshot as
  `corroborated` (the served fold correctly refuses) — gate it on `attestation["passed"]` in
  `referee_adjudicate.run_evaluation_and_record`'s `role` decision.
- dev: a corrupted hypothesis record vanishes silently from `GET .../adjudications` —
  `adjudications_response()` drops `hypothesis_store.list()`'s errors (the gap class Rider 2 just
  closed for `GET .../registry`).
- dev (docs): `state/blueprint.md:149-151` still shows the 4-key registry response (Rider 2 made it 5); `docs/handoffs/goal-referee-iter-7-dev.md:102` falsely claims it was updated.
- human, non-blocking, outside this project (since iter-2): trendora backend :8255 not restarted.
- engine: iters 6 and 7 both breached the 3600s budget (iter-7 elapsed 6581s) → full was demoted to lean and J-01..J-05 were DEFERRED-BUDGET.

## Last 2 verdicts

- iter 7: ESCALATE — J-06 verified passing, but the era's most permanent machinery shipped lean
  after a budget demotion and the evaluator's own probe found two write-side gaps.
- iter 6: CONTINUE — J-05 passed; the full lane's hard audit caught a critical backdateable-
  boundary hole that review and QA both missed.

## Do not redo

- J-06 is DONE and verified: `referee_adjudicate.py` (estimands A/B/C, evaluation as an operator
  act, one checkpoint + family BH fold, read-side fold, unwired `authorize_promotion`) — 40 tests
  green in the evaluator's own run. Fix the blockers above; do not rebuild.
- The three iter-7 riders are DONE: epoch_anchor exclusion, registry `integrity_errors` (audit
  B4), dead imports + the seeded-draw literal pin (in `tests/test_referee_null.py`, not
  `test_referee_registry.py` — audit T1).
- BH denominator protection is DONE (`_family_p_values` fills 1.0 over the frozen candidate list,
  TC-15/16); iteration 6's critical backdateable-boundary violation is FIXED and re-confirmed.
- J-10's kept-product walk ran with a fresh dated screenshot — keep that lane running every iter.
- Re-verified, keep true: zero new `Config` fields, MCP 20 tools, pin `08e471b10130e1e2`, suite 2,642 collected / 2,634 passed / 8 skipped.
