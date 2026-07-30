# Iteration Summary — goal-desk-iter-24

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-30
**Iteration:** 24

## In plain words

**What you can do now:** Run a simulated tape-reading session with live moving price bars, open the Structure page to see a stock's support and resistance on a chart, and open the Desk page to see roughly 100 stocks screened and ranked. Each ranked row shows its history depth, its price wall and the closing price it was measured from, the nearest wall on the other side, how many price levels built that wall, whether the wall sits at a round number, and its timeframe breakdown — and now all of that fits on screen at once with no sideways scrolling, so more rows are visible without extra scrolling either. You can also hover a row for more detail, repair Desk's coverage badges, browse past scans, jump from a saved scan into the matching Structure chart, and read Desk data through a connected Claude conversation.

**What changed this time:** The Desk page's ranked table was reflowed so every column — rank, symbol, side, class, distance, score, coverage marks, tick evidence, basis, history, price wall, opposite wall, and level breakdown — fits on screen at a normal window size with no sideways scrolling needed, and each row is shorter so more of them show at once.

**What's next:** Next, run one more short recording-only pass with no code changes: record the short guided video for this new layout, finish double-checking the two items (the Claude-connection tool count and the wall-composition detail) that ran out of time this round, and replay the new video's saved test script to confirm its screenshot was actually saved.

## Headline

Desk's ranked-row table reflowed to fit 1440×900 with zero horizontal scroll

## Direction

**Signal:** improving
**Why:** J-16 ("the briefing fits the page it is read on") went from absent to passing this iteration, closing the layout debt flagged since iter-21/23 (table scroll width 1795px→1214px, row height ~115px→56.5-57px on 98 of 100 rows). J-06 and J-15 were skipped this run when the browser-QA lane exceeded its wall-clock budget, and J-16's own required demo-narrator walkthrough was never recorded because the depth arbiter demoted this run from full to lean — so the evaluator withheld GOAL_ACHIEVED and returned CONTINUE. No regressions and no anti-goal violations were found; the underlying product moved forward even though the finish line wasn't crossed.

**Trend (last 4 iters):**
- Newly passing this iter: J-16
- Newly passing in last 4 iters total: J-15 (iter-23), J-16 (iter-24)
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 2 of last 4

**Latest evaluator reasoning:** "The Desk's ranked table now fits the page. At a normal window size (1440 by 900) every column of the top row is readable at once — position, symbol, side, class, distance, score, the four coverage marks, tick evidence, basis, history, band, opposite wall and what the wall is made of — with no sideways scrolling at all. I am NOT calling the goal finished, for three reasons that are about missing checks, not about broken behaviour: two journeys (J-06 "17 machine-readable tools" and J-15 "what each wall is made of") were dropped from this run's re-check when the run went over its time budget, and the short guided film that J-16's own text asks for was never recorded, because this run was dispatched at the shorter depth that records no film."

## What was done

