# Iteration Summary — goal-observation-contract-iter-1

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-09-03
**Iteration:** 1

## In plain words

**What you can do now:** Watch live simulated or historical tape data on the Cockpit page, browse market structure on the Structure page, and review desk screens on the Desk page — same as before. The new observation-summary feature is not usable by a person yet; it is still being built behind the scenes.

**What changed this time:** No page changed. Behind the scenes, the backend gained the core piece that builds one trustworthy "observation" snapshot of the tape, complete with two tamper-evident fingerprints (one for the trading facts, one for the whole record) — but nothing serves it to a screen or web address yet, so opening `/tape/SIM-BIDABS/observation` still answers "Not Found," exactly as before.

**What's next:** Next, the system will learn to read time honestly — pinning the moment something happened, the moment it was noticed, and the moment the report was written, all from one single, tamper-proof snapshot, so those three clocks can never quietly disagree. This stays invisible groundwork; no new screen or button yet.

## Headline

Built the first block of the goal's required order: schema constants, the pure builder, and the two hash rules.

## Direction

**Signal:** holding
**Why:** J-01 ("the pure-projection observation artifact") moved from failing to partial this iteration: the new builder module and its 38/0-passing test file are real, verified progress inside the goal's mandated build order. No journey reached passing because the goal's own required sequence intentionally defers the served web address to iteration 5, so J-02 through J-05 stay failing by design, not by fault. Nothing regressed (0 anti-goal violations, full suite still green at 3968/8/0), and with only two iterations recorded there is no 3-iteration stall window yet, so the project is holding a steady, on-plan pace rather than stalling or regressing.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** This iteration built the first block of the goal's required build order: the schema constants, the one pure builder, the two hash rules and their own test file. I checked the work myself rather than trusting the reports. The new test file runs 38 checks and all 38 pass, including the five "counter-example" checks that prove the guards can actually fail. The whole backend test set still passes (3968 pass, 8 skipped, 0 fail), which I ran end to end myself.

## What was done

- Product changes: apps/backend/app/engine/tape_engine.py, apps/backend/app/observation_contract.py, apps/backend/tests/test_tape_observation_projection.py
- Added the `ENGINE_SEMANTICS_VERSION` module constant to `tape_engine.py` (owner-act versioning per Constitution §6).
- Built `observation_contract.py`: schema constants, the four-group field partition, canonical encoding, both hash laws (`observation_hash`, `artifact_hash`), a memoized git-provenance resolver, and the pure `build_tape_observation` function producing the full v1 schema.
- Added `test_tape_observation_projection.py` — 38 tests (TC-1..TC-13), each guard/law paired with a required `test_counterexample_*` proving it can fail.
- Re-verified the full backend suite: 3968 passed / 8 skipped / 0 failed; `config_fingerprint` unchanged (`08e471b10130e1e2`); `tsc --noEmit` 0 errors.
- Verified 1/1 target journey check passes browser QA (UT-J-01: Sim-mode live watch, plus confirmed `/tape/SIM-BIDABS/observation` still 404s as expected).

## What's left

- Journey J-01 ("the artifact is a pure projection with semantic identity, provenance and integrity") partial — the served JSON route `/tape/{ticker}/observation` is still missing (planned for iteration ~5)
- Journey J-02 ("market-event time, measured availability and generation time are three distinct, honest instants, read atomically") failing — the watch manager's atomic settled-time read is not yet built
- Journey J-03 ("lifecycle, feed basis and session identity stay honest") failing — not yet targeted
- Journey J-04 ("ingestion-path equivalence under an identical valid event stream") failing — not yet targeted
- Journey J-05 ("one read-only machine path") failing — the served route doesn't exist yet
- Journey J-06 ("guards and the regression sentinel") partial — the dedicated guard-test module (`test_tape_observation_guards.py`) is still missing

## Next step

Build the next block in the goal's required order: J-02, "Market-event time, measured availability and generation time are three distinct, honest instants, read atomically." That means the watch manager holding the settled pair and handing out both values in one atomic read, the three time fields and `availability_basis` wired to real measured values, the interleaving test, the check that the engine folder reads no clock, and the new file `apps/backend/tests/test_tape_observation_time.py`. Keep the web address for later — it is step 5, and moving it earlier only to make a journey look green is explicitly forbidden by the goal. Next iteration should run at lean depth: backend only, no page or button changes, so the heavy review-and-audit pipeline is not needed.

## Assumptions made

- iter-2 · goal-decomposer — Ambiguity: the Binding Execution Order's step 2 names `get_observation_source` as J-02's deliverable, but Key Capability 3 describes a fuller return shape (source/session descriptor, lifecycle, provenance) that step 3 separately owns; unclear whether the method must return the full descriptor-bearing shape this iteration or a narrower one iteration 3 extends. We chose: introduce `get_observation_source(ticker)` returning only what the atomic settled pair itself carries (the settled snapshot, `settled_at_utc`, `end_reason`); the descriptor fields get added onto the same method by iteration 3 without re-reading the pair. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's Acceptance is a conjunction (the served JSON route AND the passing test file); the iter spec itself left scoring open between still-failing or partial. We chose: `partial` — steps 1/4/5 verified met, steps 2/3 verified unmet (the route 404s), matching the "only some assertion steps passed" convention already used for J-06. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: the Binding Execution Order's step 1 language is unclear whether `build_tape_observation` should be a partial function this iteration or must already produce the complete v1 schema, since separate steps 2/3 name the time and lifecycle/provenance fields. We chose: build the COMPLETE v1 schema this iteration (including the pure-math time/lifecycle/source projections), accepting already-resolved values as parameters, while the machinery that makes those values genuinely correct is left to iterations 2/3/5 — required for the four-group partition-coverage trap to be satisfiable at all this iteration. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-06 also requires the full backend suite recorded green, but browser QA's own re-run did not finish and honestly recorded `unknown`. We chose: to treat the developer's and reviewer's independent full runs plus my own re-collection as sufficient evidence the foundation is unchanged, while still leaving J-06 `partial` on the missing guard module. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-06's Acceptance is one long conjunction and the goal text doesn't say how to score a journey whose sub-checks split. We chose: `partial` in journey-history (not `failing`), because the era-open and unchanged-pages sub-checks are genuinely verified done and only the guard-test file is missing. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-observation-contract-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-observation-contract-iter-1-dev.md |
| Review | PASS | reports/reviews/goal-observation-contract-iter-1-review.md |
| Browser QA | PASS | reports/phase-goal-observation-contract-iter-1-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-observation-contract/iter-1/eval.md |
| Journey history | — | runs/goal-session-observation-contract/state/journey-history.json |
