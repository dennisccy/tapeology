# Iteration Summary — goal-hypothesis-foundry-iter-7

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-08-27
**Iteration:** 7

## In plain words

**What you can do now:** An operator can open the Desk page's Hypothesis Foundry section and see the whole research chapter so far. It shows: the new chapter opened cleanly with the old one closed, approved research ideas turned into fair test plans, proof that the idea-reading step doesn't change timing or direction, the record-keeping and lock-in checks all working, the one real research batch (11 ideas checked, none ready yet — an honest result), and now proof that the one real evaluation run over that batch actually happened and touched nothing off-limits.

**What changed this time:** Nothing changed on screen. Behind the scenes, the number shown on the Runner/Checkpoint panel — "how many candidates are ready to run" — used to be calculated in two different places in the code. Now it is calculated in exactly one place, with a permanent check that would catch it if the two ever disagreed. The number itself is still 0, same as before.

**What's next:** Next, we'll build the final summary screen for this research chapter — the one that honestly tells the whole story, including that no idea turned out to be a winner yet.

## Headline

One shared internal calculation now has exactly one home.

## Direction

**Signal:** holding
**Why:** J-01 through J-07 all replayed passing again with zero regressions, but no journey changed status this iteration — it was a deliberate consolidation-only pass to retire iter-6's COHERENCE-FAIL (the `frozen_ready_total` duplicate-computation blocker), not a scope-adding one. J-08 "The operator sees the final Foundry truth" remains the sole failing journey and was explicitly out of scope this iteration per the priority rubric; it is confirmed as the iter-8 target. Real progress happened (the blocker that stalled closure is now closed, `iter-7/coherence.md` is COHERENCE-WARN), but with zero journey movement this iteration reads as holding rather than improving.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-02, J-03, J-04, J-05, J-06, J-07
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 3 MINOR opened (1 in iter-5 "No second real generation epoch," 2 in iter-6 "Single source of truth" and "Persistence stays scoped"); 1 resolved this iteration ("Single source of truth"), 2 still open (both OWNER-only)
- Iters with no journey state change: 1 of last 5 (iter-7 only; iter-3 through iter-6 each moved at least one journey)

**Latest evaluator reasoning:** "This iteration had one job and it did it. The structural fault that stopped the last iteration — the same number being worked out in two different places — is now settled by the only legal route, and I checked that route myself instead of trusting the reports. The change is tiny (two files) and nothing an operator sees has changed. The seven finished journeys all still work. What went wrong was not the product but the paperwork: the browser test lane never actually tested this iteration's own target journey, while the quality report claimed all the required checks were complete."

## What was done

- Product changes: apps/backend/app/research/micro_routes.py, apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py
- Extracted the inline `frozen_ready_total` calculation into one named, documented function (`compute_frozen_ready_total`) — the sole non-sealed owner of the value; served value unchanged (still 0)
- Added a permanent equivalence-pinning test proving the sealed CLI's transcribed formula agrees with the new canonical helper on the real, frozen manifest
- Verified zero sealed freeze-set files were touched — all 59 pinned files byte-identical before and after
- Re-verified all 7 finished journeys (J-01 through J-07) pass browser QA / deterministic replay, including this iteration's own target J-07, which the QA lane had skipped and the auditor had to replay itself
- Auditor filed the missing J-07 evidence and corrected two false claims: a QA report that said "Browser Checks: SKIPPED" while also certifying "Definition of Done: Complete," and a browser-QA report that denied editing a golden test script it had in fact edited
- Retired iter-6's COHERENCE-FAIL verdict for the "Single source of truth" anti-goal finding (now COHERENCE-WARN), with the permanent residual duplicate formally disclosed for the era's closing record

## What's left

- Journey J-08 ("The operator sees the final Foundry truth and all foundation rails still hold") failing — the era's last remaining journey, not yet built
- Two OWNER-only anti-goal findings remain open and blocking: a page-load GET on the Foundry panel still writes a small lock file (fix lives inside a sealed file), and the discarded first real research batch still awaits an owner ruling to accept or reject
- The residual duplicate calculation inside the sealed CLI script is legally permanent — the owner may want to formally record it as an accepted exception rather than have future work keep trying to "fully" fix it
- The 80 left-out research datasets are currently only printed by a command-line tool, not shown on screen — J-08 should surface this
- J-08 still needs: the final on-screen summary, the honest "no survivor exists" statement, and the full T-9/T-10/T-11 protective-check battery

## Next step

Build J-08 "The operator sees the final Foundry truth" — the era's last remaining journey — at full review depth, since the strict review lane has found a real fault in every full iteration it has run this session, including this one. Carry three habits into that iteration: replay the target journey, not only the older ones; capture Foundry-section screenshots through the deterministic replay tool, not the browser tool's deep-scroll path, which reliably returns blank images; and stop describing the number-agreement test as drift protection — the freeze-set does that job, not the test. Three owner rulings are also still needed before the era can close: accept or reject the first real research batch that was made and discarded; accept that opening the page writes a small lock file; and record the sealed CLI's leftover duplicate calculation as a permanently allowed exception.

## Assumptions made

