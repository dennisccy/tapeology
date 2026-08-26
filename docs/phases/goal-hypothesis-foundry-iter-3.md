# Goal Iteration 3 — hermetic "complete factory" oracle suite (J-05) + two carried machinery repairs

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** hypothesis-foundry
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior evaluator verdict was `ESCALATE` (mandatory, no exceptions; also
  independently satisfies trigger 1: the composite hermetic oracle epoch exercises cross-module
  interactions across all five already-built `foundry_*.py` modules together — compiler → interpreter →
  family → freeze/ledger → runner — under every outcome type at once, which no single module's own
  existing test file covers).
- **Frontend Present:** no
- **Target journeys:** J-05, J-02, J-04
- **Required-still-passing journeys:** J-01 (the only `passing` Foundry journey; golden replay script
  exists at `runs/goal-session-hypothesis-foundry/journey-scripts/J-01.json`). Per the "widen after
  ESCALATE" rule this already covers "all currently passing journeys" since J-01 is the only one — no
  further widening is possible until more journeys reach `passing`. Do-not-regress items beyond J-01:
  the full backend suite baseline (iter-2: 3825 passed / 8 skipped / 0 failed) and `tsc --noEmit`,
  both covered by DEFINITION OF DONE, not by journey replay.
- **Anti-goal reminders:**
  - "No case-by-case scientific owner prompt during the run. Unresolved science blocks and execution
    continues unless a core integrity defect requires a halt."
  - "No source record, threshold, direction, family partition, or CandidateSpec chosen because of
    effect, p-value, sample density, or prior Scout outcome."
  - "No family-specific post-freeze extractor/evaluator path for one real candidate. Real membership
    is interpreted generically from CandidateSpec."
  - "No second Foundry statistical decision rail."
  - "No Foundry trial registered into the Scout ledger this era; the Foundry trial ledger is the
    canonical record and must carry the complete Scout screen payload plus both denominator contexts
    where defined."
  - "No exploratory read of a sealed shard; no Vault secret in repo/log/payload/screenshot."
  - "Evidence classes never mix; `historical_exposed_diagnostic` rows never pool with
    `historical_oos`/`live_confirmatory`."
  - "The accessor/evidence-control seam remains the only legal market-data door for Foundry real
    diagnostics."
  - "**No lookahead.** Every value is computed only from information legally available at its
    declared time; deferred constructs cannot be served before resolution."
  - "**Single source of truth.** Every shared scientific value has one canonical backend owner;
    REST/UI/MCP never independently recompute it."
  - "**Deterministic and seeded.** Randomized statistical draws use existing named deterministic
    streams; no wall-clock/unseeded randomness changes research results."
  - "No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a journey."
  - "No browser proof based on fabricated fixture state when a journey claims to show real final
    state; fixture and real views must be visibly distinguished."
  - "A real candidate outcome read before step 7 is a critical anti-goal violation."

## GOAL

Prove the entire five-module Foundry machinery (compiler → interpreter → family → freeze/ledger →
runner) hermetically, in one composite "complete factory" epoch that contains every possible outcome
type at once plus all-blocked, all-killed, multi-survivor, large-scale-checkpoint/resume, and
protected-data-trip fixtures — Binding Execution Order step 4 — while closing the two small,
already-identified integrity/data gaps the last review found in the already-shipped machinery.

## BACKGROUND

`iter-2/eval.md` verdict was `ESCALATE`: the spec-declared `full` depth was demoted to `lean` by the
deterministic budget arbiter (`engine.log 21:47:43`), so the era's linchpin machinery — interpreter,
family, freeze, ledger, runner, including the byte-identical Scout-equivalence oracle — shipped with
no auditor pass. Per this agent's own binding rule ("If the prior evaluator log emitted `ESCALATE`,
you MUST set depth to `full` for this iteration") this iteration runs `full`, matching the evaluator's
own explicit instruction: "Run this iteration with the deeper review pipeline; a recommendation alone
was already overridden once." `iter-2/coherence.md` was `COHERENCE-PASS`, so this is new scope, not a
consolidation pass.

