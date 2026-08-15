# goal-referee-iter-10 Frontend Handoff

**Phase:** goal-referee-iter-10
**Date:** 2026-08-15
**Agent:** developer
**Status:** complete

## What Was Built

Two new `CollapsibleSection`s on `/desk`, rendered directly below the shipped Referee Registry
section and below every other shipped section -- the era's final two Referee panels.

### Referee Adjudications

- `RefereeAdjudicationsSection` fetches `GET /research/desk/referee/adjudications` on first
  expand, plus `GET /research/desk/referee/registry` (to cross-reference each entry's own
  `null_spec_id`/`test_spec_id`, which the adjudications response itself does not carry -- see the
  dev handoff's Known Issues for why).
- Empty state: `EmptyState` with the exact text `"No hypotheses registered."`
  (`data-testid="referee-adjudications-empty"` -- a NEW testid, distinct from the Registry
  section's own `referee-hypotheses-empty`, even though the phase spec mandates the identical
  human-readable string for both panels).
- Populated state: one table row per hypothesis (`RefereeAdjudicationEntryRow`), columns
  Hypothesis / Verdict / Status / Provenance / Fragility triggers:
  - **Verdict** renders as a chip reusing the page's existing, colorless `CHIP_CLASS` (the same
    style already used for band-class/side tokens) -- Design Direction: "no color implies advice."
  - **Status** shows the refusal text when `confirmatory_output_refused`, else the checkpoint date
    when a snapshot exists, else the live `{post_boundary_sessions}/{target_sessions}` pair.
  - **Provenance** shows `evaluation_basis` hash, null spec, test spec, "seed identity" (the
    hypothesis_id -- see Known Issues), attestation pass/fail, and the BH fold `k_star/m (q=...)`.
  - **Fragility triggers** joins the array, or shows an em dash when empty/absent.
  - The served `REFEREE_REGISTER` disclosure text renders verbatim above the table
    (`data-testid="referee-adjudications-register"`).
  - `IntegrityErrorsNote` renders below, mirroring every other section's own convention.

### Referee Runs

- `RefereeRunsSection` hosts two independent sub-blocks: "Null Builds" and "Evaluations."
- **Null Builds**: one `RefereeNullBuildControl` per distinct `null_spec_id` actually present
  across the registry's hypotheses (`distinctRefereeNullSpecIds` -- a plain filter/Set/array
  conversion, deliberately NOT sorted with `.sort()`; this page's own reorder guard
  (`test_the_reorder_guard_deliberately_permits_an_operator_chosen_sort`) permits exactly ONE
  `.sort(`/`.reverse(` call in the whole file, already spent elsewhere -- order here is
  first-encountered in the registry's own served hypothesis order, which is deterministic given an
  unchanged registry response). Each control: a trigger button (`Build Null` / `Building…`), live
  `{done,total}` progress with the pulsing-dot indicator every other compute control uses, an
  inline trigger-error/refusal message, and a cancel button while running.
- **Evaluations**: one `RefereeEvaluateControl` per registered hypothesis, same shape, button label
  `Evaluate` / `Evaluating…`.
- Below each control block, the durable run ledger renders as a `useTableSort`-backed table
  (mirroring `BackscanRunsTable`'s exact structure): `run_id`, spec/hypothesis id, `state`,
  `progress` (unsortable), `started`/`finished` (instant-sorted), `error`. Empty states: `"No
  null-build runs recorded yet."` / `"No evaluation runs recorded yet."`.
- Both compute managers are single-flight PER KEY (`null_spec_id` / `hypothesis_id`), unlike every
  OTHER compute control on this page (a page-wide singleton) -- so their live snapshots and
  trigger/cancel state are `Record<key, ...>` maps. A shared `RefereeComputeControlState` type
  (`{triggering, triggerError, cancelRequested, cancelError}`) covers both managers' identical
  control-state shape rather than four separate flat maps.
- A single-flight second-trigger attempt is refused with the SAME backend-authoritative
  `started: false` check `handleRunBackscanClick` already established, rendered inline via the
  per-key `triggerError` (TC-8).
- Two new polling effects (ONE per manager, not one per key -- each polls every currently-running
  key from a single `setInterval`, stopping and refreshing the run ledger once a key's status
  leaves `running`/`cancelling`), mirroring the Backscan poll's exact shape.

## Files Changed

- `apps/frontend/app/desk/page.tsx`:
  - Imports: 9 new `@/lib/api` functions, 8 new `@/lib/types` type names.
  - `DeskCollapsibleSection` union gains `"refereeAdjudications" | "refereeRuns"`.
  - New components (inserted between `RefereeHypothesesTable` and `ReconcileIndexControl`):
    `RefereeAdjudicationEntryRow`, `RefereeAdjudicationsSection`, `RefereeComputeControlState` +
    `REFEREE_COMPUTE_CONTROL_IDLE`, `distinctRefereeNullSpecIds`, `RefereeNullBuildControl`,
    `RefereeNullBuildsBlock`, `RefereeEvaluateControl`, `RefereeEvaluateControlsBlock`,
    `REFEREE_NULL_RUN_COLUMNS` + `RefereeNullRunRow` + `RefereeNullRunsTable` +
    `RefereeNullRunsSection`, `REFEREE_EVALUATE_RUN_COLUMNS` + `RefereeEvaluationRunRow` +
    `RefereeEvaluateRunsTable` + `RefereeEvaluateRunsSection`, `RefereeRunsSection`.
  - New state (grouped with the existing Referee Registry state block): `refereeAdjudicationsResult`,
    `refereeNullRunsResult`, `refereeEvaluateRunsResult`, `refereeNullCompute`,
    `refereeNullControls`, `refereeEvalCompute`, `refereeEvalControls`.
  - `toggleSection` gains `"refereeAdjudications"`/`"refereeRuns"` branches (plain event-handler
    code, no new effect).
  - New handlers: `handleTriggerRefereeNullBuild`, `handleCancelRefereeNullBuild`,
    `handleTriggerRefereeEvaluate`, `handleCancelRefereeEvaluate`.
  - Two new `useEffect`/`setInterval` polling pairs.
  - Mount site: two new `<section>` blocks inserted between the Referee Registry section's closing
    tag and `</main>`.
- `apps/frontend/lib/api.ts`: `fetchRefereeAdjudications`, `fetchRefereeNullRuns`,
  `fetchRefereeEvaluateRuns`, `triggerRefereeNullsCompute`/`fetchRefereeNullsCompute`/
  `cancelRefereeNullsCompute`, `triggerRefereeEvaluate`/`fetchRefereeEvaluate`/
  `cancelRefereeEvaluate` -- all matching the file's established `{ok, data, error?}` shape and
  `data.detail`-surfacing convention verbatim (no shared request wrapper exists in this file; every
  fetcher hand-rolls the identical boilerplate, matched exactly).
- `apps/frontend/lib/types.ts`: `RefereeBhFold`, `RefereeAttestationQuantities`,
  `RefereeAttestation`, `RefereeAdjudicationSnapshot`, `RefereeVerdict`, `RefereeLiveCoverage`,
  `RefereeAdjudicationEntry`, `RefereeAdjudicationsResponse`, `RefereeNullComputeSnapshot`,
  `RefereeEvaluationComputeSnapshot`, `RefereeNullRun`, `RefereeNullRunsListResult`,
  `RefereeEvaluationRun`, `RefereeEvaluateRunsListResult`.

## Tests Run

- TypeScript: `npm run build` (Next.js production build, strict mode) via an isolated
  `NEXT_DIST_DIR` -- compiled clean, zero type errors. `/desk` builds at 42.8 kB.
- Backend guard tests that scan `page.tsx`'s own source text (all green, see the dev handoff for
  exact counts): `test_desk_ui_guards.py` (arithmetic-on-served-numerics guard, extended + counter-
  tested), `test_desk_refresh_chain_guard.py` (effect/interval/timeout census, re-derived; no-mount-
  trigger scan; the reorder guard that caught my own accidental second `.sort()` call before I
  removed it), `test_copy_discipline.py` (no new copy needed a lexicon change).
- Live verification: real `next dev` server (after `rm -rf .next`) served `/desk` at `200`,
  compiled 624 modules with no errors, and the response HTML contained all three Referee section
  headings. See the dev handoff for the full live-verification narrative and exact PIDs/cleanup.
- No component-level unit tests exist for this page (the project's established pattern is
  backend-side source-introspection guards over the `.tsx` file, not a frontend test runner) -- N/A.

## Known Issues

See the dev handoff's Known Issues section (seed-identity rendering choice, BH fold fields, QA
fixture-seeding left to the browser-qa-agent, no mount-time resume for an already-in-flight job).
One frontend-specific addition:

- **No dedicated verdict-chip visual language exists on this page before this iteration** -- every
  prior "state-ish" field (`hyp.status`, a run's `state`, a compute's `status`) renders as plain
  text with no styling. Verdict chips here reuse `CHIP_CLASS` (already used for band-class/side
  tokens elsewhere), which is the closest existing neutral, non-color-coded idiom -- but it was not
  purpose-built for verdicts, so a future design pass may want a dedicated component if the
  vocabulary grows or needs richer states than a plain pill.
