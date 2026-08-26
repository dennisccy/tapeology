# Iteration Summary — goal-hypothesis-foundry-iter-2

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-26
**Iteration:** 2

## In plain words

**What you can do now:** Open the Desk page and expand the "Hypothesis Foundry" section. It shows this is a brand-new, self-contained research chapter, with the previous chapter safely closed off and untouched. It also now shows the real starting numbers (test-suite counts and a code fingerprint) this chapter will be checked against, instead of a "not recorded yet" placeholder.

**What changed this time:** The Desk page's "Hypothesis Foundry" section now displays the real recorded starting numbers instead of the placeholder text it showed last round. Behind the scenes, the team also built the rulebook that will run each already-approved trading idea through Tapeology's existing fair-test process — there is nothing new to look at for this part yet, but it was proven to give the exact same answer as the existing check on every practice example tried.

**What's next:** Next, the team will build one big practice run that tries every possible outcome at once — a good idea, a blocked idea, too little data, no effect, the wrong direction, and one that survives — to prove the whole system handles every case honestly. Two small fixes ride along: making a restart correctly refuse an idea whose details changed instead of reusing an old answer, and filling in two missing pieces of information in each idea's record.

## Headline

J-01 passes; Foundry's frozen-decision machinery lands and matches Scout byte-for-byte

## Direction

**Signal:** improving
**Why:** J-01 ("The Foundry opens as a new finite era") newly passed after the QA-rig visibility gap was closed the honest way — real recorded values, no invented data. J-03 and J-04 moved from failing to partial as five new hermetic backend modules (`foundry_interpreter.py`, `foundry_family.py`, `foundry_freeze.py`, `foundry_ledger.py`, `foundry_runner.py`) landed and were proven byte-identical to the existing Scout decision path across 71 tests. ESCALATE fired only because the engine's budget rule demoted a spec-declared full-depth iteration to lean, and the lighter review still surfaced one real integrity hole in the runner's restart path — not because anything regressed.

**Trend (last 3 iters):**
- Newly passing this iter: J-01
- Newly passing in last 3 iters total: J-01
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: none
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** The blocker that held the first journey back for two iterations is gone, and it was closed the honest way. The Desk page now shows the true recorded opening numbers, and I checked them myself rather than trusting the report: I recomputed all six Referee file fingerprints and they match the stored record, the numbers on screen match that record exactly, and the test rig was fixed by copying the real recorded file in — with a plain "not recorded yet" fallback if no real file exists, so nothing is invented. The real file was not touched (its timestamp predates this run). Five new back-end pieces landed and I re-ran all 71 of their tests myself: they pass, and the key one is a genuine comparison test — it runs the same case through the old proven path and the new path and demands the entire result be identical.

## What was done

- Product changes: apps/backend/app/research/foundry_interpreter.py, apps/backend/app/research/foundry_family.py, apps/backend/app/research/foundry_freeze.py, apps/backend/app/research/foundry_ledger.py, apps/backend/app/research/foundry_runner.py, apps/backend/tests/test_foundry_interpreter.py, apps/backend/tests/test_foundry_family.py, apps/backend/tests/test_foundry_freeze.py, apps/backend/tests/test_foundry_ledger.py, apps/backend/tests/test_foundry_runner.py, apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
- Fixed the QA-rig visibility gap: the scoped test backend now serves the real recorded era-open baseline instead of "not recorded yet", completing J-01.
- Built the generic Foundry interpreter (`foundry_interpreter.py`): population resolution, symmetric timing, and a Scout-boundary adapter proven byte-identical to the existing direct Scout path.
- Built the family denominator module (`foundry_family.py`): frozen per-family variant counts, whole-family over-cap blocking, and unconditional late-insertion refusal.
- Built the freeze/manifest module (`foundry_freeze.py`): idempotent manifest replay, drift refusal instead of a silent second epoch, an AST-based freeze-set generator, and a first-read-lock integrity check.
- Built the hash-chained Foundry trial ledger (`foundry_ledger.py`) with checkpoint/resume and single-flight protection, kept structurally separate from the existing Scout ledger.
- Built the runner (`foundry_runner.py`): canonical-order exhaustion and mechanical Scout-verdict mapping.
- Added 39 new hermetic tests; full backend suite passed 3825/8 skipped/0 failed, no regressions from the iter-1 baseline (3787/8).
- Verified 1 target journey (J-01) pass browser QA.

## What's left

