# Iteration Summary — goal-referee-iter-5

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-15
**Iteration:** 5

## In plain words

**What you can do now:** You can still watch the live tape update on the Cockpit, look up a stock's price map on the Structure page, and scan for chart setups on the Desk — nothing changed there. Behind the scenes, the fact-checking work is now four rounds deep: counting how much evidence exists, giving every signal and trade one shared record shape, a tested statistics engine that decides whether a pattern is real or noise, and — as of this round — a way to compare every recorded signal against fair "nothing happened" moments from the same stock. None of this checking work has its own screen yet.

**What changed this time:** This round built the actual comparison machinery behind the Desk's signal log. For every signal already recorded, the system now picks four believable "nothing special happened" moments from the same stock. Each moment is matched by time of day and by how much trading time is left, and measured the exact same way as the real signal. It also fixed a leftover math label, so the statistics engine no longer promises a more certain answer than it can honestly reach, and it now refuses broken numbers instead of quietly using them. None of this is visible on any screen yet — it's under-the-hood work a later round will surface on the Desk page.

**What's next:** Next, the team will build a permanent record book that writes down each question before its answer exists, so results can't be cherry-picked afterward.

## Headline

The matched-comparison machinery works.

## Direction

**Signal:** improving
**Why:** J-04 "Matched nulls — comparable times, identical measurement" moved from failing to passing this iteration, with zero regressions and zero anti-goal violations — genuine forward progress along the era's own J-01 → J-05 dependency chain. The evaluator still escalated because this iteration's own plan called for the deeper full-depth pipeline and the engine cut it back to lean for time, while the work shipped permanent, append-only records nothing can later edit — the same depth gap that let iteration 3's statistics bug slip past a lean pass. Iteration 6 is dispatched at full depth to close that audit gap before J-05 builds on top of these records.

**Trend (last 5 iters):**
- Newly passing this iter: J-04
- Newly passing in last 5 iters total: J-01, J-02, J-03, J-04
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The matched-comparison machinery works. I did not take the builder's or the reviewer's word for it: I re-ran the whole test suite myself (2,553 tests collected, 2,545 passed, 8 skipped, nothing failed), printed the settings pin myself, counted the Claude connector's tools myself, and wrote my own extra test because the shipped tests never actually checked the random picking. Nothing broke: the old product replayed green with a fresh picture, and the guard over the owner's saved data reports all 11,274 files unchanged. I am asking for the next round to run at full depth because this round was cut down to the short pipeline for time reasons — its own plan asked for the long one — and it shipped records that can never be edited later.

## What was done

- Product changes: apps/backend/app/research/referee_null.py, apps/backend/app/research/referee_stats.py, apps/backend/app/research/referee_routes.py, apps/backend/tests/test_referee_null.py, apps/backend/tests/test_referee_stats.py, apps/backend/tests/test_referee_guards.py
- Built `referee_null.py` (new, 1,101 lines): both matched-null variants (`referee-null-tod-v1`, `referee-null-context-v1`) — seeded, same-symbol/same-time-of-day/remaining-time-matched comparison anchors, drawn and measured entirely through the existing imported rail, never re-derived locally
- Minted three permanent, signature-bearing spec ids (`referee-null-tod-v1`, `referee-null-context-v1`, `referee-test-perm-v1`) plus the append-only null store, a durable run ledger, a single-flight-per-spec compute manager, and a CLI warmer
- Added five routes (`GET/POST /research/desk/referee/nulls*`) — GETs never compute, unknown spec ids refused
- Fixed the carried `min_attainable_p` bug: it is now a true floor (`2/(draws_used+1)` in exact-enumeration mode), proven by a 1,000+ case sweep with 100+ cases landing exactly on the floor
- Added a fail-loud non-finite (NaN/infinity) guard at the statistics core's own entry points, and a separate exclude-and-count guard at the null adapter's measurement step
- Tightened the TC-8 fast-path test's tolerance (6.0 → 3.5 standard errors) with a mutation counter-test proving it actually catches a real regression
- Corrected the import-topology guard to match the goal's own asymmetric rule, allowing only `referee_null.py` to read the context resolver
- Full backend suite: 2,553 collected / 2,545 passed / 8 skipped / 0 failed (+40 over the iteration-4 floor); fingerprint unchanged. Verified 1 journey (J-10, the kept-product regression sentinel) pass browser QA; J-04 itself has no browser-testable surface (backend-only, keyless) and was correctly skipped, verified instead by direct code read, the evaluator's own suite re-run, and a hand-probe of the seeded draw

## What's left

- Journey J-05 (The registry — pre-registration with an immutable boundary) failing — now unblocked, since J-04, its named dependency, closed this iteration
- Journey J-06 (Estimand engines + adjudication — one checkpoint, recorded forever) failing
- Journey J-07 (The starter family — historical exploration becomes registered questions) failing
- Journey J-08 (The strategy family + the promotion interlock — fail closed, no bypass) failing
- Journey J-09 (The Referee on /desk + MCP contract v5 — 22 read-only tools) failing
- Journey J-10 (The kept product stands — regression sentinel) partial — kept-product half is green, but the era-completion clauses (three Referee /desk sections, 22 MCP tools) stay unmeetable until J-09 lands
- Test gap the evaluator found itself: every shipped fixture has four or fewer eligible comparison moments to choose from, so no shipped test actually discriminates the seeded random pick — carried as a binding rider on the next iteration
- Three smaller known issues carried from the dev handoff: the window-overlap-fraction formula is ungated by any test, the comparison record's seed slot borrows the comparison rule's own name instead of a real question id, and one rare edge case serves "0" instead of an honest "not enough data" value
- Outstanding for a person, unrelated to this project: the trendora backend on port 8255, stopped by an iteration-2 cleanup command, still needs restarting

