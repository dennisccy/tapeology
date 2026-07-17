# goal-fast_wall-iter-6 Execution Plan

Session `fast_wall`, iteration 6, depth **full**. Target journey **J-06** ("Restarts stop hurting —
the durable setups scan cache") — the seventh and final Must-have journey of "The Fast Wall"
interlude. Required-still-passing (full regression, closing-iteration framing): J-01, J-02, J-03,
J-04, J-05, J-07. Full detail, acceptance criteria, and the TC-1..TC-9 test-first contract live in
`docs/phases/goal-fast_wall-iter-6.md` — the developer must read that file in full; this plan is a
guide, not a restatement.

**Alignment check:** J-06 is named verbatim in `docs/goal.md`'s Must-have user journeys and Key
Capability 6 ("The setups durable scan cache"), and directly serves Success Criteria #3 ("the heavy
reads answer at interactive speed... a backend restart no longer re-pays cold costs") and #5 ("every
accelerator is rebuildable and proven byte-identical"). The critical anti-goals "Accelerators are
never sources of truth" and "No divergent accelerator output" govern this work directly — TC-1..TC-6
exist specifically to prove them. If J-06 lands cleanly, all 7 Must-have journeys become `passing`;
whether that is `GOAL_ACHIEVED` is the evaluator's call next iteration, not predetermined here. No
drift from the project goal; no scope creep found — the phase spec's OUT OF SCOPE section is explicit
and is carried forward unchanged below. `runs/goal-session-fast_wall/state/blueprint.md` was already
refined at decompose time with the exact `setups_scan_cache.db` accelerator shape (key composition +
path resolution) — this plan matches it.

## What to Build

- New `apps/backend/app/research/setups_scan_cache.py`: `SetupsScanCache` — a **durable-only** SQLite
  cache (mirrors `edge_report_backtest_cache.py`'s "no in-process hot slot of its own" shape, NOT
  `EdgeReportCache`'s hot+durable shape — `setups.py` already owns its own hot slot `_SCAN_CACHE`, so
  this module needs no second one). `lookup(key: str) -> dict | None` / `publish(key: str, result:
  dict) -> None`; a fresh short-lived connection per call (the `JournalStore._read_conn` precedent,
  WAL + `busy_timeout`); `sqlite3.Error` swallowed on both methods (a miss/no-op, never a crash).
  Result JSON stored WITHOUT `sort_keys` (the `EdgeReportCache._insert` byte-identity discipline).
  Path resolver function (the `resolve_cache_db_path` / `resolve_backtest_cache_db_path` precedent):
  env `TAPEOLOGY_SETUPS_CACHE_DB` if set, else `Path(store.root).parent / "setups_scan_cache.db"`
  (`BarStore.root` is the existing public property, added at J-02 precisely for this future sibling-
  path use). No `reindex()`/bulk-rebuild method — `lookup`/`publish` alone serve every caller.
- `apps/backend/app/research/setups.py`: `compute_setups`'s key changes from `(id(config),
  _store_signature(store))` to `(config_content_hash, _store_signature(store))`, where
  `config_content_hash = edge_report_cache._config_content_hash(config)` IMPORTED verbatim (never
  re-derived) — the conservative whole-config hash, NOT `config.config_fingerprint()` alone (the
  fingerprint's exclusion set drops exactly the `setups_*`/`tradability_*`/`sr_*` families this scan
  reads — see TC-3). `compute_setups` becomes a three-tier lookup: hot slot (unchanged atomic
  discipline) → the new durable `SetupsScanCache` (self-resolved from the `store: BarStore` param
  already in scope — no FastAPI DI, no signature change) → `_run_full_panel_scan`. A durable hit
  republishes to the hot slot; a full miss publishes to both layers (durable write before the
  hot-slot rebind).
- Refresh `setups.py`'s B3 module-docstring/block-comment (currently states the memo is
  "PROCESS-LOCAL and in-memory only — never SQLite/disk-persisted") to describe the new two-tier
  (hot slot + durable) reality. Documentation-only; no behavior implied beyond the code change above.
- New `apps/backend/tests/test_setups_scan_cache.py` (durability round-trip, publish-failure
  swallowing, corrupted-DB tolerance — the `test_edge_report_backtest_cache.py`/`test_dataset_index.py`
  naming precedent) + additions to `tests/test_setups.py` for TC-1..TC-8 (restart simulation,
  content-hash equality across distinct-identity equal-content `Config` objects, `setups_*`-family
  busting, store-signature busting, cache-loss recompute, the non-vacuous mutation probe).
- Zero frontend code change. Browser-QA re-verifies the EXISTING `/structure` page still reaches
  every section's ready/honest-empty state (Case Studies especially) with this iteration's caching
  change underneath it (TC-9).

### Two hard implementation constraints — both are existing guard tests, read before coding

1. **`test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes`**
   (`tests/test_setups.py:995-1017`, MUST pass byte-unmodified) asserts `compute_setups`'s source
   contains **exactly one** line (stripped) starting with `"_SCAN_CACHE = "` and exactly one
   `"global _SCAN_CACHE"`. The durable-hit-republish path and the full-miss-publish path CANNOT each
   carry their own `_SCAN_CACHE = (...)` statement — both must funnel through the SAME single rebind
   (e.g. resolve `result` from whichever tier answered, then rebind the hot slot once, after the
   tiered lookup, covering both the durable-hit and full-miss cases — never for the hot-slot-hit
   case, which returns immediately and touches `_SCAN_CACHE` not at all).
2. **`test_compute_setups_itself_never_touches_the_dataset_store`** (`tests/test_setups.py:758-771`,
   MUST pass byte-unmodified) asserts the substring `"dataset"` (case-insensitive) never appears
   ANYWHERE in `compute_setups`'s or `_run_full_panel_scan`'s source — including docstrings and
   comments, not only code. Neither function touches `DatasetStore`, so this should hold naturally,
   but be deliberate when writing the new tiered-lookup docstring/comments inside `compute_setups`:
   do not use the word "dataset" there (e.g. avoid describing the durable cache's path as "beside the
   dataset dir" inside this function) — park any such wording in the module docstring or
   `SetupsScanCache`'s own docstring instead, outside the two guarded functions.

## Out of Scope (verbatim from phase spec — do not relitigate)

- Any change to `levels.py`, `tradability.py`, `backtests.py` (J-03's files) — untouched;
  `compute_tradability` is called from `_run_full_panel_scan` exactly as before.
- Any change to `bars.py`, `datasets.py`, `dataset_index.py` (J-02's files) — unaffected, zero diff
  expected.
- Any change to `edge_report.py`, `edge_report_compute.py`, `edge_report_cache.py`'s method BODIES,
  or `edge_report_backtest_cache.py` (J-01/J-04/J-05's files) — only an IMPORT of
  `_config_content_hash` from `edge_report_cache.py` is allowed (reuse, never re-derive).
- Any new `/structure`/`/studies` UI element, nav entry, or page; any new `Config` field or runtime
  dependency beyond stdlib `sqlite3` (`config_fingerprint` stays `4d665603569b9dbf`).
- Deleting or weakening `tests/test_setups.py:758-771`/`:995-1017`, the module's existing concurrency
  tests, or any other existing test anywhere in the suite.
- Any MCP tool change — the `setups` MCP tool proxy stays byte-identical (tool count 18).
- A `reindex()`/bulk-rebuild method on `SetupsScanCache` — not needed.
- Running the CLI warmer / full real-corpus sweep to completion, or the `reports/pnl/pnl-history.md`
  append — that is J-04/J-05's already-closed scope, not reopened here.
- Verifying goal.md's literal real-corpus "within 10 seconds of navigation" figure — tagged
  `*(operator-verified on the real corpus)*`, non-blocking bonus only, never required for this
  iteration's Definition of Done.

## Agents Required

- developer: yes — implements J-06 end to end: the new `setups_scan_cache.py` module + its test
  file, `compute_setups`'s three-tier rewrite in `setups.py` (respecting the two guard-test
  constraints above), the B3 docstring refresh, and the `test_setups.py` TC-1..TC-8 additions. Also
  performs the zero-code browser re-verification pass (TC-9) against the established scoped fixture
  pair (ports 8391/3391 — see Visual Requirements below). This project's agent roster has one
  implementation agent (`developer`) covering both backend and frontend/browser-verification work —
  no separate backend-data/frontend-ux agents exist here. In code terms this iteration is
  backend-only (new cache module + `setups.py`); no frontend product file should change (`git diff
  apps/frontend/` must be empty).

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/research/setups_scan_cache.py` (NEW) — `SetupsScanCache`, `lookup`/`publish`,
  the path resolver function.
