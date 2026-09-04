# Iteration Summary — goal-observation-contract-iter-4

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-09-04
**Iteration:** 4

## In plain words

**What you can do now:** You can still watch live simulated or historical tape data on the Cockpit page, look at market structure on the Structure page, and check desk screens on the Desk page — all working the same as before. The new observation-record feature is still not reachable by anyone; it is being built piece by piece behind the scenes.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The team added tests proving that watching a ticker live and replaying the exact same recorded market data produce the exact same honest observation record, even though the two ways of receiving the data are very different underneath.

**What's next:** Next, the team will open the one web address that finally lets a screen or another program read each ticker's observation record.

## Headline

Proved the tape engine sees the same thing whether events arrive via replay or live path

## Direction

**Signal:** holding
**Why:** J-04 "Ingestion-path equivalence under an identical valid event stream" moved from failing to partial — its new equivalence proof (6/6 tests, including a genuine mutation counter-example) is real, verified progress inside the goal's mandated build order, matching the same failing-to-partial pattern already seen for J-01 (iter-1), J-02 (iter-2) and J-03 (iter-3). No journey reached passing because the goal's own required sequence intentionally reserves the served route (J-05) for iteration 5; J-05 stays failing by design, not by fault. Nothing regressed (0 anti-goal violations, full suite still green at 4036/8/0) and a journey converted state again this iteration for the fourth iteration running, so direction is holding a steady, on-plan pace toward the goal.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: none
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** This round proved, with tests only, that the tape engine sees the same thing whether the same recorded events arrive by the replay path or by the live path. I re-ran the new test file myself: 6 checks, all pass, including the one that deliberately breaks a value and shows the comparison can fail. I also re-ran the whole backend test set myself: 4036 pass, 8 skipped, 0 fail, and the settings fingerprint still reads 08e471b10130e1e2. Nothing users can see changed, and the web address `/tape/SIM-BIDABS/observation` still answers "404", which is correct for this round because that address is only built next round.

## What was done

