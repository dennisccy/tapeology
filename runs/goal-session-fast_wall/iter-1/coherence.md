# Iteration 1 — Coherence Audit

**Iteration:** goal-fast_wall-iter-1
**Date:** 2026-07-17
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Blueprint registers exactly one new row this interlude that this iteration (J-01) implements: the
not-computed edge-report payload, owned by `app/research/edge_report.py::peek_strategy_comparison_report`,
served by the existing `GET /research/edge-report` (rewired, same route). Row 2 (compute-job snapshot,
`edge_report_compute.py`) is explicitly out of scope this iteration (J-04) and no such module/route was
added — confirmed absent from the diff.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Not-computed edge-report payload (`status`/`detail`/`dataset_count`/`register`/`compute`) | OK | Computed only in `apps/backend/app/research/edge_report.py:487-518` (`peek_strategy_comparison_report`); served only by `GET /research/edge-report` (`apps/backend/app/research/routes.py:2117`, one caller confirmed by repo-wide grep). MCP `edge_report` proxies the same route byte-identically (`test_mcp_server.py:832-859`, TC-6). |
| Edge-report cells / `run_strategy_comparison_report` (frozen era-5B owner) | OK — unchanged | `_compute_strategy_comparison_report` remains the sole computation (`apps/backend/tests/test_edge_report.py:980` asserts exactly one definition, pre-existing guard untouched); `run_strategy_comparison_report` now has zero application callers (repo-wide grep: only test files and `peek_...`'s own empty-registry branch reach `_compute_strategy_comparison_report`), reserved verbatim for J-04's future compute manager. |
| Cache DB path resolution policy | OK — consolidated, not duplicated | `resolve_cache_db_path` (`apps/backend/app/research/edge_report_cache.py:200-213`) extracted FROM the previously-inline body in `routes.py`; `routes.py:1573` now calls the ONE shared function. `test_edge_report_cache.py:813-824` (new) plus `test_edge_report_route_cache_db_lives_hermetically_beside_the_test_dataset_dir` (pre-existing, unmodified) both pin the resolved path is unchanged — a coherence improvement, not a second policy. |
| `EdgeReportCache.lookup` (new, read path) | OK | Read-only by construction (no `compute_fn` parameter) and mechanically guarded: `test_edge_report.py:460-472` (`test_peek_source_never_calls_a_compute_triggering_cache_method`) asserts `peek_strategy_comparison_report`'s own source never calls `cache.get_or_compute(` or `cache.compute_and_publish(`. |
| `EdgeReportCache.compute_and_publish` (new, write path) | OK — zero app callers yet | Repo-wide grep confirms the only occurrences outside its own definition (`edge_report_cache.py:248`) are in test files — matches the iteration spec's stated scope (J-04's future CLI/route trigger; this iteration exercises it directly only via tests). |
| Frontend Edge Report display (`/structure`) | OK — re-format only | `fetchEdgeReport()` (`apps/frontend/lib/api.ts:1149-1160`) is the sole fetch, unchanged call site, hitting only the canonical `GET /research/edge-report`. `NotComputedPanel` (`apps/frontend/app/structure/page.tsx:287-297`) renders the server's own `detail` string verbatim — no client-side recomputation, no second endpoint. Repo-wide grep confirms `EdgeReportResponse`/`EdgeReportPayload`/`fetchEdgeReport` are used from exactly one source file, `apps/frontend/app/structure/page.tsx` (the `.next/` matches are compiled shared-chunk build output, not source). |

No duplicate computation, no non-canonical source. No new displayed value/entity outside the
Data Contract was introduced (the not-computed payload's fields were already registered in
`blueprint.md` at baseline, per the iteration spec's own "no blueprint edit needed" note, which I
independently verified by reading `blueprint.md` lines 58 and 89-94 — the row and the baseline probe
comment both predate this iteration and match the shipped shape field-for-field).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/structure` → Edge Report → not-computed panel | OK | Inserted as one more branch in the section's EXISTING conditional chain (`apps/frontend/app/structure/page.tsx:1879-1881`: `edgeReportResult.error` → `UnavailablePanel`, `status === "not_computed"` → new `NotComputedPanel`, else → `EdgeReportBody`) — the exact canonical home the blueprint's IA table registers for J-01 (`runs/goal-session-fast_wall/state/blueprint.md:36`). `/structure` itself is an unchanged, existing top-level nav item — 1 click, no regression in reachability. |

No new route, no new page, no new nav entry. Repo-wide `git diff --stat` against frontend paths
shows zero nav/sidebar/layout/router files touched (grep for `nav|sidebar|layout|router` over the
frontend stat returned nothing) — consistent with the blueprint's frozen-nav constraint and the
ui-surface-map's own "Navigation changes: no." `NotComputedPanel` explicitly reuses
`UnavailablePanel`'s existing amber degraded-state visual treatment per its own code comment
(`structure/page.tsx:892-896`) rather than inventing new visual language, matching the iteration
spec's Design Direction. No duplicate home, no parallel shell.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The iteration spec's own "New information displayed" prose (`docs/phases/goal-fast_wall-iter-1.md`
  line 71) states both `detail` **and** `dataset_count` "become newly visible in the Edge Report
  section." The shipped `NotComputedPanel` (`apps/frontend/app/structure/page.tsx:287-297`) renders
  only `detail`; `dataset_count` reaches typed frontend state (`EdgeReportNotComputed.dataset_count`,
  `apps/frontend/lib/types.ts:983`) but a repo-wide grep confirms it is never read or rendered
  anywhere in `page.tsx`. This is not a Data Contract violation (the value's canonical source and
  endpoint are correctly and exclusively wired — it is simply not painted to the DOM) and not an IA
  violation (no duplicate home, no nav gap) — it is a spec-completeness question, outside this gate's
  objective mandate. Noting for the record only; does not affect this verdict.

No other coherence drift observed. This iteration is a clean, narrowly-scoped implementation of
exactly the blueprint's pre-registered J-01 row: one new canonical function, one rewired (not
duplicated) route, one new panel state inside the existing canonical home, and a genuine
policy-consolidation (`resolve_cache_db_path`) rather than a second copy of existing logic.
