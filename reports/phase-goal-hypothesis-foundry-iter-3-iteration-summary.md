# Iteration Summary — goal-hypothesis-foundry-iter-3

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-27
**Iteration:** 3

## In plain words

**What you can do now:** Open the Desk page and look at the new "Hypothesis Foundry" section. It confirms this is a fresh, self-contained research chapter, shows that the previous chapter's endless-research loop has been switched off, and displays the real starting numbers this new chapter will be measured against.

**What changed this time:** The Foundry's inner machinery — the piece that runs a practice research trial from start to finish — was proven working end-to-end for the first time, all at once, in one combined test covering every possible outcome. Two behind-the-scenes safety details were also tightened: resuming an already-finished trial now double-checks its numbers before handing back a result, and every source idea's record now carries a tamper-proof fingerprint plus a note of which other idea, if any, it is a legal alternate version of. Nothing new appears on the Desk page yet — all of this happens behind the scenes.

**What's next:** Build the one Foundry screen so people can finally see this proven machinery at work, which should let several more of the chapter's checklist items turn green at once.

## Headline

Foundry's five backend modules proven together in one composite hermetic "complete factory" test

## Direction

**Signal:** holding
**Why:** No journey newly reached full passing status this iteration and none regressed — J-05 "The complete factory passes hermetic known-null, planted-effect, leakage, and honest-stop oracles" moved from failing to partial after the composite hermetic oracle suite proved all five Foundry modules together, and two long-carried blockers closed (J-04's resume-identity gap, J-02's missing `SourceRecord` fields). J-06/J-07/J-08 remain correctly un-attempted until the goal's own required next stage (an operator-visible Foundry screen) exists, so overall standing holds steady rather than advancing to a full pass this round.

**Trend (last 4 iters):**
- Newly passing this iter: none
- Newly passing in last 4 iters total: J-01 (iter-2)
- Regressions in last 4 iters: none
- Anti-goal violations in last 4 iters: none
- Iters with no journey state change: 0 of last 4

**Latest evaluator reasoning:** The deep reviewer found two real holes in the proof — the practice run never once fed a candidate built by the real compiler into the real runner, and the all-blocked case never actually ran the runner — and fixed both during the review; I confirmed those two new checks exist and pass. Two small carried repairs also landed. Nothing here is visible to the operator yet, so no journey could be photographed, and none moved to done.

## What was done

- Product changes: apps/backend/tests/test_foundry_hermetic_epoch.py, apps/backend/app/research/foundry_runner.py, apps/backend/app/research/foundry_source_registry.py, apps/backend/tests/test_foundry_source_registry.py, apps/backend/tests/test_foundry_compiler.py, apps/backend/tests/test_foundry_runner.py, docs/hypothesis-foundry-spec.md
- Built the composite hermetic "complete factory" oracle suite (TC-1..TC-8) proving all five Foundry modules (compiler → interpreter → family → ledger → runner) together on one practice epoch containing every outcome type at once.
- Proved crash/resume behavior: a 20-candidate practice run interrupted mid-epoch resumes cleanly, verifying and skipping already-finished candidates with zero duplicate records.
- Proved fail-closed behavior on protected-data access: a candidate that hits sealed/off-limits data during evidence gathering is refused outright, with no fabricated result of any kind.
- Closed a resume-identity gap: an already-finished candidate's numbers are now re-verified against the current request before being handed back, refusing on drift instead of silently returning a stale result.
- Added the two missing `SourceRecord` fields the written methodology spec already promised — a tamper-evident source fingerprint and a legal-alternate-version disclosure.
- The hard auditor found and fixed two completeness gaps in the delivered proof during review (the compiler-to-runner seam was never exercised; the all-blocked case never actually ran the runner) — both now closed and independently re-verified.
- Verified 1 target journey (J-01) still passes browser QA via regression replay.

## What's left

- Journey J-06 (One complete real epoch is generated and committed with zero Foundry outcome reads) failing — correctly not yet attempted; forbidden until the machinery and read surface are fully proven.
- Journey J-07 (Goal Mode deterministically exhausts the frozen real epoch without changing science) failing — needs a real committed epoch and a first-read lock that don't exist yet.
- Journey J-08 (The operator sees the final Foundry truth and all foundation rails still hold) failing — the safety rails are healthy, but there is nothing yet for an operator to look at.
- Journeys J-02, J-03, J-04, and J-05 stay partial — their underlying machinery is proven, but none has an on-screen Foundry view yet; twenty-two on-screen checks between them have never been photographed.
- Known limitation: the protected-data-trip proof is hermetic-only; the real data-access guard is not yet wired into the Foundry runner's real-corpus path.
- Known limitation: the "which files are locked in" freeze scanner still checks only one folder deep, carried unchanged from an earlier iteration.
- Carried, non-blocking: the mid-candidate crash-resume path still double-checks one number (the cost floor) but not the other (the manifest fingerprint) before resuming.

## Next step

Build the one Foundry screen. Every remaining piece of machinery is now proven in the test bench, but an operator still cannot see any of it, and that is the single reason J-02 "Sources compile into auditable CandidateSpecs", J-03 "Generic interpretation preserves Scout decisions", J-04 "Foundry owns the denominator, ledger, freeze barrier and lock" and J-05 "The complete factory passes hermetic oracles" are all stuck at partly done — twenty-two on-screen checks between them, and zero of those checks have ever been photographed. This is the next required stage in the goal's own order (step 5, the read surface showing fixture states while the real epoch stays unopened), and it is the only work that can turn four journeys green at once.

Carry three small, already-written-down repairs in the same iteration so they are closed before real sources get authored: (1) add a batch check that refuses a source record naming a sibling that does not exist or is not in its own family, so a typo cannot enter the frozen registry silently; (2) extend the restart check to the crash path as well, not only the already-finished path; (3) correct the QA report's habit of claiming the J-01 screen check was covered by the backend test run — it was not; it is covered by the browser replay, and the report should cite that artifact.

One thing for the operator to decide, unchanged for four iterations: the session is capped at 60 iterations and the goal document asks for 80. Run the next iteration at full depth, since it ships the first real Foundry screen and needs the browser and design review lanes.

## Assumptions made

- iter-3 · goal-decomposer — Ambiguity: Constitution §1.4 requires every source record disclose every finite alternative the compiler may enumerate, but the spec's own §1.4 field table doesn't yet define `alternatives`'s shape, and §2.1/2.2 frames alternatives as separate sibling records sharing one family key. We chose: add `alternatives` as a per-record disclosure field naming its legal sibling(s), additive on top of the existing family-key mechanism, not a replacement for it. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: whether proving hermetic fail-closed reads on withheld/sealed data requires wiring the real data accessor into the runner this iteration, since the spec marks that wiring "future work" and prior handoffs put it in a later stage. We chose: prove the fail-closed contract hermetically using the real exception types, without wiring the real accessor into the runner's real-corpus path this iteration. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-05's acceptance steps are worded as hermetic test runs rather than on-screen inspections, so the reasoning that capped J-02/J-03/J-04 at partial (their steps demand a missing view) doesn't literally apply to it. We chose: still score J-05 partial, not passing — no screenshot exists, and the chapter's own design expects an on-screen rendering of these fixture states. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: two of the fixes counted as evidence this iteration were made by the auditor during its own review pass, raising a self-verification concern. We chose: count them, but only after independently opening and re-running the added tests myself rather than trusting the audit's own report. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: whether pointing the test copy of the site at the real recorded era-open numbers (read-only) counts as blurring fixture data with real data. We chose: this is not fabrication — it is a genuine, read-only view of the real recorded artifact, so it is allowed. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: where the line falls between building the exhaust runner's own mechanics this iteration versus the full multi-outcome "complete factory" epoch. We chose: build and prove the runner's core mechanics (order, checkpoint/resume, single-flight, replay refusal) this iteration; reserve the full multi-outcome epoch for the next iteration. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: whether journeys whose steps are all on-screen inspections of a view that doesn't exist yet should score failing or partial, given the real machinery underneath is proven. We chose: score both partial, following the same precedent already set for an earlier journey. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: whether journeys never yet targeted by any iteration should count as "repeat failures" that force an automatic escalation. We chose: no — untargeted, order-blocked journeys don't count as the repeat-failure signal. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: whether "first source records" means authoring the real 11 required source objects or building the compile machinery proven on synthetic fixtures. We chose: build the compile-rule machinery first, on the 7 hermetic fixture types the journey's own steps name; leave the real 11-object registry for a later iteration. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: whether the Sources/Compiler screen could ship early since it only renders synthetic fixture data. We chose: defer all Foundry subsection UI to one later, consolidated read-surface iteration rather than building it piecemeal. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: how to score a journey whose steps are all on-screen checks of a view that was deliberately deferred, when the substance underneath is real and independently re-run. We chose: score it partial, not failing, but record that no UI step has evidence. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: whether a journey's still-unproven last step (baseline shown but reading "not recorded yet") counts as a mere capture defect rather than a real product gap. We chose: no — keep the journey partial, since the described behavior has never actually been observed working. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: whether journeys named in the browser-infrastructure token but with no fresh screenshot should score partial (infra-pending) or failing, when independent evidence shows their surfaces don't exist at all. We chose: score them failing based on that independent evidence, to avoid wasting an iteration on a make-up ride over surfaces that don't exist. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-hypothesis-foundry-iter-3.md |
| Dev handoff | — | docs/handoffs/goal-hypothesis-foundry-iter-3-dev.md |
| Review | PASS | reports/reviews/goal-hypothesis-foundry-iter-3-review.md |
| Browser QA | PASS | reports/phase-goal-hypothesis-foundry-iter-3-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-hypothesis-foundry-iter-3-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-hypothesis-foundry-iter-3-user-visible-changes.md |
| What to click | — | reports/phase-goal-hypothesis-foundry-iter-3-what-to-click.md |
| UI surface map | — | reports/phase-goal-hypothesis-foundry-iter-3-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-hypothesis-foundry-iter-3-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-hypothesis-foundry-iter-3-ux-regression.md |
| QA | PASS | reports/qa/goal-hypothesis-foundry-iter-3-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-hypothesis-foundry-iter-3-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-hypothesis-foundry-iter-3-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-hypothesis-foundry/iter-3/eval.md |
| Journey history | — | runs/goal-session-hypothesis-foundry/state/journey-history.json |
