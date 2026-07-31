# goal-desk-iter-34 Execution Plan

## What to Build
- Fix `topupLibraryReach` in `apps/frontend/app/desk/page.tsx` (currently `:878-904`) so the
  "newest recorded reach" extreme and the "earlier" partition are both computed by grouping
  `store_frozen_through_after` at CALENDAR-DAY precision (a day-truncated key,
  `store_frozen_through_after?.slice(0, 10) ?? null`), never by comparing the raw
  microsecond-precision string. A pair whose day matches the newest day's own printed date must
  never appear in "earlier" again. `newestDate`/`earlier[].date` may keep full precision in the
  returned shape (render already truncates via `.slice(0, 10)`) — only the GROUPING decision
  changes.
- Cap the returned `earlier` array at 20 entries (`EARLIER_PAIRS_DISPLAY_CAP = 20` literal) while
  preserving the TRUE total separately, so the heading can disclose it honestly.
- Render: when the true earlier-than-newest total exceeds 20, add one plain sentence beside/under
  the existing "Pairs recorded earlier (N)" heading that literally includes the word "showing" and
  both the shown count (20) and the true total (e.g. `showing 20 of <true total>`). When the true
  total is ≤ 20, no such sentence renders (unchanged behavior). No new section/control/column —
  stays entirely inside the already-registered library-reach block between
  `desk-topup-run-latest-window-basis` and `desk-topup-run-latest-failed`.
- Extend `apps/backend/tests/test_desk_topup_library_reach_guard.py` with: a day-truncation
  source-introspection assertion (grouping truncates BEFORE comparing), a cap assertion (earlier
  list capped at 20, true total preserved separately), and a seeded-violation counterpart for EACH
  new assertion (the file's existing `test_the_fallback_text_guard_can_fail_on_a_seeded_violation`
  pattern) — a guard that cannot fail proves nothing.
- Repoint `runs/goal-session-desk/journey-scripts/J-19.json` to stable substrings (`J-17.json`'s
  iter-33 hardening precedent, and `J-18.json`/`J-09.json`'s own prior hardening): assert `"reach
  it"` on the reach line and `"Pairs recorded earlier"` on the earlier-list heading; DO NOT assert
  any specific date/count that will drift on the next real ambient top-up run. Remove step 4's
  current assertion of `"AAPL 4h — 2026-07-30"` as an earlier row (it enshrines the exact bug this
  iteration fixes) — replace with a structural check that no earlier-row's own printed date equals
  the reach line's own printed newest date, or (if the replay tool cannot do a cross-step computed
  comparison) a stable non-date substring such as the row's own `SYMBOL TF — ` pattern.
  `journey-scripts/J-17.json` was already refreshed at iter-33 (commit `efef1c1`, now on HEAD) —
  do NOT touch it again.
- Update `runs/goal-session-desk/state/blueprint.md`'s existing "Top-up run records" row: change
  the iter-34 "IN BUILD" note (line ~682) to a "RESOLVED at iter-34" note, written to land in the
  SAME commit as the code (never claiming the fix shipped before it does — the iter-30 lesson).
- Dev handoff at `docs/handoffs/goal-desk-iter-34-dev.md` disclosing which of TC-1..TC-9 were
  verified live (screenshot) vs. at unit/fixture level (test output) — per the spec's own note,
  TC-4 may need a synthetic/unit-level verification (TC-3) if the current ambient run's true
  earlier-count turns out to be ≤ 20 once correctly grouped by day.
- A `[NEW]`-flagged demo-narrator walkthrough recording the fixed disclosure end to end, run
  STRICTLY AFTER the fix is committed, narrated from the actually-rendered post-fix page (not the
  spec's intent — the iter-33 lesson), against the ambient `:3301`/`:8301` pair (no scoped rig —
  the ambient store already holds `topup-2026-07-31-8fb5c9a1f737` with genuine cross-timeframe
  reach-date variance).

## Explicitly OUT OF SCOPE (do not touch)
- `_pair_window`, `run_topup`, `desk_topup_log.py`, or the stored precision of
  `store_frozen_through`/`store_frozen_through_after` — already correct, proven at iter-32.
