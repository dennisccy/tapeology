# goal-desk-iter-17 Execution Plan

## What to Build

Single journey **J-13**: record ONE new desk-owned field, `reference_close`, on every ranked
screen row (backend), and surface it on `/desk`'s ranked table beside the row's own
already-recorded `price_low`–`price_high` band range (frontend) — closing the gap where
"price is inside the wall" is currently unrecoverable arithmetic (the raw close is bound locally
in `compute_screen` at `desk_screen.py:370` and dropped before being returned).

- **Backend — `reference_close` field.** In `apps/backend/app/research/desk_screen.py`,
  `compute_screen`'s ranked-row dict (built at ~:374-389, in the `else` branch after
  `_resolve_reference_close_and_history` runs) already binds `close` at line 370 (`close,
  history_sessions, history_start = _resolve_reference_close_and_history(...)`) before calling
  `_select_best_band` (:373) and `_distance_bps` (used as a row value at :379). Add
  `"reference_close": close` to the row dict — copied verbatim from the SAME `close` local: zero
  new `BarStore` read, zero new accessor, zero re-derivation of which bar is the basis. Skip rows
  carry nothing (the `no_bars`/`no_basis` skip branches at ~:360-368 are untouched — same J-08/J-11
  shape).
- **Backend — module docstring.** Add a new "Reference-close disclosure (goal-desk-iter-17, J-13)"
  paragraph to the module docstring, mirroring the existing "Basis disclosure" (~:56-67) and
  "History disclosure" (~:69-77) paragraphs: the field is copied from the same `close` local, the
  legacy-row (entirely-absent-key, never `null`) fallback contract, zero additional
  `BarStore`/`compute_tradability` work. Update `compute_screen`'s own docstring field-list
  sentence (~:323-326, currently naming `basis_as_of`/`basis_age_days`/`history_sessions`/
  `history_start`) to also name `reference_close`.
- **Backend tests (`apps/backend/tests/test_desk_screen.py`).** Follow the exact precedent of
  `test_basis_fields_add_zero_extra_compute_tradability_calls` (~:699) and
  `test_history_fields_add_zero_extra_merged_bars_calls` (~:922):
  - A fixture-scoped golden asserting the exact `reference_close` per ranked row, including one row
    whose close lies INSIDE its own recorded band (`distance_bps == 0.0`) and one whose close lies
    outside it (TC-1).
  - A cross-check that each row's `reference_close` is byte-identical to the `close` of the `1d`
    bar dated at that row's own `basis_as_of`, read via
    `GET /research/candles?symbol=<sym>&timeframe=1d` — mirroring
    `test_aapl_row_history_cross_checks_against_get_candles` (~:961) (TC-2).
  - Byte-identical row content on a re-run under identical pins — extends the existing
    recompute-identity test pattern at ~:875-903 (TC-4).
  - A legacy-row absence check: `reference_close` key entirely absent, not `null`, on a snapshot
    recorded before this change — mirrors the tests at ~:760 and ~:905 (TC-5).
  - A `merged_bars` call-count guard: `BarStore.merged_bars(symbol, "1d")` invoked exactly once per
    symbol, no additional read beyond the one existing walk — mirrors ~:922 (TC-7).
  - A rank-order-unchanged check: the new screen's ranked-row symbol sequence is byte-identical to
    a pre-change golden fixture for the same five pins (`_row_rank_key`, ~:241, appears only as
    unchanged CONTEXT in `git diff`) (TC-3).
- **Backend test (`test_mcp_server.py`).** Confirm the MCP `desk_screen` tool and `get_endpoint`'s
  `/research/` allowlist proxy the new field with zero code change (byte-identity of the GET
  response; 17-tool contract unaffected) (TC-10).
- **Frontend — `lib/types.ts`.** `DeskScreenRow` (~:807-821): add
  `reference_close?: number | null;` beside `price_low`/`price_high` (~:813-814), following the
  exact optional-field pattern `basis_as_of`/`history_sessions` already use for a
  legacy-row-absent value. Extend the interface's doc comment (mirroring the "era-desk-iter-9"/
  "era-desk-iter-15" paragraphs above it, ~:792-806) with an "era-desk-iter-17 (J-13)" paragraph.
- **Frontend — `apps/frontend/app/desk/page.tsx`.**
  - `DeskRow` (~:291-355): add one new `<td>` cell, `data-testid="desk-row-band"`, rendering
    `row.price_low`–`row.price_high` beside `row.reference_close` (e.g.
    `band 488.50–490.85 · close 490.85`), with the honest
    `"close not recorded in this snapshot"` fallback when `row.reference_close == null` —
    following the same rounded-display (`fmt()`) split the basis/history cells (~:339-352)
    already use. Insert it as the LAST column, after the `history` cell (~:348-352), matching
    J-11's own "append after the existing last column" precedent.
  - `DeskRowsTable` header (~:370-382): add the matching `<th className={HEADER_CELL_LEFT}>band</th>`
    after the `history` header (~:381).
  - `deskRowDrillInTitle` (~:248-263): extend the composite tooltip with a `bandLine` following the
    exact `basisLine`/`historyLine` pattern (absence check via `row.reference_close == null`,
    full-precision value, `"close not recorded in this snapshot"` fallback) — appended to the
    returned template string. NEVER a new per-cell `title` under the stretched `absolute inset-0`
    drill-in anchor (the iter-6/iter-7 audit F2 lesson, applied proactively exactly as J-08/J-11
    already did).
  - Add an inline comment block above `DeskRow` (mirroring the existing iter-9/iter-15 comment
    blocks at ~:334-347) documenting the iter-17 addition.
