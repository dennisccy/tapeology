# Iteration Summary — goal-hypothesis-foundry-iter-4

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-27
**Iteration:** 4

## In plain words

**What you can do now:** Open the Desk page and see that the new Hypothesis Foundry research chapter has begun, with the old chapter safely closed off. You can also open built-in practice examples showing the new chapter reaching the exact same accept/reject calls as Tapeology's older, already-trusted method, and other practice examples showing it can count how many versions of one research idea are allowed, lock the full idea list before any results are seen, and keep a permanent, tamper-evident record book of every trial.

**What changed this time:** The Desk page's Hypothesis Foundry section grew four new expandable panels — Sources/Compiler, Interpreter Fixtures, Freeze/Integrity, and Hermetic Oracles — each clearly labeled "practice data, not the real thing." For the first time a person can open these panels and see, in plain view, that the idea-reading and idea-locking machinery gives correct answers on built-in test cases, without reading any code.

**What's next:** Next, the team plans to start writing down the first real research ideas and lock them into a permanent list — the one step in this project that cannot be undone once it happens — while also fixing three small display gaps (a couple of missing details on the Sources panel, a missing pass/fail breakdown on the Oracles panel, and a temporary shortcut in the scoring code that needs removing).

## Headline

The one Foundry screen the last two verdicts asked for is now real

## Direction

**Signal:** improving
**Why:** J-03 and J-04 moved from partial to passing this iteration on evidence the evaluator personally reproduced — it independently re-ran `foundry_interpreter.interpreter_hermetic_fixture_view()` and `foundry_freeze.freeze_integrity_hermetic_fixture_view()` and got the exact reported numbers. J-01 stayed passing on a clean regression replay and nothing regressed. J-02 and J-05 remain partial for concretely named, disclosed gaps, and a new MINOR anti-goal violation (a frozen Scout scoring function temporarily patched inside the running backend) is unresolved and blocking — which is why the verdict escalates rather than simply continuing.

**Trend (last 5 iters):**
- Newly passing this iter: J-03, J-04
- Newly passing in last 5 iters total: J-01 (iter-2), J-03 (iter-4), J-04 (iter-4)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 1 MINOR, unresolved and blocking (iter-4); none in iter-0 through iter-3
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The one Foundry screen the last two verdicts asked for is now real, and I checked it myself rather than trusting the reports. Two journeys moved from partly done to done: J-03 "Generic interpretation preserves timing, direction and Scout decisions" and J-04 "Foundry owns the denominator, ledger, freeze barrier and lock". Two stay partly done for concrete, named reasons: J-02 "Sources compile into auditable CandidateSpecs" is missing three fields its own checklist asks the screen to show, and its last check needs a report that only a later stage can write; J-05 "The complete factory passes hermetic oracles" never shows the kill-type mapping its own checklist names.

## What was done

- Product changes: apps/backend/app/research/foundry_source_registry.py, apps/backend/app/research/foundry_compiler.py, apps/backend/app/research/foundry_interpreter.py, apps/backend/app/research/foundry_freeze.py, apps/backend/app/research/foundry_runner.py, apps/backend/app/research/foundry_hermetic_summary.py, apps/backend/app/research/micro_routes.py, apps/frontend/lib/types.ts, apps/frontend/app/desk/page.tsx
- Added four additive fixture-backed views (`sources_compiler`, `interpreter_fixtures`, `freeze_integrity`, `hermetic_oracles`) to `GET /research/desk/micro/foundry`, computed once at import time and cached — no per-request compute.
- Built new `foundry_hermetic_summary.py` module summarizing `test_foundry_hermetic_epoch.py`'s existing composite-suite results, with no second oracle implementation.
- Closed carried Repair 1: `SourceRecord.alternatives` fail-closed lint now rejects a nonexistent, wrong-family, or self-referential sibling id.
- Closed carried Repair 2: `foundry_runner.run_one_candidate`'s crash-path branch now also checks `manifest_hash` drift, not only `econ_floor_bps`.
- Added four new nested "Hermetic Fixture" subsections under `/desk` → Hypothesis Foundry, each with a banner visually distinct from the real era-open baseline block.
- Full backend suite grew to 3878 passed / 8 skipped / 0 failed (up from iter-3's 3842), `tsc --noEmit` reports 0 errors, and `config_fingerprint` stayed pinned at `08e471b10130e1e2`.
- Verified 5 target journeys pass browser QA (UT-J-01 through UT-J-05, 5/5 PASS).

## What's left

- Journey J-06 "One complete real epoch is generated and committed with zero Foundry outcome reads" — failing, not yet attempted; blocked by the goal's own required build order until this iteration's read surface was complete.
- Journey J-07 "Goal Mode deterministically exhausts the frozen real epoch without changing science" — failing, not yet attempted; same order constraint.
- Journey J-08 "The operator sees the final Foundry truth and all foundation rails still hold" — failing, not yet attempted; same order constraint.
- Journey J-02 "Ratified sources compile into auditable CandidateSpecs or typed blocks without outcome input" — partial: the Sources screen is missing three required fields (operative formula references, superseded fields, alias/lineage) and shows only one record of a two-variant family; its last check needs a committed audit report that only J-06 can produce.
- Journey J-05 "The complete factory passes hermetic known-null, planted-effect, leakage, and honest-stop oracles" — partial: the Hermetic Oracles screen never shows the kill-type mapping or best-of-N disclosure its own checklist requires, and its "outcome types present" line is built from a fixed label list rather than reading each row live.
- Unresolved MINOR anti-goal violation, blocking: `foundry_hermetic_summary.py` temporarily reassigns the frozen Scout scoring function `scout._two_sided_p` inside the running backend process and restores it afterward — must be fixed or owner-dispositioned before this era can close.

## Next step

Move to the goal's own next required stage: J-06 "One complete real epoch is generated and committed with zero Foundry outcome reads" — write the real source registry, run the fresh-context audit, and generate the candidate manifest, with no candidate results read anywhere. Carry four small, named repairs alongside it: put the three missing fields on the Sources screen (operative formula refs, superseded fields, alias/lineage) and show both records of the two-variant family; show the kill-type mapping and best-of-N disclosure on the Hermetic Oracles screen and make its "outcome types present" line read each row's real result instead of a fixed label list; remove the temporary change to the frozen scoring function from the running backend; and optionally add the manifest/source/spec/configuration identities to the freeze-record view. Run this at full depth. Two operator decisions remain: the one-hour iteration budget keeps forcing the lighter review pipeline (this iteration took over two hours), and the session's 60-iteration cap may still want raising to 80.

## Assumptions made

- iter-4 · goal-evaluator — Ambiguity: the status vocabulary doesn't say how to score a journey where every numbered step is demonstrated but a sub-clause inside one step is not, versus a journey where a whole numbered step has no on-screen home at all. We chose: one uniform rule — `passing` when every numbered step is personally verified on-screen (unrendered sub-clauses recorded as a gap), `partial` when any whole numbered step is absent — yielding J-03/J-04 passing and J-02/J-05 partial. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: two of J-03's five steps prove themselves only inside a collapsed drill-in widget, and the methodology doesn't say whether a collapsed-but-present drill-in counts as "shown." We chose: count them, after independently reproducing the exact values by re-running the interpreter myself — a collapsed disclosure is a real on-screen affordance the operator can open, not an absent one. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: production code temporarily reassigning the frozen Scout function `scout._two_sided_p` and restoring it in a `finally` sits between "nothing persists" and "a frozen module was mutated inside the serving process." We chose: log it as a MINOR, unresolved, blocking anti-goal finding rather than describe it only in prose — nothing this iteration's verdict rests on, but it must be fixed or owner-dispositioned before the era can close. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: J-02 step 5 bundles a buildable hermetic-immutability check with an "inspect the committed registry-audit report" check that depends on J-06, which doesn't exist yet. We chose: scope this iteration's Sources/Compiler view to the buildable half only, and disclose upfront that J-02 may still be scored partial for that reason alone — not a defect in this iteration's execution. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: J-04 step 4 names the real tracked path `docs/hypothesis-foundry/freeze-set.json` inside a step explicitly scoped to a fixture view, but no real epoch/manifest exists yet to produce that file. We chose: the fixture Freeze/Integrity view names that path only as the future real destination, clearly labelled fixture-scope, without writing or fabricating the real file. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: J-05's acceptance steps are worded as "run a hermetic epoch"/"confirm," not as on-screen inspections like J-02/J-03/J-04's, so it's unclear whether the no-screenshot cap that held those three at partial literally applies. We chose: score J-05 partial anyway — no screenshot exists for it, unit tests are never journey evidence, and the era's own blueprint expects an operator-visible rendering. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: the auditor fixed two IMPORTANT findings during the audit pass itself rather than sending work back to the developer, so the tests J-05 was scored on are partly the auditor's own work. We chose: count them, but only after independently opening both added tests and re-running the module myself rather than trusting the audit's own report. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the spec requires every source record to disclose its finite alternatives, but the spec document doesn't define what shape that field should take — sibling records alone could arguably already satisfy this with no dedicated field needed. We chose: add an explicit `alternatives` field naming the legal sibling(s) on each record, as additive disclosure on top of the existing family-key mechanism, not a replacement for it. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: it's unclear whether J-05's "withheld/sealed reads fail closed" step requires the runner to actually call through the real accessor this iteration, or only prove the contract against a hermetic stand-in. We chose: prove the fail-closed contract hermetically using the real, already-tested exception types, without wiring the runner into the real accessor's resolution path — that full wiring stays later-stage territory. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-02's five acceptance steps are all on-screen inspections of a view deliberately deferred this iteration, so none of its assertion steps have browser evidence, yet its backend compile rules are real and independently re-run. We chose: score J-02 partial, not failing, on the strength of that independent re-run, while recording that no UI step has evidence and that it needs an additional record field before it can ever pass. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: the era-open baseline artifact is genuine and the screenshot shows the panel behaving correctly for an empty store rather than misbehaving, which could arguably count as a capture defect rather than a product failure. We chose: do not excuse it that way — keep J-01 partial, since the asserted behavior has never actually been observed and closing the gap needs a developer fix, not a re-capture. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-hypothesis-foundry-iter-4.md |
| Dev handoff | — | docs/handoffs/goal-hypothesis-foundry-iter-4-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-hypothesis-foundry-iter-4-review.md |
| Browser QA | PASS | reports/phase-goal-hypothesis-foundry-iter-4-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-hypothesis-foundry/iter-4/eval.md |
| Journey history | — | runs/goal-session-hypothesis-foundry/state/journey-history.json |
