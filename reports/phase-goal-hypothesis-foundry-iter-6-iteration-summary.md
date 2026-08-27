# Iteration Summary — goal-hypothesis-foundry-iter-6

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-27
**Iteration:** 6

## In plain words

**What you can do now:** On the Desk page's Hypothesis Foundry section you can see the whole research chapter's story so far: the new chapter has formally opened and the old auto-growing research loop is switched off; approved research ideas have been turned into fair, auditable test plans; that translation is proven to preserve the original timing, direction, and decisions exactly; the master record that tracks counts, keeps a permanent log, and locks in results; the testing factory passing its own honesty checks; the one real, permanently recorded research result for this era (which honestly found zero surviving ideas); and, new this round, proof that the one real evaluation run over that result has actually happened and touched none of the protected research data.

**What changed this time:** The Desk page's Hypothesis Foundry panel gained a new "Runner / Checkpoint" section, right below "Epoch / Manifest". It shows the exact time the one real evaluation run was recorded, a fingerprint of exactly which research data was in scope, a "Checkpoint: 0 of 0" count (honest — this era's plan had no ideas left to test), a "Protected/withheld/sealed reads: 0" line proving nothing off-limits was touched, and a plain-language sentence confirming the run finished cleanly.

**What's next:** Next, fix a bookkeeping mismatch where the same summary number is worked out two different ways in two different places, then build the final summary screen that shows the whole research chapter's honest conclusion.

## Headline

The Foundry's real, one-time evaluation run happened and finished honestly empty — but a bookkeeping mismatch blocks calling the era done.

## Direction

**Signal:** improving
**Why:** J-07 "Goal Mode exhausts the frozen real epoch" moved from failing to passing this iteration — the era's second and final irreversible act (the first-read lock) is now written and was independently re-verified against the real 26GB data store. But a structural coherence check failed (`frozen_ready_total` is computed two different ways, in `micro_routes.py` and the now-sealed `run_hypothesis_foundry_real_exhaust.py`), plus two new MINOR anti-goal findings (a page-load GET now writes a lock file; the discarded-epoch ratification from iter-5 is still unresolved), so GOAL_ACHIEVED stays blocked until those are settled or the owner rules. Only J-08 remains unbuilt.

**Trend (last 5 iters):**
- Newly passing this iter: J-07
- Newly passing in last 5 iters total (iter-2 through iter-6): J-01, J-02, J-03, J-04, J-05, J-06, J-07
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 4 new MINOR total (iter-4: 1, resolved in iter-5; iter-5: 1, still unresolved/blocking; iter-6: 2, both still unresolved/blocking)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The one-way step the goal calls the era's second irreversible act really happened, and I checked it myself instead of trusting the reports. The Foundry's record book now holds exactly one opening row, written after the code it points at was committed, and I re-computed the big data fingerprint inside it from the real 26 GB store on this machine — it matches to the character. So J-07 "Goal Mode exhausts the frozen epoch" is done. But the structural check on this iteration failed: the same number is now worked out in two different places, from two different fields of the same file, and the file that holds the second copy is one the era has already sealed — so the obvious repair is not allowed by the era's own rules.

## What was done

- Product changes: apps/backend/app/research/foundry_ledger.py, apps/backend/app/research/foundry_freeze.py, apps/backend/app/research/foundry_runner.py, apps/backend/app/research/micro_routes.py, apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py, apps/backend/scripts/run_hypothesis_foundry_real_exhaust.py, apps/backend/tests/test_foundry_freeze.py, apps/backend/tests/test_foundry_ledger.py, apps/backend/tests/test_foundry_real_epoch_artifacts.py, apps/backend/tests/test_foundry_route.py, apps/backend/tests/test_run_hypothesis_foundry_real_exhaust.py, apps/frontend/lib/types.ts, apps/frontend/app/desk/page.tsx, docs/hypothesis-foundry/freeze-set.json, docs/hypothesis-foundry/freeze-record.json, apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh
- Built and ran a new operator command that performs the Foundry's real, one-time evaluation pass against the already-frozen research plan; it completed honestly with zero candidates to evaluate.
- Added a new "Runner / Checkpoint" panel on `/desk` → Hypothesis Foundry confirming the run happened, when, and that it touched zero pieces of protected research data.
- Repaired three freeze-record bookkeeping gaps: the record is now portable across machines, correctly points at the exact code version that produced it, and states which evidence category the research is locked to.
- Provisioned the scoped QA test rig with a real copy of the one-time run's log (same pattern already used for the era-opening record), so the new panel is screenshot-able against real state, never a fabricated one.
- Verified 7 journeys (J-01 through J-07) pass browser QA (13/13 test rows, 0 skipped: 7 LLM checks plus 6 deterministic golden replays).

## What's left

- J-08 "The operator sees the final Foundry truth" is still failing — not targeted this iteration (explicitly out of scope), carried since iter-3.
- Coherence failure blocks any "goal achieved" call: `frozen_ready_total` is computed independently in two places (`micro_routes.py` vs. the now-sealed `run_hypothesis_foundry_real_exhaust.py`); the textbook fix would require editing a sealed, freeze-locked file.
- Anti-goal "No second real generation epoch" (iter-5) is still unresolved and blocking — the bypass mechanism is now closed, but only the owner can ratify or reject the discarded first epoch.
- Anti-goal "Persistence stays scoped" is a new unresolved, blocking finding — every page-load GET on the Foundry panel now writes a small lock file; the fix site is inside a sealed file, so this is an owner-disposition decision.
- No per-candidate detail or survivor-labelling view exists yet — this era's real plan has zero candidates, so there is nothing to drill into regardless, but J-08 is expected to add that surface for future eras.
- The new freeze-record field ("era-open evidence-class contract") exists only in backend bookkeeping and is not rendered anywhere in the UI.

## Next step

Two things must happen next, in order. First, settle the coherence failure blocking any goal-achieved call: the same `frozen_ready_total` count is computed in two places from two different fields of the same file, and the copy inside `run_hypothesis_foundry_real_exhaust.py` cannot legally be edited because that file is now sealed by the freeze lock — the next iteration should put the one true owner in the non-sealed `micro_routes.py` plus a test proving the sealed script's own line still matches, and if that isn't judged sufficient, stop and ask the owner rather than breaking the seal. Second, build J-08 "The operator sees the final Foundry truth" (the final on-screen summary, the withheld-datasets count, the honest "no survivors" statement, and the protective-check battery) — none of which touches a sealed file. Three decisions remain the owner's alone and the era cannot close without them: ratify or reject the first, discarded real epoch; accept the duplicated count as a known harmless flaw or sanction breaking the seal; and accept that a page visit writes a small lock file. Run the next iteration at full depth — a plain continue has already been downgraded to the lighter pipeline twice this session, and this is the era's closing act.

## Assumptions made

