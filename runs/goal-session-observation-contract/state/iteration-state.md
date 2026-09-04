# Iteration State — observation-contract

**After iteration:** 3 · **Date:** 2026-09-04 · **Verdict:** CONTINUE

## Journeys

0 passing · 2 failing (J-04 J-05) · 4 partial (J-01 J-02 J-03 J-06) — 6 total

## Active blockers

- none human-owned. Dev-owned, in the goal's required order: path equivalence (J-04, step 4), the
  route `/tape/{ticker}/observation` in `app/main.py` (J-05, step 5), guards module
  `tests/test_tape_observation_guards.py` (J-06, step 6) — all absent (my own `ls`/grep). J-01/J-02/
  J-03/J-06 are partial ONLY because that route does not exist yet.
- New MINOR (reviewer, iter-3): `tests/test_tape_observation_lifecycle_feed.py:513` asserts over a
  hardcoded set literal and never calls the manager — vacuous; delete or rewrite it.
- New advisory (coherence, iter-3): `app/main.py`'s new `_iso_utc` is a third copy of the pinned ISO
  format whose docstring claims byte-identity with the other two, but no test checks that.

## Last 2 verdicts

- iter 3: CONTINUE — J-03 failing→partial; per-watch source/session descriptor + `_settle` identity
  fix built; evaluator re-ran `test_tape_observation_lifecycle_feed.py` 30/30 and the full suite
  4039 collected / 0 fail / 8 skip; fingerprint + tsc re-verified; scan CLEAN; coherence PASS.
- iter 2: CONTINUE — J-02 failing→partial; atomic settled pair + `get_observation_source` built;
  evaluator re-ran `test_tape_observation_time.py` 33/33 and the full suite 4001/8/0; scan CLEAN.

## Do not redo

- Step 1 DONE (iter-1): `app/observation_contract.py` (schema/partition constants,
  `canonical_encode`, both hash laws, `build_tape_observation`) + 38-test
  `tests/test_tape_observation_projection.py`. Untouched since.
- Step 2 DONE (iter-2): per-ticker atomic settled pair, the one `_settle` helper, `_iso_utc`, 33-test `tests/test_tape_observation_time.py` (iter-3 changed only its tuple unpacking).
- Step 3 DONE (iter-3): `SourceDescriptor` + `_record_source` at all four `watch*` constructors,
  window bounds threaded from `main.py`'s two historical call sites, `get_observation_source`
  widened to a 4-tuple, `_settle` engine-identity check (iter-2's carry-forward MINOR — now CLOSED,
  real async switch test + counterexample), 30-test `tests/test_tape_observation_lifecycle_feed.py`.
- Do not re-pin: fingerprint `08e471b10130e1e2`, suite 4039 collected / 0 fail / 8 skip, tsc 0
  errors. Do not move the route earlier — a flat journey table through iteration 4 is expected. No
  frontend work; no `Config` field.
