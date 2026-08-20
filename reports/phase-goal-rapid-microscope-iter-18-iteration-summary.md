# Iteration Summary — goal-rapid-microscope-iter-18

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-08-20
**Iteration:** 18

## In plain words

**What you can do now:** On the Desk page, people can see an honest tally of how much market data is ready to use, watch buying and selling pressure calculated tick by tick without looking into the future, see how price levels line up with that pressure, browse a permanent record of every trading idea the product has tried (kept or rejected, nothing hidden), see how those ideas performed walking forward through time, and check whether any idea has passed the strict final locked-away test (none has yet). The same information is also available through a Claude conversation.

**What changed this time:** Behind the scenes, the internal rule that decides whether a locked-away ("sealed") test result earns a permanent "pass" now sets its own strict minimum — it needs 30 real readings and refuses to let anyone hand it a smaller number, closing a loophole where a single reading could have been rubber-stamped as a pass. It also now honestly labels measurements that don't apply at this stage instead of showing a misleading number. Nothing changed on any screen; the double-checker separately caught and fixed a small test-setup glitch this same change accidentally caused, before it reached any real record.

**What's next:** Next, the product needs one owner decision — where the "is this result big enough to matter" money threshold and its evidence label should come from — so the same locked-away judge can police those too, not just the reading count. After that, the last piece of the "nothing broke" safety check (proving repeated runs give identical results) is next, before any real trade data can ever be recorded.

## Headline

The sealed-shard pass/fail judge now owns its own minimum sample size

## Direction

**Signal:** stalling
**Why:** J-10's safety-test set reached 30 of 30 this round and the caller-supplied sample-size loophole (TR-30) genuinely closed, proven by execution rather than by reading. But no journey crossed a status line — J-01 through J-08 stayed passing, J-06 and J-10 stayed partial, and J-09 "The pilot studies" stayed failing (still unbuilt by design) — the third iteration running (16, 17, 18) with an unchanged set of journey statuses. The independent auditor also caught a real regression this round (J-08's and J-10's golden checks were silently broken mid-round, invisible to review and QA because the browser lane never ran) and fixed it before the round closed — the seventh straight round the evaluator has escalated to keep that lane mandatory.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: none
- Regressions in last 3 iters: none persisted — iter-18: J-08's and J-10's golden-script assertions were silently broken mid-round by a shared test-fixture change, but the independent auditor caught and repaired both before the round closed, so no lasting regression was recorded
- Anti-goal violations in last 3 iters: 7 new minor items opened (2 in iter-16, 2 in iter-17, 3 in iter-18); 5 older minor items closed in the same span; no critical violations opened or left unresolved
- Iters with no journey state change: 3 of last 3 (only 3 evaluator-log entries available)

**Latest evaluator reasoning:** "The one hard job of this round is genuinely done. The rule that decides whether a sealed result counts now owns its own minimum sample size: it refuses any number handed to it from outside, it needs 30 readings, and it writes 'does not apply to one hidden day' for the two breadth figures instead of quietly writing 1. I proved that myself by breaking the shipped file twice and watching the right tests go red, then putting the file back byte for byte. The bad news is about the checking machinery, not the product."

## What was done

- Product changes: apps/backend/app/research/micro_sealed_evaluation.py, apps/backend/tests/test_micro_sealed_evaluation.py, apps/backend/scripts/seed_micro_graduation_iter18_fixture.py, apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
- Rewrote the sealed-evaluation rule so it owns its own minimum sample size (30 observations), deleting the caller-override mechanism (`_resolved_floors`) and refusing any candidate spec that tries to hand in a floor.
- Session/symbol breadth fields on the persisted record now read the honest literal `not_applicable_single_shard` instead of a silent `1`; the rule-hash computation was updated to match what actually runs.
- Added a QA-only fixture-seeding script that plants a real, passing sealed-evaluation record so the Graduation endpoint (J-07) returns a genuine, checkable result for the first time this era, instead of an always-empty body.
- Closed two long-standing coverage gaps (B3: exact-instant exposure boundary, B4: trade-terminated session finalize) in the accessor and observer test suites.
- Independent auditor found and fixed a mid-round regression: the new seed script silently broke J-08's and J-10's golden test assertions by adding a real record to the shared QA test rig; both were repaired, re-verified, and confirmed to have caused no other damage.
- Verified 8 journeys (J-01–J-06, J-08, J-10) pass browser QA via the independent auditor's own replay run, plus J-07 "Graduation" via a newly discriminating screenshot — since the pipeline's own browser and replay lanes did not run this round.

## What's left

- Journey J-09 "The pilot studies" failing — still unbuilt by design, out of scope for the sixth round running; blocked until the money-floor loophole below is closed.
- Journey J-06 "The recorder and the Vault" partial — its remaining step needs an operator to record real market tape, which is forbidden by standing instruction.
- Journey J-10 "The kept product stands" partial — one gap left: proving that re-running the same work twice over unchanged stored data gives identical results.
- The sealed-evaluation judge still lets the caller supply the economic (money) floor and the evidence label — the same kind of loophole TR-30 just closed for the sample-size floor, one condition over; needs an owner decision on where those values should actually come from.
- Four stored replay checks (for J-02–J-05) currently can't fail — each only asserts an unrelated page heading and needs to be made to actually check its own subject.
- The quality-check lane reported "pass" this round even though a required verification lane (browser QA) never ran — needs a rule so that can't happen again.

