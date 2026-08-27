# goal-hypothesis-foundry-iter-5 Execution Plan

## Alignment check

Directly advances `docs/goal.md`'s Foundry era: this is Binding Execution Order step 6 (the real
registry audit + manifest generation, J-06), which two consecutive evaluator verdicts have named as
the required next step, plus the three small repairs those same verdicts carried forward against
J-02/J-05. No drift from goal.md detected — the phase spec is a faithful, tightly-scoped subset of
§1/§7.1/§8 and the J-02/J-05/J-06 journey text. J-07 (real exhaust) and the optional MCP proxy are
explicitly out of scope both in goal.md and in this spec; the plan below does not touch either.

## What to Build

**Backend — real epoch (J-06)**
- Author 11 real `SourceRecord`s (Study 1, Study 3, Cards 9.3-9.7, the two pilot proxies, plus
  excluded Card 9.1/Study 2, Card 9.2, Cards 9.8-9.11) with exact quoted spans from ratified
  repository text. Source material lives in `docs/research-directions.md` (Card 9.x definitions)
  and the Rapid Microscope Study 1/3 material in `docs/phases/goal-rapid-microscope-iter-1.md`,
  `docs/phases/goal-rapid-microscope-iter-22.md`, `docs/phases/goal-rapid-microscope-iter-24.md`
  and their dev/audit handoffs — quote from these, never invent wording.
- New CLI script `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py`, following the
  `record_foundry_era_open_baseline.py` operator-act convention (argparse, prints a summary to
  stderr, no implicit git operations): builds the 11 records, runs `foundry_compiler.compile_sources`
  over them, calls `foundry_freeze.generate_or_verify_manifest` then `generate_freeze_set` /
  `build_freeze_record`, and writes the four `docs/hypothesis-foundry/*.json` files. It must record
  its own outcome-access census (must be `0`) and must never import/extend
  `sources_compiler_hermetic_fixture_view`'s fixture set.
- **freeze_commit ordering (must-follow, not obvious from the spec text):** `build_freeze_record`
  takes `freeze_commit` as a plain string argument — there is no way to know the hash of a commit
  before it exists. Resolve this the same way §8.4's ancestry check actually works: set
  `freeze_commit` to `git rev-parse HEAD` **at generation time, before the new commit is made**.
  That existing commit is trivially an ancestor of the new commit once the 5 files are committed on
  top of it, and it already reflects the exact frozen science-file state the freeze-set hashes were
  computed from (the generation script must not modify any science file). Do not attempt to
  self-reference the not-yet-created commit; do not commit in two passes to "fix up" the hash.
- Run the fresh-context source-registry audit (§1.4 decisions, not just citations) and write
  `reports/hypothesis-foundry/source-registry-audit.md`.
- One `git add` + `git commit` containing all five tracked files together (TC-9). Verify
  `verify_commit_is_ancestor` holds against the new HEAD, and verify the real exhaust-runner
  (out of scope this iteration) still refuses to run.
- Verify replay: re-run the same CLI with byte-identical inputs and confirm
  `generate_or_verify_manifest` verifies/no-ops rather than minting a second `epoch_id`.

**Backend — route + repairs**
- `apps/backend/app/research/micro_routes.py` `get_foundry()` (currently hard-codes
  `"source_registry_hash": None` / `"source_registry_status": "not_yet_generated"` at lines
  ~794-795): replace with a real read of the literal repo-relative
  `docs/hypothesis-foundry/*.json` / `reports/hypothesis-foundry/source-registry-audit.md` paths —
  **not** through `get_foundry_dir()` / `foundry_source_registry.resolve_foundry_dir()` (that
  resolver is `TAPEOLOGY_DATASET_DIR`-scoped runtime storage for the era-open baseline only, and
  reading through it would reproduce the iter-0/iter-1 QA-invisibility bug for J-06's whole evidence
  base — see `runs/goal-session-hypothesis-foundry/state/assumptions.md` iter-5 entry). Follow the
  existing module-import-time convention (`_SOURCES_COMPILER_VIEW = ...` at line ~771): add
  `_EPOCH_MANIFEST_VIEW = read_epoch_manifest_view()` computed once at import, never per request.
  Missing files must degrade to `status: "not_yet_generated"` honestly, never fabricate a value.