- **Copy-discipline confirmation.** Confirm `apps/backend/tests/test_copy_discipline.py` (the
  frontend-literal lint, per goal.md's own framing "`tests/test_copy_discipline.py`'s
  frontend-literal lint (:220)") passes unmodified against the new `band`/`close` copy strings —
  no advice/imperative/prediction language (TC-11).
- **No-client-recomputation guard.** A source-scan test asserting no expression in
  `apps/frontend/app/desk/page.tsx` derives a price value via arithmetic on
  `distance_bps`/`price_low`/`price_high` outside the existing band-range display — follow the
  existing `test_desk_ui_guards.py` source-introspection-guard convention this era already
  established (TC-8).
- **Sentinel checks (every iteration).** `Config().config_fingerprint()` still
  `08e471b10130e1e2`; zero new `Config` field; `git diff --stat` shows zero diff to
  `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`; MCP tool count stays
  exactly 17; full backend suite green (baseline 1426 passed / 8 skipped per iter-16's handoff —
  grows, never shrinks) (TC-9).
- **Demo-narrator.** A `[NEW]`-flagged walkthrough covering: `/desk`'s ranked table showing the new
  `band` column, a row whose close sits inside its band (`distance_bps 0.0`), a row whose close
  sits outside its band, and a legacy row's honest `"close not recorded in this snapshot"` state
  (TC-12) — required by the acceptance text, and the reason the goal-decomposer set this
  iteration's depth to `full` (iter-12/iter-13 lesson: `lean`'s demo-narrator lane runs after
  scoring, so it cannot score a brand-new walkthrough clause in the same run).

## Out of scope (per goal.md / phase spec, do not build)

- Any new Data-Contract row, new endpoint, new route, or new `Config` field.
- Any diff to `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/
  `desk_coverage.py`.
- Any change to the rank key (`band_class`, `distance_bps`, `band_score`, `symbol`) or the 5-pin
  snapshot key — this journey discloses, it never ranks, filters, gates, weights, or scores.
- Any threshold, proximity/quality number, or "price is inside the band" boolean flag computed
  anywhere — the disclosure is the two raw numbers, side by side, nothing derived.
- Backfilling, rewriting, or recomputing any already-recorded screen snapshot — legacy rows keep
  their honest absent-field state forever.
- A CLI warmer for this field (the existing screen compute POST/CLI already serves it once it
  lands in `compute_screen`).
- Any WRITE to `apps/backend/.data` for evidence capture — a new screen compute for a
  not-already-recorded pin set, if needed for evidence, runs on a fixture-scoped rig only
  (iter-9/11/14/15/16 scoped-rig discipline); check the target store for an existing snapshot
  under the same five pins first and disclose any unavoidable collision (iter-10 lesson).
- J-12's `evidence_makeup: true` one-page re-capture — carried, not this iteration's concern (ride
  it on whichever lane next touches Screen History).

## Agents Required

- developer: yes -- implements both the backend change (backend-data: yes -- `desk_screen.py`
  field + docstring + tests) and the frontend change (frontend-ux: yes -- `types.ts`/`page.tsx`
  band column + tooltip + guard test) described above. This pipeline has one `developer` agent
  role that handles both backend and frontend work; there is no separate backend-data/frontend-ux
  agent in the catalog.

## Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/research/desk_screen.py` -- `compute_screen`'s ranked-row dict (~:374-389)
  gains `reference_close`; module docstring gains a "Reference-close disclosure" paragraph
  (~after :77); `compute_screen`'s own docstring field-list sentence updated (~:323-326).
- `apps/backend/tests/test_desk_screen.py` -- new "reference-close disclosure
  (goal-desk-iter-17, J-13)" section: golden per-row assertion (in-band + out-of-band rows),
  candles cross-check, byte-identical re-run, legacy-row absence, `merged_bars` call-count guard,
  rank-order-unchanged check.
- `apps/backend/tests/test_mcp_server.py` -- `desk_screen` tool / `get_endpoint` byte-identity
  extended to cover the new field (zero code change expected).
- A source-scan test for the no-client-recomputation guard (TC-8) -- add to
  `apps/backend/tests/test_desk_ui_guards.py` if that file already hosts this era's other
  page.tsx source-introspection guards, else developer's discretion on placement.
- `apps/frontend/lib/types.ts` -- `DeskScreenRow.reference_close?: number | null;`
  (~after :814) + doc-comment paragraph.
- `apps/frontend/app/desk/page.tsx` -- `DeskRow` (~:291-355) new `band` `<td>`;
  `DeskRowsTable` header (~:370-382) new `<th>band</th>`; `deskRowDrillInTitle` (~:248-263) new
  `bandLine`.
