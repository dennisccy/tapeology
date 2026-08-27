# Goal Iteration 5 — The one real epoch: source registry, manifest, and Git-visible freeze

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** hypothesis-foundry
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict (iter-4) was ESCALATE; per the binding rule this forces full
  depth this iteration with no exceptions, independent of any spec-level judgment call. (This
  iteration's own content would separately warrant scrutiny — the real epoch may be generated only
  once per §8.1 — but the ESCALATE trigger alone is sufficient and is the one actually cited.)
- **Frontend Present:** yes
- **Target journeys:** J-02, J-05, J-06
- **Required-still-passing journeys:** J-01, J-03, J-04
- **Anti-goal reminders:**
  - "No runtime LLM interpretation in the **real manifest-generation command**."
  - "No source record, threshold, direction, family partition, or CandidateSpec chosen because of
    effect, p-value, sample density, or prior Scout outcome."
  - "No candidate invented after the real manifest freezes."
  - "No family splitting to evade the 24-variant cap."
  - "No second real generation epoch."
  - "Frozen foundations stay frozen. The existing `v1` strategy, `default` profile, tape engine
    state vocabulary/thresholds, frozen structure calculations, canonical stores, and archived-era
    behavior remain additive/versioned, never silently mutated."
  - "Single source of truth. Every shared scientific value has one canonical backend owner;
    REST/UI/MCP never independently recompute it."
  - "No browser proof based on fabricated fixture state when a journey claims to show real final
    state; fixture and real views must be visibly distinguished."
  - "No Goal Mode workaround that edits/deletes/xfails a scientific guard merely to pass a journey."
  - Binding Execution Order: "A real candidate outcome read before step 7 is a critical anti-goal
    violation."

## GOAL

Generate and Git-commit the era's one and only real Foundry epoch — the 11 required source
objects each get a real disposition, the compiled family/variant manifest and freeze record exist
at their tracked paths, and the operator can see all of it on the already-registered `/desk` →
Hypothesis Foundry → Epoch / Manifest screen — while carrying three small, already-diagnosed
repairs to the Sources/Compiler and Hermetic Oracles screens and closing the one open anti-goal
finding.

## BACKGROUND

Iter-4's ESCALATE verdict is binding: per the session's own carried lesson, only an ESCALATE
verdict (not a spec-declared `Depth: full`) survives the engine's budget-breach demotion, so this
iteration runs full regardless of its own content. Binding Execution Order step 6 is the next
required stage and the evaluator's own next-step recommendation for two iterations running: "Do the
real registry audit and manifest generation (J-06), with no candidate results read," carrying four
small repairs. J-07 (the real exhaust pass) is explicitly barred from this same iteration by the
goal text itself — "if Goal Mode decomposes J-06 and J-07 together, the runner must refuse until the
next committed iteration rather than bypass the barrier" — so this spec targets J-06 alone as its
one risky/irreversible unit of work (rubric rule 5), bundled only with small, non-risky UI/anti-goal
repairs to the already-partial J-02 and J-05 (rubric rule 3: J-06's audit-report commit is also
J-02's own last remaining blocker, so it is a genuine unblocker, not scope creep).

Two carried lessons apply directly and change how this iteration must be built, not just what:

1. (iter-1/iter-2 lesson) A real recorded artifact under the runtime-scoped `.data/foundry/`
   directory is invisible to the scoped `:8301` QA rig because `resolve_foundry_dir()` derives that
   directory from `TAPEOLOGY_DATASET_DIR`. The tracked `docs/hypothesis-foundry/*.json` and
   `reports/hypothesis-foundry/source-registry-audit.md` files this iteration creates are Git-
   committed repo paths, not runtime-scoped storage — confirmed by reading
   `foundry_source_registry.resolve_foundry_dir()` (only used for the era-open baseline) and
   `micro_routes.get_foundry_dir()`/`get_foundry()` (module-level views + `foundry_dir` Depends).
   The new `epoch_manifest` payload key MUST read the literal repo-relative
   `docs/hypothesis-foundry/` / `reports/hypothesis-foundry/` paths directly — never through
   `get_foundry_dir()`/`resolve_foundry_dir()` — so the scoped QA rig, which checks out the same Git
   worktree, sees the real committed epoch without any `TAPEOLOGY_FOUNDRY_DIR`-style visibility fix.
   Getting this reversed (reading through the dataset-scoped resolver) would silently reproduce the
   exact iter-0/iter-1 failure mode for J-06's entire evidence base.
2. (iter-3 lesson) A "complete factory" suite can pass while never actually feeding a real compiler
   product into a real consumer. The real generation command must call the actual production chain
   — `foundry_source_registry` → `foundry_compiler.compile_sources` → `foundry_freeze.
   generate_or_verify_manifest` → `foundry_freeze.generate_freeze_set` / `build_freeze_record` —
   over the REAL 11-source records, never the existing 7/8-fixture hermetic set `sources_compiler`
   already uses for J-02's fixture view. The two are structurally distinct source lists; do not let
   the real command import or extend the hermetic fixture builder.

Read verified directly this iteration (not re-derived from the digest): `foundry_hermetic_summary.py`
lines ~75-82 and ~183-188 both do `original = scout._two_sided_p; scout._two_sided_p = lambda
...; try: ...; finally: scout._two_sided_p = original` inside a module that is imported and executed
at backend startup (`micro_routes.py`'s `_HERMETIC_ORACLES_VIEW = build_hermetic_oracles_summary()`
module-level call) — i.e. inside the live serving process, not inside a pytest-scoped
`monkeypatch.context()` the way the mirrored test in `test_foundry_hermetic_epoch.py` (lines
254-255, 464-465, 668-669) already does it. This is the open MINOR anti-goal finding and must close
this iteration. The underlying fixture's own docstring already documents that forcing significance
is "the only reliable way to reach [`killed_fragile`] ... hard to hand-tune reliably" — so this may
require either a better-tuned synthetic fixture that clears the two-sided screen on its own, or
sourcing the fragile-case row from a snapshot the pytest suite's own legitimate `monkeypatch`
produces, rather than a straight relocation of the same reassignment.

Also verified directly: `FoundrySourceFixture` (`apps/frontend/lib/types.ts:2989-3014`) already
carries `operative_formula_refs`, `superseded_fields`, and `aliases_lineage_ids` on every fixture —
`SourcesCompilerSubsection` (`apps/frontend/app/desk/page.tsx:7389-7478`) simply never renders them.
This is a frontend-only fix. The "only 1 of 2 sibling records shown" behavior is a *documented,
deliberate* choice (`foundry_compiler.py:411-428`'s own docstring: keeps `fixtures[]` at exactly 7
entries per an existing TC-1 assertion) that two consecutive evaluator verdicts have now flagged as
insufficient for J-02 step 2/3's plain reading ("two explicitly-frozen legal variants" — both,
inspectable). By contrast, `FoundryHermeticOracles` (`apps/frontend/lib/types.ts:3112-3123`) has NO
per-row kill-type field and NO best-of-N field at all today — that repair is a genuine backend
addition, not a rendering fix.

## IN SCOPE

### Backend

- [ ] Author the real 11 required source objects (§1.1/§1.2: Study 1, Study 3, Cards 9.3-9.7, the
  Study 1 and Study 3 pilot proxies, plus the explicit exclusions Card 9.1/Study 2, Card 9.2, Cards
  9.8-9.11) as real `SourceRecord`s citing exact quoted spans from the ratified repository text —
  never the existing 7-fixture hermetic set. Run `foundry_compiler.compile_sources` over this real
  batch (real `foundry_source_registry.py`/`foundry_compiler.py` machinery, no new module).
- [ ] Run the fresh-context independent source-registry audit (§1.4) against this real batch —
  verifying decisions (enumeration vs. block, threshold provenance, direction implication, formula
  supersession, proxy aliasing, lineage dedup), not just citations, with no session outcome/history
  artifact visible to the auditor. Commit the result at
  `reports/hypothesis-foundry/source-registry-audit.md`.
- [ ] Add one deterministic real-generation entrypoint (CLI script, following the
  `apps/backend/scripts/record_foundry_era_open_baseline.py` operator-act convention) that: compiles
  the real registry; calls `foundry_freeze.generate_or_verify_manifest` to build the real
  `epoch_id`/family/variant manifest; calls `foundry_freeze.generate_freeze_set` /
  `build_freeze_record` to build the freeze-set and freeze-record; writes
  `docs/hypothesis-foundry/source-registry.json`, `epoch-manifest.json`, `freeze-set.json`,
  `freeze-record.json` at the tracked §8.2 paths; and records the generation's own outcome-access
  census (must be `0`). It must never read a Scout/result/walkforward/Vault/Referee/PnL value.
- [ ] Verify generation replay: re-running the entrypoint with byte-identical inputs verifies/no-ops
  the existing `epoch_id` rather than creating a second one (already hermetically proven machinery —
  confirm it holds against the real artifacts too, non-destructively).
- [ ] Commit all five tracked files (`docs/hypothesis-foundry/{source-registry,epoch-manifest,
  freeze-set,freeze-record}.json`, `reports/hypothesis-foundry/source-registry-audit.md`) to Git in
  one commit — the Git-visible pre-outcome barrier (§8.4). Confirm the real exhaust-runner
  entrypoint still refuses to run (no J-07 outcome read this iteration; see OUT OF SCOPE).
- [ ] `micro_routes.get_foundry()`: replace the hard-coded `"source_registry_hash": None,
  "source_registry_status": "not_yet_generated"` with a read of the real committed
  `docs/hypothesis-foundry/` files (literal repo-relative path — NOT through `get_foundry_dir()`/
  `resolve_foundry_dir()`; see BACKGROUND lesson 1), falling back to the current honest
  not-yet-generated state if the files are absent. Add the new `epoch_manifest` top-level key (see
  Data-contract additions) computed the same way, at module-import time if the files already exist
  at process start (consistent with the router's established GET-never-computes convention), never
  recomputed per request.
- [ ] `foundry_hermetic_summary.py`: remove both `scout._two_sided_p` reassignments from the
  serving-process code path (~lines 75-82, 183-188). No frozen Scout module attribute may be
  reassigned anywhere outside `tests/`, verified by `grep -rn "scout\._two_sided_p\s*=" apps/backend`
  returning zero matches outside `apps/backend/tests/`. The composite hermetic summary must still
  report a genuine `fragility_killed` (LOSO) outcome afterward.
- [ ] `foundry_hermetic_summary.py`: `outcome_types_present` must be derived by reading each
  composite-epoch row's actual terminal `foundry_state` (or equivalent per-row real field), not
  returned from the current hard-coded `{"insufficient": "insufficient", ...}` label dict
  (~lines 303-318).
- [ ] `foundry_hermetic_summary.py` / `build_hermetic_oracles_summary`: add `kill_type_mapping`
  (one entry per composite-epoch row, pairing its outcome label with its own real `foundry_state`)
  and `best_of_n_disclosure` (the family's `n_variants_tried`/threshold values already present in
  each row's `screen_result` payload, per `scout._best_of_n_disclosure`) to the `hermetic_oracles`
  response — read from the existing rows, no new oracle implementation.
- [ ] `foundry_compiler.sources_compiler_hermetic_fixture_view`: surface BOTH sibling records of the
  `fixture-family-horizon-variants` two-variant family as their own `fixtures[]` entries (currently
  only `fixture-variant-a` is a top-level entry per that function's own documented design). Update
  the existing hard-coded "exactly 7 entries" assertion this changes to the new correct count (an
  intentional fixture-completeness fix directed by two consecutive evaluator verdicts, not a guard
  weakening — the assertion's *value* changes, its *meaning* — "every archetype has its own visible
  record" — does not).

### Frontend

- [ ] New `/desk` → Hypothesis Foundry → **Epoch / Manifest** subsection (J-06's already-registered
  blueprint home) rendering, verbatim from the new `epoch_manifest` payload: status
  (`not_yet_generated` / `generated_uncommitted` / `committed`), `epoch_id`, `source_registry_hash`,
  `manifest_hash`, `freeze_set_hash`, `freeze_commit`, `outcome_access_census`, the per-source
  disposition list (all 11 required objects), the family/variant manifest (family order, variant
  ordinal, `candidate_spec_hash`, `future_rule_id`, `prospective_root_status` per variant), and a
  reference to the committed `source-registry-audit.md` path. Visibly labelled as the REAL epoch,
  distinct from the four fixture-scope subsections already shipped (reuse the existing
  `CollapsibleSection`/`HermeticFixtureBanner`-adjacent pattern but with a "real epoch" banner
  instead).
- [ ] `SourcesCompilerSubsection`: render `operative_formula_refs`, `superseded_fields`, and
  `aliases_lineage_ids` for every fixture record (fields already on `FoundrySourceFixture`; purely
  additive JSX). Both sibling records of the two-variant family now appear as separate `<li>` rows
  once the backend change above ships. Add a visible reference/link to the real committed
  `reports/hypothesis-foundry/source-registry-audit.md` (path text is sufficient; it need not be
  fetched/rendered inline).
- [ ] `HermeticOraclesSubsection`: render the new `kill_type_mapping` list (each row's outcome label
  next to its real `foundry_state`) and the new `best_of_n_disclosure` line.

### New user-facing capability

The operator can open `/desk` → Hypothesis Foundry → Epoch / Manifest and see the era's one real
generated epoch — every required source's real disposition, the real compiled family/variant
manifest, and the freeze identity — plus a corrected Sources/Compiler view (both alias-family
records, full §1.4 field set) and a corrected Hermetic Oracles view (per-row kill-type mapping,
best-of-N line).

### New information displayed

Real (non-fixture) source dispositions for all 11 required source objects; real family/variant
manifest with `candidate_spec_hash`/`future_rule_id`/`prospective_root_status` per variant; real
`epoch_id`/`manifest_hash`/`freeze_set_hash`/`freeze_commit`; the committed audit report reference;
`operative_formula_refs`/`superseded_fields`/`aliases_lineage_ids` on every Sources/Compiler record;
the second alias-family sibling record; per-row kill-type mapping and best-of-N disclosure on the
Hermetic Oracles view.

### New user actions

None (read-only surface per the goal's own Product Shape — "No dedicated mutation page is
introduced").

### UI surface changes

One new subsection (`/desk` → Hypothesis Foundry → Epoch / Manifest) and additive field rendering
inside two already-shipped subsections (Sources/Compiler, Hermetic Oracles). No new page, no nav
change.

### Product surface delta

The Hypothesis Foundry panel on `/desk` goes from "four hermetic-fixture demonstrations only" to
"four hermetic-fixture demonstrations plus one real, Git-frozen epoch" — the first genuinely
irreversible scientific artifact of this era becomes operator-visible.

### Blueprint conformance

Lives entirely under the already-registered Information Architecture home
`/desk` → Hypothesis Foundry → Epoch / Manifest (blueprint.md Feature/journey homes table, J-06
row) and the two already-registered Sources/Compiler and Hermetic Oracles homes. No nav/IA change;
`blueprint.md` updated additively (new Data Contract row + iteration note), no
`blueprint.reapproval-requested` needed.

### Data-contract additions

- `epoch_manifest` (NEW top-level response key) — computed by the already-registered
  `foundry_source_registry.py` + `foundry_compiler.py` + `foundry_freeze.py` (all reused, no new
  module), served by `GET /research/desk/micro/foundry` (`epoch_manifest` key), reading the literal
  Git-tracked `docs/hypothesis-foundry/*.json` paths directly (never through
  `get_foundry_dir()`/`resolve_foundry_dir()`). Exact shape:
  - `status: "not_yet_generated" | "generated_uncommitted" | "committed"`
  - `epoch_id: str | null`
  - `source_registry_hash: str | null`
  - `manifest_hash: str | null`
  - `freeze_set_hash: str | null`
  - `freeze_commit: str | null`
  - `config_fingerprint: str | null`
  - `outcome_access_census: int` (must be `0` whenever `status != "not_yet_generated"`)
  - `source_dispositions: list[{source_id: str, disposition: str (one of the closed §7.1
    vocabulary), lineage_refs: tuple[str, ...], alias_refs: tuple[str, ...]}]` — one entry per
    required source object (11)
  - `families: list[{foundry_family_id: str, family_order: int, variant_count: int, variants:
    list[{variant_id: str, variant_ordinal: int, candidate_spec_hash: str, future_rule_id: str,
    prospective_root_status: str}]}]`
  - `source_registry_audit: {path: str, committed: bool}`
  This also replaces the existing hard-coded top-level `source_registry_hash: None` /
  `source_registry_status: "not_yet_generated"` fields in `get_foundry()`'s response with real
  values sourced from this same read (no second calculation path for the same value).
- `hermetic_oracles.kill_type_mapping: list[{outcome_label: str, foundry_state: str}]` (extends the
  already-registered `hermetic_oracles` row; same module/endpoint, new field) — length 7, one per
  composite-epoch row, `foundry_state` read from that row's real terminal result.
- `hermetic_oracles.best_of_n_disclosure: {n_variants_tried: int, threshold_bps: float}` (extends
  the already-registered `hermetic_oracles` row; same module/endpoint, new field) — sourced from the
  composite epoch rows' existing `screen_result.best_of_n_disclosure` payload (all rows share one
  family, so one representative value is correct; the DoD test verifies it is identical across all
  seven rows, not merely present).
- `operative_formula_refs` / `superseded_fields` / `aliases_lineage_ids` on `sources_compiler`
  fixtures and the second alias-family sibling record are NOT new Data Contract values — they were
  already computed and already part of the registered `sources_compiler` row; only their on-screen
  rendering was incomplete. No blueprint row change needed for these.

## OUT OF SCOPE

- J-07 (the real deterministic exhaust pass) — explicitly barred from this iteration by the goal's
  own text: "if Goal Mode decomposes J-06 and J-07 together, the runner must refuse until the next
  committed iteration rather than bypass the barrier." The real exhaust-runner entrypoint must
  refuse to run this iteration; do not invoke it even to "test" the refusal path against real data.
- J-08 (final read/regression pass) — depends on J-07.
- Any real Scout/`screen_candidate` outcome read against real diagnostic-corpus data.
- The optional read-only MCP proxy (`desk_micro_foundry`) — deferrable per the goal.
- Any change to `scout.py`'s frozen decision vocabulary, constants, or statistical rail (only the
  removal of the temporary runtime reassignment is in scope, not a rail change).
- Raising the session `--max-iter` cap or the per-iteration wall-clock budget — operator/process
  decisions carried in iteration-state, not a spec item.
- A second real generation epoch under any circumstance, including as a "fix" if the first real
  generation is later found imperfect — per §8.3/anti-goals, a flawed but honest real epoch is
  handled at the integrity-halt/owner level, not by silently regenerating.

## DEFINITION OF DONE

- [ ] J-06 passes via browser-qa-agent: `/desk` → Hypothesis Foundry → Epoch / Manifest shows the
  real per-source dispositions (all 11), the real family/variant manifest, freeze identities, and
  the committed audit-report reference; the five tracked artifacts exist in a single Git commit that
  is an ancestor of `HEAD`; the outcome-access census is `0`; the real exhaust-runner entrypoint
  still refuses to run.
- [ ] J-02 re-verified via browser-qa-agent: Sources/Compiler subsection now shows
  `operative_formula_refs`/`superseded_fields`/`aliases_lineage_ids` on every record, both
  alias-family sibling records, and the committed audit-report reference.
- [ ] J-05 re-verified via browser-qa-agent: Hermetic Oracles subsection shows the per-row
  `kill_type_mapping` and the `best_of_n_disclosure` line; `outcome_types_present` is proven
  row-derived, not hard-coded.
- [ ] The open MINOR anti-goal (production reassignment of `scout._two_sided_p`) is closed: zero
  matches for `scout\._two_sided_p\s*=` outside `apps/backend/tests/`.
- [ ] Required-still-passing journeys J-01, J-03, J-04 remain green (deterministic replay +
  browser-qa fallback).
- [ ] No new anti-goal violation introduced; the carried MINOR finding's disposition moves to
  `total=1/resolved=1/blocking=0/critical=0` (matching the session's established disposition-count
  format) after this iteration's fix.
- [ ] Unit tests pass; zero regressions; zero new xfail/skip.
- [ ] Dev handoff written at `docs/handoffs/goal-hypothesis-foundry-iter-5-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-02 (Sources/Compiler), J-05 (Hermetic Oracles), J-06 (Epoch/Manifest, new). Replay:
  J-01, J-03, J-04.
- Unit/integration: real registry compilation over the 11 required source objects; real manifest/
  freeze-set/freeze-record generation and replay-verification; `get_foundry()`'s new `epoch_manifest`
  read path; `kill_type_mapping`/`best_of_n_disclosure` computation; `outcome_types_present`
  row-derivation; grep-based anti-goal regression guard for `scout._two_sided_p` reassignment
  outside `tests/`.
- Error cases: a second generation attempt with drifted inputs must refuse, not silently create
  `epoch_2`; a real-evaluation invocation attempted before the freeze commit is an ancestor of `HEAD`
  must refuse; a missing/absent tracked artifact must degrade `epoch_manifest.status` to
  `not_yet_generated` honestly, never fabricate a value.

Test-first contract:

- TC-1: given the ratified §1 source scope (11 required source objects) and the real deterministic
  generation command, when it is run fresh-context, then `docs/hypothesis-foundry/source-
  registry.json` contains exactly 11 source records, each with exactly one disposition from the
  closed §7.1 vocabulary, and no required object is absent.
- TC-2: given Card 9.1/Study 2's prior-kill history, when the real registry is generated, then Card
  9.1's disposition is exactly `EXCLUDED_PREVIOUSLY_KILLED` and no field of its record recompiles,
  reverses, or rethresholds Study 2.
- TC-3: given Card 9.2's unmet delta-by-price binning prerequisite, when the real registry is
  generated, then Card 9.2's disposition is exactly `EXCLUDED_PREREQUISITE_UNMET`.
- TC-4: given Cards 9.8-9.11's closed catalog gate, when the real registry is generated, then each of
  Card 9.8, 9.9, 9.10, and 9.11 has disposition exactly `EXCLUDED_GATE_CLOSED`.
- TC-5: given the Study 1 and Study 3 frozen pilot-proxy declarations, when the real registry is
  generated, then each proxy record's disposition is `ALIASED_PROXY_ONLY` under its corresponding
  parked study id, with its existing `do_not` restriction preserved on the record.
- TC-6: given the real generation command executes end to end, when its outcome-access tripwire is
  inspected, then the recorded outcome-access census equals `0`, and `GET
  /research/desk/micro/foundry`'s `epoch_manifest.outcome_access_census` serves that same value.
- TC-7: given the real compiled family/variant manifest, when a browser operator opens `/desk` →
  Hypothesis Foundry → Epoch / Manifest, then the screen shows, read verbatim from the endpoint:
  `epoch_id`, `source_registry_hash`, `manifest_hash`, `freeze_set_hash`, `freeze_commit`, and for
  every compiled family its `family_order`, and each variant's `variant_ordinal`,
  `candidate_spec_hash`, `future_rule_id`, and `prospective_root_status`.
- TC-8: given the fresh-context independent source-registry audit is run without session outcome/
  history artifacts, when it completes, then `reports/hypothesis-foundry/source-registry-audit.md`
  exists, is committed to Git, addresses enumeration-vs-block/threshold-provenance/direction-
  implication/formula-supersession/proxy-aliasing/lineage-dedup for each of the 11 source objects,
  and the Sources/Compiler subsection shows a reference to that path.
- TC-9: given the four tracked JSON artifacts and the audit report are generated this iteration, when
  `git log --name-only` is inspected, then all five files appear together in one commit that is an
  ancestor of `HEAD`, and invoking the real exhaust-runner entrypoint still returns a refusal (no
  J-07 outcome read occurs).
- TC-10: given the just-committed manifest and byte-identical inputs, when the generation command is
  re-run, then it returns/verifies the existing `epoch_id`/`manifest_hash` unchanged and does not
  create a second `epoch_id`.
- TC-11: given the `sources_compiler` fixture set's two-variant alias family, when a browser operator
  opens `/desk` → Hypothesis Foundry → Sources/Compiler, then both `fixture-variant-a` and
  `fixture-variant-b` appear as their own visible record rows, each showing its
  `operative_formula_refs`, `superseded_fields`, and `aliases_lineage_ids` values on screen.
- TC-12: given every other Sources/Compiler fixture record (natural-boundary, magnitude-word, proxy,
  unsupported-stat, alias, directionless), when the same screen is inspected, then each record's
  `operative_formula_refs`, `superseded_fields`, and `aliases_lineage_ids` values are visible on
  screen, with an empty array/object rendered as an explicit empty state rather than omitted.
- TC-13: given the composite hermetic epoch's seven terminal rows (insufficient/null/direction/
  concentration/economic/fragile/survive), when a browser operator opens `/desk` → Hypothesis
  Foundry → Hermetic Oracles, then each row's own real `foundry_state` is shown next to its outcome
  label in the `kill_type_mapping` list, and a `best_of_n_disclosure` line showing
  `n_variants_tried`/`threshold_bps` is visible.
- TC-14: given a test that mutates one composite-epoch fixture row's terminal outcome, when
  `outcome_types_present` is recomputed, then its returned value changes accordingly, proving it is
  derived by reading each row's actual state and not returned from a hard-coded dict.
- TC-15: given `foundry_hermetic_summary.py` runs inside the live backend process, when the codebase
  is grepped for `scout\._two_sided_p\s*=` outside `apps/backend/tests/`, then zero matches are
  found, and the hermetic suite still reports a genuine `fragility_killed` entry in
  `kill_type_mapping`.
- TC-16: given the full existing Foundry hermetic suite (source registry, compiler, interpreter,
  family, freeze, ledger, runner, composite oracle, route tests) plus the pre-existing Rapid
  Microscope / Referee regression suite, when the suite runs after this iteration's changes, then
  all tests pass with zero new xfail/skip and zero deleted assertions.
- TC-17: given J-01/J-03/J-04's stored golden replay scripts, when the deterministic replay lane
  re-runs them this iteration, then all three journeys' steps still pass with no regressed step.
- TC-18: given the scoped `:8301` QA rig checked out at the same commit as the real generation, when
  it serves `GET /research/desk/micro/foundry`, then `epoch_manifest`'s values match the operator's
  real-store values byte-for-byte, because both read the same Git-tracked `docs/hypothesis-foundry/`
  paths rather than a `TAPEOLOGY_FOUNDRY_DIR`-scoped runtime directory — so no QA-rig-provisioning
  fix is needed for this journey's evidence.

## NOTES

- This iteration performs the one real epoch generation this era permits (§8.1: "at most one real
  `epoch_id`"). It is not a destructive migration and needs no operator-only isolation control — the
  generation command's own already-hermetically-proven idempotency/drift-refusal machinery
  (`generate_or_verify_manifest`, `verify_freeze_set_unchanged`) is the safety mechanism, and the DoD
  requires the app running for browser QA regardless. If the generation command is interrupted or
  produces an unexpected result mid-iteration, re-run it with byte-identical inputs to verify/no-op —
  never hand-edit the generated JSON, and never treat a bad first attempt as license to try a second
  *different* epoch.
- Three assumption-ledger entries were logged for this iteration's interpretive calls (design
  decisions on QA-rig read path, freeze-set path rendering scope, and the two-variant-family fixture-
  count change) — see `runs/goal-session-hypothesis-foundry/state/assumptions.md`, entries dated
  iter-5.
- Every iteration this session has breached its wall-clock budget (iteration-state's own carried
  Process blocker); this iteration's real-source authoring work (quoting exact ratified spans for 11
  objects) is inherently slow and should not be rushed to fit the budget — an honest partial (e.g.
  some sources ending up `BLOCKED_*` because the developer could not find a qualifying ratified
  quote in the time available) is preferable to a fabricated or under-audited quote.
