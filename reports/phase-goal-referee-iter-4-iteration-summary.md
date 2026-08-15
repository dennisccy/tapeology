# Iteration Summary — goal-referee-iter-4

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-15
**Iteration:** 4

## In plain words

**What you can do now:** You can still watch the live tape update on the Cockpit, look up a stock's price map on the Structure page, and scan for chart setups on the Desk — nothing changed there. Behind the scenes, the fact-checking work is now three rounds deep: counting how much evidence exists, giving every signal and trade one shared record shape, and — as of this round — a tested statistics engine that decides whether a pattern is real or just noise. None of this checking work has its own screen yet.

**What changed this time:** The team fixed a real flaw in the statistics-checking engine: in one narrow situation it could report a result as more certain than the math actually allows, and that is no longer possible — proven with a hand-checked example plus thousands of extra test cases run in both directions. They also gave the evidence-counting tool one small honesty upgrade: it now names any date it had to leave out of its count instead of silently dropping it. Neither change is visible on any screen yet — the checking engine still has no page of its own.

**What's next:** Next, the team will build the part that compares each signal against fair "nothing happened" moments from the same stock, so a real pattern can be told apart from a lucky coincidence.

## Headline

Fixed the exact-mode p-value floor bug in the statistics engine and proved the fix both ways

## Direction

**Signal:** improving
**Why:** J-03 "The statistics core" moved from partial to passing this iteration — the evaluator independently reproduced the fix's correctness (2,500 fresh cases, zero floor violations; the hard auditor separately found zero violations across a further 7,035 cases) rather than trusting the dev report, closing the anti-conservative bug that forced last iteration's ESCALATE. J-01 and J-02 hold their passing status unchanged and J-10's kept-product half re-verified clean, with zero anti-goal violations, so the era's dependency chain (J-01 → J-02 → J-03 → J-04…) is now fully unblocked heading into J-04.

**Trend (last 5 iters):**
- Newly passing this iter: J-03
- Newly passing in last 5 iters total: J-01, J-02, J-03
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The number problem found last time is really fixed. Last iteration the maths part could report a result as more surprising than its own method allows; this iteration it cannot. I did not take anyone's word for it. I ran the exact failing example myself and it now gives the correct answer (2/7, not 1/7), and I wrote my own fresh test of 2,500 small cases — including the hard cases where the two groups are far apart — and found zero bad answers, with 448 cases landing exactly on the lowest allowed value.

## What was done

