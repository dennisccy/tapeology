# Iteration Summary — goal-clean_slate-iter-5

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-24
**Iteration:** 5

## In plain words

**What you can do now:** Watch a simulated, live, or historical trading tape settle into a market read on the Cockpit page, with a price chart showing candles, adjustable timeframes, and live-moving bars. On the Structure page, load any stock and date to see its strongest price walls, browse the "Case Studies" list of every past touch of those walls and what happened afterward (visible again as of this iteration, with filters by symbol and outcome), and check a strategy-comparison report or an honest "not yet run" message. The app is exactly two pages — Cockpit and Structure — the old Journal, Studies, and Performance pages are fully gone.

**What changed this time:** The "Case Studies" list on the Structure page — which had quietly gone missing a few days before this clean-up project started — is back on screen, along with the short sentence that explains it. The team then re-checked the entire app end-to-end and confirmed nothing else broke, but found one small piece of leftover, unused code that still needs to be tidied up before this clean-up project can be called fully finished.

**What's next:** Next, a short, focused clean-up pass will remove that last bit of leftover code and double-check nothing else was missed, so this clean-up project can be declared complete.

## Headline

Case Studies restored on /structure; full sentinel confirms J-01–J-04 hold, but orphaned classes block closure

## Direction

**Signal:** holding
**Why:** This iteration re-verified J-01–J-04 all still pass and restored the Case Studies panel plus its framing sentence, but J-05 stayed `partial` because the hard audit found five orphaned Pydantic request-body classes left over from iter-1's route deletion — a minor, unresolved anti-goal violation that blocks GOAL_ACHIEVED even though nothing is broken. No journey flipped to passing this iteration and none are failing, so the project is holding just short of the goal; the evaluator recommends one small cleanup iteration to close J-05.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-01, J-02, J-03, J-04
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 1 (minor, unresolved — 5 orphaned Pydantic classes in `routes.py`, flagged this iter)
- Iters with no journey state change: 1 of last 5

**Latest evaluator reasoning:** The era-closing sentinel is 99% there: J-05's kept-product browser walk is genuinely and thoroughly evidenced, the full suite is green under the new pin `08e471b10130e1e2` across three independent lanes, the guard/chart-guard suites pass byte-unmodified, coherence PASSES and the secret/dep scan is CLEAN. But the hard audit found — and the evaluator independently `git grep`-verified — five orphaned Pydantic request-body classes still living in `routes.py` from iter-1's route demolition (`ThesisRequest`, `ResolveRequest`, `ActionRequest`, `StudyRequest`, `ReviewRequest`). The classes are functionally inert, so this is a MINOR violation, not REGRESSION-class — but an unresolved anti-goal violation still blocks GOAL_ACHIEVED. One small dedicated cleanup iteration closes it.

## What was done

- Restored Case Studies panel visibility on `/structure` (`SHOW_CASE_STUDIES` flag flipped false→true; gate structure untouched)
- Reinstated the framing-paragraph sentence silently dropped three days before this clean-up project began
- Ran a full regression sentinel: fresh backend suite green (1167 passed / 7 skipped / 0 failed) under fingerprint `08e471b10130e1e2`
- Re-verified 9 guard/chart-guard suites (47 tests) pass byte-unmodified
- Re-confirmed the surface inventory: 11 deleted modules gone, MCP lists exactly 15 tools, nav shows exactly 2 routes, all 14 deleted routes 404
- Produced the final I-9 kept-route byte-comparison recapture — 0 new diffs vs iter-4
- Assembled a session-wide diff-vs-inventory cross-check covering the whole interlude (91 files: 1 added, 51 deleted, 39 modified)
- Cleared review (PASS), QA (PASS, 17/17), and verified 20 target journey(s) pass browser QA (20/20, 0 skipped); the hard audit (PASS_WITH_GAPS) then caught 5 orphaned classes the cross-check itself had missed

## What's left

- Journey J-05 (The kept product stands — regression sentinel) partial: diff-vs-inventory "zero residue" clause unmet — 5 orphaned Pydantic request-body classes (`ThesisRequest`, `ResolveRequest`, `ActionRequest`, `StudyRequest`, `ReviewRequest`) survive in `apps/backend/app/research/routes.py` from iter-1's route deletion
- Unresolved anti-goal violation (minor): "Deletion is complete, never cosmetic" is breached by those same 5 orphaned classes — this is what currently blocks GOAL_ACHIEVED
- Broader orphaned-symbol sweep not yet run: grep for any other orphaned request/response models or helper symbols beyond the 5 found, plus a source-introspection guard so every `BaseModel` in `routes.py` is referenced by a live route
- UX gap (non-blocking, logged): the Case Studies row-click drill-in has no scroll-into-view affordance on the unfiltered ~1,758-row table, so a first click can look like nothing happened
- README still describes Case Studies as "withheld... pending an operator decision" — now stale since the flag was restored this iteration; needs a copy fix

## Next step

One dedicated demolition-cleanup iteration at full depth that re-verifies J-05 (not new feature work): delete the 5 orphaned classes (`ThesisRequest`, `ResolveRequest`, `ActionRequest`, `StudyRequest`, `ReviewRequest`) from `apps/backend/app/research/routes.py`; run the audit's carried-forward expanded sweep for any other orphaned request/response models and helper symbols of the deleted routes (and orphaned frontend types); re-run the full backend suite (expect still green — the classes are inert) and regenerate the diff-vs-inventory cross-check with the added orphaned-model grep; optionally add a source-introspection guard asserting every `BaseModel` in `routes.py` is referenced by at least one live route. Then J-05's completeness clause closes grep-provably and every Must-have journey is passing with no unresolved anti-goal — at which point GOAL_ACHIEVED becomes evaluable (subject to the deterministic gates + two-key confirm). Full depth is warranted because this is the era-closer and the audit lane should independently re-certify the now-complete demolition. Also fold in the README staleness fix (coherence advisory).

