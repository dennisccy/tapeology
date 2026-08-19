# Phase goal-rapid-microscope-iter-13 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-13
**Date:** 2026-08-19
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

**None.** This iteration's diff (`apps/backend/app/research/vault.py`,
`apps/backend/app/research/micro_routes.py`, plus two test files) touches zero files under
`apps/frontend/`, and the one function it substantively rewrites (`recover_shard_ledger`) has zero
production call sites — no route, CLI command, or button invokes it. There is no row to put in this
table under the template's literal meaning of "changed."

---

## Regression-Risk Surfaces (Unchanged — Verify Sameness)

`Frontend Present: yes` is declared purely to run the mechanical browser-QA sentinel this
iteration (per `runs/goal-rapid-microscope-iter-13/plan.md`'s TC-11 and the phase spec's J-10
target). The surfaces below did not change, but each transitively reads code this iteration
touched (the Microscope Readiness section's `sealed_tranche`-adjacent aggregate routes through
`vault.py`) or shares the same store the changed module reads from. Listed here, distinctly from
"Affected," so the combined-mode test plan has concrete regression targets instead of new-feature
targets that do not exist.

| Route / Page | Component / Element | Change Type | Why Included | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `PriceChart` + `TopBar` (Cockpit live tape/chart) | Unchanged — regression sentinel | J-10 kept-product sentinel; shares the backend process that `vault.py` (now modified) also runs inside | Navigate to `http://localhost:3301/`, type `AAPL` into the ticker input, click "Watch", and confirm a price chart renders below the top bar with no error banner within 10 seconds |
| `/structure` | `data-testid="structure-title"` heading + "Tradable Map" panel | Unchanged — regression sentinel | J-10 kept-product sentinel; TC-11 explicitly names "Tradable Map" load | Navigate to `http://localhost:3301/structure` and confirm the heading with `data-testid="structure-title"` and the "Tradable Map" panel both render with band/zone data, no unavailable-panel state |
| `/structure` | `data-testid="comparison-dataset-select"` dropdown (Comparison panel) | Unchanged — regression sentinel | Explicitly named in the carried pump context as a kept regression target | On `/structure`, open the "Comparison" panel further down the page, click the `data-testid="comparison-dataset-select"` dropdown, and confirm it lists registered datasets (18 expected) rather than showing the `data-testid="comparison-no-datasets"` empty state |
| `/desk` | "Microscope Readiness" section → `data-testid="micro-readiness-totals-table"` (Corpus Totals) | Unchanged — regression sentinel | J-01 re-check named explicitly in the plan (its `sealed_tranche` aggregate transitively reads `vault.py`) | On `/desk`, scroll to the last section, click its "Microscope Readiness" header to expand it (starts collapsed every reload), and confirm the "Corpus Totals" table renders its five rows with no `data-testid="micro-readiness-unavailable"` panel |
| `/desk` | "Microscope Readiness" section → `data-testid="micro-readiness-shards-table"` / `data-testid="micro-readiness-shards-empty"` (Legacy Tick Shards) | Unchanged — regression sentinel | Closest UI-observable surface to this iteration's subject matter (shard/exposure state); proven independently that its "Exposure state" column is a hardcoded constant unaffected by `vault.py` | With Microscope Readiness expanded, scroll to "Legacy Tick Shards" and confirm the empty state `data-testid="micro-readiness-shards-empty"` with text "No tick shards recorded." appears — the real store has zero recorded shards, so this is the expected, unchanged appearance |
| `/desk` | "Referee Registry" / "Referee Adjudications" / "Referee Runs" sections | Unchanged — regression sentinel | TC-11 names all three Referee sections in the kept-product sentinel list | On `/desk`, click each of the three section headers to expand them in turn and confirm each renders its existing content (registered hypotheses table / adjudication fold / run controls) with no console error |
| `/desk` | "Playbook Signals" / "Backscan" / "Playbook Evidence" sections | Unchanged — regression sentinel | TC-11 names the Playbook/Band Context/Cohorts sections in the kept-product sentinel list | On `/desk`, confirm "Playbook Signals" and "Backscan" render immediately (always-on, no click needed), then click "Playbook Evidence" to expand it and confirm its read-only fold renders |
| `/`, `/structure`, `/desk` | top-level navigation | Unchanged — regression sentinel | Basic reachability check; nothing added or removed from the route set | From `/`, navigate directly to `http://localhost:3301/structure`, then to `http://localhost:3301/desk`; confirm each loads without a blank page or 404 |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/vault.py` — `recover_shard_ledger`'s recovery logic rewritten
  halt-only (a reconstruction must hash-match the tail anchor byte-for-byte or the vault refuses to
  resume at all; the previous graded/union-marking middle path and the `exposure_unknown` shard
  state it produced are deleted) — no UI surface affected. Zero production call sites; not reachable
  from any route, CLI, or button. Two further self-attack fixes (empty-reconstruction and
  wrong-`verify_result` laundering) closed in the same file, same reasoning.
- `apps/backend/app/research/vault.py` — `seal_shard`/`assign_shard`/`expose_shard` docstring-only
  clarification that their corruption gating is scoped to their own shard ledger by design — no UI
  surface affected. Zero behavior change, zero production call sites.
- `apps/backend/app/research/micro_routes.py` — `get_tick_recorder_compute` docstring fix
  correcting stale field names in prose — no UI surface affected. The route's actual served JSON
  (`_progress_view`) is byte-unchanged; only the docstring was wrong before this fix.
- `apps/backend/tests/test_vault.py`, `apps/backend/tests/test_tick_recorder.py` — test-only
  changes (revised assertions, 9 new tests including the TR-29 six-trap table) — no UI surface
  affected; test files ship no product code.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 4 (recovery logic rewrite, deleted `exposure_unknown` state, seal/assign/expose docstring pin, micro_routes.py docstring fix — plus test-only files not counted as product changes)
- **Regression-risk surfaces listed for the combined-mode test plan:** 8 (none changed; all are kept-product sentinel targets per plan.md TC-11 and J-01)
