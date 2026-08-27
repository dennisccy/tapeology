# Goal Iteration 4 — the consolidated Foundry read surface (J-02/J-03/J-04/J-05) + two carried integrity repairs

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** hypothesis-foundry
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: this iteration builds ONE consolidated `/desk` →
  Hypothesis Foundry read surface that renders values from six already-built backend modules
  (`foundry_source_registry.py`, `foundry_compiler.py`, `foundry_interpreter.py`,
  `foundry_family.py`, `foundry_freeze.py`, `foundry_ledger.py`) plus one new summary module, all
  through a single endpoint, across four target journeys at once. No single journey's own tests
  cover the cross-module rendering seam (GET route → four subview keys → four UI subsections all
  agreeing with the underlying fixture machinery) — exactly the class of gap iter-3's auditor found
  in the compiler→runner seam. This ALSO matches the evaluator's own binding depth recommendation
  for this iteration (full), so no escape-condition analysis is needed beyond citing the trigger.
- **Frontend Present:** yes
- **Target journeys:** J-02, J-03, J-04, J-05
- **Required-still-passing journeys:** J-01 (the only `passing` Foundry journey; golden replay script
  `runs/goal-session-hypothesis-foundry/journey-scripts/J-01.json` exists and must still pass — this
  iteration extends the SAME `GET /research/desk/micro/foundry` response J-01 already reads, so a
  regression there is the single highest-risk failure mode). Do-not-regress items beyond J-01: the
  full backend suite baseline (iter-3: 3842 passed / 8 skipped / 0 failed), `tsc --noEmit` (0
  errors), and `config_fingerprint 08e471b10130e1e2` — all covered by DEFINITION OF DONE, not by
  journey replay (J-06/J-07/J-08 are still `failing` and out of scope this iteration).
- **Anti-goal reminders:**
  - "No case-by-case scientific owner prompt during the run. Unresolved science blocks and execution
    continues unless a core integrity defect requires a halt."
  - "No source record, threshold, direction, family partition, or CandidateSpec chosen because of
    effect, p-value, sample density, or prior Scout outcome."
  - "No family splitting to evade the 24-variant cap."
  - "No second Foundry statistical decision rail."
  - "No Foundry trial registered into the Scout ledger this era; the Foundry trial ledger is the
    canonical record and must carry the complete Scout screen payload plus both denominator contexts
    where defined."
  - "Evidence classes never mix; `historical_exposed_diagnostic` rows never pool with
    `historical_oos`/`live_confirmatory`."
  - "No exploratory read of a sealed shard; no Vault secret in repo/log/payload/screenshot."
  - "**Single source of truth.** Every shared scientific value has one canonical backend owner;
    REST/UI/MCP never independently recompute it."
  - "**Persistence stays scoped.** Fetching/recording/exposure is always an explicit operator act;
    page loads and Foundry reads never record market data. `GET /research/desk/micro/foundry` and
    every page-load GET are read-only and never compute/evaluate a candidate or trigger the exhaust
    runner."
  - "No browser proof based on fabricated fixture state when a journey claims to show real final
    state; fixture and real views must be visibly distinguished."
  - "No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a journey."
  - "A real candidate outcome read before step 7 is a critical anti-goal violation."
  - "No candidate invented after the real manifest freezes." / "No late variant insertion."
  - "No claim that `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN` is OOS evidence or proof of edge."

## GOAL

An operator opens `/desk` → Hypothesis Foundry and, for the first time, sees photographable evidence
of the compiler, generic interpreter, family/freeze/ledger, and hermetic-oracle machinery working
correctly on fixture data — turning four `partial` journeys (J-02, J-03, J-04, J-05) as far toward
`passing` as this stage of the goal's own Binding Execution Order allows.

## BACKGROUND

