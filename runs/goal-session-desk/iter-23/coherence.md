# Iteration 23 — Coherence Audit

**Iteration:** goal-desk-iter-23
**Date:** 2026-07-30
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `band_member_count` (new ranked-row field, J-15) | OK | `apps/backend/app/research/desk_screen.py:507` — `"band_member_count": best["member_count"]`, where `best = _select_best_band(result["bands"], close)` is the SAME call already used for `band_class`/`band_score`/`price_low`/`price_high` (line 476). No second `compute_tradability` call, no second `BarStore` read. |
| `band_round_number` (new ranked-row field, J-15) | OK | `apps/backend/app/research/desk_screen.py:508` — `"band_round_number": best["round_number"]`, read verbatim off the same `best` dict, itself built once in `tradability.py:343`'s `_band()` (`"round_number": round_number`, `"member_count": len(members)`). |
| `band_member_timeframes` (new ranked-row field, J-15) | OK | `apps/backend/app/research/desk_screen.py:509` — `_band_member_timeframes(best["members"])` (helper defined at :312-325) tallies the SAME `best["members"]` list `tradability.py:355`'s `_band()` already sorted and attached — no new store read, no new `compute_tradability` call. |
| Served endpoint | OK | Same existing `GET /research/desk/screen` (no new route file, no diff to `app/routes.py` desk endpoints — only `desk_screen.py`'s row builder changed). |
| Frontend rendering | OK | `apps/frontend/app/desk/page.tsx:459-473` renders `row.band_member_count`/`row.band_member_timeframes`/`row.band_round_number` straight off the already-fetched `GET /research/desk/screen` response (`DeskScreenRow` type, `apps/frontend/lib/types.ts:857-859`) — no new fetch, no client-side recomputation. |
| Skip-row exclusion | OK | `apps/backend/app/research/desk_screen.py:462-469` — both skip-row branches (`reason: "no_bars"` / `"no_basis"`) construct `{"symbol", "skipped", "reason", "coverage", "tick_evidence"}` only; none of the three new keys appear. |
| Single-owner check (repo-wide) | OK | `grep -rl "band_member_count\|band_round_number\|band_member_timeframes"` over `apps/backend/app`, `apps/backend/tests`, `apps/frontend/app`, `apps/frontend/lib`, `apps/frontend/components` returns exactly the four expected files (`desk_screen.py`, `test_desk_screen.py`, `desk/page.tsx`, `lib/types.ts`) — no parallel computation or a second serving path anywhere else. |
| Reused "round number" badge | OK | `apps/frontend/app/desk/page.tsx:466-471` vs. `apps/frontend/app/structure/page.tsx:613-620` — identical `data-testid="tradable-band-round-number"` and identical `className`; a genuine reuse, not a re-implemented sibling component. |
| Out-of-scope frozen modules | OK | `git diff` against the pre-iteration snapshot touches only `apps/backend/app/research/desk_screen.py`, `apps/backend/tests/test_desk_screen.py`, `apps/frontend/app/desk/page.tsx`, `apps/frontend/lib/types.ts` — zero diff on `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `StructureChart.tsx`, `app/config.py`, `app/mcp/__init__.py` (per the spec's OUT OF SCOPE list). |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` — new `levels` table column (J-15) | OK | No new page, no new route. `git diff --stat` against `apps/backend/app/meta.py` and `apps/frontend/components/NavBar.tsx` is empty — the nav skeleton (`UI_ROUTES`, `GET /meta/ui-routes`, still 3 rows) is untouched. The column lives inside the already-registered `/desk` canonical home (blueprint Feature/journey-homes table, J-15 row) beside the existing `band`/`opposite` columns (`apps/frontend/app/desk/page.tsx:497` header row addition). |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. This iteration is a clean, narrowly-scoped repeat of the J-08/J-11/J-13/J-14 disclosure pattern: three new fields copied verbatim from an already-computed band dict, rendered read-only in one new table column on the already-registered `/desk` page, with skip rows and legacy (pre-iteration) snapshots handled via the established honest-absence convention. No new endpoint, no new Config field, no new MCP tool, no nav change, no duplicate computation path found anywhere in the tree.
