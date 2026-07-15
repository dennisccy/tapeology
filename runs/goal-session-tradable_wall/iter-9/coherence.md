# Iteration 9 — Coherence Audit

**Iteration:** goal-tradable_wall-iter-9
**Date:** 2026-07-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

<!-- COHERENCE-WARN: only advisory issues; does NOT block GOAL_ACHIEVED -->

---

## Scope of this iteration

Backend-only (confirmed: `git diff badc242b --stat` outside `runs/`/`reports/`/`docs/handoffs/` touches
only `apps/backend/**`; zero `apps/frontend/**` hunks, corroborated by the ui-surface-map's "Modified
components: 0" and the frontend handoff's "Files Changed: None under `apps/frontend/`"). Seven tracked
files changed (`edge_report.py`, `pnl_history.py`, `pnl_ledger.py`, `routes.py`, three test files) plus
three new files (`edge_report_cache.py`, `test_edge_report_cache.py`, `test_pnl_history.py`), read in
full. `blueprint.md`'s only content change is the additive iter-9 annotation on the existing
"Edge-report cells" Data Contract row.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Edge-report cells (blueprint row: `edge_report.py` → `GET /research/edge-report`) | OK | `run_strategy_comparison_report` (`apps/backend/app/research/edge_report.py:16-45`) is now a thin dispatcher: `cache=None` (every existing caller, unchanged) calls `_compute_strategy_comparison_report` directly; `cache=<EdgeReportCache>` (the route only) calls `cache.get_or_compute(dataset_store, config, compute)` where `compute` is a closure over that SAME function (`edge_report.py:40-41`). `_compute_strategy_comparison_report` (`edge_report.py:48-67`) is the byte-identical pre-J-08 body, renamed only — confirmed structurally by `test_cache_wiring_source_never_duplicates_the_computation` (`tests/test_edge_report.py:589-598`), which asserts exactly one definition of each name exists. `edge_report_cache.py` never imports `backtests`/`setups`/`tradability`/`levels`/the tape engine — confirmed by `test_cache_source_never_computes_a_research_value_itself` (`tests/test_edge_report_cache.py:401-421`), which asserts those import statements are absent. `GET /research/edge-report` (`routes.py:2093-2131`) still returns `run_strategy_comparison_report(...)`'s output directly — no reshaping, one endpoint. The MCP `edge_report` proxy (`app/mcp/__init__.py:106`, `:280`) is untouched by this diff and still maps to the same `/research/edge-report` path, so it inherits the cache transparently. Byte-identity (warm cache == fresh cache-cleared compute, on the real non-degenerate 3-cell shape, not `cells: []`) is proven by `test_warm_cache_report_is_byte_identical_to_a_fresh_cache_cleared_compute` and the route-level `test_edge_report_route_response_is_byte_identical_whether_cache_is_cold_or_warm`. Champion pointer untouched: `test_cached_report_never_moves_the_champion_pointer`. This is a rebuildable accelerator per skill Part A.3 ("re-format/serve-verbatim is fine"), not a duplicate computation and not a non-canonical source. |
| PnL ledger / `pnl-history.md` (pre-existing owner `app/research/pnl_ledger.py`, self-documented at `pnl_ledger.py:1-2` as "Data Contract row 32's ONE owner"; served by `GET /research/pnl/ledger` + MCP `pnl_ledger` per `app/mcp/__init__.py:93,294`) | UNREGISTERED (blueprint gap, not a computation violation) | `git log --oneline -- apps/backend/app/research/pnl_ledger.py` shows exactly one prior commit (`9d89ec6`, the `tape_to_profit` era) before this diff — iter-9 is the **first** Era 5B iteration to touch this file. It adds a second, additive row composer `append_strategy_comparison_row` (`pnl_ledger.py:221-300`) beside the untouched `append_validation_row`, and a new markdown branch `_render_strategy_comparison_row_lines` (`pnl_ledger.py:310-354`) invoked from the SAME `render_history_markdown` (`pnl_ledger.py:409-411`) via a `row.get("kind")` dispatch — no second `ledger_projection`, no second REST route, no second renderer. Every cell field (`measurement`, `null_baseline`, `insufficient_sample`) is copied verbatim from the caller-supplied, already-computed `run_strategy_comparison_report` output via `_ledger_cell` (`pnl_ledger.py:209-218`), never recomputed — confirmed by `test_append_strategy_comparison_row_composes_cells_verbatim_with_basis_added` (`tests/test_pnl_ledger.py:767-800`). So this is **not** a duplicate-computation or non-canonical-source violation. But `runs/goal-session-tradable_wall/state/blueprint.md` (this session's own contract) has never mentioned `pnl_ledger.py`, `GET /research/pnl/ledger`, or MCP `pnl_ledger` anywhere — not in the Era 5B "New" table, not in the "Existing owners Era 5B reads verbatim" table (which already lists six other pre-existing owners Era 5B touches: `levels.py`, `bars.py`, `backtests.py`, the tape engine, `taxonomy.py`, the meta router) — and iter-9 did not add it despite now being the first iteration to touch this file. The iter-9 spec's own "Data-contract additions" field reasons through this correctly at the *value-identity* level ("not a new value; existing owner") but that reasoning never made it into `blueprint.md` as an entry, unlike the Edge-report row, which DID get its additive annotation this same iteration. |

No duplicate computation and no non-canonical source anywhere in the diff — both findings above are
either OK or an unregistered-owner completeness gap, never a value-divergence risk.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/structure` → Edge Report section (warm-cache latency change only) | OK — no new surface | Zero `apps/frontend/**` files in the diff; `reports/phase-goal-tradable_wall-iter-9-ui-surface-map.md` states "New pages/routes: 0", "Modified components: 0", "Navigation changes: no". The frontend handoff (`docs/handoffs/goal-tradable_wall-iter-9-frontend.md`) independently confirms by direct inspection of `apps/frontend/app/structure/page.tsx` and `apps/frontend/lib/api.ts` that the existing plain `fetch()` + verbatim render path needs no change — the same code path already handles both the pre-J-08 slow case and the post-J-08 fast case. Canonical home unchanged: `blueprint.md:25,35` (`/structure` → Edge Report, Structure nav section). |
| `pnl_history.py`'s new `--append-report`/`--enhancement-id`/`--title`/`--out` CLI flags | OK — not an IA surface | Operator-run terminal command only (no route, no button, no page) — the identical precedent already established for `python -m app.research.edge_report` (noted in `blueprint.md`'s Edge-report row). Nav is frozen for Era 5B per the blueprint's own IA header; a CLI flag addition to an existing operator tool carries no navigation obligation. |

No new page, route, or nav entry this iteration — Step 2 has nothing to fail on.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Register `pnl_ledger.py`/`pnl_history.py` in `blueprint.md`.** Since iter-9 is the first Era 5B
  iteration to touch this pre-existing owner, add one row/line to the "Existing owners Era 5B reads
  verbatim" table (mirroring the six rows already there) — e.g. "PnL-ledger register | `app/research/pnl_ledger.py` | `GET /research/pnl/ledger` | Data Contract row 32 (era-3); era-5B additively extends it with a `strategy_comparison` row kind (iter-9/J-08) composed verbatim from `edge_report.py`'s own cells — `ledger_projection`/`render_history_markdown` stay the single serving read/renderer, no second path." Finite, one-line fix; does not require touching any code.
- **Column-label collision in `pnl-history.md`.** The new 3-way row's markdown table
  (`_render_strategy_comparison_row_lines`, `pnl_ledger.py:340`) reuses the header `side` for
  `cell["band_side"]` (`support`/`resistance`, a price-level concept). The pre-existing two-way row's
  table (`pnl_ledger.py:429`) already uses the same header `side` for the string `"baseline"` /
  `"candidate"` (a comparison-role concept). `test_existing_two_way_rows_render_unchanged_alongside_a_new_3way_row`
  (`tests/test_pnl_ledger.py:897-931`) proves both row kinds can render into the *same* document, so a
  reader of `reports/pnl/pnl-history.md` sees the column name `side` mean two different things in two
  adjacent tables. Cosmetic/labeling only (skill Part C) — never a data-contract or IA violation; worth
  a rename (e.g. `band side` vs. the existing `side`) next time this file is touched. Minor,
  self-contained addendum: `_render_strategy_comparison_row_lines`'s own docstring (`pnl_ledger.py:314-316`)
  claims the new table is built "WITHOUT a `side` column," which does not match the header actually
  emitted two lines below it — a documentation-accuracy nit, not a functional issue.
- No FAIL-worthy Data Contract or IA violation was found; the cache implementation itself (durability,
  atomic publish, torn-read guard, four-part key with a documented rationale for exceeding the plan's
  three, store-integrity bypass) is unusually well-evidenced by tests and is judged sound for the
  single-source-of-truth question this gate exists to police.