- `apps/backend/app/research/setups.py` — `compute_setups` (currently `setups.py:386-409`)
  three-tier rewrite; the B3 module-docstring block (currently `setups.py:112-123`) and the
  `_SCAN_CACHE` block comment (currently `setups.py:324-369`) refreshed to describe the new
  two-tier reality. `_store_signature` (currently `:372-383`) stays unchanged — reused as-is.
- `apps/backend/tests/test_setups_scan_cache.py` (NEW) — durability, publish-failure swallowing,
  corrupted-DB handling.
- `apps/backend/tests/test_setups.py` — TC-1..TC-8 additions (restart simulation, content-hash
  equality, `setups_*`-family busting via a real field e.g. `setups_reaction_threshold_bps`,
  store-signature busting, cache-loss recompute, the non-vacuous mutation probe pre-seeding a
  deliberately wrong payload under the live key). The two existing guard tests (`:758-771`,
  `:995-1017`) and the module's existing concurrency tests (`_SCAN_CACHE` atomicity/threading) stay
  byte-unmodified.
- `docs/handoffs/goal-fast_wall-iter-6-dev.md` — dev handoff (required).
- **Zero diff expected:** `levels.py`, `tradability.py`, `backtests.py`, `bars.py`, `datasets.py`,
  `dataset_index.py`, `edge_report.py`, `edge_report_compute.py`, `edge_report_cache.py` (method
  bodies — only the existing `_config_content_hash` import target), `edge_report_backtest_cache.py`,
  `app/mcp/__init__.py`, `config.py`, `routes.py` (no new dependency needed — `compute_setups`'s
  signature and its 4 call sites stay frozen), and every file under `apps/frontend/`.

## UI Evolution (Frontend Present: yes)

- New user-facing capability: none new. The EXISTING Case Studies list (`/structure`) and `/studies`
  page's underlying scan becomes faster on a warm durable cache and survives a backend restart; no
  new button, panel, or filter.
- New information displayed: none. `compute_setups`'s served shape (`{"events": [...]}`) is
  byte-unchanged.
- New user actions: none — no new control anywhere on `/structure` or `/studies`.
- UI surface changes: none — `/structure`'s sections and `/studies` are byte-unchanged this
  iteration.
- Navigation changes: none.

## Visual Requirements (Frontend Present: yes)

- Component patterns: none new — reuse the existing `LoadingPanel`/`EmptyState`/table components on
  `/structure`'s Case Studies section exactly as shipped (testids `case-studies-loading` /
  `case-studies-empty` / `case-studies-table`, confirmed present at `structure/page.tsx:1915/1922/1931`).
- Layout: unchanged — `/structure`'s existing Tradable Map / Case Studies / Edge Report section
  order.
- Key visual effects: none new — dark-only, dense, terminal-grade (Design Direction unchanged from
  eras 4–5B); no new visual language.
- States to handle: TC-9's browser check runs against the ESTABLISHED scoped fixture recipe (ports
  8391/3391, `TAPEOLOGY_DATASET_DIR` pointed at a copy of `tests/fixtures/datasets_j03`,
  `TAPEOLOGY_BAR_DIR` pointed at a fresh empty directory, PLUS this iteration's new
  `TAPEOLOGY_SETUPS_CACHE_DB` appended into the same scoped temp dir). Because the scoped bar dir is
  created empty (`mkdir -p`, never populated) and the committed `tests/fixtures/bars/` fixture itself
  carries zero `"5m"`-timeframe series, Case Studies is EXPECTED to render its honest
  `case-studies-empty` "No band-touch events scanned yet." state regardless of J-06's correctness
  (iter-5's own lesson: a populated-table cache-HIT demonstration is the keyless pytest suite's job —
  TC-1 through TC-6 — never the browser leg's). The pass condition is: no `-loading`-suffixed testid
  remains anywhere on the page within 10 seconds of navigation, and the Tradable Map / Edge Report /
  Registry / Comparison sections render exactly as they did in iter-5 (zero visual regression).

## Key Test Scenarios

(Condensed — full acceptance detail and exact TC wording in `docs/phases/goal-fast_wall-iter-6.md`.)

- TC-1 (restart simulation): hot slot cleared, durable cache warm → a call-counting spy on
  `_run_full_panel_scan` records ZERO new calls; the result is byte-identical to the original scan.
- TC-2 (identity fragility gone): a second, freshly-constructed but content-equal `Config` instance
  is a cache HIT (zero new scan calls) — proving the key is content-derived, not `id(config)`.
- TC-3 (fingerprint insufficiency proven): changing one `setups_*`-family field (e.g.
  `setups_reaction_threshold_bps`) on an otherwise-identical `Config` busts the cache (exactly one
  new scan call) — proving the CONTENT hash drives the key, since `config_fingerprint()` alone would
  NOT catch this field.
- TC-4 (store-signature busting): recording a new "5m" bar series into the same store busts the key
  (exactly one new scan call).
- TC-5 (cache-loss harmless): deleting the durable DB file + clearing the hot slot recomputes exactly
  once, byte-identical to the pre-deletion result.
- TC-6 (non-vacuous mutation probe — iter-3's lesson applied directly): a durable row pre-seeded
  under the EXACT current key with a DELIBERATELY WRONG `events` payload is returned VERBATIM by
  `compute_setups` — proving the durable-hit path is genuinely read, not dead code a naive
  byte-identity assertion could pass vacuously.
- TC-7 (frozen foundations): the two source-introspection guards + the MCP 18-tool-count guard pass
  byte-unmodified; `config_fingerprint()` still `4d665603569b9dbf`.
- TC-8 (publish-failure swallowed): an unwritable/corrupted durable cache DB never blocks
  `compute_setups`/`GET /research/setups` from serving the freshly-scanned result (HTTP 200 either
  way).
- TC-9 (browser, scoped fixture pair): `/structure` reaches every section's ready/honest-empty state
  within 10s of navigation, no `-loading`-suffixed testid remains, Case Studies renders
  `case-studies-empty` (expected — see Visual Requirements), zero visual regression vs iter-5.
- Required-still-passing J-01, J-02, J-03, J-04, J-05, J-07 remain green (deterministic replay + LLM
  fallback, mechanically verified) — this is the closing iteration's full regression pass; per
  iter-2's lesson, treat the byte-identity/zero-diff evidence for these as a required gate, not a
  nicety, on any lane where replay doesn't directly re-exercise them.
- Full unit suite green (no test deleted or weakened), `config_fingerprint` unchanged, dev handoff
  written at `docs/handoffs/goal-fast_wall-iter-6-dev.md`.

## Process Notes

- `compute_setups`'s own signature (`store: BarStore, config: Config`) and its 4 call sites
  (`routes.py:1945`, `:1967`, `edge_report.py:582`, `:932`) stay byte-unchanged — no FastAPI
  dependency injection for the new cache; resolve/construct `SetupsScanCache` lazily inside
  `setups.py`, keyed off the `store` param already passed everywhere (unlike `BarIndex`/
  `DatasetIndex`/`EdgeReportCache`, there is no owning route/class to inject through here — see the
  phase spec's own NOTES section for the full rationale).
- If Chrome MCP fails to start: do not block the rest of the iteration. TC-1 through TC-8 are fully
  keyless/automated and constitute the real proof of J-06's correctness (iter-4/iter-5's lesson:
  retry the scoped recipe once in a fresh session; if it still fails, escalate the environmental
  blocker rather than treating it as new/unexplained).
- A golden-replay "possible regression" FAIL must be checked against its own evidence screenshot
  before being trusted — a "Backend unreachable" render is an infra false-negative, not a regression
  (iter-4's lesson; standing operating guidance for this closing iteration's full regression pass).