- Add the new `epoch_manifest` top-level key per the Data-contract shape in the phase spec
  (`status`, `epoch_id`, `source_registry_hash`, `manifest_hash`, `freeze_set_hash`,
  `freeze_commit`, `config_fingerprint`, `outcome_access_census`, `source_dispositions[]`,
  `families[]`, `source_registry_audit{path, committed}`).
- `apps/backend/app/research/foundry_hermetic_summary.py`:
  - Remove both `scout._two_sided_p` reassignments (lines ~75-82, ~183-188) from this
    serving-process module. Grep target: `grep -rn "scout\._two_sided_p\s*=" apps/backend` must
    return zero matches outside `apps/backend/tests/`. Source a genuine `fragility_killed` result
    the same way the pytest suite does — via a legitimate `monkeypatch`-produced snapshot/fixture
    (see `tests/test_foundry_hermetic_epoch.py` lines ~254-255/464-465/668-669), or a re-tuned
    synthetic fixture that clears the two-sided screen on its own. Do not relocate the same
    reassignment into a different production function.
  - `outcome_types_present` (currently a hard-coded label dict at lines ~303-318): derive it from
    each composite-epoch row's real `foundry_state` instead.
  - Add `kill_type_mapping` (one `{outcome_label, foundry_state}` entry per of the 7 composite rows)
    and `best_of_n_disclosure` (`{n_variants_tried, threshold_bps}`, read from
    `screen_result.screen_result.best_of_n_disclosure` — same nesting `_composite_epoch` already
    uses at line ~97) to `build_hermetic_oracles_summary()`'s returned dict.
- `apps/backend/app/research/foundry_compiler.py` `sources_compiler_hermetic_fixture_view()`
  (~lines 411-461): surface both `fixture-variant-a` and `fixture-variant-b` as their own top-level
  `fixtures[]` entries instead of only `fixture-variant-a` with `fixture-variant-b` named via
  `alternatives`. Update the two existing "exactly 7 entries" assertions this changes
  (`apps/backend/tests/test_foundry_route_hermetic_views.py` lines 32 and 235) to the new correct
  count (8) — this is a fixture-completeness fix directed by two consecutive evaluator verdicts, not
  a guard weakening: the assertion's value changes, its meaning ("every archetype has its own
  visible record") does not.

**Frontend**
- New `EpochManifestSubsection` component + `CollapsibleSection` entry in
  `apps/frontend/app/desk/page.tsx`'s `HypothesisFoundrySection` (alongside the existing
  Sources/Compiler, Interpreter Fixtures, Freeze/Integrity, Hermetic Oracles sections at
  ~lines 7828-7866; add `openSubsections.has("epoch-manifest")` the same way). Render, verbatim
  from `epoch_manifest`: status, `epoch_id`, the three hashes, `freeze_commit`,
  `outcome_access_census`, the 11-row source-disposition list, the family/variant manifest
  (`family_order`, `variant_ordinal`, `candidate_spec_hash`, `future_rule_id`,
  `prospective_root_status`), and a reference to `source_registry_audit.path`. Use a distinct "real
  epoch" banner (not `HermeticFixtureBanner`, which explicitly says "not the real epoch") so this
  section reads as visibly different from the four fixture sections.
- `apps/frontend/lib/types.ts`: add `FoundryEpochManifest` (and nested `SourceDisposition`/
  `FoundryFamily`/`FoundryVariant` types) matching the new response key; extend
  `FoundryHermeticOracles` with `kill_type_mapping` and `best_of_n_disclosure`; extend
  `DeskFoundryResponse` with `epoch_manifest`.
- `SourcesCompilerSubsection` (`apps/frontend/app/desk/page.tsx` ~lines 7389-7478): add JSX for
  `fixture.operative_formula_refs`, `fixture.superseded_fields`, `fixture.aliases_lineage_ids`
  (fields already exist on `FoundrySourceFixture` in types.ts — purely additive rendering); render
  an explicit empty state (not omission) when any is empty. Add a text reference to
  `reports/hypothesis-foundry/source-registry-audit.md` (path text only, no fetch needed).
- `HermeticOraclesSubsection` (`apps/frontend/app/desk/page.tsx` ~line 7651): render the new
  `kill_type_mapping` list (outcome label next to its `foundry_state`) and the
  `best_of_n_disclosure` line.

## Agents Required

- developer: yes -- implements both the backend real-epoch generation/route/repair work and the
  frontend rendering work described above (single developer agent, standard convention).
- backend-data: yes -- real 11-source authoring, generation CLI, route `epoch_manifest` read path,
  `foundry_hermetic_summary.py` repairs, `foundry_compiler.py` fixture-count fix, the Git commit of
  the five tracked artifacts.
- frontend-ux: yes -- new Epoch/Manifest subsection, Sources/Compiler additive fields, Hermetic
  Oracles kill-type/best-of-N rendering.

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/scripts/generate_hypothesis_foundry_real_epoch.py` -- NEW: real generation CLI entrypoint.
- `docs/hypothesis-foundry/source-registry.json` -- NEW: 11 real source records, generated + committed.
- `docs/hypothesis-foundry/epoch-manifest.json` -- NEW: real family/variant manifest, generated + committed.
- `docs/hypothesis-foundry/freeze-set.json` -- NEW: enumerated path+sha256 manifest, generated + committed.
- `docs/hypothesis-foundry/freeze-record.json` -- NEW: freeze identity record, generated + committed.
- `reports/hypothesis-foundry/source-registry-audit.md` -- NEW: fresh-context independent audit, committed.
- `apps/backend/app/research/micro_routes.py` -- `get_foundry()` real `epoch_manifest` read path; replace hard-coded `source_registry_hash`/`source_registry_status`.
- `apps/backend/app/research/foundry_hermetic_summary.py` -- remove `scout._two_sided_p` reassignment; derive `outcome_types_present`; add `kill_type_mapping`/`best_of_n_disclosure`.
- `apps/backend/app/research/foundry_compiler.py` -- surface both alias-family fixture records in `sources_compiler_hermetic_fixture_view()`.
- `apps/backend/tests/test_foundry_route_hermetic_views.py` -- update the two "exactly 7 entries" assertions to the new count; add tests for `kill_type_mapping`/`best_of_n_disclosure`/`outcome_types_present` row-derivation and the anti-goal grep guard.
- `apps/backend/tests/test_foundry_source_registry.py` / new test file -- TC-1 through TC-10 coverage for the real registry/generation/replay.
- `apps/frontend/lib/types.ts` -- `FoundryEpochManifest` + nested types; extend `FoundryHermeticOracles`, `DeskFoundryResponse`.
- `apps/frontend/app/desk/page.tsx` -- new `EpochManifestSubsection` + `CollapsibleSection`; additive fields in `SourcesCompilerSubsection`; new fields in `HermeticOraclesSubsection`.
- `docs/handoffs/goal-hypothesis-foundry-iter-5-dev.md` -- dev handoff (required by Definition of Done).

## UI Evolution

- New user-facing capability: operator can open `/desk` → Hypothesis Foundry → **Epoch / Manifest**
  and see the era's one real generated epoch (source dispositions, family/variant manifest, freeze
  identity), clearly labelled as real, not fixture.
- New information displayed: real 11-source dispositions; real family/variant manifest with
  `candidate_spec_hash`/`future_rule_id`/`prospective_root_status`; `epoch_id`/`manifest_hash`/
  `freeze_set_hash`/`freeze_commit`; committed audit-report reference; `operative_formula_refs`/
  `superseded_fields`/`aliases_lineage_ids` on every Sources/Compiler record; the second
  alias-family sibling record; per-row kill-type mapping and best-of-N disclosure on Hermetic
  Oracles.
- New user actions: none (read-only surface, per goal.md's own Product Shape).
- UI surface changes: one new subsection under the already-registered Hypothesis Foundry panel;
  additive fields inside two already-shipped subsections. No new page, no nav change.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `CollapsibleSection` pattern already used for the four
  sibling Foundry subsections; reuse the `<li>` row / `<details>` drill-in idioms already used in
  `SourcesCompilerSubsection` for per-source and per-variant rows.
- Layout: nested inside the existing `HypothesisFoundrySection` on `/desk`, appended after Hermetic
  Oracles, consistent with the other four subsections' spacing (`mt-4 space-y-3`).
- Key visual effects: a distinct "REAL EPOCH" banner styled differently from the existing amber/slate
  `HermeticFixtureBanner` (e.g., a differently-colored accent) so operators cannot mistake the real
  epoch view for a fixture demonstration — this distinction is a DoD/anti-goal requirement, not just
  polish.
- States to handle: `not_yet_generated` (should not occur post-commit, but must render honestly if
  the files are somehow absent), `generated_uncommitted`, `committed`; empty-array/empty-object
  fields render an explicit empty state rather than being omitted (same rule as
  `SourcesCompilerSubsection`'s new fields).

## Key Test Scenarios

- TC-1..TC-5: real registry generation yields exactly 11 source records, each with exactly one
  correct disposition (Study 2/Card 9.1 `EXCLUDED_PREVIOUSLY_KILLED`, Card 9.2
  `EXCLUDED_PREREQUISITE_UNMET`, Cards 9.8-9.11 `EXCLUDED_GATE_CLOSED`, both pilot proxies
  `ALIASED_PROXY_ONLY` with `do_not` preserved).
- TC-6: generation's outcome-access census is `0`; `GET /research/desk/micro/foundry`'s
  `epoch_manifest.outcome_access_census` serves the same value.
- TC-7: browser check — `/desk` → Hypothesis Foundry → Epoch / Manifest shows `epoch_id`,
  `source_registry_hash`, `manifest_hash`, `freeze_set_hash`, `freeze_commit`, and every family's
  `family_order`/variant `variant_ordinal`/`candidate_spec_hash`/`future_rule_id`/
  `prospective_root_status`.
- TC-8/TC-9: `reports/hypothesis-foundry/source-registry-audit.md` exists, is committed, and all
  five tracked files appear together in one Git commit that is an ancestor of `HEAD`; the real
  exhaust-runner entrypoint still refuses to run.
- TC-10: re-running generation with identical inputs verifies/no-ops the existing
  `epoch_id`/`manifest_hash` (no second epoch).
- TC-11/TC-12: browser check — both `fixture-variant-a` and `fixture-variant-b` appear as their own
  rows in Sources/Compiler, each showing `operative_formula_refs`/`superseded_fields`/
  `aliases_lineage_ids`; every other fixture record shows the same three fields with explicit empty
  states where applicable.
- TC-13: browser check — Hermetic Oracles shows `kill_type_mapping` (7 rows, each with its real
  `foundry_state`) and the `best_of_n_disclosure` line.
- TC-14: a test mutating one composite-epoch fixture row's terminal outcome changes
  `outcome_types_present`'s returned value (proves row-derivation, not a hard-coded dict).
- TC-15: `grep -rn "scout\._two_sided_p\s*=" apps/backend` returns zero matches outside
  `apps/backend/tests/`; hermetic suite still reports a genuine `fragility_killed` entry.
- TC-16/TC-17: full backend suite + existing Rapid Microscope/Referee regression suite all pass,
  zero new xfail/skip; J-01/J-03/J-04 deterministic replay all still pass.
- TC-18: the scoped `:8301` QA rig's `GET /research/desk/micro/foundry` `epoch_manifest` matches the
  operator's real-store values byte-for-byte (proves the literal-path read, not the
  dataset-dir-scoped resolver, was used).
- Error cases: a second generation attempt with drifted inputs refuses (no `epoch_2`); a real
  evaluation invocation before the freeze commit is an ancestor of `HEAD` refuses; a missing tracked
  artifact degrades `epoch_manifest.status` to `not_yet_generated` honestly.

## Out of Scope (explicitly excluded, matching the phase spec)

- J-07 (real deterministic exhaust pass) and J-08 (final read/regression pass) — barred this
  iteration by goal.md's own text; the exhaust-runner entrypoint must still refuse to run.
- Any real Scout/`screen_candidate` outcome read against real diagnostic-corpus data.
- The optional read-only `desk_micro_foundry` MCP proxy — deferrable.
- Any change to `scout.py`'s frozen decision vocabulary/constants/statistical rail (only removing
  the temporary runtime reassignment is in scope).
- A second real generation epoch under any circumstance.
