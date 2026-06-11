# goal-i_will_be_super_rich_with_my_loved_ones-iter-15 Frontend Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-15
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

One new section on `/journal/[id]` plus a one-line grade-chip shade unification. No new pages, no
nav change (per the iter spec UI surface delta).

- **Excursion section — "How far the tape went (R)"** (`JournalDetailView.tsx`), placed under the
  existing execution-checks/grades area, above the verdict timeline. Two **visually separate** blocks
  rendered in fixed order:
  - **"From first confirmation"** (confirmation-anchored population)
  - **"From entry mark"** (entry-anchored population)
  Each present block shows its anchor line — true-clock time (the shared `dd-MM-yyyy HH:mm` formatter
  + local-offset label), mono **reference price**, **R basis** (`R = |reference − invalidation|`), and
  **spread-at-anchor** — and per-horizon rows: the horizon (`10s/30s/60s/120s`), **MFE (R)** in
  emerald and **MAE (R)** in rose (signed, 2 dp, R unit, never currency), the **ternary outcome chip**
  (`+1R first` emerald / `−1R first` rose / `Neither within horizon` slate — labels from the
  taxonomy), and a **TRUNCATED** amber flag where the stream end / a gap cut the horizon short.
- **Honest-absence rendering** (no dishonest zeros):
  - never-confirmed ⇒ the confirmation block reads its explicit not-applicable copy (taxonomy-owned);
  - no entry mark ⇒ the entry block reads its explicit not-applicable copy;
  - the restart-sweep `tracked:false` record ⇒ the whole section reads the not-tracked copy;
  - a pre-v7 thesis (no `excursions` key) ⇒ the section reads the honest-omission "not measured" copy.
- **Copy register:** descriptive, past-tense, R-units only — no currency symbol anywhere, no
  prediction language. An R-basis caption with the spread-cost caveat sits one line under the blocks.
- **Carry-along cleanup (coherence advisory):** the grade-chip emerald shade is unified to
  `bg-emerald-900/40 border-emerald-700` in `JournalTable.tsx`'s `gradeClass` so a `thesis_held` /
  `clean` grade reads with the IDENTICAL emerald on both the journal list and the detail quadrant
  (`JournalDetailView.tsx`'s `outcomeGradeClass`/`processGradeClass` already used that shade).

## Files Changed

- `apps/frontend/lib/types.ts` -- `ExcursionHorizon`, `ExcursionPopulation`, `ThesisExcursions`, `ExcursionTaxonomy`; `excursions?` added to `JournalDetail` and `ResearchTaxonomy`
- `apps/frontend/components/JournalDetailView.tsx` -- the excursion section (`ExcursionsSection`, `ExcursionPopulationBlock`, `ExcursionHorizonRow`) + the ternary-outcome chip color helper + `formatR`
- `apps/frontend/components/JournalTable.tsx` -- grade-chip emerald shade unified with the detail view

## Design System Conformance

- Dark instrument-panel style consistent with the cockpit + journal list/detail: `slate-900/40-50`
  surfaces, `slate-800` borders, mono numerics for all prices / R figures / spreads.
- Color semantics held: emerald = favorable / +1R, rose = adverse / −1R, amber = truncated (the
  absorption/unclear-family amber, reused for the "cut short" caveat), slate = neutral/undetermined.
- All labels come from `GET /research/taxonomy` (`excursions` block) — the frontend hardcodes no
  ternary label, truncated flag, population title, or honest-absence copy; it falls back to a
  humanised id only if the taxonomy has not loaded.
- `data-testid` hooks for browser QA: `detail-excursions`, `excursion-population` (`data-population`,
  `data-present`), `excursion-anchor-time`, `excursion-reference-price`, `excursion-r-basis`,
  `excursion-spread-at-anchor`, `excursion-horizon` (`data-horizon`, `data-outcome`, `data-truncated`),
  `excursion-mfe`, `excursion-mae`, `excursion-outcome-chip`, `excursion-truncated`,
  `excursion-not-applicable`, `excursions-not-tracked`, `excursions-not-measured`,
  `excursions-r-basis-caption`.

## Tests Run

Command: `cd apps/frontend && npm run build` (+ `npx tsc --noEmit`)
Result: build succeeds, type-check clean (exit 0). Routes `/`, `/journal`, `/journal/[id]` compile;
no new business logic in the frontend (it renders the server's verbatim values only).

## Known Issues

- None. The section renders the persisted record verbatim; all states (both populations present, one
  absent, not-tracked, pre-v7 omission) have explicit honest copy. Below-the-fold on `/journal/[id]` —
  browser QA should scroll-into-view or use full-page captures to verify the new section (it sits
  below the execution-checks/grades area).
