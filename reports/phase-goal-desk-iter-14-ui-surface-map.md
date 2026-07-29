# Phase goal-desk-iter-14 — UI Surface Map

**Phase:** goal-desk-iter-14
**Date:** 2026-07-28
**Written by:** ui-impact-analyst

---

## Changed-File Classification

Per `.claude/skills/diff-to-ui-impact.md`'s categories, from the dev handoff's "Files Changed" list
(`git diff --stat` independently re-confirmed against the working tree):

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/research/desk_index_reconcile.py` (new) | backend-internal | none (direct) | `classify_drift` / `run_reconcile` / `ReconcileRunStore` / `DeskIndexReconcileComputeManager` / `resolve_desk_index_reconcile_dir` — no route decorator, not imported by the frontend. Its output reaches a user only through the four routes below. |
| `apps/backend/tests/test_desk_index_reconcile.py` (new, 44 tests) | backend-internal (test) | none | Drift-bucket, repair, run-store discipline, manager mechanics, route, and SSOT-proof tests. No UI surface. |
| `apps/backend/app/research/desk_routes.py` (modified, +137/-20) | backend-api | indirect → confirmed direct | 4 new routes added under the existing `/research/desk` router: `POST`/`GET /research/desk/coverage/reconcile/compute`, `POST .../compute/cancel`, `GET /research/desk/coverage/reconcile/runs`. `apps/frontend/lib/api.ts`'s 4 new functions call these exact paths — confirmed by direct diff inspection, not just grep. |
| `apps/frontend/lib/types.ts` (modified, +80) | frontend-direct | direct | 10 new `DeskReconcile*` interfaces (`DeskReconcileUnindexedSeries`, `DeskReconcileOrphanRow`, `DeskReconcileStaleChecksumRow`, `DeskReconcileDrift`, `DeskReconcileStoreError`, `DeskReconcileRunMeta`, `DeskReconcileRun`, `DeskReconcileRunsListResult`, `DeskReconcileComputeProgress`, `DeskReconcileComputeSnapshot`), consumed directly by the new `/desk` components. |
| `apps/frontend/lib/api.ts` (modified, +95) | frontend-direct | direct | 4 new functions (`triggerDeskReconcileCompute`, `fetchDeskReconcileCompute`, `cancelDeskReconcileCompute`, `fetchDeskReconcileRuns`) — the exact client calls `desk/page.tsx`'s mount effect, poll effect, and two new handlers invoke. |
| `apps/frontend/app/desk/page.tsx` (modified, +394/-20) | frontend-direct | direct | New `ReconcileIndexControl` / `DriftList` / `IndexReconciliationRunRow` / `IndexReconciliationTable` / `LatestReconciliationDetail` / `ReconciliationSection` components; a new top-level `<section aria-label="Index Reconciliation">`; a renamed controls-panel title and `aria-label`; a 5th/6th mount-time GET; a 3rd poll effect; two new handlers. This is the UI surface itself. |
| `runs/goal-session-desk/journey-scripts/J-10.json` (new) | test / golden-replay | none (test infra) | Automated regression script asserting the already-rendered Reconciliation section's static heading and the current honest-empty text. Read-only by design (never clicks "Reconcile Index" or "Run Screen" — see the script's own `notes`). Not shown to a product user. |
| `reports/phase-goal-desk-iter-14-smoke-replay-results.md` (new) | documentation/evidence | none | Regression-replay report for the required-still-passing journey set. Pipeline artifact. |
| `reports/qa/goal-desk-iter-14-evidence/J-01,J-02,J-03,J-04,J-05,J-07,J-08,J-09-verify.png` (8 new) | evidence (screenshot) | none | Screenshots from replaying already-shipped, unchanged journeys on the scoped rig — regression proof, not new UI. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | New section `<section aria-label="Index Reconciliation">` wrapping `Panel title="Index Reconciliation"` | New feature (page-level section) | J-10: gives the operator a durable, independently-checkable view of index-repair history, always present regardless of whether a screen exists | Load `/desk` while a screen is loading, unavailable, not-yet-computed, and populated (four separate states); confirm the "Index Reconciliation" panel renders as the LAST section on the page in all four states, immediately after "Top-up runs". |
| `/desk` | `ReconciliationSection` honest-empty state (`data-testid="desk-reconcile-runs-empty"`) | New empty state | Before any reconciliation has ever completed on a given backend, the panel must say so honestly rather than render blank | Against a backend with zero recorded reconciliation runs, load `/desk`; confirm the panel text reads exactly "No reconciliation run recorded yet." Open the network tab during the load and confirm `GET /research/desk/coverage/reconcile/runs` fires but no `POST .../compute` does — the GET must never trigger a run as a side effect. |
| `/desk` | `IndexReconciliationTable` (`data-testid="desk-reconcile-runs-table"`, rows `data-testid="desk-reconcile-run-row"`) | New table | Lists every historical reconciliation run's summary — the core of the new durable-history capability | After at least 2 reconciliation runs have completed, reload `/desk`; confirm the table shows one row per run with columns date, run id (`desk-reconcile-run-id`), state (`desk-reconcile-run-state`), series on disk (`desk-reconcile-run-series-on-disk`), and rows indexed before → after (`desk-reconcile-run-rows-indexed`, format `"<before> → <after>"`). |
| `/desk` | `LatestReconciliationDetail` (`data-testid="desk-reconcile-run-latest-detail"`) | New detail panel | Only the latest run carries full before/after drift detail, since that is the only record the meta-only `runs` list omits and `latest` alone carries | After the most recent reconciliation completes, reload `/desk`; confirm a "Latest run — `<date>` · `<id>`" block appears below the table showing `state: <state>` (`desk-reconcile-run-latest-state`), "`N` series on disk" (`desk-reconcile-run-latest-series-on-disk`), and "rows indexed: `N` before, `M` after" (`desk-reconcile-run-latest-rows-indexed`). |
| `/desk` | Drift-before / drift-after lists (`data-testid="desk-reconcile-run-latest-drift-before"` / `-drift-after"`, entries `-entry`, empty `-empty`) | New conditional element | Every affected pair must be labeled by which of the three honest drift buckets it came from, never merged into one unlabeled count (TC-1/2/3's distinct semantics) | For a reconciliation run known to have repaired an "unindexed series" pair (e.g. a symbol/timeframe deleted from the index but still on disk), reload `/desk`; confirm "Drift before (`N`)" lists an entry reading "`<SYMBOL>` `<timeframe>` — series on disk, no index row (`<series_id>`)" and "Drift after (`M`)" no longer lists that same pair (or reads "no drift" via `-drift-after-empty` if it was the only affected pair). |
| `/desk` | Store-errors list (`data-testid="desk-reconcile-run-latest-store-errors"`, rows `-store-error-row`, detail `-store-error-detail"`) | New conditional element | A corrupted bar-series file's error must be shown verbatim, never summarized, dropped, or fabricated (TC-5/TC-20) | For a reconciliation run where a corrupted bar-series file was present, reload `/desk`; confirm a "Store errors (`N`)" list appears with one item per corrupted file reading "`<filename>` — `<verbatim error text>`". For a run with no corrupted files, confirm this element is entirely absent (never a "Store errors (0)" line). |
| `/desk` | `ReconcileIndexControl` idle/running state (`data-testid="desk-reconcile-button"`, running block `desk-reconcile-compute-running"`, progress `desk-reconcile-compute-progress"`) | New control | J-10's primary trigger — an explicit operator act, mirroring Top-up's button exactly (anti-goal: no auto/scheduled trigger) | Click "Reconcile Index" (`desk-reconcile-button`); confirm the button becomes disabled, its label changes to "Reconciling…", and a progress line appears showing one of "classifying" / "reindexing" / "verifying" beside a pulsing dot; confirm the button returns to enabled "Reconcile Index" once the run reaches a terminal state. |
| `/desk` | `ReconcileIndexControl` cancel sub-control (`data-testid="desk-reconcile-compute-cancel"`, cancelled note `desk-reconcile-compute-cancelled"`) | New control | Lets the operator abort an in-flight reconciliation, mirroring Top-up's cancel including its 409-when-idle behavior | While a reconciliation is "Reconciling…", click "Cancel" (`desk-reconcile-compute-cancel`); confirm the button reads "Cancelling…", then an amber note appears reading "Index reconciliation cancelled — the index was not repaired this run." Separately, with no reconciliation running, call `POST /research/desk/coverage/reconcile/compute/cancel` directly (e.g. via curl) and confirm it returns HTTP 409, never a silent no-op. |
| `/desk` | `ReconcileIndexControl` failed state (`data-testid="desk-reconcile-compute-error"`, trigger-error `desk-reconcile-compute-trigger-error"`) | New conditional element | A failed reconciliation must be visibly retryable, not a silent dead end | Force a reconciliation to fail (e.g. an induced I/O error in a fixture-scoped test rig); reload or observe `/desk` live; confirm the button label changes to "Retry Reconcile Index" and the failure's error text renders above it in red. |
| `/desk` | Controls panel title + `aria-label` (`Panel title="Run Screen / Top-up / Reconcile Index"`, `<section aria-label="Run Screen, Top-up and Reconcile Index controls">`) | Updated layout | The shared trigger panel gained a third control and is renamed to name it, mirroring goal.md's "wired exactly like the existing Top-up button" instruction | On a populated `/desk` screen, confirm the controls panel's visible title reads "Run Screen / Top-up / Reconcile Index" (previously "Run Screen / Top-up") and contains three buttons side by side: "Run Screen", "Top-up", "Reconcile Index". |
| `/desk` | Pre-screen empty state (`DeskNotComputedPanel`) | Updated layout | The Reconcile control is available even before any screen has ever been computed, matching Top-up's own pre-screen availability | On a fresh backend where no screen has ever been computed, load `/desk`; confirm "Reconcile Index" renders beside "Run Screen" and "Top-up" in the "not computed yet" panel, not only in the post-screen controls panel. |
| `/desk` | Coverage badges (`DeskCoverageBadges`, `data-testid="desk-coverage-badge"` — component code itself unchanged this iteration) | Changed behavior (data source only) | A dark ("no bars") badge caused by index drift can now be corrected instead of staying wrong indefinitely — this is the iteration's stated product goal | With a ranked row's badge showing `data-timeframe="<tf>" data-has-bars="false"` for a symbol that genuinely has that timeframe's bar file on disk (a planted or real drift case), click "Reconcile Index", wait for it to finish, then trigger a NEW "Run Screen"; confirm the SAME badge on the new screen now renders `data-has-bars="true"` (lit, emerald styling) — and confirm the PRIOR screen's own recorded snapshot is untouched (still shows the old dark badge if re-viewed via Screen History). |
| `GET /research/desk/coverage/reconcile/runs` (backend endpoint consumed by `/desk`) | New route in `desk_routes.py` | New backend-api endpoint | The single data source backing the entire Index Reconciliation panel; must be honest-empty and never a 404 | With curl or the browser network tab, call `GET /research/desk/coverage/reconcile/runs` against a store with zero runs; confirm HTTP 200 with body exactly `{"runs": [], "latest": null}`. After a run completes, call it again and confirm `latest` carries `drift_before`/`drift_after`/`store_errors` while every entry in the `runs` array omits all three (meta-only). |
| `POST`/`GET /research/desk/coverage/reconcile/compute`, `POST .../compute/cancel` (backend endpoints consumed by `/desk`) | New routes in `desk_routes.py` | New backend-api endpoints | The trigger/poll/cancel trio the button, progress line, and cancel control above all read and write | Call `GET .../compute` with no job ever run; confirm it returns `null` and starts nothing. While a reconciliation triggered via the "Reconcile Index" button is still running (the UI button itself is disabled during a run, so issue this call directly, e.g. via curl or the network tab), call `POST .../compute` a second time; confirm it returns `started: false` with the SAME job id and unchanged snapshot, never a second concurrent job. Call `POST .../compute/cancel` while idle/no job has ever run; confirm HTTP 409, never a silent 200. |

