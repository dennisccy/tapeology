# goal-desk-iter-17 Dev Handoff

**Phase:** goal-desk-iter-17
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

**J-13: `reference_close` disclosure.** Every RANKED row of a NEWLY computed screen snapshot now
carries `reference_close` — the exact daily close `desk_screen.py`'s `compute_screen` already binds
locally (as `close`, line 370) to call `_select_best_band`/`_distance_bps`, and previously dropped
before returning the row. This closes the gap goal.md's J-13 named: `price_low`/`price_high` were
already recorded on every ranked row since iter-3 but never rendered anywhere on `/desk`, and the
reference close was not recorded at all — recoverable only by inverting `distance_bps` against a
band edge under the row's own `side`, the exact client-side recomputation the single-source-of-truth
rail forbids. Now the raw close and the band range it was measured against are both visible on
screen, side by side, with nothing derived.

- **Backend.** `compute_screen`'s ranked-row dict gains `"reference_close": close` — copied verbatim
  from the SAME `close` local `_resolve_reference_close_and_history` already returns (zero new
  `BarStore` read, zero new accessor, zero re-derivation of which bar is the basis). Skip rows carry
  nothing, matching the basis/history-disclosure precedent (J-08/J-11) exactly. A snapshot recorded
  BEFORE this iteration has ranked rows that OMIT the key entirely (never `null`, never backfilled).
  Module docstring gained a "Reference-close disclosure (goal-desk-iter-17, J-13)" paragraph
  mirroring the existing "Basis disclosure"/"History disclosure" sections; `compute_screen`'s own
  docstring field-list sentence now names `reference_close` too.
- **Frontend.** `DeskScreenRow.reference_close?: number | null` added to `lib/types.ts` (with a doc
  comment paragraph following the basis/history precedent). `apps/frontend/app/desk/page.tsx`:
  `DeskRow` gains a new `band` `<td>` (last column, after `history`) rendering
  `` `band ${fmt(price_low)}–${fmt(price_high)} · close ${fmt(reference_close)}` `` with the honest
  `"close not recorded in this snapshot"` fallback when `reference_close == null`; `DeskRowsTable`
  gains the matching `<th>band</th>`; `deskRowDrillInTitle` gains a `bandLine` in the row's existing
  composite hover tooltip (full precision, never a per-cell `title` under the stretched
  `absolute inset-0` drill-in anchor — the iter-6/iter-7 audit F2 lesson applied proactively, exactly
  as J-08/J-11 already did).
- **No client-side recomputation guard (TC-8).** A new source-scan test in
  `test_desk_ui_guards.py` asserts `apps/frontend/app/desk/page.tsx` never combines
  `row.distance_bps`/`row.price_low`/`row.price_high` with an arithmetic operator — the new `band`
  column renders `reference_close` beside `price_low`/`price_high` as two side-by-side served
  values, never a third, derived one.
- Zero new module, route, MCP tool, `Config` field, or Data-Contract row. `reference_close` rides
  the already-registered "Screen snapshots, rank rows, skip rows" Data-Contract row and the
  already-registered `GET /research/desk/screen` endpoint — an additive extension, not a second
  owner. `Config().config_fingerprint()` stays `08e471b10130e1e2`; MCP tool count stays exactly 17.

## Files Changed

- `apps/backend/app/research/desk_screen.py` — `compute_screen`'s ranked-row dict gains
  `reference_close`; module docstring gains a "Reference-close disclosure" paragraph;
  `compute_screen`'s own docstring field-list sentence updated.
- `apps/backend/tests/test_desk_screen.py` — new "reference-close disclosure
  (goal-desk-iter-17, J-13)" section (6 new tests): golden per-row assertion against the real AAPL
  fixture, a controlled in-band (`distance_bps == 0.0`, `reference_close` at the band's near edge,
  i.e. inside `[price_low, price_high]`) + out-of-band pair via a monkeypatched
  `compute_tradability`, a rank-order-unchanged check (`_row_rank_key` untouched), a
  `GET /research/candles` cross-check, a byte-identical-recompute-under-identical-pins check, and a
  legacy-row absence check. Also extended `test_history_fields_add_zero_extra_merged_bars_calls`'s
  docstring to note it already covers `reference_close`'s zero-extra-`merged_bars`-call guarantee
  (the field shares `_resolve_reference_close_and_history`'s existing tuple — no new test needed).
- `apps/backend/tests/test_mcp_server.py` — new
  `test_desk_screen_reference_close_field_proxies_verbatim`: byte-identity of `reference_close`
  through both the `desk_screen` tool (no-arg) and `get_endpoint`'s `?date=` proxy, zero MCP code
  change.
- `apps/backend/tests/test_desk_ui_guards.py` — new TC-8 guard
  (`test_desk_page_never_derives_a_price_via_arithmetic_on_distance_or_band_edges`) plus its
  seeded-violation counter-test; module docstring's guard list extended to (c).
- `apps/frontend/lib/types.ts` — `DeskScreenRow.reference_close?: number | null;` + doc-comment
  paragraph.
- `apps/frontend/app/desk/page.tsx` — `DeskRow` new `band` `<td>`; `DeskRowsTable` header new
  `<th>band</th>`; `deskRowDrillInTitle` new `bandLine`; module-level and per-cell comment updates.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: **1435 passed, 8 skipped, 0 failed** (exit code 0; baseline per the iter-16 handoff was 1426
passed / 8 skipped — grew by exactly the 9 new tests added this iteration, 0 regressed, skip count
unchanged). Also verified individually: `tests/test_desk_screen.py` (61 passed),
`tests/test_mcp_server.py` (38 passed), `tests/test_desk_ui_guards.py` (7 passed),
`tests/test_copy_discipline.py` (30 passed, unmodified).

Command: `cd apps/frontend && npx tsc --noEmit -p tsconfig.json`
Result: clean, zero errors.

### Sentinel checks (all confirmed)

- `Config().config_fingerprint()` → `08e471b10130e1e2` (unchanged).
- `git diff --stat` on `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/
  `desk_coverage.py` → empty (zero diff).
- `git diff --stat` on `apps/backend/app/config.py` → empty (zero new `Config` fields).
- MCP tool count: `len(TOOL_NAMES)` → 17.

### Live verification (Pre-handoff checklist)

Started the backend (`scripts/start-backend.sh`, port 8391) and frontend
(`scripts/start-frontend.sh`, port 3391) on scoped ports against the AMBIENT `.data/` store
(read-only — no `POST /compute` call was ever issued, so no write to `apps/backend/.data` occurred).
`GET /research/desk/screen` confirmed the existing (pre-iteration) `latest` snapshot's ranked rows
correctly omit the `reference_close` key entirely (not `null`). Navigated a real Chrome instance
(attached via CDP on the pre-existing `:9222` endpoint) to `/desk`: the ranked table's header row
shows `symbol · side · class · distance · score · coverage · tick evidence · basis · history · band`
(ten columns, confirmed via `document.querySelectorAll`), every visible row renders
`"close not recorded in this snapshot"` in its `band` cell (correct — every recorded ambient
snapshot pre-dates this change), and the row's drill-in anchor's `title` attribute carries the new
`bandLine` (`"... · close not recorded in this snapshot · ..."`) alongside the existing
distance/score/basis/history segments. Both dev servers were stopped afterward
(`pkill`/`kill -9` on their PIDs; `lsof -ti :8391 :3391` confirmed both ports free).

## Known Issues

- **TC-6's "one screenshot, one in-band row + one out-of-band row" browser evidence was NOT
  captured by this dispatch.** Every screen snapshot in the ambient `apps/backend/.data/` store
  predates this iteration, so every visible row on `/desk` right now honestly shows
  `"close not recorded in this snapshot"` — there is no ambient row yet carrying `reference_close`
  to screenshot. Producing one requires computing a NEW screen snapshot, which goal.md's own OUT OF
  SCOPE list restricts to a fixture-scoped rig (never a write to `apps/backend/.data`) with any
  collision against an existing golden's target store checked and disclosed first (iter-9/10/11/14/
  15/16 scoped-rig discipline) — that evidence-capture work belongs to the browser-qa-agent/
  demo-narrator lanes downstream, per this era's established division of labor (the developer's own
  job this iteration was the field + tests + UI wiring, all of which are verified above against the
  real, live, ambient legacy state). The backend test suite independently proves the in-band
  (`distance_bps == 0.0`, inside-band) and out-of-band cases exactly
  (`test_reference_close_golden_in_band_and_out_of_band_rows`), so the rendering logic itself is not
  in doubt — only the live-browser screenshot of a NEW snapshot remains for a downstream lane.
- No other gaps identified. Every backend TC (TC-1 through TC-5, TC-7, TC-9, TC-10, TC-11) has a
  dedicated or extended test; TC-3 (rank-order-unchanged) is additionally confirmed by `git diff`
  showing `_row_rank_key`'s own source as unchanged context.

---

## Auditor amendment (2026-07-29)

Audit finding **F1** changed the legacy-row rendering this handoff describes. The `band` cell and
the tooltip's `bandLine` no longer collapse to the bare string `"close not recorded in this
snapshot"` on a legacy row: they now render the row's OWN already-recorded band range first, then
the honest close-absent state —

- cell: `band ${fmt(row.price_low)}–${fmt(row.price_high)} · close not recorded in this snapshot`
- tooltip: `band ${row.price_low}–${row.price_high} · close not recorded in this snapshot`

goal.md's J-13 acceptance requires exactly this ("`/desk` renders their rows with their OWN
recorded band range plus the honest `\"close not recorded in this snapshot\"` state"), and
`price_low`/`price_high` are present and non-null on every ranked row of all six snapshots on disk,
including the oldest (`screen-2026-06-22-3ecd45c062c7`, iter-3). Re-verified live in a real browser
and by re-running the J-04/J-08/J-11/J-12/J-13 replay goldens (5/5 PASS). See
`docs/handoffs/goal-desk-iter-17-audit.md` §2/§4.