- Journey J-05 (The complete factory passes hermetic known-null, planted-effect, leakage, and honest-stop oracles) failing
- Journey J-06 (One complete real epoch is generated and committed with zero Foundry outcome reads) failing
- Journey J-07 (Goal Mode deterministically exhausts the frozen real epoch without changing science) failing
- Journey J-08 (The operator sees the final Foundry truth and all foundation rails still hold) failing
- J-02, J-03, and J-04 are all partly done: their backend logic is real and tested, but none has an on-screen view yet for a person to check — a single consolidated screen is planned for a later iteration
- Open defect: on restart, a candidate whose inputs changed is silently handed its old stored result instead of being refused (`foundry_runner.py:89`) — flagged by the reviewer, not yet fixed
- `SourceRecord` still lacks the "alternatives" and "source hash" fields the written method document already promises — needed before real sources are authored
- No command-line entry point exists yet to actually run the new exhaust machinery end-to-end

## Next step

Run the next iteration at full depth — this is the point of the ESCALATE verdict, since a depth recommendation alone was already overridden by the budget rule last time. Target J-05, "The complete factory passes hermetic known-null, planted-effect, leakage and honest-stop oracles" — the only legal next stage: one mixed practice run containing every outcome type at once (compiled, blocked, too-few-samples, null, wrong-direction, the three kill types, and a survivor), plus an all-blocked run, an all-killed run, and the protected-data trip tests that must fail shut. Two small repairs should ride along in the same iteration: fix the restart path so a resumed candidate whose inputs have changed is refused instead of quietly handed the old stored result (`apps/backend/app/research/foundry_runner.py:89`), and add the two missing record fields `alternatives` and `source_hash` that the written method document already promises.

## Assumptions made

- iter-2 · goal-evaluator — Ambiguity: J-03's five and J-04's six acceptance steps are all on-screen fixture inspections deferred by design this iteration, so zero assertion steps have browser evidence even though the underlying machinery is real and independently re-verified. We chose: score both journeys `partial` (not `failing`), following the same precedent set for J-02 in iter-1, after independently re-running all 71 Foundry tests and confirming the equivalence oracle compares the whole screen dict against the pre-existing direct Scout path. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: the "same journey failed 2+ consecutive iterations" escalation rule would technically fire on J-05..J-08, which have been failing since iter-0, but they are staged-out journeys the goal's binding order forbids attempting yet. We chose: not to treat never-targeted, order-blocked journeys as that repeat-failure signal — ESCALATE was instead reached because a lean iteration surfaced cross-cutting complexity after the engine demoted a spec-declared full-depth iteration. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: whether pointing the scoped test backend's foundry-directory resolver at the real, already-recorded era-open baseline folder (read-only) counts as blurring the line between fixture and real views. We chose: this is not fabrication or a blur — the served value is the genuine recorded artifact, access is read-only with no write to any protected path, and the prior iteration's own lesson named exactly this fix. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: the goal's execution-order steps don't draw an exact line for how much of the exhaust runner's own mechanics (canonical order, checkpoint/resume, single-flight, replay refusal) belong to this iteration versus the later full "complete factory" proof. We chose: this iteration builds and hermetically proves the runner's mechanics, while the full multi-family, multi-verdict-type factory proof and protected-data trip fixtures stay reserved for next iteration. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's last step (the era-open baseline block) could arguably count as a "capture defect, not a product failure" since the underlying data was genuine and the panel behaved correctly for an empty store. We chose: not to apply that exemption and to keep J-01 `partial`, since nobody had yet observed the asserted behavior and the fix needed a test-rig change, not a mere re-capture. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-02's five acceptance steps are all on-screen inspections of a view that was deliberately deferred, so none of its steps has browser evidence even though its backend compile rules are real and independently re-run. We chose: score J-02 `partial`, not `failing`, on the strength of the independently re-run tests, while recording that no UI step has evidence and that a required data field is still missing. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: the goal's methodology document didn't say whether "first source records" meant authoring the real required source objects or building the compile machinery proven on synthetic fixtures. We chose: build the compile-rule machinery and prove it on the seven hermetic fixture source types the journey names, leaving the real source registry content for a later iteration. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: nothing forbids building the Sources/Compiler fixture view early, since it would render only synthetic data. We chose: defer all Foundry subsection UI to the single later iteration that ships one consolidated read surface, rather than extending a partial UI three separate times. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: the rule for a journey with no fresh screenshot forbids scoring it `failing` on infra absence alone, yet seven journeys had independently confirmed proof their surfaces don't exist at all. We chose: score those seven journeys `failing` (and J-01 `partial`) on that independent evidence rather than spend an iteration on a wasted verify-only pass. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-hypothesis-foundry-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-hypothesis-foundry-iter-2-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-hypothesis-foundry-iter-2-review.md |
| Browser QA | PASS | reports/phase-goal-hypothesis-foundry-iter-2-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-hypothesis-foundry/iter-2/eval.md |
| Journey history | — | runs/goal-session-hypothesis-foundry/state/journey-history.json |