- Product changes: apps/backend/app/research/referee_stats.py, apps/backend/app/research/referee_evidence.py, apps/backend/tests/test_referee_stats.py, apps/backend/tests/test_referee_oracles.py, apps/backend/tests/test_referee_evidence.py
- Fixed the exact-enumeration p-value floor bug in `permutation_test` (direct per-combination `math.fsum` plus a cross-session `math.fsum` combine, found empirically necessary) so the observed grouping's statistic now reproduces bit-identically and `p` can never fall below its own floor — closes the defect that forced last iteration's ESCALATE
- Proved the fix in both directions for J-03: the evaluator's exact minimal repro now returns the correct floor value (2/7, not 1/7), a fresh 2,500-case independent sweep found zero violations, and the oracle suite gained a case that genuinely enters the enumeration branch plus a paired anti-conservative mutant
- Re-pinned the attestation and bumped `STATS_CORE_VERSION` from v1 to v2, re-verified live rather than assumed unchanged; added a test rejecting an attestation whose version string is stale
- Closed two reviewer-flagged same-file test gaps (`_draw_indices_without_replacement` coverage, the `n1>1, n2==1` fast path) and one evaluator-flagged silent-evidence-drop on J-01/J-02's shared surface (`stale_basis_dates`, additive-only, empty on all real data)
- Full backend suite: 2,504–2,505 passed / 8 skipped / 0 failed; fingerprint unchanged at `08e471b10130e1e2`; zero diff to any frozen module or store file
- Browser QA: J-03 (this iteration's only target journey) has no browser-testable surface — backend-only, unconsumed by any route; J-10's kept-product regression sentinel re-verified PASS with a fresh screenshot (one supplementary, non-blocking check failed on a pre-existing, unrelated empty state)
- The hard auditor independently re-derived J-03's correctness (7,035 generated cases, zero violations) and left one open gap for an owner ruling before J-04 consumes the module (`min_attainable_p` still advertises a value the fixed method can never reach)

## What's left

- Journey J-04 (Matched nulls — comparable times, identical measurement) failing — now unblocked, since its named dependency J-03 closed this iteration
- Journey J-05 (The registry — pre-registration with an immutable boundary) failing
- Journey J-06 (Estimand engines + adjudication — one checkpoint, recorded forever) failing
- Journey J-07 (The starter family — historical exploration becomes registered questions) failing
- Journey J-08 (The strategy family + the promotion interlock — fail closed, no bypass) failing
- Journey J-09 (The Referee on /desk + MCP contract v5 — 22 read-only tools) failing
- Journey J-10 (The kept product stands — regression sentinel) partial — kept-product half is green, but the era-completion clauses (three Referee /desk sections, 22 MCP tools) stay unmeetable until J-09 lands
- One open gap needs an owner ruling before J-04 builds on the statistics core: `min_attainable_p` still advertises a value the fixed exact method can never reach (a spec-wording ambiguity, not a new bug)
- This iteration's own closure check failed on a leftover placeholder in `what-to-click.md`, leaving its five changed files uncommitted — needs a person to commit them
- Outside this project: the unrelated trendora backend on port 8255, stopped by an iteration-2 cleanup command, still needs a person to restart it

## Next step

Build J-04 "Matched nulls" next, alone, at full depth — the part that compares every signal against fair, matched "nothing happened" moments from the same stock at the same time of day, measured through the identical rail; full depth because this iteration also mints permanent name-tags that later registered questions will point at forever. Three riders travel with it: settle what "the smallest possible surprise value" means (an owner ruling on `min_attainable_p`, free to decide before anything consumes it), refuse unusable readings (not-a-number, infinity) at the door instead of silently mis-answering, and tighten the one-against-many shortcut test's currently-wide tolerance. Two items need a person, neither blocking the next build: commit this iteration's five changed files (closure failed on a `what-to-click.md` placeholder), and restart the unrelated trendora backend on port 8255, stopped since iteration 2.

## Assumptions made

- iter-4 · goal-evaluator — Ambiguity: J-03's Acceptance says "the oracle suite is green and IS the acceptance," and every named clause passes, but the auditor found an open gap (B1: `min_attainable_p` serves a value the fixed exact method can never produce) that the acceptance sentence doesn't clearly resolve either way. We chose: Scored J-03 passing and carried B1 as a binding rider on J-04 rather than holding the journey a second iteration. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: iteration 3's next-step recommendation named two same-file riders plus "two leads in older unchanged code" to investigate, without saying whether "ride along" meant investigate-only or investigate-and-fix, or for both leads. We chose: Investigated both to a concrete root cause; Lead 1 (a stale-detector-basis date silently contributing zero to evidence counts) is closed additively this iteration; Lead 2 (`epoch_anchor` fallback conflating missing vs. explicit-zero) is dropped per this project's own T-1 rule and surfaced for an owner ruling, since it touches frozen, already-shipped behavior elsewhere. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-03's Acceptance sentence says "the oracle suite is green and IS the acceptance," and every clause it names was met, but the evaluator reproduced an anti-conservative defect the oracle suite structurally could not see, and the goal text doesn't say whether the acceptance sentence is the whole test or a proxy for "the statistics are calibrated." We chose: Read it as a proxy and scored J-03 partial, not passing, spending iteration 4 on a full-depth fix before anything builds on the module. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the statistical spec types `provenance.detector_basis` as a plain string with no ruling for the strategy family (which has no detector), and iteration 2's rider asked for a human ruling that headless goal mode could not obtain before this iteration closed. We chose: Ratified iteration 2's already-accepted convention (`detector_basis` stays `None` for strategy observations) as the standing rule, via one documentation-only spec sentence, zero behavior change. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: the spec's pseudocode types `provenance.detector_basis` as a plain string, but a strategy trade has no detector, and the goal's own rules say an unimplementable spec clause should be dropped and surfaced, never improvised. We chose: Accepted the developer's disclosed improvisation (`detector_basis: None` for every strategy observation) rather than treating it as a failure, since it was disclosed honestly and is reversible. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-02's Steps require a "completeness predicate" per record, but J-02's own Acceptance list never names it, and the shipped `session_completeness` estimate is untested and blind to intra-session bar gaps. We chose: Scored J-02 passing against its written Acceptance list, which is fully met, rather than withholding the pass for an unlisted Step sub-clause; recorded as a binding rider on the next iteration. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance requires the strategy family to carry the `basis_caveats` forming-bar disclosure "verbatim," but no verbatim text for it exists anywhere in the goal or the spec — only a description of what it must disclose. We chose: Accepted this iteration's first authoring of the exported constant naming the disclosure as satisfying "verbatim" — it is now the single source of truth later journeys must import rather than re-word. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-10 is written as a continuous regression sentinel, but its own acceptance also names era-end conditions (three Referee `/desk` sections, exactly 22 MCP tools) that were structurally unmeetable at iteration 0. We chose: Scored J-10 partial, not passing — the whole-acceptance reading — and recorded the verified kept-product evidence so no later iteration redoes that work. Reversible: yes

## Quick verify

From `reports/phase-goal-referee-iter-4-what-to-click.md`:

1. Open `http://localhost:3301/` in your browser
2. Type "SIM-BUYER" into the "Ticker" field and click the "Watch" button
3. Navigate to `http://localhost:3301/structure`
4. Type "AAPL" into the "Structure symbol" field, type "2026-06-22 12:00:00" into the date field just below it, then click the "Load" button
5. Navigate to `http://localhost:3301/desk`

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-4.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-4-dev.md |
| Review | PASS | reports/reviews/goal-referee-iter-4-review.md |
| Browser QA | FAIL | reports/phase-goal-referee-iter-4-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-referee-iter-4-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-referee-iter-4-user-visible-changes.md |
| What to click | — | reports/phase-goal-referee-iter-4-what-to-click.md |
| UI surface map | — | reports/phase-goal-referee-iter-4-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-referee-iter-4-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-referee-iter-4-ux-regression.md |
| QA | PASS | reports/qa/goal-referee-iter-4-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-referee-iter-4-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-referee-iter-4-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-referee/iter-4/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |
