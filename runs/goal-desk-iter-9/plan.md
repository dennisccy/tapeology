# goal-desk-iter-9 Execution Plan

Era B "The Desk", proposer-promoted journey **J-08** only (goal.md `AUTO:journeys` block). Iteration
8 closed the era GOAL_ACHIEVED (J-01–J-07 passing); this iteration reopens it for exactly one
additive journey and nothing else. No new page, route, Config field, or MCP tool.

## What to Build

- **Backend — basis disclosure on ranked rows.** In `desk_screen.py`'s `compute_screen` row-builder
  (the ranked-row `else` branch only, current lines ~310-325), add two fields to every ranked row:
  `basis_as_of` (copied **verbatim** from `result["basis_as_of"]`, already read at line 311 to
  resolve the reference close — zero new call) and `basis_age_days` (a plain calendar-date
  difference between that value and the loop's own `as_of` local, already in scope — the
  `_distance_bps` precedent at `desk_screen.py:197`, same "plain arithmetic derivation" style).
  Skip rows are untouched (a `"no_basis"` skip already means no basis resolved; the ranked-row
  branch is the only place these fields can exist).
- **Backend — prove no extra read.** A new guard test in `test_desk_screen.py` (mirrors
  `test_bar_store_signature_issues_zero_bar_store_calls` at line 125, but instruments
  `compute_tradability` itself, not `BarStore.list`/`get`) proving call count == member count —
  zero additional `compute_tradability`/`BarStore`/`bar_index` calls attributable to the two new
  fields (TC-8).
- **Backend — goldens.** Extend `test_desk_screen.py`: new-row `basis_as_of` byte-identical to
  `GET /research/tradability`'s own `basis_as_of` for the same symbol/as_of (TC-1); `basis_age_days`
  exact calendar-day count (TC-2, e.g. 12-day case from goal.md's own worked example); a same-pins
  re-run stays byte-identical including the two new fields and writes no second file (TC-3); the
  two REAL pre-iteration screen snapshot files on disk are proven byte-identical by checksum
  before/after (TC-4) and served with the fields absent — never defaulted, never backfilled.
- **Frontend — `DeskScreenRow` type.** `apps/frontend/lib/types.ts` (`DeskScreenRow`, currently
  line 792): add `basis_as_of: string | null` and `basis_age_days: number | null`.
- **Frontend — the `/desk` basis column.** `apps/frontend/app/desk/page.tsx`: one new "basis"
  column on `DeskRowsTable`'s header (currently lines 281-290) and `DeskRow` (currently lines
  220-265) — descriptive text only, e.g. `"basis 2026-07-13 · 12 d before as-of"` (goal.md's own
  example), rendering `"basis not recorded in this snapshot"` when either field is absent
  (**absent, not just `null`** — a legacy JSON row omits the key entirely, so check with
  `row.basis_as_of == null`, not `=== null`, or the loose-equality equivalent — a real trap for
  this iteration). Extend `deskRowDrillInTitle` (currently lines 189-194) with the full-precision
  basis detail — never a new per-cell `title` (the iter-6/iter-7 stretched-link lesson: any
  per-cell `title` in this row is pointer-unreachable under the `absolute inset-0` drill-in
  anchor). The skip-rows table (4 columns: symbol/reason/coverage/tick evidence) is **not**
  touched — skip rows structurally never carry basis fields.
- **Backend — tooltip guard extension.** Extend `test_desk_hover_tooltip_guard.py` (the existing
  source-introspection pattern) so it also asserts `deskRowDrillInTitle`'s source references
  `basis_as_of`/`basis_age_days`, mirroring its existing `distance_bps`/`band_score` checks.
- **Golden replay script.** Record `runs/goal-session-desk/journey-scripts/J-08.json` (the
  J-04/J-05/J-07 precedent format) against a **scoped throw-away backend** (own `.data/` copy —
  never the ambient store, per the iter-4/iter-5 lessons), with a post-match liveness assertion
  (iter-4 lesson: assert the page is still alive *after* the first matching string). If any step
  needs to trigger a NEW screen compute to exhibit basis data, scope that replay's backend
  explicitly. Prove it with `--mode verify --journeys J-08` against the fixture-scoped rig.
- **Dev handoffs.** `docs/handoffs/goal-desk-iter-9-dev.md` (backend) and
  `docs/handoffs/goal-desk-iter-9-frontend.md` (frontend) — this session's established two-lane
  convention (every prior iteration with a frontend touch wrote both).

**Explicit non-goals for this iteration** (already excluded by the phase spec — carried here as a
guardrail, not new scope): no edit to `tradability.py`/`levels.py`/`bars.py`/`StructureChart.tsx`/
`PriceChart.tsx`/engine/any R-1 file; no new `Config` field, route, page, or MCP tool (the
`desk_screen` MCP proxy and `desk_routes.py`'s `GET /research/desk/screen` need **zero code
change** — both routes already return plain `dict`s with no `response_model` narrowing the shape,
confirmed by reading `desk_routes.py:248-266`, so the two new dict keys flow through automatically);
no backfilling any snapshot; no `bar-index-store-reconcile` work (explicitly not promoted); no
PnL-ledger append; no re-verification of J-01–J-07's own acceptance beyond the smoke-set replay.

## Agents Required

- backend-data: yes -- `desk_screen.py` row-builder + calendar-day-diff helper, the zero-extra-call
  guard test, the extended `test_desk_screen.py` goldens (TC-1..TC-4/TC-8/TC-9), the
  `test_desk_hover_tooltip_guard.py` extension, running the full suite + fingerprint check.
- frontend-ux: yes -- `types.ts` field additions, the `/desk` basis column + honest fallback +
  tooltip extension in `page.tsx`, the `null`-vs-`undefined` legacy handling, a clean
  `rm -rf .next` rebuild.

## Frontend Present

yes

## Files to Create/Modify

- `apps/backend/app/research/desk_screen.py` -- ranked-row branch in `compute_screen` (~:310-325)
  gains `basis_as_of`/`basis_age_days`; a small local helper for the calendar-date diff.
- `apps/backend/tests/test_desk_screen.py` -- extended goldens (TC-1/TC-2/TC-3/TC-4), new
  zero-extra-`compute_tradability`-call guard test (TC-8), legacy-fixture-file read test.
- `apps/backend/tests/test_desk_hover_tooltip_guard.py` -- extend the existing source-introspection
  checks to cover the basis fields in `deskRowDrillInTitle`.
- `apps/frontend/lib/types.ts` -- `DeskScreenRow` (~:792) gains the two nullable fields.
- `apps/frontend/app/desk/page.tsx` -- `DeskRowsTable` header (~:281-290), `DeskRow` (~:220-265),
  `deskRowDrillInTitle` (~:189-194).
- `runs/goal-session-desk/journey-scripts/J-08.json` -- new golden, scoped backend.
- `docs/handoffs/goal-desk-iter-9-dev.md`, `docs/handoffs/goal-desk-iter-9-frontend.md` -- handoffs.
- Not expected to change: `apps/backend/app/research/desk_routes.py` (dict pass-through, verified
  no `response_model` narrows the row shape), `app/mcp/__init__.py` (byte-identical GET proxy),
  `apps/backend/tests/test_mcp_server.py` (re-run only), `tests/test_copy_discipline.py` (re-run
  only), any `Config` file.

## UI Evolution

- New user-facing capability: every ranked `/desk` row discloses the calendar age of the price
  reading its distance/class was measured from.