- iter-6 · goal-evaluator — Ambiguity: J-07's eight steps are mostly vacuous for a zero-candidate epoch (steps 3-6 have nothing to iterate) and step 7 permits a fixture-backed interrupt; the status vocabulary doesn't say whether a vacuously-satisfied step counts as demonstrated. We chose: score J-07 passing, extending the same precedent already set for J-06 — goal.md's own Completion section blesses "zero compiled candidates" as a valid ending; the one un-rendered field (withheld_excluded=80) is recorded as a gap for J-08 instead of capping the journey at partial. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: the ESCALATE rung literally matches (J-08 has failed six straight evaluations) and the depth arbiter has already twice demoted a CONTINUE to lean this session, but the evaluator's own agent contract says a COHERENCE-FAIL iteration must return CONTINUE. We chose: CONTINUE per the explicit contract, instead flagging the demotion risk loudly so a human can force full depth; noted J-08 was never actually targeted in those six iterations, so the rung's literal match doesn't carry its intended meaning. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: the "Persistence stays scoped" rail says every page-load GET is read-only, but the new single-flight probe makes the Foundry GET create/truncate a lock file; the rail's operative intent (no data recorded, no candidate computed) stays intact but the literal "read-only" wording is contradicted. We chose: record it as a MINOR, unresolved, blocking anti-goal entry on the literal reading rather than describe it only in prose. Does not change this iteration's verdict. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: iter-5's "No second real generation epoch" finding recorded its own close condition as satisfied once a uniqueness guard lands; a guard (`ManifestStoreMissingError`) landed and passed this iteration, which could be read as discharging the finding. We chose: keep it unresolved/blocking (fail-closed) — a guard prevents recurrence but does not un-mint the already-discarded epoch_id, and only the owner may ratify that. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: the iteration-state digest tags the three open freeze-integrity findings (B1/B2/B7) as needing owner sign-off, but goal.md §7.3 authorizes Goal Mode itself to repair freeze-hash drift before any real outcome is read — and this era's frozen epoch has zero candidates, so no outcome will ever be read. We chose: read the OWNER tag narrowly (it covers only the separate, disclosed MINOR anti-goal about the discarded first epoch) and let this iteration repair B1/B2/B7 itself via the already-proven freeze-set/freeze-record generation functions, without touching epoch_id/registry/manifest content. Reversible: no (the first-read lock and any freeze-set/freeze-record regeneration preceding it are one-way once committed)
- iter-5 · goal-decomposer — Ambiguity: J-06's real `epoch_manifest` values must be visible to the scoped QA rig, but the goal text doesn't say whether the new key should read through the existing runtime-scoped resolver or read the Git-tracked paths directly. We chose: read the literal Git-tracked `docs/hypothesis-foundry/` paths directly, never through the runtime resolver — reading through it would reproduce iter-0/iter-1's exact QA-invisibility failure. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: J-06 step 4's "freeze-set path manifest must be visible" could mean the UI must itemize every path+hash pair, or that visibility in the tracked committed file itself is enough. We chose: the UI shows the freeze_set_hash plus a reference to the committed file, not an itemized dump — forcing a full on-screen listing would add UI complexity the goal doesn't actually ask for. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: the fixture view deliberately surfaces only one sibling of a two-variant alias family (asserted at exactly 7 entries), but two consecutive evaluator verdicts asked to show both records of that family. We chose: treat this as a legitimate fixture-completeness correction, not a forbidden guard-weakening — the assertion's count changes but its meaning (every documented archetype has its own inspectable record) is preserved. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: the ESCALATE rung is worded for a lean iteration but iter-5 ran full; yet a CONTINUE here would be demoted to lean by the depth arbiter right as iter-6 was about to write the era's second irreversible act with three open freeze-integrity findings. We chose: ESCALATE, extending the rung to a full iteration that surfaced genuine cross-cutting integrity complexity, since this exact override had already happened twice (iter-2, iter-4). Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: the "No second real generation epoch" anti-goal is worded absolutely, but goal.md permits Goal Mode to repair "only before any real outcome has been read" — which is exactly what happened (a first epoch_id was minted, an audit proved one value unsupported, and the registry was regenerated before any commit or outcome read). Whether this counts as critical (forcing REGRESSION) or minor was a real fork. We chose: MINOR and unresolved/blocking, not critical — verified directly that the five tracked artifacts were added in exactly one commit, no trial ledger or candidate outcome ever existed, and the sequence is disclosed in the committed audit report. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: the real epoch compiled zero candidates, so J-06 step 4's family/variant/manifest rendering block has never displayed a row — the status vocabulary doesn't say whether a vacuously-empty step counts as demonstrated. We chose: score J-06 passing — goal.md's own Completion section lists "zero compiled candidates" as a valid successful ending, and the screen renders an explicit empty-state message rather than a blank. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: goal.md enumerates the required source objects as nine + three bullets, but the committed registry reaches 11 by collapsing constituent records and splitting one card in two, so four specific card ids the iteration spec named don't exist as their own source_ids. We chose: accept the partition and score J-06 step 2 as met — every collapsed constituent id is carried in alias_refs, an independent auditor confirmed the reading, and the alternative would require regenerating the already-frozen epoch, which the goal forbids. Reversible: no (the epoch is frozen; changing the partition would need a second epoch)

## Quick verify

From `reports/phase-goal-hypothesis-foundry-iter-6-what-to-click.md`:

1. Open http://localhost:3301/desk in your browser
2. Scroll to the bottom of the page and click the "Hypothesis Foundry" section header
3. Click the "Epoch / Manifest" subsection header (near the bottom of the expanded panel)
4. Click the "Runner / Checkpoint" subsection header (directly below "Epoch / Manifest")
5. Read the "First-read lock recorded at:" line inside the "Runner / Checkpoint" subsection

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-hypothesis-foundry-iter-6.md |
| Dev handoff | — | docs/handoffs/goal-hypothesis-foundry-iter-6-dev.md |
| Review | PASS | reports/reviews/goal-hypothesis-foundry-iter-6-review.md |
| Browser QA | PASS | reports/phase-goal-hypothesis-foundry-iter-6-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-hypothesis-foundry-iter-6-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-hypothesis-foundry-iter-6-user-visible-changes.md |
| What to click | — | reports/phase-goal-hypothesis-foundry-iter-6-what-to-click.md |
| UI surface map | — | reports/phase-goal-hypothesis-foundry-iter-6-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-hypothesis-foundry-iter-6-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-hypothesis-foundry-iter-6-ux-regression.md |
| QA | PASS | reports/qa/goal-hypothesis-foundry-iter-6-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-hypothesis-foundry-iter-6-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-hypothesis-foundry-iter-6-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-hypothesis-foundry/iter-6/eval.md |
| Journey history | — | runs/goal-session-hypothesis-foundry/state/journey-history.json |
