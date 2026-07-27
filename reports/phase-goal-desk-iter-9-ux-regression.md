# Phase goal-desk-iter-9 — UX Regression Review

**Date:** 2026-07-27

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

**Capability: "basis" column + tooltip detail on every `/desk` ranked row (J-08).**

- **Navigation path:** Home (`/`, Cockpit) → NavBar "Desk" link (1 click; the nav is server-driven
  from `GET /meta/ui-routes` with no client-side hardcoded list, and this iteration's diff touches
  neither `desk_routes.py` nor any route registration, so the nav is unchanged) → `/desk` loads with
  the basis column already populated as part of the existing ranked-rows table. **0 additional
  clicks, no toggle, no settings menu** — confirmed live by UT-10 ("visible without extra
  navigation... rendered the basis column and real data as part of the normal page load"). This
  clears the ≤2-click bar with room to spare — it is effectively 1 click from home, visible on
  arrival.
- **Label clarity:** "basis" is domain jargon, but it is the SAME term used throughout `goal.md`,
  the plan, and every dev handoff — the label matches what the spec calls the feature, so this is
  not a label-confusion mismatch. The cell text itself is self-disambiguating in context ("basis
  2026-07-13 · 12 d before as-of"), and the page already carries denser jargon (band class,
  distance-bps, band score, coverage, tick evidence) that this column sits comfortably beside. Not
  flagged.
- **Visual feedback when used:** not applicable — this is a passive display of already-loaded data
  with no new user action (no button, no toggle). The one interactive affordance (hover for
  full-precision detail) is an EXTENSION of a pattern already established in iter-4/iter-7 for
  distance/score, not a new one, and the core information (date + day-count) is on-screen without
  any interaction — hover only adds exact-timestamp precision on top.
- **Design system conformance:** the new column and tooltip content reuse the page's existing
  `HEADER_CELL_LEFT`/`LABEL_CELL` styling constants verbatim — confirmed both in the dev handoff and
  independently in the diff (`git diff be83fd1 -- apps/frontend/app/desk/page.tsx`). No new
  component, color token, or panel was introduced. UT-09 explicitly confirmed via
  `getComputedStyle` that a fresh (3d) row and a stale (14d) row render with **identical** CSS
  (`color: rgb(148,163,184)`, `font-weight: 400`, transparent background) — no color-coded
  urgency/freshness indicator, consistent with this project's explicit copy-discipline constraint
  against advice/urgency language. No visual inconsistency found.

## Regression Risk

| Shared component | Prior feature it serves | This iteration's touch | Risk | Evidence |
|---|---|---|---|---|
| `DeskRowsTable` / `DeskRow` (`page.tsx`) | J-04 (iter-4: the whole `/desk` page) and J-05 (iter-6: Screen-History drill-through — the SAME components render latest and historical) | Adds an 8th column + cell | High (central to two prior features) | UT-01 (8-col header exact, no error panel), UT-06 (drill-through + "Latest" revert both clean), UT-08 (other 7 columns + skip table byte-identical, buttons unchanged); smoke-set replay of J-01–J-07: 6 PASS / 1 no-UI-surface skip / 0 FAIL. **No regression found.** |
| `deskRowDrillInTitle` (`page.tsx`) | The exact function iter-7 CREATED to fix a real regression (per-cell `title`s made unreachable by the row's stretched `absolute inset-0` drill-in anchor — audit finding F2) | Extends the same shared tooltip composer with a basis segment; deliberately adds **no** new per-cell `title` on the new `<td>` | **Highest risk in this iteration** — a careless implementation here would reintroduce exactly the bug iter-7 fixed | Diff confirms the correct pattern was followed (extended the shared composer, zero per-cell title added). UT-04 verified tooltip content/order via direct DOM `title` inspection (`distance → score → basis → coverage`). UT-07 ran the hit-test (`document.elementFromPoint`) specifically **at the new cell's own center** — necessary because the table gained a column and cell centers moved — and confirmed the anchor (`<a data-testid="desk-row-drill-in">`), not the `<td>`, is still topmost. A durable backend guard test (`test_desk_hover_tooltip_guard.py`) was also extended to source-lock this pattern going forward. **No regression found**, and unusually well-verified given the history at this exact touchpoint. |
| `desk_screen.py` `compute_screen` | J-03/J-04/J-05/J-08 backend data source; the append-only `ScreenStore` mechanism (which had a real prior-iteration incident — iter-4's NaN-bar poisoning, per project history) | Adds two fields to the ranked-row branch only | High (append-only data integrity) | TC-3 byte-identical re-run test; TC-4 SHA-256 checksum proof the two REAL pre-existing snapshot files are byte-unchanged on disk before/after; full backend suite green at 1346 passed/8 skipped (exactly +5, matching the +5 new tests — no other file's count moved). **No regression found.** |
| `/structure` query-param prefill + auto-load (iter-6's own feature) | J-05 (the drill-in destination) | Not touched — confirmed zero diff, this file isn't even in the iter-9 Files-Changed list | Low (untouched) | UT-07 reconfirmed the click-through URL is correct; smoke-set replay of J-05 ("Ledger history + drill-in to /structure") passed end-to-end, which is what actually re-exercises the prefill+auto-load behavior. **No regression found.** |

**Non-regression observation (for transparency, not attributed to this phase):** UT-02 noted that a
newly recorded screen appends to the **bottom** of the Screen History list (chronological ascending)
rather than the top, which the test plan apparently expected. Browser QA traced this to code neither
touched by this iteration's diff (the backend's `screens` array order and the frontend's
straight pass-through with no client sort) and reported it as a pre-existing characteristic, not a
new defect. Independently consistent with the Files-Changed list in both dev handoffs — confirmed
not introduced by this phase.

## UI vs Backend Parity

| Backend capability | UI exposure |
|---|---|
| `basis_as_of` (new field, `desk_screen.py`) | Rendered in the "basis" column cell (date portion) and the row's composite hover tooltip (full precision) |
| `basis_age_days` (new field, `desk_screen.py`) | Rendered in the same cell and tooltip, as the "N d before as-of" clause |
| `GET /research/desk/screen` (REST, zero code change — dict pass-through) | Same page consumes this endpoint; confirmed via diff that `desk_routes.py` has zero changes |
| `desk_screen` MCP tool (zero code change — byte-identical proxy) | Not a competing user-facing UI surface; it is a read-only tool-consumer proxy of the same REST response the `/desk` page already renders — not a parity gap |

`implementation-summary.md` ("Backend-Only Items: None") and `user-visible-changes.md` ("Not Visible
Yet: None") agree, and this was independently verified against the actual diff
(`git diff be83fd1 -- apps/backend/app/research/desk_screen.py apps/frontend/app/desk/page.tsx
apps/frontend/lib/types.ts`): both new fields are computed backend-side and rendered frontend-side
in the same change set. No backend capability exists this iteration that lacks a UI surface.

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None confirmed. The two highest-risk touchpoints (the shared tooltip-composer function with a real
prior-regression history, and the append-only screen-snapshot store) both carry direct, specific
verification evidence (live hit-test at the new cell's moved center; SHA-256 checksum proof of
byte-identical pre-existing files) rather than incidental coverage.

### Visual Consistency
No deviation from the established `/desk` visual language found. No new component, color token, or
panel was introduced; computed styles for fresh vs. stale rows are identical (no color-coded
urgency), consistent with this project's copy-discipline constraints. The new column follows the
same rounded-display/full-precision-on-hover split already established for distance/score in prior
iterations.

## Recommendation

No action required. Discoverability exceeds the 2-click bar (1 click from home, visible on arrival,
no interaction needed for the core information). The one component with real regression history in
this codebase (the row's composite drill-in tooltip) was extended correctly and re-verified with a
live hit-test at the specific cell whose position moved. Backend/UI parity is complete.
