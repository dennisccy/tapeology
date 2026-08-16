# Iteration Summary — goal-referee-iter-12

**Verdict:** GOAL_ACHIEVED
**Iteration type:** goal-lean
**Date:** 2026-08-16
**Iteration:** 12

## In plain words

**What you can do now:** Watch the live tape on the Cockpit, check a stock's support/resistance map on the Structure page, and scan chart setups on the Desk. On the Desk page, open "Referee Registry" to review candidate research questions — each one now also shows how many trading sessions are truly on record and a wait measured in recorded sessions, not just raw calendar days — and register one, which locks in its start date for good. Open "Referee Adjudications" to see each registered question's plain verdict and evidence trail, and "Referee Runs" to start a check, watch it run, cancel it, or review past runs. The core trading strategy stays protected: it can only be replaced by a new one carrying a genuine, matching certificate.

**What changed this time:** On the Desk page's "Referee Registry" section, a new line now states how many trading sessions are truly on record, the span of dates they cover, and how long the longest silent stretch was — and a new "Projected sessions" column sits next to the existing "Projected days" column, showing each candidate question's expected wait measured in recorded sessions instead of raw calendar time. The old calendar-day numbers are still there too, unchanged.

**What's next:** Nothing new is planned right now — every planned ability now works, so the team is pausing here instead of starting a new chapter.

## Headline

Referee Registry now shows the wait in recorded sessions, not just calendar days — completing Era 6.

## Direction

**Signal:** improving
**Why:** J-11 (the accrual-basis disclosure) went from not-yet-built to passing this iteration, clearing the goal-proposer's entire appended backlog and bringing the Must-have set to 11/11 passing with zero regressed and zero newly failing. The evaluator declared GOAL_ACHIEVED again — this session's second such verdict — backed by a fresh full-suite run (2,695 collected / 2,687 passed / 8 skipped) and an unchanged fingerprint pin (`08e471b10130e1e2`). Direction reads improving rather than holding because this iteration closed real open scope, not just re-verified existing evidence.

**Trend (last 5 iters):**
- Newly passing this iter: J-11
- Newly passing in last 5 iters total: J-07, J-08, J-09, J-10, J-11
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 2 minor (iter-8's projected-days formula bug, found and fixed the same iteration; iter-9's certificate-evidence-identity gap, closed in iter-10) — both resolved, zero critical
- Iters with no journey state change: 1 of last 5 (iter-11, an evidence-only verification round)

**Latest evaluator reasoning:** The one new task in this round is done and I checked it myself. On the Desk page, the "Referee Registry" panel now shows a plain line saying how many trading sessions the system has actually recorded, over what span of dates, and how long its longest silent stretch was — plus a new column giving each candidate question its expected wait counted in recorded sessions instead of raw calendar days. The old calendar-day numbers are still there, side by side, and they did not move: the same picture shows 0.02 per day and 564 days exactly as before. All eleven journeys now hold current evidence, no rule violation is open, and the structure check passed, so the goal is met.

## What was done

- Product changes: apps/backend/app/research/referee_registry.py, apps/backend/tests/test_referee_registry.py, apps/backend/tests/test_desk_ui_guards.py, apps/frontend/lib/types.ts, apps/frontend/app/desk/page.tsx, docs/referee-statistical-spec.md
- Added an `accrual_basis` corpus disclosure (recorded/pooled session counts, date span, longest zero-session gap) plus two new per-candidate fields to `shortlist_response()`, reusing the existing single store scan — no new store reads.
- Rendered a new basis line and a "Projected sessions" column in the Desk page's Referee Registry section, beside the shipped calendar-day pair, with zero client-side arithmetic.
- Added 6 new backend tests (hand-computed fixture numbers, zero-denominator case, two-call determinism, store-scan-count pin, `referee_parameters()` golden-hash pin) plus a UI-guard counter-test.
- Appended a dated addendum to `docs/referee-statistical-spec.md` §9 stating the disclosure feeds no statistical procedure.
- Confirmed the shipped calendar-day fields stayed byte-identical, the fingerprint pin (`08e471b10130e1e2`) is unchanged, and MCP still exposes exactly 22 tools.
- Verified 5 target/regression journeys (J-05, J-07, J-09, J-10, J-11) pass browser QA; full backend suite green (2,695 collected / 2,687 passed / 8 skipped, 0 failures).
- Evaluator declared GOAL_ACHIEVED — all 11 Must-have journeys now pass, closing Era 6 "The Referee" a second time.

## What's left

- All Must-have journeys passing, no closure blockers.

## Next step

