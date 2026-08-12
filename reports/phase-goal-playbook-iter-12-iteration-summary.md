# Iteration Summary — goal-playbook-iter-12

**Verdict:** GOAL_ACHIEVED
**Iteration type:** goal-lean
**Date:** 2026-08-12
**Iteration:** 12

## In plain words

**What you can do now:** On the Desk page, you can scan any trading day for nine classic intraday chart patterns (opening-range breakouts, jump moves, capitulation sell-offs, cup-and-handle setups, and range trades among them), each one checked against what would happen by pure chance. You can run one bulk pass that fills in pattern records across every day already on file, and read an honest evidence table showing how each pattern has actually performed — including how many of its recorded signals could be measured at all, and exactly which recorded days that table is built from. The connected Claude assistant can read the pattern records and the evidence table directly.

**What changed this time:** The Desk page's Playbook Evidence section now shows a new "Basis" line stating how many records and which days a pooled result is built from, plus five new columns showing how many of a pattern's signals could actually be measured versus how many were simply unmeasurable at that time window — so a count like "0 measured" is now clearly shown as "15 signals were unmeasurable there," not mistaken for a tiny sample. The date box in the Playbook Signals section also now visibly turns orange when you type an invalid date, instead of staying grey.

**What's next:** The Playbook chapter is now finished — every planned capability works and nothing built earlier broke. What's left is just tidying up: correcting an old summary file that wrongly claims a fix shipped earlier than it did, taking one photo of the new orange warning box in action, and making sure future summaries only claim what was truly built and captured.

## Headline

J-11 ships: Evidence cells now disclose n_unmeasured/n_sessions/basis — all 11 journeys passing, era complete

## Direction

**Signal:** improving
**Why:** This iteration shipped J-11 "Every evidence cell states the basis of its own n" plus two carried passenger fixes, with zero diff to the measurement rail, detector code, or spec (git-proven by both the reviewer and the evaluator). All 11 Must-have journeys now pass and nothing regressed; the evaluator returned GOAL_ACHIEVED and the independent two-key confirm pass returned CONFIRM_ACHIEVED, closing the Playbook era. Three small showcase-artifact honesty items (an inaccurate prior demo file, a source-proven-but-unphotographed fix, two duplicate proof screenshots) are carried into the next chapter, none of them blocking.

**Trend (last 5 iters):**
- Newly passing this iter: J-11 "Every evidence cell states the basis of its own n"
- Newly passing in last 5 iters total: J-08 "The evidence view" (iter-8), J-09 "MCP contract v4" (iter-9), J-10 "The kept product stands" (iter-9), J-11 "Every evidence cell states the basis of its own n" (iter-12)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 3 minor (all opened iter-8 — a real-backend write during automated replay, an incomplete store-scope guard, and a misleading evidence-register sentence; 2 closed within iter-8 itself, the third closed iter-9)
- Iters with no journey state change: 2 of last 5 (iter-10, iter-11)

**Latest evaluator reasoning:** The one new journey of this run, J-11 "Every evidence cell states the basis of its own n", is built and works. I opened the picture myself: the Playbook Evidence panel on the Desk page now carries a new line — "Basis: 5 records pooled from 2026-06-22, 2026-06-23, 2026-06-24, 2026-06-25, 2026-08-07" — right under the line that names the signature, and the table now shows, for every row, how many recorded signals could not be measured at that time window and how many different days the row draws on. The first row reads "0 measured, 15 unmeasurable" side by side, which is exactly what the journey asks a reader to be able to see. All eleven journeys now pass, nothing kept has broken, and the coherence audit passed on its own.

## What was done

