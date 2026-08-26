# Goal Iteration 2 — generic interpreter, Scout adapter, family/freeze/ledger machinery; close the QA-rig visibility gap

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** hypothesis-foundry
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — structural/cross-cutting: this iteration builds five new modules together
  (`foundry_interpreter.py`, `foundry_family.py`, `foundry_freeze.py`, `foundry_ledger.py`,
  `foundry_runner.py`, per Binding Execution Order step 3) whose correctness depends on each
  other's interactions — population-symmetric timing feeding the Scout boundary, family-denominator
  freezing feeding the ledger's terminal rows, and ledger-driven checkpoint/resume feeding replay
  refusal — none of which is covered by either J-03's or J-04's own test surface alone, and the
  byte-identical-equivalence proof against the existing frozen `scout.screen_candidate` rail is
  exactly the kind of cross-module failure mode full depth exists to catch.
- **Frontend Present:** no
- **Target journeys:** J-01, J-03, J-04
- **Required-still-passing journeys:** none currently `passing` — 0/8 Foundry journeys have reached
  `passing` yet (J-01/J-02 are `partial`; no golden replay script exists in
  `runs/goal-session-hypothesis-foundry/journey-scripts/` for any of them). Do-not-regress items
  instead: J-01 steps 1-4 (era-transition panel content) and J-02's compile-rule machinery (40
  reviewer-verified tests) — both covered mechanically by the full backend suite + `tsc --noEmit`
  gate in DEFINITION OF DONE, not by journey replay.
- **Anti-goal reminders:**
  - "No family-specific post-freeze extractor/evaluator path for one real candidate. Real
    membership is interpreted generically from CandidateSpec."
  - "No second Foundry statistical decision rail."
  - "No Foundry trial registered into the Scout ledger this era; the Foundry trial ledger is the
    canonical record and must carry the complete Scout screen payload plus both denominator
    contexts where defined."
  - "No unsided Foundry candidate that chooses direction from discovery."
  - "No family splitting to evade the 24-variant cap."
  - "No late variant insertion."
  - "No second real generation epoch."
  - "**Single source of truth.** Every shared scientific value has one canonical backend owner;
    REST/UI/MCP never independently recompute it."
  - "**No lookahead.** Every value is computed only from information legally available at its declared
    time; deferred constructs cannot be served before resolution."
  - "**Deterministic and seeded.** Randomized statistical draws use existing named deterministic
    streams; no wall-clock/unseeded randomness changes research results."
  - "No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a
    journey."
  - "No browser proof based on fabricated fixture state when a journey claims to show real final
    state; fixture and real views must be visibly distinguished."
  - "A real candidate outcome read before step 7 is a critical anti-goal violation."

## GOAL

Build the generic Foundry candidate interpreter, its Scout adapter, the family/denominator
machinery, and the freeze-set/freeze-record/ledger/checkpoint machinery — all hermetic, all proven
byte-identical to the existing frozen Scout decision rail — while closing the QA-rig visibility gap
that has kept J-01's last step from being photographed.

## BACKGROUND

The prior evaluator (`runs/goal-session-hypothesis-foundry/iter-1/eval.md`) explicitly recommended
this exact scope at full depth: "begin the next required stage: the general reader that turns a
frozen candidate description into the existing Scout decision unchanged, plus the family and freeze
machinery (J-03 and J-04)... because that stage touches the frozen decision rail the whole project
rests on." This matches Binding Execution Order step 3 ("Generic interpreter / Scout adapter /
Foundry family + ledger + freeze machinery. Hermetic only."), which is the only legal next step —
step 2 (source registry + `CandidateSpec` schema) shipped in iter-1, and steps 6-8 (real epoch,
freeze commit, exhaust) stay illegal until steps 3-5 are hermetically proven. `iter-1/coherence.md`
was `COHERENCE-PASS`, so this iteration adds new scope rather than consolidating.

