# Phase goal-rapid-microscope-iter-2 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-2
**Date:** 2026-08-17
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

Exactly one surface has an actual (non-code) change this iteration. Its own component code is
byte-unchanged — the change is entirely in what data the isolated verification harness feeds it.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Microscope Readiness panel (`MicroReadinessSection`, expand control `data-testid="desk-section-expand-microReadiness"`) | Changed behavior (QA-harness test data only — zero `.tsx` diff) | `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` now stages 2 real tick-dataset fixtures (`6c9bf2c700d749e0993efd92c5807de3.json`, `d9f9dbe04fb24a7caccc53f0c6805412.json`, both symbol PG, session date 2026-06-09, feed sip) into the store-scoped rig's dataset folder before backend start, where before that folder was empty | Navigate to `http://localhost:3301/desk`, click the "Microscope Readiness" section header, and verify the "Legacy Tick Shards" table (`data-testid="micro-readiness-shards-table"`) shows exactly 2 rows (both symbol "PG", feed "sip") instead of the prior "No tick shards recorded." empty state, and that `micro-readiness-distinct-symbol-days` reads `1` and `micro-readiness-distinct-datasets` reads `2` |

---

## Required Regression Sentinel (J-10, widened this iteration — zero code change to any of these surfaces)

Iteration 1 returned `ESCALATE`, which this project's rules make mandatory for widening the
regression set to the full kept-product sentinel this iteration (cockpit `/`, `/structure`, every
shipped `/desk` section). None of the files below changed — these rows exist so the required
regression sweep has concrete, checkable targets, not because any code moved.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | Cockpit — `TopBar` ticker input + Watch button + live chart | Regression check (no code change) | Mandatory widened sentinel (prior-iteration `ESCALATE` rule) | Navigate to `http://localhost:3301/`, type `SIM-BUYER` into the field labeled "Ticker", click the "Watch" button, and verify the live cockpit price chart begins rendering with no red error banner |
| `/structure` | `structure-title`, `structure-as-of-today-button`, `structure-load-button`, "Tradable Map" panel | Regression check (no code change) | Mandatory widened sentinel | Navigate to `http://localhost:3301/structure`, type `PG` into the Symbol field, click "Today", click "Load", and verify the "Tradable Map" panel renders bands/levels for PG with no error message |
| `/desk` | "Playbook Signals" section — band filter (`data-testid="desk-playbook-band-filter"`) and inside/cohort filter (`data-testid="desk-playbook-inside-filter"`) — this is the surface TC-18 names "Band Context" / "Cohorts" | Regression check (no code change) | Mandatory widened sentinel | On `http://localhost:3301/desk`, change the "show" dropdown to "at a wall behind" and the "and" dropdown to "inside a band", and verify the count text (`data-testid="desk-playbook-band-filter-count"`) updates to a "showing N of M recorded signals..." string with N ≤ M |
| `/desk` | Playbook Evidence panel (`data-testid="desk-section-expand-playbookEvidence"`) | Regression check (no code change) | Mandatory widened sentinel | Click the "Playbook Evidence" section header and verify the panel expands with its existing read-only content (table or its own empty-state), no error boundary |
| `/desk` | Referee Registry panel (`data-testid="desk-section-expand-refereeRegistry"` → body `referee-registry-section`) | Regression check (no code change) | Mandatory widened sentinel | Click the "Referee Registry" section header and verify the registry table renders with no error |
| `/desk` | Referee Adjudications panel (`data-testid="desk-section-expand-refereeAdjudications"` → body `referee-adjudications-section`) | Regression check (no code change) | Mandatory widened sentinel | Click the "Referee Adjudications" section header and verify the panel renders with no error |
| `/desk` | Referee Runs panel (`data-testid="desk-section-expand-refereeRuns"` → body `referee-runs-section`) | Regression check (no code change) | Mandatory widened sentinel | Click the "Referee Runs" section header and verify the panel renders with no error |

<!-- Change Type key used above: New page | New component | Updated layout | Added navigation |
     Changed behavior | Removed element | New form | New table | New modal | Regression check -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/datasets.py` — additive `observer: object | None = None` kwarg on
  `DatasetStore.replay` (default `None`, byte-identical to every existing call site) — backend-internal,
  no UI surface.
- `apps/backend/app/research/micro_observer.py` (new) — the streaming, trade-by-trade order-flow
  observer — backend-internal, no UI surface; nothing renders its output.
- `apps/backend/app/research/micro_features.py` (new) — the order-flow arithmetic (cumulative
  delta, imbalance, run length, volume burst, divergence-at-level, impact efficiency,
  failed-aggression score, response asymmetry, spread change, quote imbalance, microprice, quote
  depletion, refill-consistency) plus the cross-basis unit refusal gate — backend-internal, no UI
  surface.
- `apps/backend/app/research/micro_snapshots.py` (new) — snapshot identity/verification,
  single-flight build manager, CLI, granularity benchmark routine — backend-internal for the
  storage/compute logic; its 3 REST routes are backend-api (see below).
- `apps/backend/app/research/micro_routes.py` (modified — adds `GET /research/desk/micro/snapshots`,
  `POST`/`GET`/`POST .../cancel` on `/snapshots/compute`, `GET /snapshots/runs`) — **backend-api,
  not yet consumed**: a repo-wide search of every frontend `.tsx`/`.ts` file for these endpoint
  paths found zero references. Not visible in the UI until a future iteration (J-08) adds a
  control that calls them.
- `apps/backend/scripts/micro_snapshot_granularity_benchmark.py` (new) — one-time CLI benchmark
  script, operator/CLI-only — no UI surface.
- `apps/backend/tests/test_micro_observer.py`, `test_micro_features.py`, `test_micro_snapshots.py`
  (new) — test modules — no UI surface.
- `apps/backend/tests/test_desk_ui_guards.py` (modified) — moved 5 misplaced counter-test
  assertions back to the function whose docstring already claimed them; zero assertion coverage
  lost, zero behavior change — no UI surface.
- `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` (modified) — stages 2 tick
  fixtures into the QA rig's own throwaway dataset directory — test-infrastructure only; its one
  downstream UI-visible consequence is the Microscope Readiness panel row in "Affected UI
  Surfaces" above.

---

## Summary

- **Frontend surfaces changed:** 0 (zero `.tsx` files touched this iteration — confirmed via
  `git diff --stat HEAD -- apps/frontend`)
- **New pages/routes:** 0 frontend routes. 3 new backend API routes shipped (snapshots
  list/compute/runs), none yet wired to any page — see Backend-Only Changes.
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 11 files (5 product modules, 3 new test modules, 1 test-hygiene edit,
  1 new CLI script, 1 QA-harness fixture-seeding script)
