# goal-desk-iter-9 Frontend Handoff

**Phase:** goal-desk-iter-9
**Date:** 2026-07-27
**Agent:** developer
**Status:** complete

## What Was Built

One new column on the already-shipped `/desk` ranked-rows table, plus a tooltip extension. No new
page, route, component, color token, or panel — everything reuses `page.tsx`'s existing
`LABEL_CELL`/`HEADER_CELL_LEFT` styling constants and the row's existing consolidated hover
tooltip.

- **`apps/frontend/lib/types.ts`** — `DeskScreenRow` (era-B iter-4's type) gains two nullable
  fields: `basis_as_of: string | null` and `basis_age_days: number | null`. A doc comment explains
  the "absent, not just null" legacy nuance: a screen snapshot recorded before this iteration has
  ranked rows that OMIT these two keys entirely (the append-only rail — legacy snapshots are never
  backfilled), so the runtime value there is `undefined`, not `null`; every read in `page.tsx`
  therefore uses `== null` (loose equality, this project's own established `fmt()` convention in
  `lib/format.ts`) to catch both in one check, never `=== null` alone.
- **`apps/frontend/app/desk/page.tsx`** —
  - `DeskRowsTable`'s header gains an 8th column, `basis` (`HEADER_CELL_LEFT`), appended after
    "tick evidence". The skip-rows table (4 columns) is untouched — skip rows structurally never
    carry basis fields.
  - `DeskRow` gains a matching `<td data-testid="desk-row-basis">` rendering
    `"basis 2026-07-13 · 12 d before as-of"` (date-only, goal.md's own example format) when both
    fields are present, or the honest `"basis not recorded in this snapshot"` text when either is
    absent. This cell carries **no `title` of its own** — the iter-6/iter-7 F2 lesson applied
    proactively (a per-cell `title` under the row's stretched `absolute inset-0` drill-in anchor is
    pointer-unreachable; the fix that iteration landed was to consolidate detail onto the anchor's
    own tooltip instead, never to re-introduce a per-cell one).
  - `deskRowDrillInTitle` (the anchor's composite tooltip function) now also composes a basis line
    using the FULL-PRECISION `row.basis_as_of` (untruncated ISO timestamp) plus `row.basis_age_days`
    — the same rounded-display/full-precision-on-hover split already established for
    distance/score — falling back to the same honest "not recorded" text when absent.
  - Two doc comments (the page-level header comment and the `DeskRow` column-list comment) updated
    to mention the new column, matching this project's convention of keeping exhaustive prose
    comments in sync with the code (the iter-8 F1 precedent: a stale comment is itself a defect).
  - The SAME `DeskRow`/`DeskRowsTable` components render both the latest screen and any J-05
    history-drill-through selection — there is no separate render path, so the honest fallback is
    reachable both ways by construction (verified live: clicking a legacy history row and reading
    its basis cell/tooltip both show the fallback text — see the dev handoff's replay evidence).

## Visual result

Confirmed in a real browser (Playwright, headless, via the recorded `J-08.json` replay against a
real-data-backed fixture-scoped rig — screenshot at
`reports/qa/goal-desk-iter-9-evidence/J-08-verify.png`): the ranked table's new "basis" column
renders real descriptive text (`"basis 2026-07-23 · 4 d before as-of"`,
`"basis 2026-07-13 · 14 d before as-of"` for the staler rows), dense/terminal-grade, consistent
with every other column on the page. No new color, spacing, or effect was introduced.

## Tests Run

- `cd apps/frontend && npx tsc --noEmit` — clean, zero type errors.
- Backend source-introspection guard (`apps/backend/tests/test_desk_hover_tooltip_guard.py`,
  extended this iteration) — pins that `deskRowDrillInTitle`'s source references
  `row.basis_as_of`/`row.basis_age_days`; passed.
- Backend source-introspection guard (`apps/backend/tests/test_desk_ui_guards.py`, unmodified) —
  re-run green: `/desk` still references zero structure-side compute endpoints.
- Backend copy-discipline lint (`apps/backend/tests/test_copy_discipline.py`, unmodified) — re-run
  green: the new "basis"/"d before as-of"/"basis not recorded in this snapshot" strings contain no
  advice/imperative/prediction language.
- Deterministic browser replay `--mode verify --journeys J-08` against a fixture-scoped rig
  (`:8301`/`:3301`, `rm -rf .next` rebuilt per T-9) — **PASS**: basis column renders on the latest
  screen, honest fallback renders on a legacy history row reached via drill-through, page stays
  alive after navigating back to Latest.
- Smoke-set replay `--mode verify --journeys J-01,J-02,J-03,J-04,J-05,J-06,J-07` against the same
  rig — 6 PASS / 1 SKIP (J-06 has no golden script, unrelated to this change) / 0 FAIL — confirms
  the new column did not regress any existing `/desk` or `/structure` flow (J-04's table checks,
  J-05's history drill-through + `/structure` prefill).

## Known Issues

- **TC-7's hit-test** (`document.elementFromPoint` confirming the drill-in anchor, not the new
  `<td>`, is topmost at the new cell's center) needs a live Chrome-MCP session — the deterministic
  Playwright replay tool has no hover/JS-evaluation action. Structurally low-risk (the new cell adds
  no `title`/z-index layer of its own), but unverified by this handoff. See the dev handoff for the
  same note.
- **TC-12's specific ≤2d-and-≥10d-in-one-screenshot requirement** is explicitly a browser-qa-agent
  deliverable per the DoD wording. This handoff's own replay evidence shows a real 4d/14d spread
  (today's actual data), not the literal ≤2d/≥10d thresholds — see the dev handoff's "Known Issues"
  for the full explanation and the reusable scoped-rig script available to that lane.
- No other frontend gaps — every `page.tsx`/`types.ts` item in the plan's Files-to-Modify list is
  done exactly as scoped; nothing outside those two files was touched.
