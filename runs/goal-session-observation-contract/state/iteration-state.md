# Iteration State — observation-contract

**After iteration:** 4 · **Date:** 2026-09-04 · **Verdict:** CONTINUE

## Journeys

0 passing · 1 failing (J-05) · 5 partial (J-01 J-02 J-03 J-04 J-06) — 6 total

## Active blockers

- None human-owned. Dev-owned, in the goal's required order: route `GET /tape/{ticker}/observation`
  in `app/main.py` + `tests/test_tape_observation_route.py` (J-05, step 5), then
  `tests/test_tape_observation_guards.py` (J-06, step 6). J-01..J-04 are partial ONLY because that
  route does not exist yet (my own grep of `main.py`). It must read `get_observation_source`, never
  an engine — the goal calls that a critical violation.
- Stale goldens: `journey-scripts/J-01.json` step 5 + `J-03.json` step 11 expect "Not Found";
  `J-04.json` steps 8-9 expect "404". Rewrite all three IN the iteration that ships the route.
- New MINOR (evaluator, iter-4): `test_tape_observation_path_equivalence.py::test_counterexample_field_partition_drift_is_detected`
  compares two hand-written literals, never the real constant — vacuous counter-example; fix it.

## Last 2 verdicts

- iter 4: CONTINUE — J-04 failing→partial; new `test_tape_observation_path_equivalence.py` (replay
  leg vs live leg, per-tick) re-run by evaluator 6/6; full suite 4036 pass / 8 skip / 0 fail; tsc 0;
  `observation_contract.py` byte-identical to iter-1; scan CLEAN; coherence PASS.
- iter 3: CONTINUE — J-03 failing→partial; per-watch source/session descriptor + `_settle` identity
  fix; suite 4039 collected / 0 fail / 8 skip; scan CLEAN; coherence PASS.

## Do not redo

- Step 1 DONE (iter-1): `app/observation_contract.py` (schema/partition constants, `canonical_encode`,
  both hash laws, `build_tape_observation`) + `tests/test_tape_observation_projection.py`. Byte-identical since.
- Step 2 DONE (iter-2): atomic settled pair, `_settle`, `_iso_utc`, `tests/test_tape_observation_time.py`
  (iter-4 made its ISO check three-way incl. `main._iso_utc` — coherence advisory CLOSED).
- Step 3 DONE (iter-3): `SourceDescriptor` + `_record_source` at all four `watch*` constructors,
  `get_observation_source` 4-tuple, `tests/test_tape_observation_lifecycle_feed.py` (iter-4 removed its one vacuous summary test — reviewer MINOR CLOSED; 29 tests, all 7 statuses still from real calls).
- Step 4 DONE (iter-4): `tests/test_tape_observation_path_equivalence.py` — PG SIP fixture + seeded sim
  scenario, replay leg vs live leg, equal `observation_hash` at every tick, partition unwidened.
- Do not re-pin: fingerprint `08e471b10130e1e2`, suite 4036 pass / 8 skip / 0 fail, tsc 0 errors. No
  frontend work; no `Config` field; do not touch the nine protected guard files.
