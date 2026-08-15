# Iteration Summary — goal-referee-iter-6

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-08-15
**Iteration:** 6

## In plain words

**What you can do now:** Watch the live tape on the Cockpit, look up a stock's price map on the Structure page, and scan for chart setups on the Desk — the same three screens as before. Behind those screens, the product can now also count its own evidence honestly, tell a real pattern from noise using careful statistics, compare a signal against fair "nothing happened" moments, and write a research question down before checking it. None of that last group has a screen of its own yet.

**What changed this time:** Behind the scenes (backend-only work — nothing new to click yet), the product gained a permanent notebook for research questions: a specific question like "does this chart pattern mean something more than chance?" can now be written down before anyone checks whether it's true, with an honest starting date stamped automatically that can never be edited later. While double-checking this new feature, the team found a real problem — the starting date could secretly be set to an earlier day, which would have let old data sneak in and count as fresh proof — and fixed it before anything was ever saved for real.

**What's next:** Next, the product will build the actual judge: the piece that compares each recorded pattern to its fair comparisons and writes down one permanent, final verdict on whether it's real.

## Headline

The hypothesis registry: a research question can be recorded permanently before evidence exists to confirm it

## Direction

**Signal:** improving
**Why:** J-05 "The registry" moved from failing to passing this iteration, joining J-01–J-04 as verified-passing while the required-still-passing journeys held on unchanged code. The deep-audit lane caught and fixed a critical anti-goal violation (a caller could backdate the immutable registration boundary via a sibling request field) before the iteration closed and before anything was committed — the same discipline that caught iteration 3's statistics bug — so nothing shipped broken. J-06 is targeted next, again at full depth, because the lighter review+QA passes have now twice missed a serious defect that only the hard audit caught.

**Trend (last 5 iters):**
- Newly passing this iter: J-05 "The registry — pre-registration with an immutable boundary"
- Newly passing in last 5 iters total: J-02 "The evidence contract", J-03 "The statistics core", J-04 "Matched nulls", J-05 "The registry" (iters 2–6)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 1 critical (iter-6, "the historical atlas is exploratory forever" — found and fixed inside the same iteration, before anything was committed)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The registry is real. A person can now write a trading question down before its answer data exists; the system stamps the start date itself from the moment of writing, and neither the question nor that date can ever be edited or deleted afterwards. I proved every clause of its acceptance myself with a 27-check probe against the real code and the real web address, and I re-ran the whole test suite myself (2,595 collected, 2,587 passed, 8 skipped, nothing failed). The deeper checking lane earned its keep this round: it found that the start date was secretly choosable by whoever sent the request — old historical days could be made to count as fresh proof — after the ordinary review and the routine test pass had both called the work complete.

## What was done

- Product changes: apps/backend/app/research/referee_registry.py (new), apps/backend/app/research/referee_routes.py, apps/backend/app/research/referee_null.py, apps/backend/tests/test_referee_registry.py (new), apps/backend/tests/test_referee_null.py, apps/backend/tests/test_referee_guards.py, GET /research/desk/referee/registry, POST /research/desk/referee/registry/hypotheses
- Built `referee_registry.py`: four append-only stores (Family/Hypothesis/Withdrawal/Certificate); no update/delete method anywhere; duplicate identity refused
- Registration (CLI + POST) is one explicit, confirmed act that stamps a server-computed boundary date and refuses malformed/duplicate/retroactive-boundary/unknown-spec-id payloads, each distinctly, with nothing written on any refusal
- Added withdrawal (refuses once a post-boundary evaluation exists) and a live per-hypothesis accrual readout, disclosed as `is_proxy: true`, reusing existing evidence-pooling code rather than a second computation
- Shipped two small riders: a null-eligibility bug fix (serve `None`, not a fabricated `0.0`, when nothing was measurable) and a stronger seeded-draw test that finally discriminates the random selection
- Hard audit found and fixed a critical anti-goal violation in the same iteration: the boundary date was backdateable through a sibling request field (`registered_at`), letting old historical sessions count as fresh proof — closed on both the route and the CLI, with regression tests, and independently re-verified fixed
- Also fixed by the audit: a duplicate registration under a new family id used to leave a permanent phantom family record behind the refusal — now blocked before any write happens
- Full suite grew from 2,553 to 2,595 tests collected (2,587 passed, 8 skipped, 0 failed); fingerprint (`08e471b10130e1e2`) and MCP tool count (20) unchanged
- No browser QA ran or was required this iteration (Frontend Present: no; J-05 carries no browser acceptance) — verified instead via a 27-check backend acceptance probe against the real module and the real route