Both of the last two evaluator verdicts point at the exact same single blocker.
`iter-3/eval.md`'s next-step recommendation: "Build the one Foundry screen. All the machinery is
proven behind the scenes, but an operator can still see none of it, and that alone is why J-02 ...
J-03 ... J-04 ... and J-05 ... are all stuck at partly done — twenty-two on-screen checks between
them, none ever photographed. This is the goal's own next required stage and the only work that can
turn four journeys green at once. ... Run it at full depth." `state/iteration-state.md`'s active
blockers section names the same thing as "THE ONE BLOCKER" and confirms the four subsection homes are
already registered in `state/blueprint.md`. This is Binding Execution Order step 5 ("Read surface.
Fixture states visible; real epoch still unopened."); steps 3-4 (interpreter/family/freeze/ledger +
hermetic oracles) already shipped and are in `iteration-state.md`'s "Do not redo" list, and steps 6-8
(real epoch, freeze commit, exhaust) stay illegal until step 5 is proven.

Targeting all four journeys in one iteration is a deliberate exception to the usual 1-3-journey
guidance: they are not four independent risky changes, they are four acceptance surfaces over the
SAME single deliverable (one read surface reading from the SAME `GET /research/desk/micro/foundry`
endpoint), exactly as both evaluator verdicts describe it. This satisfies priority rubric rule 3
(unblocker) taken to its natural conclusion rather than rule 5's "never bundle two risky journeys" —
there is one risky body of work here (the cross-cutting read surface), not two.

The evaluator's iter-3 recommendation also named three small carried repairs to ride alongside the
screen: "refuse a source record that names a sibling which does not exist or is not in its family;
extend the restart check to the crash path too; and stop the QA report claiming the J-01 screen check
was covered by the backend test run — it was covered by the browser replay." All three are included
below (two as code, one as a QA-report correction).

Two ambiguities were resolved and logged to `state/assumptions.md` (iter-4): (1) J-02 step 5 bundles
a buildable hermetic-immutability check with an "inspect the committed audit report" check that
depends on J-06's real registry, which does not exist yet — this iteration builds only the buildable
half, and J-02 may still land `partial` for that reason alone; (2) J-04 step 4 names the literal real
tracked path `docs/hypothesis-foundry/freeze-set.json` inside an otherwise fixture-scoped step — this
iteration's fixture view names that path as the future real destination without creating the file.

`lessons.md` applies directly to how this iteration must be built: (iter-3, twice) a "proof" test or
summary must actually exercise the seam/state it claims to, not merely share a name with it — the new
`hermetic_oracles` summary must read genuine outcomes from `test_foundry_hermetic_epoch.py`'s already
-hermetically-proven suite, never a hand-typed duplicate, and any crash-path claim must simulate a
state the mechanism actually holds; (iter-1) the whole browser lane depends on the scoped QA rig
booting cleanly — no fixture seeding change is planned this iteration, but any new fixture data added
to existing seed scripts must declare its unit per that lesson; (iter-2) inventing rig values instead
of reading real ones is the exact anti-goal violation to avoid — not applicable to new real artifacts
here (nothing new is recorded to the real store this iteration), but the same discipline applies to
visibly labelling fixture views as fixture, never real.

`iter-3/coherence.md` was `COHERENCE-PASS`, so this is new scope, not a consolidation pass.

## IN SCOPE

### Backend

- [ ] Extend `GET /research/desk/micro/foundry` (`apps/backend/app/research/micro_routes.py`) with
      four new top-level response keys — `sources_compiler`, `interpreter_fixtures`,
      `freeze_integrity`, `hermetic_oracles` — each read from a precomputed/cached result (module-
      level cache built once at import, or a checked-in generated snapshot); the route handler itself
      must not invoke compiler/interpreter/family/freeze/runner machinery per request, preserving the
      router's already-established GET-never-computes convention.
