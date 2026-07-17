# goal-fast_wall-iter-2 Execution Plan

Session `fast_wall`, iteration 2, single target journey **J-02** ("The stores stop re-reading —
verified-content caches + durable dataset index"). Required-still-passing: **J-01** (shares the
Data-Contract value chain this iteration accelerates — both `peek_strategy_comparison_report`'s
`_verified_records` and `EdgeReportCache._cache_key` call the now-cached `dataset_store.list()` on
every `GET /research/edge-report`, warm or cold) and **J-07** (the standing regression sentinel).
These are the only two `passing` journeys in this session's `journey-history.json`, so together
they are already this iteration's full regression set.

**Alignment check:** matches `docs/goal.md`'s stated dependency order (J-01 → J-02 → J-03 → J-04 →
J-05, with J-06 riding on J-02's durable index) and iter-1's own audit ("Proceed to the next
iteration (J-02)") plus its `eval.md` recommendation. Success Criterion #3 ("the heavy reads answer
at interactive speed when content is unchanged") is this iteration's binding target; Success
Criterion #1 (non-regression) and #5 (every accelerator rebuildable + byte-identical) are the
enforced invariants throughout. No drift, no scope creep detected — the phase spec's OUT OF SCOPE
list is internally consistent with goal.md's Non-Goals ("no new Config field", "no new runtime
dependency", "no auto-compute on page load" — untouched by this purely-read-path iteration).
`Frontend Present: no` is correct per the phase spec's own metadata and goal.md's Product Shape IA
row for J-02 ("no dedicated UI panel"); confirmed by codebase probe — this iteration's five backend
files touch nothing under `apps/frontend/`.

**Codebase probe (confirmed against current `main` before planning):** `dataset_index.py` and the
`TAPEOLOGY_DATASET_INDEX_DB` env var do not exist anywhere in the repo yet (fresh build). `bars.py`
(258 lines) and `datasets.py` (425 lines) currently have **no caching of any kind** — every `get` /
`list` / `load_bars` / `load_events` / `replay` call re-verifies from disk unconditionally, every
time. `bar_index.py` (171 lines, full file read) is the exact "derived, rebuildable, owns nothing"
shape precedent (hermetic DI'd path via constructor arg, WAL + `busy_timeout`, a `:memory:` guard,
a `reindex()` full-rebuild path) — though its SCHEMA differs: `bar_index.py` keys on a business
tuple (`symbol, timeframe, window_start_utc, window_end_utc`) for store-first lookup, while
`dataset_index.py` keys on the file `path` itself, since its job is "was this exact file content
already verified" — a durable version of the in-process stat cache, not a store-first lookup.
`edge_report_cache.py:175-188`'s `resolve_cache_db_path` and `routes.py:1550-1561`'s
`get_bar_index()` are the exact env-else-sibling resolver pattern to mirror for the new
`dataset_index.db` path (`routes.py:1410-1414`'s current 5-line `get_dataset_store()` grows to this
shape). `setups.py:369-409`'s `_SCAN_CACHE` is the atomic-tuple-publish +
read-local-reference-before-inspect concurrency precedent the two new in-process stat-keyed caches
must follow — a module global, not an instance attribute (`BarStore`/`DatasetStore` are constructed
fresh per FastAPI dependency call). `tests/conftest.py` is currently 14 lines with zero fixtures
beyond `load_env()` + `anyio_backend` — this iteration adds the file's **first** autouse fixture.
Test files confirmed present to extend: `test_bars.py` (280 lines), `test_datasets.py` (347 lines),
`test_bar_index.py` (230 lines, the structural mirror for the new `test_dataset_index.py`),
`test_datasets_api.py`, `test_mcp_server.py` (line 251:
`test_datasets_tool_byte_identical_on_a_non_empty_live_list` — the exact test the iter-1-applied
lesson says to extend for TC-8's MCP leg).

## What to Build

- **`bars.py`**: a module-level, stat-keyed `(path, st_size, st_mtime_ns)` verified-record cache
  (the `_SCAN_CACHE` atomic-publish discipline). A stat match serves the cached `_LoadedBarSeries`
  with zero I/O; any mismatch re-runs the full existing `_load` verifier; `BarSeriesIntegrityError`
  is never cached; a ~2s racy-write guard refuses to cache a just-written file. `get`/`list` return
  **per-call copies** of the cached rows (never the cached list object itself), so a caller
  mutation can never poison a later read; `load_bars` builds fresh `RawBar`s from cached rows. Add
  a public `BarStore.root` property (today only the private `self._root`, line 136) and a
  test-only cache-reset helper.
- **`datasets.py`**: the SAME stat-keyed cache shape, scoped to **metadata only** (the `meta` dict —
  never the 882MB `rows`), consulted ONLY by `get()` (line 242) and `list()` (line 246).
  `load_events()` (line 262) and `replay()` (line 268) are explicitly untouched — they keep calling
  `_load_by_id`/`_load` directly and unconditionally on every call (the trust boundary this
  interlude's critical anti-goal protects). Update both modules' docstrings ("Checksummed +
  verified on EVERY load" bullets) to the honest new contract: "re-verified on every content change
  (stat-keyed)". Add a matching test-only cache-reset helper for this store's cache.
- **New `apps/backend/app/research/dataset_index.py`**: a durable sibling SQLite metadata index —
  table `dataset_index(path PRIMARY KEY, size, mtime_ns, meta_json, created_utc)`, `meta_json`
  stored via plain `json.dumps` WITHOUT `sort_keys` (the `edge_report_cache.py` `_insert`
  byte-identity precedent). Mirrors `bar_index.py`'s hermetic-DI'd-path / WAL+busy_timeout /
  `:memory:`-guard shape and its "derived, rebuildable, owns nothing" philosophy — losing this file
  loses nothing, the next read re-verifies and repopulates it.
- **`datasets.py`**: `DatasetStore.__init__` (today `def __init__(self, root: str | Path) -> None`,
  line 189) gains a keyword-only `index_db_path: str | None = None`. Default (`None`) preserves
  today's exact in-process-only behavior for every existing caller (none pass it today). When set,
  `get()`/`list()` consult the durable index (after the in-process stat cache, before a full file
  verify) and publish newly-verified metadata into it.
- **`routes.py`**: `get_dataset_store()` (lines 1410-1414) grows to resolve
  `TAPEOLOGY_DATASET_INDEX_DB` env else the `.data/dataset_index.db` sibling of
  `CONFIG.dataset_dir_resolved()` — the exact `get_bar_index()` shape (lines 1550-1561) — and pass
  `index_db_path=...` into `DatasetStore(...)`. Zero change to any route's request/response body or
  `Depends` signature; every route already using `Depends(get_dataset_store)` is untouched.
- **`tests/conftest.py`**: add the file's first autouse fixture, resetting both new stat-keyed
  caches (via the two test-only reset helpers) between tests — prevents cross-test cache leakage.
- **Tests** (see Key Test Scenarios) across `test_bars.py`, `test_datasets.py`, a new
  `test_dataset_index.py` (mirrors `test_bar_index.py`'s structure), `test_datasets_api.py`,
  `test_edge_report_api.py`, and `test_mcp_server.py` — the last one MUST be verified both
  standalone and inside the full module (the iter-1-applied lesson: TC-8's MCP leg extends
  `test_datasets_tool_byte_identical_on_a_non_empty_live_list`, line 251, which depends on
  module-scoped shared-backend state).

## Agents Required

- developer: yes -- implements the full J-02 change in one dispatch (this project's convention: a
  single full-stack developer dispatch per iteration; there is no frontend work this iteration so
  nothing is split off).
- backend-data: yes -- `bars.py`, `datasets.py`, new `dataset_index.py`, `routes.py`'s
  `get_dataset_store` dependency, `conftest.py`'s new autouse reset fixture, and all new/adapted
  backend tests listed above.
- frontend-ux: no -- J-02 ships zero frontend files. `docs/goal.md` tags this journey
  "(Keyless; automated.)" and the phase spec's own Frontend section states verbatim: "None — J-02
  is a backend-only accelerator." Nothing under `apps/frontend/` is created or modified.

Frontend Present: no

## Files to Create/Modify

Backend:
- `apps/backend/app/research/bars.py` -- add the module-level stat-keyed verified-record cache +
  `BarStore.root` property + test-only reset helper; route `get`/`list`/`load_bars` through it.
- `apps/backend/app/research/datasets.py` -- add the metadata-only stat-keyed cache (consulted only
  by `get()`/`list()`, never `load_events()`/`replay()`); add the keyword-only `index_db_path`
  constructor arg wired to the new durable index; add a test-only reset helper; docstring updates.
- New `apps/backend/app/research/dataset_index.py` -- the durable sibling SQLite metadata index
  (schema + `insert`/`lookup`/`list`/rebuild-on-miss API, the `bar_index.py`-precedent shape).
- `apps/backend/app/research/routes.py` -- `get_dataset_store()` (lines 1410-1414) grows the
  env-else-sibling resolver, mirroring `get_bar_index()` (1550-1561); no other route touched.
- `apps/backend/tests/conftest.py` -- add the first autouse cache-reset fixture (both stores).
- `apps/backend/tests/test_bars.py` -- new tests for TC-1, TC-2, TC-3, TC-5 (bars leg), TC-6, TC-11.
- `apps/backend/tests/test_datasets.py` -- new tests for TC-4, TC-5 (datasets leg), TC-7.
- New `apps/backend/tests/test_dataset_index.py` -- TC-9, TC-10 (mirrors `test_bar_index.py`).
- `apps/backend/tests/test_datasets_api.py` -- TC-8's REST byte-identity leg (warm vs.
  force-fresh-verify response equality).
- `apps/backend/tests/test_edge_report_api.py` -- TC-14 (existing integrity-error 500 path
  unaffected by the new metadata cache).
- `apps/backend/tests/test_mcp_server.py` -- TC-8's MCP leg, extending
  `test_datasets_tool_byte_identical_on_a_non_empty_live_list` (line 251); run standalone AND
  inside the full module before trusting a green result (iter-1 audit finding T1's lesson).

Docs:
- `docs/handoffs/goal-fast_wall-iter-2-dev.md` -- required dev handoff (DoD item).

Frontend: none. No file under `apps/frontend/` is created or modified this iteration.

## Key Test Scenarios

Full test-first contract (TC-1..TC-15) is in `docs/phases/goal-fast_wall-iter-2.md` — highlights:

- `BarStore.get`/`list` warm-hit zero-read: a file-read counting spy records 0 additional reads on
  a second call for unchanged content, per-id and across a full `list()` (TC-1, TC-2).
- Tamper-after-warm-read: corrupting a bar file's bytes after it was already served once still
  raises `BarSeriesIntegrityError` on the next `get` — never stale-good, never silent (TC-3); the
  dataset-store equivalent surfaces the corrupt file in `list()`'s `errors`, never as cached-valid
  metadata (TC-4).
- Racy-write guard: a file written and re-read inside the ~2s window is never served from cache —
  the spy still records a real read on the second call, on both stores (TC-5).
- Row-copy isolation: a caller mutating `BarStore.get(...)["bars"]` in place never poisons a
  subsequent cached read (TC-6).
- Trust-boundary proof: `DatasetStore.load_events`/`replay` fully re-verify (spy proves real reads
  + both checksums recomputed) even when the metadata cache is warm — the mechanical proof of the
  critical "verification trust boundary never weakens" anti-goal (TC-7).
- Byte-identity: `GET /research/datasets` warm-cache response == a fresh cache-cleared response,
  both REST and the MCP `datasets` proxy; the MCP leg run standalone AND inside the full module
  (TC-8, applying the iter-1-audit lesson).
- Durable-index restart simulation: a brand-new `DatasetStore` (fresh in-process cache, same
  `index_db_path`, simulating a backend restart) serves `list()` with zero file reads, byte-identical
  (`sort_keys=True` equality) to a from-scratch verify (TC-9); deleting `dataset_index.db` costs
  exactly one re-verify pass per file and repopulates the DB with N rows, no data loss (TC-10).
- `BarStore.root` is a public, read-only property returning the resolved root path (TC-11).
- The new autouse conftest fixture prevents cross-test cache leakage — two tests under different
  `tmp_path` roots never observe each other's cached content (TC-12).
- Full backend suite green, 0 new failures, 0 newly-skipped/deleted tests,
  `config.config_fingerprint()` still `4d665603569b9dbf` (TC-13).
- `GET /research/edge-report`'s existing integrity-error 500 path (`"integrity"` in `detail`) is
  unaffected by the new metadata cache — `peek_strategy_comparison_report`'s `_verified_records`
  call still surfaces the error (TC-14, Required-still-passing J-01).
- Required-still-passing J-01, J-07: deterministic replay of stored golden scripts — no new
  browser-qa dispatch this iteration (neither journey's UI surface changes; `Frontend Present: no`).
- TC-15 *(non-blocking, operator-verified only)*: `GET /research/datasets` on the real 882MB /
  18-dataset corpus drops from the measured 31.4s cold baseline to sub-second once warm. Record if
  the real corpus is reachable in this environment; never a blocking gate — mirrors iter-1's own
  identical treatment of its real-corpus timing claim.

**Guardrails (do not touch, per phase spec OUT OF SCOPE):**
- `edge_report.py`, `edge_report_cache.py`, `apps/frontend/app/structure/page.tsx` — J-01's
  surfaces; this iteration's speedup reaches them as a transparent side effect through the now-cached
  `dataset_store.list()`, with **zero** code change to any of the three.
- `levels.py`, `tradability.py`, `backtests.py`'s arming checks (`_StructureArmMemo`) — J-03, not
  started here.
- `edge_report_compute.py`, the compute routes, the CLI warmer, the "Compute edge report" button —
  J-04.
- `EdgeReportBacktestCache`, the `run_pair` provider seam, the process pool — J-05.
- `setups.py`'s `_SCAN_CACHE` / `compute_setups`'s cache key, and `setups_scan_cache.py` — J-06's
  scope; it depends on this iteration's new `BarStore.root` but is not started here.
- `DatasetStore.load_events()`/`.replay()`'s verification LOGIC itself — both keep fully
  re-verifying on every call; no bypass, no shortcut, no new parameter added to either method.
- `bar_index.py` — untouched, unrelated cache (era-5's store-first bar-recording lookup index).
- Any new `Config` field or new runtime dependency (stdlib `sqlite3` only, the `bar_index.py`
  precedent — `config_fingerprint()` must stay `4d665603569b9dbf`).
- Any deletion or weakening of an existing test in `test_bars.py`, `test_datasets.py`, or
  `test_bar_index.py`.
- Any file under `apps/frontend/` — J-02 ships zero frontend files; no page, panel, or component is
  added or modified.