## What's left

- Journey J-06 "Estimand engines + adjudication — one checkpoint, recorded forever" failing — the actual statistical judge (permutation test + verdict) is not yet built
- Journey J-07 "The starter family — historical exploration becomes registered questions" failing — no registration UI on /desk yet; real question approval remains an operator act
- Journey J-08 "The strategy family + the promotion interlock" failing — certificate minting and the promotion gate are not built
- Journey J-09 "The Referee on /desk + MCP contract v5" failing — no Referee section on /desk yet; MCP still serves 20 tools, not 22
- Journey J-10 "The kept product stands — regression sentinel" partial — its browser regression walk did not run this iteration; must run next iteration before a second consecutive skip becomes a real evidence gap
- Two disclosed-but-unfixed audit gaps: a corrupted withdrawal file would be mis-reported as an ordinary "already withdrawn" refusal instead of surfacing the corruption; the registry's GET response silently drops any per-store integrity errors instead of disclosing them
- Minor cleanup outstanding: three unused imports in `referee_registry.py`, and the seeded-draw test still re-derives its expected answer from the code under test rather than a pinned literal
- No real research questions have been registered yet — this iteration proves the mechanism on test data only; the operator's real approval of 2–3 starter questions is a later step
- Outstanding for a person, unrelated to this project: the trendora backend on port 8255, stopped since iteration 2, still needs restarting

## Next step

Build J-06 "Estimand engines and adjudication" next, on its own, at full depth — the part that actually compares each recorded signal against its fair comparison moments and writes down one permanent verdict per question that no later run may change, the most permanent machinery in the whole era. Full depth because the deeper checking lane has now caught a serious fault twice in this session that the lighter checks missed: iteration 3's over-confident surprise value, and this round's secretly-choosable start date, which the ordinary review and the routine test pass had both approved.

Three things must be settled inside that round rather than becoming rounds of their own: the old strategy-trade date bug (a missing time-stamp becomes a 1969 date and lumps unrelated trades together); damaged registry files currently vanish silently instead of being reported; and the registry's readiness number is a temporary estimate that J-06 must compute for real and supersede, never inherit.

Two small clean-ups ride along: remove the three unused imports the reviewer flagged, and pin the random-draw test to a fixed expected answer instead of asking the code under test what it expects.

One thing must not slip again: the browser walk of the old product did not run this round, so next round must run it and save a picture — a second skipped round would turn a safe carry-over into a real hole.

Still outstanding for a person, from iteration 2 and outside this project: the unrelated trendora backend on port 8255 has not been restarted. Approve building J-06 next at full depth; nothing needs a human unblock to start.

## Assumptions made

- iter-6 · goal-evaluator — Ambiguity: J-05's acceptance says a withdrawal after a post-boundary evaluation exists "is refused and the hypothesis folds as p=1"; the refusal half is fully testable today, but the "folds as p=1" half needs J-06's not-yet-built evaluation store and BH computation. We chose: scored J-05 passing on the refusal half alone, treating "folds as p=1" as a forward clause J-06 must carry as its own acceptance item, not inherit as already done. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: this iteration's Definition of Done requires the required-still-passing journeys (J-01–J-04, J-10's kept half) to "remain green," but the browser/replay lane self-skipped wholesale this run, leaving no results row — not even DEFERRED-BUDGET — for any of the five. We chose: held all five at their recorded statuses under evidence durability, after proving the code behind each is unchanged (zero frontend diff, no shipped route body touched) rather than assuming it; J-04's own module changed, so it was re-verified directly instead of carried. Reversible: yes
- iter-6 · developer — Ambiguity: the spec's definitional equality for `confirmation_start_boundary` doesn't say whether a caller-supplied override field is a real feature, but a required test case needs the payload to accept and refuse an at-or-before override, implying the field is caller-visible at all. We chose: the override field exists only as a defensive/adversarial-input test hook — a value at or before the honest boundary is refused, a later value is silently ignored (never honored), since the spec names no "delay the boundary" feature. Reversible: yes
- iter-6 · developer — Ambiguity: the Data Contract note "`null_spec_id: str|None` (None for `evidence_family='strategy'`)" could be read as requiring every playbook-family hypothesis to carry a null spec id, but the statistical spec defines Estimand B as a cell-vs-complement comparison with no null population at all. We chose: `null_spec_id` is required and validated only for Estimand A or C; for Estimand B it is forced to `None` regardless of what a payload supplies, weighting the substantive estimand definitions over a summary parenthetical that never claimed to be exhaustive. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: iteration 5's carried question asked whether null records should be filed under a real hypothesis id now that hypothesis ids exist, but neither the goal nor the statistical spec states whether null-record identity should change once hypotheses exist. We chose: keep null records keyed exactly as they shipped (by observation id + null-spec signature), with no hypothesis-id field added, since null anchors are a shared, hypothesis-independent measurement multiple hypotheses can legitimately reuse. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: J-05's steps require the registry to serve "per-hypothesis accrual," but the spec's precise "informative session" definition requires J-06's not-yet-built estimand engine to pair each occurrence against real matched-null anchors, which the registry can't compute without duplicating unbuilt logic. We chose: serve accrual as an honestly-labeled, cheaper proxy (`is_proxy: true`) — the count of distinct post-boundary session dates with at least one observation in the hypothesis's own cell — reusing existing evidence-pooling code rather than a second computation; J-06's real count becomes authoritative once it exists. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: J-04's acceptance names "hand-computed draws" including three specific cases, all met, but every shipped fixture gave the code four-or-fewer comparison moments to choose from, so the seeded random-selection step itself was never actually discriminated by any test. We chose: scored J-04 passing after verifying the selection independently (a genuine non-trivial subset, reproducible, never drawing the trigger bar, different for a different observation) rather than withholding the pass for the literal clause; the shipped test gap was carried as a binding rider on the next iteration instead of a blocker. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: the statistical spec says "the minimum attainable p (granularity) is served beside every p," but the exact-enumeration branch served a value the iteration-3/4-fixed method can never actually produce, and no human ruling was available before this iteration needed to build on the field. We chose: ruled for the field's own literal name ("minimum ATTAINABLE") over the spec's looser "granularity" gloss, changing the served value to the true floor; verified zero consumers exist yet so the fix needed no version bump. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: J-03's acceptance is "the oracle suite is green and IS the acceptance," and every clause is met, but the hard auditor left one finding open (a served field that over-promises how small a p-value the method can reach), and the goal text doesn't say whether an over-promising disclosure blocks an otherwise-passing journey. We chose: scored J-03 passing and carried the finding as a binding rider on J-04 rather than holding the journey a second iteration, since the defect was a secondary disclosure field consumed by nothing today. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-6.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-6-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-referee-iter-6-review.md |
| Browser QA | SKIPPED | reports/phase-goal-referee-iter-6-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-referee-iter-6-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-referee-iter-6-user-visible-changes.md |
| What to click | — | reports/phase-goal-referee-iter-6-what-to-click.md |
| UI surface map | — | reports/phase-goal-referee-iter-6-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-referee-iter-6-ui-test-plan.md |
| QA | PASS | reports/qa/goal-referee-iter-6-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-referee-iter-6-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-referee-iter-6-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-referee/iter-6/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |
