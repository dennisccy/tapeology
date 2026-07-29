# goal-desk-iter-18 Execution Plan

Target journey: **J-14** (disclosure only). Required-still-passing: J-01..J-13. Full depth
(demo-narrator runs before scoring, per iter-12/13 lesson). Anti-goals in force: single source of
truth, immutable/append-only snapshots, no new statistic/gate/threshold, descriptive-only copy,
fingerprint pin `08e471b10130e1e2` unchanged, hermetic keyless suite.

## What to Build

- On every NEW ranked screen row, disclose the nearest band on the side of price the row's OWN
  displayed band did **not** select (`opposite_band`), plus a per-class count of every band
  `compute_tradability` returned for that symbol (`bands_by_class`). Both are drawn from the SAME
  `result["bands"]` list `compute_screen` already holds for that symbol — zero new `BarStore` read,
  zero second `compute_tradability` call, zero change to rank order or the 5-pin snapshot key.
- `opposite_band` selection reuses `_select_best_band`'s exact tie-break tuple
  (`-_CLASS_RANK[class]`, `_distance_bps`, `-quality_score`, via `min`'s first-of-tie stability),
  filtered to the side opposite `best["side"]`; `None` when no band exists on that side.
- `bands_by_class`: a plain count under fixed keys `"A"`/`"B"`/`"C"`/`"unclassified"` (a
  `class: None` band counts under `"unclassified"`); all four keys always present, even at zero.
- Legacy rows (recorded before this iteration) keep both keys entirely absent — never `null`,
  never backfilled. Skip rows never carry either field, matching the basis/history/reference-close
  precedent.
- Frontend renders a new `opposite` column (e.g. `opposite resistance A 490.88–494.22 · 0.6 bps`,
  honest `"no band on the other side"` for a recorded `null`, `"opposite wall not recorded in this
  snapshot"` for a legacy-absent row) plus one more `bands_by_class` line in the row's existing
  composite hover tooltip (full precision, never a new per-cell `title` — the iter-6/7 F2 lesson).
  The frontend renders only served fields; it derives nothing.
- A `[NEW]`-flagged demo-narrator walkthrough (run at `full` depth, before scoring) narrates the
  opposite-wall disclosure over a freshly computed, POPULATED screen on a fixture-scoped rig — this
  is DoD, not optional polish, and per the iter-17 carry note may also close J-13's legacy-only
  capture gap as a side effect (report only, not a separate goal).

## Agents Required

- backend-data: yes -- `desk_screen.py` `compute_screen` row builder (`opposite_band` selector +
  `bands_by_class` counter, both bound in the ranked-row dict beside `reference_close`, ~:385-403),
  module docstring + `compute_screen` docstring updates, and the full `test_desk_screen.py` /
  `test_mcp_server.py` test additions listed below.
- frontend-ux: yes -- `lib/types.ts` `DeskScreenRow` two new optional fields, `app/desk/page.tsx`
  new `opposite` `<td>`/`<th>` cell + tooltip line in `deskRowDrillInTitle`, confirming
  `test_copy_discipline.py` stays green unmodified.

(Both lanes are implemented by the single `developer` agent in one dispatch, per this project's
established pattern — backend and frontend changes are small, tightly coupled to one row shape,
and share the same fixture-scoped test rig.)

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/research/desk_screen.py` -- add `_select_opposite_band` (or equivalent) reusing
  `_select_best_band`'s key/`_distance_bps`; add a `bands_by_class` counter helper; bind both into
  the ranked-row dict in `compute_screen` (~:385-403); extend the module docstring with an
  "Opposite-band disclosure (goal-desk-iter-18, J-14)" section mirroring the Basis/History/
  Reference-close sections immediately above it (~:79-88), and update `compute_screen`'s own
  docstring field-list sentence (~:334-338).
- `apps/backend/tests/test_desk_screen.py` -- golden test asserting exact `opposite_band` +
  `bands_by_class` per ranked row, including one row with nearest opposite wall within 25 bps, one
  beyond 1,000 bps, and one whose nearest opposite band carries `class: null`; byte-identical
  re-run under identical pins; unit test of the selector proving honest `null` when no band exists
  on the other side (TC-8); unit test proving tie-break stability across repeated calls on a tied
  fixture (TC-9); a call-count guard test asserting no additional `BarStore.merged_bars` /
  `compute_tradability` call beyond what iteration 17 already established (TC-10, the J-11/J-13
  precedent); a rank-order-unchanged golden proving byte-identical symbol sequence vs. the pre-change
  fixture with `_row_rank_key` appearing only as unchanged context in `git diff` (TC-5); a
  legacy-row-absence test (TC-7, entirely-absent keys, on-disk checksum unchanged, no rewrite on
  re-run).
- `apps/backend/tests/test_mcp_server.py` -- extend/add the byte-identity proxy test for
  `opposite_band`/`bands_by_class` through both the `desk_screen` tool (no-arg) and `get_endpoint`'s
  `?date=` proxy (TC-14; zero MCP code change, 17-tool contract unaffected).
- `apps/backend/tests/test_desk_ui_guards.py` -- confirm (extend if the existing scan does not
  already generically cover it) that the source-scan guard proves the frontend performs no
  arithmetic deriving an opposite-band or bands-by-class value (TC-11); the existing TC-8 guard from
  iter-17 is the direct precedent to extend rather than duplicate.
- `apps/frontend/lib/types.ts` -- `DeskScreenRow.opposite_band?: {side: "support"|"resistance";
  band_class: "A"|"B"|"C"|null; price_low: number; price_high: number; band_score: number;
  distance_bps: number} | null` and `.bands_by_class?: {A: number; B: number; C: number;
  unclassified: number}`, beside `reference_close`, with a doc comment following the
  basis/history/reference-close precedent (legacy-absent-key contract, `== null` loose-equality
  check convention).
- `apps/frontend/app/desk/page.tsx` -- `DeskRow`: new `opposite` `<td>` after the existing `band`
  cell, rendering the row's `opposite_band` per the display rules above; `DeskRowsTable`: matching
  `<th>opposite</th>`; `deskRowDrillInTitle`: one more composite-tooltip line carrying full-precision
  `bands_by_class` (e.g. `10 bands · A 10 · B 0 · C 0 · unclassified 0`) -- never a new per-cell
  `title`.
- `docs/handoffs/goal-desk-iter-18-dev.md` -- dev handoff (required DoD item).

## UI Evolution

- New user-facing capability: every ranked row on `/desk` now discloses the nearest wall on the
  OTHER side of price from the one it was ranked on, plus how many bands of each class its own
  displayed wall was chosen from -- closing the gap where nine top-ranked rows read identically
  (`support · class A · 0.00 bps`) while their true opposite-side spreads range 0.6-6,067.7 bps.
- New information displayed: `opposite_band` (side, class, price range, band score, distance bps)
  in a new `opposite` column; `bands_by_class` (A/B/C/unclassified counts) in the row's composite
  hover tooltip.
- New user actions: none -- read-only render, no new button or control.
- UI surface changes: one new `opposite` column on the existing `/desk` ranked table
  (`DeskRowsTable`/`DeskRow`, growing ten columns to eleven); one new tooltip line. No new page, no
  new section, no new nav row.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing dense terminal-style `<table>`/`<td>`/`<th>` row pattern
  exactly as the `basis`/`history`/`band` columns already establish (`LABEL_CELL` class, stretched
  `absolute inset-0` drill-in `<Link>` per row, `data-testid` per cell).
- Layout: no layout change -- one additional column in the existing `DeskRowsTable`, one additional
  line in the existing composite tooltip string.
- Key visual effects: none new -- inherits the existing dark/dense/terminal-grade table styling
  unmodified.
- States to handle: populated `opposite_band` (near, e.g. ≤25 bps, and far, e.g. >1,000 bps),
  recorded `null` (`"no band on the other side"`), and legacy-absent (`"opposite wall not recorded
  in this snapshot"`) -- all three must be distinguishable and each covered by the browser-QA
  screenshot(s) and the demo-narrator walkthrough.

## Key Test Scenarios

- TC-1..TC-4: a NEW fixture-scoped screen carries `opposite_band` (or `null`) and a complete
  `bands_by_class` on every ranked row; non-null `opposite_band` fields match
  `GET /research/tradability`'s own `bands` list byte-for-byte; `opposite_band.distance_bps` matches
  the same `_distance_bps` formula; `bands_by_class`'s four values sum to that symbol's total band
  count.
- TC-5: rank order (symbol sequence) is byte-identical to the pre-change fixture; `_row_rank_key`
  untouched.
- TC-6/TC-7: re-run under identical pins returns the already-recorded response, no new file
  written; a pre-iteration snapshot's rows carry neither key (absent, not null), checksum unchanged,
  `/desk` renders the honest legacy fallback string.
- TC-8/TC-9: `opposite_band` is `null` when `compute_tradability` returns bands on only one side;
  tie-break is stable across repeated calls on a tied fixture.
- TC-10: call-count guard -- exactly one `compute_tradability` call and one
  `BarStore.merged_bars(symbol, "1d")` call per symbol, no additional reads.
- TC-11: frontend source scan finds no arithmetic deriving an opposite-band or bands-by-class value
  -- the page renders only served fields.
- TC-12 (browser, J-14): after a T-9 clean rebuild, ONE screenshot shows the `opposite` column with
  at least one row within 25 bps and one beyond 1,000 bps opposite-wall distance, both legible; a
  second screenshot shows a row tooltip carrying its `bands_by_class` line; a legacy row shows the
  honest fallback.
- TC-13: full suite green, `Config().config_fingerprint()` == `08e471b10130e1e2`, zero diff to
  `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`, zero new `Config`
  fields.
- TC-14: MCP tool count exactly 17; `desk_screen` tool + `get_endpoint` proxy both byte-identical to
  the direct `GET /research/desk/screen` response including the two new fields.
- TC-15: `test_copy_discipline.py` passes unmodified against the new `opposite`/`bands_by_class`
  copy strings.
- TC-16 (demo-narrator, `[NEW]`-flagged, full depth before scoring): `Demo Verdict: RECORDED` with a
  non-empty gallery narrating the new column, a near row, a far row, the tooltip's
  `bands_by_class` line, and a legacy row's honest fallback -- recorded on a fixture-scoped rig
  against a freshly computed, populated screen (never a write to `apps/backend/.data`; check the
  target store for an existing snapshot under the same five pins before computing and disclose any
  collision, per the iter-10 lesson).
- Regression smoke: J-01 through J-13 stay green via deterministic replay + LLM fallback.

## Notes for downstream lanes

- Scoped-rig discipline (iter-9/11/14/15/16 lessons) binds every lane: any NEW screen compute for
  evidence must run on a fixture-scoped rig (never `apps/backend/.data`), the rig path must be
  stated in each lane's own dispatch and re-derived after any re-dispatch (PID-scoped scratch dirs),
  and isolation independently verified (e.g. `/proc/<pid>/environ` for `TAPEOLOGY_*` overrides --
  scoped ports are not a scoped store).
- Browser-QA lane must assert the captured page's origin matches the rig's own base URL (iter-16
  lesson) and never mark a browser test PASS on a source-code read alone.
- Keep the `Required-still-passing journeys:` metadata line on one physical line everywhere it is
  echoed (iter-17 lesson -- the replay-lane parser truncates a wrapped continuation).
- Never start a second `next dev` from `apps/frontend` while an ambient one is running (iter-17
  lesson -- copy the whole `apps/frontend` tree to an isolated directory, or stop the ambient one
  first).
- Environment: before running tests or any command that writes temp files, export
  `TMPDIR=/home/dennis-chan/.cache/iad/iad.goal-desk-iter-18.3302867` (and matching `TMP`/`TEMP`).

## Out of scope (per spec, do not build)

- Any new Data-Contract row, endpoint, route, or `Config` field.
- Any diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/
  `desk_coverage.py`.
- Any change to the rank key or the 5-pin snapshot key.
- Any threshold, "room"/corridor, proximity flag, or derived quality number.
- Backfilling/rewriting any already-recorded screen snapshot.
- A CLI warmer for these fields.
- Any write to `apps/backend/.data` for evidence capture.
- Re-recording J-09/J-10/J-11/J-12's already-CORRECT `[NEW]` walkthroughs.
- A `/desk` "Universe ledger" section (rejected at iter-16).
