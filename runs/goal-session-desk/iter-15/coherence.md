# Iteration 15 — Coherence Audit

**Iteration:** goal-desk-iter-15
**Date:** 2026-07-29
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Iteration touches exactly one registered Data Contract row ("Screen snapshots, rank rows, skip
rows", `blueprint.md`), adding two new ranked-row-only fields (`history_sessions`,
`history_start`). No new endpoint, no new store, no new MCP tool.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Screen snapshots, rank rows (`history_sessions`/`history_start`) | OK | `apps/backend/app/research/desk_screen.py:249-283` (renamed `_resolve_reference_close` → `_resolve_reference_close_and_history`, still the ONE `store.merged_bars(symbol, "1d")` call per symbol, TC-6-guarded at `apps/backend/tests/test_desk_screen.py:915-949`); attached in the same `elif` row-builder branch at `desk_screen.py:370-388`; served verbatim by the unchanged `GET /research/desk/screen` (no route diff) |
| `basis_as_of`/`basis_age_days` (J-08, pre-existing) | OK | unchanged — `desk_screen.py`'s basis-derivation logic is only renamed/extended in place, not duplicated; `basis_as_of` still comes from `compute_tradability` verbatim |
| `DeskScreenRow` type (frontend) | OK | `apps/frontend/lib/types.ts:819-820` adds the two fields to the existing interface — no new fetch, no client-side derivation; `page.tsx` renders `row.history_sessions`/`row.history_start` straight off the row object the page already has from `GET /research/desk/screen` |
| Single-source-of-truth cross-check | OK (test-verified) | `test_aapl_row_history_cross_checks_against_get_candles` (`test_desk_screen.py:989+`) independently proves the row's `history_sessions`/`history_start` match a filtered read of `GET /research/candles` — the exact cross-check pattern this gate looks for |
| Bands/levels/bars/coverage/edge-report/PnL/strategies/taxonomy/routes/config_fingerprint (unchanged owners) | OK | zero diff — confirmed via `git diff` file list (only `desk_screen.py`, its two test files, `page.tsx`, `types.ts` changed) |

No new displayed value outside the contract; the two new fields were pre-registered in
`blueprint.md`'s "iter-15 addition" note (Data Contract, "Screen snapshots, rank rows, skip rows"
row) and the new "RESOLVED at iter-15" scope note, both present in the diff, BEFORE the code that
implements them — matching this session's own registration-before-build precedent (J-01/02/03/08/09/10).

## Information Architecture check

No new page, route, or nav entry this iteration — confirmed by the UI surface map
(`reports/phase-goal-desk-iter-15-ui-surface-map.md`: "Navigation changes: no", "New pages/routes:
0") and by the diff itself (only a `<th>`/`<td>` column and a tooltip-string addition inside the
existing `DeskRowsTable`/`DeskRow` components on the already-registered `/desk` page).

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` `history` column + tooltip addition (J-11) | OK | `apps/frontend/app/desk/page.tsx:328-336` (new `<td data-testid="desk-row-history">`) and `:365-368` (new `<th>`) — both inside the existing `/desk` page, which is already the registered J-04/05/08/09/10 canonical home in `blueprint.md`'s Feature/journey-homes table; `app/meta.py` `UI_ROUTES` (nav owner) not touched — confirmed no diff on `apps/backend/app/meta.py` in `git diff --stat` |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `blueprint.md`'s own new "iter-15 addition" prose (Data Contract, "Screen snapshots, rank rows,
  skip rows" row) still names the walk function as `_resolve_reference_close` — the actual diff
  renamed it to `_resolve_reference_close_and_history` (`desk_screen.py:249`). This is a
  documentation-currency slip inside the blueprint's own descriptive text, not a code-path
  divergence (the single canonical function, single call site, single endpoint all still hold, and
  the module docstring at `desk_screen.py:66-75` correctly uses the new name). No action required
  to unblock; worth a one-line fix next time the blueprint is touched.
- Otherwise no label/formatting drift observed: the `history` column follows the exact same
  rounded-display/full-precision-on-hover split, legacy-absence wording ("history not recorded in
  this snapshot"), and `== null` presence-check convention already established by the `basis`
  column (J-08), so the two disclosure columns read consistently.
