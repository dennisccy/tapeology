# Iteration 24 — Coherence Audit

**Iteration:** goal-desk-iter-24
**Date:** 2026-07-30
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

J-16 is a pure frontend reflow of the already-registered `/desk` ranked table (rank/symbol/side/
class/distance/score/coverage/tick-evidence/basis/history/band/opposite/levels). The scoped diff
(`git diff 51a7495 -- .`, noise excluded) touches exactly two files:

- `apps/frontend/app/desk/page.tsx` — layout only: `table-fixed` + `<colgroup>`, drops the
  redundant in-cell label prefix on 3 of 12 disclosure cells (basis/history/levels; band/opposite
  deliberately keep theirs — see below), collapses `DeskCoverageBadges` onto one line
  (`flex-wrap` → `flex-nowrap`), renders class/distance as the page's existing `CHIP_CLASS` chip
  style (byte-identical className to `TickEvidenceBadge`/the `band_round_number` badge, confirmed
  at `page.tsx:189` vs `page.tsx:294`/`:540`), and adds one `rank` cell rendering `.map((row,
  index) => ...)`'s own `index + 1` — the row's already-served array position, not a new
  computation.
- `apps/backend/tests/test_desk_ui_guards.py` — three new guard tests (TC-7a/b, plus a golden-text
  label-prefix pin) enforcing exactly the constraints below.

`git status`/the excluded-path stat confirm `docs/goal.md`, `runs/goal-session-desk/*`, and
`reports/goal-session-desk-index.html` carry no diff from the snapshot SHA (pre-existing session
bookkeeping, outside review scope per the invocation prompt) — the reviewable surface is exactly
the two files above, matching the bounded diff.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Ranked-row fields (band_class, distance_bps, band_score, coverage, tick_evidence, basis_as_of/basis_age_days, history_sessions/history_start, reference_close, price_low/price_high, opposite_band, bands_by_class, band_member_count/band_round_number/band_member_timeframes) | OK — re-format only | `apps/frontend/app/desk/page.tsx:299-560`; all read from the same already-fetched `GET /research/desk/screen` response, no new fetch, no client recomputation |
| Served row order (`rows` array) | OK — no reorder | `apps/frontend/app/desk/page.tsx:610` (`rows.map((row, index) => ...)`, `rank={index+1}`); no `.sort(`/`.reverse(`/`.slice(` over `rows` anywhere in the diff, and a new source-introspection guard (`test_desk_ui_guards.py:_ROWS_REORDER_PATTERN`, with a seeded counter-test at line ~63) proves the guard can catch a violation |
| `rank` (new display) | OK — registered, not a duplicate | Blueprint `runs/goal-session-desk/state/blueprint.md:110-115` (Navigation-skeleton note) and `:137` (Feature/journey-homes row) and the `RESOLVED at iter-24` note (`:598-626`) explicitly sanction this exact field as "the row's own 1-based position in the SERVED `rows` array verbatim... never a new computed value" — matches the diff precisely; not a synonym of any other registered value |

No new endpoint, no new backend module, and per TC-9 (confirmed by the diff itself) zero changes
to `desk_screen.py`/`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/
`config.py`.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` (unchanged route, layout-only reflow) | OK | No new route/page/component in the diff; blueprint IA section already lists `/desk` under the Desk nav section (`blueprint.md:60-115`); `app/meta.py` `UI_ROUTES` (the nav owner) is not touched by this diff |

No new page, no new nav entry needed, no parallel shell, no duplicate home — this iteration adds
no navigable surface at all.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The `band`/`opposite` cells intentionally keep their in-cell label prefix ("band "/"opposite ")
  while the sibling `basis`/`history`/`levels` cells drop theirs — a visible inconsistency in the
  reflowed table. This is a deliberate, well-documented exception (code comments at
  `page.tsx:483-488` and `:503-505`, plus the new guard
  `test_desk_row_cells_keep_the_label_prefix_their_golden_script_asserts`): two stored golden
  replay scripts (`J-13.json`, `J-14.json`) assert the literal visible text starting with those
  words via `page.get_by_text`, and TC-6 forbids editing golden scripts this iteration. Not a
  coherence violation (no duplicate source, no divergent value) — noted only as a minor cosmetic
  asymmetry a future iteration could clean up once those goldens are allowed to move.
