# Iteration 16 — Coherence Audit

**Iteration:** goal-desk-iter-16
**Date:** 2026-07-29
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Screen snapshots, rank rows, skip rows (`desk_screen.py` / `GET /research/desk/screen`) | OK | `apps/backend/app/research/desk_routes.py:326-353` — new `?id=` branch filters the SAME `store.list()` records already loaded by the existing route (`found = next((r for r in records if r["id"] == id), None)`); no new store, no new module, no new endpoint. `id`+`date` together → 422 refusal (`desk_routes.py:333-336`). Frontend reads it via `fetchDeskScreenById` → `GET /research/desk/screen?id=` (`apps/frontend/lib/api.ts:981-1006`), the canonical endpoint with a different query param — not a second endpoint. `DeskProvenance` (`apps/frontend/app/desk/page.tsx:349-350`) renders `snapshot.id`/`snapshot.created_utc`, fields already carried on the canonical `DeskScreenSnapshot` payload — a re-format, not a re-fetch. Matches blueprint's iter-16 addition note verbatim (`runs/goal-session-desk/state/blueprint.md:152,391-405`). |
| Top-up run records (`desk_topup_log.py` / `GET /research/desk/topup/runs`) | OK | `apps/backend/app/research/desk_routes.py:281-289` — `integrity_errors: errors` now returned from the SAME `store.list()` tuple the route already unpacked and previously discarded (`_errors` → `errors`); zero new store read. Frontend: `TopupRunsSection` renders `result.data.integrity_errors` from its existing `fetchDeskTopupRuns` result (`apps/frontend/app/desk/page.tsx:744-747`) — no new fetch. Matches blueprint row 155's iter-16 note. |
| Coverage-index reconciliation run records (`desk_index_reconcile.py` / `GET /research/desk/coverage/reconcile/runs`) | OK | `apps/backend/app/research/desk_routes.py:527-540` — identical pattern (`_errors` → `errors`, `"integrity_errors": errors`). Frontend: `ReconciliationSection` renders `result.data.integrity_errors` from its existing `fetchDeskReconcileRuns` result (`apps/frontend/app/desk/page.tsx:927-930`). Matches blueprint row 156's iter-16 note. |
| MCP tool surface (17 tools) | OK | `apps/backend/tests/test_mcp_server.py:419-465` — new test reaches `?id=` purely through `get_endpoint`'s existing `/research/` allowlist; no `_STATIC_PATHS` addition; `test_get_endpoint_desk_topup_runs_byte_identical_with_no_new_tool` still asserts `len(TOOL_NAMES) == 17` (`:970`). No new MCP tool introduced. |
| Frozen modules (`tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `StructureChart.tsx`, `desk_coverage.py`) | OK | Not present anywhere in the diff stat (`git diff 19a5f0eb... --stat`, 8 files changed: `desk_routes.py`, 4 test files, `page.tsx`, `api.ts`, `types.ts`) — zero diff, as required. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/desk` (all changes: Screen History id-select/highlight + "recorded" column, Provenance `id`/`created_utc` rows, three `IntegrityErrorsNote` additions) | OK | No new route, no new nav entry. `app/meta.py` `UI_ROUTES` untouched (not in diff); all changes are inline additions to sections already registered under the Desk canonical home (blueprint IA lines 60-98, feature/journey homes table row for J-12, line 116). Confirmed via `reports/phase-goal-desk-iter-16-ui-surface-map.md`: "Navigation changes: no", "New pages/routes: 0". |
| Universe ledger `integrity_errors` line (named in the phase spec's IN SCOPE bullet, `docs/phases/goal-desk-iter-16.md:90-92`, as a 4th ledger section) | OK (not a violation) | Not built — but not a coherence violation: the blueprint's IA never registers a Universe *ledger section* as a canonical home in the first place, only "surfaced as the provenance line + universe metadata on `/desk` — no standalone page" (blueprint row 105, `Universe snapshots + membership` row 149). `GET /research/desk/universe` has served `integrity_errors` since J-01, unrelated to this iteration. No duplicate path was created and no existing path was broken; this is a spec-vs-blueprint premise mismatch the dev/audit handoffs both independently caught and honestly documented (`docs/handoffs/goal-desk-iter-16-dev.md:155-183`, audit finding F1 in `docs/handoffs/goal-desk-iter-16-audit.md:57-69,240-248`). See advisory note below. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Phase-spec/plan premise error, already self-corrected.** `docs/phases/goal-desk-iter-16.md`'s IN SCOPE frontend bullet asks for a 4th "Universe" ledger `integrity_errors` line, but no Universe snapshot list/ledger section exists anywhere in the frontend (only a `universe_snapshot_id` string inside Provenance) — confirmed by `grep -rln "universe" apps/frontend/app apps/frontend/lib apps/frontend/components` per the dev handoff. The dev correctly declined to invent a brand-new Universe ledger section to satisfy a spec line that cites nonexistent types (`DeskUniverseResult` at `lib/types.ts:363/516` — those line numbers actually belong to unrelated `MergedCandlesPage`/`DatasetsListResult` fields). No `goal.md` TESTING REQUIREMENT (TC-1..TC-16) exercises a Universe integrity line either. This is correctly scoped as a documentation/decomposer-input defect, not a build defect — future specs should stop citing that premise, and if a Universe ledger section is wanted on `/desk` it should be proposed as its own journey with its own canonical-home registration.
- **Screen History integrity-error line becomes invisible in one navigation state (audit F2).** Per `docs/handoffs/goal-desk-iter-16-audit.md:73-77`, when the honest "Desk screen not computed yet." empty-state panel is showing, the Screen History section (and its `IntegrityErrorsNote`) is not rendered, so a screen-ledger integrity error would be temporarily invisible in that state. This is a visibility/completeness gap on an already-correctly-sourced value (still reading the one canonical endpoint, not a second source) — not a Data Contract or IA rule violation, so it does not FAIL here, but the decomposer should consider it for a future iteration.
- **Two `IntegrityErrorsNote` call sites read `integrity_errors` without a defensive default** (audit finding F3, `page.tsx:745,928`) — a latent fragility note (JS `undefined.length` would throw against a hypothetically malformed response), not a coherence issue since the canonical endpoint's contract already guarantees an array; noted for completeness only.
