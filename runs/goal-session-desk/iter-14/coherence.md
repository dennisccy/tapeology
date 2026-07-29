# Iteration 14 — Coherence Audit

**Iteration:** goal-desk-iter-14
**Date:** 2026-07-29
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

This iteration (J-10) implements the two Data Contract rows that were pre-registered in
`blueprint.md`'s "RESOLVED at iter-14" trailer note *before* the build, per this session's own
convention. Both are new values (coverage-index reconciliation records), not re-derivations of any
existing registered value.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Coverage-index reconciliation run records (durable ledger) | OK | Owner `apps/backend/app/research/desk_index_reconcile.py` (`ReconcileRunStore`, `record_reconcile_run`, :260-401); served by new `GET /research/desk/coverage/reconcile/runs` (`apps/backend/app/research/desk_routes.py:195-209`). Shape matches blueprint row byte-for-byte (meta-only `runs`, full `latest` with `drift_before`/`drift_after`/`store_errors`). Frontend reads it verbatim via `fetchDeskReconcileRuns` (`apps/frontend/lib/api.ts:699-720`) into `ReconciliationSection`/`IndexReconciliationTable`/`LatestReconciliationDetail` (`apps/frontend/app/desk/page.tsx`) — no client-side recomputation, only formatting (`meta.started_utc.slice(0,10)`, the `before → after` string). |
| Coverage-index reconciliation compute progress (transient) | OK | Same new module's `DeskIndexReconcileComputeManager` (`desk_index_reconcile.py:414-533`); served by `POST`/`GET /research/desk/coverage/reconcile/compute`, `POST .../compute/cancel` (`desk_routes.py:141-182`). GET never triggers a compute (`get_desk_index_reconcile_compute` at `desk_routes.py:159-166` only calls `manager.snapshot()`); frontend poll effect (`page.tsx`, `reconcileCompute` effect) only GETs while `state === "running"`. |
| Bar coverage index (internal) / coverage freshness | OK — zero diff, single owner unchanged | `desk_coverage.py`, `bar_index.py`, `bars.py` all show **zero diff** this iteration (`git diff <snapshot> --stat` confirms). `classify_drift` (`desk_index_reconcile.py:109-147`) is a pure composition of `BarStore.list(include_bars=False)` and `BarIndex.list()`'s already-public reads — it does not recompute coverage/freshness, only classifies drift between the store and the derived index. The repair path is exclusively the existing `BarIndex.reindex(store)` (`bar_index.py:198`, called once at `desk_index_reconcile.py:188`) — no second index-building path. |
| Bands / tradable-map, Levels/zones, PnL ledger, Strategy registry, Setups, Edge report, Route list (`UI_ROUTES`) | OK — zero diff, untouched | Confirmed via `git diff <snapshot> --stat` on `tradability.py`, `levels.py`, `apps/frontend/components/StructureChart.tsx`, `apps/backend/app/meta.py` (no hits — all zero diff). `apps/backend/app/meta.py:31-35`'s `UI_ROUTES` still lists exactly 3 rows (`/`, `/structure`, `/desk`); no nav-skeleton change, matching the spec's own claim of "no nav-skeleton change." |
| `config_fingerprint` / MCP tool count | OK — zero diff | `apps/backend/app/config.py` and `apps/backend/app/mcp/__init__.py` both show zero diff. Storage dir for the new store is a bare env-var-or-sibling default (`resolve_desk_index_reconcile_dir`, `desk_index_reconcile.py:217-226`), not a new `Config` field — matches the blueprint's "deliberately NOT a new `Config` field" note. No MCP tool added; the new GET route is reachable through `get_endpoint`'s existing `/research/` allowlist. |

No duplicate computation and no non-canonical source found. No new unregistered value — both rows
were registered in the blueprint before this iteration's code landed.

## Information Architecture check

No new page or route this iteration — the spec explicitly scopes this as one new read-only section
plus one new trigger button added to the already-registered `/desk` canonical home.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Index Reconciliation section (`/desk`) | OK | `apps/backend/app/meta.py:31-35` (`UI_ROUTES`, unchanged, 3 rows) — the section is placed inside the existing `/desk` page (`apps/frontend/app/desk/page.tsx`, new `<section aria-label="Index Reconciliation">` at the end of the page body, mirroring the `TopupRunsSection` placement precedent), not a new route. `/desk` remains 1 click from the persistent top nav (`NavBar.tsx`, which reads `GET /meta/ui-routes` — unmodified this iteration). |
| "Reconcile Index" trigger control | OK | Added to the two ALREADY-existing controls panels in `page.tsx` (`DeskNotComputedPanel`, `DeskPopulatedScreen`'s "Run Screen / Top-up / Reconcile Index" panel) beside `ScreenComputeControl`/`TopupComputeControl` — no parallel shell, no new panel/page. |

No duplicate home, no hidden feature, no parallel shell.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None beyond what the spec itself already discloses (e.g., the real ~88-pair ambient-store
  reconciliation is explicitly deferred to an operator-later act, not a coherence concern — this is
  a scope decision logged in `assumptions.md` iter-14, not a Data Contract or IA issue).
- The new section's copy ("No reconciliation run recorded yet.", "series on disk, no index row",
  "index row, no file on disk", "index row, file on disk fails its checksum", "Index reconciliation
  cancelled — the index was not repaired this run.") is descriptive-measurement-only, consistent
  with the established Top-up/Screen sections' tone — no drift in labeling style observed.
