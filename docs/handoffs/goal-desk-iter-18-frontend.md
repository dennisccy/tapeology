# goal-desk-iter-18 Frontend Handoff

**Phase:** goal-desk-iter-18
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

A new `opposite` column on the `/desk` ranked-rows table (growing it from ten to eleven columns),
plus one more line in the row's existing composite hover tooltip, disclosing:

- **`opposite_band`** — the nearest band on the side of price the row's own selected band did NOT
  choose (e.g. `opposite resistance A 490.88–494.22 · 0.6 bps`), with two honest fallback states: a
  recorded `null` (`compute_tradability` served no band on that other side at all) renders "no band
  on the other side"; a legacy row recorded before this iteration (key entirely absent) renders
  "opposite wall not recorded in this snapshot".
- **`bands_by_class`** — a per-class count of every band `compute_tradability` returned for that
  symbol (A/B/C/unclassified) — surfaced ONLY in the row's composite drill-in tooltip (e.g.
  `bands by class A 10 · B 0 · C 0 · unclassified 0`), not as a separate table cell, matching the
  exact scope named in this iteration's plan.

No new page, no new section, no new nav row, no new button/control — this is a pure read-only
render extension of the already-shipped `/desk` briefing table.

## Files Changed

- `apps/frontend/lib/types.ts` — `DeskScreenRow` gains two new optional fields:
  `opposite_band?: {side, band_class, price_low, price_high, band_score, distance_bps} | null` and
  `bands_by_class?: {A, B, C, unclassified}`, with a doc comment describing the legacy-absent-key
  contract (mirrors the `basis_as_of`/`history_sessions`/`reference_close` precedent exactly — see
  the comment block immediately above the interface).
- `apps/frontend/app/desk/page.tsx`:
  - `DeskRow` gains a new `opposite` `<td data-testid="desk-row-opposite">` cell, placed after the
    existing `band` cell, rendering the three distinguishable states described above using the SAME
    `fmt()` rounded-display convention the distance/score/band cells already use.
  - `DeskRowsTable` gains the matching `<th>opposite</th>` header cell.
  - `deskRowDrillInTitle` gains one more line (`bandsByClassLine`) in the row's existing composite
    tooltip string, carrying the row's full-precision `bands_by_class` breakdown — never a new
    per-cell `title` (this page already established the rule that a per-cell `title` under the
    stretched `absolute inset-0` drill-in anchor is pointer-unreachable — the iter-6/iter-7 F2
    lesson — so every full-precision detail lives in the one composite tooltip).
  - Module-level comment block updated to describe the iter-18 addition, written carefully to avoid
    the literal substrings `compute_tradability`/`compute_levels`/`/research/tradability`/
    `/research/levels` inside comments (the page's own TC-5 backend guard test scans the raw source
    text for those substrings to prove the desk page never references structure-side compute
    endpoints — a comment containing the literal name would have falsely tripped that guard, which
    is exactly what happened on the first pass and was caught by re-running the guard suite).

## Design Notes

- Reused the existing dense terminal-style `<table>`/`<td>`/`<th>` pattern exactly — `LABEL_CELL`
  class, no new colors, no new visual effect, no layout change beyond one additional column and one
  additional tooltip line.
- The `opposite` cell text intentionally omits `band_score` (goal.md's own worked example for the
  cell — `opposite resistance A 490.88–494.22 · 0.6 bps` — does not include it either, and no other
  cell in this table surfaces the SELECTED band's own score outside the dedicated `score` column).
  `band_score` is typed and available on `row.opposite_band` for any future consumer, but this
  iteration's scope (plan.md, phase spec) does not ask for it to be rendered anywhere, so it is not
  — per the "no speculative extra disclosure" simplicity bar.
- The `bands_by_class` tooltip line deliberately does NOT compute or render a summed "N bands"
  total client-side (unlike the illustrative "10 bands · A 10 · B 0 · C 0 · unclassified 0" example
  in the plan/spec, which is just showing what the numbers might look like) — summing the four
  served counts would itself be a client-side arithmetic derivation, which both the anti-goal
  ("nothing derived or graded further") and this iteration's own extended TC-11 guard forbid. The
  line renders each served count directly: `bands by class A ${A} · B ${B} · C ${C} · unclassified
  ${unclassified}`.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit -p tsconfig.json` — clean, zero errors.
Command: `cd apps/frontend && npx next build --no-lint` — compiled successfully, `/desk` route
builds with no errors (see the dev handoff's Known Issues for a note on where this build was run).
Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_ui_guards.py
tests/test_copy_discipline.py -q` — all green (10 + 30 passed), including the new/extended
arithmetic-derivation guard (TC-11) and its counter-test, and `test_copy_discipline.py` unmodified
and still green against the new `opposite`/`bands by class` copy strings (no advice, imperative, or
prediction language in either).

## Known Issues

- No live-browser screenshot of the new `opposite` column or a populated `bands_by_class` tooltip
  was captured by this dispatch — every screen snapshot in the ambient `.data/` store predates this
  iteration (both new keys honestly absent on every visible row today). That capture, plus the
  required `[NEW]`-flagged demo-narrator walkthrough, is downstream-lane work per this era's
  established division of labor — see the dev handoff's Known Issues for the full explanation.
- See the dev handoff (`docs/handoffs/goal-desk-iter-18-dev.md`) for the note on an inadvertent
  `next build` run in the shared frontend directory while an ambient `next dev` process was active,
  and the verification that the ambient process was unaffected.
