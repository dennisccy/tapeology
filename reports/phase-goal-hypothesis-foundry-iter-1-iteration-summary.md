# Iteration Summary — goal-hypothesis-foundry-iter-1

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-26
**Iteration:** 1

## In plain words

**What you can do now:** Nothing from this new research chapter yet — every journey in this era is still in progress, none of them finished. Everything built in earlier chapters (the Desk page, the Cockpit, and the Structure Map) keeps working exactly as it did before.

**What changed this time:** The Desk page now has a new "Hypothesis Foundry" section at the bottom, below all the existing sections. Opened up, it correctly tells you which research chapter is active (the previous chapter is closed, this one is open) — but the second part it's meant to show, the frozen starting numbers this whole chapter will be checked against, read "not recorded yet" when tested this round, so that part isn't confirmed working for a real user yet.

**What's next:** Make the test copy of the site actually show the real starting numbers so this screen can be fully verified, fix two small gaps in how source records are captured, and then start building the piece that turns each approved research idea into a testable specification without changing any existing trading decision.

## Headline

The dead browser lane is alive again.

## Direction

**Signal:** holding
**Why:** Nothing regressed and one journey (J-02, "Sources compile into auditable CandidateSpecs") moved from failing to partial on the strength of real, independently re-run backend machinery, but neither J-01 nor J-02 reached full "passing" status this round, so this counts as steady progress rather than a scored win. The evaluator's own recommendation to run the next iteration at full depth (it touches the frozen Scout decision rail) signals a normal, cautious next step rather than a stall or setback.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** The browser lane that was completely dead in iteration 0 works again, and I checked that it was fixed the honest way: the test fixture now declares its unit, and the safety check that caught the problem is untouched in both the committed diff and the working tree, with no test silenced anywhere. The first two screenshots of this session exist. The new Hypothesis Foundry panel on the Desk page correctly names the old era closed and this era active, so J-01 "The Foundry opens as a new finite era" gained real ground — but the same screenshot shows "The era-open baseline has not been recorded yet.", so its last step is still unproven and the journey stays partly done.

## What was done

- Product changes: apps/backend/scripts/seed_micro_graduation_iter18_fixture.py, apps/backend/app/research/foundry_source_registry.py, apps/backend/app/research/foundry_compiler.py, apps/backend/app/research/micro_routes.py, apps/backend/scripts/record_foundry_era_open_baseline.py, apps/backend/tests/test_foundry_source_registry.py, apps/backend/tests/test_foundry_compiler.py, apps/backend/tests/test_foundry_route.py, apps/backend/tests/test_foundry_fixture_unit_regression.py, apps/frontend/app/desk/page.tsx, apps/frontend/lib/api.ts, apps/frontend/lib/types.ts, docs/hypothesis-foundry-spec.md
- Fixed the QA-rig-crashing fixture bug (the seed script now declares `value_unit`) without weakening `require_canonical_observation_units`, and confirmed the scoped `:8301` QA rig starts healthy — restoring browser evidence for the whole session.
- Wrote `docs/hypothesis-foundry-spec.md`, the Foundry Methodology Spec (candidate-construction / freeze / exhaustion semantics only, references the existing statistical rail rather than forking it).
- Built `foundry_source_registry.py` (14-member disposition vocabulary, `SourceRecord` schema, owner meta-policy precedence, exact-quote lint) and `foundry_compiler.py` (`CandidateSpec` schema + order-invariant/content-sensitive hash, family grouping), proven hermetically against all 7 required fixture source archetypes (TC-3..TC-12, 40 new tests, 40/40 pass).
- Added `GET /research/desk/micro/foundry` (read-only, never computes) and appended the "Hypothesis Foundry" panel header to `/desk`, rendering era identity and the era-open baseline verbatim from that route.
- Recorded the real era-open baseline (3787 passed / 8 skipped / 0 failed, `tsc` 0 errors, config fingerprint unmoved, all six Referee-module hashes) into the operator's real data store.
- Full backend suite (3787 pass / 8 skip / 0 fail) and `tsc --noEmit` (0 errors) stayed green; reviewer independently re-ran the 40 new tests plus 143 regression-guard tests, all pass (PASS_WITH_NOTES).
- Browser QA ran both target journeys (J-01, J-02); 0/2 passed this iteration — J-01 was blocked by a QA-rig data-scoping gap (the real baseline exists but isn't visible to the scoped test backend), and J-02's UI view was deliberately deferred to a later iteration by design.

## What's left

- Journey J-03 (Generic interpretation preserves timing, population symmetry, direction, and exact Scout decisions) failing
- Journey J-04 (Foundry owns the denominator, append-only state, freeze barrier, and integrity lock) failing
- Journey J-05 (The complete factory passes hermetic known-null, planted-effect, leakage, and honest-stop oracles) failing
- Journey J-06 (One complete real epoch is generated and committed with zero Foundry outcome reads) failing
- Journey J-07 (Goal Mode deterministically exhausts the frozen real epoch without changing science) failing
- Journey J-08 (The operator sees the final Foundry truth and all foundation rails still hold) failing
- The recorded era-open baseline is real but invisible to the scoped QA rig (a store-scoping gap, not a data problem) — this is the one remaining blocker for J-01 to reach passing
- `SourceRecord` is missing two required fields (`source_hash`, `alternatives`) that the spec document claims are present verbatim — must be fixed before any real source is authored against this schema
- `BLOCKED_UNIT_CONTRACT` is not yet reachable from declared fields (collapses into `BLOCKED_SPEC_GAP`'s branch)
- `CandidateBlueprint` is still a hand-authored compiler input pending the generic interpreter (J-03)

## Next step

Make the test copy of the site show the real recorded opening numbers, so J-01 "The Foundry opens as a new finite era" can finally be photographed complete — point the test rig at the already-recorded snapshot (or copy that same real file into the rig before the browser pass); the rig must display the REAL recorded values, never invented ones. Add the two missing record fields (`alternatives` and a source hash) and make the spec document and the code agree, before any real source is written against this schema. Then start the next required stage: the general reader that turns a frozen candidate description into the existing Scout decision without changing it, plus the family/denominator and freeze machinery — J-03 "Generic interpretation preserves timing, population symmetry, direction, and exact Scout decisions" and J-04 "Foundry owns the denominator, append-only state, freeze barrier, and integrity lock". Run that next iteration at full depth, because it touches the frozen decision rail the whole project rests on and this iteration already found three places where the written spec and the code disagree.

## Assumptions made

- iter-1 · goal-evaluator — Ambiguity: Methodology A.7 ("capture defect ≠ product failure") could arguably cover J-01 step 5, since the era-open baseline artifact is genuine (all six Referee hashes recomputed and matched) and the screenshot shows the panel behaving correctly for an empty store rather than misbehaving. We chose: do NOT apply the capture-defect exception and keep J-01 partial — the asserted behavior has never been observed by anyone but the developer, and closing the gap needs a rig launch/provisioning change rather than a re-capture. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-02's five acceptance steps are all on-screen inspections of a Sources/Compiler view that was deliberately deferred, so literally zero of its steps have browser evidence, yet its backend compile rules exist and were independently re-run by the reviewer (40/40). The status vocabulary doesn't say how to score a journey whose substance is proven at a layer its own steps never name. We chose: score J-02 partial, not failing, on the reviewer's independent test re-run, while recording that no UI step has evidence and that J-02 additionally cannot pass until `SourceRecord` gains the `alternatives` field its step 3 requires. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: `docs/goal.md`'s Binding Execution Order step 2 ("Foundry methodology + source registry + CandidateSpec. No real manifest yet.") doesn't say whether "first source records" means authoring the real 11 required source objects or building the compile machinery proven on synthetic fixtures. We chose: build the compile-rule machinery and prove it on the 7 hermetic fixture source types J-02 itself names; authoring the real 11 required-source-object registry content is left to J-06. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: nothing in the Foundry Constitution's scientific-integrity rules forbids building the J-02 "Sources/Compiler fixture view" UI early, since it would render only synthetic fixture data. We chose: defer all Foundry subsection UI (Sources/Compiler included) to the single consolidated read-surface iteration named later in the Binding Execution Order, building one comprehensive read surface once instead of extending a partial UI three separate times; iter-1 ships only J-01's panel header, which is required by J-01's own acceptance and cannot wait. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: the status rule says a journey named in the browser-infra token with no fresh screenshot scores partial + pending-infra, but forbids "failing" from infra absence alone — yet 7 of the 8 journeys had deterministic, evaluator-reproduced proof that their surfaces don't exist at all. We chose: score J-02..J-08 failing and J-01 partial on that independent evidence, rather than doing a verify-only make-up ride over surfaces that don't exist, which would waste an iteration and mechanically trigger STALLED for a blocker that is really a one-line in-repo fixture fix. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-hypothesis-foundry-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-hypothesis-foundry-iter-1-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-hypothesis-foundry-iter-1-review.md |
| Browser QA | FAIL | reports/phase-goal-hypothesis-foundry-iter-1-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-hypothesis-foundry/iter-1/eval.md |
| Journey history | — | runs/goal-session-hypothesis-foundry/state/journey-history.json |
