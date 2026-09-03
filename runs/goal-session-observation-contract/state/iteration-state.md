# Iteration State — observation-contract

**After iteration:** 2 · **Date:** 2026-09-03 · **Verdict:** CONTINUE

## Journeys

0 passing · 3 failing (J-03 J-04 J-05) · 3 partial (J-01 J-02 J-06) — 6 total

## Active blockers

- none human-owned. Remaining work is dev-owned, in the goal's required order: source/session
  descriptor + lifecycle/feed honesty (J-03), path equivalence (J-04), the route
  `/tape/{ticker}/observation` in `app/main.py` (J-05), the guards module
  `tests/test_tape_observation_guards.py` (J-06) — all confirmed absent. J-01/J-02/J-06 are
  partial ONLY because that route does not exist yet (step 5), not because of a defect.
- Carry-forward MINOR (reviewer, iter-2): `_settle` at `apps/backend/app/watch_manager.py:341`
  keys its write by ticker with no check that the engine is still the registered one — a
  cancelled feeder can clobber a freshly re-watched ticker's pair; untested (sync harness only).
  Fix + a real running-task switch test before the route lands at step 5.

## Last 2 verdicts

- iter 2: CONTINUE — J-02 failing→partial; atomic settled pair + `get_observation_source` built;
  evaluator re-ran `test_tape_observation_time.py` 33/33 (9 counter-examples) and the full suite
  4001 pass / 8 skip / 0 fail; scan CLEAN; `iter-2/coherence.md` COHERENCE-PASS.
- iter 1: CONTINUE — J-01 failing→partial; builder + 38/38 tests re-run by the evaluator; suite
  3968/8/0; scan CLEAN; coherence PASS.

## Do not redo

- Order step 1 DONE (iter-1): `app/observation_contract.py` (schema constants, partition,
  `canonical_encode`, both hash laws, `build_tape_observation`) + 38-test
  `tests/test_tape_observation_projection.py`. Untouched at iter-2 by design.
- Order step 2 DONE (iter-2): per-ticker atomic settled pair, the one `_settle` helper wired
  through all five feeders + `pause()`/`resume()` + four `watch*` cold resets,
  `get_observation_source`, `_iso_utc`, 33-test `tests/test_tape_observation_time.py`.
- Settled iter-2 calls (review PASS_WITH_NOTES, coherence PASS): cold reset at each fresh engine;
  `end_reason` read live off the engine; `_iso_utc` duplicate guarded by a cross-check test.
- Do not re-pin: fingerprint `08e471b10130e1e2`, suite 4001/8/0, tsc 0 errors. Do not move the
  route earlier — a flat journey table through iterations 3-4 is expected. No frontend work.