The evaluator's next-step recommendation is followed verbatim: "Build the hermetic proof suite next —
one practice run containing every possible outcome at once, plus an all-blocked run, an all-killed
run, and the tests that must fail shut when protected data is touched. Carry two small repairs in the
same iteration: make the restart check refuse a candidate whose inputs have changed, and add the two
record fields the written method document already promises ('alternatives' and a source fingerprint)."
This is exactly Binding Execution Order step 4 ("Hermetic oracles and performance/checkpoint tests. No
real candidate outcomes."), the only legal next stage — step 3 (interpreter/family/freeze/ledger/
runner) shipped in iter-2 and is carried in `state/iteration-state.md`'s "Do not redo" list; steps 6-8
(real epoch, freeze commit, exhaust) stay illegal until steps 4-5 are proven.

Two carried small repairs ride in the same iteration, per the evaluator's instruction and the rubric's
"several trivial [fixes] alongside one risky journey" allowance — neither is itself a second risky body
of work, both are targeted closures inside already-shipped modules:

1. **Resume-identity hole** (`foundry_runner.py:89`, `run_one_candidate`'s already-terminal fast path)
   — confirmed still present by reading the current file: it returns the cached ledger row without
   re-verifying `manifest_hash`/`econ_floor` against the caller's current inputs, unlike the sibling
   intent-without-terminal branch three lines below it, which already raises
   `FoundryResumeIdentityMismatch` on drift. Flagged by the reviewer and seconded by the coherence
   auditor in iter-2; carried in `iteration-state.md`'s active blockers, "close before J-06/J-07."
2. **`SourceRecord` missing §1.4 `alternatives`/`source_hash` fields** — confirmed still absent by
   reading `foundry_source_registry.py:159`'s dataclass. `docs/hypothesis-foundry-spec.md` §1.4 already
   documents `source_hash = sha256(source_excerpt)` precisely (its own field table), so that part is
   unambiguous. `alternatives` is not yet defined at the implementation-spec level (`goal.md` §1.4 only
   says "every finite alternative the compiler is allowed to enumerate"); this iteration's own reading
   of that gap is logged in `state/assumptions.md`. Carried since iter-1's own review; hard prerequisite
   before J-06 authors the real 11 required source objects.

`lessons.md` iter-2's first lesson applies directly to how this iteration's depth was decided: "An
evaluator ESCALATE verdict, not a depth *recommendation*, is the lever that actually forces the full
pipeline" — reflected in the binding `full` depth above, not merely a spec-side `Depth: full` line.

No UI ships this iteration, matching the J-02/J-03/J-04 precedent set in iter-1/iter-2: all Foundry
subsection UI (including any future "Hermetic Oracles" fixture view) stays deferred to the single
consolidated read-surface iteration named in Binding Execution Order step 5. J-05's own acceptance
steps are hermetic-fixture run/inspect steps with no browser surface named, so — like J-02/J-03/J-04
before it — its substance is fully provable this iteration but it is expected to land at `partial`,
not `passing`, on the same "unit tests are never journey evidence, but an independently-reviewer-rerun
hermetic proof earns `partial`" precedent the evaluator has applied twice already (iter-1 for J-02,
iter-2 for J-03/J-04).

## IN SCOPE

### Backend

- [ ] New hermetic test module `apps/backend/tests/test_foundry_hermetic_epoch.py`: one composite
      "complete factory" epoch fixture run end-to-end through the real production
      compiler → interpreter → family → freeze/ledger → runner path, containing simultaneously: a
      source that stays `BLOCKED_*`, one `EXCLUDED_*`, one `ALIASED_*`, and `FROZEN_READY` variants
      that terminate as `EVALUATED_INSUFFICIENT` (`killed_insufficient_n`), `EVALUATED_KILLED` via
      each of `killed_null`/`killed_direction`/`killed_concentration`/`killed_economic`/
      `killed_fragile`, and one correctly-signed `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`. Assert
      canonical manifest-order visiting is unaffected by any kill/survivor along the way, and that
      every Foundry family's denominator/best-of-N disclosure recorded on every terminal row equals
      the pre-frozen manifest value regardless of execution progress.
- [ ] Same test module: an all-`BLOCKED_*`/`EXCLUDED_*`/`ALIASED_*` hermetic epoch (zero
      `FROZEN_READY` variants) reaching valid exhaustive completion with an honest zero-candidate
      summary, not an error; an all-killed hermetic epoch (every `FROZEN_READY` variant terminates
      `EVALUATED_INSUFFICIENT`/`EVALUATED_KILLED`, zero survivors) reaching valid completion; a
      multi-survivor hermetic epoch (two or more independently-surviving candidates) preserving every
      survivor with no ranking/selection of one over another (Required Hermetic/Trap Coverage #45).
- [ ] A large-N synthetic performance/checkpoint fixture (Constraints: "use large hermetic synthetic
      fixtures to prove performance/checkpoint behavior before the real freeze") spanning multiple
      families, with a simulated mid-epoch crash (process kill or dropped checkpoint) after some
      terminal rows already exist; assert resume reconstructs runner position from the Foundry trial
      ledger (never trusting a stale checkpoint blindly), verifies/skips every already-terminal
      candidate with zero duplicate rows, and completes the remainder in canonical order.
- [ ] Protected-data trip fixtures: a hermetic population source that raises the EXISTING
      `micro_accessor.MicroAccessorSealedShardError`/`MicroAccessorOriginFenceError` during anchor
      resolution; assert the Foundry side fails closed (no terminal `EVALUATED_*`/survivor row is
      written for that candidate, no `evidence_class` field anywhere in the oracle suite is ever set
      to `historical_oos`/`live_confirmatory`) by reusing these exact existing exception types — no
      new accessor abstraction, no parallel evidence-control path. This is a hermetic proof of the
      fail-closed CONTRACT only; wiring the real `micro_accessor.MicroAccessor` into the Foundry
      runner's real-corpus resolution path stays out of scope (J-07 territory, matching
      `docs/hypothesis-foundry-spec.md` §10's own "future work, meaning fixed here" framing).
- [ ] `foundry_runner.py` (`run_one_candidate`, `~line 89`): the already-terminal fast path must
      re-verify the stored terminal row's `manifest_hash`/`econ_floor_bps` against the current
      invocation's inputs and raise the same `FoundryResumeIdentityMismatch` the
      intent-without-terminal branch already raises on drift, instead of silently returning a stale
      row; matching inputs still return the existing row unchanged.
- [ ] `foundry_source_registry.py` (`SourceRecord`, `~line 159`): add `source_hash: str`, computed
      deterministically as `sha256(source_excerpt)` exactly as already documented in
      `docs/hypothesis-foundry-spec.md` §1.4's field table, recomputed/verified so it can never drift
      from `source_excerpt` (mirror the existing `source_registry_hash` determinism pattern). Add
      `alternatives: tuple[str, ...]` per Constitution §1.4 ("every finite alternative the compiler is
      allowed to enumerate") — see `state/assumptions.md` for this iteration's reading of the field's
      exact shape. Extend the existing "two explicitly-frozen legal variants" hermetic fixture pair
      (the one J-02 step 2 already names) to populate and assert both new fields; a mechanism with no
      ratified alternative shows an empty `alternatives` tuple.
- [ ] Extend `docs/hypothesis-foundry-spec.md` §1.4's field table with the `alternatives` row (using
      whatever exact wording matches the implementation above) — documentation-only, no scientific
      meaning change.

### Frontend

None. All Foundry UI (including any future "Hermetic Oracles" fixture subview) stays deferred to the
Binding Execution Order step-5 consolidated read-surface iteration, per `state/blueprint.md` and the
iter-1 assumption-ledger entry — unchanged this iteration.

### New user-facing capability

None. This iteration is hermetic-backend-only; the operator-visible product is unchanged.

### New information displayed

None — the oracle suite and the two field additions are exercised only by hermetic tests, not served
through `GET /research/desk/micro/foundry` or `/desk` (the real 11-source registry content and the
real epoch don't exist until J-06).

### New user actions

None — the Foundry surface remains read-only and unchanged in the UI this iteration.

### UI surface changes

None.

### Product surface delta

None visible to the operator this iteration.

### Blueprint conformance

No new page or route. All work stays inside the existing `/desk` → `Hypothesis Foundry` panel's
already-named subsection homes in `state/blueprint.md` (J-05 → "Hermetic Oracles"; J-02 → "Sources/
Compiler"; J-04 → "Freeze/Integrity") — none of those subsections ship UI yet, so nothing new becomes
reachable this iteration.

### Data-contract additions

None. This iteration deepens the hermetic-fixture proof and the internal schema of Data Contract rows
already registered in `state/blueprint.md` (row 2's `foundry_source_registry.py` gains two fields; row
7/8's `foundry_runner.py`/`foundry_ledger.py` integrity check is completed) without changing any
row's computing module, serving endpoint, or the real `GET /research/desk/micro/foundry` response body
— nothing new is served anywhere yet.

## OUT OF SCOPE

- Real source-registry authoring (the 11 required objects, §1.1/§1.2), real epoch generation, the
  freeze commit, and any real candidate outcome read (Binding Execution Order steps 6-8; J-06/J-07) —
  illegal until steps 4-5 are complete and hermetically proven.
- Any Sources/Compiler/Interpreter/Freeze/Hermetic-Oracles fixture UI subview — deferred to the
  consolidated read-surface iteration (Binding Execution Order step 5), matching the J-02/J-03/J-04
  precedent.
- Wiring the real `micro_accessor.MicroAccessor` into the Foundry runner's real-corpus resolution path
  — only the fail-closed exception-reuse CONTRACT is proven hermetically this iteration; real
  evidence-boundary wiring is J-07 territory per `docs/hypothesis-foundry-spec.md` §10.
- A CLI entry point for `foundry_runner.py` — still deferred to whichever iteration first wires
  real-epoch orchestration (J-06/J-07), per the iter-2 dev handoff's own Known Issues.
- Widening `generate_freeze_set`'s same-directory-only (`level == 1`) transitive import scan to
  cross-package dependencies — a disclosed, lesser carried item that does not block J-05's hermetic
  proof; revisit only if a real J-06/J-07 freeze-set needs to prove coverage of a cross-package
  dependency.
- §4.4's optional descriptive seam (aggressor-derived fallback-tercile disclosure) — no TC this
  iteration requires it; still speculative ahead of need.
- Real economic-floor materialization against a real corpus (§6) — J-07 territory.
- The optional read-only MCP proxy (`desk_micro_foundry`) — explicitly deferrable per the goal.
- Raising the session's `--max-iter` cap from 60 to 80 — an operator decision, carried in NOTES.

## DEFINITION OF DONE

- [ ] J-05's complete hermetic oracle suite is implemented and passes: the composite multi-outcome-type
      epoch, all-blocked epoch, all-killed epoch, multi-survivor epoch, large-scale checkpoint/resume,
      and protected-data-trip/evidence-class-immutability fixtures all run through the real production
      compiler/interpreter/family/freeze/ledger/runner path (TC-1..TC-8); J-05 is expected to move
      `failing` → `partial` (no UI exists yet, matching the J-02/J-03/J-04 precedent)
- [ ] J-04's resume-identity fast-path gap is closed: a stored terminal row whose `manifest_hash`/
      `econ_floor_bps` differ from the current invocation raises `FoundryResumeIdentityMismatch`
      instead of being silently returned (TC-9); J-04 stays `partial` (UI still deferred) but its
      carried active blocker is resolved
- [ ] J-02's `SourceRecord` gains `alternatives` and `source_hash` exactly as documented in
      `docs/hypothesis-foundry-spec.md` §1.4 (TC-10, TC-11); J-02 stays `partial` (UI still deferred)
      but its carried active blocker is resolved, unblocking J-06's future real-source authoring
- [ ] J-01 regression: the existing golden replay (`journey-scripts/J-01.json`) still passes with no
      change to the era-open baseline panel (TC-13)
- [ ] No anti-goal violation introduced: no real Foundry candidate outcome read anywhere; no second
      accessor/evidence-control abstraction; no Foundry trial written to the Scout ledger; no guard
      weakened or bypassed; no `docs/hypothesis-foundry/` real-epoch artifact created
- [ ] Unit tests pass; no regressions (full backend suite + `tsc --noEmit` stay green) (TC-12)
- [ ] Dev handoff written at `docs/handoffs/goal-hypothesis-foundry-iter-3-dev.md`

## TESTING REQUIREMENTS

- Browser: J-01 replay only (regression check; no new browser surface ships this iteration by design
  — J-05/J-02/J-04 have no UI to inspect yet).
- Unit/integration: composite multi-outcome-type hermetic epoch through the full production pipeline;
  all-blocked/all-killed/multi-survivor hermetic epochs; large-N checkpoint/resume under a simulated
  crash; protected-data-trip fail-closed behavior reusing the existing `MicroAccessor` exception types;
  evidence-class immutability across the whole oracle suite; resume-identity re-verification on the
  already-terminal fast path; `SourceRecord.source_hash`/`alternatives` correctness.
- Error cases: a sealed/withheld-shard trip must refuse the candidate, never silently promote
  `evidence_class`; a resumed candidate with a drifted `manifest_hash`/`econ_floor_bps` must raise
  `FoundryResumeIdentityMismatch`, never return a stale terminal row; an all-blocked/all-killed epoch
  must reach honest completion, never an error; a multi-survivor epoch must never rank/select one
  survivor over another.

Test-first contract:

- TC-1: given a hermetic "complete factory" epoch fixture containing a `BLOCKED_*` source, an
  `EXCLUDED_*` source, an `ALIASED_*` source, and `FROZEN_READY` variants that will terminate
  `EVALUATED_INSUFFICIENT` (via `killed_insufficient_n`), `EVALUATED_KILLED` (via each of
  `killed_null`/`killed_direction`/`killed_concentration`/`killed_economic`/`killed_fragile`), and one
  correctly-signed `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` survivor, when the checkpointed exhaust runner
  processes the whole epoch, then every `FROZEN_READY` variant reaches exactly one terminal state
  matching the §7.2 mechanical mapping, visiting order is unaffected by any kill/survivor encountered
  along the way, and every non-compiled source keeps its declared disposition unchanged.
- TC-2: given that same composite epoch, when the runner completes, then the Foundry family
  denominator and best-of-N disclosure recorded on every terminal row equal the pre-frozen manifest
  values, unaffected by which siblings had already executed.
- TC-3: given an all-`BLOCKED_*`/`EXCLUDED_*`/`ALIASED_*` hermetic epoch with zero `FROZEN_READY`
  variants, when the runner exhausts it, then it reaches a valid terminal completion state with zero
  terminal rows and an honest zero-candidate read-model summary, not an error.
- TC-4: given an all-killed hermetic epoch (every `FROZEN_READY` variant terminates
  `EVALUATED_INSUFFICIENT`/`EVALUATED_KILLED`, zero survivors), when the runner exhausts it, then
  completion is valid and the read-model summary reports zero `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`
  rows.
- TC-5: given a hermetic epoch with two or more independently-surviving candidates, when the runner
  exhausts it, then every survivor is recorded and preserved with no ranking, selection, or demotion
  of any one over another.
- TC-6: given a large synthetic hermetic fixture spanning multiple families and a simulated mid-epoch
  crash after some terminal rows already exist, when the runner resumes, then it reconstructs its
  position from the Foundry trial ledger, verifies/skips every already-terminal candidate with zero
  duplicate rows, and completes the remainder in canonical order.
- TC-7: given a hermetic population source that raises `MicroAccessorSealedShardError` or
  `MicroAccessorOriginFenceError` during anchor resolution, when the Foundry interpreter/runner
  encounters it, then the candidate is refused with a typed Foundry-level error, no terminal
  `EVALUATED_*`/survivor row is written for it, and no new accessor abstraction is introduced.
- TC-8: given the complete hermetic oracle suite from TC-1..TC-7, when every record's `evidence_class`
  field is inspected, then it is always the fixed literal `historical_exposed_diagnostic` and no code
  path in the suite sets any other value.
- TC-9: given `foundry_runner.run_one_candidate` is called for a candidate whose stored terminal row's
  `manifest_hash`/`econ_floor_bps` differ from the current invocation's inputs, when the already-terminal
  fast path is hit, then it raises `FoundryResumeIdentityMismatch` instead of returning the stale row;
  given the stored row's identities match the current inputs, when the fast path is hit, then it still
  returns the existing row unchanged.
- TC-10: given a `SourceRecord` fixture, when `source_hash` is computed, then it equals
  `sha256(source_excerpt)` exactly as documented in `docs/hypothesis-foundry-spec.md` §1.4, and
  changing `source_excerpt` changes `source_hash`.
- TC-11: given the existing hermetic fixture pair sharing one `foundry_family_key` that legally
  represents two frozen alternative variants, when each record's `alternatives` field is inspected,
  then each names the sibling representation as its legal alternative, and a fixture record whose
  mechanism has no ratified alternative shows an empty `alternatives` tuple.
- TC-12: given the full backend suite and `tsc --noEmit` run after this iteration's changes, when they
  complete, then all existing Rapid Microscope/Referee/unit/no-lookahead/no-execution tests plus every
  prior Foundry test remain green, `docs/hypothesis-foundry/source-registry.json`/`epoch-manifest.json`/
  `freeze-set.json`/`freeze-record.json` remain absent from the tree, and no real Foundry candidate
  outcome was read anywhere in this iteration's code or tests.
- TC-13: given the existing golden replay script `journey-scripts/J-01.json` run against this
  iteration's build, when replay executes, then it reproduces the same passing result with no
  regression to the era-open baseline panel.

## NOTES

- Two interpretive calls behind this iteration's scoping are logged in
  `runs/goal-session-hypothesis-foundry/state/assumptions.md` under `## iter-3 — goal-decomposer`: (1)
  the exact shape of `SourceRecord.alternatives`, since `docs/hypothesis-foundry-spec.md`'s own §1.4
  field table does not yet define it and `goal.md` only says "every finite alternative the compiler is
  allowed to enumerate"; (2) how much of the protected-data-trip proof belongs in this hermetic
  iteration versus real `MicroAccessor` wiring reserved for J-07.
- Operator decision carried forward from `iter-0/eval.md`/`iter-1/eval.md`/`iter-2/eval.md`:
  `session.json` currently caps this session at 60 iterations; the goal document recommends
  `--max-iter 80` for this era. Not an agent-fixable change; not acted on here.
- `config_fingerprint 08e471b10130e1e2` stays pinned this iteration — nothing here touches frozen
  structure/tape-engine calculations.
- `foundry_*.py` modules continue to operate on hermetic fixture epoch ids only this iteration. They
  must not read, create, or reference any tracked `docs/hypothesis-foundry/` real-epoch artifact —
  those are generated for real only at Binding Execution Order step 6 (J-06).
- `state/blueprint.md` is updated this iteration with an "Iteration note (iter-3)" describing the
  hermetic oracle suite's completion and the two field additions; no Data Contract row is added or
  re-homed, so no `blueprint.reapproval-requested` file is written.
