# Iteration Summary — goal-referee-iter-8

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-15
**Iteration:** 8

## In plain words

**What you can do now:** Watch the live tape on the Cockpit, look up a stock's price map on the Structure page, and scan chart setups on the Desk — the same as always. New this round: scroll to the bottom of the Desk page and open "Referee Registry" to see five candidate research questions with plain-English reasons and live evidence counts, then pick one, confirm, and register it for real.

**What changed this time:** The Desk page has a brand-new "Referee Registry" section at the bottom. It shows a table of five candidate research questions (for example, "does this chart pattern actually predict a bounce?"), each with a plain-English reason and live evidence counts. Selecting one opens a confirmation step; confirming permanently records the question with today's date locked in as its starting line. A registered question shows two separate counts — evidence from before it was registered ("discovery," which never counts as proof) and evidence collected since. The team also fixed a wrong number working behind this screen: a "days until enough evidence" estimate used to claim some questions were "ready now" when the honest wait is 50 to 119 days.

**What's next:** Next, the product will get a rule that refuses to approve any new trading strategy unless it has passed a real check from this new fact-checking system — no exceptions.

## Headline

Referee Registry ships on /desk: shortlist + hypothesis registration (J-07); 2 write-path safety fixes

## Direction

**Signal:** improving
**Why:** J-07 (the starter-family shortlist and registration flow) moved from failing to passing this iteration, giving the operator the first real Referee action in the browser. The iteration's own hard-audit lane again caught and fixed a real write-path bug before handoff — B1 (a second, unattested snapshot-write site on J-06) and B2 (a "ready now" projection that wrongly counted old evidence toward a post-registration target) — continuing a pattern where the deep-audit lane has found a genuine fault in nearly every full-depth round this session. J-08 and J-09 remain unbuilt and J-10 stays partial pending J-09, but five iterations in a row have each landed exactly one newly-passing journey with zero regressions.

**Trend (last 5 iters):**
- Newly passing this iter: J-07
- Newly passing in last 5 iters total: J-03, J-04, J-05, J-06, J-07
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 2 (1 critical — iter-6, found and resolved the same iteration; 1 minor — iter-8, found and resolved the same iteration)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The Referee became something a person can use. On the Desk page there is now a "Referee Registry" panel that lists the five candidate research questions, shows how much evidence each already has, and lets the operator pick one and confirm it — which writes a permanent record whose start date the server stamps itself. I opened the pictures and re-ran the checks myself rather than trusting the reports: the registration really happened and survived a page reload, the whole test suite passes (2,657 collected, 2,649 passed, 8 skipped, none failed), the settings pin is unchanged, and not one of the owner's 11,274 saved files was touched. The deeper checking lane caught a real fault again — a "days until ready" number that counted old evidence as progress and so read "0 days — ready now" against the owner's real data — and it was fixed inside this same round.

## What was done

- Product changes: apps/backend/app/research/referee_registry.py, apps/backend/app/research/referee_routes.py (new route GET /research/desk/referee/registry/shortlist), apps/backend/app/research/referee_adjudicate.py, apps/frontend/app/desk/page.tsx, apps/frontend/lib/api.ts, apps/frontend/lib/types.ts
- Added the starter-family shortlist fold (5 spec-pinned candidates S-1..S-5) with live readiness numbers (occurrences, sessions, accrual rate, projected days), served via the new shortlist route.
- Added a "discovery (exploratory)" field to every registered hypothesis, separating pre-registration evidence from post-registration accrual.
- Shipped the first Referee UI slice on `/desk`: a "Referee Registry" section with the shortlist table, a select -> confirm -> register flow, and a "Registered Hypotheses" table with an honest empty state.
- Rider 1: gated the write-side snapshot so a failed oracle attestation can never mint a hypothesis's one permanent checkpoint (the audit found and fixed a second write site the developer's own fix had missed — finding B1).
- Rider 2: surfaced corrupted hypothesis files in `GET /adjudications`'s new `integrity_errors` key instead of silently dropping them.
- Audit fixed B2: `projected_days_to_target` wrongly counted pre-registration history toward a post-registration target, serving "0 days — ready now" instead of the honest 50-119 days on the real corpus.
- Verified 1 target journey (J-07) passes browser QA — 11/11 UT test cases (UT-01..UT-11) PASS.

## What's left

