# Iteration 11 — Coherence Audit

**Iteration:** goal-rapid-microscope-iter-11
**Date:** 2026-08-19
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note

Backend-only iteration: 9 changed files, all under `apps/backend/` (`vault.py`, `micro_snapshots.py`,
`micro_readiness.py`, `tick_recorder.py`, `micro_routes.py`, `routes.py`, plus `test_vault.py`,
`test_micro_readiness.py`, `test_tick_recorder.py`); `docs/goal.md` and `docs/rapid-validation-spec.md`
also changed (spec/goal documentation, not code). Confirmed via `git diff 797ad523b...--stat`: zero
`.tsx`/`.ts` files, zero new routes, zero new MCP tools, zero nav change — matches the ui-surface-map's
own file classification. Blueprint IA (`/`, `/structure`, `/desk`, nothing else) is untouched this
iteration, so Part B (Information Architecture) has no new surface to evaluate.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Withhold predicate ("is this dataset part of an unresolved vault pool") — the choke point behind the "Corpus readiness truth" and "Vault shards, universes, exposure ledger" rows | OK | Single new computing function `vault.unresolved_pool_universe_by_dataset_id` (`apps/backend/app/research/vault.py:809-882`) + its frozenset wrapper `unresolved_pool_dataset_ids` (`vault.py:884-891`). Exhaustive grep for `vault\.withheld_dataset_ids(\|vault\.withheld_universe_by_dataset_id(` across `apps/backend/app/**/*.py` returns **zero** production call sites outside `vault.py` itself — the two narrower pre-iter-11 functions now exist only as internal building blocks the new predicate composes (test (a) inside `unresolved_pool_universe_by_dataset_id`), not as competing computations. Exactly two authorized callers of the new predicate exist, matching the blueprint's own iter-11 note verbatim: (1) `micro_snapshots._unresolved_pool_ids` (`micro_snapshots.py:134-145`), which feeds `withheld_dataset_ids_for_store`/`exclude_withheld` and, through them, all 8 of its existing corpus-wide consumers (`scout.py:1213`, `walkforward.py:1091`, `micro_join.py:180,535`, `edge_report.py:170`, `edge_report_cache.py:313,376`, `pnl_scan.py:248`, `desk_screen.py:713`, `setups.py:527`) with zero call-site changes to any of those 9 files (verified — none of them appear in the diff); (2) `micro_readiness.build_readiness` calling it directly (`micro_readiness.py:348-360`). No third, divergent implementation anywhere. |
| `routes.py`'s `get_withheld_dataset_ids` (dependency behind `GET /research/datasets`, `GET /research/datasets/{id}`, `POST /research/backtests`) | OK — bypass fixed, not introduced | Before this iteration it called `vault.withheld_dataset_ids(vault.shard_ledger_for_dataset_dir(...))` directly, bypassing the choke point (a pre-existing gap, not one this iteration created). The diff (`routes.py:395-418`) now delegates to `micro_snapshots.withheld_dataset_ids_for_store(store)` — the same shared choke point every other consumer uses. This closes a real second-computation-path risk rather than opening one; net effect this iteration is a coherence *improvement*. |
| `sealed_tranche` (existing Data Contract row, `micro_readiness.py`) | OK — shape unchanged, membership broadened per blueprint's own note | Construction site `micro_readiness.py:477-487` is unchanged code (outside the diff hunks) and still emits exactly `{shard_count, symbol_days, by_universe: {universe_id: {shard_count, symbol_days}}}` — no per-shard row, no per-shard `exposure_state`, matching blueprint.md's iter-11 note precisely. Only which dataset ids feed the aggregate changed (via the broadened predicate at `micro_readiness.py:348`), which the blueprint note explicitly documents as a semantics-broadening, not a shape or ownership change. |
| `progress.chunks_fetched` / `chunks_reused` / `chunks_unchanged` / `chunks_failed` / `trades_total` / `quotes_total` / `percent_complete` / `elapsed_seconds` (new sub-fields, "Recorder job + tranche progress/runs" row) | OK — registered this same turn | `blueprint.md`'s "Recorder-progress aggregate sub-fields" table registers exactly these 8 field names against owner `tick_recorder.py` (`TickRecorderComputeManager`), served by the already-registered `GET /research/desk/micro/recorder/compute` (no new endpoint). The diff's `_progress_view` (`tick_recorder.py:653-679`) emits exactly this field set, computed via one shared `_outcome_type_counts` helper (`tick_recorder.py:632-642`) also used by the pre-existing, unchanged `_run_log_entry` — a consolidation (two inline sum blocks → one shared helper) rather than a new duplicate. `micro_routes.py`'s `GET /recorder/compute` handler (`micro_routes.py:500-504`) forwards `snap["progress"]` verbatim with no second computation; `POST /recorder/compute`'s immediate return and `snapshot()` both route through the same `_copy_recorder_snapshot`/`_progress_view` pair (`tick_recorder.py:693-704, 745-782`), so GET and POST can never disagree. Confirmed unregistered before this iteration and newly registered in the same commit that introduces the fields — no lag this time (contrast iter-9's sub-fields, WARN'd until iter-10 caught the paperwork up). |
| Per-chunk `outcomes` / `trade_count` / `quote_count` (internal, never served) | OK — confirmed not leaked | `_chunk_entry`'s new `trade_count`/`quote_count` params (`tick_recorder.py:492-503`) exist solely so `_publish` can accumulate the aggregate `trades_total`/`quotes_total` (`tick_recorder.py:800-805`); the entry itself is appended only to the internal `progress["outcomes"]` list, which `_progress_view`'s explicit-whitelist response construction (`tick_recorder.py:653-679`) never includes. Confirmed no route serves `progress.outcomes` or any per-chunk field — matches DoD/TC-6's aggregate-only requirement. |

