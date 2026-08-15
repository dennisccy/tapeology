# Iteration Summary — goal-referee-iter-7

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-15
**Iteration:** 7

## In plain words

**What you can do now:** You can still watch the live tape on the Cockpit, look up a stock's price map on the Structure page, and scan for chart setups on the Desk. Behind the scenes, the fact-checking system can now write down a research question, measure it against fair comparison data, and record one permanent, honest verdict for it. There is no screen for any of that yet, so there is nothing new to click.

**What changed this time:** No screen changed — this work was on the research engine behind the scenes. It gained its judge: a written-down question can now be weighed against fair comparison data and given one honest, permanent verdict — real evidence, no evidence, or too shaky to trust. The team also fixed two hidden bugs: trades were being silently mis-dated to 1969, and a damaged data file could vanish without a trace instead of showing a warning.

**What's next:** Next: build the first Referee screen where someone can pick and register a real research question, and close two small honesty gaps found this round.

## Headline

The judging machinery is real and it works.

## Direction

**Signal:** improving
**Why:** J-06 "Estimand engines + adjudication" moved failing to passing this iteration — its known-positive/known-null fixture round-trip, checkpoint immutability, and tampered-attestation refusal were all independently re-verified by the evaluator, and no journeys regressed. The verdict is ESCALATE rather than CONTINUE because this was planned as the deep full-depth pass and the engine demoted it to lean for budget reasons, and because the evaluator's own probe found two gaps in the now-permanent adjudication record (an unattested evaluation still writes a "corroborated" snapshot; a corrupted hypothesis file can vanish from the adjudications list) — so J-07 is recommended next at full depth with both fixes riding along.

**Trend (last 5 iters):**
- Newly passing this iter: J-06 "Estimand engines + adjudication"
- Newly passing in last 5 iters total: J-03 "The statistics core" (iter-4), J-04 "Matched nulls" (iter-5), J-05 "The registry" (iter-6), J-06 "Estimand engines + adjudication" (iter-7)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 1 critical (iter-6 backdateable-boundary hole; found and fixed within the same iteration, re-confirmed still closed at iter-7)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The judging machinery is real and it works. A written-down question can now be measured against its fair comparison moments and come back with one permanent answer that no later run can change. I checked this myself instead of believing the report: I ran the new test file (40 checks, all pass), read the two main round-trip checks line by line — they build real price bars, real recorded signals and real comparison records, then run the real code — and a made-up "there is something here" case comes back "corroborated" while a made-up "there is nothing here" case comes back "no evidence".

## What was done

- Product changes: apps/backend/app/research/referee_adjudicate.py, apps/backend/app/research/referee_null.py, apps/backend/app/research/referee_registry.py, apps/backend/app/research/referee_evidence.py, apps/backend/app/research/referee_routes.py, /research/desk/referee/evaluate, /research/desk/referee/evaluations, /research/desk/referee/evaluate/runs, /research/desk/referee/adjudications
- Built new module `referee_adjudicate.py`: estimand A/B/C pooling, evaluation as a recorded operator act, the single append-only confirmatory checkpoint with its family BH fold, the read-side adjudication fold, and a pure (unwired) `authorize_promotion` implementing all 6 refusal classes.
- Added the evaluation store, run-ledger, and adjudication snapshot store, mirroring the existing null-compute pattern (single-flight per hypothesis, cooperative cancel, dedup reuse, terminal-only ledger writes).
- Mounted 6 new routes on the existing referee router (no new router registration).
- Fixed Rider 1: trades with a missing `epoch_anchor` are now an honest, counted exclusion instead of silently mis-dated to 1969.
- Fixed Rider 2: the registry's GET response now surfaces all four stores' `integrity_errors` instead of discarding them.
- Fixed Rider 3: removed 3 dead imports and re-pinned a seeded random-draw test to a hand-computed literal instead of deriving its own expectation from the code under test.
- Verified J-06's fixture round-trip end-to-end (known-positive to `corroborated`, known-null to `no_evidence`) and directly re-verified J-01/J-02/J-04/J-05, whose own source files changed this run.
- Browser QA: J-10's kept-product regression walk re-checked PASS with a fresh dated screenshot, closing iteration 6's evidence hole; J-06 correctly SKIPPED (keyless, no browser-observable surface this iteration).

## What's left

- Journey J-07 "The starter family" failing — the first Referee UI screen (candidate shortlist, pick-and-confirm, real registration act) is not yet built.
- Journey J-08 "The strategy family + promotion interlock" failing — `authorize_promotion` exists but is not yet wired into `pnl_scan._promote`.
- Journey J-09 "The Referee on /desk + MCP contract v5" failing — no `/desk` Referee sections exist yet; MCP still serves exactly 20 tools, not 22.
- Journey J-10 "The kept product stands" still only partial — its era-end clauses (three Referee `/desk` sections, 22 MCP tools) remain structurally blocked on J-09.
- A failed oracle attestation still writes the hypothesis's one permanent adjudication snapshot as `corroborated` — the served fold correctly refuses (`confirmatory_output_refused: true`), but the stored record is wrong forever. Found by the evaluator's own probe; not yet fixed.
- A corrupted hypothesis record file silently disappears from `GET /research/desk/referee/adjudications` instead of surfacing in `integrity_errors` — the same gap class Rider 2 just closed for the registry GET.
- Documentation drift: `blueprint.md`'s registry Data Contract note still documents the old 4-key GET shape after Rider 2 added a 5th key (`integrity_errors`); the dev handoff's claim that it "is now five keys — updated as part of this fix" is false.
- `authorize_promotion`'s refusal-class partition (spec §8) is a developer interpretation call, logged to `state/assumptions.md`; J-08 should review it before minting any real certificates.
- The unrelated trendora backend on port 8255, stopped as a side effect of an earlier iteration's `pkill` cleanup, still needs a person to restart it — outstanding since iteration 2.

## Next step

Build J-07 "The starter family" next, on its own, at full depth. This is the first Referee screen a person can actually use: the shortlist of candidate questions with live readiness numbers, a pick-and-confirm step, and the real act of writing a question down, which stamps a start date that can never be edited afterwards. Full depth because it is the first Referee page (so it needs real browser pictures) and because the act it performs is permanent.

Three fixes must ride inside that round rather than becoming a round of their own, all found by this evaluation rather than by the pipeline: (1) when the maths self-check fails, do not write the question's one permanent answer at all — record it as still pending, with an honest reason; (2) a damaged question file must be reported on the answers page, not silently disappear — the same fix just applied to the registry page; (3) correct two paperwork slips — the shared design note still describes the registry answer as having four parts when it now has five, and the builder's own write-up claims it was already updated when it was not.

For a person: approve building J-07 "The starter family" next, at full depth, with those three fixes carried along. Nothing needs a human unblock to start. Still outstanding for a person and outside this project, carried from iteration 2: the unrelated trendora backend on port 8255 has not been restarted.

## Assumptions made

- iter-7 · goal-evaluator — Ambiguity: The anti-goal "No confirmatory output without a verified oracle attestation" reads as a rule about the served fold, but a probe with a deliberately broken attestation showed the write side is not gated at all: the run still recorded `role: "checkpoint"` and appended a permanent snapshot with `verdict: "corroborated"`; only the served fold refuses (`confirmatory_output_refused: true`, `insufficient_sample`). The goal text doesn't say whether writing an unattested confirmatory verdict into an append-only record counts as "confirmatory output." We chose: Read the anti-goal as scoped to served output, so this is not a critical violation and the verdict is not REGRESSION — recorded instead as a named must-fix-next weakness. Reversible: yes.
- iter-7 · developer — Ambiguity: Spec §3.6 withholds confirmatory fields (T/permutation_p) below the registered floors but doesn't say whether descriptive companions (ci_occurrence/ci_cluster/sign_flip_p/equal_weight_T/entry-basis) are also withheld pre-eligibility, or computed whenever there's pooled data. We chose: Gated T/permutation_p/permutation_enumeration/min_attainable_p strictly on `confirmatory_eligible`; left descriptive companions computed whenever there's pooled data, since spec §3.5/§3.6 call them "descriptive companions... never a decision rule." Reversible: yes.
- iter-7 · developer — Ambiguity: Spec §5 lists `exploratory` ("basis not registered") as a live-fold verdict token, but `adjudications_response()` only ever folds hypotheses already in the registry, so none it serves could honestly be "basis not registered." We chose: Treated `exploratory` as a documented, currently-unreachable enum member — the same treatment iteration 7's `killed` drop already uses. Reversible: yes.
- iter-7 · developer — Ambiguity: Spec §4.3's entry-basis sensitivity is framed entirely around an occurrence-vs-matched-null comparison, which only makes sense for estimand A/C; estimand B (a cell-vs-complement comparison of two real occurrence groups) has no stated entry-basis treatment. We chose: `entry_basis_T`/`entry_basis_sign_flip` are computed for A/C only and honestly `None` on every B evaluation record, rather than inventing an unstated B-specific treatment. Reversible: yes.
- iter-7 · developer — Ambiguity: Spec §5's fragile rule names a `sign_flip` trigger from §3.5, which lists the session-level `sign_flip_result` first — the bare token could be misread as naming that function's own output. We chose: `sign_flip` = the equal-session-weight sensitivity's own T changing sign, not `sign_flip_result`'s output, because `sign_flip_result` computes the identical T as the primary test and structurally can never differ in sign. Reversible: yes.
- iter-7 · developer — Ambiguity: Spec §8 names all six `authorize_promotion` refusal classes but bundles several under one parenthetical, and TC-27 requires a `config_fingerprint` mismatch to fold specifically to `stale`, so the six tokens' partition wasn't fully disambiguated by the prose alone. We chose: malformed_unverifiable → no_certificate → wrong_candidate → stale → mismatched_datasets → failed_gates → authorized, in that priority order — satisfying TC-26/27/28 literally while giving each class its own non-overlapping trigger. Reversible: yes.
- iter-7 · goal-decomposer — Ambiguity: J-06's Acceptance requires a tampered attestation to "fold to the refusal state," but the verdict vocabulary's nine tokens name no distinct "attestation-refusal state." We chose: A dedicated `confirmatory_output_refused: bool` + `refusal_reason: str|None` pair that forces the served verdict to the most conservative already-named token (`insufficient_sample`), rather than inventing a tenth verdict token. Reversible: yes.
- iter-7 · goal-decomposer — Ambiguity: Spec §5 lists a `killed` verdict token ("a registered kill condition met") but defines no kill-condition mechanism anywhere — no Hypothesis field, no step, no trigger rule. We chose: Dropped `killed` from this iteration's built verdict set entirely; no code path computes or returns it, following "vagueness is a drop, never an improvisation." Reversible: yes.
- iter-6 · goal-evaluator — Ambiguity: J-05's Acceptance ends "a withdrawal after a post-boundary evaluation exists is refused and the hypothesis folds as p=1," but the p=1 fold is a BH-fold behavior that structurally cannot exist until J-06 builds the evaluation records — no evaluation store existed this iteration. We chose: Scored J-05 `passing` on the refusal half alone, treating "folds as p=1" as a forward clause J-06 owns. Reversible: yes.
- iter-6 · goal-evaluator — Ambiguity: This iteration's Definition of Done requires several journeys to "remain green — deterministic replay + LLM fallback," but the browser/replay lane self-skipped wholesale on `Frontend Present: no`, leaving no results row — not even DEFERRED-BUDGET — for any of them. The goal text doesn't say whether an un-run required-still-passing lane voids those journeys' recorded status. We chose: Held all five at their recorded statuses under evidence durability, after proving the code behind each was unchanged, or re-verifying directly anything that had changed. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-7.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-7-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-referee-iter-7-review.md |
| Browser QA | PASS | reports/phase-goal-referee-iter-7-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-referee/iter-7/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |
