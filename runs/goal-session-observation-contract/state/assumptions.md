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

## iter-2 — goal-decomposer

**Ambiguity:** Binding Execution Order step 2 names `get_observation_source` as J-02's deliverable, but
Key Capability 3 in `docs/goal.md` describes its return as carrying "the settled `EngineSnapshot`, its
source/session descriptor, its settled wall-clock time and the engine's `end_reason`" — and step 3
separately owns "Descriptor, lifecycle and provenance. Source/session descriptor...". It is not explicit
whether `get_observation_source` must return the FULL descriptor-bearing shape this iteration or may
return a narrower shape that iteration 3 extends.
**We chose:** `get_observation_source(ticker)` is introduced this iteration returning only what the
atomic settled pair itself carries — the settled snapshot, `settled_at_utc`, and `end_reason` — with the
source/session descriptor fields (mode, scenario, window, session id, session start, data feed) added
onto the SAME method by iteration 3 without re-reading the pair. This keeps iteration 2's change set to
`watch_manager.py` plus one test file, matching the evaluator's own next-step wording ("the watch
manager's single atomic read of the settled pair, the three time fields, `availability_basis`") which
names none of the descriptor fields.
**Reversible:** yes — iteration 3 extends the same method's return value; no field owner or semantic
changes.

## iter-3 — goal-decomposer

**Ambiguity:** Key Capability 4 lists `profile_id` among the manager-owned provenance fields "recorded
at watch creation" alongside mode/scenario/window/session id/session start, but engine_identity is a
route-time projection (Constitution §1) and no live/replay watch path in this repo currently supports
profile selection (`profile_id` is used only by an explicit offline backtest run). It is not explicit
whether the per-ticker descriptor this iteration builds must itself store `profile_id`, or whether that
field can simply be a literal `PROFILE_DEFAULT` the iteration-5 route supplies inline at read time.
**We chose:** store `profile_id = PROFILE_DEFAULT` as a constant field of the SAME per-ticker descriptor
recorded at watch creation (alongside `source_mode`/`data_feed`/window/session fields), matching Key
Capability 4's literal wording, even though its value never varies for any watch built by this
iteration. This keeps `get_observation_source`'s return the single place iteration 5 reads every
descriptor field from, rather than splitting provenance across two call sites.
**Reversible:** yes — a future profile-selectable watch path would only need to set a non-default value
at the same recording site; no consumer of `get_observation_source` needs to change shape.

## iter-3 — goal-decomposer

**Ambiguity:** Required Trap Coverage item 31 ("no actionability field or token") is listed under both
J-03 and J-06, but the reusable copy-discipline/compound-identifier-ban guard module
(`test_tape_observation_guards.py`) is explicitly Binding Execution Order step 6 (iteration 6). It is
not explicit whether J-03's own test module must build a second, independent scan this iteration or may
defer the check entirely to iteration 6.
**We chose:** J-03's own test module (`test_tape_observation_lifecycle_feed.py`) ships a SCOPED grep
over one fully-built artifact dict for the same fixed token list Constitution's era-specific anti-goals
name, satisfying J-03's own acceptance step now; the general-purpose, lexicon-driven, non-vacuous guard
(`find_violations` over the module/tests/served-artifact with comment/docstring stripping and a `SELF`
exclusion) remains iteration 6's own module, built once, not duplicated.
**Reversible:** yes — the scoped J-03 check and the general iteration-6 guard test different things
(one artifact instance vs. every module/test/served surface) and can coexist without a rename.

## iter-3 — goal-evaluator

**Ambiguity:** J-03's literal Steps 1-5 are browser steps that read fields out of the served JSON at
`/tape/SIM-BIDABS/observation`. That route does not exist until iteration 5, so browser-qa scored its
single row `UT-J-03` as **PASS on a narrowed "regression-smoke" scope** (Watch → Pause → Resume → Stop →
re-Watch on `/`, plus the route answering 404 throughout) rather than on the journey's literal steps. The
goal text does not say how to score a results row whose scope is deliberately narrower than the journey.
**We chose:** to accept that row as evidence only for the browser sub-steps it actually executed, and to
treat every JSON-field assertion in Steps 1-5 as unmet — so J-03 becomes `partial` (its deterministic
half verified by my own 30/30 run of `tests/test_tape_observation_lifecycle_feed.py`, its served half
verified absent by my own grep of `apps/backend/app/main.py`), never `passing`. Same convention already
applied to J-01 (iter-1) and J-02 (iter-2). `partial` never counts toward GOAL_ACHIEVED, so no gate is
loosened.
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** Only one screenshot was captured for a five-step browser sequence
(`UT-J-03-result.png`, the final re-watched-live state). The intermediate `paused` and post-Stop idle
states are described in prose but not independently captured. It is not stated whether that counts as a
capture defect (`evidence_makeup`) or simply as incomplete journey evidence.
**We chose:** NOT to set `evidence_makeup: true`. J-03 is `partial` for a substantive reason (the route
is absent), and its full browser evidence must be re-taken at iteration 5 anyway once the JSON
assertions become checkable — scheduling a make-up capture now would add noise without adding proof.
The gap is recorded in `iter-3/eval.md` and folded into the iteration-5 next-step instead.
**Reversible:** yes
