# Iteration 6 — Coherence Audit

**Iteration:** goal-desk-iter-6
**Date:** 2026-07-26
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Screen snapshots, rank rows, skip rows (`GET /research/desk/screen`, incl. `?date=`) | OK | New client helper `fetchDeskScreenByDate()` in `apps/frontend/lib/api.ts:948-978` calls `GET /research/desk/screen?date=` — the branch already registered in `blueprint.md`'s Data Contract (shipped J-03/iter-3, `desk_routes.py:248-266`); reads `data.screen` verbatim into `DeskScreenSnapshot`, no reshape/recompute. This is the row's FIRST UI caller, not a second endpoint. |
| Snapshot-level `as_of` (part of the same contract row) | OK | `apps/frontend/app/desk/page.tsx:975` (`displayedSnapshot`) and the `<DeskPopulatedScreen>` call passing `snapshot.as_of` into `DeskRowsTable`/`DeskSkippedSection` (`page.tsx:729,737`) — `asOf` is read from the displayed snapshot object, never a per-row field, matching the contract note verbatim. |
| Bands / tradable-map, Levels/zones, Bars/candles (`tradability.py`, `levels.py`, `bars.py` via `/structure`'s existing Load endpoints) | OK | The new `/structure` prefill effect (`apps/frontend/app/structure/page.tsx:1695-1715`, `J-05-PREFILL-START/END`) calls `handleLoad(symbol, asOf)` — the SAME function the manual Load button already calls, which reads only the pre-existing canonical endpoints. No new fetch/compute function introduced. Confirmed by `apps/backend/tests/test_desk_ui_guards.py::test_structure_prefill_reuses_the_existing_load_function` (passing — verified by running the suite, `apps/backend/.venv/bin/python -m pytest tests/test_desk_ui_guards.py -q` → 5 passed). |
| Desk briefing values (must never re-derive from `/research/tradability` or `/research/levels`) | OK | `apps/backend/tests/test_desk_ui_guards.py::test_desk_page_never_references_structure_compute_endpoints` scans `apps/frontend/app/desk/page.tsx` for `/research/tradability`, `/research/levels`, `compute_tradability`, `compute_levels` — zero hits, verified passing. Each guard also carries a seeded-violation counter-test proving the check can actually fail. |
| Route / nav inventory (`app/meta.py` `UI_ROUTES`) | OK — untouched | `apps/backend/app/meta.py` is not in this iteration's diff (`git diff <snapshot-sha> --stat` shows only `apps/frontend/app/desk/page.tsx`, `apps/frontend/app/structure/page.tsx`, `apps/frontend/lib/api.ts` plus the new `apps/backend/tests/test_desk_ui_guards.py`); `UI_ROUTES` still lists exactly the 3 rows (`/`, `/structure`, `/desk`), matching the blueprint's "no nav-skeleton change" claim for iter-6. |

No new displayed value or entity is introduced this iteration (matches the iter spec's "Data-contract additions: None"). No duplicate computation, no non-canonical fetch.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` history row click-through (state swap, no navigation) | OK | Same page (`/desk`), already in nav; `apps/frontend/components/NavBar.tsx` renders links from `GET /meta/ui-routes` verbatim (unchanged this iteration) — no new route, no parallel shell. |
| `/desk` ranked/skip row → `/structure?symbol=&asof=` drill-in | OK | Registered verbatim in `blueprint.md`'s Feature/journey homes table (J-05 row): `/desk` (history list) → `/structure?symbol=<sym>&asof=<iso>`. Both endpoints already have canonical homes in the nav; the link is a `next/link` `<Link>` (`apps/frontend/app/desk/page.tsx:200-206`, `:293-299`), not a new shell. Reachable in 1 click from `/desk` (itself ≤2 clicks from nav). |
| `/structure` query-param prefill | OK | Additive-only change to the existing page; no new route created. `NavBar.tsx` unchanged; `apps/backend/app/meta.py` `UI_ROUTES` unchanged (still 3 rows). |

No new page/route this iteration — confirmed by the ui-surface-map (`reports/phase-goal-desk-iter-6-ui-surface-map.md`: "New pages/routes: 0", "Navigation changes: no").

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `apps/frontend/app/desk/page.tsx:70-73` introduces `SECONDARY_BUTTON_CLASS`, described in its own comment as a byte-for-byte copy of `structure/page.tsx`'s own constant of the same name/purpose, per this project's stated convention that each page owns its own copy of small styling constants rather than sharing one. This is a styling string, not a displayed data value, so it is not a Data Contract concern — noted only for completeness, no action needed.
- Both ranked and skipped rows now drill into `/structure` (an interpretation call logged in `assumptions.md` iter-6, since goal.md's "each briefing row" language doesn't distinguish the two). This matches the blueprint's iter-6 "RESOLVED" note verbatim — not a violation, just flagging that it is a judgment call that could be narrowed later if the owner disagrees.
