# goal-desk-iter-19 Execution Plan

## What to Build
- Fix `_select_opposite_band` (`apps/backend/app/research/desk_screen.py:269-278`) to use its OWN
  tie-break key, distinct from `_select_best_band`'s, implementing `docs/goal.md` J-14 step 1
  VERBATIM: **distance ascending, then class rank descending (`_CLASS_RANK`,
  `desk_screen.py:138` — unclassified ranks lowest, never highest), then `band_score` descending,
  resolved by `min`'s first-of-tie stability over `compute_tradability`'s own served order.**
  Currently it delegates straight to `_select_best_band` (key `(-_CLASS_RANK[class],
  distance_bps, -quality_score)` — class-first), which iter-18's own audit (finding B1) flagged as
  contradicting goal.md and measured as diverging on 2/63 real rows (HONA: shipped class-A wall at
  336.96 bps vs. the nearer class-B wall at 153.67 bps; META: shipped class-A at 232.58 bps vs. the
  nearer class-C at 92.05 bps). `_select_best_band` itself (same-side selection) and
  `_row_rank_key` (cross-symbol order) stay byte-unchanged — this is a one-function edit adding a
  new local `key()` closure inside `_select_opposite_band` (distance-first ordering), not touching
  the shared helper.
- Update the module docstring's "Opposite-band disclosure (goal-desk-iter-18, J-14)" section
  (`desk_screen.py:90-99`, the sentence "ranked by the IDENTICAL `(class rank DESCENDING,
  distance_bps ascending, quality_score descending)` tuple") to describe the corrected
  distance-first order, tagged as a goal-desk-iter-19 correction (matching this module's existing
  per-iteration docstring section convention — see the Basis/History/Reference-close sections
  immediately above it for the pattern).
- Flip and rename `test_select_opposite_band_prefers_higher_class_over_closer_distance`
  (`apps/backend/tests/test_desk_screen.py:259-268`) to assert the corrected distance-first
  behavior (it currently asserts the wrong, class-first outcome — `far_but_high_class` wins; it
  must assert `close_but_low_class` wins instead). Re-verify every other opposite-band assertion in
  the same file, updating only what the two rules actually disagree on:
  - `test_opposite_band_golden_near_far_and_null_class_rows` (`:1304-1396`, TC-1/TC-2/TC-3/TC-4) —
    note: this golden's three symbols (ABBV/ACN/ADBE) each have exactly ONE opposite-side band, so
    class-vs-distance is not competing there; confirm no value actually changes, but the flipped
    unit test above (or a TC-1-shaped addition) must be the one place a real class-vs-distance
    conflict is exercised, per the spec's TC-1 wording ("close-but-lower-class... farther-but-
    higher-class... returns the closer band").
  - The byte-identical-recompute test (`test_opposite_band_stays_byte_identical_on_a_recompute_
    under_identical_pins`, `:1417+`) and the legacy-row-absence test
    (`test_a_legacy_row_recorded_without_opposite_band_fields_serves_them_absent_never_backfilled`)
    — shape unchanged, only re-verify pass under the new rule.
  - `test_select_opposite_band_returns_the_nearest_band_on_the_other_side` (`:241`) and the tie
    test `test_select_opposite_band_exact_tie_keeps_the_served_order_first_item` (`:271`) — same
    class on both candidates, so these should already agree with the new rule; re-verify, don't
    silently assume.
  - The AAPL real-route cross-check the iter-18 audit added inside
    `test_aapl_row_cross_checks_byte_identical_to_the_real_tradability_route` (near `:545`, TC-2/
    TC-3/TC-4/TC-8 vs. the live `GET /research/tradability` response) — this test derives its
    expectation dynamically from the served route rather than hardcoding a selection, so it should
    pass unmodified, but must be re-run to confirm.
- Re-verify `apps/backend/tests/test_mcp_server.py`'s
  `test_desk_screen_opposite_band_and_bands_by_class_fields_proxy_verbatim` (`:521-582`) — it seeds
  a raw `ScreenStore.record(...)` call directly (not via `compute_screen`/`_select_opposite_band`),
  so it is testing byte-identical proxying only and should need no value change; confirm and note
  in the dev handoff rather than assume.
- Verify the fix against real (or fixture-scoped multi-row-equivalent) data reproducing the exact
  HONA/META divergence the iter-18 evaluator measured (TC-6), on a fixture-scoped rig — never
  `apps/backend/.data` (per this session's own iter-9/11/14/15/17 scoped-rig lessons, restated in
  the spec's BACKGROUND). Record the before/after comparison in the dev handoff. If the fix finds
  zero real-data divergence on the actual rig used, that is a surprising result to flag explicitly
  (per spec NOTES), not silently treat as done — iter-18's own measurement (2/63) is the bar.
- Re-film the DoD-required `[NEW]`-flagged demo-narrator walkthrough over POPULATED `/desk` rows
  (never `/structure`) on a fixture-scoped rig after `rm -rf apps/frontend/.next` + rebuild (T-9),
  narrating the opposite-wall disclosure end to end — this closes BOTH this iteration's own J-14
  walkthrough clause AND iter-17's carried J-13 `RECORDED_WITH_NOTES` gap (iter-18's own re-film
  attempt landed on `/structure` in 4/6 frames per iter-18 audit finding E1 — this is the fix for
  that gap, not a repeat of the same mistake). Browser-QA screenshot evidence (TC-13) needs one row
  with `opposite.distance_bps` within 25 bps and one beyond 1,000 bps legible together, plus a
  second screenshot of a row's hover tooltip showing `bands_by_class`.
- Optional rider (not DoD, only if time/evidence-capture allows without risking the DoD): one
  full-page capture of the earlier same-day Screen History recording carried from J-12's separately
  open gap.

## Agents Required
- backend-data: yes -- the one-key selection fix in `desk_screen.py`, the docstring correction, and
  the test updates described above (developer agent covers both backend and frontend work per its
  own role definition; there is no separate "frontend-ux" track needed here since zero `page.tsx`
  code changes are in scope).
- frontend-ux: no -- no `page.tsx`/`types.ts`/component code change; the frontend already renders
  whatever `opposite_band`/`bands_by_class` the backend serves (iter-18 shipped that rendering).
  Frontend involvement this iteration is EVIDENCE CAPTURE only (browser-qa screenshots + demo
  re-film against a freshly computed screen), not code.

## Frontend Present: yes

Note on this line: the phase spec's own metadata header says "Frontend Present: no", but that
refers narrowly to "no `page.tsx` code change is needed." Per this project's own DoD, the fix
changes NEW-row CONTENT the UI already renders (the `opposite` column will show a genuinely
different wall on any row where the two rules disagree), and the phase explicitly requires a real
Chrome MCP browser pass (TC-13, DoD item 1) plus a re-filmed demo-narrator walkthrough (TC-14, DoD
item 6) over POPULATED `/desk` rows. Per the orchestrator's own governing rule ("if the phase adds
any user-facing data or capability, Frontend Present MUST be yes"), this line is set to `yes` so
qa-phase.sh and the browser-qa-agent run their Chrome MCP checks — do not let the spec's narrower
"no code change" note be read as "no browser verification needed."

## Files to Create/Modify
- `apps/backend/app/research/desk_screen.py` -- `_select_opposite_band`'s tie-break key
  (distance-first, its own closure, not delegated to `_select_best_band`); module docstring's
  Opposite-band disclosure section corrected + goal-desk-iter-19 tag.
- `apps/backend/tests/test_desk_screen.py` -- flip/rename
  `test_select_opposite_band_prefers_higher_class_over_closer_distance`; re-verify (update only
  where values actually diverge) the golden near/far/null-class test, the byte-identical-recompute
  test, the legacy-absence test, the nearest-on-other-side and tie-break tests, and the AAPL
  real-route cross-check.
- `apps/backend/tests/test_mcp_server.py` -- re-verify
  `test_desk_screen_opposite_band_and_bands_by_class_fields_proxy_verbatim` (expected: no value
  change, seeded fixture bypasses the selector).
- `docs/handoffs/goal-desk-iter-19-dev.md` -- new dev handoff (required by DoD), including the
  HONA/META-style real-data before/after comparison.
- No changes in scope to: `apps/frontend/app/desk/page.tsx`, `apps/frontend/lib/types.ts`,
  `_select_best_band`, `_row_rank_key`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`,
  `StructureChart.tsx`, `desk_coverage.py`, `config.py`, any `Config` field, any MCP tool, any new
  Data-Contract row. These must all show zero diff (TC-12) at review/audit time.
