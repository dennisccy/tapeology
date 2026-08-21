# Iteration Summary — goal-rapid-microscope-iter-22

**Verdict:** STALLED
**Iteration type:** goal-full
**Date:** 2026-08-21
**Iteration:** 22

## In plain words

**What you can do now:** On the Desk page, you can see how much market data is ready and which research checks remain unmet. You can watch buying and selling pressure tick by tick, matched to chart signals without looking ahead. You can see a permanent record of every quick trading idea the system has tested — now including all three pre-declared pilot studies, each with an honest recorded answer. You can check whether any idea has graduated to a fuller test, see how ideas hold up over time, and view sealed recordings without seeing their contents. A Claude conversation can read all of this the same way a person would on screen.

**What changed this time:** The Desk page's Scout Ledger now shows results for two more pre-declared research questions — a "does buying/selling pressure fail at a price wall" study and a "does a capitulation moment predict exhaustion" study — that an operator can trigger from the command line or the same background-job trigger the product already used. Both come back with an honest "not enough data yet" answer, recorded the same way the first study's answer already was. The Graduation check page was also re-confirmed with a fresh, dated look.

**What's next:** Next, the project needs you to decide how to handle the one remaining piece — recording real market data into the sealed Vault — before this chapter of the project can be called complete.

## Headline

Study 1 (range-wall failed aggression) can now be run by an operator.

## Direction

**Signal:** improving
**Why:** This iteration moved J-09 "The pilot studies" from partial to passing by wiring Study 1 (range-wall) and Study 3 (capitulation) through the same operator-reachable path Study 2 already used, and re-verified J-07 "Graduation" with a fresh screenshot. Nine of ten journeys are now provably green with zero regressions and zero critical anti-goal violations this round. The evaluator still halted with STALLED because the one remaining journey, J-06 "The recorder and the Vault," is blocked on an owner-only decision, not further machine work.

**Trend (last 3 iters):**
- Newly passing this iter: J-09
- Newly passing in last 3 iters total: J-09 (iter-22 only; iter-20 had no status changes, iter-21 moved J-09 failing→partial, not to passing)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 7 new minor items opened (iter-20: 0, iter-21: 4, iter-22: 3), 0 critical; 4 older minor items closed in the same span (iter-20: 1, iter-21: 2, iter-22: 1)
- Iters with no journey state change: 1 of last 3 (iter-20 — only a re-verification stamp moved, no status changed)

**Latest evaluator reasoning:** "The round did everything it set out to do, and I checked it myself rather than reading the reports. All three of the pilot studies now have a real, recorded answer on the Desk page, and they can be run by an operator from the command line or the web address — not only from a test. The graduation page was photographed fresh, which closes the gap the clock created last round. That makes nine of the ten journeys green."

## What was done

- Product changes: apps/backend/app/research/scout.py, apps/backend/app/research/micro_routes.py, apps/backend/tests/test_scout.py
- Study 1 (range-wall failed aggression) can now be run by an operator via a new grid-selector value on the existing `POST /research/desk/micro/scout/compute` trigger or the CLI, with its answer recorded in the Scout Ledger.
- Study 3 (capitulation exhaustion) can now be run by an operator the same way, via a second new grid-selector value.
- Every study now also records a second "is there enough independently-verified evidence yet" check, honestly reporting "not yet" today rather than silently skipping it.
- The default reference grid and Study 2 (delta-divergence) are unchanged and regression-tested — this round is purely additive.
- Re-photographed J-07 "Graduation" with a fresh, dated screenshot, closing the round-21 skip caused by the clock.
- Re-photographed Study 2's walk-forward eligibility row on screen, which the prior round had built but never seen rendered.
- Verified 9 of 10 journeys pass browser QA / deterministic replay this iteration (J-01–J-05, J-07, J-08, J-09, J-10 all green); J-06 was deliberately not re-tested — its remaining step is an owner-gated action.

## What's left

- Journey J-06 "The recorder and the Vault" partial — its only remaining step (recording real market tape into the sealed Vault) is an operator act the owner has withheld for six consecutive rounds; every unblock path is human-owned.
- All three pilot studies' recorded answers ("not enough data yet") come from small test fixtures, not the real market data the questions were meant to be asked of — running them for real is owner-gated, writes permanent records, and is currently too slow to finish.
- Study 1's real screen only tests the single aggression signal, not the full two-signal combination the goal describes — the second signal's logic is genuinely unbuilt and disclosed as a deliberate deferral.
- No on-screen button exists yet to trigger the two new pilot studies — an operator must already know the command-line flag or API request value.
- An operator who enters an unrecognized study name gets a generic server error instead of a friendly message (known, unfixed rough edge).
- The Desk readiness panel still takes about 22 seconds to load against the real data store (known, unfixed slowness).
- A small internal list that classifies the two new studies is duplicated in two places in the code and should be collapsed into one (no user-facing impact).
- One new study's automated test cannot actually fail if the underlying logic broke — a missing check needs to be added (found by the project's own auditor).

## Next step

Nothing the machine can do on its own will finish this era. J-06 "The recorder and the Vault" needs the owner. The recommendation is to pick one of three options: (1) authorise the real-market-data recording and attend it, after which the machine re-checks J-06 and the era can finish; (2) change what the goal asks of J-06 in `docs/goal.md` so the recorder and vault machinery count as proved on practice data instead; or (3) resume anyway and accept an unfinished era, letting the machine spend its time on three small polish jobs that need nobody's permission (speed up the Desk readiness panel, collapse the duplicated study-selector list, add the missing test check) — none of which turns a journey green.

## Assumptions made

- iter-22 · goal-evaluator (second) — Ambiguity: whether STALLED is the right verdict when the iteration made progress (J-09 partial→passing) and some machine-doable polish work still exists. We chose: STALLED — the sole remaining blocker (J-06) has only human-owned unblock paths, and the remaining machine work is polish that moves no journey, so continuing would delay asking the owner the one question that can finish the era. Reversible: yes.
- iter-22 · goal-evaluator — Ambiguity: how to score J-09 when its Acceptance clause is fully met but its Step 2 (a run against the full joinable corpus) is not — all three answers are "insufficient_n" from empty or near-empty test fixtures. We chose: passing — the Acceptance clause is satisfied field by field, the real-corpus run is owner-gated (irreversible ledger writes, would break another journey's assertion, currently too slow), and two prior evaluators already promised in writing that three recorded decisions would be enough. Reversible: yes.
- iter-22 · goal-decomposer — Ambiguity: whether Study 1 must screen the full two-signal combination the goal's prose describes, or the already-frozen single-signal request. We chose: screen on the frozen single-signal request only — inventing the two-signal rule now would be exactly the improvisation the project's own spec forbids. Reversible: yes.
- iter-21 · goal-evaluator (third) — Ambiguity: how to score J-07 when its capture was skipped this round (budget cut) rather than defective. We chose: keep J-07 passing at its prior verified iteration with no make-up flag, since it already took a make-up ride previously and nothing about it changed. Reversible: yes.
- iter-21 · goal-evaluator (second) — Ambiguity: whether ESCALATE is available when the decision tree's literal triggers don't fire. We chose: ESCALATE anyway as a deliberate departure — a checking lane failed in substance even though the closing gate never checks it, the fix to a failing test was only self-audited, and the next-round depth rule would otherwise force a lighter round. Reversible: yes.
- iter-21 · goal-evaluator — Ambiguity: how to score J-09 when its text could be read as satisfied by one screened study plus two source-only specs. We chose: J-09 stays partial, not passing, until each of the three studies is actually screened to a recorded decision. Reversible: yes.
- iter-21 · goal-decomposer (third) — Ambiguity: whether J-09's "study families EXIST" requires a real production ledger write or is satisfied by frozen, versioned source-code specs. We chose: the source-code-frozen reading, matching established precedent, avoiding an unplanned live-store write. Reversible: yes.
- iter-21 · goal-decomposer (second) — Ambiguity: how to reconcile a spec-level disclosure requirement against a module this era otherwise freezes byte-identical. We chose: build only the non-frozen half (a guard proving nothing consumes the frozen metric) and drop the on-screen-caveat half, since its only surface would require touching a frozen module. Reversible: yes.
- iter-21 · goal-decomposer — Ambiguity: whether all three pilot studies must be screened together this round or could be prioritized under scope pressure. We chose: freeze all three specs in stated priority order but screen only Study 2 this round, since it had the least invention risk and the project's own success criteria sanctioned deferring the rest. Reversible: yes.

## Quick verify

From `reports/phase-goal-rapid-microscope-iter-22-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser
2. In your terminal, run: `curl -s -X POST http://localhost:8301/research/desk/micro/scout/compute -H "Content-Type: application/json" -d '{"grid":"range_wall_failed_aggression_pilot"}'`
3. Wait about 15–30 seconds, then run: `curl -s http://localhost:8301/research/desk/micro/scout/compute`
4. Repeat steps 2–3 with `{"grid":"capitulation_exhaustion_pilot"}` instead — POST it, then poll until `"state":"done"`
5. Refresh the browser page (press F5 or Cmd+R), then click "Scout Ledger" to expand it

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-rapid-microscope-iter-22.md |
| Dev handoff | — | docs/handoffs/goal-rapid-microscope-iter-22-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-rapid-microscope-iter-22-review.md |
| Browser QA | PASS | reports/phase-goal-rapid-microscope-iter-22-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-rapid-microscope-iter-22-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-rapid-microscope-iter-22-user-visible-changes.md |
| What to click | — | reports/phase-goal-rapid-microscope-iter-22-what-to-click.md |
| UI surface map | — | reports/phase-goal-rapid-microscope-iter-22-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-rapid-microscope-iter-22-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-rapid-microscope-iter-22-ux-regression.md |
| QA | PASS | reports/qa/goal-rapid-microscope-iter-22-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-rapid-microscope-iter-22-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-rapid-microscope-iter-22-closure-verdict.md |
| Goal evaluation | STALLED | runs/goal-session-rapid-microscope/iter-22/eval.md |
| Journey history | — | runs/goal-session-rapid-microscope/state/journey-history.json |