- `docs/handoffs/goal-desk-iter-17-dev.md` -- dev handoff (required by Definition of Done).

## UI Evolution

- New user-facing capability: the operator (and any Claude/MCP reader of `desk_screen`) can see,
  for every ranked row, the exact price the wall was measured from beside the band range it sits
  in or short of — "price is inside the wall" becomes a legible fact instead of unrecoverable
  arithmetic.
- New information displayed: `reference_close` (the daily close the row's band selection and
  distance were computed from) and the row's own already-recorded `price_low`–`price_high` band
  range, rendered together in a new `band` column and in the row's composite hover tooltip.
- New user actions: none — read-only render, no new button or control.
- UI surface changes: one new `band` column on the existing `/desk` ranked-rows table
  (`DeskRowsTable`/`DeskRow`, growing from nine to ten columns); one new line in the row's
  existing composite drill-in tooltip. No new page, no new section, no new nav row.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `LABEL_CELL`/`NUMERIC_CELL`/`HEADER_CELL_LEFT` cell
  classes and the `fmt()` rounded-display helper already used by the distance/score/basis/history
  cells — no new component.
- Layout: no layout restructuring — one additive column appended after the existing `history`
  column, within the already-shipped ranked-rows table.
- Key visual effects: none new — match the existing dark, dense, terminal-grade styling already
  on `/desk`.
- States to handle: a legacy row (recorded before this iteration, `reference_close` key absent)
  renders the honest `"close not recorded in this snapshot"` fallback — `== null` (loose
  equality) must catch both `undefined` and explicit `null`, per this project's established
  convention; a row whose close sits exactly on a band edge (`distance_bps 0.0`) and a row whose
  close sits off it must both be legible in the same screenshot for the browser acceptance (TC-6).

## Key Test Scenarios

- TC-1/TC-2: a NEW screen's every ranked row carries `reference_close` equal to
  `_resolve_reference_close_and_history`'s `close`, cross-checked byte-identical against
  `GET /research/candles?symbol=<sym>&timeframe=1d`'s `close` at that row's own `basis_as_of`.
- TC-3: the new screen's ranked-row symbol sequence is byte-identical to a pre-change golden for
  the same five pins.
- TC-4: a re-run under identical pins returns the already-recorded response, byte-identical, no
  new file written.
- TC-5: a pre-iteration screen snapshot's ranked rows carry no `reference_close` key (absent, not
  `null`); on-disk checksum unchanged; `/desk` renders the honest fallback.
- TC-6 (browser): `/desk`'s ranked table `band` column shows, in ONE screenshot, at least one row
  whose `reference_close` lies inside its own `price_low`–`price_high` range and one row whose
  close lies outside it, both legible.
- TC-7: `BarStore.merged_bars(symbol, "1d")` invoked exactly once per symbol — call-count guard.
- TC-8: no expression on `apps/frontend/app/desk/page.tsx` derives a price value via arithmetic
  on `distance_bps`/`price_low`/`price_high` outside the existing band-range display.
- TC-9: full suite green; `Config().config_fingerprint()` == `08e471b10130e1e2`; zero diff to
  `tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`; zero new `Config`
  fields.
- TC-10: MCP `desk_screen` tool's JSON byte-identical to the direct GET for the same snapshot;
  tool count exactly 17.
- TC-11: `tests/test_copy_discipline.py` passes unmodified.
- TC-12 (demo-narrator): `[NEW]`-flagged J-13 walkthrough, `Demo Verdict: RECORDED`, non-empty
  gallery narrating the `band` column, an in-band row, an out-of-band row, and a legacy row's
  honest fallback.
- Regression smoke green: J-01 through J-12 (all twelve required-still-passing journeys per the
  phase spec's metadata).

## Notes / Assumptions

- No assumption-ledger entry needed this iteration — J-13's steps and acceptance text in goal.md
  are fully prescriptive (exact field name, exact source variable `close` at `desk_screen.py:370`,
  exact rendering pattern, exact test scenarios), matching the phase spec's own NOTES section.
- This is a pure additive-disclosure iteration: no new module, route, MCP tool, or `Config`
  field. Every backend edit is confirmed against the current file (`desk_screen.py` read and
  verified against this plan, line anchors matched); every frontend edit is confirmed against the
  current `page.tsx`/`lib/types.ts` (line anchors re-verified against the live file, not assumed
  from the spec).
- Alignment with `docs/goal.md`: this iteration is J-13, the `AUTO:journeys`-appended sixth
  proposer addition this era, and advances Success Criterion 4 ("The briefing is a real product
  surface") without touching the Data Contract's canonical owners (Success Criterion 3's
  byte-for-byte match invariant) — no drift from the project goal detected; the phase spec is
  fully in scope, nothing flagged as out-of-bounds.
- Environment: before running any command that writes temp files, `export
  TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-17.3302867"
  TMP="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-17.3302867"
  TEMP="/home/dennis-chan/.cache/iad/iad.goal-desk-iter-17.3302867"`.