- [ ] `sources_compiler`: reuse the exact 7 hermetic source fixture types already defined in
      `tests/test_foundry_source_registry.py` / `tests/test_foundry_compiler.py` (compileable
      natural-boundary scalar; two explicitly-frozen legal variants; unresolved magnitude word;
      proxy-only source; unsupported statistic; alias/supersession case; directionless mechanism).
      For each: the full `_canonical_source_record` field set + `disposition` + compiled
      `CandidateSpec` (every §3 field + `candidate_spec_hash`) where compiled, else `block_reason`.
      Add one `immutability_proof` entry: the same compileable fixture compiled twice with two
      different injected `extra` effect/p-value/n values, asserting identical `candidate_spec_hash`.
- [ ] `interpreter_fixtures`: reuse the exact 5 hermetic scenarios already defined in
      `tests/test_foundry_interpreter.py` (immediate-scalar Foundry-vs-direct-Scout equivalence,
      conjunction, deferred `refill_consistent`, mirrored support-long/resistance-short pair,
      unsupported ordered-relation) with the Foundry screen, the direct-Scout screen where
      applicable, equality flag, unresolved-exclusion count, and per-anchor `outcome_start` values.
- [ ] `freeze_integrity`: reuse the exact hermetic fixtures already defined in
      `tests/test_foundry_family.py` / `tests/test_foundry_freeze.py` / `tests/test_foundry_ledger.py`
      for: 1/multiple/at-cap/over-cap family denominators; late-insertion refusal; generation replay
      verify-vs-drift-refusal; a fixture freeze record/freeze-set (via `generate_freeze_set` /
      `build_freeze_record` over the same small fixture module set those tests already use — see
      `state/assumptions.md` iter-4 for why this does not require the real
      `docs/hypothesis-foundry/freeze-set.json` to exist); first-read-lock simulation with hash-drift
      refusal, dirty-session-file tolerance, and non-scientific-file exemption; replay
      idempotence/conflicting-replay refusal/concurrent single-flight refusal.
- [ ] `hermetic_oracles`: new thin summary builder (`app/research/foundry_hermetic_summary.py`) that
      reports, from `tests/test_foundry_hermetic_epoch.py`'s existing composite suite: every outcome
      type present in the composite epoch, denominator consistency across all rows, canonical-order
      preservation, and pass/fail for the all-blocked, all-killed, multi-survivor, crash-resume-at-
      scale, and protected-data-trip/evidence-class-immutability fixtures. This module summarizes the
      existing suite's already-hermetically-proven results; it introduces no second oracle
      implementation and never reads/serves any protected/sealed identity.
- [ ] Repair 1 (auditor B7): `foundry_source_registry.py` — add a fail-closed batch lint over
      `SourceRecord.alternatives` (alongside the existing `lint_quoted_spans`) that raises when an
      alternative names a `source_id` that does not exist in the registry, is not a member of the
      same `foundry_family_key`, or equals the record's own `source_id`.
- [ ] Repair 2 (auditor B4): `foundry_runner.run_one_candidate`'s intent-without-terminal ("crash")
      branch (`~line 112`) — also verify the existing intent row's own `manifest_hash` against the
      current invocation's `manifest_hash` (mirroring the already-fixed terminal-row check three
      lines above it) and raise `FoundryResumeIdentityMismatch` on drift, not only on
      `econ_floor_bps` mismatch.

### Frontend

- [ ] Four new subsections nested inside the existing `HypothesisFoundrySection` component /
      `<section aria-label="Hypothesis Foundry">` (`apps/frontend/app/desk/page.tsx`), each reading
      its corresponding new GET payload key verbatim, no client-side recomputation: Sources/Compiler
      (`foundry-sources-compiler`), Interpreter fixtures (`foundry-interpreter-fixtures`), Freeze/
      Integrity (`foundry-freeze-integrity`), Hermetic Oracles (`foundry-hermetic-oracles`) — matching
      the existing `foundry-*` test-id family and the sibling `CollapsibleSection` pattern already
      used for `hypothesisFoundry` and every other desk section.
- [ ] Sources/Compiler subsection: one row/card per fixture record showing every §1.4 field (source
      refs, exact quoted span + location, operative formula refs, superseded fields, alternatives,
      threshold provenance, direction derivation, alias/lineage, disposition) plus a drill-in for the
      compiled `CandidateSpec`'s full field set and hash; the `immutability_proof` rendered as an
      explicit side-by-side pair with matching hashes visibly called out.