- Product changes: apps/backend/app/research/desk_playbook_evidence.py, apps/backend/app/research/desk_playbook_backscan.py, apps/backend/app/research/desk_routes.py, apps/backend/tests/test_desk_playbook_evidence.py, apps/backend/tests/test_desk_playbook_backscan.py, apps/backend/tests/test_desk_ui_guards.py, apps/backend/tests/test_mcp_server.py, apps/frontend/lib/types.ts, apps/frontend/app/desk/page.tsx
- Extended the already-registered Evidence aggregates endpoint (`GET /research/desk/playbook/evidence`) with seven new fields — per-cell `n_unmeasured`/`n_sessions` (signal) and `n_truncated`/`n_unmeasured`/`n_sessions` (baseline), `other_signatures[].n_records`, and a new payload-level `basis` block (dates/record count/created span) for the pooled signature — with zero diff to `desk_forward.py`, the cache schema, or the detector spec.
- Rendered the new basis line and five new cell columns on `/desk`'s Playbook Evidence section — a pure pass-through of the enriched API body, no client-side arithmetic.
- Landed two carried passenger fixes: `TAPEOLOGY_BAR_INDEX_DB` added as a 5th required var in the backscan store-scope guard, and the Playbook Signals date input now renders an amber border (Tailwind `!important` fix) on an invalid value, scoped to that one input only.
- Added 14 net-new backend tests (8 evidence-fold cases, 2 backscan-guard, 4 UI-guard) plus a new J-11 golden replay script; full backend suite 2,182 passed / 8 skipped / 0 failed (above the 2,168 floor).
- Review verdict PASS (one NOTE-level nit on a tautological test assertion); config fingerprint (`08e471b10130e1e2`) and MCP tool count (20) both confirmed unchanged.
- Verified 8 journeys pass browser QA (1 new target J-11 + 7 regression replays), 0 skipped; the goal-evaluator returned GOAL_ACHIEVED and the independent two-key confirm pass returned CONFIRM_ACHIEVED.

## What's left

- Historical showcase artifact `reports/phase-goal-playbook-iter-11-demo.json` is still inaccurate — it claims the amber-border fix was built and verified in iteration 11 (it was not; it shipped in this iteration) and clicks Evidence/Signals tabs the Desk page does not have. Needs correction or re-recording before the era's showcase is published.
- The amber-border fix (this iteration) is proven correct in source and pinned by a source-scan guard test, but was never captured on screen turning amber this run — it stands on source proof only, not a screenshot.
- Two of this iteration's own proof screenshots, `J-08-verify.png` and `J-09-verify.png`, are byte-identical wrong-subject (top-of-page) frames — J-08 and J-09 stand on their passing replay assertions, not on those images.
- This iteration's own closing-step showcase walkthrough (demo-narrator recording), when produced, must mark a step `new`/`verified` only for content that was really built and really captured, and must never click a `role=tab` element (the Desk page has none) — the same mistake the iteration-11 recording made.

## Next step

Halt — the era is finished. All eleven journeys pass, nothing kept has broken, and no anti-goal is open. Three small write-up items are carried, not fixed, and none is a product fault: the iteration-11 showcase file must be corrected or re-recorded (it still claims an unbuilt repair), the amber-border fix needs one photograph to close the loop, and this run's own walkthrough recording must mark steps new/verified only when truly built and captured, and must never click a Desk-page tab that doesn't exist. The owner should either accept the era as finished and let these three items ride into the next chapter, or ask for one short pass that re-records the two showcase files honestly and photographs the amber border once.

## Assumptions made

- iter-12 · goal-evaluator — Ambiguity: the amber-border passenger fix is proven in source and pinned by a source-scan guard test, but no browser row exercised it this run, and nothing states how to score a visual fix that is not any journey's acceptance line and not an anti-goal. We chose: it does not gate GOAL_ACHIEVED and is not scored as verified either — recorded as fixed-in-source, unverified-on-screen. Reversible: yes — one browser row re-added next pass closes it.
- iter-12 · goal-evaluator — Ambiguity: J-11's acceptance text is met literally by a captured cell showing `n_unmeasured: 15` beside `n: 0`, but the journey's own stated purpose paradigm case is a non-zero `n` beside a large `n_unmeasured`, which exists only on the real corpus (confirmed over REST, not photographed). We chose: J-11 passing — the acceptance sentence is the binding text and is met literally and visibly; the mechanism is proven identical for every cell by test and a byte-for-byte cross-check against the live API. Reversible: yes — one capture on the real corpus closes it with zero product change.
- iter-12 · goal-decomposer — Ambiguity: three carried, disclosed-not-fixed items from prior iterations (the amber-border collision, the bar-index scoping gap, and the inaccurate iteration-11 demo file) were named in the dispatch prompt, and docs/goal.md names none of them, so nothing says whether they belong inside this iteration's scope. We chose: fold the first two in as cheap, isolated passengers with zero risk to J-11's own diff; excluded the third — correcting a historical showcase JSON file is not source code, so it is flagged for whoever next regenerates the era's showcase materials, not built here. Reversible: yes — both passenger fixes are isolated, low-blast-radius changes.
- iter-11 · goal-evaluator — Ambiguity: two of iteration 11's three planned items were never built, so its own Definition of Done was unmet, and nothing states which wins when an iteration under-delivers while the era's own bar is fully met. We chose: the era's bar wins — GOAL_ACHIEVED. Neither unbuilt item is a Must-have journey acceptance line or an anti-goal; both were carried into the halt justification so the owner could overrule cheaply. Reversible: yes — a one-line owner instruction reopens the session via --resume.
- iter-11 · goal-evaluator — Ambiguity: the iteration-11 showcase file narrates the amber-border fix as shipped when it was proven in source never to have been built, and nothing in docs/goal.md says whether a false claim in a non-product showcase artifact counts as one of its anti-goals. We chose: not an anti-goal violation, so it did not bar GOAL_ACHIEVED — but recorded loudly in four durable places as an open honesty defect that must be corrected before the era's showcase artifacts are published. Reversible: yes — correcting or re-recording the demo closes it with zero product change.
- iter-11 · goal-decomposer — Ambiguity: the invalid-date input's border staying grey instead of turning amber was left open with two sanctioned outcomes (fix the CSS class or drop the expectation), with no owner input on this specific point. We chose: fix, scoped to the one flagged input only, not the shared CSS constant or the other four call sites, as the cheaper, more honest default absent a contrary owner signal. Reversible: yes — a one-input CSS override with no data, schema, or signature implications.
- iter-11 · goal-decomposer — Ambiguity: J-09 was asked to get a saved replay script since it was the only journey without one, but the replay engine supports only five browser action types and no API/MCP-call action type exists anywhere in the codebase. We chose: author a golden that opens /desk and asserts an already-shipped shell string, honestly scoped as coverage of the data the MCP tools proxy, not of MCP transport/registration itself. Reversible: yes — the golden script is additive test infrastructure, nothing load-bearing on any served field.
- iter-10 · goal-evaluator — Ambiguity: J-09 carried a deferred status (no lane re-verified it that run) even though the evaluator independently confirmed its acceptance live, and nothing said whether the evaluator's own live check counts as that iteration's re-verification. We chose: it does not — J-09 kept its passing status but its verification stamp stayed at the prior iteration, and the live check was recorded as an evaluator observation, not a lane verdict. Reversible: yes.
- iter-10 · goal-evaluator — Ambiguity: a failing check (the invalid-date input's border never turning amber) names a colour docs/goal.md never mentions, so it is a test-designer expectation, not an acceptance line or an anti-goal, and nothing says whether such a row should count against a journey's status. We chose: it does not downgrade any journey — cosmetic and pre-existing — but the failing row was left standing rather than argued away. Reversible: yes.
- iter-10 · goal-evaluator — Ambiguity: whether two "the spec is canonical" items open since iteration 6 are discharged by the owner's R-3 ruling, since nothing states what evidence turns an owner ruling into a discharge. We chose: discharge requires both the ruling and the spec catch-up edits it directs to have actually landed — verified both in source before marking either resolved. Reversible: yes.
- iter-10 · goal-decomposer — Ambiguity: an owner ruling directed a second range-trade disclosure field reusing an already pre-registered constant, but named neither the field itself. We chose: commit to `geometry.turned_at_midrange` as the one canonical name, registered consistently across the spec, the detector code, the frontend types, the `/desk` chip, and the blueprint. Reversible: yes — a rename before the field ships touches only a handful of isolated call sites; no signature or stored record is keyed by its name.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-playbook-iter-12.md |
| Dev handoff | — | docs/handoffs/goal-playbook-iter-12-dev.md |
| Review | PASS | reports/reviews/goal-playbook-iter-12-review.md |
| Browser QA | PASS | reports/phase-goal-playbook-iter-12-ui-test-results.md |
| Goal evaluation | GOAL_ACHIEVED | runs/goal-session-playbook/iter-12/eval.md |
| Journey history | — | runs/goal-session-playbook/state/journey-history.json |
