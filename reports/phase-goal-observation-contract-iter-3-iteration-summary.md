# Iteration Summary — goal-observation-contract-iter-3

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-09-04
**Iteration:** 3

## In plain words

**What you can do now:** You can watch live simulated or historical tape data on the Cockpit page, browse market structure on the Structure page, and review desk screens on the Desk page. These all work the same as before.

**What changed this time:** Nothing changed on any screen this round. Behind the scenes, the system that watches live tape data now keeps an honest record of where each watch's data comes from and which watching session it belongs to. It also fixes a bug where a freshly restarted watch could briefly show a leftover reading from the watch it replaced.

**What's next:** Next, the team will prove that live watching and replaying the same recorded data give the same honest reading.

## Headline

This round built the third block of the goal's required order and it works.

## Direction

**Signal:** holding
**Why:** J-03 "Lifecycle, feed basis and session identity stay honest" moved from failing to partial — its new test module (30/30 passing) and a real `_settle` stale-write fix landed, but its served-JSON half stays gated on the route the goal's binding order reserves for iteration 5. This is the fourth consecutive lean, backend-only iteration where a new journey converts to partial on schedule (J-01 at iter-1, J-02 at iter-2, J-03 at iter-3) with zero regressions and a clean anti-goal scan, so the project is proceeding exactly as planned even though no journey has yet reached full `passing` status.

**Trend (last 4 iters):**
- Newly passing this iter: none
- Newly passing in last 4 iters total: none
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 0 of last 4

**Latest evaluator reasoning:** I checked the work myself instead of trusting the reports. My own run of the new file `apps/backend/tests/test_tape_observation_lifecycle_feed.py` gives 30 checks, all pass, including the five "counter-example" checks that prove the rules can really fail. My own run of the whole backend test set finishes clean (4039 checks collected, 0 failures, 8 skipped) — the previous 4009 plus exactly the 30 new ones — the settings fingerprint still reads 08e471b10130e1e2, and the frontend type check reports 0 errors.

## What was done

- Product changes: apps/backend/app/watch_manager.py, apps/backend/app/main.py, apps/backend/tests/test_tape_observation_lifecycle_feed.py, apps/backend/tests/test_tape_observation_time.py
- Added `WatchManager.SourceDescriptor` and `_record_source`, recording each watch's source/session details (mode, feed, window, session id/start, profile) once per fresh engine across all four watch constructors.
- Widened `get_observation_source(ticker)` to also return the descriptor alongside the existing settled snapshot pair, with no re-fetch.
- Fixed the carried-forward stale-write race: `_settle` now silently skips its write when the calling engine is no longer the currently-registered engine for that ticker.
- Threaded `main.py`'s already-parsed historical watch window into both historical watch constructors via a new byte-matching `_iso_utc` helper.
- Added `apps/backend/tests/test_tape_observation_lifecycle_feed.py` (30 tests, TC-1 through TC-12, including a real async running-task-switch test and five counter-example tests).
- Updated `test_tape_observation_time.py`'s tuple-unpacking for the widened 4-tuple return — mechanical only, no test added, removed, or logically changed.
- Full backend suite: 4031 passed / 8 skipped / 0 failed (iter-2's 4001 baseline plus this iteration's 30 new tests); fingerprint unchanged at `08e471b10130e1e2`; `tsc --noEmit` reports 0 errors.
- Verified the iteration's target journey (J-03) passes browser QA on its regression-smoke scope (1/1) — Watch → Pause → Resume → Stop → Watch cycle and the route's honest 404 both confirmed unchanged on `/`, `/structure`, `/desk`.

## What's left

- Journey J-04 (Ingestion-path equivalence under an identical valid event stream) failing — not yet started; targeted for the next iteration.
- Journey J-05 (One read-only machine path) failing — the `/tape/{ticker}/observation` route itself is not yet built (reserved for iteration 5).
- Journey J-01 (The artifact is a pure projection with semantic identity, provenance and integrity) partial — its test module passes; the served-JSON half is still missing.
- Journey J-02 (Market-event time, measured availability and generation time are three distinct, honest instants, read atomically) partial — same served-JSON gap.
- Journey J-03 (Lifecycle, feed basis and session identity stay honest) partial — its new test module passes (30/30) and the stale-write race is fixed; the served-JSON half is still missing.
- Journey J-06 (Guards and the regression sentinel) partial — the reusable guard-suite module (`test_tape_observation_guards.py`) is still absent (reserved for iteration 6).
- Reviewer's one open MINOR finding: a summary test in the new module asserts a hand-written literal set and never exercises the real code — needs deleting or rewriting.
- Coherence auditor's one open advisory: the new date-formatting helper in `main.py` claims to match two older copies but has no test proving that.