- [ ] Interpreter subsection: the 5 fixture scenarios, each showing the Foundry-vs-direct-Scout screen
      comparison where applicable, the boolean membership projection, the deferred-anchor exclusion
      count, the mirrored support-long/resistance-short pair's predeclared sidedness, and the blocked
      unsupported-relation case's typed block reason.
- [ ] Freeze/Integrity subsection: the family denominator table across the four cap fixtures with the
      over-cap block visibly distinct; the late-insertion-refusal and generation-replay
      verify/drift-refusal proofs; the fixture freeze record detail (naming the real target path
      `docs/hypothesis-foundry/freeze-set.json`, visibly labelled fixture-scope); the first-read-lock
      simulation's three outcomes (hash-drift refused, session dirt ignored, non-science file
      exempted); the replay idempotence/conflicting-replay-refusal/single-flight-refusal proof.
- [ ] Hermetic Oracles subsection: the outcome-type coverage list, the denominator-consistency and
      canonical-order flags, and the five named oracle pass/fail results (all-blocked, all-killed,
      multi-survivor, crash-resume-at-scale, protected-data-trip/evidence-class-immutability).
- [ ] Every one of the four new subsections carries an explicit "HERMETIC FIXTURE — not the real
      epoch" label/banner, visually distinct from the header's real `foundry-era-open-baseline` block
      (Design Direction: audit-first, no promotional language; anti-goal: fixture and real views must
      be visibly distinguished).

### New user-facing capability

An operator can open `/desk` → Hypothesis Foundry and, for the first time, inspect the compiler,
interpreter, freeze/family/ledger, and hermetic-oracle machinery's proof-of-correctness on fixture
data directly in the browser, without reading test code.

### New information displayed

The four new response/UI subviews: `sources_compiler`, `interpreter_fixtures`, `freeze_integrity`,
`hermetic_oracles` — exact field shapes in Data-contract additions below.

### New user actions

Expand/collapse each of the four new subsections (reusing the existing `CollapsibleSection` toggle
pattern). No mutation controls anywhere — the Foundry surface stays read-only per Product Shape.

### UI surface changes

`/desk` → Hypothesis Foundry panel grows from one header block to five total subsections (existing
header + four new ones); no new page, no new route.

### Product surface delta

The Hypothesis Foundry panel becomes the first fully fixture-populated read model over the era's
proven machinery. Still zero real epoch/candidate data — that remains J-06/J-07/J-08.

### Blueprint conformance

All four new subsections live under the already-registered `state/blueprint.md` Information
Architecture homes (`/desk` → Hypothesis Foundry → Sources/Compiler | Interpreter fixtures | Freeze/
Integrity | Hermetic Oracles). No nav-skeleton change; no `blueprint.reapproval-requested` needed.

### Data-contract additions

All four rows below are additive to `GET /research/desk/micro/foundry`'s existing response (already
registered owner) and are now also registered in `state/blueprint.md`'s Data Contract table
(iter-4 note):

- `sources_compiler.fixtures[]`: array of exactly 7 entries, each the existing
  `_canonical_source_record` field set (`source_id: str`, `source_path: str`, `section_ref: str`,
  `quoted_spans: {text: str, location: str}[]`, `source_excerpt: str`, `mechanism_statement: str`,
  `operative_formula_refs: str[]`, `direction_derivation: str`, `comparator_derivation: str`,
  `lineage_id: str|null`, `foundry_family_key: str|null`, `variant_ordinal: int|null`,
  `threshold_provenance: str|null`, `unresolved_magnitude_words: str[]`,
  `superseded_fields: object`, `proxy_of: object|null`, `supersession: object|null`,
  `explicit_exclusion: str|null`, `aliases_lineage_ids: str[]`, `alternatives: str[]`,
  `source_hash: str`) plus `disposition: str` (one of the closed §7.1 vocabulary) and
  `candidate_spec: CandidateSpecView|null` / `block_reason: str|null`, where `CandidateSpecView` is
  the existing `CandidateSpec` dataclass's own field set (`foundry_spec_version: str`,
  `epoch_id: str`, `source_ids: str[]`, `lineage_id: str`, `foundry_family_id: str`,
  `variant_id: str`, `variant_ordinal: int`, `population: object`, `coordinates: object[]`,
  `relation: object`, `membership_corner: str`, `outcome: object`, `economic_floor_rule: object`,
  `foundry_family_variant_count: int`, `manifest_hash: str|null`, `source_registry_hash: str`,
  `compiler_hash: str`, `candidate_spec_hash: str`).
  Computing module: `app/research/foundry_source_registry.py` + `app/research/foundry_compiler.py`
  (existing, no new module). Serving endpoint: `GET /research/desk/micro/foundry`
  (`sources_compiler` key).
- `sources_compiler.immutability_proof`: `{source_id: str, candidate_spec_hash_a: str,
  candidate_spec_hash_b: str, injected_extra_a: object, injected_extra_b: object,
  hashes_equal: bool}`. Same computing module/endpoint as above.
- `interpreter_fixtures.scenarios[]`: array of exactly 5 entries, each `{scenario_id: str,
  kind: "immediate_scalar_equivalence"|"conjunction"|"deferred_refill_consistent"|
  "mirrored_direction"|"unsupported_ordered_relation", foundry_screen: object|null,
  direct_scout_screen: object|null, screens_equal: bool|null, unresolved_excluded_count: int|null,
  outcome_start_candidate: str|null, outcome_start_comparator: str|null, block_reason: str|null}`.
  Computing module: `app/research/foundry_interpreter.py` (existing, no new module). Serving
  endpoint: `GET /research/desk/micro/foundry` (`interpreter_fixtures` key).
- `freeze_integrity`: `{family_denominator_fixtures: {family_kind:
  "single"|"multiple"|"at_cap"|"over_cap", variant_count: int,
  denominator_visible_before_result: bool, over_cap_blocked_whole: bool|null}[]` (exactly 4 entries),
  `late_insertion_refused: bool`, `generation_replay: {identical_rerun_verified: bool,
  drifted_rerun_refused: bool}`, `freeze_record: {freeze_set_target_path: str, freeze_set_hash: str,
  pinned_hashes: object, transitive_dependency_coverage_complete: bool}`, `first_read_lock:
  {hash_drift_refused: bool, session_dirt_ignored: bool, non_science_file_exempted: bool}`,
  `replay: {idempotent: bool, conflicting_replay_refused: bool,
  concurrent_runner_refused: bool}}`. Computing module: `app/research/foundry_family.py` +
  `app/research/foundry_freeze.py` + `app/research/foundry_ledger.py` (existing, no new module).
  Serving endpoint: `GET /research/desk/micro/foundry` (`freeze_integrity` key).
- `hermetic_oracles`: `{outcome_types_present: str[], denominator_consistent_across_rows: bool,
  canonical_order_preserved: bool, all_blocked_epoch_completed: bool,
  all_killed_epoch_completed: bool, multi_survivor_preserved_all: bool,
  crash_resume_at_scale_verified: bool, protected_data_trip_fails_closed: bool,
  evidence_class_immutable: bool, suite_source: str}`. Computing module: NEW
  `app/research/foundry_hermetic_summary.py` (a summary builder over the existing
  `tests/test_foundry_hermetic_epoch.py` suite; introduces no second oracle implementation). Serving
  endpoint: `GET /research/desk/micro/foundry` (`hermetic_oracles` key).

## OUT OF SCOPE

- Real source-registry authoring (the 11 required objects, §1.1/§1.2), real epoch generation, the
  freeze commit, the real committed `reports/hypothesis-foundry/source-registry-audit.md`, and any
  real candidate outcome read (Binding Execution Order steps 6-8; J-06/J-07) — illegal until step 5
  (this iteration) is complete, and J-02's step 5b specifically depends on the real audit report
  (`state/assumptions.md` iter-4).
- The Epoch/Manifest (J-06) and Runner/Checkpoint (J-07) subsections of the Foundry panel — those
  homes stay `[PLANNED, not yet built]` until their journeys are legal to attempt.
- Widening `generate_freeze_set`'s same-directory-only transitive import scan — a disclosed, lesser
  carried item that does not block this iteration's fixture freeze-record view.
- §4.4's optional descriptive seam — no TC this iteration requires it.
- The optional read-only MCP proxy (`desk_micro_foundry`) — explicitly deferrable per the goal.
- Any change to `scout.py`, `micro_features.py`, `micro_observer.py`, `micro_join.py`, `referee_*.py`,
  or `config_fingerprint` — all frozen foundation, untouched this iteration.
- Raising the session's `--max-iter` cap from 60 to 80 — an operator decision, carried in NOTES.

## DEFINITION OF DONE

- [ ] J-03 passes via browser-qa-agent: all 5 interpreter fixture scenarios visible and correct on
      `/desk` (TC-4, TC-5, TC-6, TC-7)
- [ ] J-04 passes via browser-qa-agent: all 6 freeze/family/integrity fixture checks visible and
      correct on `/desk` (TC-8, TC-9, TC-10, TC-11, TC-12, TC-13)
- [ ] J-05 passes via browser-qa-agent: the hermetic oracle summary's full coverage visible and
      correct on `/desk` (TC-14, TC-15)
- [ ] J-02's steps 1-4 and step 5's fixture-immutability check are demonstrated via browser-qa-agent
      (TC-1, TC-2, TC-3); step 5's real-audit-report inspection is explicitly out of scope pending
      J-06 (`state/assumptions.md` iter-4) — the evaluator may still score J-02 `partial` for that
      reason alone, which is not a defect in this iteration's execution
- [ ] Required-still-passing J-01 replay (`journey-scripts/J-01.json`) still passes unchanged (TC-19)
- [ ] Repair 1 closed: `SourceRecord.alternatives` fail-closed lint rejects a nonexistent, wrong-
      family, or self-referential sibling id (TC-16)
- [ ] Repair 2 closed: `foundry_runner.run_one_candidate`'s crash-path branch raises
      `FoundryResumeIdentityMismatch` on `manifest_hash` drift, not only `econ_floor_bps` drift
      (TC-17)
- [ ] QA report for this iteration cites J-01's evidence as the browser regression-replay results
      file, not the backend pytest run (auditor T5, carried since iter-3)
- [ ] No anti-goal violation introduced: no real Foundry candidate outcome read anywhere; no second
      statistical/oracle rail; no Foundry trial written to the Scout ledger; no sealed/protected
      identity ever appears in the new payload; every fixture subsection visibly labelled fixture-
      scope; no guard weakened or bypassed
- [ ] Unit tests pass; no regressions — full backend suite and `tsc --noEmit` stay green, GET route
      never executes compiler/interpreter/family/freeze/runner machinery per request (TC-18, TC-19)
- [ ] Dev handoff written at `docs/handoffs/goal-hypothesis-foundry-iter-4-dev.md`

## TESTING REQUIREMENTS

- Browser: J-02 (steps 1-4 + step 5a), J-03 (steps 1-5), J-04 (steps 1-6), J-05 (steps 1-6); replay
  J-01 (regression, `journey-scripts/J-01.json`).
- Unit/integration: `sources_compiler`/`interpreter_fixtures`/`freeze_integrity`/`hermetic_oracles`
  payload builders each reuse the SAME hermetic fixtures the existing `test_foundry_*.py` files
  already define (no new fixture content invented for the route); `foundry_hermetic_summary.py`
  genuinely reads `test_foundry_hermetic_epoch.py`'s outcomes rather than a hand-typed duplicate;
  `SourceRecord.alternatives` lint; `foundry_runner` crash-path `manifest_hash` check; a route-level
  test proving the GET handler does not call any compiler/interpreter/family/freeze/runner function
  directly (e.g. via a monkeypatch/spy asserting zero calls, or by asserting the served object is a
  cached/frozen singleton across repeated requests).
- Error cases: `alternatives` lint raises on (a) a nonexistent sibling `source_id`, (b) a sibling
  outside the record's `foundry_family_key`, (c) a self-referential id; `run_one_candidate`'s crash
  path raises `FoundryResumeIdentityMismatch` when `manifest_hash` differs from the pinned intent row
  even when `econ_floor_bps` matches; the over-cap family fixture blocks WHOLE (not truncated/split);
  the unsupported-ordered-relation interpreter fixture produces a typed block, never a guessed lag.

Test-first contract — TC-1..TC-19:

- TC-1: given the 7 hermetic J-02 source fixtures, when `GET /research/desk/micro/foundry` is
  called, then `sources_compiler.fixtures` has exactly 7 entries and each entry's `disposition`
  matches the value `test_foundry_source_registry.py`/`test_foundry_compiler.py` already assert for
  that same fixture.
- TC-2: given the compileable natural-boundary scalar fixture, when its `candidate_spec` is
  inspected, then every §3 field (`population`, `coordinates`, `relation`, `outcome`,
  `economic_floor_rule`, `foundry_family_variant_count`) is non-null and `candidate_spec_hash`
  equals the value `foundry_compiler.compile_sources` produces for the identical fixture input.
- TC-3: given the same fixture compiled twice with two different injected `extra` values, when
  `sources_compiler.immutability_proof` is inspected, then `candidate_spec_hash_a` equals
  `candidate_spec_hash_b` and `hashes_equal` is `true`.
- TC-4: given the immediate-scalar interpreter fixture, when the
  `interpreter_fixtures.scenarios[kind="immediate_scalar_equivalence"]` entry is inspected, then
  `foundry_screen` and `direct_scout_screen` are byte-identical and `screens_equal` is `true`.
- TC-5: given the deferred `refill_consistent` fixture with at least one unresolved anchor, when the
  matching scenario entry is inspected, then `unresolved_excluded_count` is greater than 0 and
  `outcome_start_candidate` equals `outcome_start_comparator` for every resolved anchor pair.
- TC-6: given the mirrored support-long/resistance-short fixture pair, when inspected, then each
  side's rendered `CandidateSpec`-derived sidedness is `long` or `short` respectively, shown before
  any outcome field is populated.
- TC-7: given the unsupported-ordered-relation fixture, when inspected, then `block_reason` equals
  the applicable typed block (e.g. `BLOCKED_UNSUPPORTED_RELATION`) and `foundry_screen` is `null`.
- TC-8: given the 1/multiple/at-cap/over-cap family fixtures, when
  `freeze_integrity.family_denominator_fixtures` is inspected, then the `over_cap` entry has
  `over_cap_blocked_whole=true` and every entry has `denominator_visible_before_result=true`.
- TC-9: given a fixture family already frozen, when a late-insertion fixture attempt replays, then
  `freeze_integrity.late_insertion_refused=true` and the family's `variant_count` is unchanged.
- TC-10: given identical fixture generation inputs run twice, when
  `freeze_integrity.generation_replay` is inspected, then `identical_rerun_verified=true`; given one
  changed input, `drifted_rerun_refused=true`.
- TC-11: given the fixture freeze record, when `freeze_integrity.freeze_record` is inspected, then
  `freeze_set_target_path` equals `"docs/hypothesis-foundry/freeze-set.json"` and `freeze_set_hash`
  equals a fresh recomputation via `foundry_freeze.generate_freeze_set` over the same fixture module
  set.
- TC-12: given a simulated first-read lock followed by (a) a pinned freeze-set path hash change,
  (b) dirty Goal Mode session/handoff files, and (c) a changed non-scientific UI-only file outside
  the freeze set, when `freeze_integrity.first_read_lock` is inspected, then `hash_drift_refused=true`
  for (a), `session_dirt_ignored=true` for (b), and `non_science_file_exempted=true` for (c).
- TC-13: given a completed fixture terminal row followed by an exact-duplicate replay, a conflicting
  replay, and a concurrent second-runner attempt, when `freeze_integrity.replay` is inspected, then
  `idempotent=true`, `conflicting_replay_refused=true`, and `concurrent_runner_refused=true`.
- TC-14: given the composite hermetic epoch fixture, when `hermetic_oracles` is inspected, then
  `outcome_types_present` includes every named outcome type from J-05 step 1 and
  `denominator_consistent_across_rows=true`.
- TC-15: given the all-blocked, all-killed, multi-survivor, crash-resume-at-scale, and protected-
  data-trip hermetic fixtures, when `hermetic_oracles` is inspected, then
  `all_blocked_epoch_completed`, `all_killed_epoch_completed`, `multi_survivor_preserved_all`,
  `crash_resume_at_scale_verified`, `protected_data_trip_fails_closed`, and
  `evidence_class_immutable` are all `true`.
- TC-16: given a `SourceRecord` whose `alternatives` names (a) a nonexistent `source_id`, (b) a
  sibling outside its `foundry_family_key`, or (c) its own `source_id`, when the alternatives lint
  runs, then it raises in all three cases.
- TC-17: given an intent-without-terminal row recorded under `manifest_hash="m1"`, when
  `run_one_candidate` is invoked again for the same `candidate_spec_hash` with `manifest_hash="m2"`
  (matching `econ_floor_bps`), then it raises `FoundryResumeIdentityMismatch`.
- TC-18: given `/desk` opened in a browser with the Hypothesis Foundry panel expanded, when each of
  the four new subsections is opened, then `foundry-sources-compiler`, `foundry-interpreter-
  fixtures`, `foundry-freeze-integrity`, and `foundry-hermetic-oracles` are all visible and each
  displays an explicit "HERMETIC FIXTURE" label distinct from `foundry-era-open-baseline`.
- TC-19: given the full backend suite, `tsc --noEmit`, and two repeated `GET
  /research/desk/micro/foundry` calls, when they are run after this iteration's changes, then the
  suite reports `0 failed`, `tsc` reports `0` errors, `config_fingerprint` still equals
  `08e471b10130e1e2`, and the two GET responses' `sources_compiler`/`interpreter_fixtures`/
  `freeze_integrity`/`hermetic_oracles` payloads are byte-identical (proving no per-request
  recomputation).

## NOTES

- Depth is `full` both because the evaluator's binding recommendation for this iteration says so and
  because Full trigger 1 independently applies (see metadata) — no conflict to resolve.
- Two ambiguities logged to `state/assumptions.md` (iter-4): J-02 step 5's audit-report dependency on
  J-06, and J-04 step 4's real-path naming inside a fixture-scoped step. Both are BINDING readings for
  this iteration; do not re-litigate without a `docs/goal.md` change.
- Applying `lessons.md` iter-3 (twice): verify by grep/read that `foundry_hermetic_summary.py` (or
  wherever the `hermetic_oracles` builder lives) actually reads `test_foundry_hermetic_epoch.py`'s own
  computed results — never a second hand-typed assertion of "these outcomes exist" — and that any
  crash-simulation claim in the new fixture views actually discards state the mechanism holds
  (mirroring the resume-identity fixes' own discipline).
- The QA report correction (auditor T5, DEFINITION OF DONE item) is a process fix, not a code change:
  whichever agent writes this iteration's QA/evaluation report must cite J-01's evidence as
  `reports/phase-...-regression-replay-results.md` (the browser replay), never the backend pytest run.
- Operator decision, unchanged from iter-0/1/2/3: the session's `session.json` iteration cap is 60;
  `docs/goal.md` recommends `--max-iter 80`. Not agent-fixable.