## Assumptions made

- iter-5 · goal-evaluator — Ambiguity: the hard audit rated the 5 orphaned request-body classes IMPORTANT-not-CRITICAL and recommended accepting this iteration (they are functionally inert), but goal.md tags the breached rail as critical while the evaluator's REGRESSION-trigger rubric reserves "critical" for secrets/paid-dep/license/backdoor/fabricated-data — does inert-but-grep-provable dead code block GOAL_ACHIEVED, and is it REGRESSION or CONTINUE?. We chose: treat it as a genuine unresolved anti-goal violation that blocks GOAL_ACHIEVED but classify it MINOR for the regression trigger → CONTINUE, not REGRESSION, with a dedicated cleanup as the next step; J-05 scored `partial`, not `passing`. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: goal.md repeatedly asserts Case Studies is a currently-live KEPT surface whose drill-in must be browser-verified this iteration, but the shipped code has `SHOW_CASE_STUDIES = false` (set by an unrelated commit three days before this goal.md was authored) — carried forward unresolved since iter-0. We chose: restore — flip the flag to `true` and reinstate the one dropped framing sentence — as this iteration's one code change, since the suppression's own code comment calls it reversible and goal.md is the most recent, most specific statement of intent naming Case Studies as kept in four places. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: goal.md's J-04 step naming no Config value to change meant literally following the instruction would silently no-op (idempotent primary-key refusal) instead of producing the required new-epoch PnL row. We chose: scope the fix narrowly to bump `Config.pnl_founding_enhancement_id`/`_title`'s literal default values (existing fields, not new ones) in the same commit as the field deletions, before computing the one new pin. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: goal.md's I-4 "Confirmed DELETE list" of 18 Config fields proved both over- and under-inclusive against a live-reader grep (4 listed fields are still read live; 9 unlisted fields also qualify for deletion). We chose: corrected the delete list to 23 fields, explicitly excluding the 4 wrongly-listed fields (plus `analytics_min_sample_size`) from deletion, with the full grep trail documented in the iteration spec. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: goal.md's I-6 lists the resulting 15-tool MCP contract in a specific prose order, but the code's natural residual order after deleting the 3 dead rows in place sequences the last 3 tools differently. We chose: read "this exact list" as specifying tool membership, not order, and kept the code's natural residual order rather than reordering for zero functional benefit. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-01's required-still-passing check expected one sanctioned kept-route diff, but the re-capture showed three — two unexplained (`research.backtests.list`, `research.pnl_ledger`) beyond the sanctioned taxonomy shrink. We chose: score J-01 `passing`, accepting the dev's root-cause that the 2 extra diffs are a launch-cwd data artifact (a different journal.db read, not different code), independently confirming the entire read/serialize code path is 0-diff. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: goal.md's I-9 byte-comparison protocol, read literally in isolation, could mean the taxonomy route is the only route payload ever allowed to differ across all three journeys — contradicting J-02's own acceptance clause requiring `GET /meta/ui-routes` to change. We chose: read the I-9 protocol as a per-journey cumulative sanctioned-diff list rather than a single fixed exception, codified as TC-14 in the iteration spec. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance lists "the full remaining backend suite is green," but the suite was 1165 passed / 1 failed / 7 skipped — the one failure being the MCP `journal` tool test that J-03's later scope owns. We chose: read "full suite green" as "green modulo the J-03-owned MCP-contract test the ordering leaves transiently red" and scored J-01 `passing`, not `partial`. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-05's literal acceptance ties full closure to the post-J-04 end state, and the spec delegates to the evaluator whether to record J-05 as passing-on-today's-evidence or partial-pending-later-journeys; separately, the expected "Case Study drill-in" clause was unreachable since `SHOW_CASE_STUDIES = false`. We chose: `partial`, not `passing` — full acceptance isn't yet evaluable pre-J-04 and a genuine acceptance clause is unmet, but the checkable kept-product core all verified intact. Reversible: yes

## Quick verify

From `reports/phase-goal-clean_slate-iter-5-what-to-click.md`:

1. Open `http://localhost:3301/` in your browser
2. Type `SIM-BUYER` into the ticker field, then click the green "Watch" button
3. Click the red "Stop" button
4. Navigate to `http://localhost:3301/structure`
5. Type `AAPL` into the "Symbol" field and `2026-06-22T21:00:00Z` into the "As-of" field, then click "Load"

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-clean_slate-iter-5.md |
| Dev handoff | — | docs/handoffs/goal-clean_slate-iter-5-dev.md |
| Review | PASS | reports/reviews/goal-clean_slate-iter-5-review.md |
| Browser QA | PASS | reports/phase-goal-clean_slate-iter-5-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-clean_slate-iter-5-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-clean_slate-iter-5-user-visible-changes.md |
| What to click | — | reports/phase-goal-clean_slate-iter-5-what-to-click.md |
| UI surface map | — | reports/phase-goal-clean_slate-iter-5-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-clean_slate-iter-5-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-clean_slate-iter-5-ux-regression.md |
| QA | PASS | reports/qa/goal-clean_slate-iter-5-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-clean_slate-iter-5-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-clean_slate-iter-5-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-clean_slate/iter-5/eval.md |
| Journey history | — | runs/goal-session-clean_slate/state/journey-history.json |
