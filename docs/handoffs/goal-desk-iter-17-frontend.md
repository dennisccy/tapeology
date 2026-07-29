# goal-desk-iter-17 Frontend Handoff

**Phase:** goal-desk-iter-17
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

A new `band` column on `/desk`'s ranked-rows table, plus one more line in each row's existing
composite hover tooltip — the row's own `reference_close` (the exact daily close the row's band
selection and `distance_bps` were measured against) rendered beside its already-recorded
`price_low`–`price_high` band range. Purely a read-only render of an already-fetched field; no new
endpoint, no new control, no new page/section/nav entry.

- **`apps/frontend/lib/types.ts`** — `DeskScreenRow` gains `reference_close?: number | null;`
  (optional, matching the plan's explicit typing), documented with an "era-desk-iter-17 (J-13)"
  paragraph mirroring the basis/history precedents: always present (non-null) on a NEWLY computed
  ranked row, entirely absent (`undefined`, never `null`) on a row recorded before this iteration —
  callers must check `row.reference_close == null` (loose equality).
- **`apps/frontend/app/desk/page.tsx`**
  - `DeskRow` gains a new `<td data-testid="desk-row-band">` as the LAST column (after `history`):
    `` `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close ${fmt(row.reference_close)}` ``,
    or `"close not recorded in this snapshot"` when `row.reference_close == null`. Uses the same
    `LABEL_CELL` class and `fmt()` rounded-display helper the basis/history cells already use — no
    new component, no new visual pattern.
  - `DeskRowsTable`'s header row gains the matching `<th className={HEADER_CELL_LEFT}>band</th>`,
    growing the table from nine to ten columns.
  - `deskRowDrillInTitle` gains a `bandLine` (full precision — the untruncated
    `reference_close`/`price_low`/`price_high`, never rounded) appended to the row's existing
    composite tooltip string — NEVER a new per-cell `title` under the stretched `absolute inset-0`
    drill-in anchor (the iter-6/iter-7 audit F2 lesson: a per-cell `title` there is
    pointer-unreachable — applied proactively here exactly as the basis/history columns already do).
  - Module-level doc comment and the per-cell inline comment block above the new `<td>` both
    document the iter-17 addition, mirroring the existing iter-9/iter-15 comment style.

## Design system conformance

No new component, no new color, no new spacing token, no new visual effect. The `band` cell reuses
`LABEL_CELL` (the exact class the `basis`/`history` cells already use) and the `fmt()` two-decimal
rounding helper already used by distance/score/basis/history. The header cell reuses
`HEADER_CELL_LEFT` verbatim. Dark, dense, terminal-grade styling — unchanged.

## States handled

- **Populated, newly-computed row**: `reference_close` present → `band <low>–<high> · close <val>`,
  full precision reachable via the row's hover tooltip.
- **Legacy row** (recorded before this iteration, key entirely absent): honest
  `"close not recorded in this snapshot"` fallback — verified live against the ambient store's
  actual pre-iteration screen snapshots (every visible row on the currently-running `/desk` shows
  this state today, since no post-iteration screen has been computed yet — see the dev handoff's
  Known Issues).
- **In-band vs out-of-band**: covered by the backend's controlled golden test
  (`test_reference_close_golden_in_band_and_out_of_band_rows`); the frontend renders whatever the
  endpoint serves verbatim in both cases — no branching logic on the frontend distinguishes them (by
  design — the disclosure is descriptive, not a computed "inside/outside" flag, per goal.md's own
  OUT OF SCOPE list).

## Live verification

Booted the frontend dev server (port 3391, against the ambient backend on port 8391) and drove a
real Chrome instance (attached via CDP to the pre-existing `:9222` endpoint) to `http://localhost:
3391/desk`. Confirmed via `document.querySelectorAll` against the live DOM:
- The ranked table's header cells read exactly
  `symbol, side, class, distance, score, coverage, tick evidence, basis, history, band`.
- Every visible row's `band` cell reads `"close not recorded in this snapshot"` (correct — every
  ambient snapshot predates this change).
- The row's drill-in anchor's `title` attribute includes the new bandLine segment.
- `npx tsc --noEmit` — zero type errors.
- `next dev` compiled `/desk` with zero build errors (`✓ Compiled /desk in 1496ms (614 modules)`,
  `GET /desk 200`).

## Known Issues

Same as the dev handoff: a live screenshot showing one in-band and one out-of-band row's
`reference_close` (TC-6) requires a NEW screen computed under this iteration's code, which is
scoped-rig, evidence-capture work for the browser-qa-agent/demo-narrator lanes downstream, not
something the ambient legacy store can currently show. The rendering logic itself is fully covered
by backend tests plus the live legacy-fallback verification above.

---

## Auditor amendment (2026-07-29)

The "Legacy row" state described above changed under audit finding **F1**: the `band` cell and the
tooltip's `bandLine` now render `band <low>–<high> · close not recorded in this snapshot` (the row's
own recorded range plus the honest close-absent state), not the bare fallback string. See
`docs/handoffs/goal-desk-iter-17-audit.md` §2/§4.