## Next step

Run the next iteration as a full round with the independent checker, and set the spec's Frontend Present to "yes" so the browser and replay lanes actually run this time — this round's spec said "no frontend," which is exactly what let the mid-round regression slip through unseen. In order: (1) close the sealed judge's remaining loophole — the money floor and evidence label are still caller-supplied — but this needs one owner decision first, namely where a candidate's pre-registered money floor and evidence label should come from; if unanswered when the round starts, build the rest and leave this one waiting rather than guess; (2) finish J-10's last piece, the repeat-run determinism check; (3) make the four non-discriminating replay checks (J-02–J-05) able to actually fail; (4) stop the quality lane from reporting "pass" when a required check didn't run, and have it report which data store the browser run actually used; (5) record the standing rule that a change to the shared test rig requires re-running the full replay set before the round is called done. Do not record real tape, and do not start J-09 yet.

## Assumptions made

- iter-18 · goal-decomposer — Ambiguity: whether a stored golden replay script may assert an honest current empty-state string, given that a future iteration could make that state non-empty. We chose: yes, provided the wording is copied verbatim from the endpoint's real current copy, the run artifact names which store it ran against, and the assertion is revisited once that endpoint's honest state goes non-empty. Reversible: yes.
- iter-18 · goal-evaluator — Ambiguity: whether the independent auditor editing two golden replay scripts (J-08, J-10) so they match a newly-seeded real record is a forbidden "edit a test to make it pass" (forcing a regression halt) or a sanctioned assertion refresh. We chose: sanctioned refresh — J-08 stays passing, J-10 stays partial, no regression declared; the product's behavior didn't change, only the assertion's premise did, the new string is strictly more discriminating than the old one, and this exact policy was pre-authorized in the round's own spec notes. Reversible: yes.
- iter-18 · goal-evaluator (second) — Ambiguity: whether the sealed judge's still-caller-supplied economic (money) floor is a critical anti-goal violation of "never manufacture a survivor," forcing a hard halt, or a minor open item. We chose: minor and open — no production caller reaches it, no survivor exists, the code is pre-existing (this round improved the same rail elsewhere), and the spec revision explicitly scopes this floor out of this round's work; escalated to the owner through the next-step recommendation instead of halting. Reversible: yes — becomes critical immediately if any production caller or real sealed-evaluation row appears.
- iter-18 · goal-evaluator (third) — Ambiguity: whether escalating to a full-depth round is available when the decision tree's literal trigger clauses don't fire — the seventh consecutive time this exact question was asked. We chose: escalate anyway, a deliberate departure from the tree's literal text, because this is the only round where the browser and replay lanes didn't run at all and a real regression shipped invisibly past review and QA — the tenth such escape this session. Reversible: yes — only sets the next iteration's depth, halts nothing.
- iter-17 · goal-evaluator — Ambiguity: whether a mechanism that would permit a manufactured survivor, but that no shipped path can reach, counts as a critical violation of the "never manufacture a survivor" anti-goal. We chose: minor and open — zero production callers, no sealed-evaluation row on disk, the round strictly improved this rail, and the owner ruled the same day, so a halt would re-ask an already-answered question. Reversible: yes — reopens as critical the moment any production caller or sealed row appears.
- iter-17 · goal-evaluator (second) — Ambiguity: whether journey J-07 "Graduation" sustains "passing" status when its owning module was rewritten but its designated check (an empty JSON response) can't tell a working module from a broken one. We chose: passing, with the weakness carried as a passenger rather than a status downgrade — the behavior was triply mutation-proved by execution even though the check itself can't discriminate. Reversible: yes — the recommended fix (seed one real family into the rig) makes the check discriminating and can reopen the journey if it then shows misbehavior.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-rapid-microscope-iter-18.md |
| Dev handoff | — | docs/handoffs/goal-rapid-microscope-iter-18-dev.md |
| Review | PASS | reports/reviews/goal-rapid-microscope-iter-18-review.md |
| Browser QA | SKIPPED | reports/phase-goal-rapid-microscope-iter-18-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-rapid-microscope-iter-18-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-rapid-microscope-iter-18-user-visible-changes.md |
| What to click | — | reports/phase-goal-rapid-microscope-iter-18-what-to-click.md |
| UI surface map | — | reports/phase-goal-rapid-microscope-iter-18-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-rapid-microscope-iter-18-ui-test-plan.md |
| QA | PASS | reports/qa/goal-rapid-microscope-iter-18-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-rapid-microscope-iter-18-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-rapid-microscope-iter-18-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-rapid-microscope/iter-18/eval.md |
| Journey history | — | runs/goal-session-rapid-microscope/state/journey-history.json |
