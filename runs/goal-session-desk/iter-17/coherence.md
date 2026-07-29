# Iteration 17 — Coherence Audit

**Iteration:** goal-desk-iter-17
**Date:** 2026-07-29
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Screen snapshots, rank rows, skip rows (`reference_close` new ranked-row field) | OK | `apps/backend/app/research/desk_screen.py:382,401` — `close, history_sessions, history_start = _resolve_reference_close_and_history(...)` (the pre-existing single call, unchanged call site) is bound to `"reference_close": close` on the row dict; the SAME `close` local already feeds `_select_best_band(result["bands"], close)` (:385) and `_distance_bps(best, close)` (:391). No new `BarStore` accessor, no second read path. |
| `price_low` / `price_high` (already-registered fields, now rendered) | OK | `apps/frontend/app/desk/page.tsx` `DeskRow` (new `<td data-testid="desk-row-band">`, ~:383-387) renders `row.price_low`/`row.price_high`/`row.reference_close` verbatim via `fmt()` — a pure re-format of fields the page already receives on the fetched row object from `GET /research/desk/screen`. No new fetch, no client-side arithmetic. |
| Bands / tradable-map scores, Levels/zones, Bars/candles, Bar coverage index (unchanged owners) | OK | `git diff` confirms zero touch to `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `StructureChart.tsx` (not present in the changed-file list at all). |
| `config_fingerprint` | OK | No new `Config` field in the diff; `desk_screen.py`'s change is a plain dict key addition, not a Config-affecting change. Iteration's own DoD requires the fingerprint print `08e471b10130e1e2` unchanged. |
| MCP `desk_screen` tool / `get_endpoint` proxy (17-tool contract) | OK | `apps/backend/tests/test_mcp_server.py` diff adds `test_desk_screen_reference_close_field_proxies_verbatim`, asserting byte-identity between the `desk_screen` tool, `get_endpoint`'s `?date=` path, and the direct REST response for the new field — zero MCP code change, confirming no second serving path was introduced. |

No new value/entity was introduced this iteration that lacks a registered owner — `reference_close` was pre-registered in the blueprint's iter-17 addition note (`runs/goal-session-desk/state/blueprint.md`, "Screen snapshots, rank rows, skip rows" row) and the matching `RESOLVED at iter-17` note, both landed in this same diff, before/alongside the code.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` ranked table — new `band` column | OK (no new surface) | `apps/frontend/app/desk/page.tsx` diff only adds a `<th>band</th>` header cell to the existing `DeskRowsTable` and one `<td>` cell to the existing `DeskRow` component, plus one more segment on the existing `deskRowDrillInTitle` composite tooltip. No new route, no new page, no new nav entry. `app/meta.py` `UI_ROUTES` (the single nav owner per the blueprint) is not in the changed-file list — nav skeleton unchanged (still 3 rows). |

No new page/route/feature was introduced this iteration — this is a within-page column addition to an already-registered canonical home (`/desk`), so the reachability/duplicate-home/parallel-shell checks do not apply.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The dev team added a proactive static guard (`apps/backend/tests/test_desk_ui_guards.py`, `test_desk_page_never_derives_a_price_via_arithmetic_on_distance_or_band_edges`) that regex-scans `desk/page.tsx` for any arithmetic combining `row.distance_bps`/`row.price_low`/`row.price_high` — directly enforcing this gate's own "no client-side recomputation" rule at the test level, with its own seeded counter-test proving the lint can fail. This is a durable improvement to the coherence guarantee beyond what this audit alone can check per-iteration; noting it as a positive precedent, not a violation.
- Everything in this iteration traces cleanly to the pre-registered blueprint contract (Data Contract row + `RESOLVED at iter-17` note, both landed in the diff itself) — no drift observed.