<!-- Change Type options used above: New feature | New empty state | New table | New detail panel |
     New conditional element | New control | Changed behavior | Updated layout | New backend-api endpoint -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/desk_index_reconcile.py` — the classify/repair/record mechanics
  themselves: `classify_drift`'s three-bucket comparison logic, `run_reconcile`'s
  classify→repair→re-classify walk, `ReconcileRunStore`'s checksum-verified append-only file
  discipline, and `DeskIndexReconcileComputeManager`'s lock/worker-thread/cancel-event internals —
  no UI surface of their own; every observable effect reaches a user only through the routes and
  `/desk` components captured in the table above.
- `apps/backend/tests/test_desk_index_reconcile.py` (44 tests) — test coverage only, no UI surface.
- `runs/goal-session-desk/journey-scripts/J-10.json` — a golden regression-replay script, not a
  product surface; deliberately read-only per this iteration's own "a golden script can be a write
  path" lesson.
- The compute manager's `progress.phase` enum values (`"classifying" | "reindexing" | "verifying"`)
  are backend-internal state; only the CURRENT phase string is surfaced to the user (via
  `desk-reconcile-compute-progress`), never the full enum or any phase-transition history.

**Note on unchanged files that still gain the new capability's data path:** `app/mcp/__init__.py`
shows zero diff this iteration (confirmed via the dev handoff and `test_mcp_server.py`'s unmodified
17-tool contract still passing) — the new `GET /research/desk/coverage/reconcile/runs` route is
already reachable through the existing `ALLOWED_GET_PREFIXES` (`/research/`) allowlist, so the MCP
`get_endpoint` tool can proxy it with no code change, even though MCP itself is not a rendered UI
surface.

---

## Summary

- **Frontend surfaces changed:** 1 (route: `/desk`)
- **New pages/routes:** 0 new frontend pages/routes (4 new backend endpoints under
  `/research/desk/coverage/reconcile/*`, all consumed by the existing `/desk` page)
- **Modified components:** 6 new components (`ReconcileIndexControl`, `DriftList`,
  `IndexReconciliationRunRow`, `IndexReconciliationTable`, `LatestReconciliationDetail`,
  `ReconciliationSection`) + 2 existing components extended with a new prop/rendered control
  (`DeskNotComputedPanel`, `DeskPopulatedScreen`) + 1 renamed Panel title/section `aria-label` + 3
  effect-hook changes (mount GET batch extended to six, one new poll effect, two new handlers) — all
  within the existing `apps/frontend/app/desk/page.tsx`
- **Navigation changes:** no
- **Backend-only changes:** 2 (the new reconcile domain module's internal classify/repair/store/
  manager mechanics, and its dedicated test file)