Halt — the goal is met; nothing needs building. Three items remain for a person, none of them product faults: commit this round's changed files along with earlier rounds' evidence files; the era still has no video walkthrough because the shared recording tool can't play a "scroll" step — J-11's own walkthrough script already uses only supported actions, so the recording can simply be taken once that shared tool is fixed, with no new build round needed; and four small clean-ups can ride along whenever someone next works in those files (add the four Referee storage folders to the store-scope guard, make a nameless certificate fail instead of match, show a clear word instead of a dash on a failed second data fetch, and fix a stale comment quoting old test counts). Also still outstanding, unrelated to this project: the trendora backend on port 8255 has been down since iteration 2. Approve closing the era and committing the files.

## Assumptions made

- iter-12 · goal-evaluator — Ambiguity: TC-14 requires every screenshot's checksum to differ, but the images cited for J-05 and J-11 are byte-identical (one whole-page capture). We chose: accepted the shared file after opening it and confirming it genuinely shows both journeys' end states (the registered S-1 row, and the new basis line/column), rather than scoring either journey down. Reversible: yes.
- iter-12 · goal-evaluator — Ambiguity: J-11's acceptance names a demo-narrator walkthrough, but none was produced — no demo step runs at lean depth and the shared recorder still can't play a "scroll" action. We chose: scored J-11 passing with the gap recorded as a capture defect, since the behaviour is proven by screenshot, backend tests, and a golden replay script; the recording is left as a human/finalization item, not a new build round. Reversible: yes.
- iter-12 · goal-decomposer — Ambiguity: goal.md's Step 4 asks for "one new right-aligned column" (singular) even though the same step's API additions are a pair, mirroring a shipped rate/projection pair that already gets two columns. We chose: render exactly one new table column (`projected_pooled_sessions_to_target`); the paired field (`informative_sessions_per_pooled_session`) is served on the API but gets no dedicated column this iteration. Reversible: yes.
- iter-11 · goal-evaluator — Ambiguity: goal.md's J-09 acceptance names a screenshot of an in-flight second "evaluation" trigger refused single-flight, but the captured image shows the null-build trigger refused instead (same panel, same code shape). We chose: read "evaluation trigger" as "a Referee Runs compute trigger" and accepted the null-build capture, clearing J-09's evidence gap. Reversible: yes.
- iter-11 · goal-decomposer — Ambiguity: the prior iteration's next-step named three follow-ups, one of which (fixing the shared walkthrough recorder's missing "scroll" action) is a code fix, but this iteration's binding depth ("evidence") structurally cannot dispatch code work. We chose: treated the recorder fix as out of scope — it is vendored framework tooling, not Tapeology product code. Reversible: yes.
- iter-10 · goal-evaluator — Ambiguity: J-10's kept-product browser walk asks for every shipped Desk section rendered plus a byte-identity check against an era-open baseline, but the fixture rig has no computed screen (screen-dependent panels show "not computed yet") and no baseline artifact was ever captured this era. We chose: scored J-10 passing, treating the not-computed panel as the shipped behaviour for an empty store, and substituting a full source-level diff proving every kept route handler untouched. Reversible: yes.
- iter-10 · goal-evaluator — Ambiguity: goal.md names a screenshot of an in-flight second evaluation trigger refused single-flight, but the cited image was byte-identical to two unrelated screenshots because the shipped UI disables the trigger on click, so a second request never fires. We chose: scored J-09 passing with the gap logged as a capture defect, since the refusal behaviour is proven three other ways (a unit test, a 5-concurrent-request probe, and the UI's own reachable refusal path). Reversible: yes.
- iter-10 · developer — Note (a scope call, not a formal ambiguity): the QA fixture-setup step (seeding a fragile hypothesis and a refused-attestation hypothesis) was left to the browser-qa-agent's own preparatory step rather than built by the developer, following the iter-9 precedent; the dev handoff documents the exact mechanics so QA doesn't have to reverse-engineer them. Reversible: yes — a future iteration could equally have the developer build the fixture setup instead.
- iter-10 · developer — Ambiguity: the new Referee Adjudications and Referee Runs sections both need registry data, but it was unclear whether they should assume the Referee Registry section was already expanded (and its data fetched) first. We chose: both new sections issue their own harmless read of the already-shipped registry endpoint on first expand, into the same shared state, so both work correctly regardless of click order. Reversible: yes.
- iter-10 · developer — Ambiguity: the Referee Adjudications provenance line needs to show a hypothesis's "seed identity," but no served field anywhere carries the raw random seed value — it's a single global constant never persisted per-hypothesis, and adding a new served field was out of scope. We chose: render "seed identity" as the entry's own hypothesis ID (already served per-entry), the one truly per-hypothesis part of the real seed recipe, rather than hardcode or newly-serve the raw constant. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-12.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-12-dev.md |
| Review | PASS | reports/reviews/goal-referee-iter-12-review.md |
| Browser QA | PASS | reports/phase-goal-referee-iter-12-ui-test-results.md |
| Goal evaluation | GOAL_ACHIEVED | runs/goal-session-referee/iter-12/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |
