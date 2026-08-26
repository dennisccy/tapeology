# Goal Iteration 1 — repair the QA rig, open the Foundry `/desk` panel, prove the source compiler on fixtures

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** hypothesis-foundry
- **Iteration:** 1
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-02
- **Required-still-passing journeys:** none — 0/8 Foundry journeys currently pass, and this
  session's fixed journey set (J-01..J-08) carries no prior-era journey IDs to replay. Foundation
  regression (existing Rapid Microscope / Referee / unit / no-lookahead / no-execution suite,
  `tsc --noEmit`) is covered every iteration by the DEFINITION OF DONE unit-test gate regardless of
  this list.
- **Anti-goal reminders:**
  - "No case-by-case scientific owner prompt during the run. Unresolved science blocks and
    execution continues unless a core integrity defect requires a halt."
  - "No source record, threshold, direction, family partition, or CandidateSpec chosen because of
    effect, p-value, sample density, or prior Scout outcome."
  - "No runtime LLM interpretation in the real manifest-generation command."
  - "Single source of truth. Every shared scientific value has one canonical backend owner;
    REST/UI/MCP never independently recompute it."
  - "Persistence stays scoped... `GET /research/desk/micro/foundry` and every page-load GET are
    read-only and never compute/evaluate a candidate or trigger the exhaust runner."
  - "No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a
    journey."
  - "No weakening or bypass of `project-extensions/host-guard/host-guard.env`; Goal Mode pauses
    `AWAITING_HOST_GUARD` if confinement cannot be established."

## GOAL

Repair the fixture bug that has blocked all browser evidence, open the `Hypothesis Foundry` panel
on `/desk` with the era-identity + era-open baseline it needs to finish J-01, and stand up the
first real piece of Foundry science — the source-registry owner-meta-policy compiler and
`CandidateSpec` schema — proven hermetically against the 7 fixture source types J-02 requires,
with no real source authored and no real candidate outcome read.

## BACKGROUND

Iteration 0 was a no-op baseline: it found the Foundry era's paperwork already done (J-01 steps
2-4) but every Foundry surface entirely unbuilt, and it found the browser lane completely dead
because the scoped `:8301` QA rig's seed fixture omits `value_unit`, tripping
`walkforward.require_canonical_observation_units` and leaving no screenshot possible for any
journey (see `lessons.md` iter-0: "The whole browser lane can be lost to a stale QA fixture...
fix the fixture, never relax the guard"). The evaluator's binding depth recommendation is `lean`;
per the rubric's priority order this iteration first fixes that blocker (rule 3, the biggest
unblocker in the session — no journey can ever reach `passing` without it), then begins the
mandatory next step of the goal's Binding Execution Order: step 1's remaining gap (J-01 steps 1+5)
and step 2 (source registry + CandidateSpec, no real manifest yet — J-02).

No full-depth trigger applies. This is deliberately scoped to backend-heavy, low-risk work: the
fixture fix is a one-line addition to a QA-only seed script; J-01's remaining gap is a small
additive display (era identity + a static, pre-computed baseline snapshot) on the already-existing
`/desk` page; and J-02's machinery this iteration is proven only against 7 synthetic hermetic
fixture source records, entirely backend/test-only (no UI, no real source content) — it does not
touch the real 11 required source objects, the generic interpreter, or any real epoch/freeze/outcome
work, so it neither refactors shared architecture nor spans ≥3 modules uncovered by its own tests
(trigger 1), nor changes an already-registered Data-Contract value's computing module (trigger 2;
this ships rows that were previously unbuilt, which is explicitly not this trigger), nor follows a
prior ESCALATE (trigger 3) or a met hardening cadence (trigger 4, currently 0/6). Two assumption-
ledger entries (`state/assumptions.md`, iter-1) record the interpretive choices behind this scoping:
(1) "first source records" in Binding Execution Order step 2 is read as compiler-rule machinery
proven on the 7 fixture types J-02 itself names, not early authoring of the real 11 sources (which
belongs to J-06 and which J-02's own step 5 partly depends on anyway); (2) the Sources/Compiler
fixture UI is deliberately deferred to the single consolidated read-surface iteration named in
Binding Execution Order step 5, built once after the interpreter/family/freeze machinery exists,
rather than extended three separate times.

Consequence for scoring: J-01 is expected to reach `passing` this iteration. J-02 is expected to
move `failing` → `partial` — its compiler/schema/lint machinery is real and hermetically tested,
but its own acceptance criteria (a UI "fixture view" plus, in step 5, inspection of the committed
J-06 audit report) cannot fully close until later iterations; that is expected, not a shortfall.

## IN SCOPE

### Backend

- [ ] Fix `apps/backend/scripts/seed_micro_graduation_iter18_fixture.py::_observation()` (line
      ~103) to declare `value_unit` on each of the 30 seeded observations, using the same canonical
      unit the fixture's own values are already in (basis points — confirm against
      `walkforward.WF_OBSERVATION_UNIT` / `micro_features.OUTCOME_UNIT`, do not invent a new unit
      constant). Do NOT modify `walkforward.require_canonical_observation_units` or loosen any
      guard it calls.