## Next step

Build J-05 "The registry" next, alone, at full depth — the part that writes each question down before its answer data exists and stamps a date after which only new trading days may count; those records can never be edited later, so they must be right the first time, and the deeper pipeline is exactly what caught this round's fix. Four small items ride along: add a test with more than four comparison moments to choose from (today's tests can never catch a broken random pick); add a test for the window-overlap number's formula (currently ungated); decide whether comparison sets should be filed under a real question id once questions exist; and serve "unknown" instead of "0" for the eligible-moments share when nothing can be measured. Outside this project, still outstanding since iteration 2: restart the trendora backend on port 8255.

## Assumptions made

- iter-5 · goal-evaluator — Ambiguity: J-04's acceptance names "hand-computed draws" as a clause, but every shipped fixture has four or fewer eligible comparison moments, so the seeded random selection is never actually discriminated by any test — any permutation (or a broken selector) would pass the same assertion. We chose: Scored J-04 passing after personally verifying the selection with a fresh 7-eligible probe — a genuine non-trivial subset, byte-identical on a second call, the trigger bar never drawn, a different subset for a different observation — rather than withholding the pass for the literal clause; the test gap is carried as a binding rider on the next iteration. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: the spec calls `min_attainable_p` "the minimum attainable p (granularity)," and the exact-enumeration branch served `1/(draws_used+1)` — a value the already-fixed method can never actually produce, since the observed grouping is always self-extreme, making the true floor `2/(draws_used+1)`; no human ruling was available headlessly before J-04 needed the field. We chose: Ruled for the field's own literal name ("minimum ATTAINABLE") over the looser "granularity" reading — `min_attainable_p` now reads `2.0/(draws_used+1)` in exact mode, unchanged in the seeded branch; verified this touches none of the four values the statistics engine's own proof record pins, so no version bump was needed. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: J-03's Acceptance says "the oracle suite is green and IS the acceptance," and every named clause passes, but the auditor found an open gap (B1: `min_attainable_p` serves a value the fixed exact method can never produce) that the acceptance sentence doesn't clearly resolve either way. We chose: Scored J-03 passing and carried B1 as a binding rider on J-04 rather than holding the journey a second iteration. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: iteration 3's next-step recommendation named two same-file riders plus "two leads in older unchanged code" to investigate, without saying whether "ride along" meant investigate-only or investigate-and-fix, or for both leads. We chose: Investigated both to a concrete root cause; Lead 1 (a stale-detector-basis date silently contributing zero to evidence counts) is closed additively this iteration; Lead 2 (`epoch_anchor` fallback conflating missing vs. explicit-zero) is dropped per this project's own T-1 rule and surfaced for an owner ruling, since it touches frozen, already-shipped behavior elsewhere. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-03's Acceptance sentence says "the oracle suite is green and IS the acceptance," and every clause it names was met, but the evaluator reproduced an anti-conservative defect the oracle suite structurally could not see, and the goal text doesn't say whether the acceptance sentence is the whole test or a proxy for "the statistics are calibrated." We chose: Read it as a proxy and scored J-03 partial, not passing, spending iteration 4 on a full-depth fix before anything builds on the module. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the statistical spec types `provenance.detector_basis` as a plain string with no ruling for the strategy family (which has no detector), and iteration 2's rider asked for a human ruling that headless goal mode could not obtain before this iteration closed. We chose: Ratified iteration 2's already-accepted convention (`detector_basis` stays `None` for strategy observations) as the standing rule, via one documentation-only spec sentence, zero behavior change. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: the spec's pseudocode types `provenance.detector_basis` as a plain string, but a strategy trade has no detector, and the goal's own rules say an unimplementable spec clause should be dropped and surfaced, never improvised. We chose: Accepted the developer's disclosed improvisation (`detector_basis: None` for every strategy observation) rather than treating it as a failure, since it was disclosed honestly and is reversible. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-02's Steps require a "completeness predicate" per record, but J-02's own Acceptance list never names it, and the shipped `session_completeness` estimate is untested and blind to intra-session bar gaps. We chose: Scored J-02 passing against its written Acceptance list, which is fully met, rather than withholding the pass for an unlisted Step sub-clause; recorded as a binding rider on the next iteration. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance requires the strategy family to carry the `basis_caveats` forming-bar disclosure "verbatim," but no verbatim text for it exists anywhere in the goal or the spec — only a description of what it must disclose. We chose: Accepted this iteration's first authoring of the exported constant naming the disclosure as satisfying "verbatim" — it is now the single source of truth later journeys must import rather than re-word. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-10 is written as a continuous regression sentinel, but its own acceptance also names era-end conditions (three Referee `/desk` sections, exactly 22 MCP tools) that were structurally unmeetable at iteration 0. We chose: Scored J-10 partial, not passing — the whole-acceptance reading — and recorded the verified kept-product evidence so no later iteration redoes that work. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-5.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-5-dev.md |
| Review | PASS | reports/reviews/goal-referee-iter-5-review.md |
| Browser QA | PASS | reports/phase-goal-referee-iter-5-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-referee/iter-5/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |
