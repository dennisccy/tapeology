# Iteration Summary — goal-hypothesis-foundry-iter-0

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-26
**Iteration:** 0

## In plain words

**What you can do now:** Just getting started — nothing for users to try yet. This new research chapter (the Hypothesis Foundry) has not built any of its own screens or features yet. Everything from earlier chapters (the desk, cockpit, and structure map) still works exactly as before, untouched.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. This iteration checked what already exists for the new "Hypothesis Foundry" chapter: it confirmed the paperwork that opened the chapter is correctly in place, but found that none of the chapter's own tools exist yet. It also found a broken practice-sandbox setup script that stops the automatic screenshot-taking tool from running — that needs fixing first.

**What's next:** Next we'll fix the broken test setup so future work can be checked with real screenshots, then start writing the methodology and source list that the Foundry's candidate-building machinery needs.

## Headline

Baseline check: era-transition paperwork done, all 8 Foundry journeys otherwise unbuilt; zero code changes.

## Direction

**Signal:** holding
**Why:** This is iteration 0 — a zero-code-change baseline that established the true starting state for all 8 journeys. J-01 came back partial (era-transition paperwork done, but the /desk panel and era-open baseline record have no home yet) and J-02 through J-08 came back failing (entirely unbuilt, as expected before any Foundry code exists). No regressions or anti-goal violations occurred, and there is no prior iteration to compare against for stalling, so this reads as a clean starting line rather than momentum in any direction.

**Trend (last 1 iters):**
- Newly passing this iter: none
- Newly passing in last 1 iters total: none
- Regressions in last 1 iters: none
- Anti-goal violations in last 1 iters: none
- Iters with no journey state change: 0 of last 1

