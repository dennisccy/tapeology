# goal-rapid-microscope-iter-11 — UI Surface Map

**Phase:** goal-rapid-microscope-iter-11
**Date:** 2026-08-19
**Written by:** ui-impact-analyst

---

## File Classification

All 9 changed files (confirmed via `git status`/`git diff --stat HEAD`) are backend Python; zero
`.tsx`/`.ts` files changed.

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/backend/app/research/vault.py` | backend-internal | none | New predicate (`unresolved_pool_universe_by_dataset_id`) + resolver (`universe_ledger_for_dataset_dir`) functions. Not a route handler; reachable only through other backend modules that call it. |
| `apps/backend/app/research/micro_snapshots.py` | backend-internal | none | `withheld_dataset_ids_for_store`/`exclude_withheld` choke-point routing. Not itself a route; consumed by 8 other backend modules. |
| `apps/backend/app/research/micro_readiness.py` | backend-api | indirect | Feeds `GET /research/desk/micro/readiness`, consumed by `/desk`'s "Microscope Readiness" section. Response shape unchanged (`shard_count`/`symbol_days`/`by_universe`/`shards` field names and per-row shape identical) — only which datasets populate `shards` can broaden. |
| `apps/backend/app/research/tick_recorder.py` | backend-api | indirect → not visible yet | Feeds `GET /research/desk/micro/recorder/compute`'s `progress` body. Response SHAPE changed (raw per-chunk `outcomes` removed; 10 aggregate fields added/kept), but a repo-wide search of `apps/frontend` finds zero references to this endpoint or its field names. |
| `apps/backend/app/research/micro_routes.py` | backend-api | indirect → not visible yet | Docstring-only update on the same route as above; no logic change (`snap["progress"]` was already forwarded verbatim). |
| `apps/backend/app/research/routes.py` | backend-api | indirect | `get_withheld_dataset_ids` (the dependency behind `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`) now delegates to the broadened predicate instead of calling `vault.withheld_dataset_ids` directly. `GET /research/datasets` is consumed by `/structure`'s "Comparison" panel dataset dropdown. This was a gap the plan's own file list missed — found and fixed by the developer during TDD (see dev handoff §"Beyond the plan"). |
| `apps/backend/tests/test_vault.py` | backend-internal (test) | none | Test-only; TC-8/TC-9 inference-trap rewrite. |
| `apps/backend/tests/test_micro_readiness.py` | backend-internal (test) | none | Test-only; TC-1/TC-3/TC-4/TC-10. |
| `apps/backend/tests/test_tick_recorder.py` | backend-internal (test) | none | Test-only; TC-6/TC-7. |

---

## Affected UI Surfaces

<!-- "What to Test" is a specific action verifiable by navigating/clicking, not "verify it works". -->

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | Microscope Readiness — "Legacy Tick Shards" table (`data-testid="micro-readiness-shards-table"` / `-shard-rows`) | Changed behavior (currently inert) | `micro_readiness.build_readiness`'s per-shard withhold check switched from "explicitly ledger-sealed only" to also excluding any dataset that is part of a registered-but-unresolved vault universe's pool | Navigate to `http://localhost:3301/desk`, scroll to the "Microscope Readiness" panel, and compare the "Legacy Tick Shards" table's rows against the pre-iteration baseline — confirm the same symbol / session-date / checksum values appear, in the same order, since the real store has zero registered vault universes and nothing should be newly hidden or newly shown |
| `/structure` | Comparison panel — "Dataset" dropdown (`data-testid="comparison-dataset-select"`) | Changed behavior (currently inert) | `routes.py`'s `get_withheld_dataset_ids` (behind `GET /research/datasets`) now delegates through the same broadened predicate instead of calling `vault.withheld_dataset_ids` directly | Navigate to `http://localhost:3301/structure`, scroll to the "Comparison" panel, click the "Dataset" dropdown, and count the `<option>` entries — confirm exactly 18 datasets are listed (the count the developer verified live immediately before handoff), each formatted `SYMBOL · split · 8-char-id`, with none missing |
| `/structure` | "Edge Report" panel | Changed behavior (currently inert) | `edge_report.py` is one of `micro_snapshots.exclude_withheld`'s 8 downstream consumers — the dataset corpus it computes the v1/structure_tape/structure_tape_map comparison over now runs through the broadened withhold filter | Navigate to `http://localhost:3301/structure`, scroll to the "Edge Report" panel, and confirm the rendered table (or "not computed yet" panel, whichever the current cache state shows) has the identical per-cell n / R / $ values as the pre-iteration baseline — the dataset corpus feeding it is unchanged |
| `/structure` | "Case Studies" panel (setups) | Changed behavior (currently inert) | `setups.py` is one of the 8 downstream consumers of the same choke point | Navigate to `http://localhost:3301/structure`, scroll to "Case Studies", leave the symbol/reaction filters at their defaults, and confirm the event table's row count matches the pre-iteration baseline exactly |
| `/desk` | Screen-related panels — "Run Screen / Top-up / Reconcile Index / Deep Backfill controls", "Screen history", "Screen Runs", "Screen Comparison" | Changed behavior (currently inert) | `desk_screen.py` is one of the 8 downstream consumers of the same choke point | Navigate to `http://localhost:3301/desk`, scroll to "Screen history" and "Screen Runs", and confirm the listed screen runs and their result/member counts are unchanged from the pre-iteration baseline |
| `/` (Cockpit) | Live tape panel + price chart | Regression check (no code touched) | Not touched by this iteration's diff; included because `plan.md` names J-01/J-02 "required-still-passing" and `Frontend Present: yes` runs the full browser regression lane regardless | Navigate to `http://localhost:3301/`, confirm the price chart renders candles (not a blank canvas) and the live tape panel shows an actively updating feed (a new tick/row appears within ~10 seconds, or the feed indicator shows connected — no error banner) |
| `/structure` | Tradable Map panel + "Price chart — S/R levels" + "Confluence zones" | Regression check (no code touched) | Not touched by this iteration's diff; included because `plan.md` names J-03/J-04/J-05 "required-still-passing" | Navigate to `http://localhost:3301/structure`, confirm the "Tradable Map" panel loads a symbol's chart with S/R band overlays rendered (not an "Unavailable" panel), and "Confluence zones" lists the same zone count as the pre-iteration baseline |
| `/desk` | Remaining shipped sections — "Forward Returns", "Briefing", "Skipped members", "Top-up runs", "Index Reconciliation", "Provenance", "Playbook Signals", "Backscan", "Playbook Evidence", "Referee Registry", "Referee Adjudications", "Referee Runs" | Regression check (no code touched) — J-10 whole-product sentinel | Not touched by this iteration's diff; `plan.md` explicitly calls for "J-10 evidence = `J-10.json`'s full kept-product sentinel walk" | Navigate to `http://localhost:3301/desk` and scroll top to bottom — confirm every section listed renders its own data-or-empty-state panel (no section shows a blank area, a stuck "Loading…" spinner, or an "Unavailable" panel with a network-error message) |
| `/`, `/structure`, `/desk` | Top navigation bar (`data-testid="app-nav"`) | Regression check (no code touched) | Not touched; confirms no accidental navigation regression from this iteration's route-file edits (`micro_routes.py`, `routes.py`) | On any page, confirm the nav bar shows exactly 3 links (`data-testid="nav-link"`) — Cockpit, Structure, Desk — and clicking each one navigates to `/`, `/structure`, `/desk` respectively, with the clicked link highlighted as the active one |

<!-- Change Type key used above: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal | Regression check -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/tick_recorder.py` + `apps/backend/app/research/micro_routes.py` —
  `GET /research/desk/micro/recorder/compute`'s `progress` body switched from a raw per-chunk
  `outcomes` list (carrying `symbol`/`date`/`dataset_id`) to 10 aggregate-only fields
  (`chunks_total`, `chunks_done`, `chunks_fetched`, `chunks_reused`, `chunks_unchanged`,
  `chunks_failed`, `trades_total`, `quotes_total`, `percent_complete`, `elapsed_seconds`) — no UI
  surface affected; a repo-wide search of `apps/frontend` finds zero references to this endpoint.
- `apps/backend/app/research/vault.py` — the new predicate and resolver have no route of their
  own; reachable only through the UI-adjacent endpoints listed above.
- `apps/backend/app/research/micro_snapshots.py`'s choke-point routing also reaches
  `scout.py`, `walkforward.py`, `micro_join.py` (2 call sites), `edge_report_cache.py` (2 call
  sites), and `pnl_scan.py` — the remaining 5 of its 8 downstream consumers not already named
  above. No dedicated UI panel could be confidently traced to each of these five specifically
  (unlike `edge_report.py`, `setups.py`, and `desk_screen.py` above, which map 1:1 to panels
  directly observed in `/structure`'s and `/desk`'s own fetch calls); any UI-visible effect they
  have is already covered by the whole-page regression rows in the table above.
- `apps/backend/tests/test_vault.py`, `test_micro_readiness.py`, `test_tick_recorder.py` —
  test-only, no UI impact.

---

## Summary

- **Frontend surfaces changed:** 0 (zero `.tsx`/`.ts` files touched this iteration)
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 6 files with no UI-rendering surface of their own (`vault.py`,
  `micro_snapshots.py`, `tick_recorder.py`, `micro_routes.py`, plus 3 test files); 2 files
  (`micro_readiness.py`, `routes.py`) feed already-shipped UI surfaces through response shapes
  that are unchanged in name/structure — only row *membership* can broaden, and does not today
  against the real store (0 registered vault universes)
