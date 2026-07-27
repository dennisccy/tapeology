# Iteration 9 — Coherence Audit

**Iteration:** goal-desk-iter-9
**Date:** 2026-07-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope of this iteration

J-08 (goal-proposer-promoted, post-GOAL_ACHIEVED enhancement loop) adds two descriptive fields —
`basis_as_of`, `basis_age_days` — to every RANKED row of a NEWLY computed `/desk` screen, plus a
"basis" column and extended drill-in tooltip to render them. Per
`docs/phases/goal-desk-iter-9.md` ("Blueprint conformance") the blueprint was updated additively
BEFORE dispatch: a new J-08 row in the Feature/journey homes table
(`runs/goal-session-desk/state/blueprint.md:94`) and an "iter-9 addition" note on the existing
"Screen snapshots, rank rows, skip rows" Data Contract row (`blueprint.md:130`, trailer
`blueprint.md:225-232`). Confirmed against `git diff 8602747593db8517b7033e4b40bd5927b725b5aa -- .`
(standard noise excludes) plus `git status`; the touched surface is exactly:

- `apps/backend/app/research/desk_screen.py` — new `_basis_age_days()` helper (:263-274) and two
  new dict keys on the ranked-row branch only (:356-357).
- `apps/backend/tests/test_desk_screen.py`, `test_desk_hover_tooltip_guard.py` — new/extended
  tests (golden cross-check, calendar-diff pure-function test, zero-extra-call guard test,
  byte-identical-rerun test, legacy-fields-absent test, tooltip-needle extension).
- `apps/frontend/app/desk/page.tsx` — one new `<td data-testid="desk-row-basis">` (:283-286), one
  new `<th>` (basis column header), `deskRowDrillInTitle` extended with a basis segment
  (:197-206).
- `apps/frontend/lib/types.ts` — `DeskScreenRow` gains `basis_as_of: string | null`,
  `basis_age_days: number | null`.
- `apps/backend/scripts/goal-desk-iter9-scoped-backend.sh` (new, untracked) — a fixture-scoped QA
  harness script (copies `.data/` to a throw-away root, never touches the ambient store); not
  imported by any app module, registers no route.
- `runs/goal-session-desk/journey-scripts/J-08.json` (new) — a read-only golden replay (goto,
  expect, click a history row, click "latest" — no compute-triggering click).

No new page, route, or `Config` field. `apps/backend/app/research/tradability.py`, `levels.py`,
`bars.py`, `StructureChart.tsx`, `app/meta.py` (`UI_ROUTES`), `desk_routes.py`, and
`app/mcp/__init__.py` all show **zero diff** against the snapshot SHA — confirmed directly in the
diff (none of these files appear in it) and matches the iter spec's TC-16 requirement.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `basis_as_of` (new ranked-row field) | OK | Computed once by `tradability.py:404` (`compute_tradability`, the row's UNCHANGED canonical owner) inside the SAME per-member call `desk_screen.py:330` (`result = compute_tradability(bar_store, symbol, as_of_epoch, config)`) that already produces `band_class`/`distance_bps`/`band_score` for that row (an iter-3-established pattern, blueprint.md:107). `desk_screen.py:356` copies `result["basis_as_of"]` verbatim into the ranked row — no second call, no re-derivation. Served by the SAME `GET /research/desk/screen` the row's other fields already use (blueprint.md:130, iter-9 addition note) — not a new endpoint. |
| `basis_age_days` (new ranked-row field) | OK | A plain calendar-date subtraction (`desk_screen.py:263-274`, `_basis_age_days`) over two values already in scope in the same loop iteration (`result["basis_as_of"]` and the loop's own `as_of`, `desk_screen.py:357`) — not a re-derivation of any registered value, and not a second read of any store. `test_basis_fields_add_zero_extra_compute_tradability_calls` (`test_desk_screen.py`) instruments `compute_tradability` call-count and asserts it equals exactly the member count — zero extra calls attributable to either new field. |
| Bands / tradable-map scores (`tradability.py`) | OK | Zero diff confirmed — not present in `git diff <snapshot-sha>`. `/structure/page.tsx:2195`'s pre-existing direct display of `tradability.basis_as_of` (live, `GET /research/tradability`) is untouched by this iteration; `/desk`'s new basis column reads a persisted COPY from the append-only screen snapshot, the same live-view-vs-pinned-snapshot split already standing for `band_class`/`distance_bps`/`band_score` since iter-3 (blueprint.md:107) — not a second implementation of `compute_tradability`, and not a case of one value diverging silently (the screen snapshot is deliberately a frozen point-in-time reading, not a live mirror). |
| Screen snapshots / ranked rows (`desk_screen.py`) | OK | Additive-only change to the EXISTING row shape, same owner, same endpoint, per the blueprint's own pre-registration (`blueprint.md:130`, "iter-9 addition" note) — matches the actual diff exactly (two new dict keys, ranked-row branch only; skip-row branch untouched, confirmed `desk_screen.py:337-341` unchanged). |
| Legacy (pre-iter-9) screen rows | OK | `test_a_legacy_row_recorded_without_basis_fields_serves_them_absent_never_backfilled` proves the two keys are entirely ABSENT (not `null`) on rows recorded before this change, served verbatim by the same endpoint — no backfill, no read-time computation. Frontend checks `row.basis_as_of == null` (loose equality, `page.tsx:202,284`) to catch both `undefined` and explicit `null` in one honest fallback branch, never fabricating a value. |

No new value was introduced without blueprint registration, so A5 (unregistered value) does not
apply — the decomposer registered both fields prospectively before dispatch.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` basis column + tooltip (J-08) | OK | Not a new page/route — one new `<td>`/`<th>` inside the already-shipped `DeskRowsTable`/`DeskRow` on the existing `/desk` route (J-04's canonical home). `app/meta.py` (`UI_ROUTES`) shows zero diff against the snapshot SHA — nav unchanged, still 3 rows. Blueprint's Feature/journey homes table already carries the row `J-08 ... | /desk (ranked table column + row drill-in tooltip) | Desk` (`blueprint.md:94`), registered before this iteration's dispatch. No parallel shell, no duplicate home — same table, same page, same nav entry J-04 already occupies. |
| Screen History drill-through (J-05, pre-existing) | OK | The ui-surface-map confirms the SAME `DeskRowsTable`/`DeskRow` components render both the latest screen and any historical screen opened via drill-through — no second render path was added for the new column (`reports/phase-goal-desk-iter-9-ui-surface-map.md`, "Screen History drill-through" row). Verified no new fetch call was added to `page.tsx` for this purpose. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The basis value is displayed with different precision in two places on the same row — the
  visible `<td>` shows the date only (`basis_as_of.slice(0, 10)`, `page.tsx:286`) while the
  drill-in anchor's composite tooltip carries the full ISO timestamp (`page.tsx:204`). This is not
  flagged as inconsistent formatting: it is the SAME rounded-cell/full-precision-tooltip split
  already established and blueprint-sanctioned for `distance_bps`/`band_score` (audit F3, iter-4),
  applied consistently to the new field.
- The ui-surface-map's own dev-handoff note flags the row anchor's hit-test at the new basis
  cell's center as "not yet verified" — i.e., whether `document.elementFromPoint` at that point
  still resolves to the stretched `absolute inset-0` drill-in anchor rather than the new `<td>`
  itself, now that the table has an 8th column. This is a functional/QA completeness question
  (browser-qa-agent's jurisdiction, not this gate's), not a Data Contract or IA violation, so it is
  noted here for visibility only and does not affect this verdict.
- `docs/goal.md` and `runs/goal-session-desk/state/blueprint.md` both show diffs in `git status`
  relative to `HEAD`, but neither appears in `git diff <snapshot-sha>` — both were already at their
  current content as of the snapshot (the goal-proposer's J-08 promotion and the decomposer's
  blueprint pre-registration both landed before this iteration's own snapshot was captured, per the
  iter spec's own account). Nothing in this iteration's own dev diff touches either file.
