# Iteration State — observation-contract

**After iteration:** 5 · **Date:** 2026-09-05 · **Verdict:** ESCALATE

## Journeys

4 passing (J-01 J-02 J-03 J-05) · 0 failing · 2 partial (J-04 J-06) — 6 total

## Active blockers

- None human-owned. Dev-owned, last of the required order: `tests/test_tape_observation_guards.py` (J-06, step 6) + whole-product re-check (full suite, `tsc --noEmit`, fingerprint, `/` `/structure` `/desk` unchanged). J-06 was NOT tested this round (row `DEFERRED-BUDGET`).
- J-04 partial for EVIDENCE only (its 6 tests pass, no browser opened the URL): watch SIM-BIDABS → Pause → reload `/tape/SIM-BIDABS/observation` twice → same `observation_hash`, different `generated_at_utc`/`artifact_hash`, screenshot each. J-02 passed on a capture filed under J-01's test id — re-run J-02's own steps too (assumptions.md).
- TOOLING (framework-owned, not product): `replay-lane.sh` runs `demo_runner.py --base-url $FRONTEND_URL` and `normalize_url()` rewrites even absolute `:8301` URLs onto it → every golden `goto` to `/tape/*/observation` renders Next.js 404 and false-FAILs (proof: `J-01/J-03/J-04-verify.png` are one byte-identical image). Queued: `goldens-regen-pending` (J-01 J-03 J-04), `golden-gaps` (J-05). Until fixed these journeys MUST ride the LLM browser-qa lane against `:8301`.

## Last 2 verdicts

- iter 5: ESCALATE — route `GET /tape/{ticker}/observation` landed (`main.py` + 2 test files); J-05 failing→passing, J-01/J-02/J-03 partial→passing on real served-JSON screenshots; my own run of the 5 observation modules = 114 pass / 0 fail; fingerprint 08e471b10130e1e2; scan CLEAN; coherence PASS. Escalated: replay lane can't reach backend URLs, J-04+J-06 unverified, next is the closure block.
- iter 4: CONTINUE — J-04 failing→partial; path-equivalence module 6/6; suite 4036 pass / 8 skip / 0 fail.

## Do not redo

- Steps 1-4 DONE (iters 1-4), unmodified this round: `observation_contract.py` + projection tests; atomic settled pair + `get_observation_source` + time tests; `SourceDescriptor` + lifecycle/feed tests; path-equivalence tests.
- Step 5 DONE (iter-5): `get_observation` + `_now_utc` in `app/main.py` (transport only — atomic read → `build_tape_observation`; AST guard + non-vacuous counter-example prove no `TapeEngine` call) plus `tests/test_tape_observation_route.py` (8 tests: MCP byte-equality vs real uvicorn, 404 parity, frozen-`now` equality, hash recompute, 100-request no-git-call).
- FIXED (iter-5): `test_counterexample_field_partition_drift_is_detected` now monkeypatches the REAL `MACHINE_OBSERVATION_SEMANTIC_FIELDS`. Goldens J-01/J-03/J-04 already rewritten off the stale "Not Found"/"404" text — the remaining problem is the runner's origin, not the assertions.
- Do not re-pin: fingerprint `08e471b10130e1e2`, suite 4044 pass / 8 skip / 0 fail, tsc 0 errors; no frontend work; no `Config` field; do not touch the nine protected guard files.