**Latest evaluator reasoning:** This was a no-change baseline, so the whole verdict rests on what the repository actually contains. I checked each journey myself instead of trusting the handoff: the paperwork that opens the new era is genuinely in place (old goal archived, dated opening note, the previous era's records untouched, the old self-extending proposer switched off), but every Foundry surface is absent — no `docs/hypothesis-foundry/`, no foundry module, no foundry route, no foundry test, nothing named "Hypothesis Foundry" on the desk page. The browser lane produced nothing at all: the guard that protects the operator's real data folder correctly refused to run, because the scoped test backend could not be started (a fixture script fails on a missing unit label). No screenshot exists, so no journey may be called passing.

## What was done

- No product change this iteration.
- Verified all 8 Must-have journeys (J-01..J-08) against current repo state via direct repository inspection: J-01 partial, J-02..J-08 failing.
- Confirmed era-transition paperwork is already complete (predecessor goal archived, dated opening note in `docs/research-directions.md`, old proposer's two-file opt-in broken).
- Recorded baseline reference: backend suite 3747 passed / 8 skipped / 0 failed, frontend `tsc --noEmit` 0 errors, `config_fingerprint` pinned at `08e471b10130e1e2`.
- Diagnosed why the browser-QA lane could not run: the scoped test-backend fixture seeding script crashes with `UnitMismatchError` (missing `value_unit`), so the store-scope guard correctly refused to touch the operator's real data.
- Drafted `runs/goal-session-hypothesis-foundry/state/blueprint.md` defining the Foundry's planned UI location (`/desk`) and its single planned read model (`GET /research/desk/micro/foundry`).
- Reviewer PASS with zero blocking issues (one NOTE on an unrelated, pre-existing, owner-authorized host-guard memory tightening).
- Verified 0 target journeys pass browser QA — the browser lane never ran this iteration (test-backend fixture bug; see What's left).

## What's left

- Journey J-01 (The Foundry opens as a new finite era and the old self-extension loop is inactive) partial — the `/desk` panel and era-open baseline record have no home yet.
- Journey J-02 (Ratified sources compile into auditable CandidateSpecs or typed blocks without outcome input) failing — entirely unbuilt.
- Journey J-03 (Generic interpretation preserves timing, population symmetry, direction, and exact Scout decisions) failing — entirely unbuilt.
- Journey J-04 (Foundry owns the denominator, append-only state, freeze barrier, and integrity lock) failing — entirely unbuilt.
- Journey J-05 (The complete factory passes hermetic known-null, planted-effect, leakage, and honest-stop oracles) failing — entirely unbuilt.
- Journey J-06 (One complete real epoch is generated and committed with zero Foundry outcome reads) failing — entirely unbuilt, correctly not attempted this early.
- Journey J-07 (Goal Mode deterministically exhausts the frozen real epoch without changing science) failing — entirely unbuilt, correctly not attempted this early.
- Journey J-08 (The operator sees the final Foundry truth and all foundation rails still hold) failing — no read model, no `/desk` panel (foundation half is healthy: suite/tsc/fingerprint all clean).
- Browser-QA rig is broken: `apps/backend/scripts/seed_micro_graduation_iter18_fixture.py`'s `_observation()` helper omits `value_unit`, so no journey can ever get a passing screenshot until it's fixed.

## Next step

Iteration 1 should do two things, in order. First, repair the test backend: the fixture seeding script (`apps/backend/scripts/seed_micro_graduation_iter18_fixture.py`) needs to declare the unit (`return_bps`) its measurements already use, without loosening the `walkforward.py` safety check that caught the gap — then confirm the scoped backend actually comes up healthy on port 8301, since no journey can be marked passing without a screenshot. Second, start the real work at step 2 of the goal's Binding Execution Order: write `docs/hypothesis-foundry-spec.md` and the CandidateSpec schema with the first source records (what J-02 needs), without touching real epoch generation, freezing, or any candidate result yet. Separately, the operator may want to raise the session's iteration cap from 60 to 80, per the goal document's own recommendation, to avoid a premature stop.

## Assumptions made

- iter-1 · goal-decomposer — Ambiguity: nothing in the Foundry Constitution's scientific-integrity rules forbids building the J-02 "Sources/Compiler fixture view" UI early, since it would render only synthetic fixture data with no real outcome. We chose: defer ALL Foundry subsection UI to the single consolidated read-surface iteration named later in the Binding Execution Order, building one comprehensive read surface once instead of extending a partial UI three separate times; iter-1 ships only J-01's panel header, which cannot wait. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: `docs/goal.md` Binding Execution Order step 2 ("Foundry methodology + source registry + CandidateSpec") doesn't say whether "first source records" means authoring the real required source objects or building the compile machinery proven on synthetic fixtures, and J-02's own acceptance steps name a fixture view over synthetic examples. We chose: iter-1 builds the compile-rule machinery (owner meta-policy, natural-boundary law, exact-quote lint, CandidateSpec schema/hash) proven on the 7 hermetic fixture source types, leaving the real 11-source registry content to a later journey (J-06). Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: the infra scoring rule says a journey named in the browser-infra token with no fresh screenshot scores `partial` + `pending_infra`, but forbids `failing` only on infra absence *alone*; here 7 of 8 journeys have deterministic, evaluator-reproduced proof their surfaces don't exist at all. We chose: score J-02..J-08 `failing` and J-01 `partial` on that independent evidence, and set `pending_infra` on none of them — a verify-only make-up ride over nonexistent surfaces would waste an iteration and mechanically trigger a stalled-class treatment for a one-line fixture bug; the infra failure is carried as the top active blocker instead. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-hypothesis-foundry-iter-0.md |
| Dev handoff | — | docs/handoffs/goal-hypothesis-foundry-iter-0-dev.md |
| Review | PASS | reports/reviews/goal-hypothesis-foundry-iter-0-review.md |
| Browser QA | SKIPPED | reports/phase-goal-hypothesis-foundry-iter-0-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-hypothesis-foundry/iter-0/eval.md |
| Journey history | — | runs/goal-session-hypothesis-foundry/state/journey-history.json |