- Journey J-08 "The strategy family + the promotion interlock" failing — not built yet; the promotion path is still unwired.
- Journey J-09 "The Referee on /desk + MCP contract v5" failing — only 1 of 3 planned /desk Referee sections exists; MCP tool count is still 20 of the required 22.
- Journey J-10 "The kept product stands" stays partial — its era-end clauses (three Referee sections, MCP = 22 tools) wait on J-09.
- Closure gate returned CLOSURE-FAIL on a paperwork false-positive: an automated check misread the phrase "backend-only" inside a sentence describing the new visible screen as a claim of "no visible changes"; this iteration's 9 changed files remain uncommitted pending a fix to that check's wording.
- Two readiness numbers (`target_sessions`, `min_occurrences`) are computed but not shown as their own table columns on the new shortlist.
- Rider 1's write-side fix and Rider 2's integrity-errors disclosure have no UI to see them yet — there is no Referee Adjudications page (that is J-09's job).
- The starter family's error-rate setting (q=0.1) still lives as a hardcoded value in the frontend instead of a backend constant.
- The "discovery" evidence count on a registered row doesn't yet apply the same wall-condition filter its shortlist row uses, so the two tables can show different numbers for the same candidate.

## Next step

Build J-08 "The strategy family and the promotion interlock" next, on its own, at full depth — the rule that stops any new trading strategy from being crowned unless a valid, strategy-specific certificate from this era's judging machinery exists, refusing with no way around it. Full depth is not optional: the deeper checking lane has found a real fault in all three of the rounds it actually ran, and this round must not be trimmed back the way rounds 6 and 7 were. Four small items ride inside that round: make the "discovery" count respect the same wall condition the shortlist uses (or mark it an estimate); get an owner ruling on the missing short side of the wall-based candidate; move the family error-rate (0.1) out of the frontend into a backend constant; and extend the on-screen number guard to the two accrual figures now shown. For a person: commit this iteration's 9 changed files (blocked only by a paperwork check that misread "backend-only" wording) and loosen that check's wording rule; separately, and unrelated to this project, the trendora backend on port 8255 still needs restarting (open since iteration 2).

## Assumptions made

- iter-8 · goal-evaluator — Ambiguity: whether the critical anti-goal "the historical atlas is exploratory forever" covers a served projection that arithmetically subtracts pre-boundary history from a post-boundary target (the pre-fix `projected_days_to_target`). We chose: scored it minor, not critical (verdict CONTINUE, not REGRESSION) because it was found and fixed inside the same iteration, is a pure read-side number with zero persisted output, and never reached the operator's real screen. Reversible: yes.
- iter-8 · goal-evaluator — Ambiguity: whether a J-07 screenshot whose numbers (517) the same iteration's own audit later corrected (to 564) still evidences the journey. We chose: scored J-07 passing with `evidence_makeup: true`, since the screenshots still evidence the rendering behavior itself, not the stale number; a re-capture rides the next iteration as a passenger task. Reversible: yes.
- iter-8 · auditor (supersedes the developer's formula call below) — Ambiguity: no spec pins the `projected_days_to_target` formula. We chose: measure it from zero (`target_sessions / accrual_rate`), never net of the candidate's own historical `n_sessions` — the net-of-history reading had served "0 days — ready now" for all three estimand-A candidates against the real corpus when the honest wait is 50-119 days. Reversible: yes.
- iter-8 · developer — Ambiguity: whether the new "discovery" fold should apply the same stale-detector-basis exclusion the "accrual" fold already applies. We chose: yes, apply the identical check, for consistency with accrual rather than counting every basis. Reversible: yes.
- iter-8 · developer — Ambiguity: `accrual_rate_sessions_per_day`'s exact formula is not pinned anywhere in spec or code. We chose: `n_sessions / corpus_span_days`, using the whole recorded corpus's own calendar-day span as one shared denominator, computed once per call. Reversible: yes.
- iter-8 · goal-decomposer — Ambiguity: whether "no hard-coded hypothesis set anywhere in code" forbids the shortlist's five spec-pinned candidate definitions from existing as code constants, or governs only the registration write path. We chose: it governs the write path only — registration stays fully generic; the five candidates remain spec-pinned module constants. Reversible: yes.
- iter-7 · goal-evaluator — Ambiguity: whether the anti-goal "no confirmatory output without a verified oracle attestation" covers only what's served, or also an unattested confirmatory verdict written into the permanent record but never served. We chose: read it as scoped to served output, so not a critical violation; recorded as a named must-fix weakness instead. Reversible: yes.
- iter-7 · developer — Ambiguity: spec §5's verdict vocabulary lists "exploratory" as a live-fold token, but the read-side fold only ever serves already-registered hypotheses, so no served entry can honestly be "basis not registered." We chose: treated "exploratory" as a documented, currently-unreachable enum member. Reversible: yes.
- iter-7 · developer — Ambiguity: whether descriptive companion fields (confidence intervals, sign-flip p, etc.) should be withheld pre-eligibility the same way confirmatory fields (T, permutation_p) are. We chose: gate only the confirmatory fields on eligibility; compute descriptive companions whenever there is pooled data, since they carry none of the p-value peeking risk the gate exists to prevent. Reversible: yes.
- iter-7 · developer — Ambiguity: spec §4.3's entry-basis sensitivity treatment is framed only around the estimand A/C occurrence-vs-matched-null comparison; estimand B (a cell-vs-complement comparison with no null) has no stated entry-basis treatment. We chose: compute entry-basis fields for estimand A/C only; leave them honestly `None` on every B record, matching the existing "`None` when structurally inapplicable" convention used elsewhere this era. Reversible: yes.

## Quick verify

From `reports/phase-goal-referee-iter-8-what-to-click.md`:

1. Open `http://localhost:3301/desk` in your browser
2. Scroll to the very bottom of the page and click the "Referee Registry" section header (the last section on the page)
3. Look at the shortlist table's "n", "Sessions", "Accrual / day", and "Projected days" columns for all 5 rows
4. Click the "Select" button on the S-4 row
5. Click "Cancel"

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-8.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-8-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-referee-iter-8-review.md |
| Browser QA | PASS | reports/phase-goal-referee-iter-8-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-referee-iter-8-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-referee-iter-8-user-visible-changes.md |
| What to click | — | reports/phase-goal-referee-iter-8-what-to-click.md |
| UI surface map | — | reports/phase-goal-referee-iter-8-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-referee-iter-8-ui-test-plan.md |
| UX regression | UX-REGRESSION-SKIPPED | reports/phase-goal-referee-iter-8-ux-regression.md |
| QA | PASS | reports/qa/goal-referee-iter-8-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-referee-iter-8-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-referee-iter-8-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-referee/iter-8/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |
