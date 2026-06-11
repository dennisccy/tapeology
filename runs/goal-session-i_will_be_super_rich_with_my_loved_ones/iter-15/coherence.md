**Verdict:** COHERENCE-PASS

## Coherence Audit — iter-15 (goal-i_will_be_super_rich_with_my_loved_ones-iter-15)

**Iteration:** Evidence layer begins — excursion outcomes (J-58)
**Snapshot SHA:** d5db7aca28eedef539fda4de75615e531c22ffe8
**Diff files changed:** 12 (backend research module, frontend JournalDetailView/JournalTable/types, blueprint update, tests)

---

## Part A — Data Contract check

### Row 20 — Excursion outcomes

**Blueprint contract:** Single owner `apps/backend/app/research/excursions.py`; served ONLY by `GET /research/journal/{id}`.

**Findings:**

- **Single owner confirmed.** The new module `apps/backend/app/research/excursions.py` is the sole computation site. The `ExcursionTracker` class and `compute_and_persist_excursions` function live exclusively there. No other module introduces an independent excursion computation.

- **R-basis shared correctly.** `excursions.py` imports and calls `r_basis` from `marks.py` (line 44: `from .marks import r_basis as _r_basis`). The `marks.py` diff introduces a single top-level `r_basis()` function at the module level and refactors `marks_projection` to call it via `r_basis_value = r_basis(entry.price, thesis.invalidation_price)`. This is the one shared helper — row 27 (realized-R) and row 20 (excursions) consume the same formula. No second R formula was introduced anywhere. This is a clean registry of one shared helper, two registered consumers, exactly as the blueprint specifies.

- **Canonical serving endpoint confirmed.** In `routes.py`, `build_journal_detail` (line ~443) reads `thesis.excursions` verbatim and emits it as `detail["excursions"]` — the ONLY serving path. No new API endpoint was added. No `GET /research/excursions` or similar route appears in the diff. The frontend (`JournalDetailView.tsx`) reads `detail.excursions` from `JournalDetail` — i.e., from `GET /research/journal/{id}` — and renders it verbatim without client-side arithmetic.

- **No client-side recomputation.** The `ExcursionsSection`, `ExcursionPopulationBlock`, and `ExcursionHorizonRow` components in `JournalDetailView.tsx` render `population.mfe_r`, `population.mae_r`, `population.r_basis`, `population.reference_price`, `population.spread_at_anchor`, and `h.outcome` verbatim. The only formatting is `formatR()` (display rounding to 2dp with sign prefix) and `population.r_basis.toFixed(2)` — these are presentation transforms of canonical values, not new computations. No data contract violation.

### Row 24 — Taxonomies + research display copy

**Blueprint contract:** Single owner `taxonomy_payload()` in `taxonomy.py`; served by `GET /research/taxonomy`.

**Findings:** The iteration adds excursion display copy (ternary-outcome labels, truncated label, population titles, not-applicable/not-tracked copy, R-basis caption) to `taxonomy.py` only, via `taxonomy_payload()`. The frontend reads these via `taxonomy?.excursions` passed from `GET /research/taxonomy`. No copy is hardcoded in the frontend components — all strings fall back to humanised ids or a fallback string when taxonomy is unavailable. Contract intact.

### Row 27 — Realized move in R + R basis

**Blueprint contract:** One shared helper; row 27 and row 20 are the two registered consumers (iter-15 additive note).

**Findings:** `marks.py` diff extracts the R formula into a top-level `r_basis()` function. `marks_projection` calls it instead of computing `abs(entry.price - thesis.invalidation_price)` inline. This is a refactor to honour the one-formula rule — not a second computation path. The blueprint's iter-15 additive note explicitly registers both consumers. No violation.

### New displayed values

The iteration displays MFE/MAE in R per horizon, ternary outcomes, spread-at-anchor, TRUNCATED flags, and anchor details. All are read from the persisted excursion record served by `GET /research/journal/{id}`. All are registered under row 20 (excursion outcomes) and row 24 (taxonomy display copy). No displayed value is a synonym or re-derivation of a previously registered value computed via a new path.

**Part A result: no violations.**

---

## Part B — Information Architecture check

### New routes/pages

The iteration introduces **no new routes**. The excursion section is an additive section within the existing `/journal/[id]` page (`JournalDetailView.tsx`). This is confirmed by the diff: only `JournalDetailView.tsx`, `JournalTable.tsx`, and `types.ts` changed on the frontend.

### Canonical home

Blueprint IA row: "J-54, J-58 (execution checks, excursions) → `/journal/[id]` → Journal". The excursion section lands exactly at `/journal/[id]` under the Journal nav entry. This is the pre-approved canonical home.

### Reachability

Nav inspection (`NavBar.tsx`): the persistent top bar has `{ href: "/journal", label: "Journal", enabled: true }`. `/journal` is one click from any page. `/journal/[id]` is one click from `/journal` (the journal table rows link to the detail page, established in iter-13). Total: two clicks. Within the ≤2-click rule.

### No parallel shell / no duplicate home

No new layout, no new nav section, no second home for the excursion entity. The `ExcursionsSection` component renders inside the existing `JournalDetailView` shell.

**Part B result: no violations.**

---

## Part C — Advisory observations (WARN only)

### Grade-chip shade unification

The iteration unifies the emerald grade-chip shade between `JournalDetailView.tsx` (already `bg-emerald-900/40`) and `JournalTable.tsx` (changed from `bg-emerald-900/20` to `bg-emerald-900/40`). This is an explicit carry-along coherence cleanup from the iter-14 evaluator and the iter-15 spec. The result is that the same grade id renders identically on both surfaces. This is a positive coherence improvement, not a concern.

No other advisory observations.

---

## Summary

All changes are correctly scoped to the pre-approved canonical home (`/journal/[id]` under Journal). The single-owner excursion module (`excursions.py`) is the only computation site. The R-basis is one shared helper with two registered consumers. The one canonical serving endpoint (`GET /research/journal/{id}`) is the sole serving path; no second endpoint was added. No new routes. No client-side arithmetic on contract values. No duplicate home. No parallel shell.

**Verdict:** COHERENCE-PASS