No new displayed value appears this iteration outside the registered sub-fields above (per the iteration spec's own "New information displayed: None new to a user" and the ui-surface-map's "0 modified components").

## Information Architecture check

No new page/route/feature this iteration — nothing to evaluate. `git diff --stat` and the
ui-surface-map both confirm zero `.tsx`/`.ts` files touched, zero navigation changes; the existing
3-link nav (Cockpit / Structure / Desk) is untouched.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new frontend surface this iteration) | OK | `git diff --stat` shows 0 frontend files; ui-surface-map confirms "Navigation changes: no" |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Checked and cleared, not a violation:** `micro_snapshots.py` adds a private `_et_session_date`
  helper (`micro_snapshots.py:96-111`) that duplicates the UTC→ET conversion logic already living in
  `micro_readiness._et_datetime` (`micro_readiness.py:126-132`). Line-by-line comparison confirms the
  two are algorithmically identical (`datetime.fromisoformat(...).replace("Z","+00:00")` → UTC
  fallback → `.astimezone(_ET_ZONE)`), so there is no risk of the two modules disagreeing on a given
  record's session date. The diff's own docstring justifies this as an intentional, pre-existing
  per-module idiom (mirrors `referee_evidence.py`) for generic timestamp arithmetic that is not
  itself a Data Contract value — not a new drift pattern. Not flagged as a WARN.
- **Independent auditor's B1/B2/B3 findings (carried context) reviewed against the Data Contract/IA
  rules specifically, per this gate's instructions — none cross into coherence territory:**
  - B1 (`vault._fully_exposed_universe_ids` still gates the `GET /research/desk/micro/vault`
    `symbol_rule`/`date_rule` reveal on shard-ledger rows only) is a completeness gap in the ONE
    already-canonical `vault.build_vault_state` computation (confirmed unmodified this iteration —
    it lives past the last hunk of `vault.py`'s diff), not a second implementation of vault state
    anywhere. No duplicate-computation or non-canonical-source violation.
  - B2 (`progress.trades_total`/`quotes_total` ambiguity against two spec clauses on a one-symbol-day
    run) is a spec-interpretation question about the single registered field, not a second
    computation of it.
  - B3 (the new predicate never calls `verify_chain()`) is a ledger-integrity omission inside the one
    canonical predicate, not a coherence split.
  All three remain correctly out of this gate's scope (integrity findings, not coherence findings) and
  are carried forward by the independent auditor's own report, not silently dropped here.
