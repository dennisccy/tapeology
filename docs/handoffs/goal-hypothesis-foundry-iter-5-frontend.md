# goal-hypothesis-foundry-iter-5 Frontend Handoff

**Phase:** goal-hypothesis-foundry-iter-5
**Date:** 2026-08-27
**Agent:** developer
**Status:** complete

## What Was Built

- **New `Epoch / Manifest` subsection** under `/desk` → Hypothesis Foundry (below the existing
  Sources/Compiler, Interpreter Fixtures, Freeze/Integrity, Hermetic Oracles subsections). Renders
  the real, Git-frozen epoch verbatim from the new `epoch_manifest` response key: status
  (`not_yet_generated` / `generated_uncommitted` / `committed`), `epoch_id`, `source_registry_hash`,
  `manifest_hash`, `freeze_set_hash`, `freeze_commit`, `config_fingerprint`,
  `outcome_access_census`, all 11 required source dispositions with lineage/alias
  cross-references, the compiled family/variant manifest (currently empty — honestly rendered as
  an explicit empty state, "Zero compiled candidates this epoch"), and a reference to the
  committed audit-report path. Carries a NEW, visually distinct "Real Epoch — not a fixture"
  banner (`RealEpochBanner`, emerald accent) — deliberately different styling from the existing
  amber `HermeticFixtureBanner` ("Hermetic Fixture — not the real epoch") used by the four sibling
  subsections, so an operator cannot mistake the one real epoch for a fixture demonstration.
- **`Sources / Compiler` subsection**: now shows `operative_formula_refs`, `superseded_fields`,
  and `aliases_lineage_ids` on every fixture row (fields already existed on the API response;
  only the rendering was missing). Empty values render as explicit empty states (`(none)`, `{}`,
  `[]`) rather than being omitted. Both sibling records of the two-variant alias family
  (`fixture-variant-a`/`fixture-variant-b`) now appear as their own rows (backend change; fixture
  count 7 → 8). Added a text reference to the committed
  `reports/hypothesis-foundry/source-registry-audit.md` path.
- **`Hermetic Oracles` subsection**: now shows the per-row `kill_type_mapping` (each of the 7
  composite outcome labels next to its real `foundry_state`) and the `best_of_n_disclosure` line
  (`n_variants_tried` / `threshold_bps`).

## Files Changed

- `apps/frontend/lib/types.ts` -- new `FoundryEpochManifest`, `FoundrySourceDisposition`,
  `FoundryFamily`, `FoundryVariant` interfaces; `FoundryHermeticOracles` grows
  `kill_type_mapping`/`best_of_n_disclosure`; `DeskFoundryResponse` grows `epoch_manifest`.
- `apps/frontend/app/desk/page.tsx`:
  - New `RealEpochBanner` component (distinct styling from `HermeticFixtureBanner`).
  - New `EpochManifestSubsection` component + its `CollapsibleSection` entry in
    `HypothesisFoundrySection` (after Hermetic Oracles).
  - `SourcesCompilerSubsection`: additive JSX for `operative_formula_refs`/`superseded_fields`/
    `aliases_lineage_ids` on every fixture row, plus an audit-report reference line.
  - `HermeticOraclesSubsection`: additive JSX for `kill_type_mapping` rows and the
    `best_of_n_disclosure` line.

## UI Evolution

- **New user-facing capability**: the operator can open `/desk` → Hypothesis Foundry → Epoch /
  Manifest and see the era's one real generated epoch — every required source's real disposition,
  the real compiled family/variant manifest (currently empty, honestly), and the freeze identity —
  visually distinguished from the four hermetic-fixture demonstrations.
- **New information displayed**: real 11-source dispositions; `epoch_id`/`manifest_hash`/
  `freeze_set_hash`/`freeze_commit`/`config_fingerprint`/`outcome_access_census`; the committed
  audit-report reference; `operative_formula_refs`/`superseded_fields`/`aliases_lineage_ids` on
  every Sources/Compiler record; the second alias-family sibling record; per-row kill-type mapping
  and best-of-N disclosure on Hermetic Oracles.
- **New user actions**: none (read-only surface, no compute button — matches the goal's own
  Product Shape: "No dedicated mutation page is introduced").
- **UI surface changes**: one new nested subsection under the already-registered Hypothesis Foundry
  panel; additive field rendering inside two already-shipped subsections. No new page, no nav
  change.
- **Navigation changes**: none.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit`
Result: 0 errors.

Browser sanity check (see the dev handoff's "Tests Run" section for the full detail): navigated
Chrome (CDP) to `/desk`, expanded Hypothesis Foundry and each of the five subsections, confirmed
via DOM text extraction that every new/changed field renders the values the backend actually
serves, with the two banners visually distinct and the empty-families/empty-field states rendering
honestly rather than being omitted.

## Known Issues

- None frontend-specific beyond what's noted in the dev handoff (the `best_of_n_disclosure.
  threshold_bps` per-row non-identity is a backend data characteristic; the frontend renders
  whatever the backend serves verbatim, with no client-side recomputation).
- The formal browser-qa-agent pass (element screenshots, the full J-02/J-05/J-06 acceptance
  checklist) has not been run by this dev pass — only the lightweight DOM-text sanity check above.