- [ ] Confirm the scoped QA rig actually comes up healthy on port 8301 after the fix (this is the
      prerequisite for any journey ever reaching `passing` via browser-qa).
- [ ] Write `docs/hypothesis-foundry-spec.md` — the Foundry Methodology Spec (Key Capability 1):
      candidate-construction / freeze / exhaustion semantics only; it must not restate or fork the
      Rapid Validation statistical decision rail, only reference it.
- [ ] New module `app/research/foundry_source_registry.py`:
  - the closed §7.1 source-disposition vocabulary as a typed enum/constant set;
  - the owner meta-policy compile rules: natural-boundary law (§2.3), enumeration-vs-block
    (§2.1/§2.2), formula-scoped supersession (§1.3);
  - the §1.4 per-source-record required fields (source_id, exact source path+section ref, exact
    quoted span+location, source hash, mechanism statement, operative formula refs, superseded
    fields, alternatives, threshold provenance, direction derivation rule or `BLOCKED_DIRECTION`,
    comparator derivation or `BLOCKED_UNSUPPORTED_STUDY_FORM`, final disposition, aliases/lineage,
    audit note);
  - an exact-quote lint utility that verifies every recorded quoted span is an exact substring of
    the cited source text at the recorded location;
  - an era-open baseline recording function that computes ONCE and persists a static snapshot
    (full backend suite pass/skip/failed counts, `tsc --noEmit` error count, `config_fingerprint`,
    SHA-256 of each of the six `referee_*.py` modules: `referee_adjudicate.py`,
    `referee_evidence.py`, `referee_null.py`, `referee_registry.py`, `referee_routes.py`,
    `referee_stats.py`) — never recomputed on a page-load GET.
- [ ] Seven hermetic fixture source records (test fixtures, not the real 11 required objects)
      covering exactly the taxonomy J-02 step 2 names: a compileable natural-boundary scalar; two
      explicitly-frozen legal variants in the same family; an unresolved magnitude word; a
      proxy-only source; an unsupported statistic; an alias/supersession case; a directionless
      mechanism.
- [ ] New module `app/research/foundry_compiler.py`: the canonical `CandidateSpec` schema
      (dataclass/typed model) implementing every §3 required field, `candidate_spec_hash`
      computation that changes on every science-affecting field and is invariant to field
      serialization order, and compilation of the `COMPILED`-disposition fixtures above into real
      `CandidateSpec` objects. Deferred/population-resolution machinery (`foundry_interpreter.py`)
      is explicitly out of scope — only fixtures that compile without it.
- [ ] New route `GET /research/desk/micro/foundry` added to the existing `micro_routes.py` router
      (same GET-only, page-load-never-computes convention as its sibling routes): serves era/session
      identity, Foundry methodology spec version, and the era-open baseline block. Render
      `source_registry_hash` as `null`/`not_yet_generated` (the real registry does not exist until
      Binding Execution Order step 6 / J-06) — never fabricate a placeholder hash.
- [ ] Unit/integration tests: `test_foundry_source_registry.py`, `test_foundry_compiler.py`
      (naming mirrors the existing `test_micro_*.py` / `test_referee_*.py` convention).

### Frontend

- [ ] `apps/frontend/app/desk/page.tsx`: append `<section aria-label="Hypothesis Foundry">` below
      the existing shipped sections, `data-testid="foundry-panel"` family. Render, verbatim from
      `GET /research/desk/micro/foundry` (no client-side recomputation): era/session identity
      distinguishing Rapid Microscope (closed foundation) from the Foundry (active era), and the
      era-open baseline block (suite pass/skip/failed counts, `tsc` error count, config
      fingerprint, the six Referee-module SHA-256 hashes).

### New user-facing capability

The operator can expand a new `Hypothesis Foundry` section on `/desk` and see the era boundary
(Rapid Microscope closed / Foundry active) plus the frozen era-open baseline the whole epoch will
be audited against.

### New information displayed

Era/session identity, Foundry methodology spec version, and the era-open baseline (suite
pass/skip/failed counts, `tsc` error count, config fingerprint, six Referee-module SHA-256 hashes).

### New user actions

None beyond expanding the existing `/desk` accordion pattern — the Foundry surface is read-only per
the goal's Product Shape.

### UI surface changes

One new `<section>` appended to `/desk`, below all existing shipped sections; no other page changes.

### Product surface delta

`/desk` gains a header-only `Hypothesis Foundry` panel; no other route changes.

### Blueprint conformance

Lives under the existing Desk nav section, per the Information Architecture already registered in
`state/blueprint.md` ("J-01 ... → `/desk` → Hypothesis Foundry panel header"). No nav-skeleton
change; no reapproval file needed.

### Data-contract additions

None — this iteration ships real implementations of Data Contract rows 1-3 already registered in
`state/blueprint.md` at baseline (era/session identity + era-open baseline; source dispositions;
`CandidateSpec` + hash), finalizing their computing modules there (`blueprint.md` updated this
iteration). No new value is introduced outside that table.

## OUT OF SCOPE

- Authoring the real 11 required source objects (§1.1/§1.2 — Study 1, Study 3, Cards 9.3-9.7, the
  two pilot proxies, plus the exclusions for Card 9.1/9.2/9.8-9.11) — that is J-06 and is illegal
  before steps 3-5 of the Binding Execution Order exist.
- The generic candidate interpreter, Scout adapter, Foundry family/denominator machinery, ledger,
  or freeze barrier (J-03/J-04) — Binding Execution Order step 3, a later iteration.
- Any Sources/Compiler (or other) fixture UI subview beyond the panel header — deferred to the
  consolidated read-surface iteration (Binding Execution Order step 5).
- Real epoch generation, freeze commit, exhaust runner, or any candidate outcome read (Binding
  Execution Order steps 6-8) — illegal until steps 2-5 are complete and hermetically proven.
- The optional read-only MCP proxy (`desk_micro_foundry`) — explicitly deferrable per the goal.
- Raising the session's `--max-iter` cap from 60 to 80 — an operator decision, not an
  agent-fixable change; carried forward in NOTES.

## DEFINITION OF DONE

- [ ] J-01 passes via browser-qa-agent (panel header renders era identity + era-open baseline,
      every displayed value matches the `GET /research/desk/micro/foundry` response body verbatim)
- [ ] J-02's compiler machinery (methodology spec doc, `CandidateSpec` schema/hash, source-registry
      compile rules across the 7 required fixture types, exact-quote lint) is implemented and
      unit-tested; the evaluator may score J-02 `partial` this iteration since its own UI view and
      the J-06 audit-report inspection are out of scope here by design
- [ ] Scoped `:8301` QA fixture rig starts healthy; `require_canonical_observation_units` is left
      unweakened
- [ ] No anti-goal violation introduced (no real Foundry outcome read; no real source authored; no
      guard weakened; new GET route never computes/evaluates)
- [ ] Unit tests pass; no regressions (full backend suite + `tsc --noEmit` stay green)
- [ ] Dev handoff written at `docs/handoffs/goal-hypothesis-foundry-iter-1-dev.md`

## TESTING REQUIREMENTS

- Browser: J-01 (`/desk` → `Hypothesis Foundry` panel header, era identity + era-open baseline,
  REST-body match)
- Unit/integration: fixture-fix unit-mismatch regression test; source-registry disposition compile
  rules across all 7 fixture types; exact-quote lint; `CandidateSpec` hash sensitivity/invariance;
  era-open baseline static-snapshot behavior
- Error cases: unresolved-magnitude-word source must block, not compile; directionless mechanism
  must block, not compile; a mismatched quoted span must fail lint closed; an injected
  effect/p-value/n fixture field must not change disposition or hash

Test-first contract:

- TC-1: given `seed_micro_graduation_iter18_fixture.py::_observation()` with the `value_unit` fix
  applied, when the scoped QA rig starts on port 8301, then it reports healthy and
  `browser-infra.json` no longer records `reason: store-scope` for this iteration.
- TC-2: given `_observation()` now returns a dict containing `value_unit`, when
  `walkforward.require_canonical_observation_units` runs over the 30 seeded values, then it
  returns without raising `UnitMismatchError`.
- TC-3: given the natural-boundary-scalar fixture source record, when
  `foundry_source_registry`/`foundry_compiler` compile it, then the resulting disposition is
  `COMPILED` and a `CandidateSpec` with a non-null `candidate_spec_hash` is produced.
- TC-4: given the two explicitly-frozen legal-variant fixture sources in one family, when compiled,
  then both variants share one `foundry_family_id`, `foundry_family_variant_count = 2`, and have
  distinct `variant_ordinal` values.
- TC-5: given the unresolved-magnitude-word fixture source, when compiled, then the disposition is
  `BLOCKED_SPEC_GAP` and no `CandidateSpec` is produced.
- TC-6: given the proxy-only fixture source, when compiled, then the disposition is
  `ALIASED_PROXY_ONLY` and its `do_not` restriction field is preserved on the record.
- TC-7: given the unsupported-statistic fixture source, when compiled, then the disposition is
  `BLOCKED_UNSUPPORTED_STUDY_FORM`.
- TC-8: given the alias/supersession fixture source pair (an older card constant vs. a newer
  frozen rule for the same formula), when compiled, then the older record's disposition is
  `ALIASED_VARIANT_VOCABULARY` (or `ALIASED_LINEAGE`) and its `superseded_fields` cite the newer
  ref.
- TC-9: given the directionless-mechanism fixture source, when compiled, then the disposition is
  `BLOCKED_DIRECTION` and no `CandidateSpec` is produced.
- TC-10: given a compiled fixture `CandidateSpec`, when one §3 science-affecting field (e.g.
  `horizon_key`) is mutated, then `candidate_spec_hash` changes; when only field-serialization
  order is shuffled, then `candidate_spec_hash` is unchanged.
- TC-11: given a compiled fixture `CandidateSpec`, when an injected `effect_bps`/`p_value`/`n`
  fixture field (outside source inputs) is added to the record, then `candidate_spec_hash` and
  `disposition` are unchanged.
- TC-12: given the exact-quote lint utility, when run over all 7 fixture source records, then every
  recorded quoted span verifies as an exact substring of its cited source at the recorded location,
  and lint fails closed on an injected mismatched span.
- TC-13: given a fresh backend suite run, `config_fingerprint`, and the six `referee_*.py` module
  hashes, when the era-open baseline recording function runs once, then it persists a static record
  that two subsequent `GET /research/desk/micro/foundry` calls serve byte-identically with no
  recomputation between calls.
- TC-14: given `/desk` loaded in a browser, when the operator expands `Hypothesis Foundry`
  (`data-testid="foundry-panel"`), then the header shows the Rapid-Microscope-closed / Foundry-
  active era identity and the era-open baseline block, and every displayed number matches the
  `GET /research/desk/micro/foundry` response body verbatim.
- TC-15: given `GET /research/desk/micro/foundry` is called twice with no intervening state change,
  when the two responses are compared, then `source_registry_hash` renders as
  `null`/`not_yet_generated` on both (never a fabricated placeholder hash).

## NOTES

- Lesson applied (`lessons.md` iter-0, applies to all future browser-evidence iterations and any
  future science-contract revision): fix the FIXTURE's missing `value_unit`, never relax
  `require_canonical_observation_units`. TC-1/TC-2 exist specifically to prove this was done the
  right way.
- Operator decision carried forward from `iter-0/eval.md`: `session.json` currently caps this
  session at 60 iterations; the goal document recommends `--max-iter 80` for this era. This is not
  an agent-fixable change and is not acted on here.
- `docs/hypothesis-foundry-spec.md`, the `foundry_source_registry.py`/`foundry_compiler.py`
  modules, and the 7 fixture source records are NOT part of the tracked `docs/hypothesis-foundry/`
  real-epoch artifact set (§8.2) — those (`source-registry.json`, `epoch-manifest.json`,
  `freeze-set.json`, `freeze-record.json`) are generated only at Binding Execution Order step 6
  (J-06) by running this iteration's machinery against the real ratified sources. Do not create
  those tracked files this iteration.
- Two interpretive calls behind this iteration's scoping are logged in
  `runs/goal-session-hypothesis-foundry/state/assumptions.md` under `## iter-1 — goal-decomposer`.
