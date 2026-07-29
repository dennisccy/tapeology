# goal-desk-iter-15 Execution Plan

## What to Build
- Journey **J-11 only**: history-depth disclosure on every ranked `/desk` briefing row —
  `history_sessions` (count of completed daily bars at or before the row's `basis_as_of`) and
  `history_start` (the earliest such bar's own timestamp), so the operator can tell a
  short-history listing (e.g. 27 sessions) from a long-history one (e.g. 500 sessions) without
  leaving `/desk`.
- Both fields are derived **inside the existing** `_resolve_reference_close` ascending walk over
  `BarStore.merged_bars(symbol, "1d")` (`apps/backend/app/research/desk_screen.py:239`) — zero new
  store read, zero new accessor on `bars.py`/`bar_index.py`.
- Attach the two fields to each RANKED row built in `compute_screen`'s `elif` branch
  (`desk_screen.py:342-359`), beside the existing `basis_as_of`/`basis_age_days`. Skip rows
  (`no_bars`/`no_basis`) never carry them — matches the J-08 precedent exactly.
- Extend the module docstring's disclosure documentation with a "History disclosure" section
  mirroring the existing "Basis disclosure" section (`desk_screen.py:56-66`).
- Frontend: `DeskScreenRow` gains `history_sessions: number | null` / `history_start: string | null`
  (types.ts ~:801-812, mirrors the `basis_as_of`/`basis_age_days` loose `== null` pattern at
  `types.ts:812`); `/desk`'s ranked table gains a `history` column beside the existing `basis`
  column (`app/desk/page.tsx` mirrors the pattern at ~:317-320/349), with the honest
  `"history not recorded in this snapshot"` fallback for legacy rows; the row anchor's existing
  composite hover tooltip (`page.tsx` ~:223-238) gains a `history_start` detail line — zero change
  to click geometry, zero change to any other column/section.
- No rank-key change, no new `Config` field, no fingerprint move, no new page/nav/endpoint/MCP
  tool. This is a pure additive-disclosure iteration structurally identical to J-08 (iter-9).
- A `[NEW]`-flagged demo-narrator walkthrough covering the history disclosure end to end (this
  iteration is dispatched at `full` depth specifically so this lane runs BEFORE the evaluator).

## Agents Required
- backend-data: yes -- `desk_screen.py` row-builder + docstring extension; `test_desk_screen.py`
  new test block (golden per-row values, byte-identical re-run, legacy-row absence,
  zero-extra-`merged_bars`-call guard, MCP `desk_screen` proxy pass-through, copy-discipline
  sentinel).
- frontend-ux: yes -- `types.ts` field additions; `app/desk/page.tsx` `history` column + tooltip
  line; a fixture-scoped browser pass proving `history_sessions <= 60` and `>= 400` rows are both
  legible in one screenshot after a T-9 clean rebuild (`rm -rf apps/frontend/.next`).

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/research/desk_screen.py` -- add `history_sessions`/`history_start` derivation
  inside `_resolve_reference_close`'s existing walk (or an equivalent same-walk helper called from
  it); attach both fields to the ranked-row dict at `compute_screen`'s `elif` branch
  (~lines 342-359); extend the module docstring with a "History disclosure" section.
- `apps/backend/tests/test_desk_screen.py` -- new test block mirroring the "basis disclosure
  (goal-desk-iter-9, J-08)" block (~line 667 onward): TC-1/TC-2 golden per-row values including one
  short-history (<=5 or <=60 per DoD) and one long-history (>=400) member in the same fixture run;
  TC-3 byte-identical re-run under identical pins; TC-4 legacy-row key-absence (never `null`); TC-5
  skip rows carry neither field; TC-6 a `merged_bars` call-count guard proving zero extra store
  reads; TC-7 cross-check against `GET /research/candles` filtered to bars at/before `basis_as_of`.
- `apps/frontend/lib/types.ts` -- `DeskScreenRow` (~:801-812) gains `history_sessions: number | null`
  and `history_start: string | null`.
- `apps/frontend/app/desk/page.tsx` -- new `history` table column beside `basis` (~:317-320 for the
  cell, ~:349 for the header), honest `"history not recorded in this snapshot"` fallback for legacy
  rows, and a `history_start` line folded into the existing composite tooltip (~:223-238) — no other
  column/section touched.
- `docs/handoffs/goal-desk-iter-15-dev.md` -- dev handoff (required by DoD).
- A golden replay script for J-11 (mirrors `runs/goal-session-desk/journey-scripts/J-08.json`) plus
  a regression smoke pass over the existing J-04/J-05/J-08/J-10 `/desk` replay scripts.

## UI Evolution
- New user-facing capability: on `/desk`, the operator can see per ranked row how many completed
  daily sessions (and from what start date) the row's wall was measured over, without opening
  `/structure`.
- New information displayed: `history_sessions` (int >= 0) and `history_start` (ISO date-time or
  absent) per ranked row.
- New user actions: none — disclosure only, no new button/control.
- UI surface changes: `/desk` ranked table gains one column (`history`); the row drill-in anchor's
  composite hover tooltip gains the `history_start` detail line. No other page/section/button
  changes; Top-up Runs and Index Reconciliation sections are untouched content-wise (only possible
  vertical layout shift from the wider table).
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse the existing dense terminal-grade table row/cell components already
  used for the `basis` column (`LABEL_CELL` class, `data-testid="desk-row-basis"` sibling pattern)
  — add `data-testid="desk-row-history"` analogously. Reuse the existing composite tooltip builder
  (`deskRowDrillInTitle`) rather than adding a second tooltip mechanism.
- Layout: no layout restructuring — one new `<th>`/`<td>` pair inserted into the existing ranked
  table, in the same row/column flow as `basis`/`distance`/`score`/coverage badges.
- Key visual effects: none new — matches the existing dark, dense, terminal-grade house style with
  no new chrome, glow, or animation.
- States to handle: legacy rows (recorded before this iteration) render
  `"history not recorded in this snapshot"` instead of a value — never blank, never `null`
  literal text; skip rows render no history cell content at all (they already have no
  band/basis cells).

## Key Test Scenarios
- TC-1/TC-2: a fixture-scoped screen run records `history_sessions`/`history_start` per ranked row,
  matching the count/earliest-timestamp of that member's own `merged_bars(symbol, "1d")` entries at
  or before its `basis_as_of`; a short-history member (<=60 sessions) and a long-history member
  (>=400 sessions) both appear in the same run with visibly different values.
- TC-3: an identical-pin re-run returns the existing snapshot unchanged (no duplicate file), with
  byte-identical `history_sessions`/`history_start` on every row.
- TC-4: `GET /research/desk/screen?date=<pre-iteration date>` omits both keys entirely on legacy
  rows (never `null`); `/desk` renders `"history not recorded in this snapshot"` for those rows.
- TC-5: skip rows (`no_bars`/`no_basis`) never carry `history_sessions`/`history_start`.
- TC-6: a `BarStore.merged_bars` call-count guard proves this addition reads the store zero extra
  times per ranked symbol.
- TC-7: single-source-of-truth cross-check — a row's `history_sessions`/`history_start` match
  `GET /research/candles?symbol=<sym>&timeframe=1d`'s own merged, price-less-row-excluded response
  filtered to bars at/before that row's `basis_as_of`.
- TC-8/TC-9 (browser, T-9 clean rebuild required): `/desk`'s ranked table shows the `history`
  column with at least one `history_sessions <= 60` row and one `>= 400` row legible in ONE
  screenshot; hovering a row's drill-in anchor shows the composite tooltip including
  `history_start` with zero click-geometry change.
- TC-10: full backend suite green; `Config().config_fingerprint()` still `08e471b10130e1e2`; zero
  new `Config` fields; MCP tool count still exactly 17; `tests/test_copy_discipline.py` green
  unmodified.
- TC-11: `[NEW]`-flagged demo-narrator walkthrough recorded against a fixture-scoped rig with a
  computed screen, narrating and screenshotting at least one short- and one long-history row.
- Regression: J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10 all remain green (deterministic replay
  + LLM fallback) — this iteration touches only `desk_screen.py`'s row-builder and `/desk`'s ranked
  table; the universe/coverage subsystem, Top-up Runs, and Index Reconciliation sections are
  untouched.

## Notes / Rig Discipline
- Every lane (dev, browser-QA, demo-narrator) must state its own fixture-scoped rig path fresh —
  the iter-14 rig (`.../iad.goal-desk-iter-14.*/desk-iter14-scoped-qa`) does not survive into this
  iteration's own PID-scoped scratch dir; re-derive per this run's `TMPDIR`
  (`/home/dennis-chan/.cache/iad/iad.goal-desk-iter-15.3302867`).
- Unlike J-09/J-10's one-way-door honest-empty captures, this journey's evidence is NOT a one-way
  door: a screen can be freely recomputed on the same rig to widen the session split if needed,
  without breaching the append-only rail (only a *new* snapshot is ever written).
- Check for golden-script collisions before recording: if this iteration computes a NEW screen into
  a scoped rig that J-04.json/J-05.json/J-08.json also replay against via "latest screen" lookups,
  disclose any unavoidable collision in the results report (iter-10 lesson).
- The cited real numbers in goal.md (`screen-2026-07-29-ce0d82b8e9bf`, HONA #8 at 27 sessions vs.
  several names at 500) are a worked example proving the split is reachable, not a literal number
  to reproduce byte-for-byte (iter-9 lesson) — independently confirm a genuine short/long split
  exists in whatever rig is actually used.
