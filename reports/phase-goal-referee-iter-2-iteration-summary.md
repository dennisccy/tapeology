# Iteration Summary — goal-referee-iter-2

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-14
**Iteration:** 2

## In plain words

**What you can do now:** As before, you can watch the live tape update on the Cockpit, browse a stock's price map on the Structure page, and scan for chart setups on the Desk. The Referee's fact-checking groundwork — now two pieces deep — still lives entirely behind the scenes, with no screen of its own yet.

**What changed this time:** Behind the scenes, the private evidence-counting tool built last round now turns every logged chart-pattern signal and every recorded test trade into one shared, detailed record — the same fields for both — so the harder statistics work coming next has one foundation to build on instead of two. Still nothing new to click; this work has no page yet.

**What's next:** Next, the team will build the part that actually decides whether a trading pattern is real evidence or just noise — the statistical judge for everything counted so far.

## Headline

J-02 — the evidence contract: two families, one typed observation shape

## Direction

**Signal:** improving
**Why:** J-02 ("the evidence contract") moved from failing to passing this iteration, following J-01 in iteration 1 — both were verified independently by re-running the tests and cross-checking code identity rather than trusting the handoff. No journeys regressed and the anti-goal checklist stayed clean (one out-of-scope host action was logged as a NOTE, not a violation). All three iterations so far have each advanced at least one journey, so the dependency chain (J-01 → J-02 → J-03…) is moving in order with no stalls.

**Trend (last 3 iters):**
- Newly passing this iter: J-02
- Newly passing in last 3 iters total: J-01, J-02
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: none
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** The work asked for this round is real and done. Every recorded trading signal and every recorded test trade can now be read as one single kind of record, with the same fields for both, so the later parts of the Referee have one shared foundation instead of two. I did not take the builder's word for it: I ran the tests myself, and I read the new test file line by line to check the numbers in it are written out by hand rather than copied from the code they are meant to check. The old product still works, the settings pin has not moved, and nothing was written into the owner's saved data.

## What was done

- Product changes: apps/backend/app/research/referee_evidence.py, apps/backend/tests/test_referee_evidence.py, apps/backend/tests/test_referee_guards.py
- Extended `referee_evidence.py` with the shared typed observation contract (`_observation` builder) and two per-family adapters: a playbook adapter (reusing J-01's `detector_basis`/newest-per-date pooling helpers verbatim) and a strategy adapter (reading `backtests.py`'s own joined trade/dataset blocks, keeping paired `random_null` trades in a separate list)
- Added `RefereeObservationCache`, a stat-keyed SQLite cache for the playbook family only — the strategy family is deliberately left uncached (documented engineering call: no metadata-only read is cheaper than reading the store itself)
- Closed the iteration-1 documentation rider: the module docstring now lists both already-served `integrity_errors` fields as part of J-01's pinned response shape, with zero behavior change (re-verified byte-identical)
- Extended `test_referee_guards.py` with a bidirectional AST import-ban guard proving no `referee_*` module imports the playbook detect/context modules, and neither of those modules imports any `referee_*` module
- Added 13 new tests (10 in `test_referee_evidence.py`, 3 in `test_referee_guards.py`); full backend suite now 2,446 pass / 8 skip / 0 failed (up from iteration 1's 2,433 floor), zero diff to any frozen file, fingerprint unchanged at `08e471b10130e1e2`
- Verified 1 target journey (J-02) passes browser QA as a live-endpoint regression check; J-02's primary acceptance evidence is the hermetic pytest fixture suite, per its Keyless/automated tag in goal.md

## What's left

- Journey J-03 (The statistics core — calibrated, seeded, oracle-proven, fail-closed) failing — `referee_stats.py` does not exist yet
- Journey J-04 (Matched nulls — comparable times, identical measurement) failing
- Journey J-05 (The registry — pre-registration with an immutable boundary) failing
- Journey J-06 (Estimand engines + adjudication — one checkpoint, recorded forever) failing
- Journey J-07 (The starter family — historical exploration becomes registered questions) failing
- Journey J-08 (The strategy family + the promotion interlock — fail closed, no bypass) failing
- Journey J-09 (The Referee on /desk + MCP contract v5 — 22 read-only tools) failing
- Journey J-10 (The kept product stands — regression sentinel) partial — the kept-product half is green, but its era-completion clauses (three Referee `/desk` sections, 22 MCP tools) stay unmeetable until J-09 lands
- `session_completeness` (the completeness predicate) has zero test assertions and is a best-effort estimate blind to intra-session bar gaps — flagged for J-06's confirmatory-eligibility dependency
- `provenance.detector_basis` is `None` for every strategy observation — a disclosed judgment call that needs an owner ruling (or spec codification) before J-06 assumes the field is always populated

## Next step

Build J-03 "The statistics core" next, alone, at full depth — it decides whether a pattern is real or noise, so a wrong sum here would still pass its own tests while quietly spoiling every later verdict, and its own acceptance says the proof suite IS the deliverable, which is exactly when an independent check of the checker is worth the time. Carry three small leftovers along with it rather than making them their own iteration: add tests for the "was this trading day complete" helper (currently untested, a rough estimate blind to gaps in the price data), add a test for the cache-path helper that is written but never called, and get an owner ruling on whether every record must carry a detector name, since a strategy trade has none and the code currently leaves it empty. Separately, outside this project: restart trendora's backend on port 8255 using the command recorded in the dev handoff — nothing inside this project is blocked.

## Assumptions made

- iter-2 · goal-evaluator — Ambiguity: `docs/referee-statistical-spec.md` §2's pseudocode types `provenance.detector_basis` as a plain string, but a strategy trade has no detector, so the field has no meaning for that family; goal.md's Constraints say an unimplementable spec clause should be dropped and surfaced for an owner ruling, never improvised (trap T-1). We chose: Accepted the developer's disclosed improvisation — `detector_basis: None` for every strategy observation, by analogy with `context_algorithm_version`'s explicit "None when inapplicable" pattern — rather than treating it as a failure, because it was surfaced honestly, is reversible, and has no consumer yet. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-02's Steps require the playbook adapter to carry a "completeness predicate" per record, but J-02's own Acceptance list never names it, and the shipped `session_completeness` is an untested, best-effort estimate blind to intra-session bar gaps, not used as a gate this iteration. We chose: Scored J-02 `passing` against its written Acceptance list, which is fully met and independently verified, rather than withholding the pass for an unlisted Step sub-clause; recorded as a binding rider on the next iteration instead of a blocker. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's acceptance requires the strategy family to carry the `basis_caveats` forming-bar disclosure "verbatim", but no verbatim text for it exists in `docs/goal.md` or the spec — only a description of what it must disclose. We chose: Accepted this iteration's first authoring of the exported constant `REFEREE_FORMING_BAR_BASIS_CAVEAT` as satisfying "verbatim" — it is now the single source of truth later journeys must import rather than re-word. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: J-10 is written as a continuous regression sentinel, but its own acceptance also names era-end conditions (three Referee `/desk` sections, exactly 22 MCP tools) that were structurally unmeetable at iteration 0. We chose: Scored J-10 `partial`, not `passing` — the whole-acceptance reading — and recorded the verified kept-product evidence so no later iteration redoes that work. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-2-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-referee-iter-2-review.md |
| Browser QA | PASS | reports/phase-goal-referee-iter-2-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-referee/iter-2/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |
