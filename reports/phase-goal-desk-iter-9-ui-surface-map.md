# Phase goal-desk-iter-9 — UI Surface Map

**Phase:** goal-desk-iter-9
**Date:** 2026-07-27
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `DeskRowsTable` header row | Updated layout | J-08 basis disclosure — every ranked row now discloses the age of the price reading its distance/class was measured from | Load `/desk`, confirm the ranked-rows table header row shows 8 columns ending in `symbol, side, class, distance, score, coverage, tick evidence, basis` (in that order); confirm the skip-rows table below it still shows only its original 4 columns (symbol, reason, coverage, tick evidence), unchanged |
| `/desk` | `DeskRow` — new `<td data-testid="desk-row-basis">` cell | New table cell (per ranked row) | Renders `basis_as_of`/`basis_age_days` for a row from a NEWLY computed screen | On a ranked row belonging to a screen computed after this iteration (e.g. run "Run Screen" for today, or use the already-recorded 2026-07-27 scoped-rig screen), confirm the basis cell's text matches exactly `"basis <YYYY-MM-DD> · <N> d before as-of"` (e.g. `"basis 2026-07-23 · 4 d before as-of"`) — not blank, not a dash |
| `/desk` | `DeskRow` — `basis` cell, honest-absence fallback | Changed behavior (new element's absent-data branch) | Screens recorded before this iteration never captured this field and must never have it faked | Open "Screen History", click a pre-iter-9 entry (the recorded `screen-2026-06-22-...` or `screen-2026-07-25-...` snapshot), confirm every ranked row's basis cell reads exactly `"basis not recorded in this snapshot"` — never blank, never a dash, never a computed/guessed value |
| `/desk` | Row drill-in anchor composite tooltip (`deskRowDrillInTitle`, the `<tr>`'s consolidated `title`) | Changed behavior (existing tooltip content extended) | Full-precision basis detail joins the SAME row-level tooltip instead of a new per-cell `title` (iter-6/iter-7 lesson: a per-cell title under the row's stretched `absolute inset-0` drill-in anchor is pointer-unreachable) | Hover anywhere over a ranked row (symbol cell, the new basis cell, anywhere within the row) and read the native browser tooltip text; confirm it contains a `basis <full ISO timestamp> (<N> d before as-of)` segment positioned between the existing `score ...` and `coverage ...` segments; for a legacy (pre-iter-9) row, confirm that segment instead reads `basis not recorded in this snapshot` |
| `/desk` | Row drill-in anchor hit-test at the new cell | Regression check (no visible change, but a correctness risk introduced by the 8th column) | The table gained a column, so every cell's screen position — including the new one's center — shifted; must confirm the full-row anchor, not the new `<td>`, is still what receives the pointer | At the new basis cell's own center point, run a `document.elementFromPoint(x, y)` check (or equivalent DevTools inspection) and confirm the returned element is the row's stretched `absolute inset-0` anchor, not the `<td>` itself — flagged by the dev handoff as **not yet verified**, still outstanding |
| `/desk` | Screen History drill-through (existing J-05 feature; same `DeskRowsTable`/`DeskRow` components render both latest and historical) | Regression check (no code change to the drill-through mechanism itself, but new fields must propagate through it) | Confirms there is no separate render path for historical vs. latest screens | Click a historical entry in "Screen History" and confirm the basis column + tooltip render for that snapshot (real data if the snapshot is from this iteration onward, honest fallback if older); click "Latest" to return and confirm the page is still interactive (not blank/dead) and shows the latest screen's own basis data again |
| `/desk` | Ranked-rows table — fresh-vs-stale legibility | Visual verification | DoD requires one screenshot showing a fresh row (basis age ≤ 2 d) and a stale row (basis age ≥ 10 d) legible together | Load `/desk`'s latest screen and scan the basis column for two rows spanning a wide age range (the dev pass observed AAPL/large-caps around 3–4 d vs. NFLX/NVDA/META around 14 d on live data); capture one screenshot containing both rows readably; if no row is actually ≤ 2 d old at QA time, explicitly judge whether the observed spread still demonstrates "fresh vs. stale" legibly, per the plan's own allowance for that call |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_desk_screen.py` — 5 new/extended tests: byte-identical golden cross-check
  of a ranked row's `basis_as_of` against `GET /research/tradability`'s own value, a pure-function
  calendar-day-diff test against goal.md's own worked example, a zero-extra-`compute_tradability`-
  call guard test, a same-pins re-run byte-identical test, and a legacy-row-fields-absent test —
  verifies backend correctness only, no UI surface affected.
- `apps/backend/tests/test_desk_hover_tooltip_guard.py` — extended source-introspection guard that
  now also asserts `deskRowDrillInTitle`'s source references `row.basis_as_of`/`row.basis_age_days`
  — a build-time correctness check on the frontend source text, not itself a UI surface.
- `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` — new dev/QA harness script that copies
  the whole `.data/` tree into a throw-away root for scoped browser testing — infrastructure/tooling
  only, never shipped to users, no UI surface.
- `runs/goal-session-desk/journey-scripts/J-08.json` — new deterministic-replay golden script used
  by the regression-replay tooling — a QA asset that exercises the UI but is not itself a UI surface.
- `docs/handoffs/goal-desk-iter-9-dev.md`, `docs/handoffs/goal-desk-iter-9-frontend.md`,
  `reports/phase-goal-desk-iter-9-*.md`, `reports/qa/goal-desk-iter-9-evidence/*.png` — process/
  documentation and evidence artifacts, no UI surface.

**Note on unchanged files that still gain the new data:** `apps/backend/app/research/desk_routes.py`
(the `GET /research/desk/screen` route) and `app/mcp/__init__.py` (the `desk_screen` MCP proxy) show
**zero diff** this iteration — confirmed via `git diff` (empty) and a `response_model` grep (no
match). Both already return the row dict verbatim with no schema narrowing, so the two new fields
flow through to REST and MCP consumers automatically, without either file being touched.

---

## Summary

- **Frontend surfaces changed:** 1 (route: `/desk`)
- **New pages/routes:** 0
- **Modified components:** 2 (`DeskRowsTable`/`DeskRow` ranked-row rendering — new column + cell;
  `deskRowDrillInTitle` — tooltip content), both within the existing `apps/frontend/app/desk/page.tsx`
- **Navigation changes:** no
- **Backend-only changes:** 5 (two extended test files, one new dev/QA harness script, one new golden
  replay script, plus handoff/report documentation artifacts)