This iteration also closes the top active blocker carried in the inlined iteration-state block:
`foundry_source_registry.resolve_foundry_dir()` derives the Foundry directory from
`TAPEOLOGY_DATASET_DIR`, which the scoped `:8301` QA rig points at a throwaway root, so
`GET /research/desk/micro/foundry` serves `era_open_baseline: null` there even though the real
recorded artifact (`apps/backend/.data/foundry/era_open_baseline.json`) is genuine — the evaluator
recomputed all six Referee hashes against it and they matched. `lessons.md` iter-1 names the fix
exactly: "give the rig the REAL artifact (copy it in, or set `TAPEOLOGY_FOUNDRY_DIR`)... planting
invented rig values instead is an explicit anti-goal." This is a small, well-scoped dev/QA-harness
fix (owner: dev, per iteration-state), not itself risky, so it is bundled alongside the one risky
body of work (the interpreter/family/freeze machinery) rather than deferred — consistent with "one
iteration may carry several trivial journeys OR one risky journey."

The second carried blocker — `SourceRecord` missing §1.4 `alternatives`/`source_hash` fields — is
explicitly OUT OF SCOPE here: it does not block J-03 or J-04, and J-02 cannot reach `passing` this
iteration regardless (its UI stays deferred), so fixing it now would not change any journey's score.
It is carried forward to the iteration immediately preceding J-06 (real source authoring), where it
is a hard prerequisite.

No UI ships this iteration. Per the iter-1 assumption-ledger entry, ALL Foundry subsection UI
(Sources/Compiler, Interpreter, Freeze/Integrity fixture views alike) is deferred to the single
consolidated read-surface iteration named in Binding Execution Order step 5. J-03 and J-04's own
acceptance steps are on-screen fixture inspections ("Open a hermetic ... fixture and confirm...");
exactly like J-02 in iter-1, their substance is provable and testable hermetically this iteration,
but neither can reach `passing` via browser-qa until that consolidated UI ships — this is expected,
not a shortfall, and mirrors the J-02 precedent exactly.

## IN SCOPE

### Backend

- [ ] Give the scoped QA rig read access to the real, already-recorded era-open baseline artifact
      without exposing any other real dataset content and without any write to the real
      `apps/backend/.data/` tree: add an optional `TAPEOLOGY_FOUNDRY_DIR` override to
      `resolve_foundry_dir()` (falling back to the current `TAPEOLOGY_DATASET_DIR`-derived path
      when unset) and configure the QA-rig launch to point it at the real `.data/foundry/`
      directory read-only, OR copy the real artifact into the rig's own scoped root before the
      browser pass — either approach is acceptable as long as the served values are the genuine
      recorded ones (never invented) and the store-scope guard stays CLEAN.
- [ ] New module `app/research/foundry_interpreter.py`: population resolution per §4.1 (resolve
      every conditioning component via its frozen `resolution_join_rule`; exclude+count unresolved
      anchors from both cells; `candidate_available_at = max(component.available_at)`;
      `outcome_start` via the existing timing helper; measure the same canonical outcome for
      candidate and comparator; evaluate the frozen membership corner); boolean projection into
      Scout per §4.2 (`feature_value = 1.0/0.0`, transform `threshold`, predicate
      `feature_value >= 1.0`, raw coordinates kept only as descriptive provenance); the §4.1 read
      model (total/eligible/unavailable-by-reason/candidate/comparator counts, usable sessions) for
      hermetic fixtures; typed block (`BLOCKED_UNSUPPORTED_RELATION`) for unfrozen ordered-lag
      fixtures instead of a guessed window.
- [ ] New Scout-boundary adapter (in `foundry_interpreter.py` or a narrowly-scoped sibling): calls
      the existing `scout.screen_candidate` directly on pre-extracted anchors — never the Scout
      registration/ledger path — using the same `family_id`/permutation seed scope as the existing
      direct scalar path, for the byte-identical scalar-equivalence oracle (§3.1/§4.2.1, goal
      Success Criterion 11).
- [ ] New module `app/research/foundry_family.py`: `foundry_family_id` grouping, complete
      pre-outcome variant denominator, hard-cap enforcement (`BLOCKED_VARIANT_EXPLOSION` whole
      family on over-cap — no subset/split/truncate), late-insertion refusal after freeze with no
      denominator change, and the complete frozen denominator passed as `n_variants_tried` to every
      sibling variant's screen regardless of execution progress.
- [ ] New module `app/research/foundry_freeze.py`: deterministic hermetic manifest generation +
      idempotent verify-replay (identical inputs → no second epoch; changed inputs → refusal, never
      silent `epoch_2`); freeze record construction pinning all required hashes (§8.4) plus
      `freeze_commit`-is-ancestor-of-`HEAD` verification; the freeze-set generator (enumerated
      checked-in-style path+sha256 manifest over the Foundry modules, `scout.py`,
      `micro_features.py`, `micro_observer.py`, `micro_join.py`, the sanctioned accessor, and
      snapshot identity/version/parameter sources) that refuses when it cannot prove a local science
      dependency is covered; first-read-lock simulation (post-lock hash mismatch on any pinned path
      → refusal; unrelated Goal Mode session/handoff dirt → no false refusal; non-scientific
      UI-only file outside the enumerated freeze-set → excluded from the lock, no false refusal).
- [ ] New module `app/research/foundry_ledger.py`: hash-chained append-only Foundry trial ledger;
      checkpoint/resume per §9.2 (already-terminal → verify+skip; intent-without-terminal after a
      simulated crash → verify pinned identities, deterministically re-execute, append exactly one
      terminal row; exact duplicate replay → return existing row; conflicting replay → refuse;
      concurrent second runner → single-flight refusal); terminal rows embed/pin the complete
      `screen_candidate` payload plus CandidateSpec/manifest/family-denominator hashes and are never
      written to the existing Scout ledger; deterministic pre-outcome `rule_id = "foundry:" +
      epoch_id + ":" + candidate_spec_hash`, immutable once written; `prospective_root_status`
      (current prospective root for scalar candidates where mechanically defined, else
      `root_deferred_composite`) copied verbatim from the manifest, never invented at terminal time.
- [ ] New module `app/research/foundry_runner.py`: orchestrates the pieces above over a hermetic
      manifest in canonical order (family order, then variant ordinal); mechanical Scout-verdict
      mapping (`killed_insufficient_n` → `EVALUATED_INSUFFICIENT`; every other kill →
      `EVALUATED_KILLED`; `survive` → `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`); order is invariant to
      effect/p-value/n/sibling verdicts — a kill never skips later predeclared variants and a
      survivor never skips later candidates.
- [ ] Unit/integration tests: `test_foundry_interpreter.py`, `test_foundry_family.py`,
      `test_foundry_freeze.py`, `test_foundry_ledger.py`, `test_foundry_runner.py` (naming mirrors
      the existing `test_foundry_*.py` / `test_micro_*.py` convention), covering TC-4..TC-19 below.

### Frontend

None — hermetic backend-only iteration. All Foundry UI (including any Interpreter or
Freeze/Integrity fixture subview) remains deferred to the Binding Execution Order step-5
consolidated read-surface iteration per `state/blueprint.md` and the iter-1 assumption-ledger entry.

### New user-facing capability

None beyond J-01's completion: the operator can now see the real recorded era-open baseline (not
"not recorded yet") when the Hypothesis Foundry panel is inspected in the QA-verified environment.
No new UI ships for J-03/J-04.

### New information displayed

None new — the interpreter/family/freeze/ledger machinery this iteration produces is exercised only
by hermetic tests and is not yet served through `GET /research/desk/micro/foundry` or `/desk`.

### New user actions

None — the Foundry surface remains read-only and unchanged in the UI this iteration.

### UI surface changes

None.

### Product surface delta

None visible to the operator except the QA-rig fix making the already-shipped Hypothesis Foundry
panel header show its real recorded numbers instead of "not recorded yet" wherever the scoped rig
is used.

### Blueprint conformance

No new page or route. All work stays inside the existing `/desk` → `Hypothesis Foundry` panel
per `state/blueprint.md`'s Information Architecture, which already names the homes for J-03
("Interpreter fixtures") and J-04 ("Freeze/Integrity") as future subsections of that one panel — no
subsection ships yet, so nothing new becomes reachable this iteration.

### Data-contract additions

None. This iteration completes the computing modules for Data Contract rows already registered in
`state/blueprint.md` at baseline — row 3 (`CandidateSpec` fields, now including deferred/population
resolution), row 4 (epoch/manifest/freeze identity), row 5 (family/variant/denominator counts), row
6 (unresolved-deferred/eligible/candidate/comparator counts), row 7 (Scout decision/disclosures, via
`foundry_runner.py` calling the unchanged `scout.screen_candidate`), and row 8 (runner
checkpoint/ledger integrity) — moving their named modules from "(planned)" to real, hermetically
proven implementations. No value is newly served through the UI or the real
`GET /research/desk/micro/foundry` response body beyond what iter-1 already ships; `blueprint.md` is
updated only to reflect the module-status change, not a new row.

## OUT OF SCOPE

- Real source-registry authoring (the 11 required objects, §1.1/§1.2), real epoch generation, the
  freeze commit, and any real candidate outcome read (Binding Execution Order steps 6-8; J-06/J-07)
  — illegal until steps 3-5 are complete and hermetically proven.
- Any Sources/Compiler/Interpreter/Freeze fixture UI subview — deferred to the consolidated
  read-surface iteration (Binding Execution Order step 5), matching the J-02 precedent.
- The complete hermetic oracle "factory" suite spanning one mixed epoch (compiled + blocked +
  insufficient + null + wrong-direction + concentration/economic/fragility-killed + survivor
  together) and the protected-data trip fixtures — J-05, Binding Execution Order step 4, next
  iteration.
- `SourceRecord`'s missing `alternatives`/`source_hash` fields — carried forward as an open blocker
  for the iteration immediately preceding J-06; not needed to unblock J-03 or J-04.
- Real economic-floor materialization (§6) — only the already-existing frozen `economic_floor_rule`
  field on `CandidateSpec` (shipped iter-1) is touched; real materialization against a real corpus
  is J-07 territory.
- The optional read-only MCP proxy (`desk_micro_foundry`) — explicitly deferrable per the goal.
- Raising the session's `--max-iter` cap from 60 to 80 — an operator decision, carried in NOTES.

## DEFINITION OF DONE

- [ ] J-01 passes via browser-qa-agent — the Hypothesis Foundry panel shows the real recorded
      era-open baseline (not "not recorded yet") in the scoped QA environment, matching
      `GET /research/desk/micro/foundry` verbatim (TC-1, TC-2)
- [ ] J-03's and J-04's backend/hermetic machinery (generic interpreter, Scout adapter, family
      denominator, freeze-set/freeze-record generation and replay, hash-chained ledger with
      checkpoint/resume/single-flight) is implemented and hermetically tested per TC-4..TC-19; both
      journeys are expected to remain/move to `partial` this iteration, since their own acceptance
      steps are UI fixture-view inspections that stay out of scope here by design (deferred to the
      Binding Execution Order step-5 consolidated read-surface iteration)
- [ ] Store-scope guard stays CLEAN — the QA rig's read of the real era-open baseline artifact never
      writes to any protected real-data file (TC-3)
- [ ] No anti-goal violation introduced (no real Foundry candidate outcome read anywhere this
      iteration; no Scout-rail behavior change; no Foundry trial written to the Scout ledger; no
      guard weakened or bypassed)
- [ ] Unit tests pass; no regressions (full backend suite + `tsc --noEmit` stay green) (TC-20)
- [ ] Dev handoff written at `docs/handoffs/goal-hypothesis-foundry-iter-2-dev.md`

## TESTING REQUIREMENTS

- Browser: J-01 only (`/desk` → `Hypothesis Foundry` panel header now shows the real recorded
  era-open baseline in the scoped QA rig). J-03/J-04 have no browser surface this iteration by
  design — their evidence is the hermetic test suite.
- Unit/integration: interpreter population resolution + timing symmetry + boolean projection +
  scalar equivalence; family denominator + cap + late-insertion refusal; freeze/manifest generation
  replay + drift refusal; freeze-set dependency-coverage refusal; first-read-lock hash-drift
  refusal; ledger checkpoint/resume/single-flight/replay idempotence; canonical-order invariance;
  mechanical Scout-verdict mapping; ledger-not-Scout-ledger boundary; deterministic `rule_id` +
  prospective-root recording.
- Error cases: unfrozen ordered-lag fixture must block (`BLOCKED_UNSUPPORTED_RELATION`), not invent
  a window; over-cap family must block whole, never a subset; late variant insertion must refuse;
  drifted regeneration inputs must refuse rather than silently produce `epoch_2`; a missing/unproven
  local science dependency must refuse freeze-set generation; a post-lock pinned-hash change must
  halt; a conflicting replay must refuse; a second concurrent runner must be rejected by
  single-flight.

Test-first contract:

- TC-1: given the real recorded artifact at `apps/backend/.data/foundry/era_open_baseline.json` and
  the scoped `:8301` QA rig launched with the visibility fix applied, when
  `GET /research/desk/micro/foundry` is called against the rig, then it returns the genuine
  non-null era-open baseline values (matching the iter-1-recorded suite counts and six Referee-
  module hashes), not `null`.
- TC-2: given `/desk` loaded against the fixed scoped rig, when the operator expands
  `Hypothesis Foundry`, then the panel no longer shows "The era-open baseline has not been recorded
  yet." and instead renders the real recorded values, completing J-01 step 5.
- TC-3: given the QA rig now reads the real `.data/foundry/` directory, when the store-scope guard
  runs after the browser pass, then every protected real-data file remains byte-identical to its
  pre-run state (the guard stays CLEAN; no write occurred).
- TC-4: given a hermetic immediate-scalar `CandidateSpec` fixture and the same scalar candidate run
  through the existing direct Scout path with the same `family_id`/permutation seed scope, when both
  are evaluated, then the Foundry adapter's `screen_candidate` decision and statistical payload are
  byte-identical to the direct path's output.
- TC-5: given a hermetic conjunction `CandidateSpec` fixture, when the interpreter evaluates it,
  then the Scout-facing transform is exactly `threshold` with predicate `feature_value >= 1.0`, and
  the raw coordinate values appear only in descriptive provenance output, never as separate features
  passed to `screen_candidate`.
- TC-6: given a hermetic `refill_consistent` deferred-completion fixture with some anchors
  unresolved, when the interpreter resolves population, then unresolved anchors are excluded from
  both candidate and comparator counts and increment the unavailable-by-reason counter, and every
  resolved anchor in both cells shares `outcome_start = max(component.available_at)`.
- TC-7: given mirrored support-long/resistance-short hermetic fixtures, when compiled and evaluated,
  then each `CandidateSpec` carries its predeclared sidedness before evaluation, and an
  opposite-signed result maps to the existing `killed_direction` (`EVALUATED_KILLED`) with no
  Foundry-side re-signing.
- TC-8: given a hermetic fixture requiring an unfrozen ordered-sequence lag, when the interpreter
  attempts compilation, then it returns `BLOCKED_UNSUPPORTED_RELATION` and produces no
  `CandidateSpec`.
- TC-9: given hermetic fixture families of 1, multiple, exactly-`SCOUT_MAX_VARIANTS_PER_FAMILY`, and
  over-cap variant counts, when compiled, then the first three each expose their complete
  denominator before any evaluation, and the over-cap family is `BLOCKED_VARIANT_EXPLOSION` in full
  with zero of its variants proceeding.
- TC-10: given a frozen hermetic family, when a late variant insertion is attempted, then it is
  refused with a typed error and the family's denominator is unchanged.
- TC-11: given identical hermetic generation inputs run twice, when the second run executes, then it
  verifies and returns the existing manifest without creating a second epoch id; given one input is
  then changed, when generation runs again, then it is refused rather than producing `epoch_2`.
- TC-12: given the freeze-set generator run over the current hermetic Foundry module set, when it
  executes, then it produces an enumerated path+sha256 manifest covering the required modules
  (`foundry_compiler.py`, `foundry_interpreter.py`, `foundry_family.py`, `foundry_freeze.py`,
  `foundry_ledger.py`, `foundry_runner.py`, `scout.py`, `micro_features.py`, `micro_observer.py`,
  `micro_join.py`) plus a freeze record pinning manifest/source-registry/spec/schema/compiler/
  interpreter/runner/`scout.screen_candidate`-source hashes and `config_fingerprint`; given a local
  science dependency the scanner cannot prove is covered, when generation runs, then it refuses.
- TC-13: given a simulated first-read row pinning the hermetic freeze hashes has been appended, when
  a pinned freeze-set path is subsequently changed, then the next check refuses with a typed
  integrity halt; given only a Goal Mode session/handoff file (outside the freeze-set) is left
  dirty, when the same check runs, then it does not falsely refuse; given only a non-scientific
  UI-only file outside the enumerated freeze-set changes, when the check runs, then it is treated
  as outside the lock and does not trigger a false refusal.
- TC-14: given a terminal hermetic candidate row already exists, when the exact same evaluation is
  replayed, then it is idempotent and returns the existing row; given a conflicting replay (a
  different frozen identity or screen payload) is attempted, then it is refused; given two runner
  invocations attempt to execute concurrently, then the second is rejected by single-flight.
- TC-15: given an intent-row-without-terminal-result hermetic candidate simulating a crash, when the
  runner resumes, then it verifies the freeze/eligible-corpus/floor identities, deterministically
  re-executes the exact screen, and appends exactly one terminal row with no duplicate.
- TC-16: given a hermetic multi-variant family containing a kill at an earlier ordinal and a
  survivor at a later ordinal, when the runner exhausts the family, then it visits every
  `FROZEN_READY` variant in manifest order and neither the kill nor the survivor causes any later
  predeclared variant to be skipped.
- TC-17: given hermetic fixtures producing each Scout kill type plus a survive, when mapped through
  the Foundry state machine, then `killed_insufficient_n` maps to `EVALUATED_INSUFFICIENT`, every
  other kill (`killed_null`, `killed_direction`, `killed_concentration`, `killed_economic`,
  `killed_fragile`) maps to `EVALUATED_KILLED`, and `survive` maps to
  `DIAGNOSTIC_SURVIVOR_OOS_RULE_FROZEN`, with no other mapping produced.
- TC-18: given a hermetic Foundry trial completes, when its terminal row is inspected, then it
  exists only in the Foundry's own hash-chained ledger and embeds/pins the complete
  `screen_candidate` result plus `CandidateSpec`/manifest/family-denominator hashes, while the
  existing Scout ledger receives zero rows from this trial.
- TC-19: given a hermetic survivor `CandidateSpec`, when its terminal row is written, then `rule_id`
  equals the deterministic pre-outcome `"foundry:" + epoch_id + ":" + candidate_spec_hash` and
  cannot be renamed, and `prospective_root_status` matches the value already fixed pre-outcome in
  the manifest (the current prospective root for scalar mechanisms with defined semantics, else
  `root_deferred_composite`).
- TC-20: given the full backend suite and `tsc --noEmit` run after this iteration's changes, when
  they complete, then all existing Rapid Microscope / Referee / unit / no-lookahead / no-execution
  tests remain green, and `docs/hypothesis-foundry/source-registry.json`,
  `epoch-manifest.json`, `freeze-set.json`, and `freeze-record.json` remain absent from the tree
  (no real epoch artifact was created this iteration).

## NOTES

- Lesson applied (`lessons.md` iter-1, applies to every Foundry journey whose evidence is a read
  surface over a recorded artifact — J-01 step 5, J-02, J-04, J-06, J-07, J-08): the QA-rig fix must
  serve the genuine recorded artifact, never invented values. TC-1/TC-2/TC-3 exist specifically to
  prove this was done the honest way and that it did not touch any protected real-data file.
- Two interpretive calls behind this iteration's scoping are logged in
  `runs/goal-session-hypothesis-foundry/state/assumptions.md` under `## iter-2 — goal-decomposer`:
  (1) whether giving the scoped QA rig read access to the real `.data/foundry/` artifact conflicts
  with the "fixture and real views must be visibly distinguished" anti-goal; (2) how much of the
  exhaust runner's mechanics (§9) belongs to this iteration (checkpoint/resume/single-flight/replay
  and single-family canonical order) versus the full multi-state "complete factory" epoch proof
  reserved for J-05 next iteration.
- Operator decision carried forward from `iter-0/eval.md` and `iter-1/eval.md`: `session.json`
  currently caps this session at 60 iterations; the goal document recommends `--max-iter 80` for
  this era. Not an agent-fixable change; not acted on here.
- `foundry_interpreter.py`, `foundry_family.py`, `foundry_freeze.py`, `foundry_ledger.py`, and
  `foundry_runner.py` operate on hermetic fixture epoch ids only this iteration. They must not read,
  create, or reference any tracked `docs/hypothesis-foundry/` real-epoch artifact — those
  (`source-registry.json`, `epoch-manifest.json`, `freeze-set.json`, `freeze-record.json`) are
  generated for real only at Binding Execution Order step 6 (J-06), by running this iteration's
  machinery against the real ratified sources.
- `state/blueprint.md` is updated this iteration to move Data Contract rows 3, 4, 5, 6, 7, and 8's
  named computing modules from "(planned)" to real (hermetic-fixture-proven); no row is added or
  re-homed, so no `blueprint.reapproval-requested` file is written.