- New information displayed: `basis_as_of` (the daily-bar date) and `basis_age_days` (days before
  the screen's own `as_of`) per ranked row of new screens; an honest
  `"basis not recorded in this snapshot"` state on every ranked row of a screen recorded before
  this iteration (both on the latest view and via J-05's history drill-through — same `DeskRow`
  component, no separate render path).
- New user actions: none — the existing Run Screen button's output simply carries two more fields.
- UI surface changes: one new "basis" column on the ranked-rows table only; the row anchor's
  existing consolidated hover tooltip (`deskRowDrillInTitle`) gains the full-precision basis line.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `NUMERIC_CELL`/`LABEL_CELL`/`HEADER_CELL*` styling
  constants already defined in `page.tsx` — no new component, no new color token, no new panel.
- Layout: append the "basis" column as an 8th column on the existing `DeskRowsTable` (ranked rows
  only); the skip table stays its existing 4 columns, unchanged.
- Key visual effects: none new — matches the page's existing dense/terminal-grade table styling.
  Descriptive text only (`"basis 2026-07-13 · 12 d before as-of"`), consistent with the
  copy-discipline rail — no color-coded freshness/urgency indicator (e.g. no red-for-stale
  styling), since that would edge toward advice/urgency language the project's copy lint forbids.
- States to handle: (1) a fresh row (basis age small, e.g. ≤2 d) and (2) a stale row (basis age
  large, e.g. ≥10 d) both legible in one screenshot (TC-12); (3) the legacy
  "basis not recorded in this snapshot" fallback on pre-iteration snapshots, reachable both as the
  latest screen and via history drill-through; no new top-level loading/empty/error state beyond
  what J-04 already ships.

## Key Test Scenarios

- TC-1/TC-2: fixture-scoped screen compute — new ranked row's `basis_as_of` byte-identical to
  `GET /research/tradability`'s own `basis_as_of` for that symbol/as_of; `basis_age_days` matches
  the exact calendar-day count (golden-asserted, e.g. a 12-day case).
- TC-3: identical-pins re-run reproduces byte-identical rows (incl. the two new fields) and writes
  no second file.
- TC-4: the two real pre-iteration screen snapshot files' SHA-256 checksums are unchanged
  before/after this iteration's full diff, and `GET /research/desk/screen?date=<either>` serves
  their rows with both fields absent.
- TC-8: `compute_tradability` call count during a screen compute equals exactly the member count —
  zero calls attributable to the basis fields (new guard test).
- TC-9: full backend suite green at/above 1341 passing / 8 skipped, `Config().config_fingerprint()`
  still `08e471b10130e1e2`.
- TC-10/TC-11: `test_mcp_server.py` and `test_copy_discipline.py` re-run green, unmodified — no
  code change expected in either surface.
- TC-5/TC-6: browser — `/desk` ranked table shows the descriptive basis column for rows that have
  it, and the honest fallback text for legacy rows (reachable via J-05 history drill-through too).
- TC-7 + hit-test: hovering anywhere in a row shows the composite tooltip including full-precision
  `basis_as_of`; a `document.elementFromPoint` check at the **new basis cell's own center** confirms
  the drill-in anchor (not the `<td>`) is still topmost — the iter-6 lesson's specific remedy,
  re-verified because the table gained a column and cell centers moved.
- TC-12: real browser, T-9 clean rebuild (`rm -rf apps/frontend/.next`), scoped copy of real data
  with a natural age spread (AAPL ~1d, MSFT ~4d, META/NFLX/NVDA ~12d per the proposer's own
  measurement) — one screenshot shows a ≤2d row and a ≥10d row together, legible.
- TC-13/TC-14: smoke-set deterministic replay of J-01–J-07 (not a full re-verification — "do not
  redo" per `iteration-state.md`) plus a fresh `--mode verify --journeys J-08` run, both against a
  fixture-scoped backend, zero write-path side effect on the ambient `.data/`.
- TC-16: `git diff` shows zero changes to `tradability.py`, `levels.py`, `bars.py`,
  `StructureChart.tsx`.
- A `[NEW]`-flagged demo-narrator walkthrough of the basis disclosure (fresh + stale case) is a
  downstream showcase-step requirement, not a dev-lane deliverable — flagged here so the iteration
  doesn't close without it.
