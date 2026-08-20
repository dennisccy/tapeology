# Iteration Summary — goal-rapid-microscope-iter-17

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-08-20
**Iteration:** 17

## In plain words

**What you can do now:** See on the Desk page how much market data is on hand and which research checks remain unmet, including honest totals for hidden recording batches (a total only, never a list). Watch buying and selling pressure tracked tick by tick. See trading signals matched to chart structure without ever peeking ahead. Browse a permanent record of every quick trading idea tested — kept or killed, nothing hidden — plus a panel showing how those ideas held up over time. Check whether any idea has "graduated" yet (none have). Ask a Claude conversation to read all of this the same way a person would on screen.

**What changed this time:** Nothing changed on any screen this round. Behind the scenes, the check that decides whether a hidden (sealed) recording batch counts as a pass or a fail now computes its own honest answer from the real evidence — before, it just believed whatever answer it was handed. A related calculation, the "earliest safe date" for a future re-check, was also fixed to look at every idea a family ever tried (including ones that were killed), not just the winner, so it can no longer be gamed by quietly ignoring inconvenient results.

**What's next:** Next, the pass/fail check for sealed recordings will be fixed so it can never be told a single reading is enough — it will set its own minimum data requirement (30 readings) instead of trusting whoever asks it, exactly as the project owner ruled today.

## Headline

Sealed-shard evaluation now computes its own pass/fail verdict instead of trusting a caller's answer

## Direction

**Signal:** holding
**Why:** No journey changed status this iteration — J-01/J-04/J-05/J-07/J-08 were all re-verified passing with zero regressions, and J-10 stays partial by design (29/29 traps landed; only the deliberately out-of-scope repeat-run check and the just-ruled TR-30 remain). The independent auditor found a real but currently-unreachable anti-goal gap in `micro_sealed_evaluation.py` (caller-supplied minimum-sample floors), which forced a same-day owner ruling (spec r9/TR-30) — the next full round targets exactly that fix.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-08 (iter-15)
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 5 new (all minor, 0 critical) opened across iters 15–17; 2 remain open at iter-17 end (sealed-verdict floors caller-supplied — TR-30 target; J-10 replay-script Playbook Evidence assertions not yet restored)
- Iters with no journey state change: 2 of last 3

**Latest evaluator reasoning:** This round built the two safety checks it promised, and I confirmed both myself rather than trusting the reports. The safety-test set is now 29 of 29. No journey moved forward or backward this round, and that was the plan: J-10 "The kept product stands" was always going to stay "partly done". The one important thing found this round was found by the independent checker, not by the review or the quality check: the new sealed-result judge lets the person asking the question hand in their own minimum sample size, so a single reading could be recorded as a permanent "pass".

## What was done

- Product changes: apps/backend/app/research/micro_sealed_evaluation.py (new), apps/backend/app/research/micro_graduation.py, apps/backend/app/research/micro_accessor.py, apps/backend/tests/test_micro_sealed_evaluation.py (new), apps/backend/tests/test_micro_graduation.py, apps/backend/tests/test_micro_accessor.py, apps/backend/tests/test_micro_observer.py
- Built `micro_sealed_evaluation.py` (TR-23), the sole owner of the sealed-shard evaluation verdict — recomputes outcomes from canonical evidence and derives a tri-state PASS/FAIL/insufficient verdict instead of trusting a caller-supplied pass/fail.
- Rewrote the confirmation-boundary formula (TR-24) in `micro_graduation.py` to scan a candidate's whole lineage — survivors, killed siblings, folds of any verdict — instead of just the winner, closing a "quietly discard inconvenient evidence" gaming vector.
- Retired `record_sealed_evaluation`'s caller-supplied `passed: bool`; corrected `micro_accessor.py`'s stale docstring; closed GAP B3 (exact-instant exposure boundary) and GAP B4 (trade-terminated session stamp).
- Trap suite reached 29/29 (TR-1 through TR-29); full backend suite green at 3,263 passed / 8 skipped / 0 failed (25 more tests than the round started with).
- Ran J-10's stored replay script through the deterministic harness for the first time this era; it genuinely failed on pre-existing real-store data drift unrelated to this round's code, left byte-unchanged per plan.
- Verified 6 journeys (J-01, J-04, J-05, J-07, J-08, J-10) via browser QA — 16/16 checks PASS, zero regressions.

## What's left

- J-09 "The pilot studies" failing — deliberately unbuilt; its blocking prerequisite (TR-22) landed, but it stays out of scope until the trap-suite work finishes.
- J-06 "The recorder and the Vault" partial — `vault.py` untouched this round; step 4 (credentialed real-tape recording) remains operator-gated and out of scope.
- J-10 "The kept product stands" partial — 29/29 traps landed, but its own goal text was edited today to ask for 30 (TR-30, just ruled by the owner); the repeat-run check (step 2) also stays out of scope by design.
- New anti-goal item (minor, open): the sealed-verdict evaluator's minimum-sample-size floors are still caller-supplied, not yet fixed — the owner's ruling (spec r9/TR-30) requires the fix land before any sealed graduation is allowed to count.
- Bookkeeping gap (minor, open): this round's quality report wrongly claimed the browser checks ran against the real data store; they correctly ran against the sanctioned throwaway rig, but the report should say so.
- J-10's replay script still carries two Playbook Evidence assertions dropped last round, not yet restored (left unchanged after a genuine, unrelated data-drift failure this round).
- Two older open items carried forward: the Referee-freeze disclosure work (open since round 9) and the anchor-lag ledger-recovery gap (open since round 13, owner-deferred).

## Next step

Build TR-30 next — the rule the owner wrote today — as a full round with the independent checker: the sealed-result judge must own its own minimum sample size and refuse any figure handed to it by the caller; a single hidden day must be recorded as "does not apply to one day" rather than quietly as 1 for its two breadth figures; and the rule fingerprint on the record must match the rule that actually ran. Carry four small passengers: add the three fixtures the checker named that can genuinely fail; make J-07's browser proof able to tell right from wrong by seeding one family into the test store; decide once for the era whether stored replay scripts may assert "empty" wording at all; and have the quality lane report the running server's actual data store rather than its own shell. Do not record real tape, and do not start J-09 yet.

## Assumptions made

- iter-17 · goal-evaluator (third) — Ambiguity: whether ESCALATE is available when the decision tree's literal clauses don't fire, asked again for a sixth consecutive round. We chose: ESCALATE — a deliberate departure from the tree's literal text, justified by an audit finding proven by execution (not just a test-quality finding) that forced a same-day owner ruling, plus this iteration again overran its clock and shed the ux-regression reviewer. Reversible: yes — ESCALATE only sets next iteration's depth; TR-30 reaching 30/30 mutation-proved lets a later evaluator return to plain CONTINUE.
- iter-17 · goal-evaluator (second) — Ambiguity: whether J-07 "Graduation" sustains `passing` when its own module was rewritten but its designated browser check (an empty JSON response) can't discriminate a working rewrite from a broken one. We chose: keep `passing`, weakness named as a passenger, because the substance was mutation-proved three independent ways (dev, reviewer, auditor) even though the screenshot alone can't tell right from wrong. Reversible: yes — seeding one family into the test store next round makes the check discriminating; if it then shows a defect, J-07 re-opens immediately.
- iter-17 · goal-evaluator — Ambiguity: whether the audit's proven defect (the sealed-verdict evaluator accepts caller-supplied minimum-sample floors) counts as a CRITICAL "manufacture a survivor" anti-goal violation or an open minor item. We chose: minor and open, not critical — zero production callers reach it, no sealed-evaluation row exists anywhere, the champion pointer is still v1 on screen, the round's own fix already improved the rail, and the owner ruled the same day (r9/TR-30). Reversible: yes — re-opens as CRITICAL the moment any production caller is wired to it or a sealed-evaluation row appears on disk.
- 2026-08-20 · owner ruling — spec revision r9 "sealed sufficiency is shard-scoped and pinned": pins a new constant SEALED_MIN_OBSERVATIONS=30, forbids any caller-supplied sufficiency value, records single-shard breadth as "not_applicable_single_shard" rather than silently 1, and requires the fix land before any sealed graduation is allowed to count. Reversible: no — this is a binding owner decision, not a reversible interpretation call; it revises the canonical spec (docs/rapid-validation-spec.md, docs/goal.md trap range TR-1..29 → TR-1..30).
- iter-17 · goal-decomposer (second) — Ambiguity: the r6 ruling requires a "lineage_data_frontier" derived from each evidence item's own "observed_through," but no ledger row anywhere is literally named that field. We chose: direct the developer to derive each item's "evidence consumed" instant from its own already-recorded timestamp field, never fabricate a new one — and drop + flag any item type that genuinely has no defensible field, rather than inventing a value. Reversible: yes — if the developer finds a type that can't supply a defensible instant, that gap surfaces as a fresh owner-ruling escalation.
- iter-17 · goal-decomposer — Ambiguity: whether to correct `micro_accessor.py`'s stale docstring (which describes an origin-fenced read path with zero production callers) or wire the fence live. We chose: correct the docstring only, do not wire the fence — the new sealed-evaluator's shard read matches the existing unfenced whole-corpus read pattern, not the fenced walk-forward pattern the stale text claims. Reversible: yes — if a future round genuinely needs an origin-fenced read, wiring the fence then is a clean additive change and the docstring can be corrected again.
- iter-16 · goal-evaluator (third) — Ambiguity: whether two audit-found untested boundary cases inside anti-goal-certifying code (a `<`→`<=` exposure-timing edge and a session-truncated stamp fixture) count as anti-goal violations or tracked coverage gaps. We chose: affirm as GAPs, not violations — verified in source that widening the boundary only makes evidence MORE conservative (never manufactures a fake pass), and the shipped code's stamp is already correct, only the fixtures can't discriminate it. Reversible: yes — either re-opens as IMPORTANT immediately if a future edit reintroduces the risky direction or a caller needs the exact boundary.

## Quick verify

From `reports/phase-goal-rapid-microscope-iter-17-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser
2. Open your browser's DevTools console (press F12, then click the "Console" tab) and leave it open for the rest of this guide
3. Click the "Microscope Readiness" section header, then "Scout Ledger", then "Walk-Forward", then "Validation Vault", one at a time
4. Click "Referee Registry", then "Referee Adjudications", then "Referee Runs"
5. Refresh the page (press F5 or Cmd+R)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-rapid-microscope-iter-17.md |
| Dev handoff | — | docs/handoffs/goal-rapid-microscope-iter-17-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-rapid-microscope-iter-17-review.md |
| Browser QA | PASS | reports/phase-goal-rapid-microscope-iter-17-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-rapid-microscope-iter-17-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-rapid-microscope-iter-17-user-visible-changes.md |
| What to click | — | reports/phase-goal-rapid-microscope-iter-17-what-to-click.md |
| UI surface map | — | reports/phase-goal-rapid-microscope-iter-17-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-rapid-microscope-iter-17-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-rapid-microscope-iter-17-ux-regression.md |
| QA | PASS | reports/qa/goal-rapid-microscope-iter-17-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-rapid-microscope-iter-17-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-rapid-microscope-iter-17-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-rapid-microscope/iter-17/eval.md |
| Journey history | — | runs/goal-session-rapid-microscope/state/journey-history.json |
