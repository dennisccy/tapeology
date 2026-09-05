# Iteration State — observation-contract

**After iteration:** 6 · **Date:** 2026-09-05 · **Verdict:** CONTINUE

## Journeys

6 passing (J-01 J-02 J-03 J-04 J-05 J-06) · 0 failing · 0 partial · 0 unknown — 6 total

## Active blockers

- ONE bookkeeping blocker, dev/QA-owned, no code needed: J-05's own row in `reports/phase-goal-observation-contract-iter-6-ui-test-results.md` is `DEFERRED-BUDGET` (shed for wall-clock budget). `goal_gate.py results` blocks GOAL_ACHIEVED on that ROW (rc 1) even though `goal_gate.py journeys` returns 6/6 passing. Fix = one `evidence`-depth round that re-opens `/tape/SIM-BIDABS/observation` (watched, live) and `/tape/ZZZZ/observation` in the LLM browser-qa lane and screenshots both. Run the cheap already-passing rows FIRST this time.
- TOOLING (framework-owned, NOT product, do not fix here): `replay-lane.sh` + `demo_runner.py normalize_url()` rewrite absolute `:8301` URLs onto the frontend origin → goldens for `/tape/*` false-FAIL (J-01/J-03 again this round; `J-01-verify.png` == `J-03-verify.png`, md5 `cdcf05e2…`). Voided by the mass-false-FAIL breaker + a dated reconciliation footer. `J-02.json` is the mirror risk: a false PASS (it never opens the address). `goldens-regen-pending` (J-01 J-03 J-04) and `golden-gaps` (J-05) stay QUEUED, not actioned.
- Audit GAPs, open and non-blocking, ledger stays 0/0/0/0/0: mutator scan sees only a receiver named `engine` (B2); external-system scan covers only `.py/.ts/.tsx/.js` under `apps/` (B3); counter-example bodies blanked before the copy-discipline scan (B4); real-provider isolation is per-module, not transitive (B5); English-only counter-test perturbs a real-derived container, not a real file (T1). None hides anything today (auditor verified empirically). Do NOT open new work for these.

## Last 2 verdicts

- iter 6: CONTINUE — guard module landed (`tests/test_tape_observation_guards.py`, 23 tests after the auditor's in-iteration B1 fix); J-04 and J-06 partial→passing on evidence I opened (paused-reload pair: identical `observation_hash`, differing `generated_at_utc`/`artifact_hash`; three pages unchanged, 3-link nav). My own runs: guard 23/23, full suite exit 0 (4075 collected = 4067 pass + 8 skip), tsc 0, fingerprint `08e471b10130e1e2`. Scan CLEAN, coherence PASS. Held back ONLY by J-05's deferred row.
- iter 5: ESCALATE — route `GET /tape/{ticker}/observation` landed; J-05 failing→passing, J-01/J-02/J-03 partial→passing; replay lane can't reach backend URLs; J-04/J-06 unverified.

## Do not redo

- Binding Execution Order steps 1-6 are ALL DONE and verified: `observation_contract.py` + projection tests (iter-1); atomic settled pair + `get_observation_source` + time tests (iter-2); `SourceDescriptor` + lifecycle/feed tests (iter-3); path-equivalence tests (iter-4); `get_observation` route in `app/main.py` + `test_tape_observation_route.py` (iter-5); `test_tape_observation_guards.py` — five mechanisms + counter-tests (iter-6).
- FIXED iter-6 (auditor, test-only): the mutator-call-site guard now requires RE-SETTLING, not just location — `_settling_method_names()` derives the allowed set from `watch_manager.py`'s own AST, with one documented carve-out (`WatchManager.stop`, which deletes the engine). Its counter-test splices a non-settling method into a copy of the REAL file. Do not re-open or re-weaken.
- Do NOT duplicate the recompute guard in the guards module — it already lives in `test_tape_observation_projection.py:160` (assumptions.md, iter-6 decomposer).
- Do NOT rebuild or re-verify anything for J-06's era-open clause: `docs/goal-archive/goal-2026-09-02.md`, the 2026-09-02 opening note in `docs/research-directions.md`, `docs/observation-contract-spec.md` all exist.
- Do not re-pin and do not change: fingerprint `08e471b10130e1e2`, MCP 28-tool contract, suite 4067 pass / 8 skip / 0 fail, tsc 0 errors; zero frontend files; no new `Config` field; the nine protected guard files stay unedited.
- No product code is needed to finish this era. The next round builds NOTHING.