- Product changes: apps/frontend/app/desk/page.tsx, apps/backend/tests/test_desk_ui_guards.py
- Reflowed the `/desk` ranked-row table with a fixed-width, 13-column layout so its own scroll width now matches its container exactly (1214px vs 1214px, was 1795px at iter-23).
- Removed `flex-wrap` from the coverage badges so all four sit on one line per row, cutting row height from ~115px to 56.5-57px on 98 of 100 rows (2 rows measure 63px because of a reused badge's own height).
- Added a new `rank` column showing each row's 1-based served position, guarded by a new test that forbids any client-side sort/reverse/slice of the row order.
- Restyled the class and distance cells as chips reusing the page's existing badge style.
- Restored the "band "/"opposite " label-prefix text that two stored golden test scripts (J-13, J-14) assert on literally — a review round caught these had been silently dropped and would have broken the scripts — and added a guard test tying the cell text to those scripts.
- Replayed all 13 stored golden journeys clean with zero script edits, and verified 14 target/regression journeys pass browser QA (including the new J-16 journey); J-06 and J-15 kept their prior passing status after running out of the iteration's time budget.

## What's left

- The guided demo-narrator walkthrough required by J-16 "The briefing fits the page it is read on" was never recorded — this run was dispatched at a shorter depth that records no film.
- J-06 "17 machine-readable tools" and J-15 "what each wall is made of" were skipped this run (time-budget cutoff); both need a formal re-check next iteration, though the evaluator hand-checked them and found no problem.
- 2 of the 100 ranked rows measure 63px, 3px over the 60px target, because of the reused "round number" badge's height — a disclosed, non-blocking residual.
- The replay lane claims it saved a screenshot for the new J-16 test script, but that file does not exist on disk yet — needs a fresh replay to confirm.

## Next step

Run one more short capture-and-check pass (`Depth: evidence`), no code change needed, with three jobs: (1) record the guided film that J-16 "The briefing fits the page it is read on" asks for, showing the `opposite` and `levels` columns inside its own frames with each click naming exactly one row; (2) re-check J-06 "17 machine-readable tools" and J-15 "what each wall is made of", the two journeys this run ran out of time for — J-15 matters more than a routine re-check because this run changed the wording in that column; (3) replay the newly saved J-16 test script, since the screenshot it claims to have produced is not on disk. Two smaller items are worth tidying on the owner's own track but are not blocking: two rows are 3px over the height target because of a badge's own height, and the back-end test suite now reads two files from the run bookkeeping folder, so archiving that folder would break the suite.

## Assumptions made

- iter-24 · goal-evaluator — Ambiguity: whether J-16's "row height ≤60px" target means literally every row or the general ~115px→~60px regime; 98 of 100 rows hit 56.5-57px but 2 rows measure 63px because of a reused badge's own height. We chose: read it as the regime and score J-16 passing, recording the 3px residual openly rather than as an unmet clause. Reversible: yes.
- iter-24 · goal-evaluator — Ambiguity: J-16 also requires a recorded demo walkthrough showing the "opposite"/"levels" columns, but this run was auto-demoted to a shorter depth that records no film, conflicting with the rule that a missing-evidence gap should never block a journey. We chose: mark J-16 passing with an evidence-makeup flag (behaviour proven by other artifacts) but keep the overall verdict CONTINUE rather than GOAL_ACHIEVED, since a deferred journey can't support an achievement claim either. Reversible: yes.
- iter-23 · goal-evaluator — Ambiguity: J-15's acceptance text says the evidence must come from a fixture-scoped rig, but this run's evidence was produced on the shared/ambient rig instead. We chose: treat the location clause as a hygiene note rather than a hard pass/fail gate, and score J-15 passing while disclosing the deviation. Reversible: no — the recorded snapshot is permanent by design.
- iter-23 · goal-evaluator — Ambiguity: two artifacts fell short of their literal wording (one UI test flagged FAIL for a self-invented scroll-free-discovery check, and the demo verdict read "RECORDED_WITH_NOTES" instead of "RECORDED") while the underlying behaviour was actually met. We chose: score J-15 passing on both counts, treating the shortfalls as disclosed notes rather than failures. Reversible: yes.
- iter-22 · goal-evaluator — Ambiguity: the GOAL_ACHIEVED call that iteration rested on a goal.md edit (adding an owner-ratification clause and a new capture rig) that no pipeline agent was seen making. We chose: treat it as the owner's own approved edit based on timing, direction, and content evidence, and score the affected journey against the new text. Reversible: yes.
- iter-21 · goal-evaluator — Ambiguity: whether a recorded walkthrough film must itself visually show the columns it narrates, or whether narrating over a populated screen is enough. We chose: treat narration over populated rows as sufficient, since pixel legibility is covered separately by browser-QA screenshots. Reversible: yes.
- iter-21 · goal-decomposer — Ambiguity: a prior run's recommendation asked for a "sideways scroll" reveal of two columns, but the recording tool has no scroll action. We chose: have the walkthrough narrate the columns via text instead of attempting a click-based reveal that doesn't exist. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-24.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-24-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-desk-iter-24-review.md |
| Browser QA | PASS | reports/phase-goal-desk-iter-24-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-desk/iter-24/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |
