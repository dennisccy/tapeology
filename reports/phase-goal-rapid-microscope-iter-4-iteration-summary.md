# Iteration Summary — goal-rapid-microscope-iter-4

**Verdict:** ESCALATE
**Iteration type:** goal-full
**Date:** 2026-08-17
**Iteration:** 4

## In plain words

**What you can do now:** You can watch live and historical price charts on the Cockpit page, map price walls on the Structure page, check chart-pattern signals against those walls on the Desk page, and browse every trading idea the Referee has judged. A "Microscope Readiness" panel on the Desk page shows how much tick-by-tick market data is on hand. Behind the scenes, three research engines now work together — reading pressure inside each trading day, matching chart signals to that pressure data, and (new this round) automatically testing small trading ideas with a permanent, tamper-proof record of every result — though none show their results on a screen yet.

**What changed this time:** Nothing changed on any screen this round. Behind the scenes, the team built a new "Scout" that tests small trading ideas against the recorded tick data and keeps a permanent, tamper-evident log of every test, including failures — an independent check found and fixed four subtle problems with how that log protected itself. The team also fixed two small honesty gaps in the existing data-inventory numbers: a damaged data file no longer disappears from a count without a trace, and a placeholder "0" now clearly says "not counted yet" instead of implying a real zero.

**What's next:** Next, the team will build the "walk-forward engine" that decides which research results are trustworthy enough to count — under the same careful, slower review process, and this time making sure the screen-by-screen safety check actually runs.

## Headline

The Scout candidate screener and its tamper-evident trial ledger ship (J-04), audited and hardened.

## Direction

**Signal:** improving
**Why:** J-04 "The Scout and the ledger" moved from failing to passing this iteration, verified end to end by the evaluator (a live CLI run plus re-proving all four auditor-found fixes on running code), while J-01/J-02/J-03 were independently re-verified against the real store rather than carried. Three critical anti-goal faults surfaced during the audit (an undetectable ledger tail-truncation, an inflated variant count, and two horizon families screened under an anti-conservative null) but all were found and fixed before the iteration closed, so nothing broken shipped. The verdict is ESCALATE rather than CONTINUE because the browser-QA lane recorded a blanket skip — J-10's 13-step kept-product sentinel did not run at all — which the evaluator flagged as the primary, binding gap for next iteration.

**Trend (last 5 iters):**
- Newly passing this iter: J-04
- Newly passing in last 5 iters total: J-01, J-02, J-03, J-04
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: iter-2 — 2 critical (both caught and fixed in-run) + 1 minor (still open, timing-stamp ruling due); iter-3 — 1 minor (a corrupt playbook record, closed in iter-4); iter-4 — 2 critical anti-goal rules / 3 underlying faults (ledger tail-truncation, inflated variant count, and an anti-conservative screening null on shares/clock horizons — all caught and fixed in-run); none in iter-0 or iter-1
- Iters with no journey state change: 1 of last 5 (iter-1)

**Latest evaluator reasoning:** The Scout and its trial ledger were built and they work. I ran them myself, end to end, on a throwaway copy of the test data: every candidate that was tried got one permanent line in the record, with an honest reason for its death, and the count of "how many things we tried" behaves correctly. The independent checker found four real integrity faults that the code review and the test pass both missed, fixed all four, and I re-proved each fix against the running code. One thing did not happen: the browser check was skipped completely, so nobody looked at the four already-working parts of the product this iteration was told to re-check — including the 13-step whole-product safety walk.

## What was done

- Product changes: apps/backend/app/research/scout_ledger.py (new), apps/backend/app/research/scout.py (new), apps/backend/app/research/micro_routes.py, apps/backend/app/research/micro_join.py, apps/backend/app/research/micro_readiness.py, apps/backend/tests/test_scout_ledger.py (new), apps/backend/tests/test_scout.py (new), apps/backend/tests/test_micro_join.py, apps/backend/tests/test_micro_readiness.py; new routes GET /research/desk/micro/scout, POST/GET/POST-cancel /research/desk/micro/scout/compute, GET /research/desk/micro/scout/runs
- Built the Scout screening engine (`scout.py`): screens pre-registered candidates against tick data with a within-session block-permutation null, gives every candidate a closed-vocabulary decision (survive or one of six kill reasons), plus mandatory disclosures and an economic-relevance column carrying the frozen cost-proxy sentence verbatim.
- Built the hash-chained, tamper-evident candidate ledger (`scout_ledger.py`): one permanent row per trial including kills; `variants_tried` is a union-N denominator across grid versions.
- Wired three new backend endpoints plus a CLI entry point for the Scout — not yet rendered on any screen (J-08's scope).
- Ran a bounded 6-candidate fixture grid end to end through both the manager and the CLI; every candidate honestly reads `killed_insufficient_n` on the tiny fixture corpus.
- Fixed two honesty gaps in the corpus-readiness numbers: a corrupted playbook record now surfaces explicitly instead of vanishing; `band_touch_count` is now a typed "not enumerated" state instead of a bare `0`.
- Discovered and fixed an O(n²) performance defect that could hang indefinitely against the real corpus; the compute manager now completes in under a second on small/medium real data, though the full 18-dataset corpus still takes minutes.
- Independent audit found and fixed 4 IMPORTANT integrity faults the review and QA both missed: the served ledger never verified its own tamper chain, a truncated tail was undetectable, repeated identical runs inflated the served variant count and jammed the compute endpoint after 12 runs, and two horizon families were screened against an anti-conservative null — all four fixed and re-proven on live code.
- Verified 0 target journey(s) pass browser QA — the browser lane recorded a blanket SKIP this iteration; J-01/J-02/J-03's re-check and J-10's 13-step kept-product sentinel did not run.

## What's left

- Journey J-05 "The walk-forward engine — chronology, fences, and the diagnostic run" failing — `micro_accessor.py`/`walkforward.py` absent from disk; it's the next target.
- Journey J-06 "The recorder and the Vault — new tape, sealed at birth" failing — `tick_recorder.py`/`vault.py` absent from disk.
- Journey J-07 "Graduation — provenance in, nothing laundered out" failing — `micro_graduation.py` absent from disk.
- Journey J-08 "The surface and MCP v6 — the funnel is visible" failing — MCP tool list still 22 of the target 26; no Scout Ledger section on `/desk` yet.
- Journey J-09 "The pilot studies — three predeclared questions, honest answers" failing — no study family predeclared or ledgered yet.
- Journey J-10 "The kept product stands — traps armed, sentinel green" partial — trap suite now 8/22 (up from 4/22); the browser sentinel was NOT re-run this iteration and needs an actual pass next.
- Browser QA did not run at all this iteration — J-01/J-02/J-03's regression re-check and J-10's 13-step kept-product sentinel are unverified by screenshot this round; carried as binding next-iteration work.
- Two owner rulings now due together: the one-quote-early depletion timing stamp (open since iteration 2), and whether "variants tried" should also be counted per data-set as the written spec says (it currently isn't).
- The Scout's grouping key (`family_id`) omits the corpus term the spec's own constant names it by — an owner ruling is needed before J-06 adds more corpora, since re-keying would rewrite rows already on the ledger.
- The Microscope Readiness panel screenshot still shows iteration 2's small fixture corpus, not the real 12-symbol-day totals — a make-up capture is still owed.

## Next step

Build J-05 "The walk-forward engine" next, and run it as a full iteration so the independent checker is in the loop again — this is the part of the era that decides which results are allowed to count, and in this session the independent checker is the only step that has ever caught that kind of mistake (twice in iteration 2, four more times this iteration, all missed by review and testing).

Carry five small passenger items, none of which should become an iteration of its own: (1) actually run the browser check this time — re-check J-01/J-02/J-03 and run the 13-step whole-product safety walk (`journey-scripts/J-10.json`) unmodified, with screenshots saved, and an honest skip recorded only for journeys with no screen — nobody ran it this iteration; (2) two owner rulings are now due together before J-06 adds more recorded data: the one-quote-early timing stamp (unresolved since iteration 2), and whether the "variants tried" bucket should be counted per data-set as well as per feature family, since the written spec says it should and the code does not; (3) re-take the corpus-readiness photograph once the browser rig can show real tick data — the current picture is honest but shows the small test corpus, not the real 12 symbol-days; (4) before any of this reaches a screen (J-08), fix one kill message that currently reads "approximately None bps" and add the new numbers to the two guard lists that protect the page's wording and arithmetic; (5) watch the running time — the full grid already takes minutes on today's 18 files and the era's later steps grow that corpus a lot, so weigh a speed-focused pass before J-06 lands.

One sentence for the owner: approve building the walk-forward engine next as a full-depth run, and please answer the two questions in item 2 — a timing question and a counting question — because both get harder to change once more data is recorded.

## Assumptions made

- iter-4 · goal-evaluator — Ambiguity: goal.md's trap T-10 says every browser acceptance needs a screenshot (none ⇒ `unknown`, never `passing`), and this iteration's browser lane recorded a blanket skip with zero screenshots and the mandated regression set never run; the goal never says whether T-10 re-asserts itself every iteration even when nothing that journey renders has changed, or only governs the iteration a journey's acceptance is first proven. We chose: the first reading, aligned with the evidence-durability rail — kept J-01/J-02/J-03 passing and J-10 partial on their existing captures, after independently confirming no field this diff touches can reach a screen (empty frontend diff; the new fields appear nowhere in the app's source). Had any frontend file changed, the set would have been scored `unknown` instead. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: the prior iteration flagged the micro-observer depletion timing stamp as an owner ruling now due, since this is the first journey conditioning a result on it, but the goal never says whether this iteration's registered grid must include a candidate that depends on it or may simply avoid registering one until the ruling lands. We chose: this iteration's registered fixture grid excludes every candidate conditioned on that flagged signal; every other eligible feature family stays in scope. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the spec says one module is the sole legal reader of snapshot/ledger-input/vault data, but that module is itself a later journey's deliverable and this iteration comes first, so the goal doesn't say whether this iteration's join may read snapshot rows directly before that module exists. We chose: the join reads through a plain reader function co-located with the snapshot writer, on the era's still-exploratory legacy corpus only; the later journey is expected to re-point this read through its own accessor. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the spec defines "Outcome start" via a per-candidate "conditioning feature set" that doesn't exist until the Scout journey, so the goal doesn't define this term at the join layer. We chose: outcome start = the trigger's own timestamp directly, with every feature family's own availability flag kept intact; a candidate-specific outcome start is deferred to later journeys. Reversible: yes
- iter-3 · goal-decomposer — Ambiguity: the acceptance criteria require the joinable-corpus count served with its per-study breakdown, but the three pilot studies aren't predeclared until a later journey, so no study identifier exists yet to break the count down by. We chose: break the count down by the finest grouping the corpus already supports (signal type, then playbook setup) — the natural precursor to the eventual per-study view. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: no module in the product enumerates wall-touch instants yet, and defining what counts as a "touch" is later work, so the goal never says whether an unenumerated side may be served as a bare `0`. We chose: scored the journey passing on a touch count of `0` disclosed as "honestly zero" in the code and dev handoff (but not yet in the served payload) — recorded as a required fix-forward item, closed this iteration. Reversible: yes
- iter-3 · goal-evaluator — Ambiguity: a fresh readiness-panel screenshot came out blank while the product code under it changed, and the methodology doesn't say what to do when a fresh capture is itself defective. We chose: kept the journey passing with an evidence-makeup flag, citing the prior iteration's good screenshot instead, since the page code is byte-unchanged and a separate screenshot this run independently photographs the same served data. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: the acceptance criteria name literal real-corpus browser figures, but the mandated test rig can never safely point at the real dataset store this iteration, since a new write-capable route's derived-cache directory defaults to a sibling of the same store path. We chose: seed the rig's own throwaway root with committed tick fixtures, so the screenshot shows a real, non-fabricated corpus proving the same rendering path, while the literal real-corpus totals stay proven against the real store as already established. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: the acceptance criteria name specific real-corpus figures AND require the panel to render "those same served values," but the two aren't simultaneously observable while the test rig can't safely point at the real store. We chose: the rendering-fidelity reading — scored the journey passing on the endpoint proof from a prior iteration plus this iteration's screenshot of a real (if small) non-fabricated corpus, flagged evidence-makeup so a real-totals make-up photograph rides a later iteration as a passenger task, never a reason to rebuild the journey's code. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: the validation spec has no dedicated readiness section, so it never defines a minutes-to-session-equivalents conversion formula or a per-study floor (that lands eight iterations away). We chose: a standard conversion that reproduces the goal document's own stated figure, and every pilot study reads the same existing frozen geometry floor for now. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: the acceptance criteria combine real-corpus endpoint values with a browser screenshot of the same values, but the goal never says which channel proves which half, and the test rig could not serve any tick corpus that iteration. We chose: credited the endpoint half from evidence produced directly against the real store, refused to credit the browser half since the only screenshot was empty, and scored the journey `partial` — which blocks full goal achievement exactly as `failing` does. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: two journeys each state one combined acceptance line, but only part of each was verifiable at era open, and the goal doesn't say whether partial satisfaction counts as `failing` or `partial`. We chose: scored both `partial`, so the verified sub-checks are not re-done later; `partial` blocks full goal achievement exactly as `failing` does, so no gate is loosened. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-rapid-microscope-iter-4.md |
| Dev handoff | — | docs/handoffs/goal-rapid-microscope-iter-4-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-rapid-microscope-iter-4-review.md |
| Browser QA | SKIPPED | reports/phase-goal-rapid-microscope-iter-4-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-rapid-microscope-iter-4-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-rapid-microscope-iter-4-user-visible-changes.md |
| What to click | — | reports/phase-goal-rapid-microscope-iter-4-what-to-click.md |
| UI surface map | — | reports/phase-goal-rapid-microscope-iter-4-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-rapid-microscope-iter-4-ui-test-plan.md |
| QA | PASS | reports/qa/goal-rapid-microscope-iter-4-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-rapid-microscope-iter-4-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-rapid-microscope-iter-4-closure-verdict.md |
| Goal evaluation | ESCALATE | runs/goal-session-rapid-microscope/iter-4/eval.md |
| Journey history | — | runs/goal-session-rapid-microscope/state/journey-history.json |
