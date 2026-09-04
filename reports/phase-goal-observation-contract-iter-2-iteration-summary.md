# Iteration Summary — goal-observation-contract-iter-2

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-09-03
**Iteration:** 2

## In plain words

**What you can do now:** Watch live simulated or historical tape data on the Cockpit page, look at market structure on the Structure page, and check desk screens on the Desk page — unchanged from before. The new observation-summary feature still isn't usable by anyone; it's being built piece by piece behind the scenes.

**What changed this time:** No page changed. Behind the scenes, the part of the system that watches live tape data now keeps one paired, tamper-safe record of "the tape's picture" and "the exact moment it was confirmed" — read together, atomically, so the two can never quietly drift apart or get mismatched. That's the plumbing needed before the system can honestly answer "when did we actually know this?" But nothing is served to a screen or web address yet, so opening `/tape/SIM-BIDABS/observation` still answers "Not Found," exactly as before.

**What's next:** Next, the system will learn each watch's real source and session story — where the data came from and which session it belongs to — and keep its status wording honest at every stage, including fixing a small, currently-harmless bug where a just-restarted watch could briefly show data left over from an old one. Still no new screen or button yet.

## Headline

Built the second block of the goal's required order: the watch manager's atomic settled-time read.

## Direction

**Signal:** holding
**Why:** J-02 ("three honest time instants, read atomically") moved from failing to partial this iteration — the watch manager's new atomic settled-pair read and its 33/33-passing test module are real, verified progress inside the goal's mandated build order. No journey reached passing because the goal's own required sequence intentionally defers the served route to iteration 5, so J-03, J-04 and J-05 stay failing by design, not by fault. Nothing regressed (0 anti-goal violations, full suite still green at 4001/8/0) and a journey changed state again this iteration (unlike a 3-iteration stall window), so the project is holding a steady, on-plan pace.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: none
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: none
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** This round built the second block of the goal's required build order: the watch manager now keeps one paired record of "the tape picture" and "the moment the system settled it," and hands both back together. I re-ran the new test file myself: 33 checks, all pass, including every "counter-example" check that proves the rules can really fail. I also re-ran the whole backend test set myself: 4001 pass, 8 skipped, 0 fail — the earlier 3968 plus exactly the 33 new ones — and the settings fingerprint still reads 08e471b10130e1e2.

## What was done

- Product changes: apps/backend/app/watch_manager.py, apps/backend/tests/test_tape_observation_time.py
- Gave `WatchManager` one atomic per-ticker settled pair (snapshot + settled time), written by a single `_settle` helper reached from every feeder path, `pause()`, `resume()`, and every lifecycle-only status flip.
- Added `WatchManager.get_observation_source(ticker)` — returns the settled snapshot, pinned-ISO `settled_at_utc`, and `end_reason` from that one atomic read; `None` for an unwatched ticker.
- Added a cold-reset at every fresh-engine construction so a re-watched ticker never reads a stale settled pair left over from its prior watch (documented design decision, reviewer-approved).
- Added `test_tape_observation_time.py` — 33 new tests (TC-1..TC-13), including every required counter-example test and the atomic-read interleaving proof.
- Re-verified the full backend suite: 4001 passed / 8 skipped / 0 failed (iter-1's 3968 + these 33 new); config fingerprint unchanged (`08e471b10130e1e2`); `tsc --noEmit` 0 errors.
- Verified 1/1 target journey-scoped browser check passes (UT-J-02: live Sim watch, `/tape/SIM-BIDABS/observation` still 404s as expected, `/structure`/`/desk` render unchanged, Watch/Pause/Resume/Stop regression smoke).

## What's left

- Journey J-03 ("Lifecycle, feed basis and session identity stay honest") failing — not yet targeted
- Journey J-04 ("Ingestion-path equivalence under an identical valid event stream") failing — not yet targeted
- Journey J-05 ("One read-only machine path") failing — the served route doesn't exist yet
- Journey J-01 ("The artifact is a pure projection with semantic identity, provenance and integrity") partial — still missing the served route
- Journey J-02 ("Market-event time, measured availability and generation time are three distinct, honest instants, read atomically") partial — the test half is done; the served route is still missing
- Journey J-06 ("Guards and the regression sentinel") partial — the dedicated guard-test module (`test_tape_observation_guards.py`) is still missing
- Reviewer's one MINOR finding: `_settle` writes are keyed only by ticker with no check that the engine passed in is still the currently-registered one, so a stale feeder's deferred cleanup could transiently overwrite a freshly re-watched ticker's settled pair during a live switch — inert today (nothing reads `get_observation_source` yet) but must be hardened before the route lands at iteration 5

## Next step

Move to the next block of the goal's required order — J-03, "Lifecycle, feed basis and session identity stay honest": give each watch a real source and session description (mode, scenario, window, session id, session start, data feed), keep the lifecycle wording honest across the seven statuses, and add the new test file `apps/backend/tests/test_tape_observation_lifecycle_feed.py`. Fold in the reviewer's one MINOR finding while that file is open: the settle helper writes into the store using only the ticker name, so an old, cancelled feed can briefly overwrite a freshly restarted watch's record; add the "is this still the current engine" check and a test that switches a watch while the old feed is genuinely still running (`apps/backend/app/watch_manager.py:341`). This must be fixed before the web address is built at step 5, because that is when a reader would first see the wrong pair. Still do not build the web address early. Next iteration should be lean and backend-only, with no visible change on screen.

## Assumptions made

- iter-2 · goal-decomposer — Ambiguity: the Binding Execution Order's step 2 names `get_observation_source` as J-02's deliverable, but Key Capability 3 describes its return as carrying the settled `EngineSnapshot`, source/session descriptor, settled wall-clock time and `end_reason`, and step 3 separately owns the descriptor/lifecycle/provenance fields; unclear whether `get_observation_source` must return the full descriptor-bearing shape this iteration or a narrower one iteration 3 extends. We chose: introduce `get_observation_source(ticker)` returning only what the atomic settled pair itself carries (the settled snapshot, `settled_at_utc`, `end_reason`), with the source/session descriptor fields added onto the same method by iteration 3 without re-reading the pair. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's Acceptance is a conjunction (the served JSON route AND the passing test file); the iter spec itself left scoring open between still-failing or partial. We chose: `partial` — steps 1/4/5 verified met, steps 2/3 verified unmet (the route 404s), matching the "only some assertion steps passed" convention already used for J-06. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: the Binding Execution Order's step 1 language is unclear whether `build_tape_observation` should be a partial function this iteration or must already produce the complete v1 schema, since separate steps 2/3 name the time and lifecycle/provenance fields. We chose: build the COMPLETE v1 schema this iteration (including the pure-math time/lifecycle/source projections), accepting already-resolved values as parameters, while the machinery that makes those values genuinely correct is left to iterations 2/3/5 — required for the four-group partition-coverage trap to be satisfiable at all this iteration. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-06 also requires the full backend suite recorded green, but browser QA's own re-run did not finish and honestly recorded `unknown`. We chose: to treat the developer's and reviewer's independent full runs plus the evaluator's own re-collection as sufficient evidence the foundation is unchanged, while still leaving J-06 `partial` on the missing guard module. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-06's Acceptance is one long conjunction and the goal text doesn't say how to score a journey whose sub-checks split. We chose: `partial` in the journey tracker (not `failing`), because the era-open and unchanged-pages sub-checks are genuinely verified done and only the guard-test file is missing. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-observation-contract-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-observation-contract-iter-2-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-observation-contract-iter-2-review.md |
| Browser QA | PASS | reports/phase-goal-observation-contract-iter-2-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-observation-contract/iter-2/eval.md |
| Journey history | — | runs/goal-session-observation-contract/state/journey-history.json |