- `runs/goal-session-desk/state/blueprint.md` -- a "NOTED at iter-19" entry appended to the existing
  "Screen snapshots, rank rows, skip rows" Data Contract row documenting the selection-rule
  correction (no new row, no new owner, no new endpoint — per spec's Blueprint conformance section).
- Demo-narrator artifacts under `reports/demo/goal-desk-iter-19/` -- the `[NEW]`-flagged re-film,
  produced by the demo-narrator lane after dev/review/QA pass, against a fixture-scoped rig with a
  freshly computed, populated screen.

## UI Evolution
- New user-facing capability: none (the `opposite` column and its tooltip already exist since
  iter-18).
- New information displayed: none new — same two fields, corrected selection, so on any row where
  the two rules disagree the DISPLAYED wall changes (a different band's side/class/price/distance),
  though the column/field shape is identical.
- New user actions: none.
- UI surface changes: none — no `page.tsx` edit.
- Navigation changes: none.

## Visual Requirements
- Component patterns: unchanged — same ranked `<table>` row/cell structure iter-18 shipped for the
  `opposite` column and its composite tooltip line; no new components.
- Layout: unchanged.
- Key visual effects: none new.
- States to handle: same three-way honest split already shipped and unchanged in this iteration —
  populated cell, recorded `null` ("no band on the other side"), and legacy-absent
  ("opposite wall not recorded in this snapshot"); re-verify all three still render correctly since
  no `page.tsx` diff is expected, but the evidence capture must SHOW the populated case with both a
  near (<25 bps) and far (>1,000 bps) row, which iter-18's own capture failed to do.

## Key Test Scenarios
- TC-1: a bands list with the row's own selected band, a close-but-lower-class opposite-side band,
  and a farther-but-higher-class opposite-side band → `_select_opposite_band` returns the closer
  band, not the higher-class one.
- TC-2/TC-9: two exactly-tied opposite-side bands, called with the list in each of the two possible
  orders → first-served-per-order, stable across repeated calls.
- TC-3: every band shares the row's own selected side → `None`.
- TC-4: golden near/far/null-class fixture rows recompute correctly under the corrected rule; no
  test in the file still asserts the pre-fix class-first selection.
- TC-5: a freshly computed screen on the fixture-scoped rig — each row's `opposite_band` is
  byte-identical (side/band_class/price_low/price_high/band_score) to
  `GET /research/tradability?symbol=<sym>&as_of=<as_of>`'s own smallest-`_distance_bps` band on the
  opposite side, and `distance_bps` reproduces the same formula the row's own `distance_bps` uses.
- TC-6: the real/fixture-scoped-equivalent screen the iter-18 evaluator measured — HONA's
  `opposite_band` now reports the nearer class-B band (~153.67 bps) not the farther class-A band
  (~336.96 bps); META's reports the nearer class-C band (~92.05 bps) not the farther class-A band
  (~232.58 bps).
- TC-7: `_select_best_band`'s own existing suite passes fully unmodified after the fix.
- TC-8/TC-9 (identical-pins/rank-order): a recompute under the SAME five pins returns the existing
  snapshot unchanged (no second write); `_row_rank_key` cross-symbol order is byte-identical
  before/after the fix.
- TC-10: the MCP `desk_screen` tool and `get_endpoint`'s proxy stay byte-identical to
  `GET /research/desk/screen`; MCP tool count stays exactly 17.
- TC-11: full backend suite green, `Config().config_fingerprint()` == `08e471b10130e1e2`,
  `test_copy_discipline.py` passes unmodified.
- TC-12: zero diff on `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/
  `desk_coverage.py`.
- TC-13 (browser): `/desk` after `rm -rf apps/frontend/.next` rebuild on a fixture-scoped rig with a
  freshly computed screen — the `opposite` column shows one row within 25 bps and one beyond
  1,000 bps legible in one screenshot, plus a tooltip screenshot showing `bands_by_class`.
- TC-14 (demo): a `[NEW]`-flagged demo-narrator walkthrough over that same populated `/desk` rig —
  every step narrates the opposite-wall disclosure over populated ranked rows, never `/structure`.
- Error cases: opposite-side-empty still returns honest `None`; a legacy row still serves both
  fields entirely absent, never backfilled.