- iter-7 · goal-evaluator — Ambiguity: the ESCALATE decision-tree rung is worded for a lean iteration and a review-lane fail-open, but iter-7 ran full with the review lane passing; the QA lane still certified "Definition of Done Complete" while its own browser checks were marked skipped, and it never replayed this iteration's own target journey J-07. We chose: ESCALATE, matching the rung's fail-open clause on the QA lane instead of the review lane, disclosing that the engine's depth arbiter would otherwise demote a CONTINUE to lean anyway. Reversible: yes
- iter-7 · goal-evaluator — Ambiguity: iter-6's "Single source of truth" anti-goal finding recorded its own close condition (one non-sealed owner plus a pinning test), which was met literally this iteration, but a permanent, un-editable duplicate remains inside a sealed CLI script. We chose: mark it resolved, per the rule that a finding's own recorded close condition being proven satisfied discharges it, while writing the permanent residual into the record so it can never be misread as "the duplicate was deleted." Reversible: yes (owner can flip it back to blocking with a one-line ruling)
- iter-7 · goal-decomposer — Ambiguity: iter-6's evaluator asked for both the `frozen_ready_total` fix and building J-08 in the same iteration, but iter-6's own coherence check had failed, and this agent's rules require a coherence-failed iteration to be consolidation-only with no new scope. We chose: fix the duplicate-computation fault only this iteration and defer J-08 to iter-8. Reversible: yes (J-08 is simply built next iteration instead)
- iter-6 · goal-evaluator — Ambiguity: a uniqueness guard landed against the "No second real generation epoch" finding's own recorded close condition ("stays blocking until the owner rules or a uniqueness guard lands"), which could argue for closing it. We chose: keep it unresolved and blocking (fail-closed reading) — a guard prevents recurrence but does not un-mint the already-discarded research batch ID, and the finding explicitly asked for owner ratification. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: the "page loads stay read-only" rule is worded literally, but a new safety check now makes each page-load also write a small lock file, even though no research data is recorded and no candidate is computed. We chose: record it as a minor, unresolved, blocking finding on the literal reading rather than dismissing it in prose. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: the decision tree's escalate rung literally matched (J-08 has failed for 6+ evaluations) and the engine had twice demoted a plain-continue verdict to a lighter review pass, but this agent's own contract states unconditionally that a coherence-failed iteration must return continue. We chose: continue, following the explicit contract over the tree rung, and flagged the demotion risk loudly instead so a human could intervene. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: J-07's checklist steps are mostly vacuous for a research batch with zero candidates, and the rules don't say whether a vacuously-satisfied step counts as demonstrated. We chose: score J-07 passing, since the project's own completion rules bless "zero compiled candidates" as a valid honest ending, and the screen shows explicit honest empty-state text rather than a blank. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: three record-keeping integrity gaps were labeled "owner-only" in the iteration state, but the project's own rules authorize automatic repair of this exact kind of gap before any real result is ever read, and this era's real research batch has zero candidates so no result will ever be read. We chose: read the "owner-only" label narrowly — it covers only the one disclosed policy finding, not routine record-keeping repair — and fixed the three gaps itself this iteration using already-proven, unchanged logic. Reversible: no (the record regeneration and the permanent lock that follows it are one-way once committed)
- iter-5 · goal-evaluator — Ambiguity: a plain continue verdict would have been automatically downgraded to a lighter review pass right before the era's second permanent, irreversible step, with three open integrity findings bearing directly on that step. We chose: escalate to force the full, careful review pass rather than continue with a recommendation the system would have overridden. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: the "only one real research batch, ever" rule is worded absolutely, but the project's own rules allow a repair "only before any real result has been read" — which is exactly what happened when a first real batch was made, found to contain one unsupported claim, and regenerated before anything was committed or read. We chose: score it a minor, unresolved finding rather than a severe one, since nothing was ever published under the discarded version and the whole sequence was disclosed openly. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: one checklist step asks to confirm the full list of candidates is visible on screen, but that list never rendered a single row because the real research batch ended up with zero candidates. We chose: score that journey passing, since the project's own rules bless a zero-candidate outcome as valid and the screen shows an honest empty-result message rather than a blank. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: the goal document names specific research-card IDs that don't exist as separate records, because the finished list combines or splits some of them into single entries. We chose: accept that grouping and count the requirement as met, since every original ID is still traceable through a cross-reference list and an independent reviewer confirmed the reading. Reversible: no (the research batch is now permanently locked; changing the grouping would require a second batch)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-hypothesis-foundry-iter-7.md |
| Dev handoff | — | docs/handoffs/goal-hypothesis-foundry-iter-7-dev.md |
| Review | PASS | reports/reviews/goal-hypothesis-foundry-iter-7-review.md |
| Browser QA | PASS | reports/phase-goal-hypothesis-foundry-iter-7-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-hypothesis-foundry-iter-7-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-hypothesis-foundry-iter-7-user-visible-changes.md |
| What to click | — | reports/phase-goal-hypothesis-foundry-iter-7-what-to-click.md |
| UI surface map | — | reports/phase-goal-hypothesis-foundry-iter-7-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-hypothesis-foundry-iter-7-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-hypothesis-foundry-iter-7-ux-regression.md |
| QA | PASS | reports/qa/goal-hypothesis-foundry-iter-7-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-hypothesis-foundry-iter-7-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-hypothesis-foundry-iter-7-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-hypothesis-foundry/iter-7/eval.md |
| Journey history | — | runs/goal-session-hypothesis-foundry/state/journey-history.json |
