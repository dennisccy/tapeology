## iter-0 — goal-evaluator

**Ambiguity:** REL-14 says a journey named in `browser-infra.json` with no fresh screenshot scores
`partial` + `pending_infra`, but forbids `failing` only on infra absence *alone*. All 8 journeys
were named in the token, yet 7 of them have deterministic, evaluator-reproduced proof that their
surfaces do not exist at all (no `docs/hypothesis-foundry/`, no foundry module/route/test, no
desk panel).
**We chose:** score J-02..J-08 `failing` and J-01 `partial` on that independent evidence, and set
`pending_infra` on none of them — a verify-only make-up ride over surfaces that do not exist would
waste an iteration and would push the token to `attempts: 2`, mechanically triggering STALLED for
a blocker that is a one-line in-repo fixture fix. The infra failure is carried as the top active
blocker instead.
**Reversible:** yes

## iter-1 — goal-decomposer

**Ambiguity:** `docs/goal.md` Binding Execution Order step 2 ("Foundry methodology + source
registry + CandidateSpec. No real manifest yet.") does not say whether "first source records"
means beginning to author the REAL 11 required source objects (§1.1/§1.2) or building the compile
MACHINERY proven on synthetic fixtures — and J-02's own acceptance steps 1-2 literally name a
"Sources/Compiler **fixture** view" over 7 synthetic taxonomy examples, not the real objects.
**We chose:** iter-1 builds the compile-rule MACHINERY (owner meta-policy, natural-boundary law,
exact-quote lint, CandidateSpec schema/hash) and proves it on the 7 hermetic fixture source types
J-02 step 2 names; authoring the REAL 11 required-source-object registry content is left to J-06
(which J-02's own step 5 partially depends on anyway, since it inspects "the committed
fresh-context registry-audit report" that only J-06 commits).
**Reversible:** yes

**Ambiguity:** nothing in the Foundry Constitution's scientific-integrity rules forbids building
the J-02 "Sources/Compiler fixture view" UI early (it renders only synthetic fixture data, no real
outcome), so the UI could technically ship in iter-1 alongside the compiler machinery rather than
waiting for the consolidated read-surface step.
**We chose:** defer ALL Foundry subsection UI (Sources/Compiler included) to the single
consolidated read-surface iteration named in Binding Execution Order step 5, which arrives after
the interpreter/family/freeze machinery (step 3) and hermetic oracles (step 4) exist — building one
comprehensive read surface once, instead of extending a partial UI three separate times across
iter-1/2/3, and matching the goal's own explicit staging. iter-1 ships only J-01's panel header
(era identity + era-open baseline), which is itself required by J-01's own acceptance and cannot
wait.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** J-02's five acceptance steps are all on-screen inspections of a Sources/Compiler
view, and that view was deliberately deferred by the iteration spec — so literally zero of its
assertion steps have browser evidence, yet its backend compile rules exist and were independently
re-run by the reviewer (40/40, TC-3..TC-12). The status vocabulary ("partial = only some assertion
steps passed") does not say how to score a journey whose substance is proven at a layer its own
steps never name.
**We chose:** score J-02 `partial`, not `failing`, on the reviewer's independent test re-run, while
recording in journey-history that no UI step has evidence and that J-02 additionally cannot pass
until `SourceRecord` gains the `alternatives` field its step 3 requires. Unit tests are explicitly
never journey evidence, so this can never support `passing`.
**Reversible:** yes

**Ambiguity:** Methodology A.7 (`capture defect ≠ product failure`) could arguably cover J-01 step
5: the era-open baseline artifact is genuine (I recomputed all six Referee hashes and they match),
and the screenshot shows the panel behaving correctly for an EMPTY store rather than misbehaving —
the data simply is not visible to the scoped QA rig.
**We chose:** do NOT apply `evidence_makeup`, and keep J-01 `partial`. The asserted behaviour
(baseline block renders the recorded values) has never been observed by anyone but the developer,
and closing the gap needs a rig launch/provisioning change by a developer rather than a re-capture,
so an `evidence` depth iteration could not fix it.
**Reversible:** yes
