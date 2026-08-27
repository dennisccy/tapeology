# Iteration Summary — goal-hypothesis-foundry-iter-5

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-08-27
**Iteration:** 5

## In plain words

**What you can do now:** Open the Desk page and see this new research chapter has begun, with the old chapter safely closed off. See the chapter's starting numbers on record. See four practice demonstrations proving the idea-testing machinery works correctly on made-up examples — turning an idea into a fair test, reading it the same way the older trusted method would, keeping a locked idea count, and passing a full test run covering every possible outcome. And now, for the first time, see the one real result: all 11 real research ideas on file, and exactly what happened to each one.

**What changed this time:** The Desk page's Hypothesis Foundry section gained a new "Epoch / Manifest" panel showing the chapter's one real, permanently-recorded decision — all 11 real research ideas and their outcomes, plus a link to an independent double-check report — marked with a distinct green banner so it can never be confused with the practice panels next to it. Two of those practice panels also got fixed to show details (extra context fields, and both halves of a two-part example) that were being calculated all along but never actually shown.

**What's next:** Next we'll build the step that would run any surviving ideas through a real test — though since none of the 11 ideas survived this round, that step mostly proves the safety machinery works correctly even on an empty list. Two decisions need the project owner's sign-off first: whether an early draft of this real result (created and corrected before anything was locked in) is acceptable, and whether a couple of the safety-record's details may still be fixed before the next step locks everything in place for good.

## Headline

Generated and Git-committed the era's one real Foundry epoch (zero candidates, honestly)

## Direction

**Signal:** improving
**Why:** Iter-5 turned three journeys from partial/failing to passing — J-02 "Sources compile into auditable CandidateSpecs", J-05 "The complete factory passes hermetic oracles", and J-06 "One complete real epoch is generated and committed" — with the era's one real, Git-committed Foundry epoch (zero compiled candidates, an outcome the goal itself blesses as valid) now live on `/desk`. J-01/J-03/J-04 all replayed clean with zero regressions. One MINOR anti-goal violation (a discarded first `epoch_id`, disclosed and low-risk) stays open and blocking, and the hard audit surfaced three IMPORTANT integrity gaps (freeze-set path portability, `freeze_commit` not yet containing the frozen bytes, owner ratification of the discarded epoch) that must close before J-07 writes the era's second irreversible lock.

**Trend (last 5 iters):**
- Newly passing this iter: J-02, J-05, J-06
- Newly passing in last 5 iters total: J-01 (iter-2), J-03 (iter-4), J-04 (iter-4), J-02 (iter-5), J-05 (iter-5), J-06 (iter-5) — all six built journeys are now passing
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 2 MINOR (iter-4's `scout._two_sided_p` reassignment, resolved in iter-5; iter-5's discarded first `epoch_id`, unresolved/blocking)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The Foundry now has its one real, frozen epoch, and I checked the artifacts myself rather than trusting the reports. Three journeys turned green: J-06 "One complete real epoch is generated and committed", J-02 "Sources compile into auditable CandidateSpecs", and J-05 "The complete factory passes hermetic oracles". The real epoch honestly produced zero candidates — all eleven ratified ideas were blocked, excluded, or renamed under the owner's own "block unresolved science" rule — which the goal itself lists as a valid successful ending, not a failure. I am escalating because the next stage writes the one-way lock that ends this era's freedom to change any science file, and three real integrity problems with that lock are still open.

## What was done

- Product changes: apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py, apps/backend/app/research/micro_routes.py, apps/backend/app/research/foundry_hermetic_summary.py, apps/backend/app/research/foundry_compiler.py, apps/frontend/lib/types.ts, apps/frontend/app/desk/page.tsx, docs/hypothesis-foundry/{source-registry,epoch-manifest,freeze-set,freeze-record}.json, reports/hypothesis-foundry/source-registry-audit.md, /research/desk/micro/foundry (epoch_manifest key)
- Generated and Git-committed the era's one real Foundry epoch: 11 ratified source ideas evaluated, all disposed as blocked/excluded/aliased (zero compiled candidates) — an honest, goal-sanctioned outcome.
- A fresh-context independent audit reviewed the registry before commit, caught and fixed two defects (a missing `audit_note` field, one unsupported direction call), and its full report was committed alongside the epoch.
- Added the new "Epoch / Manifest" screen on `/desk` → Hypothesis Foundry, visually distinct (emerald banner) from the four practice/fixture panels, showing all 11 source dispositions, freeze identities, and a link to the audit report.
- Fixed two display gaps: Sources/Compiler now shows formula refs/superseded fields/lineage ids and both alias-family sibling records (7→8 rows); Hermetic Oracles now shows a per-row kill-type mapping and best-of-N disclosure line.
- Removed the last open anti-goal issue: production code no longer temporarily reassigns the frozen Scout scoring function; a re-tuned fixture reaches the same test outcome under the real, unmodified function.
- Verified 3 target journeys (J-02, J-05, J-06) pass browser QA; replayed and confirmed J-01/J-03/J-04 still pass (12/12 browser QA checks, PASS).

## What's left

- Journey J-07 "Goal Mode deterministically exhausts the frozen real epoch without changing science" failing — not yet built; now unblocked since the epoch is committed.
- Journey J-08 "The operator sees the final Foundry truth and all foundation rails still hold" failing — depends on J-07.
- Unresolved blocking anti-goal finding: a first real epoch was minted and discarded before commit (no outcome ever read, fully disclosed) — needs owner ratification before J-07 runs.
- Audit findings B1/B2 still open: the freeze-set file pins absolute machine-local paths (the integrity lock is only verifiable on this one checkout), and `freeze_commit` does not yet contain the frozen science-file bytes (still uncommitted at generation time) — both need owner approval to fix before the one-way lock in J-07.
- No compiled candidates exist yet for the real epoch — the Epoch/Manifest screen's family list is honestly empty (expected, not a bug).
- The real exhaust pass (running candidates against real market data) has no UI or backend entrypoint yet.
- `best_of_n_disclosure.threshold_bps` is not identical across all seven Hermetic Oracles rows as originally assumed (documented, non-blocking).
- Optional read-only MCP proxy tool for Foundry data not built (deferrable per the goal).

## Next step

Build J-07 "Goal Mode exhausts the frozen real epoch" next, at full depth. Because the frozen epoch contains zero candidates, there is no result to read at all — the real work is the restartable single-flight runner, the epoch-opening record, the proof that an empty ready-list still reaches a valid finished state, and the count of protected, Vault, and Referee actions that must all be zero. Carry four repairs in the same iteration, because after the lock is written no science file may change again: store the frozen file list with paths relative to the project root instead of full machine-specific folders; commit this iteration's code changes and re-point the freeze record at that commit; add the four files and the one record field the rules require by name; and make the generation command refuse when its saved state file has simply been deleted. Two decisions belong to the operator and should be made before the lock is written: ratify (or reject) the discarded first epoch, and approve amending the already-committed frozen files for the repairs above.

## Assumptions made

