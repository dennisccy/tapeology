# App Blueprint — fast_wall (Interlude: The Fast Wall)

<!--
Coherence contract for the whole app. Drafted by goal-decomposer at baseline; auto-approved by
run-goal.sh unless --require-blueprint-approval. The coherence-auditor enforces it every iteration.
This interlude layers ON TOP of eras 1–5B (session `tradable_wall`) — the nav is FROZEN (no new
entry, no new page; anti-goal "No new nav entries or pages"); every new capability lives inside the
existing `/structure` → Edge Report section, or is a backend-only accelerator with no dedicated UI
panel. Single source of truth is anti-goal #6 (critical): each value below is computed once by ONE
module and served by ONE endpoint; REST/MCP/reports read it verbatim. This interlude changes only
WHEN/HOW OFTEN the frozen era-1–5B computations run — never WHAT they compute.

iter-4 update: refined the "Compute-job snapshot" row (below) to its full field/type shape now that
J-04 actually builds `EdgeReportComputeManager` — additive detail only, same single owner/endpoint
pre-registered at baseline; no new row, no nav change.

iter-5 update: refined the "edge_report_backtests.db" rebuildable-accelerator bullet (below) to its
exact key composition now that J-05 actually builds `EdgeReportBacktestCache` — additive detail
only, same non-canonical accelerator status pre-registered at baseline; no new row, no nav change.
-->

## Information Architecture

**Layout shell:** persistent top nav bar + main content; dark-only, dense, terminal-grade — unchanged
from eras 1–5B.

**Navigation skeleton** (frozen — no new top-level entry this interlude):

```
Tapeology
├── Cockpit        /                     (unchanged)
├── Journal        /journal  · /journal/[id]     (unchanged)
├── Studies        /studies              (unchanged; reads accelerated by J-06)
├── Performance    /performance          (unchanged)
└── Structure      /structure            (Tradable Map · Case Studies · Edge Report)
                                          Edge Report section gains: not-computed panel +
                                          "Compute edge report" button + progress line
```

**Feature / journey homes** (this session's Must-have journeys; each reachable in ≤2 clicks from nav):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 Cache-or-honest-absence edge report | `/structure` → **Edge Report** section (not-computed panel) | Structure |
| J-02 Verified-content store caches + durable dataset index | no dedicated UI panel — accelerates `GET /research/datasets` and all bar/dataset reads behind Structure + Studies | Structure / Studies (cross-cutting) |
| J-03 Per-run structure arm memo | no dedicated UI panel — accelerates the backtest sweep the J-04 button triggers | Structure (cross-cutting) |
| J-04 Operator-run compute (button + CLI warmer) | `/structure` → **Edge Report** section ("Compute edge report" button + progress line) | Structure |
| J-05 Resumable + parallel sweep | no dedicated UI panel — accelerates the same compute job J-04 exposes | Structure (cross-cutting) |
| J-06 Durable setups scan cache | no dedicated UI panel — accelerates `GET /research/setups`, backing Structure's Case Studies + `/studies` | Structure / Studies (cross-cutting) |
| J-07 Foundation regression sentinel | no UI home — guards all surfaces | (cross-cutting) |

Era 1–5B's homes (Cockpit price chart + tape markers, Journal, Studies, Performance, Structure's
Tradable Map / Case Studies sections, the era-5 fetch control + provenance badge) are **preserved
verbatim** — full registration lives in `runs/goal-session-tradable_wall/state/blueprint.md`. This
interlude does not move, rename, or duplicate any of them.

## Data Contract

Each value is computed once by ONE module and served by ONE endpoint (anti-goal #6, single source of
truth); UI/MCP/reports may only re-format what the canonical endpoint returns.

**New (this interlude) — each with exactly one owner:**

| Value / entity | Computed by (single module) | Served by (single endpoint) | Notes |
|---|---|---|---|
| Not-computed edge-report payload (`status: "not_computed"`, `detail`, `dataset_count`, `register`, embedded `compute` snapshot or `null`) | `app/research/edge_report.py` (`peek_strategy_comparison_report`) | `GET /research/edge-report` (existing route, rewired — same `Depends`/`cache=cache` wiring) | `status` key is the discriminator; a real report never carries one; a warm key still serves the report **verbatim** (unchanged shape); an empty registry still computes inline (O(1), zero backtests); MCP `edge_report` proxy mirrors byte-identically |
| Compute-job snapshot — `id: str` (job uuid), `state: "running"\|"done"\|"cancelled"\|"failed"`, `force: bool`, `started_utc: str (ISO-8601)\|null`, `finished_utc: str (ISO-8601)\|null`, `error: str\|null`, `progress: {phase: str, backtests_total: int, backtests_done: int, backtests_from_cache: int, current: {dataset_id: str, strategy_id: str}\|null}` | `app/research/edge_report_compute.py` (`EdgeReportComputeManager`) | `GET /research/edge-report/compute` (poll; returns the snapshot or `null` if no job has ever run in this process); started via `POST /research/edge-report/compute` (body `{force: bool=false}`); cancelled via `POST /research/edge-report/compute/cancel` (409 when idle) | Process-scoped bookkeeping, honestly lost on restart (existing job-manager precedent) — never a research value; single-flight (exactly ONE job slot, never per-id like `StudyJobManager`/`BacktestJobManager`); REST-only, **no MCP tool**. The SAME snapshot is embedded verbatim as the `compute` field of the not-computed edge-report payload above — never a second derivation, never a second endpoint. `progress.backtests_from_cache` (iter-5, J-05) genuinely increments once a per-pair sub-cache exists — same field, same owner, same endpoint; only its runtime value changed from always-0 to meaningful. |

**Rebuildable accelerators (explicitly NOT canonical values — deleting any loses nothing; the next
read/compute re-verifies or recomputes byte-identically through the one canonical owner below):**

- the two in-process verified-content stat-keyed caches added to `bars.py` / `datasets.py` (metadata only for `datasets.py`; `load_events`/`replay` always re-verify)
- `dataset_index.db` (`app/research/dataset_index.py`) — durable sibling of the metadata cache
- `setups_scan_cache.db` (`app/research/setups_scan_cache.py`)
- `edge_report_backtests.db` (`EdgeReportBacktestCache` — one durable row per dataset×strategy pair sub-result; key = sha256 of the canonical JSON of `{dataset_id, dataset_checksum, strategy_id, profile, config_fingerprint, config_content_hash, strategy_registry, bar_store_signature}` — `bar_store_signature` reuses `setups._store_signature(bar_store)` verbatim, never re-derived; value = the runner's own per-pair `result` block stored WITHOUT `sort_keys`; path env `TAPEOLOGY_EDGE_SWEEP_CACHE_DB` else a `.data/edge_report_backtests.db` sibling of the dataset dir — iter-5, J-05)
- the existing `edge_report_cache.db` (`EdgeReportCache`)
- the per-run `_StructureArmMemo` (in-memory, one instance per backtest run — never persisted)

Every accelerator's owner remains the store/computer it accelerates (`bars.py` owns its own cache,
`edge_report.py` / `edge_report_compute.py` own the sweep caches, `setups.py` owns its scan cache) — no
accelerator introduces a second computation path, and every one ships with a determinism/equivalence
test proving byte-identity to the fresh sequential compute (anti-goal "No divergent accelerator
output").

**Unchanged existing owners (frozen foundation — eras 1–5B; full registration in
`runs/goal-session-tradable_wall/state/blueprint.md`):** raw levels + A/B/C zones (`levels.py` →
`GET /research/levels`); tradable level map (`tradability.py` → `GET /research/tradability`); touch
events + case registry (`setups.py` → `GET /research/setups`); edge-report cells themselves
(`edge_report.py`'s `run_strategy_comparison_report` — the computation is unchanged, only *when* it
runs changes); `structure_tape_map` + strategy registry (`strategies.py` → `GET /research/strategies`);
recorded datasets (`datasets.py` → `GET /research/datasets`); bar series (`bars.py` + `bar_index.py` →
`GET /research/bars`); backtest aggregates (`backtests.py` → `GET /research/backtests`); PnL-ledger
register (`pnl_ledger.py` → `GET /research/pnl/ledger`); tape five-state timeline (frozen `TapeEngine`
→ `GET /tape/{ticker}/history`); taxonomy (`taxonomy.py` → `GET /research/taxonomy`); UI route map
(`GET /meta/ui-routes`).

<!-- Codebase probe at baseline (iter-0) confirmed the pre-interlude state matches goal.md's diagnosis:
GET /research/edge-report (routes.py:2093) calls run_strategy_comparison_report directly through the
ONLY existing cache method EdgeReportCache.get_or_compute (no lookup/compute_and_publish split yet) —
a cold cache genuinely computes inline inside the GET. None of edge_report_compute.py, dataset_index.py,
setups_scan_cache.py, EdgeReportBacktestCache, level_change_points, basis_day_key, _StructureArmMemo, or
the bars.py/datasets.py stat-keyed caches exist yet. -->

<!-- Codebase probe at iter-4 (before J-04 build): confirmed edge_report_compute.py still does not
exist; EdgeReportCache already has lookup/compute_and_publish (J-01) beside the untouched get_or_compute;
run_strategy_comparison_report(store, dataset_store, bar_store, config, *, cache=None) has no force/
progress/should_abort/sub_cache/workers hooks yet; routes.py has no /research/edge-report/compute*
routes; ResearchRegistry wires only study_jobs + backtest_jobs (the StudyJobManager/BacktestJobManager
precedent this iteration's EdgeReportComputeManager follows, adapted to single-flight); the not-computed
payload's `compute` key is unconditionally `None` (peek_strategy_comparison_report:519-524); the MCP
tool list (app/mcp/__init__.py) has exactly 18 registered names, pinned by
test_advertised_tool_set_is_exactly_capability_6. -->

<!-- Codebase probe at iter-5 (before J-05 build): confirmed EdgeReportBacktestCache/
edge_report_backtests.db does not exist anywhere yet; `_split_cells` (edge_report.py:405-481) calls
`_run_backtest` directly inline with no `run_pair` seam; `_ProgressReporter.pair_done()`
(edge_report.py:397-402) already emits a `backtests_from_cache` field in its patch but NEVER
increments it (dead, always 0 since J-04); `run_strategy_comparison_report`'s `sub_cache=`/`workers=`
keyword params (edge_report.py:544-545) exist since J-04 but are accepted-only —
`EdgeReportComputeManager.trigger()` (edge_report_compute.py:116-181) does not pass either into its own
`run_strategy_comparison_report` call, and the CLI's `main()` (edge_report_compute.py:244-299) passes
`workers=args.workers` but never `sub_cache=`. No `ProcessPoolExecutor`/`multiprocessing` usage exists
anywhere in `apps/backend/app` yet (only an unrelated `ThreadPoolExecutor` in
`providers/adapters/alpaca.py`). `setups._store_signature` (setups.py:372-383) is the confirmed
existing bar-store-signature precedent this iteration reuses, never re-derives. J-04 itself remains
`partial` (backend/API/CLI fully proven; the required browser click-through has no screenshot — Chrome
MCP failed to start in the prior session, reproduced by 4 agents) — this iteration re-attempts that
screenshot with zero new code before building J-05. -->
