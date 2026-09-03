## iter-0 — goal-evaluator

**Ambiguity:** J-06's Acceptance is one long conjunction (pages unchanged + three era-open documents
exist + guard suite green + full suite green + fingerprint pinned). The merged results row records it
as `FAIL`, but the goal text does not say how to score a journey whose sub-checks split.
**We chose:** `partial` in journey-history (not `failing`), because the era-open and unchanged-pages
sub-checks are genuinely verified done and only the guard-test file is missing — matching the
iteration spec's own TC-6 prediction and the "only some assertion steps passed" definition of partial.
Neither status counts as passing, so no gate is loosened by this choice.
**Reversible:** yes

## iter-0 — goal-evaluator

**Ambiguity:** J-06 also requires the full backend suite recorded green. Browser QA's own re-run did
not finish and it honestly recorded `unknown`.
**We chose:** to treat the developer's and reviewer's independent full runs (3930 passed / 8 skipped /
0 failed) plus my own re-collection (3938 collected) as sufficient evidence that the foundation is
unchanged, while leaving J-06 `partial` on the missing guard module regardless — so this call cannot
have promoted any journey.
**Reversible:** yes

## iter-1 — goal-decomposer

**Ambiguity:** The Binding Execution Order's step 1 says the "builder" is built alongside "constants...
and hash laws", while step 2 separately names "the three time fields, `availability_basis`" and step 3
separately names the "descriptor, lifecycle and provenance" fields. It is not explicit whether
`build_tape_observation` should be a partial function this iteration (only the semantic/integrity fields)
or must already produce the complete v1 schema.
**We chose:** `build_tape_observation` produces the COMPLETE v1 schema this iteration — including the
pure-math `observed_at_utc`/`available_at_utc`/`availability_basis` projections and the verbatim
`lifecycle.*`/`source.*` pass-throughs — accepting already-resolved values as parameters, while the
machinery that makes those parameter VALUES genuinely correct (the manager's atomic settled read, the
real source/session descriptor, the route) is left to iterations 2/3/5. This reading is required for
Required Trap Coverage item 13 ("four-group partition covers every leaf path exactly once") to be
satisfiable this iteration at all, since the partition spans every field in the schema.
**Reversible:** yes — a later iteration could split the builder further without changing any field's
owner or semantics.

## iter-1 — goal-evaluator

**Ambiguity:** J-01's Acceptance is a conjunction — the served JSON at `/tape/SIM-BIDABS/observation`
AND `tests/test_tape_observation_projection.py` passing with its counter-example tests. The iter spec
itself left the scoring open ("Expect the evaluator to record J-01 as still `failing` or move it to
`partial`"). The goal text does not say how to score a journey when one conjunct is fully met and the
other is blocked by the goal's own required build order.
**We chose:** `partial` — steps 1, 4 and 5 are verified met (live Sim watch screenshot; 38/38 tests
passing on my own re-run; 5 `test_counterexample_*` tests present), while steps 2 and 3 are verified
unmet (the route 404s). This matches the "only some assertion steps passed" definition and the same
convention iter-0 applied to J-06. `partial` never counts toward GOAL_ACHIEVED, so no gate is loosened.
**Reversible:** yes
