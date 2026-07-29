# Iteration 18 — Coherence Audit

**Iteration:** goal-desk-iter-18
**Date:** 2026-07-29
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Screen snapshots, rank rows — `opposite_band` (new field) | OK | Computed in `apps/backend/app/research/desk_screen.py:33-42` (`_select_opposite_band`), invoked from `compute_screen` at `desk_screen.py:373-377` from the SAME `result["bands"]` list `_select_best_band` already consumed (no second `compute_tradability` call, no second `BarStore` read). Served by the already-registered `GET /research/desk/screen` — no new route. |
| Screen snapshots, rank rows — `bands_by_class` (new field) | OK | `apps/backend/app/research/desk_screen.py:45-53` (`_bands_by_class`) — a plain count over the same `result["bands"]` list, same endpoint. |
| Bands / tradable-map scores (canonical owner: `tradability.py`) | OK — zero diff | `tradability.py` does not appear in the iteration diff at all; `apps/backend/tests/test_desk_screen.py:408-459` (`test_opposite_band_and_bands_by_class_add_zero_extra_compute_tradability_or_merged_bars_calls`) is a call-count guard asserting exactly one `compute_tradability` call and zero extra `BarStore.merged_bars` calls per symbol. `test_desk_screen.py:189-230` (extended at :192-230) cross-checks the new fields byte-identical against a live `GET /research/tradability` call. |
| MCP `desk_screen` tool / `get_endpoint` proxy | OK | `apps/backend/tests/test_mcp_server.py:548-610` — new test asserts both proxy paths return the two new fields byte-identical to the direct REST response; zero MCP code change, 17-tool contract unaffected. |
| Frontend render (`/desk` `DeskRow`/`deskRowDrillInTitle`) | OK — verbatim render, no client-side derivation | `apps/frontend/app/desk/page.tsx:677-685` (new `opposite` cell) and `:657-661` (new tooltip line) render `row.opposite_band`/`row.bands_by_class` fields directly; the existing arithmetic-derivation guard in `apps/backend/tests/test_desk_ui_guards.py:484-539` was extended to also forbid arithmetic on `opposite_band.*`/`bands_by_class.*` and carries its own seeded counter-test proving the guard can fail. |
| `Config`/fingerprint | OK — no new field | No `Config` changes appear in the diff; `apps/frontend/lib/types.ts:723-731` adds the two fields as plain optional TS types, no new endpoint or route file touched. |

No duplicate computation, no non-canonical fetch path, and no unregistered value: both `opposite_band` and `bands_by_class` are explicitly registered in the blueprint's Data Contract (`runs/goal-session-desk/state/blueprint.md`, the "Screen snapshots, rank rows, skip rows" row's iter-18 addition note, plus the `RESOLVED at iter-18` build-time-scope note) and in the Feature/journey homes table (J-14 → `/desk`, Desk section) as part of this same iteration's diff.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` — new `opposite` table column + tooltip line (no new page/route) | OK | `apps/frontend/app/desk/page.tsx` — a new `<td data-testid="desk-row-opposite">` cell (:677) and `<th>opposite</th>` header (:693) added to the already-registered `DeskRowsTable`/`DeskRow` components on the existing `/desk` route; `app/meta.py` `UI_ROUTES` (the single nav owner) is untouched by this diff, and no new route file is introduced. The blueprint's Navigation-skeleton Desk description already names this exact iter-18 addition ("adds one more table column ('opposite') ... no new section, no new control"). |

No new page, no parallel shell, no duplicate home — this iteration adds a column and a tooltip line to an already-registered canonical home, matching the blueprint verbatim.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- Two of the new frontend comments in `apps/frontend/app/desk/page.tsx` (lines 642 and 669) use the label "era-desk-iter-18" instead of the "goal-desk-iter-18" convention used everywhere else in this file and in the backend diff. Purely a comment-text inconsistency (not user-visible, not a Data Contract or IA issue) — worth a one-line cleanup next time this file is touched, not worth its own iteration.
