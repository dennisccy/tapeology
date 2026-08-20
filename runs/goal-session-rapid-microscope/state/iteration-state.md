# Iteration State — rapid-microscope

**After iteration:** 21 · **Date:** 2026-08-20 · **Verdict:** ESCALATE

## Journeys

8 passing (J-01 J-02 J-03 J-04 J-05 J-07 J-08 J-10) · 2 partial (J-06, **J-09 — was failing**) — 10 total.
J-09 failing→partial: study 2 of 3 screened + ledgered (`killed_insufficient_n`). J-07 NOT tested (`DEFERRED-BUDGET`, keeps its iter-20 stamp). Suite 3,316 pass / 8 skip / 0 fail (evaluator ran it).

## Active blockers

- **J-09 needs Studies 1 + 3 screened** on the SAME committed hermetic fixture study 2 used (`scout.pilot_study_candidate_grid`: `PILOT_STUDY_RANGE_WALL_FAILED_AGGRESSION` / `PILOT_STUDY_CAPITULATION_EXHAUSTION`) → recorded decisions; `insufficient_n` / `no survivor` are passing answers. Study 1 also needs two-feature (`failed_aggression_score` × `refill_consistent`) co-occurrence, named unbuilt in the grid's own comment. Owner: dev.
- **UT-04 evidence owed** (dev): the auditor's own B1 fix (`run_scout_grid_and_record` gains `exposure_registry`) is the only lane that has checked itself. Photograph the second ledger row (`stage: walkforward_floor_check`) or J-09 stays `partial`.
- **/desk readiness GET costs 22.3 s** on the real store (auditor B2, unfixed by design): `micro_routes.py:108` + `micro_join.py:639-643` re-parse every dataset per request. Fix = durable cache keyed `(dataset checksum, resolver map key)`, publish ONLY on a resolved map, never memoize a miss; mirror `MicroReadinessCache` (`micro_readiness.py:414-418`). Shed THIS first if the clock bites — never the two re-verifications.
- **HUMAN, unchanged:** sealed judge's econ-floor / evidence-label sourcing (no spec revision after r9); J-06 step 4 real Alpaca tranche recording.

## Last 2 verdicts

- iter 21: ESCALATE — J-09 partial; a FAIL browser verdict (UT-04) still closed the round (`closure_gate.py` never reads it) and only the auditor fixed it. Budget was breached, so CONTINUE would FORCE lean (`run-goal.sh` arbiter rung 3). **Keep the next round SMALL.**
- iter 20: ESCALATE — clean evidence-only round; J-07's owed capture landed and is discriminating.

## Do not redo

- **DONE iter-21, proved by the evaluator:** J-10.json steps 9-10 restored AND executed twice (UT-08 + golden replay); UT-10 element capture re-taken (UT-06, real panel text); guard/source-scan for zero micro/scout/walkforward/vault callers of `strategy_trade_readiness`.
- **Frozen foundations re-proved iter-21** — fingerprint `08e471b10130e1e2`, zero `referee_*.py` modified, MCP tools == 26, TR-1…TR-30 green (TR-17 exists only as TR-17a/b/c).
- **The "defer up to two of three studies" allowance is SPENT** — a third deferral is not available.
- **Do NOT** run the pilot grid against the real `.data/` store (quadratic divergence anchor extraction, uncancellable mid-candidate — auditor B3, deferred); do NOT author a J-07 golden script (impossible, iter-19); do NOT touch `econ_floor`, `referee_*`, or the `iter18-qa-universe` vault assertions.
- **Rig rule now covers the DEMO lane too:** rig-mutating browser tests (POST `/scout/compute`) invalidate `J-08.json` step 3 / `J-10.json` step 12 "No candidates ledgered." for every later lane.
