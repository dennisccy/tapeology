# Iteration Summary — goal-referee-iter-3

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-14
**Iteration:** 3

## In plain words

**What you can do now:** The product's three screens still work the same as always. You can watch the live tape update on the Cockpit, look up a stock's price map on the Structure page, and scan for chart setups on the Desk. Two rounds of quiet fact-checking groundwork are also done behind the scenes — counting how much evidence exists, and giving every signal and trade one shared record shape — but neither has a screen of its own yet.

**What changed this time:** Behind the scenes, the team built the actual checking engine that will one day decide whether a trading pattern is real or just noise, and tested it hard. While double-checking it themselves instead of trusting the build report, they found a real flaw: in one of its two ways of computing "how surprising is this result?", the answer can come out more confident than it honestly should. Nothing on any screen uses this engine yet, so nobody has been shown a wrong number — but it has to be fixed before anything else is built on top of it.

**What's next:** Next, the team will fix that flaw in the checking engine and prove the fix holds, with tougher tests, before building the next piece on top of it.

## Headline

Built the statistics engine that decides whether a trading pattern is real or just noise

## Direction

**Signal:** holding
**Why:** J-03 (the statistics core) moved from failing to partial this iteration — real code and a 77-test oracle suite landed, but the evaluator's own independent reproduction caught a genuine anti-conservative bug in one of the two p-value paths, so J-03 does not close yet. J-01 and J-02 hold their passing status (not re-tested this round due to a wall-clock budget cut), and J-10's kept-product half re-verified clean with zero anti-goal violations. Six journeys (J-04 through J-09) remain untouched, so the project holds steady this round: nothing broke, but nothing newly crossed into passing either.

**Trend (last 4 iters):**
- Newly passing this iter: none
- Newly passing in last 4 iters total: J-01, J-02
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 0 of last 4

**Latest evaluator reasoning:** This iteration built the statistics engine that decides whether a trading pattern is real or just noise. Most of it is genuinely good, and I checked it myself rather than trusting the report: the proof suite runs green in 81 seconds, the whole test suite is 2,495 pass / 8 skip with nothing broken, the settings pin still prints `08e471b10130e1e2`, and the tamper checks really do refuse a hand-edited proof record. But I found a real fault the developer, the reviewer and the coherence check all missed.

## What was done

- Product changes: apps/backend/app/research/referee_stats.py, apps/backend/tests/test_referee_oracles.py, apps/backend/tests/test_referee_stats.py, apps/backend/tests/test_referee_evidence.py, apps/backend/tests/test_referee_guards.py, docs/referee-statistical-spec.md
- Built `referee_stats.py`, the calibrated statistics core (seeded streams, occurrence/session bootstrap CIs, the primary within-session permutation test, sign-flip/equal-weight robustness disclosures, Benjamini-Hochberg + BY, a fail-closed oracle attestation) implementing `docs/referee-statistical-spec.md` verbatim
- Added the 6-case + mutation-fixture seeded oracle suite (`test_referee_oracles.py`, 9 tests, self-timed under the 120s budget — measured 74.7s and 76.7s in isolation) plus 32 fast mechanics tests (`test_referee_stats.py`)
- Closed all three carried-over riders from iteration 2: two test-coverage gaps in `test_referee_evidence.py` (session-completeness boundary, observation-cache path resolver) and one documentation-only sentence in `docs/referee-statistical-spec.md` §2 stating `detector_basis` is `None` for strategy observations by design
- Extended `test_referee_guards.py` with a `referee_stats.py`-scoped import-ban guard (proves the new statistics module never imports the playbook/rail modules) plus its own can-fail counter-test
- Full backend suite: 2,495 passed / 0 failed / 8 skipped (up from the 2,446 floor); `Config().config_fingerprint()` unchanged at `08e471b10130e1e2`; MCP still advertises 20 tools; zero diff to any frozen module or store file
- Browser QA: J-03 has no browser-testable surface this iteration (SKIP — backend-only, unconsumed by any route); J-10's kept-product regression sentinel re-verified PASS with a fresh screenshot
- The evaluator's own independent reproduction caught a real anti-conservative bug in the exact-enumeration p-value branch, missed by the developer, reviewer, and coherence audit — J-03 is scored partial, not passing, and fixing it is next iteration's full-depth target

## What's left

