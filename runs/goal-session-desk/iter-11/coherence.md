# Iteration 11 — Coherence Audit

**Iteration:** goal-desk-iter-11
**Date:** 2026-07-28
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Top-up run records (per-run outcome ledger) — NEW at iter-11 (J-09) | OK | Computed by the sole shared writer `record_topup_run` (`apps/backend/app/research/desk_topup_log.py:210`) over `TopupRunStore.record` (`:162`). Served by exactly one route, `GET /research/desk/topup/runs` (`apps/backend/app/research/desk_routes.py:252`). UI reads it verbatim via `fetchDeskTopupRuns()` hitting the same path (`apps/frontend/lib/api.ts:1119-1125`) — no second fetch site (only call sites are the mount effect and the terminal-state poll refetch in `apps/frontend/app/desk/page.tsx:1069-1072,1113-1119`). Shape matches the blueprint's registered row (`runs/goal-session-desk/state/blueprint.md`, "Top-up run records" row) field-for-field. |
| Top-up compute progress (existing row, J-02) | OK — shape unchanged | `self._snapshot` in `apps/backend/app/research/desk_topup_compute.py`'s `trigger()` (~:250-258) still carries the same 5 keys as before this iteration; the new `topup_run_store` param and `_record_run`/`collected` closures (`:262-268`, `:301-311`) are additive plumbing that read the job's own already-published outcomes — they write to the new store, never add a key to `self._snapshot`. |
| `run_topup` / `_run_one_pair` (existing computation, J-02) | OK — byte-unchanged | Diff touches only the callers (`trigger()`, `_work()`, `main()`); the function bodies themselves (blueprint-cited `desk_topup_compute.py:123-188`) show no lines changed. `test_manager_triggered_runs_persisted_outcomes_are_byte_identical_to_run_topups_own_return` (`apps/backend/tests/test_desk_topup_compute.py`, added this iteration) spies on the real `run_topup` and asserts the persisted record's `outcomes` equal its actual return value — proves the store is a pure read of the one existing computation, not a second implementation. |
| Per-member bar coverage + freshness (`desk_coverage.py`) | OK — untouched | `git diff 8115346.. --stat -- apps/backend/app/research/desk_coverage.py` is empty. J-09 imports nothing from it; the blueprint's own note ("J-09 reads NOTHING from this row") holds. |
| Route / nav inventory (`UI_ROUTES`) | OK — untouched | `git diff 8115346.. --stat -- apps/backend/app/meta.py` is empty; `apps/backend/app/meta.py:31-35` still lists exactly 3 rows (`/`, `/structure`, `/desk`). |
| MCP tool surface (17 read-only tools) | OK — untouched, new route reached via existing allowlist | `git diff 8115346.. --stat -- apps/backend/app/mcp/__init__.py` is empty (no new `_STATIC_PATHS` entry). New test `test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool` (`apps/backend/tests/test_mcp_server.py:904-924`) proves `get_endpoint("/research/desk/topup/runs")` is byte-identical to the direct REST call and asserts `len(TOOL_NAMES) == 17`. |
| Frozen foundations (`tradability.py`, `levels.py`, `bars.py`, `StructureChart.tsx`) | OK — zero diff | `git diff 8115346.. --stat` for all four paths returns nothing. |
| Client-side derived display fields (outcome counts, unreached-pairs count) | OK — re-format, not duplicate computation | `topupOutcomeCounts()` (`apps/frontend/app/desk/page.tsx:512-521`) and `unreached = run.pairs_total - run.pairs_attempted` (`page.tsx:585`) are pure tallies/arithmetic over fields (`outcomes`, `pairs_total`, `pairs_attempted`) already delivered verbatim by the one canonical endpoint in the same response — no other module anywhere computes an "outcome count" or "unreached pairs" value these could diverge from, so Part A.3 (re-format is fine) applies. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` "Top-up Runs" section (J-09) | OK | `apps/backend/app/meta.py:31-35` (`UI_ROUTES`, unchanged, 3 rows) — `/desk` was already `nav: True` before this iteration, confirmed via zero diff on this file. `apps/frontend/app/desk/page.tsx:1276` places the new `<section aria-label="Top-up runs">` as a direct sibling of the existing screen-state ternary inside the same `<main>` (not nested inside any conditional branch, not a new component tree, no new route) — reachable in the same 1 click from the persistent top nav as the rest of `/desk`. No `NavBar.tsx` diff. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Disclosed placement deviation, not a violation.** The blueprint's nav-skeleton text describes the new section as added "beside Screen History." The implementation renders it as an always-visible top-level section (sibling of the screen-state conditional, `apps/frontend/app/desk/page.tsx:1276`) rather than nested inside `DeskPopulatedScreen`, so it is visible even when no screen has ever been computed. This is logged as an explicit, reasoned interpretation call in `runs/goal-session-desk/state/assumptions.md` ("iter-11 — developer" entry): nesting it inside the screen branch would hide the section on the very "zero top-up runs, zero screens" empty-state screenshot TC-12 requires, and a top-up run is an independent operator act from a screen run with no backend ordering dependency between them. The section still lives on the one already-registered canonical `/desk` home, still one click from nav, still no duplicate/parallel shell — noting only for visibility, since it is a legitimate, disclosed reading of "beside" in the page's top-to-bottom flow rather than DOM nesting.
- Client-side derived fields (outcome tallies, unreached-pairs count) were checked and found to be pure arithmetic over the single canonical payload — see the Data Contract table's last row. Flagged there as reviewed, not a violation.