## Next step

Build the next block in the goal's required order: J-04 "Ingestion-path equivalence under an identical valid event stream" — feed one recorded event stream through both the replay path and the live path, capture every tick on both, and prove the content identity matches on both while source and session details honestly differ, adding `apps/backend/tests/test_tape_observation_path_equivalence.py` with its mutation counter-test. While that work is open, also clear two small things found this round: delete or rewrite the summary test at `test_tape_observation_lifecycle_feed.py:513` that only checks a hand-written list of seven words and never runs the real code, and add a three-way check proving the new date-formatting helper in `main.py` genuinely matches its two older copies. Do not build the web address `/tape/{ticker}/observation` early — the goal fixes it as step 5, and a flat journey table for one more round is the expected, correct signal.

## Assumptions made

- iter-3 · goal-evaluator — Ambiguity: only one screenshot was captured for a five-step browser sequence (the final re-watched-live state); unclear whether that counts as a capture defect or just incomplete evidence. We chose: not to flag it as evidence_makeup — J-03 is partial for a substantive reason (the route is absent) and its full browser evidence will be re-taken at iteration 5 once the JSON assertions become checkable. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-03's literal steps read fields from the served JSON at a route that doesn't exist until iteration 5, so browser QA scored its one row PASS on a narrowed regression-smoke scope instead of the journey's literal steps; the goal text doesn't say how to score a row whose scope is deliberately narrower than the journey. We chose: to accept that row as evidence only for the browser sub-steps it actually executed, treating every JSON-field assertion as unmet, so J-03 becomes partial (never passing) — the same convention already applied to J-01 and J-02. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: one required trap-coverage item ("no actionability field or token") is listed under both J-03 and J-06, but the reusable guard module is explicitly reserved for iteration 6; unclear whether J-03's own test module must build a second independent scan this iteration or can defer entirely. We chose: J-03's own test module ships a scoped check over one fully-built artifact for the same fixed token list, satisfying J-03's own acceptance step now, while the general-purpose guard remains iteration 6's own module, built once. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the goal lists `profile_id` among the manager-owned fields recorded at watch creation, but no live/replay watch path currently supports profile selection; unclear whether this iteration's descriptor must itself store `profile_id` or whether iteration 5's route can supply it inline instead. We chose: to store `profile_id` as a constant field of the same per-ticker descriptor recorded at watch creation, matching the goal's literal wording, even though its value never varies yet. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: the goal's required order names `get_observation_source` as J-02's deliverable, but a separate section describes its return as also carrying the source/session descriptor, which a later step separately owns; unclear whether `get_observation_source` must return the full descriptor-bearing shape at iteration 2 or a narrower shape iteration 3 extends. We chose: to introduce `get_observation_source` at iteration 2 returning only what the atomic settled pair itself carries, with the descriptor fields added onto the same method by iteration 3 without re-reading the pair. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance is a conjunction (served JSON + a passing test module), and the iteration spec itself left the scoring open between still-failing and partial when one half is met and the other is blocked by the goal's own required build order. We chose: partial — the test-module half verified met, the served-JSON half verified unmet — matching the "only some steps passed" definition and the same convention already applied to J-06. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: the goal's required order groups the "builder" with early constants and hash rules, while later steps separately name the time fields and the descriptor/lifecycle/provenance fields; unclear whether the builder should be a partial function this iteration or must already produce the complete record shape. We chose: the builder produces the complete record shape this iteration, accepting already-resolved values as parameters, while the machinery that makes those values genuinely correct is left to later iterations. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-06 also requires the full backend suite recorded green, but browser QA's own re-run did not finish and honestly recorded unknown. We chose: to treat the developer's and reviewer's independent full runs plus the evaluator's own re-collection as sufficient evidence that the foundation is unchanged, while still leaving J-06 partial on the missing guard module regardless. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-06's acceptance is one long conjunction (pages unchanged + documents exist + guard suite green + full suite green + fingerprint pinned); the merged results row recorded FAIL, but the goal text doesn't say how to score a journey whose sub-checks split. We chose: partial in journey-history (not failing), because the era-open and unchanged-pages sub-checks are genuinely verified done and only the guard-test file is missing. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-observation-contract-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-observation-contract-iter-3-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-observation-contract-iter-3-review.md |
| Browser QA | PASS | reports/phase-goal-observation-contract-iter-3-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-observation-contract/iter-3/eval.md |
| Journey history | — | runs/goal-session-observation-contract/state/journey-history.json |