- No product change this iteration.
- Added `apps/backend/tests/test_tape_observation_path_equivalence.py` (6 new tests) proving the replay-path leg and the live-path leg produce identical `observation_hash` values and semantic fields at every captured tick, on both the real PG SIP market-data fixture (14,241 events) and a seeded simulator scenario (120 events).
- Included a genuine mutation counter-example test proving the comparison can actually fail, plus a check confirming the four-group field partition is unchanged from iteration 1 (no widening to manufacture a false match).
- Removed a vacuous test in `test_tape_observation_lifecycle_feed.py` that asserted only a hand-written literal list and never called `WatchManager`; the coverage it claimed already existed via nine real tests directly above it.
- Extended `test_tape_observation_time.py`'s ISO-timestamp check into a three-way comparison that now also includes `main._iso_utc`, closing the coherence-auditor's carried-forward advisory from iteration 3.
- Full backend suite re-verified at 4036 passed / 8 skipped / 0 failed (net +5 over iteration 3's baseline); settings fingerprint unchanged at `08e471b10130e1e2`; frontend type check clean (0 errors).
- Verified the iteration's target journey (J-04) passes browser QA on its regression-smoke scope: the Watch → Pause → Resume → Stop cycle behaves unchanged, and the not-yet-built observation route still honestly answers 404 across two reloads.

## What's left

- Journey J-05 (One read-only machine path) failing — the `/tape/{ticker}/observation` route itself is not yet built; reserved for the next iteration.
- Journey J-01 (The artifact is a pure projection with semantic identity, provenance and integrity) partial — its test module passes; the served-JSON half is still missing.
- Journey J-02 (Market-event time, measured availability and generation time are three distinct, honest instants, read atomically) partial — same served-JSON gap.
- Journey J-03 (Lifecycle, feed basis and session identity stay honest) partial — its test module passes; the served-JSON half is still missing.
- Journey J-04 (Ingestion-path equivalence under an identical valid event stream) partial — its new equivalence-proof test module passes; the served-JSON half is still missing.
- Journey J-06 (Guards and the regression sentinel) partial — the reusable guard-suite module (`test_tape_observation_guards.py`) is still absent; reserved for iteration 6.
- One small test-quality gap: `test_counterexample_field_partition_drift_is_detected` compares two hand-written lists to each other and never reads the real values, so it would still pass even if the real list were deleted.
- Three saved replay scripts (`J-01.json` step 5, `J-03.json` step 11, `J-04.json` steps 8-9) still expect the observation route to be missing; they must be rewritten once the route ships next iteration.

## Next step

Build the web address next: `GET /tape/{ticker}/observation` plus its test file `tests/test_tape_observation_route.py`, which is J-05 "One read-only machine path" and step 5 of the goal's required order. This is the round where five journeys finally become checkable in the browser, so please note three things for it. First, the address must read the watch manager's single atomic read and must never touch the engine directly — the goal calls that mistake a critical violation. Second, three saved replay scripts still expect this address to be MISSING (`journey-scripts/J-01.json` step 5 and `J-03.json` step 11 expect "Not Found"; `J-04.json` steps 8-9 expect "404"); they must be rewritten in the same round the address starts working, or later automatic replays will report false failures. Third, one small test-quality fixup: in `apps/backend/tests/test_tape_observation_path_equivalence.py` the check named `test_counterexample_field_partition_drift_is_detected` compares two hand-written lists to each other and never reads the real values, so it would still pass if the real list were deleted — it is the same empty-check shape this round just removed elsewhere. In one sentence: next round should build and serve the observation address, refresh the three replay scripts that assume it is absent, and repair that one empty check.

## Assumptions made

- iter-4 · goal-evaluator — Ambiguity: the era anti-goal against pooling, equating or silently converting between sim, iex and sip data seems to conflict with the goal's own requirement to feed the seeded sim scenario through both the replay feeder and the live feeder for the equivalence proof. We chose: to score this anti-goal OK — the two feed bases stay distinct and are never pooled, equated, or served; the comparison exists only inside the new test file, and any later iteration that serves an artifact built this way would need this call revisited. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: only one screenshot was captured for a five-step browser sequence; unclear whether that counts as a capture defect or just incomplete evidence. We chose: not to flag it as evidence_makeup — J-03 is partial for a substantive reason (the route is absent) and its full browser evidence will be re-taken once the route ships. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-03's literal steps read fields from a served route that doesn't exist until iteration 5, so browser QA scored its one row PASS on a narrowed regression-smoke scope instead of the journey's literal steps. We chose: to accept that row as evidence only for the browser sub-steps it actually executed, treating every JSON-field assertion as unmet, so J-03 stays partial, never passing. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: one required trap-coverage item ("no actionability field or token") is listed under both J-03 and J-06, but the reusable guard module is reserved for iteration 6; unclear whether J-03's own test module must build a second independent scan now. We chose: J-03's own test module ships a scoped check over one fully-built artifact for the same fixed token list, while the general-purpose guard remains iteration 6's own module. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the goal lists profile_id among the manager-owned fields recorded at watch creation, but no live/replay watch path currently supports profile selection; unclear whether this iteration's descriptor must store it or a later route can supply it inline. We chose: to store profile_id as a constant field of the same per-ticker descriptor recorded at watch creation, matching the goal's literal wording. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: the goal's required order names get_observation_source as J-02's deliverable, but a separate section describes its return as also carrying the source/session descriptor, which a later step separately owns; unclear whether it must return the full shape now or a narrower one iteration 3 extends. We chose: to introduce get_observation_source at iteration 2 returning only what the atomic settled pair itself carries, with the descriptor fields added by iteration 3 without re-reading the pair. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance is a conjunction (served JSON + a passing test module), and the iteration spec itself left the scoring open between still-failing and partial when one half is met and the other is blocked by the goal's own required build order. We chose: partial — the test-module half verified met, the served-JSON half verified unmet — matching the convention already applied to J-06. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: the goal's required order groups the "builder" with early constants and hash rules, while later steps separately name the time and lifecycle/provenance fields; unclear whether the builder should be a partial function this iteration or must already produce the complete record shape. We chose: the builder produces the complete record shape this iteration, accepting already-resolved values as parameters, while the machinery that makes those values genuinely correct is left to later iterations. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-06 also requires the full backend suite recorded green, but browser QA's own re-run did not finish and honestly recorded unknown. We chose: to treat the developer's and reviewer's independent full runs plus the evaluator's own re-collection as sufficient evidence the foundation is unchanged, while still leaving J-06 partial on the missing guard module. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-06's acceptance is one long conjunction (pages unchanged + documents exist + guard suite green + full suite green + fingerprint pinned); the merged results row recorded FAIL, but the goal text doesn't say how to score a journey whose sub-checks split. We chose: partial in the journey tracker (not failing), because the era-open and unchanged-pages sub-checks are genuinely verified done and only the guard-test file is missing. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-observation-contract-iter-4.md |
| Dev handoff | — | docs/handoffs/goal-observation-contract-iter-4-dev.md |
| Review | PASS | reports/reviews/goal-observation-contract-iter-4-review.md |
| Browser QA | PASS | reports/phase-goal-observation-contract-iter-4-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-observation-contract/iter-4/eval.md |
| Journey history | — | runs/goal-session-observation-contract/state/journey-history.json |