- iter-5 · goal-evaluator — Ambiguity: the ESCALATE rung is worded for a lean iteration, but iter-5 ran full; a CONTINUE verdict here would be demoted to lean by the engine's depth arbiter right as the next iteration writes the era's second irreversible act with three open IMPORTANT freeze-integrity findings. We chose: ESCALATE, extending the rung to a full iteration that surfaced cross-cutting integrity complexity, rather than CONTINUE plus a depth recommendation the arbiter would override (this session has documented the same override twice already). Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: the "no second real generation epoch" rule is worded absolutely, but the goal's own rules allow repair "only before any real outcome has been read" — which is exactly what happened when a first epoch_id was minted, an audit proved one field unsupported, and the registry was regenerated before any commit or outcome read; critical vs. minor is a real fork (critical would halt the session). We chose: MINOR and unresolved (therefore blocking), verified directly (one commit only, no trial ledger ever existed, fully disclosed in the committed audit report) — it stays blocking until the owner rules. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: one required proof step asks to confirm the family/variant manifest is visible, but the real epoch compiled zero candidates so that display block has never shown a row — the rules don't say whether a vacuously-empty step counts as demonstrated. We chose: score the journey passing, since the goal's own completion rules list zero compiled candidates as a valid successful ending and the screen renders an explicit honest-empty message rather than a blank; scoring it lower would penalise the honest outcome the goal explicitly blesses. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: the goal enumerates the required source objects as nine plus three bullets, but the committed registry reaches 11 by collapsing each parked study with its pilot proxy and all four Wave-2 cards into one record each, then splitting one card in two — so four of the expected individual ids don't exist separately even though the test plan expects each to have its own disposition. We chose: accept the partition and score the "every required source appears once" check as met, recording it as a gap — every collapsed id is preserved in the alias list, an independent auditor confirmed the reading, and the alternative would require regenerating the frozen epoch, which the rules forbid. Reversible: no (the epoch is frozen; changing the partition would need a second epoch)
- iter-5 · goal-decomposer — Ambiguity: the real epoch's values must be visible to the scoped test environment, but the rules don't say whether the code should read the real committed files directly or through the same resolver used for the runtime-scoped era-open baseline (which is invisible to that test environment — a lesson already learned twice). We chose: read the literal Git-tracked files directly, never through the runtime-scoped resolver — confirmed by that resolver's own documentation, which scopes it to runtime storage only, distinct from the tracked real-epoch artifacts. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: a required step asks that the "freeze-set path manifest" be visible from the tracked files, which could mean the screen must list every one of potentially hundreds of protected file paths, or that being visible in the committed file itself is enough. We chose: the screen shows the freeze-set's fingerprint plus a reference to the committed file, not an itemized path list — forcing a full on-screen dump would add complexity the goal doesn't actually ask for. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: an existing design choice deliberately shows only one of two sibling records in a two-variant example to keep a fixed count, but two separate rounds of feedback now ask to show both records, which changes that fixed count. We chose: treat this as a legitimate completeness correction, not a forbidden weakening — the count changes but the underlying guarantee (every documented example has its own visible record) is preserved and, if anything, strengthened. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: the status rules don't say how to treat a journey where every numbered step is demonstrated but a small sub-detail inside one step is not, versus a journey where a whole step has no on-screen home at all. We chose: one uniform rule — a journey counts as fully working when every numbered step is shown on screen, with any missing sub-detail noted as a gap rather than capping the journey; a journey stays partly done only when a whole step is missing entirely. The alternative would have made this era permanently unclosable. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: two of a journey's proof points only show themselves inside a collapsed, click-to-open panel rather than directly on the visible screen, and the rules don't say whether a collapsed-but-present panel counts as "shown." We chose: count them, after independently re-running the underlying calculation and getting the exact same numbers reported — a collapsed panel a person can open is a real, present feature, not an absent one. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: production code briefly borrowing and restoring a frozen scientific setting sits between two readings of the "frozen foundations stay frozen" rule — nothing persisted and no result changed, but it is still a live reassignment inside the running system, not the safer test-only pattern used elsewhere. We chose: record it as a real, unresolved issue rather than describing it only in prose, scored as a small (not severe) problem since nothing persisted and no real data was involved — it still had to be fixed before the chapter could close. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: one required proof step bundles two separate checks — one buildable now with practice data, and one that needs a real, committed report that won't exist until a later stage. We chose: deliver only the buildable half this round and openly state that the journey may still be scored as partly done afterward, pending the later stage — a known, disclosed limit rather than a defect. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: a required proof step names the exact real, permanent file path for a piece of evidence, but that evidence is scoped to a practice/test view this round, since no real version of it exists yet. We chose: build the practice view using the same proven, already-tested machinery, clearly labelled as practice-only, showing the real target path only as a preview of where the real evidence will eventually live — never writing or faking the real file. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: one journey's required checks are worded as things to run and confirm rather than as on-screen inspections, unlike its sibling journeys — so the usual reason for holding a journey at "partly done" (no visible screen yet) doesn't literally apply to it. We chose: still score it partly done rather than fully done, because no screenshot exists for it and a private test run is never accepted as proof a person can see, and because the project's own design plan places its evidence on a visible screen that doesn't exist yet. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: a reviewer fixed two real problems found during review rather than sending the work back to be redone — meaning some of what was being checked was partly the reviewer's own work, which normally should not self-certify. We chose: count the fixes only after independently re-opening and re-checking them rather than trusting the reviewer's own report — treating an in-review fix as automatically unusable would have forced an unnecessary extra round for work that was actually present and verifiable. Reversible: yes

## Quick verify

From `reports/phase-goal-hypothesis-foundry-iter-5-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser
2. Scroll down and click the "Hypothesis Foundry" section header
3. Click the "Sources / Compiler" row header (first of five rows under Hypothesis Foundry)
4. Click the "Hermetic Oracles" row header (fourth row)
5. Click the "Epoch / Manifest" row header (fifth and last row, directly below Hermetic Oracles)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-hypothesis-foundry-iter-5.md |
| Dev handoff | — | docs/handoffs/goal-hypothesis-foundry-iter-5-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-hypothesis-foundry-iter-5-review.md |
| Browser QA | PASS | reports/phase-goal-hypothesis-foundry-iter-5-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-hypothesis-foundry-iter-5-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-hypothesis-foundry-iter-5-user-visible-changes.md |
| What to click | — | reports/phase-goal-hypothesis-foundry-iter-5-what-to-click.md |
| UI surface map | — | reports/phase-goal-hypothesis-foundry-iter-5-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-hypothesis-foundry-iter-5-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-hypothesis-foundry-iter-5-ux-regression.md |
| QA | PASS | reports/qa/goal-hypothesis-foundry-iter-5-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-hypothesis-foundry-iter-5-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-hypothesis-foundry-iter-5-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-hypothesis-foundry/iter-5/eval.md |
| Journey history | — | runs/goal-session-hypothesis-foundry/state/journey-history.json |