- `desk_topup_compute.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `desk_screen.py`,
  `tradability.py`, `levels.py`, `routes.py`'s `record_bar_series` — zero diff.
- Re-verifying J-01..J-18 as an iteration goal (all `passing`; replay-only for the
  required-still-passing set J-04, J-07, J-09, J-16, J-17).
- Any nav-skeleton change, new page, new `Config` field, new MCP tool, or new ranked-table /
  Top-up-Runs summary-table column (J-16's measured width contract stays byte-unchanged).
- Triggering a further real ambient top-up run — the current ambient run already carries the
  variance needed to exercise the fix live; a further trigger would invalidate sibling golden
  scripts (the iter-32 lesson).
- Standing up a scoped/fixture rig for evidence — record against the ambient `:3301`/`:8301` pair
  after the mandatory `rm -rf apps/frontend/.next` clean rebuild (T-9).

## Agents Required
- backend-data: yes (test-only — `test_desk_topup_library_reach_guard.py` gains day-truncation +
  cap assertions with seeded-violation counterparts, run via the full backend suite; ZERO backend
  production-code diff, per spec)
- frontend-ux: yes (`apps/frontend/app/desk/page.tsx`'s `topupLibraryReach` fix + render change;
  `journey-scripts/J-19.json` golden-script repoint; browser-qa + demo-narrator evidence capture)

Frontend Present: yes

## Files to Create/Modify
- `apps/frontend/app/desk/page.tsx` — day-precision grouping fix in `topupLibraryReach`, 20-row
  cap with true-total preserved, conditional "showing 20 of N" disclosure sentence.
- `apps/backend/tests/test_desk_topup_library_reach_guard.py` — extend with day-truncation + cap
  assertions and their seeded-violation counterparts.
- `runs/goal-session-desk/journey-scripts/J-19.json` — repoint to stable substrings; drop the
  bug-enshrining exact-row assertion.
- `runs/goal-session-desk/state/blueprint.md` — flip the iter-34 note from "IN BUILD" to
  "RESOLVED at iter-34", same commit as the code.
- `docs/handoffs/goal-desk-iter-34-dev.md` — new dev handoff (TC-1..TC-9 live-vs-unit disclosure).

## UI Evolution
- New user-facing capability: none beyond what J-19 already shipped at iter-32 — this iteration
  makes the existing "newest reach" line and "Pairs recorded earlier" list internally consistent
  (same-day pairs can no longer be double-counted as both newest and earlier) and honestly
  discloses truncation instead of rendering an unbounded list.
- New information displayed: one conditional sentence, shown only when the true earlier-pairs
  count exceeds 20 — `showing 20 of <true total>`.
- New user actions: none.
- UI surface changes: `/desk` → Top-up Runs → latest-run detail → the existing "Pairs recorded
  earlier" block gains a conditional one-line disclosure; no new section, control, or column.
- Navigation changes: none.

## Visual Requirements
- Component patterns: no new components — reuse the existing library-reach block's plain
  text/list rendering (`desk-topup-run-latest-reach`, `desk-topup-run-latest-reach-earlier`,
  `desk-topup-run-latest-reach-earlier-row` testids stay; the new disclosure sentence sits inside
  the existing heading area, matching the house's small-caps/slate-muted descriptive-text style
  already used for `WINDOW_BASIS_NOT_RECORDED`/`LIBRARY_REACH_NOT_RECORDED` fallbacks).
- Layout: no layout change — same dense terminal-grade Top-up Runs section, same position between
  the window-basis line and the failed-pairs block.
- Key visual effects: none new — plain descriptive text, no new emphasis/color/badge.
- States to handle: (1) true total ≤ 20 → heading unchanged, no disclosure sentence; (2) true
  total > 20 → heading + "showing 20 of N" sentence, list capped at 20 rows; (3) legacy run with
  no `store_frozen_through_after` on any outcome → unchanged `LIBRARY_REACH_NOT_RECORDED` fallback,
  untouched by the day-truncation/cap logic; (4) all pairs share the same day → empty "earlier"
  list, no earlier-list section at all (existing `earlier.length > 0` gate).

## Key Test Scenarios
- TC-1 (live/browser): on the ambient `/desk` page post T-9 rebuild, the "newest recorded reach"
  line's printed calendar day never matches any row's printed day inside "Pairs recorded earlier".
- TC-2 (unit): two outcomes with the same calendar day but different microsecond timestamps group
  as the SAME day; neither appears in `earlier`.
- TC-3 (unit): 25 outcomes earlier-by-day than the newest → returned `earlier` has length 20 plus
  a separate true-total of 25.
- TC-4 (live if the ambient run's true total > 20, else unit via TC-3's fixture): a run with a true
  earlier-total of 25 renders `showing 20 of 25` beside the heading.
- TC-5 (live or unit): a run with a true total ≤ 20 (or 0) renders no "showing N of M" sentence.
- TC-6 (unit): a legacy run (no `store_frozen_through_after` on any outcome) still renders
  `"library reach not recorded in this run"`, unaffected by truncation/cap logic.
- TC-7/TC-8 (unit): seeded violations (raw-field grouping; uncapped >20-length earlier array) each
  make the corresponding new guard assertion fail — proving the guards are not vacuous.
- TC-9 (live/browser replay): repointed `J-19.json` passes against the ambient `/desk` page
  without asserting any specific date, count, or the bug's contradictory row text.
- TC-10 (suite): full backend suite green, `Config().config_fingerprint()` still
  `08e471b10130e1e2`, MCP surface still exactly 17 tools, zero new `Config` fields; existing tests
  in `test_desk_topup_compute.py`, `test_desk_topup_log.py`, `test_desk_ui_guards.py`,
  `test_desk_hover_tooltip_guard.py`, `test_copy_discipline.py` pass unmodified.
- Required-still-passing replay: J-04, J-07, J-09, J-16, J-17 remain green via deterministic
  golden-script replay (no re-verification work needed beyond running their existing scripts).

## Notes for the developer
- The bug is fully diagnosed already (confirmed directly against current source this iteration):
  `topupLibraryReach` compares full-precision `store_frozen_through_after` strings for both the
  `newestDate` reduce and the `earlier` filter, while the render only truncates to day via
  `.slice(0, 10)` at display time (`:996`/`:1014`). Fix: derive one day-truncated key per outcome
  ONCE, and use that truncated key everywhere a grouping/comparison decision is made; only the
  final rendered/stored strings may keep full precision.
- `EARLIER_PAIRS_DISPLAY_CAP = 20` should be a named literal, not a magic number, matching this
  file's existing constant style (`LIBRARY_REACH_NOT_RECORDED`, `WINDOW_BASIS_NOT_RECORDED`).
- The existing guard test file's pattern (source-introspection on `page.tsx` as text; see
  `test_topup_library_reach_returns_null_when_any_outcome_lacks_store_frozen_through_after`) is the
  template for the new day-truncation/cap assertions — slice the function body between its
  declaration and the next top-level `function`, assert on structural substrings, then seed a
  violation string and prove the same check catches it.
- Demo-narrator must run AFTER the code commit, not before — an iter-33/iter-32 lesson: a
  walkthrough recorded against pre-fix source narrates the bug, not the fix.