- Journey J-03 (The statistics core — calibrated, seeded, oracle-proven, fail-closed) partial — a real anti-conservative bug in the exact-enumeration permutation branch must be fixed and proven before it can be marked passing or consumed by any later journey
- Journey J-04 (Matched nulls — comparable times, identical measurement) failing
- Journey J-05 (The registry — pre-registration with an immutable boundary) failing
- Journey J-06 (Estimand engines + adjudication — one checkpoint, recorded forever) failing
- Journey J-07 (The starter family — historical exploration becomes registered questions) failing
- Journey J-08 (The strategy family + the promotion interlock — fail closed, no bypass) failing
- Journey J-09 (The Referee on /desk + MCP contract v5 — 22 read-only tools) failing
- Journey J-10 (The kept product stands — regression sentinel) partial — kept-product half is green, but the era-completion clauses (three Referee /desk sections, 22 MCP tools) stay unmeetable until J-09 lands
- Two small carried riders from the review (an unused draw-primitive function; an untested single-anchor fast-path branch) plus two unresolved leads in older, unchanged code (a stale-detector-version date collapse; a no-time-anchor dataset becoming a 1969 date) — all queued for a future iteration
- Outside this project: the unrelated trendora backend on port 8255, stopped by an iteration-2 cleanup command, still needs a person to restart it

## Next step

Iteration 4 should fix the statistics engine's exact-mode p-value and prove the fix, at full depth, before anything else is built on top of it: make the exact mode add the second group up directly (the same way the reference figure does) so the observed arrangement always counts as extreme, guaranteeing the answer can never fall below 2/(number of arrangements + 1); add an oracle case that actually exercises the exact mode with awkward decimal values, plus a deliberately broken variant that errs in the over-confident direction, since today's mutant test can only catch the over-cautious kind; and re-pin the stored proof record while bumping the engine's version label, which is free today since nothing has been recorded yet. Two small riders should ride along: the unused draw helper and the untested single-anchor shortcut the reviewer flagged, plus a check of the two unresolved leads in older code. For a person: approve "fix and prove the p-value floor in the statistics engine, at full depth, then continue to matched nulls (J-04)" — nothing here needs a human to unblock it. Still outstanding from iteration 2: the unrelated trendora backend on port 8255 has not been restarted.

## Assumptions made

- iter-3 · goal-evaluator — Ambiguity: J-03's acceptance says "the oracle suite is green and IS the acceptance", and every clause it literally names is met, but the goal text does not say whether that sentence is the whole test or a proxy for "the statistics are calibrated" — and an anti-conservative defect was independently reproduced that the oracle suite structurally cannot see. We chose: Read the acceptance as a proxy, not the whole test, and scored J-03 `partial` rather than `passing`, matching the journey's own title ("calibrated ... oracle-proven"). Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the statistical spec types `provenance.detector_basis` as a plain string with no ruling for the strategy family (which has no detector), and iteration 2's rider asked for an owner ruling before this closed, but goal mode is headless with no human available. We chose: Ratified iteration 2's already-accepted convention (`detector_basis` stays `None` for strategy observations) as the standing rule for this era, via one clarifying, documentation-only sentence in the spec — zero `.py` behavior change. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: the spec's pseudocode types `provenance.detector_basis` as a plain string, but a strategy trade has no detector, and the goal's own Constraints say an unimplementable spec clause should be dropped and surfaced for an owner ruling, never improvised. We chose: Accepted the developer's disclosed improvisation (`detector_basis: None` for every strategy observation, by analogy with the existing "None when inapplicable" pattern) rather than treating it as a failure, since it was disclosed honestly and is reversible. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-02's Steps require a "completeness predicate" per record, but J-02's own Acceptance list never names it, and the shipped `session_completeness` estimate is untested and blind to intra-session bar gaps. We chose: Scored J-02 `passing` against its written Acceptance list, which is fully met, rather than withholding the pass for an unlisted Step sub-clause; recorded as a binding rider on the next iteration instead of a blocker. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance requires the strategy family to carry the `basis_caveats` forming-bar disclosure "verbatim", but no verbatim text for it exists anywhere in the goal or the spec — only a description of what it must disclose. We chose: Accepted this iteration's first authoring of the exported constant naming the disclosure as satisfying "verbatim" — it is now the single source of truth later journeys must import rather than re-word. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-10 is written as a continuous regression sentinel, but its own acceptance also names era-end conditions (three Referee /desk sections, exactly 22 MCP tools) that were structurally unmeetable at iteration 0. We chose: Scored J-10 `partial`, not `passing` — the whole-acceptance reading — and recorded the verified kept-product evidence so no later iteration redoes that work. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-3-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-referee-iter-3-review.md |
| Browser QA | PASS | reports/phase-goal-referee-iter-3-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-referee/iter-3/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |
